import json
import os
import shutil
import signal
import stat
import subprocess
import sys
import time
from pathlib import Path

import pytest

from tests.helpers.acceptance import (
    initialize_fixture_repository,
    initialize_repository,
    run_cli,
)
from tests.helpers.fixture_repo import (
    git as git_command,
)
from tests.helpers.fixture_repo import (
    initialize_repository as initialize_unborn_repository,
)


def _git_proxy(tmp_path: Path, behavior: str) -> tuple[Path, str]:
    real_git = shutil.which("git")
    assert real_git is not None
    shim = tmp_path / "bin" / "git"
    shim.parent.mkdir(exist_ok=True)
    shim.write_text(
        "#!/usr/bin/env python3\n"
        "import os, pathlib, sys, time\n"
        f"{behavior}\n"
        "os.execv(os.environ['CSV_REAL_GIT'], [os.environ['CSV_REAL_GIT'], *sys.argv[1:]])\n",
        encoding="utf-8",
    )
    shim.chmod(shim.stat().st_mode | stat.S_IXUSR)
    return shim.parent, real_git


@pytest.mark.parametrize(
    ("target", "context_field", "context_value"),
    [
        ("path:src/app/missing.py", "path", "src/app/missing.py"),
        ("module:app.missing", "symbol", "module:app.missing"),
        ("class:app.missing.Thing", "symbol", "class:app.missing.Thing"),
    ],
)
def test_explicit_target_in_no_python_repository_is_payload_unavailable(
    tmp_path: Path,
    target: str,
    context_field: str,
    context_value: str,
) -> None:
    repository = tmp_path / "repo"
    initialize_repository(repository)
    output = tmp_path / "output"

    result = run_cli(repository, output, "--target", target)

    assert result.returncode == 3
    assert sorted(path.name for path in output.iterdir()) == ["run-manifest.json"]
    diagnostics = [json.loads(line) for line in result.stderr.splitlines()]
    assert len(diagnostics) == 1
    assert diagnostics[0]["code"] == "CSV-PY-006"
    assert diagnostics[0][context_field] == context_value
    manifest = json.loads((output / "run-manifest.json").read_bytes())
    domain = manifest["domains"][0]
    assert (domain["status"], domain["incomplete_kind"]) == (
        "incomplete",
        "payload_unavailable",
    )
    assert domain["payload_available"] is False
    assert domain["artifact_paths"] == []


def test_failed_requested_seed_publishes_manifest_with_file_and_target_diagnostics(
    tmp_path: Path,
) -> None:
    repository = initialize_fixture_repository(tmp_path, "failed_seed")
    output = tmp_path / "output"

    result = run_cli(repository, output, "--target", "module:app.broken")

    assert result.returncode == 3
    assert sorted(path.name for path in output.iterdir()) == ["run-manifest.json"]
    diagnostics = [json.loads(line) for line in result.stderr.splitlines()]
    assert [(item["code"], item["path"], item["symbol"]) for item in diagnostics] == [
        ("CSV-PY-006", None, "module:app.broken"),
        ("CSV-PY-003", "src/app/broken.py", None),
    ]


def test_unsafe_source_symlink_is_payload_unavailable_without_reading_target(
    tmp_path: Path,
) -> None:
    outside = tmp_path / "outside.py"
    outside.write_text('SECRET = "outside"\n', encoding="utf-8")
    repository = tmp_path / "repo"
    (repository / "src" / "app").mkdir(parents=True)
    (repository / "src" / "app" / "link.py").symlink_to(outside)
    initialize_repository(repository)
    output = tmp_path / "output"

    result = run_cli(repository, output)

    assert result.returncode == 3
    assert sorted(path.name for path in output.iterdir()) == ["run-manifest.json"]
    diagnostic_value = json.loads(result.stderr)
    assert diagnostic_value["code"] == "CSV-SOURCE-002"
    assert diagnostic_value["path"] == "src/app/link.py"
    assert b"outside" not in result.stdout + result.stderr


def test_non_seed_class_identity_collision_with_safe_entity_is_partial_safe(
    tmp_path: Path,
) -> None:
    repository = initialize_fixture_repository(tmp_path, "class_collision")
    output = tmp_path / "output"

    result = run_cli(repository, output)

    assert result.returncode == 3
    assert sorted(path.name for path in output.iterdir()) == [
        "python.snapshot.puml",
        "python.snapshot.semantic.json",
        "run-manifest.json",
    ]
    diagnostic_value = json.loads(result.stderr)
    assert diagnostic_value["code"] == "CSV-PY-012"
    assert diagnostic_value["symbol"] == "python:class:app.duplicate:Duplicate"


def test_class_identity_collision_without_safe_entity_is_payload_unavailable(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repo"
    source = repository / "src" / "app" / "duplicate.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        "class Duplicate:\n    pass\n\nclass Duplicate:\n    pass\n",
        encoding="utf-8",
    )
    initialize_repository(repository)
    output = tmp_path / "output"

    result = run_cli(repository, output)

    assert result.returncode == 3
    assert sorted(path.name for path in output.iterdir()) == ["run-manifest.json"]
    diagnostic_value = json.loads(result.stderr)
    assert diagnostic_value["code"] == "CSV-PY-012"


def test_malicious_unknown_config_key_is_constant_usage_error_with_no_artifacts(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repo"
    initialize_repository(repository)
    config = tmp_path / "config.toml"
    sentinel = "/tmp/secret"
    config.write_text(
        'schema = "code-structure-viz.config/v1"\n["/tmp/secret"]\nvalue = true\n',
        encoding="utf-8",
    )
    output = tmp_path / "output"

    result = run_cli(repository, output, "--config", str(config))

    assert result.returncode == 2
    assert result.stdout == b""
    assert not output.exists()
    diagnostic_value = json.loads(result.stderr)
    assert diagnostic_value["code"] == "CSV-CONFIG-003"
    assert diagnostic_value["message"] == "Configuration contains an unknown key."
    assert all(diagnostic_value[key] is None for key in ("domain", "path", "symbol", "line"))
    assert sentinel.encode() not in result.stdout + result.stderr


def test_existing_and_inside_repository_outputs_are_run_fatal_without_publication(
    tmp_path: Path,
) -> None:
    repository = initialize_fixture_repository(tmp_path, "whole")
    existing = tmp_path / "existing"
    existing.mkdir()

    existing_result = run_cli(repository, existing)
    inside_result = run_cli(repository, repository / "generated")

    assert existing_result.returncode == 1
    assert json.loads(existing_result.stderr)["code"] == "CSV-OUTPUT-001"
    assert list(existing.iterdir()) == []
    assert inside_result.returncode == 1
    assert json.loads(inside_result.stderr)["code"] == "CSV-OUTPUT-002"
    assert not (repository / "generated").exists()


def test_zero_class_repository_missing_class_target_is_payload_unavailable(
    tmp_path: Path,
) -> None:
    repository = initialize_fixture_repository(tmp_path, "zero_class")
    output = tmp_path / "output"

    result = run_cli(
        repository,
        output,
        "--target",
        "class:app.a.Missing",
        "--stdout",
        "python:semantic-json",
    )

    assert result.returncode == 3
    assert sorted(path.name for path in output.iterdir()) == ["run-manifest.json"]
    assert json.loads(result.stdout) == {
        "type": "stdout_result",
        "schema": "code-structure-viz.stdout-result/v1",
        "selector": "python:semantic-json",
        "availability": False,
        "domain_status": "incomplete",
        "stable_reason": "domain_payload_unavailable",
        "artifact": None,
    }
    diagnostic = json.loads(result.stderr)
    assert (diagnostic["code"], diagnostic["symbol"]) == (
        "CSV-PY-006",
        "class:app.a.Missing",
    )


def test_module_collision_is_one_group_and_collided_seed_adds_one_target_diagnostic(
    tmp_path: Path,
) -> None:
    repository = initialize_fixture_repository(tmp_path, "module_collision")
    whole_output = tmp_path / "whole-output"
    seed_output = tmp_path / "seed-output"

    whole = run_cli(repository, whole_output)
    seed = run_cli(
        repository,
        seed_output,
        "--target",
        "module:pkg.item",
        "--stdout",
        "python:plantuml",
    )

    assert whole.returncode == 3
    assert sorted(path.name for path in whole_output.iterdir()) == [
        "python.snapshot.puml",
        "python.snapshot.semantic.json",
        "run-manifest.json",
    ]
    assert [json.loads(line)["code"] for line in whole.stderr.splitlines()] == ["CSV-PY-005"]
    assert seed.returncode == 3
    assert sorted(path.name for path in seed_output.iterdir()) == ["run-manifest.json"]
    assert [json.loads(line)["code"] for line in seed.stderr.splitlines()] == [
        "CSV-PY-005",
        "CSV-PY-007",
    ]


def test_colliding_class_seed_is_payload_unavailable_with_group_and_target_diagnostics(
    tmp_path: Path,
) -> None:
    repository = initialize_fixture_repository(tmp_path, "class_collision")
    output = tmp_path / "output"

    result = run_cli(
        repository,
        output,
        "--target",
        "class:app.duplicate.Duplicate",
        "--stdout",
        "python:semantic-json",
    )

    assert result.returncode == 3
    assert sorted(path.name for path in output.iterdir()) == ["run-manifest.json"]
    diagnostics = [json.loads(line) for line in result.stderr.splitlines()]
    assert [(item["code"], item["symbol"]) for item in diagnostics] == [
        ("CSV-PY-007", "class:app.duplicate.Duplicate"),
        ("CSV-PY-012", "python:class:app.duplicate:Duplicate"),
    ]


def test_true_unborn_repository_with_1001_non_python_changes_is_a_complete_snapshot(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repo"
    initialize_unborn_repository(repository)
    source = repository / "src" / "app" / "model.py"
    source.parent.mkdir(parents=True)
    source.write_text("class Model:\n    pass\n", encoding="utf-8")
    changes = repository / "changes"
    changes.mkdir()
    for index in range(1001):
        (changes / f"change-{index:04}.txt").write_text("changed\n", encoding="utf-8")
    output = tmp_path / "output"

    result = run_cli(repository, output)

    assert result.returncode == 0
    assert result.stderr == b""
    semantic = json.loads((output / "python.snapshot.semantic.json").read_bytes())
    manifest = json.loads((output / "run-manifest.json").read_bytes())
    assert semantic["source"]["head_commit"] is None
    assert manifest["source"]["head_commit"] is None
    assert manifest["source"]["file_count"] == 1
    assert manifest["domains"][0]["entity_count"] == 1

    rejected = run_cli(
        repository,
        tmp_path / "diff-output",
        "--max-changed-paths",
        "1",
    )
    assert rejected.returncode == 2
    assert rejected.stdout == b""
    assert json.loads(rejected.stderr)["code"] == "CSV-USAGE-003"
    assert not (tmp_path / "diff-output").exists()


def test_existing_non_commit_and_invalid_detached_heads_are_run_fatal(
    tmp_path: Path,
) -> None:
    results = []
    for name, detached in (("existing", False), ("detached", True)):
        repository = tmp_path / name
        initialize_unborn_repository(repository)
        object_id = (
            git_command(repository, "hash-object", "-w", ".git/HEAD").stdout.decode("ascii").strip()
        )
        if detached:
            (repository / ".git" / "HEAD").write_text(f"{object_id}\n", encoding="ascii")
        else:
            git_command(repository, "symbolic-ref", "HEAD", "refs/heads/broken")
            (repository / ".git" / "refs" / "heads" / "broken").write_text(
                f"{object_id}\n", encoding="ascii"
            )
        output = tmp_path / f"{name}-output"
        results.append((run_cli(repository, output), output))

    for result, output in results:
        assert result.returncode == 1
        assert json.loads(result.stdout) == {
            "type": "run_summary",
            "schema": "code-structure-viz.run-summary/v1",
            "run_status": "fatal",
            "exit_code": 1,
            "domains": [],
            "manifest": None,
        }
        diagnostic = json.loads(result.stderr)
        assert diagnostic["code"] == "CSV-REPO-002"
        assert all(diagnostic[key] is None for key in ("domain", "path", "symbol", "line"))
        assert not output.exists()


def test_non_utf8_git_index_path_is_fatal_without_manifest_or_synthetic_path(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repo"
    initialize_unborn_repository(repository)
    blob = subprocess.run(
        ("git", "-C", os.fsdecode(repository), "hash-object", "-w", "--stdin"),
        input=b"",
        capture_output=True,
        check=True,
    ).stdout.strip()
    subprocess.run(
        ("git", "-C", os.fsdecode(repository), "update-index", "-z", "--index-info"),
        input=b"100644 " + blob + b"\tbad-\xff.py\0",
        capture_output=True,
        check=True,
    )
    output = tmp_path / "output"

    result = run_cli(repository, output, "--stdout", "manifest")

    assert result.returncode == 1
    assert json.loads(result.stdout)["stable_reason"] == "final_manifest_unavailable"
    diagnostic = json.loads(result.stderr)
    assert diagnostic["code"] == "CSV-SOURCE-003"
    assert all(diagnostic[key] is None for key in ("domain", "path", "symbol", "line"))
    assert b"bad" not in result.stdout + result.stderr
    assert not output.exists()


def test_nfc_path_collision_is_payload_unavailable_with_one_group_diagnostic(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repo"
    source = repository / "src" / "café.py"
    source.parent.mkdir(parents=True)
    source.write_text("class Safe:\n    pass\n", encoding="utf-8")
    initialize_repository(repository)
    proxy, real_git = _git_proxy(
        tmp_path,
        "if sys.argv[-5:] == ['ls-files', '-z', '--cached', '--others', '--exclude-standard']:\n"
        "    os.write(1, 'src/café.py\\0src/cafe\\u0301.py\\0'.encode('utf-8'))\n"
        "    raise SystemExit(0)",
    )
    output = tmp_path / "output"

    result = run_cli(
        repository,
        output,
        "--stdout",
        "python:semantic-json",
        environment={
            "PATH": f"{proxy}{os.pathsep}{os.environ['PATH']}",
            "CSV_REAL_GIT": real_git,
        },
    )

    assert result.returncode == 3
    assert sorted(path.name for path in output.iterdir()) == ["run-manifest.json"]
    assert json.loads(result.stdout)["stable_reason"] == "domain_payload_unavailable"
    diagnostics = [json.loads(line) for line in result.stderr.splitlines()]
    assert [(item["code"], item["path"]) for item in diagnostics] == [
        ("CSV-SOURCE-004", "src/café.py")
    ]


def test_source_drift_aborts_staged_payload_and_manifest_before_publication(
    tmp_path: Path,
) -> None:
    repository = initialize_fixture_repository(tmp_path, "whole")
    counter = tmp_path / "ls-files-count"
    mutated_source = repository / "src" / "domain" / "base.py"
    proxy, real_git = _git_proxy(
        tmp_path,
        "if sys.argv[-5:] == ['ls-files', '-z', '--cached', '--others', '--exclude-standard']:\n"
        "    counter = pathlib.Path(os.environ['CSV_COUNTER'])\n"
        "    count = int(counter.read_text()) + 1 if counter.exists() else 1\n"
        "    counter.write_text(str(count))\n"
        "    if count == 2:\n"
        "        pathlib.Path(os.environ['CSV_MUTATE']).write_text('class Mutated:\\n    pass\\n')",
    )
    output = tmp_path / "output"

    result = run_cli(
        repository,
        output,
        "--stdout",
        "manifest",
        environment={
            "PATH": f"{proxy}{os.pathsep}{os.environ['PATH']}",
            "CSV_REAL_GIT": real_git,
            "CSV_COUNTER": str(counter),
            "CSV_MUTATE": str(mutated_source),
        },
    )

    assert result.returncode == 1
    assert json.loads(result.stdout)["stable_reason"] == "final_manifest_unavailable"
    assert json.loads(result.stderr)["code"] == "CSV-SOURCE-001"
    assert not output.exists()
    assert list(tmp_path.glob(".code-structure-viz-staging-*")) == []


def test_sigint_during_final_probe_interrupts_before_directory_rename(tmp_path: Path) -> None:
    repository = initialize_fixture_repository(tmp_path, "whole")
    counter = tmp_path / "ls-files-count"
    ready = tmp_path / "ready"
    proxy, real_git = _git_proxy(
        tmp_path,
        "if sys.argv[-5:] == ['ls-files', '-z', '--cached', '--others', '--exclude-standard']:\n"
        "    counter = pathlib.Path(os.environ['CSV_COUNTER'])\n"
        "    count = int(counter.read_text()) + 1 if counter.exists() else 1\n"
        "    counter.write_text(str(count))\n"
        "    if count == 2:\n"
        "        pathlib.Path(os.environ['CSV_READY']).write_text('ready')\n"
        "        time.sleep(1)",
    )
    output = tmp_path / "output"
    process = subprocess.Popen(
        (
            sys.executable,
            "-m",
            "code_structure_viz",
            "snapshot",
            "--repo",
            str(repository),
            "--output-dir",
            str(output),
            "--domain",
            "python",
            "--stdout",
            "manifest",
        ),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=repository,
        env={
            **os.environ,
            "NO_COLOR": "1",
            "PATH": f"{proxy}{os.pathsep}{os.environ['PATH']}",
            "CSV_REAL_GIT": real_git,
            "CSV_COUNTER": str(counter),
            "CSV_READY": str(ready),
        },
    )
    try:
        deadline = time.monotonic() + 10
        while not ready.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.01)
        assert ready.exists()
        process.send_signal(signal.SIGINT)
        stdout, stderr = process.communicate(timeout=10)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()

    assert process.returncode == 130
    assert json.loads(stdout)["stable_reason"] == "run_interrupted"
    assert json.loads(stderr)["code"] == "CSV-INTERRUPT-001"
    assert not output.exists()
    assert list(tmp_path.glob(".code-structure-viz-staging-*")) == []
