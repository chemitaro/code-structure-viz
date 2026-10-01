"""Core rejection is a typed result, never a caller-owned success or error label."""

import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from code_structure_viz.adapters.next.source_acquisition import SourceAcquisitionSeal
from tests.contracts import next_runtime_v2_reference, next_runtime_v2_validation
from tests.contracts.test_next_exchange_v2 import exchange_evidence
from tests.contracts.test_next_provenance_v2 import SLOTS
from tests.contracts.test_next_semantic_candidate_v2 import (
    candidate_for,
    core_inputs,
    model_record_inputs,
    update_model_digest,
)


def runtime_for_core_wire(
    seal: SourceAcquisitionSeal,
    assets: next_runtime_v2_reference.RetainedExecutionAssets,
    request: next_runtime_v2_reference.RetainedRequestFrameV2,
    policy: dict[str, Any],
    wire: dict[str, Any],
) -> next_runtime_v2_reference.RetainedRuntimeResultV2:
    frame = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(wire).encode(), limits=request.record()["limits"]
    )
    observation = next_runtime_v2_reference.reference_process_observation_v2(
        policy, exchange_evidence(policy, request, frame)
    )
    return next_runtime_v2_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, frame
    )


def test_shape_valid_bad_model_digest_becomes_a_closed_core_rejection(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = core_inputs(tmp_path)
    wire["semantic_payload"]["model_digest"] = "0" * 64
    candidate = candidate_for(seal, assets, request, policy, wire)
    decision = next_runtime_v2_reference.inspect_semantic_candidate_v2(candidate, seal, assets)
    assert type(decision) is next_runtime_v2_reference.RejectedSemanticDecisionV2
    assert decision.failure() == {
        "stage": "response_validation",
        "diagnostic_code": "CSV-NEXT-PROTOCOL-001",
        "reason": "model_digest",
        "model_records": None,
    }
    assert decision.transport_candidate() is candidate
    assert decision.source_seal() is seal
    assert decision.execution_assets() is assets
    assert decision.request_id == request.request_id
    assert not hasattr(decision, "gate")
    assert not hasattr(decision, "compatibility_descriptor")
    assert "const Card" not in repr(decision)


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ("project", "project_correspondence"),
        ("file", "file_correspondence"),
        ("source_proof", "proof_source_owner"),
        ("module_proof", "proof_module_owner"),
        ("dangling_proof", "proof_references"),
        ("proof", "model_proof"),
    ],
)
def test_payload_invariant_rejections_have_closed_reasons_not_exception_text(
    tmp_path: Path, mutation: str, reason: str
) -> None:
    seal, assets, request, policy, wire = core_inputs(tmp_path)
    model, proof = wire["semantic_payload"]["model"], wire["semantic_payload"]["proof"]
    if mutation == "project":
        model["projects"][0]["config_digest"] = "0" * 64
    elif mutation == "file":
        model["files"][0]["sha256"] = "0" * 64
    elif mutation == "source_proof":
        proof["discovered_records"][0]["record"] = deepcopy(model["projects"][0])
    elif mutation == "module_proof":
        record = deepcopy(model["modules"][0])
        record["path"] = "src/ghost.tsx"
        proof["discovered_records"].append(
            {"collection": "modules", "record_id": record["id"], "taints": [], "record": record}
        )
    elif mutation == "dangling_proof":
        record = deepcopy(model["facts"][0])
        record.update(id="next:fact:" + "1" * 64, owner_id="next:module:" + "0" * 64)
        proof["discovered_records"].append(
            {"collection": "facts", "record_id": record["id"], "taints": [], "record": record}
        )
        model["coverage"]["counts"].update(discovered=8, excluded=1)
    else:
        proof["discovered_records"].pop()
    update_model_digest(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    decision = next_runtime_v2_reference.inspect_semantic_candidate_v2(candidate, seal, assets)
    assert isinstance(decision, next_runtime_v2_reference.RejectedSemanticDecisionV2)
    assert decision.failure() == {
        "stage": "response_validation",
        "diagnostic_code": "CSV-NEXT-PROTOCOL-001",
        "reason": reason,
        "model_records": None,
    }


def test_valid_proof_model_record_plus_one_retains_the_actual_count_not_an_entity_budget(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy, wire = model_record_inputs(tmp_path, 1)
    runtime = runtime_for_core_wire(seal, assets, request, policy, wire)
    candidate = runtime.transport_candidate()
    assert candidate is not None
    decision = next_runtime_v2_reference.inspect_semantic_candidate_v2(candidate, seal, assets)
    assert isinstance(decision, next_runtime_v2_reference.RejectedSemanticDecisionV2)
    assert decision.failure() == {
        "stage": "model_validation",
        "diagnostic_code": "CSV-NEXT-LIMIT-005",
        "reason": "max_model_records",
        "model_records": 10_001,
    }
    value = next_runtime_v2_reference.runtime_provenance_v2(runtime, semantic_decision=decision)
    assert (value["kind"], value["stage"], value["failure_code"]) == (
        "request_bound_failure",
        "model_validation",
        "CSV-NEXT-LIMIT-005",
    )
    assert [key for key in SLOTS if value["observed"][key]["state"] == "observed"] == list(
        SLOTS[:13]
    )
    next_runtime_v2_validation.validate_runtime_provenance_v2(
        value, runtime, semantic_decision=decision
    )
    # Invalid proof takes priority over the later count gate.
    wire["semantic_payload"]["proof"]["discovered_records"].pop()
    invalid = candidate_for(seal, assets, request, policy, wire)
    invalid_decision = next_runtime_v2_reference.inspect_semantic_candidate_v2(
        invalid, seal, assets
    )
    assert isinstance(invalid_decision, next_runtime_v2_reference.RejectedSemanticDecisionV2)
    assert invalid_decision.failure()["diagnostic_code"] == "CSV-NEXT-PROTOCOL-001"
    assert invalid_decision.failure()["model_records"] is None


def test_core_rejection_preserves_actual_control_but_no_admitted_semantic_suffix(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy, wire = core_inputs(tmp_path)
    wire["semantic_payload"]["model_digest"] = "0" * 64
    frame = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(wire).encode(), limits=request.record()["limits"]
    )
    observation = next_runtime_v2_reference.reference_process_observation_v2(
        policy, exchange_evidence(policy, request, frame)
    )
    runtime = next_runtime_v2_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, frame
    )
    candidate = runtime.transport_candidate()
    assert candidate is not None
    decision = next_runtime_v2_reference.inspect_semantic_candidate_v2(candidate, seal, assets)
    assert isinstance(decision, next_runtime_v2_reference.RejectedSemanticDecisionV2)
    value = next_runtime_v2_reference.runtime_provenance_v2(runtime, semantic_decision=decision)
    assert (value["kind"], value["stage"], value["failure_code"]) == (
        "request_bound_failure",
        "response_validation",
        "CSV-NEXT-PROTOCOL-001",
    )
    assert [key for key in SLOTS if value["observed"][key]["state"] == "observed"] == list(
        SLOTS[:13]
    )
    assert runtime.control() == wire["control"]
    next_runtime_v2_validation.validate_runtime_provenance_v2(
        value, runtime, semantic_decision=decision
    )
    decision.failure().update(diagnostic_code="CSV-NEXT-NODE-004", model_records=10_001)
    decision.transport_candidate().semantic_payload()["model_digest"] = "1" * 64
    assert decision.failure()["diagnostic_code"] == "CSV-NEXT-PROTOCOL-001"
    assert decision.failure()["model_records"] is None
    assert (
        next_runtime_v2_reference.runtime_provenance_v2(runtime, semantic_decision=decision)
        == value
    )
    other_runtime = next_runtime_v2_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, frame
    )
    with pytest.raises(ValueError, match="not joined to the same runtime owner"):
        next_runtime_v2_reference.runtime_provenance_v2(other_runtime, semantic_decision=decision)


def test_core_failure_has_no_free_constructor_or_duck_owner(tmp_path: Path) -> None:
    with pytest.raises(TypeError, match="created by inspect"):
        next_runtime_v2_reference.RejectedSemanticDecisionV2()
    with pytest.raises(TypeError, match="rejected decision owner"):
        next_runtime_v2_validation.validate_rejected_semantic_decision_v2(
            cast(Any, SimpleNamespace())
        )
    seal, assets, _request, _policy, _wire = core_inputs(tmp_path)
    with pytest.raises(TypeError, match="transport candidate owner"):
        next_runtime_v2_reference.inspect_semantic_candidate_v2(
            cast(Any, SimpleNamespace()), seal, assets
        )


def test_owner_error_is_not_reclassified_as_child_payload_rejection(tmp_path: Path) -> None:
    original = tmp_path / "original"
    original.mkdir()
    seal, assets, request, policy, wire = core_inputs(original)
    wire["semantic_payload"]["model_digest"] = "0" * 64
    candidate = candidate_for(seal, assets, request, policy, wire)
    changed = tmp_path / "changed"
    changed.mkdir()
    other_seal, _assets, _request, _policy, _wire = core_inputs(changed, empty_membership=True)
    with pytest.raises(ValueError, match="source seal identity"):
        next_runtime_v2_reference.inspect_semantic_candidate_v2(candidate, other_seal, assets)


@pytest.mark.parametrize("error_type", [ValueError, RuntimeError, MemoryError, AssertionError])
def test_unrelated_internal_exception_escapes_instead_of_minting_protocol_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error_type: type[Exception]
) -> None:
    seal, assets, request, policy, wire = core_inputs(tmp_path)
    candidate = candidate_for(seal, assets, request, policy, wire)
    failure = error_type("private internal marker must not become a diagnostic")

    def fail_internal(*_args: object) -> dict[str, Any]:
        raise failure

    monkeypatch.setattr(next_runtime_v2_reference, "validate_semantic_candidate_v2", fail_internal)
    with pytest.raises(error_type) as captured:
        next_runtime_v2_reference.inspect_semantic_candidate_v2(candidate, seal, assets)
    assert captured.value is failure


@pytest.mark.parametrize("mutation", ["code", "reason", "count", "extra"])
def test_rehashed_or_free_failure_metadata_is_not_core_evidence(
    tmp_path: Path, mutation: str
) -> None:
    seal, assets, request, policy, wire = core_inputs(tmp_path)
    wire["semantic_payload"]["model_digest"] = "0" * 64
    candidate = candidate_for(seal, assets, request, policy, wire)
    decision = next_runtime_v2_reference.inspect_semantic_candidate_v2(candidate, seal, assets)
    assert isinstance(decision, next_runtime_v2_reference.RejectedSemanticDecisionV2)
    failure = decision.failure()
    if mutation == "code":
        failure["diagnostic_code"] = "CSV-NEXT-LIMIT-005"
    elif mutation == "reason":
        failure["reason"] = "max_model_records"
    elif mutation == "count":
        failure["model_records"] = 10_001
    else:
        failure["payload_available"] = True
    forged = next_runtime_v2_reference.RejectedSemanticDecisionV2._from_rejected_core(
        candidate, seal, assets, failure
    )
    with pytest.raises(ValueError, match="failure metadata differs"):
        next_runtime_v2_validation.validate_rejected_semantic_decision_v2(forged)


def test_valid_core_data_cannot_be_relabelled_as_a_rejection(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = core_inputs(tmp_path)
    candidate = candidate_for(seal, assets, request, policy, wire)
    decision = next_runtime_v2_reference.inspect_semantic_candidate_v2(candidate, seal, assets)
    assert isinstance(decision, next_runtime_v2_reference.ValidatedSemanticDecisionV2)
    assert decision.gate()["outcome"] == "complete"
    forged = next_runtime_v2_reference.RejectedSemanticDecisionV2._from_rejected_core(
        candidate,
        seal,
        assets,
        {
            "stage": "response_validation",
            "diagnostic_code": "CSV-NEXT-PROTOCOL-001",
            "reason": "model_digest",
            "model_records": None,
        },
    )
    with pytest.raises(ValueError, match="requires an actually invalid"):
        next_runtime_v2_validation.validate_rejected_semantic_decision_v2(forged)
