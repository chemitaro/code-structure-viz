"""Read-only SI06 brief admission observations; not final-owner acceptance tests."""

import json
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator

from tests.contracts import next_runtime_v2_reference as runtime_reference
from tests.contracts.next_publication_candidates_v3_reference import (
    retain_request_bound_publication_candidates_v3,
)
from tests.contracts.next_run_decision_v3_reference import retain_request_bound_run_decision_v3
from tests.contracts.test_next_process_observation_v2 import complete_evidence
from tests.contracts.test_next_semantic_core_v3 import core_inputs_v3


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="issue8-si06-admission-") as task_temp:
        seal, assets, request, policy, _wire = core_inputs_v3(Path(task_temp))
        evidence = complete_evidence(policy)
        evidence.update(
            response=None,
            terminal_cause="stage_failed",
            spawn=None,
            capture=None,
            exit_code=None,
        )
        evidence["cleanup"].update(
            group_stop="not_required", signals=[], direct_child_waited=False
        )
        observation = runtime_reference.reference_process_observation_v2(policy, evidence)
        runtime = runtime_reference.retain_runtime_result_v2(
            seal, assets, request, policy, observation, None
        )
        run = retain_request_bound_run_decision_v3(runtime)
        candidates = retain_request_bound_publication_candidates_v3(run)
        publication_schema = json.loads(
            Path("schemas/next-publication-decision-v2.schema.json").read_text()
        )
        measurement_schema = publication_schema["$defs"]["measurement"]
        unavailable_branch = publication_schema["oneOf"][2]
        branch_vector = {
            "publication_outcome": "payload_unavailable",
            "artifacts": [],
            "response": {"request_id": "0" * 64},
            "stdout": {"availability": False},
            "exit_code": 3,
        }
        results = {
            "probe_scope": "actual existing request-bound stage failure and schema fragments only",
            "runtime_result_kind": runtime.result_kind,
            "run_outcome": run.record()["outcome"],
            "provenance_stage": run.record()["provenance"]["stage"],
            "failure_code": run.record()["provenance"]["failure_code"],
            "runtime_capture": runtime.observation()["capture"],
            "candidate_capture_measurements": candidates.record()["capture_measurements"],
            "publication_measurement_accepts_null": Draft202012Validator(
                measurement_schema
            ).is_valid(None),
            "publication_measurement_accepts_zero_object": Draft202012Validator(
                measurement_schema
            ).is_valid({"allowed": True, "measured_bytes": 0, "retained_bytes": 0}),
            "unavailable_branch_nonnull_response_errors": [
                {"path": list(error.path), "message": error.message}
                for error in Draft202012Validator(unavailable_branch).iter_errors(branch_vector)
            ],
            "limits": {
                key: request.record()["limits"][key]
                for key in (
                    "max_adapter_stdout_capture_bytes",
                    "max_adapter_stderr_capture_bytes",
                    "max_stderr_bytes",
                    "max_selected_stdout_bytes",
                )
            },
            "no_si06_code_or_certificate": True,
        }
        print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
