from __future__ import annotations

import os
import re
import subprocess
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Final, Protocol

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
}


@dataclass(frozen=True, slots=True)
class CommandResult:
    returncode: int
    stdout: bytes
    stderr: bytes


class CommandRunner(Protocol):
    def run(self, argv: tuple[str, ...], env: Mapping[str, str]) -> CommandResult: ...


class SubprocessRunner:
    def run(self, argv: tuple[str, ...], env: Mapping[str, str]) -> CommandResult:
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


@dataclass(frozen=True, slots=True)
class Commit:
    object_id: str


@dataclass(frozen=True, slots=True)
class Unborn:
    branch_ref: str


type HeadState = Commit | Unborn


@dataclass(frozen=True, slots=True)
class EnumeratedPath:
    raw_text: str
    normalized: PurePosixPath


class GitReadError(RuntimeError):
    def __init__(self, value: Diagnostic) -> None:
        self.diagnostic = value
        super().__init__(value.message)


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
    def __init__(self, repository: Path, *, runner: CommandRunner | None = None) -> None:
        self.repository = repository
        self._runner = runner or SubprocessRunner()
        self._environment = _safe_environment()
        self._validated_identity: tuple[int, int] | None = None

    def _git(self, *arguments: str) -> CommandResult:
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
        return self._runner.run(argv, self._environment)

    def validate_git_version(self) -> None:
        result = self._runner.run(("git", "--version"), self._environment)
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

    def enumerate_paths(self) -> tuple[PurePosixPath, ...]:
        return tuple(entry.normalized for entry in self.enumerate_path_entries())


def _is_safe_relative_git_path(value: str) -> bool:
    if not value or value.startswith("/") or "\\" in value or "\0" in value:
        return False
    parts = value.split("/")
    return all(part not in {"", ".", ".."} for part in parts)
