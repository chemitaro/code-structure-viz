from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from code_structure_viz.core.config import ComparisonConfig
from code_structure_viz.core.diagnostics import DiagnosticCode, diagnostic
from code_structure_viz.source.git_repository import Commit, GitReadError, GitRepositoryReader


class EndpointKind(StrEnum):
    COMMIT = "commit"
    WORKING_TREE = "frozen-working-tree"


@dataclass(frozen=True, slots=True)
class ResolvedEndpoint:
    requested: str
    kind: EndpointKind
    commit: Commit | None

    @property
    def object_id(self) -> str | None:
        return self.commit.object_id if self.commit is not None else None


@dataclass(frozen=True, slots=True)
class ComparisonEndpoints:
    before: ResolvedEndpoint
    after: ResolvedEndpoint
    start_head_anchor: str | None
    selected_base_candidate: str | None
    merge_base: str | None
    resolution_method: str
    requested_from: str | None = None
    requested_to: str | None = None

    def provenance_value(self) -> dict[str, object]:
        return {
            "requested": {
                "from": self.requested_from,
                "to": self.requested_to,
            },
            "resolved": {
                "before": self.before.object_id,
                "after": self.after.object_id,
            },
            "before_kind": self.before.kind.value,
            "after_kind": self.after.kind.value,
            "start_head_anchor": self.start_head_anchor,
            "selected_base_candidate": self.selected_base_candidate,
            "merge_base": self.merge_base,
            "resolution_method": self.resolution_method,
        }


class EndpointResolutionError(GitReadError):
    """A requested endpoint or implicit comparison base cannot be resolved."""


def validate_endpoint_text(value: str) -> str:
    """Return a safe endpoint token without interpreting it as a shell command."""
    if (
        not value
        or value in {"working-tree", "head"}
        or value.startswith("-")
        or any(character in value for character in "\x00\r\n\t")
    ):
        raise EndpointResolutionError(diagnostic(DiagnosticCode.DIFF_ENDPOINT))
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeEncodeError as error:
        raise EndpointResolutionError(diagnostic(DiagnosticCode.DIFF_ENDPOINT)) from error
    return value


class ComparisonEndpointResolver:
    """Resolve immutable comparison endpoints using local Git objects only."""

    def __init__(
        self,
        reader: GitRepositoryReader,
        *,
        comparison: ComparisonConfig | None = None,
    ) -> None:
        self.reader = reader
        self.comparison = comparison or ComparisonConfig()

    def resolve(
        self,
        *,
        from_ref: str | None,
        to_ref: str | None,
        pr_target: str | None = None,
        start_head: Commit | None = None,
    ) -> ComparisonEndpoints:
        if from_ref == "working-tree":
            raise EndpointResolutionError(diagnostic(DiagnosticCode.DIFF_ENDPOINT))
        if to_ref == "working-tree" or to_ref is None:
            anchor = start_head or self._head_commit()
            after = ResolvedEndpoint(
                requested=to_ref or "working-tree",
                kind=EndpointKind.WORKING_TREE,
                commit=None,
            )
            if from_ref is not None:
                before = self._commit_endpoint(from_ref, start_head=anchor)
                return ComparisonEndpoints(
                    before,
                    after,
                    anchor.object_id,
                    None,
                    None,
                    "explicit-from-to-working-tree",
                    from_ref,
                    to_ref,
                )
            candidate, merge_base = self._resolve_implicit_base(
                anchor,
                pr_target=pr_target,
            )
            before = ResolvedEndpoint(
                requested=merge_base,
                kind=EndpointKind.COMMIT,
                commit=Commit(merge_base),
            )
            return ComparisonEndpoints(
                before,
                after,
                anchor.object_id,
                candidate,
                merge_base,
                "implicit-base-from-start-head-anchor",
                from_ref,
                to_ref,
            )

        current_head = start_head
        after = self._commit_endpoint(to_ref or "head", start_head=current_head)
        if from_ref is not None:
            before = self._commit_endpoint(from_ref, start_head=current_head)
            return ComparisonEndpoints(
                before,
                after,
                current_head.object_id if current_head is not None else None,
                None,
                None,
                "explicit-from-to",
                from_ref,
                to_ref,
            )
        endpoint_anchor = after.commit or current_head
        if endpoint_anchor is None:
            raise EndpointResolutionError(diagnostic(DiagnosticCode.DIFF_ENDPOINT))
        candidate, merge_base = self._resolve_implicit_base(
            endpoint_anchor,
            pr_target=pr_target,
        )
        return ComparisonEndpoints(
            ResolvedEndpoint(merge_base, EndpointKind.COMMIT, Commit(merge_base)),
            after,
            current_head.object_id if current_head is not None else None,
            candidate,
            merge_base,
            "implicit-base-from-endpoint-anchor",
            from_ref,
            to_ref,
        )

    def _head_commit(self) -> Commit:
        state = self.reader.resolve_head_state()
        if not isinstance(state, Commit):
            raise EndpointResolutionError(diagnostic(DiagnosticCode.DIFF_ENDPOINT))
        return state

    def _commit_endpoint(
        self, requested: str, *, start_head: Commit | None = None
    ) -> ResolvedEndpoint:
        if requested == "working-tree":
            raise EndpointResolutionError(diagnostic(DiagnosticCode.DIFF_ENDPOINT))
        if requested == "head":
            commit = start_head or self._head_commit()
            return ResolvedEndpoint("head", EndpointKind.COMMIT, commit)
        safe = validate_endpoint_text(requested)
        try:
            commit = self.reader.resolve_commit(safe)
        except GitReadError as error:
            raise EndpointResolutionError(diagnostic(DiagnosticCode.DIFF_ENDPOINT)) from error
        return ResolvedEndpoint(safe, EndpointKind.COMMIT, commit)

    def _resolve_implicit_base(
        self,
        anchor: Commit,
        *,
        pr_target: str | None,
    ) -> tuple[str, str]:
        explicit_candidates: list[str] = []
        if pr_target is not None:
            explicit_candidates.append(validate_endpoint_text(pr_target))
        target_ref = self.comparison.target_ref
        if target_ref is not None and target_ref not in explicit_candidates:
            explicit_candidates.append(validate_endpoint_text(target_ref))
        upstream_ref = self.comparison.upstream_ref
        if upstream_ref is not None:
            namespace = validate_endpoint_text(upstream_ref)
            try:
                upstream_candidates = self.reader.enumerate_ref_names(namespace)
            except GitReadError as error:
                raise EndpointResolutionError(diagnostic(DiagnosticCode.DIFF_ENDPOINT)) from error
            if not upstream_candidates:
                raise EndpointResolutionError(diagnostic(DiagnosticCode.DIFF_ENDPOINT))
            explicit_candidates.extend(
                candidate
                for candidate in upstream_candidates
                if candidate not in explicit_candidates
            )

        candidates = [*explicit_candidates, "refs/remotes/origin/HEAD"]
        candidates.extend(f"refs/heads/{name}" for name in ("main", "develop", "master"))
        for position, candidate in enumerate(candidates):
            try:
                resolved = self.reader.resolve_commit(candidate)
            except GitReadError as error:
                if position < len(explicit_candidates):
                    raise EndpointResolutionError(
                        diagnostic(DiagnosticCode.DIFF_ENDPOINT)
                    ) from error
                continue
            merge_base = self.reader.resolve_merge_base(resolved.object_id, anchor.object_id)
            if merge_base is not None:
                return candidate, merge_base
        raise EndpointResolutionError(diagnostic(DiagnosticCode.DIFF_ENDPOINT))
