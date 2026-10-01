"""Small data-only A-runtime validators, independent of the historical v1 lane."""

import json
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[2]


def validate_process_launch_policy_v2(value: dict[str, Any]) -> None:
    """Validate the closed prelaunch policy and its candidate/argv join."""

    registry = Registry()
    for path in (ROOT / "schemas").glob("*.schema.json"):
        schema = json.loads(path.read_text(encoding="utf-8"))
        identifier = schema.get("$id")
        if isinstance(identifier, str):
            registry = registry.with_resource(identifier, Resource.from_contents(schema))
    target = cast(
        dict[str, Any],
        json.loads(
            (ROOT / "schemas/next-process-launch-policy-v2.schema.json").read_text(encoding="utf-8")
        ),
    )
    Draft202012Validator(target, registry=registry).validate(value)
    if value["argv"][0] != value["node_candidate"]["absolute_path"]:
        raise ValueError("argv executable differs from the measured candidate")
    root = value["private_root"]
    if (
        value["runtime_directory"] != f"{root}/runtime"
        or value["cwd"] != f"{root}/cwd"
        or value["argv"][2] != f"{root}/runtime/next-adapter.mjs"
    ):
        raise ValueError("private layout does not match the owned runtime/cwd/entrypoint")
