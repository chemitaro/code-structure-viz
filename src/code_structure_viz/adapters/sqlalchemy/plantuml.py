from __future__ import annotations

import re
import unicodedata
from typing import TYPE_CHECKING

from code_structure_viz.adapters.sqlalchemy.er_semantics import (
    SqlAlchemyErMultiplicity,
    SqlAlchemyErRelation,
    SqlAlchemyErView,
    build_er_view,
)
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
from code_structure_viz.semantic.diff import SemanticDelta

if TYPE_CHECKING:
    from code_structure_viz.adapters.sqlalchemy.diff import SqlAlchemyDiffResult

_HEADER = (
    "@startuml",
    "title SQLAlchemy ER snapshot",
    "top to bottom direction",
    "hide circle",
    "skinparam linetype ortho",
    "hide methods",
)
_LEGEND_TAIL = (
    "  ||--|| exactly_one",
    "  |o--o| zero_or_one",
    "  }o--o{ zero_or_many",
    "  }|--|{ one_or_many",
    "  -- foreign_key (solid)",
    "  .. relationship (dotted)",
    "  --|> inheritance (not cardinality)",
    "  .. association metadata (cardinality unknown)",
    "  [?] evidence insufficient; plain line retained",
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


def escape_plantuml_display_label(value: str) -> str:
    """Escape a user value while keeping common identifier punctuation readable."""
    escaped: list[str] = []
    normalized = unicodedata.normalize("NFC", value)
    for index, character in enumerate(normalized):
        if character == "_" and re.match(r"_U[0-9A-Fa-f]{4,6}_", normalized[index:]):
            escaped.append("_U005F_")
            continue
        if unicodedata.category(character)[0] in {"L", "N"} or character in {
            " ",
            "-",
            "/",
            "$",
            "_",
            ".",
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
    return SqlAlchemyPlantUmlRenderer().render(snapshot)


class SqlAlchemyPlantUmlRenderer:
    """Render the SQLAlchemy PlantUML ER contract v2."""

    def render(self, snapshot: SqlAlchemySnapshot) -> bytes:
        return self.render_view(build_er_view(snapshot))

    def render_view(self, view: SqlAlchemyErView) -> bytes:
        return _render_view(view)


def render_sqlalchemy_diff(result: SqlAlchemyDiffResult) -> bytes:
    """Render SQLAlchemy changes without source provenance."""
    lines = [
        "@startuml",
        "title SQLAlchemy ER diff",
        "top to bottom direction",
        "hide circle",
        "skinparam linetype ortho",
        "hide methods",
    ]
    if result.status != "complete":
        lines.append(f'note "status: {result.status}" as N_DIFF_STATUS')

    entity_deltas = {item.identity: item for item in result.entities}
    member_deltas: dict[str, list[SemanticDelta]] = {}
    for member_delta in result.members:
        value = member_delta.after if member_delta.after is not None else member_delta.before
        if isinstance(value, dict) and isinstance(value.get("owner_id"), str):
            member_deltas.setdefault(value["owner_id"], []).append(member_delta)

    tables: dict[str, SqlAlchemyTable] = {}
    before_members = _members_by_id(result.before.snapshot)
    after_members = _members_by_id(result.after.snapshot)
    for snapshot in (result.before.snapshot, result.after.snapshot):
        if snapshot is not None:
            tables.update({item.id: item for item in snapshot.entities})
    rendered_ids = {
        *entity_deltas,
        *result.seeds,
        *result.impact.upstream,
        *result.impact.downstream,
        *member_deltas,
    }
    for identity in sorted(rendered_ids, key=lambda value: value.encode("utf-8")):
        table = tables.get(identity)
        if table is None:
            continue
        entity_delta = entity_deltas.get(identity)
        marker = (
            "+"
            if entity_delta is not None and entity_delta.status.value == "added"
            else "-"
            if entity_delta is not None and entity_delta.status.value == "removed"
            else "~"
            if identity in member_deltas
            else "context"
        )
        color = {
            "+": "#PaleGreen",
            "-": "#MistyRose",
            "~": "#LightYellow",
            "context": "#LightGray",
        }[marker]
        label = f"{marker} {_render_table_display(table.schema_name, table.name)}"
        lines.append(f'entity "{label}" as {_table_alias(table)} {color} {{')
        for member in sorted(member_deltas.get(identity, ()), key=lambda item: item.identity):
            value = member.after if member.after is not None else member.before
            if not isinstance(value, dict):
                continue
            if member.status.value == "modified":
                before_row = before_members[member.identity]
                after_row = after_members[member.identity]
                before_supplement, after_supplement = _hidden_safe_change_supplements(
                    before_row, after_row
                )
                lines.append(
                    "  ~ before "
                    + _row_line(
                        before_row,
                        foreign_key_columns=_foreign_key_columns(
                            result.before.snapshot, before_row.owner_id
                        ),
                    ).removeprefix("  ")
                    + before_supplement
                )
                lines.append(
                    "  ~ after "
                    + _row_line(
                        after_row,
                        foreign_key_columns=_foreign_key_columns(
                            result.after.snapshot, after_row.owner_id
                        ),
                    ).removeprefix("  ")
                    + after_supplement
                )
            else:
                row_marker = "+" if member.status.value == "added" else "-"
                row = (
                    after_members[member.identity]
                    if member.status.value == "added"
                    else before_members[member.identity]
                )
                snapshot = (
                    result.after.snapshot
                    if member.status.value == "added"
                    else result.before.snapshot
                )
                lines.append(
                    f"  {row_marker} "
                    + _row_line(
                        row,
                        foreign_key_columns=_foreign_key_columns(snapshot, row.owner_id),
                    ).removeprefix("  ")
                )
        lines.append("}")

    relation_deltas = {item.identity: item for item in result.relations}
    before_relations = _diff_er_relations(result.before.snapshot)
    after_relations = _diff_er_relations(result.after.snapshot)
    for identity in sorted(
        set(before_relations) | set(after_relations),
        key=lambda value: value.encode("utf-8"),
    ):
        relation, members = after_relations.get(identity) or before_relations[identity]
        target_id = relation.relation.target.id
        if relation.relation.source_id not in rendered_ids or target_id not in rendered_ids:
            continue
        line = _relation_line(relation, members)
        if line is not None:
            lines.append(line)
        relation_delta = relation_deltas.get(identity)
        if relation_delta is not None:
            marker = "+" if relation_delta.status.value == "added" else "-"
            label = f"{marker} relation {relation.relation.kind.value}"
            alias = identity.removeprefix("sqlalchemy:relation:")
            lines.append(f'note "{escape_plantuml_display_label(label)}" as N_{alias}')

    lines.extend(
        (
            "legend right",
            "  + added",
            "  - removed (ghost)",
            "  ~ modified (before/after)",
            "  context impact context",
            "endlegend",
            "@enduml",
        )
    )
    return ("\n".join(lines) + "\n").encode("utf-8")


def _members_by_id(snapshot: SqlAlchemySnapshot | None) -> dict[str, SqlAlchemyRow]:
    if snapshot is None:
        return {}
    return {item.id: item for item in snapshot.members}


def _hidden_safe_change_supplements(
    before: SqlAlchemyRow,
    after: SqlAlchemyRow,
) -> tuple[str, str]:
    changes: list[tuple[str, str, str]] = []
    candidates: tuple[tuple[str, RedactedExpression, RedactedExpression], ...]
    if isinstance(before, SqlAlchemyColumnRow) and isinstance(after, SqlAlchemyColumnRow):
        candidates = (
            ("computed", before.computed, after.computed),
            ("default", before.default, after.default),
            ("identity", before.identity, after.identity),
            ("onupdate", before.onupdate, after.onupdate),
            ("server_default", before.server_default, after.server_default),
            ("server_onupdate", before.server_onupdate, after.server_onupdate),
            ("type.parameters", before.type.parameters, after.type.parameters),
        )
        changes.extend(
            (name, _redacted_token(before_value), _redacted_token(after_value))
            for name, before_value, after_value in candidates
            if before_value != after_value
        )
        if before.type.name != after.type.name and _short_type_name(before) == _short_type_name(
            after
        ):
            assert before.type.name is not None and after.type.name is not None
            changes.append(
                (
                    "type.name",
                    escape_plantuml_display_label(before.type.name),
                    escape_plantuml_display_label(after.type.name),
                )
            )
        compact_candidates = (
            ("index", before.index, after.index, before.index is True, after.index is True),
            (
                "nullable",
                before.nullable,
                after.nullable,
                _nullable_marker(before),
                _nullable_marker(after),
            ),
            (
                "primary_key",
                before.primary_key,
                after.primary_key,
                before.primary_key is True,
                after.primary_key is True,
            ),
            ("unique", before.unique, after.unique, before.unique is True, after.unique is True),
        )
        changes.extend(
            (name, _safe_bool_token(before_value), _safe_bool_token(after_value))
            for name, before_value, after_value, before_marker, after_marker in compact_candidates
            if before_value != after_value and before_marker == after_marker
        )
    elif isinstance(before, SqlAlchemyRelationshipRow) and isinstance(
        after, SqlAlchemyRelationshipRow
    ):
        candidates = (
            ("foreign_keys", before.foreign_keys, after.foreign_keys),
            ("order_by", before.order_by, after.order_by),
            ("primaryjoin", before.primaryjoin, after.primaryjoin),
            ("secondaryjoin", before.secondaryjoin, after.secondaryjoin),
        )
        changes.extend(
            (name, _redacted_token(before_value), _redacted_token(after_value))
            for name, before_value, after_value in candidates
            if before_value != after_value
        )
        before_back_populates = (
            escape_plantuml_display_label(before.back_populates)
            if before.back_populates is not None
            else "-"
        )
        after_back_populates = (
            escape_plantuml_display_label(after.back_populates)
            if after.back_populates is not None
            else "-"
        )
        if (
            before.back_populates != after.back_populates
            and before_back_populates == after_back_populates
        ):
            changes.append(
                (
                    "back_populates.presence",
                    "present" if before.back_populates is not None else "absent",
                    "present" if after.back_populates is not None else "absent",
                )
            )
        changes.extend(_collapsed_target_changes("target", before.target, after.target))
        changes.extend(
            _collapsed_optional_target_changes("secondary", before.secondary, after.secondary)
        )
    elif isinstance(before, SqlAlchemyForeignKeyRow) and isinstance(after, SqlAlchemyForeignKeyRow):
        changes.extend(_collapsed_target_changes("target", before.target, after.target))
    elif isinstance(before, SqlAlchemyAssociationTableRow) and isinstance(
        after, SqlAlchemyAssociationTableRow
    ):
        changes.extend(
            _collapsed_target_changes(
                "relationship_target",
                before.relationship_target,
                after.relationship_target,
            )
        )
    if not changes:
        return "", ""
    changes.sort(key=lambda item: item[0].encode("utf-8"))
    before_tokens = " ".join(f"{name}={value}" for name, value, _ in changes)
    after_tokens = " ".join(f"{name}={value}" for name, _, value in changes)
    return f" | {before_tokens}", f" | {after_tokens}"


def _collapsed_target_changes(
    prefix: str,
    before: SqlAlchemyRelationTarget,
    after: SqlAlchemyRelationTarget,
) -> tuple[tuple[str, str, str], ...]:
    if _target_token(before) != _target_token(after):
        return ()
    candidates = (
        ("resolution", before.resolution.value, after.resolution.value),
        ("kind", before.kind.value, after.kind.value),
        ("id", before.id, after.id),
        ("schema_name", before.schema_name, after.schema_name),
        ("table_name", before.table_name, after.table_name),
        ("symbol", before.symbol, after.symbol),
        ("display_name", before.display_name, after.display_name),
    )
    return tuple(
        (f"{prefix}.{name}", _safe_optional_token(before_value), _safe_optional_token(after_value))
        for name, before_value, after_value in candidates
        if before_value != after_value
    )


def _collapsed_optional_target_changes(
    prefix: str,
    before: SqlAlchemyRelationTarget | None,
    after: SqlAlchemyRelationTarget | None,
) -> tuple[tuple[str, str, str], ...]:
    if before is not None and after is not None:
        return _collapsed_target_changes(prefix, before, after)
    before_token = _target_token(before) if before is not None else "-"
    after_token = _target_token(after) if after is not None else "-"
    if before_token != after_token or before is after:
        return ()
    return (
        (
            f"{prefix}.presence",
            "present" if before is not None else "absent",
            "present" if after is not None else "absent",
        ),
    )


def _safe_optional_token(value: str | None) -> str:
    return "-" if value is None else escape_plantuml_display_label(value)


def _safe_bool_token(value: bool | None) -> str:
    if value is None:
        return "null"
    return "true" if value else "false"


def _nullable_marker(value: SqlAlchemyColumnRow) -> str:
    if value.primary_key is True or value.nullable is False:
        return "NN"
    return "NULL" if value.nullable is True else "?NULL"


def _foreign_key_columns(
    snapshot: SqlAlchemySnapshot | None,
    owner_id: str,
) -> frozenset[str]:
    if snapshot is None:
        return frozenset()
    return frozenset(
        column
        for member in snapshot.members
        if member.owner_id == owner_id and isinstance(member, SqlAlchemyForeignKeyRow)
        for column in member.local_columns
    )


def _diff_er_relations(
    snapshot: SqlAlchemySnapshot | None,
) -> dict[str, tuple[SqlAlchemyErRelation, dict[str, SqlAlchemyRow]]]:
    if snapshot is None:
        return {}
    members = {item.id: item for item in snapshot.members}
    return {item.relation.id: (item, members) for item in build_er_view(snapshot).relations}


def _render_view(view: SqlAlchemyErView) -> bytes:
    snapshot = view.snapshot
    lines = list(_HEADER)
    for table in snapshot.entities:
        lines.append(
            f'entity "{_render_table_display(table.schema_name, table.name)}" '
            f"as {_table_alias(table)} {{"
        )
        owner_members = tuple(member for member in snapshot.members if member.owner_id == table.id)
        foreign_key_columns = _foreign_key_columns(snapshot, table.id)
        saw_constraint = False
        for member in owner_members:
            if not saw_constraint and not isinstance(member, SqlAlchemyColumnRow):
                lines.append("  --")
                saw_constraint = True
            lines.append(_row_line(member, foreign_key_columns=foreign_key_columns))
        lines.append("}")
    members_by_id = {member.id: member for member in snapshot.members}
    for item in view.relations:
        line = _relation_line(item, members_by_id)
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


def _table_alias(table: SqlAlchemyTable) -> str:
    return _table_alias_from_id(table.id)


def _table_alias_from_id(table_id: str) -> str:
    return f"T_{table_id.removeprefix('sqlalchemy:table:')}"


def _name_token(name: str | None) -> str:
    return escape_plantuml_display_label(name) if name is not None else "<unnamed>"


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
    return escape_plantuml_display_label(value.symbol)


def _columns_token(values: tuple[str, ...]) -> str:
    return ",".join(escape_plantuml_display_label(value) for value in values)


def _short_type_name(value: SqlAlchemyColumnRow) -> str | None:
    if value.type.name is None:
        return None
    return value.type.name.rsplit(".", 1)[-1]


def _column_line(value: SqlAlchemyColumnRow, foreign_key_columns: frozenset[str]) -> str:
    assert value.name is not None
    markers: list[str] = []
    if value.primary_key is True:
        markers.append("PK")
    if value.name in foreign_key_columns:
        markers.append("FK")
    if value.unique is True:
        markers.append("UQ")
    if value.index is True:
        markers.append("IX")
    mandatory = value.primary_key is True or value.nullable is False
    if mandatory:
        markers.append("NN")
    elif value.nullable is True:
        markers.append("NULL")
    else:
        markers.append("?NULL")
    type_name = _short_type_name(value)
    display_type = value.type.category.value
    if type_name is not None and type_name.lower() != display_type.lower():
        display_type = f"{display_type} ({escape_plantuml_display_label(type_name)})"
    stereotype = f" <<{', '.join(markers)}>>" if markers else ""
    prefix = "* " if mandatory else ""
    return f"  {prefix}{escape_plantuml_display_label(value.name)} : {display_type}{stereotype}"


def _row_line(value: SqlAlchemyRow, *, foreign_key_columns: frozenset[str] = frozenset()) -> str:
    if isinstance(value, SqlAlchemyColumnRow):
        return _column_line(value, foreign_key_columns)
    if isinstance(value, SqlAlchemyPrimaryKeyRow):
        return f"  primary_key {_name_token(value.name)} columns=({_columns_token(value.columns)})"
    if isinstance(value, SqlAlchemyUniqueRow):
        return f"  unique {_name_token(value.name)} columns=({_columns_token(value.columns)})"
    if isinstance(value, SqlAlchemyCheckRow):
        return f"  check {_name_token(value.name)} expression={_redacted_token(value.expression)}"
    if isinstance(value, SqlAlchemyIndexRow):
        terms = ",".join(
            (
                f"column:{escape_plantuml_display_label(term.column_name)}"
                if term.kind is IndexTermKind.COLUMN and term.column_name is not None
                else _redacted_token(term.expression)
            )
            for term in value.terms
        )
        return f"  index {_name_token(value.name)} unique={_bool_token(value.unique)} terms={terms}"
    if isinstance(value, SqlAlchemyForeignKeyRow):
        return (
            f"  foreign_key {_name_token(value.name)} "
            f"local=({_columns_token(value.local_columns)}) "
            f"references={_target_token(value.target)}({_columns_token(value.target_columns)}) "
            f"ondelete={_redacted_token(value.ondelete)} onupdate={_redacted_token(value.onupdate)}"
        )
    if isinstance(value, SqlAlchemyRelationshipRow):
        secondary = _target_token(value.secondary) if value.secondary is not None else "-"
        back_populates = (
            escape_plantuml_display_label(value.back_populates)
            if value.back_populates is not None
            else "-"
        )
        return (
            f"  relationship {_name_token(value.name)} : {value.cardinality.value} "
            f"target={_target_token(value.target)} uselist={_bool_token(value.uselist)} "
            f"back_populates={back_populates} secondary={secondary}"
        )
    if isinstance(value, SqlAlchemyInheritanceRow):
        return f"  inheritance target={_target_token(value.target)}"
    if isinstance(value, SqlAlchemyAssociationTableRow):
        return (
            f"  association_table {_name_token(value.name)} "
            f"source={_target_token(value.source_table)} "
            f"target={_target_token(value.relationship_target)}"
        )
    raise TypeError("unknown SQLAlchemy row DTO")


_LEFT_ENDPOINT = {
    SqlAlchemyErMultiplicity.EXACTLY_ONE: "||",
    SqlAlchemyErMultiplicity.ZERO_OR_ONE: "|o",
    SqlAlchemyErMultiplicity.ZERO_OR_MANY: "}o",
    SqlAlchemyErMultiplicity.ONE_OR_MANY: "}|",
}
_RIGHT_ENDPOINT = {
    SqlAlchemyErMultiplicity.EXACTLY_ONE: "||",
    SqlAlchemyErMultiplicity.ZERO_OR_ONE: "o|",
    SqlAlchemyErMultiplicity.ZERO_OR_MANY: "o{",
    SqlAlchemyErMultiplicity.ONE_OR_MANY: "|{",
}


def _multiplicity_label(value: SqlAlchemyErMultiplicity | None) -> str:
    return {
        SqlAlchemyErMultiplicity.EXACTLY_ONE: "1",
        SqlAlchemyErMultiplicity.ZERO_OR_ONE: "0..1",
        SqlAlchemyErMultiplicity.ZERO_OR_MANY: "0..N",
        SqlAlchemyErMultiplicity.ONE_OR_MANY: "1..N",
        SqlAlchemyErMultiplicity.UNKNOWN: "?",
        None: "?",
    }[value]


def _relation_line(
    value: SqlAlchemyErRelation,
    members_by_id: dict[str, SqlAlchemyRow],
) -> str | None:
    relation = value.relation
    if relation.target.resolution is not SqlAlchemyTargetResolution.INTERNAL:
        return None
    assert relation.target.id is not None
    source = _table_alias_from_id(relation.source_id)
    target = _table_alias_from_id(relation.target.id)
    if relation.kind is SqlAlchemyRelationKind.INHERITANCE:
        return f"{source} --|> {target} : inheritance"
    assert relation.via_member_id is not None
    member = members_by_id[relation.via_member_id]
    if relation.kind is SqlAlchemyRelationKind.FOREIGN_KEY:
        if not isinstance(member, SqlAlchemyForeignKeyRow):
            raise ValueError("foreign-key relation member is invalid")
        label = f"foreign_key {_name_token(member.name)}"
        style = "--"
    elif relation.kind is SqlAlchemyRelationKind.RELATIONSHIP:
        if not isinstance(member, SqlAlchemyRelationshipRow):
            raise ValueError("relationship relation member is invalid")
        label = f"relationship {_name_token(value.role or member.name)}"
        style = ".."
    else:
        if not isinstance(member, SqlAlchemyAssociationTableRow):
            raise ValueError("association relation member is invalid")
        return f"{source} .. {target} : association {_name_token(member.name)} [source=? target=?]"

    left = (
        _LEFT_ENDPOINT.get(value.source_multiplicity)
        if value.source_multiplicity is not None
        else None
    )
    right = (
        _RIGHT_ENDPOINT.get(value.target_multiplicity)
        if value.target_multiplicity is not None
        else None
    )
    if left is not None and right is not None:
        return f"{source} {left}{style}{right} {target} : {label}"
    return (
        f"{source} {style} {target} : {label} "
        f"[source={_multiplicity_label(value.source_multiplicity)} "
        f"target={_multiplicity_label(value.target_multiplicity)}]"
    )
