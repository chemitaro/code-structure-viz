"""Inspect the actual failed run and unchanged root run-block schema only."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from tests.contracts.next_final_publication_v2_fixtures import stage_failed_candidates_v3
from tests.contracts.test_json_schemas import _validator

with TemporaryDirectory(prefix="issue8-root-fp-") as task_directory:
    candidates = stage_failed_candidates_v3(Path(task_directory), selector="manifest")
    run = candidates.run_decision()
    record = run.record()
    block = {
        "status": record["status"],
        "exit_code": record["exit_code"],
        "fingerprint": record["context"]["run_fingerprint"],
        "run_context": run.runtime_result().request_frame().analysis_context().run_context(),
    }
    root_schema = _validator("run-manifest-v2.schema.json")
    run_schema = root_schema.evolve(schema=root_schema.schema["$defs"]["run"])
    errors = [
        {"path": list(error.absolute_path), "validator": error.validator,
         "message": error.message}
        for error in run_schema.iter_errors(block)
    ]
    print(json.dumps({
        "evidence": "actual request-bound v3 stage failure / root run-block schema only",
        "failure_code": record["provenance"]["failure_code"],
        "core_present": run.semantic_decision() is not None,
        "run_fingerprint": record["context"]["run_fingerprint"],
        "adapter_capture_pair": candidates.record()["capture_measurements"],
        "root_run_block_errors": errors,
        "root_owner_implemented": False,
        "alternative_hash_adopted": False,
    }, ensure_ascii=False, sort_keys=True))
