"""Decision-only public record projection; no Artifact bytes or production execution."""

from typing import Any

from tests.contracts.next_public_semantic_v2_validation import (
    validate_public_semantic_document_v2,
)
from tests.contracts.next_reference_validation import digest
from tests.contracts.next_runtime_v2_reference import (
    ValidatedSemanticDecisionV2,
    trusted_environment_manifest_v2,
)
from tests.contracts.next_runtime_v2_validation import validate_semantic_decision_v2


def project_public_semantic_document_v2(decision: ValidatedSemanticDecisionV2) -> dict[str, Any]:
    """Project available admitted data only; never synthesize failure or empty success."""

    validate_semantic_decision_v2(decision)
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
    record = {
        "type": "semantic_snapshot",
        "schema": "code-structure-viz.semantic/v2",
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
        "entities": sorted(
            model["modules"] + model["components"], key=lambda item: item["id"].encode("utf-8")
        ),
    }
    if gate["outcome"] == "partial_safe":
        record["incomplete_kind"] = "partial_safe"
    validate_public_semantic_document_v2(record, decision)
    return record
