import json
from copy import deepcopy
from pathlib import Path
from typing import cast

import pytest
from jsonschema import Draft202012Validator, ValidationError  # type: ignore[import-untyped]
from referencing import Registry, Resource

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


def _validator(name: str) -> Draft202012Validator:
    diagnostic_schema = _schema("diagnostic-v1.schema.json")
    registry = Registry().with_resource(
        "urn:code-structure-viz:schema:diagnostic-v1",
        Resource.from_contents(diagnostic_schema),
    )
    return Draft202012Validator(_schema(name), registry=registry)


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
    _validator("diagnostic-v1.schema.json").validate(value)

    with pytest.raises(ValidationError):
        _validator("diagnostic-v1.schema.json").validate({**value, "source": "secret"})


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
    _validator(name).validate(value)


def test_semantic_schema_accepts_zero_class_vector_and_rejects_shape_mutations() -> None:
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
    validator = _validator("semantic-v1.schema.json")
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

    _validator("semantic-v1.schema.json").validate(value)


@pytest.mark.parametrize(
    "path",
    sorted(SEMANTIC_GOLDEN_ROOT.glob("*/run-manifest.json")),
    ids=lambda path: path.parent.name,
)
def test_manifest_schema_accepts_every_reviewed_golden(path: Path) -> None:
    value = json.loads(path.read_text(encoding="utf-8"))

    _validator("run-manifest-v1.schema.json").validate(value)


@pytest.mark.parametrize(
    "path",
    sorted(SEMANTIC_GOLDEN_ROOT.glob("*/stdout.run-summary.jsonl")),
    ids=lambda path: path.parent.name,
)
def test_run_summary_schema_accepts_every_reviewed_golden(path: Path) -> None:
    value = json.loads(path.read_text(encoding="utf-8"))

    _validator("run-summary-v1.schema.json").validate(value)


@pytest.mark.parametrize(
    "path",
    sorted(SEMANTIC_GOLDEN_ROOT.glob("*/stderr.jsonl")),
    ids=lambda path: path.parent.name,
)
def test_diagnostic_schema_accepts_every_reviewed_golden_line(path: Path) -> None:
    validator = _validator("diagnostic-v1.schema.json")

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

    _validator("run-summary-v1.schema.json").validate(json.loads(complete.stdout))
    _validator("semantic-v1.schema.json").validate(
        json.loads((complete_output / "python.snapshot.semantic.json").read_bytes())
    )
    _validator("run-manifest-v1.schema.json").validate(
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

    _validator("stdout-result-v1.schema.json").validate(json.loads(unavailable.stdout))
    _validator("diagnostic-v1.schema.json").validate(json.loads(unavailable.stderr))
    manifest = json.loads((unavailable_output / "run-manifest.json").read_bytes())
    validator = _validator("run-manifest-v1.schema.json")
    validator.validate(manifest)
    with pytest.raises(ValidationError):
        validator.validate({**manifest, "absolute_path": "/private/secret"})
    with pytest.raises(ValidationError):
        validator.validate({**manifest, "artifacts": [{"path": "run-manifest.json"}]})


def test_semantic_schema_rejects_member_and_relation_target_discriminant_mutations() -> None:
    validator = _validator("semantic-v1.schema.json")
    whole = json.loads(
        (SEMANTIC_GOLDEN_ROOT / "whole" / "python.snapshot.semantic.json").read_text(
            encoding="utf-8"
        )
    )
    annotation_references = json.loads(
        (
            SEMANTIC_GOLDEN_ROOT / "annotation_references" / "python.snapshot.semantic.json"
        ).read_text(encoding="utf-8")
    )

    mutations: list[dict[str, object]] = []
    field_scope = deepcopy(whole)
    next(item for item in field_scope["members"] if item["kind"] == "field")["scope"] = None
    mutations.append(field_scope)
    property_signature = deepcopy(whole)
    next(item for item in property_signature["members"] if item["kind"] == "property")[
        "signature"
    ] = None
    mutations.append(property_signature)
    method_annotation = deepcopy(whole)
    next(item for item in method_annotation["members"] if item["kind"] == "method")[
        "annotation"
    ] = "Secret"
    mutations.append(method_annotation)
    internal_id = deepcopy(whole)
    next(item for item in internal_id["relations"] if item["target"]["resolution"] == "internal")[
        "target"
    ]["id"] = None
    mutations.append(internal_id)
    external_id = deepcopy(whole)
    next(item for item in external_id["relations"] if item["target"]["resolution"] == "external")[
        "target"
    ]["id"] = "python:module:secret"
    mutations.append(external_id)
    unknown_kind = deepcopy(annotation_references)
    next(item for item in unknown_kind["relations"] if item["target"]["resolution"] == "unknown")[
        "target"
    ]["kind"] = "module"
    mutations.append(unknown_kind)
    unknown_diagnostic = deepcopy(annotation_references)
    unknown_diagnostic["diagnostics"][0]["code"] = "CSV-UNKNOWN-999"
    mutations.append(unknown_diagnostic)
    wrong_diagnostic_metadata = deepcopy(annotation_references)
    wrong_diagnostic_metadata["diagnostics"][0]["severity"] = "error"
    mutations.append(wrong_diagnostic_metadata)

    for mutation in mutations:
        with pytest.raises(ValidationError):
            validator.validate(mutation)


def test_manifest_schema_rejects_status_exit_artifact_and_catalog_mutations() -> None:
    validator = _validator("run-manifest-v1.schema.json")
    complete = json.loads(
        (SEMANTIC_GOLDEN_ROOT / "whole" / "run-manifest.json").read_text(encoding="utf-8")
    )
    partial = json.loads(
        (SEMANTIC_GOLDEN_ROOT / "partial_safe" / "run-manifest.json").read_text(encoding="utf-8")
    )

    mutations: list[dict[str, object]] = []
    wrong_exit = deepcopy(complete)
    wrong_exit["run"]["exit_code"] = 3
    mutations.append(wrong_exit)
    missing_payload_artifacts = deepcopy(complete)
    missing_payload_artifacts["domains"][0]["artifact_paths"] = []
    missing_payload_artifacts["artifacts"] = []
    mutations.append(missing_payload_artifacts)
    mismatched_artifact = deepcopy(complete)
    mismatched_artifact["artifacts"][0]["format"] = "plantuml"
    mutations.append(mismatched_artifact)
    mismatched_status = deepcopy(partial)
    mismatched_status["run"]["status"] = "complete"
    mismatched_status["run"]["exit_code"] = 0
    mutations.append(mismatched_status)
    unknown_diagnostic = deepcopy(partial)
    unknown_diagnostic["domains"][0]["diagnostics"][0]["code"] = "CSV-UNKNOWN-999"
    mutations.append(unknown_diagnostic)
    wrong_diagnostic_message = deepcopy(partial)
    wrong_diagnostic_message["domains"][0]["diagnostics"][0]["message"] = "arbitrary"
    mutations.append(wrong_diagnostic_message)

    for mutation in mutations:
        with pytest.raises(ValidationError):
            validator.validate(mutation)


def test_run_summary_schema_rejects_status_exit_domain_and_manifest_mismatches() -> None:
    validator = _validator("run-summary-v1.schema.json")
    complete = json.loads(
        (SEMANTIC_GOLDEN_ROOT / "whole" / "stdout.run-summary.jsonl").read_text(encoding="utf-8")
    )
    mutations = []
    for key, value in (
        ("exit_code", 3),
        ("run_status", "fatal"),
        ("manifest", None),
    ):
        mutation = deepcopy(complete)
        mutation[key] = value
        mutations.append(mutation)
    wrong_domain = deepcopy(complete)
    wrong_domain["domains"][0]["status"] = "not_applicable"
    mutations.append(wrong_domain)

    for mutation in mutations:
        with pytest.raises(ValidationError):
            validator.validate(mutation)


def test_stdout_result_schema_rejects_selector_status_and_reason_mismatches() -> None:
    validator = _validator("stdout-result-v1.schema.json")
    unavailable = {
        "type": "stdout_result",
        "schema": "code-structure-viz.stdout-result/v1",
        "selector": "python:semantic-json",
        "availability": False,
        "domain_status": "not_applicable",
        "stable_reason": "domain_not_applicable",
        "artifact": None,
    }
    mutations = []
    for key, value in (
        ("selector", "manifest"),
        ("domain_status", "incomplete"),
        ("stable_reason", "run_fatal"),
    ):
        mutation = {**unavailable, key: value}
        mutations.append(mutation)

    for mutation in mutations:
        with pytest.raises(ValidationError):
            validator.validate(mutation)


def test_diagnostic_schema_rejects_catalog_metadata_and_context_mismatches() -> None:
    validator = _validator("diagnostic-v1.schema.json")
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
    mutations = []
    for key, changed in (
        ("severity", "info"),
        ("domain", None),
        ("symbol", "secret"),
        ("recoverable", False),
        ("message", "arbitrary message"),
    ):
        mutations.append({**value, key: changed})

    for mutation in mutations:
        with pytest.raises(ValidationError):
            validator.validate(mutation)
