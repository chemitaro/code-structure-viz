from __future__ import annotations

import subprocess
from pathlib import Path

from tests.helpers.diff import create_two_commit_repository, run_diff_cli


def test_diff_does_not_mutate_git_head_index_refs_or_worktree(tmp_path: Path) -> None:
    repository, before, after = create_two_commit_repository(
        tmp_path,
        before_text="class Order:\n    amount: int\n",
        after_text="class Order:\n    amount: str\n",
    )
    git_dir = Path(
        subprocess.check_output(
            ("git", "-C", str(repository), "rev-parse", "--git-dir"),
            text=True,
        ).strip()
    )
    if not git_dir.is_absolute():
        git_dir = repository / git_dir
    tracked_before = _git(repository, "ls-files", "-s", "-z")
    status_before = _git(repository, "status", "--porcelain=v1", "-z")
    head_before = _git(repository, "rev-parse", "HEAD")
    index_before = (git_dir / "index").read_bytes()
    refs_before = _git(repository, "show-ref")

    result = run_diff_cli(repository, tmp_path / "output", "--from", before, "--to", after)

    assert result.returncode == 0
    assert _git(repository, "ls-files", "-s", "-z") == tracked_before
    assert _git(repository, "status", "--porcelain=v1", "-z") == status_before
    assert _git(repository, "rev-parse", "HEAD") == head_before
    assert (git_dir / "index").read_bytes() == index_before
    assert _git(repository, "show-ref") == refs_before


def _git(repository: Path, *arguments: str) -> bytes:
    return subprocess.check_output(("git", "-C", str(repository), *arguments))
