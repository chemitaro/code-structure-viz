import hashlib
from pathlib import Path, PurePosixPath

from code_structure_viz.adapters.sqlalchemy.analyzer import (
    SqlAlchemyApplicability,
    SqlAlchemySnapshotAnalyzer,
)
from code_structure_viz.adapters.sqlalchemy.model import SqlAlchemyRowKind
from code_structure_viz.core.config import PythonConfig
from code_structure_viz.source.python_modules import PythonSourceIndex
from code_structure_viz.source.source_view import SourceFile, SourceFileKind, SourceView


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
