from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

from code_structure_viz.adapters.next.configuration import ResolvedProjectConfiguration
from code_structure_viz.semantic.canonical_json import encode_canonical_json

_PROGRAM_SUFFIXES = (".js", ".jsx", ".ts", ".tsx")
_CONTEXT_SUFFIXES = (".d.ts",)
_PACKAGE_SPECIFIER = re.compile(r"^(@[a-z0-9._-]+/)?[a-z0-9._-]+(?:/[a-z0-9._-]+)*$")
_REGEX_PREFIX = frozenset(
    {"=", "(", "[", "{", ",", ":", ";", "!", "?", "=>", "return", "throw", "case"}
)


@dataclass(frozen=True, slots=True)
class _Token:
    kind: str
    value: str
    start: int
    end: int


@dataclass(frozen=True, slots=True)
class _ModuleReference:
    syntax_kind: str
    specifier: str
    start: int
    end: int


class _UnsupportedModuleSyntax(ValueError):
    pass


def derive_source_graph(
    contents: Mapping[str, bytes],
    project_roots: tuple[str, ...],
    configurations: tuple[ResolvedProjectConfiguration, ...],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Derive a privacy-safe resolved/open graph from the bytes held by a seal."""

    nodes: list[dict[str, Any]] = []
    node_ids: dict[str, str] = {}
    for path, payload in sorted(contents.items(), key=lambda row: row[0].encode("utf-8")):
        root = next(
            (candidate for candidate in project_roots if _path_is_within(path, candidate)), None
        )
        if root is None:
            raise ValueError("source graph path is outside every selected project")
        node_id = _digest({"kind": "source_node", "path": path})
        node_ids[path] = node_id
        nodes.append(
            {
                "id": node_id,
                "path": path,
                "project_root": root,
                "content_sha256": hashlib.sha256(payload).hexdigest(),
            }
        )

    edges: list[dict[str, Any]] = []
    open_edges: list[dict[str, Any]] = []
    configuration_by_root = {project.project_root: project for project in configurations}
    for path, payload in sorted(contents.items(), key=lambda row: row[0].encode("utf-8")):
        if not path.endswith((*_PROGRAM_SUFFIXES, *_CONTEXT_SUFFIXES)):
            continue
        source_id = node_ids[path]
        try:
            source = payload.decode("utf-8")
            references, scanner_open = _scan_module_references(
                source, allow_jsx=not path.endswith(".ts")
            )
        except (UnicodeDecodeError, _UnsupportedModuleSyntax):
            open_edges.append(_open_edge(source_id, "source_decode", "invalid_utf8"))
            continue
        if scanner_open:
            open_edges.append(_open_edge(source_id, "module_plane", "unsupported"))
        root = next(candidate for candidate in project_roots if _path_is_within(path, candidate))
        configuration = configuration_by_root.get(root)
        for reference in references:
            candidates = _resolve_candidates(
                path,
                reference.specifier,
                root,
                configuration,
                frozenset(node_ids),
            )
            span = _byte_span(source, reference.start, reference.end)
            if len(candidates) == 1:
                normalized = candidates[0]
                edges.append(
                    {
                        "kind": "resolved",
                        "source": source_id,
                        "target": node_ids[normalized],
                        "syntax_kind": reference.syntax_kind,
                        "role": "type"
                        if reference.syntax_kind
                        in {"import_type", "export_type", "export_type_query"}
                        else "value",
                        "normalized_specifier": normalized,
                        "specifier_identity": _digest(
                            {
                                "source": source_id,
                                "syntax_kind": reference.syntax_kind,
                                "normalized_specifier": normalized,
                            }
                        ),
                        "source_span": span,
                    }
                )
                continue

            reason = "ambiguous" if len(candidates) > 1 else "unresolved"
            normalized_open = _normalize_relative_specifier(reference.specifier, path)
            open_edge: dict[str, Any] = {
                "kind": "open",
                "source": source_id,
                "syntax_kind": reference.syntax_kind,
                "reason": reason,
                "source_span": span,
            }
            if (
                normalized_open is not None
                and _is_public_path(normalized_open)
                and reference.specifier.startswith(".")
            ):
                open_edge.update(
                    {
                        "target_kind": "unresolved_relative",
                        "safe_frontier": {
                            "source": source_id,
                            "normalized_specifier": normalized_open,
                        },
                        "specifier_identity": _digest(
                            {
                                "source": source_id,
                                "syntax_kind": reference.syntax_kind,
                                "normalized_specifier": normalized_open,
                            }
                        ),
                    }
                )
            elif _PACKAGE_SPECIFIER.fullmatch(reference.specifier):
                open_edge.update(
                    {
                        "target_kind": "external_package",
                        "safe_frontier": {
                            "source": source_id,
                            "safe_specifier": reference.specifier,
                        },
                        "specifier_identity": _digest(
                            {
                                "source": source_id,
                                "syntax_kind": reference.syntax_kind,
                                "normalized_specifier": reference.specifier,
                            }
                        ),
                    }
                )
            else:
                open_edge["safe_frontier"] = {"source": source_id}
                open_edge["specifier_identity"] = _digest(
                    {
                        "source": source_id,
                        "content_sha256": hashlib.sha256(payload).hexdigest(),
                        "source_span": span,
                        "syntax_kind": reference.syntax_kind,
                        "specifier": reference.specifier,
                    }
                )
            open_edges.append(open_edge)

    local_extends: list[dict[str, Any]] = []
    for project in configurations:
        for config_path, parent_path in project.extends_edges:
            local_extends.append(
                {
                    "project_root": project.project_root,
                    "config_path": config_path,
                    "extends": [parent_path],
                }
            )
            config_source_id = node_ids.get(config_path)
            target_id = node_ids.get(parent_path)
            if config_source_id is None:
                continue
            if target_id is None:
                open_edges.append(_open_edge(config_source_id, "config_extends", "unresolved"))
                continue
            edges.append(
                {
                    "kind": "resolved",
                    "source": config_source_id,
                    "target": target_id,
                    "syntax_kind": "config_extends",
                    "role": "control",
                    "normalized_specifier": parent_path,
                    "specifier_identity": _digest(
                        {
                            "source": config_source_id,
                            "syntax_kind": "config_extends",
                            "normalized_specifier": parent_path,
                        }
                    ),
                }
            )

    edges.sort(key=encode_canonical_json)
    open_edges.sort(key=encode_canonical_json)
    graph: dict[str, Any] = {
        "nodes": sorted(nodes, key=encode_canonical_json),
        "edges": edges,
        "open_edges": open_edges,
    }
    graph["graph_digest"] = _digest(graph)
    return graph, local_extends


def _scan_module_references(
    text: str, *, allow_jsx: bool
) -> tuple[tuple[_ModuleReference, ...], bool]:
    tokens, scanner_open = _tokenize(text, allow_jsx=allow_jsx)
    references: list[_ModuleReference] = []
    require_uncertain = any(
        token.kind == "identifier"
        and token.value == "require"
        and (
            index + 1 >= len(tokens)
            or tokens[index + 1].value != "("
            or (index > 0 and tokens[index - 1].value in {".", "function", "new"})
        )
        for index, token in enumerate(tokens)
    )
    scanner_open = scanner_open or require_uncertain

    def literal_argument(index: int) -> _Token | None:
        if (
            index + 3 < len(tokens)
            and tokens[index + 1].value == "("
            and tokens[index + 2].kind == "string"
            and tokens[index + 3].value == ")"
        ):
            return tokens[index + 2]
        return None

    def scan_from(index: int) -> tuple[_Token | None, int, bool]:
        cursor = index
        while cursor < len(tokens) and tokens[cursor].value not in {";", "import", "export"}:
            if tokens[cursor].kind == "identifier" and tokens[cursor].value == "from":
                if cursor + 1 < len(tokens) and tokens[cursor + 1].kind == "string":
                    return tokens[cursor + 1], cursor + 2, False
                return None, cursor + 1, True
            cursor += 1
        return None, cursor, False

    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token.kind != "identifier":
            index += 1
            continue
        if token.value == "import":
            if index > 0 and tokens[index - 1].value == ".":
                scanner_open = True
                index += 1
                continue
            if index + 1 < len(tokens) and tokens[index + 1].value == "(":
                argument = literal_argument(index)
                if argument is None:
                    scanner_open = True
                else:
                    references.append(
                        _ModuleReference(
                            "literal_dynamic_import", argument.value, argument.start, argument.end
                        )
                    )
                index += 1
                continue
            if index + 1 < len(tokens) and tokens[index + 1].kind == "string":
                argument = tokens[index + 1]
                references.append(
                    _ModuleReference("static_import", argument.value, argument.start, argument.end)
                )
                index += 2
                continue
            if index + 1 < len(tokens) and tokens[index + 1].value != ".":
                binding_start = index + 1
                is_type = tokens[binding_start].value == "type"
                if is_type:
                    binding_start += 1
                if binding_start + 1 < len(tokens) and tokens[binding_start + 1].value == "=":
                    index += 1
                    continue
                argument, next_index, ambiguous = scan_from(index + 1)
                if argument is not None:
                    references.append(
                        _ModuleReference(
                            "import_type" if is_type else "static_import",
                            argument.value,
                            argument.start,
                            argument.end,
                        )
                    )
                scanner_open = scanner_open or ambiguous
                index = max(index, next_index - 1)
        elif token.value == "export":
            clause_start = index + 1
            is_type = clause_start < len(tokens) and tokens[clause_start].value == "type"
            if is_type:
                clause_start += 1
            if clause_start < len(tokens) and tokens[clause_start].value in {"{", "*"}:
                if tokens[clause_start].value == "{":
                    depth = 1
                    cursor = clause_start + 1
                    while cursor < len(tokens) and depth:
                        depth += int(tokens[cursor].value == "{") - int(tokens[cursor].value == "}")
                        cursor += 1
                    if depth:
                        scanner_open = True
                        index += 1
                        continue
                    if cursor < len(tokens) and tokens[cursor].value == "from":
                        argument, next_index, ambiguous = scan_from(cursor)
                    else:
                        argument, next_index, ambiguous = None, cursor, False
                else:
                    argument, next_index, ambiguous = scan_from(clause_start)
                    if argument is None:
                        ambiguous = True
                if argument is not None:
                    references.append(
                        _ModuleReference(
                            "export_type" if is_type else "export_from",
                            argument.value,
                            argument.start,
                            argument.end,
                        )
                    )
                scanner_open = scanner_open or ambiguous
                index = max(index, next_index - 1)
        elif token.value == "require":
            argument = literal_argument(index)
            if argument is not None and not require_uncertain:
                references.append(
                    _ModuleReference("require", argument.value, argument.start, argument.end)
                )
            elif index + 1 < len(tokens) and tokens[index + 1].value == "(":
                scanner_open = True
        index += 1
    return tuple(references), scanner_open


def _tokenize(text: str, *, allow_jsx: bool) -> tuple[tuple[_Token, ...], bool]:
    tokens: list[_Token] = []
    index = 0
    previous: _Token | None = None
    jsx_tag = False
    jsx_closing = False
    jsx_depth = 0
    jsx_text = False
    jsx_expression_depth = 0
    jsx_expression_parent: str | None = None
    scanner_open = False

    def append(kind: str, value: str, start: int, end: int) -> None:
        nonlocal previous
        token = _Token(kind, value, start, end)
        tokens.append(token)
        previous = token

    while index < len(text):
        character = text[index]
        if jsx_text and jsx_expression_depth == 0:
            if character == "{" and not jsx_tag:
                jsx_text = False
                jsx_expression_depth = 1
                jsx_expression_parent = "text"
                append("punct", "{", index, index + 1)
                index += 1
                continue
            if (
                character == "<"
                and index + 1 < len(text)
                and (text[index + 1] in "/>" or text[index + 1].isalpha())
            ):
                jsx_text = False
                jsx_tag = True
                jsx_closing = text.startswith("</", index)
                append("punct", "<", index, index + 1)
                index += 1
                continue
            index += 1
            continue
        if character.isspace():
            index += 1
            continue
        if text.startswith("//", index):
            index += 2
            while index < len(text) and text[index] not in "\r\n":
                index += 1
            continue
        if text.startswith("/*", index):
            end = text.find("*/", index + 2)
            if end < 0:
                return tuple(tokens), True
            index = end + 2
            continue
        if character in "'\"":
            quote = character
            start = index
            index += 1
            raw: list[str] = []
            while index < len(text) and text[index] != quote:
                if text[index] in "\r\n":
                    return tuple(tokens), True
                if text[index] == "\\" and index + 1 < len(text):
                    raw.append(text[index])
                    raw.append(text[index + 1])
                    index += 2
                else:
                    raw.append(text[index])
                    index += 1
            if index >= len(text):
                return tuple(tokens), True
            try:
                value = _decode_string_literal("".join(raw))
            except ValueError:
                return tuple(tokens), True
            index += 1
            append("string", value, start, index)
            continue
        if character == "`":
            index += 1
            has_expression = False
            while index < len(text):
                if text[index] == "\\":
                    index += 2
                    continue
                if text.startswith("${", index):
                    has_expression = True
                if text[index] == "`":
                    index += 1
                    break
                index += 1
            else:
                return tuple(tokens), True
            scanner_open = scanner_open or has_expression
            continue
        if character == "/" and (previous is None or previous.value in _REGEX_PREFIX):
            index += 1
            in_class = False
            while index < len(text):
                if text[index] == "\\":
                    index += 2
                    continue
                if text[index] == "[":
                    in_class = True
                elif text[index] == "]":
                    in_class = False
                elif text[index] == "/" and not in_class:
                    index += 1
                    while index < len(text) and text[index].isalpha():
                        index += 1
                    break
                elif text[index] in "\r\n":
                    return tuple(tokens), True
                index += 1
            else:
                return tuple(tokens), True
            continue
        if character.isalpha() or character in "_$" or ord(character) >= 0x80:
            end = index + 1
            while end < len(text) and (
                text[end].isalnum() or text[end] in "_$" or ord(text[end]) >= 0x80
            ):
                end += 1
            append("identifier", text[index:end], index, end)
            index = end
            continue
        if text.startswith("=>", index):
            append("punct", "=>", index, index + 2)
            index += 2
            continue
        if (
            allow_jsx
            and character == "<"
            and index + 1 < len(text)
            and (text[index + 1] in "/>" or text[index + 1].isalpha())
            and (
                jsx_depth > 0
                or previous is None
                or previous.value in {"=", "(", "[", "{", ":", ",", "return", "=>"}
            )
        ):
            jsx_tag = True
            jsx_closing = text.startswith("</", index)
            append("punct", "<", index, index + 1)
            index += 1
            continue
        if jsx_tag:
            if character == "{":
                jsx_tag = False
                jsx_expression_depth = 1
                jsx_expression_parent = "tag"
                append("punct", "{", index, index + 1)
                index += 1
                continue
            if character == ">":
                self_closing = index > 0 and text[index - 1] == "/"
                append("punct", character, index, index + 1)
                index += 1
                if jsx_closing:
                    jsx_depth = max(0, jsx_depth - 1)
                elif not self_closing:
                    jsx_depth += 1
                jsx_tag = False
                jsx_text = jsx_depth > 0
                continue
        if jsx_expression_depth:
            if character == "{":
                jsx_expression_depth += 1
            elif character == "}":
                jsx_expression_depth -= 1
            append("punct", character, index, index + 1)
            index += 1
            if jsx_expression_depth == 0:
                if jsx_expression_parent == "tag":
                    jsx_tag = True
                elif jsx_expression_parent == "text" and jsx_depth > 0:
                    jsx_text = True
                jsx_expression_parent = None
            continue
        append("punct", character, index, index + 1)
        index += 1
    return tuple(tokens), scanner_open or jsx_tag or jsx_depth > 0 or jsx_expression_depth > 0


def _decode_string_literal(raw: str) -> str:
    output: list[str] = []
    index = 0
    escapes = {"b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t", "v": "\v"}
    while index < len(raw):
        if raw[index] != "\\":
            output.append(raw[index])
            index += 1
            continue
        index += 1
        if index >= len(raw):
            raise ValueError("trailing escape")
        escape = raw[index]
        if escape in escapes:
            output.append(escapes[escape])
            index += 1
        elif escape in "\\/'\"`":
            output.append(escape)
            index += 1
        elif escape == "x" and index + 2 < len(raw):
            output.append(chr(int(raw[index + 1 : index + 3], 16)))
            index += 3
        elif escape == "u" and index + 4 < len(raw):
            output.append(chr(int(raw[index + 1 : index + 5], 16)))
            index += 5
        elif escape in "\r\n":
            if escape == "\r" and index + 1 < len(raw) and raw[index + 1] == "\n":
                index += 1
            index += 1
        else:
            raise ValueError("unsupported string escape")
    decoded = "".join(output)
    decoded.encode("utf-8")
    return decoded


def _resolve_candidates(
    source_path: str,
    specifier: str,
    project_root: str,
    configuration: ResolvedProjectConfiguration | None,
    available_paths: frozenset[str],
) -> tuple[str, ...]:
    roots: list[str] = []
    if specifier.startswith("."):
        normalized = _normalize_relative_specifier(specifier, source_path)
        if normalized is not None:
            roots.append(normalized)
    elif configuration is not None:
        aliases = dict(configuration.compiler_options.paths)
        for pattern in configuration.compiler_options.path_resolution_order:
            replacements = aliases[pattern]
            if "*" in pattern:
                prefix, suffix = pattern.split("*", 1)
                if (
                    len(specifier) < len(prefix) + len(suffix)
                    or not specifier.startswith(prefix)
                    or not specifier.endswith(suffix)
                ):
                    continue
                wildcard = specifier[len(prefix) : len(specifier) - len(suffix) if suffix else None]
                roots.extend(value.replace("*", wildcard, 1) for value in replacements)
            elif specifier == pattern:
                roots.extend(replacements)
            else:
                continue
            break
        if not roots and configuration.compiler_options.base_url is not None:
            base = configuration.compiler_options.base_url
            roots.append(specifier if base == "." else f"{base}/{specifier}")

    candidates: list[str] = []
    for root in roots:
        normalized = root
        for suffix in (".mjs", ".cjs", ".js", ".jsx"):
            if normalized.endswith(suffix):
                normalized = normalized[: -len(suffix)]
                break
        for candidate in (
            normalized,
            *(f"{normalized}{suffix}" for suffix in (".ts", ".tsx", ".js", ".jsx", ".d.ts")),
            *(f"{normalized}/index{suffix}" for suffix in (".ts", ".tsx", ".js", ".jsx", ".d.ts")),
        ):
            if candidate in available_paths and _path_is_within(candidate, project_root):
                candidates.append(candidate)
    return tuple(dict.fromkeys(candidates))


def _normalize_relative_specifier(specifier: str, source_path: str) -> str | None:
    parent = PurePosixPath(source_path).parent.as_posix()
    raw_path = f"{parent}/{specifier}" if parent != "." else specifier
    parts: list[str] = []
    for part in raw_path.split("/"):
        if part in {"", "."}:
            continue
        if part == "..":
            if not parts:
                return None
            parts.pop()
        else:
            parts.append(part)
    return "/".join(parts)


def _byte_span(text: str, start: int, end: int) -> dict[str, int]:
    return {
        "byte_start": len(text[:start].encode("utf-8")),
        "byte_end": len(text[:end].encode("utf-8")),
    }


def _is_public_path(path: str) -> bool:
    return (
        bool(path)
        and len(path.encode("utf-8")) <= 4096
        and unicodedata.normalize("NFC", path) == path
        and not path.startswith("/")
        and not path.endswith("/")
        and "#" not in path
        and "\\" not in path
        and "//" not in path
        and all(part not in {".", ".."} for part in path.split("/"))
        and all(ord(character) >= 0x20 and ord(character) != 0x7F for character in path)
    )


def _open_edge(source_id: str, syntax_kind: str, reason: str) -> dict[str, Any]:
    return {
        "kind": "open",
        "source": source_id,
        "syntax_kind": syntax_kind,
        "reason": reason,
        "safe_frontier": {"source": source_id},
    }


def _path_is_within(path: str, root: str) -> bool:
    return root == "." or path == root or path.startswith(f"{root.rstrip('/')}/")


def _digest(value: Any) -> str:
    return hashlib.sha256(encode_canonical_json(value)).hexdigest()
