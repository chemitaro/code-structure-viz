from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import cast

import pytest

from code_structure_viz.adapters.sqlalchemy.model import (
    SqlAlchemyCoverage,
    SqlAlchemySnapshot,
)
from code_structure_viz.adapters.sqlalchemy.snapshot_adapter import (
    SqlAlchemySnapshotDomainAdapter,
)
from code_structure_viz.cli.parser import OutputFormat, SnapshotCliRequest
from code_structure_viz.core.config import (
    ConfigSource,
    ConfigValueSources,
    LimitsConfig,
    PythonConfig,
    ResolvedConfig,
    TraversalConfig,
)
from code_structure_viz.core.outcomes import DomainStatus, IncompleteKind
from code_structure_viz.source.source_view import SourceFile, SourceFileKind, SourceView


def _source(files: dict[str, bytes]) -> SourceView:
    sources = tuple(
        SourceFile(
            PurePosixPath(path),
            SourceFileKind.REGULAR,
            None,
            len(content),
            hashlib.sha256(content).hexdigest(),
            content,
        )
        for path, content in sorted(files.items())
    )
    return SourceView("1" * 40, sources, (), "b" * 64)


def _request() -> SnapshotCliRequest:
    return SnapshotCliRequest(
        repo=Path("/repo"),
        output_dir=Path("/output"),
        domain="sqlalchemy",
        config_path=None,
        targets=(),
        upstream_depth_override=None,
        downstream_depth_override=None,
        formats=("semantic-json", "plantuml"),
        max_entities_override=None,
        stdout_selector=None,
    )


def _config() -> ResolvedConfig:
    return ResolvedConfig(
        schema="code-structure-viz.config/v1",
        python=PythonConfig(("src",), ("**/*.py",), ()),
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
        sha256="c" * 64,
    )


def test_adapter_connects_static_analysis_selection_and_both_renderers() -> None:
    source = _source(
        {
            "src/models.py": b"""
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
"""
        }
    )
    adapter = SqlAlchemySnapshotDomainAdapter()

    result = adapter.analyze(source, _request(), _config())

    assert adapter.contract.domain == "sqlalchemy"
    assert adapter.contract.adapter_name == "sqlalchemy-ast"
    assert adapter.contract.adapter_version == "1"
    assert result.status is DomainStatus.COMPLETE
    assert result.incomplete_kind is None
    assert isinstance(result.payload, SqlAlchemySnapshot)
    assert result.entity_count == 1
    assert isinstance(result.coverage, SqlAlchemyCoverage)
    semantic = adapter.render("semantic-json", result.payload, source, _request(), _config())
    plantuml = adapter.render("plantuml", result.payload, source, _request(), _config())
    assert json.loads(semantic)["domain"] == "sqlalchemy"
    assert adapter.coverage_value(result.coverage) == json.loads(semantic)["coverage"]
    assert plantuml.startswith(b"@startuml\ntitle SQLAlchemy ER snapshot\n")
    assert plantuml.endswith(b"@enduml\n")


def test_adapter_maps_not_applicable_partial_safe_and_unavailable_without_payload_leak() -> None:
    adapter = SqlAlchemySnapshotDomainAdapter()
    request = _request()
    config = _config()

    absent = adapter.analyze(_source({"src/plain.py": b"answer = 42\n"}), request, config)
    partial = adapter.analyze(
        _source(
            {
                "src/models.py": b"""
from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase): pass
class User(Base): __tablename__ = "users"
""",
                "src/broken.py": b"def broken(:\n",
            }
        ),
        request,
        config,
    )
    unavailable = adapter.analyze(_source({"src/broken.py": b"def broken(:\n"}), request, config)

    assert absent.status is DomainStatus.NOT_APPLICABLE
    assert absent.payload is None
    assert absent.entity_count == 0
    assert absent.diagnostics == ()
    assert partial.status is DomainStatus.INCOMPLETE
    assert partial.incomplete_kind is IncompleteKind.PARTIAL_SAFE
    assert isinstance(partial.payload, SqlAlchemySnapshot)
    assert partial.entity_count == 1
    assert unavailable.status is DomainStatus.INCOMPLETE
    assert unavailable.incomplete_kind is IncompleteKind.PAYLOAD_UNAVAILABLE
    assert unavailable.payload is None
    assert unavailable.entity_count is None


def test_adapter_rejects_cross_domain_payload_coverage_and_unknown_format() -> None:
    adapter = SqlAlchemySnapshotDomainAdapter()
    source = _source({"src/plain.py": b"answer = 42\n"})
    request = _request()
    config = _config()

    with pytest.raises(ValueError, match="another domain payload"):
        adapter.render("semantic-json", object(), source, request, config)
    with pytest.raises(ValueError, match="another domain coverage"):
        adapter.coverage_value(object())

    result = adapter.analyze(
        _source(
            {
                "src/models.py": b"""
from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase): pass
"""
            }
        ),
        request,
        config,
    )
    assert isinstance(result.payload, SqlAlchemySnapshot)
    with pytest.raises(ValueError, match="unsupported format"):
        adapter.render(cast(OutputFormat, "html"), result.payload, source, request, config)
