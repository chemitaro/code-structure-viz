from __future__ import annotations

from typing import cast

from code_structure_viz.semantic.diff import SemanticDiffer
from tests.helpers.python_snapshot import snapshot_from_files


def test_unique_structural_class_move_is_reported_as_moved() -> None:
    before = snapshot_from_files(
        {
            "src/old.py": (
                "class Order:\n"
                "    def total(self, amount: int) -> int:\n"
                "        return amount\n"
            )
        }
    )
    after = snapshot_from_files(
        {
            "src/new.py": (
                "class Order:\n"
                "    def total(self, amount: int) -> int:\n"
                "        return amount\n"
            )
        }
    )

    result = SemanticDiffer().compare(before, after)

    assert len(result.matching) == 1
    assert result.entities[0].status.value == "moved"
    assert result.entities[0].matching_evidence == result.matching[0]


def test_ambiguous_structural_move_stays_removed_and_added() -> None:
    before = snapshot_from_files(
        {
            "src/old.py": "class Order:\n    amount: int\n",
        }
    )
    after = snapshot_from_files(
        {
            "src/new_a.py": "class Order:\n    amount: int\n",
            "src/new_b.py": "class Order:\n    amount: int\n",
        }
    )

    result = SemanticDiffer().compare(before, after)

    assert result.matching == ()
    statuses = [item.status.value for item in result.entities]
    assert statuses.count("removed") == 1
    assert statuses.count("added") == 2


def test_existing_identity_is_not_misclassified_when_duplicate_is_added() -> None:
    before = snapshot_from_files(
        {
            "src/order.py": "class Order:\n    amount: int\n",
        }
    )
    after = snapshot_from_files(
        {
            "src/order.py": "class Order:\n    amount: int\n",
            "src/copy.py": "class Copy:\n    amount: int\n",
        }
    )

    result = SemanticDiffer().compare(before, after)

    assert result.matching == ()
    assert [item.status.value for item in result.entities] == ["added"]
    assert result.entities[0].after is not None
    after_value = cast(dict[str, object], result.entities[0].after)
    assert after_value["qualified_name"] == "Copy"
