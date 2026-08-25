import json
from pathlib import Path

from code_structure_viz.adapters.python.model import PythonCoverage
from code_structure_viz.artifacts.manifest import ArtifactDescriptor, RunManifestBuilder
from code_structure_viz.cli.parser import SnapshotCliRequest
from code_structure_viz.core.budget import EntityBudget
from code_structure_viz.core.config import (
    ConfigSource,
    ConfigValueSources,
    LimitsConfig,
    PythonConfig,
    ResolvedConfig,
    TraversalConfig,
)
from code_structure_viz.core.outcomes import DomainOutcome, RunOutcome
from code_structure_viz.source.source_view import SourceView


def _config() -> ResolvedConfig:
    return ResolvedConfig(
        schema="code-structure-viz.config/v1",
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
        sha256="d" * 64,
    )


def test_manifest_has_closed_order_descriptor_hash_and_no_self_descriptor() -> None:
    request = SnapshotCliRequest(
        repo=Path("/not-serialized/repo"),
        output_dir=Path("/not-serialized/output"),
        domain="python",
        config_path=None,
        targets=(),
        upstream_depth_override=None,
        downstream_depth_override=None,
        formats=("semantic-json",),
        max_entities_override=None,
        stdout_selector=None,
    )
    source = SourceView(None, (), (), "b" * 64)
    coverage = PythonCoverage(1, 1, (), ("domain.order",), 1, ())
    budget = EntityBudget("max_entities", None, 500, 1, ConfigSource.BUILTIN)
    domain = DomainOutcome.complete(
        object(),
        artifact_paths=("python.snapshot.semantic.json",),
        entity_count=1,
        coverage=coverage,
        budget=budget,
    )
    outcome = RunOutcome.completed((domain,), manifest_relative_path="run-manifest.json")
    descriptor = ArtifactDescriptor.create("semantic-json", b"abc")

    rendered = RunManifestBuilder().render(
        request=request,
        source_view=source,
        config=_config(),
        outcome=outcome,
        artifacts=(descriptor,),
    )
    value = json.loads(rendered)

    assert list(value) == [
        "type",
        "schema",
        "tool",
        "contracts",
        "adapters",
        "command",
        "request",
        "source",
        "config",
        "run",
        "domains",
        "artifacts",
        "diagnostics",
    ]
    assert value["artifacts"] == [
        {
            "path": "python.snapshot.semantic.json",
            "domain": "python",
            "format": "semantic-json",
            "media_type": "application/json",
            "size_bytes": 3,
            "sha256": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        }
    ]
    assert all(item["path"] != "run-manifest.json" for item in value["artifacts"])
    assert value["domains"][0]["coverage"]["selected_modules"] == ["domain.order"]
    assert value["run"]["fingerprint"] == (
        "6e7ccc3daee4e1d3d25a97090ff14407498f7369a8ef9fcfe3ca1973880f3d77"
    )
    assert b"/not-serialized/" not in rendered
    assert rendered.endswith(b"\n") and not rendered.endswith(b"\n\n")
