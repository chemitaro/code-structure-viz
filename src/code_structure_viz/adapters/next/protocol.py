from __future__ import annotations

import base64
import hashlib
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal

from code_structure_viz.semantic.canonical_json import encode_sorted_canonical_json
from code_structure_viz.source.targets import PathTarget, parse_target

from .source_acquisition import DEFAULT_NEXT_LIMITS, SourceAcquisitionSeal

_REQUEST_SCHEMA = "code-structure-viz.next-adapter-request/v1"
_PROTOCOL = "code-structure-viz.next-adapter/v1"
_TRUSTED_SCHEMA = "code-structure-viz.next-trusted-types/v1"
_TRUSTED_ENVIRONMENT_VERSION = "1"
_TRUSTED_SEMANTIC_PROFILE_ID = "next-trusted-profile-v1"
_ROLES = ("control", "context", "program")
_ROLE_PRECEDENCE = {"control": 3, "context": 2, "program": 1}
_FORMATS = ("semantic-json", "plantuml")
_BUDGET_SOURCES = {"builtin", "repository", "explicit", "cli", "unobserved"}
_SELECTORS = {None, "manifest", "next:semantic-json", "next:plantuml"}
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


class NextAdapterRequestError(ValueError):
    """A bounded request cannot be sent to the adapter."""

    def __init__(
        self,
        code: Literal["CSV-NEXT-LIMIT-001"],
        stage: Literal["stdin_encode"],
    ) -> None:
        if code != "CSV-NEXT-LIMIT-001" or stage != "stdin_encode":
            raise ValueError("unsupported Next adapter request failure code/stage")
        self.code = code
        self.stage = stage
        super().__init__(f"{code} at {stage}")


@dataclass(frozen=True, slots=True, init=False)
class NextAdapterRequest:
    """Immutable wire authority; source text is retained only in its bytes."""

    canonical_bytes: bytes = field(repr=False)
    request_id: str
    source_seal_id: str = field(repr=False)

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("NextAdapterRequest instances are created by build_next_adapter_request")

    @classmethod
    def _from_builder(
        cls, *, canonical_bytes: bytes, request_id: str, source_seal_id: str
    ) -> NextAdapterRequest:
        instance = object.__new__(cls)
        object.__setattr__(instance, "canonical_bytes", canonical_bytes)
        object.__setattr__(instance, "request_id", request_id)
        object.__setattr__(instance, "source_seal_id", source_seal_id)
        return instance


def build_next_adapter_request(
    seal: SourceAcquisitionSeal,
    *,
    adapter_version: str,
    trusted_type_environment: Mapping[str, object],
    targets: Sequence[str],
    run_context: Mapping[str, object],
) -> NextAdapterRequest:
    """Build a canonical private request using only bytes owned by ``seal``.

    Project/file membership, roles, content, and limits are derived exclusively
    from the source seal. Other inputs are already-resolved owner values; none
    may supply or replace source data.
    """

    if not isinstance(seal, SourceAcquisitionSeal):
        raise TypeError("request construction requires a SourceAcquisitionSeal")
    seal.__post_init__()
    if not isinstance(adapter_version, str) or _SEMVER.fullmatch(adapter_version) is None:
        raise ValueError("adapter version must be a stable semantic version")

    plan = seal.final_plan
    limits = _resolved_limits(plan.get("limits"))
    trusted = _trusted_environment(trusted_type_environment, plan.get("trusted_environment_digest"))
    context = _run_context(run_context, expected_budget=limits["max_entities"])
    canonical_targets = _targets(targets)

    source_by_path = {item.path.as_posix(): item for item in seal.source_view.files}
    if len(source_by_path) != len(seal.source_view.files):
        raise ValueError("sealed source paths must be unique")

    project_rows = plan.get("projects")
    role_rows = plan.get("file_role_map")
    if not isinstance(project_rows, list) or not project_rows:
        raise ValueError("a complete source seal must contain project rows")
    if not isinstance(role_rows, list):
        raise ValueError("a complete source seal must contain file-role rows")
    if len(project_rows) > 1000 or len(role_rows) > limits["max_files"]:
        raise ValueError("sealed source exceeds project or file count contract")

    projects_by_root: dict[str, dict[str, Any]] = {}
    for project in project_rows:
        if not isinstance(project, dict):
            raise ValueError("sealed project rows must be objects")
        root = project.get("root")
        source_roots = project.get("source_roots")
        config_path = project.get("config_path")
        compiler_options = project.get("compiler_options")
        if (
            not isinstance(root, str)
            or not isinstance(source_roots, list)
            or not isinstance(compiler_options, dict)
            or (config_path is not None and not isinstance(config_path, str))
            or root in projects_by_root
        ):
            raise ValueError("sealed project rows are invalid")
        _require_path(f"path:{root}")
        for source_root in source_roots:
            if not isinstance(source_root, str) or not _under(source_root, root):
                raise ValueError("sealed source roots must remain within their project")
            _require_path(f"path:{source_root}")
        if config_path is not None:
            _require_path(f"path:{config_path}")
            if not _under(config_path, root):
                raise ValueError("sealed config paths must remain within their project")
        projects_by_root[root] = project

    all_roots = sorted(projects_by_root, key=lambda value: value.encode("utf-8"))
    matrix_roots = {entry.project_root for entry in seal.package_applicability.entries}
    if set(all_roots) != matrix_roots:
        raise ValueError("sealed projects must match package applicability roots")
    for index, root in enumerate(all_roots):
        for other_root in all_roots[:index]:
            if _under(root, other_root) or _under(other_root, root):
                raise ValueError("sealed project roots must not overlap")

    applicable_roots = set(seal.package_applicability.applicable_projects)
    if not applicable_roots or not applicable_roots.issubset(projects_by_root):
        raise ValueError("a complete source seal must contain applicable project rows")

    project_records: dict[str, dict[str, Any]] = {}
    project_id_by_root: dict[str, str] = {}
    roots = sorted(applicable_roots, key=lambda value: value.encode("utf-8"))
    for root in roots:
        project = projects_by_root[root]
        identity = _identity_digest("project", {"root": root})
        project_id = f"next:project:{identity}"
        config_fields = {
            "root": root,
            "source_roots": list(project["source_roots"]),
            "config_path": project["config_path"],
            "compiler_options": project["compiler_options"],
        }
        project_records[root] = {
            "kind": "project",
            "id": project_id,
            **config_fields,
            "config_digest": _digest(config_fields),
            "file_ids": [],
        }
        project_id_by_root[root] = project_id

    file_records: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    applicable_role_paths: set[str] = set()
    decoded_bytes = 0
    for role_row in role_rows:
        if not isinstance(role_row, dict):
            raise ValueError("sealed file-role rows must be objects")
        path = role_row.get("path")
        root = role_row.get("project_root")
        roles = role_row.get("roles")
        effective_role = role_row.get("effective_role")
        if (
            not isinstance(path, str)
            or not isinstance(root, str)
            or root not in projects_by_root
            or not isinstance(roles, list)
            or path in seen_paths
            or not _under(path, root)
        ):
            raise ValueError("sealed file-role rows are invalid")
        _require_path(f"path:{path}")
        if (
            not roles
            or any(role not in _ROLES for role in roles)
            or roles != sorted(set(roles), key=_ROLES.index)
            or effective_role != max(roles, key=_ROLE_PRECEDENCE.__getitem__)
        ):
            raise ValueError("sealed source roles are not canonical")
        source_file = source_by_path.get(path)
        if source_file is None:
            raise ValueError("sealed file-role rows must match frozen source bytes")
        content = source_file.content
        if (
            source_file.size_bytes != len(content)
            or source_file.size_bytes > limits["max_file_bytes"]
            or hashlib.sha256(content).hexdigest() != source_file.sha256
        ):
            raise ValueError("sealed source file identity is inconsistent")
        seen_paths.add(path)
        if root not in applicable_roots:
            continue

        applicable_role_paths.add(path)
        decoded_bytes += len(content)
        if decoded_bytes > limits["max_decoded_bytes"]:
            raise ValueError("sealed source exceeds the decoded-byte contract")

        project_id = project_id_by_root[root]
        file_id = f"next:file:{_identity_digest('file', {'project_id': project_id, 'path': path})}"
        file_records.append(
            {
                "kind": "file",
                "id": file_id,
                "path": path,
                "project_id": project_id,
                "roles": list(roles),
                "effective_role": effective_role,
                "size_bytes": source_file.size_bytes,
                "sha256": source_file.sha256,
                "content_base64": base64.b64encode(content).decode("ascii"),
            }
        )
        project_records[root]["file_ids"].append(file_id)

    if seen_paths != set(source_by_path):
        raise ValueError("sealed file-role rows must match the complete frozen source set")
    if {record["path"] for record in file_records} != applicable_role_paths:
        raise ValueError("adapter request files must match applicable project roles")
    file_records.sort(key=lambda value: value["id"])
    projects = [project_records[root] for root in roots]
    for project in projects:
        project["file_ids"].sort()

    request: dict[str, Any] = {
        "schema": _REQUEST_SCHEMA,
        "protocol": _PROTOCOL,
        "adapter_version": adapter_version,
        "trusted_type_environment": trusted,
        "projects": projects,
        "files": file_records,
        "targets": canonical_targets,
        "limits": limits,
        "run_context": context,
    }
    _validate_request_json_limits(request, limits)
    request_id = _digest(request)
    request["request_id"] = request_id
    canonical_bytes = encode_sorted_canonical_json(request)
    if canonical_bytes.endswith(b"\n"):
        canonical_bytes = canonical_bytes[:-1]
    if len(canonical_bytes) > limits["max_encoded_stdin_bytes"]:
        raise NextAdapterRequestError("CSV-NEXT-LIMIT-001", "stdin_encode")
    return NextAdapterRequest._from_builder(
        canonical_bytes=canonical_bytes,
        request_id=request_id,
        source_seal_id=seal.seal_id,
    )


def _resolved_limits(value: object) -> dict[str, int]:
    if not isinstance(value, dict) or set(value) != set(DEFAULT_NEXT_LIMITS):
        raise ValueError("source seal limits must match the closed Next v1 set")
    limits: dict[str, int] = {}
    for key, default in DEFAULT_NEXT_LIMITS.items():
        item = value.get(key)
        if type(item) is not int:
            raise ValueError("source seal limits must be integers")
        if key == "max_entities":
            if not 1 <= item <= 100_000:
                raise ValueError("resolved entity limit is outside the v1 range")
        elif item != default:
            raise ValueError("source seal limits must use the v1 contract values")
        limits[key] = item
    return limits


def _trusted_environment(value: Mapping[str, object], expected_digest: object) -> dict[str, str]:
    keys = {"schema", "environment_version", "semantic_profile_id", "sha256"}
    if not isinstance(value, Mapping) or set(value) != keys:
        raise ValueError("trusted type environment descriptor is not closed")
    result = dict(value)
    if (
        result["schema"] != _TRUSTED_SCHEMA
        or result["environment_version"] != _TRUSTED_ENVIRONMENT_VERSION
        or result["semantic_profile_id"] != _TRUSTED_SEMANTIC_PROFILE_ID
        or not isinstance(result["sha256"], str)
        or _DIGEST.fullmatch(result["sha256"]) is None
        or result["sha256"] != expected_digest
    ):
        raise ValueError("trusted type environment must match the source-seal digest")
    return {key: str(item) for key, item in result.items()}


def _validate_request_json_limits(value: object, limits: Mapping[str, int]) -> None:
    """Bound every generated request array and JSON traversal before encoding.

    ``max_total_array_items`` is intentionally response-only in v1; the
    private request uses the per-array cap plus the common depth/string bounds.
    """

    pending: list[tuple[object, int]] = [(value, 1)]
    while pending:
        current, depth = pending.pop()
        if depth > limits["max_json_nesting"]:
            raise NextAdapterRequestError("CSV-NEXT-LIMIT-001", "stdin_encode")
        if isinstance(current, str):
            if len(current.encode("utf-8")) > limits["max_json_string_bytes"]:
                raise NextAdapterRequestError("CSV-NEXT-LIMIT-001", "stdin_encode")
            continue
        if isinstance(current, Mapping):
            for key, item in current.items():
                if not isinstance(key, str):
                    raise ValueError("request JSON object keys must be strings")
                if len(key.encode("utf-8")) > limits["max_json_string_bytes"]:
                    raise NextAdapterRequestError("CSV-NEXT-LIMIT-001", "stdin_encode")
                pending.append((item, depth + 1))
            continue
        if isinstance(current, (list, tuple)):
            if len(current) > limits["max_array_items"]:
                raise NextAdapterRequestError("CSV-NEXT-LIMIT-001", "stdin_encode")
            pending.extend((item, depth + 1) for item in current)


def _run_context(value: Mapping[str, object], *, expected_budget: int) -> dict[str, Any]:
    keys = {
        "requested_formats",
        "budget_requested",
        "budget_resolved",
        "budget_source",
        "stdout_selector",
    }
    if not isinstance(value, Mapping) or set(value) != keys:
        raise ValueError("run context must use the closed Next v1 fields")
    raw_formats = value["requested_formats"]
    if (
        not isinstance(raw_formats, (list, tuple))
        or not raw_formats
        or any(not isinstance(item, str) or item not in _FORMATS for item in raw_formats)
    ):
        raise ValueError("requested formats are invalid")
    formats = list(raw_formats)
    if len(formats) != len(set(formats)) or formats != sorted(formats, key=_FORMATS.index):
        raise ValueError("requested formats must be unique and canonical")
    budget_requested = value["budget_requested"]
    budget_resolved = value["budget_resolved"]
    budget_source = value["budget_source"]
    selector = value["stdout_selector"]
    if budget_requested is not None and (
        type(budget_requested) is not int or not 1 <= budget_requested <= 100_000
    ):
        raise ValueError("requested entity budget is invalid")
    if budget_resolved is not None and (
        type(budget_resolved) is not int or not 1 <= budget_resolved <= 100_000
    ):
        raise ValueError("resolved entity budget is invalid")
    if (
        not isinstance(budget_source, str)
        or budget_source not in _BUDGET_SOURCES
        or (selector is not None and not isinstance(selector, str))
        or selector not in _SELECTORS
    ):
        raise ValueError("run context source or selector is invalid")
    if budget_resolved != expected_budget:
        raise ValueError("run context budget must match sealed limits")
    if budget_resolved is None:
        if budget_requested is not None or budget_source != "unobserved":
            raise ValueError("unobserved budgets must have null values")
    elif budget_source == "unobserved":
        raise ValueError("resolved budgets cannot be unobserved")
    if budget_source == "builtin":
        if budget_requested is not None:
            raise ValueError("built-in budgets have no requested override")
    elif budget_source != "unobserved" and budget_requested is None:
        raise ValueError("non-built-in resolved budgets require a requested value")
    if (
        selector is not None
        and selector != "manifest"
        and selector.removeprefix("next:") not in formats
    ):
        raise ValueError("stdout selector must be included in requested formats")
    return {
        "requested_formats": formats,
        "budget_requested": budget_requested,
        "budget_resolved": budget_resolved,
        "budget_source": budget_source,
        "stdout_selector": selector,
    }


def _targets(value: Sequence[str]) -> list[str]:
    if isinstance(value, (str, bytes)) or len(value) > 10_000:
        raise ValueError("targets must be a bounded sequence of canonical paths")
    targets = list(value)
    paths: list[str] = []
    for target in targets:
        if not isinstance(target, str):
            raise ValueError("targets must be strings")
        parsed = parse_target(target, domain="next")
        if not isinstance(parsed, PathTarget) or target != f"path:{parsed.value.as_posix()}":
            raise ValueError("targets must already be canonical Next path keys")
        paths.append(parsed.value.as_posix())
    if paths != sorted(set(paths), key=lambda path: path.encode("utf-8")):
        raise ValueError("targets must be unique and sorted by UTF-8 path")
    return targets


def _require_path(target: str) -> str:
    parsed = parse_target(target, domain="next")
    if not isinstance(parsed, PathTarget) or target != f"path:{parsed.value.as_posix()}":
        raise ValueError("sealed paths must be canonical repository-relative paths")
    return parsed.value.as_posix()


def _under(path: str, root: str) -> bool:
    return root == "." or path == root or path.startswith(f"{root.rstrip('/')}/")


def _identity_digest(kind: str, identity: dict[str, str]) -> str:
    return _digest({"kind": kind, "version": 1, "identity": identity})


def _digest(value: object) -> str:
    canonical = encode_sorted_canonical_json(value)
    if not canonical.endswith(b"\n"):
        raise AssertionError("canonical JSON encoder must append one LF")
    return hashlib.sha256(canonical[:-1]).hexdigest()
