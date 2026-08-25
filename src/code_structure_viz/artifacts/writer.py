from __future__ import annotations

import json
import os
import re
import shutil
import stat
import tempfile
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path

from code_structure_viz.artifacts.manifest import (
    ArtifactDescriptor,
    ArtifactFormat,
)
from code_structure_viz.core.diagnostics import Diagnostic, DiagnosticCode, diagnostic
from code_structure_viz.semantic.canonical_json import encode_canonical_json

_FINAL_PATHS = frozenset(
    {
        "python.snapshot.semantic.json",
        "python.snapshot.puml",
        "run-manifest.json",
    }
)
_PLANTUML_RELATION = re.compile(
    r"(?:C|M)_[0-9a-f]{64} (?:<\|--|\*--|\.\.>) (?:C|M)_[0-9a-f]{64} : "
    r"(?:継承|合成|型依存|import依存)"
)


class OutputTransactionError(RuntimeError):
    def __init__(self, value: Diagnostic) -> None:
        self.diagnostic = value
        super().__init__(value.message)


class PublicationInterrupted(OutputTransactionError):
    pass


def _error(code: DiagnosticCode) -> OutputTransactionError:
    return OutputTransactionError(diagnostic(code))


def _is_within(path: Path, root: Path) -> bool:
    try:
        return os.path.commonpath((str(path), str(root))) == str(root)
    except ValueError:
        return False


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    fd = os.open(path, flags)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _canonical_json_bytes(content: bytes) -> bool:
    try:
        if content.startswith(b"\xef\xbb\xbf") or not content.endswith(b"\n"):
            return False
        if content.endswith(b"\n\n"):
            return False
        value = json.loads(content.decode("utf-8", errors="strict"))
        return encode_canonical_json(value) == content
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
        return False


def _valid_plantuml(content: bytes) -> bool:
    try:
        text = content.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return False
    if not text.endswith("\n") or text.endswith("\n\n"):
        return False
    lines = text[:-1].split("\n")
    if not lines or lines[0] != "@startuml" or lines[-1] != "@enduml":
        return False
    allowed_exact = {
        "@startuml",
        "@enduml",
        "title Python structure snapshot",
        "left to right direction",
        "skinparam classAttributeIconSize 0",
        "hide empty members",
        "legend right",
        "  <|-- 継承",
        "  *-- 合成",
        "  ..> 型依存",
        "  package ..> package import依存",
        "endlegend",
        "}",
        "  }",
    }
    allowed_prefixes = (
        'note "不完全なsnapshot:',
        'package "',
        '  note "classなし" as N_EMPTY_',
        '  class "',
        "    field ",
        "    property ",
        "    method ",
    )
    return all(
        line in allowed_exact
        or line.startswith(allowed_prefixes)
        or _PLANTUML_RELATION.fullmatch(line) is not None
        for line in lines
    )


class OutputTransaction:
    def __init__(self, repository: Path, output_dir: Path) -> None:
        try:
            self.repository = repository.resolve(strict=True)
            self.output_dir = output_dir.resolve(strict=False)
            parent = self.output_dir.parent
            parent_stat = parent.stat(follow_symlinks=False)
        except OSError as error:
            raise _error(DiagnosticCode.OUTPUT_DESTINATION) from error
        if _is_within(self.output_dir, self.repository):
            raise _error(DiagnosticCode.OUTPUT_INSIDE_REPO)
        if os.path.lexists(self.output_dir) or not stat.S_ISDIR(parent_stat.st_mode):
            raise _error(DiagnosticCode.OUTPUT_DESTINATION)
        self.parent = parent
        self._staging_root: Path | None = None
        self._descriptors: dict[str, ArtifactDescriptor] = {}
        self._manifest_staged = False
        self._committed = False

    @property
    def staging_root(self) -> Path:
        if self._staging_root is None:
            raise RuntimeError("output transaction has not begun")
        return self._staging_root

    def begin(self) -> Path:
        if self._staging_root is not None:
            raise RuntimeError("output transaction already began")
        try:
            root = Path(
                tempfile.mkdtemp(
                    prefix=".code-structure-viz-staging-",
                    dir=self.parent,
                )
            )
            root.chmod(0o700)
            (root / "source").mkdir(mode=0o700)
            (root / "artifacts").mkdir(mode=0o700)
        except OSError as error:
            if "root" in locals():
                shutil.rmtree(root, ignore_errors=True)
            raise _error(DiagnosticCode.OUTPUT_DESTINATION) from error
        self._staging_root = root
        return root

    def stage_payload(self, format_value: ArtifactFormat, content: bytes) -> ArtifactDescriptor:
        descriptor = ArtifactDescriptor.create(format_value, content)
        if descriptor.path in self._descriptors:
            raise _error(DiagnosticCode.INTERNAL_INVARIANT)
        self._validate_content(descriptor.path, content)
        self._write(descriptor.path, content)
        self._descriptors[descriptor.path] = descriptor
        return descriptor

    def stage_manifest(self, content: bytes) -> None:
        if self._manifest_staged:
            raise _error(DiagnosticCode.INTERNAL_INVARIANT)
        self._validate_content("run-manifest.json", content)
        self._write("run-manifest.json", content)
        self._manifest_staged = True

    @property
    def descriptors(self) -> tuple[ArtifactDescriptor, ...]:
        rank = {"semantic-json": 0, "plantuml": 1}
        return tuple(
            sorted(
                self._descriptors.values(),
                key=lambda item: (rank[item.format], item.path.encode("utf-8")),
            )
        )

    def commit(self, cancelled: Callable[[], bool] | None = None) -> None:
        if self._committed or not self._manifest_staged:
            raise _error(DiagnosticCode.INTERNAL_INVARIANT)
        cancellation_probe = cancelled or (lambda: False)
        try:
            self._remove_frozen_source()
            _fsync_directory(self.staging_root / "artifacts")
            if cancellation_probe():
                raise PublicationInterrupted(diagnostic(DiagnosticCode.INTERRUPTED))
            if os.path.lexists(self.output_dir):
                raise _error(DiagnosticCode.OUTPUT_DESTINATION)
            os.rename(self.staging_root / "artifacts", self.output_dir)
            self._committed = True
        except PublicationInterrupted:
            self.abort()
            raise
        except OutputTransactionError:
            self.abort()
            raise
        except OSError as error:
            self.abort()
            raise _error(DiagnosticCode.OUTPUT_DESTINATION) from error

        with suppress(OSError):
            self.staging_root.rmdir()
        with suppress(OSError):
            _fsync_directory(self.parent)

    def abort(self) -> None:
        if self._committed:
            return
        root = self._staging_root
        if root is not None:
            shutil.rmtree(root, ignore_errors=True)

    def _write(self, relative_path: str, content: bytes) -> None:
        if relative_path not in _FINAL_PATHS or type(content) is not bytes:
            raise _error(DiagnosticCode.INTERNAL_INVARIANT)
        destination = self.staging_root / "artifacts" / relative_path
        try:
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
            raise _error(DiagnosticCode.OUTPUT_DESTINATION) from error

    def _validate_content(self, relative_path: str, content: bytes) -> None:
        private_values = (
            str(self.repository).encode("utf-8"),
            str(self.staging_root).encode("utf-8"),
        )
        if b"\0" in content or any(value and value in content for value in private_values):
            raise _error(DiagnosticCode.INTERNAL_INVARIANT)
        valid = (
            _valid_plantuml(content)
            if relative_path == "python.snapshot.puml"
            else _canonical_json_bytes(content)
        )
        if not valid:
            raise _error(DiagnosticCode.INTERNAL_INVARIANT)

    def _remove_frozen_source(self) -> None:
        source = self.staging_root / "source"
        try:
            for root_text, directories, files in os.walk(source, topdown=False, followlinks=False):
                root = Path(root_text)
                for name in files:
                    (root / name).unlink()
                _fsync_directory(root)
                for name in directories:
                    (root / name).rmdir()
            source.rmdir()
            _fsync_directory(self.staging_root)
        except OSError as error:
            raise _error(DiagnosticCode.OUTPUT_DESTINATION) from error
