from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.helpers.diff import create_two_commit_repository, run_diff_cli


def test_explicit_commit_endpoints_publish_python_semantic_diff(tmp_path: Path) -> None:
    repository, before, after = create_two_commit_repository(
        tmp_path,
        before_text="class Order:\n    def total(self, amount):\n        return amount\n",
        after_text=(
            "class Order:\n    def total(self, amount: int) -> int:\n        return amount\n"
        ),
    )
    output = tmp_path / "output"

    result = run_diff_cli(repository, output, "--from", before, "--to", after)

    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    assert {path.name for path in output.iterdir() if path.is_file()} == {
        "file-changes.json",
        "python.diff.puml",
        "python.diff.semantic.json",
        "run-manifest.json",
    }
    semantic = json.loads((output / "python.diff.semantic.json").read_text(encoding="utf-8"))
    assert semantic["status"] == "complete"
    assert any(item["status"] == "modified" for item in semantic["semantic_change_set"]["members"])
    assert semantic["file_change_set"]["files"][0]["hunks"]
    plantuml = (output / "python.diff.puml").read_text(encoding="utf-8")
    assert 'class "~ Order"' in plantuml
    assert "~ method total" in plantuml


def test_from_only_freezes_working_tree_and_records_endpoint_provenance(
    tmp_path: Path,
) -> None:
    repository, before, _after = create_two_commit_repository(
        tmp_path,
        before_text="class Order:\n    def total(self, amount):\n        return amount\n",
        after_text=(
            "# stable source\nclass Order:\n    def total(self, amount):\n        return amount\n"
        ),
    )
    (repository / "src" / "app.py").write_text(
        "class Order:\n    def total(self, amount: int) -> int:\n        return amount\n",
        encoding="utf-8",
    )

    result = run_diff_cli(repository, tmp_path / "output", "--from", before)

    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    manifest = json.loads((tmp_path / "output" / "run-manifest.json").read_text(encoding="utf-8"))
    assert manifest["comparison"]["after_kind"] == "frozen-working-tree"
    assert manifest["comparison"]["resolution_method"] == "explicit-from-to-working-tree"


def test_to_working_tree_without_from_uses_start_head_implicit_base(
    tmp_path: Path,
) -> None:
    repository, _before, after = create_two_commit_repository(
        tmp_path,
        before_text="class Order:\n    def total(self, amount):\n        return amount\n",
        after_text=(
            "# stable source\nclass Order:\n    def total(self, amount):\n        return amount\n"
        ),
    )
    (repository / "src" / "app.py").write_text(
        "class Order:\n    def total(self, amount: int) -> int:\n        return amount\n",
        encoding="utf-8",
    )

    result = run_diff_cli(repository, tmp_path / "output", "--to", "working-tree")

    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    manifest = json.loads((tmp_path / "output" / "run-manifest.json").read_text(encoding="utf-8"))
    comparison = manifest["comparison"]
    assert comparison["start_head_anchor"] == after
    assert comparison["selected_base_candidate"] == "refs/heads/main"
    assert comparison["resolution_method"] == "implicit-base-from-start-head-anchor"


def test_untracked_paths_are_counted_before_python_analysis(tmp_path: Path) -> None:
    repository, before, _after = create_two_commit_repository(
        tmp_path,
        before_text="class Order:\n    amount: int\n",
        after_text="class Order:\n    amount: int\n# after\n",
    )
    (repository / "untracked-one.txt").write_text("one\n", encoding="utf-8")
    (repository / "untracked-two.txt").write_text("two\n", encoding="utf-8")
    output = tmp_path / "output"

    result = run_diff_cli(
        repository,
        output,
        "--from",
        before,
        "--max-changed-paths",
        "1",
    )

    assert result.returncode == 1
    assert b"CSV-DIFF-002" in result.stderr
    assert not output.exists()


def test_non_ascii_git_path_keeps_content_hunk_metadata(tmp_path: Path) -> None:
    repository, before, after = create_two_commit_repository(
        tmp_path,
        relative_path="src/café.py",
        before_text="class Order:\n    amount: int\n",
        after_text="class Order:\n    amount: str\n",
    )
    output = tmp_path / "output"

    result = run_diff_cli(repository, output, "--from", before, "--to", after)

    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    value = json.loads((output / "file-changes.json").read_text(encoding="utf-8"))
    assert value["files"][0]["old_path"] == "src/café.py"
    assert value["files"][0]["new_path"] == "src/café.py"
    assert value["files"][0]["hunks"]


def test_from_working_tree_is_usage_error_before_publication(tmp_path: Path) -> None:
    repository, _before, after = create_two_commit_repository(
        tmp_path,
        before_text="class Order:\n    def total(self, amount):\n        return amount\n",
        after_text=(
            "class Order:\n    def total(self, amount: int) -> int:\n        return amount\n"
        ),
    )
    output = tmp_path / "output"

    result = run_diff_cli(
        repository,
        output,
        "--from",
        "working-tree",
        "--to",
        after,
    )

    assert result.returncode == 2
    assert result.stdout == b""
    assert not output.exists()


@pytest.mark.parametrize(
    ("arguments", "method", "expected_before", "expected_after"),
    (
        ((), "implicit-base-from-start-head-anchor", "after", None),
        (("--from", "before"), "explicit-from-to-working-tree", "before", None),
        (("--to", "before"), "implicit-base-from-endpoint-anchor", "before", "before"),
        (("--to", "head"), "implicit-base-from-endpoint-anchor", "after", "after"),
        (("--to", "working-tree"), "implicit-base-from-start-head-anchor", "after", None),
        (
            ("--from", "before", "--to", "after"),
            "explicit-from-to",
            "before",
            "after",
        ),
    ),
)
def test_cli_endpoint_matrix_records_resolution_provenance(
    tmp_path: Path,
    arguments: tuple[str, ...],
    method: str,
    expected_before: str,
    expected_after: str | None,
) -> None:
    repository, before, after = create_two_commit_repository(
        tmp_path,
        before_text="class Order:\n    amount: int\n",
        after_text="class Order:\n    amount: int\n\nclass Customer:\n    name: str\n",
    )
    (repository / "src" / "app.py").write_text(
        "class Order:\n    amount: bytes\n\nclass Customer:\n    name: str\n",
        encoding="utf-8",
    )
    output = tmp_path / "output"
    substitutions = {"before": before, "after": after}
    resolved_arguments = tuple(substitutions.get(item, item) for item in arguments)

    result = run_diff_cli(repository, output, *resolved_arguments)

    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    manifest = json.loads((output / "run-manifest.json").read_text(encoding="utf-8"))
    comparison = manifest["comparison"]
    assert comparison["resolution_method"] == method
    assert comparison["resolved"]["before"] == substitutions[expected_before]
    assert comparison["resolved"]["after"] == (
        substitutions[expected_after] if expected_after is not None else None
    )
