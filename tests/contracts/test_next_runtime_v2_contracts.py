"""A-runtime data-only contracts; no Node execution or product admission."""

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import pytest
from jsonschema import Draft202012Validator, ValidationError  # type: ignore[import-untyped]
from referencing import Registry, Resource

from tests.contracts.next_runtime_v2_validation import validate_process_launch_policy_v2

ROOT = Path(__file__).resolve().parents[2]


def load_fixture(name: str) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads((ROOT / "tests/fixtures/next_runtime_v2" / name).read_text(encoding="utf-8")),
    )


def validate_schema(name: str, value: object) -> None:
    registry = Registry()
    for path in (ROOT / "schemas").glob("*.schema.json"):
        schema = json.loads(path.read_text(encoding="utf-8"))
        identifier = schema.get("$id")
        if isinstance(identifier, str):
            registry = registry.with_resource(identifier, Resource.from_contents(schema))
    target = json.loads((ROOT / "schemas" / f"{name}.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(target, registry=registry).validate(value)


def test_prelaunch_policy_accepts_intent_without_actual_node_version() -> None:
    validate_schema("next-process-launch-policy-v2", load_fixture("launch-policy.json"))


def test_policy_rejects_an_argv_executable_different_from_the_measured_candidate() -> None:
    policy = load_fixture("launch-policy.json")
    validate_process_launch_policy_v2(policy)
    mismatched = deepcopy(policy)
    mismatched["argv"][0] = "/opt/other/node"
    with pytest.raises(ValueError, match="candidate"):
        validate_process_launch_policy_v2(mismatched)


@pytest.mark.parametrize("changed", ["runtime_directory", "cwd", "entrypoint"])
def test_policy_binds_the_private_layout_to_one_root(changed: str) -> None:
    policy = load_fixture("launch-policy.json")
    validate_process_launch_policy_v2(policy)
    if changed == "entrypoint":
        policy["argv"][2] = "/private/tmp/other/next-adapter.mjs"
    else:
        policy[changed] = "/private/tmp/other"
    with pytest.raises(ValueError, match="private layout"):
        validate_process_launch_policy_v2(policy)


@pytest.mark.parametrize("placement", ["policy", "node_candidate", "runtime_requirement"])
def test_policy_rejects_actual_node_version_in_prelaunch_records(placement: str) -> None:
    policy = load_fixture("launch-policy.json")
    record = policy if placement == "policy" else policy[placement]
    record["node_version"] = "22.10.0"
    with pytest.raises(ValidationError):
        validate_process_launch_policy_v2(policy)


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("argv", ["/opt/toolchain/node", "/.code-structure-viz/next-adapter.mjs"]),
        ("shell", True),
        (
            "passed_environment",
            {"LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC", "NODE_OPTIONS": "--inspect"},
        ),
        ("fd_inheritance", {"close_fds": True, "allowed": [0, 1, 2, 9]}),
        (
            "process_group",
            {"start_new_session": False, "terminate_scope": "group", "wait_direct_child": True},
        ),
        ("platform", "darwin"),
        ("producer", "production"),
    ],
)
def test_policy_rejects_opened_launch_conditions(field: str, replacement: object) -> None:
    policy = load_fixture("launch-policy.json")
    policy[field] = replacement
    with pytest.raises(ValidationError):
        validate_process_launch_policy_v2(policy)


@pytest.mark.parametrize(
    "path",
    [
        "node",
        "//opt/node",
        "/opt/../node",
        "/opt//node",
        "/opt/./node",
        "/opt/node/",
        "/opt/node\n",
        "/opt/node\\shim",
    ],
)
def test_policy_rejects_unsafe_absolute_path_aliases(path: str) -> None:
    policy = load_fixture("launch-policy.json")
    policy["node_candidate"]["absolute_path"] = path
    policy["argv"][0] = path
    with pytest.raises(ValidationError):
        validate_process_launch_policy_v2(policy)


@pytest.mark.parametrize(
    "name", ["next-node-runtime-requirement-v1", "next-process-launch-policy-v2"]
)
def test_new_policy_schemas_are_closed_valid_draft202012(name: str) -> None:
    schema = json.loads((ROOT / "schemas" / f"{name}.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    assert schema["additionalProperties"] is False
