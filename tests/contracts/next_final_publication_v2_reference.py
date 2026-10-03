"""Incremental immutable final publication owner; not production acceptance."""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, cast

from tests.contracts.next_final_publication_v2_validation import validate_final_publication_v2
from tests.contracts.next_public_diagnostic_v3_reference import derive_public_diagnostics_v3
from tests.contracts.next_public_diagnostic_v3_validation import validate_public_diagnostics_v3
from tests.contracts.next_publication_candidates_v3_reference import (
    RetainedRequestBoundPublicationCandidatesV3,
)
from tests.contracts.next_publication_candidates_v3_validation import (
    validate_request_bound_publication_candidates_v3,
)
from tests.contracts.next_reference_validation import (
    _canonical_measurement_value,
    _public_limit_diagnostic,
    canonical_json_bytes,
    copy_selected_stdout,
    digest,
)
from tests.contracts.next_semantic_core_v3_reference import (
    RejectedSemanticDecisionV3,
    ValidatedSemanticDecisionV3,
)


@dataclass(frozen=True, slots=True, init=False)
class RetainedFinalPublicationV2:
    """Same candidates owner plus immutable final public bytes and metadata."""

    _candidates: RetainedRequestBoundPublicationCandidatesV3 = field(repr=False)
    _stdout_bytes: bytes = field(repr=False)
    _stderr_bytes: bytes = field(repr=False)
    _diagnostic_input_bytes: bytes = field(repr=False)
    _manifest_diagnostics_bytes: bytes = field(repr=False)
    _record_bytes: bytes = field(repr=False)

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("final publications are created by the candidates-only factory")

    def candidates(self) -> RetainedRequestBoundPublicationCandidatesV3:
        return self._candidates

    def stdout_bytes(self) -> bytes:
        return self._stdout_bytes

    def stderr_bytes(self) -> bytes:
        return self._stderr_bytes

    def manifest_diagnostics(self) -> tuple[dict[str, Any], ...]:
        return tuple(json.loads(self._manifest_diagnostics_bytes))

    def record(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(self._record_bytes))


def retain_final_publication_v2(
    candidates: RetainedRequestBoundPublicationCandidatesV3,
) -> RetainedFinalPublicationV2:
    """Only the same validated candidates supply status, bytes and measurements."""

    if type(candidates) is not RetainedRequestBoundPublicationCandidatesV3:
        raise TypeError("final publication requires a nominal candidates owner")
    run = candidates.run_decision()
    candidate_record = candidates.record()
    validate_request_bound_publication_candidates_v3(candidate_record, candidates, run_decision=run)
    core = run.semantic_decision()
    if core is not None and type(core) not in {
        ValidatedSemanticDecisionV3,
        RejectedSemanticDecisionV3,
    }:
        raise ValueError("unavailable final-publication branches are not admitted here yet")
    runtime = run.runtime_result()
    request = runtime.request_frame()
    limits = request.record()["limits"]
    selector = request.analysis_context().run_context()["stdout_selector"]
    if selector not in {"next:semantic-json", "next:plantuml"}:
        raise ValueError("summary/manifest final-publication branches are not admitted here yet")
    selected_artifact = next(
        (
            item
            for item in candidates.artifacts()
            if "next:" + item.descriptor()["format"] == selector
        ),
        None,
    )
    selected = copy_selected_stdout(
        selected_artifact.wire_bytes() if selected_artifact is not None else b"",
        limit=limits["max_selected_stdout_bytes"],
    )
    diagnostics = derive_public_diagnostics_v3(run)
    validate_public_diagnostics_v3(diagnostics, run)
    if not selected["allowed"]:
        diagnostics = tuple(
            sorted(
                (*diagnostics, _public_limit_diagnostic(scope="publication")),
                key=canonical_json_bytes,
            )
        )
    # Encode the final diagnostic list once, before any public write.
    diagnostic_input = b"".join(canonical_json_bytes(row) + b"\n" for row in diagnostics)
    stderr_size = len(diagnostic_input)
    stderr_failed = stderr_size > limits["max_stderr_bytes"]
    stderr = b"" if stderr_failed else diagnostic_input
    manifest_diagnostics = (_public_limit_diagnostic(),) if stderr_failed else diagnostics
    measurements: dict[str, Any] = {
        f"adapter_{stream}": {
            "allowed": held["captured_bytes"] <= held["limit_bytes"],
            "measured_bytes": held["captured_bytes"],
            "retained_bytes": held["capture_retained_bytes"],
        }
        if (held := candidate_record["capture_measurements"][f"adapter_{stream}"]) is not None
        else None
        for stream in ("stdout", "stderr")
    }
    measurements.update(
        public_stderr={
            "allowed": not stderr_failed,
            "measured_bytes": stderr_size,
            "retained_bytes": len(stderr),
        },
        selected_stdout={
            "allowed": selected["allowed"],
            "measured_bytes": selected["bytes"],
            "retained_bytes": selected["retained_bytes"],
        },
    )
    capture_failed = any(
        held is not None and not held["allowed"]
        for held in (measurements["adapter_stdout"], measurements["adapter_stderr"])
    )
    publication_failed = capture_failed or stderr_failed
    response_bytes = b""
    validated_response = None
    if type(core) is ValidatedSemanticDecisionV3:
        frame = core.transport_candidate().response_frame()
        response_bytes = frame.raw_bytes
        validated_response = {
            "request_id": core.request_id,
            "raw_sha256": frame.sha256,
            "model_digest": core.transport_candidate().semantic_payload()["model_digest"],
            "byte_length": len(frame.raw_bytes),
        }
    response = None if publication_failed else validated_response
    artifacts = (
        []
        if publication_failed
        else sorted(candidates.artifacts(), key=lambda item: item.descriptor()["path"])
    )
    stdout_bytes = selected["retained"]
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
    elif not selected["allowed"]:
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
        and selected["allowed"],
        "copy_status": (
            "not_attempted"
            if selected_artifact is None or publication_failed
            else "published"
            if selected["allowed"]
            else "unavailable"
        ),
        "candidate": selected_artifact.descriptor()
        if selected_artifact is not None and not publication_failed
        else None,
        "result_bytes_base64": base64.b64encode(stdout_bytes).decode("ascii"),
        "result_size_bytes": len(stdout_bytes),
        "result_sha256": hashlib.sha256(stdout_bytes).hexdigest(),
    }
    if selected_artifact is not None:
        stdout.update(selected_size_bytes=selected["bytes"], selected_sha256=selected["sha256"])
    run_record = run.record()
    artifact_rows = [
        {
            "descriptor": item.descriptor(),
            "bytes_base64": base64.b64encode(item.wire_bytes()).decode("ascii"),
        }
        for item in artifacts
    ]
    record = {
        "schema": "code-structure-viz.next-publication-decision/v2",
        "version": 2,
        "semantic_decision": run_record,
        "candidates": candidate_record,
        "response": response,
        "artifacts": artifact_rows,
        "stdout": stdout,
        "stderr": {
            "available": not stderr_failed,
            "bytes_base64": base64.b64encode(stderr).decode("ascii"),
            "size_bytes": len(stderr),
            "sha256": hashlib.sha256(stderr).hexdigest(),
            "diagnostics_sha256": hashlib.sha256(stderr).hexdigest(),
        },
        "measurements": measurements,
        "publication_outcome": (
            "payload_unavailable"
            if publication_failed
            else "published"
            if selected["allowed"]
            else "selected_artifact_unavailable"
        ),
        "exit_code": 3
        if publication_failed or not selected["allowed"]
        else run_record["exit_code"],
        "seal": {
            "algorithm": "sha256",
            "sha256": digest(
                {
                    "decision_run_fingerprint": run_record["context"]["run_fingerprint"],
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
                        {item.descriptor()["path"]: item.wire_bytes() for item in artifacts}
                    ),
                    "artifact_descriptors": {
                        item.descriptor()["path"]: item.descriptor() for item in artifacts
                    },
                    "selector": selector,
                    "selected_stdout": _canonical_measurement_value(selected),
                    "sealed_stdout_result": _canonical_measurement_value(stdout_bytes),
                    "diagnostic_jsonl": _canonical_measurement_value(stderr),
                    "measurement_digest": digest(measurements),
                }
            ),
            "preimage_sha256": digest(
                {
                    "semantic_decision": run_record,
                    "response": response,
                    "artifacts": artifact_rows,
                    "stdout": stdout,
                    "stderr": stderr.hex(),
                    "measurements": measurements,
                }
            ),
        },
    }
    instance = object.__new__(RetainedFinalPublicationV2)
    object.__setattr__(instance, "_candidates", candidates)
    object.__setattr__(instance, "_stdout_bytes", stdout_bytes)
    object.__setattr__(instance, "_stderr_bytes", stderr)
    object.__setattr__(instance, "_diagnostic_input_bytes", diagnostic_input)
    object.__setattr__(
        instance, "_manifest_diagnostics_bytes", canonical_json_bytes(list(manifest_diagnostics))
    )
    object.__setattr__(instance, "_record_bytes", canonical_json_bytes(record))
    validate_final_publication_v2(record, instance, candidates=candidates)
    return instance


def project_final_publication_v2(owner: RetainedFinalPublicationV2) -> dict[str, Any]:
    if type(owner) is not RetainedFinalPublicationV2:
        raise TypeError("final projection requires a nominal publication owner")
    record = owner.record()
    validate_final_publication_v2(record, owner, candidates=owner.candidates())
    return record
