from code_structure_viz.core.budget import EntityBudgetGate
from code_structure_viz.core.config import ConfigSource


def test_entity_budget_admits_exact_limit_and_records_resolved_source() -> None:
    decision = EntityBudgetGate().admit(
        domain="python",
        actual=500,
        requested=None,
        resolved=500,
        source=ConfigSource.BUILTIN,
    )

    assert decision.admitted is True
    assert decision.diagnostics == ()
    assert decision.budget.to_json_value() == {
        "name": "max_entities",
        "requested": None,
        "resolved": 500,
        "actual": 500,
        "source": "builtin",
    }


def test_entity_budget_rejects_without_truncating_selected_count() -> None:
    decision = EntityBudgetGate().admit(
        domain="python",
        actual=501,
        requested=None,
        resolved=500,
        source=ConfigSource.BUILTIN,
    )

    assert decision.admitted is False
    assert decision.budget.actual == 501
    assert [item.code.value for item in decision.diagnostics] == ["CSV-PY-010"]
    assert decision.diagnostics[0].domain == "python"


def test_entity_budget_cli_override_is_the_recorded_request_and_source() -> None:
    decision = EntityBudgetGate().admit(
        domain="python",
        actual=600,
        requested=600,
        resolved=600,
        source=ConfigSource.CLI,
    )

    assert decision.admitted is True
    assert decision.budget.to_json_value() == {
        "name": "max_entities",
        "requested": 600,
        "resolved": 600,
        "actual": 600,
        "source": "cli",
    }


def test_entity_budget_uses_closed_sqlalchemy_diagnostic_mapping() -> None:
    decision = EntityBudgetGate().admit(
        domain="sqlalchemy",
        actual=501,
        requested=None,
        resolved=500,
        source=ConfigSource.BUILTIN,
    )

    assert decision.admitted is False
    assert [item.code.value for item in decision.diagnostics] == ["CSV-SA-013"]
    assert decision.diagnostics[0].domain == "sqlalchemy"
