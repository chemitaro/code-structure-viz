"""Read-only falsification on 58864bf; not a product or future acceptance oracle."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from tests.contracts.next_semantic_core_v3_reference import decide_semantic_candidate_v3
from tests.contracts.next_semantic_core_v3_validation import validate_semantic_decision_v3
from tests.contracts.test_next_semantic_core_v3 import (
    SOURCE_BYTES,
    candidate_for,
    core_inputs_v3,
    exclude_value_module_with_root_v3,
)


def observe(kind: str, context_import: bool) -> dict[str, object]:
    sources = dict(SOURCE_BYTES)
    if context_import:
        sources["src/global.d.ts"] = (
            b'import { value } from "./value";\n' + SOURCE_BYTES["src/global.d.ts"]
        )
    with TemporaryDirectory(prefix="si04-locality-") as directory:
        seal, assets, request, policy, wire = core_inputs_v3(Path(directory), sources=sources)
        exclude_value_module_with_root_v3(wire, request, kind)
        candidate = candidate_for(seal, assets, request, policy, wire)
        decision = decide_semantic_candidate_v3(candidate, seal, assets)
        validate_semantic_decision_v3(decision)
        seam = decision.source_inventory_seam()
        assert seam is not None
        graph = seal.final_plan["source_graph"]
        nodes = {row["id"]: row["path"] for row in graph["nodes"]}
        edges = [(nodes[row["source"]], nodes[row["target"]]) for row in graph["edges"]]
        context = next(row for row in request.record()["files"] if row["path"] == "src/global.d.ts")
        discovery = next(
            row for row in candidate.semantic_payload()["proof"]["discovered_records"]
            if row["record_id"] == context["id"]
        )
        public_files = sorted(row["path"] for row in seam.safe_files())
        # Record the current wrong result, not a newly adopted expectation.
        assert decision.gate()["payload_available"] is True
        assert decision.gate()["outcome"] == "partial_safe"
        assert "src/global.d.ts" in public_files
        if context_import:
            assert ("src/global.d.ts", "src/value.ts") in edges
            assert "src/global.d.ts" in decision.locality()["reverse_affected_paths"]
        return {
            "case": "context_reverse_importer" if context_import else "independent_context_control",
            "root_kind": kind,
            "actual_source_owner": type(seal).__name__,
            "acquisition_failures": list(seal.source_view.failures),
            "graph_edges": sorted(edges),
            "graph_open_edges": graph["open_edges"],
            "context_roles": context["roles"],
            "context_taints": discovery["taints"],
            "safe_files": public_files,
            "locality": decision.locality(),
            "gate": decision.gate(),
            "independent_validator": "accepted",
        }


if __name__ == "__main__":
    print(json.dumps({
        "candidate_sha": "58864bf0223e35c6cf31ca09b0d9040954e3d9cc",
        "purpose": "current-behavior falsification; no tracked file or canonical meaning changed",
        "observations": [
            observe(kind, context_import)
            for kind in ("parse_file", "read_file")
            for context_import in (False, True)
        ],
    }, ensure_ascii=False, indent=2))
