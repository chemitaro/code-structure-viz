import hashlib
from pathlib import Path, PurePosixPath

from code_structure_viz.adapters.sqlalchemy.analyzer import (
    SqlAlchemyAnalysisResult,
    SqlAlchemyApplicability,
    SqlAlchemySnapshotAnalyzer,
)
from code_structure_viz.adapters.sqlalchemy.model import (
    SqlAlchemyAssociationTableRow,
    SqlAlchemyRelationKind,
    SqlAlchemyRelationshipRow,
    SqlAlchemyRowKind,
)
from code_structure_viz.core.config import PythonConfig
from code_structure_viz.source.python_modules import PythonSourceIndex
from code_structure_viz.source.source_view import SourceFile, SourceFileKind, SourceView


def _analyze_fixture(case: str) -> SqlAlchemyAnalysisResult:
    fixture = Path(__file__).parents[2] / "fixtures" / "sqlalchemy_snapshot" / case / "models.py"
    content = fixture.read_bytes()
    source = SourceFile(
        PurePosixPath("src/models.py"),
        SourceFileKind.REGULAR,
        None,
        len(content),
        hashlib.sha256(content).hexdigest(),
        content,
    )
    return SqlAlchemySnapshotAnalyzer().analyze(
        PythonSourceIndex.build(
            SourceView(None, (source,), (), "0" * 64),
            PythonConfig(("src",), ("**/*.py",), ()),
        )
    )


def test_foundation_fixture_is_analyzed_without_import_or_side_effect(tmp_path: Path) -> None:
    fixture = (
        Path(__file__).parents[2]
        / "fixtures"
        / "sqlalchemy_snapshot"
        / "analyzer_foundation"
        / "models.py"
    )
    content = fixture.read_bytes()
    sentinel = tmp_path / "target-imported"
    assert not sentinel.exists()
    source = SourceFile(
        PurePosixPath("src/models.py"),
        SourceFileKind.REGULAR,
        None,
        len(content),
        hashlib.sha256(content).hexdigest(),
        content,
    )
    view = SourceView(None, (source,), (), "0" * 64)

    result = SqlAlchemySnapshotAnalyzer().analyze(
        PythonSourceIndex.build(
            view,
            PythonConfig(("src",), ("**/*.py",), ()),
        )
    )

    assert result.applicability is SqlAlchemyApplicability.PRESENT
    assert [table.name for table in result.snapshot.entities] == ["audit_events"]
    assert {row.kind for row in result.snapshot.members} >= {
        SqlAlchemyRowKind.COLUMN,
        SqlAlchemyRowKind.PRIMARY_KEY,
        SqlAlchemyRowKind.CHECK,
    }
    assert not sentinel.exists()
    assert "do-not-publish-this-secret" not in repr(result.snapshot)


def test_relationship_inheritance_and_association_fixture_builds_safe_graph() -> None:
    result = _analyze_fixture("relationship_semantics")

    assert result.applicability is SqlAlchemyApplicability.PRESENT
    assert [table.name for table in result.snapshot.entities] == [
        "admins",
        "groups",
        "membership",
        "users",
    ]
    assert (
        len([row for row in result.snapshot.members if isinstance(row, SqlAlchemyRelationshipRow)])
        == 2
    )
    assert (
        len(
            [
                row
                for row in result.snapshot.members
                if isinstance(row, SqlAlchemyAssociationTableRow)
            ]
        )
        == 1
    )
    assert {relation.kind for relation in result.snapshot.relations} >= {
        SqlAlchemyRelationKind.RELATIONSHIP,
        SqlAlchemyRelationKind.INHERITANCE,
        SqlAlchemyRelationKind.ASSOCIATION,
    }
    assert result.snapshot.partial_safe is False
    assert "this fixture must never execute" not in repr(result.snapshot)


def test_lossy_fixtures_keep_only_safe_column_and_four_occurrence_diagnostics() -> None:
    for case in ("lossy_identity_conflict", "lossy_same_line_siblings"):
        result = _analyze_fixture(case)
        occurrences = [
            item for item in result.snapshot.diagnostics if item.code.value == "CSV-SA-009"
        ]

        assert [row.kind for row in result.snapshot.members] == [SqlAlchemyRowKind.COLUMN]
        assert len(occurrences) == 4
        assert len({item.symbol for item in occurrences}) == 4
        assert result.snapshot.coverage.unknown_declarations == 4
        assert result.snapshot.partial_safe is True
        assert all(not hasattr(item, "start_utf8_byte_column") for item in occurrences)
