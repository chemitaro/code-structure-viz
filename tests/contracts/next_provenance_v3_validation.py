"""Independent v3 digests and same-owner joins; never call provenance producers."""

from typing import Any

from tests.contracts.next_reference_validation import digest
from tests.contracts.next_runtime_v2_reference import RetainedRuntimeResultV2
from tests.contracts.next_runtime_v2_validation import (
    _retained_provenance_values_v2,
    _validate_schema,
)
from tests.contracts.next_semantic_core_v3_reference import (
    RejectedSemanticDecisionV3,
    ValidatedSemanticDecisionV3,
)
from tests.contracts.next_semantic_core_v3_validation import (
    validate_rejected_semantic_decision_v3,
    validate_semantic_decision_v3,
)


def validate_provenance_shape_v3(value: dict[str, Any]) -> None:
    _validate_schema("next-provenance-v3", value)


def validate_runtime_provenance_v3(
    value: dict[str, Any],
    result: RetainedRuntimeResultV2,
    *,
    semantic_decision: ValidatedSemanticDecisionV3 | RejectedSemanticDecisionV3 | None = None,
) -> None:
    validate_provenance_shape_v3(value)
    # Lower-runtime-only independent derivation: no V2 Core or producer oracle.
    actual_values = _retained_provenance_values_v2(result, None)
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
            budget_gate = semantic_decision.gate()
            actual_values["semantic_payload"] = payload
            actual_values["compatibility"] = semantic_decision.compatibility_descriptor()
            actual_values["model"] = payload["model"]
            actual_values["budget"] = budget_gate if budget_gate["actual"] is not None else None
    if result.result_kind == "success" and semantic_decision is None:
        raise ValueError("successful runtime requires a matching Core decision")
    if result.result_kind != "success" and semantic_decision is not None:
        raise ValueError("runtime failure cannot carry a Core decision")
    gate = (
        semantic_decision.gate()
        if isinstance(semantic_decision, ValidatedSemanticDecisionV3)
        else None
    )
    expected: tuple[str, str | None, str | None]
    if isinstance(semantic_decision, RejectedSemanticDecisionV3):
        failure = semantic_decision.failure()
        expected = ("request_bound_failure", failure["stage"], failure["diagnostic_code"])
    elif gate is not None and gate["payload_available"]:
        expected = ("request_bound_success", None, None)
    elif gate is not None and gate["diagnostic_code"] == "CSV-NEXT-SOURCE-003":
        expected = ("request_bound_failure", "source_read", "CSV-NEXT-SOURCE-003")
    elif gate is not None and gate["diagnostic_code"] == "CSV-NEXT-TARGET-001":
        expected = ("request_bound_failure", "target_resolution", "CSV-NEXT-TARGET-001")
    elif gate is not None and gate["diagnostic_code"] == "CSV-NEXT-EXPORT-001":
        expected = ("request_bound_failure", "response_validation", "CSV-NEXT-EXPORT-001")
    elif gate is not None and gate["diagnostic_code"] == "CSV-NEXT-LIMIT-005":
        expected = ("request_bound_failure", "model_validation", "CSV-NEXT-LIMIT-005")
    elif result.result_kind == "unsupported_runtime":
        expected = "request_bound_failure", "runtime_validation", "CSV-NEXT-NODE-001"
    elif result.result_kind in {"protocol_failure", "bootstrap_failure", "semantic_failure"}:
        child_identity = {
            "protocol_failure": ("response_protocol", "CSV-NEXT-PROTOCOL-001"),
            "bootstrap_failure": ("bootstrap", "CSV-NEXT-NODE-004"),
            "semantic_failure": ("semantic_analysis", "CSV-NEXT-NODE-004"),
        }[result.result_kind]
        expected = "request_bound_failure", *child_identity
    elif result.result_kind == "transport_failure":
        transport_identity = {
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
            transport_identity = rejection["stage"], rejection["diagnostic_code"]
        if transport_identity is None:
            raise ValueError("runtime result has no closed provenance result identity")
        expected = "request_bound_failure", *transport_identity
    else:
        raise ValueError("runtime result has no closed provenance result identity")
    if tuple(value[key] for key in ("kind", "stage", "failure_code")) != expected:
        raise ValueError("provenance result identity differs from its retained runtime/Core owners")
    for field_name, actual in actual_values.items():
        row = value["observed"][field_name]
        if (row["state"] == "observed") is not (actual is not None):
            raise ValueError("provenance observation state differs from its retained owner")
        if actual is not None:
            if type(row["value"]["version"]) is not int:
                raise ValueError("provenance observation version requires an integer")
            preimage = {
                "schema": "code-structure-viz.next-observation/v3",
                "version": 3,
                "field": field_name,
                "value": actual,
            }
            if row["value"]["sha256"] != digest(preimage):
                raise ValueError("provenance observation digest differs from its retained owner")
