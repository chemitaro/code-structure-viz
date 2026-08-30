from __future__ import annotations

from dataclasses import dataclass

from code_structure_viz.core.config import ConfigSource
from code_structure_viz.core.diagnostics import Diagnostic, DiagnosticCode, diagnostic
from code_structure_viz.core.domains import DomainName

_ENTITY_BUDGET_DIAGNOSTIC = {
    "python": DiagnosticCode.PY_ENTITY_BUDGET,
    "sqlalchemy": DiagnosticCode.SA_ENTITY_BUDGET,
}


@dataclass(frozen=True, slots=True)
class EntityBudget:
    name: str
    requested: int | None
    resolved: int
    actual: int | None
    source: ConfigSource

    def __post_init__(self) -> None:
        if self.name != "max_entities":
            raise ValueError("unknown entity budget")
        if self.requested is not None and self.requested <= 0:
            raise ValueError("requested entity budget must be positive")
        if self.resolved <= 0:
            raise ValueError("resolved entity budget must be positive")
        if self.actual is not None and self.actual < 0:
            raise ValueError("actual entity count cannot be negative")

    def to_json_value(self) -> dict[str, object]:
        return {
            "name": self.name,
            "requested": self.requested,
            "resolved": self.resolved,
            "actual": self.actual,
            "source": self.source.value,
        }


@dataclass(frozen=True, slots=True)
class BudgetDecision:
    admitted: bool
    budget: EntityBudget
    diagnostics: tuple[Diagnostic, ...]


class EntityBudgetGate:
    def admit(
        self,
        *,
        domain: DomainName,
        actual: int,
        requested: int | None,
        resolved: int,
        source: ConfigSource,
    ) -> BudgetDecision:
        budget = EntityBudget("max_entities", requested, resolved, actual, source)
        if actual <= resolved:
            return BudgetDecision(True, budget, ())
        return BudgetDecision(
            False,
            budget,
            (diagnostic(_ENTITY_BUDGET_DIAGNOSTIC[domain], domain=domain),),
        )


@dataclass(frozen=True, slots=True)
class ChangedPathBudget:
    """Run-level admission budget for metadata-only Git changed paths."""

    name: str
    requested: int | None
    resolved: int
    actual: int
    source: ConfigSource

    def __post_init__(self) -> None:
        if self.name != "max_changed_paths":
            raise ValueError("unknown changed-path budget")
        if self.requested is not None and self.requested <= 0:
            raise ValueError("requested changed-path budget must be positive")
        if self.resolved <= 0 or self.actual < 0:
            raise ValueError("changed-path budget values are invalid")

    def to_json_value(self) -> dict[str, object]:
        return {
            "name": self.name,
            "requested": self.requested,
            "resolved": self.resolved,
            "actual": self.actual,
            "source": self.source.value,
        }


@dataclass(frozen=True, slots=True)
class ChangedPathBudgetDecision:
    admitted: bool
    budget: ChangedPathBudget
    diagnostics: tuple[Diagnostic, ...]


class ChangedPathBudgetGate:
    def admit(
        self,
        *,
        actual: int,
        requested: int | None,
        resolved: int = 1000,
        source: ConfigSource = ConfigSource.BUILTIN,
    ) -> ChangedPathBudgetDecision:
        budget = ChangedPathBudget("max_changed_paths", requested, resolved, actual, source)
        if actual <= resolved:
            return ChangedPathBudgetDecision(True, budget, ())
        return ChangedPathBudgetDecision(
            False,
            budget,
            (diagnostic(DiagnosticCode.DIFF_CHANGED_PATH_BUDGET),),
        )
