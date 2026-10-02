"""SI-03 source/proof reference seam; not Core/public v3 admission."""

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, cast

from code_structure_viz.adapters.next.source_acquisition import SourceAcquisitionSeal
from tests.contracts.next_reference_validation import canonical_json_bytes
from tests.contracts.next_runtime_v2_reference import (
    RetainedExecutionAssets,
    ValidatedTransportCandidateV2,
)
from tests.contracts.next_runtime_v2_validation import validate_response_request_v2


@dataclass(frozen=True, slots=True)
class FileDispositionV3:
    record_id: str
    disposition: str
    reason: str | None


@dataclass(frozen=True, slots=True)
class SourceInventoryCountsV3:
    acquired_projects: int
    acquired_files: int
    acquired_file_bytes: int
    proof_discovered: int
    published_records: int
    proof_only_records: int
    accounted_records: int
    published_modules: int
    published_components: int
    published_entities: int


@dataclass(frozen=True, slots=True, init=False)
class ValidatedSourceInventorySeamV3:
    """SI-03 source/proof seam only; not full proof, locality or Core/public admission."""

    _candidate: ValidatedTransportCandidateV2 = field(repr=False)
    _seal: SourceAcquisitionSeal = field(repr=False)
    _assets: RetainedExecutionAssets = field(repr=False)
    _projection_bytes: bytes = field(repr=False)
    _eligible_module_ids: tuple[str, ...]
    _dispositions: tuple[FileDispositionV3, ...]
    _counts: SourceInventoryCountsV3
    _partition_bytes: bytes = field(repr=False)

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("source inventory seams are created by retain_source_inventory_seam_v3")

    @classmethod
    def _from_bound_candidate(
        cls,
        candidate: ValidatedTransportCandidateV2,
        seal: SourceAcquisitionSeal,
        assets: RetainedExecutionAssets,
        projection: dict[str, Any],
        eligible_module_ids: tuple[str, ...],
        dispositions: tuple[FileDispositionV3, ...],
        counts: SourceInventoryCountsV3,
        partition_preimage: dict[str, Any],
    ) -> "ValidatedSourceInventorySeamV3":
        instance = object.__new__(cls)
        object.__setattr__(instance, "_candidate", candidate)
        object.__setattr__(instance, "_seal", seal)
        object.__setattr__(instance, "_assets", assets)
        object.__setattr__(instance, "_projection_bytes", canonical_json_bytes(projection))
        object.__setattr__(instance, "_eligible_module_ids", eligible_module_ids)
        object.__setattr__(instance, "_dispositions", dispositions)
        object.__setattr__(instance, "_counts", counts)
        object.__setattr__(instance, "_partition_bytes", canonical_json_bytes(partition_preimage))
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

    def source_records(self) -> dict[str, list[dict[str, Any]]]:
        """Private acquired view from retained request bytes, never child metadata."""

        request = self._candidate.request_frame().record()
        return {
            "projects": request["projects"],
            "files": [
                {key: value for key, value in row.items() if key != "content_base64"}
                for row in request["files"]
            ],
        }

    def file_dispositions(self) -> tuple[FileDispositionV3, ...]:
        return self._dispositions

    def eligible_module_ids(self) -> tuple[str, ...]:
        return self._eligible_module_ids

    def safe_files(self) -> list[dict[str, Any]]:
        return cast(list[dict[str, Any]], json.loads(self._projection_bytes)["files"])

    def safe_projects(self) -> list[dict[str, Any]]:
        return cast(list[dict[str, Any]], json.loads(self._projection_bytes)["projects"])

    def counts(self) -> SourceInventoryCountsV3:
        return self._counts

    @property
    def profile_id(self) -> str:
        return str(self.partition_preimage()["profile_id"])

    def partition_preimage(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(self._partition_bytes))

    @property
    def partition_fingerprint(self) -> str:
        return hashlib.sha256(self._partition_bytes).hexdigest()


def retain_source_inventory_seam_v3(
    candidate: ValidatedTransportCandidateV2,
    seal: SourceAcquisitionSeal,
    assets: RetainedExecutionAssets,
) -> ValidatedSourceInventorySeamV3:
    """Retain source/proof joins; full mandatory proof and locality remain SI-04."""

    from tests.contracts.next_source_inventory_v3_validation import (
        derive_source_projection_v3,
        measure_source_inventory_v3,
        source_partition_preimage_v3,
        validate_public_source_metadata_v3,
        validate_source_record_payloads_v3,
    )

    if type(candidate) is not ValidatedTransportCandidateV2:
        raise TypeError("source inventory requires a retained transport candidate")
    validate_response_request_v2(
        candidate.response_frame(), candidate.request_frame(), seal, assets
    )
    if assets.adapter_identity()["version"] != "0.2.0":
        raise ValueError("source inventory profile requires retained producer version 0.2.0")
    validate_source_record_payloads_v3(candidate)
    validate_public_source_metadata_v3(candidate)
    projection, eligible, dispositions = derive_source_projection_v3(candidate)
    return ValidatedSourceInventorySeamV3._from_bound_candidate(
        candidate,
        seal,
        assets,
        projection,
        eligible,
        tuple(FileDispositionV3(*row) for row in dispositions),
        SourceInventoryCountsV3(**measure_source_inventory_v3(candidate)),
        source_partition_preimage_v3(candidate, dispositions),
    )


def validate_source_inventory_seam_v3(value: ValidatedSourceInventorySeamV3) -> None:
    from tests.contracts.next_source_inventory_v3_validation import (
        validate_source_inventory_seam_v3 as independently_validate,
    )

    independently_validate(value)
