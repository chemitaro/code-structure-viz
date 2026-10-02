"""Incremental v3 Core reference checks; production execution is a separate gate."""

import hashlib
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from code_structure_viz.adapters.next.source_acquisition import SourceAcquisitionSeal
from code_structure_viz.semantic.canonical_json import encode_canonical_json
from tests.contracts.next_reference_validation import (
    COLLECTIONS,
    ModelRecordLimitError,
    NextTargetCompletenessFailure,
    _derived_taint_fixed_point,
    _export_tokens,
    _opaque_reason_counts,
    _record_references,
    _reexport_join_key,
    _resolve_export_source_path,
    _scan_export_file,
    _string_export_resolution,
    _target_contains_export,
    _terminal_export_source_path,
    canonical_json_bytes,
    canonical_run_context,
    derive_pre_budget_outcome,
    digest,
    entity_budget_gate,
    expected_string_export_diagnostics,
    export_failure_decision,
    join_reexport_observations_to_edges,
    recompute_export_graph_case,
    recompute_record_id,
    resolve_target_resolutions,
    response_model_record_counts,
    string_export_target_resolutions,
    target_failure_decision,
    target_failure_from_proof,
    validate_model,
)
from tests.contracts.next_runtime_v2_reference import (
    RetainedExecutionAssets,
    ValidatedTransportCandidateV2,
)
from tests.contracts.next_runtime_v2_validation import validate_response_request_v2
from tests.contracts.next_semantic_profile_v1_reference import semantic_compatibility_metadata_v2
from tests.contracts.next_source_inventory_v3_reference import (
    ValidatedSourceInventorySeamV3,
    retain_source_inventory_seam_v3,
    validate_source_inventory_seam_v3,
)
from tests.contracts.next_source_inventory_v3_validation import (
    SourceInventoryInvalidErrorV3,
    full_module_owners_v3,
    resolve_discovered_v3,
    validate_public_source_metadata_v3,
    validate_source_record_payloads_v3,
)

if TYPE_CHECKING:
    from tests.contracts.next_semantic_core_v3_reference import (
        RejectedSemanticDecisionV3,
        ValidatedSemanticDecisionV3,
    )

INVARIANT_REASONS_V3 = frozenset(
    {
        "file_correspondence",
        "project_correspondence",
        "proof_source_owner",
        "proof_module_owner",
        "proof_references",
        "model_proof",
        "source_inventory_partition",
    }
)


class SemanticCandidateInvalidErrorV3(ValueError):
    """Closed invariant metadata, not an exception-text public diagnostic."""

    def __init__(self, reason: str) -> None:
        if reason not in INVARIANT_REASONS_V3:
            raise ValueError("unknown v3 semantic invariant reason")
        super().__init__(reason)
        self.reason = reason


def validate_compatibility_descriptor_v3(
    value: dict[str, Any], candidate: ValidatedTransportCandidateV2
) -> None:
    """Re-derive ten owner/profile fields without calling the descriptor producer."""

    if type(candidate) is not ValidatedTransportCandidateV2:
        raise TypeError("compatibility requires a retained transport candidate")
    context = candidate.request_frame().analysis_context()
    validate_response_request_v2(
        candidate.response_frame(),
        candidate.request_frame(),
        context.source_seal(),
        context.execution_assets(),
    )
    binding = candidate.runtime_binding()
    expected = {
        **semantic_compatibility_metadata_v2(),
        "semantic_schema": "code-structure-viz.semantic/v3",
        "semantic_admission_profile_id": "next-source-inventory-safe-subset-v1",
        "typescript_identity": binding["typescript_identity"],
        "trusted_type_environment_digest": binding["trusted_type_environment_digest"],
        "portable_toolchain_fingerprint": binding["runtime_toolchain_fingerprint"],
    }
    if canonical_json_bytes(value) != canonical_json_bytes(
        {
            "schema": "code-structure-viz.next-semantic-compatibility/v3",
            **expected,
            "compatibility_id": digest(expected),
        }
    ):
        raise ValueError("compatibility differs from its retained profile/runtime binding")


def validate_full_taint_proof_v3(candidate: ValidatedTransportCandidateV2) -> None:
    """Preserve mandatory roots/causal rules and the exact typed fixed point."""

    resolved = resolve_discovered_v3(candidate)
    discovered: dict[str, dict[str, dict[str, Any]]] = {name: {} for name in COLLECTIONS}
    for record_id, row in resolved.items():
        discovered[row["collection"]][record_id] = row
    try:
        _derived_taint_fixed_point(candidate.semantic_payload()["proof"], discovered)
    except AssertionError as error:
        raise SemanticCandidateInvalidErrorV3("model_proof") from error


def validate_proof_coverage_v3(candidate: ValidatedTransportCandidateV2) -> None:
    payload = candidate.semantic_payload()
    resolved = resolve_discovered_v3(candidate)
    tainted = {record_id for record_id, row in resolved.items() if row["taints"]}
    expected = {
        "affected_ids": sorted(tainted),
        "taint_frontier": sorted(
            {
                referenced
                for record_id in tainted
                for referenced in _record_references(resolved[record_id]["record"])
                if referenced in resolved
                and referenced not in tainted
                and resolved[referenced]["collection"] != "projects"
            }
        ),
        "failed_files": sorted(
            [
                {"path": resolved[row["record_id"]]["record"]["path"], "reason": row["reason"]}
                for row in payload["proof"]["failed"]
                if row["collection"] == "files"
            ],
            key=canonical_json_bytes,
        ),
    }
    if {key: payload["model"]["coverage"][key] for key in expected} != expected:
        raise SemanticCandidateInvalidErrorV3("model_proof")
    model = payload["model"]
    coverage = model["coverage"]
    components = {row["id"] for row in model["components"]}
    props = {row["id"]: row for row in model["members"] if row["kind"] == "prop"}
    if coverage["unknown_relation_count"] != sum(
        row.get("target", {}).get("kind") == "unresolved" for row in model["relations"]
    ) or any(
        loss["component_id"] not in components
        or loss["prop_ids"] != sorted(loss["prop_ids"])
        or loss["signature_count"]
        > candidate.request_frame().record()["limits"]["max_signatures_per_component"]
        or any(
            props.get(prop_id, {}).get("owner_id") != loss["component_id"]
            for prop_id in loss["prop_ids"]
        )
        for loss in coverage["correlation_losses"]
    ):
        raise SemanticCandidateInvalidErrorV3("model_proof")


def validate_full_model_semantics_v3(candidate: ValidatedTransportCandidateV2) -> None:
    """Apply unchanged record/Props grammar to acquired and proof-only records."""

    resolved = resolve_discovered_v3(candidate)
    public_model = candidate.semantic_payload()["model"]
    full_model = {
        **public_model,
        **{
            name: sorted(
                [row["record"] for row in resolved.values() if row["collection"] == name],
                key=lambda row: row["id"],
            )
            for name in COLLECTIONS
        },
    }
    opaque_counts: dict[str, int] = {}
    for member in full_model["members"]:
        if member["kind"] == "prop":
            for reason, count in _opaque_reason_counts(member["type_node"]).items():
                opaque_counts[reason] = opaque_counts.get(reason, 0) + count
    full_model["coverage"] = {
        **public_model["coverage"],
        "opaque_reason_counts": opaque_counts,
        "counts": {
            **{name: len(full_model[name]) for name in COLLECTIONS},
            "published": len(resolved),
            "discovered": len(resolved),
            "excluded": 0,
            "failed": 0,
            "internal_entities": len(full_model["modules"]) + len(full_model["components"]),
        },
    }
    try:
        validate_model(
            full_model,
            max_model_records=candidate.request_frame().record()["limits"]["max_total_array_items"],
        )
    except AssertionError as error:
        raise SemanticCandidateInvalidErrorV3("model_proof") from error


def validate_export_syntax_v3(
    candidate: ValidatedTransportCandidateV2, seal: SourceAcquisitionSeal
) -> None:
    """Full-D syntax comes only from the same retained frozen source bytes."""

    resolved = resolve_discovered_v3(candidate)
    content_by_path = {str(file.path): file.content for file in seal.source_view.files}
    expected = []
    for row in resolved.values():
        if row["collection"] != "modules":
            continue
        module = row["record"]
        for syntax in _scan_export_file(module["path"], content_by_path[module["path"]]):
            expected.append(
                {
                    "owner_module_id": module["id"],
                    **{key: item for key, item in syntax.items() if key != "target_declaration_id"},
                }
            )
    semantic_fields = {
        "resolution",
        "resolution_basis",
        "component_id",
        "target_declaration_id",
        "resolved_source_module_id",
        "expanded_exported_name",
        "disposition",
    }
    observed = [
        {key: item for key, item in row.items() if key not in semantic_fields}
        for row in candidate.semantic_payload()["proof"]["export_observations"]
    ]
    if sorted(expected, key=canonical_json_bytes) != sorted(observed, key=canonical_json_bytes):
        raise SemanticCandidateInvalidErrorV3("model_proof")


def _primitive_const_v3(name: str, content: bytes) -> bool:
    """Positive byte proof of the unchanged closed primitive-const grammar."""

    tokens, _text, _offsets = _export_tokens(content)
    for index, token in enumerate(tokens):
        if (
            token["kind"] != "identifier"
            or token["value"] != "const"
            or any(token[key] != 0 for key in ("brace_depth", "paren_depth", "bracket_depth"))
        ):
            continue
        declaration = tokens[index + 1 : index + 5]
        if len(declaration) != 4:
            continue
        identifier, equals, literal, end = declaration
        if (
            identifier["kind"] == "identifier"
            and identifier["value"] == name
            and equals["value"] == "="
            and end["value"] == ";"
            and (
                literal["kind"] == "string"
                or literal["value"] in {"true", "false", "null"}
                or re.fullmatch(r"[0-9]", literal["value"])
            )
        ):
            return True
    return False


def derive_reexport_witnesses_v3(
    candidate: ValidatedTransportCandidateV2, seal: SourceAcquisitionSeal
) -> list[dict[str, Any]]:
    """Recompute a graph from full-D declarations and same-seal syntax only."""

    resolved = resolve_discovered_v3(candidate)
    modules = {
        row["record"]["path"]: row["record"]
        for row in resolved.values()
        if row["collection"] == "modules"
    }
    components = {
        (row["record"]["module_id"], row["record"]["declaration_key"]): row["record"]
        for row in resolved.values()
        if row["collection"] == "components"
    }
    content_by_path = {str(file.path): file.content for file in seal.source_view.files}
    syntax_rows = [
        syntax for path in modules for syntax in _scan_export_file(path, content_by_path[path])
    ]
    direct_tables = []
    for path, module in modules.items():
        exports = []
        for syntax in syntax_rows:
            if (
                syntax["owner_file_path"] != path
                or syntax["reexport"]
                or syntax["syntax_kind"] == "string_export"
            ):
                continue
            declaration_key = syntax["imported_name"] or syntax["exported_name"]
            component = components.get((module["id"], declaration_key))
            if syntax["role"] == "type":
                resolution, target = "type", None
            elif component is not None:
                resolution, target = "component", component["declaration_key"]
            elif _primitive_const_v3(declaration_key, content_by_path[path]):
                resolution, target = "value", None
            else:
                raise SemanticCandidateInvalidErrorV3("model_proof")
            exports.append(
                {
                    "name": syntax["exported_name"],
                    "resolution": resolution,
                    "target_declaration_key": target,
                }
            )
        direct_tables.append({"path": path, "exports": exports})
    raw_edges = [
        {
            key: syntax[key]
            for key in (
                "owner_file_path",
                "source_specifier",
                "imported_name",
                "exported_name",
                "syntax_identity",
                "byte_start",
                "byte_end",
            )
        }
        for syntax in syntax_rows
        if syntax["reexport"] and syntax["syntax_kind"] != "string_export"
    ]
    joined = join_reexport_observations_to_edges(syntax_rows, raw_edges)
    syntax_by_key = {_reexport_join_key(syntax): syntax for syntax, _edge in joined}
    graph = recompute_export_graph_case({"modules": direct_tables, "edges": raw_edges})
    expected = []
    for witness in graph["witnesses"]:
        syntax = syntax_by_key[_reexport_join_key(witness)]
        source_module = modules.get(_terminal_export_source_path(witness, graph))
        component = (
            components.get((source_module["id"], witness["target_declaration_key"]))
            if source_module is not None and witness["resolution"] == "component"
            else None
        )
        if witness["resolution"] == "component" and component is None:
            raise SemanticCandidateInvalidErrorV3("model_proof")
        expected.append(
            {
                "owner_module_id": modules[witness["owner_file_path"]]["id"],
                "owner_file_path": witness["owner_file_path"],
                "byte_start": syntax["byte_start"],
                "byte_end": syntax["byte_end"],
                "token_identity": syntax["token_identity"],
                "syntax_identity": syntax["syntax_identity"],
                "source_specifier": witness["source_specifier"],
                "imported_name": witness["imported_name"],
                "original_exported_name": witness["original_exported_name"],
                "exported_name": witness["exported_name"],
                "resolved_source_module_id": source_module["id"] if source_module else None,
                "expanded_exported_name": witness["expanded_exported_name"],
                "target_declaration_id": component["id"] if component else None,
                "resolution": witness["resolution"],
                "diagnostic": witness["diagnostic"],
            }
        )
    return sorted(expected, key=canonical_json_bytes)


def validate_export_reexports_v3(
    candidate: ValidatedTransportCandidateV2, seal: SourceAcquisitionSeal
) -> None:
    expected = derive_reexport_witnesses_v3(candidate, seal)
    observed = candidate.semantic_payload()["proof"]["export_reexport_witness"]
    if observed != expected:
        raise SemanticCandidateInvalidErrorV3("model_proof")


def validate_reexport_observations_v3(
    candidate: ValidatedTransportCandidateV2, seal: SourceAcquisitionSeal
) -> None:
    witnesses = derive_reexport_witnesses_v3(candidate, seal)
    modules = {
        row["record"]["path"]: row["record"]
        for row in resolve_discovered_v3(candidate).values()
        if row["collection"] == "modules"
    }
    content_by_path = {str(file.path): file.content for file in seal.source_view.files}
    expected = []
    for path, module in modules.items():
        for syntax in _scan_export_file(path, content_by_path[path]):
            if not syntax["reexport"] or syntax["syntax_kind"] == "string_export":
                continue
            matching = [
                row for row in witnesses if _reexport_join_key(row) == _reexport_join_key(syntax)
            ]
            if not syntax["star"] and len(matching) != 1:
                raise SemanticCandidateInvalidErrorV3("model_proof")
            source_module = modules.get(
                _resolve_export_source_path(path, syntax["source_specifier"])
            )
            source_id = (
                matching[0]["resolved_source_module_id"]
                if matching
                else source_module["id"]
                if source_module
                else None
            )
            resolution = "unknown" if syntax["star"] else matching[0]["resolution"]
            component_id = (
                matching[0]["target_declaration_id"] if resolution == "component" else None
            )
            expected.append(
                {
                    "owner_module_id": module["id"],
                    **syntax,
                    "resolution": resolution,
                    "component_id": component_id,
                    "target_declaration_id": component_id,
                    "resolved_source_module_id": source_id,
                    "expanded_exported_name": None
                    if syntax["star"]
                    else matching[0]["expanded_exported_name"],
                }
            )
    observed = [
        row
        for row in candidate.semantic_payload()["proof"]["export_observations"]
        if row["reexport"] and row["syntax_kind"] != "string_export"
    ]
    if observed != sorted(expected, key=canonical_json_bytes):
        raise SemanticCandidateInvalidErrorV3("model_proof")


def validate_direct_export_observations_v3(
    candidate: ValidatedTransportCandidateV2, seal: SourceAcquisitionSeal
) -> None:
    resolved = resolve_discovered_v3(candidate)
    components = {
        (row["record"]["module_id"], row["record"]["declaration_key"]): row["record"]
        for row in resolved.values()
        if row["collection"] == "components"
    }
    content_by_path = {str(file.path): file.content for file in seal.source_view.files}
    expected = []
    for row in resolved.values():
        if row["collection"] != "modules":
            continue
        module = row["record"]
        for syntax in _scan_export_file(module["path"], content_by_path[module["path"]]):
            if syntax["reexport"] or syntax["syntax_kind"] == "string_export":
                continue
            name = syntax["imported_name"] or syntax["exported_name"]
            component = components.get((module["id"], name))
            if syntax["role"] == "type":
                resolution, component_id = "type", None
            elif component is not None:
                resolution, component_id = "component", component["id"]
            elif _primitive_const_v3(name, content_by_path[module["path"]]):
                resolution, component_id = "value", None
            else:
                raise SemanticCandidateInvalidErrorV3("model_proof")
            expected.append(
                {
                    "owner_module_id": module["id"],
                    **syntax,
                    "resolution": resolution,
                    "component_id": component_id,
                    "target_declaration_id": component_id,
                    "resolved_source_module_id": module["id"],
                    "expanded_exported_name": syntax["exported_name"],
                }
            )
    observed = [
        row
        for row in candidate.semantic_payload()["proof"]["export_observations"]
        if not row["reexport"] and row["syntax_kind"] != "string_export"
    ]
    if observed != sorted(expected, key=canonical_json_bytes):
        raise SemanticCandidateInvalidErrorV3("model_proof")


def derive_string_export_observations_v3(
    candidate: ValidatedTransportCandidateV2, seal: SourceAcquisitionSeal
) -> list[dict[str, Any]]:
    resolved = resolve_discovered_v3(candidate)
    components = [row["record"] for row in resolved.values() if row["collection"] == "components"]
    content_by_path = {str(file.path): file.content for file in seal.source_view.files}
    targets = candidate.request_frame().record()["targets"]
    expected = []
    for row in resolved.values():
        if row["collection"] != "modules":
            continue
        module = row["record"]
        owned_components = [item for item in components if item["module_id"] == module["id"]]
        for syntax in _scan_export_file(module["path"], content_by_path[module["path"]]):
            if syntax["syntax_kind"] != "string_export":
                continue
            resolution, basis, component_id = _string_export_resolution(
                syntax, content_by_path[module["path"]], owned_components
            )
            observation = {
                "owner_module_id": module["id"],
                **syntax,
                "resolution": resolution,
                "resolution_basis": basis,
                "component_id": component_id,
                "target_declaration_id": component_id,
                "resolved_source_module_id": None if syntax["reexport"] else module["id"],
                "expanded_exported_name": None,
                "disposition": (
                    "intentional_unsupported"
                    if resolution in {"value", "type"}
                    else "export_failure"
                ),
            }
            if any(_target_contains_export(target, observation) for target in targets):
                observation["disposition"] = "target_failure"
            expected.append(observation)
    return sorted(expected, key=canonical_json_bytes)


def validate_string_export_observations_v3(
    candidate: ValidatedTransportCandidateV2, seal: SourceAcquisitionSeal
) -> None:
    observed = [
        row
        for row in candidate.semantic_payload()["proof"]["export_observations"]
        if row["syntax_kind"] == "string_export"
    ]
    if observed != derive_string_export_observations_v3(candidate, seal):
        raise SemanticCandidateInvalidErrorV3("model_proof")


def derive_public_export_bindings_v3(
    candidate: ValidatedTransportCandidateV2, seal: SourceAcquisitionSeal
) -> list[dict[str, Any]]:
    """Project only source-derived component exports with both public owners."""

    payload = candidate.semantic_payload()
    public_modules = {row["id"] for row in payload["model"]["modules"]}
    public_components = {row["id"] for row in payload["model"]["components"]}
    resolved = resolve_discovered_v3(candidate)
    components = {
        (row["record"]["module_id"], row["record"]["declaration_key"]): row["record"]
        for row in resolved.values()
        if row["collection"] == "components"
    }
    content_by_path = {str(file.path): file.content for file in seal.source_view.files}
    bindings: dict[str, dict[str, Any]] = {}

    def add_binding(owner: str, name: str, component_id: str, *, reexport: bool) -> None:
        if owner not in public_modules or component_id not in public_components:
            return
        binding: dict[str, Any] = {
            "kind": "export_binding",
            "owner_id": owner,
            "exported_name": name,
            "role": "value",
            "target_component_id": component_id,
            "resolution_kind": "component",
            "reexport": reexport,
        }
        binding["id"] = recompute_record_id(binding)
        if binding["id"] in bindings and bindings[binding["id"]] != binding:
            raise SemanticCandidateInvalidErrorV3("model_proof")
        bindings[binding["id"]] = binding

    for row in resolved.values():
        if row["collection"] != "modules":
            continue
        module = row["record"]
        for syntax in _scan_export_file(module["path"], content_by_path[module["path"]]):
            if syntax["reexport"] or syntax["syntax_kind"] == "string_export":
                continue
            component = components.get(
                (module["id"], syntax["imported_name"] or syntax["exported_name"])
            )
            if syntax["role"] == "value" and component is not None:
                add_binding(module["id"], syntax["exported_name"], component["id"], reexport=False)
    for witness in derive_reexport_witnesses_v3(candidate, seal):
        if witness["resolution"] == "component":
            add_binding(
                witness["owner_module_id"],
                witness["exported_name"],
                witness["target_declaration_id"],
                reexport=True,
            )
    return sorted(bindings.values(), key=lambda binding: binding["id"])


def validate_public_export_bindings_v3(
    candidate: ValidatedTransportCandidateV2, seal: SourceAcquisitionSeal
) -> None:
    expected = derive_public_export_bindings_v3(candidate, seal)
    payload = candidate.semantic_payload()
    observed = [row for row in payload["model"]["members"] if row["kind"] == "export_binding"]
    witnesses = sorted(
        [
            {
                "member_id": binding["id"],
                "resolution": "component",
                "component_id": binding["target_component_id"],
            }
            for binding in expected
        ],
        key=canonical_json_bytes,
    )
    if observed != expected or payload["proof"]["export_resolution_witness"] != witnesses:
        raise SemanticCandidateInvalidErrorV3("model_proof")


def validate_public_export_coverage_v3(
    candidate: ValidatedTransportCandidateV2, seal: SourceAcquisitionSeal
) -> None:
    """Count the exactly revalidated evidence on the public owner surface."""

    payload = candidate.semantic_payload()
    public_modules = {row["id"] for row in payload["model"]["modules"]}
    public_evidence = [
        row
        for row in payload["proof"]["export_observations"]
        if row["owner_module_id"] in public_modules
        and (not row["reexport"] or row["syntax_kind"] == "string_export")
    ] + [
        row
        for row in derive_reexport_witnesses_v3(candidate, seal)
        if row["owner_module_id"] in public_modules
    ]
    expected = {
        "non_component_value_export_count": sum(
            row["resolution"] == "value" for row in public_evidence
        ),
        "type_only_export_count": sum(row["resolution"] == "type" for row in public_evidence),
    }
    if {key: payload["model"]["coverage"][key] for key in expected} != expected:
        raise SemanticCandidateInvalidErrorV3("model_proof")


def validate_string_export_diagnostics_v3(
    candidate: ValidatedTransportCandidateV2, seal: SourceAcquisitionSeal
) -> None:
    model = candidate.semantic_payload()["model"]
    public_modules = {row["id"] for row in model["modules"]}
    observations = derive_string_export_observations_v3(candidate, seal)
    string_owners = {row["owner_module_id"] for row in observations}
    expected = expected_string_export_diagnostics(
        [row for row in observations if row["owner_module_id"] in public_modules]
    )
    observed = [
        row
        for row in model["diagnostics"]
        if row["code"] == "CSV-NEXT-UNSUPPORTED-001" and row["symbol_ref"] in string_owners
    ]
    if observed != expected:
        raise SemanticCandidateInvalidErrorV3("model_proof")


def derive_post_acquisition_locality_v3(
    candidate: ValidatedTransportCandidateV2, seal: SourceAcquisitionSeal
) -> dict[str, Any]:
    """Use the complete production seal, never a synthetic acquisition ledger."""

    seal.__post_init__()
    graph = seal.final_plan["source_graph"]
    if (
        hashlib.sha256(
            encode_canonical_json({key: graph[key] for key in ("nodes", "edges", "open_edges")})
        ).hexdigest()
        != graph["graph_digest"]
    ):
        raise ValueError("source owner graph digest mismatch")
    files = {str(file.path): file for file in seal.source_view.files}
    nodes = {row["id"]: row for row in graph["nodes"]}
    node_by_path = {row["path"]: row["id"] for row in graph["nodes"]}
    for row in nodes.values():
        if (
            row["path"] not in files
            or files[row["path"]].sha256 != row["content_sha256"]
            or hashlib.sha256(files[row["path"]].content).hexdigest() != row["content_sha256"]
        ):
            raise ValueError("source owner graph node mismatch")
    forward: dict[str, set[str]] = {node_id: set() for node_id in nodes}
    reverse: dict[str, set[str]] = {node_id: set() for node_id in nodes}
    for edge in graph["edges"]:
        forward[edge["source"]].add(edge["target"])
        reverse[edge["target"]].add(edge["source"])

    def closure(start: str, adjacency: dict[str, set[str]]) -> set[str]:
        reached: set[str] = set()
        pending = [start]
        while pending:
            current = pending.pop()
            if current not in reached:
                reached.add(current)
                pending.extend(adjacency[current])
        return reached

    roots = [
        root
        for root in candidate.semantic_payload()["proof"]["failure_roots"]
        if root["kind"] in {"parse_file", "read_file"}
    ]
    affected: set[str] = set()
    reverse_affected: set[str] = set()
    resolved = resolve_discovered_v3(candidate)
    module_rows = {
        row["record"]["path"]: row for row in resolved.values() if row["collection"] == "modules"
    }
    for root in roots:
        start = node_by_path.get(root["path_ref"])
        if start is None:
            raise SemanticCandidateInvalidErrorV3("model_proof")
        reverse_reached = closure(start, reverse)
        # Source graph cannot be narrowed by omitting a semantic import edge.
        # Reverse importers must carry the same validated File-failure taint;
        # File publication is then independently closed over Module eligibility.
        if any(
            root["kind"] not in module_rows[path]["taints"]
            for node_id in reverse_reached
            if (path := nodes[node_id]["path"]) in module_rows
        ):
            raise SemanticCandidateInvalidErrorV3("model_proof")
        affected.update(closure(start, forward) | reverse_reached)
        reverse_affected.update(reverse_reached)
    affected_paths = sorted(nodes[node_id]["path"] for node_id in affected)
    targets = candidate.request_frame().record()["targets"]
    target_tainted = (
        any(
            target == "path:."
            or any(
                path == target.removeprefix("path:")
                or path.startswith(target.removeprefix("path:").rstrip("/") + "/")
                for path in affected_paths
            )
            for target in targets
        )
        if roots
        else False
    )
    open_dependency = bool(roots) and any(
        edge["source"] in affected or edge["syntax_kind"] == "module_plane"
        for edge in graph["open_edges"]
    )
    return {
        "source_seal_id": seal.seal_id,
        "source_graph_digest": graph["graph_digest"],
        "affected_paths": affected_paths,
        "reverse_affected_paths": sorted(nodes[node_id]["path"] for node_id in reverse_affected),
        "target_tainted": target_tainted,
        "localized": not (target_tainted or open_dependency),
    }


def validate_target_proof_v3(
    candidate: ValidatedTransportCandidateV2,
) -> NextTargetCompletenessFailure | None:
    payload = candidate.semantic_payload()
    resolved = resolve_discovered_v3(candidate)
    full_model = {
        name: sorted(
            [row["record"] for row in resolved.values() if row["collection"] == name],
            key=lambda row: row["id"],
        )
        for name in COLLECTIONS
    }
    public_ids = {row["id"] for name in COLLECTIONS for row in payload["model"][name]}
    expected = string_export_target_resolutions(
        resolve_target_resolutions(
            candidate.request_frame().record()["targets"],
            full_model,
            unavailable_record_ids=resolved.keys() - public_ids,
        ),
        payload["proof"]["export_observations"],
    )
    coverage = [
        {**row, "status": "complete" if row["status"] == "resolved" else "failed"}
        for row in expected
    ]
    if (
        payload["proof"]["target_resolutions"] != expected
        or payload["model"]["coverage"]["target_completeness"] != coverage
    ):
        raise SemanticCandidateInvalidErrorV3("model_proof")
    return target_failure_from_proof(payload["proof"])


@dataclass(frozen=True, slots=True)
class CoreValidationResultV3:
    source_inventory: ValidatedSourceInventorySeamV3
    gate: dict[str, Any]
    locality: dict[str, Any]
    measurements: dict[str, Any]


def validate_semantic_candidate_v3(
    candidate: ValidatedTransportCandidateV2,
    seal: SourceAcquisitionSeal,
    assets: RetainedExecutionAssets,
) -> CoreValidationResultV3:
    """Map only the lower seam's expected invariant errors; owner errors escape."""

    try:
        return _validate_semantic_candidate_v3(candidate, seal, assets)
    except SourceInventoryInvalidErrorV3 as error:
        raise SemanticCandidateInvalidErrorV3(error.reason) from error


def _validate_semantic_candidate_v3(
    candidate: ValidatedTransportCandidateV2,
    seal: SourceAcquisitionSeal,
    assets: RetainedExecutionAssets,
) -> CoreValidationResultV3:
    """Validate the normal source-bound positive; later SI-04 checks remain open."""

    if type(candidate) is not ValidatedTransportCandidateV2:
        raise TypeError("Core requires a retained transport candidate")
    validate_response_request_v2(
        candidate.response_frame(), candidate.request_frame(), seal, assets
    )
    if assets.adapter_identity()["version"] != "0.2.0":
        raise ValueError("Core v3 requires retained producer version 0.2.0")
    validate_source_record_payloads_v3(candidate)
    validate_public_source_metadata_v3(candidate)
    full_module_owners_v3(candidate)
    validate_full_model_semantics_v3(candidate)
    validate_full_taint_proof_v3(candidate)
    validate_proof_coverage_v3(candidate)
    validate_export_syntax_v3(candidate, seal)
    validate_export_reexports_v3(candidate, seal)
    validate_reexport_observations_v3(candidate, seal)
    validate_direct_export_observations_v3(candidate, seal)
    validate_string_export_observations_v3(candidate, seal)
    validate_public_export_bindings_v3(candidate, seal)
    validate_public_export_coverage_v3(candidate, seal)
    validate_string_export_diagnostics_v3(candidate, seal)
    payload = candidate.semantic_payload()
    try:
        actual = validate_model(
            payload["model"],
            max_model_records=candidate.request_frame().record()["limits"]["max_total_array_items"],
        )
        outcome = derive_pre_budget_outcome(payload["proof"], payload["model"])
    except AssertionError as error:
        raise SemanticCandidateInvalidErrorV3("model_proof") from error
    locality = derive_post_acquisition_locality_v3(candidate, seal)
    context = canonical_run_context(**payload["run_context"])
    target_failure = validate_target_proof_v3(candidate)
    # Mint the normal seam only after the full proof/export/target/locality base.
    # Its cardinality/partition rules are unchanged and are not target exceptions.
    seam = retain_source_inventory_seam_v3(candidate, seal, assets)
    if target_failure is not None:
        return CoreValidationResultV3(
            seam,
            target_failure_decision(target_failure, context),
            locality,
            {"model_records": None, "entity_budget": None},
        )
    published, proof_only, accounted = response_model_record_counts(
        payload["model"], payload["proof"]
    )
    if accounted > candidate.request_frame().record()["limits"]["max_model_records"]:
        raise ModelRecordLimitError(accounted)
    measurements: dict[str, Any] = {
        "model_records": {
            "published": published,
            "proof_only": proof_only,
            "accounted": accounted,
            "limit": candidate.request_frame().record()["limits"]["max_model_records"],
        },
        "entity_budget": None,
    }
    public_modules = {row["id"] for row in payload["model"]["modules"]}
    export_gate = export_failure_decision(
        {
            key: [row for row in payload["proof"][key] if row["owner_module_id"] in public_modules]
            for key in ("export_observations", "export_reexport_witness")
        },
        context,
    )
    if export_gate is not None:
        return CoreValidationResultV3(seam, export_gate, locality, measurements)
    if not locality["localized"]:
        return CoreValidationResultV3(
            seam,
            {
                "actual": None,
                "resolved": context["budget_resolved"],
                "allowed": False,
                "payload_available": False,
                "original_outcome": "payload_unavailable",
                "outcome": "payload_unavailable",
                "diagnostic_code": "CSV-NEXT-SOURCE-003",
                "run_context": context,
                "requested_formats": context["requested_formats"],
                "budget_requested": context["budget_requested"],
                "budget_source": context["budget_source"],
                "stdout_selector": context["stdout_selector"],
                "artifact_paths": [],
            },
            locality,
            measurements,
        )
    gate = entity_budget_gate(
        actual,
        original_outcome=outcome,
        run_context=context,
    )
    measurements["entity_budget"] = {"actual": actual, "limit": context["budget_resolved"]}
    return CoreValidationResultV3(seam, gate, locality, measurements)


def validate_semantic_decision_v3(decision: "ValidatedSemanticDecisionV3") -> None:
    from tests.contracts.next_semantic_core_v3_reference import ValidatedSemanticDecisionV3

    if type(decision) is not ValidatedSemanticDecisionV3:
        raise TypeError("semantic validation requires a v3 Core decision owner")
    expected = validate_semantic_candidate_v3(
        decision.transport_candidate(), decision.source_seal(), decision.execution_assets()
    )
    if (
        canonical_json_bytes(decision.gate()) != canonical_json_bytes(expected.gate)
        or canonical_json_bytes(decision.locality()) != canonical_json_bytes(expected.locality)
        or canonical_json_bytes(decision.measurements())
        != canonical_json_bytes(expected.measurements)
    ):
        raise ValueError("Core gate/locality differs from its retained owners")
    seam = decision.source_inventory_seam()
    validate_source_inventory_seam_v3(seam)
    if (
        seam.transport_candidate() is not decision.transport_candidate()
        or seam.source_seal() is not decision.source_seal()
        or seam.execution_assets() is not decision.execution_assets()
    ):
        raise ValueError("Core source inventory differs from its retained owners")
    validate_compatibility_descriptor_v3(
        decision.compatibility_descriptor(), decision.transport_candidate()
    )


def validate_rejected_semantic_decision_v3(decision: "RejectedSemanticDecisionV3") -> None:
    from tests.contracts.next_semantic_core_v3_reference import RejectedSemanticDecisionV3

    if type(decision) is not RejectedSemanticDecisionV3:
        raise TypeError("rejection validation requires a rejected v3 Core owner")
    try:
        validate_semantic_candidate_v3(
            decision.transport_candidate(), decision.source_seal(), decision.execution_assets()
        )
    except SemanticCandidateInvalidErrorV3 as error:
        expected: dict[str, Any] = {
            "stage": "response_validation",
            "diagnostic_code": "CSV-NEXT-PROTOCOL-001",
            "reason": error.reason,
            "model_records": None,
        }
    except ModelRecordLimitError as error:
        expected = {
            "stage": "model_validation",
            "diagnostic_code": "CSV-NEXT-LIMIT-005",
            "reason": "max_model_records",
            "model_records": error.measured,
        }
    else:
        raise ValueError("Core rejection requires an actually invalid or over-limit candidate")
    if canonical_json_bytes(decision.failure()) != canonical_json_bytes(expected):
        raise ValueError("Core failure metadata differs from its retained candidate")
