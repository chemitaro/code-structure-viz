import base64
import copy
import hashlib
import json
from typing import Any

import pytest
from jsonschema import ValidationError

from tests.contracts.next_reference_validation import (
    COLLECTIONS,
    VALIDATOR_SCHEMA,
    canonical_json_bytes,
    digest,
    recompute_compatibility_id,
    recompute_request_id,
    recompute_run_fingerprint,
    render_plantuml,
    validate_compatibility_descriptor,
    validate_domain_manifest,
    validate_limits,
    validate_limits_consistency,
    validate_model,
    validate_no_trusted_shadowing,
    validate_plantuml_contract,
    validate_proof,
    validate_request_envelope,
    validate_request_files,
    validate_response_envelope,
    validate_runtime_manifest,
    validate_trusted_environment,
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
    return f"next:{kind}:{digit * 64}"


def _descriptor() -> dict[str, Any]:
    descriptor = _next_compatibility_descriptor()
    descriptor["compatibility_id"] = recompute_compatibility_id(descriptor)
    return descriptor


def _project() -> dict[str, Any]:
    project = _next_project()
    project["id"] = _id("project", "0")
    project["file_ids"] = [_id("file", "1"), _id("file", "2")]
    return project


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
    file_one = _file("1", "src/Button.tsx", "program", b"export default Button;\n")
    file_two = _file("2", "src/types.d.ts", "context", b"export interface Props {}\n")
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
        "path": "src/types.d.ts",
        "router_context": "none",
        "client_entry": False,
        "derived_roles": [],
    }
    component_one = {
        "kind": "component",
        "id": _id("component", "5"),
        "module_id": module_one["id"],
        "declaration_key": "Button",
        "recognition_evidence": ["route_default", "jsx_output"],
        "props_state": "known",
    }
    component_two = {
        "kind": "component",
        "id": _id("component", "6"),
        "module_id": module_two["id"],
        "declaration_key": "PropsView",
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
            "reexport": False,
        },
        {
            "kind": "import_binding",
            "id": _id("member", "8"),
            "owner_id": module_one["id"],
            "local_component_id": component_two["id"],
            "imported_name": "PropsView",
            "role": "value",
            "source": {"kind": "internal", "module_id": module_two["id"]},
        },
        {
            "kind": "prop",
            "id": _id("member", "9"),
            "owner_id": component_one["id"],
            "name": "props",
            "type_node": _type_ir(module_one["id"]),
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
    ]
    model = {
        "schema": "code-structure-viz.next-model/v1",
        "projects": [_project()],
        "files": [file_one, file_two],
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
    counts["discovered"] = counts["published"]
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
        "request": {
            "projects": ["."],
            "targets": [],
            "upstream_depth": 1,
            "downstream_depth": 1,
            "formats": ["semantic-json", "plantuml"],
            "limits": _next_limits(),
            "source_plan_digest": "c" * 64,
            "domain_config_digest": "d" * 64,
            "run_fingerprint": "e" * 64,
            "trusted_environment_digest": trusted_environment_digest,
        },
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
                "path_ref": "src/Button.tsx",
                "symbol_ref": None,
                "outcome": "partial_safe",
                "ref_permission": "path_or_symbol",
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
    contents = [b"export default Button;\n", b"export interface Props {}\n"]
    files = []
    for file_record, content in zip(model["files"], contents, strict=True):
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
        "excluded": [],
        "failed": [],
    }


def _response(model: dict[str, Any], proof: dict[str, Any] | None = None) -> dict[str, Any]:
    descriptor = _descriptor()
    trusted_environment_digest = _trusted_environment()["sha256"]
    return {
        "schema": "code-structure-viz.next-adapter-response/v1",
        "protocol": "code-structure-viz.next-adapter/v1",
        "request_id": _request()["request_id"],
        "adapter_version": "1.0.0",
        "trusted_type_environment_digest": trusted_environment_digest,
        "semantic_compatibility_id": descriptor["compatibility_id"],
        "compatibility_descriptor": descriptor,
        "identity_versions": descriptor["identity_versions"],
        "limits": _next_limits(),
        "model": model,
        "proof": proof or _complete_proof(model),
        "model_digest": digest(model),
    }


def _trusted_environment() -> dict[str, Any]:
    value = _next_trusted_environment()
    value["sha256"] = digest({key: item for key, item in value.items() if key != "sha256"})
    return value


def _public_diagnostic(
    code: str, *, path: str | None = None, symbol: str | None = None
) -> dict[str, Any]:
    catalog = {
        entry["code"]: entry for entry in _schema("next-diagnostic-catalog-v1.json")["entries"]
    }
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
    status: str = "complete", *, overrun: bool = False, runtime_unavailable: bool = False
) -> dict[str, Any]:
    model = _model()
    descriptor = _descriptor()
    environment = _trusted_environment()
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
        entity_count: int | None = 4
        payload_available = True
        incomplete_kind = None
        artifact_paths = ["next.snapshot.semantic.json", "next.snapshot.puml"]
        diagnostics: list[dict[str, Any]] = []
        actual = 4
    elif status == "not_applicable":
        entity_count = 0
        payload_available = False
        incomplete_kind = None
        artifact_paths = []
        diagnostics = [_public_diagnostic("CSV-NEXT-APPLICABILITY-001")]
        actual = 0
    else:
        entity_count = None if overrun else 4
        payload_available = not overrun
        incomplete_kind = "payload_unavailable" if overrun else "partial_safe"
        artifact_paths = [] if overrun else ["next.snapshot.semantic.json", "next.snapshot.puml"]
        diagnostics = [
            _public_diagnostic(
                "CSV-NEXT-LIMIT-005" if overrun else "CSV-NEXT-FLOW-001",
                symbol=None if overrun else _id("component", "5"),
            )
        ]
        actual = 501 if overrun else 4
    value: dict[str, Any] = {
        "domain": "next",
        "status": status,
        "payload_available": payload_available,
        "entity_count": entity_count,
        "budget": {
            "name": "max_entities",
            "requested": None,
            "resolved": 500,
            "actual": actual,
            "source": "builtin",
        },
        "semantic_compatibility_id": descriptor["compatibility_id"],
        "compatibility_descriptor": descriptor,
        "identity_versions": descriptor["identity_versions"],
        "source_plan_digest": "c" * 64,
        "domain_config_digest": "d" * 64,
        "run_fingerprint": "e" * 64,
        "source": {
            "schema": "code-structure-viz.source-view/v1",
            "kind": "working-tree",
            "head_commit": None,
            "fingerprint": "b" * 64,
            "file_count": 2,
        },
        "request": {
            "projects": ["."],
            "targets": [],
            "upstream_depth": 1,
            "downstream_depth": 1,
            "formats": ["semantic-json", "plantuml"],
        },
        "config": {
            "schema": "code-structure-viz.domain-config/next/v1",
            "sha256": "8" * 64,
            "projects": [copy.deepcopy(model["projects"][0])],
            "limits": _next_limits(),
            "trusted_environment_digest": environment["sha256"],
        },
        "projects": [copy.deepcopy(model["projects"][0])],
        "targets": [],
        "formats": ["semantic-json", "plantuml"],
        "toolchain": {
            "node_version": "22.14.0",
            "typescript_version": "5.9.2",
            "adapter_version": "1.0.0",
            "protocol": "code-structure-viz.next-adapter/v1",
        },
        "trusted_environment": environment,
        "limits": _next_limits(),
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
    return value


def _run_manifest(domain: dict[str, Any]) -> dict[str, Any]:
    base = json.loads(
        (ROOT / "tests" / "golden" / "python_snapshot" / "whole" / "run-manifest.json").read_text(
            encoding="utf-8"
        )
    )
    status = domain["status"]
    base["contracts"]["plantuml"] = "code-structure-viz.plantuml/next/v1"
    base["adapters"] = [{"domain": "next", "name": "next-typescript", "version": "1"}]
    base["command"] = {
        "name": "snapshot",
        "domain": "next",
        "formats": ["semantic-json", "plantuml"],
        "stdout_selector": "next:semantic-json",
    }
    base["request"] = {
        "projects": ["."],
        "targets": [],
        "formats": ["semantic-json", "plantuml"],
        "upstream_depth": 1,
        "downstream_depth": 1,
    }
    base["source"] = domain["source"]
    base["config"] = {
        "schema": "code-structure-viz.config/v1",
        "source": "builtin",
        "sha256": "8" * 64,
        "resolved": {
            "next": {
                "projects": ["."],
                "targets": [],
                "formats": ["semantic-json", "plantuml"],
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
    base["run"] = {
        "status": status,
        "exit_code": 0 if status in {"complete", "not_applicable"} else 3,
        "fingerprint": "e" * 64,
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
                "size_bytes": 1,
                "sha256": "a" * 64,
            }
        )
    base["diagnostics"] = []
    return base


def test_public_next_semantic_variants_are_closed() -> None:
    validator = _validator("semantic-v1.schema.json")
    empty = _semantic(_empty_model())
    non_empty = _semantic(_model())
    partial = _semantic(_model(), "incomplete")
    for value in (empty, non_empty, partial):
        validator.validate(value)

    wrong_domain = copy.deepcopy(non_empty)
    wrong_domain["domain"] = "python"
    with pytest.raises(ValidationError):
        validator.validate(wrong_domain)
    wrong_shape = copy.deepcopy(non_empty)
    wrong_shape["facts"][0]["value"] = False
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


def test_props_ir_matches_design_variants_and_rejects_old_shapes() -> None:
    validator = _validator("next-semantic-v1.schema.json")
    value = _semantic(_model())
    validator.validate(value)

    mutations = []
    redacted_old = copy.deepcopy(value)
    redacted_props = {
        item["name"]: item for item in redacted_old["members"][2]["type_node"]["properties"]
    }
    redacted_props["title"]["type"] = {
        "kind": "redacted_literal",
        "value_kind": "string",
        "value_digest": "a" * 64,
    }
    mutations.append(redacted_old)
    tuple_old = copy.deepcopy(value)
    tuple_props = {
        item["name"]: item for item in tuple_old["members"][2]["type_node"]["properties"]
    }
    tuple_props["values"]["type"]["elements"][0]["rest"] = False
    mutations.append(tuple_old)
    function_old = copy.deepcopy(value)
    function_props = {
        item["name"]: item for item in function_old["members"][2]["type_node"]["properties"]
    }
    function_props["render"]["type"]["generic_ordinals"] = []
    mutations.append(function_old)
    repository_path = copy.deepcopy(value)
    repository_props = {
        item["name"]: item for item in repository_path["members"][2]["type_node"]["properties"]
    }
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
        variant["members"][2]["type_node"] = node
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
        variant["members"][2]["type_node"] = node
        with pytest.raises(ValidationError):
            validator.validate(variant)


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
    mutations = []

    duplicate = copy.deepcopy(model)
    duplicate["files"].append(copy.deepcopy(duplicate["files"][0]))
    mutations.append(duplicate)
    wrong_owner = copy.deepcopy(model)
    wrong_owner["members"][2]["owner_id"] = _id("module", "4")
    mutations.append(wrong_owner)
    wrong_roles = copy.deepcopy(model)
    wrong_roles["files"][0]["roles"] = ["program", "control"]
    mutations.append(wrong_roles)
    wrong_project = copy.deepcopy(model)
    wrong_project["files"][0]["project_id"] = _id("project", "9")
    mutations.append(wrong_project)
    wrong_fact = copy.deepcopy(model)
    wrong_fact["facts"][0]["value"] = False
    mutations.append(wrong_fact)
    dangling = copy.deepcopy(model)
    dangling["relations"][0]["target"]["module_id"] = _id("module", "f")
    mutations.append(dangling)
    wrong_count = copy.deepcopy(model)
    wrong_count["coverage"]["counts"]["components"] += 1
    mutations.append(wrong_count)

    for mutation in mutations:
        with pytest.raises(AssertionError):
            validate_model(mutation)


def test_adapter_request_response_and_partial_safe_proof_are_reference_validated() -> None:
    request = _request()
    _validator("next-adapter-request-v1.schema.json").validate(request)
    validate_request_envelope(request)

    response = _response(_model())
    _validator("next-adapter-response-v1.schema.json").validate(response)
    validate_response_envelope(response, request)
    validate_model(response["model"])
    validate_proof(response["proof"], response["model"])

    partial_model = _model()
    partial_model["coverage"]["counts"]["discovered"] += 2
    partial_model["coverage"]["counts"]["excluded"] = 1
    partial_model["coverage"]["counts"]["failed"] = 1
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
    partial_proof = _complete_proof(partial_model)
    partial_proof["discovered_records"].extend(
        [
            {"collection": "files", "record": extra_file, "taints": ["parse_file"]},
            {"collection": "modules", "record": extra_module, "taints": ["parse_file"]},
        ]
    )
    partial_proof["excluded"] = [
        {"collection": "files", "record_id": extra_file["id"], "reason": "tainted"}
    ]
    partial_proof["failed"] = [
        {"collection": "modules", "record_id": extra_module["id"], "reason": "parse_file"}
    ]
    partial_proof["failure_roots"] = [
        {
            "id": "next:failure:" + "0" * 64,
            "collection": "files",
            "kind": "parse_file",
            "path_ref": "src/Unused.tsx",
        }
    ]
    partial_proof["causal_edges"] = [
        {
            "source_id": "next:failure:" + "0" * 64,
            "record_id": extra_file["id"],
            "rule": "file_all_records",
        }
    ]
    partial_proof["target_resolutions"] = [
        {
            "target_key": "component:src/Button.tsx#Button",
            "status": "resolved",
            "record_ids": [_id("component", "5")],
        }
    ]
    partial_model["coverage"]["target_completeness"] = [
        {
            "target_key": "component:src/Button.tsx#Button",
            "status": "complete",
            "record_ids": [_id("component", "5")],
        }
    ]
    partial_response = _response(partial_model, partial_proof)
    _validator("next-adapter-response-v1.schema.json").validate(partial_response)
    validate_proof(
        partial_response["proof"],
        partial_response["model"],
        {"component:src/Button.tsx#Button": (_id("component", "5"),)},
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
            {"component:src/Button.tsx#Button": (_id("component", "5"),)},
        )

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
    entries = catalog["entries"]
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
    _validator("next-domain-manifest-v1.schema.json").validate(domain)
    _validator("run-manifest-v1.schema.json").validate(manifest)
    summary = {
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
    _validator("run-summary-v1.schema.json").validate(summary)
    if status != "complete":
        stream = {
            "type": "stdout_result",
            "schema": "code-structure-viz.stdout-result/v1",
            "selector": "next:semantic-json",
            "availability": False,
            "domain_status": status,
            "stable_reason": "domain_not_applicable"
            if status == "not_applicable"
            else "domain_payload_unavailable",
            "artifact": None,
        }
        _validator("stdout-result-v1.schema.json").validate(stream)


def test_entity_budget_overrun_is_payload_unavailable_without_artifacts() -> None:
    domain = _domain("incomplete", overrun=True)
    validate_domain_manifest(domain)
    _validator("next-domain-manifest-v1.schema.json").validate(domain)
    manifest = _run_manifest(domain)
    _validator("run-manifest-v1.schema.json").validate(manifest)
    assert domain["budget"]["actual"] > domain["budget"]["resolved"]
    assert domain["artifact_paths"] == []
    assert domain["payload_available"] is False


def test_runtime_unavailable_is_a_manifest_only_payload_unavailable_vector() -> None:
    domain = _domain("incomplete", runtime_unavailable=True)
    validate_domain_manifest(domain)
    _validator("next-domain-manifest-v1.schema.json").validate(domain)
    manifest = _run_manifest(domain)
    _validator("run-manifest-v1.schema.json").validate(manifest)
    assert domain["incomplete_kind"] == "payload_unavailable"
    assert domain["diagnostics"][0]["code"] == "CSV-NEXT-NODE-001"
    assert domain["artifact_paths"] == []
    assert domain["payload_available"] is False


def test_trusted_and_runtime_manifests_have_exact_sets_order_and_known_digests() -> None:
    environment = _trusted_environment()
    assert environment["sha256"] == (
        "940c693665536e0acc578b9f14551e4c23e031e916a3bfc6c92adc09e4386218"
    )
    validate_trusted_environment(environment)
    validate_trusted_environment(environment, ["src/Button.tsx"])
    validate_no_trusted_shadowing(
        [{"source_kind": "module", "source_name": "app-local", "operation": "declare"}],
        environment,
    )
    with pytest.raises(AssertionError):
        validate_no_trusted_shadowing(
            [{"source_kind": "global", "source_name": "JSX", "operation": "augment"}],
            environment,
        )
    _validator("next-trusted-type-environment-v1.schema.json").validate(environment)

    runtime = {
        "schema": "code-structure-viz.next-runtime-manifest/v1",
        "members": [
            {
                "path": "src/code_structure_viz/_next_runtime/adapter.js",
                "size_bytes": 1,
                "sha256": "a" * 64,
                "role": "adapter",
            },
            {
                "path": "src/code_structure_viz/_next_runtime/trusted.d.ts",
                "size_bytes": 1,
                "sha256": "b" * 64,
                "role": "trusted_declaration",
            },
        ],
        "licenses": [
            {
                "ecosystem": "npm",
                "name": "typescript",
                "version": "5.9.2",
                "license_id": "Apache-2.0",
                "source_url": "https://www.npmjs.com/package/typescript",
                "content_or_lock_digest": "c" * 64,
            }
        ],
    }
    runtime["build_input_digest"] = digest(
        {"members": runtime["members"], "licenses": runtime["licenses"]}
    )
    runtime["build_output_digest"] = digest({"members": runtime["members"]})
    assert runtime["build_input_digest"] == (
        "0b8038c5aeb4b5e31fb58bc7f9c43a30a136b71fb903daf0b6e3fe3e83f0d0c5"
    )
    assert runtime["build_output_digest"] == (
        "be7bb162b13397ec6cf9a977a3a2da86e64599a2ee5a1c15238931639cb61eaf"
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
    wrong_digest = copy.deepcopy(environment)
    wrong_digest["sha256"] = "0" * 64
    with pytest.raises(AssertionError):
        validate_trusted_environment(wrong_digest)
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
        b".. prop/import/export member\n"
        b"--> static_import|literal_dynamic_import\n"
        b"..> jsx_render|component_wrap\n"
        b"marker=client_entry|router_context=<context>|client_dependency|server_candidate|unknown\n"
        b"marker=partial_safe\n"
        b"endlegend\n"
        b'package "P:next:project:'
        b'0000000000000000000000000000000000000000000000000000000000000000" '
        b"as N_P_0000000000000000000000000000000000000000000000000000000000000000 {\n"
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
    rich_output = render_plantuml(rich)
    validate_plantuml_contract(rich_output, rich)
    assert b"literal_dynamic_import" in rich_output
    assert b'cloud "external:react#lazy" as X_' in rich_output


def test_compatibility_descriptor_known_answer_is_content_independent() -> None:
    descriptor = _descriptor()
    validate_compatibility_descriptor(descriptor)
    assert descriptor["compatibility_id"] == (
        "08e1262b7b6e8dddab2e31afc1ba36e868d1021c5cd147eaed17c779bf63f9da"
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
        "plantuml-control-escape",
        "plantuml-complete-non-empty",
        "plantuml-partial-safe",
        "plantuml-external-dynamic",
        "nfc-canonical-digest",
        "compatibility-known-answer",
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
        "unsafe-trusted-path",
        "runtime-http-url",
        "compatibility-mismatch",
        "plantuml-injection",
    } <= set(fixture["negative"])
