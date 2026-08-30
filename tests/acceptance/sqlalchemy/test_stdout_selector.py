from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.helpers.acceptance import initialize_repository
from tests.helpers.sqlalchemy_snapshot import (
    initialize_sqlalchemy_fixture_repository,
    run_snapshot_cli,
)


@pytest.mark.parametrize(
    ("format_value", "selector", "artifact"),
    [
        (
            "semantic-json",
            "sqlalchemy:semantic-json",
            "sqlalchemy.snapshot.semantic.json",
        ),
        ("plantuml", "sqlalchemy:plantuml", "sqlalchemy.snapshot.puml"),
    ],
)
def test_sqlalchemy_available_selector_is_exact_final_file_bytes(
    tmp_path: Path,
    format_value: str,
    selector: str,
    artifact: str,
) -> None:
    repository = initialize_sqlalchemy_fixture_repository(tmp_path, "canonical_model")
    output = tmp_path / "output"

    result = run_snapshot_cli(
        repository,
        output,
        "--format",
        format_value,
        "--stdout",
        selector,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == (output / artifact).read_bytes()
    assert result.stderr == b""


def test_sqlalchemy_manifest_selector_is_exact_final_manifest_bytes(tmp_path: Path) -> None:
    repository = initialize_sqlalchemy_fixture_repository(tmp_path, "canonical_model")
    output = tmp_path / "output"

    result = run_snapshot_cli(repository, output, "--stdout", "manifest")

    assert result.returncode == 0, result.stderr
    assert result.stdout == (output / "run-manifest.json").read_bytes()


def test_sqlalchemy_not_applicable_and_payload_unavailable_results_are_typed(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repo"
    source = repository / "src" / "plain.py"
    source.parent.mkdir(parents=True)
    source.write_text("answer = 42\n", encoding="utf-8")
    initialize_repository(repository)

    absent = run_snapshot_cli(
        repository,
        tmp_path / "absent-output",
        "--stdout",
        "sqlalchemy:semantic-json",
    )
    missing = run_snapshot_cli(
        repository,
        tmp_path / "missing-output",
        "--target",
        "module:missing",
        "--stdout",
        "sqlalchemy:plantuml",
    )

    assert json.loads(absent.stdout) == {
        "type": "stdout_result",
        "schema": "code-structure-viz.stdout-result/v1",
        "selector": "sqlalchemy:semantic-json",
        "availability": False,
        "domain_status": "not_applicable",
        "stable_reason": "domain_not_applicable",
        "artifact": None,
    }
    assert absent.returncode == 0
    assert json.loads(missing.stdout)["stable_reason"] == "domain_payload_unavailable"
    assert missing.returncode == 3


def test_sqlalchemy_cross_domain_selector_is_usage_without_output(tmp_path: Path) -> None:
    repository = initialize_sqlalchemy_fixture_repository(tmp_path, "canonical_model")
    output = tmp_path / "output"

    result = run_snapshot_cli(
        repository,
        output,
        "--stdout",
        "python:semantic-json",
    )

    assert result.returncode == 2
    assert result.stdout == b""
    assert json.loads(result.stderr)["code"] == "CSV-USAGE-005"
    assert not output.exists()
