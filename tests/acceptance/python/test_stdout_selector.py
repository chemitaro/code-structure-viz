import ctypes
import json
import os
import shutil
import signal
from pathlib import Path

import pytest

from code_structure_viz.cli.main import main
from tests.helpers.acceptance import (
    ROOT,
    initialize_fixture_repository,
    initialize_repository,
    run_cli,
)
from tests.helpers.diff import create_two_commit_repository, run_diff_cli


class _RenameFunction:
    def __init__(self, operation: object) -> None:
        self._operation = operation
        self.argtypes: object = None
        self.restype: object = None

    def __call__(self, *arguments: object) -> int:
        operation = self._operation
        assert callable(operation)
        if len(arguments) == 5:
            source_directory, source, destination_directory, destination, _flags = arguments
            assert isinstance(source_directory, int)
            assert isinstance(source, bytes)
            assert isinstance(destination_directory, int)
            assert isinstance(destination, bytes)
            operation(
                Path(os.fsdecode(source)),
                Path(os.fsdecode(destination)),
                source_directory=source_directory,
                destination_directory=destination_directory,
            )
        else:
            paths = [argument for argument in arguments if isinstance(argument, bytes)]
            assert len(paths) == 2
            operation(Path(os.fsdecode(paths[0])), Path(os.fsdecode(paths[1])))
        return 0


class _RenameLibrary:
    def __init__(self, operation: object) -> None:
        function = _RenameFunction(operation)
        self.renamex_np = function
        self.renameatx_np = function
        self.renameat2 = function


@pytest.mark.parametrize(
    ("format_value", "selector", "artifact"),
    [
        ("semantic-json", "python:semantic-json", "python.snapshot.semantic.json"),
        ("plantuml", "python:plantuml", "python.snapshot.puml"),
    ],
)
def test_available_domain_selector_is_exact_final_file_bytes(
    tmp_path: Path,
    format_value: str,
    selector: str,
    artifact: str,
) -> None:
    repository = initialize_fixture_repository(tmp_path, "whole")
    output = tmp_path / "output"

    result = run_cli(
        repository,
        output,
        "--format",
        format_value,
        "--stdout",
        selector,
    )

    assert result.returncode == 0
    assert result.stdout == (output / artifact).read_bytes()
    assert result.stderr == b""
    assert sorted(path.name for path in output.iterdir()) == [artifact, "run-manifest.json"]


def test_manifest_selector_is_exact_final_manifest_bytes(tmp_path: Path) -> None:
    repository = initialize_fixture_repository(tmp_path, "whole")
    output = tmp_path / "output"

    result = run_cli(repository, output, "--stdout", "manifest")

    assert result.returncode == 0
    assert result.stdout == (output / "run-manifest.json").read_bytes()
    assert result.stderr == b""


def test_not_applicable_domain_selector_emits_closed_unavailable_result(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repo"
    initialize_repository(repository)
    output = tmp_path / "output"

    result = run_cli(repository, output, "--stdout", "python:semantic-json")

    assert result.returncode == 0
    assert result.stdout == (
        b'{"type":"stdout_result","schema":"code-structure-viz.stdout-result/v1",'
        b'"selector":"python:semantic-json","availability":false,'
        b'"domain_status":"not_applicable","stable_reason":"domain_not_applicable",'
        b'"artifact":null}\n'
    )
    assert result.stderr == b""


def test_payload_unavailable_domain_selector_emits_closed_result_and_diagnostic(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repo"
    initialize_repository(repository)
    output = tmp_path / "output"

    result = run_cli(
        repository,
        output,
        "--target",
        "class:app.missing.Thing",
        "--stdout",
        "python:plantuml",
    )

    assert result.returncode == 3
    assert result.stdout == (
        b'{"type":"stdout_result","schema":"code-structure-viz.stdout-result/v1",'
        b'"selector":"python:plantuml","availability":false,'
        b'"domain_status":"incomplete",'
        b'"stable_reason":"domain_payload_unavailable","artifact":null}\n'
    )
    assert json.loads(result.stderr)["code"] == "CSV-PY-006"


def test_partial_safe_selector_copies_incomplete_payload_exactly(tmp_path: Path) -> None:
    repository = initialize_fixture_repository(tmp_path, "partial_safe")
    output = tmp_path / "output"

    result = run_cli(
        repository,
        output,
        "--target",
        "module:app.good",
        "--stdout",
        "python:semantic-json",
    )

    assert result.returncode == 3
    assert result.stdout == (output / "python.snapshot.semantic.json").read_bytes()
    assert json.loads(result.stderr)["code"] == "CSV-PY-003"


def test_unselected_stdout_format_is_usage_error_before_source_acquisition(
    tmp_path: Path,
) -> None:
    repository = initialize_fixture_repository(tmp_path, "whole")
    output = tmp_path / "output"

    result = run_cli(
        repository,
        output,
        "--format",
        "semantic-json",
        "--stdout",
        "python:plantuml",
    )

    assert result.returncode == 2
    assert result.stdout == b""
    assert json.loads(result.stderr)["code"] == "CSV-USAGE-005"
    assert not output.exists()


def test_depth_limit_frontier_does_not_emit_stderr(tmp_path: Path) -> None:
    repository = initialize_fixture_repository(tmp_path, "targeted")
    output = tmp_path / "output"

    result = run_cli(
        repository,
        output,
        "--target",
        "class:app.a.A",
        "--upstream-depth",
        "0",
        "--downstream-depth",
        "0",
    )

    assert result.returncode == 0
    assert result.stderr == b""
    semantic = json.loads((output / "python.snapshot.semantic.json").read_bytes())
    assert semantic["coverage"]["frontier"] != []


def test_manifest_selector_on_run_fatal_reports_final_manifest_unavailable(
    tmp_path: Path,
) -> None:
    repository = initialize_fixture_repository(tmp_path, "whole")
    output = tmp_path / "output"
    output.mkdir()

    result = run_cli(repository, output, "--stdout", "manifest")

    assert result.returncode == 1
    assert result.stdout == (
        b'{"type":"stdout_result","schema":"code-structure-viz.stdout-result/v1",'
        b'"selector":"manifest","availability":false,"run_status":"fatal",'
        b'"stable_reason":"final_manifest_unavailable","artifact":null}\n'
    )
    assert json.loads(result.stderr)["code"] == "CSV-OUTPUT-001"


def test_post_rename_signal_and_output_deletion_keep_bound_stdout_and_exit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsysbinary: pytest.CaptureFixture[bytes],
) -> None:
    repository = initialize_fixture_repository(tmp_path, "whole")
    output = tmp_path / "output"
    expected = (
        ROOT / "tests" / "golden" / "python_snapshot" / "whole" / "python.snapshot.puml"
    ).read_bytes()
    real_rename = os.rename
    published = False

    def rename_then_delete_and_interrupt(
        source: Path,
        destination: Path,
        *,
        source_directory: int | None = None,
        destination_directory: int | None = None,
    ) -> None:
        nonlocal published
        if source_directory is None or destination_directory is None:
            real_rename(source, destination)
        else:
            real_rename(
                source,
                destination,
                src_dir_fd=source_directory,
                dst_dir_fd=destination_directory,
            )
        if output.exists() and not published:
            published = True
            shutil.rmtree(output)
            os.kill(os.getpid(), signal.SIGINT)

    monkeypatch.setattr(os, "rename", rename_then_delete_and_interrupt)
    monkeypatch.setattr(
        ctypes,
        "CDLL",
        lambda *_arguments, **_keywords: _RenameLibrary(rename_then_delete_and_interrupt),
    )

    exit_code = main(
        [
            "snapshot",
            "--repo",
            str(repository),
            "--output-dir",
            str(output),
            "--domain",
            "python",
            "--format",
            "plantuml",
            "--stdout",
            "python:plantuml",
        ]
    )

    captured = capsysbinary.readouterr()
    assert published
    assert exit_code == 0
    assert captured.out == expected
    assert captured.err == b""


def test_diff_stdout_selector_copies_exact_semantic_artifact_bytes(tmp_path: Path) -> None:
    repository, before, after = create_two_commit_repository(
        tmp_path,
        before_text="class Order:\n    amount: int\n",
        after_text="class Order:\n    amount: str\n",
    )
    output = tmp_path / "output"

    result = run_diff_cli(
        repository,
        output,
        "--from",
        before,
        "--to",
        after,
        "--stdout",
        "python:semantic-json",
    )

    assert result.returncode == 0
    assert result.stdout == (output / "python.diff.semantic.json").read_bytes()
    assert b"run_summary" not in result.stdout


def test_diff_manifest_selector_copies_exact_manifest_bytes(tmp_path: Path) -> None:
    repository, before, after = create_two_commit_repository(
        tmp_path,
        before_text="class Order:\n    amount: int\n",
        after_text="class Order:\n    amount: str\n",
    )
    output = tmp_path / "output"

    result = run_diff_cli(
        repository,
        output,
        "--from",
        before,
        "--to",
        after,
        "--stdout",
        "manifest",
    )

    assert result.returncode == 0
    assert result.stdout == (output / "run-manifest.json").read_bytes()


def test_diff_unavailable_domain_selector_returns_typed_result(tmp_path: Path) -> None:
    repository, before, after = create_two_commit_repository(
        tmp_path,
        before_text=(
            "class Order:\n"
            "    def total(self, amount):\n"
            "        return amount\n\n"
            "class Customer:\n"
            "    name: str\n"
        ),
        after_text=(
            "class Order:\n"
            "    def total(self, amount: int) -> int:\n"
            "        return amount\n\n"
            "class Customer:\n"
            "    name: bytes\n"
        ),
    )
    output = tmp_path / "output"

    result = run_diff_cli(
        repository,
        output,
        "--from",
        before,
        "--to",
        after,
        "--max-entities",
        "1",
        "--stdout",
        "python:semantic-json",
    )

    assert result.returncode == 3
    assert json.loads(result.stdout) == {
        "type": "stdout_result",
        "schema": "code-structure-viz.stdout-result/v1",
        "selector": "python:semantic-json",
        "availability": False,
        "domain_status": "incomplete",
        "stable_reason": "domain_payload_unavailable",
        "artifact": None,
    }


def test_diff_selector_compatibility_is_rejected_before_publication(tmp_path: Path) -> None:
    repository, before, after = create_two_commit_repository(
        tmp_path,
        before_text="class Order:\n    amount: int\n",
        after_text="class Order:\n    amount: str\n",
    )
    output = tmp_path / "output"

    result = run_diff_cli(
        repository,
        output,
        "--from",
        before,
        "--to",
        after,
        "--format",
        "semantic-json",
        "--stdout",
        "python:plantuml",
    )

    assert result.returncode == 2
    assert result.stdout == b""
    assert not output.exists()
