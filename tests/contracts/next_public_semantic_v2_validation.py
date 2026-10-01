"""Independent public record/owner joins; schema routing alone is not Core admission."""

from heapq import merge
from typing import Any

from tests.contracts.next_reference_validation import digest
from tests.contracts.next_runtime_v2_reference import (
    ValidatedSemanticDecisionV2,
    trusted_environment_manifest_v2,
)
from tests.contracts.next_runtime_v2_validation import (
    _validate_schema,
    validate_compatibility_descriptor_v2,
    validate_next_analysis_context_v2,
    validate_request_frame_v2,
    validate_semantic_decision_v2,
)


def _require_public_integer_numbers(value: Any) -> None:
    """The closed public schema has integer counts, never floating-point values."""

    if type(value) is float:
        raise ValueError("public numbers must retain integer representations")
    if isinstance(value, dict):
        for child in value.values():
            _require_public_integer_numbers(child)
    elif isinstance(value, list):
        for child in value:
            _require_public_integer_numbers(child)


def validate_public_semantic_document_v2(
    value: dict[str, Any], decision: ValidatedSemanticDecisionV2
) -> None:
    """Recompute each projection without calling its producer or an expected-record builder."""

    validate_semantic_decision_v2(decision)
    _validate_schema("next-semantic-v2", value)
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
    }
    source = value["source"]
    if source != {
        "schema": seal.source_view.schema,
        "kind": seal.source_view.kind,
        "head_commit": seal.source_view.head_commit,
        "fingerprint": seal.source_view.fingerprint,
        "file_count": len(seal.source_view.files),
    }:
        raise ValueError("public source differs from its retained source seal")
    public_request = value["request"]
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
    if any(public_request[key] != config[key] for key in fields):
        raise ValueError("public request differs from its retained analysis context")
    if public_request["run_fingerprint"] != digest(preimage):
        raise ValueError("public run fingerprint differs from its owner-derived preimage")
    compatibility = value["compatibility_descriptor"]
    validate_compatibility_descriptor_v2(compatibility, candidate)
    payload = candidate.semantic_payload()
    if (
        compatibility != decision.compatibility_descriptor()
        or value["semantic_compatibility_id"] != compatibility["compatibility_id"]
        or value["identity_versions"] != compatibility["identity_versions"]
        or value["identity_versions"] != payload["identity_versions"]
    ):
        raise ValueError("public compatibility differs from its parent-owned descriptor")
    expected_status = "complete" if gate["outcome"] == "complete" else "incomplete"
    if value["status"] != expected_status:
        raise ValueError("public status differs from its admitted Core gate")
    model = payload["model"]
    for field in ("projects", "files", "members", "relations", "facts", "coverage", "diagnostics"):
        if value[field] != model[field]:
            raise ValueError(f"public {field} differs from its retained model/order")
    expected_entities = list(
        merge(model["modules"], model["components"], key=lambda item: item["id"].encode("utf-8"))
    )
    if value["entities"] != expected_entities:
        raise ValueError("public entities differ from the canonical retained model merge")


def validate_semantic_dispatcher_v2(value: dict[str, Any]) -> None:
    """Route document/domain/version offline; this does not prove any retained owner."""

    _validate_schema("semantic-v2", value)
