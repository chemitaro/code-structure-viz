"""Run-v3 joins the actual runtime2 and Core3; no final publication authority."""

import hashlib
import json
from copy import copy
from importlib import import_module, util
from pathlib import Path
from typing import Any

import pytest
from jsonschema import ValidationError  # type: ignore[import-untyped]

from tests.contracts import next_runtime_v2_reference as runtime_reference
from tests.contracts.next_reference_validation import canonical_json_bytes
from tests.contracts.next_run_decision_v3_reference import (
    project_request_bound_run_decision_v3,
    retain_request_bound_run_decision_v3,
)
from tests.contracts.next_run_decision_v3_validation import validate_request_bound_run_decision_v3
from tests.contracts.next_semantic_core_v3_reference import (
    RejectedSemanticDecisionV3,
    decide_semantic_candidate_v3,
    inspect_semantic_candidate_v3,
)
from tests.contracts.test_next_core_failure_v2 import runtime_for_core_wire
from tests.contracts.test_next_exchange_v2 import exchange_evidence
from tests.contracts.test_next_process_observation_v2 import complete_evidence
from tests.contracts.test_next_provenance_v3 import matching_runtime_core_v3
from tests.contracts.test_next_semantic_core_v3 import (
    SOURCE_BYTES,
    add_literal_reference_props_v3,
    core_inputs_v3,
    exclude_value_module_with_root_v3,
    omit_selected_button_module_v3,
    unknown_value_export_v3,
)


def independent_run_preimage_v3(core: Any) -> dict[str, Any]:
    candidate = core.transport_candidate()
    frame = candidate.request_frame()
    request, context = frame.record(), frame.analysis_context()
    config, run = context.domain_config(), context.run_context()
    return {
        "source_view_fingerprint": core.source_seal().source_view.fingerprint,
        "source_plan_digest": core.source_seal().recompute_plan_digest(),
        "domain_config_digest": hashlib.sha256(
            json.dumps(
                {key: row for key, row in config.items() if key != "domain_config_digest"},
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode()
        ).hexdigest(),
        "projects": request["projects"],
        "targets": context.analysis_intent()["targets"],
        "formats": run["requested_formats"],
        "stdout_selector": run["stdout_selector"],
        "limits": request["limits"],
        "node_version": candidate.runtime_binding()["node_observation"]["version"],
        "typescript_version": "5.9.2",
        "adapter_version": "0.2.0",
        "protocol": "code-structure-viz.next-adapter/v2",
        "trusted_environment_digest": request["trusted_type_environment"]["sha256"],
        "semantic_admission_profile_id": "next-source-inventory-safe-subset-v1",
    }


def test_run_joins_core_with_fourteen_key_fingerprint(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    runtime = runtime_for_core_wire(seal, assets, request, policy, wire)
    candidate = runtime.transport_candidate()
    assert candidate is not None
    core = decide_semantic_candidate_v3(candidate, seal, assets)
    assert core.gate()["payload_available"] is True
    module = "tests.contracts.next_run_decision_v3_reference"
    assert util.find_spec(module) is not None, "same runtime/Core3 have no retained run3"
    run = import_module(module)
    owner = run.retain_request_bound_run_decision_v3(runtime, semantic_decision=core)
    value = run.project_request_bound_run_decision_v3(owner)
    assert owner.runtime_result() is runtime and owner.semantic_decision() is core
    assert value["schema"] == "code-structure-viz.next-run-decision/v3" and value["version"] == 3
    assert (value["kind"], value["status"], value["outcome"], value["exit_code"]) == (
        "request_bound_success",
        "complete",
        "complete",
        0,
    )
    preimage = independent_run_preimage_v3(core)
    assert len(preimage) == 14
    expected = hashlib.sha256(
        json.dumps(preimage, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()
    assert value["context"]["run_fingerprint"] == expected
    assert (
        value["context"]["compatibility_id"] == core.compatibility_descriptor()["compatibility_id"]
    )
    assert value["context"]["observed_prefix"] == value["provenance"]["observed"]
    assert value["core_measurement"] == {"kind": "entity_budget", "actual": 4, "limit": 500}


@pytest.mark.parametrize("kind", ["parse_file", "read_file"])
def test_source_unavailable_run_keeps_compatibility_and_null_entity_budget(
    tmp_path: Path, kind: str
) -> None:
    sources = {
        **SOURCE_BYTES,
        "src/value.ts": SOURCE_BYTES["src/value.ts"] + b"require(variable);\n",
    }
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path, sources=sources)
    exclude_value_module_with_root_v3(wire, request, kind)
    runtime = runtime_for_core_wire(seal, assets, request, policy, wire)
    candidate = runtime.transport_candidate()
    assert candidate is not None
    core = decide_semantic_candidate_v3(candidate, seal, assets)
    assert core.gate()["diagnostic_code"] == "CSV-NEXT-SOURCE-003"
    assert core.gate()["payload_available"] is False
    owner = retain_request_bound_run_decision_v3(runtime, semantic_decision=core)
    value = project_request_bound_run_decision_v3(owner)
    assert (value["kind"], value["outcome"], value["payload_available"], value["exit_code"]) == (
        "request_bound_failure",
        "payload_unavailable",
        False,
        3,
    )
    assert (value["provenance"]["stage"], value["provenance"]["failure_code"]) == (
        "source_read",
        "CSV-NEXT-SOURCE-003",
    )
    assert (
        value["context"]["compatibility_id"] == core.compatibility_descriptor()["compatibility_id"]
    )
    preimage = independent_run_preimage_v3(core)
    expected = hashlib.sha256(
        json.dumps(preimage, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()
    assert value["context"]["run_fingerprint"] == expected
    assert value["core_measurement"] is None
    assert value["provenance"]["observed"]["budget"] == {"state": "unobserved", "value": None}
    assert all(
        value["provenance"]["observed"][slot]["state"] == "observed"
        for slot in ("semantic_payload", "compatibility", "model")
    )


def test_target_unavailable_run_keeps_its_proven_identity(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path, targets=["path:src/button.tsx"])
    omit_selected_button_module_v3(wire)
    runtime = runtime_for_core_wire(seal, assets, request, policy, wire)
    candidate = runtime.transport_candidate()
    assert candidate is not None
    core = decide_semantic_candidate_v3(candidate, seal, assets)
    assert core.gate()["diagnostic_code"] == "CSV-NEXT-TARGET-001"
    owner = retain_request_bound_run_decision_v3(runtime, semantic_decision=core)
    value = project_request_bound_run_decision_v3(owner)
    assert (value["provenance"]["stage"], value["provenance"]["failure_code"]) == (
        "target_resolution",
        "CSV-NEXT-TARGET-001",
    )
    assert (
        value["context"]["compatibility_id"] == core.compatibility_descriptor()["compatibility_id"]
    )
    assert value["core_measurement"] is None and value["outcome"] == "payload_unavailable"


@pytest.mark.parametrize("cause", ["export", "entity_budget"])
def test_validated_core_unavailable_run_preserves_identity_and_actual_budget(
    tmp_path: Path,
    cause: str,
) -> None:
    sources = (
        {
            **SOURCE_BYTES,
            "src/value.ts": (
                b'const value = makeValue();\nexport { value as "opaque-public-name" };\n'
            ),
        }
        if cause == "export"
        else None
    )
    seal, assets, request, policy, wire = core_inputs_v3(
        tmp_path,
        sources=sources,
        max_entities=3 if cause == "entity_budget" else 500,
    )
    if cause == "export":
        unknown_value_export_v3(wire)
    runtime = runtime_for_core_wire(seal, assets, request, policy, wire)
    candidate = runtime.transport_candidate()
    assert candidate is not None
    core = decide_semantic_candidate_v3(candidate, seal, assets)
    assert core.gate()["diagnostic_code"] == (
        "CSV-NEXT-EXPORT-001" if cause == "export" else "CSV-NEXT-LIMIT-005"
    )
    assert core.gate()["payload_available"] is False
    owner = retain_request_bound_run_decision_v3(runtime, semantic_decision=core)
    value = project_request_bound_run_decision_v3(owner)
    assert value["outcome"] == "payload_unavailable" and value["exit_code"] == 3
    assert (value["provenance"]["stage"], value["provenance"]["failure_code"]) == (
        "response_validation" if cause == "export" else "model_validation",
        "CSV-NEXT-EXPORT-001" if cause == "export" else "CSV-NEXT-LIMIT-005",
    )
    assert (
        value["context"]["compatibility_id"] == core.compatibility_descriptor()["compatibility_id"]
    )
    assert (
        value["context"]["run_fingerprint"]
        == hashlib.sha256(
            json.dumps(
                independent_run_preimage_v3(core),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode()
        ).hexdigest()
    )
    assert value["core_measurement"] == (
        None if cause == "export" else {"kind": "entity_budget", "actual": 4, "limit": 3}
    )
    assert value["provenance"]["observed"]["budget"]["state"] == (
        "unobserved" if cause == "export" else "observed"
    )


@pytest.mark.parametrize("failure", ["model_digest", "model_record_limit"])
def test_rejected_core_run_keeps_control_prefix_but_no_semantic_suffix(
    tmp_path: Path, failure: str
) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    if failure == "model_digest":
        wire["semantic_payload"]["model_digest"] = "0" * 64
    else:
        exclude_value_module_with_root_v3(wire, request, "module_relation")
        add_literal_reference_props_v3(wire, 10_001 - 17)
    runtime = runtime_for_core_wire(seal, assets, request, policy, wire)
    candidate = runtime.transport_candidate()
    assert candidate is not None
    core = inspect_semantic_candidate_v3(candidate, seal, assets)
    assert type(core) is RejectedSemanticDecisionV3
    assert core.failure()["model_records"] == (None if failure == "model_digest" else 10_001)
    owner = retain_request_bound_run_decision_v3(runtime, semantic_decision=core)
    value = project_request_bound_run_decision_v3(owner)
    assert value["outcome"] == "payload_unavailable" and value["exit_code"] == 3
    assert value["context"]["compatibility_id"] is None
    assert isinstance(value["context"]["run_fingerprint"], str)
    observed = value["provenance"]["observed"]
    assert observed["control_response"]["state"] == "observed"
    assert all(
        observed[slot] == {"state": "unobserved", "value": None}
        for slot in (
            "semantic_payload",
            "compatibility",
            "model",
            "budget",
        )
    )
    expected_measurement = (
        None
        if failure == "model_digest"
        else {
            "kind": "model_record_limit",
            "actual": 10_001,
            "limit": 10_000,
        }
    )
    assert value["core_measurement"] == expected_measurement


@pytest.mark.parametrize(
    "failure",
    [
        "unsupported_runtime",
        "protocol_failure",
        "bootstrap_failure",
        "semantic_failure",
        "stage_failed",
        "stdout_limit",
        "stderr_limit",
        "timeout",
        "write_failed",
        "read_failed",
    ],
)
def test_runtime_only_run_has_no_core_fingerprint_or_semantic_suffix(
    tmp_path: Path,
    failure: str,
) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    if failure in {
        "unsupported_runtime",
        "protocol_failure",
        "bootstrap_failure",
        "semantic_failure",
    }:
        wire["semantic_payload"] = None
        wire["control"]["result_kind"] = failure
        if failure == "unsupported_runtime":
            wire["control"]["runtime"].update(
                version_raw="20.19.0", version="20.19.0", eligibility="unsupported"
            )
        elif failure != "semantic_failure":
            wire["control"].update(runtime=None, binding={"state": "unbound", "request_id": None})
        response = runtime_reference.retain_response_frame_v2(
            json.dumps(wire).encode(), limits=request.record()["limits"]
        )
        evidence = exchange_evidence(policy, request, response)
        evidence["exit_code"] = {
            "unsupported_runtime": 66,
            "protocol_failure": 65,
            "bootstrap_failure": 67,
            "semantic_failure": 68,
        }[failure]
    else:
        response = None
        evidence = complete_evidence(policy)
        evidence.update(response=None, exit_code=-15, terminal_cause=failure)
        evidence["capture"].update(
            stdin_bytes=len(request.canonical_bytes),
            stdin_sent_bytes=len(request.canonical_bytes),
            stdout_bytes=0,
            stdout_retained_bytes=0,
            stderr_bytes=0,
            stderr_retained_bytes=0,
        )
        evidence["cleanup"].update(group_stop="verified", signals=["TERM"])
        if failure == "stage_failed":
            evidence.update(spawn=None, capture=None, exit_code=None)
            evidence["cleanup"].update(
                group_stop="not_required", signals=[], direct_child_waited=False
            )
        elif failure.endswith("_limit"):
            stream = failure.removesuffix("_limit")
            evidence["capture"][stream + "_bytes"] = 16_777_217 if stream == "stdout" else 65_537
            evidence["capture"][stream + "_eof"] = False
        elif failure == "timeout":
            evidence["capture"]["stdout_eof"] = False
        else:
            evidence["capture"].update(
                stdin_sent_bytes=1 if failure == "write_failed" else len(request.canonical_bytes),
                stdout_bytes=0 if failure == "write_failed" else 17,
                stdout_eof=False,
            )
    observation = runtime_reference.reference_process_observation_v2(policy, evidence)
    runtime = runtime_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, response
    )
    assert runtime.result_kind != "success" and runtime.transport_candidate() is None
    owner = retain_request_bound_run_decision_v3(runtime, semantic_decision=None)
    value = project_request_bound_run_decision_v3(owner)
    assert value["kind"] == "request_bound_failure" and value["outcome"] == "payload_unavailable"
    assert (
        value["context"]["run_fingerprint"] is None and value["context"]["compatibility_id"] is None
    )
    assert value["core_measurement"] is None
    expected_identity = {
        "unsupported_runtime": ("runtime_validation", "CSV-NEXT-NODE-001"),
        "protocol_failure": ("response_protocol", "CSV-NEXT-PROTOCOL-001"),
        "bootstrap_failure": ("bootstrap", "CSV-NEXT-NODE-004"),
        "semantic_failure": ("semantic_analysis", "CSV-NEXT-NODE-004"),
        "stage_failed": ("node_spawn", "CSV-NEXT-NODE-002"),
        "stdout_limit": ("adapter_stdout_capture", "CSV-NEXT-LIMIT-003"),
        "stderr_limit": ("adapter_stderr_capture", "CSV-NEXT-LIMIT-003"),
        "timeout": ("node_timeout", "CSV-NEXT-NODE-003"),
        "write_failed": ("node_process", "CSV-NEXT-NODE-004"),
        "read_failed": ("node_process", "CSV-NEXT-NODE-004"),
    }
    assert (value["provenance"]["stage"], value["provenance"]["failure_code"]) == expected_identity[
        failure
    ]
    assert all(
        value["provenance"]["observed"][slot] == {"state": "unobserved", "value": None}
        for slot in (
            "semantic_payload",
            "compatibility",
            "model",
            "budget",
        )
    )


@pytest.mark.parametrize(
    "mutation",
    ["fingerprint", "count", "observed_hash", "private", "float_version", "foreign_runtime"],
)
def test_run_validator_rederives_fields_even_after_metadata_cache_is_rehashed(
    tmp_path: Path, mutation: str
) -> None:
    runtime, core = matching_runtime_core_v3(tmp_path)
    original = retain_request_bound_run_decision_v3(runtime, semantic_decision=core)
    owner = copy(original)
    value = owner.record()
    if mutation == "fingerprint":
        value["context"]["run_fingerprint"] = "0" * 64
    elif mutation == "count":
        value["core_measurement"]["actual"] = 5
    elif mutation == "observed_hash":
        value["context"]["observed_prefix"]["model"]["value"]["sha256"] = "0" * 64
        value["provenance"]["observed"]["model"]["value"]["sha256"] = "0" * 64
    elif mutation == "private":
        value["context"]["cwd"] = "/private/secret"
    elif mutation == "float_version":
        value["version"] = 3.0
    else:
        other_path = tmp_path / "other"
        other_path.mkdir()
        other_runtime, other_core = matching_runtime_core_v3(other_path)
        assert core.request_id == other_core.request_id
        object.__setattr__(owner, "_runtime", other_runtime)
    object.__setattr__(
        owner, "_record_bytes", json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    )
    with pytest.raises((ValueError, ValidationError)):
        validate_request_bound_run_decision_v3(value, owner)


def test_run_refuses_a_fresh_equal_content_but_foreign_core(tmp_path: Path) -> None:
    other_path = tmp_path / "other"
    other_path.mkdir()
    runtime, core = matching_runtime_core_v3(tmp_path)
    _, foreign = matching_runtime_core_v3(other_path)
    assert core.request_id == foreign.request_id
    assert canonical_json_bytes(core.gate()) == canonical_json_bytes(foreign.gate())
    with pytest.raises(ValueError, match="same runtime owner"):
        retain_request_bound_run_decision_v3(runtime, semantic_decision=foreign)


def test_partial_safe_run_never_becomes_complete_even_with_safe_candidates(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    exclude_value_module_with_root_v3(wire, request, "module_relation")
    runtime = runtime_for_core_wire(seal, assets, request, policy, wire)
    candidate = runtime.transport_candidate()
    assert candidate is not None
    core = decide_semantic_candidate_v3(candidate, seal, assets)
    run = retain_request_bound_run_decision_v3(runtime, semantic_decision=core)
    value = run.record()
    assert (value["status"], value["outcome"], value["payload_available"], value["exit_code"]) == (
        "incomplete",
        "partial_safe",
        True,
        3,
    )
    assert value["core_measurement"] == {"kind": "entity_budget", "actual": 3, "limit": 500}
