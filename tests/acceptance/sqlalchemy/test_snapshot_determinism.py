from __future__ import annotations

from pathlib import Path

from tests.helpers.sqlalchemy_snapshot import (
    initialize_sqlalchemy_fixture_repository,
    run_snapshot_cli,
)


def _published(output: Path) -> dict[str, bytes]:
    return {
        path.relative_to(output).as_posix(): path.read_bytes()
        for path in sorted(output.rglob("*"))
        if path.is_file()
    }


def test_same_sqlalchemy_request_has_identical_files_streams_and_exit(
    tmp_path: Path,
) -> None:
    repository = initialize_sqlalchemy_fixture_repository(tmp_path, "canonical_model")
    first_output = tmp_path / "first"
    second_output = tmp_path / "second"

    first = run_snapshot_cli(repository, first_output)
    second = run_snapshot_cli(repository, second_output)

    assert second == first
    assert _published(second_output) == _published(first_output)
