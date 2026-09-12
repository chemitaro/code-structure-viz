"""Parsing for the deliberately small JSONC dialect used by Next controls."""

from __future__ import annotations

import json
import math
from typing import Any, NoReturn

_CONFIG_ERROR_CODE = "CSV-NEXT-CONFIG-001"
_CONFIG_ERROR_STAGE = "source_control"
_JSON_WHITESPACE = frozenset(" \t\r\n")


class NextConfigurationError(ValueError):
    """A project control cannot be safely decoded under the Next v1 policy."""

    def __init__(self, message: str, *, path: str) -> None:
        self.code = _CONFIG_ERROR_CODE
        self.stage = _CONFIG_ERROR_STAGE
        self.path = path
        super().__init__(message)


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

    def next_value_index(start: int) -> int:
        cursor = start
        while cursor < len(text):
            while cursor < len(text) and text[cursor] in _JSON_WHITESPACE:
                cursor += 1
            if text.startswith("//", cursor):
                cursor += 2
                while cursor < len(text) and text[cursor] not in "\r\n":
                    cursor += 1
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
            end = index + 2
            while end < len(text) and text[end] not in "\r\n":
                end += 1
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
