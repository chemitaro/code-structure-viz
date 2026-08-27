from __future__ import annotations

import os
import shutil
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class CliResult:
    returncode: int
    stdout: bytes
    stderr: bytes


def initialize_fixture_repository(tmp_path: Path, case: str) -> Path:
    source = ROOT / "tests" / "fixtures" / "python_snapshot" / case / "repo"
    repository = tmp_path / "repo"
    shutil.copytree(source, repository, symlinks=True)
    _git(
        repository,
        "init",
        "--quiet",
        "--initial-branch=main",
        "--object-format=sha1",
    )
    _git(repository, "add", ".")
    environment = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Code Structure Viz Fixture",
        "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
        "GIT_AUTHOR_DATE": "2000-01-01T00:00:00Z",
        "GIT_COMMITTER_NAME": "Code Structure Viz Fixture",
        "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
        "GIT_COMMITTER_DATE": "2000-01-01T00:00:00Z",
    }
    _git(repository, "commit", "--quiet", "--message=fixture", env=environment)
    return repository


def initialize_repository(repository: Path) -> None:
    repository.mkdir(exist_ok=True)
    _git(
        repository,
        "init",
        "--quiet",
        "--initial-branch=main",
        "--object-format=sha1",
    )
    _git(repository, "add", ".")
    environment = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Code Structure Viz Fixture",
        "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
        "GIT_AUTHOR_DATE": "2000-01-01T00:00:00Z",
        "GIT_COMMITTER_NAME": "Code Structure Viz Fixture",
        "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
        "GIT_COMMITTER_DATE": "2000-01-01T00:00:00Z",
    }
    _git(repository, "commit", "--quiet", "--allow-empty", "--message=fixture", env=environment)


def run_cli(
    repository: Path,
    output: Path,
    *arguments: str,
    environment: Mapping[str, str] | None = None,
) -> CliResult:
    completed = subprocess.run(
        (
            sys.executable,
            "-m",
            "code_structure_viz",
            "snapshot",
            "--repo",
            str(repository),
            "--output-dir",
            str(output),
            "--domain",
            "python",
            *arguments,
        ),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
        cwd=repository,
        env={**os.environ, "NO_COLOR": "1", **(environment or {})},
    )
    return CliResult(completed.returncode, completed.stdout, completed.stderr)


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
    if arguments and arguments[0] == "init":
        subprocess.run(
            ("git", "-C", str(repository), "config", "core.ignoreCase", "false"),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=True,
            env=env,
        )
