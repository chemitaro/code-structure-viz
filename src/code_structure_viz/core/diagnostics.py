from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from code_structure_viz.semantic.canonical_json import encode_canonical_json


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class DiagnosticCode(StrEnum):
    USAGE_GRAMMAR = "CSV-USAGE-001"
    USAGE_DUPLICATE = "CSV-USAGE-002"
    USAGE_DIFF_OPTION = "CSV-USAGE-003"
    USAGE_STDOUT_SYNTAX = "CSV-USAGE-004"
    USAGE_STDOUT_COMPATIBILITY = "CSV-USAGE-005"
    CONFIG_READ = "CSV-CONFIG-001"
    CONFIG_TOML = "CSV-CONFIG-002"
    CONFIG_UNKNOWN_KEY = "CSV-CONFIG-003"
    CONFIG_VALUE = "CSV-CONFIG-004"
    ENV_PYTHON = "CSV-ENV-001"
    ENV_GIT = "CSV-ENV-002"
    REPO_ROOT = "CSV-REPO-001"
    REPO_HEAD = "CSV-REPO-002"
    OUTPUT_DESTINATION = "CSV-OUTPUT-001"
    OUTPUT_INSIDE_REPO = "CSV-OUTPUT-002"
    SOURCE_DRIFT = "CSV-SOURCE-001"
    SOURCE_SYMLINK = "CSV-SOURCE-002"
    SOURCE_NON_UTF8 = "CSV-SOURCE-003"
    SOURCE_PATH_COLLISION = "CSV-SOURCE-004"
    PY_READ = "CSV-PY-001"
    PY_ENCODING = "CSV-PY-002"
    PY_PARSE = "CSV-PY-003"
    PY_MODULE_IDENTITY = "CSV-PY-004"
    PY_MODULE_COLLISION = "CSV-PY-005"
    PY_TARGET_MISSING = "CSV-PY-006"
    PY_TARGET_AMBIGUOUS = "CSV-PY-007"
    PY_REFERENCE_UNKNOWN = "CSV-PY-008"
    PY_CLASS_SCOPE = "CSV-PY-009"
    PY_ENTITY_BUDGET = "CSV-PY-010"
    PY_TYPE_UNSUPPORTED = "CSV-PY-011"
    PY_CLASS_COLLISION = "CSV-PY-012"
    PY_FIELD_CONFLICT = "CSV-PY-013"
    INTERNAL_INVARIANT = "CSV-INTERNAL-001"
    INTERRUPTED = "CSV-INTERRUPT-001"


@dataclass(frozen=True, slots=True)
class _DiagnosticSpec:
    severity: Severity
    recoverable: bool
    message: str


_SPECS: Final[dict[DiagnosticCode, _DiagnosticSpec]] = {
    DiagnosticCode.USAGE_GRAMMAR: _DiagnosticSpec(
        Severity.ERROR, False, "Command line does not match the snapshot v1 grammar."
    ),
    DiagnosticCode.USAGE_DUPLICATE: _DiagnosticSpec(
        Severity.ERROR, False, "Single-value option '{option}' was specified more than once."
    ),
    DiagnosticCode.USAGE_DIFF_OPTION: _DiagnosticSpec(
        Severity.ERROR, False, "Snapshot does not accept diff-only option '{option}'."
    ),
    DiagnosticCode.USAGE_STDOUT_SYNTAX: _DiagnosticSpec(
        Severity.ERROR, False, "Stdout selector is not valid for snapshot v1."
    ),
    DiagnosticCode.USAGE_STDOUT_COMPATIBILITY: _DiagnosticSpec(
        Severity.ERROR,
        False,
        "Stdout selector does not name a selected domain and requested format.",
    ),
    DiagnosticCode.CONFIG_READ: _DiagnosticSpec(
        Severity.ERROR, False, "Configuration file could not be read."
    ),
    DiagnosticCode.CONFIG_TOML: _DiagnosticSpec(
        Severity.ERROR, False, "Configuration is not valid TOML."
    ),
    DiagnosticCode.CONFIG_UNKNOWN_KEY: _DiagnosticSpec(
        Severity.ERROR, False, "Configuration contains an unknown key."
    ),
    DiagnosticCode.CONFIG_VALUE: _DiagnosticSpec(
        Severity.ERROR, False, "Configuration value '{key}' is invalid for config v1."
    ),
    DiagnosticCode.ENV_PYTHON: _DiagnosticSpec(
        Severity.ERROR, False, "Python 3.12 or newer is required."
    ),
    DiagnosticCode.ENV_GIT: _DiagnosticSpec(
        Severity.ERROR, False, "Git 2.39 or newer is required."
    ),
    DiagnosticCode.REPO_ROOT: _DiagnosticSpec(
        Severity.ERROR, False, "Repository path must be an exact Git working-tree root."
    ),
    DiagnosticCode.REPO_HEAD: _DiagnosticSpec(
        Severity.ERROR,
        False,
        "Repository HEAD is neither a resolvable commit nor a valid unborn branch.",
    ),
    DiagnosticCode.OUTPUT_DESTINATION: _DiagnosticSpec(
        Severity.ERROR,
        False,
        "Output destination already exists or cannot be published atomically.",
    ),
    DiagnosticCode.OUTPUT_INSIDE_REPO: _DiagnosticSpec(
        Severity.ERROR, False, "Output destination must be outside the target repository."
    ),
    DiagnosticCode.SOURCE_DRIFT: _DiagnosticSpec(
        Severity.ERROR, False, "Source view changed before publication."
    ),
    DiagnosticCode.SOURCE_SYMLINK: _DiagnosticSpec(
        Severity.ERROR, False, "Python source symlink is unsafe."
    ),
    DiagnosticCode.SOURCE_NON_UTF8: _DiagnosticSpec(
        Severity.ERROR, False, "Repository contains a path that is not valid UTF-8."
    ),
    DiagnosticCode.SOURCE_PATH_COLLISION: _DiagnosticSpec(
        Severity.ERROR, False, "Repository paths are not unique after safe path normalization."
    ),
    DiagnosticCode.PY_READ: _DiagnosticSpec(
        Severity.ERROR, True, "Python source could not be read."
    ),
    DiagnosticCode.PY_ENCODING: _DiagnosticSpec(
        Severity.ERROR, True, "Python source encoding could not be decoded safely."
    ),
    DiagnosticCode.PY_PARSE: _DiagnosticSpec(
        Severity.ERROR,
        True,
        "Python source could not be parsed with the v1 Python 3.12 grammar.",
    ),
    DiagnosticCode.PY_MODULE_IDENTITY: _DiagnosticSpec(
        Severity.ERROR, True, "Python source path does not map to a valid module identity."
    ),
    DiagnosticCode.PY_MODULE_COLLISION: _DiagnosticSpec(
        Severity.ERROR, True, "More than one source file maps to the same Python module identity."
    ),
    DiagnosticCode.PY_TARGET_MISSING: _DiagnosticSpec(
        Severity.ERROR, False, "Requested Python target was not found in the safe source view."
    ),
    DiagnosticCode.PY_TARGET_AMBIGUOUS: _DiagnosticSpec(
        Severity.ERROR, False, "Requested Python target is ambiguous."
    ),
    DiagnosticCode.PY_REFERENCE_UNKNOWN: _DiagnosticSpec(
        Severity.WARNING, True, "Python reference could not be resolved statically."
    ),
    DiagnosticCode.PY_CLASS_SCOPE: _DiagnosticSpec(
        Severity.INFO,
        True,
        "Class declaration outside a direct module or class body is outside Python semantic v1.",
    ),
    DiagnosticCode.PY_ENTITY_BUDGET: _DiagnosticSpec(
        Severity.ERROR, False, "Python entity count exceeds the resolved max-entities limit."
    ),
    DiagnosticCode.PY_TYPE_UNSUPPORTED: _DiagnosticSpec(
        Severity.WARNING, True, "Python type expression was reduced to an unknown marker."
    ),
    DiagnosticCode.PY_CLASS_COLLISION: _DiagnosticSpec(
        Severity.ERROR,
        True,
        "More than one class declaration maps to the same Python class identity.",
    ),
    DiagnosticCode.PY_FIELD_CONFLICT: _DiagnosticSpec(
        Severity.WARNING, True, "Conflicting field annotations were reduced to an unknown marker."
    ),
    DiagnosticCode.INTERNAL_INVARIANT: _DiagnosticSpec(
        Severity.ERROR, False, "Internal snapshot contract invariant failed before publication."
    ),
    DiagnosticCode.INTERRUPTED: _DiagnosticSpec(
        Severity.WARNING, False, "Snapshot was interrupted before publication."
    ),
}

_SAFE_OPTIONS: Final[frozenset[str]] = frozenset(
    {
        "diff",
        "--repo",
        "--output-dir",
        "--domain",
        "--config",
        "--upstream-depth",
        "--downstream-depth",
        "--max-entities",
        "--stdout",
        "--from",
        "--to",
        "--pr-target",
        "--max-changed-paths",
    }
)
_SAFE_CONFIG_KEYS: Final[frozenset[str]] = frozenset(
    {
        "schema",
        "python.source_roots",
        "python.include",
        "python.exclude",
        "traversal.upstream_depth",
        "traversal.downstream_depth",
        "limits.max_entities",
    }
)
_RUN_CONTEXT_CODES: Final[frozenset[DiagnosticCode]] = frozenset(
    {
        DiagnosticCode.USAGE_GRAMMAR,
        DiagnosticCode.USAGE_DUPLICATE,
        DiagnosticCode.USAGE_DIFF_OPTION,
        DiagnosticCode.USAGE_STDOUT_SYNTAX,
        DiagnosticCode.USAGE_STDOUT_COMPATIBILITY,
        DiagnosticCode.CONFIG_READ,
        DiagnosticCode.CONFIG_TOML,
        DiagnosticCode.CONFIG_UNKNOWN_KEY,
        DiagnosticCode.CONFIG_VALUE,
        DiagnosticCode.ENV_PYTHON,
        DiagnosticCode.ENV_GIT,
        DiagnosticCode.REPO_ROOT,
        DiagnosticCode.REPO_HEAD,
        DiagnosticCode.OUTPUT_DESTINATION,
        DiagnosticCode.OUTPUT_INSIDE_REPO,
        DiagnosticCode.SOURCE_DRIFT,
        DiagnosticCode.SOURCE_NON_UTF8,
        DiagnosticCode.INTERNAL_INVARIANT,
        DiagnosticCode.INTERRUPTED,
    }
)


def _validate_context(
    code: DiagnosticCode,
    *,
    domain: str | None,
    path: str | None,
    symbol: str | None,
    line: int | None,
) -> None:
    if line is not None and (type(line) is not int or line <= 0):
        raise ValueError("diagnostic line must be a positive integer or null")
    if code in _RUN_CONTEXT_CODES:
        if any(value is not None for value in (domain, path, symbol, line)):
            raise ValueError("run diagnostic context must be null")
        return
    if domain != "python":
        raise ValueError("Python diagnostic domain must be python")
    if code in {DiagnosticCode.SOURCE_SYMLINK, DiagnosticCode.SOURCE_PATH_COLLISION}:
        if path is None or symbol is not None or line is not None:
            raise ValueError("source path diagnostic context is invalid")
        return
    if code in {
        DiagnosticCode.PY_READ,
        DiagnosticCode.PY_ENCODING,
        DiagnosticCode.PY_MODULE_IDENTITY,
    }:
        if path is None or symbol is not None or line is not None:
            raise ValueError("Python file diagnostic context is invalid")
        return
    if code is DiagnosticCode.PY_PARSE:
        if path is None or symbol is not None:
            raise ValueError("Python parse diagnostic context is invalid")
        return
    if code is DiagnosticCode.PY_MODULE_COLLISION:
        if path is not None or symbol is None or line is not None:
            raise ValueError("Python module collision context is invalid")
        return
    if code in {DiagnosticCode.PY_TARGET_MISSING, DiagnosticCode.PY_TARGET_AMBIGUOUS}:
        if (path is None) == (symbol is None) or line is not None:
            raise ValueError("Python target diagnostic context is invalid")
        return
    if code in {
        DiagnosticCode.PY_REFERENCE_UNKNOWN,
        DiagnosticCode.PY_CLASS_SCOPE,
        DiagnosticCode.PY_TYPE_UNSUPPORTED,
        DiagnosticCode.PY_FIELD_CONFLICT,
    }:
        if path is None or symbol is None or line is None:
            raise ValueError("Python occurrence diagnostic context is invalid")
        return
    if code is DiagnosticCode.PY_ENTITY_BUDGET:
        if any(value is not None for value in (path, symbol, line)):
            raise ValueError("Python budget diagnostic context is invalid")
        return
    if code is DiagnosticCode.PY_CLASS_COLLISION:
        if path is not None or symbol is None or line is not None:
            raise ValueError("Python class collision context is invalid")
        return
    raise ValueError("diagnostic code has no context contract")


@dataclass(frozen=True, slots=True)
class Diagnostic:
    code: DiagnosticCode
    severity: Severity
    domain: str | None
    path: str | None
    symbol: str | None
    line: int | None
    recoverable: bool
    message: str

    def to_json_value(self) -> dict[str, object]:
        return {
            "type": "diagnostic",
            "schema": "code-structure-viz.diagnostic/v1",
            "code": self.code.value,
            "severity": self.severity.value,
            "domain": self.domain,
            "path": self.path,
            "symbol": self.symbol,
            "line": self.line,
            "recoverable": self.recoverable,
            "message": self.message,
        }


def diagnostic(
    code: DiagnosticCode,
    *,
    option: str | None = None,
    key: str | None = None,
    domain: str | None = None,
    path: str | None = None,
    symbol: str | None = None,
    line: int | None = None,
) -> Diagnostic:
    spec = _SPECS[code]
    if option is not None and option not in _SAFE_OPTIONS:
        raise ValueError("unsafe diagnostic option")
    if key is not None and key not in _SAFE_CONFIG_KEYS:
        raise ValueError("unsafe diagnostic config key")
    message = spec.message
    if "{option}" in message:
        if option is None:
            raise ValueError("diagnostic option is required")
        message = message.format(option=option)
    if "{key}" in message:
        if key is None:
            raise ValueError("diagnostic config key is required")
        message = message.format(key=key)
    _validate_context(code, domain=domain, path=path, symbol=symbol, line=line)
    return Diagnostic(
        code=code,
        severity=spec.severity,
        domain=domain,
        path=path,
        symbol=symbol,
        line=line,
        recoverable=spec.recoverable,
        message=message,
    )


def diagnostic_sort_key(value: Diagnostic) -> tuple[object, ...]:
    return (
        value.domain is not None,
        (value.domain or "").encode("utf-8"),
        value.path is not None,
        (value.path or "").encode("utf-8"),
        value.line is not None,
        value.line or 0,
        value.code.value.encode("utf-8"),
        value.symbol is not None,
        (value.symbol or "").encode("utf-8"),
        value.message.encode("utf-8"),
    )


def canonical_diagnostics(values: tuple[Diagnostic, ...]) -> tuple[Diagnostic, ...]:
    unique = {value: None for value in values}
    return tuple(sorted(unique, key=diagnostic_sort_key))


def encode_diagnostic_jsonl(values: tuple[Diagnostic, ...]) -> bytes:
    return b"".join(
        encode_canonical_json(item.to_json_value()) for item in canonical_diagnostics(values)
    )
