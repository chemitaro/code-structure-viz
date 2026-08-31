from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from tests.helpers.diff import create_two_commit_repository_from_files, create_unmerged_repository


def _run_diff(
    repository: Path,
    output: Path,
    before: str,
    after: str,
    *arguments: str,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        (
            sys.executable,
            "-m",
            "code_structure_viz",
            "diff",
            "--repo",
            str(repository),
            "--output-dir",
            str(output),
            "--domain",
            "sqlalchemy",
            "--from",
            before,
            "--to",
            after,
            *arguments,
        ),
        cwd=repository,
        env={**os.environ, "NO_COLOR": "1"},
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
    )


def test_complete_sqlalchemy_diff_publishes_closed_payloads_and_manifest(
    tmp_path: Path,
) -> None:
    repository, before, after = create_two_commit_repository_from_files(
        tmp_path,
        before_files={
            "src/models.py": (
                "from sqlalchemy import ForeignKey\n"
                "from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column\n"
                "class Base(DeclarativeBase): pass\n"
                "class Account(Base): __tablename__ = 'accounts'\n"
                "class User(Base):\n"
                "    __tablename__ = 'users'\n"
                "    account_id: Mapped[int] = mapped_column(ForeignKey('accounts.id'))\n"
                "    name: Mapped[str] = mapped_column(nullable=True)\n"
            )
        },
        after_files={
            "src/models.py": (
                "from sqlalchemy import ForeignKey\n"
                "from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column\n"
                "class Base(DeclarativeBase): pass\n"
                "class Account(Base): __tablename__ = 'accounts'\n"
                "class User(Base):\n"
                "    __tablename__ = 'users'\n"
                "    account_id: Mapped[int] = mapped_column(ForeignKey('accounts.id'))\n"
                "    name: Mapped[str] = mapped_column(nullable=False)\n"
            )
        },
    )
    output = tmp_path / "output"

    result = _run_diff(repository, output, before, after)

    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    assert sorted(path.name for path in output.iterdir()) == [
        "file-changes.json",
        "run-manifest.json",
        "sqlalchemy.diff.puml",
        "sqlalchemy.diff.semantic.json",
    ]
    semantic = json.loads((output / "sqlalchemy.diff.semantic.json").read_bytes())
    plantuml = (output / "sqlalchemy.diff.puml").read_bytes()
    manifest = json.loads((output / "run-manifest.json").read_bytes())
    assert semantic["domain"] == "sqlalchemy"
    assert semantic["before"]["head_commit"] == before
    assert semantic["after"]["head_commit"] == after
    assert semantic["before"]["file_count"] == 1
    assert semantic["semantic_change_set"]["members"][0]["status"] == "modified"
    assert b"skinparam classAttributeIconSize 0\n" in plantuml
    assert b"\nhide methods\n" not in plantuml
    assert b"~ before <color:DarkGoldenRod>name : string (str) <<NULL>></color>" in plantuml
    assert b"~ after <color:DarkGoldenRod>* name : string (str) <<NN>></color>" in plantuml
    assert manifest["adapters"] == [
        {"domain": "sqlalchemy", "name": "sqlalchemy-ast", "version": "1"}
    ]
    assert manifest["domains"][0]["artifact_paths"] == [
        "sqlalchemy.diff.semantic.json",
        "sqlalchemy.diff.puml",
    ]

    repeated_output = tmp_path / "repeated-output"
    repeated = _run_diff(repository, repeated_output, before, after)

    assert repeated.returncode == 0, repeated.stderr
    for artifact in ("sqlalchemy.diff.semantic.json", "sqlalchemy.diff.puml"):
        assert (repeated_output / artifact).read_bytes() == (output / artifact).read_bytes()


def test_absent_and_one_side_absent_follow_the_parent_truth_table(tmp_path: Path) -> None:
    plain, plain_before, plain_after = create_two_commit_repository_from_files(
        tmp_path / "plain",
        before_files={"src/app.py": "answer = 1\n"},
        after_files={"src/app.py": "answer = 2\n"},
    )
    absent_output = tmp_path / "absent-output"

    absent = _run_diff(plain, absent_output, plain_before, plain_after)

    assert absent.returncode == 0
    assert sorted(path.name for path in absent_output.iterdir()) == [
        "file-changes.json",
        "run-manifest.json",
    ]
    absent_manifest = json.loads((absent_output / "run-manifest.json").read_bytes())
    assert absent_manifest["domains"][0]["status"] == "not_applicable"

    repository, before, after = create_two_commit_repository_from_files(
        tmp_path / "one-side",
        before_files={"src/app.py": "answer = 1\n"},
        after_files={
            "src/app.py": "answer = 1\n",
            "src/models.py": (
                "from sqlalchemy.orm import DeclarativeBase\n"
                "class Base(DeclarativeBase): pass\n"
                "class User(Base): __tablename__ = 'users'\n"
            ),
        },
    )
    output = tmp_path / "one-side-output"

    added = _run_diff(repository, output, before, after)

    assert added.returncode == 0, added.stderr
    semantic = json.loads((output / "sqlalchemy.diff.semantic.json").read_bytes())
    assert {item["status"] for item in semantic["semantic_change_set"]["entities"]} == {"added"}
    assert semantic["before"]["kind"] == "canonical-empty-side"

    removed_output = tmp_path / "removed-output"
    removed = _run_diff(repository, removed_output, after, before)

    assert removed.returncode == 0, removed.stderr
    removed_semantic = json.loads((removed_output / "sqlalchemy.diff.semantic.json").read_bytes())
    assert {item["status"] for item in removed_semantic["semantic_change_set"]["entities"]} == {
        "removed"
    }
    assert removed_semantic["after"]["kind"] == "canonical-empty-side"


def test_incomplete_side_and_entity_budget_publish_no_domain_payload(tmp_path: Path) -> None:
    source = (
        "from sqlalchemy.orm import DeclarativeBase\n"
        "class Base(DeclarativeBase): pass\n"
        "class User(Base): __tablename__ = 'users'\n"
        "class Team(Base): __tablename__ = 'teams'\n"
    )
    repository, before, after = create_two_commit_repository_from_files(
        tmp_path / "incomplete",
        before_files={"src/models.py": source},
        after_files={"src/models.py": "from sqlalchemy.orm import DeclarativeBase\ndef broken(:\n"},
    )
    output = tmp_path / "incomplete-output"

    incomplete = _run_diff(repository, output, before, after)

    assert incomplete.returncode == 3
    assert sorted(path.name for path in output.iterdir()) == [
        "file-changes.json",
        "run-manifest.json",
    ]
    manifest = json.loads((output / "run-manifest.json").read_bytes())
    assert manifest["domains"][0]["incomplete_kind"] == "payload_unavailable"

    budget_repo, budget_before, budget_after = create_two_commit_repository_from_files(
        tmp_path / "budget",
        before_files={"src/app.py": "answer = 1\n"},
        after_files={"src/models.py": source},
    )
    budget_output = tmp_path / "budget-output"

    overrun = _run_diff(
        budget_repo,
        budget_output,
        budget_before,
        budget_after,
        "--max-entities",
        "1",
    )

    assert overrun.returncode == 3
    assert sorted(path.name for path in budget_output.iterdir()) == [
        "file-changes.json",
        "run-manifest.json",
    ]


def test_changed_path_budget_is_fatal_and_stdout_is_exact_payload(tmp_path: Path) -> None:
    repository, before, after = create_two_commit_repository_from_files(
        tmp_path / "stdout",
        before_files={
            "src/models.py": (
                "from sqlalchemy.orm import DeclarativeBase\n"
                "class Base(DeclarativeBase): pass\n"
                "class User(Base): __tablename__ = 'users'\n"
            ),
            "src/other.py": "value = 1\n",
        },
        after_files={
            "src/models.py": (
                "from sqlalchemy.orm import DeclarativeBase\n"
                "class Base(DeclarativeBase): pass\n"
                "class User(Base): __tablename__ = 'renamed_users'\n"
            ),
            "src/other.py": "value = 2\n",
        },
    )
    fatal_output = tmp_path / "fatal-output"

    fatal = _run_diff(
        repository,
        fatal_output,
        before,
        after,
        "--max-changed-paths",
        "1",
    )

    assert fatal.returncode == 1
    assert not fatal_output.exists()

    output = tmp_path / "stdout-output"
    selected = _run_diff(
        repository,
        output,
        before,
        after,
        "--format",
        "semantic-json",
        "--stdout",
        "sqlalchemy:semantic-json",
    )

    assert selected.returncode == 0, selected.stderr
    assert selected.stdout == (output / "sqlalchemy.diff.semantic.json").read_bytes()


def test_working_tree_unmerged_side_fails_closed_without_sqlalchemy_payload(
    tmp_path: Path,
) -> None:
    repository, before = create_unmerged_repository(
        tmp_path,
        base_text=(
            "from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column\n"
            "class Base(DeclarativeBase): pass\n"
            "class Order(Base):\n"
            "    __tablename__ = 'orders'\n"
            "    amount: Mapped[int] = mapped_column()\n"
        ),
    )
    output = tmp_path / "output"

    result = _run_diff(repository, output, before, "working-tree")

    assert result.returncode == 3, result.stderr
    assert sorted(path.name for path in output.iterdir()) == [
        "file-changes.json",
        "run-manifest.json",
    ]
    manifest = json.loads((output / "run-manifest.json").read_bytes())
    assert manifest["semantic_sides"]["before"]["kind"] == "real"
    assert manifest["semantic_sides"]["after"]["kind"] == "analysis-failed"
    assert manifest["domains"][0]["incomplete_kind"] == "payload_unavailable"
