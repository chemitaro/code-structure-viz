"""Opaque Core rejection owners, separate from admitted semantic decisions."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, cast

from tests.contracts.next_reference_validation import ModelRecordLimitError, canonical_json_bytes
from tests.contracts.next_runtime_v2_validation import SemanticCandidateInvalidErrorV2

if TYPE_CHECKING:
    from code_structure_viz.adapters.next.source_acquisition import SourceAcquisitionSeal
    from tests.contracts.next_runtime_v2_reference import (
        RetainedExecutionAssets,
        ValidatedSemanticDecisionV2,
        ValidatedTransportCandidateV2,
    )


@dataclass(frozen=True, slots=True, init=False)
class RejectedSemanticDecisionV2:
    """Retained rejected candidate evidence, never a public semantic projection."""

    _candidate: ValidatedTransportCandidateV2 = field(repr=False)
    _seal: SourceAcquisitionSeal = field(repr=False)
    _assets: RetainedExecutionAssets = field(repr=False)
    _failure_bytes: bytes = field(repr=False)

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("Core rejections are created by inspect_semantic_candidate_v2")

    @classmethod
    def _from_rejected_core(
        cls,
        candidate: ValidatedTransportCandidateV2,
        seal: SourceAcquisitionSeal,
        assets: RetainedExecutionAssets,
        failure: dict[str, Any],
    ) -> RejectedSemanticDecisionV2:
        instance = object.__new__(cls)
        object.__setattr__(instance, "_candidate", candidate)
        object.__setattr__(instance, "_seal", seal)
        object.__setattr__(instance, "_assets", assets)
        object.__setattr__(instance, "_failure_bytes", canonical_json_bytes(failure))
        return instance

    @property
    def request_id(self) -> str:
        return self._candidate.request_id

    def transport_candidate(self) -> ValidatedTransportCandidateV2:
        return self._candidate

    def source_seal(self) -> SourceAcquisitionSeal:
        return self._seal

    def execution_assets(self) -> RetainedExecutionAssets:
        return self._assets

    def failure(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(self._failure_bytes))


def inspect_semantic_candidate_v2(
    candidate: ValidatedTransportCandidateV2,
    seal: SourceAcquisitionSeal,
    assets: RetainedExecutionAssets,
) -> ValidatedSemanticDecisionV2 | RejectedSemanticDecisionV2:
    """Only expected payload violations become a rejection; internal errors escape."""

    from tests.contracts.next_runtime_v2_reference import decide_semantic_candidate_v2

    try:
        return decide_semantic_candidate_v2(candidate, seal, assets)
    except ModelRecordLimitError as failure:
        return RejectedSemanticDecisionV2._from_rejected_core(
            candidate,
            seal,
            assets,
            {
                "stage": "model_validation",
                "diagnostic_code": "CSV-NEXT-LIMIT-005",
                "reason": "max_model_records",
                "model_records": failure.measured,
            },
        )
    except SemanticCandidateInvalidErrorV2 as failure:
        return RejectedSemanticDecisionV2._from_rejected_core(
            candidate,
            seal,
            assets,
            {
                "stage": "response_validation",
                "diagnostic_code": "CSV-NEXT-PROTOCOL-001",
                "reason": failure.reason,
                "model_records": None,
            },
        )
