"""Catalog-only public diagnostics from the same retained run-v3 owners."""

from typing import Any

from tests.contracts.next_reference_validation import _diagnostic_catalog, canonical_json_bytes
from tests.contracts.next_run_decision_v3_reference import RetainedRequestBoundRunDecisionV3
from tests.contracts.next_run_decision_v3_validation import validate_request_bound_run_decision_v3
from tests.contracts.next_semantic_core_v3_reference import (
    RejectedSemanticDecisionV3,
    ValidatedSemanticDecisionV3,
)


def _row(
    code: str, *, path: str | None = None, symbol: str | None = None, reason: str | None = None
) -> dict[str, Any]:
    entry = _diagnostic_catalog()[code]
    return {
        "type": "diagnostic",
        "schema": "code-structure-viz.diagnostic/v1",
        "domain": "next",
        "code": code,
        "path": path,
        "symbol": symbol,
        "line": None,
        **({"reason": reason} if reason is not None else {}),
        **{
            key: entry[key]
            for key in ("severity", "recoverable", "message", "outcome", "ref_permission")
        },
    }


def derive_public_diagnostics_v3(
    run_decision: RetainedRequestBoundRunDecisionV3,
) -> tuple[dict[str, Any], ...]:
    if type(run_decision) is not RetainedRequestBoundRunDecisionV3:
        raise TypeError("public diagnostics require a nominal run owner")
    record = run_decision.record()
    validate_request_bound_run_decision_v3(record, run_decision)
    core = run_decision.semantic_decision()
    if type(core) is RejectedSemanticDecisionV3:
        code = core.failure()["diagnostic_code"]
        assert _diagnostic_catalog()[code]["ref_permission"] == "none"
        return (_row(code),)
    if type(core) is ValidatedSemanticDecisionV3 and core.gate()["payload_available"]:
        payload = core.transport_candidate().semantic_payload()
        rows = [
            _row(
                row["code"],
                path=row["path_ref"],
                symbol=row["symbol_ref"],
                reason=row.get("reason"),
            )
            for row in payload["model"]["diagnostics"]
        ]
        for root in payload["proof"]["failure_roots"]:
            if root["kind"] in {"parse_file", "read_file"} and not any(
                row["code"] == "CSV-NEXT-SOURCE-001" and row["path"] == root["path_ref"]
                for row in rows
            ):
                rows.append(_row("CSV-NEXT-SOURCE-001", path=root["path_ref"]))
        return tuple(sorted(rows, key=canonical_json_bytes))
    if (
        type(core) is ValidatedSemanticDecisionV3
        and core.gate()["diagnostic_code"] == "CSV-NEXT-LIMIT-005"
    ):
        return (_row("CSV-NEXT-LIMIT-005"),)
    if (
        type(core) is ValidatedSemanticDecisionV3
        and core.gate()["diagnostic_code"] == "CSV-NEXT-EXPORT-001"
    ):
        failed = {row["syntax_identity"] for row in core.gate()["export_failures"]}
        payload = core.transport_candidate().semantic_payload()
        public_modules = {row["id"] for row in payload["model"]["modules"]}
        owners = {
            row["owner_module_id"]
            for row in (
                *payload["proof"]["export_observations"],
                *payload["proof"]["export_reexport_witness"],
            )
            if row["syntax_identity"] in failed and row["owner_module_id"] in public_modules
        }
        if not owners:
            raise ValueError("EXPORT diagnostic requires validated public Module witnesses")
        return tuple(
            sorted(
                (_row("CSV-NEXT-EXPORT-001", symbol=owner) for owner in owners),
                key=canonical_json_bytes,
            )
        )
    if (
        type(core) is ValidatedSemanticDecisionV3
        and core.gate()["diagnostic_code"] == "CSV-NEXT-TARGET-001"
    ):
        return tuple(
            sorted(
                (
                    _row(
                        "CSV-NEXT-TARGET-001",
                        path=failure["target_key"].removeprefix("path:"),
                        reason=failure["reason"],
                    )
                    for failure in core.gate()["target_failures"]
                ),
                key=canonical_json_bytes,
            )
        )
    if (
        type(core) is ValidatedSemanticDecisionV3
        and core.gate()["diagnostic_code"] == "CSV-NEXT-SOURCE-003"
    ):
        paths = {
            root["path_ref"]
            for root in core.transport_candidate().semantic_payload()["proof"]["failure_roots"]
            if root["kind"] in {"parse_file", "read_file"}
        }
        if not paths or None in paths:
            raise ValueError("SOURCE-003 requires validated source failure roots")
        return tuple(
            sorted(
                (_row("CSV-NEXT-SOURCE-003", path=path) for path in paths), key=canonical_json_bytes
            )
        )
    if core is not None:
        raise ValueError("other Core public diagnostic branches have not been admitted here")
    code = record["provenance"]["failure_code"]
    assert _diagnostic_catalog()[code]["ref_permission"] == "none"
    return (_row(code),)
