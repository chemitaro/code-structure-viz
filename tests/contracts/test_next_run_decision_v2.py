"""Request-bound run records are owner-derived, not publication/OS certificates."""

import hashlib
import json
from copy import copy, deepcopy
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from jsonschema import ValidationError  # type: ignore[import-untyped]

from tests.contracts import next_run_decision_v2_reference as run_reference
from tests.contracts import next_runtime_v2_reference as runtime_reference
from tests.contracts.next_run_decision_v2_validation import validate_request_bound_run_decision_v2
from tests.contracts.next_runtime_v2_validation import _validate_schema
from tests.contracts.test_next_core_failure_v2 import runtime_for_core_wire
from tests.contracts.test_next_exchange_v2 import exchange_evidence, request_inputs, shape_wire
from tests.contracts.test_next_observed_response_receipt_v2 import protocol_runtime
from tests.contracts.test_next_process_observation_v2 import complete_evidence
from tests.contracts.test_next_provenance_v2 import complete_core_runtime
from tests.contracts.test_next_public_semantic_v2 import (
    CARD_COMPONENT_ID,
    RUN_PREIMAGE_FIELDS,
    independent_ascii_hash,
)
from tests.contracts.test_next_semantic_candidate_v2 import (
    CARD_MODULE_ID,
    core_inputs,
    model_record_inputs,
    update_model_digest,
)

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def complete_run_owner(
    tmp_path_factory: pytest.TempPathFactory,
) -> run_reference.RetainedRequestBoundRunDecisionV2:
    runtime, core = complete_core_runtime(tmp_path_factory.mktemp("run2-known"))
    return run_reference.retain_request_bound_run_decision_v2(runtime, semantic_decision=core)


def complete_shape() -> dict[str, Any]:
    """Shape-only example; these placeholders are not actual owner digests."""

    observed = {
        key: {
            "state": "observed",
            "value": {
                "schema": "code-structure-viz.next-observation/v2",
                "version": 2,
                "sha256": "1" * 64,
            },
        }
        for key in (
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
    }
    return {
        "schema": "code-structure-viz.next-run-decision/v2",
        "version": 2,
        "kind": "request_bound_success",
        "status": "complete",
        "outcome": "complete",
        "request_independent": False,
        "payload_available": True,
        "exit_code": 0,
        "provenance": {
            "schema": "code-structure-viz.next-provenance/v2",
            "kind": "request_bound_success",
            "stage": None,
            "failure_code": None,
            "observed": observed,
        },
        "context": {
            "request_id": "2" * 64,
            "run_fingerprint": "3" * 64,
            "run_context": {
                "requested_formats": ["semantic-json", "plantuml"],
                "budget_requested": None,
                "budget_resolved": 500,
                "budget_source": "builtin",
                "stdout_selector": None,
            },
            "analysis_intent": {"targets": [], "upstream_depth": 0, "downstream_depth": 0},
            "domain_config_digest": "4" * 64,
            "source_plan_digest": "5" * 64,
            "source_view_fingerprint": "6" * 64,
            "compatibility_id": "7" * 64,
            "observed_prefix": observed,
        },
        "request": {
            "request_id": "2" * 64,
            "raw_sha256": "8" * 64,
            "byte_length": 3961,
            "canonical_json": True,
        },
        "response": {"raw_sha256": "9" * 64, "byte_length": 9472, "canonical_json": False},
        "core_measurement": {"kind": "entity_budget", "actual": 1, "limit": 500},
    }


def test_run_v2_schema_accepts_closed_complete_and_noncanonical_observed_response() -> None:
    _validate_schema("next-run-decision-v2", complete_shape())


def test_run_v2_complete_projects_the_same_runtime_core_and_parent_context(tmp_path: Path) -> None:
    runtime, core = complete_core_runtime(tmp_path)

    owner = run_reference.retain_request_bound_run_decision_v2(runtime, semantic_decision=core)
    record = run_reference.project_request_bound_run_decision_v2(owner)
    assert owner.runtime_result() is runtime
    assert owner.semantic_decision() is core
    assert (record["kind"], record["status"], record["outcome"], record["exit_code"]) == (
        "request_bound_success",
        "complete",
        "complete",
        0,
    )
    assert record["context"]["run_fingerprint"] == (
        "066d76ba2cfbae97b137a7a1bd59a4181dee2c0ccf31f5c013a9a1735dc8c56e"
    )
    assert record["context"]["observed_prefix"] == record["provenance"]["observed"]
    assert record["response"]["canonical_json"] is False
    assert record["core_measurement"] == {"kind": "entity_budget", "actual": 1, "limit": 500}
    validate_request_bound_run_decision_v2(record, owner)


def test_run_v2_target_unavailable_keeps_core_identity_without_entity_measurement(
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
    resolution = {
        "target_key": "path:src/Card.tsx",
        "status": "failed",
        "record_ids": [],
        "reason": "missing",
    }
    proof["target_resolutions"] = [resolution]
    model["coverage"]["target_completeness"] = [resolution]
    update_model_digest(wire)
    runtime = runtime_for_core_wire(seal, assets, request, policy, wire)
    candidate = runtime.transport_candidate()
    assert candidate is not None
    core = runtime_reference.decide_semantic_candidate_v2(candidate, seal, assets)
    assert core.gate()["actual"] is None
    owner = run_reference.retain_request_bound_run_decision_v2(runtime, semantic_decision=core)
    record = owner.record()
    assert (
        record["kind"],
        record["status"],
        record["outcome"],
        record["payload_available"],
        record["exit_code"],
    ) == (
        "request_bound_failure",
        "incomplete",
        "payload_unavailable",
        False,
        3,
    )
    assert record["context"]["run_fingerprint"] is not None
    assert (
        record["context"]["compatibility_id"] == core.compatibility_descriptor()["compatibility_id"]
    )
    assert record["core_measurement"] is None
    assert record["provenance"]["failure_code"] == "CSV-NEXT-TARGET-001"
    assert record["provenance"]["observed"]["budget"] == {"state": "unobserved", "value": None}
    validate_request_bound_run_decision_v2(record, owner)


def test_run_v2_proof_backed_partial_safe_preserves_payload_and_exit_three(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = core_inputs(tmp_path)
    model, proof = wire["semantic_payload"]["model"], wire["semantic_payload"]["proof"]
    failure_id = "next:failure:" + "1" * 64
    proof["discovered_records"].append(
        {
            "collection": "components",
            "record_id": CARD_COMPONENT_ID,
            "taints": ["type_symbol"],
            "record": {
                "kind": "component",
                "id": CARD_COMPONENT_ID,
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
            "record_ids": [CARD_COMPONENT_ID],
        }
    ]
    proof["causal_edges"] = [
        {"source_id": failure_id, "record_id": CARD_COMPONENT_ID, "rule": "type_subtree"}
    ]
    proof["excluded"] = [
        {"collection": "components", "record_id": CARD_COMPONENT_ID, "reason": "tainted"}
    ]
    model["coverage"].update(affected_ids=[CARD_COMPONENT_ID], taint_frontier=[CARD_MODULE_ID])
    model["coverage"]["counts"].update(discovered=8, excluded=1)
    model["diagnostics"] = [
        {
            "code": "CSV-NEXT-TYPE-001",
            "severity": "warning",
            "recoverable": True,
            "outcome": "partial_safe",
            "ref_permission": "symbol",
            "path_ref": None,
            "symbol_ref": CARD_COMPONENT_ID,
            "count": 1,
        }
    ]
    update_model_digest(wire)
    runtime = runtime_for_core_wire(seal, assets, request, policy, wire)
    candidate = runtime.transport_candidate()
    assert candidate is not None
    core = runtime_reference.decide_semantic_candidate_v2(candidate, seal, assets)
    assert core.gate()["outcome"] == "partial_safe"
    owner = run_reference.retain_request_bound_run_decision_v2(runtime, semantic_decision=core)
    record = owner.record()
    assert (
        record["kind"],
        record["status"],
        record["outcome"],
        record["payload_available"],
        record["exit_code"],
    ) == (
        "request_bound_success",
        "incomplete",
        "partial_safe",
        True,
        3,
    )
    assert record["core_measurement"] == {"kind": "entity_budget", "actual": 1, "limit": 500}
    validate_request_bound_run_decision_v2(record, owner)


def test_run_v2_typed_core_rejection_keeps_transport_fingerprint_not_admitted_suffix(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy, wire = core_inputs(tmp_path)
    wire["semantic_payload"]["model_digest"] = "0" * 64
    runtime = runtime_for_core_wire(seal, assets, request, policy, wire)
    candidate = runtime.transport_candidate()
    assert candidate is not None
    core = runtime_reference.inspect_semantic_candidate_v2(candidate, seal, assets)
    assert type(core) is runtime_reference.RejectedSemanticDecisionV2
    owner = run_reference.retain_request_bound_run_decision_v2(runtime, semantic_decision=core)
    record = owner.record()
    assert record["context"]["run_fingerprint"] == (
        "066d76ba2cfbae97b137a7a1bd59a4181dee2c0ccf31f5c013a9a1735dc8c56e"
    )
    assert record["context"]["compatibility_id"] is None
    assert record["core_measurement"] is None
    assert (record["provenance"]["stage"], record["provenance"]["failure_code"]) == (
        "response_validation",
        "CSV-NEXT-PROTOCOL-001",
    )
    assert all(
        record["provenance"]["observed"][key] == {"state": "unobserved", "value": None}
        for key in ("semantic_payload", "compatibility", "model", "budget")
    )
    validate_request_bound_run_decision_v2(record, owner)


def test_run_v2_model_record_plus_one_is_not_an_entity_measurement(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = model_record_inputs(tmp_path, 1)
    runtime = runtime_for_core_wire(seal, assets, request, policy, wire)
    candidate = runtime.transport_candidate()
    assert candidate is not None
    core = runtime_reference.inspect_semantic_candidate_v2(candidate, seal, assets)
    assert isinstance(core, runtime_reference.RejectedSemanticDecisionV2)
    assert core.failure()["model_records"] == 10_001
    owner = run_reference.retain_request_bound_run_decision_v2(runtime, semantic_decision=core)
    record = owner.record()
    assert record["core_measurement"] == {
        "kind": "model_record_limit",
        "actual": 10_001,
        "limit": 10_000,
    }
    assert record["provenance"]["stage"] == "model_validation"
    assert record["provenance"]["failure_code"] == "CSV-NEXT-LIMIT-005"
    assert record["provenance"]["observed"]["budget"]["state"] == "unobserved"
    validate_request_bound_run_decision_v2(record, owner)


@pytest.mark.parametrize("cause", ["stage_failed", "spawn_failed"])
def test_run_v2_pre_spawn_failure_has_no_fake_fingerprint_response_or_semantic_suffix(
    tmp_path: Path, cause: str
) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    evidence = complete_evidence(policy)
    evidence.update(spawn=None, capture=None, response=None, exit_code=None, terminal_cause=cause)
    evidence["cleanup"]["direct_child_waited"] = False
    observation = runtime_reference.reference_process_observation_v2(policy, evidence)
    runtime = runtime_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, None
    )
    owner = run_reference.retain_request_bound_run_decision_v2(runtime)
    record = owner.record()
    assert owner.semantic_decision() is None
    assert (record["kind"], record["outcome"], record["exit_code"]) == (
        "request_bound_failure",
        "payload_unavailable",
        3,
    )
    assert record["context"]["run_fingerprint"] is None
    assert record["context"]["compatibility_id"] is None
    assert record["response"] is None
    assert record["core_measurement"] is None
    assert (record["provenance"]["stage"], record["provenance"]["failure_code"]) == (
        "node_spawn",
        "CSV-NEXT-NODE-002",
    )
    assert all(
        record["provenance"]["observed"][key]["state"] == "unobserved"
        for key in (
            "process_start",
            "node_version",
            "control_response",
            "semantic_payload",
            "compatibility",
            "model",
            "budget",
        )
    )
    validate_request_bound_run_decision_v2(record, owner)


def test_run_v2_validator_rejects_a_foreign_cached_record_even_with_valid_projection(
    complete_run_owner: run_reference.RetainedRequestBoundRunDecisionV2,
) -> None:
    owner = copy(complete_run_owner)
    original = owner.record()
    foreign = deepcopy(original)
    foreign["context"]["run_fingerprint"] = "0" * 64
    # Malformed conformance input only, not an API or hostile same-UID claim.
    object.__setattr__(
        owner, "_record_bytes", json.dumps(foreign, sort_keys=True, separators=(",", ":")).encode()
    )
    with pytest.raises(ValueError, match="retained record"):
        validate_request_bound_run_decision_v2(original, owner)


def aligned_bad_cache(
    owner: run_reference.RetainedRequestBoundRunDecisionV2, value: dict[str, Any]
) -> run_reference.RetainedRequestBoundRunDecisionV2:
    """Malformed conformance owner: agreement with a producer cache must not suffice."""

    clone = copy(owner)
    object.__setattr__(
        clone,
        "_record_bytes",
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(),
    )
    return clone


@pytest.mark.parametrize("field", RUN_PREIMAGE_FIELDS)
def test_run_v2_independently_rejects_each_rehashed_fingerprint_field(
    complete_run_owner: run_reference.RetainedRequestBoundRunDecisionV2, field: str
) -> None:
    value = complete_run_owner.record()
    preimage = json.loads(
        (ROOT / "tests/fixtures/next_runtime_v2/public-semantic-run-preimage.json").read_text()
    )
    preimage[field] = {"foreign": preimage[field]}
    value["context"]["run_fingerprint"] = independent_ascii_hash(preimage)
    _validate_schema("next-run-decision-v2", value)
    with pytest.raises(ValueError, match="13-key owner-derived"):
        validate_request_bound_run_decision_v2(value, aligned_bad_cache(complete_run_owner, value))


@pytest.mark.parametrize("slot", runtime_reference.PROVENANCE_SLOTS_V2)
def test_run_v2_independently_rejects_every_rehashed_observation_even_with_matching_alias_and_cache(
    complete_run_owner: run_reference.RetainedRequestBoundRunDecisionV2, slot: str
) -> None:
    value = complete_run_owner.record()
    value["provenance"]["observed"][slot]["value"]["sha256"] = independent_ascii_hash(
        {"foreign": slot}
    )
    value["context"]["observed_prefix"] = deepcopy(value["provenance"]["observed"])
    _validate_schema("next-run-decision-v2", value)
    with pytest.raises(ValueError, match="observation digest differs"):
        validate_request_bound_run_decision_v2(value, aligned_bad_cache(complete_run_owner, value))


@pytest.mark.parametrize(
    "field",
    [
        "request_id",
        "domain_config_digest",
        "source_plan_digest",
        "source_view_fingerprint",
        "compatibility_id",
        "analysis_intent",
        "run_context",
        "observed_prefix",
    ],
)
def test_run_v2_rejects_foreign_parent_context(
    complete_run_owner: run_reference.RetainedRequestBoundRunDecisionV2, field: str
) -> None:
    value = complete_run_owner.record()
    context = value["context"]
    if field == "analysis_intent":
        context[field]["upstream_depth"] += 1
    elif field == "run_context":
        context[field]["stdout_selector"] = "manifest"
    elif field == "observed_prefix":
        context[field]["request"]["value"]["sha256"] = "0" * 64
    else:
        context[field] = "0" * 64
    _validate_schema("next-run-decision-v2", value)
    with pytest.raises(ValueError):
        validate_request_bound_run_decision_v2(value, aligned_bad_cache(complete_run_owner, value))


@pytest.mark.parametrize(
    ("surface", "field"),
    [
        ("request", "raw_sha256"),
        ("request", "byte_length"),
        ("request", "request_id"),
        ("response", "raw_sha256"),
        ("response", "byte_length"),
        ("response", "canonical_json"),
        ("core_measurement", "actual"),
        ("core_measurement", "limit"),
    ],
)
def test_run_v2_rejects_schema_valid_descriptor_or_measurement_substitution(
    complete_run_owner: run_reference.RetainedRequestBoundRunDecisionV2, surface: str, field: str
) -> None:
    value = complete_run_owner.record()
    if field in {"raw_sha256", "request_id"}:
        value[surface][field] = "0" * 64
    elif field == "canonical_json":
        value[surface][field] = not value[surface][field]
    else:
        value[surface][field] += 1
    _validate_schema("next-run-decision-v2", value)
    with pytest.raises(ValueError):
        validate_request_bound_run_decision_v2(value, aligned_bad_cache(complete_run_owner, value))


def test_run_v2_nominal_constructor_frozen_private_repr_and_fresh_projection(
    complete_run_owner: run_reference.RetainedRequestBoundRunDecisionV2,
) -> None:
    owner = complete_run_owner
    with pytest.raises(TypeError):
        run_reference.RetainedRequestBoundRunDecisionV2(
            owner.runtime_result(), owner.semantic_decision()
        )
    with pytest.raises(FrozenInstanceError):
        owner._record_bytes = b"{}"  # type: ignore[misc]
    assert repr(owner) == "RetainedRequestBoundRunDecisionV2()"
    value = run_reference.project_request_bound_run_decision_v2(owner)
    value["context"]["run_fingerprint"] = "0" * 64
    assert (
        owner.record()["context"]["run_fingerprint"]
        == "066d76ba2cfbae97b137a7a1bd59a4181dee2c0ccf31f5c013a9a1735dc8c56e"
    )
    with pytest.raises(TypeError):
        run_reference.project_request_bound_run_decision_v2(SimpleNamespace(record=owner.record))  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        validate_request_bound_run_decision_v2(
            owner.record(),
            SimpleNamespace(runtime_result=owner.runtime_result),  # type: ignore[arg-type]
        )


def test_run_v2_rejects_equal_content_core_from_another_exchange(
    complete_run_owner: run_reference.RetainedRequestBoundRunDecisionV2,
) -> None:
    original = complete_run_owner.runtime_result()
    candidate = original.transport_candidate()
    assert candidate is not None
    other = runtime_reference.retain_runtime_result_v2(
        original.source_seal(),
        original.execution_assets(),
        original.request_frame(),
        original.policy(),
        original.observation(),
        candidate.response_frame(),
    )
    assert other is not original and other.transport_candidate() is not candidate
    with pytest.raises(ValueError, match="same runtime owner"):
        run_reference.retain_request_bound_run_decision_v2(
            other, semantic_decision=complete_run_owner.semantic_decision()
        )
    malformed = copy(complete_run_owner)
    object.__setattr__(malformed, "_runtime", other)
    with pytest.raises(ValueError, match="same runtime owner"):
        validate_request_bound_run_decision_v2(malformed.record(), malformed)


def test_run_v2_success_requires_core_and_rejects_duck_core(
    complete_run_owner: run_reference.RetainedRequestBoundRunDecisionV2,
) -> None:
    with pytest.raises(ValueError, match="matching Core"):
        run_reference.retain_request_bound_run_decision_v2(complete_run_owner.runtime_result())
    with pytest.raises(TypeError, match="nominal Core"):
        run_reference.retain_request_bound_run_decision_v2(
            complete_run_owner.runtime_result(),
            semantic_decision=SimpleNamespace(gate=lambda: {}),  # type: ignore[arg-type]
        )


def test_run_v2_failure_receipt_does_not_reopen_a_disposed_frame_or_mint_binding(
    tmp_path: Path,
) -> None:
    runtime, frame = protocol_runtime(tmp_path)
    object.__setattr__(frame, "raw_bytes", b"discarded original input; not retained by the result")
    owner = run_reference.retain_request_bound_run_decision_v2(runtime)
    value = owner.record()
    assert value["context"]["run_fingerprint"] is None
    assert value["context"]["compatibility_id"] is None
    assert value["response"] == {
        "raw_sha256": "39f69e2d4585d53c3ff3ac4db463beba675bf4fa908b6f984f08927631150a25",
        "byte_length": 263,
        "canonical_json": False,
    }
    assert value["provenance"]["observed"]["node_version"]["state"] == "unobserved"
    assert (
        value["provenance"]["observed"]["control_response"]["value"]["sha256"]
        == "6edadd2c0fcf54ca5477efc71e258580b669f26d92e2767fc5032d3af4f601d3"
    )
    validate_request_bound_run_decision_v2(value, owner)


@pytest.mark.parametrize("branch", ["empty", "export", "entity"])
def test_run_v2_distinguishes_actual_empty_export_and_entity_measurements(
    tmp_path: Path, branch: str
) -> None:
    if branch == "empty":
        seal, assets, request, policy, wire = core_inputs(tmp_path, empty_membership=True)
    elif branch == "export":
        seal, assets, request, policy, wire = core_inputs(tmp_path, corpus="string-unknown")
    else:
        seal, assets, request, policy, wire = core_inputs(tmp_path, max_entities=1)
        model = wire["semantic_payload"]["model"]
        model["components"] = [
            {
                "kind": "component",
                "id": CARD_COMPONENT_ID,
                "module_id": CARD_MODULE_ID,
                "declaration_key": "Card",
                "recognition_evidence": ["trusted_callable"],
                "props_state": "no_props",
            }
        ]
        model["coverage"]["counts"].update(
            components=1, internal_entities=2, published=8, discovered=8
        )
        wire["semantic_payload"]["proof"]["discovered_records"] = [
            {"collection": name, "record_id": row["id"], "taints": []}
            for name in (
                "projects",
                "files",
                "modules",
                "components",
                "members",
                "relations",
                "facts",
            )
            for row in model[name]
        ]
        update_model_digest(wire)
    runtime = runtime_for_core_wire(seal, assets, request, policy, wire)
    candidate = runtime.transport_candidate()
    assert candidate is not None
    core = runtime_reference.decide_semantic_candidate_v2(candidate, seal, assets)
    owner = run_reference.retain_request_bound_run_decision_v2(runtime, semantic_decision=core)
    value = owner.record()
    if branch == "empty":
        assert (value["outcome"], value["exit_code"]) == ("complete", 0)
        assert value["core_measurement"] == {"kind": "entity_budget", "actual": 0, "limit": 500}
    elif branch == "export":
        assert value["provenance"]["failure_code"] == "CSV-NEXT-EXPORT-001"
        assert value["core_measurement"] is None
    else:
        assert value["provenance"]["failure_code"] == "CSV-NEXT-LIMIT-005"
        assert value["core_measurement"] == {"kind": "entity_budget", "actual": 2, "limit": 1}
    validate_request_bound_run_decision_v2(value, owner)


def test_run_v2_measurement_rejects_float_even_when_it_equals_the_integer(
    complete_run_owner: run_reference.RetainedRequestBoundRunDecisionV2,
) -> None:
    value = complete_run_owner.record()
    value["core_measurement"]["actual"] = 1.0
    _validate_schema("next-run-decision-v2", value)
    with pytest.raises(ValueError):
        validate_request_bound_run_decision_v2(value, aligned_bad_cache(complete_run_owner, value))


def test_run_v2_request_descriptor_requires_the_actual_integer_byte_length(
    complete_run_owner: run_reference.RetainedRequestBoundRunDecisionV2,
) -> None:
    value = complete_run_owner.record()
    value["request"]["byte_length"] = float(value["request"]["byte_length"])
    _validate_schema("next-run-decision-v2", value)
    with pytest.raises(ValueError):
        validate_request_bound_run_decision_v2(value, aligned_bad_cache(complete_run_owner, value))


def test_run_v2_response_receipt_requires_the_actual_integer_byte_length(
    complete_run_owner: run_reference.RetainedRequestBoundRunDecisionV2,
) -> None:
    value = complete_run_owner.record()
    value["response"]["byte_length"] = float(value["response"]["byte_length"])
    _validate_schema("next-run-decision-v2", value)
    with pytest.raises(ValueError):
        validate_request_bound_run_decision_v2(value, aligned_bad_cache(complete_run_owner, value))


@pytest.mark.parametrize(
    ("surface", "field"),
    [
        ("analysis_intent", "upstream_depth"),
        ("analysis_intent", "downstream_depth"),
        ("run_context", "budget_resolved"),
    ],
)
def test_run_v2_context_preserves_integer_intent_and_budget(
    complete_run_owner: run_reference.RetainedRequestBoundRunDecisionV2, surface: str, field: str
) -> None:
    value = complete_run_owner.record()
    value["context"][surface][field] = float(value["context"][surface][field])
    _validate_schema("next-run-decision-v2", value)
    with pytest.raises(ValueError):
        validate_request_bound_run_decision_v2(value, aligned_bad_cache(complete_run_owner, value))


@pytest.mark.parametrize("field", ["version", "exit_code"])
def test_run_v2_fixed_integer_fields_do_not_accept_float_equivalence(
    complete_run_owner: run_reference.RetainedRequestBoundRunDecisionV2, field: str
) -> None:
    value = complete_run_owner.record()
    value[field] = float(value[field])
    _validate_schema("next-run-decision-v2", value)
    with pytest.raises(ValueError):
        validate_request_bound_run_decision_v2(value, aligned_bad_cache(complete_run_owner, value))


def test_run_v2_observation_descriptors_preserve_integer_versions(
    complete_run_owner: run_reference.RetainedRequestBoundRunDecisionV2,
) -> None:
    value = complete_run_owner.record()
    value["provenance"]["observed"]["request"]["value"]["version"] = 2.0
    value["context"]["observed_prefix"] = deepcopy(value["provenance"]["observed"])
    _validate_schema("next-run-decision-v2", value)
    with pytest.raises(ValueError):
        validate_request_bound_run_decision_v2(value, aligned_bad_cache(complete_run_owner, value))


def test_run_v2_observed_prefix_is_an_exact_json_alias(
    complete_run_owner: run_reference.RetainedRequestBoundRunDecisionV2,
) -> None:
    value = complete_run_owner.record()
    value["context"]["observed_prefix"]["request"]["value"]["version"] = 2.0
    _validate_schema("next-run-decision-v2", value)
    with pytest.raises(ValueError):
        validate_request_bound_run_decision_v2(value, aligned_bad_cache(complete_run_owner, value))


@pytest.mark.parametrize(
    ("kind", "exit_code", "stage", "version"),
    [
        ("protocol_failure", 65, "response_protocol", None),
        ("bootstrap_failure", 67, "bootstrap", None),
        ("semantic_failure", 68, "semantic_analysis", "22.10.0"),
        ("unsupported_runtime", 66, "runtime_validation", "20.19.0"),
    ],
)
def test_run_v2_closed_child_failure_uses_receipt_not_fake_binding(
    tmp_path: Path, kind: str, exit_code: int, stage: str, version: str | None
) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    wire = shape_wire(request)
    wire["control"].update(
        result_kind=kind,
        runtime=None
        if version is None
        else {
            "engine": "node",
            "version_raw": version,
            "version": version,
            "eligibility": "unsupported" if kind == "unsupported_runtime" else "supported",
            "observation_source": "process.versions.node",
        },
    )
    if version is None:
        wire["control"]["binding"] = {"state": "unbound", "request_id": None}
    wire["semantic_payload"] = None
    frame = runtime_reference.retain_response_frame_v2(
        json.dumps(wire).encode() + b"\n", limits=request.record()["limits"]
    )
    evidence = exchange_evidence(policy, request, frame)
    evidence["exit_code"] = exit_code
    observation = runtime_reference.reference_process_observation_v2(policy, evidence)
    runtime = runtime_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, frame
    )
    owner = run_reference.retain_request_bound_run_decision_v2(runtime)
    value = owner.record()
    assert value["provenance"]["stage"] == stage
    assert value["context"]["run_fingerprint"] is None
    assert value["context"]["compatibility_id"] is None
    assert value["response"]["raw_sha256"] == hashlib.sha256(frame.raw_bytes).hexdigest()
    assert value["response"]["canonical_json"] is False
    assert (value["provenance"]["observed"]["node_version"]["state"] == "observed") is (
        version is not None
    )
    validate_request_bound_run_decision_v2(value, owner)


@pytest.mark.parametrize(
    "cause",
    [
        "cleanup_unverified",
        "candidate_drift",
        "assets_drift",
        "binding_mismatch",
        "response_invalid",
        "exit_mismatch",
    ],
)
def test_run_v2_complete_frame_late_failure_keeps_descriptor_without_core_authority(
    tmp_path: Path, cause: str
) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    wire = shape_wire(request)
    if cause == "binding_mismatch":
        wire["control"]["binding"]["request_id"] = "0" * 64
    elif cause == "response_invalid":
        wire["semantic_payload"]["run_context"]["stdout_selector"] = "manifest"
    frame = runtime_reference.retain_response_frame_v2(
        json.dumps(wire).encode(), limits=request.record()["limits"]
    )
    evidence = exchange_evidence(policy, request, frame)
    evidence["terminal_cause"] = cause
    evidence["capture"]["stdout_retained_bytes"] = 0
    if cause == "cleanup_unverified":
        evidence["cleanup"]["private_root_removed"] = False
    elif cause in {"candidate_drift", "assets_drift"}:
        evidence[cause.removesuffix("_drift") + "_check"] = "drift"
    elif cause == "exit_mismatch":
        evidence["exit_code"] = 65
    observation = runtime_reference.reference_process_observation_v2(policy, evidence)
    runtime = runtime_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, frame
    )
    owner = run_reference.retain_request_bound_run_decision_v2(runtime)
    value = owner.record()
    assert value["response"] is not None
    assert value["context"]["run_fingerprint"] is None
    assert value["provenance"]["observed"]["control_response"]["state"] == "observed"
    assert all(
        value["provenance"]["observed"][key]["state"] == "unobserved"
        for key in ("semantic_payload", "compatibility", "model", "budget")
    )
    validate_request_bound_run_decision_v2(value, owner)


@pytest.mark.parametrize(
    ("cause", "with_control", "stage", "code"),
    [
        ("write_failed", False, "node_process", "CSV-NEXT-NODE-004"),
        ("read_failed", False, "node_process", "CSV-NEXT-NODE-004"),
        ("timeout", False, "node_timeout", "CSV-NEXT-NODE-003"),
        ("timeout", True, "node_timeout", "CSV-NEXT-NODE-003"),
        ("stdout_limit", False, "adapter_stdout_capture", "CSV-NEXT-LIMIT-003"),
        ("stderr_limit", False, "adapter_stderr_capture", "CSV-NEXT-LIMIT-003"),
        ("stderr_limit", True, "adapter_stderr_capture", "CSV-NEXT-LIMIT-003"),
    ],
)
def test_run_v2_post_spawn_failure_uses_actual_control_presence_not_stage(
    tmp_path: Path, cause: str, with_control: bool, stage: str, code: str
) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    frame = (
        runtime_reference.retain_response_frame_v2(
            json.dumps(shape_wire(request)).encode(), limits=request.record()["limits"]
        )
        if with_control
        else None
    )
    evidence = (
        exchange_evidence(policy, request, frame)
        if frame is not None
        else complete_evidence(policy)
    )
    evidence.update(terminal_cause=cause, exit_code=-15)
    if frame is None:
        evidence["response"] = None
    evidence["capture"].update(
        stdin_bytes=len(request.canonical_bytes),
        stdin_sent_bytes=1 if cause == "write_failed" else len(request.canonical_bytes),
        stdout_bytes=len(frame.raw_bytes) if frame is not None else 0,
        stdout_retained_bytes=0,
        stdout_eof=frame is not None,
        stderr_retained_bytes=0,
    )
    if cause in {"stdout_limit", "stderr_limit"}:
        stream = cause.removesuffix("_limit")
        evidence["capture"][stream + "_bytes"] = (
            request.record()["limits"]["max_adapter_" + stream + "_capture_bytes"] + 1
        )
        evidence["capture"][stream + "_eof"] = False
    evidence["cleanup"].update(group_stop="verified", signals=["TERM"])
    observation = runtime_reference.reference_process_observation_v2(policy, evidence)
    runtime = runtime_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, frame
    )
    owner = run_reference.retain_request_bound_run_decision_v2(runtime)
    value = owner.record()
    assert (value["provenance"]["stage"], value["provenance"]["failure_code"]) == (stage, code)
    assert (value["response"] is not None) is with_control
    assert (value["provenance"]["observed"]["node_version"]["state"] == "observed") is with_control
    assert value["context"]["run_fingerprint"] is None
    validate_request_bound_run_decision_v2(value, owner)


@pytest.mark.parametrize(
    ("raw", "stage", "code"),
    [
        (b'{"control":', "response_decode", "CSV-NEXT-PROTOCOL-001"),
        (b'{"schema":"unknown"}', "response_schema", "CSV-NEXT-PROTOCOL-001"),
        (b'{"x":1,"x":2}', "response_decode", "CSV-NEXT-PROTOCOL-001"),
        (
            b'{"deep":' + b"[" * 64 + b"0" + b"]" * 64 + b"}",
            "response_decode",
            "CSV-NEXT-LIMIT-003",
        ),
    ],
)
def test_run_v2_decoder_rejection_is_not_a_complete_response_descriptor(
    tmp_path: Path, raw: bytes, stage: str, code: str
) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    rejected = runtime_reference.inspect_response_frame_v2(raw, limits=request.record()["limits"])
    assert isinstance(rejected, runtime_reference.RejectedResponseFrameV2)
    evidence = complete_evidence(policy)
    evidence.update(response=None, terminal_cause="frame_invalid")
    evidence["capture"].update(
        stdin_bytes=len(request.canonical_bytes),
        stdin_sent_bytes=len(request.canonical_bytes),
        stdout_bytes=len(raw),
        stdout_retained_bytes=0,
    )
    observation = runtime_reference.reference_process_observation_v2(policy, evidence)
    runtime = runtime_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, rejected
    )
    owner = run_reference.retain_request_bound_run_decision_v2(runtime)
    value = owner.record()
    assert value["response"] is None
    assert (value["provenance"]["stage"], value["provenance"]["failure_code"]) == (stage, code)
    assert value["provenance"]["observed"]["control_response"]["state"] == "unobserved"
    validate_request_bound_run_decision_v2(value, owner)


def test_run_v2_failure_refuses_core_and_interrupt_has_no_ordinary_run_record(
    tmp_path: Path, complete_run_owner: run_reference.RetainedRequestBoundRunDecisionV2
) -> None:
    (tmp_path / "failure").mkdir()
    (tmp_path / "interrupt").mkdir()
    runtime, _frame = protocol_runtime(tmp_path / "failure")
    with pytest.raises(ValueError, match="failure cannot carry"):
        run_reference.retain_request_bound_run_decision_v2(
            runtime, semantic_decision=complete_run_owner.semantic_decision()
        )
    seal, assets, request, policy = request_inputs(tmp_path / "interrupt")
    evidence = complete_evidence(policy)
    evidence.update(
        spawn=None, capture=None, response=None, exit_code=None, terminal_cause="interrupted"
    )
    evidence["cleanup"]["direct_child_waited"] = False
    observation = runtime_reference.reference_process_observation_v2(policy, evidence)
    interrupt = runtime_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, None
    )
    with pytest.raises(ValueError, match="interrupt"):
        run_reference.retain_request_bound_run_decision_v2(interrupt)


@pytest.mark.parametrize("surface", ["root", "context", "request", "response", "core_measurement"])
@pytest.mark.parametrize(
    "field",
    [
        "semantic_payload",
        "proof",
        "content_base64",
        "absolute_path",
        "pid",
        "spawn_parameters",
        "receipt_id",
        "validated",
    ],
)
def test_run_v2_nested_surfaces_are_closed_against_private_or_invented_proof_fields(
    complete_run_owner: run_reference.RetainedRequestBoundRunDecisionV2, surface: str, field: str
) -> None:
    value = complete_run_owner.record()
    target = value if surface == "root" else value[surface]
    target[field] = "private"
    with pytest.raises(ValidationError):
        _validate_schema("next-run-decision-v2", value)


@pytest.mark.parametrize(
    "kind",
    [
        "request_independent_failure",
        "request_independent_not_applicable",
        "fatal",
        "usage",
        "interrupted",
    ],
)
def test_run_v2_has_no_shape_only_future_or_terminal_branch(kind: str) -> None:
    value = complete_shape()
    value["kind"] = kind
    with pytest.raises(ValidationError):
        _validate_schema("next-run-decision-v2", value)


@pytest.mark.parametrize("code", ["CSV-NEXT-ASSET-001", "CSV-NEXT-ASSET-002"])
def test_run_v2_does_not_preempt_unadopted_asset_policy(code: str) -> None:
    fixture = ROOT / "tests/fixtures/next_runtime_v2/run-decision-pre-spawn-failure.json"
    value = json.loads(fixture.read_text())
    _validate_schema("next-run-decision-v2", value)
    value["provenance"]["failure_code"] = code
    with pytest.raises(ValidationError):
        _validate_schema("next-run-decision-v2", value)


def test_run_v2_refs_and_branch_shapes_are_exact_without_old_whole_runtime_fallback() -> None:
    schema = json.loads((ROOT / "schemas/next-run-decision-v2.schema.json").read_text())
    refs: set[str] = set()
    pending: list[Any] = [schema]
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            if "$ref" in value:
                refs.add(value["$ref"])
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
    assert len(schema["oneOf"]) == 5
    assert "urn:code-structure-viz:schema:next-provenance-v2" in refs
    assert all(
        "next-provenance-v1" not in ref
        and "next-run-decision-v1" not in ref
        and "next-process" not in ref
        for ref in refs
    )


def known_run_inputs(
    tmp_path: Path, case: str
) -> tuple[
    runtime_reference.RetainedRuntimeResultV2,
    runtime_reference.ValidatedSemanticDecisionV2
    | runtime_reference.RejectedSemanticDecisionV2
    | None,
    bytes | None,
]:
    """Fixed corpus input assembly; never call a run/provenance producer here."""

    tmp_path.mkdir(exist_ok=True)
    if case == "complete":
        runtime, core = complete_core_runtime(tmp_path)
        candidate = runtime.transport_candidate()
        assert candidate is not None
        return runtime, core, candidate.response_frame().raw_bytes
    if case == "core-rejected":
        seal, assets, request, policy, wire = core_inputs(tmp_path)
        wire["semantic_payload"]["model_digest"] = "0" * 64
        runtime = runtime_for_core_wire(seal, assets, request, policy, wire)
        candidate = runtime.transport_candidate()
        assert candidate is not None
        return (
            runtime,
            runtime_reference.inspect_semantic_candidate_v2(candidate, seal, assets),
            candidate.response_frame().raw_bytes,
        )
    assert case == "pre-spawn-failure"
    seal, assets, request, policy = request_inputs(tmp_path)
    evidence = complete_evidence(policy)
    evidence.update(
        spawn=None, capture=None, response=None, exit_code=None, terminal_cause="spawn_failed"
    )
    evidence["cleanup"]["direct_child_waited"] = False
    observation = runtime_reference.reference_process_observation_v2(policy, evidence)
    return (
        runtime_reference.retain_runtime_result_v2(
            seal, assets, request, policy, observation, None
        ),
        None,
        None,
    )


def independent_ascii_run_literal(
    runtime: runtime_reference.RetainedRuntimeResultV2,
    core: runtime_reference.ValidatedSemanticDecisionV2
    | runtime_reference.RejectedSemanticDecisionV2
    | None,
    raw: bytes | None,
    *,
    case: str,
) -> dict[str, Any]:
    """Explicit worked ASCII vector, separate from all new record/provenance builders."""

    frame, seal = runtime.request_frame(), runtime.source_seal()
    request, policy = frame.record(), runtime.policy()
    parent, plan = frame.analysis_context(), seal.final_plan
    config = parent.domain_config()
    control = json.loads(raw)["control"] if raw is not None else None
    response = (
        None
        if raw is None
        else {
            "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "byte_length": len(raw),
            "canonical_json": raw
            == json.dumps(
                json.loads(raw), sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode(),
        }
    )
    portable = {
        "producer": policy["producer"],
        "node_candidate": {"sha256": policy["node_candidate"]["sha256"]},
        **{
            key: deepcopy(policy[key])
            for key in (
                "runtime_requirement",
                "execution_asset_set_id",
                "adapter",
                "typescript_identity",
                "trusted_environment_digest",
                "shell",
                "passed_environment",
                "stdio",
                "fd_inheritance",
                "process_group",
                "limits",
            )
        },
        "argv": [
            {"kind": "node_candidate", "sha256": policy["node_candidate"]["sha256"]},
            "--max-old-space-size=512",
            {
                "kind": "execution_member",
                "package_path": "code_structure_viz/_next_runtime/next-adapter.mjs",
            },
        ],
        "cwd": {"kind": "empty_private_directory"},
    }
    if case == "complete":
        assert raw is not None
        payload = json.loads(raw)["semantic_payload"]
    else:
        payload = None
    compatibility = (
        json.loads((ROOT / "tests/fixtures/next_runtime_v2/compatibility.json").read_text())
        if case == "complete"
        else None
    )
    values = {
        "applicability": seal.package_applicability.observation_value(),
        "config": plan["projects"],
        "source": seal.source_view.fingerprint_value(),
        "limits": plan["limits"],
        "source_plan": plan,
        "trusted_environment": request["trusted_type_environment"],
        "runtime_bundle": runtime.execution_assets().descriptor(),
        "node_candidate": {"sha256": policy["node_candidate"]["sha256"]},
        "request": request,
        "launch_policy": portable,
        "process_start": None
        if case == "pre-spawn-failure"
        else {
            "primitive": "subprocess.Popen",
            "parameters": {
                key: portable[key]
                for key in (
                    "argv",
                    "cwd",
                    "shell",
                    "passed_environment",
                    "stdio",
                    "fd_inheritance",
                    "process_group",
                )
            },
        },
        "node_version": control["runtime"] if control is not None else None,
        "control_response": None if control is None else {"control": control, "response": response},
        "semantic_payload": payload,
        "compatibility": compatibility,
        "model": payload["model"] if payload is not None else None,
        "budget": core.gate()
        if isinstance(core, runtime_reference.ValidatedSemanticDecisionV2)
        else None,
    }
    observed = {
        key: {"state": "unobserved", "value": None}
        if value is None
        else {
            "state": "observed",
            "value": {
                "schema": "code-structure-viz.next-observation/v2",
                "version": 2,
                "sha256": independent_ascii_hash(
                    {
                        "schema": "code-structure-viz.next-observation/v2",
                        "version": 2,
                        "field": key,
                        "value": value,
                    }
                ),
            },
        }
        for key, value in values.items()
    }
    kind = "request_bound_success" if case == "complete" else "request_bound_failure"
    stage, code = {
        "complete": (None, None),
        "pre-spawn-failure": ("node_spawn", "CSV-NEXT-NODE-002"),
        "core-rejected": ("response_validation", "CSV-NEXT-PROTOCOL-001"),
    }[case]
    return {
        "schema": "code-structure-viz.next-run-decision/v2",
        "version": 2,
        "kind": kind,
        "status": "complete" if case == "complete" else "incomplete",
        "outcome": "complete" if case == "complete" else "payload_unavailable",
        "request_independent": False,
        "payload_available": case == "complete",
        "exit_code": 0 if case == "complete" else 3,
        "provenance": {
            "schema": "code-structure-viz.next-provenance/v2",
            "kind": kind,
            "stage": stage,
            "failure_code": code,
            "observed": observed,
        },
        "context": {
            "request_id": frame.request_id,
            "run_fingerprint": None
            if case == "pre-spawn-failure"
            else "066d76ba2cfbae97b137a7a1bd59a4181dee2c0ccf31f5c013a9a1735dc8c56e",
            "run_context": parent.run_context(),
            "analysis_intent": parent.analysis_intent(),
            "domain_config_digest": config["domain_config_digest"],
            "source_plan_digest": seal.plan_digest,
            "source_view_fingerprint": seal.source_view_fingerprint,
            "compatibility_id": compatibility["compatibility_id"]
            if compatibility is not None
            else None,
            "observed_prefix": deepcopy(observed),
        },
        "request": {
            "request_id": frame.request_id,
            "raw_sha256": hashlib.sha256(frame.canonical_bytes).hexdigest(),
            "byte_length": len(frame.canonical_bytes),
            "canonical_json": True,
        },
        "response": response,
        "core_measurement": {"kind": "entity_budget", "actual": 1, "limit": 500}
        if case == "complete"
        else None,
    }


@pytest.mark.parametrize(
    ("case", "byte_length", "cj_sha256", "file_sha256"),
    [
        (
            "complete",
            7763,
            "673215084459eee6f9bb8bad68d450af15bd3b3f0ec83cdaea2f14142a4418f1",
            "1371006299668af69f7a04bc0d179ed162f9089a00a2f4dbd640847cbd1bf24f",
        ),
        (
            "pre-spawn-failure",
            5671,
            "b075ae42f25d307d3a7aa3adffcaecc5af7634a90650bc806a526ecc177abfbf",
            "05e6d22d9565a57a938ecff753ddeab71cc3a5bd19eb368f5b8f4216be151017",
        ),
        (
            "core-rejected",
            6644,
            "bae073c0520dbe79823dda41d583626d773071a1dcfe58857b6ed7138af16e6c",
            "ee65f475d92172ddc2b0f8dbf2e3f88182bf897ae7420e13ab67da2adcd17622",
        ),
    ],
)
def test_run_v2_known_literals_are_independent_of_record_and_provenance_producers(
    tmp_path: Path, case: str, byte_length: int, cj_sha256: str, file_sha256: str
) -> None:
    fixture = ROOT / "tests/fixtures/next_runtime_v2" / f"run-decision-{case}.json"
    expected_bytes = fixture.read_bytes()
    expected = json.loads(expected_bytes)
    cj = json.dumps(expected, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    assert len(cj) == byte_length
    assert hashlib.sha256(cj).hexdigest() == cj_sha256
    assert expected_bytes == cj + b"\n"
    assert hashlib.sha256(expected_bytes).hexdigest() == file_sha256
    runtime, core, raw = known_run_inputs(tmp_path, case)
    assert independent_ascii_run_literal(runtime, core, raw, case=case) == expected
    owner = run_reference.retain_request_bound_run_decision_v2(runtime, semantic_decision=core)
    projected = run_reference.project_request_bound_run_decision_v2(owner)
    assert projected == expected
    validate_request_bound_run_decision_v2(expected, owner)
