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
from tests.contracts.next_core_failure_v2_reference import (
    RejectedSemanticDecisionV2 as RejectedSemanticDecisionV2,
)
from tests.contracts.next_core_failure_v2_reference import (
    inspect_semantic_candidate_v2 as inspect_semantic_candidate_v2,
)
from tests.contracts.next_reference_validation import (
    canonical_json_bytes,
    digest,
    project_config_digest,
    recompute_record_id,
)
from tests.contracts.next_runtime_v2_validation import (
    process_payload_gate_v2,
    response_rejection_v2,
    validate_compatibility_descriptor_v2,
    validate_execution_asset_identity_v1,
    validate_launch_policy_assets_v2,
    validate_next_analysis_context_v2,
    validate_observation_request_v2,
    validate_observed_response_receipt_before_disposal_v2,
    validate_process_launch_policy_v2,
    validate_process_observation_v2,
    validate_rejected_frame_observation_v2,
    validate_rejected_semantic_decision_v2,
    validate_request_frame_v2,
    validate_request_json_limits_v2,
    validate_request_record_v2,
    validate_request_stdin_bytes_v2,
    validate_response_frame_bytes_v2,
    validate_response_frame_observation_v2,
    validate_response_request_v2,
    validate_runtime_binding_identity_v1,
    validate_runtime_binding_observation_v1,
    validate_runtime_result_v2,
    validate_semantic_candidate_v2,
    validate_semantic_decision_v2,
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
class RejectedResponseFrameV2:
    """Bounded decoder failure metadata only; no raw body or validated control."""

    _failure_bytes: bytes = field(repr=False)
    _limits_bytes: bytes = field(repr=False)

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("response rejections are created by inspect_response_frame_v2")

    @classmethod
    def _from_rejected_bytes(
        cls, failure: dict[str, Any], limits: dict[str, int]
    ) -> "RejectedResponseFrameV2":
        instance = object.__new__(cls)
        object.__setattr__(instance, "_failure_bytes", canonical_json_bytes(failure))
        object.__setattr__(instance, "_limits_bytes", canonical_json_bytes(limits))
        return instance

    def failure(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(self._failure_bytes))

    def limits(self) -> dict[str, int]:
        return cast(dict[str, int], json.loads(self._limits_bytes))


def inspect_response_frame_v2(
    raw: bytes, *, limits: dict[str, int]
) -> RetainedResponseFrameV2 | RejectedResponseFrameV2:
    """Retain a valid frame or typed rejection, never a raw failure buffer."""

    failure = response_rejection_v2(raw, limits)
    if failure is not None:
        return RejectedResponseFrameV2._from_rejected_bytes(failure, limits)
    return retain_response_frame_v2(raw, limits=limits)


@dataclass(frozen=True, slots=True, init=False)
class RetainedNextAnalysisContextV2:
    """Immutable parent intent/config; not a child or selected-graph certificate."""

    _seal: SourceAcquisitionSeal = field(repr=False)
    _assets: RetainedExecutionAssets = field(repr=False)
    _intent_bytes: bytes = field(repr=False)
    _run_context_bytes: bytes = field(repr=False)
    _config_bytes: bytes = field(repr=False)

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("analysis contexts are created by retain_next_analysis_context_v2")

    @classmethod
    def _from_validated_intent(
        cls,
        seal: SourceAcquisitionSeal,
        assets: RetainedExecutionAssets,
        intent: dict[str, Any],
        context: dict[str, Any],
        config: dict[str, Any],
    ) -> "RetainedNextAnalysisContextV2":
        instance = object.__new__(cls)
        object.__setattr__(instance, "_seal", seal)
        object.__setattr__(instance, "_assets", assets)
        object.__setattr__(instance, "_intent_bytes", canonical_json_bytes(intent))
        object.__setattr__(instance, "_run_context_bytes", canonical_json_bytes(context))
        object.__setattr__(instance, "_config_bytes", canonical_json_bytes(config))
        return instance

    def source_seal(self) -> SourceAcquisitionSeal:
        return self._seal

    def execution_assets(self) -> RetainedExecutionAssets:
        return self._assets

    def analysis_intent(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(self._intent_bytes))

    def run_context(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(self._run_context_bytes))

    def domain_config(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(self._config_bytes))


def retain_next_analysis_context_v2(
    seal: SourceAcquisitionSeal,
    assets: RetainedExecutionAssets,
    *,
    targets: list[str],
    upstream_depth: int,
    downstream_depth: int,
    run_context: dict[str, Any],
) -> RetainedNextAnalysisContextV2:
    """Seal resolved intent without accepting caller-selected config or digests."""

    validate_source_seal_trusted_v2(seal, assets)
    plan = seal.final_plan
    applicable = set(seal.package_applicability.applicable_projects)
    intent = {
        "targets": deepcopy(targets),
        "upstream_depth": upstream_depth,
        "downstream_depth": downstream_depth,
    }
    validate_request_json_limits_v2({"intent": intent, "run_context": run_context}, plan["limits"])
    config = {
        "schema": "code-structure-viz.domain-config/next/v1",
        "request_independent": False,
        "projects": [deepcopy(row) for row in plan["projects"] if row["root"] in applicable],
        **intent,
        "formats": deepcopy(run_context["requested_formats"]),
        "limits": deepcopy(plan["limits"]),
        "trusted_environment_digest": plan["trusted_environment_digest"],
        "source_plan": plan,
        "source_plan_digest": seal.plan_digest,
        "config_resolution": deepcopy(plan["config_resolution"]),
    }
    config["domain_config_digest"] = digest(config)
    retained = RetainedNextAnalysisContextV2._from_validated_intent(
        seal, assets, intent, run_context, config
    )
    validate_next_analysis_context_v2(retained, seal, assets)
    return retained


@dataclass(frozen=True, slots=True, init=False)
class RetainedRequestFrameV2:
    """Generated private bytes bound to one source seal, not a Node observation."""

    canonical_bytes: bytes = field(repr=False)
    request_id: str
    source_seal_id: str = field(repr=False)
    execution_asset_set_id: str = field(repr=False)
    _analysis_context: RetainedNextAnalysisContextV2 = field(repr=False)
    analysis_context_digest: str = field(repr=False)

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("request frames are created by build_request_frame_v2")

    @classmethod
    def _from_builder(
        cls,
        *,
        raw: bytes,
        request_id: str,
        source_seal_id: str,
        execution_asset_set_id: str,
        analysis_context: RetainedNextAnalysisContextV2,
        analysis_context_digest: str,
    ) -> "RetainedRequestFrameV2":
        instance = object.__new__(cls)
        object.__setattr__(instance, "canonical_bytes", raw)
        object.__setattr__(instance, "request_id", request_id)
        object.__setattr__(instance, "source_seal_id", source_seal_id)
        object.__setattr__(instance, "execution_asset_set_id", execution_asset_set_id)
        object.__setattr__(instance, "_analysis_context", analysis_context)
        object.__setattr__(instance, "analysis_context_digest", analysis_context_digest)
        return instance

    def record(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(self.canonical_bytes))

    def analysis_context(self) -> RetainedNextAnalysisContextV2:
        return self._analysis_context


def build_request_frame_v2(
    seal: SourceAcquisitionSeal,
    assets: RetainedExecutionAssets,
    analysis_context: RetainedNextAnalysisContextV2,
) -> RetainedRequestFrameV2:
    """Reference projection from retained owners; never reopen target/package files."""

    validate_next_analysis_context_v2(analysis_context, seal, assets)
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
        "targets": analysis_context.analysis_intent()["targets"],
        "limits": plan["limits"],
        "run_context": analysis_context.run_context(),
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
        analysis_context=analysis_context,
        analysis_context_digest=digest(
            {
                "domain_config_digest": analysis_context.domain_config()["domain_config_digest"],
                "run_context": analysis_context.run_context(),
                "source_seal_id": seal.seal_id,
                "execution_asset_set_id": assets.descriptor()["asset_set_id"],
            }
        ),
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


@dataclass(frozen=True, slots=True, init=False)
class RetainedObservedResponseReceiptV2:
    """Live-validated metadata, never retained response bytes or semantic authority."""

    _request: RetainedRequestFrameV2 = field(repr=False)
    _observation_bytes: bytes = field(repr=False)
    _descriptor_bytes: bytes = field(repr=False)

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("response receipts are created by retain_runtime_result_v2")

    def request_frame(self) -> RetainedRequestFrameV2:
        return self._request

    def control(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(self._observation_bytes)["response"]["control"])

    def descriptor(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(self._descriptor_bytes))


def _retain_observed_response_receipt_v2(
    request: RetainedRequestFrameV2,
    observation_snapshot: bytes,
    frame: RetainedResponseFrameV2,
) -> RetainedObservedResponseReceiptV2:
    receipt = object.__new__(RetainedObservedResponseReceiptV2)
    object.__setattr__(receipt, "_request", request)
    object.__setattr__(receipt, "_observation_bytes", observation_snapshot)
    object.__setattr__(
        receipt,
        "_descriptor_bytes",
        canonical_json_bytes(
            {
                "raw_sha256": hashlib.sha256(frame.raw_bytes).hexdigest(),
                "byte_length": len(frame.raw_bytes),
                "canonical_json": frame.raw_bytes
                == canonical_json_bytes(json.loads(frame.raw_bytes)),
            }
        ),
    )
    return receipt


@dataclass(frozen=True, slots=True, init=False)
class RetainedRuntimeResultV2:
    """Private data-only result, with no raw failure buffers or semantic certificate."""

    _seal: SourceAcquisitionSeal = field(repr=False)
    _assets: RetainedExecutionAssets = field(repr=False)
    _request: RetainedRequestFrameV2 = field(repr=False)
    _policy_bytes: bytes = field(repr=False)
    _observation_bytes: bytes = field(repr=False)
    _response_receipt: RetainedObservedResponseReceiptV2 | None = field(repr=False)
    _candidate: ValidatedTransportCandidateV2 | None = field(repr=False)
    _rejected_frame: RejectedResponseFrameV2 | None = field(repr=False)

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("runtime results are created by retain_runtime_result_v2")

    @classmethod
    def _from_joined_observations(
        cls,
        seal: SourceAcquisitionSeal,
        assets: RetainedExecutionAssets,
        request: RetainedRequestFrameV2,
        policy_snapshot: bytes,
        observation_snapshot: bytes,
        receipt: RetainedObservedResponseReceiptV2 | None,
        candidate: ValidatedTransportCandidateV2 | None,
        rejected_frame: RejectedResponseFrameV2 | None = None,
    ) -> "RetainedRuntimeResultV2":
        instance = object.__new__(cls)
        for owner_name, owner in (("_seal", seal), ("_assets", assets), ("_request", request)):
            object.__setattr__(instance, owner_name, owner)
        object.__setattr__(instance, "_policy_bytes", policy_snapshot)
        object.__setattr__(instance, "_observation_bytes", observation_snapshot)
        object.__setattr__(instance, "_response_receipt", receipt)
        object.__setattr__(instance, "_candidate", candidate)
        object.__setattr__(instance, "_rejected_frame", rejected_frame)
        return instance

    @property
    def result_kind(self) -> str:
        observation = self.observation()
        if observation["terminal_cause"] == "interrupted":
            return "interrupted"
        if observation["terminal_cause"] != "none":
            return "transport_failure"
        return cast(str, observation["response"]["control"]["result_kind"])

    def observation(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(self._observation_bytes))

    def control(self) -> dict[str, Any] | None:
        response = self.observation()["response"]
        return None if response is None else cast(dict[str, Any], response["control"])

    def response_descriptor(self) -> dict[str, Any] | None:
        return None if self._response_receipt is None else self._response_receipt.descriptor()

    def observed_response_receipt(self) -> RetainedObservedResponseReceiptV2 | None:
        return self._response_receipt

    def frame_rejection(self) -> dict[str, Any] | None:
        return None if self._rejected_frame is None else self._rejected_frame.failure()

    def transport_candidate(self) -> ValidatedTransportCandidateV2 | None:
        return self._candidate

    def source_seal(self) -> SourceAcquisitionSeal:
        return self._seal

    def execution_assets(self) -> RetainedExecutionAssets:
        return self._assets

    def request_frame(self) -> RetainedRequestFrameV2:
        return self._request

    def policy(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(self._policy_bytes))


def retain_runtime_result_v2(
    seal: SourceAcquisitionSeal,
    assets: RetainedExecutionAssets,
    request: RetainedRequestFrameV2,
    policy: dict[str, Any],
    observation: dict[str, Any],
    response: RetainedResponseFrameV2 | RejectedResponseFrameV2 | None,
) -> RetainedRuntimeResultV2:
    """Preserve a joined closed result, not a success default for child failures."""

    policy_snapshot = json.dumps(
        policy, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    observation_snapshot = json.dumps(
        observation, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    policy, observation = json.loads(policy_snapshot), json.loads(observation_snapshot)
    validate_observation_request_v2(observation, policy, request, seal, assets)
    if response is not None and type(response) not in {
        RetainedResponseFrameV2,
        RejectedResponseFrameV2,
    }:
        raise TypeError("runtime response requires a retained frame owner")
    rejected = response if isinstance(response, RejectedResponseFrameV2) else None
    frame = response if isinstance(response, RetainedResponseFrameV2) else None
    if observation["terminal_cause"] == "frame_invalid":
        validate_rejected_frame_observation_v2(observation, policy, rejected)
    elif rejected is not None:
        raise ValueError("rejected frame requires the actual frame-invalid cause")
    if observation["terminal_cause"] == "binding_mismatch" and not (
        observation["response"] is not None
        and observation["response"]["control"]["binding"]["state"] == "bound"
        and observation["response"]["control"]["binding"]["request_id"] != request.request_id
    ):
        raise ValueError("binding mismatch requires an actual foreign control binding")
    receipt = None
    if observation["response"] is None:
        if observation["terminal_cause"] == "response_invalid":
            raise ValueError("response mismatch requires a complete joined frame")
        if frame is not None:
            raise ValueError("runtime result cannot attach an unobserved response frame")
    else:
        if frame is None:
            raise ValueError("runtime control requires the retained complete frame")
        validate_response_frame_observation_v2(observation, policy, frame)
        if observation["terminal_cause"] == "none":
            validate_response_request_v2(frame, request, seal, assets)
        receipt = _retain_observed_response_receipt_v2(request, observation_snapshot, frame)
        validate_observed_response_receipt_before_disposal_v2(
            receipt,
            frame,
            request=request,
            observation_snapshot=observation_snapshot,
            policy=policy,
            seal=seal,
            assets=assets,
        )
    candidate = (
        retain_transport_candidate_v2(seal, assets, request, policy, observation, frame)
        if observation["transport_payload_admissible"] and frame is not None
        else None
    )
    result = RetainedRuntimeResultV2._from_joined_observations(
        seal, assets, request, policy_snapshot, observation_snapshot, receipt, candidate, rejected
    )
    validate_runtime_result_v2(result)
    return result


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


PROVENANCE_SLOTS_V2 = (
    "applicability",
    "config",
    "source",
    "limits",
    "source_plan",
    "trusted_environment",
    "runtime_bundle",
    "node_candidate",
    "request",
    "launch_policy",
    "process_start",
    "node_version",
    "control_response",
    "semantic_payload",
    "compatibility",
    "model",
    "budget",
)


def portable_launch_value_v2(policy: dict[str, Any]) -> dict[str, Any]:
    """Observation preimage only, not a policy-schema alias or runtime fingerprint."""

    validate_process_launch_policy_v2(policy)
    return {
        "producer": policy["producer"],
        "node_candidate": {"sha256": policy["node_candidate"]["sha256"]},
        **{
            key: deepcopy(policy[key])
            for key in (
                "runtime_requirement",
                "execution_asset_set_id",
                "adapter",
                "typescript_identity",
                "trusted_environment_digest",
                "shell",
                "passed_environment",
                "stdio",
                "fd_inheritance",
                "process_group",
                "limits",
            )
        },
        "argv": [
            {"kind": "node_candidate", "sha256": policy["node_candidate"]["sha256"]},
            policy["argv"][1],
            {"kind": "execution_member", "package_path": policy["adapter"]["entrypoint_member"]},
        ],
        "cwd": {"kind": "empty_private_directory"},
    }


def runtime_provenance_values_v2(
    result: RetainedRuntimeResultV2,
    semantic_decision: ValidatedSemanticDecisionV2 | RejectedSemanticDecisionV2 | None = None,
) -> dict[str, Any]:
    """Actual retained inputs, with a portable projection of host-local observations."""

    if type(result) is not RetainedRuntimeResultV2:
        raise TypeError("runtime provenance requires the retained runtime result owner")
    validate_runtime_result_v2(result)
    seal, assets, request = result.source_seal(), result.execution_assets(), result.request_frame()
    policy, observation = result.policy(), result.observation()
    validate_observation_request_v2(observation, policy, request, seal, assets)
    plan, control = seal.final_plan, result.control()
    portable_policy = portable_launch_value_v2(policy)
    values = {
        "applicability": seal.package_applicability.observation_value(),
        "config": plan["projects"],
        "source": seal.source_view.fingerprint_value(),
        "limits": plan["limits"],
        "source_plan": plan,
        # This is the expected read-only descriptor, never evidence of a TS import.
        "trusted_environment": trusted_environment_manifest_v2(assets)["environment_descriptor"],
        "runtime_bundle": assets.descriptor(),
        "node_candidate": {"sha256": policy["node_candidate"]["sha256"]},
        "request": request.record(),
        "launch_policy": portable_policy,
        "process_start": None
        if observation["spawn"] is None
        else {
            "primitive": observation["spawn"]["primitive"],
            "parameters": {key: portable_policy[key] for key in observation["spawn"]["parameters"]},
        },
        "node_version": None if control is None else control["runtime"],
        "control_response": None
        if control is None
        else {"control": control, "response": result.response_descriptor()},
        "semantic_payload": None,
        "compatibility": None,
        "model": None,
        "budget": None,
    }
    if semantic_decision is not None:
        if isinstance(semantic_decision, RejectedSemanticDecisionV2):
            validate_rejected_semantic_decision_v2(semantic_decision)
        else:
            validate_semantic_decision_v2(semantic_decision)
        if (
            semantic_decision.transport_candidate() is not result.transport_candidate()
            or semantic_decision.source_seal() is not seal
            or semantic_decision.execution_assets() is not assets
        ):
            raise ValueError("provenance Core decision is not joined to the same runtime owner")
        if isinstance(semantic_decision, ValidatedSemanticDecisionV2):
            payload = semantic_decision.transport_candidate().semantic_payload()
            gate = semantic_decision.gate()
            values.update(
                semantic_payload=payload,
                compatibility=semantic_decision.compatibility_descriptor(),
                model=payload["model"],
                budget=gate if gate["actual"] is not None else None,
            )
    return values


def provenance_observation_v2(field_name: str, value: Any) -> dict[str, Any]:
    """Digest a closed named observation value, not a field-name success marker."""

    if field_name not in PROVENANCE_SLOTS_V2:
        raise ValueError("unknown provenance observation field")
    if value is None:
        return {"state": "unobserved", "value": None}
    return {
        "state": "observed",
        "value": {
            "schema": "code-structure-viz.next-observation/v2",
            "version": 2,
            "sha256": digest(
                {
                    "schema": "code-structure-viz.next-observation/v2",
                    "version": 2,
                    "field": field_name,
                    "value": value,
                }
            ),
        },
    }


def runtime_provenance_v2(
    result: RetainedRuntimeResultV2,
    *,
    semantic_decision: ValidatedSemanticDecisionV2 | RejectedSemanticDecisionV2 | None = None,
) -> dict[str, Any]:
    """Reference prefix; failure rows do not admit a semantic model or proof."""

    values = runtime_provenance_values_v2(result, semantic_decision)
    if result.result_kind == "interrupted":
        raise ValueError("terminal interrupt requires the core interrupted/exit-130 branch")
    stage: str | None
    code: str | None
    if result.result_kind == "unsupported_runtime":
        kind, stage, code = "request_bound_failure", "runtime_validation", "CSV-NEXT-NODE-001"
    elif result.result_kind in {"protocol_failure", "bootstrap_failure", "semantic_failure"}:
        stage, code = {
            "protocol_failure": ("response_protocol", "CSV-NEXT-PROTOCOL-001"),
            "bootstrap_failure": ("bootstrap", "CSV-NEXT-NODE-004"),
            "semantic_failure": ("semantic_analysis", "CSV-NEXT-NODE-004"),
        }[result.result_kind]
        kind = "request_bound_failure"
    elif result.result_kind == "transport_failure":
        failure = {
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
            failure = rejection["stage"], rejection["diagnostic_code"]
        if failure is None:
            raise ValueError("runtime result has no closed provenance branch yet")
        kind, (stage, code) = "request_bound_failure", failure
    elif result.result_kind == "success" and isinstance(
        semantic_decision, RejectedSemanticDecisionV2
    ):
        core_failure = semantic_decision.failure()
        kind, stage, code = (
            "request_bound_failure",
            core_failure["stage"],
            core_failure["diagnostic_code"],
        )
    elif result.result_kind == "success" and isinstance(
        semantic_decision, ValidatedSemanticDecisionV2
    ):
        gate = semantic_decision.gate()
        if gate["outcome"] == "payload_unavailable":
            code = gate["diagnostic_code"]
            stage = {
                "CSV-NEXT-TARGET-001": "target_resolution",
                "CSV-NEXT-EXPORT-001": "response_validation",
                "CSV-NEXT-LIMIT-005": "model_validation",
            }[code]
            kind = "request_bound_failure"
        else:
            kind, stage, code = "request_bound_success", None, None
    else:
        raise ValueError("runtime result has no closed provenance branch yet")
    return {
        "schema": "code-structure-viz.next-provenance/v2",
        "kind": kind,
        "stage": stage,
        "failure_code": code,
        "observed": {key: provenance_observation_v2(key, value) for key, value in values.items()},
    }
