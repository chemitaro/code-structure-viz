from __future__ import annotations

import json
from pathlib import Path

from tests.helpers.acceptance import ROOT, initialize_repository
from tests.helpers.sqlalchemy_snapshot import (
    initialize_sqlalchemy_fixture_repository,
    run_snapshot_cli,
)


def _relationship_repository(tmp_path: Path) -> Path:
    repository = tmp_path / "repo"
    source = repository / "src" / "models.py"
    source.parent.mkdir(parents=True)
    source.write_bytes(
        (
            ROOT
            / "tests"
            / "fixtures"
            / "sqlalchemy_snapshot"
            / "relationship_semantics"
            / "models.py"
        ).read_bytes()
    )
    initialize_repository(repository)
    return repository


def test_sqlalchemy_class_target_depth_controls_internal_graph(tmp_path: Path) -> None:
    repository = _relationship_repository(tmp_path)
    seed_output = tmp_path / "seed-output"
    expanded_output = tmp_path / "expanded-output"

    seed = run_snapshot_cli(
        repository,
        seed_output,
        "--target",
        "class:models.User",
        "--upstream-depth",
        "0",
        "--downstream-depth",
        "0",
    )
    expanded = run_snapshot_cli(
        repository,
        expanded_output,
        "--target",
        "class:models.User",
        "--upstream-depth",
        "1",
        "--downstream-depth",
        "1",
    )

    assert seed.returncode == 0, seed.stderr
    assert expanded.returncode == 0, expanded.stderr
    seed_value = json.loads((seed_output / "sqlalchemy.snapshot.semantic.json").read_bytes())
    expanded_value = json.loads(
        (expanded_output / "sqlalchemy.snapshot.semantic.json").read_bytes()
    )
    assert [item["name"] for item in seed_value["entities"]] == ["users"]
    assert seed_value["relations"] == []
    assert seed_value["coverage"]["frontier"] != []
    assert {item["name"] for item in expanded_value["entities"]} == {
        "admins",
        "groups",
        "membership",
        "users",
    }
    assert expanded_value["coverage"]["selected_entities"] == 4


def test_sqlalchemy_multiple_targets_are_a_normalized_union(tmp_path: Path) -> None:
    repository = _relationship_repository(tmp_path)
    output = tmp_path / "output"

    result = run_snapshot_cli(
        repository,
        output,
        "--target",
        "class:models.User",
        "--target",
        "module:models",
        "--target",
        "class:models.User",
        "--upstream-depth",
        "0",
        "--downstream-depth",
        "0",
    )

    assert result.returncode == 0, result.stderr
    semantic = json.loads((output / "sqlalchemy.snapshot.semantic.json").read_bytes())
    assert {item["name"] for item in semantic["entities"]} == {
        "admins",
        "groups",
        "membership",
        "users",
    }
    assert semantic["request"]["targets"] == [
        {"kind": "module", "value": "models"},
        {"kind": "class", "value": "models.User"},
    ]


def test_targeted_fixture_resolves_path_module_and_class_targets(tmp_path: Path) -> None:
    repository = initialize_sqlalchemy_fixture_repository(tmp_path, "targeted")

    path_result = run_snapshot_cli(
        repository,
        tmp_path / "path-output",
        "--target",
        "path:src/models.py",
        "--upstream-depth",
        "0",
        "--downstream-depth",
        "0",
    )
    module_result = run_snapshot_cli(
        repository,
        tmp_path / "module-output",
        "--target",
        "module:models",
        "--upstream-depth",
        "0",
        "--downstream-depth",
        "0",
    )
    class_result = run_snapshot_cli(
        repository,
        tmp_path / "class-output",
        "--target",
        "class:models.User",
        "--upstream-depth",
        "0",
        "--downstream-depth",
        "0",
    )

    assert path_result.returncode == module_result.returncode == class_result.returncode == 0
    path_entities = json.loads(
        (tmp_path / "path-output" / "sqlalchemy.snapshot.semantic.json").read_bytes()
    )["entities"]
    module_entities = json.loads(
        (tmp_path / "module-output" / "sqlalchemy.snapshot.semantic.json").read_bytes()
    )["entities"]
    class_entities = json.loads(
        (tmp_path / "class-output" / "sqlalchemy.snapshot.semantic.json").read_bytes()
    )["entities"]
    assert {item["name"] for item in path_entities} == {"accounts", "users"}
    assert {item["name"] for item in module_entities} == {"accounts", "users"}
    assert [item["name"] for item in class_entities] == ["users"]
