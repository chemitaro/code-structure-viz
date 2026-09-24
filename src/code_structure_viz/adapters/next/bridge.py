from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Literal

from .applicability import PackageApplicabilityMatrix
from .process_observation import (
    NextProcessLaunchObservation,
    production_unavailable_process_observation,
)
from .protocol import NextAdapterRequest, build_next_adapter_request
from .source_acquisition import (
    NextNotApplicableAcquisition,
    NextSourceSealReader,
    SourceAcquisitionSeal,
    SourceDiscoveryIntent,
    seal_source_acquisition,
)


@dataclass(frozen=True, slots=True)
class NextNotApplicableBridgeResult:
    """Package-only result for a selected scope with no direct Next project."""

    package_applicability: PackageApplicabilityMatrix


@dataclass(frozen=True, slots=True)
class NextProductionUnavailableBridgeResult:
    """Sealed request rejected before execution because no runner is accepted."""

    source_seal: SourceAcquisitionSeal
    request: NextAdapterRequest
    process_observation: NextProcessLaunchObservation
    failure_stage: Literal["node_discovery"] = field(default="node_discovery", init=False)
    diagnostic_code: Literal["CSV-NEXT-NODE-001"] = field(default="CSV-NEXT-NODE-001", init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.source_seal, SourceAcquisitionSeal):
            raise TypeError("Next bridge result requires a production source seal")
        if not isinstance(self.request, NextAdapterRequest):
            raise TypeError("Next bridge result requires a production request")
        if not isinstance(self.process_observation, NextProcessLaunchObservation):
            raise TypeError("Next bridge result requires a production process observation")
        if self.request.source_seal_id != self.source_seal.seal_id:
            raise ValueError("Next bridge request must preserve its source seal identity")


NextBridgeResult = NextNotApplicableBridgeResult | NextProductionUnavailableBridgeResult


class NextAdapterBridge:
    """Prepare one sealed Next request and stop before any unsupported OS launch."""

    def prepare(
        self,
        *,
        intent: SourceDiscoveryIntent,
        reader: NextSourceSealReader,
        trusted_environment_digest: str,
        adapter_version: str,
        trusted_type_environment: Mapping[str, object],
        targets: Sequence[str],
        run_context: Mapping[str, object],
        max_entities: int = 500,
    ) -> NextBridgeResult:
        acquisition = seal_source_acquisition(
            intent,
            reader,
            trusted_environment_digest=trusted_environment_digest,
            max_entities=max_entities,
        )
        if isinstance(acquisition, NextNotApplicableAcquisition):
            return NextNotApplicableBridgeResult(acquisition.package_applicability)

        request = build_next_adapter_request(
            acquisition,
            adapter_version=adapter_version,
            trusted_type_environment=trusted_type_environment,
            targets=targets,
            run_context=run_context,
        )
        observation = production_unavailable_process_observation()
        return NextProductionUnavailableBridgeResult(
            source_seal=acquisition,
            request=request,
            process_observation=observation,
        )
