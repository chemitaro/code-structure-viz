import ast
from pathlib import PurePosixPath

import pytest

from code_structure_viz.adapters.python.model import SourceRangeWithColumns
from code_structure_viz.adapters.python.type_expr import (
    BindingKind,
    ImportBinding,
    SafeTypeExpressionRenderer,
    TypeReferenceRole,
    TypeReferenceSite,
    TypeReferenceSiteKind,
)


def _render(
    expression: str, bindings: tuple[ImportBinding, ...] = ()
) -> tuple[str, tuple[tuple[str, str], ...], bool]:
    node = ast.parse(expression, mode="eval", feature_version=(3, 12)).body
    return _render_node(node, bindings)


def _render_node(
    node: ast.expr, bindings: tuple[ImportBinding, ...] = ()
) -> tuple[str, tuple[tuple[str, str], ...], bool]:
    site = TypeReferenceSite(
        TypeReferenceSiteKind.FIELD_ANNOTATION,
        "python:class:pkg.mod:Owner",
        "python:member:field",
        0,
        PurePosixPath("src/pkg/mod.py"),
    )
    rendered = SafeTypeExpressionRenderer(bindings).render(node, site)
    occurrences = tuple((".".join(item.spelling), item.role.value) for item in rendered.occurrences)
    return rendered.text, occurrences, rendered.supported


@pytest.mark.parametrize(
    ("expression", "text"),
    [
        ("()", "()"),
        ("(T,)", "(T,)"),
        ("(T1, T2)", "(T1, T2)"),
        ("Box[T]", "Box[T]"),
        ("Pair[T1, T2]", "Pair[T1, T2]"),
        ("(A | B) | C", "A | B | C"),
        ("Box[A | B]", "Box[A | B]"),
        ("None", "None"),
        ("...", "..."),
        ("42", "?"),
    ],
)
def test_closed_type_text_grammar(expression: str, text: str) -> None:
    rendered, _, supported = _render(expression)

    assert rendered == text
    assert supported is True


def test_symbol_occurrences_preserve_pre_alias_spelling_and_closed_roles() -> None:
    text, occurrences, supported = _render(
        "Alias[Left | pkg.Right]",
        (ImportBinding("Alias", "external.Box", BindingKind.SYMBOL),),
    )

    assert text == "external.Box[Left | pkg.Right]"
    assert occurrences == (
        ("Alias", TypeReferenceRole.HEAD.value),
        ("Left", TypeReferenceRole.ARGUMENT.value),
        ("pkg.Right", TypeReferenceRole.ARGUMENT.value),
    )
    assert supported is True


def test_forward_annotation_uses_same_closed_grammar() -> None:
    assert _render('"list[Foo | None]"') == (
        "list[Foo | None]",
        (
            ("list", "head"),
            ("Foo", "argument"),
        ),
        True,
    )
    assert _render('"not valid ["') == ("?", (), False)


def test_forward_annotation_expands_only_once_and_then_treats_strings_as_literals() -> None:
    assert _render("\"'private.Secret'\"") == ("?", (), True)


def test_literal_and_annotated_redact_values_without_making_references() -> None:
    bindings = (
        ImportBinding("L", "typing.Literal", BindingKind.SYMBOL),
        ImportBinding("A", "typing.Annotated", BindingKind.SYMBOL),
    )

    assert _render("L[1, 'secret']", bindings) == (
        "typing.Literal[?, ?]",
        (),
        True,
    )
    assert _render("A[Foo, 'secret', token]", bindings) == (
        "typing.Annotated[Foo, ?]",
        (("Foo", "head"),),
        True,
    )


@pytest.mark.parametrize("expression", ["factory()", "(factory())[Secret]", "[Secret]"])
def test_unsupported_site_becomes_one_unknown_without_inferred_references(
    expression: str,
) -> None:
    assert _render(expression) == ("?", (), False)


@pytest.mark.parametrize("shape", ["attribute", "union"])
def test_deep_valid_type_expression_preserves_the_supported_grammar(shape: str) -> None:
    depth = 1_500
    if shape == "attribute":
        node: ast.expr = ast.Name(id="Root", ctx=ast.Load())
        for _ in range(depth):
            node = ast.Attribute(value=node, attr="part", ctx=ast.Load())
    elif shape == "union":
        node = ast.Name(id="Left", ctx=ast.Load())
        for _ in range(depth):
            node = ast.BinOp(
                left=node,
                op=ast.BitOr(),
                right=ast.Name(id="Right", ctx=ast.Load()),
            )
    rendered, occurrences, supported = _render_node(node)

    assert supported is True
    assert rendered.startswith("Root" if shape == "attribute" else "Left")
    assert len(occurrences) == (1 if shape == "attribute" else depth + 1)


def test_occurrence_keeps_internal_columns_but_not_source_text() -> None:
    node = ast.parse("pkg.Type", mode="eval", feature_version=(3, 12)).body
    site = TypeReferenceSite(
        TypeReferenceSiteKind.RETURN_ANNOTATION,
        "python:class:pkg.mod:Owner",
        "python:member:method",
        0,
        PurePosixPath("src/pkg/mod.py"),
    )

    occurrence = SafeTypeExpressionRenderer(()).render(node, site).occurrences[0]

    assert occurrence.range == SourceRangeWithColumns(1, 0, 1, 8)
    assert occurrence.preorder_ordinal == 0
