"""Data-only A-runtime reference producers; never a production runner."""

import base64
import hashlib
import json
import re
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, cast

from code_structure_viz.adapters.next.source_acquisition import SourceAcquisitionSeal
from tests.contracts.next_reference_validation import (
    canonical_json_bytes,
    digest,
    project_config_digest,
    recompute_record_id,
)
from tests.contracts.next_runtime_v2_validation import (
    process_payload_gate_v2,
    validate_compatibility_descriptor_v2,
    validate_execution_asset_identity_v1,
    validate_launch_policy_assets_v2,
    validate_process_launch_policy_v2,
    validate_process_observation_v2,
    validate_request_frame_v2,
    validate_request_json_limits_v2,
    validate_request_record_v2,
    validate_request_stdin_bytes_v2,
    validate_response_frame_bytes_v2,
    validate_runtime_binding_identity_v1,
    validate_runtime_binding_observation_v1,
    validate_semantic_candidate_v2,
    validate_source_seal_trusted_v2,
    validate_transport_exchange_v2,
    validate_trusted_environment_manifest_v2,
)
from tests.contracts.next_semantic_profile_v1_reference import semantic_compatibility_metadata_v2
from tests.contracts.next_trusted_profile_v1_reference import (
    PROFILE_DECLARATIONS,
    TRUSTED_PACKAGE_PREFIX,
    TRUSTED_VIRTUAL_PREFIX,
    trusted_profile_metadata_v1,
)

ENTRYPOINT_MEMBER = "code_structure_viz/_next_runtime/next-adapter.mjs"


@dataclass(frozen=True, slots=True, init=False)
class RetainedExecutionAssets:
    """One immutable byte snapshot for content identity and later staging."""

    _members: tuple[tuple[str, str, bytes], ...] = field(repr=False)

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("execution assets are created by retain_execution_assets_v1")

    @classmethod
    def _from_retained_members(
        cls, members: tuple[tuple[str, str, bytes], ...]
    ) -> "RetainedExecutionAssets":
        instance = object.__new__(cls)
        object.__setattr__(instance, "_members", members)
        return instance

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
    retained = RetainedExecutionAssets._from_retained_members(
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


def trusted_environment_manifest_v2(assets: RetainedExecutionAssets) -> dict[str, Any]:
    """Read-only profile metadata from retained bytes; no resource relookup."""

    if type(assets) is not RetainedExecutionAssets:
        raise TypeError("trusted metadata requires a retained execution asset owner")
    members = {member["package_path"]: member for member in assets.descriptor()["members"]}
    if any(TRUSTED_PACKAGE_PREFIX + name not in members for name, *_rest in PROFILE_DECLARATIONS):
        raise ValueError("retained bytes are missing a locked trusted declaration")
    if {path for path, row in members.items() if row["role"] == "trusted_declaration"} != {
        TRUSTED_PACKAGE_PREFIX + name for name, *_rest in PROFILE_DECLARATIONS
    }:
        raise ValueError("retained assets differ from the locked declaration role set")
    if any(
        members[TRUSTED_PACKAGE_PREFIX + name]["size_bytes"] != size
        or members[TRUSTED_PACKAGE_PREFIX + name]["sha256"] != sha
        for name, size, sha, _license in PROFILE_DECLARATIONS
    ):
        raise ValueError("retained bytes differ from the locked trusted declaration profile")
    files = [
        {
            "package_path": TRUSTED_PACKAGE_PREFIX + name,
            "virtual_path": TRUSTED_VIRTUAL_PREFIX + name,
            "size_bytes": members[TRUSTED_PACKAGE_PREFIX + name]["size_bytes"],
            "sha256": members[TRUSTED_PACKAGE_PREFIX + name]["sha256"],
            "license_id": license_id,
        }
        for name, _size, _sha, license_id in PROFILE_DECLARATIONS
    ]
    descriptor = {
        "schema": "code-structure-viz.next-trusted-types/v2",
        "environment_version": "2",
        "semantic_profile_id": "next-trusted-profile-v1",
    }
    metadata = trusted_profile_metadata_v1()
    preimage = {
        **descriptor,
        **metadata,
        "files": [
            {key: value for key, value in row.items() if key != "package_path"} for row in files
        ],
    }
    encoded = json.dumps(
        preimage, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    manifest = {
        "schema": "code-structure-viz.next-trusted-type-environment-manifest/v2",
        "environment_descriptor": {**descriptor, "sha256": hashlib.sha256(encoded).hexdigest()},
        **metadata,
        "files": files,
    }
    encoded_manifest = json.dumps(
        manifest, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    manifest["manifest_sha256"] = hashlib.sha256(encoded_manifest).hexdigest()
    validate_trusted_environment_manifest_v2(manifest, assets)
    return manifest


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


@dataclass(frozen=True, slots=True, init=False)
class RetainedRequestFrameV2:
    """Generated private bytes bound to one source seal, not a Node observation."""

    canonical_bytes: bytes = field(repr=False)
    request_id: str
    source_seal_id: str = field(repr=False)
    execution_asset_set_id: str = field(repr=False)

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("request frames are created by build_request_frame_v2")

    @classmethod
    def _from_builder(
        cls, *, raw: bytes, request_id: str, source_seal_id: str, execution_asset_set_id: str
    ) -> "RetainedRequestFrameV2":
        instance = object.__new__(cls)
        object.__setattr__(instance, "canonical_bytes", raw)
        object.__setattr__(instance, "request_id", request_id)
        object.__setattr__(instance, "source_seal_id", source_seal_id)
        object.__setattr__(instance, "execution_asset_set_id", execution_asset_set_id)
        return instance

    def record(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(self.canonical_bytes))


def build_request_frame_v2(
    seal: SourceAcquisitionSeal,
    assets: RetainedExecutionAssets,
    *,
    targets: list[str],
    run_context: dict[str, Any],
) -> RetainedRequestFrameV2:
    """Reference projection from retained owners; never reopen target/package files."""

    validate_source_seal_trusted_v2(seal, assets)
    plan = seal.final_plan
    applicable_roots = set(seal.package_applicability.applicable_projects)
    projects: dict[str, dict[str, Any]] = {}
    for row in plan["projects"]:
        if row["root"] not in applicable_roots:
            continue
        project = {
            "kind": "project",
            **{
                key: deepcopy(row[key])
                for key in ("root", "source_roots", "config_path", "compiler_options")
            },
            "file_ids": [],
        }
        project["id"] = recompute_record_id(project)
        project["config_digest"] = project_config_digest(project)
        projects[row["root"]] = project
    source = {item.path.as_posix(): item for item in seal.source_view.files}
    files = []
    for row in plan["file_role_map"]:
        if row["project_root"] not in applicable_roots:
            continue
        observed = source[row["path"]]
        file_record = {
            "kind": "file",
            "path": row["path"],
            "project_id": projects[row["project_root"]]["id"],
            "roles": list(row["roles"]),
            "effective_role": row["effective_role"],
            "size_bytes": observed.size_bytes,
            "sha256": observed.sha256,
            "content_base64": base64.b64encode(observed.content).decode("ascii"),
        }
        file_record["id"] = recompute_record_id(file_record)
        files.append(file_record)
        projects[row["project_root"]]["file_ids"].append(file_record["id"])
    for project in projects.values():
        project["file_ids"].sort()
    request = {
        "schema": "code-structure-viz.next-adapter-request/v2",
        "protocol": "code-structure-viz.next-adapter/v2",
        "adapter_version": assets.adapter_identity()["version"],
        "trusted_type_environment": trusted_environment_manifest_v2(assets)[
            "environment_descriptor"
        ],
        "runtime_requirement": {
            "schema": "code-structure-viz.next-node-runtime-requirement/v1",
            "engine": "node",
            "release": "stable",
            "minimum_major": 22,
        },
        "projects": [projects[root] for root in sorted(projects, key=lambda p: p.encode("utf-8"))],
        "files": sorted(files, key=lambda item: item["id"]),
        "targets": list(targets),
        "limits": plan["limits"],
        "run_context": deepcopy(run_context),
    }
    validate_request_json_limits_v2(request, request["limits"])
    request["request_id"] = digest(request)
    validate_request_record_v2(request)
    raw = canonical_json_bytes(request)
    validate_request_stdin_bytes_v2(raw, request["limits"])
    retained = RetainedRequestFrameV2._from_builder(
        raw=raw,
        request_id=request["request_id"],
        source_seal_id=seal.seal_id,
        execution_asset_set_id=assets.descriptor()["asset_set_id"],
    )
    validate_request_frame_v2(retained, seal, assets)
    return retained


@dataclass(frozen=True, slots=True, init=False)
class ValidatedTransportCandidateV2:
    """Closed data joins only: not Core proof, actual TS or OS acceptance."""

    _request: RetainedRequestFrameV2 = field(repr=False)
    _response: RetainedResponseFrameV2 = field(repr=False)
    _runtime_binding_bytes: bytes = field(repr=False)

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("transport candidates are created by retain_transport_candidate_v2")

    @classmethod
    def _from_exchange(
        cls,
        request: RetainedRequestFrameV2,
        response: RetainedResponseFrameV2,
        binding: dict[str, Any],
    ) -> "ValidatedTransportCandidateV2":
        instance = object.__new__(cls)
        object.__setattr__(instance, "_request", request)
        object.__setattr__(instance, "_response", response)
        object.__setattr__(
            instance,
            "_runtime_binding_bytes",
            json.dumps(
                binding, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8"),
        )
        return instance

    @property
    def request_id(self) -> str:
        return self._request.request_id

    def request_frame(self) -> RetainedRequestFrameV2:
        return self._request

    def response_frame(self) -> RetainedResponseFrameV2:
        return self._response

    def runtime_binding(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(self._runtime_binding_bytes))

    def semantic_payload(self) -> dict[str, Any]:
        return cast(dict[str, Any], self._response.semantic_payload())


def retain_transport_candidate_v2(
    seal: SourceAcquisitionSeal,
    assets: RetainedExecutionAssets,
    request: RetainedRequestFrameV2,
    policy: dict[str, Any],
    observation: dict[str, Any],
    response: RetainedResponseFrameV2,
) -> ValidatedTransportCandidateV2:
    """Reference-only whole exchange seal; never trust a free gate checkbox."""

    validate_transport_exchange_v2(seal, assets, request, policy, observation, response)
    binding = runtime_binding_from_observation_v1(policy, assets, observation)
    return ValidatedTransportCandidateV2._from_exchange(request, response, binding)


def compatibility_descriptor_v2(candidate: ValidatedTransportCandidateV2) -> dict[str, Any]:
    """Parent-owned projection after whole exchange joins, never from child fields."""

    if type(candidate) is not ValidatedTransportCandidateV2:
        raise TypeError("compatibility requires a whole-exchange transport candidate owner")
    binding = candidate.runtime_binding()
    value = {
        "schema": "code-structure-viz.next-semantic-compatibility/v2",
        **semantic_compatibility_metadata_v2(),
        "typescript_identity": binding["typescript_identity"],
        "trusted_type_environment_digest": binding["trusted_type_environment_digest"],
        "portable_toolchain_fingerprint": binding["runtime_toolchain_fingerprint"],
    }
    value["compatibility_id"] = digest(
        {key: item for key, item in value.items() if key != "schema"}
    )
    validate_compatibility_descriptor_v2(value, candidate)
    return value


@dataclass(frozen=True, slots=True, init=False)
class ValidatedSemanticDecisionV2:
    """Reference Core authority, not actual TypeScript or publication acceptance."""

    _candidate: ValidatedTransportCandidateV2 = field(repr=False)
    _seal: SourceAcquisitionSeal = field(repr=False)
    _assets: RetainedExecutionAssets = field(repr=False)
    _gate_bytes: bytes = field(repr=False)
    _compatibility_bytes: bytes = field(repr=False)

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("semantic decisions are created by decide_semantic_candidate_v2")

    @classmethod
    def _from_validated_core(
        cls,
        candidate: ValidatedTransportCandidateV2,
        seal: SourceAcquisitionSeal,
        assets: RetainedExecutionAssets,
        gate: dict[str, Any],
        compatibility: dict[str, Any],
    ) -> "ValidatedSemanticDecisionV2":
        instance = object.__new__(cls)
        object.__setattr__(instance, "_candidate", candidate)
        object.__setattr__(instance, "_seal", seal)
        object.__setattr__(instance, "_assets", assets)
        object.__setattr__(instance, "_gate_bytes", canonical_json_bytes(gate))
        object.__setattr__(instance, "_compatibility_bytes", canonical_json_bytes(compatibility))
        return instance

    @property
    def request_id(self) -> str:
        return self._candidate.request_id

    def transport_candidate(self) -> ValidatedTransportCandidateV2:
        return self._candidate

    def source_seal(self) -> SourceAcquisitionSeal:
        return self._seal

    def execution_assets(self) -> RetainedExecutionAssets:
        return self._assets

    def gate(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(self._gate_bytes))

    def compatibility_descriptor(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(self._compatibility_bytes))


def decide_semantic_candidate_v2(
    candidate: ValidatedTransportCandidateV2,
    seal: SourceAcquisitionSeal,
    assets: RetainedExecutionAssets,
) -> ValidatedSemanticDecisionV2:
    """Mint an immutable authority only after source, model and proof admission."""

    gate = validate_semantic_candidate_v2(candidate, seal, assets)
    compatibility = compatibility_descriptor_v2(candidate)
    return ValidatedSemanticDecisionV2._from_validated_core(
        candidate, seal, assets, gate, compatibility
    )
