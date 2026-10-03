"""Requested candidates do not become final selected publication certificates."""

import json
from copy import copy, deepcopy
from importlib import import_module, util
from pathlib import Path

import pytest
from jsonschema import ValidationError  # type: ignore[import-untyped]

from tests.contracts import next_runtime_v2_reference as runtime_reference
from tests.contracts.next_publication_candidates_v3_reference import (
    project_request_bound_publication_candidates_v3,
    retain_request_bound_publication_candidates_v3,
)
from tests.contracts.next_publication_candidates_v3_validation import (
    validate_request_bound_publication_candidates_v3,
)
from tests.contracts.next_reference_validation import canonical_json_bytes
from tests.contracts.next_run_decision_v3_reference import retain_request_bound_run_decision_v3
from tests.contracts.next_semantic_core_v3_reference import (
    decide_semantic_candidate_v3,
    inspect_semantic_candidate_v3,
)
from tests.contracts.test_next_core_failure_v2 import runtime_for_core_wire
from tests.contracts.test_next_exchange_v2 import exchange_evidence
from tests.contracts.test_next_provenance_v3 import matching_runtime_core_v3
from tests.contracts.test_next_semantic_core_v3 import (
    SOURCE_BYTES,
    core_inputs_v3,
    exclude_value_module_with_root_v3,
    omit_selected_button_module_v3,
)


def test_selector_does_not_shrink_requested_candidate_set(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(
        tmp_path, requested_formats=["semantic-json", "plantuml"], stdout_selector="next:plantuml"
    )
    runtime = runtime_for_core_wire(seal, assets, request, policy, wire)
    candidate = runtime.transport_candidate()
    assert candidate is not None
    core = decide_semantic_candidate_v3(candidate, seal, assets)
    run = retain_request_bound_run_decision_v3(runtime, semantic_decision=core)
    assert run.record()["context"]["run_context"]["stdout_selector"] == "next:plantuml"
    module = "tests.contracts.next_publication_candidates_v3_reference"
    assert util.find_spec(module) is not None, "retained run3 has no requested candidate owner"
    factory = import_module(module)
    owner = factory.retain_request_bound_publication_candidates_v3(run)
    value = factory.project_request_bound_publication_candidates_v3(owner)
    assert owner.run_decision() is run
    assert value["schema"] == "code-structure-viz.next-publication-candidates/v3"
    assert value["version"] == 3 and value["run_decision"] == run.record()
    assert [item["format"] for item in value["artifacts"]] == ["semantic-json", "plantuml"]
    assert all(artifact.semantic_decision() is core for artifact in owner.artifacts())
    assert owner.artifact_bytes("semantic-json") is not None
    assert owner.artifact_bytes("plantuml") is not None
    capture = runtime.observation()["capture"]
    assert value["capture_measurements"]["adapter_stdout"] == {
        "captured_bytes": capture["stdout_bytes"],
        "capture_retained_bytes": capture["stdout_retained_bytes"],
        "eof": capture["stdout_eof"],
        "limit_bytes": 16_777_216,
    }


@pytest.mark.parametrize(
    "formats,selector",
    [
        (["semantic-json"], "manifest"),
        (["plantuml"], None),
        (["semantic-json", "plantuml"], None),
    ],
)
def test_candidates_keep_requested_format_order_independent_of_selector(
    tmp_path: Path,
    formats: list[str],
    selector: str | None,
) -> None:
    seal, assets, request, policy, wire = core_inputs_v3(
        tmp_path, requested_formats=formats, stdout_selector=selector
    )
    runtime = runtime_for_core_wire(seal, assets, request, policy, wire)
    candidate = runtime.transport_candidate()
    assert candidate is not None
    core = decide_semantic_candidate_v3(candidate, seal, assets)
    run = retain_request_bound_run_decision_v3(runtime, semantic_decision=core)
    owner = retain_request_bound_publication_candidates_v3(run)
    assert [row["format"] for row in owner.record()["artifacts"]] == formats
    for fmt in ("semantic-json", "plantuml"):
        assert (owner.artifact_bytes(fmt) is not None) is (fmt in formats)


def test_reversed_requested_formats_are_rejected_before_candidate_admission(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="v1 invariants"):
        core_inputs_v3(tmp_path, requested_formats=["plantuml", "semantic-json"])


@pytest.mark.parametrize("cause", ["target", "source", "rejected", "runtime"])
def test_unavailable_or_unadmitted_runs_never_create_candidates(tmp_path: Path, cause: str) -> None:
    sources = (
        {**SOURCE_BYTES, "src/value.ts": SOURCE_BYTES["src/value.ts"] + b"require(variable);\n"}
        if cause == "source"
        else None
    )
    seal, assets, request, policy, wire = core_inputs_v3(
        tmp_path,
        sources=sources,
        targets=["path:src/button.tsx"] if cause == "target" else [],
    )
    if cause == "target":
        omit_selected_button_module_v3(wire)
    elif cause == "source":
        exclude_value_module_with_root_v3(wire, request, "parse_file")
    elif cause == "rejected":
        wire["semantic_payload"]["model_digest"] = "0" * 64
    if cause == "runtime":
        wire["semantic_payload"] = None
        wire["control"].update(
            result_kind="protocol_failure",
            runtime=None,
            binding={"state": "unbound", "request_id": None},
        )
        response = runtime_reference.retain_response_frame_v2(
            json.dumps(wire).encode(), limits=request.record()["limits"]
        )
        evidence = exchange_evidence(policy, request, response)
        evidence["exit_code"] = 65
        observation = runtime_reference.reference_process_observation_v2(policy, evidence)
        runtime = runtime_reference.retain_runtime_result_v2(
            seal, assets, request, policy, observation, response
        )
        core = None
    else:
        runtime = runtime_for_core_wire(seal, assets, request, policy, wire)
        candidate = runtime.transport_candidate()
        assert candidate is not None
        core = inspect_semantic_candidate_v3(candidate, seal, assets)
    run = retain_request_bound_run_decision_v3(runtime, semantic_decision=core)
    owner = retain_request_bound_publication_candidates_v3(run)
    assert owner.artifacts() == () and owner.record()["artifacts"] == []
    assert owner.artifact_bytes("semantic-json") is owner.artifact_bytes("plantuml") is None


@pytest.mark.parametrize("mutation", ["capture", "private", "version", "foreign_artifact"])
def test_candidates_independently_reject_rehashed_cache_substitution(
    tmp_path: Path, mutation: str
) -> None:
    runtime, core = matching_runtime_core_v3(tmp_path)
    run = retain_request_bound_run_decision_v3(runtime, semantic_decision=core)
    original = retain_request_bound_publication_candidates_v3(run)
    owner = copy(original)
    value = deepcopy(owner.record())
    if mutation == "capture":
        value["capture_measurements"]["adapter_stdout"]["captured_bytes"] += 1
    elif mutation == "private":
        value["artifacts"][0]["content_base64"] = "private"
    elif mutation == "version":
        value["version"] = 3.0
    else:
        other_path = tmp_path / "other"
        other_path.mkdir()
        other_runtime, other_core = matching_runtime_core_v3(other_path)
        other_run = retain_request_bound_run_decision_v3(
            other_runtime, semantic_decision=other_core
        )
        other_owner = retain_request_bound_publication_candidates_v3(other_run)
        assert original.record() == other_owner.record()
        object.__setattr__(owner, "_artifacts", other_owner.artifacts())
    object.__setattr__(
        owner, "_record_bytes", json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    )
    with pytest.raises((ValueError, ValidationError)):
        project_request_bound_publication_candidates_v3(owner)


def test_candidates_refuse_an_equal_content_but_foreign_run_owner(tmp_path: Path) -> None:
    other_path = tmp_path / "other"
    other_path.mkdir()
    runtime, core = matching_runtime_core_v3(tmp_path)
    other_runtime, other_core = matching_runtime_core_v3(other_path)
    run = retain_request_bound_run_decision_v3(runtime, semantic_decision=core)
    other_run = retain_request_bound_run_decision_v3(other_runtime, semantic_decision=other_core)
    owner = retain_request_bound_publication_candidates_v3(run)
    assert canonical_json_bytes(run.record()) == canonical_json_bytes(other_run.record())
    with pytest.raises(ValueError, match="run owner"):
        validate_request_bound_publication_candidates_v3(
            owner.record(), owner, run_decision=other_run
        )
