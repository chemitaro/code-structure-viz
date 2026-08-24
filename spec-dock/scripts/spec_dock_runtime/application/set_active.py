from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, cast

from spec_dock_runtime.application.contracts import (
    ActiveClearResult,
    ActiveSetResult,
    ActiveViewEntry,
    ActiveViewResult,
    ClearActiveRequest,
    SetActiveRequest,
    ShowActiveRequest,
    TargetRef,
)
from spec_dock_runtime.application.github_issue_targets import normalize_repo_slug
from spec_dock_runtime.domain.active import resolve_branch_decision
from spec_dock_runtime.domain.ids import format_id, parse_id
from spec_dock_runtime.domain.models import (
    ActiveSelection,
    BranchDecision,
    NodeId,
    SpecGraph,
    SpecNodeKind,
    SpecNodeSeed,
)
from spec_dock_runtime.domain.tree import build_graph, select_active_chain
from spec_dock_runtime.infra.contracts import ActiveManifest, ActiveManifestEntry, StoredMetaRecord

if TYPE_CHECKING:
    from spec_dock_runtime.application.ports import Ports


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


def _resolve_specdock_dir(ports: Ports) -> Path:
    if ports.specdock_dir is not None:
        return ports.specdock_dir
    if ports.repo_root is not None:
        return ports.repo_root / "spec-dock"
    raise RuntimeError("specdock_dir is required")


def _resolve_repo_root(ports: Ports) -> Path:
    if ports.repo_root is None:
        raise RuntimeError("repo_root is required")
    return ports.repo_root


def _to_repo_relative_specdock_path(path: Path, *, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        parts = path.parts
        if not parts:
            raise RuntimeError(f"Cannot canonicalize empty node path: {path}") from None
        if parts[0] == "spec-dock":
            return path.as_posix()
        if "spec-dock" in parts:
            index = parts.index("spec-dock")
            return Path(*parts[index:]).as_posix()
        raise RuntimeError(f"Node path is not under repo root and missing 'spec-dock' segment: {path}") from None


def _find_existing_id_by_num(graph: SpecGraph, *, prefix: str, num: int, local: bool) -> str | None:
    for node_id in graph.nodes_by_id:
        try:
            parsed_prefix, is_local, parsed_num = parse_id(str(node_id))
        except RuntimeError:
            continue
        if parsed_prefix == prefix and parsed_num == num and is_local == local:
            return str(node_id)
    return None


def resolve_target_node_id(graph: SpecGraph, target: TargetRef) -> str:
    if target.kind == "github_issue":
        if target.github_issue_number is None:
            raise RuntimeError("TargetRef.github_issue_number is required")
        matches = [
            node
            for node in graph.nodes_by_id.values()
            if node.github_issue_number == int(target.github_issue_number)
            and node.kind in ("initiative", "epic", "issue")
        ]
        target_repo_slug = normalize_repo_slug(target.github_repo_owner, target.github_repo_name)
        if target_repo_slug is not None:
            exact_scoped = [
                node
                for node in matches
                if normalize_repo_slug(node.github_repo_owner, node.github_repo_name) == target_repo_slug
            ]
            unscoped = [
                node for node in matches if normalize_repo_slug(node.github_repo_owner, node.github_repo_name) is None
            ]
            scoped = exact_scoped or unscoped
            if not scoped:
                raise RuntimeError(
                    "No node found for "
                    f"github.issue_number={int(target.github_issue_number)} in repo scope ({target_repo_slug}). "
                    "Create/link the node first."
                )
            if len(scoped) > 1:
                ids = ", ".join(sorted(f"{node.kind}:{node.id}" for node in scoped))
                raise RuntimeError(
                    f"Ambiguous github.issue_number={int(target.github_issue_number)} in repo scope "
                    f"({target_repo_slug}): {ids}"
                )
            return scoped[0].id
        if not matches:
            raise RuntimeError(
                f"No node found for github.issue_number={int(target.github_issue_number)}. Create/link the node first."
            )
        if len(matches) > 1:
            ids = ", ".join(sorted(f"{node.kind}:{node.id}" for node in matches))
            raise RuntimeError(f"Ambiguous github.issue_number={int(target.github_issue_number)}: {ids}")
        return matches[0].id

    if target.kind != "node_id":
        raise RuntimeError(f"Unsupported target kind: {target.kind}")
    if target.node_id is None:
        raise RuntimeError("TargetRef.node_id is required")

    raw_id = str(target.node_id).strip().lower()
    prefix, is_local, num = parse_id(raw_id)
    resolved = _find_existing_id_by_num(graph, prefix=prefix, num=num, local=is_local) or format_id(
        prefix, num, local=is_local
    )
    node = graph.nodes_by_id.get(resolved)
    if node is None or node.kind not in ("initiative", "epic", "issue"):
        raise RuntimeError(f"Node not found: {resolved}")
    return node.id


def _to_view_entry(entry: ActiveManifestEntry | None) -> ActiveViewEntry:
    if entry is None:
        return ActiveViewEntry(id=None, path=None)
    return ActiveViewEntry(id=entry.id, path=entry.path)


def _to_active_selection(manifest: ActiveManifest | None) -> ActiveSelection | None:
    if manifest is None:
        return None
    return ActiveSelection(
        initiative_id=manifest.initiative.id if manifest.initiative is not None else None,
        epic_id=manifest.epic.id if manifest.epic is not None else None,
        issue_id=manifest.issue.id if manifest.issue is not None else None,
    )


def _append_unique(warnings: list[str], warning: str) -> None:
    if warning not in warnings:
        warnings.append(warning)


def build_context_pack_text(manifest: ActiveManifest, *, repo_root: Path | None = None) -> str:
    del repo_root
    has_init = manifest.initiative is not None
    has_epic = manifest.epic is not None
    has_issue = manifest.issue is not None
    init_id = manifest.initiative.id if has_init else "(none)"
    epic_id = manifest.epic.id if has_epic else "(none)"
    issue_id = manifest.issue.id if has_issue else "(none)"

    lines: list[str] = []
    lines.append("# Context Pack (generated)")
    lines.append("")
    lines.append("## Active")
    lines.append(f"- initiative: {init_id}")
    lines.append(f"- epic: {epic_id}")
    lines.append(f"- issue: {issue_id}")
    lines.append("")
    lines.append("## Generated state")
    lines.append("- entry: `spec-dock/.agent/active.json`")
    lines.append("- default working set: `spec-dock/.agent/index.json`")
    lines.append("- default dependency view: `spec-dock/.agent/deps-issues.json`")
    lines.append("- escalation only: `spec-dock/.agent/index-all.json`")
    lines.append("- human-oriented tree: `spec-dock/.agent/tree.json`")
    lines.append("")
    lines.append("## Read order")
    lines.append("- Start with `spec-dock/.agent/active.json`.")
    lines.append("- For normal work, read `spec-dock/.agent/index.json` and `spec-dock/.agent/deps-issues.json`.")
    lines.append("- Read `spec-dock/.agent/index-all.json` only when full-history context is needed.")
    lines.append(
        "- `spec-dock/active/context-pack.md` is human guidance that mirrors this contract; it is not the sole source of truth."
    )
    lines.append("- Then follow the active documents:")
    if has_init:
        lines.append("- `spec-dock/active/initiative/requirement.md`")
        lines.append("- `spec-dock/active/initiative/design.md`")
        lines.append("- `spec-dock/active/initiative/plan.md`")
    else:
        lines.append("- `spec-dock/active/initiative/README.md`")
    if has_epic:
        lines.append("- `spec-dock/active/epic/requirement.md`")
        lines.append("- `spec-dock/active/epic/design.md`")
        lines.append("- `spec-dock/active/epic/plan.md`")
    else:
        lines.append("- `spec-dock/active/epic/README.md`")
    if has_issue:
        lines.append("- `spec-dock/active/issue/requirement.md`")
        lines.append("- `spec-dock/active/issue/design.md`")
        lines.append("- `spec-dock/active/issue/plan.md`")
        lines.append("- `spec-dock/active/issue/report.md`")
    else:
        lines.append("- `spec-dock/active/issue/README.md`")
    lines.append("")
    lines.append("## Commands")
    lines.append("- state (github default): `./spec-dock/scripts/spec-dock sync`")
    lines.append("- state (cache/local opt-out): `./spec-dock/scripts/spec-dock sync --no-github`")
    lines.append("- validate: `./spec-dock/scripts/spec-dock validate`")
    lines.append("")
    return "\n".join(lines) + "\n"


def _build_context_pack_text(manifest: ActiveManifest, *, repo_root: Path | None = None) -> str:
    return build_context_pack_text(manifest, repo_root=repo_root)


def show_active(req: ShowActiveRequest, ports: Ports) -> ActiveViewResult:
    del req
    if ports.active_state_store is None:
        raise RuntimeError("active_state_store is required")

    specdock_dir = _resolve_specdock_dir(ports)
    load_result = ports.active_state_store.load_active_manifest(specdock_dir)
    manifest = load_result.manifest
    return ActiveViewResult(
        initiative=_to_view_entry(manifest.initiative if manifest is not None else None),
        epic=_to_view_entry(manifest.epic if manifest is not None else None),
        issue=_to_view_entry(manifest.issue if manifest is not None else None),
        source=load_result.source,
        warnings=list(load_result.warnings),
    )


def build_active_manifest(selection: ActiveSelection, graph: SpecGraph, *, repo_root: Path) -> ActiveManifest:
    def _entry(node_id: str | None) -> ActiveManifestEntry | None:
        if node_id is None:
            return None
        node = graph.nodes_by_id.get(node_id)
        if node is None:
            raise RuntimeError(f"Node not found while building active manifest: {node_id}")
        return ActiveManifestEntry(
            id=node.id,
            path=_to_repo_relative_specdock_path(node.path, repo_root=repo_root),
        )

    return ActiveManifest(
        initiative=_entry(selection.initiative_id),
        epic=_entry(selection.epic_id),
        issue=_entry(selection.issue_id),
    )


def commit_active_state(
    *,
    persisted_manifest: ActiveManifest,
    patch_manifest: ActiveManifest | None,
    ports: Ports,
    context_pack_text: str,
) -> ActiveManifest:
    if ports.active_state_store is None:
        raise RuntimeError("active_state_store is required")
    specdock_dir = _resolve_specdock_dir(ports)
    snapshot = ports.active_state_store.snapshot_current_state(specdock_dir)
    try:
        written = ports.active_state_store.write_active_manifest(specdock_dir, persisted_manifest)
        ports.active_state_store.apply_active_pointers(specdock_dir, written, context_pack_text)
        ports.active_state_store.patch_agent_state_active_fields(specdock_dir, patch_manifest)
        return written
    except Exception as original_error:
        try:
            ports.active_state_store.restore_previous_state(specdock_dir, snapshot)
        except Exception as rollback_error:
            raise RuntimeError(f"{original_error}\nrollback_failed: {rollback_error}") from original_error
        raise


def checkout_active_target(
    *,
    graph: SpecGraph,
    target_id: str,
    ports: Ports,
    warnings: list[str],
) -> BranchDecision:
    if ports.git_gateway is None:
        raise RuntimeError("git_gateway is required when checkout is enabled")
    repo_root = _resolve_repo_root(ports)
    node = graph.nodes_by_id.get(target_id)
    if node is None:
        raise RuntimeError(f"Node not found: {target_id}")
    is_valid = ports.git_gateway.check_ref_format_branch(repo_root, f"{node.id}-{node.slug}")
    decision = resolve_branch_decision(node, candidate_is_valid=is_valid)
    for warning in decision.warnings:
        _append_unique(warnings, warning)

    ports.git_gateway.require_clean_working_tree(repo_root)
    current_branch = ports.git_gateway.current_branch_or_none(repo_root)
    if current_branch != decision.desired:
        if ports.git_gateway.local_branch_exists(repo_root, decision.desired):
            _append_unique(warnings, "branch already exists; reusing existing branch; content is not verified")
            ports.git_gateway.checkout_branch(repo_root, decision.desired)
        else:
            ports.git_gateway.create_and_checkout_branch(repo_root, decision.desired)
    return decision


def set_active(req: SetActiveRequest, ports: Ports) -> ActiveSetResult:
    if ports.active_state_store is None:
        raise RuntimeError("active_state_store is required")

    records = ports.node_reader.load_node_records()
    if not records:
        raise RuntimeError("No nodes found. Create at least one initiative/epic/issue.")
    graph = build_graph([_to_spec_node_seed(record) for record in records])
    specdock_dir = _resolve_specdock_dir(ports)
    warnings: list[str] = []

    current = ports.active_state_store.load_active_manifest(specdock_dir)
    for warning in current.warnings:
        _append_unique(warnings, warning)

    target_id = resolve_target_node_id(graph, req.target)

    selection = select_active_chain(graph, NodeId(target_id))
    branch = (
        checkout_active_target(
            graph=graph,
            target_id=target_id,
            ports=ports,
            warnings=warnings,
        )
        if req.checkout
        else None
    )

    manifest = build_active_manifest(selection, graph, repo_root=_resolve_repo_root(ports))
    context_pack_text = _build_context_pack_text(manifest, repo_root=_resolve_repo_root(ports))
    commit_active_state(
        persisted_manifest=manifest,
        patch_manifest=manifest,
        ports=ports,
        context_pack_text=context_pack_text,
    )
    return ActiveSetResult(
        selection=selection,
        branch=branch,
        manifest_written=True,
        pointer_updated=True,
        warnings=warnings,
    )


def clear_active(req: ClearActiveRequest, ports: Ports) -> ActiveClearResult:
    del req
    if ports.active_state_store is None:
        raise RuntimeError("active_state_store is required")
    records = ports.node_reader.load_node_records()
    graph = build_graph([_to_spec_node_seed(record) for record in records])
    specdock_dir = _resolve_specdock_dir(ports)
    load_result = ports.active_state_store.load_active_manifest(specdock_dir)
    previous = _to_active_selection(load_result.manifest)
    empty_selection = ActiveSelection(initiative_id=None, epic_id=None, issue_id=None)
    manifest = build_active_manifest(empty_selection, graph, repo_root=_resolve_repo_root(ports))
    context_pack_text = _build_context_pack_text(manifest, repo_root=_resolve_repo_root(ports))
    commit_active_state(
        persisted_manifest=manifest,
        patch_manifest=None,
        ports=ports,
        context_pack_text=context_pack_text,
    )
    return ActiveClearResult(cleared=True, previous=previous, warnings=list(load_result.warnings))
