import hashlib
from pathlib import PurePosixPath

from code_structure_viz.adapters.sqlalchemy.analyzer import (
    SqlAlchemyAnalysisResult,
    SqlAlchemyApplicability,
    SqlAlchemySnapshotAnalyzer,
)
from code_structure_viz.adapters.sqlalchemy.model import (
    SqlAlchemyAssociationTableRow,
    SqlAlchemyCardinality,
    SqlAlchemyColumnRow,
    SqlAlchemyIndexRow,
    SqlAlchemyInheritanceRow,
    SqlAlchemyMappingKind,
    SqlAlchemyPrimaryKeyRow,
    SqlAlchemyRelationKind,
    SqlAlchemyRelationshipRow,
    SqlAlchemyRowKind,
    SqlAlchemyTargetResolution,
    SqlAlchemyTypeCategory,
    SqlAlchemyUniqueRow,
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


def test_relationship_descriptors_and_relations_are_extracted_statically() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase): pass

class Parent(Base):
    __tablename__ = "parents"
    id: Mapped[int] = mapped_column(primary_key=True)
    children: Mapped[list["Child"]] = relationship(
        "Child",
        back_populates="parent",
        primaryjoin=id == "never-publish-join",
        secondaryjoin=object(),
        order_by=id,
        foreign_keys=[id],
    )
    audit: Mapped[list["external.models.Audit"]] = relationship(
        "external.models.Audit",
        uselist=True,
    )

class Child(Base):
    __tablename__ = "children"
    id: Mapped[int] = mapped_column(primary_key=True)
    parent: Mapped[Parent] = relationship(
        argument=Parent,
        uselist=False,
        back_populates="children",
    )
"""
        }
    )

    relationships = {
        row.name: row
        for row in result.snapshot.members
        if isinstance(row, SqlAlchemyRelationshipRow)
    }
    assert set(relationships) == {"audit", "children", "parent"}
    assert relationships["children"].target.resolution is SqlAlchemyTargetResolution.INTERNAL
    assert relationships["children"].target.table_name == "children"
    assert relationships["children"].cardinality is SqlAlchemyCardinality.MANY
    assert relationships["children"].uselist is None
    assert relationships["children"].back_populates == "parent"
    assert relationships["children"].primaryjoin.present is True
    assert relationships["children"].secondaryjoin.present is True
    assert relationships["children"].order_by.present is True
    assert relationships["children"].foreign_keys.present is True
    assert relationships["parent"].cardinality is SqlAlchemyCardinality.SCALAR
    assert relationships["parent"].uselist is False
    assert relationships["audit"].target.resolution is SqlAlchemyTargetResolution.EXTERNAL
    assert relationships["audit"].target.symbol == "external.models.Audit"
    assert [
        relation.kind
        for relation in result.snapshot.relations
        if relation.kind is SqlAlchemyRelationKind.RELATIONSHIP
    ] == [SqlAlchemyRelationKind.RELATIONSHIP] * 2
    assert result.snapshot.coverage.redaction.redacted_values == 4
    assert result.snapshot.partial_safe is False
    assert "never-publish-join" not in repr(result.snapshot)


def test_relationship_unknown_values_are_partial_and_closed_keywords_are_rejected() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship

class Base(DeclarativeBase): pass

class User(Base):
    __tablename__ = "users"
    missing: Mapped["Missing"] = relationship("Missing")
    dynamic: Mapped["external.Target"] = relationship(
        "external.Target",
        uselist=USING_LIST,
        back_populates=BACK_NAME,
        secondary=secondary_factory(),
    )
    rejected_backref: Mapped["external.Target"] = relationship(
        "external.Target", backref="users"
    )
    rejected_cascade: Mapped["external.Target"] = relationship(
        "external.Target", cascade="all"
    )
"""
        }
    )

    relationships = {
        row.name: row
        for row in result.snapshot.members
        if isinstance(row, SqlAlchemyRelationshipRow)
    }
    assert set(relationships) == {"dynamic", "missing"}
    assert relationships["missing"].target.resolution is SqlAlchemyTargetResolution.UNKNOWN
    assert relationships["dynamic"].cardinality is SqlAlchemyCardinality.UNKNOWN
    assert relationships["dynamic"].back_populates is None
    assert relationships["dynamic"].secondary is not None
    assert relationships["dynamic"].secondary.resolution is SqlAlchemyTargetResolution.UNKNOWN
    codes = [item.code.value for item in result.snapshot.diagnostics]
    assert codes.count("CSV-SA-009") == 4
    assert codes.count("CSV-SA-010") == 2
    assert result.snapshot.coverage.unknown_declarations == 4
    assert result.snapshot.partial_safe is True


def test_unknown_type_target_and_cardinality_are_partial_with_failure_frontier() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase): pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column()
    dynamic = mapped_column(type_factory())
    missing: Mapped["Missing"] = relationship("Missing")
    cardinality = relationship("external.Target")
"""
        }
    )

    assert [table.name for table in result.snapshot.entities] == ["users"]
    assert {row.name for row in result.snapshot.members} == {
        "cardinality",
        "dynamic",
        "id",
        "missing",
    }
    assert [item.code.value for item in result.snapshot.diagnostics].count("CSV-SA-009") == 3
    assert [item.code.value for item in result.snapshot.diagnostics].count("CSV-SA-010") == 1
    assert result.snapshot.coverage.unknown_declarations == 3
    assert result.snapshot.partial_safe is True
    assert all(item.direction.value == "failure" for item in result.snapshot.coverage.frontier)


def test_closed_outer_call_grammar_omits_each_offending_row_once() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy import CheckConstraint, Computed, ForeignKey, Identity, Index, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase): pass

class Item(Base):
    __tablename__ = "items"
    __table_args__ = (
        CheckConstraint(*checks),
        Index("ix_dynamic", *terms),
    )
    id: Mapped[int] = mapped_column()
    starred = mapped_column(*parts)
    keyword_star = mapped_column(**options)
    type_after_special = mapped_column(ForeignKey("parents.id"), Integer)
    duplicate_computed = mapped_column(Integer, Computed("first"), Computed("second"))
    duplicate_identity = mapped_column(Integer, Identity(), Identity())
"""
        }
    )

    assert [row.name for row in result.snapshot.members] == ["id"]
    codes = [item.code.value for item in result.snapshot.diagnostics]
    assert codes == ["CSV-SA-009"] * 7
    assert result.snapshot.coverage.unknown_declarations == 7
    assert len(result.snapshot.coverage.frontier) == 7
    assert result.snapshot.partial_safe is True


def test_unsupported_table_call_consumes_nested_construction_calls_once() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy import Column, ForeignKey, Integer, Table

users = Table(
    "users",
    object(),
    Column("account_id", Integer, ForeignKey("accounts.id")),
    autoload_with=engine,
)
"""
        }
    )

    assert result.snapshot.entities == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-007"]
    assert result.snapshot.coverage.unknown_declarations == 1
    assert len(result.snapshot.coverage.frontier) == 1
    assert result.snapshot.partial_safe is True


def test_duplicate_source_class_declarations_remain_ambiguous_without_a_winner() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase): pass
class User(Base): __tablename__ = "users_one"
class User(Base): __tablename__ = "users_two"
"""
        }
    )

    assert [table.name for table in result.snapshot.entities] == ["users_one", "users_two"]
    assert all(
        [source.symbol for source in table.mapping_sources] == ["models.User"]
        for table in result.snapshot.entities
    )
    assert [item.code.value for item in result.snapshot.diagnostics] == [
        "CSV-SA-006",
        "CSV-SA-006",
    ]
    assert result.snapshot.partial_safe is True


def test_relationship_annotation_fallback_supports_optional_union_and_collection() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from typing import List, Optional
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship
class Base(DeclarativeBase): pass
class Child(Base): __tablename__ = "children"
class Parent(Base):
    __tablename__ = "parents"
    optional_child: Mapped[Optional[Child]] = relationship()
    union_child: Mapped[Child | None] = relationship()
    children: Mapped[List["Child"]] = relationship()
"""
        }
    )

    relationships = {
        row.name: row
        for row in result.snapshot.members
        if isinstance(row, SqlAlchemyRelationshipRow)
    }
    assert relationships["optional_child"].cardinality is SqlAlchemyCardinality.SCALAR
    assert relationships["union_child"].cardinality is SqlAlchemyCardinality.SCALAR
    assert relationships["children"].cardinality is SqlAlchemyCardinality.MANY
    assert all(row.target.table_name == "children" for row in relationships.values())
    assert result.snapshot.partial_safe is False


def test_inheritance_and_internal_secondary_create_rows_and_relations() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy import Column, Integer, Table
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship

membership = Table("membership", object(), Column("id", Integer))

class Base(DeclarativeBase): pass

class User(Base):
    __tablename__ = "users"
    groups: Mapped[list["Group"]] = relationship("Group", secondary=membership)

class Group(Base):
    __tablename__ = "groups"

class Admin(User):
    __tablename__ = "admins"

class SameTableUser(User):
    pass
"""
        }
    )

    inheritance = [
        row for row in result.snapshot.members if isinstance(row, SqlAlchemyInheritanceRow)
    ]
    associations = [
        row for row in result.snapshot.members if isinstance(row, SqlAlchemyAssociationTableRow)
    ]
    assert len(inheritance) == 1
    assert inheritance[0].target.table_name == "users"
    assert len(associations) == 1
    assert associations[0].owner_id == next(
        table.id for table in result.snapshot.entities if table.name == "membership"
    )
    assert associations[0].source_table.table_name == "users"
    assert associations[0].relationship_target.table_name == "groups"
    assert result.snapshot.coverage.association_tables == 1
    assert {relation.kind for relation in result.snapshot.relations} == {
        SqlAlchemyRelationKind.RELATIONSHIP,
        SqlAlchemyRelationKind.INHERITANCE,
        SqlAlchemyRelationKind.ASSOCIATION,
    }


def test_cross_module_relationship_and_secondary_aliases_resolve_to_internal_tables() -> None:
    result = _analyze(
        {
            "src/pkg/base.py": b"""
from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase): pass
""",
            "src/pkg/tables.py": b"""
from sqlalchemy import Table
membership = Table("membership", object())
""",
            "src/pkg/groups.py": b"""
from .base import Base
class Group(Base): __tablename__ = "groups"
""",
            "src/pkg/users.py": b"""
from .base import Base
from .groups import Group as Team
from .tables import membership as membership_table
from sqlalchemy.orm import Mapped, relationship
class User(Base):
    __tablename__ = "users"
    teams: Mapped[list[Team]] = relationship(Team, secondary=membership_table)
""",
        }
    )

    relationship = next(
        row for row in result.snapshot.members if isinstance(row, SqlAlchemyRelationshipRow)
    )
    association = next(
        row for row in result.snapshot.members if isinstance(row, SqlAlchemyAssociationTableRow)
    )
    assert relationship.target.resolution is SqlAlchemyTargetResolution.INTERNAL
    assert relationship.target.table_name == "groups"
    assert relationship.secondary is not None
    assert relationship.secondary.table_name == "membership"
    assert association.source_table.table_name == "users"
    assert result.snapshot.partial_safe is False


def test_static_secondary_to_declarative_table_does_not_synthesize_association_marker() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship
class Base(DeclarativeBase): pass
class Link(Base): __tablename__ = "links"
class User(Base):
    __tablename__ = "users"
    links: Mapped[list[Link]] = relationship(Link, secondary="links")
"""
        }
    )

    relationship = next(
        row for row in result.snapshot.members if isinstance(row, SqlAlchemyRelationshipRow)
    )
    assert relationship.secondary is not None
    assert relationship.secondary.resolution is SqlAlchemyTargetResolution.INTERNAL
    assert not any(
        isinstance(row, SqlAlchemyAssociationTableRow) for row in result.snapshot.members
    )
    assert result.snapshot.coverage.association_tables == 0


def test_lossy_constraint_and_index_occurrences_are_all_excluded() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy import CheckConstraint, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase): pass

class Item(Base):
    __tablename__ = "items"
    __table_args__ = (
        CheckConstraint("private-a"),
        CheckConstraint("private-b"),
        Index(None, lower(first_secret)),
        Index(None, upper(second_secret)),
    )
    id: Mapped[int] = mapped_column()
"""
        }
    )

    assert [row.kind for row in result.snapshot.members] == [SqlAlchemyRowKind.COLUMN]
    occurrences = [item for item in result.snapshot.diagnostics if item.code.value == "CSV-SA-009"]
    assert len(occurrences) == 4
    assert len({item.symbol for item in occurrences}) == 4
    assert result.snapshot.coverage.unknown_declarations == 4
    assert result.snapshot.partial_safe is True
    assert "private-a" not in repr(result.snapshot)
    assert "private-b" not in repr(result.snapshot)


def test_same_line_lossy_siblings_keep_distinct_occurrence_symbols() -> None:
    result = _analyze(
        {
            "src/models.py": (
                b"""
from sqlalchemy import CheckConstraint, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
class Base(DeclarativeBase): pass
class Item(Base):
    __tablename__ = "items"
"""
                b'    __table_args__ = (CheckConstraint("a"), CheckConstraint("b"), '
                b"Index(None, lower(a)), Index(None, upper(b)))\n"
                b"""
    id: Mapped[int] = mapped_column()
"""
            )
        }
    )

    occurrences = [item for item in result.snapshot.diagnostics if item.code.value == "CSV-SA-009"]
    assert len(occurrences) == 4
    assert {item.line for item in occurrences} == {7}
    assert len({item.symbol for item in occurrences}) == 4
    assert [row.kind for row in result.snapshot.members] == [SqlAlchemyRowKind.COLUMN]


def test_ordinary_non_lossy_duplicate_is_canonicalized_without_partial_status() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email"),)
    email: Mapped[str] = mapped_column(unique=True)
"""
        }
    )

    assert [row.kind for row in result.snapshot.members].count(SqlAlchemyRowKind.UNIQUE) == 1
    assert result.snapshot.diagnostics == ()
    assert result.snapshot.partial_safe is False


def test_rebound_column_is_unknown_instead_of_false_complete() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy import Column, Integer
from sqlalchemy.orm import DeclarativeBase

Column = replacement

class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    python_name = Column(Integer)
"""
        }
    )

    assert [table.name for table in result.snapshot.entities] == ["users"]
    assert result.snapshot.members == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-009"]
    assert result.snapshot.coverage.unknown_declarations == 1
    assert result.snapshot.partial_safe is True


def test_star_import_mapped_annotation_is_unknown_in_a_safe_table() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import *
from sqlalchemy.orm import DeclarativeBase as SafeBase

class Base(SafeBase): pass
class User(Base):
    __tablename__ = "users"
    id: Mapped[int]
"""
        }
    )

    assert [table.name for table in result.snapshot.entities] == ["users"]
    assert result.snapshot.members == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-009"]
    assert result.snapshot.coverage.unknown_declarations == 1
    assert result.snapshot.partial_safe is True


def test_star_import_declarative_base_is_indeterminate() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy.orm import *

class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
"""
        }
    )

    assert result.applicability is SqlAlchemyApplicability.INDETERMINATE
    assert result.snapshot.entities == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-006"]
    assert result.snapshot.coverage.unknown_declarations == 1
    assert result.snapshot.partial_safe is True


def test_star_import_relationship_call_is_unknown_in_a_safe_table() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy.orm import DeclarativeBase, Mapped
from sqlalchemy.orm import *
from sqlalchemy.orm import DeclarativeBase as SafeBase, Mapped as SafeMapped

class Base(SafeBase): pass
class User(Base):
    __tablename__ = "users"
    parent: SafeMapped["Parent"] = relationship("Parent")
"""
        }
    )

    assert [table.name for table in result.snapshot.entities] == ["users"]
    assert result.snapshot.members == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-009"]
    assert result.snapshot.coverage.unknown_declarations == 1
    assert result.snapshot.partial_safe is True


def test_unrelated_star_import_call_is_not_sqlalchemy_evidence() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy.orm import *

def helper():
    return relationship("not-a-declaration")
"""
        }
    )

    assert result.applicability is SqlAlchemyApplicability.ABSENT
    assert result.snapshot.diagnostics == ()
    assert result.snapshot.coverage.unknown_declarations == 0
    assert result.snapshot.partial_safe is False


def test_explicit_column_names_override_class_attribute_names_for_both_styles() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy import Column, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase): pass

class Modern(Base):
    __tablename__ = "modern"
    python_name: Mapped[int] = mapped_column("modern_db_name", Integer)

class Legacy(Base):
    __tablename__ = "legacy"
    python_name = Column("legacy_db_name", Integer)
"""
        }
    )

    columns = {row.name for row in result.snapshot.members if isinstance(row, SqlAlchemyColumnRow)}
    assert columns == {"modern_db_name", "legacy_db_name"}
    assert result.snapshot.diagnostics == ()
    assert result.snapshot.partial_safe is False


def test_empty_table_args_mapping_is_a_safe_no_options_state() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    __table_args__ = {}
"""
        }
    )

    assert [table.name for table in result.snapshot.entities] == ["users"]
    assert result.snapshot.diagnostics == ()
    assert result.snapshot.coverage.unknown_declarations == 0
    assert result.snapshot.partial_safe is False


def test_callable_check_constraints_are_locally_unknown_without_run_fatal() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy import CheckConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

def named_check():
    return True

class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(lambda: True),
        CheckConstraint(named_check),
    )
    id: Mapped[int] = mapped_column()
"""
        }
    )

    assert [table.name for table in result.snapshot.entities] == ["users"]
    assert [row.kind for row in result.snapshot.members] == [SqlAlchemyRowKind.COLUMN]
    assert [item.code.value for item in result.snapshot.diagnostics] == [
        "CSV-SA-009",
        "CSV-SA-009",
    ]
    assert result.snapshot.coverage.unknown_declarations == 2
    assert result.snapshot.partial_safe is True


def test_rebound_sqlalchemy_alias_is_unknown_instead_of_false_complete() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy import Column as SAColumn, Integer
from sqlalchemy.orm import DeclarativeBase

SAColumn = replacement

class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    python_name = SAColumn(Integer)
"""
        }
    )

    assert [table.name for table in result.snapshot.entities] == ["users"]
    assert result.snapshot.members == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-009"]
    assert result.snapshot.coverage.unknown_declarations == 1
    assert result.snapshot.partial_safe is True


def test_conditionally_rebound_sqlalchemy_alias_is_unknown() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy import Column as SAColumn, Integer
from sqlalchemy.orm import DeclarativeBase

if condition:
    SAColumn = replacement

class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    python_name = SAColumn(Integer)
"""
        }
    )

    assert [table.name for table in result.snapshot.entities] == ["users"]
    assert result.snapshot.members == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-009"]
    assert result.snapshot.coverage.unknown_declarations == 1
    assert result.snapshot.partial_safe is True


def test_conditionally_imported_sqlalchemy_module_is_unknown() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy import Integer
from sqlalchemy.orm import DeclarativeBase

if condition:
    import sqlalchemy as sa

class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    python_name = sa.Column(Integer)
"""
        }
    )

    assert [table.name for table in result.snapshot.entities] == ["users"]
    assert result.snapshot.members == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-009"]
    assert result.snapshot.coverage.unknown_declarations == 1
    assert result.snapshot.partial_safe is True


def test_runtime_target_rebinding_of_sqlalchemy_alias_is_unknown() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy import Column as SAColumn, Integer
from sqlalchemy.orm import DeclarativeBase

for SAColumn in replacements:
    pass

class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    python_name = SAColumn(Integer)
"""
        }
    )

    assert [table.name for table in result.snapshot.entities] == ["users"]
    assert result.snapshot.members == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-009"]
    assert result.snapshot.coverage.unknown_declarations == 1
    assert result.snapshot.partial_safe is True


def test_conditionally_rebound_local_declarative_base_is_unknown() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase): pass

if condition:
    Base = replacement

class User(Base):
    __tablename__ = "users"
"""
        }
    )

    assert result.applicability is SqlAlchemyApplicability.PRESENT
    assert result.snapshot.entities == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-006"]
    assert result.snapshot.coverage.unknown_declarations >= 1
    assert result.snapshot.partial_safe is True


def test_star_import_invalidates_existing_sqlalchemy_column_binding() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy import Column, Integer
from sqlalchemy.orm import DeclarativeBase
from helpers import *
from sqlalchemy.orm import DeclarativeBase as SafeBase

class Base(SafeBase): pass
class User(Base):
    __tablename__ = "users"
    python_name = Column(Integer)
"""
        }
    )

    assert [table.name for table in result.snapshot.entities] == ["users"]
    assert result.snapshot.members == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-009"]
    assert result.snapshot.coverage.unknown_declarations == 1
    assert result.snapshot.partial_safe is True


def test_unrebound_sqlalchemy_alias_remains_supported() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy import Column as SAColumn, Integer
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    python_name = SAColumn("db_name", Integer)
"""
        }
    )

    assert [row.name for row in result.snapshot.members] == ["db_name"]
    assert result.snapshot.diagnostics == ()
    assert result.snapshot.partial_safe is False


def test_explicit_column_names_resolve_attribute_references_in_class_constraints() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy import (
    Column,
    Index,
    Integer,
    PrimaryKeyConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase): pass

class Modern(Base):
    __tablename__ = "modern"
    __table_args__ = (
        PrimaryKeyConstraint(modern_name),
        UniqueConstraint(modern_name),
        Index("ix_modern", modern_name),
    )
    modern_name: Mapped[int] = mapped_column("modern_db_name", Integer)

class Legacy(Base):
    __tablename__ = "legacy"
    __table_args__ = (
        PrimaryKeyConstraint(legacy_name),
        UniqueConstraint(legacy_name),
        Index("ix_legacy", legacy_name),
    )
    legacy_name = Column("legacy_db_name", Integer)
"""
        }
    )

    columns = {row.name for row in result.snapshot.members if isinstance(row, SqlAlchemyColumnRow)}
    primary_keys = {
        row.columns for row in result.snapshot.members if isinstance(row, SqlAlchemyPrimaryKeyRow)
    }
    uniques = {
        row.columns for row in result.snapshot.members if isinstance(row, SqlAlchemyUniqueRow)
    }
    indexes = {
        (row.name, tuple(term.column_name for term in row.terms))
        for row in result.snapshot.members
        if isinstance(row, SqlAlchemyIndexRow)
    }
    assert columns == {"modern_db_name", "legacy_db_name"}
    assert primary_keys == {("modern_db_name",), ("legacy_db_name",)}
    assert uniques == {("modern_db_name",), ("legacy_db_name",)}
    assert indexes == {
        ("ix_modern", ("modern_db_name",)),
        ("ix_legacy", ("legacy_db_name",)),
    }
    assert result.snapshot.diagnostics == ()
    assert result.snapshot.partial_safe is False


def test_destructured_rebinding_of_sqlalchemy_column_is_unknown() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy import Column, Integer
from sqlalchemy.orm import DeclarativeBase

Column, other = replacements

class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    python_name = Column(Integer)
"""
        }
    )

    assert [table.name for table in result.snapshot.entities] == ["users"]
    assert result.snapshot.members == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-009"]
    assert result.snapshot.coverage.unknown_declarations == 1
    assert result.snapshot.partial_safe is True


def test_class_scope_rebinding_of_sqlalchemy_column_is_unknown() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy import Column, Integer
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    Column = helper
    python_name = Column(Integer)
"""
        }
    )

    assert [table.name for table in result.snapshot.entities] == ["users"]
    assert result.snapshot.members == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-009"]
    assert result.snapshot.coverage.unknown_declarations == 1
    assert result.snapshot.partial_safe is True


def test_unknown_module_same_terminal_alias_is_not_sqlalchemy_evidence() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from fake import DeclarativeBase as DB

DB = replacement

class Candidate(DB): pass
"""
        }
    )

    assert result.applicability is SqlAlchemyApplicability.ABSENT
    assert result.snapshot.entities == ()
    assert result.snapshot.diagnostics == ()
    assert result.snapshot.coverage.unknown_declarations == 0
    assert result.snapshot.partial_safe is False


def test_reexported_repository_base_alias_resolves_across_modules() -> None:
    result = _analyze(
        {
            "src/pkg/base.py": b"""
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase): pass
""",
            "src/pkg/__init__.py": b"""
from .base import Base
""",
            "src/pkg/models.py": b"""
from . import Base

class User(Base):
    __tablename__ = "users"
""",
        }
    )

    assert [table.name for table in result.snapshot.entities] == ["users"]
    assert result.snapshot.diagnostics == ()
    assert result.snapshot.partial_safe is False


def test_duplicate_module_table_binding_has_no_last_winner() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy import Table

users = Table("first", object())
users = Table("second", object())
"""
        }
    )

    assert result.applicability is SqlAlchemyApplicability.INDETERMINATE
    assert result.snapshot.entities == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == [
        "CSV-SA-007",
        "CSV-SA-007",
    ]
    assert result.snapshot.coverage.unknown_declarations == 2
    assert result.snapshot.partial_safe is True


def test_duplicate_plain_python_classes_do_not_create_sqlalchemy_evidence() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
class Helper: pass
class Helper: pass
"""
        }
    )

    assert result.applicability is SqlAlchemyApplicability.ABSENT
    assert result.snapshot.entities == ()
    assert result.snapshot.diagnostics == ()
    assert result.snapshot.coverage.unknown_declarations == 0
    assert result.snapshot.partial_safe is False


def test_sqlalchemy_prefixed_module_star_import_is_not_trusted() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy import Column, Integer
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy_helpers import *
from sqlalchemy.orm import DeclarativeBase as SafeBase

class Base(SafeBase): pass
class User(Base):
    __tablename__ = "users"
    python_name = Column(Integer)
"""
        }
    )

    assert [table.name for table in result.snapshot.entities] == ["users"]
    assert result.snapshot.members == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-009"]
    assert result.snapshot.coverage.unknown_declarations == 1
    assert result.snapshot.partial_safe is True


def test_type_alias_rebinding_of_sqlalchemy_column_is_unknown() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy import Column, Integer
from sqlalchemy.orm import DeclarativeBase

type Column = object

class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    python_name = Column(Integer)
"""
        }
    )

    assert [table.name for table in result.snapshot.entities] == ["users"]
    assert result.snapshot.members == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-009"]
    assert result.snapshot.partial_safe is True


def test_conditional_type_alias_rebinding_of_sqlalchemy_column_is_unknown() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy import Column, Integer
from sqlalchemy.orm import DeclarativeBase

if condition:
    type Column = object

class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    python_name = Column(Integer)
"""
        }
    )

    assert [table.name for table in result.snapshot.entities] == ["users"]
    assert result.snapshot.members == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-009"]
    assert result.snapshot.partial_safe is True


def test_ambiguous_reexport_propagates_proven_declarative_base_origin() -> None:
    result = _analyze(
        {
            "src/pkg/base.py": b"""
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase): pass
""",
            "src/pkg/__init__.py": b"""
from .base import Base

if condition:
    Base = replacement
""",
            "src/pkg/models.py": b"""
from . import Base

class User(Base):
    __tablename__ = "users"
""",
        }
    )

    assert result.applicability is SqlAlchemyApplicability.PRESENT
    assert result.snapshot.entities == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-006"]
    assert result.snapshot.partial_safe is True


def test_repository_module_attribute_base_alias_resolves_across_modules() -> None:
    result = _analyze(
        {
            "src/pkg/base.py": b"""
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase): pass
""",
            "src/pkg/__init__.py": b"""
from .base import Base
""",
            "src/pkg/models.py": b"""
import pkg

class User(pkg.Base):
    __tablename__ = "users"
""",
        }
    )

    assert [table.name for table in result.snapshot.entities] == ["users"]
    assert result.snapshot.diagnostics == ()
    assert result.snapshot.partial_safe is False


def test_unbound_sqlalchemy_terminal_names_are_not_domain_evidence() -> None:
    result = _analyze(
        {
            "src/plain_base.py": b"class Candidate(DeclarativeBase): pass\n",
            "src/plain_factory.py": b"Base = declarative_base()\nclass Candidate(Base): pass\n",
            "src/plain_table.py": b'users = Table("users", object())\n',
        }
    )

    assert result.applicability is SqlAlchemyApplicability.ABSENT
    assert result.snapshot.entities == ()
    assert result.snapshot.diagnostics == ()
    assert result.snapshot.coverage.unknown_declarations == 0
    assert result.snapshot.partial_safe is False


def test_module_binding_shadows_builtin_scalar_column_type() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from custom_types import CustomType
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

int = CustomType

class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column()
"""
        }
    )

    columns = [row for row in result.snapshot.members if isinstance(row, SqlAlchemyColumnRow)]
    assert len(columns) == 1
    assert columns[0].type.category is SqlAlchemyTypeCategory.CUSTOM
    assert columns[0].type.name == "models.int"
    assert result.snapshot.diagnostics == ()
    assert result.snapshot.partial_safe is False


def test_module_binding_shadows_builtin_relationship_collection() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from custom_types import CustomCollection
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship

list = CustomCollection

class Base(DeclarativeBase): pass
class Parent(Base):
    __tablename__ = "parents"
    children: Mapped[list["Child"]] = relationship("Child")

class Child(Base):
    __tablename__ = "children"
"""
        }
    )

    relationships = [
        row for row in result.snapshot.members if isinstance(row, SqlAlchemyRelationshipRow)
    ]
    assert len(relationships) == 1
    assert relationships[0].cardinality is SqlAlchemyCardinality.UNKNOWN
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-009"]
    assert result.snapshot.partial_safe is True


def test_sqlalchemy_star_import_invalidates_existing_column_binding() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy import Column, Integer
from sqlalchemy.orm import *
from sqlalchemy.orm import DeclarativeBase as SafeBase

class Base(SafeBase): pass
class User(Base):
    __tablename__ = "users"
    id = Column(Integer)
"""
        }
    )

    assert [table.name for table in result.snapshot.entities] == ["users"]
    assert result.snapshot.members == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-009"]
    assert result.snapshot.partial_safe is True


def test_class_local_sqlalchemy_import_alias_resolves_column() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    from sqlalchemy import Column as LocalColumn, Integer as LocalInteger
    id = LocalColumn(LocalInteger)
"""
        }
    )

    columns = [row for row in result.snapshot.members if isinstance(row, SqlAlchemyColumnRow)]
    assert len(columns) == 1
    assert columns[0].name == "id"
    assert columns[0].type.category is SqlAlchemyTypeCategory.INTEGER
    assert result.snapshot.diagnostics == ()
    assert result.snapshot.partial_safe is False


def test_star_imported_repository_reexport_remains_unknown() -> None:
    result = _analyze(
        {
            "src/pkg/base.py": b"from sqlalchemy.orm import *\n",
            "src/pkg/models.py": b"""
from .base import DeclarativeBase as Base

class User(Base):
    __tablename__ = "users"
""",
        }
    )

    assert result.applicability is SqlAlchemyApplicability.INDETERMINATE
    assert result.snapshot.entities == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-006"]
    assert result.snapshot.partial_safe is True


def test_repository_sqlalchemy_module_shadows_external_namespace() -> None:
    result = _analyze(
        {
            "src/sqlalchemy.py": b"def Table(*args): return args\n",
            "src/models.py": b"""
import sqlalchemy

users = sqlalchemy.Table("users", object())
""",
        }
    )

    assert result.applicability is SqlAlchemyApplicability.ABSENT
    assert result.snapshot.entities == ()
    assert result.snapshot.diagnostics == ()
    assert result.snapshot.coverage.unknown_declarations == 0
    assert result.snapshot.partial_safe is False


def test_class_local_scalar_binding_shadows_builtin_in_statement_order() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from custom_types import CustomType
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase): pass
class Before(Base):
    __tablename__ = "before"
    int = CustomType
    id: Mapped[int] = mapped_column()

class After(Base):
    __tablename__ = "after"
    id: Mapped[int] = mapped_column()
    int = CustomType
"""
        }
    )

    columns = {
        next(table.name for table in result.snapshot.entities if table.id == row.owner_id): row
        for row in result.snapshot.members
        if isinstance(row, SqlAlchemyColumnRow)
    }
    assert columns["before"].type.category is SqlAlchemyTypeCategory.CUSTOM
    assert columns["before"].type.name == "models.Before.int"
    assert columns["after"].type.category is SqlAlchemyTypeCategory.INTEGER
    assert columns["after"].type.name == "builtins.int"
    assert result.snapshot.diagnostics == ()
    assert result.snapshot.partial_safe is False


def test_class_local_collection_binding_shadows_builtin_in_statement_order() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from custom_types import CustomCollection
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship

class Base(DeclarativeBase): pass
class Parent(Base):
    __tablename__ = "parents"
    before: Mapped[list["Child"]] = relationship("Child")
    list = CustomCollection
    after: Mapped[list["Child"]] = relationship("Child")

class Child(Base):
    __tablename__ = "children"
"""
        }
    )

    relationships = {
        row.name: row
        for row in result.snapshot.members
        if isinstance(row, SqlAlchemyRelationshipRow)
    }
    assert relationships["before"].cardinality is SqlAlchemyCardinality.MANY
    assert relationships["after"].cardinality is SqlAlchemyCardinality.UNKNOWN
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-009"]
    assert result.snapshot.partial_safe is True


def test_canonical_calls_outside_declaration_positions_are_not_evidence() -> None:
    result = _analyze(
        {
            "src/helpers.py": b"""
from sqlalchemy import Column, Table
from sqlalchemy.orm import declarative_base, relationship

Column("top-level-expression")
Table("top-level-expression", object())
relationship("top-level-expression")
declarative_base()

def helper():
    local_base = declarative_base()
    return Column("function-local")

class Plain:
    value = Column("plain-class")
    local_base = declarative_base()
"""
        }
    )

    assert result.applicability is SqlAlchemyApplicability.ABSENT
    assert result.snapshot.entities == ()
    assert result.snapshot.diagnostics == ()
    assert result.snapshot.coverage.unknown_declarations == 0
    assert result.snapshot.partial_safe is False


def test_conditional_repository_base_import_retains_ambiguous_provenance() -> None:
    result = _analyze(
        {
            "src/pkg/base.py": b"""
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase): pass
""",
            "src/pkg/models.py": b"""
if condition:
    from .base import Base

class User(Base):
    __tablename__ = "users"
""",
        }
    )

    assert result.applicability is SqlAlchemyApplicability.PRESENT
    assert result.snapshot.entities == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-006"]
    assert result.snapshot.partial_safe is True


def test_conditional_repository_module_import_retains_ambiguous_provenance() -> None:
    result = _analyze(
        {
            "src/pkg/base.py": b"""
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase): pass
""",
            "src/pkg/models.py": b"""
if condition:
    import pkg.base as local_base

class User(local_base.Base):
    __tablename__ = "users"
""",
        }
    )

    assert result.applicability is SqlAlchemyApplicability.PRESENT
    assert result.snapshot.entities == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-006"]
    assert result.snapshot.partial_safe is True


def test_conditional_unknown_module_base_import_is_not_sqlalchemy_evidence() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
if condition:
    from fake import DeclarativeBase as Base

class Candidate(Base): pass
"""
        }
    )

    assert result.applicability is SqlAlchemyApplicability.ABSENT
    assert result.snapshot.entities == ()
    assert result.snapshot.diagnostics == ()
    assert result.snapshot.coverage.unknown_declarations == 0
    assert result.snapshot.partial_safe is False


def test_unsupported_module_table_assignment_shapes_are_unknown() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy import Table

if condition:
    conditional = Table("conditional", object())
first, second = Table("unpacked", object())
holder.attribute = Table("attribute", object())
"""
        }
    )

    assert result.applicability is SqlAlchemyApplicability.INDETERMINATE
    assert result.snapshot.entities == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == [
        "CSV-SA-007",
        "CSV-SA-007",
        "CSV-SA-007",
    ]
    assert result.snapshot.coverage.unknown_declarations == 3
    assert len(result.snapshot.coverage.frontier) == 3
    assert result.snapshot.partial_safe is True


def test_unsupported_declarative_row_assignment_shapes_are_unknown() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy import Column, Integer
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    if condition:
        conditional = Column(Integer)
    first, second = Column(Integer)
    holder.attribute = Column(Integer)
"""
        }
    )

    assert [table.name for table in result.snapshot.entities] == ["users"]
    assert result.snapshot.members == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == [
        "CSV-SA-009",
        "CSV-SA-009",
        "CSV-SA-009",
    ]
    assert result.snapshot.coverage.unknown_declarations == 3
    assert len(result.snapshot.coverage.frontier) == 3
    assert result.snapshot.partial_safe is True


def test_conditional_special_attribute_rebinding_makes_table_identity_unknown() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    if condition:
        __tablename__ = "admins"
"""
        }
    )

    assert result.applicability is SqlAlchemyApplicability.PRESENT
    assert result.snapshot.entities == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-007"]
    assert result.snapshot.coverage.unknown_declarations == 1
    assert result.snapshot.partial_safe is True


def test_class_local_constraint_shadow_makes_table_identity_unknown() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from helpers import helper
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    UniqueConstraint = helper
    __table_args__ = (UniqueConstraint("id"),)
    id: Mapped[int] = mapped_column()
"""
        }
    )

    assert result.applicability is SqlAlchemyApplicability.PRESENT
    assert result.snapshot.entities == ()
    assert result.snapshot.members == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-007"]
    assert result.snapshot.coverage.unknown_declarations == 1
    assert result.snapshot.partial_safe is True


def test_class_local_constraint_import_is_used_by_table_args() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase): pass
class User(Base):
    from sqlalchemy import UniqueConstraint as LocalUniqueConstraint
    __tablename__ = "users"
    __table_args__ = (LocalUniqueConstraint("id"),)
    id: Mapped[int] = mapped_column()
"""
        }
    )

    assert [table.name for table in result.snapshot.entities] == ["users"]
    assert [row.kind for row in result.snapshot.members] == [
        SqlAlchemyRowKind.COLUMN,
        SqlAlchemyRowKind.UNIQUE,
    ]
    assert result.snapshot.diagnostics == ()
    assert result.snapshot.partial_safe is False


def test_class_local_table_import_is_used_by_table_special() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase): pass
class User(Base):
    from sqlalchemy import Column as LocalColumn, Integer as LocalInteger, Table as LocalTable
    __table__ = LocalTable(
        "users",
        object(),
        LocalColumn("id", LocalInteger),
    )
"""
        }
    )

    assert [table.name for table in result.snapshot.entities] == ["users"]
    columns = [row for row in result.snapshot.members if isinstance(row, SqlAlchemyColumnRow)]
    assert len(columns) == 1
    assert columns[0].name == "id"
    assert columns[0].type.category is SqlAlchemyTypeCategory.INTEGER
    assert result.snapshot.diagnostics == ()
    assert result.snapshot.partial_safe is False


def test_dynamic_call_result_base_with_declarative_argument_is_unknown() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy.orm import DeclarativeBase

def wrap(value):
    return value

class User(wrap(DeclarativeBase)):
    __tablename__ = "users"
"""
        }
    )

    assert result.applicability is SqlAlchemyApplicability.INDETERMINATE
    assert result.snapshot.entities == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-006"]
    assert result.snapshot.partial_safe is True


def test_conditional_declarative_base_factory_assignment_is_unknown() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy.orm import declarative_base

if condition:
    Base = declarative_base()

class User(Base):
    __tablename__ = "users"
"""
        }
    )

    assert result.applicability is SqlAlchemyApplicability.INDETERMINATE
    assert result.snapshot.entities == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-006"]
    assert result.snapshot.partial_safe is True


def test_rebound_direct_declarative_base_factory_assignment_is_unknown() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy.orm import declarative_base

Base = declarative_base()
Base = replacement

class User(Base):
    __tablename__ = "users"
"""
        }
    )

    assert result.applicability is SqlAlchemyApplicability.INDETERMINATE
    assert result.snapshot.entities == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-006"]
    assert result.snapshot.partial_safe is True


def test_arbitrary_call_result_base_is_not_sqlalchemy_evidence() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
def make_base():
    return object

candidate = (make_base(),)[0]

def helper():
    return (make_base(),)[0]

class Plain:
    candidate = (make_base(),)[0]

class Candidate(make_base()):
    pass
"""
        }
    )

    assert result.applicability is SqlAlchemyApplicability.ABSENT
    assert result.snapshot.entities == ()
    assert result.snapshot.diagnostics == ()
    assert result.snapshot.coverage.unknown_declarations == 0
    assert result.snapshot.partial_safe is False


def test_conditional_expression_base_with_declarative_evidence_is_unknown() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy.orm import DeclarativeBase

class User(DeclarativeBase if USE_SQLA else object):
    __tablename__ = "users"
"""
        }
    )

    assert result.applicability is SqlAlchemyApplicability.INDETERMINATE
    assert result.snapshot.entities == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-006"]
    assert result.snapshot.partial_safe is True


def test_composite_declarative_base_factory_assignment_is_unknown() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy.orm import declarative_base

Base = (declarative_base(),)[0]

class User(Base):
    __tablename__ = "users"
"""
        }
    )

    assert result.applicability is SqlAlchemyApplicability.INDETERMINATE
    assert result.snapshot.entities == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-006"]
    assert result.snapshot.partial_safe is True


def test_composite_assignment_from_proven_base_is_unknown() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy.orm import DeclarativeBase

class Root(DeclarativeBase):
    pass

Base = (Root,)[0]

class User(Base):
    __tablename__ = "users"
"""
        }
    )

    assert result.applicability is SqlAlchemyApplicability.PRESENT
    assert result.snapshot.entities == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-006"]
    assert result.snapshot.partial_safe is True


def test_composite_attribute_assignment_consumed_as_base_is_unknown() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy.orm import declarative_base

class Namespace:
    pass

namespace = Namespace()
namespace.Base = (declarative_base(),)[0]

class User(namespace.Base):
    __tablename__ = "users"
"""
        }
    )

    assert result.applicability is SqlAlchemyApplicability.INDETERMINATE
    assert result.snapshot.entities == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-006"]
    assert result.snapshot.partial_safe is True


def test_unused_declarative_base_reference_is_not_domain_evidence() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy.orm import DeclarativeBase

unused = DeclarativeBase
"""
        }
    )

    assert result.applicability is SqlAlchemyApplicability.ABSENT
    assert result.snapshot.entities == ()
    assert result.snapshot.diagnostics == ()
    assert result.snapshot.coverage.unknown_declarations == 0
    assert result.snapshot.partial_safe is False


def test_declarative_class_registries_are_not_unknown_evidence() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

MODEL_TYPES = (User,)
REGISTRY = [Base]
all_models = (User,)
"""
        }
    )

    assert result.applicability is SqlAlchemyApplicability.PRESENT
    assert [table.name for table in result.snapshot.entities] == ["users"]
    assert result.snapshot.diagnostics == ()
    assert result.snapshot.coverage.unknown_declarations == 0
    assert result.snapshot.partial_safe is False


def test_qualified_declarative_base_rebinding_is_unknown() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
import sqlalchemy.orm as orm

orm.DeclarativeBase = object

class User(orm.DeclarativeBase):
    __tablename__ = "users"
"""
        }
    )

    assert result.applicability is SqlAlchemyApplicability.INDETERMINATE
    assert result.snapshot.entities == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-006"]
    assert result.snapshot.partial_safe is True


def test_qualified_declarative_base_delete_is_unknown() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
import sqlalchemy.orm as orm

del orm.DeclarativeBase

class User(orm.DeclarativeBase):
    __tablename__ = "users"
"""
        }
    )

    assert result.applicability is SqlAlchemyApplicability.INDETERMINATE
    assert result.snapshot.entities == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-006"]
    assert result.snapshot.partial_safe is True


def test_qualified_table_rebinding_is_unknown() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
import sqlalchemy as sa

sa.Table = replacement
users = sa.Table("users", object())
"""
        }
    )

    assert result.applicability is SqlAlchemyApplicability.INDETERMINATE
    assert result.snapshot.entities == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-007"]
    assert result.snapshot.partial_safe is True


def test_repository_module_attribute_rebinding_is_unknown() -> None:
    result = _analyze(
        {
            "src/pkg/base.py": b"""
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
""",
            "src/pkg/__init__.py": b"from .base import Base\n",
            "src/pkg/models.py": b"""
import pkg as local_pkg

local_pkg.Base = replacement

class User(local_pkg.Base):
    __tablename__ = "users"
""",
        }
    )

    assert result.applicability is SqlAlchemyApplicability.PRESENT
    assert result.snapshot.entities == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-006"]
    assert result.snapshot.partial_safe is True


def test_qualified_declarative_base_mutation_taints_importfrom_binding() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
import sqlalchemy.orm as orm

orm.DeclarativeBase = object
from sqlalchemy.orm import DeclarativeBase

class User(DeclarativeBase):
    __tablename__ = "users"
"""
        }
    )

    assert result.applicability is SqlAlchemyApplicability.INDETERMINATE
    assert result.snapshot.entities == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-006"]
    assert result.snapshot.partial_safe is True


def test_qualified_table_mutation_taints_importfrom_binding() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
import sqlalchemy as sa

sa.Table = replacement
from sqlalchemy import Table

users = Table("users", object())
"""
        }
    )

    assert result.applicability is SqlAlchemyApplicability.INDETERMINATE
    assert result.snapshot.entities == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-007"]
    assert result.snapshot.partial_safe is True


def test_nested_imported_module_alias_table_mutation_is_unknown() -> None:
    result = _analyze(
        {
            "src/aliases.py": b"import sqlalchemy as sa\n",
            "src/models.py": b"""
import aliases

aliases.sa.Table = replacement
users = aliases.sa.Table("users", object())
""",
        }
    )

    assert result.applicability is SqlAlchemyApplicability.INDETERMINATE
    assert result.snapshot.entities == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-007"]
    assert result.snapshot.partial_safe is True


def test_nested_imported_module_alias_declarative_base_mutation_is_unknown() -> None:
    result = _analyze(
        {
            "src/aliases.py": b"import sqlalchemy.orm as orm\n",
            "src/models.py": b"""
import aliases

aliases.orm.DeclarativeBase = object

class User(aliases.orm.DeclarativeBase):
    __tablename__ = "users"
""",
        }
    )

    assert result.applicability is SqlAlchemyApplicability.INDETERMINATE
    assert result.snapshot.entities == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-006"]
    assert result.snapshot.partial_safe is True


def test_nested_module_alias_mutation_taints_direct_source_import() -> None:
    result = _analyze(
        {
            "src/aliases.py": b"import sqlalchemy as sa\n",
            "src/mutator.py": b"""
import aliases

aliases.sa.Table = replacement
""",
            "src/models.py": b"""
from sqlalchemy import Table

users = Table("users", object())
""",
        }
    )

    assert result.applicability is SqlAlchemyApplicability.INDETERMINATE
    assert result.snapshot.entities == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-007"]
    assert result.snapshot.partial_safe is True


def test_importfrom_module_alias_mutation_taints_direct_declarative_base_import() -> None:
    result = _analyze(
        {
            "src/aliases.py": b"from sqlalchemy import orm\n",
            "src/models.py": b"""
import aliases

aliases.orm.DeclarativeBase = object
from sqlalchemy.orm import DeclarativeBase

class User(DeclarativeBase):
    __tablename__ = "users"
""",
        }
    )

    assert result.applicability is SqlAlchemyApplicability.INDETERMINATE
    assert result.snapshot.entities == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-006"]
    assert result.snapshot.partial_safe is True


def test_importfrom_module_alias_mutation_taints_direct_table_import() -> None:
    result = _analyze(
        {
            "src/aliases.py": b"from sqlalchemy import schema\n",
            "src/models.py": b"""
import aliases

aliases.schema.Table = replacement
from sqlalchemy import Table

users = Table("users", object())
""",
        }
    )

    assert result.applicability is SqlAlchemyApplicability.INDETERMINATE
    assert result.snapshot.entities == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-007"]
    assert result.snapshot.partial_safe is True


def test_repository_reexported_module_alias_mutation_taints_source_import() -> None:
    result = _analyze(
        {
            "src/bridge.py": b"from sqlalchemy import orm\n",
            "src/aliases.py": b"from bridge import orm\n",
            "src/models.py": b"""
import aliases

aliases.orm.DeclarativeBase = object
from sqlalchemy.orm import DeclarativeBase

class User(DeclarativeBase):
    __tablename__ = "users"
""",
        }
    )

    assert result.applicability is SqlAlchemyApplicability.INDETERMINATE
    assert result.snapshot.entities == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-006"]
    assert result.snapshot.partial_safe is True


def test_rebound_importfrom_module_alias_does_not_taint_source_import() -> None:
    result = _analyze(
        {
            "src/aliases.py": b"""
from sqlalchemy import orm

class Replacement:
    pass

orm = Replacement()
""",
            "src/models.py": b"""
import aliases

aliases.orm.DeclarativeBase = object
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
""",
        }
    )

    assert result.applicability is SqlAlchemyApplicability.PRESENT
    assert [table.name for table in result.snapshot.entities] == ["users"]
    assert result.snapshot.diagnostics == ()
    assert result.snapshot.partial_safe is False


def test_rebound_imported_module_alias_does_not_taint_source_import() -> None:
    result = _analyze(
        {
            "src/aliases.py": b"""
import sqlalchemy as sa

class Replacement:
    pass

sa = Replacement()
""",
            "src/models.py": b"""
import aliases

aliases.sa.Table = replacement
from sqlalchemy import Table

users = Table("users", object())
""",
        }
    )

    assert result.applicability is SqlAlchemyApplicability.PRESENT
    assert [table.name for table in result.snapshot.entities] == ["users"]
    assert result.snapshot.diagnostics == ()
    assert result.snapshot.partial_safe is False


def test_conditionally_rebound_importfrom_module_alias_taints_source_import() -> None:
    result = _analyze(
        {
            "src/aliases.py": b"""
from sqlalchemy import orm

class Replacement:
    pass

if condition:
    orm = Replacement()
""",
            "src/models.py": b"""
import aliases

aliases.orm.DeclarativeBase = object
from sqlalchemy.orm import DeclarativeBase

class User(DeclarativeBase):
    __tablename__ = "users"
""",
        }
    )

    assert result.applicability is SqlAlchemyApplicability.INDETERMINATE
    assert result.snapshot.entities == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-006"]
    assert result.snapshot.partial_safe is True


def test_conditionally_rebound_imported_module_alias_taints_source_import() -> None:
    result = _analyze(
        {
            "src/aliases.py": b"""
import sqlalchemy as sa

class Replacement:
    pass

if condition:
    sa = Replacement()
""",
            "src/models.py": b"""
import aliases

aliases.sa.Table = replacement
from sqlalchemy import Table

users = Table("users", object())
""",
        }
    )

    assert result.applicability is SqlAlchemyApplicability.INDETERMINATE
    assert result.snapshot.entities == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-007"]
    assert result.snapshot.partial_safe is True


def test_later_definite_rebind_invalidates_conditional_module_alias() -> None:
    result = _analyze(
        {
            "src/aliases.py": b"""
if condition:
    from sqlalchemy import orm

class Replacement:
    pass

orm = Replacement()
""",
            "src/models.py": b"""
import aliases

aliases.orm.DeclarativeBase = object
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
""",
        }
    )

    assert result.applicability is SqlAlchemyApplicability.PRESENT
    assert [table.name for table in result.snapshot.entities] == ["users"]
    assert result.snapshot.diagnostics == ()
    assert result.snapshot.partial_safe is False


def test_repository_attribute_mutation_taints_importfrom_binding() -> None:
    result = _analyze(
        {
            "src/pkg/base.py": b"""
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
""",
            "src/pkg/__init__.py": b"from .base import Base\n",
            "src/pkg/models.py": b"""
import pkg

pkg.Base = replacement
from pkg import Base

class User(Base):
    __tablename__ = "users"
""",
        }
    )

    assert result.applicability is SqlAlchemyApplicability.PRESENT
    assert result.snapshot.entities == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-006"]
    assert result.snapshot.partial_safe is True


def test_reexport_attribute_mutation_does_not_taint_direct_source_import() -> None:
    result = _analyze(
        {
            "src/compat.py": b"from sqlalchemy.orm import DeclarativeBase\n",
            "src/mutator.py": b"""
import compat

compat.DeclarativeBase = object
""",
            "src/models.py": b"""
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
""",
        }
    )

    assert result.applicability is SqlAlchemyApplicability.PRESENT
    assert [table.name for table in result.snapshot.entities] == ["users"]
    assert result.snapshot.diagnostics == ()
    assert result.snapshot.partial_safe is False


def test_reexport_attribute_mutation_taints_reexport_importfrom_binding() -> None:
    result = _analyze(
        {
            "src/compat.py": b"from sqlalchemy.orm import DeclarativeBase\n",
            "src/models.py": b"""
import compat

compat.DeclarativeBase = object
from compat import DeclarativeBase

class User(DeclarativeBase):
    __tablename__ = "users"
""",
        }
    )

    assert result.applicability is SqlAlchemyApplicability.INDETERMINATE
    assert result.snapshot.entities == ()
    assert [item.code.value for item in result.snapshot.diagnostics] == ["CSV-SA-006"]
    assert result.snapshot.partial_safe is True


def test_unrelated_or_function_local_namespace_mutation_does_not_taint_base() -> None:
    result = _analyze(
        {
            "src/models.py": b"""
import sqlalchemy.orm as orm

orm.unrelated = object

def helper():
    orm.DeclarativeBase = object

from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
"""
        }
    )

    assert result.applicability is SqlAlchemyApplicability.PRESENT
    assert [table.name for table in result.snapshot.entities] == ["users"]
    assert result.snapshot.diagnostics == ()
    assert result.snapshot.partial_safe is False
