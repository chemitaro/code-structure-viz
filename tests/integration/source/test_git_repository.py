from __future__ import annotations

import os
import subprocess
from pathlib import Path, PurePosixPath

import pytest

from code_structure_viz.core.config import PythonConfig
from code_structure_viz.source.git_repository import (
    Commit,
    GitReadError,
    GitRepositoryReader,
    Unborn,
    UnrepresentableGitPathFatal,
)
from code_structure_viz.source.source_view import SourceViewBuilder
from tests.helpers.fixture_repo import commit_all, git, initialize_repository


def test_real_git_accepts_exact_root_and_rejects_nested_non_git_and_bare(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    initialize_repository(repo)
    nested = repo / "nested"
    nested.mkdir()

    assert GitRepositoryReader(repo).validate_repository_root() == repo.resolve()
    GitRepositoryReader(repo).validate_git_version()
    with pytest.raises(GitReadError) as nested_error:
        GitRepositoryReader(nested).validate_repository_root()
    assert nested_error.value.diagnostic.code.value == "CSV-REPO-001"

    non_git = tmp_path / "non-git"
    non_git.mkdir()
    with pytest.raises(GitReadError):
        GitRepositoryReader(non_git).validate_repository_root()

    bare = tmp_path / "bare.git"
    subprocess.run(
        ("git", "init", "--quiet", "--bare", str(bare)),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
    )
    with pytest.raises(GitReadError):
        GitRepositoryReader(bare).validate_repository_root()


def test_real_git_classifies_unborn_and_committed_head(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    initialize_repository(repo)
    reader = GitRepositoryReader(repo)

    assert reader.resolve_head_state() == Unborn("refs/heads/main")
    (repo / "README.md").write_text("fixture\n", encoding="utf-8")
    object_id = commit_all(repo)

    assert reader.resolve_head_state() == Commit(object_id)


def test_real_git_and_source_view_admit_tracked_and_unignored_untracked_python(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    initialize_repository(repo)
    (repo / ".gitignore").write_text("ignored.py\n", encoding="utf-8")
    (repo / "tracked.py").write_text("tracked = True\n", encoding="utf-8")
    (repo / "deleted.py").write_text("deleted = True\n", encoding="utf-8")
    commit_all(repo)
    (repo / "deleted.py").unlink()
    (repo / "untracked.py").write_text("untracked = True\n", encoding="utf-8")
    (repo / "ignored.py").write_text("ignored = True\n", encoding="utf-8")
    (repo / "types.pyi").write_text("value: int\n", encoding="utf-8")
    reader = GitRepositoryReader(repo)
    entries = reader.enumerate_path_entries()

    view = SourceViewBuilder(repo, tmp_path / "stage").build(
        reader.resolve_head_state(), entries, PythonConfig((".",), ("**/*.py",), ())
    )

    assert tuple(item.path for item in view.files) == (
        PurePosixPath("tracked.py"),
        PurePosixPath("untracked.py"),
    )
    assert PurePosixPath("ignored.py") not in tuple(entry.normalized for entry in entries)
    assert view.failures == ()


def test_real_git_non_utf8_path_stops_before_source_view(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    initialize_repository(repo)
    blob = subprocess.run(
        ("git", "-C", os.fsdecode(repo), "hash-object", "-w", "--stdin"),
        input=b"",
        capture_output=True,
        check=True,
    ).stdout.strip()
    subprocess.run(
        ("git", "-C", os.fsdecode(repo), "update-index", "-z", "--index-info"),
        input=b"100644 " + blob + b"\tbad-\xff.py\0",
        capture_output=True,
        check=True,
    )

    with pytest.raises(UnrepresentableGitPathFatal) as caught:
        GitRepositoryReader(repo).enumerate_path_entries()

    diagnostic = caught.value.diagnostic
    assert diagnostic.code.value == "CSV-SOURCE-003"
    assert (diagnostic.domain, diagnostic.path, diagnostic.symbol, diagnostic.line) == (
        None,
        None,
        None,
        None,
    )
    assert not (tmp_path / "stage").exists()


def test_existing_non_commit_head_is_not_classified_as_unborn(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    initialize_repository(repo)
    git(repo, "symbolic-ref", "HEAD", "refs/heads/broken")
    object_id = git(repo, "hash-object", "-w", ".git/HEAD").stdout.decode("ascii").strip()
    (repo / ".git/refs/heads/broken").write_text(f"{object_id}\n", encoding="ascii")

    with pytest.raises(GitReadError) as caught:
        GitRepositoryReader(repo).resolve_head_state()

    assert caught.value.diagnostic.code.value == "CSV-REPO-002"
