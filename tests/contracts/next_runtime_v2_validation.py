"""Small data-only A-runtime validators, independent of the historical v1 lane."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]
from referencing import Registry, Resource

from tests.contracts.next_reference_validation import bounded_decode_json
from tests.contracts.next_trusted_profile_v1_reference import (
    PROFILE_DECLARATIONS,
    TRUSTED_PACKAGE_PREFIX,
    TRUSTED_VIRTUAL_PREFIX,
    trusted_profile_metadata_v1,
)

if TYPE_CHECKING:
    from code_structure_viz.adapters.next.source_acquisition import SourceAcquisitionSeal
    from tests.contracts.next_runtime_v2_reference import (
        RetainedExecutionAssets,
        RetainedResponseFrameV2,
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
    if value["terminal_cause"] == "none" and value["response"] is not None:
        expected_exit = {
            "success": 0,
            "protocol_failure": 65,
            "unsupported_runtime": 66,
            "bootstrap_failure": 67,
            "semantic_failure": 68,
        }[value["response"]["control"]["result_kind"]]
        if value["exit_code"] != expected_exit:
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
