from __future__ import annotations

import json
from pathlib import Path

from tests.helpers.acceptance import initialize_repository
from tests.helpers.sqlalchemy_snapshot import run_snapshot_cli


def _repository_with_tables(tmp_path: Path, count: int) -> Path:
    repository = tmp_path / "repo"
    source = repository / "src" / "models.py"
    source.parent.mkdir(parents=True)
    declarations = [
        "from sqlalchemy.orm import DeclarativeBase",
        "class Base(DeclarativeBase): pass",
    ]
    declarations.extend(
        f"class Model{index:04d}(Base): __tablename__ = 'table_{index:04d}'"
        for index in range(count)
    )
    source.write_text("\n".join(declarations) + "\n", encoding="utf-8")
    initialize_repository(repository)
    return repository


def test_sqlalchemy_default_budget_admits_500_tables(tmp_path: Path) -> None:
    repository = _repository_with_tables(tmp_path, 500)
    output = tmp_path / "output"

    result = run_snapshot_cli(repository, output, "--format", "semantic-json")

    assert result.returncode == 0, result.stderr
    manifest = json.loads((output / "run-manifest.json").read_bytes())
    assert manifest["domains"][0]["budget"]["actual"] == 500


def test_sqlalchemy_default_budget_rejects_501_without_payload(tmp_path: Path) -> None:
    repository = _repository_with_tables(tmp_path, 501)
    output = tmp_path / "output"

    result = run_snapshot_cli(repository, output)

    assert result.returncode == 3
    assert sorted(path.name for path in output.iterdir()) == ["run-manifest.json"]
    assert json.loads(result.stderr)["code"] == "CSV-SA-013"
    domain = json.loads((output / "run-manifest.json").read_bytes())["domains"][0]
    assert domain["entity_count"] == 501
    assert domain["coverage"]["selected_entities"] == 501
    assert domain["budget"]["actual"] == 501


def test_sqlalchemy_positive_override_admits_600_tables(tmp_path: Path) -> None:
    repository = _repository_with_tables(tmp_path, 600)
    output = tmp_path / "output"

    result = run_snapshot_cli(
        repository,
        output,
        "--max-entities",
        "600",
        "--format",
        "semantic-json",
    )

    assert result.returncode == 0, result.stderr
    budget = json.loads((output / "run-manifest.json").read_bytes())["domains"][0]["budget"]
    assert budget == {
        "name": "max_entities",
        "requested": 600,
        "resolved": 600,
        "actual": 600,
        "source": "cli",
    }
