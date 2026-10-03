"""Paired candidate bytes from the same actual v3 Core; no publication certificate."""

import hashlib
import json
from copy import copy
from importlib import import_module, util
from pathlib import Path

import pytest

from tests.contracts.next_public_artifact_v3_reference import (
    retain_public_plantuml_artifact_v3,
    retain_public_semantic_artifact_v3,
)
from tests.contracts.next_public_artifact_v3_validation import (
    validate_public_plantuml_artifact_v3,
    validate_public_semantic_artifact_v3,
)
from tests.contracts.next_public_semantic_v3_reference import project_public_semantic_document_v3
from tests.contracts.next_reference_validation import (
    canonical_json_bytes,
    validate_plantuml_contract,
)
from tests.contracts.test_next_public_semantic_v3 import nominal_decision_v3


def test_paired_public_bytes_retain_the_same_core_owner(tmp_path: Path) -> None:
    decision = nominal_decision_v3(tmp_path)
    document = project_public_semantic_document_v3(decision)
    assert document["source_inventory_summary"]["published_entities"]["total"] == 4
    module = "tests.contracts.next_public_artifact_v3_reference"
    assert util.find_spec(module) is not None, "same Core-v3 has no paired candidate byte owners"
    artifacts = import_module(module)
    semantic = artifacts.retain_public_semantic_artifact_v3(decision)
    plantuml = artifacts.retain_public_plantuml_artifact_v3(decision)
    assert semantic.semantic_decision() is plantuml.semantic_decision() is decision
    expected_json = (
        json.dumps(
            document, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        ).encode()
        + b"\n"
    )
    assert semantic.wire_bytes() == expected_json
    validate_plantuml_contract(
        plantuml.wire_bytes(),
        decision.transport_candidate().semantic_payload()["model"],
        "complete",
    )
    for artifact, path, fmt, media in (
        (semantic, "next.snapshot.semantic.json", "semantic-json", "application/json"),
        (plantuml, "next.snapshot.puml", "plantuml", "text/vnd.plantuml; charset=utf-8"),
    ):
        raw = artifact.wire_bytes()
        assert type(raw) is bytes and raw.endswith(b"\n") and not raw.endswith(b"\n\n")
        assert artifact.descriptor() == {
            "path": path,
            "domain": "next",
            "format": fmt,
            "media_type": media,
            "size_bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }


@pytest.mark.parametrize("format_name", ["semantic-json", "plantuml"])
def test_artifact_refuses_equal_content_from_another_actual_owner(
    tmp_path: Path,
    format_name: str,
) -> None:
    first_path, second_path = tmp_path / "first", tmp_path / "second"
    first_path.mkdir()
    second_path.mkdir()
    first, second = nominal_decision_v3(first_path), nominal_decision_v3(second_path)
    assert first.request_id == second.request_id
    factory, validate = (
        (retain_public_semantic_artifact_v3, validate_public_semantic_artifact_v3)
        if format_name == "semantic-json"
        else (retain_public_plantuml_artifact_v3, validate_public_plantuml_artifact_v3)
    )
    artifact = factory(first)
    assert artifact.wire_bytes() == factory(second).wire_bytes()
    with pytest.raises(ValueError, match="Core owner"):
        validate(artifact, second)  # type: ignore[arg-type]


def test_artifact_validator_rejects_rehashed_false_summary_not_just_cache_mismatch(
    tmp_path: Path,
) -> None:
    core = nominal_decision_v3(tmp_path)
    original = retain_public_semantic_artifact_v3(core)
    forged = copy(original)
    document = json.loads(original.wire_bytes())
    document["source_inventory_summary"]["safe"]["files"] -= 1
    raw = canonical_json_bytes(document) + b"\n"
    descriptor = original.descriptor()
    descriptor.update(size_bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    object.__setattr__(forged, "_wire_bytes", raw)
    object.__setattr__(forged, "_descriptor_bytes", canonical_json_bytes(descriptor))
    with pytest.raises(ValueError, match="inventory summary"):
        validate_public_semantic_artifact_v3(forged, core)
