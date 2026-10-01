"""A-runtime data-only contracts; no Node execution or product admission."""

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import pytest
from jsonschema import Draft202012Validator, ValidationError  # type: ignore[import-untyped]
from referencing import Registry, Resource

from tests.contracts import next_runtime_v2_reference
from tests.contracts.next_runtime_v2_validation import (
    validate_execution_asset_identity_v1,
    validate_execution_assets_v1,
    validate_launch_policy_assets_v2,
    validate_process_launch_policy_v2,
)

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


def test_execution_asset_identity_has_a_closed_portable_shape() -> None:
    validate_schema("next-execution-assets-v1", load_fixture("execution-assets.json"))


def test_retained_asset_bytes_produce_the_worked_identity_and_staging_content() -> None:
    # Synthetic bytes, not a runnable compiler or a complete package profile.
    members = {
        "code_structure_viz/_next_runtime/typescript/typescript.cjs": (
            "typescript_lib",
            b"reference compiler\n",
        ),
        "code_structure_viz/_next_runtime/next-adapter.mjs": (
            "adapter",
            b"// CodeStructureViz-Adapter-Version: 0.1.0\n",
        ),
    }
    assets = next_runtime_v2_reference.retain_execution_assets_v1(members)
    assert assets.descriptor() == load_fixture("execution-assets.json")
    assert assets.staging_members() == (
        (
            "code_structure_viz/_next_runtime/next-adapter.mjs",
            b"// CodeStructureViz-Adapter-Version: 0.1.0\n",
        ),
        (
            "code_structure_viz/_next_runtime/typescript/typescript.cjs",
            b"reference compiler\n",
        ),
    )


def test_execution_asset_identity_rejects_a_wrong_self_digest() -> None:
    descriptor = load_fixture("execution-assets.json")
    validate_execution_asset_identity_v1(descriptor)
    descriptor["asset_set_id"] = "0" * 64
    with pytest.raises(ValueError, match="asset_set_id"):
        validate_execution_asset_identity_v1(descriptor)


def test_execution_asset_identity_rejects_reordered_members_even_with_a_matching_digest() -> None:
    descriptor = load_fixture("execution-assets.json")
    descriptor["members"].reverse()
    preimage = json.dumps(
        {key: value for key, value in descriptor.items() if key != "asset_set_id"},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    descriptor["asset_set_id"] = hashlib.sha256(preimage).hexdigest()
    with pytest.raises(ValueError, match="order"):
        validate_execution_asset_identity_v1(descriptor)


def test_execution_asset_identity_rejects_duplicate_paths_with_different_metadata() -> None:
    descriptor = load_fixture("execution-assets.json")
    duplicate = deepcopy(descriptor["members"][0])
    duplicate["sha256"] = "0" * 64
    descriptor["members"].insert(1, duplicate)
    preimage = json.dumps(
        {key: value for key, value in descriptor.items() if key != "asset_set_id"},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    descriptor["asset_set_id"] = hashlib.sha256(preimage).hexdigest()
    with pytest.raises(ValueError, match="duplicate"):
        validate_execution_asset_identity_v1(descriptor)


def test_execution_asset_identity_requires_its_entrypoint_with_the_adapter_role() -> None:
    descriptor = load_fixture("execution-assets.json")
    descriptor["members"][0]["role"] = "typescript_lib"
    preimage = json.dumps(
        {key: value for key, value in descriptor.items() if key != "asset_set_id"},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    descriptor["asset_set_id"] = hashlib.sha256(preimage).hexdigest()
    with pytest.raises(ValueError, match="entrypoint"):
        validate_execution_asset_identity_v1(descriptor)


def test_retained_asset_owner_rejects_an_invalid_entrypoint_identity() -> None:
    with pytest.raises(ValueError, match="entrypoint"):
        next_runtime_v2_reference.retain_execution_assets_v1(
            {"code_structure_viz/_next_runtime/other.mjs": ("adapter", b"other\n")}
        )


def test_asset_identity_and_staging_do_not_follow_later_caller_mutations() -> None:
    path = "code_structure_viz/_next_runtime/next-adapter.mjs"
    original = b"// CodeStructureViz-Adapter-Version: 0.1.0\n"
    members = {path: ("adapter", original)}
    assets = next_runtime_v2_reference.retain_execution_assets_v1(members)
    first = assets.descriptor()
    members[path] = ("adapter", b"changed\n")
    exposed = assets.descriptor()
    exposed["members"][0]["sha256"] = "0" * 64
    assert assets.descriptor() == first
    assert assets.staging_members() == ((path, original),)


def test_asset_admission_rejects_rehashed_metadata_that_disagrees_with_retained_bytes() -> None:
    assets = next_runtime_v2_reference.retain_execution_assets_v1(
        {
            "code_structure_viz/_next_runtime/next-adapter.mjs": (
                "adapter",
                b"// CodeStructureViz-Adapter-Version: 0.1.0\n",
            )
        }
    )
    descriptor = assets.descriptor()
    validate_execution_assets_v1(descriptor, assets)
    descriptor["members"][0]["sha256"] = "0" * 64
    preimage = json.dumps(
        {key: value for key, value in descriptor.items() if key != "asset_set_id"},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    descriptor["asset_set_id"] = hashlib.sha256(preimage).hexdigest()
    validate_execution_asset_identity_v1(descriptor)
    with pytest.raises(ValueError, match="retained bytes"):
        validate_execution_assets_v1(descriptor, assets)


def test_asset_retention_rejects_non_byte_content_instead_of_manufacturing_bytes() -> None:
    with pytest.raises(TypeError, match="bytes"):
        next_runtime_v2_reference.retain_execution_assets_v1(
            {"code_structure_viz/_next_runtime/next-adapter.mjs": ("adapter", cast(bytes, 3))}
        )


def test_adapter_identity_is_derived_from_the_retained_entrypoint_header_and_bytes() -> None:
    assets = next_runtime_v2_reference.retain_execution_assets_v1(
        {
            "code_structure_viz/_next_runtime/next-adapter.mjs": (
                "adapter",
                b"// CodeStructureViz-Adapter-Version: 2.3.4\n",
            )
        }
    )
    assert assets.adapter_identity() == {
        "protocol": "code-structure-viz.next-adapter/v2",
        "version": "2.3.4",
        "sha256": "9bfc66a39766ca565a16a6355df0bf2a14f61efd3bbe0f573468debb86b0e0df",
        "entrypoint_member": "code_structure_viz/_next_runtime/next-adapter.mjs",
    }


def test_adapter_identity_rejects_a_second_version_marker_anywhere_in_retained_content() -> None:
    assets = next_runtime_v2_reference.retain_execution_assets_v1(
        {
            "code_structure_viz/_next_runtime/next-adapter.mjs": (
                "adapter",
                b"// CodeStructureViz-Adapter-Version: 0.1.0\n"
                b"// CodeStructureViz-Adapter-Version: 2.3.4\n",
            )
        }
    )
    with pytest.raises(ValueError, match="marker"):
        assets.adapter_identity()


@pytest.mark.parametrize(
    "content",
    [
        b"\xef\xbb\xbf// CodeStructureViz-Adapter-Version: 0.1.0\n",
        b"// CodeStructureViz-Adapter-Version: 0.1.0\r\n",
        b"// CodeStructureViz-Adapter-Version: 00.1.0\n",
        b"// CodeStructureViz-Adapter-Version: 0.1.0-rc.1\n",
        b"// CodeStructureViz-Adapter-Version: 0.1.0+build\n",
        b"// CodeStructureViz-Adapter-Version:  0.1.0\n",
        b"// other\n// CodeStructureViz-Adapter-Version: 0.1.0\n",
    ],
)
def test_adapter_identity_preserves_the_frozen_header_grammar(content: bytes) -> None:
    assets = next_runtime_v2_reference.retain_execution_assets_v1(
        {"code_structure_viz/_next_runtime/next-adapter.mjs": ("adapter", content)}
    )
    with pytest.raises(ValueError, match="header"):
        assets.adapter_identity()


def test_policy_accepts_adapter_identity_derived_from_its_retained_asset_owner() -> None:
    assets = next_runtime_v2_reference.retain_execution_assets_v1(
        {
            "code_structure_viz/_next_runtime/next-adapter.mjs": (
                "adapter",
                b"// CodeStructureViz-Adapter-Version: 0.1.0\n",
            )
        }
    )
    policy = load_fixture("launch-policy.json")
    policy["adapter"] = assets.adapter_identity()
    policy["execution_asset_set_id"] = assets.descriptor()["asset_set_id"]
    validate_process_launch_policy_v2(policy)


def test_policy_asset_join_rejects_identity_not_derived_from_the_retained_owner() -> None:
    assets = next_runtime_v2_reference.retain_execution_assets_v1(
        {
            "code_structure_viz/_next_runtime/next-adapter.mjs": (
                "adapter",
                b"// CodeStructureViz-Adapter-Version: 0.1.0\n",
            )
        }
    )
    policy = load_fixture("launch-policy.json")
    policy["adapter"] = assets.adapter_identity()
    policy["execution_asset_set_id"] = assets.descriptor()["asset_set_id"]
    validate_launch_policy_assets_v2(policy, assets)
    policy["execution_asset_set_id"] = "0" * 64
    with pytest.raises(ValueError, match="retained owner"):
        validate_launch_policy_assets_v2(policy, assets)


def test_policy_asset_join_rejects_a_free_adapter_version_even_if_the_hash_matches() -> None:
    assets = next_runtime_v2_reference.retain_execution_assets_v1(
        {
            "code_structure_viz/_next_runtime/next-adapter.mjs": (
                "adapter",
                b"// CodeStructureViz-Adapter-Version: 0.1.0\n",
            )
        }
    )
    policy = load_fixture("launch-policy.json")
    policy["adapter"] = assets.adapter_identity()
    policy["execution_asset_set_id"] = assets.descriptor()["asset_set_id"]
    policy["adapter"]["version"] = "9.9.9"
    with pytest.raises(ValueError, match="adapter identity"):
        validate_launch_policy_assets_v2(policy, assets)


@pytest.mark.parametrize(
    "path",
    [
        "code_structure_viz/_next_runtime/../other.mjs",
        "code_structure_viz/_next_runtime/typescript/../../escape.mjs",
        "code_structure_viz/_next_runtime/./other.mjs",
        "code_structure_viz/_next_runtime//other.mjs",
        "code_structure_viz/_next_runtime/other.mjs\n",
        "code_structure_viz/_next_runtime/other\\name.mjs",
        "/code_structure_viz/_next_runtime/other.mjs",
        "other/entrypoint.mjs",
    ],
)
def test_execution_asset_identity_rejects_unsafe_member_paths(path: str) -> None:
    descriptor = load_fixture("execution-assets.json")
    descriptor["members"][1]["package_path"] = path
    with pytest.raises(ValidationError):
        validate_execution_asset_identity_v1(descriptor)


@pytest.mark.parametrize("field", ["absolute_path", "inode", "pid", "fd"])
def test_execution_asset_identity_excludes_host_observation_fields(field: str) -> None:
    descriptor = load_fixture("execution-assets.json")
    descriptor["members"][0][field] = 42
    with pytest.raises(ValidationError):
        validate_execution_asset_identity_v1(descriptor)


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
    "name",
    [
        "next-node-runtime-requirement-v1",
        "next-process-launch-policy-v2",
        "next-execution-assets-v1",
    ],
)
def test_new_policy_schemas_are_closed_valid_draft202012(name: str) -> None:
    schema = json.loads((ROOT / "schemas" / f"{name}.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    assert schema["additionalProperties"] is False
