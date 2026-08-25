from __future__ import annotations

from dataclasses import dataclass

from code_structure_viz.adapters.python.analyzer import PythonAnalysisResult
from code_structure_viz.adapters.python.model import (
    CoverageFrontier,
    FailedStage,
    FrontierDirection,
    FrontierKind,
    FrontierReason,
    PythonCoverage,
    PythonSnapshot,
    TargetResolution,
    entity_sort_key,
    frontier_sort_key,
    member_sort_key,
    relation_sort_key,
)
from code_structure_viz.core.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    canonical_diagnostics,
    diagnostic,
)
from code_structure_viz.core.outcomes import DomainStatus, IncompleteKind
from code_structure_viz.source.targets import (
    ModuleTarget,
    PathTarget,
    TargetSpec,
    target_sort_key,
)


@dataclass(frozen=True, slots=True)
class PythonSelectionResult:
    status: DomainStatus
    incomplete_kind: IncompleteKind | None
    snapshot: PythonSnapshot | None
    coverage: PythonCoverage
    diagnostics: tuple[Diagnostic, ...]

    def __post_init__(self) -> None:
        if self.status is DomainStatus.COMPLETE:
            if self.incomplete_kind is not None or self.snapshot is None:
                raise ValueError("complete selection requires a snapshot")
        elif self.status is DomainStatus.NOT_APPLICABLE:
            if self.incomplete_kind is not None or self.snapshot is not None:
                raise ValueError("not-applicable selection cannot carry a snapshot")
        elif self.incomplete_kind is IncompleteKind.PARTIAL_SAFE:
            if self.snapshot is None:
                raise ValueError("partial-safe selection requires a snapshot")
        elif self.incomplete_kind is IncompleteKind.PAYLOAD_UNAVAILABLE:
            if self.snapshot is not None:
                raise ValueError("payload-unavailable selection cannot carry a snapshot")
        else:
            raise ValueError("incomplete selection requires a kind")


@dataclass(frozen=True, slots=True)
class _TargetFailure:
    target: TargetSpec
    code: DiagnosticCode


class PythonTargetSelector:
    def select(
        self,
        analysis: PythonAnalysisResult,
        targets: tuple[TargetSpec, ...],
        upstream_depth: int,
        downstream_depth: int,
    ) -> PythonSelectionResult:
        if not targets and analysis.candidate_file_count == 0 and not analysis.failures:
            coverage = PythonCoverage(0, 0, (), (), 0, ())
            return PythonSelectionResult(DomainStatus.NOT_APPLICABLE, None, None, coverage, ())

        base_frontier = _failure_frontier(analysis)
        if not targets:
            selected_nodes = {
                *(item.id for item in analysis.modules),
                *(item.id for item in analysis.entities),
            }
            return _selection_from_nodes(
                analysis,
                selected_nodes,
                base_frontier,
                whole=True,
            )

        seeds: set[str] = set()
        target_failures: list[_TargetFailure] = []
        for target in sorted(targets, key=target_sort_key):
            resolved, failure = _resolve_target(analysis, target)
            if failure is not None:
                target_failures.append(failure)
            else:
                seeds.update(resolved)

        if target_failures:
            target_diagnostics = tuple(_target_diagnostic(item) for item in target_failures)
            frontier = tuple(
                sorted(
                    {
                        *base_frontier,
                        *analysis.frontier,
                        *(_target_frontier(item.target) for item in target_failures),
                    },
                    key=frontier_sort_key,
                )
            )
            diagnostics = canonical_diagnostics((*analysis.diagnostics, *target_diagnostics))
            coverage = PythonCoverage(
                analysis.candidate_file_count,
                analysis.parsed_file_count,
                analysis.failures,
                (),
                0,
                frontier,
            )
            return PythonSelectionResult(
                DomainStatus.INCOMPLETE,
                IncompleteKind.PAYLOAD_UNAVAILABLE,
                None,
                coverage,
                diagnostics,
            )

        selected_nodes, depth_frontier = _traverse(
            analysis, seeds, upstream_depth, downstream_depth
        )
        return _selection_from_nodes(
            analysis,
            selected_nodes,
            (*base_frontier, *depth_frontier),
            whole=False,
        )


def _resolve_target(
    analysis: PythonAnalysisResult, target: TargetSpec
) -> tuple[frozenset[str], _TargetFailure | None]:
    parsed_paths = {item.path: item.id for item in analysis.modules}
    source_collision_paths = {
        item.path
        for item in analysis.failures
        if item.diagnostic_code is DiagnosticCode.SOURCE_PATH_COLLISION
    }
    if isinstance(target, PathTarget):
        module_id = parsed_paths.get(target.value)
        if module_id is not None:
            return frozenset({module_id}), None
        code = (
            DiagnosticCode.PY_TARGET_AMBIGUOUS
            if target.value in source_collision_paths
            else DiagnosticCode.PY_TARGET_MISSING
        )
        return frozenset(), _TargetFailure(target, code)

    parsed_modules = {item.module: item.id for item in analysis.modules}
    collision_modules = {item.module for item in analysis.module_collisions}
    indexed_modules = {item.module for item in analysis.indexed_modules}
    if isinstance(target, ModuleTarget):
        if target.value in parsed_modules:
            return frozenset({parsed_modules[target.value]}), None
        code = (
            DiagnosticCode.PY_TARGET_AMBIGUOUS
            if target.value in collision_modules
            else DiagnosticCode.PY_TARGET_MISSING
        )
        return frozenset(), _TargetFailure(target, code)

    all_modules = {*parsed_modules, *collision_modules, *indexed_modules}
    parts = target.raw.split(".")
    module = next(
        (
            ".".join(parts[:end])
            for end in range(len(parts) - 1, 0, -1)
            if ".".join(parts[:end]) in all_modules
        ),
        None,
    )
    if module is None:
        return frozenset(), _TargetFailure(target, DiagnosticCode.PY_TARGET_MISSING)
    if module in collision_modules:
        return frozenset(), _TargetFailure(target, DiagnosticCode.PY_TARGET_AMBIGUOUS)
    qualified_name = target.raw[len(module) + 1 :]
    entity_id = f"python:class:{module}:{qualified_name}"
    if any(item.entity_id == entity_id for item in analysis.class_collisions):
        return frozenset(), _TargetFailure(target, DiagnosticCode.PY_TARGET_AMBIGUOUS)
    if any(item.id == entity_id for item in analysis.entities):
        return frozenset({entity_id}), None
    if module not in parsed_modules and module in indexed_modules:
        return frozenset(), _TargetFailure(target, DiagnosticCode.PY_TARGET_MISSING)
    return frozenset(), _TargetFailure(target, DiagnosticCode.PY_TARGET_MISSING)


def _target_diagnostic(failure: _TargetFailure) -> Diagnostic:
    target = failure.target
    if isinstance(target, PathTarget):
        return diagnostic(
            failure.code,
            domain="python",
            path=target.value.as_posix(),
        )
    symbol = f"module:{target.value}" if isinstance(target, ModuleTarget) else f"class:{target.raw}"
    return diagnostic(failure.code, domain="python", symbol=symbol)


def _target_frontier(target: TargetSpec) -> CoverageFrontier:
    if isinstance(target, PathTarget):
        kind = FrontierKind.FILE
        reference = target.value.as_posix()
    elif isinstance(target, ModuleTarget):
        kind = FrontierKind.MODULE
        reference = f"python:module:{target.value}"
    else:
        kind = FrontierKind.SYMBOL
        reference = f"class:{target.raw}"
    return CoverageFrontier(
        FrontierDirection.FAILURE,
        kind,
        reference,
        FrontierReason.UNRESOLVED_REFERENCE,
    )


def _failure_frontier(
    analysis: PythonAnalysisResult,
) -> tuple[CoverageFrontier, ...]:
    values = [
        CoverageFrontier(
            FrontierDirection.FAILURE,
            FrontierKind.FILE,
            item.path.as_posix(),
            (
                FrontierReason.IDENTITY_COLLISION
                if item.stage in {FailedStage.PATH_SAFETY, FailedStage.MODULE_COLLISION}
                else FrontierReason.FAILED_SOURCE
            ),
        )
        for item in analysis.failures
    ]
    return tuple(sorted(set(values), key=frontier_sort_key))


def _membership_closure(
    nodes: set[str],
    module_classes: dict[str, set[str]],
    class_module: dict[str, str],
) -> set[str]:
    result = set(nodes)
    changed = True
    while changed:
        changed = False
        for node in tuple(result):
            if node.startswith("python:module:"):
                additions = module_classes.get(node, set()) - result
            else:
                module = class_module.get(node)
                additions = ({module} if module is not None else set()) - result
            if additions:
                result.update(additions)
                changed = True
    return result


def _traverse_direction(
    seeds: set[str],
    adjacency: dict[str, set[str]],
    depth: int,
    module_classes: dict[str, set[str]],
    class_module: dict[str, str],
) -> tuple[set[str], set[str]]:
    visited = _membership_closure(seeds, module_classes, class_module)
    level = set(visited)
    for _ in range(depth):
        neighbors = {target for source in level for target in adjacency.get(source, set())}
        next_level = (
            _membership_closure(neighbors - visited, module_classes, class_module) - visited
        )
        if not next_level:
            level = set()
            break
        visited.update(next_level)
        level = next_level
    boundary = {
        target
        for source in level
        for target in adjacency.get(source, set())
        if target not in visited
    }
    return visited, boundary


def _traverse(
    analysis: PythonAnalysisResult,
    seeds: set[str],
    upstream_depth: int,
    downstream_depth: int,
) -> tuple[set[str], tuple[CoverageFrontier, ...]]:
    module_classes: dict[str, set[str]] = {item.id: set() for item in analysis.modules}
    class_module: dict[str, str] = {}
    for entity in analysis.entities:
        module_id = f"python:module:{entity.module}"
        module_classes.setdefault(module_id, set()).add(entity.id)
        class_module[entity.id] = module_id

    forward: dict[str, set[str]] = {}
    reverse: dict[str, set[str]] = {}
    for relation in analysis.relations:
        if relation.target.resolution is not TargetResolution.INTERNAL:
            continue
        assert relation.target.id is not None
        forward.setdefault(relation.source_id, set()).add(relation.target.id)
        reverse.setdefault(relation.target.id, set()).add(relation.source_id)

    downstream, downstream_boundary = _traverse_direction(
        seeds, forward, downstream_depth, module_classes, class_module
    )
    upstream, upstream_boundary = _traverse_direction(
        seeds, reverse, upstream_depth, module_classes, class_module
    )
    selected = downstream | upstream
    frontier: set[CoverageFrontier] = set()
    for direction, nodes in (
        (FrontierDirection.UPSTREAM, upstream_boundary),
        (FrontierDirection.DOWNSTREAM, downstream_boundary),
    ):
        for node in nodes - selected:
            frontier.add(
                CoverageFrontier(
                    direction,
                    (
                        FrontierKind.MODULE
                        if node.startswith("python:module:")
                        else FrontierKind.CLASS
                    ),
                    node,
                    FrontierReason.DEPTH_LIMIT,
                )
            )
    return selected, tuple(sorted(frontier, key=frontier_sort_key))


def _analysis_frontier_for_selection(
    analysis: PythonAnalysisResult,
    selected_nodes: set[str],
) -> tuple[CoverageFrontier, ...]:
    selected_modules = {item.module for item in analysis.modules if item.id in selected_nodes}
    selected_relations = [item for item in analysis.relations if item.source_id in selected_nodes]
    values: list[CoverageFrontier] = []
    for item in analysis.frontier:
        if item.reason is FrontierReason.UNRESOLVED_REFERENCE:
            if any(
                relation.target.resolution is TargetResolution.UNKNOWN
                and relation.target.name == item.reference
                for relation in selected_relations
            ):
                values.append(item)
        elif item.reason is FrontierReason.STAR_IMPORT:
            if any(
                relation.target.id == item.reference or relation.target.name == item.reference
                for relation in selected_relations
            ):
                values.append(item)
        elif item.reason is FrontierReason.UNSUPPORTED_SCOPE:
            if any(
                item.reference.startswith(f"python:class:{module}:") for module in selected_modules
            ):
                values.append(item)
        else:
            values.append(item)
    return tuple(values)


def _selection_diagnostics(
    analysis: PythonAnalysisResult,
    selected_nodes: set[str],
    *,
    whole: bool,
) -> tuple[Diagnostic, ...]:
    if whole:
        return analysis.diagnostics
    selected_paths = {
        item.path.as_posix() for item in analysis.modules if item.id in selected_nodes
    }
    always = {
        DiagnosticCode.SOURCE_SYMLINK,
        DiagnosticCode.SOURCE_PATH_COLLISION,
        DiagnosticCode.PY_READ,
        DiagnosticCode.PY_ENCODING,
        DiagnosticCode.PY_PARSE,
        DiagnosticCode.PY_MODULE_IDENTITY,
        DiagnosticCode.PY_MODULE_COLLISION,
        DiagnosticCode.PY_CLASS_COLLISION,
    }
    return canonical_diagnostics(
        tuple(
            item
            for item in analysis.diagnostics
            if item.code in always or item.path in selected_paths
        )
    )


def _must_be_payload_unavailable(analysis: PythonAnalysisResult) -> bool:
    if any(
        item.diagnostic_code
        in {DiagnosticCode.SOURCE_SYMLINK, DiagnosticCode.SOURCE_PATH_COLLISION}
        for item in analysis.failures
    ):
        return True
    if analysis.failures and not analysis.modules:
        return True
    return bool(analysis.class_collisions and not analysis.entities)


def _selection_from_nodes(
    analysis: PythonAnalysisResult,
    selected_nodes: set[str],
    supplied_frontier: tuple[CoverageFrontier, ...],
    *,
    whole: bool,
) -> PythonSelectionResult:
    selected_modules = tuple(
        sorted(
            (item.module for item in analysis.modules if item.id in selected_nodes),
            key=lambda value: value.encode("utf-8"),
        )
    )
    selected_entities = tuple(
        sorted(
            (item for item in analysis.entities if item.id in selected_nodes),
            key=entity_sort_key,
        )
    )
    selected_entity_ids = {item.id for item in selected_entities}
    members = tuple(
        sorted(
            (item for item in analysis.members if item.owner_id in selected_entity_ids),
            key=member_sort_key,
        )
    )
    relations = tuple(
        sorted(
            (
                item
                for item in analysis.relations
                if item.source_id in selected_nodes
                and (
                    item.target.resolution is not TargetResolution.INTERNAL
                    or item.target.id in selected_nodes
                )
            ),
            key=relation_sort_key,
        )
    )
    analysis_frontier = (
        analysis.frontier if whole else _analysis_frontier_for_selection(analysis, selected_nodes)
    )
    frontier = tuple(sorted({*supplied_frontier, *analysis_frontier}, key=frontier_sort_key))
    diagnostics = _selection_diagnostics(analysis, selected_nodes, whole=whole)
    coverage = PythonCoverage(
        analysis.candidate_file_count,
        analysis.parsed_file_count,
        analysis.failures,
        selected_modules,
        len(selected_entities),
        frontier,
    )

    if _must_be_payload_unavailable(analysis):
        unavailable_coverage = PythonCoverage(
            coverage.candidate_files,
            coverage.parsed_files,
            coverage.failed_files,
            (),
            0,
            coverage.frontier,
        )
        return PythonSelectionResult(
            DomainStatus.INCOMPLETE,
            IncompleteKind.PAYLOAD_UNAVAILABLE,
            None,
            unavailable_coverage,
            diagnostics,
        )

    partial = bool(analysis.failures or analysis.class_collisions)
    snapshot = PythonSnapshot(
        selected_entities,
        members,
        relations,
        coverage,
        diagnostics,
        partial_safe=partial,
    )
    return PythonSelectionResult(
        DomainStatus.INCOMPLETE if partial else DomainStatus.COMPLETE,
        IncompleteKind.PARTIAL_SAFE if partial else None,
        snapshot,
        coverage,
        diagnostics,
    )
