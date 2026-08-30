import hashlib
from dataclasses import fields

import pytest

from code_structure_viz.adapters.sqlalchemy.model import (
    IndexTermKind,
    RedactedExpression,
    RedactedExpressionCategory,
    SqlAlchemyAssociationTableRow,
    SqlAlchemyCardinality,
    SqlAlchemyCheckRow,
    SqlAlchemyColumnRow,
    SqlAlchemyCoverage,
    SqlAlchemyCoverageFrontier,
    SqlAlchemyFrontierDirection,
    SqlAlchemyFrontierKind,
    SqlAlchemyFrontierReason,
    SqlAlchemyIndexRow,
    SqlAlchemyIndexTerm,
    SqlAlchemyInternalDeclarationSpan,
    SqlAlchemyMappingSource,
    SqlAlchemyMappingSourceKind,
    SqlAlchemyRedactionSummary,
    SqlAlchemyRelation,
    SqlAlchemyRelationKind,
    SqlAlchemyRelationshipRow,
    SqlAlchemyRelationTarget,
    SqlAlchemyRowEvidence,
    SqlAlchemyRowKind,
    SqlAlchemySnapshot,
    SqlAlchemySourceLocation,
    SqlAlchemySourceRange,
    SqlAlchemyTable,
    SqlAlchemyTargetKind,
    SqlAlchemyTargetResolution,
    SqlAlchemyTypeCategory,
    SqlAlchemyTypeDescriptor,
    canonicalize_row_evidence,
    row_sort_key,
    safe_structural_string,
    sqlalchemy_occurrence_diagnostic_symbol,
    sqlalchemy_relation_id,
    sqlalchemy_row_id,
    sqlalchemy_table_id,
    table_sort_key,
)
from code_structure_viz.semantic.canonical_json import encode_canonical_json


def _location(path: str = "models.py", line: int = 1) -> SqlAlchemySourceLocation:
    return SqlAlchemySourceLocation(path, SqlAlchemySourceRange(line, line))


def _span(
    line: int = 1, start_column: int = 0, end_column: int = 10
) -> SqlAlchemyInternalDeclarationSpan:
    return SqlAlchemyInternalDeclarationSpan(line, start_column, line, end_column)


def _table(
    *,
    schema_name: str | None = None,
    name: str = "users",
    path: str = "models.py",
    line: int = 1,
) -> SqlAlchemyTable:
    source = SqlAlchemyMappingSource(
        SqlAlchemyMappingSourceKind.DECLARATIVE_CLASS,
        "models",
        "models.User",
        _location(path, line),
    )
    return SqlAlchemyTable.create(
        schema_name=schema_name,
        name=name,
        mapping_sources=(source,),
    )


def _integer_type(*, parameters: RedactedExpression | None = None) -> SqlAlchemyTypeDescriptor:
    return SqlAlchemyTypeDescriptor(
        SqlAlchemyTypeCategory.INTEGER,
        "sqlalchemy.Integer",
        parameters or RedactedExpression.absent(),
    )


def test_closed_enum_vocabularies_and_public_source_shape_are_exact() -> None:
    assert tuple(value.value for value in SqlAlchemyRowKind) == (
        "column",
        "primary_key",
        "unique",
        "check",
        "index",
        "foreign_key",
        "relationship",
        "inheritance",
        "association_table",
    )
    assert tuple(value.value for value in SqlAlchemyRelationKind) == (
        "foreign_key",
        "relationship",
        "inheritance",
        "association",
    )
    assert tuple(value.value for value in SqlAlchemyTargetKind) == (
        "table",
        "mapped_class",
        "unknown",
    )
    assert tuple(value.value for value in SqlAlchemyTargetResolution) == (
        "internal",
        "external",
        "unknown",
    )
    assert tuple(value.value for value in SqlAlchemyCardinality) == (
        "scalar",
        "many",
        "unknown",
    )
    assert tuple(value.value for value in IndexTermKind) == ("column", "expression")
    assert {field.name for field in fields(SqlAlchemySourceLocation)} == {"path", "range"}
    assert all("column" not in field.name for field in fields(SqlAlchemySourceLocation))


def test_table_identity_uses_canonical_json_with_final_lf_and_ignores_provenance() -> None:
    expected = hashlib.sha256(
        encode_canonical_json(
            {
                "schema": "code-structure-viz.sqlalchemy-table-id/v1",
                "schema_name": None,
                "table_name": "users",
            }
        )
    ).hexdigest()

    first = _table(path="z.py", line=9)
    second = _table(path="a.py", line=2)

    assert first.id == second.id == f"sqlalchemy:table:{expected}"
    assert first.display_name == "<default>.users"
    assert _table(schema_name="auth").display_name == "auth.users"


@pytest.mark.parametrize(
    "value",
    ("", "a/b", r"a\b", "/tmp/table", "../table", "file://table", "C:table", "bad\nname"),
)
def test_structural_strings_reject_path_uri_and_control_spellings(value: str) -> None:
    with pytest.raises(ValueError):
        safe_structural_string(value)


def test_redacted_expression_and_index_term_invariants_do_not_have_raw_value_fields() -> None:
    absent = RedactedExpression.absent()
    redacted = RedactedExpression.present_as(RedactedExpressionCategory.SQL_EXPRESSION)

    assert absent == RedactedExpression(False, RedactedExpressionCategory.ABSENT, False)
    assert redacted == RedactedExpression(True, RedactedExpressionCategory.SQL_EXPRESSION, True)
    assert {field.name for field in fields(RedactedExpression)} == {
        "present",
        "category",
        "redacted",
    }
    assert SqlAlchemyIndexTerm.column("email").expression == absent
    assert (
        SqlAlchemyIndexTerm.redacted_expression(RedactedExpressionCategory.SQL_EXPRESSION).kind
        is IndexTermKind.EXPRESSION
    )
    with pytest.raises(ValueError):
        RedactedExpression(True, RedactedExpressionCategory.ABSENT, True)


def test_row_and_relation_id_preimages_exclude_source_and_display_fields() -> None:
    table = _table()
    first = SqlAlchemyColumnRow.create(
        owner_id=table.id,
        name="id",
        source=_location("z.py", 9),
        type=_integer_type(),
        primary_key=True,
    )
    second = SqlAlchemyColumnRow.create(
        owner_id=table.id,
        name="id",
        source=_location("a.py", 2),
        type=_integer_type(),
        primary_key=False,
    )
    expected_row = sqlalchemy_row_id(
        table.id,
        SqlAlchemyRowKind.COLUMN,
        {"name": "id"},
    )
    assert first.id == second.id == expected_row

    target_table = _table(name="accounts")
    target = SqlAlchemyRelationTarget.internal_table(target_table)
    relation_id = sqlalchemy_relation_id(
        kind=SqlAlchemyRelationKind.FOREIGN_KEY,
        source_id=table.id,
        target=target,
        via_member_id=first.id,
        role=None,
    )
    relation = SqlAlchemyRelation.create(
        kind=SqlAlchemyRelationKind.FOREIGN_KEY,
        source_id=table.id,
        target=target,
        via_member_id=first.id,
        role=None,
        source=first.source,
    )
    assert relation.id == relation_id


@pytest.mark.parametrize(
    "reference",
    (
        "/private/secret.py",
        "../secret.py",
        "src/../secret.py",
        "https://example.invalid/secret.py",
        "urn:private:secret.py",
        "C:/secret.py",
        r"src\secret.py",
        "raw secret",
        "sqlalchemy:binding:models",
        "row\x00secret",
    ),
)
def test_frontier_reference_rejects_private_path_and_raw_spellings(reference: str) -> None:
    with pytest.raises(ValueError, match="frontier reference"):
        SqlAlchemyCoverageFrontier(
            SqlAlchemyFrontierDirection.FAILURE,
            SqlAlchemyFrontierKind.ROW,
            reference,
            SqlAlchemyFrontierReason.UNSUPPORTED_PATTERN,
        )


def test_frontier_reference_accepts_closed_path_symbol_and_semantic_id_shapes() -> None:
    table = _table()
    column = SqlAlchemyColumnRow.create(
        owner_id=table.id,
        name="id",
        source=_location(),
        type=_integer_type(),
    )
    occurrence = sqlalchemy_occurrence_diagnostic_symbol(
        table.id,
        SqlAlchemyRowKind.COLUMN,
        "models.py",
        _span(),
    )

    for reference in (
        "models.py",
        "src/models.py",
        "models.User",
        "module:models",
        "class:models.User",
        table.id,
        column.id,
        occurrence,
    ):
        assert (
            SqlAlchemyCoverageFrontier(
                SqlAlchemyFrontierDirection.FAILURE,
                SqlAlchemyFrontierKind.ROW,
                reference,
                SqlAlchemyFrontierReason.UNSUPPORTED_PATTERN,
            ).reference
            == reference
        )


def test_relation_kind_matrix_requires_internal_targets_and_exact_role_shape() -> None:
    source = _table(name="source")
    target = _table(name="target")
    column = SqlAlchemyColumnRow.create(
        owner_id=source.id,
        name="target_id",
        source=_location(),
        type=_integer_type(),
    )
    internal = SqlAlchemyRelationTarget.internal_table(target)

    with pytest.raises(ValueError, match="internal target"):
        SqlAlchemyRelation.create(
            kind=SqlAlchemyRelationKind.FOREIGN_KEY,
            source_id=source.id,
            target=SqlAlchemyRelationTarget.external_table(
                schema_name=None,
                table_name="external",
            ),
            via_member_id=column.id,
            role=None,
            source=column.source,
        )
    with pytest.raises(ValueError, match="role"):
        SqlAlchemyRelation.create(
            kind=SqlAlchemyRelationKind.FOREIGN_KEY,
            source_id=source.id,
            target=internal,
            via_member_id=column.id,
            role="target",
            source=column.source,
        )
    with pytest.raises(ValueError, match="role"):
        SqlAlchemyRelation.create(
            kind=SqlAlchemyRelationKind.RELATIONSHIP,
            source_id=source.id,
            target=internal,
            via_member_id=column.id,
            role=None,
            source=column.source,
        )


def test_occurrence_symbol_uses_full_internal_span_and_distinguishes_same_line_siblings() -> None:
    table = _table()
    first_span = _span(42, 12, 47)
    second_span = _span(42, 49, 84)
    first = sqlalchemy_occurrence_diagnostic_symbol(
        table.id, SqlAlchemyRowKind.CHECK, "models.py", first_span
    )
    repeated = sqlalchemy_occurrence_diagnostic_symbol(
        table.id, SqlAlchemyRowKind.CHECK, "models.py", first_span
    )
    sibling = sqlalchemy_occurrence_diagnostic_symbol(
        table.id, SqlAlchemyRowKind.CHECK, "models.py", second_span
    )

    expected = hashlib.sha256(
        encode_canonical_json(
            {
                "schema": "code-structure-viz.sqlalchemy-occurrence-diagnostic-symbol/v1",
                "owner_id": table.id,
                "kind": "check",
                "path": "models.py",
                "span": {
                    "start_line": 42,
                    "start_utf8_byte_column": 12,
                    "end_line": 42,
                    "end_utf8_byte_column": 47,
                },
            }
        )
    ).hexdigest()
    assert first == repeated == f"sqlalchemy:occurrence:{expected}"
    assert sibling != first
    assert len(first.removeprefix("sqlalchemy:occurrence:")) == 64


def test_lossy_conflicts_exclude_rows_and_keep_four_occurrence_diagnostics() -> None:
    table = _table()
    source = _location("models.py", 7)
    expression = RedactedExpression.present_as(RedactedExpressionCategory.SQL_EXPRESSION)
    checks = (
        SqlAlchemyCheckRow.create(
            owner_id=table.id,
            name=None,
            source=source,
            expression=expression,
        ),
        SqlAlchemyCheckRow.create(
            owner_id=table.id,
            name=None,
            source=source,
            expression=expression,
        ),
    )
    expression_term = SqlAlchemyIndexTerm.redacted_expression(
        RedactedExpressionCategory.SQL_EXPRESSION
    )
    indexes = (
        SqlAlchemyIndexRow.create(
            owner_id=table.id,
            name=None,
            source=source,
            unique=False,
            terms=(expression_term,),
        ),
        SqlAlchemyIndexRow.create(
            owner_id=table.id,
            name=None,
            source=source,
            unique=False,
            terms=(expression_term,),
        ),
    )
    column = SqlAlchemyColumnRow.create(
        owner_id=table.id,
        name="id",
        source=source,
        type=_integer_type(),
    )
    evidence = (
        SqlAlchemyRowEvidence(column, _span(7, 0, 10)),
        SqlAlchemyRowEvidence(checks[0], _span(7, 12, 32)),
        SqlAlchemyRowEvidence(checks[0], _span(7, 12, 32)),
        SqlAlchemyRowEvidence(checks[1], _span(7, 34, 54)),
        SqlAlchemyRowEvidence(indexes[0], _span(7, 56, 76)),
        SqlAlchemyRowEvidence(indexes[1], _span(7, 78, 98)),
    )

    rows, diagnostics = canonicalize_row_evidence(evidence)

    assert rows == (column,)
    assert [item.code.value for item in diagnostics] == ["CSV-SA-009"] * 4
    assert len({item.symbol for item in diagnostics}) == 4
    assert all(item.line == 7 for item in diagnostics)


def test_non_lossy_exact_duplicates_choose_the_smallest_source_without_incompleteness() -> None:
    table = _table()
    later = SqlAlchemyColumnRow.create(
        owner_id=table.id,
        name="id",
        source=_location("z.py", 9),
        type=_integer_type(),
    )
    earlier = SqlAlchemyColumnRow.create(
        owner_id=table.id,
        name="id",
        source=_location("a.py", 2),
        type=_integer_type(),
    )

    rows, diagnostics = canonicalize_row_evidence(
        (
            SqlAlchemyRowEvidence(later, _span(9, 0, 5)),
            SqlAlchemyRowEvidence(earlier, _span(2, 0, 5)),
        )
    )

    assert rows == (earlier,)
    assert diagnostics == ()
    assert rows == tuple(sorted(rows, key=row_sort_key))


def test_snapshot_requires_redaction_count_from_final_selected_rows() -> None:
    table = _table()
    parameters = RedactedExpression.present_as(RedactedExpressionCategory.LITERAL)
    column = SqlAlchemyColumnRow.create(
        owner_id=table.id,
        name="name",
        source=_location(),
        type=SqlAlchemyTypeDescriptor(
            SqlAlchemyTypeCategory.STRING,
            "sqlalchemy.String",
            parameters,
        ),
    )
    coverage = SqlAlchemyCoverage(
        candidate_files=1,
        parsed_files=1,
        failed_files=(),
        evidence_files=("models.py",),
        selected_modules=("models",),
        mapped_classes=1,
        association_tables=0,
        selected_entities=1,
        unknown_declarations=0,
        frontier=(),
        redaction=SqlAlchemyRedactionSummary.create(1),
    )

    snapshot = SqlAlchemySnapshot((table,), (column,), (), coverage, (), False)

    assert snapshot.coverage.redaction.redacted_values == 1
    with pytest.raises(ValueError, match="redaction coverage"):
        SqlAlchemySnapshot(
            (table,),
            (column,),
            (),
            SqlAlchemyCoverage(
                candidate_files=1,
                parsed_files=1,
                failed_files=(),
                evidence_files=("models.py",),
                selected_modules=("models",),
                mapped_classes=1,
                association_tables=0,
                selected_entities=1,
                unknown_declarations=0,
                frontier=(),
                redaction=SqlAlchemyRedactionSummary.create(0),
            ),
            (),
            False,
        )


def test_snapshot_rejects_unknown_complete_payload_and_failure_frontier() -> None:
    table = _table()
    unknown = SqlAlchemyColumnRow.create(
        owner_id=table.id,
        name="dynamic",
        source=_location(),
        type=SqlAlchemyTypeDescriptor(
            SqlAlchemyTypeCategory.UNKNOWN,
            None,
            RedactedExpression.absent(),
        ),
    )
    base_coverage = SqlAlchemyCoverage(
        candidate_files=1,
        parsed_files=1,
        failed_files=(),
        evidence_files=("models.py",),
        selected_modules=("models",),
        mapped_classes=1,
        association_tables=0,
        selected_entities=1,
        unknown_declarations=0,
        frontier=(),
        redaction=SqlAlchemyRedactionSummary.create(0),
    )

    with pytest.raises(ValueError, match="unknown SQLAlchemy value"):
        SqlAlchemySnapshot((table,), (unknown,), (), base_coverage, (), False)

    failure = SqlAlchemyCoverageFrontier(
        SqlAlchemyFrontierDirection.FAILURE,
        SqlAlchemyFrontierKind.TABLE,
        table.id,
        SqlAlchemyFrontierReason.UNSUPPORTED_PATTERN,
    )
    with pytest.raises(ValueError, match="failure frontier"):
        SqlAlchemySnapshot(
            (table,),
            (),
            (),
            SqlAlchemyCoverage(
                candidate_files=1,
                parsed_files=1,
                failed_files=(),
                evidence_files=("models.py",),
                selected_modules=("models",),
                mapped_classes=1,
                association_tables=0,
                selected_entities=1,
                unknown_declarations=0,
                frontier=(failure,),
                redaction=SqlAlchemyRedactionSummary.create(0),
            ),
            (),
            False,
        )

    depth = SqlAlchemyCoverageFrontier(
        SqlAlchemyFrontierDirection.UPSTREAM,
        SqlAlchemyFrontierKind.TABLE,
        table.id,
        SqlAlchemyFrontierReason.DEPTH_LIMIT,
    )
    complete = SqlAlchemySnapshot(
        (table,),
        (),
        (),
        SqlAlchemyCoverage(
            candidate_files=1,
            parsed_files=1,
            failed_files=(),
            evidence_files=("models.py",),
            selected_modules=("models",),
            mapped_classes=1,
            association_tables=0,
            selected_entities=1,
            unknown_declarations=0,
            frontier=(depth,),
            redaction=SqlAlchemyRedactionSummary.create(0),
        ),
        (),
        False,
    )
    assert complete.coverage.frontier == (depth,)

    unsupported = SqlAlchemyCoverageFrontier(
        SqlAlchemyFrontierDirection.UPSTREAM,
        SqlAlchemyFrontierKind.TABLE,
        table.id,
        SqlAlchemyFrontierReason.UNSUPPORTED_PATTERN,
    )
    with pytest.raises(ValueError, match="depth-limit frontier"):
        SqlAlchemySnapshot(
            (table,),
            (),
            (),
            SqlAlchemyCoverage(
                candidate_files=1,
                parsed_files=1,
                failed_files=(),
                evidence_files=("models.py",),
                selected_modules=("models",),
                mapped_classes=1,
                association_tables=0,
                selected_entities=1,
                unknown_declarations=0,
                frontier=(unsupported,),
                redaction=SqlAlchemyRedactionSummary.create(0),
            ),
            (),
            False,
        )


@pytest.mark.parametrize(
    "direction",
    (
        SqlAlchemyFrontierDirection.UPSTREAM,
        SqlAlchemyFrontierDirection.DOWNSTREAM,
    ),
)
def test_complete_snapshot_rejects_non_depth_directional_frontier(
    direction: SqlAlchemyFrontierDirection,
) -> None:
    table = _table()
    frontier = SqlAlchemyCoverageFrontier(
        direction,
        SqlAlchemyFrontierKind.TABLE,
        table.id,
        SqlAlchemyFrontierReason.UNRESOLVED_REFERENCE,
    )

    with pytest.raises(ValueError, match="depth-limit frontier"):
        SqlAlchemySnapshot(
            (table,),
            (),
            (),
            SqlAlchemyCoverage(
                candidate_files=1,
                parsed_files=1,
                failed_files=(),
                evidence_files=("models.py",),
                selected_modules=("models",),
                mapped_classes=1,
                association_tables=0,
                selected_entities=1,
                unknown_declarations=0,
                frontier=(frontier,),
                redaction=SqlAlchemyRedactionSummary.create(0),
            ),
            (),
            False,
        )


def test_snapshot_rejects_via_member_kind_and_role_mismatch() -> None:
    source = _table(name="source")
    target = _table(name="target")
    target_descriptor = SqlAlchemyRelationTarget.internal_table(target)
    column = SqlAlchemyColumnRow.create(
        owner_id=source.id,
        name="target_id",
        source=_location(),
        type=_integer_type(),
    )
    relationship = SqlAlchemyRelationshipRow.create(
        owner_id=source.id,
        name="target",
        source=_location(line=2),
        target=target_descriptor,
        cardinality=SqlAlchemyCardinality.SCALAR,
        uselist=False,
        back_populates=None,
        secondary=None,
    )
    coverage = SqlAlchemyCoverage(
        candidate_files=1,
        parsed_files=1,
        failed_files=(),
        evidence_files=("models.py",),
        selected_modules=("models",),
        mapped_classes=2,
        association_tables=0,
        selected_entities=2,
        unknown_declarations=0,
        frontier=(),
        redaction=SqlAlchemyRedactionSummary.create(0),
    )
    wrong_kind = SqlAlchemyRelation.create(
        kind=SqlAlchemyRelationKind.FOREIGN_KEY,
        source_id=source.id,
        target=target_descriptor,
        via_member_id=column.id,
        role=None,
        source=column.source,
    )
    wrong_role = SqlAlchemyRelation.create(
        kind=SqlAlchemyRelationKind.RELATIONSHIP,
        source_id=source.id,
        target=target_descriptor,
        via_member_id=relationship.id,
        role="other",
        source=relationship.source,
    )

    with pytest.raises(ValueError, match="foreign-key relation member"):
        SqlAlchemySnapshot(
            tuple(sorted((source, target), key=table_sort_key)),
            tuple(sorted((column, relationship), key=row_sort_key)),
            (wrong_kind,),
            coverage,
            (),
            False,
        )
    with pytest.raises(ValueError, match="relationship relation member"):
        SqlAlchemySnapshot(
            tuple(sorted((source, target), key=table_sort_key)),
            tuple(sorted((column, relationship), key=row_sort_key)),
            (wrong_role,),
            coverage,
            (),
            False,
        )


def test_snapshot_rejects_association_marker_role_mismatch() -> None:
    source = _table(name="source")
    target = _table(name="target")
    secondary = _table(name="secondary")
    relationship = SqlAlchemyRelationshipRow.create(
        owner_id=source.id,
        name="targets",
        source=_location(),
        target=SqlAlchemyRelationTarget.internal_table(target),
        cardinality=SqlAlchemyCardinality.MANY,
        uselist=True,
        back_populates=None,
        secondary=SqlAlchemyRelationTarget.internal_table(secondary),
    )
    marker = SqlAlchemyAssociationTableRow.create(
        owner_id=secondary.id,
        name="targets",
        source=_location(line=2),
        source_table=SqlAlchemyRelationTarget.internal_table(source),
        relationship_target=SqlAlchemyRelationTarget.internal_table(target),
        relationship_member_id=relationship.id,
    )
    relation = SqlAlchemyRelation.create(
        kind=SqlAlchemyRelationKind.ASSOCIATION,
        source_id=source.id,
        target=SqlAlchemyRelationTarget.internal_table(secondary),
        via_member_id=marker.id,
        role="other",
        source=marker.source,
    )
    coverage = SqlAlchemyCoverage(
        candidate_files=1,
        parsed_files=1,
        failed_files=(),
        evidence_files=("models.py",),
        selected_modules=("models",),
        mapped_classes=3,
        association_tables=1,
        selected_entities=3,
        unknown_declarations=0,
        frontier=(),
        redaction=SqlAlchemyRedactionSummary.create(0),
    )

    with pytest.raises(ValueError, match="association relation member"):
        SqlAlchemySnapshot(
            tuple(sorted((source, target, secondary), key=table_sort_key)),
            tuple(sorted((relationship, marker), key=row_sort_key)),
            (relation,),
            coverage,
            (),
            False,
        )


def test_table_id_factory_normalizes_nfc() -> None:
    assert sqlalchemy_table_id(None, "e\N{COMBINING ACUTE ACCENT}") == sqlalchemy_table_id(
        None, "\N{LATIN SMALL LETTER E WITH ACUTE}"
    )
