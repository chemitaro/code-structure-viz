from __future__ import annotations

from code_structure_viz.semantic.diff import SemanticDiffer
from tests.helpers.python_snapshot import snapshot_from_text


def test_comments_and_import_order_do_not_create_semantic_seeds() -> None:
    before = snapshot_from_text("import os\nimport typing\n\nclass Order:\n    amount: int\n")
    after = snapshot_from_text(
        "# documentation only\nimport typing\nimport os\n\nclass Order:\n    amount: int\n"
    )

    result = SemanticDiffer().compare(before, after)

    assert result.entities == ()
    assert result.members == ()
    assert result.relations == ()
    assert result.seeds == ()
    assert result.impact.upstream == ()
    assert result.impact.downstream == ()


def test_member_change_seeds_only_its_owner() -> None:
    before = snapshot_from_text(
        "class Order:\n    def total(self, amount):\n        return amount\n\n"
        "class Customer:\n    name: str\n"
    )
    after = snapshot_from_text(
        "class Order:\n    def total(self, amount: int) -> int:\n        return amount\n\n"
        "class Customer:\n    name: str\n"
    )

    result = SemanticDiffer().compare(before, after)

    assert result.entities == ()
    assert len(result.members) == 1
    assert result.members[0].status.value == "modified"
    assert result.seeds == ("python:class:app:Order",)


def test_class_only_change_is_reported_and_becomes_a_semantic_seed() -> None:
    before = snapshot_from_text("class Order:\n    amount: int\n")
    after = snapshot_from_text("@dataclass\nclass Order:\n    amount: int\n")

    result = SemanticDiffer().compare(before, after)

    assert len(result.entities) == 1
    assert result.entities[0].status.value == "modified"
    assert result.seeds == ("python:class:app:Order",)
    assert result.entity_count == 1


def test_relation_change_seeds_relation_source_and_exposes_removed_target_context() -> None:
    before = snapshot_from_text("class Base:\n    pass\n\nclass Order:\n    value: Base\n")
    after = snapshot_from_text("class Base:\n    pass\n\nclass Order:\n    value: str\n")

    result = SemanticDiffer().compare(before, after)

    assert len(result.relations) == 1
    assert result.relations[0].status.value == "removed"
    assert result.seeds == ("python:class:app:Order",)
    assert result.impact.downstream == ("python:class:app:Base",)
