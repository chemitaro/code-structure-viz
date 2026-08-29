from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path

from tests.helpers.acceptance import ROOT, CliResult, initialize_repository

SQLALCHEMY_FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "sqlalchemy_snapshot"
SQLALCHEMY_GOLDEN_CASES = (
    "canonical_model",
    "relationship_semantics",
    "lossy_identity_conflict",
    "lossy_same_line_siblings",
)


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


def _copy_golden_fixture(repository: Path, case: str) -> None:
    source = (SQLALCHEMY_FIXTURE_ROOT / case).resolve()
    if not source.is_relative_to(SQLALCHEMY_FIXTURE_ROOT.resolve()):
        raise ValueError("golden case must stay within the SQLAlchemy fixture root")
    repository.mkdir(parents=True)
    if (source / "repo").is_dir():
        shutil.copytree(source / "repo", repository, dirs_exist_ok=True)
    else:
        destination = repository / "src" / "models.py"
        destination.parent.mkdir(parents=True)
        shutil.copy2(source / "models.py", destination)
    initialize_repository(repository)


def render_sqlalchemy_golden_case(case: str) -> dict[str, bytes]:
    if case not in SQLALCHEMY_GOLDEN_CASES:
        raise ValueError("golden case is not in the closed allowlist")
    with tempfile.TemporaryDirectory(
        prefix="code-structure-viz-sqlalchemy-golden-",
        dir=Path(tempfile.gettempdir()).resolve(),
    ) as directory:
        temporary = Path(directory).resolve()
        repository = temporary / "repo"
        _copy_golden_fixture(repository, case)
        output = temporary / "output"
        result = run_snapshot_cli(repository, output)
        published_names = tuple(
            sorted(
                (path.name for path in output.iterdir() if path.is_file()),
                key=lambda value: value.encode("utf-8"),
            )
        )
        rendered = {name: (output / name).read_bytes() for name in published_names}
        rendered.update(
            {
                "stdout.run-summary.jsonl": result.stdout,
                "stderr.jsonl": result.stderr,
                "published-files.txt": b"".join(
                    name.encode("utf-8") + b"\n" for name in published_names
                ),
                "exit-code.txt": f"{result.returncode}\n".encode("ascii"),
            }
        )
        return rendered
