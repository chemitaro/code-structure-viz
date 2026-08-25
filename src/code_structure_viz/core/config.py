from __future__ import annotations

import hashlib
import os
import tomllib
import unicodedata
from dataclasses import dataclass, replace
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Final, cast

from code_structure_viz.cli.parser import SnapshotCliRequest
from code_structure_viz.core.diagnostics import Diagnostic, DiagnosticCode, diagnostic
from code_structure_viz.core.path_safety import has_symlink_component
from code_structure_viz.semantic.canonical_json import encode_canonical_json


class ConfigSource(StrEnum):
    BUILTIN = "builtin"
    REPOSITORY = "repository"
    EXPLICIT = "explicit"
    CLI = "cli"


@dataclass(frozen=True, slots=True)
class PythonConfig:
    source_roots: tuple[str, ...]
    include: tuple[str, ...]
    exclude: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TraversalConfig:
    upstream_depth: int
    downstream_depth: int


@dataclass(frozen=True, slots=True)
class LimitsConfig:
    max_entities: int


@dataclass(frozen=True, slots=True)
class ConfigValueSources:
    python_source_roots: ConfigSource
    python_include: ConfigSource
    python_exclude: ConfigSource
    upstream_depth: ConfigSource
    downstream_depth: ConfigSource
    max_entities: ConfigSource


@dataclass(frozen=True, slots=True)
class ResolvedConfig:
    schema: str
    python: PythonConfig
    traversal: TraversalConfig
    limits: LimitsConfig
    value_sources: ConfigValueSources
    source: ConfigSource
    sha256: str

    def digest_value(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "python": {
                "source_roots": list(self.python.source_roots),
                "include": list(self.python.include),
                "exclude": list(self.python.exclude),
            },
            "traversal": {
                "upstream_depth": self.traversal.upstream_depth,
                "downstream_depth": self.traversal.downstream_depth,
            },
            "limits": {"max_entities": self.limits.max_entities},
        }


class ConfigResolutionError(Exception):
    def __init__(self, value: Diagnostic) -> None:
        super().__init__(value.message)
        self.diagnostic = value


_SCHEMA: Final = "code-structure-viz.config/v1"
_TOP_LEVEL_KEYS: Final = frozenset({"schema", "python", "traversal", "limits"})
_PYTHON_KEYS: Final = frozenset({"source_roots", "include", "exclude"})
_TRAVERSAL_KEYS: Final = frozenset({"upstream_depth", "downstream_depth"})
_LIMIT_KEYS: Final = frozenset({"max_entities"})
_TOP_LEVEL_MISSING_KEYS: Final[dict[str, str]] = {
    "schema": "schema",
    "python": "python.source_roots",
    "traversal": "traversal.upstream_depth",
    "limits": "limits.max_entities",
}
_MAX_GLOB_PATTERNS: Final = 256
_MAX_GLOB_LENGTH: Final = 4096
_MAX_GLOB_SEGMENTS: Final = 256


def _error(code: DiagnosticCode, *, key: str | None = None) -> ConfigResolutionError:
    return ConfigResolutionError(diagnostic(code, key=key))


def _normalize_string(value: object, *, key: str) -> str:
    if not isinstance(value, str):
        raise _error(DiagnosticCode.CONFIG_VALUE, key=key)
    return unicodedata.normalize("NFC", value)


def _string_array(value: object, *, key: str, allow_empty: bool) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise _error(DiagnosticCode.CONFIG_VALUE, key=key)
    result = tuple(_normalize_string(item, key=key) for item in value)
    if not allow_empty and not result:
        raise _error(DiagnosticCode.CONFIG_VALUE, key=key)
    if len(result) != len(set(result)):
        raise _error(DiagnosticCode.CONFIG_VALUE, key=key)
    return result


def _integer(value: object, *, key: str, positive: bool) -> int:
    if type(value) is not int:
        raise _error(DiagnosticCode.CONFIG_VALUE, key=key)
    parsed = value
    if parsed < (1 if positive else 0):
        raise _error(DiagnosticCode.CONFIG_VALUE, key=key)
    return parsed


def _validate_source_root(value: str, *, repo: Path, require_exists: bool) -> None:
    path = PurePosixPath(value)
    if (
        not value
        or "\\" in value
        or path.is_absolute()
        or value != path.as_posix()
        or any(part in {"", ".."} for part in path.parts)
    ):
        raise _error(DiagnosticCode.CONFIG_VALUE, key="python.source_roots")
    if value != "." and any(part == "." for part in path.parts):
        raise _error(DiagnosticCode.CONFIG_VALUE, key="python.source_roots")
    if not require_exists:
        return
    candidate = repo.joinpath(*path.parts).resolve(strict=False)
    try:
        common = os.path.commonpath((str(repo.resolve()), str(candidate)))
    except ValueError as exc:
        raise _error(DiagnosticCode.CONFIG_VALUE, key="python.source_roots") from exc
    if common != str(repo.resolve()) or not candidate.is_dir():
        raise _error(DiagnosticCode.CONFIG_VALUE, key="python.source_roots")


def _validate_glob(value: str, *, key: str) -> None:
    path = PurePosixPath(value)
    if (
        not value
        or len(value) > _MAX_GLOB_LENGTH
        or len(path.parts) > _MAX_GLOB_SEGMENTS
        or "\\" in value
        or path.is_absolute()
        or any(token in value for token in ("!", "[", "]", "{", "}"))
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise _error(DiagnosticCode.CONFIG_VALUE, key=key)
    for part in path.parts:
        if "**" in part and part != "**":
            raise _error(DiagnosticCode.CONFIG_VALUE, key=key)


def _closed_table(value: object, *, expected: frozenset[str]) -> dict[str, object]:
    if not isinstance(value, dict):
        raise _error(DiagnosticCode.CONFIG_VALUE, key="schema")
    table = cast(dict[object, object], value)
    if any(not isinstance(key, str) for key in table):
        raise _error(DiagnosticCode.CONFIG_UNKNOWN_KEY)
    typed = cast(dict[str, object], table)
    if set(typed) - expected:
        raise _error(DiagnosticCode.CONFIG_UNKNOWN_KEY)
    return typed


def _decode_config(data: object, *, source: ConfigSource, repo: Path) -> ResolvedConfig:
    root = _closed_table(data, expected=_TOP_LEVEL_KEYS)
    if set(root) != _TOP_LEVEL_KEYS:
        safe_key = min(
            (_TOP_LEVEL_MISSING_KEYS[item] for item in _TOP_LEVEL_KEYS - set(root)),
            key=lambda item: item.encode("utf-8"),
        )
        raise _error(DiagnosticCode.CONFIG_VALUE, key=safe_key)
    if root["schema"] != _SCHEMA:
        raise _error(DiagnosticCode.CONFIG_VALUE, key="schema")
    python = _closed_table(root["python"], expected=_PYTHON_KEYS)
    traversal = _closed_table(root["traversal"], expected=_TRAVERSAL_KEYS)
    limits = _closed_table(root["limits"], expected=_LIMIT_KEYS)
    if set(python) != _PYTHON_KEYS:
        key = min(
            (f"python.{item}" for item in _PYTHON_KEYS - set(python)),
            key=lambda item: item.encode("utf-8"),
        )
        raise _error(DiagnosticCode.CONFIG_VALUE, key=key)
    if set(traversal) != _TRAVERSAL_KEYS:
        key = min(
            (f"traversal.{item}" for item in _TRAVERSAL_KEYS - set(traversal)),
            key=lambda item: item.encode("utf-8"),
        )
        raise _error(DiagnosticCode.CONFIG_VALUE, key=key)
    if set(limits) != _LIMIT_KEYS:
        raise _error(DiagnosticCode.CONFIG_VALUE, key="limits.max_entities")

    source_roots = _string_array(
        python["source_roots"], key="python.source_roots", allow_empty=False
    )
    include = _string_array(python["include"], key="python.include", allow_empty=False)
    exclude = _string_array(python["exclude"], key="python.exclude", allow_empty=True)
    if len(include) > _MAX_GLOB_PATTERNS:
        raise _error(DiagnosticCode.CONFIG_VALUE, key="python.include")
    if len(exclude) > _MAX_GLOB_PATTERNS:
        raise _error(DiagnosticCode.CONFIG_VALUE, key="python.exclude")
    for value in source_roots:
        _validate_source_root(value, repo=repo, require_exists=True)
    for value in include:
        _validate_glob(value, key="python.include")
    for value in exclude:
        _validate_glob(value, key="python.exclude")

    value_sources = ConfigValueSources(
        python_source_roots=source,
        python_include=source,
        python_exclude=source,
        upstream_depth=source,
        downstream_depth=source,
        max_entities=source,
    )
    result = ResolvedConfig(
        schema=_SCHEMA,
        python=PythonConfig(source_roots, include, exclude),
        traversal=TraversalConfig(
            _integer(traversal["upstream_depth"], key="traversal.upstream_depth", positive=False),
            _integer(
                traversal["downstream_depth"],
                key="traversal.downstream_depth",
                positive=False,
            ),
        ),
        limits=LimitsConfig(
            _integer(limits["max_entities"], key="limits.max_entities", positive=True)
        ),
        value_sources=value_sources,
        source=source,
        sha256="",
    )
    return _with_digest(result)


def _with_digest(value: ResolvedConfig) -> ResolvedConfig:
    digest = hashlib.sha256(encode_canonical_json(value.digest_value())).hexdigest()
    return replace(value, sha256=digest)


def _builtin(repo: Path) -> ResolvedConfig:
    for root in ("src", "."):
        _validate_source_root(root, repo=repo, require_exists=False)
    result = ResolvedConfig(
        schema=_SCHEMA,
        python=PythonConfig(("src", "."), ("**/*.py",), ()),
        traversal=TraversalConfig(1, 1),
        limits=LimitsConfig(500),
        value_sources=ConfigValueSources(
            ConfigSource.BUILTIN,
            ConfigSource.BUILTIN,
            ConfigSource.BUILTIN,
            ConfigSource.BUILTIN,
            ConfigSource.BUILTIN,
            ConfigSource.BUILTIN,
        ),
        source=ConfigSource.BUILTIN,
        sha256="",
    )
    return _with_digest(result)


def _load(path: Path, *, source: ConfigSource, repo: Path) -> ResolvedConfig:
    try:
        if has_symlink_component(path) or not path.is_file():
            raise OSError
        raw = path.read_bytes()
    except OSError as exc:
        raise _error(DiagnosticCode.CONFIG_READ) from exc
    try:
        parsed = tomllib.loads(raw.decode("utf-8", errors="strict"))
    except UnicodeDecodeError as exc:
        raise _error(DiagnosticCode.CONFIG_TOML) from exc
    except tomllib.TOMLDecodeError as exc:
        raise _error(DiagnosticCode.CONFIG_TOML) from exc
    return _decode_config(parsed, source=source, repo=repo)


def resolve_config(request: SnapshotCliRequest, repo: Path) -> ResolvedConfig:
    """Resolve exactly one config source and then apply CLI overrides."""
    repository_path = repo / ".code-structure-viz.toml"
    if request.config_path is not None:
        resolved = _load(request.config_path, source=ConfigSource.EXPLICIT, repo=repo)
    elif repository_path.exists() or repository_path.is_symlink():
        resolved = _load(repository_path, source=ConfigSource.REPOSITORY, repo=repo)
    else:
        resolved = _builtin(repo)

    traversal = resolved.traversal
    limits = resolved.limits
    sources = resolved.value_sources
    if request.upstream_depth_override is not None:
        traversal = replace(traversal, upstream_depth=request.upstream_depth_override)
        sources = replace(sources, upstream_depth=ConfigSource.CLI)
    if request.downstream_depth_override is not None:
        traversal = replace(traversal, downstream_depth=request.downstream_depth_override)
        sources = replace(sources, downstream_depth=ConfigSource.CLI)
    if request.max_entities_override is not None:
        limits = replace(limits, max_entities=request.max_entities_override)
        sources = replace(sources, max_entities=ConfigSource.CLI)
    return _with_digest(
        replace(resolved, traversal=traversal, limits=limits, value_sources=sources)
    )
