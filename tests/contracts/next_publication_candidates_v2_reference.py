"""Request-bound candidate bytes/accounting only; no final publication claim."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Literal, cast

from tests.contracts.next_public_artifact_v2_reference import (
    RetainedPublicPlantumlArtifactV2,
    RetainedPublicSemanticArtifactV2,
    retain_public_plantuml_artifact_v2,
    retain_public_semantic_artifact_v2,
)
from tests.contracts.next_publication_candidates_v2_validation import (
    validate_request_bound_publication_candidates_v2,
)
from tests.contracts.next_reference_validation import canonical_json_bytes
from tests.contracts.next_run_decision_v2_reference import RetainedRequestBoundRunDecisionV2
from tests.contracts.next_run_decision_v2_validation import validate_request_bound_run_decision_v2
from tests.contracts.next_runtime_v2_reference import ValidatedSemanticDecisionV2

PublicArtifactV2 = RetainedPublicSemanticArtifactV2 | RetainedPublicPlantumlArtifactV2


@dataclass(frozen=True, slots=True, init=False)
class RetainedRequestBoundPublicationCandidatesV2:
    """Same run/Core owners with private immutable bytes and fresh metadata."""

    _run: RetainedRequestBoundRunDecisionV2 = field(repr=False)
    _artifacts: tuple[PublicArtifactV2, ...] = field(repr=False)
    _record_bytes: bytes = field(repr=False)

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("publication candidates are created by the retained run factory")

    def run_decision(self) -> RetainedRequestBoundRunDecisionV2:
        return self._run

    def artifacts(self) -> tuple[PublicArtifactV2, ...]:
        return self._artifacts

    def record(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(self._record_bytes))

    def artifact_bytes(self, format_name: Literal["semantic-json", "plantuml"]) -> bytes | None:
        if type(format_name) is not str:
            raise TypeError("artifact format must be a closed string")
        if format_name not in {"semantic-json", "plantuml"}:
            raise ValueError("unknown artifact format")
        return next(
            (
                item.wire_bytes()
                for item in self._artifacts
                if item.descriptor()["format"] == format_name
            ),
            None,
        )


def retain_request_bound_publication_candidates_v2(
    run_decision: RetainedRequestBoundRunDecisionV2,
) -> RetainedRequestBoundPublicationCandidatesV2:
    """Derive candidates from the same validated run, never caller bytes or counts."""

    if type(run_decision) is not RetainedRequestBoundRunDecisionV2:
        raise TypeError("publication candidates require a nominal run owner")
    run_record = run_decision.record()
    validate_request_bound_run_decision_v2(run_record, run_decision)
    runtime = run_decision.runtime_result()
    formats = runtime.request_frame().analysis_context().run_context()["requested_formats"]
    core = run_decision.semantic_decision()
    artifacts: tuple[PublicArtifactV2, ...] = ()
    if type(core) is ValidatedSemanticDecisionV2 and core.gate()["payload_available"]:
        artifacts = tuple(
            retain_public_semantic_artifact_v2(core)
            if format_name == "semantic-json"
            else retain_public_plantuml_artifact_v2(core)
            for format_name in formats
        )
    capture = runtime.observation()["capture"]
    limits = runtime.request_frame().record()["limits"]
    record = {
        "schema": "code-structure-viz.next-publication-candidates/v2",
        "version": 2,
        "run_decision": run_record,
        "artifacts": [item.descriptor() for item in artifacts],
        "capture_measurements": {
            f"adapter_{stream}": {
                "captured_bytes": capture[f"{stream}_bytes"],
                "capture_retained_bytes": capture[f"{stream}_retained_bytes"],
                "eof": capture[f"{stream}_eof"],
                "limit_bytes": limits[f"max_adapter_{stream}_capture_bytes"],
            }
            if capture is not None
            else None
            for stream in ("stdout", "stderr")
        },
    }
    instance = object.__new__(RetainedRequestBoundPublicationCandidatesV2)
    object.__setattr__(instance, "_run", run_decision)
    object.__setattr__(instance, "_artifacts", artifacts)
    object.__setattr__(instance, "_record_bytes", canonical_json_bytes(record))
    validate_request_bound_publication_candidates_v2(record, instance, run_decision=run_decision)
    return instance


def project_request_bound_publication_candidates_v2(
    owner: RetainedRequestBoundPublicationCandidatesV2,
) -> dict[str, Any]:
    if type(owner) is not RetainedRequestBoundPublicationCandidatesV2:
        raise TypeError("projection requires a nominal candidate owner")
    record = owner.record()
    validate_request_bound_publication_candidates_v2(
        record, owner, run_decision=owner.run_decision()
    )
    return record
