"""Requested candidate bytes/accounting, not final publication or real OS execution."""

import hashlib
import json
from copy import copy
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Literal, cast

import pytest
from jsonschema import ValidationError  # type: ignore[import-untyped]

from tests.contracts import next_publication_candidates_v2_reference as candidate_reference
from tests.contracts import next_runtime_v2_reference as runtime_reference
from tests.contracts.next_public_artifact_v2_reference import RetainedPublicSemanticArtifactV2
from tests.contracts.next_public_artifact_v2_validation import validate_public_semantic_artifact_v2
from tests.contracts.next_publication_candidates_v2_fixtures import (
    available_large_json_run,
    known_run_with_formats,
    unavailable_core_run,
)
from tests.contracts.next_publication_candidates_v2_validation import (
    validate_request_bound_publication_candidates_v2,
)
from tests.contracts.next_run_decision_v2_reference import retain_request_bound_run_decision_v2
from tests.contracts.next_runtime_v2_validation import _validate_schema
from tests.contracts.test_next_core_failure_v2 import runtime_for_core_wire
from tests.contracts.test_next_exchange_v2 import request_inputs
from tests.contracts.test_next_observed_response_receipt_v2 import protocol_runtime
from tests.contracts.test_next_process_observation_v2 import complete_evidence
from tests.contracts.test_next_provenance_v2 import complete_core_runtime
from tests.contracts.test_next_semantic_candidate_v2 import core_inputs, update_model_digest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def complete_candidates(
    tmp_path_factory: pytest.TempPathFactory,
) -> candidate_reference.RetainedRequestBoundPublicationCandidatesV2:
    runtime, core = complete_core_runtime(tmp_path_factory.mktemp("candidate-known"))
    run = retain_request_bound_run_decision_v2(runtime, semantic_decision=core)
    return candidate_reference.retain_request_bound_publication_candidates_v2(run)


@pytest.fixture(scope="module")
def both_candidates(
    tmp_path_factory: pytest.TempPathFactory,
) -> candidate_reference.RetainedRequestBoundPublicationCandidatesV2:
    run = known_run_with_formats(
        tmp_path_factory.mktemp("candidate-both"), ["semantic-json", "plantuml"]
    )
    return candidate_reference.retain_request_bound_publication_candidates_v2(run)


def aligned_candidate_cache(
    owner: candidate_reference.RetainedRequestBoundPublicationCandidatesV2, value: dict[str, Any]
) -> candidate_reference.RetainedRequestBoundPublicationCandidatesV2:
    """Malformed conformance owner only; cache agreement must not prove actual bytes."""

    bad = copy(owner)
    object.__setattr__(
        bad, "_record_bytes", json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    )
    return bad


def test_json_only_run_retains_its_known_candidate_and_actual_capture(tmp_path: Path) -> None:
    runtime, core = complete_core_runtime(tmp_path)
    run = retain_request_bound_run_decision_v2(runtime, semantic_decision=core)

    from tests.contracts.next_publication_candidates_v2_reference import (
        project_request_bound_publication_candidates_v2,
        retain_request_bound_publication_candidates_v2,
    )

    owner = retain_request_bound_publication_candidates_v2(run)
    wire = owner.artifact_bytes("semantic-json")
    assert wire is not None
    assert (len(wire), hashlib.sha256(wire).hexdigest()) == (
        9472,
        "545389abfa3975b2c95083db9cca6b8efbe071c4526b90cbe55fe9bdc84b5957",
    )
    assert owner.run_decision() is run
    assert owner.artifacts()[0].semantic_decision() is core
    assert owner.artifact_bytes("plantuml") is None
    record = project_request_bound_publication_candidates_v2(owner)
    assert record["schema"] == "code-structure-viz.next-publication-candidates/v2"
    assert record["run_decision"] == run.record()
    assert record["artifacts"] == [
        {
            "path": "next.snapshot.semantic.json",
            "domain": "next",
            "format": "semantic-json",
            "media_type": "application/json",
            "size_bytes": 9472,
            "sha256": "545389abfa3975b2c95083db9cca6b8efbe071c4526b90cbe55fe9bdc84b5957",
        }
    ]
    assert record["capture_measurements"] == {
        "adapter_stdout": {
            "captured_bytes": 6320,
            "capture_retained_bytes": 6320,
            "eof": True,
            "limit_bytes": 16777216,
        },
        "adapter_stderr": {
            "captured_bytes": 0,
            "capture_retained_bytes": 0,
            "eof": True,
            "limit_bytes": 65536,
        },
    }


def test_plantuml_only_run_does_not_add_an_unrequested_json_candidate(tmp_path: Path) -> None:
    from tests.contracts.next_publication_candidates_v2_reference import (
        retain_request_bound_publication_candidates_v2,
    )

    run = known_run_with_formats(tmp_path, ["plantuml"], selector="next:plantuml")
    owner = retain_request_bound_publication_candidates_v2(run)
    assert owner.artifact_bytes("semantic-json") is None
    wire = owner.artifact_bytes("plantuml")
    assert wire is not None
    assert (len(wire), hashlib.sha256(wire).hexdigest()) == (
        1082,
        "0bce98e4e12b722ff2685a76c52bddba7bca735af090ad735d94bbfc9e50c2a9",
    )
    assert [item["format"] for item in owner.record()["artifacts"]] == ["plantuml"]
    assert owner.run_decision() is run


def test_both_formats_keep_canonical_order_even_when_plantuml_is_selected(tmp_path: Path) -> None:
    from tests.contracts.next_publication_candidates_v2_reference import (
        retain_request_bound_publication_candidates_v2,
    )

    run = known_run_with_formats(tmp_path, ["semantic-json", "plantuml"], selector="next:plantuml")
    owner = retain_request_bound_publication_candidates_v2(run)
    record = owner.record()
    assert [item["format"] for item in record["artifacts"]] == ["semantic-json", "plantuml"]
    assert all(item.semantic_decision() is run.semantic_decision() for item in owner.artifacts())
    json_bytes = owner.artifact_bytes("semantic-json")
    assert json_bytes is not None
    document = json.loads(json_bytes)
    assert document["request"]["formats"] == ["semantic-json", "plantuml"]
    assert document["request"]["run_fingerprint"] != (
        "066d76ba2cfbae97b137a7a1bd59a4181dee2c0ccf31f5c013a9a1735dc8c56e"
    )
    for descriptor in record["artifacts"]:
        actual = owner.artifact_bytes(descriptor["format"])
        assert actual is not None
        assert descriptor["size_bytes"] == len(actual)
        assert descriptor["sha256"] == hashlib.sha256(actual).hexdigest()


@pytest.mark.parametrize("outcome", ["partial_safe", "complete_empty"])
def test_available_nondefault_outcomes_keep_their_actual_safe_subset(
    tmp_path: Path, outcome: str
) -> None:
    from tests.contracts.next_publication_candidates_v2_reference import (
        retain_request_bound_publication_candidates_v2,
    )

    run = known_run_with_formats(
        tmp_path,
        ["semantic-json", "plantuml"],
        empty_membership=outcome == "complete_empty",
        partial_safe=outcome == "partial_safe",
    )
    owner = retain_request_bound_publication_candidates_v2(run)
    raw_json = owner.artifact_bytes("semantic-json")
    raw_plantuml = owner.artifact_bytes("plantuml")
    assert raw_json is not None and raw_plantuml is not None
    document = json.loads(raw_json)
    assert owner.record()["run_decision"]["payload_available"] is True
    assert all(row["kind"] == "module" for row in document["entities"])
    if outcome == "partial_safe":
        assert run.record()["outcome"] == "partial_safe"
        assert document["status"] == "incomplete"
        assert document["incomplete_kind"] == "partial_safe"
        assert len(document["entities"]) == 1
        assert b"marker=partial_safe\n" in raw_plantuml
        assert document["coverage"]["counts"]["excluded"] == 1
    else:
        assert run.record()["outcome"] == document["status"] == "complete"
        assert document["entities"] == []
        assert document["coverage"]["counts"]["internal_entities"] == 0
        assert b'component "M:' not in raw_plantuml


def test_ordinary_runtime_failure_retains_accounting_but_no_candidate_bytes(tmp_path: Path) -> None:
    from tests.contracts.next_publication_candidates_v2_reference import (
        retain_request_bound_publication_candidates_v2,
    )

    runtime, failure_frame = protocol_runtime(tmp_path)
    run = retain_request_bound_run_decision_v2(runtime)
    owner = retain_request_bound_publication_candidates_v2(run)
    assert owner.run_decision() is run
    assert owner.artifacts() == ()
    assert owner.artifact_bytes("semantic-json") is None
    assert owner.artifact_bytes("plantuml") is None
    assert owner.record()["artifacts"] == []
    assert owner.record()["run_decision"]["payload_available"] is False
    assert owner.record()["capture_measurements"]["adapter_stdout"] == {
        "captured_bytes": 263,
        "capture_retained_bytes": 263,
        "eof": True,
        "limit_bytes": 16777216,
    }
    assert runtime.transport_candidate() is None
    assert not hasattr(owner, "response_frame")
    assert failure_frame.raw_bytes not in owner._record_bytes


def test_candidate_rejects_float_counts_even_in_a_schema_admitted_observation(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    evidence = complete_evidence(policy)
    evidence.update(response=None, terminal_cause="timeout", exit_code=-15)
    evidence["capture"].update(
        stdin_bytes=len(request.canonical_bytes),
        stdin_sent_bytes=len(request.canonical_bytes),
        stdout_bytes=17.0,
        stdout_retained_bytes=0,
        stdout_eof=False,
    )
    evidence["cleanup"].update(group_stop="verified", signals=["TERM"])
    observation = runtime_reference.reference_process_observation_v2(policy, evidence)
    runtime = runtime_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, None
    )
    run = retain_request_bound_run_decision_v2(runtime)
    with pytest.raises(ValueError, match=r"capture.*integer"):
        candidate_reference.retain_request_bound_publication_candidates_v2(run)


@pytest.mark.parametrize("cause", ["spawn_failed", "stage_failed"])
def test_pre_spawn_failure_uses_null_capture_slots_not_zero_byte_success(
    tmp_path: Path, cause: str
) -> None:
    from tests.contracts.next_publication_candidates_v2_reference import (
        retain_request_bound_publication_candidates_v2,
    )

    seal, assets, request, policy = request_inputs(tmp_path)
    evidence = complete_evidence(policy)
    evidence.update(spawn=None, capture=None, response=None, exit_code=None, terminal_cause=cause)
    evidence["cleanup"]["direct_child_waited"] = False
    observation = runtime_reference.reference_process_observation_v2(policy, evidence)
    runtime = runtime_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, None
    )
    run = retain_request_bound_run_decision_v2(runtime)
    owner = retain_request_bound_publication_candidates_v2(run)
    assert owner.artifacts() == ()
    assert owner.record()["capture_measurements"] == {
        "adapter_stdout": None,
        "adapter_stderr": None,
    }
    assert owner.record()["run_decision"]["response"] is None
    assert owner.record()["run_decision"]["context"]["run_fingerprint"] is None


@pytest.mark.parametrize(
    ("branch", "code"),
    [
        ("target", "CSV-NEXT-TARGET-001"),
        ("export", "CSV-NEXT-EXPORT-001"),
        ("entity", "CSV-NEXT-LIMIT-005"),
        ("rejected", "CSV-NEXT-PROTOCOL-001"),
    ],
)
def test_core_unavailable_is_not_projected_as_empty_complete(
    tmp_path: Path, branch: Literal["target", "export", "entity", "rejected"], code: str
) -> None:
    from tests.contracts.next_publication_candidates_v2_reference import (
        retain_request_bound_publication_candidates_v2,
    )

    run = unavailable_core_run(tmp_path, branch)
    owner = retain_request_bound_publication_candidates_v2(run)
    record = owner.record()
    assert owner.run_decision() is run
    assert run.semantic_decision() is not None
    assert owner.artifacts() == ()
    assert owner.artifact_bytes("semantic-json") is None
    assert owner.artifact_bytes("plantuml") is None
    assert record["artifacts"] == []
    assert record["run_decision"]["outcome"] == "payload_unavailable"
    assert record["run_decision"]["provenance"]["failure_code"] == code
    assert record["capture_measurements"]["adapter_stdout"]["eof"] is True


def test_candidate_schema_rejects_duplicate_or_unrequested_artifact_shapes(
    complete_candidates: candidate_reference.RetainedRequestBoundPublicationCandidatesV2,
) -> None:
    record = complete_candidates.record()
    record["artifacts"] *= 2
    with pytest.raises(ValidationError):
        _validate_schema("next-publication-candidates-v2", record)


def test_json_leaf_descriptor_rejects_float_equal_to_its_actual_byte_length(
    complete_candidates: candidate_reference.RetainedRequestBoundPublicationCandidatesV2,
) -> None:
    artifact = copy(complete_candidates.artifacts()[0])
    assert type(artifact) is RetainedPublicSemanticArtifactV2
    descriptor = artifact.descriptor()
    descriptor["size_bytes"] = float(descriptor["size_bytes"])
    _validate_schema("next-publication-decision-v1", descriptor, "#/$defs/artifact_descriptor")
    # Malformed conformance input only; callers cannot set retained bytes or descriptors.
    object.__setattr__(artifact, "_descriptor_bytes", json.dumps(descriptor).encode())
    with pytest.raises(ValueError):
        validate_public_semantic_artifact_v2(artifact, artifact.semantic_decision())


@pytest.mark.parametrize("surface", ["coverage", "source", "request", "versions", "file"])
def test_rehashed_json_candidate_rejects_float_equal_to_core_integer(
    complete_candidates: candidate_reference.RetainedRequestBoundPublicationCandidatesV2,
    surface: str,
) -> None:
    artifact = copy(complete_candidates.artifacts()[0])
    assert type(artifact) is RetainedPublicSemanticArtifactV2
    document = json.loads(artifact.wire_bytes())
    if surface == "coverage":
        document["coverage"]["counts"]["internal_entities"] = 1.0
    elif surface == "source":
        document["source"]["file_count"] = float(document["source"]["file_count"])
    elif surface == "request":
        document["request"]["limits"]["max_entities"] = 500.0
    elif surface == "versions":
        document["identity_versions"]["module"] = 1.0
    else:
        document["files"][0]["size_bytes"] = float(document["files"][0]["size_bytes"])
    _validate_schema("next-semantic-v2", document)
    wire = (
        json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        + b"\n"
    )
    descriptor = artifact.descriptor()
    descriptor.update(size_bytes=len(wire), sha256=hashlib.sha256(wire).hexdigest())
    object.__setattr__(artifact, "_wire_bytes", wire)
    object.__setattr__(artifact, "_descriptor_bytes", json.dumps(descriptor).encode())
    with pytest.raises(ValueError):
        validate_public_semantic_artifact_v2(artifact, artifact.semantic_decision())


@pytest.mark.parametrize(
    ("formats", "selector"),
    [
        (["semantic-json"], None),
        (["semantic-json"], "manifest"),
        (["semantic-json"], "next:semantic-json"),
        (["plantuml"], None),
        (["plantuml"], "manifest"),
        (["plantuml"], "next:plantuml"),
        (["semantic-json", "plantuml"], None),
        (["semantic-json", "plantuml"], "manifest"),
        (["semantic-json", "plantuml"], "next:semantic-json"),
    ],
)
def test_selector_does_not_shrink_the_requested_artifact_set(
    tmp_path: Path, formats: list[str], selector: str | None
) -> None:
    run = known_run_with_formats(tmp_path, formats, selector=selector)
    owner = candidate_reference.retain_request_bound_publication_candidates_v2(run)
    assert [item["format"] for item in owner.record()["artifacts"]] == formats
    assert owner.record()["run_decision"]["context"]["run_context"]["stdout_selector"] == selector
    assert not any(
        key in owner.record() for key in ("allowed", "published", "copy_status", "selected_stdout")
    )


@pytest.mark.parametrize(
    "mutation", ["missing", "extra", "reversed", "wrong_path", "private", "capture_split"]
)
def test_schema_closes_requested_shapes_and_metadata_fields(
    both_candidates: candidate_reference.RetainedRequestBoundPublicationCandidatesV2,
    mutation: str,
) -> None:
    value = both_candidates.record()
    if mutation == "missing":
        value["artifacts"].pop()
    elif mutation == "extra":
        value["artifacts"].append(value["artifacts"][0])
    elif mutation == "reversed":
        value["artifacts"].reverse()
    elif mutation == "wrong_path":
        value["artifacts"][0]["path"] = "run-manifest.json"
    elif mutation == "private":
        value["capture_measurements"]["adapter_stdout"]["raw_bytes"] = "private"
    else:
        value["capture_measurements"]["adapter_stdout"] = None
    with pytest.raises(ValidationError):
        _validate_schema("next-publication-candidates-v2", value)


def test_foreign_equal_content_run_is_not_the_expected_owner(
    complete_candidates: candidate_reference.RetainedRequestBoundPublicationCandidatesV2,
) -> None:
    original = complete_candidates.run_decision()
    other = retain_request_bound_run_decision_v2(
        original.runtime_result(), semantic_decision=original.semantic_decision()
    )
    assert other is not original and other.record() == original.record()
    with pytest.raises(ValueError, match="retained run owner"):
        validate_request_bound_publication_candidates_v2(
            complete_candidates.record(), complete_candidates, run_decision=other
        )


def test_foreign_core_with_equal_content_cannot_replace_a_candidate_leaf(
    complete_candidates: candidate_reference.RetainedRequestBoundPublicationCandidatesV2,
) -> None:
    owner = copy(complete_candidates)
    leaf = copy(owner.artifacts()[0])
    core = leaf.semantic_decision()
    foreign = runtime_reference.decide_semantic_candidate_v2(
        core.transport_candidate(), core.source_seal(), core.execution_assets()
    )
    assert foreign is not core and foreign.gate() == core.gate()
    object.__setattr__(leaf, "_decision", foreign)
    object.__setattr__(owner, "_artifacts", (leaf,))
    with pytest.raises(ValueError, match="retained Core owner"):
        validate_request_bound_publication_candidates_v2(
            owner.record(), owner, run_decision=owner.run_decision()
        )


@pytest.mark.parametrize("surface", ["descriptor", "capture", "parent", "core"])
def test_cache_aligned_substitution_still_requires_actual_owners(
    complete_candidates: candidate_reference.RetainedRequestBoundPublicationCandidatesV2,
    surface: str,
) -> None:
    value = complete_candidates.record()
    if surface == "descriptor":
        value["artifacts"][0]["sha256"] = "0" * 64
    elif surface == "capture":
        value["capture_measurements"]["adapter_stdout"]["captured_bytes"] += 1
    elif surface == "parent":
        value["run_decision"]["context"]["domain_config_digest"] = "0" * 64
    else:
        value["run_decision"]["core_measurement"]["actual"] += 1
    _validate_schema("next-publication-candidates-v2", value)
    bad = aligned_candidate_cache(complete_candidates, value)
    with pytest.raises(ValueError):
        validate_request_bound_publication_candidates_v2(
            value, bad, run_decision=bad.run_decision()
        )


@pytest.mark.parametrize("surface", ["version", "size", "captured", "retained", "limit", "core"])
def test_equal_float_numeric_substitution_is_not_the_retained_integer(
    complete_candidates: candidate_reference.RetainedRequestBoundPublicationCandidatesV2,
    surface: str,
) -> None:
    value = complete_candidates.record()
    if surface == "version":
        value["version"] = 2.0
    elif surface == "size":
        value["artifacts"][0]["size_bytes"] = float(value["artifacts"][0]["size_bytes"])
    elif surface == "core":
        value["run_decision"]["core_measurement"]["actual"] = 1.0
    else:
        field = {
            "captured": "captured_bytes",
            "retained": "capture_retained_bytes",
            "limit": "limit_bytes",
        }[surface]
        slot = value["capture_measurements"]["adapter_stdout"]
        slot[field] = float(slot[field])
    _validate_schema("next-publication-candidates-v2", value)
    bad = aligned_candidate_cache(complete_candidates, value)
    with pytest.raises(ValueError):
        validate_request_bound_publication_candidates_v2(
            value, bad, run_decision=bad.run_decision()
        )


@pytest.mark.parametrize("surface", ["size", "captured", "eof", "core"])
def test_bool_integer_alias_is_schema_invalid(
    complete_candidates: candidate_reference.RetainedRequestBoundPublicationCandidatesV2,
    surface: str,
) -> None:
    value = complete_candidates.record()
    if surface == "size":
        value["artifacts"][0]["size_bytes"] = True
    elif surface == "core":
        value["run_decision"]["core_measurement"]["actual"] = True
    else:
        slot = value["capture_measurements"]["adapter_stdout"]
        slot["captured_bytes" if surface == "captured" else "eof"] = (
            True if surface == "captured" else 1
        )
    with pytest.raises(ValidationError):
        _validate_schema("next-publication-candidates-v2", value)


def test_nominal_factory_frozen_owners_fresh_metadata_and_private_repr(
    complete_candidates: candidate_reference.RetainedRequestBoundPublicationCandidatesV2,
) -> None:
    owner = complete_candidates
    with pytest.raises(TypeError):
        candidate_reference.RetainedRequestBoundPublicationCandidatesV2(owner.run_decision())
    with pytest.raises(FrozenInstanceError):
        cast(Any, owner)._record_bytes = b"{}"
    assert repr(owner) == "RetainedRequestBoundPublicationCandidatesV2()"
    value = candidate_reference.project_request_bound_publication_candidates_v2(owner)
    value["artifacts"].clear()
    value["capture_measurements"]["adapter_stdout"]["eof"] = False
    assert owner.record()["artifacts"]
    assert owner.record()["capture_measurements"]["adapter_stdout"]["eof"] is True
    # The portable semantic_payload observation name is intentional; it contains a digest,
    # not a retained child payload. Do not confuse that closed observation with raw data.
    semantic_observation = owner.record()["run_decision"]["provenance"]["observed"][
        "semantic_payload"
    ]
    assert set(semantic_observation["value"]) == {"schema", "version", "sha256"}
    for forbidden in ("const Card", "content_base64", "proof", '"pid"', "/private", '"spawn"'):
        assert forbidden not in json.dumps(owner.record())
        assert forbidden not in repr(owner)
    with pytest.raises(TypeError):
        candidate_reference.retain_request_bound_publication_candidates_v2(
            cast(Any, SimpleNamespace())
        )
    with pytest.raises(TypeError):
        candidate_reference.project_request_bound_publication_candidates_v2(
            cast(Any, SimpleNamespace())
        )
    with pytest.raises(ValueError):
        owner.artifact_bytes(cast(Any, "unknown"))
    with pytest.raises(TypeError):
        owner.artifact_bytes(cast(Any, b"plantuml"))
    with pytest.raises(TypeError):
        candidate_reference.retain_request_bound_publication_candidates_v2(
            owner.run_decision(), artifacts=()
        )  # type: ignore[call-arg]


def test_source_changes_after_sealing_do_not_change_retained_candidate_bytes(
    tmp_path: Path,
) -> None:
    run = known_run_with_formats(tmp_path, ["semantic-json", "plantuml"])
    before = candidate_reference.retain_request_bound_publication_candidates_v2(run)
    (tmp_path / "repo/src/Card.tsx").write_bytes(b"private changed source\n")
    after = candidate_reference.retain_request_bound_publication_candidates_v2(run)
    assert after.record() == before.record()
    assert after.artifact_bytes("semantic-json") == before.artifact_bytes("semantic-json")
    assert after.artifact_bytes("plantuml") == before.artifact_bytes("plantuml")


@pytest.mark.parametrize("delta", [0, 1])
def test_actual_json_candidate_at_selected_copy_cap_and_plus_one_is_retained(
    tmp_path: Path, delta: int
) -> None:
    cap = 16 * 1024 * 1024
    run, independent_expected = available_large_json_run(tmp_path, cap + delta)
    owner = candidate_reference.retain_request_bound_publication_candidates_v2(run)
    actual = owner.artifact_bytes("semantic-json")
    assert actual is not None and actual == independent_expected
    assert len(actual) == cap + delta
    descriptor = owner.record()["artifacts"][0]
    assert descriptor["size_bytes"] == cap + delta
    assert descriptor["sha256"] == hashlib.sha256(independent_expected).hexdigest()
    assert run.record()["payload_available"] is True
    assert run.record()["core_measurement"] == {
        "kind": "entity_budget",
        "actual": 1000,
        "limit": 1000,
    }
    request = run.runtime_result().request_frame().record()
    assert request["limits"]["max_selected_stdout_bytes"] == cap
    assert run.record()["response"]["byte_length"] < cap
    assert (
        len(run.runtime_result().request_frame().canonical_bytes)
        < request["limits"]["max_encoded_stdin_bytes"]
    )
    assert "copy_status" not in owner.record()
    print(
        json.dumps(
            {
                "reference_case": "actual-public-json-copy-boundary",
                "delta": delta,
                "json_bytes": len(actual),
                "json_sha256": descriptor["sha256"],
                "request_bytes": len(run.runtime_result().request_frame().canonical_bytes),
                "response_bytes": run.record()["response"]["byte_length"],
                "sealed_files": len(request["files"]),
                "internal_entities": run.record()["core_measurement"]["actual"],
                "longest_relative_path_bytes": max(
                    len(row["path"].encode()) for row in request["files"]
                ),
                "context_file_bytes": next(
                    row["size_bytes"]
                    for row in request["files"]
                    if row["path"] == "src/global.d.ts"
                ),
            },
            sort_keys=True,
        )
    )


@pytest.mark.parametrize(
    ("name", "file_hash"),
    [
        (
            "publication-candidates-json-only.json",
            "243ee57df040dd8969544fa3f9b6a3e82566451c98185312aaee373fb0a85fec",
        ),
        (
            "publication-candidates-both.json",
            "ad2424a19dcd0f8db6529342e0d2b38c8aae28b7e7733ca737bd6920679045df",
        ),
        (
            "publication-candidates-pre-spawn-failure.json",
            "863a4f141598219c37181caa03594166fed262d6f4b0fd27d3b3c56bdab6e752",
        ),
    ],
)
def test_candidate_metadata_matches_independent_frozen_literals(
    tmp_path: Path,
    complete_candidates: candidate_reference.RetainedRequestBoundPublicationCandidatesV2,
    both_candidates: candidate_reference.RetainedRequestBoundPublicationCandidatesV2,
    name: str,
    file_hash: str,
) -> None:
    raw = (ROOT / "tests/fixtures/next_runtime_v2" / name).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == file_hash
    expected = json.loads(raw)
    if name == "publication-candidates-json-only.json":
        owner = complete_candidates
    elif name == "publication-candidates-both.json":
        owner = both_candidates
    else:
        seal, assets, request, policy = request_inputs(tmp_path)
        evidence = complete_evidence(policy)
        evidence.update(
            spawn=None, capture=None, response=None, exit_code=None, terminal_cause="spawn_failed"
        )
        evidence["cleanup"]["direct_child_waited"] = False
        observation = runtime_reference.reference_process_observation_v2(policy, evidence)
        runtime = runtime_reference.retain_runtime_result_v2(
            seal, assets, request, policy, observation, None
        )
        owner = candidate_reference.retain_request_bound_publication_candidates_v2(
            retain_request_bound_run_decision_v2(runtime)
        )
    _validate_schema("next-publication-candidates-v2", expected)
    assert candidate_reference.project_request_bound_publication_candidates_v2(owner) == expected
    validate_request_bound_publication_candidates_v2(
        expected, owner, run_decision=owner.run_decision()
    )


def test_discarded_capture_keeps_observed_counts_and_false_eof(tmp_path: Path) -> None:
    seal, assets, request, policy = request_inputs(tmp_path)
    evidence = complete_evidence(policy)
    evidence.update(response=None, terminal_cause="timeout", exit_code=-15)
    evidence["capture"].update(
        stdin_bytes=len(request.canonical_bytes),
        stdin_sent_bytes=len(request.canonical_bytes),
        stdout_bytes=17,
        stdout_retained_bytes=0,
        stdout_eof=False,
        stderr_bytes=9,
        stderr_retained_bytes=0,
        stderr_eof=False,
    )
    evidence["cleanup"].update(group_stop="verified", signals=["TERM"])
    observation = runtime_reference.reference_process_observation_v2(policy, evidence)
    runtime = runtime_reference.retain_runtime_result_v2(
        seal, assets, request, policy, observation, None
    )
    owner = candidate_reference.retain_request_bound_publication_candidates_v2(
        retain_request_bound_run_decision_v2(runtime)
    )
    assert owner.record()["capture_measurements"] == {
        "adapter_stdout": {
            "captured_bytes": 17,
            "capture_retained_bytes": 0,
            "eof": False,
            "limit_bytes": 16777216,
        },
        "adapter_stderr": {
            "captured_bytes": 9,
            "capture_retained_bytes": 0,
            "eof": False,
            "limit_bytes": 65536,
        },
    }
    assert owner.artifacts() == ()


def test_public_json_rejects_float_in_the_admitted_core_projection(tmp_path: Path) -> None:
    seal, assets, request, policy, wire = core_inputs(tmp_path)
    wire["semantic_payload"]["model"]["coverage"]["counts"]["internal_entities"] = 1.0
    update_model_digest(wire)
    runtime = runtime_for_core_wire(seal, assets, request, policy, wire)
    candidate = runtime.transport_candidate()
    assert candidate is not None
    core = runtime_reference.decide_semantic_candidate_v2(candidate, seal, assets)
    run = retain_request_bound_run_decision_v2(runtime, semantic_decision=core)
    with pytest.raises(ValueError, match=r"public.*integer"):
        candidate_reference.retain_request_bound_publication_candidates_v2(run)
