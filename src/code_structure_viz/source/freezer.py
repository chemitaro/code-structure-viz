from __future__ import annotations

import hashlib
from collections.abc import Callable
from pathlib import Path, PurePosixPath

from code_structure_viz.core.config import PythonConfig
from code_structure_viz.core.diagnostics import DiagnosticCode, diagnostic
from code_structure_viz.semantic.canonical_json import encode_canonical_json
from code_structure_viz.source.git_repository import (
    Commit,
    CommitTreeEntry,
    EnumeratedPath,
    GitIndexEntry,
    GitlinkWorktreeState,
    GitPathIdentity,
    GitPathIdentityCollisionFatal,
    GitRepositoryReader,
    HeadState,
)
from code_structure_viz.source.source_view import (
    AcquisitionStage,
    SourceAcquisitionFailure,
    SourceFile,
    SourceFileKind,
    SourceInventoryEntry,
    SourceView,
    SourceViewBuilder,
    _is_candidate,
)


class WorkingTreeFreezer:
    """Freeze the working tree once, delegating path-safe reads to SourceViewBuilder."""

    def __init__(
        self,
        repository: Path,
        staging_root: Path,
        *,
        staging_root_descriptor: int | None = None,
        repository_descriptor: int | None = None,
        cancelled: Callable[[], bool] | None = None,
    ) -> None:
        self._builder = SourceViewBuilder(
            repository,
            staging_root,
            staging_root_descriptor=staging_root_descriptor,
            repository_descriptor=repository_descriptor,
            cancelled=cancelled,
            fatal_path_identity_collisions=True,
        )

    def freeze(
        self,
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
    ) -> SourceView:
        return self._builder.build(
            head_state,
            entries,
            config,
            include_inventory=True,
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
        self._builder.assert_unchanged(
            initial,
            head_state,
            entries,
            config,
            untracked_paths=untracked_paths,
            unmerged_paths=unmerged_paths,
            index_entries=index_entries,
            untracked_entries=untracked_entries,
            unmerged_entries=unmerged_entries,
            gitlink_states=gitlink_states,
        )


def build_commit_source_view(
    reader: GitRepositoryReader,
    commit: Commit,
    config: PythonConfig,
) -> SourceView:
    """Build an immutable SourceView directly from local Git blobs."""
    tree = reader.enumerate_commit_tree(commit.object_id)
    _validate_tree_identities(tree)
    candidates = tuple(item for item in tree if _is_candidate(item.path, config))
    collision_groups = _collision_groups(candidates)
    collision_paths = {path for group in collision_groups for path in group}
    failures: list[SourceAcquisitionFailure] = [
        SourceAcquisitionFailure(
            path,
            AcquisitionStage.PATH_SAFETY,
            DiagnosticCode.SOURCE_PATH_COLLISION,
        )
        for path in sorted(collision_paths, key=_path_key)
    ]
    files: list[SourceFile] = []
    inventory: list[SourceInventoryEntry] = []
    contents: dict[PurePosixPath, bytes] = {}
    for item in tree:
        if item.kind == "blob":
            content = reader.read_blob_object(item.object_id)
            contents[item.path] = content
            inventory.append(
                SourceInventoryEntry(
                    item.path,
                    item.raw_text or item.path.as_posix(),
                    "symlink" if item.mode == "120000" else "regular",
                    len(content),
                    hashlib.sha256(content).hexdigest(),
                    "tracked",
                    item.mode,
                    item.object_id,
                    ("unavailable" if item.mode == "120000" else "available"),
                    False,
                    None if item.mode == "120000" else content,
                )
            )
        else:
            inventory.append(
                SourceInventoryEntry(
                    item.path,
                    item.raw_text or item.path.as_posix(),
                    "gitlink" if item.mode == "160000" else item.kind,
                    None,
                    item.object_id,
                    "tracked",
                    item.mode,
                    item.object_id,
                    "unavailable",
                )
            )
    for item in candidates:
        if item.path in collision_paths:
            continue
        if item.mode == "120000":
            failures.append(
                SourceAcquisitionFailure(
                    item.path,
                    AcquisitionStage.PATH_SAFETY,
                    DiagnosticCode.SOURCE_SYMLINK,
                )
            )
            continue
        if item.kind != "blob":
            failures.append(
                SourceAcquisitionFailure(
                    item.path,
                    AcquisitionStage.READ,
                    DiagnosticCode.PY_READ,
                )
            )
            continue
        content = contents[item.path]
        files.append(
            SourceFile(
                path=item.path,
                kind=SourceFileKind.REGULAR,
                resolved_target=None,
                size_bytes=len(content),
                sha256=hashlib.sha256(content).hexdigest(),
                content=content,
            )
        )
    ordered_files = tuple(sorted(files, key=lambda item: _path_key(item.path)))
    ordered_failures = tuple(
        sorted(failures, key=lambda item: (item.path.as_posix().encode("utf-8"), item.stage.value))
    )
    value = {
        "schema": "code-structure-viz.source-view/v1",
        "kind": "commit",
        "head_commit": commit.object_id,
        "files": [item.descriptor_value() for item in ordered_files],
        "failures": [item.descriptor_value() for item in ordered_failures],
    }
    return SourceView(
        head_commit=commit.object_id,
        files=ordered_files,
        failures=ordered_failures,
        fingerprint=hashlib.sha256(encode_canonical_json(value)).hexdigest(),
        kind="commit",
        collision_groups=tuple(tuple(sorted(group, key=_path_key)) for group in collision_groups),
        inventory=tuple(sorted(inventory, key=lambda item: item.path.as_posix().encode("utf-8"))),
    )


def _path_key(path: PurePosixPath) -> bytes:
    return path.as_posix().encode("utf-8")


def _collision_groups(
    entries: tuple[CommitTreeEntry, ...],
) -> tuple[tuple[PurePosixPath, ...], ...]:
    groups: dict[str, list[PurePosixPath]] = {}
    for entry in entries:
        groups.setdefault(entry.path.as_posix().casefold(), []).append(entry.path)
    return tuple(
        sorted(
            (
                tuple(sorted(set(paths), key=_path_key))
                for paths in groups.values()
                if len(set(paths)) > 1
            ),
            key=lambda group: tuple(_path_key(path) for path in group),
        )
    )


def _validate_tree_identities(entries: tuple[CommitTreeEntry, ...]) -> None:
    raw_by_path: dict[PurePosixPath, str] = {}
    for item in entries:
        previous = raw_by_path.get(item.path)
        if previous is not None:
            raise GitPathIdentityCollisionFatal(diagnostic(DiagnosticCode.DIFF_FILE_CHANGE))
        raw_by_path[item.path] = item.raw_text or item.path.as_posix()
