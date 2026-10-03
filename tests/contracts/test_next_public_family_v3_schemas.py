"""SI-05 schema/ref vectors only; not the executable SI-06 finalizer certificate."""

import base64
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, ValidationError  # type: ignore[import-untyped]

from tests.contracts.next_final_publication_v2_fixtures import stage_failed_candidates_v3
from tests.contracts.next_public_semantic_v3_reference import project_public_semantic_document_v3
from tests.contracts.next_public_semantic_v3_validation import validate_semantic_dispatcher_v3
from tests.contracts.next_publication_candidates_v3_reference import (
    retain_request_bound_publication_candidates_v3,
)
from tests.contracts.next_run_decision_v3_reference import retain_request_bound_run_decision_v3
from tests.contracts.next_runtime_v2_reference import trusted_environment_manifest_v2
from tests.contracts.next_semantic_core_v3_reference import decide_semantic_candidate_v3
from tests.contracts.test_json_schemas import _schema, _validator
from tests.contracts.test_next_core_failure_v2 import runtime_for_core_wire
from tests.contracts.test_next_semantic_core_v3 import core_inputs_v3

ROOT = Path(__file__).resolve().parents[2]
FAMILY = (
    "next-compatibility-v3",
    "next-semantic-v3",
    "semantic-v3",
    "next-provenance-v3",
    "next-run-decision-v3",
    "next-publication-candidates-v3",
    "next-domain-manifest-v2",
    "next-publication-decision-v2",
    "run-manifest-v2",
    "stdout-result-v2",
)
OLD_WHOLE_NEXT = {
    "next-compatibility-v1",
    "next-compatibility-v2",
    "next-semantic-v1",
    "next-semantic-v2",
    "next-provenance-v1",
    "next-provenance-v2",
    "next-run-decision-v1",
    "next-run-decision-v2",
    "next-publication-candidates-v2",
    "next-domain-manifest-v1",
    "next-publication-decision-v1",
}


def refs(value: Any) -> list[str]:
    if isinstance(value, dict):
        return ([value["$ref"]] if "$ref" in value else []) + [
            ref for child in value.values() for ref in refs(child)
        ]
    if isinstance(value, list):
        return [ref for child in value for ref in refs(child)]
    return []


def test_outer_v2_contracts_complete_the_closed_offline_v3_family() -> None:
    identities = []
    for name in FAMILY:
        path = ROOT / "schemas" / f"{name}.schema.json"
        assert path.is_file(), f"public exact-ref family is missing {name}"
        schema = _schema(path.name)
        Draft202012Validator.check_schema(schema)
        assert schema["additionalProperties"] is False
        assert schema["$id"] == f"urn:code-structure-viz:schema:{name}"
        identities.append(schema["$id"])
        validator = _validator(path.name)
        for ref in refs(schema):
            validator._resolver.lookup(ref)
            suffix = ref.removeprefix("urn:code-structure-viz:schema:")
            assert "#" in suffix or suffix not in OLD_WHOLE_NEXT, ref
    assert len(set(identities)) == 10


@pytest.fixture(scope="module")
def outer_vectors(tmp_path_factory: pytest.TempPathFactory) -> dict[str, dict[str, Any]]:
    """Actual run/candidate inputs; literal final metadata only, not a finalizer."""
    seal, assets, request, policy, wire = core_inputs_v3(
        tmp_path_factory.mktemp("outer-schema3"),
        stdout_selector="next:semantic-json",
    )
    runtime = runtime_for_core_wire(seal, assets, request, policy, wire)
    candidate = runtime.transport_candidate()
    assert candidate is not None
    core = decide_semantic_candidate_v3(candidate, seal, assets)
    run = retain_request_bound_run_decision_v3(runtime, semantic_decision=core)
    candidates = retain_request_bound_publication_candidates_v3(run)
    artifact = candidates.artifacts()[0]
    raw, descriptor = artifact.wire_bytes(), artifact.descriptor()
    empty_sha = hashlib.sha256(b"").hexdigest()
    capture = candidates.record()["capture_measurements"]
    # These literal shapes do not certify the future single-copy/stderr owner.
    publication = {
        "schema": "code-structure-viz.next-publication-decision/v2",
        "version": 2,
        "semantic_decision": run.record(),
        "candidates": candidates.record(),
        "response": {
            "request_id": request.request_id,
            "raw_sha256": candidate.response_frame().sha256,
            "model_digest": candidate.semantic_payload()["model_digest"],
            "byte_length": len(candidate.response_frame().raw_bytes),
        },
        "artifacts": [
            {"descriptor": descriptor, "bytes_base64": base64.b64encode(raw).decode("ascii")}
        ],
        "stdout": {
            "selector": "next:semantic-json",
            "availability": True,
            "copy_status": "published",
            "candidate": descriptor,
            "result_bytes_base64": base64.b64encode(raw).decode("ascii"),
            "result_size_bytes": len(raw),
            "result_sha256": hashlib.sha256(raw).hexdigest(),
        },
        "stderr": {
            "available": True,
            "bytes_base64": "",
            "size_bytes": 0,
            "sha256": empty_sha,
            "diagnostics_sha256": hashlib.sha256(b"[]").hexdigest(),
        },
        "measurements": {
            **{
                f"adapter_{stream}": {
                    "allowed": True,
                    "measured_bytes": capture[f"adapter_{stream}"]["captured_bytes"],
                    "retained_bytes": capture[f"adapter_{stream}"]["capture_retained_bytes"],
                }
                for stream in ("stdout", "stderr")
            },
            "public_stderr": {"allowed": True, "measured_bytes": 0, "retained_bytes": 0},
            "selected_stdout": {
                "allowed": True,
                "measured_bytes": len(raw),
                "retained_bytes": len(raw),
            },
        },
        "publication_outcome": "published",
        "exit_code": 0,
        "seal": {"algorithm": "sha256", "sha256": "0" * 64, "preimage_sha256": "1" * 64},
    }
    semantic = project_public_semantic_document_v3(core)
    config = request.analysis_context().domain_config()
    context = request.analysis_context().run_context()
    domain = {
        "schema": "code-structure-viz.next-domain-manifest/v2",
        "domain": "next",
        "request_independent": False,
        "status": "complete",
        "payload_available": True,
        "entity_count": 4,
        "budget": {
            "name": "max_entities",
            "requested": None,
            "resolved": 500,
            "actual": 4,
            "source": "builtin",
            "outcome": "complete",
        },
        "run_context": context,
        "semantic_compatibility_id": semantic["semantic_compatibility_id"],
        "compatibility_descriptor": semantic["compatibility_descriptor"],
        "identity_versions": semantic["identity_versions"],
        "source_plan_digest": seal.plan_digest,
        "domain_config_digest": config["domain_config_digest"],
        "run_fingerprint": run.record()["context"]["run_fingerprint"],
        "source": semantic["source"],
        "request": {
            key: value for key, value in semantic["request"].items() if key != "run_fingerprint"
        },
        "config": config,
        "projects": semantic["projects"],
        "targets": config["targets"],
        "formats": config["formats"],
        "toolchain": {
            "node": {"status": "available", "version": "22.10.0", "failure_kind": None},
            "node_version": "22.10.0",
            "typescript_version": "5.9.2",
            "adapter_version": "0.2.0",
            "protocol": "code-structure-viz.next-adapter/v2",
        },
        "trusted_environment": trusted_environment_manifest_v2(assets)["environment_descriptor"],
        "limits": request.record()["limits"],
        "coverage": semantic["coverage"],
        "artifact_paths": [descriptor["path"]],
        "diagnostics": [],
        "decision": run.record(),
        "publication": publication,
    }
    root = {
        "type": "run_manifest",
        "schema": "code-structure-viz.run-manifest/v2",
        "tool": {"name": "code-structure-viz", "version": "0.1.0.dev0"},
        "contracts": {
            "config": "code-structure-viz.config/v1",
            "diagnostic": "code-structure-viz.diagnostic/v1",
            "source_view": "code-structure-viz.source-view/v1",
            "semantic": "code-structure-viz.semantic/v3",
            "manifest": "code-structure-viz.run-manifest/v2",
            "run_summary": "code-structure-viz.run-summary/v1",
            "stdout_result": "code-structure-viz.stdout-result/v2",
            "plantuml": "code-structure-viz.plantuml/next/v1",
        },
        "adapters": [{"domain": "next", "name": "next-typescript", "version": "1"}],
        "command": {
            "name": "snapshot",
            "domain": "next",
            "formats": config["formats"],
            "stdout_selector": context["stdout_selector"],
        },
        "request_independent": False,
        "request": {
            "projects": ["."],
            "targets": [],
            "formats": config["formats"],
            "upstream_depth": 0,
            "downstream_depth": 0,
        },
        "next_request": domain["request"],
        "next_config": config,
        "next_decision": run.record(),
        "next_publication": publication,
        "source": semantic["source"],
        "config": {
            "schema": "code-structure-viz.config/v1",
            "source": "builtin",
            "sha256": config["domain_config_digest"],
            "resolved": {
                "next": {
                    "projects": ["."],
                    "targets": [],
                    "formats": config["formats"],
                    "trusted_environment_digest": config["trusted_environment_digest"],
                },
                "traversal": {"upstream_depth": 0, "downstream_depth": 0},
                "limits": config["limits"],
            },
            "value_sources": {
                name: "builtin"
                for name in (
                    "next_projects",
                    "next_targets",
                    "formats",
                    "upstream_depth",
                    "downstream_depth",
                    "limits",
                    "trusted_environment",
                )
            },
        },
        "run": {
            "status": "complete",
            "exit_code": 0,
            "fingerprint": domain["run_fingerprint"],
            "run_context": context,
        },
        "domains": [domain],
        "artifacts": [descriptor],
        "diagnostics": [],
    }
    stdout = {
        "type": "stdout_result",
        "schema": "code-structure-viz.stdout-result/v2",
        "selector": "next:semantic-json",
        "availability": True,
        "domain_status": "complete",
        "stable_reason": "published_artifact",
        "artifact": descriptor,
        "publication": publication,
    }
    return {
        "next-domain-manifest-v2": domain,
        "next-publication-decision-v2": publication,
        "run-manifest-v2": root,
        "stdout-result-v2": stdout,
    }


def test_publication_v2_accepts_unobserved_capture_null_pair(
    tmp_path: Path, outer_vectors: dict[str, dict[str, Any]]
) -> None:
    """Shape-only vector from actual stage failure, not a final-owner certificate."""
    candidates = stage_failed_candidates_v3(tmp_path)
    assert candidates.record()["capture_measurements"] == {
        "adapter_stdout": None,
        "adapter_stderr": None,
    }
    value = deepcopy(outer_vectors["next-publication-decision-v2"])
    value.update(
        semantic_decision=candidates.run_decision().record(),
        candidates=candidates.record(),
        response=None,
        artifacts=[],
        exit_code=3,
    )
    value["measurements"].update(adapter_stdout=None, adapter_stderr=None)
    value["stdout"].update(
        availability=False,
        copy_status="not_attempted",
        candidate=None,
        result_bytes_base64="",
        result_size_bytes=0,
        result_sha256=hashlib.sha256(b"").hexdigest(),
    )
    value["measurements"]["selected_stdout"] = {
        "allowed": True,
        "measured_bytes": 0,
        "retained_bytes": 0,
    }
    _validator("next-publication-decision-v2.schema.json").validate(value)


@pytest.mark.parametrize(
    "field", ["adapter_stdout", "adapter_stderr", "public_stderr", "selected_stdout"]
)
def test_publication_v2_rejects_one_sided_or_public_null_measurement(
    outer_vectors: dict[str, dict[str, Any]], field: str
) -> None:
    value = deepcopy(outer_vectors["next-publication-decision-v2"])
    value["measurements"][field] = None
    with pytest.raises(ValidationError):
        _validator("next-publication-decision-v2.schema.json").validate(value)


@pytest.mark.parametrize("name", FAMILY[-4:])
def test_outer_schema_vectors_accept_new_exact_refs_and_reject_private_extras(
    outer_vectors: dict[str, dict[str, Any]],
    name: str,
) -> None:
    value = outer_vectors[name]
    validator = _validator(f"{name}.schema.json")
    validator.validate(value)
    for extra in ("proof", "content_base64", "raw_stderr", "cwd", "pid"):
        with pytest.raises(ValidationError):
            validator.validate({**value, extra: "private"})
    required = _schema(f"{name}.schema.json")["required"]
    assert isinstance(required, list)
    for field in value:
        if field in required:
            without = deepcopy(value)
            del without[field]
            with pytest.raises(ValidationError):
                validator.validate(without)


@pytest.mark.parametrize(
    "path",
    [
        ("compatibility_descriptor", "schema"),
        ("decision", "schema"),
        ("publication", "schema"),
        ("publication", "candidates", "schema"),
    ],
)
def test_domain_v2_rejects_nested_downgrade(
    outer_vectors: dict[str, dict[str, Any]],
    path: tuple[str, ...],
) -> None:
    value = deepcopy(outer_vectors["next-domain-manifest-v2"])
    row = value
    for key in path[:-1]:
        row = row[key]
    row[path[-1]] = row[path[-1]].replace("/v3", "/v2").replace("decision/v2", "decision/v1")
    with pytest.raises(ValidationError):
        _validator("next-domain-manifest-v2.schema.json").validate(value)


def test_root_v2_requires_current_next_semantic_contract(
    outer_vectors: dict[str, dict[str, Any]],
) -> None:
    value = deepcopy(outer_vectors["run-manifest-v2"])
    value["contracts"]["semantic"] = "code-structure-viz.semantic/v1"
    with pytest.raises(ValidationError):
        _validator("run-manifest-v2.schema.json").validate(value)


def test_legacy_python_sqlalchemy_dispatcher_and_root_branch_meanings_are_unchanged() -> None:
    for domain in ("python", "sqlalchemy"):
        for path in sorted(
            (ROOT / "tests/golden" / f"{domain}_snapshot").glob("*/*.semantic.json")
        ):
            validate_semantic_dispatcher_v3(json.loads(path.read_bytes()))
        for path in sorted(
            (ROOT / "tests/golden" / f"{domain}_snapshot").glob("*/run-manifest.json")
        ):
            original = json.loads(path.read_bytes())
            _validator("run-manifest-v1.schema.json").validate(original)
            sibling = deepcopy(original)
            sibling["schema"] = "code-structure-viz.run-manifest/v2"
            sibling["contracts"]["manifest"] = "code-structure-viz.run-manifest/v2"
            sibling["contracts"]["stdout_result"] = "code-structure-viz.stdout-result/v2"
            _validator("run-manifest-v2.schema.json").validate(sibling)


@pytest.mark.parametrize(
    "reason", ["missing", "duplicate", "out_of_scope", "unsupported_export", "selected_taint"]
)
def test_stdout_v2_schema_keeps_target_rows_only_on_the_target_unavailable_branch(
    reason: str,
) -> None:
    value = {
        "type": "stdout_result",
        "schema": "code-structure-viz.stdout-result/v2",
        "selector": "next:semantic-json",
        "availability": False,
        "domain_status": "incomplete",
        "stable_reason": "target_payload_unavailable",
        "artifact": None,
        "target_failures": [{"target_key": "path:src/button.tsx", "reason": reason}],
    }
    validator = _validator("stdout-result-v2.schema.json")
    validator.validate(value)
    value["incomplete_kind"] = "payload_unavailable"
    with pytest.raises(ValidationError):
        validator.validate(value)
    del value["incomplete_kind"]
    value["stable_reason"] = "domain_payload_unavailable"
    with pytest.raises(ValidationError):
        validator.validate(value)
    del value["target_failures"]
    validator.validate(value)
    value["stable_reason"] = "target_payload_unavailable"
    with pytest.raises(ValidationError):
        validator.validate(value)


@pytest.mark.parametrize("mutation", ["payload", "incomplete_kind", "bool_count"])
def test_domain_v2_schema_preserves_closed_status_payload_count_correlation(
    outer_vectors: dict[str, dict[str, Any]],
    mutation: str,
) -> None:
    value = deepcopy(outer_vectors["next-domain-manifest-v2"])
    if mutation == "payload":
        value["payload_available"] = False
    elif mutation == "incomplete_kind":
        value["incomplete_kind"] = "payload_unavailable"
    else:
        value["entity_count"] = True
    with pytest.raises(ValidationError):
        _validator("next-domain-manifest-v2.schema.json").validate(value)
