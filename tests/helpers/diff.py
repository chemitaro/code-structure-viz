from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path


def create_two_commit_repository(
    tmp_path: Path,
    *,
    before_text: str,
    after_text: str | None = None,
    relative_path: str = "src/app.py",
) -> tuple[Path, str, str]:
    repository = tmp_path / "repo"
    (repository / "src").mkdir(parents=True)
    _git(repository, "init", "--quiet", "--initial-branch=main")
    source = repository / relative_path
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(before_text, encoding="utf-8")
    _git(repository, "add", ".")
    _git(repository, "commit", "--quiet", "--message=before", env=_commit_env())
    before = _head(repository)
    if after_text is None:
        after_text = before_text
    source.write_text(after_text, encoding="utf-8")
    _git(repository, "add", ".")
    _git(repository, "commit", "--quiet", "--message=after", env=_commit_env())
    return repository, before, _head(repository)


def create_two_commit_repository_from_files(
    tmp_path: Path,
    *,
    before_files: Mapping[str, str],
    after_files: Mapping[str, str],
) -> tuple[Path, str, str]:
    repository = tmp_path / "repo"
    repository.mkdir(parents=True)
    _git(repository, "init", "--quiet", "--initial-branch=main")
    _write_fixture_files(repository, before_files)
    _git(repository, "add", ".")
    _git(repository, "commit", "--quiet", "--message=before", env=_commit_env())
    before = _head(repository)
    for relative_path in set(before_files) - set(after_files):
        (repository / relative_path).unlink()
    _write_fixture_files(repository, after_files)
    _git(repository, "add", ".")
    _git(repository, "commit", "--quiet", "--message=after", env=_commit_env())
    return repository, before, _head(repository)


def create_unmerged_repository(
    tmp_path: Path,
    *,
    base_text: str = "class Order:\n    amount: int\n",
) -> tuple[Path, str]:
    """Create a repository whose current working tree has one real merge conflict."""
    repository = tmp_path / "repo"
    (repository / "src").mkdir(parents=True)
    _git(repository, "init", "--quiet", "--initial-branch=main")
    source = repository / "src/app.py"
    source.write_text(base_text, encoding="utf-8")
    _git(repository, "add", ".")
    _git(repository, "commit", "--quiet", "--message=base", env=_commit_env())
    base = _head(repository)

    _git(repository, "switch", "--quiet", "--create", "side")
    source.write_text("class Order:\n    amount: str\n", encoding="utf-8")
    _git(repository, "add", ".")
    _git(repository, "commit", "--quiet", "--message=side", env=_commit_env())

    _git(repository, "switch", "--quiet", "main")
    source.write_text("class Order:\n    amount: bytes\n", encoding="utf-8")
    _git(repository, "add", ".")
    _git(repository, "commit", "--quiet", "--message=main", env=_commit_env())
    merge = subprocess.run(
        ("git", "-C", str(repository), "merge", "--no-commit", "side"),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
    )
    if merge.returncode == 0:
        raise AssertionError("fixture merge unexpectedly succeeded")
    return repository, base


def run_diff_cli(
    repository: Path,
    output: Path,
    *arguments: str,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        (
            sys.executable,
            "-m",
            "code_structure_viz",
            "diff",
            "--repo",
            str(repository),
            "--output-dir",
            str(output),
            "--domain",
            "python",
            *arguments,
        ),
        cwd=repository,
        env={**os.environ, "NO_COLOR": "1"},
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
    )


def commit_current_changes(repository: Path, message: str) -> str:
    _git(repository, "add", ".")
    _git(repository, "commit", "--quiet", f"--message={message}", env=_commit_env())
    return _head(repository)


def _commit_env() -> dict[str, str]:
    return {
        **os.environ,
        "GIT_AUTHOR_NAME": "Code Structure Viz Fixture",
        "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
        "GIT_AUTHOR_DATE": "2000-01-01T00:00:00Z",
        "GIT_COMMITTER_NAME": "Code Structure Viz Fixture",
        "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
        "GIT_COMMITTER_DATE": "2000-01-01T00:00:00Z",
    }


def _head(repository: Path) -> str:
    return subprocess.check_output(
        ("git", "-C", str(repository), "rev-parse", "HEAD"),
        text=True,
    ).strip()


def _write_fixture_files(repository: Path, files: Mapping[str, str]) -> None:
    for relative_path, content in files.items():
        path = repository / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def _git(
    repository: Path,
    *arguments: str,
    env: dict[str, str] | None = None,
) -> None:
    subprocess.run(
        ("git", "-C", str(repository), *arguments),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
        env=env,
    )
