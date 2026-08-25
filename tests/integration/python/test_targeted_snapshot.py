from pathlib import Path

from code_structure_viz.adapters.python.analyzer import PythonSnapshotAnalyzer
from code_structure_viz.adapters.python.module_index import PythonModuleIndex
from code_structure_viz.adapters.python.selection import PythonTargetSelector
from code_structure_viz.core.config import PythonConfig
from code_structure_viz.core.outcomes import DomainStatus
from code_structure_viz.source.git_repository import GitRepositoryReader
from code_structure_viz.source.source_view import SourceViewBuilder
from code_structure_viz.source.targets import ClassTarget
from tests.helpers.fixture_repo import commit_all, copy_fixture_repository, git


def test_targeted_fixture_runs_from_real_git_bytes_through_static_selection(
    tmp_path: Path,
) -> None:
    repo = copy_fixture_repository("targeted", tmp_path / "repo")
    git(repo, "init", "--quiet", "--initial-branch=main")
    commit_all(repo)
    reader = GitRepositoryReader(repo)
    source_view = SourceViewBuilder(repo, tmp_path / "stage").build(
        reader.resolve_head_state(),
        reader.enumerate_path_entries(),
        PythonConfig(("src",), ("**/*.py",), ()),
    )

    analysis = PythonSnapshotAnalyzer().analyze(
        PythonModuleIndex.build(source_view, PythonConfig(("src",), ("**/*.py",), ()))
    )
    result = PythonTargetSelector().select(analysis, (ClassTarget("app.a.A"),), 0, 1)

    assert result.status is DomainStatus.COMPLETE
    assert result.snapshot is not None
    assert result.coverage.selected_modules == ("app.a", "app.b")
    assert tuple(item.name for item in result.snapshot.entities) == ("A", "B")
    assert {item.target.name for item in result.snapshot.relations} == {
        "app.b",
        "app.b.B",
    }
    assert result.diagnostics == ()
