"""Closed runtime results preserve observations without inventing semantic proof."""

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from tests.contracts import next_runtime_v2_reference
from tests.contracts.test_next_exchange_v2 import exchange_evidence, request_inputs, shape_wire
from tests.contracts.test_next_process_observation_v2 import complete_evidence


def test_unsupported_same_process_runtime_is_a_closed_result_without_a_candidate(
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
    raw = json.dumps(wire, sort_keys=True, separators=(",", ":")).encode()
    frame = next_runtime_v2_reference.retain_response_frame_v2(
        raw, limits=request.record()["limits"]
    )
    evidence: dict[str, Any] = exchange_evidence(policy, request, frame)
    evidence["exit_code"] = 66
    observation = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)

    result = next_runtime_v2_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, frame
    )

    assert result.result_kind == "unsupported_runtime"
    assert result.transport_candidate() is None
    assert result.control() == wire["control"]
    assert result.response_descriptor() == {
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "byte_length": len(raw),
        "canonical_json": True,
    }


def test_success_result_retains_the_joined_transport_candidate_not_semantic_success(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    # Valid wire shape, deliberately fabricated model_digest: Core must still reject it.
    frame = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(shape_wire(request), indent=2).encode() + b"\n",
        limits=request.record()["limits"],
    )
    observation = next_runtime_v2_reference.reference_process_observation_v2(
        policy, exchange_evidence(policy, request, frame)
    )
    result = next_runtime_v2_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, frame
    )
    candidate = result.transport_candidate()
    assert candidate is not None
    assert result.result_kind == "success"
    assert candidate.request_frame() is request
    assert candidate.response_frame() is frame
    descriptor = result.response_descriptor()
    assert descriptor is not None and descriptor["canonical_json"] is False


def test_timeout_without_a_complete_frame_cannot_invent_runtime_control(tmp_path: Path) -> None:
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
    assert result.result_kind == "transport_failure"
    assert result.control() is None
    assert result.response_descriptor() is None
    assert result.transport_candidate() is None


def test_complete_foreign_binding_is_preserved_as_failure_not_rebound_to_the_request(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    wire = shape_wire(request)
    wire["control"]["binding"]["request_id"] = "0" * 64
    frame = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(wire).encode(), limits=request.record()["limits"]
    )
    evidence = exchange_evidence(policy, request, frame)
    evidence["terminal_cause"] = "binding_mismatch"
    evidence["capture"]["stdout_retained_bytes"] = 0
    observation = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    result = next_runtime_v2_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, frame
    )
    assert result.result_kind == "transport_failure"
    assert result.control() == wire["control"]
    assert result.transport_candidate() is None


def test_binding_mismatch_label_requires_an_actual_foreign_control_binding(tmp_path: Path) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    frame = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(shape_wire(request)).encode(), limits=request.record()["limits"]
    )
    evidence = exchange_evidence(policy, request, frame)
    evidence["terminal_cause"] = "binding_mismatch"
    evidence["capture"]["stdout_retained_bytes"] = 0
    observation = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    with pytest.raises(ValueError, match=r"binding mismatch.*actual"):
        next_runtime_v2_reference.retain_runtime_result_v2(
            seal, assets, request, policy, observation, frame
        )


@pytest.mark.parametrize(
    ("kind", "exit_code", "bound", "runtime"),
    [
        ("protocol_failure", 65, False, None),
        ("bootstrap_failure", 67, False, None),
        (
            "semantic_failure",
            68,
            True,
            {
                "engine": "node",
                "version_raw": "22.10.0",
                "version": "22.10.0",
                "eligibility": "supported",
                "observation_source": "process.versions.node",
            },
        ),
    ],
)
def test_other_closed_child_failures_never_gain_a_semantic_candidate(
    tmp_path: Path, kind: str, exit_code: int, bound: bool, runtime: dict[str, Any] | None
) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    wire = shape_wire(request)
    wire["control"].update(
        result_kind=kind,
        runtime=runtime,
        binding={"state": "bound", "request_id": request.request_id}
        if bound
        else {"state": "unbound", "request_id": None},
    )
    wire["semantic_payload"] = None
    frame = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(wire).encode(), limits=request.record()["limits"]
    )
    evidence = exchange_evidence(policy, request, frame)
    evidence["exit_code"] = exit_code
    observation = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    result = next_runtime_v2_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, frame
    )
    assert result.result_kind == kind
    assert result.control() == wire["control"]
    assert result.transport_candidate() is None


@pytest.mark.parametrize("cause", ["cleanup_unverified", "candidate_drift", "assets_drift"])
def test_late_transport_failure_keeps_control_but_discards_semantic_authority(
    tmp_path: Path, cause: str
) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    frame = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(shape_wire(request)).encode(), limits=request.record()["limits"]
    )
    evidence = exchange_evidence(policy, request, frame)
    evidence["terminal_cause"] = cause
    evidence["capture"]["stdout_retained_bytes"] = 0
    if cause == "cleanup_unverified":
        evidence["cleanup"]["private_root_removed"] = False
    else:
        evidence[cause.removesuffix("_drift") + "_check"] = "drift"
    observation = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    result = next_runtime_v2_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, frame
    )
    assert result.result_kind == "transport_failure"
    assert result.control() == frame.control()
    assert result.response_descriptor() is not None
    assert result.transport_candidate() is None


@pytest.mark.parametrize("cause", ["stage_failed", "spawn_failed"])
def test_pre_spawn_failure_does_not_claim_a_process_or_frame(tmp_path: Path, cause: str) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    evidence = complete_evidence(policy)
    evidence.update(spawn=None, capture=None, response=None, exit_code=None, terminal_cause=cause)
    evidence["cleanup"]["direct_child_waited"] = False
    observation = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    result = next_runtime_v2_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, None
    )
    assert result.result_kind == "transport_failure"
    assert result.observation()["spawn"] is None
    assert result.control() is None
    assert result.response_descriptor() is None
    assert result.transport_candidate() is None


def test_result_freezes_inputs_and_returns_fresh_observation_projections(tmp_path: Path) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    frame = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(shape_wire(request)).encode(), limits=request.record()["limits"]
    )
    observation = next_runtime_v2_reference.reference_process_observation_v2(
        policy, exchange_evidence(policy, request, frame)
    )
    original = deepcopy(observation)
    result = next_runtime_v2_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, frame
    )
    observation["response"]["control"]["runtime"]["version"] = "99.0.0"
    result.observation()["spawn"]["pid"] = 99999
    assert result.observation() == original
    assert result.control() == frame.control()
    assert "src/page.tsx" not in repr(result)


def test_free_constructor_and_unjoined_control_projection_cannot_mint_a_result(
    tmp_path: Path,
) -> None:
    with pytest.raises(TypeError, match="created by"):
        next_runtime_v2_reference.RetainedRuntimeResultV2()
    seal, assets, request, policy = request_inputs(tmp_path)
    frame = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(shape_wire(request)).encode(), limits=request.record()["limits"]
    )
    observation = next_runtime_v2_reference.reference_process_observation_v2(
        policy, exchange_evidence(policy, request, frame)
    )
    with pytest.raises(TypeError, match="retained frame owner"):
        next_runtime_v2_reference.retain_runtime_result_v2(
            seal,
            assets,
            request,
            policy,
            observation,
            SimpleNamespace(**frame.control()),  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="retained complete frame"):
        next_runtime_v2_reference.retain_runtime_result_v2(
            seal, assets, request, policy, observation, None
        )
    observation["response"]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="retained response bytes"):
        next_runtime_v2_reference.retain_runtime_result_v2(
            seal, assets, request, policy, observation, frame
        )
