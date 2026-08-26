from __future__ import annotations

import keyword
from dataclasses import dataclass
from pathlib import PurePosixPath

from code_structure_viz.adapters.python.model import (
    FailedSourceFile,
    FailedStage,
    failed_source_sort_key,
)
from code_structure_viz.core.config import PythonConfig
from code_structure_viz.core.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    canonical_diagnostics,
    diagnostic,
)
from code_structure_viz.source.source_view import (
    AcquisitionStage,
    SourceFile,
    SourceView,
)


@dataclass(frozen=True, slots=True)
class IndexedModule:
    module: str
    source: SourceFile

    @property
    def id(self) -> str:
        return f"python:module:{self.module}"

    @property
    def path(self) -> PurePosixPath:
        return self.source.path


@dataclass(frozen=True, slots=True)
class ModuleCollision:
    module: str
    paths: tuple[PurePosixPath, ...]


@dataclass(frozen=True, slots=True)
class PythonModuleIndex:
    modules: tuple[IndexedModule, ...]
    failures: tuple[FailedSourceFile, ...]
    diagnostics: tuple[Diagnostic, ...]
    collisions: tuple[ModuleCollision, ...]
    candidate_file_count: int

    @property
    def collided_modules(self) -> tuple[str, ...]:
        return tuple(item.module for item in self.collisions)

    @classmethod
    def build(cls, source_view: SourceView, config: PythonConfig) -> PythonModuleIndex:
        failures: list[FailedSourceFile] = []
        diagnostics: list[Diagnostic] = []
        collision_failure_paths: set[PurePosixPath] = set()
        for source_failure in source_view.failures:
            stage = (
                FailedStage.READ
                if source_failure.stage is AcquisitionStage.READ
                else FailedStage.PATH_SAFETY
            )
            failures.append(
                FailedSourceFile(
                    source_failure.path,
                    stage,
                    source_failure.diagnostic_code,
                )
            )
            if source_failure.diagnostic_code is DiagnosticCode.SOURCE_PATH_COLLISION:
                collision_failure_paths.add(source_failure.path)
                continue
            diagnostics.append(
                diagnostic(
                    source_failure.diagnostic_code,
                    domain="python",
                    path=source_failure.path.as_posix(),
                )
            )
        covered_collision_paths: set[PurePosixPath] = set()
        for collision_group in source_view.collision_groups:
            group_paths = tuple(
                sorted(
                    (path for path in collision_group if path in collision_failure_paths),
                    key=_path_key,
                )
            )
            if not group_paths:
                continue
            covered_collision_paths.update(group_paths)
            diagnostics.append(
                diagnostic(
                    DiagnosticCode.SOURCE_PATH_COLLISION,
                    domain="python",
                    path=group_paths[0].as_posix(),
                )
            )
        for path in sorted(collision_failure_paths - covered_collision_paths, key=_path_key):
            diagnostics.append(
                diagnostic(
                    DiagnosticCode.SOURCE_PATH_COLLISION,
                    domain="python",
                    path=path.as_posix(),
                )
            )

        candidates: dict[str, list[SourceFile]] = {}
        for source in source_view.files:
            module = _module_name(source.path, config.source_roots)
            if module is None:
                failures.append(
                    FailedSourceFile(
                        source.path,
                        FailedStage.MODULE_IDENTITY,
                        DiagnosticCode.PY_MODULE_IDENTITY,
                    )
                )
                diagnostics.append(
                    diagnostic(
                        DiagnosticCode.PY_MODULE_IDENTITY,
                        domain="python",
                        path=source.path.as_posix(),
                    )
                )
                continue
            candidates.setdefault(module, []).append(source)

        modules: list[IndexedModule] = []
        collisions: list[ModuleCollision] = []
        for module, sources in candidates.items():
            if len(sources) == 1:
                modules.append(IndexedModule(module, sources[0]))
                continue
            paths = tuple(sorted((source.path for source in sources), key=_path_key))
            collisions.append(ModuleCollision(module, paths))
            failures.extend(
                FailedSourceFile(
                    path, FailedStage.MODULE_COLLISION, DiagnosticCode.PY_MODULE_COLLISION
                )
                for path in paths
            )
            diagnostics.append(
                diagnostic(
                    DiagnosticCode.PY_MODULE_COLLISION,
                    domain="python",
                    symbol=f"python:module:{module}",
                )
            )

        return cls(
            modules=tuple(sorted(modules, key=lambda item: _utf8(item.module))),
            failures=tuple(sorted(failures, key=failed_source_sort_key)),
            diagnostics=canonical_diagnostics(tuple(diagnostics)),
            collisions=tuple(sorted(collisions, key=lambda item: _utf8(item.module))),
            candidate_file_count=len(source_view.files) + len(source_view.failures),
        )


def _utf8(value: str) -> bytes:
    return value.encode("utf-8")


def _path_key(value: PurePosixPath) -> bytes:
    return _utf8(value.as_posix())


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
