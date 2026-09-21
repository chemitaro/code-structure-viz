"""Parsing for the deliberately small JSONC dialect used by Next controls."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Literal, NoReturn

from code_structure_viz.semantic.canonical_json import encode_canonical_json

from .applicability import _validate_path

_CONFIG_ERROR_CODE = "CSV-NEXT-CONFIG-001"
_EXTERNAL_CONFIG_ERROR_CODE = "CSV-NEXT-CONFIG-002"
_CONFIG_ERROR_STAGE = "source_control"
_JSON_WHITESPACE = frozenset(" \t\r\n")
_CONTROL_KEYS = frozenset({"compilerOptions", "include", "exclude", "files", "extends"})
_FORBIDDEN_COMPILER_OPTIONS = frozenset({"plugins", "typeRoots", "types"})
_BOOLEAN_COMPILER_OPTIONS = frozenset(
    {
        "declaration",
        "declarationMap",
        "sourceMap",
        "noEmit",
        "incremental",
        "composite",
        "strict",
        "esModuleInterop",
        "skipLibCheck",
        "resolveJsonModule",
        "isolatedModules",
        "verbatimModuleSyntax",
    }
)
_IGNORED_COMPILER_OPTIONS = _BOOLEAN_COMPILER_OPTIONS | frozenset(
    {"outDir", "rootDir", "target", "lib"}
)
_SUPPORTED_COMPILER_OPTIONS = (
    frozenset(
        {
            "allowJs",
            "checkJs",
            "jsx",
            "module",
            "moduleResolution",
            "baseUrl",
            "paths",
        }
    )
    | _IGNORED_COMPILER_OPTIONS
)
_PROJECT_CONTROL_CANDIDATES = ("tsconfig.json", "jsconfig.json")


class NextConfigurationError(ValueError):
    """A project control cannot be safely decoded under the Next v1 policy."""

    def __init__(self, message: str, *, path: str, code: str = _CONFIG_ERROR_CODE) -> None:
        self.code = code
        self.stage = _CONFIG_ERROR_STAGE
        self.path = path
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class ResolvedControlClosure:
    """Effective values derived from one project's already-frozen controls."""

    values: dict[str, Any]
    declaring_paths: dict[str, str]
    control_paths: tuple[str, ...]
    extends_edges: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class ResolvedCompilerOptions:
    """The closed compiler-option projection used by Next analysis."""

    allow_js: bool
    check_js: bool
    jsx: str
    module: str
    module_resolution: str
    base_url: str | None
    paths: tuple[tuple[str, tuple[str, ...]], ...]
    path_resolution_order: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "allow_js": self.allow_js,
            "check_js": self.check_js,
            "jsx": self.jsx,
            "module": self.module,
            "module_resolution": self.module_resolution,
            "base_url": self.base_url,
            "paths": {key: list(values) for key, values in self.paths},
        }


@dataclass(frozen=True, slots=True)
class ResolvedMembership:
    """Canonical project membership derived from controls and path inventory."""

    kind: Literal["files", "include", "default"]
    patterns: tuple[str, ...]
    exclude: tuple[str, ...]
    source_roots: tuple[str, ...]
    paths: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "patterns": list(self.patterns),
            "exclude": list(self.exclude),
        }


@dataclass(frozen=True, slots=True)
class ResolvedProjectConfiguration:
    """One project config projection derived from selected frozen controls."""

    project_root: str
    config_path: str | None
    compiler_options: ResolvedCompilerOptions
    membership: ResolvedMembership
    declaring_paths: tuple[tuple[str, str], ...]
    control_paths: tuple[str, ...]
    extends_edges: tuple[tuple[str, str], ...]

    def project_value(self) -> dict[str, object]:
        return {
            "root": self.project_root,
            "source_roots": list(self.membership.source_roots),
            "config_path": self.config_path,
            "compiler_options": self.compiler_options.as_dict(),
        }

    def config_resolution_value(self) -> dict[str, object]:
        declaring_paths = [
            {
                "option": key.removeprefix("compilerOptions."),
                "path": path,
            }
            for key, path in self.declaring_paths
        ]
        declaring_paths.sort(key=encode_canonical_json)
        return {
            "project_root": self.project_root,
            "config_path": self.config_path,
            "declaring_paths": declaring_paths,
            "membership": self.membership.as_dict(),
            "path_resolution_order": list(self.compiler_options.path_resolution_order),
        }


def parse_control_jsonc(payload: bytes, *, path: str) -> dict[str, Any]:
    """Decode one frozen project-control file using the closed JSONC grammar.

    The accepted extensions are one leading UTF-8 BOM, comments outside JSON
    strings, and trailing commas. Duplicate object keys and non-finite numbers
    are rejected at every nesting level. This function performs no filesystem
    access; callers own control discovery and byte acquisition.
    """

    if not isinstance(payload, bytes):
        raise NextConfigurationError("control content must be frozen bytes", path=path)
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise NextConfigurationError("control content is not valid UTF-8", path=path) from error

    normalized = _strip_jsonc(text, path=path)
    try:
        value = json.loads(
            normalized,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_non_finite_constant,
            parse_float=_parse_finite_float,
        )
    except (ValueError, RecursionError) as error:
        raise NextConfigurationError("control content is malformed JSONC", path=path) from error
    if not isinstance(value, dict):
        raise NextConfigurationError("control root must be an object", path=path)
    return value


def resolve_control_closure(
    frozen_controls: Mapping[str, bytes], *, project_root: str, config_path: str
) -> ResolvedControlClosure:
    """Resolve one local ``extends`` chain from captured bytes, without I/O.

    Paths and effective control values are derived only from the supplied
    frozen map. The result is an intermediate for source sealing; callers must
    not use it as a substitute for the final plan/view seal.
    """

    _validate_control_location(project_root, config_path)
    if not isinstance(frozen_controls, Mapping):
        raise NextConfigurationError("frozen controls must be a mapping", path=config_path)

    chain: list[tuple[str, dict[str, Any], str | None]] = []
    visited: set[str] = set()
    current_path = config_path
    while True:
        if current_path in visited:
            raise NextConfigurationError(
                "control extends chain contains a cycle", path=current_path
            )
        if current_path not in frozen_controls:
            raise NextConfigurationError("control bytes were not captured", path=current_path)

        control = parse_control_jsonc(frozen_controls[current_path], path=current_path)
        unknown = set(control) - _CONTROL_KEYS
        if unknown:
            raise NextConfigurationError("control contains an unknown key", path=current_path)

        visited.add(current_path)
        parent_path: str | None = None
        if "extends" in control:
            specifier = control["extends"]
            if not isinstance(specifier, str):
                raise NextConfigurationError("extends must be one local path", path=current_path)
            parent_path = _resolve_local_extends_path(
                current_path, project_root=project_root, specifier=specifier
            )
            if parent_path not in frozen_controls:
                raise NextConfigurationError(
                    "extends control bytes were not captured", path=parent_path
                )

        chain.append((current_path, control, parent_path))
        if parent_path is None:
            break
        current_path = parent_path

    values: dict[str, Any] = {}
    declaring_paths: dict[str, str] = {}
    control_paths: list[str] = []
    extends_edges: list[tuple[str, str]] = []
    for path, control, parent_path in reversed(chain):
        parent_options = values.get("compilerOptions", {})
        child_options = control.get("compilerOptions", {})
        if not isinstance(parent_options, dict) or not isinstance(child_options, dict):
            raise NextConfigurationError("compilerOptions must be an object", path=path)

        values["compilerOptions"] = {**parent_options, **child_options}
        declaring_paths.update({f"compilerOptions.{key}": path for key in child_options})
        for key in ("include", "exclude", "files"):
            if key in control:
                values[key] = control[key]
                declaring_paths[key] = path

        control_paths.append(path)
        if parent_path is not None:
            extends_edges.append((path, parent_path))

    return ResolvedControlClosure(
        values=values,
        declaring_paths=declaring_paths,
        control_paths=tuple(control_paths),
        extends_edges=tuple(extends_edges),
    )


def resolve_compiler_options(
    closure: ResolvedControlClosure, *, project_root: str
) -> ResolvedCompilerOptions:
    """Validate and normalize the compiler options relevant to Next analysis."""

    try:
        _validate_path(project_root, allow_root=True)
    except (TypeError, ValueError) as error:
        raise NextConfigurationError("project root is invalid", path=project_root) from error

    if not isinstance(closure, ResolvedControlClosure):
        raise NextConfigurationError("control closure is invalid", path=project_root)
    failure_path = closure.control_paths[-1] if closure.control_paths else project_root
    options = closure.values.get("compilerOptions", {})
    if not isinstance(options, dict):
        raise NextConfigurationError("compilerOptions must be an object", path=failure_path)

    forbidden = _FORBIDDEN_COMPILER_OPTIONS.intersection(options)
    if forbidden:
        option = sorted(forbidden)[0]
        raise NextConfigurationError(
            f"compiler option {option} is not supported",
            path=failure_path,
            code=_EXTERNAL_CONFIG_ERROR_CODE,
        )
    unknown = set(options) - _SUPPORTED_COMPILER_OPTIONS
    if unknown:
        raise NextConfigurationError(
            "compilerOptions contains an unsupported option", path=failure_path
        )

    for option in _BOOLEAN_COMPILER_OPTIONS.intersection(options):
        if not isinstance(options[option], bool):
            raise NextConfigurationError(
                f"compiler option {option} must be boolean", path=failure_path
            )
    for option in ("outDir", "rootDir", "target"):
        if option in options and not isinstance(options[option], str):
            raise NextConfigurationError(
                f"compiler option {option} must be a string", path=failure_path
            )
    if "lib" in options and (
        not isinstance(options["lib"], list)
        or any(not isinstance(value, str) for value in options["lib"])
    ):
        raise NextConfigurationError(
            "compiler option lib must be a string array", path=failure_path
        )

    allow_js = options.get("allowJs", True)
    check_js = options.get("checkJs", False)
    jsx = options.get("jsx", "preserve")
    module = options.get("module", "esnext")
    module_resolution = options.get("moduleResolution", "bundler")
    if not isinstance(allow_js, bool):
        raise NextConfigurationError("allowJs must be boolean", path=failure_path)
    if not isinstance(check_js, bool):
        raise NextConfigurationError("checkJs must be boolean", path=failure_path)
    if not isinstance(jsx, str) or jsx not in {
        "preserve",
        "react",
        "react-jsx",
        "react-jsxdev",
    }:
        raise NextConfigurationError("jsx compiler option is unsupported", path=failure_path)
    if module != "esnext":
        raise NextConfigurationError("module must be esnext", path=failure_path)
    if module_resolution != "bundler":
        raise NextConfigurationError("moduleResolution must be bundler", path=failure_path)

    raw_base_url = options.get("baseUrl")
    if raw_base_url is not None and not isinstance(raw_base_url, str):
        raise NextConfigurationError("baseUrl must be a path or null", path=failure_path)
    base_url = (
        _resolve_declaring_config_path(
            raw_base_url,
            config_path=_declaring_path(closure, "compilerOptions.baseUrl", failure_path),
            project_root=project_root,
            allow_root_sentinel=True,
        )
        if isinstance(raw_base_url, str)
        else None
    )

    raw_paths = options.get("paths", {})
    if not isinstance(raw_paths, dict):
        raise NextConfigurationError("paths must be an object", path=failure_path)
    resolved_paths: list[tuple[str, tuple[str, ...]]] = []
    for key, replacements in raw_paths.items():
        if (
            not isinstance(key, str)
            or re.fullmatch(r"[A-Za-z0-9_.*?/@-]+", key) is None
            or key.count("*") > 1
            or not isinstance(replacements, list)
            or not replacements
            or any(
                not isinstance(value, str) or value.count("*") > key.count("*")
                for value in replacements
            )
        ):
            raise NextConfigurationError("paths mapping is invalid", path=failure_path)
        declaring_path = _declaring_path(closure, "compilerOptions.paths", failure_path)
        resolved_replacements = tuple(
            _resolve_declaring_config_path(
                value,
                config_path=declaring_path,
                project_root=project_root,
                allow_root_sentinel=False,
            )
            for value in replacements
        )
        resolved_paths.append((key, resolved_replacements))

    path_resolution_order = tuple(
        sorted((key for key, _values in resolved_paths), key=_path_alias_priority)
    )
    return ResolvedCompilerOptions(
        allow_js=allow_js,
        check_js=check_js,
        jsx=jsx,
        module=module,
        module_resolution=module_resolution,
        base_url=base_url,
        paths=tuple(resolved_paths),
        path_resolution_order=path_resolution_order,
    )


def resolve_membership(
    closure: ResolvedControlClosure,
    *,
    project_root: str,
    inventory_paths: Sequence[str],
) -> ResolvedMembership:
    """Resolve project file membership without reading or importing target files.

    ``files`` and ``include`` are mutually exclusive authorities. Their values
    are interpreted relative to the control file that declared them. The path
    inventory supplies names only; the caller retains ownership of reading and
    freezing selected bytes.
    """

    if not isinstance(closure, ResolvedControlClosure):
        raise NextConfigurationError("control closure is invalid", path=project_root)
    failure_path = closure.control_paths[-1] if closure.control_paths else project_root
    try:
        _validate_path(project_root, allow_root=True)
    except (TypeError, ValueError) as error:
        raise NextConfigurationError("project root is invalid", path=project_root) from error
    if not isinstance(closure.values, Mapping) or not isinstance(closure.declaring_paths, Mapping):
        raise NextConfigurationError("control closure is invalid", path=failure_path)
    if isinstance(inventory_paths, (str, bytes)) or not isinstance(inventory_paths, Sequence):
        raise NextConfigurationError("source inventory paths must be a sequence", path=failure_path)

    paths = tuple(inventory_paths)
    try:
        for path in paths:
            _validate_path(path, allow_root=False)
    except (TypeError, ValueError) as error:
        raise NextConfigurationError(
            "source inventory path is invalid", path=failure_path
        ) from error
    if len(set(paths)) != len(paths):
        raise NextConfigurationError("source inventory path is duplicated", path=failure_path)

    control_values = closure.values
    include_present = "include" in control_values
    files_present = "files" in control_values
    if include_present and files_present:
        raise NextConfigurationError(
            "files and include are mutually exclusive authorities", path=failure_path
        )

    raw_values: dict[str, list[str]] = {}
    declaring_paths: dict[str, str] = {}
    for name in ("include", "exclude", "files"):
        if name not in control_values:
            raw_values[name] = []
            continue
        value = control_values[name]
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            raise NextConfigurationError(f"{name} must be an array of paths", path=failure_path)
        declaring_path = closure.declaring_paths.get(name)
        if not isinstance(declaring_path, str):
            raise NextConfigurationError(f"{name} has no declaring config path", path=failure_path)
        _validate_control_location(project_root, declaring_path)
        declaring_paths[name] = declaring_path
        raw_values[name] = value

    def resolve_values(name: str, *, allow_root_sentinel: bool, glob: bool) -> tuple[str, ...]:
        if name not in declaring_paths:
            return ()
        origin = declaring_paths[name]
        resolved: list[str] = []
        for value in raw_values[name]:
            path = _resolve_declaring_config_path(
                value,
                config_path=origin,
                project_root=project_root,
                allow_root_sentinel=allow_root_sentinel,
            )
            if glob:
                _validate_segment_glob(path, config_path=origin)
            resolved.append(path)
        return tuple(dict.fromkeys(resolved))

    include_values = resolve_values("include", allow_root_sentinel=True, glob=True)
    exclude_values = resolve_values("exclude", allow_root_sentinel=True, glob=True)
    explicit_values = resolve_values("files", allow_root_sentinel=False, glob=False)
    if any(any(token in path for token in "*?[]{}()!+") for path in explicit_values):
        raise NextConfigurationError(
            "files requires literal paths", path=declaring_paths.get("files", failure_path)
        )

    compiler_options = resolve_compiler_options(closure, project_root=project_root)
    source_roots: list[str] = []
    for pattern in include_values:
        static_prefix = re.split(r"[*?]", pattern, maxsplit=1)[0].rstrip("/")
        source_roots.append(static_prefix or project_root)
    if not source_roots and files_present:
        source_roots.extend(PurePosixPath(path).parent.as_posix() for path in explicit_values)
        if not source_roots:
            source_roots.append(project_root)
    if not source_roots:
        default_src = "src" if project_root == "." else f"{project_root.rstrip('/')}/src"
        has_default_src = any(
            _has_source_suffix(path) and _path_is_within(path, default_src) for path in paths
        )
        source_roots.append(default_src if has_default_src else project_root)
    canonical_source_roots = tuple(sorted(set(source_roots), key=lambda path: path.encode("utf-8")))

    kind: Literal["files", "include", "default"]
    if files_present:
        kind = "files"
        patterns = explicit_values
        public_excludes: tuple[str, ...] = ()
    elif include_present:
        kind = "include"
        patterns = include_values
        public_excludes = exclude_values
    else:
        kind = "default"
        patterns = canonical_source_roots
        public_excludes = exclude_values

    members: set[str] = set()
    explicit_set = set(explicit_values)
    for candidate in paths:
        if not _path_is_within(candidate, project_root):
            continue
        if files_present:
            included = candidate in explicit_set
        elif include_present:
            included = any(
                _segment_glob_matches_path_or_descendant(
                    _relative_to_project(pattern, project_root),
                    _relative_to_project(candidate, project_root),
                )
                for pattern in include_values
            )
        else:
            included = any(_path_is_within(candidate, root) for root in canonical_source_roots)
        excluded = not files_present and any(
            _segment_glob_matches_path_or_descendant(
                _relative_to_project(pattern, project_root),
                _relative_to_project(candidate, project_root),
            )
            for pattern in exclude_values
        )
        if (
            included
            and not excluded
            and _has_source_suffix(candidate)
            and (compiler_options.allow_js or not candidate.endswith((".js", ".jsx")))
        ):
            members.add(candidate)

    return ResolvedMembership(
        kind=kind,
        patterns=patterns,
        exclude=public_excludes,
        source_roots=canonical_source_roots,
        paths=tuple(sorted(members, key=lambda path: path.encode("utf-8"))),
    )


def resolve_project_configuration(
    frozen_controls: Mapping[str, bytes],
    *,
    project_root: str,
    inventory_paths: Sequence[str],
    control_candidates: Sequence[str] = _PROJECT_CONTROL_CANDIDATES,
) -> ResolvedProjectConfiguration:
    """Resolve the selected root config and its derived project membership.

    Only the declared root candidates participate in config selection. A
    selected ``tsconfig.json`` takes precedence over ``jsconfig.json``; an
    unselected candidate is never parsed. With no selected config, the closed
    built-in compiler and membership defaults apply.
    """

    try:
        _validate_path(project_root, allow_root=True)
    except (TypeError, ValueError) as error:
        raise NextConfigurationError("project root is invalid", path=project_root) from error
    if not isinstance(frozen_controls, Mapping):
        raise NextConfigurationError("frozen controls must be a mapping", path=project_root)
    if isinstance(control_candidates, (str, bytes)) or not isinstance(control_candidates, Sequence):
        raise NextConfigurationError("control candidates must be a sequence", path=project_root)
    candidates = tuple(control_candidates)
    if any(
        not isinstance(candidate, str) or candidate not in _PROJECT_CONTROL_CANDIDATES
        for candidate in candidates
    ) or len(set(candidates)) != len(candidates):
        raise NextConfigurationError("control candidates are invalid", path=project_root)

    candidate_set = set(candidates)
    observed_root_candidates = {
        candidate
        for candidate in _PROJECT_CONTROL_CANDIDATES
        if _project_control_path(project_root, candidate) in frozen_controls
    }
    if not observed_root_candidates.issubset(candidate_set):
        raise NextConfigurationError(
            "frozen root config observations are not declared as candidates",
            path=project_root,
        )
    selected_config_path = next(
        (
            _project_control_path(project_root, candidate)
            for candidate in _PROJECT_CONTROL_CANDIDATES
            if candidate in candidate_set
            and _project_control_path(project_root, candidate) in frozen_controls
        ),
        None,
    )
    closure = (
        resolve_control_closure(
            frozen_controls,
            project_root=project_root,
            config_path=selected_config_path,
        )
        if selected_config_path is not None
        else ResolvedControlClosure({}, {}, (), ())
    )
    compiler_options = resolve_compiler_options(closure, project_root=project_root)
    membership = resolve_membership(
        closure,
        project_root=project_root,
        inventory_paths=inventory_paths,
    )
    return ResolvedProjectConfiguration(
        project_root=project_root,
        config_path=selected_config_path,
        compiler_options=compiler_options,
        membership=membership,
        declaring_paths=tuple(closure.declaring_paths.items()),
        control_paths=closure.control_paths,
        extends_edges=closure.extends_edges,
    )


def _declaring_path(closure: ResolvedControlClosure, option: str, fallback: str) -> str:
    path = closure.declaring_paths.get(option)
    if path is None:
        raise NextConfigurationError(f"{option} has no declaring config path", path=fallback)
    return path


def _resolve_declaring_config_path(
    value: str,
    *,
    config_path: str,
    project_root: str,
    allow_root_sentinel: bool,
) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value.startswith("/")
        or "\\" in value
        or "#" in value
        or any(ord(character) < 0x20 or ord(character) == 0x7F for character in value)
        or any(part == ".." for part in value.split("/"))
    ):
        raise NextConfigurationError("compiler path is unsafe", path=config_path)
    if any(part == "" for part in value.split("/")[1:]):
        raise NextConfigurationError("compiler path is not canonical", path=config_path)

    declaring_parent = PurePosixPath(config_path).parent
    raw_parts = (*declaring_parent.parts, *value.split("/"))
    parts = tuple(part for part in raw_parts if part not in {"", ".", "/"})
    candidate = "/".join(parts) or "."
    try:
        _validate_path(candidate, allow_root=allow_root_sentinel)
        _validate_control_location(project_root, config_path)
    except (TypeError, ValueError) as error:
        raise NextConfigurationError("compiler path is invalid", path=config_path) from error
    if candidate == "." and project_root != ".":
        candidate = project_root
    elif project_root != "." and not _path_is_within(candidate, project_root):
        raise NextConfigurationError("compiler path is outside the project root", path=config_path)
    return candidate


def _path_alias_priority(pattern: str) -> tuple[bool, int]:
    return "*" in pattern, -len(pattern.replace("*", ""))


def _validate_control_location(project_root: str, config_path: str) -> None:
    try:
        _validate_path(project_root, allow_root=True)
        _validate_path(config_path, allow_root=False)
    except (TypeError, ValueError) as error:
        raise NextConfigurationError("control location is invalid", path=config_path) from error
    if config_path == project_root or not _path_is_within(config_path, project_root):
        raise NextConfigurationError("control is outside the project root", path=config_path)


def _resolve_local_extends_path(config_path: str, *, project_root: str, specifier: str) -> str:
    if specifier.startswith(("../", "/", "\\")):
        raise NextConfigurationError(
            "extends must remain within the project root", path=config_path
        )
    if not specifier.startswith("./") or "://" in specifier:
        raise NextConfigurationError(
            "extends requests external resolution",
            path=config_path,
            code=_EXTERNAL_CONFIG_ERROR_CODE,
        )
    relative_path = specifier[2:]
    try:
        _validate_path(relative_path, allow_root=False)
        parent = PurePosixPath(config_path).parent
        resolved_path = (parent / relative_path).as_posix()
        _validate_path(resolved_path, allow_root=False)
    except (TypeError, ValueError) as error:
        raise NextConfigurationError("extends path is invalid", path=config_path) from error
    if not _path_is_within(resolved_path, project_root):
        raise NextConfigurationError("extends escapes the project root", path=config_path)
    return resolved_path


def _path_is_within(path: str, root: str) -> bool:
    return root == "." or path == root or path.startswith(f"{root.rstrip('/')}/")


def _project_control_path(project_root: str, control_name: str) -> str:
    return control_name if project_root == "." else f"{project_root.rstrip('/')}/{control_name}"


def _has_source_suffix(path: str) -> bool:
    return path.endswith((".js", ".jsx", ".ts", ".tsx", ".d.ts"))


def _relative_to_project(path: str, project_root: str) -> str:
    if project_root == ".":
        return path
    return path.removeprefix(f"{project_root.rstrip('/')}/")


def _validate_segment_glob(pattern: str, *, config_path: str) -> None:
    """Reject glob syntax outside ``*``, ``?``, and whole-segment ``**``."""

    for segment in pattern.split("/"):
        if segment == "**":
            continue
        if "**" in segment or any(token in segment for token in "[]{}()!+"):
            raise NextConfigurationError(
                "include/exclude contains unsupported glob syntax", path=config_path
            )


def _single_segment_matches(pattern: str, value: str) -> bool:
    """Match one path segment using only ``*`` and ``?`` without regex rules."""

    pattern_index = 0
    value_index = 0
    last_star = -1
    retry_value_index = 0
    while value_index < len(value):
        if pattern_index < len(pattern) and (
            pattern[pattern_index] == "?" or pattern[pattern_index] == value[value_index]
        ):
            pattern_index += 1
            value_index += 1
        elif pattern_index < len(pattern) and pattern[pattern_index] == "*":
            last_star = pattern_index
            pattern_index += 1
            retry_value_index = value_index
        elif last_star >= 0:
            retry_value_index += 1
            value_index = retry_value_index
            pattern_index = last_star + 1
        else:
            return False

    while pattern_index < len(pattern) and pattern[pattern_index] == "*":
        pattern_index += 1
    return pattern_index == len(pattern)


def _glob_epsilon_closure(states: set[int], segments: tuple[str, ...]) -> set[int]:
    expanded = set(states)
    pending = list(states)
    while pending:
        index = pending.pop()
        if index < len(segments) and segments[index] == "**" and index + 1 not in expanded:
            expanded.add(index + 1)
            pending.append(index + 1)
    return expanded


def _segment_glob_matches_path_or_descendant(pattern: str, candidate: str) -> bool:
    """Match a path pattern against a candidate or any directory prefix."""

    segments = (*pattern.split("/"), "**")
    states = _glob_epsilon_closure({0}, segments)
    terminal = len(segments)
    for candidate_segment in candidate.split("/"):
        next_states: set[int] = set()
        for index in states:
            if index == terminal:
                continue
            segment = segments[index]
            if segment == "**":
                next_states.add(index)
            elif _single_segment_matches(segment, candidate_segment):
                next_states.add(index + 1)
        states = _glob_epsilon_closure(next_states, segments)
        if terminal in states:
            return True
    return terminal in states


def _strip_jsonc(text: str, *, path: str) -> str:
    output: list[str] = []
    last_significant: str | None = None

    def append_comment_as_whitespace(start: int, end: int) -> None:
        output.extend(character if character in "\r\n" else " " for character in text[start:end])

    def block_comment_end(start: int) -> int:
        terminator = text.find("*/", start + 2)
        if terminator < 0:
            raise NextConfigurationError("control has an unterminated comment", path=path)
        return terminator + 2

    def line_comment_end(start: int) -> int:
        end = start + 2
        while end < len(text) and text[end] not in "\r\n":
            end += 1
        return end

    def next_value_index(start: int) -> int:
        cursor = start
        while cursor < len(text):
            while cursor < len(text) and text[cursor] in _JSON_WHITESPACE:
                cursor += 1
            if text.startswith("//", cursor):
                cursor = line_comment_end(cursor)
                continue
            if text.startswith("/*", cursor):
                cursor = block_comment_end(cursor)
                continue
            break
        return cursor

    index = 0
    in_string = False
    escaped = False
    while index < len(text):
        character = text[index]
        if in_string:
            output.append(character)
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
                last_significant = '"'
            index += 1
            continue

        if character == '"':
            in_string = True
            output.append(character)
            index += 1
            continue
        if text.startswith("//", index):
            end = line_comment_end(index)
            append_comment_as_whitespace(index, end)
            index = end
            continue
        if text.startswith("/*", index):
            end = block_comment_end(index)
            append_comment_as_whitespace(index, end)
            index = end
            continue
        if character == ",":
            lookahead = next_value_index(index + 1)
            if (
                lookahead < len(text)
                and text[lookahead] in "]}"
                and last_significant not in {None, "{", "[", ",", ":"}
            ):
                index += 1
                continue

        output.append(character)
        if character not in _JSON_WHITESPACE:
            last_significant = character
        index += 1

    if in_string or escaped:
        raise NextConfigurationError("control has an unterminated string", path=path)
    return "".join(output)


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate control key")
        result[key] = value
    return result


def _reject_non_finite_constant(value: str) -> NoReturn:
    raise ValueError(f"non-finite JSON number: {value}")


def _parse_finite_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("non-finite JSON number")
    return number
