"""Retained declaration-profile metadata; not compiler or package admission."""

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from jsonschema import ValidationError  # type: ignore[import-untyped]

from tests.contracts import next_runtime_v2_reference, next_runtime_v2_validation
from tests.contracts.next_runtime_v2_fixtures import sealed_source_fixture_v1

ROOT = Path(__file__).resolve().parents[2]
TRUSTED_PREFIX = "code_structure_viz/_next_runtime/trusted/"


def profile_members() -> dict[str, tuple[str, bytes]]:
    members = {
        "code_structure_viz/_next_runtime/next-adapter.mjs": (
            "adapter",
            b"// CodeStructureViz-Adapter-Version: 0.1.0\n",
        )
    }
    for name in ("jsx-runtime.d.ts", "lib.d.ts", "next-dynamic.d.ts", "react.d.ts"):
        members[TRUSTED_PREFIX + name] = (
            "trusted_declaration",
            (ROOT / "tests/fixtures/next_trusted_profile" / name).read_bytes(),
        )
    return members


def test_retained_assets_expose_v2_trusted_metadata_without_host_or_fixture_paths() -> None:
    assets = next_runtime_v2_reference.retain_execution_assets_v1(profile_members())
    manifest: dict[str, Any] = next_runtime_v2_reference.trusted_environment_manifest_v2(assets)
    assert manifest["schema"] == "code-structure-viz.next-trusted-type-environment-manifest/v2"
    assert manifest["environment_descriptor"] == {
        "schema": "code-structure-viz.next-trusted-types/v2",
        "environment_version": "2",
        "semantic_profile_id": "next-trusted-profile-v1",
        "sha256": manifest["environment_descriptor"]["sha256"],
    }
    assert manifest["files"][0] == {
        "package_path": TRUSTED_PREFIX + "jsx-runtime.d.ts",
        "virtual_path": "/.code-structure-viz/trusted/v1/jsx-runtime.d.ts",
        "size_bytes": 206,
        "sha256": "183bcc7eba1b976a64ade01e69fdf5afd1e950875a10b249fb0f4249af31f2f9",
        "license_id": "MIT",
    }
    assert "physical_path" not in str(manifest)
    assert "tests/fixtures" not in str(manifest)


def test_changed_declaration_bytes_cannot_issue_the_unchanged_trusted_profile() -> None:
    members = profile_members()
    path = TRUSTED_PREFIX + "jsx-runtime.d.ts"
    role, content = members[path]
    members[path] = (role, content + b"\n")
    assets = next_runtime_v2_reference.retain_execution_assets_v1(members)
    with pytest.raises(ValueError, match="locked trusted declaration"):
        next_runtime_v2_reference.trusted_environment_manifest_v2(assets)


def test_missing_locked_declaration_is_a_typed_profile_failure_not_a_lookup_error() -> None:
    members = profile_members()
    del members[TRUSTED_PREFIX + "react.d.ts"]
    assets = next_runtime_v2_reference.retain_execution_assets_v1(members)
    with pytest.raises(ValueError, match="locked trusted declaration"):
        next_runtime_v2_reference.trusted_environment_manifest_v2(assets)


@pytest.mark.parametrize("change", ["wrong_role", "extra_declaration"])
def test_trusted_profile_requires_the_exact_declaration_role_set(change: str) -> None:
    members = profile_members()
    if change == "wrong_role":
        path = TRUSTED_PREFIX + "lib.d.ts"
        members[path] = ("typescript_lib", members[path][1])
    else:
        members[TRUSTED_PREFIX + "extra.d.ts"] = ("trusted_declaration", b"export {};\n")
    assets = next_runtime_v2_reference.retain_execution_assets_v1(members)
    with pytest.raises(ValueError, match="declaration role set"):
        next_runtime_v2_reference.trusted_environment_manifest_v2(assets)


def test_manifest_validator_joins_the_complete_retained_declaration_profile() -> None:
    assets = next_runtime_v2_reference.retain_execution_assets_v1(profile_members())
    manifest = next_runtime_v2_reference.trusted_environment_manifest_v2(assets)
    next_runtime_v2_validation.validate_trusted_environment_manifest_v2(manifest, assets)


@pytest.mark.parametrize("digest", ["environment", "manifest"])
def test_trusted_manifest_checks_each_distinct_hash_preimage(digest: str) -> None:
    assets = next_runtime_v2_reference.retain_execution_assets_v1(profile_members())
    manifest = next_runtime_v2_reference.trusted_environment_manifest_v2(assets)
    if digest == "environment":
        manifest["environment_descriptor"]["sha256"] = "0" * 64
    else:
        manifest["manifest_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="preimage"):
        next_runtime_v2_validation.validate_trusted_environment_manifest_v2(manifest, assets)


def rehash_modified_manifest(value: dict[str, Any]) -> None:
    # Negative-vector transport repair, not a known-answer expected hash.
    logical = {
        **{key: item for key, item in value["environment_descriptor"].items() if key != "sha256"},
        **{
            key: item
            for key, item in value.items()
            if key not in {"schema", "environment_descriptor", "files", "manifest_sha256"}
        },
        "files": [
            {key: item for key, item in row.items() if key != "package_path"}
            for row in value["files"]
        ],
    }
    value["environment_descriptor"]["sha256"] = hashlib.sha256(
        json.dumps(logical, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    value["manifest_sha256"] = hashlib.sha256(
        json.dumps(
            {key: item for key, item in value.items() if key != "manifest_sha256"},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


@pytest.mark.parametrize(
    "change",
    ["symbol_signature", "symbol_order", "unicode_table", "license_inventory", "reserved_order"],
)
def test_self_consistent_metadata_cannot_redefine_the_locked_profile(change: str) -> None:
    assets = next_runtime_v2_reference.retain_execution_assets_v1(profile_members())
    manifest = next_runtime_v2_reference.trusted_environment_manifest_v2(assets)
    if change == "symbol_signature":
        manifest["certified_symbols"][0]["signature_digest"] = "0" * 64
    elif change == "symbol_order":
        manifest["certified_symbols"].reverse()
    elif change == "unicode_table":
        manifest["identifier_unicode_table_digest"] = "0" * 64
    elif change == "license_inventory":
        manifest["license_inventory_digest"] = "0" * 64
    else:
        manifest["reserved_module_specifiers"].reverse()
    rehash_modified_manifest(manifest)
    with pytest.raises(ValueError, match="locked trusted metadata"):
        next_runtime_v2_validation.validate_trusted_environment_manifest_v2(manifest, assets)


@pytest.mark.parametrize("entry", ["producer", "validator"])
def test_trusted_metadata_rejects_caller_manufactured_byte_owners(entry: str) -> None:
    assets = next_runtime_v2_reference.retain_execution_assets_v1(profile_members())
    manifest = next_runtime_v2_reference.trusted_environment_manifest_v2(assets)
    fake = cast(Any, SimpleNamespace(descriptor=assets.descriptor))
    with pytest.raises(TypeError, match="retained execution asset owner"):
        if entry == "producer":
            next_runtime_v2_reference.trusted_environment_manifest_v2(fake)
        else:
            next_runtime_v2_validation.validate_trusted_environment_manifest_v2(manifest, fake)


def test_asset_owner_cannot_be_constructed_from_an_unvalidated_caller_tuple() -> None:
    with pytest.raises(TypeError, match="created by retain_execution_assets_v1"):
        next_runtime_v2_reference.RetainedExecutionAssets(())


def test_trusted_profile_has_independently_computed_logical_and_mapping_hashes() -> None:
    # Worked v1 declarations/inventory -> jq -cjnS -> shasum, not this producer.
    assets = next_runtime_v2_reference.retain_execution_assets_v1(profile_members())
    manifest = next_runtime_v2_reference.trusted_environment_manifest_v2(assets)
    assert manifest["environment_descriptor"]["sha256"] == (
        "49458cb6f0f5097d486a2e4f7691f3f80d1e62ea4dbc65ceff00b862ce84e366"
    )
    assert manifest["manifest_sha256"] == (
        "a23265240ebcfa3ba6670f6b0f4982eb96025be093a19ea9b1d74561d32ac31f"
    )


def test_readonly_metadata_reuses_kept_bytes_and_has_no_mutable_projection_alias() -> None:
    members = profile_members()
    assets = next_runtime_v2_reference.retain_execution_assets_v1(members)
    expected = next_runtime_v2_reference.trusted_environment_manifest_v2(assets)
    members.clear()
    modified = next_runtime_v2_reference.trusted_environment_manifest_v2(assets)
    modified["files"][0]["sha256"] = "0" * 64
    modified["certified_symbols"][0]["signature_digest"] = "0" * 64
    modified["environment_descriptor"]["sha256"] = "0" * 64
    assert next_runtime_v2_reference.trusted_environment_manifest_v2(assets) == expected


def test_v2_manifest_preserves_all_four_declarations_and_fourteen_v1_symbols() -> None:
    assets = next_runtime_v2_reference.retain_execution_assets_v1(profile_members())
    manifest = next_runtime_v2_reference.trusted_environment_manifest_v2(assets)
    inventory = json.loads(
        (ROOT / "tests/fixtures/next_trusted_profile/expected_inventory.json").read_text(
            encoding="utf-8"
        )
    )
    expected = sorted(
        [
            {
                key: row[key]
                for key in (
                    "source_kind",
                    "source_name",
                    "export_path",
                    "symbol_kind",
                    "signature_digest",
                )
            }
            for row in inventory
        ],
        key=lambda row: (row["source_kind"], row["source_name"], row["export_path"]),
    )
    projected = [
        {key: item for key, item in row.items() if key != "declaration_sha256"}
        for row in manifest["certified_symbols"]
    ]
    assert len(manifest["files"]) == 4
    assert len(projected) == 14
    assert projected == expected


def test_launch_policy_joins_the_trusted_descriptor_of_its_retained_assets() -> None:
    assets = next_runtime_v2_reference.retain_execution_assets_v1(profile_members())
    manifest = next_runtime_v2_reference.trusted_environment_manifest_v2(assets)
    policy = json.loads(
        (ROOT / "tests/fixtures/next_runtime_v2/launch-policy.json").read_text(encoding="utf-8")
    )
    policy["execution_asset_set_id"] = assets.descriptor()["asset_set_id"]
    policy["adapter"] = assets.adapter_identity()
    policy["trusted_environment_digest"] = manifest["environment_descriptor"]["sha256"]
    next_runtime_v2_validation.validate_launch_policy_trusted_v2(policy, assets)
    policy["trusted_environment_digest"] = "5" * 64
    with pytest.raises(ValueError, match="retained trusted environment"):
        next_runtime_v2_validation.validate_launch_policy_trusted_v2(policy, assets)


@pytest.mark.parametrize("matches_owner", [True, False])
def test_readonly_descriptor_joins_source_seal_without_observing_node(
    tmp_path: Path, matches_owner: bool
) -> None:
    assets = next_runtime_v2_reference.retain_execution_assets_v1(profile_members())
    descriptor = next_runtime_v2_reference.trusted_environment_manifest_v2(assets)[
        "environment_descriptor"
    ]
    seal = sealed_source_fixture_v1(
        tmp_path, trusted_digest=descriptor["sha256"] if matches_owner else "5" * 64
    )
    if matches_owner:
        next_runtime_v2_validation.validate_source_seal_trusted_v2(seal, assets)
        assert seal.final_plan["trusted_environment_digest"] == descriptor["sha256"]
    else:
        with pytest.raises(ValueError, match="retained trusted environment"):
            next_runtime_v2_validation.validate_source_seal_trusted_v2(seal, assets)


@pytest.mark.parametrize("change", ["physical_path", "host_path", "old_descriptor", "old_manifest"])
def test_new_trusted_shape_cannot_impersonate_old_or_host_local_records(change: str) -> None:
    assets = next_runtime_v2_reference.retain_execution_assets_v1(profile_members())
    manifest = next_runtime_v2_reference.trusted_environment_manifest_v2(assets)
    if change == "physical_path":
        manifest["files"][0]["physical_path"] = (
            "tests/fixtures/next_trusted_profile/jsx-runtime.d.ts"
        )
    elif change == "host_path":
        manifest["files"][0]["package_path"] = "/tmp/runtime/trusted/jsx-runtime.d.ts"
    elif change == "old_descriptor":
        manifest["environment_descriptor"].update(
            {"schema": "code-structure-viz.next-trusted-types/v1", "environment_version": "1"}
        )
    else:
        manifest["schema"] = "code-structure-viz.next-trusted-types/v1"
    with pytest.raises(ValidationError):
        next_runtime_v2_validation.validate_trusted_environment_manifest_shape_v2(manifest)


@pytest.mark.parametrize("change", ["mapping_swap", "file_order", "duplicate_path", "file_license"])
def test_rehashed_mapping_cannot_change_fixed_profile_files(change: str) -> None:
    assets = next_runtime_v2_reference.retain_execution_assets_v1(profile_members())
    manifest = next_runtime_v2_reference.trusted_environment_manifest_v2(assets)
    if change == "mapping_swap":
        one, two = manifest["files"][:2]
        one["package_path"], two["package_path"] = two["package_path"], one["package_path"]
    elif change == "file_order":
        manifest["files"].reverse()
    elif change == "duplicate_path":
        manifest["files"][0]["package_path"] = manifest["files"][1]["package_path"]
    else:
        manifest["files"][0]["license_id"] = "Apache-2.0"
    rehash_modified_manifest(manifest)
    with pytest.raises(ValueError, match="locked trusted declaration"):
        next_runtime_v2_validation.validate_trusted_environment_manifest_v2(manifest, assets)


def test_correct_manifest_cannot_be_validated_against_altered_retained_bytes() -> None:
    members = profile_members()
    assets = next_runtime_v2_reference.retain_execution_assets_v1(members)
    manifest = next_runtime_v2_reference.trusted_environment_manifest_v2(assets)
    path = TRUSTED_PREFIX + "react.d.ts"
    members[path] = ("trusted_declaration", members[path][1] + b"\n")
    changed_owner = next_runtime_v2_reference.retain_execution_assets_v1(members)
    with pytest.raises(ValueError, match="retained declaration bytes"):
        next_runtime_v2_validation.validate_trusted_environment_manifest_v2(manifest, changed_owner)
