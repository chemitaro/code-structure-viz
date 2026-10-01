"""Parent-owned analysis intent, not proof of a compiler or selected graph."""

import hashlib
import json
from copy import copy
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from tests.contracts import next_runtime_v2_reference, next_runtime_v2_validation
from tests.contracts.next_reference_validation import canonical_json_bytes, digest
from tests.contracts.next_runtime_v2_fixtures import sealed_source_fixture_v1
from tests.contracts.test_next_request_frame_v2 import run_context
from tests.contracts.test_next_trusted_environment_v2 import profile_members


def test_analysis_context_derives_closed_config_from_seal_assets_and_resolved_intent(
    tmp_path: Path,
) -> None:
    assets = next_runtime_v2_reference.retain_execution_assets_v1(profile_members())
    trusted = next_runtime_v2_reference.trusted_environment_manifest_v2(assets)[
        "environment_descriptor"
    ]
    seal = sealed_source_fixture_v1(tmp_path, trusted_digest=trusted["sha256"])
    context = next_runtime_v2_reference.retain_next_analysis_context_v2(
        seal,
        assets,
        targets=["path:src/page.tsx"],
        upstream_depth=1,
        downstream_depth=2,
        run_context=run_context(),
    )
    plan = seal.final_plan
    expected = {
        "schema": "code-structure-viz.domain-config/next/v1",
        "request_independent": False,
        "projects": plan["projects"],
        "targets": ["path:src/page.tsx"],
        "upstream_depth": 1,
        "downstream_depth": 2,
        "formats": ["semantic-json"],
        "limits": plan["limits"],
        "trusted_environment_digest": trusted["sha256"],
        "source_plan": plan,
        "source_plan_digest": seal.plan_digest,
        "config_resolution": plan["config_resolution"],
    }
    # ASCII corpus: an independently spelled JSON encoder, not the new factory's hash.
    expected_digest = hashlib.sha256(
        json.dumps(expected, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    assert context.domain_config() == {**expected, "domain_config_digest": expected_digest}
    assert context.run_context() == run_context()
    assert context.source_seal() is seal
    assert context.execution_assets() is assets


def test_request_retains_the_exact_analysis_context_without_changing_known_wire(
    tmp_path: Path,
) -> None:
    assets = next_runtime_v2_reference.retain_execution_assets_v1(profile_members())
    trusted = next_runtime_v2_reference.trusted_environment_manifest_v2(assets)[
        "environment_descriptor"
    ]
    seal = sealed_source_fixture_v1(tmp_path, trusted_digest=trusted["sha256"])
    context = next_runtime_v2_reference.retain_next_analysis_context_v2(
        seal,
        assets,
        targets=["path:src/page.tsx"],
        upstream_depth=1,
        downstream_depth=2,
        run_context=run_context(),
    )
    request = next_runtime_v2_reference.build_request_frame_v2(seal, assets, context)
    expected = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "tests/fixtures/next_runtime_v2/source-sealed-request.json"
        ).read_text(encoding="utf-8")
    )
    assert request.analysis_context() is context
    assert request.record() == expected
    assert request.request_id == "364ae1c7150c97541f990bffc4a864ebc405cdf5d0472f3c250434a8f1375197"
    assert len(request.canonical_bytes) == 3961
    assert hashlib.sha256(request.canonical_bytes).hexdigest() == (
        "2775c51cb98c3a0c024521007b9c3473c65720ae592597fb9f4c7a9e675ce44f"
    )


def test_request_refuses_another_analysis_intent_even_when_child_wire_is_identical(
    tmp_path: Path,
) -> None:
    assets = next_runtime_v2_reference.retain_execution_assets_v1(profile_members())
    trusted = next_runtime_v2_reference.trusted_environment_manifest_v2(assets)[
        "environment_descriptor"
    ]
    seal = sealed_source_fixture_v1(tmp_path, trusted_digest=trusted["sha256"])
    original, changed = [
        next_runtime_v2_reference.retain_next_analysis_context_v2(
            seal,
            assets,
            targets=["path:src/page.tsx"],
            upstream_depth=1,
            downstream_depth=depth,
            run_context=run_context(),
        )
        for depth in (1, 2)
    ]
    request = next_runtime_v2_reference.build_request_frame_v2(seal, assets, original)
    other = next_runtime_v2_reference.build_request_frame_v2(seal, assets, changed)
    assert request.canonical_bytes == other.canonical_bytes
    assert original.domain_config() != changed.domain_config()
    forged = copy(request)
    object.__setattr__(forged, "_analysis_context", changed)
    with pytest.raises(ValueError, match="analysis context identity"):
        next_runtime_v2_validation.validate_request_frame_v2(forged, seal, assets)


def context_inputs(
    tmp_path: Path,
) -> tuple[
    next_runtime_v2_reference.RetainedNextAnalysisContextV2,
    next_runtime_v2_reference.RetainedExecutionAssets,
]:
    assets = next_runtime_v2_reference.retain_execution_assets_v1(profile_members())
    trusted = next_runtime_v2_reference.trusted_environment_manifest_v2(assets)[
        "environment_descriptor"
    ]
    seal = sealed_source_fixture_v1(tmp_path, trusted_digest=trusted["sha256"])
    context = next_runtime_v2_reference.retain_next_analysis_context_v2(
        seal, assets, targets=[], upstream_depth=1, downstream_depth=2, run_context=run_context()
    )
    return context, assets


def test_analysis_context_requires_its_nominal_constructor_and_same_owners(tmp_path: Path) -> None:
    context, assets = context_inputs(tmp_path)
    seal = context.source_seal()
    with pytest.raises(TypeError, match="retain_next_analysis_context_v2"):
        next_runtime_v2_reference.RetainedNextAnalysisContextV2()
    with pytest.raises(TypeError, match="retained analysis context"):
        next_runtime_v2_validation.validate_next_analysis_context_v2(
            cast(Any, SimpleNamespace()), seal, assets
        )
    with pytest.raises(ValueError, match="source/asset owners"):
        next_runtime_v2_validation.validate_next_analysis_context_v2(
            context, seal, next_runtime_v2_reference.retain_execution_assets_v1(profile_members())
        )
    with pytest.raises(TypeError, match="targets"):
        next_runtime_v2_reference.build_request_frame_v2(
            seal,
            assets,
            targets=[],
            run_context=run_context(),  # type: ignore[call-arg]
        )


def test_analysis_context_owns_input_and_fresh_projections_without_resource_relookup(
    tmp_path: Path,
) -> None:
    context, assets = context_inputs(tmp_path)
    before = context.domain_config()
    context.domain_config()["source_plan"]["limits"]["max_entities"] = 1
    context.run_context()["requested_formats"].append("plantuml")
    context.analysis_intent()["downstream_depth"] = 0
    (tmp_path / "repo/tsconfig.json").write_bytes(b"changed after seal")
    assert context.domain_config() == before
    assert context.run_context() == run_context()
    assert context.analysis_intent()["downstream_depth"] == 2
    assert repr(context) == "RetainedNextAnalysisContextV2()"
    next_runtime_v2_validation.validate_next_analysis_context_v2(
        context, context.source_seal(), assets
    )


@pytest.mark.parametrize("field", ["depth", "source", "digest", "trust", "extra"])
def test_rehashed_public_config_cannot_replace_the_retained_parent_intent(
    tmp_path: Path,
    field: str,
) -> None:
    context, assets = context_inputs(tmp_path)
    config = context.domain_config()
    if field == "depth":
        config["downstream_depth"] = 3
    elif field == "source":
        config["source_plan_digest"] = "0" * 64
    elif field == "digest":
        config["domain_config_digest"] = "0" * 64
    elif field == "trust":
        config["trusted_environment_digest"] = "0" * 64
    else:
        config["caller_hash"] = "0" * 64
    if field != "digest":
        config["domain_config_digest"] = digest(
            {key: value for key, value in config.items() if key != "domain_config_digest"}
        )
    forged = copy(context)
    object.__setattr__(forged, "_config_bytes", canonical_json_bytes(config))
    with pytest.raises(ValueError, match="retained owners/intent"):
        next_runtime_v2_validation.validate_next_analysis_context_v2(
            forged, context.source_seal(), assets
        )


@pytest.mark.parametrize("depth", [-1, 65, True, "1", None])
def test_analysis_context_does_not_default_or_coerce_invalid_depths(
    tmp_path: Path,
    depth: Any,
) -> None:
    context, assets = context_inputs(tmp_path)
    with pytest.raises(ValueError, match="depth"):
        next_runtime_v2_reference.retain_next_analysis_context_v2(
            context.source_seal(),
            assets,
            targets=[],
            upstream_depth=depth,
            downstream_depth=1,
            run_context=run_context(),
        )
