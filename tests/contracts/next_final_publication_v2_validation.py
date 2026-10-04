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
    from tests.contracts.next_final_publication_v2_reference import (
        RetainedFinalPublicationV2,
        RetainedParentConfigurationV2,
    )
    from tests.contracts.next_runtime_v2_reference import RetainedNextAnalysisContextV2


def _same(value: Any, expected: Any) -> bool:
    return canonical_json_bytes(value) == canonical_json_bytes(expected)


def validate_parent_configuration_v2(
    owner: RetainedParentConfigurationV2, *, context: RetainedNextAnalysisContextV2
) -> None:
    from tests.contracts.next_final_publication_v2_reference import RetainedParentConfigurationV2
    from tests.contracts.next_runtime_v2_reference import RetainedNextAnalysisContextV2

    if (
        type(owner) is not RetainedParentConfigurationV2
        or type(context) is not RetainedNextAnalysisContextV2
    ):
        raise TypeError("parent selection requires nominal configuration/context owners")
    if owner.analysis_context() is not context:
        raise ValueError("parent selection requires the same analysis context")
    config = context.domain_config()
    expected = {
        "next_projects": [row["root"] for row in config["projects"]],
        "next_targets": config["targets"],
        "formats": context.run_context()["requested_formats"],
        "upstream_depth": config["upstream_depth"],
        "downstream_depth": config["downstream_depth"],
        "limits": config["limits"],
        "trusted_environment": config["trusted_environment_digest"],
    }
    selections = owner.selections()
    if (
        owner.source not in ("builtin", "repository", "explicit")
        or type(selections) is not dict
        or selections.keys() != expected.keys()
    ):
        raise ValueError("parent selection input is not closed")
    for name, value in expected.items():
        row = selections[name]
        if (
            type(row) is not dict
            or row.keys() != {"source", "value"}
            or row["source"] not in ("builtin", "repository", "explicit", "cli")
        ):
            raise ValueError("parent selection origin is not an observed configuration source")
        if not _same(row["value"], value):
            raise ValueError("parent selected value differs from the analysis context")


def validate_run_summary_v1(value: Mapping[str, Any], owner: RetainedFinalPublicationV2) -> None:
    from tests.contracts.next_final_publication_v2_reference import RetainedFinalPublicationV2

    if type(owner) is not RetainedFinalPublicationV2:
        raise TypeError("summary validation requires a nominal final owner")
    publication = owner.record()
    validate_final_publication_v2(publication, owner, candidates=owner.candidates())
    _validate_schema("run-summary-v1", value)
    run = owner.candidates().run_decision().record()
    outcome = run["outcome"]
    for name in ("adapter_stdout", "adapter_stderr", "public_stderr"):
        measured = publication["measurements"][name]
        if measured is not None and measured["allowed"] is False:
            outcome = "payload_unavailable"
    domain = {"domain": "next", "status": "complete" if outcome == "complete" else "incomplete"}
    if outcome != "complete":
        domain["incomplete_kind"] = outcome
    expected = {
        "type": "run_summary",
        "schema": "code-structure-viz.run-summary/v1",
        "run_status": "complete" if publication["exit_code"] == 0 else "incomplete",
        "exit_code": publication["exit_code"],
        "domains": [domain],
        "manifest": "run-manifest.json",
    }
    if not _same(dict(value), expected):
        raise ValueError("summary differs from the same semantic and publication outcomes")


def validate_run_manifest_v2(value: Mapping[str, Any], owner: RetainedFinalPublicationV2) -> None:
    from tests.contracts.next_final_publication_v2_reference import RetainedFinalPublicationV2

    if type(owner) is not RetainedFinalPublicationV2:
        raise TypeError("root validation requires a nominal final owner")
    validate_final_publication_v2(owner.record(), owner, candidates=owner.candidates())
    _validate_run_manifest_fields(value, owner, pre_copy=False)


def _validate_run_manifest_fields(
    value: Mapping[str, Any], owner: RetainedFinalPublicationV2, *, pre_copy: bool
) -> None:
    _validate_schema("run-manifest-v2", value)
    _validate_domain_manifest_fields(value["domains"][0], owner, pre_copy=pre_copy)
    parent = owner.parent_configuration()
    context = parent.analysis_context()
    config, run_context = context.domain_config(), context.run_context()
    expected_config = {
        "schema": "code-structure-viz.config/v1",
        "source": parent.source,
        "resolved": {
            "next": {
                "projects": [row["root"] for row in config["projects"]],
                "targets": config["targets"],
                "formats": run_context["requested_formats"],
                "trusted_environment_digest": config["trusted_environment_digest"],
            },
            "traversal": {
                "upstream_depth": config["upstream_depth"],
                "downstream_depth": config["downstream_depth"],
            },
            "limits": config["limits"],
        },
        "value_sources": {name: row["source"] for name, row in parent.selections().items()},
    }
    expected_config["sha256"] = digest(expected_config)
    if not _same(value["config"], expected_config):
        raise ValueError("root config differs from the retained parent selection")
    run = owner.candidates().run_decision().record()
    publication = owner.record()
    exit_code = run["exit_code"] if pre_copy else publication["exit_code"]
    domain = value["domains"][0]
    expected = {
        "request_independent": False,
        "command": {
            "name": "snapshot",
            "domain": "next",
            "formats": run_context["requested_formats"],
            "stdout_selector": run_context["stdout_selector"],
        },
        "request": {
            "projects": [row["root"] for row in config["projects"]],
            "targets": config["targets"],
            "formats": run_context["requested_formats"],
            "upstream_depth": config["upstream_depth"],
            "downstream_depth": config["downstream_depth"],
        },
        "next_request": domain["request"],
        "next_config": config,
        "next_decision": run,
        "source": domain["source"],
        "run": {
            "status": "complete" if exit_code == 0 else "incomplete",
            "exit_code": exit_code,
            "fingerprint": run["context"]["run_fingerprint"],
            "run_context": run_context,
        },
        "artifacts": sorted(
            (item.descriptor() for item in owner.candidates().artifacts()),
            key=lambda row: row["path"],
        )
        if pre_copy
        else [row["descriptor"] for row in publication["artifacts"]],
        "diagnostics": domain["diagnostics"],
    }
    if not pre_copy:
        expected["next_publication"] = publication
    if value.keys() != expected.keys() | {
        "type",
        "schema",
        "tool",
        "contracts",
        "adapters",
        "domains",
        "config",
    }:
        raise ValueError("root manifest contains fields outside the Next snapshot projection")
    for name, row in expected.items():
        if not _same(value.get(name), row):
            raise ValueError(f"root {name} differs from the retained run/publication")


def validate_domain_manifest_v2(
    value: Mapping[str, Any],
    owner: RetainedFinalPublicationV2,
) -> None:
    from tests.contracts.next_final_publication_v2_reference import RetainedFinalPublicationV2

    if type(owner) is not RetainedFinalPublicationV2:
        raise TypeError("domain validation requires a nominal final publication owner")
    validate_final_publication_v2(owner.record(), owner, candidates=owner.candidates())
    _validate_domain_manifest_fields(value, owner, pre_copy=False)


def _validate_domain_manifest_fields(
    value: Mapping[str, Any], owner: RetainedFinalPublicationV2, *, pre_copy: bool
) -> None:
    _validate_schema("next-domain-manifest-v2", value)
    run = owner.candidates().run_decision()
    fingerprint = run.record()["context"]["run_fingerprint"]
    if not _same(value["run_fingerprint"], fingerprint) or (
        "run_fingerprint" in value["request"]
        if fingerprint is None
        else value["request"].get("run_fingerprint") != fingerprint
    ):
        raise ValueError("domain/request fingerprint differs from the same run")
    from tests.contracts.next_runtime_v2_reference import trusted_environment_manifest_v2

    runtime = run.runtime_result()
    request = runtime.request_frame().record()
    context = runtime.request_frame().analysis_context()
    config, run_context = context.domain_config(), context.run_context()
    seal = runtime.source_seal()
    trusted = trusted_environment_manifest_v2(runtime.execution_assets())
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
    ):
        if not _same(value["request"][key], config[key]):
            raise ValueError("domain request differs from the retained configuration")
    expected = {
        "config": config,
        "run_context": run_context,
        "source_plan_digest": seal.plan_digest,
        "domain_config_digest": config["domain_config_digest"],
        "targets": config["targets"],
        "formats": run_context["requested_formats"],
        "limits": request["limits"],
        "trusted_environment": trusted["environment_descriptor"],
        "decision": run.record(),
        "diagnostics": [
            row
            for line in owner._diagnostic_input_bytes.splitlines()
            if "scope" not in (row := json.loads(line))
        ]
        if pre_copy
        else list(owner.manifest_diagnostics()),
        "source": {
            "schema": seal.source_view.schema,
            "kind": seal.source_view.kind,
            "head_commit": seal.source_view.head_commit,
            "fingerprint": seal.source_view_fingerprint,
            "file_count": len(seal.source_view.files),
        },
    }
    if pre_copy:
        if "publication" in value:
            raise ValueError("pre-copy domain cannot contain its own publication")
    else:
        expected["publication"] = owner.record()
    core = run.semantic_decision()
    if type(core) is ValidatedSemanticDecisionV3:
        gate = core.gate()
        payload = core.transport_candidate().semantic_payload()
        compatibility = core.compatibility_descriptor()
        expected.update(
            projects=payload["model"]["projects"],
            coverage=payload["model"]["coverage"],
            compatibility_descriptor=compatibility,
            semantic_compatibility_id=compatibility["compatibility_id"],
            identity_versions=payload["identity_versions"],
        )
        actual = gate["actual"]
    else:
        actual = None
        counts = {
            name: 0
            for name in (
                "projects",
                "files",
                "modules",
                "components",
                "members",
                "relations",
                "facts",
                "internal_entities",
                "discovered",
                "published",
                "excluded",
                "failed",
            )
        }
        counts["projects"], counts["files"] = len(request["projects"]), len(request["files"])
        counts["discovered"] = counts["published"] = counts["projects"] + counts["files"]
        expected.update(
            projects=request["projects"],
            compatibility_descriptor=None,
            semantic_compatibility_id=None,
            identity_versions=None,
            coverage={
                "counts": counts,
                "failed_files": [],
                "affected_ids": [],
                "taint_frontier": [],
                "opaque_reason_counts": {},
                "unknown_relation_count": 0,
                "correlation_losses": [],
                "non_component_value_export_count": 0,
                "type_only_export_count": 0,
                "target_completeness": [],
            },
        )
    outcome = run.record()["outcome"]
    available = run.record()["payload_available"]
    measurements = owner.record()["measurements"]
    if not pre_copy and any(
        row is not None and row["allowed"] is False
        for name in ("adapter_stdout", "adapter_stderr", "public_stderr")
        for row in (measurements[name],)
    ):
        outcome, available, actual = "payload_unavailable", False, None
    expected.update(
        status="complete" if outcome == "complete" else "incomplete",
        payload_available=available,
        entity_count=actual if available else None,
        budget={
            "name": "max_entities",
            "requested": run_context["budget_requested"],
            "resolved": run_context["budget_resolved"],
            "actual": actual,
            "source": run_context["budget_source"],
            "outcome": outcome,
        },
        artifact_paths=sorted(item.descriptor()["path"] for item in owner.candidates().artifacts())
        if pre_copy
        else [row["descriptor"]["path"] for row in owner.record()["artifacts"]],
    )
    if value.get("incomplete_kind") != (None if outcome == "complete" else outcome):
        raise ValueError("domain incomplete kind differs from its outcome")
    control = runtime.control()
    node = control["runtime"] if control is not None else None
    if node is not None and node["eligibility"] == "supported":
        public_node = {"status": "available", "version": node["version"], "failure_kind": None}
    else:
        cause = runtime.observation()["terminal_cause"]
        failure = (
            "unsupported_version"
            if node is not None
            else "timeout"
            if cause == "timeout"
            else "spawn_failed"
            if cause in {"stage_failed", "spawn_failed"}
            else "process_failed"
        )
        public_node = {"status": "unavailable", "version": None, "failure_kind": failure}
    expected["toolchain"] = {
        "node": public_node,
        "node_version": public_node["version"],
        "typescript_version": trusted["typescript_version"],
        "adapter_version": request["adapter_version"],
        "protocol": request["protocol"],
    }
    for name, row in expected.items():
        if not _same(value.get(name), row):
            raise ValueError(f"domain {name} differs from its retained authority")


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
    validate_parent_configuration_v2(owner.parent_configuration(), context=frame.analysis_context())
    limits = frame.record()["limits"]
    selector = frame.analysis_context().run_context()["stdout_selector"]
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
    selected_descriptor = selected_artifact.descriptor() if selected_artifact is not None else None
    if selector != "manifest" and owner._manifest_input_bytes is not None:
        raise ValueError("non-manifest selection cannot retain manifest candidate bytes")
    if selector is None:
        run_record = run.record()
        summary_domain = {"domain": "next", "status": run_record["status"]}
        if run_record["status"] == "incomplete":
            summary_domain["incomplete_kind"] = run_record["outcome"]
        raw = (
            canonical_json_bytes(
                {
                    "type": "run_summary",
                    "schema": "code-structure-viz.run-summary/v1",
                    "run_status": run_record["status"],
                    "exit_code": run_record["exit_code"],
                    "domains": [summary_domain],
                    "manifest": "run-manifest.json",
                }
            )
            + b"\n"
        )
    elif selector == "manifest":
        if type(owner._manifest_input_bytes) is not bytes:
            raise ValueError("manifest selection requires the original pre-copy bytes")
        raw = owner._manifest_input_bytes
        manifest = json.loads(raw)
        if raw != canonical_json_bytes(manifest) + b"\n":
            raise ValueError("manifest candidate is not canonical JSONL")
        _validate_run_manifest_fields(manifest, owner, pre_copy=True)
        selected_descriptor = {
            "path": "run-manifest.json",
            "domain": "next",
            "format": "semantic-json",
            "media_type": "application/json",
            "size_bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
    selected_available = selector is None or selected_descriptor is not None
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
    if selector is None and (publication_failed or selected_failed):
        stdout_bytes = (
            canonical_json_bytes(
                {
                    "type": "stdout_result",
                    "schema": "code-structure-viz.stdout-result/v2",
                    "selector": None,
                    "availability": False,
                    "run_status": "incomplete",
                    "stable_reason": "run_summary",
                    "selected_stdout_unavailable": True,
                    "artifact": None,
                }
            )
            + b"\n"
        )
    elif not selected_available or publication_failed:
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
            "artifact": selected_descriptor,
        }
        if run.record()["status"] == "incomplete":
            replacement["incomplete_kind"] = run.record()["incomplete_kind"]
        stdout_bytes = canonical_json_bytes(replacement) + b"\n"
    stdout = {
        "selector": selector,
        "availability": selected_available and not publication_failed and not selected_failed,
        "copy_status": (
            "not_attempted"
            if not selected_available or publication_failed
            else "unavailable"
            if selected_failed
            else "published"
        ),
        "candidate": selected_descriptor if not publication_failed else None,
        "result_bytes_base64": base64.b64encode(stdout_bytes).decode("ascii"),
        "result_size_bytes": len(stdout_bytes),
        "result_sha256": hashlib.sha256(stdout_bytes).hexdigest(),
    }
    if selected_available:
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
