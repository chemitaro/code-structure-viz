from __future__ import annotations

import hashlib
import json
from pathlib import PurePosixPath
from typing import cast

import pytest

from code_structure_viz.adapters.sqlalchemy.analyzer import SqlAlchemySnapshotAnalyzer
from code_structure_viz.adapters.sqlalchemy.model import (
    SqlAlchemyCoverage,
    SqlAlchemyRedactionSummary,
    SqlAlchemyRowKind,
    SqlAlchemySnapshot,
)
from code_structure_viz.adapters.sqlalchemy.semantic_json import (
    SqlAlchemySemanticJsonRenderer,
    coverage_value,
    render_semantic_snapshot,
)
from code_structure_viz.core.config import PythonConfig
from code_structure_viz.source.python_modules import PythonSourceIndex
from code_structure_viz.source.source_view import SourceFile, SourceFileKind, SourceView
from code_structure_viz.source.targets import ClassTarget, ModuleTarget, PathTarget


def _analyze(files: dict[str, bytes]) -> tuple[SourceView, SqlAlchemySnapshot]:
    sources = tuple(
        SourceFile(
            PurePosixPath(path),
            SourceFileKind.REGULAR,
            None,
            len(content),
            hashlib.sha256(content).hexdigest(),
            content,
        )
        for path, content in sorted(files.items())
    )
    view = SourceView("1" * 40, sources, (), "b" * 64)
    result = SqlAlchemySnapshotAnalyzer().analyze(
        PythonSourceIndex.build(
            view,
            PythonConfig(("src",), ("**/*.py",), ()),
        )
    )
    return view, result.snapshot


def test_complete_empty_semantic_json_has_exact_field_order_and_one_lf() -> None:
    source = SourceView("1" * 40, (), (), "b" * 64)
    coverage = SqlAlchemyCoverage(
        candidate_files=0,
        parsed_files=0,
        failed_files=(),
        evidence_files=(),
        selected_modules=(),
        mapped_classes=0,
        association_tables=0,
        selected_entities=0,
        unknown_declarations=0,
        frontier=(),
        redaction=SqlAlchemyRedactionSummary.create(0),
    )
    snapshot = SqlAlchemySnapshot((), (), (), coverage, (), partial_safe=False)

    rendered = render_semantic_snapshot(snapshot, source, (), 1, 1)

    assert rendered == (
        b'{"type":"semantic_snapshot","schema":"code-structure-viz.semantic/v1",'
        b'"domain":"sqlalchemy","document_kind":"snapshot","status":"complete",'
        b'"source":{"schema":"code-structure-viz.source-view/v1","kind":"working-tree",'
        b'"head_commit":"1111111111111111111111111111111111111111",'
        b'"fingerprint":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",'
        b'"file_count":0},"request":{"targets":[],"upstream_depth":1,'
        b'"downstream_depth":1},"coverage":{"candidate_files":0,"parsed_files":0,'
        b'"failed_files":[],"evidence_files":[],"selected_modules":[],'
        b'"mapped_classes":0,"association_tables":0,"selected_entities":0,'
        b'"unknown_declarations":0,"frontier":[],"redaction":{'
        b'"rule_version":"code-structure-viz.sqlalchemy-redaction/v1",'
        b'"redacted_values":0}},"entities":[],"members":[],"relations":[],'
        b'"diagnostics":[]}\n'
    )


def test_renderer_serializes_every_closed_row_and_relation_shape_without_raw_values() -> None:
    source, snapshot = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Table, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

membership = Table("membership", object())

class Base(DeclarativeBase):
    pass

class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[int] = mapped_column(primary_key=True)

class Group(Base):
    __tablename__ = "groups"
    id: Mapped[int] = mapped_column(primary_key=True)

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        CheckConstraint(object(), name="ck_users_safe"),
        Index("ix_users_email", "email"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), default="DO_NOT_LEAK")
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    groups: Mapped[list["Group"]] = relationship(
        "Group", secondary=membership, primaryjoin=object()
    )

class Admin(User):
    __tablename__ = "admins"
"""
        }
    )
    rendered = SqlAlchemySemanticJsonRenderer(
        source_view=source,
        targets=(
            ClassTarget("models.User"),
            ModuleTarget("models"),
            PathTarget(PurePosixPath("src/models.py")),
        ),
        upstream_depth=2,
        downstream_depth=1,
    ).render(snapshot)
    value = json.loads(rendered)

    assert list(value) == [
        "type",
        "schema",
        "domain",
        "document_kind",
        "status",
        "source",
        "request",
        "coverage",
        "entities",
        "members",
        "relations",
        "diagnostics",
    ]
    assert value["request"]["targets"] == [
        {"kind": "path", "value": "src/models.py"},
        {"kind": "module", "value": "models"},
        {"kind": "class", "value": "models.User"},
    ]
    assert list(value["coverage"]) == [
        "candidate_files",
        "parsed_files",
        "failed_files",
        "evidence_files",
        "selected_modules",
        "mapped_classes",
        "association_tables",
        "selected_entities",
        "unknown_declarations",
        "frontier",
        "redaction",
    ]
    assert value["coverage"] == coverage_value(snapshot.coverage)
    assert all(
        list(entity)
        == [
            "id",
            "kind",
            "schema_name",
            "name",
            "display_name",
            "mapping_kind",
            "mapping_sources",
        ]
        for entity in value["entities"]
    )
    expected_row_keys = {
        "column": [
            "type",
            "nullable",
            "primary_key",
            "unique",
            "index",
            "default",
            "server_default",
            "onupdate",
            "server_onupdate",
            "computed",
            "identity",
        ],
        "primary_key": ["columns"],
        "unique": ["columns"],
        "check": ["expression"],
        "index": ["unique", "terms"],
        "foreign_key": ["local_columns", "target", "target_columns", "ondelete", "onupdate"],
        "relationship": [
            "target",
            "cardinality",
            "uselist",
            "back_populates",
            "secondary",
            "primaryjoin",
            "secondaryjoin",
            "order_by",
            "foreign_keys",
        ],
        "inheritance": ["target"],
        "association_table": [
            "source_table",
            "relationship_target",
            "relationship_member_id",
        ],
    }
    assert {member["kind"] for member in value["members"]} == {
        kind.value for kind in SqlAlchemyRowKind
    }
    for member in value["members"]:
        assert list(member) == [
            "id",
            "owner_id",
            "kind",
            "name",
            "source",
            *expected_row_keys[member["kind"]],
        ]
    assert all(
        list(relation)
        == [
            "id",
            "kind",
            "source_id",
            "target",
            "via_member_id",
            "role",
            "source",
        ]
        for relation in value["relations"]
    )
    assert rendered.endswith(b"\n") and not rendered.endswith(b"\n\n")
    assert not rendered.startswith(b"\xef\xbb\xbf")
    assert b"DO_NOT_LEAK" not in rendered
    assert b"utf8_byte_column" not in rendered


def test_partial_safe_adds_only_the_closed_incomplete_kind() -> None:
    source, snapshot = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase): pass
class Safe(Base): __tablename__ = "safe"
""",
            "src/broken.py": b"def broken(:\n",
        }
    )

    rendered = render_semantic_snapshot(snapshot, source, (), 0, 0)
    value = json.loads(rendered)

    assert list(value)[:7] == [
        "type",
        "schema",
        "domain",
        "document_kind",
        "status",
        "incomplete_kind",
        "source",
    ]
    assert value["status"] == "incomplete"
    assert value["incomplete_kind"] == "partial_safe"
    assert value["diagnostics"][0]["code"] == "CSV-SA-003"


def test_unknown_selected_member_is_always_serialized_as_partial_safe() -> None:
    source, snapshot = _analyze(
        {
            "src/models.py": b"""
from sqlalchemy.orm import DeclarativeBase, mapped_column
class Base(DeclarativeBase): pass
class Safe(Base):
    __tablename__ = "safe"
    dynamic = mapped_column(type_factory())
"""
        }
    )

    value = json.loads(render_semantic_snapshot(snapshot, source, (), 0, 0))

    assert value["status"] == "incomplete"
    assert value["incomplete_kind"] == "partial_safe"
    assert value["members"][0]["type"]["category"] == "unknown"
    assert [item["code"] for item in value["diagnostics"]] == ["CSV-SA-009"]
    assert value["coverage"]["unknown_declarations"] == 1
    assert value["coverage"]["frontier"][0]["direction"] == "failure"


def test_renderer_rejects_a_non_snapshot_payload() -> None:
    renderer = SqlAlchemySemanticJsonRenderer(
        source_view=SourceView(None, (), (), "c" * 64),
        targets=(),
        upstream_depth=0,
        downstream_depth=0,
    )

    with pytest.raises(ValueError, match="SQLAlchemy snapshot"):
        renderer.render(cast(SqlAlchemySnapshot, None))
