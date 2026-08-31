import base64
import copy
import hashlib
import json
from itertools import combinations
from typing import Any, cast

import pytest
from jsonschema import ValidationError  # type: ignore[import-untyped]

from code_structure_viz.artifacts.streams import StdoutEmitter
from code_structure_viz.cli.parser import DomainFormatSelector, ManifestSelector
from code_structure_viz.core.outcomes import RunOutcome
from tests.contracts.next_reference_validation import (
    COLLECTIONS,
    LIMIT_CONTRACTS,
    ROLE_ORDER,
    ROLE_PRECEDENCE,
    RUNTIME_PHYSICAL_TO_VIRTUAL,
    RUNTIME_REQUIRED_PATHS,
    TRUSTED_PROFILE_CERTIFIED_SYMBOLS,
    TRUSTED_PROFILE_FILE_LICENSES,
    TRUSTED_PROFILE_FILE_SHA256,
    TRUSTED_PROFILE_FILE_SIZES,
    TRUSTED_PROFILE_LICENSE_DIGEST,
    TRUSTED_PROFILE_LICENSES,
    TRUSTED_PROFILE_PHYSICAL_TO_VIRTUAL,
    TRUSTED_PROFILE_SHADOWING_WITNESS,
    VALIDATOR_SCHEMA,
    _derived_taint_fixed_point,
    _scan_export_file,
    assert_encoded_stdin_boundary,
    assert_limit_boundary,
    bounded_decode_json,
    canonical_json_bytes,
    canonical_target_key,
    capture_adapter_stderr,
    count_array_items_before_materialization,
    derive_required_causal_edges,
    digest,
    encoded_request_bytes,
    entity_budget_allowed,
    entity_budget_gate,
    expected_export_observations,
    expected_export_reexport_witness,
    expected_export_resolution_witness,
    internal_entity_count,
    load_export_census_fixture,
    load_export_graph_cases,
    load_export_graph_fixture,
    load_export_graph_raw_fixture,
    model_record_budget_allowed,
    project_config_digest,
    recompute_compatibility_id,
    recompute_export_graph_case,
    recompute_record_id,
    recompute_request_id,
    recompute_run_fingerprint,
    render_plantuml,
    render_public_diagnostic_stderr,
    resolve_target_resolutions,
    scan_export_syntax_census,
    source_plan_descriptor,
    validate_compatibility_descriptor,
    validate_domain_manifest,
    validate_encoded_stdin_size,
    validate_limits,
    validate_limits_consistency,
    validate_model,
    validate_no_trusted_shadowing,
    validate_plantuml_contract,
    validate_proof,
    validate_request_envelope,
    validate_request_files,
    validate_response_envelope,
    validate_run_manifest,
    validate_run_status_vector,
    validate_runtime_manifest,
    validate_semantic_snapshot,
    validate_trusted_environment,
)
from tests.contracts.next_reference_validation import (
    source_plan_digest as recompute_source_plan_digest,
)
from tests.contracts.test_json_schemas import (
    ROOT,
    _next_compatibility_descriptor,
    _next_coverage,
    _next_limits,
    _next_project,
    _next_trusted_environment,
    _schema,
    _validator,
)


def _id(kind: str, digit: str) -> str:
    def raw(record_kind: str, identity: dict[str, Any]) -> str:
        preimage = {"kind": record_kind, "version": 1, "identity": identity}
        return f"next:{record_kind}:{digest(preimage)}"

    project_id = "next:project:" + digest(
        {"kind": "project", "version": 1, "identity": {"root": "."}}
    )
    known: dict[tuple[str, str], dict[str, Any]] = {
        ("project", "0"): {"root": "."},
        ("file", "1"): {"project_id": project_id, "path": "src/Button.tsx"},
        ("file", "2"): {"project_id": project_id, "path": "src/Card.tsx"},
        ("file", "c"): {"project_id": project_id, "path": "src/types.d.ts"},
        ("file", "e"): {"project_id": project_id, "path": "src/Unused.tsx"},
        ("file", "p"): {"project_id": project_id, "path": "package.json"},
        ("file", "t"): {"project_id": project_id, "path": "tsconfig.json"},
        ("file", "j"): {"project_id": project_id, "path": "jsconfig.json"},
        ("module", "3"): {"project_id": project_id, "path": "src/Button.tsx"},
        ("module", "4"): {"project_id": project_id, "path": "src/Card.tsx"},
        ("module", "f"): {"project_id": project_id, "path": "src/Unused.tsx"},
        (
            "component",
            "5",
        ): {
            "module_id": raw("module", {"project_id": project_id, "path": "src/Button.tsx"}),
            "declaration_key": "Button",
        },
        (
            "component",
            "6",
        ): {
            "module_id": raw("module", {"project_id": project_id, "path": "src/Card.tsx"}),
            "declaration_key": "Card",
        },
        (
            "member",
            "7",
        ): {
            "owner_id": raw("module", {"project_id": project_id, "path": "src/Button.tsx"}),
            "exported_name": "default",
            "role": "value",
        },
        (
            "member",
            "8",
        ): {
            "owner_id": raw("module", {"project_id": project_id, "path": "src/Button.tsx"}),
            "imported_name": "Card",
            "role": "value",
            "source": {
                "kind": "internal",
                "module_id": raw("module", {"project_id": project_id, "path": "src/Card.tsx"}),
            },
        },
        (
            "member",
            "9",
        ): {
            "owner_id": raw(
                "component",
                {
                    "module_id": raw(
                        "module", {"project_id": project_id, "path": "src/Button.tsx"}
                    ),
                    "declaration_key": "Button",
                },
            ),
            "name": "props",
        },
        (
            "relation",
            "a",
        ): {
            "kind": "static_import",
            "source_id": raw("module", {"project_id": project_id, "path": "src/Button.tsx"}),
            "target": {
                "kind": "internal",
                "module_id": raw("module", {"project_id": project_id, "path": "src/Card.tsx"}),
            },
            "role": "value",
            "reexport": False,
            "boundary_effect": "none",
        },
        (
            "relation",
            "b",
        ): {
            "kind": "jsx_render",
            "source_id": raw(
                "component",
                {
                    "module_id": raw(
                        "module", {"project_id": project_id, "path": "src/Button.tsx"}
                    ),
                    "declaration_key": "Button",
                },
            ),
            "target": {
                "kind": "internal",
                "component_id": raw(
                    "component",
                    {
                        "module_id": raw(
                            "module", {"project_id": project_id, "path": "src/Card.tsx"}
                        ),
                        "declaration_key": "Card",
                    },
                ),
            },
        },
        (
            "relation",
            "c",
        ): {
            "kind": "component_wrap",
            "source_id": raw(
                "component",
                {
                    "module_id": raw("module", {"project_id": project_id, "path": "src/Card.tsx"}),
                    "declaration_key": "Card",
                },
            ),
            "target_component_id": raw(
                "component",
                {
                    "module_id": raw(
                        "module", {"project_id": project_id, "path": "src/Button.tsx"}
                    ),
                    "declaration_key": "Button",
                },
            ),
        },
        (
            "relation",
            "1",
        ): {
            "kind": "literal_dynamic_import",
            "source_id": raw("module", {"project_id": project_id, "path": "src/Button.tsx"}),
            "target": {
                "kind": "external",
                "safe_specifier": "react",
                "exported_name": "lazy",
            },
            "role": "value",
            "reexport": False,
            "boundary_effect": "none",
        },
        ("fact", "d"): {
            "kind": "client_entry",
            "owner_id": raw("module", {"project_id": project_id, "path": "src/Button.tsx"}),
            "value": True,
        },
        (
            "fact",
            "e",
        ): {
            "kind": "router_context",
            "owner_id": raw("module", {"project_id": project_id, "path": "src/Button.tsx"}),
            "value": "app_ui",
        },
        (
            "fact",
            "f",
        ): {
            "kind": "router_context",
            "owner_id": raw("module", {"project_id": project_id, "path": "src/Card.tsx"}),
            "value": "none",
        },
    }
    identity = known.get((kind, digit))
    if identity is None:
        fallback = digest({"kind": kind, "fixture": digit})
        return f"next:{kind}:{fallback}"
    if kind in {"static_import", "literal_dynamic_import", "jsx_render", "component_wrap"}:
        identity = {**identity}
    semantic_kind = {
        ("member", "7"): "export_binding",
        ("member", "8"): "import_binding",
        ("member", "9"): "prop",
        ("relation", "a"): "static_import",
        ("relation", "1"): "literal_dynamic_import",
        ("relation", "b"): "jsx_render",
        ("relation", "c"): "component_wrap",
        ("fact", "d"): "client_entry",
        ("fact", "e"): "router_context",
        ("fact", "f"): "router_context",
    }.get((kind, digit), kind)
    preimage = {
        "kind": semantic_kind,
        "version": 1,
        "identity": identity,
    }
    return f"next:{kind}:{digest(preimage)}"


def _descriptor() -> dict[str, Any]:
    descriptor = _next_compatibility_descriptor()
    descriptor["compatibility_id"] = recompute_compatibility_id(descriptor)
    return descriptor


def _project() -> dict[str, Any]:
    project = _next_project()
    project["id"] = _id("project", "0")
    project["file_ids"] = [_id("file", "1"), _id("file", "2"), _id("file", "c")]
    project["config_digest"] = project_config_digest(project)
    return project


def _config_project(project: dict[str, Any] | None = None) -> dict[str, Any]:
    source = project or _project()
    return {
        "root": source["root"],
        "source_roots": source["source_roots"],
        "config_path": source["config_path"],
        "compiler_options": copy.deepcopy(source["compiler_options"]),
    }


def _config_projection(
    *,
    projects: list[dict[str, Any]] | None = None,
    targets: list[str] | None = None,
    formats: list[str] | None = None,
    source_plan_digest_value: str | None = None,
    source_plan_file_role_map: list[dict[str, Any]] | None = None,
    source_plan_local_extends: list[dict[str, Any]] | None = None,
    source_plan_control_paths: list[dict[str, Any]] | None = None,
    limits: dict[str, int] | None = None,
) -> dict[str, Any]:
    config_projects = sorted(
        [_config_project(project) for project in (projects or [_project()])],
        key=lambda project: canonical_json_bytes(project["root"]),
    )
    projection: dict[str, Any] = {
        "schema": "code-structure-viz.domain-config/next/v1",
        "projects": config_projects,
        "targets": list(targets or []),
        "upstream_depth": 1,
        "downstream_depth": 1,
        "formats": list(formats or ["semantic-json", "plantuml"]),
        "limits": copy.deepcopy(limits or _next_limits()),
        "trusted_environment_digest": _trusted_environment()["sha256"],
        "source_plan_digest": "0" * 64,
        "domain_config_digest": "0" * 64,
    }
    projection["source_plan"] = source_plan_descriptor(
        projection,
        resolved_control_paths=source_plan_control_paths,
        local_extends=source_plan_local_extends,
        file_role_map=source_plan_file_role_map,
    )
    projection["source_plan_digest"] = source_plan_digest_value or recompute_source_plan_digest(
        projection
    )
    projection["domain_config_digest"] = digest(
        {key: value for key, value in projection.items() if key != "domain_config_digest"}
    )
    return projection


def _snapshot_request(
    *,
    projects: list[dict[str, Any]] | None = None,
    targets: list[str] | None = None,
    formats: list[str] | None = None,
    source_plan_digest: str | None = None,
    run_fingerprint: str = "e" * 64,
    limits: dict[str, int] | None = None,
) -> dict[str, Any]:
    projection = _config_projection(
        projects=projects,
        targets=targets,
        formats=formats,
        source_plan_digest_value=source_plan_digest,
        limits=limits,
    )
    return {
        "schema": "code-structure-viz.next-snapshot-request/v1",
        "projects": projection["projects"],
        "targets": projection["targets"],
        "upstream_depth": projection["upstream_depth"],
        "downstream_depth": projection["downstream_depth"],
        "formats": projection["formats"],
        "limits": projection["limits"],
        "trusted_environment_digest": projection["trusted_environment_digest"],
        "source_plan": copy.deepcopy(projection["source_plan"]),
        "source_plan_digest": projection["source_plan_digest"],
        "domain_config_digest": projection["domain_config_digest"],
        "run_fingerprint": run_fingerprint,
    }


def _file(file_id: str, path: str, role: str, content: bytes) -> dict[str, Any]:
    return {
        "kind": "file",
        "id": _id("file", file_id),
        "path": path,
        "project_id": _id("project", "0"),
        "roles": [role],
        "effective_role": role,
        "size_bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def _type_ir(module_id: str) -> dict[str, Any]:
    primitive = {"kind": "primitive", "name": "string"}
    return {
        "kind": "object",
        "properties": [
            {
                "name": "render",
                "type": {
                    "kind": "function",
                    "type_parameter_count": 1,
                    "this_type": None,
                    "parameters": [
                        {
                            "type": {"kind": "type_parameter", "ordinal": 0},
                            "optional": False,
                            "rest": False,
                        }
                    ],
                    "return_type": {
                        "kind": "reference",
                        "scope": "repository",
                        "module": module_id,
                        "exported_name": "Props",
                        "type_arguments": [],
                    },
                },
                "optional": False,
                "readonly": False,
            },
            {"name": "title", "type": primitive, "optional": False, "readonly": True},
            {
                "name": "values",
                "type": {
                    "kind": "tuple",
                    "elements": [{"type": primitive, "optional": False}],
                    "rest": {"kind": "array", "element": primitive, "readonly": True},
                    "readonly": True,
                },
                "optional": True,
                "readonly": False,
            },
        ],
        "index_signatures": [{"key_type": "string", "value_type": primitive, "readonly": True}],
        "call_signatures": [
            {
                "type_parameter_count": 0,
                "this_type": None,
                "parameters": [{"type": primitive, "optional": True, "rest": False}],
                "return_type": {"kind": "primitive", "name": "unknown"},
            }
        ],
    }


def _model() -> dict[str, Any]:
    file_one = _file(
        "1",
        "src/Button.tsx",
        "program",
        (
            b"export default Button;\n"
            b"export const renderValue = 1;\n"
            b"export type Props = { title: string };\n"
            b'export * from "./Other";\n'
        ),
    )
    file_two = _file("2", "src/Card.tsx", "program", b"const Card = 1;\n")
    file_three = _file("c", "src/types.d.ts", "context", b"export interface Props {}\n")
    module_one = {
        "kind": "module",
        "id": _id("module", "3"),
        "project_id": _id("project", "0"),
        "path": "src/Button.tsx",
        "router_context": "app_ui",
        "client_entry": True,
        "derived_roles": ["client_dependency"],
    }
    module_two = {
        "kind": "module",
        "id": _id("module", "4"),
        "project_id": _id("project", "0"),
        "path": "src/Card.tsx",
        "router_context": "none",
        "client_entry": False,
        "derived_roles": [],
    }
    component_one = {
        "kind": "component",
        "id": _id("component", "5"),
        "module_id": module_one["id"],
        "declaration_key": "Button",
        "recognition_evidence": ["jsx_output", "route_default"],
        "props_state": "known",
    }
    component_two = {
        "kind": "component",
        "id": _id("component", "6"),
        "module_id": module_two["id"],
        "declaration_key": "Card",
        "recognition_evidence": ["trusted_callable"],
        "props_state": "no_props",
    }
    members = [
        {
            "kind": "export_binding",
            "id": _id("member", "7"),
            "owner_id": module_one["id"],
            "exported_name": "default",
            "role": "value",
            "target_component_id": component_one["id"],
            "resolution_kind": "component",
            "reexport": False,
        },
        {
            "kind": "import_binding",
            "id": _id("member", "8"),
            "owner_id": module_one["id"],
            "local_component_id": component_two["id"],
            "imported_name": "Card",
            "role": "value",
            "source": {"kind": "internal", "module_id": module_two["id"]},
        },
        {
            "kind": "prop",
            "id": _id("member", "9"),
            "owner_id": component_one["id"],
            "name": "props",
            "type_node": _type_ir(cast(str, module_one["id"])),
            "optional": False,
            "readonly": False,
            "default_evidence": "none",
        },
    ]
    relations = [
        {
            "kind": "static_import",
            "id": _id("relation", "a"),
            "source_id": module_one["id"],
            "target": {"kind": "internal", "module_id": module_two["id"]},
            "role": "value",
            "reexport": False,
            "boundary_effect": "none",
        },
        {
            "kind": "jsx_render",
            "id": _id("relation", "b"),
            "source_id": component_one["id"],
            "target": {"kind": "internal", "component_id": component_two["id"]},
            "occurrence_count": 1,
            "contexts": ["direct"],
        },
        {
            "kind": "component_wrap",
            "id": _id("relation", "c"),
            "source_id": component_two["id"],
            "target_component_id": component_one["id"],
            "occurrence_count": 1,
            "contexts": ["direct"],
        },
    ]
    facts = [
        {
            "kind": "client_entry",
            "id": _id("fact", "d"),
            "owner_id": module_one["id"],
            "value": True,
        },
        {
            "kind": "router_context",
            "id": _id("fact", "e"),
            "owner_id": module_one["id"],
            "value": "app_ui",
        },
        {
            "kind": "router_context",
            "id": _id("fact", "f"),
            "owner_id": module_two["id"],
            "value": "none",
        },
    ]
    model: dict[str, Any] = {
        "schema": "code-structure-viz.next-model/v1",
        "projects": [_project()],
        "files": [file_one, file_two, file_three],
        "modules": [module_one, module_two],
        "components": [component_one, component_two],
        "members": members,
        "relations": relations,
        "facts": facts,
        "coverage": _next_coverage(),
        "diagnostics": [],
    }
    counts = model["coverage"]["counts"]
    for collection in COLLECTIONS:
        counts[collection] = len(model[collection])
    counts["published"] = sum(len(model[collection]) for collection in COLLECTIONS)
    counts["internal_entities"] = len(model["modules"]) + len(model["components"])
    counts["discovered"] = counts["published"]
    model["coverage"]["non_component_value_export_count"] = 1
    model["coverage"]["type_only_export_count"] = 1
    for collection in COLLECTIONS:
        model[collection].sort(key=lambda record: record["id"])
    for project in model["projects"]:
        project["file_ids"].sort()
    return model


def _empty_model() -> dict[str, Any]:
    model = _model()
    model["projects"][0]["file_ids"] = []
    for collection in COLLECTIONS[1:]:
        model[collection] = []
    counts = model["coverage"]["counts"]
    for collection in COLLECTIONS:
        counts[collection] = len(model[collection])
    counts["published"] = 1
    counts["discovered"] = 1
    counts["internal_entities"] = 0
    return model


def _semantic(model: dict[str, Any], status: str = "complete") -> dict[str, Any]:
    descriptor = _descriptor()
    trusted_environment_digest = _trusted_environment()["sha256"]
    value = {
        "type": "semantic_snapshot",
        "schema": "code-structure-viz.semantic/v1",
        "domain": "next",
        "document_kind": "snapshot",
        "status": status,
        "semantic_compatibility_id": descriptor["compatibility_id"],
        "compatibility_descriptor": descriptor,
        "identity_versions": descriptor["identity_versions"],
        "source": {
            "schema": "code-structure-viz.source-view/v1",
            "kind": "working-tree",
            "head_commit": None,
            "fingerprint": "b" * 64,
            "file_count": len(model["files"]),
        },
        "request": _snapshot_request(),
        "coverage": copy.deepcopy(model["coverage"]),
        "projects": model["projects"],
        "files": model["files"],
        "entities": [*model["modules"], *model["components"]],
        "members": model["members"],
        "relations": model["relations"],
        "facts": model["facts"],
        "diagnostics": [],
    }
    if status == "incomplete":
        value["incomplete_kind"] = "partial_safe"
        value["diagnostics"] = [
            {
                "code": "CSV-NEXT-FLOW-001",
                "severity": "warning",
                "recoverable": True,
                "count": 1,
                "path_ref": None,
                "symbol_ref": _id("component", "5"),
                "outcome": "partial_safe",
                "ref_permission": "symbol",
            }
        ]
    value["request"]["run_fingerprint"] = recompute_run_fingerprint(
        source_view_fingerprint=value["source"]["fingerprint"],
        source_plan_digest=value["request"]["source_plan_digest"],
        domain_config_digest=value["request"]["domain_config_digest"],
        projects=value["projects"],
        targets=value["request"]["targets"],
        limits=value["request"]["limits"],
        node_version="22.14.0",
        typescript_version="5.9.2",
        adapter_version="1.0.0",
        protocol="code-structure-viz.next-adapter/v1",
        trusted_environment_digest=trusted_environment_digest,
    )
    return value


def _request() -> dict[str, Any]:
    model = _model()
    trusted_environment_digest = _trusted_environment()["sha256"]
    project = copy.deepcopy(model["projects"][0])
    contents = {
        "src/Button.tsx": (
            b"export default Button;\n"
            b"export const renderValue = 1;\n"
            b"export type Props = { title: string };\n"
            b'export * from "./Other";\n'
        ),
        "src/Card.tsx": b"const Card = 1;\n",
        "src/types.d.ts": b"export interface Props {}\n",
    }
    files = []
    for file_record in model["files"]:
        content = contents[file_record["path"]]
        files.append(
            {
                **file_record,
                "content_base64": base64.b64encode(content).decode("ascii"),
            }
        )
    request = {
        "schema": "code-structure-viz.next-adapter-request/v1",
        "protocol": "code-structure-viz.next-adapter/v1",
        "request_id": "0" * 64,
        "adapter_version": "1.0.0",
        "trusted_type_environment": {
            "schema": "code-structure-viz.next-trusted-types/v1",
            "environment_version": "1",
            "semantic_profile_id": "next-trusted-profile-v1",
            "sha256": trusted_environment_digest,
        },
        "projects": [project],
        "files": files,
        "targets": [],
        "limits": _next_limits(),
    }
    request["request_id"] = recompute_request_id(request)
    return request


def _complete_proof(model: dict[str, Any]) -> dict[str, Any]:
    records = []
    for collection in COLLECTIONS:
        for record in model[collection]:
            records.append({"collection": collection, "record": record, "taints": []})
    return {
        "discovered_records": records,
        "failure_roots": [],
        "causal_edges": [],
        "target_resolutions": [],
        "export_observations": expected_export_observations(model),
        "export_resolution_witness": expected_export_resolution_witness(model),
        "export_reexport_witness": expected_export_reexport_witness(model),
        "excluded": [],
        "failed": [],
    }


def _discovered_index(proof: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    discovered: dict[str, dict[str, dict[str, Any]]] = {
        collection: {} for collection in COLLECTIONS
    }
    for item in proof["discovered_records"]:
        discovered[item["collection"]][item["record"]["id"]] = item
    return discovered


def _materialize_single_root_taints(proof: dict[str, Any]) -> None:
    """Populate one root's labels from the independently generated edge witness."""

    discovered = _discovered_index(proof)
    edges = derive_required_causal_edges(proof, discovered)
    proof["causal_edges"] = edges
    adjacency: dict[str, set[str]] = {}
    for edge in edges:
        adjacency.setdefault(edge["source_id"], set()).add(edge["record_id"])
    root = proof["failure_roots"][0]
    reachable: set[str] = set()
    pending = [root["id"]]
    while pending:
        source_id = pending.pop()
        for record_id in adjacency.get(source_id, set()):
            if record_id not in reachable:
                reachable.add(record_id)
                pending.append(record_id)
    for item in proof["discovered_records"]:
        item["taints"] = [root["kind"]] if item["record"]["id"] in reachable else []


def _response(
    model: dict[str, Any],
    proof: dict[str, Any] | None = None,
    request: dict[str, Any] | None = None,
) -> dict[str, Any]:
    descriptor = _descriptor()
    trusted_environment_digest = _trusted_environment()["sha256"]
    request_value = request or _request()
    return {
        "schema": "code-structure-viz.next-adapter-response/v1",
        "protocol": "code-structure-viz.next-adapter/v1",
        "request_id": request_value["request_id"],
        "adapter_version": "1.0.0",
        "trusted_type_environment_digest": trusted_environment_digest,
        "semantic_compatibility_id": descriptor["compatibility_id"],
        "compatibility_descriptor": descriptor,
        "identity_versions": descriptor["identity_versions"],
        "limits": _next_limits(),
        "model": model,
        "proof": proof if proof is not None else _complete_proof(model),
        "model_digest": digest(model),
    }


def _trusted_environment() -> dict[str, Any]:
    value = _next_trusted_environment()
    value["license_inventory_digest"] = TRUSTED_PROFILE_LICENSE_DIGEST
    value["files"] = [
        {
            "physical_path": physical_path,
            "virtual_path": virtual_path,
            "size_bytes": TRUSTED_PROFILE_FILE_SIZES[virtual_path],
            "sha256": TRUSTED_PROFILE_FILE_SHA256[virtual_path],
            "license_id": TRUSTED_PROFILE_FILE_LICENSES[virtual_path],
        }
        for physical_path, virtual_path in TRUSTED_PROFILE_PHYSICAL_TO_VIRTUAL
    ]
    value["certified_symbols"] = copy.deepcopy(list(TRUSTED_PROFILE_CERTIFIED_SYMBOLS))
    value["anti_shadowing_witness"] = list(TRUSTED_PROFILE_SHADOWING_WITNESS)
    value["sha256"] = digest({key: item for key, item in value.items() if key != "sha256"})
    return value


def _public_diagnostic(
    code: str, *, path: str | None = None, symbol: str | None = None
) -> dict[str, Any]:
    entries = cast(list[dict[str, Any]], _schema("next-diagnostic-catalog-v1.json")["entries"])
    catalog = {entry["code"]: entry for entry in entries}
    entry = catalog[code]
    if entry["ref_permission"] == "path" and path is None:
        path = "src/Button.tsx"
    elif entry["ref_permission"] == "symbol" and symbol is None:
        symbol = _id("component", "5")
    elif entry["ref_permission"] == "path_or_symbol" and path is None and symbol is None:
        path = "src/Button.tsx"
    return {
        "type": "diagnostic",
        "schema": "code-structure-viz.diagnostic/v1",
        "code": code,
        "severity": entry["severity"],
        "domain": "next",
        "path": path,
        "symbol": symbol,
        "line": None,
        "recoverable": entry["recoverable"],
        "message": entry["message"],
        "outcome": entry["outcome"],
        "ref_permission": entry["ref_permission"],
    }


def _domain(
    status: str = "complete",
    *,
    overrun: bool = False,
    runtime_unavailable: bool = False,
    targets: list[str] | None = None,
    formats: list[str] | None = None,
    max_entities: int = 500,
) -> dict[str, Any]:
    model = _model()
    descriptor = _descriptor()
    environment = _trusted_environment()
    target_values = list(targets or [])
    format_values = list(formats or ["semantic-json", "plantuml"])
    limits = _next_limits(max_entities=max_entities)
    config = _config_projection(
        projects=model["projects"], targets=target_values, formats=format_values, limits=limits
    )
    snapshot_request = _snapshot_request(
        projects=model["projects"],
        targets=target_values,
        formats=format_values,
        limits=limits,
    )
    artifact_for_format = {
        "semantic-json": "next.snapshot.semantic.json",
        "plantuml": "next.snapshot.puml",
    }
    selected_artifacts = [artifact_for_format[format_name] for format_name in format_values]
    entity_count: int | None
    payload_available: bool
    incomplete_kind: str | None
    artifact_paths: list[str]
    diagnostics: list[dict[str, Any]]
    actual: int | None
    measured_actual = 501 if overrun else 4
    budget_overrun = measured_actual > max_entities
    if runtime_unavailable:
        assert status == "incomplete"
        assert not overrun
        entity_count = None
        payload_available = False
        incomplete_kind = "payload_unavailable"
        artifact_paths = []
        diagnostics = [_public_diagnostic("CSV-NEXT-NODE-001")]
        actual = None
    elif status == "complete":
        assert not budget_overrun
        entity_count = measured_actual
        payload_available = True
        incomplete_kind = None
        artifact_paths = selected_artifacts
        diagnostics = []
        actual = measured_actual
    elif status == "not_applicable":
        entity_count = 0
        payload_available = False
        incomplete_kind = None
        artifact_paths = []
        diagnostics = [_public_diagnostic("CSV-NEXT-APPLICABILITY-001")]
        actual = 0
    else:
        entity_count = None if budget_overrun else measured_actual
        payload_available = not budget_overrun
        incomplete_kind = "payload_unavailable" if budget_overrun else "partial_safe"
        artifact_paths = [] if budget_overrun else selected_artifacts
        diagnostics = [
            _public_diagnostic(
                "CSV-NEXT-LIMIT-005" if budget_overrun else "CSV-NEXT-FLOW-001",
                symbol=None if budget_overrun else _id("component", "5"),
            )
        ]
        actual = measured_actual
    value: dict[str, Any] = {
        "domain": "next",
        "status": status,
        "payload_available": payload_available,
        "entity_count": entity_count,
        "budget": {
            "name": "max_entities",
            "requested": None,
            "resolved": max_entities,
            "actual": actual,
            "source": "builtin",
            "outcome": (
                "not_applicable"
                if status == "not_applicable"
                else "payload_unavailable"
                if incomplete_kind == "payload_unavailable"
                else "partial_safe"
                if incomplete_kind == "partial_safe"
                else "complete"
            ),
        },
        "semantic_compatibility_id": descriptor["compatibility_id"],
        "compatibility_descriptor": descriptor,
        "identity_versions": descriptor["identity_versions"],
        "source_plan_digest": config["source_plan_digest"],
        "domain_config_digest": config["domain_config_digest"],
        "run_fingerprint": "e" * 64,
        "source": {
            "schema": "code-structure-viz.source-view/v1",
            "kind": "working-tree",
            "head_commit": None,
            "fingerprint": "b" * 64,
            "file_count": len(model["files"]),
        },
        "request": snapshot_request,
        "config": config,
        "projects": [copy.deepcopy(model["projects"][0])],
        "targets": target_values,
        "formats": format_values,
        "toolchain": {
            "node": {
                "status": (
                    "not_applicable"
                    if status == "not_applicable"
                    else "unavailable"
                    if runtime_unavailable
                    else "available"
                ),
                "version": None if status == "not_applicable" or runtime_unavailable else "22.14.0",
                "failure_kind": (
                    None
                    if status == "not_applicable"
                    else "missing"
                    if runtime_unavailable
                    else None
                ),
            },
            "node_version": None
            if status == "not_applicable" or runtime_unavailable
            else "22.14.0",
            "typescript_version": "5.9.2",
            "adapter_version": "1.0.0",
            "protocol": "code-structure-viz.next-adapter/v1",
        },
        "trusted_environment": environment,
        "limits": limits,
        "coverage": copy.deepcopy(model["coverage"]),
        "artifact_paths": artifact_paths,
        "diagnostics": diagnostics,
    }
    if incomplete_kind is not None:
        value["incomplete_kind"] = incomplete_kind
    value["run_fingerprint"] = recompute_run_fingerprint(
        source_view_fingerprint=value["source"]["fingerprint"],
        source_plan_digest=value["source_plan_digest"],
        domain_config_digest=value["domain_config_digest"],
        projects=value["projects"],
        targets=value["targets"],
        limits=value["limits"],
        node_version=value["toolchain"]["node_version"],
        typescript_version=value["toolchain"]["typescript_version"],
        adapter_version=value["toolchain"]["adapter_version"],
        protocol=value["toolchain"]["protocol"],
        trusted_environment_digest=value["trusted_environment"]["sha256"],
    )
    value["request"]["run_fingerprint"] = value["run_fingerprint"]
    if actual is not None:
        value["coverage"]["counts"]["internal_entities"] = actual
    resolutions = resolve_target_resolutions(target_values, model)
    value["coverage"]["target_completeness"] = [
        {
            "target_key": item["target_key"],
            "status": "complete" if item["status"] == "resolved" else "failed",
            "record_ids": item["record_ids"],
        }
        for item in resolutions
    ]
    return value


def _run_manifest(domain: dict[str, Any]) -> dict[str, Any]:
    base = cast(
        dict[str, Any],
        json.loads(
            (
                ROOT / "tests" / "golden" / "python_snapshot" / "whole" / "run-manifest.json"
            ).read_text(encoding="utf-8")
        ),
    )
    status = domain["status"]
    base["contracts"]["plantuml"] = "code-structure-viz.plantuml/next/v1"
    base["adapters"] = [{"domain": "next", "name": "next-typescript", "version": "1"}]
    base["command"] = {
        "name": "snapshot",
        "domain": "next",
        "formats": domain["formats"],
        "stdout_selector": f"next:{domain['formats'][0]}",
    }
    root_projects = sorted(
        (project["root"] for project in domain["projects"]), key=canonical_json_bytes
    )
    base["request"] = {
        "projects": root_projects,
        "targets": domain["targets"],
        "formats": domain["formats"],
        "upstream_depth": 1,
        "downstream_depth": 1,
    }
    base["next_request"] = copy.deepcopy(domain["request"])
    base["next_config"] = copy.deepcopy(domain["config"])
    base["source"] = domain["source"]
    base["config"] = {
        "schema": "code-structure-viz.config/v1",
        "source": "builtin",
        "sha256": "8" * 64,
        "resolved": {
            "next": {
                "projects": root_projects,
                "targets": domain["targets"],
                "formats": domain["formats"],
                "trusted_environment_digest": domain["trusted_environment"]["sha256"],
            },
            "traversal": {"upstream_depth": 1, "downstream_depth": 1},
            "limits": _next_limits(),
        },
        "value_sources": {
            "next_projects": "builtin",
            "next_targets": "builtin",
            "formats": "builtin",
            "upstream_depth": "builtin",
            "downstream_depth": "builtin",
            "limits": "builtin",
            "trusted_environment": "builtin",
        },
    }
    base["config"]["sha256"] = digest(
        {key: value for key, value in base["config"].items() if key != "sha256"}
    )
    base["run"] = {
        "status": status,
        "exit_code": 0 if status in {"complete", "not_applicable"} else 3,
        "fingerprint": domain["run_fingerprint"],
    }
    base["domains"] = [domain]
    base["artifacts"] = []
    for path in domain["artifact_paths"]:
        fmt = "semantic-json" if path.endswith(".json") else "plantuml"
        media_type = (
            "application/json" if fmt == "semantic-json" else "text/vnd.plantuml; charset=utf-8"
        )
        base["artifacts"].append(
            {
                "path": path,
                "domain": "next",
                "format": fmt,
                "media_type": media_type,
                "size_bytes": len(_published_bytes(domain)[path]),
                "sha256": hashlib.sha256(_published_bytes(domain)[path]).hexdigest(),
            }
        )
    base["diagnostics"] = copy.deepcopy(domain["diagnostics"])
    return base


def _published_bytes(domain: dict[str, Any]) -> dict[str, bytes]:
    return {
        path: (
            b'{"schema":"code-structure-viz.semantic/v1"}\n'
            if path.endswith(".json")
            else b"@startuml\n@enduml\n"
        )
        for path in domain["artifact_paths"]
    }


def _stdout_result_for_domain(
    domain: dict[str, Any],
    manifest: dict[str, Any],
    selector: str | None = None,
) -> dict[str, Any]:
    selector = selector or f"next:{domain['formats'][0]}"
    if domain["payload_available"]:
        format_name = selector.removeprefix("next:")
        artifact = next(item for item in manifest["artifacts"] if item["format"] == format_name)
        result: dict[str, Any] = {
            "type": "stdout_result",
            "schema": "code-structure-viz.stdout-result/v1",
            "selector": selector,
            "availability": True,
            "stable_reason": "published_artifact",
            "artifact": artifact,
            "domain_status": domain["status"],
        }
        if domain["status"] == "incomplete":
            result["incomplete_kind"] = "partial_safe"
        return result
    return {
        "type": "stdout_result",
        "schema": "code-structure-viz.stdout-result/v1",
        "selector": selector,
        "availability": False,
        "domain_status": domain["status"],
        "stable_reason": (
            "domain_not_applicable"
            if domain["status"] == "not_applicable"
            else "domain_payload_unavailable"
        ),
        "artifact": None,
    }


def _run_summary_value(run_status: str, domain: dict[str, Any] | None = None) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "type": "run_summary",
        "schema": "code-structure-viz.run-summary/v1",
        "run_status": run_status,
        "exit_code": {
            "complete": 0,
            "not_applicable": 0,
            "incomplete": 3,
            "fatal": 1,
            "usage": 2,
            "interrupted": 130,
        }[run_status],
        "domains": [],
        "manifest": None,
    }
    if domain is not None:
        summary["domains"] = [
            {
                "domain": "next",
                "status": domain["status"],
                **(
                    {"incomplete_kind": domain["incomplete_kind"]}
                    if domain["status"] == "incomplete"
                    else {}
                ),
            }
        ]
        summary["manifest"] = "run-manifest.json"
    return summary


def _diagnostic_jsonl(diagnostics: list[dict[str, Any]]) -> bytes:
    return b"".join(canonical_json_bytes(item) + b"\n" for item in diagnostics)


def _runtime_manifest() -> dict[str, Any]:
    members: list[dict[str, Any]] = []
    for physical_path, path in RUNTIME_PHYSICAL_TO_VIRTUAL:
        content = (ROOT / physical_path).read_bytes()
        members.append(
            {
                "physical_path": physical_path,
                "path": path,
                "size_bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
                "role": RUNTIME_REQUIRED_PATHS[path],
            }
        )
    members.sort(key=lambda item: item["path"])
    licenses = copy.deepcopy(list(TRUSTED_PROFILE_LICENSES))
    manifest: dict[str, Any] = {
        "schema": "code-structure-viz.next-runtime-manifest/v1",
        "members": members,
        "licenses": licenses,
        "license_inventory_digest": TRUSTED_PROFILE_LICENSE_DIGEST,
        "inventory_attestation": {
            "schema": "code-structure-viz.next-runtime-inventory/v1",
            "members": members,
            "sha256": digest({"members": members}),
        },
    }
    manifest["build_input_digest"] = digest({"members": members, "licenses": licenses})
    manifest["build_output_digest"] = digest({"members": members})
    manifest["manifest_sha256"] = digest(
        {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    )
    return manifest


def test_public_next_semantic_variants_are_closed() -> None:
    validator = _validator("semantic-v1.schema.json")
    empty = _semantic(_empty_model())
    non_empty = _semantic(_model())
    partial = _semantic(_model(), "incomplete")
    for value in (empty, non_empty, partial):
        validator.validate(value)
        validate_semantic_snapshot(value)

    wrong_domain = copy.deepcopy(non_empty)
    wrong_domain["domain"] = "python"
    with pytest.raises(ValidationError):
        validator.validate(wrong_domain)
    wrong_shape = copy.deepcopy(non_empty)
    next(fact for fact in wrong_shape["facts"] if fact["kind"] == "client_entry")["value"] = False
    with pytest.raises(ValidationError):
        validator.validate(wrong_shape)
    wrong_entity_shape = copy.deepcopy(non_empty)
    wrong_entity_shape["entities"] = [
        {
            "kind": "class",
            "id": "python:class:" + "0" * 64,
            "module": "app.widgets",
            "qualified_name": "app.widgets.Button",
            "name": "Button",
            "path": "app/widgets.py",
            "range": {"start_line": 1, "start_column": 0, "end_line": 1, "end_column": 1},
            "decorators": [],
        }
    ]
    with pytest.raises(ValidationError):
        validator.validate(wrong_entity_shape)


def test_head_commit_accepts_only_full_sha1_or_sha256_lengths() -> None:
    validator = _validator("semantic-v1.schema.json")
    for length in (40, 64):
        value = _semantic(_model())
        value["source"]["head_commit"] = "a" * length
        validator.validate(value)
        validate_semantic_snapshot(value)
    for length in (39, 41, 63, 65):
        value = _semantic(_model())
        value["source"]["head_commit"] = "a" * length
        with pytest.raises(ValidationError):
            validator.validate(value)
        with pytest.raises(AssertionError):
            validate_semantic_snapshot(value)


def test_props_ir_matches_design_variants_and_rejects_old_shapes() -> None:
    validator = _validator("next-semantic-v1.schema.json")
    value = _semantic(_model())
    validator.validate(value)

    mutations = []
    redacted_old = copy.deepcopy(value)
    redacted_member = next(item for item in redacted_old["members"] if item["kind"] == "prop")
    redacted_props = {item["name"]: item for item in redacted_member["type_node"]["properties"]}
    redacted_props["title"]["type"] = {
        "kind": "redacted_literal",
        "value_kind": "string",
        "value_digest": "a" * 64,
    }
    mutations.append(redacted_old)
    tuple_old = copy.deepcopy(value)
    tuple_member = next(item for item in tuple_old["members"] if item["kind"] == "prop")
    tuple_props = {item["name"]: item for item in tuple_member["type_node"]["properties"]}
    tuple_props["values"]["type"]["elements"][0]["rest"] = False
    mutations.append(tuple_old)
    function_old = copy.deepcopy(value)
    function_member = next(item for item in function_old["members"] if item["kind"] == "prop")
    function_props = {item["name"]: item for item in function_member["type_node"]["properties"]}
    function_props["render"]["type"]["generic_ordinals"] = []
    mutations.append(function_old)
    repository_path = copy.deepcopy(value)
    repository_member = next(item for item in repository_path["members"] if item["kind"] == "prop")
    repository_props = {item["name"]: item for item in repository_member["type_node"]["properties"]}
    repository_props["render"]["type"]["return_type"]["module"] = "src/Button.tsx"
    mutations.append(repository_path)
    for mutation in mutations:
        with pytest.raises(ValidationError):
            validator.validate(mutation)

    variants = [
        {"kind": "redacted_literals", "base": "string", "count": 2},
        {
            "kind": "reference",
            "scope": "external",
            "module": "@types/react/jsx-runtime",
            "exported_name": "Element",
            "type_arguments": [],
        },
        {
            "kind": "reference",
            "scope": "trusted",
            "module": "typescript/lib",
            "exported_name": None,
            "type_arguments": [],
        },
        {
            "kind": "union",
            "members": [
                {"kind": "primitive", "name": "string"},
                {"kind": "primitive", "name": "undefined"},
            ],
        },
        {
            "kind": "intersection",
            "members": [{"kind": "primitive", "name": "string"}],
        },
        {"kind": "opaque", "reason": "unsupported_syntax"},
    ]
    for node in variants:
        variant = _semantic(_model())
        next(item for item in variant["members"] if item["kind"] == "prop")["type_node"] = node
        validator.validate(variant)

    invalid_variants = [
        {
            "kind": "reference",
            "scope": "external",
            "module": "@types/react",
            "exported_name": None,
            "type_arguments": [],
        },
        {
            "kind": "reference",
            "scope": "trusted",
            "module": "target-package",
            "exported_name": "Element",
            "type_arguments": [],
        },
        {
            "kind": "reference",
            "scope": "trusted",
            "module": "react",
            "exported_name": None,
            "type_arguments": [],
        },
        {"kind": "redacted_literals", "base": "string", "count": 0},
    ]
    for node in invalid_variants:
        variant = _semantic(_model())
        next(item for item in variant["members"] if item["kind"] == "prop")["type_node"] = node
        with pytest.raises(ValidationError):
            validator.validate(variant)


def test_props_ir_limits_and_canonical_rules_are_reference_enforced() -> None:
    validator = _validator("semantic-v1.schema.json")

    def semantic_with_type(node: dict[str, Any]) -> dict[str, Any]:
        value = _semantic(_model())
        prop = next(item for item in value["members"] if item["kind"] == "prop")
        prop["type_node"] = copy.deepcopy(node)
        return value

    depth_16: dict[str, Any] = {"kind": "primitive", "name": "string"}
    for _ in range(15):
        depth_16 = {"kind": "array", "element": depth_16, "readonly": False}
    depth_value = semantic_with_type(depth_16)
    validator.validate(depth_value)
    validate_semantic_snapshot(depth_value)

    depth_17 = {"kind": "array", "element": depth_16, "readonly": False}
    depth_value = semantic_with_type(depth_17)
    validator.validate(depth_value)
    with pytest.raises(AssertionError):
        validate_semantic_snapshot(depth_value)

    node_512_properties: list[dict[str, Any]] = [
        {
            "name": f"p{index:03d}",
            "type": (
                {
                    "kind": "array",
                    "element": {"kind": "primitive", "name": "string"},
                    "readonly": False,
                }
                if index < 255
                else {"kind": "primitive", "name": "string"}
            ),
            "optional": False,
            "readonly": False,
        }
        for index in range(256)
    ]
    node_512: dict[str, Any] = {
        "kind": "object",
        "properties": node_512_properties,
        "index_signatures": [],
        "call_signatures": [],
    }
    value_512 = semantic_with_type(node_512)
    validator.validate(value_512)
    validate_semantic_snapshot(value_512)
    node_513 = copy.deepcopy(node_512)
    node_513["properties"][-1]["type"] = {
        "kind": "array",
        "element": {"kind": "primitive", "name": "string"},
        "readonly": False,
    }
    value_513 = semantic_with_type(node_513)
    validator.validate(value_513)
    with pytest.raises(AssertionError):
        validate_semantic_snapshot(value_513)

    union_64: dict[str, Any] = {
        "kind": "union",
        "members": [
            {"kind": "redacted_literals", "base": "string", "count": count}
            for count in range(1, 65)
        ],
    }
    union_64["members"].sort(key=canonical_json_bytes)
    union_value = semantic_with_type(union_64)
    validator.validate(union_value)
    validate_semantic_snapshot(union_value)
    union_65: dict[str, Any] = copy.deepcopy(union_64)
    union_65["members"].append({"kind": "redacted_literals", "base": "string", "count": 65})
    union_65["members"].sort(key=canonical_json_bytes)
    with pytest.raises(ValidationError):
        validator.validate(semantic_with_type(union_65))

    unsorted_union: dict[str, Any] = copy.deepcopy(union_64)
    unsorted_union["members"].reverse()
    with pytest.raises(AssertionError):
        validate_semantic_snapshot(semantic_with_type(unsorted_union))
    duplicate_union: dict[str, Any] = copy.deepcopy(union_64)
    duplicate_union["members"][-1] = copy.deepcopy(duplicate_union["members"][-2])
    with pytest.raises(AssertionError):
        validate_semantic_snapshot(semantic_with_type(duplicate_union))

    object_256: dict[str, Any] = {
        "kind": "object",
        "properties": [
            {
                "name": f"p{index:03d}",
                "type": {"kind": "primitive", "name": "string"},
                "optional": False,
                "readonly": False,
            }
            for index in range(256)
        ],
        "index_signatures": [],
        "call_signatures": [],
    }
    validator.validate(semantic_with_type(object_256))
    object_257 = copy.deepcopy(object_256)
    object_257["properties"].append(
        {
            "name": "p256",
            "type": {"kind": "primitive", "name": "string"},
            "optional": False,
            "readonly": False,
        }
    )
    with pytest.raises(ValidationError):
        validator.validate(semantic_with_type(object_257))

    nested_257 = {
        "kind": "object",
        "properties": [
            {
                "name": "nested",
                "type": object_256,
                "optional": False,
                "readonly": False,
            }
        ],
        "index_signatures": [],
        "call_signatures": [],
    }
    with pytest.raises(AssertionError):
        validate_semantic_snapshot(semantic_with_type(nested_257))

    bad_ordinal = {
        "kind": "function",
        "type_parameter_count": 1,
        "this_type": None,
        "parameters": [],
        "return_type": {"kind": "type_parameter", "ordinal": 1},
    }
    with pytest.raises(AssertionError):
        validate_semantic_snapshot(semantic_with_type(bad_ordinal))
    bad_rest = {
        "kind": "function",
        "type_parameter_count": 0,
        "this_type": None,
        "parameters": [
            {"type": {"kind": "primitive", "name": "string"}, "optional": False, "rest": True},
            {"type": {"kind": "primitive", "name": "string"}, "optional": False, "rest": False},
        ],
        "return_type": {"kind": "primitive", "name": "undefined"},
    }
    with pytest.raises(AssertionError):
        validate_semantic_snapshot(semantic_with_type(bad_rest))

    def add_signature_props(model: dict[str, Any], count: int) -> None:
        component_id = _id("component", "5")
        for index in range(count):
            prop: dict[str, Any] = {
                "kind": "prop",
                "id": "",
                "owner_id": component_id,
                "name": f"signature{index:02d}",
                "type_node": {
                    "kind": "object",
                    "properties": [],
                    "index_signatures": [],
                    "call_signatures": [
                        {
                            "type_parameter_count": 0,
                            "this_type": None,
                            "parameters": [],
                            "return_type": {"kind": "primitive", "name": "undefined"},
                        }
                    ],
                },
                "optional": False,
                "readonly": False,
                "default_evidence": "none",
            }
            prop["id"] = recompute_record_id(prop)
            model["members"].append(prop)
        model["members"].sort(key=lambda item: item["id"])
        model["coverage"]["counts"]["members"] = len(model["members"])
        model["coverage"]["counts"]["published"] += count
        model["coverage"]["counts"]["discovered"] += count

    signatures_14 = _model()
    add_signature_props(signatures_14, 14)
    validate_semantic_snapshot(_semantic(signatures_14))
    signatures_15 = _model()
    add_signature_props(signatures_15, 15)
    with pytest.raises(AssertionError):
        validate_semantic_snapshot(_semantic(signatures_15))


def test_reference_validator_closes_ownership_order_and_fact_invariants() -> None:
    model = _model()
    validate_model(model)
    diagnostic_model = copy.deepcopy(model)
    diagnostic_model["diagnostics"] = [
        {
            "code": "CSV-NEXT-FLOW-001",
            "severity": "warning",
            "recoverable": True,
            "count": 1,
            "path_ref": None,
            "symbol_ref": _id("component", "5"),
            "outcome": "partial_safe",
            "ref_permission": "symbol",
        }
    ]
    validate_model(diagnostic_model)
    wrong_diagnostic = copy.deepcopy(diagnostic_model)
    wrong_diagnostic["diagnostics"][0]["severity"] = "error"
    with pytest.raises(AssertionError):
        validate_model(wrong_diagnostic)
    unknown_diagnostic = copy.deepcopy(diagnostic_model)
    unknown_diagnostic["diagnostics"][0]["code"] = "CSV-NEXT-UNKNOWN-999"
    with pytest.raises(AssertionError):
        validate_model(unknown_diagnostic)
    split_diagnostic = copy.deepcopy(diagnostic_model)
    split_diagnostic["diagnostics"].append(copy.deepcopy(split_diagnostic["diagnostics"][0]))
    split_diagnostic["diagnostics"].sort(key=canonical_json_bytes)
    with pytest.raises(AssertionError):
        validate_model(split_diagnostic)
    wrong_reference = copy.deepcopy(diagnostic_model)
    wrong_reference["diagnostics"][0]["path_ref"] = "src/Button.tsx"
    with pytest.raises(AssertionError):
        validate_model(wrong_reference)
    wrong_status = copy.deepcopy(_semantic(_model(), "incomplete"))
    wrong_status["diagnostics"][0]["outcome"] = "complete"
    with pytest.raises(AssertionError):
        validate_semantic_snapshot(wrong_status)
    mutations = []

    duplicate = copy.deepcopy(model)
    duplicate["files"].append(copy.deepcopy(duplicate["files"][0]))
    mutations.append(duplicate)
    wrong_owner = copy.deepcopy(model)
    next(member for member in wrong_owner["members"] if member["kind"] == "prop")["owner_id"] = _id(
        "module", "4"
    )
    mutations.append(wrong_owner)
    wrong_roles = copy.deepcopy(model)
    wrong_roles["files"][0]["roles"] = ["program", "control"]
    mutations.append(wrong_roles)
    wrong_project = copy.deepcopy(model)
    wrong_project["files"][0]["project_id"] = _id("project", "9")
    mutations.append(wrong_project)
    wrong_fact = copy.deepcopy(model)
    next(fact for fact in wrong_fact["facts"] if fact["kind"] == "client_entry")["value"] = False
    mutations.append(wrong_fact)
    dangling = copy.deepcopy(model)
    next(relation for relation in dangling["relations"] if relation["kind"] == "static_import")[
        "target"
    ]["module_id"] = _id("module", "f")
    mutations.append(dangling)
    wrong_count = copy.deepcopy(model)
    wrong_count["coverage"]["counts"]["components"] += 1
    mutations.append(wrong_count)

    dynamic_wrong_role = copy.deepcopy(model)
    dynamic_wrong_role["relations"].append(
        {
            "kind": "literal_dynamic_import",
            "id": _id("relation", "1"),
            "source_id": _id("module", "3"),
            "target": {"kind": "external", "safe_specifier": "react", "exported_name": "lazy"},
            "role": "type",
            "reexport": False,
            "boundary_effect": "none",
        }
    )
    dynamic_wrong_role["coverage"]["counts"]["relations"] += 1
    dynamic_wrong_role["coverage"]["counts"]["published"] += 1
    dynamic_wrong_role["coverage"]["counts"]["discovered"] += 1
    dynamic_wrong_role["relations"].sort(key=lambda record: record["id"])
    mutations.append(dynamic_wrong_role)

    missing_fact = copy.deepcopy(model)
    missing_fact["facts"] = [
        fact for fact in missing_fact["facts"] if fact["kind"] != "router_context"
    ]
    missing_fact["coverage"]["counts"]["facts"] -= 2
    missing_fact["coverage"]["counts"]["published"] -= 2
    missing_fact["coverage"]["counts"]["discovered"] -= 2
    mutations.append(missing_fact)

    for mutation in mutations:
        with pytest.raises(AssertionError):
            validate_model(mutation)

    stale_identity = copy.deepcopy(model)
    prop = next(item for item in stale_identity["members"] if item["kind"] == "prop")
    prop["name"] = "renamed"
    with pytest.raises(AssertionError):
        validate_model(stale_identity)
    payload_only = copy.deepcopy(model)
    payload_prop = next(item for item in payload_only["members"] if item["kind"] == "prop")
    payload_prop["optional"] = True
    validate_model(payload_only)


def test_adapter_request_response_and_partial_safe_proof_are_reference_validated() -> None:
    request = _request()
    _validator("next-adapter-request-v1.schema.json").validate(request)
    validate_request_envelope(request)

    response = _response(_model())
    _validator("next-adapter-response-v1.schema.json").validate(response)
    assert validate_response_envelope(response, request) == {
        "actual": 4,
        "resolved": 500,
        "allowed": True,
        "payload_available": True,
        "original_outcome": "complete",
        "outcome": "complete",
        "diagnostic_code": None,
        "requested_formats": ["semantic-json", "plantuml"],
        "artifact_paths": ["next.snapshot.semantic.json", "next.snapshot.puml"],
    }
    validate_model(response["model"])
    validate_proof(response["proof"], response["model"])

    partial_model = _model()
    partial_model["coverage"]["counts"]["excluded"] = 1
    partial_model["coverage"]["counts"]["failed"] = 1
    partial_model["coverage"]["affected_ids"] = sorted([_id("file", "e"), _id("module", "f")])
    extra_file = _file("e", "src/Unused.tsx", "program", b"export const unused = 1;\n")
    extra_module = {
        "kind": "module",
        "id": _id("module", "f"),
        "project_id": _id("project", "0"),
        "path": "src/Unused.tsx",
        "router_context": "none",
        "client_entry": False,
        "derived_roles": [],
    }
    extra_import: dict[str, Any] = {
        "kind": "import_binding",
        "id": "",
        "owner_id": extra_module["id"],
        "local_component_id": None,
        "imported_name": "default",
        "role": "value",
        "source": {"kind": "internal", "module_id": _id("module", "3")},
    }
    extra_import["id"] = recompute_record_id(extra_import)
    extra_import_alias = copy.deepcopy(extra_import)
    extra_import_alias["imported_name"] = "PropsView"
    extra_import_alias["id"] = recompute_record_id(extra_import_alias)
    partial_proof = _complete_proof(partial_model)
    partial_proof["discovered_records"].extend(
        [
            {"collection": "files", "record": extra_file, "taints": ["parse_file"]},
            {"collection": "modules", "record": extra_module, "taints": ["parse_file"]},
            {"collection": "members", "record": extra_import, "taints": ["parse_file"]},
            {"collection": "members", "record": extra_import_alias, "taints": ["parse_file"]},
        ]
    )
    partial_proof["excluded"] = [
        {"collection": "files", "record_id": extra_file["id"], "reason": "tainted"},
        {"collection": "members", "record_id": extra_import["id"], "reason": "tainted"},
        {
            "collection": "members",
            "record_id": extra_import_alias["id"],
            "reason": "tainted",
        },
    ]
    partial_proof["failed"] = [
        {"collection": "modules", "record_id": extra_module["id"], "reason": "parse_file"},
    ]
    partial_proof["failure_roots"] = [
        {
            "id": "next:failure:" + "0" * 64,
            "collection": "files",
            "kind": "parse_file",
            "path_ref": "src/Unused.tsx",
            "record_ids": sorted(
                [extra_file["id"], extra_module["id"], extra_import["id"], extra_import_alias["id"]]
            ),
        }
    ]
    _materialize_single_root_taints(partial_proof)
    tainted_ids = {
        item["record"]["id"] for item in partial_proof["discovered_records"] if item["taints"]
    }
    partial_model["coverage"]["affected_ids"] = sorted(tainted_ids)
    partial_model["coverage"]["taint_frontier"] = [_id("module", "3")]
    partial_model["coverage"]["counts"]["discovered"] += 4
    partial_model["coverage"]["counts"]["excluded"] = 3
    partial_model["coverage"]["counts"]["failed"] = 1
    target_request = _request()
    target_request["targets"] = ["path:src/Button.tsx"]
    target_request["request_id"] = recompute_request_id(target_request)
    partial_proof["target_resolutions"] = [
        {
            "target_key": "path:src/Button.tsx",
            "status": "resolved",
            "record_ids": sorted([_id("file", "1"), _id("module", "3"), _id("component", "5")]),
        }
    ]
    partial_model["coverage"]["target_completeness"] = [
        {
            "target_key": "path:src/Button.tsx",
            "status": "complete",
            "record_ids": sorted([_id("file", "1"), _id("module", "3"), _id("component", "5")]),
        }
    ]
    partial_response = _response(partial_model, partial_proof, target_request)
    _validator("next-adapter-response-v1.schema.json").validate(partial_response)
    validate_response_envelope(partial_response, target_request)
    partial_decision = validate_response_envelope(partial_response, target_request)
    assert partial_decision["original_outcome"] == "partial_safe"
    assert partial_decision["outcome"] == "partial_safe"
    assert partial_decision["artifact_paths"] == [
        "next.snapshot.semantic.json",
        "next.snapshot.puml",
    ]
    validate_proof(
        partial_response["proof"],
        partial_response["model"],
        {
            "path:src/Button.tsx": tuple(
                sorted([_id("file", "1"), _id("module", "3"), _id("component", "5")])
            )
        },
        request_targets=target_request["targets"],
    )

    broken_proof = copy.deepcopy(partial_response["proof"])
    broken_proof["excluded"] = []
    with pytest.raises(AssertionError):
        validate_proof(broken_proof, partial_response["model"])
    overlapping_proof = copy.deepcopy(partial_response["proof"])
    overlapping_proof["failed"].append(
        {"collection": "files", "record_id": extra_file["id"], "reason": "parse_file"}
    )
    with pytest.raises(AssertionError):
        validate_proof(overlapping_proof, partial_response["model"])
    broken_target = copy.deepcopy(partial_response["proof"])
    broken_target["target_resolutions"][0]["record_ids"] = [_id("component", "6")]
    with pytest.raises(AssertionError):
        validate_proof(
            broken_target,
            partial_response["model"],
            {
                "path:src/Button.tsx": tuple(
                    sorted([_id("file", "1"), _id("module", "3"), _id("component", "5")])
                )
            },
        )

    missing_target = copy.deepcopy(partial_response)
    missing_target["proof"]["target_resolutions"] = []
    with pytest.raises(AssertionError):
        validate_response_envelope(missing_target, target_request)
    extra_target = copy.deepcopy(partial_response)
    extra_target["proof"]["target_resolutions"].append(
        {"target_key": "path:src/Missing.tsx", "status": "failed", "record_ids": []}
    )
    extra_target["proof"]["target_resolutions"].sort(key=canonical_json_bytes)
    with pytest.raises(AssertionError):
        validate_response_envelope(extra_target, target_request)
    failed_as_resolved = copy.deepcopy(partial_response)
    failed_as_resolved["proof"]["target_resolutions"][0] = {
        "target_key": "path:src/Button.tsx",
        "status": "failed",
        "record_ids": [],
    }
    with pytest.raises(AssertionError):
        validate_response_envelope(failed_as_resolved, target_request)

    missing_taint = copy.deepcopy(partial_response["proof"])
    next(
        item
        for item in missing_taint["discovered_records"]
        if item["record"]["id"] == extra_module["id"]
    )["taints"] = []
    with pytest.raises(AssertionError):
        validate_proof(missing_taint, partial_response["model"])

    excess_taint = copy.deepcopy(partial_response["proof"])
    next(
        item
        for item in excess_taint["discovered_records"]
        if item["record"]["id"] == extra_module["id"]
    )["taints"] = ["parse_file", "read_file"]
    with pytest.raises(AssertionError):
        validate_proof(excess_taint, partial_response["model"])

    illegal_root_edge = copy.deepcopy(partial_response["proof"])
    illegal_root_edge["causal_edges"].append(
        {
            "source_id": "next:failure:" + "0" * 64,
            "record_id": _id("component", "5"),
            "rule": "type_subtree",
        }
    )
    illegal_root_edge["causal_edges"].sort(key=canonical_json_bytes)
    with pytest.raises(AssertionError):
        validate_proof(illegal_root_edge, partial_response["model"])

    omitted_edge = copy.deepcopy(partial_response["proof"])
    omitted_edge["causal_edges"].pop()
    with pytest.raises(AssertionError):
        validate_proof(omitted_edge, partial_response["model"])

    illegal_type_root = copy.deepcopy(partial_response["proof"])
    illegal_type_root["failure_roots"].append(
        {
            "id": "next:failure:" + "2" * 64,
            "collection": "members",
            "kind": "type_symbol",
            "path_ref": "src/Unused.tsx",
            "record_ids": [extra_module["id"]],
        }
    )
    illegal_type_root["causal_edges"].append(
        {
            "source_id": "next:failure:" + "2" * 64,
            "record_id": extra_module["id"],
            "rule": "identity_dependency",
        }
    )
    illegal_type_root["failure_roots"].sort(key=canonical_json_bytes)
    illegal_type_root["causal_edges"].sort(key=canonical_json_bytes)
    with pytest.raises(AssertionError):
        validate_proof(illegal_type_root, partial_response["model"])

    disconnected_edge = copy.deepcopy(partial_response["proof"])
    disconnected_edge["causal_edges"].append(
        {
            "source_id": _id("module", "3"),
            "record_id": _id("file", "1"),
            "rule": "file_all_records",
        }
    )
    disconnected_edge["causal_edges"].sort(key=canonical_json_bytes)
    with pytest.raises(AssertionError):
        validate_proof(disconnected_edge, partial_response["model"])

    vacuous_root = copy.deepcopy(partial_response["proof"])
    vacuous_root["failure_roots"].append(
        {
            "id": "next:failure:" + "1" * 64,
            "collection": "files",
            "kind": "read_file",
            "path_ref": "src/Unused.tsx",
            "record_ids": [extra_file["id"]],
        }
    )
    vacuous_root["failure_roots"].sort(key=canonical_json_bytes)
    with pytest.raises(AssertionError):
        validate_proof(vacuous_root, partial_response["model"])

    wrong_frontier = copy.deepcopy(partial_response["model"])
    wrong_frontier["coverage"]["taint_frontier"] = [_id("module", "4")]
    with pytest.raises(AssertionError):
        validate_proof(partial_response["proof"], wrong_frontier)

    duplicate_frontier = copy.deepcopy(partial_response["model"])
    duplicate_frontier["coverage"]["taint_frontier"] = [_id("module", "3")] * 2
    with pytest.raises(AssertionError):
        validate_proof(partial_response["proof"], duplicate_frontier)

    wrong_count = copy.deepcopy(partial_response["model"])
    wrong_count["coverage"]["counts"]["failed"] += 1
    with pytest.raises(AssertionError):
        validate_proof(partial_response["proof"], wrong_count)

    broken_request = copy.deepcopy(request)
    broken_request["files"][0]["content_base64"] = "not-base64"
    with pytest.raises((AssertionError, ValueError)):
        validate_request_files(broken_request)

    broken_envelope = copy.deepcopy(response)
    broken_envelope["model_digest"] = "0" * 64
    with pytest.raises(AssertionError):
        validate_response_envelope(broken_envelope, request)
    wrong_adapter = copy.deepcopy(response)
    wrong_adapter["adapter_version"] = "2.0.0"
    with pytest.raises(AssertionError):
        validate_response_envelope(wrong_adapter, request)
    wrong_descriptor = copy.deepcopy(response)
    wrong_descriptor["compatibility_descriptor"]["algorithm_versions"]["props"] = 2
    with pytest.raises(AssertionError):
        validate_response_envelope(wrong_descriptor, request)


def test_export_resolution_witness_uses_complete_source_census_and_coverage_only_rows() -> None:
    model = _model()
    validate_model(model)
    proof = _complete_proof(model)
    validate_proof(proof, model)
    assert {item["resolution"] for item in proof["export_observations"]} == {
        "component",
        "value",
        "type",
        "unknown",
    }
    assert model["coverage"]["non_component_value_export_count"] == 1
    assert model["coverage"]["type_only_export_count"] == 1
    assert proof["export_resolution_witness"] == expected_export_resolution_witness(model)

    for mutation in (
        "missing_observation",
        "duplicate_observation",
        "substituted_observation",
        "star_resolution_conflict",
        "value_resolution_conflict",
    ):
        candidate = copy.deepcopy(proof)
        if mutation == "missing_observation":
            candidate["export_observations"].pop()
        elif mutation == "duplicate_observation":
            candidate["export_observations"].append(
                copy.deepcopy(candidate["export_observations"][0])
            )
            candidate["export_observations"].sort(key=canonical_json_bytes)
        elif mutation == "substituted_observation":
            component = next(
                item
                for item in candidate["export_observations"]
                if item["resolution"] == "component"
            )
            component["component_id"] = _id("component", "6")
        else:
            if mutation == "star_resolution_conflict":
                star = next(item for item in candidate["export_observations"] if item["star"])
                star["resolution"] = "component"
                star["component_id"] = _id("component", "5")
            else:
                value = next(
                    item
                    for item in candidate["export_observations"]
                    if item["resolution"] == "value"
                )
                value["resolution"] = "unknown"
        with pytest.raises(AssertionError):
            validate_proof(candidate, model)

    for field in ("non_component_value_export_count", "type_only_export_count"):
        candidate = copy.deepcopy(model)
        candidate["coverage"][field] += 1
        with pytest.raises(AssertionError):
            validate_proof(_complete_proof(candidate), candidate)

    missing_binding = copy.deepcopy(model)
    missing_binding["members"] = [
        member for member in missing_binding["members"] if member["kind"] != "export_binding"
    ]
    missing_binding["coverage"]["counts"]["members"] -= 1
    missing_binding["coverage"]["counts"]["published"] -= 1
    missing_binding["coverage"]["counts"]["discovered"] -= 1
    with pytest.raises(AssertionError):
        validate_proof(_complete_proof(missing_binding), missing_binding)

    # Removing the same component observation, public binding, and coverage
    # record must still fail: the Python-owned source census is independent of
    # all three submitted projections.
    component_observation = next(
        item for item in proof["export_observations"] if item["resolution"] == "component"
    )
    component_member_id = next(
        member["id"]
        for member in model["members"]
        if member["kind"] == "export_binding"
        and member["owner_id"] == component_observation["owner_module_id"]
        and member["exported_name"] == component_observation["exported_name"]
    )
    coordinated_model = copy.deepcopy(model)
    coordinated_model["members"] = [
        member for member in coordinated_model["members"] if member["id"] != component_member_id
    ]
    for count_name in ("members", "published", "discovered"):
        coordinated_model["coverage"]["counts"][count_name] -= 1
    coordinated_proof = copy.deepcopy(proof)
    coordinated_proof["export_observations"] = [
        item
        for item in coordinated_proof["export_observations"]
        if item["syntax_identity"] != component_observation["syntax_identity"]
    ]
    coordinated_proof["export_resolution_witness"] = [
        item
        for item in coordinated_proof["export_resolution_witness"]
        if item["member_id"] != component_member_id
    ]
    coordinated_proof["discovered_records"] = [
        item
        for item in coordinated_proof["discovered_records"]
        if item["record"]["id"] != component_member_id
    ]
    with pytest.raises(AssertionError):
        validate_proof(coordinated_proof, coordinated_model)


def test_export_scanner_closes_unicode_bom_crlf_comments_and_reexport_forms() -> None:
    fixtures = load_export_census_fixture()
    assert any(item["content"].startswith(b"\xef\xbb\xbf") for item in fixtures)
    rows = scan_export_syntax_census()
    assert {row["syntax_kind"] for row in rows} == {
        "default_export",
        "named_export",
        "type_export",
        "reexport",
        "export_all",
    }
    assert any(row["role"] == "type" and row["reexport"] for row in rows)
    assert any(row["imported_name"] == "*" and row["star"] for row in rows)
    assert len(load_export_graph_fixture()) == 4
    unicode_row = next(row for row in rows if row["exported_name"] == "Unicode公開")
    assert unicode_row["owner_file_path"] == "src/ExportGrammar.tsx"
    assert unicode_row["byte_end"] > unicode_row["byte_start"]
    assert (
        unicode_row["byte_end"]
        <= next(
            item["content"] for item in fixtures if item["path"] == unicode_row["owner_file_path"]
        ).__len__()
    )
    assert len({row["token_identity"] for row in rows}) == len(rows)
    assert len({row["syntax_identity"] for row in rows}) == len(rows)


def test_export_scanner_is_module_level_and_handles_async_generics_and_false_positives() -> None:
    source = (
        b"const jsx = <div>export default false</div>;\n"
        b"const object = { export: 1 };\n"
        b"const member = object.export;\n"
        b"const regex = /export default/;\n"
        b'const text = "export default";\n'
        b"const template = `export default`;\n"
        b"// export default\n"
        b"export async function AsyncPage<T>() { return <span>export</span>; }\n"
        b"export default async function DefaultPage<T>() { return 1; }\n"
        b"export type Result<T> = { value: T };\n"
        b"export { type Result as PublicResult };\n"
    )
    rows = _scan_export_file("src/scanner.tsx", source)
    assert [(row["syntax_kind"], row["exported_name"], row["role"]) for row in rows] == [
        ("named_export", "AsyncPage", "value"),
        ("default_export", "default", "value"),
        ("type_export", "Result", "type"),
        ("named_export", "PublicResult", "type"),
    ]
    assert all(row["byte_end"] <= len(source) for row in rows)
    assert all(row["byte_start"] < row["byte_end"] for row in rows)
    with pytest.raises(AssertionError):
        _scan_export_file("src/invalid.ts", b"export const first = 1\nexport const second = 2;")
    with pytest.raises(AssertionError):
        _scan_export_file("src/invalid.ts", b'export * from "./other"')


def test_reexport_graph_recomputes_alias_star_cycle_and_conflict_witnesses() -> None:
    cases = {case["name"]: case for case in load_export_graph_cases()}
    assert set(cases) == {"alias", "conflict", "cycle", "star"}

    alias = recompute_export_graph_case(cases["alias"])
    alias_row = next(row for row in alias["exports"] if row["module_file_path"] == "src/index.ts")
    assert alias_row == {
        "module_file_path": "src/index.ts",
        "exported_name": "Alias",
        "source_file_path": "src/Button.tsx",
        "expanded_exported_name": "Button",
        "target_declaration_key": "Button",
        "resolution": "component",
        "reason": None,
    }
    assert alias["cycles"] == []
    assert alias["conflicts"] == []

    star = recompute_export_graph_case(cases["star"])
    star_rows = [row for row in star["witnesses"] if row["owner_file_path"] == "src/index.ts"]
    assert [row["exported_name"] for row in star_rows] == ["Card", "answer"]
    assert {row["resolution"] for row in star_rows} == {"component", "value"}
    assert all(row["exported_name"] != "default" for row in star_rows)

    cycle = recompute_export_graph_case(cases["cycle"])
    assert cycle["cycles"] == [
        {"module_file_path": "src/a.ts", "exported_name": "Loop"},
        {"module_file_path": "src/b.ts", "exported_name": "Loop"},
    ]
    assert all(row["resolution"] == "unknown" for row in cycle["witnesses"])
    assert all(row["diagnostic"] == "cycle" for row in cycle["witnesses"])

    conflict = recompute_export_graph_case(cases["conflict"])
    assert conflict["conflicts"] == [
        {"module_file_path": "src/index.ts", "exported_name": "Shared"}
    ]
    assert len(conflict["witnesses"]) == 2
    assert all(row["resolution"] == "unknown" for row in conflict["witnesses"])
    assert all(row["diagnostic"] == "conflict" for row in conflict["witnesses"])

    # A submitted witness cannot replace the independent result with a
    # component resolution, nor can it drop one of the two star edges.
    mutated = copy.deepcopy(conflict["witnesses"])
    mutated[0]["resolution"] = "component"
    assert mutated != conflict["witnesses"]
    assert len(conflict["witnesses"]) != 1


def test_main_reexport_witness_comes_from_raw_declarations_and_edges() -> None:
    raw = load_export_graph_raw_fixture()
    _validator("next-export-graph-raw-v1.schema.json").validate(
        {
            "schema": "code-structure-viz.next-export-graph-raw/v1",
            **raw,
        }
    )
    assert all(
        set(edge) == {"owner_file_path", "source_specifier", "imported_name", "exported_name"}
        for edge in raw["edges"]
    )
    result = recompute_export_graph_case(raw)
    star = [
        witness
        for witness in result["witnesses"]
        if witness["owner_file_path"] == "src/ExportReexport.ts" and witness["imported_name"] == "*"
    ]
    assert [witness["exported_name"] for witness in star] == [
        "LocalValue",
        "Props",
        "Unicode表示",
    ]
    model = _model()
    expected = expected_export_reexport_witness(model)
    assert expected == [
        {
            "syntax_identity": next(
                row
                for row in scan_export_syntax_census()
                if row["owner_file_path"] == "src/Button.tsx" and row["star"]
            )["syntax_identity"],
            "source_specifier": "./Other",
            "imported_name": "*",
            "resolved_source_module_id": None,
            "expanded_exported_name": None,
            "target_declaration_id": None,
            "resolution": "unknown",
        }
    ]
    mutated = copy.deepcopy(raw)
    mutated["edges"] = mutated["edges"][1:]
    assert recompute_export_graph_case(mutated) != result


def test_source_plan_descriptor_hashes_every_resolved_field_and_known_mutations() -> None:
    config = _config_projection()
    descriptor = config["source_plan"]
    _validator("next-source-plan-v1.schema.json").validate(descriptor)
    assert config["source_plan_digest"] == recompute_source_plan_digest(config)
    for field in ("local_extends", "resolved_control_paths", "file_role_map"):
        mutation = copy.deepcopy(config)
        if field == "local_extends":
            mutation["source_plan"][field] = [
                {"project_root": ".", "config_path": "tsconfig.json", "extends": ["base.json"]}
            ]
        elif field == "resolved_control_paths":
            mutation["source_plan"][field].append({"project_root": ".", "path": "vite.config.ts"})
            mutation["source_plan"][field].sort(key=canonical_json_bytes)
        else:
            mutation["source_plan"][field][0]["roles"] = ["program"]
            mutation["source_plan"][field][0]["effective_role"] = "program"
            mutation["source_plan"][field].sort(key=canonical_json_bytes)
        mutation["source_plan_digest"] = recompute_source_plan_digest(mutation)
        assert mutation["source_plan_digest"] != config["source_plan_digest"]

    # The remaining descriptor fields are closed v1 values, but they still
    # belong to the digest preimage.  Hashing a valid descriptor-shaped
    # mutation directly proves that no field is silently omitted from that
    # preimage without relaxing the v1 fixed-value validator.
    for field, replacement in (
        (
            "projects",
            [
                {
                    **descriptor["projects"][0],
                    "root": "workspace",
                    "source_roots": ["workspace/src"],
                    "config_path": "workspace/tsconfig.json",
                }
            ],
        ),
        ("program_suffixes", [".js", ".jsx", ".mjs", ".ts", ".tsx"]),
        ("context_suffixes", [".d.ts", ".d.mts"]),
        ("hard_exclusions", [*descriptor["hard_exclusions"], "vendor"]),
        ("limits", {**descriptor["limits"], "max_flow_visits": 10001}),
        ("trusted_environment_digest", "8" * 64),
    ):
        mutated_descriptor = copy.deepcopy(descriptor)
        mutated_descriptor[field] = replacement
        assert digest(mutated_descriptor) != digest(descriptor)


def test_project_surface_order_is_root_path_while_semantic_records_remain_id_order() -> None:
    first = _project()
    first["root"] = "zeta"
    first["source_roots"] = ["zeta/src"]
    first["config_path"] = "zeta/tsconfig.json"
    first["id"] = recompute_record_id(first)
    first["config_digest"] = project_config_digest(first)
    second = _project()
    second["root"] = "alpha"
    second["source_roots"] = ["alpha/src"]
    second["config_path"] = "alpha/tsconfig.json"
    second["id"] = recompute_record_id(second)
    second["config_digest"] = project_config_digest(second)
    assert [
        project["root"] for project in sorted((first, second), key=lambda item: item["root"])
    ] != [
        project["root"] for project in sorted((first, second), key=lambda item: item["id"])
    ]  # path order and ID order intentionally differ
    config_a = _config_projection(projects=[first, second])
    config_b = _config_projection(projects=[second, first])
    assert [project["root"] for project in config_a["projects"]] == ["alpha", "zeta"]
    assert config_a["projects"] == config_b["projects"]
    assert config_a["source_plan_digest"] == config_b["source_plan_digest"]
    assert config_a["domain_config_digest"] == config_b["domain_config_digest"]
    assert [project["root"] for project in config_a["source_plan"]["projects"]] == [
        "alpha",
        "zeta",
    ]


def test_public_targets_are_path_only_and_resolve_frozen_file_or_directory_sets() -> None:
    model = _model()
    all_records = {collection: list(model[collection]) for collection in COLLECTIONS}
    file_target = resolve_target_resolutions(["path:src/Button.tsx"], all_records)
    assert file_target == [
        {
            "target_key": "path:src/Button.tsx",
            "status": "resolved",
            "record_ids": sorted([_id("file", "1"), _id("module", "3"), _id("component", "5")]),
        }
    ]
    directory_target = resolve_target_resolutions(["path:src"], all_records)
    assert directory_target == [
        {
            "target_key": "path:src",
            "status": "resolved",
            "record_ids": sorted(
                [
                    _id("file", "1"),
                    _id("file", "2"),
                    _id("file", "c"),
                    _id("module", "3"),
                    _id("module", "4"),
                    _id("component", "5"),
                    _id("component", "6"),
                ]
            ),
        }
    ]
    assert resolve_target_resolutions(["path:src/Missing.tsx"], all_records) == [
        {"target_key": "path:src/Missing.tsx", "status": "failed", "record_ids": []}
    ]
    assert resolve_target_resolutions(["path:src/types.d.ts"], all_records) == [
        {"target_key": "path:src/types.d.ts", "status": "failed", "record_ids": []}
    ]
    control_records = {collection: list(records) for collection, records in all_records.items()}
    for digit, control_path in (
        ("p", "package.json"),
        ("t", "tsconfig.json"),
        ("j", "jsconfig.json"),
    ):
        control_records["files"].append(_file(digit, control_path, "control", b"{}\n"))
    control_records["files"].sort(key=lambda record: record["id"])
    for control_path in ("package.json", "tsconfig.json", "jsconfig.json"):
        target_key = "path:" + control_path
        assert resolve_target_resolutions([target_key], control_records) == [
            {"target_key": target_key, "status": "failed", "record_ids": []}
        ]
    unavailable = resolve_target_resolutions(
        ["path:src/Button.tsx"],
        all_records,
        unavailable_record_ids={_id("component", "5")},
    )
    assert unavailable == [
        {"target_key": "path:src/Button.tsx", "status": "failed", "record_ids": []}
    ]
    for target in (
        "component:" + _id("component", "5"),
        "module:" + _id("module", "3"),
        "file:" + _id("file", "1"),
        "path:../escape.tsx",
        "path:/absolute.tsx",
        "path:src\\Button.tsx",
        "path:src/Button.tsx#fragment",
    ):
        with pytest.raises(AssertionError):
            canonical_target_key(target)
        with pytest.raises(ValidationError):
            _validator("next-config-v1.schema.json").validate(_config_projection(targets=[target]))

    multi_target_model = _model()
    multi_target_proof = _complete_proof(multi_target_model)
    requested_targets = ["path:src", "path:src/Button.tsx"]
    resolutions = resolve_target_resolutions(requested_targets, multi_target_model)
    multi_target_proof["target_resolutions"] = resolutions
    multi_target_model["coverage"]["target_completeness"] = [
        {
            "target_key": item["target_key"],
            "status": "complete",
            "record_ids": item["record_ids"],
        }
        for item in resolutions
    ]
    validate_proof(multi_target_proof, multi_target_model, request_targets=requested_targets)
    permuted_targets = copy.deepcopy(multi_target_proof)
    permuted_targets["target_resolutions"].reverse()
    with pytest.raises(AssertionError):
        validate_proof(permuted_targets, multi_target_model, request_targets=requested_targets)
    permuted_coverage = copy.deepcopy(multi_target_proof)
    permuted_coverage_model = copy.deepcopy(multi_target_model)
    permuted_coverage_model["coverage"]["target_completeness"].reverse()
    with pytest.raises(AssertionError):
        validate_proof(
            permuted_coverage,
            permuted_coverage_model,
            request_targets=requested_targets,
        )


def test_taint_edges_are_derived_for_boundary_and_shared_frontier() -> None:
    model = _model()
    boundary_relation: dict[str, Any] = {
        "kind": "static_import",
        "id": "",
        "source_id": _id("module", "4"),
        "target": {"kind": "internal", "module_id": _id("module", "3")},
        "role": "value",
        "reexport": False,
        "boundary_effect": "server_to_client_entry",
    }
    boundary_relation["id"] = recompute_record_id(boundary_relation)
    model["relations"].append(boundary_relation)
    model["relations"].sort(key=lambda record: record["id"])
    model["coverage"]["counts"]["relations"] += 1
    model["coverage"]["counts"]["published"] += 1
    model["coverage"]["counts"]["discovered"] += 1
    model["modules"][1]["derived_roles"] = ["server_candidate"]
    validate_model(model)

    proof = _complete_proof(model)
    proof["failure_roots"] = [
        {
            "id": "next:failure:" + "b" * 64,
            "collection": "modules",
            "kind": "boundary_derivation",
            "path_ref": None,
            "record_ids": [_id("module", "4")],
        }
    ]
    discovered = _discovered_index(proof)
    edges = derive_required_causal_edges(proof, discovered)
    _materialize_single_root_taints(proof)
    tainted = _derived_taint_fixed_point(proof, discovered)
    assert boundary_relation["id"] in tainted
    assert {
        (edge["rule"], edge["record_id"])
        for edge in edges
        if edge["source_id"] == proof["failure_roots"][0]["id"]
    } == {("boundary_closure", _id("module", "4"))}
    assert any(
        edge["rule"] == "boundary_closure" and edge["record_id"] == boundary_relation["id"]
        for edge in edges
    )
    omitted_boundary_edge = copy.deepcopy(proof)
    omitted_boundary_edge["causal_edges"] = [
        edge
        for edge in omitted_boundary_edge["causal_edges"]
        if not (edge["rule"] == "boundary_closure" and edge["record_id"] == boundary_relation["id"])
    ]
    with pytest.raises(AssertionError):
        _derived_taint_fixed_point(omitted_boundary_edge, discovered)

    shared_frontier = {
        edge["record_id"] for edge in edges if edge["record_id"] == _id("module", "3")
    }
    assert shared_frontier == {_id("module", "3")}


def test_export_root_seeds_include_target_barrel_and_consumer_records() -> None:
    model = _model()
    barrel_module: dict[str, Any] = {
        "kind": "module",
        "id": "",
        "project_id": _id("project", "0"),
        "path": "src/index.ts",
        "router_context": "none",
        "client_entry": False,
        "derived_roles": [],
    }
    barrel_module["id"] = recompute_record_id(barrel_module)
    consumer_module: dict[str, Any] = {
        "kind": "module",
        "id": "",
        "project_id": _id("project", "0"),
        "path": "src/consumer.tsx",
        "router_context": "none",
        "client_entry": False,
        "derived_roles": [],
    }
    consumer_module["id"] = recompute_record_id(consumer_module)
    barrel_export: dict[str, Any] = {
        "kind": "export_binding",
        "id": "",
        "owner_id": barrel_module["id"],
        "exported_name": "Button",
        "role": "value",
        "target_component_id": _id("component", "5"),
        "resolution_kind": "component",
        "reexport": True,
    }
    barrel_export["id"] = recompute_record_id(barrel_export)
    incoming_reexport: dict[str, Any] = {
        "kind": "static_import",
        "id": "",
        "source_id": barrel_module["id"],
        "target": {"kind": "internal", "module_id": _id("module", "3")},
        "role": "value",
        "reexport": True,
        "boundary_effect": "none",
    }
    incoming_reexport["id"] = recompute_record_id(incoming_reexport)
    consumer_binding: dict[str, Any] = {
        "kind": "import_binding",
        "id": "",
        "owner_id": consumer_module["id"],
        "local_component_id": _id("component", "5"),
        "imported_name": "Button",
        "role": "value",
        "source": {"kind": "internal", "module_id": _id("module", "3")},
    }
    consumer_binding["id"] = recompute_record_id(consumer_binding)
    proof = _complete_proof(model)
    proof["discovered_records"].extend(
        [
            {"collection": "modules", "record": barrel_module, "taints": []},
            {"collection": "modules", "record": consumer_module, "taints": []},
            {"collection": "members", "record": barrel_export, "taints": []},
            {"collection": "members", "record": consumer_binding, "taints": []},
            {"collection": "relations", "record": incoming_reexport, "taints": []},
        ]
    )
    records = _discovered_index(proof)
    root = {
        "id": "next:failure:" + "c" * 64,
        "collection": "members",
        "kind": "export_binding",
        "path_ref": "src/Button.tsx",
        "record_ids": [],
    }
    expected_seed_ids = sorted(
        {
            _id("module", "3"),
            _id("member", "7"),
            _id("component", "5"),
            barrel_module["id"],
            consumer_module["id"],
            barrel_export["id"],
            incoming_reexport["id"],
            consumer_binding["id"],
        }
    )
    root["record_ids"] = expected_seed_ids
    proof["failure_roots"] = [root]
    edges = derive_required_causal_edges(proof, records)
    assert edges
    for omitted in (
        _id("component", "5"),
        barrel_module["id"],
        consumer_binding["id"],
    ):
        under_tainted = copy.deepcopy(proof)
        under_tainted["failure_roots"][0]["record_ids"].remove(omitted)
        with pytest.raises(AssertionError):
            derive_required_causal_edges(under_tainted, records)
    excess = copy.deepcopy(proof)
    excess["failure_roots"][0]["record_ids"].append(_id("module", "4"))
    excess["failure_roots"][0]["record_ids"].sort()
    with pytest.raises(AssertionError):
        derive_required_causal_edges(excess, records)


def test_limits_are_one_resolved_record_across_all_projections() -> None:
    limits = _next_limits()
    validate_limits(limits)
    domain = _domain()
    validate_limits_consistency(
        limits,
        _semantic(_model())["request"]["limits"],
        _response(_model())["limits"],
        domain["limits"],
        domain["config"]["limits"],
    )
    mutated = copy.deepcopy(limits)
    mutated["max_flow_visits"] += 1
    with pytest.raises(AssertionError):
        validate_limits_consistency(limits, mutated)


def test_every_normative_limit_has_an_inclusive_arithmetic_boundary() -> None:
    limits = _next_limits()
    assert set(LIMIT_CONTRACTS) == set(limits)
    for name, contract in LIMIT_CONTRACTS.items():
        limit = limits[name]
        assert contract["encoding"] in {"utf8", "not_applicable"}
        assert contract["inclusive"] is True
        assert contract["outcome"] in {"partial_safe", "payload_unavailable"}
        assert_limit_boundary(limit, at_limit=True, over_limit=False)


def test_entity_and_record_budgets_use_distinct_non_allocating_counters() -> None:
    internal_model = {
        "modules": [None] * 250,
        "components": [None] * 250,
    }
    assert internal_entity_count(internal_model) == 500
    assert entity_budget_allowed(500, 500)
    assert not entity_budget_allowed(501, 500)
    assert entity_budget_allowed(501, 600)

    # 99,500 non-Module/Component records can coexist with 500 published
    # internal entities at the all-record boundary.
    assert model_record_budget_allowed(500 + 99_500, 100_000)
    assert not model_record_budget_allowed(500 + 99_501, 100_000)
    assert not model_record_budget_allowed(100_001, 100_000)


def test_role_precedence_and_exact_encoded_request_boundaries_cover_every_subset() -> None:
    request = _request()
    assert encoded_request_bytes(request) == canonical_json_bytes(request)
    measured = len(encoded_request_bytes(request))
    assert validate_encoded_stdin_size(request) == measured
    limit = request["limits"]["max_encoded_stdin_bytes"]
    assert_encoded_stdin_boundary(limit - 1, limit, True)
    assert_encoded_stdin_boundary(limit, limit, True)
    assert_encoded_stdin_boundary(limit + 1, limit, False)

    for size in range(1, len(ROLE_ORDER) + 1):
        for subset in combinations(ROLE_ORDER, size):
            candidate = copy.deepcopy(request)
            roles = sorted(subset, key=ROLE_ORDER.__getitem__)
            candidate["files"][0]["roles"] = roles
            candidate["files"][0]["effective_role"] = max(roles, key=ROLE_PRECEDENCE.__getitem__)
            candidate["request_id"] = recompute_request_id(candidate)
            validate_request_envelope(candidate)

    wrong = copy.deepcopy(request)
    wrong["files"][0]["roles"] = ["control", "program"]
    wrong["files"][0]["effective_role"] = "program"
    wrong["request_id"] = recompute_request_id(wrong)
    with pytest.raises(AssertionError):
        validate_request_envelope(wrong)


def test_run_fingerprint_preimage_includes_limits_and_toolchain() -> None:
    domain = _domain()
    fingerprint = recompute_run_fingerprint(
        source_view_fingerprint=domain["source"]["fingerprint"],
        source_plan_digest=domain["source_plan_digest"],
        domain_config_digest=domain["domain_config_digest"],
        projects=domain["projects"],
        targets=domain["targets"],
        limits=domain["limits"],
        node_version=domain["toolchain"]["node_version"],
        typescript_version=domain["toolchain"]["typescript_version"],
        adapter_version=domain["toolchain"]["adapter_version"],
        protocol=domain["toolchain"]["protocol"],
        trusted_environment_digest=domain["trusted_environment"]["sha256"],
    )
    assert fingerprint == domain["run_fingerprint"]
    changed = copy.deepcopy(domain["limits"])
    changed["max_flow_visits"] += 1
    assert (
        recompute_run_fingerprint(
            source_view_fingerprint=domain["source"]["fingerprint"],
            source_plan_digest=domain["source_plan_digest"],
            domain_config_digest=domain["domain_config_digest"],
            projects=domain["projects"],
            targets=domain["targets"],
            limits=changed,
            node_version=domain["toolchain"]["node_version"],
            typescript_version=domain["toolchain"]["typescript_version"],
            adapter_version=domain["toolchain"]["adapter_version"],
            protocol=domain["toolchain"]["protocol"],
            trusted_environment_digest=domain["trusted_environment"]["sha256"],
        )
        != fingerprint
    )


def test_next_diagnostic_catalog_is_the_public_and_manifest_authority() -> None:
    catalog = _schema("next-diagnostic-catalog-v1.json")
    assert catalog["domain"] == "next"
    entries = cast(list[dict[str, Any]], catalog["entries"])
    assert len(entries) == 26
    assert len({entry["code"] for entry in entries}) == len(entries)
    validator = _validator("diagnostic-v1.schema.json")
    for entry in entries:
        value = _public_diagnostic(entry["code"])
        validator.validate(value)
        assert value["message"] == entry["message"]
        assert value["severity"] == entry["severity"]
        assert value["recoverable"] is entry["recoverable"]
        assert value["outcome"] == entry["outcome"]
        assert value["ref_permission"] == entry["ref_permission"]
        wrong_metadata = copy.deepcopy(value)
        wrong_metadata["outcome"] = "complete" if value["outcome"] != "complete" else "fatal"
        with pytest.raises(ValidationError):
            validator.validate(wrong_metadata)
        permission = entry["ref_permission"]
        if permission == "none":
            wrong_reference = copy.deepcopy(value)
            wrong_reference["path"] = "src/Button.tsx"
            with pytest.raises(ValidationError):
                validator.validate(wrong_reference)
        elif permission == "path":
            wrong_reference = copy.deepcopy(value)
            wrong_reference["path"] = None
            with pytest.raises(ValidationError):
                validator.validate(wrong_reference)
        elif permission == "symbol":
            wrong_reference = copy.deepcopy(value)
            wrong_reference["symbol"] = None
            with pytest.raises(ValidationError):
                validator.validate(wrong_reference)
        else:
            assert permission == "path_or_symbol"
            wrong_reference = copy.deepcopy(value)
            wrong_reference["path"] = None
            wrong_reference["symbol"] = None
            with pytest.raises(ValidationError):
                validator.validate(wrong_reference)
            both_references = copy.deepcopy(value)
            both_references["symbol"] = _id("component", "5")
            with pytest.raises(ValidationError):
                validator.validate(both_references)
    manifest = _run_manifest(_domain("not_applicable"))
    _validator("run-manifest-v1.schema.json").validate(manifest)
    assert manifest["domains"][0]["diagnostics"][0]["code"] == "CSV-NEXT-APPLICABILITY-001"


@pytest.mark.parametrize("status", ["complete", "not_applicable", "incomplete"])
def test_next_run_manifest_status_matrix_and_public_stream_extensions(status: str) -> None:
    domain = _domain(status)
    validate_domain_manifest(domain)
    manifest = _run_manifest(domain)
    validate_run_manifest(manifest, domain, _published_bytes(domain))
    _validator("next-domain-manifest-v1.schema.json").validate(domain)
    _validator("run-manifest-v1.schema.json").validate(manifest)
    summary: dict[str, Any] = {
        "type": "run_summary",
        "schema": "code-structure-viz.run-summary/v1",
        "run_status": status,
        "exit_code": 0 if status in {"complete", "not_applicable"} else 3,
        "domains": [
            {
                "domain": "next",
                "status": status,
                **(
                    {"incomplete_kind": domain["incomplete_kind"]} if status == "incomplete" else {}
                ),
            }
        ],
        "manifest": "run-manifest.json",
    }
    published = _published_bytes(domain)
    for selector in ("next:semantic-json", "next:plantuml"):
        _validator("run-summary-v1.schema.json").validate(summary)
        stream = _stdout_result_for_domain(domain, manifest, selector)
        _validator("stdout-result-v1.schema.json").validate(stream)
        stream_bytes = (
            published[
                "next.snapshot.semantic.json"
                if selector.endswith("semantic-json")
                else "next.snapshot.puml"
            ]
            if stream["availability"]
            else canonical_json_bytes(stream) + b"\n"
        )
        validate_run_status_vector(
            manifest,
            summary,
            stream,
            published,
            stream_bytes,
            manifest["diagnostics"],
        )


def test_next_non_empty_run_manifest_discriminates_path_targets_and_projections() -> None:
    domain = _domain(targets=["path:src", "path:src/Button.tsx"])
    manifest = _run_manifest(domain)
    validate_domain_manifest(domain)
    validate_run_manifest(manifest, domain, _published_bytes(domain))
    _validator("run-manifest-v1.schema.json").validate(manifest)
    assert manifest["request"]["targets"] == manifest["next_request"]["targets"]
    assert manifest["request"]["targets"] == manifest["config"]["resolved"]["next"]["targets"]
    assert manifest["request"]["targets"] == manifest["domains"][0]["targets"]

    mutations: list[tuple[dict[str, Any], bool]] = []
    object_target = copy.deepcopy(manifest)
    object_target["request"]["targets"] = [{"kind": "path", "value": "src/Button.tsx"}]
    mutations.append((object_target, True))
    mixed_targets = copy.deepcopy(manifest)
    mixed_targets["request"]["targets"] = [
        "path:src",
        {"kind": "path", "value": "src/Button.tsx"},
    ]
    mutations.append((mixed_targets, True))
    old_target = copy.deepcopy(manifest)
    old_target["request"]["targets"] = ["module:" + _id("module", "3")]
    mutations.append((old_target, True))
    class_target = copy.deepcopy(manifest)
    class_target["request"]["targets"] = ["class:src.Button"]
    mutations.append((class_target, True))
    module_object_target = copy.deepcopy(manifest)
    module_object_target["request"]["targets"] = [{"kind": "module", "value": "src.Button"}]
    mutations.append((module_object_target, True))
    permuted = copy.deepcopy(manifest)
    permuted["request"]["targets"].reverse()
    mutations.append((permuted, False))
    duplicate = copy.deepcopy(manifest)
    duplicate["request"]["targets"].append("path:src")
    mutations.append((duplicate, True))
    for mutation, schema_rejects in mutations:
        with pytest.raises((AssertionError, ValidationError)):
            validate_run_manifest(mutation, domain, _published_bytes(domain))
        if schema_rejects:
            with pytest.raises(ValidationError):
                _validator("run-manifest-v1.schema.json").validate(mutation)


@pytest.mark.parametrize(
    ("status", "overrun"),
    [
        ("complete", False),
        ("not_applicable", False),
        ("incomplete", False),
        ("incomplete", True),
    ],
)
@pytest.mark.parametrize(
    "selector",
    [None, "manifest", "next:semantic-json", "next:plantuml"],
)
def test_next_stdout_matrix_has_exact_bytes_for_core_outcomes(
    status: str, overrun: bool, selector: str | None
) -> None:
    domain = _domain(status, overrun=overrun)
    manifest = _run_manifest(domain)
    published = _published_bytes(domain)
    validate_domain_manifest(domain)
    validate_run_manifest(manifest, domain, published)
    summary = _run_summary_value(status, domain)
    _validator("run-summary-v1.schema.json").validate(summary)
    _validator("run-manifest-v1.schema.json").validate(manifest)

    if selector is None:
        stdout = canonical_json_bytes(summary) + b"\n"
    elif selector == "manifest":
        stdout = canonical_json_bytes(manifest) + b"\n"
    else:
        stream = _stdout_result_for_domain(domain, manifest, selector)
        _validator("stdout-result-v1.schema.json").validate(stream)
        if stream["availability"]:
            artifact_path = (
                "next.snapshot.semantic.json"
                if selector.endswith("semantic-json")
                else "next.snapshot.puml"
            )
            stdout = published[artifact_path]
        else:
            stdout = canonical_json_bytes(stream) + b"\n"
        validate_run_status_vector(
            manifest,
            summary,
            stream,
            published,
            stdout,
            manifest["diagnostics"],
        )
    assert stdout.endswith(b"\n")
    stderr = _diagnostic_jsonl(manifest["diagnostics"])
    assert stderr == _diagnostic_jsonl(sorted(manifest["diagnostics"], key=canonical_json_bytes))
    assert stderr == _diagnostic_jsonl(domain["diagnostics"])


@pytest.mark.parametrize("run_status", ["fatal", "interrupted"])
@pytest.mark.parametrize(
    "selector",
    [None, "manifest", "next:semantic-json", "next:plantuml"],
)
def test_next_stdout_matrix_is_manifest_free_for_fatal_and_interrupt(
    run_status: str, selector: str | None
) -> None:
    summary = _run_summary_value(run_status)
    _validator("run-summary-v1.schema.json").validate(summary)
    if selector is None:
        stdout = canonical_json_bytes(summary) + b"\n"
    else:
        stable_reason = (
            "run_interrupted"
            if run_status == "interrupted"
            else "final_manifest_unavailable"
            if selector == "manifest"
            else "run_fatal"
        )
        stream: dict[str, Any] = {
            "type": "stdout_result",
            "schema": "code-structure-viz.stdout-result/v1",
            "selector": selector,
            "availability": False,
            "run_status": run_status,
            "stable_reason": stable_reason,
            "artifact": None,
        }
        _validator("stdout-result-v1.schema.json").validate(stream)
        stdout = canonical_json_bytes(stream) + b"\n"
        validate_run_status_vector(None, summary, stream, {}, stdout, [])
    assert stdout.endswith(b"\n")


@pytest.mark.parametrize(
    "selector",
    [None, "manifest", "next:semantic-json", "next:plantuml"],
)
def test_next_stdout_matrix_usage_is_empty_and_manifest_free(selector: str | None) -> None:
    summary = _run_summary_value("usage")
    _validator("run-summary-v1.schema.json").validate(summary)
    selected = (
        None
        if selector is None
        else ManifestSelector()
        if selector == "manifest"
        else DomainFormatSelector(
            domain="next",
            format=selector.removeprefix("next:"),  # type: ignore[arg-type]
        )
    )
    assert StdoutEmitter().render(RunOutcome.usage(), selected, ROOT) == b""
    validate_run_status_vector(None, summary, None, {}, b"", [])


def test_entity_budget_overrun_is_payload_unavailable_without_artifacts() -> None:
    domain = _domain("incomplete", overrun=True)
    validate_domain_manifest(domain)
    _validator("next-domain-manifest-v1.schema.json").validate(domain)
    manifest = _run_manifest(domain)
    validate_run_manifest(manifest, domain, _published_bytes(domain))
    _validator("run-manifest-v1.schema.json").validate(manifest)
    assert domain["budget"]["actual"] > domain["budget"]["resolved"]
    assert domain["artifact_paths"] == []
    assert domain["payload_available"] is False
    summary: dict[str, Any] = {
        "type": "run_summary",
        "schema": "code-structure-viz.run-summary/v1",
        "run_status": "incomplete",
        "exit_code": 3,
        "domains": [
            {
                "domain": "next",
                "status": "incomplete",
                "incomplete_kind": "payload_unavailable",
            }
        ],
        "manifest": "run-manifest.json",
    }
    stream = _stdout_result_for_domain(domain, manifest)
    _validator("run-summary-v1.schema.json").validate(summary)
    _validator("stdout-result-v1.schema.json").validate(stream)
    validate_run_status_vector(
        manifest,
        summary,
        stream,
        _published_bytes(domain),
        canonical_json_bytes(stream) + b"\n",
        manifest["diagnostics"],
    )


def test_direct_context_target_is_manifest_and_stdout_payload_unavailable() -> None:
    domain = _domain("incomplete", targets=["path:src/types.d.ts"])
    domain["payload_available"] = False
    domain["entity_count"] = None
    domain["incomplete_kind"] = "payload_unavailable"
    domain["artifact_paths"] = []
    domain["budget"]["actual"] = None
    domain["budget"]["outcome"] = "payload_unavailable"
    domain["diagnostics"] = [_public_diagnostic("CSV-NEXT-TARGET-001", path="src/types.d.ts")]
    validate_domain_manifest(domain)
    manifest = _run_manifest(domain)
    published: dict[str, bytes] = {}
    validate_run_manifest(manifest, domain, published)
    _validator("next-domain-manifest-v1.schema.json").validate(domain)
    _validator("run-manifest-v1.schema.json").validate(manifest)
    stream = _stdout_result_for_domain(domain, manifest, "next:semantic-json")
    _validator("stdout-result-v1.schema.json").validate(stream)
    assert stream["availability"] is False
    assert stream["artifact"] is None
    assert stream["domain_status"] == "incomplete"
    assert canonical_json_bytes(stream) + b"\n" == (
        b'{"artifact":null,"availability":false,"domain_status":"incomplete",'
        b'"schema":"code-structure-viz.stdout-result/v1",'
        b'"selector":"next:semantic-json","stable_reason":"domain_payload_unavailable",'
        b'"type":"stdout_result"}\n'
    )


def test_entity_budget_gate_composes_entity_and_model_record_boundaries() -> None:
    for actual, resolved, allowed in ((500, 500, True), (501, 500, False), (501, 600, True)):
        outcome = entity_budget_gate(
            actual,
            resolved,
            original_outcome="complete",
            requested_formats=["semantic-json", "plantuml"],
        )
        assert outcome["actual"] == actual
        assert outcome["resolved"] == resolved
        assert outcome["allowed"] is allowed
        assert outcome["payload_available"] is allowed
        assert outcome["original_outcome"] == "complete"
        assert outcome["outcome"] == ("complete" if allowed else "payload_unavailable")
        assert outcome["diagnostic_code"] == (None if allowed else "CSV-NEXT-LIMIT-005")
        assert outcome["artifact_paths"] == (
            ["next.snapshot.semantic.json", "next.snapshot.puml"] if allowed else []
        )
    assert model_record_budget_allowed(100000, 100000)
    assert not model_record_budget_allowed(100001, 100000)


def test_entity_budget_gate_preserves_partial_safe_and_overrun_is_unavailable() -> None:
    partial = entity_budget_gate(
        500,
        500,
        original_outcome="partial_safe",
        requested_formats=["semantic-json"],
    )
    assert partial["allowed"] is True
    assert partial["payload_available"] is True
    assert partial["original_outcome"] == "partial_safe"
    assert partial["outcome"] == "partial_safe"
    overridden = entity_budget_gate(
        501,
        600,
        original_outcome="partial_safe",
        requested_formats=["plantuml"],
    )
    assert overridden["allowed"] is True
    assert overridden["outcome"] == "partial_safe"
    overrun = entity_budget_gate(
        501,
        500,
        original_outcome="partial_safe",
        requested_formats=["semantic-json", "plantuml"],
    )
    assert overrun["allowed"] is False
    assert overrun["payload_available"] is False
    assert overrun["outcome"] == "payload_unavailable"
    assert overrun["original_outcome"] == "partial_safe"


@pytest.mark.parametrize(
    ("formats", "expected_paths"),
    [
        (["semantic-json"], ["next.snapshot.semantic.json"]),
        (["plantuml"], ["next.snapshot.puml"]),
        (["semantic-json", "plantuml"], ["next.snapshot.semantic.json", "next.snapshot.puml"]),
    ],
)
def test_entity_budget_gate_publishes_only_requested_formats(
    formats: list[str], expected_paths: list[str]
) -> None:
    decision = entity_budget_gate(
        4,
        500,
        original_outcome="complete",
        requested_formats=formats,
    )
    assert decision["requested_formats"] == formats
    assert decision["artifact_paths"] == expected_paths


def test_round10_path_value_contract_rejects_aliases_and_counts_path_bytes() -> None:
    assert canonical_target_key("path:.") == "path:."
    assert canonical_target_key("path:src/Button.tsx") == "path:src/Button.tsx"
    accepted = "a" * 4096
    assert canonical_target_key(f"path:{accepted}") == f"path:{accepted}"
    for invalid in (
        "path:",
        "path:a//b",
        "path:a/./b",
        "path:a/../b",
        "path:a/",
        "path:a\\b",
        "path:a\x00b",
        "path:e\u0301.txt",
        f"path:{accepted}a",
    ):
        with pytest.raises(AssertionError):
            canonical_target_key(invalid)


def test_program_file_requires_exactly_one_module_for_file_and_directory_targets() -> None:
    model = _model()
    model["modules"] = [module for module in model["modules"] if module["path"] != "src/Card.tsx"]
    model["modules"].sort(key=lambda record: record["id"])
    resolution = resolve_target_resolutions(["path:src/Card.tsx"], model)
    assert resolution == [{"target_key": "path:src/Card.tsx", "status": "failed", "record_ids": []}]
    directory_resolution = resolve_target_resolutions(["path:src"], model)
    assert directory_resolution == [
        {"target_key": "path:src", "status": "failed", "record_ids": []}
    ]
    with pytest.raises(AssertionError):
        validate_model(model)


def test_array_and_adapter_stderr_limits_have_independent_incremental_boundaries() -> None:
    aggregate_limit = 100000
    assert count_array_items_before_materialization(
        [50000, 50000], max_total_array_items=aggregate_limit
    )["allowed"]
    aggregate_overrun = count_array_items_before_materialization(
        [50000, 50000, 1], max_total_array_items=aggregate_limit
    )
    assert aggregate_overrun == {
        "allowed": False,
        "total": 100001,
        "failed_at": 2,
        "reason": "max_total_array_items",
    }
    assert count_array_items_before_materialization(
        [20000, 20000], max_array_items=20000, max_total_array_items=100000
    )["allowed"]
    capture_limit = 65536
    assert capture_adapter_stderr([b"a" * capture_limit])["allowed"]
    exceeded = capture_adapter_stderr([b"a" * capture_limit, b"b"])
    assert exceeded["allowed"] is False
    assert exceeded["captured_bytes"] == capture_limit + 1
    assert exceeded["process_group_terminated"] is True
    assert exceeded["raw_disposed"] is True
    assert exceeded["partial_disposed"] is True
    assert exceeded["manifest_stderr_bytes"] == 0
    assert exceeded["diagnostic_code"] == "CSV-NEXT-LIMIT-003"


def test_public_diagnostic_stderr_is_utf8_jsonl_all_or_none() -> None:
    diagnostic = _public_diagnostic("CSV-NEXT-TARGET-001", path="src/表示.tsx")
    gate = render_public_diagnostic_stderr([diagnostic], limit=10_000)
    assert gate["allowed"] is True
    assert gate["encoded_bytes"] == len(gate["payload"])
    assert gate["emitted_bytes"] == gate["encoded_bytes"]
    assert gate["partial_write_bytes"] == 0
    assert gate["manifest_diagnostics"] == [diagnostic]
    assert gate["payload"].endswith(b"\n")

    exact = render_public_diagnostic_stderr([diagnostic], limit=gate["encoded_bytes"])
    assert exact["allowed"] is True
    over = render_public_diagnostic_stderr([diagnostic], limit=gate["encoded_bytes"] - 1)
    assert over["allowed"] is False
    assert over["encoded_bytes"] == gate["encoded_bytes"]
    assert over["emitted_bytes"] == 0
    assert over["partial_write_bytes"] == 0
    assert over["payload"] == b""
    assert over["raw_disposed"] is True
    assert over["partial_disposed"] is True
    assert over["manifest_only"] is True
    assert over["diagnostic_code"] == "CSV-NEXT-LIMIT-003"
    assert [item["code"] for item in over["manifest_diagnostics"]] == ["CSV-NEXT-LIMIT-003"]


def test_bounded_decoder_rejects_duplicates_depth_strings_and_aggregate_before_materializing() -> (
    None
):
    allowed = bounded_decode_json(b'{"items":[1,2],"nested":{"ok":true}}')
    assert allowed["allowed"] is True
    assert allowed["materialized"] is False
    duplicate = bounded_decode_json(b'{"items":1,"items":2}')
    assert duplicate["allowed"] is False
    assert duplicate["reason"] == "duplicate_object_key"

    nested = bounded_decode_json(b"[" * 65 + b"0" + b"]" * 65)
    assert nested["allowed"] is False
    assert nested["reason"] == "max_json_nesting"
    long_string = bounded_decode_json(b'{"value":"abcd"}', limits={"max_json_string_bytes": 3})
    assert long_string["allowed"] is False
    assert long_string["reason"] == "max_json_string_bytes"
    per_array = bounded_decode_json(b"[0,1,2]", limits={"max_array_items": 2})
    assert per_array["allowed"] is False
    assert per_array["reason"] == "max_array_items"

    aggregate_payload = (
        b'{"first":['
        + b"0," * 50_000
        + b"0],"
        + b'"second":['
        + b"0," * 49_999
        + b"0],"
        + b'"last":[0]}'
    )
    aggregate = bounded_decode_json(aggregate_payload)
    assert aggregate["allowed"] is False
    assert aggregate["reason"] == "max_total_array_items"
    assert aggregate["total_array_items"] == 100_001
    assert aggregate["materialized"] is False


def test_whole_run_validator_rejects_projection_and_artifact_mutations() -> None:
    domain = _domain()
    manifest = _run_manifest(domain)
    published = _published_bytes(domain)
    validate_run_manifest(manifest, domain, published)

    wrong_config = copy.deepcopy(manifest)
    wrong_config["next_config"]["limits"]["max_flow_visits"] += 1
    with pytest.raises(AssertionError):
        validate_run_manifest(wrong_config, domain, published)

    wrong_request = copy.deepcopy(manifest)
    wrong_request["request"]["formats"] = ["plantuml"]
    with pytest.raises(AssertionError):
        validate_run_manifest(wrong_request, domain, published)

    wrong_artifact = copy.deepcopy(manifest)
    wrong_artifact["artifacts"][0]["sha256"] = "0" * 64
    with pytest.raises(AssertionError):
        validate_run_manifest(wrong_artifact, domain, published)

    wrong_diagnostic = copy.deepcopy(manifest)
    wrong_diagnostic["diagnostics"] = [_public_diagnostic("CSV-NEXT-FLOW-001")]
    with pytest.raises(AssertionError):
        validate_run_manifest(wrong_diagnostic, domain, published)


@pytest.mark.parametrize(
    ("run_status", "selector", "stable_reason"),
    [
        ("fatal", "next:semantic-json", "run_fatal"),
        ("fatal", "manifest", "final_manifest_unavailable"),
        ("interrupted", "next:plantuml", "run_interrupted"),
    ],
)
def test_fatal_and_interrupt_status_vectors_are_manifest_free(
    run_status: str, selector: str, stable_reason: str
) -> None:
    summary: dict[str, Any] = {
        "type": "run_summary",
        "schema": "code-structure-viz.run-summary/v1",
        "run_status": run_status,
        "exit_code": 1 if run_status == "fatal" else 130,
        "domains": [],
        "manifest": None,
    }
    stream: dict[str, Any] = {
        "type": "stdout_result",
        "schema": "code-structure-viz.stdout-result/v1",
        "selector": selector,
        "availability": False,
        "run_status": run_status,
        "stable_reason": stable_reason,
        "artifact": None,
    }
    _validator("run-summary-v1.schema.json").validate(summary)
    _validator("stdout-result-v1.schema.json").validate(stream)
    validate_run_status_vector(None, summary, stream, {}, canonical_json_bytes(stream) + b"\n", [])


def test_runtime_unavailable_is_a_manifest_only_payload_unavailable_vector() -> None:
    domain = _domain("incomplete", runtime_unavailable=True)
    validate_domain_manifest(domain)
    _validator("next-domain-manifest-v1.schema.json").validate(domain)
    manifest = _run_manifest(domain)
    validate_run_manifest(manifest, domain, _published_bytes(domain))
    _validator("run-manifest-v1.schema.json").validate(manifest)
    assert domain["incomplete_kind"] == "payload_unavailable"
    assert domain["diagnostics"][0]["code"] == "CSV-NEXT-NODE-001"
    assert domain["artifact_paths"] == []
    assert domain["payload_available"] is False
    summary: dict[str, Any] = {
        "type": "run_summary",
        "schema": "code-structure-viz.run-summary/v1",
        "run_status": "incomplete",
        "exit_code": 3,
        "domains": [
            {
                "domain": "next",
                "status": "incomplete",
                "incomplete_kind": "payload_unavailable",
            }
        ],
        "manifest": "run-manifest.json",
    }
    stream = _stdout_result_for_domain(domain, manifest)
    _validator("run-summary-v1.schema.json").validate(summary)
    _validator("stdout-result-v1.schema.json").validate(stream)
    validate_run_status_vector(
        manifest,
        summary,
        stream,
        _published_bytes(domain),
        canonical_json_bytes(stream) + b"\n",
        manifest["diagnostics"],
    )


def test_trusted_and_runtime_manifests_have_exact_sets_order_and_known_digests() -> None:
    environment = _trusted_environment()
    assert environment["sha256"] == (
        "a437f12d35d8ad909e63d6f41b451d25c35e46d3726bd108d63acaede14f02c5"
    )
    validate_trusted_environment(environment)
    validate_trusted_environment(environment, ["src/Button.tsx"])
    assert validate_no_trusted_shadowing(
        [{"source_kind": "module", "source_name": "app-local", "operation": "declare"}],
        environment,
    ) == [
        {
            "source_kind": "module",
            "source_name": "app-local",
            "operation": "declare",
            "decision": "allow",
        }
    ]
    with pytest.raises(AssertionError):
        validate_no_trusted_shadowing(
            [{"source_kind": "global", "source_name": "JSX", "operation": "augment"}],
            environment,
        )
    _validator("next-trusted-type-environment-v1.schema.json").validate(environment)

    runtime = _runtime_manifest()
    assert runtime["build_input_digest"] == (
        "5e43a79f64dbcea5c4be8c268f0d888dfa91d714be88951895ab8cc1b5a22d00"
    )
    assert runtime["build_output_digest"] == (
        "b866a8e7ee775ee3143b272824a55d4e5332a532d08860254b5398cff25026f1"
    )
    assert runtime["manifest_sha256"] == (
        "8b43890131639a685f064b361e97c98798fd09736129e95420215aac441164ab"
    )
    assert runtime["build_input_digest"] == digest(
        {"members": runtime["members"], "licenses": runtime["licenses"]}
    )
    assert runtime["build_output_digest"] == digest({"members": runtime["members"]})
    assert runtime["manifest_sha256"] == digest(
        {key: value for key, value in runtime.items() if key != "manifest_sha256"}
    )
    validate_runtime_manifest(runtime)
    _validator("next-runtime-manifest-v1.schema.json").validate(runtime)

    unsafe = copy.deepcopy(runtime)
    unsafe["members"][0]["path"] = "src/code_structure_viz/_next_runtime/../secret.js"
    with pytest.raises(AssertionError):
        validate_runtime_manifest(unsafe)
    with pytest.raises(ValidationError):
        _validator("next-runtime-manifest-v1.schema.json").validate(unsafe)
    unsafe_url = copy.deepcopy(runtime)
    unsafe_url["licenses"][0]["source_url"] = "http://registry.invalid/typescript"
    with pytest.raises(AssertionError):
        validate_runtime_manifest(unsafe_url)
    with pytest.raises(ValidationError):
        _validator("next-runtime-manifest-v1.schema.json").validate(unsafe_url)
    missing_member = copy.deepcopy(runtime)
    missing_member["members"].pop()
    with pytest.raises(AssertionError):
        validate_runtime_manifest(missing_member)
    changed_member_bytes = copy.deepcopy(runtime)
    changed_member_bytes["members"][0]["sha256"] = "0" * 64
    with pytest.raises(AssertionError):
        validate_runtime_manifest(changed_member_bytes)
    changed_attestation = copy.deepcopy(runtime)
    changed_attestation["inventory_attestation"]["sha256"] = "0" * 64
    with pytest.raises(AssertionError):
        validate_runtime_manifest(changed_attestation)
    extra_member = copy.deepcopy(runtime)
    extra_member["members"].append(
        {
            "path": "src/code_structure_viz/_next_runtime/extra.js",
            "size_bytes": 1,
            "sha256": "e" * 64,
            "role": "adapter",
        }
    )
    with pytest.raises(AssertionError):
        validate_runtime_manifest(extra_member)
    changed_license = copy.deepcopy(runtime)
    changed_license["licenses"][0]["license_id"] = "MIT"
    with pytest.raises(AssertionError):
        validate_runtime_manifest(changed_license)
    missing_license = copy.deepcopy(runtime)
    missing_license["licenses"].pop()
    with pytest.raises(AssertionError):
        validate_runtime_manifest(missing_license)
    wrong_digest = copy.deepcopy(environment)
    wrong_digest["sha256"] = "0" * 64
    with pytest.raises(AssertionError):
        validate_trusted_environment(wrong_digest)
    missing_file = copy.deepcopy(environment)
    missing_file["files"].pop()
    with pytest.raises(AssertionError):
        validate_trusted_environment(missing_file)
    extra_file = copy.deepcopy(environment)
    extra_file["files"].append(
        {
            "virtual_path": "/.code-structure-viz/trusted/v1/extra.d.ts",
            "sha256": "5" * 64,
            "license_id": "MIT",
        }
    )
    with pytest.raises(AssertionError):
        validate_trusted_environment(extra_file)
    changed_symbol = copy.deepcopy(environment)
    changed_symbol["certified_symbols"][0]["signature_digest"] = "0" * 64
    with pytest.raises(AssertionError):
        validate_trusted_environment(changed_symbol)
    unsafe_environment_path = copy.deepcopy(environment)
    unsafe_environment_path["files"][0]["virtual_path"] = (
        "/.code-structure-viz/trusted/v1/../escape.d.ts"
    )
    with pytest.raises(ValidationError):
        _validator("next-trusted-type-environment-v1.schema.json").validate(unsafe_environment_path)
    with pytest.raises(AssertionError):
        validate_trusted_environment(environment, [environment["files"][0]["virtual_path"]])


def test_plantuml_exact_bytes_and_control_character_golden() -> None:
    model = _empty_model()
    golden = render_plantuml(model)
    expected = (
        b"@startuml\n"
        b"title CodeStructureViz Next snapshot\n"
        b"note top: status=complete; coverage=complete\n"
        b"legend\n"
        b"N_P project\n"
        b"N_M module\n"
        b"N_C component\n"
        b"<<export_binding>> export member\n"
        b"<<import_binding>> import member\n"
        b"<<prop>> prop member\n"
        b"--> static_import|literal_dynamic_import\n"
        b"..> jsx_render|component_wrap\n"
        b"facet=role:<value|type>|reexport=<true|false>|boundary=<none|server_to_client_entry>\n"
        b"marker=client_entry|router_context=<context>|client_dependency|server_candidate|unknown\n"
        b"marker=partial_safe\n"
        b"external=cloud-after-components-before-members\n"
        b"sort=kind-prefixed-id-utf8\n"
        b"endlegend\n"
        b'package "P:next:project:'
        b'530b20c858c6039c19737f386f96cfabdadda6b8a0a1c98b5ca639beb2765c25" '
        b"as N_P_530b20c858c6039c19737f386f96cfabdadda6b8a0a1c98b5ca639beb2765c25 {\n"
        b"}\n"
        b"@enduml\n"
    )
    assert golden == expected
    validate_plantuml_contract(golden, model)

    attack = _model()
    attack["components"][0]["declaration_key"] = 'Bad";\nname<&payload>'
    escaped = render_plantuml(attack)
    validate_plantuml_contract(escaped, attack)
    assert b'Bad\\"\\;\\nname' in escaped
    assert b"\\u003c" in escaped and b"\\u003e" in escaped
    assert b"\nname" not in escaped

    partial = render_plantuml(model, status="partial_safe")
    validate_plantuml_contract(partial, model, status="partial_safe")
    assert b"note top: status=partial_safe; coverage=partial_safe\n" in partial
    assert b"note top: marker=partial_safe\n" in partial

    rich = _model()
    rich["relations"].append(
        {
            "kind": "literal_dynamic_import",
            "id": _id("relation", "1"),
            "source_id": _id("module", "3"),
            "target": {"kind": "external", "safe_specifier": "react", "exported_name": "lazy"},
            "role": "value",
            "reexport": False,
            "boundary_effect": "none",
        }
    )
    rich["modules"][1]["derived_roles"] = ["server_candidate"]
    boundary_relation: dict[str, Any] = {
        "kind": "static_import",
        "id": "",
        "source_id": rich["modules"][1]["id"],
        "target": {"kind": "internal", "module_id": rich["modules"][0]["id"]},
        "role": "value",
        "reexport": False,
        "boundary_effect": "server_to_client_entry",
    }
    boundary_relation["id"] = recompute_record_id(boundary_relation)
    rich["relations"].append(boundary_relation)
    external_jsx: dict[str, Any] = {
        "kind": "jsx_render",
        "id": "",
        "source_id": _id("component", "5"),
        "target": {
            "kind": "external",
            "safe_specifier": "react",
            "exported_name": "memo",
        },
        "occurrence_count": 2,
        "contexts": ["direct"],
    }
    external_jsx["id"] = recompute_record_id(external_jsx)
    rich["relations"].append(external_jsx)
    rich["relations"].sort(key=lambda record: record["id"])
    rich["coverage"]["counts"]["relations"] = len(rich["relations"])
    rich["coverage"]["counts"]["published"] += 3
    rich["coverage"]["counts"]["discovered"] += 3
    validate_model(rich)
    rich_output = render_plantuml(rich)
    validate_plantuml_contract(rich_output, rich)
    assert b"literal_dynamic_import" in rich_output
    assert b"boundary=server_to_client_entry" in rich_output
    assert b'cloud "external:react#lazy" as X_' in rich_output
    assert b"..> X_" in rich_output
    assert b"jsx_render|occurrences=2|contexts=direct" in rich_output

    external_jsx_mutation = copy.deepcopy(rich)
    jsx_relation = next(
        relation
        for relation in external_jsx_mutation["relations"]
        if relation["kind"] == "jsx_render" and relation["target"]["kind"] == "external"
    )
    jsx_relation["target"]["safe_specifier"] = "react-dom"
    with pytest.raises(AssertionError):
        validate_model(external_jsx_mutation)

    external_import = next(
        member for member in rich["members"] if member["kind"] == "import_binding"
    )
    external_import["source"] = {
        "kind": "external",
        "safe_specifier": "react",
        "exported_name": "memo",
    }
    external_import["id"] = recompute_record_id(external_import)
    rich["members"].sort(key=lambda record: record["id"])
    validate_model(rich)
    rich_with_external_member = render_plantuml(rich)
    validate_plantuml_contract(rich_with_external_member, rich)
    assert b'cloud "external:react#memo" as X_' in rich_with_external_member


def test_compatibility_descriptor_known_answer_is_content_independent() -> None:
    descriptor = _descriptor()
    validate_compatibility_descriptor(descriptor)
    assert descriptor["compatibility_id"] == (
        "28fa8dfaef26afad655f7bc915308b87e4bd026c5720834c2d3a5b6e48ef06c5"
    )
    assert descriptor["compatibility_id"] == recompute_compatibility_id(descriptor)
    changed_content = copy.deepcopy(descriptor)
    changed_content["compatibility_id"] = descriptor["compatibility_id"]
    assert changed_content["compatibility_id"] == recompute_compatibility_id(changed_content)
    changed_algorithm = copy.deepcopy(descriptor)
    changed_algorithm["algorithm_versions"]["props"] = 2
    changed_algorithm["compatibility_id"] = recompute_compatibility_id(changed_algorithm)
    assert changed_algorithm["compatibility_id"] != descriptor["compatibility_id"]
    wrong = copy.deepcopy(descriptor)
    wrong["compatibility_id"] = "0" * 64
    with pytest.raises(AssertionError):
        validate_compatibility_descriptor(wrong)


def test_canonical_digest_normalizes_unicode_before_hashing() -> None:
    composed = {"label": "é"}
    decomposed = {"label": "e\u0301"}
    assert canonical_json_bytes(composed) == b'{"label":"\xc3\xa9"}'
    assert digest(composed) == digest(decomposed)


def test_contract_fixture_index_materializes_plan_008_vectors() -> None:
    assert VALIDATOR_SCHEMA == "code-structure-viz.next-reference-validation/v1"
    fixture = json.loads(
        (ROOT / "tests" / "fixtures" / "next_contract_vectors.json").read_text(encoding="utf-8")
    )
    assert fixture["schema"] == "code-structure-viz.next-contract-vectors/v1"
    assert {
        "semantic-complete-empty",
        "semantic-complete-non-empty",
        "semantic-partial-safe",
        "partial-proof-decomposition",
        "run-status-matrix",
        "runtime-unavailable",
        "entity-overrun",
        "request-response-envelope",
        "diagnostic-catalog",
        "trusted-known-answer",
        "runtime-known-answer",
        "config-projection",
        "status-cross-artifact",
        "props-ir-limits",
        "trusted-runtime-exact-set",
        "plantuml-control-escape",
        "plantuml-complete-non-empty",
        "plantuml-partial-safe",
        "plantuml-external-dynamic",
        "plantuml-external-jsx",
        "nfc-canonical-digest",
        "compatibility-known-answer",
        "export-resolution-witness",
        "limits-inclusive-boundaries",
        "runtime-inventory-attestation",
        "stdout-all-selectors",
        "head-commit-known-lengths",
        "taint-boundary-closure",
        "export-closed-tokenizer",
        "export-reexport-graph-closure",
        "entity-budget-outcome-preserving",
        "adapter-stderr-capture-bound",
        "array-aggregate-bound",
        "source-acquisition-plan-v1",
        "surface-order-by-domain",
    } <= set(fixture["positive"])
    assert {
        "cross-domain",
        "wrong-fact-value",
        "wrong-project-owner",
        "wrong-role-precedence",
        "dangling-reference",
        "duplicate-project-file",
        "taint-set-mismatch",
        "failed-proof-overlap",
        "diagnostic-ref-permission",
        "diagnostic-catalog-mutation",
        "unsafe-trusted-path",
        "trusted-runtime-set-mutation",
        "props-ir-limit",
        "taint-frontier-count",
        "config-projection-mutation",
        "runtime-http-url",
        "compatibility-mismatch",
        "plantuml-injection",
        "plantuml-facet-mutation",
        "taint-omitted-edge",
        "taint-shared-frontier-duplicate",
        "taint-boundary-underflow",
        "target-missing-resolution",
        "target-extra-resolution",
        "target-substituted-id",
        "target-failed-as-resolved",
        "export-witness-count-mutation",
        "runtime-member-byte-mutation",
        "runtime-attestation-mutation",
        "head-commit-invalid-length",
        "export-syntax-omission",
        "export-syntax-mutation",
        "reexport-cycle",
        "reexport-conflict",
        "entity-budget-outcome-upgrade",
        "adapter-stderr-limit-plus-one",
        "array-aggregate-pre-materialization",
        "source-plan-field-mutation",
        "surface-order-mutation",
    } <= set(fixture["negative"])
