"""Independent field/owner verification, not a producer-built expected record."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from tests.contracts.next_reference_validation import canonical_json_bytes, digest
from tests.contracts.next_runtime_v2_reference import (
    RejectedSemanticDecisionV2,
    ValidatedSemanticDecisionV2,
)
from tests.contracts.next_runtime_v2_validation import (
    _validate_schema,
    validate_next_analysis_context_v2,
    validate_rejected_semantic_decision_v2,
    validate_runtime_provenance_v2,
    validate_runtime_result_v2,
    validate_semantic_decision_v2,
)

if TYPE_CHECKING:
    from tests.contracts.next_run_decision_v2_reference import RetainedRequestBoundRunDecisionV2


def validate_request_bound_run_decision_v2(
    value: Mapping[str, Any],
    owner: RetainedRequestBoundRunDecisionV2,
) -> None:
    """Verify retained sources and actual bytes, never call the run producer."""

    from tests.contracts.next_run_decision_v2_reference import RetainedRequestBoundRunDecisionV2

    if type(owner) is not RetainedRequestBoundRunDecisionV2:
        raise TypeError("run validation requires a retained run owner")
    _validate_schema("next-run-decision-v2", value)
    if any(type(value[key]) is not int for key in ("version", "exit_code")):
        raise ValueError("run version and exit code require integer values")
    held_record = owner.record()
    if value != held_record or owner._record_bytes != canonical_json_bytes(held_record):
        raise ValueError("run projection differs from its immutable retained record")
    # This equality is only a cache/owner join. Independently verify every
    # field below; agreement with a faulty producer's record is not admission.
    runtime, core = owner.runtime_result(), owner.semantic_decision()
    validate_runtime_result_v2(runtime)
    if runtime.result_kind == "interrupted":
        raise ValueError(
            "interrupt requires the core interrupted terminal route, not ordinary run2"
        )
    if runtime.result_kind == "success" and core is None:
        raise ValueError("successful runtime requires a matching Core decision owner")
    if runtime.result_kind != "success" and core is not None:
        raise ValueError("runtime failure cannot carry a Core decision owner")
    seal, assets = runtime.source_seal(), runtime.execution_assets()
    if core is not None:
        if type(core) not in {ValidatedSemanticDecisionV2, RejectedSemanticDecisionV2}:
            raise TypeError("run validation requires a matching Core decision owner")
        if isinstance(core, ValidatedSemanticDecisionV2):
            validate_semantic_decision_v2(core)
        else:
            validate_rejected_semantic_decision_v2(core)
        if (
            core.transport_candidate() is not runtime.transport_candidate()
            or core.source_seal() is not seal
            or core.execution_assets() is not assets
        ):
            raise ValueError("run Core decision is not joined to the same runtime owner")
    gate = core.gate() if isinstance(core, ValidatedSemanticDecisionV2) else None
    outcome = gate["outcome"] if gate is not None else "payload_unavailable"
    if outcome not in {"complete", "partial_safe", "payload_unavailable"}:
        raise ValueError("run result has no closed outcome branch yet")
    if tuple(
        value[key] for key in ("kind", "status", "outcome", "payload_available", "exit_code")
    ) != (
        "request_bound_failure" if outcome == "payload_unavailable" else "request_bound_success",
        "complete" if outcome == "complete" else "incomplete",
        outcome,
        gate["payload_available"] if gate is not None else False,
        0 if outcome == "complete" else 3,
    ):
        raise ValueError("run outcome differs from its retained runtime/Core owners")
    validate_runtime_provenance_v2(value["provenance"], runtime, semantic_decision=core)
    if canonical_json_bytes(value["context"]["observed_prefix"]) != canonical_json_bytes(
        value["provenance"]["observed"]
    ):
        raise ValueError("run observed prefix differs from its provenance")
    frame = runtime.request_frame()
    parent = frame.analysis_context()
    validate_next_analysis_context_v2(parent, seal, assets)
    config, run = parent.domain_config(), parent.run_context()
    request, context = frame.record(), value["context"]
    config_digest = digest(
        {key: row for key, row in config.items() if key != "domain_config_digest"}
    )
    identities = {
        "request_id": frame.request_id,
        "run_context": run,
        "analysis_intent": parent.analysis_intent(),
        "domain_config_digest": config_digest,
        "source_plan_digest": seal.recompute_plan_digest(),
        "source_view_fingerprint": seal.source_view.fingerprint,
        "compatibility_id": core.compatibility_descriptor()["compatibility_id"]
        if isinstance(core, ValidatedSemanticDecisionV2)
        else None,
    }
    if any(
        canonical_json_bytes(context[key]) != canonical_json_bytes(actual)
        for key, actual in identities.items()
    ):
        raise ValueError("run context differs from its retained parent/source owners")
    binding = core.transport_candidate().runtime_binding() if core is not None else None
    preimage = (
        None
        if binding is None
        else {
            "source_view_fingerprint": seal.source_view.fingerprint,
            "source_plan_digest": seal.recompute_plan_digest(),
            "domain_config_digest": config_digest,
            "projects": request["projects"],
            "targets": parent.analysis_intent()["targets"],
            "formats": run["requested_formats"],
            "stdout_selector": run["stdout_selector"],
            "limits": seal.final_plan["limits"],
            "node_version": binding["node_observation"]["version"],
            # Locked expected metadata, never an actual TypeScript-use attestation.
            "typescript_version": "5.9.2",
            "adapter_version": assets.adapter_identity()["version"],
            "protocol": assets.adapter_identity()["protocol"],
            "trusted_environment_digest": request["trusted_type_environment"]["sha256"],
        }
    )
    if context["run_fingerprint"] != (digest(preimage) if preimage is not None else None):
        raise ValueError("run fingerprint differs from its 13-key owner-derived preimage")
    if canonical_json_bytes(value["request"]) != canonical_json_bytes(
        {
            "request_id": frame.request_id,
            "raw_sha256": hashlib.sha256(frame.canonical_bytes).hexdigest(),
            "byte_length": len(frame.canonical_bytes),
            "canonical_json": frame.canonical_bytes == canonical_json_bytes(request),
        }
    ):
        raise ValueError("run request descriptor differs from its actual retained bytes")
    receipt = runtime.observed_response_receipt()
    if canonical_json_bytes(value["response"]) != canonical_json_bytes(
        receipt.descriptor() if receipt is not None else None
    ):
        raise ValueError("run response descriptor differs from its validated receipt")
    measurement = (
        None
        if gate is None or gate["actual"] is None
        else {
            "kind": "entity_budget",
            "actual": gate["actual"],
            "limit": request["limits"]["max_entities"],
        }
    )
    if isinstance(core, RejectedSemanticDecisionV2) and core.failure()["model_records"] is not None:
        measurement = {
            "kind": "model_record_limit",
            "actual": core.failure()["model_records"],
            "limit": request["limits"]["max_model_records"],
        }
    if value["core_measurement"] is not None and any(
        type(value["core_measurement"][key]) is not int for key in ("actual", "limit")
    ):
        raise ValueError("run measurement requires actual integer counts, not bool/float")
    if value["core_measurement"] != measurement:
        raise ValueError("run measurement differs from its actual Core gate/rejection")
