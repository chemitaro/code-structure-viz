from __future__ import annotations

import sys
from collections.abc import Callable

from code_structure_viz.application.snapshot_domain import (
    SnapshotAdapterContract,
    SnapshotAnalysis,
    snapshot_adapter_for,
)
from code_structure_viz.artifacts.manifest import RunManifestBuilder, artifact_format
from code_structure_viz.artifacts.writer import (
    OutputTransaction,
    OutputTransactionError,
    PublicationInterrupted,
)
from code_structure_viz.cli.parser import SnapshotCliRequest
from code_structure_viz.core.budget import EntityBudget, EntityBudgetGate
from code_structure_viz.core.config import ConfigResolutionError, ResolvedConfig, resolve_config
from code_structure_viz.core.diagnostics import (
    DiagnosticCode,
    canonical_diagnostics,
    diagnostic,
)
from code_structure_viz.core.outcomes import (
    DomainOutcome,
    DomainStatus,
    IncompleteKind,
    RunOutcome,
)
from code_structure_viz.source.git_repository import GitReadError, GitRepositoryReader
from code_structure_viz.source.source_view import SourceViewBuilder, SourceViewBuildError


class SnapshotApplication:
    """Own one static working-tree snapshot lifecycle through publication."""

    def __init__(
        self,
        *,
        cancelled: Callable[[], bool] | None = None,
        artifacts_bound: Callable[[dict[str, bytes]], None] | None = None,
    ) -> None:
        self._cancelled = cancelled or (lambda: False)
        self._artifacts_bound = artifacts_bound or (lambda _artifacts: None)

    def run(self, request: SnapshotCliRequest) -> RunOutcome:
        transaction: OutputTransaction | None = None
        try:
            self._checkpoint()
            if sys.version_info < (3, 12):  # noqa: UP036 - runtime environment contract
                return RunOutcome.fatal((diagnostic(DiagnosticCode.ENV_PYTHON),))

            repository_reader = GitRepositoryReader(request.repo)
            repository_reader.validate_git_version()
            repository = repository_reader.validate_repository_root()
            transaction = OutputTransaction(
                repository,
                request.output_dir,
                repository_identity=repository_reader.repository_identity,
            )
            config = resolve_config(request, repository)
            head_state = repository_reader.resolve_head_state()
            entries = repository_reader.enumerate_path_entries()
            self._checkpoint()

            transaction.begin()
            source_builder = SourceViewBuilder(
                repository,
                transaction.staging_root,
                staging_root_descriptor=transaction.staging_root_descriptor,
                repository_descriptor=transaction.repository_descriptor,
            )
            source_view = source_builder.build(head_state, entries, config.python)
            adapter = snapshot_adapter_for(request.domain)
            analysis = adapter.analyze(source_view, request, config)
            domain = self._domain_outcome(request, config, analysis, adapter.contract)
            self._checkpoint()

            if domain.payload_available:
                payload = analysis.payload
                if payload is None:
                    raise ValueError("available domain outcome lost its payload")
                for format_value in request.formats:
                    content = adapter.render(
                        format_value,
                        payload,
                        source_view,
                        request,
                        config,
                    )
                    transaction.stage_snapshot_payload(
                        request.domain,
                        artifact_format(format_value),
                        content,
                    )

            outcome = (
                RunOutcome.incomplete((domain,), manifest_relative_path="run-manifest.json")
                if domain.status is DomainStatus.INCOMPLETE
                else RunOutcome.completed((domain,), manifest_relative_path="run-manifest.json")
            )
            manifest = RunManifestBuilder().render(
                request=request,
                source_view=source_view,
                config=config,
                outcome=outcome,
                artifacts=transaction.descriptors,
                adapter_contract=adapter.contract,
                coverage_encoder=adapter.coverage_value,
            )
            transaction.stage_manifest(manifest)

            current_head = repository_reader.resolve_head_state()
            current_entries = repository_reader.enumerate_path_entries()
            source_builder.assert_unchanged(
                source_view,
                current_head,
                current_entries,
                config.python,
            )
            self._artifacts_bound(transaction.read_staged_artifacts())
            transaction.commit(self._cancelled)
            return outcome
        except ConfigResolutionError as error:
            return RunOutcome.usage((error.diagnostic,))
        except PublicationInterrupted:
            return RunOutcome.interrupted((diagnostic(DiagnosticCode.INTERRUPTED),))
        except (GitReadError, SourceViewBuildError, OutputTransactionError) as error:
            return RunOutcome.fatal((error.diagnostic,))
        finally:
            if transaction is not None:
                transaction.abort()

    def _checkpoint(self) -> None:
        if self._cancelled():
            raise PublicationInterrupted(diagnostic(DiagnosticCode.INTERRUPTED))

    @staticmethod
    def _domain_outcome(
        request: SnapshotCliRequest,
        config: ResolvedConfig,
        analysis: SnapshotAnalysis,
        contract: SnapshotAdapterContract,
    ) -> DomainOutcome:
        if request.domain != contract.domain:
            raise ValueError("snapshot request and adapter domain do not match")
        source = config.value_sources.max_entities
        requested = request.max_entities_override
        if analysis.status is DomainStatus.NOT_APPLICABLE:
            budget = EntityBudget(
                "max_entities",
                requested,
                config.limits.max_entities,
                0,
                source,
            )
            return DomainOutcome.not_applicable(
                domain=contract.domain,
                diagnostics=analysis.diagnostics,
                coverage=analysis.coverage,
                budget=budget,
            )
        if analysis.incomplete_kind is IncompleteKind.PAYLOAD_UNAVAILABLE:
            budget = EntityBudget(
                "max_entities",
                requested,
                config.limits.max_entities,
                None,
                source,
            )
            return DomainOutcome.payload_unavailable(
                domain=contract.domain,
                diagnostics=analysis.diagnostics,
                entity_count=analysis.entity_count,
                coverage=analysis.coverage,
                budget=budget,
            )

        payload = analysis.payload
        actual = analysis.entity_count
        if payload is None or actual is None:
            raise ValueError("selected domain payload is unavailable")
        decision = EntityBudgetGate().admit(
            domain=contract.domain,
            actual=actual,
            requested=requested,
            resolved=config.limits.max_entities,
            source=source,
        )
        if not decision.admitted:
            return DomainOutcome.payload_unavailable(
                domain=contract.domain,
                diagnostics=canonical_diagnostics((*analysis.diagnostics, *decision.diagnostics)),
                entity_count=actual,
                coverage=analysis.coverage,
                budget=decision.budget,
            )

        artifact_paths = tuple(
            contract.semantic_path if item == "semantic-json" else contract.plantuml_path
            for item in request.formats
        )
        if analysis.incomplete_kind is IncompleteKind.PARTIAL_SAFE:
            return DomainOutcome.partial_safe(
                payload,
                domain=contract.domain,
                artifact_paths=artifact_paths,
                diagnostics=analysis.diagnostics,
                entity_count=actual,
                coverage=analysis.coverage,
                budget=decision.budget,
            )
        return DomainOutcome.complete(
            payload,
            domain=contract.domain,
            artifact_paths=artifact_paths,
            diagnostics=analysis.diagnostics,
            entity_count=actual,
            coverage=analysis.coverage,
            budget=decision.budget,
        )
