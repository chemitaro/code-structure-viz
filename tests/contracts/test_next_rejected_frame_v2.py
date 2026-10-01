"""Rejected bytes have a closed owner without retaining body or inventing control."""

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.contracts import next_runtime_v2_reference, next_runtime_v2_validation
from tests.contracts.test_next_exchange_v2 import request_inputs, shape_wire
from tests.contracts.test_next_process_observation_v2 import complete_evidence


def test_malformed_json_is_a_typed_rejection_without_retained_raw_body(tmp_path: Path) -> None:
    _seal, _assets, request, _policy = request_inputs(tmp_path)
    raw = b'{"control":'
    result = next_runtime_v2_reference.inspect_response_frame_v2(
        raw, limits=request.record()["limits"]
    )
    assert type(result) is next_runtime_v2_reference.RejectedResponseFrameV2
    failure = result.failure()
    assert (failure["stage"], failure["diagnostic_code"], failure["reason"]) == (
        "response_decode",
        "CSV-NEXT-PROTOCOL-001",
        "invalid_json",
    )
    assert failure["raw_sha256"] == hashlib.sha256(raw).hexdigest()
    assert failure["byte_length"] == 11
    assert not hasattr(result, "raw_bytes")
    assert "control" not in repr(result)


def test_closed_shape_violation_is_a_typed_rejection_not_a_control_observation(
    tmp_path: Path,
) -> None:
    _seal, _assets, request, _policy = request_inputs(tmp_path)
    result = next_runtime_v2_reference.inspect_response_frame_v2(
        b'{"schema":"unknown"}', limits=request.record()["limits"]
    )
    assert type(result) is next_runtime_v2_reference.RejectedResponseFrameV2
    assert (
        result.failure()["stage"],
        result.failure()["diagnostic_code"],
        result.failure()["reason"],
    ) == ("response_schema", "CSV-NEXT-PROTOCOL-001", "closed_response_shape")
    assert not hasattr(result, "control")


def test_raw_response_cap_plus_one_is_measured_before_json_materialization(tmp_path: Path) -> None:
    _seal, _assets, request, _policy = request_inputs(tmp_path)
    result = next_runtime_v2_reference.inspect_response_frame_v2(
        b" " * 16_777_217, limits=request.record()["limits"]
    )
    assert type(result) is next_runtime_v2_reference.RejectedResponseFrameV2
    failure = result.failure()
    assert (failure["stage"], failure["diagnostic_code"], failure["reason"]) == (
        "response_raw_bytes",
        "CSV-NEXT-LIMIT-003",
        "max_adapter_response_bytes",
    )
    assert failure["byte_length"] == 16_777_217
    assert failure["measurement"]["materialized"] is False
    assert failure["measurement"]["max_nesting"] == 0


def test_structural_depth_breach_is_a_measured_limit_not_a_malformed_protocol(
    tmp_path: Path,
) -> None:
    _seal, _assets, request, _policy = request_inputs(tmp_path)
    raw = b'{"deep":' + b"[" * 64 + b"0" + b"]" * 64 + b"}"
    result = next_runtime_v2_reference.inspect_response_frame_v2(
        raw, limits=request.record()["limits"]
    )
    assert type(result) is next_runtime_v2_reference.RejectedResponseFrameV2
    failure = result.failure()
    assert (failure["stage"], failure["diagnostic_code"], failure["reason"]) == (
        "response_decode",
        "CSV-NEXT-LIMIT-003",
        "max_json_nesting",
    )
    assert failure["measurement"]["max_nesting"] == 65
    assert failure["measurement"]["materialized"] is False


@pytest.mark.parametrize(
    ("raw", "stage", "code"),
    [
        (b'{"control":', "response_decode", "CSV-NEXT-PROTOCOL-001"),
        (b'{"schema":"unknown"}', "response_schema", "CSV-NEXT-PROTOCOL-001"),
        (
            b'{"deep":' + b"[" * 64 + b"0" + b"]" * 64 + b"}",
            "response_decode",
            "CSV-NEXT-LIMIT-003",
        ),
    ],
    ids=["json", "schema", "structure"],
)
def test_rejected_bytes_join_to_actual_capture_without_inventing_a_control_prefix(
    tmp_path: Path,
    raw: bytes,
    stage: str,
    code: str,
) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    rejected = next_runtime_v2_reference.inspect_response_frame_v2(
        raw, limits=request.record()["limits"]
    )
    assert isinstance(rejected, next_runtime_v2_reference.RejectedResponseFrameV2)
    evidence = complete_evidence(policy)
    evidence.update(response=None, terminal_cause="frame_invalid")
    evidence["capture"].update(
        stdin_bytes=len(request.canonical_bytes),
        stdin_sent_bytes=len(request.canonical_bytes),
        stdout_bytes=len(raw),
        stdout_retained_bytes=0,
    )
    observation = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    runtime = next_runtime_v2_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, rejected
    )
    assert runtime.frame_rejection() == rejected.failure()
    assert runtime.control() is None and runtime.response_descriptor() is None
    assert runtime.transport_candidate() is None
    value = next_runtime_v2_reference.runtime_provenance_v2(runtime)
    assert (value["stage"], value["failure_code"]) == (stage, code)
    assert value["observed"]["request"]["state"] == "observed"
    assert value["observed"]["process_start"]["state"] == "observed"
    for slot in (
        "node_version",
        "control_response",
        "semantic_payload",
        "compatibility",
        "model",
        "budget",
    ):
        assert value["observed"][slot] == {"state": "unobserved", "value": None}
    next_runtime_v2_validation.validate_runtime_provenance_v2(value, runtime)


@pytest.mark.parametrize(
    "raw",
    [b"\xef\xbb\xbf{}", b"banner\n{}", b'{"x":1,"x":2}', b"{} {}", b'{"x":"\xff"}', b'{"x":NaN}'],
    ids=["bom", "banner", "duplicate", "two-json", "utf8", "nonfinite"],
)
def test_rejected_grammar_never_becomes_a_validated_control(tmp_path: Path, raw: bytes) -> None:
    _seal, _assets, request, _policy = request_inputs(tmp_path)
    rejected = next_runtime_v2_reference.inspect_response_frame_v2(
        raw, limits=request.record()["limits"]
    )
    assert isinstance(rejected, next_runtime_v2_reference.RejectedResponseFrameV2)
    assert (rejected.failure()["stage"], rejected.failure()["diagnostic_code"]) == (
        "response_decode",
        "CSV-NEXT-PROTOCOL-001",
    )
    assert rejected.failure()["measurement"]["materialized"] is False
    assert not hasattr(rejected, "control")


@pytest.mark.parametrize(
    ("raw", "reason", "total", "peak"),
    [
        (b'{"many":[' + b"0," * 100_000 + b"0]}", "max_array_items", 100_000, 100_001),
        (
            b'{"left":[' + b"0," * 49_999 + b'0],"right":[' + b"0," * 50_000 + b"0]}",
            "max_total_array_items",
            100_001,
            50_001,
        ),
    ],
    ids=["per-array", "aggregate"],
)
def test_array_breach_keeps_actual_measurement_without_retaining_array_values(
    tmp_path: Path, raw: bytes, reason: str, total: int, peak: int
) -> None:
    _seal, _assets, request, _policy = request_inputs(tmp_path)
    rejected = next_runtime_v2_reference.inspect_response_frame_v2(
        raw, limits=request.record()["limits"]
    )
    assert isinstance(rejected, next_runtime_v2_reference.RejectedResponseFrameV2)
    failure = rejected.failure()
    assert (failure["stage"], failure["diagnostic_code"], failure["reason"]) == (
        "response_decode",
        "CSV-NEXT-LIMIT-003",
        reason,
    )
    assert failure["measurement"]["total_array_items"] == total
    assert failure["measurement"]["max_array_items"] == peak
    assert "value" not in failure["measurement"]


def test_string_byte_breach_is_a_structural_limit_before_materialization(tmp_path: Path) -> None:
    _seal, _assets, request, _policy = request_inputs(tmp_path)
    raw = b'{"data":"' + b"a" * 8_388_609 + b'"}'
    rejected = next_runtime_v2_reference.inspect_response_frame_v2(
        raw, limits=request.record()["limits"]
    )
    assert isinstance(rejected, next_runtime_v2_reference.RejectedResponseFrameV2)
    failure = rejected.failure()
    assert (failure["stage"], failure["diagnostic_code"], failure["reason"]) == (
        "response_decode",
        "CSV-NEXT-LIMIT-003",
        "max_json_string_bytes",
    )
    assert failure["measurement"]["max_string_bytes"] == 8_388_609
    assert failure["measurement"]["materialized"] is False


@pytest.mark.parametrize("mutation", ["byte_count", "missing_eof", "blind_control"])
def test_rejected_owner_cannot_be_rebound_to_different_or_incomplete_capture(
    tmp_path: Path, mutation: str
) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    rejected = next_runtime_v2_reference.inspect_response_frame_v2(
        b'{"control":', limits=request.record()["limits"]
    )
    evidence = complete_evidence(policy)
    evidence.update(response=None, terminal_cause="frame_invalid")
    evidence["capture"].update(
        stdin_bytes=len(request.canonical_bytes),
        stdin_sent_bytes=len(request.canonical_bytes),
        stdout_bytes=11,
        stdout_retained_bytes=0,
    )
    if mutation == "byte_count":
        evidence["capture"]["stdout_bytes"] = 12
    elif mutation == "missing_eof":
        evidence["capture"]["stdout_eof"] = False
    else:
        evidence["response"] = complete_evidence(policy)["response"]
    observation = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    with pytest.raises(ValueError, match="rejected frame is not joined"):
        next_runtime_v2_reference.retain_runtime_result_v2(
            seal, assets, request, policy, observation, rejected
        )


def test_rejection_limits_are_frozen_and_must_match_the_request_owner(tmp_path: Path) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    limits = request.record()["limits"]
    limits["max_entities"] = 501
    rejected = next_runtime_v2_reference.inspect_response_frame_v2(b'{"control":', limits=limits)
    assert isinstance(rejected, next_runtime_v2_reference.RejectedResponseFrameV2)
    limits["max_entities"] = 500
    rejected.limits()["max_entities"] = 500
    rejected.failure()["diagnostic_code"] = "CSV-NEXT-NODE-004"
    assert rejected.limits()["max_entities"] == 501
    assert rejected.failure()["diagnostic_code"] == "CSV-NEXT-PROTOCOL-001"
    evidence = complete_evidence(policy)
    evidence.update(response=None, terminal_cause="frame_invalid")
    evidence["capture"].update(
        stdin_bytes=len(request.canonical_bytes),
        stdin_sent_bytes=len(request.canonical_bytes),
        stdout_bytes=11,
        stdout_retained_bytes=0,
    )
    observation = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    with pytest.raises(ValueError, match="rejected frame limits differ"):
        next_runtime_v2_reference.retain_runtime_result_v2(
            seal, assets, request, policy, observation, rejected
        )


def test_inspection_retains_valid_frame_but_no_free_rejection_owner(tmp_path: Path) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    valid = next_runtime_v2_reference.inspect_response_frame_v2(
        json.dumps(shape_wire(request)).encode(), limits=request.record()["limits"]
    )
    assert type(valid) is next_runtime_v2_reference.RetainedResponseFrameV2
    with pytest.raises(TypeError, match="created by"):
        next_runtime_v2_reference.RejectedResponseFrameV2()
    with pytest.raises(TypeError, match="immutable bytes"):
        next_runtime_v2_reference.inspect_response_frame_v2(
            bytearray(b"{}"),  # type: ignore[arg-type]
            limits=request.record()["limits"],
        )
    evidence = complete_evidence(policy)
    evidence.update(response=None, terminal_cause="frame_invalid")
    evidence["capture"].update(
        stdin_bytes=len(request.canonical_bytes),
        stdin_sent_bytes=len(request.canonical_bytes),
        stdout_bytes=11,
        stdout_retained_bytes=0,
    )
    observation = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    for fake in (None, SimpleNamespace(failure=lambda: {"stage": "response_decode"})):
        with pytest.raises(TypeError, match=r"(rejected byte owner|retained frame owner)"):
            next_runtime_v2_reference.retain_runtime_result_v2(
                seal,
                assets,
                request,
                policy,
                observation,
                fake,  # type: ignore[arg-type]
            )
