from __future__ import annotations

import hashlib
import importlib.resources
import os
import re
import stat
from dataclasses import dataclass

_RESOURCE_PACKAGE = "code_structure_viz"
_RESOURCE_PARTS = ("_next_runtime", "next-adapter.mjs")
_VERSION_MARKER = b"CodeStructureViz-Adapter-Version:"
_VERSION_HEADER = re.compile(
    rb"\A// CodeStructureViz-Adapter-Version: "
    rb"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\n"
)


class NextAdapterIdentityError(RuntimeError):
    """The packaged Next adapter resource cannot provide a trusted identity."""


class NodeCandidateIdentityError(RuntimeError):
    """A supplied candidate path cannot provide a stable open-file identity."""


@dataclass(frozen=True, slots=True)
class NextAdapterIdentity:
    """Stable identity derived from one read of the packaged adapter entrypoint."""

    version: str
    sha256: str


@dataclass(slots=True)
class OpenedNodeCandidate:
    """Own one open candidate descriptor and its measured content identity."""

    candidate_path: str
    sha256: str
    device: int
    inode: int
    _descriptor: int | None

    def fileno(self) -> int:
        """Return the live descriptor owned by this candidate."""

        if self._descriptor is None:
            raise ValueError("candidate descriptor is closed")
        return self._descriptor

    def close(self) -> None:
        """Close the owned descriptor once; repeated calls are harmless."""

        descriptor = self._descriptor
        self._descriptor = None
        if descriptor is not None:
            os.close(descriptor)

    def __enter__(self) -> OpenedNodeCandidate:
        self.fileno()
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()


def _validate_absolute_candidate_path(candidate_path: str) -> None:
    if (
        not candidate_path.startswith("/")
        or candidate_path.startswith("//")
        or "\x00" in candidate_path
    ):
        raise NodeCandidateIdentityError("candidate path is not a canonical absolute POSIX path")

    components = candidate_path[1:].split("/")
    if not components or any(component in {"", ".", ".."} for component in components):
        raise NodeCandidateIdentityError("candidate path contains an unsafe component")


def _open_candidate_no_follow(candidate_path: str) -> int:
    components = candidate_path[1:].split("/")
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    parent_descriptor = os.open("/", directory_flags)
    try:
        for component in components[:-1]:
            child_descriptor = os.open(component, directory_flags, dir_fd=parent_descriptor)
            os.close(parent_descriptor)
            parent_descriptor = child_descriptor
        return os.open(
            components[-1],
            os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
            dir_fd=parent_descriptor,
        )
    finally:
        os.close(parent_descriptor)


def _candidate_stability_tuple(value: os.stat_result) -> tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _require_no_follow_open_capabilities() -> None:
    required_flags = ("O_NOFOLLOW", "O_CLOEXEC", "O_DIRECTORY")
    if any(not hasattr(os, name) for name in required_flags) or os.open not in os.supports_dir_fd:
        raise NodeCandidateIdentityError("required no-follow open capabilities are unavailable")


def open_node_candidate_identity(absolute_candidate: str) -> OpenedNodeCandidate:
    """Hash a supplied regular file through one retained, close-on-exec FD.

    This measures an opened object's bytes and host-local identity only. It
    does not establish that the path is trusted, executable, or Node.js.
    """

    _validate_absolute_candidate_path(absolute_candidate)
    _require_no_follow_open_capabilities()
    descriptor: int | None = None
    try:
        descriptor = _open_candidate_no_follow(absolute_candidate)
        os.set_inheritable(descriptor, False)
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise NodeCandidateIdentityError("candidate is not a regular file")

        digest = hashlib.sha256()
        while chunk := os.read(descriptor, 1024 * 1024):
            digest.update(chunk)

        after = os.fstat(descriptor)
        if _candidate_stability_tuple(before) != _candidate_stability_tuple(after):
            raise NodeCandidateIdentityError("candidate identity changed while hashing")

        os.lseek(descriptor, 0, os.SEEK_SET)
        result = OpenedNodeCandidate(
            candidate_path=absolute_candidate,
            sha256=digest.hexdigest(),
            device=before.st_dev,
            inode=before.st_ino,
            _descriptor=descriptor,
        )
        descriptor = None
        return result
    except NodeCandidateIdentityError:
        raise
    except OSError as error:
        raise NodeCandidateIdentityError("candidate file cannot be opened or measured") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)


def resolve_next_adapter_identity() -> NextAdapterIdentity:
    """Resolve the adapter identity without accepting a caller-selected resource."""

    try:
        resource = importlib.resources.files(_RESOURCE_PACKAGE).joinpath(*_RESOURCE_PARTS)
        if not resource.is_file():
            raise NextAdapterIdentityError("packaged Next adapter entrypoint is not a file")
        content = resource.read_bytes()
    except NextAdapterIdentityError:
        raise
    except (ImportError, OSError) as error:
        raise NextAdapterIdentityError("packaged Next adapter entrypoint is unavailable") from error

    if content.count(_VERSION_MARKER) != 1:
        raise NextAdapterIdentityError(
            "packaged Next adapter version marker is missing or duplicated"
        )
    match = _VERSION_HEADER.match(content)
    if match is None:
        raise NextAdapterIdentityError("packaged Next adapter version header is invalid")

    version = b".".join(match.groups()).decode("ascii")
    return NextAdapterIdentity(version=version, sha256=hashlib.sha256(content).hexdigest())
