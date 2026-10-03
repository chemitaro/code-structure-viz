"""Retained public candidate bytes only; no final publication or filesystem claim."""

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, cast

from tests.contracts.next_public_artifact_v3_validation import (
    validate_public_plantuml_artifact_v3,
    validate_public_semantic_artifact_v3,
)
from tests.contracts.next_public_semantic_v3_reference import project_public_semantic_document_v3
from tests.contracts.next_reference_validation import canonical_json_bytes, render_plantuml
from tests.contracts.next_semantic_core_v3_reference import ValidatedSemanticDecisionV3
from tests.contracts.next_semantic_core_v3_validation import validate_semantic_decision_v3


@dataclass(frozen=True, slots=True, init=False)
class RetainedPublicSemanticArtifactV3:
    """Same Core owner with immutable canonical JSON candidate and actual descriptor."""

    _decision: ValidatedSemanticDecisionV3 = field(repr=False)
    _wire_bytes: bytes = field(repr=False)
    _descriptor_bytes: bytes = field(repr=False)

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("public artifacts are created by retain_public_semantic_artifact_v3")

    def semantic_decision(self) -> ValidatedSemanticDecisionV3:
        return self._decision

    def wire_bytes(self) -> bytes:
        return self._wire_bytes

    def descriptor(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(self._descriptor_bytes))


def retain_public_semantic_artifact_v3(
    decision: ValidatedSemanticDecisionV3,
) -> RetainedPublicSemanticArtifactV3:
    """Render once from an available decision; never accept caller bytes or descriptors."""

    document = project_public_semantic_document_v3(decision)
    wire = canonical_json_bytes(document) + b"\n"
    descriptor = {
        "path": "next.snapshot.semantic.json",
        "domain": "next",
        "format": "semantic-json",
        "media_type": "application/json",
        "size_bytes": len(wire),
        "sha256": hashlib.sha256(wire).hexdigest(),
    }
    instance = object.__new__(RetainedPublicSemanticArtifactV3)
    object.__setattr__(instance, "_decision", decision)
    object.__setattr__(instance, "_wire_bytes", wire)
    object.__setattr__(instance, "_descriptor_bytes", canonical_json_bytes(descriptor))
    validate_public_semantic_artifact_v3(instance, decision)
    return instance


@dataclass(frozen=True, slots=True, init=False)
class RetainedPublicPlantumlArtifactV3:
    """Exact PlantUML bytes bound to the same available Core owner."""

    _decision: ValidatedSemanticDecisionV3 = field(repr=False)
    _wire_bytes: bytes = field(repr=False)
    _descriptor_bytes: bytes = field(repr=False)

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("PlantUML artifacts are created by retain_public_plantuml_artifact_v3")

    def semantic_decision(self) -> ValidatedSemanticDecisionV3:
        return self._decision

    def wire_bytes(self) -> bytes:
        return self._wire_bytes

    def descriptor(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(self._descriptor_bytes))


def retain_public_plantuml_artifact_v3(
    decision: ValidatedSemanticDecisionV3,
) -> RetainedPublicPlantumlArtifactV3:
    validate_semantic_decision_v3(decision)
    gate = decision.gate()
    if not gate["payload_available"]:
        raise ValueError("unavailable Core cannot create a PlantUML candidate")
    wire = render_plantuml(
        decision.transport_candidate().semantic_payload()["model"], gate["outcome"]
    )
    descriptor = {
        "path": "next.snapshot.puml",
        "domain": "next",
        "format": "plantuml",
        "media_type": "text/vnd.plantuml; charset=utf-8",
        "size_bytes": len(wire),
        "sha256": hashlib.sha256(wire).hexdigest(),
    }
    instance = object.__new__(RetainedPublicPlantumlArtifactV3)
    object.__setattr__(instance, "_decision", decision)
    object.__setattr__(instance, "_wire_bytes", wire)
    object.__setattr__(instance, "_descriptor_bytes", canonical_json_bytes(descriptor))
    validate_public_plantuml_artifact_v3(instance, decision)
    return instance
