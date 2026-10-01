"""Source-sealed request v2 contracts, before production runtime admission."""

import base64
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from jsonschema import ValidationError  # type: ignore[import-untyped]

from tests.contracts import next_runtime_v2_reference, next_runtime_v2_validation
from tests.contracts.next_reference_validation import LIMIT_DEFAULTS, digest, project_config_digest
from tests.contracts.next_runtime_v2_fixtures import sealed_source_fixture_v1
from tests.contracts.test_next_trusted_environment_v2 import profile_members

ROOT = Path(__file__).resolve().parents[2]


def run_context() -> dict[str, Any]:
    return {
        "requested_formats": ["semantic-json"],
        "budget_requested": None,
        "budget_resolved": 500,
        "budget_source": "builtin",
        "stdout_selector": None,
    }


def request_limits() -> dict[str, int]:
    return {**LIMIT_DEFAULTS, "max_entities": 500}


def test_generated_request_array_limit_is_inclusive_and_not_response_aggregate() -> None:
    arrays = [[None] * 100_000, [None] * 100_000]
    next_runtime_v2_validation.validate_request_json_limits_v2(arrays, request_limits())
    arrays[0].append(None)
    with pytest.raises(ValueError, match="max_array_items"):
        next_runtime_v2_validation.validate_request_json_limits_v2(arrays, request_limits())


def test_generated_request_depth_rejects_child_descent_past_64() -> None:
    value: Any = None
    for _ in range(63):
        value = [value]
    next_runtime_v2_validation.validate_request_json_limits_v2(value, request_limits())
    with pytest.raises(ValueError, match="max_json_nesting"):
        next_runtime_v2_validation.validate_request_json_limits_v2([value], request_limits())


@pytest.mark.parametrize("as_key", [False, True])
def test_generated_request_string_bound_counts_utf8_bytes_in_values_and_keys(as_key: bool) -> None:
    text = "é" * (4 * 1024 * 1024)
    value = {text: None} if as_key else text
    next_runtime_v2_validation.validate_request_json_limits_v2(value, request_limits())
    text += "a"
    value = {text: None} if as_key else text
    with pytest.raises(ValueError, match="max_json_string_bytes"):
        next_runtime_v2_validation.validate_request_json_limits_v2(value, request_limits())


def test_stdin_size_boundary_measures_actual_bytes_at_96_mib_not_response_cap() -> None:
    raw = b" " * 100_663_296
    next_runtime_v2_validation.validate_request_stdin_bytes_v2(raw, request_limits())
    with pytest.raises(ValueError, match="max_encoded_stdin_bytes"):
        next_runtime_v2_validation.validate_request_stdin_bytes_v2(raw + b" ", request_limits())


def test_stdin_byte_cap_requires_immutable_bytes_not_a_mutable_view() -> None:
    with pytest.raises(TypeError, match="immutable bytes"):
        next_runtime_v2_validation.validate_request_stdin_bytes_v2(
            cast(Any, bytearray(b"{}")), request_limits()
        )


def test_generated_request_json_rejects_nonstring_object_keys() -> None:
    with pytest.raises(ValueError, match="keys must be strings"):
        next_runtime_v2_validation.validate_request_json_limits_v2({1: None}, request_limits())


def test_request_v2_uses_source_and_asset_owners_without_actual_runtime_fields(
    tmp_path: Path,
) -> None:
    assets = next_runtime_v2_reference.retain_execution_assets_v1(profile_members())
    descriptor = next_runtime_v2_reference.trusted_environment_manifest_v2(assets)[
        "environment_descriptor"
    ]
    seal = sealed_source_fixture_v1(tmp_path, trusted_digest=descriptor["sha256"])
    retained = next_runtime_v2_reference.build_request_frame_v2(
        seal, assets, targets=["path:src/page.tsx"], run_context=run_context()
    )
    wire = retained.record()
    expected = json.loads(
        (ROOT / "tests/fixtures/next_runtime_v2/source-sealed-request.json").read_text(
            encoding="utf-8"
        )
    )
    assert wire == expected
    assert retained.request_id == "364ae1c7150c97541f990bffc4a864ebc405cdf5d0472f3c250434a8f1375197"
    assert len(retained.canonical_bytes) == 3961
    assert hashlib.sha256(retained.canonical_bytes).hexdigest() == (
        "2775c51cb98c3a0c024521007b9c3473c65720ae592597fb9f4c7a9e675ce44f"
    )
    assert wire["schema"] == "code-structure-viz.next-adapter-request/v2"
    assert wire["protocol"] == "code-structure-viz.next-adapter/v2"
    assert wire["adapter_version"] == "0.1.0"
    assert wire["trusted_type_environment"] == descriptor
    assert wire["runtime_requirement"] == {
        "schema": "code-structure-viz.next-node-runtime-requirement/v1",
        "engine": "node",
        "release": "stable",
        "minimum_major": 22,
    }
    assert not {"node_version", "node_candidate", "compatibility_descriptor"}.intersection(wire)
    assert retained.source_seal_id == seal.seal_id
    assert wire["request_id"] == retained.request_id
    page = next(row for row in wire["files"] if row["path"] == "src/page.tsx")
    assert base64.b64decode(page["content_base64"]) == (
        b"export default function Page() { return null; }"
    )
    assert page["effective_role"] == "program"


def test_request_context_budget_cannot_disagree_with_source_seal_limits(tmp_path: Path) -> None:
    assets = next_runtime_v2_reference.retain_execution_assets_v1(profile_members())
    descriptor = next_runtime_v2_reference.trusted_environment_manifest_v2(assets)[
        "environment_descriptor"
    ]
    seal = sealed_source_fixture_v1(tmp_path, trusted_digest=descriptor["sha256"])
    context = run_context()
    context["budget_resolved"] = 499
    with pytest.raises(ValueError, match="context budget"):
        next_runtime_v2_reference.build_request_frame_v2(
            seal, assets, targets=[], run_context=context
        )


def test_request_builder_checks_generated_structure_before_hash_or_schema(tmp_path: Path) -> None:
    assets = next_runtime_v2_reference.retain_execution_assets_v1(profile_members())
    descriptor = next_runtime_v2_reference.trusted_environment_manifest_v2(assets)[
        "environment_descriptor"
    ]
    seal = sealed_source_fixture_v1(tmp_path, trusted_digest=descriptor["sha256"])
    with pytest.raises(ValueError, match="max_json_string_bytes"):
        next_runtime_v2_reference.build_request_frame_v2(
            seal, assets, targets=["a" * 8_388_609], run_context=run_context()
        )


def test_request_builder_rejects_noncanonical_target_order_without_reordering_it(
    tmp_path: Path,
) -> None:
    assets = next_runtime_v2_reference.retain_execution_assets_v1(profile_members())
    descriptor = next_runtime_v2_reference.trusted_environment_manifest_v2(assets)[
        "environment_descriptor"
    ]
    seal = sealed_source_fixture_v1(tmp_path, trusted_digest=descriptor["sha256"])
    with pytest.raises(ValueError, match="source/entity or context"):
        next_runtime_v2_reference.build_request_frame_v2(
            seal,
            assets,
            targets=["path:src/page.tsx", "path:src/global.d.ts"],
            run_context=run_context(),
        )


def test_request_record_recomputes_its_id_from_the_new_preimage(tmp_path: Path) -> None:
    assets = next_runtime_v2_reference.retain_execution_assets_v1(profile_members())
    descriptor = next_runtime_v2_reference.trusted_environment_manifest_v2(assets)[
        "environment_descriptor"
    ]
    seal = sealed_source_fixture_v1(tmp_path, trusted_digest=descriptor["sha256"])
    retained = next_runtime_v2_reference.build_request_frame_v2(
        seal, assets, targets=[], run_context=run_context()
    )
    value = retained.record()
    value["request_id"] = "0" * 64
    with pytest.raises(ValueError, match="request_id"):
        next_runtime_v2_validation.validate_request_record_v2(value)


def test_request_frame_joins_its_actual_source_seal_not_a_second_snapshot(tmp_path: Path) -> None:
    assets = next_runtime_v2_reference.retain_execution_assets_v1(profile_members())
    descriptor = next_runtime_v2_reference.trusted_environment_manifest_v2(assets)[
        "environment_descriptor"
    ]
    seal = sealed_source_fixture_v1(tmp_path, trusted_digest=descriptor["sha256"])
    retained = next_runtime_v2_reference.build_request_frame_v2(
        seal, assets, targets=[], run_context=run_context()
    )
    next_runtime_v2_validation.validate_request_frame_v2(retained, seal, assets)
    other_root = tmp_path / "other"
    other_root.mkdir()
    other_seal = sealed_source_fixture_v1(
        other_root,
        trusted_digest=descriptor["sha256"],
        page_content=b"export default function Changed() { return null; }",
    )
    with pytest.raises(ValueError, match="source seal identity"):
        next_runtime_v2_validation.validate_request_frame_v2(retained, other_seal, assets)


def test_request_owner_stamp_rejects_other_assets_with_the_same_header_and_profile(
    tmp_path: Path,
) -> None:
    members = profile_members()
    assets = next_runtime_v2_reference.retain_execution_assets_v1(members)
    descriptor = next_runtime_v2_reference.trusted_environment_manifest_v2(assets)[
        "environment_descriptor"
    ]
    seal = sealed_source_fixture_v1(tmp_path, trusted_digest=descriptor["sha256"])
    retained = next_runtime_v2_reference.build_request_frame_v2(
        seal, assets, targets=[], run_context=run_context()
    )
    entry = "code_structure_viz/_next_runtime/next-adapter.mjs"
    members[entry] = ("adapter", members[entry][1] + b"// different adapter body\n")
    other_assets = next_runtime_v2_reference.retain_execution_assets_v1(members)
    with pytest.raises(ValueError, match="execution asset identity"):
        next_runtime_v2_validation.validate_request_frame_v2(retained, seal, other_assets)


@pytest.mark.parametrize(
    "change", ["bytes", "membership", "options", "roles", "version", "trust", "limits"]
)
def test_self_consistent_rehashed_request_cannot_replace_its_source_or_asset_owners(
    tmp_path: Path, change: str
) -> None:
    assets = next_runtime_v2_reference.retain_execution_assets_v1(profile_members())
    descriptor = next_runtime_v2_reference.trusted_environment_manifest_v2(assets)[
        "environment_descriptor"
    ]
    seal = sealed_source_fixture_v1(tmp_path, trusted_digest=descriptor["sha256"])
    retained = next_runtime_v2_reference.build_request_frame_v2(
        seal, assets, targets=[], run_context=run_context()
    )
    value = retained.record()
    page = next(row for row in value["files"] if row["path"] == "src/page.tsx")
    if change == "bytes":
        content = b"export default function Changed() { return null; }"
        page.update(
            content_base64=base64.b64encode(content).decode("ascii"),
            size_bytes=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
        )
    elif change == "membership":
        value["files"].remove(page)
        value["projects"][0]["file_ids"].remove(page["id"])
    elif change == "options":
        project = value["projects"][0]
        project["compiler_options"]["jsx"] = "react-jsx"
        project["config_digest"] = project_config_digest(project)
    elif change == "roles":
        page["roles"] = ["context", "program"]
        page["effective_role"] = "context"
    elif change == "version":
        value["adapter_version"] = "0.2.0"
    elif change == "trust":
        value["trusted_type_environment"]["sha256"] = "0" * 64
    elif change == "limits":
        value["limits"]["max_entities"] = 1
        value["run_context"].update(budget_resolved=1, budget_requested=1, budget_source="cli")
    value["request_id"] = digest({key: row for key, row in value.items() if key != "request_id"})
    next_runtime_v2_validation.validate_request_record_v2(value)
    with pytest.raises(ValueError, match=r"source seal|adapter/trusted identity"):
        next_runtime_v2_validation.validate_request_source_binding_v2(value, seal, assets)


def test_request_projection_is_fresh_and_uses_frozen_source_not_later_disk_bytes(
    tmp_path: Path,
) -> None:
    assets = next_runtime_v2_reference.retain_execution_assets_v1(profile_members())
    descriptor = next_runtime_v2_reference.trusted_environment_manifest_v2(assets)[
        "environment_descriptor"
    ]
    seal = sealed_source_fixture_v1(tmp_path, trusted_digest=descriptor["sha256"])
    original = b"export default function Page() { return null; }"
    (tmp_path / "repo/src/page.tsx").write_bytes(b"later disk bytes must not be read")
    context = run_context()
    retained = next_runtime_v2_reference.build_request_frame_v2(
        seal, assets, targets=[], run_context=context
    )
    context["requested_formats"].append("plantuml")
    projection = retained.record()
    projection["files"][0]["content_base64"] = ""
    value = retained.record()
    page = next(row for row in value["files"] if row["path"] == "src/page.tsx")
    assert base64.b64decode(page["content_base64"]) == original
    assert value["run_context"]["requested_formats"] == ["semantic-json"]
    assert not retained.canonical_bytes.endswith(b"\n")
    assert "canonical_bytes" not in repr(retained)
    assert "source_seal_id" not in repr(retained)
    next_runtime_v2_validation.validate_request_frame_v2(retained, seal, assets)


def test_request_owner_constructor_and_duck_frame_are_not_an_admission_route(
    tmp_path: Path,
) -> None:
    with pytest.raises(TypeError, match="build_request_frame_v2"):
        next_runtime_v2_reference.RetainedRequestFrameV2()
    assets = next_runtime_v2_reference.retain_execution_assets_v1(profile_members())
    descriptor = next_runtime_v2_reference.trusted_environment_manifest_v2(assets)[
        "environment_descriptor"
    ]
    seal = sealed_source_fixture_v1(tmp_path, trusted_digest=descriptor["sha256"])
    with pytest.raises(TypeError, match="retained request frame owner"):
        next_runtime_v2_validation.validate_request_frame_v2(
            cast(Any, SimpleNamespace()), seal, assets
        )


@pytest.mark.parametrize(
    "field",
    [
        "node_version",
        "node_candidate",
        "compatibility_descriptor",
        "runtime_toolchain_fingerprint",
        "source_seal_id",
    ],
)
def test_request_schema_rejects_actual_runtime_and_parent_private_fields(
    tmp_path: Path, field: str
) -> None:
    assets = next_runtime_v2_reference.retain_execution_assets_v1(profile_members())
    descriptor = next_runtime_v2_reference.trusted_environment_manifest_v2(assets)[
        "environment_descriptor"
    ]
    seal = sealed_source_fixture_v1(tmp_path, trusted_digest=descriptor["sha256"])
    value = next_runtime_v2_reference.build_request_frame_v2(
        seal, assets, targets=[], run_context=run_context()
    ).record()
    value[field] = "0" * 64
    with pytest.raises(ValidationError, match="Additional properties"):
        next_runtime_v2_validation.validate_request_shape_v2(value)
