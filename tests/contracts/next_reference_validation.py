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


def _without(value: dict[str, Any], key: str) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result.pop(key, None)
    return result


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
    assert request["request_id"] == recompute_request_id(request)
    validate_limits(request["limits"])
    validate_request_files(request)


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


def recompute_run_fingerprint(
    *,
    source_view_fingerprint: str,
    source_plan_digest: str,
    domain_config_digest: str,
    projects: list[dict[str, Any]],
    targets: list[str],
    limits: dict[str, Any],
    node_version: str,
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
    assert value["config"]["trusted_environment_digest"] == value["trusted_environment"]["sha256"]
    project_records = _assert_sorted_unique(value["projects"], "projects")
    roots: list[tuple[str, str]] = []
    for project in project_records.values():
        assert project["kind"] == "project"
        _assert_path(project["root"])
        for other_root, other_id in roots:
            assert not _under(project["root"], other_root)
            assert not _under(other_root, project["root"])
            assert project["id"] != other_id
        roots.append((project["root"], project["id"]))
        assert project["source_roots"] == sorted(project["source_roots"])
        for source_root in project["source_roots"]:
            _assert_path(source_root)
            assert _under(source_root, project["root"])
        if project["config_path"] is not None:
            _assert_path(project["config_path"])
            assert _under(project["config_path"], project["root"])
        assert project["file_ids"] == sorted(set(project["file_ids"]))
        assert all(_id_kind(file_id) == "file" for file_id in project["file_ids"])
    assert value["config"]["projects"] == value["projects"]
    assert value["request"]["projects"] == [project["root"] for project in value["projects"]]
    assert value["request"]["targets"] == value["targets"]
    _assert_target_keys(value["targets"])
    assert value["request"]["formats"] == value["formats"]
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
    assert descriptor["compatibility_id"] == recompute_compatibility_id(descriptor)


def validate_limits(limits: dict[str, Any]) -> None:
    assert set(limits) == {"max_entities", *LIMIT_DEFAULTS}
    assert 1 <= limits["max_entities"] <= 100000
    for name, expected in LIMIT_DEFAULTS.items():
        assert limits[name] == expected, name


def validate_limits_consistency(*projections: dict[str, Any]) -> None:
    assert projections
    for projection in projections:
        validate_limits(projection)
    first = projections[0]
    assert all(projection == first for projection in projections[1:])


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
    return {record_id: record for record_id, record in zip(ids, records, strict=True)}


def _assert_unique(values: list[Any]) -> None:
    encoded = [canonical_json_bytes(value) for value in values]
    assert len(encoded) == len(set(encoded))


def _assert_canonical(values: list[Any]) -> None:
    encoded = [canonical_json_bytes(value) for value in values]
    assert encoded == sorted(encoded)
    assert len(encoded) == len(set(encoded))


def _assert_target_keys(targets: list[str]) -> None:
    normalized = [unicodedata.normalize("NFC", target) for target in targets]
    assert normalized == targets
    _assert_canonical(targets)
    assert all(1 <= len(target) <= 4096 for target in targets)


def _assert_external_target(target: dict[str, Any]) -> None:
    assert target["kind"] in {"external", "unresolved"}
    assert PACKAGE_RE.fullmatch(target["safe_specifier"]), target
    exported_name = target["exported_name"]
    assert (
        exported_name is None
        or exported_name == "default"
        or re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", exported_name)
    )


def _validate_type_node(node: dict[str, Any], module_ids: set[str]) -> None:
    kind = node["kind"]
    if kind == "primitive":
        assert set(node) == {"kind", "name"}
    elif kind == "type_parameter":
        assert set(node) == {"kind", "ordinal"}
    elif kind == "redacted_literals":
        assert set(node) == {"kind", "base", "count"}
        assert node["base"] in {"boolean", "bigint", "number", "string"}
        assert node["count"] >= 1
    elif kind == "reference":
        assert set(node) == {"kind", "scope", "module", "exported_name", "type_arguments"}
        if node["scope"] == "repository":
            assert node["module"] in module_ids
            assert node["exported_name"] == "default" or re.fullmatch(
                r"[A-Za-z_$][A-Za-z0-9_$]*", node["exported_name"]
            )
        elif node["scope"] == "external":
            assert PACKAGE_RE.fullmatch(node["module"])
            assert node["exported_name"] != "" and node["exported_name"] is not None
        else:
            assert node["scope"] == "trusted"
            assert node["module"] in TRUSTED_REFERENCE_MODULES
            if node["module"] != "typescript/lib":
                assert node["exported_name"] is not None
            assert (
                node["exported_name"] is None
                or node["exported_name"] == "default"
                or re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", node["exported_name"])
            )
        for child in node["type_arguments"]:
            _validate_type_node(child, module_ids)
    elif kind == "array":
        assert set(node) == {"kind", "element", "readonly"}
        _validate_type_node(node["element"], module_ids)
    elif kind == "tuple":
        assert set(node) == {"kind", "elements", "rest", "readonly"}
        for element in node["elements"]:
            assert set(element) == {"type", "optional"}
            _validate_type_node(element["type"], module_ids)
        if node["rest"] is not None:
            _validate_type_node(node["rest"], module_ids)
    elif kind == "function":
        assert set(node) == {
            "kind",
            "type_parameter_count",
            "this_type",
            "parameters",
            "return_type",
        }
        if node["this_type"] is not None:
            _validate_type_node(node["this_type"], module_ids)
        for parameter in node["parameters"]:
            assert set(parameter) == {"type", "optional", "rest"}
            _validate_type_node(parameter["type"], module_ids)
        _validate_type_node(node["return_type"], module_ids)
    elif kind in {"union", "intersection"}:
        assert set(node) == {"kind", "members"}
        assert node["members"]
        _assert_canonical(node["members"])
        for child in node["members"]:
            _validate_type_node(child, module_ids)
    elif kind == "object":
        assert set(node) == {"kind", "properties", "index_signatures", "call_signatures"}
        _assert_canonical([prop["name"] for prop in node["properties"]])
        _assert_canonical([item["key_type"] for item in node["index_signatures"]])
        _assert_canonical(node["call_signatures"])
        for prop in node["properties"]:
            assert set(prop) == {"name", "type", "optional", "readonly"}
            assert unicodedata.normalize("NFC", prop["name"]) == prop["name"]
            _validate_type_node(prop["type"], module_ids)
        for signature in node["index_signatures"]:
            assert set(signature) == {"key_type", "value_type", "readonly"}
            _validate_type_node(signature["value_type"], module_ids)
        for signature in node["call_signatures"]:
            assert set(signature) == {
                "type_parameter_count",
                "this_type",
                "parameters",
                "return_type",
            }
            if signature["this_type"] is not None:
                _validate_type_node(signature["this_type"], module_ids)
            for parameter in signature["parameters"]:
                assert set(parameter) == {"type", "optional", "rest"}
                _validate_type_node(parameter["type"], module_ids)
            _validate_type_node(signature["return_type"], module_ids)
    else:
        assert kind == "opaque"
        assert set(node) == {"kind", "reason"}


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
        entry = catalog[diagnostic["code"]]
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
        entry = catalog[diagnostic["code"]]
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
        _assert_path(project["root"])
        for other_root, other_id in roots:
            assert not _under(project["root"], other_root)
            assert not _under(other_root, project["root"])
            assert project["id"] != other_id
        roots.append((project["root"], project["id"]))
        assert project["file_ids"] == sorted(project["file_ids"])
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
        assert roles == sorted(roles, key=ROLE_ORDER.__getitem__)
        assert file_record["effective_role"] == max(roles, key=ROLE_ORDER.__getitem__)
        files_by_project[file_record["project_id"]].append(file_record["id"])
    for project_id, project in project_records.items():
        assert project["file_ids"] == sorted(files_by_project[project_id])

    for module in module_records.values():
        assert module["kind"] == "module"
        assert module["project_id"] in project_records
        _assert_path(module["path"])
        assert module["derived_roles"] == sorted(module["derived_roles"])
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
    for member in member_records.values():
        if member["kind"] == "export_binding":
            assert member["owner_id"] in module_records
            assert member["target_component_id"] in component_records
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
            _validate_type_node(member["type_node"], set(module_records))
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

    _validate_model_diagnostics(model["diagnostics"])

    counts = model["coverage"]["counts"]
    for collection in COLLECTIONS:
        assert counts[collection] == len(collections[collection])
    assert counts["published"] == sum(len(collections[collection]) for collection in COLLECTIONS)
    assert counts["published"] <= counts["discovered"]
    assert counts["excluded"] >= 0
    assert counts["failed"] >= 0


def validate_request_files(request: dict[str, Any]) -> None:
    _assert_target_keys(request["targets"])
    project_ids = [project["id"] for project in request["projects"]]
    assert project_ids == sorted(project_ids)
    assert len(project_ids) == len(set(project_ids))
    assert all(_id_kind(project_id) == "project" for project_id in project_ids)
    roots = [(project["root"], project["id"]) for project in request["projects"]]
    for index, (root, project_id) in enumerate(roots):
        assert request["projects"][index]["kind"] == "project"
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
        assert file_record["project_id"] in project_set
        _assert_path(file_record["path"])
        matching_roots = [
            project_id for root, project_id in roots if _under(file_record["path"], root)
        ]
        assert matching_roots == [file_record["project_id"]]
        roles = file_record["roles"]
        assert roles == sorted(roles, key=ROLE_ORDER.__getitem__)
        assert file_record["effective_role"] == max(roles, key=ROLE_ORDER.__getitem__)
        files_by_project[file_record["project_id"]].append(file_record["id"])
        file_keys.append((file_record["project_id"], file_record["path"]))
        encoded = file_record["content_base64"]
        decoded = base64.b64decode(encoded, validate=True)
        assert base64.b64encode(decoded).decode("ascii") == encoded
        assert file_record["size_bytes"] == len(decoded)
        assert hashlib.sha256(decoded).hexdigest() == file_record["sha256"]
        total_decoded_bytes += len(decoded)
    _assert_unique(file_keys)
    assert total_decoded_bytes <= LIMIT_DEFAULTS["max_decoded_bytes"]
    for project in request["projects"]:
        assert project["file_ids"] == sorted(files_by_project[project["id"]])


def validate_proof(
    proof: dict[str, Any],
    model: dict[str, Any],
    expected_targets: dict[str, tuple[str, ...]] | None = None,
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
        assert all(taint in TAINTS for taint in item["taints"])
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
    taint_closure = _taint_dependency_closure(discovered, tainted_ids)
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

    failure_ids = {root["id"] for root in proof["failure_roots"]}
    assert len(failure_ids) == len(proof["failure_roots"])
    for root in proof["failure_roots"]:
        assert root["id"].startswith("next:failure:")
        if root["path_ref"] is not None:
            _assert_path(root["path_ref"])
    all_discovered = set().union(*(set(records) for records in discovered.values()))
    for edge in proof["causal_edges"]:
        assert edge["source_id"] in all_discovered | failure_ids
        assert edge["record_id"] in all_discovered

    assert all(
        root["id"] in {edge["source_id"] for edge in proof["causal_edges"]}
        for root in proof["failure_roots"]
    )

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


def validate_trusted_environment(
    environment: dict[str, Any], target_paths: list[str] | None = None
) -> None:
    assert environment["reserved_module_specifiers"] == list(TRUSTED_MODULES)
    assert environment["reserved_global_names"] == list(TRUSTED_GLOBALS)
    files = environment["files"]
    assert [item["virtual_path"] for item in files] == sorted(
        item["virtual_path"] for item in files
    )
    assert len({item["virtual_path"] for item in files}) == len(files)
    file_digests = {item["sha256"] for item in files}
    for item in files:
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
    symbol_keys = [
        (item["source_kind"], item["source_name"], tuple(item["export_path"])) for item in symbols
    ]
    assert symbol_keys == sorted(symbol_keys)
    assert len(symbol_keys) == len(set(symbol_keys))
    for symbol in symbols:
        assert symbol["declaration_sha256"] in file_digests
        if symbol["source_kind"] == "module":
            assert symbol["source_name"] in TRUSTED_MODULES
        else:
            assert symbol["source_name"] in TRUSTED_GLOBALS
    assert environment["sha256"] == digest(_without(environment, "sha256"))


def validate_no_trusted_shadowing(
    declarations: list[dict[str, str]], environment: dict[str, Any]
) -> None:
    """Reject target declarations that could augment a trusted namespace."""

    reserved_modules = set(environment["reserved_module_specifiers"])
    reserved_globals = set(environment["reserved_global_names"])
    for declaration in declarations:
        assert set(declaration) == {"source_kind", "source_name", "operation"}
        assert declaration["source_kind"] in {"module", "global"}
        assert declaration["operation"] in {"declare", "augment", "redirect"}
        if declaration["source_kind"] == "module":
            assert declaration["source_name"] not in reserved_modules
        else:
            assert declaration["source_name"] not in reserved_globals


def validate_runtime_manifest(manifest: dict[str, Any]) -> None:
    members = manifest["members"]
    assert [item["path"] for item in members] == sorted(item["path"] for item in members)
    assert len({item["path"] for item in members}) == len(members)
    for item in members:
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
    assert manifest["build_input_digest"] == digest({"members": members, "licenses": licenses})
    assert manifest["build_output_digest"] == digest({"members": members})


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
        ".. prop/import/export member",
        "--> static_import|literal_dynamic_import",
        "..> jsx_render|component_wrap",
        "marker=client_entry|router_context=<context>|client_dependency|server_candidate|unknown",
        "marker=partial_safe",
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
        elif member["kind"] == "export_binding":
            owner = f"N_M_{member['owner_id'].split(':')[-1]}"
            label = f"export {escape_plantuml_label(member['exported_name'])}"
        else:
            owner = f"N_M_{member['owner_id'].split(':')[-1]}"
            label = f"import {escape_plantuml_label(member['imported_name'])}"
        lines.append(f'{owner} .. "{label}" : {member["id"]}')
    for relation in sorted(model["relations"], key=lambda item: item["id"]):
        if relation["kind"] in {"static_import", "literal_dynamic_import"}:
            source = f"N_M_{relation['source_id'].split(':')[-1]}"
            target = relation["target"]
            target_alias = (
                f"N_M_{target['module_id'].split(':')[-1]}"
                if target["kind"] == "internal"
                else f"X_{external_target_digest(target)}"
            )
            lines.append(f"{source} --> {target_alias} : {relation['kind']}")
        elif relation["kind"] == "jsx_render":
            source = f"N_C_{relation['source_id'].split(':')[-1]}"
            target = relation["target"]
            target_alias = (
                f"N_C_{target['component_id'].split(':')[-1]}"
                if target["kind"] == "internal"
                else f"X_{external_target_digest(target)}"
            )
            lines.append(f"{source} ..> {target_alias} : jsx_render")
        else:
            source = f"N_C_{relation['source_id'].split(':')[-1]}"
            target = f"N_C_{relation['target_component_id'].split(':')[-1]}"
            lines.append(f"{source} ..> {target} : component_wrap")
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
        ".. prop/import/export member",
        "--> static_import|literal_dynamic_import",
        "..> jsx_render|component_wrap",
        "marker=client_entry|router_context=<context>|client_dependency|server_candidate|unknown",
        "marker=partial_safe",
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

    external_targets = {
        external_target_digest(relation["target"]): relation["target"]
        for relation in model["relations"]
        if relation.get("target") is not None and relation["target"]["kind"] != "internal"
    }
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
        elif member["kind"] == "export_binding":
            label = f"export {escape_plantuml_label(member['exported_name'])}"
        else:
            label = f"import {escape_plantuml_label(member['imported_name'])}"
        assert lines[cursor] == (f'{owner_prefix}_{suffix} .. "{label}" : {member["id"]}')
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
            expected = f"{source} --> {target_alias} : {relation['kind']}"
        elif relation["kind"] == "jsx_render":
            source = f"N_C_{relation['source_id'].split(':')[-1]}"
            target = relation["target"]
            target_alias = (
                f"N_C_{target['component_id'].split(':')[-1]}"
                if target["kind"] == "internal"
                else f"X_{external_target_digest(target)}"
            )
            expected = f"{source} ..> {target_alias} : jsx_render"
        else:
            expected = (
                f"N_C_{relation['source_id'].split(':')[-1]} ..> "
                f"N_C_{relation['target_component_id'].split(':')[-1]} : component_wrap"
            )
        assert lines[cursor] == expected
        cursor += 1
    assert lines[cursor] == "@enduml"
    assert cursor + 1 == len(lines)
