import json
import subprocess
import sys
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import pytest
from jsonschema import Draft202012Validator, ValidationError  # type: ignore[import-untyped]
from referencing import Registry, Resource

from code_structure_viz.adapters.sqlalchemy.model import (
    SqlAlchemyCoverage,
    SqlAlchemyRedactionSummary,
    SqlAlchemySnapshot,
)
from code_structure_viz.adapters.sqlalchemy.semantic_json import render_semantic_snapshot
from code_structure_viz.source.source_view import SourceView
from tests.contracts.ecmascript_unicode_15_0 import TABLE_DIGEST
from tests.contracts.next_reference_validation import (
    process_launch_local_attestation_digest,
    process_launch_stable_fingerprint,
)
from tests.helpers.acceptance import (
    initialize_fixture_repository,
    initialize_repository,
    run_cli,
)
from tests.helpers.diff import create_two_commit_repository_from_files, run_diff_cli
from tests.helpers.sqlalchemy_snapshot import (
    initialize_sqlalchemy_fixture_repository,
)
from tests.helpers.sqlalchemy_snapshot import (
    run_snapshot_cli as run_sqlalchemy_snapshot_cli,
)

ROOT = Path(__file__).resolve().parents[2]
SEMANTIC_GOLDEN_ROOT = ROOT / "tests" / "golden" / "python_snapshot"


def _schema(name: str) -> dict[str, object]:
    return cast(
        dict[str, object],
        json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8")),
    )


def _validator(name: str) -> Draft202012Validator:
    resources = {
        "next-compatibility-v1",
        "diagnostic-v1",
        "next-adapter-request-v1",
        "next-adapter-response-v1",
        "next-config-v1",
        "next-domain-manifest-v1",
        "next-process-launch-v1",
        "next-process-launch-observation-v1",
        "next-export-graph-raw-v1",
        "next-limits-v1",
        "next-semantic-v1",
        "next-source-plan-v1",
        "next-path-v1",
        "next-root-or-path-v1",
        "next-run-context-v1",
        "next-provenance-v1",
        "next-package-applicability-v1",
        "next-applicability-decision-v1",
        "next-trusted-type-environment-v1",
    }
    registry = Registry()
    for resource_name in resources:
        registry = registry.with_resource(
            f"urn:code-structure-viz:schema:{resource_name}",
            Resource.from_contents(_schema(f"{resource_name}.schema.json")),
        )
    return Draft202012Validator(_schema(name), registry=registry)


@pytest.mark.parametrize(
    "name",
    [
        "diagnostic-v1.schema.json",
        "next-compatibility-v1.schema.json",
        "file-change-set-v1.schema.json",
        "next-adapter-request-v1.schema.json",
        "next-adapter-response-v1.schema.json",
        "next-config-v1.schema.json",
        "next-domain-manifest-v1.schema.json",
        "next-process-launch-v1.schema.json",
        "next-process-launch-observation-v1.schema.json",
        "next-export-graph-raw-v1.schema.json",
        "next-limits-v1.schema.json",
        "next-runtime-manifest-v1.schema.json",
        "next-source-plan-v1.schema.json",
        "next-path-v1.schema.json",
        "next-root-or-path-v1.schema.json",
        "next-run-context-v1.schema.json",
        "next-provenance-v1.schema.json",
        "next-package-applicability-v1.schema.json",
        "next-applicability-decision-v1.schema.json",
        "next-semantic-v1.schema.json",
        "next-trusted-type-environment-v1.schema.json",
        "run-manifest-v1.schema.json",
        "run-summary-v1.schema.json",
        "semantic-v1.schema.json",
        "stdout-result-v1.schema.json",
    ],
)
def test_checked_in_schema_is_valid_and_closed(name: str) -> None:
    schema = _schema(name)

    Draft202012Validator.check_schema(schema)
    assert schema["additionalProperties"] is False


def test_next_path_schema_rejects_fragment_marker() -> None:
    validator = _validator("next-path-v1.schema.json")
    with pytest.raises(ValidationError):
        validator.validate("src/Button#shadow.tsx")


def test_next_diagnostic_catalog_is_unique_and_closed() -> None:
    catalog = _schema("next-diagnostic-catalog-v1.json")
    assert catalog["schema"] == "code-structure-viz.next-diagnostic-catalog/v1"
    entries = cast(list[dict[str, object]], catalog["entries"])
    codes = [entry["code"] for entry in entries]
    assert len(codes) == len(set(codes))
    assert {
        "CSV-NEXT-LIMIT-001",
        "CSV-NEXT-LIMIT-002",
        "CSV-NEXT-LIMIT-003",
        "CSV-NEXT-LIMIT-004",
        "CSV-NEXT-LIMIT-005",
    } <= set(codes)
    assert all(
        set(entry) == {"code", "severity", "recoverable", "message", "ref_permission", "outcome"}
        for entry in entries
    )
    assert all(
        entry["ref_permission"] in {"none", "path", "symbol", "path_or_symbol"} for entry in entries
    )


def _next_limits(*, max_entities: int = 500) -> dict[str, int]:
    return {
        "max_entities": max_entities,
        "max_files": 20000,
        "max_file_bytes": 4194304,
        "max_decoded_bytes": 67108864,
        "max_encoded_stdin_bytes": 100663296,
        "max_json_nesting": 64,
        "max_json_string_bytes": 8388608,
        "max_array_items": 100000,
        "max_total_array_items": 100000,
        "max_collection_items": 20000,
        "max_model_records": 10000,
        "max_stdout_bytes": 16777216,
        "max_adapter_response_bytes": 16777216,
        "max_selected_stdout_bytes": 16777216,
        "max_stderr_bytes": 65536,
        "max_adapter_stderr_capture_bytes": 65536,
        "max_adapter_stdout_capture_bytes": 16777216,
        "timeout_seconds": 60,
        "v8_old_space_mib": 512,
        "max_type_depth": 16,
        "max_type_nodes_per_prop": 512,
        "max_union_members": 64,
        "max_intersection_members": 64,
        "max_nested_properties": 256,
        "max_signatures_per_component": 16,
        "max_flow_visits": 10000,
        "max_alias_edges": 64,
    }


def _next_source_plan(config_project: Mapping[str, object]) -> dict[str, object]:
    return {
        "schema": "code-structure-viz.source-acquisition-plan/next/v1",
        "version": "1",
        "projects": [config_project],
        "resolved_control_paths": [
            {"project_root": ".", "path": "package.json"},
            {"project_root": ".", "path": "tsconfig.json"},
            {"project_root": ".", "path": "jsconfig.json"},
        ],
        "local_extends": [],
        "file_role_map": [],
        "program_suffixes": [".js", ".jsx", ".ts", ".tsx"],
        "context_suffixes": [".d.ts"],
        "hard_exclusions": [".git", "node_modules", ".next", "out", "dist", "build", "coverage"],
        "limits": _next_limits(),
        "trusted_environment_digest": "7" * 64,
    }


def _next_coverage() -> dict[str, object]:
    return {
        "counts": {
            "projects": 0,
            "files": 0,
            "modules": 0,
            "components": 0,
            "members": 0,
            "relations": 0,
            "facts": 0,
            "internal_entities": 0,
            "discovered": 0,
            "published": 0,
            "excluded": 0,
            "failed": 0,
        },
        "failed_files": [],
        "affected_ids": [],
        "taint_frontier": [],
        "opaque_reason_counts": {},
        "unknown_relation_count": 0,
        "correlation_losses": [],
        "non_component_value_export_count": 0,
        "type_only_export_count": 0,
        "target_completeness": [],
    }


def _next_compatibility_descriptor() -> dict[str, object]:
    return {
        "schema": "code-structure-viz.next-semantic-compatibility/v1",
        "semantic_schema": "code-structure-viz.semantic/v1",
        "identity_versions": {
            "project": 1,
            "file": 1,
            "module": 1,
            "component": 1,
            "member": 1,
            "relation": 1,
            "fact": 1,
            "props_ir": 1,
        },
        "algorithm_versions": {
            "recognition": 1,
            "export": 1,
            "props": 1,
            "relation": 1,
            "fact": 1,
            "boundary": 1,
            "identifier_unicode": "ecma-unicode-15.0",
            "identifier_unicode_table_digest": TABLE_DIGEST,
        },
        "semantic_profile_id": "next-trusted-profile-v1",
        "compatibility_id": "a" * 64,
    }


def _next_project() -> dict[str, object]:
    return {
        "kind": "project",
        "id": "next:project:" + "1" * 64,
        "root": ".",
        "source_roots": ["src"],
        "config_path": "tsconfig.json",
        "config_digest": "2" * 64,
        "compiler_options": {
            "allow_js": True,
            "check_js": False,
            "jsx": "preserve",
            "module": "esnext",
            "module_resolution": "bundler",
            "base_url": None,
            "paths": {},
        },
        "file_ids": [],
    }


def _next_trusted_environment() -> dict[str, object]:
    return {
        "schema": "code-structure-viz.next-trusted-types/v1",
        "environment_version": "1",
        "semantic_profile_id": "next-trusted-profile-v1",
        "typescript_version": "5.9.2",
        "identifier_unicode_table_digest": TABLE_DIGEST,
        "license_inventory_digest": (
            "473c908d234c02e497c4f0ff5bcc7a626dd8b488e487ec3c7f7202ae1c9e1ea8"
        ),
        "files": [
            {
                "physical_path": "tests/fixtures/next_trusted_profile/jsx-runtime.d.ts",
                "virtual_path": "/.code-structure-viz/trusted/v1/jsx-runtime.d.ts",
                "size_bytes": 1,
                "sha256": "1" * 64,
                "license_id": "MIT",
            },
            {
                "physical_path": "tests/fixtures/next_trusted_profile/lib.d.ts",
                "virtual_path": "/.code-structure-viz/trusted/v1/lib.d.ts",
                "size_bytes": 1,
                "sha256": "2" * 64,
                "license_id": "Apache-2.0",
            },
            {
                "physical_path": "tests/fixtures/next_trusted_profile/next-dynamic.d.ts",
                "virtual_path": "/.code-structure-viz/trusted/v1/next-dynamic.d.ts",
                "size_bytes": 1,
                "sha256": "3" * 64,
                "license_id": "MIT",
            },
            {
                "physical_path": "tests/fixtures/next_trusted_profile/react.d.ts",
                "virtual_path": "/.code-structure-viz/trusted/v1/react.d.ts",
                "size_bytes": 1,
                "sha256": "4" * 64,
                "license_id": "MIT",
            },
        ],
        "reserved_module_specifiers": [
            "react",
            "react/jsx-runtime",
            "react/jsx-dev-runtime",
            "next/dynamic",
        ],
        "reserved_global_names": ["Array", "JSX", "ReadonlyArray"],
        "anti_shadowing_witness": [
            {"source_kind": "module", "source_name": "react", "decision": "reserved"},
            {"source_kind": "module", "source_name": "react/jsx-runtime", "decision": "reserved"},
            {
                "source_kind": "module",
                "source_name": "react/jsx-dev-runtime",
                "decision": "reserved",
            },
            {"source_kind": "module", "source_name": "next/dynamic", "decision": "reserved"},
            {"source_kind": "global", "source_name": "Array", "decision": "reserved"},
            {"source_kind": "global", "source_name": "JSX", "decision": "reserved"},
            {"source_kind": "global", "source_name": "ReadonlyArray", "decision": "reserved"},
        ],
        "certified_symbols": [
            {
                "source_kind": "global",
                "source_name": "Array",
                "export_path": ["flatMap"],
                "declaration_sha256": "2" * 64,
                "symbol_kind": "method",
                "signature_digest": "5" * 64,
            },
            {
                "source_kind": "global",
                "source_name": "Array",
                "export_path": ["map"],
                "declaration_sha256": "2" * 64,
                "symbol_kind": "method",
                "signature_digest": "6" * 64,
            },
            {
                "source_kind": "global",
                "source_name": "JSX",
                "export_path": ["Element"],
                "declaration_sha256": "1" * 64,
                "symbol_kind": "interface",
                "signature_digest": "7" * 64,
            },
            {
                "source_kind": "global",
                "source_name": "ReadonlyArray",
                "export_path": ["flatMap"],
                "declaration_sha256": "2" * 64,
                "symbol_kind": "method",
                "signature_digest": "8" * 64,
            },
            {
                "source_kind": "global",
                "source_name": "ReadonlyArray",
                "export_path": ["map"],
                "declaration_sha256": "2" * 64,
                "symbol_kind": "method",
                "signature_digest": "9" * 64,
            },
            {
                "source_kind": "module",
                "source_name": "next/dynamic",
                "export_path": ["default"],
                "declaration_sha256": "3" * 64,
                "symbol_kind": "function",
                "signature_digest": "3" * 64,
            },
            {
                "source_kind": "module",
                "source_name": "react",
                "export_path": ["Component"],
                "declaration_sha256": "4" * 64,
                "symbol_kind": "class",
                "signature_digest": "a" * 64,
            },
            {
                "source_kind": "module",
                "source_name": "react",
                "export_path": ["createElement"],
                "declaration_sha256": "4" * 64,
                "symbol_kind": "function",
                "signature_digest": "b" * 64,
            },
            {
                "source_kind": "module",
                "source_name": "react",
                "export_path": ["forwardRef"],
                "declaration_sha256": "4" * 64,
                "symbol_kind": "function",
                "signature_digest": "c" * 64,
            },
            {
                "source_kind": "module",
                "source_name": "react",
                "export_path": ["lazy"],
                "declaration_sha256": "4" * 64,
                "symbol_kind": "function",
                "signature_digest": "d" * 64,
            },
            {
                "source_kind": "module",
                "source_name": "react",
                "export_path": ["memo"],
                "declaration_sha256": "4" * 64,
                "symbol_kind": "function",
                "signature_digest": "e" * 64,
            },
            {
                "source_kind": "module",
                "source_name": "react/jsx-runtime",
                "export_path": ["Fragment"],
                "declaration_sha256": "1" * 64,
                "symbol_kind": "interface",
                "signature_digest": "f" * 64,
            },
            {
                "source_kind": "module",
                "source_name": "react/jsx-runtime",
                "export_path": ["jsx"],
                "declaration_sha256": "1" * 64,
                "symbol_kind": "function",
                "signature_digest": "1" * 64,
            },
            {
                "source_kind": "module",
                "source_name": "react/jsx-runtime",
                "export_path": ["jsxs"],
                "declaration_sha256": "1" * 64,
                "symbol_kind": "function",
                "signature_digest": "2" * 64,
            },
        ],
        "sha256": "7" * 64,
    }


def test_next_semantic_and_domain_manifest_contracts_resolve_and_reject_extras() -> None:
    identity_versions = {
        "project": 1,
        "file": 1,
        "module": 1,
        "component": 1,
        "member": 1,
        "relation": 1,
        "fact": 1,
        "props_ir": 1,
    }
    config_project = {
        "root": ".",
        "source_roots": ["src"],
        "config_path": "tsconfig.json",
        "compiler_options": {
            "allow_js": False,
            "check_js": False,
            "jsx": "preserve",
            "module": "esnext",
            "module_resolution": "bundler",
            "base_url": None,
            "paths": {},
        },
    }
    semantic: dict[str, Any] = {
        "type": "semantic_snapshot",
        "schema": "code-structure-viz.semantic/v1",
        "domain": "next",
        "document_kind": "snapshot",
        "status": "complete",
        "semantic_compatibility_id": "a" * 64,
        "compatibility_descriptor": _next_compatibility_descriptor(),
        "identity_versions": identity_versions,
        "source": {
            "schema": "code-structure-viz.source-view/v1",
            "kind": "working-tree",
            "head_commit": None,
            "fingerprint": "b" * 64,
            "file_count": 0,
        },
        "request": {
            "schema": "code-structure-viz.next-snapshot-request/v1",
            "projects": [config_project],
            "targets": [],
            "upstream_depth": 1,
            "downstream_depth": 1,
            "formats": ["semantic-json"],
            "limits": _next_limits(),
            "trusted_environment_digest": "7" * 64,
            "source_plan": _next_source_plan(config_project),
            "source_plan_digest": "c" * 64,
            "domain_config_digest": "d" * 64,
            "run_fingerprint": "e" * 64,
        },
        "coverage": _next_coverage(),
        "projects": [_next_project()],
        "files": [],
        "entities": [],
        "members": [],
        "relations": [],
        "facts": [],
        "diagnostics": [],
    }
    semantic_validator = _validator("next-semantic-v1.schema.json")
    semantic_validator.validate(semantic)
    with pytest.raises(ValidationError):
        semantic_validator.validate({**semantic, "absolute_path": "/private/secret"})

    domain: dict[str, Any] = {
        "domain": "next",
        "request_independent": False,
        "status": "complete",
        "payload_available": True,
        "entity_count": 0,
        "semantic_compatibility_id": "a" * 64,
        "compatibility_descriptor": _next_compatibility_descriptor(),
        "identity_versions": identity_versions,
        "budget": {
            "name": "max_entities",
            "requested": None,
            "resolved": 500,
            "actual": 0,
            "source": "builtin",
            "outcome": "complete",
        },
        "run_context": {
            "requested_formats": ["semantic-json"],
            "budget_requested": None,
            "budget_resolved": 500,
            "budget_source": "builtin",
            "stdout_selector": "next:semantic-json",
        },
        "source_plan_digest": "c" * 64,
        "domain_config_digest": "d" * 64,
        "run_fingerprint": "e" * 64,
        "source": {
            "schema": "code-structure-viz.source-view/v1",
            "kind": "working-tree",
            "head_commit": None,
            "fingerprint": "b" * 64,
            "file_count": 0,
        },
        "request": {
            "schema": "code-structure-viz.next-snapshot-request/v1",
            "projects": [config_project],
            "targets": [],
            "upstream_depth": 1,
            "downstream_depth": 1,
            "formats": ["semantic-json"],
            "limits": _next_limits(),
            "trusted_environment_digest": "7" * 64,
            "source_plan": _next_source_plan(config_project),
            "source_plan_digest": "c" * 64,
            "domain_config_digest": "d" * 64,
        },
        "config": {
            "schema": "code-structure-viz.domain-config/next/v1",
            "request_independent": False,
            "projects": [config_project],
            "targets": [],
            "upstream_depth": 1,
            "downstream_depth": 1,
            "formats": ["semantic-json"],
            "limits": _next_limits(),
            "trusted_environment_digest": "7" * 64,
            "source_plan": _next_source_plan(config_project),
            "source_plan_digest": "c" * 64,
            "domain_config_digest": "d" * 64,
        },
        "projects": [_next_project()],
        "targets": [],
        "formats": ["semantic-json"],
        "toolchain": {
            "node": {"status": "available", "version": "22.14.0", "failure_kind": None},
            "node_version": "22.14.0",
            "typescript_version": "5.9.2",
            "adapter_version": "1.0.0",
            "protocol": "code-structure-viz.next-adapter/v1",
        },
        "trusted_environment": _next_trusted_environment(),
        "limits": _next_limits(),
        "coverage": _next_coverage(),
        "artifact_paths": ["next.snapshot.semantic.json"],
        "diagnostics": [],
    }
    domain_validator = _validator("next-domain-manifest-v1.schema.json")
    domain_validator.validate(domain)
    with pytest.raises(ValidationError):
        domain_validator.validate({**domain, "incomplete_kind": "partial_safe"})

    # ``.`` is the explicit project/source-root sentinel.  The same shared
    # root-or-path schema must accept it through every nested surface that
    # carries SourceAcquisitionPlan/Config/Request/Semantic project roots.
    root_semantic = deepcopy(semantic)
    root_semantic["projects"][0]["source_roots"] = ["."]
    root_semantic["request"]["projects"][0]["source_roots"] = ["."]
    root_semantic["request"]["source_plan"]["projects"][0]["source_roots"] = ["."]
    semantic_validator.validate(root_semantic)
    root_domain = deepcopy(domain)
    for projection in (
        root_domain["projects"],
        root_domain["request"]["projects"],
        root_domain["config"]["projects"],
        root_domain["config"]["source_plan"]["projects"],
    ):
        projection[0]["source_roots"] = ["."]
    domain_validator.validate(root_domain)
    for validator, value in (
        (semantic_validator, root_semantic),
        (domain_validator, root_domain),
    ):
        invalid_root = deepcopy(value)
        if validator is semantic_validator:
            surfaces: tuple[Any, ...] = (
                invalid_root["projects"],
                invalid_root["request"]["projects"],
                invalid_root["request"]["source_plan"]["projects"],
            )
        else:
            surfaces = (
                invalid_root["projects"],
                invalid_root["request"]["projects"],
                invalid_root["config"]["projects"],
                invalid_root["config"]["source_plan"]["projects"],
            )
        for projection in surfaces:
            projection[0]["source_roots"] = ["./src"]
        with pytest.raises(ValidationError):
            validator.validate(invalid_root)

    config_validator = _validator("next-config-v1.schema.json")
    root_config = deepcopy(domain["config"])
    root_config["projects"][0]["source_roots"] = ["."]
    root_config["source_plan"]["projects"][0]["source_roots"] = ["."]
    config_validator.validate(root_config)
    source_plan_validator = _validator("next-source-plan-v1.schema.json")
    root_source_plan = deepcopy(domain["config"]["source_plan"])
    root_source_plan["projects"][0]["source_roots"] = ["."]
    source_plan_validator.validate(root_source_plan)

    adapter_request_validator = _validator("next-adapter-request-v1.schema.json")
    adapter_project = _next_project()
    adapter_project["source_roots"] = ["."]
    adapter_request: dict[str, Any] = {
        "schema": "code-structure-viz.next-adapter-request/v1",
        "protocol": "code-structure-viz.next-adapter/v1",
        "request_id": "a" * 64,
        "adapter_version": "1.0.0",
        "trusted_type_environment": {
            "schema": "code-structure-viz.next-trusted-types/v1",
            "environment_version": "1",
            "semantic_profile_id": "next-trusted-profile-v1",
            "sha256": "7" * 64,
        },
        "projects": [adapter_project],
        "files": [],
        "targets": [],
        "limits": _next_limits(),
        "run_context": {
            "requested_formats": ["semantic-json"],
            "budget_requested": None,
            "budget_resolved": 500,
            "budget_source": "builtin",
            "stdout_selector": "next:semantic-json",
        },
    }
    adapter_request_validator.validate(adapter_request)
    for validator, value in (
        (config_validator, root_config),
        (source_plan_validator, root_source_plan),
        (adapter_request_validator, adapter_request),
    ):
        invalid_root = deepcopy(value)
        project_paths = (
            (invalid_root["projects"], invalid_root["source_plan"]["projects"])
            if validator is config_validator
            else (invalid_root["projects"],)
        )
        for projects in project_paths:
            projects[0]["source_roots"] = ["./src"]
        with pytest.raises(ValidationError):
            validator.validate(invalid_root)

    for validator, value in (
        (semantic_validator, semantic),
        (domain_validator, domain),
    ):
        for length in (40, 64):
            candidate = deepcopy(value)
            candidate["source"]["head_commit"] = "a" * length
            validator.validate(candidate)
        for length in (39, 41, 63, 65):
            candidate = deepcopy(value)
            candidate["source"]["head_commit"] = "a" * length
            with pytest.raises(ValidationError):
                validator.validate(candidate)


def test_diagnostic_schema_accepts_exact_vector_and_rejects_extra_field() -> None:
    value = {
        "type": "diagnostic",
        "schema": "code-structure-viz.diagnostic/v1",
        "code": "CSV-PY-003",
        "severity": "error",
        "domain": "python",
        "path": "src/broken.py",
        "symbol": None,
        "line": 7,
        "recoverable": True,
        "message": "Python source could not be parsed with the v1 Python 3.12 grammar.",
    }
    _validator("diagnostic-v1.schema.json").validate(value)

    with pytest.raises(ValidationError):
        _validator("diagnostic-v1.schema.json").validate({**value, "source": "secret"})


@pytest.mark.parametrize(
    "code_message",
    (
        (
            "CSV-DIFF-001",
            "Comparison endpoint or implicit base could not be resolved safely.",
        ),
        (
            "CSV-DIFF-002",
            "Changed path count exceeds the resolved comparison limit.",
        ),
        (
            "CSV-DIFF-003",
            "Git changed-path metadata could not be read safely.",
        ),
    ),
)
def test_diagnostic_schema_accepts_diff_diagnostic_vectors(
    code_message: tuple[str, str],
) -> None:
    code, message = code_message
    _validator("diagnostic-v1.schema.json").validate(
        {
            "type": "diagnostic",
            "schema": "code-structure-viz.diagnostic/v1",
            "code": code,
            "severity": "error",
            "domain": None,
            "path": None,
            "symbol": None,
            "line": None,
            "recoverable": False,
            "message": message,
        }
    )


@pytest.mark.parametrize(
    ("name", "value"),
    [
        (
            "run-summary-v1.schema.json",
            {
                "type": "run_summary",
                "schema": "code-structure-viz.run-summary/v1",
                "run_status": "fatal",
                "exit_code": 1,
                "domains": [],
                "manifest": None,
            },
        ),
        (
            "run-summary-v1.schema.json",
            {
                "type": "run_summary",
                "schema": "code-structure-viz.run-summary/v1",
                "run_status": "usage",
                "exit_code": 2,
                "domains": [],
                "manifest": None,
            },
        ),
        (
            "run-summary-v1.schema.json",
            {
                "type": "run_summary",
                "schema": "code-structure-viz.run-summary/v1",
                "run_status": "complete",
                "exit_code": 0,
                "domains": [{"domain": "sqlalchemy", "status": "complete"}],
                "manifest": "run-manifest.json",
            },
        ),
        (
            "stdout-result-v1.schema.json",
            {
                "type": "stdout_result",
                "schema": "code-structure-viz.stdout-result/v1",
                "selector": "python:semantic-json",
                "availability": False,
                "domain_status": "not_applicable",
                "stable_reason": "domain_not_applicable",
                "artifact": None,
            },
        ),
        (
            "stdout-result-v1.schema.json",
            {
                "type": "stdout_result",
                "schema": "code-structure-viz.stdout-result/v1",
                "selector": "sqlalchemy:plantuml",
                "availability": False,
                "domain_status": "incomplete",
                "stable_reason": "domain_payload_unavailable",
                "artifact": None,
            },
        ),
        (
            "stdout-result-v1.schema.json",
            {
                "type": "stdout_result",
                "schema": "code-structure-viz.stdout-result/v1",
                "selector": "manifest",
                "availability": False,
                "run_status": "fatal",
                "stable_reason": "final_manifest_unavailable",
                "artifact": None,
            },
        ),
    ],
)
def test_stream_contract_schema_accepts_closed_positive_vectors(
    name: str, value: dict[str, object]
) -> None:
    _validator(name).validate(value)


def test_round18_stdout_union_rejects_partial_discriminator_and_wrong_next_descriptor() -> None:
    validator = _validator("stdout-result-v1.schema.json")
    artifact = {
        "path": "next.snapshot.semantic.json",
        "domain": "next",
        "format": "semantic-json",
        "media_type": "application/json",
        "size_bytes": 1,
        "sha256": "a" * 64,
    }
    complete = {
        "type": "stdout_result",
        "schema": "code-structure-viz.stdout-result/v1",
        "selector": "next:semantic-json",
        "availability": True,
        "domain_status": "complete",
        "stable_reason": "published_artifact",
        "artifact": artifact,
    }
    validator.validate(complete)
    for field, value in (
        ("run_status", "fatal"),
        ("incomplete_kind", "partial_safe"),
        ("selected_stdout_unavailable", True),
    ):
        with pytest.raises(ValidationError):
            validator.validate({**complete, field: value})
    with pytest.raises(ValidationError):
        validator.validate(
            {
                **complete,
                "artifact": {**artifact, "path": "arbitrary.json"},
            }
        )
    unavailable = {
        **complete,
        "availability": False,
        "stable_reason": "selected_artifact_unavailable",
        "selected_stdout_unavailable": True,
    }
    validator.validate(unavailable)


def test_round18_target_reason_is_required_and_forbidden_for_other_diagnostics() -> None:
    validator = _validator("diagnostic-v1.schema.json")
    target = {
        "type": "diagnostic",
        "schema": "code-structure-viz.diagnostic/v1",
        "code": "CSV-NEXT-TARGET-001",
        "severity": "error",
        "domain": "next",
        "path": "src/Missing.tsx",
        "symbol": None,
        "line": None,
        "recoverable": False,
        "message": "An explicit Next.js target cannot be resolved uniquely.",
        "outcome": "payload_unavailable",
        "ref_permission": "path_or_symbol",
        "reason": "missing",
    }
    validator.validate(target)
    with pytest.raises(ValidationError):
        validator.validate({key: value for key, value in target.items() if key != "reason"})
    non_target = {
        **target,
        "code": "CSV-NEXT-CONFIG-001",
        "message": "Configuration file could not be read.",
    }
    with pytest.raises(ValidationError):
        validator.validate(non_target)


def test_round19_process_observation_is_fixture_or_supported_os_production() -> None:
    validator = _validator("next-process-launch-observation-v1.schema.json")
    fixture = {
        "schema": "code-structure-viz.next-process-launch-observation/v1",
        "version": 1,
        "kind": "fixture",
        "host_os": "fixture",
        "node_status": "available",
        "fixture_id": "reference-process-v1",
        "identity_token": "fixture-node-identity",
        "spawn_primitive": "recorded-fixture",
        "toctou_failure_point": "not-exercised",
        "argv": ["/usr/local/bin/node", "/.code-structure-viz/next-adapter.mjs"],
        "shell": False,
        "process_group": {"create": True, "terminate_scope": "group", "wait_after_terminate": True},
        "cwd": "/.code-structure-viz/private-run",
        "env_allowlist": {"LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC"},
        "denied_env": ["NODE_OPTIONS", "NODE_PATH", "PATH", "npm_config_user_config"],
        "stdio": {"stdin": "pipe", "stdout": "pipe", "stderr": "pipe"},
        "fd_inheritance": {"close_fds": True, "allowed": [0, 1, 2]},
    }
    fixture["stable_toolchain_fingerprint"] = process_launch_stable_fingerprint(fixture)
    fixture["local_process_attestation_digest"] = process_launch_local_attestation_digest(fixture)
    validator.validate(fixture)
    identity = {
        "realpath": "/usr/local/bin/node",
        "sha256": "1" * 64,
        "version": "22.14.0",
        "device": 1,
        "inode": 2,
    }
    production = {
        "schema": "code-structure-viz.next-process-launch-observation/v1",
        "version": 1,
        "kind": "production",
        "host_os": "linux",
        "node_status": "available",
        "node_realpath": "/usr/local/bin/node",
        "node_sha256": "1" * 64,
        "node_version": "22.14.0",
        "file_identity_at_hash": identity,
        "file_identity_at_spawn": identity,
        "verified_open_handle": {
            "kind": "fd",
            "number": 7,
            "cloexec": True,
            "retained_through_spawn": True,
        },
        "spawn_primitive": "linux-posix-spawn-verified-fd",
        "post_spawn_identity_check": {
            "performed": True,
            "result": "equal",
            "identity_at_spawn": identity,
        },
        "fd_lifecycle": {
            "opened_before_hash": True,
            "retained_through_spawn": True,
            "inherited_by_child": False,
            "closed_after_spawn_result": True,
        },
        "toctou_failure_point": "none",
        "argv": ["/usr/local/bin/node", "/.code-structure-viz/next-adapter.mjs"],
        "shell": False,
        "process_group": {"create": True, "terminate_scope": "group", "wait_after_terminate": True},
        "cwd": "/.code-structure-viz/private-run",
        "env_allowlist": {"LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC"},
        "denied_env": ["NODE_OPTIONS", "NODE_PATH", "PATH", "npm_config_user_config"],
        "stdio": {"stdin": "pipe", "stdout": "pipe", "stderr": "pipe"},
        "fd_inheritance": {"close_fds": True, "allowed": [0, 1, 2]},
    }
    production["stable_fingerprint"] = process_launch_stable_fingerprint(production)
    production["stable_toolchain_fingerprint"] = production["stable_fingerprint"]
    production["local_process_attestation_digest"] = process_launch_local_attestation_digest(
        production
    )
    validator.validate(production)
    for mutation in (
        {**production, "host_os": "windows"},
        {**production, "spawn_primitive": "recorded-fixture"},
        {key: value for key, value in production.items() if key != "verified_open_handle"},
        {**fixture, "kind": "production", "host_os": "linux"},
    ):
        with pytest.raises(ValidationError):
            validator.validate(mutation)


def test_round19_stage_provenance_is_closed_and_preserves_observed_prefix() -> None:
    validator = _validator("next-provenance-v1.schema.json")

    def row(observed: bool) -> dict[str, object]:
        return {
            "state": "observed" if observed else "unobserved",
            "value": (
                {
                    "schema": "code-structure-viz.next-observation/v1",
                    "version": 1,
                    "sha256": "a" * 64,
                }
                if observed
                else None
            ),
        }

    independent = {
        "kind": "request_independent",
        "stage": "source_selection",
        "failure_code": "CSV-NEXT-SOURCE-003",
        "observed": {
            "request": row(False),
            "limits": row(True),
            "source_plan": row(True),
            "toolchain": row(False),
            "trusted_environment": row(False),
            "compatibility": row(False),
            "process_launch": row(False),
            "budget": row(False),
        },
    }
    validator.validate(independent)
    validator.validate(
        {
            **independent,
            "stage": "config_validation",
            "failure_code": "CSV-NEXT-CONFIG-001",
            "observed": {key: row(False) for key in independent["observed"]},
        }
    )
    bound = {
        "kind": "request_bound",
        "stage": None,
        "failure_code": None,
        "observed": {key: row(True) for key in independent["observed"]},
    }
    validator.validate(bound)
    independent_observed = cast(dict[str, dict[str, object]], independent["observed"])
    for mutation in (
        {**independent, "observed": {**independent_observed, "request": row(True)}},
        {**independent, "observed": {**independent_observed, "limits": row(False)}},
        {
            **bound,
            "kind": "request_independent",
            "stage": "source_selection",
            "failure_code": "CSV-NEXT-SOURCE-003",
        },
    ):
        with pytest.raises(ValidationError):
            validator.validate(mutation)


def test_semantic_schema_accepts_zero_class_vector_and_rejects_shape_mutations() -> None:
    value = {
        "type": "semantic_snapshot",
        "schema": "code-structure-viz.semantic/v1",
        "domain": "python",
        "document_kind": "snapshot",
        "status": "complete",
        "source": {
            "schema": "code-structure-viz.source-view/v1",
            "kind": "working-tree",
            "head_commit": None,
            "fingerprint": "b" * 64,
            "file_count": 2,
        },
        "request": {"targets": [], "upstream_depth": 1, "downstream_depth": 1},
        "coverage": {
            "candidate_files": 2,
            "parsed_files": 2,
            "failed_files": [],
            "selected_modules": ["app.a", "app.b"],
            "selected_entities": 0,
            "frontier": [],
        },
        "entities": [],
        "members": [],
        "relations": [],
        "diagnostics": [],
    }
    validator = _validator("semantic-v1.schema.json")
    validator.validate(value)

    with pytest.raises(ValidationError):
        validator.validate({**value, "absolute_path": "/private/secret"})
    with pytest.raises(ValidationError):
        validator.validate({**value, "status": "incomplete"})
    with pytest.raises(ValidationError):
        validator.validate({**value, "entities": None})
    with pytest.raises(ValidationError):
        validator.validate({**value, "coverage": {"unexpected": 1}})


def _sqlalchemy_semantic_vector() -> dict[str, Any]:
    table_id = f"sqlalchemy:table:{'1' * 64}"
    target_table_id = f"sqlalchemy:table:{'2' * 64}"
    row_ids = [f"sqlalchemy:row:{index:064x}" for index in range(1, 10)]
    source = {"path": "src/models.py", "range": {"start_line": 1, "end_line": 1}}
    absent = {"present": False, "category": "absent", "redacted": False}
    present = {"present": True, "category": "literal", "redacted": True}
    internal_target = {
        "resolution": "internal",
        "kind": "table",
        "id": target_table_id,
        "schema_name": None,
        "table_name": "target",
        "symbol": None,
        "display_name": "<default>.target",
    }
    source_target = {
        "resolution": "internal",
        "kind": "table",
        "id": table_id,
        "schema_name": None,
        "table_name": "source",
        "symbol": None,
        "display_name": "<default>.source",
    }
    common = {"owner_id": table_id, "name": None, "source": source}
    members = [
        {
            "id": row_ids[0],
            **common,
            "kind": "column",
            "name": "id",
            "type": {
                "category": "integer",
                "name": "sqlalchemy.Integer",
                "parameters": absent,
            },
            "nullable": False,
            "primary_key": True,
            "unique": False,
            "index": False,
            "default": present,
            "server_default": absent,
            "onupdate": absent,
            "server_onupdate": absent,
            "computed": absent,
            "identity": absent,
        },
        {"id": row_ids[1], **common, "kind": "primary_key", "columns": ["id"]},
        {"id": row_ids[2], **common, "kind": "unique", "columns": ["email"]},
        {"id": row_ids[3], **common, "kind": "check", "expression": present},
        {
            "id": row_ids[4],
            **common,
            "kind": "index",
            "unique": False,
            "terms": [
                {"kind": "column", "column_name": "email", "expression": absent},
                {"kind": "expression", "column_name": None, "expression": present},
            ],
        },
        {
            "id": row_ids[5],
            **common,
            "kind": "foreign_key",
            "local_columns": ["target_id"],
            "target": internal_target,
            "target_columns": ["id"],
            "ondelete": absent,
            "onupdate": absent,
        },
        {
            "id": row_ids[6],
            **common,
            "kind": "relationship",
            "name": "target",
            "target": internal_target,
            "cardinality": "scalar",
            "uselist": False,
            "back_populates": None,
            "secondary": None,
            "primaryjoin": present,
            "secondaryjoin": absent,
            "order_by": absent,
            "foreign_keys": absent,
        },
        {
            "id": row_ids[7],
            **common,
            "kind": "inheritance",
            "target": internal_target,
        },
        {
            "id": row_ids[8],
            **common,
            "owner_id": target_table_id,
            "kind": "association_table",
            "name": "target",
            "source_table": source_target,
            "relationship_target": internal_target,
            "relationship_member_id": row_ids[6],
        },
    ]
    mapping_source = {
        "kind": "declarative_class",
        "module": "models",
        "symbol": "models.Source",
        "source": source,
    }
    return {
        "type": "semantic_snapshot",
        "schema": "code-structure-viz.semantic/v1",
        "domain": "sqlalchemy",
        "document_kind": "snapshot",
        "status": "incomplete",
        "incomplete_kind": "partial_safe",
        "source": {
            "schema": "code-structure-viz.source-view/v1",
            "kind": "working-tree",
            "head_commit": None,
            "fingerprint": "b" * 64,
            "file_count": 1,
        },
        "request": {
            "targets": [{"kind": "class", "value": "models.Source"}],
            "upstream_depth": 1,
            "downstream_depth": 2,
        },
        "coverage": {
            "candidate_files": 1,
            "parsed_files": 1,
            "failed_files": [],
            "evidence_files": ["src/models.py"],
            "selected_modules": ["models"],
            "mapped_classes": 1,
            "association_tables": 1,
            "selected_entities": 2,
            "unknown_declarations": 1,
            "frontier": [
                {
                    "direction": "failure",
                    "kind": "row",
                    "reference": f"sqlalchemy:occurrence:{'a' * 64}",
                    "reason": "unsupported_pattern",
                }
            ],
            "redaction": {
                "rule_version": "code-structure-viz.sqlalchemy-redaction/v1",
                "redacted_values": 4,
            },
        },
        "entities": [
            {
                "id": table_id,
                "kind": "table",
                "schema_name": None,
                "name": "source",
                "display_name": "<default>.source",
                "mapping_kind": "declarative_class",
                "mapping_sources": [mapping_source],
            },
            {
                "id": target_table_id,
                "kind": "table",
                "schema_name": None,
                "name": "target",
                "display_name": "<default>.target",
                "mapping_kind": "table",
                "mapping_sources": [
                    {
                        **mapping_source,
                        "kind": "table",
                        "symbol": "models.target_table",
                    }
                ],
            },
        ],
        "members": members,
        "relations": [
            {
                "id": f"sqlalchemy:relation:{'3' * 64}",
                "kind": "relationship",
                "source_id": table_id,
                "target": internal_target,
                "via_member_id": row_ids[6],
                "role": "target",
                "source": source,
            }
        ],
        "diagnostics": [
            {
                "type": "diagnostic",
                "schema": "code-structure-viz.diagnostic/v1",
                "code": "CSV-SA-009",
                "severity": "warning",
                "domain": "sqlalchemy",
                "path": "src/models.py",
                "symbol": f"sqlalchemy:occurrence:{'a' * 64}",
                "line": 1,
                "recoverable": True,
                "message": "SQLAlchemy row declaration could not be represented safely.",
            }
        ],
    }


def test_semantic_schema_accepts_closed_sqlalchemy_snapshot_variants() -> None:
    validator = _validator("semantic-v1.schema.json")
    partial = _sqlalchemy_semantic_vector()
    validator.validate(partial)

    complete = deepcopy(partial)
    complete["status"] = "complete"
    complete.pop("incomplete_kind")
    complete["diagnostics"] = []
    complete["coverage"]["unknown_declarations"] = 0
    complete["coverage"]["frontier"] = []
    validator.validate(complete)

    complete_with_depth_frontier = deepcopy(complete)
    complete_with_depth_frontier["coverage"]["frontier"] = [
        {
            "direction": "upstream",
            "kind": "table",
            "reference": complete["entities"][0]["id"],
            "reason": "depth_limit",
        }
    ]
    validator.validate(complete_with_depth_frontier)

    complete_with_failure_frontier = deepcopy(complete_with_depth_frontier)
    complete_with_failure_frontier["coverage"]["frontier"][0].update(
        direction="failure",
        reason="unsupported_pattern",
    )
    with pytest.raises(ValidationError):
        validator.validate(complete_with_failure_frontier)


def test_semantic_schema_rejects_unknown_sqlalchemy_values_from_complete_snapshot() -> None:
    validator = _validator("semantic-v1.schema.json")
    complete = _sqlalchemy_semantic_vector()
    complete["status"] = "complete"
    complete.pop("incomplete_kind")
    complete["diagnostics"] = []
    complete["coverage"]["unknown_declarations"] = 0
    complete["coverage"]["frontier"] = []

    mutations = []
    unknown_type = deepcopy(complete)
    unknown_type["members"][0]["type"] = {
        "category": "unknown",
        "name": None,
        "parameters": {"present": False, "category": "absent", "redacted": False},
    }
    mutations.append(unknown_type)
    unknown_descriptor = deepcopy(complete)
    unknown_descriptor["members"][0]["default"] = {
        "present": True,
        "category": "unknown",
        "redacted": True,
    }
    mutations.append(unknown_descriptor)
    unknown_target = deepcopy(complete)
    unknown_target["members"][6]["target"] = {
        "resolution": "unknown",
        "kind": "unknown",
        "id": None,
        "schema_name": None,
        "table_name": None,
        "symbol": None,
        "display_name": "<unknown>",
    }
    mutations.append(unknown_target)
    unknown_cardinality = deepcopy(complete)
    unknown_cardinality["members"][6]["cardinality"] = "unknown"
    mutations.append(unknown_cardinality)

    for mutation in mutations:
        with pytest.raises(ValidationError):
            validator.validate(mutation)

    partial = _sqlalchemy_semantic_vector()
    partial["members"][6]["cardinality"] = "unknown"
    validator.validate(partial)


@pytest.mark.parametrize(
    "reference",
    [
        "/private/secret.py",
        "../secret.py",
        "src/../secret.py",
        "https://example.invalid/secret",
        "urn:private:secret.py",
        "C:/secret.py",
        "src\\secret.py",
        "sqlalchemy:binding:models",
        "raw secret",
        "sqlalchemy:table:not-a-digest",
        "module:bad/value",
        "row\u0000secret",
    ],
)
def test_semantic_schema_rejects_unsafe_sqlalchemy_frontier_reference(
    reference: str,
) -> None:
    value = _sqlalchemy_semantic_vector()
    value["coverage"]["frontier"][0]["reference"] = reference

    with pytest.raises(ValidationError):
        _validator("semantic-v1.schema.json").validate(value)


def test_semantic_schema_accepts_actual_sqlalchemy_renderer_bytes() -> None:
    coverage = SqlAlchemyCoverage(
        candidate_files=0,
        parsed_files=0,
        failed_files=(),
        evidence_files=(),
        selected_modules=(),
        mapped_classes=0,
        association_tables=0,
        selected_entities=0,
        unknown_declarations=0,
        frontier=(),
        redaction=SqlAlchemyRedactionSummary.create(0),
    )
    snapshot = SqlAlchemySnapshot((), (), (), coverage, (), partial_safe=False)
    rendered = render_semantic_snapshot(
        snapshot,
        SourceView(None, (), (), "b" * 64),
        (),
        1,
        1,
    )

    _validator("semantic-v1.schema.json").validate(json.loads(rendered))


def test_semantic_schema_rejects_sqlalchemy_cross_domain_and_raw_shape_mutations() -> None:
    validator = _validator("semantic-v1.schema.json")
    value = _sqlalchemy_semantic_vector()

    mutations = []
    sql_diff = deepcopy(value)
    sql_diff["type"] = "semantic_diff"
    sql_diff["document_kind"] = "diff"
    mutations.append(sql_diff)
    diff_field_in_snapshot = deepcopy(value)
    diff_field_in_snapshot["before"] = {
        "kind": "real",
        "domain": "python",
        "schema": "code-structure-viz.semantic/v1",
        "digest": "0" * 64,
        "head_commit": None,
        "file_count": 0,
    }
    mutations.append(diff_field_in_snapshot)
    not_applicable = deepcopy(value)
    not_applicable["status"] = "not_applicable"
    mutations.append(not_applicable)
    unknown_row = deepcopy(value)
    unknown_row["members"][0]["kind"] = "unknown"
    mutations.append(unknown_row)
    cross_kind = deepcopy(value)
    cross_kind["members"][0]["columns"] = ["id"]
    mutations.append(cross_kind)
    raw_expression = deepcopy(value)
    raw_expression["members"][0]["default"]["raw"] = "DO_NOT_LEAK"
    mutations.append(raw_expression)
    internal_column = deepcopy(value)
    internal_column["members"][0]["source"]["range"]["start_utf8_byte_column"] = 0
    mutations.append(internal_column)
    python_diagnostic = deepcopy(value)
    python_diagnostic["diagnostics"][0]["code"] = "CSV-PY-003"
    mutations.append(python_diagnostic)
    wrong_failure = deepcopy(value)
    wrong_failure["coverage"]["failed_files"] = [
        {"path": "src/broken.py", "stage": "parse", "diagnostic_code": "CSV-SA-002"}
    ]
    mutations.append(wrong_failure)
    cross_domain = deepcopy(value)
    cross_domain["domain"] = "python"
    mutations.append(cross_domain)

    for mutation in mutations:
        with pytest.raises(ValidationError):
            validator.validate(mutation)


def test_diagnostic_schema_accepts_closed_sqlalchemy_occurrence_vector() -> None:
    value = _sqlalchemy_semantic_vector()["diagnostics"][0]

    _validator("diagnostic-v1.schema.json").validate(value)

    invalid = deepcopy(value)
    invalid["start_utf8_byte_column"] = 0
    with pytest.raises(ValidationError):
        _validator("diagnostic-v1.schema.json").validate(invalid)


def test_package_root_relative_import_renders_schema_valid_semantic_artifact(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    (repository / "app.py").write_text("from ...foo import Bar\n", encoding="utf-8")
    initialize_repository(repository)
    output = tmp_path / "output"

    result = run_cli(repository, output)

    assert result.returncode == 0
    semantic = json.loads((output / "python.snapshot.semantic.json").read_bytes())
    _validator("semantic-v1.schema.json").validate(semantic)
    relation = semantic["relations"][0]
    assert relation["kind"] == "import_dependency"
    assert relation["target"] == {
        "resolution": "external",
        "kind": "module",
        "id": None,
        "name": "relative-import",
    }


@pytest.mark.parametrize(
    "path",
    sorted(SEMANTIC_GOLDEN_ROOT.glob("*/python.snapshot.semantic.json")),
    ids=lambda path: path.parent.name,
)
def test_semantic_schema_accepts_every_reviewed_golden(path: Path) -> None:
    value = json.loads(path.read_text(encoding="utf-8"))

    _validator("semantic-v1.schema.json").validate(value)


@pytest.mark.parametrize(
    "path",
    sorted(SEMANTIC_GOLDEN_ROOT.glob("*/run-manifest.json")),
    ids=lambda path: path.parent.name,
)
def test_manifest_schema_accepts_every_reviewed_golden(path: Path) -> None:
    value = json.loads(path.read_text(encoding="utf-8"))

    _validator("run-manifest-v1.schema.json").validate(value)


def test_run_manifest_head_commit_accepts_only_full_hash_lengths() -> None:
    value = json.loads(
        (SEMANTIC_GOLDEN_ROOT / "whole" / "run-manifest.json").read_text(encoding="utf-8")
    )
    validator = _validator("run-manifest-v1.schema.json")
    for length in (40, 64):
        candidate = deepcopy(value)
        candidate["source"]["head_commit"] = "a" * length
        validator.validate(candidate)
    for length in (39, 41, 63, 65):
        candidate = deepcopy(value)
        candidate["source"]["head_commit"] = "a" * length
        with pytest.raises(ValidationError):
            validator.validate(candidate)


@pytest.mark.parametrize(
    "path",
    sorted(SEMANTIC_GOLDEN_ROOT.glob("*/stdout.run-summary.jsonl")),
    ids=lambda path: path.parent.name,
)
def test_run_summary_schema_accepts_every_reviewed_golden(path: Path) -> None:
    value = json.loads(path.read_text(encoding="utf-8"))

    _validator("run-summary-v1.schema.json").validate(value)


@pytest.mark.parametrize(
    "path",
    sorted(SEMANTIC_GOLDEN_ROOT.glob("*/stderr.jsonl")),
    ids=lambda path: path.parent.name,
)
def test_diagnostic_schema_accepts_every_reviewed_golden_line(path: Path) -> None:
    validator = _validator("diagnostic-v1.schema.json")

    for line in path.read_text(encoding="utf-8").splitlines():
        validator.validate(json.loads(line))


def test_schemas_accept_captured_complete_and_unavailable_cli_json(
    tmp_path: Path,
) -> None:
    complete_root = tmp_path / "complete"
    repository = initialize_fixture_repository(complete_root, "whole")
    complete_output = complete_root / "output"
    complete = run_cli(repository, complete_output)
    assert complete.returncode == 0

    _validator("run-summary-v1.schema.json").validate(json.loads(complete.stdout))
    _validator("semantic-v1.schema.json").validate(
        json.loads((complete_output / "python.snapshot.semantic.json").read_bytes())
    )
    _validator("run-manifest-v1.schema.json").validate(
        json.loads((complete_output / "run-manifest.json").read_bytes())
    )

    unavailable_root = tmp_path / "unavailable"
    unavailable_root.mkdir()
    unavailable_repository = unavailable_root / "repo"
    initialize_repository(unavailable_repository)
    unavailable_output = unavailable_root / "output"
    unavailable = run_cli(
        unavailable_repository,
        unavailable_output,
        "--target",
        "module:missing.module",
        "--stdout",
        "python:semantic-json",
    )
    assert unavailable.returncode == 3

    _validator("stdout-result-v1.schema.json").validate(json.loads(unavailable.stdout))
    _validator("diagnostic-v1.schema.json").validate(json.loads(unavailable.stderr))
    manifest = json.loads((unavailable_output / "run-manifest.json").read_bytes())
    validator = _validator("run-manifest-v1.schema.json")
    validator.validate(manifest)
    with pytest.raises(ValidationError):
        validator.validate({**manifest, "absolute_path": "/private/secret"})
    with pytest.raises(ValidationError):
        validator.validate({**manifest, "artifacts": [{"path": "run-manifest.json"}]})


def test_manifest_and_stream_schemas_accept_closed_sqlalchemy_cli_output(
    tmp_path: Path,
) -> None:
    repository = initialize_sqlalchemy_fixture_repository(tmp_path, "canonical_model")
    output = tmp_path / "output"

    result = run_sqlalchemy_snapshot_cli(repository, output)

    assert result.returncode == 0, result.stderr
    _validator("run-summary-v1.schema.json").validate(json.loads(result.stdout))
    semantic = json.loads((output / "sqlalchemy.snapshot.semantic.json").read_bytes())
    _validator("semantic-v1.schema.json").validate(semantic)
    manifest = json.loads((output / "run-manifest.json").read_bytes())
    validator = _validator("run-manifest-v1.schema.json")
    validator.validate(manifest)

    diff_coverage = deepcopy(manifest)
    snapshot_coverage = manifest["domains"][0]["coverage"]
    diff_coverage["domains"][0]["coverage"] = {
        "before": deepcopy(snapshot_coverage),
        "after": deepcopy(snapshot_coverage),
    }
    with pytest.raises(ValidationError):
        validator.validate(diff_coverage)

    diff_path = deepcopy(manifest)
    diff_path["domains"][0]["artifact_paths"] = ["sqlalchemy.diff.semantic.json"]
    with pytest.raises(ValidationError):
        validator.validate(diff_path)

    diff_descriptor = deepcopy(manifest)
    diff_descriptor["artifacts"][0]["path"] = "sqlalchemy.diff.semantic.json"
    with pytest.raises(ValidationError):
        validator.validate(diff_descriptor)

    depth_frontier = deepcopy(manifest)
    depth_frontier["domains"][0]["coverage"]["frontier"] = [
        {
            "direction": "downstream",
            "kind": "table",
            "reference": semantic["entities"][0]["id"],
            "reason": "depth_limit",
        }
    ]
    validator.validate(depth_frontier)

    mutations = []
    failure_frontier = deepcopy(depth_frontier)
    failure_frontier["domains"][0]["coverage"]["frontier"][0].update(
        direction="failure",
        reason="unsupported_pattern",
    )
    mutations.append(failure_frontier)
    unsafe_frontier = deepcopy(depth_frontier)
    unsafe_frontier["domains"][0]["coverage"]["frontier"][0]["reference"] = "/private/secret.py"
    mutations.append(unsafe_frontier)
    sql_diff = deepcopy(manifest)
    sql_diff["command"]["name"] = "diff"
    mutations.append(sql_diff)
    python_adapter = deepcopy(manifest)
    python_adapter["adapters"][0] = {
        "domain": "python",
        "name": "python-ast",
        "version": "1",
    }
    mutations.append(python_adapter)
    cross_artifact = deepcopy(manifest)
    cross_artifact["artifacts"][0]["path"] = "python.snapshot.semantic.json"
    mutations.append(cross_artifact)
    wrong_contract = deepcopy(manifest)
    wrong_contract["contracts"]["plantuml"] = "code-structure-viz.plantuml/python/v1"
    mutations.append(wrong_contract)

    for mutation in mutations:
        with pytest.raises(ValidationError):
            validator.validate(mutation)


def test_schemas_accept_captured_complete_diff_json(tmp_path: Path) -> None:
    repository, before, after = create_two_commit_repository_from_files(
        tmp_path,
        before_files={"src/app.py": "class Order:\n    amount: int\n"},
        after_files={"src/app.py": "class Order:\n    amount: str\n"},
    )
    output = tmp_path / "output"
    result = run_diff_cli(repository.resolve(), output, "--from", before, "--to", after)

    assert result.returncode == 0
    _validator("file-change-set-v1.schema.json").validate(
        json.loads((output / "file-changes.json").read_bytes())
    )
    _validator("semantic-v1.schema.json").validate(
        json.loads((output / "python.diff.semantic.json").read_bytes())
    )
    manifest = json.loads((output / "run-manifest.json").read_bytes())
    validator = _validator("run-manifest-v1.schema.json")
    validator.validate(manifest)
    missing_observations = deepcopy(manifest)
    missing_observations["comparison"].pop("candidate_observations")
    with pytest.raises(ValidationError):
        validator.validate(missing_observations)
    before = manifest["comparison"]["resolved"]["before"]
    manifest["comparison"]["candidate_observations"] = [
        {
            "ordinal": 0,
            "origin": "config-upstream",
            "reference": "refs/remotes/upstream/a",
            "resolved_object": before,
            "merge_base": None,
            "disposition": "no-merge-base",
        },
        {
            "ordinal": 1,
            "origin": "config-upstream",
            "reference": "refs/remotes/upstream/b",
            "resolved_object": before,
            "merge_base": before,
            "disposition": "selected",
        },
    ]
    validator.validate(manifest)
    with pytest.raises(ValidationError):
        validator.validate(
            {
                **manifest,
                "comparison": {
                    **manifest["comparison"],
                    "candidate_observations": [
                        {**manifest["comparison"]["candidate_observations"][0], "origin": "other"}
                    ],
                },
            }
        )
    with pytest.raises(ValidationError):
        validator.validate(
            {
                **manifest,
                "comparison": {
                    **manifest["comparison"],
                    "candidate_observations": [
                        {
                            **manifest["comparison"]["candidate_observations"][0],
                            "extra": True,
                        }
                    ],
                },
            }
        )


def test_schemas_accept_captured_sqlalchemy_diff_json(tmp_path: Path) -> None:
    repository, before, after = create_two_commit_repository_from_files(
        tmp_path,
        before_files={
            "src/models.py": (
                "from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column\n"
                "class Base(DeclarativeBase): pass\n"
                "class User(Base):\n"
                "    __tablename__ = 'users'\n"
                "    name: Mapped[str] = mapped_column(nullable=True)\n"
            )
        },
        after_files={
            "src/models.py": (
                "from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column\n"
                "class Base(DeclarativeBase): pass\n"
                "class User(Base):\n"
                "    __tablename__ = 'users'\n"
                "    name: Mapped[str] = mapped_column(nullable=False)\n"
            )
        },
    )
    output = tmp_path / "output"

    result = subprocess.run(
        (
            sys.executable,
            "-m",
            "code_structure_viz",
            "diff",
            "--repo",
            str(repository),
            "--output-dir",
            str(output),
            "--domain",
            "sqlalchemy",
            "--from",
            before,
            "--to",
            after,
        ),
        cwd=repository,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    semantic = json.loads((output / "sqlalchemy.diff.semantic.json").read_bytes())
    semantic_validator = _validator("semantic-v1.schema.json")
    semantic_validator.validate(semantic)
    cross_domain_semantic = deepcopy(semantic)
    cross_domain_semantic["before"]["domain"] = "python"
    with pytest.raises(ValidationError):
        semantic_validator.validate(cross_domain_semantic)

    manifest = json.loads((output / "run-manifest.json").read_bytes())
    manifest_validator = _validator("run-manifest-v1.schema.json")
    manifest_validator.validate(manifest)

    snapshot_coverage = deepcopy(manifest)
    snapshot_coverage["domains"][0]["coverage"] = deepcopy(
        manifest["domains"][0]["coverage"]["before"]
    )
    with pytest.raises(ValidationError):
        manifest_validator.validate(snapshot_coverage)

    snapshot_path = deepcopy(manifest)
    snapshot_path["domains"][0]["artifact_paths"] = ["sqlalchemy.snapshot.semantic.json"]
    with pytest.raises(ValidationError):
        manifest_validator.validate(snapshot_path)

    snapshot_descriptor = deepcopy(manifest)
    semantic_descriptor = next(
        item for item in snapshot_descriptor["artifacts"] if item["format"] == "semantic-json"
    )
    semantic_descriptor["path"] = "sqlalchemy.snapshot.semantic.json"
    with pytest.raises(ValidationError):
        manifest_validator.validate(snapshot_descriptor)

    cross_domain_manifest = deepcopy(manifest)
    cross_domain_manifest["semantic_sides"]["before"]["domain"] = "python"
    with pytest.raises(ValidationError):
        manifest_validator.validate(cross_domain_manifest)


def test_manifest_schema_accepts_incomplete_diff_descriptor_and_comparison_config(
    tmp_path: Path,
) -> None:
    repository, before, after = create_two_commit_repository_from_files(
        tmp_path,
        before_files={
            "src/app.py": ("class Order:\n    amount: int\n\nclass Customer:\n    name: str\n")
        },
        after_files={
            "src/app.py": ("class Order:\n    amount: bytes\n\nclass Customer:\n    name: bytes\n")
        },
    )
    config = tmp_path / "config.toml"
    config.write_text(
        """schema = \"code-structure-viz.config/v1\"
[python]
source_roots = [\"src\"]
include = [\"**/*.py\"]
exclude = []
[traversal]
upstream_depth = 1
downstream_depth = 1
[limits]
max_entities = 500
[comparison]
target_ref = \"refs/heads/main\"
upstream_ref = \"refs/remotes/origin\"
""",
        encoding="utf-8",
    )
    output = tmp_path / "output"

    result = run_diff_cli(
        repository,
        output,
        "--from",
        before,
        "--to",
        after,
        "--config",
        str(config),
        "--max-entities",
        "1",
    )

    assert result.returncode == 3, result.stderr.decode("utf-8", errors="replace")
    manifest = json.loads((output / "run-manifest.json").read_bytes())
    _validator("run-manifest-v1.schema.json").validate(manifest)
    assert [item["path"] for item in manifest["artifacts"]] == ["file-changes.json"]
    assert manifest["config"]["resolved"]["comparison"] == {
        "target_ref": "refs/heads/main",
        "upstream_ref": "refs/remotes/origin",
    }
    assert manifest["domains"][0]["artifact_paths"] == []
    with_diff_diagnostic = {
        **manifest,
        "diagnostics": [
            {
                "type": "diagnostic",
                "schema": "code-structure-viz.diagnostic/v1",
                "code": "CSV-DIFF-002",
                "severity": "error",
                "domain": None,
                "path": None,
                "symbol": None,
                "line": None,
                "recoverable": False,
                "message": "Changed path count exceeds the resolved comparison limit.",
            }
        ],
    }
    _validator("run-manifest-v1.schema.json").validate(with_diff_diagnostic)


def test_semantic_schema_rejects_member_and_relation_target_discriminant_mutations() -> None:
    validator = _validator("semantic-v1.schema.json")
    whole = json.loads(
        (SEMANTIC_GOLDEN_ROOT / "whole" / "python.snapshot.semantic.json").read_text(
            encoding="utf-8"
        )
    )
    annotation_references = json.loads(
        (
            SEMANTIC_GOLDEN_ROOT / "annotation_references" / "python.snapshot.semantic.json"
        ).read_text(encoding="utf-8")
    )

    mutations: list[dict[str, object]] = []
    field_scope = deepcopy(whole)
    next(item for item in field_scope["members"] if item["kind"] == "field")["scope"] = None
    mutations.append(field_scope)
    property_signature = deepcopy(whole)
    next(item for item in property_signature["members"] if item["kind"] == "property")[
        "signature"
    ] = None
    mutations.append(property_signature)
    method_annotation = deepcopy(whole)
    next(item for item in method_annotation["members"] if item["kind"] == "method")[
        "annotation"
    ] = "Secret"
    mutations.append(method_annotation)
    internal_id = deepcopy(whole)
    next(item for item in internal_id["relations"] if item["target"]["resolution"] == "internal")[
        "target"
    ]["id"] = None
    mutations.append(internal_id)
    external_id = deepcopy(whole)
    next(item for item in external_id["relations"] if item["target"]["resolution"] == "external")[
        "target"
    ]["id"] = "python:module:secret"
    mutations.append(external_id)
    unknown_kind = deepcopy(annotation_references)
    next(item for item in unknown_kind["relations"] if item["target"]["resolution"] == "unknown")[
        "target"
    ]["kind"] = "module"
    mutations.append(unknown_kind)
    unknown_diagnostic = deepcopy(annotation_references)
    unknown_diagnostic["diagnostics"][0]["code"] = "CSV-UNKNOWN-999"
    mutations.append(unknown_diagnostic)
    wrong_diagnostic_metadata = deepcopy(annotation_references)
    wrong_diagnostic_metadata["diagnostics"][0]["severity"] = "error"
    mutations.append(wrong_diagnostic_metadata)

    for mutation in mutations:
        with pytest.raises(ValidationError):
            validator.validate(mutation)


def test_manifest_schema_rejects_status_exit_artifact_and_catalog_mutations() -> None:
    validator = _validator("run-manifest-v1.schema.json")
    complete = json.loads(
        (SEMANTIC_GOLDEN_ROOT / "whole" / "run-manifest.json").read_text(encoding="utf-8")
    )
    partial = json.loads(
        (SEMANTIC_GOLDEN_ROOT / "partial_safe" / "run-manifest.json").read_text(encoding="utf-8")
    )

    mutations: list[dict[str, object]] = []
    wrong_exit = deepcopy(complete)
    wrong_exit["run"]["exit_code"] = 3
    mutations.append(wrong_exit)
    missing_payload_artifacts = deepcopy(complete)
    missing_payload_artifacts["domains"][0]["artifact_paths"] = []
    missing_payload_artifacts["artifacts"] = []
    mutations.append(missing_payload_artifacts)
    mismatched_artifact = deepcopy(complete)
    mismatched_artifact["artifacts"][0]["format"] = "plantuml"
    mutations.append(mismatched_artifact)
    mismatched_status = deepcopy(partial)
    mismatched_status["run"]["status"] = "complete"
    mismatched_status["run"]["exit_code"] = 0
    mutations.append(mismatched_status)
    unknown_diagnostic = deepcopy(partial)
    unknown_diagnostic["domains"][0]["diagnostics"][0]["code"] = "CSV-UNKNOWN-999"
    mutations.append(unknown_diagnostic)
    wrong_diagnostic_message = deepcopy(partial)
    wrong_diagnostic_message["domains"][0]["diagnostics"][0]["message"] = "arbitrary"
    mutations.append(wrong_diagnostic_message)

    for mutation in mutations:
        with pytest.raises(ValidationError):
            validator.validate(mutation)


def test_run_summary_schema_rejects_status_exit_domain_and_manifest_mismatches() -> None:
    validator = _validator("run-summary-v1.schema.json")
    complete = json.loads(
        (SEMANTIC_GOLDEN_ROOT / "whole" / "stdout.run-summary.jsonl").read_text(encoding="utf-8")
    )
    mutations = []
    for key, value in (
        ("exit_code", 3),
        ("run_status", "fatal"),
        ("manifest", None),
    ):
        mutation = deepcopy(complete)
        mutation[key] = value
        mutations.append(mutation)
    wrong_domain = deepcopy(complete)
    wrong_domain["domains"][0]["status"] = "not_applicable"
    mutations.append(wrong_domain)

    for mutation in mutations:
        with pytest.raises(ValidationError):
            validator.validate(mutation)


def test_stdout_result_schema_rejects_selector_status_and_reason_mismatches() -> None:
    validator = _validator("stdout-result-v1.schema.json")
    unavailable = {
        "type": "stdout_result",
        "schema": "code-structure-viz.stdout-result/v1",
        "selector": "python:semantic-json",
        "availability": False,
        "domain_status": "not_applicable",
        "stable_reason": "domain_not_applicable",
        "artifact": None,
    }
    mutations = []
    for key, value in (
        ("selector", "manifest"),
        ("domain_status", "incomplete"),
        ("stable_reason", "run_fatal"),
    ):
        mutation = {**unavailable, key: value}
        mutations.append(mutation)
    # Target reasons are only valid inside the canonical target_failures array;
    # the former top-level single-reason compatibility field is closed.
    mutations.append({**unavailable, "reason": "missing"})

    for mutation in mutations:
        with pytest.raises(ValidationError):
            validator.validate(mutation)


def test_diagnostic_schema_rejects_catalog_metadata_and_context_mismatches() -> None:
    validator = _validator("diagnostic-v1.schema.json")
    value = {
        "type": "diagnostic",
        "schema": "code-structure-viz.diagnostic/v1",
        "code": "CSV-PY-003",
        "severity": "error",
        "domain": "python",
        "path": "src/broken.py",
        "symbol": None,
        "line": 7,
        "recoverable": True,
        "message": "Python source could not be parsed with the v1 Python 3.12 grammar.",
    }
    mutations = []
    for key, changed in (
        ("severity", "info"),
        ("domain", None),
        ("symbol", "secret"),
        ("recoverable", False),
        ("message", "arbitrary message"),
    ):
        mutations.append({**value, key: changed})

    for mutation in mutations:
        with pytest.raises(ValidationError):
            validator.validate(mutation)
