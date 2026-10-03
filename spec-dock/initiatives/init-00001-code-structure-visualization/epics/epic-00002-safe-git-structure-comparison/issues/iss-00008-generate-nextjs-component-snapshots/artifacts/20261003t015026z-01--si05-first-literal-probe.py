"""Read-only discovery of existing Core facts; not a TDD or SI-05 pass."""

import hashlib
import json
import tempfile
from dataclasses import asdict
from pathlib import Path

from tests.contracts.next_semantic_core_v3_reference import decide_semantic_candidate_v3
from tests.contracts.test_next_semantic_candidate_v2 import candidate_for
from tests.contracts.test_next_semantic_core_v3 import SOURCE_BYTES, core_inputs_v3

with tempfile.TemporaryDirectory(prefix="si05-literal-") as directory:
    seal, assets, request, policy, wire = core_inputs_v3(Path(directory))
    candidate = candidate_for(seal, assets, request, policy, wire)
    decision = decide_semantic_candidate_v3(candidate, seal, assets)
    seam = decision.source_inventory_seam()
    assert seam is not None
    preimage = {
        "profile_id": "next-source-inventory-safe-subset-v1",
        "request_id": request.request_id,
        "projects": [
            {
                "project_id": project["id"],
                "safe_file_ids": project["file_ids"],
                "failed_file_ids": [],
                "excluded_file_ids": [],
            }
            for project in request.record()["projects"]
        ],
    }
    encoded = json.dumps(preimage, sort_keys=True, separators=(",", ":")).encode()
    independent_hash = hashlib.sha256(encoded).hexdigest()
    assert request.request_id == "4c19dcf0e98eb6df4e58af251216f4a06764cb5edf3217f7298c00995efff122"
    assert independent_hash == "c543f59be0403f3bcf1cf13510f065f6a7e152e555aa394a42960d02a31d6d9f"
    assert seam.partition_preimage() == preimage
    assert seam.partition_fingerprint == independent_hash
    assert len(SOURCE_BYTES) == 6 and sum(map(len, SOURCE_BYTES.values())) == 246
    assert decision.compatibility_descriptor()["compatibility_id"] == (
        "ecf055ae84276a9209e8cb65addabd0cbf4d882e0b76f54cc6f06208fa95880f"
    )
    print(
        json.dumps(
            {
                "request_id": request.request_id,
                "source_sizes": {path: len(raw) for path, raw in SOURCE_BYTES.items()},
                "source_counts": asdict(seam.counts()),
                "partition_preimage": preimage,
                "partition_sha256": independent_hash,
                "compatibility_id": decision.compatibility_descriptor()["compatibility_id"],
                "outcome": decision.gate()["outcome"],
                "entity_actual": decision.gate()["actual"],
                "scope": "existing exact-base Core facts; no public-v3 producer exists",
            },
            sort_keys=True,
        )
    )
