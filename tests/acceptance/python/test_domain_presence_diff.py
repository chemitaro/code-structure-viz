from __future__ import annotations

import json
from pathlib import Path

from code_structure_viz.semantic.diff import (
    CanonicalEmptySide,
    DomainPresenceResolver,
    SemanticDiffer,
    SideKind,
)
from tests.helpers.diff import (
    create_two_commit_repository_from_files,
    create_unmerged_repository,
    run_diff_cli,
)
from tests.helpers.python_snapshot import snapshot_from_text


def test_absent_python_domain_on_both_sides_is_not_applicable() -> None:
    result = SemanticDiffer().compare(None, None)

    assert result.status == "not_applicable"
    assert result.entities == ()
    assert result.before.kind is SideKind.CANONICAL_EMPTY
    assert result.after.kind is SideKind.CANONICAL_EMPTY
    assert result.before.digest == CanonicalEmptySide.digest()
    assert result.before.digest == result.after.digest


def test_real_before_and_absent_after_are_all_removed() -> None:
    before = snapshot_from_text("class Order:\n    amount: int\n")

    result = SemanticDiffer().compare(before, None)

    assert result.status == "complete"
    assert result.after.kind is SideKind.CANONICAL_EMPTY
    assert result.entities
    assert {item.status.value for item in result.entities} == {"removed"}
    assert all(item.status.value == "removed" for item in result.members)


def test_absent_before_and_real_after_are_all_added() -> None:
    after = snapshot_from_text("class Order:\n    amount: int\n")

    result = SemanticDiffer().compare(None, after)

    assert result.status == "complete"
    assert result.before.kind is SideKind.CANONICAL_EMPTY
    assert result.entities
    assert {item.status.value for item in result.entities} == {"added"}
    assert all(item.status.value == "added" for item in result.members)


def test_analysis_failed_side_never_becomes_an_empty_side_or_guessable_delta() -> None:
    before = snapshot_from_text("class Order:\n    amount: int\n")
    before_side = DomainPresenceResolver.side(before, analysis_failed=True)

    result = SemanticDiffer().compare(
        before,
        None,
        before_side=before_side,
    )

    assert result.status == "incomplete"
    assert result.before.kind is SideKind.ANALYSIS_FAILED
    assert result.entities == ()
    assert result.members == ()
    assert result.relations == ()


def test_cli_presence_matrix_publishes_only_safe_artifacts_for_each_case(
    tmp_path: Path,
) -> None:
    cases = (
        (
            "both-absent",
            {"README.md": "before\n"},
            {"README.md": "after\n"},
            0,
            "not_applicable",
            {"file-changes.json", "run-manifest.json"},
        ),
        (
            "before-only",
            {"src/app.py": "class Order:\n    amount: int\n"},
            {"README.md": "after\n"},
            0,
            "complete",
            {
                "file-changes.json",
                "python.diff.semantic.json",
                "python.diff.puml",
                "run-manifest.json",
            },
        ),
        (
            "after-only",
            {"README.md": "before\n"},
            {"src/app.py": "class Order:\n    amount: int\n"},
            0,
            "complete",
            {
                "file-changes.json",
                "python.diff.semantic.json",
                "python.diff.puml",
                "run-manifest.json",
            },
        ),
        (
            "analysis-failed",
            {"src/app.py": "class Order:\n    amount: int\n"},
            {"src/app.py": "class Order(:\n    amount: int\n"},
            3,
            "incomplete",
            {"file-changes.json", "run-manifest.json"},
        ),
    )
    for name, before_files, after_files, exit_code, status, expected_files in cases:
        case_root = tmp_path / name
        repository, before, after = create_two_commit_repository_from_files(
            case_root,
            before_files=before_files,
            after_files=after_files,
        )
        output = case_root / "output"

        result = run_diff_cli(repository, output, "--from", before, "--to", after)

        assert result.returncode == exit_code, result.stderr.decode("utf-8", errors="replace")
        assert {path.name for path in output.iterdir()} == expected_files
        manifest = json.loads((output / "run-manifest.json").read_text(encoding="utf-8"))
        assert manifest["domains"][0]["status"] == status
        if status == "not_applicable":
            assert manifest["domains"][0]["artifact_paths"] == []
        if status == "incomplete":
            assert manifest["domains"][0]["incomplete_kind"] == "payload_unavailable"
            assert manifest["domains"][0]["payload_available"] is False
            for side_name in ("before", "after"):
                side = manifest["semantic_sides"][side_name]
                assert len(side["digest"]) == 64
                if side["kind"] == "analysis-failed":
                    assert side["digest"] == manifest["sources"][side_name]["fingerprint"]


def test_unmerged_working_tree_records_only_after_side_as_unanalyzed(tmp_path: Path) -> None:
    repository, base = create_unmerged_repository(tmp_path)
    output = tmp_path / "output"

    result = run_diff_cli(repository, output, "--from", base)

    assert result.returncode == 3, result.stderr.decode("utf-8", errors="replace")
    assert {path.name for path in output.iterdir()} == {
        "file-changes.json",
        "run-manifest.json",
    }
    manifest = json.loads((output / "run-manifest.json").read_text(encoding="utf-8"))
    assert {item["status"] for item in manifest["file_change_set"]["files"]} == {"U"}
    domain = manifest["domains"][0]
    assert domain["incomplete_kind"] == "payload_unavailable"
    assert domain["payload_available"] is False
    assert domain["coverage"]["before"] == {
        "candidate_files": 1,
        "parsed_files": 1,
        "failed_files": [],
        "selected_modules": ["app"],
        "selected_entities": 1,
        "frontier": [],
    }
    assert domain["coverage"]["after"] == {
        "candidate_files": 0,
        "parsed_files": 0,
        "failed_files": [],
        "selected_modules": [],
        "selected_entities": 0,
        "frontier": [],
    }
    assert [item["code"] for item in domain["diagnostics"]] == ["CSV-DIFF-003"]
    assert manifest["semantic_sides"]["before"]["kind"] == "real"
    assert manifest["semantic_sides"]["after"]["kind"] == "analysis-failed"
    assert (
        manifest["semantic_sides"]["after"]["digest"] == manifest["sources"]["after"]["fingerprint"]
    )


def test_unmerged_working_tree_preserves_failed_before_analysis_evidence(
    tmp_path: Path,
) -> None:
    repository, base = create_unmerged_repository(
        tmp_path,
        base_text="class Order(:\n    amount: int\n",
    )
    output = tmp_path / "output"

    result = run_diff_cli(repository, output, "--from", base)

    assert result.returncode == 3, result.stderr.decode("utf-8", errors="replace")
    manifest = json.loads((output / "run-manifest.json").read_text(encoding="utf-8"))
    domain = manifest["domains"][0]
    assert domain["incomplete_kind"] == "payload_unavailable"
    assert domain["payload_available"] is False
    assert domain["coverage"]["before"] == {
        "candidate_files": 1,
        "parsed_files": 0,
        "failed_files": [
            {
                "path": "src/app.py",
                "stage": "parse",
                "diagnostic_code": "CSV-PY-003",
            }
        ],
        "selected_modules": [],
        "selected_entities": 0,
        "frontier": [
            {
                "direction": "failure",
                "kind": "file",
                "reference": "src/app.py",
                "reason": "failed_source",
            }
        ],
    }
    assert [item["code"] for item in domain["diagnostics"]] == [
        "CSV-DIFF-003",
        "CSV-PY-003",
    ]
    assert manifest["semantic_sides"]["before"]["kind"] == "analysis-failed"
    assert (
        manifest["semantic_sides"]["before"]["digest"]
        == manifest["sources"]["before"]["fingerprint"]
    )
    assert manifest["semantic_sides"]["after"]["kind"] == "analysis-failed"
    assert (
        manifest["semantic_sides"]["after"]["digest"] == manifest["sources"]["after"]["fingerprint"]
    )
