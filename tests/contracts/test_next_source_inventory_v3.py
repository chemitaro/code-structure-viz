"""Owner-closed source/proof seam, not full Core/TS/OS certification."""

import json
from pathlib import Path, PurePosixPath
from typing import Any, cast

import pytest
from jsonschema import ValidationError  # type: ignore[import-untyped]

from code_structure_viz.adapters.next.source_acquisition import (
    SourceAcquisitionSeal,
    SourceDiscoveryIntent,
    seal_source_acquisition,
)
from code_structure_viz.source.git_repository import Commit, EnumeratedPath
from code_structure_viz.source.source_view import DescriptorAnchoredSourceReadSession
from tests.contracts import next_runtime_v2_reference as runtime
from tests.contracts import next_source_inventory_v3_reference as inventory
from tests.contracts.next_reference_validation import COLLECTIONS, recompute_record_id
from tests.contracts.next_runtime_v2_fixtures import (
    analysis_context_fixture_v2,
    sealed_source_fixture_v1,
)
from tests.contracts.test_next_exchange_v2 import shape_wire
from tests.contracts.test_next_process_observation_v2 import policy_fixture
from tests.contracts.test_next_request_frame_v2 import run_context
from tests.contracts.test_next_semantic_candidate_v2 import candidate_for, update_model_digest
from tests.contracts.test_next_trusted_environment_v2 import profile_members

NONFILE_ROOT_RULES = {
    "module_relation": "relation_dependency",
    "export_binding": "incoming_reexport",
    "boundary_derivation": "boundary_closure",
}


def inventory_inputs(
    tmp_path: Path,
    *,
    version: str = "0.2.0",
    extra_programs: dict[str, bytes] | None = None,
    targets: list[str] | None = None,
    project_roots: tuple[str, ...] = (".",),
) -> tuple[Any, ...]:
    """Real retained source/assets; synthetic semantic input is not a Core certificate."""

    members = profile_members()
    members[runtime.ENTRYPOINT_MEMBER] = (
        "adapter",
        f"// CodeStructureViz-Adapter-Version: {version}\n".encode("ascii"),
    )
    assets = runtime.retain_execution_assets_v1(members)
    trusted = runtime.trusted_environment_manifest_v2(assets)["environment_descriptor"]
    if extra_programs or project_roots != (".",):
        repository = tmp_path / "repo"
        repository.mkdir()
        files = {}
        for root in project_roots:
            prefix = "" if root == "." else root + "/"
            files.update(
                {
                    prefix + "package.json": b'{"dependencies":{"next":"15"}}',
                    prefix + "tsconfig.json": b'{"include":["src/**/*"]}',
                    prefix + "src/page.tsx": b"export default function Page() { return null; }",
                    prefix + "src/global.d.ts": b"declare interface Window { marker: string; }",
                }
            )
        files.update(extra_programs or {})
        for relative_path, content in files.items():
            path = repository / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        entries = tuple(EnumeratedPath(path, PurePosixPath(path)) for path in sorted(files))
        head = Commit("1" * 40)
        reader = DescriptorAnchoredSourceReadSession(
            repository,
            entries,
            head_state=head,
            current_entries=lambda: entries,
            current_head_state=lambda: head,
            max_files=20_000,
            max_file_bytes=4 * 1024 * 1024,
            max_total_bytes=64 * 1024 * 1024,
        )
        seal = seal_source_acquisition(
            SourceDiscoveryIntent(project_roots),
            reader,
            trusted_environment_digest=trusted["sha256"],
        )
        assert type(seal) is SourceAcquisitionSeal
    else:
        seal = sealed_source_fixture_v1(tmp_path, trusted_digest=trusted["sha256"])
    request = runtime.build_request_frame_v2(
        seal,
        assets,
        analysis_context_fixture_v2(seal, assets, targets=targets or [], run_context=run_context()),
    )
    policy = policy_fixture()
    policy.update(
        request_id=request.request_id,
        adapter=assets.adapter_identity(),
        execution_asset_set_id=assets.descriptor()["asset_set_id"],
        trusted_environment_digest=trusted["sha256"],
        limits=request.record()["limits"],
    )
    wire = shape_wire(request)
    model = wire["semantic_payload"]["model"]
    model["projects"] = request.record()["projects"]
    model["files"] = [
        {key: value for key, value in row.items() if key != "content_base64"}
        for row in request.record()["files"]
    ]
    for row in request.record()["files"]:
        if "program" not in row["roles"]:
            continue
        module = {
            "kind": "module",
            "project_id": row["project_id"],
            "path": row["path"],
            "router_context": "none",
            "client_entry": False,
            "derived_roles": [],
        }
        module["id"] = recompute_record_id(module)
        model["modules"].append(module)
    model["modules"].sort(key=lambda row: row["id"])
    model["files"].sort(key=lambda row: row["id"])
    model["projects"].sort(key=lambda row: row["id"])
    wire["semantic_payload"]["proof"]["discovered_records"] = [
        {"collection": name, "record_id": row["id"], "taints": []}
        for name in COLLECTIONS
        for row in model[name]
    ]
    counts = model["coverage"]["counts"]
    counts.update({name: len(model[name]) for name in COLLECTIONS})
    refresh_wire(wire)
    return seal, assets, request, policy, wire


def exclude_record(
    wire: dict[str, Any], collection: str, record_id: str, *, reason: str, taints: list[str]
) -> None:
    payload = wire["semantic_payload"]
    record = next(row for row in payload["model"][collection] if row["id"] == record_id)
    payload["model"][collection].remove(record)
    row = next(
        row for row in payload["proof"]["discovered_records"] if row["record_id"] == record_id
    )
    row["taints"] = taints
    if collection not in {"projects", "files"}:
        row["record"] = record
    payload["proof"]["excluded"].append(
        {"collection": collection, "record_id": record_id, "reason": reason}
    )
    if collection == "files":
        project = next(
            row for row in payload["model"]["projects"] if row["id"] == record["project_id"]
        )
        project["file_ids"].remove(record_id)


def refresh_wire(wire: dict[str, Any]) -> None:
    """Input fixture census, not an expected-value oracle for the v3 seam."""

    payload = wire["semantic_payload"]
    model, proof = payload["model"], payload["proof"]
    counts = model["coverage"]["counts"]
    counts.update({name: len(model[name]) for name in COLLECTIONS})
    counts.update(
        published=sum(len(model[name]) for name in COLLECTIONS),
        discovered=len(proof["discovered_records"]),
        excluded=len(proof["excluded"]),
        failed=len(proof["failed"]),
        internal_entities=len(model["modules"]) + len(model["components"]),
    )
    model["coverage"]["affected_ids"] = sorted(
        row["record_id"] for row in proof["discovered_records"] if row["taints"]
    )
    for rows in proof.values():
        rows.sort(
            key=lambda row: json.dumps(row, sort_keys=True, separators=(",", ":")).encode("ascii")
        )
    update_model_digest(wire)


def test_v3_reference_uses_0_2_0_retained_assets_without_relabeling_v2_kat(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy, wire = inventory_inputs(tmp_path)
    candidate = candidate_for(seal, assets, request, policy, wire)
    factory = getattr(inventory, "retain_source_inventory_seam_v3", None)
    assert callable(factory), "SI-03 retained source/proof seam is not implemented"
    value = factory(candidate, seal, assets)
    assert value.request_id == request.request_id
    assert value.transport_candidate() is candidate
    assert value.source_seal() is seal
    assert value.execution_assets() is assets
    assert candidate.response_frame().control()["adapter_version"] == "0.2.0"
    old = json.loads(
        (
            Path(__file__).parents[1] / "fixtures/next_runtime_v2/source-sealed-request.json"
        ).read_text()
    )
    assert old["adapter_version"] == "0.1.0"


@pytest.mark.parametrize("owner", ["candidate", "seal", "assets"])
def test_inventory_binding_rejects_unowned_values(tmp_path: Path, owner: str) -> None:
    seal, assets, request, policy, wire = inventory_inputs(tmp_path)
    candidate = candidate_for(seal, assets, request, policy, wire)
    values: dict[str, Any] = {"candidate": candidate, "seal": seal, "assets": assets}
    values[owner] = object()
    with pytest.raises(TypeError):
        inventory.retain_source_inventory_seam_v3(**values)


def test_inventory_profile_does_not_relabel_an_old_retained_producer(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = inventory_inputs(tmp_path, version="0.1.0")
    candidate = candidate_for(seal, assets, request, policy, wire)
    with pytest.raises(ValueError, match=r"producer version 0\.2\.0"):
        inventory.retain_source_inventory_seam_v3(candidate, seal, assets)


def test_inventory_binding_rejects_another_acquisition(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = inventory_inputs(tmp_path)
    candidate = candidate_for(seal, assets, request, policy, wire)
    other_dir = tmp_path / "other"
    other_dir.mkdir()
    trusted = runtime.trusted_environment_manifest_v2(assets)["environment_descriptor"]
    other_seal = sealed_source_fixture_v1(
        other_dir, trusted_digest=trusted["sha256"], page_content=b"export const other = 1;"
    )
    with pytest.raises(ValueError):
        inventory.retain_source_inventory_seam_v3(candidate, other_seal, assets)


def test_inventory_binding_rejects_different_assets_with_the_same_version(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = inventory_inputs(tmp_path)
    candidate = candidate_for(seal, assets, request, policy, wire)
    members = profile_members()
    members[runtime.ENTRYPOINT_MEMBER] = (
        "adapter",
        b"// CodeStructureViz-Adapter-Version: 0.2.0\n// different retained bytes\n",
    )
    other_assets = runtime.retain_execution_assets_v1(members)
    assert other_assets.adapter_identity()["version"] == "0.2.0"
    with pytest.raises(ValueError):
        inventory.retain_source_inventory_seam_v3(candidate, seal, other_assets)


def test_inventory_binding_is_immutable_and_cannot_be_directly_constructed(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = inventory_inputs(tmp_path)
    candidate = candidate_for(seal, assets, request, policy, wire)
    value = inventory.retain_source_inventory_seam_v3(candidate, seal, assets)
    with pytest.raises(TypeError, match="created by retain_source_inventory_seam_v3"):
        inventory.ValidatedSourceInventorySeamV3()
    with pytest.raises((AttributeError, TypeError)):
        cast(Any, value).request_id = "forged-request"


def test_source_rows_are_resolved_from_same_request_without_record_payload(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = inventory_inputs(tmp_path)
    candidate = candidate_for(seal, assets, request, policy, wire)
    value = inventory.retain_source_inventory_seam_v3(candidate, seal, assets)
    assert value.source_records() == {
        "projects": request.record()["projects"],
        "files": [
            {key: item for key, item in row.items() if key != "content_base64"}
            for row in request.record()["files"]
        ],
    }


@pytest.mark.parametrize("collection", ["projects", "files"])
def test_source_record_payload_is_rejected_even_when_it_matches_the_parent(
    tmp_path: Path, collection: str
) -> None:
    seal, assets, request, policy, wire = inventory_inputs(tmp_path)
    payload = wire["semantic_payload"]
    source_row = next(
        row for row in payload["proof"]["discovered_records"] if row["collection"] == collection
    )
    source_row["record"] = payload["model"][collection][0]
    candidate = candidate_for(seal, assets, request, policy, wire)
    with pytest.raises(ValueError, match="source discovery record"):
        inventory.retain_source_inventory_seam_v3(candidate, seal, assets)


@pytest.mark.parametrize("collection", ["projects", "files"])
@pytest.mark.parametrize("mutation", ["missing", "duplicate"])
def test_each_acquired_source_is_discovered_exactly_once(
    tmp_path: Path, collection: str, mutation: str
) -> None:
    seal, assets, request, policy, wire = inventory_inputs(tmp_path)
    rows = wire["semantic_payload"]["proof"]["discovered_records"]
    source_row = next(row for row in rows if row["collection"] == collection)
    if mutation == "missing":
        rows.remove(source_row)
    else:
        rows.append(dict(source_row))
    candidate = candidate_for(seal, assets, request, policy, wire)
    with pytest.raises(ValueError, match="acquired source discovery"):
        inventory.retain_source_inventory_seam_v3(candidate, seal, assets)


@pytest.mark.parametrize("mutation", ["missing", "hidden_missing", "duplicate", "nonprogram"])
def test_full_module_ownership_is_checked_before_public_projection(
    tmp_path: Path, mutation: str
) -> None:
    seal, assets, request, policy, wire = inventory_inputs(tmp_path)
    payload = wire["semantic_payload"]
    module = payload["model"]["modules"][0]
    row = next(
        row for row in payload["proof"]["discovered_records"] if row["collection"] == "modules"
    )
    if mutation in {"missing", "hidden_missing"}:
        payload["proof"]["discovered_records"].remove(row)
        payload["model"]["modules"] = []
        if mutation == "hidden_missing":
            file = next(file for file in payload["model"]["files"] if "program" in file["roles"])
            payload["model"]["files"].remove(file)
            payload["proof"]["excluded"].append(
                {"collection": "files", "record_id": file["id"], "reason": "not_selected"}
            )
            payload["model"]["projects"][0]["file_ids"].remove(file["id"])
    elif mutation == "duplicate":
        payload["proof"]["discovered_records"].append(dict(row))
    else:
        nonprogram = next(
            file for file in request.record()["files"] if "program" not in file["roles"]
        )
        module["path"] = nonprogram["path"]
        module["id"] = recompute_record_id(module)
        row["record_id"] = module["id"]
    update_model_digest(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    with pytest.raises(ValueError, match="full Module owner"):
        inventory.retain_source_inventory_seam_v3(candidate, seal, assets)


@pytest.mark.parametrize("collection,field", [("files", "sha256"), ("projects", "config_digest")])
def test_public_source_metadata_cannot_be_replaced_by_child(
    tmp_path: Path, collection: str, field: str
) -> None:
    seal, assets, request, policy, wire = inventory_inputs(tmp_path)
    wire["semantic_payload"]["model"][collection][0][field] = "0" * 64
    update_model_digest(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    with pytest.raises(ValueError, match="source metadata"):
        inventory.retain_source_inventory_seam_v3(candidate, seal, assets)


def test_complete_inventory_has_exact_published_partition_and_module_eligibility(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy, wire = inventory_inputs(tmp_path)
    candidate = candidate_for(seal, assets, request, policy, wire)
    value = inventory.retain_source_inventory_seam_v3(candidate, seal, assets)
    assert value.file_dispositions() == tuple(
        inventory.FileDispositionV3(row["id"], "published", None)
        for row in sorted(request.record()["files"], key=lambda row: row["id"])
    )
    assert value.eligible_module_ids() == (wire["semantic_payload"]["model"]["modules"][0]["id"],)
    assert value.safe_files() == wire["semantic_payload"]["model"]["files"]
    assert value.safe_projects() == wire["semantic_payload"]["model"]["projects"]


@pytest.mark.parametrize("kind", ["module_relation", "export_binding", "boundary_derivation"])
def test_nonfile_module_failure_excludes_owner_file_without_faking_file_taint(
    tmp_path: Path, kind: str
) -> None:
    seal, assets, request, policy, wire = inventory_inputs(tmp_path)
    payload = wire["semantic_payload"]
    module = dict(payload["model"]["modules"][0])
    file = next(row for row in request.record()["files"] if "program" in row["roles"])
    exclude_record(wire, "modules", module["id"], reason="tainted", taints=[kind])
    exclude_record(wire, "files", file["id"], reason="failed", taints=[])
    payload["proof"]["failure_roots"] = [
        {
            "id": "next:failure:" + "1" * 64,
            "collection": "modules",
            "kind": kind,
            "path_ref": module["path"],
            "record_ids": [module["id"]],
        }
    ]
    payload["proof"]["causal_edges"] = [
        {
            "source_id": "next:failure:" + "1" * 64,
            "record_id": module["id"],
            "rule": NONFILE_ROOT_RULES[kind],
        }
    ]
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    value = inventory.retain_source_inventory_seam_v3(candidate, seal, assets)
    disposition = next(row for row in value.file_dispositions() if row.record_id == file["id"])
    assert disposition == inventory.FileDispositionV3(file["id"], "excluded", "failed")
    assert value.eligible_module_ids() == ()
    assert {row["id"] for row in value.safe_files()} == {
        row["id"] for row in request.record()["files"] if row["id"] != file["id"]
    }
    assert value.safe_projects()[0]["file_ids"] == sorted(
        row["id"] for row in request.record()["files"] if row["id"] != file["id"]
    )
    source_row = next(
        row for row in payload["proof"]["discovered_records"] if row["record_id"] == file["id"]
    )
    assert source_row["taints"] == [] and "record" not in source_row
    assert not any(row["record_id"] == file["id"] for row in payload["proof"]["failed"])


@pytest.mark.parametrize("kind", ["parse_file", "read_file"])
def test_acquired_file_root_partition_keeps_independent_sibling_and_source_metadata(
    tmp_path: Path, kind: str
) -> None:
    seal, assets, request, policy, wire = inventory_inputs(
        tmp_path, extra_programs={"src/broken.tsx": b"export default function Broken("}
    )
    payload = wire["semantic_payload"]
    file = next(row for row in request.record()["files"] if row["path"] == "src/broken.tsx")
    module = next(row for row in payload["model"]["modules"] if row["path"] == file["path"])
    exclude_record(wire, "modules", module["id"], reason="tainted", taints=[kind])
    exclude_record(wire, "files", file["id"], reason="tainted", taints=[kind])
    payload["proof"]["excluded"] = [
        row for row in payload["proof"]["excluded"] if row["record_id"] != file["id"]
    ]
    payload["proof"]["failed"] = [{"collection": "files", "record_id": file["id"], "reason": kind}]
    payload["proof"]["failure_roots"] = [
        {
            "id": "next:failure:" + "2" * 64,
            "kind": kind,
            "collection": "files",
            "path_ref": file["path"],
            "record_ids": sorted([file["id"], module["id"]]),
        }
    ]
    payload["proof"]["causal_edges"] = [
        {
            "source_id": "next:failure:" + "2" * 64,
            "record_id": record_id,
            "rule": "file_all_records",
        }
        for record_id in sorted([file["id"], module["id"]])
    ]
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    value = inventory.retain_source_inventory_seam_v3(candidate, seal, assets)
    assert next(row for row in value.file_dispositions() if row.record_id == file["id"]) == (
        inventory.FileDispositionV3(file["id"], "failed", kind)
    )
    assert {row["path"] for row in value.safe_files()} == {
        "package.json",
        "tsconfig.json",
        "src/global.d.ts",
        "src/page.tsx",
    }
    assert {row["path"] for row in value.source_records()["files"]} == {
        "package.json",
        "tsconfig.json",
        "src/global.d.ts",
        "src/page.tsx",
        "src/broken.tsx",
    }
    assert "content_base64" not in value.source_records()["files"][0]
    assert value.source_seal() is seal


@pytest.mark.parametrize("mutation", ["no_root", "fake_file_taint"])
def test_owner_failure_cannot_be_forged_or_relabelled_as_file_taint(
    tmp_path: Path, mutation: str
) -> None:
    seal, assets, request, policy, wire = inventory_inputs(tmp_path)
    payload = wire["semantic_payload"]
    module = dict(payload["model"]["modules"][0])
    file = next(row for row in request.record()["files"] if "program" in row["roles"])
    exclude_record(wire, "modules", module["id"], reason="tainted", taints=["module_relation"])
    exclude_record(
        wire,
        "files",
        file["id"],
        reason="tainted" if mutation == "fake_file_taint" else "failed",
        taints=["module_relation"] if mutation == "fake_file_taint" else [],
    )
    if mutation == "fake_file_taint":
        payload["proof"]["failure_roots"] = [
            {
                "id": "next:failure:" + "1" * 64,
                "collection": "modules",
                "kind": "module_relation",
                "path_ref": module["path"],
                "record_ids": [module["id"]],
            }
        ]
        payload["proof"]["causal_edges"] = [
            {
                "source_id": "next:failure:" + "1" * 64,
                "record_id": module["id"],
                "rule": "relation_dependency",
            }
        ]
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    with pytest.raises(ValueError, match=r"owner cause|File taint"):
        inventory.retain_source_inventory_seam_v3(candidate, seal, assets)


@pytest.mark.parametrize(
    "mutation", ["digest", "public_payload", "public_duplicate", "private_missing"]
)
def test_model_digest_and_full_discovered_join_are_revalidated(
    tmp_path: Path, mutation: str
) -> None:
    seal, assets, request, policy, wire = inventory_inputs(tmp_path)
    payload = wire["semantic_payload"]
    module = payload["model"]["modules"][0]
    if mutation == "public_payload":
        row = next(
            row
            for row in payload["proof"]["discovered_records"]
            if row["record_id"] == module["id"]
        )
        row["record"] = dict(module)
    elif mutation == "public_duplicate":
        payload["model"]["modules"].append(dict(module))
    elif mutation == "private_missing":
        payload["proof"]["discovered_records"].append(
            {
                "collection": "components",
                "record_id": "next:component:" + "0" * 64,
                "taints": [],
            }
        )
    refresh_wire(wire)
    if mutation == "digest":
        payload["model_digest"] = "0" * 64
    candidate = candidate_for(seal, assets, request, policy, wire)
    with pytest.raises(ValueError, match="model/proof"):
        inventory.retain_source_inventory_seam_v3(candidate, seal, assets)


@pytest.mark.parametrize("view", ["private_dangling", "public_to_private"])
def test_references_close_in_the_correct_public_or_private_view(tmp_path: Path, view: str) -> None:
    seal, assets, request, policy, wire = inventory_inputs(tmp_path)
    payload = wire["semantic_payload"]
    module = dict(payload["model"]["modules"][0])
    component = {
        "kind": "component",
        "module_id": "next:module:" + "0" * 64 if view == "private_dangling" else module["id"],
        "declaration_key": "Detached",
        "recognition_evidence": ["trusted_callable"],
        "props_state": "no_props",
    }
    component["id"] = recompute_record_id(component)
    row: dict[str, Any] = {"collection": "components", "record_id": component["id"], "taints": []}
    if view == "private_dangling":
        row["record"] = component
        payload["proof"]["excluded"].append(
            {
                "collection": "components",
                "record_id": component["id"],
                "reason": "not_selected",
            }
        )
    else:
        payload["model"]["components"] = [component]
        file = next(row for row in request.record()["files"] if "program" in row["roles"])
        exclude_record(wire, "modules", module["id"], reason="tainted", taints=["module_relation"])
        exclude_record(wire, "files", file["id"], reason="failed", taints=[])
        payload["proof"]["failure_roots"] = [
            {
                "id": "next:failure:" + "1" * 64,
                "collection": "modules",
                "kind": "module_relation",
                "path_ref": module["path"],
                "record_ids": [module["id"]],
            }
        ]
        payload["proof"]["causal_edges"] = [
            {
                "source_id": "next:failure:" + "1" * 64,
                "record_id": module["id"],
                "rule": "relation_dependency",
            }
        ]
    payload["proof"]["discovered_records"].append(row)
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    with pytest.raises(ValueError, match="reference"):
        inventory.retain_source_inventory_seam_v3(candidate, seal, assets)


@pytest.mark.parametrize("reason", ["not_selected", "target_excluded", "unsupported"])
def test_owner_bookkeeping_reason_is_preserved_without_a_fake_failure(
    tmp_path: Path, reason: str
) -> None:
    seal, assets, request, policy, wire = inventory_inputs(
        tmp_path,
        extra_programs={"src/other.tsx": b"export const Other = () => null;"},
        targets=["path:src/page.tsx"],
    )
    payload = wire["semantic_payload"]
    module = next(row for row in payload["model"]["modules"] if row["path"] == "src/other.tsx")
    file = next(row for row in request.record()["files"] if row["path"] == module["path"])
    selected = next(row for row in payload["model"]["modules"] if row["path"] == "src/page.tsx")
    exclude_record(wire, "modules", module["id"], reason=reason, taints=[])
    exclude_record(wire, "files", file["id"], reason=reason, taints=[])
    selected_file = next(
        row for row in request.record()["files"] if row["path"] == selected["path"]
    )
    payload["proof"]["target_resolutions"] = [
        {
            "target_key": "path:src/page.tsx",
            "status": "resolved",
            "record_ids": sorted([selected_file["id"], selected["id"]]),
        }
    ]
    if reason == "unsupported":
        relation = {
            "kind": "literal_dynamic_import",
            "source_id": selected["id"],
            "target": {
                "kind": "unresolved",
                "target_kind": "unresolved_relative",
                "safe_specifier": "unknown",
                "exported_name": None,
            },
            "role": "value",
            "reexport": False,
            "boundary_effect": "none",
        }
        relation["id"] = recompute_record_id(relation)
        payload["model"]["relations"].append(relation)
        payload["proof"]["discovered_records"].append(
            {
                "collection": "relations",
                "record_id": relation["id"],
                "taints": [],
            }
        )
        payload["model"]["coverage"]["unknown_relation_count"] = 1
        payload["model"]["diagnostics"] = [
            {
                "code": "CSV-NEXT-UNSUPPORTED-001",
                "severity": "warning",
                "recoverable": True,
                "outcome": "complete",
                "ref_permission": "path_or_symbol",
                "path_ref": None,
                "symbol_ref": module["id"],
                "count": 1,
            }
        ]
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    value = inventory.retain_source_inventory_seam_v3(candidate, seal, assets)
    assert next(row for row in value.file_dispositions() if row.record_id == file["id"]) == (
        inventory.FileDispositionV3(file["id"], "excluded", reason)
    )
    assert value.eligible_module_ids() == (selected["id"],)
    assert payload["proof"]["failure_roots"] == []
    assert all(row["taints"] == [] for row in payload["proof"]["discovered_records"])


def test_counts_are_actual_acquired_discovered_and_published_measurements(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = inventory_inputs(tmp_path)
    candidate = candidate_for(seal, assets, request, policy, wire)
    value = inventory.retain_source_inventory_seam_v3(candidate, seal, assets)
    assert value.counts() == inventory.SourceInventoryCountsV3(
        acquired_projects=1,
        acquired_files=4,
        acquired_file_bytes=145,
        proof_discovered=6,
        published_records=6,
        proof_only_records=0,
        accounted_records=6,
        published_modules=1,
        published_components=0,
        published_entities=1,
    )
    with pytest.raises((AttributeError, TypeError)):
        cast(Any, value.counts()).acquired_file_bytes = 0


@pytest.mark.parametrize("count", ["discovered", "published", "files", "excluded", "failed"])
def test_coverage_cannot_hide_actual_inventory_counts(tmp_path: Path, count: str) -> None:
    seal, assets, request, policy, wire = inventory_inputs(tmp_path)
    wire["semantic_payload"]["model"]["coverage"]["counts"][count] += 1
    update_model_digest(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    with pytest.raises(ValueError, match="actual inventory counts"):
        inventory.retain_source_inventory_seam_v3(candidate, seal, assets)


def test_partition_fingerprint_matches_independent_ascii_literal_kat(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = inventory_inputs(tmp_path)
    candidate = candidate_for(seal, assets, request, policy, wire)
    value = inventory.retain_source_inventory_seam_v3(candidate, seal, assets)
    # Produced once by independent json.dumps/hashlib using the fixture INPUT,
    # before a v3 fingerprint producer existed. No producer computes this oracle.
    literal = (
        '{"profile_id":"next-source-inventory-safe-subset-v1","projects":['
        '{"excluded_file_ids":[],"failed_file_ids":[],"project_id":'
        '"next:project:530b20c858c6039c19737f386f96cfabdadda6b8a0a1c98b5ca639beb2765c25",'
        '"safe_file_ids":['
        '"next:file:6e5a491cdd30e69e4cf115a95b99ad11d83beac749f4f20d7fa12cb26d9f7c0c",'
        '"next:file:8cb22e35356bd13a3869a5dd8bd680300b8f8ba5bd33bcdbfc7653cc1eba3e76",'
        '"next:file:c5682d41cbd3e90660a43a123464d5f3e07a5536afab19de928c1aebdbf2153b",'
        '"next:file:c891008136a6466799eb75e12e6b6d7b2bdb35587cb8c2f96b3b5a720da870bf"]}],'
        '"request_id":"8a550469363d2d92f6c55345cb8cc0c2f540109cafd4e8b507cfb5cf25de175d"}'
    )
    assert value.profile_id == "next-source-inventory-safe-subset-v1"
    assert value.partition_preimage() == json.loads(literal)
    assert (
        value.partition_fingerprint
        == "0c380fdc863eab3e029cec9129a8fa000bb0695321221a559025757060d48b83"
    )


@pytest.mark.parametrize(
    "mutation",
    ["private_unaccounted", "multiple", "public_taint", "project_excluded", "project_taint"],
)
def test_each_full_record_has_one_legal_disposition_and_projects_are_always_public(
    tmp_path: Path, mutation: str
) -> None:
    seal, assets, request, policy, wire = inventory_inputs(tmp_path)
    payload = wire["semantic_payload"]
    if mutation in {"private_unaccounted", "multiple"}:
        component = {
            "kind": "component",
            "module_id": payload["model"]["modules"][0]["id"],
            "declaration_key": "Private",
            "recognition_evidence": ["trusted_callable"],
            "props_state": "no_props",
        }
        component["id"] = recompute_record_id(component)
        payload["proof"]["discovered_records"].append(
            {
                "collection": "components",
                "record_id": component["id"],
                "taints": [],
                "record": component,
            }
        )
        if mutation == "multiple":
            row = {
                "collection": "components",
                "record_id": component["id"],
                "reason": "not_selected",
            }
            payload["proof"]["excluded"] = [row, {**row, "reason": "target_excluded"}]
    elif mutation == "project_excluded":
        payload["proof"]["excluded"] = [
            {
                "collection": "projects",
                "record_id": request.record()["projects"][0]["id"],
                "reason": "not_selected",
            }
        ]
    else:
        collection = "projects" if mutation == "project_taint" else "modules"
        row = next(
            row for row in payload["proof"]["discovered_records"] if row["collection"] == collection
        )
        row["taints"] = ["module_relation"]
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    with pytest.raises(ValueError, match=r"disposition|public.*taint|Project.*taint"):
        inventory.retain_source_inventory_seam_v3(candidate, seal, assets)


def test_independent_revalidation_uses_retained_owners_and_getters_do_not_leak_caches(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy, wire = inventory_inputs(tmp_path)
    candidate = candidate_for(seal, assets, request, policy, wire)
    value = inventory.retain_source_inventory_seam_v3(candidate, seal, assets)
    validate = getattr(inventory, "validate_source_inventory_seam_v3", None)
    assert callable(validate), "independent source/proof revalidation is not implemented"
    assert validate(value) is None
    value.safe_files()[0]["sha256"] = "0" * 64
    value.safe_projects()[0]["file_ids"].clear()
    value.partition_preimage()["projects"].clear()
    value.source_records()["files"].clear()
    assert validate(value) is None
    assert value.counts().acquired_files == 4
    with pytest.raises(TypeError):
        validate(object())


@pytest.mark.parametrize("delta", [0, 1])
def test_actual_10000_and_plus_one_measurements_include_payload_free_source_rows(
    tmp_path: Path, delta: int
) -> None:
    seal, assets, request, policy, wire = inventory_inputs(tmp_path)
    payload = wire["semantic_payload"]
    model, proof = payload["model"], payload["proof"]
    file = next(row for row in request.record()["files"] if row["path"] == "src/global.d.ts")
    exclude_record(wire, "files", file["id"], reason="tainted", taints=["read_file"])
    proof["excluded"] = []
    proof["failed"] = [{"collection": "files", "record_id": file["id"], "reason": "read_file"}]
    proof["failure_roots"] = [
        {
            "id": "next:failure:" + "2" * 64,
            "kind": "read_file",
            "collection": "files",
            "path_ref": file["path"],
            "record_ids": [file["id"]],
        }
    ]
    proof["causal_edges"] = [
        {
            "source_id": "next:failure:" + "2" * 64,
            "record_id": file["id"],
            "rule": "file_all_records",
        }
    ]
    component = {
        "kind": "component",
        "module_id": model["modules"][0]["id"],
        "declaration_key": "Page",
        "recognition_evidence": ["trusted_callable"],
        "props_state": "known",
    }
    component["id"] = recompute_record_id(component)
    model["components"] = [component]
    proof["discovered_records"].append(
        {
            "collection": "components",
            "record_id": component["id"],
            "taints": [],
        }
    )
    for index in range(9993 + delta):
        member = {
            "kind": "prop",
            "owner_id": component["id"],
            "name": f"p{index:05d}",
            "type_node": {"kind": "primitive", "name": "string"},
            "optional": False,
            "readonly": False,
            "default_evidence": "none",
        }
        member["id"] = recompute_record_id(member)
        model["members"].append(member)
        proof["discovered_records"].append(
            {
                "collection": "members",
                "record_id": member["id"],
                "taints": [],
            }
        )
    model["members"].sort(key=lambda row: row["id"])
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    value = inventory.retain_source_inventory_seam_v3(candidate, seal, assets)
    assert value.counts().acquired_files == 4 and value.counts().acquired_file_bytes == 145
    assert value.counts().proof_only_records == 1
    assert value.counts().published_records == 9999 + delta
    assert value.counts().proof_discovered == value.counts().accounted_records == 10000 + delta
    assert value.counts().published_entities == 2
    source_row = next(row for row in proof["discovered_records"] if row["record_id"] == file["id"])
    assert "record" not in source_row
    # Measurement only: SI-04 owns inclusive/+1 limit admission and routing.
    inventory.validate_source_inventory_seam_v3(value)


@pytest.mark.parametrize("roots", [("a",), ("a", "z")])
def test_empty_project_projection_does_not_erase_another_project_inventory(
    tmp_path: Path, roots: tuple[str, ...]
) -> None:
    seal, assets, request, policy, wire = inventory_inputs(tmp_path, project_roots=roots)
    payload = wire["semantic_payload"]
    model, proof = payload["model"], payload["proof"]
    for index, file in enumerate(request.record()["files"]):
        if not file["path"].startswith("a/"):
            continue
        module = next((row for row in model["modules"] if row["path"] == file["path"]), None)
        if module is not None:
            exclude_record(wire, "modules", module["id"], reason="tainted", taints=["read_file"])
        exclude_record(wire, "files", file["id"], reason="tainted", taints=["read_file"])
        proof["excluded"] = [row for row in proof["excluded"] if row["record_id"] != file["id"]]
        proof["failed"].append(
            {"collection": "files", "record_id": file["id"], "reason": "read_file"}
        )
        failure_id = "next:failure:" + f"{index + 1:064x}"
        seeds = sorted([file["id"]] + ([module["id"]] if module is not None else []))
        proof["failure_roots"].append(
            {
                "id": failure_id,
                "kind": "read_file",
                "collection": "files",
                "path_ref": file["path"],
                "record_ids": seeds,
            }
        )
        proof["causal_edges"].extend(
            {"source_id": failure_id, "record_id": record_id, "rule": "file_all_records"}
            for record_id in seeds
        )
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    value = inventory.retain_source_inventory_seam_v3(candidate, seal, assets)
    projects = {row["root"]: row for row in value.safe_projects()}
    assert projects["a"]["file_ids"] == []
    if len(roots) == 2:
        assert len(projects["z"]["file_ids"]) == 4
    assert {row["path"] for row in value.safe_files()} == (
        {"z/package.json", "z/tsconfig.json", "z/src/page.tsx", "z/src/global.d.ts"}
        if len(roots) == 2
        else set()
    )
    expected = (
        inventory.SourceInventoryCountsV3(
            acquired_projects=2,
            acquired_files=8,
            acquired_file_bytes=290,
            proof_discovered=12,
            published_records=7,
            proof_only_records=5,
            accounted_records=12,
            published_modules=1,
            published_components=0,
            published_entities=1,
        )
        if len(roots) == 2
        else inventory.SourceInventoryCountsV3(
            acquired_projects=1,
            acquired_files=4,
            acquired_file_bytes=145,
            proof_discovered=6,
            published_records=1,
            proof_only_records=5,
            accounted_records=6,
            published_modules=0,
            published_components=0,
            published_entities=0,
        )
    )
    assert value.counts() == expected
    assert [row["project_id"] for row in value.partition_preimage()["projects"]] == [
        row["id"] for row in request.record()["projects"]
    ]
    assert [row["root"] for row in request.record()["projects"]] == list(roots)
    assert len(value.source_records()["projects"][0]["file_ids"]) == 4
    inventory.validate_source_inventory_seam_v3(value)


@pytest.mark.parametrize("kind", ["module_relation", "export_binding", "boundary_derivation"])
@pytest.mark.parametrize("extra_root_edge", [False, True])
def test_owner_cause_cannot_borrow_a_root_from_an_independent_module(
    tmp_path: Path, kind: str, extra_root_edge: bool
) -> None:
    seal, assets, request, policy, wire = inventory_inputs(
        tmp_path, extra_programs={"src/other.tsx": b"export const Other = () => null;"}
    )
    payload = wire["semantic_payload"]
    modules = list(payload["model"]["modules"])
    for module in modules:
        file = next(row for row in request.record()["files"] if row["path"] == module["path"])
        exclude_record(wire, "modules", module["id"], reason="tainted", taints=[kind])
        exclude_record(wire, "files", file["id"], reason="failed", taints=[])
    witnessed = modules[0]
    payload["proof"]["failure_roots"] = [
        {
            "id": "next:failure:" + "1" * 64,
            "collection": "modules",
            "kind": kind,
            "path_ref": witnessed["path"],
            "record_ids": [witnessed["id"]],
        }
    ]
    payload["proof"]["causal_edges"] = [
        {
            "source_id": "next:failure:" + "1" * 64,
            "record_id": module["id"],
            "rule": NONFILE_ROOT_RULES[kind],
        }
        for module in (modules if extra_root_edge else [witnessed])
    ]
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    with pytest.raises(ValueError, match="owner cause"):
        inventory.retain_source_inventory_seam_v3(candidate, seal, assets)


@pytest.mark.parametrize("missing", ["file_seed", "file_edge", "file_taint"])
def test_direct_file_failure_keeps_its_source_seed_edge_and_typed_taint(
    tmp_path: Path, missing: str
) -> None:
    seal, assets, request, policy, wire = inventory_inputs(tmp_path)
    payload = wire["semantic_payload"]
    file = next(row for row in request.record()["files"] if row["path"] == "src/global.d.ts")
    exclude_record(wire, "files", file["id"], reason="tainted", taints=["read_file"])
    payload["proof"]["excluded"] = []
    payload["proof"]["failed"] = [
        {"collection": "files", "record_id": file["id"], "reason": "read_file"}
    ]
    payload["proof"]["failure_roots"] = [
        {
            "id": "next:failure:" + "2" * 64,
            "kind": "read_file",
            "collection": "files",
            "path_ref": file["path"],
            "record_ids": [file["id"]],
        }
    ]
    payload["proof"]["causal_edges"] = [
        {
            "source_id": "next:failure:" + "2" * 64,
            "record_id": file["id"],
            "rule": "file_all_records",
        }
    ]
    if missing == "file_seed":
        payload["proof"]["failure_roots"][0]["record_ids"] = [payload["model"]["modules"][0]["id"]]
    elif missing == "file_edge":
        payload["proof"]["causal_edges"] = []
    else:
        next(
            row for row in payload["proof"]["discovered_records"] if row["record_id"] == file["id"]
        )["taints"] = []
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    with pytest.raises(ValueError):
        inventory.retain_source_inventory_seam_v3(candidate, seal, assets)


@pytest.mark.parametrize("kind", ["parse_file", "read_file"])
def test_direct_file_seed_cannot_borrow_an_indirect_module_witness(
    tmp_path: Path, kind: str
) -> None:
    seal, assets, request, policy, wire = inventory_inputs(tmp_path)
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
    payload["proof"]["failure_roots"] = [
        {
            "id": root_id,
            "kind": kind,
            "collection": "files",
            "path_ref": file["path"],
            "record_ids": sorted([file["id"], module["id"]]),
        }
    ]
    payload["proof"]["causal_edges"] = [
        {"source_id": root_id, "record_id": module["id"], "rule": "file_all_records"},
        {"source_id": module["id"], "record_id": file["id"], "rule": "file_all_records"},
    ]
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    with pytest.raises(ValueError, match="root-origin"):
        inventory.retain_source_inventory_seam_v3(candidate, seal, assets)


def test_discovery_object_order_is_canonical_not_adapter_iteration_order(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = inventory_inputs(tmp_path)
    wire["semantic_payload"]["proof"]["discovered_records"].reverse()
    candidate = candidate_for(seal, assets, request, policy, wire)
    with pytest.raises(ValueError, match="model/proof"):
        inventory.retain_source_inventory_seam_v3(candidate, seal, assets)


@pytest.mark.parametrize("kind", ["module_relation", "export_binding", "boundary_derivation"])
def test_owner_root_rejects_a_noncanonical_rule_even_when_its_shape_is_allowed(
    tmp_path: Path, kind: str
) -> None:
    seal, assets, request, policy, wire = inventory_inputs(tmp_path)
    payload = wire["semantic_payload"]
    file = next(row for row in request.record()["files"] if "program" in row["roles"])
    module = payload["model"]["modules"][0]
    exclude_record(wire, "modules", module["id"], reason="tainted", taints=[kind])
    exclude_record(wire, "files", file["id"], reason="failed", taints=[])
    root_id = "next:failure:" + "3" * 64
    payload["proof"]["failure_roots"] = [
        {
            "id": root_id,
            "kind": kind,
            "collection": "modules",
            "path_ref": module["path"],
            "record_ids": [module["id"]],
        }
    ]
    payload["proof"]["causal_edges"] = [
        {"source_id": root_id, "record_id": module["id"], "rule": "identity_dependency"}
    ]
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    with pytest.raises(ValueError, match="root-origin rule"):
        inventory.retain_source_inventory_seam_v3(candidate, seal, assets)


@pytest.mark.parametrize(
    "kinds", [("parse_file", "read_file"), ("parse_file", "parse_file"), ("read_file", "read_file")]
)
@pytest.mark.parametrize("missing_edge", [None, 0, 1])
def test_every_root_keeps_its_own_direct_file_seed_witness(
    tmp_path: Path, kinds: tuple[str, str], missing_edge: int | None
) -> None:
    seal, assets, request, policy, wire = inventory_inputs(tmp_path)
    payload = wire["semantic_payload"]
    file = next(row for row in request.record()["files"] if "program" in row["roles"])
    module = payload["model"]["modules"][0]
    taints = sorted(set(kinds), key=["parse_file", "read_file"].index)
    exclude_record(wire, "modules", module["id"], reason="tainted", taints=taints)
    exclude_record(wire, "files", file["id"], reason="tainted", taints=taints)
    proof = payload["proof"]
    proof["excluded"] = [row for row in proof["excluded"] if row["record_id"] != file["id"]]
    proof["failed"] = [{"collection": "files", "record_id": file["id"], "reason": taints[0]}]
    proof["failure_roots"] = [
        {
            "id": "next:failure:" + f"{index + 1:064x}",
            "kind": kind,
            "collection": "files",
            "path_ref": file["path"],
            "record_ids": sorted([file["id"], module["id"]]),
        }
        for index, kind in enumerate(kinds)
    ]
    proof["causal_edges"] = [
        {"source_id": root["id"], "record_id": record_id, "rule": "file_all_records"}
        for index, root in enumerate(proof["failure_roots"])
        for record_id in [file["id"], module["id"]]
        if missing_edge != index or record_id != file["id"]
    ]
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    if missing_edge is not None:
        with pytest.raises(ValueError, match="root-origin"):
            inventory.retain_source_inventory_seam_v3(candidate, seal, assets)
        return
    value = inventory.retain_source_inventory_seam_v3(candidate, seal, assets)
    assert next(row for row in value.file_dispositions() if row.record_id == file["id"]) == (
        inventory.FileDispositionV3(file["id"], "failed", taints[0])
    )
    assert value.counts() == inventory.SourceInventoryCountsV3(
        acquired_projects=1,
        acquired_files=4,
        acquired_file_bytes=145,
        proof_discovered=6,
        published_records=4,
        proof_only_records=2,
        accounted_records=6,
        published_modules=0,
        published_components=0,
        published_entities=0,
    )
    assert value.safe_projects()[0]["file_ids"] == sorted(
        row["id"] for row in request.record()["files"] if row["id"] != file["id"]
    )
    inventory.validate_source_inventory_seam_v3(value)


def test_wrong_private_record_kind_in_module_collection_is_a_bounded_rejection(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy, wire = inventory_inputs(tmp_path)
    payload = wire["semantic_payload"]
    module = payload["model"]["modules"].pop()
    row = next(
        row for row in payload["proof"]["discovered_records"] if row["collection"] == "modules"
    )
    component = {
        "kind": "component",
        "module_id": module["id"],
        "declaration_key": "WrongCollection",
        "recognition_evidence": ["trusted_callable"],
        "props_state": "no_props",
    }
    component["id"] = recompute_record_id(component)
    row["record"] = component
    payload["proof"]["excluded"] = [
        {"collection": "modules", "record_id": module["id"], "reason": "not_selected"}
    ]
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    with pytest.raises(ValueError, match="full Module owner"):
        inventory.retain_source_inventory_seam_v3(candidate, seal, assets)


@pytest.mark.parametrize("collection", ["projects", "files"])
def test_null_source_payload_is_rejected_by_existing_transport_schema(
    tmp_path: Path, collection: str
) -> None:
    seal, assets, request, policy, wire = inventory_inputs(tmp_path)
    row = next(
        row
        for row in wire["semantic_payload"]["proof"]["discovered_records"]
        if row["collection"] == collection
    )
    row["record"] = None
    with pytest.raises(ValidationError):
        candidate_for(seal, assets, request, policy, wire)


def test_source_reader_prefix_cannot_be_promoted_to_a_complete_inventory_seam(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy, wire = inventory_inputs(tmp_path)
    candidate = candidate_for(seal, assets, request, policy, wire)
    prefix = {"stage": "source_read", "known_files": 1, "observed_paths": ["package.json"]}
    with pytest.raises(TypeError):
        inventory.retain_source_inventory_seam_v3(candidate, cast(Any, prefix), assets)


def test_nonprogram_only_inventory_has_no_module_owner_requirement(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = inventory_inputs(
        tmp_path,
        extra_programs={"tsconfig.json": b'{"include":["src/**/*.d.ts"]}'},
    )
    candidate = candidate_for(seal, assets, request, policy, wire)
    value = inventory.retain_source_inventory_seam_v3(candidate, seal, assets)
    assert value.eligible_module_ids() == ()
    assert value.counts().published_entities == 0
    assert {row["path"] for row in value.safe_files()} == {
        "package.json",
        "tsconfig.json",
        "src/global.d.ts",
    }
    assert all(row.disposition == "published" for row in value.file_dispositions())
    assert value.counts().proof_discovered == value.counts().accounted_records == 4
    inventory.validate_source_inventory_seam_v3(value)


@pytest.mark.parametrize(
    "record_kind,field,value",
    [
        ("files", "size_bytes", 0),
        ("files", "roles", ["context"]),
        ("files", "effective_role", "context"),
        ("files", "path", "src/forged.tsx"),
        ("projects", "source_roots", ["other"]),
    ],
)
def test_all_public_source_fields_are_parent_owned(
    tmp_path: Path, record_kind: str, field: str, value: Any
) -> None:
    seal, assets, request, policy, wire = inventory_inputs(tmp_path)
    wire["semantic_payload"]["model"][record_kind][0][field] = value
    update_model_digest(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    with pytest.raises(ValueError, match="source metadata"):
        inventory.retain_source_inventory_seam_v3(candidate, seal, assets)


def test_unsupported_owner_needs_actual_unknown_frontier_coverage(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = inventory_inputs(
        tmp_path,
        extra_programs={"src/other.tsx": b"export const Other = () => null;"},
        targets=["path:src/page.tsx"],
    )
    payload = wire["semantic_payload"]
    other = next(row for row in payload["model"]["modules"] if row["path"] == "src/other.tsx")
    file = next(row for row in request.record()["files"] if row["path"] == other["path"])
    selected = next(row for row in payload["model"]["modules"] if row["path"] == "src/page.tsx")
    exclude_record(wire, "modules", other["id"], reason="unsupported", taints=[])
    exclude_record(wire, "files", file["id"], reason="unsupported", taints=[])
    relation = {
        "kind": "literal_dynamic_import",
        "source_id": selected["id"],
        "target": {
            "kind": "unresolved",
            "target_kind": "unresolved_relative",
            "safe_specifier": "unknown",
            "exported_name": None,
        },
        "role": "value",
        "reexport": False,
        "boundary_effect": "none",
    }
    relation["id"] = recompute_record_id(relation)
    payload["model"]["relations"] = [relation]
    payload["proof"]["discovered_records"].append(
        {"collection": "relations", "record_id": relation["id"], "taints": []}
    )
    payload["model"]["diagnostics"] = [
        {
            "code": "CSV-NEXT-UNSUPPORTED-001",
            "severity": "warning",
            "recoverable": True,
            "outcome": "complete",
            "ref_permission": "path_or_symbol",
            "path_ref": None,
            "symbol_ref": other["id"],
            "count": 1,
        }
    ]
    assert payload["model"]["coverage"]["unknown_relation_count"] == 0
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    with pytest.raises(ValueError, match="unsupported frontier"):
        inventory.retain_source_inventory_seam_v3(candidate, seal, assets)


def test_module_cannot_publish_when_its_owner_file_is_failed_even_with_missing_module_taint(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy, wire = inventory_inputs(tmp_path)
    payload = wire["semantic_payload"]
    file = next(row for row in request.record()["files"] if "program" in row["roles"])
    exclude_record(wire, "files", file["id"], reason="tainted", taints=["parse_file"])
    payload["proof"]["excluded"] = []
    payload["proof"]["failed"] = [
        {"collection": "files", "record_id": file["id"], "reason": "parse_file"}
    ]
    payload["proof"]["failure_roots"] = [
        {
            "id": "next:failure:" + "2" * 64,
            "kind": "parse_file",
            "collection": "files",
            "path_ref": file["path"],
            "record_ids": [file["id"]],
        }
    ]
    payload["proof"]["causal_edges"] = [
        {
            "source_id": "next:failure:" + "2" * 64,
            "record_id": file["id"],
            "rule": "file_all_records",
        }
    ]
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    with pytest.raises(ValueError, match="Module eligibility"):
        inventory.retain_source_inventory_seam_v3(candidate, seal, assets)
