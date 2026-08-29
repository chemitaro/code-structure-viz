from __future__ import annotations

from code_structure_viz.adapters.sqlalchemy.model import (
    RedactedExpression,
    RedactedExpressionCategory,
    SqlAlchemyAssociationTableRow,
    SqlAlchemyCardinality,
    SqlAlchemyCheckRow,
    SqlAlchemyColumnRow,
    SqlAlchemyCoverage,
    SqlAlchemyForeignKeyRow,
    SqlAlchemyIndexRow,
    SqlAlchemyIndexTerm,
    SqlAlchemyInheritanceRow,
    SqlAlchemyMappingSource,
    SqlAlchemyMappingSourceKind,
    SqlAlchemyPrimaryKeyRow,
    SqlAlchemyRedactionSummary,
    SqlAlchemyRelation,
    SqlAlchemyRelationKind,
    SqlAlchemyRelationshipRow,
    SqlAlchemyRelationTarget,
    SqlAlchemyRow,
    SqlAlchemySnapshot,
    SqlAlchemySourceLocation,
    SqlAlchemySourceRange,
    SqlAlchemyTable,
    SqlAlchemyTypeCategory,
    SqlAlchemyTypeDescriptor,
    SqlAlchemyUniqueRow,
    redacted_value_count,
    relation_sort_key,
    row_sort_key,
    table_sort_key,
)
from code_structure_viz.adapters.sqlalchemy.plantuml import (
    SqlAlchemyPlantUmlRenderer,
    _render_table_display,
    escape_plantuml_label,
    render_plantuml,
)


def _location(line: int = 1) -> SqlAlchemySourceLocation:
    return SqlAlchemySourceLocation(
        "src/DO_NOT_RENDER_secret.py",
        SqlAlchemySourceRange(line, line),
    )


def _table(
    *,
    schema_name: str | None,
    name: str,
    symbol: str,
    line: int,
) -> SqlAlchemyTable:
    return SqlAlchemyTable.create(
        schema_name=schema_name,
        name=name,
        mapping_sources=(
            SqlAlchemyMappingSource(
                SqlAlchemyMappingSourceKind.DECLARATIVE_CLASS,
                "models",
                f"models.{symbol}",
                _location(line),
            ),
        ),
    )


def _snapshot(
    entities: tuple[SqlAlchemyTable, ...],
    members: tuple[SqlAlchemyRow, ...] = (),
    relations: tuple[SqlAlchemyRelation, ...] = (),
    *,
    association_tables: int = 0,
) -> SqlAlchemySnapshot:
    typed_members = tuple(sorted(members, key=row_sort_key))
    redacted_values = redacted_value_count(typed_members)
    canonical_entities = tuple(sorted(entities, key=table_sort_key))
    coverage = SqlAlchemyCoverage(
        candidate_files=1 if canonical_entities else 0,
        parsed_files=1 if canonical_entities else 0,
        failed_files=(),
        evidence_files=("src/DO_NOT_RENDER_secret.py",) if canonical_entities else (),
        selected_modules=("models",) if canonical_entities else (),
        mapped_classes=len(canonical_entities),
        association_tables=association_tables,
        selected_entities=len(canonical_entities),
        unknown_declarations=0,
        frontier=(),
        redaction=SqlAlchemyRedactionSummary.create(redacted_values),
    )
    return SqlAlchemySnapshot(
        canonical_entities,
        typed_members,
        tuple(sorted(relations, key=relation_sort_key)),
        coverage,
        (),
        False,
    )


def _alias(table: SqlAlchemyTable) -> str:
    return f"T_{table.id.removeprefix('sqlalchemy:table:')}"


def test_escape_plantuml_label_is_injective_and_component_safe() -> None:
    assert escape_plantuml_label("e\N{COMBINING ACUTE ACCENT} A9-/$") == "é A9-/$"
    assert escape_plantuml_label('"') == "_U0022_"
    assert escape_plantuml_label("_U0022_") == "_U005F_U0022_U005F_"
    assert escape_plantuml_label(".") == "_U002E_"
    assert escape_plantuml_label("_U002E_") == "_U005F_U002E_U005F_"
    assert escape_plantuml_label("\\\n{\N{ZERO WIDTH SPACE}") == ("_U005C__U000A__U007B__U200B_")


def test_table_display_escapes_components_before_the_owned_separator() -> None:
    assert _render_table_display(None, "b.c") == "b_U002E_c"
    assert _render_table_display("a", "b.c") == "a.b_U002E_c"
    assert _render_table_display("a.b", "c") == "a_U002E_b.c"


def test_zero_table_snapshot_has_the_exact_skeleton_and_metadata() -> None:
    snapshot = _snapshot(())

    expected = (
        b"@startuml\n"
        b"title SQLAlchemy ER snapshot\n"
        b"left to right direction\n"
        b"skinparam linetype ortho\n"
        b"hide methods\n"
        b"legend right\n"
        b"  rule_version=code-structure-viz.sqlalchemy-redaction/v1\n"
        b"  redacted_values=0\n"
        b"  --> foreign_key\n"
        b"  ..> relationship\n"
        b"  --|> inheritance\n"
        b"  -- association table\n"
        b"  [redacted] literal/expression value omitted\n"
        b"endlegend\n"
        b"@enduml\n"
    )

    assert render_plantuml(snapshot) == expected
    assert SqlAlchemyPlantUmlRenderer().render(snapshot) == expected


def test_renderer_uses_all_closed_row_templates_and_four_relation_arrows() -> None:
    source = _table(schema_name="a", name="b.c", symbol="Source", line=1)
    target = _table(schema_name="a.b", name="c", symbol="Target", line=2)
    secondary = _table(schema_name=None, name="membership", symbol="Membership", line=3)
    source_target = SqlAlchemyRelationTarget.internal_table(source)
    target_target = SqlAlchemyRelationTarget.internal_table(target)
    secondary_target = SqlAlchemyRelationTarget.internal_table(secondary)
    literal = RedactedExpression.present_as(RedactedExpressionCategory.LITERAL)
    sql_expression = RedactedExpression.present_as(RedactedExpressionCategory.SQL_EXPRESSION)
    column = SqlAlchemyColumnRow.create(
        owner_id=source.id,
        name="user_name",
        source=_location(10),
        type=SqlAlchemyTypeDescriptor(
            SqlAlchemyTypeCategory.STRING,
            "sqlalchemy.String",
            literal,
        ),
        nullable=False,
        primary_key=True,
        unique=None,
        index=True,
        default=literal,
        computed=RedactedExpression.present_as(RedactedExpressionCategory.COMPUTED),
        identity=RedactedExpression.present_as(RedactedExpressionCategory.IDENTITY),
    )
    primary_key = SqlAlchemyPrimaryKeyRow.create(
        owner_id=source.id,
        name=None,
        source=_location(11),
        columns=("user_name", "id"),
    )
    unique = SqlAlchemyUniqueRow.create(
        owner_id=source.id,
        name="uq_user_name",
        source=_location(12),
        columns=("user_name",),
    )
    check = SqlAlchemyCheckRow.create(
        owner_id=source.id,
        name="ck_user_active",
        source=_location(13),
        expression=sql_expression,
    )
    index = SqlAlchemyIndexRow.create(
        owner_id=source.id,
        name="ix_user_name",
        source=_location(14),
        unique=None,
        terms=(
            SqlAlchemyIndexTerm.column("user_name"),
            SqlAlchemyIndexTerm.redacted_expression(RedactedExpressionCategory.SQL_EXPRESSION),
        ),
    )
    foreign_key = SqlAlchemyForeignKeyRow.create(
        owner_id=source.id,
        name=None,
        source=_location(15),
        local_columns=("group_id",),
        target=target_target,
        target_columns=("id",),
        ondelete=literal,
    )
    relationship = SqlAlchemyRelationshipRow.create(
        owner_id=source.id,
        name="groups",
        source=_location(16),
        target=target_target,
        cardinality=SqlAlchemyCardinality.MANY,
        uselist=True,
        back_populates="users",
        secondary=secondary_target,
        primaryjoin=sql_expression,
        secondaryjoin=sql_expression,
        order_by=RedactedExpression.present_as(RedactedExpressionCategory.CALLABLE),
        foreign_keys=sql_expression,
    )
    external_relationship = SqlAlchemyRelationshipRow.create(
        owner_id=source.id,
        name="external_items",
        source=_location(17),
        target=SqlAlchemyRelationTarget.external_mapped_class("external.Service"),
        cardinality=SqlAlchemyCardinality.UNKNOWN,
        uselist=None,
        back_populates=None,
        secondary=None,
    )
    unknown_relationship = SqlAlchemyRelationshipRow.create(
        owner_id=source.id,
        name="mystery",
        source=_location(18),
        target=SqlAlchemyRelationTarget.unknown(),
        cardinality=SqlAlchemyCardinality.UNKNOWN,
        uselist=None,
        back_populates=None,
        secondary=None,
    )
    inheritance = SqlAlchemyInheritanceRow.create(
        owner_id=source.id,
        source=_location(19),
        target=target_target,
    )
    association = SqlAlchemyAssociationTableRow.create(
        owner_id=secondary.id,
        name="groups",
        source=_location(20),
        source_table=source_target,
        relationship_target=target_target,
        relationship_member_id=relationship.id,
    )
    relations = (
        SqlAlchemyRelation.create(
            kind=SqlAlchemyRelationKind.FOREIGN_KEY,
            source_id=source.id,
            target=target_target,
            via_member_id=foreign_key.id,
            role=None,
            source=foreign_key.source,
        ),
        SqlAlchemyRelation.create(
            kind=SqlAlchemyRelationKind.RELATIONSHIP,
            source_id=source.id,
            target=target_target,
            via_member_id=relationship.id,
            role="groups",
            source=relationship.source,
        ),
        SqlAlchemyRelation.create(
            kind=SqlAlchemyRelationKind.INHERITANCE,
            source_id=source.id,
            target=target_target,
            via_member_id=None,
            role=None,
            source=inheritance.source,
        ),
        SqlAlchemyRelation.create(
            kind=SqlAlchemyRelationKind.ASSOCIATION,
            source_id=source.id,
            target=secondary_target,
            via_member_id=association.id,
            role="groups",
            source=association.source,
        ),
    )
    members = (
        column,
        primary_key,
        unique,
        check,
        index,
        foreign_key,
        relationship,
        external_relationship,
        unknown_relationship,
        inheritance,
        association,
    )
    snapshot = _snapshot(
        (source, target, secondary),
        members,
        relations,
        association_tables=1,
    )

    rendered = render_plantuml(snapshot).decode()

    expected_lines = {
        'entity "a.b_U002E_c" as ' + _alias(source) + " {",
        'entity "a_U002E_b.c" as ' + _alias(target) + " {",
        "  column user_U005F_name : string type=sqlalchemy_U002E_String "
        "type_parameters=[redacted:literal] nullable=false primary_key=true "
        "unique=? index=true default=[redacted:literal] server_default=- onupdate=- "
        "server_onupdate=- computed=[redacted:computed] identity=[redacted:identity]",
        "  primary_key <unnamed> columns=id,user_U005F_name",
        "  unique uq_U005F_user_U005F_name columns=user_U005F_name",
        "  check ck_U005F_user_U005F_active expression=[redacted:sql_expression]",
        "  index ix_U005F_user_U005F_name unique=? "
        "terms=column:user_U005F_name,[redacted:sql_expression]",
        "  foreign_key <unnamed> local=group_U005F_id target=a_U002E_b.c "
        "remote=id ondelete=[redacted:literal] onupdate=-",
        "  relationship groups target=a_U002E_b.c cardinality=many uselist=true "
        "back_populates=users secondary=membership primaryjoin=[redacted:sql_expression] "
        "secondaryjoin=[redacted:sql_expression] order_by=[redacted:callable] "
        "foreign_keys=[redacted:sql_expression]",
        "  relationship external_U005F_items target=external_U002E_Service "
        "cardinality=unknown uselist=? back_populates=- secondary=- primaryjoin=- "
        "secondaryjoin=- order_by=- foreign_keys=-",
        "  relationship mystery target=<unknown> cardinality=unknown uselist=? "
        "back_populates=- secondary=- primaryjoin=- secondaryjoin=- order_by=- "
        "foreign_keys=-",
        "  inheritance target=a_U002E_b.c",
        "  association_table groups source=a.b_U002E_c target=a_U002E_b.c "
        f"relationship_member={relationship.id.removeprefix('sqlalchemy:row:')}",
        f"{_alias(source)} --> {_alias(target)} : foreign_key <unnamed>",
        f"{_alias(source)} ..> {_alias(target)} : relationship groups",
        f"{_alias(source)} --|> {_alias(target)} : inheritance",
        f"{_alias(source)} -- {_alias(secondary)} : association groups",
    }
    assert expected_lines <= set(rendered.splitlines())
    assert snapshot.coverage.redaction.redacted_values == 11
    lines = rendered.splitlines()
    legend = lines.index("legend right")
    assert lines[legend + 1 : legend + 3] == [
        "  rule_version=code-structure-viz.sqlalchemy-redaction/v1",
        "  redacted_values=11",
    ]
    assert rendered.count("rule_version=") == 1
    assert rendered.count("redacted_values=") == 1
    assert rendered.count('entity "') == 3
    assert "DO_NOT_RENDER" not in rendered
    assert "src/" not in rendered
    assert "sqlalchemy:row:" not in rendered
    assert render_plantuml(snapshot).decode() == rendered


def test_renderer_keeps_quote_and_literal_escape_token_labels_distinct() -> None:
    quote = _table(schema_name=None, name='"', symbol="Quote", line=1)
    token = _table(schema_name=None, name="_U0022_", symbol="Token", line=2)

    rendered = render_plantuml(_snapshot((quote, token))).decode()

    assert f'entity "_U0022_" as {_alias(quote)} {{' in rendered
    assert f'entity "_U005F_U0022_U005F_" as {_alias(token)} {{' in rendered
    assert rendered.count('entity "') == 2
