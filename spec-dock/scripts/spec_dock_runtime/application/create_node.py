from __future__ import annotations

import contextlib
import ctypes
from dataclasses import replace
from datetime import date
import errno
import os
from pathlib import Path
import shlex
import stat
import sys
import time
from typing import TYPE_CHECKING, Literal, cast
import uuid

from spec_dock_runtime.application.contracts import (
    CreateNodeRequest,
    CreateNodeResult,
    CreatePlan,
)
from spec_dock_runtime.application.repo_context import (
    require_current_repo_slug,
    resolve_current_repo_slug,
    split_repo_slug,
)
from spec_dock_runtime.application.sync_state import post_mutation_sync
from spec_dock_runtime.domain.ids import (
    find_existing_id_by_num,
    format_id,
    parse_id,
    resolve_id_input,
    resolve_input_title_and_slug,
)
from spec_dock_runtime.domain.models import SpecGraph, SpecNode, SpecNodeKind, SpecNodeSeed
from spec_dock_runtime.domain.tree import build_graph
from spec_dock_runtime.domain.validation import validate_graph_and_deps
from spec_dock_runtime.infra.contracts import StoredMetaRecord

if TYPE_CHECKING:
    from collections.abc import Callable

    from spec_dock_runtime.application.ports import Ports


_META_FILENAME = ".meta.json"
_CREATE_LOCK_DIRNAME = ".runtime"
_CREATE_LOCK_FILENAME = "create.lock"
_ENV_CREATE_LOCK_WAIT_SECONDS = "SPEC_DOCK_CREATE_LOCK_WAIT_SECONDS"
_ENV_CREATE_LOCK_POLL_SECONDS = "SPEC_DOCK_CREATE_LOCK_POLL_SECONDS"
_ENV_CREATE_LOCK_STALE_SECONDS = "SPEC_DOCK_CREATE_LOCK_STALE_SECONDS"
_DEFAULT_CREATE_LOCK_WAIT_SECONDS = 3.0
_DEFAULT_CREATE_LOCK_POLL_SECONDS = 0.05
_DEFAULT_CREATE_LOCK_STALE_SECONDS = 600.0
CreateWritePhase = Literal["none", "scaffold_copied", "meta_written", "post_write_verified"]
_PARTIAL_LOCAL_WRITE_PHASES: tuple[CreateWritePhase, ...] = (
    "scaffold_copied",
    "meta_written",
    "post_write_verified",
)


class CreatePlanExecutionError(RuntimeError):
    def __init__(self, *, phase: CreateWritePhase, message: str):
        super().__init__(message)
        self.phase = phase


def _resolve_duration_seconds(env_name: str, default: float, *, minimum: float) -> float:
    raw = os.environ.get(env_name)
    if raw is None or not raw.strip():
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise RuntimeError(f"Invalid {env_name}: {raw!r}") from exc
    if value < minimum:
        raise RuntimeError(f"Invalid {env_name}: {value} (must be >= {minimum})")
    return value


def _resolve_duration_seconds_exclusive(env_name: str, default: float, *, minimum: float) -> float:
    raw = os.environ.get(env_name)
    if raw is None or not raw.strip():
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise RuntimeError(f"Invalid {env_name}: {raw!r}") from exc
    if value <= minimum:
        raise RuntimeError(f"Invalid {env_name}: {value} (must be > {minimum})")
    return value


def _resolve_create_lock_path(specdock_dir: Path) -> Path:
    return specdock_dir / "system" / _CREATE_LOCK_DIRNAME / _CREATE_LOCK_FILENAME


def _build_create_lock_metadata(token: str) -> str:
    now_unix = time.time()
    lines = [
        f"token={token}",
        f"pid={os.getpid()}",
        f"user={os.environ.get('USER', 'unknown')}",
        f"created_unix={now_unix:.6f}",
        f"created_iso={date.today().isoformat()}",
    ]
    return "\n".join(lines) + "\n"


def _write_create_lock_payload(fd: int, payload: str) -> None:
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(payload)


def _read_create_lock_metadata(lock_path: Path) -> tuple[dict[str, str], str]:
    try:
        text = lock_path.read_text(encoding="utf-8")
    except OSError as exc:
        return {}, f"unreadable={exc}"

    meta: dict[str, str] = {}
    for line in text.splitlines():
        key, sep, value = line.partition("=")
        if not sep:
            continue
        key = key.strip()
        if not key:
            continue
        meta[key] = value.strip()
    if not meta:
        stripped = text.strip()
        if stripped:
            return {}, f"raw={stripped}"
        return {}, "empty"
    fields = []
    for key in ("pid", "user", "created_unix", "created_iso"):
        if key in meta:
            fields.append(f"{key}={meta[key]}")
    if not fields:
        fields = [f"{k}={v}" for k, v in sorted(meta.items())]
    return meta, ", ".join(fields)


def _is_stale_lock(meta: dict[str, str], *, stale_after_seconds: float) -> bool:
    created_raw = meta.get("created_unix")
    if created_raw is None:
        return False
    try:
        created_unix = float(created_raw)
    except ValueError:
        return False
    return (time.time() - created_unix) >= stale_after_seconds


def _lock_failure_message(
    *,
    specdock_dir: Path,
    lock_path: Path,
    wait_seconds: float,
    elapsed_seconds: float,
    stale: bool,
    lock_meta_summary: str,
) -> str:
    stale_flag = "true" if stale else "false"
    return (
        "create lock acquisition failed: "
        f"wait_s={elapsed_seconds:.3f} wait_limit_s={wait_seconds:.3f} stale={stale_flag} "
        f"path={lock_path} lock_meta=[{lock_meta_summary}]. "
        f"No files were written. {_doctor_guidance_message(specdock_dir)}"
    )


def _runtime_entrypoint_path(specdock_dir: Path) -> Path:
    return (specdock_dir / "scripts" / "spec-dock").resolve()


def _specdock_dir_from_lock_path(lock_path: Path) -> Path:
    if len(lock_path.parents) >= 3:
        return lock_path.parents[2].resolve()
    return lock_path.parent.resolve()


def _doctor_guidance_message(specdock_dir: Path) -> str:
    command = " ".join(shlex.quote(part) for part in (str(_runtime_entrypoint_path(specdock_dir)), "doctor"))
    return f"Run `{command}` for guidance."


def _acquire_create_lock(specdock_dir: Path) -> tuple[Path, str]:
    lock_path = _resolve_create_lock_path(specdock_dir)
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    wait_seconds = _resolve_duration_seconds(
        _ENV_CREATE_LOCK_WAIT_SECONDS,
        _DEFAULT_CREATE_LOCK_WAIT_SECONDS,
        minimum=0.0,
    )
    poll_seconds = _resolve_duration_seconds(
        _ENV_CREATE_LOCK_POLL_SECONDS,
        _DEFAULT_CREATE_LOCK_POLL_SECONDS,
        minimum=0.001,
    )
    stale_after_seconds = _resolve_duration_seconds(
        _ENV_CREATE_LOCK_STALE_SECONDS,
        _DEFAULT_CREATE_LOCK_STALE_SECONDS,
        minimum=0.0,
    )

    token = uuid.uuid4().hex
    payload = _build_create_lock_metadata(token)
    started_at = time.monotonic()
    deadline = started_at + wait_seconds

    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            meta, summary = _read_create_lock_metadata(lock_path)
            elapsed = time.monotonic() - started_at
            if _is_stale_lock(meta, stale_after_seconds=stale_after_seconds):
                raise RuntimeError(
                    _lock_failure_message(
                        specdock_dir=specdock_dir,
                        lock_path=lock_path,
                        wait_seconds=wait_seconds,
                        elapsed_seconds=elapsed,
                        stale=True,
                        lock_meta_summary=summary,
                    )
                ) from None
            if elapsed >= wait_seconds:
                raise RuntimeError(
                    _lock_failure_message(
                        specdock_dir=specdock_dir,
                        lock_path=lock_path,
                        wait_seconds=wait_seconds,
                        elapsed_seconds=elapsed,
                        stale=False,
                        lock_meta_summary=summary,
                    )
                ) from None
            remaining = max(0.0, deadline - time.monotonic())
            if remaining <= 0:
                continue
            time.sleep(min(poll_seconds, remaining))
            continue
        except OSError as exc:
            raise RuntimeError(
                "create lock acquisition failed: "
                f"path={lock_path} error={exc}. {_doctor_guidance_message(specdock_dir)}"
            ) from exc
        else:
            try:
                _write_create_lock_payload(fd, payload)
            except Exception as exc:
                cleanup_result = "cleanup_unlink=ok"
                try:
                    lock_path.unlink()
                except OSError as cleanup_exc:
                    cleanup_result = f"cleanup_unlink_failed={cleanup_exc}"
                raise RuntimeError(
                    "create lock metadata write failed: "
                    f"path={lock_path} error={exc} {cleanup_result}. "
                    f"No files were written. {_doctor_guidance_message(specdock_dir)}"
                ) from exc
            return lock_path, token


def _release_create_lock(lock_path: Path, token: str, *, specdock_dir: Path | None = None) -> None:
    effective_specdock_dir = specdock_dir if specdock_dir is not None else _specdock_dir_from_lock_path(lock_path)
    meta, _summary = _read_create_lock_metadata(lock_path)
    if meta.get("token") != token:
        if lock_path.exists():
            raise RuntimeError(
                "create lock release failed: "
                f"path={lock_path} reason=ownership_mismatch. "
                f"Create may have already written files. {_doctor_guidance_message(effective_specdock_dir)}"
            )
        return
    try:
        lock_path.unlink()
    except OSError as exc:
        raise RuntimeError(
            "create lock release failed: "
            f"path={lock_path} error={exc}. "
            f"Create may have already written files. {_doctor_guidance_message(effective_specdock_dir)}"
        ) from exc


def _post_write_duplicate_guard(ports: Ports, *, node_id: str) -> None:
    try:
        graph = load_graph(ports, validate=False)
    except RuntimeError as exc:
        raise RuntimeError(f"post-write duplicate guard failed: {exc}") from exc
    if node_id not in graph.nodes_by_id:
        raise RuntimeError(f"post-write duplicate guard failed: created id not found: {node_id}")


def _resolve_specdock_dir(ports: Ports) -> Path:
    if ports.specdock_dir is not None:
        return ports.specdock_dir
    if ports.repo_root is not None:
        return ports.repo_root / "spec-dock"
    raise RuntimeError("specdock_dir is required")


def _resolve_repo_root(ports: Ports) -> Path:
    if ports.repo_root is None:
        raise RuntimeError("repo_root is required")
    return ports.repo_root


def _normalize_repo_slug(owner: str | None, repo: str | None) -> str | None:
    normalized_owner = str(owner or "").strip().lower()
    normalized_repo = str(repo or "").strip().lower()
    if not normalized_owner or not normalized_repo:
        return None
    return f"{normalized_owner}/{normalized_repo}"


def _resolve_node_repo(ports: Ports):
    if ports.node_repo is not None:
        return ports.node_repo

    if ports.node_reader is None:
        raise RuntimeError("node_repo is required")

    class _NodeRepoAdapter:
        def __init__(self, reader):
            self._reader = reader

        def load_node_records(self, specdock_dir: Path):
            try:
                return self._reader.load_node_records(specdock_dir)
            except TypeError:
                return self._reader.load_node_records()

        def write_meta(self, dest_dir: Path, record: StoredMetaRecord) -> None:
            writer = getattr(self._reader, "write_meta", None)
            if writer is None:
                raise RuntimeError("node_repo.write_meta is required")
            writer(dest_dir, record)

        def write_meta_at(self, dest_dir_fd: int, record: StoredMetaRecord) -> None:
            writer = getattr(self._reader, "write_meta_at", None)
            if writer is None:
                raise RuntimeError("node_repo.write_meta_at is required")
            writer(dest_dir_fd, record)

    return _NodeRepoAdapter(ports.node_reader)


def _resolve_template_scaffolder(ports: Ports):
    if ports.template_scaffolder is None:
        raise RuntimeError("template_scaffolder is required")
    return ports.template_scaffolder


def _to_spec_node_seed(record: StoredMetaRecord) -> SpecNodeSeed:
    return SpecNodeSeed(
        kind=cast("SpecNodeKind", record.kind),
        id=record.id,
        title=record.title,
        slug=record.slug,
        path=Path(record.path),
        meta_path=Path(record.meta_path),
        parent_id=record.parent_id,
        initiative_id=record.initiative_id,
        epic_id=record.epic_id,
        github_issue_number=record.github_issue_number,
        github_repo_owner=record.github_repo_owner,
        github_repo_name=record.github_repo_name,
    )


def _to_spec_node(record: StoredMetaRecord) -> SpecNode:
    return SpecNode(
        kind=cast("SpecNodeKind", record.kind),
        id=record.id,
        title=record.title,
        slug=record.slug,
        path=Path(record.path),
        meta_path=Path(record.meta_path),
        parent_id=record.parent_id,
        initiative_id=record.initiative_id,
        epic_id=record.epic_id,
        github_issue_number=record.github_issue_number,
        github_repo_owner=record.github_repo_owner,
        github_repo_name=record.github_repo_name,
    )


def load_graph(ports: Ports, *, validate: bool) -> SpecGraph:
    specdock_dir = _resolve_specdock_dir(ports)
    node_repo = _resolve_node_repo(ports)
    records = node_repo.load_node_records(specdock_dir)
    graph = build_graph([_to_spec_node_seed(record) for record in records])
    if validate:
        repo_root = _resolve_repo_root(ports)
        current_repo_slug = resolve_current_repo_slug(ports)
        report = validate_graph_and_deps(
            graph,
            repo_root=repo_root,
            current_repo_slug=current_repo_slug,
        )
        if report.errors:
            raise RuntimeError(report.errors[0])
    return graph


def _prefix_for_kind(kind: Literal["initiative", "epic", "issue"]) -> str:
    if kind == "initiative":
        return "init"
    if kind == "epic":
        return "epic"
    return "iss"


def _resolve_github_mode(
    req: CreateNodeRequest, kind: Literal["initiative", "epic", "issue"]
) -> Literal["create", "link_existing"]:
    del kind

    if req.github_mode is None:
        return "create"
    if req.github_mode not in ("create", "link_existing"):
        raise RuntimeError(f"Unsupported github mode: {req.github_mode}")
    return req.github_mode


def resolve_parent_for_create(
    req: CreateNodeRequest,
    graph: SpecGraph,
    *,
    kind: Literal["initiative", "epic", "issue"],
) -> str | None:
    if kind == "initiative":
        return None

    if kind == "epic":
        if req.parent_id is None:
            raise RuntimeError("--initiative is required")
        parent_id = resolve_id_input(req.parent_id, prefix="init", field="initiative", nodes=graph.nodes_by_id)
        parent = graph.nodes_by_id.get(parent_id)
        if parent is None or parent.kind != "initiative":
            raise RuntimeError(f"Initiative not found: {parent_id}")
        return parent.id

    if req.parent_id is None:
        raise RuntimeError("--epic is required")
    parent_id = resolve_id_input(req.parent_id, prefix="epic", field="epic", nodes=graph.nodes_by_id)
    parent = graph.nodes_by_id.get(parent_id)
    if parent is None or parent.kind != "epic":
        raise RuntimeError(f"Epic not found: {parent_id}")
    if not parent.initiative_id:
        raise RuntimeError(f"Epic meta missing initiative_id: {parent.id}")
    return parent.id


def _node_github_linkage_key(
    node: SpecNode,
    *,
    current_repo_slug: str | None,
) -> tuple[str | None, int] | None:
    if node.kind not in ("initiative", "epic", "issue") or node.github_issue_number is None:
        return None
    repo_slug = _normalize_repo_slug(node.github_repo_owner, node.github_repo_name) or current_repo_slug
    return (repo_slug, int(node.github_issue_number))


def _node_github_repo_slug(node: SpecNode) -> str | None:
    return _normalize_repo_slug(node.github_repo_owner, node.github_repo_name)


def _resolve_requested_repo_slug(req: CreateNodeRequest, *, current_repo_slug: str | None) -> str | None:
    owner = (req.github_repo_owner or "").strip().lower()
    repo = (req.github_repo_name or "").strip().lower()
    if owner or repo:
        if not owner or not repo:
            raise RuntimeError("github_repo_owner and github_repo_name must be provided together")
        requested_repo_slug = _normalize_repo_slug(owner, repo)
        if current_repo_slug is not None and requested_repo_slug != current_repo_slug:
            raise RuntimeError(
                "cross-repo GitHub linkage is not supported: "
                f"requested repo={requested_repo_slug} current repo={current_repo_slug}"
            )
        return requested_repo_slug
    return current_repo_slug


def guard_github_issue_uniqueness(
    graph: SpecGraph,
    github_issue_number: int | None,
    *,
    github_repo_owner: str | None = None,
    github_repo_name: str | None = None,
    current_repo_slug: str | None = None,
) -> None:
    if github_issue_number is None:
        return
    requested_repo_slug = _normalize_repo_slug(github_repo_owner, github_repo_name) or current_repo_slug
    linked_same_number = sorted(
        [
            node
            for node in graph.nodes_by_id.values()
            if node.kind in ("initiative", "epic", "issue") and node.github_issue_number == int(github_issue_number)
        ],
        key=lambda node: (node.kind, node.id, node.meta_path.as_posix()),
    )
    # Fail closed: when current repo cannot be resolved, mixing scoped and unscoped linkage
    # for the same issue number can represent the same logical GitHub issue.
    if linked_same_number:
        mixed_scope_conflict = []
        for node in linked_same_number:
            explicit_repo_slug = _node_github_repo_slug(node)
            effective_repo_slug = explicit_repo_slug or current_repo_slug
            if requested_repo_slug is None and explicit_repo_slug is not None:
                mixed_scope_conflict.append(node)
                continue
            if requested_repo_slug is not None and effective_repo_slug is None:
                mixed_scope_conflict.append(node)
                continue
        if mixed_scope_conflict:
            found = ", ".join(f"{node.kind}:{node.id} ({node.meta_path.as_posix()})" for node in mixed_scope_conflict)
            requested_repo_label = requested_repo_slug if requested_repo_slug is not None else "(current-or-unknown)"
            raise RuntimeError(
                "github linkage scope is ambiguous and rejected (fail-closed): "
                f"repo={requested_repo_label} github.issue_number={int(github_issue_number)} conflicts with "
                "existing linkage(s) whose repository scope cannot be resolved: "
                f"{found}. Configure current repo remote (origin) or normalize linkage scope before retrying."
            )

    linkage_key = (requested_repo_slug, int(github_issue_number))
    linked = [
        node
        for node in graph.nodes_by_id.values()
        if _node_github_linkage_key(node, current_repo_slug=current_repo_slug) == linkage_key
    ]
    if not linked:
        return
    linked = sorted(linked, key=lambda node: (node.kind, node.id, node.meta_path.as_posix()))
    found = ", ".join(f"{node.kind}:{node.id} ({node.meta_path.as_posix()})" for node in linked)
    repo_label = requested_repo_slug if requested_repo_slug is not None else "(current-or-unknown)"
    raise RuntimeError(
        f"github linkage is already linked: repo={repo_label} github.issue_number={int(github_issue_number)}: {found}. "
        "Fix github linkage in one of the listed .meta.json files, "
        "or choose a different GitHub issue number (target)."
    )


def _scaffold_file_paths(template_dir: Path, dest_dir: Path) -> list[Path]:
    if not template_dir.exists() or not template_dir.is_dir():
        raise RuntimeError(f"Missing template directory: {template_dir}")
    files: list[Path] = []
    for src_path in sorted(template_dir.rglob("*"), key=lambda p: p.as_posix()):
        if src_path.is_file():
            files.append(dest_dir / src_path.relative_to(template_dir))
    return files


def _rules_source_paths(
    *,
    kind: Literal["initiative", "epic", "issue"],
    specdock_dir: Path,
) -> list[Path]:
    docs_rules_dir = specdock_dir / "docs" / "rules"
    if kind == "initiative":
        return [
            docs_rules_dir / "initiative" / "epics.md",
            docs_rules_dir / "initiative" / "artifacts.md",
        ]
    if kind == "epic":
        return [
            docs_rules_dir / "epic" / "issues.md",
            docs_rules_dir / "epic" / "artifacts.md",
        ]
    return [docs_rules_dir / "issue" / "artifacts.md"]


def _rules_scaffold_specs(
    *,
    kind: Literal["initiative", "epic", "issue"],
    dest_dir: Path,
    specdock_dir: Path,
) -> list[tuple[Path, Path]]:
    rules_source_paths = _rules_source_paths(kind=kind, specdock_dir=specdock_dir)
    if kind == "initiative":
        return [
            (dest_dir / "epics" / "rules.md", rules_source_paths[0]),
            (dest_dir / "artifacts" / "rules.md", rules_source_paths[1]),
        ]
    if kind == "epic":
        return [
            (dest_dir / "issues" / "rules.md", rules_source_paths[0]),
            (dest_dir / "artifacts" / "rules.md", rules_source_paths[1]),
        ]
    return [
        (dest_dir / "artifacts" / "rules.md", rules_source_paths[0]),
    ]


def _create_relative_symlink(link_path: Path, target_path: Path) -> None:
    _validate_rules_symlink_preflight(link_path=link_path, target_path=target_path)
    link_path.parent.mkdir(parents=True, exist_ok=True)
    rel_target = os.path.relpath(target_path, start=link_path.parent)
    Path(link_path).symlink_to(rel_target)


def _open_relative_directory_at(root_fd: int, parts: tuple[str, ...]) -> int:
    current_fd = os.dup(root_fd)
    try:
        for part in parts:
            with contextlib.suppress(FileExistsError):
                os.mkdir(part, dir_fd=current_fd)
            next_fd = os.open(
                part,
                os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=current_fd,
            )
            os.close(current_fd)
            current_fd = next_fd
        return current_fd
    except Exception:
        with contextlib.suppress(OSError):
            os.close(current_fd)
        raise


def _create_relative_symlink_at(
    node_fd: int,
    *,
    node_dir: Path,
    link_path: Path,
    target_path: Path,
) -> None:
    _validate_rules_symlink_preflight(link_path=link_path, target_path=target_path)
    relative_link_path = link_path.relative_to(node_dir)
    parent_fd = _open_relative_directory_at(node_fd, relative_link_path.parts[:-1])
    try:
        rel_target = os.path.relpath(target_path, start=link_path.parent)
        os.symlink(rel_target, relative_link_path.name, dir_fd=parent_fd)
    finally:
        os.close(parent_fd)


def _validate_parent_dir_preflight(parent_dir: Path) -> None:
    current = parent_dir
    while True:
        if os.path.lexists(current):
            if current.is_symlink():
                raise RuntimeError(f"Destination already exists: {current}")
            if not current.is_dir():
                raise RuntimeError(f"Destination already exists: {current}")
            return
        next_parent = current.parent
        if next_parent == current:
            return
        current = next_parent


def _validate_rules_symlink_preflight(*, link_path: Path, target_path: Path) -> None:
    if not target_path.exists() or not target_path.is_file():
        raise RuntimeError(f"Missing rules source: {target_path}")
    _validate_parent_dir_preflight(link_path.parent)
    if os.path.lexists(link_path):
        raise RuntimeError(f"Destination already exists: {link_path}")


def _nearest_existing_parent_dir(path: Path) -> Path:
    current = path
    while not os.path.lexists(current):
        next_parent = current.parent
        if next_parent == current:
            raise RuntimeError(f"Destination already exists: {path}")
        current = next_parent
    return current


def _preflight_symlink_creation_capability(*, link_path: Path) -> None:
    probe_dir = _nearest_existing_parent_dir(link_path.parent)
    if probe_dir.is_symlink() or not probe_dir.is_dir():
        raise RuntimeError(f"Destination already exists: {probe_dir}")
    probe_path = probe_dir / f".spec-dock-symlink-probe-{os.getpid()}-{uuid.uuid4().hex}"
    probe_target = f".spec-dock-symlink-target-{uuid.uuid4().hex}"
    try:
        Path(probe_path).symlink_to(probe_target)
    except OSError as exc:
        raise RuntimeError(f"Symlink creation preflight failed at {link_path.parent}: {exc}") from exc
    try:
        probe_path.unlink()
    except OSError as exc:
        raise RuntimeError(f"Symlink creation preflight cleanup failed at {probe_path}: {exc}") from exc


def _preflight_rules_symlink_creation_capability(
    rules_scaffold_specs: list[tuple[Path, Path]],
) -> None:
    probed_dirs: set[Path] = set()
    for link_path, _target_path in rules_scaffold_specs:
        probe_dir = _nearest_existing_parent_dir(link_path.parent)
        if probe_dir in probed_dirs:
            continue
        _preflight_symlink_creation_capability(link_path=link_path)
        probed_dirs.add(probe_dir)


def _precheck_pre_github_create_rules_sources(
    *,
    kind: Literal["initiative", "epic", "issue"],
    specdock_dir: Path,
) -> None:
    for target_path in _rules_source_paths(kind=kind, specdock_dir=specdock_dir):
        if not target_path.exists() or not target_path.is_file():
            raise RuntimeError(f"Missing rules source: {target_path}")


def _precheck_pre_github_create_symlink_dest_dir(
    *,
    kind: Literal["initiative", "epic", "issue"],
    specdock_dir: Path,
    parent: SpecNode | None,
) -> Path:
    probe_leaf = f".spec-dock-github-create-preflight-{uuid.uuid4().hex}"
    if kind == "initiative":
        return specdock_dir / "initiatives" / probe_leaf
    if parent is None:
        raise RuntimeError("parent is required for nested GitHub create preflight")
    if kind == "epic":
        return parent.path / "epics" / probe_leaf
    return parent.path / "issues" / probe_leaf


def _precheck_pre_github_create_symlink_capability(
    *,
    kind: Literal["initiative", "epic", "issue"],
    specdock_dir: Path,
    parent: SpecNode | None,
) -> None:
    dest_dir = _precheck_pre_github_create_symlink_dest_dir(
        kind=kind,
        specdock_dir=specdock_dir,
        parent=parent,
    )
    rules_scaffold_specs = _rules_scaffold_specs(kind=kind, dest_dir=dest_dir, specdock_dir=specdock_dir)
    _preflight_rules_symlink_creation_capability(rules_scaffold_specs)


def _replacements(
    *,
    kind: Literal["initiative", "epic", "issue"],
    node_id: str,
    title: str,
    parent_id: str | None,
    initiative_id: str | None,
    github_issue_number: int | None,
    today: str,
) -> dict[str, str]:
    issue_ref = f"#{github_issue_number}" if github_issue_number is not None else ""
    common = {
        "<YOUR_NAME>": os.environ.get("USER", "<YOUR_NAME>"),
        "YYYY-MM-DD": today,
    }
    if kind == "initiative":
        return {
            "<INIT_ID>": node_id,
            "<INIT_TITLE>": title,
            "<GITHUB_ISSUE_NUMBER_OR_URL>": issue_ref,
            **common,
        }
    if kind == "epic":
        assert parent_id is not None
        return {
            "<EPIC_ID>": node_id,
            "<EPIC_TITLE>": title,
            "<INIT_ID>": parent_id,
            "<GITHUB_ISSUE_NUMBER_OR_URL>": issue_ref,
            **common,
        }
    assert parent_id is not None and initiative_id is not None
    return {
        "<ISS_ID>": node_id,
        "<ISS_TITLE>": title,
        "<FEATURE_ID>": node_id,
        "<FEATURE_NAME>": title,
        "<EPIC_ID>": parent_id,
        "<INIT_ID>": initiative_id,
        "<ISSUE_NUMBER_OR_URL>": issue_ref,
        "<GITHUB_ISSUE_NUMBER_OR_URL>": issue_ref,
        **common,
    }


def _resolve_dest_dir(
    *,
    kind: Literal["initiative", "epic", "issue"],
    node_id: str,
    slug: str,
    graph: SpecGraph,
    specdock_dir: Path,
    parent_id: str | None,
) -> tuple[Path, str | None, str | None]:
    if kind == "initiative":
        return specdock_dir / "initiatives" / f"{node_id}-{slug}", None, None

    assert parent_id is not None
    parent = graph.nodes_by_id.get(parent_id)
    if parent is None:
        raise RuntimeError(f"Parent not found: {parent_id}")

    if kind == "epic":
        return parent.path / "epics" / f"{node_id}-{slug}", parent.id, None

    if not parent.initiative_id:
        raise RuntimeError(f"Epic meta missing initiative_id: {parent.id}")
    return parent.path / "issues" / f"{node_id}-{slug}", parent.initiative_id, parent.id


def plan_node_creation(
    req: CreateNodeRequest,
    graph: SpecGraph,
    *,
    kind: Literal["initiative", "epic", "issue"],
    specdock_dir: Path,
    today: str,
    current_repo_slug: str | None = None,
) -> CreatePlan:
    title, slug = resolve_input_title_and_slug(req.title, req.slug)
    mode = _resolve_github_mode(req, kind)
    prefix = _prefix_for_kind(kind)
    requested_repo_slug = _resolve_requested_repo_slug(req, current_repo_slug=current_repo_slug)

    if req.github_issue_number is None:
        raise RuntimeError("github_issue_number is required for github mode")
    node_id = format_id(prefix, int(req.github_issue_number), local=False)
    guard_github_issue_uniqueness(
        graph,
        int(req.github_issue_number),
        github_repo_owner=req.github_repo_owner,
        github_repo_name=req.github_repo_name,
        current_repo_slug=current_repo_slug,
    )

    parsed_prefix, is_local, num = parse_id(node_id)
    existing_id = find_existing_id_by_num(graph.nodes_by_id, prefix=parsed_prefix, num=num, local=is_local)
    if existing_id and mode in ("create", "link_existing") and req.github_issue_number is not None:
        existing = graph.nodes_by_id[existing_id]
        existing_repo_slug = (
            _normalize_repo_slug(existing.github_repo_owner, existing.github_repo_name) or current_repo_slug
        )
        if existing_repo_slug != requested_repo_slug:
            existing_repo_label = existing_repo_slug if existing_repo_slug is not None else "(current-or-unknown)"
            requested_repo_label = requested_repo_slug if requested_repo_slug is not None else "(current-or-unknown)"
            raise RuntimeError(
                "cross-repo GitHub linkage is not supported: "
                f"requested repo={requested_repo_label} github.issue_number={int(req.github_issue_number)} "
                f"conflicts with existing repo={existing_repo_label}: {existing_id} ({existing.meta_path})"
            )
    if existing_id:
        existing = graph.nodes_by_id[existing_id]
        raise RuntimeError(f"id already exists: {existing_id} ({existing.meta_path})")

    parent_id = resolve_parent_for_create(req, graph, kind=kind)
    dest_dir, initiative_id, epic_id = _resolve_dest_dir(
        kind=kind,
        node_id=node_id,
        slug=slug,
        graph=graph,
        specdock_dir=specdock_dir,
        parent_id=parent_id,
    )
    replacements = _replacements(
        kind=kind,
        node_id=node_id,
        title=title,
        parent_id=parent_id,
        initiative_id=initiative_id,
        github_issue_number=req.github_issue_number,
        today=today,
    )
    github_repo_owner: str | None = None
    github_repo_name: str | None = None
    if req.github_issue_number is not None:
        current_scope = split_repo_slug(requested_repo_slug)
        if current_scope is not None:
            github_repo_owner, github_repo_name = current_scope
    template_dir = specdock_dir / "templates" / kind
    planned_paths = _scaffold_file_paths(template_dir, dest_dir)
    planned_paths.extend(
        link_path
        for link_path, _target_path in _rules_scaffold_specs(kind=kind, dest_dir=dest_dir, specdock_dir=specdock_dir)
    )
    planned_paths.append(dest_dir / _META_FILENAME)
    meta_path = dest_dir / _META_FILENAME
    return CreatePlan(
        meta=StoredMetaRecord(
            kind=kind,
            id=node_id,
            title=title,
            slug=slug,
            path=dest_dir.as_posix(),
            parent_id=parent_id,
            initiative_id=initiative_id,
            epic_id=epic_id,
            github_issue_number=req.github_issue_number,
            meta_path=meta_path.as_posix(),
            github_repo_owner=github_repo_owner,
            github_repo_name=github_repo_name,
        ),
        dest_dir=dest_dir,
        replacements=replacements,
        planned_paths=planned_paths,
    )


def _resolve_template_dir(plan: CreatePlan) -> Path:
    for parent in [plan.dest_dir, *plan.dest_dir.parents]:
        if parent.name == "spec-dock":
            return parent / "templates" / plan.meta.kind
    raise RuntimeError(f"spec-dock root not found from destination: {plan.dest_dir}")


def create_write_phase_has_local_writes(phase: CreateWritePhase) -> bool:
    return phase in _PARTIAL_LOCAL_WRITE_PHASES


def resolve_create_write_phase(error: Exception, *, default: CreateWritePhase = "none") -> CreateWritePhase:
    if isinstance(error, CreatePlanExecutionError):
        return error.phase
    return default


def _claimed_node_tree_identity_at(parent_fd: int, name: str) -> tuple[int, int]:
    stat_result = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    if not stat.S_ISDIR(stat_result.st_mode):
        raise RuntimeError(f"Claimed node destination is not a directory: {name}")
    return stat_result.st_dev, stat_result.st_ino


def _directory_path_identity(path: Path) -> tuple[int, int]:
    stat_result = path.stat(follow_symlinks=False)
    if not stat.S_ISDIR(stat_result.st_mode):
        raise RuntimeError(f"Destination parent is not a directory: {path}")
    return stat_result.st_dev, stat_result.st_ino


def _resolve_node_tree_no_replace_rename() -> tuple[Callable[..., int], int]:
    library = ctypes.CDLL(None, use_errno=True)
    if sys.platform.startswith("linux"):
        rename = getattr(library, "renameat2", None)
        flag = 0x00000001
    elif sys.platform == "darwin":
        rename = getattr(library, "renameatx_np", None)
        flag = 0x00000004
    else:
        raise NotImplementedError("atomic no-replace rename is unavailable")
    if rename is None:
        raise NotImplementedError("atomic no-replace rename is unavailable")
    rename.argtypes = (
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    )
    rename.restype = ctypes.c_int
    return cast("Callable[..., int]", rename), flag


def _require_node_tree_no_replace_rename_capability() -> None:
    _resolve_node_tree_no_replace_rename()


def _rename_node_tree_no_replace_between_at(
    source_parent_fd: int,
    source_name: str,
    destination_parent_fd: int,
    destination_name: str,
) -> None:
    rename, flag = _resolve_node_tree_no_replace_rename()
    result = rename(
        source_parent_fd,
        os.fsencode(source_name),
        destination_parent_fd,
        os.fsencode(destination_name),
        flag,
    )
    if result == 0:
        return
    error_number = ctypes.get_errno()
    if error_number in (errno.EEXIST, errno.ENOTEMPTY):
        raise FileExistsError(error_number, os.strerror(error_number), destination_name)
    raise OSError(error_number, os.strerror(error_number), destination_name)


def _remove_claimed_directory_contents_at(directory_fd: int) -> None:
    for name in os.listdir(directory_fd):
        entry_stat = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        if not stat.S_ISDIR(entry_stat.st_mode):
            os.unlink(name, dir_fd=directory_fd)
            continue

        child_fd = os.open(
            name,
            os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=directory_fd,
        )
        try:
            child_stat = os.fstat(child_fd)
            child_identity = child_stat.st_dev, child_stat.st_ino
            if child_identity != (entry_stat.st_dev, entry_stat.st_ino):
                raise RuntimeError(f"node rollback child identity changed before open: {name}")
            _remove_claimed_directory_contents_at(child_fd)
            current_identity = _claimed_node_tree_identity_at(directory_fd, name)
            if current_identity != child_identity:
                raise RuntimeError(f"node rollback child identity changed before removal: {name}")
            os.rmdir(name, dir_fd=directory_fd)
        finally:
            os.close(child_fd)


def _verified_directory_identity_at(
    parent_fd: int,
    name: str,
    directory_fd: int,
    *,
    expected_identity: tuple[int, int] | None = None,
) -> tuple[int, int]:
    descriptor_stat = os.fstat(directory_fd)
    if not stat.S_ISDIR(descriptor_stat.st_mode):
        raise RuntimeError(f"Claimed node transaction entry is not a directory: {name}")
    descriptor_identity = descriptor_stat.st_dev, descriptor_stat.st_ino
    if expected_identity is not None and descriptor_identity != expected_identity:
        raise RuntimeError(f"Claimed node transaction descriptor identity changed: {name}")
    entry_identity = _claimed_node_tree_identity_at(parent_fd, name)
    if entry_identity != descriptor_identity:
        raise RuntimeError(f"Claimed node transaction entry identity changed: {name}")
    return descriptor_identity


def _cleanup_node_tree_transaction(
    *,
    parent_fd: int,
    outer_name: str,
    outer_created: bool,
    outer_fd: int | None,
    outer_identity: tuple[int, int] | None,
    payload_created: bool,
    payload_fd: int | None,
    payload_identity: tuple[int, int] | None,
) -> None:
    if not outer_created:
        return
    if outer_fd is None or outer_identity is None:
        raise RuntimeError("Claimed node outer transaction identity is unconfirmed; refusing cleanup")

    outer_stat = os.fstat(outer_fd)
    verified_outer_identity = outer_stat.st_dev, outer_stat.st_ino
    if not stat.S_ISDIR(outer_stat.st_mode) or verified_outer_identity != outer_identity:
        raise RuntimeError("Claimed node outer transaction descriptor identity changed")
    if payload_created:
        if payload_fd is None or payload_identity is None:
            raise RuntimeError("Claimed node payload identity is unconfirmed; refusing cleanup")
        verified_payload_identity = _verified_directory_identity_at(
            outer_fd,
            "payload",
            payload_fd,
            expected_identity=payload_identity,
        )
        _remove_claimed_directory_contents_at(payload_fd)
        if _claimed_node_tree_identity_at(outer_fd, "payload") != verified_payload_identity:
            raise RuntimeError("Claimed node payload identity changed before cleanup")
        os.rmdir("payload", dir_fd=outer_fd)
    if _claimed_node_tree_identity_at(parent_fd, outer_name) != verified_outer_identity:
        raise RuntimeError("Claimed node outer transaction identity changed before cleanup")
    os.rmdir(outer_name, dir_fd=parent_fd)


def _cleanup_committed_outer_transaction(
    *,
    parent_fd: int,
    outer_name: str,
    outer_identity: tuple[int, int],
) -> None:
    if _claimed_node_tree_identity_at(parent_fd, outer_name) != outer_identity:
        return
    os.rmdir(outer_name, dir_fd=parent_fd)


def _close_node_tree_parent_fd(descriptor: int) -> None:
    os.close(descriptor)


def execute_create_plan(plan: CreatePlan, ports: Ports) -> list[Path]:
    node_repo = _resolve_node_repo(ports)
    template_scaffolder = _resolve_template_scaffolder(ports)
    specdock_dir = _resolve_specdock_dir(ports)

    collisions = [path for path in plan.planned_paths if os.path.lexists(path)]
    if collisions:
        raise RuntimeError(f"Destination already exists: {collisions[0]}")

    template_dir = _resolve_template_dir(plan)
    rules_scaffold_specs = _rules_scaffold_specs(
        kind=plan.meta.kind,
        dest_dir=plan.dest_dir,
        specdock_dir=specdock_dir,
    )
    for link_path, target_path in rules_scaffold_specs:
        _validate_rules_symlink_preflight(link_path=link_path, target_path=target_path)
    if os.path.lexists(plan.dest_dir):
        raise RuntimeError(f"Destination already exists: {plan.dest_dir}")
    _require_node_tree_no_replace_rename_capability()
    _preflight_rules_symlink_creation_capability(rules_scaffold_specs)

    destination_parent_fd: int | None = None
    destination_parent_identity: tuple[int, int] | None = None
    outer_name = f".{plan.dest_dir.name}.transaction-{uuid.uuid4().hex}"
    outer_created = False
    outer_fd: int | None = None
    outer_identity: tuple[int, int] | None = None
    payload_created = False
    payload_fd: int | None = None
    payload_identity: tuple[int, int] | None = None
    committed = False
    try:
        plan.dest_dir.parent.mkdir(parents=True, exist_ok=True)
        destination_parent_fd = os.open(
            plan.dest_dir.parent,
            os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0),
        )
        parent_stat = os.fstat(destination_parent_fd)
        destination_parent_identity = (parent_stat.st_dev, parent_stat.st_ino)
        os.mkdir(outer_name, mode=0o700, dir_fd=destination_parent_fd)
        outer_created = True
        outer_fd = os.open(
            outer_name,
            os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=destination_parent_fd,
        )
        outer_identity = _verified_directory_identity_at(destination_parent_fd, outer_name, outer_fd)
        os.fchmod(outer_fd, 0o700)
        os.mkdir("payload", dir_fd=outer_fd)
        payload_created = True
        payload_fd = os.open(
            "payload",
            os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=outer_fd,
        )
        payload_identity = _verified_directory_identity_at(outer_fd, "payload", payload_fd)
        created_paths = template_scaffolder.copy_scaffolded_tree_at(
            src_dir=template_dir,
            dest_dir=plan.dest_dir,
            dest_dir_fd=payload_fd,
            replacements=plan.replacements,
        )
        created_rule_links: list[Path] = []
        for link_path, target_path in rules_scaffold_specs:
            _create_relative_symlink_at(
                payload_fd,
                node_dir=plan.dest_dir,
                link_path=link_path,
                target_path=target_path,
            )
            created_rule_links.append(link_path)
        node_repo.write_meta_at(payload_fd, plan.meta)
        if _directory_path_identity(plan.dest_dir.parent) != destination_parent_identity:
            raise RuntimeError(f"Destination parent identity changed before publication: {plan.dest_dir.parent}")
        _verified_directory_identity_at(
            destination_parent_fd,
            outer_name,
            outer_fd,
            expected_identity=outer_identity,
        )
        _verified_directory_identity_at(
            outer_fd,
            "payload",
            payload_fd,
            expected_identity=payload_identity,
        )
        _rename_node_tree_no_replace_between_at(
            outer_fd,
            "payload",
            destination_parent_fd,
            plan.dest_dir.name,
        )
        committed = True
        with contextlib.suppress(OSError, RuntimeError):
            _cleanup_committed_outer_transaction(
                parent_fd=destination_parent_fd,
                outer_name=outer_name,
                outer_identity=outer_identity,
            )
    except Exception as exc:
        if not committed and destination_parent_fd is not None:
            try:
                _cleanup_node_tree_transaction(
                    parent_fd=destination_parent_fd,
                    outer_name=outer_name,
                    outer_created=outer_created,
                    outer_fd=outer_fd,
                    outer_identity=outer_identity,
                    payload_created=payload_created,
                    payload_fd=payload_fd,
                    payload_identity=payload_identity,
                )
            except Exception as cleanup_exc:
                raise CreatePlanExecutionError(
                    phase="scaffold_copied",
                    message=f"{exc}; node scaffold rollback failed: {cleanup_exc}",
                ) from exc
        raise CreatePlanExecutionError(phase="none", message=str(exc)) from exc
    finally:
        if payload_fd is not None:
            with contextlib.suppress(OSError):
                os.close(payload_fd)
        if outer_fd is not None:
            with contextlib.suppress(OSError):
                os.close(outer_fd)
        if destination_parent_fd is not None:
            with contextlib.suppress(OSError):
                _close_node_tree_parent_fd(destination_parent_fd)
    created_non_meta_paths = sorted([*created_paths, *created_rule_links], key=lambda path: path.as_posix())
    return [*created_non_meta_paths, Path(plan.meta.meta_path)]


def _github_issue_body(
    *,
    kind: Literal["initiative", "epic", "issue"],
) -> str:
    if kind == "initiative":
        return "Created by spec-dock.\n\nType: initiative\nLocal specs are stored under `spec-dock/initiatives/`.\n"

    if kind == "epic":
        return "Created by spec-dock.\n\nType: epic\nLocal specs are stored under `spec-dock/initiatives/`.\n"

    return "Created by spec-dock.\n\nType: issue\nLocal specs are stored under `spec-dock/initiatives/`.\n"


def _validate_pre_github_create_inputs(
    req: CreateNodeRequest,
    *,
    kind: Literal["initiative", "epic", "issue"],
    mode: Literal["create", "link_existing"],
) -> None:
    del mode

    if kind == "epic" and req.parent_id is None:
        raise RuntimeError("--initiative is required")

    if kind == "issue" and req.parent_id is None:
        raise RuntimeError("--epic is required")

    owner = (req.github_repo_owner or "").strip()
    repo = (req.github_repo_name or "").strip()
    if (owner or repo) and (not owner or not repo):
        raise RuntimeError("github_repo_owner and github_repo_name must be provided together")


def _precheck_pre_github_create_parent(
    req: CreateNodeRequest,
    ports: Ports,
    *,
    kind: Literal["initiative", "epic", "issue"],
) -> SpecNode | None:
    graph = load_graph(ports, validate=False)
    if kind == "initiative":
        return None
    parent_id = resolve_parent_for_create(req, graph, kind=kind)
    return graph.nodes_by_id[parent_id]


def _post_github_recovery_command(
    *,
    github_issue_number: int,
    kind: Literal["initiative", "epic", "issue"],
    req: CreateNodeRequest,
    title: str,
    specdock_dir: Path,
) -> str:
    command_args = [
        str(_runtime_entrypoint_path(specdock_dir)),
        "new",
        kind,
        "--title",
        title,
    ]
    if kind == "epic" and req.parent_id is not None:
        command_args.extend(["--initiative", req.parent_id])
    if kind == "issue" and req.parent_id is not None:
        command_args.extend(["--epic", req.parent_id])
    command_args.extend(["--github-issue", str(github_issue_number)])
    return " ".join(shlex.quote(part) for part in command_args)


def _post_github_retry_or_cleanup_guidance(
    *,
    github_issue_number: int,
    kind: Literal["initiative", "epic", "issue"],
    req: CreateNodeRequest,
    title: str,
    specdock_dir: Path,
) -> str:
    recovery_command = _post_github_recovery_command(
        github_issue_number=github_issue_number,
        kind=kind,
        req=req,
        title=title,
        specdock_dir=specdock_dir,
    )
    return (
        f"Recovery: rerun `{recovery_command}` to link the existing GitHub issue, "
        "or close/cleanup that GitHub issue before retrying."
    )


def _post_github_doctor_first_guidance(
    *,
    specdock_dir: Path,
    local_node_id: str | None,
) -> str:
    node_hint = (
        f"local node `{local_node_id}`" if local_node_id is not None else "the local node created by this request"
    )
    return (
        "Create may already have succeeded. Do not rerun blindly. "
        f"First inspect {node_hint}. {_doctor_guidance_message(specdock_dir)}"
    )


def _build_pre_github_create_failure(*, error: Exception) -> RuntimeError:
    return RuntimeError(f"Outcome: pre_github_fail. {error}")


def _build_post_github_create_failure(
    *,
    local_error: Exception | None,
    release_error: Exception | None,
    created_github_issue_number: int | None,
    kind: Literal["initiative", "epic", "issue"],
    req: CreateNodeRequest,
    title: str,
    specdock_dir: Path,
    local_write_phase: CreateWritePhase,
    local_node_id: str | None,
    lock_acquired: bool,
) -> RuntimeError | None:
    if created_github_issue_number is None:
        return None

    if not lock_acquired:
        if local_error is None:
            return None
        guidance = _post_github_retry_or_cleanup_guidance(
            github_issue_number=created_github_issue_number,
            kind=kind,
            req=req,
            title=title,
            specdock_dir=specdock_dir,
        )
        return RuntimeError(
            "Outcome: post_github_remote_only_fail. "
            f"{local_error} "
            f"GitHub issue was created: #{created_github_issue_number}. "
            f"{guidance}"
        )

    if local_error is not None and release_error is not None:
        guidance = (
            _post_github_doctor_first_guidance(specdock_dir=specdock_dir, local_node_id=local_node_id)
            if create_write_phase_has_local_writes(local_write_phase)
            else _post_github_retry_or_cleanup_guidance(
                github_issue_number=created_github_issue_number,
                kind=kind,
                req=req,
                title=title,
                specdock_dir=specdock_dir,
            )
        )
        return RuntimeError(
            "Outcome: post_github_body_and_cleanup_fail. "
            f"Primary local failure: {local_error}. "
            f"Cleanup failure: {release_error}. "
            f"GitHub issue was created: #{created_github_issue_number}. "
            f"{guidance}"
        )

    if local_error is not None:
        guidance = (
            _post_github_doctor_first_guidance(specdock_dir=specdock_dir, local_node_id=local_node_id)
            if create_write_phase_has_local_writes(local_write_phase)
            else _post_github_retry_or_cleanup_guidance(
                github_issue_number=created_github_issue_number,
                kind=kind,
                req=req,
                title=title,
                specdock_dir=specdock_dir,
            )
        )
        return RuntimeError(
            "Outcome: post_github_local_write_fail. "
            f"{local_error} "
            f"GitHub issue was created: #{created_github_issue_number}. "
            f"{guidance}"
        )

    if release_error is not None:
        guidance = _post_github_doctor_first_guidance(specdock_dir=specdock_dir, local_node_id=local_node_id)
        return RuntimeError(
            "Outcome: post_github_local_write_success_cleanup_fail. "
            f"Cleanup failure: {release_error}. "
            f"GitHub issue was created: #{created_github_issue_number}. "
            f"{guidance}"
        )

    return None


def create_node_core(
    req: CreateNodeRequest,
    ports: Ports,
    *,
    kind: Literal["initiative", "epic", "issue"],
) -> CreateNodeResult:
    mode = _resolve_github_mode(req, kind)
    title, _slug = resolve_input_title_and_slug(req.title, req.slug)
    github_issue_number = req.github_issue_number
    created_github_issue_number: int | None = None
    current_repo_slug: str | None = None
    specdock_dir: Path | None = None

    try:
        _validate_pre_github_create_inputs(req, kind=kind, mode=mode)
        specdock_dir = _resolve_specdock_dir(ports)
        if mode in ("create", "link_existing"):
            current_repo_slug = require_current_repo_slug(ports)
            _resolve_requested_repo_slug(req, current_repo_slug=current_repo_slug)

        if mode == "link_existing" and github_issue_number is None:
            raise RuntimeError("github_issue_number is required for link_existing mode")

        if mode == "create" and github_issue_number is None:
            if ports.issue_gateway is None:
                raise RuntimeError("issue_gateway is required for github issue creation")
            parent = _precheck_pre_github_create_parent(req, ports, kind=kind)
            _precheck_pre_github_create_rules_sources(kind=kind, specdock_dir=specdock_dir)
            _precheck_pre_github_create_symlink_capability(kind=kind, specdock_dir=specdock_dir, parent=parent)
            repo_root = _resolve_repo_root(ports)
            github_issue_number = ports.issue_gateway.issue_create(
                repo_root,
                title=title,
                body=_github_issue_body(kind=kind),
            )
            created_github_issue_number = int(github_issue_number)
    except Exception as exc:
        if mode == "create" and req.github_issue_number is None and created_github_issue_number is None:
            raise _build_pre_github_create_failure(error=exc) from exc
        raise

    assert specdock_dir is not None

    try:
        lock_path, lock_token = _acquire_create_lock(specdock_dir)
    except Exception as exc:
        wrapped_error = _build_post_github_create_failure(
            local_error=exc,
            release_error=None,
            created_github_issue_number=created_github_issue_number,
            kind=kind,
            req=req,
            title=title,
            specdock_dir=specdock_dir,
            local_write_phase="none",
            local_node_id=None,
            lock_acquired=False,
        )
        if wrapped_error is not None:
            raise wrapped_error from exc
        raise

    result: CreateNodeResult | None = None
    body_error: Exception | None = None
    local_write_phase: CreateWritePhase = "none"
    local_node_id: str | None = None
    try:
        graph = load_graph(ports, validate=False)
        if current_repo_slug is None:
            current_repo_slug = resolve_current_repo_slug(ports)

        today = ports.clock.today() if ports.clock is not None else date.today().isoformat()
        plan = plan_node_creation(
            replace(
                req,
                github_mode=mode,
                github_issue_number=github_issue_number,
            ),
            graph,
            kind=kind,
            specdock_dir=specdock_dir,
            today=today,
            current_repo_slug=current_repo_slug,
        )
        local_node_id = plan.meta.id
        created_paths = execute_create_plan(plan, ports)
        local_write_phase = "meta_written"
        _post_write_duplicate_guard(ports, node_id=plan.meta.id)
        local_write_phase = "post_write_verified"
        result = CreateNodeResult(
            node=_to_spec_node(plan.meta),
            created_paths=created_paths,
            warnings=[],
        )
    except Exception as exc:
        body_error = exc
        local_write_phase = resolve_create_write_phase(exc, default=local_write_phase)
    finally:
        release_error: Exception | None = None
        try:
            _release_create_lock(lock_path, lock_token, specdock_dir=specdock_dir)
        except Exception as exc:
            release_error = exc

        wrapped_outcome_error = _build_post_github_create_failure(
            local_error=body_error,
            release_error=release_error,
            created_github_issue_number=created_github_issue_number,
            kind=kind,
            req=req,
            title=title,
            specdock_dir=specdock_dir,
            local_write_phase=local_write_phase,
            local_node_id=local_node_id if create_write_phase_has_local_writes(local_write_phase) else None,
            lock_acquired=True,
        )
        if wrapped_outcome_error is not None:
            cause = body_error if body_error is not None else release_error
            if cause is not None:
                raise wrapped_outcome_error from cause
            raise wrapped_outcome_error

        if body_error is not None:
            if release_error is not None:
                raise RuntimeError(f"{body_error}; additionally {release_error}") from body_error
            raise body_error
        if release_error is not None:
            raise release_error

    if result is None:
        raise RuntimeError("create failed without result")
    return replace(result, post_sync=post_mutation_sync(ports))


def create_initiative(req: CreateNodeRequest, ports: Ports) -> CreateNodeResult:
    return create_node_core(req, ports, kind="initiative")


def create_epic(req: CreateNodeRequest, ports: Ports) -> CreateNodeResult:
    return create_node_core(req, ports, kind="epic")


def create_issue(req: CreateNodeRequest, ports: Ports) -> CreateNodeResult:
    return create_node_core(req, ports, kind="issue")
