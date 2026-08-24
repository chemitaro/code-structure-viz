from __future__ import annotations

import os
from pathlib import Path
import shutil
import stat
from typing import Any

from spec_dock_runtime.infra.clock import now_iso
from spec_dock_runtime.infra.contracts import (
    ActiveManifest,
    ActiveManifestEntry,
    ActiveManifestLoadResult,
    ActiveStateSnapshot,
    PathState,
    ProjectionTreeState,
)
from spec_dock_runtime.infra.json_store import load_json, write_json

_AGENT_DIRNAME = ".agent"
_LEGACY_WORK_DIRNAME = ".work"
_ACTIVE_DIRNAME = "active"
_ACTIVE_MANAGED_NAMES = (
    "initiative",
    "epic",
    "issue",
    "context-pack.md",
    "current-runbook.json",
    "current-runbook.md",
    "initiative.path",
    "epic.path",
    "issue.path",
)
_ACTIVE_GENERATED_FILE_NAMES = {"context-pack.md", "current-runbook.json", "current-runbook.md"}
_MANAGED_AGENT_NAMES = ("index-all.json", "tree-all.json", "index.json", "tree.json")


def _reject_hard_linked_managed_json(specdock_dir: Path) -> None:
    agent_dir = specdock_dir / _AGENT_DIRNAME
    managed_paths = (agent_dir / "active.json", *(agent_dir / name for name in _MANAGED_AGENT_NAMES))
    for path in managed_paths:
        try:
            path_stat = path.stat()
        except FileNotFoundError:
            continue
        if stat.S_ISREG(path_stat.st_mode) and path_stat.st_nlink > 1:
            managed_path = path.relative_to(specdock_dir).as_posix()
            raise RuntimeError(
                f"Refusing active state transaction: managed JSON has multiple hard links: {managed_path}"
            )


def _normalize_entry(entry: Any) -> ActiveManifestEntry | None:
    if not isinstance(entry, dict):
        return None
    raw_id = entry.get("id")
    if not isinstance(raw_id, str) or not raw_id.strip():
        return None
    raw_path = entry.get("path")
    path_value = raw_path if isinstance(raw_path, str) and raw_path.strip() else None
    return ActiveManifestEntry(
        id=raw_id.strip(),
        path=path_value,
    )


def _normalize_manifest(current: Any) -> ActiveManifest | None:
    if not isinstance(current, dict):
        return None
    if all(key in current and current[key] is None for key in ("initiative", "epic", "issue")):
        return ActiveManifest(initiative=None, epic=None, issue=None)
    initiative = _normalize_entry(current.get("initiative"))
    epic = _normalize_entry(current.get("epic"))
    issue = _normalize_entry(current.get("issue"))
    if initiative is None and epic is None and issue is None:
        return None
    return ActiveManifest(initiative=initiative, epic=epic, issue=issue)


def _manifest_to_json_obj(manifest: ActiveManifest | None) -> dict[str, Any]:
    def _entry(entry: ActiveManifestEntry | None) -> dict[str, Any] | None:
        if entry is None:
            return None
        out: dict[str, Any] = {"id": entry.id}
        if entry.path:
            out["path"] = entry.path
        return out

    return {
        "schema_version": 2,
        "updated_at": now_iso(),
        "initiative": _entry(manifest.initiative if manifest is not None else None),
        "epic": _entry(manifest.epic if manifest is not None else None),
        "issue": _entry(manifest.issue if manifest is not None else None),
    }


def _active_entry_path(repo_root: Path, entry: ActiveManifestEntry | None) -> Path | None:
    if entry is None or entry.path is None:
        return None
    raw_path = entry.path.strip()
    if not raw_path:
        return None

    parsed = Path(raw_path)
    candidates: list[Path] = []

    if parsed.is_absolute():
        try:
            rel_from_repo_root = parsed.relative_to(repo_root)
            candidates.append(repo_root / rel_from_repo_root)
        except ValueError:
            pass
        parts = parsed.parts
        for specdock_index in range(len(parts) - 1, -1, -1):
            if parts[specdock_index] != "spec-dock":
                continue
            candidates.append(repo_root / Path(*parts[specdock_index:]))
    else:
        # Canonical persisted path is repo-relative (`spec-dock/...`).
        candidates.append(repo_root / parsed)

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _active_placeholder_dir(specdock_dir: Path, layer: str) -> Path:
    path = specdock_dir / "system" / "active-none" / layer
    if not path.exists():
        raise RuntimeError(f"Missing placeholder directory: {path} (run 'spec-dock update')")
    return path


def _unlink_any(path: Path, *, allow_directory: bool = True) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
        return
    if path.is_dir():
        if not allow_directory:
            raise RuntimeError(f"Refusing to remove directory at generated file path: {path}")
        shutil.rmtree(path)


def _write_pathfile(active_dir: Path, name: str, target: Path) -> None:
    pathfile = active_dir / f"{name}.path"
    rel_target = os.path.relpath(target, start=active_dir)
    pathfile.write_text(rel_target + "\n", encoding="utf-8")


def _render_context_pack(manifest: ActiveManifest | None, *, repo_root: Path | None = None) -> str:
    del repo_root
    initiative = manifest.initiative if manifest is not None else None
    epic = manifest.epic if manifest is not None else None
    issue = manifest.issue if manifest is not None else None
    init_id = initiative.id if initiative is not None else "(none)"
    epic_id = epic.id if epic is not None else "(none)"
    issue_id = issue.id if issue is not None else "(none)"

    lines: list[str] = []
    lines.append("# Context Pack (generated)")
    lines.append("")
    lines.append("## Active")
    lines.append(f"- initiative: {init_id}")
    lines.append(f"- epic: {epic_id}")
    lines.append(f"- issue: {issue_id}")
    lines.append("")
    lines.append("## Generated state")
    lines.append("- entry: `spec-dock/.agent/active.json`")
    lines.append("- default working set: `spec-dock/.agent/index.json`")
    lines.append("- default dependency view: `spec-dock/.agent/deps-issues.json`")
    lines.append("- escalation only: `spec-dock/.agent/index-all.json`")
    lines.append("- human-oriented tree: `spec-dock/.agent/tree.json`")
    lines.append("")
    lines.append("## Read order")
    lines.append("- Start with `spec-dock/.agent/active.json`.")
    lines.append("- For normal work, read `spec-dock/.agent/index.json` and `spec-dock/.agent/deps-issues.json`.")
    lines.append("- Read `spec-dock/.agent/index-all.json` only when full-history context is needed.")
    lines.append(
        "- `spec-dock/active/context-pack.md` is human guidance that mirrors this contract; it is not the sole source of truth."
    )
    lines.append("- Then follow the active documents:")
    if initiative is not None:
        lines.append("- `spec-dock/active/initiative/requirement.md`")
        lines.append("- `spec-dock/active/initiative/design.md`")
        lines.append("- `spec-dock/active/initiative/plan.md`")
    else:
        lines.append("- `spec-dock/active/initiative/README.md`")
    if epic is not None:
        lines.append("- `spec-dock/active/epic/requirement.md`")
        lines.append("- `spec-dock/active/epic/design.md`")
        lines.append("- `spec-dock/active/epic/plan.md`")
    else:
        lines.append("- `spec-dock/active/epic/README.md`")
    if issue is not None:
        lines.append("- `spec-dock/active/issue/requirement.md`")
        lines.append("- `spec-dock/active/issue/design.md`")
        lines.append("- `spec-dock/active/issue/plan.md`")
        lines.append("- `spec-dock/active/issue/report.md`")
    else:
        lines.append("- `spec-dock/active/issue/README.md`")
    lines.append("")
    lines.append("## Commands")
    lines.append("- state (github default): `./spec-dock/scripts/spec-dock sync`")
    lines.append("- state (cache/local opt-out): `./spec-dock/scripts/spec-dock sync --no-github`")
    lines.append("- validate: `./spec-dock/scripts/spec-dock validate`")
    lines.append("")
    return "\n".join(lines) + "\n"


def load_active_manifest(specdock_dir: Path) -> ActiveManifestLoadResult:
    candidates = (
        ("agent.active", specdock_dir / ".agent" / "active.json"),
        ("legacy.work.active", specdock_dir / ".work" / "active.json"),
        ("legacy.work.current", specdock_dir / ".work" / "current.json"),
    )
    warnings: list[str] = []

    for source, path in candidates:
        if not path.exists():
            continue
        try:
            loaded = load_json(path)
        except RuntimeError:
            warnings.append(f"active_manifest_invalid_json:{source}")
            continue
        manifest = _normalize_manifest(loaded)
        if manifest is None:
            warnings.append(f"active_manifest_invalid_shape:{source}")
            continue
        return ActiveManifestLoadResult(
            manifest=manifest,
            source=source,  # type: ignore[arg-type]
            warnings=warnings,
        )

    return ActiveManifestLoadResult(manifest=None, source="none", warnings=warnings)


def load_active_manifest_no_migrate(specdock_dir: Path) -> ActiveManifestLoadResult:
    return load_active_manifest(specdock_dir)


def load_active_issue_id(specdock_dir: Path) -> str | None:
    result = load_active_manifest(specdock_dir)
    if result.manifest is None or result.manifest.issue is None:
        return None
    return result.manifest.issue.id


def write_active_manifest(specdock_dir: Path, manifest: ActiveManifest) -> ActiveManifest:
    agent_dir = specdock_dir / _AGENT_DIRNAME
    legacy_work_dir = specdock_dir / _LEGACY_WORK_DIRNAME
    agent_dir.mkdir(parents=True, exist_ok=True)
    write_json(agent_dir / "active.json", _manifest_to_json_obj(manifest))
    (legacy_work_dir / "active.json").unlink(missing_ok=True)
    (legacy_work_dir / "current.json").unlink(missing_ok=True)
    return manifest


def apply_active_pointers(specdock_dir: Path, manifest: ActiveManifest | None, rendered_context_pack: str) -> None:
    repo_root = specdock_dir.parent
    active_dir = specdock_dir / _ACTIVE_DIRNAME
    active_dir.mkdir(parents=True, exist_ok=True)

    for name in _ACTIVE_MANAGED_NAMES:
        _unlink_any(active_dir / name, allow_directory=name not in _ACTIVE_GENERATED_FILE_NAMES)

    def _target_dir(layer: str) -> Path:
        if manifest is None:
            return _active_placeholder_dir(specdock_dir, layer)
        entry = getattr(manifest, layer)
        return _active_entry_path(repo_root, entry) or _active_placeholder_dir(specdock_dir, layer)

    def _symlink(name: str, target: Path) -> None:
        link = active_dir / name
        rel_target = os.path.relpath(target, start=active_dir)
        try:
            Path(link).symlink_to(rel_target)
        except OSError:
            _write_pathfile(active_dir, name, target)

    _symlink("initiative", _target_dir("initiative"))
    _symlink("epic", _target_dir("epic"))
    _symlink("issue", _target_dir("issue"))
    (active_dir / "context-pack.md").write_text(rendered_context_pack, encoding="utf-8")


def patch_agent_state_active_fields(specdock_dir: Path, manifest: ActiveManifest | None) -> None:
    agent_dir = specdock_dir / _AGENT_DIRNAME
    active_obj = _manifest_to_json_obj(manifest)
    for name in _MANAGED_AGENT_NAMES:
        path = agent_dir / name
        if not path.is_file():
            continue
        loaded = load_json(path)
        if not isinstance(loaded, dict):
            raise RuntimeError(f"invalid JSON shape (expected object): {path}")
        loaded["active"] = active_obj
        write_json(path, loaded)


def _snapshot_tree_entry(
    path: Path,
    relative: str,
    state: ProjectionTreeState,
) -> None:
    if path.is_symlink():
        state[relative] = ("symlink", str(path.readlink()))
        return
    if path.is_file():
        state[relative] = ("file", path.read_bytes())
        return
    if path.is_dir():
        state[relative] = ("directory", None)
        for child in sorted(path.iterdir(), key=lambda item: item.name):
            child_relative = child.name if relative == "." else f"{relative}/{child.name}"
            _snapshot_tree_entry(child, child_relative, state)


def _snapshot_projection_tree(
    root: Path,
) -> ProjectionTreeState:
    state: ProjectionTreeState = {}
    _snapshot_tree_entry(root, ".", state)
    return state


def _restore_projection_entries(
    root: Path,
    state: ProjectionTreeState,
) -> None:
    for relative in sorted(state, key=lambda value: (value.count("/"), value)):
        kind, payload = state[relative]
        path = root if relative == "." else root / relative
        if kind == "directory":
            path.mkdir(parents=True, exist_ok=True)
        elif kind == "file":
            if not isinstance(payload, bytes):
                raise RuntimeError(f"Invalid active projection file snapshot: {relative}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        elif kind == "symlink":
            if not isinstance(payload, str):
                raise RuntimeError(f"Invalid active projection symlink snapshot: {relative}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.symlink_to(payload)
        else:
            raise RuntimeError(f"Invalid active projection snapshot kind: {relative}: {kind}")


def _restore_projection_tree(
    root: Path,
    state: ProjectionTreeState,
) -> None:
    _unlink_any(root)
    _restore_projection_entries(root, state)


def _resolve_symlink_target(path: Path, target: str) -> Path:
    parsed = Path(target)
    if not parsed.is_absolute():
        parsed = path.parent / parsed
    return parsed.resolve(strict=False)


def _snapshot_managed_projection_tree(
    root: Path,
) -> ProjectionTreeState:
    state: ProjectionTreeState = {}
    for name in _ACTIVE_MANAGED_NAMES:
        _snapshot_tree_entry(root / name, name, state)
    return state


def _restore_managed_projection_tree(
    root: Path,
    state: ProjectionTreeState,
) -> None:
    if not root.is_dir() or root.is_symlink():
        raise RuntimeError(f"Active projection symlink target is no longer a directory: {root}")
    for name in _ACTIVE_MANAGED_NAMES:
        _unlink_any(root / name)
    _restore_projection_entries(root, state)


def _snapshot_path(path: Path) -> PathState:
    if path.is_symlink():
        return ("symlink", str(path.readlink()))
    if path.is_file():
        return ("file", path.read_bytes())
    if path.is_dir():
        return ("directory", _snapshot_projection_tree(path))
    return ("missing", None)


def _snapshot_path_symlink_target(
    path: Path,
    state: PathState,
) -> tuple[str, PathState] | None:
    kind, payload = state
    if kind != "symlink":
        return None
    if not isinstance(payload, str):
        raise RuntimeError(f"Invalid symlink snapshot: {path}")
    target_path = _resolve_symlink_target(path, payload)
    target_state = _snapshot_path(target_path)
    if target_state[0] == "directory":
        return None
    return (str(target_path), target_state)


def _restore_path(path: Path, state: PathState) -> None:
    _unlink_any(path)
    kind, payload = state
    if kind == "missing":
        return
    if kind == "directory":
        if not isinstance(payload, dict):
            raise RuntimeError(f"Invalid directory snapshot: {path}")
        _restore_projection_entries(path, payload)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if kind == "file":
        if not isinstance(payload, bytes):
            raise RuntimeError(f"Invalid file snapshot: {path}")
        path.write_bytes(payload)
        return
    if kind == "symlink":
        if not isinstance(payload, str):
            raise RuntimeError(f"Invalid symlink snapshot: {path}")
        path.symlink_to(payload)
        return
    raise RuntimeError(f"Invalid path snapshot kind: {path}: {kind}")


def snapshot_current_state(specdock_dir: Path) -> ActiveStateSnapshot:
    _reject_hard_linked_managed_json(specdock_dir)
    agent_dir = specdock_dir / _AGENT_DIRNAME
    legacy_work_dir = specdock_dir / _LEGACY_WORK_DIRNAME
    active_json_path = agent_dir / "active.json"
    legacy_active_json_path = legacy_work_dir / "active.json"
    legacy_current_json_path = legacy_work_dir / "current.json"
    context_pack_path = specdock_dir / _ACTIVE_DIRNAME / "context-pack.md"

    context_pack_text = context_pack_path.read_text(encoding="utf-8") if context_pack_path.exists() else None
    manifest = load_active_manifest(specdock_dir).manifest
    active_json_state = _snapshot_path(active_json_path)
    active_projection_state = _snapshot_projection_tree(specdock_dir / _ACTIVE_DIRNAME)
    active_projection_symlink_target_state = None
    projection_root = active_projection_state.get(".")
    if projection_root is not None and projection_root[0] == "symlink":
        projection_target = projection_root[1]
        if not isinstance(projection_target, str):
            raise RuntimeError("Invalid active projection root symlink snapshot")
        projection_target_path = _resolve_symlink_target(specdock_dir / _ACTIVE_DIRNAME, projection_target)
        if projection_target_path.is_dir():
            active_projection_symlink_target_state = (
                str(projection_target_path),
                _snapshot_managed_projection_tree(projection_target_path),
            )

    managed_agent_path_states = {}
    managed_agent_symlink_target_states = {}
    for name in _MANAGED_AGENT_NAMES:
        path = agent_dir / name
        path_state = _snapshot_path(path)
        managed_agent_path_states[name] = path_state
        symlink_target_state = _snapshot_path_symlink_target(path, path_state)
        if symlink_target_state is not None:
            managed_agent_symlink_target_states[name] = symlink_target_state
        if path.is_file():
            loaded = load_json(path)
            if not isinstance(loaded, dict):
                raise RuntimeError(f"invalid JSON shape (expected object): {path}")

    return ActiveStateSnapshot(
        manifest=manifest,
        context_pack_text=context_pack_text,
        active_json_text=None,
        managed_agent_state={},
        active_projection_state=active_projection_state,
        legacy_active_json_state=_snapshot_path(legacy_active_json_path),
        legacy_current_json_state=_snapshot_path(legacy_current_json_path),
        active_json_state=active_json_state,
        active_json_symlink_target_state=_snapshot_path_symlink_target(active_json_path, active_json_state),
        active_projection_symlink_target_state=active_projection_symlink_target_state,
        managed_agent_path_states=managed_agent_path_states,
        managed_agent_symlink_target_states=managed_agent_symlink_target_states,
    )


def restore_previous_state(specdock_dir: Path, snapshot: ActiveStateSnapshot) -> None:
    agent_dir = specdock_dir / _AGENT_DIRNAME
    legacy_work_dir = specdock_dir / _LEGACY_WORK_DIRNAME
    active_dir = specdock_dir / _ACTIVE_DIRNAME
    active_json_path = agent_dir / "active.json"
    legacy_active_json_path = legacy_work_dir / "active.json"
    legacy_current_json_path = legacy_work_dir / "current.json"
    context_pack_path = active_dir / "context-pack.md"

    if snapshot.active_json_symlink_target_state is not None:
        target_path, target_state = snapshot.active_json_symlink_target_state
        _restore_path(Path(target_path), target_state)
    if snapshot.active_json_state is not None:
        _restore_path(active_json_path, snapshot.active_json_state)
    elif snapshot.active_json_text is None:
        _unlink_any(active_json_path)
    else:
        active_json_path.parent.mkdir(parents=True, exist_ok=True)
        active_json_path.write_text(snapshot.active_json_text, encoding="utf-8")

    for path, previous_state in (
        (legacy_active_json_path, snapshot.legacy_active_json_state),
        (legacy_current_json_path, snapshot.legacy_current_json_state),
    ):
        if previous_state is None:
            _unlink_any(path)
        else:
            _restore_path(path, previous_state)

    if snapshot.active_projection_state is None:
        if snapshot.context_pack_text is None:
            context_pack_path.unlink(missing_ok=True)
        else:
            context_pack_path.parent.mkdir(parents=True, exist_ok=True)
            context_pack_path.write_text(snapshot.context_pack_text, encoding="utf-8")

    if snapshot.managed_agent_path_states is not None:
        target_states = snapshot.managed_agent_symlink_target_states or {}
        for name, previous_state in snapshot.managed_agent_path_states.items():
            target_state = target_states.get(name)
            if target_state is not None:
                target_path, target_path_state = target_state
                _restore_path(Path(target_path), target_path_state)
            _restore_path(agent_dir / name, previous_state)
    else:
        for name, previous_text in snapshot.managed_agent_state.items():
            path = agent_dir / name
            if previous_text is None:
                path.unlink(missing_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(previous_text, encoding="utf-8")

    if snapshot.active_projection_state is not None:
        if snapshot.active_projection_symlink_target_state is not None:
            target_path, target_state = snapshot.active_projection_symlink_target_state
            _restore_managed_projection_tree(Path(target_path), target_state)
        _restore_projection_tree(active_dir, snapshot.active_projection_state)
    else:
        restored_manifest = snapshot.manifest
        restored_context_pack = snapshot.context_pack_text
        if restored_context_pack is None:
            restored_context_pack = _render_context_pack(restored_manifest, repo_root=specdock_dir.parent)
        apply_active_pointers(specdock_dir, restored_manifest, restored_context_pack)
