"""Final publication-v2 owner joins actual candidates, bytes and measurements."""

import base64
import hashlib
import json
from copy import copy
from importlib import import_module, util
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from jsonschema import ValidationError  # type: ignore[import-untyped]

from tests.contracts.next_final_publication_v2_fixtures import (
    capture_overflow_candidates_v3,
    complete_candidates_v3,
    entity_budget_candidates_v3,
    explicit_parent_selections_v2,
    export_failure_candidates_v3,
    large_selected_stdout_candidates_v3,
    observed_zero_capture_candidates_v3,
    parent_configuration_fixture_v2,
    partial_stderr_overflow_candidates_v3,
    rejected_candidates_v3,
    runtime_control_failure_candidates_v3,
    source_failure_candidates_v3,
    stage_failed_candidates_v3,
    stderr_boundary_candidates_v3,
    target_failure_candidates_v3,
)
from tests.contracts.test_json_schemas import _validator
from tests.contracts.test_next_public_diagnostic_v3 import NODE_002_JSONL
from tests.contracts.test_next_semantic_core_v3 import MODULE_IDS, SOURCE_BYTES, core_inputs_v3


def _literal_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _literal_sha(value: object) -> str:
    return hashlib.sha256(_literal_json(value)).hexdigest()


def test_manifest_selector_publishes_a_finite_same_run_candidate_on_stage_failure(
    tmp_path: Path,
) -> None:
    candidates = stage_failed_candidates_v3(tmp_path, selector="manifest")
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    owner = reference.retain_final_publication_v2(
        candidates, parent_configuration=parent_configuration_fixture_v2(candidates)
    )
    raw = owner.stdout_bytes()
    manifest = json.loads(raw)
    _validator("run-manifest-v2.schema.json").validate(manifest)
    assert raw == _literal_json(manifest) + b"\n"
    assert "next_publication" not in manifest
    assert "publication" not in manifest["domains"][0]
    assert manifest["command"]["stdout_selector"] == "manifest"
    assert manifest["run"]["fingerprint"] is None
    assert "run_fingerprint" not in manifest["next_request"]
    assert manifest["run"]["status"] == "incomplete" and manifest["run"]["exit_code"] == 3
    assert manifest["config"]["source"] == "explicit"
    assert set(manifest["config"]["value_sources"].values()) == {"explicit"}
    assert manifest["artifacts"] == []
    assert manifest["next_decision"] == candidates.run_decision().record()
    final_manifest = owner.run_manifest()
    assert final_manifest.pop("next_publication") == owner.record()
    assert final_manifest["domains"][0].pop("publication") == owner.record()
    assert final_manifest == manifest
    value = owner.record()
    assert value["publication_outcome"] == "published" and value["exit_code"] == 3
    assert value["stdout"]["availability"] is True
    assert value["stdout"]["copy_status"] == "published"
    assert value["stdout"]["candidate"] == {
        "path": "run-manifest.json",
        "domain": "next",
        "format": "semantic-json",
        "media_type": "application/json",
        "size_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    assert value["stdout"]["selected_size_bytes"] == len(raw)
    assert value["stdout"]["selected_sha256"] == hashlib.sha256(raw).hexdigest()
    assert value["measurements"]["selected_stdout"] == {
        "allowed": True,
        "measured_bytes": len(raw),
        "retained_bytes": len(raw),
    }
    assert owner.stderr_bytes() == NODE_002_JSONL


def test_manifest_selector_keeps_both_requested_artifacts_in_public_path_order(
    tmp_path: Path,
) -> None:
    candidates = complete_candidates_v3(
        tmp_path, selector="manifest", requested_formats=["semantic-json", "plantuml"]
    )
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    owner = reference.retain_final_publication_v2(
        candidates, parent_configuration=parent_configuration_fixture_v2(candidates)
    )
    manifest = json.loads(owner.stdout_bytes())
    assert manifest["run"]["status"] == "complete" and manifest["run"]["exit_code"] == 0
    assert (
        manifest["run"]["fingerprint"]
        == candidates.run_decision().record()["context"]["run_fingerprint"]
    )
    assert manifest["next_request"]["run_fingerprint"] == manifest["run"]["fingerprint"]
    assert manifest["domains"][0]["artifact_paths"] == [
        "next.snapshot.puml",
        "next.snapshot.semantic.json",
    ]
    assert manifest["domains"][0]["formats"] == ["semantic-json", "plantuml"]
    expected = sorted(
        (item.descriptor() for item in candidates.artifacts()), key=lambda row: row["path"]
    )
    assert manifest["artifacts"] == expected
    assert owner.run_manifest()["artifacts"] == expected
    assert owner.domain_manifest()["artifact_paths"] == [row["path"] for row in expected]
    assert [row["descriptor"] for row in owner.record()["artifacts"]] == expected
    assert owner.record()["stdout"]["candidate"]["path"] == "run-manifest.json"


def test_no_selector_publishes_a_measured_summary_even_when_analysis_failed(tmp_path: Path) -> None:
    candidates = stage_failed_candidates_v3(tmp_path)
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    owner = reference.retain_final_publication_v2(
        candidates, parent_configuration=parent_configuration_fixture_v2(candidates)
    )
    expected = {
        "type": "run_summary",
        "schema": "code-structure-viz.run-summary/v1",
        "run_status": "incomplete",
        "exit_code": 3,
        "domains": [
            {"domain": "next", "status": "incomplete", "incomplete_kind": "payload_unavailable"}
        ],
        "manifest": "run-manifest.json",
    }
    raw = _literal_json(expected) + b"\n"
    assert owner.stdout_bytes() == raw
    assert owner.run_summary() == expected
    value = owner.record()
    assert value["publication_outcome"] == "published" and value["exit_code"] == 3
    assert value["stdout"] == {
        "selector": None,
        "availability": True,
        "copy_status": "published",
        "candidate": None,
        "selected_size_bytes": len(raw),
        "selected_sha256": hashlib.sha256(raw).hexdigest(),
        "result_bytes_base64": base64.b64encode(raw).decode("ascii"),
        "result_size_bytes": len(raw),
        "result_sha256": hashlib.sha256(raw).hexdigest(),
    }
    assert value["measurements"]["selected_stdout"] == {
        "allowed": True,
        "measured_bytes": len(raw),
        "retained_bytes": len(raw),
    }
    assert value["measurements"]["adapter_stdout"] is None
    assert owner.stderr_bytes() == NODE_002_JSONL
    assert owner.run_manifest()["run"]["fingerprint"] is None


@pytest.mark.parametrize("selector", [None, "manifest"])
@pytest.mark.parametrize("stream", ["stdout", "stderr"])
def test_metadata_selector_capture_failure_returns_typed_unavailable_without_remeasurement(
    tmp_path: Path,
    selector: str | None,
    stream: str,
) -> None:
    candidates = capture_overflow_candidates_v3(tmp_path, stream, selector=selector)
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    owner = reference.retain_final_publication_v2(
        candidates, parent_configuration=parent_configuration_fixture_v2(candidates)
    )
    summary = owner.run_summary()
    measured = _literal_json(summary) + b"\n"
    replacement = {
        "type": "stdout_result",
        "schema": "code-structure-viz.stdout-result/v2",
        "selector": None,
        "availability": False,
        "run_status": "incomplete",
        "stable_reason": "run_summary",
        "selected_stdout_unavailable": True,
        "artifact": None,
    }
    if selector == "manifest":
        manifest = owner.run_manifest()
        del manifest["next_publication"]
        del manifest["domains"][0]["publication"]
        measured = _literal_json(manifest) + b"\n"
        replacement = {
            "type": "stdout_result",
            "schema": "code-structure-viz.stdout-result/v2",
            "selector": "manifest",
            "availability": False,
            "domain_status": "incomplete",
            "stable_reason": "domain_payload_unavailable",
            "artifact": None,
        }
    assert owner.stdout_bytes() == _literal_json(replacement) + b"\n"
    _validator("stdout-result-v2.schema.json").validate(replacement)
    value = owner.record()
    assert value["publication_outcome"] == "payload_unavailable" and value["exit_code"] == 3
    assert value["response"] is None and value["artifacts"] == []
    assert value["stdout"]["availability"] is False
    assert value["stdout"]["copy_status"] == "not_attempted"
    assert value["stdout"]["selected_sha256"] == hashlib.sha256(measured).hexdigest()
    assert value["measurements"]["selected_stdout"] == {
        "allowed": True,
        "measured_bytes": len(measured),
        "retained_bytes": len(measured),
    }
    assert value["stdout"]["result_sha256"] == hashlib.sha256(owner.stdout_bytes()).hexdigest()
    assert owner.stdout_bytes() != measured


@pytest.mark.parametrize("case", ["complete", "partial", "rejected"])
@pytest.mark.parametrize("selector", [None, "manifest"])
def test_metadata_selectors_preserve_the_same_semantic_outcome_and_all_artifacts(
    tmp_path: Path,
    case: str,
    selector: str | None,
) -> None:
    if case == "partial":
        candidates = source_failure_candidates_v3(
            tmp_path, "parse_file", isolated=True, selector=selector
        )
    else:
        candidates = (complete_candidates_v3 if case == "complete" else rejected_candidates_v3)(
            tmp_path, selector=selector
        )
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    owner = reference.retain_final_publication_v2(
        candidates, parent_configuration=parent_configuration_fixture_v2(candidates)
    )
    expected_domain = {
        "domain": "next",
        "status": "complete" if case == "complete" else "incomplete",
    }
    if case != "complete":
        expected_domain["incomplete_kind"] = (
            "partial_safe" if case == "partial" else "payload_unavailable"
        )
    expected = {
        "type": "run_summary",
        "schema": "code-structure-viz.run-summary/v1",
        "run_status": expected_domain["status"],
        "exit_code": 0 if case == "complete" else 3,
        "domains": [expected_domain],
        "manifest": "run-manifest.json",
    }
    raw = _literal_json(expected) + b"\n"
    if selector == "manifest":
        manifest = owner.run_manifest()
        del manifest["next_publication"]
        del manifest["domains"][0]["publication"]
        raw = _literal_json(manifest) + b"\n"
    assert owner.stdout_bytes() == raw and owner.run_summary() == expected
    value = owner.record()
    assert value["publication_outcome"] == "published"
    assert value["stdout"]["availability"] is True
    if selector is None:
        assert value["stdout"]["candidate"] is None
    else:
        assert value["stdout"]["candidate"]["path"] == "run-manifest.json"
    assert value["measurements"]["selected_stdout"] == {
        "allowed": True,
        "measured_bytes": len(raw),
        "retained_bytes": len(raw),
    }
    assert value["artifacts"] == [
        {
            "descriptor": item.descriptor(),
            "bytes_base64": base64.b64encode(item.wire_bytes()).decode("ascii"),
        }
        for item in candidates.artifacts()
    ]
    assert value["semantic_decision"] == candidates.run_decision().record()


@pytest.mark.parametrize("selector", [None, "manifest"])
def test_metadata_selector_stderr_failure_keeps_the_original_partial_measurement(
    tmp_path: Path,
    selector: str | None,
) -> None:
    candidates = partial_stderr_overflow_candidates_v3(tmp_path, selector=selector)
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    owner = reference.retain_final_publication_v2(
        candidates, parent_configuration=parent_configuration_fixture_v2(candidates)
    )
    original = (
        _literal_json(
            {
                "type": "run_summary",
                "schema": "code-structure-viz.run-summary/v1",
                "run_status": "incomplete",
                "exit_code": 3,
                "domains": [
                    {"domain": "next", "status": "incomplete", "incomplete_kind": "partial_safe"}
                ],
                "manifest": "run-manifest.json",
            }
        )
        + b"\n"
    )
    value = owner.record()
    assert value["publication_outcome"] == "payload_unavailable"
    assert value["semantic_decision"]["outcome"] == "partial_safe"
    assert value["measurements"]["public_stderr"]["measured_bytes"] > 65_536
    assert owner.stderr_bytes() == b""
    measured = value["measurements"]["selected_stdout"]
    if selector is None:
        assert measured == {
            "allowed": True,
            "measured_bytes": len(original),
            "retained_bytes": len(original),
        }
        assert value["stdout"]["selected_sha256"] == hashlib.sha256(original).hexdigest()
    else:
        assert measured["allowed"] is True
        assert measured["measured_bytes"] == measured["retained_bytes"] > 65_536
        assert value["stdout"]["selected_size_bytes"] == measured["measured_bytes"]
        root = owner.run_manifest()
        assert (
            root["artifacts"] == []
            and root["domains"][0]["incomplete_kind"] == "payload_unavailable"
        )
        assert (
            root["run"]["fingerprint"] == value["semantic_decision"]["context"]["run_fingerprint"]
        )
    replacement = json.loads(owner.stdout_bytes())
    _validator("stdout-result-v2.schema.json").validate(replacement)
    assert replacement["availability"] is False
    if selector is None:
        assert replacement["stable_reason"] == "run_summary"
        assert replacement["selected_stdout_unavailable"] is True
    else:
        assert replacement["stable_reason"] == "domain_payload_unavailable"
        assert replacement["artifact"] is None
    assert owner.run_summary()["domains"] == [
        {"domain": "next", "status": "incomplete", "incomplete_kind": "payload_unavailable"}
    ]
    assert value["stdout"]["result_sha256"] != value["stdout"]["selected_sha256"]


def test_stage_failure_root_retains_null_fingerprint_and_actual_parent_selections(
    tmp_path: Path,
) -> None:
    candidates = stage_failed_candidates_v3(tmp_path, selector="next:semantic-json")
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    context = candidates.run_decision().runtime_result().request_frame().analysis_context()
    selections = explicit_parent_selections_v2(context)
    selections["next_targets"]["source"] = "cli"
    selections["formats"]["source"] = "repository"
    parent = reference.retain_parent_configuration_v2(
        context, source="repository", selections=selections
    )
    owner = reference.retain_final_publication_v2(candidates, parent_configuration=parent)
    assert hasattr(owner, "run_manifest"), "final owner has no root manifest projection"
    root = owner.run_manifest()
    _validator("run-manifest-v2.schema.json").validate(root)
    domain = owner.domain_manifest()
    assert root["domains"] == [domain]
    assert root["next_request"] == domain["request"]
    assert "run_fingerprint" not in root["next_request"]
    assert root["next_config"] == context.domain_config()
    assert root["run"] == {
        "status": "incomplete",
        "exit_code": 3,
        "fingerprint": None,
        "run_context": context.run_context(),
    }
    assert root["request"] == {
        "projects": ["."],
        "targets": [],
        "formats": ["semantic-json"],
        "upstream_depth": 1,
        "downstream_depth": 1,
    }
    assert root["config"]["source"] == "repository"
    assert root["config"]["value_sources"] == {
        "next_projects": "explicit",
        "next_targets": "cli",
        "formats": "repository",
        "upstream_depth": "explicit",
        "downstream_depth": "explicit",
        "limits": "explicit",
        "trusted_environment": "explicit",
    }
    assert root["config"]["resolved"] == {
        "next": {
            "projects": ["."],
            "targets": [],
            "formats": ["semantic-json"],
            "trusted_environment_digest": context.domain_config()["trusted_environment_digest"],
        },
        "traversal": {"upstream_depth": 1, "downstream_depth": 1},
        "limits": context.domain_config()["limits"],
    }
    assert root["config"]["sha256"] == _literal_sha(
        {k: v for k, v in root["config"].items() if k != "sha256"}
    )
    assert root["next_decision"] == candidates.run_decision().record()
    assert root["next_publication"] == owner.record()
    assert root["artifacts"] == []
    assert root["diagnostics"] == domain["diagnostics"]


def test_root_validation_rejects_rehashed_origins_that_differ_from_parent_input(
    tmp_path: Path,
) -> None:
    candidates = stage_failed_candidates_v3(tmp_path, selector="next:semantic-json")
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    validation = import_module("tests.contracts.next_final_publication_v2_validation")
    owner = reference.retain_final_publication_v2(
        candidates, parent_configuration=parent_configuration_fixture_v2(candidates)
    )
    root = owner.run_manifest()
    root["config"]["value_sources"]["next_projects"] = "builtin"
    root["config"]["sha256"] = _literal_sha(
        {k: v for k, v in root["config"].items() if k != "sha256"}
    )
    _validator("run-manifest-v2.schema.json").validate(root)
    assert hasattr(validation, "validate_run_manifest_v2"), "root has no independent parent join"
    with pytest.raises(ValueError, match=r"root.*config"):
        validation.validate_run_manifest_v2(root, owner)


def test_root_validation_rejects_detached_request_source_and_run_fields(tmp_path: Path) -> None:
    candidates = stage_failed_candidates_v3(tmp_path, selector="next:semantic-json")
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    validation = import_module("tests.contracts.next_final_publication_v2_validation")
    owner = reference.retain_final_publication_v2(
        candidates, parent_configuration=parent_configuration_fixture_v2(candidates)
    )
    original = owner.run_manifest()
    for path, replacement in [
        (("run", "fingerprint"), "0" * 64),
        (("request", "upstream_depth"), 9),
        (("next_request", "downstream_depth"), 9),
        (("next_config", "domain_config_digest"), "0" * 64),
        (("source", "fingerprint"), "0" * 64),
        (("command", "stdout_selector"), "manifest"),
        (("run", "run_context", "budget_resolved"), 99),
        (("diagnostics",), original["diagnostics"] * 2),
    ]:
        changed = json.loads(_literal_json(original))
        parent = changed
        for key in path[:-1]:
            parent = parent[key]
        parent[path[-1]] = replacement
        errors = list(_validator("run-manifest-v2.schema.json").iter_errors(changed))
        assert not errors, (path, [list(error.path) for error in errors])
        with pytest.raises(ValueError, match="root"):
            validation.validate_run_manifest_v2(changed, owner)


@pytest.mark.parametrize("case", ["complete", "rejected", "partial"])
def test_root_nonnull_identity_and_artifacts_come_from_the_same_final_owner(
    tmp_path: Path, case: str
) -> None:
    if case == "partial":
        candidates = source_failure_candidates_v3(
            tmp_path, "parse_file", isolated=True, selector="next:semantic-json"
        )
    else:
        candidates = (complete_candidates_v3 if case == "complete" else rejected_candidates_v3)(
            tmp_path, selector="next:semantic-json"
        )
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    validation = import_module("tests.contracts.next_final_publication_v2_validation")
    owner = reference.retain_final_publication_v2(
        candidates, parent_configuration=parent_configuration_fixture_v2(candidates)
    )
    root = owner.run_manifest()
    run = candidates.run_decision().record()
    assert isinstance(root["run"]["fingerprint"], str)
    assert (
        root["run"]["fingerprint"]
        == root["next_request"]["run_fingerprint"]
        == run["context"]["run_fingerprint"]
    )
    assert root["run"]["status"] == ("complete" if case == "complete" else "incomplete")
    assert root["run"]["exit_code"] == (0 if case == "complete" else 3)
    assert root["artifacts"] == [row["descriptor"] for row in owner.record()["artifacts"]]
    summary = owner.run_summary()
    expected_domain = {"domain": "next", "status": root["run"]["status"]}
    if case != "complete":
        expected_domain["incomplete_kind"] = (
            "partial_safe" if case == "partial" else "payload_unavailable"
        )
    assert summary == {
        "type": "run_summary",
        "schema": "code-structure-viz.run-summary/v1",
        "run_status": root["run"]["status"],
        "exit_code": root["run"]["exit_code"],
        "domains": [expected_domain],
        "manifest": "run-manifest.json",
    }
    if root["artifacts"]:
        root = json.loads(_literal_json(root))
        root["artifacts"][0]["sha256"] = "0" * 64
        with pytest.raises(ValueError, match="root artifacts"):
            validation.validate_run_manifest_v2(root, owner)


def test_summary_reports_the_same_failed_run_and_manifest_availability(tmp_path: Path) -> None:
    candidates = stage_failed_candidates_v3(tmp_path, selector="next:semantic-json")
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    owner = reference.retain_final_publication_v2(
        candidates, parent_configuration=parent_configuration_fixture_v2(candidates)
    )
    assert hasattr(owner, "run_summary"), "final owner has no summary projection"
    summary = owner.run_summary()
    _validator("run-summary-v1.schema.json").validate(summary)
    assert summary == {
        "type": "run_summary",
        "schema": "code-structure-viz.run-summary/v1",
        "run_status": "incomplete",
        "exit_code": 3,
        "domains": [
            {"domain": "next", "status": "incomplete", "incomplete_kind": "payload_unavailable"}
        ],
        "manifest": "run-manifest.json",
    }


def test_summary_validation_rejects_schema_valid_status_and_native_number_substitution(
    tmp_path: Path,
) -> None:
    candidates = stage_failed_candidates_v3(tmp_path, selector="next:semantic-json")
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    validation = import_module("tests.contracts.next_final_publication_v2_validation")
    owner = reference.retain_final_publication_v2(
        candidates, parent_configuration=parent_configuration_fixture_v2(candidates)
    )
    original = owner.run_summary()
    assert hasattr(validation, "validate_run_summary_v1"), "summary lacks its same-owner validation"
    for change in ("success", "partial", "native"):
        value = json.loads(_literal_json(original))
        if change == "success":
            value.update(
                run_status="complete",
                exit_code=0,
                domains=[{"domain": "next", "status": "complete"}],
            )
        elif change == "partial":
            value["domains"][0]["incomplete_kind"] = "partial_safe"
        else:
            value["exit_code"] = 3.0
        _validator("run-summary-v1.schema.json").validate(value)
        with pytest.raises(ValueError, match="summary"):
            validation.validate_run_summary_v1(value, owner)


def test_stage_failure_domain_retains_request_without_inventing_semantic_observations(
    tmp_path: Path,
) -> None:
    candidates = stage_failed_candidates_v3(tmp_path, selector="next:semantic-json")
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    owner = reference.retain_final_publication_v2(
        candidates, parent_configuration=parent_configuration_fixture_v2(candidates)
    )
    assert hasattr(owner, "domain_manifest"), "final owner has no domain projection"
    domain = owner.domain_manifest()
    _validator("next-domain-manifest-v2.schema.json").validate(domain)
    runtime = candidates.run_decision().runtime_result()
    context = runtime.request_frame().analysis_context()
    assert domain["config"] == context.domain_config()
    assert domain["run_context"] == context.run_context()
    assert domain["request_independent"] is False
    assert domain["request"]["projects"] == context.domain_config()["projects"]
    assert domain["run_fingerprint"] is None
    assert "run_fingerprint" not in domain["request"]
    assert (domain["status"], domain["incomplete_kind"], domain["payload_available"]) == (
        "incomplete",
        "payload_unavailable",
        False,
    )
    assert domain["entity_count"] is domain["budget"]["actual"] is None
    assert domain["semantic_compatibility_id"] is domain["compatibility_descriptor"] is None
    assert domain["identity_versions"] is None
    assert domain["toolchain"]["node"] == {
        "status": "unavailable",
        "version": None,
        "failure_kind": "spawn_failed",
    }
    assert domain["coverage"]["target_completeness"] == []
    assert domain["coverage"]["counts"]["internal_entities"] == 0
    assert domain["artifact_paths"] == []
    assert domain["decision"] == candidates.run_decision().record()
    assert domain["publication"] == owner.record()
    assert domain["diagnostics"] == list(owner.manifest_diagnostics())
    domain["request"]["projects"].clear()
    assert owner.domain_manifest()["request"]["projects"]


def test_complete_domain_uses_the_same_admitted_semantic_result(tmp_path: Path) -> None:
    candidates = complete_candidates_v3(tmp_path)
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    owner = reference.retain_final_publication_v2(
        candidates, parent_configuration=parent_configuration_fixture_v2(candidates)
    )
    domain = owner.domain_manifest()
    _validator("next-domain-manifest-v2.schema.json").validate(domain)
    semantic = json.loads(candidates.artifacts()[0].wire_bytes())
    assert domain["status"] == "complete"
    assert "incomplete_kind" not in domain
    assert domain["payload_available"] is True
    assert domain["entity_count"] == domain["budget"]["actual"] == 4
    assert domain["budget"]["outcome"] == "complete"
    for key in (
        "projects",
        "coverage",
        "source",
        "request",
        "compatibility_descriptor",
        "semantic_compatibility_id",
        "identity_versions",
    ):
        assert domain[key] == semantic[key]
    assert domain["run_fingerprint"] == semantic["request"]["run_fingerprint"]
    assert (
        domain["run_fingerprint"]
        == candidates.run_decision().record()["context"]["run_fingerprint"]
    )
    assert domain["toolchain"]["node"] == {
        "status": "available",
        "version": "22.10.0",
        "failure_kind": None,
    }
    assert domain["toolchain"]["node_version"] == "22.10.0"
    assert domain["artifact_paths"] == [
        item.descriptor()["path"] for item in candidates.artifacts()
    ]


def test_rejected_core_domain_keeps_fingerprint_but_not_unvalidated_model(tmp_path: Path) -> None:
    candidates = rejected_candidates_v3(tmp_path, selector="next:semantic-json")
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    owner = reference.retain_final_publication_v2(
        candidates, parent_configuration=parent_configuration_fixture_v2(candidates)
    )
    domain = owner.domain_manifest()
    _validator("next-domain-manifest-v2.schema.json").validate(domain)
    fingerprint = candidates.run_decision().record()["context"]["run_fingerprint"]
    assert isinstance(fingerprint, str)
    assert domain["run_fingerprint"] == domain["request"]["run_fingerprint"] == fingerprint
    assert domain["toolchain"]["node_version"] == "22.10.0"
    assert domain["entity_count"] is domain["budget"]["actual"] is None
    assert domain["compatibility_descriptor"] is domain["identity_versions"] is None
    assert domain["coverage"]["counts"]["internal_entities"] == 0
    assert domain["coverage"]["target_completeness"] == []
    assert domain["artifact_paths"] == []


def test_timeout_domain_does_not_claim_spawn_failure_or_runtime_observation(tmp_path: Path) -> None:
    candidates = observed_zero_capture_candidates_v3(tmp_path)
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    owner = reference.retain_final_publication_v2(
        candidates, parent_configuration=parent_configuration_fixture_v2(candidates)
    )
    domain = owner.domain_manifest()
    assert domain["toolchain"]["node"] == {
        "status": "unavailable",
        "version": None,
        "failure_kind": "timeout",
    }
    assert domain["run_fingerprint"] is None
    assert "run_fingerprint" not in domain["request"]


@pytest.mark.parametrize(
    "failure,node",
    [
        (
            "unsupported_runtime",
            {"status": "unavailable", "version": None, "failure_kind": "unsupported_version"},
        ),
        ("semantic_failure", {"status": "available", "version": "22.10.0", "failure_kind": None}),
        (
            "protocol_failure",
            {"status": "unavailable", "version": None, "failure_kind": "process_failed"},
        ),
        (
            "bootstrap_failure",
            {"status": "unavailable", "version": None, "failure_kind": "process_failed"},
        ),
    ],
)
def test_domain_runtime_metadata_uses_observed_control_without_claiming_core_admission(
    tmp_path: Path, failure: str, node: dict[str, Any]
) -> None:
    candidates = runtime_control_failure_candidates_v3(tmp_path, failure)
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    owner = reference.retain_final_publication_v2(
        candidates, parent_configuration=parent_configuration_fixture_v2(candidates)
    )
    domain = owner.domain_manifest()
    _validator("next-domain-manifest-v2.schema.json").validate(domain)
    assert domain["toolchain"]["node"] == node
    assert domain["toolchain"]["node_version"] == node["version"]
    assert domain["run_fingerprint"] is domain["compatibility_descriptor"] is None
    assert "run_fingerprint" not in domain["request"]
    assert domain["coverage"]["target_completeness"] == []


def test_domain_validation_rejects_a_schema_valid_invented_fingerprint(tmp_path: Path) -> None:
    candidates = stage_failed_candidates_v3(tmp_path, selector="next:semantic-json")
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    validation = import_module("tests.contracts.next_final_publication_v2_validation")
    owner = reference.retain_final_publication_v2(
        candidates, parent_configuration=parent_configuration_fixture_v2(candidates)
    )
    domain = owner.domain_manifest()
    domain["run_fingerprint"] = "0" * 64
    domain["request"]["run_fingerprint"] = "0" * 64
    _validator("next-domain-manifest-v2.schema.json").validate(domain)
    assert hasattr(validation, "validate_domain_manifest_v2"), (
        "domain has no owner-bound validation"
    )
    with pytest.raises(ValueError, match="fingerprint"):
        validation.validate_domain_manifest_v2(domain, owner)


def test_domain_validation_rejects_schema_valid_drift_from_retained_context(tmp_path: Path) -> None:
    candidates = stage_failed_candidates_v3(tmp_path, selector="next:semantic-json")
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    validation = import_module("tests.contracts.next_final_publication_v2_validation")
    owner = reference.retain_final_publication_v2(
        candidates, parent_configuration=parent_configuration_fixture_v2(candidates)
    )
    original = owner.domain_manifest()
    mutations = [
        (("request", "upstream_depth"), 9),
        (("config", "downstream_depth"), 9),
        (("source", "fingerprint"), "0" * 64),
        (("source", "file_count"), float(original["source"]["file_count"])),
        (("run_context", "budget_resolved"), 99),
        (("budget", "actual"), 0),
        (("limits", "max_entities"), 99),
        (("toolchain", "node", "failure_kind"), "timeout"),
        (("trusted_environment", "sha256"), "0" * 64),
        (("coverage", "counts", "internal_entities"), 1),
        (("projects", 0, "file_ids"), []),
        (("diagnostics",), original["diagnostics"] * 2),
        (("domain_config_digest",), "0" * 64),
        (("source_plan_digest",), "0" * 64),
    ]
    for path, replacement in mutations:
        changed = json.loads(_literal_json(original))
        parent = changed
        for key in path[:-1]:
            parent = parent[key]
        parent[path[-1]] = replacement
        errors = list(_validator("next-domain-manifest-v2.schema.json").iter_errors(changed))
        assert not errors, (path, [list(error.path) for error in errors])
        with pytest.raises(ValueError, match="domain"):
            validation.validate_domain_manifest_v2(changed, owner)


@pytest.mark.parametrize("case", ["partial", "source", "target", "export", "entity"])
def test_domain_retains_only_same_core_coverage_and_entity_measurement(
    tmp_path: Path, case: str
) -> None:
    if case in {"partial", "source"}:
        candidates = source_failure_candidates_v3(
            tmp_path, "parse_file", isolated=case == "partial", selector="next:semantic-json"
        )
    else:
        factory = {
            "target": target_failure_candidates_v3,
            "export": export_failure_candidates_v3,
            "entity": entity_budget_candidates_v3,
        }[case]
        candidates = factory(tmp_path, selector="next:semantic-json")
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    validation = import_module("tests.contracts.next_final_publication_v2_validation")
    owner = reference.retain_final_publication_v2(
        candidates, parent_configuration=parent_configuration_fixture_v2(candidates)
    )
    domain = owner.domain_manifest()
    core = candidates.run_decision().semantic_decision()
    assert core is not None
    model = core.transport_candidate().semantic_payload()["model"]
    assert domain["projects"] == model["projects"]
    assert domain["coverage"] == model["coverage"]
    assert domain["status"] == "incomplete"
    assert domain["incomplete_kind"] == (
        "partial_safe" if case == "partial" else "payload_unavailable"
    )
    assert domain["payload_available"] is (case == "partial")
    assert domain["entity_count"] == (3 if case == "partial" else None)
    assert domain["budget"]["actual"] == (
        3 if case == "partial" else 4 if case == "entity" else None
    )
    assert bool(domain["artifact_paths"]) is (case == "partial")
    assert domain["run_fingerprint"] == domain["request"]["run_fingerprint"]
    domain["coverage"]["counts"]["files"] += 1
    with pytest.raises(ValueError, match="domain coverage"):
        validation.validate_domain_manifest_v2(domain, owner)


def test_stderr_overflow_downgrades_domain_without_rewriting_its_semantic_decision(
    tmp_path: Path,
) -> None:
    candidates = partial_stderr_overflow_candidates_v3(tmp_path)
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    owner = reference.retain_final_publication_v2(
        candidates, parent_configuration=parent_configuration_fixture_v2(candidates)
    )
    assert owner.record()["measurements"]["public_stderr"]["measured_bytes"] > 65_536
    assert owner.record()["publication_outcome"] == "payload_unavailable"
    domain = owner.domain_manifest()
    assert domain["status"] == "incomplete" and domain["incomplete_kind"] == "payload_unavailable"
    assert domain["payload_available"] is False
    assert domain["entity_count"] is domain["budget"]["actual"] is None
    assert domain["budget"]["outcome"] == "payload_unavailable"
    assert domain["artifact_paths"] == []
    assert domain["decision"]["outcome"] == "partial_safe"
    assert domain["decision"]["core_measurement"]["actual"] == 4
    assert len(domain["coverage"]["failed_files"]) == 80
    assert [row["code"] for row in domain["diagnostics"]] == ["CSV-NEXT-LIMIT-003"]
    assert domain["run_fingerprint"] == domain["decision"]["context"]["run_fingerprint"]

    root = owner.run_manifest()
    assert root["domains"] == [domain]
    assert root["artifacts"] == []
    assert root["run"]["status"] == "incomplete" and root["run"]["exit_code"] == 3
    assert root["run"]["fingerprint"] == domain["run_fingerprint"]
    assert owner.run_summary()["domains"] == [
        {"domain": "next", "status": "incomplete", "incomplete_kind": "payload_unavailable"}
    ]


def test_parent_configuration_retains_explicit_selections_without_inferring_defaults(
    tmp_path: Path,
) -> None:
    _, _, request, _, _ = core_inputs_v3(tmp_path)
    context = request.analysis_context()
    config = context.domain_config()
    selections: dict[str, Any] = {
        "next_projects": {"value": ["."], "source": "explicit"},
        "next_targets": {"value": [], "source": "cli"},
        "formats": {"value": ["semantic-json"], "source": "repository"},
        "upstream_depth": {"value": 1, "source": "builtin"},
        "downstream_depth": {"value": 1, "source": "explicit"},
        "limits": {"value": config["limits"], "source": "builtin"},
        "trusted_environment": {"value": config["trusted_environment_digest"], "source": "builtin"},
    }
    original = _literal_json(selections)
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    assert hasattr(reference, "retain_parent_configuration_v2"), "parent choices are not retained"
    parent = reference.retain_parent_configuration_v2(
        context, source="explicit", selections=selections
    )
    assert parent.analysis_context() is context
    assert parent.source == "explicit"
    assert _literal_json(parent.selections()) == original
    selections["next_targets"]["source"] = "builtin"
    parent.selections()["next_projects"]["value"].append("other")
    assert _literal_json(parent.selections()) == original


@pytest.mark.parametrize(
    "name,value",
    [
        ("next_projects", ["elsewhere"]),
        ("next_targets", ["path:src/button.tsx"]),
        ("formats", ["plantuml"]),
        ("upstream_depth", 2),
        ("downstream_depth", 0),
        ("limits", {}),
        ("trusted_environment", "0" * 64),
    ],
)
def test_parent_selected_values_must_match_the_analysis_context(
    tmp_path: Path, name: str, value: Any
) -> None:
    _, _, request, _, _ = core_inputs_v3(tmp_path)
    context = request.analysis_context()
    selections = explicit_parent_selections_v2(context)
    selections[name]["value"] = value
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    with pytest.raises(ValueError, match="selected value"):
        reference.retain_parent_configuration_v2(context, source="explicit", selections=selections)


@pytest.mark.parametrize(
    "case", ["extra", "missing", "invalid_origin", "unobserved", "overall_cli", "extra_row"]
)
def test_parent_configuration_accepts_only_the_closed_observed_selection_input(
    tmp_path: Path, case: str
) -> None:
    _, _, request, _, _ = core_inputs_v3(tmp_path)
    context = request.analysis_context()
    selections = explicit_parent_selections_v2(context)
    source = "explicit"
    if case == "extra":
        selections["unrelated"] = {"value": None, "source": "builtin"}
    elif case == "missing":
        del selections["formats"]
    elif case == "invalid_origin":
        selections["formats"]["source"] = "tsconfig.json"
    elif case == "unobserved":
        selections["limits"]["source"] = "unobserved"
    elif case == "overall_cli":
        source = "cli"
    else:
        selections["formats"]["path"] = "/private/config.json"
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    with pytest.raises(ValueError, match="parent selection"):
        reference.retain_parent_configuration_v2(context, source=source, selections=selections)


def test_parent_configuration_rejects_equal_content_foreign_context(tmp_path: Path) -> None:
    (tmp_path / "original").mkdir()
    (tmp_path / "foreign").mkdir()
    _, _, request, _, _ = core_inputs_v3(tmp_path / "original")
    _, _, foreign_request, _, _ = core_inputs_v3(tmp_path / "foreign")
    context, foreign = request.analysis_context(), foreign_request.analysis_context()
    assert context is not foreign and context.domain_config() == foreign.domain_config()
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    parent = reference.retain_parent_configuration_v2(
        context, source="explicit", selections=explicit_parent_selections_v2(context)
    )
    validation = import_module("tests.contracts.next_final_publication_v2_validation")
    with pytest.raises(ValueError, match="same analysis context"):
        validation.validate_parent_configuration_v2(parent, context=foreign)


def test_parent_configuration_requires_nominal_input_owners(tmp_path: Path) -> None:
    _, _, request, _, _ = core_inputs_v3(tmp_path)
    context = request.analysis_context()
    selections = explicit_parent_selections_v2(context)
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    foreign = SimpleNamespace(domain_config=context.domain_config, run_context=context.run_context)
    with pytest.raises(TypeError, match="nominal"):
        reference.retain_parent_configuration_v2(foreign, source="explicit", selections=selections)
    parent = reference.retain_parent_configuration_v2(
        context, source="explicit", selections=selections
    )
    forged = SimpleNamespace(
        analysis_context=lambda: context, source="explicit", selections=parent.selections
    )
    validation = import_module("tests.contracts.next_final_publication_v2_validation")
    with pytest.raises(TypeError, match="nominal"):
        validation.validate_parent_configuration_v2(forged, context=context)


@pytest.mark.parametrize("source", ["builtin", "repository", "explicit"])
@pytest.mark.parametrize("origin", ["builtin", "repository", "explicit", "cli"])
def test_parent_configuration_preserves_every_legal_origin(
    tmp_path: Path, source: str, origin: str
) -> None:
    _, _, request, _, _ = core_inputs_v3(tmp_path)
    context = request.analysis_context()
    selections = explicit_parent_selections_v2(context)
    for row in selections.values():
        row["source"] = origin
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    parent = reference.retain_parent_configuration_v2(context, source=source, selections=selections)
    assert parent.source == source
    assert parent.selections() == selections


@pytest.mark.parametrize("value", [True, 1.0])
def test_parent_configuration_does_not_coerce_selected_numbers(tmp_path: Path, value: Any) -> None:
    _, _, request, _, _ = core_inputs_v3(tmp_path)
    context = request.analysis_context()
    selections = explicit_parent_selections_v2(context)
    selections["upstream_depth"]["value"] = value
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    with pytest.raises(ValueError, match="selected value"):
        reference.retain_parent_configuration_v2(context, source="explicit", selections=selections)


def test_final_publication_requires_the_parent_configuration_input(tmp_path: Path) -> None:
    candidates = stage_failed_candidates_v3(tmp_path, selector="next:semantic-json")
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    with pytest.raises(TypeError, match="parent_configuration"):
        reference.retain_final_publication_v2(candidates)


def test_final_publication_rejects_foreign_parent_configuration_even_with_equal_values(
    tmp_path: Path,
) -> None:
    (tmp_path / "original").mkdir()
    (tmp_path / "foreign").mkdir()
    candidates = stage_failed_candidates_v3(tmp_path / "original", selector="next:semantic-json")
    foreign = stage_failed_candidates_v3(tmp_path / "foreign", selector="next:semantic-json")
    parent = parent_configuration_fixture_v2(candidates)
    foreign_parent = parent_configuration_fixture_v2(foreign)
    assert parent.selections() == foreign_parent.selections()
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    with pytest.raises(ValueError, match="same analysis context"):
        reference.retain_final_publication_v2(candidates, parent_configuration=foreign_parent)
    owner = reference.retain_final_publication_v2(candidates, parent_configuration=parent)
    assert owner.parent_configuration() is parent
    forged = copy(owner)
    object.__setattr__(forged, "_parent_configuration", foreign_parent)
    with pytest.raises(ValueError, match="same analysis context"):
        reference.project_final_publication_v2(forged)


def _aligned_unavailable_cache(owner: Any, value: dict[str, Any]) -> Any:
    """Attacker reseals a claim; actual candidate/run authorities stay unchanged."""
    assert owner.candidates().run_decision().semantic_decision() is None
    assert owner.candidates().artifacts() == ()
    assert value["response"] is None and value["artifacts"] == []
    selector = value["stdout"]["selector"]
    assert selector in {"next:semantic-json", "manifest"}
    selected_raw = owner._manifest_input_bytes if selector == "manifest" else b""
    assert isinstance(selected_raw, bytes)
    stdout = base64.b64decode(value["stdout"]["result_bytes_base64"])
    stderr = base64.b64decode(value["stderr"]["bytes_base64"])
    boundary = {
        "decision_run_fingerprint": None,
        "response_bytes": {"__bytes_hex__": ""},
        "validated_request_id": None,
        "response_sha256": None,
        "response_model_digest": None,
        "artifact_bytes": {},
        "artifact_descriptors": {},
        "selector": selector,
        "selected_stdout": {
            "allowed": True,
            "bytes": len(selected_raw),
            "sha256": hashlib.sha256(selected_raw).hexdigest(),
            "retained": {"__bytes_hex__": selected_raw.hex()},
            "retained_bytes": len(selected_raw),
            "partial_disposed": False,
            "publication_outcome": "published_artifact",
            "diagnostic_code": None,
        },
        "sealed_stdout_result": {"__bytes_hex__": stdout.hex()},
        "diagnostic_jsonl": {"__bytes_hex__": stderr.hex()},
        "measurement_digest": _literal_sha(value["measurements"]),
    }
    public = {
        "semantic_decision": value["semantic_decision"],
        "response": value["response"],
        "artifacts": value["artifacts"],
        "stdout": value["stdout"],
        "stderr": stderr.hex(),
        "measurements": value["measurements"],
    }
    assert len(boundary) == 12 and len(public) == 6
    value["seal"] = {
        "algorithm": "sha256",
        "sha256": _literal_sha(boundary),
        "preimage_sha256": _literal_sha(public),
    }
    forged = copy(owner)
    object.__setattr__(forged, "_record_bytes", _literal_json(value))
    return forged


def test_resealed_manifest_candidate_must_still_match_original_parent_and_run(
    tmp_path: Path,
) -> None:
    candidates = stage_failed_candidates_v3(tmp_path, selector="manifest")
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    owner = reference.retain_final_publication_v2(
        candidates, parent_configuration=parent_configuration_fixture_v2(candidates)
    )
    original = owner.record()
    control = _aligned_unavailable_cache(owner, owner.record())
    assert control.record() == original
    assert reference.project_final_publication_v2(control) == original
    for mutation, expected_error in [
        ("origin", "root config"),
        ("fingerprint", "root run"),
        ("native", "domain source"),
        ("sidecar", "outside"),
        ("encoding", "canonical"),
    ]:
        manifest = json.loads(owner.stdout_bytes())
        if mutation == "origin":
            manifest["config"]["value_sources"]["next_projects"] = "builtin"
            manifest["config"]["sha256"] = _literal_sha(
                {key: value for key, value in manifest["config"].items() if key != "sha256"}
            )
        elif mutation == "fingerprint":
            manifest["run"]["fingerprint"] = "0" * 64
        elif mutation == "native":
            source = manifest["domains"][0]["source"]
            source["file_count"] = float(source["file_count"])
        elif mutation == "sidecar":
            manifest["next_publication"] = original
        _validator("run-manifest-v2.schema.json").validate(manifest)
        raw = (
            json.dumps(manifest, indent=2).encode()
            if mutation == "encoding"
            else _literal_json(manifest)
        ) + b"\n"
        forged = copy(owner)
        object.__setattr__(forged, "_manifest_input_bytes", raw)
        object.__setattr__(forged, "_stdout_bytes", raw)
        value = owner.record()
        raw_sha = hashlib.sha256(raw).hexdigest()
        value["stdout"].update(
            selected_size_bytes=len(raw),
            selected_sha256=raw_sha,
            result_size_bytes=len(raw),
            result_sha256=raw_sha,
            result_bytes_base64=base64.b64encode(raw).decode("ascii"),
        )
        value["stdout"]["candidate"].update(size_bytes=len(raw), sha256=raw_sha)
        value["measurements"]["selected_stdout"].update(
            measured_bytes=len(raw), retained_bytes=len(raw)
        )
        forged = _aligned_unavailable_cache(forged, value)
        _validator("next-publication-decision-v2.schema.json").validate(forged.record())
        with pytest.raises(ValueError, match=expected_error):
            reference.project_final_publication_v2(forged)


@pytest.mark.parametrize(
    "group,key,kind",
    [
        (None, "version", "float"),
        (None, "version", "bool"),
        (None, "exit_code", "float"),
        ("public_stderr", "measured_bytes", "float"),
        ("public_stderr", "retained_bytes", "float"),
        ("selected_stdout", "measured_bytes", "float"),
        ("selected_stdout", "retained_bytes", "float"),
        ("selected_stdout", "retained_bytes", "bool"),
        ("adapter_stdout", "measured_bytes", "float"),
        ("adapter_stderr", "retained_bytes", "float"),
        ("adapter_stderr", "retained_bytes", "bool"),
    ],
)
def test_aligned_resealed_cache_cannot_coerce_native_counts_or_version(
    tmp_path: Path,
    group: str | None,
    key: str,
    kind: str,
) -> None:
    candidates = (
        observed_zero_capture_candidates_v3(tmp_path)
        if group is not None and group.startswith("adapter_")
        else stage_failed_candidates_v3(tmp_path, selector="next:semantic-json")
    )
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    owner = reference.retain_final_publication_v2(
        candidates, parent_configuration=parent_configuration_fixture_v2(candidates)
    )
    reference.project_final_publication_v2(owner)
    value = owner.record()
    location = value if group is None else value["measurements"][group]
    location[key] = float(location[key]) if kind == "float" else False
    forged = _aligned_unavailable_cache(owner, value)
    assert forged.record() == value
    if kind == "float":
        # JSON Schema's integer vocabulary accepts 0.0/2.0; owner-native types do not.
        _validator("next-publication-decision-v2.schema.json").validate(value)
    with pytest.raises((ValueError, ValidationError)):
        reference.project_final_publication_v2(forged)


def test_equal_content_foreign_candidates_and_run_do_not_replace_the_actual_owner(
    tmp_path: Path,
) -> None:
    original_path, foreign_path = tmp_path / "original", tmp_path / "foreign"
    original_path.mkdir()
    foreign_path.mkdir()
    original = stage_failed_candidates_v3(original_path, selector="next:semantic-json")
    foreign = stage_failed_candidates_v3(foreign_path, selector="next:semantic-json")
    assert original is not foreign
    assert original.run_decision() is not foreign.run_decision()
    assert original.record() == foreign.record()
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    validate = import_module(
        "tests.contracts.next_final_publication_v2_validation"
    ).validate_final_publication_v2
    owner = reference.retain_final_publication_v2(
        original, parent_configuration=parent_configuration_fixture_v2(original)
    )
    value = reference.project_final_publication_v2(owner)
    _validator("next-publication-decision-v2.schema.json").validate(value)
    with pytest.raises(ValueError, match="same candidates owner"):
        validate(value, owner, candidates=foreign)


def test_complete_final_owner_publishes_the_same_artifact_and_catalog_stderr(
    tmp_path: Path,
) -> None:
    candidates = complete_candidates_v3(tmp_path)
    module = "tests.contracts.next_final_publication_v2_reference"
    assert util.find_spec(module) is not None, "actual candidates have no final publication owner"
    reference = import_module(module)
    owner = reference.retain_final_publication_v2(
        candidates, parent_configuration=parent_configuration_fixture_v2(candidates)
    )
    value = reference.project_final_publication_v2(owner)
    assert owner.candidates() is candidates
    artifact = candidates.artifacts()[0]
    assert value["semantic_decision"] == candidates.run_decision().record()
    assert value["candidates"] == candidates.record()
    assert value["publication_outcome"] == "published" and value["exit_code"] == 0
    assert base64.b64decode(value["stdout"]["result_bytes_base64"]) == artifact.wire_bytes()
    assert value["stdout"]["candidate"] == artifact.descriptor()
    assert value["artifacts"] == [
        {
            "descriptor": artifact.descriptor(),
            "bytes_base64": base64.b64encode(artifact.wire_bytes()).decode("ascii"),
        }
    ]
    expected_row = {
        "type": "diagnostic",
        "schema": "code-structure-viz.diagnostic/v1",
        "domain": "next",
        "code": "CSV-NEXT-UNSUPPORTED-001",
        "severity": "info",
        "recoverable": True,
        "message": "A runtime-dependent pattern is intentionally represented as unknown.",
        "outcome": "complete",
        "ref_permission": "symbol",
        "path": None,
        "symbol": MODULE_IDS["src/value.ts"],
        "line": None,
    }
    expected_stderr = (
        json.dumps(expected_row, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        + b"\n"
    )
    assert owner.stdout_bytes() == artifact.wire_bytes()
    assert owner.stderr_bytes() == expected_stderr
    assert base64.b64decode(value["stderr"]["bytes_base64"]) == expected_stderr
    assert value["stderr"]["sha256"] == hashlib.sha256(expected_stderr).hexdigest()
    assert value["measurements"]["public_stderr"] == {
        "allowed": True,
        "measured_bytes": len(expected_stderr),
        "retained_bytes": len(expected_stderr),
    }
    assert value["measurements"]["selected_stdout"] == {
        "allowed": True,
        "measured_bytes": len(artifact.wire_bytes()),
        "retained_bytes": len(artifact.wire_bytes()),
    }
    _validator("next-publication-decision-v2.schema.json").validate(value)


@pytest.mark.parametrize("selector", ["next:semantic-json", "manifest"])
def test_partial_safe_final_projection_keeps_private_proof_and_source_bytes_private(
    tmp_path: Path,
    selector: str,
) -> None:
    candidates = source_failure_candidates_v3(
        tmp_path, "parse_file", isolated=True, selector=selector
    )
    core = candidates.run_decision().semantic_decision()
    assert core is not None
    transport = core.transport_candidate()
    assert transport.semantic_payload()["proof"]["failure_roots"]
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    owner = reference.retain_final_publication_v2(
        candidates, parent_configuration=parent_configuration_fixture_v2(candidates)
    )
    value = reference.project_final_publication_v2(owner)
    assert value["semantic_decision"]["outcome"] == "partial_safe"
    artifact_documents = [
        json.loads(base64.b64decode(row["bytes_base64"])) for row in value["artifacts"]
    ]
    stderr_rows = [json.loads(row) for row in owner.stderr_bytes().splitlines()]
    assert stderr_rows[0]["path"] == "src/value.ts"  # Catalog-authorized ref stays public.
    public_values = [
        value,
        owner.run_manifest(),
        owner.run_summary(),
        json.loads(owner.stdout_bytes()),
        *stderr_rows,
        *artifact_documents,
    ]
    private_keys = {
        "proof",
        "content_base64",
        "source_bytes",
        "failure_roots",
        "affected_paths",
        "effect_edges",
        "raw_response_bytes",
        "raw_child_stderr",
        "raw_stderr",
        "pid",
        "pgid",
        "cwd",
    }
    public_strings: list[str] = []

    def check_public(item: Any) -> None:
        if isinstance(item, dict):
            assert not private_keys.intersection(item)
            for child in item.values():
                check_public(child)
        elif isinstance(item, list):
            for child in item:
                check_public(child)
        elif isinstance(item, str):
            public_strings.append(item)

    for document in public_values:
        check_public(document)
    response = transport.response_frame().raw_bytes
    assert base64.b64encode(response).decode("ascii") not in public_strings
    for content in SOURCE_BYTES.values():
        assert not any(content.decode().strip() in text for text in public_strings)
        assert base64.b64encode(content).decode("ascii") not in public_strings
    _validator("next-publication-decision-v2.schema.json").validate(value)


def test_target_unavailable_stdout_retains_the_actual_failed_target(tmp_path: Path) -> None:
    candidates = target_failure_candidates_v3(tmp_path, selector="next:semantic-json")
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    owner = reference.retain_final_publication_v2(
        candidates, parent_configuration=parent_configuration_fixture_v2(candidates)
    )
    value = reference.project_final_publication_v2(owner)
    assert value["publication_outcome"] == "published" and value["exit_code"] == 3
    assert value["response"] is not None and value["artifacts"] == []
    expected = {
        "type": "stdout_result",
        "schema": "code-structure-viz.stdout-result/v2",
        "selector": "next:semantic-json",
        "availability": False,
        "domain_status": "incomplete",
        "stable_reason": "target_payload_unavailable",
        "artifact": None,
        "target_failures": [{"target_key": "path:src/button.tsx", "reason": "missing"}],
    }
    actual = json.loads(owner.stdout_bytes())
    assert actual == expected
    _validator("stdout-result-v2.schema.json").validate(actual)


def test_observed_zero_capture_is_not_replaced_by_unobserved_null(tmp_path: Path) -> None:
    candidates = observed_zero_capture_candidates_v3(tmp_path)
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    validate = import_module(
        "tests.contracts.next_final_publication_v2_validation"
    ).validate_final_publication_v2
    owner = reference.retain_final_publication_v2(
        candidates, parent_configuration=parent_configuration_fixture_v2(candidates)
    )
    value = reference.project_final_publication_v2(owner)
    assert value["publication_outcome"] == "published" and value["exit_code"] == 3
    assert value["semantic_decision"]["provenance"]["failure_code"] == "CSV-NEXT-NODE-003"
    assert value["response"] is None
    for name in ("adapter_stdout", "adapter_stderr"):
        assert value["measurements"][name] == {
            "allowed": True,
            "measured_bytes": 0,
            "retained_bytes": 0,
        }
    value["measurements"].update(adapter_stdout=None, adapter_stderr=None)
    # Align both seal claims and cache; this still is not a new capture observation.
    changed = _aligned_unavailable_cache(owner, value)
    _validator("next-publication-decision-v2.schema.json").validate(value)
    with pytest.raises(ValueError, match="capture measurement"):
        validate(value, changed, candidates=candidates)


def test_unobserved_capture_cannot_be_zero_filled_in_aligned_metadata(tmp_path: Path) -> None:
    candidates = stage_failed_candidates_v3(tmp_path, selector="next:semantic-json")
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    validate = import_module(
        "tests.contracts.next_final_publication_v2_validation"
    ).validate_final_publication_v2
    owner = reference.retain_final_publication_v2(
        candidates, parent_configuration=parent_configuration_fixture_v2(candidates)
    )
    value = owner.record()
    for name in ("adapter_stdout", "adapter_stderr"):
        value["measurements"][name] = {
            "allowed": True,
            "measured_bytes": 0,
            "retained_bytes": 0,
        }
    changed = _aligned_unavailable_cache(owner, value)
    _validator("next-publication-decision-v2.schema.json").validate(value)
    with pytest.raises(ValueError, match="capture measurement"):
        validate(value, changed, candidates=candidates)


def test_stage_failure_final_owner_preserves_unobserved_capture_and_publishes_the_failure(
    tmp_path: Path,
) -> None:
    candidates = stage_failed_candidates_v3(tmp_path, selector="next:semantic-json")
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    owner = reference.retain_final_publication_v2(
        candidates, parent_configuration=parent_configuration_fixture_v2(candidates)
    )
    value = reference.project_final_publication_v2(owner)
    expected_stdout = (
        b'{"artifact":null,"availability":false,"domain_status":"incomplete",'
        b'"schema":"code-structure-viz.stdout-result/v2","selector":"next:semantic-json",'
        b'"stable_reason":"domain_payload_unavailable","type":"stdout_result"}\n'
    )
    assert owner.candidates() is candidates
    assert value["semantic_decision"] == candidates.run_decision().record()
    assert value["publication_outcome"] == "published" and value["exit_code"] == 3
    assert value["response"] is None and value["artifacts"] == []
    assert value["measurements"]["adapter_stdout"] is None
    assert value["measurements"]["adapter_stderr"] is None
    assert value["stdout"]["copy_status"] == "not_attempted"
    assert value["stdout"]["candidate"] is None
    assert value["stdout"]["availability"] is False
    assert owner.stdout_bytes() == expected_stdout
    assert owner.stderr_bytes() == NODE_002_JSONL
    assert base64.b64decode(value["stdout"]["result_bytes_base64"]) == expected_stdout
    assert value["measurements"]["selected_stdout"] == {
        "allowed": True,
        "measured_bytes": 0,
        "retained_bytes": 0,
    }
    assert value["measurements"]["public_stderr"] == {
        "allowed": True,
        "measured_bytes": 304,
        "retained_bytes": 304,
    }
    measurements = {
        "adapter_stdout": None,
        "adapter_stderr": None,
        "public_stderr": {"allowed": True, "measured_bytes": 304, "retained_bytes": 304},
        "selected_stdout": {"allowed": True, "measured_bytes": 0, "retained_bytes": 0},
    }
    measurement_sha = _literal_sha(measurements)
    assert measurement_sha == "55e1176ea7f986b17dd9179ef571767614c50f3fd10dd79a1b08afc092675bef"
    preimage = {
        "decision_run_fingerprint": None,
        "response_bytes": {"__bytes_hex__": ""},
        "validated_request_id": None,
        "response_sha256": None,
        "response_model_digest": None,
        "artifact_bytes": {},
        "artifact_descriptors": {},
        "selector": "next:semantic-json",
        "selected_stdout": {
            "allowed": True,
            "bytes": 0,
            "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "retained": {"__bytes_hex__": ""},
            "retained_bytes": 0,
            "partial_disposed": False,
            "publication_outcome": "published_artifact",
            "diagnostic_code": None,
        },
        "sealed_stdout_result": {"__bytes_hex__": expected_stdout.hex()},
        "diagnostic_jsonl": {"__bytes_hex__": NODE_002_JSONL.hex()},
        "measurement_digest": measurement_sha,
    }
    assert len(preimage) == 12
    boundary_sha = _literal_sha(preimage)
    assert boundary_sha == "b790e3d366dec43adad1c2ed0926e33d5961f81d699d40423370e3f66a822e27"
    assert value["seal"]["sha256"] == boundary_sha
    _validator("stdout-result-v2.schema.json").validate(json.loads(expected_stdout))
    _validator("next-publication-decision-v2.schema.json").validate(value)


@pytest.mark.parametrize("kind", ["parse_file", "read_file"])
def test_source_unavailable_is_published_with_its_same_validated_response(
    tmp_path: Path,
    kind: str,
) -> None:
    candidates = source_failure_candidates_v3(tmp_path, kind, selector="next:semantic-json")
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    owner = reference.retain_final_publication_v2(
        candidates, parent_configuration=parent_configuration_fixture_v2(candidates)
    )
    value = reference.project_final_publication_v2(owner)
    run = candidates.run_decision()
    core = run.semantic_decision()
    assert core is not None
    frame = core.transport_candidate().response_frame()
    assert value["publication_outcome"] == "published" and value["exit_code"] == 3
    assert value["semantic_decision"]["outcome"] == "payload_unavailable"
    assert value["semantic_decision"] == run.record()
    assert value["response"] == {
        "request_id": run.runtime_result().request_frame().request_id,
        "raw_sha256": hashlib.sha256(frame.raw_bytes).hexdigest(),
        "model_digest": core.transport_candidate().semantic_payload()["model_digest"],
        "byte_length": len(frame.raw_bytes),
    }
    assert value["artifacts"] == [] and value["stdout"]["copy_status"] == "not_attempted"
    for name in ("adapter_stdout", "adapter_stderr"):
        actual = candidates.record()["capture_measurements"][name]
        assert value["measurements"][name] == {
            "allowed": True,
            "measured_bytes": actual["captured_bytes"],
            "retained_bytes": actual["capture_retained_bytes"],
        }
    stderr_row = json.loads(owner.stderr_bytes())
    assert stderr_row["code"] == "CSV-NEXT-SOURCE-003"
    assert stderr_row["path"] == "src/value.ts" and stderr_row["symbol"] is None
    _validator("next-publication-decision-v2.schema.json").validate(value)


def test_rejected_core_can_publish_the_failure_but_not_an_eligible_response_link(
    tmp_path: Path,
) -> None:
    candidates = rejected_candidates_v3(tmp_path, selector="next:semantic-json")
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    owner = reference.retain_final_publication_v2(
        candidates, parent_configuration=parent_configuration_fixture_v2(candidates)
    )
    value = reference.project_final_publication_v2(owner)
    assert value["semantic_decision"]["provenance"]["failure_code"] == "CSV-NEXT-PROTOCOL-001"
    assert value["publication_outcome"] == "published" and value["exit_code"] == 3
    assert value["response"] is None and value["artifacts"] == []
    assert json.loads(owner.stderr_bytes())["code"] == "CSV-NEXT-PROTOCOL-001"
    assert value["stdout"]["copy_status"] == "not_attempted"
    _validator("next-publication-decision-v2.schema.json").validate(value)


@pytest.mark.parametrize("case", ["export", "entity_budget", "partial_safe"])
def test_other_validated_failures_preserve_their_semantic_axis_and_eligible_response(
    tmp_path: Path,
    case: str,
) -> None:
    if case == "export":
        candidates = export_failure_candidates_v3(tmp_path, selector="next:semantic-json")
        expected_code = "CSV-NEXT-EXPORT-001"
    elif case == "entity_budget":
        candidates = entity_budget_candidates_v3(tmp_path, selector="next:semantic-json")
        expected_code = "CSV-NEXT-LIMIT-005"
    else:
        candidates = source_failure_candidates_v3(
            tmp_path, "parse_file", isolated=True, selector="next:semantic-json"
        )
        expected_code = "CSV-NEXT-SOURCE-001"
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    owner = reference.retain_final_publication_v2(
        candidates, parent_configuration=parent_configuration_fixture_v2(candidates)
    )
    value = reference.project_final_publication_v2(owner)
    run = candidates.run_decision()
    core = run.semantic_decision()
    assert core is not None
    frame = core.transport_candidate().response_frame()
    assert value["publication_outcome"] == "published" and value["exit_code"] == 3
    assert value["semantic_decision"] == run.record()
    assert value["response"]["raw_sha256"] == hashlib.sha256(frame.raw_bytes).hexdigest()
    assert {json.loads(row)["code"] for row in owner.stderr_bytes().splitlines()} == {expected_code}
    if case == "partial_safe":
        assert value["semantic_decision"]["outcome"] == "partial_safe"
        assert value["stdout"]["copy_status"] == "published"
        assert owner.stdout_bytes() == candidates.artifacts()[0].wire_bytes()
    else:
        assert value["semantic_decision"]["outcome"] == "payload_unavailable"
        assert value["artifacts"] == [] and value["stdout"]["copy_status"] == "not_attempted"
    _validator("next-publication-decision-v2.schema.json").validate(value)


@pytest.mark.parametrize("stream,measured", [("stdout", 16_777_217), ("stderr", 65_537)])
def test_actual_adapter_capture_overflow_is_a_publication_failure_not_null_capture(
    tmp_path: Path,
    stream: str,
    measured: int,
) -> None:
    candidates = capture_overflow_candidates_v3(tmp_path, stream)
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    owner = reference.retain_final_publication_v2(
        candidates, parent_configuration=parent_configuration_fixture_v2(candidates)
    )
    value = reference.project_final_publication_v2(owner)
    assert value["publication_outcome"] == "payload_unavailable" and value["exit_code"] == 3
    assert value["response"] is None and value["artifacts"] == []
    assert value["measurements"]["adapter_" + stream] == {
        "allowed": False,
        "measured_bytes": measured,
        "retained_bytes": 0,
    }
    other = "stderr" if stream == "stdout" else "stdout"
    assert value["measurements"]["adapter_" + other] == {
        "allowed": True,
        "measured_bytes": 0,
        "retained_bytes": 0,
    }
    assert value["stdout"]["copy_status"] == "not_attempted"
    assert value["measurements"]["selected_stdout"] == {
        "allowed": True,
        "measured_bytes": 0,
        "retained_bytes": 0,
    }
    assert json.loads(owner.stderr_bytes())["code"] == "CSV-NEXT-LIMIT-003"
    _validator("next-publication-decision-v2.schema.json").validate(value)


@pytest.mark.parametrize("delta", [0, 1])
def test_configured_public_stderr_boundary_keeps_all_or_no_bytes(
    tmp_path: Path, delta: int
) -> None:
    candidates = stderr_boundary_candidates_v3(tmp_path, delta)
    request = candidates.run_decision().runtime_result().request_frame().record()
    assert request["limits"]["max_stderr_bytes"] == 65_536
    # Independent catalog literal and stdlib codec, not the diagnostic producer.
    rows = [
        {
            "type": "diagnostic",
            "schema": "code-structure-viz.diagnostic/v1",
            "domain": "next",
            "code": "CSV-NEXT-TARGET-001",
            "severity": "error",
            "recoverable": False,
            "message": "An explicit Next.js target cannot be resolved uniquely.",
            "outcome": "payload_unavailable",
            "ref_permission": "path_or_symbol",
            "path": target.removeprefix("path:"),
            "symbol": None,
            "line": None,
            "reason": "missing",
        }
        for target in request["targets"]
    ]
    expected = b"".join(
        json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode() + b"\n"
        for row in rows
    )
    assert len(expected) == 65_536 + delta
    assert hashlib.sha256(expected).hexdigest() == (
        "702dbbfdd93207ea5e659026f9706d8278a3568eaf401394f57adfda56411216"
        if delta == 0
        else "c9373a44926510bbf4508a8702e0f8f9b217764ea4f1f7979f342c61b3e3a08b"
    )
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    owner = reference.retain_final_publication_v2(
        candidates, parent_configuration=parent_configuration_fixture_v2(candidates)
    )
    value = reference.project_final_publication_v2(owner)
    assert value["measurements"]["public_stderr"] == {
        "allowed": delta == 0,
        "measured_bytes": 65_536 + delta,
        "retained_bytes": 65_536 if delta == 0 else 0,
    }
    if delta == 0:
        assert owner.stderr_bytes() == expected
        assert value["publication_outcome"] == "published"
        assert value["response"] is not None
    else:
        assert owner.stderr_bytes() == b""
        assert value["publication_outcome"] == "payload_unavailable"
        assert value["response"] is None and value["artifacts"] == []
        assert len(owner.manifest_diagnostics()) == 1
        assert owner.manifest_diagnostics()[0]["code"] == "CSV-NEXT-LIMIT-003"
        assert json.loads(owner.stdout_bytes())["stable_reason"] == "domain_payload_unavailable"
    _validator("next-publication-decision-v2.schema.json").validate(value)


@pytest.mark.parametrize("delta", [0, 1])
def test_configured_selected_stdout_boundary_retains_the_original_candidate_measurement(
    tmp_path: Path,
    delta: int,
) -> None:
    candidates, expected = large_selected_stdout_candidates_v3(tmp_path, delta)
    artifact = candidates.artifacts()[0]
    assert artifact.wire_bytes() == expected
    assert len(expected) == 16_777_216 + delta
    assert artifact.descriptor()["size_bytes"] == 16_777_216 + delta
    assert (
        candidates.run_decision()
        .runtime_result()
        .request_frame()
        .record()["limits"]["max_selected_stdout_bytes"]
        == 16_777_216
    )
    reference = import_module("tests.contracts.next_final_publication_v2_reference")
    owner = reference.retain_final_publication_v2(
        candidates, parent_configuration=parent_configuration_fixture_v2(candidates)
    )
    value = reference.project_final_publication_v2(owner)
    assert value["measurements"]["selected_stdout"] == {
        "allowed": delta == 0,
        "measured_bytes": 16_777_216 + delta,
        "retained_bytes": 16_777_216 if delta == 0 else 0,
    }
    assert value["semantic_decision"]["status"] == "complete"
    assert value["response"] is not None
    assert value["stdout"]["candidate"] == artifact.descriptor()
    assert value["artifacts"][0]["descriptor"] == artifact.descriptor()
    if delta == 0:
        assert owner.stdout_bytes() == expected
        assert value["publication_outcome"] == "published" and value["exit_code"] == 0
    else:
        assert value["publication_outcome"] == "selected_artifact_unavailable"
        assert value["exit_code"] == 3 and value["stdout"]["copy_status"] == "unavailable"
        replacement = json.loads(owner.stdout_bytes())
        assert replacement["stable_reason"] == "selected_artifact_unavailable"
        assert replacement["artifact"] == artifact.descriptor()
        assert replacement["selected_stdout_unavailable"] is True
        assert value["stdout"]["result_size_bytes"] == len(owner.stdout_bytes()) < 16_777_216
        assert value["stdout"]["result_sha256"] == hashlib.sha256(owner.stdout_bytes()).hexdigest()
        assert json.loads(owner.stderr_bytes())["code"] == "CSV-NEXT-LIMIT-003"
        assert json.loads(owner.stderr_bytes())["scope"] == "publication"
        _validator("stdout-result-v2.schema.json").validate(replacement)
    root = owner.run_manifest()
    summary = owner.run_summary()
    assert (
        root["run"]["status"]
        == summary["run_status"]
        == ("complete" if delta == 0 else "incomplete")
    )
    assert root["run"]["exit_code"] == summary["exit_code"] == (0 if delta == 0 else 3)
    assert root["domains"][0]["status"] == "complete"
    assert summary["domains"] == [{"domain": "next", "status": "complete"}]
    assert root["artifacts"] == [artifact.descriptor()]
    assert root["run"]["fingerprint"] == value["semantic_decision"]["context"]["run_fingerprint"]
    _validator("next-publication-decision-v2.schema.json").validate(value)
