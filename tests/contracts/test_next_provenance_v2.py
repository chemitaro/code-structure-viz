"""Public provenance uses actual owner values, never stage-guessed success suffixes."""

import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from jsonschema import ValidationError  # type: ignore[import-untyped]

from tests.contracts import next_runtime_v2_reference, next_runtime_v2_validation
from tests.contracts.test_next_exchange_v2 import exchange_evidence, request_inputs, shape_wire
from tests.contracts.test_next_process_observation_v2 import complete_evidence
from tests.contracts.test_next_semantic_candidate_v2 import core_inputs, update_model_digest

SLOTS = (
    "applicability",
    "config",
    "source",
    "limits",
    "source_plan",
    "trusted_environment",
    "runtime_bundle",
    "node_candidate",
    "request",
    "launch_policy",
    "process_start",
    "node_version",
    "control_response",
    "semantic_payload",
    "compatibility",
    "model",
    "budget",
)


def complete_core_runtime(
    tmp_path: Path,
) -> tuple[
    next_runtime_v2_reference.RetainedRuntimeResultV2,
    next_runtime_v2_reference.ValidatedSemanticDecisionV2,
]:
    """Known corpus + real source acquisition; process observations remain synthetic."""

    seal, assets, request, policy, wire = core_inputs(tmp_path)
    response = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(wire).encode(), limits=request.record()["limits"]
    )
    observation = next_runtime_v2_reference.reference_process_observation_v2(
        policy, exchange_evidence(policy, request, response)
    )
    runtime = next_runtime_v2_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, response
    )
    candidate = runtime.transport_candidate()
    assert candidate is not None
    return runtime, next_runtime_v2_reference.decide_semantic_candidate_v2(candidate, seal, assets)


def test_unsupported_runtime_keeps_its_real_prefix_without_semantic_observations(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    wire = shape_wire(request)
    wire["control"].update(
        result_kind="unsupported_runtime",
        runtime={
            "engine": "node",
            "version_raw": "20.19.0",
            "version": "20.19.0",
            "eligibility": "unsupported",
            "observation_source": "process.versions.node",
        },
    )
    wire["semantic_payload"] = None
    response = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(wire).encode(), limits=request.record()["limits"]
    )
    evidence = exchange_evidence(policy, request, response)
    evidence["exit_code"] = 66
    observation = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    runtime = next_runtime_v2_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, response
    )
    provenance = next_runtime_v2_reference.runtime_provenance_v2(runtime)

    assert provenance["schema"] == "code-structure-viz.next-provenance/v2"
    assert (provenance["kind"], provenance["stage"], provenance["failure_code"]) == (
        "request_bound_failure",
        "runtime_validation",
        "CSV-NEXT-NODE-001",
    )
    assert set(provenance["observed"]) == set(SLOTS)
    assert [key for key in SLOTS if provenance["observed"][key]["state"] == "observed"] == list(
        SLOTS[:13]
    )
    assert all(
        provenance["observed"][key] == {"state": "unobserved", "value": None} for key in SLOTS[13:]
    )


def test_success_provenance_requires_the_matching_core_decision_not_a_transport_boolean(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy, wire = core_inputs(tmp_path, targets=["path:src/Card.tsx"])
    response = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(wire).encode(), limits=request.record()["limits"]
    )
    observation = next_runtime_v2_reference.reference_process_observation_v2(
        policy, exchange_evidence(policy, request, response)
    )
    runtime = next_runtime_v2_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, response
    )
    candidate = runtime.transport_candidate()
    assert candidate is not None
    decision = next_runtime_v2_reference.decide_semantic_candidate_v2(candidate, seal, assets)
    provenance = next_runtime_v2_reference.runtime_provenance_v2(
        runtime, semantic_decision=decision
    )
    assert (provenance["kind"], provenance["stage"], provenance["failure_code"]) == (
        "request_bound_success",
        None,
        None,
    )
    assert all(provenance["observed"][key]["state"] == "observed" for key in SLOTS)


def test_process_start_hash_describes_spawn_parameters_not_expected_compiler_metadata(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy, wire = core_inputs(tmp_path)
    response = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(wire).encode(), limits=request.record()["limits"]
    )
    observation = next_runtime_v2_reference.reference_process_observation_v2(
        policy, exchange_evidence(policy, request, response)
    )
    runtime = next_runtime_v2_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, response
    )
    candidate = runtime.transport_candidate()
    assert candidate is not None
    decision = next_runtime_v2_reference.decide_semantic_candidate_v2(candidate, seal, assets)
    provenance = next_runtime_v2_reference.runtime_provenance_v2(
        runtime, semantic_decision=decision
    )
    # Fixed ASCII preimages worked independently with jq -cSj | shasum, not the producer.
    assert provenance["observed"]["process_start"]["value"]["sha256"] == (
        "3869aabc86551c31c55fca1229360dc3efe591ab6449bb33dc465a3b8bf6b5d4"
    )
    assert provenance["observed"]["node_candidate"]["value"]["sha256"] == (
        "49629589791b75238da6a7744ddb40b19386eb9482a8e05a90a2bf2717870def"
    )


def test_provenance_has_its_own_closed_v2_schema_not_an_additive_legacy_view() -> None:
    # Shape-only vector: these digests are deliberately not an owner certificate.
    value: dict[str, Any] = {
        "schema": "code-structure-viz.next-provenance/v2",
        "kind": "request_bound_failure",
        "stage": "runtime_validation",
        "failure_code": "CSV-NEXT-NODE-001",
        "observed": {
            key: {
                "state": "observed",
                "value": {
                    "schema": "code-structure-viz.next-observation/v2",
                    "version": 2,
                    "sha256": "1" * 64,
                },
            }
            if index < 13
            else {"state": "unobserved", "value": None}
            for index, key in enumerate(SLOTS)
        },
    }
    next_runtime_v2_validation.validate_provenance_shape_v2(value)
    wrong_identity = deepcopy(value)
    wrong_identity["schema"] = "code-structure-viz.next-provenance/v1"
    old_slot = deepcopy(value)
    old_slot["observed"]["toolchain"] = old_slot["observed"]["node_version"]
    wrong_version = deepcopy(value)
    wrong_version["observed"]["request"]["value"]["version"] = 1
    fabricated_suffix = deepcopy(value)
    fabricated_suffix["observed"]["model"] = fabricated_suffix["observed"]["request"]
    for mutation in (wrong_identity, old_slot, wrong_version, fabricated_suffix):
        with pytest.raises(ValidationError):
            next_runtime_v2_validation.validate_provenance_shape_v2(mutation)


def test_timeout_prefix_stops_before_version_but_keeps_the_prepared_request(tmp_path: Path) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    evidence = complete_evidence(policy)
    evidence.update(response=None, terminal_cause="timeout", exit_code=-15)
    evidence["capture"].update(
        stdin_bytes=len(request.canonical_bytes),
        stdin_sent_bytes=len(request.canonical_bytes),
        stdout_bytes=17,
        stdout_retained_bytes=0,
        stdout_eof=False,
    )
    evidence["cleanup"].update(group_stop="verified", signals=["TERM"])
    observation = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    result = next_runtime_v2_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, None
    )
    provenance = next_runtime_v2_reference.runtime_provenance_v2(result)
    assert (provenance["stage"], provenance["failure_code"]) == (
        "node_timeout",
        "CSV-NEXT-NODE-003",
    )
    assert [key for key in SLOTS if provenance["observed"][key]["state"] == "observed"] == list(
        SLOTS[:11]
    )
    next_runtime_v2_validation.validate_provenance_shape_v2(provenance)


@pytest.mark.parametrize("cause", ["stage_failed", "spawn_failed"])
def test_failed_prelaunch_never_claims_a_started_process_or_runtime(
    tmp_path: Path, cause: str
) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    evidence = complete_evidence(policy)
    evidence.update(spawn=None, capture=None, response=None, exit_code=None, terminal_cause=cause)
    evidence["cleanup"]["direct_child_waited"] = False
    observation = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    runtime = next_runtime_v2_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, None
    )
    value = next_runtime_v2_reference.runtime_provenance_v2(runtime)
    assert (value["kind"], value["stage"], value["failure_code"]) == (
        "request_bound_failure",
        "node_spawn",
        "CSV-NEXT-NODE-002",
    )
    assert [key for key in SLOTS if value["observed"][key]["state"] == "observed"] == list(
        SLOTS[:10]
    )
    next_runtime_v2_validation.validate_runtime_provenance_v2(value, runtime)


@pytest.mark.parametrize(
    ("stream", "measured", "stage"),
    [
        ("stdout", 16_777_217, "adapter_stdout_capture"),
        ("stderr", 65_537, "adapter_stderr_capture"),
    ],
)
def test_capture_cap_plus_one_has_limit_failure_without_a_semantic_suffix(
    tmp_path: Path, stream: str, measured: int, stage: str
) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    evidence = complete_evidence(policy)
    evidence.update(response=None, exit_code=-15, terminal_cause=stream + "_limit")
    evidence["capture"].update(
        stdin_bytes=len(request.canonical_bytes),
        stdin_sent_bytes=len(request.canonical_bytes),
        stdout_bytes=0,
        stdout_retained_bytes=0,
        stderr_bytes=0,
        stderr_retained_bytes=0,
    )
    evidence["capture"][stream + "_bytes"] = measured
    evidence["capture"][stream + "_eof"] = False
    evidence["cleanup"].update(group_stop="verified", signals=["TERM"])
    observation = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    runtime = next_runtime_v2_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, None
    )
    value = next_runtime_v2_reference.runtime_provenance_v2(runtime)
    assert (value["stage"], value["failure_code"]) == (stage, "CSV-NEXT-LIMIT-003")
    assert [key for key in SLOTS if value["observed"][key]["state"] == "observed"] == list(
        SLOTS[:11]
    )
    next_runtime_v2_validation.validate_runtime_provenance_v2(value, runtime)


@pytest.mark.parametrize("cause", ["write_failed", "read_failed"])
def test_transport_io_failure_keeps_prepared_request_but_no_invented_control(
    tmp_path: Path, cause: str
) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    evidence = complete_evidence(policy)
    evidence.update(response=None, exit_code=-15, terminal_cause=cause)
    evidence["capture"].update(
        stdin_bytes=len(request.canonical_bytes),
        stdin_sent_bytes=1 if cause == "write_failed" else len(request.canonical_bytes),
        stdout_bytes=0 if cause == "write_failed" else 17,
        stdout_retained_bytes=0,
        stdout_eof=False,
    )
    evidence["cleanup"].update(group_stop="verified", signals=["TERM"])
    observation = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    runtime = next_runtime_v2_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, None
    )
    value = next_runtime_v2_reference.runtime_provenance_v2(runtime)
    assert (value["stage"], value["failure_code"]) == ("node_process", "CSV-NEXT-NODE-004")
    assert [key for key in SLOTS if value["observed"][key]["state"] == "observed"] == list(
        SLOTS[:11]
    )
    next_runtime_v2_validation.validate_runtime_provenance_v2(value, runtime)


@pytest.mark.parametrize(
    ("cause", "stage", "code"),
    [
        ("binding_mismatch", "response_validation", "CSV-NEXT-PROTOCOL-001"),
        ("exit_mismatch", "node_process", "CSV-NEXT-NODE-004"),
    ],
)
def test_complete_control_mismatch_preserves_actual_prefix_without_a_candidate(
    tmp_path: Path, cause: str, stage: str, code: str
) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    wire = shape_wire(request)
    if cause == "binding_mismatch":
        wire["control"]["binding"]["request_id"] = "0" * 64
    frame = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(wire).encode(), limits=request.record()["limits"]
    )
    evidence = exchange_evidence(policy, request, frame)
    evidence["terminal_cause"] = cause
    evidence["capture"]["stdout_retained_bytes"] = 0
    if cause == "exit_mismatch":
        evidence["exit_code"] = 1
    observation = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    runtime = next_runtime_v2_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, frame
    )
    value = next_runtime_v2_reference.runtime_provenance_v2(runtime)
    assert (value["stage"], value["failure_code"]) == (stage, code)
    assert [key for key in SLOTS if value["observed"][key]["state"] == "observed"] == list(
        SLOTS[:13]
    )
    assert runtime.control() == wire["control"]
    assert runtime.transport_candidate() is None
    next_runtime_v2_validation.validate_runtime_provenance_v2(value, runtime)


def test_invalid_semantic_echo_is_protocol_failure_with_only_the_control_prefix(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    wire = shape_wire(request)
    wire["semantic_payload"]["trusted_type_environment_digest"] = "0" * 64
    frame = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(wire).encode(), limits=request.record()["limits"]
    )
    evidence = exchange_evidence(policy, request, frame)
    evidence["terminal_cause"] = "response_invalid"
    evidence["capture"]["stdout_retained_bytes"] = 0
    observation = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    runtime = next_runtime_v2_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, frame
    )
    value = next_runtime_v2_reference.runtime_provenance_v2(runtime)
    assert (value["stage"], value["failure_code"]) == (
        "response_validation",
        "CSV-NEXT-PROTOCOL-001",
    )
    assert [key for key in SLOTS if value["observed"][key]["state"] == "observed"] == list(
        SLOTS[:13]
    )
    assert runtime.transport_candidate() is None
    next_runtime_v2_validation.validate_runtime_provenance_v2(value, runtime)


def test_proof_bound_target_failure_is_not_success_and_has_no_entity_measurement(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy, wire = core_inputs(tmp_path, targets=["path:src/Card.tsx"])
    model, proof = wire["semantic_payload"]["model"], wire["semantic_payload"]["proof"]
    model["modules"], model["facts"] = [], []
    model["coverage"]["counts"].update(
        modules=0, facts=0, internal_entities=0, published=5, discovered=5
    )
    proof["discovered_records"] = [
        row for row in proof["discovered_records"] if row["collection"] not in {"modules", "facts"}
    ]
    failed_target = {
        "target_key": "path:src/Card.tsx",
        "status": "failed",
        "record_ids": [],
        "reason": "missing",
    }
    proof["target_resolutions"] = [deepcopy(failed_target)]
    model["coverage"]["target_completeness"] = [deepcopy(failed_target)]
    update_model_digest(wire)
    response = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(wire).encode(), limits=request.record()["limits"]
    )
    observation = next_runtime_v2_reference.reference_process_observation_v2(
        policy, exchange_evidence(policy, request, response)
    )
    runtime = next_runtime_v2_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, response
    )
    candidate = runtime.transport_candidate()
    assert candidate is not None
    decision = next_runtime_v2_reference.decide_semantic_candidate_v2(candidate, seal, assets)
    provenance = next_runtime_v2_reference.runtime_provenance_v2(
        runtime, semantic_decision=decision
    )
    assert (provenance["kind"], provenance["stage"], provenance["failure_code"]) == (
        "request_bound_failure",
        "target_resolution",
        "CSV-NEXT-TARGET-001",
    )
    assert [key for key in SLOTS if provenance["observed"][key]["state"] == "observed"] == list(
        SLOTS[:16]
    )
    assert provenance["observed"]["budget"] == {"state": "unobserved", "value": None}
    next_runtime_v2_validation.validate_provenance_shape_v2(provenance)


@pytest.mark.parametrize("cause", ["cleanup_unverified", "candidate_drift", "assets_drift"])
def test_late_failure_cannot_erase_already_joined_version_and_control(
    tmp_path: Path, cause: str
) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    response = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(shape_wire(request)).encode(), limits=request.record()["limits"]
    )
    evidence = exchange_evidence(policy, request, response)
    evidence["terminal_cause"] = cause
    evidence["capture"]["stdout_retained_bytes"] = 0
    if cause == "cleanup_unverified":
        evidence["cleanup"]["private_root_removed"] = False
    else:
        evidence[cause.removesuffix("_drift") + "_check"] = "drift"
    observation = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    runtime = next_runtime_v2_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, response
    )
    provenance = next_runtime_v2_reference.runtime_provenance_v2(runtime)
    assert (provenance["stage"], provenance["failure_code"]) == (
        "node_process",
        "CSV-NEXT-NODE-004",
    )
    assert [key for key in SLOTS if provenance["observed"][key]["state"] == "observed"] == list(
        SLOTS[:13]
    )
    next_runtime_v2_validation.validate_provenance_shape_v2(provenance)


def test_schema_valid_rehashed_observations_must_still_match_the_actual_retained_owners(
    tmp_path: Path,
) -> None:
    runtime, decision = complete_core_runtime(tmp_path)
    value = next_runtime_v2_reference.runtime_provenance_v2(runtime, semantic_decision=decision)
    next_runtime_v2_validation.validate_runtime_provenance_v2(
        value, runtime, semantic_decision=decision
    )
    changed = deepcopy(value)
    changed["observed"]["request"]["value"]["sha256"] = "0" * 64
    next_runtime_v2_validation.validate_provenance_shape_v2(changed)
    with pytest.raises(ValueError, match=r"observation.*retained"):
        next_runtime_v2_validation.validate_runtime_provenance_v2(
            changed, runtime, semantic_decision=decision
        )


def test_matching_digests_do_not_authorize_a_fabricated_failure_or_budget_status(
    tmp_path: Path,
) -> None:
    runtime, decision = complete_core_runtime(tmp_path)
    value = next_runtime_v2_reference.runtime_provenance_v2(runtime, semantic_decision=decision)
    value.update(
        kind="request_bound_failure", stage="model_validation", failure_code="CSV-NEXT-LIMIT-005"
    )
    next_runtime_v2_validation.validate_provenance_shape_v2(value)
    with pytest.raises(ValueError, match=r"provenance.*result identity"):
        next_runtime_v2_validation.validate_runtime_provenance_v2(
            value, runtime, semantic_decision=decision
        )


@pytest.mark.parametrize(
    ("kind", "exit_code", "stage", "code"),
    [
        ("protocol_failure", 65, "response_protocol", "CSV-NEXT-PROTOCOL-001"),
        ("bootstrap_failure", 67, "bootstrap", "CSV-NEXT-NODE-004"),
        ("semantic_failure", 68, "semantic_analysis", "CSV-NEXT-NODE-004"),
    ],
)
def test_closed_child_failures_use_their_actual_control_prefix_not_success_defaults(
    tmp_path: Path, kind: str, exit_code: int, stage: str, code: str
) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    wire = shape_wire(request)
    wire["control"]["result_kind"] = kind
    if kind != "semantic_failure":
        wire["control"].update(runtime=None, binding={"state": "unbound", "request_id": None})
    wire["semantic_payload"] = None
    response = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(wire).encode(), limits=request.record()["limits"]
    )
    evidence = exchange_evidence(policy, request, response)
    evidence["exit_code"] = exit_code
    observation = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    result = next_runtime_v2_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, response
    )
    value = next_runtime_v2_reference.runtime_provenance_v2(result)
    assert (value["kind"], value["stage"], value["failure_code"]) == (
        "request_bound_failure",
        stage,
        code,
    )
    observed_keys = list(SLOTS[:13])
    if kind != "semantic_failure":
        observed_keys.remove("node_version")
    assert [key for key in SLOTS if value["observed"][key]["state"] == "observed"] == observed_keys
    next_runtime_v2_validation.validate_runtime_provenance_v2(value, result)


def test_host_relocation_and_pid_changes_do_not_change_portable_provenance(tmp_path: Path) -> None:
    original, original_decision = complete_core_runtime(tmp_path)
    candidate = original.transport_candidate()
    assert candidate is not None
    seal, assets, request = (
        original.source_seal(),
        original.execution_assets(),
        original.request_frame(),
    )
    policy = original.policy()
    policy["node_candidate"]["absolute_path"] = "/opt/relocated/node"
    policy["private_root"] = "/private/tmp/csv-relocated-e\u0301"
    policy["runtime_directory"] = policy["private_root"] + "/runtime"
    policy["cwd"] = policy["private_root"] + "/cwd"
    policy["argv"][0] = policy["node_candidate"]["absolute_path"]
    policy["argv"][2] = policy["runtime_directory"] + "/next-adapter.mjs"
    response = candidate.response_frame()
    evidence = exchange_evidence(policy, request, response)
    evidence["spawn"].update(pid=9876, pgid=9876)
    observation = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    relocated = next_runtime_v2_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, response
    )
    relocated_candidate = relocated.transport_candidate()
    assert relocated_candidate is not None
    relocated_decision = next_runtime_v2_reference.decide_semantic_candidate_v2(
        relocated_candidate, seal, assets
    )
    original_value = next_runtime_v2_reference.runtime_provenance_v2(
        original, semantic_decision=original_decision
    )
    relocated_value = next_runtime_v2_reference.runtime_provenance_v2(
        relocated, semantic_decision=relocated_decision
    )
    assert original.observation()["policy_digest"] != relocated.observation()["policy_digest"]
    assert original_value == relocated_value
    public_json = json.dumps(relocated_value)
    assert "/private/tmp/" not in public_json and "/opt/relocated/" not in public_json
    assert "const Card = 1" not in public_json and "discovered_records" not in public_json
    next_runtime_v2_validation.validate_runtime_provenance_v2(
        relocated_value, relocated, semantic_decision=relocated_decision
    )


def test_provenance_cannot_borrow_a_core_owner_from_another_identical_exchange(
    tmp_path: Path,
) -> None:
    runtime, decision = complete_core_runtime(tmp_path)
    candidate = runtime.transport_candidate()
    assert candidate is not None
    other = next_runtime_v2_reference.retain_runtime_result_v2(
        runtime.source_seal(),
        runtime.execution_assets(),
        runtime.request_frame(),
        runtime.policy(),
        runtime.observation(),
        candidate.response_frame(),
    )
    with pytest.raises(ValueError, match="same runtime owner"):
        next_runtime_v2_reference.runtime_provenance_v2(other, semantic_decision=decision)
    with pytest.raises(ValueError, match="closed provenance branch"):
        next_runtime_v2_reference.runtime_provenance_v2(runtime)
    with pytest.raises(TypeError, match="retained runtime result owner"):
        next_runtime_v2_reference.runtime_provenance_v2(SimpleNamespace())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="Core decision owner"):
        next_runtime_v2_reference.runtime_provenance_v2(
            runtime,
            semantic_decision=SimpleNamespace(gate=decision.gate),  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("field_name", SLOTS)
def test_each_public_observation_is_joined_to_its_actual_value_not_a_marker(
    tmp_path: Path, field_name: str
) -> None:
    runtime, decision = complete_core_runtime(tmp_path)
    value = next_runtime_v2_reference.runtime_provenance_v2(runtime, semantic_decision=decision)
    value["observed"][field_name]["value"]["sha256"] = "0" * 64
    next_runtime_v2_validation.validate_provenance_shape_v2(value)
    with pytest.raises(ValueError, match="observation digest"):
        next_runtime_v2_validation.validate_runtime_provenance_v2(
            value, runtime, semantic_decision=decision
        )
