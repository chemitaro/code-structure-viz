"""Known reference corpus with real source seal; never an actual compiler claim."""

import hashlib
import json
import os
from contextlib import suppress
from pathlib import Path, PurePosixPath
from typing import Any, Literal

from code_structure_viz.adapters.next.source_acquisition import (
    SourceAcquisitionSeal,
    SourceDiscoveryIntent,
    seal_source_acquisition,
)
from code_structure_viz.source.git_repository import Commit, EnumeratedPath
from code_structure_viz.source.source_view import DescriptorAnchoredSourceReadSession
from tests.contracts import next_runtime_v2_reference as runtime_reference
from tests.contracts.next_run_decision_v2_reference import (
    RetainedRequestBoundRunDecisionV2,
    retain_request_bound_run_decision_v2,
)
from tests.contracts.test_next_core_failure_v2 import runtime_for_core_wire
from tests.contracts.test_next_exchange_v2 import exchange_evidence, shape_wire
from tests.contracts.test_next_process_observation_v2 import policy_fixture
from tests.contracts.test_next_public_semantic_v2 import CARD_COMPONENT_ID
from tests.contracts.test_next_request_frame_v2 import run_context
from tests.contracts.test_next_semantic_candidate_v2 import (
    CARD_MODULE_ID,
    COLLECTIONS,
    core_inputs,
    update_model_digest,
)
from tests.contracts.test_next_trusted_environment_v2 import profile_members


def known_run_with_formats(
    tmp_path: Path,
    formats: list[str],
    *,
    selector: str | None = None,
    empty_membership: bool = False,
    partial_safe: bool = False,
) -> RetainedRequestBoundRunDecisionV2:
    seal, assets, original_request, policy, wire = core_inputs(
        tmp_path, empty_membership=empty_membership
    )
    original_context = original_request.analysis_context()
    context = runtime_reference.retain_next_analysis_context_v2(
        seal,
        assets,
        targets=[],
        upstream_depth=0,
        downstream_depth=0,
        run_context={
            **original_context.run_context(),
            "requested_formats": formats,
            "stdout_selector": selector,
        },
    )
    request = runtime_reference.build_request_frame_v2(seal, assets, context)
    policy["request_id"] = request.request_id
    wire["control"]["binding"]["request_id"] = request.request_id
    wire["semantic_payload"]["run_context"] = request.record()["run_context"]
    if partial_safe:
        model, proof = wire["semantic_payload"]["model"], wire["semantic_payload"]["proof"]
        failure_id = "next:failure:" + "1" * 64
        proof["discovered_records"].append(
            {
                "collection": "components",
                "record_id": CARD_COMPONENT_ID,
                "taints": ["type_symbol"],
                "record": {
                    "kind": "component",
                    "id": CARD_COMPONENT_ID,
                    "module_id": CARD_MODULE_ID,
                    "declaration_key": "Card",
                    "recognition_evidence": ["trusted_callable"],
                    "props_state": "no_props",
                },
            }
        )
        proof["failure_roots"] = [
            {
                "id": failure_id,
                "collection": "components",
                "kind": "type_symbol",
                "path_ref": None,
                "record_ids": [CARD_COMPONENT_ID],
            }
        ]
        proof["causal_edges"] = [
            {"source_id": failure_id, "record_id": CARD_COMPONENT_ID, "rule": "type_subtree"}
        ]
        proof["excluded"] = [
            {"collection": "components", "record_id": CARD_COMPONENT_ID, "reason": "tainted"}
        ]
        model["coverage"].update(affected_ids=[CARD_COMPONENT_ID], taint_frontier=[CARD_MODULE_ID])
        model["coverage"]["counts"].update(discovered=8, excluded=1)
        model["diagnostics"] = [
            {
                "code": "CSV-NEXT-TYPE-001",
                "severity": "warning",
                "recoverable": True,
                "outcome": "partial_safe",
                "ref_permission": "symbol",
                "path_ref": None,
                "symbol_ref": CARD_COMPONENT_ID,
                "count": 1,
            }
        ]
        update_model_digest(wire)
    response = runtime_reference.retain_response_frame_v2(
        json.dumps(wire).encode(), limits=request.record()["limits"]
    )
    observation = runtime_reference.reference_process_observation_v2(
        policy, exchange_evidence(policy, request, response)
    )
    runtime = runtime_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, response
    )
    candidate = runtime.transport_candidate()
    assert candidate is not None
    core = runtime_reference.decide_semantic_candidate_v2(candidate, seal, assets)
    return retain_request_bound_run_decision_v2(runtime, semantic_decision=core)


def independent_ascii_bytes(value: object) -> bytes:
    """Test-side ASCII codec, not the candidate producer or its expected builder."""

    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def independent_record_id(kind: str, identity: dict[str, Any], prefix: str) -> str:
    preimage = {"kind": kind, "version": 1, "identity": identity}
    return f"next:{prefix}:" + hashlib.sha256(independent_ascii_bytes(preimage)).hexdigest()


def _long_prefix(length: int) -> str:
    parts = ["src"]
    remaining = length - 3
    while remaining:
        if remaining == 1:
            parts[-1] += "d"
            break
        size = min(200, remaining - 1)
        parts.append("d" * size)
        remaining -= size + 1
    result = "/".join(parts)
    assert len(result) == length and all(len(part) <= 201 for part in parts)
    return result


def _long_case_inputs(
    tmp_path: Path, *, prefix_length: int, longer_names: int = 0, context_digits: int = 2
) -> tuple[
    SourceAcquisitionSeal,
    runtime_reference.RetainedExecutionAssets,
    runtime_reference.RetainedRequestFrameV2,
    dict[str, Any],
    dict[str, Any],
    bytes,
]:
    """Real descriptor-relative files/seal and 1000 source-bound known Card modules.

    Paths above the host's full-path syscall limit are created component-by-component.
    No fake seal, metadata-only file, appended padding or compiler execution is used.
    """

    assets = runtime_reference.retain_execution_assets_v1(profile_members())
    trusted = runtime_reference.trusted_environment_manifest_v2(assets)["environment_descriptor"][
        "sha256"
    ]
    repository = tmp_path / "repo"
    repository.mkdir(parents=True)
    prefix = _long_prefix(prefix_length)
    paths = [
        f"{prefix}/n{index:04d}{'x' if index < longer_names else ''}/src/Card.tsx"
        for index in range(1000)
    ]
    assert all(len(path.encode()) <= 4096 for path in paths)
    # The unchanged export-census oracle requires actual known Card bytes under a
    # rebased /src/Card.tsx suffix. Context declarations are not program Modules.
    # An actual valid .d.ts comment varies its real file length across decimal digit
    # boundaries; no bytes are appended to a candidate or injected into an owner.
    context_size = {2: 99, 3: 100, 4: 1000, 5: 10_000}[context_digits]
    context_prefix = b"declare interface Window { marker: string; }\n/*"
    context_content = context_prefix + b"x" * (context_size - len(context_prefix) - 3) + b"*/\n"
    assert len(context_content) == context_size
    files = {
        "package.json": b'{"dependencies":{"next":"15"}}',
        "tsconfig.json": b'{"include":["src/**/*"]}',
        "src/global.d.ts": context_content,
    }
    for path, content in files.items():
        location = repository / path
        location.parent.mkdir(parents=True, exist_ok=True)
        location.write_bytes(content)
    directory_fd = os.open(repository, os.O_RDONLY | os.O_DIRECTORY)
    try:
        for component in prefix.split("/"):
            with suppress(FileExistsError):
                os.mkdir(component, dir_fd=directory_fd)
            child_fd = os.open(component, os.O_RDONLY | os.O_DIRECTORY, dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = child_fd
        for path in paths:
            content = b"const Card = 1;\n"
            owner_name = PurePosixPath(path).parts[-3]
            os.mkdir(owner_name, dir_fd=directory_fd)
            owner_fd = os.open(owner_name, os.O_RDONLY | os.O_DIRECTORY, dir_fd=directory_fd)
            try:
                os.mkdir("src", dir_fd=owner_fd)
                program_fd = os.open("src", os.O_RDONLY | os.O_DIRECTORY, dir_fd=owner_fd)
                try:
                    fd = os.open(
                        "Card.tsx", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=program_fd
                    )
                    with os.fdopen(fd, "wb") as output:
                        output.write(content)
                finally:
                    os.close(program_fd)
            finally:
                os.close(owner_fd)
            files[path] = content
    finally:
        os.close(directory_fd)
    entries = tuple(EnumeratedPath(path, PurePosixPath(path)) for path in sorted(files))
    head = Commit("1" * 40)
    reader = DescriptorAnchoredSourceReadSession(
        repository,
        entries,
        head_state=head,
        current_entries=lambda: entries,
        current_head_state=lambda: head,
        max_files=20_000,
        max_file_bytes=4 * 1024 * 1024,
        max_total_bytes=64 * 1024 * 1024,
    )
    seal = seal_source_acquisition(
        SourceDiscoveryIntent((".",)), reader, trusted_environment_digest=trusted, max_entities=1000
    )
    assert isinstance(seal, SourceAcquisitionSeal)
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
        },
    )
    request = runtime_reference.build_request_frame_v2(seal, assets, context)
    request_record = request.record()
    policy = policy_fixture()
    policy.update(
        request_id=request.request_id,
        adapter=assets.adapter_identity(),
        execution_asset_set_id=assets.descriptor()["asset_set_id"],
        trusted_environment_digest=trusted,
        limits=request_record["limits"],
    )
    wire = shape_wire(request)
    model = wire["semantic_payload"]["model"]
    model["projects"] = request_record["projects"]
    model["files"] = [
        {key: value for key, value in row.items() if key != "content_base64"}
        for row in request_record["files"]
    ]
    project_id = model["projects"][0]["id"]
    modules = [
        {
            "kind": "module",
            "project_id": project_id,
            "path": path,
            "id": independent_record_id(
                "module", {"project_id": project_id, "path": path}, "module"
            ),
            "client_entry": False,
            "router_context": "none",
            "derived_roles": [],
        }
        for path in paths
    ]
    model["modules"] = sorted(modules, key=lambda row: row["id"])
    model["facts"] = sorted(
        [
            {
                "kind": "router_context",
                "owner_id": row["id"],
                "value": "none",
                "id": independent_record_id(
                    "router_context",
                    {"kind": "router_context", "owner_id": row["id"], "value": "none"},
                    "fact",
                ),
            }
            for row in modules
        ],
        key=lambda row: row["id"],
    )
    counts = {name: len(model[name]) for name in COLLECTIONS}
    model["coverage"]["counts"].update(
        **counts,
        internal_entities=1000,
        published=sum(counts.values()),
        discovered=sum(counts.values()),
    )
    wire["semantic_payload"]["proof"]["discovered_records"] = [
        {"collection": name, "record_id": row["id"], "taints": []}
        for name in COLLECTIONS
        for row in model[name]
    ]
    update_model_digest(wire)
    # Independent expected record: explicit source/config/model fields plus the existing
    # fixed compatibility literal for the unchanged assets/Node observation. Never render.
    root = Path(__file__).resolve().parents[2]
    expected = json.loads(
        (root / "tests/fixtures/next_runtime_v2/public-semantic.json").read_text()
    )
    config = context.domain_config()
    preimage = {
        "source_view_fingerprint": seal.source_view.fingerprint,
        "source_plan_digest": seal.plan_digest,
        "domain_config_digest": config["domain_config_digest"],
        "projects": request_record["projects"],
        "targets": [],
        "formats": ["semantic-json"],
        "stdout_selector": None,
        "limits": request_record["limits"],
        "node_version": "22.10.0",
        "typescript_version": "5.9.2",
        "adapter_version": request_record["adapter_version"],
        "protocol": request_record["protocol"],
        "trusted_environment_digest": trusted,
    }
    expected["source"] = {
        "schema": seal.source_view.schema,
        "kind": seal.source_view.kind,
        "head_commit": seal.source_view.head_commit,
        "fingerprint": seal.source_view.fingerprint,
        "file_count": len(seal.source_view.files),
    }
    expected["request"] = {
        "schema": "code-structure-viz.next-snapshot-request/v1",
        **{
            key: config[key]
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
            )
        },
        "run_fingerprint": hashlib.sha256(independent_ascii_bytes(preimage)).hexdigest(),
    }
    for name in ("projects", "files", "members", "relations", "facts", "coverage", "diagnostics"):
        expected[name] = model[name]
    expected["entities"] = sorted(model["modules"] + model["components"], key=lambda row: row["id"])
    return seal, assets, request, policy, wire, independent_ascii_bytes(expected) + b"\n"


def available_large_json_run(
    tmp_path: Path, target_bytes: int
) -> tuple[RetainedRequestBoundRunDecisionV2, bytes]:
    """Tune legitimate paths and actual context file size, not artifact padding.

    Only final inputs are admitted through response/runtime/Core/run owners. The first
    fresh seal/request calibrates an independently spelled expected JSON length.
    """

    assert target_bytes in {16 * 1024 * 1024, 16 * 1024 * 1024 + 1}
    initial_prefix = 3800
    *_calibration, expected = _long_case_inputs(
        tmp_path / "calibration", prefix_length=initial_prefix
    )
    path_delta, context_delta = divmod(target_bytes - len(expected), 4)
    prefix_delta, longer_names = divmod(path_delta, 1000)
    seal, assets, request, policy, wire, expected = _long_case_inputs(
        tmp_path / "final",
        prefix_length=initial_prefix + prefix_delta,
        longer_names=longer_names,
        context_digits=2 + context_delta,
    )
    assert len(expected) == target_bytes
    raw = independent_ascii_bytes(wire)
    assert len(raw) <= request.record()["limits"]["max_adapter_response_bytes"]
    response = runtime_reference.retain_response_frame_v2(raw, limits=request.record()["limits"])
    observation = runtime_reference.reference_process_observation_v2(
        policy, exchange_evidence(policy, request, response)
    )
    runtime = runtime_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, response
    )
    candidate = runtime.transport_candidate()
    assert candidate is not None
    core = runtime_reference.decide_semantic_candidate_v2(candidate, seal, assets)
    assert core.gate()["payload_available"] is True and core.gate()["actual"] == 1000
    return retain_request_bound_run_decision_v2(runtime, semantic_decision=core), expected


def unavailable_core_run(
    tmp_path: Path, branch: Literal["target", "export", "entity", "rejected"]
) -> RetainedRequestBoundRunDecisionV2:
    """Known lower-gate conformance inputs, not real TS recognition or error injection."""

    seal, assets, request, policy, wire = core_inputs(
        tmp_path,
        targets=["path:src/Card.tsx"] if branch == "target" else None,
        corpus="string-unknown" if branch == "export" else "card",
        max_entities=1 if branch == "entity" else 500,
    )
    model, proof = wire["semantic_payload"]["model"], wire["semantic_payload"]["proof"]
    if branch == "target":
        model["modules"], model["facts"] = [], []
        model["coverage"]["counts"].update(
            modules=0, facts=0, internal_entities=0, published=5, discovered=5
        )
        resolution = {
            "target_key": "path:src/Card.tsx",
            "status": "failed",
            "record_ids": [],
            "reason": "missing",
        }
        proof["target_resolutions"] = [resolution]
        model["coverage"]["target_completeness"] = [resolution]
    elif branch == "entity":
        model["components"] = [
            {
                "kind": "component",
                "id": CARD_COMPONENT_ID,
                "module_id": CARD_MODULE_ID,
                "declaration_key": "Card",
                "recognition_evidence": ["trusted_callable"],
                "props_state": "no_props",
            }
        ]
        model["coverage"]["counts"].update(
            components=1, internal_entities=2, published=8, discovered=8
        )
    if branch in {"target", "entity"}:
        proof["discovered_records"] = [
            {"collection": name, "record_id": row["id"], "taints": []}
            for name in COLLECTIONS
            for row in model[name]
        ]
        update_model_digest(wire)
    if branch == "rejected":
        wire["semantic_payload"]["model_digest"] = "0" * 64
    runtime = runtime_for_core_wire(seal, assets, request, policy, wire)
    candidate = runtime.transport_candidate()
    assert candidate is not None
    core = runtime_reference.inspect_semantic_candidate_v2(candidate, seal, assets)
    return retain_request_bound_run_decision_v2(runtime, semantic_decision=core)
