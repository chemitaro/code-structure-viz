import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath

import pytest

from code_structure_viz.source.git_repository import (
    CommandResult,
    Commit,
    GitIndexEntry,
    GitReadError,
    GitRepositoryReader,
    SubprocessRunner,
    Unborn,
    UnrepresentableGitPathFatal,
)


class ScriptedRunner:
    def __init__(self, results: Sequence[CommandResult]) -> None:
        self._results = list(results)
        self.calls: list[tuple[tuple[str, ...], dict[str, str]]] = []

    def run(self, argv: tuple[str, ...], env: Mapping[str, str]) -> CommandResult:
        self.calls.append((argv, dict(env)))
        if not self._results:
            raise AssertionError(f"unexpected command: {argv!r}")
        return self._results.pop(0)


def _result(returncode: int, stdout: bytes = b"", stderr: bytes = b"") -> CommandResult:
    return CommandResult(returncode=returncode, stdout=stdout, stderr=stderr)


def test_resolve_head_state_accepts_full_sha1_and_uses_fixed_read_only_command(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    object_id = "1" * 40
    runner = ScriptedRunner([_result(0, f"{object_id}\n".encode("ascii"))])

    state = GitRepositoryReader(repo, runner=runner).resolve_head_state()

    assert state == Commit(object_id)
    assert runner.calls[0][0] == (
        "git",
        "-C",
        str(repo),
        "-c",
        "core.fsmonitor=false",
        "rev-parse",
        "--verify",
        "HEAD^{commit}",
    )
    env = runner.calls[0][1]
    assert {
        key: env[key]
        for key in (
            "LC_ALL",
            "LANG",
            "GIT_OPTIONAL_LOCKS",
            "GIT_CONFIG_NOSYSTEM",
            "GIT_CONFIG_GLOBAL",
            "GIT_TERMINAL_PROMPT",
            "GIT_PAGER",
            "PAGER",
            "NO_COLOR",
        )
    } == {
        "LC_ALL": "C",
        "LANG": "C",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_PAGER": "cat",
        "PAGER": "cat",
        "NO_COLOR": "1",
    }


def test_git_child_environment_drops_repository_config_object_and_trace_injection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    hostile = {
        "GIT_DIR": "/tmp/attacker-git-dir",
        "GIT_WORK_TREE": "/tmp/attacker-work-tree",
        "GIT_INDEX_FILE": "/tmp/attacker-index",
        "GIT_OBJECT_DIRECTORY": "/tmp/attacker-objects",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES": "/tmp/attacker-alternates",
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "alias.rev-parse",
        "GIT_CONFIG_VALUE_0": "!malicious",
        "GIT_TRACE": "1",
        "GIT_TRACE2": "/tmp/attacker-trace",
    }
    for key, value in hostile.items():
        monkeypatch.setenv(key, value)
    runner = ScriptedRunner([_result(0, b"1" * 40 + b"\n")])

    GitRepositoryReader(repo, runner=runner).resolve_head_state()

    child_environment = runner.calls[0][1]
    assert not set(hostile).intersection(child_environment)
    assert set(child_environment).issubset(
        {
            "PATH",
            "LC_ALL",
            "LANG",
            "GIT_OPTIONAL_LOCKS",
            "GIT_CONFIG_NOSYSTEM",
            "GIT_CONFIG_GLOBAL",
            "GIT_TERMINAL_PROMPT",
            "GIT_PAGER",
            "PAGER",
            "NO_COLOR",
            "GIT_NO_LAZY_FETCH",
            "GIT_NO_REPLACE_OBJECTS",
        }
    )


def test_subprocess_runner_starts_git_in_an_independent_signal_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_run(argv: tuple[str, ...], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        captured.update(kwargs)
        return subprocess.CompletedProcess(argv, 0, b"git version 2.39.5\n", b"")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = SubprocessRunner().run(("git", "--version"), {"LC_ALL": "C"})

    assert result.returncode == 0
    assert captured["start_new_session"] is True


def test_subprocess_runner_terminates_the_process_group_on_cancellation() -> None:
    runner = SubprocessRunner(cancelled=lambda: True)

    with pytest.raises(GitReadError) as caught:
        runner.run(
            (sys.executable, "-c", "import time; time.sleep(30)"),
            {"PATH": "/usr/bin"},
        )

    assert caught.value.diagnostic.code.value == "CSV-INTERRUPT-001"


@pytest.mark.parametrize(
    "version",
    [
        b"git version 2.39\n",
        b"git version 2.39.3\n",
        b"git version 2.39.3 (Apple Git-145)\n",
        b"git version 2.43.0.windows.1\n",
        b"git version 10.1.vendor-build\n",
    ],
)
def test_git_version_accepts_numeric_minimum_with_single_line_vendor_suffix(
    tmp_path: Path, version: bytes
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    GitRepositoryReader(repo, runner=ScriptedRunner([_result(0, version)])).validate_git_version()


@pytest.mark.parametrize(
    "version",
    [
        b"git version 2.38.99 (Apple Git-999)\n",
        b"git version 2.x\n",
        b"git version 2.39beta\n",
        b"git version 2.39\r\n",
        b"git version 2.39.3\nextra\n",
        b"git version 2.39.3\x00vendor\n",
    ],
)
def test_git_version_rejects_old_malformed_or_multiline_protocol(
    tmp_path: Path, version: bytes
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    with pytest.raises(GitReadError) as caught:
        GitRepositoryReader(
            repo, runner=ScriptedRunner([_result(0, version)])
        ).validate_git_version()

    assert caught.value.diagnostic.code.value == "CSV-ENV-002"


def test_only_missing_valid_symbolic_branch_is_unborn(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    runner = ScriptedRunner(
        [
            _result(128, stderr=b"not used for classification"),
            _result(0, b"refs/heads/new-branch\n"),
            _result(0),
            _result(1),
        ]
    )

    state = GitRepositoryReader(repo, runner=runner).resolve_head_state()

    assert state == Unborn("refs/heads/new-branch")
    assert [call[0][5:] for call in runner.calls] == [
        ("rev-parse", "--verify", "HEAD^{commit}"),
        ("symbolic-ref", "-q", "HEAD"),
        ("check-ref-format", "refs/heads/new-branch"),
        ("show-ref", "--verify", "--quiet", "refs/heads/new-branch"),
    ]


def test_validated_repository_identity_rejects_path_replacement(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    displaced = tmp_path / "displaced-repo"
    runner = ScriptedRunner([_result(0, f"{repo}\n".encode())])
    reader = GitRepositoryReader(repo, runner=runner)

    assert reader.validate_repository_root() == repo
    repo.rename(displaced)
    repo.mkdir()

    assert not reader.repository_is_current()
    with pytest.raises(GitReadError) as caught:
        reader.resolve_head_state()
    assert caught.value.diagnostic.code.value == "CSV-REPO-001"


@pytest.mark.parametrize(
    "results",
    [
        [_result(0, b"abc\n")],
        [_result(128), _result(1)],
        [_result(128), _result(0, b"refs/heads/bad..name\n"), _result(1)],
        [
            _result(128),
            _result(0, b"refs/heads/existing\n"),
            _result(0),
            _result(0),
        ],
    ],
)
def test_invalid_or_non_unborn_head_is_fatal(tmp_path: Path, results: list[CommandResult]) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    with pytest.raises(GitReadError) as caught:
        GitRepositoryReader(repo, runner=ScriptedRunner(results)).resolve_head_state()

    assert caught.value.diagnostic.code.value == "CSV-REPO-002"


def test_enumerate_paths_strictly_decodes_nul_delimited_utf8_and_normalizes_nfc(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    runner = ScriptedRunner([_result(0, "src/cafe\u0301.py\0README\0".encode())])

    paths = GitRepositoryReader(repo, runner=runner).enumerate_paths()

    assert paths == (PurePosixPath("src/caf\u00e9.py"), PurePosixPath("README"))
    assert runner.calls[0][0][5:] == (
        "ls-files",
        "-z",
        "--cached",
        "--others",
        "--exclude-standard",
    )


def test_non_utf8_git_path_is_fatal_without_synthetic_path(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    runner = ScriptedRunner([_result(0, b"good.py\0bad-\xff.py\0")])

    with pytest.raises(UnrepresentableGitPathFatal) as caught:
        GitRepositoryReader(repo, runner=runner).enumerate_paths()

    value = caught.value.diagnostic
    assert value.code.value == "CSV-SOURCE-003"
    assert (value.domain, value.path, value.symbol, value.line) == (None, None, None, None)
    assert b"bad" not in str(caught.value).encode("utf-8")


def test_commit_blob_is_read_by_captured_object_identity(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    object_id = "a" * 40
    runner = ScriptedRunner([_result(0, b"content\n")])

    content = GitRepositoryReader(repo, runner=runner).read_blob_object(object_id)

    assert content == b"content\n"
    assert runner.calls[0][0][5:] == ("cat-file", "blob", object_id)


def test_index_inventory_preserves_mode_object_stage_and_deterministic_path_order(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    first_object = "a" * 40
    second_object = "b" * 40
    runner = ScriptedRunner(
        [
            _result(
                0,
                b"100755 "
                + second_object.encode("ascii")
                + b" 2\tsrc/z.py\0"
                + b"100644 "
                + first_object.encode("ascii")
                + b" 0\tsrc/a.py\0",
            )
        ]
    )

    entries = GitRepositoryReader(repo, runner=runner).enumerate_index_entries()

    assert entries == (
        GitIndexEntry(PurePosixPath("src/a.py"), first_object, "100644", 0),
        GitIndexEntry(PurePosixPath("src/z.py"), second_object, "100755", 2),
    )
    assert runner.calls[0][0][5:] == ("ls-files", "--stage", "-z", "--cached", "--")


@pytest.mark.parametrize(
    ("payload", "diagnostic_code"),
    (
        (b"10064x " + (b"a" * 40) + b" 0\tsrc/app.py\0", "CSV-INTERNAL-001"),
        (b"100644 bad-object 0\tsrc/app.py\0", "CSV-INTERNAL-001"),
        (b"100644 " + (b"a" * 40) + b" 4\tsrc/app.py\0", "CSV-INTERNAL-001"),
        (
            b"100644 " + (b"a" * 40) + b" 0\tsrc/bad-\xff.py\0",
            "CSV-SOURCE-003",
        ),
    ),
)
def test_index_inventory_rejects_malformed_protocol(
    tmp_path: Path,
    payload: bytes,
    diagnostic_code: str,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    with pytest.raises(GitReadError) as caught:
        GitRepositoryReader(
            repo,
            runner=ScriptedRunner([_result(0, payload)]),
        ).enumerate_index_entries()

    assert caught.value.diagnostic.code.value == diagnostic_code


def test_ref_namespace_expands_to_sorted_deduplicated_child_refs(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    runner = ScriptedRunner(
        [
            _result(
                0,
                b"refs/remotes/upstream/z\n"
                b"refs/remotes/upstream/main\n"
                b"refs/remotes/upstream/main\n",
            )
        ]
    )

    refs = GitRepositoryReader(repo, runner=runner).enumerate_ref_names("refs/remotes/upstream")

    assert refs == (
        "refs/remotes/upstream/main",
        "refs/remotes/upstream/z",
    )
    assert runner.calls[0][0][5:] == (
        "for-each-ref",
        "--format=%(refname)",
        "refs/remotes/upstream/",
    )


@pytest.mark.parametrize(
    "payload",
    (
        b"refs/remotes/other/main\n",
        b"refs/remotes/upstream/main",
        b"refs/remotes/upstream/bad-\xff\n",
    ),
)
def test_ref_namespace_rejects_malformed_or_out_of_namespace_protocol(
    tmp_path: Path,
    payload: bytes,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    with pytest.raises(GitReadError) as caught:
        GitRepositoryReader(
            repo,
            runner=ScriptedRunner([_result(0, payload)]),
        ).enumerate_ref_names("refs/remotes/upstream")

    assert caught.value.diagnostic.code.value == "CSV-DIFF-001"
