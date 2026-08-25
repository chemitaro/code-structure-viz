import pytest

from code_structure_viz.core.diagnostics import (
    DiagnosticCode,
    DiagnosticContext,
    canonical_diagnostics,
    diagnostic,
    encode_diagnostic_jsonl,
)


def test_python_parse_diagnostic_has_exact_json_field_order_and_context() -> None:
    value = diagnostic(
        DiagnosticCode.PY_PARSE,
        domain="python",
        path="src/broken.py",
        line=7,
    )

    assert encode_diagnostic_jsonl((value,)) == (
        b'{"type":"diagnostic","schema":"code-structure-viz.diagnostic/v1",'
        b'"code":"CSV-PY-003","severity":"error","domain":"python",'
        b'"path":"src/broken.py","symbol":null,"line":7,"recoverable":true,'
        b'"message":"Python source could not be parsed with the v1 Python 3.12 grammar."}\n'
    )


def test_diagnostic_exposes_its_context_as_an_immutable_typed_value() -> None:
    value = diagnostic(
        DiagnosticCode.PY_REFERENCE_UNKNOWN,
        domain="python",
        path="src/app/model.py",
        symbol="Missing",
        line=4,
    )

    assert value.context == DiagnosticContext(
        domain="python",
        path="src/app/model.py",
        symbol="Missing",
        line=4,
    )


@pytest.mark.parametrize(
    ("code", "kwargs"),
    [
        (DiagnosticCode.PY_PARSE, {}),
        (DiagnosticCode.SOURCE_NON_UTF8, {"path": "invented.py"}),
        (DiagnosticCode.CONFIG_UNKNOWN_KEY, {"domain": "python"}),
    ],
)
def test_diagnostic_constructor_rejects_context_not_allowed_by_code(
    code: DiagnosticCode, kwargs: dict[str, object]
) -> None:
    with pytest.raises(ValueError):
        diagnostic(code, **kwargs)  # type: ignore[arg-type]


def test_diagnostics_are_deduplicated_and_sorted_by_closed_key() -> None:
    later = diagnostic(
        DiagnosticCode.PY_REFERENCE_UNKNOWN,
        domain="python",
        path="z.py",
        symbol="Missing",
        line=2,
    )
    first = diagnostic(
        DiagnosticCode.PY_REFERENCE_UNKNOWN,
        domain="python",
        path="a.py",
        symbol="Missing",
        line=1,
    )

    assert canonical_diagnostics((later, first, first)) == (first, later)
