from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from code_structure_viz.core.diagnostics import Diagnostic


class DomainStatus(StrEnum):
    COMPLETE = "complete"
    NOT_APPLICABLE = "not_applicable"
    INCOMPLETE = "incomplete"


class IncompleteKind(StrEnum):
    PARTIAL_SAFE = "partial_safe"
    PAYLOAD_UNAVAILABLE = "payload_unavailable"


class RunStatus(StrEnum):
    COMPLETE = "complete"
    NOT_APPLICABLE = "not_applicable"
    INCOMPLETE = "incomplete"
    FATAL = "fatal"
    USAGE = "usage"
    INTERRUPTED = "interrupted"


@dataclass(frozen=True, slots=True)
class DomainOutcome:
    status: DomainStatus
    incomplete_kind: IncompleteKind | None
    payload_available: bool
    payload: object | None
    artifact_paths: tuple[str, ...]
    diagnostics: tuple[Diagnostic, ...] = ()
    entity_count: int | None = None
    coverage: object | None = None
    budget: object | None = None

    def __post_init__(self) -> None:
        if self.status is DomainStatus.COMPLETE:
            if (
                self.incomplete_kind is not None
                or not self.payload_available
                or self.payload is None
            ):
                raise ValueError("complete domain outcome requires an available payload")
        elif self.status is DomainStatus.NOT_APPLICABLE:
            if (
                self.incomplete_kind is not None
                or self.payload_available
                or self.payload is not None
                or self.artifact_paths
            ):
                raise ValueError("not-applicable domain outcome cannot carry a payload")
        elif self.status is DomainStatus.INCOMPLETE:
            if self.incomplete_kind is IncompleteKind.PARTIAL_SAFE:
                if not self.payload_available or self.payload is None:
                    raise ValueError("partial-safe outcome requires an available safe payload")
            elif self.incomplete_kind is IncompleteKind.PAYLOAD_UNAVAILABLE:
                if self.payload_available or self.payload is not None or self.artifact_paths:
                    raise ValueError("payload-unavailable outcome cannot carry domain artifacts")
            else:
                raise ValueError("incomplete domain outcome requires an incomplete kind")

    @classmethod
    def complete(
        cls,
        payload: object,
        *,
        artifact_paths: tuple[str, ...] = (),
        diagnostics: tuple[Diagnostic, ...] = (),
        entity_count: int | None = None,
        coverage: object | None = None,
        budget: object | None = None,
    ) -> DomainOutcome:
        return cls(
            DomainStatus.COMPLETE,
            None,
            True,
            payload,
            artifact_paths,
            diagnostics,
            entity_count,
            coverage,
            budget,
        )

    @classmethod
    def not_applicable(
        cls,
        *,
        diagnostics: tuple[Diagnostic, ...] = (),
        coverage: object | None = None,
        budget: object | None = None,
    ) -> DomainOutcome:
        return cls(
            DomainStatus.NOT_APPLICABLE,
            None,
            False,
            None,
            (),
            diagnostics,
            0,
            coverage,
            budget,
        )

    @classmethod
    def partial_safe(
        cls,
        payload: object,
        *,
        artifact_paths: tuple[str, ...] = (),
        diagnostics: tuple[Diagnostic, ...] = (),
        entity_count: int | None = None,
        coverage: object | None = None,
        budget: object | None = None,
    ) -> DomainOutcome:
        return cls(
            DomainStatus.INCOMPLETE,
            IncompleteKind.PARTIAL_SAFE,
            True,
            payload,
            artifact_paths,
            diagnostics,
            entity_count,
            coverage,
            budget,
        )

    @classmethod
    def payload_unavailable(
        cls,
        *,
        diagnostics: tuple[Diagnostic, ...] = (),
        entity_count: int | None = None,
        coverage: object | None = None,
        budget: object | None = None,
    ) -> DomainOutcome:
        return cls(
            DomainStatus.INCOMPLETE,
            IncompleteKind.PAYLOAD_UNAVAILABLE,
            False,
            None,
            (),
            diagnostics,
            entity_count,
            coverage,
            budget,
        )


@dataclass(frozen=True, slots=True)
class RunOutcome:
    status: RunStatus
    exit_code: int
    domains: tuple[DomainOutcome, ...]
    manifest_relative_path: str | None
    diagnostics: tuple[Diagnostic, ...] = ()

    def __post_init__(self) -> None:
        expected_exit = {
            RunStatus.COMPLETE: 0,
            RunStatus.NOT_APPLICABLE: 0,
            RunStatus.INCOMPLETE: 3,
            RunStatus.FATAL: 1,
            RunStatus.USAGE: 2,
            RunStatus.INTERRUPTED: 130,
        }[self.status]
        if self.exit_code != expected_exit:
            raise ValueError("run status and exit code do not match")
        has_manifest = self.manifest_relative_path is not None
        if self.status in {RunStatus.COMPLETE, RunStatus.NOT_APPLICABLE, RunStatus.INCOMPLETE}:
            if not has_manifest or not self.domains:
                raise ValueError("valid core outcome requires a manifest and domain outcome")
        elif has_manifest or self.domains:
            raise ValueError("fatal, usage, and interrupt outcomes cannot carry a manifest")

    @classmethod
    def completed(
        cls,
        domains: tuple[DomainOutcome, ...],
        *,
        manifest_relative_path: str,
    ) -> RunOutcome:
        status = (
            RunStatus.NOT_APPLICABLE
            if all(domain.status is DomainStatus.NOT_APPLICABLE for domain in domains)
            else RunStatus.COMPLETE
        )
        if any(domain.status is DomainStatus.INCOMPLETE for domain in domains):
            raise ValueError("completed run cannot contain an incomplete domain")
        return cls(status, 0, domains, manifest_relative_path)

    @classmethod
    def incomplete(
        cls,
        domains: tuple[DomainOutcome, ...],
        *,
        manifest_relative_path: str,
    ) -> RunOutcome:
        if not any(domain.status is DomainStatus.INCOMPLETE for domain in domains):
            raise ValueError("incomplete run requires an incomplete domain")
        return cls(RunStatus.INCOMPLETE, 3, domains, manifest_relative_path)

    @classmethod
    def fatal(cls, diagnostics: tuple[Diagnostic, ...] = ()) -> RunOutcome:
        return cls(RunStatus.FATAL, 1, (), None, diagnostics)

    @classmethod
    def usage(cls, diagnostics: tuple[Diagnostic, ...] = ()) -> RunOutcome:
        return cls(RunStatus.USAGE, 2, (), None, diagnostics)

    @classmethod
    def interrupted(cls, diagnostics: tuple[Diagnostic, ...] = ()) -> RunOutcome:
        return cls(RunStatus.INTERRUPTED, 130, (), None, diagnostics)
