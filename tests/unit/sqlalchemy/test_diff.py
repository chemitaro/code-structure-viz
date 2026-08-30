from __future__ import annotations

import hashlib
import json
from pathlib import PurePosixPath
from typing import cast

from code_structure_viz.adapters.sqlalchemy.analyzer import SqlAlchemySnapshotAnalyzer
from code_structure_viz.adapters.sqlalchemy.diff import SqlAlchemyDiffer
from code_structure_viz.adapters.sqlalchemy.model import SqlAlchemySnapshot
from code_structure_viz.adapters.sqlalchemy.plantuml import render_sqlalchemy_diff
from code_structure_viz.adapters.sqlalchemy.semantic_json import (
    render_sqlalchemy_diff as render_json_diff,
)
from code_structure_viz.core.config import PythonConfig
from code_structure_viz.source.file_changes import FileChangeSet
from code_structure_viz.source.python_modules import PythonSourceIndex
from code_structure_viz.source.source_view import SourceFile, SourceFileKind, SourceView


def _snapshot(source: bytes) -> SqlAlchemySnapshot:
    source_file = SourceFile(
        PurePosixPath("src/models.py"),
        SourceFileKind.REGULAR,
        None,
        len(source),
        hashlib.sha256(source).hexdigest(),
        source,
    )
    view = SourceView("1" * 40, (source_file,), (), hashlib.sha256(source).hexdigest())
    return (
        SqlAlchemySnapshotAnalyzer()
        .analyze(PythonSourceIndex.build(view, PythonConfig(("src",), ("**/*.py",), ())))
        .snapshot
    )


def test_exact_id_comparison_adds_tables_and_modifies_rows() -> None:
    before = _snapshot(
        b"""
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    name: Mapped[str] = mapped_column(nullable=True)
"""
    )
    after = _snapshot(
        b"""
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    name: Mapped[str] = mapped_column(nullable=False)
class Team(Base):
    __tablename__ = "teams"
"""
    )

    result = SqlAlchemyDiffer().compare(before, after)

    assert [delta.status.value for delta in result.entities] == ["added"]
    assert result.entities[0].before is None
    added_table = cast(dict[str, object], result.entities[0].after)
    assert added_table["name"] == "teams"
    assert [delta.status.value for delta in result.members] == ["modified"]
    before_row = cast(dict[str, object], result.members[0].before)
    after_row = cast(dict[str, object], result.members[0].after)
    assert before_row["nullable"] is True
    assert after_row["nullable"] is False
    assert result.matching == ()


def test_provenance_only_changes_are_ignored_and_id_changes_are_remove_add() -> None:
    before = _snapshot(
        b"""
from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
class Base(DeclarativeBase): pass
class Account(Base): __tablename__ = "accounts"
class User(Base):
    __tablename__ = "users"
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
"""
    )
    after = _snapshot(
        b"""
from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase): pass
class RenamedAccount(Base): __tablename__ = "renamed_accounts"
class RenamedUser(Base):
    __tablename__ = "users"
    account_id: Mapped[int] = mapped_column(ForeignKey("renamed_accounts.id"))
"""
    )

    result = SqlAlchemyDiffer().compare(before, after)

    assert {delta.status.value for delta in result.entities} == {"removed", "added"}
    assert {delta.status.value for delta in result.relations} == {"removed", "added"}
    assert [delta.identity for delta in result.entities] == sorted(
        (delta.identity for delta in result.entities), key=lambda value: value.encode("utf-8")
    )
    assert [delta.identity for delta in result.relations] == sorted(
        (delta.identity for delta in result.relations), key=lambda value: value.encode("utf-8")
    )
    assert all(delta.status.value != "modified" for delta in result.entities)
    assert all(delta.status.value != "modified" for delta in result.relations)
    rendered = render_sqlalchemy_diff(result)
    assert b"foreign_key" in rendered
    assert b"- relation foreign_key" in rendered


def test_source_and_mapping_provenance_only_changes_have_no_delta() -> None:
    before = _snapshot(
        b"""
from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
class Base(DeclarativeBase): pass
class Account(Base): __tablename__ = "accounts"
class User(Base):
    __tablename__ = "users"
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
"""
    )
    after = _snapshot(
        b"""
from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase): pass
class AccountRecord(Base): __tablename__ = "accounts"
class UserRecord(Base):
    __tablename__ = "users"
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
"""
    )

    result = SqlAlchemyDiffer().compare(before, after)

    assert result.entities == ()
    assert result.members == ()
    assert result.relations == ()


def test_presence_mapping_distinguishes_absence_from_analysis_failure() -> None:
    snapshot = _snapshot(
        b"""
from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase): pass
class User(Base): __tablename__ = "users"
"""
    )

    absent = SqlAlchemyDiffer().compare(None, None)
    added = SqlAlchemyDiffer().compare(None, snapshot)
    failed = SqlAlchemyDiffer().compare(None, snapshot, before_analysis_failed=True)

    assert absent.status == "not_applicable"
    assert absent.before.kind.value == "canonical-empty-side"
    assert absent.before.digest == absent.after.digest
    assert added.status == "complete"
    assert {delta.status.value for delta in added.entities} == {"added"}
    assert failed.status == "incomplete"
    assert failed.entities == ()
    assert failed.members == ()
    assert failed.relations == ()


def test_impact_traverses_internal_relation_union_from_changed_row_owner() -> None:
    before = _snapshot(
        b"""
from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
class Base(DeclarativeBase): pass
class Account(Base): __tablename__ = "accounts"
class User(Base):
    __tablename__ = "users"
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    name: Mapped[str] = mapped_column(nullable=True)
"""
    )
    after = _snapshot(
        b"""
from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
class Base(DeclarativeBase): pass
class Account(Base): __tablename__ = "accounts"
class User(Base):
    __tablename__ = "users"
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    name: Mapped[str] = mapped_column(nullable=False)
"""
    )

    result = SqlAlchemyDiffer().compare(before, after, downstream_depth=1)
    user_id = next(item.id for item in after.entities if item.name == "users")
    account_id = next(item.id for item in after.entities if item.name == "accounts")

    assert result.seeds == (user_id,)
    assert result.impact.upstream == ()
    assert result.impact.downstream == (account_id,)
    assert result.entity_count == 2
    assert b"foreign_key" in render_sqlalchemy_diff(result)


def test_diff_renderers_expose_safe_delta_and_visible_markers() -> None:
    before = _snapshot(
        b"""
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    name: Mapped[str] = mapped_column(nullable=True)
"""
    )
    after = _snapshot(
        b"""
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    name: Mapped[str] = mapped_column(nullable=False)
class Team(Base): __tablename__ = "teams"
"""
    )
    result = SqlAlchemyDiffer().compare(before, after)
    file_changes = FileChangeSet((), before="1" * 40, after="2" * 40)

    semantic = render_json_diff(result, file_changes)
    plantuml = render_sqlalchemy_diff(result)
    value = json.loads(semantic)

    assert value["domain"] == "sqlalchemy"
    assert value["semantic_change_set"]["matching"] == []
    assert value["semantic_change_set"]["entities"][0]["status"] == "added"
    assert value["semantic_change_set"]["members"][0]["status"] == "modified"
    assert b"title SQLAlchemy ER diff" in plantuml
    assert b"+ teams" in plantuml
    assert b"~ before name : string (str) <<NULL>>" in plantuml
    assert b"~ after * name : string (str) <<NN>>" in plantuml
    assert b"src/models.py" not in plantuml


def test_modified_row_plantuml_uses_typed_safe_before_and_after_lines() -> None:
    before = _snapshot(
        b"""
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    name: Mapped[int] = mapped_column()
"""
    )
    after = _snapshot(
        b"""
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    name: Mapped[str] = mapped_column()
"""
    )

    plantuml = render_sqlalchemy_diff(SqlAlchemyDiffer().compare(before, after))

    assert b"~ before name : integer" in plantuml
    assert b"~ after name : string" in plantuml
    assert b"[changed]" not in plantuml


def test_modified_column_plantuml_supplements_default_only_safe_change() -> None:
    before = _snapshot(
        b"""
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    name: Mapped[str] = mapped_column()
"""
    )
    after = _snapshot(
        b"""
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    name: Mapped[str] = mapped_column(default="DO_NOT_RENDER")
"""
    )

    plantuml = render_sqlalchemy_diff(SqlAlchemyDiffer().compare(before, after))

    assert b"| default=-" in plantuml
    assert b"| default=[redacted:literal]" in plantuml
    assert b"DO_NOT_RENDER" not in plantuml


def test_modified_column_plantuml_supplements_type_parameter_only_safe_change() -> None:
    before = _snapshot(
        b"""
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    name: Mapped[str] = mapped_column(String)
"""
    )
    after = _snapshot(
        b"""
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    name: Mapped[str] = mapped_column(String(255))
"""
    )

    plantuml = render_sqlalchemy_diff(SqlAlchemyDiffer().compare(before, after))

    assert b"| type.parameters=-" in plantuml
    assert b"| type.parameters=[redacted:literal]" in plantuml
    assert b"255" not in plantuml


def test_modified_column_plantuml_supplements_collapsed_full_type_name_change() -> None:
    before = _snapshot(
        b"""
import pkg_a
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    value: Mapped[object] = mapped_column(pkg_a.CustomType)
"""
    )
    after = _snapshot(
        b"""
import pkg_b
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    value: Mapped[object] = mapped_column(pkg_b.CustomType)
"""
    )

    plantuml = render_sqlalchemy_diff(SqlAlchemyDiffer().compare(before, after))

    assert b"| type.name=pkg_a.CustomType" in plantuml
    assert b"| type.name=pkg_b.CustomType" in plantuml


def test_modified_column_plantuml_supplements_type_names_with_same_compact_display() -> None:
    before = _snapshot(
        b"""
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    value: Mapped[float] = mapped_column()
"""
    )
    after = _snapshot(
        b"""
from sqlalchemy import Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    value: Mapped[float] = mapped_column(Float)
"""
    )

    result = SqlAlchemyDiffer().compare(before, after)
    plantuml = render_sqlalchemy_diff(result)

    assert [item.status.value for item in result.members] == ["modified"]
    assert b"| type.name=builtins.float" in plantuml
    assert b"| type.name=sqlalchemy.Float" in plantuml


def test_modified_column_plantuml_supplements_collapsed_compact_marker_changes() -> None:
    before = _snapshot(
        b"""
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    value: Mapped[int] = mapped_column(
        primary_key=True,
        nullable=True,
        unique=False,
        index=False,
    )
"""
    )
    after = _snapshot(
        b"""
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    value: Mapped[int] = mapped_column(primary_key=True, nullable=False)
"""
    )

    plantuml = render_sqlalchemy_diff(SqlAlchemyDiffer().compare(before, after))

    assert b"| index=false nullable=true unique=false" in plantuml
    assert b"| index=null nullable=false unique=null" in plantuml


def test_modified_relationship_plantuml_supplements_join_and_order_only_safe_changes() -> None:
    before = _snapshot(
        b"""
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship
class Base(DeclarativeBase): pass
class Child(Base): __tablename__ = "children"
class Parent(Base):
    __tablename__ = "parents"
    children: Mapped[list["Child"]] = relationship("Child")
"""
    )
    after = _snapshot(
        b"""
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship
class Base(DeclarativeBase): pass
class Child(Base): __tablename__ = "children"
class Parent(Base):
    __tablename__ = "parents"
    children: Mapped[list["Child"]] = relationship(
        "Child",
        primaryjoin="Parent.id == Child.parent_id",
        order_by="Child.id",
    )
"""
    )

    plantuml = render_sqlalchemy_diff(SqlAlchemyDiffer().compare(before, after))

    assert b"| order_by=- primaryjoin=-" in plantuml
    assert b"| order_by=[redacted:literal] primaryjoin=[redacted:literal]" in plantuml
    assert b"Parent.id == Child.parent_id" not in plantuml
    assert b"Child.id" not in plantuml


def test_modified_relationship_plantuml_distinguishes_absent_back_populates_from_dash() -> None:
    before = _snapshot(
        b"""
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship
class Base(DeclarativeBase): pass
class Child(Base): __tablename__ = "children"
class Parent(Base):
    __tablename__ = "parents"
    children: Mapped[list["Child"]] = relationship("Child")
"""
    )
    after = _snapshot(
        b"""
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship
class Base(DeclarativeBase): pass
class Child(Base): __tablename__ = "children"
class Parent(Base):
    __tablename__ = "parents"
    children: Mapped[list["Child"]] = relationship("Child", back_populates="-")
"""
    )

    result = SqlAlchemyDiffer().compare(before, after)
    plantuml = render_sqlalchemy_diff(result)

    assert [item.status.value for item in result.members] == ["modified"]
    assert b"back_populates.presence=absent" in plantuml
    assert b"back_populates.presence=present" in plantuml


def test_modified_relationship_plantuml_distinguishes_absent_secondary_from_dash_table() -> None:
    before = _snapshot(
        b"""
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship
class Base(DeclarativeBase): pass
class Child(Base): __tablename__ = "children"
class Parent(Base):
    __tablename__ = "parents"
    children: Mapped[list["Child"]] = relationship("Child")
"""
    )
    after = _snapshot(
        b"""
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship
class Base(DeclarativeBase): pass
class Child(Base): __tablename__ = "children"
class Parent(Base):
    __tablename__ = "parents"
    children: Mapped[list["Child"]] = relationship("Child", secondary="-")
"""
    )

    result = SqlAlchemyDiffer().compare(before, after)
    plantuml = render_sqlalchemy_diff(result)

    assert [item.status.value for item in result.members] == ["modified"]
    assert b"secondary.presence=absent" in plantuml
    assert b"secondary.presence=present" in plantuml


def test_named_foreign_key_plantuml_supplements_collapsed_target_resolution_change() -> None:
    before = _snapshot(
        b"""
from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
class Base(DeclarativeBase): pass
class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = {"schema": "audit"}
class User(Base):
    __tablename__ = "users"
    account_id: Mapped[int] = mapped_column(
        ForeignKey("audit.accounts.id", name="fk_user_account")
    )
"""
    )
    after = _snapshot(
        b"""
from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    account_id: Mapped[int] = mapped_column(
        ForeignKey("audit.accounts.id", name="fk_user_account")
    )
"""
    )

    result = SqlAlchemyDiffer().compare(before, after)
    plantuml = render_sqlalchemy_diff(result)

    assert [item.status.value for item in result.members] == ["modified"]
    assert b"target.resolution=internal" in plantuml
    assert b"target.resolution=external" in plantuml
    assert b"target.id=sqlalchemy_U003A_table_U003A_" in plantuml
    assert b"target.id=-" in plantuml


def test_removed_row_plantuml_keeps_typed_before_ghost() -> None:
    before = _snapshot(
        b"""
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    legacy: Mapped[str] = mapped_column(nullable=False)
"""
    )
    after = _snapshot(
        b"""
from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase): pass
class User(Base): __tablename__ = "users"
"""
    )

    removed = render_sqlalchemy_diff(SqlAlchemyDiffer().compare(before, after))
    added = render_sqlalchemy_diff(SqlAlchemyDiffer().compare(after, before))

    assert b"- * legacy : string" in removed
    assert b"- column legacy" not in removed
    assert b"+ * legacy : string" in added
    assert b"+ column legacy" not in added


def test_diff_plantuml_qualifies_same_name_tables_with_schema() -> None:
    before = _snapshot(
        b"""
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
class Base(DeclarativeBase): pass
class AuditUser(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "audit"}
    name: Mapped[str] = mapped_column(nullable=True)
class PublicUser(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}
    name: Mapped[str] = mapped_column(nullable=True)
"""
    )
    after = _snapshot(
        b"""
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
class Base(DeclarativeBase): pass
class AuditUser(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "audit"}
    name: Mapped[str] = mapped_column(nullable=False)
class PublicUser(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}
    name: Mapped[str] = mapped_column(nullable=False)
"""
    )

    plantuml = render_sqlalchemy_diff(SqlAlchemyDiffer().compare(before, after))

    assert b'entity "~ audit.users"' in plantuml
    assert b'entity "~ public.users"' in plantuml


def test_removed_relation_plantuml_keeps_before_only_er_evidence() -> None:
    before = _snapshot(
        b"""
from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
class Base(DeclarativeBase): pass
class Account(Base): __tablename__ = "accounts"
class User(Base):
    __tablename__ = "users"
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
"""
    )
    after = _snapshot(
        b"""
from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase): pass
class Account(Base): __tablename__ = "accounts"
class User(Base): __tablename__ = "users"
"""
    )

    result = SqlAlchemyDiffer().compare(before, after)
    plantuml = render_sqlalchemy_diff(result)

    assert result.after.snapshot is not None
    assert result.after.snapshot.relations == ()
    assert b": foreign_key <unnamed>" in plantuml
    assert b'note "- relation foreign_key"' in plantuml
