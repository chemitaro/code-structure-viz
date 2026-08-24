from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, cast

from spec_dock_runtime.application.check_deps import check_deps
from spec_dock_runtime.application.close_node import close_node
from spec_dock_runtime.application.contracts import (
    CheckDepsRequest,
    ClearActiveRequest,
    CloseNodeRequest,
    IssueFinishRequest,
    IssueFinishResult,
    IssueStartRequest,
    IssueStartResult,
    SetActiveRequest,
    TargetRef,
)
from spec_dock_runtime.application.github_issue_targets import normalize_repo_slug
from spec_dock_runtime.application.repo_context import resolve_current_repo_slug
from spec_dock_runtime.application.set_active import (
    checkout_active_target,
    clear_active,
    resolve_target_node_id,
    set_active,
)
from spec_dock_runtime.application.sync_state import post_mutation_sync
from spec_dock_runtime.domain.models import DepsEvaluation, SpecGraph, SpecNode, SpecNodeKind, SpecNodeSeed
from spec_dock_runtime.domain.tree import build_graph

if TYPE_CHECKING:
    from spec_dock_runtime.application.ports import Ports
    from spec_dock_runtime.infra.contracts import ActiveManifest, StoredMetaRecord


def _to_spec_node_seed(record: StoredMetaRecord) -> SpecNodeSeed:
    return SpecNodeSeed(
        kind=cast("SpecNodeKind", record.kind),
        id=record.id,
        title=record.title,
        slug=record.slug,
        path=Path(record.path),
        meta_path=Path(record.meta_path),
        parent_id=record.parent_id,
        initiative_id=record.initiative_id,
        epic_id=record.epic_id,
        github_issue_number=record.github_issue_number,
        github_repo_owner=record.github_repo_owner,
        github_repo_name=record.github_repo_name,
    )


def _resolve_repo_root(ports: Ports) -> Path:
    if ports.repo_root is None:
        raise RuntimeError("repo_root is required")
    return ports.repo_root


def _resolve_specdock_dir(ports: Ports) -> Path:
    if ports.specdock_dir is not None:
        return ports.specdock_dir
    if ports.repo_root is not None:
        return ports.repo_root / "spec-dock"
    raise RuntimeError("specdock_dir is required")


def _build_graph(ports: Ports) -> SpecGraph:
    records = ports.node_reader.load_node_records()
    if not records:
        raise RuntimeError("No nodes found. Create at least one initiative/epic/issue.")
    return build_graph([_to_spec_node_seed(record) for record in records])


def _resolve_target_node(graph: SpecGraph, target: TargetRef) -> SpecNode:
    return graph.nodes_by_id[resolve_target_node_id(graph, target)]


def _active_issue_id(manifest: ActiveManifest | None) -> str | None:
    if manifest is None or manifest.issue is None:
        return None
    return manifest.issue.id


def _github_state_for_node(node: SpecNode, ports: Ports, *, current_repo_slug: str | None) -> str:
    if node.github_issue_number is None:
        return "UNKNOWN"
    if ports.issue_gateway is None:
        return "UNKNOWN"
    repo_slug = normalize_repo_slug(node.github_repo_owner, node.github_repo_name) or current_repo_slug
    try:
        snapshot = ports.issue_gateway.issue_view_snapshot(
            _resolve_repo_root(ports),
            int(node.github_issue_number),
            repo_slug=repo_slug,
        )
    except RuntimeError:
        return "UNKNOWN"
    state = str(snapshot.state).strip().upper()
    return state or "UNKNOWN"


def _format_issue_target(node: SpecNode) -> str:
    return node.id


def _unfinished_issue_start_guidance(
    *,
    active_issue_id: str,
    current_branch: str,
    requested_issue_id: str,
    github_state: str,
    active_node_resolved: bool,
) -> str:
    active_resolution = "resolved" if active_node_resolved else "missing"
    return "\n".join([
        "issue start blocked: unfinished active issue",
        f"- current active issue: {active_issue_id}",
        f"- current branch: {current_branch}",
        f"- requested issue: {requested_issue_id}",
        f"- github state: {github_state}",
        f"- active node resolution: {active_resolution}",
        "The current branch is diagnostic only; it does not change this guard.",
        "Next commands:",
        "  spec-dock/scripts/spec-dock issue finish",
        f"  spec-dock/scripts/spec-dock issue start {requested_issue_id} -f",
        f"  spec-dock/scripts/spec-dock active set {requested_issue_id}",
    ])


def _dependency_issue_start_guidance(*, requested_issue_id: str, evaluation: DepsEvaluation) -> str:
    blockers = [str(value) for value in getattr(evaluation, "blockers", ())]
    for blocker in getattr(evaluation, "node_blockers", ()):
        node_id = str(getattr(blocker, "node_id", "")).strip()
        if node_id and node_id not in blockers:
            blockers.append(node_id)
    blocker_lines = [f"- blocker: {blocker}" for blocker in blockers] or ["- blocker: unknown"]
    return "\n".join([
        "issue start blocked: dependency readiness failed",
        f"- requested issue: {requested_issue_id}",
        f"- guard reason: {getattr(evaluation, 'guard_reason', 'unknown')}",
        *blocker_lines,
        "`--force` bypasses only the unfinished active issue guard.",
        "Next command:",
        f"  spec-dock/scripts/spec-dock deps check {requested_issue_id}",
    ])


def _checkout_issue_start_failure(*, requested_issue_id: str, error: Exception) -> RuntimeError:
    return RuntimeError(
        "\n".join([
            "issue start failed during branch checkout.",
            f"- requested issue: {requested_issue_id}",
            "Active selection was not changed.",
            "Post-mutation sync was not run.",
            "Recovery:",
            "  fix the Git checkout failure shown below",
            f"  spec-dock/scripts/spec-dock issue start {requested_issue_id}",
            str(error),
        ])
    )


def _active_write_issue_start_failure(
    *,
    requested_issue_id: str,
    before_branch: str,
    after_branch: str,
    error: Exception,
) -> RuntimeError:
    rollback = "failed" if "rollback_failed:" in str(error) else "restored"
    return RuntimeError(
        "\n".join([
            "issue start failed while persisting active selection after checkout.",
            f"- requested issue: {requested_issue_id}",
            f"- branch side effect: {before_branch} -> {after_branch}",
            f"- active rollback: {rollback}",
            "Post-mutation sync was not run.",
            "Recovery:",
            "  spec-dock/scripts/spec-dock active show",
            f"  spec-dock/scripts/spec-dock issue start {requested_issue_id}",
            str(error),
        ])
    )


def _finish_failure_guidance(*, active_issue_id: str, error: RuntimeError) -> str:
    return "\n".join([
        f"issue finish failed while closing GitHub issue for active issue {active_issue_id}.",
        "- github_closed=false",
        "- active_cleared=false",
        "- post_sync=not_run",
        "Active selection was not cleared.",
        "Recovery:",
        "  spec-dock/scripts/spec-dock active show",
        "  spec-dock/scripts/spec-dock issue finish",
        "  gh issue view <github-issue-number>",
        str(error),
    ])


def _finish_active_clear_failure_guidance(
    *,
    active_issue_id: str,
    github_issue_number: int,
    already_closed: bool,
    error: Exception,
) -> str:
    return "\n".join([
        f"issue finish failed after GitHub close/already-closed step for active issue {active_issue_id}.",
        f"- github_issue_number={github_issue_number}",
        "- github_closed=true",
        f"- already_closed={'true' if already_closed else 'false'}",
        "- active_cleared=false",
        "- post_sync=not_run",
        "Active selection remains set.",
        "Recovery:",
        "  spec-dock/scripts/spec-dock active show",
        "  spec-dock/scripts/spec-dock issue finish",
        "  spec-dock/scripts/spec-dock active set <issue-id>",
        "Post-mutation sync was not run; derived artifacts remain stale.",
        str(error),
    ])


def issue_start(req: IssueStartRequest, ports: Ports) -> IssueStartResult:
    if ports.active_state_store is None:
        raise RuntimeError("active_state_store is required")
    if ports.git_gateway is None:
        raise RuntimeError("git_gateway is required")

    graph = _build_graph(ports)
    current_repo_slug = resolve_current_repo_slug(ports)
    requested = _resolve_target_node(graph, req.target)
    if requested.kind != "issue":
        raise RuntimeError(f"issue start only accepts issue nodes: target={requested.id} kind={requested.kind}")

    specdock_dir = _resolve_specdock_dir(ports)
    active_load = ports.active_state_store.load_active_manifest(specdock_dir)
    active_issue_id = _active_issue_id(active_load.manifest)
    current_branch = ports.git_gateway.current_branch_or_none(_resolve_repo_root(ports)) or "(detached)"

    if active_issue_id is not None and active_issue_id != requested.id and not req.force:
        active_node = graph.nodes_by_id.get(active_issue_id)
        github_state = (
            _github_state_for_node(active_node, ports, current_repo_slug=current_repo_slug)
            if active_node is not None
            else "UNKNOWN"
        )
        if github_state != "CLOSED":
            raise RuntimeError(
                _unfinished_issue_start_guidance(
                    active_issue_id=active_issue_id,
                    current_branch=current_branch,
                    requested_issue_id=requested.id,
                    github_state=github_state,
                    active_node_resolved=active_node is not None,
                )
            )

    canonical_target = TargetRef(kind="node_id", node_id=requested.id, github_issue_number=None)
    deps_result = check_deps(
        CheckDepsRequest(target=canonical_target, use_github=True, issue_limit=req.issue_limit),
        ports,
    )
    evaluation = deps_result.inspection.evaluation
    if not evaluation.ready:
        raise RuntimeError(
            _dependency_issue_start_guidance(
                requested_issue_id=requested.id,
                evaluation=evaluation,
            )
        )

    warnings = list(deps_result.warnings)
    if req.force:
        warnings.insert(0, f"issue start forced=true guard=unfinished_active_issue requested={requested.id}")

    try:
        branch = checkout_active_target(
            graph=graph,
            target_id=requested.id,
            ports=ports,
            warnings=warnings,
        )
    except Exception as error:
        raise _checkout_issue_start_failure(requested_issue_id=requested.id, error=error) from error

    try:
        active_set_result = set_active(
            SetActiveRequest(
                target=canonical_target,
                force=False,
                checkout=False,
                use_github=False,
                issue_limit=req.issue_limit,
            ),
            ports,
        )
    except Exception as error:
        after_branch = ports.git_gateway.current_branch_or_none(_resolve_repo_root(ports)) or "(detached)"
        raise _active_write_issue_start_failure(
            requested_issue_id=requested.id,
            before_branch=current_branch,
            after_branch=after_branch,
            error=error,
        ) from error

    active_set_result = replace(active_set_result, branch=branch)
    for warning in active_set_result.warnings:
        if warning not in warnings:
            warnings.append(warning)
    post_sync = post_mutation_sync(ports)
    return IssueStartResult(
        target_display=_format_issue_target(requested),
        requested_issue_id=requested.id,
        active_set=active_set_result,
        forced=bool(req.force),
        warnings=warnings,
        post_sync=post_sync,
    )


def issue_finish(req: IssueFinishRequest, ports: Ports) -> IssueFinishResult:
    del req
    if ports.active_state_store is None:
        raise RuntimeError("active_state_store is required")

    specdock_dir = _resolve_specdock_dir(ports)
    active_load = ports.active_state_store.load_active_manifest(specdock_dir)
    active_issue_id = _active_issue_id(active_load.manifest)
    if active_issue_id is None:
        raise RuntimeError(
            "issue finish requires an active issue. Recovery: run issue start <issue> or active set <issue>."
        )

    try:
        close_result = close_node(
            CloseNodeRequest(
                target=TargetRef(kind="node_id", node_id=active_issue_id, github_issue_number=None),
                run_post_sync=False,
            ),
            ports,
        )
    except RuntimeError as error:
        raise RuntimeError(_finish_failure_guidance(active_issue_id=active_issue_id, error=error)) from error
    try:
        clear_result = clear_active(ClearActiveRequest(), ports)
    except Exception as error:
        raise RuntimeError(
            _finish_active_clear_failure_guidance(
                active_issue_id=active_issue_id,
                github_issue_number=close_result.github_issue_number,
                already_closed=close_result.already_closed,
                error=error,
            )
        ) from error
    post_sync = post_mutation_sync(ports)
    warnings = [*active_load.warnings, *close_result.warnings, *clear_result.warnings]
    return IssueFinishResult(
        issue_id=close_result.node_id,
        github_issue_number=close_result.github_issue_number,
        already_closed=close_result.already_closed,
        active_cleared=clear_result.cleared,
        warnings=warnings,
        post_sync=post_sync,
    )
