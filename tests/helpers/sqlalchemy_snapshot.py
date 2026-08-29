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
    "escape_collision",
    "component_split_collision",
)


def initialize_sqlalchemy_fixture_repository(
    tmp_path: Path,
    case: str,
    *,
    fixture_root: Path = SQLALCHEMY_FIXTURE_ROOT,
) -> Path:
    root = fixture_root.resolve()
    case_root = (root / case).resolve()
    if not case_root.is_relative_to(root):
        raise ValueError("fixture case must stay within the fixture root")
    source = case_root / "repo"
    if source.is_dir():
        source = source.resolve()
    elif any(case_root.glob("*.py")):
        source = case_root
    else:
        raise FileNotFoundError(case_root)

    repository = tmp_path / "repo"
    if source.name == "repo":
        shutil.copytree(source, repository, symlinks=True)
    else:
        destination_root = repository / "src" / ("pkg" if case == "cross_module" else "")
        destination_root.mkdir(parents=True, exist_ok=True)
        for path in source.rglob("*.py"):
            destination = destination_root / path.relative_to(source)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
        if case == "cross_module":
            (destination_root / "__init__.py").write_text("", encoding="utf-8")
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
