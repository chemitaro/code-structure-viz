from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from code_structure_viz.core.diagnostics import Diagnostic, DiagnosticCode, diagnostic
from code_structure_viz.source.targets import TargetSpec, parse_target, target_sort_key

OutputFormat = Literal["semantic-json", "plantuml"]


@dataclass(frozen=True, slots=True)
class ManifestSelector:
    value: Literal["manifest"] = "manifest"


@dataclass(frozen=True, slots=True)
class DomainFormatSelector:
    domain: str
    format: OutputFormat


StdoutSelector = ManifestSelector | DomainFormatSelector


@dataclass(frozen=True, slots=True)
class SnapshotCliRequest:
    repo: Path
    output_dir: Path
    domain: Literal["python"]
    config_path: Path | None
    targets: tuple[TargetSpec, ...]
    upstream_depth_override: int | None
    downstream_depth_override: int | None
    formats: tuple[OutputFormat, ...]
    max_entities_override: int | None
    stdout_selector: StdoutSelector | None


class CliUsageError(Exception):
    def __init__(self, value: Diagnostic) -> None:
        super().__init__(value.message)
        self.diagnostic = value


_SINGLE_OPTIONS = frozenset(
    {
        "--repo",
        "--output-dir",
        "--domain",
        "--config",
        "--upstream-depth",
        "--downstream-depth",
        "--max-entities",
        "--stdout",
    }
)
_REPEATABLE_OPTIONS = frozenset({"--target", "--format"})
_DIFF_OPTIONS = frozenset({"--from", "--to", "--pr-target", "--max-changed-paths"})
_ASCII_DECIMAL = re.compile(r"[0-9]+\Z", flags=re.ASCII)


def _usage(code: DiagnosticCode, *, option: str | None = None) -> CliUsageError:
    return CliUsageError(diagnostic(code, option=option))


def _parse_non_negative(value: str) -> int:
    if _ASCII_DECIMAL.fullmatch(value) is None:
        raise _usage(DiagnosticCode.USAGE_GRAMMAR)
    return int(value, 10)


def _parse_positive(value: str) -> int:
    parsed = _parse_non_negative(value)
    if parsed == 0:
        raise _usage(DiagnosticCode.USAGE_GRAMMAR)
    return parsed


def _parse_stdout(value: str) -> StdoutSelector:
    if value == "manifest":
        return ManifestSelector()
    parts = value.split(":")
    if len(parts) != 2:
        raise _usage(DiagnosticCode.USAGE_STDOUT_SYNTAX)
    domain, format_value = parts
    if domain not in {"python", "sqlalchemy", "next"} or format_value not in {
        "semantic-json",
        "plantuml",
    }:
        raise _usage(DiagnosticCode.USAGE_STDOUT_SYNTAX)
    return DomainFormatSelector(domain=domain, format=format_value)  # type: ignore[arg-type]


def parse_cli(argv: Sequence[str]) -> SnapshotCliRequest:
    """Parse the closed snapshot command grammar."""
    if not argv:
        raise _usage(DiagnosticCode.USAGE_GRAMMAR)
    if argv[0] == "diff":
        raise _usage(DiagnosticCode.USAGE_DIFF_OPTION, option="diff")
    if argv[0] != "snapshot":
        raise _usage(DiagnosticCode.USAGE_GRAMMAR)

    values: dict[str, str] = {}
    targets: list[str] = []
    formats: list[str] = []
    index = 1
    while index < len(argv):
        option = argv[index]
        if option in _DIFF_OPTIONS:
            raise _usage(DiagnosticCode.USAGE_DIFF_OPTION, option=option)
        if option.startswith("--") and "=" in option:
            raise _usage(DiagnosticCode.USAGE_GRAMMAR)
        if option not in _SINGLE_OPTIONS and option not in _REPEATABLE_OPTIONS:
            raise _usage(DiagnosticCode.USAGE_GRAMMAR)
        if index + 1 >= len(argv) or argv[index + 1].startswith("--"):
            code = (
                DiagnosticCode.USAGE_STDOUT_SYNTAX
                if option == "--stdout"
                else DiagnosticCode.USAGE_GRAMMAR
            )
            raise _usage(code)
        raw_value = argv[index + 1]
        if option in _SINGLE_OPTIONS:
            if option in values:
                raise _usage(DiagnosticCode.USAGE_DUPLICATE, option=option)
            values[option] = raw_value
        elif option == "--target":
            targets.append(unicodedata.normalize("NFC", raw_value))
        else:
            formats.append(raw_value)
        index += 2

    if not {"--repo", "--output-dir", "--domain"}.issubset(values):
        raise _usage(DiagnosticCode.USAGE_GRAMMAR)
    if values["--domain"] != "python":
        raise _usage(DiagnosticCode.USAGE_GRAMMAR)
    if len(formats) != len(set(formats)) or any(
        value not in {"semantic-json", "plantuml"} for value in formats
    ):
        raise _usage(DiagnosticCode.USAGE_GRAMMAR)

    upstream = (
        _parse_non_negative(values["--upstream-depth"]) if "--upstream-depth" in values else None
    )
    downstream = (
        _parse_non_negative(values["--downstream-depth"])
        if "--downstream-depth" in values
        else None
    )
    try:
        typed_targets = {parse_target(value) for value in targets}
    except ValueError as exc:
        raise _usage(DiagnosticCode.USAGE_GRAMMAR) from exc
    normalized_targets = tuple(sorted(typed_targets, key=target_sort_key))
    if (upstream is not None or downstream is not None) and not normalized_targets:
        raise _usage(DiagnosticCode.USAGE_GRAMMAR)
    max_entities = _parse_positive(values["--max-entities"]) if "--max-entities" in values else None

    resolved_formats: tuple[OutputFormat, ...]
    if not formats:
        resolved_formats = ("semantic-json", "plantuml")
    else:
        resolved_formats = cast(
            tuple[OutputFormat, ...],
            tuple(value for value in ("semantic-json", "plantuml") if value in formats),
        )
    stdout_selector = _parse_stdout(values["--stdout"]) if "--stdout" in values else None
    if isinstance(stdout_selector, DomainFormatSelector) and (
        stdout_selector.domain != "python" or stdout_selector.format not in resolved_formats
    ):
        raise _usage(DiagnosticCode.USAGE_STDOUT_COMPATIBILITY)

    invocation_cwd = Path.cwd()

    def resolve_path(raw: str) -> Path:
        path = Path(raw)
        if not path.is_absolute():
            path = invocation_cwd / path
        return path.resolve(strict=False)

    return SnapshotCliRequest(
        repo=resolve_path(values["--repo"]),
        output_dir=resolve_path(values["--output-dir"]),
        domain="python",
        config_path=resolve_path(values["--config"]) if "--config" in values else None,
        targets=normalized_targets,
        upstream_depth_override=upstream,
        downstream_depth_override=downstream,
        formats=resolved_formats,
        max_entities_override=max_entities,
        stdout_selector=stdout_selector,
    )
