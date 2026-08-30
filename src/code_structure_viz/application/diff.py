from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

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
from code_structure_viz.adapters.sqlalchemy.analyzer import SqlAlchemySnapshotAnalyzer
from code_structure_viz.adapters.sqlalchemy.diff import (
    SqlAlchemyDiffer,
    SqlAlchemyDiffResult,
)
from code_structure_viz.adapters.sqlalchemy.model import (
    SqlAlchemyCoverage,
    SqlAlchemySnapshot,
)
from code_structure_viz.adapters.sqlalchemy.plantuml import render_sqlalchemy_diff
from code_structure_viz.adapters.sqlalchemy.selection import (
    SqlAlchemySelectionResult,
    SqlAlchemyTargetSelector,
)
from code_structure_viz.adapters.sqlalchemy.semantic_json import (
    coverage_value as sqlalchemy_coverage_value,
)
from code_structure_viz.adapters.sqlalchemy.semantic_json import (
    render_sqlalchemy_diff as render_sqlalchemy_semantic_diff,
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
    DuplicateCanonicalPathError,
    FileChangeSet,
    attach_content_hunks,
    build_working_tree_file_change_set,
    content_evidence_from_inventory,
    parse_name_status,
    unavailable_content_paths,
    validate_cross_side_path_identities,
)
from code_structure_viz.source.freezer import WorkingTreeFreezer, build_commit_source_view
from code_structure_viz.source.git_repository import (
    Commit,
    EnumeratedPath,
    GitIndexEntry,
    GitInterruptedError,
    GitlinkWorktreeState,
    GitPathIdentity,
    GitReadError,
    GitRepositoryReader,
    HeadState,
    UntrackedObservation,
)
from code_structure_viz.source.python_modules import PythonSourceIndex
from code_structure_viz.source.source_view import (
    SourceDriftError,
    SourceInterruptedError,
    SourceView,
    SourceViewBuildError,
    with_content_unavailable_failures,
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
        working_source_authority: SourceView | None = None
        working_entries: tuple[EnumeratedPath, ...] = ()
        index_entries: tuple[GitIndexEntry, ...] = ()
        untracked_entries: tuple[GitPathIdentity, ...] = ()
        initial_untracked_observation: UntrackedObservation | None = None
        unmerged_entries: tuple[GitPathIdentity, ...] = ()
        gitlink_states: tuple[GitlinkWorktreeState, ...] = ()
        semantic_result: SemanticDiffResult | SqlAlchemyDiffResult | None = None
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
                index_entries = reader.enumerate_index_entries()
                untracked_entries = reader.enumerate_untracked_entries()
                initial_untracked_observation = reader.last_untracked_observation
                if initial_untracked_observation is None:
                    raise GitReadError(diagnostic(DiagnosticCode.DIFF_FILE_CHANGE))
                unmerged_entries = reader.enumerate_unmerged_entries()
                gitlink_states = reader.enumerate_gitlink_states(index_entries)
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
                after_source = working_freezer.freeze(
                    start_head,
                    working_entries,
                    config.python,
                    untracked_paths=frozenset(item.canonical_path for item in untracked_entries),
                    unmerged_paths=frozenset(item.canonical_path for item in unmerged_entries),
                    index_entries=index_entries,
                    untracked_entries=untracked_entries,
                    unmerged_entries=unmerged_entries,
                    gitlink_states=gitlink_states,
                )
                working_source_authority = after_source
            before_source = build_commit_source_view(reader, Commit(before_id), config.python)
            if endpoints.after.kind is EndpointKind.WORKING_TREE:
                assert working_freezer is not None
                validate_cross_side_path_identities(before_source.inventory, after_source.inventory)
                file_changes = build_working_tree_file_change_set(
                    before_source.inventory,
                    after_source.inventory,
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
                validate_cross_side_path_identities(before_source.inventory, after_source.inventory)
                try:
                    changed_paths = parse_name_status(reader.diff_name_status(before_id, after_id))
                except ValueError as error:
                    raise GitReadError(diagnostic(DiagnosticCode.DIFF_FILE_CHANGE)) from error
                file_changes = FileChangeSet(changed_paths, before=before_id, after=after_id)
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
            before_content = content_evidence_from_inventory(before_source.inventory)
            after_content = content_evidence_from_inventory(after_source.inventory)
            unavailable_before, unavailable_after = unavailable_content_paths(
                file_changes,
                before_contents=before_content,
                after_contents=after_content,
            )
            before_source = with_content_unavailable_failures(
                before_source,
                unavailable_before,
                config.python,
            )
            after_source = with_content_unavailable_failures(
                after_source,
                unavailable_after,
                config.python,
            )
            file_changes = attach_content_hunks(
                file_changes,
                before_contents=before_content,
                after_contents=after_content,
                before=file_changes.before,
                after=file_changes.after,
            )
            has_unmerged = any(item.status == "U" for item in file_changes)
            self._checkpoint()
            semantic_sides: dict[str, object]
            if has_unmerged:
                if request.domain == "python":
                    python_before_selection = self._analyze(before_source, config)
                    domain, semantic_sides = self._unmerged_domain(
                        request,
                        config,
                        before_source,
                        after_source,
                        python_before_selection,
                    )
                else:
                    sqlalchemy_before_selection = self._analyze_sqlalchemy(before_source, config)
                    domain, semantic_sides = self._unmerged_sqlalchemy_domain(
                        request,
                        config,
                        before_source,
                        after_source,
                        sqlalchemy_before_selection,
                    )
            else:
                if request.domain == "python":
                    python_before_selection = self._analyze(before_source, config)
                    self._checkpoint()
                    python_after_selection = self._analyze(after_source, config)
                    self._checkpoint()
                    python_before_snapshot, before_failed, python_before_coverage = (
                        self._selection_snapshot(python_before_selection)
                    )
                    python_after_snapshot, after_failed, python_after_coverage = (
                        self._selection_snapshot(python_after_selection)
                    )
                    before_side = DomainPresenceResolver.side(
                        python_before_snapshot,
                        digest=before_source.fingerprint if before_failed else None,
                        head_commit=before_source.head_commit,
                        file_count=len(before_source.files),
                        analysis_failed=before_failed,
                    )
                    after_side = DomainPresenceResolver.side(
                        python_after_snapshot,
                        digest=after_source.fingerprint if after_failed else None,
                        head_commit=after_source.head_commit,
                        file_count=len(after_source.files),
                        analysis_failed=after_failed,
                    )
                    semantic_result = SemanticDiffer().compare(
                        python_before_snapshot,
                        python_after_snapshot,
                        before_side=before_side,
                        after_side=after_side,
                        upstream_depth=config.traversal.upstream_depth,
                        downstream_depth=config.traversal.downstream_depth,
                    )
                    diagnostics = canonical_diagnostics(
                        (
                            *python_before_selection.diagnostics,
                            *python_after_selection.diagnostics,
                        )
                    )
                    semantic_result = _with_diagnostics(semantic_result, diagnostics)
                    domain = self._domain_outcome(
                        request,
                        config,
                        semantic_result,
                        diagnostics,
                        python_before_coverage,
                        python_after_coverage,
                    )
                else:
                    sqlalchemy_before_selection = self._analyze_sqlalchemy(before_source, config)
                    self._checkpoint()
                    sqlalchemy_after_selection = self._analyze_sqlalchemy(after_source, config)
                    self._checkpoint()
                    sqlalchemy_before_snapshot, before_failed, sqlalchemy_before_coverage = (
                        self._sqlalchemy_selection_snapshot(sqlalchemy_before_selection)
                    )
                    sqlalchemy_after_snapshot, after_failed, sqlalchemy_after_coverage = (
                        self._sqlalchemy_selection_snapshot(sqlalchemy_after_selection)
                    )
                    semantic_result = SqlAlchemyDiffer().compare(
                        sqlalchemy_before_snapshot,
                        sqlalchemy_after_snapshot,
                        before_analysis_failed=before_failed,
                        after_analysis_failed=after_failed,
                        upstream_depth=config.traversal.upstream_depth,
                        downstream_depth=config.traversal.downstream_depth,
                        before_head_commit=before_source.head_commit,
                        after_head_commit=after_source.head_commit,
                        before_file_count=len(before_source.files),
                        after_file_count=len(after_source.files),
                        before_failure_digest=before_source.fingerprint,
                        after_failure_digest=after_source.fingerprint,
                    )
                    diagnostics = canonical_diagnostics(
                        (
                            *sqlalchemy_before_selection.diagnostics,
                            *sqlalchemy_after_selection.diagnostics,
                        )
                    )
                    domain = self._sqlalchemy_domain_outcome(
                        request,
                        config,
                        semantic_result,
                        diagnostics,
                        sqlalchemy_before_coverage,
                        sqlalchemy_after_coverage,
                    )
                semantic_sides = {
                    "before": semantic_result.before.to_json_value(),
                    "after": semantic_result.after.to_json_value(),
                }

            change_content = _file_change_content(file_changes)
            transaction.stage_diff_payload(request.domain, "file-change-set", change_content)
            if domain.payload_available:
                if semantic_result is None:
                    raise ValueError("available diff outcome lost its semantic result")
                for format_value in request.formats:
                    if request.domain == "python":
                        assert isinstance(semantic_result, SemanticDiffResult)
                        content = (
                            render_semantic_diff(semantic_result, file_changes)
                            if format_value == "semantic-json"
                            else render_plantuml_diff(semantic_result)
                        )
                    else:
                        assert isinstance(semantic_result, SqlAlchemyDiffResult)
                        content = (
                            render_sqlalchemy_semantic_diff(semantic_result, file_changes)
                            if format_value == "semantic-json"
                            else render_sqlalchemy_diff(semantic_result)
                        )
                    transaction.stage_diff_payload(request.domain, format_value, content)

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
                try:
                    current_head = reader.resolve_head_state()
                    current_entries = reader.enumerate_path_entries()
                    current_index_entries = reader.enumerate_index_entries()
                    current_untracked = reader.enumerate_untracked_entries()
                    current_untracked_observation = reader.last_untracked_observation
                    current_unmerged = reader.enumerate_unmerged_entries()
                    current_gitlink_states = reader.enumerate_gitlink_states(current_index_entries)
                except GitInterruptedError:
                    raise
                except GitReadError as error:
                    raise SourceDriftError(diagnostic(DiagnosticCode.SOURCE_DRIFT)) from error
                if (
                    current_index_entries != index_entries
                    or current_untracked != untracked_entries
                    or current_untracked_observation != initial_untracked_observation
                    or current_unmerged != unmerged_entries
                    or current_gitlink_states != gitlink_states
                ):
                    raise SourceDriftError(diagnostic(DiagnosticCode.SOURCE_DRIFT))
                assert working_freezer is not None
                assert working_source_authority is not None
                working_freezer.assert_unchanged(
                    working_source_authority,
                    current_head,
                    current_entries,
                    config.python,
                    untracked_paths=frozenset(item.canonical_path for item in current_untracked),
                    unmerged_paths=frozenset(item.canonical_path for item in current_unmerged),
                    index_entries=current_index_entries,
                    untracked_entries=current_untracked,
                    unmerged_entries=current_unmerged,
                    gitlink_states=current_gitlink_states,
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
        except DuplicateCanonicalPathError:
            return RunOutcome.fatal((diagnostic(DiagnosticCode.DIFF_FILE_CHANGE),))
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
    def _analyze_sqlalchemy(
        source: SourceView,
        config: ResolvedConfig,
    ) -> SqlAlchemySelectionResult:
        analysis = SqlAlchemySnapshotAnalyzer().analyze(
            PythonSourceIndex.build(source, config.python)
        )
        return SqlAlchemyTargetSelector().select(
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
    def _sqlalchemy_selection_snapshot(
        selection: SqlAlchemySelectionResult,
    ) -> tuple[SqlAlchemySnapshot | None, bool, SqlAlchemyCoverage]:
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
                domain="python",
                diagnostics=diagnostics,
                coverage=_diff_coverage(before_coverage, after_coverage),
                budget=budget,
            )
        if result.status != "complete":
            return DomainOutcome.payload_unavailable(
                domain="python",
                diagnostics=diagnostics,
                entity_count=None,
                coverage=_diff_coverage(before_coverage, after_coverage),
                budget=budget,
            )
        decision = EntityBudgetGate().admit(
            domain="python",
            actual=result.entity_count,
            requested=request.max_entities_override,
            resolved=config.limits.max_entities,
            source=config.value_sources.max_entities,
        )
        if not decision.admitted:
            return DomainOutcome.payload_unavailable(
                domain="python",
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
            domain="python",
            artifact_paths=paths,
            diagnostics=diagnostics,
            entity_count=result.entity_count,
            coverage=_diff_coverage(before_coverage, after_coverage),
            budget=decision.budget,
        )

    @staticmethod
    def _sqlalchemy_domain_outcome(
        request: DiffCliRequest,
        config: ResolvedConfig,
        result: SqlAlchemyDiffResult,
        diagnostics: tuple[Diagnostic, ...],
        before_coverage: SqlAlchemyCoverage,
        after_coverage: SqlAlchemyCoverage,
    ) -> DomainOutcome:
        coverage = {
            "before": sqlalchemy_coverage_value(before_coverage),
            "after": sqlalchemy_coverage_value(after_coverage),
        }
        budget = EntityBudget(
            "max_entities",
            request.max_entities_override,
            config.limits.max_entities,
            0 if result.status == "not_applicable" else result.entity_count,
            config.value_sources.max_entities,
        )
        if result.status == "not_applicable":
            return DomainOutcome.not_applicable(
                domain="sqlalchemy",
                diagnostics=diagnostics,
                coverage=coverage,
                budget=budget,
            )
        if result.status != "complete":
            return DomainOutcome.payload_unavailable(
                domain="sqlalchemy",
                diagnostics=diagnostics,
                entity_count=None,
                coverage=coverage,
                budget=budget,
            )
        decision = EntityBudgetGate().admit(
            domain="sqlalchemy",
            actual=result.entity_count,
            requested=request.max_entities_override,
            resolved=config.limits.max_entities,
            source=config.value_sources.max_entities,
        )
        if not decision.admitted:
            return DomainOutcome.payload_unavailable(
                domain="sqlalchemy",
                diagnostics=canonical_diagnostics((*diagnostics, *decision.diagnostics)),
                entity_count=result.entity_count,
                coverage=coverage,
                budget=decision.budget,
            )
        paths = tuple(
            {
                "semantic-json": "sqlalchemy.diff.semantic.json",
                "plantuml": "sqlalchemy.diff.puml",
            }[format_value]
            for format_value in request.formats
        )
        return DomainOutcome.complete(
            result,
            domain="sqlalchemy",
            artifact_paths=paths,
            diagnostics=diagnostics,
            entity_count=result.entity_count,
            coverage=coverage,
            budget=decision.budget,
        )

    @staticmethod
    def _unmerged_domain(
        request: DiffCliRequest,
        config: ResolvedConfig,
        before_source: SourceView,
        after_source: SourceView,
        before_selection: PythonSelectionResult,
    ) -> tuple[DomainOutcome, dict[str, object]]:
        before_snapshot, before_failed, before_coverage = DiffApplication._selection_snapshot(
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
        diagnostics = canonical_diagnostics(
            (*before_selection.diagnostics, diagnostic(DiagnosticCode.DIFF_FILE_CHANGE))
        )
        domain = DomainOutcome.payload_unavailable(
            domain="python",
            diagnostics=diagnostics,
            entity_count=None,
            coverage=_diff_coverage(before_coverage, after_coverage),
            budget=budget,
        )
        semantic_sides: dict[str, object] = {
            "before": before_side.to_json_value(),
            "after": after_side.to_json_value(),
        }
        return domain, semantic_sides

    @staticmethod
    def _unmerged_sqlalchemy_domain(
        request: DiffCliRequest,
        config: ResolvedConfig,
        before_source: SourceView,
        after_source: SourceView,
        before_selection: SqlAlchemySelectionResult,
    ) -> tuple[DomainOutcome, dict[str, object]]:
        before_snapshot, before_failed, before_coverage = (
            DiffApplication._sqlalchemy_selection_snapshot(before_selection)
        )
        result = SqlAlchemyDiffer().compare(
            before_snapshot,
            None,
            before_analysis_failed=before_failed,
            after_analysis_failed=True,
            upstream_depth=config.traversal.upstream_depth,
            downstream_depth=config.traversal.downstream_depth,
            before_head_commit=before_source.head_commit,
            after_head_commit=after_source.head_commit,
            before_file_count=len(before_source.files),
            after_file_count=len(after_source.files),
            before_failure_digest=before_source.fingerprint,
            after_failure_digest=after_source.fingerprint,
        )
        after_coverage = SqlAlchemyCoverage(
            len(after_source.files),
            0,
            (),
            (),
            (),
            0,
            0,
            0,
            0,
            (),
            before_coverage.redaction.create(0),
        )
        diagnostics = canonical_diagnostics(
            (*before_selection.diagnostics, diagnostic(DiagnosticCode.DIFF_FILE_CHANGE))
        )
        domain = DiffApplication._sqlalchemy_domain_outcome(
            request,
            config,
            result,
            diagnostics,
            before_coverage,
            after_coverage,
        )
        return domain, {
            "before": result.before.to_json_value(),
            "after": result.after.to_json_value(),
        }

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
