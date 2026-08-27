from __future__ import annotations

from code_structure_viz.semantic.diff import SemanticDiffer
from tests.helpers.python_snapshot import snapshot_from_text


def test_impact_uses_union_of_before_and_after_relations() -> None:
    before = snapshot_from_text(
        "class Base:\n"
        "    pass\n\n"
        "class Order:\n"
        "    value: Base\n\n"
        "class Consumer:\n"
        "    order: Order\n"
    )
    after = snapshot_from_text(
        "class Base:\n"
        "    pass\n\n"
        "class Order:\n"
        "    value: str\n\n"
        "class Consumer:\n"
        "    order: Order\n"
    )

    result = SemanticDiffer().compare(before, after, upstream_depth=1, downstream_depth=1)

    assert result.seeds == ("python:class:app:Order",)
    assert result.impact.upstream == ("python:class:app:Consumer",)
    assert result.impact.downstream == ("python:class:app:Base",)
