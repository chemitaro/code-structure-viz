from __future__ import annotations

import json
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


def test_identity_order_fixture_keeps_ids_and_order_stable_across_declaration_order(
    tmp_path: Path,
) -> None:
    first_repository = initialize_sqlalchemy_fixture_repository(
        tmp_path / "first", "identity_order"
    )
    second_repository = initialize_sqlalchemy_fixture_repository(
        tmp_path / "second", "identity_order"
    )
    (second_repository / "src" / "a.py").write_text(
        "from base import Base as DeclarativeBaseAlias\n\n"
        'class Zed(DeclarativeBaseAlias):\n    __tablename__ = "zed"\n',
        encoding="utf-8",
    )
    (second_repository / "src" / "z.py").write_text(
        "from base import Base as DeclarativeBaseAlias\n\n"
        'class Alpha(DeclarativeBaseAlias):\n    __tablename__ = "alpha"\n',
        encoding="utf-8",
    )

    first = run_snapshot_cli(first_repository, tmp_path / "first-output")
    second = run_snapshot_cli(second_repository, tmp_path / "second-output")

    assert first.returncode == second.returncode == 0
    first_entities = json.loads(
        (tmp_path / "first-output" / "sqlalchemy.snapshot.semantic.json").read_bytes()
    )["entities"]
    second_entities = json.loads(
        (tmp_path / "second-output" / "sqlalchemy.snapshot.semantic.json").read_bytes()
    )["entities"]
    assert [item["name"] for item in first_entities] == ["alpha", "zed"]
    assert [item["name"] for item in second_entities] == ["alpha", "zed"]
    assert [item["id"] for item in first_entities] == [item["id"] for item in second_entities]
