from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def git(repo: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ("git", "-C", str(repo), *arguments),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=check,
    )


def initialize_repository(repo: Path) -> None:
    repo.mkdir()
    subprocess.run(
        ("git", "init", "--quiet", "--initial-branch=main", str(repo)),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
    )


def commit_all(repo: Path, message: str = "fixture") -> str:
    git(repo, "add", "--all")
    git(
        repo,
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "--quiet",
        "--message",
        message,
    )
    return git(repo, "rev-parse", "HEAD").stdout.decode("ascii").strip()


def copy_fixture_repository(case: str, destination: Path) -> Path:
    fixture = Path(__file__).parents[1] / "fixtures" / "python_snapshot" / case / "repo"
    shutil.copytree(fixture, destination)
    return destination
