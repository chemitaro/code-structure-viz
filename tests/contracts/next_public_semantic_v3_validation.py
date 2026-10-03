"""Independent public v3 owner/count/partition joins; no producer-derived oracle."""

from heapq import merge
from typing import Any

from tests.contracts.next_reference_validation import COLLECTIONS, digest
from tests.contracts.next_runtime_v2_reference import trusted_environment_manifest_v2
from tests.contracts.next_runtime_v2_validation import (
    _validate_schema,
    validate_next_analysis_context_v2,
    validate_request_frame_v2,
)
from tests.contracts.next_semantic_core_v3_reference import ValidatedSemanticDecisionV3
from tests.contracts.next_semantic_core_v3_validation import (
    validate_compatibility_descriptor_v3,
    validate_semantic_decision_v3,
)


def _require_public_integer_numbers(value: Any) -> None:
    if type(value) is float:
        raise ValueError("public numbers must retain integer representations")
    if isinstance(value, dict):
        for child in value.values():
            _require_public_integer_numbers(child)
    elif isinstance(value, list):
        for child in value:
            _require_public_integer_numbers(child)


def validate_public_semantic_document_v3(
    value: dict[str, Any], decision: ValidatedSemanticDecisionV3
) -> None:
    """Recompute from actual retained owners, never call the public projector."""

    validate_semantic_decision_v3(decision)
    _validate_schema("next-semantic-v3", value)
    _require_public_integer_numbers(value)
    gate = decision.gate()
    if gate["payload_available"] is not True or gate["outcome"] not in {"complete", "partial_safe"}:
        raise ValueError("public semantic validation requires an available Core decision")
    seal, assets = decision.source_seal(), decision.execution_assets()
    candidate = decision.transport_candidate()
    frame = candidate.request_frame()
    validate_request_frame_v2(frame, seal, assets)
    context = frame.analysis_context()
    validate_next_analysis_context_v2(context, seal, assets)
    config, run = context.domain_config(), context.run_context()
    request, binding = frame.record(), candidate.runtime_binding()
    trusted = trusted_environment_manifest_v2(assets)
    config_digest = digest(
        {key: row for key, row in config.items() if key != "domain_config_digest"}
    )
    preimage = {
        "source_view_fingerprint": seal.source_view.fingerprint,
        "source_plan_digest": seal.recompute_plan_digest(),
        "domain_config_digest": config_digest,
        "projects": request["projects"],
        "targets": context.analysis_intent()["targets"],
        "formats": run["requested_formats"],
        "stdout_selector": run["stdout_selector"],
        "limits": seal.final_plan["limits"],
        "node_version": binding["node_observation"]["version"],
        "typescript_version": trusted["typescript_version"],
        "adapter_version": assets.adapter_identity()["version"],
        "protocol": assets.adapter_identity()["protocol"],
        "trusted_environment_digest": trusted["environment_descriptor"]["sha256"],
        "semantic_admission_profile_id": "next-source-inventory-safe-subset-v1",
    }
    if value["source"] != {
        "schema": seal.source_view.schema,
        "kind": seal.source_view.kind,
        "head_commit": seal.source_view.head_commit,
        "fingerprint": seal.source_view.fingerprint,
        "file_count": len(seal.source_view.files),
    }:
        raise ValueError("public source differs from its retained source seal")
    fields = (
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
    if any(value["request"][key] != config[key] for key in fields):
        raise ValueError("public request differs from its retained analysis context")
    if value["request"]["run_fingerprint"] != digest(preimage):
        raise ValueError("public run fingerprint differs from its owner-derived preimage")
    compatibility = value["compatibility_descriptor"]
    validate_compatibility_descriptor_v3(compatibility, candidate)
    payload = candidate.semantic_payload()
    if (
        compatibility != decision.compatibility_descriptor()
        or value["semantic_compatibility_id"] != compatibility["compatibility_id"]
        or value["identity_versions"] != compatibility["identity_versions"]
        or value["identity_versions"] != payload["identity_versions"]
    ):
        raise ValueError("public compatibility differs from its parent-owned descriptor")
    status = "complete" if gate["outcome"] == "complete" else "incomplete"
    if value["status"] != status:
        raise ValueError("public status differs from its admitted Core gate")
    model, proof = payload["model"], payload["proof"]
    for field in ("projects", "files", "members", "relations", "facts", "coverage", "diagnostics"):
        if value[field] != model[field]:
            raise ValueError(f"public {field} differs from its retained model/order")
    if value["entities"] != list(
        merge(model["modules"], model["components"], key=lambda item: item["id"].encode("utf-8"))
    ):
        raise ValueError("public entities differ from the canonical retained model merge")

    # Partition and counts are independently measured, not copied from seam caches.
    safe = {row["id"] for row in model["files"]}
    failed = {row["record_id"] for row in proof["failed"] if row["collection"] == "files"}
    excluded = {row["record_id"] for row in proof["excluded"] if row["collection"] == "files"}
    partition = {
        "profile_id": "next-source-inventory-safe-subset-v1",
        "request_id": candidate.request_id,
        "projects": [
            {
                "project_id": project["id"],
                "safe_file_ids": sorted(set(project["file_ids"]) & safe),
                "failed_file_ids": sorted(set(project["file_ids"]) & failed),
                "excluded_file_ids": sorted(set(project["file_ids"]) & excluded),
            }
            for project in request["projects"]
        ],
    }
    sealed = {row.path.as_posix(): row.content for row in seal.source_view.files}
    published_ids = {row["id"] for name in COLLECTIONS for row in model[name]}
    published = sum(len(model[name]) for name in COLLECTIONS)
    proof_only = sum(row["record_id"] not in published_ids for row in proof["discovered_records"])
    modules, components = len(model["modules"]), len(model["components"])
    expected_summary = {
        "profile_id": "next-source-inventory-safe-subset-v1",
        "source_partition_fingerprint": digest(partition),
        "acquired": {
            "projects": len(request["projects"]),
            "files": len(request["files"]),
            "file_bytes": sum(len(sealed[row["path"]]) for row in request["files"]),
        },
        "safe": {"projects": len(model["projects"]), "files": len(safe)},
        "proof_only": {"failed_files": len(failed), "excluded_files": len(excluded)},
        "records": {
            "proof_discovered": len(proof["discovered_records"]),
            "published": published,
            "proof_only": proof_only,
            "accounted": published + proof_only,
        },
        "published_entities": {
            "modules": modules,
            "components": components,
            "total": modules + components,
        },
    }
    if value["source_inventory_summary"] != expected_summary:
        raise ValueError("public inventory summary differs from actual retained partition/counts")


def validate_semantic_dispatcher_v3(value: dict[str, Any]) -> None:
    """Offline domain/version routing only; never promote it to owner admission."""

    _validate_schema("semantic-v3", value)
