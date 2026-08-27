from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

from code_structure_viz.adapters.python.model import (
    PythonClassEntity,
    PythonMember,
    PythonRelation,
    PythonSnapshot,
    TargetResolution,
    entity_sort_key,
    member_sort_key,
    relation_sort_key,
)
from code_structure_viz.core.diagnostics import Diagnostic
from code_structure_viz.semantic.canonical_json import encode_canonical_json


class DeltaStatus(StrEnum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    MOVED = "moved"
    UNKNOWN = "unknown"


class SideKind(StrEnum):
    REAL = "real"
    CANONICAL_EMPTY = "canonical-empty-side"
    ANALYSIS_FAILED = "analysis-failed"


@dataclass(frozen=True, slots=True)
class DiffSide:
    kind: SideKind
    schema: str
    digest: str
    head_commit: str | None
    file_count: int
    snapshot: PythonSnapshot | None

    def to_json_value(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "schema": self.schema,
            "digest": self.digest,
            "head_commit": self.head_commit,
            "file_count": self.file_count,
        }


@dataclass(frozen=True, slots=True)
class SemanticDelta:
    status: DeltaStatus
    identity: str
    before: object | None
    after: object | None
    matching_evidence: dict[str, object] | None = None

    def to_json_value(self) -> dict[str, object]:
        value: dict[str, object] = {
            "status": self.status.value,
            "id": self.identity,
            "before": self.before,
            "after": self.after,
        }
        if self.matching_evidence is not None:
            value["matching_evidence"] = self.matching_evidence
        return value


@dataclass(frozen=True, slots=True)
class ImpactContext:
    upstream: tuple[str, ...]
    downstream: tuple[str, ...]

    def to_json_value(self) -> dict[str, object]:
        return {"upstream": list(self.upstream), "downstream": list(self.downstream)}


@dataclass(frozen=True, slots=True)
class SemanticDiffResult:
    status: str
    before: DiffSide
    after: DiffSide
    entities: tuple[SemanticDelta, ...]
    members: tuple[SemanticDelta, ...]
    relations: tuple[SemanticDelta, ...]
    seeds: tuple[str, ...]
    impact: ImpactContext
    matching: tuple[dict[str, object], ...]
    diagnostics: tuple[Diagnostic, ...] = ()

    @property
    def entity_count(self) -> int:
        changed_entities = {item.identity for item in self.entities}
        return len(
            {
                *changed_entities,
                *self.seeds,
                *self.impact.upstream,
                *self.impact.downstream,
            }
        )


class CanonicalEmptySide:
    """Stable internal side used only when the Python domain is absent."""

    schema = "code-structure-viz.empty-side/v1"
    domain = "python"

    @classmethod
    def value(cls) -> dict[str, object]:
        return {
            "schema": cls.schema,
            "domain": cls.domain,
            "document_kind": "internal-diff-side",
            "entities": [],
            "members": [],
            "relations": [],
        }

    @classmethod
    def bytes(cls) -> bytes:
        return encode_canonical_json(cls.value())

    @classmethod
    def digest(cls) -> str:
        return hashlib.sha256(cls.bytes()).hexdigest()

    @classmethod
    def side(cls) -> DiffSide:
        return DiffSide(SideKind.CANONICAL_EMPTY, cls.schema, cls.digest(), None, 0, None)


class DomainPresenceResolver:
    @staticmethod
    def side(
        snapshot: PythonSnapshot | None,
        *,
        digest: str | None = None,
        head_commit: str | None = None,
        file_count: int = 0,
        analysis_failed: bool = False,
    ) -> DiffSide:
        if analysis_failed:
            return DiffSide(
                SideKind.ANALYSIS_FAILED,
                "code-structure-viz.semantic/v1",
                digest or "",
                head_commit,
                file_count,
                snapshot,
            )
        if snapshot is None:
            return CanonicalEmptySide.side()
        return DiffSide(
            SideKind.REAL,
            "code-structure-viz.semantic/v1",
            digest or _snapshot_digest(snapshot),
            head_commit,
            file_count,
            snapshot,
        )


class SemanticDiffer:
    """Compare two Python semantic snapshots without using source text or patch lines."""

    def compare(
        self,
        before: PythonSnapshot | None,
        after: PythonSnapshot | None,
        *,
        before_side: DiffSide | None = None,
        after_side: DiffSide | None = None,
        upstream_depth: int = 1,
        downstream_depth: int = 1,
    ) -> SemanticDiffResult:
        resolved_before = before_side or DomainPresenceResolver.side(before)
        resolved_after = after_side or DomainPresenceResolver.side(after)
        if SideKind.ANALYSIS_FAILED in {resolved_before.kind, resolved_after.kind}:
            return SemanticDiffResult(
                "incomplete",
                resolved_before,
                resolved_after,
                (),
                (),
                (),
                (),
                ImpactContext((), ()),
                (),
            )
        if (
            resolved_before.kind is SideKind.CANONICAL_EMPTY
            and resolved_after.kind is SideKind.CANONICAL_EMPTY
        ):
            return SemanticDiffResult(
                "not_applicable",
                resolved_before,
                resolved_after,
                (),
                (),
                (),
                (),
                ImpactContext((), ()),
                (),
            )

        before_snapshot = before if before is not None else _empty_snapshot()
        after_snapshot = after if after is not None else _empty_snapshot()
        entities, entity_matches = _entity_deltas(before_snapshot, after_snapshot)
        members = _member_deltas(before_snapshot, after_snapshot, entity_matches)
        relations = _relation_deltas(before_snapshot, after_snapshot, entity_matches)
        seeds = _seeds(members, relations)
        impact = ImpactExplorer().explore(
            before_snapshot,
            after_snapshot,
            seeds,
            upstream_depth=upstream_depth,
            downstream_depth=downstream_depth,
        )
        return SemanticDiffResult(
            "complete",
            resolved_before,
            resolved_after,
            entities,
            members,
            relations,
            tuple(sorted(seeds, key=lambda item: item.encode("utf-8"))),
            impact,
            tuple(entity_matches),
        )


class ImpactExplorer:
    """Traverse the union of before/after internal relations from changed seeds."""

    def explore(
        self,
        before: PythonSnapshot,
        after: PythonSnapshot,
        seeds: Iterable[str],
        *,
        upstream_depth: int = 1,
        downstream_depth: int = 1,
    ) -> ImpactContext:
        forward: dict[str, set[str]] = {}
        reverse: dict[str, set[str]] = {}
        for relation in (*before.relations, *after.relations):
            if relation.target.resolution is not TargetResolution.INTERNAL:
                continue
            target = relation.target.id
            if target is None:
                continue
            forward.setdefault(relation.source_id, set()).add(target)
            reverse.setdefault(target, set()).add(relation.source_id)
        seed_set = set(seeds)
        return ImpactContext(
            _walk(reverse, seed_set, upstream_depth),
            _walk(forward, seed_set, downstream_depth),
        )


def _walk(adjacency: dict[str, set[str]], seeds: set[str], depth: int) -> tuple[str, ...]:
    visited: set[str] = set()
    frontier = set(seeds)
    for _ in range(max(0, depth)):
        next_nodes = {
            target for node in frontier for target in adjacency.get(node, set())
        } - visited - seeds
        if not next_nodes:
            break
        visited.update(next_nodes)
        frontier = next_nodes
    return tuple(sorted(visited, key=lambda item: item.encode("utf-8")))


def _entity_deltas(
    before: PythonSnapshot,
    after: PythonSnapshot,
) -> tuple[tuple[SemanticDelta, ...], list[dict[str, object]]]:
    from code_structure_viz.adapters.python.matcher import PythonMoveMatcher

    before_map = {item.id: item for item in before.entities}
    after_map = {item.id: item for item in after.entities}
    matches = PythonMoveMatcher().match(
        before.entities,
        after.entities,
        before.members,
        after.members,
    )
    matched_before = {item["before_id"] for item in matches}
    matched_after = {item["after_id"] for item in matches}
    deltas: list[SemanticDelta] = []
    for identity in sorted(set(before_map) | set(after_map), key=lambda item: item.encode("utf-8")):
        left = before_map.get(identity)
        right = after_map.get(identity)
        if left is not None and right is not None:
            if _entity_key(left) != _entity_key(right):
                deltas.append(
                    SemanticDelta(
                        DeltaStatus.MODIFIED,
                        identity,
                        _entity_value(left),
                        _entity_value(right),
                    )
                )
            continue
        if identity in matched_before or identity in matched_after:
            continue
        if left is not None:
            deltas.append(SemanticDelta(DeltaStatus.REMOVED, identity, _entity_value(left), None))
        elif right is not None:
            deltas.append(SemanticDelta(DeltaStatus.ADDED, identity, None, _entity_value(right)))
    for match in matches:
        deltas.append(
            SemanticDelta(
                DeltaStatus.MOVED,
                str(match["after_id"]),
                _entity_value(before_map[str(match["before_id"])]),
                _entity_value(after_map[str(match["after_id"])]),
                match,
            )
        )
    deltas.sort(
        key=lambda item: (item.identity.encode("utf-8"), item.status.value.encode("utf-8"))
    )
    return tuple(deltas), matches


def _member_deltas(
    before: PythonSnapshot,
    after: PythonSnapshot,
    entity_matches: list[dict[str, object]],
) -> tuple[SemanticDelta, ...]:
    owner_map = {str(item["before_id"]): str(item["after_id"]) for item in entity_matches}
    before_map = {item.id: item for item in before.members}
    after_map = {item.id: item for item in after.members}
    deltas: list[SemanticDelta] = []
    consumed_before: set[str] = set()
    consumed_after: set[str] = set()
    for before_id, after_owner in owner_map.items():
        left_items = [item for item in before.members if item.owner_id == before_id]
        right_items = [item for item in after.members if item.owner_id == after_owner]
        for left in left_items:
            candidates = [
                right
                for right in right_items
                if (
                    right.id not in consumed_after
                    and _member_identity_key(left) == _member_identity_key(right)
                )
            ]
            if len(candidates) == 1:
                right = candidates[0]
                consumed_before.add(left.id)
                consumed_after.add(right.id)
                if _member_key(left) != _member_key(right) or left.owner_id != right.owner_id:
                    deltas.append(
                        SemanticDelta(
                            (
                                DeltaStatus.MOVED
                                if left.owner_id != right.owner_id
                                else DeltaStatus.MODIFIED
                            ),
                            right.id,
                            _member_value(left),
                            _member_value(right),
                        )
                    )
    for identity in sorted(set(before_map) | set(after_map), key=lambda item: item.encode("utf-8")):
        if identity in consumed_before or identity in consumed_after:
            continue
        before_member: PythonMember | None = before_map.get(identity)
        after_member: PythonMember | None = after_map.get(identity)
        if before_member is not None and after_member is not None:
            if _member_key(before_member) != _member_key(after_member):
                deltas.append(
                    SemanticDelta(
                        DeltaStatus.MODIFIED,
                        identity,
                        _member_value(before_member),
                        _member_value(after_member),
                    )
                )
        elif before_member is not None:
            deltas.append(
                SemanticDelta(
                    DeltaStatus.REMOVED,
                    identity,
                    _member_value(before_member),
                    None,
                )
            )
        elif after_member is not None:
            deltas.append(
                SemanticDelta(
                    DeltaStatus.ADDED,
                    identity,
                    None,
                    _member_value(after_member),
                )
            )
    return tuple(
        sorted(
            deltas,
            key=lambda item: (item.identity.encode("utf-8"), item.status.value.encode("utf-8")),
        )
    )


def _relation_deltas(
    before: PythonSnapshot,
    after: PythonSnapshot,
    entity_matches: list[dict[str, object]],
) -> tuple[SemanticDelta, ...]:
    before_map = {item.id: item for item in before.relations}
    after_map = {item.id: item for item in after.relations}
    deltas: list[SemanticDelta] = []
    for identity in sorted(set(before_map) | set(after_map), key=lambda item: item.encode("utf-8")):
        left = before_map.get(identity)
        right = after_map.get(identity)
        if left is not None and right is not None:
            if _relation_key(left) != _relation_key(right):
                deltas.append(
                    SemanticDelta(
                        DeltaStatus.MODIFIED,
                        identity,
                        _relation_value(left),
                        _relation_value(right),
                    )
                )
        elif left is not None:
            deltas.append(SemanticDelta(DeltaStatus.REMOVED, identity, _relation_value(left), None))
        elif right is not None:
            deltas.append(SemanticDelta(DeltaStatus.ADDED, identity, None, _relation_value(right)))
    return tuple(
        sorted(
            deltas,
            key=lambda item: (item.identity.encode("utf-8"), item.status.value.encode("utf-8")),
        )
    )


def _seeds(
    members: tuple[SemanticDelta, ...],
    relations: tuple[SemanticDelta, ...],
) -> set[str]:
    values: set[str] = set()
    for delta in members:
        for side in (delta.before, delta.after):
            if isinstance(side, dict) and isinstance(side.get("owner_id"), str):
                values.add(side["owner_id"])
    for delta in relations:
        for side in (delta.before, delta.after):
            if isinstance(side, dict) and isinstance(side.get("source_id"), str):
                values.add(side["source_id"])
    return values


def _snapshot_digest(snapshot: PythonSnapshot) -> str:
    value = {
        "entities": [
            _entity_value(item) for item in sorted(snapshot.entities, key=entity_sort_key)
        ],
        "members": [
            _member_value(item) for item in sorted(snapshot.members, key=member_sort_key)
        ],
        "relations": [
            _relation_value(item) for item in sorted(snapshot.relations, key=relation_sort_key)
        ],
    }
    return hashlib.sha256(encode_canonical_json(value)).hexdigest()


def _empty_snapshot() -> PythonSnapshot:
    from code_structure_viz.adapters.python.model import PythonCoverage

    return PythonSnapshot((), (), (), PythonCoverage(0, 0, (), (), 0, ()), ())


def _entity_key(value: PythonClassEntity) -> tuple[object, ...]:
    return (
        value.module,
        value.qualified_name,
        value.name,
        tuple((item.name, item.called) for item in value.decorators),
    )


def _member_identity_key(value: PythonMember) -> tuple[object, ...]:
    return (
        value.kind.value,
        value.name,
        value.scope.value if value.scope else None,
        value.property_role.value if value.property_role else None,
        value.method_kind.value if value.method_kind else None,
        value.declaration_ordinal,
    )


def _member_key(value: PythonMember) -> object:
    return _member_value(value) | {"range": None}


def _relation_key(value: PythonRelation) -> object:
    return _relation_value(value) | {"range": None}


def _entity_value(value: PythonClassEntity) -> dict[str, object]:
    return {
        "id": value.id,
        "kind": value.kind,
        "module": value.module,
        "qualified_name": value.qualified_name,
        "name": value.name,
        "path": value.path.as_posix(),
        "range": {"start_line": value.range.start_line, "end_line": value.range.end_line},
        "decorators": [{"name": item.name, "called": item.called} for item in value.decorators],
    }


def _member_value(value: PythonMember) -> dict[str, object]:
    from code_structure_viz.adapters.python.semantic_json import _member_value as render

    return render(value)


def _relation_value(value: PythonRelation) -> dict[str, object]:
    from code_structure_viz.adapters.python.semantic_json import _relation_value as render

    return render(value)


__all__ = [
    "CanonicalEmptySide",
    "DeltaStatus",
    "DiffSide",
    "DomainPresenceResolver",
    "ImpactContext",
    "ImpactExplorer",
    "SemanticDelta",
    "SemanticDiffResult",
    "SemanticDiffer",
    "SideKind",
]
