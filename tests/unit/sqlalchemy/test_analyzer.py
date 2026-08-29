import hashlib
from pathlib import PurePosixPath

from code_structure_viz.adapters.sqlalchemy.analyzer import (
    SqlAlchemyAnalysisResult,
    SqlAlchemyApplicability,
    SqlAlchemySnapshotAnalyzer,
)
from code_structure_viz.adapters.sqlalchemy.model import (
    SqlAlchemyColumnRow,
    SqlAlchemyMappingKind,
    SqlAlchemyRowKind,
    SqlAlchemyTypeCategory,
)
from code_structure_viz.core.config import PythonConfig
from code_structure_viz.source.python_modules import PythonSourceIndex
from code_structure_viz.source.source_view import SourceFile, SourceFileKind, SourceView


def _analyze(files: dict[str, bytes]) -> SqlAlchemyAnalysisResult:
    sources = tuple(
        SourceFile(
            PurePosixPath(path),
            SourceFileKind.REGULAR,
            None,
            len(content),
            hashlib.sha256(content).hexdigest(),
            content,
        )
        for path, content in files.items()
    )
    view = SourceView(None, sources, (), "0" * 64)
    index = PythonSourceIndex.build(
        view,
        PythonConfig(("src",), ("**/*.py",), ()),
    )
    return SqlAlchemySnapshotAnalyzer().analyze(index)


def test_modern_declarative_columns_and_basic_constraints_are_static() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        CheckConstraint("secret_balance > 0"),
        Index("ix_users_email", "email"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, default="secret")
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
"""
        }
    )

    assert result.applicability is SqlAlchemyApplicability.PRESENT
    assert [table.display_name for table in result.snapshot.entities] == ["<default>.users"]
    assert {row.kind for row in result.snapshot.members} >= {
        SqlAlchemyRowKind.COLUMN,
        SqlAlchemyRowKind.PRIMARY_KEY,
        SqlAlchemyRowKind.UNIQUE,
        SqlAlchemyRowKind.CHECK,
        SqlAlchemyRowKind.INDEX,
        SqlAlchemyRowKind.FOREIGN_KEY,
    }
    columns = {
        row.name: row for row in result.snapshot.members if isinstance(row, SqlAlchemyColumnRow)
    }
    assert columns["id"].type.category is SqlAlchemyTypeCategory.INTEGER
    assert columns["email"].type.category is SqlAlchemyTypeCategory.STRING
    assert columns["email"].type.parameters.present is True
    assert columns["email"].default.present is True
    assert "secret" not in repr(result.snapshot)


def test_classic_declarative_base_and_column_are_supported() -> None:
    result = _analyze(
        {
            "src/legacy.py": b"""
from sqlalchemy import Column, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Legacy(Base):
    __tablename__ = "legacy"
    id = Column(Integer, primary_key=True)
"""
        }
    )

    assert result.applicability is SqlAlchemyApplicability.PRESENT
    assert [table.name for table in result.snapshot.entities] == ["legacy"]
    assert [
        row.name for row in result.snapshot.members if row.kind is SqlAlchemyRowKind.COLUMN
    ] == ["id"]


def test_module_table_and_exact_table_link_merge_mapping_sources() -> None:
    result = _analyze(
        {
            "src/tables.py": b"""
from sqlalchemy import Column, Integer, Table
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase): pass

users = Table("users", object(), Column("id", Integer, primary_key=True), schema="auth")

class User(Base):
    __table__ = users
"""
        }
    )

    assert len(result.snapshot.entities) == 1
    table = result.snapshot.entities[0]
    assert table.display_name == "auth.users"
    assert table.mapping_kind is SqlAlchemyMappingKind.MIXED
    assert [source.kind.value for source in table.mapping_sources] == [
        "declarative_class",
        "table",
    ]


def test_abstract_base_is_present_empty_but_import_only_is_absent() -> None:
    abstract = _analyze(
        {
            "src/base.py": b"""
from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase):
    __abstract__ = True
"""
        }
    )
    import_only = _analyze(
        {"src/unused.py": b"from sqlalchemy.orm import DeclarativeBase, Mapped\n"}
    )

    assert abstract.applicability is SqlAlchemyApplicability.PRESENT
    assert abstract.snapshot.entities == ()
    assert abstract.snapshot.partial_safe is False
    assert import_only.applicability is SqlAlchemyApplicability.ABSENT
    assert import_only.snapshot.entities == ()


def test_parse_encoding_and_module_failures_are_indeterminate_and_mapped_to_sa_codes() -> None:
    parsed = _analyze({"src/broken.py": b"class Broken(\n"})
    encoded = _analyze({"src/encoded.py": b"# coding: unknown-codec\npass\n"})
    invalid_module = _analyze({"src/class.py": b"pass\n"})

    assert parsed.applicability is SqlAlchemyApplicability.INDETERMINATE
    assert [item.code.value for item in parsed.snapshot.diagnostics] == ["CSV-SA-003"]
    assert encoded.applicability is SqlAlchemyApplicability.INDETERMINATE
    assert [item.code.value for item in encoded.snapshot.diagnostics] == ["CSV-SA-002"]
    assert invalid_module.applicability is SqlAlchemyApplicability.INDETERMINATE
    assert [item.code.value for item in invalid_module.snapshot.diagnostics] == ["CSV-SA-004"]


def test_unrelated_same_table_identity_has_no_winner() -> None:
    result = _analyze(
        {
            "src/one.py": b"""
from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase): pass
class One(Base): __tablename__ = "shared"
""",
            "src/two.py": b"""
from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase): pass
class Two(Base): __tablename__ = "shared"
""",
        }
    )

    assert result.applicability is SqlAlchemyApplicability.PRESENT
    assert result.snapshot.entities == ()
    assert result.snapshot.partial_safe is True
    assert [item.code.value for item in result.snapshot.diagnostics].count("CSV-SA-008") == 1


def test_cross_module_base_binding_and_source_enumeration_are_deterministic() -> None:
    files = {
        "src/pkg/base.py": b"""
from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase): pass
""",
        "src/pkg/model.py": b"""
from .base import Base
from sqlalchemy.orm import Mapped, mapped_column
class Item(Base):
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(primary_key=True)
""",
    }

    first = _analyze(files)
    second = _analyze(dict(reversed(tuple(files.items()))))

    assert first == second
    assert [table.name for table in first.snapshot.entities] == ["items"]
