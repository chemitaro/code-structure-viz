import json
from pathlib import Path

import pytest

from tests.helpers.acceptance import (
    initialize_fixture_repository,
    initialize_repository,
    run_cli,
)


@pytest.mark.parametrize(
    ("format_value", "selector", "artifact"),
    [
        ("semantic-json", "python:semantic-json", "python.snapshot.semantic.json"),
        ("plantuml", "python:plantuml", "python.snapshot.puml"),
    ],
)
def test_available_domain_selector_is_exact_final_file_bytes(
    tmp_path: Path,
    format_value: str,
    selector: str,
    artifact: str,
) -> None:
    repository = initialize_fixture_repository(tmp_path, "whole")
    output = tmp_path / "output"

    result = run_cli(
        repository,
        output,
        "--format",
        format_value,
        "--stdout",
        selector,
    )

    assert result.returncode == 0
    assert result.stdout == (output / artifact).read_bytes()
    assert result.stderr == b""
    assert sorted(path.name for path in output.iterdir()) == [artifact, "run-manifest.json"]


def test_manifest_selector_is_exact_final_manifest_bytes(tmp_path: Path) -> None:
    repository = initialize_fixture_repository(tmp_path, "whole")
    output = tmp_path / "output"

    result = run_cli(repository, output, "--stdout", "manifest")

    assert result.returncode == 0
    assert result.stdout == (output / "run-manifest.json").read_bytes()
    assert result.stderr == b""


def test_not_applicable_domain_selector_emits_closed_unavailable_result(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repo"
    initialize_repository(repository)
    output = tmp_path / "output"

    result = run_cli(repository, output, "--stdout", "python:semantic-json")

    assert result.returncode == 0
    assert result.stdout == (
        b'{"type":"stdout_result","schema":"code-structure-viz.stdout-result/v1",'
        b'"selector":"python:semantic-json","availability":false,'
        b'"domain_status":"not_applicable","stable_reason":"domain_not_applicable",'
        b'"artifact":null}\n'
    )
    assert result.stderr == b""


def test_payload_unavailable_domain_selector_emits_closed_result_and_diagnostic(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repo"
    initialize_repository(repository)
    output = tmp_path / "output"

    result = run_cli(
        repository,
        output,
        "--target",
        "class:app.missing.Thing",
        "--stdout",
        "python:plantuml",
    )

    assert result.returncode == 3
    assert result.stdout == (
        b'{"type":"stdout_result","schema":"code-structure-viz.stdout-result/v1",'
        b'"selector":"python:plantuml","availability":false,'
        b'"domain_status":"incomplete",'
        b'"stable_reason":"domain_payload_unavailable","artifact":null}\n'
    )
    assert json.loads(result.stderr)["code"] == "CSV-PY-006"


def test_partial_safe_selector_copies_incomplete_payload_exactly(tmp_path: Path) -> None:
    repository = initialize_fixture_repository(tmp_path, "partial_safe")
    output = tmp_path / "output"

    result = run_cli(
        repository,
        output,
        "--target",
        "module:app.good",
        "--stdout",
        "python:semantic-json",
    )

    assert result.returncode == 3
    assert result.stdout == (output / "python.snapshot.semantic.json").read_bytes()
    assert json.loads(result.stderr)["code"] == "CSV-PY-003"


def test_unselected_stdout_format_is_usage_error_before_source_acquisition(
    tmp_path: Path,
) -> None:
    repository = initialize_fixture_repository(tmp_path, "whole")
    output = tmp_path / "output"

    result = run_cli(
        repository,
        output,
        "--format",
        "semantic-json",
        "--stdout",
        "python:plantuml",
    )

    assert result.returncode == 2
    assert result.stdout == b""
    assert json.loads(result.stderr)["code"] == "CSV-USAGE-005"
    assert not output.exists()


def test_depth_limit_frontier_does_not_emit_stderr(tmp_path: Path) -> None:
    repository = initialize_fixture_repository(tmp_path, "targeted")
    output = tmp_path / "output"

    result = run_cli(
        repository,
        output,
        "--target",
        "class:app.a.A",
        "--upstream-depth",
        "0",
        "--downstream-depth",
        "0",
    )

    assert result.returncode == 0
    assert result.stderr == b""
    semantic = json.loads((output / "python.snapshot.semantic.json").read_bytes())
    assert semantic["coverage"]["frontier"] != []


def test_manifest_selector_on_run_fatal_reports_final_manifest_unavailable(
    tmp_path: Path,
) -> None:
    repository = initialize_fixture_repository(tmp_path, "whole")
    output = tmp_path / "output"
    output.mkdir()

    result = run_cli(repository, output, "--stdout", "manifest")

    assert result.returncode == 1
    assert result.stdout == (
        b'{"type":"stdout_result","schema":"code-structure-viz.stdout-result/v1",'
        b'"selector":"manifest","availability":false,"run_status":"fatal",'
        b'"stable_reason":"final_manifest_unavailable","artifact":null}\n'
    )
    assert json.loads(result.stderr)["code"] == "CSV-OUTPUT-001"
