"""Retained candidate bytes, not filesystem publication or stdout admission."""

import hashlib
import json
from copy import copy
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from jsonschema import ValidationError  # type: ignore[import-untyped]

from tests.contracts import next_runtime_v2_reference
from tests.contracts.next_public_artifact_v2_reference import (
    RetainedPublicSemanticArtifactV2,
    retain_public_semantic_artifact_v2,
)
from tests.contracts.next_public_artifact_v2_validation import validate_public_semantic_artifact_v2
from tests.contracts.next_reference_validation import canonical_json_bytes
from tests.contracts.test_next_public_semantic_v2 import KNOWN_PUBLIC_DIR, nominal_decision
from tests.contracts.test_next_semantic_candidate_v2 import candidate_for, core_inputs


def test_public_semantic_artifact_v2_retains_known_lf_bytes_and_descriptor(tmp_path: Path) -> None:
    from tests.contracts.next_public_artifact_v2_reference import retain_public_semantic_artifact_v2
    from tests.contracts.next_public_artifact_v2_validation import (
        validate_public_semantic_artifact_v2,
    )

    decision = nominal_decision(tmp_path)
    artifact = retain_public_semantic_artifact_v2(decision)
    known = json.loads((KNOWN_PUBLIC_DIR / "public-semantic.json").read_text(encoding="utf-8"))
    expected = (
        json.dumps(known, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        + b"\n"
    )
    assert len(expected) == 9472
    assert hashlib.sha256(expected).hexdigest() == (
        "545389abfa3975b2c95083db9cca6b8efbe071c4526b90cbe55fe9bdc84b5957"
    )
    assert artifact.wire_bytes() == expected
    assert artifact.descriptor() == {
        "path": "next.snapshot.semantic.json",
        "domain": "next",
        "format": "semantic-json",
        "media_type": "application/json",
        "size_bytes": 9472,
        "sha256": "545389abfa3975b2c95083db9cca6b8efbe071c4526b90cbe55fe9bdc84b5957",
    }
    assert artifact.semantic_decision() is decision
    validate_public_semantic_artifact_v2(artifact, decision)


def rehashed_body(
    artifact: RetainedPublicSemanticArtifactV2, body: bytes
) -> RetainedPublicSemanticArtifactV2:
    """Fault injection only: try forging a self-consistent retained candidate."""

    forged = copy(artifact)
    descriptor = artifact.descriptor()
    descriptor.update(size_bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
    object.__setattr__(forged, "_wire_bytes", body)
    object.__setattr__(forged, "_descriptor_bytes", canonical_json_bytes(descriptor))
    return forged


def test_public_semantic_artifact_v2_has_closed_immutable_ownership(tmp_path: Path) -> None:
    decision = nominal_decision(tmp_path)
    artifact = retain_public_semantic_artifact_v2(decision)
    with pytest.raises(TypeError, match="created by retain_public_semantic_artifact_v2"):
        RetainedPublicSemanticArtifactV2(decision, artifact.wire_bytes(), artifact.descriptor())
    with pytest.raises(FrozenInstanceError):
        artifact._wire_bytes = b"{}\n"  # type: ignore[misc]
    assert repr(artifact) == "RetainedPublicSemanticArtifactV2()"
    descriptor = artifact.descriptor()
    descriptor.update(size_bytes=0, sha256="0" * 64, path="private")
    assert artifact.descriptor()["size_bytes"] == 9472
    assert artifact.wire_bytes().endswith(b"}\n")
    validate_public_semantic_artifact_v2(artifact, decision)


def test_public_semantic_artifact_v2_rejects_an_identical_foreign_core_owner(
    tmp_path: Path,
) -> None:
    (tmp_path / "first").mkdir()
    (tmp_path / "second").mkdir()
    first = nominal_decision(tmp_path / "first")
    second = nominal_decision(tmp_path / "second")
    artifact = retain_public_semantic_artifact_v2(first)
    assert artifact.wire_bytes() == retain_public_semantic_artifact_v2(second).wire_bytes()
    with pytest.raises(ValueError, match="retained Core owner"):
        validate_public_semantic_artifact_v2(artifact, second)


def test_public_semantic_artifact_v2_refuses_a_duck_owner(tmp_path: Path) -> None:
    decision = nominal_decision(tmp_path)
    artifact = retain_public_semantic_artifact_v2(decision)
    duck = SimpleNamespace(
        semantic_decision=artifact.semantic_decision,
        wire_bytes=artifact.wire_bytes,
        descriptor=artifact.descriptor,
    )
    with pytest.raises(TypeError, match="nominal owner"):
        validate_public_semantic_artifact_v2(cast(RetainedPublicSemanticArtifactV2, duck), decision)


@pytest.mark.parametrize(
    "encoding",
    ["no-lf", "two-lf", "crlf", "bom", "spaces", "duplicate-key", "two-json", "invalid-utf8"],
)
def test_public_semantic_artifact_v2_refuses_rehashed_noncanonical_bytes(
    tmp_path: Path, encoding: str
) -> None:
    decision = nominal_decision(tmp_path)
    artifact = retain_public_semantic_artifact_v2(decision)
    body = artifact.wire_bytes()
    mutated = {
        "no-lf": body[:-1],
        "two-lf": body + b"\n",
        "crlf": body[:-1] + b"\r\n",
        "bom": b"\xef\xbb\xbf" + body,
        "spaces": b" " + body,
        "duplicate-key": b'{"domain":"next",' + body[1:],
        "two-json": body + b"{}\n",
        "invalid-utf8": b"\xff" + body,
    }[encoding]
    forged = rehashed_body(artifact, mutated)
    assert forged.descriptor()["sha256"] == hashlib.sha256(mutated).hexdigest()
    with pytest.raises(ValueError):
        validate_public_semantic_artifact_v2(forged, decision)


@pytest.mark.parametrize("field", ["source", "request", "coverage"])
def test_public_semantic_artifact_v2_refuses_rehashed_foreign_canonical_record(
    tmp_path: Path, field: str
) -> None:
    decision = nominal_decision(tmp_path)
    artifact = retain_public_semantic_artifact_v2(decision)
    document = json.loads(artifact.wire_bytes())
    if field == "source":
        document["source"]["fingerprint"] = "0" * 64
    elif field == "request":
        document["request"]["run_fingerprint"] = "0" * 64
    else:
        document["coverage"]["counts"]["published"] += 1
    forged = rehashed_body(artifact, canonical_json_bytes(document) + b"\n")
    with pytest.raises(ValueError):
        validate_public_semantic_artifact_v2(forged, decision)


@pytest.mark.parametrize(
    ("field", "mutated"),
    [
        ("path", "next.snapshot.puml"),
        ("domain", "python"),
        ("format", "plantuml"),
        ("media_type", "text/vnd.plantuml; charset=utf-8"),
        ("size_bytes", 9471),
        ("size_bytes", True),
        ("sha256", "0" * 64),
        ("private_path", "/private/foreign"),
    ],
)
def test_public_semantic_artifact_v2_refuses_foreign_descriptor_fields(
    tmp_path: Path, field: str, mutated: Any
) -> None:
    decision = nominal_decision(tmp_path)
    artifact = retain_public_semantic_artifact_v2(decision)
    descriptor = artifact.descriptor()
    descriptor[field] = mutated
    forged = copy(artifact)
    object.__setattr__(forged, "_descriptor_bytes", canonical_json_bytes(descriptor))
    with pytest.raises((ValueError, ValidationError)):
        validate_public_semantic_artifact_v2(forged, decision)


def test_public_semantic_artifact_v2_keeps_retained_bytes_after_source_changes(
    tmp_path: Path,
) -> None:
    decision = nominal_decision(tmp_path)
    artifact = retain_public_semantic_artifact_v2(decision)
    before = artifact.wire_bytes()
    # Independent filesystem boundary mutation: projection must never reread the target.
    (tmp_path / "repo/src/Card.tsx").write_bytes(b"throw new Error('changed');\n")
    validate_public_semantic_artifact_v2(artifact, decision)
    assert artifact.wire_bytes() == before
    assert retain_public_semantic_artifact_v2(decision).wire_bytes() == before


def test_public_semantic_artifact_v2_complete_empty_is_not_synthetic_success(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy, wire = core_inputs(tmp_path, empty_membership=True)
    decision = next_runtime_v2_reference.decide_semantic_candidate_v2(
        candidate_for(seal, assets, request, policy, wire), seal, assets
    )
    artifact = retain_public_semantic_artifact_v2(decision)
    document = json.loads(artifact.wire_bytes())
    assert document["status"] == "complete"
    assert document["entities"] == []
    assert document["projects"] and document["files"]
    validate_public_semantic_artifact_v2(artifact, decision)


def test_public_semantic_artifact_v2_does_not_turn_export_failure_into_empty_bytes(
    tmp_path: Path,
) -> None:
    seal, assets, request, policy, wire = core_inputs(tmp_path, corpus="string-unknown")
    decision = next_runtime_v2_reference.decide_semantic_candidate_v2(
        candidate_for(seal, assets, request, policy, wire), seal, assets
    )
    assert decision.gate()["payload_available"] is False
    with pytest.raises(ValueError, match="available Core decision"):
        retain_public_semantic_artifact_v2(decision)
