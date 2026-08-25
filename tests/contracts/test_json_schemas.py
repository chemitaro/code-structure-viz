import json
from pathlib import Path
from typing import cast

import pytest
from jsonschema import Draft202012Validator, ValidationError  # type: ignore[import-untyped]

from tests.helpers.acceptance import (
    initialize_fixture_repository,
    initialize_repository,
    run_cli,
)

ROOT = Path(__file__).resolve().parents[2]
SEMANTIC_GOLDEN_ROOT = ROOT / "tests" / "golden" / "python_snapshot"


def _schema(name: str) -> dict[str, object]:
    return cast(
        dict[str, object],
        json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8")),
    )


@pytest.mark.parametrize(
    "name",
    [
        "diagnostic-v1.schema.json",
        "run-manifest-v1.schema.json",
        "run-summary-v1.schema.json",
        "semantic-v1.schema.json",
        "stdout-result-v1.schema.json",
    ],
)
def test_checked_in_schema_is_valid_and_closed(name: str) -> None:
    schema = _schema(name)

    Draft202012Validator.check_schema(schema)
    assert schema["additionalProperties"] is False


def test_diagnostic_schema_accepts_exact_vector_and_rejects_extra_field() -> None:
    schema = _schema("diagnostic-v1.schema.json")
    value = {
        "type": "diagnostic",
        "schema": "code-structure-viz.diagnostic/v1",
        "code": "CSV-PY-003",
        "severity": "error",
        "domain": "python",
        "path": "src/broken.py",
        "symbol": None,
        "line": 7,
        "recoverable": True,
        "message": "Python source could not be parsed with the v1 Python 3.12 grammar.",
    }
    Draft202012Validator(schema).validate(value)

    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate({**value, "source": "secret"})


@pytest.mark.parametrize(
    ("name", "value"),
    [
        (
            "run-summary-v1.schema.json",
            {
                "type": "run_summary",
                "schema": "code-structure-viz.run-summary/v1",
                "run_status": "fatal",
                "exit_code": 1,
                "domains": [],
                "manifest": None,
            },
        ),
        (
            "stdout-result-v1.schema.json",
            {
                "type": "stdout_result",
                "schema": "code-structure-viz.stdout-result/v1",
                "selector": "python:semantic-json",
                "availability": False,
                "domain_status": "not_applicable",
                "stable_reason": "domain_not_applicable",
                "artifact": None,
            },
        ),
        (
            "stdout-result-v1.schema.json",
            {
                "type": "stdout_result",
                "schema": "code-structure-viz.stdout-result/v1",
                "selector": "manifest",
                "availability": False,
                "run_status": "fatal",
                "stable_reason": "final_manifest_unavailable",
                "artifact": None,
            },
        ),
    ],
)
def test_stream_contract_schema_accepts_closed_positive_vectors(
    name: str, value: dict[str, object]
) -> None:
    Draft202012Validator(_schema(name)).validate(value)


def test_semantic_schema_accepts_zero_class_vector_and_rejects_shape_mutations() -> None:
    schema = _schema("semantic-v1.schema.json")
    value = {
        "type": "semantic_snapshot",
        "schema": "code-structure-viz.semantic/v1",
        "domain": "python",
        "document_kind": "snapshot",
        "status": "complete",
        "source": {
            "schema": "code-structure-viz.source-view/v1",
            "kind": "working-tree",
            "head_commit": None,
            "fingerprint": "b" * 64,
            "file_count": 2,
        },
        "request": {"targets": [], "upstream_depth": 1, "downstream_depth": 1},
        "coverage": {
            "candidate_files": 2,
            "parsed_files": 2,
            "failed_files": [],
            "selected_modules": ["app.a", "app.b"],
            "selected_entities": 0,
            "frontier": [],
        },
        "entities": [],
        "members": [],
        "relations": [],
        "diagnostics": [],
    }
    validator = Draft202012Validator(schema)
    validator.validate(value)

    with pytest.raises(ValidationError):
        validator.validate({**value, "absolute_path": "/private/secret"})
    with pytest.raises(ValidationError):
        validator.validate({**value, "status": "incomplete"})
    with pytest.raises(ValidationError):
        validator.validate({**value, "entities": None})


@pytest.mark.parametrize(
    "path",
    sorted(SEMANTIC_GOLDEN_ROOT.glob("*/python.snapshot.semantic.json")),
    ids=lambda path: path.parent.name,
)
def test_semantic_schema_accepts_every_reviewed_golden(path: Path) -> None:
    value = json.loads(path.read_text(encoding="utf-8"))

    Draft202012Validator(_schema("semantic-v1.schema.json")).validate(value)


@pytest.mark.parametrize(
    "path",
    sorted(SEMANTIC_GOLDEN_ROOT.glob("*/run-manifest.json")),
    ids=lambda path: path.parent.name,
)
def test_manifest_schema_accepts_every_reviewed_golden(path: Path) -> None:
    value = json.loads(path.read_text(encoding="utf-8"))

    Draft202012Validator(_schema("run-manifest-v1.schema.json")).validate(value)


@pytest.mark.parametrize(
    "path",
    sorted(SEMANTIC_GOLDEN_ROOT.glob("*/stdout.run-summary.jsonl")),
    ids=lambda path: path.parent.name,
)
def test_run_summary_schema_accepts_every_reviewed_golden(path: Path) -> None:
    value = json.loads(path.read_text(encoding="utf-8"))

    Draft202012Validator(_schema("run-summary-v1.schema.json")).validate(value)


@pytest.mark.parametrize(
    "path",
    sorted(SEMANTIC_GOLDEN_ROOT.glob("*/stderr.jsonl")),
    ids=lambda path: path.parent.name,
)
def test_diagnostic_schema_accepts_every_reviewed_golden_line(path: Path) -> None:
    validator = Draft202012Validator(_schema("diagnostic-v1.schema.json"))

    for line in path.read_text(encoding="utf-8").splitlines():
        validator.validate(json.loads(line))


def test_schemas_accept_captured_complete_and_unavailable_cli_json(
    tmp_path: Path,
) -> None:
    complete_root = tmp_path / "complete"
    repository = initialize_fixture_repository(complete_root, "whole")
    complete_output = complete_root / "output"
    complete = run_cli(repository, complete_output)
    assert complete.returncode == 0

    Draft202012Validator(_schema("run-summary-v1.schema.json")).validate(
        json.loads(complete.stdout)
    )
    Draft202012Validator(_schema("semantic-v1.schema.json")).validate(
        json.loads((complete_output / "python.snapshot.semantic.json").read_bytes())
    )
    Draft202012Validator(_schema("run-manifest-v1.schema.json")).validate(
        json.loads((complete_output / "run-manifest.json").read_bytes())
    )

    unavailable_root = tmp_path / "unavailable"
    unavailable_root.mkdir()
    unavailable_repository = unavailable_root / "repo"
    initialize_repository(unavailable_repository)
    unavailable_output = unavailable_root / "output"
    unavailable = run_cli(
        unavailable_repository,
        unavailable_output,
        "--target",
        "module:missing.module",
        "--stdout",
        "python:semantic-json",
    )
    assert unavailable.returncode == 3

    Draft202012Validator(_schema("stdout-result-v1.schema.json")).validate(
        json.loads(unavailable.stdout)
    )
    Draft202012Validator(_schema("diagnostic-v1.schema.json")).validate(
        json.loads(unavailable.stderr)
    )
    manifest = json.loads((unavailable_output / "run-manifest.json").read_bytes())
    validator = Draft202012Validator(_schema("run-manifest-v1.schema.json"))
    validator.validate(manifest)
    with pytest.raises(ValidationError):
        validator.validate({**manifest, "absolute_path": "/private/secret"})
    with pytest.raises(ValidationError):
        validator.validate({**manifest, "artifacts": [{"path": "run-manifest.json"}]})
