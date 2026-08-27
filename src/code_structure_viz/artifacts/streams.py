from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from code_structure_viz.cli.parser import (
    DomainFormatSelector,
    ManifestSelector,
    StdoutSelector,
)
from code_structure_viz.core.diagnostics import (
    canonical_diagnostics,
    encode_diagnostic_jsonl,
)
from code_structure_viz.core.outcomes import (
    DomainStatus,
    IncompleteKind,
    RunOutcome,
    RunStatus,
)
from code_structure_viz.semantic.canonical_json import encode_canonical_json

_DOMAIN_PATHS = {
    "semantic-json": "python.snapshot.semantic.json",
    "plantuml": "python.snapshot.puml",
}
_DIFF_DOMAIN_PATHS = {
    "semantic-json": "python.diff.semantic.json",
    "plantuml": "python.diff.puml",
}


def _selector_value(selector: StdoutSelector) -> str:
    if isinstance(selector, ManifestSelector):
        return selector.value
    return f"{selector.domain}:{selector.format}"


def _summary(outcome: RunOutcome) -> bytes:
    domains: list[dict[str, object]] = []
    for domain in outcome.domains:
        value: dict[str, object] = {
            "domain": "python",
            "status": domain.status.value,
        }
        if domain.status is DomainStatus.INCOMPLETE:
            assert domain.incomplete_kind is not None
            value["incomplete_kind"] = domain.incomplete_kind.value
        domains.append(value)
    return encode_canonical_json(
        {
            "type": "run_summary",
            "schema": "code-structure-viz.run-summary/v1",
            "run_status": outcome.status.value,
            "exit_code": outcome.exit_code,
            "domains": domains,
            "manifest": outcome.manifest_relative_path,
        }
    )


def _domain_unavailable(
    selector: DomainFormatSelector,
    status: DomainStatus,
    reason: str,
) -> bytes:
    return encode_canonical_json(
        {
            "type": "stdout_result",
            "schema": "code-structure-viz.stdout-result/v1",
            "selector": _selector_value(selector),
            "availability": False,
            "domain_status": status.value,
            "stable_reason": reason,
            "artifact": None,
        }
    )


def _run_unavailable(selector: StdoutSelector, status: RunStatus, reason: str) -> bytes:
    return encode_canonical_json(
        {
            "type": "stdout_result",
            "schema": "code-structure-viz.stdout-result/v1",
            "selector": _selector_value(selector),
            "availability": False,
            "run_status": status.value,
            "stable_reason": reason,
            "artifact": None,
        }
    )


class StdoutEmitter:
    def render(
        self,
        outcome: RunOutcome,
        selector: StdoutSelector | None,
        output_dir: Path,
        *,
        published_artifacts: Mapping[str, bytes] | None = None,
    ) -> bytes:
        if outcome.status is RunStatus.USAGE:
            return b""
        if selector is None:
            return _summary(outcome)
        if outcome.status is RunStatus.INTERRUPTED:
            return _run_unavailable(selector, outcome.status, "run_interrupted")
        if outcome.status is RunStatus.FATAL:
            reason = (
                "final_manifest_unavailable"
                if isinstance(selector, ManifestSelector)
                else "run_fatal"
            )
            return _run_unavailable(selector, outcome.status, reason)
        if isinstance(selector, ManifestSelector):
            if outcome.manifest_relative_path is None:
                raise ValueError("committed outcome is missing a manifest")
            if published_artifacts is not None:
                return published_artifacts[outcome.manifest_relative_path]
            return (output_dir / outcome.manifest_relative_path).read_bytes()

        assert isinstance(selector, DomainFormatSelector)
        if len(outcome.domains) != 1:
            raise ValueError("domain selector requires one Python outcome")
        domain = outcome.domains[0]
        if domain.status is DomainStatus.NOT_APPLICABLE:
            return _domain_unavailable(selector, domain.status, "domain_not_applicable")
        if domain.incomplete_kind is IncompleteKind.PAYLOAD_UNAVAILABLE:
            return _domain_unavailable(selector, domain.status, "domain_payload_unavailable")
        candidates = (_DIFF_DOMAIN_PATHS[selector.format], _DOMAIN_PATHS[selector.format])
        relative_path = next(
            (item for item in candidates if item in domain.artifact_paths), None
        )
        if relative_path is None:
            raise ValueError("selected domain artifact was not published")
        if published_artifacts is not None:
            return published_artifacts[relative_path]
        return (output_dir / relative_path).read_bytes()


class StderrEmitter:
    def render(self, outcome: RunOutcome) -> bytes:
        diagnostics = [*outcome.diagnostics]
        for domain in outcome.domains:
            diagnostics.extend(domain.diagnostics)
        return encode_diagnostic_jsonl(canonical_diagnostics(tuple(diagnostics)))
