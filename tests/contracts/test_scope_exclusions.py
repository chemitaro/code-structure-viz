from __future__ import annotations

import ast
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = ROOT / "src" / "code_structure_viz"
_FORBIDDEN_IMPORTS = frozenset(
    {
        "jsonschema",
        "sqlalchemy",
        "pyclassuml",
        "tree_git_diff",
    }
)


@pytest.mark.parametrize(
    "arguments",
    [
        ("diff",),
        ("snapshot", "--domain", "sqlalchemy"),
        ("snapshot", "--domain", "next"),
        ("snapshot", "--domain", "python", "--format", "html"),
    ],
)
def test_cli_registers_only_python_snapshot_and_v1_formats(arguments: tuple[str, ...]) -> None:
    completed = subprocess.run(
        (sys.executable, "-m", "code_structure_viz", *arguments),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
        cwd=ROOT,
    )

    assert completed.returncode == 2
    assert completed.stdout == b""


def test_help_exposes_no_diff_database_next_or_html_surface() -> None:
    completed = subprocess.run(
        (sys.executable, "-m", "code_structure_viz", "--help"),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
        cwd=ROOT,
    )
    help_text = completed.stdout.decode("ascii").lower()

    assert "snapshot" in help_text
    assert all(value not in help_text for value in ("diff", "sqlalchemy", "next", "html"))


def test_runtime_dependency_import_and_package_surfaces_are_closed() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["dependencies"] == []

    forbidden: list[tuple[str, str]] = []
    for path in sorted(SOURCE_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                names = [node.module]
            else:
                continue
            forbidden.extend(
                (path.relative_to(ROOT).as_posix(), name)
                for name in names
                if name.split(".", 1)[0] in _FORBIDDEN_IMPORTS
            )

    assert forbidden == []
    assert not any(
        path.is_dir() and path.name.lower() in {"diff", "sqlalchemy", "next", "html"}
        for path in SOURCE_ROOT.rglob("*")
    )
    assert not any(path.suffix.lower() in {".html", ".htm"} for path in SOURCE_ROOT.rglob("*"))


def test_runtime_does_not_load_schema_files_or_validator_packages() -> None:
    findings: list[tuple[str, int]] = []
    for path in sorted(SOURCE_ROOT.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(source.splitlines(), start=1):
            if re.search(r"schemas?/|\.schema\.json|jsonschema", line, flags=re.IGNORECASE):
                findings.append((path.relative_to(ROOT).as_posix(), line_number))

    assert findings == []


def test_ci_keeps_specdock_validation_and_adds_all_product_gates() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "validate:" in workflow
    assert "python3 ./spec-dock/scripts/spec-dock validate" in workflow
    for job in (
        "product-test-minimum",
        "product-test-latest",
        "product-test-macos",
        "product-package-offline",
        "product-contract-scope",
    ):
        assert f"  {job}:" in workflow
    assert "continue-on-error" not in workflow
    assert "upload-artifact" not in workflow
    assert "release" not in workflow.lower()
    assert '--user "$(id -u):$(id -g)"' in workflow

    assert (ROOT / "ci" / "latest-python.txt").read_bytes() == b"3.14\n"
    dockerfile = (ROOT / "ci" / "toolchains" / "git-2.39.5.Dockerfile").read_text(encoding="utf-8")
    checksum = (ROOT / "ci" / "toolchains" / "git-2.39.5.sha256").read_text(encoding="ascii")
    assert "git-2.39.5.tar.xz" in dockerfile
    assert "sha256sum --check" in dockerfile
    assert "git version 2.39.5" in workflow
    assert re.fullmatch(r"[0-9a-f]{64}  git-2\.39\.5\.tar\.xz\n", checksum)
