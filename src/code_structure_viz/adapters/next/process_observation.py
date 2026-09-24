from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, cast

from code_structure_viz.semantic.canonical_json import encode_sorted_canonical_json

_OBSERVATION_SCHEMA = "code-structure-viz.next-process-launch-observation/v1"
_FINGERPRINT_FIELDS = frozenset(
    {
        "stable_fingerprint",
        "stable_toolchain_fingerprint",
        "local_process_attestation_digest",
    }
)


@dataclass(frozen=True, slots=True, init=False)
class NextProcessLaunchObservation:
    """Immutable canonical process observation bytes owned by the Next adapter."""

    canonical_bytes: bytes = field(repr=False)

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("Next process observations are created by their producer")

    @classmethod
    def _from_producer(cls, value: dict[str, Any]) -> NextProcessLaunchObservation:
        instance = object.__new__(cls)
        object.__setattr__(instance, "canonical_bytes", _canonical_json_bytes(value))
        instance.__post_init__()
        return instance

    def __post_init__(self) -> None:
        if not isinstance(self.canonical_bytes, bytes):
            raise TypeError("process observation authority must be immutable bytes")
        value = json.loads(self.canonical_bytes)
        if not isinstance(value, dict) or _canonical_json_bytes(value) != self.canonical_bytes:
            raise ValueError("process observation bytes must be canonical JSON")
        stable = _stable_fingerprint(value)
        if (
            value.get("stable_fingerprint") != stable
            or value.get("stable_toolchain_fingerprint") != stable
            or value.get("local_process_attestation_digest") != _local_attestation_digest(value)
        ):
            raise ValueError("process observation digests do not match their authority")

    def as_dict(self) -> dict[str, Any]:
        """Return an isolated projection; the canonical bytes remain authoritative."""

        return cast(dict[str, Any], json.loads(self.canonical_bytes))


def production_unavailable_process_observation() -> NextProcessLaunchObservation:
    """Describe that no accepted production runner is available, without host access."""

    value: dict[str, Any] = {
        "schema": _OBSERVATION_SCHEMA,
        "version": 1,
        "kind": "production",
        "host_os": "unknown",
        "node_status": "unavailable",
        "argv": ["<unavailable>", "/.code-structure-viz/next-adapter.mjs"],
        "shell": False,
        "process_group": {
            "create": True,
            "terminate_scope": "group",
            "wait_after_terminate": True,
        },
        "cwd": "/.code-structure-viz/private-run",
        "env_allowlist": {"LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC"},
        "denied_env": ["NODE_OPTIONS", "NODE_PATH", "PATH", "npm_config_user_config"],
        "stdio": {"stdin": "pipe", "stdout": "pipe", "stderr": "pipe"},
        "fd_inheritance": {"close_fds": True, "allowed": [0, 1, 2]},
        "node_realpath": None,
        "node_sha256": None,
        "node_version": None,
        "file_identity_at_hash": None,
        "file_identity_at_spawn": None,
        "verified_open_handle": None,
        "spawn_primitive": None,
        "post_spawn_identity_check": None,
        "fd_lifecycle": None,
        "toctou_failure_point": "node-discovery",
    }
    stable = _stable_fingerprint(value)
    value["stable_fingerprint"] = stable
    value["stable_toolchain_fingerprint"] = stable
    value["local_process_attestation_digest"] = _local_attestation_digest(value)
    return NextProcessLaunchObservation._from_producer(value)


def _canonical_json_bytes(value: object) -> bytes:
    """Return sorted canonical JSON without the presentation line terminator."""

    encoded = encode_sorted_canonical_json(value)
    if not encoded.endswith(b"\n"):
        raise ValueError("canonical JSON encoder must end with LF")
    return encoded[:-1]


def _stable_fingerprint(value: dict[str, Any]) -> str:
    argv = list(value["argv"])
    if value["node_status"] == "available":
        argv[0] = "<node>"
    projection: dict[str, Any] = {
        "schema": value["schema"],
        "version": value["version"],
        "kind": value["kind"],
        "node_status": value["node_status"],
        "argv": argv,
        "shell": value["shell"],
        "process_group": value["process_group"],
        "node_sha256": value.get("node_sha256"),
        "node_version": value.get("node_version"),
        "stdio": value["stdio"],
        "fd_inheritance": value["fd_inheritance"],
        "env_allowlist": value["env_allowlist"],
        "denied_env": value["denied_env"],
    }
    if value["kind"] == "fixture":
        projection["fixture_id"] = value["fixture_id"]
        projection["identity_token"] = value["identity_token"]
    for name in ("adapter", "timeout_seconds", "capture_limits"):
        if name in value:
            projection[name] = value[name]
    return hashlib.sha256(_canonical_json_bytes(projection)).hexdigest()


def _local_attestation_digest(value: dict[str, Any]) -> str:
    local = {key: item for key, item in value.items() if key not in _FINGERPRINT_FIELDS}
    return hashlib.sha256(_canonical_json_bytes(local)).hexdigest()
