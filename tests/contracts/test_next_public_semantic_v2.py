"""Public-format records from known Core corpus; not TS/OS/CLI/publication evidence."""

import hashlib
import json
from copy import copy, deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from jsonschema import ValidationError  # type: ignore[import-untyped]

from tests.contracts import next_runtime_v2_reference, next_runtime_v2_validation
from tests.contracts.next_public_semantic_v2_reference import project_public_semantic_document_v2
from tests.contracts.next_public_semantic_v2_validation import (
    validate_public_semantic_document_v2,
    validate_semantic_dispatcher_v2,
)
from tests.contracts.next_reference_validation import canonical_json_bytes, digest
from tests.contracts.test_json_schemas import _next_compatibility_descriptor
from tests.contracts.test_next_semantic_candidate_v2 import (
    CARD_MODULE_ID,
    COLLECTIONS,
    candidate_for,
    core_inputs,
    update_model_digest,
)

CARD_COMPONENT_ID = (
    "next:component:6227b1d19e897d12ed303743051ed58b6fac3fd2b7c64b03175713939d0cc3d9"
)
ROOT = Path(__file__).resolve().parents[2]
KNOWN_PUBLIC_DIR = ROOT / "tests/fixtures/next_runtime_v2"
RUN_PREIMAGE_FIELDS = (
    "source_view_fingerprint",
    "source_plan_digest",
    "domain_config_digest",
    "projects",
    "targets",
    "formats",
    "stdout_selector",
    "limits",
    "node_version",
    "typescript_version",
    "adapter_version",
    "protocol",
    "trusted_environment_digest",
)
OLD_DOMAIN_GOLDENS = sorted(
    path.relative_to(ROOT).as_posix()
    for domain in ("python", "sqlalchemy")
    for path in (ROOT / "tests/golden" / f"{domain}_snapshot").glob("*/*.semantic.json")
)


def independent_ascii_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def nominal_decision(tmp_path: Path) -> next_runtime_v2_reference.ValidatedSemanticDecisionV2:
    seal, assets, request, policy, wire = core_inputs(tmp_path)
    candidate = candidate_for(seal, assets, request, policy, wire)
    return next_runtime_v2_reference.decide_semantic_candidate_v2(candidate, seal, assets)


def independent_public_record(
    decision: next_runtime_v2_reference.ValidatedSemanticDecisionV2,
) -> dict[str, Any]:
    """Explicit test-side projection before the new producer exists, ASCII corpus only."""

    candidate = decision.transport_candidate()
    seal = decision.source_seal()
    request = candidate.request_frame().record()
    context = candidate.request_frame().analysis_context()
    config = context.domain_config()
    run = context.run_context()
    binding = candidate.runtime_binding()
    preimage = {
        "source_view_fingerprint": seal.source_view_fingerprint,
        "source_plan_digest": seal.plan_digest,
        "domain_config_digest": config["domain_config_digest"],
        "projects": request["projects"],
        "targets": request["targets"],
        "formats": run["requested_formats"],
        "stdout_selector": run["stdout_selector"],
        "limits": request["limits"],
        "node_version": binding["node_observation"]["version"],
        "typescript_version": "5.9.2",
        "adapter_version": request["adapter_version"],
        "protocol": "code-structure-viz.next-adapter/v2",
        "trusted_environment_digest": config["trusted_environment_digest"],
    }
    public_request = {
        "schema": "code-structure-viz.next-snapshot-request/v1",
        **{
            key: deepcopy(config[key])
            for key in (
                "projects",
                "targets",
                "upstream_depth",
                "downstream_depth",
                "formats",
                "limits",
                "trusted_environment_digest",
                "source_plan",
                "source_plan_digest",
                "domain_config_digest",
            )
        },
        "run_fingerprint": independent_ascii_hash(preimage),
    }
    payload = candidate.semantic_payload()
    model = payload["model"]
    compatibility = decision.compatibility_descriptor()
    result = {
        "type": "semantic_snapshot",
        "schema": "code-structure-viz.semantic/v2",
        "domain": "next",
        "document_kind": "snapshot",
        "status": "complete",
        "source": {
            "schema": "code-structure-viz.source-view/v1",
            "kind": seal.source_view.kind,
            "head_commit": seal.source_view.head_commit,
            "fingerprint": seal.source_view_fingerprint,
            "file_count": len(seal.source_view.files),
        },
        "request": public_request,
        "identity_versions": deepcopy(payload["identity_versions"]),
        "compatibility_descriptor": compatibility,
        "semantic_compatibility_id": compatibility["compatibility_id"],
        **{
            key: deepcopy(model[key])
            for key in (
                "projects",
                "files",
                "members",
                "relations",
                "facts",
                "coverage",
                "diagnostics",
            )
        },
        "entities": sorted(
            deepcopy(model["modules"] + model["components"]), key=lambda row: row["id"].encode()
        ),
    }
    return result


def test_next_semantic_v2_schema_accepts_nominal_closed_record(tmp_path: Path) -> None:
    record = independent_public_record(nominal_decision(tmp_path))
    next_runtime_v2_validation._validate_schema("next-semantic-v2", record)


def test_semantic_v2_dispatcher_routes_the_new_next_record(tmp_path: Path) -> None:
    record = project_public_semantic_document_v2(nominal_decision(tmp_path))
    validate_semantic_dispatcher_v2(record)


@pytest.mark.parametrize("path", OLD_DOMAIN_GOLDENS)
def test_semantic_v2_dispatcher_preserves_existing_domain_documents(path: str) -> None:
    record = json.loads((ROOT / path).read_text(encoding="utf-8"))
    assert record["domain"] in {"python", "sqlalchemy"}
    assert record["schema"] == "code-structure-viz.semantic/v1"
    validate_semantic_dispatcher_v2(record)


def test_semantic_v2_dispatcher_refuses_old_next_bypass_and_cross_version_mix(
    tmp_path: Path,
) -> None:
    record = project_public_semantic_document_v2(nominal_decision(tmp_path))
    # Shape-only historical record: never assert this is an admitted v2 runtime.
    legacy = deepcopy(record)
    legacy["schema"] = "code-structure-viz.semantic/v1"
    legacy["compatibility_descriptor"] = _next_compatibility_descriptor()
    legacy["semantic_compatibility_id"] = legacy["compatibility_descriptor"]["compatibility_id"]
    next_runtime_v2_validation._validate_schema("next-semantic-v1", legacy)
    next_runtime_v2_validation._validate_schema("semantic-v1", legacy)
    with pytest.raises(ValidationError):
        validate_semantic_dispatcher_v2(legacy)
    for mixed in (
        {**record, "schema": "code-structure-viz.semantic/v1"},
        {**legacy, "schema": "code-structure-viz.semantic/v2"},
        {**record, "domain": "python"},
    ):
        with pytest.raises(ValidationError):
            validate_semantic_dispatcher_v2(mixed)
    with pytest.raises(ValidationError):
        next_runtime_v2_validation._validate_schema("next-semantic-v1", record)


def test_public_semantic_v2_projects_one_nominal_core_decision(tmp_path: Path) -> None:
    decision = nominal_decision(tmp_path)
    record = project_public_semantic_document_v2(decision)
    assert record == independent_public_record(decision)
    validate_public_semantic_document_v2(record, decision)


def test_public_semantic_v2_matches_independent_frozen_literals(tmp_path: Path) -> None:
    decision = nominal_decision(tmp_path)
    expected = json.loads((KNOWN_PUBLIC_DIR / "public-semantic.json").read_text(encoding="utf-8"))
    preimage = json.loads(
        (KNOWN_PUBLIC_DIR / "public-semantic-run-preimage.json").read_text(encoding="utf-8")
    )
    assert set(preimage) == set(RUN_PREIMAGE_FIELDS)
    assert independent_ascii_hash(preimage) == (
        "066d76ba2cfbae97b137a7a1bd59a4181dee2c0ccf31f5c013a9a1735dc8c56e"
    )
    assert independent_ascii_hash(expected) == (
        "d9cd6519d5911be7f043dfcec3ddb96a71cfaaccc11532a74191cedb99b3b13e"
    )
    assert project_public_semantic_document_v2(decision) == expected
    validate_public_semantic_document_v2(expected, decision)


@pytest.mark.parametrize("field", RUN_PREIMAGE_FIELDS)
def test_public_semantic_v2_rejects_each_foreign_fingerprint_preimage_field(
    tmp_path: Path, field: str
) -> None:
    decision = nominal_decision(tmp_path)
    record = project_public_semantic_document_v2(decision)
    preimage = json.loads(
        (KNOWN_PUBLIC_DIR / "public-semantic-run-preimage.json").read_text(encoding="utf-8")
    )
    preimage[field] = {"not_the_retained_value": preimage[field]}
    record["request"]["run_fingerprint"] = independent_ascii_hash(preimage)
    with pytest.raises(ValueError, match="owner-derived preimage"):
        validate_public_semantic_document_v2(record, decision)


@pytest.mark.parametrize("field", ["source", "files", "coverage", "status"])
def test_public_semantic_v2_rejects_schema_valid_foreign_projection(
    tmp_path: Path, field: str
) -> None:
    decision = nominal_decision(tmp_path)
    record = project_public_semantic_document_v2(decision)
    if field == "source":
        record["source"]["fingerprint"] = "0" * 64
    elif field == "files":
        record["files"].reverse()
    elif field == "coverage":
        record["coverage"]["counts"]["published"] += 1
    else:
        record["status"] = "incomplete"
        record["incomplete_kind"] = "partial_safe"
    next_runtime_v2_validation._validate_schema("next-semantic-v2", record)
    with pytest.raises(ValueError, match=f"public {field}"):
        validate_public_semantic_document_v2(record, decision)


@pytest.mark.parametrize("surface", ["source", "request", "entity"])
def test_public_semantic_v2_rejects_nested_private_fields(tmp_path: Path, surface: str) -> None:
    decision = nominal_decision(tmp_path)
    record = project_public_semantic_document_v2(decision)
    target = record["entities"][0] if surface == "entity" else record[surface]
    target["content_base64"] = "cHJpdmF0ZQ=="
    with pytest.raises(ValidationError) as rejected:
        validate_public_semantic_document_v2(record, decision)
    assert list(rejected.value.absolute_path) == (
        ["entities", 0] if surface == "entity" else [surface]
    )


def test_public_semantic_v2_merges_modules_and_components_by_full_id(tmp_path: Path) -> None:
    # Hand-worked model/proof vector: this certifies projection, not TS recognition.
    seal, assets, request, policy, wire = core_inputs(tmp_path)
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
    model["coverage"]["counts"].update(components=1, internal_entities=2, published=8, discovered=8)
    wire["semantic_payload"]["proof"]["discovered_records"] = [
        {"collection": name, "record_id": row["id"], "taints": []}
        for name in COLLECTIONS
        for row in model[name]
    ]
    update_model_digest(wire)
    decision = next_runtime_v2_reference.decide_semantic_candidate_v2(
        candidate_for(seal, assets, request, policy, wire), seal, assets
    )
    record = project_public_semantic_document_v2(decision)
    assert [row["id"] for row in record["entities"]] == [CARD_COMPONENT_ID, CARD_MODULE_ID]
    record["entities"].reverse()
    with pytest.raises(ValueError, match="canonical retained model merge"):
        validate_public_semantic_document_v2(record, decision)


def test_public_semantic_v2_complete_empty_requires_full_source_and_proof(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = core_inputs(tmp_path, empty_membership=True)
    candidate = candidate_for(seal, assets, request, policy, wire)
    decision = next_runtime_v2_reference.decide_semantic_candidate_v2(candidate, seal, assets)
    assert decision.gate()["actual"] == 0
    record = project_public_semantic_document_v2(decision)
    assert record["status"] == "complete"
    assert record["projects"]
    assert record["files"]
    assert all(record[key] == [] for key in ("entities", "members", "relations", "facts"))
    validate_public_semantic_document_v2(record, decision)


def test_public_semantic_v2_preserves_a_proof_backed_safe_subset(tmp_path: Path) -> None:
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
        {
            "source_id": failure_id,
            "record_id": CARD_COMPONENT_ID,
            "rule": "type_subtree",
        }
    ]
    proof["excluded"] = [
        {
            "collection": "components",
            "record_id": CARD_COMPONENT_ID,
            "reason": "tainted",
        }
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
    decision = next_runtime_v2_reference.decide_semantic_candidate_v2(
        candidate_for(seal, assets, request, policy, wire), seal, assets
    )
    assert decision.gate()["outcome"] == "partial_safe"
    record = project_public_semantic_document_v2(decision)
    assert record["status"] == "incomplete"
    assert record["incomplete_kind"] == "partial_safe"
    assert record["coverage"]["affected_ids"] == [CARD_COMPONENT_ID]
    assert record["coverage"]["taint_frontier"] == [CARD_MODULE_ID]
    assert [row["id"] for row in record["entities"]] == [CARD_MODULE_ID]
    assert "proof" not in record
    validate_public_semantic_document_v2(record, decision)


@pytest.mark.parametrize("failure", ["target", "export", "entity"])
def test_public_semantic_v2_refuses_validated_unavailable_without_empty_success(
    tmp_path: Path,
    failure: str,
) -> None:
    seal, assets, request, policy, wire = core_inputs(
        tmp_path,
        targets=["path:src/Card.tsx"] if failure == "target" else [],
        corpus="string-unknown" if failure == "export" else "card",
        max_entities=1 if failure == "entity" else 500,
    )
    model, proof = wire["semantic_payload"]["model"], wire["semantic_payload"]["proof"]
    if failure == "target":
        model["modules"], model["facts"] = [], []
        model["coverage"]["counts"].update(
            modules=0,
            facts=0,
            internal_entities=0,
            published=5,
            discovered=5,
        )
        proof["discovered_records"] = [
            row
            for row in proof["discovered_records"]
            if row["collection"] not in {"modules", "facts"}
        ]
        target = [
            {
                "target_key": "path:src/Card.tsx",
                "status": "failed",
                "record_ids": [],
                "reason": "missing",
            }
        ]
        model["coverage"]["target_completeness"] = target
        proof["target_resolutions"] = deepcopy(target)
    elif failure == "entity":
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
            components=1,
            internal_entities=2,
            published=8,
            discovered=8,
        )
        proof["discovered_records"] = [
            {"collection": collection, "record_id": row["id"], "taints": []}
            for collection in COLLECTIONS
            for row in model[collection]
        ]
    update_model_digest(wire)
    decision = next_runtime_v2_reference.decide_semantic_candidate_v2(
        candidate_for(seal, assets, request, policy, wire), seal, assets
    )
    assert decision.gate()["outcome"] == "payload_unavailable"
    assert decision.gate()["payload_available"] is False
    assert (
        decision.gate()["diagnostic_code"]
        == {
            "target": "CSV-NEXT-TARGET-001",
            "export": "CSV-NEXT-EXPORT-001",
            "entity": "CSV-NEXT-LIMIT-005",
        }[failure]
    )
    with pytest.raises(ValueError, match="available Core"):
        project_public_semantic_document_v2(decision)


def test_public_semantic_v2_rejects_nominal_core_rejection_and_duck_owner(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = core_inputs(tmp_path)
    wire["semantic_payload"]["model_digest"] = "0" * 64
    rejected = next_runtime_v2_reference.inspect_semantic_candidate_v2(
        candidate_for(seal, assets, request, policy, wire), seal, assets
    )
    assert type(rejected) is next_runtime_v2_reference.RejectedSemanticDecisionV2
    for owner in (rejected, SimpleNamespace()):
        with pytest.raises(TypeError, match="Core decision owner"):
            project_public_semantic_document_v2(cast(Any, owner))


def test_public_semantic_v2_is_fresh_and_checks_forged_core_gate(tmp_path: Path) -> None:
    decision = nominal_decision(tmp_path)
    original = project_public_semantic_document_v2(decision)
    changed = project_public_semantic_document_v2(decision)
    changed["request"]["source_plan"]["limits"]["max_entities"] = 1
    changed["entities"].clear()
    assert project_public_semantic_document_v2(decision) == original
    with pytest.raises(ValueError, match="analysis context"):
        validate_public_semantic_document_v2(changed, decision)
    forged = copy(decision)
    gate = decision.gate()
    gate["outcome"] = "partial_safe"
    object.__setattr__(forged, "_gate_bytes", canonical_json_bytes(gate))
    with pytest.raises(ValueError, match="semantic gate"):
        project_public_semantic_document_v2(forged)


@pytest.mark.parametrize("field", ["proof", "content_base64", "request_id", "pid", "cwd"])
def test_public_semantic_v2_rejects_private_root_fields(tmp_path: Path, field: str) -> None:
    decision = nominal_decision(tmp_path)
    record = project_public_semantic_document_v2(decision)
    record[field] = "private data"
    with pytest.raises(ValidationError, match="Additional properties"):
        validate_public_semantic_document_v2(record, decision)


def test_public_semantic_v2_rejects_rehashing_unowned_request_and_compatibility(
    tmp_path: Path,
) -> None:
    decision = nominal_decision(tmp_path)
    record = project_public_semantic_document_v2(decision)
    record["request"]["upstream_depth"] = 2
    record["request"]["run_fingerprint"] = independent_ascii_hash(record["request"])
    with pytest.raises(ValueError, match="analysis context"):
        validate_public_semantic_document_v2(record, decision)
    record = project_public_semantic_document_v2(decision)
    compatibility = record["compatibility_descriptor"]
    compatibility["portable_toolchain_fingerprint"] = "0" * 64
    compatibility["compatibility_id"] = digest(
        {
            key: value
            for key, value in compatibility.items()
            if key not in {"schema", "compatibility_id"}
        }
    )
    record["semantic_compatibility_id"] = compatibility["compatibility_id"]
    with pytest.raises(ValueError, match="compatibility"):
        validate_public_semantic_document_v2(record, decision)
