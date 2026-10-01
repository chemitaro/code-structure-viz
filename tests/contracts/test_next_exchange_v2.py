"""Cross-owner private wire joins, without a production process certificate."""

import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from jsonschema import ValidationError  # type: ignore[import-untyped]

from code_structure_viz.adapters.next.source_acquisition import SourceAcquisitionSeal
from tests.contracts import next_runtime_v2_reference, next_runtime_v2_validation
from tests.contracts.next_reference_validation import digest
from tests.contracts.next_runtime_v2_fixtures import sealed_source_fixture_v1
from tests.contracts.test_next_process_observation_v2 import complete_evidence, policy_fixture
from tests.contracts.test_next_request_frame_v2 import run_context
from tests.contracts.test_next_trusted_environment_v2 import profile_members

ROOT = Path(__file__).resolve().parents[2]


def request_inputs(
    tmp_path: Path,
) -> tuple[
    SourceAcquisitionSeal,
    next_runtime_v2_reference.RetainedExecutionAssets,
    next_runtime_v2_reference.RetainedRequestFrameV2,
    dict[str, Any],
]:
    assets = next_runtime_v2_reference.retain_execution_assets_v1(profile_members())
    trusted = next_runtime_v2_reference.trusted_environment_manifest_v2(assets)[
        "environment_descriptor"
    ]
    seal = sealed_source_fixture_v1(tmp_path, trusted_digest=trusted["sha256"])
    request = next_runtime_v2_reference.build_request_frame_v2(
        seal, assets, targets=["path:src/page.tsx"], run_context=run_context()
    )
    policy = policy_fixture()
    policy.update(
        request_id=request.request_id,
        adapter=assets.adapter_identity(),
        execution_asset_set_id=assets.descriptor()["asset_set_id"],
        trusted_environment_digest=trusted["sha256"],
        limits=request.record()["limits"],
    )
    return seal, assets, request, policy


def shape_wire(request: next_runtime_v2_reference.RetainedRequestFrameV2) -> dict[str, Any]:
    """Synthetic echo-only candidate; intentionally not a valid Core model/proof."""

    wire = request.record()
    collections = ("projects", "files", "modules", "components", "members", "relations", "facts")
    model = {
        "schema": "code-structure-viz.next-model/v1",
        **{name: [] for name in collections},
        "diagnostics": [],
        "coverage": {
            "counts": {
                name: 0
                for name in (
                    *collections,
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
    return {
        "schema": "code-structure-viz.next-adapter-response/v2",
        "control": {
            "protocol": "code-structure-viz.next-adapter/v2",
            "adapter_version": wire["adapter_version"],
            "binding": {"state": "bound", "request_id": request.request_id},
            "runtime": {
                "engine": "node",
                "version_raw": "22.10.0",
                "version": "22.10.0",
                "eligibility": "supported",
                "observation_source": "process.versions.node",
            },
            "result_kind": "success",
        },
        "semantic_payload": {
            "typescript_identity": "typescript-5.9.2",
            "trusted_type_environment_digest": wire["trusted_type_environment"]["sha256"],
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
            "limits": wire["limits"],
            "run_context": wire["run_context"],
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
        },
    }


def exchange_evidence(
    policy: dict[str, Any],
    request: next_runtime_v2_reference.RetainedRequestFrameV2,
    response: next_runtime_v2_reference.RetainedResponseFrameV2,
) -> dict[str, Any]:
    evidence = complete_evidence(policy)
    evidence["capture"].update(
        stdin_bytes=len(request.canonical_bytes),
        stdin_sent_bytes=len(request.canonical_bytes),
        stdout_bytes=len(response.raw_bytes),
        stdout_retained_bytes=len(response.raw_bytes),
    )
    evidence["response"] = {"sha256": response.sha256, "control": response.control()}
    return evidence


def test_launch_policy_must_bind_the_source_owned_request_not_a_free_request_id(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    next_runtime_v2_validation.validate_launch_policy_request_v2(policy, request, seal, assets)
    policy["request_id"] = "0" * 64
    next_runtime_v2_validation.validate_launch_policy_trusted_v2(policy, assets)
    with pytest.raises(ValueError, match=r"policy.*request"):
        next_runtime_v2_validation.validate_launch_policy_request_v2(policy, request, seal, assets)


def test_launch_policy_cannot_loosen_or_replace_the_source_owned_limits(tmp_path: Path) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    policy["limits"]["max_entities"] = 501
    next_runtime_v2_validation.validate_launch_policy_trusted_v2(policy, assets)
    with pytest.raises(ValueError, match=r"policy.*request limits"):
        next_runtime_v2_validation.validate_launch_policy_request_v2(policy, request, seal, assets)


def test_capture_counts_are_joined_to_the_same_canonical_stdin_not_free_numbers(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    evidence = complete_evidence(policy)
    size = len(request.canonical_bytes)
    evidence["capture"].update(stdin_bytes=size, stdin_sent_bytes=size)
    observation = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    next_runtime_v2_validation.validate_observation_request_v2(
        observation, policy, request, seal, assets
    )
    evidence["capture"].update(stdin_bytes=size + 1, stdin_sent_bytes=size + 1)
    unrelated = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    with pytest.raises(ValueError, match=r"stdin.*request bytes"):
        next_runtime_v2_validation.validate_observation_request_v2(
            unrelated, policy, request, seal, assets
        )


def test_response_control_is_bound_to_the_same_actual_request_frame(tmp_path: Path) -> None:
    seal, assets, request, _policy = request_inputs(tmp_path)
    wire = shape_wire(request)
    frame = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(wire).encode(), limits=request.record()["limits"]
    )
    next_runtime_v2_validation.validate_response_request_v2(frame, request, seal, assets)
    wire["control"]["binding"]["request_id"] = "0" * 64
    unrelated = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(wire).encode(), limits=request.record()["limits"]
    )
    with pytest.raises(ValueError, match="response request binding"):
        next_runtime_v2_validation.validate_response_request_v2(unrelated, request, seal, assets)


def test_response_adapter_version_must_echo_the_retained_request_identity(tmp_path: Path) -> None:
    seal, assets, request, _policy = request_inputs(tmp_path)
    wire = shape_wire(request)
    wire["control"]["adapter_version"] = "0.2.0"
    response = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(wire).encode(), limits=request.record()["limits"]
    )
    with pytest.raises(ValueError, match="response adapter"):
        next_runtime_v2_validation.validate_response_request_v2(response, request, seal, assets)


@pytest.mark.parametrize("field", ["trusted_type_environment_digest", "limits", "run_context"])
def test_success_payload_cannot_replace_source_owned_echoes(tmp_path: Path, field: str) -> None:
    seal, assets, request, _policy = request_inputs(tmp_path)
    wire = shape_wire(request)
    payload = wire["semantic_payload"]
    if field == "trusted_type_environment_digest":
        payload[field] = "0" * 64
    elif field == "limits":
        payload[field]["max_entities"] = 501
    elif field == "run_context":
        payload[field]["requested_formats"] = ["plantuml"]
    response = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(wire).encode(), limits=request.record()["limits"]
    )
    with pytest.raises(ValueError, match=r"response.*echo"):
        next_runtime_v2_validation.validate_response_request_v2(response, request, seal, assets)


def test_transport_candidate_requires_the_whole_exchange_not_only_a_payload_gate(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    response = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(shape_wire(request)).encode(), limits=request.record()["limits"]
    )
    observation = next_runtime_v2_reference.reference_process_observation_v2(
        policy, exchange_evidence(policy, request, response)
    )
    candidate = next_runtime_v2_reference.retain_transport_candidate_v2(
        seal, assets, request, policy, observation, response
    )
    assert candidate.request_id == request.request_id
    assert candidate.runtime_binding()["node_observation"] == {
        "version": "22.10.0",
        "source": "process.versions.node",
    }
    assert candidate.runtime_binding()["execution_asset_set_id"] == (
        "50923cb225647685051b2f46f14fe8fc4adc02b168906595e7ed5a518cd479a7"
    )
    assert candidate.runtime_binding()["runtime_toolchain_fingerprint"] == (
        "2654b8357780949c2f53254993c9bcbfd911c2222d3a69b6d1a6e4028330b888"
    )
    # The transport owner still must not certify this intentionally invalid model hash.
    assert candidate.semantic_payload()["model_digest"] == "0" * 64


@pytest.mark.parametrize("change", ["stdin", "stdout", "echo"])
def test_payload_gate_true_is_not_enough_for_a_mismatched_exchange(
    tmp_path: Path, change: str
) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    wire = shape_wire(request)
    if change == "echo":
        wire["semantic_payload"]["trusted_type_environment_digest"] = "0" * 64
    response = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(wire).encode(), limits=request.record()["limits"]
    )
    evidence = exchange_evidence(policy, request, response)
    if change == "stdin":
        evidence["capture"]["stdin_bytes"] += 1
        evidence["capture"]["stdin_sent_bytes"] += 1
    elif change == "stdout":
        evidence["capture"]["stdout_bytes"] += 1
        evidence["capture"]["stdout_retained_bytes"] += 1
    observation = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    assert observation["transport_payload_admissible"] is True
    with pytest.raises(ValueError):
        next_runtime_v2_reference.retain_transport_candidate_v2(
            seal, assets, request, policy, observation, response
        )


@pytest.mark.parametrize(
    "kind,exit_code",
    [
        ("protocol_failure", 65),
        ("unsupported_runtime", 66),
        ("bootstrap_failure", 67),
        ("semantic_failure", 68),
    ],
)
def test_controlled_failure_has_no_semantic_candidate_even_with_complete_capture(
    tmp_path: Path, kind: str, exit_code: int
) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    wire = shape_wire(request)
    wire["control"]["result_kind"] = kind
    wire["semantic_payload"] = None
    if kind == "protocol_failure":
        wire["control"]["binding"] = {"state": "unbound", "request_id": None}
        wire["control"]["runtime"] = None
    elif kind == "unsupported_runtime":
        wire["control"]["runtime"].update(
            version_raw="20.19.5", version="20.19.5", eligibility="unsupported"
        )
    elif kind == "bootstrap_failure":
        wire["control"]["runtime"] = None
    response = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(wire).encode(), limits=request.record()["limits"]
    )
    next_runtime_v2_validation.validate_response_request_v2(response, request, seal, assets)
    evidence = exchange_evidence(policy, request, response)
    evidence["exit_code"] = exit_code
    observation = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    assert observation["transport_payload_admissible"] is False
    with pytest.raises(ValueError, match="transport-admissible"):
        next_runtime_v2_reference.retain_transport_candidate_v2(
            seal, assets, request, policy, observation, response
        )
    assert response.semantic_payload() is None
    assert "target_completeness" not in observation


@pytest.mark.parametrize("cause", ["candidate_drift", "assets_drift", "cleanup_unverified"])
def test_late_transport_failure_keeps_control_prefix_but_cannot_mint_a_candidate(
    tmp_path: Path, cause: str
) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    response = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(shape_wire(request)).encode(), limits=request.record()["limits"]
    )
    evidence = exchange_evidence(policy, request, response)
    evidence["terminal_cause"] = cause
    evidence["capture"].update(stdout_retained_bytes=0, stderr_retained_bytes=0)
    if cause == "cleanup_unverified":
        evidence["cleanup"]["private_root_removed"] = False
    else:
        evidence[cause.removesuffix("_drift") + "_check"] = "drift"
    observation = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    assert observation["response"]["control"]["runtime"]["version"] == "22.10.0"
    with pytest.raises(ValueError, match="transport-admissible"):
        next_runtime_v2_reference.retain_transport_candidate_v2(
            seal, assets, request, policy, observation, response
        )


def test_transport_owner_has_no_mutable_alias_to_external_records(tmp_path: Path) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    response = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(shape_wire(request)).encode(), limits=request.record()["limits"]
    )
    observation = next_runtime_v2_reference.reference_process_observation_v2(
        policy, exchange_evidence(policy, request, response)
    )
    before = deepcopy(observation)
    candidate = next_runtime_v2_reference.retain_transport_candidate_v2(
        seal, assets, request, policy, observation, response
    )
    assert observation == before
    observation["response"]["control"]["runtime"]["version"] = "24.0.0"
    policy["node_candidate"]["sha256"] = "0" * 64
    candidate.runtime_binding()["node_observation"]["version"] = "25.0.0"
    candidate.semantic_payload()["model_digest"] = "1" * 64
    assert candidate.runtime_binding()["node_observation"]["version"] == "22.10.0"
    assert candidate.runtime_binding()["node_candidate"]["sha256"] == "2" * 64
    assert candidate.semantic_payload()["model_digest"] == "0" * 64
    assert candidate.request_frame() is request
    assert candidate.response_frame() is response
    assert "raw_bytes" not in repr(candidate)


def test_transport_constructor_and_response_duck_object_cannot_admit_a_candidate(
    tmp_path: Path,
) -> None:
    with pytest.raises(TypeError, match="retain_transport_candidate_v2"):
        next_runtime_v2_reference.ValidatedTransportCandidateV2()
    seal, assets, request, policy = request_inputs(tmp_path)
    response = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(shape_wire(request)).encode(), limits=request.record()["limits"]
    )
    observation = next_runtime_v2_reference.reference_process_observation_v2(
        policy, exchange_evidence(policy, request, response)
    )
    fake = SimpleNamespace(raw_bytes=response.raw_bytes, sha256=response.sha256)
    with pytest.raises(TypeError, match="retained frame owner"):
        next_runtime_v2_reference.retain_transport_candidate_v2(
            seal, assets, request, policy, observation, cast(Any, fake)
        )


def test_parent_compatibility_is_derived_after_the_actual_joined_control(tmp_path: Path) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    response = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(shape_wire(request)).encode(), limits=request.record()["limits"]
    )
    observation = next_runtime_v2_reference.reference_process_observation_v2(
        policy, exchange_evidence(policy, request, response)
    )
    candidate = next_runtime_v2_reference.retain_transport_candidate_v2(
        seal, assets, request, policy, observation, response
    )
    descriptor = next_runtime_v2_reference.compatibility_descriptor_v2(candidate)
    assert descriptor == json.loads(
        (ROOT / "tests/fixtures/next_runtime_v2/compatibility.json").read_text(encoding="utf-8")
    )
    assert descriptor["schema"] == "code-structure-viz.next-semantic-compatibility/v2"
    assert descriptor["semantic_schema"] == "code-structure-viz.semantic/v2"
    assert descriptor["runtime_binding_profile_id"] == "next-public-spawn-runtime-v1"
    assert descriptor["portable_toolchain_fingerprint"] == (
        "2654b8357780949c2f53254993c9bcbfd911c2222d3a69b6d1a6e4028330b888"
    )
    assert set(descriptor["identity_versions"].values()) == {1}


@pytest.mark.parametrize(
    "field",
    [
        "portable_toolchain_fingerprint",
        "trusted_type_environment_digest",
        "unicode_profile",
        "algorithm_versions",
        "compatibility_id",
    ],
)
def test_rehashing_a_foreign_compatibility_does_not_bind_it_to_the_actual_owner(
    tmp_path: Path, field: str
) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    response = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(shape_wire(request)).encode(), limits=request.record()["limits"]
    )
    observation = next_runtime_v2_reference.reference_process_observation_v2(
        policy, exchange_evidence(policy, request, response)
    )
    candidate = next_runtime_v2_reference.retain_transport_candidate_v2(
        seal, assets, request, policy, observation, response
    )
    descriptor = next_runtime_v2_reference.compatibility_descriptor_v2(candidate)
    if field == "unicode_profile":
        descriptor[field]["table_digest"] = "0" * 64
    elif field == "algorithm_versions":
        descriptor[field]["identifier_unicode_table_digest"] = "0" * 64
    else:
        descriptor[field] = "0" * 64
    if field != "compatibility_id":
        descriptor["compatibility_id"] = digest(
            {
                key: value
                for key, value in descriptor.items()
                if key not in {"schema", "compatibility_id"}
            }
        )
    with pytest.raises(
        ValueError, match=r"compatibility.*profile|compatibility.*binding|compatibility_id"
    ):
        next_runtime_v2_validation.validate_compatibility_descriptor_v2(descriptor, candidate)


def test_compatibility_excludes_host_paths_policy_observation_and_request_state(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    response = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(shape_wire(request)).encode(), limits=request.record()["limits"]
    )
    first_observation = next_runtime_v2_reference.reference_process_observation_v2(
        policy, exchange_evidence(policy, request, response)
    )
    first = next_runtime_v2_reference.retain_transport_candidate_v2(
        seal, assets, request, policy, first_observation, response
    )
    other_request = next_runtime_v2_reference.build_request_frame_v2(
        seal, assets, targets=[], run_context={**run_context(), "requested_formats": ["plantuml"]}
    )
    assert other_request.request_id != request.request_id
    relocated = deepcopy(policy)
    relocated.update(
        request_id=other_request.request_id,
        private_root="/private/run/other",
        runtime_directory="/private/run/other/runtime",
        cwd="/private/run/other/cwd",
    )
    relocated["node_candidate"]["absolute_path"] = "/opt/other/node"
    relocated["argv"] = [
        "/opt/other/node",
        "--max-old-space-size=512",
        "/private/run/other/runtime/next-adapter.mjs",
    ]
    other_response = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(shape_wire(other_request)).encode(), limits=other_request.record()["limits"]
    )
    other_observation = next_runtime_v2_reference.reference_process_observation_v2(
        relocated, exchange_evidence(relocated, other_request, other_response)
    )
    assert other_observation["policy_digest"] != first_observation["policy_digest"]
    other = next_runtime_v2_reference.retain_transport_candidate_v2(
        seal, assets, other_request, relocated, other_observation, other_response
    )
    assert next_runtime_v2_reference.compatibility_descriptor_v2(other) == (
        next_runtime_v2_reference.compatibility_descriptor_v2(first)
    )


def test_compatibility_cannot_use_a_duck_candidate_or_carry_parent_private_fields(
    tmp_path: Path,
) -> None:
    with pytest.raises(TypeError, match="transport candidate owner"):
        next_runtime_v2_reference.compatibility_descriptor_v2(cast(Any, SimpleNamespace()))
    seal, assets, request, policy = request_inputs(tmp_path)
    response = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(shape_wire(request)).encode(), limits=request.record()["limits"]
    )
    observation = next_runtime_v2_reference.reference_process_observation_v2(
        policy, exchange_evidence(policy, request, response)
    )
    candidate = next_runtime_v2_reference.retain_transport_candidate_v2(
        seal, assets, request, policy, observation, response
    )
    descriptor = next_runtime_v2_reference.compatibility_descriptor_v2(candidate)
    with pytest.raises(TypeError, match="transport candidate owner"):
        next_runtime_v2_validation.validate_compatibility_descriptor_v2(
            descriptor, cast(Any, SimpleNamespace())
        )
    descriptor["node_path"] = "/opt/user/node"
    with pytest.raises(ValidationError, match="Additional properties"):
        next_runtime_v2_validation.validate_compatibility_descriptor_v2(descriptor, candidate)
