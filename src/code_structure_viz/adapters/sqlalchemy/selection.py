from __future__ import annotations

from dataclasses import dataclass

from code_structure_viz.adapters.sqlalchemy.analyzer import (
    SqlAlchemyAnalysisResult,
    SqlAlchemyApplicability,
)
from code_structure_viz.adapters.sqlalchemy.model import (
    SqlAlchemyCoverage,
    SqlAlchemyCoverageFrontier,
    SqlAlchemyFailedStage,
    SqlAlchemyFrontierDirection,
    SqlAlchemyFrontierKind,
    SqlAlchemyFrontierReason,
    SqlAlchemyMappingSourceKind,
    SqlAlchemyRedactionSummary,
    SqlAlchemyRow,
    SqlAlchemySnapshot,
    SqlAlchemyTable,
    SqlAlchemyTargetResolution,
    frontier_sort_key,
    redacted_value_count,
    relation_sort_key,
    row_sort_key,
    table_sort_key,
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
class SqlAlchemySelectionResult:
    status: DomainStatus
    incomplete_kind: IncompleteKind | None
    snapshot: SqlAlchemySnapshot | None
    coverage: SqlAlchemyCoverage
    diagnostics: tuple[Diagnostic, ...]

    def __post_init__(self) -> None:
        if self.status is DomainStatus.COMPLETE:
            if self.incomplete_kind is not None or self.snapshot is None:
                raise ValueError("complete SQLAlchemy selection requires a snapshot")
        elif self.status is DomainStatus.NOT_APPLICABLE:
            if self.incomplete_kind is not None or self.snapshot is not None or self.diagnostics:
                raise ValueError("not-applicable SQLAlchemy selection cannot carry a payload")
        elif self.incomplete_kind is IncompleteKind.PARTIAL_SAFE:
            if self.snapshot is None:
                raise ValueError("partial-safe SQLAlchemy selection requires a snapshot")
        elif self.incomplete_kind is IncompleteKind.PAYLOAD_UNAVAILABLE:
            if self.snapshot is not None:
                raise ValueError("payload-unavailable SQLAlchemy selection cannot carry a snapshot")
        else:
            raise ValueError("incomplete SQLAlchemy selection requires a kind")
        if self.snapshot is not None and (
            self.coverage != self.snapshot.coverage or self.diagnostics != self.snapshot.diagnostics
        ):
            raise ValueError("SQLAlchemy selection payload metadata is inconsistent")


@dataclass(frozen=True, slots=True)
class _TargetFailure:
    target: TargetSpec
    code: DiagnosticCode


class SqlAlchemyTargetSelector:
    def select(
        self,
        analysis: SqlAlchemyAnalysisResult,
        targets: tuple[TargetSpec, ...],
        upstream_depth: int,
        downstream_depth: int,
    ) -> SqlAlchemySelectionResult:
        normalized_targets = tuple(sorted(set(targets), key=target_sort_key))
        if not normalized_targets:
            return _whole_selection(analysis)

        seeds: set[str] = set()
        failures: list[_TargetFailure] = []
        for target in normalized_targets:
            resolved, failure = _resolve_target(analysis.snapshot, target)
            seeds.update(resolved)
            if failure is not None:
                failures.append(failure)

        if failures:
            diagnostics = canonical_diagnostics(
                (*analysis.snapshot.diagnostics, *(_target_diagnostic(item) for item in failures))
            )
            frontier = tuple(
                sorted(
                    {
                        *analysis.snapshot.coverage.frontier,
                        *(_target_frontier(item) for item in failures),
                    },
                    key=frontier_sort_key,
                )
            )
            return _unavailable(analysis, diagnostics=diagnostics, frontier=frontier)

        if analysis.applicability is not SqlAlchemyApplicability.PRESENT:
            return _unavailable(
                analysis,
                diagnostics=analysis.snapshot.diagnostics,
                frontier=analysis.snapshot.coverage.frontier,
            )

        selected, depth_frontier = _traverse(
            analysis.snapshot,
            seeds,
            upstream_depth=upstream_depth,
            downstream_depth=downstream_depth,
        )
        return _selection_from_tables(
            analysis,
            selected,
            tuple(
                sorted(
                    {*analysis.snapshot.coverage.frontier, *depth_frontier},
                    key=frontier_sort_key,
                )
            ),
        )


def _whole_selection(analysis: SqlAlchemyAnalysisResult) -> SqlAlchemySelectionResult:
    if analysis.applicability is SqlAlchemyApplicability.ABSENT:
        coverage = _selected_coverage(
            analysis.snapshot.coverage,
            entities=(),
            members=(),
            frontier=analysis.snapshot.coverage.frontier,
        )
        return SqlAlchemySelectionResult(
            DomainStatus.NOT_APPLICABLE,
            None,
            None,
            coverage,
            (),
        )
    if analysis.applicability is SqlAlchemyApplicability.INDETERMINATE:
        return _unavailable(
            analysis,
            diagnostics=analysis.snapshot.diagnostics,
            frontier=analysis.snapshot.coverage.frontier,
        )
    return _selection_from_tables(
        analysis,
        {item.id for item in analysis.snapshot.entities},
        analysis.snapshot.coverage.frontier,
    )


def _resolve_target(
    snapshot: SqlAlchemySnapshot,
    target: TargetSpec,
) -> tuple[frozenset[str], _TargetFailure | None]:
    if isinstance(target, PathTarget):
        path = target.value.as_posix()
        matches = frozenset(
            table.id
            for table in snapshot.entities
            if any(source.source.path == path for source in table.mapping_sources)
        )
    elif isinstance(target, ModuleTarget):
        matches = frozenset(
            table.id
            for table in snapshot.entities
            if any(source.module == target.value for source in table.mapping_sources)
        )
    else:
        matches = frozenset(
            table.id
            for table in snapshot.entities
            if any(
                source.kind is SqlAlchemyMappingSourceKind.DECLARATIVE_CLASS
                and source.symbol == target.raw
                for source in table.mapping_sources
            )
        )
        if len(matches) > 1:
            return frozenset(), _TargetFailure(target, DiagnosticCode.SA_TARGET_AMBIGUOUS)
    if not matches:
        return frozenset(), _TargetFailure(target, DiagnosticCode.SA_TARGET_MISSING)
    return matches, None


def _target_diagnostic(failure: _TargetFailure) -> Diagnostic:
    target = failure.target
    if isinstance(target, PathTarget):
        return diagnostic(
            failure.code,
            domain="sqlalchemy",
            path=target.value.as_posix(),
        )
    symbol = f"module:{target.value}" if isinstance(target, ModuleTarget) else f"class:{target.raw}"
    return diagnostic(failure.code, domain="sqlalchemy", symbol=symbol)


def _target_frontier(failure: _TargetFailure) -> SqlAlchemyCoverageFrontier:
    target = failure.target
    if isinstance(target, PathTarget):
        kind = SqlAlchemyFrontierKind.FILE
        reference = target.value.as_posix()
    elif isinstance(target, ModuleTarget):
        kind = SqlAlchemyFrontierKind.MODULE
        reference = f"module:{target.value}"
    else:
        kind = SqlAlchemyFrontierKind.CLASS
        reference = f"class:{target.raw}"
    return SqlAlchemyCoverageFrontier(
        SqlAlchemyFrontierDirection.FAILURE,
        kind,
        reference,
        (
            SqlAlchemyFrontierReason.TARGET_AMBIGUOUS
            if failure.code is DiagnosticCode.SA_TARGET_AMBIGUOUS
            else SqlAlchemyFrontierReason.TARGET_MISSING
        ),
    )


def _traverse_direction(
    seeds: set[str],
    adjacency: dict[str, set[str]],
    depth: int,
) -> tuple[set[str], set[str]]:
    visited = set(seeds)
    level = set(seeds)
    for _ in range(depth):
        next_level = {
            target
            for source in level
            for target in adjacency.get(source, set())
            if target not in visited
        }
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
    snapshot: SqlAlchemySnapshot,
    seeds: set[str],
    *,
    upstream_depth: int,
    downstream_depth: int,
) -> tuple[set[str], tuple[SqlAlchemyCoverageFrontier, ...]]:
    forward: dict[str, set[str]] = {}
    reverse: dict[str, set[str]] = {}
    for relation in snapshot.relations:
        if relation.target.resolution is not SqlAlchemyTargetResolution.INTERNAL:
            continue
        assert relation.target.id is not None
        forward.setdefault(relation.source_id, set()).add(relation.target.id)
        reverse.setdefault(relation.target.id, set()).add(relation.source_id)

    downstream, downstream_boundary = _traverse_direction(seeds, forward, downstream_depth)
    upstream, upstream_boundary = _traverse_direction(seeds, reverse, upstream_depth)
    selected = downstream | upstream
    frontier = {
        SqlAlchemyCoverageFrontier(
            direction,
            SqlAlchemyFrontierKind.TABLE,
            table_id,
            SqlAlchemyFrontierReason.DEPTH_LIMIT,
        )
        for direction, boundary in (
            (SqlAlchemyFrontierDirection.UPSTREAM, upstream_boundary),
            (SqlAlchemyFrontierDirection.DOWNSTREAM, downstream_boundary),
        )
        for table_id in boundary - selected
    }
    return selected, tuple(sorted(frontier, key=frontier_sort_key))


def _selection_from_tables(
    analysis: SqlAlchemyAnalysisResult,
    selected_ids: set[str],
    frontier: tuple[SqlAlchemyCoverageFrontier, ...],
) -> SqlAlchemySelectionResult:
    entities = tuple(
        sorted(
            (item for item in analysis.snapshot.entities if item.id in selected_ids),
            key=table_sort_key,
        )
    )
    entity_ids = {item.id for item in entities}
    members = tuple(
        sorted(
            (item for item in analysis.snapshot.members if item.owner_id in entity_ids),
            key=row_sort_key,
        )
    )
    relations = tuple(
        sorted(
            (
                item
                for item in analysis.snapshot.relations
                if item.source_id in entity_ids
                and item.target.resolution is SqlAlchemyTargetResolution.INTERNAL
                and item.target.id in entity_ids
            ),
            key=relation_sort_key,
        )
    )
    coverage = _selected_coverage(
        analysis.snapshot.coverage,
        entities=entities,
        members=members,
        frontier=frontier,
    )
    partial = _is_partial(analysis)
    if _must_be_payload_unavailable(analysis) or (not entities and partial):
        return _unavailable(
            analysis,
            diagnostics=analysis.snapshot.diagnostics,
            frontier=frontier,
        )
    snapshot = SqlAlchemySnapshot(
        entities,
        members,
        relations,
        coverage,
        analysis.snapshot.diagnostics,
        partial,
    )
    return SqlAlchemySelectionResult(
        DomainStatus.INCOMPLETE if partial else DomainStatus.COMPLETE,
        IncompleteKind.PARTIAL_SAFE if partial else None,
        snapshot,
        coverage,
        analysis.snapshot.diagnostics,
    )


def _is_partial(analysis: SqlAlchemyAnalysisResult) -> bool:
    coverage = analysis.snapshot.coverage
    return bool(
        analysis.snapshot.partial_safe
        or coverage.failed_files
        or coverage.unknown_declarations
        or analysis.snapshot.diagnostics
    )


def _must_be_payload_unavailable(analysis: SqlAlchemyAnalysisResult) -> bool:
    return any(
        item.stage is SqlAlchemyFailedStage.PATH_SAFETY
        for item in analysis.snapshot.coverage.failed_files
    )


def _selected_coverage(
    base: SqlAlchemyCoverage,
    *,
    entities: tuple[SqlAlchemyTable, ...],
    members: tuple[SqlAlchemyRow, ...],
    frontier: tuple[SqlAlchemyCoverageFrontier, ...],
) -> SqlAlchemyCoverage:
    selected_modules = tuple(
        sorted(
            {source.module for table in entities for source in table.mapping_sources},
            key=lambda value: value.encode("utf-8"),
        )
    )
    return SqlAlchemyCoverage(
        candidate_files=base.candidate_files,
        parsed_files=base.parsed_files,
        failed_files=base.failed_files,
        evidence_files=base.evidence_files,
        selected_modules=selected_modules,
        mapped_classes=base.mapped_classes,
        association_tables=base.association_tables,
        selected_entities=len(entities),
        unknown_declarations=base.unknown_declarations,
        frontier=tuple(sorted(set(frontier), key=frontier_sort_key)),
        redaction=SqlAlchemyRedactionSummary.create(redacted_value_count(members)),
    )


def _unavailable(
    analysis: SqlAlchemyAnalysisResult,
    *,
    diagnostics: tuple[Diagnostic, ...],
    frontier: tuple[SqlAlchemyCoverageFrontier, ...],
) -> SqlAlchemySelectionResult:
    coverage = _selected_coverage(
        analysis.snapshot.coverage,
        entities=(),
        members=(),
        frontier=frontier,
    )
    return SqlAlchemySelectionResult(
        DomainStatus.INCOMPLETE,
        IncompleteKind.PAYLOAD_UNAVAILABLE,
        None,
        coverage,
        canonical_diagnostics(diagnostics),
    )
