from __future__ import annotations

import json
from pathlib import Path

from tests.helpers.diff import (
    commit_current_changes,
    create_two_commit_repository,
    create_two_commit_repository_from_files,
    run_diff_cli,
)


def test_changed_path_budget_fails_before_domain_publication(tmp_path: Path) -> None:
    repository, _before, after = create_two_commit_repository(
        tmp_path,
        before_text="class Order:\n    amount: int\n",
        after_text="class Order:\n    amount: str\n",
    )
    (repository / "src" / "app.py").write_text(
        "class Order:\n    amount: float\n",
        encoding="utf-8",
    )
    (repository / "src" / "other.py").write_text(
        "class Customer:\n    name: str\n",
        encoding="utf-8",
    )
    target = commit_current_changes(repository, "two changed paths")

    result = run_diff_cli(
        repository,
        tmp_path / "output",
        "--from",
        after,
        "--to",
        target,
        "--max-changed-paths",
        "1",
    )

    assert result.returncode == 1
    assert result.stdout == (
        b'{"type":"run_summary","schema":"code-structure-viz.run-summary/v1",'
        b'"run_status":"fatal","exit_code":1,"domains":[],"manifest":null}\n'
    )
    assert not (tmp_path / "output").exists()
    assert b"source" not in result.stderr.lower()


def test_changed_path_budget_override_is_recorded_in_manifest(tmp_path: Path) -> None:
    repository, _before, after = create_two_commit_repository(
        tmp_path,
        before_text="class Order:\n    amount: int\n",
        after_text="class Order:\n    amount: str\n",
    )
    (repository / "src" / "app.py").write_text(
        "class Order:\n    amount: float\n",
        encoding="utf-8",
    )
    (repository / "src" / "other.py").write_text(
        "class Customer:\n    name: str\n",
        encoding="utf-8",
    )
    target = commit_current_changes(repository, "two changed paths")
    output = tmp_path / "output"

    result = run_diff_cli(
        repository,
        output,
        "--from",
        after,
        "--to",
        target,
        "--max-changed-paths",
        "3",
    )

    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    manifest = json.loads((output / "run-manifest.json").read_text(encoding="utf-8"))
    assert manifest["changed_path_budget"] == {
        "name": "max_changed_paths",
        "requested": 3,
        "resolved": 3,
        "actual": 2,
        "source": "cli",
    }


def test_default_changed_path_budget_rejects_1001_paths(tmp_path: Path) -> None:
    before_files = {f"docs/file-{index:04d}.txt": "before\n" for index in range(1001)}
    after_files = {path: "after\n" for path in before_files}
    repository, before, after = create_two_commit_repository_from_files(
        tmp_path,
        before_files=before_files,
        after_files=after_files,
    )

    result = run_diff_cli(repository, tmp_path / "output", "--from", before, "--to", after)

    assert result.returncode == 1
    assert b"CSV-DIFF-002" in result.stderr
    assert not (tmp_path / "output").exists()
