"""Candidate validation independently joins retained owners, bytes and counts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from tests.contracts.next_public_artifact_v3_reference import (
    RetainedPublicPlantumlArtifactV3,
    RetainedPublicSemanticArtifactV3,
)
from tests.contracts.next_public_artifact_v3_validation import (
    validate_public_plantuml_artifact_v3,
    validate_public_semantic_artifact_v3,
)
from tests.contracts.next_reference_validation import canonical_json_bytes
from tests.contracts.next_run_decision_v3_reference import RetainedRequestBoundRunDecisionV3
from tests.contracts.next_run_decision_v3_validation import validate_request_bound_run_decision_v3
from tests.contracts.next_runtime_v2_validation import _validate_schema
from tests.contracts.next_semantic_core_v3_reference import ValidatedSemanticDecisionV3

if TYPE_CHECKING:
    from tests.contracts.next_publication_candidates_v3_reference import (
        RetainedRequestBoundPublicationCandidatesV3,
    )


def validate_request_bound_publication_candidates_v3(
    value: Mapping[str, Any],
    owner: RetainedRequestBoundPublicationCandidatesV3,
    *,
    run_decision: RetainedRequestBoundRunDecisionV3,
) -> None:
    from tests.contracts.next_publication_candidates_v3_reference import (
        RetainedRequestBoundPublicationCandidatesV3,
    )

    if (
        type(owner) is not RetainedRequestBoundPublicationCandidatesV3
        or type(run_decision) is not RetainedRequestBoundRunDecisionV3
    ):
        raise TypeError("candidate validation requires nominal owners")
    if owner.run_decision() is not run_decision:
        raise ValueError("candidate differs from its retained run owner")
    _validate_schema("next-publication-candidates-v3", value)
    if type(value["version"]) is not int:
        raise ValueError("candidate version must retain an integer")
    if canonical_json_bytes(dict(value)) != canonical_json_bytes(owner.record()):
        raise ValueError("candidate record differs from its retained metadata")
    validate_request_bound_run_decision_v3(value["run_decision"], run_decision)
    runtime = run_decision.runtime_result()
    core = run_decision.semantic_decision()
    formats = runtime.request_frame().analysis_context().run_context()["requested_formats"]
    artifacts = owner.artifacts()
    available = type(core) is ValidatedSemanticDecisionV3 and core.gate()["payload_available"]
    if not available and artifacts != ():
        raise ValueError("unavailable run cannot own candidate artifacts")
    if type(artifacts) is not tuple or len(artifacts) != (len(formats) if available else 0):
        raise ValueError("candidate artifacts differ from held requested formats")
    for format_name, artifact in zip(formats if available else [], artifacts, strict=True):
        assert type(core) is ValidatedSemanticDecisionV3
        if format_name == "semantic-json":
            if type(artifact) is not RetainedPublicSemanticArtifactV3:
                raise TypeError("candidate JSON artifact requires a nominal owner")
            validate_public_semantic_artifact_v3(artifact, core)
        else:
            if type(artifact) is not RetainedPublicPlantumlArtifactV3:
                raise TypeError("candidate PlantUML artifact requires a nominal owner")
            validate_public_plantuml_artifact_v3(artifact, core)
    if canonical_json_bytes(value["artifacts"]) != canonical_json_bytes(
        [item.descriptor() for item in artifacts]
    ):
        raise ValueError("candidate descriptors differ from retained artifacts")
    if any(type(item["size_bytes"]) is not int for item in value["artifacts"]):
        raise ValueError("candidate byte length must retain an integer")
    capture = runtime.observation()["capture"]
    limits = runtime.request_frame().record()["limits"]
    for stream in ("stdout", "stderr"):
        measurement = value["capture_measurements"][f"adapter_{stream}"]
        if measurement is not None and (
            any(
                type(measurement[key]) is not int
                for key in ("captured_bytes", "capture_retained_bytes", "limit_bytes")
            )
            or type(measurement["eof"]) is not bool
        ):
            raise ValueError("candidate capture requires actual integer counts and boolean EOF")
        expected = (
            {
                "captured_bytes": capture[f"{stream}_bytes"],
                "capture_retained_bytes": capture[f"{stream}_retained_bytes"],
                "eof": capture[f"{stream}_eof"],
                "limit_bytes": limits[f"max_adapter_{stream}_capture_bytes"],
            }
            if capture is not None
            else None
        )
        if canonical_json_bytes(measurement) != canonical_json_bytes(expected):
            raise ValueError("candidate capture accounting differs from retained observation")
