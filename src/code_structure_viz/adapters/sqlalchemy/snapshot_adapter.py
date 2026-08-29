from __future__ import annotations

from collections.abc import Mapping

from code_structure_viz.adapters.sqlalchemy.analyzer import SqlAlchemySnapshotAnalyzer
from code_structure_viz.adapters.sqlalchemy.model import (
    SqlAlchemyCoverage,
    SqlAlchemySnapshot,
)
from code_structure_viz.adapters.sqlalchemy.plantuml import SqlAlchemyPlantUmlRenderer
from code_structure_viz.adapters.sqlalchemy.selection import SqlAlchemyTargetSelector
from code_structure_viz.adapters.sqlalchemy.semantic_json import (
    SqlAlchemySemanticJsonRenderer,
)
from code_structure_viz.adapters.sqlalchemy.semantic_json import (
    coverage_value as sqlalchemy_coverage_value,
)
from code_structure_viz.application.snapshot_domain import (
    SnapshotAdapterContract,
    SnapshotAnalysis,
)
from code_structure_viz.cli.parser import OutputFormat, SnapshotCliRequest
from code_structure_viz.core.config import ResolvedConfig
from code_structure_viz.core.outcomes import DomainStatus
from code_structure_viz.source.python_modules import PythonSourceIndex
from code_structure_viz.source.source_view import SourceView


class SqlAlchemySnapshotDomainAdapter:
    contract = SnapshotAdapterContract(
        domain="sqlalchemy",
        adapter_name="sqlalchemy-ast",
        adapter_version="1",
        plantuml_contract="code-structure-viz.plantuml/sqlalchemy/v1",
        semantic_path="sqlalchemy.snapshot.semantic.json",
        plantuml_path="sqlalchemy.snapshot.puml",
    )

    def analyze(
        self,
        source_view: SourceView,
        request: SnapshotCliRequest,
        config: ResolvedConfig,
    ) -> SnapshotAnalysis:
        analysis = SqlAlchemySnapshotAnalyzer().analyze(
            PythonSourceIndex.build(source_view, config.python)
        )
        selection = SqlAlchemyTargetSelector().select(
            analysis,
            request.targets,
            config.traversal.upstream_depth,
            config.traversal.downstream_depth,
        )
        entity_count = (
            len(selection.snapshot.entities)
            if selection.snapshot is not None
            else 0
            if selection.status is DomainStatus.NOT_APPLICABLE
            else None
        )
        return SnapshotAnalysis(
            status=selection.status,
            incomplete_kind=selection.incomplete_kind,
            payload=selection.snapshot,
            coverage=selection.coverage,
            diagnostics=selection.diagnostics,
            entity_count=entity_count,
        )

    def render(
        self,
        format_value: OutputFormat,
        payload: object,
        source_view: SourceView,
        request: SnapshotCliRequest,
        config: ResolvedConfig,
    ) -> bytes:
        if not isinstance(payload, SqlAlchemySnapshot):
            raise ValueError("SQLAlchemy snapshot adapter received another domain payload")
        if format_value == "semantic-json":
            return SqlAlchemySemanticJsonRenderer(
                source_view=source_view,
                targets=request.targets,
                upstream_depth=config.traversal.upstream_depth,
                downstream_depth=config.traversal.downstream_depth,
            ).render(payload)
        if format_value == "plantuml":
            return SqlAlchemyPlantUmlRenderer().render(payload)
        raise ValueError("SQLAlchemy snapshot adapter received an unsupported format")

    def coverage_value(self, coverage: object) -> Mapping[str, object]:
        if not isinstance(coverage, SqlAlchemyCoverage):
            raise ValueError("SQLAlchemy snapshot adapter received another domain coverage")
        return sqlalchemy_coverage_value(coverage)
