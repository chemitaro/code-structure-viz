from __future__ import annotations

import pytest

from code_structure_viz.adapters.sqlalchemy.er_semantics import (
    SqlAlchemyErMultiplicity,
    build_er_view,
)
from code_structure_viz.adapters.sqlalchemy.model import (
    RedactedExpression,
    SqlAlchemyCardinality,
    SqlAlchemyColumnRow,
    SqlAlchemyForeignKeyRow,
    SqlAlchemyRelation,
    SqlAlchemyRelationKind,
    SqlAlchemyRelationshipRow,
    SqlAlchemyRelationTarget,
    SqlAlchemySnapshot,
    SqlAlchemyTypeCategory,
    SqlAlchemyTypeDescriptor,
)
from code_structure_viz.adapters.sqlalchemy.plantuml import render_plantuml
from tests.unit.sqlalchemy.test_plantuml import _location, _snapshot, _table


def _column(
    owner_id: str,
    name: str,
    *,
    nullable: bool | None,
    primary_key: bool | None = False,
    unique: bool | None = False,
) -> SqlAlchemyColumnRow:
    return SqlAlchemyColumnRow.create(
        owner_id=owner_id,
        name=name,
        source=_location(),
        type=SqlAlchemyTypeDescriptor(
            SqlAlchemyTypeCategory.INTEGER,
            "sqlalchemy.Integer",
            RedactedExpression.absent(),
        ),
        nullable=nullable,
        primary_key=primary_key,
        unique=unique,
        index=None,
    )


def _foreign_key_snapshot(
    *,
    nullable: bool | None,
    unique: bool | None,
    partial_safe: bool = False,
    composite: bool = False,
) -> tuple[SqlAlchemySnapshot, SqlAlchemyRelation]:
    parent = _table(schema_name=None, name="parents", symbol="Parent", line=1)
    child = _table(schema_name=None, name="children", symbol="Child", line=2)
    if composite:
        parent_columns: tuple[SqlAlchemyColumnRow, ...] = (
            _column(parent.id, "parent_a", nullable=None, primary_key=True),
            _column(parent.id, "parent_b", nullable=None, primary_key=True),
        )
        target_names: tuple[str, ...] = ("parent_a", "parent_b")
    else:
        parent_columns = (_column(parent.id, "id", nullable=None, primary_key=True),)
        target_names = ("id",)
    if composite:
        local_names: tuple[str, ...] = ("parent_a", "parent_b")
        child_columns: tuple[SqlAlchemyColumnRow, ...] = (
            _column(child.id, "parent_a", nullable=nullable, primary_key=True, unique=unique),
            _column(child.id, "parent_b", nullable=nullable, primary_key=True),
        )
    else:
        local_names = ("parent_id",)
        child_columns = (
            _column(child.id, "id", nullable=None, primary_key=True),
            _column(child.id, "parent_id", nullable=nullable, unique=unique),
        )
    foreign_key = SqlAlchemyForeignKeyRow.create(
        owner_id=child.id,
        name=None,
        source=_location(3),
        local_columns=local_names,
        target=SqlAlchemyRelationTarget.internal_table(parent),
        target_columns=target_names,
    )
    relation = SqlAlchemyRelation.create(
        kind=SqlAlchemyRelationKind.FOREIGN_KEY,
        source_id=child.id,
        target=SqlAlchemyRelationTarget.internal_table(parent),
        via_member_id=foreign_key.id,
        role=None,
        source=foreign_key.source,
    )
    unknown = 1 if partial_safe else 0
    snapshot = _snapshot(
        (parent, child),
        (*parent_columns, *child_columns, foreign_key),
        (relation,),
        unknown_declarations=unknown,
    )
    return snapshot, relation


@pytest.mark.parametrize(
    ("nullable", "unique", "source", "target"),
    (
        (
            False,
            False,
            SqlAlchemyErMultiplicity.ZERO_OR_MANY,
            SqlAlchemyErMultiplicity.EXACTLY_ONE,
        ),
        (
            True,
            False,
            SqlAlchemyErMultiplicity.ZERO_OR_MANY,
            SqlAlchemyErMultiplicity.ZERO_OR_ONE,
        ),
        (
            False,
            True,
            SqlAlchemyErMultiplicity.ZERO_OR_ONE,
            SqlAlchemyErMultiplicity.EXACTLY_ONE,
        ),
        (
            True,
            True,
            SqlAlchemyErMultiplicity.ZERO_OR_ONE,
            SqlAlchemyErMultiplicity.ZERO_OR_ONE,
        ),
    ),
)
def test_fk_multiplicity_uses_nullable_and_unique_evidence(
    nullable: bool,
    unique: bool,
    source: SqlAlchemyErMultiplicity,
    target: SqlAlchemyErMultiplicity,
) -> None:
    snapshot, _ = _foreign_key_snapshot(nullable=nullable, unique=unique)

    projected = build_er_view(snapshot).relations

    assert len(projected) == 1
    assert projected[0].source_multiplicity is source
    assert projected[0].target_multiplicity is target


def test_partial_safe_does_not_infer_non_unique_from_missing_evidence() -> None:
    snapshot, _ = _foreign_key_snapshot(nullable=False, unique=False, partial_safe=True)

    projected = build_er_view(snapshot).relations

    assert projected[0].source_multiplicity is SqlAlchemyErMultiplicity.UNKNOWN
    assert projected[0].target_multiplicity is SqlAlchemyErMultiplicity.EXACTLY_ONE


def test_partial_safe_keeps_explicit_unique_positive_evidence() -> None:
    snapshot, _ = _foreign_key_snapshot(nullable=False, unique=True, partial_safe=True)

    projected = build_er_view(snapshot).relations

    assert projected[0].source_multiplicity is SqlAlchemyErMultiplicity.ZERO_OR_ONE


def test_composite_primary_key_is_one_candidate_key_not_singleton_keys() -> None:
    snapshot, _ = _foreign_key_snapshot(
        nullable=False,
        unique=False,
        composite=True,
    )

    projected = build_er_view(snapshot).relations

    assert projected[0].source_multiplicity is SqlAlchemyErMultiplicity.ZERO_OR_ONE


def test_unknown_nullable_or_unknown_target_key_stays_unknown() -> None:
    snapshot, _ = _foreign_key_snapshot(nullable=None, unique=True)

    projected = build_er_view(snapshot).relations

    assert projected[0].target_multiplicity is SqlAlchemyErMultiplicity.UNKNOWN


def test_reciprocal_many_to_many_secondary_becomes_one_direct_edge() -> None:
    users = _table(schema_name=None, name="users", symbol="User", line=1)
    groups = _table(schema_name=None, name="groups", symbol="Group", line=2)
    membership = _table(schema_name=None, name="membership", symbol="Membership", line=3)
    secondary = SqlAlchemyRelationTarget.internal_table(membership)
    user_to_group = SqlAlchemyRelationshipRow.create(
        owner_id=users.id,
        name="groups",
        source=_location(4),
        target=SqlAlchemyRelationTarget.internal_table(groups),
        cardinality=SqlAlchemyCardinality.MANY,
        uselist=True,
        back_populates="users",
        secondary=secondary,
    )
    group_to_user = SqlAlchemyRelationshipRow.create(
        owner_id=groups.id,
        name="users",
        source=_location(5),
        target=SqlAlchemyRelationTarget.internal_table(users),
        cardinality=SqlAlchemyCardinality.MANY,
        uselist=True,
        back_populates="groups",
        secondary=secondary,
    )
    relations = (
        SqlAlchemyRelation.create(
            kind=SqlAlchemyRelationKind.RELATIONSHIP,
            source_id=users.id,
            target=SqlAlchemyRelationTarget.internal_table(groups),
            via_member_id=user_to_group.id,
            role="groups",
            source=user_to_group.source,
        ),
        SqlAlchemyRelation.create(
            kind=SqlAlchemyRelationKind.RELATIONSHIP,
            source_id=groups.id,
            target=SqlAlchemyRelationTarget.internal_table(users),
            via_member_id=group_to_user.id,
            role="users",
            source=group_to_user.source,
        ),
    )
    snapshot = _snapshot(
        (users, groups, membership),
        (user_to_group, group_to_user),
        relations,
    )

    projected = build_er_view(snapshot).relations

    assert len(projected) == 1
    assert projected[0].source_multiplicity is SqlAlchemyErMultiplicity.ZERO_OR_MANY
    assert projected[0].target_multiplicity is SqlAlchemyErMultiplicity.ZERO_OR_MANY
    assert projected[0].role == "groups / users"


@pytest.mark.parametrize(
    ("nullable", "unique", "edge"),
    (
        (False, False, "}o--||"),
        (True, False, "}o--o|"),
        (False, True, "|o--||"),
        (True, True, "|o--o|"),
    ),
)
def test_renderer_emits_ie_crowfoot_edge(
    nullable: bool,
    unique: bool,
    edge: str,
) -> None:
    snapshot, _ = _foreign_key_snapshot(nullable=nullable, unique=unique)

    rendered = render_plantuml(snapshot).decode("utf-8")

    assert edge in rendered
    assert " --> " not in rendered
