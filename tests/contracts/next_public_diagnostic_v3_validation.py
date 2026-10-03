"""Independent catalog/owner validation, without a diagnostic producer oracle."""

from typing import Any

from tests.contracts.next_reference_validation import (
    _diagnostic_catalog,
    _validate_public_diagnostics,
)
from tests.contracts.next_run_decision_v3_reference import RetainedRequestBoundRunDecisionV3
from tests.contracts.next_run_decision_v3_validation import validate_request_bound_run_decision_v3
from tests.contracts.next_runtime_v2_validation import _validate_schema
from tests.contracts.next_semantic_core_v3_reference import (
    RejectedSemanticDecisionV3,
    ValidatedSemanticDecisionV3,
)


def validate_public_diagnostics_v3(
    diagnostics: tuple[dict[str, Any], ...],
    run_decision: RetainedRequestBoundRunDecisionV3,
) -> None:
    if type(diagnostics) is not tuple:
        raise TypeError("public diagnostics require a closed tuple")
    validate_request_bound_run_decision_v3(run_decision.record(), run_decision)
    _validate_public_diagnostics(list(diagnostics))
    for row in diagnostics:
        _validate_schema("diagnostic-v1", row)
    core = run_decision.semantic_decision()
    if type(core) is RejectedSemanticDecisionV3:
        code = core.failure()["diagnostic_code"]
        assert _diagnostic_catalog()[code]["ref_permission"] == "none"
        expected = {(code, None, None, None)}
    elif type(core) is ValidatedSemanticDecisionV3 and core.gate()["payload_available"]:
        payload = core.transport_candidate().semantic_payload()
        expected = {
            (row["code"], row["path_ref"], row["symbol_ref"], row.get("reason"))
            for row in payload["model"]["diagnostics"]
        } | {
            ("CSV-NEXT-SOURCE-001", root["path_ref"], None, None)
            for root in payload["proof"]["failure_roots"]
            if root["kind"] in {"parse_file", "read_file"}
        }
    elif (
        type(core) is ValidatedSemanticDecisionV3
        and core.gate()["diagnostic_code"] == "CSV-NEXT-LIMIT-005"
    ):
        expected = {("CSV-NEXT-LIMIT-005", None, None, None)}
    elif (
        type(core) is ValidatedSemanticDecisionV3
        and core.gate()["diagnostic_code"] == "CSV-NEXT-EXPORT-001"
    ):
        payload = core.transport_candidate().semantic_payload()
        allowed_modules = {row["id"] for row in payload["model"]["modules"]}
        failed_syntax = {failure["syntax_identity"] for failure in core.gate()["export_failures"]}
        expected = {
            ("CSV-NEXT-EXPORT-001", None, witness["owner_module_id"], None)
            for field in ("export_observations", "export_reexport_witness")
            for witness in payload["proof"][field]
            if witness["syntax_identity"] in failed_syntax
            and witness["owner_module_id"] in allowed_modules
        }
        if not expected:
            raise ValueError("EXPORT failure has no actual public Module witness")
    elif (
        type(core) is ValidatedSemanticDecisionV3
        and core.gate()["diagnostic_code"] == "CSV-NEXT-TARGET-001"
    ):
        expected = {
            ("CSV-NEXT-TARGET-001", row["target_key"].removeprefix("path:"), None, row["reason"])
            for row in core.gate()["target_failures"]
        }
    elif (
        type(core) is ValidatedSemanticDecisionV3
        and core.gate()["diagnostic_code"] == "CSV-NEXT-SOURCE-003"
    ):
        expected = {
            ("CSV-NEXT-SOURCE-003", root["path_ref"], None, None)
            for root in core.transport_candidate().semantic_payload()["proof"]["failure_roots"]
            if root["kind"] in {"parse_file", "read_file"}
        }
        if not expected or any(path is None for _code, path, _symbol, _reason in expected):
            raise ValueError("SOURCE-003 has no actual source failure root")
    elif core is None:
        code = run_decision.record()["provenance"]["failure_code"]
        assert _diagnostic_catalog()[code]["ref_permission"] == "none"
        expected = {(code, None, None, None)}
    else:
        raise ValueError("other Core diagnostic validation has not been admitted here")
    if {
        (row["code"], row["path"], row["symbol"], row.get("reason")) for row in diagnostics
    } != expected:
        raise ValueError("public diagnostic refs differ from the same run/Core evidence")
    for row in diagnostics:
        keys = {
            "type",
            "schema",
            "domain",
            "code",
            "severity",
            "recoverable",
            "message",
            "outcome",
            "ref_permission",
            "path",
            "symbol",
            "line",
        }
        if row["code"] == "CSV-NEXT-TARGET-001":
            keys.add("reason")
        if set(row) != keys:
            raise ValueError("diagnostic carries unauthorized public fields")
