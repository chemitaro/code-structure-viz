from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import PurePosixPath

from code_structure_viz.adapters.sqlalchemy.analyzer import (
    SqlAlchemyAnalysisResult,
    SqlAlchemyApplicability,
    SqlAlchemySnapshotAnalyzer,
)
from code_structure_viz.adapters.sqlalchemy.model import (
    SqlAlchemyCoverage,
    SqlAlchemyFailedSource,
    SqlAlchemyFailedStage,
    SqlAlchemyFrontierDirection,
    SqlAlchemyFrontierReason,
    SqlAlchemyMappingSource,
    SqlAlchemyMappingSourceKind,
    SqlAlchemyRedactionSummary,
    SqlAlchemyRelationKind,
    SqlAlchemySnapshot,
    SqlAlchemySourceLocation,
    SqlAlchemySourceRange,
    SqlAlchemyTable,
    table_sort_key,
)
from code_structure_viz.adapters.sqlalchemy.selection import (
    SqlAlchemySelectionResult,
    SqlAlchemyTargetSelector,
)
from code_structure_viz.core.budget import EntityBudgetGate
from code_structure_viz.core.config import ConfigSource, PythonConfig
from code_structure_viz.core.diagnostics import DiagnosticCode, diagnostic
from code_structure_viz.core.outcomes import DomainStatus, IncompleteKind
from code_structure_viz.source.python_modules import PythonSourceIndex
from code_structure_viz.source.source_view import SourceFile, SourceFileKind, SourceView
from code_structure_viz.source.targets import ClassTarget, ModuleTarget, PathTarget


def _analysis(files: dict[str, bytes]) -> SqlAlchemyAnalysisResult:
    source_files = tuple(
        SourceFile(
            PurePosixPath(path),
            SourceFileKind.REGULAR,
            None,
            len(data),
            hashlib.sha256(data).hexdigest(),
            data,
        )
        for path, data in sorted(files.items())
    )
    index = PythonSourceIndex.build(
        SourceView(None, source_files, (), "a" * 64),
        PythonConfig((".",), ("**/*.py",), ()),
    )
    return SqlAlchemySnapshotAnalyzer().analyze(index)


def _select(
    analysis: SqlAlchemyAnalysisResult,
    *targets: PathTarget | ModuleTarget | ClassTarget,
    upstream_depth: int = 0,
    downstream_depth: int = 0,
) -> SqlAlchemySelectionResult:
    return SqlAlchemyTargetSelector().select(
        analysis,
        targets,
        upstream_depth=upstream_depth,
        downstream_depth=downstream_depth,
    )


def _manual_analysis(
    table_count: int,
    *,
    shared_class_symbol: str | None = None,
) -> SqlAlchemyAnalysisResult:
    tables = []
    for index in range(table_count):
        symbol = shared_class_symbol or f"bulk.Model{index:04d}"
        tables.append(
            SqlAlchemyTable.create(
                schema_name=None,
                name=f"table_{index:04d}",
                mapping_sources=(
                    SqlAlchemyMappingSource(
                        kind=SqlAlchemyMappingSourceKind.DECLARATIVE_CLASS,
                        module="bulk",
                        symbol=symbol,
                        source=SqlAlchemySourceLocation(
                            path="src/bulk.py",
                            range=SqlAlchemySourceRange(
                                start_line=index + 1,
                                end_line=index + 1,
                            ),
                        ),
                    ),
                ),
            )
        )
    entities = tuple(sorted(tables, key=table_sort_key))
    coverage = SqlAlchemyCoverage(
        candidate_files=1,
        parsed_files=1,
        failed_files=(),
        evidence_files=("src/bulk.py",),
        selected_modules=("bulk",) if entities else (),
        mapped_classes=table_count,
        association_tables=0,
        selected_entities=table_count,
        unknown_declarations=0,
        frontier=(),
        redaction=SqlAlchemyRedactionSummary.create(0),
    )
    return SqlAlchemyAnalysisResult(
        snapshot=SqlAlchemySnapshot(
            entities=entities,
            members=(),
            relations=(),
            coverage=coverage,
            diagnostics=(),
            partial_safe=False,
        ),
        applicability=SqlAlchemyApplicability.PRESENT,
    )


def test_whole_selection_applies_the_status_matrix() -> None:
    selector = SqlAlchemyTargetSelector()

    absent = selector.select(
        _analysis({"src/plain.py": b"value = 1\n"}),
        (),
        upstream_depth=0,
        downstream_depth=0,
    )
    assert absent.status is DomainStatus.NOT_APPLICABLE
    assert absent.incomplete_kind is None
    assert absent.snapshot is None
    assert absent.diagnostics == ()

    empty_present = selector.select(
        _analysis(
            {
                "src/base.py": b"""
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
"""
            }
        ),
        (),
        upstream_depth=0,
        downstream_depth=0,
    )
    assert empty_present.status is DomainStatus.COMPLETE
    assert empty_present.incomplete_kind is None
    assert empty_present.snapshot is not None
    assert empty_present.snapshot.entities == ()

    unavailable = selector.select(
        _analysis({"src/broken.py": b"def broken(:\n"}),
        (),
        upstream_depth=0,
        downstream_depth=0,
    )
    assert unavailable.status is DomainStatus.INCOMPLETE
    assert unavailable.incomplete_kind is IncompleteKind.PAYLOAD_UNAVAILABLE
    assert unavailable.snapshot is None

    partial = selector.select(
        _analysis(
            {
                "src/models.py": b"""
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class Account(Base):
    __tablename__ = "account"
""",
                "src/broken.py": b"def broken(:\n",
            }
        ),
        (),
        upstream_depth=0,
        downstream_depth=0,
    )
    assert partial.status is DomainStatus.INCOMPLETE
    assert partial.incomplete_kind is IncompleteKind.PARTIAL_SAFE
    assert partial.snapshot is not None
    assert len(partial.snapshot.entities) == 1
    assert partial.snapshot.partial_safe is True

    base = _manual_analysis(1)
    unsafe_diagnostic = diagnostic(
        DiagnosticCode.SA_READ,
        domain="sqlalchemy",
        path="src/unsafe.py",
    )
    unsafe_coverage = replace(
        base.snapshot.coverage,
        failed_files=(
            SqlAlchemyFailedSource(
                "src/unsafe.py",
                SqlAlchemyFailedStage.PATH_SAFETY,
                DiagnosticCode.SA_READ,
            ),
        ),
    )
    unsafe_analysis = SqlAlchemyAnalysisResult(
        replace(
            base.snapshot,
            coverage=unsafe_coverage,
            diagnostics=(unsafe_diagnostic,),
            partial_safe=True,
        ),
        SqlAlchemyApplicability.PRESENT,
    )
    unsafe = _select(unsafe_analysis)
    assert unsafe.status is DomainStatus.INCOMPLETE
    assert unsafe.incomplete_kind is IncompleteKind.PAYLOAD_UNAVAILABLE
    assert unsafe.snapshot is None


def test_path_module_class_and_multi_target_union_are_exact() -> None:
    analysis = _analysis(
        {
            "pkg/a.py": b"""
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class A1(Base):
    __tablename__ = "a1"

class A2(Base):
    __tablename__ = "a2"
""",
            "pkg/b.py": b"""
from pkg.a import Base

class B(Base):
    __tablename__ = "b"
""",
        }
    )

    by_path = _select(analysis, PathTarget(PurePosixPath("pkg/a.py")))
    assert by_path.status is DomainStatus.COMPLETE
    assert by_path.snapshot is not None
    assert [entity.name for entity in by_path.snapshot.entities] == ["a1", "a2"]
    assert by_path.coverage.selected_modules == ("pkg.a",)

    by_module = _select(analysis, ModuleTarget("pkg.b"))
    assert by_module.snapshot is not None
    assert [entity.name for entity in by_module.snapshot.entities] == ["b"]

    by_class = _select(analysis, ClassTarget("pkg.a.A1"))
    assert by_class.snapshot is not None
    assert [entity.name for entity in by_class.snapshot.entities] == ["a1"]

    union = _select(
        analysis,
        PathTarget(PurePosixPath("pkg/a.py")),
        ClassTarget("pkg.b.B"),
        PathTarget(PurePosixPath("pkg/a.py")),
    )
    assert union.snapshot is not None
    assert [entity.name for entity in union.snapshot.entities] == ["a1", "a2", "b"]
    assert union.coverage.selected_modules == ("pkg.a", "pkg.b")


def test_any_missing_target_makes_the_explicit_selection_unavailable() -> None:
    analysis = _analysis(
        {
            "app/models.py": b"""
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class Present(Base):
    __tablename__ = "present"
"""
        }
    )
    result = _select(
        analysis,
        ClassTarget("app.models.Present"),
        ClassTarget("app.models.Missing"),
        ModuleTarget("missing.module"),
        PathTarget(PurePosixPath("missing/path.py")),
    )

    assert result.status is DomainStatus.INCOMPLETE
    assert result.incomplete_kind is IncompleteKind.PAYLOAD_UNAVAILABLE
    assert result.snapshot is None
    assert result.coverage.selected_entities == 0
    assert result.coverage.selected_modules == ()
    assert result.coverage.redaction.redacted_values == 0
    assert [diagnostic.code for diagnostic in result.diagnostics].count(
        DiagnosticCode.SA_TARGET_MISSING
    ) == 3
    assert {
        item.reason
        for item in result.coverage.frontier
        if item.reason is SqlAlchemyFrontierReason.TARGET_MISSING
    } == {SqlAlchemyFrontierReason.TARGET_MISSING}


def test_class_target_ambiguity_never_selects_a_winner() -> None:
    result = _select(
        _manual_analysis(2, shared_class_symbol="bulk.Shared"),
        ClassTarget("bulk.Shared"),
    )

    assert result.status is DomainStatus.INCOMPLETE
    assert result.incomplete_kind is IncompleteKind.PAYLOAD_UNAVAILABLE
    assert result.snapshot is None
    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        DiagnosticCode.SA_TARGET_AMBIGUOUS
    ]
    assert result.coverage.selected_entities == 0
    assert any(
        item.reason is SqlAlchemyFrontierReason.TARGET_AMBIGUOUS
        for item in result.coverage.frontier
    )


def test_upstream_and_downstream_bfs_are_independent_and_report_depth_frontier() -> None:
    analysis = _analysis(
        {
            "graph.py": b"""
from sqlalchemy import ForeignKey, Table
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

link = Table("links", object())

class Base(DeclarativeBase):
    pass

class C(Base):
    __tablename__ = "c"

class B(Base):
    __tablename__ = "b"
    c_id: Mapped[int] = mapped_column(ForeignKey("c.id"), default="DO_NOT_LEAK")

class A(Base):
    __tablename__ = "a"
    bs: Mapped[list["B"]] = relationship(
        "B",
        secondary=link,
        primaryjoin=object(),
    )
    outside: Mapped["vendor.External"] = relationship("vendor.External", uselist=False)

class D(A):
    __tablename__ = "d"
"""
        }
    )

    depth_zero = _select(
        analysis,
        ClassTarget("graph.A"),
        upstream_depth=0,
        downstream_depth=0,
    )
    assert depth_zero.snapshot is not None
    assert [entity.name for entity in depth_zero.snapshot.entities] == ["a"]
    assert depth_zero.snapshot.relations == ()
    assert {member.name for member in depth_zero.snapshot.members} == {"bs", "outside"}
    assert depth_zero.coverage.redaction.redacted_values == 1
    assert {
        (item.direction, item.reference)
        for item in depth_zero.coverage.frontier
        if item.reason is SqlAlchemyFrontierReason.DEPTH_LIMIT
    } == {
        (
            SqlAlchemyFrontierDirection.DOWNSTREAM,
            next(e.id for e in analysis.snapshot.entities if e.name == "b"),
        ),
        (
            SqlAlchemyFrontierDirection.DOWNSTREAM,
            next(e.id for e in analysis.snapshot.entities if e.name == "links"),
        ),
        (
            SqlAlchemyFrontierDirection.UPSTREAM,
            next(e.id for e in analysis.snapshot.entities if e.name == "d"),
        ),
    }

    depth_one = _select(
        analysis,
        ClassTarget("graph.A"),
        upstream_depth=1,
        downstream_depth=1,
    )
    assert depth_one.snapshot is not None
    assert {entity.name for entity in depth_one.snapshot.entities} == {"a", "b", "d", "links"}
    assert {relation.kind for relation in depth_one.snapshot.relations} == {
        SqlAlchemyRelationKind.ASSOCIATION,
        SqlAlchemyRelationKind.INHERITANCE,
        SqlAlchemyRelationKind.RELATIONSHIP,
    }
    assert depth_one.coverage.redaction.redacted_values == 2
    c_id = next(entity.id for entity in analysis.snapshot.entities if entity.name == "c")
    assert any(
        item.direction is SqlAlchemyFrontierDirection.DOWNSTREAM
        and item.reference == c_id
        and item.reason is SqlAlchemyFrontierReason.DEPTH_LIMIT
        for item in depth_one.coverage.frontier
    )
    assert not any(
        item.direction is SqlAlchemyFrontierDirection.UPSTREAM and item.reference == c_id
        for item in depth_one.coverage.frontier
    )

    depth_two = _select(
        analysis,
        ClassTarget("graph.A"),
        upstream_depth=0,
        downstream_depth=2,
    )
    assert depth_two.snapshot is not None
    assert {entity.name for entity in depth_two.snapshot.entities} == {"a", "b", "c", "links"}
    assert {relation.kind for relation in depth_two.snapshot.relations} == {
        SqlAlchemyRelationKind.ASSOCIATION,
        SqlAlchemyRelationKind.FOREIGN_KEY,
        SqlAlchemyRelationKind.RELATIONSHIP,
    }


def test_selected_coverage_recomputes_only_selection_owned_fields() -> None:
    analysis = _analysis(
        {
            "selected.py": b"""
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Selected(Base):
    __tablename__ = "selected"
    value: Mapped[int] = mapped_column(default="SELECTED_SECRET")
""",
            "other.py": b"""
from selected import Base
from sqlalchemy import Table
from sqlalchemy.orm import Mapped, mapped_column

association = Table("association", object())

class Other(Base):
    __tablename__ = "other"
    value: Mapped[int] = mapped_column(default="OTHER_SECRET")
""",
        }
    )
    result = _select(analysis, ClassTarget("selected.Selected"))

    assert result.snapshot is not None
    assert result.coverage.selected_modules == ("selected",)
    assert result.coverage.selected_entities == 1
    assert result.coverage.redaction.redacted_values == 1
    assert result.coverage.mapped_classes == analysis.snapshot.coverage.mapped_classes
    assert result.coverage.association_tables == analysis.snapshot.coverage.association_tables
    assert result.coverage.unknown_declarations == analysis.snapshot.coverage.unknown_declarations
    assert "SELECTED_SECRET" not in repr(result)
    assert "OTHER_SECRET" not in repr(result)


def test_entity_budget_uses_the_actual_selected_table_count() -> None:
    selector = SqlAlchemyTargetSelector()
    gate = EntityBudgetGate()

    selected_500 = selector.select(
        _manual_analysis(500),
        (),
        upstream_depth=0,
        downstream_depth=0,
    )
    selected_501 = selector.select(
        _manual_analysis(501),
        (),
        upstream_depth=0,
        downstream_depth=0,
    )
    targeted_one = selector.select(
        _manual_analysis(501),
        (ClassTarget("bulk.Model0000"),),
        upstream_depth=0,
        downstream_depth=0,
    )

    assert (
        gate.admit(
            actual=selected_500.coverage.selected_entities,
            requested=None,
            resolved=500,
            source=ConfigSource.BUILTIN,
            domain="sqlalchemy",
        ).admitted
        is True
    )
    assert (
        gate.admit(
            actual=selected_501.coverage.selected_entities,
            requested=None,
            resolved=500,
            source=ConfigSource.BUILTIN,
            domain="sqlalchemy",
        ).admitted
        is False
    )
    assert (
        gate.admit(
            actual=selected_501.coverage.selected_entities,
            requested=600,
            resolved=600,
            source=ConfigSource.EXPLICIT,
            domain="sqlalchemy",
        ).admitted
        is True
    )
    assert targeted_one.coverage.selected_entities == 1
