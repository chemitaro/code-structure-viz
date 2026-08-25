import hashlib
from pathlib import PurePosixPath

from code_structure_viz.adapters.python.analyzer import (
    PythonAnalysisResult,
    PythonSnapshotAnalyzer,
)
from code_structure_viz.adapters.python.module_index import PythonModuleIndex
from code_structure_viz.adapters.python.selection import PythonTargetSelector
from code_structure_viz.core.config import PythonConfig
from code_structure_viz.core.outcomes import DomainStatus, IncompleteKind
from code_structure_viz.source.source_view import SourceFile, SourceFileKind, SourceView
from code_structure_viz.source.targets import ClassTarget, ModuleTarget, PathTarget


def _analysis(files: dict[str, bytes]) -> PythonAnalysisResult:
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
    config = PythonConfig(("src",), ("**/*.py",), ())
    return PythonSnapshotAnalyzer().analyze(PythonModuleIndex.build(view, config))


def test_not_applicable_is_only_whole_mode_with_no_candidates_or_failures() -> None:
    result = PythonTargetSelector().select(_analysis({}), (), 1, 1)

    assert result.status is DomainStatus.NOT_APPLICABLE
    assert result.snapshot is None
    assert result.incomplete_kind is None
    assert result.coverage.candidate_files == 0


def test_whole_mode_keeps_every_safe_module_including_classless_modules() -> None:
    analysis = _analysis(
        {
            "src/app/a.py": b"import app.b\nclass A: pass\n",
            "src/app/b.py": b"VALUE = 1\n",
            "src/app/c.py": b"class C: pass\n",
        }
    )

    result = PythonTargetSelector().select(analysis, (), 0, 0)

    assert result.status is DomainStatus.COMPLETE
    assert result.snapshot is not None
    assert result.coverage.selected_modules == ("app.a", "app.b", "app.c")
    assert tuple(entity.name for entity in result.snapshot.entities) == ("A", "C")
    assert len(result.snapshot.relations) == 1
    assert result.snapshot.relations[0].target.name == "app.b"
    assert result.coverage.frontier == ()


def test_targeted_downstream_and_upstream_traversal_use_zero_cost_membership() -> None:
    analysis = _analysis(
        {
            "src/app/a.py": b"import app.b\nclass A: pass\n",
            "src/app/b.py": b"VALUE = 1\n",
        }
    )

    depth_zero = PythonTargetSelector().select(analysis, (ModuleTarget("app.a"),), 0, 0)
    downstream = PythonTargetSelector().select(analysis, (ClassTarget("app.a.A"),), 0, 1)
    upstream = PythonTargetSelector().select(analysis, (ModuleTarget("app.b"),), 1, 0)

    assert depth_zero.coverage.selected_modules == ("app.a",)
    assert depth_zero.snapshot is not None and depth_zero.snapshot.relations == ()
    assert tuple(
        (item.direction.value, item.kind.value, item.reference, item.reason.value)
        for item in depth_zero.coverage.frontier
    ) == (("downstream", "module", "python:module:app.b", "depth_limit"),)
    assert downstream.coverage.selected_modules == ("app.a", "app.b")
    assert downstream.snapshot is not None and len(downstream.snapshot.relations) == 1
    assert upstream.coverage.selected_modules == ("app.a", "app.b")
    assert upstream.snapshot is not None and len(upstream.snapshot.entities) == 1


def test_path_and_multiple_targets_form_an_exact_union() -> None:
    analysis = _analysis(
        {
            "src/app/a.py": b"class A: pass\n",
            "src/app/b.py": b"class B: pass\n",
            "src/app/unrelated.py": b"class Unrelated: pass\n",
        }
    )

    result = PythonTargetSelector().select(
        analysis,
        (
            PathTarget(PurePosixPath("src/app/a.py")),
            ClassTarget("app.b.B"),
        ),
        0,
        0,
    )

    assert result.coverage.selected_modules == ("app.a", "app.b")
    assert result.snapshot is not None
    assert tuple(entity.name for entity in result.snapshot.entities) == ("A", "B")


def test_any_missing_target_makes_the_whole_targeted_payload_unavailable() -> None:
    analysis = _analysis({"src/app/a.py": b"class A: pass\n"})

    result = PythonTargetSelector().select(
        analysis,
        (
            ModuleTarget("app.a"),
            ModuleTarget("app.missing"),
            PathTarget(PurePosixPath("src/app/missing.py")),
            ClassTarget("app.a.Missing"),
        ),
        1,
        1,
    )

    assert result.status is DomainStatus.INCOMPLETE
    assert result.incomplete_kind is IncompleteKind.PAYLOAD_UNAVAILABLE
    assert result.snapshot is None
    missing = [item for item in result.diagnostics if item.code.value == "CSV-PY-006"]
    assert len(missing) == 3
    assert len(result.coverage.frontier) == 3
    assert result.coverage.selected_modules == ()


def test_zero_class_repository_with_missing_class_target_is_not_not_applicable() -> None:
    result = PythonTargetSelector().select(
        _analysis({"src/app/config.py": b"VALUE = 1\n"}),
        (ClassTarget("app.config.Missing"),),
        1,
        1,
    )

    assert result.status is DomainStatus.INCOMPLETE
    assert result.incomplete_kind is IncompleteKind.PAYLOAD_UNAVAILABLE
    assert result.snapshot is None
    assert [item.code.value for item in result.diagnostics] == ["CSV-PY-006"]


def test_failed_requested_file_keeps_file_and_target_diagnostics() -> None:
    result = PythonTargetSelector().select(
        _analysis({"src/app/broken.py": b"class Broken(\n"}),
        (PathTarget(PurePosixPath("src/app/broken.py")),),
        1,
        1,
    )

    assert result.incomplete_kind is IncompleteKind.PAYLOAD_UNAVAILABLE
    assert [item.code.value for item in result.diagnostics] == ["CSV-PY-006", "CSV-PY-003"]


def test_class_collision_target_is_ambiguous_and_has_no_safe_winner() -> None:
    result = PythonTargetSelector().select(
        _analysis({"src/app/duplicate.py": b"class Same: pass\nclass Same: pass\n"}),
        (ClassTarget("app.duplicate.Same"),),
        1,
        1,
    )

    assert result.incomplete_kind is IncompleteKind.PAYLOAD_UNAVAILABLE
    assert [item.code.value for item in result.diagnostics] == ["CSV-PY-007", "CSV-PY-012"]
