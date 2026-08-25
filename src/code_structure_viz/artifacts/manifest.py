from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Literal

from code_structure_viz import __version__
from code_structure_viz.adapters.python.model import PythonCoverage
from code_structure_viz.adapters.python.semantic_json import coverage_value, target_value
from code_structure_viz.cli.parser import (
    DomainFormatSelector,
    ManifestSelector,
    OutputFormat,
    SnapshotCliRequest,
    StdoutSelector,
)
from code_structure_viz.core.budget import EntityBudget
from code_structure_viz.core.config import ResolvedConfig
from code_structure_viz.core.diagnostics import canonical_diagnostics
from code_structure_viz.core.outcomes import DomainOutcome, DomainStatus, RunOutcome
from code_structure_viz.semantic.canonical_json import encode_canonical_json
from code_structure_viz.source.source_view import SourceView
from code_structure_viz.source.targets import target_sort_key

ArtifactFormat = Literal["semantic-json", "plantuml"]

_ARTIFACT_CONTRACT = {
    "semantic-json": (
        "python.snapshot.semantic.json",
        "application/json",
    ),
    "plantuml": (
        "python.snapshot.puml",
        "text/vnd.plantuml; charset=utf-8",
    ),
}
_FORMAT_RANK = {"semantic-json": 0, "plantuml": 1}


@dataclass(frozen=True, slots=True)
class ArtifactDescriptor:
    path: str
    domain: Literal["python"]
    format: ArtifactFormat
    media_type: str
    size_bytes: int
    sha256: str

    @classmethod
    def create(cls, format_value: ArtifactFormat, content: bytes) -> ArtifactDescriptor:
        path, media_type = _ARTIFACT_CONTRACT[format_value]
        return cls(
            path=path,
            domain="python",
            format=format_value,
            media_type=media_type,
            size_bytes=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
        )

    def to_json_value(self) -> dict[str, object]:
        return {
            "path": self.path,
            "domain": self.domain,
            "format": self.format,
            "media_type": self.media_type,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
        }


def _selector_value(selector: StdoutSelector | None) -> str | None:
    if selector is None:
        return None
    if isinstance(selector, ManifestSelector):
        return selector.value
    assert isinstance(selector, DomainFormatSelector)
    return f"{selector.domain}:{selector.format}"


def _command_value(request: SnapshotCliRequest) -> dict[str, object]:
    return {
        "name": "snapshot",
        "domain": request.domain,
        "formats": list(request.formats),
        "stdout_selector": _selector_value(request.stdout_selector),
    }


def _request_value(request: SnapshotCliRequest, config: ResolvedConfig) -> dict[str, object]:
    return {
        "targets": [target_value(item) for item in sorted(request.targets, key=target_sort_key)],
        "upstream_depth": config.traversal.upstream_depth,
        "downstream_depth": config.traversal.downstream_depth,
    }


def _source_value(source_view: SourceView) -> dict[str, object]:
    return {
        "schema": source_view.schema,
        "kind": source_view.kind,
        "head_commit": source_view.head_commit,
        "fingerprint": source_view.fingerprint,
        "file_count": len(source_view.files),
    }


def _config_value(config: ResolvedConfig) -> dict[str, object]:
    return {
        "schema": config.schema,
        "source": config.source.value,
        "sha256": config.sha256,
        "resolved": {
            "python": {
                "source_roots": list(config.python.source_roots),
                "include": list(config.python.include),
                "exclude": list(config.python.exclude),
            },
            "traversal": {
                "upstream_depth": config.traversal.upstream_depth,
                "downstream_depth": config.traversal.downstream_depth,
            },
            "limits": {"max_entities": config.limits.max_entities},
        },
        "value_sources": {
            "python_source_roots": config.value_sources.python_source_roots.value,
            "python_include": config.value_sources.python_include.value,
            "python_exclude": config.value_sources.python_exclude.value,
            "upstream_depth": config.value_sources.upstream_depth.value,
            "downstream_depth": config.value_sources.downstream_depth.value,
            "max_entities": config.value_sources.max_entities.value,
        },
    }


def _run_fingerprint(
    request: SnapshotCliRequest,
    source_view: SourceView,
    config: ResolvedConfig,
) -> str:
    preimage = {
        "schema": "code-structure-viz.run-fingerprint/v1",
        "tool_version": __version__,
        "adapter_version": "python-ast/1",
        "source_fingerprint": source_view.fingerprint,
        "config_sha256": config.sha256,
        "command": _command_value(request),
        "request": _request_value(request, config),
    }
    return hashlib.sha256(encode_canonical_json(preimage)).hexdigest()


def _domain_value(domain: DomainOutcome) -> dict[str, object]:
    if not isinstance(domain.coverage, PythonCoverage):
        raise ValueError("manifest domain requires Python coverage")
    if not isinstance(domain.budget, EntityBudget):
        raise ValueError("manifest domain requires an entity budget")
    value: dict[str, object] = {
        "domain": "python",
        "status": domain.status.value,
    }
    if domain.status is DomainStatus.INCOMPLETE:
        if domain.incomplete_kind is None:
            raise ValueError("incomplete domain requires an incomplete kind")
        value["incomplete_kind"] = domain.incomplete_kind.value
    value.update(
        {
            "payload_available": domain.payload_available,
            "entity_count": domain.entity_count,
            "coverage": coverage_value(domain.coverage),
            "budget": domain.budget.to_json_value(),
            "artifact_paths": list(domain.artifact_paths),
            "diagnostics": [
                item.to_json_value() for item in canonical_diagnostics(domain.diagnostics)
            ],
        }
    )
    return value


class RunManifestBuilder:
    def render(
        self,
        *,
        request: SnapshotCliRequest,
        source_view: SourceView,
        config: ResolvedConfig,
        outcome: RunOutcome,
        artifacts: tuple[ArtifactDescriptor, ...],
    ) -> bytes:
        if len(outcome.domains) != 1 or outcome.manifest_relative_path != "run-manifest.json":
            raise ValueError("manifest requires exactly one committed Python domain")
        ordered_artifacts = tuple(
            sorted(
                artifacts,
                key=lambda item: (_FORMAT_RANK[item.format], item.path.encode("utf-8")),
            )
        )
        if tuple(item.path for item in ordered_artifacts) != outcome.domains[0].artifact_paths:
            raise ValueError("domain artifact paths and descriptors do not match")
        if any(
            item.path != _ARTIFACT_CONTRACT[item.format][0]
            or item.media_type != _ARTIFACT_CONTRACT[item.format][1]
            for item in ordered_artifacts
        ):
            raise ValueError("artifact descriptor violates the closed contract")

        value = {
            "type": "run_manifest",
            "schema": "code-structure-viz.run-manifest/v1",
            "tool": {"name": "code-structure-viz", "version": __version__},
            "contracts": {
                "config": "code-structure-viz.config/v1",
                "diagnostic": "code-structure-viz.diagnostic/v1",
                "source_view": "code-structure-viz.source-view/v1",
                "semantic": "code-structure-viz.semantic/v1",
                "manifest": "code-structure-viz.run-manifest/v1",
                "run_summary": "code-structure-viz.run-summary/v1",
                "stdout_result": "code-structure-viz.stdout-result/v1",
                "plantuml": "code-structure-viz.plantuml/python/v1",
            },
            "adapters": [{"domain": "python", "name": "python-ast", "version": "1"}],
            "command": _command_value(request),
            "request": _request_value(request, config),
            "source": _source_value(source_view),
            "config": _config_value(config),
            "run": {
                "status": outcome.status.value,
                "exit_code": outcome.exit_code,
                "fingerprint": _run_fingerprint(request, source_view, config),
            },
            "domains": [_domain_value(outcome.domains[0])],
            "artifacts": [item.to_json_value() for item in ordered_artifacts],
            "diagnostics": [
                item.to_json_value() for item in canonical_diagnostics(outcome.diagnostics)
            ],
        }
        return encode_canonical_json(value)


def artifact_format(value: OutputFormat) -> ArtifactFormat:
    return value
