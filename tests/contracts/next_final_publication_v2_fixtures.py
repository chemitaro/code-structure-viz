"""Actual v3 owner fixtures for SI-06; never fabricated final measurements."""

import hashlib
import json
from pathlib import Path
from typing import Any

from code_structure_viz.adapters.next.source_acquisition import SourceAcquisitionSeal
from tests.contracts import next_runtime_v2_reference as runtime_reference
from tests.contracts.next_final_publication_v2_reference import (
    RetainedParentConfigurationV2,
    retain_parent_configuration_v2,
)
from tests.contracts.next_publication_candidates_v2_fixtures import _long_case_inputs
from tests.contracts.next_publication_candidates_v3_reference import (
    RetainedRequestBoundPublicationCandidatesV3,
    retain_request_bound_publication_candidates_v3,
)
from tests.contracts.next_reference_validation import recompute_record_id
from tests.contracts.next_run_decision_v3_reference import retain_request_bound_run_decision_v3
from tests.contracts.next_runtime_v2_reference import (
    reference_process_observation_v2,
    retain_runtime_result_v2,
)
from tests.contracts.next_semantic_core_v3_reference import (
    RejectedSemanticDecisionV3,
    decide_semantic_candidate_v3,
    inspect_semantic_candidate_v3,
)
from tests.contracts.test_next_core_failure_v2 import runtime_for_core_wire
from tests.contracts.test_next_exchange_v2 import exchange_evidence, shape_wire
from tests.contracts.test_next_process_observation_v2 import complete_evidence, policy_fixture
from tests.contracts.test_next_request_frame_v2 import run_context
from tests.contracts.test_next_semantic_core_v3 import (
    BUTTON_ID,
    MODULE_IDS,
    SOURCE_BYTES,
    compatibility_preimage_literal_v3,
    core_inputs_v3,
    exclude_value_module_with_root_v3,
    omit_selected_button_module_v3,
    unknown_value_export_v3,
)
from tests.contracts.test_next_source_inventory_v3 import exclude_record, refresh_wire
from tests.contracts.test_next_trusted_environment_v2 import profile_members


def explicit_parent_selections_v2(
    context: runtime_reference.RetainedNextAnalysisContextV2,
) -> dict[str, Any]:
    """Explicit reference inputs; no inference of real CLI/filesystem origins."""
    config = context.domain_config()
    values = {
        "next_projects": [row["root"] for row in config["projects"]],
        "next_targets": config["targets"],
        "formats": config["formats"],
        "upstream_depth": config["upstream_depth"],
        "downstream_depth": config["downstream_depth"],
        "limits": config["limits"],
        "trusted_environment": config["trusted_environment_digest"],
    }
    return {name: {"value": value, "source": "explicit"} for name, value in values.items()}


def parent_configuration_fixture_v2(
    candidates: RetainedRequestBoundPublicationCandidatesV3,
) -> RetainedParentConfigurationV2:
    context = candidates.run_decision().runtime_result().request_frame().analysis_context()
    return retain_parent_configuration_v2(
        context, source="explicit", selections=explicit_parent_selections_v2(context)
    )


def stage_failed_candidates_v3(
    tmp_path: Path, *, selector: str | None = None
) -> RetainedRequestBoundPublicationCandidatesV3:
    seal, assets, request, policy, _wire = core_inputs_v3(tmp_path, stdout_selector=selector)
    evidence = complete_evidence(policy)
    evidence.update(
        spawn=None, capture=None, response=None, exit_code=None, terminal_cause="stage_failed"
    )
    evidence["cleanup"].update(group_stop="not_required", signals=[], direct_child_waited=False)
    observation = reference_process_observation_v2(policy, evidence)
    runtime = retain_runtime_result_v2(seal, assets, request, policy, observation, None)
    run = retain_request_bound_run_decision_v3(runtime, semantic_decision=None)
    return retain_request_bound_publication_candidates_v3(run)


def observed_zero_capture_candidates_v3(
    tmp_path: Path,
) -> RetainedRequestBoundPublicationCandidatesV3:
    seal, assets, request, policy, _wire = core_inputs_v3(
        tmp_path, stdout_selector="next:semantic-json"
    )
    evidence = complete_evidence(policy)
    evidence.update(response=None, exit_code=-15, terminal_cause="timeout")
    evidence["capture"].update(
        stdin_bytes=len(request.canonical_bytes),
        stdin_sent_bytes=len(request.canonical_bytes),
        stdout_bytes=0,
        stdout_retained_bytes=0,
        stderr_bytes=0,
        stderr_retained_bytes=0,
        stdout_eof=False,
    )
    evidence["cleanup"].update(group_stop="verified", signals=["TERM"])
    observation = reference_process_observation_v2(policy, evidence)
    runtime = retain_runtime_result_v2(seal, assets, request, policy, observation, None)
    run = retain_request_bound_run_decision_v3(runtime, semantic_decision=None)
    return retain_request_bound_publication_candidates_v3(run)


def runtime_control_failure_candidates_v3(
    tmp_path: Path,
    failure: str,
) -> RetainedRequestBoundPublicationCandidatesV3:
    seal, assets, request, policy, wire = core_inputs_v3(
        tmp_path, stdout_selector="next:semantic-json"
    )
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
    observation = reference_process_observation_v2(policy, evidence)
    runtime = retain_runtime_result_v2(seal, assets, request, policy, observation, response)
    return retain_request_bound_publication_candidates_v3(
        retain_request_bound_run_decision_v3(runtime)
    )


def capture_overflow_candidates_v3(
    tmp_path: Path,
    stream: str,
) -> RetainedRequestBoundPublicationCandidatesV3:
    assert stream in {"stdout", "stderr"}
    seal, assets, request, policy, _wire = core_inputs_v3(
        tmp_path, stdout_selector="next:semantic-json"
    )
    evidence = complete_evidence(policy)
    evidence.update(response=None, exit_code=-15, terminal_cause=stream + "_limit")
    evidence["capture"].update(
        stdin_bytes=len(request.canonical_bytes),
        stdin_sent_bytes=len(request.canonical_bytes),
        stdout_bytes=0,
        stdout_retained_bytes=0,
        stderr_bytes=0,
        stderr_retained_bytes=0,
    )
    evidence["capture"][stream + "_bytes"] = (
        request.record()["limits"][f"max_adapter_{stream}_capture_bytes"] + 1
    )
    evidence["capture"][stream + "_eof"] = False
    evidence["cleanup"].update(group_stop="verified", signals=["TERM"])
    observation = reference_process_observation_v2(policy, evidence)
    runtime = retain_runtime_result_v2(seal, assets, request, policy, observation, None)
    run = retain_request_bound_run_decision_v3(runtime, semantic_decision=None)
    return retain_request_bound_publication_candidates_v3(run)


def stderr_boundary_candidates_v3(
    tmp_path: Path,
    delta: int,
) -> RetainedRequestBoundPublicationCandidatesV3:
    """Real missing-target proof, calibrated legal paths, configured 64 KiB cap."""
    assert delta in {0, 1}
    targets = [
        "path:src/missing/"
        + f"{index:02d}/"
        + ("a" * 200 + "/") * 18
        + "b" * (120 + (delta if index == 15 else 0))
        + ".tsx"
        for index in range(16)
    ]
    seal, assets, request, policy, wire = core_inputs_v3(
        tmp_path, targets=targets, stdout_selector="next:semantic-json"
    )
    rows = [
        {"target_key": target, "status": "failed", "record_ids": [], "reason": "missing"}
        for target in targets
    ]
    wire["semantic_payload"]["proof"]["target_resolutions"] = rows
    wire["semantic_payload"]["model"]["coverage"]["target_completeness"] = [
        dict(row) for row in rows
    ]
    refresh_wire(wire)
    runtime = runtime_for_core_wire(seal, assets, request, policy, wire)
    candidate = runtime.transport_candidate()
    assert candidate is not None
    core = decide_semantic_candidate_v3(candidate, seal, assets)
    assert core.gate()["diagnostic_code"] == "CSV-NEXT-TARGET-001"
    run = retain_request_bound_run_decision_v3(runtime, semantic_decision=core)
    return retain_request_bound_publication_candidates_v3(run)


def partial_stderr_overflow_candidates_v3(
    tmp_path: Path,
) -> RetainedRequestBoundPublicationCandidatesV3:
    """Actual isolated failed files produce more than the configured 64 KiB JSONL."""
    failed_paths = ["src/" + ("a" * 150 + "/") * 4 + f"failed-{n:02d}.ts" for n in range(80)]
    seal, assets, request, policy, wire = core_inputs_v3(
        tmp_path,
        sources={**SOURCE_BYTES, **dict.fromkeys(failed_paths, b"export {}; const broken = (\n")},
        targets=["path:src/button.tsx"],
        stdout_selector="next:semantic-json",
    )
    model, proof = wire["semantic_payload"]["model"], wire["semantic_payload"]["proof"]
    failed = [row for row in request.record()["files"] if row["path"] in failed_paths]
    for row in failed:
        exclude_record(wire, "files", row["id"], reason="tainted", taints=["parse_file"])
        module = {
            "kind": "module",
            "project_id": row["project_id"],
            "path": row["path"],
            "router_context": "none",
            "client_entry": False,
            "derived_roles": [],
        }
        module["id"] = recompute_record_id(module)
        proof["discovered_records"].append(
            {
                "collection": "modules",
                "record_id": module["id"],
                "taints": ["parse_file"],
                "record": module,
            }
        )
        proof["excluded"].append(
            {"collection": "modules", "record_id": module["id"], "reason": "tainted"}
        )
        fact = {"kind": "router_context", "owner_id": module["id"], "value": "none"}
        fact["id"] = recompute_record_id(fact)
        proof["discovered_records"].append(
            {
                "collection": "facts",
                "record_id": fact["id"],
                "taints": ["parse_file"],
                "record": fact,
            }
        )
        proof["excluded"].append(
            {"collection": "facts", "record_id": fact["id"], "reason": "tainted"}
        )
        root_id = "next:failure:" + hashlib.sha256(row["path"].encode()).hexdigest()
        proof["failed"].append(
            {"collection": "files", "record_id": row["id"], "reason": "parse_file"}
        )
        proof["failure_roots"].append(
            {
                "id": root_id,
                "collection": "files",
                "kind": "parse_file",
                "path_ref": row["path"],
                "record_ids": sorted([row["id"], module["id"], fact["id"]]),
            }
        )
        proof["causal_edges"].extend(
            {"source_id": root_id, "record_id": record_id, "rule": "file_all_records"}
            for record_id in (row["id"], module["id"], fact["id"])
        )
        proof["causal_edges"].append(
            {
                "source_id": module["id"],
                "record_id": fact["id"],
                "rule": "identity_dependency",
            }
        )
    failed_ids = {row["id"] for row in failed}
    proof["excluded"] = [row for row in proof["excluded"] if row["record_id"] not in failed_ids]
    model["coverage"]["failed_files"] = [
        {"path": path, "reason": "parse_file"} for path in sorted(failed_paths)
    ]
    button_file = next(
        row["id"] for row in request.record()["files"] if row["path"] == "src/button.tsx"
    )
    target = {
        "target_key": "path:src/button.tsx",
        "status": "resolved",
        "record_ids": sorted([button_file, MODULE_IDS["src/button.tsx"], BUTTON_ID]),
    }
    proof["target_resolutions"] = [target]
    model["coverage"]["target_completeness"] = [{**target, "status": "complete"}]
    refresh_wire(wire)
    runtime = runtime_for_core_wire(seal, assets, request, policy, wire)
    candidate = runtime.transport_candidate()
    assert candidate is not None
    core = decide_semantic_candidate_v3(candidate, seal, assets)
    assert core.gate()["outcome"] == "partial_safe" and core.gate()["actual"] == 4
    return retain_request_bound_publication_candidates_v3(
        retain_request_bound_run_decision_v3(runtime, semantic_decision=core)
    )


def _independent_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _large_inputs_v3(
    tmp_path: Path,
    *,
    prefix_length: int,
    longer_names: int = 0,
    context_digits: int = 2,
) -> tuple[
    SourceAcquisitionSeal,
    runtime_reference.RetainedExecutionAssets,
    runtime_reference.RetainedRequestFrameV2,
    dict[str, Any],
    dict[str, Any],
    bytes,
]:
    # The shared helper generates actual descriptor-relative files and a source
    # seal. No legacy semantic/run owner or publication producer is reused.
    seal, _old_assets, _old_request, _old_policy, old_wire, old_expected = _long_case_inputs(
        tmp_path,
        prefix_length=prefix_length,
        longer_names=longer_names,
        context_digits=context_digits,
    )
    members = profile_members()
    members[runtime_reference.ENTRYPOINT_MEMBER] = (
        "adapter",
        b"// CodeStructureViz-Adapter-Version: 0.2.0\n",
    )
    assets = runtime_reference.retain_execution_assets_v1(members)
    context = runtime_reference.retain_next_analysis_context_v2(
        seal,
        assets,
        targets=[],
        upstream_depth=0,
        downstream_depth=0,
        run_context={
            **run_context(),
            "budget_requested": 1000,
            "budget_resolved": 1000,
            "budget_source": "cli",
            "stdout_selector": "next:semantic-json",
        },
    )
    request = runtime_reference.build_request_frame_v2(seal, assets, context)
    request_record, config = request.record(), context.domain_config()
    policy = policy_fixture()
    policy.update(
        request_id=request.request_id,
        adapter=assets.adapter_identity(),
        execution_asset_set_id=assets.descriptor()["asset_set_id"],
        trusted_environment_digest=request_record["trusted_type_environment"]["sha256"],
        limits=request_record["limits"],
    )
    wire = shape_wire(request)
    wire["semantic_payload"]["model"] = old_wire["semantic_payload"]["model"]
    wire["semantic_payload"]["proof"] = old_wire["semantic_payload"]["proof"]
    refresh_wire(wire)
    assert len(wire["semantic_payload"]["proof"]["discovered_records"]) == 3004
    # Independent explicit v3 fields, standard codec and worked all-safe counts.
    # The old expected record is a wire-independent literal, not a v3 renderer.
    expected = json.loads(old_expected)
    compatibility = compatibility_preimage_literal_v3()
    compatibility_id = hashlib.sha256(_independent_bytes(compatibility)).hexdigest()
    expected.update(
        schema="code-structure-viz.semantic/v3",
        semantic_compatibility_id=compatibility_id,
        compatibility_descriptor={
            "schema": "code-structure-viz.next-semantic-compatibility/v3",
            **compatibility,
            "compatibility_id": compatibility_id,
        },
    )
    preimage = {
        "source_view_fingerprint": seal.source_view_fingerprint,
        "source_plan_digest": seal.plan_digest,
        "domain_config_digest": config["domain_config_digest"],
        "projects": request_record["projects"],
        "targets": [],
        "formats": ["semantic-json"],
        "stdout_selector": "next:semantic-json",
        "limits": request_record["limits"],
        "node_version": "22.10.0",
        "typescript_version": "5.9.2",
        "adapter_version": "0.2.0",
        "protocol": "code-structure-viz.next-adapter/v2",
        "trusted_environment_digest": request_record["trusted_type_environment"]["sha256"],
        "semantic_admission_profile_id": "next-source-inventory-safe-subset-v1",
    }
    assert len(preimage) == 14
    expected["request"]["run_fingerprint"] = hashlib.sha256(
        _independent_bytes(preimage)
    ).hexdigest()
    partition = {
        "profile_id": "next-source-inventory-safe-subset-v1",
        "request_id": request.request_id,
        "projects": [
            {
                "project_id": project["id"],
                "safe_file_ids": sorted(project["file_ids"]),
                "failed_file_ids": [],
                "excluded_file_ids": [],
            }
            for project in request_record["projects"]
        ],
    }
    expected["source_inventory_summary"] = {
        "profile_id": "next-source-inventory-safe-subset-v1",
        "source_partition_fingerprint": hashlib.sha256(_independent_bytes(partition)).hexdigest(),
        "acquired": {
            "projects": 1,
            "files": 1003,
            "file_bytes": sum(file.size_bytes for file in seal.source_view.files),
        },
        "safe": {"projects": 1, "files": 1003},
        "proof_only": {"failed_files": 0, "excluded_files": 0},
        "records": {
            "proof_discovered": 3004,
            "published": 3004,
            "proof_only": 0,
            "accounted": 3004,
        },
        "published_entities": {"modules": 1000, "components": 0, "total": 1000},
    }
    return seal, assets, request, policy, wire, _independent_bytes(expected) + b"\n"


def large_selected_stdout_candidates_v3(
    tmp_path: Path,
    delta: int,
) -> tuple[RetainedRequestBoundPublicationCandidatesV3, bytes]:
    assert delta in {0, 1}
    target_bytes = 16_777_216 + delta
    *_initial, expected = _large_inputs_v3(tmp_path / "calibration", prefix_length=3800)
    path_delta, context_delta = divmod(target_bytes - len(expected), 4)
    prefix_delta, longer_names = divmod(path_delta, 1000)
    seal, assets, request, policy, wire, expected = _large_inputs_v3(
        tmp_path / "final",
        prefix_length=3800 + prefix_delta,
        longer_names=longer_names,
        context_digits=2 + context_delta,
    )
    assert len(expected) == target_bytes
    assert len(_independent_bytes(wire)) <= request.record()["limits"]["max_adapter_response_bytes"]
    runtime = runtime_for_core_wire(seal, assets, request, policy, wire)
    candidate = runtime.transport_candidate()
    assert candidate is not None
    core = decide_semantic_candidate_v3(candidate, seal, assets)
    assert core.gate()["payload_available"] is True and core.gate()["actual"] == 1000
    run = retain_request_bound_run_decision_v3(runtime, semantic_decision=core)
    return retain_request_bound_publication_candidates_v3(run), expected


def source_failure_candidates_v3(
    tmp_path: Path, kind: str, *, isolated: bool = False, selector: str | None = None
) -> RetainedRequestBoundPublicationCandidatesV3:
    sources = (
        SOURCE_BYTES
        if isolated
        else {
            **SOURCE_BYTES,
            "src/value.ts": SOURCE_BYTES["src/value.ts"] + b"require(variable);\n",
        }
    )
    seal, assets, request, policy, wire = core_inputs_v3(
        tmp_path, sources=sources, stdout_selector=selector
    )
    exclude_value_module_with_root_v3(wire, request, kind)
    runtime = runtime_for_core_wire(seal, assets, request, policy, wire)
    candidate = runtime.transport_candidate()
    assert candidate is not None
    core = decide_semantic_candidate_v3(candidate, seal, assets)
    if isolated:
        assert core.gate()["outcome"] == "partial_safe"
    else:
        assert core.gate()["diagnostic_code"] == "CSV-NEXT-SOURCE-003"
    run = retain_request_bound_run_decision_v3(runtime, semantic_decision=core)
    return retain_request_bound_publication_candidates_v3(run)


def target_failure_candidates_v3(
    tmp_path: Path, *, selector: str | None = None
) -> RetainedRequestBoundPublicationCandidatesV3:
    seal, assets, request, policy, wire = core_inputs_v3(
        tmp_path, targets=["path:src/button.tsx"], stdout_selector=selector
    )
    omit_selected_button_module_v3(wire)
    runtime = runtime_for_core_wire(seal, assets, request, policy, wire)
    candidate = runtime.transport_candidate()
    assert candidate is not None
    core = decide_semantic_candidate_v3(candidate, seal, assets)
    assert core.gate()["diagnostic_code"] == "CSV-NEXT-TARGET-001"
    run = retain_request_bound_run_decision_v3(runtime, semantic_decision=core)
    return retain_request_bound_publication_candidates_v3(run)


def export_failure_candidates_v3(
    tmp_path: Path, *, selector: str | None = None
) -> RetainedRequestBoundPublicationCandidatesV3:
    sources = {
        **SOURCE_BYTES,
        "src/value.ts": b'const value = makeValue();\nexport { value as "opaque-public-name" };\n',
    }
    seal, assets, request, policy, wire = core_inputs_v3(
        tmp_path, sources=sources, stdout_selector=selector
    )
    unknown_value_export_v3(wire)
    runtime = runtime_for_core_wire(seal, assets, request, policy, wire)
    candidate = runtime.transport_candidate()
    assert candidate is not None
    core = decide_semantic_candidate_v3(candidate, seal, assets)
    assert core.gate()["diagnostic_code"] == "CSV-NEXT-EXPORT-001"
    run = retain_request_bound_run_decision_v3(runtime, semantic_decision=core)
    return retain_request_bound_publication_candidates_v3(run)


def entity_budget_candidates_v3(
    tmp_path: Path, *, selector: str | None = None
) -> RetainedRequestBoundPublicationCandidatesV3:
    seal, assets, request, policy, wire = core_inputs_v3(
        tmp_path, max_entities=3, stdout_selector=selector
    )
    runtime = runtime_for_core_wire(seal, assets, request, policy, wire)
    candidate = runtime.transport_candidate()
    assert candidate is not None
    core = decide_semantic_candidate_v3(candidate, seal, assets)
    assert core.gate()["actual"] == 4 and core.gate()["diagnostic_code"] == "CSV-NEXT-LIMIT-005"
    run = retain_request_bound_run_decision_v3(runtime, semantic_decision=core)
    return retain_request_bound_publication_candidates_v3(run)


def complete_candidates_v3(
    tmp_path: Path, *, selector: str | None = "next:semantic-json"
) -> RetainedRequestBoundPublicationCandidatesV3:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path, stdout_selector=selector)
    runtime = runtime_for_core_wire(seal, assets, request, policy, wire)
    candidate = runtime.transport_candidate()
    assert candidate is not None
    core = decide_semantic_candidate_v3(candidate, seal, assets)
    assert core.gate()["outcome"] == "complete"
    run = retain_request_bound_run_decision_v3(runtime, semantic_decision=core)
    return retain_request_bound_publication_candidates_v3(run)


def rejected_candidates_v3(
    tmp_path: Path, *, selector: str | None = None
) -> RetainedRequestBoundPublicationCandidatesV3:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path, stdout_selector=selector)
    wire["semantic_payload"]["model_digest"] = "0" * 64
    runtime = runtime_for_core_wire(seal, assets, request, policy, wire)
    candidate = runtime.transport_candidate()
    assert candidate is not None
    core = inspect_semantic_candidate_v3(candidate, seal, assets)
    assert type(core) is RejectedSemanticDecisionV3
    run = retain_request_bound_run_decision_v3(runtime, semantic_decision=core)
    return retain_request_bound_publication_candidates_v3(run)
