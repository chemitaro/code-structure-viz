from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from code_structure_viz.core.config import ComparisonConfig
from code_structure_viz.core.diagnostics import DiagnosticCode, diagnostic
from code_structure_viz.source.git_repository import Commit, GitReadError, GitRepositoryReader


class EndpointKind(StrEnum):
    COMMIT = "commit"
    WORKING_TREE = "frozen-working-tree"


class CandidateOrigin(StrEnum):
    PR_TARGET = "pr-target"
    CONFIG_TARGET = "config-target"
    CONFIG_UPSTREAM = "config-upstream"
    BUILTIN = "builtin"


class CandidateDisposition(StrEnum):
    UNRESOLVED = "unresolved"
    NO_MERGE_BASE = "no-merge-base"
    SELECTED = "selected"
    NOT_EVALUATED = "not-evaluated"


@dataclass(frozen=True, slots=True)
class BaseCandidateObservation:
    ordinal: int
    origin: CandidateOrigin
    reference: str
    resolved_object: str | None
    merge_base: str | None
    disposition: CandidateDisposition

    def to_json_value(self) -> dict[str, object]:
        return {
            "ordinal": self.ordinal,
            "origin": self.origin.value,
            "reference": self.reference,
            "resolved_object": self.resolved_object,
            "merge_base": self.merge_base,
            "disposition": self.disposition.value,
        }


@dataclass(frozen=True, slots=True)
class ImplicitBaseResolution:
    selected_reference: str
    selected_merge_base: str
    observations: tuple[BaseCandidateObservation, ...]


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
    candidate_observations: tuple[BaseCandidateObservation, ...] = ()

    def __post_init__(self) -> None:
        if not self.candidate_observations:
            if self.selected_base_candidate is not None or self.merge_base is not None:
                raise ValueError("explicit endpoint provenance cannot select an implicit base")
            return
        expected_ordinals = tuple(range(len(self.candidate_observations)))
        if tuple(item.ordinal for item in self.candidate_observations) != expected_ordinals:
            raise ValueError("candidate observation ordinals are not deterministic")
        selected = tuple(
            item
            for item in self.candidate_observations
            if item.disposition is CandidateDisposition.SELECTED
        )
        if len(selected) != 1:
            raise ValueError("implicit endpoint requires exactly one selected candidate")
        if (
            selected[0].reference != self.selected_base_candidate
            or selected[0].merge_base != self.merge_base
        ):
            raise ValueError("selected candidate does not match endpoint provenance")

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
            "candidate_observations": [
                item.to_json_value() for item in self.candidate_observations
            ],
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
            resolution = self._resolve_implicit_base(
                anchor,
                pr_target=pr_target,
            )
            before = ResolvedEndpoint(
                requested=resolution.selected_merge_base,
                kind=EndpointKind.COMMIT,
                commit=Commit(resolution.selected_merge_base),
            )
            return ComparisonEndpoints(
                before,
                after,
                anchor.object_id,
                resolution.selected_reference,
                resolution.selected_merge_base,
                "implicit-base-from-start-head-anchor",
                from_ref,
                to_ref,
                resolution.observations,
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
        resolution = self._resolve_implicit_base(
            endpoint_anchor,
            pr_target=pr_target,
        )
        return ComparisonEndpoints(
            ResolvedEndpoint(
                resolution.selected_merge_base,
                EndpointKind.COMMIT,
                Commit(resolution.selected_merge_base),
            ),
            after,
            current_head.object_id if current_head is not None else None,
            resolution.selected_reference,
            resolution.selected_merge_base,
            "implicit-base-from-endpoint-anchor",
            from_ref,
            to_ref,
            resolution.observations,
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
    ) -> ImplicitBaseResolution:
        explicit_candidates: list[tuple[str, CandidateOrigin]] = []
        if pr_target is not None:
            explicit_candidates.append(
                (validate_endpoint_text(pr_target), CandidateOrigin.PR_TARGET)
            )
        target_ref = self.comparison.target_ref
        if target_ref is not None and target_ref not in {item[0] for item in explicit_candidates}:
            explicit_candidates.append(
                (validate_endpoint_text(target_ref), CandidateOrigin.CONFIG_TARGET)
            )
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
                (candidate, CandidateOrigin.CONFIG_UPSTREAM)
                for candidate in upstream_candidates
                if candidate not in {item[0] for item in explicit_candidates}
            )

        candidate_specs = [
            *explicit_candidates,
            ("refs/remotes/origin/HEAD", CandidateOrigin.BUILTIN),
            *(
                (f"refs/heads/{name}", CandidateOrigin.BUILTIN)
                for name in ("main", "develop", "master")
            ),
        ]
        deduplicated: list[tuple[str, CandidateOrigin]] = []
        seen: set[str] = set()
        for candidate, origin in candidate_specs:
            if candidate not in seen:
                deduplicated.append((candidate, origin))
                seen.add(candidate)
        observations: list[BaseCandidateObservation] = []
        for position, (candidate, origin) in enumerate(deduplicated):
            try:
                resolved = self.reader.resolve_commit(candidate)
            except GitReadError as error:
                observations.append(
                    BaseCandidateObservation(
                        position,
                        origin,
                        candidate,
                        None,
                        None,
                        CandidateDisposition.UNRESOLVED,
                    )
                )
                if origin is not CandidateOrigin.BUILTIN:
                    raise EndpointResolutionError(
                        diagnostic(DiagnosticCode.DIFF_ENDPOINT)
                    ) from error
                continue
            merge_base = self.reader.resolve_merge_base(resolved.object_id, anchor.object_id)
            if merge_base is not None:
                observations.append(
                    BaseCandidateObservation(
                        position,
                        origin,
                        candidate,
                        resolved.object_id,
                        merge_base,
                        CandidateDisposition.SELECTED,
                    )
                )
                observations.extend(
                    BaseCandidateObservation(
                        next_position,
                        next_origin,
                        next_candidate,
                        None,
                        None,
                        CandidateDisposition.NOT_EVALUATED,
                    )
                    for next_position, (next_candidate, next_origin) in enumerate(
                        deduplicated[position + 1 :], start=position + 1
                    )
                )
                return ImplicitBaseResolution(candidate, merge_base, tuple(observations))
            observations.append(
                BaseCandidateObservation(
                    position,
                    origin,
                    candidate,
                    resolved.object_id,
                    None,
                    CandidateDisposition.NO_MERGE_BASE,
                )
            )
        raise EndpointResolutionError(diagnostic(DiagnosticCode.DIFF_ENDPOINT))
