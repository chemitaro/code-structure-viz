"""Named v3 observations; unchanged lower-runtime values are not Core admission."""

from typing import Any

from tests.contracts.next_provenance_v3_validation import validate_runtime_provenance_v3
from tests.contracts.next_reference_validation import digest
from tests.contracts.next_runtime_v2_reference import (
    PROVENANCE_SLOTS_V2,
    RetainedRuntimeResultV2,
    runtime_provenance_values_v2,
)
from tests.contracts.next_semantic_core_v3_reference import (
    RejectedSemanticDecisionV3,
    ValidatedSemanticDecisionV3,
)
from tests.contracts.next_semantic_core_v3_validation import (
    validate_rejected_semantic_decision_v3,
    validate_semantic_decision_v3,
)


def runtime_provenance_values_v3(
    result: RetainedRuntimeResultV2,
    semantic_decision: ValidatedSemanticDecisionV3 | RejectedSemanticDecisionV3 | None = None,
) -> dict[str, Any]:
    """Only the unchanged runtime prefix comes from the legacy lower owner."""

    values = runtime_provenance_values_v2(result, None)
    if semantic_decision is not None:
        if type(semantic_decision) not in {ValidatedSemanticDecisionV3, RejectedSemanticDecisionV3}:
            raise TypeError("provenance requires a nominal v3 Core decision")
        if isinstance(semantic_decision, ValidatedSemanticDecisionV3):
            validate_semantic_decision_v3(semantic_decision)
        else:
            validate_rejected_semantic_decision_v3(semantic_decision)
        if (
            semantic_decision.transport_candidate() is not result.transport_candidate()
            or semantic_decision.source_seal() is not result.source_seal()
            or semantic_decision.execution_assets() is not result.execution_assets()
        ):
            raise ValueError("provenance Core decision is not joined to the same runtime owner")
        if isinstance(semantic_decision, ValidatedSemanticDecisionV3):
            payload = semantic_decision.transport_candidate().semantic_payload()
            gate = semantic_decision.gate()
            values.update(
                semantic_payload=payload,
                compatibility=semantic_decision.compatibility_descriptor(),
                model=payload["model"],
                budget=gate if gate["actual"] is not None else None,
            )
    return values


def provenance_observation_v3(field_name: str, value: Any) -> dict[str, Any]:
    if field_name not in PROVENANCE_SLOTS_V2:
        raise ValueError("unknown provenance observation field")
    if value is None:
        return {"state": "unobserved", "value": None}
    preimage = {
        "schema": "code-structure-viz.next-observation/v3",
        "version": 3,
        "field": field_name,
        "value": value,
    }
    return {
        "state": "observed",
        "value": {"schema": preimage["schema"], "version": 3, "sha256": digest(preimage)},
    }


def runtime_provenance_v3(
    result: RetainedRuntimeResultV2,
    *,
    semantic_decision: ValidatedSemanticDecisionV3 | RejectedSemanticDecisionV3 | None = None,
) -> dict[str, Any]:
    values = runtime_provenance_values_v3(result, semantic_decision)
    if result.result_kind == "success" and semantic_decision is None:
        raise ValueError("successful runtime requires a matching Core decision")
    if result.result_kind != "success" and semantic_decision is not None:
        raise ValueError("runtime failure cannot carry a Core decision")
    if result.result_kind == "interrupted":
        raise ValueError("interrupt requires the core interrupted terminal route")
    gate = (
        semantic_decision.gate()
        if isinstance(semantic_decision, ValidatedSemanticDecisionV3)
        else None
    )
    stage: str | None
    code: str | None
    if result.result_kind == "unsupported_runtime":
        kind, stage, code = "request_bound_failure", "runtime_validation", "CSV-NEXT-NODE-001"
    elif result.result_kind in {"protocol_failure", "bootstrap_failure", "semantic_failure"}:
        stage, code = {
            "protocol_failure": ("response_protocol", "CSV-NEXT-PROTOCOL-001"),
            "bootstrap_failure": ("bootstrap", "CSV-NEXT-NODE-004"),
            "semantic_failure": ("semantic_analysis", "CSV-NEXT-NODE-004"),
        }[result.result_kind]
        kind = "request_bound_failure"
    elif result.result_kind == "transport_failure":
        failure = {
            "stage_failed": ("node_spawn", "CSV-NEXT-NODE-002"),
            "spawn_failed": ("node_spawn", "CSV-NEXT-NODE-002"),
            "write_failed": ("node_process", "CSV-NEXT-NODE-004"),
            "read_failed": ("node_process", "CSV-NEXT-NODE-004"),
            "binding_mismatch": ("response_validation", "CSV-NEXT-PROTOCOL-001"),
            "response_invalid": ("response_validation", "CSV-NEXT-PROTOCOL-001"),
            "exit_mismatch": ("node_process", "CSV-NEXT-NODE-004"),
            "stdout_limit": ("adapter_stdout_capture", "CSV-NEXT-LIMIT-003"),
            "stderr_limit": ("adapter_stderr_capture", "CSV-NEXT-LIMIT-003"),
            "timeout": ("node_timeout", "CSV-NEXT-NODE-003"),
            "cleanup_unverified": ("node_process", "CSV-NEXT-NODE-004"),
            "candidate_drift": ("node_process", "CSV-NEXT-NODE-004"),
            "assets_drift": ("node_process", "CSV-NEXT-NODE-004"),
        }.get(result.observation()["terminal_cause"])
        if (rejection := result.frame_rejection()) is not None:
            failure = rejection["stage"], rejection["diagnostic_code"]
        if failure is None:
            raise ValueError("runtime result has no closed provenance branch yet")
        kind, (stage, code) = "request_bound_failure", failure
    elif isinstance(semantic_decision, RejectedSemanticDecisionV3):
        core_failure = semantic_decision.failure()
        kind, stage, code = (
            "request_bound_failure",
            core_failure["stage"],
            core_failure["diagnostic_code"],
        )
    elif gate is not None and gate["payload_available"]:
        kind, stage, code = "request_bound_success", None, None
    elif gate is not None and gate["diagnostic_code"] == "CSV-NEXT-SOURCE-003":
        kind, stage, code = "request_bound_failure", "source_read", "CSV-NEXT-SOURCE-003"
    elif gate is not None and gate["diagnostic_code"] == "CSV-NEXT-TARGET-001":
        kind, stage, code = "request_bound_failure", "target_resolution", "CSV-NEXT-TARGET-001"
    elif gate is not None and gate["diagnostic_code"] == "CSV-NEXT-EXPORT-001":
        kind, stage, code = "request_bound_failure", "response_validation", "CSV-NEXT-EXPORT-001"
    elif gate is not None and gate["diagnostic_code"] == "CSV-NEXT-LIMIT-005":
        kind, stage, code = "request_bound_failure", "model_validation", "CSV-NEXT-LIMIT-005"
    else:
        raise ValueError("runtime result has no closed provenance branch yet")
    value = {
        "schema": "code-structure-viz.next-provenance/v3",
        "kind": kind,
        "stage": stage,
        "failure_code": code,
        "observed": {key: provenance_observation_v3(key, row) for key, row in values.items()},
    }
    validate_runtime_provenance_v3(value, result, semantic_decision=semantic_decision)
    return value
