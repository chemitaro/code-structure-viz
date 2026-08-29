from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.helpers.acceptance import initialize_repository
from tests.helpers.sqlalchemy_snapshot import (
    initialize_sqlalchemy_fixture_repository,
    run_snapshot_cli,
)


def test_default_sqlalchemy_snapshot_publishes_both_payloads_and_manifest(
    tmp_path: Path,
) -> None:
    repository = initialize_sqlalchemy_fixture_repository(tmp_path, "canonical_model")
    output = tmp_path / "output"

    result = run_snapshot_cli(repository, output)

    assert result.returncode == 0, result.stderr
    assert result.stdout == (
        b'{"type":"run_summary","schema":"code-structure-viz.run-summary/v1",'
        b'"run_status":"complete","exit_code":0,"domains":'
        b'[{"domain":"sqlalchemy","status":"complete"}],'
        b'"manifest":"run-manifest.json"}\n'
    )
    assert result.stderr == b""
    assert sorted(path.name for path in output.iterdir()) == [
        "run-manifest.json",
        "sqlalchemy.snapshot.puml",
        "sqlalchemy.snapshot.semantic.json",
    ]
    semantic = json.loads((output / "sqlalchemy.snapshot.semantic.json").read_bytes())
    manifest = json.loads((output / "run-manifest.json").read_bytes())
    plantuml = (output / "sqlalchemy.snapshot.puml").read_bytes()
    assert semantic["domain"] == "sqlalchemy"
    assert semantic["status"] == "complete"
    assert semantic["coverage"]["selected_entities"] == 3
    assert manifest["adapters"] == [
        {"domain": "sqlalchemy", "name": "sqlalchemy-ast", "version": "1"}
    ]
    assert manifest["contracts"]["plantuml"] == ("code-structure-viz.plantuml/sqlalchemy/v1")
    assert manifest["domains"][0]["coverage"] == semantic["coverage"]
    assert [item["path"] for item in manifest["artifacts"]] == [
        "sqlalchemy.snapshot.semantic.json",
        "sqlalchemy.snapshot.puml",
    ]
    redaction = semantic["coverage"]["redaction"]
    assert f"  rule_version={redaction['rule_version']}\n".encode() in plantuml
    assert f"  redacted_values={redaction['redacted_values']}\n".encode() in plantuml
    public = (
        result.stdout
        + result.stderr
        + b"".join(path.read_bytes() for path in sorted(output.iterdir()))
    )
    assert b"DO_NOT_PUBLISH_THIS_SECRET" not in public
    assert not (repository / "TARGET_CODE_EXECUTED").exists()


def test_sqlalchemy_snapshot_one_format_uses_closed_path(tmp_path: Path) -> None:
    repository = initialize_sqlalchemy_fixture_repository(tmp_path, "canonical_model")
    output = tmp_path / "output"

    result = run_snapshot_cli(repository, output, "--format", "semantic-json")

    assert result.returncode == 0, result.stderr
    assert sorted(path.name for path in output.iterdir()) == [
        "run-manifest.json",
        "sqlalchemy.snapshot.semantic.json",
    ]


def test_python_only_repository_is_not_applicable_but_abstract_base_is_complete_empty(
    tmp_path: Path,
) -> None:
    plain = tmp_path / "plain"
    source = plain / "repo" / "src" / "plain.py"
    source.parent.mkdir(parents=True)
    source.write_text("answer = 42\n", encoding="utf-8")
    initialize_repository(plain / "repo")
    plain_output = plain / "output"

    absent = run_snapshot_cli(plain / "repo", plain_output)

    assert absent.returncode == 0
    assert sorted(path.name for path in plain_output.iterdir()) == ["run-manifest.json"]
    absent_manifest = json.loads((plain_output / "run-manifest.json").read_bytes())
    assert absent_manifest["domains"][0]["status"] == "not_applicable"

    abstract = tmp_path / "abstract"
    abstract_source = abstract / "repo" / "src" / "base.py"
    abstract_source.parent.mkdir(parents=True)
    abstract_source.write_text(
        "from sqlalchemy.orm import DeclarativeBase\n"
        "class Base(DeclarativeBase):\n"
        "    __abstract__ = True\n",
        encoding="utf-8",
    )
    initialize_repository(abstract / "repo")
    abstract_output = abstract / "output"

    empty = run_snapshot_cli(abstract / "repo", abstract_output)

    assert empty.returncode == 0, empty.stderr
    semantic = json.loads((abstract_output / "sqlalchemy.snapshot.semantic.json").read_bytes())
    assert semantic["status"] == "complete"
    assert semantic["entities"] == []


def test_sqlalchemy_safe_table_plus_parse_failure_is_partial_safe(tmp_path: Path) -> None:
    repository = initialize_sqlalchemy_fixture_repository(tmp_path, "canonical_model")
    broken = repository / "src" / "broken.py"
    broken.write_bytes(b"def broken(:\n")
    output = tmp_path / "output"

    result = run_snapshot_cli(repository, output)

    assert result.returncode == 3
    assert sorted(path.name for path in output.iterdir()) == [
        "run-manifest.json",
        "sqlalchemy.snapshot.puml",
        "sqlalchemy.snapshot.semantic.json",
    ]
    assert json.loads(result.stderr)["code"] == "CSV-SA-003"
    semantic = json.loads((output / "sqlalchemy.snapshot.semantic.json").read_bytes())
    assert (semantic["status"], semantic["incomplete_kind"]) == (
        "incomplete",
        "partial_safe",
    )


def test_sqlalchemy_missing_target_is_payload_unavailable_manifest_only(
    tmp_path: Path,
) -> None:
    repository = initialize_sqlalchemy_fixture_repository(tmp_path, "canonical_model")
    output = tmp_path / "output"

    result = run_snapshot_cli(
        repository,
        output,
        "--target",
        "class:models.Missing",
    )

    assert result.returncode == 3
    assert sorted(path.name for path in output.iterdir()) == ["run-manifest.json"]
    assert json.loads(result.stderr)["code"] == "CSV-SA-011"
    manifest = json.loads((output / "run-manifest.json").read_bytes())
    assert manifest["domains"][0]["incomplete_kind"] == "payload_unavailable"
    assert manifest["domains"][0]["artifact_paths"] == []


@pytest.mark.parametrize(
    ("case", "expected_entities"),
    [
        ("classic_declarative", {"legacy"}),
        ("association_table", {"groups", "membership", "users"}),
        ("cross_module", {"groups", "membership", "users"}),
        ("table_binding", {"users"}),
    ],
)
def test_fixture_families_are_reachable_through_the_cli(
    tmp_path: Path,
    case: str,
    expected_entities: set[str],
) -> None:
    repository = initialize_sqlalchemy_fixture_repository(tmp_path, case)
    output = tmp_path / "output"

    result = run_snapshot_cli(repository, output)

    assert result.returncode == 0, result.stderr
    semantic = json.loads((output / "sqlalchemy.snapshot.semantic.json").read_bytes())
    assert semantic["status"] == "complete"
    assert {item["name"] for item in semantic["entities"]} == expected_entities
