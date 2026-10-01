"""Core admission is independent of transport shape and runtime data joins."""

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Literal, cast

import pytest

from code_structure_viz.adapters.next.source_acquisition import SourceAcquisitionSeal
from tests.contracts import next_runtime_v2_reference, next_runtime_v2_validation
from tests.contracts.next_reference_validation import (
    ModelRecordLimitError,
    digest,
    expected_export_observations,
)
from tests.contracts.next_runtime_v2_fixtures import (
    analysis_context_fixture_v2,
    sealed_source_fixture_v1,
)
from tests.contracts.test_next_exchange_v2 import exchange_evidence, request_inputs, shape_wire
from tests.contracts.test_next_process_observation_v2 import policy_fixture
from tests.contracts.test_next_request_frame_v2 import run_context
from tests.contracts.test_next_trusted_environment_v2 import profile_members

CARD_MODULE_ID = "next:module:824683f7952e8b11fdeb41f85419fe44398dac828c221140a11bd31e433df71e"
CARD_FACT_ID = "next:fact:88cd5b76689041e7b68f733b5fc162f5ae0cdff5aef9f10c861f6ab5a7959999"
PROJECT_ID = "next:project:530b20c858c6039c19737f386f96cfabdadda6b8a0a1c98b5ca639beb2765c25"
COLLECTIONS = ("projects", "files", "modules", "components", "members", "relations", "facts")


def core_inputs(
    tmp_path: Path,
    *,
    targets: list[str] | None = None,
    max_entities: int = 500,
    empty_membership: bool = False,
    corpus: Literal["card", "string-unknown"] = "card",
) -> tuple[
    SourceAcquisitionSeal,
    next_runtime_v2_reference.RetainedExecutionAssets,
    next_runtime_v2_reference.RetainedRequestFrameV2,
    dict[str, Any],
    dict[str, Any],
]:
    """A real source seal for one known semantic corpus file; no child execution."""

    assets = next_runtime_v2_reference.retain_execution_assets_v1(profile_members())
    descriptor = next_runtime_v2_reference.trusted_environment_manifest_v2(assets)[
        "environment_descriptor"
    ]
    program_path = "src/Card.tsx" if corpus == "card" else "src/string-unknown.tsx"
    program_content = (
        b"const Card = 1;\n"
        if corpus == "card"
        else (b'const value = makeValue();\nexport { value as "opaque-public-name" };\n')
    )
    module_id = (
        CARD_MODULE_ID
        if corpus == "card"
        else ("next:module:0d5793bbfc727772d88500d15174f3e1d0e105a7fa288f777411d3359f5df50a")
    )
    fact_id = (
        CARD_FACT_ID
        if corpus == "card"
        else ("next:fact:ac9c259691a94d1f6d7e3130c79153d96bb691282ff9f2889125ec1a582ee390")
    )
    seal = sealed_source_fixture_v1(
        tmp_path,
        trusted_digest=descriptor["sha256"],
        program_path=program_path,
        page_content=program_content,
        config_content=b'{"include":[]}' if empty_membership else b'{"include":["src/**/*"]}',
        max_entities=max_entities,
    )
    request = next_runtime_v2_reference.build_request_frame_v2(
        seal,
        assets,
        analysis_context_fixture_v2(
            seal,
            assets,
            targets=targets or [],
            run_context=run_context()
            if max_entities == 500
            else {
                **run_context(),
                "budget_requested": max_entities,
                "budget_resolved": max_entities,
                "budget_source": "cli",
            },
        ),
    )
    policy = policy_fixture()
    policy.update(
        request_id=request.request_id,
        adapter=assets.adapter_identity(),
        execution_asset_set_id=assets.descriptor()["asset_set_id"],
        trusted_environment_digest=descriptor["sha256"],
        limits=request.record()["limits"],
    )
    wire = shape_wire(request)
    model = wire["semantic_payload"]["model"]
    model["projects"] = request.record()["projects"]
    model["files"] = [
        {key: value for key, value in record.items() if key != "content_base64"}
        for record in request.record()["files"]
    ]
    # Identity preimages were worked independently with jq/shasum, not the new producer.
    model["modules"] = (
        []
        if empty_membership
        else [
            {
                "kind": "module",
                "id": module_id,
                "project_id": PROJECT_ID,
                "path": program_path,
                "router_context": "none",
                "client_entry": False,
                "derived_roles": [],
            }
        ]
    )
    model["facts"] = (
        []
        if empty_membership
        else [
            {
                "kind": "router_context",
                "id": fact_id,
                "owner_id": module_id,
                "value": "none",
            }
        ]
    )
    counts = model["coverage"]["counts"]
    counts.update({name: len(model[name]) for name in COLLECTIONS})
    published = sum(len(model[name]) for name in COLLECTIONS)
    counts.update(
        published=published, discovered=published, internal_entities=len(model["modules"])
    )
    wire["semantic_payload"]["proof"]["discovered_records"] = [
        {"collection": collection, "record_id": record["id"], "taints": []}
        for collection in COLLECTIONS
        for record in model[collection]
    ]
    if corpus == "string-unknown":
        # This reuses the old corpus witness, never an old runtime/envelope certificate.
        wire["semantic_payload"]["proof"]["export_observations"] = expected_export_observations(
            model
        )
    if targets == ["path:src/Card.tsx"]:
        card_file = next(record for record in model["files"] if record["path"] == "src/Card.tsx")
        record_ids = sorted([card_file["id"], CARD_MODULE_ID])
        wire["semantic_payload"]["proof"]["target_resolutions"] = [
            {"target_key": "path:src/Card.tsx", "status": "resolved", "record_ids": record_ids}
        ]
        model["coverage"]["target_completeness"] = [
            {"target_key": "path:src/Card.tsx", "status": "complete", "record_ids": record_ids}
        ]
    update_model_digest(wire)
    return seal, assets, request, policy, wire


def update_model_digest(wire: dict[str, Any]) -> None:
    # ASCII known corpus: independently spell canonical wire bytes rather than call the gate.
    model_bytes = json.dumps(
        wire["semantic_payload"]["model"], sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    wire["semantic_payload"]["model_digest"] = hashlib.sha256(model_bytes).hexdigest()


def candidate_for(
    seal: SourceAcquisitionSeal,
    assets: next_runtime_v2_reference.RetainedExecutionAssets,
    request: next_runtime_v2_reference.RetainedRequestFrameV2,
    policy: dict[str, Any],
    wire: dict[str, Any],
) -> next_runtime_v2_reference.ValidatedTransportCandidateV2:
    response = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(wire).encode(), limits=request.record()["limits"]
    )
    observation = next_runtime_v2_reference.reference_process_observation_v2(
        policy, exchange_evidence(policy, request, response)
    )
    return next_runtime_v2_reference.retain_transport_candidate_v2(
        seal, assets, request, policy, observation, response
    )


def test_core_rejects_a_transport_admissible_payload_with_a_fabricated_model_digest(
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
    with pytest.raises(ValueError, match="model digest"):
        next_runtime_v2_validation.validate_semantic_candidate_v2(candidate, seal, assets)


def test_rehashing_an_empty_model_cannot_claim_the_frozen_project_was_analyzed(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    wire = shape_wire(request)
    wire["semantic_payload"]["model_digest"] = digest(wire["semantic_payload"]["model"])
    response = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(wire).encode(), limits=request.record()["limits"]
    )
    observation = next_runtime_v2_reference.reference_process_observation_v2(
        policy, exchange_evidence(policy, request, response)
    )
    candidate = next_runtime_v2_reference.retain_transport_candidate_v2(
        seal, assets, request, policy, observation, response
    )
    with pytest.raises(ValueError, match="project correspondence"):
        next_runtime_v2_validation.validate_semantic_candidate_v2(candidate, seal, assets)


def test_rehashing_source_metadata_cannot_substitute_other_analyzed_bytes(tmp_path: Path) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    wire = shape_wire(request)
    model = wire["semantic_payload"]["model"]
    model["projects"] = request.record()["projects"]
    model["files"] = [
        {key: value for key, value in record.items() if key != "content_base64"}
        for record in request.record()["files"]
    ]
    model["files"][0]["sha256"] = "0" * 64
    wire["semantic_payload"]["model_digest"] = digest(model)
    response = next_runtime_v2_reference.retain_response_frame_v2(
        json.dumps(wire).encode(), limits=request.record()["limits"]
    )
    observation = next_runtime_v2_reference.reference_process_observation_v2(
        policy, exchange_evidence(policy, request, response)
    )
    candidate = next_runtime_v2_reference.retain_transport_candidate_v2(
        seal, assets, request, policy, observation, response
    )
    with pytest.raises(ValueError, match="file correspondence"):
        next_runtime_v2_validation.validate_semantic_candidate_v2(candidate, seal, assets)


def test_core_accepts_a_closed_source_bound_module_and_complete_proof(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = core_inputs(tmp_path)
    candidate = candidate_for(seal, assets, request, policy, wire)
    gate = next_runtime_v2_validation.validate_semantic_candidate_v2(candidate, seal, assets)
    assert gate["actual"] == 1
    assert gate["resolved"] == 500
    assert gate["payload_available"] is True
    assert gate["outcome"] == gate["original_outcome"] == "complete"
    assert gate["diagnostic_code"] is None
    assert gate["artifact_paths"] == ["next.snapshot.semantic.json"]


def test_selected_missing_module_is_a_proof_bound_target_failure_not_a_protocol_assertion(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy, wire = core_inputs(tmp_path, targets=["path:src/Card.tsx"])
    model = wire["semantic_payload"]["model"]
    model["modules"] = []
    model["facts"] = []
    model["coverage"]["counts"].update(
        modules=0, facts=0, internal_entities=0, published=5, discovered=5
    )
    proof = wire["semantic_payload"]["proof"]
    proof["discovered_records"] = [
        row for row in proof["discovered_records"] if row["collection"] not in {"modules", "facts"}
    ]
    proof["target_resolutions"] = [
        {
            "target_key": "path:src/Card.tsx",
            "status": "failed",
            "record_ids": [],
            "reason": "missing",
        }
    ]
    model["coverage"]["target_completeness"] = [
        {
            "target_key": "path:src/Card.tsx",
            "status": "failed",
            "record_ids": [],
            "reason": "missing",
        }
    ]
    update_model_digest(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    gate = next_runtime_v2_validation.validate_semantic_candidate_v2(candidate, seal, assets)
    assert gate["outcome"] == "payload_unavailable"
    assert gate["diagnostic_code"] == "CSV-NEXT-TARGET-001"
    assert gate["actual"] is None
    assert gate["payload_available"] is False
    assert gate["artifact_paths"] == []
    assert gate["target_failures"] == [{"target_key": "path:src/Card.tsx", "reason": "missing"}]


def test_only_byte_identical_selected_duplicate_modules_get_typed_target_routing(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy, wire = core_inputs(tmp_path, targets=["path:src/Card.tsx"])
    model = wire["semantic_payload"]["model"]
    model["modules"].append(deepcopy(model["modules"][0]))
    model["coverage"]["counts"].update(modules=2, internal_entities=2, published=8, discovered=8)
    failure_row = {
        "target_key": "path:src/Card.tsx",
        "status": "failed",
        "record_ids": [],
        "reason": "duplicate",
    }
    model["coverage"]["target_completeness"] = [deepcopy(failure_row)]
    wire["semantic_payload"]["proof"]["target_resolutions"] = [deepcopy(failure_row)]
    update_model_digest(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    gate = next_runtime_v2_validation.validate_semantic_candidate_v2(candidate, seal, assets)
    assert gate["target_failures"] == [{"target_key": "path:src/Card.tsx", "reason": "duplicate"}]
    assert gate["diagnostic_code"] == "CSV-NEXT-TARGET-001"
    model["modules"][1]["client_entry"] = True
    update_model_digest(wire)
    inconsistent = candidate_for(seal, assets, request, policy, wire)
    with pytest.raises(ValueError, match="model/proof"):
        next_runtime_v2_validation.validate_semantic_candidate_v2(inconsistent, seal, assets)


@pytest.mark.parametrize(
    "mutation",
    ["id", "dangling_fact", "count", "missing_proof", "duplicate_proof", "proof_payload", "target"],
)
def test_rehashing_shape_valid_records_cannot_bypass_core_references_counts_or_proof(
    tmp_path: Path,
    mutation: str,
) -> None:
    seal, assets, request, policy, wire = core_inputs(tmp_path)
    model, proof = wire["semantic_payload"]["model"], wire["semantic_payload"]["proof"]
    if mutation == "id":
        model["modules"][0]["id"] = "next:module:" + "0" * 64
    elif mutation == "dangling_fact":
        model["facts"][0]["owner_id"] = "next:module:" + "0" * 64
    elif mutation == "count":
        model["coverage"]["counts"]["internal_entities"] = 0
    elif mutation == "missing_proof":
        proof["discovered_records"].pop()
    elif mutation == "duplicate_proof":
        proof["discovered_records"].append(deepcopy(proof["discovered_records"][0]))
    elif mutation == "proof_payload":
        proof["discovered_records"][0]["record"] = deepcopy(model["projects"][0])
    else:
        proof["target_resolutions"] = [
            {
                "target_key": "path:src/Card.tsx",
                "status": "resolved",
                "record_ids": [CARD_MODULE_ID],
            }
        ]
    update_model_digest(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    with pytest.raises(ValueError, match=r"model/proof|proof-only source"):
        next_runtime_v2_validation.validate_semantic_candidate_v2(candidate, seal, assets)


def test_empty_membership_is_accepted_only_after_source_correspondence_and_complete_proof(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy, wire = core_inputs(tmp_path, empty_membership=True)
    assert all(record["effective_role"] != "program" for record in request.record()["files"])
    candidate = candidate_for(seal, assets, request, policy, wire)
    gate = next_runtime_v2_validation.validate_semantic_candidate_v2(candidate, seal, assets)
    assert gate["actual"] == 0
    assert gate["payload_available"] is True
    assert gate["outcome"] == "complete"
    wire["semantic_payload"]["proof"]["discovered_records"] = []
    invalid = candidate_for(seal, assets, request, policy, wire)
    with pytest.raises(ValueError, match="model/proof"):
        next_runtime_v2_validation.validate_semantic_candidate_v2(invalid, seal, assets)


def test_entity_exact_plus_one_preserves_the_pre_budget_semantic_outcome(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = core_inputs(tmp_path, max_entities=1)
    exact = candidate_for(seal, assets, request, policy, wire)
    exact_gate = next_runtime_v2_validation.validate_semantic_candidate_v2(exact, seal, assets)
    assert (exact_gate["actual"], exact_gate["resolved"], exact_gate["outcome"]) == (
        1,
        1,
        "complete",
    )
    model = wire["semantic_payload"]["model"]
    component_id = "next:component:6227b1d19e897d12ed303743051ed58b6fac3fd2b7c64b03175713939d0cc3d9"
    # Synthetic known-corpus semantic records exercise the count gate, not real TS recognition.
    model["components"] = [
        {
            "kind": "component",
            "id": component_id,
            "module_id": CARD_MODULE_ID,
            "declaration_key": "Card",
            "recognition_evidence": ["trusted_callable"],
            "props_state": "no_props",
        }
    ]
    model["coverage"]["counts"].update(components=1, internal_entities=2, published=8, discovered=8)
    proof = wire["semantic_payload"]["proof"]
    proof["discovered_records"] = [
        {"collection": collection, "record_id": record["id"], "taints": []}
        for collection in COLLECTIONS
        for record in model[collection]
    ]
    model["diagnostics"] = [
        {
            "code": "CSV-NEXT-TYPE-001",
            "severity": "warning",
            "recoverable": True,
            "outcome": "partial_safe",
            "ref_permission": "symbol",
            "path_ref": None,
            "symbol_ref": component_id,
            "count": 1,
        }
    ]
    update_model_digest(wire)
    over = candidate_for(seal, assets, request, policy, wire)
    over_gate = next_runtime_v2_validation.validate_semantic_candidate_v2(over, seal, assets)
    assert (over_gate["actual"], over_gate["resolved"]) == (2, 1)
    assert over_gate["original_outcome"] == "partial_safe"
    assert over_gate["outcome"] == "payload_unavailable"
    assert over_gate["diagnostic_code"] == "CSV-NEXT-LIMIT-005"
    assert over_gate["payload_available"] is False
    assert over_gate["artifact_paths"] == []


def test_core_decision_keeps_one_immutable_source_transport_gate_and_parent_compatibility(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy, wire = core_inputs(tmp_path)
    candidate = candidate_for(seal, assets, request, policy, wire)
    decision = next_runtime_v2_reference.decide_semantic_candidate_v2(candidate, seal, assets)
    assert decision.request_id == request.request_id
    assert decision.transport_candidate() is candidate
    assert decision.source_seal() is seal
    assert decision.execution_assets() is assets
    assert decision.gate()["actual"] == 1
    assert decision.compatibility_descriptor() == json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "tests/fixtures/next_runtime_v2/compatibility.json"
        ).read_text()
    )
    next_runtime_v2_validation.validate_semantic_decision_v2(decision)
    decision.gate()["outcome"] = "payload_unavailable"
    decision.compatibility_descriptor()["compatibility_id"] = "0" * 64
    decision.transport_candidate().semantic_payload()["model"]["modules"] = []
    assert decision.gate()["outcome"] == "complete"
    assert (
        decision.transport_candidate().semantic_payload()["model"]["modules"][0]["id"]
        == CARD_MODULE_ID
    )
    next_runtime_v2_validation.validate_semantic_decision_v2(decision)
    assert "const Card" not in repr(decision)


def test_proof_selected_taint_is_not_upgraded_to_safe_partial_by_the_entity_gate(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy, wire = core_inputs(tmp_path, targets=["path:src/Card.tsx"])
    model, proof = wire["semantic_payload"]["model"], wire["semantic_payload"]["proof"]
    component_id = "next:component:6227b1d19e897d12ed303743051ed58b6fac3fd2b7c64b03175713939d0cc3d9"
    failure_id = "next:failure:" + "1" * 64
    proof["discovered_records"].append(
        {
            "collection": "components",
            "record_id": component_id,
            "taints": ["type_symbol"],
            "record": {
                "kind": "component",
                "id": component_id,
                "module_id": CARD_MODULE_ID,
                "declaration_key": "Card",
                "recognition_evidence": ["trusted_callable"],
                "props_state": "no_props",
            },
        }
    )
    proof["failure_roots"] = [
        {
            "id": failure_id,
            "collection": "components",
            "kind": "type_symbol",
            "path_ref": None,
            "record_ids": [component_id],
        }
    ]
    proof["causal_edges"] = [
        {"source_id": failure_id, "record_id": component_id, "rule": "type_subtree"}
    ]
    proof["excluded"] = [
        {"collection": "components", "record_id": component_id, "reason": "tainted"}
    ]
    proof["target_resolutions"] = [
        {
            "target_key": "path:src/Card.tsx",
            "status": "failed",
            "record_ids": [],
            "reason": "selected_taint",
        }
    ]
    model["coverage"].update(affected_ids=[component_id], taint_frontier=[CARD_MODULE_ID])
    model["coverage"]["counts"].update(discovered=8, excluded=1)
    model["coverage"]["target_completeness"] = deepcopy(proof["target_resolutions"])
    model["diagnostics"] = [
        {
            "code": "CSV-NEXT-TYPE-001",
            "severity": "warning",
            "recoverable": True,
            "outcome": "partial_safe",
            "ref_permission": "symbol",
            "path_ref": None,
            "symbol_ref": component_id,
            "count": 1,
        }
    ]
    update_model_digest(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    gate = next_runtime_v2_validation.validate_semantic_candidate_v2(candidate, seal, assets)
    assert gate["outcome"] == "payload_unavailable"
    assert gate["diagnostic_code"] == "CSV-NEXT-TARGET-001"
    assert gate["target_failures"] == [
        {"target_key": "path:src/Card.tsx", "reason": "selected_taint"}
    ]


def model_record_inputs(
    tmp_path: Path, delta: int
) -> tuple[
    SourceAcquisitionSeal,
    next_runtime_v2_reference.RetainedExecutionAssets,
    next_runtime_v2_reference.RetainedRequestFrameV2,
    dict[str, Any],
    dict[str, Any],
]:
    """Generate actual 10,000/+1 wire records on the existing four-file source seal."""

    seal, assets, request, policy, wire = core_inputs(tmp_path)
    model = wire["semantic_payload"]["model"]
    component_id = "next:component:6227b1d19e897d12ed303743051ed58b6fac3fd2b7c64b03175713939d0cc3d9"
    model["components"] = [
        {
            "kind": "component",
            "id": component_id,
            "module_id": CARD_MODULE_ID,
            "declaration_key": "Card",
            "recognition_evidence": ["trusted_callable"],
            "props_state": "known",
        }
    ]
    members: list[dict[str, Any]] = []
    for index in range(9_992 + delta):
        name = f"p{index:05d}"
        preimage = {
            "kind": "prop",
            "version": 1,
            "identity": {"owner_id": component_id, "name": name},
        }
        record_id = (
            "next:member:"
            + hashlib.sha256(
                json.dumps(preimage, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
        )
        members.append(
            {
                "kind": "prop",
                "id": record_id,
                "owner_id": component_id,
                "name": name,
                "type_node": {"kind": "primitive", "name": "string"},
                "optional": False,
                "readonly": False,
                "default_evidence": "none",
            }
        )
    model["members"] = sorted(members, key=lambda member: member["id"])
    model["coverage"]["counts"].update(
        components=1,
        members=9_992 + delta,
        internal_entities=2,
        published=10_000 + delta,
        discovered=10_000 + delta,
    )
    wire["semantic_payload"]["proof"]["discovered_records"] = [
        {"collection": collection, "record_id": record["id"], "taints": []}
        for collection in COLLECTIONS
        for record in model[collection]
    ]
    update_model_digest(wire)
    assert model["coverage"]["counts"]["published"] == 10_000 + delta
    return seal, assets, request, policy, wire


@pytest.mark.parametrize("delta", [0, 1])
def test_source_bound_generated_model_record_limit_exact_plus_one(
    tmp_path: Path, delta: int
) -> None:
    seal, assets, request, policy, wire = model_record_inputs(tmp_path, delta)
    candidate = candidate_for(seal, assets, request, policy, wire)
    if delta == 0:
        gate = next_runtime_v2_validation.validate_semantic_candidate_v2(candidate, seal, assets)
        assert gate["actual"] == 2
        assert gate["payload_available"] is True
    else:
        with pytest.raises(ModelRecordLimitError) as captured:
            next_runtime_v2_validation.validate_semantic_candidate_v2(candidate, seal, assets)
        assert captured.value.measured == 10_001
        # A malformed proof must be a protocol refusal, not hidden by the later count gate.
        wire["semantic_payload"]["proof"]["discovered_records"].pop()
        bad_proof = candidate_for(seal, assets, request, policy, wire)
        with pytest.raises(ValueError, match="model/proof"):
            next_runtime_v2_validation.validate_semantic_candidate_v2(bad_proof, seal, assets)


def test_proof_valid_unknown_string_export_is_export_unavailable_not_complete(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy, wire = core_inputs(tmp_path, corpus="string-unknown")
    observations = wire["semantic_payload"]["proof"]["export_observations"]
    assert len(observations) == 1
    assert observations[0]["disposition"] == "export_failure"
    candidate = candidate_for(seal, assets, request, policy, wire)
    gate = next_runtime_v2_validation.validate_semantic_candidate_v2(candidate, seal, assets)
    assert gate["outcome"] == "payload_unavailable"
    assert gate["payload_available"] is False
    assert gate["diagnostic_code"] == "CSV-NEXT-EXPORT-001"
    assert gate["artifact_paths"] == []
    assert gate["export_failures"][0]["diagnostic"] == "unsupported_string_export"


def test_semantic_authority_has_no_public_constructor_or_duck_projection_bypass(
    tmp_path: Path,
) -> None:
    with pytest.raises(TypeError, match="decide_semantic_candidate_v2"):
        next_runtime_v2_reference.ValidatedSemanticDecisionV2()
    with pytest.raises(TypeError, match="Core decision owner"):
        next_runtime_v2_validation.validate_semantic_decision_v2(cast(Any, SimpleNamespace()))
    seal, assets, _request, _policy, _wire = core_inputs(tmp_path)
    with pytest.raises(TypeError, match="transport candidate owner"):
        next_runtime_v2_reference.decide_semantic_candidate_v2(
            cast(Any, SimpleNamespace()), seal, assets
        )


def test_semantic_decision_cannot_be_rebound_to_a_different_actual_source_seal(
    tmp_path: Path,
) -> None:
    original = tmp_path / "original"
    original.mkdir()
    seal, assets, request, policy, wire = core_inputs(original)
    candidate = candidate_for(seal, assets, request, policy, wire)
    changed = tmp_path / "changed"
    changed.mkdir()
    trusted = next_runtime_v2_reference.trusted_environment_manifest_v2(assets)[
        "environment_descriptor"
    ]
    other = sealed_source_fixture_v1(changed, trusted_digest=trusted["sha256"])
    with pytest.raises(ValueError):
        next_runtime_v2_reference.decide_semantic_candidate_v2(candidate, other, assets)


def test_proof_only_file_cannot_invent_bytes_outside_the_frozen_request(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = core_inputs(tmp_path)
    preimage = {
        "kind": "file",
        "version": 1,
        "identity": {"project_id": PROJECT_ID, "path": "src/ghost.d.ts"},
    }
    record_id = (
        "next:file:"
        + hashlib.sha256(
            json.dumps(preimage, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    )
    ghost = {
        "kind": "file",
        "id": record_id,
        "project_id": PROJECT_ID,
        "path": "src/ghost.d.ts",
        "roles": ["context"],
        "effective_role": "context",
        "size_bytes": 0,
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    }
    proof = wire["semantic_payload"]["proof"]
    proof["discovered_records"].append(
        {"collection": "files", "record_id": record_id, "taints": [], "record": ghost}
    )
    proof["excluded"] = [{"collection": "files", "record_id": record_id, "reason": "not_selected"}]
    wire["semantic_payload"]["model"]["coverage"]["counts"].update(discovered=8, excluded=1)
    update_model_digest(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    with pytest.raises(ValueError, match=r"proof.*source"):
        next_runtime_v2_validation.validate_semantic_candidate_v2(candidate, seal, assets)


@pytest.mark.parametrize("path", ["src/ghost.tsx", "src/global.d.ts"])
def test_proof_only_module_requires_a_frozen_program_file_not_a_context_or_ghost(
    tmp_path: Path,
    path: str,
) -> None:
    seal, assets, request, policy, wire = core_inputs(tmp_path)
    preimage = {
        "kind": "module",
        "version": 1,
        "identity": {"project_id": PROJECT_ID, "path": path},
    }
    record_id = (
        "next:module:"
        + hashlib.sha256(
            json.dumps(preimage, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    )
    record = {
        "kind": "module",
        "id": record_id,
        "project_id": PROJECT_ID,
        "path": path,
        "router_context": "none",
        "client_entry": False,
        "derived_roles": [],
    }
    proof = wire["semantic_payload"]["proof"]
    proof["discovered_records"].append(
        {"collection": "modules", "record_id": record_id, "taints": [], "record": record}
    )
    proof["excluded"] = [
        {"collection": "modules", "record_id": record_id, "reason": "not_selected"}
    ]
    wire["semantic_payload"]["model"]["coverage"]["counts"].update(discovered=8, excluded=1)
    update_model_digest(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    with pytest.raises(ValueError, match=r"proof.*source"):
        next_runtime_v2_validation.validate_semantic_candidate_v2(candidate, seal, assets)


def test_excluding_a_proof_only_component_does_not_allow_a_dangling_module_owner(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy, wire = core_inputs(tmp_path)
    module_id = "next:module:" + "0" * 64
    preimage = {
        "kind": "component",
        "version": 1,
        "identity": {"module_id": module_id, "declaration_key": "Ghost"},
    }
    record_id = (
        "next:component:"
        + hashlib.sha256(
            json.dumps(preimage, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    )
    record = {
        "kind": "component",
        "id": record_id,
        "module_id": module_id,
        "declaration_key": "Ghost",
        "recognition_evidence": ["trusted_callable"],
        "props_state": "no_props",
    }
    proof = wire["semantic_payload"]["proof"]
    proof["discovered_records"].append(
        {"collection": "components", "record_id": record_id, "taints": [], "record": record}
    )
    proof["excluded"] = [
        {"collection": "components", "record_id": record_id, "reason": "not_selected"}
    ]
    wire["semantic_payload"]["model"]["coverage"]["counts"].update(discovered=8, excluded=1)
    update_model_digest(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    with pytest.raises(ValueError, match=r"proof.*reference"):
        next_runtime_v2_validation.validate_semantic_candidate_v2(candidate, seal, assets)
