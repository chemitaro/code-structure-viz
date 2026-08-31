"""Data-only reference checks for the Issue #8 pre-implementation contract.

The production adapter is intentionally absent.  These checks model the
Python-side validation boundary that will consume an untrusted adapter
response and are kept in tests so that the contract can be exercised now.
"""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

VALIDATOR_SCHEMA = "code-structure-viz.next-reference-validation/v1"
CATALOG_PATH = Path(__file__).resolve().parents[2] / "schemas" / "next-diagnostic-catalog-v1.json"
COLLECTIONS = ("projects", "files", "modules", "components", "members", "relations", "facts")
ROLES = ("control", "context", "program")
ROLE_ORDER = {role: index for index, role in enumerate(ROLES)}
# The tuple above is the canonical wire order.  Precedence is intentionally a
# separate mapping: a lower sort index is the stronger role, while the
# effective role is selected by precedence rather than by whichever role was
# appended last.
ROLE_PRECEDENCE = {"control": 3, "context": 2, "program": 1}
FORMAT_ORDER = ("semantic-json", "plantuml")
FORMAT_ORDER_INDEX = {format_name: index for index, format_name in enumerate(FORMAT_ORDER)}
TAINTS = {
    "parse_file",
    "read_file",
    "type_symbol",
    "export_binding",
    "props_subtree",
    "component_flow",
    "module_relation",
    "boundary_derivation",
}
TAINT_ORDER = (
    "parse_file",
    "read_file",
    "type_symbol",
    "export_binding",
    "props_subtree",
    "component_flow",
    "module_relation",
    "boundary_derivation",
)
TAINT_ORDER_INDEX = {taint: index for index, taint in enumerate(TAINT_ORDER)}
ROOT_EDGE_TARGET_KINDS = {
    "type_symbol": {"component", "prop"},
    "props_subtree": {"component", "prop"},
    "export_binding": {"module", "component", "export_binding", "import_binding"},
    "component_flow": {"component", "jsx_render", "component_wrap"},
    "module_relation": {"module", "static_import", "literal_dynamic_import"},
    "boundary_derivation": {
        "module",
        "static_import",
        "literal_dynamic_import",
        "client_entry",
        "router_context",
    },
}
ID_RE = re.compile(r"^next:(project|file|module|component|member|relation|fact):[0-9a-f]{64}$")
PATH_RE = re.compile(r"^(?!/)(?!.*(?:^|/)\.\.(?:/|$))(?!.*\\)(?!.*[\x00-\x1f\x7f]).+$")
PACKAGE_RE = re.compile(r"^(@[a-z0-9._-]+/)?[a-z0-9._-]+(?:/[a-z0-9._-]+)*$")
TRUSTED_MODULES = ("react", "react/jsx-runtime", "react/jsx-dev-runtime", "next/dynamic")
TRUSTED_REFERENCE_MODULES = (*TRUSTED_MODULES, "typescript/lib")
TRUSTED_GLOBALS = ("Array", "JSX", "ReadonlyArray")
LIMIT_DEFAULTS = {
    "max_files": 20000,
    "max_file_bytes": 4194304,
    "max_decoded_bytes": 67108864,
    "max_encoded_stdin_bytes": 100663296,
    "max_json_nesting": 64,
    "max_json_string_bytes": 8388608,
    "max_array_items": 100000,
    "max_collection_items": 20000,
    "max_model_records": 100000,
    "max_stdout_bytes": 16777216,
    "max_stderr_bytes": 65536,
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

# Every limit has an explicit measurement contract.  The production adapter
# must use the same unit, measurement point, inclusive boundary, and stable
# outcome; these records are intentionally data-only and cheap to exercise.
LIMIT_CONTRACTS: dict[str, dict[str, Any]] = {
    "max_entities": {
        "unit": "model_records",
        "measurement": "after_projection_before_publication",
        "encoding": "not_applicable",
        "inclusive": True,
        "outcome": "payload_unavailable",
    },
    "max_files": {
        "unit": "files",
        "measurement": "after_safe_source_selection_before_read",
        "encoding": "not_applicable",
        "inclusive": True,
        "outcome": "payload_unavailable",
    },
    "max_file_bytes": {
        "unit": "utf8_bytes_per_file",
        "measurement": "after_read_before_base64",
        "encoding": "utf8",
        "inclusive": True,
        "outcome": "payload_unavailable",
    },
    "max_decoded_bytes": {
        "unit": "utf8_bytes_per_request",
        "measurement": "sum_after_decode_before_adapter_spawn",
        "encoding": "utf8",
        "inclusive": True,
        "outcome": "payload_unavailable",
    },
    "max_encoded_stdin_bytes": {
        "unit": "utf8_bytes_per_stdin_payload",
        "measurement": "canonical_json_encode_before_adapter_spawn",
        "encoding": "utf8",
        "inclusive": True,
        "outcome": "payload_unavailable",
    },
    "max_json_nesting": {
        "unit": "json_nesting_levels",
        "measurement": "parser_depth_before_child_descent",
        "encoding": "utf8",
        "inclusive": True,
        "outcome": "payload_unavailable",
    },
    "max_json_string_bytes": {
        "unit": "utf8_bytes_per_json_string",
        "measurement": "parser_decode_before_materialization",
        "encoding": "utf8",
        "inclusive": True,
        "outcome": "payload_unavailable",
    },
    "max_array_items": {
        "unit": "items_per_json_array",
        "measurement": "parser_item_count_before_append",
        "encoding": "not_applicable",
        "inclusive": True,
        "outcome": "payload_unavailable",
    },
    "max_collection_items": {
        "unit": "records_per_model_collection",
        "measurement": "adapter_record_emission_before_append",
        "encoding": "not_applicable",
        "inclusive": True,
        "outcome": "payload_unavailable",
    },
    "max_model_records": {
        "unit": "records_per_model",
        "measurement": "adapter_model_assembly_before_publication",
        "encoding": "not_applicable",
        "inclusive": True,
        "outcome": "payload_unavailable",
    },
    "max_stdout_bytes": {
        "unit": "utf8_bytes_per_stdout_payload",
        "measurement": "canonical_output_encode_before_write",
        "encoding": "utf8",
        "inclusive": True,
        "outcome": "payload_unavailable",
    },
    "max_stderr_bytes": {
        "unit": "utf8_bytes_per_stderr_payload",
        "measurement": "diagnostic_encode_before_write",
        "encoding": "utf8",
        "inclusive": True,
        "outcome": "payload_unavailable",
    },
    "timeout_seconds": {
        "unit": "wall_clock_seconds_per_adapter_run",
        "measurement": "monotonic_deadline_at_process_wait",
        "encoding": "not_applicable",
        "inclusive": True,
        "outcome": "payload_unavailable",
    },
    "v8_old_space_mib": {
        "unit": "binary_mib_heap_limit",
        "measurement": "adapter_process_start_flag",
        "encoding": "not_applicable",
        "inclusive": True,
        "outcome": "payload_unavailable",
    },
    "max_type_depth": {
        "unit": "type_ir_levels_per_prop",
        "measurement": "validator_before_child_descent",
        "encoding": "not_applicable",
        "inclusive": True,
        "outcome": "partial_safe",
    },
    "max_type_nodes_per_prop": {
        "unit": "type_ir_nodes_per_prop",
        "measurement": "validator_before_node_visit",
        "encoding": "not_applicable",
        "inclusive": True,
        "outcome": "partial_safe",
    },
    "max_union_members": {
        "unit": "members_per_union",
        "measurement": "validator_before_union_member_visit",
        "encoding": "not_applicable",
        "inclusive": True,
        "outcome": "partial_safe",
    },
    "max_intersection_members": {
        "unit": "members_per_intersection",
        "measurement": "validator_before_intersection_member_visit",
        "encoding": "not_applicable",
        "inclusive": True,
        "outcome": "partial_safe",
    },
    "max_nested_properties": {
        "unit": "properties_per_prop_tree",
        "measurement": "validator_before_property_visit",
        "encoding": "not_applicable",
        "inclusive": True,
        "outcome": "partial_safe",
    },
    "max_signatures_per_component": {
        "unit": "signatures_per_component",
        "measurement": "validator_before_signature_visit",
        "encoding": "not_applicable",
        "inclusive": True,
        "outcome": "partial_safe",
    },
    "max_flow_visits": {
        "unit": "flow_visits_per_component",
        "measurement": "flow_traversal_before_node_visit",
        "encoding": "not_applicable",
        "inclusive": True,
        "outcome": "partial_safe",
    },
    "max_alias_edges": {
        "unit": "alias_edges_per_module",
        "measurement": "alias_graph_before_edge_append",
        "encoding": "not_applicable",
        "inclusive": True,
        "outcome": "partial_safe",
    },
}

IDENTITY_VERSIONS = {
    "project": 1,
    "file": 1,
    "module": 1,
    "component": 1,
    "member": 1,
    "relation": 1,
    "fact": 1,
    "props_ir": 1,
}
RECORD_ID_PREFIX = {
    "project": "project",
    "file": "file",
    "module": "module",
    "component": "component",
    "export_binding": "member",
    "import_binding": "member",
    "prop": "member",
    "static_import": "relation",
    "literal_dynamic_import": "relation",
    "jsx_render": "relation",
    "component_wrap": "relation",
    "client_entry": "fact",
    "router_context": "fact",
}

# The v1 trusted profile is deliberately small and closed.  The declaration
# bytes live in checked-in data-only fixtures.  Keeping the physical-to-virtual
# mapping here makes the attestation independently reproducible before the
# production adapter exists.
REPO_ROOT = Path(__file__).resolve().parents[2]
TRUSTED_PROFILE_PHYSICAL_TO_VIRTUAL = (
    (
        "tests/fixtures/next_trusted_profile/jsx-runtime.d.ts",
        "/.code-structure-viz/trusted/v1/jsx-runtime.d.ts",
    ),
    (
        "tests/fixtures/next_trusted_profile/lib.d.ts",
        "/.code-structure-viz/trusted/v1/lib.d.ts",
    ),
    (
        "tests/fixtures/next_trusted_profile/next-dynamic.d.ts",
        "/.code-structure-viz/trusted/v1/next-dynamic.d.ts",
    ),
    (
        "tests/fixtures/next_trusted_profile/react.d.ts",
        "/.code-structure-viz/trusted/v1/react.d.ts",
    ),
)
TRUSTED_PROFILE_LICENSE_INPUTS = (
    "npm:typescript@5.9.2:Apache-2.0",
    "resource:code-structure-viz-next-trusted-types@1:MIT",
)
TRUSTED_PROFILE_LICENSES: tuple[dict[str, str], ...] = (
    {
        "ecosystem": "npm",
        "name": "typescript",
        "version": "5.9.2",
        "license_id": "Apache-2.0",
        "source_url": "https://www.npmjs.com/package/typescript",
        "content_or_lock_digest": hashlib.sha256(
            TRUSTED_PROFILE_LICENSE_INPUTS[0].encode("utf-8")
        ).hexdigest(),
    },
    {
        "ecosystem": "resource",
        "name": "code-structure-viz-next-trusted-types",
        "version": "1",
        "license_id": "MIT",
        "source_url": "https://github.com/chemitaro/code-structure-viz",
        "content_or_lock_digest": hashlib.sha256(
            TRUSTED_PROFILE_LICENSE_INPUTS[1].encode("utf-8")
        ).hexdigest(),
    },
)
TRUSTED_PROFILE_FILES = (
    "/.code-structure-viz/trusted/v1/jsx-runtime.d.ts",
    "/.code-structure-viz/trusted/v1/lib.d.ts",
    "/.code-structure-viz/trusted/v1/next-dynamic.d.ts",
    "/.code-structure-viz/trusted/v1/react.d.ts",
)
TRUSTED_PROFILE_FILE_LICENSES = {
    TRUSTED_PROFILE_FILES[0]: "MIT",
    TRUSTED_PROFILE_FILES[1]: "Apache-2.0",
    TRUSTED_PROFILE_FILES[2]: "MIT",
    TRUSTED_PROFILE_FILES[3]: "MIT",
}
TRUSTED_PROFILE_FILE_SHA256 = {
    virtual_path: hashlib.sha256((REPO_ROOT / physical_path).read_bytes()).hexdigest()
    for physical_path, virtual_path in TRUSTED_PROFILE_PHYSICAL_TO_VIRTUAL
}
TRUSTED_PROFILE_FILE_SIZES = {
    virtual_path: (REPO_ROOT / physical_path).stat().st_size
    for physical_path, virtual_path in TRUSTED_PROFILE_PHYSICAL_TO_VIRTUAL
}
TRUSTED_PROFILE_SHADOWING_WITNESS = tuple(
    [
        {
            "source_kind": "module",
            "source_name": module,
            "decision": "reserved",
        }
        for module in TRUSTED_MODULES
    ]
    + [
        {
            "source_kind": "global",
            "source_name": global_name,
            "decision": "reserved",
        }
        for global_name in TRUSTED_GLOBALS
    ]
)
TRUSTED_PROFILE_MODULE_SYMBOLS = (
    ("next/dynamic", ("default",)),
    ("react", ("Component",)),
    ("react", ("createElement",)),
    ("react", ("forwardRef",)),
    ("react", ("lazy",)),
    ("react", ("memo",)),
    ("react/jsx-runtime", ("Fragment",)),
    ("react/jsx-runtime", ("jsx",)),
    ("react/jsx-runtime", ("jsxs",)),
)
TRUSTED_PROFILE_GLOBAL_SYMBOLS = (
    ("Array", ("flatMap",)),
    ("Array", ("map",)),
    ("JSX", ("Element",)),
    ("ReadonlyArray", ("flatMap",)),
    ("ReadonlyArray", ("map",)),
)


def _signature_digest(
    source_kind: str, source_name: str, export_name: str, symbol_kind: str
) -> str:
    preimage = {
        "source_kind": source_kind,
        "source_name": source_name,
        "export_name": export_name,
        "symbol_kind": symbol_kind,
    }
    return hashlib.sha256(
        json.dumps(preimage, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()


TRUSTED_PROFILE_CERTIFIED_SYMBOLS: tuple[dict[str, Any], ...] = (
    {
        "source_kind": "global",
        "source_name": "Array",
        "export_path": ["flatMap"],
        "declaration_sha256": TRUSTED_PROFILE_FILE_SHA256[TRUSTED_PROFILE_FILES[1]],
        "symbol_kind": "method",
        "signature_digest": _signature_digest("global", "Array", "flatMap", "method"),
    },
    {
        "source_kind": "global",
        "source_name": "Array",
        "export_path": ["map"],
        "declaration_sha256": TRUSTED_PROFILE_FILE_SHA256[TRUSTED_PROFILE_FILES[1]],
        "symbol_kind": "method",
        "signature_digest": _signature_digest("global", "Array", "map", "method"),
    },
    {
        "source_kind": "global",
        "source_name": "JSX",
        "export_path": ["Element"],
        "declaration_sha256": TRUSTED_PROFILE_FILE_SHA256[TRUSTED_PROFILE_FILES[1]],
        "symbol_kind": "interface",
        "signature_digest": _signature_digest("global", "JSX", "Element", "interface"),
    },
    {
        "source_kind": "global",
        "source_name": "ReadonlyArray",
        "export_path": ["flatMap"],
        "declaration_sha256": TRUSTED_PROFILE_FILE_SHA256[TRUSTED_PROFILE_FILES[1]],
        "symbol_kind": "method",
        "signature_digest": _signature_digest("global", "ReadonlyArray", "flatMap", "method"),
    },
    {
        "source_kind": "global",
        "source_name": "ReadonlyArray",
        "export_path": ["map"],
        "declaration_sha256": TRUSTED_PROFILE_FILE_SHA256[TRUSTED_PROFILE_FILES[1]],
        "symbol_kind": "method",
        "signature_digest": _signature_digest("global", "ReadonlyArray", "map", "method"),
    },
    {
        "source_kind": "module",
        "source_name": "next/dynamic",
        "export_path": ["default"],
        "declaration_sha256": TRUSTED_PROFILE_FILE_SHA256[TRUSTED_PROFILE_FILES[2]],
        "symbol_kind": "function",
        "signature_digest": _signature_digest("module", "next/dynamic", "default", "function"),
    },
    {
        "source_kind": "module",
        "source_name": "react",
        "export_path": ["Component"],
        "declaration_sha256": TRUSTED_PROFILE_FILE_SHA256[TRUSTED_PROFILE_FILES[3]],
        "symbol_kind": "class",
        "signature_digest": _signature_digest("module", "react", "Component", "class"),
    },
    {
        "source_kind": "module",
        "source_name": "react",
        "export_path": ["createElement"],
        "declaration_sha256": TRUSTED_PROFILE_FILE_SHA256[TRUSTED_PROFILE_FILES[3]],
        "symbol_kind": "function",
        "signature_digest": _signature_digest("module", "react", "createElement", "function"),
    },
    {
        "source_kind": "module",
        "source_name": "react",
        "export_path": ["forwardRef"],
        "declaration_sha256": TRUSTED_PROFILE_FILE_SHA256[TRUSTED_PROFILE_FILES[3]],
        "symbol_kind": "function",
        "signature_digest": _signature_digest("module", "react", "forwardRef", "function"),
    },
    {
        "source_kind": "module",
        "source_name": "react",
        "export_path": ["lazy"],
        "declaration_sha256": TRUSTED_PROFILE_FILE_SHA256[TRUSTED_PROFILE_FILES[3]],
        "symbol_kind": "function",
        "signature_digest": _signature_digest("module", "react", "lazy", "function"),
    },
    {
        "source_kind": "module",
        "source_name": "react",
        "export_path": ["memo"],
        "declaration_sha256": TRUSTED_PROFILE_FILE_SHA256[TRUSTED_PROFILE_FILES[3]],
        "symbol_kind": "function",
        "signature_digest": _signature_digest("module", "react", "memo", "function"),
    },
    {
        "source_kind": "module",
        "source_name": "react/jsx-runtime",
        "export_path": ["Fragment"],
        "declaration_sha256": TRUSTED_PROFILE_FILE_SHA256[TRUSTED_PROFILE_FILES[0]],
        "symbol_kind": "interface",
        "signature_digest": _signature_digest(
            "module", "react/jsx-runtime", "Fragment", "interface"
        ),
    },
    {
        "source_kind": "module",
        "source_name": "react/jsx-runtime",
        "export_path": ["jsx"],
        "declaration_sha256": TRUSTED_PROFILE_FILE_SHA256[TRUSTED_PROFILE_FILES[0]],
        "symbol_kind": "function",
        "signature_digest": _signature_digest("module", "react/jsx-runtime", "jsx", "function"),
    },
    {
        "source_kind": "module",
        "source_name": "react/jsx-runtime",
        "export_path": ["jsxs"],
        "declaration_sha256": TRUSTED_PROFILE_FILE_SHA256[TRUSTED_PROFILE_FILES[0]],
        "symbol_kind": "function",
        "signature_digest": _signature_digest("module", "react/jsx-runtime", "jsxs", "function"),
    },
)
RUNTIME_REQUIRED_MEMBER_ROLES = {
    "adapter",
    "manifest",
    "trusted_declaration",
    "typescript_lib",
}
RUNTIME_REQUIRED_PATHS = {
    "src/code_structure_viz/_next_runtime/adapter.js": "adapter",
    "src/code_structure_viz/_next_runtime/manifest.json": "manifest",
    "src/code_structure_viz/_next_runtime/trusted.d.ts": "trusted_declaration",
    "src/code_structure_viz/_next_runtime/typescript-lib.d.ts": "typescript_lib",
}
RUNTIME_PHYSICAL_TO_VIRTUAL = (
    ("tests/fixtures/next_runtime/adapter.js", "src/code_structure_viz/_next_runtime/adapter.js"),
    (
        "tests/fixtures/next_runtime/manifest.json",
        "src/code_structure_viz/_next_runtime/manifest.json",
    ),
    (
        "tests/fixtures/next_runtime/trusted.d.ts",
        "src/code_structure_viz/_next_runtime/trusted.d.ts",
    ),
    (
        "tests/fixtures/next_runtime/typescript-lib.d.ts",
        "src/code_structure_viz/_next_runtime/typescript-lib.d.ts",
    ),
)
SOURCE_PLAN_PROGRAM_SUFFIXES = (".js", ".jsx", ".ts", ".tsx")
SOURCE_PLAN_CONTEXT_SUFFIXES = (".d.ts",)
SOURCE_PLAN_HARD_EXCLUSIONS = (".git", "node_modules", ".next", "out", "dist", "build", "coverage")
SOURCE_PLAN_CONTROL_PATHS = ("package.json", "tsconfig.json", "jsconfig.json")
SOURCE_PLAN_VERSION = "1"
TARGET_KEY_RE = re.compile(r"^(component|module|file):([^#]+)(?:#(.+))?$")

# The propagation vocabulary is closed.  A failure root first reaches its
# declared seed records (or every record on its path for a file failure), then
# this table derives only ownership/reference edges from the reachable set.
TAINT_ROOT_RULES = {
    "parse_file": "file_all_records",
    "read_file": "file_all_records",
    "type_symbol": "type_subtree",
    "props_subtree": "type_subtree",
    "export_binding": "incoming_reexport",
    "component_flow": "component_flow",
    "module_relation": "relation_dependency",
    "boundary_derivation": "boundary_closure",
}
TAINT_EDGE_RULES = (
    "file_all_records",
    "incoming_reexport",
    "value_import_dependency",
    "component_flow",
    "boundary_closure",
    "type_subtree",
    "identity_dependency",
    "relation_dependency",
)


def _canonicalize(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [_canonicalize(item) for item in value]
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            assert isinstance(key, str)
            normalized_key = unicodedata.normalize("NFC", key)
            assert normalized_key not in normalized
            normalized[normalized_key] = _canonicalize(item)
        return normalized
    return value


def canonical_json_bytes(value: Any) -> bytes:
    """Return the v1 canonical JSON byte representation used by digests."""

    return json.dumps(
        _canonicalize(value),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


TRUSTED_PROFILE_LICENSE_DIGEST = digest(list(TRUSTED_PROFILE_LICENSES))


def resolved_config_digest(config: dict[str, Any]) -> str:
    return digest({key: value for key, value in config.items() if key != "domain_config_digest"})


def project_config_digest(project: dict[str, Any]) -> str:
    return digest(
        {
            "root": project["root"],
            "source_roots": project["source_roots"],
            "config_path": project["config_path"],
            "compiler_options": project["compiler_options"],
        }
    )


def source_plan_digest(config_or_request: dict[str, Any]) -> str:
    """Recompute the source-plan digest from the closed config projection."""

    projects = config_or_request["projects"]
    return digest(
        {
            "schema": "code-structure-viz.source-acquisition-plan/next/v1",
            "version": SOURCE_PLAN_VERSION,
            "projects": projects,
            "program_suffixes": SOURCE_PLAN_PROGRAM_SUFFIXES,
            "context_suffixes": SOURCE_PLAN_CONTEXT_SUFFIXES,
            "control_paths": SOURCE_PLAN_CONTROL_PATHS,
            "hard_exclusions": SOURCE_PLAN_HARD_EXCLUSIONS,
            "limits": config_or_request["limits"],
            "trusted_type_environment_digest": config_or_request["trusted_environment_digest"],
        }
    )


def _without(value: dict[str, Any], key: str) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result.pop(key, None)
    return result


def identity_preimage(record: dict[str, Any]) -> dict[str, Any]:
    """Return the closed, content-independent identity preimage for a record.

    The preimage is intentionally made from semantic identity fields only;
    ranges, ordering, aliases, source text and other payload fields cannot
    change an entity's identity.  A caller must still validate ownership and
    cross-record references separately.
    """

    kind = record["kind"]
    if kind == "project":
        identity: dict[str, Any] = {"root": record["root"]}
    elif kind in {"file", "module"}:
        identity = {"project_id": record["project_id"], "path": record["path"]}
    elif kind == "component":
        identity = {"module_id": record["module_id"], "declaration_key": record["declaration_key"]}
    elif kind == "export_binding":
        identity = {
            "owner_id": record["owner_id"],
            "exported_name": record["exported_name"],
            "role": record["role"],
        }
    elif kind == "import_binding":
        identity = {
            "owner_id": record["owner_id"],
            "imported_name": record["imported_name"],
            "role": record["role"],
            "source": record["source"],
        }
    elif kind == "prop":
        identity = {"owner_id": record["owner_id"], "name": record["name"]}
    elif kind in {"static_import", "literal_dynamic_import"}:
        identity = {
            "kind": kind,
            "source_id": record["source_id"],
            "target": record["target"],
            "role": record["role"],
            "reexport": record["reexport"],
            "boundary_effect": record["boundary_effect"],
        }
    elif kind == "jsx_render":
        identity = {"kind": kind, "source_id": record["source_id"], "target": record["target"]}
    elif kind == "component_wrap":
        identity = {
            "kind": kind,
            "source_id": record["source_id"],
            "target_component_id": record["target_component_id"],
        }
    elif kind in {"client_entry", "router_context"}:
        # Fact values are semantic: a router context mutation must not retain
        # a stale ID even though the owner remains the same.
        identity = {"kind": kind, "owner_id": record["owner_id"], "value": record["value"]}
    else:
        raise AssertionError(f"unknown Next record kind: {kind}")
    return {
        "kind": kind,
        "version": IDENTITY_VERSIONS[RECORD_ID_PREFIX[kind]],
        "identity": identity,
    }


def recompute_record_id(record: dict[str, Any]) -> str:
    """Compute the kind-prefixed SHA-256 ID mandated by Next semantic v1."""

    kind = record["kind"]
    return f"next:{RECORD_ID_PREFIX[kind]}:{digest(identity_preimage(record))}"


def recompute_compatibility_id(descriptor: dict[str, Any]) -> str:
    """Recompute the compatibility ID from the normative, content-independent preimage."""

    return digest(
        {
            "semantic_schema": descriptor["semantic_schema"],
            "identity_versions": descriptor["identity_versions"],
            "algorithm_versions": descriptor["algorithm_versions"],
            "semantic_profile_id": descriptor["semantic_profile_id"],
        }
    )


def recompute_request_id(request: dict[str, Any]) -> str:
    return digest(_without(request, "request_id"))


def validate_request_envelope(request: dict[str, Any]) -> None:
    trusted = request["trusted_type_environment"]
    assert set(trusted) == {"schema", "environment_version", "semantic_profile_id", "sha256"}
    assert trusted["schema"] == "code-structure-viz.next-trusted-types/v1"
    assert trusted["environment_version"] == "1"
    assert trusted["semantic_profile_id"] == "next-trusted-profile-v1"
    assert re.fullmatch(r"[0-9a-f]{64}", trusted["sha256"])
    assert request["request_id"] == recompute_request_id(request)
    validate_limits(request["limits"])
    validate_request_files(request)
    assert canonical_json_bytes(request) == canonical_json_bytes(_canonicalize(request))
    validate_encoded_stdin_size(request)


def validate_response_envelope(response: dict[str, Any], request: dict[str, Any]) -> None:
    assert response["protocol"] == request["protocol"] == "code-structure-viz.next-adapter/v1"
    assert response["request_id"] == request["request_id"]
    assert response["adapter_version"] == request["adapter_version"]
    assert response["model_digest"] == digest(response["model"])
    validate_compatibility_descriptor(response["compatibility_descriptor"])
    assert (
        response["semantic_compatibility_id"]
        == response["compatibility_descriptor"]["compatibility_id"]
    )
    assert (
        response["identity_versions"] == response["compatibility_descriptor"]["identity_versions"]
    )
    assert (
        response["trusted_type_environment_digest"] == request["trusted_type_environment"]["sha256"]
    )
    validate_limits_consistency(request["limits"], response["limits"])
    model = response["model"]
    assert model["projects"] == request["projects"]
    request_files = [
        {key: item for key, item in file_record.items() if key != "content_base64"}
        for file_record in request["files"]
    ]
    assert model["files"] == request_files
    validate_model(model)
    validate_proof(response["proof"], model, request_targets=request["targets"])


def recompute_run_fingerprint(
    *,
    source_view_fingerprint: str,
    source_plan_digest: str,
    domain_config_digest: str,
    projects: list[dict[str, Any]],
    targets: list[str],
    limits: dict[str, Any],
    node_version: str | None,
    typescript_version: str,
    adapter_version: str,
    protocol: str,
    trusted_environment_digest: str,
) -> str:
    return digest(
        {
            "source_view_fingerprint": source_view_fingerprint,
            "source_plan_digest": source_plan_digest,
            "domain_config_digest": domain_config_digest,
            "projects": projects,
            "targets": targets,
            "limits": limits,
            "node_version": node_version,
            "typescript_version": typescript_version,
            "adapter_version": adapter_version,
            "protocol": protocol,
            "trusted_environment_digest": trusted_environment_digest,
        }
    )


def validate_domain_manifest(value: dict[str, Any]) -> None:
    assert value["domain"] == "next"
    validate_compatibility_descriptor(value["compatibility_descriptor"])
    assert (
        value["semantic_compatibility_id"] == value["compatibility_descriptor"]["compatibility_id"]
    )
    validate_limits_consistency(value["limits"], value["config"]["limits"])
    validate_trusted_environment(value["trusted_environment"])
    _validate_public_diagnostics(value["diagnostics"])
    node = value["toolchain"]["node"]
    if value["status"] == "not_applicable":
        assert node == {"status": "not_applicable", "version": None, "failure_kind": None}
        assert value["toolchain"]["node_version"] is None
    elif value["status"] == "incomplete" and value["incomplete_kind"] == "payload_unavailable":
        if node["status"] == "unavailable":
            assert node["version"] is None
            assert node["failure_kind"] in {
                "missing",
                "unsupported_version",
                "spawn_failed",
                "timeout",
                "process_failed",
            }
            assert value["toolchain"]["node_version"] is None
        else:
            assert node["status"] == "available"
            assert node["version"] == value["toolchain"]["node_version"]
            assert node["failure_kind"] is None
    else:
        assert node["status"] == "available"
        assert node["version"] == value["toolchain"]["node_version"]
        assert node["failure_kind"] is None
        assert value["toolchain"]["node_version"] is not None
    if value["status"] == "complete":
        allowed_outcomes = {"complete"}
    elif value["status"] == "not_applicable":
        allowed_outcomes = {"not_applicable"}
    else:
        allowed_outcomes = {value["incomplete_kind"]}
    assert {diagnostic["outcome"] for diagnostic in value["diagnostics"]} <= allowed_outcomes
    assert value["config"]["trusted_environment_digest"] == value["trusted_environment"]["sha256"]
    assert value["config"]["domain_config_digest"] == resolved_config_digest(value["config"])
    assert value["config"]["domain_config_digest"] == value["domain_config_digest"]
    assert value["config"]["source_plan_digest"] == value["source_plan_digest"]
    assert value["config"]["source_plan_digest"] == source_plan_digest(value["config"])
    project_records = _assert_sorted_unique(value["projects"], "projects")
    roots: list[tuple[str, str]] = []
    for project in project_records.values():
        assert project["kind"] == "project"
        assert project["config_digest"] == project_config_digest(project)
        _assert_path(project["root"])
        for other_root, other_id in roots:
            assert not _under(project["root"], other_root)
            assert not _under(other_root, project["root"])
            assert project["id"] != other_id
        roots.append((project["root"], project["id"]))
        assert project["source_roots"] == sorted(project["source_roots"])
        assert len(project["source_roots"]) == len(set(project["source_roots"]))
        for source_root in project["source_roots"]:
            _assert_path(source_root)
            assert _under(source_root, project["root"])
        if project["config_path"] is not None:
            _assert_path(project["config_path"])
            assert _under(project["config_path"], project["root"])
        assert project["file_ids"] == sorted(set(project["file_ids"]))
        assert all(_id_kind(file_id) == "file" for file_id in project["file_ids"])
    assert value["source"]["file_count"] == sum(
        len(project["file_ids"]) for project in value["projects"]
    )
    expected_config_projects = [
        {
            "root": project["root"],
            "source_roots": project["source_roots"],
            "config_path": project["config_path"],
            "compiler_options": project["compiler_options"],
        }
        for project in value["projects"]
    ]
    assert value["config"]["projects"] == expected_config_projects
    assert value["request"]["projects"] == expected_config_projects
    assert value["request"]["targets"] == value["targets"]
    assert value["config"]["targets"] == value["targets"]
    assert value["config"]["formats"] == value["formats"]
    assert value["config"]["upstream_depth"] == value["request"]["upstream_depth"]
    assert value["config"]["downstream_depth"] == value["request"]["downstream_depth"]
    _assert_target_keys(value["targets"])
    _assert_formats(value["formats"])
    assert value["request"]["formats"] == value["formats"]
    assert value["request"]["limits"] == value["limits"]
    assert value["request"]["trusted_environment_digest"] == value["trusted_environment"]["sha256"]
    assert value["request"]["source_plan_digest"] == value["source_plan_digest"]
    assert value["request"]["domain_config_digest"] == value["domain_config_digest"]
    assert value["request"]["run_fingerprint"] == value["run_fingerprint"]
    expected_artifacts = {
        "semantic-json": "next.snapshot.semantic.json",
        "plantuml": "next.snapshot.puml",
    }
    if value["status"] == "not_applicable":
        assert value["payload_available"] is False
        assert value["entity_count"] == 0
        assert "incomplete_kind" not in value
        assert value["artifact_paths"] == []
        assert value["diagnostics"]
    elif value["status"] == "complete":
        assert value["payload_available"] is True
        assert "incomplete_kind" not in value
        assert value["entity_count"] is not None
        assert value["artifact_paths"] == [expected_artifacts[fmt] for fmt in value["formats"]]
    else:
        assert value["status"] == "incomplete"
        assert value["incomplete_kind"] in {"partial_safe", "payload_unavailable"}
        if value["incomplete_kind"] == "partial_safe":
            assert value["payload_available"] is True
            assert value["entity_count"] is not None
            assert value["artifact_paths"] == [expected_artifacts[fmt] for fmt in value["formats"]]
        else:
            assert value["payload_available"] is False
            assert value["entity_count"] is None
            assert value["artifact_paths"] == []
        assert value["diagnostics"]
    if value["budget"]["actual"] is not None:
        if value["budget"]["actual"] > value["budget"]["resolved"]:
            assert value["incomplete_kind"] == "payload_unavailable"
        else:
            assert value["entity_count"] in {0, value["budget"]["actual"]}
    assert value["run_fingerprint"] == recompute_run_fingerprint(
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


def validate_compatibility_descriptor(descriptor: dict[str, Any]) -> None:
    assert descriptor["schema"] == "code-structure-viz.next-semantic-compatibility/v1"
    assert descriptor["semantic_schema"] == "code-structure-viz.semantic/v1"
    assert descriptor["semantic_profile_id"] == "next-trusted-profile-v1"
    assert descriptor["identity_versions"] == {
        "project": 1,
        "file": 1,
        "module": 1,
        "component": 1,
        "member": 1,
        "relation": 1,
        "fact": 1,
        "props_ir": 1,
    }
    assert descriptor["compatibility_id"] == recompute_compatibility_id(descriptor)


def validate_limits(limits: dict[str, Any]) -> None:
    assert set(limits) == {"max_entities", *LIMIT_DEFAULTS}
    assert 1 <= limits["max_entities"] <= 100000
    for name, expected in LIMIT_DEFAULTS.items():
        assert limits[name] == expected, name
    validate_limit_contracts()


def validate_limit_contracts() -> None:
    """Ensure every resolved limit has a closed measurement contract."""

    assert set(LIMIT_CONTRACTS) == {"max_entities", *LIMIT_DEFAULTS}
    for contract in LIMIT_CONTRACTS.values():
        assert set(contract) == {"unit", "measurement", "encoding", "inclusive", "outcome"}
        assert contract["unit"]
        assert contract["measurement"]
        assert contract["encoding"] in {"utf8", "not_applicable"}
        assert contract["inclusive"] is True
        assert contract["outcome"] in {"partial_safe", "payload_unavailable"}


def limit_boundary_allowed(limit: int, measured: int) -> bool:
    """Model an inclusive non-negative counter boundary without allocation."""

    return measured >= 0 and measured <= limit


def assert_limit_boundary(limit: int, *, at_limit: bool, over_limit: bool) -> None:
    assert limit >= 1
    assert limit_boundary_allowed(limit, limit - 1)
    assert limit_boundary_allowed(limit, limit) is at_limit
    assert limit_boundary_allowed(limit, limit + 1) is over_limit


def validate_limits_consistency(*projections: dict[str, Any]) -> None:
    assert projections
    for projection in projections:
        validate_limits(projection)
    first = projections[0]
    assert all(projection == first for projection in projections[1:])


def encoded_request_bytes(request: dict[str, Any]) -> bytes:
    """Return the exact UTF-8 bytes sent to the adapter's stdin."""

    return canonical_json_bytes(request)


def validate_encoded_stdin_size(request: dict[str, Any], encoded: bytes | None = None) -> int:
    """Validate the request byte cap and return the measured size.

    The boundary helper accepts precomputed bytes so tests can exercise
    limit-1/limit/limit+1 without allocating a 96 MiB payload.
    """

    measured = len(encoded if encoded is not None else encoded_request_bytes(request))
    limit = request["limits"]["max_encoded_stdin_bytes"]
    assert encoded_stdin_allowed(measured, limit)
    return measured


def encoded_stdin_allowed(measured: int, limit: int) -> bool:
    return 0 <= measured <= limit


def assert_encoded_stdin_boundary(measured: int, limit: int, expected: bool) -> None:
    """Model the exact inclusive byte boundary without constructing bytes."""

    assert measured >= 0
    assert encoded_stdin_allowed(measured, limit) is expected


def _id_kind(record_id: str) -> str:
    match = ID_RE.fullmatch(record_id)
    assert match, record_id
    return match.group(1)


def _assert_path(path: str) -> None:
    assert unicodedata.normalize("NFC", path) == path
    assert PATH_RE.fullmatch(path), path


def _under(path: str, root: str) -> bool:
    return root == "." or path == root or path.startswith(root.rstrip("/") + "/")


def _assert_sorted_unique(
    records: list[dict[str, Any]], collection: str
) -> dict[str, dict[str, Any]]:
    ids = [record["id"] for record in records]
    assert ids == sorted(ids), collection
    assert len(ids) == len(set(ids)), collection
    assert all(_id_kind(record_id) == collection.removesuffix("s") for record_id in ids)
    for record in records:
        assert recompute_record_id(record) == record["id"]
    return {record_id: record for record_id, record in zip(ids, records, strict=True)}


def _assert_unique(values: list[Any]) -> None:
    encoded = [canonical_json_bytes(value) for value in values]
    assert len(encoded) == len(set(encoded))


def _assert_canonical(values: list[Any]) -> None:
    encoded = [canonical_json_bytes(value) for value in values]
    assert encoded == sorted(encoded)
    assert len(encoded) == len(set(encoded))


def _assert_target_keys(targets: list[str]) -> None:
    assert all(1 <= len(target) <= 4096 for target in targets)
    normalized = [canonical_target_key(target) for target in targets]
    assert normalized == targets
    _assert_canonical(targets)


def canonical_target_key(target: str) -> str:
    """Canonicalize one explicit target key before proof comparison."""

    normalized = unicodedata.normalize("NFC", target)
    match = TARGET_KEY_RE.fullmatch(normalized)
    assert match is not None
    kind, path, name = match.groups()
    _assert_path(path)
    if kind == "component":
        assert name is not None
        assert 1 <= len(name) <= 256
        assert "#" not in name
        return f"component:{path}#{name}"
    assert name is None
    return f"{kind}:{path}"


def resolve_target_resolutions(targets: list[str], model: dict[str, Any]) -> list[dict[str, Any]]:
    """Resolve request targets from model records, without trusting adapter IDs."""

    collections = _validate_model_collections(model)
    resolutions: list[dict[str, Any]] = []
    for target in targets:
        target_key = canonical_target_key(target)
        kind, remainder = target_key.split(":", 1)
        if kind == "component":
            path, name = remainder.rsplit("#", 1)
            matching = [
                record["id"]
                for record in collections["components"].values()
                if record["declaration_key"] == name
                and any(
                    module["id"] == record["module_id"] and module["path"] == path
                    for module in collections["modules"].values()
                )
            ]
        else:
            collection = f"{kind}s"
            matching = [
                record["id"]
                for record in collections[collection].values()
                if record["path"] == remainder
            ]
        matching.sort()
        resolutions.append(
            {
                "target_key": target_key,
                "status": "resolved" if len(matching) == 1 else "failed",
                "record_ids": matching if len(matching) == 1 else [],
            }
        )
    return resolutions


def _assert_formats(formats: list[str]) -> None:
    assert formats
    assert len(formats) == len(set(formats))
    assert all(format_name in FORMAT_ORDER_INDEX for format_name in formats)
    assert formats == sorted(formats, key=FORMAT_ORDER_INDEX.__getitem__)


def _assert_external_target(target: dict[str, Any]) -> None:
    assert target["kind"] in {"external", "unresolved"}
    assert PACKAGE_RE.fullmatch(target["safe_specifier"]), target
    exported_name = target["exported_name"]
    assert (
        exported_name is None
        or exported_name == "default"
        or re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", exported_name)
    )


def _validate_type_node(
    node: dict[str, Any],
    module_ids: set[str],
    *,
    _depth: int = 1,
    _type_parameter_scope: int | None = None,
    _state: dict[str, int] | None = None,
) -> None:
    """Validate the complete PropsTypeIR grammar and its finite limits."""

    state = (
        _state
        if _state is not None
        else {
            "nodes": 0,
            "properties": 0,
            "union_members": 0,
            "intersection_members": 0,
            "signatures": 0,
        }
    )
    assert 1 <= _depth <= LIMIT_DEFAULTS["max_type_depth"]
    state["nodes"] += 1
    assert state["nodes"] <= LIMIT_DEFAULTS["max_type_nodes_per_prop"]
    kind = node["kind"]
    if kind == "primitive":
        assert set(node) == {"kind", "name"}
    elif kind == "type_parameter":
        assert set(node) == {"kind", "ordinal"}
        assert _type_parameter_scope is not None
        assert 0 <= node["ordinal"] < _type_parameter_scope
    elif kind == "redacted_literals":
        assert set(node) == {"kind", "base", "count"}
        assert node["base"] in {"boolean", "bigint", "number", "string"}
        assert node["count"] >= 1
    elif kind == "reference":
        assert set(node) == {"kind", "scope", "module", "exported_name", "type_arguments"}
        scope = node["scope"]
        if scope == "repository":
            assert node["module"] in module_ids
            assert node["exported_name"] == "default" or re.fullmatch(
                r"[A-Za-z_$][A-Za-z0-9_$]*", node["exported_name"]
            )
        elif scope == "external":
            assert PACKAGE_RE.fullmatch(node["module"])
            assert node["exported_name"] == "default" or re.fullmatch(
                r"[A-Za-z_$][A-Za-z0-9_$]*", node["exported_name"]
            )
        else:
            assert scope == "trusted"
            assert node["module"] in TRUSTED_REFERENCE_MODULES
            if node["module"] != "typescript/lib":
                assert node["exported_name"] is not None
            assert (
                node["exported_name"] is None
                or node["exported_name"] == "default"
                or re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", node["exported_name"])
            )
        for child in node["type_arguments"]:
            _validate_type_node(
                child,
                module_ids,
                _depth=_depth + 1,
                _type_parameter_scope=_type_parameter_scope,
                _state=state,
            )
    elif kind == "array":
        assert set(node) == {"kind", "element", "readonly"}
        _validate_type_node(
            node["element"],
            module_ids,
            _depth=_depth + 1,
            _type_parameter_scope=_type_parameter_scope,
            _state=state,
        )
    elif kind == "tuple":
        assert set(node) == {"kind", "elements", "rest", "readonly"}
        optional_seen = False
        for element in node["elements"]:
            assert set(element) == {"type", "optional"}
            if element["optional"]:
                optional_seen = True
            elif optional_seen:
                raise AssertionError("required tuple element follows optional element")
            _validate_type_node(
                element["type"],
                module_ids,
                _depth=_depth + 1,
                _type_parameter_scope=_type_parameter_scope,
                _state=state,
            )
        if node["rest"] is not None:
            _validate_type_node(
                node["rest"],
                module_ids,
                _depth=_depth + 1,
                _type_parameter_scope=_type_parameter_scope,
                _state=state,
            )
    elif kind == "function":
        assert set(node) == {
            "kind",
            "type_parameter_count",
            "this_type",
            "parameters",
            "return_type",
        }
        parameter_scope = node["type_parameter_count"]
        assert 0 <= parameter_scope <= LIMIT_DEFAULTS["max_signatures_per_component"]
        state["signatures"] += 1
        assert state["signatures"] <= LIMIT_DEFAULTS["max_signatures_per_component"]
        if node["this_type"] is not None:
            _validate_type_node(
                node["this_type"],
                module_ids,
                _depth=_depth + 1,
                _type_parameter_scope=parameter_scope,
                _state=state,
            )
        optional_seen = False
        rest_seen = False
        for parameter in node["parameters"]:
            assert set(parameter) == {"type", "optional", "rest"}
            assert not rest_seen
            if parameter["rest"]:
                assert not parameter["optional"]
                rest_seen = True
            elif parameter["optional"]:
                optional_seen = True
            else:
                assert not optional_seen
            _validate_type_node(
                parameter["type"],
                module_ids,
                _depth=_depth + 1,
                _type_parameter_scope=parameter_scope,
                _state=state,
            )
        _validate_type_node(
            node["return_type"],
            module_ids,
            _depth=_depth + 1,
            _type_parameter_scope=parameter_scope,
            _state=state,
        )
    elif kind in {"union", "intersection"}:
        assert set(node) == {"kind", "members"}
        assert node["members"]
        assert len(node["members"]) <= LIMIT_DEFAULTS[f"max_{kind}_members"]
        assert all(child["kind"] != kind for child in node["members"])
        _assert_canonical(node["members"])
        for child in node["members"]:
            _validate_type_node(
                child,
                module_ids,
                _depth=_depth + 1,
                _type_parameter_scope=_type_parameter_scope,
                _state=state,
            )
    elif kind == "object":
        assert set(node) == {"kind", "properties", "index_signatures", "call_signatures"}
        assert len(node["properties"]) <= LIMIT_DEFAULTS["max_nested_properties"]
        _assert_canonical([prop["name"] for prop in node["properties"]])
        _assert_canonical([item["key_type"] for item in node["index_signatures"]])
        assert len(node["call_signatures"]) <= LIMIT_DEFAULTS["max_signatures_per_component"]
        _assert_canonical(node["call_signatures"])
        for prop in node["properties"]:
            assert set(prop) == {"name", "type", "optional", "readonly"}
            assert unicodedata.normalize("NFC", prop["name"]) == prop["name"]
            state["properties"] += 1
            assert state["properties"] <= LIMIT_DEFAULTS["max_nested_properties"]
            _validate_type_node(
                prop["type"],
                module_ids,
                _depth=_depth + 1,
                _type_parameter_scope=_type_parameter_scope,
                _state=state,
            )
        for signature in node["index_signatures"]:
            assert set(signature) == {"key_type", "value_type", "readonly"}
            _validate_type_node(
                signature["value_type"],
                module_ids,
                _depth=_depth + 1,
                _type_parameter_scope=_type_parameter_scope,
                _state=state,
            )
        for signature in node["call_signatures"]:
            assert set(signature) == {
                "type_parameter_count",
                "this_type",
                "parameters",
                "return_type",
            }
            signature_scope = signature["type_parameter_count"]
            assert 0 <= signature_scope <= LIMIT_DEFAULTS["max_signatures_per_component"]
            state["signatures"] += 1
            assert state["signatures"] <= LIMIT_DEFAULTS["max_signatures_per_component"]
            if signature["this_type"] is not None:
                _validate_type_node(
                    signature["this_type"],
                    module_ids,
                    _depth=_depth + 1,
                    _type_parameter_scope=signature_scope,
                    _state=state,
                )
            optional_seen = False
            rest_seen = False
            for parameter in signature["parameters"]:
                assert set(parameter) == {"type", "optional", "rest"}
                assert not rest_seen
                if parameter["rest"]:
                    assert not parameter["optional"]
                    rest_seen = True
                elif parameter["optional"]:
                    optional_seen = True
                else:
                    assert not optional_seen
                _validate_type_node(
                    parameter["type"],
                    module_ids,
                    _depth=_depth + 1,
                    _type_parameter_scope=signature_scope,
                    _state=state,
                )
            _validate_type_node(
                signature["return_type"],
                module_ids,
                _depth=_depth + 1,
                _type_parameter_scope=signature_scope,
                _state=state,
            )
    else:
        assert kind == "opaque"
        assert set(node) == {"kind", "reason"}


def _opaque_reason_counts(node: dict[str, Any]) -> dict[str, int]:
    """Project every opaque TypeIR reason without trusting adapter counts."""

    if node["kind"] == "opaque":
        return {node["reason"]: 1}
    children: list[dict[str, Any]] = []
    if node["kind"] == "array":
        children = [node["element"]]
    elif node["kind"] == "tuple":
        children = [element["type"] for element in node["elements"]]
        if node["rest"] is not None:
            children.append(node["rest"])
    elif node["kind"] == "function":
        children = [parameter["type"] for parameter in node["parameters"]]
        children.append(node["return_type"])
        if node["this_type"] is not None:
            children.append(node["this_type"])
    elif node["kind"] in {"union", "intersection"}:
        children = list(node["members"])
    elif node["kind"] == "object":
        children = [prop["type"] for prop in node["properties"]]
        children.extend(signature["value_type"] for signature in node["index_signatures"])
        for signature in node["call_signatures"]:
            children.extend(parameter["type"] for parameter in signature["parameters"])
            children.append(signature["return_type"])
            if signature["this_type"] is not None:
                children.append(signature["this_type"])
    result: dict[str, int] = {}
    for child in children:
        for reason, count in _opaque_reason_counts(child).items():
            result[reason] = result.get(reason, 0) + count
    return result


def _validate_model_collections(model: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    result: dict[str, dict[str, dict[str, Any]]] = {}
    for collection in COLLECTIONS:
        result[collection] = _assert_sorted_unique(model[collection], collection)
    return result


def _diagnostic_catalog() -> dict[str, dict[str, Any]]:
    return {
        entry["code"]: entry
        for entry in json.loads(CATALOG_PATH.read_text(encoding="utf-8"))["entries"]
    }


def _validate_model_diagnostics(diagnostics: list[dict[str, Any]]) -> None:
    catalog = _diagnostic_catalog()
    for diagnostic in diagnostics:
        entry = catalog.get(diagnostic["code"])
        assert entry is not None
        for field in ("severity", "recoverable", "outcome", "ref_permission"):
            assert diagnostic[field] == entry[field]
        assert diagnostic["count"] >= 1
        permission = entry["ref_permission"]
        path_ref = diagnostic["path_ref"]
        symbol_ref = diagnostic["symbol_ref"]
        if permission == "none":
            assert path_ref is None and symbol_ref is None
        elif permission == "path":
            assert path_ref is not None and symbol_ref is None
            _assert_path(path_ref)
        elif permission == "symbol":
            assert path_ref is None and symbol_ref is not None
            _id_kind(symbol_ref)
        else:
            assert permission == "path_or_symbol"
            assert (path_ref is None) != (symbol_ref is None)
            if path_ref is not None:
                _assert_path(path_ref)
            if symbol_ref is not None:
                _id_kind(symbol_ref)


def _validate_public_diagnostics(diagnostics: list[dict[str, Any]]) -> None:
    catalog = _diagnostic_catalog()
    for diagnostic in diagnostics:
        entry = catalog.get(diagnostic["code"])
        assert entry is not None
        assert diagnostic["type"] == "diagnostic"
        assert diagnostic["schema"] == "code-structure-viz.diagnostic/v1"
        assert diagnostic["domain"] == "next"
        assert diagnostic["line"] is None
        assert diagnostic["message"] == entry["message"]
        for field in ("severity", "recoverable", "outcome", "ref_permission"):
            assert diagnostic[field] == entry[field]
        permission = entry["ref_permission"]
        path = diagnostic["path"]
        symbol = diagnostic["symbol"]
        if permission == "none":
            assert path is None and symbol is None
        elif permission == "path":
            assert path is not None and symbol is None
            _assert_path(path)
        elif permission == "symbol":
            assert path is None and symbol is not None
            _id_kind(symbol)
        else:
            assert permission == "path_or_symbol"
            assert (path is None) != (symbol is None)
            if path is not None:
                _assert_path(path)
            if symbol is not None:
                _id_kind(symbol)


def validate_semantic_snapshot(value: dict[str, Any]) -> None:
    """Validate public Next projection and its status/diagnostic agreement."""

    assert value["type"] == "semantic_snapshot"
    assert value["schema"] == "code-structure-viz.semantic/v1"
    assert value["domain"] == "next"
    assert value["document_kind"] == "snapshot"
    status = value["status"]
    if status == "complete":
        assert "incomplete_kind" not in value
        allowed_outcomes = {"complete"}
    else:
        assert status == "incomplete"
        assert value["incomplete_kind"] == "partial_safe"
        allowed_outcomes = {"partial_safe"}
    _validate_model_diagnostics(value["diagnostics"])
    assert {item["outcome"] for item in value["diagnostics"]} <= allowed_outcomes
    entities = value["entities"]
    model = {
        "schema": "code-structure-viz.next-model/v1",
        "projects": value["projects"],
        "files": value["files"],
        "modules": [item for item in entities if item["kind"] == "module"],
        "components": [item for item in entities if item["kind"] == "component"],
        "members": value["members"],
        "relations": value["relations"],
        "facts": value["facts"],
        "coverage": value["coverage"],
        "diagnostics": value["diagnostics"],
    }
    validate_model(model)
    expected_projects = [
        {
            "root": project["root"],
            "source_roots": project["source_roots"],
            "config_path": project["config_path"],
            "compiler_options": project["compiler_options"],
        }
        for project in value["projects"]
    ]
    assert value["request"]["projects"] == expected_projects
    _assert_target_keys(value["request"]["targets"])
    _assert_formats(value["request"]["formats"])
    assert value["source"]["file_count"] == len(value["files"])


def _record_references(record: dict[str, Any]) -> set[str]:
    """Return declared record IDs that make ``record`` unsafe when tainted."""

    references: set[str] = set()
    kind = record["kind"]
    if kind in {"file", "module"}:
        references.add(record["project_id"])
    elif kind == "project":
        pass
    elif kind == "component":
        references.add(record["module_id"])
    elif kind == "export_binding":
        references.update((record["owner_id"], record["target_component_id"]))
    elif kind == "import_binding":
        references.add(record["owner_id"])
        if record["local_component_id"] is not None:
            references.add(record["local_component_id"])
        if record["source"]["kind"] == "internal":
            references.add(record["source"]["module_id"])
    elif kind in {"prop", "client_entry", "router_context"}:
        references.add(record["owner_id"])
    elif kind in {"static_import", "literal_dynamic_import", "jsx_render"}:
        references.add(record["source_id"])
        target = record["target"]
        target_id_key = (
            "module_id" if kind in {"static_import", "literal_dynamic_import"} else "component_id"
        )
        if target["kind"] == "internal":
            references.add(target[target_id_key])
    else:
        assert kind == "component_wrap"
        references.update((record["source_id"], record["target_component_id"]))
    return references


def _taint_dependency_closure(
    discovered: dict[str, dict[str, dict[str, Any]]],
    tainted_ids: set[str],
) -> set[str]:
    """Expand file/project and declared-reference taint to all dependent records."""

    closure = set(tainted_ids)
    changed = True
    while changed:
        changed = False
        tainted_projects = {
            record_id for record_id, item in discovered["projects"].items() if record_id in closure
        }
        for records in discovered.values():
            for record_id, item in records.items():
                record = item["record"]
                if record_id in closure:
                    continue
                if (
                    record["kind"] in {"file", "module"}
                    and record["project_id"] in tainted_projects
                ):
                    closure.add(record_id)
                    changed = True
                    continue
                if _record_references(record) & closure:
                    closure.add(record_id)
                    changed = True
        tainted_files = [
            item["record"]
            for records in discovered.values()
            for item in records.values()
            if item["record"]["kind"] == "file" and item["record"]["id"] in closure
        ]
        for records in discovered.values():
            for record_id, item in records.items():
                record = item["record"]
                if record_id in closure or record["kind"] != "module":
                    continue
                if any(
                    record["project_id"] == file_record["project_id"]
                    and record["path"] == file_record["path"]
                    for file_record in tainted_files
                ):
                    closure.add(record_id)
                    changed = True
    return closure


def _record_index(discovered: dict[str, dict[str, dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    return {
        record_id: item["record"]
        for records in discovered.values()
        for record_id, item in records.items()
    }


def _record_project_path(
    record: dict[str, Any], records: dict[str, dict[str, Any]]
) -> tuple[str, str] | None:
    """Resolve the owning project/path used by ``file_all_records``."""

    kind = record["kind"]
    if kind == "project":
        return None
    if kind in {"file", "module"}:
        return (record["project_id"], record["path"])
    if kind == "component":
        owner = records.get(record["module_id"])
    elif kind in {"export_binding", "import_binding"}:
        owner = records.get(record["owner_id"])
    elif kind == "prop":
        component = records.get(record["owner_id"])
        owner = records.get(component["module_id"]) if component is not None else None
    elif kind in {"static_import", "literal_dynamic_import"}:
        owner = records.get(record["source_id"])
    elif kind in {"jsx_render", "component_wrap"}:
        component = records.get(record["source_id"])
        owner = records.get(component["module_id"]) if component is not None else None
    else:
        assert kind in {"client_entry", "router_context"}
        owner = records.get(record["owner_id"])
    if owner is None:
        return None
    return (owner["project_id"], owner["path"])


def _root_edge_is_allowed(root: dict[str, Any], target: dict[str, Any], rule: str) -> bool:
    """Keep root-to-record edges in the closed v1 taint vocabulary."""

    root_kind = root["kind"]
    target_kind = target["kind"]
    if root["collection"] == "files":
        return (
            root_kind in {"parse_file", "read_file"}
            and rule == "file_all_records"
            and target_kind
            in {
                "file",
                "module",
                "component",
                "export_binding",
                "import_binding",
                "prop",
                "static_import",
                "literal_dynamic_import",
                "jsx_render",
                "component_wrap",
                "client_entry",
                "router_context",
            }
        )
    allowed_rules = {
        "type_symbol": {"type_subtree", "identity_dependency"},
        "props_subtree": {"type_subtree", "identity_dependency"},
        "export_binding": {"incoming_reexport", "identity_dependency"},
        "component_flow": {"component_flow", "identity_dependency"},
        "module_relation": {
            "value_import_dependency",
            "relation_dependency",
            "identity_dependency",
        },
        "boundary_derivation": {"boundary_closure", "relation_dependency", "identity_dependency"},
        "parse_file": {"file_all_records"},
        "read_file": {"file_all_records"},
    }
    return rule in allowed_rules.get(
        root_kind, set()
    ) and target_kind in ROOT_EDGE_TARGET_KINDS.get(root_kind, set())


def _causal_edge_is_allowed(
    edge: dict[str, Any],
    records: dict[str, dict[str, Any]],
    failure_roots: dict[str, dict[str, Any]],
) -> bool:
    """Check a causal edge against the closed v1 propagation rules."""

    source_id = edge["source_id"]
    target_id = edge["record_id"]
    target = records[target_id]
    rule = edge["rule"]
    if source_id in failure_roots:
        root = failure_roots[source_id]
        if not _root_edge_is_allowed(root, target, rule):
            return False
        if root["path_ref"] is not None:
            target_path = _record_project_path(target, records)
            if target_path is None or target_path[1] != root["path_ref"]:
                return False
        return True

    if source_id not in records:
        return False
    source = records[source_id]
    if source_id == target_id:
        return False
    if rule == "file_all_records":
        if source["kind"] not in {"file", "module"} or target["kind"] == "project":
            return False
        source_path = _record_project_path(source, records)
        target_path = _record_project_path(target, records)
        return source_path is not None and source_path == target_path
    if rule == "incoming_reexport":
        return (
            source["kind"] in {"module", "export_binding", "import_binding"}
            and target["kind"] in {"module", "export_binding", "import_binding"}
            and (source_id in _record_references(target) or target_id in _record_references(source))
            and (
                target.get("reexport") is True
                or source.get("reexport") is True
                or target["kind"] == "module"
            )
        )
    if rule == "value_import_dependency":
        return (
            target["kind"] in {"import_binding", "static_import"}
            and target.get("role") == "value"
            and source_id in _record_references(target)
        )
    if rule == "component_flow":
        return (
            source["kind"] == "component"
            and target["kind"] in {"jsx_render", "component_wrap"}
            and target.get("source_id") == source_id
        ) or (
            target["kind"] == "component"
            and source["kind"] in {"jsx_render", "component_wrap"}
            and target_id in _record_references(source)
        )
    if rule == "boundary_closure":
        return (
            source["kind"] in {"module", "static_import"}
            and target["kind"]
            in {
                "module",
                "static_import",
                "literal_dynamic_import",
                "client_entry",
                "router_context",
            }
            and (source_id in _record_references(target) or target_id in _record_references(source))
        )
    if rule == "type_subtree":
        return (
            source["kind"] in {"component", "prop"}
            and target["kind"] in {"component", "prop"}
            and _record_project_path(source, records) == _record_project_path(target, records)
        )
    if rule == "identity_dependency":
        return source_id in _record_references(target)
    if rule == "relation_dependency":
        return source["kind"] in {
            "static_import",
            "literal_dynamic_import",
            "jsx_render",
            "component_wrap",
        } and target_id in _record_references(source)
    return False


def _record_edge_rule(source: dict[str, Any], target: dict[str, Any]) -> str | None:
    """Return the one closed rule for a reachable record pair."""

    if source["id"] == target["id"]:
        return None
    source_kind = source["kind"]
    target_kind = target["kind"]
    if (
        source_kind == "component"
        and target_kind in {"jsx_render", "component_wrap"}
        and target.get("source_id") == source["id"]
    ):
        return "component_flow"
    if (
        source_kind in {"jsx_render", "component_wrap"}
        and target_kind == "component"
        and target["id"] in _record_references(source)
    ):
        return "relation_dependency"
    if (
        source_kind in {"component", "prop"}
        and target_kind in {"component", "prop"}
        and (
            (source_kind == "component" and target.get("owner_id") == source["id"])
            or (target_kind == "component" and target["id"] == source.get("owner_id"))
        )
    ):
        return "type_subtree"
    if (
        source_kind in {"module", "static_import", "literal_dynamic_import"}
        and target_kind
        in {"module", "static_import", "literal_dynamic_import", "client_entry", "router_context"}
        and (
            source.get("boundary_effect") == "server_to_client_entry"
            or target.get("boundary_effect") == "server_to_client_entry"
        )
        and (
            target["id"] in _record_references(source) or source["id"] in _record_references(target)
        )
    ):
        return "boundary_closure"
    if source_kind in {"static_import", "literal_dynamic_import"} and target[
        "id"
    ] in _record_references(source):
        return "relation_dependency"
    if (
        target_kind in {"import_binding", "static_import"}
        and target.get("role") == "value"
        and source["id"] in _record_references(target)
    ):
        return "value_import_dependency"
    if source["id"] in _record_references(target):
        return "identity_dependency"
    return None


def derive_required_causal_edges(
    proof: dict[str, Any], discovered: dict[str, dict[str, dict[str, Any]]]
) -> list[dict[str, str]]:
    """Generate the mandatory taint witness from roots and record ownership.

    This is deliberately independent of adapter-provided ``taints`` and
    ``causal_edges``.  Only records reachable from a root are expanded, while
    every expansion rule is selected from the closed table above.
    """

    records = _record_index(discovered)
    roots = {root["id"]: root for root in proof["failure_roots"]}
    edges: dict[tuple[str, str], dict[str, str]] = {}
    pending: list[str] = []
    reachable: set[str] = set()

    for root_id in sorted(roots):
        root = roots[root_id]
        seed_ids = root["record_ids"]
        assert seed_ids == sorted(set(seed_ids))
        assert all(seed_id in records for seed_id in seed_ids)
        if root["kind"] in {"parse_file", "read_file"}:
            candidates = []
            for record in records.values():
                if root["path_ref"] is None:
                    continue
                record_path = _record_project_path(record, records)
                if record_path is not None and record_path[1] == root["path_ref"]:
                    candidates.append(record)
            candidate_ids = {record["id"] for record in candidates}
            assert set(seed_ids) <= candidate_ids
        else:
            candidates = [records[seed_id] for seed_id in seed_ids]
        for target in sorted(candidates, key=lambda item: item["id"]):
            root_rule = TAINT_ROOT_RULES[root["kind"]]
            assert root_rule in TAINT_EDGE_RULES
            edge = {
                "source_id": root_id,
                "record_id": target["id"],
                "rule": root_rule,
            }
            assert _causal_edge_is_allowed(edge, records, roots)
            edges[(root_id, target["id"])] = edge
            if target["id"] not in reachable:
                reachable.add(target["id"])
                pending.append(target["id"])

    while pending:
        source_id = pending.pop()
        source = records[source_id]
        for target in sorted(records.values(), key=lambda item: item["id"]):
            edge_rule = _record_edge_rule(source, target)
            if edge_rule is None:
                continue
            assert edge_rule in TAINT_EDGE_RULES
            edge = {
                "source_id": source_id,
                "record_id": target["id"],
                "rule": edge_rule,
            }
            assert _causal_edge_is_allowed(edge, records, roots)
            key = (source_id, target["id"])
            if key not in edges:
                edges[key] = edge
            if target["id"] not in reachable:
                reachable.add(target["id"])
                pending.append(target["id"])
    result = list(edges.values())
    result.sort(key=canonical_json_bytes)
    return result


def _derived_taint_fixed_point(
    proof: dict[str, Any],
    discovered: dict[str, dict[str, dict[str, Any]]],
) -> set[str]:
    """Derive tainted records solely from roots and validated causal edges."""

    records = _record_index(discovered)
    roots = {root["id"]: root for root in proof["failure_roots"]}
    assert len(roots) == len(proof["failure_roots"])
    edges = proof["causal_edges"]
    assert edges == derive_required_causal_edges(proof, discovered)
    adjacency: dict[str, set[str]] = {}
    for edge in edges:
        assert edge["record_id"] in records
        assert _causal_edge_is_allowed(edge, records, roots)
        adjacency.setdefault(edge["source_id"], set()).add(edge["record_id"])

    reachable: set[str] = set()
    reachable_sources = set(roots)
    pending = list(roots)
    while pending:
        source_id = pending.pop()
        for target_id in adjacency.get(source_id, set()):
            if target_id in reachable:
                continue
            reachable.add(target_id)
            reachable_sources.add(target_id)
            pending.append(target_id)
    assert all(edge["source_id"] in reachable_sources for edge in edges)
    expected_taints: dict[str, set[str]] = {}
    pending_pairs = [(root_id, roots[root_id]["kind"]) for root_id in roots if root_id in adjacency]
    while pending_pairs:
        source_id, taint = pending_pairs.pop()
        for target_id in adjacency.get(source_id, set()):
            taints = expected_taints.setdefault(target_id, set())
            if taint in taints:
                continue
            taints.add(taint)
            pending_pairs.append((target_id, taint))
    for record_id, item in (
        (record_id, item)
        for records_by_collection in discovered.values()
        for record_id, item in records_by_collection.items()
    ):
        assert set(item["taints"]) == expected_taints.get(record_id, set())
    return reachable


def validate_model(model: dict[str, Any]) -> None:
    collections = _validate_model_collections(model)
    project_records = collections["projects"]
    file_records = collections["files"]
    module_records = collections["modules"]
    component_records = collections["components"]
    member_records = collections["members"]
    relation_records = collections["relations"]
    fact_records = collections["facts"]

    roots: list[tuple[str, str]] = []
    for project in project_records.values():
        assert project["kind"] == "project"
        assert project["config_digest"] == project_config_digest(project)
        _assert_path(project["root"])
        for other_root, other_id in roots:
            assert not _under(project["root"], other_root)
            assert not _under(other_root, project["root"])
            assert project["id"] != other_id
        roots.append((project["root"], project["id"]))
        assert project["file_ids"] == sorted(project["file_ids"])
        assert all(_id_kind(file_id) == "file" for file_id in project["file_ids"])
        assert project["source_roots"] == sorted(project["source_roots"])
        assert len(project["source_roots"]) == len(set(project["source_roots"]))
        for source_root in project["source_roots"]:
            _assert_path(source_root)
            assert _under(source_root, project["root"])
        if project["config_path"] is not None:
            _assert_path(project["config_path"])
            assert _under(project["config_path"], project["root"])

    files_by_project: dict[str, list[str]] = {project_id: [] for project_id in project_records}
    for file_record in file_records.values():
        assert file_record["kind"] == "file"
        assert file_record["project_id"] in project_records
        _assert_path(file_record["path"])
        matching_roots = [
            project_id for root, project_id in roots if _under(file_record["path"], root)
        ]
        assert matching_roots == [file_record["project_id"]]
        roles = file_record["roles"]
        assert roles and set(roles) <= set(ROLES)
        assert len(roles) == len(set(roles))
        assert roles == sorted(roles, key=ROLE_ORDER.__getitem__)
        assert file_record["effective_role"] == max(roles, key=ROLE_PRECEDENCE.__getitem__)
        files_by_project[file_record["project_id"]].append(file_record["id"])
    for project_id, project in project_records.items():
        assert project["file_ids"] == sorted(files_by_project[project_id])

    for module in module_records.values():
        assert module["kind"] == "module"
        assert module["project_id"] in project_records
        _assert_path(module["path"])
        assert module["derived_roles"] == sorted(module["derived_roles"])
        assert len(module["derived_roles"]) == len(set(module["derived_roles"]))
        assert any(
            file_record["project_id"] == module["project_id"]
            and file_record["path"] == module["path"]
            for file_record in file_records.values()
        )
    _assert_unique([(module["project_id"], module["path"]) for module in module_records.values()])
    for component in component_records.values():
        assert component["kind"] == "component"
        assert component["module_id"] in module_records
        _assert_unique(component["recognition_evidence"])
    _assert_unique(
        [
            (component["module_id"], component["declaration_key"])
            for component in component_records.values()
        ]
    )

    member_keys: list[Any] = []
    component_signature_counts: dict[str, int] = {}
    for member in member_records.values():
        if member["kind"] == "export_binding":
            assert member["owner_id"] in module_records
            assert member["resolution_kind"] in {"component", "value", "type"}
            if member["resolution_kind"] == "component":
                assert member["role"] == "value"
                assert member["target_component_id"] in component_records
            elif member["resolution_kind"] == "value":
                assert member["role"] == "value"
                assert member["target_component_id"] is None
            else:
                assert member["role"] == "type"
                assert member["target_component_id"] is None
            member_keys.append((member["kind"], member["owner_id"], member["exported_name"]))
        elif member["kind"] == "import_binding":
            assert member["owner_id"] in module_records
            if member["local_component_id"] is not None:
                assert member["local_component_id"] in component_records
            source = member["source"]
            if source["kind"] == "internal":
                assert source["module_id"] in module_records
            else:
                _assert_external_target(source)
            member_keys.append(
                (
                    member["kind"],
                    member["owner_id"],
                    member["imported_name"],
                    member["role"],
                    tuple(sorted(source.items())),
                )
            )
        else:
            assert member["kind"] == "prop"
            assert member["owner_id"] in component_records
            type_state: dict[str, int] = {
                "nodes": 0,
                "properties": 0,
                "union_members": 0,
                "intersection_members": 0,
                "signatures": 0,
            }
            _validate_type_node(member["type_node"], set(module_records), _state=type_state)
            component_signature_counts[member["owner_id"]] = (
                component_signature_counts.get(member["owner_id"], 0) + type_state["signatures"]
            )
            assert (
                component_signature_counts[member["owner_id"]]
                <= LIMIT_DEFAULTS["max_signatures_per_component"]
            )
            member_keys.append((member["kind"], member["owner_id"], member["name"]))
    _assert_unique(member_keys)

    relation_keys: list[Any] = []
    for relation in relation_records.values():
        if relation["kind"] in {"static_import", "literal_dynamic_import"}:
            assert relation["source_id"] in module_records
            target = relation["target"]
            if target["kind"] == "internal":
                assert target["module_id"] in module_records
            else:
                _assert_external_target(target)
            if relation["kind"] == "literal_dynamic_import":
                assert relation["role"] == "value"
                assert relation["reexport"] is False
                assert relation["boundary_effect"] == "none"
            elif relation["boundary_effect"] == "server_to_client_entry":
                assert relation["role"] == "value"
                assert target["kind"] == "internal"
                assert module_records[relation["source_id"]]["client_entry"] is False
                assert "server_candidate" in module_records[relation["source_id"]]["derived_roles"]
                assert module_records[target["module_id"]]["client_entry"] is True
            else:
                assert relation["boundary_effect"] == "none"
            assert relation["role"] in {"value", "type"}
            assert isinstance(relation["reexport"], bool)
            relation_keys.append(
                (
                    relation["kind"],
                    relation["source_id"],
                    relation["role"],
                    relation["reexport"],
                    relation["boundary_effect"],
                    tuple(sorted(target.items())),
                )
            )
        elif relation["kind"] == "jsx_render":
            assert relation["source_id"] in component_records
            target = relation["target"]
            if target["kind"] == "internal":
                assert target["component_id"] in component_records
            else:
                _assert_external_target(target)
            assert relation["occurrence_count"] >= 1
            assert relation["contexts"] == sorted(set(relation["contexts"]))
            relation_keys.append(
                (
                    relation["kind"],
                    relation["source_id"],
                    tuple(sorted(target.items())),
                )
            )
        else:
            assert relation["kind"] == "component_wrap"
            assert relation["source_id"] in component_records
            assert relation["target_component_id"] in component_records
            assert relation["occurrence_count"] >= 1
            assert relation["contexts"] == ["direct"]
            relation_keys.append(
                (
                    relation["kind"],
                    relation["source_id"],
                    relation["target_component_id"],
                )
            )
    _assert_unique(relation_keys)

    fact_keys: list[Any] = []
    for fact in fact_records.values():
        assert fact["owner_id"] in module_records
        if fact["kind"] == "client_entry":
            assert fact["value"] is True
            assert module_records[fact["owner_id"]]["client_entry"] is True
        else:
            assert fact["kind"] == "router_context"
            assert fact["value"] in {"app_ui", "app_route_handler", "pages_ui", "pages_api", "none"}
            assert module_records[fact["owner_id"]]["router_context"] == fact["value"]
        fact_keys.append((fact["kind"], fact["owner_id"]))
    _assert_unique(fact_keys)

    expected_facts = {
        ("client_entry", module_id, True)
        for module_id, module in module_records.items()
        if module["client_entry"]
    }
    expected_facts.update(
        ("router_context", module_id, module["router_context"])
        for module_id, module in module_records.items()
    )
    actual_facts = {
        (fact["kind"], fact["owner_id"], fact["value"]) for fact in fact_records.values()
    }
    assert actual_facts == expected_facts

    _validate_model_diagnostics(model["diagnostics"])

    counts = model["coverage"]["counts"]
    opaque_counts: dict[str, int] = {}
    for member in member_records.values():
        if member["kind"] != "prop":
            continue
        for reason, count in _opaque_reason_counts(member["type_node"]).items():
            opaque_counts[reason] = opaque_counts.get(reason, 0) + count
    assert model["coverage"]["opaque_reason_counts"] == opaque_counts
    for collection in COLLECTIONS:
        assert counts[collection] == len(collections[collection])
        assert counts[collection] <= LIMIT_DEFAULTS["max_collection_items"]
    assert counts["published"] == sum(len(collections[collection]) for collection in COLLECTIONS)
    assert counts["published"] <= counts["discovered"]
    assert counts["discovered"] <= LIMIT_DEFAULTS["max_model_records"]
    assert counts["excluded"] >= 0
    assert counts["failed"] >= 0


def validate_request_files(request: dict[str, Any]) -> None:
    _assert_target_keys(request["targets"])
    assert len(request["files"]) <= LIMIT_DEFAULTS["max_files"]
    project_ids = [project["id"] for project in request["projects"]]
    assert project_ids == sorted(project_ids)
    assert len(project_ids) == len(set(project_ids))
    assert all(_id_kind(project_id) == "project" for project_id in project_ids)
    roots = [(project["root"], project["id"]) for project in request["projects"]]
    for index, (root, project_id) in enumerate(roots):
        assert request["projects"][index]["kind"] == "project"
        assert request["projects"][index]["config_digest"] == project_config_digest(
            request["projects"][index]
        )
        assert recompute_record_id(request["projects"][index]) == project_id
        _assert_path(root)
        for source_root in request["projects"][index]["source_roots"]:
            _assert_path(source_root)
            assert _under(source_root, root)
        config_path = request["projects"][index]["config_path"]
        if config_path is not None:
            _assert_path(config_path)
            assert _under(config_path, root)
        for other_root, other_id in roots[:index]:
            assert project_id != other_id
            assert not _under(root, other_root)
            assert not _under(other_root, root)
    file_ids = [file_record["id"] for file_record in request["files"]]
    assert file_ids == sorted(file_ids)
    assert len(file_ids) == len(set(file_ids))
    assert all(_id_kind(file_id) == "file" for file_id in file_ids)
    project_set = set(project_ids)
    files_by_project: dict[str, list[str]] = {project_id: [] for project_id in project_ids}
    file_keys: list[tuple[str, str]] = []
    total_decoded_bytes = 0
    for file_record in request["files"]:
        assert file_record["kind"] == "file"
        assert recompute_record_id(file_record) == file_record["id"]
        assert file_record["project_id"] in project_set
        _assert_path(file_record["path"])
        matching_roots = [
            project_id for root, project_id in roots if _under(file_record["path"], root)
        ]
        assert matching_roots == [file_record["project_id"]]
        roles = file_record["roles"]
        assert roles and set(roles) <= set(ROLES)
        assert len(roles) == len(set(roles))
        assert roles == sorted(roles, key=ROLE_ORDER.__getitem__)
        assert file_record["effective_role"] == max(roles, key=ROLE_PRECEDENCE.__getitem__)
        files_by_project[file_record["project_id"]].append(file_record["id"])
        file_keys.append((file_record["project_id"], file_record["path"]))
        encoded = file_record["content_base64"]
        decoded = base64.b64decode(encoded, validate=True)
        assert base64.b64encode(decoded).decode("ascii") == encoded
        assert file_record["size_bytes"] == len(decoded)
        assert len(decoded) <= LIMIT_DEFAULTS["max_file_bytes"]
        assert hashlib.sha256(decoded).hexdigest() == file_record["sha256"]
        total_decoded_bytes += len(decoded)
    _assert_unique(file_keys)
    assert total_decoded_bytes <= LIMIT_DEFAULTS["max_decoded_bytes"]
    for project in request["projects"]:
        assert project["file_ids"] == sorted(files_by_project[project["id"]])


def expected_export_resolution_witness(model: dict[str, Any]) -> list[dict[str, Any]]:
    """Project every export binding into an independently checkable witness."""

    witnesses = []
    for member in model["members"]:
        if member["kind"] != "export_binding":
            continue
        witnesses.append(
            {
                "member_id": member["id"],
                "resolution": member["resolution_kind"],
                "component_id": (
                    member["target_component_id"]
                    if member["resolution_kind"] == "component"
                    else None
                ),
            }
        )
    witnesses.sort(key=canonical_json_bytes)
    return witnesses


def validate_proof(
    proof: dict[str, Any],
    model: dict[str, Any],
    expected_targets: dict[str, tuple[str, ...]] | None = None,
    request_targets: list[str] | None = None,
) -> None:
    model_collections = _validate_model_collections(model)
    discovered: dict[str, dict[str, dict[str, Any]]] = {
        collection: {} for collection in COLLECTIONS
    }
    for item in proof["discovered_records"]:
        record = item["record"]
        collection = item["collection"]
        record_id = record["id"]
        assert record_id not in discovered[collection]
        assert _id_kind(record_id) == collection.removesuffix("s")
        assert recompute_record_id(record) == record_id
        assert all(taint in TAINTS for taint in item["taints"])
        assert item["taints"] == sorted(item["taints"], key=TAINT_ORDER_INDEX.__getitem__)
        discovered[collection][record_id] = item

    published = {collection: set(records) for collection, records in model_collections.items()}
    for collection, record_ids in published.items():
        assert record_ids <= set(discovered[collection])
        for record_id in record_ids:
            discovered_record = discovered[collection][record_id]["record"]
            assert discovered_record == model_collections[collection][record_id]
            assert discovered[collection][record_id]["taints"] == []

    tainted_ids = {
        record_id
        for records in discovered.values()
        for record_id, item in records.items()
        if item["taints"]
    }

    failure_ids = {root["id"] for root in proof["failure_roots"]}
    assert len(failure_ids) == len(proof["failure_roots"])
    all_discovered_ids = set().union(*(set(records) for records in discovered.values()))
    for root in proof["failure_roots"]:
        assert root["id"].startswith("next:failure:")
        assert root["collection"] in COLLECTIONS
        assert root["kind"] in TAINTS
        expected_collections = {
            "parse_file": {"files"},
            "read_file": {"files"},
            "type_symbol": {"components", "members"},
            "props_subtree": {"components", "members"},
            "export_binding": {"members", "modules"},
            "component_flow": {"components", "relations"},
            "module_relation": {"modules", "relations"},
            "boundary_derivation": {"modules", "relations", "facts"},
        }
        assert root["collection"] in expected_collections[root["kind"]]
        record_ids = root["record_ids"]
        assert record_ids == sorted(set(record_ids))
        assert record_ids
        assert set(record_ids) <= all_discovered_ids
        if root["collection"] == "files":
            assert root["path_ref"] is not None
        if root["path_ref"] is not None:
            _assert_path(root["path_ref"])
    taint_closure = _derived_taint_fixed_point(proof, discovered)
    assert taint_closure == tainted_ids
    assert not any(
        record_id in taint_closure for record_ids in published.values() for record_id in record_ids
    )

    excluded: dict[str, set[str]] = {collection: set() for collection in COLLECTIONS}
    for item in proof["excluded"]:
        collection = item["collection"]
        record_id = item["record_id"]
        assert record_id in discovered[collection]
        assert record_id not in excluded[collection]
        assert record_id not in published[collection]
        if item["reason"] == "tainted":
            assert discovered[collection][record_id]["taints"]
        excluded[collection].add(record_id)

    failed: dict[str, set[str]] = {collection: set() for collection in COLLECTIONS}
    for item in proof["failed"]:
        collection = item["collection"]
        record_id = item["record_id"]
        assert record_id in discovered[collection]
        assert record_id not in failed[collection]
        assert record_id not in published[collection]
        failed[collection].add(record_id)

    for collection in COLLECTIONS:
        assert excluded[collection].isdisjoint(failed[collection])
        assert (
            set(discovered[collection])
            == published[collection] | excluded[collection] | failed[collection]
        )

    excluded_reasons = {
        (item["collection"], item["record_id"]): item["reason"] for item in proof["excluded"]
    }
    failed_reasons = {
        (item["collection"], item["record_id"]): item["reason"] for item in proof["failed"]
    }
    assert len(excluded_reasons) == len(proof["excluded"])
    assert len(failed_reasons) == len(proof["failed"])
    for collection, records in discovered.items():
        for record_id, item in records.items():
            disposition = (collection, record_id)
            if item["taints"]:
                assert disposition in excluded_reasons or disposition in failed_reasons
            if disposition in excluded_reasons and excluded_reasons[disposition] == "tainted":
                assert item["taints"]
            if disposition in failed_reasons:
                reason = failed_reasons[disposition]
                assert reason == "over_budget" or reason in item["taints"]

    assert taint_closure <= {
        record_id
        for collection in COLLECTIONS
        for record_id in (excluded[collection] | failed[collection])
    }

    all_discovered = set().union(*(set(records) for records in discovered.values()))
    _assert_canonical(proof["causal_edges"])
    for edge in proof["causal_edges"]:
        assert edge["source_id"] in all_discovered | failure_ids
        assert edge["record_id"] in all_discovered

    assert all(
        root["id"] in {edge["source_id"] for edge in proof["causal_edges"]}
        for root in proof["failure_roots"]
    )

    assert proof["causal_edges"] == derive_required_causal_edges(proof, discovered)

    assert proof["export_resolution_witness"] == expected_export_resolution_witness(model)

    target_keys = [item["target_key"] for item in proof["target_resolutions"]]
    assert target_keys == sorted(target_keys)
    assert len(target_keys) == len(set(target_keys))
    for resolution in proof["target_resolutions"]:
        if resolution["status"] == "resolved":
            assert resolution["record_ids"]
            assert resolution["record_ids"] == sorted(resolution["record_ids"])
            assert set(resolution["record_ids"]) <= all_discovered
            assert set(resolution["record_ids"]) <= set().union(*published.values())
        else:
            assert resolution["record_ids"] == []
    if expected_targets is not None:
        actual_targets = {
            resolution["target_key"]: (
                resolution["status"],
                tuple(resolution["record_ids"]),
            )
            for resolution in proof["target_resolutions"]
        }
        for target_key, expected_ids in expected_targets.items():
            assert actual_targets[target_key] == ("resolved", expected_ids)
    if request_targets is not None:
        canonical_targets = [canonical_target_key(target) for target in request_targets]
        assert canonical_targets == request_targets
        assert proof["target_resolutions"] == resolve_target_resolutions(request_targets, model)
    coverage_targets = {
        item["target_key"]: (item["status"], tuple(item["record_ids"]))
        for item in model["coverage"]["target_completeness"]
    }
    assert len(coverage_targets) == len(model["coverage"]["target_completeness"])
    proof_targets = {
        item["target_key"]: (
            "complete" if item["status"] == "resolved" else "failed",
            tuple(item["record_ids"]),
        )
        for item in proof["target_resolutions"]
    }
    assert coverage_targets == proof_targets

    for collection, count in model["coverage"]["counts"].items():
        if collection in COLLECTIONS:
            assert count == len(model_collections[collection])
    assert model["coverage"]["counts"]["discovered"] == sum(
        len(records) for records in discovered.values()
    )
    assert model["coverage"]["counts"]["excluded"] == sum(
        len(records) for records in excluded.values()
    )
    assert model["coverage"]["counts"]["failed"] == sum(len(records) for records in failed.values())

    coverage = model["coverage"]
    assert coverage["affected_ids"] == sorted(taint_closure)
    tainted_records = {
        record_id: records[record_id]["record"]
        for records in discovered.values()
        for record_id in records
        if record_id in taint_closure
    }
    expected_frontier = sorted(
        {
            referenced_id
            for record in tainted_records.values()
            for referenced_id in _record_references(record)
            if referenced_id in all_discovered
            and referenced_id not in taint_closure
            and _id_kind(referenced_id) != "project"
        }
    )
    assert coverage["taint_frontier"] == expected_frontier
    expected_failed_files = sorted(
        {
            (discovered["files"][record_id]["record"]["path"], reason)
            for (collection, record_id), reason in failed_reasons.items()
            if collection == "files"
        }
    )
    assert (
        sorted((item["path"], item["reason"]) for item in coverage["failed_files"])
        == expected_failed_files
    )

    opaque_counts: dict[str, int] = {}
    for member in model["members"]:
        if member["kind"] != "prop":
            continue
        for reason, count in _opaque_reason_counts(member["type_node"]).items():
            opaque_counts[reason] = opaque_counts.get(reason, 0) + count
    assert coverage["opaque_reason_counts"] == opaque_counts
    losses = coverage["correlation_losses"]
    _assert_canonical(losses)
    component_ids = set(model_collections["components"])
    prop_records = {member["id"]: member for member in model["members"] if member["kind"] == "prop"}
    for loss in losses:
        assert loss["component_id"] in component_ids
        assert loss["prop_ids"] == sorted(loss["prop_ids"])
        assert loss["prop_ids"]
        assert loss["signature_count"] <= LIMIT_DEFAULTS["max_signatures_per_component"]
        assert all(
            prop_records[prop_id]["owner_id"] == loss["component_id"]
            for prop_id in loss["prop_ids"]
        )
    assert coverage["unknown_relation_count"] == sum(
        relation["target"]["kind"] == "unresolved"
        for relation in model["relations"]
        if "target" in relation
    )
    assert coverage["non_component_value_export_count"] == sum(
        member["resolution_kind"] == "value"
        for member in model["members"]
        if member["kind"] == "export_binding" and member["role"] == "value"
    )
    assert coverage["type_only_export_count"] == sum(
        member["resolution_kind"] == "type"
        for member in model["members"]
        if member["kind"] == "export_binding"
    )


def validate_trusted_environment(
    environment: dict[str, Any], target_paths: list[str] | None = None
) -> None:
    assert environment["environment_version"] == "1"
    assert environment["semantic_profile_id"] == "next-trusted-profile-v1"
    assert environment["typescript_version"] == "5.9.2"
    assert environment["license_inventory_digest"] == TRUSTED_PROFILE_LICENSE_DIGEST
    assert environment["reserved_module_specifiers"] == list(TRUSTED_MODULES)
    assert environment["reserved_global_names"] == list(TRUSTED_GLOBALS)
    files = environment["files"]
    assert [item["virtual_path"] for item in files] == list(TRUSTED_PROFILE_FILES)
    assert len({item["virtual_path"] for item in files}) == len(files)
    assert files == [
        {
            "physical_path": physical_path,
            "virtual_path": path,
            "size_bytes": TRUSTED_PROFILE_FILE_SIZES[path],
            "sha256": TRUSTED_PROFILE_FILE_SHA256[path],
            "license_id": TRUSTED_PROFILE_FILE_LICENSES[path],
        }
        for physical_path, path in TRUSTED_PROFILE_PHYSICAL_TO_VIRTUAL
    ]
    file_digests = {item["sha256"] for item in files}
    for item in files:
        physical_path = item["physical_path"]
        assert physical_path in {
            physical for physical, _virtual in TRUSTED_PROFILE_PHYSICAL_TO_VIRTUAL
        }
        physical_file = REPO_ROOT / physical_path
        assert physical_file.is_file()
        content = physical_file.read_bytes()
        assert item["size_bytes"] == len(content)
        assert item["sha256"] == hashlib.sha256(content).hexdigest()
        virtual_path = item["virtual_path"]
        assert unicodedata.normalize("NFC", virtual_path) == virtual_path
        assert re.fullmatch(
            r"/\.code-structure-viz/trusted/v1/[A-Za-z0-9._/-]+\.d\.ts", virtual_path
        )
        assert "//" not in virtual_path
        assert ".." not in virtual_path.split("/")
    for target_path in target_paths or []:
        _assert_path(target_path)
        normalized = unicodedata.normalize("NFC", target_path)
        assert not any(normalized == item["virtual_path"] for item in files)
    symbols = environment["certified_symbols"]
    assert symbols == list(TRUSTED_PROFILE_CERTIFIED_SYMBOLS)
    symbol_keys = [
        (item["source_kind"], item["source_name"], tuple(item["export_path"])) for item in symbols
    ]
    expected_symbol_keys = sorted(
        [("global", source, export_path) for source, export_path in TRUSTED_PROFILE_GLOBAL_SYMBOLS]
        + [
            ("module", source, export_path)
            for source, export_path in TRUSTED_PROFILE_MODULE_SYMBOLS
        ]
    )
    assert symbol_keys == expected_symbol_keys
    assert len(symbol_keys) == len(set(symbol_keys))
    for symbol in symbols:
        assert symbol["declaration_sha256"] in file_digests
        if symbol["source_kind"] == "module":
            assert symbol["source_name"] in TRUSTED_MODULES
            declaration_path = {
                "react/jsx-runtime": TRUSTED_PROFILE_FILES[0],
                "next/dynamic": TRUSTED_PROFILE_FILES[2],
                "react": TRUSTED_PROFILE_FILES[3],
                "react/jsx-dev-runtime": TRUSTED_PROFILE_FILES[0],
            }[symbol["source_name"]]
        else:
            assert symbol["source_name"] in TRUSTED_GLOBALS
            declaration_path = TRUSTED_PROFILE_FILES[1]
        assert symbol["declaration_sha256"] == TRUSTED_PROFILE_FILE_SHA256[declaration_path]
        assert symbol["signature_digest"] == _signature_digest(
            symbol["source_kind"],
            symbol["source_name"],
            symbol["export_path"][-1],
            symbol["symbol_kind"],
        )
    assert environment["anti_shadowing_witness"] == list(TRUSTED_PROFILE_SHADOWING_WITNESS)
    assert environment["sha256"] == digest(_without(environment, "sha256"))


def validate_no_trusted_shadowing(
    declarations: list[dict[str, str]], environment: dict[str, Any]
) -> list[dict[str, str]]:
    """Reject target declarations that could augment a trusted namespace."""

    reserved_modules = set(environment["reserved_module_specifiers"])
    reserved_globals = set(environment["reserved_global_names"])
    witness: list[dict[str, str]] = []
    for declaration in declarations:
        assert set(declaration) == {"source_kind", "source_name", "operation"}
        assert declaration["source_kind"] in {"module", "global"}
        assert declaration["operation"] in {"declare", "augment", "redirect"}
        if declaration["source_kind"] == "module":
            reserved = declaration["source_name"] in reserved_modules
        else:
            reserved = declaration["source_name"] in reserved_globals
        decision = "reject" if reserved else "allow"
        witness.append({**declaration, "decision": decision})
        assert not reserved
    return witness


def validate_runtime_manifest(manifest: dict[str, Any]) -> None:
    members = manifest["members"]
    assert [item["path"] for item in members] == sorted(item["path"] for item in members)
    assert len({item["path"] for item in members}) == len(members)
    assert {item["path"]: item["role"] for item in members} == RUNTIME_REQUIRED_PATHS
    assert {item["role"] for item in members} == RUNTIME_REQUIRED_MEMBER_ROLES
    expected_members: list[dict[str, Any]] = []
    for physical_path, virtual_path in RUNTIME_PHYSICAL_TO_VIRTUAL:
        content = (REPO_ROOT / physical_path).read_bytes()
        expected_members.append(
            {
                "physical_path": physical_path,
                "path": virtual_path,
                "size_bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
                "role": RUNTIME_REQUIRED_PATHS[virtual_path],
            }
        )
    expected_members.sort(key=lambda item: item["path"])
    assert members == expected_members
    for item in members:
        physical_path = item["physical_path"]
        assert physical_path in {path for path, _virtual in RUNTIME_PHYSICAL_TO_VIRTUAL}
        assert (REPO_ROOT / physical_path).is_file()
        _assert_path(item["path"])
        assert item["path"].startswith("src/code_structure_viz/_next_runtime/")
        assert "//" not in item["path"]
        assert ".." not in item["path"].split("/")
    licenses = manifest["licenses"]
    license_keys = [
        (item["ecosystem"], item["name"], item["version"], item["license_id"]) for item in licenses
    ]
    assert license_keys == sorted(license_keys)
    assert len(license_keys) == len(set(license_keys))
    for license_record in licenses:
        parsed = urlparse(license_record["source_url"])
        assert parsed.scheme == "https" and parsed.netloc
    assert licenses == list(TRUSTED_PROFILE_LICENSES)
    assert manifest["license_inventory_digest"] == TRUSTED_PROFILE_LICENSE_DIGEST
    assert manifest["inventory_attestation"] == {
        "schema": "code-structure-viz.next-runtime-inventory/v1",
        "members": members,
        "sha256": digest({"members": members}),
    }
    assert manifest["build_input_digest"] == digest({"members": members, "licenses": licenses})
    assert manifest["build_output_digest"] == digest({"members": members})
    assert manifest["manifest_sha256"] == digest(_without(manifest, "manifest_sha256"))


def validate_run_status_vector(
    manifest: dict[str, Any] | None,
    summary: dict[str, Any],
    stdout_result: dict[str, Any] | None,
    published_bytes: dict[str, bytes],
    stdout_bytes: bytes | None,
    stderr_diagnostics: list[dict[str, Any]],
) -> None:
    """Validate the cross-artifact status and exact-byte publication vector."""

    run_status = summary["run_status"]
    expected_exit = {
        "complete": 0,
        "not_applicable": 0,
        "incomplete": 3,
        "fatal": 1,
        "usage": 2,
        "interrupted": 130,
    }[run_status]
    assert summary["exit_code"] == expected_exit
    if run_status == "usage":
        assert manifest is None
        assert summary["domains"] == []
        assert summary["manifest"] is None
        assert stdout_result is None
        assert stdout_bytes == b""
        assert stderr_diagnostics == []
        return
    if run_status in {"fatal", "interrupted"}:
        assert manifest is None
        assert summary["domains"] == []
        assert summary["manifest"] is None
        assert stdout_result is not None
        assert stdout_result["availability"] is False
        assert stdout_result["run_status"] == run_status
        assert stdout_result["artifact"] is None
        assert stdout_bytes == canonical_json_bytes(stdout_result) + b"\n"
        assert stderr_diagnostics == []
        return

    assert manifest is not None
    assert manifest["run"]["status"] == run_status
    assert manifest["run"]["exit_code"] == expected_exit
    assert summary["manifest"] == "run-manifest.json"
    assert len(summary["domains"]) == 1
    summary_domain = summary["domains"][0]
    domain = manifest["domains"][0]
    assert summary_domain["domain"] == domain["domain"] == "next"
    assert summary_domain["status"] == domain["status"] == run_status
    if run_status == "incomplete":
        assert summary_domain["incomplete_kind"] == domain["incomplete_kind"]
    assert manifest["next_request"] == domain["request"]
    assert manifest["next_config"] == domain["config"]
    artifact_paths = set(domain["artifact_paths"])
    assert set(published_bytes) == artifact_paths
    artifact_records = {artifact["path"]: artifact for artifact in manifest["artifacts"]}
    assert set(artifact_records) == artifact_paths
    for path, payload in published_bytes.items():
        descriptor = artifact_records[path]
        assert descriptor["size_bytes"] == len(payload)
        assert descriptor["sha256"] == hashlib.sha256(payload).hexdigest()
    assert stderr_diagnostics == manifest["diagnostics"]

    assert stdout_result is not None
    selector = stdout_result["selector"]
    assert selector in {"next:semantic-json", "next:plantuml"}
    assert stdout_result["domain_status"] == run_status
    format_name = selector.removeprefix("next:")
    expected_path = (
        "next.snapshot.semantic.json" if format_name == "semantic-json" else "next.snapshot.puml"
    )
    if run_status == "not_applicable" or domain.get("incomplete_kind") == "payload_unavailable":
        assert stdout_result["availability"] is False
        assert stdout_result["artifact"] is None
        assert "incomplete_kind" not in stdout_result
        assert stdout_result["stable_reason"] in {
            "domain_not_applicable",
            "domain_payload_unavailable",
        }
        assert stdout_bytes == canonical_json_bytes(stdout_result) + b"\n"
    else:
        assert expected_path in published_bytes
        assert stdout_result["availability"] is True
        assert stdout_result["stable_reason"] == "published_artifact"
        assert stdout_result["artifact"] == artifact_records[expected_path]
        if run_status == "incomplete":
            assert stdout_result["incomplete_kind"] == "partial_safe"
        assert stdout_bytes == published_bytes[expected_path]


def validate_run_manifest(
    manifest: dict[str, Any],
    domain: dict[str, Any],
    published_bytes: dict[str, bytes],
) -> None:
    """Validate the whole-run Next projection, not only its domain entry."""

    validate_domain_manifest(domain)
    assert manifest["type"] == "run_manifest"
    assert manifest["schema"] == "code-structure-viz.run-manifest/v1"
    assert manifest["contracts"]["plantuml"] == "code-structure-viz.plantuml/next/v1"
    assert manifest["adapters"] == [{"domain": "next", "name": "next-typescript", "version": "1"}]
    assert manifest["command"] == {
        "name": "snapshot",
        "domain": "next",
        "formats": domain["formats"],
        "stdout_selector": "next:semantic-json",
    }
    assert manifest["source"] == domain["source"]
    assert manifest["next_request"] == domain["request"]
    assert manifest["next_config"] == domain["config"]
    assert manifest["domains"] == [domain]
    assert manifest["diagnostics"] == domain["diagnostics"]
    assert manifest["request"] == {
        "projects": [project["root"] for project in domain["projects"]],
        "targets": domain["targets"],
        "formats": domain["formats"],
        "upstream_depth": domain["request"]["upstream_depth"],
        "downstream_depth": domain["request"]["downstream_depth"],
    }
    resolved_next = manifest["config"]["resolved"]["next"]
    assert resolved_next == {
        "projects": [project["root"] for project in domain["projects"]],
        "targets": domain["targets"],
        "formats": domain["formats"],
        "trusted_environment_digest": domain["trusted_environment"]["sha256"],
    }
    assert manifest["config"]["resolved"]["traversal"] == {
        "upstream_depth": domain["request"]["upstream_depth"],
        "downstream_depth": domain["request"]["downstream_depth"],
    }
    assert manifest["config"]["resolved"]["limits"] == domain["limits"]
    assert manifest["config"]["sha256"] == digest(_without(manifest["config"], "sha256"))
    expected_exit = 0 if domain["status"] in {"complete", "not_applicable"} else 3
    assert manifest["run"] == {
        "status": domain["status"],
        "exit_code": expected_exit,
        "fingerprint": domain["run_fingerprint"],
    }
    expected_artifacts = []
    for path in domain["artifact_paths"]:
        payload = published_bytes[path]
        format_name = "semantic-json" if path.endswith(".json") else "plantuml"
        expected_artifacts.append(
            {
                "path": path,
                "domain": "next",
                "format": format_name,
                "media_type": (
                    "application/json"
                    if format_name == "semantic-json"
                    else "text/vnd.plantuml; charset=utf-8"
                ),
                "size_bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    assert manifest["artifacts"] == expected_artifacts


def escape_plantuml_label(value: str) -> str:
    normalized = unicodedata.normalize("NFC", value)
    escaped: list[str] = []
    for character in normalized:
        codepoint = ord(character)
        if character == "\\":
            escaped.append("\\\\")
        elif character == '"':
            escaped.append('\\"')
        elif character == "\t":
            escaped.append("\\t")
        elif character == "\r":
            escaped.append("\\r")
        elif character == "\n":
            escaped.append("\\n")
        elif character == ";":
            escaped.append("\\;")
        elif character in "<>" or codepoint < 0x20 or codepoint == 0x7F:
            escaped.append(f"\\u{codepoint:04x}")
        else:
            escaped.append(character)
    return "".join(escaped)


def external_target_digest(target: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(target)).hexdigest()


def render_plantuml(model: dict[str, Any], status: str = "complete") -> bytes:
    """Render the small exact-byte contract fixture, not production output."""

    assert status in {"complete", "partial_safe"}
    external_targets: dict[str, dict[str, Any]] = {}
    for member in model["members"]:
        source = member.get("source")
        if source is not None and source["kind"] != "internal":
            external_targets[external_target_digest(source)] = source
    for relation in model["relations"]:
        target = relation.get("target")
        if target is not None and target["kind"] != "internal":
            external_targets[external_target_digest(target)] = target

    lines = [
        "@startuml",
        "title CodeStructureViz Next snapshot",
        f"note top: status={status}; coverage={status}",
        "legend",
        "N_P project",
        "N_M module",
        "N_C component",
        "<<export_binding>> export member",
        "<<import_binding>> import member",
        "<<prop>> prop member",
        "--> static_import|literal_dynamic_import",
        "..> jsx_render|component_wrap",
        "facet=role:<value|type>|reexport=<true|false>|boundary=<none|server_to_client_entry>",
        "marker=client_entry|router_context=<context>|client_dependency|server_candidate|unknown",
        "marker=partial_safe",
        "external=cloud-after-components-before-members",
        "sort=kind-prefixed-id-utf8",
        "endlegend",
    ]
    for project in sorted(model["projects"], key=lambda item: item["id"]):
        project_alias = project["id"].split(":")[-1]
        lines.append(f'package "P:{project["id"]}" as N_P_{project_alias} {{')
        lines.append("}")
    for module in sorted(model["modules"], key=lambda item: item["id"]):
        module_alias = module["id"].split(":")[-1]
        lines.append(f'component "M:{escape_plantuml_label(module["path"])}" as N_M_{module_alias}')
        markers = ["client_entry"] if module["client_entry"] else []
        if module["router_context"] != "none":
            markers.append(f"router_context={module['router_context']}")
        markers.extend(sorted(module["derived_roles"]))
        lines.append(f"N_M_{module_alias} : marker={'|'.join(markers or ['unknown'])}")
    for component in sorted(model["components"], key=lambda item: item["id"]):
        alias = component["id"].split(":")[-1]
        lines.append(
            f'rectangle "C:{escape_plantuml_label(component["declaration_key"])}" as N_C_{alias}'
        )
    for module in sorted(model["modules"], key=lambda item: item["id"]):
        module_alias = module["id"].split(":")[-1]
        project = next(item for item in model["projects"] if item["id"] == module["project_id"])
        project_alias = project["id"].split(":")[-1]
        lines.append(f"N_P_{project_alias} .. N_M_{module_alias} : contains")
    for component in sorted(model["components"], key=lambda item: item["id"]):
        component_alias = component["id"].split(":")[-1]
        module_alias = component["module_id"].split(":")[-1]
        lines.append(f"N_M_{module_alias} .. N_C_{component_alias} : contains")
    for target_digest in sorted(external_targets):
        target = external_targets[target_digest]
        label = f"external:{target['safe_specifier']}"
        if target.get("exported_name") is not None:
            label += f"#{target['exported_name']}"
        lines.append(f'cloud "{escape_plantuml_label(label)}" as X_{target_digest}')
    if status == "partial_safe":
        lines.append("note top: marker=partial_safe")
    for member in sorted(model["members"], key=lambda item: item["id"]):
        if member["kind"] == "prop":
            owner = f"N_C_{member['owner_id'].split(':')[-1]}"
            label = f"prop {escape_plantuml_label(member['name'])}"
            stereotype = "prop"
            facets = (
                f"optional={str(member['optional']).lower()}|readonly={str(member['readonly']).lower()}"
                f"|default={member['default_evidence']}"
            )
        elif member["kind"] == "export_binding":
            owner = f"N_M_{member['owner_id'].split(':')[-1]}"
            label = f"export {escape_plantuml_label(member['exported_name'])}"
            stereotype = "export_binding"
            facets = f"role={member['role']}|reexport={str(member['reexport']).lower()}"
        else:
            owner = f"N_M_{member['owner_id'].split(':')[-1]}"
            label = f"import {escape_plantuml_label(member['imported_name'])}"
            stereotype = "import_binding"
            source = member["source"]
            source_descriptor = source["kind"]
            if source["kind"] == "internal":
                source_descriptor += f"#{source['module_id']}"
            else:
                source_descriptor += f"#{source['safe_specifier']}"
                if source.get("exported_name") is not None:
                    source_descriptor += f"#{source['exported_name']}"
            facets = f"role={member['role']}|source={source_descriptor}"
        lines.append(f'{owner} .. "{label}" <<{stereotype}>> : {member["id"]}|{facets}')
    for relation in sorted(model["relations"], key=lambda item: item["id"]):
        if relation["kind"] in {"static_import", "literal_dynamic_import"}:
            source = f"N_M_{relation['source_id'].split(':')[-1]}"
            target = relation["target"]
            target_alias = (
                f"N_M_{target['module_id'].split(':')[-1]}"
                if target["kind"] == "internal"
                else f"X_{external_target_digest(target)}"
            )
            lines.append(
                f"{source} --> {target_alias} : {relation['kind']}|role={relation['role']}"
                f"|reexport={str(relation['reexport']).lower()}|boundary={relation['boundary_effect']}"
            )
        elif relation["kind"] == "jsx_render":
            source = f"N_C_{relation['source_id'].split(':')[-1]}"
            target = relation["target"]
            target_alias = (
                f"N_C_{target['component_id'].split(':')[-1]}"
                if target["kind"] == "internal"
                else f"X_{external_target_digest(target)}"
            )
            lines.append(
                f"{source} ..> {target_alias} : jsx_render|occurrences="
                f"{relation['occurrence_count']}"
                f"|contexts={','.join(relation['contexts'])}"
            )
        else:
            source = f"N_C_{relation['source_id'].split(':')[-1]}"
            target = f"N_C_{relation['target_component_id'].split(':')[-1]}"
            lines.append(
                f"{source} ..> {target} : component_wrap|occurrences={relation['occurrence_count']}"
                f"|contexts={','.join(relation['contexts'])}"
            )
    lines.append("@enduml")
    return ("\n".join(lines) + "\n").encode("utf-8")


def plantuml_aliases_are_safe(data: bytes) -> None:
    text = data.decode("utf-8")
    assert not text.startswith("\ufeff")
    assert text.endswith("\n")
    assert "\r" not in text
    aliases = re.findall(r"\bas ((?:N_[PMC]|X)_[0-9a-f]{64})\b", text)
    assert len(aliases) == len(set(aliases))
    for line in text.splitlines():
        assert "../" not in line
        if not line.startswith("note top: "):
            assert all(
                character != ";" or (index > 0 and line[index - 1] == "\\")
                for index, character in enumerate(line)
            )


def validate_plantuml_contract(
    data: bytes, model: dict[str, Any], status: str = "complete"
) -> None:
    """Parse the exact statement sequence independently of PlantUML itself."""

    assert status in {"complete", "partial_safe"}
    plantuml_aliases_are_safe(data)
    lines = data.decode("utf-8").splitlines()
    legend = [
        "legend",
        "N_P project",
        "N_M module",
        "N_C component",
        "<<export_binding>> export member",
        "<<import_binding>> import member",
        "<<prop>> prop member",
        "--> static_import|literal_dynamic_import",
        "..> jsx_render|component_wrap",
        "facet=role:<value|type>|reexport=<true|false>|boundary=<none|server_to_client_entry>",
        "marker=client_entry|router_context=<context>|client_dependency|server_candidate|unknown",
        "marker=partial_safe",
        "external=cloud-after-components-before-members",
        "sort=kind-prefixed-id-utf8",
        "endlegend",
    ]
    prefix = [
        "@startuml",
        "title CodeStructureViz Next snapshot",
        f"note top: status={status}; coverage={status}",
        *legend,
    ]
    assert lines[: len(prefix)] == prefix
    cursor = len(prefix)

    for project in sorted(model["projects"], key=lambda item: item["id"]):
        suffix = project["id"].split(":")[-1]
        assert lines[cursor] == (f'package "P:{project["id"]}" as N_P_{suffix} {{')
        assert lines[cursor + 1] == "}"
        cursor += 2
    for module in sorted(model["modules"], key=lambda item: item["id"]):
        suffix = module["id"].split(":")[-1]
        expected_label = escape_plantuml_label(module["path"])
        assert lines[cursor] == f'component "M:{expected_label}" as N_M_{suffix}'
        cursor += 1
        markers = ["client_entry"] if module["client_entry"] else []
        if module["router_context"] != "none":
            markers.append(f"router_context={module['router_context']}")
        markers.extend(sorted(module["derived_roles"]))
        assert lines[cursor] == f"N_M_{suffix} : marker={'|'.join(markers or ['unknown'])}"
        cursor += 1
    for component in sorted(model["components"], key=lambda item: item["id"]):
        suffix = component["id"].split(":")[-1]
        expected_label = escape_plantuml_label(component["declaration_key"])
        assert lines[cursor] == f'rectangle "C:{expected_label}" as N_C_{suffix}'
        cursor += 1

    for module in sorted(model["modules"], key=lambda item: item["id"]):
        module_suffix = module["id"].split(":")[-1]
        project = next(item for item in model["projects"] if item["id"] == module["project_id"])
        project_suffix = project["id"].split(":")[-1]
        assert lines[cursor] == f"N_P_{project_suffix} .. N_M_{module_suffix} : contains"
        cursor += 1
    for component in sorted(model["components"], key=lambda item: item["id"]):
        component_suffix = component["id"].split(":")[-1]
        module_suffix = component["module_id"].split(":")[-1]
        assert lines[cursor] == f"N_M_{module_suffix} .. N_C_{component_suffix} : contains"
        cursor += 1

    external_targets: dict[str, dict[str, Any]] = {}
    for member in model["members"]:
        source = member.get("source")
        if source is not None and source["kind"] != "internal":
            external_targets[external_target_digest(source)] = source
    for relation in model["relations"]:
        target = relation.get("target")
        if target is not None and target["kind"] != "internal":
            external_targets[external_target_digest(target)] = target
    for target_digest in sorted(external_targets):
        target = external_targets[target_digest]
        label = f"external:{target['safe_specifier']}"
        if target.get("exported_name") is not None:
            label += f"#{target['exported_name']}"
        assert lines[cursor] == (f'cloud "{escape_plantuml_label(label)}" as X_{target_digest}')
        cursor += 1
    if status == "partial_safe":
        assert lines[cursor] == "note top: marker=partial_safe"
        cursor += 1

    for member in sorted(model["members"], key=lambda item: item["id"]):
        suffix = member["owner_id"].split(":")[-1]
        owner_prefix = "N_C" if member["kind"] == "prop" else "N_M"
        if member["kind"] == "prop":
            label = f"prop {escape_plantuml_label(member['name'])}"
            stereotype = "prop"
            facets = (
                f"optional={str(member['optional']).lower()}|readonly={str(member['readonly']).lower()}"
                f"|default={member['default_evidence']}"
            )
        elif member["kind"] == "export_binding":
            label = f"export {escape_plantuml_label(member['exported_name'])}"
            stereotype = "export_binding"
            facets = f"role={member['role']}|reexport={str(member['reexport']).lower()}"
        else:
            label = f"import {escape_plantuml_label(member['imported_name'])}"
            stereotype = "import_binding"
            source = member["source"]
            source_descriptor = source["kind"]
            if source["kind"] == "internal":
                source_descriptor += f"#{source['module_id']}"
            else:
                source_descriptor += f"#{source['safe_specifier']}"
                if source.get("exported_name") is not None:
                    source_descriptor += f"#{source['exported_name']}"
            facets = f"role={member['role']}|source={source_descriptor}"
        expected_member = (
            f'{owner_prefix}_{suffix} .. "{label}" <<{stereotype}>> : {member["id"]}|{facets}'
        )
        assert lines[cursor] == expected_member
        cursor += 1
    for relation in sorted(model["relations"], key=lambda item: item["id"]):
        if relation["kind"] in {"static_import", "literal_dynamic_import"}:
            source = f"N_M_{relation['source_id'].split(':')[-1]}"
            target = relation["target"]
            target_alias = (
                f"N_M_{target['module_id'].split(':')[-1]}"
                if target["kind"] == "internal"
                else f"X_{external_target_digest(target)}"
            )
            expected = (
                f"{source} --> {target_alias} : {relation['kind']}|role={relation['role']}"
                f"|reexport={str(relation['reexport']).lower()}|boundary={relation['boundary_effect']}"
            )
        elif relation["kind"] == "jsx_render":
            source = f"N_C_{relation['source_id'].split(':')[-1]}"
            target = relation["target"]
            target_alias = (
                f"N_C_{target['component_id'].split(':')[-1]}"
                if target["kind"] == "internal"
                else f"X_{external_target_digest(target)}"
            )
            expected = (
                f"{source} ..> {target_alias} : jsx_render|occurrences="
                f"{relation['occurrence_count']}"
                f"|contexts={','.join(relation['contexts'])}"
            )
        else:
            expected = (
                f"N_C_{relation['source_id'].split(':')[-1]} ..> "
                f"N_C_{relation['target_component_id'].split(':')[-1]} : component_wrap"
                f"|occurrences={relation['occurrence_count']}|contexts={','.join(relation['contexts'])}"
            )
        assert lines[cursor] == expected
        cursor += 1
    assert lines[cursor] == "@enduml"
    assert cursor + 1 == len(lines)
