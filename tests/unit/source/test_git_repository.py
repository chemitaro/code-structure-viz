import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath

import pytest

from code_structure_viz.source.git_repository import (
    CommandResult,
    Commit,
    GitIndexEntry,
    GitlinkComparisonProfile,
    GitPathIdentity,
    GitPathIdentityCollisionFatal,
    GitReadError,
    GitRepositoryReader,
    SubprocessRunner,
    Unborn,
    UnrepresentableGitPathFatal,
    _attribute_is_raw_safe,
    _git_blob_digest,
    _GitlinkTreeEntry,
    _parse_git_bool,
    _parse_git_config_records,
    _raw_modes_equal,
    parse_check_attr_z,
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
            "GIT_ATTR_NOSYSTEM",
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
        "GIT_ATTR_NOSYSTEM": "1",
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
            "GIT_ATTR_NOSYSTEM",
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
            ),
            _result(0, b"H src/z.py\0H src/a.py\0"),
        ]
    )

    entries = GitRepositoryReader(repo, runner=runner).enumerate_index_entries()

    assert entries == (
        GitIndexEntry(PurePosixPath("src/a.py"), first_object, "100644", 0),
        GitIndexEntry(PurePosixPath("src/z.py"), second_object, "100755", 2),
    )
    assert runner.calls[0][0][5:] == ("ls-files", "--stage", "-z", "--cached", "--")


def test_index_inventory_preserves_raw_spelling_and_skip_worktree_flag(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    object_id = "a" * 40
    runner = ScriptedRunner(
        [
            _result(0, b"100644 " + object_id.encode("ascii") + b" 0	cafe\xcc\x81.py\0"),
            _result(0, b"S cafe\xcc\x81.py\0"),
        ]
    )

    entries = GitRepositoryReader(repo, runner=runner).enumerate_index_entries()

    assert entries[0].path == PurePosixPath("café.py")
    assert entries[0].raw_text == "cafe\u0301.py"
    assert entries[0].skip_worktree is True
    assert [call[0][5:] for call in runner.calls] == [
        ("ls-files", "--stage", "-z", "--cached", "--"),
        ("ls-files", "-v", "-z", "--cached", "--"),
    ]


@pytest.mark.parametrize(
    "flags_payload",
    (
        b"X src/app.py\0",
        b"H src/app.py\0S src/app.py\0",
        b"M src/app.py\0S src/app.py\0",
    ),
)
def test_index_flag_protocol_rejects_malformed_or_duplicate_records(
    tmp_path: Path,
    flags_payload: bytes,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    object_id = "a" * 40
    runner = ScriptedRunner(
        [
            _result(0, b"100644 " + object_id.encode("ascii") + b" 0	src/app.py\0"),
            _result(0, flags_payload),
        ]
    )

    with pytest.raises(GitReadError) as caught:
        GitRepositoryReader(repo, runner=runner).enumerate_index_entries()

    assert caught.value.diagnostic.code.value == "CSV-INTERNAL-001"


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        ("true", True),
        ("YES", True),
        ("on", True),
        ("1", True),
        ("false", False),
        ("NO", False),
        ("off", False),
        ("0", False),
    ),
)
def test_git_bool_parser_accepts_only_supported_boolean_spellings(
    value: str,
    expected: bool,
) -> None:
    assert _parse_git_bool(value) is expected


@pytest.mark.parametrize("value", ("input", "maybe", "", "2"))
def test_git_bool_parser_rejects_malformed_or_enum_values(value: str) -> None:
    assert _parse_git_bool(value) is None


@pytest.mark.parametrize(
    "payload",
    (
        b"core.filemode\nfalse",
        b"core.filemode\nfalse\0malformed-record\0",
        b"core.filemode\nfalse\xff\0",
    ),
)
def test_git_config_null_parser_rejects_malformed_records(payload: bytes) -> None:
    with pytest.raises(ValueError):
        _parse_git_config_records(payload)


def test_gitlink_config_profile_accepts_explicit_safe_values(tmp_path: Path) -> None:
    location = tmp_path / "nested"
    git_dir = tmp_path / "git"
    location.mkdir()
    git_dir.mkdir()
    runner = ScriptedRunner(
        [
            _result(0, b"core.autocrlf\nfalse\0core.filemode\nfalse\0"),
            _result(1),
        ]
    )

    profile = GitRepositoryReader(location, runner=runner)._gitlink_config_profile(
        location,
        git_dir,
    )

    assert profile[1:] == (True, False, True)


@pytest.mark.parametrize(
    "payload",
    (
        b"core.autocrlf\ninput\0",
        b"core.autocrlf\nmaybe\0",
        b"core.eol\nlf\0",
        b"core.filemode\nmaybe\0",
        b"filter.sentinel\nclean helper\0",
        b"include.path\n/tmp/outside\0",
        b"core.filemode\nfalse\0core.filemode\ntrue\0",
    ),
)
def test_gitlink_config_profile_rejects_unsafe_or_malformed_values(
    tmp_path: Path,
    payload: bytes,
) -> None:
    location = tmp_path / "nested"
    git_dir = tmp_path / "git"
    location.mkdir()
    git_dir.mkdir()
    runner = ScriptedRunner([_result(0, payload), _result(1)])

    profile = GitRepositoryReader(location, runner=runner)._gitlink_config_profile(
        location,
        git_dir,
    )

    assert profile[1] is False


def test_check_attr_null_parser_accepts_strict_known_tuples() -> None:
    payload = b"README\0text\0unspecified\0README\0eol\0unspecified\0"

    assert parse_check_attr_z(payload, "README") == (
        ("README", "text", "unspecified"),
        ("README", "eol", "unspecified"),
    )


@pytest.mark.parametrize(
    "payload",
    (
        b"README\0text\0unspecified",
        b"README\0text\0",
        b"README\0text\0unspecified\0README\0",
        b"\0text\0set\0",
        b"README\0\0set\0",
        b"other\0text\0set\0",
        b"README\xff\0text\0set\0",
        b"README\0text\xff\0set\0",
    ),
)
def test_check_attr_null_parser_rejects_malformed_or_missing_tuples(
    payload: bytes,
) -> None:
    with pytest.raises(ValueError):
        parse_check_attr_z(payload, "README")


def test_unknown_check_attr_is_not_raw_safe() -> None:
    parsed = parse_check_attr_z(b"README\0unknown\0set\0", "README")

    assert parsed == (("README", "unknown", "set"),)
    assert _attribute_is_raw_safe(*parsed[0][1:]) is False


def test_gitlink_external_attributes_source_is_unsafe_without_running_git(
    tmp_path: Path,
) -> None:
    location = tmp_path / "nested"
    git_dir = tmp_path / "git"
    location.mkdir()
    (git_dir / "info").mkdir(parents=True)
    (git_dir / "info" / "attributes").write_text("README text\n", encoding="utf-8")
    runner = ScriptedRunner([])
    reader = GitRepositoryReader(location, runner=runner)
    identity = GitPathIdentity("README", PurePosixPath("README"))

    attributes = reader._gitlink_attributes_profile(location, git_dir, (identity,), ())

    assert attributes == ((), False)
    assert runner.calls == []


@pytest.mark.parametrize(
    ("attribute", "value", "expected"),
    (
        ("text", "unset", True),
        ("crlf", "unset", True),
        ("ident", "unset", True),
        ("filter", "unset", True),
        ("text", "unspecified", True),
        ("eol", "unspecified", True),
        ("working-tree-encoding", "unspecified", True),
        ("eol", "unset", False),
        ("text", "set", False),
        ("filter", "sentinel", False),
        ("unknown", "unspecified", False),
    ),
)
def test_gitlink_attribute_raw_safety_is_closed_world(
    attribute: str,
    value: str,
    expected: bool,
) -> None:
    assert _attribute_is_raw_safe(attribute, value) is expected


def test_gitlink_unsafe_profile_is_rejected_before_raw_reads(tmp_path: Path) -> None:
    reader = GitRepositoryReader(tmp_path, runner=ScriptedRunner([]))
    profile = GitlinkComparisonProfile("config", "attributes", "flags", False)

    with pytest.raises(GitReadError) as caught:
        reader._gitlink_worktree_differs(tmp_path, (), "sha1", profile)

    assert caught.value.diagnostic.code.value == "CSV-DIFF-003"


@pytest.mark.parametrize(
    "entry",
    (
        GitIndexEntry(PurePosixPath("README"), "a" * 40, "100644", 1),
        GitIndexEntry(
            PurePosixPath("README"),
            "a" * 40,
            "100644",
            0,
            skip_worktree=True,
            index_flag="S",
        ),
        GitIndexEntry(
            PurePosixPath("README"),
            "a" * 40,
            "100644",
            0,
            assume_unchanged=True,
            index_flag="h",
        ),
    ),
)
def test_gitlink_profile_rejects_stage_and_index_identity_flags(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    entry: GitIndexEntry,
) -> None:
    reader = GitRepositoryReader(tmp_path, runner=ScriptedRunner([]))
    monkeypatch.setattr(
        reader,
        "_gitlink_config_profile",
        lambda *_arguments: ((), True, True, True),
    )
    monkeypatch.setattr(
        reader,
        "_gitlink_attributes_profile",
        lambda *_arguments: ((), True),
    )

    with pytest.raises(GitReadError) as caught:
        reader._gitlink_comparison_profile(tmp_path, tmp_path, (), (entry,), ())

    assert caught.value.diagnostic.code.value == "CSV-DIFF-003"


def test_gitlink_profile_rejects_other_index_markers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    identity = GitPathIdentity("README", PurePosixPath("README"))
    entry = GitIndexEntry(identity.path, "a" * 40, "100644", 0, identity.raw_text, index_flag="K")
    reader = GitRepositoryReader(tmp_path, runner=ScriptedRunner([]))
    monkeypatch.setattr(
        reader,
        "_gitlink_config_profile",
        lambda *_arguments: ((), True, True, True),
    )
    monkeypatch.setattr(
        reader,
        "_gitlink_attributes_profile",
        lambda *_arguments: ((), True),
    )

    with pytest.raises(GitReadError) as caught:
        reader._gitlink_comparison_profile(tmp_path, tmp_path, (), (entry,), ())

    assert caught.value.diagnostic.code.value == "CSV-DIFF-003"


def test_gitlink_profile_rejects_symlink_mode_when_core_symlinks_is_false(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    identity = GitPathIdentity("README", PurePosixPath("README"))
    entry = GitIndexEntry(identity.path, "a" * 40, "120000", 0, identity.raw_text)
    tree = (_GitlinkTreeEntry(identity, "a" * 40, "120000", "blob"),)
    reader = GitRepositoryReader(tmp_path, runner=ScriptedRunner([]))
    monkeypatch.setattr(
        reader,
        "_gitlink_config_profile",
        lambda *_arguments: ((), True, True, False),
    )
    monkeypatch.setattr(
        reader,
        "_gitlink_attributes_profile",
        lambda *_arguments: ((), True),
    )

    with pytest.raises(GitReadError) as caught:
        reader._gitlink_comparison_profile(tmp_path, tmp_path, tree, (entry,), ())

    assert caught.value.diagnostic.code.value == "CSV-DIFF-003"


def test_gitlink_filemode_false_ignores_only_regular_exec_bit_and_type_changes(
    tmp_path: Path,
) -> None:
    nested = tmp_path / "nested"
    nested.mkdir()
    path = nested / "README"
    content = b"payload"
    path.write_bytes(content)
    path.chmod(0o755)
    entry = GitIndexEntry(
        PurePosixPath("README"),
        _git_blob_digest(content, "sha1"),
        "100644",
        0,
    )
    profile = GitlinkComparisonProfile("config", "attributes", "flags", True, False)
    reader = GitRepositoryReader(tmp_path, runner=ScriptedRunner([]))

    dirty, _digest = reader._gitlink_worktree_differs(nested, (entry,), "sha1", profile)
    assert dirty is False
    assert _raw_modes_equal("100644", "100755", False) is True
    assert _raw_modes_equal("100644", "120000", False) is False

    path.unlink()
    path.symlink_to("payload")
    dirty, _digest = reader._gitlink_worktree_differs(nested, (entry,), "sha1", profile)
    assert dirty is True


def test_gitlink_profile_digest_is_deterministic_and_detects_drift() -> None:
    first = GitlinkComparisonProfile("config", "attributes", "flags", True, False)
    same = GitlinkComparisonProfile("config", "attributes", "flags", True, False)
    changed = GitlinkComparisonProfile("changed", "attributes", "flags", True, False)
    changed_mode = GitlinkComparisonProfile("config", "attributes", "flags", True, True)

    assert first.digest == same.digest
    assert first.digest != changed.digest
    assert first.digest != changed_mode.digest


def test_gitlink_profile_commands_are_bounded_metadata_only(tmp_path: Path) -> None:
    location = tmp_path / "nested"
    git_dir = tmp_path / "git"
    location.mkdir()
    git_dir.mkdir()
    identity = GitPathIdentity("README", PurePosixPath("README"))
    runner = ScriptedRunner([_result(1), _result(1), _result(0)])
    reader = GitRepositoryReader(location, runner=runner)

    reader._gitlink_config_profile(location, git_dir)
    reader._gitlink_attributes_profile(location, git_dir, (identity,), ())

    commands = [call[0] for call in runner.calls]
    assert all("status" not in command for command in commands)
    assert all("diff" not in command for command in commands)
    assert all("hash-object" not in command for command in commands)
    assert all("--path" not in command for command in commands)
    assert all("--no-includes" in command for command in commands[:2])
    assert "check-attr" in commands[2]


def test_commit_tree_rejects_distinct_raw_spellings_with_one_nfc_identity(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    object_id = "a" * 40
    payload = (
        b"100644 blob "
        + object_id.encode("ascii")
        + b" 1\tdocs/caf\xc3\xa9.txt\0"
        + b"100644 blob "
        + object_id.encode("ascii")
        + b" 1\tdocs/cafe\xcc\x81.txt\0"
    )
    runner = ScriptedRunner([_result(0, payload)])

    with pytest.raises(GitPathIdentityCollisionFatal) as caught:
        GitRepositoryReader(repo, runner=runner).enumerate_commit_tree(object_id)

    assert caught.value.diagnostic.code.value == "CSV-DIFF-003"


@pytest.mark.parametrize(
    ("raw", "canonical"),
    (
        ("src/other.py", PurePosixPath("src/app.py")),
        ("src/cafe\u0301.py", PurePosixPath("src/cafe\u0301.py")),
    ),
)
def test_git_path_identity_rejects_invalid_raw_canonical_pair(
    raw: str,
    canonical: PurePosixPath,
) -> None:
    with pytest.raises(ValueError):
        GitPathIdentity(raw, canonical)


@pytest.mark.parametrize("layout", ("missing", "uninitialized", "external-pointer"))
def test_gitlink_state_requires_a_safe_initialized_nested_repository(
    tmp_path: Path,
    layout: str,
) -> None:
    repo = tmp_path / "repo"
    nested = repo / "vendor" / "component"
    nested.parent.mkdir(parents=True)
    repo.mkdir(exist_ok=True)
    nested.mkdir()
    if layout == "uninitialized":
        (nested / "README").write_text("not a repository\n", encoding="utf-8")
    elif layout == "external-pointer":
        (nested / ".git").write_text("gitdir: /tmp/not-the-superproject\n", encoding="utf-8")

    entry = GitIndexEntry(
        PurePosixPath("vendor/component"),
        "a" * 40,
        "160000",
        0,
    )
    reader = GitRepositoryReader(repo, runner=ScriptedRunner([]))

    with pytest.raises(GitReadError) as caught:
        reader.enumerate_gitlink_states((entry,))

    assert caught.value.diagnostic.code.value == "CSV-DIFF-003"


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
