"""Final publication-v2 owner joins actual candidates, bytes and measurements."""

import base64
import hashlib
import json
from copy import copy
from importlib import import_module, util
from pathlib import Path
from typing import Any

import pytest
from jsonschema import ValidationError  # type: ignore[import-untyped]

from tests.contracts.next_final_publication_v2_fixtures import (
    capture_overflow_candidates_v3,
    complete_candidates_v3,
    entity_budget_candidates_v3,
    export_failure_candidates_v3,
    large_selected_stdout_candidates_v3,
    observed_zero_capture_candidates_v3,
    rejected_candidates_v3,
    source_failure_candidates_v3,
    stage_failed_candidates_v3,
    stderr_boundary_candidates_v3,
    target_failure_candidates_v3,
)
from tests.contracts.test_json_schemas import _validator
from tests.contracts.test_next_public_diagnostic_v3 import NODE_002_JSONL
from tests.contracts.test_next_semantic_core_v3 import MODULE_IDS, SOURCE_BYTES


def _literal_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _literal_sha(value: object) -> str:
    return hashlib.sha256(_literal_json(value)).hexdigest()


def _aligned_unavailable_cache(owner: Any, value: dict[str, Any]) -> Any:
    """Attacker reseals a claim; actual candidate/run/byte owners stay unchanged."""
    assert owner.candidates().run_decision().semantic_decision() is None
    assert owner.candidates().artifacts() == ()
    assert value["response"] is None and value["artifacts"] == []
    assert value["stdout"]["selector"] == "next:semantic-json"
    stdout = base64.b64decode(value["stdout"]["result_bytes_base64"])
    stderr = base64.b64decode(value["stderr"]["bytes_base64"])
    boundary = {
        "decision_run_fingerprint": None,
        "response_bytes": {"__bytes_hex__": ""},
        "validated_request_id": None,
        "response_sha256": None,
        "response_model_digest": None,
        "artifact_bytes": {},
        "artifact_descriptors": {},
        "selector": "next:semantic-json",
        "selected_stdout": {
            "allowed": True,
            "bytes": 0,
            "sha256": hashlib.sha256(b"").hexdigest(),
            "retained": {"__bytes_hex__": ""},
            "retained_bytes": 0,
            "partial_disposed": False,
            "publication_outcome": "published_artifact",
            "diagnostic_code": None,
        },
        "sealed_stdout_result": {"__bytes_hex__": stdout.hex()},
        "diagnostic_jsonl": {"__bytes_hex__": stderr.hex()},
        "measurement_digest": _literal_sha(value["measurements"]),
    }
    public = {
        "semantic_decision": value["semantic_decision"],
        "response": value["response"],
        "artifacts": value["artifacts"],
        "stdout": value["stdout"],
        "stderr": stderr.hex(),
        "measurements": value["measurements"],
    }
    assert len(boundary) == 12 and len(public) == 6
    value["seal"] = {
        "algorithm": "sha256",
        "sha256": _literal_sha(boundary),
        "preimage_sha256": _literal_sha(public),
    }
    forged = copy(owner)
    object.__setattr__(forged, "_record_bytes", _literal_json(value))
    return forged


@pytest.mark.parametrize(
    "group,key,kind",
    [
        (None, "version", "float"),
        (None, "version", "bool"),
        (None, "exit_code", "float"),
        ("public_stderr", "measured_bytes", "float"),
        ("public_stderr", "retained_bytes", "float"),
        ("selected_stdout", "measured_bytes", "float"),
        ("selected_stdout", "retained_bytes", "float"),
        ("selected_stdout", "retained_bytes", "bool"),
        ("adapter_stdout", "measured_bytes", "float"),
        ("adapter_stderr", "retained_bytes", "float"),
        ("adapter_stderr", "retained_bytes", "bool"),
    ],
)
def test_aligned_resealed_cache_cannot_coerce_native_counts_or_version(
    tmp_path: Path,
    group: str | None,
    key: str,
    kind: str,
) -> None:
    candidates = (
        observed_zero_capture_candidates_v3(tmp_path)
        if group is not None and group.startswith("adapter_")
        else stage_failed_candidates_v3(tmp_path, selector="next:semantic-json")
    )
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    owner = reference.retain_final_publication_v2(candidates)
    reference.project_final_publication_v2(owner)
    value = owner.record()
    location = value if group is None else value["measurements"][group]
    location[key] = float(location[key]) if kind == "float" else False
    forged = _aligned_unavailable_cache(owner, value)
    assert forged.record() == value
    if kind == "float":
        # JSON Schema's integer vocabulary accepts 0.0/2.0; owner-native types do not.
        _validator("next-publication-decision-v2.schema.json").validate(value)
    with pytest.raises((ValueError, ValidationError)):
        reference.project_final_publication_v2(forged)


def test_equal_content_foreign_candidates_and_run_do_not_replace_the_actual_owner(
    tmp_path: Path,
) -> None:
    original_path, foreign_path = tmp_path / "original", tmp_path / "foreign"
    original_path.mkdir()
    foreign_path.mkdir()
    original = stage_failed_candidates_v3(original_path, selector="next:semantic-json")
    foreign = stage_failed_candidates_v3(foreign_path, selector="next:semantic-json")
    assert original is not foreign
    assert original.run_decision() is not foreign.run_decision()
    assert original.record() == foreign.record()
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    validate = import_module(
        "tests.contracts.next_final_publication_v2_validation"
    ).validate_final_publication_v2
    owner = reference.retain_final_publication_v2(original)
    value = reference.project_final_publication_v2(owner)
    _validator("next-publication-decision-v2.schema.json").validate(value)
    with pytest.raises(ValueError, match="same candidates owner"):
        validate(value, owner, candidates=foreign)


def test_complete_final_owner_publishes_the_same_artifact_and_catalog_stderr(
    tmp_path: Path,
) -> None:
    candidates = complete_candidates_v3(tmp_path)
    module = "tests.contracts.next_final_publication_v2_reference"
    assert util.find_spec(module) is not None, "actual candidates have no final publication owner"
    reference = import_module(module)
    owner = reference.retain_final_publication_v2(candidates)
    value = reference.project_final_publication_v2(owner)
    assert owner.candidates() is candidates
    artifact = candidates.artifacts()[0]
    assert value["semantic_decision"] == candidates.run_decision().record()
    assert value["candidates"] == candidates.record()
    assert value["publication_outcome"] == "published" and value["exit_code"] == 0
    assert base64.b64decode(value["stdout"]["result_bytes_base64"]) == artifact.wire_bytes()
    assert value["stdout"]["candidate"] == artifact.descriptor()
    assert value["artifacts"] == [
        {
            "descriptor": artifact.descriptor(),
            "bytes_base64": base64.b64encode(artifact.wire_bytes()).decode("ascii"),
        }
    ]
    expected_row = {
        "type": "diagnostic",
        "schema": "code-structure-viz.diagnostic/v1",
        "domain": "next",
        "code": "CSV-NEXT-UNSUPPORTED-001",
        "severity": "info",
        "recoverable": True,
        "message": "A runtime-dependent pattern is intentionally represented as unknown.",
        "outcome": "complete",
        "ref_permission": "symbol",
        "path": None,
        "symbol": MODULE_IDS["src/value.ts"],
        "line": None,
    }
    expected_stderr = (
        json.dumps(expected_row, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        + b"\n"
    )
    assert owner.stdout_bytes() == artifact.wire_bytes()
    assert owner.stderr_bytes() == expected_stderr
    assert base64.b64decode(value["stderr"]["bytes_base64"]) == expected_stderr
    assert value["stderr"]["sha256"] == hashlib.sha256(expected_stderr).hexdigest()
    assert value["measurements"]["public_stderr"] == {
        "allowed": True,
        "measured_bytes": len(expected_stderr),
        "retained_bytes": len(expected_stderr),
    }
    assert value["measurements"]["selected_stdout"] == {
        "allowed": True,
        "measured_bytes": len(artifact.wire_bytes()),
        "retained_bytes": len(artifact.wire_bytes()),
    }
    _validator("next-publication-decision-v2.schema.json").validate(value)


def test_partial_safe_final_projection_keeps_private_proof_and_source_bytes_private(
    tmp_path: Path,
) -> None:
    candidates = source_failure_candidates_v3(
        tmp_path, "parse_file", isolated=True, selector="next:semantic-json"
    )
    core = candidates.run_decision().semantic_decision()
    assert core is not None
    transport = core.transport_candidate()
    assert transport.semantic_payload()["proof"]["failure_roots"]
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    owner = reference.retain_final_publication_v2(candidates)
    value = reference.project_final_publication_v2(owner)
    assert value["semantic_decision"]["outcome"] == "partial_safe"
    artifact_documents = [
        json.loads(base64.b64decode(row["bytes_base64"])) for row in value["artifacts"]
    ]
    stderr_rows = [json.loads(row) for row in owner.stderr_bytes().splitlines()]
    assert stderr_rows[0]["path"] == "src/value.ts"  # Catalog-authorized ref stays public.
    public_values = [value, json.loads(owner.stdout_bytes()), *stderr_rows, *artifact_documents]
    private_keys = {
        "proof",
        "content_base64",
        "source_bytes",
        "failure_roots",
        "affected_paths",
        "effect_edges",
        "raw_response_bytes",
        "raw_child_stderr",
        "raw_stderr",
        "pid",
        "pgid",
        "cwd",
    }
    public_strings: list[str] = []

    def check_public(item: Any) -> None:
        if isinstance(item, dict):
            assert not private_keys.intersection(item)
            for child in item.values():
                check_public(child)
        elif isinstance(item, list):
            for child in item:
                check_public(child)
        elif isinstance(item, str):
            public_strings.append(item)

    for document in public_values:
        check_public(document)
    response = transport.response_frame().raw_bytes
    assert base64.b64encode(response).decode("ascii") not in public_strings
    for content in SOURCE_BYTES.values():
        assert not any(content.decode().strip() in text for text in public_strings)
        assert base64.b64encode(content).decode("ascii") not in public_strings
    _validator("next-publication-decision-v2.schema.json").validate(value)


def test_target_unavailable_stdout_retains_the_actual_failed_target(tmp_path: Path) -> None:
    candidates = target_failure_candidates_v3(tmp_path, selector="next:semantic-json")
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    owner = reference.retain_final_publication_v2(candidates)
    value = reference.project_final_publication_v2(owner)
    assert value["publication_outcome"] == "published" and value["exit_code"] == 3
    assert value["response"] is not None and value["artifacts"] == []
    expected = {
        "type": "stdout_result",
        "schema": "code-structure-viz.stdout-result/v2",
        "selector": "next:semantic-json",
        "availability": False,
        "domain_status": "incomplete",
        "stable_reason": "target_payload_unavailable",
        "artifact": None,
        "target_failures": [{"target_key": "path:src/button.tsx", "reason": "missing"}],
    }
    actual = json.loads(owner.stdout_bytes())
    assert actual == expected
    _validator("stdout-result-v2.schema.json").validate(actual)


def test_observed_zero_capture_is_not_replaced_by_unobserved_null(tmp_path: Path) -> None:
    candidates = observed_zero_capture_candidates_v3(tmp_path)
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    validate = import_module(
        "tests.contracts.next_final_publication_v2_validation"
    ).validate_final_publication_v2
    owner = reference.retain_final_publication_v2(candidates)
    value = reference.project_final_publication_v2(owner)
    assert value["publication_outcome"] == "published" and value["exit_code"] == 3
    assert value["semantic_decision"]["provenance"]["failure_code"] == "CSV-NEXT-NODE-003"
    assert value["response"] is None
    for name in ("adapter_stdout", "adapter_stderr"):
        assert value["measurements"][name] == {
            "allowed": True,
            "measured_bytes": 0,
            "retained_bytes": 0,
        }
    value["measurements"].update(adapter_stdout=None, adapter_stderr=None)
    # Align both seal claims and cache; this still is not a new capture observation.
    changed = _aligned_unavailable_cache(owner, value)
    _validator("next-publication-decision-v2.schema.json").validate(value)
    with pytest.raises(ValueError, match="capture measurement"):
        validate(value, changed, candidates=candidates)


def test_unobserved_capture_cannot_be_zero_filled_in_aligned_metadata(tmp_path: Path) -> None:
    candidates = stage_failed_candidates_v3(tmp_path, selector="next:semantic-json")
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    validate = import_module(
        "tests.contracts.next_final_publication_v2_validation"
    ).validate_final_publication_v2
    owner = reference.retain_final_publication_v2(candidates)
    value = owner.record()
    for name in ("adapter_stdout", "adapter_stderr"):
        value["measurements"][name] = {
            "allowed": True,
            "measured_bytes": 0,
            "retained_bytes": 0,
        }
    changed = _aligned_unavailable_cache(owner, value)
    _validator("next-publication-decision-v2.schema.json").validate(value)
    with pytest.raises(ValueError, match="capture measurement"):
        validate(value, changed, candidates=candidates)


def test_stage_failure_final_owner_preserves_unobserved_capture_and_publishes_the_failure(
    tmp_path: Path,
) -> None:
    candidates = stage_failed_candidates_v3(tmp_path, selector="next:semantic-json")
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    owner = reference.retain_final_publication_v2(candidates)
    value = reference.project_final_publication_v2(owner)
    expected_stdout = (
        b'{"artifact":null,"availability":false,"domain_status":"incomplete",'
        b'"schema":"code-structure-viz.stdout-result/v2","selector":"next:semantic-json",'
        b'"stable_reason":"domain_payload_unavailable","type":"stdout_result"}\n'
    )
    assert owner.candidates() is candidates
    assert value["semantic_decision"] == candidates.run_decision().record()
    assert value["publication_outcome"] == "published" and value["exit_code"] == 3
    assert value["response"] is None and value["artifacts"] == []
    assert value["measurements"]["adapter_stdout"] is None
    assert value["measurements"]["adapter_stderr"] is None
    assert value["stdout"]["copy_status"] == "not_attempted"
    assert value["stdout"]["candidate"] is None
    assert value["stdout"]["availability"] is False
    assert owner.stdout_bytes() == expected_stdout
    assert owner.stderr_bytes() == NODE_002_JSONL
    assert base64.b64decode(value["stdout"]["result_bytes_base64"]) == expected_stdout
    assert value["measurements"]["selected_stdout"] == {
        "allowed": True,
        "measured_bytes": 0,
        "retained_bytes": 0,
    }
    assert value["measurements"]["public_stderr"] == {
        "allowed": True,
        "measured_bytes": 304,
        "retained_bytes": 304,
    }
    measurements = {
        "adapter_stdout": None,
        "adapter_stderr": None,
        "public_stderr": {"allowed": True, "measured_bytes": 304, "retained_bytes": 304},
        "selected_stdout": {"allowed": True, "measured_bytes": 0, "retained_bytes": 0},
    }
    measurement_sha = _literal_sha(measurements)
    assert measurement_sha == "55e1176ea7f986b17dd9179ef571767614c50f3fd10dd79a1b08afc092675bef"
    preimage = {
        "decision_run_fingerprint": None,
        "response_bytes": {"__bytes_hex__": ""},
        "validated_request_id": None,
        "response_sha256": None,
        "response_model_digest": None,
        "artifact_bytes": {},
        "artifact_descriptors": {},
        "selector": "next:semantic-json",
        "selected_stdout": {
            "allowed": True,
            "bytes": 0,
            "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "retained": {"__bytes_hex__": ""},
            "retained_bytes": 0,
            "partial_disposed": False,
            "publication_outcome": "published_artifact",
            "diagnostic_code": None,
        },
        "sealed_stdout_result": {"__bytes_hex__": expected_stdout.hex()},
        "diagnostic_jsonl": {"__bytes_hex__": NODE_002_JSONL.hex()},
        "measurement_digest": measurement_sha,
    }
    assert len(preimage) == 12
    boundary_sha = _literal_sha(preimage)
    assert boundary_sha == "b790e3d366dec43adad1c2ed0926e33d5961f81d699d40423370e3f66a822e27"
    assert value["seal"]["sha256"] == boundary_sha
    _validator("stdout-result-v2.schema.json").validate(json.loads(expected_stdout))
    _validator("next-publication-decision-v2.schema.json").validate(value)


@pytest.mark.parametrize("kind", ["parse_file", "read_file"])
def test_source_unavailable_is_published_with_its_same_validated_response(
    tmp_path: Path,
    kind: str,
) -> None:
    candidates = source_failure_candidates_v3(tmp_path, kind, selector="next:semantic-json")
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    owner = reference.retain_final_publication_v2(candidates)
    value = reference.project_final_publication_v2(owner)
    run = candidates.run_decision()
    core = run.semantic_decision()
    assert core is not None
    frame = core.transport_candidate().response_frame()
    assert value["publication_outcome"] == "published" and value["exit_code"] == 3
    assert value["semantic_decision"]["outcome"] == "payload_unavailable"
    assert value["semantic_decision"] == run.record()
    assert value["response"] == {
        "request_id": run.runtime_result().request_frame().request_id,
        "raw_sha256": hashlib.sha256(frame.raw_bytes).hexdigest(),
        "model_digest": core.transport_candidate().semantic_payload()["model_digest"],
        "byte_length": len(frame.raw_bytes),
    }
    assert value["artifacts"] == [] and value["stdout"]["copy_status"] == "not_attempted"
    for name in ("adapter_stdout", "adapter_stderr"):
        actual = candidates.record()["capture_measurements"][name]
        assert value["measurements"][name] == {
            "allowed": True,
            "measured_bytes": actual["captured_bytes"],
            "retained_bytes": actual["capture_retained_bytes"],
        }
    stderr_row = json.loads(owner.stderr_bytes())
    assert stderr_row["code"] == "CSV-NEXT-SOURCE-003"
    assert stderr_row["path"] == "src/value.ts" and stderr_row["symbol"] is None
    _validator("next-publication-decision-v2.schema.json").validate(value)


def test_rejected_core_can_publish_the_failure_but_not_an_eligible_response_link(
    tmp_path: Path,
) -> None:
    candidates = rejected_candidates_v3(tmp_path, selector="next:semantic-json")
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    owner = reference.retain_final_publication_v2(candidates)
    value = reference.project_final_publication_v2(owner)
    assert value["semantic_decision"]["provenance"]["failure_code"] == "CSV-NEXT-PROTOCOL-001"
    assert value["publication_outcome"] == "published" and value["exit_code"] == 3
    assert value["response"] is None and value["artifacts"] == []
    assert json.loads(owner.stderr_bytes())["code"] == "CSV-NEXT-PROTOCOL-001"
    assert value["stdout"]["copy_status"] == "not_attempted"
    _validator("next-publication-decision-v2.schema.json").validate(value)


@pytest.mark.parametrize("case", ["export", "entity_budget", "partial_safe"])
def test_other_validated_failures_preserve_their_semantic_axis_and_eligible_response(
    tmp_path: Path,
    case: str,
) -> None:
    if case == "export":
        candidates = export_failure_candidates_v3(tmp_path, selector="next:semantic-json")
        expected_code = "CSV-NEXT-EXPORT-001"
    elif case == "entity_budget":
        candidates = entity_budget_candidates_v3(tmp_path, selector="next:semantic-json")
        expected_code = "CSV-NEXT-LIMIT-005"
    else:
        candidates = source_failure_candidates_v3(
            tmp_path, "parse_file", isolated=True, selector="next:semantic-json"
        )
        expected_code = "CSV-NEXT-SOURCE-001"
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    owner = reference.retain_final_publication_v2(candidates)
    value = reference.project_final_publication_v2(owner)
    run = candidates.run_decision()
    core = run.semantic_decision()
    assert core is not None
    frame = core.transport_candidate().response_frame()
    assert value["publication_outcome"] == "published" and value["exit_code"] == 3
    assert value["semantic_decision"] == run.record()
    assert value["response"]["raw_sha256"] == hashlib.sha256(frame.raw_bytes).hexdigest()
    assert {json.loads(row)["code"] for row in owner.stderr_bytes().splitlines()} == {expected_code}
    if case == "partial_safe":
        assert value["semantic_decision"]["outcome"] == "partial_safe"
        assert value["stdout"]["copy_status"] == "published"
        assert owner.stdout_bytes() == candidates.artifacts()[0].wire_bytes()
    else:
        assert value["semantic_decision"]["outcome"] == "payload_unavailable"
        assert value["artifacts"] == [] and value["stdout"]["copy_status"] == "not_attempted"
    _validator("next-publication-decision-v2.schema.json").validate(value)


@pytest.mark.parametrize("stream,measured", [("stdout", 16_777_217), ("stderr", 65_537)])
def test_actual_adapter_capture_overflow_is_a_publication_failure_not_null_capture(
    tmp_path: Path,
    stream: str,
    measured: int,
) -> None:
    candidates = capture_overflow_candidates_v3(tmp_path, stream)
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    owner = reference.retain_final_publication_v2(candidates)
    value = reference.project_final_publication_v2(owner)
    assert value["publication_outcome"] == "payload_unavailable" and value["exit_code"] == 3
    assert value["response"] is None and value["artifacts"] == []
    assert value["measurements"]["adapter_" + stream] == {
        "allowed": False,
        "measured_bytes": measured,
        "retained_bytes": 0,
    }
    other = "stderr" if stream == "stdout" else "stdout"
    assert value["measurements"]["adapter_" + other] == {
        "allowed": True,
        "measured_bytes": 0,
        "retained_bytes": 0,
    }
    assert value["stdout"]["copy_status"] == "not_attempted"
    assert value["measurements"]["selected_stdout"] == {
        "allowed": True,
        "measured_bytes": 0,
        "retained_bytes": 0,
    }
    assert json.loads(owner.stderr_bytes())["code"] == "CSV-NEXT-LIMIT-003"
    _validator("next-publication-decision-v2.schema.json").validate(value)


@pytest.mark.parametrize("delta", [0, 1])
def test_configured_public_stderr_boundary_keeps_all_or_no_bytes(
    tmp_path: Path, delta: int
) -> None:
    candidates = stderr_boundary_candidates_v3(tmp_path, delta)
    request = candidates.run_decision().runtime_result().request_frame().record()
    assert request["limits"]["max_stderr_bytes"] == 65_536
    # Independent catalog literal and stdlib codec, not the diagnostic producer.
    rows = [
        {
            "type": "diagnostic",
            "schema": "code-structure-viz.diagnostic/v1",
            "domain": "next",
            "code": "CSV-NEXT-TARGET-001",
            "severity": "error",
            "recoverable": False,
            "message": "An explicit Next.js target cannot be resolved uniquely.",
            "outcome": "payload_unavailable",
            "ref_permission": "path_or_symbol",
            "path": target.removeprefix("path:"),
            "symbol": None,
            "line": None,
            "reason": "missing",
        }
        for target in request["targets"]
    ]
    expected = b"".join(
        json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode() + b"\n"
        for row in rows
    )
    assert len(expected) == 65_536 + delta
    assert hashlib.sha256(expected).hexdigest() == (
        "702dbbfdd93207ea5e659026f9706d8278a3568eaf401394f57adfda56411216"
        if delta == 0
        else "c9373a44926510bbf4508a8702e0f8f9b217764ea4f1f7979f342c61b3e3a08b"
    )
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    owner = reference.retain_final_publication_v2(candidates)
    value = reference.project_final_publication_v2(owner)
    assert value["measurements"]["public_stderr"] == {
        "allowed": delta == 0,
        "measured_bytes": 65_536 + delta,
        "retained_bytes": 65_536 if delta == 0 else 0,
    }
    if delta == 0:
        assert owner.stderr_bytes() == expected
        assert value["publication_outcome"] == "published"
        assert value["response"] is not None
    else:
        assert owner.stderr_bytes() == b""
        assert value["publication_outcome"] == "payload_unavailable"
        assert value["response"] is None and value["artifacts"] == []
        assert len(owner.manifest_diagnostics()) == 1
        assert owner.manifest_diagnostics()[0]["code"] == "CSV-NEXT-LIMIT-003"
        assert json.loads(owner.stdout_bytes())["stable_reason"] == "domain_payload_unavailable"
    _validator("next-publication-decision-v2.schema.json").validate(value)


@pytest.mark.parametrize("delta", [0, 1])
def test_configured_selected_stdout_boundary_retains_the_original_candidate_measurement(
    tmp_path: Path,
    delta: int,
) -> None:
    candidates, expected = large_selected_stdout_candidates_v3(tmp_path, delta)
    artifact = candidates.artifacts()[0]
    assert artifact.wire_bytes() == expected
    assert len(expected) == 16_777_216 + delta
    assert artifact.descriptor()["size_bytes"] == 16_777_216 + delta
    assert (
        candidates.run_decision()
        .runtime_result()
        .request_frame()
        .record()["limits"]["max_selected_stdout_bytes"]
        == 16_777_216
    )
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    owner = reference.retain_final_publication_v2(candidates)
    value = reference.project_final_publication_v2(owner)
    assert value["measurements"]["selected_stdout"] == {
        "allowed": delta == 0,
        "measured_bytes": 16_777_216 + delta,
        "retained_bytes": 16_777_216 if delta == 0 else 0,
    }
    assert value["semantic_decision"]["status"] == "complete"
    assert value["response"] is not None
    assert value["stdout"]["candidate"] == artifact.descriptor()
    assert value["artifacts"][0]["descriptor"] == artifact.descriptor()
    if delta == 0:
        assert owner.stdout_bytes() == expected
        assert value["publication_outcome"] == "published" and value["exit_code"] == 0
    else:
        assert value["publication_outcome"] == "selected_artifact_unavailable"
        assert value["exit_code"] == 3 and value["stdout"]["copy_status"] == "unavailable"
        replacement = json.loads(owner.stdout_bytes())
        assert replacement["stable_reason"] == "selected_artifact_unavailable"
        assert replacement["artifact"] == artifact.descriptor()
        assert replacement["selected_stdout_unavailable"] is True
        assert value["stdout"]["result_size_bytes"] == len(owner.stdout_bytes()) < 16_777_216
        assert value["stdout"]["result_sha256"] == hashlib.sha256(owner.stdout_bytes()).hexdigest()
        assert json.loads(owner.stderr_bytes())["code"] == "CSV-NEXT-LIMIT-003"
        assert json.loads(owner.stderr_bytes())["scope"] == "publication"
        _validator("stdout-result-v2.schema.json").validate(replacement)
    _validator("next-publication-decision-v2.schema.json").validate(value)
