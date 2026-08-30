from __future__ import annotations

from collections.abc import Mapping

from code_structure_viz.adapters.python.analyzer import PythonSnapshotAnalyzer
from code_structure_viz.adapters.python.model import PythonCoverage, PythonSnapshot
from code_structure_viz.adapters.python.module_index import PythonModuleIndex
from code_structure_viz.adapters.python.plantuml import PythonPlantUmlRenderer
from code_structure_viz.adapters.python.selection import PythonTargetSelector
from code_structure_viz.adapters.python.semantic_json import (
    PythonSemanticJsonRenderer,
)
from code_structure_viz.adapters.python.semantic_json import (
    coverage_value as python_coverage_value,
)
from code_structure_viz.application.snapshot_domain import (
    SnapshotAdapterContract,
    SnapshotAnalysis,
)
from code_structure_viz.cli.parser import OutputFormat, SnapshotCliRequest
from code_structure_viz.core.config import ResolvedConfig
from code_structure_viz.core.outcomes import DomainStatus
from code_structure_viz.source.source_view import SourceView


class PythonSnapshotDomainAdapter:
    contract = SnapshotAdapterContract(
        domain="python",
        adapter_name="python-ast",
        adapter_version="1",
        plantuml_contract="code-structure-viz.plantuml/python/v1",
        semantic_path="python.snapshot.semantic.json",
        plantuml_path="python.snapshot.puml",
    )

    def analyze(
        self,
        source_view: SourceView,
        request: SnapshotCliRequest,
        config: ResolvedConfig,
    ) -> SnapshotAnalysis:
        analysis = PythonSnapshotAnalyzer().analyze(
            PythonModuleIndex.build(source_view, config.python)
        )
        selection = PythonTargetSelector().select(
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
        if not isinstance(payload, PythonSnapshot):
            raise ValueError("Python snapshot adapter received another domain payload")
        if format_value == "semantic-json":
            return PythonSemanticJsonRenderer(
                source_view=source_view,
                targets=request.targets,
                upstream_depth=config.traversal.upstream_depth,
                downstream_depth=config.traversal.downstream_depth,
            ).render(payload)
        if format_value == "plantuml":
            return PythonPlantUmlRenderer().render(payload)
        raise ValueError("Python snapshot adapter received an unsupported format")

    def coverage_value(self, coverage: object) -> Mapping[str, object]:
        if not isinstance(coverage, PythonCoverage):
            raise ValueError("Python snapshot adapter received another domain coverage")
        return python_coverage_value(coverage)
