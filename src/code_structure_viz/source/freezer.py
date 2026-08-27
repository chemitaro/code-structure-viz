from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath

from code_structure_viz.core.config import PythonConfig
from code_structure_viz.core.diagnostics import DiagnosticCode
from code_structure_viz.semantic.canonical_json import encode_canonical_json
from code_structure_viz.source.git_repository import (
    Commit,
    CommitTreeEntry,
    EnumeratedPath,
    GitReadError,
    GitRepositoryReader,
    HeadState,
)
from code_structure_viz.source.source_view import (
    AcquisitionStage,
    SourceAcquisitionFailure,
    SourceFile,
    SourceFileKind,
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
    ) -> None:
        self._builder = SourceViewBuilder(
            repository,
            staging_root,
            staging_root_descriptor=staging_root_descriptor,
            repository_descriptor=repository_descriptor,
        )

    def freeze(
        self,
        head_state: HeadState,
        entries: tuple[EnumeratedPath, ...],
        config: PythonConfig,
    ) -> SourceView:
        return self._builder.build(head_state, entries, config)

    def assert_unchanged(
        self,
        initial: SourceView,
        head_state: HeadState,
        entries: tuple[EnumeratedPath, ...],
        config: PythonConfig,
    ) -> None:
        self._builder.assert_unchanged(initial, head_state, entries, config)


def build_commit_source_view(
    reader: GitRepositoryReader,
    commit: Commit,
    config: PythonConfig,
) -> SourceView:
    """Build an immutable SourceView directly from local Git blobs."""
    candidates = tuple(
        item
        for item in reader.enumerate_commit_tree(commit.object_id)
        if _is_candidate(item.path, config)
    )
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
            continue
        try:
            content = reader.read_commit_blob(commit.object_id, item.path)
        except (GitReadError, OSError):
            failures.append(
                SourceAcquisitionFailure(item.path, AcquisitionStage.READ, DiagnosticCode.PY_READ)
            )
            continue
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
        collision_groups=tuple(
            tuple(sorted(group, key=_path_key)) for group in collision_groups
        ),
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
