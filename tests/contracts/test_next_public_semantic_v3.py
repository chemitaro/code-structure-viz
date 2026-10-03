"""Public v3 projection from real retained lower owners, not production execution."""

import hashlib
import json
from copy import deepcopy
from importlib import import_module, util
from pathlib import Path
from typing import Any

import pytest
from jsonschema import ValidationError  # type: ignore[import-untyped]

from tests.contracts import next_public_semantic_v3_validation as validation
from tests.contracts.next_public_semantic_v3_reference import project_public_semantic_document_v3
from tests.contracts.next_reference_validation import (
    COLLECTIONS,
    _derive_required_root_seed_ids,
    derive_required_causal_edges,
)
from tests.contracts.next_semantic_core_v3_reference import (
    ValidatedSemanticDecisionV3,
    decide_semantic_candidate_v3,
)
from tests.contracts.test_next_semantic_candidate_v2 import candidate_for
from tests.contracts.test_next_semantic_core_v3 import (
    FACT_IDS,
    MODULE_IDS,
    SOURCE_BYTES,
    compatibility_preimage_literal_v3,
    core_inputs_v3,
    exclude_value_module_with_root_v3,
    omit_selected_button_module_v3,
    select_literal_button_target_v3,
    simple_multiple_projects_fixture_v3,
)
from tests.contracts.test_next_source_inventory_v3 import exclude_record, refresh_wire


def nominal_decision_v3(tmp_path: Path) -> ValidatedSemanticDecisionV3:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    return decide_semantic_candidate_v3(
        candidate_for(seal, assets, request, policy, wire), seal, assets
    )


def test_available_core_projects_closed_inventory_summary(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    candidate = candidate_for(seal, assets, request, policy, wire)
    decision = decide_semantic_candidate_v3(candidate, seal, assets)
    assert decision.gate()["payload_available"] is True
    assert decision.gate()["outcome"] == "complete"
    assert len(request.record()["files"]) == 6

    # The lower real owners must succeed before observing the missing public seam.
    module = "tests.contracts.next_public_semantic_v3_reference"
    assert util.find_spec(module) is not None, "available Core-v3 has no public projection"
    document = import_module(module).project_public_semantic_document_v3(decision)
    assert document["schema"] == "code-structure-viz.semantic/v3"
    assert document["source_inventory_summary"] == {
        "profile_id": "next-source-inventory-safe-subset-v1",
        "source_partition_fingerprint": (
            "c543f59be0403f3bcf1cf13510f065f6a7e152e555aa394a42960d02a31d6d9f"
        ),
        "acquired": {"projects": 1, "files": 6, "file_bytes": 246},
        "safe": {"projects": 1, "files": 6},
        "proof_only": {"failed_files": 0, "excluded_files": 0},
        "records": {
            "proof_discovered": 17,
            "published": 17,
            "proof_only": 0,
            "accounted": 17,
        },
        "published_entities": {"modules": 3, "components": 1, "total": 4},
    }
    assert document["semantic_compatibility_id"] == (
        "ecf055ae84276a9209e8cb65addabd0cbf4d882e0b76f54cc6f06208fa95880f"
    )


def test_dispatcher_routes_only_current_next_family(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    decision = decide_semantic_candidate_v3(
        candidate_for(seal, assets, request, policy, wire), seal, assets
    )
    document = project_public_semantic_document_v3(decision)
    route = getattr(validation, "validate_semantic_dispatcher_v3", None)
    assert callable(route), "public dispatcher cannot route an admitted Next-v3 document"
    route(document)
    document["schema"] = "code-structure-viz.semantic/v2"
    with pytest.raises(ValidationError):
        route(document)


@pytest.mark.parametrize("kind", ["module_relation", "parse_file", "read_file"])
def test_public_safe_membership_does_not_rewrite_acquired_request(
    tmp_path: Path, kind: str
) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    file_id = exclude_value_module_with_root_v3(wire, request, kind)
    decision = decide_semantic_candidate_v3(
        candidate_for(seal, assets, request, policy, wire), seal, assets
    )
    value = project_public_semantic_document_v3(decision)
    assert value["status"] == "incomplete" and value["incomplete_kind"] == "partial_safe"
    summary = value["source_inventory_summary"]
    assert summary["acquired"] == {"projects": 1, "files": 6, "file_bytes": 246}
    assert summary["safe"] == {"projects": 1, "files": 5}
    assert summary["records"] == {
        "proof_discovered": 17,
        "published": 14,
        "proof_only": 3,
        "accounted": 17,
    }
    assert summary["published_entities"] == {"modules": 2, "components": 1, "total": 3}
    assert summary["proof_only"] == {
        "failed_files": int(kind != "module_relation"),
        "excluded_files": int(kind == "module_relation"),
    }
    assert file_id not in value["projects"][0]["file_ids"]
    assert value["request"]["projects"] == request.analysis_context().domain_config()["projects"]
    assert len(value["source_inventory_summary"]) == 7
    validation.validate_public_semantic_document_v3(value, decision)


@pytest.mark.parametrize(
    "field", ["acquired", "safe", "proof_only", "records", "published_entities"]
)
@pytest.mark.parametrize("wrong", [False, 1.0, -1, "1"])
def test_summary_refuses_non_native_counts(tmp_path: Path, field: str, wrong: object) -> None:
    decision = nominal_decision_v3(tmp_path)
    value = project_public_semantic_document_v3(decision)
    key = next(iter(value["source_inventory_summary"][field]))
    value["source_inventory_summary"][field][key] = wrong
    with pytest.raises((ValueError, ValidationError)):
        validation.validate_public_semantic_document_v3(value, decision)


@pytest.mark.parametrize(
    "field", ["acquired", "safe", "proof_only", "records", "published_entities"]
)
def test_summary_rejects_schema_valid_wrong_counts(tmp_path: Path, field: str) -> None:
    decision = nominal_decision_v3(tmp_path)
    value = project_public_semantic_document_v3(decision)
    key = next(iter(value["source_inventory_summary"][field]))
    value["source_inventory_summary"][field][key] += 1
    with pytest.raises(ValueError, match="inventory summary"):
        validation.validate_public_semantic_document_v3(value, decision)


@pytest.mark.parametrize(
    "field", [None, "acquired", "safe", "proof_only", "records", "published_entities"]
)
def test_summary_is_closed_at_every_object(tmp_path: Path, field: str | None) -> None:
    decision = nominal_decision_v3(tmp_path)
    value = project_public_semantic_document_v3(decision)
    summary = value["source_inventory_summary"]
    target = summary if field is None else summary[field]
    target["source_bytes"] = "private"
    with pytest.raises(ValidationError):
        validation.validate_public_semantic_document_v3(value, decision)


def test_projection_recomputes_partition_and_preserves_returned_tree_isolation(
    tmp_path: Path,
) -> None:
    decision = nominal_decision_v3(tmp_path)
    value = project_public_semantic_document_v3(decision)
    forged = deepcopy(value)
    forged["source_inventory_summary"]["source_partition_fingerprint"] = "0" * 64
    with pytest.raises(ValueError, match="inventory summary"):
        validation.validate_public_semantic_document_v3(forged, decision)
    # Returned trees cannot mutate the actual retained decision.
    value["files"].clear()
    assert len(project_public_semantic_document_v3(decision)["files"]) == 6
    with pytest.raises(TypeError, match="v3 Core decision"):
        project_public_semantic_document_v3({"gate": decision.gate()})  # type: ignore[arg-type]


def test_fourteen_key_ascii_kat_is_new_and_independent_of_actual_fixture() -> None:
    root = Path(__file__).resolve().parents[2]
    preimage = json.loads(
        (root / "tests/fixtures/next_runtime_v3/public-semantic-run-preimage.json").read_text()
    )
    legacy = json.loads(
        (root / "tests/fixtures/next_runtime_v2/public-semantic-run-preimage.json").read_text()
    )
    assert len(preimage) == 14 and len(legacy) == 13
    assert preimage == {
        **legacy,
        "adapter_version": "0.2.0",
        "semantic_admission_profile_id": "next-source-inventory-safe-subset-v1",
    }
    raw = json.dumps(preimage, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    assert (
        hashlib.sha256(raw).hexdigest()
        == "0e7bdc459bf01e9b42e4f416e565c8636b6a5dffde226aeca7beb4deee7207f0"
    )


def test_ten_key_compatibility_hash_uses_the_independent_literal_not_public_counts(
    tmp_path: Path,
) -> None:
    core = nominal_decision_v3(tmp_path)
    preimage = compatibility_preimage_literal_v3()
    assert len(preimage) == 10
    expected = hashlib.sha256(
        json.dumps(preimage, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()
    assert expected == "ecf055ae84276a9209e8cb65addabd0cbf4d882e0b76f54cc6f06208fa95880f"
    assert core.compatibility_descriptor() == {
        **preimage,
        "schema": "code-structure-viz.next-semantic-compatibility/v3",
        "compatibility_id": expected,
    }


@pytest.mark.parametrize("ambient", [False, True])
def test_public_complete_empty_keeps_actual_nonprogram_inventory(
    tmp_path: Path, ambient: bool
) -> None:
    sources = {
        name: content
        for name, content in SOURCE_BYTES.items()
        if name in {"package.json", "tsconfig.json"} or (ambient and name == "src/global.d.ts")
    }
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path, sources=sources)
    payload = wire["semantic_payload"]
    for name in COLLECTIONS:
        if name not in {"projects", "files"}:
            payload["model"][name] = []
    payload["model"]["diagnostics"] = []
    payload["model"]["coverage"]["non_component_value_export_count"] = 0
    payload["proof"] = {key: [] for key in payload["proof"]}
    payload["proof"]["discovered_records"] = [
        {"collection": name, "record_id": row["id"], "taints": []}
        for name in ("projects", "files")
        for row in payload["model"][name]
    ]
    refresh_wire(wire)
    core = decide_semantic_candidate_v3(
        candidate_for(seal, assets, request, policy, wire), seal, assets
    )
    value = project_public_semantic_document_v3(core)
    count = 3 if ambient else 2
    assert value["status"] == "complete" and "incomplete_kind" not in value
    assert value["entities"] == [] and len(value["files"]) == count
    assert value["source_inventory_summary"]["acquired"] == {
        "projects": 1,
        "files": count,
        "file_bytes": 99 if ambient else 54,
    }
    assert value["source_inventory_summary"]["records"] == {
        "proof_discovered": count + 1,
        "published": count + 1,
        "proof_only": 0,
        "accounted": count + 1,
    }


def test_public_selection_only_remains_complete_without_changing_source_inventory(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path, targets=["path:src/button.tsx"])
    file_id = next(row["id"] for row in request.record()["files"] if row["path"] == "src/value.ts")
    for name, record_id in (
        ("modules", MODULE_IDS["src/value.ts"]),
        ("facts", FACT_IDS["src/value.ts"]),
        ("files", file_id),
    ):
        exclude_record(wire, name, record_id, reason="not_selected", taints=[])
    wire["semantic_payload"]["model"]["diagnostics"] = []
    wire["semantic_payload"]["model"]["coverage"]["non_component_value_export_count"] = 0
    select_literal_button_target_v3(wire, request)
    core = decide_semantic_candidate_v3(
        candidate_for(seal, assets, request, policy, wire), seal, assets
    )
    value = project_public_semantic_document_v3(core)
    assert value["status"] == "complete" and "incomplete_kind" not in value
    assert value["source_inventory_summary"]["proof_only"] == {
        "failed_files": 0,
        "excluded_files": 1,
    }
    assert value["source_inventory_summary"]["safe"] == {"projects": 1, "files": 5}
    assert value["request"]["projects"] == request.analysis_context().domain_config()["projects"]
    assert len(request.record()["projects"][0]["file_ids"]) == 6


def test_public_all_private_files_keep_the_project_and_never_become_complete_empty(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    payload = wire["semantic_payload"]
    original = {row["id"]: row for name in COLLECTIONS for row in payload["model"][name]}
    roots = []
    for index, file in enumerate(request.record()["files"]):
        root = {
            "id": "next:failure:" + f"{index + 1:064x}",
            "collection": "files",
            "kind": "parse_file",
            "path_ref": file["path"],
            "record_ids": [],
        }
        root["record_ids"] = _derive_required_root_seed_ids(root, original)
        roots.append(root)
    for name in COLLECTIONS:
        if name != "projects":
            for row in list(payload["model"][name]):
                exclude_record(wire, name, row["id"], reason="tainted", taints=["parse_file"])
    proof = payload["proof"]
    proof["failure_roots"] = roots
    proof["excluded"] = [row for row in proof["excluded"] if row["collection"] != "files"]
    proof["failed"] = [
        {"collection": "files", "record_id": row["id"], "reason": "parse_file"}
        for row in request.record()["files"]
    ]
    full: dict[str, dict[str, dict[str, Any]]] = {name: {} for name in COLLECTIONS}
    for row in proof["discovered_records"]:
        full[row["collection"]][row["record_id"]] = {**row, "record": original[row["record_id"]]}
    proof["causal_edges"] = derive_required_causal_edges(proof, full)
    proof["export_resolution_witness"] = []
    payload["model"]["diagnostics"] = []
    payload["model"]["coverage"]["non_component_value_export_count"] = 0
    payload["model"]["coverage"]["failed_files"] = sorted(
        [{"path": file["path"], "reason": "parse_file"} for file in request.record()["files"]],
        key=lambda row: row["path"],
    )
    refresh_wire(wire)
    core = decide_semantic_candidate_v3(
        candidate_for(seal, assets, request, policy, wire), seal, assets
    )
    value = project_public_semantic_document_v3(core)
    assert value["status"] == "incomplete" and value["incomplete_kind"] == "partial_safe"
    assert value["files"] == value["projects"][0]["file_ids"] == value["entities"] == []
    assert value["source_inventory_summary"]["proof_only"] == {
        "failed_files": 6,
        "excluded_files": 0,
    }
    assert value["source_inventory_summary"]["records"] == {
        "proof_discovered": 17,
        "published": 1,
        "proof_only": 16,
        "accounted": 17,
    }


@pytest.mark.parametrize("selected", [False, True])
def test_public_empty_project_never_erases_an_independent_safe_project(
    tmp_path: Path, selected: bool
) -> None:
    seal, assets, request, policy, wire = simple_multiple_projects_fixture_v3(
        tmp_path, selected=selected
    )
    core = decide_semantic_candidate_v3(
        candidate_for(seal, assets, request, policy, wire), seal, assets
    )
    value = project_public_semantic_document_v3(core)
    projects = {row["root"]: row for row in value["projects"]}
    assert projects["apps/a"]["file_ids"] == []
    assert projects["apps/b"]["file_ids"] == request.record()["projects"][1]["file_ids"]
    assert value["source_inventory_summary"]["acquired"] == {
        "projects": 2,
        "files": 8,
        "file_bytes": 234,
    }
    assert value["source_inventory_summary"]["safe"] == {"projects": 2, "files": 4}
    assert value["source_inventory_summary"]["records"] == {
        "proof_discovered": 14,
        "published": 8,
        "proof_only": 6,
        "accounted": 14,
    }


def test_public_semantic_refuses_target_unavailable_instead_of_synthesizing_empty(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path, targets=["path:src/button.tsx"])
    omit_selected_button_module_v3(wire)
    core = decide_semantic_candidate_v3(
        candidate_for(seal, assets, request, policy, wire), seal, assets
    )
    assert core.gate()["payload_available"] is False
    with pytest.raises(ValueError, match="available Core"):
        project_public_semantic_document_v3(core)
