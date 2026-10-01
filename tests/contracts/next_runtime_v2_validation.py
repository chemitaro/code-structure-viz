"""Small data-only A-runtime validators, independent of the historical v1 lane."""

from __future__ import annotations

import base64
import hashlib
import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from jsonschema import Draft202012Validator, ValidationError  # type: ignore[import-untyped]
from referencing import Registry, Resource

from tests.contracts.next_reference_validation import (
    COLLECTIONS,
    ModelRecordLimitError,
    _is_program_file,
    _record_references,
    _target_duplicate_module_exceptions,
    _target_missing_module_exceptions,
    _validate_project_correspondence,
    _validate_response_base,
    _validate_target_exception_proof_base,
    bounded_decode_json,
    canonical_json_bytes,
    canonical_run_context,
    derive_pre_budget_outcome,
    digest,
    entity_budget_gate,
    export_failure_decision,
    response_model_record_counts,
    target_completeness_failure,
    target_failure_decision,
    target_failure_from_proof,
    validate_model,
    validate_proof,
    validate_request_files,
)
from tests.contracts.next_semantic_profile_v1_reference import semantic_compatibility_metadata_v2
from tests.contracts.next_trusted_profile_v1_reference import (
    PROFILE_DECLARATIONS,
    TRUSTED_PACKAGE_PREFIX,
    TRUSTED_VIRTUAL_PREFIX,
    trusted_profile_metadata_v1,
)

if TYPE_CHECKING:
    from code_structure_viz.adapters.next.source_acquisition import SourceAcquisitionSeal
    from tests.contracts.next_runtime_v2_reference import (
        RejectedResponseFrameV2,
        RetainedExecutionAssets,
        RetainedRequestFrameV2,
        RetainedResponseFrameV2,
        RetainedRuntimeResultV2,
        ValidatedSemanticDecisionV2,
        ValidatedTransportCandidateV2,
    )

ROOT = Path(__file__).resolve().parents[2]


def _validate_schema(name: str, value: object, fragment: str = "") -> None:
    registry = Registry()
    for path in (ROOT / "schemas").glob("*.schema.json"):
        schema = json.loads(path.read_text(encoding="utf-8"))
        identifier = schema.get("$id")
        if isinstance(identifier, str):
            registry = registry.with_resource(identifier, Resource.from_contents(schema))
    target = cast(
        dict[str, Any],
        json.loads((ROOT / "schemas" / f"{name}.schema.json").read_text(encoding="utf-8")),
    )
    if fragment:
        target = {"$ref": target["$id"] + fragment}
    Draft202012Validator(target, registry=registry).validate(value)


def validate_execution_asset_identity_v1(value: dict[str, Any]) -> None:
    """Validate portable identity; this does not certify installed member bytes."""

    _validate_schema("next-execution-assets-v1", value)
    paths = [member["package_path"] for member in value["members"]]
    if len(paths) != len(set(paths)):
        raise ValueError("execution asset members have duplicate package paths")
    if paths != sorted(paths, key=lambda path: path.encode("utf-8")):
        raise ValueError("execution asset members are not in UTF-8 package-path order")
    if not any(
        member["package_path"] == value["entrypoint_member"] and member["role"] == "adapter"
        for member in value["members"]
    ):
        raise ValueError("execution asset entrypoint is missing or not an adapter")
    preimage = json.dumps(
        {key: item for key, item in value.items() if key != "asset_set_id"},
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    if value["asset_set_id"] != hashlib.sha256(preimage).hexdigest():
        raise ValueError("asset_set_id differs from the portable content preimage")


def validate_execution_assets_v1(value: dict[str, Any], owner: RetainedExecutionAssets) -> None:
    """Admit a portable identity only when its retained byte owner also agrees."""

    validate_execution_asset_identity_v1(value)
    if value != owner.descriptor():
        raise ValueError("execution asset metadata differs from its retained bytes")


def validate_trusted_environment_manifest_shape_v2(value: dict[str, Any]) -> None:
    """Closed manifest shape only, not profile, hash or retained-byte admission."""

    _validate_schema("next-trusted-type-environment-v2", value)


def validate_request_shape_v2(value: dict[str, Any]) -> None:
    """Closed generated request shape, without source/byte-owner admission."""

    _validate_schema("next-adapter-request-v2", value)


def validate_provenance_shape_v2(value: dict[str, Any]) -> None:
    """Closed public shape only; actual observation values require retained owners."""

    _validate_schema("next-provenance-v2", value)


def validate_runtime_provenance_v2(
    value: dict[str, Any],
    result: RetainedRuntimeResultV2,
    *,
    semantic_decision: ValidatedSemanticDecisionV2 | None = None,
) -> None:
    """Recalculate each digest from the actual immutable owner, not the public row."""

    from tests.contracts.next_runtime_v2_reference import runtime_provenance_values_v2

    validate_provenance_shape_v2(value)
    actual_values = runtime_provenance_values_v2(result, semantic_decision)
    expected: tuple[str, str | None, str | None]
    if result.result_kind == "success" and semantic_decision is not None:
        gate = semantic_decision.gate()
        if gate["outcome"] == "payload_unavailable":
            stage = {
                "CSV-NEXT-TARGET-001": "target_resolution",
                "CSV-NEXT-EXPORT-001": "response_validation",
                "CSV-NEXT-LIMIT-005": "model_validation",
            }[gate["diagnostic_code"]]
            expected = "request_bound_failure", stage, gate["diagnostic_code"]
        else:
            expected = "request_bound_success", None, None
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
        if actual is not None and row["value"]["sha256"] != digest(
            {
                "schema": "code-structure-viz.next-observation/v2",
                "version": 2,
                "field": field_name,
                "value": actual,
            }
        ):
            raise ValueError("provenance observation digest differs from its retained owner")


def validate_request_json_limits_v2(value: object, limits: dict[str, int]) -> None:
    """Generated JSON bounds; response aggregate-array limits do not apply."""

    _validate_schema("next-limits-v1", limits)
    pending = [(value, 1)]
    while pending:
        current, depth = pending.pop()
        if depth > limits["max_json_nesting"]:
            raise ValueError("request exceeds max_json_nesting before encoding")
        if (
            isinstance(current, str)
            and len(current.encode("utf-8")) > limits["max_json_string_bytes"]
        ):
            raise ValueError("request exceeds max_json_string_bytes before encoding")
        if isinstance(current, dict):
            if any(not isinstance(key, str) for key in current):
                raise ValueError("request JSON object keys must be strings")
            if any(len(key.encode("utf-8")) > limits["max_json_string_bytes"] for key in current):
                raise ValueError("request exceeds max_json_string_bytes before encoding")
            pending.extend((item, depth + 1) for item in current.values())
        elif isinstance(current, list):
            if len(current) > limits["max_array_items"]:
                raise ValueError("request exceeds max_array_items before encoding")
            pending.extend((item, depth + 1) for item in current)


def validate_request_stdin_bytes_v2(raw: bytes, limits: dict[str, int]) -> None:
    """Actual encoded byte cap only, not JSON shape or source admission."""

    if not isinstance(raw, bytes):
        raise TypeError("request input must be immutable bytes")
    _validate_schema("next-limits-v1", limits)
    if len(raw) > limits["max_encoded_stdin_bytes"]:
        raise ValueError("request exceeds max_encoded_stdin_bytes before send")


def validate_request_record_v2(value: dict[str, Any]) -> None:
    """Validate generated request data; the retained-source join is separate."""

    validate_request_json_limits_v2(value, value.get("limits", {}))
    validate_request_shape_v2(value)
    if value["request_id"] != digest(
        {key: item for key, item in value.items() if key != "request_id"}
    ):
        raise ValueError("request_id differs from the new request preimage")
    if value["run_context"]["budget_resolved"] != value["limits"]["max_entities"]:
        raise ValueError("request context budget differs from its source-sealed limits")
    try:
        canonical_run_context(**value["run_context"])
        validate_request_files(value)
    except AssertionError as error:
        raise ValueError("request violates its source/entity or context contract") from error


def validate_request_source_binding_v2(
    value: dict[str, Any], seal: SourceAcquisitionSeal, owner: RetainedExecutionAssets
) -> None:
    """Independent data joins; never regenerate expected bytes with the builder."""

    from tests.contracts.next_runtime_v2_reference import trusted_environment_manifest_v2

    validate_source_seal_trusted_v2(seal, owner)
    validate_request_record_v2(value)
    if value["adapter_version"] != owner.adapter_identity()["version"] or (
        value["trusted_type_environment"]
        != trusted_environment_manifest_v2(owner)["environment_descriptor"]
    ):
        raise ValueError("request differs from its retained adapter/trusted identity")
    plan = seal.final_plan
    if value["limits"] != plan["limits"]:
        raise ValueError("request limits differ from their source seal")
    applicable = set(seal.package_applicability.applicable_projects)
    projects = {row["root"]: row for row in value["projects"]}
    expected_projects = {row["root"]: row for row in plan["projects"] if row["root"] in applicable}
    if set(projects) != set(expected_projects) or any(
        row[key] != expected_projects[root][key]
        for root, row in projects.items()
        for key in ("root", "source_roots", "config_path", "compiler_options")
    ):
        raise ValueError("request projects differ from their source seal")
    source = {item.path.as_posix(): item for item in seal.source_view.files}
    roles = {row["path"]: row for row in plan["file_role_map"] if row["project_root"] in applicable}
    files = {row["path"]: row for row in value["files"]}
    if set(files) != set(roles):
        raise ValueError("request file membership differs from its source seal")
    for path, row in files.items():
        role = roles[path]
        observed = source[path]
        if (
            row["project_id"] != projects[role["project_root"]]["id"]
            or row["roles"] != role["roles"]
            or row["effective_role"] != role["effective_role"]
            or row["size_bytes"] != observed.size_bytes
            or row["sha256"] != observed.sha256
            or base64.b64decode(row["content_base64"], validate=True) != observed.content
        ):
            raise ValueError("request file roles/bytes differ from their source seal")


def validate_request_frame_v2(
    frame: RetainedRequestFrameV2, seal: SourceAcquisitionSeal, owner: RetainedExecutionAssets
) -> None:
    """Admit immutable generated request bytes only at their actual owner join."""

    from tests.contracts.next_runtime_v2_reference import RetainedRequestFrameV2

    if type(frame) is not RetainedRequestFrameV2:
        raise TypeError("request validation requires a retained request frame owner")
    validate_source_seal_trusted_v2(seal, owner)
    if frame.source_seal_id != seal.seal_id:
        raise ValueError("request source seal identity differs from its actual owner")
    if frame.execution_asset_set_id != owner.descriptor()["asset_set_id"]:
        raise ValueError("request execution asset identity differs from its retained owner")
    validate_request_stdin_bytes_v2(frame.canonical_bytes, seal.final_plan["limits"])
    value = frame.record()
    validate_request_source_binding_v2(value, seal, owner)
    if (
        value["request_id"] != frame.request_id
        or canonical_json_bytes(value) != frame.canonical_bytes
    ):
        raise ValueError("request canonical bytes/id differ from their retained frame")


def validate_trusted_environment_manifest_v2(
    value: dict[str, Any], owner: RetainedExecutionAssets
) -> None:
    """Join reference profile metadata to the one retained declaration owner."""

    from tests.contracts.next_runtime_v2_reference import RetainedExecutionAssets

    if type(owner) is not RetainedExecutionAssets:
        raise TypeError("trusted metadata requires a retained execution asset owner")
    validate_trusted_environment_manifest_shape_v2(value)
    if any(value[key] != item for key, item in trusted_profile_metadata_v1().items()):
        raise ValueError("manifest differs from the locked trusted metadata")
    descriptor = owner.descriptor()
    validate_execution_assets_v1(descriptor, owner)
    members = {member["package_path"]: member for member in descriptor["members"]}
    expected_files = [
        {
            "package_path": TRUSTED_PACKAGE_PREFIX + name,
            "virtual_path": TRUSTED_VIRTUAL_PREFIX + name,
            "size_bytes": size,
            "sha256": sha,
            "license_id": license_id,
        }
        for name, size, sha, license_id in PROFILE_DECLARATIONS
    ]
    if value["files"] != expected_files:
        raise ValueError("manifest differs from the locked trusted declaration profile")
    if {path for path, row in members.items() if row["role"] == "trusted_declaration"} != {
        row["package_path"] for row in expected_files
    }:
        raise ValueError("retained assets differ from the locked declaration role set")
    if any(
        members[row["package_path"]]["size_bytes"] != row["size_bytes"]
        or members[row["package_path"]]["sha256"] != row["sha256"]
        for row in expected_files
    ):
        raise ValueError("manifest differs from its retained declaration bytes")
    semantic_preimage = {
        **{key: item for key, item in value["environment_descriptor"].items() if key != "sha256"},
        **{
            key: item
            for key, item in value.items()
            if key not in {"schema", "environment_descriptor", "files", "manifest_sha256"}
        },
        "files": [
            {key: item for key, item in row.items() if key != "package_path"}
            for row in value["files"]
        ],
    }
    encoded = json.dumps(
        semantic_preimage,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    if value["environment_descriptor"]["sha256"] != hashlib.sha256(encoded).hexdigest():
        raise ValueError("trusted environment digest differs from its logical profile preimage")
    encoded = json.dumps(
        {key: item for key, item in value.items() if key != "manifest_sha256"},
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    if value["manifest_sha256"] != hashlib.sha256(encoded).hexdigest():
        raise ValueError("trusted manifest digest differs from its package mapping preimage")


def validate_process_launch_policy_v2(value: dict[str, Any]) -> None:
    """Validate the closed prelaunch policy and its candidate/argv join."""

    _validate_schema("next-process-launch-policy-v2", value)
    if value["argv"][0] != value["node_candidate"]["absolute_path"]:
        raise ValueError("argv executable differs from the measured candidate")
    root = value["private_root"]
    if (
        value["runtime_directory"] != f"{root}/runtime"
        or value["cwd"] != f"{root}/cwd"
        or value["argv"][2] != f"{root}/runtime/next-adapter.mjs"
    ):
        raise ValueError("private layout does not match the owned runtime/cwd/entrypoint")


def validate_launch_policy_assets_v2(value: dict[str, Any], owner: RetainedExecutionAssets) -> None:
    """Validate a policy against the byte owner, not separately supplied metadata."""

    validate_process_launch_policy_v2(value)
    descriptor = owner.descriptor()
    validate_execution_assets_v1(descriptor, owner)
    if value["execution_asset_set_id"] != descriptor["asset_set_id"]:
        raise ValueError("policy execution asset identity differs from its retained owner")
    if value["adapter"] != owner.adapter_identity():
        raise ValueError("policy adapter identity differs from its retained entrypoint")


def validate_launch_policy_trusted_v2(
    value: dict[str, Any], owner: RetainedExecutionAssets
) -> None:
    """Add the retained declaration-profile join, not real compiler admission."""

    from tests.contracts.next_runtime_v2_reference import trusted_environment_manifest_v2

    manifest = trusted_environment_manifest_v2(owner)
    validate_launch_policy_assets_v2(value, owner)
    if value["trusted_environment_digest"] != manifest["environment_descriptor"]["sha256"]:
        raise ValueError("policy differs from its retained trusted environment")


def validate_launch_policy_request_v2(
    policy: dict[str, Any],
    request: RetainedRequestFrameV2,
    seal: SourceAcquisitionSeal,
    owner: RetainedExecutionAssets,
) -> None:
    """Join policy to the actual generated request and retained byte owners."""

    validate_request_frame_v2(request, seal, owner)
    validate_launch_policy_trusted_v2(policy, owner)
    if policy["request_id"] != request.request_id:
        raise ValueError("policy differs from its source-owned request identity")
    record = request.record()
    if policy["limits"] != record["limits"]:
        raise ValueError("policy differs from its source-owned request limits")
    if policy["runtime_requirement"] != record["runtime_requirement"]:
        raise ValueError("policy differs from its source-owned runtime requirement")


def validate_observation_request_v2(
    observation: dict[str, Any],
    policy: dict[str, Any],
    request: RetainedRequestFrameV2,
    seal: SourceAcquisitionSeal,
    owner: RetainedExecutionAssets,
) -> None:
    """Join all observed phases to prepared stdin; not real capture evidence."""

    validate_launch_policy_request_v2(policy, request, seal, owner)
    validate_process_observation_v2(observation, policy)
    if observation["capture"] is not None and (
        observation["capture"]["stdin_bytes"] != len(request.canonical_bytes)
    ):
        raise ValueError("observed stdin size differs from its prepared request bytes")


def validate_source_seal_trusted_v2(
    seal: SourceAcquisitionSeal, owner: RetainedExecutionAssets
) -> None:
    """Join unchanged source-seal identity to read-only retained profile metadata."""

    from code_structure_viz.adapters.next.source_acquisition import SourceAcquisitionSeal
    from tests.contracts.next_runtime_v2_reference import trusted_environment_manifest_v2

    if type(seal) is not SourceAcquisitionSeal:
        raise TypeError("trusted profile joins require an actual SourceAcquisitionSeal")
    seal.__post_init__()
    plan = seal.final_plan
    _validate_schema("next-source-plan-v1", plan)
    manifest = trusted_environment_manifest_v2(owner)
    if plan["trusted_environment_digest"] != manifest["environment_descriptor"]["sha256"]:
        raise ValueError("source seal differs from its retained trusted environment")


def validate_runtime_binding_identity_v1(value: dict[str, Any]) -> None:
    """Validate portable binding identity, not same-process execution evidence."""

    _validate_schema("next-runtime-binding-v1", value)
    preimage = {
        key: value[key]
        for key in (
            "runtime_binding_profile_id",
            "node_candidate",
            "node_observation",
            "execution_asset_set_id",
            "typescript_identity",
            "trusted_type_environment_digest",
        )
    }
    preimage["adapter"] = {key: value["adapter"][key] for key in ("protocol", "version", "sha256")}
    encoded = json.dumps(
        preimage, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    if value["runtime_toolchain_fingerprint"] != hashlib.sha256(encoded).hexdigest():
        raise ValueError("runtime binding fingerprint differs from its portable preimage")


def validate_runtime_binding_observation_v1(
    value: dict[str, Any],
    policy: dict[str, Any],
    owner: RetainedExecutionAssets,
    observation: dict[str, Any],
) -> None:
    """Join data records; this still requires the separate raw-frame validation gate."""

    validate_runtime_binding_identity_v1(value)
    validate_launch_policy_assets_v2(policy, owner)
    validate_process_observation_v2(observation, policy)
    if not observation["transport_payload_admissible"]:
        raise ValueError("runtime binding requires a successful transport observation")
    runtime = observation["response"]["control"]["runtime"]
    if value["node_observation"] != {
        "version": runtime["version"],
        "source": runtime["observation_source"],
    }:
        raise ValueError("runtime binding differs from its joined node observation")
    expected = {
        "node_candidate": {"sha256": policy["node_candidate"]["sha256"]},
        "execution_asset_set_id": owner.descriptor()["asset_set_id"],
        "adapter": owner.adapter_identity(),
        "typescript_identity": policy["typescript_identity"],
        "trusted_type_environment_digest": policy["trusted_environment_digest"],
    }
    if any(value[key] != item for key, item in expected.items()):
        raise ValueError("runtime binding owner identity differs from its retained/measured input")


def validate_process_observation_v2(value: dict[str, Any], policy: dict[str, Any]) -> None:
    """Validate a data-only post-launch record; raw-frame joins are a separate gate."""

    validate_process_launch_policy_v2(policy)
    _validate_schema("next-process-launch-observation-v2", value)
    encoded_policy = json.dumps(
        policy, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    if value["policy_digest"] != hashlib.sha256(encoded_policy).hexdigest() or any(
        value[key] != policy[key] for key in ("producer", "platform", "request_id")
    ):
        raise ValueError("observed owner identity does not match its policy binding")
    if value["spawn"] is not None and any(
        observed != policy[name] for name, observed in value["spawn"]["parameters"].items()
    ):
        raise ValueError("observed spawn parameters differ from their sealed policy")
    if value["spawn"] is not None and value["spawn"]["pid"] != value["spawn"]["pgid"]:
        raise ValueError("observed process group is not the new session leader group")
    if value["terminal_cause"] in {"stage_failed", "spawn_failed"} and value["spawn"] is not None:
        raise ValueError("pre-spawn failure cannot include a successful spawn observation")
    if value["terminal_cause"] in {
        "write_failed",
        "read_failed",
        "stdout_limit",
        "stderr_limit",
        "timeout",
        "frame_invalid",
        "response_invalid",
        "binding_mismatch",
        "exit_mismatch",
    } and (value["spawn"] is None or value["capture"] is None):
        raise ValueError("post-spawn failure requires actual spawn and capture observations")
    if value["spawn"] is None and any(
        value[key] is not None for key in ("capture", "exit_code", "response")
    ):
        raise ValueError("capture, exit and control observations require an actual spawn")
    if value["spawn"] is None and value["cleanup"]["direct_child_waited"]:
        raise ValueError("unspawned observation cannot claim that a child was waited")
    if value["spawn"] is None and (
        value["cleanup"]["group_stop"] != "not_required" or value["cleanup"]["signals"]
    ):
        raise ValueError("unspawned observation cannot claim a process group cleanup")
    if value["spawn"] is not None and value["cleanup"]["direct_child_waited"] is not (
        value["exit_code"] is not None
    ):
        raise ValueError("direct child wait must agree with an observed exit status")
    if value["capture"] is not None:
        capture = value["capture"]
        if any(
            capture[actual] > capture[total]
            for actual, total in (
                ("stdin_sent_bytes", "stdin_bytes"),
                ("stdout_retained_bytes", "stdout_bytes"),
                ("stderr_retained_bytes", "stderr_bytes"),
            )
        ):
            raise ValueError("capture counters claim more bytes than were observed or encoded")
    if value["terminal_cause"] in {"stdout_limit", "stderr_limit"}:
        stream = value["terminal_cause"].removesuffix("_limit")
        if (
            value["capture"] is None
            or value["capture"][f"{stream}_bytes"]
            != policy["limits"][f"max_adapter_{stream}_capture_bytes"] + 1
        ):
            raise ValueError("capture limit cause requires its actual cap measurement plus one")
    if value["terminal_cause"] == "none" and value["response"] is None:
        raise ValueError("normal terminal cause requires a validated control response")
    if value["response"] is not None:
        capture = value["capture"]
        if (
            capture is None
            or not capture["stdout_eof"]
            or not 0
            < capture["stdout_bytes"]
            <= policy["limits"]["max_adapter_stdout_capture_bytes"]
        ):
            raise ValueError("control observation requires complete stdout within its capture cap")
        validate_response_control_v2(value["response"]["control"])
        if value["response"]["control"]["adapter_version"] != policy["adapter"]["version"]:
            raise ValueError("control adapter version differs from its retained policy identity")
        binding = value["response"]["control"]["binding"]
        if (
            value["terminal_cause"] == "none"
            and binding["state"] == "bound"
            and binding["request_id"] != policy["request_id"]
        ):
            raise ValueError("normal control response has an unrelated request binding")
    if value["terminal_cause"] == "exit_mismatch" and (
        value["response"] is None or value["exit_code"] is None
    ):
        raise ValueError("exit mismatch requires an observed control and actual exit")
    if value["terminal_cause"] in {"none", "exit_mismatch"} and value["response"] is not None:
        expected_exit = {
            "success": 0,
            "protocol_failure": 65,
            "unsupported_runtime": 66,
            "bootstrap_failure": 67,
            "semantic_failure": 68,
        }[value["response"]["control"]["result_kind"]]
        if value["terminal_cause"] == "exit_mismatch" and value["exit_code"] == expected_exit:
            raise ValueError("exit mismatch requires an actual control/exit disagreement")
        if value["terminal_cause"] == "none" and value["exit_code"] != expected_exit:
            raise ValueError("normal control response and child exit code disagree")
    if value["terminal_cause"] == "none" and not _cleanup_is_verified(value["cleanup"]):
        raise ValueError("normal terminal cause cannot hide unverified cleanup")
    if value["terminal_cause"] == "cleanup_unverified" and not (
        value["cleanup"]["group_stop"] == "unverified"
        or (value["spawn"] is not None and not value["cleanup"]["direct_child_waited"])
        or any(
            not value["cleanup"][key]
            for key in ("pipes_closed", "candidate_closed", "private_root_removed")
        )
    ):
        raise ValueError("cleanup cause requires an actually unverified cleanup condition")
    if value["terminal_cause"] == "none" and (
        value["cleanup"]["group_stop"] != "not_required" or value["cleanup"]["signals"]
    ):
        raise ValueError("normal exit does not terminate the first-party process group")
    if value["terminal_cause"] == "none" and not _capture_is_complete(value["capture"]):
        raise ValueError("normal terminal cause cannot hide incomplete capture")
    if value["terminal_cause"] == "none" and any(
        value[key] != "unchanged" for key in ("candidate_check", "assets_check")
    ):
        raise ValueError("normal terminal cause cannot omit successful observable drift checks")
    if value["terminal_cause"] in {"candidate_drift", "assets_drift"}:
        subject = value["terminal_cause"].removesuffix("_drift")
        if value[f"{subject}_check"] != "drift":
            raise ValueError("drift cause requires the corresponding observable drift result")
    if (
        value["terminal_cause"] != "none"
        and value["capture"] is not None
        and any(
            value["capture"][key] != 0 for key in ("stdout_retained_bytes", "stderr_retained_bytes")
        )
    ):
        raise ValueError("terminal transport failure must discard raw buffers")
    if value["transport_payload_admissible"] is not process_payload_gate_v2(value):
        raise ValueError("observed payload gate differs from the closed process conditions")


def process_payload_gate_v2(value: dict[str, Any]) -> bool:
    """Compute the data-only transport gate; not a raw-frame or semantic validator."""

    _validate_schema("next-process-launch-observation-v2", value)
    return bool(
        value["terminal_cause"] == "none"
        and value["spawn"] is not None
        and value["response"] is not None
        and value["response"]["control"]["result_kind"] == "success"
        and value["exit_code"] == 0
        and value["response"]["control"]["binding"]["state"] == "bound"
        and value["response"]["control"]["binding"]["request_id"] == value["request_id"]
        and value["response"]["control"]["runtime"] is not None
        and value["response"]["control"]["runtime"]["eligibility"] == "supported"
        and _cleanup_is_verified(value["cleanup"])
        and value["cleanup"]["group_stop"] == "not_required"
        and not value["cleanup"]["signals"]
        and _capture_is_complete(value["capture"])
        and value["candidate_check"] == "unchanged"
        and value["assets_check"] == "unchanged"
    )


def validate_response_control_v2(value: dict[str, Any]) -> None:
    """Validate the closed child control projection, not a complete wire frame."""

    _validate_schema("next-process-launch-observation-v2", value, "#/$defs/response_control")
    runtime = value["runtime"]
    if runtime is not None:
        raw = runtime["version_raw"]
        canonical = (
            raw
            if re.fullmatch(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)", raw)
            else None
        )
        if runtime["version"] != canonical:
            raise ValueError("runtime version does not match its exact raw observation")
        eligibility = (
            "invalid"
            if canonical is None
            else ("supported" if int(canonical.split(".", 1)[0]) >= 22 else "unsupported")
        )
        if runtime["eligibility"] != eligibility:
            raise ValueError("runtime eligibility differs from the stable-major-22 requirement")
    if value["result_kind"] in {"success", "semantic_failure"} and (
        value["binding"]["state"] != "bound"
        or runtime is None
        or runtime["eligibility"] != "supported"
    ):
        raise ValueError(f"{value['result_kind']} control requires a bound supported runtime")
    if value["result_kind"] == "protocol_failure" and value["binding"]["state"] != "unbound":
        raise ValueError("protocol_failure control must not echo an unvalidated request ID")
    if value["result_kind"] == "unsupported_runtime" and (
        value["binding"]["state"] != "bound"
        or runtime is None
        or runtime["eligibility"] not in {"invalid", "unsupported"}
    ):
        raise ValueError("unsupported_runtime control requires a bound ineligible runtime")


def validate_response_frame_shape_v2(value: dict[str, Any]) -> None:
    """Validate closed frame shape/control, not semantic proof or request-owner joins."""

    _validate_schema("next-adapter-response-v2", value)
    validate_response_control_v2(value["control"])


def validate_response_frame_bytes_v2(raw: bytes, limits: dict[str, int]) -> None:
    """Use the unchanged wire-agnostic bounded JSON grammar, never v1 runtime admission."""

    if not isinstance(raw, bytes):
        raise TypeError("response frame input must already be immutable bytes")
    _validate_schema("next-limits-v1", limits)
    decoded = bounded_decode_json(raw, limits=limits)
    if not decoded["allowed"]:
        raise ValueError(f"response frame rejected: {decoded['reason']}")
    validate_response_frame_shape_v2(decoded["value"])


def response_rejection_v2(raw: bytes, limits: dict[str, int]) -> dict[str, Any] | None:
    """Classify bounded bytes; a caller-supplied result dict is not an owner."""

    if not isinstance(raw, bytes):
        raise TypeError("response frame input must already be immutable bytes")
    _validate_schema("next-limits-v1", limits)
    decoded = bounded_decode_json(raw, limits=limits)
    stage, reason = "response_decode", decoded.get("reason")
    if decoded["allowed"]:
        try:
            validate_response_frame_shape_v2(decoded["value"])
        except (ValidationError, ValueError):
            stage, reason = "response_schema", "closed_response_shape"
        else:
            return None
    code = "CSV-NEXT-PROTOCOL-001"
    if reason == "max_adapter_response_bytes":
        stage, code = "response_raw_bytes", "CSV-NEXT-LIMIT-003"
    elif reason in {
        "max_json_nesting",
        "max_array_items",
        "max_total_array_items",
        "max_json_string_bytes",
    }:
        code = "CSV-NEXT-LIMIT-003"
    return {
        "stage": stage,
        "diagnostic_code": code,
        "reason": reason,
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "byte_length": len(raw),
        "measurement": {
            key: decoded[key]
            for key in (
                "bytes",
                "total_array_items",
                "array_count",
                "max_array_items",
                "max_nesting",
                "max_string_bytes",
                "failed_at_byte",
                "materialized",
            )
        },
    }


def validate_rejected_frame_observation_v2(
    observation: dict[str, Any], policy: dict[str, Any], rejected: RejectedResponseFrameV2 | None
) -> None:
    """Join decoder-owned rejected byte measurement to the same complete capture."""

    from tests.contracts.next_runtime_v2_reference import RejectedResponseFrameV2

    if type(rejected) is not RejectedResponseFrameV2:
        raise TypeError("frame-invalid result requires the rejected byte owner")
    assert rejected is not None
    validate_process_observation_v2(observation, policy)
    failure, capture = rejected.failure(), observation["capture"]
    if rejected.limits() != policy["limits"]:
        raise ValueError("rejected frame limits differ from the retained request policy")
    if (
        observation["terminal_cause"] != "frame_invalid"
        or observation["response"] is not None
        or capture is None
        or not capture["stdout_eof"]
        or capture["stdout_bytes"] != failure["byte_length"]
        or capture["stdout_bytes"] > policy["limits"]["max_adapter_stdout_capture_bytes"]
    ):
        raise ValueError("rejected frame is not joined to its complete captured bytes")


def validate_response_frame_observation_v2(
    value: dict[str, Any], policy: dict[str, Any], frame: RetainedResponseFrameV2
) -> None:
    """Join a raw frame to its observation; request/proof/OS joins are separate."""

    from tests.contracts.next_runtime_v2_reference import RetainedResponseFrameV2

    if type(frame) is not RetainedResponseFrameV2:
        raise TypeError("response observation join requires the retained frame owner")
    validate_process_observation_v2(value, policy)
    validate_response_frame_bytes_v2(frame.raw_bytes, policy["limits"])
    if (
        value["response"] is None
        or value["response"]["sha256"] != frame.sha256
        or value["response"]["control"] != frame.control()
        or value["capture"]["stdout_bytes"] != len(frame.raw_bytes)
    ):
        raise ValueError("observation is not joined to its retained response bytes")


def validate_response_request_v2(
    response: RetainedResponseFrameV2,
    request: RetainedRequestFrameV2,
    seal: SourceAcquisitionSeal,
    owner: RetainedExecutionAssets,
) -> None:
    """Request/response echoes only; independent Core model/proof checks remain."""

    from tests.contracts.next_runtime_v2_reference import RetainedResponseFrameV2

    if type(response) is not RetainedResponseFrameV2:
        raise TypeError("response request join requires a retained frame owner")
    validate_request_frame_v2(request, seal, owner)
    record = request.record()
    validate_response_frame_bytes_v2(response.raw_bytes, record["limits"])
    control = response.control()
    if control["adapter_version"] != record["adapter_version"]:
        raise ValueError("response adapter version differs from its retained request identity")
    binding = control["binding"]
    if binding["state"] == "bound" and binding["request_id"] != request.request_id:
        raise ValueError("response request binding differs from its prepared frame")
    payload = response.semantic_payload()
    if payload is not None:
        expected = {
            "trusted_type_environment_digest": record["trusted_type_environment"]["sha256"],
            "limits": record["limits"],
            "run_context": record["run_context"],
        }
        if any(payload[key] != value for key, value in expected.items()):
            raise ValueError("response semantic echo differs from its source-owned request")


def validate_transport_exchange_v2(
    seal: SourceAcquisitionSeal,
    owner: RetainedExecutionAssets,
    request: RetainedRequestFrameV2,
    policy: dict[str, Any],
    observation: dict[str, Any],
    response: RetainedResponseFrameV2,
) -> None:
    """Full data-only transport join; no Core semantic or actual OS certificate."""

    validate_observation_request_v2(observation, policy, request, seal, owner)
    validate_response_request_v2(response, request, seal, owner)
    validate_response_frame_observation_v2(observation, policy, response)
    if not observation["transport_payload_admissible"]:
        raise ValueError("exchange has no transport-admissible semantic candidate")


def validate_compatibility_descriptor_v2(
    value: dict[str, Any], candidate: ValidatedTransportCandidateV2
) -> None:
    """Lock semantic metadata and join it to the whole-exchange runtime owner."""

    from tests.contracts.next_runtime_v2_reference import ValidatedTransportCandidateV2

    if type(candidate) is not ValidatedTransportCandidateV2:
        raise TypeError("compatibility requires a whole-exchange transport candidate owner")
    _validate_schema("next-compatibility-v2", value)
    if any(value[key] != item for key, item in semantic_compatibility_metadata_v2().items()):
        raise ValueError("compatibility differs from its locked semantic profile")
    binding = candidate.runtime_binding()
    validate_runtime_binding_identity_v1(binding)
    expected = {
        "runtime_binding_profile_id": binding["runtime_binding_profile_id"],
        "typescript_identity": binding["typescript_identity"],
        "trusted_type_environment_digest": binding["trusted_type_environment_digest"],
        "portable_toolchain_fingerprint": binding["runtime_toolchain_fingerprint"],
    }
    if any(value[key] != item for key, item in expected.items()):
        raise ValueError("compatibility differs from its retained runtime binding")
    if value["compatibility_id"] != digest(
        {key: item for key, item in value.items() if key not in {"schema", "compatibility_id"}}
    ):
        raise ValueError("compatibility_id differs from its new portable preimage")


def validate_semantic_candidate_v2(
    candidate: ValidatedTransportCandidateV2,
    seal: SourceAcquisitionSeal,
    owner: RetainedExecutionAssets,
) -> dict[str, Any]:
    """Core checks are separate from the transport owner and its true predicate."""

    from tests.contracts.next_runtime_v2_reference import ValidatedTransportCandidateV2

    if type(candidate) is not ValidatedTransportCandidateV2:
        raise TypeError("Core requires a whole-exchange transport candidate owner")
    validate_response_request_v2(candidate.response_frame(), candidate.request_frame(), seal, owner)
    payload = candidate.semantic_payload()
    if payload["model_digest"] != digest(payload["model"]):
        raise ValueError("semantic model digest differs from the retained payload")
    try:
        _validate_project_correspondence(
            candidate.request_frame().record()["projects"], payload["model"]["projects"]
        )
    except AssertionError as exc:
        raise ValueError("semantic project correspondence differs from its frozen request") from exc
    expected_files = [
        {key: value for key, value in record.items() if key != "content_base64"}
        for record in candidate.request_frame().record()["files"]
    ]
    if payload["model"]["files"] != expected_files:
        raise ValueError("semantic file correspondence differs from its frozen request")
    request = candidate.request_frame().record()
    model, proof = payload["model"], payload["proof"]
    program_keys = {
        (file["project_id"], file["path"]) for file in request["files"] if _is_program_file(file)
    }
    for row in proof["discovered_records"]:
        if row["collection"] in {"projects", "files"} and row.get("record") is not None:
            # Every frozen source project/file is already required in model correspondence.
            # A supplied proof-only source record is therefore not another observed source.
            raise ValueError("proof-only source metadata is outside the frozen request owner")
        if (
            row["collection"] == "modules"
            and (record := row.get("record")) is not None
            and (
                record.get("kind") != "module"
                or (record.get("project_id"), record.get("path")) not in program_keys
            )
        ):
            raise ValueError("proof-only module has no frozen program source owner")
    context = canonical_run_context(**payload["run_context"])
    try:
        target_failure = target_completeness_failure(model, request["targets"])
        allowed_keys, allowed_ids = _target_missing_module_exceptions(
            model, request["targets"], target_failure
        )
        allowed_duplicates = _target_duplicate_module_exceptions(
            model, request["targets"], target_failure
        )
        _validate_response_base(
            payload,
            allowed_missing_module_keys=allowed_keys,
            allowed_missing_module_ids=allowed_ids,
            allowed_duplicate_module_keys=allowed_duplicates,
        )
        known_ids = {record["id"] for collection in COLLECTIONS for record in model[collection]} | {
            row["record_id"] for row in proof["discovered_records"]
        }
        for row in proof["discovered_records"]:
            if (record := row.get("record")) is not None:
                references = {value for value in _record_references(record) if value is not None}
                if not references <= known_ids | allowed_ids:
                    raise ValueError(
                        "proof-only record contains a dangling reference outside its owner"
                    )
        if target_failure is not None:
            _validate_target_exception_proof_base(proof, model, request["targets"], target_failure)
            return target_failure_decision(target_failure, context)
        actual = validate_model(model, max_model_records=request["limits"]["max_total_array_items"])
        validate_proof(proof, model, request_targets=request["targets"])
        proof_failure = target_failure_from_proof(proof)
        if proof_failure is not None:
            return target_failure_decision(proof_failure, context)
        outcome = derive_pre_budget_outcome(proof, model)
    except AssertionError as exc:
        raise ValueError("semantic model/proof violates its closed invariants") from exc
    _published, _proof_only, wire_records = response_model_record_counts(model, proof)
    if wire_records > request["limits"]["max_model_records"]:
        raise ModelRecordLimitError(wire_records)
    export_failure = export_failure_decision(proof, context)
    if export_failure is not None:
        return export_failure
    return entity_budget_gate(actual, original_outcome=outcome, run_context=context)


def validate_semantic_decision_v2(decision: ValidatedSemanticDecisionV2) -> None:
    """Recheck the same immutable Core owners, never a caller-supplied gate dict."""

    from tests.contracts.next_runtime_v2_reference import ValidatedSemanticDecisionV2

    if type(decision) is not ValidatedSemanticDecisionV2:
        raise TypeError("semantic validation requires a Core decision owner")
    candidate = decision.transport_candidate()
    expected = validate_semantic_candidate_v2(
        candidate, decision.source_seal(), decision.execution_assets()
    )
    if decision.gate() != expected:
        raise ValueError("semantic gate differs from its retained Core decision")
    validate_compatibility_descriptor_v2(decision.compatibility_descriptor(), candidate)


def _cleanup_is_verified(cleanup: dict[str, Any]) -> bool:
    return bool(
        cleanup["group_stop"] != "unverified"
        and all(
            cleanup[key]
            for key in (
                "direct_child_waited",
                "pipes_closed",
                "candidate_closed",
                "private_root_removed",
            )
        )
    )


def _capture_is_complete(capture: dict[str, Any] | None) -> bool:
    return bool(
        capture is not None
        and capture["stdin_bytes"] == capture["stdin_sent_bytes"]
        and capture["stdout_bytes"] > 0
        and capture["stdout_eof"]
        and capture["stderr_eof"]
        and capture["stdout_bytes"] == capture["stdout_retained_bytes"]
        and capture["stderr_bytes"] == capture["stderr_retained_bytes"]
    )
