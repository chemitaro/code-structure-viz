"""Closed v2 response-byte contracts; no actual Node or OS execution."""

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from jsonschema import ValidationError  # type: ignore[import-untyped]

from tests.contracts import next_runtime_v2_reference, next_runtime_v2_validation

ROOT = Path(__file__).resolve().parents[2]


def policy_fixture() -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads(
            (ROOT / "tests/fixtures/next_runtime_v2/launch-policy.json").read_text(encoding="utf-8")
        ),
    )


def failure_frame() -> bytes:
    return (
        b'{"schema":"code-structure-viz.next-adapter-response/v2",'
        b'"control":{"protocol":"code-structure-viz.next-adapter/v2",'
        b'"adapter_version":"0.1.0","binding":{"state":"bound",'
        b'"request_id":"1111111111111111111111111111111111111111111111111111111111111111"},'
        b'"runtime":{"engine":"node","version_raw":"20.19.5","version":"20.19.5",'
        b'"eligibility":"unsupported","observation_source":"process.versions.node"},'
        b'"result_kind":"unsupported_runtime"},"semantic_payload":null}\n'
    )


def test_one_closed_failure_frame_has_real_byte_identity_without_semantic_payload() -> None:
    raw = failure_frame()
    retained = next_runtime_v2_reference.retain_response_frame_v2(
        raw, limits=policy_fixture()["limits"]
    )
    assert retained.raw_bytes == raw
    assert retained.sha256 == "f0bbb753ad4ae8fa9304279c4075b2388e1b01a11d92d1ae457e23f76551b6ce"
    assert retained.control()["runtime"]["version"] == "20.19.5"
    assert retained.semantic_payload() is None


def test_response_frame_rejects_duplicate_keys_before_returning_a_retained_owner() -> None:
    raw = failure_frame().replace(
        b'"semantic_payload":null', b'"semantic_payload":{},"semantic_payload":null'
    )
    with pytest.raises(ValueError, match="duplicate_object_key"):
        next_runtime_v2_reference.retain_response_frame_v2(raw, limits=policy_fixture()["limits"])


def test_response_frame_rejects_mutable_input_instead_of_retaining_a_live_alias() -> None:
    with pytest.raises(TypeError, match="immutable bytes"):
        next_runtime_v2_reference.retain_response_frame_v2(
            cast(Any, bytearray(failure_frame())),
            limits=policy_fixture()["limits"],
        )


@pytest.mark.parametrize(
    "transform",
    [
        lambda raw: b"\xef\xbb\xbf" + raw,
        lambda raw: b"banner\n" + raw,
        lambda raw: raw + raw,
        lambda raw: raw[:-2],
    ],
)
def test_response_frame_rejects_bom_banner_multiple_json_or_partial_frame(transform: Any) -> None:
    with pytest.raises(ValueError, match="invalid_json"):
        next_runtime_v2_reference.retain_response_frame_v2(
            transform(failure_frame()), limits=policy_fixture()["limits"]
        )


def test_success_control_requires_a_semantic_payload_in_the_same_closed_frame() -> None:
    wire = json.loads(failure_frame())
    wire["control"]["result_kind"] = "success"
    wire["control"]["runtime"].update(
        {"version_raw": "22.10.0", "version": "22.10.0", "eligibility": "supported"}
    )
    with pytest.raises(ValidationError):
        next_runtime_v2_reference.retain_response_frame_v2(
            json.dumps(wire).encode(), limits=policy_fixture()["limits"]
        )


@pytest.mark.parametrize(
    "field",
    [
        "compatibility_descriptor",
        "runtime_binding",
        "semantic_compatibility_id",
        "target_completeness",
    ],
)
def test_child_frame_cannot_author_parent_runtime_or_presemantic_target_fields(field: str) -> None:
    wire = json.loads(failure_frame())
    wire[field] = {}
    with pytest.raises(ValidationError):
        next_runtime_v2_reference.retain_response_frame_v2(
            json.dumps(wire).encode(), limits=policy_fixture()["limits"]
        )


def test_retained_control_has_no_mutable_alias_back_to_the_response_authority() -> None:
    retained = next_runtime_v2_reference.retain_response_frame_v2(
        failure_frame(), limits=policy_fixture()["limits"]
    )
    control = retained.control()
    control["runtime"]["version"] = "99.0.0"
    assert retained.control()["runtime"]["version"] == "20.19.5"
    assert "20.19.5" not in repr(retained)
    with pytest.raises(TypeError, match="created by"):
        next_runtime_v2_reference.RetainedResponseFrameV2(
            raw_bytes=failure_frame(), sha256="0" * 64
        )


def test_response_raw_byte_cap_accepts_exact_and_rejects_plus_one_even_whitespace() -> None:
    limits = policy_fixture()["limits"]
    base = failure_frame()
    exact = base + b" " * (limits["max_adapter_response_bytes"] - len(base))
    retained = next_runtime_v2_reference.retain_response_frame_v2(exact, limits=limits)
    assert len(retained.raw_bytes) == 16777216
    with pytest.raises(ValueError, match="max_adapter_response_bytes"):
        next_runtime_v2_reference.retain_response_frame_v2(exact + b" ", limits=limits)


def test_observation_response_identity_is_joined_to_retained_raw_frame_bytes() -> None:
    policy = policy_fixture()
    retained = next_runtime_v2_reference.retain_response_frame_v2(
        failure_frame(), limits=policy["limits"]
    )
    observed = json.loads(
        (ROOT / "tests/fixtures/next_runtime_v2/launch-observation.json").read_text(
            encoding="utf-8"
        )
    )
    observed["exit_code"] = 66
    observed["response"] = {"sha256": retained.sha256, "control": retained.control()}
    observed["capture"]["stdout_bytes"] = len(retained.raw_bytes)
    observed["capture"]["stdout_retained_bytes"] = len(retained.raw_bytes)
    observed["transport_payload_admissible"] = False
    next_runtime_v2_validation.validate_response_frame_observation_v2(observed, policy, retained)

    observed["response"]["sha256"] = "7" * 64
    with pytest.raises(ValueError, match="retained response bytes"):
        next_runtime_v2_validation.validate_response_frame_observation_v2(
            observed, policy, retained
        )


@pytest.mark.parametrize("field", ["control", "stdout_bytes"])
def test_real_response_digest_does_not_authorize_forged_control_or_capture_count(
    field: str,
) -> None:
    policy = policy_fixture()
    retained = next_runtime_v2_reference.retain_response_frame_v2(
        failure_frame(), limits=policy["limits"]
    )
    observed = json.loads(
        (ROOT / "tests/fixtures/next_runtime_v2/launch-observation.json").read_text(
            encoding="utf-8"
        )
    )
    observed["exit_code"] = 66
    observed["response"] = {"sha256": retained.sha256, "control": retained.control()}
    observed["capture"]["stdout_bytes"] = len(retained.raw_bytes)
    observed["capture"]["stdout_retained_bytes"] = len(retained.raw_bytes)
    observed["transport_payload_admissible"] = False
    if field == "control":
        observed["response"]["control"]["runtime"].update(
            {"version_raw": "20.19.4", "version": "20.19.4"}
        )
    else:
        observed["capture"]["stdout_bytes"] += 1
        observed["capture"]["stdout_retained_bytes"] += 1
    with pytest.raises(ValueError, match="retained response bytes"):
        next_runtime_v2_validation.validate_response_frame_observation_v2(
            observed, policy, retained
        )


def test_response_join_rejects_caller_metadata_masquerading_as_a_retained_frame() -> None:
    policy = policy_fixture()
    retained = next_runtime_v2_reference.retain_response_frame_v2(
        failure_frame(), limits=policy["limits"]
    )
    observed = json.loads(
        (ROOT / "tests/fixtures/next_runtime_v2/launch-observation.json").read_text(
            encoding="utf-8"
        )
    )
    observed["exit_code"] = 66
    observed["response"] = {"sha256": retained.sha256, "control": retained.control()}
    observed["capture"].update(
        {"stdout_bytes": len(retained.raw_bytes), "stdout_retained_bytes": len(retained.raw_bytes)}
    )
    observed["transport_payload_admissible"] = False
    fake = SimpleNamespace(
        raw_bytes=retained.raw_bytes, sha256=retained.sha256, control=retained.control
    )
    with pytest.raises(TypeError, match="retained frame owner"):
        next_runtime_v2_validation.validate_response_frame_observation_v2(
            observed, policy, cast(Any, fake)
        )


def test_success_candidate_shape_resolves_unchanged_model_proof_and_identity_defs() -> None:
    # Deliberately not a Core-certified model: no request/source proof join and
    # the candidate model_digest is only syntactically valid. The frame owner
    # must not be confused with semantic or target-completeness acceptance.
    model = {
        "schema": "code-structure-viz.next-model/v1",
        **{
            name: []
            for name in (
                "projects",
                "files",
                "modules",
                "components",
                "members",
                "relations",
                "facts",
            )
        },
        "diagnostics": [],
        "coverage": {
            "counts": {
                name: 0
                for name in (
                    "projects",
                    "files",
                    "modules",
                    "components",
                    "members",
                    "relations",
                    "facts",
                    "internal_entities",
                    "discovered",
                    "published",
                    "excluded",
                    "failed",
                )
            },
            "failed_files": [],
            "affected_ids": [],
            "taint_frontier": [],
            "opaque_reason_counts": {},
            "unknown_relation_count": 0,
            "correlation_losses": [],
            "non_component_value_export_count": 0,
            "type_only_export_count": 0,
            "target_completeness": [],
        },
    }
    payload = {
        "typescript_identity": "typescript-5.9.2",
        "trusted_type_environment_digest": "5" * 64,
        "identity_versions": {
            name: 1
            for name in (
                "project",
                "file",
                "module",
                "component",
                "member",
                "relation",
                "fact",
                "props_ir",
            )
        },
        "limits": policy_fixture()["limits"],
        "run_context": {
            "requested_formats": ["semantic-json"],
            "budget_requested": None,
            "budget_resolved": 500,
            "budget_source": "builtin",
            "stdout_selector": None,
        },
        "model": model,
        "proof": {
            name: []
            for name in (
                "discovered_records",
                "failure_roots",
                "causal_edges",
                "target_resolutions",
                "export_observations",
                "export_resolution_witness",
                "export_reexport_witness",
                "excluded",
                "failed",
            )
        },
        "model_digest": "0" * 64,
    }
    wire = json.loads(failure_frame())
    wire["control"]["result_kind"] = "success"
    wire["control"]["runtime"].update(
        {"version_raw": "22.10.0", "version": "22.10.0", "eligibility": "supported"}
    )
    wire["semantic_payload"] = payload
    retained = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(wire).encode(), limits=policy_fixture()["limits"]
    )
    assert retained.semantic_payload() == payload

    wire["control"]["result_kind"] = "semantic_failure"
    with pytest.raises(ValidationError):
        next_runtime_v2_reference.retain_response_frame_v2(
            json.dumps(wire).encode(), limits=policy_fixture()["limits"]
        )
