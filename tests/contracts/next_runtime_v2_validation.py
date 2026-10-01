"""Small data-only A-runtime validators, independent of the historical v1 lane."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]
from referencing import Registry, Resource

if TYPE_CHECKING:
    from tests.contracts.next_runtime_v2_reference import RetainedExecutionAssets

ROOT = Path(__file__).resolve().parents[2]


def _validate_schema(name: str, value: object) -> None:
    registry = Registry()
    for path in (ROOT / "schemas").glob("*.schema.json"):
        schema = json.loads(path.read_text(encoding="utf-8"))
        identifier = schema.get("$id")
        if isinstance(identifier, str):
            registry = registry.with_resource(identifier, Resource.from_contents(schema))
    target = cast(
        dict[str, Any],
        json.loads((ROOT / "schemas" / f"{name}.schema.json").read_text(encoding="utf-8")),
    )
    Draft202012Validator(target, registry=registry).validate(value)


def validate_execution_asset_identity_v1(value: dict[str, Any]) -> None:
    """Validate portable identity; this does not certify installed member bytes."""

    _validate_schema("next-execution-assets-v1", value)
    paths = [member["package_path"] for member in value["members"]]
    if len(paths) != len(set(paths)):
        raise ValueError("execution asset members have duplicate package paths")
    if paths != sorted(paths, key=lambda path: path.encode("utf-8")):
        raise ValueError("execution asset members are not in UTF-8 package-path order")
    if not any(
        member["package_path"] == value["entrypoint_member"] and member["role"] == "adapter"
        for member in value["members"]
    ):
        raise ValueError("execution asset entrypoint is missing or not an adapter")
    preimage = json.dumps(
        {key: item for key, item in value.items() if key != "asset_set_id"},
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    if value["asset_set_id"] != hashlib.sha256(preimage).hexdigest():
        raise ValueError("asset_set_id differs from the portable content preimage")


def validate_execution_assets_v1(value: dict[str, Any], owner: RetainedExecutionAssets) -> None:
    """Admit a portable identity only when its retained byte owner also agrees."""

    validate_execution_asset_identity_v1(value)
    if value != owner.descriptor():
        raise ValueError("execution asset metadata differs from its retained bytes")


def validate_process_launch_policy_v2(value: dict[str, Any]) -> None:
    """Validate the closed prelaunch policy and its candidate/argv join."""

    _validate_schema("next-process-launch-policy-v2", value)
    if value["argv"][0] != value["node_candidate"]["absolute_path"]:
        raise ValueError("argv executable differs from the measured candidate")
    root = value["private_root"]
    if (
        value["runtime_directory"] != f"{root}/runtime"
        or value["cwd"] != f"{root}/cwd"
        or value["argv"][2] != f"{root}/runtime/next-adapter.mjs"
    ):
        raise ValueError("private layout does not match the owned runtime/cwd/entrypoint")


def validate_launch_policy_assets_v2(value: dict[str, Any], owner: RetainedExecutionAssets) -> None:
    """Validate a policy against the byte owner, not separately supplied metadata."""

    validate_process_launch_policy_v2(value)
    descriptor = owner.descriptor()
    validate_execution_assets_v1(descriptor, owner)
    if value["execution_asset_set_id"] != descriptor["asset_set_id"]:
        raise ValueError("policy execution asset identity differs from its retained owner")
    if value["adapter"] != owner.adapter_identity():
        raise ValueError("policy adapter identity differs from its retained entrypoint")
