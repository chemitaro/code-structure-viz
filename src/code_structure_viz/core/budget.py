from __future__ import annotations

from dataclasses import dataclass

from code_structure_viz.core.config import ConfigSource
from code_structure_viz.core.diagnostics import Diagnostic, DiagnosticCode, diagnostic


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
            (diagnostic(DiagnosticCode.PY_ENTITY_BUDGET, domain="python"),),
        )
