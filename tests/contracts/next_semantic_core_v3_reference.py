"""Incremental same-owner v3 Core reference; not production/TS certification."""

import json
from dataclasses import dataclass, field
from typing import Any, cast

from code_structure_viz.adapters.next.source_acquisition import SourceAcquisitionSeal
from tests.contracts.next_reference_validation import (
    ModelRecordLimitError,
    canonical_json_bytes,
    digest,
)
from tests.contracts.next_runtime_v2_reference import (
    RetainedExecutionAssets,
    ValidatedTransportCandidateV2,
)
from tests.contracts.next_semantic_core_v3_validation import (
    SemanticCandidateInvalidErrorV3,
    validate_semantic_candidate_v3,
)
from tests.contracts.next_semantic_profile_v1_reference import semantic_compatibility_metadata_v2
from tests.contracts.next_source_inventory_v3_reference import ValidatedSourceInventorySeamV3


def compatibility_descriptor_v3(candidate: ValidatedTransportCandidateV2) -> dict[str, Any]:
    if type(candidate) is not ValidatedTransportCandidateV2:
        raise TypeError("compatibility requires a retained transport candidate")
    binding = candidate.runtime_binding()
    preimage = {
        **semantic_compatibility_metadata_v2(),
        "semantic_schema": "code-structure-viz.semantic/v3",
        "semantic_admission_profile_id": "next-source-inventory-safe-subset-v1",
        "typescript_identity": binding["typescript_identity"],
        "trusted_type_environment_digest": binding["trusted_type_environment_digest"],
        "portable_toolchain_fingerprint": binding["runtime_toolchain_fingerprint"],
    }
    return {
        "schema": "code-structure-viz.next-semantic-compatibility/v3",
        **preimage,
        "compatibility_id": digest(preimage),
    }


@dataclass(frozen=True, slots=True, init=False)
class ValidatedSemanticDecisionV3:
    """Closed owner; SI-04's full negative/locality/budget gate is not yet complete."""

    _candidate: ValidatedTransportCandidateV2 = field(repr=False)
    _seal: SourceAcquisitionSeal = field(repr=False)
    _assets: RetainedExecutionAssets = field(repr=False)
    _source_inventory: ValidatedSourceInventorySeamV3 = field(repr=False)
    _gate_bytes: bytes = field(repr=False)
    _locality_bytes: bytes = field(repr=False)
    _compatibility_bytes: bytes = field(repr=False)
    _measurement_bytes: bytes = field(repr=False)

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("semantic decisions are created by decide_semantic_candidate_v3")

    @property
    def request_id(self) -> str:
        return self._candidate.request_id

    def transport_candidate(self) -> ValidatedTransportCandidateV2:
        return self._candidate

    def source_seal(self) -> SourceAcquisitionSeal:
        return self._seal

    def execution_assets(self) -> RetainedExecutionAssets:
        return self._assets

    def source_inventory_seam(self) -> ValidatedSourceInventorySeamV3:
        return self._source_inventory

    def gate(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(self._gate_bytes))

    def locality(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(self._locality_bytes))

    def compatibility_descriptor(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(self._compatibility_bytes))

    def measurements(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(self._measurement_bytes))


def decide_semantic_candidate_v3(
    candidate: ValidatedTransportCandidateV2,
    seal: SourceAcquisitionSeal,
    assets: RetainedExecutionAssets,
) -> ValidatedSemanticDecisionV3:
    result = validate_semantic_candidate_v3(candidate, seal, assets)
    instance = object.__new__(ValidatedSemanticDecisionV3)
    object.__setattr__(instance, "_candidate", candidate)
    object.__setattr__(instance, "_seal", seal)
    object.__setattr__(instance, "_assets", assets)
    object.__setattr__(instance, "_source_inventory", result.source_inventory)
    object.__setattr__(instance, "_gate_bytes", canonical_json_bytes(result.gate))
    object.__setattr__(instance, "_locality_bytes", canonical_json_bytes(result.locality))
    object.__setattr__(
        instance,
        "_compatibility_bytes",
        canonical_json_bytes(compatibility_descriptor_v3(candidate)),
    )
    object.__setattr__(instance, "_measurement_bytes", canonical_json_bytes(result.measurements))
    return instance


@dataclass(frozen=True, slots=True, init=False)
class RejectedSemanticDecisionV3:
    """Expected Core rejection only; no available seam or compatibility cache."""

    _candidate: ValidatedTransportCandidateV2 = field(repr=False)
    _seal: SourceAcquisitionSeal = field(repr=False)
    _assets: RetainedExecutionAssets = field(repr=False)
    _failure_bytes: bytes = field(repr=False)

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("Core rejections are created by inspect_semantic_candidate_v3")

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


def inspect_semantic_candidate_v3(
    candidate: ValidatedTransportCandidateV2,
    seal: SourceAcquisitionSeal,
    assets: RetainedExecutionAssets,
) -> ValidatedSemanticDecisionV3 | RejectedSemanticDecisionV3:
    try:
        return decide_semantic_candidate_v3(candidate, seal, assets)
    except SemanticCandidateInvalidErrorV3 as error:
        failure: dict[str, Any] = {
            "stage": "response_validation",
            "diagnostic_code": "CSV-NEXT-PROTOCOL-001",
            "reason": error.reason,
            "model_records": None,
        }
    except ModelRecordLimitError as error:
        failure = {
            "stage": "model_validation",
            "diagnostic_code": "CSV-NEXT-LIMIT-005",
            "reason": "max_model_records",
            "model_records": error.measured,
        }
    instance = object.__new__(RejectedSemanticDecisionV3)
    object.__setattr__(instance, "_candidate", candidate)
    object.__setattr__(instance, "_seal", seal)
    object.__setattr__(instance, "_assets", assets)
    object.__setattr__(instance, "_failure_bytes", canonical_json_bytes(failure))
    return instance
