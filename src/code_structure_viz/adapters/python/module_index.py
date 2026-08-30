from __future__ import annotations

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
from code_structure_viz.source.python_modules import (
    PythonSourceFailure,
    PythonSourceIndex,
    PythonSourceStage,
)
from code_structure_viz.source.source_view import SourceFile, SourceView


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
        language_index = PythonSourceIndex.build(source_view, config)
        failures = tuple(
            sorted(
                (_python_failure(item) for item in language_index.failures),
                key=failed_source_sort_key,
            )
        )
        diagnostics: list[Diagnostic] = []
        collision_failure_paths = {
            item.path
            for item in language_index.failures
            if item.source_code is DiagnosticCode.SOURCE_PATH_COLLISION
        }
        for item in language_index.failures:
            code = _python_failure_code(item)
            if code is DiagnosticCode.SOURCE_PATH_COLLISION or (
                item.stage is PythonSourceStage.MODULE_COLLISION
            ):
                continue
            diagnostics.append(diagnostic(code, domain="python", path=item.path.as_posix()))

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

        for collision in language_index.collisions:
            diagnostics.append(
                diagnostic(
                    DiagnosticCode.PY_MODULE_COLLISION,
                    domain="python",
                    symbol=f"python:module:{collision.module}",
                )
            )

        return cls(
            modules=tuple(
                IndexedModule(item.module, item.source) for item in language_index.modules
            ),
            failures=failures,
            diagnostics=canonical_diagnostics(tuple(diagnostics)),
            collisions=tuple(
                ModuleCollision(item.module, item.paths) for item in language_index.collisions
            ),
            candidate_file_count=language_index.candidate_file_count,
        )


def _python_failure(value: PythonSourceFailure) -> FailedSourceFile:
    stage = {
        PythonSourceStage.READ: FailedStage.READ,
        PythonSourceStage.PATH_SAFETY: FailedStage.PATH_SAFETY,
        PythonSourceStage.MODULE_IDENTITY: FailedStage.MODULE_IDENTITY,
        PythonSourceStage.MODULE_COLLISION: FailedStage.MODULE_COLLISION,
    }[value.stage]
    return FailedSourceFile(value.path, stage, _python_failure_code(value))


def _python_failure_code(value: PythonSourceFailure) -> DiagnosticCode:
    if value.source_code is not None:
        return value.source_code
    return {
        PythonSourceStage.MODULE_IDENTITY: DiagnosticCode.PY_MODULE_IDENTITY,
        PythonSourceStage.MODULE_COLLISION: DiagnosticCode.PY_MODULE_COLLISION,
    }[value.stage]


def _utf8(value: str) -> bytes:
    return value.encode("utf-8")


def _path_key(value: PurePosixPath) -> bytes:
    return _utf8(value.as_posix())
