from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

from tests.helpers.diff import (
    create_gitlink_repository,
    create_raw_path_collision_repository,
    create_raw_path_transition_repository,
    create_two_commit_repository,
    create_two_commit_repository_from_files,
    run_diff_cli,
)


def _git_proxy(tmp_path: Path, behavior: str) -> Path:
    real_git = shutil.which("git")
    assert real_git is not None
    shim = tmp_path / "bin" / "git"
    shim.parent.mkdir(exist_ok=True)
    shim.write_text(
        "#!/usr/bin/env python3\n"
        "import os, pathlib, subprocess, sys\n"
        f"{behavior}\n"
        f"os.execv({real_git!r}, [{real_git!r}, *sys.argv[1:]])\n",
        encoding="utf-8",
    )
    shim.chmod(shim.stat().st_mode | stat.S_IXUSR)
    return shim.parent


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


def test_configured_upstream_namespace_expands_to_deterministic_candidate(
    tmp_path: Path,
) -> None:
    repository, before, _after = create_two_commit_repository(
        tmp_path,
        before_text="class Order:\n    amount: int\n",
        after_text="class Order:\n    amount: str\n",
    )
    subprocess.run(
        (
            "git",
            "-C",
            str(repository),
            "update-ref",
            "refs/remotes/upstream/main",
            before,
        ),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
    )
    config = tmp_path / "config.toml"
    config.write_text(
        """schema = "code-structure-viz.config/v1"
[python]
source_roots = ["src"]
include = ["**/*.py"]
exclude = []
[traversal]
upstream_depth = 1
downstream_depth = 1
[limits]
max_entities = 500
[comparison]
upstream_ref = "refs/remotes/upstream"
""",
        encoding="utf-8",
    )
    output = tmp_path / "output"

    result = run_diff_cli(repository, output, "--config", str(config))

    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    manifest = json.loads((output / "run-manifest.json").read_text(encoding="utf-8"))
    assert manifest["comparison"]["selected_base_candidate"] == ("refs/remotes/upstream/main")
    assert manifest["comparison"]["merge_base"] == before
    assert manifest["config"]["resolved"]["comparison"] == {
        "target_ref": None,
        "upstream_ref": "refs/remotes/upstream",
    }


def test_implicit_candidate_observations_record_rejected_then_selected_refs(
    tmp_path: Path,
) -> None:
    repository, before, _after = create_two_commit_repository(
        tmp_path,
        before_text="class Order:\n    amount: int\n",
        after_text="class Order:\n    amount: str\n",
    )
    empty_tree = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
    unrelated = (
        subprocess.run(
            ("git", "-C", str(repository), "commit-tree", empty_tree, "-m", "unrelated"),
            input=b"",
            capture_output=True,
            check=True,
            env={
                **os.environ,
                **{
                    "GIT_AUTHOR_NAME": "Code Structure Viz Fixture",
                    "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
                    "GIT_COMMITTER_NAME": "Code Structure Viz Fixture",
                    "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
                },
            },
        )
        .stdout.decode("ascii")
        .strip()
    )
    subprocess.run(
        ("git", "-C", str(repository), "update-ref", "refs/remotes/upstream/a", unrelated),
        check=True,
    )
    subprocess.run(
        ("git", "-C", str(repository), "update-ref", "refs/remotes/upstream/b", before),
        check=True,
    )
    config = tmp_path / "config.toml"
    config.write_text(
        """schema = \"code-structure-viz.config/v1\"
[python]
source_roots = [\"src\"]
include = [\"**/*.py\"]
exclude = []
[traversal]
upstream_depth = 1
downstream_depth = 1
[limits]
max_entities = 500
[comparison]
upstream_ref = \"refs/remotes/upstream\"
""",
        encoding="utf-8",
    )

    output = tmp_path / "output"
    result = run_diff_cli(repository, output, "--config", str(config))

    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    comparison = json.loads((output / "run-manifest.json").read_text(encoding="utf-8"))[
        "comparison"
    ]
    assert comparison["candidate_observations"] == [
        {
            "ordinal": 0,
            "origin": "config-upstream",
            "reference": "refs/remotes/upstream/a",
            "resolved_object": unrelated,
            "merge_base": None,
            "disposition": "no-merge-base",
        },
        {
            "ordinal": 1,
            "origin": "config-upstream",
            "reference": "refs/remotes/upstream/b",
            "resolved_object": before,
            "merge_base": before,
            "disposition": "selected",
        },
        {
            "ordinal": 2,
            "origin": "builtin",
            "reference": "refs/remotes/origin/HEAD",
            "resolved_object": None,
            "merge_base": None,
            "disposition": "not-evaluated",
        },
        {
            "ordinal": 3,
            "origin": "builtin",
            "reference": "refs/heads/main",
            "resolved_object": None,
            "merge_base": None,
            "disposition": "not-evaluated",
        },
        {
            "ordinal": 4,
            "origin": "builtin",
            "reference": "refs/heads/develop",
            "resolved_object": None,
            "merge_base": None,
            "disposition": "not-evaluated",
        },
        {
            "ordinal": 5,
            "origin": "builtin",
            "reference": "refs/heads/master",
            "resolved_object": None,
            "merge_base": None,
            "disposition": "not-evaluated",
        },
    ]
    second_output = tmp_path / "second-output"
    second_result = run_diff_cli(repository, second_output, "--config", str(config))
    assert second_result.returncode == 0, second_result.stderr.decode("utf-8", errors="replace")
    assert (output / "run-manifest.json").read_bytes() == (
        second_output / "run-manifest.json"
    ).read_bytes()


def test_explicit_endpoints_publish_empty_candidate_observations(tmp_path: Path) -> None:
    repository, before, after = create_two_commit_repository(
        tmp_path,
        before_text="class Order:\n    amount: int\n",
        after_text="class Order:\n    amount: str\n",
    )

    result = run_diff_cli(
        repository,
        tmp_path / "output",
        "--from",
        before,
        "--to",
        after,
    )

    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    comparison = json.loads(
        (tmp_path / "output" / "run-manifest.json").read_text(encoding="utf-8")
    )["comparison"]
    assert comparison["candidate_observations"] == []
    assert comparison["selected_base_candidate"] is None
    assert comparison["merge_base"] is None


def test_missing_skip_worktree_python_is_unavailable_not_actual_deletion(tmp_path: Path) -> None:
    repository, _before, after = create_two_commit_repository(
        tmp_path,
        before_text="class Order:\n    amount: int\n",
        after_text="class Order:\n    amount: str\n",
    )
    subprocess.run(
        ("git", "-C", str(repository), "update-index", "--skip-worktree", "--", "src/app.py"),
        check=True,
    )
    (repository / "src" / "app.py").unlink()

    output = tmp_path / "output"
    result = run_diff_cli(repository, output, "--from", after)

    assert result.returncode == 3, result.stderr.decode("utf-8", errors="replace")
    assert {path.name for path in output.iterdir()} == {"file-changes.json", "run-manifest.json"}
    file_changes = json.loads((output / "file-changes.json").read_text(encoding="utf-8"))
    assert file_changes["files"] == []
    manifest = json.loads((output / "run-manifest.json").read_text(encoding="utf-8"))
    assert manifest["domains"][0]["incomplete_kind"] == "payload_unavailable"
    assert manifest["domains"][0]["payload_available"] is False


def test_missing_non_skip_worktree_python_remains_actual_deletion(tmp_path: Path) -> None:
    repository, _before, after = create_two_commit_repository(
        tmp_path,
        before_text="class Order:\n    amount: int\n",
        after_text="class Order:\n    amount: str\n",
    )
    (repository / "src" / "app.py").unlink()

    output = tmp_path / "output"
    result = run_diff_cli(repository, output, "--from", after)

    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    file_changes = json.loads((output / "file-changes.json").read_text(encoding="utf-8"))
    assert [
        (item["status"], item["old_path"], item["new_path"]) for item in file_changes["files"]
    ] == [("D", "src/app.py", None)]


def test_dirty_gitlink_is_one_superproject_change(tmp_path: Path) -> None:
    repository, parent_head, _nested, _nested_head = create_gitlink_repository(tmp_path)

    output = tmp_path / "output"
    result = run_diff_cli(repository, output, "--from", parent_head)

    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    file_changes = json.loads((output / "file-changes.json").read_text(encoding="utf-8"))
    assert [
        (item["status"], item["old_path"], item["new_path"]) for item in file_changes["files"]
    ] == [("M", "src/component", "src/component")]
    manifest = json.loads((output / "run-manifest.json").read_text(encoding="utf-8"))
    assert manifest["changed_path_budget"]["actual"] == 1
    assert b"nested after" not in result.stdout + result.stderr


@pytest.mark.parametrize("dirty_kind", ("tracked", "untracked"))
def test_dirty_gitlink_contents_are_one_superproject_change(
    tmp_path: Path,
    dirty_kind: str,
) -> None:
    repository, parent_head, nested, _nested_head = create_gitlink_repository(tmp_path)
    subprocess.run(
        ("git", "-C", str(nested), "reset", "--hard", "HEAD^"),
        check=True,
        capture_output=True,
    )
    if dirty_kind == "tracked":
        (nested / "README").write_text("nested dirty\n", encoding="utf-8")
    else:
        (nested / "untracked.txt").write_text("nested untracked\n", encoding="utf-8")

    output = tmp_path / "output"
    result = run_diff_cli(repository, output, "--from", parent_head)

    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    file_changes = json.loads((output / "file-changes.json").read_text(encoding="utf-8"))
    assert [
        (item["status"], item["old_path"], item["new_path"]) for item in file_changes["files"]
    ] == [("M", "src/component", "src/component")]


def test_gitlink_state_drift_before_publication_is_fatal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, parent_head, nested, nested_head = create_gitlink_repository(tmp_path)
    (nested / "README").write_text("nested final\n", encoding="utf-8")
    subprocess.run(
        ("git", "-C", str(nested), "add", "."),
        check=True,
    )
    subprocess.run(
        (
            "git",
            "-C",
            str(nested),
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "--quiet",
            "--message=final",
        ),
        check=True,
    )
    nested_final_head = subprocess.check_output(
        ("git", "-C", str(nested), "rev-parse", "HEAD"),
        text=True,
    ).strip()
    subprocess.run(("git", "-C", str(nested), "reset", "--hard", nested_head), check=True)
    counter = tmp_path / "gitlink-head-count"
    proxy = _git_proxy(
        tmp_path,
        "if sys.argv[1:3] == ['-C', "
        f"{str(nested)!r}] and sys.argv[-3:] == ['rev-parse', '--verify', 'HEAD^{{commit}}']:\n"
        f"    counter = pathlib.Path({str(counter)!r})\n"
        "    count = int(counter.read_text()) + 1 if counter.exists() else 1\n"
        "    counter.write_text(str(count))\n"
        "    if count == 2:\n"
        f"        subprocess.run(({'git'!r}, '-C', {str(nested)!r}, 'reset', '--hard', "
        f"{str(nested_final_head)!r}), stdin=subprocess.DEVNULL, capture_output=True, "
        "check=True)",
    )
    monkeypatch.setenv("PATH", f"{proxy}{os.pathsep}{os.environ['PATH']}")

    output = tmp_path / "output"
    result = run_diff_cli(repository, output, "--from", parent_head)

    assert result.returncode == 1
    assert b"CSV-SOURCE-001" in result.stderr
    assert not output.exists()
    assert list(tmp_path.glob(".code-structure-viz-staging-*")) == []


def test_gitlink_state_unreadable_during_final_observation_is_source_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, parent_head, nested, _nested_head = create_gitlink_repository(tmp_path)
    counter = tmp_path / "gitlink-head-count"
    removed = nested.with_name("component-removed")
    proxy = _git_proxy(
        tmp_path,
        "if sys.argv[1:3] == ['-C', "
        f"{str(nested)!r}] and sys.argv[-3:] == ['rev-parse', '--verify', 'HEAD^{{commit}}']:\n"
        f"    counter = pathlib.Path({str(counter)!r})\n"
        "    count = int(counter.read_text()) + 1 if counter.exists() else 1\n"
        "    counter.write_text(str(count))\n"
        "    if count == 2:\n"
        f"        pathlib.Path({str(nested)!r}).rename({str(removed)!r})",
    )
    monkeypatch.setenv("PATH", f"{proxy}{os.pathsep}{os.environ['PATH']}")

    output = tmp_path / "output"
    result = run_diff_cli(repository, output, "--from", parent_head)

    assert result.returncode == 1
    assert b"CSV-SOURCE-001" in result.stderr
    assert not output.exists()
    assert list(tmp_path.glob(".code-structure-viz-staging-*")) == []


@pytest.mark.parametrize("layout", ("missing", "uninitialized", "external-pointer"))
def test_invalid_gitlink_materialization_is_run_fatal_without_publication(
    tmp_path: Path,
    layout: str,
) -> None:
    repository, parent_head, nested, _nested_head = create_gitlink_repository(tmp_path)
    if layout == "missing":
        shutil.rmtree(nested)
    elif layout == "uninitialized":
        shutil.rmtree(nested / ".git")
    else:
        shutil.rmtree(nested / ".git")
        (nested / ".git").write_text(
            "gitdir: /tmp/code-structure-viz-external-gitdir\n", encoding="utf-8"
        )

    output = tmp_path / "output"
    result = run_diff_cli(repository, output, "--from", parent_head)

    assert result.returncode == 1
    assert b"CSV-DIFF-003" in result.stderr
    assert not output.exists()
    assert b"/tmp/code-structure-viz-external-gitdir" not in result.stderr


def test_nested_gitlink_observer_never_runs_textconv_or_clean_process_filter(
    tmp_path: Path,
) -> None:
    repository, parent_head, nested, _nested_head = create_gitlink_repository(tmp_path)
    sentinel = tmp_path / "nested-helper-ran"
    helper = tmp_path / "helper.py"
    helper.write_text(
        f"from pathlib import Path\nPath({str(sentinel)!r}).write_text('ran', encoding='utf-8')\n",
        encoding="utf-8",
    )
    helper.chmod(0o700)
    subprocess.run(
        (
            "git",
            "-C",
            str(nested),
            "config",
            "diff.sentinel.textconv",
            f"{os.environ.get('PYTHON', 'python3')} {helper}",
        ),
        check=True,
        capture_output=True,
    )
    subprocess.run(
        (
            "git",
            "-C",
            str(nested),
            "config",
            "filter.sentinel.clean",
            f"{os.environ.get('PYTHON', 'python3')} {helper}",
        ),
        check=True,
        capture_output=True,
    )
    subprocess.run(
        (
            "git",
            "-C",
            str(nested),
            "config",
            "filter.sentinel.process",
            f"{os.environ.get('PYTHON', 'python3')} {helper}",
        ),
        check=True,
        capture_output=True,
    )
    (nested / ".gitattributes").write_text(
        "README diff=sentinel filter=sentinel\n", encoding="utf-8"
    )

    output = tmp_path / "output"
    result = run_diff_cli(repository, output, "--from", parent_head)

    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    assert not sentinel.exists()


def test_materialized_gitlink_gitfile_pointer_within_superproject_git_is_supported(
    tmp_path: Path,
) -> None:
    repository, parent_head, nested, _nested_head = create_gitlink_repository(tmp_path)
    nested_git_dir = repository / ".git" / "modules" / "src" / "component"
    nested_git_dir.parent.mkdir(parents=True)
    shutil.move(str(nested / ".git"), str(nested_git_dir))
    (nested / ".git").write_text("gitdir: ../../.git/modules/src/component\n", encoding="utf-8")

    output = tmp_path / "output"
    result = run_diff_cli(repository, output, "--from", parent_head)

    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    file_changes = json.loads((output / "file-changes.json").read_text(encoding="utf-8"))
    assert [
        (item["status"], item["old_path"], item["new_path"]) for item in file_changes["files"]
    ] == [("M", "src/component", "src/component")]


def test_working_tree_raw_path_transition_is_run_fatal_without_publication(
    tmp_path: Path,
) -> None:
    repository, before = create_raw_path_transition_repository(tmp_path)
    output = tmp_path / "output"

    result = run_diff_cli(repository, output, "--from", before)

    assert result.returncode == 1
    assert b"CSV-DIFF-003" in result.stderr
    assert not output.exists()
    assert b"cafe" not in result.stderr


def test_non_python_nfc_nfd_collision_is_run_fatal_without_publication(tmp_path: Path) -> None:
    repository, _before, after = create_raw_path_collision_repository(tmp_path)

    output = tmp_path / "output"
    result = run_diff_cli(repository, output, "--from", after, "--to", after)

    assert result.returncode == 1
    assert b"CSV-DIFF-003" in result.stderr
    assert not output.exists()
    assert b"cafe" not in result.stderr


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


def test_tracked_to_untracked_uses_canonical_records_for_budget_and_manifest(
    tmp_path: Path,
) -> None:
    repository, _before, after = create_two_commit_repository(
        tmp_path,
        before_text="class Order:\n    amount: int\n",
        after_text="class Order:\n    amount: str\n",
    )
    subprocess.run(
        ("git", "-C", str(repository), "rm", "--cached", "--", "src/app.py"),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
    )

    rejected = run_diff_cli(
        repository,
        tmp_path / "rejected",
        "--from",
        after,
        "--max-changed-paths",
        "1",
    )

    assert rejected.returncode == 1
    assert b"CSV-DIFF-002" in rejected.stderr
    assert not (tmp_path / "rejected").exists()

    output = tmp_path / "accepted"
    accepted = run_diff_cli(
        repository,
        output,
        "--from",
        after,
        "--max-changed-paths",
        "2",
    )

    assert accepted.returncode == 0, accepted.stderr.decode("utf-8", errors="replace")
    file_changes = json.loads((output / "file-changes.json").read_text(encoding="utf-8"))
    assert [
        (item["status"], item["old_path"], item["new_path"]) for item in file_changes["files"]
    ] == [
        ("D", "src/app.py", None),
        ("?", None, "src/app.py"),
    ]
    manifest = json.loads((output / "run-manifest.json").read_text(encoding="utf-8"))
    assert manifest["changed_path_budget"] == {
        "name": "max_changed_paths",
        "requested": 2,
        "resolved": 2,
        "actual": 2,
        "source": "cli",
    }


def test_default_budget_rejects_1002_tracked_to_untracked_records_and_override_admits(
    tmp_path: Path,
) -> None:
    before_files = {
        "src/app.py": "class Order:\n    amount: int\n",
        **{f"docs/file-{index:04d}.txt": f"value-{index}\n" for index in range(500)},
    }
    after_files = {**before_files, "src/app.py": "class Order:\n    amount: str\n"}
    repository, _before, after = create_two_commit_repository_from_files(
        tmp_path,
        before_files=before_files,
        after_files=after_files,
    )
    subprocess.run(
        ("git", "-C", str(repository), "rm", "--cached", "-r", "--", "."),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
    )

    rejected = run_diff_cli(repository, tmp_path / "rejected", "--from", after)

    assert rejected.returncode == 1
    assert b"CSV-DIFF-002" in rejected.stderr
    assert not (tmp_path / "rejected").exists()

    output = tmp_path / "accepted"
    accepted = run_diff_cli(
        repository,
        output,
        "--from",
        after,
        "--max-changed-paths",
        "1002",
    )

    assert accepted.returncode == 0, accepted.stderr.decode("utf-8", errors="replace")
    manifest = json.loads((output / "run-manifest.json").read_text(encoding="utf-8"))
    assert manifest["changed_path_budget"] == {
        "name": "max_changed_paths",
        "requested": 1002,
        "resolved": 1002,
        "actual": 1002,
        "source": "cli",
    }
    assert len(manifest["file_change_set"]["files"]) == 1002


def test_mode_only_working_tree_change_is_one_metadata_record(tmp_path: Path) -> None:
    repository, _before, after = create_two_commit_repository(
        tmp_path,
        before_text="class Order:\n    amount: int\n",
        after_text="class Order:\n    amount: str\n",
    )
    os.chmod(repository / "src" / "app.py", 0o755)
    output = tmp_path / "output"

    result = run_diff_cli(repository, output, "--from", after)

    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    file_changes = json.loads((output / "file-changes.json").read_text(encoding="utf-8"))
    assert file_changes["files"] == [
        {
            "status": "M",
            "old_path": "src/app.py",
            "new_path": "src/app.py",
            "hunks": [],
        }
    ]
    manifest = json.loads((output / "run-manifest.json").read_text(encoding="utf-8"))
    assert manifest["changed_path_budget"]["actual"] == 1


def test_regular_to_symlink_working_tree_change_is_type_transition(tmp_path: Path) -> None:
    repository, _before, after = create_two_commit_repository_from_files(
        tmp_path,
        before_files={
            "src/app.py": "class Order:\n    amount: int\n",
            "src/target.txt": "class Order:\n    amount: str\n",
        },
        after_files={
            "src/app.py": "class Order:\n    amount: str\n",
            "src/target.txt": "class Order:\n    amount: str\n",
        },
    )
    source = repository / "src" / "app.py"
    source.unlink()
    source.symlink_to("target.txt")
    output = tmp_path / "output"

    result = run_diff_cli(repository, output, "--from", after)

    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    file_changes = json.loads((output / "file-changes.json").read_text(encoding="utf-8"))
    assert [
        (item["status"], item["old_path"], item["new_path"]) for item in file_changes["files"]
    ] == [("T", "src/app.py", "src/app.py")]
    assert file_changes["files"][0]["hunks"] == []


def test_unique_working_tree_rename_is_one_canonical_record(tmp_path: Path) -> None:
    repository, _before, after = create_two_commit_repository(
        tmp_path,
        before_text="class Order:\n    amount: int\n",
        after_text="class Order:\n    amount: str\n",
    )
    subprocess.run(
        (
            "git",
            "-C",
            str(repository),
            "mv",
            "--",
            "src/app.py",
            "src/order.py",
        ),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
    )
    output = tmp_path / "output"

    result = run_diff_cli(repository, output, "--from", after)

    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    file_changes = json.loads((output / "file-changes.json").read_text(encoding="utf-8"))
    assert [
        (item["status"], item["old_path"], item["new_path"]) for item in file_changes["files"]
    ] == [("R", "src/app.py", "src/order.py")]
    assert (
        json.loads((output / "run-manifest.json").read_text(encoding="utf-8"))[
            "changed_path_budget"
        ]["actual"]
        == 1
    )


def test_unique_working_tree_copy_is_one_canonical_record(tmp_path: Path) -> None:
    repository, _before, after = create_two_commit_repository(
        tmp_path,
        before_text="class Order:\n    amount: int\n",
        after_text="class Order:\n    amount: str\n",
    )
    shutil.copyfile(repository / "src" / "app.py", repository / "src" / "order.py")
    subprocess.run(
        ("git", "-C", str(repository), "add", "--", "src/order.py"),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
    )
    output = tmp_path / "output"

    result = run_diff_cli(repository, output, "--from", after)

    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    file_changes = json.loads((output / "file-changes.json").read_text(encoding="utf-8"))
    assert [
        (item["status"], item["old_path"], item["new_path"]) for item in file_changes["files"]
    ] == [("C", "src/app.py", "src/order.py")]
    assert (
        json.loads((output / "run-manifest.json").read_text(encoding="utf-8"))[
            "changed_path_budget"
        ]["actual"]
        == 1
    )


def test_ambiguous_working_tree_copy_falls_back_to_add(tmp_path: Path) -> None:
    source = "class Order:\n    amount: str\n"
    repository, _before, after = create_two_commit_repository_from_files(
        tmp_path,
        before_files={
            "src/app.py": "class Order:\n    amount: int\n",
            "src/duplicate.py": source,
        },
        after_files={
            "src/app.py": source,
            "src/duplicate.py": source,
        },
    )
    shutil.copyfile(repository / "src" / "app.py", repository / "src" / "order.py")
    subprocess.run(
        ("git", "-C", str(repository), "add", "--", "src/order.py"),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
    )
    output = tmp_path / "output"

    result = run_diff_cli(repository, output, "--from", after)

    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    file_changes = json.loads((output / "file-changes.json").read_text(encoding="utf-8"))
    assert [
        (item["status"], item["old_path"], item["new_path"]) for item in file_changes["files"]
    ] == [("A", None, "src/order.py")]


def test_regular_to_gitlink_is_type_transition_with_unavailable_payload(
    tmp_path: Path,
) -> None:
    repository, _before, after = create_two_commit_repository(
        tmp_path,
        before_text="class Order:\n    amount: int\n",
        after_text="class Order:\n    amount: str\n",
    )
    source = repository / "src" / "app.py"
    source.unlink()
    source.mkdir()
    subprocess.run(
        ("git", "-C", str(source), "init", "--quiet", "--initial-branch=main"),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
    )
    (source / "README").write_text("nested\n", encoding="utf-8")
    subprocess.run(
        ("git", "-C", str(source), "add", "--", "README"),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        (
            "git",
            "-C",
            str(source),
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "--quiet",
            "--message=nested",
        ),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ("git", "-C", str(repository), "add", "--", "src/app.py"),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
    )
    output = tmp_path / "output"

    result = run_diff_cli(repository, output, "--from", after)

    assert result.returncode == 3, result.stderr.decode("utf-8", errors="replace")
    assert {path.name for path in output.iterdir()} == {
        "file-changes.json",
        "run-manifest.json",
    }
    file_changes = json.loads((output / "file-changes.json").read_text(encoding="utf-8"))
    assert [
        (item["status"], item["old_path"], item["new_path"]) for item in file_changes["files"]
    ] == [("T", "src/app.py", "src/app.py")]
    manifest = json.loads((output / "run-manifest.json").read_text(encoding="utf-8"))
    assert manifest["domains"][0]["incomplete_kind"] == "payload_unavailable"
    assert manifest["changed_path_budget"]["actual"] == 1


def test_unreadable_untracked_python_path_is_counted_before_analysis(tmp_path: Path) -> None:
    repository, before, _after = create_two_commit_repository(
        tmp_path,
        before_text="class Order:\n    amount: int\n",
        after_text="class Order:\n    amount: str\n",
    )
    unreadable = repository / "src" / "unreadable.py"
    unreadable.write_text("class Hidden:\n    pass\n", encoding="utf-8")
    os.chmod(unreadable, 0)
    try:
        result = run_diff_cli(
            repository,
            tmp_path / "output",
            "--from",
            before,
            "--max-changed-paths",
            "1",
        )
    finally:
        os.chmod(unreadable, 0o600)

    assert result.returncode == 1
    assert b"CSV-DIFF-002" in result.stderr
    assert not (tmp_path / "output").exists()


def test_unreadable_python_content_publishes_only_safe_metadata(tmp_path: Path) -> None:
    repository, _before, after = create_two_commit_repository(
        tmp_path,
        before_text="class Order:\n    amount: int\n",
        after_text="class Order:\n    amount: str\n",
    )
    unreadable = repository / "src" / "unreadable.py"
    unreadable.write_text("class Hidden:\n    pass\n", encoding="utf-8")
    os.chmod(unreadable, 0)
    output = tmp_path / "output"
    try:
        result = run_diff_cli(repository, output, "--from", after)
    finally:
        os.chmod(unreadable, 0o600)

    assert result.returncode == 3, result.stderr.decode("utf-8", errors="replace")
    assert {path.name for path in output.iterdir()} == {
        "file-changes.json",
        "run-manifest.json",
    }
    file_changes = json.loads((output / "file-changes.json").read_text(encoding="utf-8"))
    assert file_changes["files"] == [
        {
            "status": "?",
            "old_path": None,
            "new_path": "src/unreadable.py",
            "hunks": [],
        }
    ]
    manifest = json.loads((output / "run-manifest.json").read_text(encoding="utf-8"))
    assert manifest["domains"][0]["incomplete_kind"] == "payload_unavailable"
    assert manifest["domains"][0]["payload_available"] is False


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


def test_non_python_change_uses_repository_wide_hunk_evidence(tmp_path: Path) -> None:
    repository, before, after = create_two_commit_repository_from_files(
        tmp_path,
        before_files={
            "src/app.py": "class Order:\n    amount: int\n",
            "README.txt": "before\n",
        },
        after_files={
            "src/app.py": "class Order:\n    amount: int\n",
            "README.txt": "after\n",
        },
    )
    output = tmp_path / "output"

    result = run_diff_cli(repository, output, "--from", before, "--to", after)

    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    file_changes = json.loads((output / "file-changes.json").read_text(encoding="utf-8"))
    readme = next(item for item in file_changes["files"] if item["new_path"] == "README.txt")
    assert readme["status"] == "M"
    assert len(readme["hunks"]) == 1
    hunk = readme["hunks"][0]
    assert {key: hunk[key] for key in hunk if key != "hunk_id"} == {
        "old_start": 1,
        "old_line_count": 1,
        "new_start": 1,
        "new_line_count": 1,
        "ordinal": 0,
    }
    assert len(hunk["hunk_id"]) == 64


@pytest.mark.parametrize(
    ("before_text", "after_text"),
    (("same\n", "same"), ("same\n", "same\r\n")),
)
def test_line_terminator_only_change_has_deterministic_hunk(
    tmp_path: Path,
    before_text: str,
    after_text: str,
) -> None:
    repository, before, after = create_two_commit_repository_from_files(
        tmp_path,
        before_files={
            "src/app.py": "class Order:\n    amount: int\n",
            "README.txt": before_text,
        },
        after_files={
            "src/app.py": "class Order:\n    amount: int\n",
            "README.txt": after_text,
        },
    )
    output = tmp_path / "output"

    result = run_diff_cli(repository, output, "--from", before, "--to", after)

    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    file_changes = json.loads((output / "file-changes.json").read_text(encoding="utf-8"))
    readme = next(item for item in file_changes["files"] if item["new_path"] == "README.txt")
    assert [
        (
            item["old_start"],
            item["old_line_count"],
            item["new_start"],
            item["new_line_count"],
            item["ordinal"],
        )
        for item in readme["hunks"]
    ] == [(1, 1, 1, 1, 0)]


def test_unavailable_non_python_content_does_not_publish_fake_hunk(tmp_path: Path) -> None:
    repository, _before, after = create_two_commit_repository_from_files(
        tmp_path,
        before_files={
            "src/app.py": "class Order:\n    amount: int\n",
            "README.txt": "before\n",
        },
        after_files={
            "src/app.py": "class Order:\n    amount: str\n",
            "README.txt": "after\n",
        },
    )
    unreadable = repository / "README.txt"
    os.chmod(unreadable, 0)
    output = tmp_path / "output"
    try:
        result = run_diff_cli(repository, output, "--from", after)
    finally:
        os.chmod(unreadable, 0o600)

    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    file_changes = json.loads((output / "file-changes.json").read_text(encoding="utf-8"))
    readme = next(item for item in file_changes["files"] if item["new_path"] == "README.txt")
    assert readme == {
        "status": "M",
        "old_path": "README.txt",
        "new_path": "README.txt",
        "hunks": [],
    }


def test_unavailable_changed_python_hunk_evidence_is_payload_unavailable(
    tmp_path: Path,
) -> None:
    repository, _before, after = create_two_commit_repository(
        tmp_path,
        before_text="class Order:\n    amount: int\n",
        after_text="class Order:\n    amount: str\n",
    )
    (repository / "src" / "app.py").write_bytes(
        b"class Order:\n    amount: str\n#" + (b"x" * (128 * 1024)) + b"\n"
    )
    output = tmp_path / "output"

    result = run_diff_cli(repository, output, "--from", after)

    assert result.returncode == 3, result.stderr.decode("utf-8", errors="replace")
    assert {path.name for path in output.iterdir()} == {
        "file-changes.json",
        "run-manifest.json",
    }
    file_changes = json.loads((output / "file-changes.json").read_text(encoding="utf-8"))
    assert file_changes["files"] == [
        {
            "status": "M",
            "old_path": "src/app.py",
            "new_path": "src/app.py",
            "hunks": [],
        }
    ]
    manifest = json.loads((output / "run-manifest.json").read_text(encoding="utf-8"))
    assert manifest["semantic_sides"]["after"]["kind"] == "analysis-failed"
    assert manifest["domains"][0]["incomplete_kind"] == "payload_unavailable"


def test_missing_commit_blob_is_run_fatal_without_publication(tmp_path: Path) -> None:
    repository, before, after = create_two_commit_repository(
        tmp_path,
        before_text="class Order:\n    amount: int\n",
        after_text="class Order:\n    amount: str\n",
    )
    object_id = subprocess.check_output(
        ("git", "-C", str(repository), "rev-parse", f"{before}:src/app.py"),
        text=True,
    ).strip()
    (repository / ".git" / "objects" / object_id[:2] / object_id[2:]).unlink()
    output = tmp_path / "output"

    result = run_diff_cli(repository, output, "--from", before, "--to", after)

    assert result.returncode == 1
    assert b"CSV-DIFF-001" in result.stderr
    assert not output.exists()


def test_working_tree_drift_aborts_staged_diff_before_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, _before, after = create_two_commit_repository(
        tmp_path,
        before_text="class Order:\n    amount: int\n",
        after_text="class Order:\n    amount: str\n",
    )
    counter = tmp_path / "ls-files-count"
    source = repository / "src" / "app.py"
    proxy = _git_proxy(
        tmp_path,
        "if sys.argv[-5:] == "
        "['ls-files', '-z', '--cached', '--others', '--exclude-standard']:\n"
        f"    counter = pathlib.Path({str(counter)!r})\n"
        "    count = int(counter.read_text()) + 1 if counter.exists() else 1\n"
        "    counter.write_text(str(count))\n"
        "    if count == 2:\n"
        f"        pathlib.Path({str(source)!r}).write_text("
        "'class Mutated:\\n    pass\\n')",
    )
    monkeypatch.setenv("PATH", f"{proxy}{os.pathsep}{os.environ['PATH']}")
    output = tmp_path / "output"

    result = run_diff_cli(repository, output, "--from", after)

    assert result.returncode == 1
    assert b"CSV-SOURCE-001" in result.stderr
    assert not output.exists()
    assert list(tmp_path.glob(".code-structure-viz-staging-*")) == []


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
