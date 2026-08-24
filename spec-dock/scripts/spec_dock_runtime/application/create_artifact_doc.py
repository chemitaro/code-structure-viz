from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
import stat
from typing import TYPE_CHECKING

from spec_dock_runtime.application.contracts import CreateArtifactDocRequest, CreateArtifactDocResult
from spec_dock_runtime.application.create_node import (
    _acquire_create_lock,
    _prefix_for_kind,
    _release_create_lock,
    _replacements,
    _resolve_specdock_dir,
    _resolve_template_scaffolder,
    load_graph,
)
from spec_dock_runtime.domain.artifacts import (
    CURRENT_CREATABLE_ARTIFACT_TYPES,
    allocate_artifact_filename_for_timestamp,
    artifact_id_from_path,
    can_create_artifact_type,
    is_ambiguous_blank_artifact_slug,
    scan_artifact_duplicate_state,
)
from spec_dock_runtime.domain.ids import resolve_id_input, slugify, validate_input_slug_kebab

if TYPE_CHECKING:
    from spec_dock_runtime.application.ports import Ports
    from spec_dock_runtime.domain.models import SpecGraph, SpecNode


@dataclass(frozen=True)
class ArtifactSetupTarget:
    path: Path
    artifacts_dir: Path
    rules_kind: str


@dataclass
class ArtifactMutationJournal:
    artifacts_dir: Path
    rules_path: Path
    artifacts_dir_preflight_identity: PathIdentity | None = None
    artifacts_dir_identity: PathIdentity | None = None
    artifacts_dir_descriptor: int | None = None
    artifacts_dir_open_identity: PathIdentity | None = None
    rules_path_identity: PathIdentity | None = None
    temp_path: Path | None = None
    temp_path_identity: PathIdentity | None = None
    dest_path: Path | None = None
    dest_path_identity: PathIdentity | None = None


@dataclass(frozen=True)
class PathIdentity:
    device: int
    inode: int
    mode: int


def create_artifact_doc(
    req: CreateArtifactDocRequest,
    ports: Ports,
) -> CreateArtifactDocResult:
    template_scaffolder = _resolve_template_scaffolder(ports)
    specdock_dir = _resolve_specdock_dir(ports)
    graph = load_graph(ports, validate=False)

    artifact_type, title, slug = _normalize_artifact_inputs(req)
    scope = _resolve_scope_node(req, graph)
    _ensure_scope_path_is_safe(scope=scope, specdock_dir=specdock_dir)
    artifacts_dir = scope.path / "artifacts"
    timestamp = _format_artifact_timestamp(ports.clock.now_iso() if ports.clock is not None else None)
    template_path, template_text = _resolve_artifact_template_text(
        artifact_type=artifact_type,
        specdock_dir=specdock_dir,
    )
    del template_path

    lock_path, lock_token = _acquire_create_lock(specdock_dir)
    result: CreateArtifactDocResult | None = None
    body_error: Exception | None = None
    cleanup_error: Exception | None = None
    journal: ArtifactMutationJournal | None = None
    try:
        dest_path, artifact_id, artifacts_dir_preflight_identity = _allocate_artifact_destination_under_create_lock(
            scope=scope,
            specdock_dir=specdock_dir,
            artifacts_dir=artifacts_dir,
            timestamp=timestamp,
            artifact_type=artifact_type,
            slug=slug,
        )
        rules_path = artifacts_dir / "rules.md"
        journal = ArtifactMutationJournal(
            artifacts_dir=artifacts_dir,
            rules_path=rules_path,
            artifacts_dir_preflight_identity=artifacts_dir_preflight_identity,
            dest_path=dest_path,
        )
        rendered_text = template_scaffolder.render_text(
            template_text,
            _artifact_replacements(
                scope=scope,
                artifact_id=artifact_id,
                artifact_type=artifact_type,
                title=title,
            ),
        )
        setup_target = ArtifactSetupTarget(
            path=scope.path,
            artifacts_dir=artifacts_dir,
            rules_kind=scope.kind,
        )
        _ensure_artifacts_setup_for_attempt(
            target=setup_target,
            specdock_dir=specdock_dir,
            journal=journal,
        )
        assert journal.artifacts_dir_descriptor is not None
        temp_fd, temp_path, temp_identity = _claim_artifact_temp_path(
            dest_path,
            directory_descriptor=journal.artifacts_dir_descriptor,
        )
        journal.temp_path = temp_path
        journal.temp_path_identity = temp_identity
        _write_and_close_claimed_artifact_temp(temp_fd, rendered_text)
        _require_artifacts_directory_path_identity(journal)
        _publish_artifact_temp_no_replace(
            temp_path=temp_path,
            dest_path=dest_path,
            expected_identity=temp_identity,
            directory_descriptor=journal.artifacts_dir_descriptor,
        )
        journal.dest_path_identity = temp_identity
        _require_entry_identity(
            journal.artifacts_dir_descriptor,
            dest_path,
            temp_identity,
            label="published artifact",
            require_regular=True,
        )
        _remove_owned_path_or_raise(
            temp_path,
            temp_identity,
            label="artifact temporary file",
            is_directory=False,
            directory_descriptor=journal.artifacts_dir_descriptor,
        )
        journal.temp_path_identity = None
        written_artifact_id = artifact_id_from_path(dest_path)
        _require_artifacts_directory_path_identity(journal)
        duplicate_error, artifact_ids = scan_artifact_duplicate_state(artifacts_dir)
        _require_artifacts_directory_path_identity(journal)
        if duplicate_error is not None:
            raise RuntimeError(f"post-write duplicate guard failed: {duplicate_error}")
        if written_artifact_id not in artifact_ids:
            raise RuntimeError(
                f"post-write duplicate guard failed: created artifact id not found: {written_artifact_id}"
            )
        _require_entry_identity(
            journal.artifacts_dir_descriptor,
            dest_path,
            temp_identity,
            label="published artifact",
            require_regular=True,
        )
        result = CreateArtifactDocResult(
            artifact_id=written_artifact_id,
            artifact_type=artifact_type,
            scope_node_id=scope.id,
            path=dest_path,
            warnings=[],
        )
    except Exception as exc:
        body_error = exc
        if journal is not None:
            cleanup_error = _rollback_artifact_attempt(journal)
    finally:
        if journal is not None and journal.artifacts_dir_descriptor is not None:
            try:
                _close_artifacts_directory(journal)
            except OSError as close_exc:
                if result is not None and body_error is None:
                    result.warnings.append(
                        _committed_cleanup_warning(
                            label="artifact directory close failed",
                            error=close_exc,
                        )
                    )
                elif body_error is None:
                    body_error = close_exc
                else:
                    cleanup_error = _combine_cleanup_errors(
                        cleanup_error,
                        close_exc,
                        label="artifact directory close failed",
                    )
        try:
            _release_create_lock(lock_path, lock_token, specdock_dir=specdock_dir)
        except Exception as release_exc:
            if result is not None and body_error is None:
                result.warnings.append(
                    _committed_cleanup_warning(
                        label="create lock release failed",
                        error=release_exc,
                    )
                )
            elif body_error is None:
                raise
            else:
                cleanup_error = _combine_cleanup_errors(
                    cleanup_error,
                    release_exc,
                    label="create lock release failed",
                )
    if body_error is not None:
        if cleanup_error is not None:
            raise body_error from cleanup_error
        raise body_error
    assert result is not None
    return result


def _allocate_artifact_destination_under_create_lock(
    *,
    scope: SpecNode,
    specdock_dir: Path,
    artifacts_dir: Path,
    timestamp: str,
    artifact_type: str,
    slug: str,
) -> tuple[Path, str, PathIdentity | None]:
    setup_target = ArtifactSetupTarget(
        path=scope.path,
        artifacts_dir=artifacts_dir,
        rules_kind=scope.kind,
    )
    _preflight_artifacts_setup_for_target(target=setup_target, specdock_dir=specdock_dir)
    artifacts_dir_preflight_identity = _lstat_identity(artifacts_dir)
    duplicate_error, _artifact_ids = scan_artifact_duplicate_state(artifacts_dir)
    if duplicate_error is not None:
        raise RuntimeError(duplicate_error)
    dest_path, artifact_id = allocate_artifact_filename_for_timestamp(
        artifacts_dir,
        timestamp=timestamp,
        artifact_type=artifact_type,
        slug=slug,
    )
    if os.path.lexists(dest_path):
        raise RuntimeError(f"Artifact already exists: {dest_path}")
    return dest_path, artifact_id, artifacts_dir_preflight_identity


def _normalize_artifact_inputs(req: CreateArtifactDocRequest) -> tuple[str, str, str]:
    artifact_type = str(req.artifact_type).strip().lower()
    if not can_create_artifact_type(artifact_type):
        allowed = ", ".join(CURRENT_CREATABLE_ARTIFACT_TYPES)
        raise RuntimeError(
            f"Cannot create artifact type: {artifact_type or '<empty>'}. Current artifact types: {allowed}"
        )

    title = str(req.title).strip()
    if not title:
        raise RuntimeError("--title is required")
    slug = str(req.slug).strip() if req.slug is not None else slugify(title)
    if not slug:
        raise RuntimeError("Failed to derive slug from title. Pass --slug explicitly.")
    normalized_slug = validate_input_slug_kebab(slug, field="--slug")
    if artifact_type == "blank" and is_ambiguous_blank_artifact_slug(normalized_slug):
        raise RuntimeError(
            "Ambiguous blank artifact slug: "
            f"{normalized_slug}. "
            "Blank artifact slugs must not start with a supported artifact type prefix."
        )
    return artifact_type, title, normalized_slug


def _resolve_scope_node(req: CreateArtifactDocRequest, graph: SpecGraph) -> SpecNode:
    scope_node_id = req.scope_node_id
    if req.scope_kind is not None:
        scope_prefix = _prefix_for_kind(req.scope_kind)
        scope_node_id = resolve_id_input(
            req.scope_node_id,
            prefix=scope_prefix,
            field=f"--{req.scope_kind}",
            nodes=graph.nodes_by_id,
        )
    scope = graph.nodes_by_id.get(scope_node_id)
    if scope is None:
        raise RuntimeError(f"Scope node not found: {scope_node_id}")
    if req.scope_kind is not None and scope.kind != req.scope_kind:
        raise RuntimeError(f"Scope kind mismatch: expected {req.scope_kind}, got {scope.kind}")
    if scope.kind not in ("initiative", "epic", "issue"):
        raise RuntimeError(f"Unsupported scope kind for artifact docs: {scope.kind}")
    return scope


def _ensure_scope_path_is_safe(*, scope: SpecNode, specdock_dir: Path) -> None:
    initiatives_root = specdock_dir / "initiatives"
    if initiatives_root.is_symlink():
        raise RuntimeError(f"Initiatives root is symlinked: {initiatives_root}")
    lexical_root = initiatives_root.absolute()
    lexical_scope = scope.path.absolute()
    try:
        relative_scope = lexical_scope.relative_to(lexical_root)
    except ValueError:
        raise RuntimeError(f"Scope path escapes spec-dock initiatives: {scope.id}") from None

    resolved_root = initiatives_root.resolve(strict=False)
    resolved_scope = scope.path.resolve(strict=False)
    try:
        resolved_scope.relative_to(resolved_root)
    except ValueError:
        raise RuntimeError(f"Scope path escapes spec-dock initiatives: {scope.id}") from None

    current = lexical_root
    for component in relative_scope.parts:
        current /= component
        if current.is_symlink():
            raise RuntimeError(f"Scope path contains a symlink: {scope.id}")

    meta_parent = scope.meta_path.absolute().parent
    if meta_parent != lexical_scope:
        raise RuntimeError(f"Scope metadata path mismatch: {scope.id}")


def _format_artifact_timestamp(now_iso: str | None = None) -> str:
    if now_iso is None:
        dt = datetime.now(timezone.utc)
    else:
        normalized = now_iso.strip()
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y%m%dt%H%M%S") + "z"


def _format_artifact_date_from_id(artifact_id: str) -> str:
    timestamp = artifact_id.split("-", 1)[0]
    return datetime.strptime(timestamp, "%Y%m%dt%H%M%Sz").date().isoformat()


def _resolve_artifact_template_text(
    *,
    artifact_type: str,
    specdock_dir: Path,
) -> tuple[Path, str]:
    path = specdock_dir / "templates" / "artifacts" / f"{artifact_type}.md"
    return path, _load_required_template_text(path, label=f"artifact {artifact_type}")


def _load_required_template_text(path: Path, *, label: str) -> str:
    if path.is_symlink():
        raise RuntimeError(f"Template is symlinked: {path}")
    if path.exists() and not path.is_file():
        raise RuntimeError(f"Template is not a file: {path}")
    if not path.is_file():
        raise RuntimeError(f"Missing template source for {label}: {path}")
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise RuntimeError(f"Template is empty: {path}")
    return text


def _preflight_artifacts_dir(artifacts_dir: Path) -> PathIdentity | None:
    artifacts_dir_identity = _lstat_identity(artifacts_dir)
    if artifacts_dir_identity is not None and not stat.S_ISDIR(artifacts_dir_identity.mode):
        raise RuntimeError(f"Destination already exists: {artifacts_dir}")
    parent = artifacts_dir.parent
    parent_identity = _lstat_identity(parent)
    if parent_identity is None or not stat.S_ISDIR(parent_identity.mode):
        raise RuntimeError(f"Destination already exists: {parent}")
    return artifacts_dir_identity


def _rules_source_path(*, scope: SpecNode, specdock_dir: Path) -> Path:
    return specdock_dir / "docs" / "rules" / scope.kind / "artifacts.md"


def _preflight_artifacts_rules(*, scope: SpecNode, specdock_dir: Path, artifacts_dir: Path) -> None:
    source = _rules_source_path(scope=scope, specdock_dir=specdock_dir)
    if source.is_symlink():
        raise RuntimeError(f"Missing rules source: {source}")
    if not source.is_file():
        raise RuntimeError(f"Missing rules source: {source}")
    link_path = artifacts_dir / "rules.md"
    if not os.path.lexists(link_path):
        return
    if not link_path.is_symlink():
        raise RuntimeError(f"Destination already exists: {link_path}")
    if not link_path.exists():
        raise RuntimeError(f"Broken artifact rules symlink: {link_path}")
    if link_path.resolve() != source.resolve():
        raise RuntimeError(f"Artifact rules symlink points to wrong target: {link_path}")


def _ensure_artifacts_setup_for_attempt(
    *,
    target: ArtifactSetupTarget,
    specdock_dir: Path,
    journal: ArtifactMutationJournal,
) -> None:
    _preflight_artifacts_setup_for_target(target=target, specdock_dir=specdock_dir)
    expected_directory_identity = journal.artifacts_dir_preflight_identity
    if not os.path.lexists(target.artifacts_dir):
        try:
            target.artifacts_dir.mkdir(parents=False, exist_ok=False)
        except FileExistsError:
            expected_directory_identity = _preflight_artifacts_dir(target.artifacts_dir)
            if expected_directory_identity is None:
                raise RuntimeError(
                    f"Artifact directory identity missing after creation race: {target.artifacts_dir}"
                ) from None
        else:
            journal.artifacts_dir_identity = _require_created_path_identity(
                target.artifacts_dir,
                label="artifact directory",
                require_directory=True,
            )
            expected_directory_identity = journal.artifacts_dir_identity
    directory_descriptor, directory_identity = _open_artifacts_directory(
        target.artifacts_dir,
        expected_identity=expected_directory_identity,
    )
    journal.artifacts_dir_descriptor = directory_descriptor
    journal.artifacts_dir_open_identity = directory_identity
    _require_artifacts_directory_path_identity(journal)

    source = specdock_dir / "docs" / "rules" / target.rules_kind / "artifacts.md"
    link_path = target.artifacts_dir / "rules.md"
    if _lstat_entry_identity(directory_descriptor, link_path.name) is None:
        try:
            os.symlink(
                os.path.relpath(source, start=target.artifacts_dir),
                link_path.name,
                dir_fd=directory_descriptor,
            )
        except FileExistsError:
            _require_artifact_rules_entry(
                directory_descriptor=directory_descriptor,
                artifacts_dir=target.artifacts_dir,
                source=source,
            )
        else:
            journal.rules_path_identity = _require_created_entry_identity(
                directory_descriptor,
                link_path,
                label="artifact rules link",
                require_symlink=True,
            )
    _require_artifact_rules_entry(
        directory_descriptor=directory_descriptor,
        artifacts_dir=target.artifacts_dir,
        source=source,
    )
    _require_artifacts_directory_path_identity(journal)


def _open_artifacts_directory(
    artifacts_dir: Path,
    *,
    expected_identity: PathIdentity | None,
) -> tuple[int, PathIdentity]:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(artifacts_dir, flags)
    except OSError as exc:
        raise RuntimeError(f"Artifact directory identity changed: {artifacts_dir}: {exc}") from None
    try:
        identity = _identity_from_stat_result(os.fstat(descriptor))
        if not stat.S_ISDIR(identity.mode):
            raise RuntimeError(f"Artifact directory is not a directory: {artifacts_dir}")
        if expected_identity is not None and identity != expected_identity:
            raise RuntimeError(f"Artifact directory identity changed: {artifacts_dir}")
        current = _lstat_identity(artifacts_dir)
        if current != identity:
            raise RuntimeError(f"Artifact directory identity changed: {artifacts_dir}")
    except Exception as exc:
        try:
            os.close(descriptor)
        except OSError as close_exc:
            raise exc from close_exc
        raise
    return descriptor, identity


def _claim_artifact_temp_path(
    dest_path: Path,
    *,
    directory_descriptor: int,
) -> tuple[int, Path, PathIdentity]:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    for suffix in range(100):
        suffix_token = "" if suffix == 0 else f"-{suffix:02d}"
        candidate = dest_path.with_name(f".{dest_path.name}{suffix_token}.tmp")
        try:
            descriptor = os.open(candidate.name, flags, 0o666, dir_fd=directory_descriptor)
        except FileExistsError:
            continue
        identity = _identity_from_stat_result(os.fstat(descriptor))
        if not stat.S_ISREG(identity.mode):
            os.close(descriptor)
            raise RuntimeError(f"Artifact temporary claim is not a regular file: {candidate}")
        return descriptor, candidate, identity
    raise RuntimeError(f"Artifact temporary path exhaustion under {dest_path.parent}")


def _identity_from_stat_result(result: os.stat_result) -> PathIdentity:
    return PathIdentity(device=result.st_dev, inode=result.st_ino, mode=result.st_mode)


def _lstat_identity(path: Path) -> PathIdentity | None:
    try:
        return _identity_from_stat_result(os.lstat(path))
    except FileNotFoundError:
        return None


def _lstat_entry_identity(directory_descriptor: int, name: str) -> PathIdentity | None:
    try:
        result = os.stat(name, dir_fd=directory_descriptor, follow_symlinks=False)
    except FileNotFoundError:
        return None
    return _identity_from_stat_result(result)


def _require_created_path_identity(
    path: Path,
    *,
    label: str,
    require_directory: bool = False,
    require_symlink: bool = False,
) -> PathIdentity:
    identity = _lstat_identity(path)
    if identity is None:
        raise RuntimeError(f"{label} identity missing after creation: {path}")
    if require_directory and not stat.S_ISDIR(identity.mode):
        raise RuntimeError(f"{label} is not a directory after creation: {path}")
    if require_symlink and not stat.S_ISLNK(identity.mode):
        raise RuntimeError(f"{label} is not a symlink after creation: {path}")
    return identity


def _require_created_entry_identity(
    directory_descriptor: int,
    path: Path,
    *,
    label: str,
    require_symlink: bool = False,
) -> PathIdentity:
    identity = _lstat_entry_identity(directory_descriptor, path.name)
    if identity is None:
        raise RuntimeError(f"{label} identity missing after creation: {path}")
    if require_symlink and not stat.S_ISLNK(identity.mode):
        raise RuntimeError(f"{label} is not a symlink after creation: {path}")
    return identity


def _require_artifact_rules_entry(
    *,
    directory_descriptor: int,
    artifacts_dir: Path,
    source: Path,
) -> None:
    link_path = artifacts_dir / "rules.md"
    identity = _lstat_entry_identity(directory_descriptor, link_path.name)
    if identity is None:
        raise RuntimeError(f"Artifact rules link identity missing: {link_path}")
    if not stat.S_ISLNK(identity.mode):
        raise RuntimeError(f"Destination already exists: {link_path}")
    target = os.readlink(link_path.name, dir_fd=directory_descriptor)
    if Path(target).is_absolute():
        target_matches = os.path.realpath(target) == os.path.realpath(source)
    else:
        expected = os.path.normpath(os.path.relpath(source, start=artifacts_dir))
        target_matches = os.path.normpath(target) == expected
    if not target_matches:
        raise RuntimeError(f"Artifact rules symlink points to wrong target: {link_path}")


def _require_artifacts_directory_path_identity(journal: ArtifactMutationJournal) -> None:
    expected = journal.artifacts_dir_open_identity
    if expected is None:
        raise RuntimeError(f"Artifact directory identity missing: {journal.artifacts_dir}")
    current = _lstat_identity(journal.artifacts_dir)
    if current != expected:
        raise RuntimeError(f"Artifact directory identity changed: {journal.artifacts_dir}")


def _require_entry_identity(
    directory_descriptor: int,
    path: Path,
    expected_identity: PathIdentity,
    *,
    label: str,
    require_regular: bool = False,
) -> None:
    current = _lstat_entry_identity(directory_descriptor, path.name)
    if current is None:
        raise RuntimeError(f"{label} identity missing: {path}")
    if current != expected_identity:
        raise RuntimeError(f"{label} identity changed: {path}")
    if require_regular and not stat.S_ISREG(current.mode):
        raise RuntimeError(f"{label} is not a regular file: {path}")


def _write_and_close_claimed_artifact_temp(descriptor: int, text: str) -> None:
    write_error: Exception | None = None
    try:
        _write_claimed_artifact_temp(descriptor, text)
    except Exception as exc:
        write_error = exc
    try:
        os.close(descriptor)
    except OSError as close_exc:
        if write_error is None:
            raise
        raise write_error from close_exc
    if write_error is not None:
        raise write_error


def _write_claimed_artifact_temp(descriptor: int, text: str) -> None:
    content = text.encode("utf-8")
    offset = 0
    while offset < len(content):
        written = os.write(descriptor, content[offset:])
        if written <= 0:
            raise OSError("Artifact temporary write made no progress")
        offset += written
    os.fsync(descriptor)


def _publish_artifact_temp_no_replace(
    *,
    temp_path: Path,
    dest_path: Path,
    expected_identity: PathIdentity,
    directory_descriptor: int,
) -> None:
    _require_entry_identity(
        directory_descriptor,
        temp_path,
        expected_identity,
        label="artifact temporary file",
        require_regular=True,
    )
    try:
        os.link(
            temp_path.name,
            dest_path.name,
            src_dir_fd=directory_descriptor,
            dst_dir_fd=directory_descriptor,
            follow_symlinks=False,
        )
    except FileExistsError:
        raise RuntimeError(f"Artifact already exists: {dest_path}") from None


def _rollback_artifact_attempt(journal: ArtifactMutationJournal) -> Exception | None:
    errors: list[str] = []
    directory_descriptor = journal.artifacts_dir_descriptor
    if directory_descriptor is None:
        if journal.artifacts_dir_identity is not None:
            _remove_owned_path(
                journal.artifacts_dir,
                journal.artifacts_dir_identity,
                label="artifact directory",
                is_directory=True,
                errors=errors,
                directory_descriptor=None,
            )
        if not errors:
            return None
        return RuntimeError("Artifact rollback failed: " + "; ".join(errors))
    if journal.dest_path_identity is not None and journal.dest_path is not None:
        _remove_owned_path(
            journal.dest_path,
            journal.dest_path_identity,
            label="published artifact",
            is_directory=False,
            errors=errors,
            directory_descriptor=directory_descriptor,
        )
    if journal.temp_path_identity is not None and journal.temp_path is not None:
        _remove_owned_path(
            journal.temp_path,
            journal.temp_path_identity,
            label="artifact temporary file",
            is_directory=False,
            errors=errors,
            directory_descriptor=directory_descriptor,
        )
    if journal.rules_path_identity is not None:
        _remove_owned_path(
            journal.rules_path,
            journal.rules_path_identity,
            label="artifact rules link",
            is_directory=False,
            errors=errors,
            directory_descriptor=directory_descriptor,
        )
    try:
        _require_artifacts_directory_path_identity(journal)
    except RuntimeError as exc:
        errors.append(str(exc))
    if journal.artifacts_dir_identity is not None:
        _remove_owned_path(
            journal.artifacts_dir,
            journal.artifacts_dir_identity,
            label="artifact directory",
            is_directory=True,
            errors=errors,
            directory_descriptor=None,
        )
    if not errors:
        return None
    return RuntimeError("Artifact rollback failed: " + "; ".join(errors))


def _remove_owned_path_or_raise(
    path: Path,
    expected_identity: PathIdentity,
    *,
    label: str,
    is_directory: bool,
    directory_descriptor: int | None = None,
) -> None:
    errors: list[str] = []
    _remove_owned_path(
        path,
        expected_identity,
        label=label,
        is_directory=is_directory,
        errors=errors,
        directory_descriptor=directory_descriptor,
    )
    if errors:
        raise RuntimeError("Artifact cleanup failed: " + "; ".join(errors))


def _remove_owned_path(
    path: Path,
    expected_identity: PathIdentity,
    *,
    label: str,
    is_directory: bool,
    errors: list[str],
    directory_descriptor: int | None,
) -> None:
    if directory_descriptor is not None:
        current = _lstat_entry_identity(directory_descriptor, path.name)
        if current is None:
            errors.append(f"{label} {path}: identity missing; preserved")
            return
        if current != expected_identity:
            errors.append(f"{label} {path}: identity changed; preserved")
            return
        try:
            if is_directory:
                os.rmdir(path.name, dir_fd=directory_descriptor)
            else:
                os.unlink(path.name, dir_fd=directory_descriptor)
        except OSError as exc:
            errors.append(f"{label} {path}: {exc}")
        return

    parent_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    parent_flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        parent_descriptor = os.open(path.parent, parent_flags)
    except OSError as exc:
        errors.append(f"{label} {path}: failed to open parent for cleanup: {exc}")
        return
    try:
        try:
            current = _identity_from_stat_result(os.stat(path.name, dir_fd=parent_descriptor, follow_symlinks=False))
        except FileNotFoundError:
            errors.append(f"{label} {path}: identity missing; preserved")
            return
        if current != expected_identity:
            errors.append(f"{label} {path}: identity changed; preserved")
            return
        try:
            if is_directory:
                os.rmdir(path.name, dir_fd=parent_descriptor)
            else:
                os.unlink(path.name, dir_fd=parent_descriptor)
        except OSError as exc:
            errors.append(f"{label} {path}: {exc}")
    finally:
        os.close(parent_descriptor)


def _close_artifacts_directory(journal: ArtifactMutationJournal) -> None:
    descriptor = journal.artifacts_dir_descriptor
    if descriptor is None:
        return
    os.close(descriptor)
    journal.artifacts_dir_descriptor = None


def _combine_cleanup_errors(
    current: Exception | None,
    added: Exception,
    *,
    label: str,
) -> Exception:
    if current is None:
        return added
    return RuntimeError(f"{current}; {label}: {added}")


def _committed_cleanup_warning(*, label: str, error: Exception) -> str:
    return f"artifact committed; {label}: {error}; do not retry creation without inspecting the committed artifact"


def _preflight_artifacts_setup_for_target(*, target: ArtifactSetupTarget, specdock_dir: Path) -> None:
    _preflight_artifacts_dir(target.artifacts_dir)
    source = specdock_dir / "docs" / "rules" / target.rules_kind / "artifacts.md"
    if source.is_symlink() or not source.is_file():
        raise RuntimeError(f"Missing rules source: {source}")
    link_path = target.artifacts_dir / "rules.md"
    if os.path.lexists(link_path):
        if not link_path.is_symlink():
            raise RuntimeError(f"Destination already exists: {link_path}")
        if not link_path.exists():
            raise RuntimeError(f"Broken artifact rules symlink: {link_path}")
        if link_path.resolve() != source.resolve():
            raise RuntimeError(f"Artifact rules symlink points to wrong target: {link_path}")


def _artifact_replacements(
    *,
    scope: SpecNode,
    artifact_id: str,
    artifact_type: str,
    title: str,
) -> dict[str, str]:
    today = _format_artifact_date_from_id(artifact_id)
    replacements = _replacements(
        kind=scope.kind,
        node_id=scope.id,
        title=scope.title,
        parent_id=scope.parent_id,
        initiative_id=scope.initiative_id,
        github_issue_number=scope.github_issue_number,
        today=today,
    )
    replacements.update({
        "<ARTIFACT_ID>": artifact_id,
        "<ARTIFACT_TITLE>": title,
        "<ADR_ID>": artifact_id,
        "<ADR_TITLE>": title,
        "<DISC_ID>": artifact_id,
        "<DISC_TITLE>": title,
        "<RESEARCH_ID>": artifact_id,
        "<RESEARCH_TITLE>": title,
        "<INTERVIEW_ID>": artifact_id,
        "<INTERVIEW_TITLE>": title,
        "<DECISION_CANDIDATE_ID>": artifact_id,
        "<DECISION_CANDIDATE_TITLE>": title,
        "<PR_REPAIR_BATCH_ID>": artifact_id,
        "<PR_REPAIR_BATCH_TITLE>": title,
        "<SCOPE_ID>": scope.id,
        "<YOUR_NAME>": os.environ.get("USER", "<YOUR_NAME>"),
        "YYYY-MM-DD": today,
    })
    if artifact_type.startswith("draft-"):
        replacements["<SCOPE_ID>"] = scope.id
    return replacements
