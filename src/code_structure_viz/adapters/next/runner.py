from __future__ import annotations

import hashlib
import importlib.resources
import re
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


@dataclass(frozen=True, slots=True)
class NextAdapterIdentity:
    """Stable identity derived from one read of the packaged adapter entrypoint."""

    version: str
    sha256: str


def resolve_next_adapter_identity() -> NextAdapterIdentity:
    """Resolve the adapter identity without accepting a caller-selected resource."""

    try:
        resource = importlib.resources.files(_RESOURCE_PACKAGE).joinpath(*_RESOURCE_PARTS)
        if not resource.is_file():
            raise NextAdapterIdentityError("packaged Next adapter entrypoint is not a file")
        content = resource.read_bytes()
    except NextAdapterIdentityError:
        raise
    except (ModuleNotFoundError, OSError) as error:
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
