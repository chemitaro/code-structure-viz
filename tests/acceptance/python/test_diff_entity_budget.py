from __future__ import annotations

import json
from pathlib import Path

from tests.helpers.diff import create_two_commit_repository, run_diff_cli


def _many_changed_classes(annotation: str) -> str:
    return "\n".join(f"class Entity{index}:\n    value: {annotation}\n" for index in range(501))


def test_entity_budget_hides_affected_payload_but_publishes_safe_manifest(
    tmp_path: Path,
) -> None:
    repository, before, after = create_two_commit_repository(
        tmp_path,
        before_text=(
            "class Order:\n"
            "    def total(self, amount):\n"
            "        return amount\n\n"
            "class Customer:\n"
            "    name: str\n"
        ),
        after_text=(
            "class Order:\n"
            "    def total(self, amount: int) -> int:\n"
            "        return amount\n\n"
            "class Customer:\n"
            "    name: bytes\n"
        ),
    )
    output = tmp_path / "output"

    result = run_diff_cli(
        repository,
        output,
        "--from",
        before,
        "--to",
        after,
        "--max-entities",
        "1",
    )

    assert result.returncode == 3
    assert {path.name for path in output.iterdir()} == {
        "file-changes.json",
        "run-manifest.json",
    }
    manifest = json.loads((output / "run-manifest.json").read_text(encoding="utf-8"))
    domain = manifest["domains"][0]
    assert domain["status"] == "incomplete"
    assert domain["incomplete_kind"] == "payload_unavailable"
    assert domain["payload_available"] is False
    assert domain["artifact_paths"] == []
    assert domain["budget"]["requested"] == 1
    assert domain["budget"]["resolved"] == 1
    assert domain["budget"]["actual"] > 1


def test_default_entity_budget_rejects_501_changed_entities(tmp_path: Path) -> None:
    repository, before, after = create_two_commit_repository(
        tmp_path,
        before_text=_many_changed_classes("int"),
        after_text=_many_changed_classes("str"),
    )
    output = tmp_path / "output"

    result = run_diff_cli(repository, output, "--from", before, "--to", after)

    assert result.returncode == 3, result.stderr.decode("utf-8", errors="replace")
    assert {path.name for path in output.iterdir()} == {
        "file-changes.json",
        "run-manifest.json",
    }
    manifest = json.loads((output / "run-manifest.json").read_text(encoding="utf-8"))
    assert manifest["domains"][0]["budget"] == {
        "name": "max_entities",
        "requested": None,
        "resolved": 500,
        "actual": 501,
        "source": "builtin",
    }


def test_valid_entity_budget_override_publishes_all_501_changed_entities(
    tmp_path: Path,
) -> None:
    repository, before, after = create_two_commit_repository(
        tmp_path,
        before_text=_many_changed_classes("int"),
        after_text=_many_changed_classes("str"),
    )
    output = tmp_path / "output"

    result = run_diff_cli(
        repository,
        output,
        "--from",
        before,
        "--to",
        after,
        "--max-entities",
        "600",
    )

    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    assert {path.name for path in output.iterdir()} == {
        "file-changes.json",
        "python.diff.puml",
        "python.diff.semantic.json",
        "run-manifest.json",
    }
    manifest = json.loads((output / "run-manifest.json").read_text(encoding="utf-8"))
    assert manifest["domains"][0]["budget"] == {
        "name": "max_entities",
        "requested": 600,
        "resolved": 600,
        "actual": 501,
        "source": "cli",
    }
