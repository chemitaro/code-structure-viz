from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from code_structure_viz.core.diagnostics import Diagnostic
from code_structure_viz.core.domains import SNAPSHOT_DOMAINS, DomainName
from code_structure_viz.core.outcomes import DomainStatus, IncompleteKind

if TYPE_CHECKING:
    from code_structure_viz.cli.parser import OutputFormat, SnapshotCliRequest
    from code_structure_viz.core.config import ResolvedConfig
    from code_structure_viz.source.source_view import SourceView


@dataclass(frozen=True, slots=True)
class SnapshotAdapterContract:
    domain: DomainName
    adapter_name: str
    adapter_version: str
    plantuml_contract: str
    semantic_path: str
    plantuml_path: str

    def __post_init__(self) -> None:
        expected = {
            "python": (
                "python-ast",
                "1",
                "code-structure-viz.plantuml/python/v1",
                "python.snapshot.semantic.json",
                "python.snapshot.puml",
            ),
            "sqlalchemy": (
                "sqlalchemy-ast",
                "1",
                "code-structure-viz.plantuml/sqlalchemy/v1",
                "sqlalchemy.snapshot.semantic.json",
                "sqlalchemy.snapshot.puml",
            ),
        }
        if (
            self.domain not in SNAPSHOT_DOMAINS
            or (
                self.adapter_name,
                self.adapter_version,
                self.plantuml_contract,
                self.semantic_path,
                self.plantuml_path,
            )
            != expected[self.domain]
        ):
            raise ValueError("snapshot adapter contract is not a closed first-party contract")


@dataclass(frozen=True, slots=True)
class SnapshotAnalysis:
    status: DomainStatus
    incomplete_kind: IncompleteKind | None
    payload: object | None
    coverage: object
    diagnostics: tuple[Diagnostic, ...]
    entity_count: int | None

    def __post_init__(self) -> None:
        if self.coverage is None:
            raise ValueError("snapshot analysis requires coverage")
        if self.entity_count is not None and (
            type(self.entity_count) is not int or self.entity_count < 0
        ):
            raise ValueError("snapshot analysis entity count is invalid")
        if self.status is DomainStatus.COMPLETE:
            if (
                self.incomplete_kind is not None
                or self.payload is None
                or self.entity_count is None
            ):
                raise ValueError("complete snapshot analysis requires a payload and count")
        elif self.status is DomainStatus.NOT_APPLICABLE:
            if (
                self.incomplete_kind is not None
                or self.payload is not None
                or self.entity_count != 0
                or self.diagnostics
            ):
                raise ValueError("not-applicable snapshot analysis has an invalid state")
        elif self.status is DomainStatus.INCOMPLETE:
            if self.incomplete_kind is IncompleteKind.PARTIAL_SAFE:
                if self.payload is None or self.entity_count is None:
                    raise ValueError("partial-safe snapshot analysis requires a payload and count")
            elif self.incomplete_kind is IncompleteKind.PAYLOAD_UNAVAILABLE:
                if self.payload is not None:
                    raise ValueError("payload-unavailable snapshot analysis cannot carry a payload")
            else:
                raise ValueError("incomplete snapshot analysis requires an incomplete kind")


class SnapshotDomainAdapter(Protocol):
    contract: SnapshotAdapterContract

    def analyze(
        self,
        source_view: SourceView,
        request: SnapshotCliRequest,
        config: ResolvedConfig,
    ) -> SnapshotAnalysis: ...

    def render(
        self,
        format_value: OutputFormat,
        payload: object,
        source_view: SourceView,
        request: SnapshotCliRequest,
        config: ResolvedConfig,
    ) -> bytes: ...

    def coverage_value(self, coverage: object) -> Mapping[str, object]: ...


def snapshot_adapter_for(domain: DomainName) -> SnapshotDomainAdapter:
    if domain == "python":
        from code_structure_viz.adapters.python.snapshot_adapter import (
            PythonSnapshotDomainAdapter,
        )

        return PythonSnapshotDomainAdapter()
    if domain == "sqlalchemy":
        from code_structure_viz.adapters.sqlalchemy.snapshot_adapter import (
            SqlAlchemySnapshotDomainAdapter,
        )

        return SqlAlchemySnapshotDomainAdapter()
    raise ValueError("unknown snapshot domain")
