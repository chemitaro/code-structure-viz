from __future__ import annotations

import os
import re
import selectors
import subprocess
import unicodedata
from collections.abc import Callable, Mapping
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import BinaryIO, Final, Protocol, cast

from code_structure_viz.core.diagnostics import Diagnostic, DiagnosticCode, diagnostic
from code_structure_viz.core.path_safety import has_symlink_component

_OBJECT_ID: Final[re.Pattern[bytes]] = re.compile(rb"(?:[0-9A-Fa-f]{40}|[0-9A-Fa-f]{64})\n")
_GIT_VERSION_PREFIX: Final[re.Pattern[bytes]] = re.compile(rb"git version ([0-9]+)\.([0-9]+)")
_FIXED_ENV: Final[dict[str, str]] = {
    "LC_ALL": "C",
    "LANG": "C",
    "GIT_OPTIONAL_LOCKS": "0",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_TERMINAL_PROMPT": "0",
    "GIT_PAGER": "cat",
    "PAGER": "cat",
    "NO_COLOR": "1",
    "GIT_NO_LAZY_FETCH": "1",
    "GIT_NO_REPLACE_OBJECTS": "1",
}


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
class CommitTreeEntry:
    path: PurePosixPath
    object_id: str
    mode: str
    kind: str


@dataclass(frozen=True, slots=True)
class EnumeratedPath:
    raw_text: str
    normalized: PurePosixPath


@dataclass(frozen=True, slots=True)
class GitIndexEntry:
    path: PurePosixPath
    object_id: str
    mode: str
    stage: int


class UnrepresentableGitPathFatal(GitReadError):
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

    def enumerate_path_entries(self) -> tuple[EnumeratedPath, ...]:
        result = self._git("ls-files", "-z", "--cached", "--others", "--exclude-standard")
        if result.returncode != 0:
            raise _path_protocol_fatal()
        raw_entries = result.stdout.split(b"\0")
        if raw_entries and raw_entries[-1] == b"":
            raw_entries.pop()
        if any(not entry for entry in raw_entries):
            raise _path_protocol_fatal()

        entries: list[EnumeratedPath] = []
        for raw in raw_entries:
            try:
                decoded = raw.decode("utf-8", errors="strict")
            except UnicodeDecodeError as error:
                value = diagnostic(DiagnosticCode.SOURCE_NON_UTF8)
                raise UnrepresentableGitPathFatal(value) from error
            normalized = unicodedata.normalize("NFC", decoded)
            if not _is_safe_relative_git_path(normalized):
                raise _path_protocol_fatal()
            entries.append(EnumeratedPath(decoded, PurePosixPath(normalized)))
        return tuple(entries)

    def enumerate_untracked_paths(self) -> tuple[PurePosixPath, ...]:
        result = self._git("ls-files", "-z", "--others", "--exclude-standard", "--")
        if result.returncode != 0:
            raise _path_protocol_fatal()
        return _decode_path_list(result.stdout)

    def enumerate_index_entries(self) -> tuple[GitIndexEntry, ...]:
        result = self._git("ls-files", "--stage", "-z", "--cached", "--")
        if result.returncode != 0:
            raise _path_protocol_fatal()
        fields = result.stdout.split(b"\0")
        if fields and fields[-1] == b"":
            fields.pop()
        values: list[GitIndexEntry] = []
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
                values.append(
                    GitIndexEntry(
                        path=_decode_git_path(raw_path),
                        object_id=object_raw.decode("ascii").lower(),
                        mode=mode_raw.decode("ascii"),
                        stage=int(stage_raw),
                    )
                )
            except (UnicodeDecodeError, ValueError) as error:
                raise _path_protocol_fatal() from error
        return tuple(
            sorted(
                values,
                key=lambda item: (item.path.as_posix().encode("utf-8"), item.stage),
            )
        )

    def enumerate_unmerged_paths(self) -> tuple[PurePosixPath, ...]:
        result = self._git("ls-files", "-u", "-z", "--")
        if result.returncode != 0:
            raise _path_protocol_fatal()
        fields = result.stdout.split(b"\0")
        if fields and fields[-1] == b"":
            fields.pop()
        values: set[PurePosixPath] = set()
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
                values.add(_decode_git_path(raw_path))
            except (UnicodeDecodeError, ValueError) as error:
                raise _path_protocol_fatal() from error
        return tuple(sorted(values, key=lambda item: item.as_posix().encode("utf-8")))

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
        records = result.stdout.split(b"\0")
        if records and records[-1] == b"":
            records.pop()
        for record in records:
            try:
                metadata, raw_path = record.split(b"\t", 1)
                mode_raw, kind_raw, object_raw, _size_raw = metadata.split(b" ", 3)
                path_text = raw_path.decode("utf-8", errors="strict")
                normalized = unicodedata.normalize("NFC", path_text)
                if not _is_safe_relative_git_path(normalized):
                    raise ValueError
                object_id = object_raw.decode("ascii", errors="strict").lower()
                if len(object_id) not in {40, 64} or any(
                    character not in "0123456789abcdef" for character in object_id
                ):
                    raise ValueError
                entries.append(
                    CommitTreeEntry(
                        PurePosixPath(normalized),
                        object_id,
                        mode_raw.decode("ascii", errors="strict"),
                        kind_raw.decode("ascii", errors="strict"),
                    )
                )
            except (UnicodeDecodeError, ValueError) as error:
                raise _fatal(DiagnosticCode.DIFF_FILE_CHANGE) from error
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


def _is_safe_relative_git_path(value: str) -> bool:
    if not value or value.startswith("/") or "\\" in value or "\0" in value:
        return False
    if any(ord(character) < 0x20 or ord(character) == 0x7F for character in value):
        return False
    parts = value.split("/")
    return all(part not in {"", ".", ".."} for part in parts)


def _decode_git_path(raw: bytes) -> PurePosixPath:
    try:
        decoded = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise UnrepresentableGitPathFatal(diagnostic(DiagnosticCode.SOURCE_NON_UTF8)) from error
    normalized = unicodedata.normalize("NFC", decoded)
    if not _is_safe_relative_git_path(normalized):
        raise ValueError("unsafe Git path")
    return PurePosixPath(normalized)


def _decode_path_list(payload: bytes) -> tuple[PurePosixPath, ...]:
    fields = payload.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()
    if any(not field for field in fields):
        raise _path_protocol_fatal()
    values = {_decode_git_path(field) for field in fields}
    return tuple(sorted(values, key=lambda item: item.as_posix().encode("utf-8")))
