"""Independent retained public bytes / same Core owner / descriptor validation."""

import hashlib
import json
from typing import TYPE_CHECKING

from tests.contracts.next_public_semantic_v2_validation import validate_public_semantic_document_v2
from tests.contracts.next_reference_validation import canonical_json_bytes
from tests.contracts.next_runtime_v2_reference import ValidatedSemanticDecisionV2
from tests.contracts.next_runtime_v2_validation import _validate_schema

if TYPE_CHECKING:
    from tests.contracts.next_public_artifact_v2_reference import RetainedPublicSemanticArtifactV2


def validate_public_semantic_artifact_v2(
    artifact: "RetainedPublicSemanticArtifactV2", decision: ValidatedSemanticDecisionV2
) -> None:
    """Check retained bytes directly, without invoking the renderer or expected builder."""

    from tests.contracts.next_public_artifact_v2_reference import RetainedPublicSemanticArtifactV2

    if type(artifact) is not RetainedPublicSemanticArtifactV2:
        raise TypeError("public artifact validation requires a retained nominal owner")
    if artifact.semantic_decision() is not decision:
        raise ValueError("public artifact differs from its retained Core owner")
    wire = artifact.wire_bytes()
    if type(wire) is not bytes:
        raise TypeError("public artifact bytes must be immutable bytes")
    document = json.loads(wire.decode("utf-8"))
    if not isinstance(document, dict):
        raise ValueError("public artifact must encode a semantic object")
    validate_public_semantic_document_v2(document, decision)
    if wire != canonical_json_bytes(document) + b"\n":
        raise ValueError("public artifact bytes are not canonical UTF-8 JSON with one LF")
    descriptor = artifact.descriptor()
    # Only this unchanged, versionless six-field shape is reused, never a v1 runtime owner.
    _validate_schema("next-publication-decision-v1", descriptor, "#/$defs/artifact_descriptor")
    if (
        descriptor["path"] != "next.snapshot.semantic.json"
        or descriptor["domain"] != "next"
        or descriptor["format"] != "semantic-json"
        or descriptor["media_type"] != "application/json"
        or descriptor["size_bytes"] != len(wire)
        or descriptor["sha256"] != hashlib.sha256(wire).hexdigest()
    ):
        raise ValueError("public artifact descriptor differs from its actual retained bytes")
