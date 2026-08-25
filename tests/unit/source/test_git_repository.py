from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath

import pytest

from code_structure_viz.source.git_repository import (
    CommandResult,
    Commit,
    GitReadError,
    GitRepositoryReader,
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
