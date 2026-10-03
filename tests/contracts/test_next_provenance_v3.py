"""V3 named observations from existing runtime owners and the matching Core-v3."""

import hashlib
import json
from copy import deepcopy
from importlib import import_module, util
from pathlib import Path

import pytest
from jsonschema import ValidationError  # type: ignore[import-untyped]

from tests.contracts.next_provenance_v3_reference import runtime_provenance_v3
from tests.contracts.next_provenance_v3_validation import validate_runtime_provenance_v3
from tests.contracts.next_runtime_v2_reference import RetainedRuntimeResultV2
from tests.contracts.next_semantic_core_v3_reference import (
    ValidatedSemanticDecisionV3,
    decide_semantic_candidate_v3,
)
from tests.contracts.test_next_core_failure_v2 import runtime_for_core_wire
from tests.contracts.test_next_provenance_v2 import SLOTS
from tests.contracts.test_next_semantic_core_v3 import core_inputs_v3


def test_provenance_wraps_the_matching_core_in_seventeen_v3_slots(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    runtime = runtime_for_core_wire(seal, assets, request, policy, wire)
    candidate = runtime.transport_candidate()
    assert candidate is not None
    core = decide_semantic_candidate_v3(candidate, seal, assets)
    assert core.gate()["payload_available"] is True
    module = "tests.contracts.next_provenance_v3_reference"
    assert util.find_spec(module) is not None, "matching Core-v3 has no versioned provenance"
    value = import_module(module).runtime_provenance_v3(runtime, semantic_decision=core)
    assert value["schema"] == "code-structure-viz.next-provenance/v3"
    assert (value["kind"], value["stage"], value["failure_code"]) == (
        "request_bound_success",
        None,
        None,
    )
    assert set(value["observed"]) == set(SLOTS) and len(value["observed"]) == 17
    preimage = {
        "schema": "code-structure-viz.next-observation/v3",
        "version": 3,
        "field": "compatibility",
        "value": core.compatibility_descriptor(),
    }
    expected = hashlib.sha256(
        json.dumps(preimage, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    assert value["observed"]["compatibility"] == {
        "state": "observed",
        "value": {
            "schema": "code-structure-viz.next-observation/v3",
            "version": 3,
            "sha256": expected,
        },
    }


def matching_runtime_core_v3(
    tmp_path: Path,
) -> tuple[RetainedRuntimeResultV2, ValidatedSemanticDecisionV3]:
    seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
    runtime = runtime_for_core_wire(seal, assets, request, policy, wire)
    candidate = runtime.transport_candidate()
    assert candidate is not None
    return runtime, decide_semantic_candidate_v3(candidate, seal, assets)


@pytest.mark.parametrize("slot", ["semantic_payload", "compatibility", "model", "budget"])
def test_v3_suffix_hash_is_field_bound_and_independently_rederived(
    tmp_path: Path, slot: str
) -> None:
    runtime, core = matching_runtime_core_v3(tmp_path)
    value = runtime_provenance_v3(runtime, semantic_decision=core)
    payload = core.transport_candidate().semantic_payload()
    actual = {
        "semantic_payload": payload,
        "compatibility": core.compatibility_descriptor(),
        "model": payload["model"],
        "budget": core.gate(),
    }[slot]
    expected = hashlib.sha256(
        json.dumps(
            {
                "schema": "code-structure-viz.next-observation/v3",
                "version": 3,
                "field": slot,
                "value": actual,
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode()
    ).hexdigest()
    assert value["observed"][slot]["value"]["sha256"] == expected
    value["observed"][slot] = deepcopy(value["observed"]["request"])
    with pytest.raises(ValueError, match="digest"):
        validate_runtime_provenance_v3(value, runtime, semantic_decision=core)


@pytest.mark.parametrize(
    "mutation", ["old_wrapper", "float_version", "bool_version", "missing_slot", "host_path"]
)
def test_v3_provenance_rejects_downgrade_native_type_and_private_mutations(
    tmp_path: Path, mutation: str
) -> None:
    runtime, core = matching_runtime_core_v3(tmp_path)
    value = runtime_provenance_v3(runtime, semantic_decision=core)
    if mutation == "missing_slot":
        del value["observed"]["model"]
    elif mutation == "host_path":
        value["observed"]["request"]["value"]["cwd"] = "/private/secret"
    else:
        row = value["observed"]["request"]["value"]
        if mutation == "old_wrapper":
            row.update(schema="code-structure-viz.next-observation/v2", version=2)
        else:
            row["version"] = 3.0 if mutation == "float_version" else True
    with pytest.raises((ValueError, ValidationError)):
        validate_runtime_provenance_v3(value, runtime, semantic_decision=core)


def test_provenance_refuses_equal_content_core_from_another_exchange(tmp_path: Path) -> None:
    first_path, second_path = tmp_path / "first", tmp_path / "second"
    first_path.mkdir()
    second_path.mkdir()
    first_runtime, first_core = matching_runtime_core_v3(first_path)
    _, second_core = matching_runtime_core_v3(second_path)
    assert first_core.request_id == second_core.request_id
    with pytest.raises(ValueError, match="same runtime owner"):
        runtime_provenance_v3(first_runtime, semantic_decision=second_core)
