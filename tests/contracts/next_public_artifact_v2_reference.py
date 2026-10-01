"""Retained public candidate bytes only; no final publication or filesystem claim."""

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, cast

from tests.contracts.next_public_artifact_v2_validation import (
    validate_public_plantuml_artifact_v2,
    validate_public_semantic_artifact_v2,
)
from tests.contracts.next_public_semantic_v2_reference import project_public_semantic_document_v2
from tests.contracts.next_reference_validation import canonical_json_bytes, render_plantuml
from tests.contracts.next_runtime_v2_reference import ValidatedSemanticDecisionV2
from tests.contracts.next_runtime_v2_validation import validate_semantic_decision_v2


@dataclass(frozen=True, slots=True, init=False)
class RetainedPublicSemanticArtifactV2:
    """Same Core owner with immutable canonical JSON candidate and actual descriptor."""

    _decision: ValidatedSemanticDecisionV2 = field(repr=False)
    _wire_bytes: bytes = field(repr=False)
    _descriptor_bytes: bytes = field(repr=False)

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("public artifacts are created by retain_public_semantic_artifact_v2")

    def semantic_decision(self) -> ValidatedSemanticDecisionV2:
        return self._decision

    def wire_bytes(self) -> bytes:
        return self._wire_bytes

    def descriptor(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(self._descriptor_bytes))


def retain_public_semantic_artifact_v2(
    decision: ValidatedSemanticDecisionV2,
) -> RetainedPublicSemanticArtifactV2:
    """Render once from an available decision; never accept caller bytes or descriptors."""

    document = project_public_semantic_document_v2(decision)
    wire = canonical_json_bytes(document) + b"\n"
    descriptor = {
        "path": "next.snapshot.semantic.json",
        "domain": "next",
        "format": "semantic-json",
        "media_type": "application/json",
        "size_bytes": len(wire),
        "sha256": hashlib.sha256(wire).hexdigest(),
    }
    instance = object.__new__(RetainedPublicSemanticArtifactV2)
    object.__setattr__(instance, "_decision", decision)
    object.__setattr__(instance, "_wire_bytes", wire)
    object.__setattr__(instance, "_descriptor_bytes", canonical_json_bytes(descriptor))
    validate_public_semantic_artifact_v2(instance, decision)
    return instance


@dataclass(frozen=True, slots=True, init=False)
class RetainedPublicPlantumlArtifactV2:
    """Exact PlantUML bytes bound to the same available Core owner."""

    _decision: ValidatedSemanticDecisionV2 = field(repr=False)
    _wire_bytes: bytes = field(repr=False)
    _descriptor_bytes: bytes = field(repr=False)

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("PlantUML artifacts are created by retain_public_plantuml_artifact_v2")

    def semantic_decision(self) -> ValidatedSemanticDecisionV2:
        return self._decision

    def wire_bytes(self) -> bytes:
        return self._wire_bytes

    def descriptor(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(self._descriptor_bytes))


def retain_public_plantuml_artifact_v2(
    decision: ValidatedSemanticDecisionV2,
) -> RetainedPublicPlantumlArtifactV2:
    validate_semantic_decision_v2(decision)
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
    instance = object.__new__(RetainedPublicPlantumlArtifactV2)
    object.__setattr__(instance, "_decision", decision)
    object.__setattr__(instance, "_wire_bytes", wire)
    object.__setattr__(instance, "_descriptor_bytes", canonical_json_bytes(descriptor))
    validate_public_plantuml_artifact_v2(instance, decision)
    return instance
