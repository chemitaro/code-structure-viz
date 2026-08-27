from __future__ import annotations

from pathlib import Path

from tests.helpers.diff import create_two_commit_repository, run_diff_cli


def test_missing_explicit_endpoint_fails_without_partial_artifacts(tmp_path: Path) -> None:
    repository, _before, after = create_two_commit_repository(
        tmp_path,
        before_text="class Order:\n    amount: int\n",
        after_text="class Order:\n    amount: str\n",
    )
    output = tmp_path / "output"

    result = run_diff_cli(repository, output, "--from", "refs/heads/missing", "--to", after)

    assert result.returncode == 1
    assert result.stdout.startswith(b'{"type":"run_summary"')
    assert b'"run_status":"fatal"' in result.stdout
    assert not output.exists()
    assert b"CSV-DIFF-001" in result.stderr
    assert b"missing" not in result.stderr


def test_invalid_endpoint_token_is_usage_error_before_git_access(tmp_path: Path) -> None:
    repository, _before, after = create_two_commit_repository(
        tmp_path,
        before_text="class Order:\n    amount: int\n",
        after_text="class Order:\n    amount: str\n",
    )
    output = tmp_path / "output"

    result = run_diff_cli(repository, output, "--from", "--bad", "--to", after)

    assert result.returncode == 2
    assert result.stdout == b""
    assert not output.exists()
