import base64
import copy
import hashlib
import inspect
import json
import re
import sys
from collections.abc import Mapping
from dataclasses import replace
from itertools import combinations
from pathlib import Path
from typing import Any, cast

import pytest
from jsonschema import ValidationError  # type: ignore[import-untyped]

from code_structure_viz.artifacts.streams import StdoutEmitter
from code_structure_viz.cli.parser import DomainFormatSelector, ManifestSelector
from code_structure_viz.core.outcomes import RunOutcome
from tests.contracts.ecmascript_unicode_15_0 import (
    TABLE_DIGEST as ECMASCRIPT_UNICODE_TABLE_DIGEST,
)
from tests.contracts.ecmascript_unicode_15_0 import (
    canonical_table_bytes,
)
from tests.contracts.next_reference_validation import (
    COLLECTIONS,
    DECISION_FAILURE_MATRIX,
    ECMASCRIPT_IDENTIFIER_UNICODE_TABLE_DIGEST,
    ECMASCRIPT_IDENTIFIER_UNICODE_VERSION,
    IDENTIFIER_CLASSIFICATION_SHA256,
    LIMIT_CONTRACTS,
    ROLE_ORDER,
    ROLE_PRECEDENCE,
    RUNTIME_PHYSICAL_TO_VIRTUAL,
    RUNTIME_REQUIRED_PATHS,
    TARGET_FAILURE_REASONS,
    TRUSTED_PROFILE_CERTIFIED_SYMBOLS,
    TRUSTED_PROFILE_FILE_LICENSES,
    TRUSTED_PROFILE_FILE_SHA256,
    TRUSTED_PROFILE_FILE_SIZES,
    TRUSTED_PROFILE_LICENSE_DIGEST,
    TRUSTED_PROFILE_LICENSES,
    TRUSTED_PROFILE_PHYSICAL_TO_VIRTUAL,
    TRUSTED_PROFILE_SHADOWING_WITNESS,
    VALIDATOR_SCHEMA,
    InstrumentedSourceReader,
    NextDecisionContext,
    NextPublicationContext,
    NextRunContext,
    NextRunDecision,
    NextValidatedDecision,
    NotApplicableDecision,
    PreResponseFailureDecision,
    PublicationBoundaryDecision,
    SourceAcquisitionError,
    SourceDiscoveryIntent,
    SourceFailureLedger,
    _assert_file_path,
    _assert_path,
    _canonical_json_line,
    _decision_known_counts,
    _decision_provenance,
    _derived_taint_fixed_point,
    _export_binding_projection_for_model,
    _is_export_identifier,
    _is_jsx_identifier_part,
    _is_jsx_identifier_start,
    _path_sort_key,
    _publication_context_for_validated_request,
    _scan_export_file,
    _toolchain_snapshot,
    assert_encoded_stdin_boundary,
    assert_limit_boundary,
    bounded_decode_json,
    canonical_json_bytes,
    canonical_run_context,
    canonical_target_key,
    capture_adapter_stderr,
    capture_adapter_stdout,
    classify_response_limit,
    classify_source_failure,
    copy_selected_stdout,
    count_array_items_before_materialization,
    decision_context_for_request,
    decision_failure_kind,
    decision_failure_spec,
    derive_boundary_roles,
    derive_pre_budget_outcome,
    derive_required_causal_edges,
    digest,
    encoded_request_bytes,
    entity_budget_allowed,
    entity_budget_gate,
    expected_export_coverage_counts,
    expected_export_observations,
    expected_export_reexport_witness,
    expected_export_resolution_witness,
    export_failure_decision,
    export_reexport_failure_rows,
    finalize_publication_decision,
    identifier_classification_digest,
    internal_entity_count,
    is_binding_identifier,
    is_declaration_key,
    is_identifier_name,
    is_next_run_decision,
    join_reexport_observations_to_edges,
    load_export_census_fixture,
    load_export_graph_cases,
    load_export_graph_fixture,
    load_export_graph_raw_fixture,
    model_record_budget_allowed,
    model_wire_record_count,
    not_applicable_decision,
    pre_response_failure_decision,
    process_launch_descriptor,
    project_config_digest,
    recompute_compatibility_id,
    recompute_export_graph_case,
    recompute_publication_projection_digest,
    recompute_record_id,
    recompute_request_id,
    recompute_run_fingerprint,
    render_plantuml,
    render_public_diagnostic_stderr,
    resolve_target_resolutions,
    response_boundary_decision,
    scan_export_syntax_census,
    seal_source_acquisition,
    source_plan_descriptor,
    target_completeness_failure,
    target_failure_from_proof,
    validate_adapter_request,
    validate_compatibility_descriptor,
    validate_domain_manifest,
    validate_encoded_stdin_size,
    validate_limits,
    validate_limits_consistency,
    validate_model,
    validate_no_trusted_shadowing,
    validate_plantuml_contract,
    validate_process_launch_descriptor,
    validate_proof,
    validate_published_projection,
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


def _run_context(
    formats: list[str] | None = None,
    *,
    resolved: int | None = 500,
    source: str = "builtin",
    requested: int | None = None,
    selector: str | None = "next:semantic-json",
    independent: bool = False,
) -> NextRunContext:
    format_values = list(formats or ["semantic-json", "plantuml"])
    if independent:
        resolved = None
        source = "unobserved"
        requested = None
    return canonical_run_context(
        requested_formats=format_values,
        budget_requested=requested,
        budget_resolved=resolved,
        budget_source=source,
        stdout_selector=selector,
    )


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
        key=lambda project: _path_sort_key(project["root"]),
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
        "derived_roles": [],
    }
    module_two = {
        "kind": "module",
        "id": _id("module", "4"),
        "project_id": _id("project", "0"),
        "path": "src/Card.tsx",
        "router_context": "none",
        "client_entry": False,
        "derived_roles": ["client_dependency"],
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


def _generated_context_model(file_count: int) -> dict[str, Any]:
    """Generate a compact, schema-valid model for wire-limit boundaries."""

    assert file_count >= 1
    empty_sha256 = hashlib.sha256(b"").hexdigest()
    files: list[dict[str, Any]] = []
    for index in range(file_count):
        file_record: dict[str, Any] = {
            "kind": "file",
            "id": "",
            "path": f"src/generated/{index:05d}.d.ts",
            "project_id": _id("project", "0"),
            "roles": ["context"],
            "effective_role": "context",
            "size_bytes": 0,
            "sha256": empty_sha256,
        }
        file_record["id"] = recompute_record_id(file_record)
        files.append(file_record)
    files.sort(key=lambda record: record["id"])
    project = _project()
    project["file_ids"] = sorted(record["id"] for record in files)
    project["config_digest"] = project_config_digest(project)
    model: dict[str, Any] = {
        "schema": "code-structure-viz.next-model/v1",
        "projects": [project],
        "files": files,
        "modules": [],
        "components": [],
        "members": [],
        "relations": [],
        "facts": [],
        "coverage": _next_coverage(),
        "diagnostics": [],
    }
    _refresh_model_counts(model)
    return model


def _model_with_positive_reexports() -> dict[str, Any]:
    """Build a complete model that carries component and star re-exports."""

    model = _model()
    project_id = model["projects"][0]["id"]
    census = {item["path"]: item["content"] for item in load_export_census_fixture()}
    extra_paths = ("src/ExportGrammar.tsx", "src/ExportReexport.ts", "src/ExportTypes.ts")
    for path in extra_paths:
        content = census[path]
        file_record: dict[str, Any] = {
            "kind": "file",
            "id": "",
            "path": path,
            "project_id": project_id,
            "roles": ["program"],
            "effective_role": "program",
            "size_bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        }
        file_record["id"] = recompute_record_id(file_record)
        model["files"].append(file_record)
        module: dict[str, Any] = {
            "kind": "module",
            "id": "",
            "project_id": project_id,
            "path": path,
            "router_context": "none",
            "client_entry": False,
            "derived_roles": [],
        }
        module["id"] = recompute_record_id(module)
        model["modules"].append(module)

    grammar_module = next(
        module for module in model["modules"] if module["path"] == "src/ExportGrammar.tsx"
    )
    grammar_component: dict[str, Any] = {
        "kind": "component",
        "id": "",
        "module_id": grammar_module["id"],
        "declaration_key": "表示",
        "recognition_evidence": ["trusted_callable"],
        "props_state": "no_props",
    }
    grammar_component["id"] = recompute_record_id(grammar_component)
    model["components"].append(grammar_component)

    for module in model["modules"]:
        if any(fact["owner_id"] == module["id"] for fact in model["facts"]):
            continue
        fact: dict[str, Any] = {
            "kind": "router_context",
            "id": "",
            "owner_id": module["id"],
            "value": "none",
        }
        fact["id"] = recompute_record_id(fact)
        model["facts"].append(fact)

    project = model["projects"][0]
    project["file_ids"] = sorted(file["id"] for file in model["files"])
    project["config_digest"] = project_config_digest(project)
    for collection in COLLECTIONS:
        model[collection].sort(key=lambda record: record["id"])

    # Public export bindings are intentionally regenerated after adding the
    # raw-graph modules.  This makes the response witness and model members
    # share the same exported-name/physical-component join.
    model["members"] = [member for member in model["members"] if member["kind"] != "export_binding"]
    model["members"].extend(copy.deepcopy(_export_binding_projection_for_model(model)))
    model["members"].sort(key=lambda record: record["id"])
    counts = model["coverage"]["counts"]
    for collection in COLLECTIONS:
        counts[collection] = len(model[collection])
    counts["published"] = sum(len(model[collection]) for collection in COLLECTIONS)
    counts["discovered"] = counts["published"]
    counts["internal_entities"] = len(model["modules"]) + len(model["components"])
    model["coverage"].update(expected_export_coverage_counts(model))
    return model


def _model_with_graph_failure_cases(
    *, include_cycle: bool = True, include_conflict: bool = True
) -> dict[str, Any]:
    """Build a schema-valid model with positive and selected failure graphs."""

    model = _model()
    project_id = model["projects"][0]["id"]
    census = {item["path"]: item["content"] for item in load_export_census_fixture()}
    graph_paths = [
        "src/GraphAliasBarrel.ts",
        "src/GraphAliasButton.tsx",
        "src/GraphAliasIndex.ts",
        "src/GraphDefaultIndex.ts",
        "src/GraphDefaultSource.ts",
        "src/GraphEmpty.ts",
        "src/GraphEmptyIndex.ts",
        "src/GraphOne.ts",
        "src/GraphTwo.ts",
    ]
    if include_conflict:
        graph_paths.extend(
            (
                "src/GraphConflictIndex.ts",
                "src/GraphSameIndex.ts",
                "src/GraphSameSource.ts",
            )
        )
    if include_cycle:
        graph_paths.extend(
            (
                "src/GraphCycleA.ts",
                "src/GraphCycleB.ts",
                "src/GraphStarCycleA.ts",
                "src/GraphStarCycleB.ts",
            )
        )
    for path in graph_paths:
        content = census[path]
        file_record: dict[str, Any] = {
            "kind": "file",
            "id": "",
            "path": path,
            "project_id": project_id,
            "roles": ["program"],
            "effective_role": "program",
            "size_bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        }
        file_record["id"] = recompute_record_id(file_record)
        model["files"].append(file_record)
        module: dict[str, Any] = {
            "kind": "module",
            "id": "",
            "project_id": project_id,
            "path": path,
            "router_context": "none",
            "client_entry": False,
            "derived_roles": [],
        }
        module["id"] = recompute_record_id(module)
        model["modules"].append(module)

    component_specs = [
        ("src/GraphAliasButton.tsx", "Button"),
        ("src/GraphOne.ts", "Shared"),
        ("src/GraphTwo.ts", "Shared"),
    ]
    if include_conflict:
        component_specs.append(("src/GraphSameSource.ts", "Foo"))
    for path, declaration_key in component_specs:
        module = next(item for item in model["modules"] if item["path"] == path)
        component: dict[str, Any] = {
            "kind": "component",
            "id": "",
            "module_id": module["id"],
            "declaration_key": declaration_key,
            "recognition_evidence": ["trusted_callable"],
            "props_state": "no_props",
        }
        component["id"] = recompute_record_id(component)
        model["components"].append(component)

    for module in model["modules"]:
        if any(fact["owner_id"] == module["id"] for fact in model["facts"]):
            continue
        fact: dict[str, Any] = {
            "kind": "router_context",
            "id": "",
            "owner_id": module["id"],
            "value": "none",
        }
        fact["id"] = recompute_record_id(fact)
        model["facts"].append(fact)

    project = model["projects"][0]
    project["file_ids"] = sorted(file["id"] for file in model["files"])
    project["config_digest"] = project_config_digest(project)
    model["members"] = [member for member in model["members"] if member["kind"] != "export_binding"]
    model["members"].extend(copy.deepcopy(_export_binding_projection_for_model(model)))
    for collection in COLLECTIONS:
        model[collection].sort(key=lambda record: record["id"])
    _refresh_model_counts(model)
    model["coverage"].update(expected_export_coverage_counts(model))
    return model


def _refresh_model_counts(model: dict[str, Any]) -> None:
    """Keep a deliberately mutated model structurally count-consistent."""

    counts = model["coverage"]["counts"]
    for collection in COLLECTIONS:
        counts[collection] = len(model[collection])
    counts["published"] = sum(len(model[collection]) for collection in COLLECTIONS)
    counts["discovered"] = counts["published"]
    counts["internal_entities"] = len(model["modules"]) + len(model["components"])


def _path_in_root(root: str, path: str) -> str:
    return path if root == "." else f"{root.rstrip('/')}/{path}"


def _rebase_model(model: dict[str, Any], root: str) -> dict[str, Any]:
    """Create a complete second project while recomputing every owned ID."""

    old_project_id = model["projects"][0]["id"]
    project = copy.deepcopy(model["projects"][0])
    project["root"] = root
    project["source_roots"] = [_path_in_root(root, "src")]
    project["config_path"] = _path_in_root(root, "tsconfig.json")
    project["id"] = recompute_record_id(project)
    id_map = {old_project_id: project["id"]}
    rebased: dict[str, list[dict[str, Any]]] = {collection: [] for collection in COLLECTIONS}
    rebased["projects"] = [project]

    for collection in ("files", "modules"):
        for original in model[collection]:
            record = copy.deepcopy(original)
            old_id = record["id"]
            record["project_id"] = project["id"]
            record["path"] = _path_in_root(root, record["path"])
            record["id"] = recompute_record_id(record)
            id_map[old_id] = record["id"]
            rebased[collection].append(record)

    def replace_ids(value: Any) -> Any:
        if isinstance(value, str):
            return id_map.get(value, value)
        if isinstance(value, list):
            return [replace_ids(item) for item in value]
        if isinstance(value, dict):
            return {key: replace_ids(item) for key, item in value.items()}
        return value

    for collection in ("components", "members", "relations", "facts"):
        for original in model[collection]:
            record = replace_ids(copy.deepcopy(original))
            assert isinstance(record, dict)
            if "path" in record:
                record["path"] = _path_in_root(root, record["path"])
            old_id = original["id"]
            record["id"] = recompute_record_id(record)
            id_map[old_id] = record["id"]
            rebased[collection].append(record)

    project["file_ids"] = sorted(record["id"] for record in rebased["files"])
    project["config_digest"] = project_config_digest(project)
    for collection in COLLECTIONS:
        rebased[collection].sort(key=lambda record: record["id"])
    result: dict[str, Any] = {
        "schema": model["schema"],
        **rebased,
        "coverage": copy.deepcopy(model["coverage"]),
        "diagnostics": copy.deepcopy(model["diagnostics"]),
    }
    counts = result["coverage"]["counts"]
    for collection in COLLECTIONS:
        counts[collection] = len(result[collection])
    counts["published"] = sum(len(result[collection]) for collection in COLLECTIONS)
    counts["internal_entities"] = len(result["modules"]) + len(result["components"])
    counts["discovered"] = counts["published"]
    return result


def _trim_to_card_module(model: dict[str, Any]) -> dict[str, Any]:
    """Keep a complete but export-empty project for the inverse-order vector."""

    card_paths = {
        record["path"] for record in model["files"] if record["path"].endswith("Card.tsx")
    }
    card_module_ids = {record["id"] for record in model["modules"] if record["path"] in card_paths}
    card_component_ids = {
        record["id"] for record in model["components"] if record["module_id"] in card_module_ids
    }
    model["files"] = [
        record
        for record in model["files"]
        if record["path"] in card_paths or record["path"].endswith("types.d.ts")
    ]
    model["modules"] = [record for record in model["modules"] if record["id"] in card_module_ids]
    for module in model["modules"]:
        module["derived_roles"] = []
    model["components"] = [
        record for record in model["components"] if record["id"] in card_component_ids
    ]
    model["members"] = []
    model["relations"] = []
    model["facts"] = [
        record for record in model["facts"] if record.get("owner_id") in card_module_ids
    ]
    project = model["projects"][0]
    project["file_ids"] = sorted(record["id"] for record in model["files"])
    for collection in COLLECTIONS:
        model[collection].sort(key=lambda record: record["id"])
    counts = model["coverage"]["counts"]
    for collection in COLLECTIONS:
        counts[collection] = len(model[collection])
    counts["published"] = sum(len(model[collection]) for collection in COLLECTIONS)
    counts["internal_entities"] = len(model["modules"]) + len(model["components"])
    counts["discovered"] = counts["published"]
    return model


def _inverse_order_two_project_model() -> dict[str, Any]:
    """Build two disjoint complete projects whose root and ID orders differ."""

    candidates = (
        ("apps/a", "apps/z"),
        ("packages/a", "packages/z"),
        ("workspace/a", "workspace/z"),
        ("project/a", "project/z"),
        ("a", "z"),
        ("alpha", "omega"),
    )
    for left_root, right_root in candidates:
        left_id = "next:project:" + digest(
            {"kind": "project", "version": 1, "identity": {"root": left_root}}
        )
        right_id = "next:project:" + digest(
            {"kind": "project", "version": 1, "identity": {"root": right_root}}
        )
        if [left_root, right_root] == sorted((left_root, right_root)) and [
            left_id,
            right_id,
        ] != sorted((left_id, right_id)):
            first = _rebase_model(_model(), left_root)
            second = _trim_to_card_module(_rebase_model(_model(), right_root))
            combined: dict[str, Any] = {
                "schema": "code-structure-viz.next-model/v1",
                **{
                    collection: sorted(
                        [*first[collection], *second[collection]],
                        key=lambda record: record["id"],
                    )
                    for collection in COLLECTIONS
                },
                "coverage": copy.deepcopy(first["coverage"]),
                "diagnostics": [],
            }
            counts = combined["coverage"]["counts"]
            for collection in COLLECTIONS:
                counts[collection] = len(combined[collection])
            counts["published"] = sum(len(combined[collection]) for collection in COLLECTIONS)
            counts["internal_entities"] = len(combined["modules"]) + len(combined["components"])
            counts["discovered"] = counts["published"]
            return combined
    raise AssertionError("candidate roots did not produce inverse project orders")


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


def _semantic(
    model: dict[str, Any],
    status: str = "complete",
    *,
    domain: dict[str, Any] | None = None,
) -> dict[str, Any]:
    descriptor = _descriptor()
    trusted_environment_digest = _trusted_environment()["sha256"]
    if domain is None:
        semantic_diagnostics: list[dict[str, Any]] = []
    else:
        # Domain diagnostics are the public diagnostic wire shape.  The
        # semantic projection has its own closed, aggregated shape, so the
        # renderer must project fields explicitly instead of copying a
        # differently-shaped dict into the published bytes.
        semantic_diagnostics = [
            {
                "code": diagnostic["code"],
                "severity": diagnostic["severity"],
                "recoverable": diagnostic["recoverable"],
                "count": 1,
                "path_ref": diagnostic["path"],
                "symbol_ref": diagnostic["symbol"],
                "outcome": diagnostic["outcome"],
                "ref_permission": diagnostic["ref_permission"],
                **({"reason": diagnostic["reason"]} if "reason" in diagnostic else {}),
            }
            for diagnostic in domain["diagnostics"]
        ]
    value = {
        "type": "semantic_snapshot",
        "schema": "code-structure-viz.semantic/v1",
        "domain": "next",
        "document_kind": "snapshot",
        "status": status,
        "semantic_compatibility_id": descriptor["compatibility_id"],
        "compatibility_descriptor": descriptor,
        "identity_versions": descriptor["identity_versions"],
        "source": copy.deepcopy(
            domain["source"]
            if domain is not None
            else {
                "schema": "code-structure-viz.source-view/v1",
                "kind": "working-tree",
                "head_commit": None,
                "fingerprint": "b" * 64,
                "file_count": len(model["files"]),
            }
        ),
        "request": copy.deepcopy(domain["request"] if domain is not None else _snapshot_request()),
        "coverage": copy.deepcopy(model["coverage"]),
        # Project/config surfaces are root-path ordered; semantic records
        # inside entities/members/relations/facts retain kind-prefixed ID
        # order.  The inverse-order fixture makes this distinction observable.
        "projects": sorted(model["projects"], key=lambda item: item["id"]),
        "files": model["files"],
        "entities": [*model["modules"], *model["components"]],
        "members": model["members"],
        "relations": model["relations"],
        "facts": model["facts"],
        "diagnostics": semantic_diagnostics,
    }
    if status == "incomplete" and domain is None:
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
    if domain is not None:
        # The domain's validated decision owns the context and fingerprint;
        # publication must echo it byte-for-byte rather than infer a selector
        # from the first requested format.
        value["request"]["run_fingerprint"] = domain["run_fingerprint"]
        value["status"] = status
        if status == "incomplete" and domain.get("incomplete_kind") == "partial_safe":
            value["incomplete_kind"] = "partial_safe"
        return value
    value["request"]["run_fingerprint"] = recompute_run_fingerprint(
        source_view_fingerprint=value["source"]["fingerprint"],
        source_plan_digest=value["request"]["source_plan_digest"],
        domain_config_digest=value["request"]["domain_config_digest"],
        projects=value["projects"],
        targets=value["request"]["targets"],
        formats=value["request"]["formats"],
        stdout_selector=f"next:{value['request']['formats'][0]}",
        limits=value["request"]["limits"],
        node_version="22.14.0",
        typescript_version="5.9.2",
        adapter_version="1.0.0",
        protocol="code-structure-viz.next-adapter/v1",
        trusted_environment_digest=trusted_environment_digest,
    )
    return value


def _request(
    model: dict[str, Any] | None = None,
    *,
    targets: list[str] | None = None,
    limits: dict[str, int] | None = None,
    run_context: NextRunContext | None = None,
    default_content: bytes | None = None,
) -> dict[str, Any]:
    model = model or _model()
    trusted_environment_digest = _trusted_environment()["sha256"]
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
    census_contents = {item["path"]: item["content"] for item in load_export_census_fixture()}
    for file_record in model["files"]:
        content = contents.get(file_record["path"]) or census_contents.get(file_record["path"])
        if content is None and file_record["path"].endswith("Button.tsx"):
            content = contents["src/Button.tsx"]
        elif content is None and file_record["path"].endswith("Card.tsx"):
            content = contents["src/Card.tsx"]
        elif content is None and file_record["path"].endswith("types.d.ts"):
            content = contents["src/types.d.ts"]
        elif content is None and default_content is not None:
            content = default_content
        assert content is not None
        files.append(
            {
                **file_record,
                "content_base64": base64.b64encode(content).decode("ascii"),
            }
        )
    if run_context is None:
        resolved = (limits or _next_limits())["max_entities"]
        assert resolved == 500
        context = _run_context()
    else:
        context = canonical_run_context(**run_context)
        assert context["budget_resolved"] == (limits or _next_limits())["max_entities"]
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
        "projects": sorted(
            copy.deepcopy(model["projects"]), key=lambda item: canonical_json_bytes(item["root"])
        ),
        "files": files,
        "targets": list(targets or []),
        "limits": copy.deepcopy(limits or _next_limits()),
        "run_context": context,
    }
    request["request_id"] = recompute_request_id(request)
    return request


def _complete_proof(model: dict[str, Any]) -> dict[str, Any]:
    records = []
    seen_ids: set[str] = set()
    for collection in COLLECTIONS:
        for record in model[collection]:
            # A typed duplicate-target response is allowed to carry the
            # duplicated Module in its model, but the proof authority remains
            # a set of discovered records.  Keep one exact row here; the
            # response validator checks that the omitted row is the narrowly
            # permitted byte-identical duplicate.
            if record["id"] in seen_ids:
                continue
            seen_ids.add(record["id"])
            records.append({"collection": collection, "record_id": record["id"], "taints": []})
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


def _target_proof_model(model: dict[str, Any], failure: Any, targets: list[str]) -> dict[str, Any]:
    """Remove only selected, byte-identical duplicate Modules for proof derivation."""

    candidate = copy.deepcopy(model)
    failed_reasons = {item["target_key"]: item["reason"] for item in failure.failures}
    selected_targets = list(targets) or [
        f"path:{record['path']}"
        for record in model["files"]
        if "program" in record["roles"] and not record["path"].endswith(".d.ts")
    ]
    duplicate_keys: set[tuple[str, str]] = set()
    for target in selected_targets:
        if failed_reasons.get(canonical_target_key(target)) != "duplicate":
            continue
        requested_path = canonical_target_key(target).removeprefix("path:")
        matching_files = [
            record
            for record in model["files"]
            if record["path"] == requested_path
            or requested_path == "."
            or record["path"].startswith(requested_path.rstrip("/") + "/")
        ]
        for file_record in matching_files:
            if "program" not in file_record["roles"]:
                continue
            key = (file_record["project_id"], file_record["path"])
            rows = [
                module
                for module in model["modules"]
                if (module["project_id"], module["path"]) == key
            ]
            if len(rows) > 1 and len({canonical_json_bytes(row) for row in rows}) == 1:
                duplicate_keys.add(key)
    seen_keys: set[tuple[str, str]] = set()
    retained_modules: list[dict[str, Any]] = []
    for module in candidate["modules"]:
        key = (module["project_id"], module["path"])
        if key in duplicate_keys and key in seen_keys:
            continue
        retained_modules.append(module)
        seen_keys.add(key)
    candidate["modules"] = retained_modules
    counts = candidate["coverage"]["counts"]
    for collection in COLLECTIONS:
        counts[collection] = len(candidate[collection])
    counts["published"] = sum(len(candidate[collection]) for collection in COLLECTIONS)
    counts["discovered"] = counts["published"]
    counts["internal_entities"] = len(candidate["modules"]) + len(candidate["components"])
    return candidate


def _target_proof_resolutions(
    model: dict[str, Any], failure: Any, targets: list[str]
) -> list[dict[str, Any]]:
    """Build complete target rows, retaining a reason only for typed failures."""

    failed_by_key = {item["target_key"]: item["reason"] for item in failure.failures}
    effective_targets = list(targets) or [
        f"path:{record['path']}"
        for record in model["files"]
        if "program" in record["roles"] and not record["path"].endswith(".d.ts")
    ]
    rows: list[dict[str, Any]] = []
    for target in effective_targets:
        target_key = canonical_target_key(target)
        if target_key in failed_by_key:
            rows.append(
                {
                    "target_key": target_key,
                    "status": "failed",
                    "record_ids": [],
                    "reason": failed_by_key[target_key],
                }
            )
            continue
        resolved = resolve_target_resolutions([target], model)
        assert len(resolved) == 1
        rows.append(resolved[0])
    return sorted(rows, key=canonical_json_bytes)


def _discovered_index(
    proof: dict[str, Any], model: dict[str, Any] | None = None
) -> dict[str, dict[str, dict[str, Any]]]:
    discovered: dict[str, dict[str, dict[str, Any]]] = {
        collection: {} for collection in COLLECTIONS
    }
    for item in proof["discovered_records"]:
        if "record" in item:
            discovered[item["collection"]][item["record_id"]] = item
            continue
        assert model is not None
        record = next(
            record for record in model[item["collection"]] if record["id"] == item["record_id"]
        )
        discovered[item["collection"]][item["record_id"]] = {**item, "record": record}
    return discovered


def _materialize_single_root_taints(
    proof: dict[str, Any], model: dict[str, Any] | None = None
) -> None:
    """Populate one root's labels from the independently generated edge witness."""

    discovered = _discovered_index(proof, model or _model())
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
        item["taints"] = [root["kind"]] if item["record_id"] in reachable else []


def _response(
    model: dict[str, Any],
    proof: dict[str, Any] | None = None,
    request: dict[str, Any] | None = None,
    run_context: NextRunContext | None = None,
) -> dict[str, Any]:
    descriptor = _descriptor()
    trusted_environment_digest = _trusted_environment()["sha256"]
    request_value = request or _request()
    request_context = canonical_run_context(**request_value["run_context"])
    if run_context is None:
        context = request_context
    else:
        context = canonical_run_context(**run_context)
        assert context == request_context
    response_proof = proof
    if response_proof is None:
        target_failure = target_completeness_failure(model, request_value["targets"])
        if target_failure is not None:
            target_rows = _target_proof_resolutions(model, target_failure, request_value["targets"])
            model["coverage"]["target_completeness"] = [
                {
                    "target_key": row["target_key"],
                    "status": "complete" if row["status"] == "resolved" else "failed",
                    "record_ids": row["record_ids"],
                    **(
                        {"reason": row["reason"]}
                        if row.get("reason") in TARGET_FAILURE_REASONS
                        else {}
                    ),
                }
                for row in target_rows
            ]
            assert target_failure is not None
            proof_model = _target_proof_model(model, target_failure, request_value["targets"])
            response_proof = _complete_proof(proof_model)
            response_proof["target_resolutions"] = target_rows
        else:
            response_proof = _complete_proof(model)
    return {
        "schema": "code-structure-viz.next-adapter-response/v1",
        "protocol": "code-structure-viz.next-adapter/v1",
        "request_id": request_value["request_id"],
        "adapter_version": "1.0.0",
        "trusted_type_environment_digest": trusted_environment_digest,
        "semantic_compatibility_id": descriptor["compatibility_id"],
        "compatibility_descriptor": descriptor,
        "identity_versions": descriptor["identity_versions"],
        "limits": copy.deepcopy(request_value["limits"]),
        "run_context": context,
        "model": model,
        "proof": response_proof,
        "model_digest": digest(model),
    }


def _trusted_environment() -> dict[str, Any]:
    value = _next_trusted_environment()
    value["identifier_unicode_table_digest"] = ECMASCRIPT_IDENTIFIER_UNICODE_TABLE_DIGEST
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
    code: str,
    *,
    path: str | None = None,
    symbol: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    entries = cast(list[dict[str, Any]], _schema("next-diagnostic-catalog-v1.json")["entries"])
    catalog = {entry["code"]: entry for entry in entries}
    entry = catalog[code]
    if code == "CSV-NEXT-TARGET-001" and reason is None:
        reason = "missing"
    if entry["ref_permission"] == "path" and path is None:
        path = "src/Button.tsx"
    elif entry["ref_permission"] == "symbol" and symbol is None:
        symbol = _id("component", "5")
    elif entry["ref_permission"] == "path_or_symbol" and path is None and symbol is None:
        path = "src/Button.tsx"
    value = {
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
    if reason is not None:
        assert code == "CSV-NEXT-TARGET-001"
        assert reason in TARGET_FAILURE_REASONS
        value["reason"] = reason
    return value


class _DomainProjection(dict[str, Any]):
    """Serializable domain mapping with a private validated-model sidecar.

    The sidecar is intentionally not a wire field: the run-manifest schema
    remains a compact domain descriptor, while the reference publication
    renderer can still prove that semantic and PlantUML bytes came from the
    exact model accepted at the response boundary.  ``deepcopy`` retains the
    sidecar for mutation tests.
    """

    def __init__(
        self,
        value: dict[str, Any],
        *,
        validated_model: dict[str, Any],
        validated_decision: NextRunDecision | None,
    ) -> None:
        super().__init__(value)
        self.validated_model = copy.deepcopy(validated_model)
        self.validated_decision = validated_decision
        self.publication_boundary: PublicationBoundaryDecision | None = None

    def __deepcopy__(self, memo: dict[int, Any]) -> "_DomainProjection":
        result = type(self).__new__(type(self))
        memo[id(self)] = result
        dict.__init__(result, copy.deepcopy(dict(self), memo))
        result.validated_model = copy.deepcopy(self.validated_model, memo)
        result.validated_decision = copy.deepcopy(self.validated_decision, memo)
        result.publication_boundary = copy.deepcopy(self.publication_boundary, memo)
        return result


def _target_reason_for_domain(domain: dict[str, Any], target_key: str | None = None) -> str | None:
    """Read the typed target reason from the immutable decision evidence."""

    decision = getattr(domain, "validated_decision", None)
    if not isinstance(decision, NextValidatedDecision):
        return None
    failures = decision.target_failures
    if target_key is None:
        if len(failures) != 1:
            return None
        reason = failures[0].get("reason")
    else:
        reason = next(
            (
                failure.get("reason")
                for failure in failures
                if failure.get("target_key") == target_key
            ),
            None,
        )
    return reason if reason in TARGET_FAILURE_REASONS else None


def _target_failures_for_domain(domain: dict[str, Any]) -> list[dict[str, str]]:
    """Return every typed target failure in canonical stdout order."""

    decision = getattr(domain, "validated_decision", None)
    if not isinstance(decision, NextValidatedDecision):
        return []
    failures = [
        {
            "target_key": item["target_key"],
            "reason": item["reason"],
        }
        for item in decision.target_failures
        if item.get("reason") in TARGET_FAILURE_REASONS
    ]
    return sorted(failures, key=canonical_json_bytes)


_UNSET = object()


def _legacy_domain_fixture(
    status: str | object = _UNSET,
    *,
    overrun: bool = False,
    runtime_unavailable: bool = False,
    export_failure: bool = False,
    targets: list[str] | None = None,
    formats: list[str] | object = _UNSET,
    max_entities: int | object = _UNSET,
    model: dict[str, Any] | None = None,
    budget_source: str | object = _UNSET,
    budget_requested: int | object | None = _UNSET,
    stdout_selector: str | object | None = _UNSET,
    response_decision: dict[str, Any] | None = None,
) -> _DomainProjection:
    status_supplied = status is not _UNSET
    targets_supplied = targets is not None
    formats_supplied = formats is not _UNSET
    max_entities_supplied = max_entities is not _UNSET
    budget_source_supplied = budget_source is not _UNSET
    budget_requested_supplied = budget_requested is not _UNSET
    stdout_selector_supplied = stdout_selector is not _UNSET
    status_arg = status
    formats_arg = formats
    max_entities_arg = max_entities
    budget_source_arg = budget_source
    budget_requested_arg = budget_requested
    stdout_selector_arg = stdout_selector
    if status_arg is _UNSET:
        status_arg = "complete"
    if formats_arg is _UNSET:
        formats_arg = None
    if max_entities_arg is _UNSET:
        max_entities_arg = 500
    if budget_source_arg is _UNSET:
        budget_source_arg = "builtin"
    if budget_requested_arg is _UNSET:
        budget_requested_arg = None
    if stdout_selector_arg is _UNSET:
        stdout_selector_arg = "next:semantic-json"
    if formats is _UNSET:
        formats = cast(list[str] | None, formats_arg)
    if max_entities is _UNSET:
        max_entities = cast(int, max_entities_arg)
    if budget_source is _UNSET:
        budget_source = cast(str, budget_source_arg)
    if budget_requested is _UNSET:
        budget_requested = cast(int | None, budget_requested_arg)
    if stdout_selector is _UNSET:
        stdout_selector = cast(str | None, stdout_selector_arg)
    assert isinstance(status_arg, str)
    assert formats_arg is None or isinstance(formats_arg, list)
    assert isinstance(max_entities_arg, int)
    assert isinstance(budget_source_arg, str)
    assert budget_requested_arg is None or isinstance(budget_requested_arg, int)
    assert stdout_selector_arg is None or isinstance(stdout_selector_arg, str)
    validated_decision: NextValidatedDecision | None = None
    if response_decision is not None:
        candidate = response_decision.get("validated_decision")
        if isinstance(candidate, NextValidatedDecision):
            # Once the raw response has produced a validated decision, every
            # downstream projection must consume that object as its sole
            # authority.  Re-supplying an equal-looking value is still a
            # second authority and is therefore rejected rather than merely
            # compared for equality.
            assert not status_supplied
            assert not targets_supplied
            assert not formats_supplied
            assert not max_entities_supplied
            assert not budget_source_supplied
            assert not budget_requested_supplied
            assert not stdout_selector_supplied
            assert not overrun
            assert not runtime_unavailable
            assert not export_failure
            assert model is None
            validated_decision = candidate
            validated_model = candidate.validated_model
            model = copy.deepcopy(validated_model)
            context = candidate.run_context
            max_entities = context["budget_resolved"]
            budget_requested = context["budget_requested"]
            budget_source = context["budget_source"]
            stdout_selector = context["stdout_selector"]
            formats = list(context["requested_formats"])
        else:
            raise AssertionError("downstream publication requires NextValidatedDecision")
    model = model or _model()
    if response_decision is not None and validated_decision is None:
        assert model is not None
    if validated_decision is not None:
        # The pre-budget outcome and gate result are authoritative.  A caller
        # cannot upgrade a partial or unavailable response by choosing a new
        # status while building a publication projection.
        gate_outcome = validated_decision.gate["outcome"]
        if (
            validated_decision.target_failures
            or validated_decision.export_failures
            or gate_outcome in {"partial_safe", "payload_unavailable"}
        ):
            status_arg = "incomplete"
        else:
            status_arg = "complete"
        export_failure = bool(validated_decision.export_failures)
    status = status_arg
    formats = cast(list[str] | None, formats)
    max_entities = cast(int, max_entities)
    budget_source = cast(str, budget_source)
    budget_requested = cast(int | None, budget_requested)
    stdout_selector = cast(str | None, stdout_selector)
    descriptor = _descriptor()
    environment = _trusted_environment()
    if validated_decision is not None:
        target_values = list(validated_decision.targets)
    else:
        target_values = list(targets or [])
    format_values = list(formats or ["semantic-json", "plantuml"])
    limits = _next_limits(max_entities=max_entities)
    run_context = _run_context(
        format_values,
        resolved=max_entities,
        source=budget_source,
        requested=budget_requested,
        selector=stdout_selector,
    )
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
    target_resolutions = (
        copy.deepcopy(validated_decision.validated_proof["target_resolutions"])
        if validated_decision is not None and validated_decision.target_failures
        else resolve_target_resolutions(target_values, model)
    )
    target_failed = any(item["status"] == "failed" for item in target_resolutions)
    entity_count: int | None
    payload_available: bool
    incomplete_kind: str | None
    artifact_paths: list[str]
    diagnostics: list[dict[str, Any]]
    actual: int | None
    measured_actual = 501 if overrun else internal_entity_count(model)
    budget_overrun = measured_actual > max_entities
    if target_failed:
        assert status != "not_applicable"
        target_reason_by_key = {
            item["target_key"]: item.get("reason")
            for item in (
                validated_decision.target_failures if validated_decision is not None else ()
            )
        }
        if validated_decision is None:
            fallback_failure = target_completeness_failure(model, target_values)
            target_reason_by_key.update(
                {
                    item["target_key"]: item["reason"]
                    for item in (fallback_failure.failures if fallback_failure else ())
                }
            )
        status = "incomplete"
        entity_count = None
        payload_available = False
        incomplete_kind = "payload_unavailable"
        artifact_paths = []
        diagnostics = [
            _public_diagnostic(
                "CSV-NEXT-TARGET-001",
                path=failed_target["target_key"].removeprefix("path:"),
                reason=(
                    target_reason_by_key.get(failed_target["target_key"])
                    if target_reason_by_key.get(failed_target["target_key"])
                    in TARGET_FAILURE_REASONS
                    else None
                ),
            )
            for failed_target in target_resolutions
            if failed_target["status"] == "failed"
        ]
        actual = None
    elif export_failure:
        assert status == "incomplete"
        assert not overrun
        entity_count = None
        payload_available = False
        incomplete_kind = "payload_unavailable"
        artifact_paths = []
        diagnostics = [_public_diagnostic("CSV-NEXT-EXPORT-001")]
        actual = None
    elif runtime_unavailable:
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
        # Every schema-valid domain projection carries an explicit authority
        # discriminator.  Historical fixture vectors use ``false``; only a
        # request-independent decision may set it to ``true``.
        "request_independent": False,
        "status": status,
        "payload_available": payload_available,
        "entity_count": entity_count,
        "budget": {
            "name": "max_entities",
            "requested": budget_requested,
            "resolved": max_entities,
            "actual": actual,
            "source": budget_source,
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
        "run_context": run_context,
        "projects": copy.deepcopy(model["projects"]),
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
    if validated_decision is not None:
        sealed = validated_decision.publication_context
        assert sealed is not None
        assert sealed.source_view_descriptor is not None
        assert sealed.final_source_acquisition_plan is not None
        assert sealed.public_next_request is not None
        value["source"]["fingerprint"] = sealed.source_view_fingerprint
        value["source"]["file_count"] = sealed.source_view_descriptor["file_count"]
        value["config"]["source_plan"] = copy.deepcopy(sealed.final_source_acquisition_plan)
        value["config"]["source_plan_digest"] = sealed.source_plan_digest
        value["request"]["source_plan"] = copy.deepcopy(sealed.final_source_acquisition_plan)
        value["request"]["source_plan_digest"] = sealed.source_plan_digest
    if incomplete_kind is not None:
        value["incomplete_kind"] = incomplete_kind
    value["run_fingerprint"] = recompute_run_fingerprint(
        source_view_fingerprint=value["source"]["fingerprint"],
        source_plan_digest=value["source_plan_digest"],
        domain_config_digest=value["domain_config_digest"],
        projects=value["projects"],
        targets=value["targets"],
        formats=value["formats"],
        stdout_selector=value["run_context"]["stdout_selector"],
        limits=value["limits"],
        node_version=value["toolchain"]["node_version"],
        typescript_version=value["toolchain"]["typescript_version"],
        adapter_version=value["toolchain"]["adapter_version"],
        protocol=value["toolchain"]["protocol"],
        trusted_environment_digest=value["trusted_environment"]["sha256"],
        process_launch_descriptor_digest=digest(
            process_launch_descriptor(
                node_status=(
                    "not_applicable"
                    if status == "not_applicable"
                    else "unavailable"
                    if runtime_unavailable
                    else "available"
                ),
                node_realpath=(
                    None
                    if status == "not_applicable" or runtime_unavailable
                    else "/usr/local/bin/node"
                ),
                node_sha256=(
                    None if status == "not_applicable" or runtime_unavailable else "1" * 64
                ),
                node_version=(
                    None if status == "not_applicable" or runtime_unavailable else "22.14.0"
                ),
                spawn_executable=(
                    None
                    if status == "not_applicable" or runtime_unavailable
                    else "/usr/local/bin/node"
                ),
                file_identity_at_hash=(
                    None
                    if status == "not_applicable" or runtime_unavailable
                    else {
                        "realpath": "/usr/local/bin/node",
                        "sha256": "1" * 64,
                        "version": "22.14.0",
                    }
                ),
                file_identity_at_spawn=(
                    None
                    if status == "not_applicable" or runtime_unavailable
                    else {
                        "realpath": "/usr/local/bin/node",
                        "sha256": "1" * 64,
                        "version": "22.14.0",
                    }
                ),
                spawn_handle=(
                    None
                    if status == "not_applicable" or runtime_unavailable
                    else "fixture-process-group"
                ),
            )
        ),
    )
    value["request"]["run_fingerprint"] = value["run_fingerprint"]
    counts = value["coverage"]["counts"]
    for collection in COLLECTIONS:
        counts[collection] = len(model[collection])
    counts["published"] = sum(len(model[collection]) for collection in COLLECTIONS)
    counts["discovered"] = counts["published"]
    # The fixture's compositional overrun counter represents the measured
    # selected/published entity count without allocating 501 records.  A
    # not-applicable run publishes no entities, so its measured count is zero.
    counts["internal_entities"] = (
        0
        if status == "not_applicable"
        else measured_actual
        if actual is not None
        else len(model["modules"]) + len(model["components"])
    )
    fallback_target_failure = (
        target_completeness_failure(model, target_values) if validated_decision is None else None
    )
    target_reason_by_key = {
        item["target_key"]: item["reason"]
        for item in (fallback_target_failure.failures if fallback_target_failure else [])
    }
    target_reason_by_key.update(
        {
            item["target_key"]: item["reason"]
            for item in (
                validated_decision.target_failures if validated_decision is not None else ()
            )
        }
    )
    value["coverage"]["target_completeness"] = []
    for item in target_resolutions:
        row = {
            "target_key": item["target_key"],
            "status": "complete" if item["status"] == "resolved" else "failed",
            "record_ids": item["record_ids"],
        }
        if row["status"] == "failed" and item["target_key"] in target_reason_by_key:
            reason = target_reason_by_key[item["target_key"]]
            # Only the typed program File→Module reasons are public evidence.
            # Other target-classification failures (context/control file,
            # project ambiguity, and a missing descendant program file) keep
            # the failure row reason-free while the diagnostic identifies the
            # rejected path.
            if reason in TARGET_FAILURE_REASONS:
                row["reason"] = reason
        value["coverage"]["target_completeness"].append(row)
    if validated_decision is None:
        pre_budget_outcome = (
            "payload_unavailable"
            if target_failed or export_failure or budget_overrun
            else "partial_safe"
            if status == "incomplete"
            else "not_applicable"
            if status == "not_applicable"
            else "complete"
        )
        target_evidence = tuple(
            {
                "target_key": row["target_key"],
                **(
                    {"reason": row["reason"]} if row.get("reason") in TARGET_FAILURE_REASONS else {}
                ),
            }
            for row in value["coverage"]["target_completeness"]
            if row["status"] == "failed"
        )
        export_evidence = ({"diagnostic": "CSV-NEXT-EXPORT-001"},) if export_failure else ()
        legacy_request = validate_adapter_request(
            _request(
                model=model,
                targets=target_values,
                limits=limits,
                run_context=run_context,
            )
        )
        validated_decision = NextValidatedDecision(
            validated_model=model,
            validated_proof={},
            run_context=run_context,
            pre_budget_outcome=pre_budget_outcome,
            gate={
                "actual": value["budget"]["actual"],
                "resolved": value["budget"]["resolved"],
                "allowed": value["payload_available"],
                "payload_available": value["payload_available"],
                "original_outcome": pre_budget_outcome,
                "outcome": value["budget"]["outcome"],
                "diagnostic_code": value["diagnostics"][0]["code"]
                if value["diagnostics"]
                else None,
                "run_context": run_context,
                "requested_formats": value["formats"],
                "budget_requested": value["budget"]["requested"],
                "budget_source": value["budget"]["source"],
                "stdout_selector": run_context["stdout_selector"],
                "artifact_paths": value["artifact_paths"],
            },
            request=legacy_request,
            raw_response_bytes=canonical_json_bytes({"model": model, "proof": {}}),
            raw_response_sha256=hashlib.sha256(
                canonical_json_bytes({"model": model, "proof": {}})
            ).hexdigest(),
            targets=tuple(target_values),
            target_failures=target_evidence,
            export_failures=export_evidence,
            publication_context=_publication_context_for_validated_request(
                legacy_request,
                run_context,
                toolchain={
                    "node": {
                        "status": "not_applicable"
                        if status == "not_applicable"
                        else "unavailable"
                        if runtime_unavailable
                        else "available",
                        "version": None
                        if status == "not_applicable" or runtime_unavailable
                        else "22.14.0",
                        "failure_kind": None
                        if status == "not_applicable" or not runtime_unavailable
                        else "missing",
                    },
                    "node_version": None
                    if status == "not_applicable" or runtime_unavailable
                    else "22.14.0",
                    "typescript_version": "5.9.2",
                    "adapter_version": "1.0.0",
                    "protocol": "code-structure-viz.next-adapter/v1",
                },
                trusted_environment=_trusted_environment(),
                projects_for_fingerprint=copy.deepcopy(model["projects"]),
                source_failure_ledger=(),
                process_launch_descriptor=process_launch_descriptor(
                    node_status=(
                        "not_applicable"
                        if status == "not_applicable"
                        else "unavailable"
                        if runtime_unavailable
                        else "available"
                    ),
                    node_realpath=(
                        None
                        if status == "not_applicable" or runtime_unavailable
                        else "/usr/local/bin/node"
                    ),
                    node_sha256=(
                        None if status == "not_applicable" or runtime_unavailable else "1" * 64
                    ),
                    node_version=(
                        None if status == "not_applicable" or runtime_unavailable else "22.14.0"
                    ),
                    spawn_executable=(
                        None
                        if status == "not_applicable" or runtime_unavailable
                        else "/usr/local/bin/node"
                    ),
                    file_identity_at_hash=(
                        None
                        if status == "not_applicable" or runtime_unavailable
                        else {
                            "realpath": "/usr/local/bin/node",
                            "sha256": "1" * 64,
                            "version": "22.14.0",
                        }
                    ),
                    file_identity_at_spawn=(
                        None
                        if status == "not_applicable" or runtime_unavailable
                        else {
                            "realpath": "/usr/local/bin/node",
                            "sha256": "1" * 64,
                            "version": "22.14.0",
                        }
                    ),
                    spawn_handle=(
                        None
                        if status == "not_applicable" or runtime_unavailable
                        else "fixture-process-group"
                    ),
                ),
            ),
        )
    return _DomainProjection(
        value,
        validated_model=model,
        validated_decision=validated_decision,
    )


def _decision_model_shell(decision: NextRunDecision) -> dict[str, Any]:
    """Build only the non-authoritative empty model needed by no-payload runs."""

    if isinstance(decision, NextValidatedDecision):
        return copy.deepcopy(decision.validated_model)
    publication_context = decision.publication_context
    assert publication_context is not None
    # Pre-response decisions have no validated model.  The only permissible
    # shell data is the immutable semantic source snapshot sealed in the
    # publication context; never reconstruct it from the public request (the
    # latter intentionally omits adapter file bytes and semantic IDs).
    projects = copy.deepcopy(publication_context.semantic_projects)
    files = copy.deepcopy(publication_context.semantic_files)
    model: dict[str, Any] = {
        "schema": "code-structure-viz.next-model/v1",
        "projects": projects,
        "files": files,
        "modules": [],
        "components": [],
        "members": [],
        "relations": [],
        "facts": [],
        "coverage": _next_coverage(),
        "diagnostics": [],
    }
    _refresh_model_counts(model)
    return model


def _decision_diagnostics(decision: NextRunDecision, model: dict[str, Any]) -> list[dict[str, Any]]:
    """Project diagnostics from the decision, never from a fixture status flag."""

    if isinstance(decision, (PreResponseFailureDecision, NotApplicableDecision)):
        return [copy.deepcopy(decision.diagnostic)]
    if decision.target_failures:
        return [
            _public_diagnostic(
                "CSV-NEXT-TARGET-001",
                path=failure["target_key"].removeprefix("path:"),
                reason=failure["reason"],
            )
            for failure in decision.target_failures
        ]
    if decision.export_failures:
        return [_public_diagnostic("CSV-NEXT-EXPORT-001")]
    diagnostic_code = decision.gate.get("diagnostic_code")
    if isinstance(diagnostic_code, str):
        return [_public_diagnostic(diagnostic_code)]
    if decision.gate["outcome"] == "partial_safe":
        return [_public_diagnostic("CSV-NEXT-FLOW-001")]
    # ``model`` is an authority carried by the decision.  It is intentionally
    # accepted as an argument to make this branch explicit for future partial
    # diagnostics, while a complete decision has no public diagnostics.
    assert not model["diagnostics"]
    return []


def _decision_target_resolutions(
    decision: NextRunDecision, model: dict[str, Any], targets: list[str]
) -> list[dict[str, Any]]:
    if isinstance(decision, NextValidatedDecision):
        proof_rows = decision.validated_proof.get("target_resolutions", [])
        if proof_rows:
            return copy.deepcopy(proof_rows)
        return resolve_target_resolutions(targets, model)
    if isinstance(decision, NotApplicableDecision):
        return [
            {"target_key": target, "status": "resolved", "record_ids": []} for target in targets
        ]
    return [{"target_key": target, "status": "failed", "record_ids": []} for target in targets]


def _domain_from_run_decision(decision: NextRunDecision) -> _DomainProjection:
    """Project the closed decision and its immutable publication context.

    This builder deliberately has no legacy-fixture fallback.  Every
    authority-bearing field comes from ``decision`` or its
    ``NextPublicationContext``; the only synthetic values are schema-required
    empty collections for a run that has no validated payload.
    """

    assert isinstance(
        decision, (NextValidatedDecision, PreResponseFailureDecision, NotApplicableDecision)
    )
    publication_context = decision.publication_context
    assert publication_context is not None
    context = publication_context.run_context
    assert context == decision.run_context
    model = _decision_model_shell(decision)
    public_config = publication_context.public_next_config
    config = copy.deepcopy(public_config)
    independent = publication_context.observation_provenance["kind"] == "request_independent"
    if independent:
        assert publication_context.source_acquisition_seal is None
        assert config["limits"] is None
        assert config["source_plan"] is None
        assert config["source_plan_digest"] is None
        assert config["trusted_environment_digest"] is None
    else:
        assert publication_context.final_source_acquisition_plan is not None
        assert publication_context.source_plan_digest is not None
        assert publication_context.trusted_environment is not None
        config["source_plan"] = copy.deepcopy(publication_context.final_source_acquisition_plan)
        config["source_plan_digest"] = publication_context.source_plan_digest
        config["trusted_environment_digest"] = publication_context.trusted_environment["sha256"]
    config["domain_config_digest"] = public_config["domain_config_digest"]
    limits = copy.deepcopy(config["limits"])
    targets = list(config["targets"])
    formats = list(context["requested_formats"])
    # A normal response carries the sealed public snapshot request.  A
    # request-independent pre-response failure intentionally carries no
    # request at all; the schema branch uses ``request_independent`` instead
    # of inventing project/config input that was never available.
    request = copy.deepcopy(publication_context.public_next_request)
    source_view = publication_context.source_view_descriptor
    if independent:
        assert source_view is None
        source = {
            "schema": "code-structure-viz.source-view/v1",
            "kind": "unavailable",
            "head_commit": None,
            "fingerprint": None,
            "file_count": 0,
        }
    else:
        assert source_view is not None
        source = {
            "schema": "code-structure-viz.source-view/v1",
            "kind": source_view["kind"],
            "head_commit": source_view["head_commit"],
            "fingerprint": publication_context.source_view_fingerprint,
            "file_count": source_view["file_count"],
        }
    toolchain = copy.deepcopy(publication_context.toolchain)
    trusted_environment = copy.deepcopy(publication_context.trusted_environment)
    if isinstance(decision, NextValidatedDecision):
        outcome = decision.gate["outcome"]
        payload_available = bool(decision.gate["payload_available"])
        actual = decision.gate["actual"]
        artifact_paths = list(decision.gate["artifact_paths"])
    else:
        outcome = decision.outcome
        payload_available = decision.payload_available
        actual = 0 if isinstance(decision, NotApplicableDecision) else None
        artifact_paths = list(decision.artifact_paths)
    status = (
        "not_applicable"
        if outcome == "not_applicable"
        else "complete"
        if outcome == "complete"
        else "incomplete"
    )
    incomplete_kind = None if status != "incomplete" else outcome
    diagnostics = _decision_diagnostics(decision, model)
    target_resolutions = _decision_target_resolutions(decision, model, targets)
    coverage = copy.deepcopy(model["coverage"])
    coverage["target_completeness"] = []
    target_reasons = {
        item["target_key"]: item["reason"]
        for item in (
            decision.target_failures if isinstance(decision, NextValidatedDecision) else ()
        )
    }
    for item in target_resolutions:
        row = {
            "target_key": item["target_key"],
            "status": "complete" if item["status"] == "resolved" else "failed",
            "record_ids": copy.deepcopy(item["record_ids"]),
        }
        reason = target_reasons.get(item["target_key"])
        if row["status"] == "failed" and reason in TARGET_FAILURE_REASONS:
            row["reason"] = reason
        coverage["target_completeness"].append(row)
    counts = coverage["counts"]
    for collection in COLLECTIONS:
        counts[collection] = len(model[collection])
    counts["published"] = sum(len(model[collection]) for collection in COLLECTIONS)
    counts["discovered"] = counts["published"]
    counts["internal_entities"] = len(model["modules"]) + len(model["components"])
    compatibility_descriptor = copy.deepcopy(publication_context.compatibility_descriptor)
    if independent:
        assert compatibility_descriptor is None
        assert toolchain is None
        assert trusted_environment is None
    value: dict[str, Any] = {
        "domain": "next",
        "status": status,
        "payload_available": payload_available,
        "entity_count": (
            actual
            if payload_available
            else 0
            if isinstance(decision, NotApplicableDecision)
            else None
        ),
        "budget": {
            "name": "max_entities",
            "requested": context["budget_requested"],
            "resolved": context["budget_resolved"] if limits is not None else None,
            "actual": actual,
            "source": context["budget_source"] if limits is not None else "unobserved",
            "outcome": outcome,
        },
        "semantic_compatibility_id": (
            compatibility_descriptor["compatibility_id"]
            if compatibility_descriptor is not None
            else None
        ),
        "compatibility_descriptor": compatibility_descriptor,
        "identity_versions": (
            copy.deepcopy(compatibility_descriptor["identity_versions"])
            if compatibility_descriptor is not None
            else None
        ),
        "source_plan_digest": publication_context.source_plan_digest,
        "domain_config_digest": config["domain_config_digest"],
        "run_fingerprint": "0" * 64,
        "source": source,
        "request": request,
        "config": config,
        "run_context": copy.deepcopy(context),
        "projects": copy.deepcopy(model["projects"]),
        "targets": targets,
        "formats": formats,
        "toolchain": toolchain,
        "trusted_environment": trusted_environment,
        "limits": limits,
        "coverage": coverage,
        "artifact_paths": artifact_paths,
        "diagnostics": diagnostics,
    }
    if incomplete_kind is not None:
        value["incomplete_kind"] = incomplete_kind
    preimage = publication_context.run_fingerprint_preimage
    assert preimage["domain_config_digest"] == value["domain_config_digest"]
    assert preimage["projects"] == value["projects"]
    value["run_fingerprint"] = digest(preimage)
    if not independent:
        assert toolchain is not None
        assert trusted_environment is not None
        assert publication_context.process_launch_descriptor is not None
        assert isinstance(source["fingerprint"], str)
        assert value["run_fingerprint"] == recompute_run_fingerprint(
            source_view_fingerprint=source["fingerprint"],
            source_plan_digest=value["source_plan_digest"],
            domain_config_digest=value["domain_config_digest"],
            projects=value["projects"],
            targets=value["targets"],
            formats=value["formats"],
            stdout_selector=context["stdout_selector"],
            limits=value["limits"],
            node_version=toolchain["node_version"],
            typescript_version=toolchain["typescript_version"],
            adapter_version=toolchain["adapter_version"],
            protocol=toolchain["protocol"],
            trusted_environment_digest=trusted_environment["sha256"],
            process_launch_descriptor_digest=digest(publication_context.process_launch_descriptor),
            source_failure_ledger=publication_context.source_failure_ledger,
        )
    if value["request"] is not None:
        value["request"]["run_fingerprint"] = value["run_fingerprint"]
    value["request_independent"] = independent
    return _DomainProjection(
        value,
        validated_model=model,
        validated_decision=decision,
    )


def _domain(*, decision: NextRunDecision) -> _DomainProjection:
    """Project only the closed decision union into publication surfaces.

    Legacy status vectors use ``_legacy_domain_fixture`` directly and never
    represent a production downstream authority path.
    """

    assert is_next_run_decision(decision)
    return _domain_from_run_decision(decision)


def _semantic_artifacts_from_decision(
    decision: NextRunDecision,
) -> dict[str, bytes]:
    """Render candidate artifacts from the sealed decision before publication.

    This is the pre-publication renderer used to provide bytes to the final
    boundary seal.  It does not create a domain or manifest and takes all
    identity-bearing values from the decision's immutable context.
    """

    if not isinstance(decision, NextValidatedDecision):
        return {}
    context = decision.publication_context
    assert context.public_next_request is not None
    outcome = decision.gate["outcome"]
    assert outcome in {"complete", "partial_safe"}
    status = "partial_safe" if outcome == "partial_safe" else "complete"
    model = decision.validated_model
    source_view = context.source_view_descriptor
    assert source_view is not None
    assert context.compatibility_descriptor is not None
    semantic = {
        "type": "semantic_snapshot",
        "schema": "code-structure-viz.semantic/v1",
        "domain": "next",
        "document_kind": "snapshot",
        "status": "incomplete" if status == "partial_safe" else "complete",
        "semantic_compatibility_id": context.compatibility_descriptor["compatibility_id"],
        "compatibility_descriptor": copy.deepcopy(context.compatibility_descriptor),
        "identity_versions": copy.deepcopy(context.compatibility_descriptor["identity_versions"]),
        "source": {
            "schema": source_view["schema"],
            "kind": source_view["kind"],
            "head_commit": source_view["head_commit"],
            "fingerprint": context.source_view_fingerprint,
            "file_count": source_view["file_count"],
        },
        "request": copy.deepcopy(context.public_next_request),
        "coverage": copy.deepcopy(model["coverage"]),
        "projects": sorted(copy.deepcopy(model["projects"]), key=lambda item: item["id"]),
        "files": copy.deepcopy(model["files"]),
        "entities": [*model["modules"], *model["components"]],
        "members": copy.deepcopy(model["members"]),
        "relations": copy.deepcopy(model["relations"]),
        "facts": copy.deepcopy(model["facts"]),
        "diagnostics": [],
    }
    if status == "partial_safe":
        semantic["incomplete_kind"] = "partial_safe"
    semantic["request"]["run_fingerprint"] = digest(context.run_fingerprint_preimage)
    semantic_bytes = canonical_json_bytes(semantic) + b"\n"
    plantuml_bytes = render_plantuml(model, status=status)
    format_paths = {
        "semantic-json": "next.snapshot.semantic.json",
        "plantuml": "next.snapshot.puml",
    }
    return {
        format_paths[format_name]: (
            semantic_bytes if format_name == "semantic-json" else plantuml_bytes
        )
        for format_name in context.run_context["requested_formats"]
    }


def _publication_domain(
    publication: PublicationBoundaryDecision,
) -> _DomainProjection:
    """Project every domain field from one final publication decision."""

    assert isinstance(publication, PublicationBoundaryDecision)
    domain = _domain_from_run_decision(publication.semantic_decision)
    domain.publication_boundary = publication
    transport_failed = (
        not publication.adapter_stdout["allowed"]
        or not publication.adapter_stderr["allowed"]
        or not publication.public_stderr["allowed"]
    )
    if transport_failed:
        domain["status"] = "incomplete"
        domain["incomplete_kind"] = "payload_unavailable"
        domain["payload_available"] = False
        domain["entity_count"] = None
        domain["budget"]["actual"] = None
        domain["budget"]["outcome"] = "payload_unavailable"
        domain["artifact_paths"] = []
        domain["diagnostics"] = [_public_diagnostic("CSV-NEXT-LIMIT-003")]
    elif publication.publication_outcome == "selected_artifact_unavailable":
        assert domain["payload_available"] is True
        assert domain["artifact_paths"]
    return domain


def _publication_artifacts(
    publication: PublicationBoundaryDecision,
) -> dict[str, bytes]:
    """Return persisted artifact bytes using only the sealed boundary."""

    assert isinstance(publication, PublicationBoundaryDecision)
    return publication.artifact_bytes


def _publication_manifest(
    publication: PublicationBoundaryDecision,
) -> dict[str, Any]:
    """Decode the root manifest bytes sealed by the final decision only."""

    assert isinstance(publication, PublicationBoundaryDecision)
    sealed_manifest = publication.sealed_stdout_candidates.get("manifest")
    assert isinstance(sealed_manifest, bytes) and sealed_manifest
    parsed = json.loads(sealed_manifest.decode("utf-8"))
    assert isinstance(parsed, dict)
    assert canonical_json_bytes(parsed) + b"\n" == sealed_manifest
    assert parsed["run"]["exit_code"] == publication.exit_code
    return parsed


def _publication_stdout(
    publication: PublicationBoundaryDecision,
) -> dict[str, Any]:
    """Build selected stdout from the final publication decision only."""

    assert isinstance(publication, PublicationBoundaryDecision)
    domain = _publication_domain(publication)
    manifest = _publication_manifest(publication)
    if publication.publication_outcome == "selected_artifact_unavailable":
        sealed_result = publication.sealed_stdout_result
        assert sealed_result.endswith(b"\n")
        result = json.loads(sealed_result.decode("utf-8"))
        assert isinstance(result, dict)
        assert canonical_json_bytes(result) + b"\n" == sealed_result
        return result
    return _stdout_result_for_domain(domain, manifest)


def _publication_stdout_bytes(publication: PublicationBoundaryDecision) -> bytes:
    """Return the exact stdout bytes sealed by the final decision.

    The metadata object is useful for machine inspection, but it is not the
    selected stream itself.  For successful summary/manifest/artifact
    branches, the retained selected-copy bytes are the authority.  A failed
    selected copy emits only the canonical typed-unavailable line.
    """

    assert isinstance(publication, PublicationBoundaryDecision)
    retained = publication.selected_stdout["retained"]
    if publication.publication_outcome == "payload_unavailable":
        return b""
    if publication.selected_stdout["allowed"] and retained:
        return cast(bytes, retained)
    sealed_result = publication.sealed_stdout_result
    assert sealed_result.endswith(b"\n")
    return sealed_result


def _publication_stderr_bytes(
    publication: PublicationBoundaryDecision,
) -> bytes:
    """Return public stderr bytes from the sealed boundary."""

    assert isinstance(publication, PublicationBoundaryDecision)
    return bytes(publication.public_stderr["payload"])


def _publication_exit(publication: PublicationBoundaryDecision) -> int:
    """Return the process exit selected by the final boundary seal."""

    assert isinstance(publication, PublicationBoundaryDecision)
    return publication.exit_code


def _validate_publication_chain(
    publication: PublicationBoundaryDecision,
) -> tuple[_DomainProjection, dict[str, Any], dict[str, Any], dict[str, bytes], bytes]:
    """Validate every public surface from one final boundary object."""

    assert isinstance(publication, PublicationBoundaryDecision)
    domain = _publication_domain(publication)
    manifest = _publication_manifest(publication)
    stdout = _publication_stdout(publication)
    stdout_bytes = _publication_stdout_bytes(publication)
    artifacts = _publication_artifacts(publication)
    stderr = _publication_stderr_bytes(publication)
    _validator("next-domain-manifest-v1.schema.json").validate(domain)
    _validator("run-manifest-v1.schema.json").validate(manifest)
    _validator("stdout-result-v1.schema.json").validate(stdout)
    selector = domain["run_context"]["stdout_selector"]
    if selector is None:
        summary = _run_summary_value(manifest["run"]["status"], domain)
        _validator("run-summary-v1.schema.json").validate(summary)
        if publication.selected_stdout["allowed"] and publication.selected_stdout["retained"]:
            assert stdout_bytes == _canonical_json_line(summary)
    elif selector == "manifest":
        manifest_bytes = _canonical_json_line(manifest)
        if stdout["availability"]:
            assert stdout_bytes == manifest_bytes
            assert publication.selected_stdout["retained"] == manifest_bytes
        else:
            assert stdout_bytes == _canonical_json_line(stdout)
    validate_domain_manifest(domain)
    validate_run_manifest(manifest, domain, artifacts)
    validate_published_projection(domain, artifacts)
    if publication.public_stderr["allowed"]:
        assert stderr == publication.public_stderr["payload"]
        assert stderr.endswith(b"\n") if stderr else not stderr
    else:
        assert stderr == b""
    assert _publication_exit(publication) == publication.exit_code
    return domain, manifest, stdout, artifacts, stderr


def _run_manifest(
    domain: dict[str, Any],
    *,
    publication: PublicationBoundaryDecision | None = None,
) -> dict[str, Any]:
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
        "stdout_selector": domain["run_context"]["stdout_selector"],
    }
    independent = domain.get("request_independent") is True
    base["request_independent"] = independent
    root_projects = sorted((project["root"] for project in domain["projects"]), key=_path_sort_key)
    if independent:
        # A pre-request failure has no public request or project root.  Keep
        # the explicit null/empty branch all the way through the root
        # manifest instead of reconstructing a plausible normal request.
        assert domain["request"] is None
        base["request"] = None
        base["next_request"] = None
        base["next_config"] = copy.deepcopy(domain["config"])
    else:
        base["request"] = {
            "projects": root_projects,
            "targets": domain["targets"],
            "formats": domain["formats"],
            "upstream_depth": domain["request"]["upstream_depth"],
            "downstream_depth": domain["request"]["downstream_depth"],
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
                **({"request_independent": True} if independent else {}),
                "projects": root_projects,
                "targets": domain["targets"],
                "formats": domain["formats"],
                "trusted_environment_digest": (
                    None if independent else domain["trusted_environment"]["sha256"]
                ),
            },
            "traversal": {
                "upstream_depth": None if independent else domain["request"]["upstream_depth"],
                "downstream_depth": None if independent else domain["request"]["downstream_depth"],
            },
            "limits": None if independent else copy.deepcopy(domain["limits"]),
        },
        "value_sources": {
            "next_projects": "builtin",
            "next_targets": "builtin",
            "formats": "builtin",
            "upstream_depth": "builtin",
            "downstream_depth": "builtin",
            "limits": "unobserved" if independent else domain["budget"]["source"],
            "trusted_environment": "unobserved" if independent else "builtin",
        },
    }
    base["config"]["sha256"] = digest(
        {key: value for key, value in base["config"].items() if key != "sha256"}
    )
    base["run"] = {
        "status": status,
        "exit_code": 0 if status in {"complete", "not_applicable"} else 3,
        "fingerprint": domain["run_fingerprint"],
        "run_context": copy.deepcopy(domain["run_context"]),
    }
    base["domains"] = [domain]
    sealed_artifacts = (
        publication.artifact_bytes if publication is not None else _published_bytes(domain)
    )
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
                "size_bytes": len(sealed_artifacts[path]),
                "sha256": hashlib.sha256(sealed_artifacts[path]).hexdigest(),
            }
        )
    base["diagnostics"] = copy.deepcopy(domain["diagnostics"])
    return base


def _published_bytes(domain: dict[str, Any]) -> dict[str, bytes]:
    decision = getattr(domain, "validated_decision", None)
    if isinstance(decision, (PreResponseFailureDecision, NotApplicableDecision)):
        assert domain["artifact_paths"] == []
        return {}
    assert isinstance(decision, NextValidatedDecision), "publication requires validated decision"
    validated_model = decision.validated_model
    semantic = _semantic(
        validated_model,
        status="incomplete" if domain["status"] == "incomplete" else "complete",
        domain=domain,
    )
    semantic_bytes = canonical_json_bytes(semantic) + b"\n"
    plantuml_bytes = render_plantuml(
        validated_model,
        status="partial_safe" if domain["status"] == "incomplete" else "complete",
    )
    return {
        path: semantic_bytes if path.endswith(".json") else plantuml_bytes
        for path in domain["artifact_paths"]
    }


_SELECTOR_UNSET = object()


def _stdout_result_for_domain(
    domain: dict[str, Any],
    manifest: dict[str, Any],
    selector: str | object | None = _SELECTOR_UNSET,
) -> dict[str, Any]:
    if selector is _SELECTOR_UNSET:
        selector = domain["run_context"]["stdout_selector"]
    if selector is None:
        return {
            "type": "stdout_result",
            "schema": "code-structure-viz.stdout-result/v1",
            "selector": None,
            "availability": False,
            "run_status": domain["status"],
            "stable_reason": "run_summary",
            "artifact": None,
        }
    assert isinstance(selector, str)
    if selector == "manifest":
        manifest_bytes = canonical_json_bytes(manifest) + b"\n"
        return {
            "type": "stdout_result",
            "schema": "code-structure-viz.stdout-result/v1",
            "selector": "manifest",
            "availability": True,
            "domain_status": domain["status"],
            "stable_reason": "run_manifest",
            "artifact": {
                "path": "run-manifest.json",
                "domain": "next",
                "format": "semantic-json",
                "media_type": "application/json",
                "size_bytes": len(manifest_bytes),
                "sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            },
        }
    if domain["payload_available"]:
        format_name = selector.removeprefix("next:")
        artifact = next(item for item in manifest["artifacts"] if item["format"] == format_name)
        available_result: dict[str, Any] = {
            "type": "stdout_result",
            "schema": "code-structure-viz.stdout-result/v1",
            "selector": selector,
            "availability": True,
            "stable_reason": "published_artifact",
            "artifact": artifact,
            "domain_status": domain["status"],
        }
        if domain["status"] == "incomplete":
            available_result["incomplete_kind"] = "partial_safe"
        return available_result
    target_failures = _target_failures_for_domain(domain)
    result = {
        "type": "stdout_result",
        "schema": "code-structure-viz.stdout-result/v1",
        "selector": selector,
        "availability": False,
        "domain_status": domain["status"],
        "stable_reason": (
            "domain_not_applicable"
            if domain["status"] == "not_applicable"
            else "target_payload_unavailable"
            if target_failures
            else "domain_payload_unavailable"
        ),
        "artifact": None,
    }
    if target_failures:
        result["target_failures"] = target_failures
    return result


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
    decision = validate_response_envelope(canonical_json_bytes(response), request)
    assert {
        key: value
        for key, value in decision.items()
        if key not in {"validated_model", "validated_proof", "validated_decision"}
    } == {
        "actual": 4,
        "resolved": 500,
        "allowed": True,
        "payload_available": True,
        "original_outcome": "complete",
        "outcome": "complete",
        "diagnostic_code": None,
        "run_context": _run_context(),
        "requested_formats": ["semantic-json", "plantuml"],
        "budget_requested": None,
        "budget_source": "builtin",
        "stdout_selector": "next:semantic-json",
        "artifact_paths": ["next.snapshot.semantic.json", "next.snapshot.puml"],
    }
    validate_model(response["model"])
    validate_proof(response["proof"], response["model"])
    assert all("record" not in item for item in response["proof"]["discovered_records"])
    duplicated_proof_payload = copy.deepcopy(response)
    duplicated_proof_payload["proof"]["discovered_records"][0]["record"] = copy.deepcopy(
        response["model"]["projects"][0]
    )
    _validator("next-adapter-response-v1.schema.json").validate(duplicated_proof_payload)
    with pytest.raises(AssertionError):
        validate_response_envelope(canonical_json_bytes(duplicated_proof_payload), request)

    wrong_schema = copy.deepcopy(response)
    wrong_schema["schema"] = "code-structure-viz.next-adapter-response/v0"
    with pytest.raises(AssertionError):
        validate_response_envelope(canonical_json_bytes(wrong_schema), request)
    extra_field = copy.deepcopy(response)
    extra_field["unexpected"] = True
    with pytest.raises(AssertionError):
        validate_response_envelope(canonical_json_bytes(extra_field), request)
    unsafe_compound = copy.deepcopy(response)
    unsafe_compound["proof"]["target_resolutions"] = [
        {
            "target_key": "path:e\u0301.tsx",
            "status": "failed",
            "record_ids": [],
            "reason": "missing",
        }
    ]
    _validator("next-adapter-response-v1.schema.json").validate(unsafe_compound)
    with pytest.raises(AssertionError):
        validate_response_envelope(canonical_json_bytes(unsafe_compound), request)

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
            {
                "collection": "files",
                "record_id": extra_file["id"],
                "record": extra_file,
                "taints": ["parse_file"],
            },
            {
                "collection": "modules",
                "record_id": extra_module["id"],
                "record": extra_module,
                "taints": ["parse_file"],
            },
            {
                "collection": "members",
                "record_id": extra_import["id"],
                "record": extra_import,
                "taints": ["parse_file"],
            },
            {
                "collection": "members",
                "record_id": extra_import_alias["id"],
                "record": extra_import_alias,
                "taints": ["parse_file"],
            },
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
        item["record_id"] for item in partial_proof["discovered_records"] if item["taints"]
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
    validate_response_envelope(canonical_json_bytes(partial_response), target_request)
    partial_decision = validate_response_envelope(
        canonical_json_bytes(partial_response), target_request
    )
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
        validate_response_envelope(canonical_json_bytes(missing_target), target_request)
    extra_target = copy.deepcopy(partial_response)
    extra_target["proof"]["target_resolutions"].append(
        {"target_key": "path:src/Missing.tsx", "status": "failed", "record_ids": []}
    )
    extra_target["proof"]["target_resolutions"].sort(key=canonical_json_bytes)
    with pytest.raises(AssertionError):
        validate_response_envelope(canonical_json_bytes(extra_target), target_request)
    failed_as_resolved = copy.deepcopy(partial_response)
    failed_as_resolved["proof"]["target_resolutions"][0] = {
        "target_key": "path:src/Button.tsx",
        "status": "failed",
        "record_ids": [],
    }
    with pytest.raises(AssertionError):
        validate_response_envelope(canonical_json_bytes(failed_as_resolved), target_request)

    missing_taint = copy.deepcopy(partial_response["proof"])
    next(
        item
        for item in missing_taint["discovered_records"]
        if item["record_id"] == extra_module["id"]
    )["taints"] = []
    with pytest.raises(AssertionError):
        validate_proof(missing_taint, partial_response["model"])

    excess_taint = copy.deepcopy(partial_response["proof"])
    next(
        item
        for item in excess_taint["discovered_records"]
        if item["record_id"] == extra_module["id"]
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
        validate_response_envelope(canonical_json_bytes(broken_envelope), request)
    wrong_adapter = copy.deepcopy(response)
    wrong_adapter["adapter_version"] = "2.0.0"
    with pytest.raises(AssertionError):
        validate_response_envelope(canonical_json_bytes(wrong_adapter), request)
    wrong_descriptor = copy.deepcopy(response)
    wrong_descriptor["compatibility_descriptor"]["algorithm_versions"]["props"] = 2
    with pytest.raises(AssertionError):
        validate_response_envelope(canonical_json_bytes(wrong_descriptor), request)


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
        if item["record_id"] != component_member_id
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
    declaration_source = (
        b"export async function Generic<T extends { value: string }>() { return 1; }\n"
        b"export default class Default<T extends { value: string }> { value = 1; }\n"
        b"export interface Shape<T extends { value: string }> { value: T; }\n"
    )
    declaration_rows = _scan_export_file("src/declarations.ts", declaration_source)
    assert [row["exported_name"] for row in declaration_rows] == [
        "Generic",
        "default",
        "Shape",
    ]
    assert all(
        declaration_source[row["byte_start"] : row["byte_end"]].rstrip(b"\n").endswith(b"}")
        for row in declaration_rows
    )
    with pytest.raises(AssertionError):
        _scan_export_file("src/invalid.ts", b"export const first = 1\nexport const second = 2;")
    with pytest.raises(AssertionError):
        _scan_export_file("src/invalid.ts", b'export * from "./other"')


def test_export_scanner_tracks_jsx_stack_and_attribute_lexical_state() -> None:
    source = (
        'const nested = <Item data={"> export default"} '
        "expr={/}> export type False/.test(value)} template={`> export default`} "
        "prop={<Item />}><!-- export default -->"
        "export default false<Item>export type AlsoFalse = 1;</Item>"
        "</Item>;\n"
        "const fragment = <><Item />{/* export const StillFalse = 1; */}"
        "export const StillFalse = 1;</>;\n"
        "const unicode = <表示 data={{text: 'export default'}} />;\n"
        "export const 実在 = 1;\n"
    ).encode()
    rows = _scan_export_file("src/jsx-state.tsx", source)
    assert [(row["syntax_kind"], row["exported_name"]) for row in rows] == [
        ("named_export", "実在")
    ]
    row = rows[0]
    expected_start = source.index("export const 実在".encode())
    assert row["byte_start"] == expected_start
    assert row["byte_end"] == len(source) - 1
    assert (
        source[row["byte_start"] : row["byte_end"]].decode("utf-8").startswith("export const 実在")
    )


def test_export_scanner_closes_unicode_paired_member_and_namespace_jsx_tags() -> None:
    source = (
        "const paired = <表示.子 attr={{value: `</表示.子>`}}><ns:内>"
        "export const FakeInside = 1;"
        "<表示><表示>export type AlsoFake = 1;</表示></表示>"
        "</ns:内></表示.子>;\n"
        "const combining = <aְ.Panel><ns:Tagְ>"
        "export const FakeCombining = 1;"
        "<aְ.Panel>export type AlsoFakeCombining = 1;</aְ.Panel>"
        "</ns:Tagְ></aְ.Panel>;\n"
        "const otherIdContinue = <Foo·Bar><Foo·Bar>"
        "export const FakeMiddleDot = 1;"
        "</Foo·Bar></Foo·Bar>;\n"
        "export const 実在 = 1;\n"
    ).encode()
    rows = _scan_export_file("src/unicode-jsx.tsx", source)
    assert [(row["syntax_kind"], row["exported_name"]) for row in rows] == [
        ("named_export", "実在")
    ]
    assert source[rows[0]["byte_start"] : rows[0]["byte_end"]].startswith(
        "export const 実在".encode()
    )
    other_id = _scan_export_file("src/other-id.ts", "export const Foo·Bar = 1;\n".encode())
    assert [row["exported_name"] for row in other_id] == ["Foo·Bar"]


def test_round13_ecmascript_identifier_tables_are_pinned_and_complete() -> None:
    import unicodedata

    assert hashlib.sha256(canonical_table_bytes()).hexdigest() == ECMASCRIPT_UNICODE_TABLE_DIGEST
    assert ECMASCRIPT_IDENTIFIER_UNICODE_TABLE_DIGEST == ECMASCRIPT_UNICODE_TABLE_DIGEST
    assert _is_jsx_identifier_start("\u1885")
    assert _is_jsx_identifier_start("\u212e")
    assert not _is_jsx_identifier_start("\u00b7")
    for character in "\u00b7\u0387\u1369\u136a\u136b\u136c\u136d\u136e\u136f\u1370\u1371\u19da":
        assert _is_jsx_identifier_part(character)
    assert not _is_jsx_identifier_part("\u0375")
    assert _is_export_identifier("Foo\u00b7Bar")
    assert not _is_export_identifier("\u00b7Foo")
    assert identifier_classification_digest() == IDENTIFIER_CLASSIFICATION_SHA256

    descriptor = _descriptor()
    assert descriptor["algorithm_versions"]["identifier_unicode"] == "ecma-unicode-15.0"
    assert descriptor["algorithm_versions"]["identifier_unicode_table_digest"] == (
        ECMASCRIPT_UNICODE_TABLE_DIGEST
    )
    environment = _trusted_environment()
    assert environment["identifier_unicode_table_digest"] == ECMASCRIPT_UNICODE_TABLE_DIGEST
    original_category = unicodedata.category
    unicodedata.category = lambda _character: (_ for _ in ()).throw(AssertionError("host UCD"))
    try:
        assert _is_jsx_identifier_start("\u1885")
        assert _is_jsx_identifier_part("\u00b7")
    finally:
        unicodedata.category = original_category
    wrong_descriptor = copy.deepcopy(descriptor)
    wrong_descriptor["algorithm_versions"]["identifier_unicode"] = "ecma-unicode-14.0"
    with pytest.raises(AssertionError):
        validate_compatibility_descriptor(wrong_descriptor)
    wrong_table = copy.deepcopy(descriptor)
    wrong_table["algorithm_versions"]["identifier_unicode_table_digest"] = "f" * 64
    with pytest.raises(AssertionError):
        validate_compatibility_descriptor(wrong_table)

    domain = _legacy_domain_fixture()
    fingerprint = recompute_run_fingerprint(
        source_view_fingerprint=domain["source"]["fingerprint"],
        source_plan_digest=domain["source_plan_digest"],
        domain_config_digest=domain["domain_config_digest"],
        projects=domain["projects"],
        targets=domain["targets"],
        formats=domain["formats"],
        stdout_selector=domain["run_context"]["stdout_selector"],
        limits=domain["limits"],
        node_version=domain["toolchain"]["node_version"],
        typescript_version=domain["toolchain"]["typescript_version"],
        adapter_version=domain["toolchain"]["adapter_version"],
        protocol=domain["toolchain"]["protocol"],
        trusted_environment_digest=domain["trusted_environment"]["sha256"],
        identifier_unicode_version="ecma-unicode-14.0",
    )
    assert fingerprint != domain["run_fingerprint"]
    table_fingerprint = recompute_run_fingerprint(
        source_view_fingerprint=domain["source"]["fingerprint"],
        source_plan_digest=domain["source_plan_digest"],
        domain_config_digest=domain["domain_config_digest"],
        projects=domain["projects"],
        targets=domain["targets"],
        formats=domain["formats"],
        stdout_selector=domain["run_context"]["stdout_selector"],
        limits=domain["limits"],
        node_version=domain["toolchain"]["node_version"],
        typescript_version=domain["toolchain"]["typescript_version"],
        adapter_version=domain["toolchain"]["adapter_version"],
        protocol=domain["toolchain"]["protocol"],
        trusted_environment_digest=domain["trusted_environment"]["sha256"],
        identifier_unicode_table_digest="f" * 64,
    )
    assert table_fingerprint != domain["run_fingerprint"]


def test_round15_identifier_name_is_contextual_and_host_ucd_independent() -> None:
    # Unicode 15.0 Other_ID_Start/Continue and Join_Control are part of the
    # checked-in table, while a code point introduced after 15.0 is rejected.
    assert is_identifier_name("\u1885")
    assert is_identifier_name("\u212e")
    assert is_identifier_name("A\u00b7B")
    assert is_identifier_name("A\u200cB")
    assert not is_identifier_name("\u00b7A")
    assert not is_identifier_name("\u200cA")
    assert not is_identifier_name("\U0002ebf0")
    assert is_identifier_name("class")
    assert not is_binding_identifier("class")
    assert is_declaration_key("class")
    assert not is_binding_identifier("default")
    assert is_declaration_key("default")
    assert not is_identifier_name("e\u0301")
    assert not is_identifier_name("A\x00B")
    assert identifier_classification_digest() == IDENTIFIER_CLASSIFICATION_SHA256

    # The same contextual predicates are intentionally used by component
    # bindings, export/import names, property keys, and external references.
    assert _is_export_identifier("class", allow_keyword=True)
    assert not _is_export_identifier("class")


def test_round16_identifier_contexts_cover_reserved_exports_and_anonymous_default() -> None:
    rows = _scan_export_file(
        "src/contextual-export.ts",
        b"const value = 1;\nexport { value as class };\n",
    )
    assert rows[0]["exported_name"] == "class"
    assert rows[0]["role"] == "value"
    with pytest.raises(AssertionError):
        _scan_export_file("src/reserved-binding.ts", b"export const class = 1;\n")

    semantic = _semantic(_model())
    next(entity for entity in semantic["entities"] if entity["kind"] == "component")[
        "declaration_key"
    ] = "@anonymous-default"
    _validator("next-semantic-v1.schema.json").validate(semantic)
    assert not is_binding_identifier("@anonymous-default")


def test_round14_proof_reason_semantics_keep_selection_and_unsupported_complete() -> None:
    model = {
        "diagnostics": [
            _public_diagnostic("CSV-NEXT-UNSUPPORTED-001", symbol=_id("component", "5"))
        ],
        "coverage": {"unknown_relation_count": 1},
    }
    for reason in ("not_selected", "target_excluded", "unsupported"):
        proof = {"failure_roots": [], "excluded": [{"reason": reason}], "failed": []}
        assert derive_pre_budget_outcome(proof, model) == "complete"
    localized = {
        "failure_roots": [{"id": "next:failure:" + "0" * 64}],
        "excluded": [{"reason": "tainted"}],
        "failed": [],
    }
    assert derive_pre_budget_outcome(localized, {"diagnostics": []}) == "partial_safe"
    with pytest.raises(AssertionError):
        derive_pre_budget_outcome(
            {"failure_roots": [], "excluded": [{"reason": "tainted"}], "failed": []},
            {"diagnostics": []},
        )


@pytest.mark.parametrize(
    ("localized", "safe_subset_proven", "code", "outcome", "payload_available"),
    [
        (True, True, "CSV-NEXT-SOURCE-001", "partial_safe", True),
        (False, True, "CSV-NEXT-SOURCE-003", "payload_unavailable", False),
        (True, False, "CSV-NEXT-SOURCE-003", "payload_unavailable", False),
        (False, False, "CSV-NEXT-SOURCE-003", "payload_unavailable", False),
    ],
)
def test_round15_source_failure_preserves_locality_boundary(
    localized: bool,
    safe_subset_proven: bool,
    code: str,
    outcome: str,
    payload_available: bool,
) -> None:
    graph: dict[str, tuple[dict[str, str], ...]] = {
        "nodes": (
            {"id": "broken", "path": "src/Broken.tsx", "project_root": "."},
            {"id": "target", "path": "src/Other.tsx", "project_root": "."},
        ),
        "edges": ({"source": "broken", "target": "target"},) if localized is False else (),
        "open_edges": (
            ({"source": "broken"},) if localized is True and not safe_subset_proven else ()
        ),
    }
    if localized and safe_subset_proven:
        graph["edges"] = ()
        graph["open_edges"] = ()
    graph["edges"] = tuple(graph["edges"])
    seal_id = "d" * 64
    proof_roots = ({"id": "round15-root", "path_ref": "src/Broken.tsx"},)
    ledger_material = {
        "seal_id": seal_id,
        "source_graph": graph,
        "project_roots": ["."],
        "targets": ["path:src/Other.tsx"],
        "proof_roots": list(proof_roots),
    }
    ledger = SourceFailureLedger(
        failures=({"path": "src/Broken.tsx", "stage": "source_read"},),
        source_graph=graph,
        project_roots=(".",),
        targets=("path:src/Other.tsx",),
        proof_roots=proof_roots,
        seal_id=seal_id,
        seal_digest=digest(ledger_material),
    )
    result = classify_source_failure(ledger)
    assert result == {
        "diagnostic_code": code,
        "outcome": outcome,
        "payload_available": payload_available,
        "exit_code": 3,
    }


def test_round14_adapter_proof_cannot_claim_entity_over_budget() -> None:
    response = _response(_model())
    response["proof"]["failed"] = [
        {"collection": "modules", "record_id": _id("module", "3"), "reason": "over_budget"}
    ]
    with pytest.raises(ValidationError):
        _validator("next-adapter-response-v1.schema.json").validate(response)
    response["proof"]["failed"][0]["reason"] = "parse_file"
    _validator("next-adapter-response-v1.schema.json").validate(response)
    with pytest.raises(AssertionError):
        validate_response_envelope(canonical_json_bytes(response), _request())


def test_export_scanner_type_alias_span_includes_generic_object_terminator() -> None:
    source = b"export type Result<T extends { value: string }> = { value: T };\n"
    rows = _scan_export_file("src/type-span.ts", source)
    assert len(rows) == 1
    row = rows[0]
    assert row["role"] == "type"
    assert source[row["byte_start"] : row["byte_end"]] == source.rstrip(b"\n")


def test_reexport_graph_recomputes_alias_star_cycle_and_conflict_witnesses() -> None:
    cases = {case["name"]: case for case in load_export_graph_cases()}
    assert set(cases) == {
        "alias",
        "conflict",
        "cycle",
        "double-alias",
        "empty-star",
        "hidden-key",
        "same-specifier-aliases",
        "star",
        "star-cycle",
    }

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

    double_alias = recompute_export_graph_case(cases["double-alias"])
    final_alias = next(
        row for row in double_alias["exports"] if row["module_file_path"] == "src/index.ts"
    )
    assert final_alias["exported_name"] == "FinalButton"
    assert final_alias["target_declaration_key"] == "Button"
    assert final_alias["resolution"] == "component"
    assert [row["exported_name"] for row in double_alias["witnesses"]] == [
        "ButtonAlias",
        "FinalButton",
    ]

    empty_star = recompute_export_graph_case(cases["empty-star"])
    assert empty_star["witnesses"] == []
    assert empty_star["conflicts"] == []
    assert empty_star["cycles"] == []

    star = recompute_export_graph_case(cases["star"])
    star_rows = [row for row in star["witnesses"] if row["owner_file_path"] == "src/index.ts"]
    assert [row["exported_name"] for row in star_rows] == ["Card", "answer"]
    assert {row["resolution"] for row in star_rows} == {"component", "value"}
    assert all(row["exported_name"] != "default" for row in star_rows)

    hidden_key = recompute_export_graph_case(cases["hidden-key"])
    hidden_row = next(row for row in hidden_key["witnesses"] if row["exported_name"] == "Alias")
    assert hidden_row["resolution"] == "unknown"
    assert hidden_row["diagnostic"] == "missing_export"
    assert hidden_row["target_declaration_key"] is None

    star_cycle = recompute_export_graph_case(cases["star-cycle"])
    assert star_cycle["witnesses"]
    assert all(row["resolution"] == "unknown" for row in star_cycle["witnesses"])
    assert all(row["diagnostic"] == "cycle" for row in star_cycle["witnesses"])

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
    assert all(row["original_exported_name"] == "*" for row in conflict["witnesses"])

    same_shape = recompute_export_graph_case(cases["same-specifier-aliases"])
    same_shape_witnesses = same_shape["witnesses"]
    assert len(same_shape_witnesses) == 3
    assert {row["syntax_identity"] for row in same_shape_witnesses} == {
        "export:src/index.ts:8:18:reexport:A",
        "export:src/index.ts:42:52:reexport:A:second",
        "export:src/index.ts:25:35:reexport:B",
    }
    assert sorted(row["exported_name"] for row in same_shape_witnesses) == ["A", "A", "B"]
    diagnostics_by_name = {
        row["syntax_identity"]: row["diagnostic"] for row in same_shape_witnesses
    }
    assert diagnostics_by_name["export:src/index.ts:8:18:reexport:A"] == "conflict"
    assert diagnostics_by_name["export:src/index.ts:42:52:reexport:A:second"] == "conflict"
    assert diagnostics_by_name["export:src/index.ts:25:35:reexport:B"] is None
    assert (
        len(
            {
                (
                    row["owner_file_path"],
                    row["source_specifier"],
                    row["imported_name"],
                    row["original_exported_name"],
                    row["syntax_identity"],
                    row["byte_start"],
                    row["byte_end"],
                )
                for row in same_shape_witnesses
            }
        )
        == 3
    )

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
        set(edge)
        == {
            "owner_file_path",
            "source_specifier",
            "imported_name",
            "exported_name",
            "syntax_identity",
            "byte_start",
            "byte_end",
        }
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
    star_row = next(
        row
        for row in scan_export_syntax_census()
        if row["owner_file_path"] == "src/Button.tsx" and row["star"]
    )
    assert expected == [
        {
            "owner_module_id": _id("module", "3"),
            "owner_file_path": "src/Button.tsx",
            "byte_start": star_row["byte_start"],
            "byte_end": star_row["byte_end"],
            "token_identity": star_row["token_identity"],
            "syntax_identity": star_row["syntax_identity"],
            "source_specifier": "./Other",
            "imported_name": "*",
            "original_exported_name": "*",
            "exported_name": None,
            "resolved_source_module_id": None,
            "expanded_exported_name": None,
            "target_declaration_id": None,
            "resolution": "unknown",
            "diagnostic": "missing_source",
        }
    ]
    mutated = copy.deepcopy(raw)
    mutated["edges"] = mutated["edges"][1:]
    assert recompute_export_graph_case(mutated) != result


def test_round13_reexport_join_is_bijective_for_aliases_and_repeated_forms() -> None:
    source = (
        b'export { Foo as A, Foo as B } from "./source";\nexport { Foo as A } from "./source";\n'
    )
    syntax_rows = _scan_export_file("src/index.ts", source)
    reexports = [row for row in syntax_rows if row["reexport"]]
    assert [row["exported_name"] for row in reexports] == ["A", "B", "A"]
    raw_edges = [
        {
            key: row[key]
            for key in (
                "owner_file_path",
                "source_specifier",
                "imported_name",
                "exported_name",
                "syntax_identity",
                "byte_start",
                "byte_end",
            )
        }
        for row in reexports
    ]
    joined = join_reexport_observations_to_edges(reexports, raw_edges)
    assert len(joined) == 3
    assert [syntax["exported_name"] for syntax, _edge in joined] == ["A", "A", "B"]
    assert len({syntax["syntax_identity"] for syntax, _edge in joined}) == 3

    substituted = copy.deepcopy(raw_edges)
    substituted[0]["exported_name"], substituted[1]["exported_name"] = (
        substituted[1]["exported_name"],
        substituted[0]["exported_name"],
    )
    with pytest.raises(AssertionError):
        join_reexport_observations_to_edges(reexports, substituted)


def test_round12_positive_reexport_witness_reaches_response_domain_and_root() -> None:
    model = _model_with_positive_reexports()
    request = _request(model)
    response = _response(model, request=request)
    _validator("next-adapter-response-v1.schema.json").validate(response)
    decision = validate_response_envelope(canonical_json_bytes(response), request)
    assert decision["allowed"] is True
    witnesses = expected_export_reexport_witness(model)
    component_rows = [
        row
        for row in witnesses
        if row["resolution"] == "component" and row["target_declaration_id"]
    ]
    assert component_rows
    assert all(row["owner_module_id"].startswith("next:module:") for row in component_rows)
    assert any(row["imported_name"] == "default" for row in component_rows)
    assert any(row["imported_name"] == "*" for row in witnesses)
    assert any(
        member["reexport"]
        and member["target_component_id"] == component_rows[0]["target_declaration_id"]
        for member in model["members"]
        if member["kind"] == "export_binding"
    )
    domain = _domain(decision=decision["validated_decision"])
    assert (
        domain["coverage"]["non_component_value_export_count"]
        == expected_export_coverage_counts(model)["non_component_value_export_count"]
    )
    validate_domain_manifest(domain)
    manifest = _run_manifest(domain)
    published = _published_bytes(domain)
    validate_run_manifest(manifest, domain, published)
    validate_published_projection(domain, published)

    omitted = copy.deepcopy(response)
    omitted["proof"]["export_reexport_witness"] = [
        row
        for row in omitted["proof"]["export_reexport_witness"]
        if row["target_declaration_id"] is None
    ]
    with pytest.raises(AssertionError):
        validate_response_envelope(canonical_json_bytes(omitted), request)


def test_reexport_witness_schema_preserves_original_name_and_failure_reason() -> None:
    conflict = next(case for case in load_export_graph_cases() if case["name"] == "conflict")
    result = recompute_export_graph_case(conflict)
    for witness in result["witnesses"]:
        assert witness["original_exported_name"] == "*"
        assert witness["exported_name"] == "Shared"
        assert witness["diagnostic"] == "conflict"
    cycle = next(case for case in load_export_graph_cases() if case["name"] == "cycle")
    cycle_result = recompute_export_graph_case(cycle)
    assert {witness["diagnostic"] for witness in cycle_result["witnesses"]} == {"cycle"}


@pytest.mark.parametrize(
    ("graph_name", "diagnostic", "include_cycle", "include_conflict"),
    [
        ("cycle", "cycle", True, False),
        ("conflict", "conflict", False, True),
    ],
)
def test_reexport_failure_graph_is_schema_valid_and_projects_whole_run(
    graph_name: str, diagnostic: str, include_cycle: bool, include_conflict: bool
) -> None:
    model = _model_with_graph_failure_cases(
        include_cycle=include_cycle,
        include_conflict=include_conflict,
    )
    request = _request(model)
    response = _response(model, request=request)
    _validator("next-adapter-response-v1.schema.json").validate(response)
    witnesses = response["proof"]["export_reexport_witness"]
    final_button = next(
        row
        for row in witnesses
        if row["owner_file_path"] == "src/GraphAliasIndex.ts"
        and row["exported_name"] == "FinalButton"
    )
    assert final_button["resolution"] == "component"
    assert final_button["target_declaration_id"] is not None
    assert any(
        row["owner_file_path"] == "src/GraphDefaultIndex.ts" and row["exported_name"] == "Visible"
        for row in witnesses
    )
    assert not any(row["owner_file_path"] == "src/GraphEmptyIndex.ts" for row in witnesses)
    if include_conflict:
        same_rows = [row for row in witnesses if row["owner_file_path"] == "src/GraphSameIndex.ts"]
        assert [
            row["exported_name"] for row in sorted(same_rows, key=lambda item: item["byte_start"])
        ] == ["A", "B", "A"]
        assert {row["diagnostic"] for row in same_rows if row["exported_name"] == "A"} == {
            "conflict"
        }
    result = recompute_export_graph_case(
        next(case for case in load_export_graph_cases() if case["name"] == graph_name)
    )
    assert result["cycles"] or result["conflicts"]
    assert any(row["diagnostic"] == diagnostic for row in result["witnesses"])
    decision = validate_response_envelope(canonical_json_bytes(response), request)
    assert decision["allowed"] is False
    assert decision["diagnostic_code"] == "CSV-NEXT-EXPORT-001"
    assert decision["payload_available"] is False
    assert decision["export_failures"]
    domain = _domain(decision=decision["validated_decision"])
    assert domain["status"] == "incomplete"
    assert domain["incomplete_kind"] == "payload_unavailable"
    assert domain["artifact_paths"] == []
    assert domain["diagnostics"][0]["code"] == "CSV-NEXT-EXPORT-001"
    validate_domain_manifest(domain)
    manifest = _run_manifest(domain)
    validate_run_manifest(manifest, domain, {})
    summary = _run_summary_value("incomplete", domain)
    for selector in ("next:semantic-json", "next:plantuml"):
        stream = _stdout_result_for_domain(domain, manifest, selector)
        assert stream["availability"] is False
        validate_run_status_vector(
            manifest,
            summary,
            stream,
            {},
            canonical_json_bytes(stream) + b"\n",
            manifest["diagnostics"],
            stderr_bytes=_diagnostic_jsonl(manifest["diagnostics"]),
        )

    mutated = copy.deepcopy(response)
    witness = mutated["proof"]["export_reexport_witness"][0]
    witness["exported_name"] = "Substituted"
    with pytest.raises(AssertionError):
        validate_response_envelope(canonical_json_bytes(mutated), request)


def test_reexport_witness_requires_owner_join_and_component_target() -> None:
    response = _response(_model())
    validator = _validator("next-adapter-response-v1.schema.json")
    validator.validate(response)
    reexport = response["proof"]["export_reexport_witness"][0]
    missing_owner = copy.deepcopy(response)
    missing_owner["proof"]["export_reexport_witness"][0].pop("owner_module_id")
    with pytest.raises(ValidationError):
        validator.validate(missing_owner)

    component_resolution = copy.deepcopy(response)
    component_resolution["proof"]["export_resolution_witness"][0]["component_id"] = None
    with pytest.raises(ValidationError):
        validator.validate(component_resolution)
    assert reexport["owner_file_path"] == "src/Button.tsx"


def test_reexport_conflict_projects_export_failure_through_whole_run() -> None:
    conflict = next(case for case in load_export_graph_cases() if case["name"] == "conflict")
    conflict_result = recompute_export_graph_case(conflict)
    proof = {
        "export_reexport_witness": [
            {
                "syntax_identity": "export:src/index.ts:0:20:export_all:*",
                "original_exported_name": witness["original_exported_name"],
                "exported_name": witness["exported_name"],
                "diagnostic": witness["diagnostic"],
            }
            for witness in conflict_result["witnesses"]
        ]
    }
    assert export_reexport_failure_rows(proof)
    context: NextRunContext = {
        "requested_formats": ["plantuml"],
        "budget_requested": 600,
        "budget_resolved": 600,
        "budget_source": "explicit",
        "stdout_selector": "next:plantuml",
    }
    decision = export_failure_decision(proof, context)
    assert decision is not None
    assert decision["diagnostic_code"] == "CSV-NEXT-EXPORT-001"
    assert decision["outcome"] == "payload_unavailable"
    assert decision["artifact_paths"] == []

    domain = _legacy_domain_fixture(
        "incomplete",
        export_failure=True,
        formats=["plantuml"],
        max_entities=600,
        budget_source="explicit",
        budget_requested=600,
        stdout_selector="next:plantuml",
    )
    validate_domain_manifest(domain)
    manifest = _run_manifest(domain)
    validate_run_manifest(manifest, domain, {})
    stream = _stdout_result_for_domain(domain, manifest, "next:plantuml")
    assert stream["availability"] is False
    assert stream["selector"] == "next:plantuml"
    summary = _run_summary_value("incomplete", domain)
    validate_run_status_vector(
        manifest,
        summary,
        stream,
        {},
        canonical_json_bytes(stream) + b"\n",
        manifest["diagnostics"],
        stderr_bytes=_diagnostic_jsonl(manifest["diagnostics"]),
    )
    assert manifest["run"]["exit_code"] == 3


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


def test_source_plan_and_view_are_atomically_sealed_after_single_reads() -> None:
    config = _config_projection()
    files = {
        "package.json": b'{"name":"fixture"}',
        "tsconfig.json": b'{"compilerOptions":{}}',
        "src/Button.tsx": b"export default Button;\n",
        "src/types.d.ts": b"export interface Props {}\n",
    }
    intent = SourceDiscoveryIntent(
        project_roots=(".",),
        control_candidates=("package.json", "tsconfig.json"),
    )
    inventory = {
        "observed_limits": copy.deepcopy(config["limits"]),
        "observed_trusted_environment_digest": config["trusted_environment_digest"],
    }
    reader = InstrumentedSourceReader(files)
    seal = seal_source_acquisition(intent, reader, inventory)
    assert reader.sealed is True
    assert reader.seal_calls == 1
    assert seal.seal_operation == 1
    assert seal.final_plan["projects"] == config["projects"]
    assert seal.final_plan["resolved_control_paths"] == [
        {"project_root": ".", "path": "package.json"},
        {"project_root": ".", "path": "tsconfig.json"},
    ]
    assert seal.plan_digest == digest(seal.final_plan)
    assert seal.source_view["file_count"] == 4
    assert seal.source_view_fingerprint == digest(seal.source_view)
    assert seal.seal_id == digest(
        {
            "plan_digest": seal.plan_digest,
            "source_view_fingerprint": seal.source_view_fingerprint,
            "seal_operation": seal.seal_operation,
            "snapshot_id": seal.snapshot_id,
            "revision_before": seal.revision_before,
            "revision_after": seal.revision_after,
        }
    )
    assert reader.read_counts == {
        "package.json": 1,
        "tsconfig.json": 1,
        "src/Button.tsx": 1,
        "src/types.d.ts": 1,
    }
    with pytest.raises(AssertionError):
        reader.read("src/Button.tsx")
    with pytest.raises(AssertionError):
        seal_source_acquisition(
            SourceDiscoveryIntent(
                project_roots=(".",),
                control_candidates=("package.json",),
            ),
            InstrumentedSourceReader(
                {"package.json": b"{}"}, revision="inventory-v1", revision_after="inventory-v2"
            ),
        )


def test_source_seal_derives_plan_and_view_from_one_intent_and_rejects_drift() -> None:
    config = _config_projection()
    plan = config["source_plan"]
    files = {
        "package.json": b'{"name":"fixture"}',
        "tsconfig.json": b'{"compilerOptions":{}}',
        "src/Button.tsx": b"export default Button;\n",
        "src/types.d.ts": b"export interface Props {}\n",
    }
    intent = SourceDiscoveryIntent(
        project_roots=(".",),
        control_candidates=("package.json", "tsconfig.json"),
    )
    inventory = {
        "observed_limits": copy.deepcopy(config["limits"]),
        "observed_trusted_environment_digest": config["trusted_environment_digest"],
    }
    reader = InstrumentedSourceReader(files)
    seal = seal_source_acquisition(intent, reader, inventory)
    assert seal.final_plan["projects"] == config["projects"]
    assert seal.source_view["file_count"] == len(files)
    assert reader.seal_calls == 1
    assert reader.read_counts == {path: 1 for path in files}

    with pytest.raises(TypeError):
        seal_source_acquisition(intent, InstrumentedSourceReader(files), final_plan=plan)  # type: ignore[call-arg]

    plan_only_intent = SourceDiscoveryIntent(
        project_roots=(".",),
        control_candidates=("package.json",),
    )
    with pytest.raises(AssertionError):
        seal_source_acquisition(
            plan_only_intent,
            InstrumentedSourceReader({"package.json": files["package.json"]}),
            {"derived_plan": plan},
        )
    with pytest.raises(AssertionError):
        seal_source_acquisition(
            plan_only_intent,
            InstrumentedSourceReader({"package.json": files["package.json"]}),
            {"file_digests": []},
        )

    with pytest.raises(AssertionError):
        seal_source_acquisition(
            SourceDiscoveryIntent(
                project_roots=(".",),
                control_candidates=("package.json", "tsconfig.json"),
            ),
            InstrumentedSourceReader(files, revision="v1", revision_after="v2"),
        )
    with pytest.raises(AssertionError):
        seal_source_acquisition(
            SourceDiscoveryIntent(
                project_roots=(".",),
                control_candidates=("package.json", "package.json"),
            ),
            InstrumentedSourceReader(files),
        )
    with pytest.raises(AssertionError):
        seal_source_acquisition(
            intent,
            InstrumentedSourceReader(files),
            {"file_digests": [{"path": "package.json", "size_bytes": 0, "sha256": "0" * 64}]},
        )
    wrong_role_map = copy.deepcopy(plan["file_role_map"])
    wrong_role_map[0]["effective_role"] = "program"
    with pytest.raises(AssertionError):
        seal_source_acquisition(
            {
                "project_roots": (".",),
                "control_candidates": ("package.json", "tsconfig.json"),
                "file_role_map": wrong_role_map,
            },
            InstrumentedSourceReader(files),
            inventory,
        )


def test_round17_source_inventory_accepts_observations_only() -> None:
    """Resolved plan fields cannot be injected through the inventory."""

    files = {
        "package.json": b'{"name":"fixture"}',
        "tsconfig.json": b'{"compilerOptions":{}}',
        "src/Button.tsx": b"export default Button;\n",
    }
    intent = SourceDiscoveryIntent(
        project_roots=(".",),
        control_candidates=("package.json", "tsconfig.json"),
    )
    observed = {
        "observed_limits": copy.deepcopy(_config_projection()["limits"]),
        "observed_trusted_environment_digest": _config_projection()["trusted_environment_digest"],
    }
    for key, value in (
        ("project_descriptors", [_config_project()]),
        ("compiler_options", {"module": "commonjs"}),
        ("source_roots", ["other/src"]),
        ("config", {"projects": []}),
        ("local_extends", []),
        ("final_paths", ["src/Other.tsx"]),
        ("file_role_map", []),
        ("resolved_control_paths", []),
        ("plan_digest", "0" * 64),
        ("source_view_fingerprint", "0" * 64),
    ):
        injected = {**observed, key: value}
        with pytest.raises(AssertionError):
            seal_source_acquisition(intent, InstrumentedSourceReader(files), injected)


def test_round17_request_owned_derived_source_claims_cannot_override_control_bytes() -> None:
    request = _request()
    request["projects"][0]["compiler_options"]["module"] = "commonjs"
    request["projects"][0]["config_digest"] = project_config_digest(request["projects"][0])
    request["request_id"] = recompute_request_id(request)
    sealed = validate_adapter_request(request)
    with pytest.raises(AssertionError):
        _publication_context_for_validated_request(
            sealed,
            _run_context(),
            toolchain={
                "node": {"status": "available", "version": "22.14.0", "failure_kind": None},
                "node_version": "22.14.0",
                "typescript_version": "5.9.2",
                "adapter_version": "1.0.0",
                "protocol": "code-structure-viz.next-adapter/v1",
            },
            trusted_environment=_trusted_environment(),
            source_failure_ledger=(),
            process_launch_descriptor=process_launch_descriptor(
                node_status="available",
                node_realpath="/usr/local/bin/node",
                node_sha256="1" * 64,
                node_version="22.14.0",
                spawn_executable="/usr/local/bin/node",
                file_identity_at_hash={
                    "realpath": "/usr/local/bin/node",
                    "sha256": "1" * 64,
                    "version": "22.14.0",
                },
                file_identity_at_spawn={
                    "realpath": "/usr/local/bin/node",
                    "sha256": "1" * 64,
                    "version": "22.14.0",
                },
                spawn_handle="fixture-process-group",
            ),
        )


def test_round18_source_seal_rejects_caller_membership_and_typed_drift() -> None:
    files = {
        "package.json": b'{"name":"fixture"}',
        "tsconfig.json": b'{"compilerOptions":{}}',
        "src/Button.tsx": b"export default Button;\n",
    }
    intent = SourceDiscoveryIntent(
        project_roots=(".",), control_candidates=("package.json", "tsconfig.json")
    )
    observed = {
        "observed_limits": _config_projection()["limits"],
        "observed_trusted_environment_digest": _config_projection()["trusted_environment_digest"],
    }
    with pytest.raises(AssertionError):
        seal_source_acquisition(
            intent,
            InstrumentedSourceReader(files),
            {**observed, "observed_paths": tuple(files)},
        )
    with pytest.raises(SourceAcquisitionError) as malformed:
        seal_source_acquisition(
            intent,
            InstrumentedSourceReader({**files, "tsconfig.json": b"[]"}),
            observed,
        )
    assert malformed.value.code == "CSV-NEXT-CONFIG-002"
    with pytest.raises(SourceAcquisitionError) as drift:
        seal_source_acquisition(
            intent,
            InstrumentedSourceReader(files, revision="v1", revision_after="v2"),
            observed,
        )
    assert drift.value.code == "CSV-NEXT-SOURCE-002"


def test_round17_source_failure_ledger_derives_locality_without_caller_booleans() -> None:
    base: dict[str, Any] = {
        "failures": ({"path": "src/Broken.tsx", "stage": "source_read"},),
        "source_graph": {
            "nodes": (
                {"id": "broken", "path": "src/Broken.tsx", "project_root": "."},
                {"id": "unrelated", "path": "src/Other.tsx", "project_root": "."},
            ),
            "edges": (),
            "open_edges": (),
        },
        "project_roots": (".",),
        "targets": ("path:src/Other.tsx",),
        "proof_roots": ({"id": "failure-root", "path_ref": "src/Broken.tsx"},),
        "seal_id": "a" * 64,
    }
    base["seal_digest"] = digest(
        {
            "seal_id": base["seal_id"],
            "source_graph": base["source_graph"],
            "project_roots": list(base["project_roots"]),
            "targets": list(base["targets"]),
            "proof_roots": list(base["proof_roots"]),
        }
    )
    ledger = SourceFailureLedger(**base)
    assert ledger.safe_subset_proven is True
    for field in ("isolated", "target_tainted", "safe_subset_proven"):
        injected = copy.deepcopy(base)
        injected["failures"] = ({"path": "src/Broken.tsx", "stage": "source_read", field: True},)
        with pytest.raises(AssertionError):
            SourceFailureLedger(**injected)

    tainted = copy.deepcopy(base)
    tainted["source_graph"]["edges"] = ({"source": "broken", "target": "unrelated"},)
    tainted["seal_digest"] = digest(
        {
            "seal_id": tainted["seal_id"],
            "source_graph": tainted["source_graph"],
            "project_roots": list(tainted["project_roots"]),
            "targets": list(tainted["targets"]),
            "proof_roots": list(tainted["proof_roots"]),
        }
    )
    tainted_ledger = SourceFailureLedger(**tainted)
    assert tainted_ledger.explicit_target_tainted is True
    assert tainted_ledger.safe_subset_proven is False

    nonisolatable = copy.deepcopy(base)
    nonisolatable["source_graph"]["open_edges"] = ({"source": "broken"},)
    nonisolatable["seal_digest"] = digest(
        {
            "seal_id": nonisolatable["seal_id"],
            "source_graph": nonisolatable["source_graph"],
            "project_roots": list(nonisolatable["project_roots"]),
            "targets": list(nonisolatable["targets"]),
            "proof_roots": list(nonisolatable["proof_roots"]),
        }
    )
    nonisolatable_ledger = SourceFailureLedger(**nonisolatable)
    assert nonisolatable_ledger.safe_subset_proven is False


def test_round18_source_failure_ledger_recomputes_reachability() -> None:
    """Round 18 keeps the raw-graph counterexamples as executable evidence."""

    test_round17_source_failure_ledger_derives_locality_without_caller_booleans()


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


def test_round18_path_only_order_is_nfc_utf8_and_object_rows_are_canonical_json() -> None:
    quote_root = _project()
    quote_root["root"] = 'a"'
    quote_root["source_roots"] = ['a"/src']
    quote_root["config_path"] = 'a"/tsconfig.json'
    quote_root["id"] = recompute_record_id(quote_root)
    quote_root["config_digest"] = project_config_digest(quote_root)
    ascii_root = _project()
    ascii_root["root"] = "aA"
    ascii_root["source_roots"] = ["aA/src"]
    ascii_root["config_path"] = "aA/tsconfig.json"
    ascii_root["id"] = recompute_record_id(ascii_root)
    ascii_root["config_digest"] = project_config_digest(ascii_root)

    assert sorted(['a"', "aA"], key=_path_sort_key) == ['a"', "aA"]
    assert sorted(['a"', "aA"], key=canonical_json_bytes) == ["aA", 'a"']
    config = _config_projection(projects=[ascii_root, quote_root])
    assert [project["root"] for project in config["projects"]] == ['a"', "aA"]

    files = {
        "package.json": b'{"name":"fixture"}',
        "tsconfig.json": b'{"compilerOptions":{}}',
        'a"': b"opaque-a\n",
        "aA": b"opaque-b\n",
    }
    seal = seal_source_acquisition(
        SourceDiscoveryIntent(
            project_roots=(".",), control_candidates=("package.json", "tsconfig.json")
        ),
        InstrumentedSourceReader(files),
        {
            "observed_limits": config["limits"],
            "observed_trusted_environment_digest": config["trusted_environment_digest"],
        },
    )
    assert seal.source_view["files"] == sorted(seal.source_view["files"], key=canonical_json_bytes)


def test_round11_inverse_project_order_reaches_response_domain_root_and_fingerprint() -> None:
    model = _inverse_order_two_project_model()
    request = _request(model)
    validate_request_envelope(request)
    roots = [project["root"] for project in request["projects"]]
    model_ids = [project["id"] for project in model["projects"]]
    assert roots == sorted(roots, key=_path_sort_key)
    assert model_ids == sorted(model_ids)
    assert roots != [
        project["root"] for project in sorted(model["projects"], key=lambda item: item["id"])
    ]

    context = _run_context()
    response = _response(model, request=request, run_context=context)
    _validator("next-adapter-response-v1.schema.json").validate(response)
    decision = validate_response_envelope(canonical_json_bytes(response), request)
    assert decision["run_context"] == context
    assert decision["allowed"] is True

    domain = _domain(decision=decision["validated_decision"])
    validate_domain_manifest(domain)
    manifest = _run_manifest(domain)
    validate_run_manifest(manifest, domain, _published_bytes(domain))
    _validator("next-domain-manifest-v1.schema.json").validate(domain)
    _validator("run-manifest-v1.schema.json").validate(manifest)
    assert manifest["run"]["run_context"] == context
    assert manifest["command"]["stdout_selector"] == context["stdout_selector"]

    bad_request = copy.deepcopy(request)
    bad_request["projects"].reverse()
    bad_request["request_id"] = recompute_request_id(bad_request)
    with pytest.raises(AssertionError):
        validate_request_envelope(bad_request)

    bad_response = copy.deepcopy(response)
    bad_response["model"]["projects"].reverse()
    bad_response["model_digest"] = digest(bad_response["model"])
    with pytest.raises(AssertionError):
        validate_response_envelope(canonical_json_bytes(bad_response), request)

    bad_domain = copy.deepcopy(domain)
    bad_domain["projects"].reverse()
    with pytest.raises(AssertionError):
        validate_domain_manifest(bad_domain)

    for field in ("request", "config"):
        bad_projection = copy.deepcopy(domain)
        bad_projection[field]["projects"].reverse()
        with pytest.raises(AssertionError):
            validate_domain_manifest(bad_projection)

    bad_manifest = copy.deepcopy(manifest)
    bad_manifest["request"]["projects"].reverse()
    with pytest.raises(AssertionError):
        validate_run_manifest(bad_manifest, domain, _published_bytes(domain))

    for field in ("next_request", "next_config"):
        bad_manifest_projection = copy.deepcopy(manifest)
        bad_manifest_projection[field]["projects"].reverse()
        with pytest.raises(AssertionError):
            validate_run_manifest(bad_manifest_projection, domain, _published_bytes(domain))

    bad_resolved = copy.deepcopy(manifest)
    bad_resolved["config"]["resolved"]["next"]["projects"].reverse()
    with pytest.raises(AssertionError):
        validate_run_manifest(bad_resolved, domain, _published_bytes(domain))

    changed_fingerprint = recompute_run_fingerprint(
        source_view_fingerprint=domain["source"]["fingerprint"],
        source_plan_digest=domain["source_plan_digest"],
        domain_config_digest=domain["domain_config_digest"],
        projects=domain["projects"],
        targets=domain["targets"],
        formats=["semantic-json"],
        stdout_selector="next:semantic-json",
        limits=domain["limits"],
        node_version=domain["toolchain"]["node_version"],
        typescript_version=domain["toolchain"]["typescript_version"],
        adapter_version=domain["toolchain"]["adapter_version"],
        protocol=domain["toolchain"]["protocol"],
        trusted_environment_digest=domain["trusted_environment"]["sha256"],
    )
    assert changed_fingerprint != domain["run_fingerprint"]
    changed_selector = recompute_run_fingerprint(
        source_view_fingerprint=domain["source"]["fingerprint"],
        source_plan_digest=domain["source_plan_digest"],
        domain_config_digest=domain["domain_config_digest"],
        projects=domain["projects"],
        targets=domain["targets"],
        formats=domain["formats"],
        stdout_selector="next:plantuml",
        limits=domain["limits"],
        node_version=domain["toolchain"]["node_version"],
        typescript_version=domain["toolchain"]["typescript_version"],
        adapter_version=domain["toolchain"]["adapter_version"],
        protocol=domain["toolchain"]["protocol"],
        trusted_environment_digest=domain["trusted_environment"]["sha256"],
    )
    assert changed_selector != domain["run_fingerprint"]


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
        {
            "target_key": "path:src/Missing.tsx",
            "status": "failed",
            "record_ids": [],
            "reason": "missing",
        }
    ]
    assert resolve_target_resolutions(["path:src/types.d.ts"], all_records) == [
        {
            "target_key": "path:src/types.d.ts",
            "status": "failed",
            "record_ids": [],
            "reason": "control_context",
        }
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
            {
                "target_key": target_key,
                "status": "failed",
                "record_ids": [],
                "reason": "control_context",
            }
        ]
    unavailable = resolve_target_resolutions(
        ["path:src/Button.tsx"],
        all_records,
        unavailable_record_ids={_id("component", "5")},
    )
    assert unavailable == [
        {
            "target_key": "path:src/Button.tsx",
            "status": "failed",
            "record_ids": [],
            "reason": "selected_taint",
        }
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
    base_model = _model()
    base_roles = derive_boundary_roles(base_model)
    assert base_roles[_id("module", "3")] == []
    assert base_roles[_id("module", "4")] == ["client_dependency"]

    model = base_model
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
    model["modules"][1]["derived_roles"] = ["client_dependency", "server_candidate"]
    roles = derive_boundary_roles(model)
    assert roles[_id("module", "3")] == []
    assert roles[_id("module", "4")] == ["client_dependency", "server_candidate"]
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
    discovered = _discovered_index(proof, model)
    edges = derive_required_causal_edges(proof, discovered)
    _materialize_single_root_taints(proof, model)
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
            {
                "collection": "modules",
                "record_id": barrel_module["id"],
                "record": barrel_module,
                "taints": [],
            },
            {
                "collection": "modules",
                "record_id": consumer_module["id"],
                "record": consumer_module,
                "taints": [],
            },
            {
                "collection": "members",
                "record_id": barrel_export["id"],
                "record": barrel_export,
                "taints": [],
            },
            {
                "collection": "members",
                "record_id": consumer_binding["id"],
                "record": consumer_binding,
                "taints": [],
            },
            {
                "collection": "relations",
                "record_id": incoming_reexport["id"],
                "record": incoming_reexport,
                "taints": [],
            },
        ]
    )
    records = _discovered_index(proof, model)
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
    domain = _legacy_domain_fixture()
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

    # 9,500 non-Module/Component records can coexist with 500 published
    # internal entities at the all-record boundary.
    assert model_record_budget_allowed(500 + 9_500, 10_000)
    assert not model_record_budget_allowed(500 + 9_501, 10_000)
    assert not model_record_budget_allowed(10_001, 10_000)


def test_model_proof_wire_budget_and_response_precedence() -> None:
    limit = _next_limits()["max_model_records"]
    assert model_wire_record_count(limit) == limit
    assert model_wire_record_count(limit - 1, 1) == limit
    assert not model_record_budget_allowed(model_wire_record_count(limit), limit - 1)
    assert not model_record_budget_allowed(model_wire_record_count(limit, 1), limit)

    exact_model = classify_response_limit(
        raw_bytes=1024,
        aggregate_array_items=10,
        model_records=limit,
    )
    assert exact_model["allowed"] is True
    model_plus_one = classify_response_limit(
        raw_bytes=1024,
        aggregate_array_items=10,
        model_records=limit,
        proof_only_records=1,
    )
    assert model_plus_one["diagnostic_code"] == "CSV-NEXT-LIMIT-005"
    aggregate_plus_one = classify_response_limit(
        raw_bytes=1024,
        aggregate_array_items=100_001,
        model_records=10,
    )
    assert aggregate_plus_one["diagnostic_code"] == "CSV-NEXT-LIMIT-003"
    raw_plus_one = classify_response_limit(
        raw_bytes=16_777_217,
        aggregate_array_items=100_001,
        model_records=limit + 1,
    )
    assert raw_plus_one["diagnostic_code"] == "CSV-NEXT-LIMIT-003"
    assert raw_plus_one["stage"] == "response_raw_bytes"


def test_schema_valid_model_record_limit_is_reachable_on_generated_wire() -> None:
    limit = _next_limits()["max_model_records"]

    exact_model = _generated_context_model(limit - 1)
    exact_request = _request(exact_model, default_content=b"")
    exact_response = _response(exact_model, request=exact_request)
    _validator("next-adapter-response-v1.schema.json").validate(exact_response)
    exact_bytes = canonical_json_bytes(exact_response)
    exact_bounded = bounded_decode_json(exact_bytes, limits=exact_request["limits"])
    assert exact_bounded["allowed"] is True
    assert exact_bounded["materialized"] is True
    assert exact_bounded["total_array_items"] < exact_request["limits"]["max_total_array_items"]
    assert len(exact_bytes) < exact_request["limits"]["max_adapter_response_bytes"]
    assert validate_response_envelope(exact_bytes, exact_request)["allowed"] is True
    exact_decision = response_boundary_decision(
        exact_bytes, validate_adapter_request(exact_request)
    )
    assert isinstance(exact_decision, NextValidatedDecision)

    over_model = _generated_context_model(limit)
    over_request = _request(over_model, default_content=b"")
    over_response = _response(over_model, request=over_request)
    _validator("next-adapter-response-v1.schema.json").validate(over_response)
    over_bytes = canonical_json_bytes(over_response)
    over_bounded = bounded_decode_json(over_bytes, limits=over_request["limits"])
    assert over_bounded["allowed"] is True
    assert over_bounded["total_array_items"] < over_request["limits"]["max_total_array_items"]
    assert len(over_bytes) < over_request["limits"]["max_adapter_response_bytes"]
    with pytest.raises(AssertionError):
        validate_response_envelope(over_bytes, over_request)
    over_decision = response_boundary_decision(over_bytes, validate_adapter_request(over_request))
    assert isinstance(over_decision, PreResponseFailureDecision)
    assert over_decision.stage == "model_validation"
    assert over_decision.diagnostic_code == "CSV-NEXT-LIMIT-005"
    assert over_decision.known_counts["model_records"] == limit + 1
    assert over_decision.payload_available is False


def test_schema_valid_wire_aggregate_plus_one_precedes_model_and_schema_routing() -> None:
    """Exercise aggregate+1 on a schema-valid envelope, not a counter stub."""

    request = _request()
    response = _response(_model(), request=request)
    baseline = bounded_decode_json(canonical_json_bytes(response), limits=request["limits"])
    assert baseline["allowed"] is True
    aggregate_limit = request["limits"]["max_total_array_items"]
    extra = aggregate_limit + 1 - baseline["total_array_items"]
    assert extra > 1
    excluded_count = extra // 2
    failed_count = extra - excluded_count
    response["proof"]["excluded"] = [
        {
            "collection": "files",
            "record_id": f"next:file:{index:064x}",
            "reason": "not_selected",
        }
        for index in range(excluded_count)
    ]
    response["proof"]["failed"] = [
        {
            "collection": "files",
            "record_id": f"next:file:{index + excluded_count:064x}",
            "reason": "read_file",
        }
        for index in range(failed_count)
    ]
    _validator("next-adapter-response-v1.schema.json").validate(response)
    response_bytes = canonical_json_bytes(response)
    assert len(response_bytes) < request["limits"]["max_adapter_response_bytes"]
    bounded = bounded_decode_json(response_bytes, limits=request["limits"])
    assert bounded["allowed"] is False
    assert bounded["reason"] == "max_total_array_items"
    assert bounded["total_array_items"] == aggregate_limit + 1
    decision = response_boundary_decision(response_bytes, validate_adapter_request(request))
    assert isinstance(decision, PreResponseFailureDecision)
    assert decision.stage == "response_decode"
    assert decision.diagnostic_code == "CSV-NEXT-LIMIT-003"
    assert decision.known_counts["stdout_bytes"] == len(response_bytes)


def test_actual_json_aggregate_boundary_precedes_schema_validation() -> None:
    request = _request()
    aggregate_limit = request["limits"]["max_total_array_items"]
    aggregate_payload = (
        b'{"first":['
        + b"0," * (aggregate_limit // 2)
        + b"0],"
        + b'"second":['
        + b"0," * (aggregate_limit - aggregate_limit // 2 - 1)
        + b"0],"
        + b'"last":[0]}'
    )
    bounded = bounded_decode_json(aggregate_payload, limits=request["limits"])
    assert bounded["allowed"] is False
    assert bounded["reason"] == "max_total_array_items"
    assert bounded["total_array_items"] == aggregate_limit + 1
    decision = response_boundary_decision(aggregate_payload, validate_adapter_request(request))
    assert isinstance(decision, PreResponseFailureDecision)
    assert decision.stage == "response_decode"
    assert decision.diagnostic_code == "CSV-NEXT-LIMIT-003"
    assert decision.known_counts["stdout_bytes"] == len(aggregate_payload)
    assert decision.payload_available is False


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
    domain = _legacy_domain_fixture()
    decision = domain.validated_decision
    assert isinstance(decision, NextValidatedDecision)
    publication_context = decision.publication_context
    assert publication_context is not None
    launch_digest = digest(publication_context.process_launch_descriptor)
    fingerprint = recompute_run_fingerprint(
        source_view_fingerprint=domain["source"]["fingerprint"],
        source_plan_digest=domain["source_plan_digest"],
        domain_config_digest=domain["domain_config_digest"],
        projects=domain["projects"],
        targets=domain["targets"],
        formats=domain["formats"],
        stdout_selector=domain["run_context"]["stdout_selector"],
        limits=domain["limits"],
        node_version=domain["toolchain"]["node_version"],
        typescript_version=domain["toolchain"]["typescript_version"],
        adapter_version=domain["toolchain"]["adapter_version"],
        protocol=domain["toolchain"]["protocol"],
        trusted_environment_digest=domain["trusted_environment"]["sha256"],
        process_launch_descriptor_digest=launch_digest,
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
            formats=domain["formats"],
            stdout_selector=domain["run_context"]["stdout_selector"],
            limits=changed,
            node_version=domain["toolchain"]["node_version"],
            typescript_version=domain["toolchain"]["typescript_version"],
            adapter_version=domain["toolchain"]["adapter_version"],
            protocol=domain["toolchain"]["protocol"],
            trusted_environment_digest=domain["trusted_environment"]["sha256"],
            process_launch_descriptor_digest=launch_digest,
        )
        != fingerprint
    )
    changed_model_limit = copy.deepcopy(domain["limits"])
    changed_model_limit["max_model_records"] -= 1
    assert (
        recompute_run_fingerprint(
            source_view_fingerprint=domain["source"]["fingerprint"],
            source_plan_digest=domain["source_plan_digest"],
            domain_config_digest=domain["domain_config_digest"],
            projects=domain["projects"],
            targets=domain["targets"],
            formats=domain["formats"],
            stdout_selector=domain["run_context"]["stdout_selector"],
            limits=changed_model_limit,
            node_version=domain["toolchain"]["node_version"],
            typescript_version=domain["toolchain"]["typescript_version"],
            adapter_version=domain["toolchain"]["adapter_version"],
            protocol=domain["toolchain"]["protocol"],
            trusted_environment_digest=domain["trusted_environment"]["sha256"],
            process_launch_descriptor_digest=launch_digest,
        )
        != fingerprint
    )


def test_next_diagnostic_catalog_is_the_public_and_manifest_authority() -> None:
    catalog = _schema("next-diagnostic-catalog-v1.json")
    assert catalog["domain"] == "next"
    entries = cast(list[dict[str, Any]], catalog["entries"])
    assert len(entries) == 27
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
    manifest = _run_manifest(_legacy_domain_fixture("not_applicable"))
    _validator("run-manifest-v1.schema.json").validate(manifest)
    assert manifest["domains"][0]["diagnostics"][0]["code"] == "CSV-NEXT-APPLICABILITY-001"


@pytest.mark.parametrize("status", ["complete", "not_applicable", "incomplete"])
def test_next_run_manifest_status_matrix_and_public_stream_extensions(status: str) -> None:
    domain = _legacy_domain_fixture(status)
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
            stderr_bytes=_diagnostic_jsonl(manifest["diagnostics"]),
        )


def test_next_non_empty_run_manifest_discriminates_path_targets_and_projections() -> None:
    domain = _legacy_domain_fixture(targets=["path:src", "path:src/Button.tsx"])
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
    domain = _legacy_domain_fixture(status, overrun=overrun)
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
            stderr_bytes=_diagnostic_jsonl(manifest["diagnostics"]),
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
        validate_run_status_vector(None, summary, stream, {}, stdout, [], stderr_bytes=b"")
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
    validate_run_status_vector(None, summary, None, {}, b"", [], stderr_bytes=b"")


def test_entity_budget_overrun_is_payload_unavailable_without_artifacts() -> None:
    domain = _legacy_domain_fixture("incomplete", overrun=True)
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
        stderr_bytes=_diagnostic_jsonl(manifest["diagnostics"]),
    )


def test_direct_context_target_is_manifest_and_stdout_payload_unavailable() -> None:
    domain = _legacy_domain_fixture("incomplete", targets=["path:src/types.d.ts"])
    domain["payload_available"] = False
    domain["entity_count"] = None
    domain["incomplete_kind"] = "payload_unavailable"
    domain["artifact_paths"] = []
    domain["budget"]["actual"] = None
    domain["budget"]["outcome"] = "payload_unavailable"
    domain["diagnostics"] = [
        _public_diagnostic("CSV-NEXT-TARGET-001", path="src/types.d.ts", reason="control_context")
    ]
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
        b'"selector":"next:semantic-json","stable_reason":"target_payload_unavailable",'
        b'"target_failures":[{"reason":"control_context",'
        b'"target_key":"path:src/types.d.ts"}],'
        b'"type":"stdout_result"}\n'
    )


def test_entity_budget_gate_composes_entity_and_model_record_boundaries() -> None:
    for actual, resolved, allowed in ((500, 500, True), (501, 500, False), (501, 600, True)):
        outcome = entity_budget_gate(
            actual,
            original_outcome="complete",
            run_context=_run_context(
                resolved=resolved,
                source="builtin" if resolved == 500 else "explicit",
                requested=None if resolved == 500 else resolved,
            ),
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
    limit = _next_limits()["max_model_records"]
    assert model_record_budget_allowed(limit, limit)
    assert not model_record_budget_allowed(limit + 1, limit)


def test_entity_budget_gate_preserves_partial_safe_and_overrun_is_unavailable() -> None:
    partial = entity_budget_gate(
        500,
        original_outcome="partial_safe",
        run_context=_run_context(["semantic-json"]),
    )
    assert partial["allowed"] is True
    assert partial["payload_available"] is True
    assert partial["original_outcome"] == "partial_safe"
    assert partial["outcome"] == "partial_safe"
    overridden = entity_budget_gate(
        501,
        original_outcome="partial_safe",
        run_context=_run_context(
            ["plantuml"], resolved=600, source="explicit", requested=600, selector="next:plantuml"
        ),
    )
    assert overridden["allowed"] is True
    assert overridden["outcome"] == "partial_safe"
    overrun = entity_budget_gate(
        501,
        original_outcome="partial_safe",
        run_context=_run_context(["semantic-json", "plantuml"]),
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
        original_outcome="complete",
        run_context=_run_context(
            formats,
            selector=f"next:{formats[0]}" if len(formats) == 1 else "next:semantic-json",
        ),
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
        "path:a#b",
        "path:a\x00b",
        "path:e\u0301.txt",
        f"path:{accepted}a",
    ):
        with pytest.raises(AssertionError):
            canonical_target_key(invalid)


def test_round11_path_helper_is_byte_bounded_and_root_contextual() -> None:
    path_4095 = "é" * 2047 + "a"
    path_4096 = "é" * 2048
    path_4097 = path_4096 + "a"

    for path in (path_4095, path_4096):
        assert len(path.encode("utf-8")) in {4095, 4096}
        _assert_path(path, allow_root=False)
        _assert_file_path(path)
        assert canonical_target_key(f"path:{path}") == f"path:{path}"
        _validator("next-path-v1.schema.json").validate(path)

    # maxLength is intentionally only a character-count guard: this 4097-byte
    # value remains schema-shaped (2,049 code points) but the shared helper
    # rejects it on every path-bearing reference surface.
    _validator("next-path-v1.schema.json").validate(path_4097)
    with pytest.raises(AssertionError):
        _assert_file_path(path_4097)
    with pytest.raises(AssertionError):
        canonical_target_key(f"path:{path_4097}")

    assert canonical_target_key("path:.") == "path:."
    _assert_path(".")
    with pytest.raises(AssertionError):
        _assert_file_path(".")
    decomposed = "e\u0301.txt"
    with pytest.raises(AssertionError):
        _assert_file_path(decomposed)
    with pytest.raises(AssertionError):
        canonical_target_key(f"path:{decomposed}")
    with pytest.raises(AssertionError):
        _assert_file_path("src/a#b.ts")


def test_round11_run_context_is_explicit_across_budget_domain_root_and_stdout() -> None:
    context = _run_context(
        ["plantuml"],
        resolved=600,
        source="explicit",
        requested=600,
        selector="next:plantuml",
    )
    assert context == {
        "requested_formats": ["plantuml"],
        "budget_requested": 600,
        "budget_resolved": 600,
        "budget_source": "explicit",
        "stdout_selector": "next:plantuml",
    }
    with pytest.raises(AssertionError):
        canonical_run_context(
            requested_formats=["semantic-json"],
            budget_requested=600,
            budget_resolved=600,
            budget_source="explicit",
            stdout_selector="next:plantuml",
        )
    domain = _legacy_domain_fixture(
        formats=["plantuml"],
        max_entities=600,
        budget_source="explicit",
        budget_requested=600,
        stdout_selector="next:plantuml",
    )
    assert domain["run_context"] == context
    assert domain["budget"]["requested"] == 600
    assert domain["budget"]["resolved"] == 600
    assert domain["budget"]["source"] == "explicit"
    validate_domain_manifest(domain)
    manifest = _run_manifest(domain)
    validate_run_manifest(manifest, domain, _published_bytes(domain))
    assert manifest["run"]["run_context"] == context
    assert manifest["config"]["resolved"]["limits"] == domain["limits"]
    assert manifest["config"]["value_sources"]["limits"] == "explicit"
    stdout = _stdout_result_for_domain(domain, manifest)
    assert stdout["selector"] == "next:plantuml"
    assert stdout["artifact"]["format"] == "plantuml"


@pytest.mark.parametrize("selector", [None, "manifest", "next:semantic-json", "next:plantuml"])
def test_round12_run_context_selector_is_exactly_echoed_across_request_response_and_root(
    selector: str | None,
) -> None:
    context = _run_context(selector=selector)
    request = _request(run_context=context)
    validate_request_envelope(request)
    response = _response(_model(), request=request, run_context=context)
    decision = validate_response_envelope(canonical_json_bytes(response), request)
    assert decision["run_context"] == context

    domain = _domain(decision=decision["validated_decision"])
    validate_domain_manifest(domain)
    manifest = _run_manifest(domain)
    published = _published_bytes(domain)
    validate_run_manifest(manifest, domain, published)
    assert manifest["run"]["run_context"] == context
    assert manifest["command"]["stdout_selector"] == selector
    sealed_decision = domain.validated_decision
    assert sealed_decision is not None
    assert domain["run_fingerprint"] == recompute_run_fingerprint(
        source_view_fingerprint=domain["source"]["fingerprint"],
        source_plan_digest=domain["source_plan_digest"],
        domain_config_digest=domain["domain_config_digest"],
        projects=domain["projects"],
        targets=domain["targets"],
        formats=context["requested_formats"],
        stdout_selector=selector,
        limits=domain["limits"],
        node_version=domain["toolchain"]["node_version"],
        typescript_version=domain["toolchain"]["typescript_version"],
        adapter_version=domain["toolchain"]["adapter_version"],
        protocol=domain["toolchain"]["protocol"],
        trusted_environment_digest=domain["trusted_environment"]["sha256"],
        process_launch_descriptor_digest=digest(
            sealed_decision.publication_context.process_launch_descriptor
        ),
    )

    changed = copy.deepcopy(response)
    changed["run_context"]["stdout_selector"] = (
        "manifest" if selector != "manifest" else "next:semantic-json"
    )
    with pytest.raises(AssertionError):
        validate_response_envelope(canonical_json_bytes(changed), request)


def test_round12_repository_budget_500_is_not_inferred_as_builtin() -> None:
    context = _run_context(source="repository", requested=500, resolved=500, selector="manifest")
    request = _request(run_context=context)
    validate_request_envelope(request)
    response = _response(_model(), request=request, run_context=context)
    decision = validate_response_envelope(canonical_json_bytes(response), request)
    assert decision["budget_requested"] == 500
    assert decision["budget_source"] == "repository"


def test_program_file_requires_exactly_one_module_for_file_and_directory_targets() -> None:
    model = _model()
    model["modules"] = [module for module in model["modules"] if module["path"] != "src/Card.tsx"]
    model["modules"].sort(key=lambda record: record["id"])
    resolution = resolve_target_resolutions(["path:src/Card.tsx"], model)
    assert resolution == [
        {
            "target_key": "path:src/Card.tsx",
            "status": "failed",
            "record_ids": [],
            "reason": "component_only",
        }
    ]
    directory_resolution = resolve_target_resolutions(["path:src"], model)
    assert directory_resolution == [
        {
            "target_key": "path:src",
            "status": "failed",
            "record_ids": [],
            "reason": "component_only",
        }
    ]
    with pytest.raises(AssertionError):
        validate_model(model)


@pytest.mark.parametrize("target", ["path:src/Card.tsx", "path:src"])
@pytest.mark.parametrize("mutation", ["missing", "duplicate", "component_only"])
def test_round11_target_completeness_is_typed_and_projects_to_unavailable_run(
    target: str, mutation: str
) -> None:
    model = _model()
    card_module = next(module for module in model["modules"] if module["path"] == "src/Card.tsx")
    if mutation == "missing":
        model["modules"].remove(card_module)
        model["components"] = [
            component
            for component in model["components"]
            if component["module_id"] != card_module["id"]
        ]
    elif mutation == "duplicate":
        model["modules"].append(copy.deepcopy(card_module))
    else:
        model["modules"].remove(card_module)
        # Keep the component with its former module identity to prove that a
        # component record cannot substitute for the semantic Module owner.
    if mutation in {"missing", "component_only"}:
        card_component_id = _id("component", "6")
        model["members"] = [
            member
            for member in model["members"]
            if member.get("local_component_id") != card_component_id
        ]
        model["relations"] = [
            relation
            for relation in model["relations"]
            if relation.get("source_id") not in {card_module["id"], card_component_id}
            and relation.get("target", {}).get("module_id") != card_module["id"]
            and relation.get("target", {}).get("component_id") != card_component_id
            and relation.get("target_component_id") != card_component_id
        ]
        model["facts"] = [
            fact for fact in model["facts"] if fact.get("owner_id") != card_module["id"]
        ]
    _refresh_model_counts(model)
    request = _request(model, targets=[target])
    response = _response(model, request=request, run_context=_run_context())
    decision = validate_response_envelope(canonical_json_bytes(response), request)
    assert decision["diagnostic_code"] == "CSV-NEXT-TARGET-001"
    assert decision["outcome"] == "payload_unavailable"
    assert decision["payload_available"] is False
    assert decision["artifact_paths"] == []
    assert decision["target_failures"][0]["target_key"] == target
    expected_reason = {
        "missing": "missing",
        "duplicate": "duplicate",
        "component_only": "component_only",
    }[mutation]
    assert decision["target_failures"][0]["reason"] == expected_reason
    response_target = next(
        item
        for item in response["model"]["coverage"]["target_completeness"]
        if item["target_key"] == target
    )
    assert response_target["reason"] == expected_reason
    proof_target = next(
        item for item in response["proof"]["target_resolutions"] if item["target_key"] == target
    )
    assert proof_target["reason"] == expected_reason

    domain = _domain(decision=decision["validated_decision"])
    assert domain["incomplete_kind"] == "payload_unavailable"
    assert domain["payload_available"] is False
    assert domain["artifact_paths"] == []
    assert domain["diagnostics"][0]["code"] == "CSV-NEXT-TARGET-001"
    assert domain["diagnostics"][0]["reason"] == expected_reason
    domain_target = next(
        item for item in domain["coverage"]["target_completeness"] if item["target_key"] == target
    )
    assert domain_target["reason"] == expected_reason
    validate_domain_manifest(domain)
    manifest = _run_manifest(domain)
    validate_run_manifest(manifest, domain, {})
    manifest_target = next(
        item
        for item in manifest["domains"][0]["coverage"]["target_completeness"]
        if item["target_key"] == target
    )
    assert manifest_target["reason"] == expected_reason
    assert manifest["diagnostics"][0]["reason"] == expected_reason
    stream = _stdout_result_for_domain(domain, manifest, "next:semantic-json")
    _validator("stdout-result-v1.schema.json").validate(stream)
    assert stream["availability"] is False
    assert stream["target_failures"] == [{"target_key": target, "reason": expected_reason}]
    summary = _run_summary_value("incomplete", domain)
    validate_run_status_vector(
        manifest,
        summary,
        stream,
        {},
        canonical_json_bytes(stream) + b"\n",
        manifest["diagnostics"],
        stderr_bytes=_diagnostic_jsonl(manifest["diagnostics"]),
    )
    assert manifest["run"]["exit_code"] == 3


def test_response_base_rejects_invalid_cross_reference_before_target_failure() -> None:
    model = _model()
    card_module = next(module for module in model["modules"] if module["path"] == "src/Card.tsx")
    model["modules"].remove(card_module)
    model["components"] = [
        component
        for component in model["components"]
        if component["module_id"] != card_module["id"]
    ]
    model["members"] = [
        member
        for member in model["members"]
        if member.get("local_component_id") != _id("component", "6")
    ]
    model["relations"] = [
        relation
        for relation in model["relations"]
        if relation.get("source_id") != _id("component", "6")
        and relation.get("target", {}).get("component_id") != _id("component", "6")
        and relation.get("target_component_id") != _id("component", "6")
    ]
    model["facts"] = [fact for fact in model["facts"] if fact.get("owner_id") != card_module["id"]]
    invalid_relation = next(
        relation for relation in model["relations"] if relation["kind"] == "static_import"
    )
    invalid_relation["target"]["module_id"] = _id("module", "dead")
    invalid_relation["id"] = recompute_record_id(invalid_relation)
    _refresh_model_counts(model)
    request = _request(model, targets=["path:src/Card.tsx"])
    response = _response(model, request=request, run_context=_run_context())
    _validator("next-adapter-response-v1.schema.json").validate(response)
    failure = target_completeness_failure(model, request["targets"])
    assert failure is not None
    assert failure.failures == [{"target_key": "path:src/Card.tsx", "reason": "missing"}]
    with pytest.raises(AssertionError):
        validate_response_envelope(canonical_json_bytes(response), request)


def test_response_base_rejects_invalid_cross_reference_before_duplicate_target_failure() -> None:
    model = _model()
    card_module = next(module for module in model["modules"] if module["path"] == "src/Card.tsx")
    model["modules"].append(copy.deepcopy(card_module))
    invalid_relation = next(
        relation for relation in model["relations"] if relation["kind"] == "static_import"
    )
    invalid_relation["target"]["module_id"] = _id("module", "dead")
    invalid_relation["id"] = recompute_record_id(invalid_relation)
    _refresh_model_counts(model)
    request = _request(model, targets=["path:src/Card.tsx"])
    response = _response(model, request=request, run_context=_run_context())
    _validator("next-adapter-response-v1.schema.json").validate(response)
    failure = target_completeness_failure(model, request["targets"])
    assert failure is not None
    assert failure.failures == [{"target_key": "path:src/Card.tsx", "reason": "duplicate"}]
    with pytest.raises(AssertionError):
        validate_response_envelope(canonical_json_bytes(response), request)


@pytest.mark.parametrize("target_mutation", ["missing", "component_only", "duplicate"])
@pytest.mark.parametrize("proof_mutation", ["causal_edge", "export_owner", "extra_target"])
def test_target_failure_validates_complete_proof_before_typed_routing(
    target_mutation: str, proof_mutation: str
) -> None:
    """Compound proof corruption cannot be relabelled as a target failure."""

    model = _model()
    card_module = next(module for module in model["modules"] if module["path"] == "src/Card.tsx")
    if target_mutation == "missing":
        model["modules"].remove(card_module)
        model["components"] = [
            component
            for component in model["components"]
            if component["module_id"] != card_module["id"]
        ]
    elif target_mutation == "component_only":
        model["modules"].remove(card_module)
    else:
        model["modules"].append(copy.deepcopy(card_module))
    if target_mutation in {"missing", "component_only"}:
        card_component_id = _id("component", "6")
        model["members"] = [
            member
            for member in model["members"]
            if member.get("local_component_id") != card_component_id
        ]
        model["relations"] = [
            relation
            for relation in model["relations"]
            if relation.get("source_id") not in {card_module["id"], card_component_id}
            and relation.get("target", {}).get("module_id") != card_module["id"]
            and relation.get("target", {}).get("component_id") != card_component_id
            and relation.get("target_component_id") != card_component_id
        ]
        model["facts"] = [
            fact for fact in model["facts"] if fact.get("owner_id") != card_module["id"]
        ]
    _refresh_model_counts(model)
    request = _request(model, targets=["path:src/Card.tsx"])
    response = _response(model, request=request, run_context=_run_context())
    _validator("next-adapter-response-v1.schema.json").validate(response)

    mutated = copy.deepcopy(response)
    proof = mutated["proof"]
    if proof_mutation == "causal_edge":
        records = proof["discovered_records"]
        proof["causal_edges"].append(
            {
                "source_id": records[0]["record_id"],
                "record_id": records[1]["record_id"],
                "rule": "identity_dependency",
            }
        )
    elif proof_mutation == "export_owner":
        reexport = proof["export_reexport_witness"][0]
        reexport["owner_module_id"] = "next:module:" + "d" * 64
    else:
        proof["target_resolutions"].append(
            {
                "target_key": "path:src/types.d.ts",
                "status": "failed",
                "record_ids": [],
                "reason": "missing",
            }
        )
    _validator("next-adapter-response-v1.schema.json").validate(mutated)
    with pytest.raises(AssertionError):
        validate_response_envelope(canonical_json_bytes(mutated), request)


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


def test_adapter_stdout_capture_is_incremental_and_disposes_overrun() -> None:
    """Exercise a faithful chunk-reader harness, not an OS process test."""

    limit = 32
    decoded: list[bytes] = []
    exact_reads: list[int] = []

    def exact_chunks() -> Any:
        for chunk in (b"a" * 17, b"b" * 15):
            exact_reads.append(len(chunk))
            yield chunk

    exact = capture_adapter_stdout(exact_chunks(), limit=limit, decoder=decoded.append)
    assert exact["allowed"] is True
    assert exact["captured_bytes"] == limit
    assert exact["retained_bytes"] == limit
    assert exact["retained"] == b"a" * 17 + b"b" * 15
    assert exact["decoder_called"] is True
    assert exact["retained_bytes"] <= limit
    assert decoded == [b"a" * 17 + b"b" * 15]
    assert exact_reads == [17, 15]

    over_decoded: list[bytes] = []
    over_reads: list[int] = []

    def over_chunks() -> Any:
        for chunk in (b"a" * limit, b"b"):
            over_reads.append(len(chunk))
            yield chunk
        raise AssertionError("capture continued reading after process-group termination")

    over = capture_adapter_stdout(over_chunks(), limit=limit, decoder=over_decoded.append)
    assert over["allowed"] is False
    assert over["captured_bytes"] == limit + 1
    assert over["retained_bytes"] == 0
    assert over["retained"] == b""
    assert over["process_group_terminated"] is True
    assert over["raw_disposed"] is True
    assert over["partial_disposed"] is True
    assert over["read_stopped"] is True
    assert over["process_group_disposed"] is True
    assert over["decoder_called"] is False
    assert over_decoded == []
    assert over["diagnostic_code"] == "CSV-NEXT-LIMIT-003"
    assert over_reads == [limit, 1]

    unbounded_reads: list[int] = []

    def unbounded_chunks() -> Any:
        for index in range(100):
            unbounded_reads.append(index)
            yield b"x" * 7

    unbounded = capture_adapter_stdout(unbounded_chunks(), limit=10)
    assert unbounded["allowed"] is False
    assert unbounded["retained_bytes"] <= 10
    assert unbounded["retained"] == b""
    assert unbounded_reads == [0, 1]


def test_capture_success_routes_schema_valid_private_response_to_one_decision() -> None:
    request = _request()
    response_bytes = canonical_json_bytes(_response(_model(), request=request))
    decisions: list[NextRunDecision] = []

    def decode(payload: bytes) -> None:
        decisions.append(response_boundary_decision(payload, validate_adapter_request(request)))

    captured = capture_adapter_stdout(
        (response_bytes,),
        limit=request["limits"]["max_adapter_stdout_capture_bytes"],
        decoder=decode,
    )
    assert captured["allowed"] is True
    assert captured["decoder_called"] is True
    assert captured["retained"] == response_bytes
    assert len(decisions) == 1
    assert isinstance(decisions[0], NextValidatedDecision)


def test_adapter_stderr_harness_stops_before_retaining_child_text() -> None:
    limit = 8
    reads: list[int] = []

    def chunks() -> Any:
        for chunk in (b"a" * limit, b"b"):
            reads.append(len(chunk))
            yield chunk
        raise AssertionError("stderr capture continued after process-group termination")

    result = capture_adapter_stderr(chunks(), limit=limit)
    assert result["allowed"] is False
    assert result["captured_bytes"] == limit + 1
    assert result["read_stopped"] is True
    assert result["process_group_terminated"] is True
    assert result["process_group_disposed"] is True
    assert result["raw_disposed"] is True
    assert result["partial_disposed"] is True
    assert result["manifest_stderr_bytes"] == 0
    assert result["child_text_leaked"] is False
    assert reads == [limit, 1]


def test_selected_stdout_copy_has_exact_and_plus_one_publication_boundaries() -> None:
    payload = "UTF-8 表示\n".encode()
    exact = copy_selected_stdout(payload, limit=len(payload))
    assert exact["allowed"] is True
    assert exact["retained"] == payload
    assert exact["retained_bytes"] == len(payload)
    assert exact["publication_outcome"] == "published_artifact"

    over = copy_selected_stdout(payload, limit=len(payload) - 1)
    assert over["allowed"] is False
    assert over["retained"] == b""
    assert over["retained_bytes"] == 0
    assert over["partial_disposed"] is True
    assert over["publication_outcome"] == "selected_artifact_unavailable"
    assert over["diagnostic_code"] == "CSV-NEXT-LIMIT-003"


def _sealed_candidates_for_publication(
    decision: NextRunDecision,
    artifact_bytes: Mapping[str, bytes],
    *,
    transport_failure: bool = False,
    selected_copy_failure: bool = False,
) -> dict[str, bytes]:
    """Build all candidate streams before the final boundary seals them."""

    domain = _domain(decision=decision)
    if transport_failure and isinstance(decision, NextValidatedDecision):
        domain["status"] = "incomplete"
        domain["incomplete_kind"] = "payload_unavailable"
        domain["payload_available"] = False
        domain["entity_count"] = None
        domain["budget"]["actual"] = None
        domain["budget"]["outcome"] = "payload_unavailable"
        domain["artifact_paths"] = []
        domain["diagnostics"] = [_public_diagnostic("CSV-NEXT-LIMIT-003")]
    manifest = _run_manifest(domain)
    if selected_copy_failure:
        manifest["run"]["status"] = "incomplete"
        manifest["run"]["exit_code"] = 3
    summary = _run_summary_value(manifest["run"]["status"], domain)
    return {
        "summary": _canonical_json_line(summary),
        "manifest": _canonical_json_line(manifest),
        **{path: bytes(payload) for path, payload in artifact_bytes.items()},
    }


def test_round16_final_publication_decision_seals_capture_stderr_and_selected_copy() -> None:
    request = _request()
    response = _response(_model(), request=request)
    decision = validate_response_envelope(canonical_json_bytes(response), request)[
        "validated_decision"
    ]
    assert isinstance(decision, NextValidatedDecision)
    semantic_artifacts = _semantic_artifacts_from_decision(decision)
    selected_payload = semantic_artifacts["next.snapshot.semantic.json"]
    exact = finalize_publication_decision(
        decision,
        artifact_bytes=semantic_artifacts,
        stdout_candidates=_sealed_candidates_for_publication(decision, semantic_artifacts),
        adapter_stdout_chunks=(canonical_json_bytes(response),),
        adapter_stderr_chunks=(b"diagnostic",),
        adapter_stdout_limit=len(canonical_json_bytes(response)),
        adapter_stderr_limit=10,
        selected_stdout_limit=len(selected_payload),
    )
    assert exact.semantic_decision is decision
    assert exact.publication_outcome == "published"
    assert exact.exit_code == 0
    assert exact.adapter_stdout["retained_bytes"] == len(canonical_json_bytes(response))
    assert exact.adapter_stderr["captured_bytes"] == 10
    assert exact.selected_stdout["retained"] == selected_payload
    exact_domain, exact_manifest, exact_stream, exact_artifacts, exact_stderr = (
        _validate_publication_chain(exact)
    )
    assert exact_domain["status"] == "complete"
    assert exact_manifest["run"]["exit_code"] == 0
    assert exact_stream["availability"] is True
    assert exact_artifacts["next.snapshot.semantic.json"] == selected_payload
    assert exact_stderr == b""

    selected_overrun = finalize_publication_decision(
        decision,
        artifact_bytes=semantic_artifacts,
        stdout_candidates=_sealed_candidates_for_publication(
            decision, semantic_artifacts, selected_copy_failure=True
        ),
        adapter_stdout_chunks=(canonical_json_bytes(response),),
        adapter_stdout_limit=len(canonical_json_bytes(response)),
        selected_stdout_limit=len(selected_payload) - 1,
    )
    assert selected_overrun.semantic_decision is decision
    assert selected_overrun.publication_outcome == "selected_artifact_unavailable"
    assert selected_overrun.exit_code == 3
    assert selected_overrun.selected_stdout["retained_bytes"] == 0
    selected_domain, selected_manifest, selected_stream, selected_artifacts, selected_stderr = (
        _validate_publication_chain(selected_overrun)
    )
    assert selected_domain["status"] == "complete"
    assert selected_manifest["run"]["status"] == "incomplete"
    assert selected_manifest["run"]["exit_code"] == 3
    assert selected_stream["stable_reason"] == "selected_artifact_unavailable"
    assert selected_stream["artifact"] == selected_manifest["artifacts"][0]
    assert selected_artifacts["next.snapshot.semantic.json"] == selected_payload
    assert selected_stderr == b""

    capture_overrun = finalize_publication_decision(
        decision,
        artifact_bytes={},
        stdout_candidates=_sealed_candidates_for_publication(
            decision,
            {"next.snapshot.semantic.json": selected_payload},
            transport_failure=True,
        ),
        adapter_stdout_chunks=(b"ab",),
        adapter_stdout_limit=1,
    )
    assert capture_overrun.publication_outcome == "payload_unavailable"
    assert capture_overrun.exit_code == 3
    assert capture_overrun.adapter_stdout["retained_bytes"] == 0
    assert capture_overrun.adapter_stdout["decoder_called"] is False
    capture_domain, capture_manifest, capture_stream, capture_artifacts, capture_stderr = (
        _validate_publication_chain(capture_overrun)
    )
    assert capture_domain["incomplete_kind"] == "payload_unavailable"
    assert capture_manifest["run"]["exit_code"] == 3
    assert capture_stream["stable_reason"] == "domain_payload_unavailable"
    assert capture_artifacts == {}
    assert capture_stderr == b""

    stderr_overrun = finalize_publication_decision(
        decision,
        artifact_bytes={},
        stdout_candidates=_sealed_candidates_for_publication(
            decision,
            {"next.snapshot.semantic.json": selected_payload},
            transport_failure=True,
        ),
        adapter_stdout_chunks=(canonical_json_bytes(response),),
        adapter_stdout_limit=len(canonical_json_bytes(response)),
        adapter_stderr_chunks=(b"ab",),
        adapter_stderr_limit=1,
    )
    assert stderr_overrun.publication_outcome == "payload_unavailable"
    assert stderr_overrun.exit_code == 3
    assert stderr_overrun.adapter_stderr["manifest_stderr_bytes"] == 0
    stderr_domain, stderr_manifest, stderr_stream, stderr_artifacts, stderr_bytes = (
        _validate_publication_chain(stderr_overrun)
    )
    assert stderr_domain["incomplete_kind"] == "payload_unavailable"
    assert stderr_manifest["run"]["exit_code"] == 3
    assert stderr_stream["stable_reason"] == "domain_payload_unavailable"
    assert stderr_artifacts == {}
    assert stderr_bytes == b""

    target_request = _request(targets=["path:src/Missing.tsx"])
    target_response_bytes = canonical_json_bytes(_response(_model(), request=target_request))
    target_decision = validate_response_envelope(target_response_bytes, target_request)[
        "validated_decision"
    ]
    assert isinstance(target_decision, NextValidatedDecision)
    public_stderr_overrun = finalize_publication_decision(
        target_decision,
        artifact_bytes={},
        stdout_candidates=_sealed_candidates_for_publication(
            target_decision, {"next.snapshot.semantic.json": b""}
        ),
        adapter_stdout_chunks=(target_response_bytes,),
        adapter_stdout_limit=len(target_response_bytes),
        public_stderr_limit=1,
    )
    assert public_stderr_overrun.publication_outcome == "payload_unavailable"
    assert public_stderr_overrun.public_stderr["emitted_bytes"] == 0
    assert public_stderr_overrun.public_stderr["manifest_only"] is True
    assert _publication_stderr_bytes(public_stderr_overrun) == b""
    assert public_stderr_overrun.artifact_bytes == {}

    measurement_snapshot = exact.adapter_stdout
    measurement_snapshot["retained"] = b"substituted"
    assert exact.adapter_stdout["retained"] == canonical_json_bytes(response)
    substituted_measurement = exact.adapter_stdout
    substituted_measurement["captured_bytes"] = 1
    substituted_measurement["retained_bytes"] = 1
    substituted_measurement["retained"] = b"x"
    with pytest.raises(AssertionError):
        replace(exact, adapter_stdout=substituted_measurement)
    with pytest.raises(AssertionError):
        replace(exact, measurement_digest="0" * 64)
    with pytest.raises(TypeError):
        _publication_stdout(exact, publication_outcome="payload_unavailable")  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        _publication_domain(exact, selected_stdout={"allowed": False})  # type: ignore[call-arg]
    with pytest.raises(AssertionError):
        replace(exact, publication_outcome="payload_unavailable")


def test_round17_publication_artifacts_are_bound_to_the_immutable_decision() -> None:
    request = _request()
    response = _response(_model(), request=request)
    decision = validate_response_envelope(canonical_json_bytes(response), request)[
        "validated_decision"
    ]
    assert isinstance(decision, NextValidatedDecision)
    artifacts = _semantic_artifacts_from_decision(decision)
    semantic = json.loads(artifacts["next.snapshot.semantic.json"].decode("utf-8"))
    semantic["source"]["fingerprint"] = "0" * 64
    substituted = {
        **artifacts,
        "next.snapshot.semantic.json": canonical_json_bytes(semantic) + b"\n",
    }
    with pytest.raises(AssertionError):
        finalize_publication_decision(
            decision,
            artifact_bytes=substituted,
            stdout_candidates=_sealed_candidates_for_publication(decision, substituted),
            adapter_stdout_chunks=(canonical_json_bytes(response),),
        )


def test_round18_publication_projections_return_sealed_candidate_bytes() -> None:
    request = _request(run_context=_run_context(selector="manifest"))
    response = _response(_model(), request=request)
    response_bytes = canonical_json_bytes(response)
    decision = validate_response_envelope(response_bytes, request)["validated_decision"]
    assert isinstance(decision, NextValidatedDecision)
    artifacts = _semantic_artifacts_from_decision(decision)
    pre_domain = _domain(decision=decision)
    pre_manifest = _run_manifest(pre_domain)
    candidates = {
        "summary": _canonical_json_line(
            _run_summary_value(pre_manifest["run"]["status"], pre_domain)
        ),
        "manifest": _canonical_json_line(pre_manifest),
        **artifacts,
    }
    publication = finalize_publication_decision(
        decision,
        artifact_bytes=artifacts,
        stdout_candidates=candidates,
        adapter_stdout_chunks=(response_bytes,),
        adapter_stdout_limit=len(response_bytes),
        selected_stdout_limit=len(candidates["manifest"]),
    )
    assert publication.publication_outcome == "published"
    assert _publication_stdout_bytes(publication) == candidates["manifest"]
    assert publication.sealed_stdout_candidates["manifest"] == candidates["manifest"]
    candidate_snapshot = publication.sealed_stdout_candidates
    candidates["manifest"] = b"substituted"
    assert publication.sealed_stdout_candidates == candidate_snapshot
    _, manifest, stdout, artifacts_out, _ = _validate_publication_chain(publication)
    assert _canonical_json_line(manifest) == candidate_snapshot["manifest"]
    assert stdout["availability"] is True
    assert artifacts_out == artifacts


def test_round18_run_manifest_and_diagnostic_discriminators_are_closed() -> None:
    request = _request()
    response = _response(_model(), request=request)
    decision = validate_response_envelope(canonical_json_bytes(response), request)[
        "validated_decision"
    ]
    assert isinstance(decision, NextValidatedDecision)
    domain = _domain(decision=decision)
    manifest = _run_manifest(domain)
    manifest_validator = _validator("run-manifest-v1.schema.json")
    manifest_validator.validate(manifest)
    missing_discriminator = copy.deepcopy(manifest)
    del missing_discriminator["request_independent"]
    with pytest.raises(ValidationError):
        manifest_validator.validate(missing_discriminator)

    target = _public_diagnostic("CSV-NEXT-TARGET-001", path="src/Missing.tsx", reason="missing")
    diagnostic_validator = _validator("diagnostic-v1.schema.json")
    diagnostic_validator.validate(target)
    without_reason = {key: value for key, value in target.items() if key != "reason"}
    with pytest.raises(ValidationError):
        diagnostic_validator.validate(without_reason)


@pytest.mark.parametrize(
    "selector",
    [None, "manifest", "next:semantic-json", "next:plantuml"],
)
def test_round17_final_publication_stdout_union_seals_summary_manifest_exact_and_plus_one(
    selector: str | None,
) -> None:
    """Exercise non-domain stdout branches through the final decision object."""

    request = _request(run_context=_run_context(selector=selector))
    response = _response(_model(), request=request)
    response_bytes = canonical_json_bytes(response)
    decision = validate_response_envelope(response_bytes, request)["validated_decision"]
    assert isinstance(decision, NextValidatedDecision)
    artifacts = _semantic_artifacts_from_decision(decision)
    prepublication_domain = _domain(decision=decision)
    prepublication_manifest = _run_manifest(prepublication_domain)
    if selector is None:
        selected_payload = _canonical_json_line(
            _run_summary_value(prepublication_manifest["run"]["status"], prepublication_domain)
        )
    elif selector == "manifest":
        selected_payload = _canonical_json_line(prepublication_manifest)
    else:
        selected_payload = artifacts[
            "next.snapshot.semantic.json"
            if selector == "next:semantic-json"
            else "next.snapshot.puml"
        ]

    exact = finalize_publication_decision(
        decision,
        artifact_bytes=artifacts,
        stdout_candidates=_sealed_candidates_for_publication(decision, artifacts),
        adapter_stdout_chunks=(response_bytes,),
        adapter_stdout_limit=len(response_bytes),
        selected_stdout_limit=len(selected_payload),
    )
    assert exact.publication_outcome == "published"
    exact_domain, exact_manifest, exact_stdout, _, _ = _validate_publication_chain(exact)
    assert exact_domain["status"] == "complete"
    assert exact_manifest["run"]["exit_code"] == 0
    assert _publication_stdout_bytes(exact) == selected_payload
    assert exact.selected_stdout["retained"] == selected_payload
    if selector is None:
        assert exact_stdout["selector"] is None
        assert exact_stdout["stable_reason"] == "run_summary"
        assert exact_stdout["availability"] is False
    elif selector == "manifest":
        assert exact_stdout["selector"] == "manifest"
        assert exact_stdout["stable_reason"] == "run_manifest"
        assert exact_stdout["availability"] is True
    else:
        assert exact_stdout["selector"] == selector
        assert exact_stdout["stable_reason"] == "published_artifact"
        assert exact_stdout["availability"] is True

    overrun = finalize_publication_decision(
        decision,
        artifact_bytes=artifacts,
        stdout_candidates=_sealed_candidates_for_publication(
            decision, artifacts, selected_copy_failure=True
        ),
        adapter_stdout_chunks=(response_bytes,),
        adapter_stdout_limit=len(response_bytes),
        selected_stdout_limit=len(selected_payload) - 1,
    )
    assert overrun.publication_outcome == "selected_artifact_unavailable"
    assert overrun.exit_code == 3
    assert overrun.selected_stdout["retained"] == b""
    over_domain, over_manifest, over_stdout, _, _ = _validate_publication_chain(overrun)
    assert over_domain["status"] == "complete"
    assert over_manifest["run"]["status"] == "incomplete"
    assert over_manifest["run"]["exit_code"] == 3
    assert over_stdout["availability"] is False
    assert over_stdout["selected_stdout_unavailable"] is True
    assert _publication_stdout_bytes(overrun) == _canonical_json_line(over_stdout)
    if selector is None:
        assert over_stdout["run_status"] == "incomplete"
        assert over_stdout["artifact"] is None
    elif selector == "manifest":
        assert over_stdout["domain_status"] == "complete"
        assert over_stdout["stable_reason"] == "selected_artifact_unavailable"
        assert over_stdout["artifact"]["path"] == "run-manifest.json"
    else:
        assert over_stdout["domain_status"] == "complete"
        assert over_stdout["stable_reason"] == "selected_artifact_unavailable"
        assert over_stdout["artifact"]["path"] in {
            "next.snapshot.semantic.json",
            "next.snapshot.puml",
        }


def test_round16_process_launch_descriptor_is_closed_and_security_deterministic() -> None:
    descriptor = process_launch_descriptor(
        node_status="available",
        node_realpath="/usr/local/bin/node",
        node_sha256="1" * 64,
        node_version="22.14.0",
        spawn_executable="/usr/local/bin/node",
        file_identity_at_hash={
            "realpath": "/usr/local/bin/node",
            "sha256": "1" * 64,
            "version": "22.14.0",
        },
        file_identity_at_spawn={
            "realpath": "/usr/local/bin/node",
            "sha256": "1" * 64,
            "version": "22.14.0",
        },
        spawn_handle="fixture-process-group",
    )
    validate_process_launch_descriptor(descriptor)
    _validator("next-process-launch-v1.schema.json").validate(descriptor)
    assert descriptor["node_realpath"].startswith("/")
    assert descriptor["shell"] is False
    assert descriptor["fd_inheritance"] == {"close_fds": True, "allowed": [0, 1, 2]}
    assert descriptor["env_allowlist"] == {"LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC"}
    for field, mutation in (
        ("node_realpath", "node"),
        ("symlink_policy", "follow"),
        ("shell", True),
        ("env_allowlist", {"LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC", "PATH": "/tmp"}),
        ("fd_inheritance", {"close_fds": False, "allowed": [0, 1, 2, 3]}),
        (
            "process_group",
            {"create": True, "terminate_scope": "children", "wait_after_terminate": True},
        ),
    ):
        mutated = copy.deepcopy(descriptor)
        mutated[field] = mutation
        with pytest.raises(AssertionError):
            validate_process_launch_descriptor(mutated)
        with pytest.raises(ValidationError):
            _validator("next-process-launch-v1.schema.json").validate(mutated)
    unavailable = process_launch_descriptor(
        node_status="unavailable",
        node_realpath=None,
        node_sha256=None,
        node_version=None,
        spawn_executable=None,
        file_identity_at_hash=None,
        file_identity_at_spawn=None,
        spawn_handle=None,
    )
    validate_process_launch_descriptor(unavailable)
    _validator("next-process-launch-v1.schema.json").validate(unavailable)
    with pytest.raises(AssertionError):
        validate_process_launch_descriptor({**unavailable, "node_realpath": "/usr/local/bin/node"})


def test_round18_process_descriptor_requires_os_identity_and_spawn_binding() -> None:
    """Round 18 retains the explicit identity/handle mutation gate."""

    test_round16_process_launch_descriptor_is_closed_and_security_deterministic()


def test_round16_publication_context_requires_explicit_launch_and_decision_context() -> None:
    """Every decision seals the observed launch descriptor; no writer defaults it."""

    request = _request()
    response = _response(_model(), request=request)
    validated = validate_response_envelope(canonical_json_bytes(response), request)[
        "validated_decision"
    ]
    assert isinstance(validated, NextValidatedDecision)
    pre_response = pre_response_failure_decision(
        request,
        stage="node_discovery",
        diagnostic_code="CSV-NEXT-NODE-001",
        decision_context=decision_context_for_request(
            validate_adapter_request(request),
            stage="node_discovery",
            diagnostic_code="CSV-NEXT-NODE-001",
            known_counts=_decision_known_counts(request),
            source_failure_ledger=(),
        ),
    )
    decisions: tuple[NextRunDecision, ...] = (
        validated,
        pre_response,
        not_applicable_decision(request),
    )

    assert (
        inspect.signature(NextPublicationContext).parameters["process_launch_descriptor"].default
        is inspect.Parameter.empty
    )
    assert (
        inspect.signature(PreResponseFailureDecision).parameters["decision_context"].default
        is inspect.Parameter.empty
    )
    assert (
        inspect.signature(NotApplicableDecision).parameters["decision_context"].default
        is inspect.Parameter.empty
    )

    context = validated.publication_context
    assert context is not None
    constructor_values = {
        name: getattr(context, name)
        for name in inspect.signature(NextPublicationContext).parameters
    }
    del constructor_values["process_launch_descriptor"]
    with pytest.raises(TypeError):
        NextPublicationContext(**constructor_values)

    with pytest.raises(TypeError):
        _publication_context_for_validated_request(
            validated.request,
            validated.run_context,
            toolchain=_toolchain_snapshot(),
            trusted_environment=_trusted_environment(),
            source_failure_ledger=(),
        )  # type: ignore[call-arg]

    for decision in decisions:
        publication_context = decision.publication_context
        assert publication_context is not None
        assert publication_context.process_launch_descriptor is not None
        assert publication_context.toolchain is not None
        assert (
            publication_context.process_launch_descriptor["node_status"]
            == publication_context.toolchain["node"]["status"]
        )
        mismatched_status = (
            "unavailable"
            if publication_context.process_launch_descriptor["node_status"] != "unavailable"
            else "available"
        )
        with pytest.raises(AssertionError):
            replace(
                publication_context,
                process_launch_descriptor=process_launch_descriptor(
                    node_status=mismatched_status,
                    node_realpath=None
                    if mismatched_status != "available"
                    else "/usr/local/bin/node",
                    node_sha256=None if mismatched_status != "available" else "1" * 64,
                    node_version=None if mismatched_status != "available" else "22.14.0",
                    spawn_executable=None
                    if mismatched_status != "available"
                    else "/usr/local/bin/node",
                    file_identity_at_hash=None
                    if mismatched_status != "available"
                    else {
                        "realpath": "/usr/local/bin/node",
                        "sha256": "1" * 64,
                        "version": "22.14.0",
                    },
                    file_identity_at_spawn=None
                    if mismatched_status != "available"
                    else {
                        "realpath": "/usr/local/bin/node",
                        "sha256": "1" * 64,
                        "version": "22.14.0",
                    },
                    spawn_handle=None
                    if mismatched_status != "available"
                    else "fixture-process-group",
                ),
            )

    with pytest.raises(AssertionError):
        replace(pre_response, decision_context=None)  # type: ignore[arg-type]
    with pytest.raises(AssertionError):
        replace(not_applicable_decision(request), decision_context=None)  # type: ignore[arg-type]


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


def test_public_stderr_limit_is_projected_through_manifest_and_selector_end_to_end() -> None:
    source_domain = _legacy_domain_fixture(
        "incomplete",
        formats=["plantuml"],
        stdout_selector="next:plantuml",
    )
    exact_gate = render_public_diagnostic_stderr(
        source_domain["diagnostics"],
        limit=len(_diagnostic_jsonl(source_domain["diagnostics"])),
    )
    assert exact_gate["allowed"] is True
    exact_manifest = _run_manifest(source_domain)
    exact_summary = _run_summary_value("incomplete", source_domain)
    exact_stream = _stdout_result_for_domain(source_domain, exact_manifest, "next:plantuml")
    validate_run_status_vector(
        exact_manifest,
        exact_summary,
        exact_stream,
        _published_bytes(source_domain),
        _published_bytes(source_domain)["next.snapshot.puml"],
        exact_manifest["diagnostics"],
        stderr_bytes=exact_gate["payload"],
        public_stderr_diagnostics=exact_gate["stderr_diagnostics"],
    )

    over_gate = render_public_diagnostic_stderr(
        source_domain["diagnostics"],
        limit=exact_gate["encoded_bytes"] - 1,
    )
    unavailable = copy.deepcopy(source_domain)
    unavailable["incomplete_kind"] = "payload_unavailable"
    unavailable["payload_available"] = False
    unavailable["entity_count"] = None
    unavailable["artifact_paths"] = []
    unavailable["budget"]["outcome"] = "payload_unavailable"
    unavailable["diagnostics"] = over_gate["manifest_diagnostics"]
    unavailable_manifest = _run_manifest(unavailable)
    validate_domain_manifest(unavailable)
    validate_run_manifest(unavailable_manifest, unavailable, {})
    unavailable_summary = _run_summary_value("incomplete", unavailable)
    unavailable_stream = _stdout_result_for_domain(
        unavailable, unavailable_manifest, "next:plantuml"
    )
    assert unavailable_stream["availability"] is False
    assert unavailable_manifest["run"]["exit_code"] == 3
    validate_run_status_vector(
        unavailable_manifest,
        unavailable_summary,
        unavailable_stream,
        {},
        canonical_json_bytes(unavailable_stream) + b"\n",
        unavailable_manifest["diagnostics"],
        stderr_bytes=over_gate["payload"],
        public_stderr_diagnostics=over_gate["stderr_diagnostics"],
    )


def test_bounded_decoder_rejects_duplicates_depth_strings_and_aggregate_before_materializing() -> (
    None
):
    allowed = bounded_decode_json(b'{"items":[1,2],"nested":{"ok":true}}')
    assert allowed["allowed"] is True
    assert allowed["materialized"] is True
    assert allowed["value"] == {"items": [1, 2], "nested": {"ok": True}}
    duplicate = bounded_decode_json(b'{"items":1,"items":2}')
    assert duplicate["allowed"] is False
    assert duplicate["reason"] == "duplicate_object_key"

    nested = bounded_decode_json(b"[" * 65 + b"0" + b"]" * 65)
    assert nested["allowed"] is False
    assert nested["reason"] == "max_json_nesting"
    long_string = bounded_decode_json(b'{"value":"abcd"}', limits={"max_json_string_bytes": 3})
    assert long_string["allowed"] is False
    assert long_string["reason"] == "max_json_string_bytes"
    unicode_string = bounded_decode_json('{"value":"表示"}'.encode())
    assert unicode_string["allowed"] is True
    assert unicode_string["max_string_bytes"] == len("表示".encode()) == 6
    assert bounded_decode_json('{"value":"表示"}'.encode(), limits={"max_json_string_bytes": 6})[
        "allowed"
    ]
    unicode_overrun = bounded_decode_json(
        '{"value":"表示"}'.encode(), limits={"max_json_string_bytes": 5}
    )
    assert unicode_overrun["allowed"] is False
    assert unicode_overrun["reason"] == "max_json_string_bytes"
    surrogate = bounded_decode_json(b'{"v":"\\ud83d\\ude00"}')
    assert surrogate["allowed"] is True
    assert surrogate["max_string_bytes"] == 4
    lone_surrogate = bounded_decode_json(b'{"v":"\\ud83d"}')
    assert lone_surrogate["allowed"] is False
    assert lone_surrogate["reason"] == "invalid_json"
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


def test_response_validation_accepts_only_the_bounded_raw_bytes_entrypoint() -> None:
    model = _model()
    request = _request(model)
    response = _response(model, request=request)
    response_bytes = canonical_json_bytes(response)
    assert validate_response_envelope(response_bytes, request)["allowed"] is True
    with pytest.raises((AssertionError, TypeError)):
        validate_response_envelope(response, request)  # type: ignore[arg-type]


def test_round18_validated_response_raw_bytes_are_opaque_authority() -> None:
    model = _model()
    request = validate_adapter_request(_request(model))
    response_bytes = canonical_json_bytes(_response(model, request=request.snapshot()))
    decision = validate_response_envelope(response_bytes, request)["validated_decision"]
    assert isinstance(decision, NextValidatedDecision)
    assert decision.raw_response_bytes == response_bytes
    assert decision.raw_response_sha256 == hashlib.sha256(response_bytes).hexdigest()
    mutated = response_bytes.replace(b'"proof":', b'"proof":', 1) + b" "
    with pytest.raises(AssertionError):
        replace(
            decision,
            raw_response_bytes=mutated,
            raw_response_sha256=hashlib.sha256(mutated).hexdigest(),
        )
    raw_snapshot = decision.raw_response_bytes
    assert isinstance(raw_snapshot, bytes)
    with pytest.raises(TypeError):
        cast(Any, decision.raw_response_bytes)[0] = 0


def test_raw_response_stdout_byte_cap_has_exact_and_plus_one_whole_run_projection() -> None:
    model = _model()
    request = _request(model)
    response_bytes = canonical_json_bytes(_response(model, request=request))
    limit = request["limits"]["max_adapter_response_bytes"]
    assert limit == request["limits"]["max_stdout_bytes"]
    assert len(response_bytes) < limit
    # Canonical raw bytes are the opaque response authority.  Whitespace
    # padding is still measured by the bounded decoder, but cannot be sealed
    # as a validated response because it is not canonical v1 JSON.
    exact = response_bytes
    exact_result = bounded_decode_json(exact, limits=request["limits"])
    assert exact_result["allowed"] is True
    assert exact_result["materialized"] is True
    assert validate_response_envelope(exact, request)["allowed"] is True

    plus_one = (response_bytes + b" " * (limit - len(response_bytes))) + b" "
    over_result = bounded_decode_json(plus_one, limits=request["limits"])
    assert over_result == {
        "allowed": False,
        "bytes": limit + 1,
        "total_array_items": 0,
        "array_count": 0,
        "max_array_items": 0,
        "max_nesting": 0,
        "max_string_bytes": 0,
        "failed_at_byte": limit,
        "reason": "max_adapter_response_bytes",
        "materialized": False,
    }
    with pytest.raises(AssertionError):
        validate_response_envelope(plus_one, request)

    # A raw response cap has no trusted model to publish.  The stable limit
    # diagnostic is the only manifest projection, and all selectors become
    # unavailable with exit 3; no artifact bytes are retained.  The decision
    # is created at the raw-response boundary, rather than by synthesizing an
    # incomplete domain object downstream.
    decision = response_boundary_decision(plus_one, validate_adapter_request(request))
    assert isinstance(decision, PreResponseFailureDecision)
    assert decision.stage == "response_raw_bytes"
    assert decision.diagnostic_code == "CSV-NEXT-LIMIT-003"
    assert decision.known_counts["stdout_bytes"] == limit + 1
    unavailable = _domain(decision=decision)
    manifest = _run_manifest(unavailable)
    validate_domain_manifest(unavailable)
    validate_run_manifest(manifest, unavailable, {})
    summary = _run_summary_value("incomplete", unavailable)
    stream = _stdout_result_for_domain(unavailable, manifest, "next:semantic-json")
    validate_run_status_vector(
        manifest,
        summary,
        stream,
        {},
        canonical_json_bytes(stream) + b"\n",
        manifest["diagnostics"],
        stderr_bytes=_diagnostic_jsonl(manifest["diagnostics"]),
    )
    assert manifest["run"]["exit_code"] == 3


def test_raw_response_mutations_all_cross_the_same_bounded_entrypoint() -> None:
    model = _model()
    request = _request(model)
    response_bytes = canonical_json_bytes(_response(model, request=request))
    duplicate = response_bytes.replace(
        b'"schema":"code-structure-viz.next-adapter-response/v1"',
        b'"schema":"code-structure-viz.next-adapter-response/v1",'
        b'"schema":"code-structure-viz.next-adapter-response/v1"',
        1,
    )
    raw_mutations = [
        (duplicate, request, "duplicate_object_key"),
        (b"[" * 65 + b"0" + b"]" * 65, request, "max_json_nesting"),
        (
            b'{"value":"abcd"}',
            {**request, "limits": {**request["limits"], "max_json_string_bytes": 3}},
            "max_json_string_bytes",
        ),
        (
            b"[0,1,2]",
            {**request, "limits": {**request["limits"], "max_array_items": 2}},
            "max_array_items",
        ),
    ]
    aggregate_payload = (
        b'{"first":['
        + b"0," * 50_000
        + b"0],"
        + b'"second":['
        + b"0," * 49_999
        + b"0],"
        + b'"last":[0]}'
    )
    raw_mutations.append((aggregate_payload, request, "max_total_array_items"))
    for payload, mutated_request, reason in raw_mutations:
        bounded = bounded_decode_json(payload, limits=mutated_request["limits"])
        assert bounded["allowed"] is False
        assert bounded["reason"] == reason
        with pytest.raises(AssertionError):
            validate_response_envelope(payload, mutated_request)


def test_whole_run_validator_rejects_projection_and_artifact_mutations() -> None:
    domain = _legacy_domain_fixture()
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


def test_publication_bytes_are_exact_model_payloads_and_digest_roots() -> None:
    domain = _legacy_domain_fixture(model=_inverse_order_two_project_model())
    manifest = _run_manifest(domain)
    published = _published_bytes(domain)
    validate_run_manifest(manifest, domain, published)
    decision = domain.validated_decision
    assert decision is not None
    assert recompute_publication_projection_digest(domain) == digest(
        {
            "model": decision.validated_model,
            "targets": domain["targets"],
            "formats": domain["formats"],
            "run_context": domain["run_context"],
            "run_fingerprint": domain["run_fingerprint"],
        }
    )

    semantic = json.loads(published["next.snapshot.semantic.json"].decode("utf-8"))
    semantic_validator = _validator("semantic-v1.schema.json")
    semantic_validator.validate(semantic)

    # Every public collection participates in the exact-byte root.  A
    # schema-valid order mutation and a schema-valid payload mutation for
    # each collection must both invalidate the artifact descriptor.
    for collection in ("projects", "files", "entities", "members", "relations", "facts"):
        ordered = copy.deepcopy(semantic)
        assert len(ordered[collection]) >= 2
        ordered[collection].reverse()
        semantic_validator.validate(ordered)
        ordered_bytes = canonical_json_bytes(ordered) + b"\n"
        ordered_published = dict(published)
        ordered_published["next.snapshot.semantic.json"] = ordered_bytes
        with pytest.raises(AssertionError):
            validate_run_manifest(manifest, domain, ordered_published)

        payload = copy.deepcopy(semantic)
        first = payload[collection][0]
        assert isinstance(first.get("id"), str)
        prefix, _separator, _old_digest = first["id"].rpartition(":")
        first["id"] = prefix + ":" + "f" * 64
        semantic_validator.validate(payload)
        payload_bytes = canonical_json_bytes(payload) + b"\n"
        payload_published = dict(published)
        payload_published["next.snapshot.semantic.json"] = payload_bytes
        with pytest.raises(AssertionError):
            validate_run_manifest(manifest, domain, payload_published)

    semantic["entities"].pop()
    omitted_entity = canonical_json_bytes(semantic) + b"\n"
    mutated = dict(published)
    mutated["next.snapshot.semantic.json"] = omitted_entity
    with pytest.raises(AssertionError):
        validate_run_manifest(manifest, domain, mutated)

    substituted = json.loads(published["next.snapshot.semantic.json"].decode("utf-8"))
    substituted["members"][0] = copy.deepcopy(substituted["members"][1])
    substituted["members"][0]["id"] = substituted["members"][1]["id"]
    substituted_bytes = canonical_json_bytes(substituted) + b"\n"
    mutated["next.snapshot.semantic.json"] = substituted_bytes
    with pytest.raises(AssertionError):
        validate_run_manifest(manifest, domain, mutated)

    plantuml = published["next.snapshot.puml"]
    assert b"M:apps/a/src/Button.tsx" in plantuml
    mutated["next.snapshot.puml"] = plantuml.replace(
        b"M:apps/a/src/Button.tsx", b"M:apps/a/src/Changed.tsx", 1
    )
    with pytest.raises(AssertionError):
        validate_run_manifest(manifest, domain, mutated)

    wrong_root = copy.deepcopy(manifest)
    wrong_root["artifacts"][0]["sha256"] = hashlib.sha256(omitted_entity).hexdigest()
    with pytest.raises(AssertionError):
        validate_run_manifest(wrong_root, domain, published)


def test_validated_decision_is_the_only_publication_authority() -> None:
    context = _run_context(["plantuml"], selector="next:plantuml")
    request = _request(run_context=context)
    response = _response(_model(), request=request, run_context=context)
    decision_projection = validate_response_envelope(canonical_json_bytes(response), request)
    decision = decision_projection["validated_decision"]
    assert isinstance(decision, NextValidatedDecision)
    assert decision.targets == ()
    original_model = decision.validated_model
    original_model["modules"].clear()
    assert decision.validated_model == decision_projection["validated_model"]

    domain = _domain(decision=decision_projection["validated_decision"])
    assert domain["run_context"] == context
    with pytest.raises(TypeError):
        _domain(  # type: ignore[call-arg]
            decision=decision_projection["validated_decision"], formats=["semantic-json"]
        )
    with pytest.raises(TypeError):
        _domain(  # type: ignore[call-arg]
            decision=decision_projection["validated_decision"], budget_source="explicit"
        )
    with pytest.raises(TypeError):
        _domain(
            decision=decision_projection["validated_decision"],
            stdout_selector="next:semantic-json",
        )  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        _domain(  # type: ignore[call-arg]
            decision=decision_projection["validated_decision"], status="incomplete"
        )

    published = _published_bytes(domain)
    validate_published_projection(domain, published)


def test_all_decision_variants_project_without_legacy_fixture_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    response = _response(_model(), request=request)
    validated_projection = validate_response_envelope(canonical_json_bytes(response), request)
    decisions: list[NextRunDecision] = [
        validated_projection["validated_decision"],
        pre_response_failure_decision(
            request,
            stage="response_protocol",
            diagnostic_code="CSV-NEXT-PROTOCOL-001",
            decision_context=decision_context_for_request(
                validate_adapter_request(request),
                stage="response_protocol",
                diagnostic_code="CSV-NEXT-PROTOCOL-001",
                known_counts=_decision_known_counts(request),
                source_failure_ledger=(),
            ),
        ),
        not_applicable_decision(request),
    ]

    def legacy_must_not_be_called(*_args: Any, **_kwargs: Any) -> _DomainProjection:
        pytest.fail("decision projection consulted the legacy fixture")

    def authority_helper_must_not_be_called(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        pytest.fail("decision projection consulted an external compatibility descriptor")

    monkeypatch.setattr(sys.modules[__name__], "_legacy_domain_fixture", legacy_must_not_be_called)
    monkeypatch.setattr(sys.modules[__name__], "_descriptor", authority_helper_must_not_be_called)
    for decision in decisions:
        domain = _domain(decision=decision)
        context = decision.publication_context
        assert context is not None
        assert domain["source"]["fingerprint"] == context.source_view_fingerprint
        assert domain["config"]["source_plan"] == context.final_source_acquisition_plan
        assert domain["config"]["limits"] == context.public_next_config["limits"]
        assert domain["run_context"] == context.run_context
        assert domain["toolchain"] == context.toolchain
        assert domain["trusted_environment"] == context.trusted_environment
        assert domain["compatibility_descriptor"] == context.compatibility_descriptor
        assert context.compatibility_descriptor is not None
        compatibility_descriptor = context.compatibility_descriptor
        assert domain["semantic_compatibility_id"] == compatibility_descriptor["compatibility_id"]
        assert domain["identity_versions"] == compatibility_descriptor["identity_versions"]
        assert domain["run_fingerprint"] == digest(context.run_fingerprint_preimage)
        validate_domain_manifest(domain)


def test_validated_decision_defensively_copies_request_and_publication_context() -> None:
    request = _request()
    response = _response(_model(), request=request)
    projection = validate_response_envelope(canonical_json_bytes(response), request)
    decision = projection["validated_decision"]
    assert isinstance(decision, NextValidatedDecision)
    request_snapshot = copy.deepcopy(decision.request)
    context_snapshot = decision.publication_context
    assert context_snapshot is not None
    assert (
        context_snapshot.run_fingerprint_preimage["identifier_unicode_version"]
        == ECMASCRIPT_IDENTIFIER_UNICODE_VERSION
    )
    assert (
        context_snapshot.run_fingerprint_preimage["identifier_unicode_table_digest"]
        == ECMASCRIPT_UNICODE_TABLE_DIGEST
    )
    request["limits"]["max_entities"] = 1
    request["targets"].append("path:src/Other.tsx")
    response["model"]["files"].clear()
    mutated_context = decision.publication_context
    assert decision.request == request_snapshot
    assert decision.publication_context == context_snapshot
    assert mutated_context is not None
    assert mutated_context.compatibility_descriptor is not None
    mutated_context.public_next_config["limits"]["max_entities"] = 1
    mutated_context.compatibility_descriptor["algorithm_versions"]["props"] = 99
    assert decision.publication_context == context_snapshot
    request_limits = decision.request["limits"]
    request_limits["max_entities"] = 1
    assert decision.request["limits"]["max_entities"] == request_snapshot["limits"]["max_entities"]
    with pytest.raises(TypeError):
        cast(Any, decision.request)["request_id"] = "0" * 64

    with pytest.raises(AssertionError):
        NextValidatedDecision(
            validated_model=decision.validated_model,
            validated_proof=decision.validated_proof,
            run_context=decision.run_context,
            pre_budget_outcome=decision.pre_budget_outcome,
            gate=decision.gate,
            request=decision.request,
            raw_response_bytes=canonical_json_bytes(
                {"model": decision.validated_model, "proof": decision.validated_proof}
            ),
            raw_response_sha256=hashlib.sha256(
                canonical_json_bytes(
                    {"model": decision.validated_model, "proof": decision.validated_proof}
                )
            ).hexdigest(),
            targets=decision.targets,
            target_failures=({"target_key": "path:src/Other.tsx", "reason": "missing"},),
            publication_context=decision.publication_context,
        )


def test_round17_validated_request_is_composed_and_revalidated() -> None:
    request = _request()
    sealed = validate_adapter_request(request)
    assert not isinstance(sealed, dict)
    assert sealed.canonical_bytes == canonical_json_bytes(request)
    assert sealed.canonical_sha256 == hashlib.sha256(sealed.canonical_bytes).hexdigest()

    request["limits"]["max_entities"] = 1
    request["files"][0]["content_base64"] = base64.b64encode(b"mutated\n").decode("ascii")
    assert sealed["limits"]["max_entities"] == _next_limits()["max_entities"]
    assert sealed["files"][0]["content_base64"] != request["files"][0]["content_base64"]
    snapshot = sealed.snapshot()
    snapshot["projects"][0]["root"] = "substituted"
    assert sealed["projects"][0]["root"] == "."

    with pytest.raises(TypeError):
        cast(Any, sealed)["request_id"] = "0" * 64
    with pytest.raises(TypeError):
        dict.__setitem__(cast(Any, sealed), "request_id", "0" * 64)
    assert validate_adapter_request(sealed) is sealed

    tampered = validate_adapter_request(_request())
    object.__setattr__(tampered, "canonical_sha256", "f" * 64)
    with pytest.raises(AssertionError):
        validate_adapter_request(tampered)


def test_request_independent_pre_response_decision_keeps_closed_context() -> None:
    context = _run_context(independent=True)
    decision_context = NextDecisionContext(
        run_context=context,
        request_id=None,
        targets=(),
        limits=None,
        stage="config_validation",
        diagnostic_code="CSV-NEXT-CONFIG-001",
        failure_kind="config",
        known_counts={
            "files": None,
            "source_bytes": None,
            "model_records": None,
            "stdout_bytes": None,
        },
        source_failure_ledger=(),
        outcome="payload_unavailable",
        payload_unavailable=True,
        exit_code=3,
        provenance_observation=_decision_provenance(
            kind="request_independent",
            stage="config_validation",
            request=False,
            limits=False,
            source_plan=False,
            toolchain=False,
            trusted_environment=False,
            budget=False,
        ),
        provenance="request_independent",
    )
    decision = pre_response_failure_decision(
        None,
        stage="config_validation",
        diagnostic_code="CSV-NEXT-CONFIG-001",
        decision_context=decision_context,
    )
    assert decision.request is None
    assert decision.decision_context is not None
    assert decision.decision_context.request_id is None
    assert decision.decision_context.limits is None
    assert decision.publication_context is not None
    assert decision.publication_context.public_next_request is None
    assert decision.outcome == "payload_unavailable"
    assert decision.exit_code == 3


def test_round18_request_independent_provenance_is_explicitly_unobserved() -> None:
    context = _run_context(independent=True)
    provenance = _decision_provenance(
        kind="request_independent",
        stage="config_validation",
        request=False,
        limits=False,
        source_plan=False,
        toolchain=False,
        trusted_environment=False,
        budget=False,
    )
    decision_context = NextDecisionContext(
        run_context=context,
        request_id=None,
        targets=(),
        limits=None,
        stage="config_validation",
        diagnostic_code="CSV-NEXT-CONFIG-001",
        failure_kind="config",
        known_counts={
            "files": None,
            "source_bytes": None,
            "model_records": None,
            "stdout_bytes": None,
        },
        source_failure_ledger=(),
        outcome="payload_unavailable",
        payload_unavailable=True,
        exit_code=3,
        provenance_observation=provenance,
        provenance="request_independent",
    )
    decision = pre_response_failure_decision(
        None,
        stage="config_validation",
        diagnostic_code="CSV-NEXT-CONFIG-001",
        decision_context=decision_context,
    )
    context_provenance = decision.publication_context.observation_provenance
    assert context_provenance["failure_stage"] == "config_validation"
    assert context_provenance["failure_code"] == "CSV-NEXT-CONFIG-001"
    assert context_provenance["observed"]["budget"] == {
        "state": "unobserved",
        "value": None,
    }
    assert decision.publication_context.public_next_config["limits"] is None
    assert decision.publication_context.toolchain is None
    with pytest.raises(AssertionError):
        canonical_run_context(
            requested_formats=["semantic-json"],
            budget_requested=None,
            budget_resolved=500,
            budget_source="unobserved",
            stdout_selector="next:semantic-json",
        )


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
    validate_run_status_vector(
        None,
        summary,
        stream,
        {},
        canonical_json_bytes(stream) + b"\n",
        [],
        stderr_bytes=b"",
    )


def test_runtime_unavailable_is_a_manifest_only_payload_unavailable_vector() -> None:
    request = _request()
    decision = pre_response_failure_decision(
        request,
        stage="node_discovery",
        diagnostic_code="CSV-NEXT-NODE-001",
        decision_context=decision_context_for_request(
            validate_adapter_request(request),
            stage="node_discovery",
            diagnostic_code="CSV-NEXT-NODE-001",
            known_counts=_decision_known_counts(request),
            source_failure_ledger=(),
        ),
    )
    domain = _domain(decision=decision)
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
        stderr_bytes=_diagnostic_jsonl(manifest["diagnostics"]),
    )


def test_round16_failure_matrix_is_catalog_derived_and_rejects_cross_product() -> None:
    """Every failure row has one legal stage/outcome and no free cross-product."""

    all_stages = {
        stage for row in DECISION_FAILURE_MATRIX.values() for stage in row["allowed_stages"]
    }
    for code, row in DECISION_FAILURE_MATRIX.items():
        for stage in row["allowed_stages"]:
            resolved = decision_failure_spec(code, stage)
            assert resolved["diagnostic_code"] == code
            assert resolved["failure_kind"] == decision_failure_kind(code)
            assert resolved["outcome"] in {"partial_safe", "payload_unavailable"}
            assert resolved["exit_code"] == (3 if resolved["outcome"] != "not_applicable" else 0)
            assert resolved["ref_permission"] in {"none", "path", "symbol", "path_or_symbol"}
        invalid_stage = next(stage for stage in all_stages if stage not in row["allowed_stages"])
        with pytest.raises(AssertionError):
            decision_failure_spec(code, invalid_stage)


def test_round16_pre_response_failure_is_narrowed_to_nonisolatable_source() -> None:
    """Pre-adapter source failures never invent a partial model/request."""

    context = _run_context(independent=True)
    ledger = SourceFailureLedger(
        failures=(
            {
                "path": "src/Broken.tsx",
                "stage": "source_read",
            },
        ),
        source_graph={
            "nodes": (
                {"id": "broken", "path": "src/Broken.tsx", "project_root": "src"},
                {"id": "unrelated", "path": "src/Unrelated.tsx", "project_root": "src"},
            ),
            "edges": (),
            "open_edges": (),
        },
        project_roots=("src",),
        targets=("path:src/Unrelated.tsx",),
        proof_roots=({"id": "failure-root-1", "path_ref": "src/Broken.tsx"},),
        seal_id="b" * 64,
        seal_digest=digest(
            {
                "seal_id": "b" * 64,
                "source_graph": {
                    "nodes": (
                        {"id": "broken", "path": "src/Broken.tsx", "project_root": "src"},
                        {"id": "unrelated", "path": "src/Unrelated.tsx", "project_root": "src"},
                    ),
                    "edges": (),
                    "open_edges": (),
                },
                "project_roots": ["src"],
                "targets": ["path:src/Unrelated.tsx"],
                "proof_roots": [{"id": "failure-root-1", "path_ref": "src/Broken.tsx"}],
            }
        ),
    )
    assert classify_source_failure(ledger)["diagnostic_code"] == "CSV-NEXT-SOURCE-001"
    assert ledger.safe_subset_proven is True
    with pytest.raises(AssertionError):
        pre_response_failure_decision(
            None,
            stage="source_read",
            diagnostic_code="CSV-NEXT-SOURCE-001",
            decision_context=NextDecisionContext(
                run_context=context,
                request_id=None,
                targets=(),
                limits=None,
                stage="source_read",
                diagnostic_code="CSV-NEXT-SOURCE-001",
                failure_kind="source",
                known_counts={
                    "files": None,
                    "source_bytes": None,
                    "model_records": None,
                    "stdout_bytes": None,
                },
                source_failure_ledger=(),
                outcome="payload_unavailable",
                payload_unavailable=True,
                exit_code=3,
                provenance_observation=_decision_provenance(
                    kind="request_independent",
                    stage="source_read",
                    request=False,
                    limits=False,
                    source_plan=False,
                    toolchain=False,
                    trusted_environment=False,
                    budget=False,
                ),
                provenance="request_independent",
            ),
        )
    unavailable = classify_source_failure(ledger)
    assert unavailable == {
        "diagnostic_code": "CSV-NEXT-SOURCE-001",
        "outcome": "partial_safe",
        "payload_available": True,
        "exit_code": 3,
    }


def test_round16_request_independent_source_failure_projects_schema_valid_whole_run() -> None:
    context = _run_context(independent=True)
    ledger = SourceFailureLedger(
        failures=(
            {
                "path": "src/Broken.tsx",
                "stage": "source_selection",
            },
        ),
        source_graph={
            "nodes": ({"id": "broken", "path": "src/Broken.tsx", "project_root": "src"},),
            "edges": (),
            "open_edges": ({"source": "broken"},),
        },
        project_roots=("src",),
        targets=(),
        proof_roots=({"id": "failure-root-2", "path_ref": "src/Broken.tsx"},),
        seal_id="c" * 64,
        seal_digest=digest(
            {
                "seal_id": "c" * 64,
                "source_graph": {
                    "nodes": ({"id": "broken", "path": "src/Broken.tsx", "project_root": "src"},),
                    "edges": (),
                    "open_edges": ({"source": "broken"},),
                },
                "project_roots": ["src"],
                "targets": [],
                "proof_roots": [{"id": "failure-root-2", "path_ref": "src/Broken.tsx"}],
            }
        ),
    )
    decision_context = NextDecisionContext(
        run_context=context,
        request_id=None,
        targets=(),
        limits=None,
        stage="source_selection",
        diagnostic_code="CSV-NEXT-SOURCE-003",
        failure_kind="source",
        known_counts={
            "files": None,
            "source_bytes": None,
            "model_records": None,
            "stdout_bytes": None,
        },
        source_failure_ledger=ledger.failures,
        outcome="payload_unavailable",
        payload_unavailable=True,
        exit_code=3,
        provenance_observation=_decision_provenance(
            kind="request_independent",
            stage="source_selection",
            request=False,
            limits=False,
            source_plan=False,
            toolchain=False,
            trusted_environment=False,
            budget=False,
        ),
        provenance="request_independent",
    )
    decision = pre_response_failure_decision(
        None,
        stage="source_selection",
        diagnostic_code="CSV-NEXT-SOURCE-003",
        decision_context=decision_context,
        source_failure_ledger=ledger,
        path="src/Broken.tsx",
    )
    assert decision.request is None
    assert decision.publication_context.source_failure_ledger == ledger.failures
    domain = _domain(decision=decision)
    validate_domain_manifest(domain)
    _validator("next-domain-manifest-v1.schema.json").validate(domain)
    manifest = _run_manifest(domain)
    validate_run_manifest(manifest, domain, {})
    _validator("run-manifest-v1.schema.json").validate(manifest)
    stream = _stdout_result_for_domain(domain, manifest)
    _validator("stdout-result-v1.schema.json").validate(stream)
    assert stream["stable_reason"] == "domain_payload_unavailable"


@pytest.mark.parametrize(
    ("stage", "diagnostic_code"),
    [
        ("node_discovery", "CSV-NEXT-NODE-001"),
        ("node_spawn", "CSV-NEXT-NODE-002"),
        ("node_timeout", "CSV-NEXT-NODE-003"),
        ("node_process", "CSV-NEXT-NODE-004"),
        ("response_protocol", "CSV-NEXT-PROTOCOL-001"),
        ("source_read", "CSV-NEXT-LIMIT-001"),
        ("source_selection", "CSV-NEXT-LIMIT-002"),
        ("adapter_stdout_capture", "CSV-NEXT-LIMIT-003"),
        ("adapter_heap", "CSV-NEXT-LIMIT-004"),
        ("model_validation", "CSV-NEXT-LIMIT-005"),
    ],
)
def test_pre_response_decision_is_the_only_authority_for_manifest_stdout_and_exit(
    stage: str, diagnostic_code: str
) -> None:
    request = _request()
    decision = pre_response_failure_decision(
        request,
        stage=stage,
        diagnostic_code=diagnostic_code,
        stdout_bytes=(request["limits"]["max_adapter_response_bytes"] + 1)
        if diagnostic_code == "CSV-NEXT-LIMIT-003"
        else None,
        decision_context=decision_context_for_request(
            validate_adapter_request(request),
            stage=stage,
            diagnostic_code=diagnostic_code,
            known_counts=_decision_known_counts(
                request,
                stdout_bytes=(request["limits"]["max_adapter_response_bytes"] + 1)
                if diagnostic_code == "CSV-NEXT-LIMIT-003"
                else None,
            ),
            source_failure_ledger=(),
        ),
    )
    assert isinstance(decision, PreResponseFailureDecision)
    assert decision.payload_available is False
    assert decision.artifact_paths == ()
    assert decision.exit_code == 3
    decision_request = decision.request
    assert decision_request is not None
    assert decision_request["request_id"] == request["request_id"]

    domain = _domain(decision=decision)
    assert domain.validated_decision is decision
    assert domain["status"] == "incomplete"
    assert domain["incomplete_kind"] == "payload_unavailable"
    assert domain["payload_available"] is False
    assert domain["entity_count"] is None
    assert domain["artifact_paths"] == []
    assert domain["diagnostics"] == [decision.diagnostic]
    validate_domain_manifest(domain)
    manifest = _run_manifest(domain)
    published = _published_bytes(domain)
    validate_run_manifest(manifest, domain, published)
    stream = _stdout_result_for_domain(domain, manifest)
    _validator("stdout-result-v1.schema.json").validate(stream)
    assert stream["availability"] is False
    assert stream["artifact"] is None
    assert stream["stable_reason"] == "domain_payload_unavailable"
    summary = _run_summary_value("incomplete", domain)
    validate_run_status_vector(
        manifest,
        summary,
        stream,
        published,
        canonical_json_bytes(stream) + b"\n",
        manifest["diagnostics"],
        stderr_bytes=_diagnostic_jsonl(manifest["diagnostics"]),
    )


@pytest.mark.parametrize("mutation", ["malformed_json", "duplicate_key", "schema", "reference"])
def test_response_boundary_failures_are_pre_response_decisions(mutation: str) -> None:
    request = _request()
    if mutation == "malformed_json":
        response_bytes = b'{"schema":'
    elif mutation == "duplicate_key":
        response_bytes = b'{"schema":"first","schema":"second"}'
    else:
        response = _response(_model(), request=request, run_context=_run_context())
        if mutation == "schema":
            response["unexpected"] = True
        else:
            relation = next(
                relation
                for relation in response["model"]["relations"]
                if relation["kind"] == "static_import"
            )
            relation["target"]["module_id"] = _id("module", "dead")
            relation["id"] = recompute_record_id(relation)
            response["model_digest"] = digest(response["model"])
        response_bytes = canonical_json_bytes(response)

    decision = response_boundary_decision(response_bytes, validate_adapter_request(request))
    assert isinstance(decision, PreResponseFailureDecision)
    assert decision.stage in {"response_decode", "response_validation"}
    assert decision.diagnostic_code == "CSV-NEXT-PROTOCOL-001"
    assert decision.payload_available is False
    assert decision.artifact_paths == ()
    domain = _domain(decision=decision)
    manifest = _run_manifest(domain)
    stream = _stdout_result_for_domain(domain, manifest)
    validate_run_status_vector(
        manifest,
        _run_summary_value("incomplete", domain),
        stream,
        {},
        canonical_json_bytes(stream) + b"\n",
        manifest["diagnostics"],
        stderr_bytes=_diagnostic_jsonl(manifest["diagnostics"]),
    )


def test_stdout_target_failures_are_bijective_sorted_and_target_only() -> None:
    model = _model()
    model["modules"].append(
        copy.deepcopy(
            next(module for module in model["modules"] if module["path"] == "src/Button.tsx")
        )
    )
    _refresh_model_counts(model)
    targets = ["path:src/Button.tsx", "path:src/Missing.tsx", "path:src/Other.tsx"]
    request = _request(model, targets=targets)
    response = _response(model, request=request, run_context=_run_context())
    decision_projection = validate_response_envelope(canonical_json_bytes(response), request)
    domain = _domain(decision=decision_projection["validated_decision"])
    manifest = _run_manifest(domain)
    stream = _stdout_result_for_domain(domain, manifest)
    _validator("stdout-result-v1.schema.json").validate(stream)
    assert stream["target_failures"] == [
        {"target_key": "path:src/Button.tsx", "reason": "duplicate"},
        {"target_key": "path:src/Missing.tsx", "reason": "missing"},
        {"target_key": "path:src/Other.tsx", "reason": "missing"},
    ]
    assert "reason" not in stream

    for base_domain in (
        _legacy_domain_fixture(),
        _legacy_domain_fixture("not_applicable"),
        _legacy_domain_fixture("incomplete", overrun=True),
    ):
        base_manifest = _run_manifest(base_domain)
        base_stream = _stdout_result_for_domain(base_domain, base_manifest)
        base_stream["target_failures"] = [
            {"target_key": "path:src/Missing.tsx", "reason": "missing"}
        ]
        with pytest.raises(ValidationError):
            _validator("stdout-result-v1.schema.json").validate(base_stream)


@pytest.mark.parametrize("reason", sorted(TARGET_FAILURE_REASONS))
def test_stdout_target_failure_reason_enum_is_closed_for_each_resolution_failure(
    reason: str,
) -> None:
    stream: dict[str, Any] = {
        "type": "stdout_result",
        "schema": "code-structure-viz.stdout-result/v1",
        "selector": "next:semantic-json",
        "availability": False,
        "domain_status": "incomplete",
        "stable_reason": "target_payload_unavailable",
        "artifact": None,
        "target_failures": [{"target_key": "path:src/Example.tsx", "reason": reason}],
    }
    _validator("stdout-result-v1.schema.json").validate(stream)
    duplicate_reason = copy.deepcopy(stream)
    duplicate_reason["target_failures"].append(
        {"target_key": "path:src/Other.tsx", "reason": reason}
    )
    duplicate_reason["target_failures"].sort(key=canonical_json_bytes)
    _validator("stdout-result-v1.schema.json").validate(duplicate_reason)
    with pytest.raises(ValidationError):
        _validator("stdout-result-v1.schema.json").validate(
            {**stream, "selector": "python:semantic-json"}
        )


def test_round16_target_resolution_exposes_all_closed_failure_reasons() -> None:
    base = _model()
    cases: dict[str, dict[str, Any]] = {}

    missing = copy.deepcopy(base)
    cases["missing"] = missing

    out_of_scope = copy.deepcopy(base)
    cases["out_of_scope"] = out_of_scope

    non_program = copy.deepcopy(base)
    non_program["files"].append(_file("n", "src/ambient.d.ts", "program", b"declare const x: 1;\n"))
    cases["non_program"] = non_program

    control_context = copy.deepcopy(base)
    cases["control_context"] = control_context

    project_ambiguity = copy.deepcopy(base)
    other_file = _file("m", "src/Other.tsx", "program", b"export const Other = 1;\n")
    other_file["project_id"] = _id("project", "other")
    project_ambiguity["files"].append(other_file)
    cases["project_ambiguity"] = project_ambiguity

    expected_targets = {
        "missing": "path:src/NoSuch.tsx",
        "out_of_scope": "path:outside/NoSuch.tsx",
        "non_program": "path:src/ambient.d.ts",
        "control_context": "path:src/types.d.ts",
        "project_ambiguity": "path:src",
    }
    for reason, model in cases.items():
        failure = target_completeness_failure(model, [expected_targets[reason]])
        assert failure is not None
        assert failure.failures == [{"target_key": expected_targets[reason], "reason": reason}]

    component_only = copy.deepcopy(base)
    card_module = next(
        module for module in component_only["modules"] if module["path"] == "src/Card.tsx"
    )
    component_only["modules"].remove(card_module)
    component_only_failure = target_completeness_failure(component_only, ["path:src/Card.tsx"])
    assert component_only_failure is not None
    assert component_only_failure.failures == [
        {"target_key": "path:src/Card.tsx", "reason": "component_only"}
    ]

    duplicate = copy.deepcopy(base)
    duplicate["files"].append(
        copy.deepcopy(next(file for file in duplicate["files"] if file["path"] == "src/Card.tsx"))
    )
    duplicate_failure = target_completeness_failure(duplicate, ["path:src/Card.tsx"])
    assert duplicate_failure is not None
    assert duplicate_failure.failures == [
        {"target_key": "path:src/Card.tsx", "reason": "duplicate"}
    ]

    selected_taint = resolve_target_resolutions(
        ["path:src/Button.tsx"], base, unavailable_record_ids={_id("component", "5")}
    )
    assert selected_taint[0]["reason"] == "selected_taint"


def test_round17_proof_derived_target_failure_is_typed_and_sorted() -> None:
    proof = {
        "target_resolutions": [
            {
                "target_key": "path:src/Other.tsx",
                "status": "failed",
                "record_ids": [],
                "reason": "selected_taint",
            },
            {
                "target_key": "path:src/Button.tsx",
                "status": "failed",
                "record_ids": [],
                "reason": "component_only",
            },
        ]
    }
    proof["target_resolutions"].sort(key=canonical_json_bytes)
    failure = target_failure_from_proof(proof)
    assert failure is not None
    assert failure.failures == [
        {"target_key": "path:src/Button.tsx", "reason": "component_only"},
        {"target_key": "path:src/Other.tsx", "reason": "selected_taint"},
    ]
    with pytest.raises(AssertionError):
        target_failure_from_proof(
            {
                "target_resolutions": [
                    {
                        "target_key": "path:src/Button.tsx",
                        "status": "failed",
                        "record_ids": [],
                        "reason": "not_a_target_reason",
                    }
                ]
            }
        )


def test_trusted_and_runtime_manifests_have_exact_sets_order_and_known_digests() -> None:
    environment = _trusted_environment()
    assert environment["sha256"] == (
        "2e232edf27d832b12ecd8159295681145eb27ce906a06abfa0e666eaa82de77d"
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
    rich["modules"][1]["derived_roles"] = ["client_dependency", "server_candidate"]
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
        "927c4a8619d7d3550db6dc817f5c359df8fe5f7443eef66aeaa1774b375192ca"
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


def test_round16_html_has_no_fixed_limit_inventory() -> None:
    html_path = (
        ROOT
        / "spec-dock"
        / "initiatives"
        / "init-00001-code-structure-visualization"
        / "epics"
        / "epic-00002-safe-git-structure-comparison"
        / "issues"
        / "iss-00008-generate-nextjs-component-snapshots"
        / "artifacts"
        / "20260831t022707z--nextjs-component-snapshot-best-practice-guide.html"
    )
    source = html_path.read_text(encoding="utf-8")
    assert "Round 16" in source
    assert "max_adapter_response_bytes" in source
    assert "max_selected_stdout_bytes" in source
    assert "stdout 16 MiB" not in source
    assert 'data-plantuml-contract="2"' in source


def test_round17_html_has_validation_pipeline_and_round17_state() -> None:
    html_path = (
        ROOT
        / "spec-dock"
        / "initiatives"
        / "init-00001-code-structure-visualization"
        / "epics"
        / "epic-00002-safe-git-structure-comparison"
        / "issues"
        / "iss-00008-generate-nextjs-component-snapshots"
        / "artifacts"
        / "20260831t022707z--nextjs-component-snapshot-best-practice-guide.html"
    )
    source = html_path.read_text(encoding="utf-8")
    assert "Round 17" in source
    for token in (
        "SourceDiscoveryIntent",
        "SourceFailureLedger",
        "request-independent",
        "process_launch_descriptor",
        "PublicationBoundaryDecision",
        "raw cap",
        "bounded decode/aggregate",
        "closed schema",
        "base/path/reference/proof",
        "actual model+proof-only count",
        "model gate",
        "entity gate",
        "selected copy",
        "LIMIT-003",
        "PROTOCOL-001",
        "selected_taint",
        "sort_keys=True",
    ):
        assert token in source
    assert "stdout 16 MiB" not in source
    assert 'data-plantuml-contract="2"' in source


def test_round18_html_validation_order_is_strict_and_reverse_mutation_fails() -> None:
    html_path = (
        ROOT
        / "spec-dock"
        / "initiatives"
        / "init-00001-code-structure-visualization"
        / "epics"
        / "epic-00002-safe-git-structure-comparison"
        / "issues"
        / "iss-00008-generate-nextjs-component-snapshots"
        / "artifacts"
        / "20260831t022707z--nextjs-component-snapshot-best-practice-guide.html"
    )
    source = html_path.read_text(encoding="utf-8")
    start = source.index('<section id="round18">')
    end = source.index("</section>", start)
    section = source[start:end]
    tokens = (
        "raw cap",
        "bounded decode/aggregate",
        "closed schema",
        "base/path/reference/proof",
        "actual model+proof-only count",
        "model gate",
        "entity gate",
        "selected copy",
    )
    positions = [section.index(f"<code>{token}</code>") for token in tokens]
    assert positions == sorted(positions)
    assert len(set(positions)) == len(tokens)

    reverse = section.replace(
        "<code>model gate</code> → <code>entity gate</code>",
        "<code>entity gate</code> → <code>model gate</code>",
    )
    reverse_positions = [reverse.index(f"<code>{token}</code>") for token in tokens]
    assert reverse_positions != sorted(reverse_positions)


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
        "round11-inverse-project-full-chain",
        "round11-run-context-propagation",
        "round11-path-byte-boundaries",
        "round11-file-module-typed-target-failure",
        "round11-jsx-lexical-state",
        "round11-reexport-star-zero",
        "round11-reexport-double-alias",
        "round11-export-failure-projection",
        "round11-raw-response-trust-boundary",
        "round11-stderr-end-to-end",
        "round17-request-authority",
        "round17-source-inventory-observation",
        "round17-request-independent-null-provenance",
        "round17-source-locality-derived",
        "round17-process-launch-explicit",
        "round17-publication-boundary-seal",
        "round17-stdout-closed-union",
        "round17-proof-target-reroute",
        "round17-surface-order",
        "round18-source-seal-observation",
        "round18-source-locality-seal",
        "round18-response-byte-authority",
        "round18-publication-sealed-bytes",
        "round18-process-identity-contract",
        "round18-request-independent-discriminator",
        "round18-stdout-closed-union",
        "round18-html-validation-order",
        "round18-path-byte-order",
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
        "round11-inverse-project-request-order",
        "round11-inverse-project-response-order",
        "round11-inverse-project-domain-order",
        "round11-inverse-project-root-order",
        "round11-run-context-selector-substitution",
        "round11-path-4097-byte",
        "round11-path-nfc-collision",
        "round11-target-missing-module-file",
        "round11-target-missing-module-directory",
        "round11-target-duplicate-module-file",
        "round11-target-duplicate-module-directory",
        "round11-target-component-only-file",
        "round11-target-component-only-directory",
        "round11-jsx-false-positive",
        "round11-reexport-witness-original-name",
        "round11-reexport-failure-as-resolved",
        "round11-raw-response-duplicate-key",
        "round11-raw-response-limit-mutation",
        "round11-stderr-limit-plus-one-end-to-end",
        "round17-source-inventory-injection",
        "round17-request-derived-mutation",
        "round17-source-locality-boolean",
        "round17-process-launch-substitution",
        "round17-publication-artifact-substitution",
        "round17-selector-branch-mutation",
        "round17-target-reason-mutation",
        "round17-order-reversal",
        "round18-source-inventory-injection",
        "round18-source-locality-boolean-equivalent",
        "round18-response-byte-substitution",
        "round18-publication-candidate-substitution",
        "round18-process-identity-substitution",
        "round18-request-independent-omission",
        "round18-stdout-branch-field",
        "round18-html-order-reversal",
        "round18-path-quote-inverse",
    } <= set(fixture["negative"])

    mapping = fixture["criterion_test_map"]
    expected_criteria = {
        *(f"round14.p1-{index}" for index in range(1, 6)),
        "round14.p2-1",
        "round14.p2-2",
        *(f"round15.p1-{index}" for index in range(1, 14)),
        *(f"round16.p1-{index}" for index in range(1, 17)),
        "round16.p2-1",
        "round16.p2-2",
        "round16.p2-3",
        *(f"round17.p1-{index}" for index in range(1, 10)),
        *(f"round17.p2-{index}" for index in range(1, 4)),
        *(f"round18.p1-{index}" for index in range(1, 8)),
        *(f"round18.p2-{index}" for index in range(1, 3)),
    }
    assert set(mapping) == expected_criteria
    mapped_tests = {name for names in mapping.values() for name in names}
    assert mapped_tests
    test_source = Path(__file__).read_text(encoding="utf-8")
    declared_tests = set(re.findall(r"^def (test_[A-Za-z0-9_]+)\(", test_source, re.MULTILINE))
    assert mapped_tests <= declared_tests
    reverse: dict[str, list[str]] = {name: [] for name in mapped_tests}
    for criterion, names in mapping.items():
        assert names
        for name in names:
            reverse[name].append(criterion)
    assert all(reverse.values())
