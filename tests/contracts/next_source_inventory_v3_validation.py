"""Independent SI-03 source/proof checks, not full root/locality/Core admission."""

from collections import deque
from dataclasses import asdict
from typing import Any

from tests.contracts.next_reference_validation import (
    COLLECTIONS,
    TAINT_ORDER_INDEX,
    TAINT_ROOT_RULES,
    _assert_canonical,
    _causal_edge_is_allowed,
    _id_kind,
    _is_program_file,
    _record_references,
    _validate_model_collections,
    digest,
    recompute_record_id,
)
from tests.contracts.next_runtime_v2_reference import ValidatedTransportCandidateV2
from tests.contracts.next_runtime_v2_validation import validate_response_request_v2

PROFILE_ID = "next-source-inventory-safe-subset-v1"


class SourceInventoryInvalidErrorV3(ValueError):
    """Private invariant rejection; not a new public diagnostic code."""

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(detail)
        self.reason = reason


def validate_source_record_payloads_v3(candidate: ValidatedTransportCandidateV2) -> None:
    """Source row metadata belongs only to the same retained parent request."""

    for row in candidate.semantic_payload()["proof"]["discovered_records"]:
        if row["collection"] in {"projects", "files"} and "record" in row:
            raise SourceInventoryInvalidErrorV3(
                "proof_source_owner", "source discovery record payload must be omitted"
            )
    request = candidate.request_frame().record()
    for collection in ("projects", "files"):
        observed = [
            row["record_id"]
            for row in candidate.semantic_payload()["proof"]["discovered_records"]
            if row["collection"] == collection
        ]
        if len(observed) != len(set(observed)) or set(observed) != {
            row["id"] for row in request[collection]
        }:
            raise SourceInventoryInvalidErrorV3(
                "proof_source_owner", "acquired source discovery must occur exactly once"
            )


def full_module_owners_v3(candidate: ValidatedTransportCandidateV2) -> dict[str, dict[str, Any]]:
    """Check the normal full base, never hide missing Modules behind File projection."""

    request = candidate.request_frame().record()
    program = {
        (row["project_id"], row["path"]): row["id"]
        for row in request["files"]
        if _is_program_file(row)
    }
    payload = candidate.semantic_payload()
    public = {row["id"]: row for row in payload["model"]["modules"]}
    owners: dict[str, dict[str, Any]] = {}
    for row in payload["proof"]["discovered_records"]:
        if row["collection"] != "modules":
            continue
        module = row.get("record", public.get(row["record_id"]))
        if module is None or module["kind"] != "module" or module["id"] != row["record_id"]:
            raise SourceInventoryInvalidErrorV3(
                "proof_module_owner", "full Module owner missing or misjoined"
            )
        file_id = program.get((module["project_id"], module["path"]))
        if file_id is None or file_id in owners:
            raise SourceInventoryInvalidErrorV3(
                "proof_module_owner", "full Module owner must match one acquired program File"
            )
        owners[file_id] = module
    if set(owners) != set(program.values()):
        raise SourceInventoryInvalidErrorV3(
            "proof_module_owner", "full Module owner cardinality must be one per program File"
        )
    return owners


def validate_public_source_metadata_v3(candidate: ValidatedTransportCandidateV2) -> None:
    request = candidate.request_frame().record()
    model = candidate.semantic_payload()["model"]
    for collection in ("projects", "files"):
        parents = {row["id"]: row for row in request[collection]}
        omitted = {"content_base64"} if collection == "files" else {"file_ids"}
        for row in model[collection]:
            parent = parents.get(row["id"])
            if parent is None or {
                key: value for key, value in row.items() if key not in omitted
            } != {key: value for key, value in parent.items() if key not in omitted}:
                raise SourceInventoryInvalidErrorV3(
                    "file_correspondence" if collection == "files" else "project_correspondence",
                    "public source metadata must match the retained parent request",
                )


def resolve_discovered_v3(candidate: ValidatedTransportCandidateV2) -> dict[str, dict[str, Any]]:
    """Resolve a unique private view; source metadata is never supplied by a child."""

    request = candidate.request_frame().record()
    payload = candidate.semantic_payload()
    model = payload["model"]
    if payload["model_digest"] != digest(model):
        raise SourceInventoryInvalidErrorV3("model_proof", "model/proof digest mismatch")
    try:
        public = _validate_model_collections(model)
        for rows in payload["proof"].values():
            _assert_canonical(rows)
        sources = {
            name: {
                row["id"]: {key: value for key, value in row.items() if key != "content_base64"}
                for row in request[name]
            }
            for name in ("projects", "files")
        }
        result: dict[str, dict[str, Any]] = {}
        for row in payload["proof"]["discovered_records"]:
            name, record_id = row["collection"], row["record_id"]
            assert record_id not in result
            assert _id_kind(record_id) == name.removesuffix("s")
            if name in sources:
                record = sources[name][record_id]
            elif record_id in public[name]:
                assert "record" not in row
                record = public[name][record_id]
            else:
                record = row["record"]
            assert record["id"] == record_id == recompute_record_id(record)
            assert row["taints"] == sorted(row["taints"], key=TAINT_ORDER_INDEX.__getitem__)
            result[record_id] = {**row, "record": record}
        assert all(
            record_id in result and result[record_id]["collection"] == name
            for name in COLLECTIONS
            for record_id in public[name]
        )
        return result
    except (AssertionError, KeyError, TypeError) as error:
        raise SourceInventoryInvalidErrorV3(
            "model_proof", "model/proof discovered record join, identity or order mismatch"
        ) from error


def derive_source_projection_v3(
    candidate: ValidatedTransportCandidateV2,
) -> tuple[dict[str, Any], tuple[str, ...], tuple[tuple[str, str, str | None], ...]]:
    """Derive publication from full retained proof state, not submitted absence."""

    request = candidate.request_frame().record()
    model, proof = candidate.semantic_payload()["model"], candidate.semantic_payload()["proof"]
    owners = full_module_owners_v3(candidate)
    resolved = resolve_discovered_v3(candidate)
    public_ids = {row["id"] for name in COLLECTIONS for row in model[name]}
    if any(not _record_references(row["record"]) <= resolved.keys() for row in resolved.values()):
        raise SourceInventoryInvalidErrorV3("proof_references", "private reference must close in D")
    if any(
        not _record_references(row) <= public_ids for name in COLLECTIONS for row in model[name]
    ):
        raise SourceInventoryInvalidErrorV3("proof_references", "public reference must close in M")
    validate_dispositions_v3(candidate, resolved)
    rows = {row["record_id"]: row for row in proof["discovered_records"]}
    direct_roots: dict[str, set[str]] = {}
    files_by_path = {file["path"]: file for file in request["files"]}
    for root in proof["failure_roots"]:
        if root["kind"] not in {"parse_file", "read_file"}:
            continue
        file = files_by_path.get(root["path_ref"])
        if (
            root["collection"] != "files"
            or file is None
            or file["id"] not in root["record_ids"]
            or root["kind"] not in rows[file["id"]]["taints"]
        ):
            raise SourceInventoryInvalidErrorV3(
                "model_proof", "source File root must join its acquired seed and typed taint"
            )
        direct_roots.setdefault(file["id"], set()).add(root["kind"])
    for file in request["files"]:
        if not set(rows[file["id"]]["taints"]) <= direct_roots.get(file["id"], set()):
            raise SourceInventoryInvalidErrorV3(
                "source_inventory_partition", "File taint cannot be invented from an owner cause"
            )
    witnessed = source_owner_witness_kinds_v3(proof, resolved)
    for file in request["files"]:
        if not set(rows[file["id"]]["taints"]) <= witnessed.get(file["id"], set()):
            raise SourceInventoryInvalidErrorV3(
                "model_proof", "source File root must retain its File causal witness"
            )
    for module in owners.values():
        if not set(rows[module["id"]]["taints"]) <= witnessed.get(module["id"], set()):
            raise SourceInventoryInvalidErrorV3(
                "source_inventory_partition", "owner cause requires matching retained failure roots"
            )
    module_reasons: dict[str, str] = {}
    selected_ids = {
        record_id for row in proof["target_resolutions"] for record_id in row["record_ids"]
    }
    for item in proof["excluded"]:
        if item["collection"] != "modules" or item["reason"] not in {
            "not_selected",
            "target_excluded",
            "unsupported",
        }:
            continue
        module = resolved[item["record_id"]]["record"]
        reason = item["reason"]
        if reason == "unsupported":
            supported_frontier = any(
                row["code"] == "CSV-NEXT-UNSUPPORTED-001"
                and row["outcome"] == "complete"
                and (row["symbol_ref"] == module["id"] or row["path_ref"] == module["path"])
                for row in model["diagnostics"]
            )
            unknown = sum(
                row.get("target", {}).get("kind") == "unresolved" for row in model["relations"]
            )
            if (
                not supported_frontier
                or not unknown
                or model["coverage"]["unknown_relation_count"] != unknown
            ):
                raise SourceInventoryInvalidErrorV3(
                    "source_inventory_partition",
                    "owner cause needs a represented unsupported frontier",
                )
        elif (
            not request["targets"]
            or module["id"] in selected_ids
            or any(
                module["path"] == target.removeprefix("path:")
                or module["path"].startswith(target.removeprefix("path:").rstrip("/") + "/")
                or target == "path:."
                for target in request["targets"]
            )
        ):
            raise SourceInventoryInvalidErrorV3(
                "source_inventory_partition", "owner cause needs unrelated retained selection"
            )
        module_reasons[module["id"]] = reason
    eligible = tuple(
        sorted(
            module["id"]
            for file_id, module in owners.items()
            if not rows[file_id]["taints"]
            and not rows[module["id"]]["taints"]
            and module["id"] not in module_reasons
        )
    )
    if {row["id"] for row in model["modules"]} != set(eligible):
        raise SourceInventoryInvalidErrorV3(
            "source_inventory_partition", "public Module eligibility must equal the full-base set"
        )
    dispositions: list[tuple[str, str, str | None]] = []
    for file in sorted(request["files"], key=lambda row: row["id"]):
        file_id = file["id"]
        if file_id in direct_roots:
            reason = min(direct_roots[file_id], key=TAINT_ORDER_INDEX.__getitem__)
            dispositions.append((file_id, "failed", reason))
        elif rows[file_id]["taints"]:
            dispositions.append((file_id, "excluded", "tainted"))
        elif file_id in owners and owners[file_id]["id"] not in eligible:
            module_id = owners[file_id]["id"]
            reason = "failed" if rows[module_id]["taints"] else module_reasons[module_id]
            dispositions.append((file_id, "excluded", reason))
        else:
            dispositions.append((file_id, "published", None))
    safe = {record_id for record_id, state, _reason in dispositions if state == "published"}
    projection = {
        "files": [
            {key: value for key, value in file.items() if key != "content_base64"}
            for file in sorted(request["files"], key=lambda row: row["id"])
            if file["id"] in safe
        ],
        "projects": [
            {
                **project,
                "file_ids": [record_id for record_id in project["file_ids"] if record_id in safe],
            }
            for project in sorted(request["projects"], key=lambda row: row["id"])
        ],
    }
    actual = [(row["id"], "published", None) for row in model["files"]]
    actual.extend(
        (row["record_id"], state, row["reason"])
        for state in ("excluded", "failed")
        for row in proof[state]
        if row["collection"] == "files"
    )
    if sorted(actual) != dispositions or model["files"] != projection["files"]:
        raise SourceInventoryInvalidErrorV3(
            "source_inventory_partition", "File partition/dispositions must equal the derived set"
        )
    if model["projects"] != projection["projects"]:
        raise SourceInventoryInvalidErrorV3(
            "project_correspondence", "Project safe membership must equal the retained projection"
        )
    return projection, eligible, tuple(dispositions)


def source_owner_witness_kinds_v3(
    proof: dict[str, Any], resolved: dict[str, dict[str, Any]]
) -> dict[str, set[str]]:
    """Join owner causes to supplied closed edges, NOT certify mandatory edge completeness."""

    roots = {root["id"]: root for root in proof["failure_roots"]}
    records = {record_id: row["record"] for record_id, row in resolved.items()}
    if len(roots) != len(proof["failure_roots"]) or any(
        not set(root["record_ids"]) <= records.keys() for root in roots.values()
    ):
        raise SourceInventoryInvalidErrorV3(
            "model_proof", "owner cause root references must close in D"
        )
    adjacency: dict[str, set[str]] = {}
    for edge in proof["causal_edges"]:
        root = roots.get(edge["source_id"])
        if root is not None and edge["record_id"] not in root["record_ids"]:
            raise SourceInventoryInvalidErrorV3(
                "model_proof", "owner cause root-origin edge must target its declared seed"
            )
        if root is not None and edge["rule"] != TAINT_ROOT_RULES[root["kind"]]:
            raise SourceInventoryInvalidErrorV3(
                "model_proof", "owner cause root-origin rule must match the canonical root rule"
            )
        if edge["record_id"] not in records or not _causal_edge_is_allowed(edge, records, roots):
            raise SourceInventoryInvalidErrorV3(
                "proof_references", "owner cause edge must use closed references"
            )
        adjacency.setdefault(edge["source_id"], set()).add(edge["record_id"])
    if any(
        not set(root["record_ids"]) <= adjacency.get(root_id, set())
        for root_id, root in roots.items()
    ):
        raise SourceInventoryInvalidErrorV3(
            "model_proof", "owner cause root-origin witnesses must cover its declared seeds"
        )
    witnessed = {root_id: {root["kind"]} for root_id, root in roots.items()}
    pending = deque(roots)
    while pending:
        source_id = pending.popleft()
        for target_id in adjacency.get(source_id, set()):
            target_kinds = witnessed.setdefault(target_id, set())
            missing = witnessed[source_id] - target_kinds
            if missing:
                target_kinds.update(missing)
                pending.append(target_id)
    return witnessed


def validate_dispositions_v3(
    candidate: ValidatedTransportCandidateV2, resolved: dict[str, dict[str, Any]]
) -> None:
    """Full accounting and local state joins; full selection/taint derivation is SI-04."""

    payload = candidate.semantic_payload()
    actual: dict[str, list[tuple[str, str | None]]] = {record_id: [] for record_id in resolved}
    for name in COLLECTIONS:
        for record in payload["model"][name]:
            actual[record["id"]].append(("published", None))
    for state in ("excluded", "failed"):
        for row in payload["proof"][state]:
            source = resolved.get(row["record_id"])
            if source is None or source["collection"] != row["collection"]:
                raise SourceInventoryInvalidErrorV3(
                    "model_proof", "disposition must join discovery"
                )
            actual[row["record_id"]].append((state, row["reason"]))
    for record_id, row in resolved.items():
        states = actual[record_id]
        if len(states) != 1:
            raise SourceInventoryInvalidErrorV3("model_proof", "every record needs one disposition")
        state, reason = states[0]
        taints = row["taints"]
        if row["collection"] == "projects" and (taints or state != "published"):
            raise SourceInventoryInvalidErrorV3(
                "project_correspondence", "Project disposition/taint forbidden"
            )
        if state == "published" and taints:
            raise SourceInventoryInvalidErrorV3("model_proof", "public records cannot carry taint")
        if state == "failed" and reason not in taints:
            raise SourceInventoryInvalidErrorV3(
                "model_proof", "failed disposition must join typed taint"
            )
        if state == "excluded" and (
            (reason == "tainted" and not taints)
            or (reason == "failed" and not taints and row["collection"] != "files")
            or (taints and reason not in {"tainted", "failed"})
        ):
            raise SourceInventoryInvalidErrorV3(
                "model_proof", "excluded disposition/taint mismatch"
            )


def measure_source_inventory_v3(candidate: ValidatedTransportCandidateV2) -> dict[str, int]:
    request = candidate.request_frame().record()
    payload = candidate.semantic_payload()
    model, proof = payload["model"], payload["proof"]
    published_ids = {row["id"] for name in COLLECTIONS for row in model[name]}
    published = sum(len(model[name]) for name in COLLECTIONS)
    proof_only = sum(row["record_id"] not in published_ids for row in proof["discovered_records"])
    modules, components = len(model["modules"]), len(model["components"])
    expected_coverage = {name: len(model[name]) for name in COLLECTIONS}
    expected_coverage.update(
        internal_entities=modules + components,
        discovered=len(proof["discovered_records"]),
        published=published,
        excluded=len(proof["excluded"]),
        failed=len(proof["failed"]),
    )
    if model["coverage"]["counts"] != expected_coverage:
        raise SourceInventoryInvalidErrorV3(
            "model_proof", "coverage must equal actual inventory counts"
        )
    return {
        "acquired_projects": len(request["projects"]),
        "acquired_files": len(request["files"]),
        "acquired_file_bytes": sum(row["size_bytes"] for row in request["files"]),
        "proof_discovered": len(proof["discovered_records"]),
        "published_records": published,
        "proof_only_records": proof_only,
        "accounted_records": published + proof_only,
        "published_modules": modules,
        "published_components": components,
        "published_entities": modules + components,
    }


def source_partition_preimage_v3(
    candidate: ValidatedTransportCandidateV2,
    dispositions: tuple[tuple[str, str, str | None], ...],
) -> dict[str, Any]:
    states = {record_id: state for record_id, state, _reason in dispositions}
    return {
        "profile_id": PROFILE_ID,
        "request_id": candidate.request_id,
        "projects": [
            {
                "project_id": project["id"],
                **{
                    key: sorted(
                        record_id for record_id in project["file_ids"] if states[record_id] == state
                    )
                    for key, state in (
                        ("safe_file_ids", "published"),
                        ("failed_file_ids", "failed"),
                        ("excluded_file_ids", "excluded"),
                    )
                },
            }
            for project in candidate.request_frame().record()["projects"]
        ],
    }


def validate_source_inventory_seam_v3(value: Any) -> None:
    """Re-derive from the same owners, never use producer caches as the oracle."""

    from tests.contracts.next_source_inventory_v3_reference import (
        FileDispositionV3,
        SourceInventoryCountsV3,
        ValidatedSourceInventorySeamV3,
    )

    if type(value) is not ValidatedSourceInventorySeamV3:
        raise TypeError("source inventory revalidation requires the retained v3 seam")
    candidate, seal, assets = (
        value.transport_candidate(),
        value.source_seal(),
        value.execution_assets(),
    )
    if type(candidate) is not ValidatedTransportCandidateV2:
        raise TypeError("source inventory requires a retained transport candidate")
    validate_response_request_v2(
        candidate.response_frame(), candidate.request_frame(), seal, assets
    )
    if assets.adapter_identity()["version"] != "0.2.0":
        raise SourceInventoryInvalidErrorV3(
            "model_proof", "source inventory requires producer version 0.2.0"
        )
    validate_source_record_payloads_v3(candidate)
    validate_public_source_metadata_v3(candidate)
    projection, eligible, dispositions = derive_source_projection_v3(candidate)
    counts = measure_source_inventory_v3(candidate)
    preimage = source_partition_preimage_v3(candidate, dispositions)
    if (
        value.request_id != candidate.request_id
        or value.profile_id != PROFILE_ID
        or value.safe_files() != projection["files"]
        or value.safe_projects() != projection["projects"]
        or value.eligible_module_ids() != eligible
        or type(value.counts()) is not SourceInventoryCountsV3
        or asdict(value.counts()) != counts
        or any(type(row) is not FileDispositionV3 for row in value.file_dispositions())
        or tuple((row.record_id, row.disposition, row.reason) for row in value.file_dispositions())
        != dispositions
        or value.partition_preimage() != preimage
        or value.partition_fingerprint != digest(preimage)
    ):
        raise SourceInventoryInvalidErrorV3(
            "model_proof", "source inventory cache differs from retained owners"
        )
