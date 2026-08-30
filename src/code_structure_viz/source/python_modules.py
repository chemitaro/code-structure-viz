from __future__ import annotations

import keyword
from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath

from code_structure_viz.core.config import PythonConfig
from code_structure_viz.core.diagnostics import DiagnosticCode
from code_structure_viz.source.source_view import AcquisitionStage, SourceFile, SourceView


class PythonSourceStage(StrEnum):
    READ = "read"
    PATH_SAFETY = "path_safety"
    MODULE_IDENTITY = "module_identity"
    MODULE_COLLISION = "module_collision"


@dataclass(frozen=True, slots=True)
class PythonSourceFailure:
    path: PurePosixPath
    stage: PythonSourceStage
    source_code: DiagnosticCode | None


@dataclass(frozen=True, slots=True)
class PythonSourceModule:
    module: str
    source: SourceFile


@dataclass(frozen=True, slots=True)
class PythonSourceCollision:
    module: str
    paths: tuple[PurePosixPath, ...]


@dataclass(frozen=True, slots=True)
class PythonSourceIndex:
    modules: tuple[PythonSourceModule, ...]
    failures: tuple[PythonSourceFailure, ...]
    collisions: tuple[PythonSourceCollision, ...]
    candidate_file_count: int

    @classmethod
    def build(cls, source_view: SourceView, config: PythonConfig) -> PythonSourceIndex:
        failures = [
            PythonSourceFailure(
                item.path,
                (
                    PythonSourceStage.READ
                    if item.stage is AcquisitionStage.READ
                    else PythonSourceStage.PATH_SAFETY
                ),
                item.diagnostic_code,
            )
            for item in source_view.failures
        ]
        candidates: dict[str, list[SourceFile]] = {}
        for source in source_view.files:
            module = _module_name(source.path, config.source_roots)
            if module is None:
                failures.append(
                    PythonSourceFailure(
                        source.path,
                        PythonSourceStage.MODULE_IDENTITY,
                        None,
                    )
                )
                continue
            candidates.setdefault(module, []).append(source)

        modules: list[PythonSourceModule] = []
        collisions: list[PythonSourceCollision] = []
        for module, sources in candidates.items():
            if len(sources) == 1:
                modules.append(PythonSourceModule(module, sources[0]))
                continue
            paths = tuple(sorted((source.path for source in sources), key=_path_key))
            collisions.append(PythonSourceCollision(module, paths))
            failures.extend(
                PythonSourceFailure(path, PythonSourceStage.MODULE_COLLISION, None)
                for path in paths
            )

        return cls(
            modules=tuple(
                sorted(
                    modules,
                    key=lambda item: (_utf8(item.module), _path_key(item.source.path)),
                )
            ),
            failures=tuple(sorted(failures, key=_failure_key)),
            collisions=tuple(
                sorted(
                    collisions,
                    key=lambda item: (
                        _utf8(item.module),
                        tuple(_path_key(path) for path in item.paths),
                    ),
                )
            ),
            candidate_file_count=len(source_view.files) + len(source_view.failures),
        )


def _utf8(value: str) -> bytes:
    return value.encode("utf-8")


def _path_key(value: PurePosixPath) -> bytes:
    return _utf8(value.as_posix())


def _failure_key(value: PythonSourceFailure) -> tuple[bytes, bytes, bytes]:
    return (
        _path_key(value.path),
        _utf8(value.stage.value),
        _utf8(value.source_code.value if value.source_code is not None else ""),
    )


def _module_name(path: PurePosixPath, source_roots: tuple[str, ...]) -> str | None:
    matches: list[tuple[int, int, PurePosixPath]] = []
    for order, raw_root in enumerate(source_roots):
        root = PurePosixPath(raw_root)
        if raw_root == ".":
            relative = path
            depth = 0
        elif path != root and root not in path.parents:
            continue
        else:
            relative = path.relative_to(root)
            depth = len(root.parts)
        matches.append((depth, -order, relative))
    if not matches:
        return None
    _, _, relative = max(matches, key=lambda item: (item[0], item[1]))
    if relative.suffix != ".py":
        return None
    parts = [*relative.parts[:-1], relative.name.removesuffix(".py")]
    if parts[-1] == "__init__":
        parts.pop()
    if not parts:
        parts = ["__init__"]
    if not all(part.isidentifier() and not keyword.iskeyword(part) for part in parts):
        return None
    return ".".join(parts)
