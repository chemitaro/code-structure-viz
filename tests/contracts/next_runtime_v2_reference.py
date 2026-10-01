"""Data-only A-runtime reference producers; never a production runner."""

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from tests.contracts.next_runtime_v2_validation import validate_execution_asset_identity_v1

ENTRYPOINT_MEMBER = "code_structure_viz/_next_runtime/next-adapter.mjs"


@dataclass(frozen=True)
class RetainedExecutionAssets:
    """One immutable byte snapshot for content identity and later staging."""

    _members: tuple[tuple[str, str, bytes], ...] = field(repr=False)

    def descriptor(self) -> dict[str, Any]:
        record: dict[str, Any] = {
            "schema": "code-structure-viz.next-execution-assets/v1",
            "entrypoint_member": ENTRYPOINT_MEMBER,
            "members": [
                {
                    "package_path": path,
                    "role": role,
                    "size_bytes": len(content),
                    "sha256": hashlib.sha256(content).hexdigest(),
                }
                for path, role, content in self._members
            ],
        }
        preimage = json.dumps(
            record, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return {**record, "asset_set_id": hashlib.sha256(preimage).hexdigest()}

    def staging_members(self) -> tuple[tuple[str, bytes], ...]:
        return tuple((path, content) for path, _role, content in self._members)

    def adapter_identity(self) -> dict[str, str]:
        content = next(
            content for path, _role, content in self._members if path == ENTRYPOINT_MEMBER
        )
        if content.count(b"CodeStructureViz-Adapter-Version:") != 1:
            raise ValueError("retained adapter version marker is missing or duplicated")
        marker = re.match(
            rb"\A// CodeStructureViz-Adapter-Version: "
            rb"((?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*))\n",
            content,
        )
        if marker is None:
            raise ValueError("retained adapter header has no canonical stable version")
        return {
            "protocol": "code-structure-viz.next-adapter/v2",
            "version": marker.group(1).decode("ascii"),
            "sha256": hashlib.sha256(content).hexdigest(),
            "entrypoint_member": ENTRYPOINT_MEMBER,
        }


def retain_execution_assets_v1(
    members: Mapping[str, tuple[str, bytes]],
) -> RetainedExecutionAssets:
    """Freeze already-read reference bytes, not paths for a later resource read."""

    snapshot = tuple((path, role, content) for path, (role, content) in members.items())
    if any(not isinstance(content, bytes) for _path, _role, content in snapshot):
        raise TypeError("execution asset content must already be immutable bytes")
    retained = RetainedExecutionAssets(
        tuple(
            (path, role, bytes(content))
            for path, role, content in sorted(snapshot, key=lambda row: row[0].encode("utf-8"))
        )
    )
    validate_execution_asset_identity_v1(retained.descriptor())
    return retained
