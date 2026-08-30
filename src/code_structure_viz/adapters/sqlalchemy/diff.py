from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass

from code_structure_viz.adapters.sqlalchemy.model import (
    SqlAlchemyCoverage,
    SqlAlchemyRedactionSummary,
    SqlAlchemySnapshot,
    SqlAlchemyTargetResolution,
)
from code_structure_viz.adapters.sqlalchemy.semantic_json import (
    _relation_value,
    _row_value,
    _table_value,
)
from code_structure_viz.semantic.canonical_json import encode_sorted_canonical_json
from code_structure_viz.semantic.diff import DeltaStatus, ImpactContext, SemanticDelta, SideKind

_SEMANTIC_SCHEMA = "code-structure-viz.semantic/v1"
_EMPTY_SIDE_SCHEMA = "code-structure-viz.empty-side/v1"


@dataclass(frozen=True, slots=True)
class SqlAlchemyDiffSide:
    kind: SideKind
    schema: str
    digest: str
    head_commit: str | None
    file_count: int
    snapshot: SqlAlchemySnapshot | None

    def to_json_value(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "domain": "sqlalchemy",
            "schema": self.schema,
            "digest": self.digest,
            "head_commit": self.head_commit,
            "file_count": self.file_count,
        }


@dataclass(frozen=True, slots=True)
class SqlAlchemyDiffResult:
    status: str
    before: SqlAlchemyDiffSide
    after: SqlAlchemyDiffSide
    entities: tuple[SemanticDelta, ...]
    members: tuple[SemanticDelta, ...]
    relations: tuple[SemanticDelta, ...]
    seeds: tuple[str, ...]
    impact: ImpactContext
    matching: tuple[dict[str, object], ...] = ()

    @property
    def entity_count(self) -> int:
        return len(
            {
                *(item.identity for item in self.entities),
                *self.seeds,
                *self.impact.upstream,
                *self.impact.downstream,
            }
        )


class SqlAlchemyDiffer:
    """Compare SQLAlchemy snapshots by their existing stable IDs."""

    def compare(
        self,
        before: SqlAlchemySnapshot | None,
        after: SqlAlchemySnapshot | None,
        *,
        before_analysis_failed: bool = False,
        after_analysis_failed: bool = False,
        upstream_depth: int = 1,
        downstream_depth: int = 1,
        before_head_commit: str | None = None,
        after_head_commit: str | None = None,
        before_file_count: int = 0,
        after_file_count: int = 0,
        before_failure_digest: str = "",
        after_failure_digest: str = "",
    ) -> SqlAlchemyDiffResult:
        before_side = _side(
            before,
            analysis_failed=before_analysis_failed,
            head_commit=before_head_commit,
            file_count=before_file_count,
            failure_digest=before_failure_digest,
        )
        after_side = _side(
            after,
            analysis_failed=after_analysis_failed,
            head_commit=after_head_commit,
            file_count=after_file_count,
            failure_digest=after_failure_digest,
        )
        if SideKind.ANALYSIS_FAILED in {before_side.kind, after_side.kind}:
            return _empty_result("incomplete", before_side, after_side)
        if before is None and after is None:
            return _empty_result("not_applicable", before_side, after_side)

        before_snapshot = before or _empty_snapshot()
        after_snapshot = after or _empty_snapshot()
        entities = _entity_deltas(before_snapshot, after_snapshot)
        members = _member_deltas(before_snapshot, after_snapshot)
        relations = _relation_deltas(before_snapshot, after_snapshot)
        seeds = _seeds(entities, members, relations)
        impact = _impact(
            before_snapshot,
            after_snapshot,
            seeds,
            upstream_depth=upstream_depth,
            downstream_depth=downstream_depth,
        )
        return SqlAlchemyDiffResult(
            "complete",
            before_side,
            after_side,
            entities,
            members,
            relations,
            seeds,
            impact,
        )


def _empty_result(
    status: str,
    before: SqlAlchemyDiffSide,
    after: SqlAlchemyDiffSide,
) -> SqlAlchemyDiffResult:
    return SqlAlchemyDiffResult(status, before, after, (), (), (), (), ImpactContext((), ()))


def _side(
    snapshot: SqlAlchemySnapshot | None,
    *,
    analysis_failed: bool,
    head_commit: str | None,
    file_count: int,
    failure_digest: str,
) -> SqlAlchemyDiffSide:
    if analysis_failed:
        return SqlAlchemyDiffSide(
            SideKind.ANALYSIS_FAILED,
            _SEMANTIC_SCHEMA,
            failure_digest,
            head_commit,
            file_count,
            snapshot,
        )
    if snapshot is None:
        empty_value = {
            "schema": _EMPTY_SIDE_SCHEMA,
            "domain": "sqlalchemy",
            "document_kind": "internal-diff-side",
            "entities": [],
            "members": [],
            "relations": [],
        }
        digest = hashlib.sha256(encode_sorted_canonical_json(empty_value)).hexdigest()
        return SqlAlchemyDiffSide(
            SideKind.CANONICAL_EMPTY,
            _EMPTY_SIDE_SCHEMA,
            digest,
            None,
            0,
            None,
        )
    snapshot_value: dict[str, object] = {
        "entities": [_table_value(item) for item in snapshot.entities],
        "members": [_row_value(item) for item in snapshot.members],
        "relations": [_relation_value(item) for item in snapshot.relations],
    }
    digest = hashlib.sha256(encode_sorted_canonical_json(snapshot_value)).hexdigest()
    return SqlAlchemyDiffSide(
        SideKind.REAL,
        _SEMANTIC_SCHEMA,
        digest,
        head_commit,
        file_count,
        snapshot,
    )


def _empty_snapshot() -> SqlAlchemySnapshot:
    coverage = SqlAlchemyCoverage(
        0,
        0,
        (),
        (),
        (),
        0,
        0,
        0,
        0,
        (),
        SqlAlchemyRedactionSummary.create(0),
    )
    return SqlAlchemySnapshot((), (), (), coverage, (), False)


def _entity_deltas(
    before: SqlAlchemySnapshot,
    after: SqlAlchemySnapshot,
) -> tuple[SemanticDelta, ...]:
    left = {item.id: item for item in before.entities}
    right = {item.id: item for item in after.entities}
    return tuple(
        SemanticDelta(
            DeltaStatus.REMOVED if identity in left else DeltaStatus.ADDED,
            identity,
            _table_value(left[identity]) if identity in left else None,
            _table_value(right[identity]) if identity in right else None,
        )
        for identity in _ordered_symmetric_difference(left, right)
    )


def _member_deltas(
    before: SqlAlchemySnapshot,
    after: SqlAlchemySnapshot,
) -> tuple[SemanticDelta, ...]:
    left = {item.id: item for item in before.members}
    right = {item.id: item for item in after.members}
    deltas: list[SemanticDelta] = []
    for identity in _ordered_union(left, right):
        before_value = _row_value(left[identity]) if identity in left else None
        after_value = _row_value(right[identity]) if identity in right else None
        if identity not in left:
            deltas.append(SemanticDelta(DeltaStatus.ADDED, identity, None, after_value))
        elif identity not in right:
            deltas.append(SemanticDelta(DeltaStatus.REMOVED, identity, before_value, None))
        elif _without_source(before_value) != _without_source(after_value):
            deltas.append(SemanticDelta(DeltaStatus.MODIFIED, identity, before_value, after_value))
    return tuple(deltas)


def _relation_deltas(
    before: SqlAlchemySnapshot,
    after: SqlAlchemySnapshot,
) -> tuple[SemanticDelta, ...]:
    left = {item.id: item for item in before.relations}
    right = {item.id: item for item in after.relations}
    return tuple(
        SemanticDelta(
            DeltaStatus.REMOVED if identity in left else DeltaStatus.ADDED,
            identity,
            _relation_value(left[identity]) if identity in left else None,
            _relation_value(right[identity]) if identity in right else None,
        )
        for identity in _ordered_symmetric_difference(left, right)
    )


def _seeds(
    entities: tuple[SemanticDelta, ...],
    members: tuple[SemanticDelta, ...],
    relations: tuple[SemanticDelta, ...],
) -> tuple[str, ...]:
    values = {item.identity for item in entities}
    for delta in members:
        value = delta.after if delta.after is not None else delta.before
        if isinstance(value, dict) and isinstance(value.get("owner_id"), str):
            values.add(value["owner_id"])
    for delta in relations:
        value = delta.after if delta.after is not None else delta.before
        if not isinstance(value, dict):
            continue
        source_id = value.get("source_id")
        if isinstance(source_id, str):
            values.add(source_id)
        target = value.get("target")
        if (
            isinstance(target, dict)
            and target.get("resolution") == SqlAlchemyTargetResolution.INTERNAL.value
            and isinstance(target.get("id"), str)
        ):
            values.add(target["id"])
    return tuple(sorted(values, key=lambda value: value.encode("utf-8")))


def _impact(
    before: SqlAlchemySnapshot,
    after: SqlAlchemySnapshot,
    seeds: tuple[str, ...],
    *,
    upstream_depth: int,
    downstream_depth: int,
) -> ImpactContext:
    forward: dict[str, set[str]] = {}
    reverse: dict[str, set[str]] = {}
    for relation in (*before.relations, *after.relations):
        if relation.target.resolution is not SqlAlchemyTargetResolution.INTERNAL:
            continue
        assert relation.target.id is not None
        forward.setdefault(relation.source_id, set()).add(relation.target.id)
        reverse.setdefault(relation.target.id, set()).add(relation.source_id)
    seed_set = set(seeds)
    return ImpactContext(
        _walk(reverse, seed_set, upstream_depth),
        _walk(forward, seed_set, downstream_depth),
    )


def _walk(
    adjacency: dict[str, set[str]],
    seeds: set[str],
    depth: int,
) -> tuple[str, ...]:
    visited: set[str] = set()
    frontier = set(seeds)
    for _ in range(max(0, depth)):
        next_nodes = (
            {target for node in frontier for target in adjacency.get(node, set())} - visited - seeds
        )
        if not next_nodes:
            break
        visited.update(next_nodes)
        frontier = next_nodes
    return tuple(sorted(visited, key=lambda value: value.encode("utf-8")))


def _ordered_union(left: Mapping[str, object], right: Mapping[str, object]) -> tuple[str, ...]:
    return tuple(sorted(set(left) | set(right), key=lambda value: value.encode("utf-8")))


def _ordered_symmetric_difference(
    left: Mapping[str, object], right: Mapping[str, object]
) -> tuple[str, ...]:
    return tuple(sorted(set(left) ^ set(right), key=lambda value: value.encode("utf-8")))


def _without_source(value: dict[str, object] | None) -> dict[str, object] | None:
    if value is None:
        return None
    return {key: item for key, item in value.items() if key != "source"}
