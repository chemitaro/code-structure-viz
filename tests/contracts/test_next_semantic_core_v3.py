"""Full-Core reference corpus; no actual TypeScript/process/CLI certification."""

from copy import deepcopy
from importlib import import_module
from pathlib import Path, PurePosixPath
from typing import Any

import pytest

from code_structure_viz.adapters.next.source_acquisition import (
    SourceAcquisitionSeal,
    SourceDiscoveryIntent,
    seal_source_acquisition,
)
from code_structure_viz.source.git_repository import Commit, EnumeratedPath
from code_structure_viz.source.source_view import DescriptorAnchoredSourceReadSession
from tests.contracts import next_runtime_v2_reference as runtime
from tests.contracts.next_reference_validation import (
    COLLECTIONS,
    ModelRecordLimitError,
    _derive_required_root_seed_ids,
    derive_required_causal_edges,
    digest,
    recompute_record_id,
    validate_model,
)
from tests.contracts.next_runtime_v2_fixtures import analysis_context_fixture_v2
from tests.contracts.next_source_inventory_v3_reference import retain_source_inventory_seam_v3
from tests.contracts.test_next_exchange_v2 import shape_wire
from tests.contracts.test_next_process_observation_v2 import policy_fixture
from tests.contracts.test_next_request_frame_v2 import run_context
from tests.contracts.test_next_semantic_candidate_v2 import candidate_for
from tests.contracts.test_next_source_inventory_v3 import exclude_record, refresh_wire
from tests.contracts.test_next_trusted_environment_v2 import profile_members

SOURCE_BYTES = {
    "package.json": b'{"dependencies":{"next":"15"}}',
    "tsconfig.json": b'{"include":["src/**/*"]}',
    "src/button.tsx": b"export function Button() { return null; }\n",
    "src/index.ts": b'export { Button as Primary } from "./button";\n',
    "src/value.ts": b'const value = 1;\nexport { value as "opaque-public-name" };\n',
    "src/global.d.ts": b"declare interface Window { marker: string; }\n",
}
SOURCE_HASHES = {
    "package.json": "e1cba2a2526ff053f2d5931bf33cfc1e9eabf400fe0651ee341cb4dac23e29f4",
    "tsconfig.json": "d22d6c841f113e55b1ad3c0858b78148e6c5196bb88c91b8cd213f22b7524a9b",
    "src/button.tsx": "1dc7a2111f31e37e693b6b6befa5c7141411471168e20a2fc93c886382dfb862",
    "src/index.ts": "4a0d75a51f0ffd2f39ab05d7e739e1e6d045bb1e1e7177d34a32a80494592788",
    "src/value.ts": "cd622fd53afb830fdded48bebbd77ac22f2a22da282b34bdf977cb1b3006fadd",
    "src/global.d.ts": "434a26e7917f46b586775bc326d6ba34994e183118ffecf96c9caf8e09207643",
}
PROJECT_ID = "next:project:530b20c858c6039c19737f386f96cfabdadda6b8a0a1c98b5ca639beb2765c25"
MODULE_IDS = {
    "src/button.tsx": (
        "next:module:4130a3bcc0554a01d2f7111d613cdf150e6e3104575fe6a46ee5b057c6414b7d"
    ),
    "src/index.ts": "next:module:024a4e0cf9fee9411a055c04c95ff34b0909e69f80b3f4a9dff0cec438c9e4c3",
    "src/value.ts": "next:module:f8a3c82434f22cef3d54190f8a81a7b7788efcbac0cdbec594a7f1b0edbbf16b",
}
FACT_IDS = {
    "src/button.tsx": "next:fact:fad69b0c4f9499f6b03b9a3ed75bde3416620b9f724cb392ece749b1883ac3b7",
    "src/index.ts": "next:fact:5af45a15f0cfe0ec35e9c1fe62bea79bf1fefba6968ed6bfa69573c74ca51af0",
    "src/value.ts": "next:fact:75c153d8a3122c1eec2e9b23b9b93d7c7f237265c7b785b70b1c4c2e892dd8e9",
}
BUTTON_ID = "next:component:56983cafa7d11d2d42ecdca27a9061799006d6154f77cb9e4ee2a954d95659e8"
BUTTON_EXPORT_ID = "next:member:9a0c2c2d46a1812864d748f99ffa5448f755aa3edcd7894873c291d46c958279"
PRIMARY_EXPORT_ID = "next:member:0f044044b752a86452130d42b130ed1ea2952d101484e73c283db9d84094a1de"
REEXPORT_RELATION_ID = (
    "next:relation:4be44776badbed873e1ed93a50e33c8c248fb7a9dec5b75a9a78191df7efc03d"
)


def compatibility_preimage_literal_v3() -> dict[str, Any]:
    return {
        "semantic_schema": "code-structure-viz.semantic/v3",
        "identity_versions": {
            "project": 1,
            "file": 1,
            "module": 1,
            "component": 1,
            "member": 1,
            "relation": 1,
            "fact": 1,
            "props_ir": 1,
        },
        "algorithm_versions": {
            "recognition": 1,
            "export": 1,
            "props": 1,
            "relation": 1,
            "fact": 1,
            "boundary": 1,
            "identifier_unicode": "ecma-unicode-15.0",
            "identifier_unicode_table_digest": (
                "c9336daa555ce98e93cbd48e6b91df22f50a221881bd10b3ed79cf9180297969"
            ),
        },
        "semantic_profile_id": "next-trusted-profile-v1",
        "unicode_profile": {
            "profile_id": "unicode-15.0.0-nfc-v1",
            "unicode_version": "15.0.0",
            "normalization": "NFC",
            "algorithm_version": "unicode-nfc-15.0.0",
            "table_digest": "877b34f03bc09c193fb9014c381b3d3d980dea0676b942b4d54f56c1e11a6eb2",
            "full_scalar_kat_digest": (
                "61f9ea3772b20f223112b3709361f387cde38bf0c5b7c329aeae49fd0d7de3d5"
            ),
        },
        "runtime_binding_profile_id": "next-public-spawn-runtime-v1",
        "semantic_admission_profile_id": "next-source-inventory-safe-subset-v1",
        "typescript_identity": "typescript-5.9.2",
        "trusted_type_environment_digest": (
            "49458cb6f0f5097d486a2e4f7691f3f80d1e62ea4dbc65ceff00b862ce84e366"
        ),
        "portable_toolchain_fingerprint": (
            "4010221ccab7c9954ac52b6a0492b6baf67c41d7073fe1fdbfe1dc8ac773bf09"
        ),
    }


def export_observations_literal() -> list[dict[str, Any]]:
    """Worked syntax/witness literals, not the new validator's expected-value helper."""

    return [
        {
            "owner_module_id": MODULE_IDS["src/button.tsx"],
            "owner_file_path": "src/button.tsx",
            "byte_start": 0,
            "byte_end": 41,
            "token_identity": "c5a8c4d6b89384890dcfa31e00c713bbbc6eb3d5f95f02e204e96b817b271006",
            "syntax_identity": "export:src/button.tsx:0:41:named_export:Button",
            "syntax_kind": "named_export",
            "exported_name": "Button",
            "role": "value",
            "reexport": False,
            "star": False,
            "source_specifier": None,
            "imported_name": "Button",
            "resolution": "component",
            "component_id": BUTTON_ID,
            "target_declaration_id": BUTTON_ID,
            "resolved_source_module_id": MODULE_IDS["src/button.tsx"],
            "expanded_exported_name": "Button",
        },
        {
            "owner_module_id": MODULE_IDS["src/index.ts"],
            "owner_file_path": "src/index.ts",
            "byte_start": 9,
            "byte_end": 26,
            "token_identity": "0629e28100820ed2c813333c1cb6ee468df1cbe8342568cf400c347d27bc7317",
            "syntax_identity": "export:src/index.ts:9:26:reexport:Primary",
            "syntax_kind": "reexport",
            "exported_name": "Primary",
            "role": "value",
            "reexport": True,
            "star": False,
            "source_specifier": "./button",
            "imported_name": "Button",
            "resolution": "component",
            "component_id": BUTTON_ID,
            "target_declaration_id": BUTTON_ID,
            "resolved_source_module_id": MODULE_IDS["src/button.tsx"],
            "expanded_exported_name": "Button",
        },
        {
            "owner_module_id": MODULE_IDS["src/value.ts"],
            "owner_file_path": "src/value.ts",
            "byte_start": 26,
            "byte_end": 55,
            "token_identity": "5c9ef3c2108d37898e837134472acdff79f8da99522c50aa48d053c07b35857f",
            "syntax_identity": "export:src/value.ts:26:55:string_export",
            "syntax_kind": "string_export",
            "exported_name": None,
            "role": "value",
            "reexport": False,
            "star": False,
            "source_specifier": None,
            "imported_name": None,
            "string_names": {
                "imported": {
                    "form": "identifier",
                    "safe_identifier": "value",
                    "decoded_sha256": (
                        "845f2300840149e04bd7f052692d98162794772ccbdb815ac047b6fcf7fdeb8f"
                    ),
                },
                "exported": {
                    "form": "string",
                    "safe_identifier": None,
                    "decoded_sha256": (
                        "95e1681dd3a7182a48a163da69122ce2ef03c39477a0e8b98c4a1c5a31648f9a"
                    ),
                },
            },
            "resolution": "value",
            "resolution_basis": "primitive_const",
            "component_id": None,
            "target_declaration_id": None,
            "resolved_source_module_id": MODULE_IDS["src/value.ts"],
            "expanded_exported_name": None,
            "disposition": "intentional_unsupported",
        },
    ]


def core_inputs_v3(
    tmp_path: Path,
    *,
    sources: dict[str, bytes] | None = None,
    targets: list[str] | None = None,
    project_roots: tuple[str, ...] = (".",),
    max_entities: int = 500,
    requested_formats: list[str] | None = None,
    stdout_selector: str | None = None,
) -> tuple[
    SourceAcquisitionSeal,
    runtime.RetainedExecutionAssets,
    runtime.RetainedRequestFrameV2,
    dict[str, Any],
    dict[str, Any],
]:
    """Real frozen bytes/source graph; explicit reference semantic witnesses."""

    members = profile_members()
    members[runtime.ENTRYPOINT_MEMBER] = (
        "adapter",
        b"// CodeStructureViz-Adapter-Version: 0.2.0\n",
    )
    assets = runtime.retain_execution_assets_v1(members)
    trusted = runtime.trusted_environment_manifest_v2(assets)["environment_descriptor"]
    repository = tmp_path / "repo"
    repository.mkdir()
    source_bytes = SOURCE_BYTES if sources is None else sources
    for relative_path, content in source_bytes.items():
        path = repository / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    entries = tuple(EnumeratedPath(path, PurePosixPath(path)) for path in sorted(source_bytes))
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
        max_entities=max_entities,
    )
    assert type(seal) is SourceAcquisitionSeal
    request = runtime.build_request_frame_v2(
        seal,
        assets,
        analysis_context_fixture_v2(
            seal,
            assets,
            targets=targets or [],
            run_context={
                **run_context(),
                **(
                    {}
                    if max_entities == 500
                    else {
                        "budget_requested": max_entities,
                        "budget_resolved": max_entities,
                        "budget_source": "cli",
                    }
                ),
                "requested_formats": ["semantic-json"]
                if requested_formats is None
                else requested_formats,
                "stdout_selector": stdout_selector,
            },
        ),
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
    payload = wire["semantic_payload"]
    model, proof = payload["model"], payload["proof"]
    model["projects"] = request.record()["projects"]
    model["files"] = [
        {key: value for key, value in row.items() if key != "content_base64"}
        for row in request.record()["files"]
    ]
    model["modules"] = [
        {
            "kind": "module",
            "id": module_id,
            "project_id": PROJECT_ID,
            "path": path,
            "router_context": "none",
            "client_entry": False,
            "derived_roles": [],
        }
        for path, module_id in sorted(MODULE_IDS.items(), key=lambda row: row[1])
    ]
    model["facts"] = sorted(
        [
            {
                "kind": "router_context",
                "id": FACT_IDS[path],
                "owner_id": module_id,
                "value": "none",
            }
            for path, module_id in MODULE_IDS.items()
        ],
        key=lambda row: row["id"],
    )
    model["components"] = [
        {
            "kind": "component",
            "id": BUTTON_ID,
            "module_id": MODULE_IDS["src/button.tsx"],
            "declaration_key": "Button",
            "recognition_evidence": ["trusted_callable"],
            "props_state": "no_props",
        }
    ]
    model["members"] = [
        {
            "kind": "export_binding",
            "id": member_id,
            "owner_id": owner,
            "exported_name": name,
            "role": "value",
            "target_component_id": BUTTON_ID,
            "resolution_kind": "component",
            "reexport": reexport,
        }
        for member_id, owner, name, reexport in (
            (PRIMARY_EXPORT_ID, MODULE_IDS["src/index.ts"], "Primary", True),
            (BUTTON_EXPORT_ID, MODULE_IDS["src/button.tsx"], "Button", False),
        )
    ]
    model["relations"] = [
        {
            "kind": "static_import",
            "id": REEXPORT_RELATION_ID,
            "source_id": MODULE_IDS["src/index.ts"],
            "target": {"kind": "internal", "module_id": MODULE_IDS["src/button.tsx"]},
            "role": "value",
            "reexport": True,
            "boundary_effect": "none",
        }
    ]
    model["diagnostics"] = [
        {
            "code": "CSV-NEXT-UNSUPPORTED-001",
            "severity": "info",
            "recoverable": True,
            "outcome": "complete",
            "ref_permission": "symbol",
            "path_ref": None,
            "symbol_ref": MODULE_IDS["src/value.ts"],
            "count": 1,
        }
    ]
    model["coverage"]["non_component_value_export_count"] = 1
    proof["discovered_records"] = [
        {"collection": collection, "record_id": record["id"], "taints": []}
        for collection in COLLECTIONS
        for record in model[collection]
    ]
    proof["export_observations"] = export_observations_literal()
    if "path:src/value.ts" in (targets or []):
        for row in proof["export_observations"]:
            if row["syntax_kind"] == "string_export":
                row["disposition"] = "target_failure"
    proof["export_resolution_witness"] = [
        {"member_id": member_id, "resolution": "component", "component_id": BUTTON_ID}
        for member_id in (PRIMARY_EXPORT_ID, BUTTON_EXPORT_ID)
    ]
    proof["export_reexport_witness"] = [
        {
            "owner_module_id": MODULE_IDS["src/index.ts"],
            "owner_file_path": "src/index.ts",
            "byte_start": 9,
            "byte_end": 26,
            "token_identity": "0629e28100820ed2c813333c1cb6ee468df1cbe8342568cf400c347d27bc7317",
            "syntax_identity": "export:src/index.ts:9:26:reexport:Primary",
            "source_specifier": "./button",
            "imported_name": "Button",
            "original_exported_name": "Primary",
            "exported_name": "Primary",
            "resolved_source_module_id": MODULE_IDS["src/button.tsx"],
            "expanded_exported_name": "Button",
            "target_declaration_id": BUTTON_ID,
            "resolution": "component",
            "diagnostic": None,
        }
    ]
    refresh_wire(wire)
    return seal, assets, request, policy, wire


def test_v3_core_accepts_same_seal_source_bound_export_corpus(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    assert assets.adapter_identity()["version"] == "0.2.0"
    assert {str(file.path): file.sha256 for file in seal.source_view.files} == SOURCE_HASHES
    candidate = candidate_for(seal, assets, request, policy, wire)
    seam = retain_source_inventory_seam_v3(candidate, seal, assets)
    assert seam.counts().accounted_records == 17
    assert validate_model(wire["semantic_payload"]["model"]) == 4
    # Late import ensures the coherent lower-owner fixture executes before the first Red.
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    decision = core.decide_semantic_candidate_v3(candidate, seal, assets)
    assert type(decision) is core.ValidatedSemanticDecisionV3
    assert decision.transport_candidate() is candidate
    assert decision.source_seal() is seal
    assert decision.execution_assets() is assets
    assert decision.source_inventory_seam().counts().accounted_records == 17
    assert {key: decision.gate()[key] for key in ("actual", "allowed", "outcome")} == {
        "actual": 4,
        "allowed": True,
        "outcome": "complete",
    }


def test_v3_core_rejects_coordinated_export_observation_and_binding_omission(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    payload = wire["semantic_payload"]
    model, proof = payload["model"], payload["proof"]
    model["members"] = [row for row in model["members"] if row["id"] != BUTTON_EXPORT_ID]
    proof["discovered_records"] = [
        row for row in proof["discovered_records"] if row["record_id"] != BUTTON_EXPORT_ID
    ]
    proof["export_observations"] = [
        row
        for row in proof["export_observations"]
        if row["owner_module_id"] != MODULE_IDS["src/button.tsx"]
    ]
    proof["export_resolution_witness"] = [
        row for row in proof["export_resolution_witness"] if row["member_id"] != BUTTON_EXPORT_ID
    ]
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    with pytest.raises(ValueError, match="model_proof"):
        core.decide_semantic_candidate_v3(candidate, seal, assets)


def test_v3_core_rejects_stale_export_witness_after_fresh_source_acquisition(
    tmp_path: Path,
) -> None:
    sources = {
        **SOURCE_BYTES,
        "src/index.ts": b'export { Button as Secondary } from "./button";\n',
    }
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path, sources=sources)
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    with pytest.raises(ValueError, match="model_proof"):
        core.decide_semantic_candidate_v3(candidate, seal, assets)


@pytest.mark.parametrize(
    ("field", "wrong"),
    (
        ("resolved_source_module_id", MODULE_IDS["src/value.ts"]),
        ("expanded_exported_name", "Secondary"),
        ("target_declaration_id", "next:component:" + "f" * 64),
        ("resolution", "value"),
        ("syntax_identity", "export:src/index.ts:9:26:reexport:Secondary"),
        ("byte_start", 10),
        ("byte_end", 27),
    ),
)
def test_v3_core_rejects_reexport_witness_not_derived_from_same_source_graph(
    tmp_path: Path, field: str, wrong: Any
) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    witness = wire["semantic_payload"]["proof"]["export_reexport_witness"][0]
    witness[field] = wrong
    if field == "resolution":
        witness["target_declaration_id"] = None
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    with pytest.raises(ValueError, match="model_proof"):
        core.decide_semantic_candidate_v3(candidate, seal, assets)


def test_v3_core_rejects_missing_public_binding_with_complete_syntax_witness(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    model, proof = wire["semantic_payload"]["model"], wire["semantic_payload"]["proof"]
    model["members"] = [row for row in model["members"] if row["id"] != BUTTON_EXPORT_ID]
    proof["discovered_records"] = [
        row for row in proof["discovered_records"] if row["record_id"] != BUTTON_EXPORT_ID
    ]
    proof["export_resolution_witness"] = [
        row for row in proof["export_resolution_witness"] if row["member_id"] != BUTTON_EXPORT_ID
    ]
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    with pytest.raises(ValueError, match="model_proof"):
        core.decide_semantic_candidate_v3(candidate, seal, assets)


def test_v3_core_rejects_unbound_direct_export_resolution(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    observations = wire["semantic_payload"]["proof"]["export_observations"]
    direct = next(row for row in observations if row["syntax_kind"] == "named_export")
    direct["component_id"] = "next:component:" + "f" * 64
    direct["target_declaration_id"] = direct["component_id"]
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    with pytest.raises(ValueError, match="model_proof"):
        core.decide_semantic_candidate_v3(candidate, seal, assets)


def test_v3_core_rejects_reexport_observation_disagreeing_with_source_graph(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    observation = next(
        row
        for row in wire["semantic_payload"]["proof"]["export_observations"]
        if row["syntax_kind"] == "reexport"
    )
    observation["resolved_source_module_id"] = MODULE_IDS["src/value.ts"]
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    with pytest.raises(ValueError, match="model_proof"):
        core.decide_semantic_candidate_v3(candidate, seal, assets)


def test_v3_core_rejects_fabricated_string_export_resolution_basis(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    observation = next(
        row
        for row in wire["semantic_payload"]["proof"]["export_observations"]
        if row["syntax_kind"] == "string_export"
    )
    observation["resolution_basis"] = "open_world"
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    with pytest.raises(ValueError, match="model_proof"):
        core.decide_semantic_candidate_v3(candidate, seal, assets)


def test_v3_core_rejects_fabricated_public_export_coverage(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    wire["semantic_payload"]["model"]["coverage"]["non_component_value_export_count"] = 2
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    with pytest.raises(ValueError, match="model_proof"):
        core.decide_semantic_candidate_v3(candidate, seal, assets)


def test_v3_core_rejects_missing_intentional_string_export_diagnostic(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    wire["semantic_payload"]["model"]["diagnostics"] = []
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    with pytest.raises(ValueError, match="model_proof"):
        core.decide_semantic_candidate_v3(candidate, seal, assets)


def test_v3_core_rejects_causal_edges_without_a_valid_failure_root(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    wire["semantic_payload"]["proof"]["causal_edges"] = [
        {
            "source_id": MODULE_IDS["src/button.tsx"],
            "record_id": BUTTON_ID,
            "rule": "identity_dependency",
        }
    ]
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    with pytest.raises(ValueError, match="model_proof"):
        core.decide_semantic_candidate_v3(candidate, seal, assets)


def exclude_value_module_with_root_v3(
    wire: dict[str, Any], request: runtime.RetainedRequestFrameV2, kind: str
) -> str:
    """Worked full proof for an isolated owner failure, not a Core expected oracle."""

    payload = wire["semantic_payload"]
    file = next(row for row in request.record()["files"] if row["path"] == "src/value.ts")
    module_id, fact_id = MODULE_IDS["src/value.ts"], FACT_IDS["src/value.ts"]
    file_root = kind in {"parse_file", "read_file"}
    exclude_record(wire, "modules", module_id, reason="tainted", taints=[kind])
    exclude_record(wire, "facts", fact_id, reason="tainted", taints=[kind])
    exclude_record(
        wire,
        "files",
        file["id"],
        reason="tainted" if file_root else "failed",
        taints=[kind] if file_root else [],
    )
    if file_root:
        payload["proof"]["excluded"] = [
            row for row in payload["proof"]["excluded"] if row["record_id"] != file["id"]
        ]
        payload["proof"]["failed"] = [
            {"collection": "files", "record_id": file["id"], "reason": kind}
        ]
        payload["model"]["coverage"]["failed_files"] = [{"path": "src/value.ts", "reason": kind}]
    root_id = "next:failure:" + "1" * 64
    seeds = [module_id, fact_id] if kind == "boundary_derivation" else [module_id]
    if file_root:
        seeds = [file["id"], module_id, fact_id]
    root_rule = {
        "module_relation": "relation_dependency",
        "export_binding": "incoming_reexport",
        "boundary_derivation": "boundary_closure",
        "parse_file": "file_all_records",
        "read_file": "file_all_records",
    }[kind]
    payload["proof"]["failure_roots"] = [
        {
            "id": root_id,
            "collection": "files" if file_root else "modules",
            "kind": kind,
            "path_ref": "src/value.ts",
            "record_ids": sorted(seeds),
        }
    ]
    payload["proof"]["causal_edges"] = [
        {"source_id": root_id, "record_id": record_id, "rule": root_rule} for record_id in seeds
    ] + [{"source_id": module_id, "record_id": fact_id, "rule": "identity_dependency"}]
    payload["model"]["diagnostics"] = []
    payload["model"]["coverage"]["non_component_value_export_count"] = 0
    refresh_wire(wire)
    return str(file["id"])


@pytest.mark.parametrize("kind", ["module_relation", "export_binding", "boundary_derivation"])
def test_v3_core_keeps_untainted_file_private_with_its_failed_module(
    tmp_path: Path, kind: str
) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    file_id = exclude_value_module_with_root_v3(wire, request, kind)
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    decision = core.decide_semantic_candidate_v3(candidate, seal, assets)
    assert {key: decision.gate()[key] for key in ("actual", "allowed", "outcome")} == {
        "actual": 3,
        "allowed": True,
        "outcome": "partial_safe",
    }
    seam = decision.source_inventory_seam()
    disposition = next(row for row in seam.file_dispositions() if row.record_id == file_id)
    assert (disposition.disposition, disposition.reason) == ("excluded", "failed")
    source_row = next(
        row
        for row in wire["semantic_payload"]["proof"]["discovered_records"]
        if row["record_id"] == file_id
    )
    assert source_row["taints"] == [] and "record" not in source_row
    assert seam.counts().accounted_records == 17
    assert file_id not in seam.safe_projects()[0]["file_ids"]


def test_v3_core_rejects_out_of_scope_type_parameter_in_private_prop(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    model, proof = wire["semantic_payload"]["model"], wire["semantic_payload"]["proof"]
    model["components"][0]["props_state"] = "known"
    prop = {
        "kind": "prop",
        "owner_id": BUTTON_ID,
        "name": "scope",
        "optional": False,
        "readonly": False,
        "default_evidence": "none",
        "type_node": {"kind": "type_parameter", "ordinal": 0},
    }
    prop["id"] = recompute_record_id(prop)
    proof["discovered_records"].append(
        {"collection": "members", "record_id": prop["id"], "taints": [], "record": prop}
    )
    proof["excluded"].append(
        {"collection": "members", "record_id": prop["id"], "reason": "not_selected"}
    )
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    with pytest.raises(ValueError, match="model_proof"):
        core.decide_semantic_candidate_v3(candidate, seal, assets)


@pytest.mark.parametrize("kind", ["parse_file", "read_file"])
def test_v3_core_keeps_localized_acquired_file_failure_partial_safe(
    tmp_path: Path, kind: str
) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    file_id = exclude_value_module_with_root_v3(wire, request, kind)
    assert seal.source_view.failures == ()
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    decision = core.decide_semantic_candidate_v3(candidate, seal, assets)
    assert {key: decision.gate()[key] for key in ("actual", "allowed", "outcome")} == {
        "actual": 3,
        "allowed": True,
        "outcome": "partial_safe",
    }
    disposition = next(
        row
        for row in decision.source_inventory_seam().file_dispositions()
        if row.record_id == file_id
    )
    assert (disposition.disposition, disposition.reason) == ("failed", kind)


def test_v3_core_rejects_partial_publication_when_failed_source_has_open_dependency(
    tmp_path: Path,
) -> None:
    sources = {
        **SOURCE_BYTES,
        "src/value.ts": SOURCE_BYTES["src/value.ts"] + b"require(variable);\n",
    }
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path, sources=sources)
    exclude_value_module_with_root_v3(wire, request, "read_file")
    assert any(
        row["syntax_kind"] == "module_plane"
        for row in seal.final_plan["source_graph"]["open_edges"]
    )
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    decision = core.decide_semantic_candidate_v3(candidate, seal, assets)
    assert {key: decision.gate()[key] for key in ("actual", "allowed", "diagnostic_code")} == {
        "actual": None,
        "allowed": False,
        "diagnostic_code": "CSV-NEXT-SOURCE-003",
    }
    assert decision.gate()["payload_available"] is False


def test_v3_core_prioritizes_proven_selected_file_failure_over_source_locality(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path, targets=["path:src/value.ts"])
    exclude_value_module_with_root_v3(wire, request, "read_file")
    payload = wire["semantic_payload"]
    payload["proof"]["target_resolutions"] = [
        {
            "target_key": "path:src/value.ts",
            "status": "failed",
            "record_ids": [],
            "reason": "selected_taint",
        }
    ]
    payload["model"]["coverage"]["target_completeness"] = [
        {
            "target_key": "path:src/value.ts",
            "status": "failed",
            "record_ids": [],
            "reason": "selected_taint",
        }
    ]
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    decision = core.decide_semantic_candidate_v3(candidate, seal, assets)
    assert decision.gate()["diagnostic_code"] == "CSV-NEXT-TARGET-001"
    assert decision.gate()["actual"] is None
    assert decision.gate()["payload_available"] is False


def add_literal_reference_props_v3(wire: dict[str, Any], count: int) -> None:
    model, proof = wire["semantic_payload"]["model"], wire["semantic_payload"]["proof"]
    model["components"][0]["props_state"] = "known"
    for index in range(count):
        prop = {
            "kind": "prop",
            "owner_id": BUTTON_ID,
            "name": f"p{index}",
            "type_node": {"kind": "primitive", "name": "string"},
            "optional": False,
            "readonly": False,
            "default_evidence": "none",
        }
        prop["id"] = recompute_record_id(prop)
        model["members"].append(prop)
        proof["discovered_records"].append(
            {"collection": "members", "record_id": prop["id"], "taints": []}
        )
    for name in COLLECTIONS:
        model[name].sort(key=lambda row: row["id"])
    refresh_wire(wire)


@pytest.mark.parametrize("total", [10_000, 10_001])
def test_v3_core_measures_actual_record_boundary_including_private_source_rows(
    tmp_path: Path, total: int
) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    exclude_value_module_with_root_v3(wire, request, "module_relation")
    add_literal_reference_props_v3(wire, total - 17)
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    assert request.record()["limits"]["max_model_records"] == 10_000
    if total == 10_001:
        with pytest.raises(ModelRecordLimitError) as error:
            core.decide_semantic_candidate_v3(candidate, seal, assets)
        assert error.value.measured == 10_001
    else:
        decision = core.decide_semantic_candidate_v3(candidate, seal, assets)
        assert decision.source_inventory_seam().counts().accounted_records == 10_000
        assert decision.source_inventory_seam().counts().proof_only_records == 3
        assert decision.gate()["outcome"] == "partial_safe"


@pytest.mark.parametrize(
    ("field", "wrong"),
    [
        ("affected_ids", []),
        ("taint_frontier", [BUTTON_ID]),
        ("failed_files", [{"path": "src/button.tsx", "reason": "parse_file"}]),
    ],
)
def test_v3_core_rejects_coverage_disagreeing_with_full_proof(
    tmp_path: Path, field: str, wrong: Any
) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    exclude_value_module_with_root_v3(wire, request, "module_relation")
    wire["semantic_payload"]["model"]["coverage"][field] = wrong
    # Do not call the fixture census after deliberately changing proof-derived coverage.
    from tests.contracts.test_next_semantic_candidate_v2 import update_model_digest

    update_model_digest(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    with pytest.raises(ValueError, match="model_proof"):
        core.decide_semantic_candidate_v3(candidate, seal, assets)


def unknown_value_export_v3(wire: dict[str, Any]) -> None:
    """Literal unknown resolution for actually acquired makeValue() bytes."""

    payload = wire["semantic_payload"]
    observation = next(
        row
        for row in payload["proof"]["export_observations"]
        if row["syntax_kind"] == "string_export"
    )
    observation.update(
        byte_start=36,
        byte_end=65,
        token_identity="30e0406cb70e17554740988a07e231c0063fd13eb94cae9b821e4d311bed0ed3",
        syntax_identity="export:src/value.ts:36:65:string_export",
        resolution="unknown",
        resolution_basis="open_world",
        disposition="export_failure",
    )
    payload["model"]["diagnostics"] = []
    payload["model"]["coverage"]["non_component_value_export_count"] = 0
    refresh_wire(wire)


def test_v3_core_routes_source_proven_unknown_export_without_entity_measurement(
    tmp_path: Path,
) -> None:
    sources = {
        **SOURCE_BYTES,
        "src/value.ts": b'const value = makeValue();\nexport { value as "opaque-public-name" };\n',
    }
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path, sources=sources)
    unknown_value_export_v3(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    decision = core.decide_semantic_candidate_v3(candidate, seal, assets)
    assert {key: decision.gate()[key] for key in ("actual", "allowed", "diagnostic_code")} == {
        "actual": None,
        "allowed": False,
        "diagnostic_code": "CSV-NEXT-EXPORT-001",
    }
    assert decision.gate()["payload_available"] is False


def test_v3_core_inspection_retains_only_closed_expected_invariant_metadata(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    wire["semantic_payload"]["proof"]["export_observations"][0]["component_id"] = (
        "next:component:" + "f" * 64
    )
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    rejection = core.inspect_semantic_candidate_v3(candidate, seal, assets)
    assert type(rejection) is core.RejectedSemanticDecisionV3
    assert rejection.transport_candidate() is candidate
    assert rejection.source_seal() is seal
    assert rejection.execution_assets() is assets
    assert rejection.request_id == request.request_id
    assert rejection.failure() == {
        "stage": "response_validation",
        "diagnostic_code": "CSV-NEXT-PROTOCOL-001",
        "reason": "model_proof",
        "model_records": None,
    }
    assert not any(
        hasattr(rejection, name)
        for name in ("gate", "compatibility_descriptor", "source_inventory_seam")
    )


def test_v3_core_inspection_maps_source_payload_injection_to_closed_rejection(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    file = next(row for row in request.record()["files"] if row["path"] == "src/button.tsx")
    row = next(
        row
        for row in wire["semantic_payload"]["proof"]["discovered_records"]
        if row["record_id"] == file["id"]
    )
    row["record"] = {key: value for key, value in file.items() if key != "content_base64"}
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    rejection = core.inspect_semantic_candidate_v3(candidate, seal, assets)
    assert type(rejection) is core.RejectedSemanticDecisionV3
    assert rejection.failure() == {
        "stage": "response_validation",
        "diagnostic_code": "CSV-NEXT-PROTOCOL-001",
        "reason": "proof_source_owner",
        "model_records": None,
    }


def test_v3_core_retains_independent_ten_key_compatibility_literal(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    decision = core.decide_semantic_candidate_v3(candidate, seal, assets)
    descriptor = decision.compatibility_descriptor()
    assert descriptor == {
        "schema": "code-structure-viz.next-semantic-compatibility/v3",
        **compatibility_preimage_literal_v3(),
        "compatibility_id": "ecf055ae84276a9209e8cb65addabd0cbf4d882e0b76f54cc6f06208fa95880f",
    }
    descriptor["identity_versions"]["project"] = 99
    assert decision.compatibility_descriptor()["identity_versions"]["project"] == 1


def test_v3_core_compatibility_validator_rejects_rehashed_foreign_admission(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    validation = import_module("tests.contracts.next_semantic_core_v3_validation")
    descriptor = core.decide_semantic_candidate_v3(
        candidate, seal, assets
    ).compatibility_descriptor()
    validation.validate_compatibility_descriptor_v3(descriptor, candidate)
    descriptor["semantic_admission_profile_id"] = "foreign-admission-v1"
    descriptor["compatibility_id"] = digest(
        {
            key: value
            for key, value in descriptor.items()
            if key not in {"schema", "compatibility_id"}
        }
    )
    with pytest.raises(ValueError, match="compatibility"):
        validation.validate_compatibility_descriptor_v3(descriptor, candidate)


def test_v3_core_decision_validators_recheck_real_owner_chain(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    validation = import_module("tests.contracts.next_semantic_core_v3_validation")
    candidate = candidate_for(seal, assets, request, policy, wire)
    decision = core.decide_semantic_candidate_v3(candidate, seal, assets)
    validation.validate_semantic_decision_v3(decision)
    wire["semantic_payload"]["model"]["diagnostics"] = []
    refresh_wire(wire)
    bad_candidate = candidate_for(seal, assets, request, policy, wire)
    rejection = core.inspect_semantic_candidate_v3(bad_candidate, seal, assets)
    validation.validate_rejected_semantic_decision_v3(rejection)
    with pytest.raises(TypeError):
        validation.validate_semantic_decision_v3(rejection)
    with pytest.raises(TypeError):
        validation.validate_rejected_semantic_decision_v3(decision)


def test_v3_core_retains_actual_private_record_and_safe_entity_measurements(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    exclude_value_module_with_root_v3(wire, request, "module_relation")
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    decision = core.decide_semantic_candidate_v3(candidate, seal, assets)
    assert decision.measurements() == {
        "model_records": {"published": 14, "proof_only": 3, "accounted": 17, "limit": 10_000},
        "entity_budget": {"actual": 3, "limit": 500},
    }
    decision.measurements()["entity_budget"]["actual"] = 0
    assert decision.measurements()["entity_budget"]["actual"] == 3
    validation = import_module("tests.contracts.next_semantic_core_v3_validation")
    validation.validate_semantic_decision_v3(decision)


def test_v3_core_rejects_public_importer_omitted_from_failed_source_taint_region(
    tmp_path: Path,
) -> None:
    sources = {
        **SOURCE_BYTES,
        "src/button.tsx": SOURCE_BYTES["src/button.tsx"] + b'import "./value";\n',
    }
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path, sources=sources)
    exclude_value_module_with_root_v3(wire, request, "parse_file")
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    with pytest.raises(ValueError, match="model_proof"):
        core.decide_semantic_candidate_v3(candidate, seal, assets)


@pytest.mark.parametrize(
    ("field", "wrong"),
    [
        ("unknown_relation_count", 1),
        (
            "correlation_losses",
            [{"component_id": BUTTON_ID, "prop_ids": [BUTTON_EXPORT_ID], "signature_count": 2}],
        ),
    ],
)
def test_v3_core_rejects_unbound_public_relation_and_props_coverage(
    tmp_path: Path, field: str, wrong: Any
) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    wire["semantic_payload"]["model"]["coverage"][field] = wrong
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    with pytest.raises(ValueError, match="model_proof"):
        core.decide_semantic_candidate_v3(candidate, seal, assets)


def select_literal_button_target_v3(
    wire: dict[str, Any], request: runtime.RetainedRequestFrameV2
) -> None:
    file_id = next(
        row["id"] for row in request.record()["files"] if row["path"] == "src/button.tsx"
    )
    target = {
        "target_key": "path:src/button.tsx",
        "status": "resolved",
        "record_ids": sorted([file_id, MODULE_IDS["src/button.tsx"], BUTTON_ID]),
    }
    wire["semantic_payload"]["proof"]["target_resolutions"] = [target]
    wire["semantic_payload"]["model"]["coverage"]["target_completeness"] = [
        {**target, "status": "complete"}
    ]
    refresh_wire(wire)


@pytest.mark.parametrize(
    "reason",
    ["module_relation", "export_binding", "boundary_derivation", "not_selected", "target_excluded"],
)
def test_v3_core_keeps_independent_safe_target_available_with_private_owner(
    tmp_path: Path, reason: str
) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path, targets=["path:src/button.tsx"])
    if reason in {"not_selected", "target_excluded"}:
        file_id = next(
            row["id"] for row in request.record()["files"] if row["path"] == "src/value.ts"
        )
        for name, record_id in (
            ("modules", MODULE_IDS["src/value.ts"]),
            ("facts", FACT_IDS["src/value.ts"]),
            ("files", file_id),
        ):
            exclude_record(wire, name, record_id, reason=reason, taints=[])
        wire["semantic_payload"]["model"]["diagnostics"] = []
        wire["semantic_payload"]["model"]["coverage"]["non_component_value_export_count"] = 0
    else:
        exclude_value_module_with_root_v3(wire, request, reason)
    select_literal_button_target_v3(wire, request)
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    decision = core.decide_semantic_candidate_v3(candidate, seal, assets)
    assert decision.gate()["allowed"] is True
    assert decision.gate()["actual"] == 3
    assert decision.gate()["outcome"] == (
        "complete" if reason in {"not_selected", "target_excluded"} else "partial_safe"
    )


@pytest.mark.parametrize("ambient", [False, True])
def test_v3_core_preserves_complete_empty_and_safe_nonprogram_files(
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
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    decision = core.decide_semantic_candidate_v3(candidate, seal, assets)
    assert decision.gate()["outcome"] == "complete"
    assert decision.gate()["actual"] == 0
    assert decision.source_inventory_seam().counts().acquired_files == (3 if ambient else 2)


def test_v3_core_never_converts_another_source_owner_error_to_child_rejection(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    other_path = tmp_path / "other"
    other_path.mkdir()
    other_seal, _, _, _, _ = core_inputs_v3(other_path)
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    with pytest.raises(ValueError) as error:
        core.inspect_semantic_candidate_v3(candidate, other_seal, assets)
    assert type(error.value).__name__ != "SemanticCandidateInvalidErrorV3"


def test_v3_core_keeps_project_when_every_acquired_file_is_legitimately_proof_only(
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
        if name == "projects":
            continue
        for row in list(payload["model"][name]):
            exclude_record(wire, name, row["id"], reason="tainted", taints=["parse_file"])
    payload["proof"]["failure_roots"] = roots
    payload["proof"]["excluded"] = [
        row for row in payload["proof"]["excluded"] if row["collection"] != "files"
    ]
    payload["proof"]["failed"] = [
        {"collection": "files", "record_id": row["id"], "reason": "parse_file"}
        for row in request.record()["files"]
    ]
    full_discovery: dict[str, dict[str, dict[str, Any]]] = {name: {} for name in COLLECTIONS}
    for row in payload["proof"]["discovered_records"]:
        full_discovery[row["collection"]][row["record_id"]] = {
            **row,
            "record": original[row["record_id"]],
        }
    payload["proof"]["causal_edges"] = derive_required_causal_edges(
        payload["proof"], full_discovery
    )
    payload["proof"]["export_resolution_witness"] = []
    payload["model"]["diagnostics"] = []
    payload["model"]["coverage"]["non_component_value_export_count"] = 0
    payload["model"]["coverage"]["failed_files"] = sorted(
        [{"path": file["path"], "reason": "parse_file"} for file in request.record()["files"]],
        key=lambda row: str(row["path"]),
    )
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    decision = core.decide_semantic_candidate_v3(candidate, seal, assets)
    assert decision.gate()["outcome"] == "partial_safe" and decision.gate()["actual"] == 0
    assert decision.source_inventory_seam().safe_projects()[0]["file_ids"] == []
    assert decision.source_inventory_seam().counts().proof_only_records == 16


@pytest.mark.parametrize("entities", [500, 501])
def test_v3_core_entity_budget_measures_actual_frozen_programs_not_private_modules(
    tmp_path: Path, entities: int
) -> None:
    sources = {
        **SOURCE_BYTES,
        **{f"src/extra{index}.ts": b"const marker = 1;\n" for index in range(entities - 3)},
    }
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path, sources=sources)
    payload = wire["semantic_payload"]
    for file in request.record()["files"]:
        if not file["path"].startswith("src/extra"):
            continue
        module = {
            "kind": "module",
            "project_id": file["project_id"],
            "path": file["path"],
            "router_context": "none",
            "client_entry": False,
            "derived_roles": [],
        }
        module["id"] = recompute_record_id(module)
        fact = {"kind": "router_context", "owner_id": module["id"], "value": "none"}
        fact["id"] = recompute_record_id(fact)
        for name, row in (("modules", module), ("facts", fact)):
            payload["model"][name].append(row)
            payload["proof"]["discovered_records"].append(
                {"collection": name, "record_id": row["id"], "taints": []}
            )
    exclude_value_module_with_root_v3(wire, request, "module_relation")
    for name in COLLECTIONS:
        payload["model"][name].sort(key=lambda row: row["id"])
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    decision = core.decide_semantic_candidate_v3(candidate, seal, assets)
    assert decision.measurements()["entity_budget"] == {"actual": entities, "limit": 500}
    assert decision.gate()["original_outcome"] == "partial_safe"
    assert decision.gate()["payload_available"] is (entities == 500)
    assert decision.gate()["diagnostic_code"] == (None if entities == 500 else "CSV-NEXT-LIMIT-005")


def omit_selected_button_module_v3(wire: dict[str, Any], *, keep_component: bool = False) -> None:
    """Worked missing-owner corpus; incoming source remains acquired and unknown."""

    payload = wire["semantic_payload"]
    removed = {
        MODULE_IDS["src/button.tsx"],
        FACT_IDS["src/button.tsx"],
        BUTTON_ID,
        BUTTON_EXPORT_ID,
        PRIMARY_EXPORT_ID,
        REEXPORT_RELATION_ID,
    }
    if keep_component:
        removed.remove(BUTTON_ID)
    for name in COLLECTIONS:
        payload["model"][name] = [row for row in payload["model"][name] if row["id"] not in removed]
    payload["proof"]["discovered_records"] = [
        row for row in payload["proof"]["discovered_records"] if row["record_id"] not in removed
    ]
    payload["proof"]["export_observations"] = [
        row
        for row in payload["proof"]["export_observations"]
        if row["owner_module_id"] != MODULE_IDS["src/button.tsx"]
    ]
    for row in (
        payload["proof"]["export_observations"] + payload["proof"]["export_reexport_witness"]
    ):
        if row["owner_module_id"] == MODULE_IDS["src/index.ts"]:
            row.update(
                resolution="unknown",
                component_id=None,
                target_declaration_id=None,
                resolved_source_module_id=None,
            )
            if "component_id" in row and "diagnostic" in row:
                del row["component_id"]
    payload["proof"]["export_resolution_witness"] = []
    target = {
        "target_key": "path:src/button.tsx",
        "status": "failed",
        "record_ids": [],
        "reason": "component_only" if keep_component else "missing",
    }
    payload["proof"]["target_resolutions"] = [target]
    payload["model"]["coverage"]["target_completeness"] = [dict(target)]
    refresh_wire(wire)


def test_v3_core_selected_missing_module_routes_after_full_exception_proof(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path, targets=["path:src/button.tsx"])
    omit_selected_button_module_v3(wire)
    assert len(wire["semantic_payload"]["proof"]["discovered_records"]) == 11
    assert {str(file.path): file.sha256 for file in seal.source_view.files} == SOURCE_HASHES
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    decision = core.decide_semantic_candidate_v3(candidate, seal, assets)
    assert decision.transport_candidate() is candidate
    assert decision.source_seal() is seal
    assert decision.execution_assets() is assets
    assert decision.source_inventory_seam() is None
    assert decision.gate()["diagnostic_code"] == "CSV-NEXT-TARGET-001"
    assert decision.gate()["target_failures"] == [
        {"target_key": "path:src/button.tsx", "reason": "missing"}
    ]
    assert decision.gate()["payload_available"] is False
    assert decision.measurements() == {"model_records": None, "entity_budget": None}


def test_v3_core_selected_component_only_routes_after_full_exception_proof(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path, targets=["path:src/button.tsx"])
    omit_selected_button_module_v3(wire, keep_component=True)
    assert len(wire["semantic_payload"]["proof"]["discovered_records"]) == 12
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    decision = core.decide_semantic_candidate_v3(candidate, seal, assets)
    assert decision.source_inventory_seam() is None
    assert decision.gate()["diagnostic_code"] == "CSV-NEXT-TARGET-001"
    assert decision.gate()["target_failures"] == [
        {"target_key": "path:src/button.tsx", "reason": "component_only"}
    ]
    assert decision.measurements() == {"model_records": None, "entity_budget": None}
    assert candidate.semantic_payload()["model"]["members"] == []


def duplicate_selected_button_module_v3(wire: dict[str, Any]) -> None:
    """Two identical raw occurrences, one semantic discovery and no fake owner."""

    payload = wire["semantic_payload"]
    modules = payload["model"]["modules"]
    modules.append(deepcopy(next(row for row in modules if row["path"] == "src/button.tsx")))
    modules.sort(key=lambda row: row["id"])
    target = {
        "target_key": "path:src/button.tsx",
        "status": "failed",
        "record_ids": [],
        "reason": "duplicate",
    }
    payload["proof"]["target_resolutions"] = [target]
    payload["model"]["coverage"]["target_completeness"] = [dict(target)]
    refresh_wire(wire)
    # Raw occurrence accounting is not the unique proof census.
    payload["model"]["coverage"]["counts"]["discovered"] += 1
    payload["model_digest"] = digest(payload["model"])


def test_v3_core_selected_identical_duplicate_routes_after_full_exception_proof(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path, targets=["path:src/button.tsx"])
    duplicate_selected_button_module_v3(wire)
    payload = wire["semantic_payload"]
    assert len(payload["model"]["modules"]) == 4
    assert len(payload["proof"]["discovered_records"]) == 17
    assert payload["model"]["coverage"]["counts"]["published"] == 18
    assert payload["model"]["coverage"]["counts"]["discovered"] == 18
    candidate = candidate_for(seal, assets, request, policy, wire)
    raw_before = candidate.semantic_payload()
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    decision = core.decide_semantic_candidate_v3(candidate, seal, assets)
    assert decision.transport_candidate() is candidate
    assert decision.source_seal() is seal
    assert decision.execution_assets() is assets
    assert decision.source_inventory_seam() is None
    assert decision.gate()["diagnostic_code"] == "CSV-NEXT-TARGET-001"
    assert decision.gate()["target_failures"] == [
        {"target_key": "path:src/button.tsx", "reason": "duplicate"}
    ]
    assert decision.gate()["payload_available"] is False
    assert decision.measurements() == {"model_records": None, "entity_budget": None}
    assert candidate.semantic_payload() == raw_before


def append_literal_safe_target_v3(
    wire: dict[str, Any], request: runtime.RetainedRequestFrameV2, path: str
) -> None:
    file_id = next(row["id"] for row in request.record()["files"] if row["path"] == path)
    row = {
        "target_key": f"path:{path}",
        "status": "resolved",
        "record_ids": sorted([file_id, MODULE_IDS[path]]),
    }
    wire["semantic_payload"]["proof"]["target_resolutions"].append(row)
    wire["semantic_payload"]["model"]["coverage"]["target_completeness"].append(
        {**row, "status": "complete"}
    )
    refresh_wire(wire)


def test_v3_core_default_selection_preserves_missing_and_independent_safe_targets(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    assert request.record()["targets"] == []
    omit_selected_button_module_v3(wire)
    append_literal_safe_target_v3(wire, request, "src/index.ts")
    append_literal_safe_target_v3(wire, request, "src/value.ts")
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    decision = core.decide_semantic_candidate_v3(candidate, seal, assets)
    assert decision.gate()["target_failures"] == [
        {"target_key": "path:src/button.tsx", "reason": "missing"}
    ]
    assert len(candidate.semantic_payload()["proof"]["target_resolutions"]) == 3
    assert decision.gate()["diagnostic_code"] == "CSV-NEXT-TARGET-001"
    assert decision.source_inventory_seam() is None


def apply_cardinality_fixture_v3(wire: dict[str, Any], kind: str) -> None:
    if kind == "duplicate":
        duplicate_selected_button_module_v3(wire)
    else:
        omit_selected_button_module_v3(wire, keep_component=kind == "component_only")


def refresh_cardinality_fixture_v3(wire: dict[str, Any], kind: str) -> None:
    refresh_wire(wire)
    if kind == "duplicate":
        wire["semantic_payload"]["model"]["coverage"]["counts"]["discovered"] += 1
        wire["semantic_payload"]["model_digest"] = digest(wire["semantic_payload"]["model"])


@pytest.mark.parametrize("kind", ["missing", "component_only", "duplicate"])
def test_v3_core_mixed_cardinality_targets_keep_literal_safe_resolution(
    tmp_path: Path, kind: str
) -> None:
    targets = ["path:src/button.tsx", "path:src/index.ts"]
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path, targets=targets)
    apply_cardinality_fixture_v3(wire, kind)
    append_literal_safe_target_v3(wire, request, "src/index.ts")
    refresh_cardinality_fixture_v3(wire, kind)
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    validation = import_module("tests.contracts.next_semantic_core_v3_validation")
    decision = core.decide_semantic_candidate_v3(candidate, seal, assets)
    assert decision.gate()["target_failures"] == [
        {"target_key": "path:src/button.tsx", "reason": kind}
    ]
    rows = candidate.semantic_payload()["proof"]["target_resolutions"]
    assert rows[1]["status"] == "resolved" and len(rows[1]["record_ids"]) == 2
    validation.validate_semantic_decision_v3(decision)
    original_gate = decision.gate()
    decision.gate()["target_failures"][0]["reason"] = "out_of_scope"
    decision.measurements()["model_records"] = {"accounted": 0}
    assert decision.gate() == original_gate
    assert decision.measurements() == {"model_records": None, "entity_budget": None}


@pytest.mark.parametrize("kind", ["missing", "component_only", "duplicate"])
@pytest.mark.parametrize(
    "mutation",
    [
        "source_discovery_omission",
        "source_record_injection",
        "semantic_discovery_duplicate",
        "unrelated_file_exclusion",
        "dangling_record",
        "incoming_witness",
        "wrong_target_reason",
        "raw_module_count",
    ],
)
def test_v3_core_cardinality_is_not_an_exemption_from_full_proof(
    tmp_path: Path, kind: str, mutation: str
) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path, targets=["path:src/button.tsx"])
    apply_cardinality_fixture_v3(wire, kind)
    payload = wire["semantic_payload"]
    model, proof = payload["model"], payload["proof"]
    file = next(row for row in request.record()["files"] if row["path"] == "src/index.ts")
    if mutation == "source_discovery_omission":
        proof["discovered_records"] = [
            row for row in proof["discovered_records"] if row["record_id"] != file["id"]
        ]
    elif mutation == "source_record_injection":
        row = next(row for row in proof["discovered_records"] if row["record_id"] == file["id"])
        row["record"] = {key: value for key, value in file.items() if key != "content_base64"}
    elif mutation == "semantic_discovery_duplicate":
        proof["discovered_records"].append(
            deepcopy(
                next(row for row in proof["discovered_records"] if row["collection"] == "modules")
            )
        )
    elif mutation == "unrelated_file_exclusion":
        exclude_record(wire, "files", file["id"], reason="not_selected", taints=[])
    elif mutation == "dangling_record":
        record = next(
            row for row in model["facts"] if row["owner_id"] == MODULE_IDS["src/index.ts"]
        )
        old_id = record["id"]
        record["owner_id"] = "next:module:" + "f" * 64
        record["id"] = recompute_record_id(record)
        next(row for row in proof["discovered_records"] if row["record_id"] == old_id)[
            "record_id"
        ] = record["id"]
        model["facts"].sort(key=lambda row: row["id"])
    elif mutation == "incoming_witness":
        proof["export_reexport_witness"][0]["syntax_identity"] = (
            "export:src/index.ts:9:26:reexport:Secondary"
        )
    elif mutation == "wrong_target_reason":
        proof["target_resolutions"][0]["reason"] = "out_of_scope"
        model["coverage"]["target_completeness"][0]["reason"] = "out_of_scope"
    refresh_cardinality_fixture_v3(wire, kind)
    if mutation == "raw_module_count":
        model["coverage"]["counts"]["modules"] += 1
        payload["model_digest"] = digest(model)
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    validation = import_module("tests.contracts.next_semantic_core_v3_validation")
    rejection = core.inspect_semantic_candidate_v3(candidate, seal, assets)
    assert type(rejection) is core.RejectedSemanticDecisionV3
    assert rejection.failure()["diagnostic_code"] == "CSV-NEXT-PROTOCOL-001"
    assert rejection.failure()["model_records"] is None
    validation.validate_rejected_semantic_decision_v3(rejection)


@pytest.mark.parametrize("mutation", ["not_selected", "contradictory"])
def test_v3_core_does_not_generalize_duplicate_exception(tmp_path: Path, mutation: str) -> None:
    targets = ["path:src/index.ts"] if mutation == "not_selected" else ["path:src/button.tsx"]
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path, targets=targets)
    duplicate_selected_button_module_v3(wire)
    payload = wire["semantic_payload"]
    if mutation == "not_selected":
        payload["proof"]["target_resolutions"] = []
        payload["model"]["coverage"]["target_completeness"] = []
        append_literal_safe_target_v3(wire, request, "src/index.ts")
    else:
        next(row for row in payload["model"]["modules"] if row["path"] == "src/button.tsx")[
            "client_entry"
        ] = True
    refresh_cardinality_fixture_v3(wire, "duplicate")
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    rejection = core.inspect_semantic_candidate_v3(candidate, seal, assets)
    assert type(rejection) is core.RejectedSemanticDecisionV3
    assert rejection.failure()["diagnostic_code"] == "CSV-NEXT-PROTOCOL-001"


@pytest.mark.parametrize("kind", ["component_only", "duplicate"])
def test_v3_core_default_selection_also_preserves_other_cardinality_failures(
    tmp_path: Path, kind: str
) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    apply_cardinality_fixture_v3(wire, kind)
    append_literal_safe_target_v3(wire, request, "src/index.ts")
    append_literal_safe_target_v3(wire, request, "src/value.ts")
    refresh_cardinality_fixture_v3(wire, kind)
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    decision = core.decide_semantic_candidate_v3(candidate, seal, assets)
    assert decision.gate()["target_failures"] == [
        {"target_key": "path:src/button.tsx", "reason": kind}
    ]
    assert len(candidate.semantic_payload()["proof"]["target_resolutions"]) == 3
    assert decision.source_inventory_seam() is None


@pytest.mark.parametrize("mode", ["over_limit", "invalid_proof", "proven_target"])
def test_v3_core_actual_record_limit_preserves_proof_and_target_precedence(
    tmp_path: Path, mode: str
) -> None:
    targets = ["path:src/value.ts"] if mode == "proven_target" else []
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path, targets=targets)
    exclude_value_module_with_root_v3(wire, request, "module_relation")
    add_literal_reference_props_v3(wire, 10_001 - 17)
    payload = wire["semantic_payload"]
    if mode == "invalid_proof":
        payload["proof"]["causal_edges"].pop()
    elif mode == "proven_target":
        row = {
            "target_key": "path:src/value.ts",
            "status": "failed",
            "record_ids": [],
            "reason": "selected_taint",
        }
        payload["proof"]["target_resolutions"] = [row]
        payload["model"]["coverage"]["target_completeness"] = [dict(row)]
    refresh_wire(wire)
    assert len(payload["proof"]["discovered_records"]) == 10_001
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    validation = import_module("tests.contracts.next_semantic_core_v3_validation")
    result = core.inspect_semantic_candidate_v3(candidate, seal, assets)
    if mode == "proven_target":
        assert type(result) is core.ValidatedSemanticDecisionV3
        assert result.gate()["diagnostic_code"] == "CSV-NEXT-TARGET-001"
        assert result.gate()["target_failures"] == [
            {"target_key": "path:src/value.ts", "reason": "selected_taint"}
        ]
        # The Module exists in private D: it is not a selected missing-owner exception.
        assert result.source_inventory_seam() is not None
        assert result.measurements() == {"model_records": None, "entity_budget": None}
        validation.validate_semantic_decision_v3(result)
    else:
        assert type(result) is core.RejectedSemanticDecisionV3
        if mode == "over_limit":
            assert result.failure() == {
                "stage": "model_validation",
                "diagnostic_code": "CSV-NEXT-LIMIT-005",
                "reason": "max_model_records",
                "model_records": 10_001,
            }
        else:
            assert result.failure()["diagnostic_code"] == "CSV-NEXT-PROTOCOL-001"
            assert result.failure()["model_records"] is None
        validation.validate_rejected_semantic_decision_v3(result)


def simple_multiple_projects_fixture_v3(tmp_path: Path, *, selected: bool) -> tuple[Any, ...]:
    sources = {
        root + suffix: content
        for root in ("apps/a", "apps/b")
        for suffix, content in (
            ("/package.json", b'{"dependencies":{"next":"15"}}'),
            ("/tsconfig.json", b'{"include":["src/**/*"]}'),
            ("/src/value.ts", b"const marker = 1;\n"),
            ("/src/global.d.ts", b"declare interface Window { marker: string; }\n"),
        )
    }
    seal, assets, request, policy, wire = core_inputs_v3(
        tmp_path,
        sources=sources,
        project_roots=("apps/a", "apps/b"),
        targets=["path:apps/b/src/value.ts"] if selected else [],
    )
    payload = wire["semantic_payload"]
    model, proof = payload["model"], payload["proof"]
    for name in ("modules", "components", "members", "relations", "facts"):
        model[name] = []
    for file in request.record()["files"]:
        if "program" not in file["roles"]:
            continue
        module = {
            "kind": "module",
            "project_id": file["project_id"],
            "path": file["path"],
            "router_context": "none",
            "client_entry": False,
            "derived_roles": [],
        }
        module["id"] = recompute_record_id(module)
        fact = {"kind": "router_context", "owner_id": module["id"], "value": "none"}
        fact["id"] = recompute_record_id(fact)
        model["modules"].append(module)
        model["facts"].append(fact)
    for name in COLLECTIONS:
        model[name].sort(key=lambda row: row["id"])
    original = {row["id"]: deepcopy(row) for name in COLLECTIONS for row in model[name]}
    model["diagnostics"] = []
    model["coverage"]["non_component_value_export_count"] = 0
    proof.update(
        discovered_records=[
            {"collection": name, "record_id": row["id"], "taints": []}
            for name in COLLECTIONS
            for row in model[name]
        ],
        export_observations=[],
        export_resolution_witness=[],
        export_reexport_witness=[],
    )
    for index, file in enumerate(request.record()["files"]):
        if file["project_id"] != request.record()["projects"][0]["id"]:
            continue
        owned = [file["id"]]
        modules = [row for row in model["modules"] if row["path"] == file["path"]]
        if modules:
            owned.append(modules[0]["id"])
            fact = next(row for row in model["facts"] if row["owner_id"] == modules[0]["id"])
            owned.append(fact["id"])
            exclude_record(
                wire, "modules", modules[0]["id"], reason="tainted", taints=["parse_file"]
            )
            exclude_record(wire, "facts", fact["id"], reason="tainted", taints=["parse_file"])
        exclude_record(wire, "files", file["id"], reason="tainted", taints=["parse_file"])
        proof["excluded"] = [row for row in proof["excluded"] if row["record_id"] != file["id"]]
        proof["failed"].append(
            {"collection": "files", "record_id": file["id"], "reason": "parse_file"}
        )
        proof["failure_roots"].append(
            {
                "id": "next:failure:" + f"{index + 1:064x}",
                "collection": "files",
                "kind": "parse_file",
                "path_ref": file["path"],
                "record_ids": sorted(owned),
            }
        )
    full: dict[str, dict[str, dict[str, Any]]] = {name: {} for name in COLLECTIONS}
    for row in proof["discovered_records"]:
        full[row["collection"]][row["record_id"]] = {**row, "record": original[row["record_id"]]}
    proof["causal_edges"] = derive_required_causal_edges(proof, full)
    model["coverage"]["failed_files"] = sorted(
        [
            {"path": file["path"], "reason": "parse_file"}
            for file in request.record()["files"]
            if file["project_id"] == request.record()["projects"][0]["id"]
        ],
        key=lambda row: row["path"],
    )
    if selected:
        file = next(
            row for row in request.record()["files"] if row["path"] == "apps/b/src/value.ts"
        )
        module = next(row for row in model["modules"] if row["path"] == file["path"])
        target = {
            "target_key": "path:apps/b/src/value.ts",
            "status": "resolved",
            "record_ids": sorted([file["id"], module["id"]]),
        }
        proof["target_resolutions"] = [target]
        model["coverage"]["target_completeness"] = [{**target, "status": "complete"}]
    refresh_wire(wire)
    return seal, assets, request, policy, wire


@pytest.mark.parametrize("selected", [False, True])
def test_v3_core_empty_project_membership_never_erases_an_independent_safe_project(
    tmp_path: Path, selected: bool
) -> None:
    seal, assets, request, policy, wire = simple_multiple_projects_fixture_v3(
        tmp_path, selected=selected
    )
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    validation = import_module("tests.contracts.next_semantic_core_v3_validation")
    decision = core.decide_semantic_candidate_v3(candidate, seal, assets)
    projects = {row["root"]: row for row in decision.source_inventory_seam().safe_projects()}
    assert set(projects) == {"apps/a", "apps/b"}
    assert projects["apps/a"]["file_ids"] == []
    assert projects["apps/b"]["file_ids"] == request.record()["projects"][1]["file_ids"]
    assert decision.gate()["outcome"] == "partial_safe"
    assert decision.gate()["payload_available"] is True
    assert decision.measurements() == {
        "model_records": {"published": 8, "proof_only": 6, "accounted": 14, "limit": 10_000},
        "entity_budget": {"actual": 1, "limit": 500},
    }
    assert decision.locality()["affected_paths"] == sorted(
        file["path"] for file in request.record()["files"] if file["path"].startswith("apps/a/")
    )
    validation.validate_semantic_decision_v3(decision)


@pytest.mark.parametrize("mode", ["represented", "missing_count", "missing_diagnostic"])
def test_v3_core_unsupported_owner_needs_a_represented_frontier_not_a_failure(
    tmp_path: Path, mode: str
) -> None:
    sources = {
        **SOURCE_BYTES,
        "src/index.ts": SOURCE_BYTES["src/index.ts"] + b'import("./not-found");\n',
        "src/value.ts": b"const value = 1;\n",
    }
    seal, assets, request, policy, wire = core_inputs_v3(
        tmp_path, sources=sources, targets=["path:src/button.tsx"]
    )
    payload = wire["semantic_payload"]
    model, proof = payload["model"], payload["proof"]
    file = next(row for row in request.record()["files"] if row["path"] == "src/value.ts")
    exclude_record(wire, "modules", MODULE_IDS["src/value.ts"], reason="unsupported", taints=[])
    exclude_record(wire, "facts", FACT_IDS["src/value.ts"], reason="unsupported", taints=[])
    exclude_record(wire, "files", file["id"], reason="unsupported", taints=[])
    proof["export_observations"] = [
        row for row in proof["export_observations"] if row["owner_file_path"] != "src/value.ts"
    ]
    relation = {
        "kind": "literal_dynamic_import",
        "source_id": MODULE_IDS["src/index.ts"],
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
    model["relations"].append(relation)
    model["relations"].sort(key=lambda row: row["id"])
    proof["discovered_records"].append(
        {"collection": "relations", "record_id": relation["id"], "taints": []}
    )
    model["coverage"]["unknown_relation_count"] = 0 if mode == "missing_count" else 1
    model["coverage"]["non_component_value_export_count"] = 0
    if mode == "missing_diagnostic":
        model["diagnostics"] = []
    select_literal_button_target_v3(wire, request)
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    validation = import_module("tests.contracts.next_semantic_core_v3_validation")
    result = core.inspect_semantic_candidate_v3(candidate, seal, assets)
    assert proof["failure_roots"] == []
    assert all(row["taints"] == [] for row in proof["discovered_records"])
    assert seal.final_plan["source_graph"]["open_edges"]
    if mode == "represented":
        assert type(result) is core.ValidatedSemanticDecisionV3
        assert result.gate()["outcome"] == "complete"
        assert result.gate()["payload_available"] is True
        assert result.measurements() == {
            "model_records": {"published": 15, "proof_only": 3, "accounted": 18, "limit": 10_000},
            "entity_budget": {"actual": 3, "limit": 500},
        }
        assert (
            next(
                row
                for row in result.source_inventory_seam().file_dispositions()
                if row.record_id == file["id"]
            ).reason
            == "unsupported"
        )
        validation.validate_semantic_decision_v3(result)
    else:
        assert type(result) is core.RejectedSemanticDecisionV3
        assert result.failure()["diagnostic_code"] == "CSV-NEXT-PROTOCOL-001"
        validation.validate_rejected_semantic_decision_v3(result)


@pytest.mark.parametrize("mode", ["proven", "file_seed", "causal_edge", "file_taint", "root_kind"])
def test_v3_core_missing_target_keeps_full_unrelated_file_root_proof(
    tmp_path: Path, mode: str
) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path, targets=["path:src/button.tsx"])
    omit_selected_button_module_v3(wire)
    file_id = exclude_value_module_with_root_v3(wire, request, "parse_file")
    proof = wire["semantic_payload"]["proof"]
    if mode == "file_seed":
        proof["failure_roots"][0]["record_ids"].remove(file_id)
        proof["causal_edges"] = [
            row for row in proof["causal_edges"] if row["record_id"] != file_id
        ]
    elif mode == "causal_edge":
        proof["causal_edges"].pop()
    elif mode == "file_taint":
        next(row for row in proof["discovered_records"] if row["record_id"] == file_id)[
            "taints"
        ] = []
    elif mode == "root_kind":
        proof["failure_roots"][0]["kind"] = "read_file"
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    validation = import_module("tests.contracts.next_semantic_core_v3_validation")
    result = core.inspect_semantic_candidate_v3(candidate, seal, assets)
    if mode == "proven":
        assert type(result) is core.ValidatedSemanticDecisionV3
        assert result.gate()["target_failures"] == [
            {"target_key": "path:src/button.tsx", "reason": "missing"}
        ]
        assert result.locality()["affected_paths"] == ["src/value.ts"]
        assert result.source_inventory_seam() is None
        validation.validate_semantic_decision_v3(result)
    else:
        assert type(result) is core.RejectedSemanticDecisionV3
        assert result.failure()["diagnostic_code"] == "CSV-NEXT-PROTOCOL-001"
        validation.validate_rejected_semantic_decision_v3(result)


def test_v3_core_component_only_does_not_exempt_props_repository_references(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path, targets=["path:src/button.tsx"])
    omit_selected_button_module_v3(wire, keep_component=True)
    add_literal_reference_props_v3(wire, 1)
    model = wire["semantic_payload"]["model"]
    next(row for row in model["members"] if row["kind"] == "prop")["type_node"] = {
        "kind": "reference",
        "scope": "repository",
        "module": MODULE_IDS["src/button.tsx"],
        "exported_name": "Props",
        "type_arguments": [],
    }
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    rejection = core.inspect_semantic_candidate_v3(candidate, seal, assets)
    assert type(rejection) is core.RejectedSemanticDecisionV3
    assert rejection.failure()["diagnostic_code"] == "CSV-NEXT-PROTOCOL-001"


def test_v3_core_wrong_private_module_kind_is_a_bounded_rejection_not_a_classifier_error(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    exclude_value_module_with_root_v3(wire, request, "module_relation")
    proof = wire["semantic_payload"]["proof"]
    module = next(
        row for row in proof["discovered_records"] if row["record_id"] == MODULE_IDS["src/value.ts"]
    )
    fact = next(
        row for row in proof["discovered_records"] if row["record_id"] == FACT_IDS["src/value.ts"]
    )
    module["record"] = deepcopy(fact["record"])
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    validation = import_module("tests.contracts.next_semantic_core_v3_validation")
    rejection = core.inspect_semantic_candidate_v3(candidate, seal, assets)
    assert type(rejection) is core.RejectedSemanticDecisionV3
    assert rejection.failure()["diagnostic_code"] == "CSV-NEXT-PROTOCOL-001"
    assert rejection.failure()["model_records"] is None
    validation.validate_rejected_semantic_decision_v3(rejection)


@pytest.mark.parametrize("kind", ["parse_file", "read_file"])
def test_v3_core_cannot_publish_a_context_file_in_the_reverse_failure_closure(
    tmp_path: Path, kind: str
) -> None:
    sources = {
        **SOURCE_BYTES,
        "src/global.d.ts": b'import { value } from "./value";\n' + SOURCE_BYTES["src/global.d.ts"],
    }
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path, sources=sources)
    exclude_value_module_with_root_v3(wire, request, kind)
    candidate = candidate_for(seal, assets, request, policy, wire)
    graph = seal.final_plan["source_graph"]
    paths = {row["id"]: row["path"] for row in graph["nodes"]}
    assert ("src/global.d.ts", "src/value.ts") in {
        (paths[row["source"]], paths[row["target"]]) for row in graph["edges"]
    }
    assert graph["open_edges"] == [] and seal.source_view.failures == ()
    context = next(row for row in request.record()["files"] if row["path"] == "src/global.d.ts")
    discovery = next(
        row
        for row in candidate.semantic_payload()["proof"]["discovered_records"]
        if row["record_id"] == context["id"]
    )
    assert context["roles"] == ["context"] and discovery["taints"] == []
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    validation = import_module("tests.contracts.next_semantic_core_v3_validation")
    decision = core.decide_semantic_candidate_v3(candidate, seal, assets)
    assert decision.locality()["reverse_affected_paths"] == ["src/global.d.ts", "src/value.ts"]
    assert decision.locality()["localized"] is False
    assert decision.locality()["target_tainted"] is False
    assert decision.gate()["diagnostic_code"] == "CSV-NEXT-SOURCE-003"
    assert decision.gate()["payload_available"] is False
    assert decision.gate()["artifact_paths"] == []
    # Publication eligibility is unchanged; no context Module or File taint is invented.
    seam = decision.source_inventory_seam()
    assert seam is not None
    assert "src/global.d.ts" in {row["path"] for row in seam.safe_files()}
    assert "src/global.d.ts" not in {
        row["path"] for row in candidate.semantic_payload()["model"]["modules"]
    }
    validation.validate_semantic_decision_v3(decision)


@pytest.mark.parametrize("relationship", ["forward_only", "transitive_reverse"])
def test_v3_core_context_safety_depends_on_reverse_not_forward_reachability(
    tmp_path: Path, relationship: str
) -> None:
    sources = dict(SOURCE_BYTES)
    if relationship == "forward_only":
        sources["src/value.ts"] += b'import "./global";\n'
        expected_reverse = ["src/value.ts"]
    else:
        sources["src/bridge.d.ts"] = b'import "./value";\n'
        sources["src/global.d.ts"] = b'import "./bridge";\n' + SOURCE_BYTES["src/global.d.ts"]
        expected_reverse = ["src/bridge.d.ts", "src/global.d.ts", "src/value.ts"]
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path, sources=sources)
    exclude_value_module_with_root_v3(wire, request, "parse_file")
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    validation = import_module("tests.contracts.next_semantic_core_v3_validation")
    decision = core.decide_semantic_candidate_v3(candidate, seal, assets)
    available = relationship == "forward_only"
    assert decision.locality()["reverse_affected_paths"] == expected_reverse
    assert "src/global.d.ts" in decision.locality()["affected_paths"]
    assert decision.locality()["localized"] is available
    assert decision.gate()["payload_available"] is available
    assert decision.gate()["diagnostic_code"] == (None if available else "CSV-NEXT-SOURCE-003")
    if available:
        assert decision.gate()["outcome"] == "partial_safe"
    validation.validate_semantic_decision_v3(decision)


@pytest.mark.parametrize("context_failed", [False, True])
def test_v3_core_multiple_roots_use_the_actual_public_file_projection(
    tmp_path: Path, context_failed: bool
) -> None:
    sources = {
        **SOURCE_BYTES,
        "src/global.d.ts": b'import "./value";\n' + SOURCE_BYTES["src/global.d.ts"],
    }
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path, sources=sources)
    exclude_value_module_with_root_v3(wire, request, "parse_file")
    payload = wire["semantic_payload"]
    proof = payload["proof"]
    failed_path = "src/global.d.ts" if context_failed else "package.json"
    file = next(row for row in request.record()["files"] if row["path"] == failed_path)
    exclude_record(wire, "files", file["id"], reason="tainted", taints=["read_file"])
    proof["excluded"] = [row for row in proof["excluded"] if row["record_id"] != file["id"]]
    proof["failed"].append({"collection": "files", "record_id": file["id"], "reason": "read_file"})
    root_id = "next:failure:" + "2" * 64
    proof["failure_roots"].append(
        {
            "id": root_id,
            "collection": "files",
            "kind": "read_file",
            "path_ref": failed_path,
            "record_ids": [file["id"]],
        }
    )
    proof["causal_edges"].append(
        {"source_id": root_id, "record_id": file["id"], "rule": "file_all_records"}
    )
    payload["model"]["coverage"]["failed_files"] = sorted(
        [
            {"path": failed_path, "reason": "read_file"},
            {"path": "src/value.ts", "reason": "parse_file"},
        ],
        key=lambda row: row["path"],
    )
    refresh_wire(wire)
    candidate = candidate_for(seal, assets, request, policy, wire)
    core = import_module("tests.contracts.next_semantic_core_v3_reference")
    validation = import_module("tests.contracts.next_semantic_core_v3_validation")
    decision = core.decide_semantic_candidate_v3(candidate, seal, assets)
    assert len(proof["failure_roots"]) == 2
    assert decision.locality()["localized"] is context_failed
    assert decision.gate()["payload_available"] is context_failed
    assert decision.gate()["diagnostic_code"] == (None if context_failed else "CSV-NEXT-SOURCE-003")
    seam = decision.source_inventory_seam()
    assert seam is not None
    assert ("src/global.d.ts" in {row["path"] for row in seam.safe_files()}) is not context_failed
    assert {row["path"] for row in seam.safe_files()} >= {"src/button.tsx", "src/index.ts"}
    if context_failed:
        assert decision.gate()["outcome"] == "partial_safe"
    validation.validate_semantic_decision_v3(decision)
