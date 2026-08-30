from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from code_structure_viz.adapters.sqlalchemy.model import (
    IndexTermKind,
    SqlAlchemyAssociationTableRow,
    SqlAlchemyCardinality,
    SqlAlchemyColumnRow,
    SqlAlchemyForeignKeyRow,
    SqlAlchemyIndexRow,
    SqlAlchemyPrimaryKeyRow,
    SqlAlchemyRelation,
    SqlAlchemyRelationKind,
    SqlAlchemyRelationshipRow,
    SqlAlchemyRow,
    SqlAlchemySnapshot,
    SqlAlchemyTargetResolution,
    SqlAlchemyUniqueRow,
    relation_sort_key,
)


class SqlAlchemyErMultiplicity(StrEnum):
    """A conservative Information Engineering endpoint multiplicity."""

    EXACTLY_ONE = "exactly_one"
    ZERO_OR_ONE = "zero_or_one"
    ZERO_OR_MANY = "zero_or_many"
    ONE_OR_MANY = "one_or_many"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class SqlAlchemyErRelation:
    """A PlantUML-independent ER projection of one semantic relation."""

    relation: SqlAlchemyRelation
    source_multiplicity: SqlAlchemyErMultiplicity | None
    target_multiplicity: SqlAlchemyErMultiplicity | None
    role: str | None = None


@dataclass(frozen=True, slots=True)
class SqlAlchemyErView:
    snapshot: SqlAlchemySnapshot
    relations: tuple[SqlAlchemyErRelation, ...]


@dataclass(frozen=True, slots=True)
class _KeyFacts:
    keys: frozenset[frozenset[str]]

    def proves_unique(self, columns: tuple[str, ...]) -> bool:
        values = frozenset(columns)
        return bool(values) and any(key <= values for key in self.keys)


def build_er_view(snapshot: SqlAlchemySnapshot) -> SqlAlchemyErView:
    """Derive a conservative ER view without changing semantic snapshot facts."""

    members_by_id = {member.id: member for member in snapshot.members}
    relationships_list: list[tuple[SqlAlchemyRelation, SqlAlchemyRelationshipRow]] = []
    for relation in snapshot.relations:
        if relation.kind is not SqlAlchemyRelationKind.RELATIONSHIP:
            continue
        if relation.via_member_id is None:
            continue
        member = members_by_id.get(relation.via_member_id)
        if isinstance(member, SqlAlchemyRelationshipRow):
            relationships_list.append((relation, member))
    relationships = tuple(relationships_list)
    relationships_by_id = {relation.id: (relation, member) for relation, member in relationships}
    key_facts = _key_facts(snapshot)
    fk_relations = tuple(
        relation
        for relation in snapshot.relations
        if relation.kind is SqlAlchemyRelationKind.FOREIGN_KEY
    )
    result: list[SqlAlchemyErRelation] = []
    consumed_relationships: set[str] = set()

    for relation in snapshot.relations:
        if relation.target.resolution is not SqlAlchemyTargetResolution.INTERNAL:
            continue
        member = members_by_id.get(relation.via_member_id) if relation.via_member_id else None
        if relation.kind is SqlAlchemyRelationKind.FOREIGN_KEY:
            if not isinstance(member, SqlAlchemyForeignKeyRow):
                continue
            source, target = _foreign_key_multiplicity(
                member,
                snapshot=snapshot,
                key_facts=key_facts,
            )
            result.append(SqlAlchemyErRelation(relation, source, target))
            continue

        if relation.kind is SqlAlchemyRelationKind.RELATIONSHIP:
            if not isinstance(member, SqlAlchemyRelationshipRow):
                continue
            if relation.id in consumed_relationships:
                continue
            reciprocal = _reciprocal_relationship(
                relation,
                member,
                relationships_by_id,
            )
            if reciprocal is not None:
                _, reciprocal_member = reciprocal
                if not _secondary_pair_matches(member, reciprocal_member):
                    reciprocal = None
            if reciprocal is not None:
                reciprocal_relation, reciprocal_member = reciprocal
                consumed_relationships.add(reciprocal_relation.id)
                if relation_sort_key(reciprocal_relation) < relation_sort_key(relation):
                    consumed_relationships.add(relation.id)
                    continue
                source = _relationship_navigation_multiplicity(
                    reciprocal_relation,
                    reciprocal_member,
                    snapshot=snapshot,
                    fk_relations=fk_relations,
                    key_facts=key_facts,
                )
                target = _relationship_navigation_multiplicity(
                    relation,
                    member,
                    snapshot=snapshot,
                    fk_relations=fk_relations,
                    key_facts=key_facts,
                )
                role = _paired_role(member.name, reciprocal_member.name)
                result.append(SqlAlchemyErRelation(relation, source, target, role))
                continue

            source, target = _relationship_multiplicity(
                relation,
                member,
                snapshot=snapshot,
                fk_relations=fk_relations,
                key_facts=key_facts,
            )
            result.append(SqlAlchemyErRelation(relation, source, target))
            continue

        if relation.kind is SqlAlchemyRelationKind.INHERITANCE:
            result.append(SqlAlchemyErRelation(relation, None, None))
            continue

        if relation.kind is SqlAlchemyRelationKind.ASSOCIATION and isinstance(
            member, SqlAlchemyAssociationTableRow
        ):
            # This row describes ORM secondary metadata, not a physical FK.
            # Keep it as an unknown-cardinality metadata edge; physical FKs
            # remain the source of truth for the bridge table.
            result.append(SqlAlchemyErRelation(relation, None, None))

    return SqlAlchemyErView(snapshot, tuple(result))


def _key_facts(snapshot: SqlAlchemySnapshot) -> dict[str, _KeyFacts]:
    members_by_owner: dict[str, list[SqlAlchemyRow]] = {table.id: [] for table in snapshot.entities}
    for member in snapshot.members:
        members_by_owner.setdefault(member.owner_id, []).append(member)

    facts: dict[str, _KeyFacts] = {}
    for owner_id, members in members_by_owner.items():
        columns = {
            member.name: member
            for member in members
            if isinstance(member, SqlAlchemyColumnRow) and member.name is not None
        }
        inline_primary = frozenset(
            name for name, member in columns.items() if member.primary_key is True
        )
        keys: set[frozenset[str]] = set()
        primary_rows = [member for member in members if isinstance(member, SqlAlchemyPrimaryKeyRow)]
        if inline_primary:
            # Analyzer versions may emit one singleton row per inline column in
            # a composite PK. The complete inline set is the only safe key.
            keys.add(inline_primary)
            if len(inline_primary) == 1:
                keys.update(frozenset(row.columns) for row in primary_rows)
            else:
                keys.update(frozenset(row.columns) for row in primary_rows if len(row.columns) > 1)
        else:
            keys.update(frozenset(row.columns) for row in primary_rows)
        for member in members:
            if isinstance(member, SqlAlchemyColumnRow) and member.unique is True:
                assert member.name is not None
                keys.add(frozenset((member.name,)))
            elif isinstance(member, SqlAlchemyUniqueRow):
                keys.add(frozenset(member.columns))
            elif isinstance(member, SqlAlchemyIndexRow) and member.unique is True:
                if all(term.kind is IndexTermKind.COLUMN for term in member.terms):
                    names = tuple(
                        term.column_name for term in member.terms if term.column_name is not None
                    )
                    if len(names) == len(member.terms):
                        keys.add(frozenset(names))
        facts[owner_id] = _KeyFacts(frozenset(key for key in keys if key))
    return facts


def _foreign_key_multiplicity(
    member: SqlAlchemyForeignKeyRow,
    *,
    snapshot: SqlAlchemySnapshot,
    key_facts: dict[str, _KeyFacts],
) -> tuple[SqlAlchemyErMultiplicity, SqlAlchemyErMultiplicity]:
    target_id = member.target.id
    if target_id is None:
        return SqlAlchemyErMultiplicity.UNKNOWN, SqlAlchemyErMultiplicity.UNKNOWN
    target_key = key_facts.get(target_id)
    source_key = key_facts.get(member.owner_id)
    target_is_one = target_key is not None and target_key.proves_unique(member.target_columns)
    source_is_one = source_key is not None and source_key.proves_unique(member.local_columns)

    source = (
        SqlAlchemyErMultiplicity.ZERO_OR_ONE
        if source_is_one
        else SqlAlchemyErMultiplicity.ZERO_OR_MANY
        if not snapshot.partial_safe
        else SqlAlchemyErMultiplicity.UNKNOWN
    )
    nullable = _foreign_key_nullable(member, snapshot)
    if not target_is_one or nullable is None:
        target = SqlAlchemyErMultiplicity.UNKNOWN
    elif nullable:
        target = SqlAlchemyErMultiplicity.ZERO_OR_ONE
    else:
        target = SqlAlchemyErMultiplicity.EXACTLY_ONE
    return source, target


def _foreign_key_nullable(
    member: SqlAlchemyForeignKeyRow,
    snapshot: SqlAlchemySnapshot,
) -> bool | None:
    columns = {
        (row.owner_id, row.name): row
        for row in snapshot.members
        if isinstance(row, SqlAlchemyColumnRow) and row.name is not None
    }
    values: list[bool | None] = []
    for name in member.local_columns:
        column = columns.get((member.owner_id, name))
        if column is None:
            return None
        if column.primary_key is True or column.nullable is False:
            values.append(False)
        elif column.nullable is True:
            values.append(True)
        else:
            values.append(None)
    if any(value is None for value in values):
        return None
    return any(values)


def _reciprocal_relationship(
    relation: SqlAlchemyRelation,
    member: SqlAlchemyRelationshipRow,
    relationships_by_id: dict[str, tuple[SqlAlchemyRelation, SqlAlchemyRelationshipRow]],
) -> tuple[SqlAlchemyRelation, SqlAlchemyRelationshipRow] | None:
    if member.back_populates is None or relation.target.id is None:
        return None
    candidates = [
        (candidate_relation, candidate)
        for candidate_relation, candidate in relationships_by_id.values()
        if candidate.owner_id == relation.target.id
        and candidate.name == member.back_populates
        and candidate.target.id == relation.source_id
        and candidate.back_populates == member.name
    ]
    if len(candidates) != 1:
        return None
    return candidates[0]


def _relationship_navigation_multiplicity(
    relation: SqlAlchemyRelation,
    member: SqlAlchemyRelationshipRow,
    *,
    snapshot: SqlAlchemySnapshot,
    fk_relations: tuple[SqlAlchemyRelation, ...],
    key_facts: dict[str, _KeyFacts],
) -> SqlAlchemyErMultiplicity:
    if member.cardinality is SqlAlchemyCardinality.MANY:
        return SqlAlchemyErMultiplicity.ZERO_OR_MANY
    if member.cardinality is not SqlAlchemyCardinality.SCALAR:
        return SqlAlchemyErMultiplicity.UNKNOWN
    direct = _single_fk_for_pair(fk_relations, relation.source_id, relation.target.id)
    if direct is None:
        return SqlAlchemyErMultiplicity.UNKNOWN
    fk_member = next(
        row
        for row in snapshot.members
        if isinstance(row, SqlAlchemyForeignKeyRow) and row.id == direct.via_member_id
    )
    _, target = _foreign_key_multiplicity(
        fk_member,
        snapshot=snapshot,
        key_facts=key_facts,
    )
    return target


def _relationship_multiplicity(
    relation: SqlAlchemyRelation,
    member: SqlAlchemyRelationshipRow,
    *,
    snapshot: SqlAlchemySnapshot,
    fk_relations: tuple[SqlAlchemyRelation, ...],
    key_facts: dict[str, _KeyFacts],
) -> tuple[SqlAlchemyErMultiplicity, SqlAlchemyErMultiplicity]:
    target = _relationship_navigation_multiplicity(
        relation,
        member,
        snapshot=snapshot,
        fk_relations=fk_relations,
        key_facts=key_facts,
    )
    direct = _single_fk_for_pair(fk_relations, relation.source_id, relation.target.id)
    reverse = _single_fk_for_pair(fk_relations, relation.target.id, relation.source_id)
    if direct is not None:
        fk_member = _fk_member(snapshot, direct)
        source, fk_target = _foreign_key_multiplicity(
            fk_member,
            snapshot=snapshot,
            key_facts=key_facts,
        )
        if target is SqlAlchemyErMultiplicity.UNKNOWN:
            target = fk_target
        return source, target
    if reverse is not None:
        fk_member = _fk_member(snapshot, reverse)
        reverse_source, reverse_target = _foreign_key_multiplicity(
            fk_member,
            snapshot=snapshot,
            key_facts=key_facts,
        )
        if target is SqlAlchemyErMultiplicity.UNKNOWN:
            target = reverse_source
        return reverse_target, target
    return SqlAlchemyErMultiplicity.UNKNOWN, target


def _single_fk_for_pair(
    relations: tuple[SqlAlchemyRelation, ...],
    source_id: str | None,
    target_id: str | None,
) -> SqlAlchemyRelation | None:
    if source_id is None or target_id is None:
        return None
    candidates = [
        relation
        for relation in relations
        if relation.source_id == source_id and relation.target.id == target_id
    ]
    return candidates[0] if len(candidates) == 1 else None


def _fk_member(
    snapshot: SqlAlchemySnapshot,
    relation: SqlAlchemyRelation,
) -> SqlAlchemyForeignKeyRow:
    assert relation.via_member_id is not None
    member = next(
        row
        for row in snapshot.members
        if isinstance(row, SqlAlchemyForeignKeyRow) and row.id == relation.via_member_id
    )
    return member


def _paired_role(first: str | None, second: str | None) -> str | None:
    if first is None:
        return second
    if second is None or first == second:
        return first
    return f"{first} / {second}"


def _secondary_pair_matches(
    first: SqlAlchemyRelationshipRow,
    second: SqlAlchemyRelationshipRow,
) -> bool:
    if first.secondary is None or second.secondary is None:
        return first.secondary is None and second.secondary is None
    return first.secondary == second.secondary
