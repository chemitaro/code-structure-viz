from __future__ import annotations

import fnmatch
import hashlib
import os
import stat
import unicodedata
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass, field, replace
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Final

from code_structure_viz.core.config import PythonConfig
from code_structure_viz.core.diagnostics import Diagnostic, DiagnosticCode, diagnostic
from code_structure_viz.semantic.canonical_json import encode_canonical_json
from code_structure_viz.source.git_repository import (
    Commit,
    EnumeratedPath,
    GitIndexEntry,
    GitlinkWorktreeState,
    GitPathIdentity,
    HeadState,
)

_SCHEMA: Final = "code-structure-viz.source-view/v1"
_KIND: Final = "working-tree"


class SourceFileKind(StrEnum):
    REGULAR = "regular"
    SYMLINK = "symlink"


class AcquisitionStage(StrEnum):
    READ = "read"
    PATH_SAFETY = "path_safety"


@dataclass(frozen=True, slots=True)
class SourceFile:
    path: PurePosixPath
    kind: SourceFileKind
    resolved_target: PurePosixPath | None
    size_bytes: int
    sha256: str
    content: bytes = field(repr=False)

    def descriptor_value(self) -> dict[str, object]:
        return {
            "path": self.path.as_posix(),
            "kind": self.kind.value,
            "resolved_target": (
                self.resolved_target.as_posix() if self.resolved_target is not None else None
            ),
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
        }


@dataclass(frozen=True, slots=True)
class SourceInventoryEntry:
    """Internal immutable working-tree entry used for drift and diff evidence."""

    path: PurePosixPath
    raw_path: str
    kind: str
    size_bytes: int | None
    digest: str | None
    tracking_state: str = "tracked"
    git_mode: str | None = None
    object_id: str | None = None
    availability: str = "available"
    unmerged: bool = False
    content: bytes | None = field(default=None, repr=False, compare=False)
    materialization_state: str = "present"
    index_object_id: str | None = None
    worktree_object_id: str | None = None
    worktree_dirty: bool = False
    tracked_content_dirty: bool = False
    untracked_content_dirty: bool = False
    gitlink_profile_digest: str | None = None
    gitlink_worktree_digest: str | None = None
    gitlink_untracked_paths: tuple[GitPathIdentity, ...] = ()

    def __post_init__(self) -> None:
        GitPathIdentity(self.raw_path, self.path)
        if self.index_object_id is None and self.object_id is not None:
            object.__setattr__(self, "index_object_id", self.object_id)

    def descriptor_value(self) -> dict[str, object]:
        return {
            "path": self.path.as_posix(),
            "raw_path": self.raw_path,
            "kind": self.kind,
            "size_bytes": self.size_bytes,
            "digest": self.digest,
            "tracking_state": self.tracking_state,
            "git_mode": self.git_mode,
            "object_id": self.object_id,
            "availability": self.availability,
            "unmerged": self.unmerged,
            "materialization_state": self.materialization_state,
            "index_object_id": self.index_object_id,
            "worktree_object_id": self.worktree_object_id,
            "worktree_dirty": self.worktree_dirty,
            "tracked_content_dirty": self.tracked_content_dirty,
            "untracked_content_dirty": self.untracked_content_dirty,
            "gitlink_profile_digest": self.gitlink_profile_digest,
            "gitlink_worktree_digest": self.gitlink_worktree_digest,
            "gitlink_untracked_paths": [item.raw_text for item in self.gitlink_untracked_paths],
        }


@dataclass(frozen=True, slots=True)
class SourceAcquisitionFailure:
    path: PurePosixPath
    stage: AcquisitionStage
    diagnostic_code: DiagnosticCode

    def descriptor_value(self) -> dict[str, object]:
        return {
            "path": self.path.as_posix(),
            "stage": self.stage.value,
            "diagnostic_code": self.diagnostic_code.value,
        }


@dataclass(frozen=True, slots=True)
class SourceView:
    head_commit: str | None
    files: tuple[SourceFile, ...]
    failures: tuple[SourceAcquisitionFailure, ...]
    fingerprint: str
    schema: str = _SCHEMA
    kind: str = _KIND
    collision_groups: tuple[tuple[PurePosixPath, ...], ...] = ()
    inventory: tuple[SourceInventoryEntry, ...] = ()
    state_fingerprint: str | None = None

    def fingerprint_value(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "kind": self.kind,
            "head_commit": self.head_commit,
            "files": [item.descriptor_value() for item in self.files],
            "failures": [item.descriptor_value() for item in self.failures],
        }


class SourceViewBuildError(RuntimeError):
    def __init__(self, value: Diagnostic) -> None:
        self.diagnostic = value
        super().__init__(value.message)


class SourceDriftError(SourceViewBuildError):
    pass


class SourceInterruptedError(SourceViewBuildError):
    pass


class _UnsafeSymlinkError(Exception):
    pass


class _ConcurrentMutationError(Exception):
    pass


def _path_key(path: PurePosixPath) -> bytes:
    return path.as_posix().encode("utf-8")


def _failure_key(value: SourceAcquisitionFailure) -> tuple[bytes, bytes, bytes]:
    return (
        _path_key(value.path),
        value.stage.value.encode("utf-8"),
        value.diagnostic_code.value.encode("utf-8"),
    )


def _inventory_key(value: SourceInventoryEntry) -> tuple[bytes, bytes]:
    return (value.raw_path.encode("utf-8"), _path_key(value.path))


def with_content_unavailable_failures(
    source: SourceView,
    paths: frozenset[PurePosixPath],
    config: PythonConfig,
) -> SourceView:
    candidate_paths = frozenset(path for path in paths if _is_candidate(path, config))
    if not candidate_paths:
        return source
    files = tuple(item for item in source.files if item.path not in candidate_paths)
    existing_paths = {item.path for item in source.failures}
    failures = tuple(
        sorted(
            (
                *source.failures,
                *(
                    SourceAcquisitionFailure(
                        path,
                        AcquisitionStage.READ,
                        DiagnosticCode.PY_READ,
                    )
                    for path in candidate_paths - existing_paths
                ),
            ),
            key=_failure_key,
        )
    )
    updated = replace(source, files=files, failures=failures)
    return replace(
        updated,
        fingerprint=hashlib.sha256(encode_canonical_json(updated.fingerprint_value())).hexdigest(),
    )


def _head_commit(state: HeadState) -> str | None:
    return state.object_id if isinstance(state, Commit) else None


def _segment_matches(pattern: str, path: str) -> bool:
    pattern_parts = pattern.split("/")
    path_parts = path.split("/")
    suffix = [False] * (len(path_parts) + 1)
    suffix[-1] = True
    for token in reversed(pattern_parts):
        current = [False] * (len(path_parts) + 1)
        if token == "**":
            current[-1] = suffix[-1]
            for path_index in range(len(path_parts) - 1, -1, -1):
                current[path_index] = suffix[path_index] or current[path_index + 1]
        else:
            for path_index in range(len(path_parts) - 1, -1, -1):
                current[path_index] = suffix[path_index + 1] and fnmatch.fnmatchcase(
                    path_parts[path_index], token
                )
        suffix = current
    return suffix[0]


def _under_source_root(path: PurePosixPath, roots: tuple[str, ...]) -> bool:
    for raw_root in roots:
        if raw_root == ".":
            return True
        root = PurePosixPath(raw_root)
        if path == root or root in path.parents:
            return True
    return False


def _is_candidate(path: PurePosixPath, config: PythonConfig) -> bool:
    rendered = path.as_posix()
    return (
        path.suffix == ".py"
        and _under_source_root(path, config.source_roots)
        and any(_segment_matches(pattern, rendered) for pattern in config.include)
        and not any(_segment_matches(pattern, rendered) for pattern in config.exclude)
    )


def _stat_signature(value: os.stat_result) -> tuple[int, int, int, int, int]:
    return (value.st_dev, value.st_ino, value.st_mode, value.st_size, value.st_mtime_ns)


def _read_fd(fd: int) -> bytes:
    chunks: list[bytes] = []
    while True:
        chunk = os.read(fd, 1024 * 1024)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


def _directory_flags() -> int:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    return flags


def _read_flags() -> int:
    flags = os.O_RDONLY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    return flags


def _open_repository_descriptor(repository: Path, repository_descriptor: int | None) -> int:
    if repository_descriptor is not None:
        return os.dup(repository_descriptor)
    return os.open(repository, _directory_flags())


def _open_parent_without_symlinks(
    repository: Path,
    relative: PurePosixPath,
    *,
    repository_descriptor: int | None = None,
) -> int:
    descriptor = _open_repository_descriptor(repository, repository_descriptor)
    try:
        for component in relative.parts[:-1]:
            before = os.stat(component, dir_fd=descriptor, follow_symlinks=False)
            if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode):
                raise _UnsafeSymlinkError
            child = os.open(component, _directory_flags(), dir_fd=descriptor)
            after = os.fstat(child)
            if _stat_signature(before) != _stat_signature(after):
                os.close(child)
                raise _ConcurrentMutationError
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _collapse_relative_parts(parts: tuple[str, ...]) -> tuple[str, ...]:
    collapsed: list[str] = []
    for component in parts:
        if component in {"", "."}:
            continue
        if component == "..":
            if not collapsed:
                raise _UnsafeSymlinkError
            collapsed.pop()
            continue
        collapsed.append(component)
    return tuple(collapsed)


def _symlink_target_parts(
    repository: Path,
    parent_parts: tuple[str, ...],
    target: str,
    remaining: tuple[str, ...],
) -> tuple[str, ...]:
    target_path = Path(target)
    if target_path.is_absolute():
        normalized = Path(os.path.normpath(target))
        try:
            relative = normalized.relative_to(repository)
        except ValueError as error:
            raise _UnsafeSymlinkError from error
        prefix = relative.parts
    else:
        prefix = (*parent_parts, *PurePosixPath(target).parts)
    return _collapse_relative_parts((*prefix, *remaining))


def _resolve_repository_file(
    repository: Path,
    relative: PurePosixPath,
    *,
    repository_descriptor: int | None = None,
) -> tuple[PurePosixPath, int, str, os.stat_result]:
    pending = list(_collapse_relative_parts(relative.parts))
    if not pending:
        raise _UnsafeSymlinkError
    resolved: list[str] = []
    descriptor = _open_repository_descriptor(repository, repository_descriptor)
    symlink_count = 0
    try:
        while pending:
            component = pending.pop(0)
            before = os.stat(component, dir_fd=descriptor, follow_symlinks=False)
            if stat.S_ISLNK(before.st_mode):
                symlink_count += 1
                if symlink_count > 40:
                    raise _UnsafeSymlinkError
                target = os.readlink(component, dir_fd=descriptor)
                pending = list(
                    _symlink_target_parts(
                        repository,
                        tuple(resolved),
                        target,
                        tuple(pending),
                    )
                )
                resolved.clear()
                os.close(descriptor)
                descriptor = _open_repository_descriptor(repository, repository_descriptor)
                continue
            if pending:
                if not stat.S_ISDIR(before.st_mode):
                    raise _UnsafeSymlinkError
                child = os.open(component, _directory_flags(), dir_fd=descriptor)
                after = os.fstat(child)
                if _stat_signature(before) != _stat_signature(after):
                    os.close(child)
                    raise _ConcurrentMutationError
                os.close(descriptor)
                descriptor = child
                resolved.append(component)
                continue
            if not stat.S_ISREG(before.st_mode):
                raise _UnsafeSymlinkError
            return PurePosixPath(*resolved, component), descriptor, component, before
        raise _UnsafeSymlinkError
    except BaseException:
        os.close(descriptor)
        raise


class SourceViewBuilder:
    def __init__(
        self,
        repository: Path,
        staging_root: Path,
        *,
        staging_root_descriptor: int | None = None,
        repository_descriptor: int | None = None,
        cancelled: Callable[[], bool] | None = None,
        fatal_path_identity_collisions: bool = False,
    ) -> None:
        self.repository = repository if repository.is_absolute() else repository.resolve()
        self.staging_root = staging_root
        self._staging_root_descriptor = staging_root_descriptor
        self._repository_descriptor = repository_descriptor
        self._cancelled = cancelled or (lambda: False)
        self._fatal_path_identity_collisions = fatal_path_identity_collisions

    def build(
        self,
        head_state: HeadState,
        entries: tuple[EnumeratedPath, ...],
        config: PythonConfig,
        *,
        include_inventory: bool = False,
        untracked_paths: frozenset[PurePosixPath] = frozenset(),
        unmerged_paths: frozenset[PurePosixPath] = frozenset(),
        index_entries: tuple[GitIndexEntry, ...] = (),
        untracked_entries: tuple[GitPathIdentity, ...] = (),
        unmerged_entries: tuple[GitPathIdentity, ...] = (),
        gitlink_states: tuple[GitlinkWorktreeState, ...] = (),
    ) -> SourceView:
        self._prepare_staging()
        return self._collect(
            head_state,
            entries,
            config,
            write_frozen=True,
            include_inventory=include_inventory,
            untracked_paths=untracked_paths,
            unmerged_paths=unmerged_paths,
            index_entries=index_entries,
            untracked_entries=untracked_entries,
            unmerged_entries=unmerged_entries,
            gitlink_states=gitlink_states,
        )

    def assert_unchanged(
        self,
        initial: SourceView,
        head_state: HeadState,
        entries: tuple[EnumeratedPath, ...],
        config: PythonConfig,
        *,
        untracked_paths: frozenset[PurePosixPath] = frozenset(),
        unmerged_paths: frozenset[PurePosixPath] = frozenset(),
        index_entries: tuple[GitIndexEntry, ...] = (),
        untracked_entries: tuple[GitPathIdentity, ...] = (),
        unmerged_entries: tuple[GitPathIdentity, ...] = (),
        gitlink_states: tuple[GitlinkWorktreeState, ...] = (),
    ) -> None:
        try:
            current = self._collect(
                head_state,
                entries,
                config,
                write_frozen=False,
                include_inventory=True,
                untracked_paths=untracked_paths,
                unmerged_paths=unmerged_paths,
                index_entries=index_entries,
                untracked_entries=untracked_entries,
                unmerged_entries=unmerged_entries,
                gitlink_states=gitlink_states,
            )
        except SourceViewBuildError as error:
            raise SourceDriftError(diagnostic(DiagnosticCode.SOURCE_DRIFT)) from error
        if current.fingerprint != initial.fingerprint or (
            initial.state_fingerprint is not None
            and current.state_fingerprint != initial.state_fingerprint
        ):
            raise SourceDriftError(diagnostic(DiagnosticCode.SOURCE_DRIFT))

    def _prepare_staging(self) -> None:
        try:
            if self._staging_root_descriptor is not None:
                if set(os.listdir(self._staging_root_descriptor)) != {"source", "artifacts"}:
                    raise OSError
                source_descriptor: int | None = None
                artifacts_descriptor: int | None = None
                try:
                    source_descriptor = os.open(
                        "source",
                        _directory_flags(),
                        dir_fd=self._staging_root_descriptor,
                    )
                    artifacts_descriptor = os.open(
                        "artifacts",
                        _directory_flags(),
                        dir_fd=self._staging_root_descriptor,
                    )
                    if os.listdir(source_descriptor) or os.listdir(artifacts_descriptor):
                        raise OSError
                finally:
                    if source_descriptor is not None:
                        os.close(source_descriptor)
                    if artifacts_descriptor is not None:
                        os.close(artifacts_descriptor)
                return
            if self.staging_root.exists():
                source = self.staging_root / "source"
                artifacts = self.staging_root / "artifacts"
                if (
                    self.staging_root.is_symlink()
                    or not self.staging_root.is_dir()
                    or source.is_symlink()
                    or not source.is_dir()
                    or artifacts.is_symlink()
                    or not artifacts.is_dir()
                    or any(source.iterdir())
                    or any(artifacts.iterdir())
                ):
                    raise OSError
            else:
                self.staging_root.mkdir(mode=0o700, parents=False, exist_ok=False)
                self.staging_root.chmod(0o700)
                (self.staging_root / "source").mkdir(mode=0o700)
                (self.staging_root / "artifacts").mkdir(mode=0o700)
        except OSError as error:
            raise SourceViewBuildError(diagnostic(DiagnosticCode.OUTPUT_DESTINATION)) from error

    def _collect(
        self,
        head_state: HeadState,
        entries: tuple[EnumeratedPath, ...],
        config: PythonConfig,
        *,
        write_frozen: bool,
        include_inventory: bool = False,
        untracked_paths: frozenset[PurePosixPath] = frozenset(),
        unmerged_paths: frozenset[PurePosixPath] = frozenset(),
        index_entries: tuple[GitIndexEntry, ...] = (),
        untracked_entries: tuple[GitPathIdentity, ...] = (),
        unmerged_entries: tuple[GitPathIdentity, ...] = (),
        gitlink_states: tuple[GitlinkWorktreeState, ...] = (),
    ) -> SourceView:
        self._checkpoint()
        if self._fatal_path_identity_collisions:
            self._validate_identities(
                entries,
                index_entries,
                untracked_entries,
                unmerged_entries,
            )
        inventory_before = (
            self._inventory(
                entries,
                untracked_paths=untracked_paths,
                unmerged_paths=unmerged_paths,
                index_entries=index_entries,
                untracked_entries=untracked_entries,
                unmerged_entries=unmerged_entries,
                gitlink_states=gitlink_states,
            )
            if include_inventory
            else ()
        )
        unavailable_unmerged = frozenset(unmerged_paths) | frozenset(
            item.canonical_path for item in unmerged_entries
        )
        candidates = tuple(
            entry
            for entry in entries
            if _is_candidate(entry.normalized, config)
            and entry.normalized not in unavailable_unmerged
        )
        collision_groups = self._collision_groups(candidates)
        collision_paths = frozenset(path for group in collision_groups for path in group)
        failures = [
            SourceAcquisitionFailure(
                path,
                AcquisitionStage.PATH_SAFETY,
                DiagnosticCode.SOURCE_PATH_COLLISION,
            )
            for path in collision_paths
        ]
        files: list[SourceFile] = []
        inventory_by_path = {item.path: item for item in inventory_before}
        for entry in candidates:
            self._checkpoint()
            if entry.normalized in collision_paths:
                continue
            inventory_entry = inventory_by_path.get(entry.normalized)
            if (
                inventory_entry is not None
                and inventory_entry.materialization_state == "sparse-unavailable"
            ):
                failures.append(
                    SourceAcquisitionFailure(
                        entry.normalized,
                        AcquisitionStage.READ,
                        DiagnosticCode.PY_READ,
                    )
                )
                continue
            frozen = self._freeze(entry, write_frozen=write_frozen)
            if isinstance(frozen, SourceFile):
                files.append(frozen)
            elif frozen is not None:
                failures.append(frozen)

        ordered_files = tuple(sorted(files, key=lambda item: _path_key(item.path)))
        ordered_failures = tuple(sorted(failures, key=_failure_key))
        inventory_after = (
            self._inventory(
                entries,
                untracked_paths=untracked_paths,
                unmerged_paths=unmerged_paths,
                index_entries=index_entries,
                untracked_entries=untracked_entries,
                unmerged_entries=unmerged_entries,
                gitlink_states=gitlink_states,
            )
            if include_inventory
            else inventory_before
        )
        if include_inventory and inventory_after != inventory_before:
            raise SourceDriftError(diagnostic(DiagnosticCode.SOURCE_DRIFT))
        value = {
            "schema": _SCHEMA,
            "kind": _KIND,
            "head_commit": _head_commit(head_state),
            "files": [item.descriptor_value() for item in ordered_files],
            "failures": [item.descriptor_value() for item in ordered_failures],
        }
        fingerprint = hashlib.sha256(encode_canonical_json(value)).hexdigest()
        return SourceView(
            head_commit=_head_commit(head_state),
            files=ordered_files,
            failures=ordered_failures,
            fingerprint=fingerprint,
            collision_groups=collision_groups,
            inventory=inventory_after,
            state_fingerprint=(
                _state_fingerprint(head_state, inventory_after) if include_inventory else None
            ),
        )

    @staticmethod
    def _validate_identities(
        entries: tuple[EnumeratedPath, ...],
        index_entries: tuple[GitIndexEntry, ...],
        untracked_entries: tuple[GitPathIdentity, ...],
        unmerged_entries: tuple[GitPathIdentity, ...],
    ) -> None:
        canonical_to_raw: dict[PurePosixPath, str] = {}
        identities: tuple[GitPathIdentity, ...] = (
            tuple(item.identity for item in entries)
            + tuple(item.identity for item in index_entries)
            + untracked_entries
            + unmerged_entries
        )
        for identity in identities:
            previous = canonical_to_raw.get(identity.canonical_path)
            if previous is None:
                canonical_to_raw[identity.canonical_path] = identity.raw_text
            elif previous != identity.raw_text:
                raise SourceViewBuildError(diagnostic(DiagnosticCode.DIFF_FILE_CHANGE))

    def _inventory(
        self,
        entries: tuple[EnumeratedPath, ...],
        *,
        untracked_paths: frozenset[PurePosixPath],
        unmerged_paths: frozenset[PurePosixPath],
        index_entries: tuple[GitIndexEntry, ...],
        untracked_entries: tuple[GitPathIdentity, ...],
        unmerged_entries: tuple[GitPathIdentity, ...],
        gitlink_states: tuple[GitlinkWorktreeState, ...],
    ) -> tuple[SourceInventoryEntry, ...]:
        values: list[SourceInventoryEntry] = []
        index_by_path: dict[PurePosixPath, GitIndexEntry] = {}
        for item in index_entries:
            if item.stage != 0:
                continue
            if item.path in index_by_path:
                raise SourceViewBuildError(diagnostic(DiagnosticCode.DIFF_FILE_CHANGE))
            index_by_path[item.path] = item
        tracked_paths = {item.path for item in index_entries}
        untracked_by_path = {item.canonical_path: item for item in untracked_entries}
        unmerged_by_path = {item.canonical_path: item for item in unmerged_entries}
        gitlink_by_path = {item.identity.canonical_path: item for item in gitlink_states}
        for entry in entries:
            self._checkpoint()
            logical_path = entry.normalized
            physical_path = PurePosixPath(entry.raw_text)
            index_entry = index_by_path.get(logical_path)
            tracking_state = (
                "tracked"
                if logical_path in tracked_paths
                else "untracked"
                if logical_path in untracked_paths or logical_path in untracked_by_path
                else "tracked"
            )
            unmerged = logical_path in unmerged_paths or logical_path in unmerged_by_path
            gitlink_state = gitlink_by_path.get(logical_path)
            parent_descriptor: int | None = None
            try:
                if index_entry is not None and index_entry.mode == "160000":
                    if gitlink_state is None:
                        raise SourceViewBuildError(diagnostic(DiagnosticCode.DIFF_FILE_CHANGE))
                    values.append(
                        SourceInventoryEntry(
                            logical_path,
                            entry.raw_text,
                            "gitlink",
                            None,
                            index_entry.object_id,
                            tracking_state,
                            index_entry.mode,
                            index_entry.object_id,
                            "unavailable",
                            unmerged,
                            None,
                            gitlink_state.materialization_state,
                            index_entry.object_id,
                            gitlink_state.current_head,
                            gitlink_state.dirty,
                            gitlink_state.tracked_content_dirty,
                            gitlink_state.untracked_content_dirty,
                            gitlink_state.comparison_profile_digest,
                            gitlink_state.tracked_worktree_digest,
                            gitlink_state.untracked_paths,
                        )
                    )
                    continue
                parent_descriptor = _open_parent_without_symlinks(
                    self.repository,
                    physical_path,
                    repository_descriptor=self._repository_descriptor,
                )
                name = physical_path.name
                before = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
                if stat.S_ISLNK(before.st_mode):
                    target = os.readlink(name, dir_fd=parent_descriptor)
                    values.append(
                        SourceInventoryEntry(
                            logical_path,
                            entry.raw_text,
                            "symlink",
                            len(os.fsencode(target)),
                            hashlib.sha256(os.fsencode(target)).hexdigest(),
                            tracking_state,
                            "120000",
                            index_entry.object_id if index_entry is not None else None,
                            "unavailable",
                            unmerged,
                            None,
                            "unavailable",
                        )
                    )
                    continue
                if not stat.S_ISREG(before.st_mode):
                    values.append(
                        SourceInventoryEntry(
                            logical_path,
                            entry.raw_text,
                            "other",
                            before.st_size,
                            None,
                            tracking_state,
                            None,
                            index_entry.object_id if index_entry is not None else None,
                            "unavailable",
                            unmerged,
                            None,
                            "unavailable",
                        )
                    )
                    continue
                fd = os.open(name, _read_flags(), dir_fd=parent_descriptor)
                try:
                    opened_before = os.fstat(fd)
                    content = _read_fd(fd)
                    opened_after = os.fstat(fd)
                finally:
                    os.close(fd)
                if (
                    _stat_signature(before) != _stat_signature(opened_before)
                    or _stat_signature(opened_before) != _stat_signature(opened_after)
                    or len(content) != opened_after.st_size
                ):
                    raise _ConcurrentMutationError
                values.append(
                    SourceInventoryEntry(
                        logical_path,
                        entry.raw_text,
                        "regular",
                        len(content),
                        hashlib.sha256(content).hexdigest(),
                        tracking_state,
                        "100755" if before.st_mode & 0o111 else "100644",
                        index_entry.object_id if index_entry is not None else None,
                        "available",
                        unmerged,
                        content,
                        "present",
                    )
                )
            except _ConcurrentMutationError as error:
                raise SourceDriftError(diagnostic(DiagnosticCode.SOURCE_DRIFT)) from error
            except FileNotFoundError:
                values.append(
                    SourceInventoryEntry(
                        logical_path,
                        entry.raw_text,
                        "sparse-unavailable"
                        if index_entry is not None and index_entry.skip_worktree
                        else "missing",
                        None,
                        None,
                        tracking_state,
                        index_entry.mode if index_entry is not None else None,
                        index_entry.object_id if index_entry is not None else None,
                        "unavailable" if index_entry and index_entry.skip_worktree else "absent",
                        unmerged,
                        None,
                        (
                            "sparse-unavailable"
                            if index_entry and index_entry.skip_worktree
                            else "absent"
                        ),
                    )
                )
            except (_UnsafeSymlinkError, OSError):
                values.append(
                    SourceInventoryEntry(
                        logical_path,
                        entry.raw_text,
                        "unavailable",
                        None,
                        None,
                        tracking_state,
                        None,
                        index_entry.object_id if index_entry is not None else None,
                        "unavailable",
                        unmerged,
                        None,
                        "unavailable",
                    )
                )
            finally:
                if parent_descriptor is not None:
                    os.close(parent_descriptor)
        return tuple(sorted(values, key=_inventory_key))

    def _checkpoint(self) -> None:
        if self._cancelled():
            raise SourceInterruptedError(diagnostic(DiagnosticCode.INTERRUPTED))

    def _collision_groups(
        self, candidates: tuple[EnumeratedPath, ...]
    ) -> tuple[tuple[PurePosixPath, ...], ...]:
        normalized_groups: dict[PurePosixPath, list[EnumeratedPath]] = {}
        for entry in candidates:
            normalized_groups.setdefault(entry.normalized, []).append(entry)
        paths = tuple(normalized_groups)
        parents = list(range(len(paths)))
        collision_nodes = {
            index for index, path in enumerate(paths) if len(normalized_groups[path]) > 1
        }

        def find(index: int) -> int:
            while parents[index] != index:
                parents[index] = parents[parents[index]]
                index = parents[index]
            return index

        def union(left: int, right: int) -> None:
            left_root = find(left)
            right_root = find(right)
            if left_root == right_root:
                return
            parents[right_root] = left_root

        case_groups: dict[str, list[int]] = {}
        for index, path in enumerate(paths):
            case_groups.setdefault(path.as_posix().casefold(), []).append(index)
        for group in case_groups.values():
            for left_offset, left_index in enumerate(group):
                for right_index in group[left_offset + 1 :]:
                    matched = False
                    for left in normalized_groups[paths[left_index]]:
                        for right in normalized_groups[paths[right_index]]:
                            matched = self._samefile(left, right)
                            if matched:
                                break
                        if matched:
                            break
                    if matched:
                        union(left_index, right_index)
                        collision_nodes.update((left_index, right_index))

        components: dict[int, list[PurePosixPath]] = {}
        for index, path in enumerate(paths):
            if index in collision_nodes:
                components.setdefault(find(index), []).append(path)
        return tuple(
            sorted(
                (tuple(sorted(component, key=_path_key)) for component in components.values()),
                key=lambda component: tuple(_path_key(path) for path in component),
            )
        )

    def _samefile(self, left: EnumeratedPath, right: EnumeratedPath) -> bool:
        if self._repository_descriptor is None:
            try:
                return os.path.samefile(
                    self.repository.joinpath(*PurePosixPath(left.raw_text).parts),
                    self.repository.joinpath(*PurePosixPath(right.raw_text).parts),
                )
            except OSError:
                return False

        descriptors: list[int] = []
        try:
            _left_path, _left_parent, _left_name, left_stat = _resolve_repository_file(
                self.repository,
                PurePosixPath(left.raw_text),
                repository_descriptor=self._repository_descriptor,
            )
            descriptors.append(_left_parent)
            _right_path, _right_parent, _right_name, right_stat = _resolve_repository_file(
                self.repository,
                PurePosixPath(right.raw_text),
                repository_descriptor=self._repository_descriptor,
            )
            descriptors.append(_right_parent)
            return (left_stat.st_dev, left_stat.st_ino) == (right_stat.st_dev, right_stat.st_ino)
        except _ConcurrentMutationError as error:
            raise SourceDriftError(diagnostic(DiagnosticCode.SOURCE_DRIFT)) from error
        except (OSError, RuntimeError, ValueError, _UnsafeSymlinkError):
            return False
        finally:
            for descriptor in descriptors:
                with suppress(OSError):
                    os.close(descriptor)

    def _freeze(
        self, entry: EnumeratedPath, *, write_frozen: bool
    ) -> SourceFile | SourceAcquisitionFailure | None:
        logical_path = entry.normalized
        physical_path = PurePosixPath(entry.raw_text)
        source_parent_descriptor: int | None = None
        target_parent_descriptor: int | None = None
        try:
            source_parent_descriptor = _open_parent_without_symlinks(
                self.repository,
                physical_path,
                repository_descriptor=self._repository_descriptor,
            )
            source_name = physical_path.name
            logical_before = os.stat(
                source_name,
                dir_fd=source_parent_descriptor,
                follow_symlinks=False,
            )
        except _ConcurrentMutationError as error:
            raise SourceDriftError(diagnostic(DiagnosticCode.SOURCE_DRIFT)) from error
        except _UnsafeSymlinkError:
            return SourceAcquisitionFailure(
                logical_path,
                AcquisitionStage.PATH_SAFETY,
                DiagnosticCode.SOURCE_SYMLINK,
            )
        except FileNotFoundError:
            return None
        except OSError:
            return SourceAcquisitionFailure(
                logical_path, AcquisitionStage.READ, DiagnosticCode.PY_READ
            )

        try:
            if stat.S_ISLNK(logical_before.st_mode):
                kind = SourceFileKind.SYMLINK
                try:
                    target_text = os.readlink(source_name, dir_fd=source_parent_descriptor)
                    target_path = Path(target_text)
                    if target_path.is_absolute():
                        try:
                            absolute_target = Path(os.path.normpath(target_text))
                            relative_target = absolute_target.relative_to(self.repository)
                        except ValueError as error:
                            raise _UnsafeSymlinkError from error
                        initial_target = PurePosixPath(*relative_target.parts)
                    else:
                        initial_target = physical_path.parent / PurePosixPath(target_text)
                    (
                        physical_target,
                        target_parent_descriptor,
                        target_name,
                        target_before,
                    ) = _resolve_repository_file(
                        self.repository,
                        initial_target,
                        repository_descriptor=self._repository_descriptor,
                    )
                except _ConcurrentMutationError:
                    raise
                except (OSError, RuntimeError, ValueError, _UnsafeSymlinkError) as error:
                    raise _UnsafeSymlinkError from error
                resolved_target = PurePosixPath(
                    unicodedata.normalize("NFC", physical_target.as_posix())
                )
            elif stat.S_ISREG(logical_before.st_mode):
                kind = SourceFileKind.REGULAR
                target_parent_descriptor = source_parent_descriptor
                target_name = source_name
                target_before = logical_before
                resolved_target = None
            else:
                return SourceAcquisitionFailure(
                    logical_path, AcquisitionStage.READ, DiagnosticCode.PY_READ
                )

            fd = os.open(
                target_name,
                _read_flags(),
                dir_fd=target_parent_descriptor,
            )
            try:
                opened_before = os.fstat(fd)
                if _stat_signature(opened_before) != _stat_signature(target_before):
                    raise _ConcurrentMutationError
                content = _read_fd(fd)
                opened_after = os.fstat(fd)
            finally:
                os.close(fd)
            logical_after = os.stat(
                source_name,
                dir_fd=source_parent_descriptor,
                follow_symlinks=False,
            )
            target_after = os.stat(
                target_name,
                dir_fd=target_parent_descriptor,
                follow_symlinks=False,
            )
            if (
                _stat_signature(opened_before) != _stat_signature(opened_after)
                or _stat_signature(logical_before) != _stat_signature(logical_after)
                or _stat_signature(target_before) != _stat_signature(target_after)
                or len(content) != opened_after.st_size
            ):
                raise _ConcurrentMutationError
        except _ConcurrentMutationError as error:
            raise SourceDriftError(diagnostic(DiagnosticCode.SOURCE_DRIFT)) from error
        except _UnsafeSymlinkError:
            return SourceAcquisitionFailure(
                logical_path,
                AcquisitionStage.PATH_SAFETY,
                DiagnosticCode.SOURCE_SYMLINK,
            )
        except OSError:
            return SourceAcquisitionFailure(
                logical_path, AcquisitionStage.READ, DiagnosticCode.PY_READ
            )
        finally:
            if (
                target_parent_descriptor is not None
                and target_parent_descriptor != source_parent_descriptor
            ):
                os.close(target_parent_descriptor)
            if source_parent_descriptor is not None:
                os.close(source_parent_descriptor)

        if write_frozen:
            self._write_frozen(logical_path, content)
        return SourceFile(
            path=logical_path,
            kind=kind,
            resolved_target=resolved_target,
            size_bytes=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
            content=content,
        )

    def _write_frozen(self, logical_path: PurePosixPath, content: bytes) -> None:
        if self._staging_root_descriptor is not None:
            self._write_frozen_at(self._staging_root_descriptor, logical_path, content)
            return
        destination = (self.staging_root / "source").joinpath(*logical_path.parts)
        try:
            destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            if hasattr(os, "O_CLOEXEC"):
                flags |= os.O_CLOEXEC
            fd = os.open(destination, flags, 0o600)
            try:
                remaining = memoryview(content)
                while remaining:
                    written = os.write(fd, remaining)
                    if written <= 0:
                        raise OSError
                    remaining = remaining[written:]
                os.fsync(fd)
            finally:
                os.close(fd)
        except OSError as error:
            raise SourceViewBuildError(diagnostic(DiagnosticCode.OUTPUT_DESTINATION)) from error

    @staticmethod
    def _write_frozen_at(
        staging_root_descriptor: int,
        logical_path: PurePosixPath,
        content: bytes,
    ) -> None:
        directory_descriptor: int | None = None
        try:
            directory_descriptor = os.open(
                "source",
                _directory_flags(),
                dir_fd=staging_root_descriptor,
            )
            for component in logical_path.parts[:-1]:
                try:
                    child = os.open(
                        component,
                        _directory_flags(),
                        dir_fd=directory_descriptor,
                    )
                except FileNotFoundError:
                    with suppress(FileExistsError):
                        os.mkdir(component, mode=0o700, dir_fd=directory_descriptor)
                    child = os.open(
                        component,
                        _directory_flags(),
                        dir_fd=directory_descriptor,
                    )
                os.close(directory_descriptor)
                directory_descriptor = child
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            if hasattr(os, "O_CLOEXEC"):
                flags |= os.O_CLOEXEC
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            file_descriptor = os.open(
                logical_path.name,
                flags,
                0o600,
                dir_fd=directory_descriptor,
            )
            try:
                remaining = memoryview(content)
                while remaining:
                    written = os.write(file_descriptor, remaining)
                    if written <= 0:
                        raise OSError
                    remaining = remaining[written:]
                os.fsync(file_descriptor)
            finally:
                os.close(file_descriptor)
        except OSError as error:
            raise SourceViewBuildError(diagnostic(DiagnosticCode.OUTPUT_DESTINATION)) from error
        finally:
            if directory_descriptor is not None:
                os.close(directory_descriptor)


def _state_fingerprint(
    head_state: HeadState,
    inventory: tuple[SourceInventoryEntry, ...],
) -> str:
    value = {
        "schema": "code-structure-viz.working-tree-state/v1",
        "head_commit": _head_commit(head_state),
        "inventory": [item.descriptor_value() for item in inventory],
    }
    return hashlib.sha256(encode_canonical_json(value)).hexdigest()
