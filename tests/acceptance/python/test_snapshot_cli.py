import json
from pathlib import Path

from tests.helpers.acceptance import (
    initialize_fixture_repository,
    initialize_repository,
    run_cli,
)


def test_whole_snapshot_cli_atomically_publishes_requested_payloads_and_manifest(
    tmp_path: Path,
) -> None:
    repository = initialize_fixture_repository(tmp_path, "whole")
    output = tmp_path / "output"

    result = run_cli(repository, output)

    assert result.returncode == 0
    assert result.stdout == (
        b'{"type":"run_summary","schema":"code-structure-viz.run-summary/v1",'
        b'"run_status":"complete","exit_code":0,"domains":'
        b'[{"domain":"python","status":"complete"}],'
        b'"manifest":"run-manifest.json"}\n'
    )
    assert result.stderr == b""
    assert sorted(path.name for path in output.iterdir()) == [
        "python.snapshot.puml",
        "python.snapshot.semantic.json",
        "run-manifest.json",
    ]
    semantic = json.loads((output / "python.snapshot.semantic.json").read_bytes())
    manifest = json.loads((output / "run-manifest.json").read_bytes())
    assert semantic["status"] == "complete"
    assert semantic["coverage"]["selected_modules"] == [
        "domain.base",
        "domain.order",
        "domain.service",
    ]
    assert semantic["coverage"]["selected_entities"] == 4
    assert manifest["run"]["status"] == "complete"
    assert [item["path"] for item in manifest["artifacts"]] == [
        "python.snapshot.semantic.json",
        "python.snapshot.puml",
    ]


def test_whole_repository_without_python_is_not_applicable_and_manifest_only(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repo"
    initialize_repository(repository)
    output = tmp_path / "output"

    result = run_cli(repository, output)

    assert result.returncode == 0
    assert result.stderr == b""
    assert sorted(path.name for path in output.iterdir()) == ["run-manifest.json"]
    manifest = json.loads((output / "run-manifest.json").read_bytes())
    assert manifest["run"]["status"] == "not_applicable"
    assert manifest["domains"] == [
        {
            "domain": "python",
            "status": "not_applicable",
            "payload_available": False,
            "entity_count": 0,
            "coverage": {
                "candidate_files": 0,
                "parsed_files": 0,
                "failed_files": [],
                "selected_modules": [],
                "selected_entities": 0,
                "frontier": [],
            },
            "budget": {
                "name": "max_entities",
                "requested": None,
                "resolved": 500,
                "actual": 0,
                "source": "builtin",
            },
            "artifact_paths": [],
            "diagnostics": [],
        }
    ]


def test_partial_safe_cli_publishes_safe_payload_with_parse_diagnostic(
    tmp_path: Path,
) -> None:
    repository = initialize_fixture_repository(tmp_path, "partial_safe")
    output = tmp_path / "output"

    result = run_cli(
        repository,
        output,
        "--target",
        "module:app.good",
    )

    assert result.returncode == 3
    assert sorted(path.name for path in output.iterdir()) == [
        "python.snapshot.puml",
        "python.snapshot.semantic.json",
        "run-manifest.json",
    ]
    assert result.stderr.count(b"\n") == 1
    assert b'"code":"CSV-PY-003"' in result.stderr
    semantic = json.loads((output / "python.snapshot.semantic.json").read_bytes())
    assert (semantic["status"], semantic["incomplete_kind"]) == (
        "incomplete",
        "partial_safe",
    )
