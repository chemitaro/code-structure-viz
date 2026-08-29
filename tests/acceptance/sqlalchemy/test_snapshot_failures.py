from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.helpers.acceptance import ROOT, initialize_repository
from tests.helpers.sqlalchemy_snapshot import run_snapshot_cli


def _repository_from_fixture(tmp_path: Path, case: str) -> Path:
    repository = tmp_path / "repo"
    source = repository / "src" / "models.py"
    source.parent.mkdir(parents=True)
    source.write_bytes(
        (ROOT / "tests" / "fixtures" / "sqlalchemy_snapshot" / case / "models.py").read_bytes()
    )
    initialize_repository(repository)
    return repository


@pytest.mark.parametrize("case", ["lossy_identity_conflict", "lossy_same_line_siblings"])
def test_lossy_row_conflicts_publish_only_safe_subset_with_four_occurrences(
    tmp_path: Path,
    case: str,
) -> None:
    repository = _repository_from_fixture(tmp_path, case)
    output = tmp_path / "output"

    result = run_snapshot_cli(repository, output)

    assert result.returncode == 3
    diagnostics = [json.loads(line) for line in result.stderr.splitlines()]
    occurrences = [item for item in diagnostics if item["code"] == "CSV-SA-009"]
    assert len(occurrences) == 4
    assert len({item["symbol"] for item in occurrences}) == 4
    semantic = json.loads((output / "sqlalchemy.snapshot.semantic.json").read_bytes())
    assert semantic["incomplete_kind"] == "partial_safe"
    assert [item["kind"] for item in semantic["members"]] == ["column"]
    assert all("utf8_byte_column" not in json.dumps(item) for item in occurrences)


def test_table_identity_collision_has_no_winner_and_no_payload(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    for module, symbol in (("one", "One"), ("two", "Two")):
        source = repository / "src" / f"{module}.py"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(
            "from sqlalchemy.orm import DeclarativeBase\n"
            "class Base(DeclarativeBase): pass\n"
            f"class {symbol}(Base): __tablename__ = 'shared'\n",
            encoding="utf-8",
        )
    initialize_repository(repository)
    output = tmp_path / "output"

    result = run_snapshot_cli(repository, output)

    assert result.returncode == 3
    assert sorted(path.name for path in output.iterdir()) == ["run-manifest.json"]
    assert json.loads(result.stderr)["code"] == "CSV-SA-008"


def test_duplicate_class_binding_is_payload_unavailable_without_fallback(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repo"
    source = repository / "src" / "models.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        "from sqlalchemy.orm import DeclarativeBase\n"
        "class Base(DeclarativeBase): pass\n"
        "class User(Base): __tablename__ = 'users_one'\n"
        "class User(Base): __tablename__ = 'users_two'\n",
        encoding="utf-8",
    )
    initialize_repository(repository)
    output = tmp_path / "output"

    result = run_snapshot_cli(
        repository,
        output,
        "--target",
        "class:models.User",
    )

    assert result.returncode == 3
    assert sorted(path.name for path in output.iterdir()) == ["run-manifest.json"]
    diagnostics = [json.loads(line) for line in result.stderr.splitlines()]
    assert [item["code"] for item in diagnostics] == [
        "CSV-SA-011",
        "CSV-SA-006",
        "CSV-SA-006",
    ]
