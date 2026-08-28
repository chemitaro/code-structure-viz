from __future__ import annotations

from pathlib import Path

from tests.helpers.acceptance import ROOT, initialize_fixture_repository, run_cli
from tests.helpers.sqlalchemy_snapshot import (
    initialize_sqlalchemy_fixture_repository,
    run_snapshot_cli,
)


def test_helpers_match_existing_python_fixture_and_cli_bytes(tmp_path: Path) -> None:
    legacy_root = tmp_path / "legacy"
    helper_root = tmp_path / "helper"
    legacy_root.mkdir()
    helper_root.mkdir()
    legacy_repository = initialize_fixture_repository(legacy_root, "targeted")
    helper_repository = initialize_sqlalchemy_fixture_repository(
        helper_root,
        "targeted",
        fixture_root=ROOT / "tests" / "fixtures" / "python_snapshot",
    )
    arguments = (
        "--target",
        "class:app.a.A",
        "--upstream-depth",
        "0",
        "--downstream-depth",
        "1",
        "--format",
        "semantic-json",
        "--stdout",
        "python:semantic-json",
    )
    legacy_output = tmp_path / "legacy-output"
    helper_output = tmp_path / "helper-output"

    legacy_result = run_cli(legacy_repository, legacy_output, *arguments)
    helper_result = run_snapshot_cli(
        helper_repository,
        helper_output,
        *arguments,
        domain="python",
    )

    assert helper_result == legacy_result
    assert _published_bytes(helper_output) == _published_bytes(legacy_output)


def _published_bytes(output: Path) -> dict[str, bytes]:
    return {
        path.relative_to(output).as_posix(): path.read_bytes()
        for path in output.rglob("*")
        if path.is_file()
    }
