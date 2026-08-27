from __future__ import annotations

import json
from pathlib import Path

from tests.helpers.diff import create_two_commit_repository, run_diff_cli


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
