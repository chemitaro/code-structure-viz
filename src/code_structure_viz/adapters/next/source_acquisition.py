from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Protocol, cast

from code_structure_viz.adapters.next.applicability import (
    PackageApplicabilityMatrix,
    PackageApplicabilityState,
    derive_package_applicability_matrix,
)
from code_structure_viz.adapters.next.configuration import (
    SOURCE_PLAN_HARD_EXCLUSIONS,
    NextConfigurationError,
    ResolvedProjectConfiguration,
    is_hard_excluded_source_path,
    parse_control_jsonc,
    resolve_local_extends_path,
    resolve_project_configuration,
)
from code_structure_viz.adapters.next.source_graph import derive_source_graph
from code_structure_viz.semantic.canonical_json import encode_canonical_json
from code_structure_viz.source.source_view import (
    SourceDriftError,
    SourceReadFailure,
    SourceReadFailureKind,
    SourceView,
)

SOURCE_PLAN_PROGRAM_SUFFIXES = (".js", ".jsx", ".ts", ".tsx")
SOURCE_PLAN_CONTEXT_SUFFIXES = (".d.ts",)
SOURCE_PLAN_CONTROL_CANDIDATES = ("tsconfig.json", "jsconfig.json")
_DEFAULT_NEXT_LIMIT_VALUES = {
    "max_entities": 500,
    "max_files": 20_000,
    "max_file_bytes": 4_194_304,
    "max_decoded_bytes": 67_108_864,
    "max_encoded_stdin_bytes": 100_663_296,
    "max_json_nesting": 64,
    "max_json_string_bytes": 8_388_608,
    "max_array_items": 100_000,
    "max_total_array_items": 100_000,
    "max_collection_items": 20_000,
    "max_model_records": 10_000,
    "max_stdout_bytes": 16_777_216,
    "max_adapter_response_bytes": 16_777_216,
    "max_selected_stdout_bytes": 16_777_216,
    "max_stderr_bytes": 65_536,
    "max_adapter_stderr_capture_bytes": 65_536,
    "max_adapter_stdout_capture_bytes": 16_777_216,
    "timeout_seconds": 60,
    "v8_old_space_mib": 512,
    "max_type_depth": 16,
    "max_type_nodes_per_prop": 512,
    "max_union_members": 64,
    "max_intersection_members": 64,
    "max_nested_properties": 256,
    "max_signatures_per_component": 16,
    "max_flow_visits": 10_000,
    "max_alias_edges": 64,
}
DEFAULT_NEXT_LIMITS = MappingProxyType(_DEFAULT_NEXT_LIMIT_VALUES)


class NextSourceAcquisitionError(RuntimeError):
    """A typed, non-content-bearing failure during Next source acquisition."""

    def __init__(self, code: str, stage: str, *, path: str | None = None) -> None:
        self.code = code
        self.stage = stage
        self.path = path
        super().__init__(code)


class NextSourceIntegrityError(NextSourceAcquisitionError):
    """A fatal inventory or revision mismatch during source sealing."""

    def __init__(self, *, path: str | None = None) -> None:
        super().__init__("CSV-NEXT-SOURCE-INTEGRITY-001", "source_integrity", path=path)


@dataclass(frozen=True, slots=True)
class NextNotApplicableAcquisition:
    package_applicability: PackageApplicabilityMatrix


@dataclass(frozen=True, slots=True, init=False)
class SourceAcquisitionSeal:
    """Plan and frozen view returned together from one successful source seal."""

    plan_bytes: bytes = field(repr=False)
    plan_digest: str
    source_view: SourceView
    source_view_fingerprint: str
    seal_id: str
    package_applicability: PackageApplicabilityMatrix = field(repr=False)

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        raise TypeError("SourceAcquisitionSeal instances are created by seal_source_acquisition")

    @classmethod
    def _from_acquisition(
        cls,
        *,
        plan_bytes: bytes,
        plan_digest: str,
        source_view: SourceView,
        source_view_fingerprint: str,
        seal_id: str,
        package_applicability: PackageApplicabilityMatrix,
    ) -> SourceAcquisitionSeal:
        instance = object.__new__(cls)
        object.__setattr__(instance, "plan_bytes", plan_bytes)
        object.__setattr__(instance, "plan_digest", plan_digest)
        object.__setattr__(instance, "source_view", source_view)
        object.__setattr__(instance, "source_view_fingerprint", source_view_fingerprint)
        object.__setattr__(instance, "seal_id", seal_id)
        object.__setattr__(instance, "package_applicability", package_applicability)
        instance.__post_init__()
        return instance

    def __post_init__(self) -> None:
        plan = json.loads(self.plan_bytes)
        if encode_canonical_json(plan) != self.plan_bytes:
            raise ValueError("source plan bytes must be canonical JSON")
        actual_plan_digest = hashlib.sha256(self.plan_bytes).hexdigest()
        if actual_plan_digest != self.plan_digest:
            raise ValueError("source plan bytes do not match their digest")
        if self.source_view.fingerprint != self.source_view_fingerprint:
            raise ValueError("source view fingerprint does not match the sealed view")
        graph_digest = plan["source_graph"]["graph_digest"]
        graph_without_digest = {
            key: value for key, value in plan["source_graph"].items() if key != "graph_digest"
        }
        if _digest(graph_without_digest) != graph_digest:
            raise ValueError("source graph digest does not match its sealed graph")
        if graph_digest != self.source_view.source_graph_digest:
            raise ValueError("source plan and view must share one source graph digest")
        view_value = self.source_view.fingerprint_value()
        if (
            hashlib.sha256(encode_canonical_json(view_value)).hexdigest()
            != self.source_view_fingerprint
        ):
            raise ValueError("source view fingerprint does not match its canonical contents")
        expected_paths = {row["path"] for row in plan["file_role_map"]}
        actual_files = {item.path.as_posix(): item for item in self.source_view.files}
        if len(actual_files) != len(self.source_view.files) or set(actual_files) != expected_paths:
            raise ValueError("source plan file roles must match the sealed source view")
        if self.source_view.failures:
            raise ValueError("a complete source seal cannot contain source-view failures")
        for node in plan["source_graph"]["nodes"]:
            source_file = actual_files.get(node["path"])
            if source_file is None or source_file.sha256 != node["content_sha256"]:
                raise ValueError("source graph nodes must match the sealed source view files")
        expected_seal_id = _digest(
            {
                "plan_digest": self.plan_digest,
                "source_view_fingerprint": self.source_view_fingerprint,
                "source_graph_digest": graph_digest,
            }
        )
        if self.seal_id != expected_seal_id:
            raise ValueError("source acquisition seal identity is inconsistent")

    @property
    def final_plan(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(self.plan_bytes))

    def recompute_plan_digest(self) -> str:
        return hashlib.sha256(encode_canonical_json(self.final_plan)).hexdigest()


NextSourceAcquisitionResult = NextNotApplicableAcquisition | SourceAcquisitionSeal


@dataclass(frozen=True, slots=True)
class SourceDiscoveryIntent:
    """Caller-owned roots and fixed discovery rules, never resolved source data."""

    project_roots: tuple[str, ...]
    control_candidates: tuple[str, ...] = SOURCE_PLAN_CONTROL_CANDIDATES
    program_suffixes: tuple[str, ...] = SOURCE_PLAN_PROGRAM_SUFFIXES
    context_suffixes: tuple[str, ...] = SOURCE_PLAN_CONTEXT_SUFFIXES
    hard_exclusions: tuple[str, ...] = SOURCE_PLAN_HARD_EXCLUSIONS

    def __post_init__(self) -> None:
        if any(
            isinstance(value, (str, bytes))
            for value in (
                self.project_roots,
                self.control_candidates,
                self.program_suffixes,
                self.context_suffixes,
                self.hard_exclusions,
            )
        ):
            raise ValueError("discovery intent fields must be immutable path tuples")
        roots = tuple(self.project_roots)
        controls = tuple(self.control_candidates)
        program_suffixes = tuple(self.program_suffixes)
        context_suffixes = tuple(self.context_suffixes)
        hard_exclusions = tuple(self.hard_exclusions)
        derive_package_applicability_matrix({}, roots)
        allowed_controls = set(SOURCE_PLAN_CONTROL_CANDIDATES)
        if len(controls) != len(set(controls)) or not set(controls).issubset(allowed_controls):
            raise ValueError("discovery intent control candidates are invalid")
        canonical_controls = tuple(
            name for name in SOURCE_PLAN_CONTROL_CANDIDATES if name in controls
        )
        if program_suffixes != SOURCE_PLAN_PROGRAM_SUFFIXES:
            raise ValueError("discovery intent program suffixes are fixed")
        if context_suffixes != SOURCE_PLAN_CONTEXT_SUFFIXES:
            raise ValueError("discovery intent context suffixes are fixed")
        if hard_exclusions != SOURCE_PLAN_HARD_EXCLUSIONS:
            raise ValueError("discovery intent hard exclusions are fixed")
        ordered_roots = tuple(sorted(roots, key=lambda value: value.encode("utf-8")))
        for index, root in enumerate(ordered_roots):
            for other in ordered_roots[index + 1 :]:
                if root == "." or other.startswith(f"{root.rstrip('/')}/"):
                    raise ValueError("project roots must not overlap")
        object.__setattr__(self, "project_roots", ordered_roots)
        object.__setattr__(self, "control_candidates", canonical_controls)
        object.__setattr__(self, "program_suffixes", program_suffixes)
        object.__setattr__(self, "context_suffixes", context_suffixes)
        object.__setattr__(self, "hard_exclusions", hard_exclusions)


class NextSourceReader(Protocol):
    """Trusted read-once view of one repository path inventory."""

    def enumerate_paths(self) -> tuple[str, ...]: ...

    def read_once(self, path: str) -> bytes: ...


class NextSourceSealReader(NextSourceReader, Protocol):
    def seal(self, *, source_graph_digest: str | None = None) -> SourceView: ...


class _GuardedSourceReader:
    """Translate trusted descriptor-read failures into closed domain outcomes."""

    def __init__(
        self, reader: NextSourceSealReader, *, applicability_paths: frozenset[str]
    ) -> None:
        self._reader = reader
        self._applicability_paths = applicability_paths

    def enumerate_paths(self) -> tuple[str, ...]:
        try:
            return self._reader.enumerate_paths()
        except SourceDriftError as error:
            raise NextSourceIntegrityError() from error

    def read_once(self, path: str) -> bytes:
        try:
            return self._reader.read_once(path)
        except SourceDriftError as error:
            raise NextSourceIntegrityError(path=path) from error
        except SourceReadFailure as error:
            if error.kind in {
                SourceReadFailureKind.TOO_LARGE,
                SourceReadFailureKind.TOO_MANY_FILES,
            }:
                raise NextSourceAcquisitionError(
                    "CSV-NEXT-LIMIT-001", "limits", path=path
                ) from error
            if error.kind is SourceReadFailureKind.READ and path in self._applicability_paths:
                raise NextSourceAcquisitionError(
                    "CSV-NEXT-APPLICABILITY-002", "applicability"
                ) from error
            raise NextSourceAcquisitionError(
                "CSV-NEXT-SOURCE-003", "source_read", path=path
            ) from error

    def seal(self, *, source_graph_digest: str | None = None) -> SourceView:
        try:
            return self._reader.seal(source_graph_digest=source_graph_digest)
        except SourceDriftError as error:
            raise NextSourceIntegrityError() from error


@dataclass(frozen=True, slots=True)
class NextPackagePreflight:
    matrix: PackageApplicabilityMatrix
    frozen_package_bytes: tuple[tuple[str, bytes | None], ...] = field(repr=False)

    def __post_init__(self) -> None:
        observations = self.frozen_package_bytes
        if not isinstance(observations, tuple) or any(
            not isinstance(row, tuple) or len(row) != 2 for row in observations
        ):
            raise ValueError("package preflight observations must be immutable rows")
        if any(
            not isinstance(path, str) or (payload is not None and not isinstance(payload, bytes))
            for path, payload in observations
        ):
            raise ValueError("package preflight observations must contain frozen bytes")
        if observations != self.matrix.frozen_package_bytes:
            raise ValueError("package preflight bytes must match the applicability observation")


@dataclass(frozen=True, slots=True)
class NextConfigurationResolution:
    preflight: NextPackagePreflight
    projects: tuple[ResolvedProjectConfiguration, ...]
    frozen_control_bytes: tuple[tuple[str, bytes], ...] = field(repr=False)

    def __post_init__(self) -> None:
        projects = tuple(self.projects)
        controls = tuple(self.frozen_control_bytes)
        if any(
            not isinstance(row, tuple)
            or len(row) != 2
            or not isinstance(row[0], str)
            or not isinstance(row[1], bytes)
            for row in controls
        ):
            raise ValueError("frozen control observations must be immutable byte rows")
        if controls != tuple(sorted(controls, key=lambda row: row[0].encode("utf-8"))):
            raise ValueError("frozen control observations must use canonical path order")
        if len({path for path, _payload in controls}) != len(controls):
            raise ValueError("frozen control paths must be unique")
        expected_roots = self.preflight.matrix.applicable_projects
        if tuple(project.project_root for project in projects) != expected_roots:
            raise ValueError("resolved projects must match applicable project roots")
        observed_paths = {path for path, _payload in controls}
        if any(not set(project.control_paths).issubset(observed_paths) for project in projects):
            raise ValueError("resolved projects require their frozen control observations")
        object.__setattr__(self, "projects", projects)
        object.__setattr__(self, "frozen_control_bytes", controls)


class NextSourceAcquirer:
    """Own Next's causal transition from package bytes to source observation."""

    def __init__(self, reader: NextSourceReader) -> None:
        self._reader = reader
        self._started = False
        self._paths: tuple[str, ...] = ()
        self._path_set: frozenset[str] = frozenset()
        self._observed: dict[str, bytes] = {}
        self._preflight: NextPackagePreflight | None = None
        self._intent: SourceDiscoveryIntent | None = None

    def preflight(self, intent: SourceDiscoveryIntent) -> NextPackagePreflight:
        if self._started:
            raise RuntimeError("Next source acquisition is one-shot")
        self._started = True
        if not isinstance(intent, SourceDiscoveryIntent):
            raise TypeError("source acquisition requires a discovery intent")
        self._intent = intent
        roots = intent.project_roots

        paths = self._reader.enumerate_paths()
        if not isinstance(paths, tuple) or any(not isinstance(path, str) for path in paths):
            raise ValueError("source reader returned an invalid path inventory")
        if len(paths) != len(set(paths)):
            raise ValueError("source reader returned duplicate paths")
        self._paths = tuple(
            sorted(
                (path for path in paths if not _is_hard_excluded(path)),
                key=lambda path: path.encode("utf-8"),
            )
        )
        self._path_set = frozenset(self._paths)

        observations: list[tuple[str, bytes | None]] = []
        for root in roots:
            package_path = "package.json" if root == "." else f"{root}/package.json"
            payload = self._read_once(package_path) if package_path in self._path_set else None
            if payload is not None and not isinstance(payload, bytes):
                raise ValueError("source reader must return frozen package bytes")
            observations.append((package_path, payload))

        frozen_package_bytes = tuple(observations)
        matrix = derive_package_applicability_matrix(dict(frozen_package_bytes), roots)
        self._preflight = NextPackagePreflight(matrix, frozen_package_bytes)
        return self._preflight

    def resolve_configurations(
        self, preflight: NextPackagePreflight
    ) -> NextConfigurationResolution:
        if preflight is not self._preflight:
            raise ValueError("configuration resolution must use this acquisition's preflight")
        intent = self._intent
        if intent is None:
            raise RuntimeError("configuration resolution requires a completed package preflight")
        if preflight.matrix.aggregate_state is PackageApplicabilityState.MALFORMED:
            raise NextConfigurationError(
                "malformed package applicability evidence",
                path=next(
                    entry.package_path
                    for entry in preflight.matrix.entries
                    if entry.state is PackageApplicabilityState.MALFORMED
                ),
                code="CSV-NEXT-APPLICABILITY-002",
            )
        if preflight.matrix.aggregate_state is PackageApplicabilityState.NON_APPLICABLE:
            return NextConfigurationResolution(preflight, (), ())

        frozen_controls: dict[str, bytes] = {}
        resolved_projects: list[ResolvedProjectConfiguration] = []
        roots = preflight.matrix.applicable_projects
        for root in roots:
            config_path = next(
                (
                    self._project_control_path(root, name)
                    for name in intent.control_candidates
                    if self._project_control_path(root, name) in self._path_set
                ),
                None,
            )
            controls_for_project: dict[str, bytes] = {}
            if config_path is not None:
                queue = [config_path]
                while queue:
                    path = queue.pop(0)
                    if path in controls_for_project:
                        continue
                    payload = self._read_once(path)
                    controls_for_project[path] = payload
                    frozen_controls[path] = payload
                    value = parse_control_jsonc(payload, path=path)
                    if "extends" not in value:
                        continue
                    specifier = value["extends"]
                    if not isinstance(specifier, str):
                        raise NextConfigurationError("extends must be one local path", path=path)
                    parent_path = resolve_local_extends_path(
                        path, project_root=root, specifier=specifier
                    )
                    if parent_path not in self._path_set:
                        raise NextConfigurationError(
                            "extends control path is absent from the repository inventory",
                            path=parent_path,
                        )
                    queue.append(parent_path)

            package_and_control_bytes = {
                path: payload
                for path, payload in (
                    *preflight.frozen_package_bytes,
                    *controls_for_project.items(),
                )
                if payload is not None
            }
            resolved_projects.append(
                resolve_project_configuration(
                    package_and_control_bytes,
                    project_root=root,
                    inventory_paths=self._paths,
                    control_candidates=intent.control_candidates,
                )
            )

        frozen_control_bytes = tuple(
            sorted(frozen_controls.items(), key=lambda row: row[0].encode("utf-8"))
        )
        return NextConfigurationResolution(
            preflight,
            tuple(resolved_projects),
            frozen_control_bytes,
        )

    @staticmethod
    def _project_control_path(project_root: str, control_name: str) -> str:
        return control_name if project_root == "." else f"{project_root}/{control_name}"

    def _read_once(self, path: str) -> bytes:
        if path not in self._path_set:
            raise ValueError("source path is not in the frozen inventory")
        if path in self._observed:
            raise ValueError("source path bytes were requested more than once")
        payload = self._reader.read_once(path)
        if not isinstance(payload, bytes):
            raise ValueError("source reader must return frozen bytes")
        self._observed[path] = payload
        return payload


def _is_hard_excluded(path: str) -> bool:
    return is_hard_excluded_source_path(path)


def seal_source_acquisition(
    intent: SourceDiscoveryIntent,
    reader: NextSourceSealReader,
    *,
    trusted_environment_digest: str,
    max_entities: int = 500,
) -> NextSourceAcquisitionResult:
    """Acquire a Next source view and its complete source plan in one operation."""

    if not isinstance(intent, SourceDiscoveryIntent):
        raise TypeError("source acquisition requires a SourceDiscoveryIntent")
    if type(max_entities) is not int or not 1 <= max_entities <= 100_000:
        raise NextSourceAcquisitionError("CSV-NEXT-LIMIT-001", "limits")

    applicability_paths = frozenset(
        "package.json" if root == "." else f"{root}/package.json" for root in intent.project_roots
    )
    guarded_reader = _GuardedSourceReader(reader, applicability_paths=applicability_paths)
    acquirer = NextSourceAcquirer(guarded_reader)
    preflight = acquirer.preflight(intent)
    applicability = preflight.matrix
    if applicability.aggregate_state is PackageApplicabilityState.MALFORMED:
        raise NextSourceAcquisitionError(
            "CSV-NEXT-APPLICABILITY-002",
            "applicability",
            path=next(
                entry.package_path
                for entry in applicability.entries
                if entry.state is PackageApplicabilityState.MALFORMED
            ),
        )
    if applicability.aggregate_state is PackageApplicabilityState.NON_APPLICABLE:
        return NextNotApplicableAcquisition(applicability)

    if (
        not isinstance(trusted_environment_digest, str)
        or re.fullmatch(r"[0-9a-f]{64}", trusted_environment_digest) is None
    ):
        raise NextSourceAcquisitionError("CSV-NEXT-SOURCE-003", "trusted_environment")

    configuration = acquirer.resolve_configurations(preflight)
    configurations = {project.project_root: project for project in configuration.projects}
    source_paths = tuple(
        sorted(
            {path for project in configuration.projects for path in project.membership.paths},
            key=lambda path: path.encode("utf-8"),
        )
    )
    package_paths = {
        path for path, payload in preflight.frozen_package_bytes if payload is not None
    }
    control_paths = package_paths.union(
        path for project in configuration.projects for path in project.control_paths
    )
    final_paths = tuple(
        sorted(control_paths.union(source_paths), key=lambda path: path.encode("utf-8"))
    )
    limits = dict(DEFAULT_NEXT_LIMITS)
    limits["max_entities"] = max_entities
    if len(final_paths) > limits["max_files"]:
        raise NextSourceAcquisitionError("CSV-NEXT-LIMIT-001", "source_selection")

    contents = dict(acquirer._observed)
    total_bytes = sum(len(payload) for payload in contents.values())
    for path, payload in contents.items():
        if len(payload) > limits["max_file_bytes"]:
            raise NextSourceAcquisitionError("CSV-NEXT-LIMIT-001", "source_read", path=path)
    if total_bytes > limits["max_decoded_bytes"]:
        raise NextSourceAcquisitionError("CSV-NEXT-LIMIT-001", "source_read")

    for path in source_paths:
        if path in contents:
            continue
        payload = acquirer._read_once(path)
        if len(payload) > limits["max_file_bytes"]:
            raise NextSourceAcquisitionError("CSV-NEXT-LIMIT-001", "source_read", path=path)
        total_bytes += len(payload)
        if total_bytes > limits["max_decoded_bytes"]:
            raise NextSourceAcquisitionError("CSV-NEXT-LIMIT-001", "source_read", path=path)
        contents[path] = payload

    graph, local_extends = derive_source_graph(
        contents,
        intent.project_roots,
        configuration.projects,
    )
    plan = _build_source_plan(
        intent=intent,
        applicability=applicability,
        configurations=configurations,
        package_paths=package_paths,
        control_paths=control_paths,
        final_paths=final_paths,
        limits=limits,
        trusted_environment_digest=trusted_environment_digest,
        local_extends=local_extends,
        source_graph=graph,
    )
    plan_bytes = encode_canonical_json(plan)
    plan_digest = hashlib.sha256(plan_bytes).hexdigest()
    source_view = guarded_reader.seal(source_graph_digest=graph["graph_digest"])
    source_view_fingerprint = source_view.fingerprint
    seal_id = _digest(
        {
            "plan_digest": plan_digest,
            "source_view_fingerprint": source_view_fingerprint,
            "source_graph_digest": graph["graph_digest"],
        }
    )
    return SourceAcquisitionSeal._from_acquisition(
        plan_bytes=plan_bytes,
        plan_digest=plan_digest,
        source_view=source_view,
        source_view_fingerprint=source_view_fingerprint,
        seal_id=seal_id,
        package_applicability=applicability,
    )


def _build_source_plan(
    *,
    intent: SourceDiscoveryIntent,
    applicability: PackageApplicabilityMatrix,
    configurations: Mapping[str, ResolvedProjectConfiguration],
    package_paths: set[str],
    control_paths: set[str],
    final_paths: tuple[str, ...],
    limits: dict[str, int],
    trusted_environment_digest: str,
    local_extends: list[dict[str, Any]],
    source_graph: dict[str, Any],
) -> dict[str, Any]:
    projects: list[dict[str, Any]] = []
    config_resolution: list[dict[str, Any]] = []
    for root in intent.project_roots:
        resolved = configurations.get(root)
        if resolved is None:
            projects.append(
                {
                    "root": root,
                    "source_roots": [root],
                    "config_path": None,
                    "compiler_options": {
                        "allow_js": True,
                        "check_js": False,
                        "jsx": "preserve",
                        "module": "esnext",
                        "module_resolution": "bundler",
                        "base_url": None,
                        "paths": {},
                    },
                }
            )
            config_resolution.append(
                {
                    "project_root": root,
                    "config_path": None,
                    "declaring_paths": [],
                    "membership": {"kind": "not_applicable", "patterns": [], "exclude": []},
                    "path_resolution_order": [],
                }
            )
            continue
        projects.append(resolved.project_value())
        config_resolution.append(resolved.config_resolution_value())

    resolved_control_paths = [
        {"project_root": root, "path": path}
        for path in control_paths
        if path in package_paths
        or any(path in project.control_paths for project in configurations.values())
        for root in intent.project_roots
        if _path_is_within(path, root)
    ]
    file_role_map = []
    for path in final_paths:
        root = next(root for root in intent.project_roots if _path_is_within(path, root))
        role = (
            "control"
            if path in control_paths
            else "context"
            if path.endswith(SOURCE_PLAN_CONTEXT_SUFFIXES)
            else "program"
        )
        file_role_map.append(
            {
                "project_root": root,
                "path": path,
                "roles": [role],
                "effective_role": role,
            }
        )

    return {
        "schema": "code-structure-viz.source-acquisition-plan/next/v1",
        "version": "1",
        "projects": sorted(projects, key=lambda row: row["root"].encode("utf-8")),
        "resolved_control_paths": sorted(resolved_control_paths, key=encode_canonical_json),
        "local_extends": sorted(local_extends, key=encode_canonical_json),
        "file_role_map": sorted(file_role_map, key=encode_canonical_json),
        "program_suffixes": list(intent.program_suffixes),
        "context_suffixes": list(intent.context_suffixes),
        "hard_exclusions": list(intent.hard_exclusions),
        "limits": limits,
        "trusted_environment_digest": trusted_environment_digest,
        "config_resolution": sorted(
            config_resolution, key=lambda row: row["project_root"].encode("utf-8")
        ),
        "source_graph": source_graph,
    }


def _path_is_within(path: str, root: str) -> bool:
    return root == "." or path == root or path.startswith(f"{root.rstrip('/')}/")


def _digest(value: Any) -> str:
    return hashlib.sha256(encode_canonical_json(value)).hexdigest()
