from __future__ import annotations

import fnmatch
import hashlib
import os
import stat
import unicodedata
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Final

from code_structure_viz.core.config import PythonConfig
from code_structure_viz.core.diagnostics import Diagnostic, DiagnosticCode, diagnostic
from code_structure_viz.semantic.canonical_json import encode_canonical_json
from code_structure_viz.source.git_repository import Commit, EnumeratedPath, HeadState

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


def _head_commit(state: HeadState) -> str | None:
    return state.object_id if isinstance(state, Commit) else None


def _segment_matches(pattern: str, path: str) -> bool:
    pattern_parts = pattern.split("/")
    path_parts = path.split("/")

    def match(pattern_index: int, path_index: int) -> bool:
        if pattern_index == len(pattern_parts):
            return path_index == len(path_parts)
        token = pattern_parts[pattern_index]
        if token == "**":
            return match(pattern_index + 1, path_index) or (
                path_index < len(path_parts) and match(pattern_index, path_index + 1)
            )
        return (
            path_index < len(path_parts)
            and fnmatch.fnmatchcase(path_parts[path_index], token)
            and match(pattern_index + 1, path_index + 1)
        )

    return match(0, 0)


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


def _open_read_only(path: Path) -> int:
    flags = os.O_RDONLY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    return os.open(path, flags)


class SourceViewBuilder:
    def __init__(self, repository: Path, staging_root: Path) -> None:
        self.repository = repository.resolve()
        self.staging_root = staging_root

    def build(
        self,
        head_state: HeadState,
        entries: tuple[EnumeratedPath, ...],
        config: PythonConfig,
    ) -> SourceView:
        self._prepare_staging()
        return self._collect(head_state, entries, config, write_frozen=True)

    def assert_unchanged(
        self,
        initial: SourceView,
        head_state: HeadState,
        entries: tuple[EnumeratedPath, ...],
        config: PythonConfig,
    ) -> None:
        try:
            current = self._collect(head_state, entries, config, write_frozen=False)
        except SourceViewBuildError as error:
            raise SourceDriftError(diagnostic(DiagnosticCode.SOURCE_DRIFT)) from error
        if current.fingerprint != initial.fingerprint:
            raise SourceDriftError(diagnostic(DiagnosticCode.SOURCE_DRIFT))

    def _prepare_staging(self) -> None:
        try:
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
    ) -> SourceView:
        candidates = tuple(entry for entry in entries if _is_candidate(entry.normalized, config))
        collision_paths = self._collision_paths(candidates)
        failures = [
            SourceAcquisitionFailure(
                path,
                AcquisitionStage.PATH_SAFETY,
                DiagnosticCode.SOURCE_PATH_COLLISION,
            )
            for path in collision_paths
        ]
        files: list[SourceFile] = []
        for entry in candidates:
            if entry.normalized in collision_paths:
                continue
            frozen = self._freeze(entry.normalized, write_frozen=write_frozen)
            if isinstance(frozen, SourceFile):
                files.append(frozen)
            elif frozen is not None:
                failures.append(frozen)

        ordered_files = tuple(sorted(files, key=lambda item: _path_key(item.path)))
        ordered_failures = tuple(sorted(failures, key=_failure_key))
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
        )

    def _collision_paths(self, candidates: tuple[EnumeratedPath, ...]) -> frozenset[PurePosixPath]:
        normalized_groups: dict[PurePosixPath, list[EnumeratedPath]] = {}
        for entry in candidates:
            normalized_groups.setdefault(entry.normalized, []).append(entry)
        collision_paths = {path for path, group in normalized_groups.items() if len(group) > 1}

        case_groups: dict[str, list[PurePosixPath]] = {}
        for path in normalized_groups:
            case_groups.setdefault(path.as_posix().casefold(), []).append(path)
        for group in case_groups.values():
            if len(group) < 2:
                continue
            for index, left in enumerate(group):
                for right in group[index + 1 :]:
                    try:
                        if os.path.samefile(self.repository / left, self.repository / right):
                            collision_paths.update((left, right))
                    except OSError:
                        continue
        return frozenset(collision_paths)

    def _freeze(
        self, logical_path: PurePosixPath, *, write_frozen: bool
    ) -> SourceFile | SourceAcquisitionFailure | None:
        source_path = self.repository.joinpath(*logical_path.parts)
        try:
            logical_before = source_path.lstat()
        except FileNotFoundError:
            return None
        except OSError:
            return SourceAcquisitionFailure(
                logical_path, AcquisitionStage.READ, DiagnosticCode.PY_READ
            )
        if stat.S_ISLNK(logical_before.st_mode):
            kind = SourceFileKind.SYMLINK
            try:
                opened_path = source_path.resolve(strict=True)
                relative_target = opened_path.relative_to(self.repository)
                target_before = opened_path.stat(follow_symlinks=False)
                if not stat.S_ISREG(target_before.st_mode):
                    raise _UnsafeSymlinkError
            except (OSError, RuntimeError, ValueError, _UnsafeSymlinkError):
                return SourceAcquisitionFailure(
                    logical_path,
                    AcquisitionStage.PATH_SAFETY,
                    DiagnosticCode.SOURCE_SYMLINK,
                )
            resolved_target = PurePosixPath(
                unicodedata.normalize("NFC", relative_target.as_posix())
            )
        elif stat.S_ISREG(logical_before.st_mode):
            kind = SourceFileKind.REGULAR
            opened_path = source_path
            target_before = logical_before
            resolved_target = None
        else:
            return None

        try:
            fd = _open_read_only(opened_path)
            try:
                opened_before = os.fstat(fd)
                if _stat_signature(opened_before) != _stat_signature(target_before):
                    raise _ConcurrentMutationError
                content = _read_fd(fd)
                opened_after = os.fstat(fd)
            finally:
                os.close(fd)
            logical_after = source_path.lstat()
            target_after = opened_path.stat(follow_symlinks=False)
            if (
                _stat_signature(opened_before) != _stat_signature(opened_after)
                or _stat_signature(logical_before) != _stat_signature(logical_after)
                or _stat_signature(target_before) != _stat_signature(target_after)
                or len(content) != opened_after.st_size
            ):
                raise _ConcurrentMutationError
        except _ConcurrentMutationError as error:
            raise SourceDriftError(diagnostic(DiagnosticCode.SOURCE_DRIFT)) from error
        except OSError:
            return SourceAcquisitionFailure(
                logical_path, AcquisitionStage.READ, DiagnosticCode.PY_READ
            )

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
