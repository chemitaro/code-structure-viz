"""Read-only candidate probe; writes only temporary synthetic test input."""

import json
import tempfile
from pathlib import Path

from tests.contracts import next_source_inventory_v3_reference as inventory
from tests.contracts.test_next_semantic_candidate_v2 import candidate_for
from tests.contracts.test_next_source_inventory_v3 import (
    exclude_record,
    inventory_inputs,
    refresh_wire,
)


def probe(path: Path, *, extra_root_edge: bool) -> dict[str, object]:
    seal, assets, request, policy, wire = inventory_inputs(
        path, extra_programs={"src/other.tsx": b"export const Other = () => null;"}
    )
    payload = wire["semantic_payload"]
    modules = list(payload["model"]["modules"])
    for module in modules:
        source = next(row for row in request.record()["files"] if row["path"] == module["path"])
        exclude_record(wire, "modules", module["id"], reason="tainted", taints=["module_relation"])
        exclude_record(wire, "files", source["id"], reason="failed", taints=[])
    root_id = "next:failure:" + "1" * 64
    payload["proof"]["failure_roots"] = [{
        "id": root_id,
        "collection": "modules",
        "kind": "module_relation",
        "path_ref": modules[0]["path"],
        "record_ids": [modules[0]["id"]],
    }]
    payload["proof"]["causal_edges"] = [
        {"source_id": root_id, "record_id": module["id"], "rule": "identity_dependency"}
        for module in (modules if extra_root_edge else modules[:1])
    ]
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    try:
        value = inventory.retain_source_inventory_seam_v3(candidate, seal, assets)
    except ValueError as error:
        return {"extra_root_edge": extra_root_edge, "admitted": False, "detail": str(error)}
    inventory.validate_source_inventory_seam_v3(value)
    return {
        "extra_root_edge": extra_root_edge,
        "admitted": True,
        "module_paths": [module["path"] for module in modules],
        "root_seed_count": 1,
        "excluded_owner_files": sum(row.reason == "failed" for row in value.file_dispositions()),
        "independent_revalidation": "passed",
    }


def direct_file_probe(path: Path, kind: str) -> dict[str, object]:
    seal, assets, request, policy, wire = inventory_inputs(path)
    payload = wire["semantic_payload"]
    file = next(row for row in request.record()["files"] if "program" in row["roles"])
    module = payload["model"]["modules"][0]
    exclude_record(wire, "modules", module["id"], reason="tainted", taints=[kind])
    exclude_record(wire, "files", file["id"], reason="tainted", taints=[kind])
    payload["proof"]["excluded"] = [
        row for row in payload["proof"]["excluded"] if row["record_id"] != file["id"]
    ]
    payload["proof"]["failed"] = [{"collection": "files", "record_id": file["id"], "reason": kind}]
    root_id = "next:failure:" + "2" * 64
    payload["proof"]["failure_roots"] = [{
        "id": root_id,
        "collection": "files",
        "kind": kind,
        "path_ref": file["path"],
        "record_ids": sorted([file["id"], module["id"]]),
    }]
    payload["proof"]["causal_edges"] = [
        {"source_id": root_id, "record_id": module["id"], "rule": "file_all_records"},
        {"source_id": module["id"], "record_id": file["id"], "rule": "file_all_records"},
    ]
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    try:
        value = inventory.retain_source_inventory_seam_v3(candidate, seal, assets)
    except ValueError as error:
        return {"direct_file_bypass": kind, "admitted": False, "detail": str(error)}
    inventory.validate_source_inventory_seam_v3(value)
    return {
        "direct_file_bypass": kind,
        "admitted": True,
        "declared_file_seed": True,
        "direct_root_file_edge": False,
        "actual_file_disposition": next(
            row.disposition for row in value.file_dispositions() if row.record_id == file["id"]
        ),
        "independent_revalidation": "passed",
    }


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="si03-probe-", dir=Path(__file__).parent) as scratch:
        root = Path(scratch)
        for label, extra_edge in (("original_negative", False), ("bypass", True)):
            case = root / label
            case.mkdir()
            print(json.dumps(probe(case, extra_root_edge=extra_edge), sort_keys=True))
        for kind in ("parse_file", "read_file"):
            case = root / kind
            case.mkdir()
            print(json.dumps(direct_file_probe(case, kind), sort_keys=True))
