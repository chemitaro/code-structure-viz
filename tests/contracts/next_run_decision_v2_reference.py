"""Request-bound reference run authority, separate from final publication."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, cast

from tests.contracts.next_reference_validation import canonical_json_bytes, digest
from tests.contracts.next_run_decision_v2_validation import validate_request_bound_run_decision_v2
from tests.contracts.next_runtime_v2_reference import (
    RejectedSemanticDecisionV2,
    RetainedRuntimeResultV2,
    ValidatedSemanticDecisionV2,
    runtime_provenance_v2,
    trusted_environment_manifest_v2,
)
from tests.contracts.next_runtime_v2_validation import (
    validate_rejected_semantic_decision_v2,
    validate_runtime_result_v2,
    validate_semantic_decision_v2,
)


@dataclass(frozen=True, slots=True, init=False)
class RetainedRequestBoundRunDecisionV2:
    """One immutable projection joined to the same runtime and Core owners."""

    _runtime: RetainedRuntimeResultV2 = field(repr=False)
    _semantic: ValidatedSemanticDecisionV2 | RejectedSemanticDecisionV2 | None = field(repr=False)
    _record_bytes: bytes = field(repr=False)

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("run decisions are created by retain_request_bound_run_decision_v2")

    @classmethod
    def _from_joined_owners(
        cls,
        runtime: RetainedRuntimeResultV2,
        semantic: ValidatedSemanticDecisionV2 | RejectedSemanticDecisionV2 | None,
        record: dict[str, Any],
    ) -> RetainedRequestBoundRunDecisionV2:
        instance = object.__new__(cls)
        object.__setattr__(instance, "_runtime", runtime)
        object.__setattr__(instance, "_semantic", semantic)
        object.__setattr__(instance, "_record_bytes", canonical_json_bytes(record))
        return instance

    def runtime_result(self) -> RetainedRuntimeResultV2:
        return self._runtime

    def semantic_decision(self) -> ValidatedSemanticDecisionV2 | RejectedSemanticDecisionV2 | None:
        return self._semantic

    def record(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(self._record_bytes))


def retain_request_bound_run_decision_v2(
    runtime_result: RetainedRuntimeResultV2,
    *,
    semantic_decision: ValidatedSemanticDecisionV2 | RejectedSemanticDecisionV2 | None = None,
) -> RetainedRequestBoundRunDecisionV2:
    """No free status, measurement, hash, prefix, or descriptor inputs."""

    validate_runtime_result_v2(runtime_result)
    if runtime_result.result_kind == "interrupted":
        raise ValueError(
            "interrupt requires the core interrupted terminal route, not ordinary run2"
        )
    if runtime_result.result_kind == "success" and semantic_decision is None:
        raise ValueError("successful runtime requires a matching Core decision owner")
    if runtime_result.result_kind != "success" and semantic_decision is not None:
        raise ValueError("runtime failure cannot carry a Core decision owner")
    if semantic_decision is not None:
        if type(semantic_decision) not in {ValidatedSemanticDecisionV2, RejectedSemanticDecisionV2}:
            raise TypeError("run requires a nominal Core decision owner")
        if isinstance(semantic_decision, ValidatedSemanticDecisionV2):
            validate_semantic_decision_v2(semantic_decision)
        else:
            validate_rejected_semantic_decision_v2(semantic_decision)
        if (
            semantic_decision.transport_candidate() is not runtime_result.transport_candidate()
            or semantic_decision.source_seal() is not runtime_result.source_seal()
            or semantic_decision.execution_assets() is not runtime_result.execution_assets()
        ):
            raise ValueError("run Core decision is not joined to the same runtime owner")
    gate = (
        semantic_decision.gate()
        if isinstance(semantic_decision, ValidatedSemanticDecisionV2)
        else None
    )
    outcome = gate["outcome"] if gate is not None else "payload_unavailable"
    if outcome not in {"complete", "partial_safe", "payload_unavailable"}:
        raise ValueError("run result has no closed outcome branch yet")
    seal, frame = runtime_result.source_seal(), runtime_result.request_frame()
    request, parent = frame.record(), frame.analysis_context()
    config, run = parent.domain_config(), parent.run_context()
    binding = (
        semantic_decision.transport_candidate().runtime_binding()
        if semantic_decision is not None
        else None
    )
    trusted = trusted_environment_manifest_v2(runtime_result.execution_assets())
    fingerprint = (
        None
        if binding is None
        else digest(
            {
                "source_view_fingerprint": seal.source_view_fingerprint,
                "source_plan_digest": seal.plan_digest,
                "domain_config_digest": config["domain_config_digest"],
                "projects": request["projects"],
                "targets": request["targets"],
                "formats": run["requested_formats"],
                "stdout_selector": run["stdout_selector"],
                "limits": request["limits"],
                "node_version": binding["node_observation"]["version"],
                "typescript_version": trusted["typescript_version"],
                "adapter_version": request["adapter_version"],
                "protocol": request["protocol"],
                "trusted_environment_digest": config["trusted_environment_digest"],
            }
        )
    )
    provenance = runtime_provenance_v2(runtime_result, semantic_decision=semantic_decision)
    measurement = (
        None
        if gate is None or gate["actual"] is None
        else {
            "kind": "entity_budget",
            "actual": gate["actual"],
            "limit": request["limits"]["max_entities"],
        }
    )
    if (
        isinstance(semantic_decision, RejectedSemanticDecisionV2)
        and semantic_decision.failure()["model_records"] is not None
    ):
        measurement = {
            "kind": "model_record_limit",
            "actual": semantic_decision.failure()["model_records"],
            "limit": request["limits"]["max_model_records"],
        }
    record = {
        "schema": "code-structure-viz.next-run-decision/v2",
        "version": 2,
        "kind": provenance["kind"],
        "status": "complete" if outcome == "complete" else "incomplete",
        "outcome": outcome,
        "request_independent": False,
        "payload_available": gate["payload_available"] if gate is not None else False,
        "exit_code": 0 if outcome == "complete" else 3,
        "provenance": provenance,
        "context": {
            "request_id": frame.request_id,
            "run_fingerprint": fingerprint,
            "run_context": run,
            "analysis_intent": parent.analysis_intent(),
            "domain_config_digest": config["domain_config_digest"],
            "source_plan_digest": seal.plan_digest,
            "source_view_fingerprint": seal.source_view_fingerprint,
            "compatibility_id": semantic_decision.compatibility_descriptor()["compatibility_id"]
            if isinstance(semantic_decision, ValidatedSemanticDecisionV2)
            else None,
            "observed_prefix": provenance["observed"],
        },
        "request": {
            "request_id": frame.request_id,
            "raw_sha256": hashlib.sha256(frame.canonical_bytes).hexdigest(),
            "byte_length": len(frame.canonical_bytes),
            "canonical_json": True,
        },
        "response": runtime_result.response_descriptor(),
        "core_measurement": measurement,
    }
    owner = RetainedRequestBoundRunDecisionV2._from_joined_owners(
        runtime_result, semantic_decision, record
    )
    validate_request_bound_run_decision_v2(record, owner)
    return owner


def project_request_bound_run_decision_v2(
    owner: RetainedRequestBoundRunDecisionV2,
) -> dict[str, Any]:
    if type(owner) is not RetainedRequestBoundRunDecisionV2:
        raise TypeError("run projection requires a retained run owner")
    record = owner.record()
    validate_request_bound_run_decision_v2(record, owner)
    return record
