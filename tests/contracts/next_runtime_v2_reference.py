"""Data-only A-runtime reference producers; never a production runner."""

import hashlib
import json
import re
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, cast

from tests.contracts.next_runtime_v2_validation import (
    process_payload_gate_v2,
    validate_execution_asset_identity_v1,
    validate_launch_policy_assets_v2,
    validate_process_launch_policy_v2,
    validate_process_observation_v2,
    validate_response_frame_bytes_v2,
    validate_runtime_binding_identity_v1,
    validate_runtime_binding_observation_v1,
)

ENTRYPOINT_MEMBER = "code_structure_viz/_next_runtime/next-adapter.mjs"


@dataclass(frozen=True)
class RetainedExecutionAssets:
    """One immutable byte snapshot for content identity and later staging."""

    _members: tuple[tuple[str, str, bytes], ...] = field(repr=False)

    def descriptor(self) -> dict[str, Any]:
        record: dict[str, Any] = {
            "schema": "code-structure-viz.next-execution-assets/v1",
            "entrypoint_member": ENTRYPOINT_MEMBER,
            "members": [
                {
                    "package_path": path,
                    "role": role,
                    "size_bytes": len(content),
                    "sha256": hashlib.sha256(content).hexdigest(),
                }
                for path, role, content in self._members
            ],
        }
        preimage = json.dumps(
            record, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return {**record, "asset_set_id": hashlib.sha256(preimage).hexdigest()}

    def staging_members(self) -> tuple[tuple[str, bytes], ...]:
        return tuple((path, content) for path, _role, content in self._members)

    def adapter_identity(self) -> dict[str, str]:
        content = next(
            content for path, _role, content in self._members if path == ENTRYPOINT_MEMBER
        )
        if content.count(b"CodeStructureViz-Adapter-Version:") != 1:
            raise ValueError("retained adapter version marker is missing or duplicated")
        marker = re.match(
            rb"\A// CodeStructureViz-Adapter-Version: "
            rb"((?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*))\n",
            content,
        )
        if marker is None:
            raise ValueError("retained adapter header has no canonical stable version")
        return {
            "protocol": "code-structure-viz.next-adapter/v2",
            "version": marker.group(1).decode("ascii"),
            "sha256": hashlib.sha256(content).hexdigest(),
            "entrypoint_member": ENTRYPOINT_MEMBER,
        }


def retain_execution_assets_v1(
    members: Mapping[str, tuple[str, bytes]],
) -> RetainedExecutionAssets:
    """Freeze already-read reference bytes, not paths for a later resource read."""

    snapshot = tuple((path, role, content) for path, (role, content) in members.items())
    if any(not isinstance(content, bytes) for _path, _role, content in snapshot):
        raise TypeError("execution asset content must already be immutable bytes")
    retained = RetainedExecutionAssets(
        tuple(
            (path, role, bytes(content))
            for path, role, content in sorted(snapshot, key=lambda row: row[0].encode("utf-8"))
        )
    )
    validate_execution_asset_identity_v1(retained.descriptor())
    return retained


def runtime_binding_identity_v1(
    policy: dict[str, Any], assets: RetainedExecutionAssets, *, node_version: str
) -> dict[str, Any]:
    """Project reference identity; a supplied version is not process admission."""

    validate_launch_policy_assets_v2(policy, assets)
    adapter = assets.adapter_identity()
    preimage: dict[str, Any] = {
        "runtime_binding_profile_id": "next-public-spawn-runtime-v1",
        "node_candidate": {"sha256": policy["node_candidate"]["sha256"]},
        "node_observation": {"version": node_version, "source": "process.versions.node"},
        "execution_asset_set_id": assets.descriptor()["asset_set_id"],
        "adapter": {key: adapter[key] for key in ("protocol", "version", "sha256")},
        "typescript_identity": policy["typescript_identity"],
        "trusted_type_environment_digest": policy["trusted_environment_digest"],
    }
    encoded = json.dumps(
        preimage, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    identity = {
        "schema": "code-structure-viz.next-runtime-binding/v1",
        **preimage,
        "adapter": adapter,
        "runtime_toolchain_fingerprint": hashlib.sha256(encoded).hexdigest(),
    }
    validate_runtime_binding_identity_v1(identity)
    return identity


def reference_process_observation_v2(
    policy: dict[str, Any], evidence: dict[str, Any]
) -> dict[str, Any]:
    """Seal explicit reference evidence, never claim a real OS launch."""

    validate_process_launch_policy_v2(policy)
    if policy["producer"] != "reference":
        raise ValueError("reference observation requires a reference policy")
    if set(evidence) != {
        "spawn",
        "capture",
        "exit_code",
        "response",
        "candidate_check",
        "assets_check",
        "terminal_cause",
        "cleanup",
    }:
        raise ValueError("reference evidence fields differ from the closed owner input")
    encoded_policy = json.dumps(
        policy, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    record = {
        "schema": "code-structure-viz.next-process-launch-observation/v2",
        "version": 2,
        "producer": "reference",
        "platform": "fixture",
        "request_id": policy["request_id"],
        "policy_digest": hashlib.sha256(encoded_policy).hexdigest(),
        **deepcopy(evidence),
        "transport_payload_admissible": False,
    }
    record["transport_payload_admissible"] = process_payload_gate_v2(record)
    validate_process_observation_v2(record, policy)
    return record


def runtime_binding_from_observation_v1(
    policy: dict[str, Any], assets: RetainedExecutionAssets, observation: dict[str, Any]
) -> dict[str, Any]:
    """Join reference records; raw response bytes and OS evidence remain separate."""

    validate_process_observation_v2(observation, policy)
    if not observation["transport_payload_admissible"]:
        raise ValueError("runtime binding requires a successful transport observation")
    binding = runtime_binding_identity_v1(
        policy, assets, node_version=observation["response"]["control"]["runtime"]["version"]
    )
    validate_runtime_binding_observation_v1(binding, policy, assets, observation)
    return binding


@dataclass(frozen=True, slots=True, init=False)
class RetainedResponseFrameV2:
    """Immutable response-byte authority; never a semantic or OS certificate."""

    raw_bytes: bytes = field(repr=False)
    sha256: str

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("response frames are created by retain_response_frame_v2")

    @classmethod
    def _from_validated(cls, raw: bytes) -> "RetainedResponseFrameV2":
        instance = object.__new__(cls)
        object.__setattr__(instance, "raw_bytes", raw)
        object.__setattr__(instance, "sha256", hashlib.sha256(raw).hexdigest())
        return instance

    def control(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(self.raw_bytes)["control"])

    def semantic_payload(self) -> dict[str, Any] | None:
        return cast(dict[str, Any] | None, json.loads(self.raw_bytes)["semantic_payload"])


def retain_response_frame_v2(raw: bytes, *, limits: dict[str, int]) -> RetainedResponseFrameV2:
    """Freeze a reference response frame; no caller metadata is response authority."""

    validate_response_frame_bytes_v2(raw, limits)
    return RetainedResponseFrameV2._from_validated(raw)
