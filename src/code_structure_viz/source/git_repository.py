from __future__ import annotations

import hashlib
import os
import re
import selectors
import stat
import subprocess
import unicodedata
from collections.abc import Callable, Iterable, Mapping
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import BinaryIO, Final, Protocol, cast

from code_structure_viz.core.diagnostics import Diagnostic, DiagnosticCode, diagnostic
from code_structure_viz.core.path_safety import has_symlink_component
from code_structure_viz.semantic.canonical_json import encode_canonical_json

_OBJECT_ID: Final[re.Pattern[bytes]] = re.compile(rb"(?:[0-9A-Fa-f]{40}|[0-9A-Fa-f]{64})\n")
_GIT_VERSION_PREFIX: Final[re.Pattern[bytes]] = re.compile(rb"git version ([0-9]+)\.([0-9]+)")
_FIXED_ENV: Final[dict[str, str]] = {
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
    "GIT_NO_LAZY_FETCH": "1",
    "GIT_NO_REPLACE_OBJECTS": "1",
}
_MAX_GITLINK_METADATA_BYTES: Final[int] = 64 * 1024
_MAX_GITLINK_FILE_BYTES: Final[int] = 64 * 1024 * 1024
_MAX_IGNORE_AUTHORITY_DIRECTORIES: Final[int] = 65536
_MAX_IGNORE_AUTHORITY_FILES: Final[int] = 8192
_GITLINK_PROFILE_SCHEMA: Final = "code-structure-viz.gitlink-comparison-profile/v1"
_IGNORE_PROFILE_SCHEMA: Final = "code-structure-viz.ignore-authority-profile/v1"
_UNTRACKED_OBSERVATION_SCHEMA: Final = "code-structure-viz.untracked-observation/v1"
_IGNORE_CONFIG_PATTERN: Final = r"^(core\.(excludesfile|ignorecase)|include.*)$"
_IGNORE_CASE_CONFIG_PATTERN: Final = r"^core\.ignorecase$"
_GITLINK_CONFIG_PATTERN: Final = (
    r"^(core\.(autocrlf|attributesfile|eol|filemode|symlinks)|"
    r"filter\..*|diff\..*|include.*)$"
)
_GITLINK_ATTRIBUTE_NAMES: Final[frozenset[str]] = frozenset(
    {"text", "crlf", "eol", "ident", "working-tree-encoding", "filter"}
)


@dataclass(frozen=True, slots=True)
class CommandResult:
    returncode: int
    stdout: bytes
    stderr: bytes


class CommandRunner(Protocol):
    def run(self, argv: tuple[str, ...], env: Mapping[str, str]) -> CommandResult: ...


class GitReadError(RuntimeError):
    def __init__(self, value: Diagnostic) -> None:
        self.diagnostic = value
        super().__init__(value.message)


class GitInterruptedError(GitReadError):
    """Raised when a Git child is terminated by the caller's cancellation signal."""


class SubprocessRunner:
    def __init__(
        self,
        *,
        cancelled: Callable[[], bool] | None = None,
        max_output_bytes: int = 64 * 1024 * 1024,
    ) -> None:
        self._cancelled = cancelled
        self._max_output_bytes = max_output_bytes

    def run(self, argv: tuple[str, ...], env: Mapping[str, str]) -> CommandResult:
        if self._cancelled is None:
            return self._run_without_cancellation(argv, env)
        return self._run_with_cancellation(argv, env)

    @staticmethod
    def _run_without_cancellation(argv: tuple[str, ...], env: Mapping[str, str]) -> CommandResult:
        try:
            completed = subprocess.run(
                argv,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                check=False,
                env=env,
                shell=False,
                start_new_session=True,
            )
        except OSError:
            return CommandResult(127, b"", b"")
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)

    def _run_with_cancellation(
        self, argv: tuple[str, ...], env: Mapping[str, str]
    ) -> CommandResult:
        try:
            process = subprocess.Popen(
                argv,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                shell=False,
                start_new_session=True,
            )
        except OSError:
            return CommandResult(127, b"", b"")

        assert process.stdout is not None
        assert process.stderr is not None
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ, "stdout")
        selector.register(process.stderr, selectors.EVENT_READ, "stderr")
        chunks: dict[str, list[bytes]] = {"stdout": [], "stderr": []}
        sizes = {"stdout": 0, "stderr": 0}
        try:
            while selector.get_map():
                if self._cancelled is not None and self._cancelled():
                    _terminate_process_group(process)
                    raise GitInterruptedError(diagnostic(DiagnosticCode.INTERRUPTED))
                for key, _events in selector.select(timeout=0.05):
                    stream = cast(BinaryIO, key.fileobj)
                    chunk = stream.read(64 * 1024)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        stream.close()
                        continue
                    name = str(key.data)
                    sizes[name] += len(chunk)
                    if sizes[name] > self._max_output_bytes:
                        _terminate_process_group(process)
                        return CommandResult(125, b"", b"")
                    chunks[name].append(chunk)
            returncode = process.wait()
            return CommandResult(
                returncode,
                b"".join(chunks["stdout"]),
                b"".join(chunks["stderr"]),
            )
        finally:
            selector.close()
            if process.poll() is None:
                _terminate_process_group(process)
            with suppress(OSError):
                process.wait(timeout=1)


def _terminate_process_group(process: subprocess.Popen[bytes]) -> None:
    try:
        os.killpg(process.pid, 15)
    except OSError:
        with suppress(OSError):
            process.terminate()
    try:
        process.wait(timeout=0.2)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, 9)
        except OSError:
            with suppress(OSError):
                process.kill()


@dataclass(frozen=True, slots=True)
class Commit:
    object_id: str


@dataclass(frozen=True, slots=True)
class Unborn:
    branch_ref: str


type HeadState = Commit | Unborn


@dataclass(frozen=True, slots=True)
class GitPathIdentity:
    """The raw Git UTF-8 spelling and its safe NFC logical path."""

    raw_text: str
    canonical_path: PurePosixPath

    @property
    def path(self) -> PurePosixPath:
        return self.canonical_path

    def __post_init__(self) -> None:
        try:
            self.raw_text.encode("utf-8", errors="strict")
        except UnicodeEncodeError as error:
            raise ValueError("Git path is not valid UTF-8") from error
        if not _is_safe_relative_git_path(self.raw_text):
            raise ValueError("Git path is not safe")
        canonical = self.canonical_path.as_posix()
        if (
            unicodedata.normalize("NFC", self.raw_text) != canonical
            or unicodedata.normalize("NFC", canonical) != canonical
            or not _is_safe_relative_git_path(canonical)
        ):
            raise ValueError("Git path identity is not canonical")


@dataclass(frozen=True, slots=True)
class CommitTreeEntry:
    path: PurePosixPath
    object_id: str
    mode: str
    kind: str
    raw_text: str | None = None

    def __post_init__(self) -> None:
        if self.raw_text is None:
            object.__setattr__(self, "raw_text", self.path.as_posix())
        assert self.raw_text is not None
        GitPathIdentity(self.raw_text, self.path)

    @property
    def identity(self) -> GitPathIdentity:
        assert self.raw_text is not None
        return GitPathIdentity(self.raw_text, self.path)


@dataclass(frozen=True, slots=True)
class EnumeratedPath:
    raw_text: str
    normalized: PurePosixPath

    def __post_init__(self) -> None:
        GitPathIdentity(self.raw_text, self.normalized)

    @property
    def identity(self) -> GitPathIdentity:
        return GitPathIdentity(self.raw_text, self.normalized)


@dataclass(frozen=True, slots=True)
class GitIndexEntry:
    path: PurePosixPath
    object_id: str
    mode: str
    stage: int
    raw_text: str | None = None
    skip_worktree: bool = False
    assume_unchanged: bool = False
    index_flag: str = "H"

    def __post_init__(self) -> None:
        if self.raw_text is None:
            object.__setattr__(self, "raw_text", self.path.as_posix())
        assert self.raw_text is not None
        GitPathIdentity(self.raw_text, self.path)

    @property
    def identity(self) -> GitPathIdentity:
        assert self.raw_text is not None
        return GitPathIdentity(self.raw_text, self.path)


@dataclass(frozen=True, slots=True)
class GitlinkWorktreeState:
    identity: GitPathIdentity
    index_object_id: str
    current_head: str | None
    initialized: bool
    tracked_content_dirty: bool
    untracked_content_dirty: bool
    binding_identity: str | None = None
    comparison_profile_digest: str = ""
    tracked_worktree_digest: str = ""
    untracked_paths: tuple[GitPathIdentity, ...] = ()

    def __post_init__(self) -> None:
        if not self.initialized or self.current_head is None or not self.binding_identity:
            raise ValueError("gitlink observations must be initialized and complete")

    @property
    def dirty(self) -> bool:
        return (
            (self.current_head is not None and self.current_head != self.index_object_id)
            or self.tracked_content_dirty
            or self.untracked_content_dirty
        )

    @property
    def materialization_state(self) -> str:
        return "present"


@dataclass(frozen=True, slots=True)
class IgnoreAuthorityProfile:
    """Closed-world evidence for the ignore sources used by Git enumeration."""

    config_keys_digest: str
    gitignore_digest: str | None
    info_exclude_digest: str | None
    allowed: bool = True
    common_git_dir_identity: str = ""
    core_ignore_case: bool = False
    common_git_dir: Path | None = None

    @property
    def digest(self) -> str:
        value = {
            "schema": _IGNORE_PROFILE_SCHEMA,
            "config_keys_digest": self.config_keys_digest,
            "gitignore_digest": self.gitignore_digest,
            "info_exclude_digest": self.info_exclude_digest,
            "allowed": self.allowed,
            "common_git_dir_identity": self.common_git_dir_identity,
            "core_ignore_case": self.core_ignore_case,
        }
        return hashlib.sha256(encode_canonical_json(value)).hexdigest()


@dataclass(frozen=True, slots=True)
class UntrackedObservation:
    """The deterministic untracked result bound to one ignore authority profile."""

    paths: tuple[GitPathIdentity, ...]
    authority: IgnoreAuthorityProfile

    def __post_init__(self) -> None:
        ordered = tuple(
            sorted(
                self.paths,
                key=lambda item: (
                    item.canonical_path.as_posix().encode("utf-8"),
                    item.raw_text.encode("utf-8"),
                ),
            )
        )
        if ordered != self.paths:
            object.__setattr__(self, "paths", ordered)

    @property
    def authority_digest(self) -> str:
        return self.authority.digest

    @property
    def digest(self) -> str:
        value = {
            "schema": _UNTRACKED_OBSERVATION_SCHEMA,
            "authority_digest": self.authority_digest,
            "paths": [item.raw_text for item in self.paths],
        }
        return hashlib.sha256(encode_canonical_json(value)).hexdigest()

    @property
    def observation_digest(self) -> str:
        return self.digest


@dataclass(frozen=True, slots=True)
class GitlinkComparisonProfile:
    """Closed-world evidence needed before raw nested worktree comparison."""

    config_digest: str
    attributes_digest: str
    index_flags_digest: str
    raw_comparison_allowed: bool
    core_filemode: bool = True
    ignore_digest: str = ""

    @property
    def digest(self) -> str:
        value = {
            "schema": _GITLINK_PROFILE_SCHEMA,
            "config_digest": self.config_digest,
            "attributes_digest": self.attributes_digest,
            "index_flags_digest": self.index_flags_digest,
            "raw_comparison_allowed": self.raw_comparison_allowed,
            "core_filemode": self.core_filemode,
            "ignore_digest": self.ignore_digest,
        }
        return hashlib.sha256(encode_canonical_json(value)).hexdigest()


@dataclass(frozen=True, slots=True)
class _GitlinkTreeEntry:
    identity: GitPathIdentity
    object_id: str
    mode: str
    kind: str


@dataclass(frozen=True, slots=True)
class _GitIndexFlag:
    marker: str
    skip_worktree: bool
    assume_unchanged: bool


class UnrepresentableGitPathFatal(GitReadError):
    pass


class GitPathIdentityCollisionFatal(GitReadError):
    pass


def _safe_environment() -> dict[str, str]:
    environment = dict(_FIXED_ENV)
    executable_path = os.environ.get("PATH")
    if executable_path is not None:
        environment["PATH"] = executable_path
    return environment


def _fatal(code: DiagnosticCode) -> GitReadError:
    return GitReadError(diagnostic(code))


def _path_protocol_fatal() -> GitReadError:
    return _fatal(DiagnosticCode.INTERNAL_INVARIANT)


class GitRepositoryReader:
    def __init__(
        self,
        repository: Path,
        *,
        runner: CommandRunner | None = None,
        cancelled: Callable[[], bool] | None = None,
    ) -> None:
        self.repository = repository
        self._cancelled = cancelled or (lambda: False)
        self._runner = runner or SubprocessRunner(cancelled=self._cancelled)
        self._environment = _safe_environment()
        self._validated_identity: tuple[int, int] | None = None
        self._pending_untracked_observation: UntrackedObservation | None = None
        self._last_untracked_observation: UntrackedObservation | None = None

    def _git(self, *arguments: str) -> CommandResult:
        if self._cancelled():
            raise GitInterruptedError(diagnostic(DiagnosticCode.INTERRUPTED))
        if self._validated_identity is not None and not self.repository_is_current():
            raise _fatal(DiagnosticCode.REPO_ROOT)
        argv = (
            "git",
            "-C",
            str(self.repository),
            "-c",
            "core.fsmonitor=false",
            *arguments,
        )
        result = self._runner.run(argv, self._environment)
        if self._cancelled():
            raise GitInterruptedError(diagnostic(DiagnosticCode.INTERRUPTED))
        return result

    def validate_git_version(self) -> None:
        if self._cancelled():
            raise GitInterruptedError(diagnostic(DiagnosticCode.INTERRUPTED))
        result = self._runner.run(("git", "--version"), self._environment)
        if self._cancelled():
            raise GitInterruptedError(diagnostic(DiagnosticCode.INTERRUPTED))
        if (
            result.returncode != 0
            or not result.stdout.endswith(b"\n")
            or result.stdout.count(b"\n") != 1
        ):
            raise _fatal(DiagnosticCode.ENV_GIT)
        line = result.stdout[:-1]
        match = _GIT_VERSION_PREFIX.match(line)
        suffix = line[match.end() :] if match is not None else b""
        valid_suffix = not suffix or (
            len(suffix) > 1
            and suffix[:1] in {b".", b" "}
            and all(0x20 <= byte <= 0x7E for byte in suffix)
        )
        if match is None or (int(match[1]), int(match[2])) < (2, 39):
            raise _fatal(DiagnosticCode.ENV_GIT)
        if not valid_suffix:
            raise _fatal(DiagnosticCode.ENV_GIT)

    def validate_repository_root(self) -> Path:
        try:
            if has_symlink_component(self.repository) or not self.repository.is_dir():
                raise _fatal(DiagnosticCode.REPO_ROOT)
            expected = self.repository.resolve(strict=True)
        except OSError as error:
            raise _fatal(DiagnosticCode.REPO_ROOT) from error
        result = self._git("rev-parse", "--show-toplevel")
        if result.returncode != 0:
            raise _fatal(DiagnosticCode.REPO_ROOT)
        try:
            if not result.stdout.endswith(b"\n") or result.stdout.count(b"\n") != 1:
                raise _fatal(DiagnosticCode.REPO_ROOT)
            decoded = result.stdout[:-1].decode("utf-8", errors="strict")
            actual = Path(decoded).resolve(strict=True)
        except (OSError, UnicodeDecodeError) as error:
            raise _fatal(DiagnosticCode.REPO_ROOT) from error
        if actual != expected:
            raise _fatal(DiagnosticCode.REPO_ROOT)
        try:
            identity = expected.stat(follow_symlinks=False)
        except OSError as error:
            raise _fatal(DiagnosticCode.REPO_ROOT) from error
        self._validated_identity = (identity.st_dev, identity.st_ino)
        return expected

    @property
    def repository_identity(self) -> tuple[int, int] | None:
        return self._validated_identity

    def repository_is_current(self) -> bool:
        identity = self._validated_identity
        if identity is None or has_symlink_component(self.repository):
            return identity is None
        try:
            current = self.repository.stat(follow_symlinks=False)
        except OSError:
            return False
        return (current.st_dev, current.st_ino) == identity

    @property
    def last_untracked_observation(self) -> UntrackedObservation | None:
        return self._last_untracked_observation

    def resolve_head_state(self) -> HeadState:
        resolved = self._git("rev-parse", "--verify", "HEAD^{commit}")
        if resolved.returncode == 0:
            if _OBJECT_ID.fullmatch(resolved.stdout) is None:
                raise _fatal(DiagnosticCode.REPO_HEAD)
            return Commit(resolved.stdout[:-1].decode("ascii").lower())

        symbolic = self._git("symbolic-ref", "-q", "HEAD")
        if symbolic.returncode != 0:
            raise _fatal(DiagnosticCode.REPO_HEAD)
        raw_ref = symbolic.stdout
        if (
            not raw_ref.endswith(b"\n")
            or raw_ref.count(b"\n") != 1
            or b"\0" in raw_ref
            or len(raw_ref) == 1
        ):
            raise _fatal(DiagnosticCode.REPO_HEAD)
        raw_ref = raw_ref[:-1]
        try:
            branch_ref = raw_ref.decode("utf-8", errors="strict")
            round_trip = os.fsencode(branch_ref)
        except (UnicodeDecodeError, UnicodeEncodeError) as error:
            raise _fatal(DiagnosticCode.REPO_HEAD) from error
        if round_trip != raw_ref or not branch_ref.startswith("refs/heads/"):
            raise _fatal(DiagnosticCode.REPO_HEAD)

        checked = self._git("check-ref-format", branch_ref)
        if checked.returncode != 0 or checked.stdout:
            raise _fatal(DiagnosticCode.REPO_HEAD)
        shown = self._git("show-ref", "--verify", "--quiet", branch_ref)
        if shown.returncode != 1 or shown.stdout:
            raise _fatal(DiagnosticCode.REPO_HEAD)
        return Unborn(branch_ref)

    def _observe_untracked(
        self,
        *,
        location: Path | None = None,
        git_dir: Path | None = None,
    ) -> UntrackedObservation:
        nested = location is not None
        observed_location = self.repository if location is None else location
        observed_git_dir = git_dir
        if observed_git_dir is None:
            observed_git_dir = self._repository_git_dir()
        authority_before = self._ignore_authority_profile(
            observed_location,
            observed_git_dir,
        )
        ignore_case = "true" if authority_before.core_ignore_case else "false"
        linked_worktree = authority_before.common_git_dir not in {
            None,
            observed_git_dir,
        }
        arguments: tuple[str, ...] = (
            "-c",
            f"core.ignoreCase={ignore_case}",
            "ls-files",
            "-z",
            "--others",
            "--exclude-standard",
        )
        if linked_worktree and authority_before.info_exclude_digest is not None:
            if authority_before.common_git_dir is None:
                raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
            arguments += (
                "--exclude-from",
                str(authority_before.common_git_dir / "info" / "exclude"),
            )
        arguments += ("--",)
        result = (
            self._git(*arguments)
            if not nested
            else self._git_at(observed_location, *arguments, git_dir=observed_git_dir)
        )
        if result.returncode != 0 or result.stderr:
            raise _path_protocol_fatal()
        untracked = _decode_identity_list(result.stdout)
        authority_after = self._ignore_authority_profile(
            observed_location,
            observed_git_dir,
        )
        if authority_before != authority_after:
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
        return UntrackedObservation(untracked, authority_before)

    def _ignore_authority_profile(
        self,
        location: Path,
        git_dir: Path,
    ) -> IgnoreAuthorityProfile:
        config_records = self._ignore_config_records(location, git_dir)
        if any(
            key == "core.excludesfile" or key.startswith("include")
            for _scope, key in config_records
        ):
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
        core_ignore_case = self._ignore_case_config_value(location, git_dir)
        common_git_dir, common_git_dir_identity = self._resolve_git_common_dir(
            location,
            git_dir,
        )
        try:
            info = common_git_dir / "info"
            if has_symlink_component(info):
                raise OSError("Git info directory is unsafe")
            try:
                info_stat = info.lstat()
            except FileNotFoundError:
                info_stat = None
            if info_stat is not None and (
                stat.S_ISLNK(info_stat.st_mode) or not stat.S_ISDIR(info_stat.st_mode)
            ):
                raise OSError("Git info directory is unsafe")
            if common_git_dir != git_dir:
                worktree_info = git_dir / "info"
                try:
                    worktree_info_stat = worktree_info.lstat()
                except FileNotFoundError:
                    worktree_info_stat = None
                if worktree_info_stat is not None and (
                    stat.S_ISLNK(worktree_info_stat.st_mode)
                    or not stat.S_ISDIR(worktree_info_stat.st_mode)
                ):
                    raise OSError("per-worktree Git info directory is unsafe")
                if worktree_info_stat is not None:
                    worktree_exclude = worktree_info / "exclude"
                    try:
                        worktree_exclude_stat = worktree_exclude.lstat()
                    except FileNotFoundError:
                        worktree_exclude_stat = None
                    if worktree_exclude_stat is not None:
                        raise OSError("per-worktree Git exclude is unsupported")
            gitignore_digest = _ignore_authority_gitignore_digest(location, git_dir)
            info_exclude_digest = _ignore_authority_file_digest(info / "exclude")
        except OSError as error:
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE) from error
        return IgnoreAuthorityProfile(
            config_keys_digest=_ignore_config_digest(config_records),
            gitignore_digest=gitignore_digest,
            info_exclude_digest=info_exclude_digest,
            common_git_dir_identity=common_git_dir_identity,
            core_ignore_case=core_ignore_case,
            common_git_dir=common_git_dir,
        )

    def _ignore_case_config_value(self, location: Path, git_dir: Path) -> bool:
        try:
            worktree_config_present = _is_regular_file(git_dir / "config.worktree")
            linked_worktree = _is_linked_worktree_git_dir(git_dir)
        except OSError as error:
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE) from error
        values: dict[str, bool | None] = {}
        for scope in ("local", "worktree"):
            if scope == "worktree" and linked_worktree and not worktree_config_present:
                continue
            arguments = (
                "config",
                "--null",
                "--no-includes",
                f"--{scope}",
                "--get-regexp",
                _IGNORE_CASE_CONFIG_PATTERN,
            )
            result = (
                self._git(*arguments)
                if location == self.repository
                else self._git_at(location, *arguments, git_dir=git_dir)
            )
            if result.returncode not in {0, 1} or result.stderr:
                raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
            try:
                value = _parse_git_bool_records(result.stdout, "core.ignorecase")
            except ValueError as error:
                raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE) from error
            values[scope] = value
        selected = values.get("worktree") if worktree_config_present else None
        if selected is None:
            selected = values.get("local")
        return bool(selected) if selected is not None else False

    def _resolve_git_common_dir(
        self,
        location: Path,
        git_dir: Path,
    ) -> tuple[Path, str]:
        try:
            git_identity_before = self._binding_identity(git_dir)
        except GitReadError:
            raise
        result = (
            self._git("rev-parse", "--path-format=absolute", "--git-common-dir")
            if location == self.repository
            else self._git_at(
                location,
                "rev-parse",
                "--path-format=absolute",
                "--git-common-dir",
                git_dir=git_dir,
            )
        )
        if result.returncode != 0 or result.stderr:
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
        try:
            common_path = _parse_git_common_dir(result.stdout)
            if has_symlink_component(common_path):
                raise OSError("common Git directory is unsafe")
            common_resolved = common_path.resolve(strict=True)
            if has_symlink_component(common_resolved):
                raise OSError("common Git directory is unsafe")
            if not common_resolved.is_dir():
                raise OSError("common Git directory is not a directory")
            common_identity = self._binding_identity(common_resolved)
            git_resolved = git_dir.resolve(strict=True)
            if git_resolved != common_resolved and not _is_relative_to(
                git_resolved,
                common_resolved / "worktrees",
            ):
                raise OSError("per-worktree Git directory is outside common directory")
            git_identity_after = self._binding_identity(git_dir)
            common_identity_after = self._binding_identity(common_resolved)
        except (OSError, RuntimeError, ValueError) as error:
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE) from error
        if git_identity_before != git_identity_after or common_identity != common_identity_after:
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
        return common_resolved, common_identity

    def _ignore_config_records(
        self,
        location: Path,
        git_dir: Path,
    ) -> tuple[tuple[str, str], ...]:
        records: list[tuple[str, str]] = []
        try:
            worktree_config_present = _is_regular_file(git_dir / "config.worktree")
            linked_worktree = _is_linked_worktree_git_dir(git_dir)
        except OSError as error:
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE) from error
        for scope in ("local", "worktree"):
            if scope == "worktree" and linked_worktree and not worktree_config_present:
                continue
            arguments = (
                "config",
                "--null",
                "--no-includes",
                "--name-only",
                f"--{scope}",
                "--get-regexp",
                _IGNORE_CONFIG_PATTERN,
            )
            result = (
                self._git(*arguments)
                if location == self.repository
                else self._git_at(location, *arguments, git_dir=git_dir)
            )
            if result.returncode not in {0, 1} or result.stderr:
                raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
            if result.returncode == 0 or result.stdout:
                try:
                    keys = _parse_git_config_name_only(result.stdout)
                except ValueError as error:
                    raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE) from error
                if scope == "local" or worktree_config_present:
                    records.extend((scope, key) for key in keys)
        return tuple(sorted(records))

    def _repository_git_dir(self) -> Path:
        metadata = self.repository / ".git"
        try:
            metadata_stat = metadata.lstat()
        except OSError as error:
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE) from error
        if stat.S_ISLNK(metadata_stat.st_mode):
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
        if stat.S_ISDIR(metadata_stat.st_mode):
            git_dir = metadata
        elif stat.S_ISREG(metadata_stat.st_mode):
            pointer = self._read_gitlink_pointer(metadata)
            pointer_path = Path(pointer)
            git_dir = pointer_path if pointer_path.is_absolute() else metadata.parent / pointer_path
        else:
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
        try:
            resolved = git_dir.resolve(strict=True)
        except (OSError, RuntimeError) as error:
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE) from error
        if has_symlink_component(git_dir) or has_symlink_component(resolved):
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
        if not resolved.is_dir():
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
        return resolved

    def enumerate_path_entries(self) -> tuple[EnumeratedPath, ...]:
        observation = self._observe_untracked()
        self._pending_untracked_observation = observation
        self._last_untracked_observation = observation
        # Reuse the already profiled untracked observation.  A second
        # ``--others --exclude-standard`` query would reintroduce an ambient
        # ignore authority between the profile and the inventory we freeze.
        result = self._git("ls-files", "-z", "--cached", "--")
        if result.returncode != 0:
            raise _path_protocol_fatal()
        raw_entries = result.stdout.split(b"\0")
        if raw_entries and raw_entries[-1] == b"":
            raw_entries.pop()
        if any(not entry for entry in raw_entries):
            raise _path_protocol_fatal()
        raw_entries.extend(
            item.raw_text.encode("utf-8")
            for item in observation.paths
            if item.raw_text.encode("utf-8") not in raw_entries
        )

        entries: list[EnumeratedPath] = []
        seen_raw: set[bytes] = set()
        for raw in raw_entries:
            if raw in seen_raw:
                continue
            seen_raw.add(raw)
            try:
                decoded = raw.decode("utf-8", errors="strict")
            except UnicodeDecodeError as error:
                value = diagnostic(DiagnosticCode.SOURCE_NON_UTF8)
                raise UnrepresentableGitPathFatal(value) from error
            normalized = unicodedata.normalize("NFC", decoded)
            if not _is_safe_relative_git_path(normalized):
                raise _path_protocol_fatal()
            identity = GitPathIdentity(decoded, PurePosixPath(normalized))
            entries.append(EnumeratedPath(identity.raw_text, identity.canonical_path))
        return tuple(entries)

    def enumerate_untracked_entries(self) -> tuple[GitPathIdentity, ...]:
        observation = self._pending_untracked_observation
        if observation is None:
            observation = self._observe_untracked()
        self._pending_untracked_observation = None
        self._last_untracked_observation = observation
        return observation.paths

    def enumerate_untracked_paths(self) -> tuple[PurePosixPath, ...]:
        return tuple(item.canonical_path for item in self.enumerate_untracked_entries())

    def enumerate_index_entries(self) -> tuple[GitIndexEntry, ...]:
        result = self._git("ls-files", "--stage", "-z", "--cached", "--")
        if result.returncode != 0:
            raise _path_protocol_fatal()
        fields = result.stdout.split(b"\0")
        if fields and fields[-1] == b"":
            fields.pop()
        values: list[GitIndexEntry] = []
        seen_stage: set[tuple[bytes, int]] = set()
        for field in fields:
            try:
                metadata, raw_path = field.split(b"\t", 1)
                mode_raw, object_raw, stage_raw = metadata.split(b" ", 2)
                if (
                    len(mode_raw) != 6
                    or any(character not in b"01234567" for character in mode_raw)
                    or len(object_raw) not in {40, 64}
                    or any(character not in b"0123456789abcdefABCDEF" for character in object_raw)
                    or stage_raw not in {b"0", b"1", b"2", b"3"}
                ):
                    raise ValueError
                identity = _decode_git_identity(raw_path)
                stage = int(stage_raw)
                key = (raw_path, stage)
                if key in seen_stage:
                    raise ValueError
                seen_stage.add(key)
                values.append(
                    GitIndexEntry(
                        path=identity.canonical_path,
                        object_id=object_raw.decode("ascii").lower(),
                        mode=mode_raw.decode("ascii"),
                        stage=stage,
                        raw_text=identity.raw_text,
                    )
                )
            except (UnicodeDecodeError, ValueError) as error:
                raise _path_protocol_fatal() from error
        _validate_path_identity_injectivity(item.identity for item in values)
        expected_flag_counts: dict[str, int] = {}
        for item in values:
            expected_flag_counts[item.identity.raw_text] = (
                expected_flag_counts.get(item.identity.raw_text, 0) + 1
            )
        flags = self._enumerate_index_flags(expected_flag_counts)
        if set(flags) != set(expected_flag_counts):
            raise _path_protocol_fatal()
        values = [
            GitIndexEntry(
                item.path,
                item.object_id,
                item.mode,
                item.stage,
                item.raw_text,
                flags[item.identity.raw_text].skip_worktree,
                flags[item.identity.raw_text].assume_unchanged,
                flags[item.identity.raw_text].marker,
            )
            for item in values
        ]
        return tuple(
            sorted(
                values,
                key=lambda item: ((item.raw_text or "").encode("utf-8"), item.stage),
            )
        )

    def _enumerate_index_flags(
        self,
        expected_counts: Mapping[str, int],
        *,
        location: Path | None = None,
        git_dir: Path | None = None,
    ) -> dict[str, _GitIndexFlag]:
        arguments = ("ls-files", "-v", "-z", "--cached", "--")
        result = (
            self._git(*arguments)
            if location is None
            else self._git_at(location, *arguments, git_dir=git_dir)
        )
        if result.returncode != 0:
            raise _path_protocol_fatal()
        fields = result.stdout.split(b"\0")
        if fields and fields[-1] == b"":
            fields.pop()
        values: dict[str, _GitIndexFlag] = {}
        counts: dict[str, int] = {}
        identities: list[GitPathIdentity] = []
        for field in fields:
            if len(field) < 3 or field[1:2] != b" " or field[:1] not in b"HhSsMmRrCcKk?":
                raise _path_protocol_fatal()
            identity = _decode_git_identity(field[2:])
            counts[identity.raw_text] = counts.get(identity.raw_text, 0) + 1
            if counts[identity.raw_text] > expected_counts.get(identity.raw_text, 0):
                raise _path_protocol_fatal()
            marker = field[:1].decode("ascii")
            flag = _GitIndexFlag(
                marker,
                marker in {"S", "s"},
                marker in {"h", "s"},
            )
            previous = values.get(identity.raw_text)
            if previous is not None and previous != flag:
                raise _path_protocol_fatal()
            values[identity.raw_text] = flag
            identities.append(identity)
        _validate_path_identity_injectivity(identities)
        if counts != dict(expected_counts):
            raise _path_protocol_fatal()
        return values

    def enumerate_unmerged_entries(self) -> tuple[GitPathIdentity, ...]:
        result = self._git("ls-files", "-u", "-z", "--")
        if result.returncode != 0:
            raise _path_protocol_fatal()
        fields = result.stdout.split(b"\0")
        if fields and fields[-1] == b"":
            fields.pop()
        values: dict[str, GitPathIdentity] = {}
        for field in fields:
            try:
                metadata, raw_path = field.split(b"\t", 1)
                mode, object_id, stage = metadata.split(b" ", 2)
                if (
                    len(mode) != 6
                    or any(character not in b"01234567" for character in mode)
                    or len(object_id) not in {40, 64}
                    or any(character not in b"0123456789abcdefABCDEF" for character in object_id)
                    or stage not in {b"1", b"2", b"3"}
                ):
                    raise ValueError
                identity = _decode_git_identity(raw_path)
                previous = values.get(identity.raw_text)
                if previous is not None and previous != identity:
                    raise ValueError
                values[identity.raw_text] = identity
            except (UnicodeDecodeError, ValueError) as error:
                raise _path_protocol_fatal() from error
        identities = tuple(values.values())
        _validate_path_identity_injectivity(identities)
        return tuple(
            sorted(
                identities,
                key=lambda item: (
                    item.canonical_path.as_posix().encode("utf-8"),
                    item.raw_text.encode("utf-8"),
                ),
            )
        )

    def enumerate_unmerged_paths(self) -> tuple[PurePosixPath, ...]:
        return tuple(item.canonical_path for item in self.enumerate_unmerged_entries())

    def enumerate_gitlink_states(
        self,
        index_entries: tuple[GitIndexEntry, ...],
    ) -> tuple[GitlinkWorktreeState, ...]:
        """Observe each materialized gitlink without invoking Git conversion helpers."""
        states: list[GitlinkWorktreeState] = []
        for entry in index_entries:
            if entry.stage != 0 or entry.mode != "160000":
                continue
            identity = entry.identity
            nested = self.repository.joinpath(*PurePosixPath(identity.raw_text).parts)
            if has_symlink_component(nested):
                raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
            try:
                nested_stat = nested.lstat()
            except OSError as error:
                raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE) from error
            if not stat.S_ISDIR(nested_stat.st_mode):
                raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
            git_metadata = nested / ".git"
            try:
                metadata_stat = git_metadata.lstat()
            except OSError as error:
                raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE) from error
            if stat.S_ISLNK(metadata_stat.st_mode):
                raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
            git_dir = self._validate_gitlink_binding(nested, git_metadata, metadata_stat)
            self._validate_gitlink_metadata(git_dir)
            binding_identity = self._binding_identity(git_dir)
            head = self._git_at(
                nested,
                "rev-parse",
                "--verify",
                "HEAD^{commit}",
                git_dir=git_dir,
            )
            if head.returncode != 0 or _OBJECT_ID.fullmatch(head.stdout) is None:
                raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
            current_head = head.stdout[:-1].decode("ascii").lower()
            object_format = self._gitlink_object_format(nested, git_dir)
            head_tree = self._enumerate_gitlink_tree(nested, git_dir, current_head)
            nested_index = self._enumerate_gitlink_index(nested, git_dir)
            staged_dirty = self._gitlink_index_differs_from_head(head_tree, nested_index)
            untracked_observation = self._observe_untracked(
                location=nested,
                git_dir=git_dir,
            )
            untracked_entries = untracked_observation.paths
            profile = self._gitlink_comparison_profile(
                nested,
                git_dir,
                head_tree,
                nested_index,
                untracked_entries,
                ignore_profile=untracked_observation.authority,
            )
            tracked_dirty, tracked_worktree_digest = self._gitlink_worktree_differs(
                nested,
                nested_index,
                object_format,
                profile,
            )
            if self._binding_identity(git_dir) != binding_identity:
                raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
            states.append(
                GitlinkWorktreeState(
                    identity=identity,
                    index_object_id=entry.object_id,
                    current_head=current_head,
                    initialized=True,
                    tracked_content_dirty=tracked_dirty or staged_dirty,
                    untracked_content_dirty=bool(untracked_entries),
                    binding_identity=binding_identity,
                    comparison_profile_digest=profile.digest,
                    tracked_worktree_digest=tracked_worktree_digest,
                    untracked_paths=untracked_entries,
                )
            )
        return tuple(
            sorted(
                states,
                key=lambda item: (
                    item.identity.canonical_path.as_posix().encode("utf-8"),
                    item.identity.raw_text.encode("utf-8"),
                ),
            )
        )

    def _gitlink_comparison_profile(
        self,
        location: Path,
        git_dir: Path,
        tree: tuple[_GitlinkTreeEntry, ...],
        index: tuple[GitIndexEntry, ...],
        untracked: tuple[GitPathIdentity, ...],
        *,
        ignore_profile: IgnoreAuthorityProfile | None = None,
    ) -> GitlinkComparisonProfile:
        if ignore_profile is None:
            ignore_profile = IgnoreAuthorityProfile("", None, None)
        config_records, config_allowed, core_filemode, core_symlinks = self._gitlink_config_profile(
            location,
            git_dir,
        )
        identities = _unique_gitlink_identities(
            tuple(item.identity for item in tree)
            + tuple(item.identity for item in index)
            + untracked
        )
        attributes_records, attributes_allowed = self._gitlink_attributes_profile(
            location,
            git_dir,
            identities,
            config_records,
        )
        index_flags_digest = _gitlink_index_flags_digest(index)
        config_digest = _gitlink_config_digest(config_records)
        attributes_digest = _gitlink_attributes_digest(attributes_records, identities)
        raw_comparison_allowed = config_allowed and attributes_allowed and ignore_profile.allowed
        if any(item.stage != 0 for item in index):
            raw_comparison_allowed = False
        if any(item.skip_worktree or item.assume_unchanged for item in index):
            raw_comparison_allowed = False
        if any(item.index_flag != "H" for item in index):
            raw_comparison_allowed = False
        supported_modes = {"100644", "100755", "120000"}
        if any(item.mode not in supported_modes for item in tree) or any(
            item.mode not in supported_modes for item in index
        ):
            raw_comparison_allowed = False
        if not core_symlinks and (
            any(item.mode == "120000" for item in tree)
            or any(item.mode == "120000" for item in index)
        ):
            raw_comparison_allowed = False
        profile = GitlinkComparisonProfile(
            config_digest=config_digest,
            attributes_digest=attributes_digest,
            index_flags_digest=index_flags_digest,
            raw_comparison_allowed=raw_comparison_allowed,
            core_filemode=bool(core_filemode),
            ignore_digest=ignore_profile.digest,
        )
        if not profile.raw_comparison_allowed:
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
        return profile

    def _gitlink_config_profile(
        self,
        location: Path,
        git_dir: Path,
    ) -> tuple[tuple[tuple[str, str, str], ...], bool, bool, bool]:
        records: list[tuple[str, str, str]] = []
        try:
            worktree_config_present = _is_regular_file(git_dir / "config.worktree")
            linked_worktree = _is_linked_worktree_git_dir(git_dir)
        except OSError as error:
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE) from error
        for scope in ("local", "worktree"):
            if scope == "worktree" and linked_worktree and not worktree_config_present:
                continue
            result = self._git_at(
                location,
                "config",
                "--null",
                "--no-includes",
                f"--{scope}",
                "--get-regexp",
                _GITLINK_CONFIG_PATTERN,
                git_dir=git_dir,
            )
            if result.returncode not in {0, 1} or result.stderr:
                raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
            if result.returncode == 0:
                try:
                    parsed = _parse_git_config_records(result.stdout)
                except ValueError as error:
                    raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE) from error
                if scope == "local" or worktree_config_present:
                    records.extend((scope, key, value) for key, value in parsed)

        by_scope_key: dict[str, dict[str, list[str]]] = {"local": {}, "worktree": {}}
        for scope, key, value in records:
            by_scope_key.setdefault(scope, {}).setdefault(key, []).append(value)
        by_key: dict[str, list[str]] = {}
        for key in {key for _scope, key, _value in records}:
            worktree_values = by_scope_key["worktree"].get(key, [])
            by_key[key] = worktree_values or by_scope_key["local"].get(key, [])
        allowed = True
        core_filemode = True
        core_symlinks = True
        for key in ("core.autocrlf", "core.eol", "core.filemode", "core.symlinks"):
            if any(len(by_scope_key[scope].get(key, [])) > 1 for scope in by_scope_key):
                allowed = False
        autocrlf = [
            value
            for scope in by_scope_key
            for value in by_scope_key[scope].get("core.autocrlf", [])
        ]
        if autocrlf and any(_parse_git_bool(value) is not False for value in autocrlf):
            allowed = False
        if any(by_scope_key[scope].get("core.eol") for scope in by_scope_key):
            allowed = False
        filemode = by_key.get("core.filemode")
        if filemode:
            parsed_filemode = _parse_git_bool(filemode[0])
            if parsed_filemode is None:
                allowed = False
            else:
                core_filemode = parsed_filemode
        symlinks = by_key.get("core.symlinks")
        if symlinks:
            parsed_symlinks = _parse_git_bool(symlinks[0])
            if parsed_symlinks is None:
                allowed = False
            else:
                core_symlinks = parsed_symlinks
        if any(
            key.startswith(("filter.", "diff.", "include")) or key == "core.attributesfile"
            for _scope, key, _value in records
        ):
            allowed = False
        return tuple(sorted(records)), allowed, core_filemode, core_symlinks

    def _gitlink_attributes_profile(
        self,
        location: Path,
        git_dir: Path,
        identities: tuple[GitPathIdentity, ...],
        config_records: tuple[tuple[str, str, str], ...],
    ) -> tuple[tuple[tuple[str, str, str], ...], bool]:
        try:
            external_attributes = _gitlink_external_attributes_source(git_dir)
        except OSError as error:
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE) from error
        if external_attributes:
            return (), False
        if any(
            key.startswith("include") or key == "core.attributesfile"
            for _scope, key, _value in config_records
        ):
            return (), False
        try:
            _validate_gitlink_attributes_files(location, identities)
        except OSError as error:
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE) from error
        records: list[tuple[str, str, str]] = []
        allowed = True
        for identity in identities:
            result = self._git_at(
                location,
                "check-attr",
                "-z",
                "--all",
                "--",
                identity.raw_text,
                git_dir=git_dir,
            )
            if result.returncode != 0 or result.stderr:
                raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
            try:
                parsed = parse_check_attr_z(result.stdout, identity.raw_text)
            except ValueError as error:
                raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE) from error
            records.extend(parsed)
            if any(not _attribute_is_raw_safe(attribute, value) for _, attribute, value in parsed):
                allowed = False
        return tuple(sorted(records)), allowed

    def _git_at(
        self,
        location: Path,
        *arguments: str,
        git_dir: Path | None = None,
    ) -> CommandResult:
        if self._cancelled():
            raise GitInterruptedError(diagnostic(DiagnosticCode.INTERRUPTED))
        command: tuple[str, ...] = ("git", "-C", str(location))
        if git_dir is not None:
            command += ("--git-dir", str(git_dir), "--work-tree", str(location))
        result = self._runner.run(
            (*command, "-c", "core.fsmonitor=false", *arguments),
            self._environment,
        )
        if self._cancelled():
            raise GitInterruptedError(diagnostic(DiagnosticCode.INTERRUPTED))
        return result

    def _validate_gitlink_binding(
        self,
        nested: Path,
        git_metadata: Path,
        metadata_stat: os.stat_result,
    ) -> Path:
        if stat.S_ISDIR(metadata_stat.st_mode):
            git_dir = git_metadata
        elif stat.S_ISREG(metadata_stat.st_mode):
            pointer = self._read_gitlink_pointer(git_metadata)
            pointer_path = Path(pointer)
            git_dir = pointer_path if pointer_path.is_absolute() else nested / pointer_path
        else:
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)

        try:
            resolved_nested = nested.resolve(strict=True)
            resolved_git_dir = git_dir.resolve(strict=True)
        except (OSError, RuntimeError) as error:
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE) from error
        if (
            has_symlink_component(nested)
            or has_symlink_component(git_metadata)
            or has_symlink_component(git_dir)
            or has_symlink_component(resolved_git_dir)
            or not resolved_git_dir.is_dir()
        ):
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)

        allowed_roots = [resolved_nested]
        parent_git = self.repository / ".git"
        try:
            if parent_git.is_dir() and not has_symlink_component(parent_git):
                allowed_roots.append(parent_git.resolve(strict=True))
        except (OSError, RuntimeError) as error:
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE) from error
        if not any(_is_relative_to(resolved_git_dir, root) for root in allowed_roots):
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
        return resolved_git_dir

    @staticmethod
    def _read_gitlink_pointer(metadata: Path) -> str:
        try:
            descriptor = os.open(metadata, _read_file_flags())
            try:
                payload = _read_bounded_file(descriptor, _MAX_GITLINK_METADATA_BYTES)
            finally:
                os.close(descriptor)
        except OSError as error:
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE) from error
        if not payload.endswith(b"\n") or payload.count(b"\n") != 1:
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
        value = payload[:-1]
        if not value.startswith(b"gitdir: "):
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
        try:
            pointer = value[len(b"gitdir: ") :].decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE) from error
        if not pointer or any(
            ord(character) < 0x20 or ord(character) == 0x7F for character in pointer
        ):
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
        return pointer

    @staticmethod
    def _validate_gitlink_metadata(git_dir: Path) -> None:
        for name in ("HEAD",):
            path = git_dir / name
            try:
                value = path.lstat()
            except OSError as error:
                raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE) from error
            if not stat.S_ISREG(value.st_mode) or stat.S_ISLNK(value.st_mode):
                raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)

    def _gitlink_object_format(self, location: Path, git_dir: Path) -> str:
        result = self._git_at(
            location,
            "rev-parse",
            "--show-object-format",
            git_dir=git_dir,
        )
        if result.returncode != 0 or result.stdout not in {b"sha1\n", b"sha256\n"}:
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
        return result.stdout[:-1].decode("ascii")

    def _enumerate_gitlink_tree(
        self,
        location: Path,
        git_dir: Path,
        commit: str,
    ) -> tuple[_GitlinkTreeEntry, ...]:
        result = self._git_at(
            location,
            "ls-tree",
            "-r",
            "-z",
            "--long",
            "--full-tree",
            commit,
            git_dir=git_dir,
        )
        if result.returncode != 0:
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
        values: list[_GitlinkTreeEntry] = []
        records = result.stdout.split(b"\0")
        if records and records[-1] == b"":
            records.pop()
        for record in records:
            try:
                metadata, raw_path = record.split(b"\t", 1)
                mode_raw, kind_raw, object_raw, _size_raw = metadata.split(b" ", 3)
                identity = _decode_git_identity(raw_path)
                object_id = object_raw.decode("ascii", errors="strict").lower()
                mode = mode_raw.decode("ascii", errors="strict")
                kind = kind_raw.decode("ascii", errors="strict")
                if len(object_id) not in {40, 64} or any(
                    character not in "0123456789abcdef" for character in object_id
                ):
                    raise ValueError
                values.append(_GitlinkTreeEntry(identity, object_id, mode, kind))
            except (UnicodeDecodeError, ValueError) as error:
                raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE) from error
        _validate_path_identity_injectivity(item.identity for item in values)
        return tuple(
            sorted(
                values,
                key=lambda item: (
                    item.identity.canonical_path.as_posix().encode("utf-8"),
                    item.identity.raw_text.encode("utf-8"),
                ),
            )
        )

    def _enumerate_gitlink_index(
        self,
        location: Path,
        git_dir: Path,
    ) -> tuple[GitIndexEntry, ...]:
        result = self._git_at(
            location,
            "ls-files",
            "--stage",
            "-z",
            "--cached",
            "--",
            git_dir=git_dir,
        )
        if result.returncode != 0:
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
        fields = result.stdout.split(b"\0")
        if fields and fields[-1] == b"":
            fields.pop()
        values: list[GitIndexEntry] = []
        seen: set[tuple[bytes, int]] = set()
        for field in fields:
            try:
                metadata, raw_path = field.split(b"\t", 1)
                mode_raw, object_raw, stage_raw = metadata.split(b" ", 2)
                if (
                    len(mode_raw) != 6
                    or any(character not in b"01234567" for character in mode_raw)
                    or len(object_raw) not in {40, 64}
                    or any(character not in b"0123456789abcdefABCDEF" for character in object_raw)
                    or stage_raw not in {b"0", b"1", b"2", b"3"}
                ):
                    raise ValueError
                identity = _decode_git_identity(raw_path)
                stage = int(stage_raw)
                key = (raw_path, stage)
                if key in seen:
                    raise ValueError
                seen.add(key)
                values.append(
                    GitIndexEntry(
                        identity.canonical_path,
                        object_raw.decode("ascii").lower(),
                        mode_raw.decode("ascii"),
                        stage,
                        identity.raw_text,
                    )
                )
            except (UnicodeDecodeError, ValueError) as error:
                raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE) from error
        _validate_path_identity_injectivity(item.identity for item in values)
        expected_flag_counts: dict[str, int] = {}
        for item in values:
            expected_flag_counts[item.identity.raw_text] = (
                expected_flag_counts.get(item.identity.raw_text, 0) + 1
            )
        flags = self._enumerate_index_flags(
            expected_flag_counts,
            location=location,
            git_dir=git_dir,
        )
        if set(flags) != set(expected_flag_counts):
            raise _path_protocol_fatal()
        values = [
            GitIndexEntry(
                item.path,
                item.object_id,
                item.mode,
                item.stage,
                item.raw_text,
                flags[item.identity.raw_text].skip_worktree,
                flags[item.identity.raw_text].assume_unchanged,
                flags[item.identity.raw_text].marker,
            )
            for item in values
        ]
        return tuple(
            sorted(
                values,
                key=lambda item: (
                    item.identity.canonical_path.as_posix().encode("utf-8"),
                    item.identity.raw_text.encode("utf-8") if item.raw_text else b"",
                    item.stage,
                ),
            )
        )

    @staticmethod
    def _gitlink_index_differs_from_head(
        tree: tuple[_GitlinkTreeEntry, ...],
        index: tuple[GitIndexEntry, ...],
    ) -> bool:
        if any(item.stage != 0 for item in index):
            return True
        tree_by_path = {item.identity.canonical_path: item for item in tree}
        index_by_path = {item.path: item for item in index}
        if set(tree_by_path) != set(index_by_path):
            return True
        for path, tree_entry in tree_by_path.items():
            index_entry = index_by_path[path]
            if (
                tree_entry.object_id != index_entry.object_id
                or tree_entry.mode != index_entry.mode
                or tree_entry.identity.raw_text != index_entry.identity.raw_text
            ):
                return True
        return False

    def _gitlink_worktree_differs(
        self,
        nested: Path,
        index: tuple[GitIndexEntry, ...],
        object_format: str,
        profile: GitlinkComparisonProfile,
    ) -> tuple[bool, str]:
        if not profile.raw_comparison_allowed:
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
        observations: list[dict[str, str | None]] = []
        dirty = False
        for entry in index:
            if entry.stage != 0:
                dirty = True
                continue
            if entry.mode == "160000":
                raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
            try:
                mode, digest = _read_nested_worktree_entry(nested, entry.identity, object_format)
            except OSError as error:
                raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE) from error
            observations.append(
                {
                    "raw_path": entry.identity.raw_text,
                    "index_mode": entry.mode,
                    "index_object_id": entry.object_id,
                    "worktree_mode": mode,
                    "worktree_object_id": digest,
                }
            )
            if mode is None:
                dirty = True
                continue
            if not _raw_modes_equal(entry.mode, mode, profile.core_filemode) or (
                digest != entry.object_id
            ):
                dirty = True
        ordered_observations = tuple(sorted(observations, key=_gitlink_observation_key))
        tracked_digest = hashlib.sha256(
            encode_canonical_json(
                {
                    "schema": "code-structure-viz.gitlink-worktree-content/v1",
                    "entries": ordered_observations,
                }
            )
        ).hexdigest()
        return dirty, tracked_digest

    @staticmethod
    def _binding_identity(git_dir: Path) -> str:
        if has_symlink_component(git_dir):
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
        try:
            value = git_dir.stat(follow_symlinks=False)
        except OSError as error:
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE) from error
        if not stat.S_ISDIR(value.st_mode):
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
        return f"{os.fspath(git_dir)}:{value.st_dev}:{value.st_ino}"

    def enumerate_paths(self) -> tuple[PurePosixPath, ...]:
        return tuple(entry.normalized for entry in self.enumerate_path_entries())

    def resolve_commit(self, reference: str) -> Commit:
        """Resolve a local Git reference to a commit without updating repository state."""
        if (
            not reference
            or reference.startswith("-")
            or any(character in reference for character in "\x00\r\n\t")
        ):
            raise _fatal(DiagnosticCode.DIFF_ENDPOINT)
        result = self._git(
            "rev-parse",
            "--verify",
            "--end-of-options",
            f"{reference}^{{commit}}",
        )
        if result.returncode != 0 or _OBJECT_ID.fullmatch(result.stdout) is None:
            raise _fatal(DiagnosticCode.DIFF_ENDPOINT)
        return Commit(result.stdout[:-1].decode("ascii").lower())

    def resolve_merge_base(self, left: str, right: str) -> str | None:
        result = self._git("merge-base", "--all", left, right)
        if result.returncode != 0:
            return None
        values = [item for item in result.stdout.splitlines() if _OBJECT_ID.fullmatch(item + b"\n")]
        if not values:
            return None
        return min(values).decode("ascii").lower()

    def enumerate_ref_names(self, namespace: str) -> tuple[str, ...]:
        if (
            not namespace.startswith("refs/")
            or namespace.endswith("/")
            or namespace.startswith("-")
            or any(character in namespace for character in "\x00\r\n\t")
        ):
            raise _fatal(DiagnosticCode.DIFF_ENDPOINT)
        prefix = f"{namespace}/"
        result = self._git("for-each-ref", "--format=%(refname)", prefix)
        if result.returncode != 0:
            raise _fatal(DiagnosticCode.DIFF_ENDPOINT)
        if not result.stdout:
            return ()
        if not result.stdout.endswith(b"\n"):
            raise _fatal(DiagnosticCode.DIFF_ENDPOINT)
        values: list[str] = []
        for raw in result.stdout.splitlines():
            try:
                value = raw.decode("utf-8", errors="strict")
            except UnicodeDecodeError as error:
                raise _fatal(DiagnosticCode.DIFF_ENDPOINT) from error
            if (
                not value.startswith(prefix)
                or value.startswith("-")
                or any(character in value for character in "\x00\r\n\t")
            ):
                raise _fatal(DiagnosticCode.DIFF_ENDPOINT)
            values.append(value)
        return tuple(sorted(set(values), key=lambda item: item.encode("utf-8")))

    def enumerate_commit_tree(self, commit: str) -> tuple[CommitTreeEntry, ...]:
        result = self._git("ls-tree", "-r", "-z", "--long", "--full-tree", commit)
        if result.returncode != 0:
            raise _fatal(DiagnosticCode.DIFF_ENDPOINT)
        entries: list[CommitTreeEntry] = []
        seen_raw: set[bytes] = set()
        records = result.stdout.split(b"\0")
        if records and records[-1] == b"":
            records.pop()
        for record in records:
            try:
                metadata, raw_path = record.split(b"\t", 1)
                if raw_path in seen_raw:
                    raise ValueError
                seen_raw.add(raw_path)
                mode_raw, kind_raw, object_raw, _size_raw = metadata.split(b" ", 3)
                identity = _decode_git_identity(raw_path)
                object_id = object_raw.decode("ascii", errors="strict").lower()
                if len(object_id) not in {40, 64} or any(
                    character not in "0123456789abcdef" for character in object_id
                ):
                    raise ValueError
                entries.append(
                    CommitTreeEntry(
                        identity.canonical_path,
                        object_id,
                        mode_raw.decode("ascii", errors="strict"),
                        kind_raw.decode("ascii", errors="strict"),
                        identity.raw_text,
                    )
                )
            except (UnicodeDecodeError, ValueError) as error:
                raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE) from error
        _validate_path_identity_injectivity(item.identity for item in entries)
        return tuple(sorted(entries, key=lambda item: item.path.as_posix().encode("utf-8")))

    def read_commit_blob(self, commit: str, path: PurePosixPath) -> bytes:
        if not _is_safe_relative_git_path(path.as_posix()):
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
        result = self._git("cat-file", "blob", f"{commit}:{path.as_posix()}")
        if result.returncode != 0:
            raise _fatal(DiagnosticCode.DIFF_ENDPOINT)
        return result.stdout

    def read_blob_object(self, object_id: str) -> bytes:
        if len(object_id) not in {40, 64} or any(
            character not in "0123456789abcdef" for character in object_id
        ):
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
        result = self._git("cat-file", "blob", object_id)
        if result.returncode != 0:
            raise _fatal(DiagnosticCode.DIFF_ENDPOINT)
        return result.stdout

    def diff_name_status(self, before: str, after: str | None = None) -> bytes:
        endpoints = (before,) if after is None else (before, after)
        result = self._git(
            "diff",
            "--no-ext-diff",
            "--no-textconv",
            "--no-color",
            "--find-renames=50%",
            "--find-copies=50%",
            "--name-status",
            "-z",
            "--format=",
            *endpoints,
            "--",
        )
        if result.returncode != 0:
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
        return result.stdout

    def diff_patch(self, before: str, after: str | None = None) -> bytes:
        endpoints = (before,) if after is None else (before, after)
        result = self._git(
            "diff",
            "--no-ext-diff",
            "--no-textconv",
            "--no-color",
            "--find-renames=50%",
            "--find-copies=50%",
            "--unified=0",
            "--format=",
            *endpoints,
            "--",
        )
        if result.returncode != 0:
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
        return result.stdout


def _parse_git_config_records(payload: bytes) -> tuple[tuple[str, str], ...]:
    """Parse ``git config --null --get-regexp`` without accepting lossy records."""
    if len(payload) > _MAX_GITLINK_METADATA_BYTES:
        raise ValueError("Git config output exceeds the bounded profile limit")
    if not payload:
        return ()
    if not payload.endswith(b"\0"):
        raise ValueError("Git config output is not NUL terminated")
    values: list[tuple[str, str]] = []
    for record in payload[:-1].split(b"\0"):
        if record.count(b"\n") != 1:
            raise ValueError("Git config record is not a key/value tuple")
        raw_key, raw_value = record.split(b"\n", 1)
        if not raw_key or b"\r" in raw_key or b"\0" in raw_key:
            raise ValueError("Git config key is malformed")
        if b"\r" in raw_value or b"\0" in raw_value:
            raise ValueError("Git config value is malformed")
        try:
            key = raw_key.decode("ascii", errors="strict").lower()
            value = raw_value.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise ValueError("Git config record is not valid text") from error
        if any(ord(character) < 0x20 or ord(character) == 0x7F for character in key):
            raise ValueError("Git config key contains a control character")
        if any(ord(character) < 0x20 or ord(character) == 0x7F for character in value):
            raise ValueError("Git config value contains a control character")
        values.append((key, value))
    return tuple(values)


def _parse_git_config_name_only(payload: bytes) -> tuple[str, ...]:
    """Parse ``git config --null --name-only`` without accepting lossy keys."""
    if len(payload) > _MAX_GITLINK_METADATA_BYTES:
        raise ValueError("Git config key output exceeds the bounded profile limit")
    if not payload:
        return ()
    if not payload.endswith(b"\0"):
        raise ValueError("Git config key output is not NUL terminated")
    values: list[str] = []
    for raw_key in payload[:-1].split(b"\0"):
        if not raw_key:
            raise ValueError("Git config key is missing")
        try:
            key = raw_key.decode("ascii", errors="strict").lower()
        except UnicodeDecodeError as error:
            raise ValueError("Git config key is not ASCII") from error
        if any(ord(character) < 0x20 or ord(character) == 0x7F for character in key):
            raise ValueError("Git config key contains a control character")
        if key not in {"core.excludesfile", "core.ignorecase"} and not key.startswith("include"):
            raise ValueError("Git config key is outside the ignore authority query")
        values.append(key)
    return tuple(values)


def _parse_git_bool_records(payload: bytes, expected_key: str) -> bool | None:
    records = _parse_git_config_records(payload)
    if any(key != expected_key for key, _value in records):
        raise ValueError("Git config output contains an unexpected key")
    if len(records) > 1:
        raise ValueError("Git config output contains duplicate values")
    if not records:
        return None
    value = _parse_git_bool(records[0][1])
    if value is None:
        raise ValueError("Git config boolean value is malformed")
    return value


def _parse_git_common_dir(payload: bytes) -> Path:
    if len(payload) > _MAX_GITLINK_METADATA_BYTES:
        raise ValueError("Git common directory output exceeds the bounded profile limit")
    if not payload.endswith(b"\n") or payload.count(b"\n") != 1:
        raise ValueError("Git common directory output is not one line")
    raw_path = payload[:-1]
    if not raw_path or b"\0" in raw_path:
        raise ValueError("Git common directory output is empty or NUL terminated")
    try:
        value = raw_path.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ValueError("Git common directory output is not UTF-8") from error
    if any(ord(character) < 0x20 or ord(character) == 0x7F for character in value):
        raise ValueError("Git common directory output contains a control character")
    path = Path(value)
    if not path.is_absolute():
        raise ValueError("Git common directory output is not absolute")
    return path


def _parse_git_bool(value: str) -> bool | None:
    normalized = value.strip().lower()
    if normalized in {"true", "yes", "on", "1"}:
        return True
    if normalized in {"false", "no", "off", "0"}:
        return False
    return None


def parse_check_attr_z(payload: bytes, expected_path: str) -> tuple[tuple[str, str, str], ...]:
    """Strictly parse ``git check-attr -z --all`` path/attribute/value tuples."""
    if len(payload) > _MAX_GITLINK_METADATA_BYTES:
        raise ValueError("Git attributes output exceeds the bounded profile limit")
    if not payload:
        return ()
    if not payload.endswith(b"\0"):
        raise ValueError("Git attributes output is not NUL terminated")
    fields = payload[:-1].split(b"\0")
    if len(fields) % 3 != 0:
        raise ValueError("Git attributes output is not a tuple stream")
    values: list[tuple[str, str, str]] = []
    for offset in range(0, len(fields), 3):
        raw_path, raw_attribute, raw_value = fields[offset : offset + 3]
        if not raw_path or not raw_attribute:
            raise ValueError("Git attributes tuple is missing a field")
        try:
            path = raw_path.decode("utf-8", errors="strict")
            attribute = raw_attribute.decode("ascii", errors="strict")
            value = raw_value.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise ValueError("Git attributes tuple is not valid text") from error
        if path != expected_path:
            raise ValueError("Git attributes path does not match the requested identity")
        if any(ord(character) < 0x20 or ord(character) == 0x7F for character in attribute):
            raise ValueError("Git attribute name contains a control character")
        if any(ord(character) < 0x20 or ord(character) == 0x7F for character in value):
            raise ValueError("Git attribute value contains a control character")
        values.append((path, attribute, value))
    return tuple(values)


def _attribute_is_raw_safe(attribute: str, value: str) -> bool:
    if attribute not in _GITLINK_ATTRIBUTE_NAMES:
        return False
    if attribute in {"text", "crlf", "ident", "filter"}:
        return value in {"unset", "unspecified"}
    return value == "unspecified"


def _gitlink_external_attributes_source(git_dir: Path) -> bool:
    info = git_dir / "info"
    try:
        info_stat = info.lstat()
    except FileNotFoundError:
        return False
    if stat.S_ISLNK(info_stat.st_mode) or not stat.S_ISDIR(info_stat.st_mode):
        raise OSError("nested Git attributes directory is unsafe")
    path = info / "attributes"
    try:
        value = path.lstat()
    except FileNotFoundError:
        return False
    if stat.S_ISLNK(value.st_mode) or not stat.S_ISREG(value.st_mode):
        raise OSError("nested Git attributes source is unsafe")
    return True


def _is_regular_file(path: Path) -> bool:
    try:
        value = path.lstat()
    except FileNotFoundError:
        return False
    if stat.S_ISLNK(value.st_mode) or not stat.S_ISREG(value.st_mode):
        raise OSError("nested Git config source is unsafe")
    return True


def _is_linked_worktree_git_dir(git_dir: Path) -> bool:
    path = git_dir / "commondir"
    try:
        value = path.lstat()
    except FileNotFoundError:
        return False
    if stat.S_ISLNK(value.st_mode) or not stat.S_ISREG(value.st_mode):
        raise OSError("linked worktree metadata is unsafe")
    return True


def _ignore_authority_file_digest(path: Path) -> str | None:
    """Read one allowed ignore file with a bounded, race-checked descriptor."""
    if has_symlink_component(path):
        raise OSError("ignore authority path is unsafe")
    try:
        before = path.lstat()
    except FileNotFoundError:
        return None
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise OSError("ignore authority path is not a regular file")
    descriptor = os.open(path, _read_file_flags())
    try:
        opened = os.fstat(descriptor)
        if _stat_signature(before) != _stat_signature(opened):
            raise OSError("ignore authority path changed before read")
        payload = _read_bounded_file(descriptor, _MAX_GITLINK_METADATA_BYTES)
        after_open = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    try:
        after = path.lstat()
    except OSError as error:
        raise OSError("ignore authority path disappeared after read") from error
    if _stat_signature(before) != _stat_signature(after) or _stat_signature(
        opened
    ) != _stat_signature(after_open):
        raise OSError("ignore authority path changed during read")
    value = {
        "present": True,
        "signature": _stat_signature(after),
        "content_digest": hashlib.sha256(payload).hexdigest(),
    }
    return hashlib.sha256(encode_canonical_json(value)).hexdigest()


def _ignore_authority_gitignore_digest(location: Path, git_dir: Path) -> str:
    """Digest all working-tree ``.gitignore`` files within safe repository bounds."""
    directories = [location]
    records: list[tuple[str, str]] = []
    visited_directories = 0
    while directories:
        directory = directories.pop()
        visited_directories += 1
        if visited_directories > _MAX_IGNORE_AUTHORITY_DIRECTORIES:
            raise OSError("ignore authority walk exceeded its directory bound")
        if directory != location and _is_relative_to(directory, git_dir):
            continue
        if directory != location and _directory_has_git_metadata(directory):
            continue
        try:
            with os.scandir(directory) as scanner:
                entries = sorted(
                    scanner,
                    key=lambda entry: os.fsencode(entry.name),
                )
        except (OSError, UnicodeEncodeError) as error:
            raise OSError("ignore authority walk is unsafe") from error
        for entry in entries:
            try:
                name = entry.name
                name.encode("utf-8", errors="strict")
                path = Path(entry.path)
                if name == ".git":
                    continue
                if name == ".gitignore":
                    digest = _ignore_authority_file_digest(path)
                    if digest is None:
                        raise OSError("ignore authority file disappeared")
                    if len(records) >= _MAX_IGNORE_AUTHORITY_FILES:
                        raise OSError("ignore authority walk exceeded its file bound")
                    relative = path.relative_to(location).as_posix()
                    records.append((relative, digest))
                    continue
                if entry.is_symlink():
                    continue
                if entry.is_dir(follow_symlinks=False):
                    directories.append(path)
            except (OSError, UnicodeEncodeError) as error:
                raise OSError("ignore authority walk is unsafe") from error
    ordered = sorted(records, key=lambda item: item[0].encode("utf-8"))
    return hashlib.sha256(
        encode_canonical_json(
            {
                "schema": "code-structure-viz.gitignore-observation/v1",
                "files": [{"path": relative, "digest": digest} for relative, digest in ordered],
            }
        )
    ).hexdigest()


def _directory_has_git_metadata(directory: Path) -> bool:
    try:
        (directory / ".git").lstat()
    except FileNotFoundError:
        return False
    except OSError as error:
        raise OSError("nested Git metadata cannot be inspected") from error
    return True


def _validate_gitlink_attributes_files(
    location: Path,
    identities: Iterable[GitPathIdentity],
) -> None:
    candidates: set[Path] = {location / ".gitattributes"}
    for identity in identities:
        parts = PurePosixPath(identity.raw_text).parts
        for depth in range(len(parts)):
            candidates.add(location.joinpath(*parts[:depth], ".gitattributes"))
    for path in sorted(candidates, key=lambda item: item.as_posix().encode("utf-8")):
        if has_symlink_component(path):
            raise OSError("nested .gitattributes path is unsafe")
        try:
            value = path.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(value.st_mode) or not stat.S_ISREG(value.st_mode):
            raise OSError("nested .gitattributes source is unsafe")


def _unique_gitlink_identities(
    identities: Iterable[GitPathIdentity],
) -> tuple[GitPathIdentity, ...]:
    values: dict[str, GitPathIdentity] = {}
    for identity in identities:
        previous = values.get(identity.raw_text)
        if previous is not None and previous != identity:
            raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE)
        values[identity.raw_text] = identity
    result = tuple(values.values())
    _validate_path_identity_injectivity(result)
    return tuple(
        sorted(
            result,
            key=lambda item: (
                item.canonical_path.as_posix().encode("utf-8"),
                item.raw_text.encode("utf-8"),
            ),
        )
    )


def _gitlink_config_digest(records: Iterable[tuple[str, str, str]]) -> str:
    return hashlib.sha256(
        encode_canonical_json(
            {
                "schema": "code-structure-viz.gitlink-config-observation/v1",
                "records": [
                    {"scope": scope, "key": key, "value": value}
                    for scope, key, value in sorted(records)
                ],
            }
        )
    ).hexdigest()


def _ignore_config_digest(records: Iterable[tuple[str, str]]) -> str:
    return hashlib.sha256(
        encode_canonical_json(
            {
                "schema": "code-structure-viz.ignore-config-observation/v1",
                "records": [{"scope": scope, "key": key} for scope, key in sorted(records)],
            }
        )
    ).hexdigest()


def _gitlink_attributes_digest(
    records: Iterable[tuple[str, str, str]],
    identities: Iterable[GitPathIdentity],
) -> str:
    ordered_identities = tuple(
        sorted(
            identities,
            key=lambda item: (
                item.canonical_path.as_posix().encode("utf-8"),
                item.raw_text.encode("utf-8"),
            ),
        )
    )
    return hashlib.sha256(
        encode_canonical_json(
            {
                "schema": "code-structure-viz.gitlink-attributes-observation/v1",
                "paths": [item.raw_text for item in ordered_identities],
                "records": [
                    {"path": path, "attribute": attribute, "value": value}
                    for path, attribute, value in sorted(records)
                ],
            }
        )
    ).hexdigest()


def _gitlink_observation_key(item: dict[str, str | None]) -> bytes:
    return str(item["raw_path"]).encode("utf-8")


def _gitlink_index_flags_digest(index: Iterable[GitIndexEntry]) -> str:
    values = sorted(
        (
            {
                "raw_path": item.identity.raw_text,
                "stage": item.stage,
                "mode": item.mode,
                "object_id": item.object_id,
                "skip_worktree": item.skip_worktree,
                "assume_unchanged": item.assume_unchanged,
                "index_flag": item.index_flag,
            }
            for item in index
        ),
        key=lambda item: (
            str(item["raw_path"]).encode("utf-8"),
            cast(int, item["stage"]),
        ),
    )
    return hashlib.sha256(
        encode_canonical_json(
            {
                "schema": "code-structure-viz.gitlink-index-flags/v1",
                "entries": values,
            }
        )
    ).hexdigest()


def _raw_modes_equal(expected: str, observed: str, filemode: bool) -> bool:
    if expected == observed:
        return True
    return not filemode and {expected, observed} <= {"100644", "100755"}


def _is_safe_relative_git_path(value: str) -> bool:
    if not value or value.startswith("/") or "\\" in value or "\0" in value:
        return False
    if any(ord(character) < 0x20 or ord(character) == 0x7F for character in value):
        return False
    parts = value.split("/")
    return all(part not in {"", ".", ".."} for part in parts)


def _decode_git_path(raw: bytes) -> PurePosixPath:
    return _decode_git_identity(raw).canonical_path


def _decode_git_identity(raw: bytes) -> GitPathIdentity:
    try:
        decoded = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise UnrepresentableGitPathFatal(diagnostic(DiagnosticCode.SOURCE_NON_UTF8)) from error
    normalized = unicodedata.normalize("NFC", decoded)
    if not _is_safe_relative_git_path(normalized):
        raise ValueError("unsafe Git path")
    return GitPathIdentity(decoded, PurePosixPath(normalized))


def _validate_path_identity_injectivity(identities: Iterable[GitPathIdentity]) -> None:
    canonical_to_raw: dict[PurePosixPath, bytes] = {}
    for identity in identities:
        raw = identity.raw_text.encode("utf-8")
        previous = canonical_to_raw.get(identity.canonical_path)
        if previous is None:
            canonical_to_raw[identity.canonical_path] = raw
        elif previous != raw:
            raise GitPathIdentityCollisionFatal(diagnostic(DiagnosticCode.DIFF_FILE_CHANGE))


def _decode_identity_list(payload: bytes) -> tuple[GitPathIdentity, ...]:
    if len(payload) > 64 * 1024 * 1024:
        raise _path_protocol_fatal()
    fields = payload.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()
    if any(not field for field in fields):
        raise _path_protocol_fatal()
    values: dict[str, GitPathIdentity] = {}
    for field in fields:
        try:
            identity = _decode_git_identity(field)
        except (UnicodeDecodeError, ValueError) as error:
            raise _path_protocol_fatal() from error
        if identity.raw_text in values:
            raise _path_protocol_fatal()
        values[identity.raw_text] = identity
    identities = tuple(values.values())
    _validate_path_identity_injectivity(identities)
    return tuple(
        sorted(
            identities,
            key=lambda item: (
                item.canonical_path.as_posix().encode("utf-8"),
                item.raw_text.encode("utf-8"),
            ),
        )
    )


def _single_line_bytes(value: bytes) -> bool:
    return (
        len(value) <= 64 * 1024
        and value.endswith(b"\n")
        and value.count(b"\n") == 1
        and b"\0" not in value
    )


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _read_file_flags() -> int:
    flags = os.O_RDONLY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    return flags


def _directory_flags() -> int:
    flags = _read_file_flags()
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    return flags


def _read_bounded_file(descriptor: int, limit: int) -> bytes:
    chunks: list[bytes] = []
    size = 0
    while True:
        chunk = os.read(descriptor, 1024 * 1024)
        if not chunk:
            return b"".join(chunks)
        size += len(chunk)
        if size > limit:
            raise OSError("bounded Git metadata read exceeded")
        chunks.append(chunk)


def _stat_signature(value: os.stat_result) -> tuple[int, int, int, int, int]:
    return (value.st_dev, value.st_ino, value.st_mode, value.st_size, value.st_mtime_ns)


def _read_nested_worktree_entry(
    nested: Path,
    identity: GitPathIdentity,
    object_format: str,
) -> tuple[str | None, str | None]:
    """Read one nested tracked path without following repository-controlled links."""
    components = PurePosixPath(identity.raw_text).parts
    if not components:
        raise OSError("empty nested path")
    parent: int | None = None
    try:
        parent = os.open(nested, _directory_flags())
        for component in components[:-1]:
            try:
                before = os.stat(component, dir_fd=parent, follow_symlinks=False)
            except FileNotFoundError:
                return None, None
            if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode):
                raise OSError("nested tracked path has unsafe parent")
            child = os.open(component, _directory_flags(), dir_fd=parent)
            try:
                after = os.fstat(child)
                if _stat_signature(before) != _stat_signature(after):
                    raise OSError("nested tracked path changed during observation")
            except BaseException:
                os.close(child)
                raise
            os.close(parent)
            parent = child

        name = components[-1]
        try:
            value = os.stat(name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            return None, None
        if stat.S_ISLNK(value.st_mode):
            target = os.readlink(name, dir_fd=parent)
            content = os.fsencode(target)
            if len(content) > _MAX_GITLINK_FILE_BYTES:
                raise OSError("nested symlink target is too large")
            return "120000", _git_blob_digest(content, object_format)
        if not stat.S_ISREG(value.st_mode):
            return None, None
        if value.st_size < 0 or value.st_size > _MAX_GITLINK_FILE_BYTES:
            raise OSError("nested tracked file is too large")
        descriptor = os.open(name, _read_file_flags(), dir_fd=parent)
        try:
            opened_before = os.fstat(descriptor)
            if _stat_signature(value) != _stat_signature(opened_before):
                raise OSError("nested tracked file changed before read")
            digest = _git_blob_stream_digest(descriptor, opened_before.st_size, object_format)
            opened_after = os.fstat(descriptor)
        finally:
            os.close(descriptor)
        final_value = os.stat(name, dir_fd=parent, follow_symlinks=False)
        if _stat_signature(value) != _stat_signature(final_value) or _stat_signature(
            opened_before
        ) != _stat_signature(opened_after):
            raise OSError("nested tracked file changed during read")
        mode = "100755" if value.st_mode & 0o111 else "100644"
        return mode, digest
    finally:
        if parent is not None:
            os.close(parent)


def _git_blob_digest(content: bytes, object_format: str) -> str:
    digest = hashlib.new(object_format)
    digest.update(f"blob {len(content)}\0".encode("ascii"))
    digest.update(content)
    return digest.hexdigest()


def _git_blob_stream_digest(descriptor: int, size: int, object_format: str) -> str:
    digest = hashlib.new(object_format)
    digest.update(f"blob {size}\0".encode("ascii"))
    remaining = size
    while remaining:
        chunk = os.read(descriptor, min(1024 * 1024, remaining))
        if not chunk:
            raise OSError("nested tracked file ended during read")
        digest.update(chunk)
        remaining -= len(chunk)
    return digest.hexdigest()


def _decode_path_list(payload: bytes) -> tuple[PurePosixPath, ...]:
    return tuple(item.canonical_path for item in _decode_identity_list(payload))
