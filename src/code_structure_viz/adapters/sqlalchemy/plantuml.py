from __future__ import annotations

import unicodedata

from code_structure_viz.adapters.sqlalchemy.model import (
    IndexTermKind,
    RedactedExpression,
    SqlAlchemyAssociationTableRow,
    SqlAlchemyCheckRow,
    SqlAlchemyColumnRow,
    SqlAlchemyForeignKeyRow,
    SqlAlchemyIndexRow,
    SqlAlchemyInheritanceRow,
    SqlAlchemyPrimaryKeyRow,
    SqlAlchemyRelation,
    SqlAlchemyRelationKind,
    SqlAlchemyRelationshipRow,
    SqlAlchemyRelationTarget,
    SqlAlchemyRow,
    SqlAlchemySnapshot,
    SqlAlchemyTable,
    SqlAlchemyTargetKind,
    SqlAlchemyTargetResolution,
    SqlAlchemyUniqueRow,
)

_HEADER = (
    "@startuml",
    "title SQLAlchemy ER snapshot",
    "left to right direction",
    "skinparam linetype ortho",
    "hide methods",
)
_LEGEND_TAIL = (
    "  --> foreign_key",
    "  ..> relationship",
    "  --|> inheritance",
    "  -- association table",
    "  [redacted] literal/expression value omitted",
    "endlegend",
    "@enduml",
)


def escape_plantuml_label(value: str) -> str:
    escaped: list[str] = []
    for character in unicodedata.normalize("NFC", value):
        if unicodedata.category(character)[0] in {"L", "N"} or character in {
            " ",
            "-",
            "/",
            "$",
        }:
            escaped.append(character)
        else:
            escaped.append(f"_U{ord(character):04X}_")
    return "".join(escaped)


def _render_table_display(schema_name: str | None, table_name: str) -> str:
    table = escape_plantuml_label(table_name)
    if schema_name is None:
        return table
    return f"{escape_plantuml_label(schema_name)}.{table}"


def render_plantuml(snapshot: SqlAlchemySnapshot) -> bytes:
    members_by_id = {member.id: member for member in snapshot.members}
    lines = list(_HEADER)
    for table in snapshot.entities:
        lines.append(
            f'entity "{_render_table_display(table.schema_name, table.name)}" '
            f"as {_table_alias(table)} {{"
        )
        lines.extend(
            _row_line(member) for member in snapshot.members if member.owner_id == table.id
        )
        lines.append("}")
    for relation in snapshot.relations:
        line = _relation_line(relation, members_by_id)
        if line is not None:
            lines.append(line)
    lines.extend(
        (
            "legend right",
            f"  rule_version={snapshot.coverage.redaction.rule_version}",
            f"  redacted_values={snapshot.coverage.redaction.redacted_values}",
            *_LEGEND_TAIL,
        )
    )
    return ("\n".join(lines) + "\n").encode("utf-8")


class SqlAlchemyPlantUmlRenderer:
    """Render SQLAlchemy ER PlantUML v1 bytes."""

    def render(self, snapshot: SqlAlchemySnapshot) -> bytes:
        return render_plantuml(snapshot)


def _table_alias(table: SqlAlchemyTable) -> str:
    return _table_alias_from_id(table.id)


def _table_alias_from_id(table_id: str) -> str:
    return f"T_{table_id.removeprefix('sqlalchemy:table:')}"


def _name_token(name: str | None) -> str:
    return escape_plantuml_label(name) if name is not None else "<unnamed>"


def _bool_token(value: bool | None) -> str:
    if value is None:
        return "?"
    return "true" if value else "false"


def _redacted_token(value: RedactedExpression) -> str:
    if not value.present:
        return "-"
    return f"[redacted:{value.category.value}]"


def _target_token(value: SqlAlchemyRelationTarget) -> str:
    if value.resolution is SqlAlchemyTargetResolution.UNKNOWN:
        return "<unknown>"
    if value.kind is SqlAlchemyTargetKind.TABLE:
        assert value.table_name is not None
        return _render_table_display(value.schema_name, value.table_name)
    assert value.kind is SqlAlchemyTargetKind.MAPPED_CLASS
    assert value.symbol is not None
    return escape_plantuml_label(value.symbol)


def _columns_token(values: tuple[str, ...]) -> str:
    return ",".join(escape_plantuml_label(value) for value in values)


def _row_line(value: SqlAlchemyRow) -> str:
    if isinstance(value, SqlAlchemyColumnRow):
        type_name = escape_plantuml_label(value.type.name) if value.type.name is not None else "-"
        return (
            f"  column {_name_token(value.name)} : {value.type.category.value} "
            f"type={type_name} type_parameters={_redacted_token(value.type.parameters)} "
            f"nullable={_bool_token(value.nullable)} "
            f"primary_key={_bool_token(value.primary_key)} "
            f"unique={_bool_token(value.unique)} index={_bool_token(value.index)} "
            f"default={_redacted_token(value.default)} "
            f"server_default={_redacted_token(value.server_default)} "
            f"onupdate={_redacted_token(value.onupdate)} "
            f"server_onupdate={_redacted_token(value.server_onupdate)} "
            f"computed={_redacted_token(value.computed)} "
            f"identity={_redacted_token(value.identity)}"
        )
    if isinstance(value, SqlAlchemyPrimaryKeyRow):
        return f"  primary_key {_name_token(value.name)} columns={_columns_token(value.columns)}"
    if isinstance(value, SqlAlchemyUniqueRow):
        return f"  unique {_name_token(value.name)} columns={_columns_token(value.columns)}"
    if isinstance(value, SqlAlchemyCheckRow):
        return f"  check {_name_token(value.name)} expression={_redacted_token(value.expression)}"
    if isinstance(value, SqlAlchemyIndexRow):
        terms = ",".join(
            (
                f"column:{escape_plantuml_label(term.column_name)}"
                if term.kind is IndexTermKind.COLUMN and term.column_name is not None
                else _redacted_token(term.expression)
            )
            for term in value.terms
        )
        return f"  index {_name_token(value.name)} unique={_bool_token(value.unique)} terms={terms}"
    if isinstance(value, SqlAlchemyForeignKeyRow):
        return (
            f"  foreign_key {_name_token(value.name)} "
            f"local={_columns_token(value.local_columns)} target={_target_token(value.target)} "
            f"remote={_columns_token(value.target_columns)} "
            f"ondelete={_redacted_token(value.ondelete)} "
            f"onupdate={_redacted_token(value.onupdate)}"
        )
    if isinstance(value, SqlAlchemyRelationshipRow):
        secondary = _target_token(value.secondary) if value.secondary is not None else "-"
        back_populates = (
            escape_plantuml_label(value.back_populates) if value.back_populates is not None else "-"
        )
        return (
            f"  relationship {_name_token(value.name)} target={_target_token(value.target)} "
            f"cardinality={value.cardinality.value} uselist={_bool_token(value.uselist)} "
            f"back_populates={back_populates} secondary={secondary} "
            f"primaryjoin={_redacted_token(value.primaryjoin)} "
            f"secondaryjoin={_redacted_token(value.secondaryjoin)} "
            f"order_by={_redacted_token(value.order_by)} "
            f"foreign_keys={_redacted_token(value.foreign_keys)}"
        )
    if isinstance(value, SqlAlchemyInheritanceRow):
        return f"  inheritance target={_target_token(value.target)}"
    if isinstance(value, SqlAlchemyAssociationTableRow):
        member_id = value.relationship_member_id.removeprefix("sqlalchemy:row:")
        return (
            f"  association_table {_name_token(value.name)} "
            f"source={_target_token(value.source_table)} "
            f"target={_target_token(value.relationship_target)} "
            f"relationship_member={member_id}"
        )
    raise TypeError("unknown SQLAlchemy row DTO")


def _relation_line(
    value: SqlAlchemyRelation,
    members_by_id: dict[str, SqlAlchemyRow],
) -> str | None:
    if value.target.resolution is not SqlAlchemyTargetResolution.INTERNAL:
        return None
    assert value.target.id is not None
    source = _table_alias_from_id(value.source_id)
    target = _table_alias_from_id(value.target.id)
    if value.kind is SqlAlchemyRelationKind.INHERITANCE:
        return f"{source} --|> {target} : inheritance"
    assert value.via_member_id is not None
    member = members_by_id[value.via_member_id]
    if value.kind is SqlAlchemyRelationKind.FOREIGN_KEY:
        if not isinstance(member, SqlAlchemyForeignKeyRow):
            raise ValueError("foreign-key relation member is invalid")
        return f"{source} --> {target} : foreign_key {_name_token(member.name)}"
    if value.kind is SqlAlchemyRelationKind.RELATIONSHIP:
        if not isinstance(member, SqlAlchemyRelationshipRow):
            raise ValueError("relationship relation member is invalid")
        return f"{source} ..> {target} : relationship {_name_token(member.name)}"
    if not isinstance(member, SqlAlchemyAssociationTableRow):
        raise ValueError("association relation member is invalid")
    return f"{source} -- {target} : association {_name_token(member.name)}"
