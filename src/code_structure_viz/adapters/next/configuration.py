"""Parsing for the deliberately small JSONC dialect used by Next controls."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, NoReturn

from .applicability import _validate_path

_CONFIG_ERROR_CODE = "CSV-NEXT-CONFIG-001"
_EXTERNAL_CONFIG_ERROR_CODE = "CSV-NEXT-CONFIG-002"
_CONFIG_ERROR_STAGE = "source_control"
_JSON_WHITESPACE = frozenset(" \t\r\n")
_CONTROL_KEYS = frozenset({"compilerOptions", "include", "exclude", "files", "extends"})


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
