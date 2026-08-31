from __future__ import annotations

import hashlib
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Literal

from code_structure_viz import __version__
from code_structure_viz.adapters.python.model import PythonCoverage
from code_structure_viz.adapters.python.semantic_json import (
    coverage_value as python_coverage_value,
)
from code_structure_viz.adapters.python.semantic_json import target_value
from code_structure_viz.application.snapshot_domain import SnapshotAdapterContract
from code_structure_viz.cli.parser import (
    DiffCliRequest,
    DomainFormatSelector,
    ManifestSelector,
    OutputFormat,
    SnapshotCliRequest,
    StdoutSelector,
)
from code_structure_viz.core.budget import EntityBudget
from code_structure_viz.core.config import ResolvedConfig
from code_structure_viz.core.diagnostics import canonical_diagnostics
from code_structure_viz.core.domains import DomainName
from code_structure_viz.core.outcomes import DomainOutcome, DomainStatus, RunOutcome
from code_structure_viz.semantic.canonical_json import encode_canonical_json
from code_structure_viz.source.source_view import SourceView
from code_structure_viz.source.targets import target_sort_key

ArtifactFormat = Literal["semantic-json", "plantuml", "file-change-set"]

_SNAPSHOT_ARTIFACT_CONTRACT = {
    ("python", "semantic-json"): (
        "python.snapshot.semantic.json",
        "application/json",
    ),
    ("python", "plantuml"): (
        "python.snapshot.puml",
        "text/vnd.plantuml; charset=utf-8",
    ),
    ("sqlalchemy", "semantic-json"): (
        "sqlalchemy.snapshot.semantic.json",
        "application/json",
    ),
    ("sqlalchemy", "plantuml"): (
        "sqlalchemy.snapshot.puml",
        "text/vnd.plantuml; charset=utf-8",
    ),
}
_DIFF_ARTIFACT_CONTRACT = {
    ("python", "semantic-json"): (
        "python.diff.semantic.json",
        "application/json",
    ),
    ("python", "plantuml"): (
        "python.diff.puml",
        "text/vnd.plantuml; charset=utf-8",
    ),
    ("sqlalchemy", "semantic-json"): (
        "sqlalchemy.diff.semantic.json",
        "application/json",
    ),
    ("sqlalchemy", "plantuml"): (
        "sqlalchemy.diff.puml",
        "text/vnd.plantuml; charset=utf-8",
    ),
    ("python", "file-change-set"): (
        "file-changes.json",
        "application/json",
    ),
    ("sqlalchemy", "file-change-set"): (
        "file-changes.json",
        "application/json",
    ),
}
_FORMAT_RANK = {"semantic-json": 0, "plantuml": 1}
_PYTHON_SNAPSHOT_CONTRACT = SnapshotAdapterContract(
    domain="python",
    adapter_name="python-ast",
    adapter_version="1",
    plantuml_contract="code-structure-viz.plantuml/python/v1",
    semantic_path="python.snapshot.semantic.json",
    plantuml_path="python.snapshot.puml",
)


@dataclass(frozen=True, slots=True)
class ArtifactDescriptor:
    path: str
    domain: DomainName
    format: ArtifactFormat
    media_type: str
    size_bytes: int
    sha256: str

    @classmethod
    def create(cls, format_value: ArtifactFormat, content: bytes) -> ArtifactDescriptor:
        return cls.create_snapshot("python", format_value, content)

    @classmethod
    def create_snapshot(
        cls,
        domain: DomainName,
        format_value: ArtifactFormat,
        content: bytes,
    ) -> ArtifactDescriptor:
        if format_value not in {"semantic-json", "plantuml"}:
            raise ValueError("snapshot artifact format is not supported")
        path, media_type = _SNAPSHOT_ARTIFACT_CONTRACT[(domain, format_value)]
        return cls(
            path=path,
            domain=domain,
            format=format_value,
            media_type=media_type,
            size_bytes=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
        )

    @classmethod
    def create_diff(
        cls,
        domain: DomainName,
        format_value: ArtifactFormat,
        content: bytes,
    ) -> ArtifactDescriptor:
        path, media_type = _DIFF_ARTIFACT_CONTRACT[(domain, format_value)]
        return cls(
            path=path,
            domain=domain,
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
    value: dict[str, object] = {
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
    if config.comparison.target_ref is not None or config.comparison.upstream_ref is not None:
        resolved = value["resolved"]
        assert isinstance(resolved, dict)
        resolved["comparison"] = {
            "target_ref": config.comparison.target_ref,
            "upstream_ref": config.comparison.upstream_ref,
        }
    return value


def _run_fingerprint(
    request: SnapshotCliRequest,
    source_view: SourceView,
    config: ResolvedConfig,
    adapter_contract: SnapshotAdapterContract,
) -> str:
    preimage = {
        "schema": "code-structure-viz.run-fingerprint/v1",
        "tool_version": __version__,
        "adapter_version": (f"{adapter_contract.adapter_name}/{adapter_contract.adapter_version}"),
        "source_fingerprint": source_view.fingerprint,
        "config_sha256": config.sha256,
        "command": _command_value(request),
        "request": _request_value(request, config),
    }
    return hashlib.sha256(encode_canonical_json(preimage)).hexdigest()


def _python_coverage_encoder(value: object) -> Mapping[str, object]:
    if not isinstance(value, PythonCoverage):
        raise ValueError("manifest domain requires Python coverage")
    return python_coverage_value(value)


def _domain_value(
    domain: DomainOutcome,
    expected_domain: DomainName,
    coverage_encoder: Callable[[object], Mapping[str, object]],
) -> dict[str, object]:
    if domain.domain != expected_domain:
        raise ValueError("manifest domain and adapter domain do not match")
    if not isinstance(domain.budget, EntityBudget):
        raise ValueError("manifest domain requires an entity budget")
    coverage = coverage_encoder(domain.coverage)
    value: dict[str, object] = {
        "domain": domain.domain,
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
            "coverage": dict(coverage),
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
        adapter_contract: SnapshotAdapterContract = _PYTHON_SNAPSHOT_CONTRACT,
        coverage_encoder: Callable[[object], Mapping[str, object]] = _python_coverage_encoder,
    ) -> bytes:
        if len(outcome.domains) != 1 or outcome.manifest_relative_path != "run-manifest.json":
            raise ValueError("manifest requires exactly one committed snapshot domain")
        domain = outcome.domains[0]
        if request.domain != adapter_contract.domain or domain.domain != adapter_contract.domain:
            raise ValueError("manifest request, domain, and adapter do not match")
        if any(item.format not in _FORMAT_RANK for item in artifacts):
            raise ValueError("artifact descriptor violates the snapshot contract")
        ordered_artifacts = tuple(
            sorted(
                artifacts,
                key=lambda item: (_FORMAT_RANK[item.format], item.path.encode("utf-8")),
            )
        )
        if tuple(item.path for item in ordered_artifacts) != domain.artifact_paths:
            raise ValueError("domain artifact paths and descriptors do not match")
        if any(
            item.domain != adapter_contract.domain
            or item.path != _SNAPSHOT_ARTIFACT_CONTRACT[(adapter_contract.domain, item.format)][0]
            or item.media_type
            != _SNAPSHOT_ARTIFACT_CONTRACT[(adapter_contract.domain, item.format)][1]
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
                "plantuml": adapter_contract.plantuml_contract,
            },
            "adapters": [
                {
                    "domain": adapter_contract.domain,
                    "name": adapter_contract.adapter_name,
                    "version": adapter_contract.adapter_version,
                }
            ],
            "command": _command_value(request),
            "request": _request_value(request, config),
            "source": _source_value(source_view),
            "config": _config_value(config),
            "run": {
                "status": outcome.status.value,
                "exit_code": outcome.exit_code,
                "fingerprint": _run_fingerprint(
                    request,
                    source_view,
                    config,
                    adapter_contract,
                ),
            },
            "domains": [_domain_value(domain, adapter_contract.domain, coverage_encoder)],
            "artifacts": [item.to_json_value() for item in ordered_artifacts],
            "diagnostics": [
                item.to_json_value() for item in canonical_diagnostics(outcome.diagnostics)
            ],
        }
        return encode_canonical_json(value)


def artifact_format(value: OutputFormat) -> ArtifactFormat:
    return value


class DiffManifestBuilder:
    """Render one first-party domain diff run manifest."""

    def render(
        self,
        *,
        request: DiffCliRequest,
        config: ResolvedConfig,
        outcome: RunOutcome,
        endpoints: object,
        before_source: SourceView,
        after_source: SourceView,
        file_changes: object,
        artifacts: tuple[ArtifactDescriptor, ...],
        changed_path_budget: object | None = None,
        semantic_sides: Mapping[str, object] | None = None,
    ) -> bytes:
        if len(outcome.domains) != 1 or outcome.manifest_relative_path != "run-manifest.json":
            raise ValueError("diff manifest requires one domain")
        domain = outcome.domains[0]
        if domain.domain != request.domain:
            raise ValueError("diff request and outcome domains do not match")
        if isinstance(domain.coverage, PythonCoverage):
            coverage: object | None = python_coverage_value(domain.coverage)
        elif isinstance(domain.coverage, Mapping):
            coverage = dict(domain.coverage)
        else:
            coverage = None
        budget = domain.budget.to_json_value() if isinstance(domain.budget, EntityBudget) else None
        endpoint_value = (
            endpoints.provenance_value() if hasattr(endpoints, "provenance_value") else {}
        )
        file_change_value = (
            file_changes.to_json_value() if hasattr(file_changes, "to_json_value") else None
        )
        if not isinstance(file_change_value, dict):
            raise ValueError("diff manifest requires a file-change set")
        ordered_artifacts = tuple(
            sorted(
                artifacts,
                key=lambda item: (
                    {"file-change-set": 0, "semantic-json": 1, "plantuml": 2}[item.format],
                    item.path.encode("utf-8"),
                ),
            )
        )
        if any(
            (item.domain, item.format) not in _DIFF_ARTIFACT_CONTRACT for item in ordered_artifacts
        ):
            raise ValueError("artifact descriptor violates the diff contract")
        expected_domain_paths = tuple(
            item.path for item in ordered_artifacts if item.format != "file-change-set"
        )
        if expected_domain_paths != domain.artifact_paths:
            raise ValueError("domain artifact paths and diff descriptors do not match")
        if not any(item.format == "file-change-set" for item in ordered_artifacts):
            raise ValueError("diff manifest requires a file-change descriptor")
        if any(
            item.path != _DIFF_ARTIFACT_CONTRACT[(request.domain, item.format)][0]
            or item.media_type != _DIFF_ARTIFACT_CONTRACT[(request.domain, item.format)][1]
            or item.domain != request.domain
            for item in ordered_artifacts
        ):
            raise ValueError("artifact descriptor violates the diff contract")
        domain_value: dict[str, object] = {
            "domain": request.domain,
            "status": domain.status.value,
            "payload_available": domain.payload_available,
            "entity_count": domain.entity_count,
            "coverage": coverage,
            "budget": budget,
            "artifact_paths": list(domain.artifact_paths),
            "diagnostics": [
                item.to_json_value() for item in canonical_diagnostics(domain.diagnostics)
            ],
        }
        if domain.status is DomainStatus.INCOMPLETE:
            if domain.incomplete_kind is None:
                raise ValueError("incomplete diff domain has no kind")
            domain_value["incomplete_kind"] = domain.incomplete_kind.value
        preimage = {
            "schema": "code-structure-viz.run-fingerprint/v1",
            "tool_version": __version__,
            "adapter_version": (
                "python-ast/1" if request.domain == "python" else "sqlalchemy-ast/1"
            ),
            "config_sha256": config.sha256,
            "command": "diff",
            "formats": list(request.formats),
            "stdout_selector": _selector_value(request.stdout_selector),
            "endpoints": endpoint_value,
            "sources": {
                "before": _source_value(before_source),
                "after": _source_value(after_source),
            },
            "semantic_sides": dict(semantic_sides or {}),
            "file_change_set": file_change_value,
            "changed_path_budget": (
                changed_path_budget.to_json_value()
                if hasattr(changed_path_budget, "to_json_value")
                else None
            ),
            "run_status": outcome.status.value,
        }
        run_fingerprint = hashlib.sha256(encode_canonical_json(preimage)).hexdigest()
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
                "plantuml": (
                    "code-structure-viz.plantuml/python/v1"
                    if request.domain == "python"
                    else "code-structure-viz.plantuml/sqlalchemy/v2"
                ),
                "file_change_set": "code-structure-viz.file-change-set/v1",
            },
            "adapters": [
                {
                    "domain": request.domain,
                    "name": "python-ast" if request.domain == "python" else "sqlalchemy-ast",
                    "version": "1",
                }
            ],
            "command": {
                "name": "diff",
                "domain": request.domain,
                "formats": list(request.formats),
                "stdout_selector": _selector_value(request.stdout_selector),
            },
            "request": {
                "from": request.from_ref,
                "to": request.to_ref,
                "pr_target": request.pr_target,
                "upstream_depth": config.traversal.upstream_depth,
                "downstream_depth": config.traversal.downstream_depth,
            },
            "comparison": endpoint_value,
            "sources": {
                "before": _source_value(before_source),
                "after": _source_value(after_source),
            },
            "semantic_sides": dict(semantic_sides or {}),
            "file_change_set": file_change_value,
            "changed_path_budget": (
                changed_path_budget.to_json_value()
                if hasattr(changed_path_budget, "to_json_value")
                else None
            ),
            "config": _config_value(config),
            "run": {
                "status": outcome.status.value,
                "exit_code": outcome.exit_code,
                "fingerprint": run_fingerprint,
            },
            "domains": [domain_value],
            "artifacts": [item.to_json_value() for item in ordered_artifacts],
            "diagnostics": [
                item.to_json_value() for item in canonical_diagnostics(outcome.diagnostics)
            ],
        }
        return encode_canonical_json(value)
