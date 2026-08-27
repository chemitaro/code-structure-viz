from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from pathlib import PurePosixPath

from code_structure_viz.adapters.python.analyzer import PythonSnapshotAnalyzer
from code_structure_viz.adapters.python.diff_renderer import (
    render_plantuml_diff,
    render_semantic_diff,
)
from code_structure_viz.adapters.python.model import PythonCoverage, PythonSnapshot
from code_structure_viz.adapters.python.module_index import PythonModuleIndex
from code_structure_viz.adapters.python.selection import (
    PythonSelectionResult,
    PythonTargetSelector,
)
from code_structure_viz.artifacts.manifest import DiffManifestBuilder
from code_structure_viz.artifacts.writer import (
    OutputTransaction,
    OutputTransactionError,
    PublicationInterrupted,
)
from code_structure_viz.cli.parser import DiffCliRequest
from code_structure_viz.core.budget import (
    ChangedPathBudgetGate,
    EntityBudget,
    EntityBudgetGate,
)
from code_structure_viz.core.config import (
    ConfigResolutionError,
    ConfigSource,
    ResolvedConfig,
    resolve_config,
)
from code_structure_viz.core.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    canonical_diagnostics,
    diagnostic,
)
from code_structure_viz.core.outcomes import DomainOutcome, DomainStatus, RunOutcome
from code_structure_viz.semantic.canonical_json import encode_canonical_json
from code_structure_viz.semantic.diff import (
    DomainPresenceResolver,
    SemanticDiffer,
    SemanticDiffResult,
)
from code_structure_viz.source.endpoints import (
    ComparisonEndpointResolver,
    EndpointKind,
    EndpointResolutionError,
)
from code_structure_viz.source.file_changes import (
    FileChangeSet,
    attach_content_hunks,
    build_working_tree_file_change_set,
    parse_name_status,
)
from code_structure_viz.source.freezer import WorkingTreeFreezer, build_commit_source_view
from code_structure_viz.source.git_repository import (
    Commit,
    EnumeratedPath,
    GitInterruptedError,
    GitReadError,
    GitRepositoryReader,
    HeadState,
)
from code_structure_viz.source.source_view import (
    SourceDriftError,
    SourceInterruptedError,
    SourceView,
    SourceViewBuildError,
)

_DIFF_ARTIFACT_FORMATS = {"semantic-json": "semantic-json", "plantuml": "plantuml"}


class DiffApplication:
    """Own one safe Python dual-snapshot comparison lifecycle."""

    def __init__(
        self,
        *,
        cancelled: Callable[[], bool] | None = None,
        artifacts_bound: Callable[[dict[str, bytes]], None] | None = None,
    ) -> None:
        self._cancelled = cancelled or (lambda: False)
        self._artifacts_bound = artifacts_bound or (lambda _artifacts: None)

    def run(self, request: DiffCliRequest) -> RunOutcome:
        transaction: OutputTransaction | None = None
        working_freezer: WorkingTreeFreezer | None = None
        working_entries: tuple[EnumeratedPath, ...] = ()
        untracked_paths: tuple[PurePosixPath, ...] = ()
        unmerged_paths: tuple[PurePosixPath, ...] = ()
        semantic_result: SemanticDiffResult | None = None
        try:
            self._checkpoint()
            if request.from_ref == "working-tree":
                return RunOutcome.usage((diagnostic(DiagnosticCode.USAGE_GRAMMAR),))
            reader = GitRepositoryReader(request.repo, cancelled=self._cancelled)
            reader.validate_git_version()
            repository = reader.validate_repository_root()
            config = resolve_config(request, repository)
            start_head = reader.resolve_head_state()
            working_tree_requested = request.to_ref in {None, "working-tree"}
            if working_tree_requested:
                working_entries = reader.enumerate_path_entries()
                untracked_paths = reader.enumerate_untracked_paths()
                unmerged_paths = reader.enumerate_unmerged_paths()
            self._checkpoint()
            endpoints = ComparisonEndpointResolver(
                reader,
                comparison=config.comparison,
            ).resolve(
                from_ref=request.from_ref,
                to_ref=request.to_ref,
                pr_target=request.pr_target,
                start_head=start_head if isinstance(start_head, Commit) else None,
            )
            before_id = endpoints.before.object_id
            if before_id is None:
                raise EndpointResolutionError(diagnostic(DiagnosticCode.DIFF_ENDPOINT))
            after_id = endpoints.after.object_id

            transaction = OutputTransaction(
                repository,
                request.output_dir,
                repository_identity=reader.repository_identity,
            )
            transaction.begin()
            if endpoints.after.kind is EndpointKind.WORKING_TREE:
                working_freezer = WorkingTreeFreezer(
                    repository,
                    transaction.staging_root,
                    staging_root_descriptor=transaction.staging_root_descriptor,
                    repository_descriptor=transaction.repository_descriptor,
                    cancelled=self._cancelled,
                )
                after_source = working_freezer.freeze(start_head, working_entries, config.python)
            before_source = build_commit_source_view(reader, Commit(before_id), config.python)
            if endpoints.after.kind is EndpointKind.WORKING_TREE:
                assert working_freezer is not None
                file_changes = build_working_tree_file_change_set(
                    before_source.inventory,
                    after_source.inventory,
                    untracked_paths=untracked_paths,
                    unmerged_paths=unmerged_paths,
                    before_contents=_source_contents(before_source),
                    after_contents=_source_contents(after_source),
                    before=before_id,
                    after=None,
                )
            else:
                if endpoints.after.commit is None:
                    raise EndpointResolutionError(diagnostic(DiagnosticCode.DIFF_ENDPOINT))
                after_source = build_commit_source_view(
                    reader,
                    endpoints.after.commit,
                    config.python,
                )
                try:
                    changed_paths = parse_name_status(reader.diff_name_status(before_id, after_id))
                except ValueError as error:
                    raise GitReadError(diagnostic(DiagnosticCode.DIFF_FILE_CHANGE)) from error
                file_changes = attach_content_hunks(
                    changed_paths,
                    before_contents=_source_contents(before_source),
                    after_contents=_source_contents(after_source),
                    before=before_id,
                    after=after_id,
                )
            changed_path_budget = ChangedPathBudgetGate().admit(
                actual=file_changes.count,
                requested=request.max_changed_paths_override,
                resolved=(request.max_changed_paths_override or 1000),
                source=(
                    ConfigSource.CLI
                    if request.max_changed_paths_override is not None
                    else ConfigSource.BUILTIN
                ),
            )
            if not changed_path_budget.admitted:
                return RunOutcome.fatal((diagnostic(DiagnosticCode.DIFF_CHANGED_PATH_BUDGET),))
            has_unmerged = any(item.status == "U" for item in file_changes)
            self._checkpoint()
            semantic_sides: dict[str, object]
            if has_unmerged:
                domain = self._unmerged_domain(request, config, before_source, after_source)
                before_selection = self._analyze(before_source, config)
                before_snapshot, before_failed, _before_coverage = self._selection_snapshot(
                    before_selection
                )
                before_side = DomainPresenceResolver.side(
                    before_snapshot,
                    digest=before_source.fingerprint if before_failed else None,
                    head_commit=before_source.head_commit,
                    file_count=len(before_source.files),
                    analysis_failed=before_failed,
                )
                after_side = DomainPresenceResolver.side(
                    None,
                    digest=after_source.fingerprint,
                    head_commit=after_source.head_commit,
                    file_count=len(after_source.files),
                    analysis_failed=True,
                )
                semantic_sides = {
                    "before": before_side.to_json_value(),
                    "after": after_side.to_json_value(),
                }
            else:
                before_selection = self._analyze(before_source, config)
                self._checkpoint()
                after_selection = self._analyze(after_source, config)
                self._checkpoint()
                before_snapshot, before_failed, before_coverage = self._selection_snapshot(
                    before_selection
                )
                after_snapshot, after_failed, after_coverage = self._selection_snapshot(
                    after_selection
                )
                before_side = DomainPresenceResolver.side(
                    before_snapshot,
                    digest=before_source.fingerprint if before_failed else None,
                    head_commit=before_source.head_commit,
                    file_count=len(before_source.files),
                    analysis_failed=before_failed,
                )
                after_side = DomainPresenceResolver.side(
                    after_snapshot,
                    digest=after_source.fingerprint if after_failed else None,
                    head_commit=after_source.head_commit,
                    file_count=len(after_source.files),
                    analysis_failed=after_failed,
                )
                semantic_result = SemanticDiffer().compare(
                    before_snapshot,
                    after_snapshot,
                    before_side=before_side,
                    after_side=after_side,
                    upstream_depth=config.traversal.upstream_depth,
                    downstream_depth=config.traversal.downstream_depth,
                )
                diagnostics = canonical_diagnostics(
                    (*before_selection.diagnostics, *after_selection.diagnostics)
                )
                semantic_result = _with_diagnostics(semantic_result, diagnostics)
                semantic_sides = {
                    "before": semantic_result.before.to_json_value(),
                    "after": semantic_result.after.to_json_value(),
                }
                domain = self._domain_outcome(
                    request,
                    config,
                    semantic_result,
                    diagnostics,
                    before_coverage,
                    after_coverage,
                )

            change_content = _file_change_content(file_changes)
            transaction.stage_diff_payload("file-change-set", change_content)
            if domain.payload_available:
                if semantic_result is None:
                    raise ValueError("available diff outcome lost its semantic result")
                for format_value in request.formats:
                    if format_value == "semantic-json":
                        content = render_semantic_diff(semantic_result, file_changes)
                    else:
                        content = render_plantuml_diff(semantic_result)
                    transaction.stage_diff_payload(format_value, content)

            outcome = (
                RunOutcome.incomplete((domain,), manifest_relative_path="run-manifest.json")
                if domain.status is DomainStatus.INCOMPLETE
                else RunOutcome.completed((domain,), manifest_relative_path="run-manifest.json")
            )
            manifest = DiffManifestBuilder().render(
                request=request,
                config=config,
                outcome=outcome,
                endpoints=endpoints,
                before_source=before_source,
                after_source=after_source,
                file_changes=file_changes,
                artifacts=transaction.descriptors,
                changed_path_budget=changed_path_budget.budget,
                semantic_sides=semantic_sides,
            )
            transaction.stage_manifest(manifest)
            self._checkpoint()
            if endpoints.after.kind is EndpointKind.WORKING_TREE:
                current_head = reader.resolve_head_state()
                current_entries = reader.enumerate_path_entries()
                current_untracked = reader.enumerate_untracked_paths()
                current_unmerged = reader.enumerate_unmerged_paths()
                if current_untracked != untracked_paths or current_unmerged != unmerged_paths:
                    raise SourceDriftError(diagnostic(DiagnosticCode.SOURCE_DRIFT))
                assert working_freezer is not None
                working_freezer.assert_unchanged(
                    after_source,
                    current_head,
                    current_entries,
                    config.python,
                )
            self._artifacts_bound(transaction.read_staged_artifacts())
            transaction.commit(self._cancelled)
            return outcome
        except ConfigResolutionError as error:
            return RunOutcome.usage((error.diagnostic,))
        except EndpointResolutionError as error:
            return RunOutcome.fatal((error.diagnostic,))
        except GitInterruptedError:
            return RunOutcome.interrupted((diagnostic(DiagnosticCode.INTERRUPTED),))
        except PublicationInterrupted:
            return RunOutcome.interrupted((diagnostic(DiagnosticCode.INTERRUPTED),))
        except SourceInterruptedError:
            return RunOutcome.interrupted((diagnostic(DiagnosticCode.INTERRUPTED),))
        except (GitReadError, OutputTransactionError) as error:
            return RunOutcome.fatal((error.diagnostic,))
        except SourceViewBuildError as error:
            return RunOutcome.fatal((error.diagnostic,))
        except Exception:
            return RunOutcome.fatal((diagnostic(DiagnosticCode.INTERNAL_INVARIANT),))
        finally:
            if transaction is not None:
                transaction.abort()

    @staticmethod
    def _analyze(source: SourceView, config: ResolvedConfig) -> PythonSelectionResult:
        analysis = PythonSnapshotAnalyzer().analyze(PythonModuleIndex.build(source, config.python))
        return PythonTargetSelector().select(
            analysis,
            (),
            config.traversal.upstream_depth,
            config.traversal.downstream_depth,
        )

    @staticmethod
    def _selection_snapshot(
        selection: PythonSelectionResult,
    ) -> tuple[PythonSnapshot | None, bool, PythonCoverage]:
        if selection.status is DomainStatus.NOT_APPLICABLE:
            return None, False, selection.coverage
        if selection.status is DomainStatus.COMPLETE:
            return selection.snapshot, False, selection.coverage
        return None, True, selection.coverage

    @staticmethod
    def _build_after_source(
        reader: GitRepositoryReader,
        working_tree: bool,
        commit: Commit | None,
        transaction: OutputTransaction,
        start_head: HeadState,
        config: ResolvedConfig,
    ) -> SourceView:
        if not working_tree:
            if commit is None:
                raise EndpointResolutionError(diagnostic(DiagnosticCode.DIFF_ENDPOINT))
            return build_commit_source_view(reader, commit, config.python)
        entries = reader.enumerate_path_entries()
        return WorkingTreeFreezer(
            reader.repository,
            transaction.staging_root,
            staging_root_descriptor=transaction.staging_root_descriptor,
            repository_descriptor=transaction.repository_descriptor,
        ).freeze(start_head, entries, config.python)

    @staticmethod
    def _domain_outcome(
        request: DiffCliRequest,
        config: ResolvedConfig,
        result: SemanticDiffResult,
        diagnostics: tuple[Diagnostic, ...],
        before_coverage: PythonCoverage,
        after_coverage: PythonCoverage,
    ) -> DomainOutcome:
        budget = EntityBudget(
            "max_entities",
            request.max_entities_override,
            config.limits.max_entities,
            0 if result.status == "not_applicable" else result.entity_count,
            config.value_sources.max_entities,
        )
        if result.status == "not_applicable":
            return DomainOutcome.not_applicable(
                diagnostics=diagnostics,
                coverage=_diff_coverage(before_coverage, after_coverage),
                budget=budget,
            )
        if result.status != "complete":
            return DomainOutcome.payload_unavailable(
                diagnostics=diagnostics,
                entity_count=None,
                coverage=_diff_coverage(before_coverage, after_coverage),
                budget=budget,
            )
        decision = EntityBudgetGate().admit(
            actual=result.entity_count,
            requested=request.max_entities_override,
            resolved=config.limits.max_entities,
            source=config.value_sources.max_entities,
        )
        if not decision.admitted:
            return DomainOutcome.payload_unavailable(
                diagnostics=canonical_diagnostics((*diagnostics, *decision.diagnostics)),
                entity_count=result.entity_count,
                coverage=_diff_coverage(before_coverage, after_coverage),
                budget=decision.budget,
            )
        paths = tuple(
            {
                "semantic-json": "python.diff.semantic.json",
                "plantuml": "python.diff.puml",
            }[format_value]
            for format_value in request.formats
        )
        return DomainOutcome.complete(
            result,
            artifact_paths=paths,
            diagnostics=diagnostics,
            entity_count=result.entity_count,
            coverage=_diff_coverage(before_coverage, after_coverage),
            budget=decision.budget,
        )

    @staticmethod
    def _unmerged_domain(
        request: DiffCliRequest,
        config: ResolvedConfig,
        before_source: SourceView,
        after_source: SourceView,
    ) -> DomainOutcome:
        empty_coverage = PythonCoverage(
            len(before_source.files),
            0,
            (),
            (),
            0,
            (),
        )
        after_coverage = PythonCoverage(
            len(after_source.files),
            0,
            (),
            (),
            0,
            (),
        )
        budget = EntityBudget(
            "max_entities",
            request.max_entities_override,
            config.limits.max_entities,
            None,
            config.value_sources.max_entities,
        )
        return DomainOutcome.payload_unavailable(
            diagnostics=(diagnostic(DiagnosticCode.DIFF_FILE_CHANGE),),
            entity_count=None,
            coverage=_diff_coverage(empty_coverage, after_coverage),
            budget=budget,
        )

    def _checkpoint(self) -> None:
        if self._cancelled():
            raise PublicationInterrupted(diagnostic(DiagnosticCode.INTERRUPTED))


def _with_diagnostics(
    result: SemanticDiffResult,
    diagnostics: tuple[Diagnostic, ...],
) -> SemanticDiffResult:
    return replace(result, diagnostics=diagnostics)


def _diff_coverage(
    before: PythonCoverage,
    after: PythonCoverage,
) -> dict[str, object]:
    from code_structure_viz.adapters.python.semantic_json import coverage_value

    return {"before": coverage_value(before), "after": coverage_value(after)}


def _file_change_content(file_changes: FileChangeSet) -> bytes:
    return encode_canonical_json(file_changes.to_json_value())


def _source_contents(source: SourceView) -> dict[PurePosixPath, bytes]:
    return {item.path: item.content for item in source.files}
