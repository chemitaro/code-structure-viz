from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from code_structure_viz.core.diagnostics import Diagnostic, DiagnosticCode, diagnostic
from code_structure_viz.core.path_safety import lexical_absolute
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


@dataclass(frozen=True, slots=True)
class DiffCliRequest:
    repo: Path
    output_dir: Path
    domain: Literal["python"]
    config_path: Path | None
    from_ref: str | None
    to_ref: str | None
    pr_target: str | None
    upstream_depth_override: int | None
    downstream_depth_override: int | None
    max_changed_paths_override: int | None
    max_entities_override: int | None
    formats: tuple[OutputFormat, ...]
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


@dataclass(frozen=True, slots=True)
class _UsageCandidate:
    phase: int
    index: int
    code: DiagnosticCode
    option: str | None = None


def _usage(code: DiagnosticCode, *, option: str | None = None) -> CliUsageError:
    return CliUsageError(diagnostic(code, option=option))


def _parse_non_negative(value: str) -> int:
    if _ASCII_DECIMAL.fullmatch(value) is None:
        raise _usage(DiagnosticCode.USAGE_GRAMMAR)
    parsed = 0
    for offset in range(0, len(value), 9):
        chunk = value[offset : offset + 9]
        parsed = parsed * (10 ** len(chunk)) + int(chunk, 10)
    return parsed


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


def _candidate_error(candidates: list[_UsageCandidate]) -> None:
    if not candidates:
        return
    selected = min(candidates, key=lambda item: (item.phase, item.index))
    raise _usage(selected.code, option=selected.option)


def _validate_usage_priority(argv: Sequence[str]) -> None:
    if not argv:
        raise _usage(DiagnosticCode.USAGE_GRAMMAR)
    if argv[0] == "diff":
        raise _usage(DiagnosticCode.USAGE_DIFF_OPTION, option="diff")
    if argv[0] != "snapshot":
        raise _usage(DiagnosticCode.USAGE_GRAMMAR)

    candidates: list[_UsageCandidate] = []
    occurrences: dict[str, list[tuple[int, int, str]]] = {}
    index = 1
    while index < len(argv):
        option = argv[index]
        if option.startswith("--") and "=" in option:
            candidates.append(_UsageCandidate(0, index, DiagnosticCode.USAGE_GRAMMAR))
            index += 1
            continue
        if option in _DIFF_OPTIONS:
            candidates.append(_UsageCandidate(2, index, DiagnosticCode.USAGE_DIFF_OPTION, option))
            if index + 1 < len(argv) and not argv[index + 1].startswith("--"):
                index += 2
            else:
                index += 1
            continue
        if option not in _SINGLE_OPTIONS and option not in _REPEATABLE_OPTIONS:
            candidates.append(_UsageCandidate(0, index, DiagnosticCode.USAGE_GRAMMAR))
            index += 1
            continue
        if index + 1 >= len(argv) or argv[index + 1].startswith("--"):
            candidates.append(
                _UsageCandidate(
                    3 if option == "--stdout" else 0,
                    index,
                    (
                        DiagnosticCode.USAGE_STDOUT_SYNTAX
                        if option == "--stdout"
                        else DiagnosticCode.USAGE_GRAMMAR
                    ),
                )
            )
            index += 1
            continue
        occurrences.setdefault(option, []).append((index, index + 1, argv[index + 1]))
        index += 2

    for option in _SINGLE_OPTIONS:
        values = occurrences.get(option, [])
        for option_index, _value_index, _value in values[1:]:
            candidates.append(
                _UsageCandidate(1, option_index, DiagnosticCode.USAGE_DUPLICATE, option)
            )
    required = {"--repo", "--output-dir", "--domain"}
    if any(not occurrences.get(option) for option in required):
        candidates.append(_UsageCandidate(0, len(argv), DiagnosticCode.USAGE_GRAMMAR))

    domain_values = occurrences.get("--domain", [])
    if domain_values and domain_values[0][2] != "python":
        candidates.append(_UsageCandidate(0, domain_values[0][1], DiagnosticCode.USAGE_GRAMMAR))

    format_values = occurrences.get("--format", [])
    seen_formats: set[str] = set()
    for option_index, _value_index, value in format_values:
        if value not in {"semantic-json", "plantuml"} or value in seen_formats:
            candidates.append(_UsageCandidate(0, option_index, DiagnosticCode.USAGE_GRAMMAR))
        seen_formats.add(value)

    target_values = occurrences.get("--target", [])
    for _option_index, value_index, value in target_values:
        try:
            parse_target(unicodedata.normalize("NFC", value))
        except ValueError:
            candidates.append(_UsageCandidate(0, value_index, DiagnosticCode.USAGE_GRAMMAR))

    for option in ("--upstream-depth", "--downstream-depth"):
        values = occurrences.get(option, [])
        if values:
            option_index, value_index, value = values[0]
            if _ASCII_DECIMAL.fullmatch(value) is None:
                candidates.append(_UsageCandidate(0, value_index, DiagnosticCode.USAGE_GRAMMAR))
            if not target_values:
                candidates.append(_UsageCandidate(0, option_index, DiagnosticCode.USAGE_GRAMMAR))

    max_values = occurrences.get("--max-entities", [])
    if max_values:
        _option_index, value_index, value = max_values[0]
        if _ASCII_DECIMAL.fullmatch(value) is None or not value.strip("0"):
            candidates.append(_UsageCandidate(0, value_index, DiagnosticCode.USAGE_GRAMMAR))

    stdout_values = occurrences.get("--stdout", [])
    if stdout_values:
        option_index, _value_index, value = stdout_values[0]
        try:
            selector = _parse_stdout(value)
        except CliUsageError:
            candidates.append(_UsageCandidate(3, option_index, DiagnosticCode.USAGE_STDOUT_SYNTAX))
        else:
            resolved_formats = {item[2] for item in format_values} or {"semantic-json", "plantuml"}
            if isinstance(selector, DomainFormatSelector) and (
                selector.domain != "python" or selector.format not in resolved_formats
            ):
                candidates.append(
                    _UsageCandidate(4, option_index, DiagnosticCode.USAGE_STDOUT_COMPATIBILITY)
                )

    _candidate_error(candidates)


def parse_cli(argv: Sequence[str]) -> SnapshotCliRequest:
    """Parse the closed snapshot command grammar."""
    _validate_usage_priority(argv)

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
        return lexical_absolute(path)

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


_DIFF_SINGLE_OPTIONS = frozenset(
    {
        "--repo",
        "--output-dir",
        "--domain",
        "--config",
        "--from",
        "--to",
        "--pr-target",
        "--upstream-depth",
        "--downstream-depth",
        "--max-changed-paths",
        "--max-entities",
        "--stdout",
    }
)


def _validate_diff_argv(argv: Sequence[str]) -> dict[str, list[tuple[int, int, str]]]:
    if not argv or argv[0] != "diff":
        raise _usage(DiagnosticCode.USAGE_GRAMMAR)
    occurrences: dict[str, list[tuple[int, int, str]]] = {}
    candidates: list[_UsageCandidate] = []
    index = 1
    while index < len(argv):
        option = argv[index]
        if option.startswith("--") and "=" in option:
            candidates.append(_UsageCandidate(0, index, DiagnosticCode.USAGE_GRAMMAR))
            index += 1
            continue
        if option not in _DIFF_SINGLE_OPTIONS and option != "--format":
            candidates.append(_UsageCandidate(0, index, DiagnosticCode.USAGE_GRAMMAR))
            index += 1
            continue
        if index + 1 >= len(argv) or argv[index + 1].startswith("--"):
            candidates.append(
                _UsageCandidate(
                    3 if option == "--stdout" else 0,
                    index,
                    DiagnosticCode.USAGE_STDOUT_SYNTAX
                    if option == "--stdout"
                    else DiagnosticCode.USAGE_GRAMMAR,
                    option if option == "--stdout" else None,
                )
            )
            index += 1
            continue
        occurrences.setdefault(option, []).append((index, index + 1, argv[index + 1]))
        index += 2

    for option in _DIFF_SINGLE_OPTIONS:
        values = occurrences.get(option, [])
        for option_index, _value_index, _value in values[1:]:
            candidates.append(
                _UsageCandidate(1, option_index, DiagnosticCode.USAGE_DUPLICATE, option)
            )
    for option in ("--repo", "--output-dir", "--domain"):
        if not occurrences.get(option):
            candidates.append(_UsageCandidate(0, len(argv), DiagnosticCode.USAGE_GRAMMAR))
    domain_values = occurrences.get("--domain", [])
    if domain_values and domain_values[0][2] != "python":
        candidates.append(_UsageCandidate(0, domain_values[0][1], DiagnosticCode.USAGE_GRAMMAR))
    format_values = occurrences.get("--format", [])
    seen_formats: set[str] = set()
    for option_index, _value_index, value in format_values:
        if value not in {"semantic-json", "plantuml"} or value in seen_formats:
            candidates.append(_UsageCandidate(0, option_index, DiagnosticCode.USAGE_GRAMMAR))
        seen_formats.add(value)
    for option in ("--upstream-depth", "--downstream-depth"):
        values = occurrences.get(option, [])
        if values and _ASCII_DECIMAL.fullmatch(values[0][2]) is None:
            candidates.append(_UsageCandidate(0, values[0][1], DiagnosticCode.USAGE_GRAMMAR))
    for option in ("--max-changed-paths", "--max-entities"):
        values = occurrences.get(option, [])
        if values:
            value = values[0][2]
            if _ASCII_DECIMAL.fullmatch(value) is None or not value.strip("0"):
                candidates.append(_UsageCandidate(0, values[0][1], DiagnosticCode.USAGE_GRAMMAR))
    stdout_values = occurrences.get("--stdout", [])
    if stdout_values:
        option_index, _value_index, value = stdout_values[0]
        try:
            selector = _parse_stdout(value)
        except CliUsageError:
            candidates.append(_UsageCandidate(3, option_index, DiagnosticCode.USAGE_STDOUT_SYNTAX))
        else:
            resolved_formats = {item[2] for item in format_values} or {
                "semantic-json",
                "plantuml",
            }
            if isinstance(selector, DomainFormatSelector) and (
                selector.domain != "python" or selector.format not in resolved_formats
            ):
                candidates.append(
                    _UsageCandidate(4, option_index, DiagnosticCode.USAGE_STDOUT_COMPATIBILITY)
                )
    _candidate_error(candidates)
    return occurrences


def parse_diff_cli(argv: Sequence[str]) -> DiffCliRequest:
    """Parse the closed Python ``diff`` command grammar."""
    occurrences = _validate_diff_argv(argv)
    values = {option: entries[0][2] for option, entries in occurrences.items()}
    if values.get("--from") == "working-tree":
        raise _usage(DiagnosticCode.USAGE_GRAMMAR)
    formats_raw = [item[2] for item in occurrences.get("--format", [])]
    resolved_formats: tuple[OutputFormat, ...]
    if not formats_raw:
        resolved_formats = ("semantic-json", "plantuml")
    else:
        resolved_formats = cast(
            tuple[OutputFormat, ...],
            tuple(value for value in ("semantic-json", "plantuml") if value in formats_raw),
        )

    def resolve_path(raw: str) -> Path:
        path = Path(raw)
        if not path.is_absolute():
            path = Path.cwd() / path
        return lexical_absolute(path)

    stdout_selector = _parse_stdout(values["--stdout"]) if "--stdout" in values else None
    return DiffCliRequest(
        repo=resolve_path(values["--repo"]),
        output_dir=resolve_path(values["--output-dir"]),
        domain="python",
        config_path=resolve_path(values["--config"]) if "--config" in values else None,
        from_ref=values.get("--from"),
        to_ref=values.get("--to"),
        pr_target=values.get("--pr-target"),
        upstream_depth_override=(
            _parse_non_negative(values["--upstream-depth"])
            if "--upstream-depth" in values
            else None
        ),
        downstream_depth_override=(
            _parse_non_negative(values["--downstream-depth"])
            if "--downstream-depth" in values
            else None
        ),
        max_changed_paths_override=(
            _parse_positive(values["--max-changed-paths"])
            if "--max-changed-paths" in values
            else None
        ),
        max_entities_override=(
            _parse_positive(values["--max-entities"]) if "--max-entities" in values else None
        ),
        formats=resolved_formats,
        stdout_selector=stdout_selector,
    )
