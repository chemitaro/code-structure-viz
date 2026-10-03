"""Core-v3-only public record projection; no Artifact bytes or production execution."""

from typing import Any

from tests.contracts.next_public_semantic_v3_validation import (
    validate_public_semantic_document_v3,
)
from tests.contracts.next_reference_validation import digest
from tests.contracts.next_runtime_v2_reference import (
    trusted_environment_manifest_v2,
)
from tests.contracts.next_semantic_core_v3_reference import ValidatedSemanticDecisionV3
from tests.contracts.next_semantic_core_v3_validation import validate_semantic_decision_v3


def project_public_semantic_document_v3(decision: ValidatedSemanticDecisionV3) -> dict[str, Any]:
    """Project available admitted data only; never synthesize failure or empty success."""

    validate_semantic_decision_v3(decision)
    gate = decision.gate()
    if gate["payload_available"] is not True or gate["outcome"] not in {"complete", "partial_safe"}:
        raise ValueError("public semantic projection requires an available Core decision")
    seal = decision.source_seal()
    candidate = decision.transport_candidate()
    frame = candidate.request_frame()
    request = frame.record()
    context = frame.analysis_context()
    config = context.domain_config()
    run_context = context.run_context()
    binding = candidate.runtime_binding()
    trusted = trusted_environment_manifest_v2(decision.execution_assets())
    fingerprint = digest(
        {
            "source_view_fingerprint": seal.source_view_fingerprint,
            "source_plan_digest": seal.plan_digest,
            "domain_config_digest": config["domain_config_digest"],
            "projects": request["projects"],
            "targets": request["targets"],
            "formats": run_context["requested_formats"],
            "stdout_selector": run_context["stdout_selector"],
            "limits": request["limits"],
            "node_version": binding["node_observation"]["version"],
            "typescript_version": trusted["typescript_version"],
            "adapter_version": request["adapter_version"],
            "protocol": request["protocol"],
            "trusted_environment_digest": config["trusted_environment_digest"],
            "semantic_admission_profile_id": "next-source-inventory-safe-subset-v1",
        }
    )
    public_request = {
        "schema": "code-structure-viz.next-snapshot-request/v1",
        **{
            key: config[key]
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
        "run_fingerprint": fingerprint,
    }
    payload = candidate.semantic_payload()
    model = payload["model"]
    compatibility = decision.compatibility_descriptor()
    seam = decision.source_inventory_seam()
    assert seam is not None
    counts = seam.counts()
    dispositions = seam.file_dispositions()
    record = {
        "type": "semantic_snapshot",
        "schema": "code-structure-viz.semantic/v3",
        "domain": "next",
        "document_kind": "snapshot",
        "status": "complete" if gate["outcome"] == "complete" else "incomplete",
        "semantic_compatibility_id": compatibility["compatibility_id"],
        "compatibility_descriptor": compatibility,
        "identity_versions": payload["identity_versions"],
        "source": {
            "schema": seal.source_view.schema,
            "kind": seal.source_view.kind,
            "head_commit": seal.source_view.head_commit,
            "fingerprint": seal.source_view_fingerprint,
            "file_count": len(seal.source_view.files),
        },
        "request": public_request,
        **{
            key: model[key]
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
        "source_inventory_summary": {
            "profile_id": seam.profile_id,
            "source_partition_fingerprint": seam.partition_fingerprint,
            "acquired": {
                "projects": counts.acquired_projects,
                "files": counts.acquired_files,
                "file_bytes": counts.acquired_file_bytes,
            },
            "safe": {"projects": len(model["projects"]), "files": len(model["files"])},
            "proof_only": {
                "failed_files": sum(row.disposition == "failed" for row in dispositions),
                "excluded_files": sum(row.disposition == "excluded" for row in dispositions),
            },
            "records": {
                "proof_discovered": counts.proof_discovered,
                "published": counts.published_records,
                "proof_only": counts.proof_only_records,
                "accounted": counts.accounted_records,
            },
            "published_entities": {
                "modules": counts.published_modules,
                "components": counts.published_components,
                "total": counts.published_entities,
            },
        },
        "entities": sorted(
            model["modules"] + model["components"], key=lambda item: item["id"].encode("utf-8")
        ),
    }
    if gate["outcome"] == "partial_safe":
        record["incomplete_kind"] = "partial_safe"
    validate_public_semantic_document_v3(record, decision)
    return record
