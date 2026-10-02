"""Exact-candidate read-only probe; only temporary synthetic test inputs are written."""

import json
import tempfile
from pathlib import Path

from tests.contracts import next_source_inventory_v3_reference as inventory
from tests.contracts.next_reference_validation import recompute_record_id
from tests.contracts.test_next_semantic_candidate_v2 import candidate_for
from tests.contracts.test_next_source_inventory_v3 import (
    exclude_record,
    inventory_inputs,
    refresh_wire,
)


def probe(path: Path, scenario: str, *, nested: bool) -> dict[str, object]:
    extra = {"src/other.tsx": b"export const Other = () => null;"}
    seal, assets, request, policy, wire = inventory_inputs(path, extra_programs=extra)
    payload = wire["semantic_payload"]
    model, proof = payload["model"], payload["proof"]
    public_module = next(row for row in model["modules"] if row["path"] == "src/page.tsx")
    other_module = next(row for row in model["modules"] if row["path"] == "src/other.tsx")
    private_prop = scenario.startswith("private_")
    private_module = scenario.endswith("proof_only")
    target_module = public_module["id"]
    if scenario == "private_dangling":
        target_module = "next:module:" + "f" * 64
    elif private_module:
        target_module = other_module["id"]
    node = {
        "kind": "reference",
        "scope": "repository",
        "module": target_module,
        "exported_name": "Props",
        "type_arguments": [],
    }
    if nested:
        node = {"kind": "array", "element": node, "readonly": False}
    component = {
        "kind": "component",
        "module_id": public_module["id"],
        "declaration_key": "Page",
        "recognition_evidence": ["trusted_callable"],
        "props_state": "known",
    }
    component["id"] = recompute_record_id(component)
    model["components"] = [component]
    prop = {
        "kind": "prop",
        "owner_id": component["id"],
        "name": "p",
        "type_node": node,
        "optional": False,
        "readonly": False,
        "default_evidence": "none",
    }
    prop["id"] = recompute_record_id(prop)
    model["members"] = [prop]
    for collection, record in (("components", component), ("members", prop)):
        proof["discovered_records"].append(
            {"collection": collection, "record_id": record["id"], "taints": []}
        )
    if private_module:
        other_file = next(row for row in request.record()["files"] if row["path"] == "src/other.tsx")
        exclude_record(
            wire, "modules", other_module["id"], reason="tainted", taints=["module_relation"]
        )
        exclude_record(wire, "files", other_file["id"], reason="failed", taints=[])
        root_id = "next:failure:" + "4" * 64
        proof["failure_roots"] = [{
            "id": root_id,
            "kind": "module_relation",
            "collection": "modules",
            "path_ref": other_module["path"],
            "record_ids": [other_module["id"]],
        }]
        proof["causal_edges"] = [{
            "source_id": root_id,
            "record_id": other_module["id"],
            "rule": "relation_dependency",
        }]
    if private_prop:
        exclude_record(wire, "members", prop["id"], reason="not_selected", taints=[])
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    known_in_d = target_module in {row["record_id"] for row in proof["discovered_records"]}
    known_in_m = target_module in {row["id"] for row in model["modules"]}
    result = {
        "scenario": scenario,
        "nested_array": nested,
        "prop_in_public": not private_prop,
        "target_module_in_d": known_in_d,
        "target_module_in_m": known_in_m,
    }
    try:
        value = inventory.retain_source_inventory_seam_v3(candidate, seal, assets)
    except ValueError as error:
        return {**result, "admitted": False, "detail": str(error)}
    inventory.validate_source_inventory_seam_v3(value)
    return {**result, "admitted": True, "independent_revalidation": "passed"}


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="si03-type-ref-", dir=Path(__file__).parent) as scratch:
        root = Path(scratch)
        for scenario in (
            "public_existing",
            "private_dangling",
            "private_proof_only",
            "public_proof_only",
        ):
            for nested in (False, True):
                case = root / (scenario + ("_nested" if nested else "_direct"))
                case.mkdir()
                print(json.dumps(probe(case, scenario, nested=nested), sort_keys=True))
