"""Read-only product diagnosis; no gate, guard change, or real compiler claim."""

import hashlib
import json
import tempfile
import traceback
from copy import deepcopy
from pathlib import Path

from tests.contracts import next_runtime_v2_reference as runtime
from tests.contracts import next_runtime_v2_validation as validation
from tests.contracts.next_reference_validation import _derive_required_root_seed_ids
from tests.contracts.next_run_decision_v2_reference import retain_request_bound_run_decision_v2
from tests.contracts.test_next_exchange_v2 import exchange_evidence
from tests.contracts.test_next_semantic_candidate_v2 import core_inputs, update_model_digest


def codec(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def joined_run(seal, assets, request, policy, wire):
    response = runtime.retain_response_frame_v2(
        json.dumps(wire).encode(), limits=request.record()["limits"]
    )
    observation = runtime.reference_process_observation_v2(
        policy, exchange_evidence(policy, request, response)
    )
    result = runtime.retain_runtime_result_v2(seal, assets, request, policy, observation, response)
    candidate = result.transport_candidate()
    assert candidate is not None
    core = runtime.inspect_semantic_candidate_v2(candidate, seal, assets)
    run = retain_request_bound_run_decision_v2(result, semantic_decision=core)
    return candidate, core, run, len(response.raw_bytes)


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="csv-a02-root-probe-") as temporary:
        case_directory = Path(temporary) / "file-root"
        case_directory.mkdir()
        seal, assets, request, policy, wire = core_inputs(case_directory)
        candidate, core, run, _ = joined_run(seal, assets, request, policy, wire)
        assert isinstance(core, runtime.ValidatedSemanticDecisionV2)
        assert run.record()["outcome"] == "complete"
        print(json.dumps({"case": "control", "outcome": "complete", "gate": core.gate()}))
        model = wire["semantic_payload"]["model"]
        file = next(row for row in model["files"] if row["path"] == "src/Card.tsx")
        records = {row["id"]: row for rows in (model[k] for k in (
            "projects", "files", "modules", "components", "members", "relations", "facts"
        )) for row in rows}
        for kind in ("parse_file", "read_file"):
            root = {"id": "next:failure:" + "1" * 64, "collection": "files",
                    "kind": kind, "path_ref": "src/Card.tsx", "record_ids": []}
            seeds = _derive_required_root_seed_ids(root, records)
            assert file["id"] in seeds
            print(json.dumps({"case": "required-seeds", "root_kind": kind,
                              "seed_kinds": [records[i]["kind"] for i in seeds],
                              "file_in_required_seed": True}))
            for case in ("retain-tainted-file", "remove-file", "proof-only-file", "omit-file-seed"):
                attempt = deepcopy(wire)
                payload = attempt["semantic_payload"]
                proof = payload["proof"]
                proposed_root = deepcopy(root)
                proposed_root["record_ids"] = seeds if case != "omit-file-seed" else [
                    i for i in seeds if i != file["id"]
                ]
                proof["failure_roots"] = [proposed_root]
                proof["causal_edges"] = sorted([
                    {"source_id": root["id"], "record_id": i, "rule": "file_all_records"}
                    for i in proposed_root["record_ids"]
                ], key=codec)
                if case == "retain-tainted-file":
                    for row in proof["discovered_records"]:
                        if row["record_id"] in seeds:
                            row["taints"] = [kind]
                elif case == "remove-file":
                    payload["model"]["files"] = [
                        row for row in payload["model"]["files"] if row["id"] != file["id"]
                    ]
                elif case == "proof-only-file":
                    row = next(row for row in proof["discovered_records"]
                               if row["record_id"] == file["id"])
                    row["record"] = deepcopy(file)
                update_model_digest(attempt)
                bad_candidate, rejected, rejected_run, _ = joined_run(
                    seal, assets, request, policy, attempt
                )
                assert isinstance(rejected, runtime.RejectedSemanticDecisionV2)
                assert rejected_run.record()["outcome"] == "payload_unavailable"
                try:
                    validation.validate_semantic_candidate_v2(bad_candidate, seal, assets)
                except validation.SemanticCandidateInvalidErrorV2 as error:
                    cause_error = error.__cause__ or error
                    cause_frames = traceback.extract_tb(cause_error.__traceback__)
                    cause = cause_frames[-1]
                    print(json.dumps({"case": case, "root_kind": kind,
                                      "failure": rejected.failure(),
                                      "rejection_origin": {"exception": type(cause_error).__name__,
                                                           "file": Path(cause.filename).name,
                                                           "line": cause.lineno,
                                                           "function": cause.name,
                                                           "expression": cause.line}}))
                else:
                    raise AssertionError("malformed file-root input unexpectedly admitted")

        for delta in (0, 1):
            paths = ["src/missing/" + f"{i:02d}/" + ("a" * 200 + "/") * 18
                     + "b" * (120 + (delta if i == 15 else 0)) + ".tsx" for i in range(16)]
            targets = ["path:" + path for path in paths]
            case_directory = Path(temporary) / f"target-{delta}"
            case_directory.mkdir()
            seal, assets, request, policy, wire = core_inputs(
                case_directory, targets=targets
            )
            rows = [{"target_key": target, "status": "failed", "record_ids": [],
                     "reason": "missing"} for target in targets]
            wire["semantic_payload"]["proof"]["target_resolutions"] = rows
            wire["semantic_payload"]["model"]["coverage"]["target_completeness"] = deepcopy(rows)
            update_model_digest(wire)
            _, core, run, response_length = joined_run(seal, assets, request, policy, wire)
            assert isinstance(core, runtime.ValidatedSemanticDecisionV2)
            assert core.gate()["diagnostic_code"] == "CSV-NEXT-TARGET-001"
            assert core.gate()["target_failures"] == [
                {"target_key": target, "reason": "missing"} for target in targets
            ]
            # Worked independent public literal, NOT an implemented diagnostic projection.
            public_rows = [{"type": "diagnostic", "schema": "code-structure-viz.diagnostic/v1",
                            "code": "CSV-NEXT-TARGET-001", "severity": "error", "domain": "next",
                            "path": path, "symbol": None, "line": None, "reason": "missing",
                            "recoverable": False, "message": "An explicit Next.js target cannot be resolved uniquely.",
                            "outcome": "payload_unavailable", "ref_permission": "path_or_symbol"}
                           for path in paths]
            jsonl = b"".join(codec(row) + b"\n" for row in public_rows)
            assert len(jsonl) == 65536 + delta
            print(json.dumps({"case": "boundary-input-reachability", "delta": delta,
                              "request_bytes": len(request.canonical_bytes),
                              "response_bytes": response_length,
                              "outcome": run.record()["outcome"],
                              "entity_actual": core.gate()["actual"],
                              "literal_jsonl_bytes": len(jsonl),
                              "literal_jsonl_sha256": hashlib.sha256(jsonl).hexdigest(),
                              "targets_bytes": len(codec(targets)),
                              "targets_sha256": hashlib.sha256(codec(targets)).hexdigest(),
                              "diagnostic_owner_or_stderr_gate_certified": False}))


main()
