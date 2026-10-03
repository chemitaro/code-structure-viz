"""Independently verify final publication against retained owners and bytes."""

from __future__ import annotations

import base64
import hashlib
import json
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from tests.contracts.next_public_diagnostic_v3_validation import validate_public_diagnostics_v3
from tests.contracts.next_publication_candidates_v3_reference import (
    RetainedRequestBoundPublicationCandidatesV3,
)
from tests.contracts.next_publication_candidates_v3_validation import (
    validate_request_bound_publication_candidates_v3,
)
from tests.contracts.next_reference_validation import (
    _canonical_measurement_value,
    _diagnostic_catalog,
    canonical_json_bytes,
    digest,
)
from tests.contracts.next_runtime_v2_validation import _validate_schema
from tests.contracts.next_semantic_core_v3_reference import (
    RejectedSemanticDecisionV3,
    ValidatedSemanticDecisionV3,
)

if TYPE_CHECKING:
    from tests.contracts.next_final_publication_v2_reference import RetainedFinalPublicationV2


def _same(value: Any, expected: Any) -> bool:
    return canonical_json_bytes(value) == canonical_json_bytes(expected)


def validate_final_publication_v2(
    value: Mapping[str, Any],
    owner: RetainedFinalPublicationV2,
    *,
    candidates: RetainedRequestBoundPublicationCandidatesV3,
) -> None:
    from tests.contracts.next_final_publication_v2_reference import RetainedFinalPublicationV2

    if (
        type(owner) is not RetainedFinalPublicationV2
        or type(candidates) is not RetainedRequestBoundPublicationCandidatesV3
    ):
        raise TypeError("final validation requires nominal publication and candidates owners")
    if owner.candidates() is not candidates:
        raise ValueError("final publication differs from its same candidates owner")
    _validate_schema("next-publication-decision-v2", value)
    if type(value["version"]) is not int or type(value["exit_code"]) is not int:
        raise ValueError("publication version/exit must be native integers")
    if not _same(dict(value), owner.record()) or owner._record_bytes != canonical_json_bytes(
        owner.record()
    ):
        raise ValueError("final projection differs from its immutable retained metadata")
    run = candidates.run_decision()
    validate_request_bound_publication_candidates_v3(
        value["candidates"], candidates, run_decision=run
    )
    if not _same(value["semantic_decision"], run.record()):
        raise ValueError("publication semantic decision differs from the same run owner")
    core = run.semantic_decision()
    if core is not None and type(core) not in {
        ValidatedSemanticDecisionV3,
        RejectedSemanticDecisionV3,
    }:
        raise ValueError("unavailable final-publication validation is not admitted here yet")
    frame = run.runtime_result().request_frame()
    limits = frame.record()["limits"]
    selector = frame.analysis_context().run_context()["stdout_selector"]
    if selector not in {"next:semantic-json", "next:plantuml"}:
        raise ValueError("summary/manifest final-publication validation is not admitted here yet")
    held = candidates.record()["capture_measurements"]
    capture_failed = False
    for stream in ("stdout", "stderr"):
        captured = held[f"adapter_{stream}"]
        expected = (
            None
            if captured is None
            else {
                "allowed": captured["captured_bytes"] <= captured["limit_bytes"],
                "measured_bytes": captured["captured_bytes"],
                "retained_bytes": captured["capture_retained_bytes"],
            }
        )
        if not _same(value["measurements"][f"adapter_{stream}"], expected):
            raise ValueError("final capture measurement differs from the same observation owner")
        capture_failed = capture_failed or (expected is not None and not expected["allowed"])
    diagnostic_input = owner._diagnostic_input_bytes
    stderr_failed = len(diagnostic_input) > limits["max_stderr_bytes"]
    publication_failed = capture_failed or stderr_failed
    ordered = sorted(candidates.artifacts(), key=lambda item: item.descriptor()["path"])
    selected_artifact = next(
        (item for item in ordered if "next:" + item.descriptor()["format"] == selector),
        None,
    )
    raw = selected_artifact.wire_bytes() if selected_artifact is not None else b""
    selected_sha = hashlib.sha256(raw).hexdigest()
    selected_failed = len(raw) > limits["max_selected_stdout_bytes"]
    expected_outcome = (
        "payload_unavailable"
        if publication_failed
        else "selected_artifact_unavailable"
        if selected_failed
        else "published"
    )
    if value["publication_outcome"] != expected_outcome or value["exit_code"] != (
        3 if publication_failed or selected_failed else run.record()["exit_code"]
    ):
        raise ValueError("final publication outcome differs from the actual successful boundaries")
    published_artifacts = [] if publication_failed else ordered
    artifacts = [
        {
            "descriptor": item.descriptor(),
            "bytes_base64": base64.b64encode(item.wire_bytes()).decode("ascii"),
        }
        for item in published_artifacts
    ]
    if not _same(value["artifacts"], artifacts):
        raise ValueError("published artifacts differ from actual retained candidates")
    response_bytes = b""
    validated_response = None
    if type(core) is ValidatedSemanticDecisionV3:
        response_frame = core.transport_candidate().response_frame()
        response_bytes = response_frame.raw_bytes
        validated_response = {
            "request_id": core.request_id,
            "raw_sha256": hashlib.sha256(response_bytes).hexdigest(),
            "model_digest": core.transport_candidate().semantic_payload()["model_digest"],
            "byte_length": len(response_bytes),
        }
    response = None if publication_failed else validated_response
    if not _same(value["response"], response):
        raise ValueError("published response link differs from the same validated Core receipt")
    stdout_bytes = raw
    if selected_artifact is None or publication_failed:
        unavailable: dict[str, Any] = {
            "type": "stdout_result",
            "schema": "code-structure-viz.stdout-result/v2",
            "selector": selector,
            "availability": False,
            "domain_status": "incomplete",
            "stable_reason": "domain_payload_unavailable",
            "artifact": None,
        }
        if (
            type(core) is ValidatedSemanticDecisionV3
            and not publication_failed
            and core.gate()["diagnostic_code"] == "CSV-NEXT-TARGET-001"
        ):
            unavailable["stable_reason"] = "target_payload_unavailable"
            unavailable["target_failures"] = sorted(
                [
                    {"target_key": row["target_key"], "reason": row["reason"]}
                    for row in core.gate()["target_failures"]
                ],
                key=canonical_json_bytes,
            )
        stdout_bytes = canonical_json_bytes(unavailable) + b"\n"
    elif selected_failed:
        replacement: dict[str, Any] = {
            "type": "stdout_result",
            "schema": "code-structure-viz.stdout-result/v2",
            "selector": selector,
            "availability": False,
            "domain_status": run.record()["status"],
            "stable_reason": "selected_artifact_unavailable",
            "selected_stdout_unavailable": True,
            "artifact": selected_artifact.descriptor(),
        }
        if run.record()["status"] == "incomplete":
            replacement["incomplete_kind"] = run.record()["incomplete_kind"]
        stdout_bytes = canonical_json_bytes(replacement) + b"\n"
    stdout = {
        "selector": selector,
        "availability": selected_artifact is not None
        and not publication_failed
        and not selected_failed,
        "copy_status": (
            "not_attempted"
            if selected_artifact is None or publication_failed
            else "unavailable"
            if selected_failed
            else "published"
        ),
        "candidate": selected_artifact.descriptor()
        if selected_artifact is not None and not publication_failed
        else None,
        "result_bytes_base64": base64.b64encode(stdout_bytes).decode("ascii"),
        "result_size_bytes": len(stdout_bytes),
        "result_sha256": hashlib.sha256(stdout_bytes).hexdigest(),
    }
    if selected_artifact is not None:
        stdout.update(selected_size_bytes=len(raw), selected_sha256=selected_sha)
    if owner.stdout_bytes() != stdout_bytes or not _same(value["stdout"], stdout):
        raise ValueError("final stdout differs from its actual pre-copy candidate bytes")
    diagnostics = tuple(json.loads(line) for line in diagnostic_input.splitlines())
    base_diagnostics = tuple(row for row in diagnostics if "scope" not in row)
    validate_public_diagnostics_v3(base_diagnostics, run)
    catalog = _diagnostic_catalog()["CSV-NEXT-LIMIT-003"]
    limit_row = {
        "type": "diagnostic",
        "schema": "code-structure-viz.diagnostic/v1",
        "domain": "next",
        "path": None,
        "symbol": None,
        "line": None,
        **{
            key: catalog[key]
            for key in ("code", "severity", "recoverable", "message", "outcome", "ref_permission")
        },
    }
    expected_diagnostics = sorted(
        [
            *base_diagnostics,
            *([{**limit_row, "scope": "publication"}] if selected_failed else []),
        ],
        key=canonical_json_bytes,
    )
    if not _same(diagnostics, expected_diagnostics):
        raise ValueError("final diagnostic list differs from the actual selected-copy disposition")
    if diagnostic_input != b"".join(canonical_json_bytes(row) + b"\n" for row in diagnostics):
        raise ValueError("measured diagnostic input is not canonical owner-derived JSONL")
    expected_stderr = b"" if stderr_failed else diagnostic_input
    stderr = owner.stderr_bytes()
    if stderr != expected_stderr:
        raise ValueError("retained public stderr differs from its all-or-none disposition")
    expected_manifest = list(diagnostics)
    if stderr_failed:
        expected_manifest = [limit_row]
    if owner._manifest_diagnostics_bytes != canonical_json_bytes(expected_manifest):
        raise ValueError("manifest diagnostics differ from the final stderr disposition")
    stderr_sha = hashlib.sha256(stderr).hexdigest()
    if len(stderr) > limits["max_stderr_bytes"] or not _same(
        value["stderr"],
        {
            "available": not stderr_failed,
            "bytes_base64": base64.b64encode(stderr).decode("ascii"),
            "size_bytes": len(stderr),
            "sha256": stderr_sha,
            "diagnostics_sha256": stderr_sha,
        },
    ):
        raise ValueError("final stderr metadata differs from actual canonical public bytes")
    if not _same(
        value["measurements"]["public_stderr"],
        {
            "allowed": not stderr_failed,
            "measured_bytes": len(diagnostic_input),
            "retained_bytes": len(expected_stderr),
        },
    ):
        raise ValueError("final stderr measurement differs from the original encoded input")
    if not _same(
        value["measurements"]["selected_stdout"],
        {
            "allowed": not selected_failed,
            "measured_bytes": len(raw),
            "retained_bytes": 0 if selected_failed else len(raw),
        },
    ):
        raise ValueError("final public measurement differs from actual retained bytes")
    # Recreate the legacy wire-independent preimage shapes here, not by calling
    # the producer, finalizer, copy function or a producer expected-value builder.
    selected = {
        "allowed": not selected_failed,
        "bytes": len(raw),
        "sha256": selected_sha,
        "retained": b"" if selected_failed else raw,
        "retained_bytes": 0 if selected_failed else len(raw),
        "partial_disposed": selected_failed,
        "publication_outcome": "selected_artifact_unavailable"
        if selected_failed
        else "published_artifact",
        "diagnostic_code": "CSV-NEXT-LIMIT-003" if selected_failed else None,
    }
    seal = {
        "algorithm": "sha256",
        "sha256": digest(
            {
                "decision_run_fingerprint": run.record()["context"]["run_fingerprint"],
                "response_bytes": _canonical_measurement_value(response_bytes),
                "validated_request_id": validated_response["request_id"]
                if validated_response is not None
                else None,
                "response_sha256": validated_response["raw_sha256"]
                if validated_response is not None
                else None,
                "response_model_digest": validated_response["model_digest"]
                if validated_response is not None
                else None,
                "artifact_bytes": _canonical_measurement_value(
                    {item.descriptor()["path"]: item.wire_bytes() for item in published_artifacts}
                ),
                "artifact_descriptors": {
                    item.descriptor()["path"]: item.descriptor() for item in published_artifacts
                },
                "selector": selector,
                "selected_stdout": _canonical_measurement_value(selected),
                "sealed_stdout_result": _canonical_measurement_value(stdout_bytes),
                "diagnostic_jsonl": _canonical_measurement_value(stderr),
                "measurement_digest": digest(value["measurements"]),
            }
        ),
        "preimage_sha256": digest(
            {
                "semantic_decision": run.record(),
                "response": response,
                "artifacts": artifacts,
                "stdout": stdout,
                "stderr": stderr.hex(),
                "measurements": value["measurements"],
            }
        ),
    }
    if not _same(value["seal"], seal):
        raise ValueError("publication seal differs from the actual retained owners and bytes")
