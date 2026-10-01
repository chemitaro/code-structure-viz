"""Live byte validation and descriptor-only failure receipts are distinct gates."""

import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from tests.contracts import next_runtime_v2_reference, next_runtime_v2_validation
from tests.contracts.next_reference_validation import canonical_json_bytes
from tests.contracts.test_next_exchange_v2 import exchange_evidence, request_inputs, shape_wire
from tests.contracts.test_next_process_observation_v2 import complete_evidence

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_FAILURE = ROOT / "tests/fixtures/next_runtime_v2/observed-response-protocol-failure.json"


def protocol_runtime(
    tmp_path: Path, *, canonical: bool = False
) -> tuple[
    next_runtime_v2_reference.RetainedRuntimeResultV2,
    next_runtime_v2_reference.RetainedResponseFrameV2,
]:
    seal, assets, request, policy = request_inputs(tmp_path)
    raw = PROTOCOL_FAILURE.read_bytes()
    if canonical:
        raw = raw.removesuffix(b"\n")
    frame = next_runtime_v2_reference.retain_response_frame_v2(
        raw, limits=request.record()["limits"]
    )
    evidence = exchange_evidence(policy, request, frame)
    evidence["exit_code"] = 65
    observation = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    return next_runtime_v2_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, frame
    ), frame


def test_complete_failure_retains_a_joined_descriptor_receipt_without_semantic_authority(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    raw = PROTOCOL_FAILURE.read_bytes()
    frame = next_runtime_v2_reference.retain_response_frame_v2(
        raw, limits=request.record()["limits"]
    )
    evidence = exchange_evidence(policy, request, frame)
    evidence["exit_code"] = 65
    observation = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    result = next_runtime_v2_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, frame
    )

    receipt = result.observed_response_receipt()
    assert receipt is not None
    assert receipt.request_frame() is request
    assert receipt.control() == frame.control()
    assert receipt.descriptor() == {
        "raw_sha256": "39f69e2d4585d53c3ff3ac4db463beba675bf4fa908b6f984f08927631150a25",
        "byte_length": 263,
        "canonical_json": False,
    }
    assert result.response_descriptor() == receipt.descriptor()
    assert result.transport_candidate() is None
    next_runtime_v2_validation.validate_observed_response_receipt_v2(receipt, result)
    next_runtime_v2_validation.validate_runtime_result_v2(result)


def test_failure_result_validation_rejects_a_retained_semantic_candidate(tmp_path: Path) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    failure_frame = next_runtime_v2_reference.retain_response_frame_v2(
        PROTOCOL_FAILURE.read_bytes(), limits=request.record()["limits"]
    )
    evidence = exchange_evidence(policy, request, failure_frame)
    evidence["exit_code"] = 65
    observation = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    result = next_runtime_v2_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, failure_frame
    )
    success_frame = next_runtime_v2_reference.retain_response_frame_v2(
        canonical_json_bytes(shape_wire(request)), limits=request.record()["limits"]
    )
    success_observation = next_runtime_v2_reference.reference_process_observation_v2(
        policy, exchange_evidence(policy, request, success_frame)
    )
    success_result = next_runtime_v2_reference.retain_runtime_result_v2(
        seal, assets, request, policy, success_observation, success_frame
    )
    # Deliberately malformed validator input, not an API or hostile same-UID promise.
    object.__setattr__(result, "_candidate", success_result.transport_candidate())

    with pytest.raises(ValueError, match=r"failure.*candidate"):
        next_runtime_v2_validation.validate_runtime_result_v2(result)


def test_success_validation_rechecks_the_retained_frame_not_only_metadata(tmp_path: Path) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    frame = next_runtime_v2_reference.retain_response_frame_v2(
        canonical_json_bytes(shape_wire(request)), limits=request.record()["limits"]
    )
    observation = next_runtime_v2_reference.reference_process_observation_v2(
        policy, exchange_evidence(policy, request, frame)
    )
    result = next_runtime_v2_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, frame
    )
    object.__setattr__(
        frame, "raw_bytes", json.dumps(json.loads(frame.raw_bytes), indent=2).encode()
    )

    with pytest.raises(ValueError, match=r"retained response bytes|live bytes"):
        next_runtime_v2_validation.validate_runtime_result_v2(result)


def test_receipt_has_closed_constructor_frozen_fields_and_fresh_projections(tmp_path: Path) -> None:
    result, _frame = protocol_runtime(tmp_path)
    receipt = result.observed_response_receipt()
    assert receipt is not None
    with pytest.raises(TypeError, match="created by"):
        next_runtime_v2_reference.RetainedObservedResponseReceiptV2()
    with pytest.raises(FrozenInstanceError):
        cast(Any, receipt)._descriptor_bytes = b"{}"
    assert repr(receipt) == "RetainedObservedResponseReceiptV2()"
    descriptor = receipt.descriptor()
    descriptor["canonical_json"] = True
    control = receipt.control()
    control["runtime"] = {"version": "99.0.0"}
    assert receipt.descriptor()["canonical_json"] is False
    assert receipt.control()["runtime"] is None
    next_runtime_v2_validation.validate_runtime_result_v2(result)


def test_equal_content_receipt_from_another_runtime_snapshot_is_not_the_same_owner(
    tmp_path: Path,
) -> None:
    result, frame = protocol_runtime(tmp_path)
    other = next_runtime_v2_reference.retain_runtime_result_v2(
        result.source_seal(),
        result.execution_assets(),
        result.request_frame(),
        result.policy(),
        result.observation(),
        frame,
    )
    first, second = result.observed_response_receipt(), other.observed_response_receipt()
    assert first is not None and second is not None
    assert first.descriptor() == second.descriptor()
    assert first.request_frame() is second.request_frame()
    next_runtime_v2_validation.validate_observed_response_receipt_v2(second, other)
    with pytest.raises(ValueError, match="same-runtime"):
        next_runtime_v2_validation.validate_observed_response_receipt_v2(first, other)
    # Even injecting the foreign receipt cannot erase the exact snapshot boundary.
    object.__setattr__(other, "_response_receipt", first)
    with pytest.raises(ValueError, match="same-runtime"):
        next_runtime_v2_validation.validate_runtime_result_v2(other)


def test_provenance_rejects_a_receipt_from_a_different_runtime_snapshot(tmp_path: Path) -> None:
    result, frame = protocol_runtime(tmp_path)
    other = next_runtime_v2_reference.retain_runtime_result_v2(
        result.source_seal(),
        result.execution_assets(),
        result.request_frame(),
        result.policy(),
        result.observation(),
        frame,
    )
    object.__setattr__(result, "_response_receipt", other.observed_response_receipt())
    with pytest.raises(ValueError, match="same-runtime"):
        next_runtime_v2_reference.runtime_provenance_v2(result)


def test_runtime_validation_requires_the_decoder_rejection_owner_for_invalid_frames(
    tmp_path: Path,
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
    observation = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    result = next_runtime_v2_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, rejected
    )
    assert result.observed_response_receipt() is None
    assert result.response_descriptor() is None
    next_runtime_v2_validation.validate_runtime_result_v2(result)
    object.__setattr__(result, "_rejected_frame", None)
    with pytest.raises(TypeError, match="rejected byte owner"):
        next_runtime_v2_validation.validate_runtime_result_v2(result)


@pytest.mark.parametrize("cause", ["binding_mismatch", "response_invalid"])
def test_live_receipt_requires_actual_violation_not_only_a_mismatch_label(
    tmp_path: Path, cause: str
) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    frame = next_runtime_v2_reference.retain_response_frame_v2(
        canonical_json_bytes(shape_wire(request)), limits=request.record()["limits"]
    )
    evidence = exchange_evidence(policy, request, frame)
    observation = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    result = next_runtime_v2_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, frame
    )
    receipt = result.observed_response_receipt()
    assert receipt is not None
    evidence["terminal_cause"] = cause
    evidence["capture"]["stdout_retained_bytes"] = 0
    bad_observation = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    snapshot = canonical_json_bytes(bad_observation)
    object.__setattr__(receipt, "_observation_bytes", snapshot)
    with pytest.raises(ValueError, match=r"mismatch.*actual"):
        next_runtime_v2_validation.validate_observed_response_receipt_before_disposal_v2(
            receipt,
            frame,
            request=request,
            observation_snapshot=snapshot,
            policy=policy,
            seal=seal,
            assets=assets,
        )


@pytest.mark.parametrize("target", ["receipt", "result"])
def test_receipt_validation_rejects_duck_owners(tmp_path: Path, target: str) -> None:
    result, _frame = protocol_runtime(tmp_path)
    receipt = result.observed_response_receipt()
    assert receipt is not None
    with pytest.raises(TypeError, match="owner"):
        next_runtime_v2_validation.validate_observed_response_receipt_v2(
            cast(Any, SimpleNamespace()) if target == "receipt" else receipt,
            cast(Any, SimpleNamespace()) if target == "result" else result,
        )


@pytest.mark.parametrize(
    ("key", "replacement"),
    [
        ("raw_sha256", "0" * 64),
        ("byte_length", 262),
        ("canonical_json", True),
        ("semantic_payload", {}),
        ("byte_length", True),
    ],
)
def test_live_validator_rejects_wrong_producer_descriptor_against_actual_bytes(
    tmp_path: Path, key: str, replacement: Any
) -> None:
    result, frame = protocol_runtime(tmp_path)
    receipt = result.observed_response_receipt()
    assert receipt is not None
    bad = receipt.descriptor()
    bad[key] = replacement
    object.__setattr__(receipt, "_descriptor_bytes", canonical_json_bytes(bad))
    with pytest.raises(ValueError, match="live bytes"):
        next_runtime_v2_validation.validate_observed_response_receipt_before_disposal_v2(
            receipt,
            frame,
            request=result.request_frame(),
            observation_snapshot=result._observation_bytes,
            policy=result.policy(),
            seal=result.source_seal(),
            assets=result.execution_assets(),
        )


def test_live_receipt_recomputes_raw_sha_instead_of_trusting_frame_and_capture_metadata(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    frame = next_runtime_v2_reference.retain_response_frame_v2(
        PROTOCOL_FAILURE.read_bytes(), limits=request.record()["limits"]
    )
    object.__setattr__(frame, "sha256", "0" * 64)
    evidence = exchange_evidence(policy, request, frame)
    evidence["exit_code"] = 65
    observation = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    with pytest.raises(ValueError, match="live bytes"):
        next_runtime_v2_reference.retain_runtime_result_v2(
            seal, assets, request, policy, observation, frame
        )


def test_failure_validation_does_not_read_the_disposed_frame_again(tmp_path: Path) -> None:
    result, frame = protocol_runtime(tmp_path)
    descriptor = result.response_descriptor()
    # The caller's input still exists; zeroization of that separate object is not promised.
    object.__setattr__(frame, "raw_bytes", b"invalid discarded body")
    object.__setattr__(frame, "sha256", "0" * 64)
    next_runtime_v2_validation.validate_runtime_result_v2(result)
    assert result.response_descriptor() == descriptor
    assert (
        next_runtime_v2_reference.runtime_provenance_v2(result)["observed"]["control_response"][
            "state"
        ]
        == "observed"
    )


@pytest.mark.parametrize(
    "cause",
    [
        "cleanup_unverified",
        "candidate_drift",
        "assets_drift",
        "binding_mismatch",
        "exit_mismatch",
        "response_invalid",
    ],
)
def test_failure_result_graph_retains_no_frame_payload_or_candidate(
    tmp_path: Path, cause: str
) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    wire = shape_wire(request)
    if cause == "binding_mismatch":
        wire["control"]["binding"]["request_id"] = "0" * 64
    if cause == "response_invalid":
        wire["semantic_payload"]["trusted_type_environment_digest"] = "0" * 64
    frame = next_runtime_v2_reference.retain_response_frame_v2(
        canonical_json_bytes(wire), limits=request.record()["limits"]
    )
    evidence = exchange_evidence(policy, request, frame)
    evidence["terminal_cause"] = cause
    evidence["capture"]["stdout_retained_bytes"] = 0
    if cause == "cleanup_unverified":
        evidence["cleanup"]["private_root_removed"] = False
    elif cause.endswith("_drift"):
        evidence[cause.removesuffix("_drift") + "_check"] = "drift"
    elif cause == "exit_mismatch":
        evidence["exit_code"] = 68
    observation = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    result = next_runtime_v2_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, frame
    )
    assert result.transport_candidate() is None
    receipt = result.observed_response_receipt()
    assert receipt is not None
    assert {item.name for item in fields(receipt)} == {
        "_request",
        "_observation_bytes",
        "_descriptor_bytes",
    }
    # Walk retained data fields only, not Python class/module globals or caller inputs.
    pending: list[Any] = [result]
    seen: set[int] = set()
    while pending:
        value = pending.pop()
        if id(value) in seen:
            continue
        seen.add(id(value))
        assert not isinstance(
            value,
            (
                next_runtime_v2_reference.RetainedResponseFrameV2,
                next_runtime_v2_reference.ValidatedTransportCandidateV2,
                memoryview,
            ),
        )
        if is_dataclass(value) and not isinstance(value, type):
            pending.extend(getattr(value, item.name) for item in fields(value))
        elif isinstance(value, dict):
            pending.extend(value.values())
        elif isinstance(value, (tuple, list)):
            pending.extend(value)
        if isinstance(value, bytes):
            assert value != frame.raw_bytes
    next_runtime_v2_validation.validate_runtime_result_v2(result)


@pytest.mark.parametrize(
    ("canonical", "raw_sha", "length", "control_sha"),
    [
        (
            True,
            "a1b2f3c703021e2c41f095771e4d16bb23fc1b4ce9ebea0edaa32dc8dc251407",
            262,
            "fcb066cbc493a50d2403ac3f179c09167705dbcf390cce752e5f5a1837cf0164",
        ),
        (
            False,
            "39f69e2d4585d53c3ff3ac4db463beba675bf4fa908b6f984f08927631150a25",
            263,
            "6edadd2c0fcf54ca5477efc71e258580b669f26d92e2767fc5032d3af4f601d3",
        ),
    ],
)
def test_independent_ascii_failure_known_vectors_keep_raw_and_observation_hashes_distinct(
    tmp_path: Path, canonical: bool, raw_sha: str, length: int, control_sha: str
) -> None:
    result, _frame = protocol_runtime(tmp_path, canonical=canonical)
    assert result.response_descriptor() == {
        "raw_sha256": raw_sha,
        "byte_length": length,
        "canonical_json": canonical,
    }
    provenance = next_runtime_v2_reference.runtime_provenance_v2(result)
    assert provenance["observed"]["node_version"] == {"state": "unobserved", "value": None}
    assert provenance["observed"]["control_response"]["value"]["sha256"] == control_sha
    next_runtime_v2_validation.validate_runtime_provenance_v2(provenance, result)
