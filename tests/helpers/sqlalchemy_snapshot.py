from __future__ import annotations

import os
import shutil
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path

from tests.helpers.acceptance import ROOT, CliResult, initialize_repository

SQLALCHEMY_FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "sqlalchemy_snapshot"


def initialize_sqlalchemy_fixture_repository(
    tmp_path: Path,
    case: str,
    *,
    fixture_root: Path = SQLALCHEMY_FIXTURE_ROOT,
) -> Path:
    root = fixture_root.resolve()
    source = (root / case / "repo").resolve()
    if not source.is_relative_to(root):
        raise ValueError("fixture case must stay within the fixture root")
    if not source.is_dir():
        raise FileNotFoundError(source)

    repository = tmp_path / "repo"
    shutil.copytree(source, repository, symlinks=True)
    initialize_repository(repository)
    return repository


def run_snapshot_cli(
    repository: Path,
    output: Path,
    *arguments: str,
    domain: str = "sqlalchemy",
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
            domain,
            *arguments,
        ),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
        cwd=repository,
        env={**os.environ, "NO_COLOR": "1", **(environment or {})},
    )
    return CliResult(completed.returncode, completed.stdout, completed.stderr)
