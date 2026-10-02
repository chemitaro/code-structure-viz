"""Incremental v3 Core reference checks; production execution is a separate gate."""

import hashlib
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from code_structure_viz.adapters.next.source_acquisition import SourceAcquisitionSeal
from code_structure_viz.semantic.canonical_json import encode_canonical_json
from tests.contracts.next_reference_validation import (
    COLLECTIONS,
    TAINT_ORDER_INDEX,
    ModelRecordLimitError,
    NextTargetCompletenessFailure,
    _assert_canonical,
    _deduplicated_model_for_base_validation,
    _derived_taint_fixed_point,
    _export_tokens,
    _id_kind,
    _is_program_file,
    _opaque_reason_counts,
    _record_references,
    _reexport_join_key,
    _resolve_export_source_path,
    _scan_export_file,
    _string_export_resolution,
    _target_contains_export,
    _target_duplicate_module_exceptions,
    _target_missing_module_exceptions,
    _terminal_export_source_path,
    _validate_model_collections,
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
    target_completeness_failure,
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
    _record_closure_references_v3,
    full_module_owners_v3,
    resolve_discovered_v3,
    source_owner_witness_kinds_v3,
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


@dataclass(frozen=True, slots=True)
class _CoreValidationViewV3:
    """Internal data only; never a candidate, Module, or available source certificate."""

    resolved: dict[str, dict[str, Any]]
    missing_module_keys: frozenset[tuple[str, str]]
    source_paths: tuple[str, ...]
    component_only_module_ids: frozenset[str]
    model: dict[str, Any]
    cardinality_failure: NextTargetCompletenessFailure
    removed_duplicates: int


def _selected_cardinality_view_v3(
    candidate: ValidatedTransportCandidateV2,
) -> _CoreValidationViewV3 | None:
    request = candidate.request_frame().record()
    payload = candidate.semantic_payload()
    raw_model = payload["model"]
    if payload["model_digest"] != digest(raw_model):
        raise SemanticCandidateInvalidErrorV3("model_proof")
    # Classify real raw semantic occurrences plus proof-only records. Sources
    # always come from the retained parent, never the child's public projection.
    classification = {
        name: list(request[name] if name in {"projects", "files"} else raw_model[name])
        for name in COLLECTIONS
    }
    for row in payload["proof"]["discovered_records"]:
        name = row["collection"]
        if name not in {"projects", "files"} and "record" in row:
            if name == "modules" and row["record"]["kind"] != "module":
                raise SemanticCandidateInvalidErrorV3("proof_module_owner")
            classification[name].append(row["record"])
    failure = target_completeness_failure(classification, request["targets"])
    missing, component_only = _target_missing_module_exceptions(
        classification, request["targets"], failure
    )
    duplicates = _target_duplicate_module_exceptions(classification, request["targets"], failure)
    if not missing and not duplicates:
        return None
    assert failure is not None
    model = _deduplicated_model_for_base_validation(raw_model, duplicates)
    removed = len(raw_model["modules"]) - len(model["modules"])
    resolved = (
        _resolve_exception_discovery_v3(candidate, model)
        if removed
        else resolve_discovered_v3(candidate)
    )
    return _CoreValidationViewV3(
        resolved,
        frozenset(missing),
        tuple(file["path"] for file in request["files"] if _is_program_file(file)),
        frozenset(component_only),
        model,
        failure,
        removed,
    )


def _resolve_exception_discovery_v3(
    candidate: ValidatedTransportCandidateV2, model: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    """Join a unique D against a deduplicated data view, not a fake candidate."""

    request = candidate.request_frame().record()
    payload = candidate.semantic_payload()
    try:
        for name in COLLECTIONS:
            ids = [row["id"] for row in payload["model"][name]]
            assert ids == sorted(ids)
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
        resolved: dict[str, dict[str, Any]] = {}
        for row in payload["proof"]["discovered_records"]:
            name, record_id = row["collection"], row["record_id"]
            assert record_id not in resolved
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
            resolved[record_id] = {**row, "record": record}
        assert all(
            record_id in resolved and resolved[record_id]["collection"] == name
            for name in COLLECTIONS
            for record_id in public[name]
        )
        return resolved
    except (AssertionError, KeyError, TypeError) as error:
        raise SemanticCandidateInvalidErrorV3("model_proof") from error


def _resolved_for_view_v3(
    candidate: ValidatedTransportCandidateV2, view: _CoreValidationViewV3 | None
) -> dict[str, dict[str, Any]]:
    return resolve_discovered_v3(candidate) if view is None else view.resolved


def _validate_exception_dispositions_v3(
    model: dict[str, Any], proof: dict[str, Any], resolved: dict[str, dict[str, Any]]
) -> None:
    actual: dict[str, list[tuple[str, str | None]]] = {record_id: [] for record_id in resolved}
    for name in COLLECTIONS:
        for record in model[name]:
            actual[record["id"]].append(("published", None))
    for state in ("excluded", "failed"):
        for row in proof[state]:
            source = resolved.get(row["record_id"])
            if source is None or source["collection"] != row["collection"]:
                raise SemanticCandidateInvalidErrorV3("model_proof")
            actual[row["record_id"]].append((state, row["reason"]))
    for record_id, row in resolved.items():
        if len(actual[record_id]) != 1:
            raise SemanticCandidateInvalidErrorV3("model_proof")
        state, reason = actual[record_id][0]
        taints = row["taints"]
        if row["collection"] == "projects" and (taints or state != "published"):
            raise SemanticCandidateInvalidErrorV3("project_correspondence")
        if (
            (state == "published" and taints)
            or (state == "failed" and reason not in taints)
            or (
                state == "excluded"
                and (
                    (reason == "tainted" and not taints)
                    or (reason == "failed" and not taints and row["collection"] != "files")
                    or (taints and reason not in {"tainted", "failed"})
                )
            )
        ):
            raise SemanticCandidateInvalidErrorV3("model_proof")


def _validate_exception_source_view_v3(
    candidate: ValidatedTransportCandidateV2, view: _CoreValidationViewV3
) -> None:
    """Keep unrelated owner-closed partition rules without minting a normal seam."""

    request = candidate.request_frame().record()
    raw_model, proof = candidate.semantic_payload()["model"], candidate.semantic_payload()["proof"]
    model = view.model
    resolved = view.resolved
    expected_counts = {name: len(raw_model[name]) for name in COLLECTIONS}
    expected_counts.update(
        discovered=len(resolved) + view.removed_duplicates,
        published=sum(len(raw_model[name]) for name in COLLECTIONS),
        excluded=len(proof["excluded"]),
        failed=len(proof["failed"]),
        internal_entities=len(raw_model["modules"]) + len(raw_model["components"]),
    )
    if raw_model["coverage"]["counts"] != expected_counts:
        raise SemanticCandidateInvalidErrorV3("model_proof")
    public_ids = {row["id"] for name in COLLECTIONS for row in model[name]}

    def closure_references(record: dict[str, Any]) -> set[str]:
        references = _record_closure_references_v3(record)
        if record["kind"] == "component" and record["module_id"] in view.component_only_module_ids:
            # Only Component ownership may name this exact selected gap.
            # Props repository references and every other record stay closed.
            references.discard(record["module_id"])
        return references

    if any(
        not closure_references(row["record"]) <= resolved.keys() for row in resolved.values()
    ) or any(
        not closure_references(row) <= public_ids for name in COLLECTIONS for row in model[name]
    ):
        raise SemanticCandidateInvalidErrorV3("proof_references")
    _validate_exception_dispositions_v3(model, proof, resolved)
    program = {
        (file["project_id"], file["path"]): file
        for file in request["files"]
        if _is_program_file(file)
    }
    module_rows = [row for row in resolved.values() if row["collection"] == "modules"]
    owners = {
        (row["record"]["project_id"], row["record"]["path"]): row["record"] for row in module_rows
    }
    if len(owners) != len(module_rows) or set(owners) != program.keys() - view.missing_module_keys:
        raise SemanticCandidateInvalidErrorV3("proof_module_owner")
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
            or root["kind"] not in resolved[file["id"]]["taints"]
        ):
            raise SemanticCandidateInvalidErrorV3("model_proof")
        direct_roots.setdefault(file["id"], set()).add(root["kind"])
    witnessed = source_owner_witness_kinds_v3(proof, resolved)
    for file in request["files"]:
        if not set(resolved[file["id"]]["taints"]) <= direct_roots.get(file["id"], set()):
            raise SemanticCandidateInvalidErrorV3("source_inventory_partition")
        if not set(resolved[file["id"]]["taints"]) <= witnessed.get(file["id"], set()):
            raise SemanticCandidateInvalidErrorV3("model_proof")
    for module in owners.values():
        if not set(resolved[module["id"]]["taints"]) <= witnessed.get(module["id"], set()):
            raise SemanticCandidateInvalidErrorV3("source_inventory_partition")
    selected_ids = {
        record_id for row in proof["target_resolutions"] for record_id in row["record_ids"]
    }
    module_reasons = {}
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
            unknown = sum(
                row.get("target", {}).get("kind") == "unresolved" for row in model["relations"]
            )
            if (
                not unknown
                or model["coverage"]["unknown_relation_count"] != unknown
                or not any(
                    row["code"] == "CSV-NEXT-UNSUPPORTED-001"
                    and row["outcome"] == "complete"
                    and (row["symbol_ref"] == module["id"] or row["path_ref"] == module["path"])
                    for row in model["diagnostics"]
                )
            ):
                raise SemanticCandidateInvalidErrorV3("source_inventory_partition")
        elif (
            not request["targets"]
            or module["id"] in selected_ids
            or any(
                target == "path:."
                or module["path"] == target.removeprefix("path:")
                or module["path"].startswith(target.removeprefix("path:").rstrip("/") + "/")
                for target in request["targets"]
            )
        ):
            raise SemanticCandidateInvalidErrorV3("source_inventory_partition")
        module_reasons[module["id"]] = reason
    eligible = {
        module["id"]
        for key, module in owners.items()
        if not resolved[program[key]["id"]]["taints"]
        and not resolved[module["id"]]["taints"]
        and module["id"] not in module_reasons
    }
    if {row["id"] for row in model["modules"]} != eligible:
        raise SemanticCandidateInvalidErrorV3("source_inventory_partition")
    dispositions = []
    for file in request["files"]:
        file_id = file["id"]
        module = owners.get((file["project_id"], file["path"]))
        if file_id in direct_roots:
            state, reason = "failed", min(direct_roots[file_id], key=TAINT_ORDER_INDEX.__getitem__)
        elif resolved[file_id]["taints"]:
            state, reason = "excluded", "tainted"
        elif module is not None and module["id"] not in eligible:
            state = "excluded"
            reason = "failed" if resolved[module["id"]]["taints"] else module_reasons[module["id"]]
        else:
            state, reason = "published", None
        dispositions.append((file_id, state, reason))
    actual = [(row["id"], "published", None) for row in model["files"]]
    actual.extend(
        (row["record_id"], state, row["reason"])
        for state in ("excluded", "failed")
        for row in proof[state]
        if row["collection"] == "files"
    )
    safe = {record_id for record_id, state, _reason in dispositions if state == "published"}
    expected_files = [
        {key: value for key, value in file.items() if key != "content_base64"}
        for file in sorted(request["files"], key=lambda row: row["id"])
        if file["id"] in safe
    ]
    expected_projects = [
        {
            **project,
            "file_ids": [record_id for record_id in project["file_ids"] if record_id in safe],
        }
        for project in sorted(request["projects"], key=lambda row: row["id"])
    ]
    if sorted(actual) != sorted(dispositions) or canonical_json_bytes(
        model["files"]
    ) != canonical_json_bytes(expected_files):
        raise SemanticCandidateInvalidErrorV3("source_inventory_partition")
    if canonical_json_bytes(model["projects"]) != canonical_json_bytes(expected_projects):
        raise SemanticCandidateInvalidErrorV3("project_correspondence")


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


def validate_full_taint_proof_v3(
    candidate: ValidatedTransportCandidateV2, view: _CoreValidationViewV3 | None = None
) -> None:
    """Preserve mandatory roots/causal rules and the exact typed fixed point."""

    resolved = _resolved_for_view_v3(candidate, view)
    discovered: dict[str, dict[str, dict[str, Any]]] = {name: {} for name in COLLECTIONS}
    for record_id, row in resolved.items():
        discovered[row["collection"]][record_id] = row
    try:
        _derived_taint_fixed_point(candidate.semantic_payload()["proof"], discovered)
    except AssertionError as error:
        raise SemanticCandidateInvalidErrorV3("model_proof") from error


def validate_proof_coverage_v3(
    candidate: ValidatedTransportCandidateV2, view: _CoreValidationViewV3 | None = None
) -> None:
    payload = candidate.semantic_payload()
    resolved = _resolved_for_view_v3(candidate, view)
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


def validate_full_model_semantics_v3(
    candidate: ValidatedTransportCandidateV2, view: _CoreValidationViewV3 | None = None
) -> None:
    """Apply unchanged record/Props grammar to acquired and proof-only records."""

    resolved = _resolved_for_view_v3(candidate, view)
    public_model = candidate.semantic_payload()["model"] if view is None else view.model
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
            allowed_missing_module_keys=set(view.missing_module_keys) if view is not None else None,
            allowed_missing_module_ids=set(view.component_only_module_ids)
            if view is not None
            else None,
        )
    except AssertionError as error:
        raise SemanticCandidateInvalidErrorV3("model_proof") from error


def validate_export_syntax_v3(
    candidate: ValidatedTransportCandidateV2,
    seal: SourceAcquisitionSeal,
    view: _CoreValidationViewV3 | None = None,
) -> None:
    """Full-D syntax comes only from the same retained frozen source bytes."""

    resolved = _resolved_for_view_v3(candidate, view)
    content_by_path = {str(file.path): file.content for file in seal.source_view.files}
    expected = []
    if view is not None:
        # Source-only slots have no semantic owner/observation. They still enter
        # the source-derived reexport graph below and can never be skipped there.
        for path in view.source_paths:
            _scan_export_file(path, content_by_path[path])
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
    candidate: ValidatedTransportCandidateV2,
    seal: SourceAcquisitionSeal,
    view: _CoreValidationViewV3 | None = None,
) -> list[dict[str, Any]]:
    """Recompute a graph from full-D declarations and same-seal syntax only."""

    resolved = _resolved_for_view_v3(candidate, view)
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
    paths = view.source_paths if view is not None else tuple(modules)
    syntax_rows = [
        syntax for path in paths for syntax in _scan_export_file(path, content_by_path[path])
    ]
    direct_tables = []
    for path in paths:
        module = modules.get(path)
        exports = []
        for syntax in syntax_rows:
            if (
                syntax["owner_file_path"] != path
                or syntax["reexport"]
                or syntax["syntax_kind"] == "string_export"
            ):
                continue
            declaration_key = syntax["imported_name"] or syntax["exported_name"]
            component = (
                components.get((module["id"], declaration_key)) if module is not None else None
            )
            if syntax["role"] == "type":
                resolution, target = "type", None
            elif component is not None:
                resolution, target = "component", component["declaration_key"]
            elif _primitive_const_v3(declaration_key, content_by_path[path]):
                resolution, target = "value", None
            elif module is None:
                resolution, target = "unknown", None
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
        if witness["owner_file_path"] not in modules:
            continue
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
    candidate: ValidatedTransportCandidateV2,
    seal: SourceAcquisitionSeal,
    view: _CoreValidationViewV3 | None = None,
) -> None:
    expected = derive_reexport_witnesses_v3(candidate, seal, view)
    observed = candidate.semantic_payload()["proof"]["export_reexport_witness"]
    if observed != expected:
        raise SemanticCandidateInvalidErrorV3("model_proof")


def validate_reexport_observations_v3(
    candidate: ValidatedTransportCandidateV2,
    seal: SourceAcquisitionSeal,
    view: _CoreValidationViewV3 | None = None,
) -> None:
    witnesses = derive_reexport_witnesses_v3(candidate, seal, view)
    modules = {
        row["record"]["path"]: row["record"]
        for row in _resolved_for_view_v3(candidate, view).values()
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
    candidate: ValidatedTransportCandidateV2,
    seal: SourceAcquisitionSeal,
    view: _CoreValidationViewV3 | None = None,
) -> None:
    resolved = _resolved_for_view_v3(candidate, view)
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
    candidate: ValidatedTransportCandidateV2,
    seal: SourceAcquisitionSeal,
    view: _CoreValidationViewV3 | None = None,
) -> list[dict[str, Any]]:
    resolved = _resolved_for_view_v3(candidate, view)
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
    candidate: ValidatedTransportCandidateV2,
    seal: SourceAcquisitionSeal,
    view: _CoreValidationViewV3 | None = None,
) -> None:
    observed = [
        row
        for row in candidate.semantic_payload()["proof"]["export_observations"]
        if row["syntax_kind"] == "string_export"
    ]
    if observed != derive_string_export_observations_v3(candidate, seal, view):
        raise SemanticCandidateInvalidErrorV3("model_proof")


def derive_public_export_bindings_v3(
    candidate: ValidatedTransportCandidateV2,
    seal: SourceAcquisitionSeal,
    view: _CoreValidationViewV3 | None = None,
) -> list[dict[str, Any]]:
    """Project only source-derived component exports with both public owners."""

    payload = candidate.semantic_payload()
    public_modules = {row["id"] for row in payload["model"]["modules"]}
    public_components = {row["id"] for row in payload["model"]["components"]}
    resolved = _resolved_for_view_v3(candidate, view)
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
    for witness in derive_reexport_witnesses_v3(candidate, seal, view):
        if witness["resolution"] == "component":
            add_binding(
                witness["owner_module_id"],
                witness["exported_name"],
                witness["target_declaration_id"],
                reexport=True,
            )
    return sorted(bindings.values(), key=lambda binding: binding["id"])


def validate_public_export_bindings_v3(
    candidate: ValidatedTransportCandidateV2,
    seal: SourceAcquisitionSeal,
    view: _CoreValidationViewV3 | None = None,
) -> None:
    expected = derive_public_export_bindings_v3(candidate, seal, view)
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
    candidate: ValidatedTransportCandidateV2,
    seal: SourceAcquisitionSeal,
    view: _CoreValidationViewV3 | None = None,
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
        for row in derive_reexport_witnesses_v3(candidate, seal, view)
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
    candidate: ValidatedTransportCandidateV2,
    seal: SourceAcquisitionSeal,
    view: _CoreValidationViewV3 | None = None,
) -> None:
    model = candidate.semantic_payload()["model"]
    public_modules = {row["id"] for row in model["modules"]}
    observations = derive_string_export_observations_v3(candidate, seal, view)
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
    candidate: ValidatedTransportCandidateV2,
    seal: SourceAcquisitionSeal,
    view: _CoreValidationViewV3 | None = None,
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
    resolved = _resolved_for_view_v3(candidate, view)
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
    view: _CoreValidationViewV3 | None = None,
) -> NextTargetCompletenessFailure | None:
    payload = candidate.semantic_payload()
    resolved = _resolved_for_view_v3(candidate, view)
    full_model = {
        name: sorted(
            [row["record"] for row in resolved.values() if row["collection"] == name],
            key=lambda row: row["id"],
        )
        for name in COLLECTIONS
    }
    public_ids = {row["id"] for name in COLLECTIONS for row in payload["model"][name]}
    targets = candidate.request_frame().record()["targets"]
    if view is not None:
        targets = targets or [
            f"path:{file['path']}" for file in full_model["files"] if _is_program_file(file)
        ]
        # The old aggregate preflight leaves safe rows empty when another
        # target has a cardinality failure. Resolve each independent target.
        resolutions = [
            row
            for target in targets
            for row in resolve_target_resolutions(
                [target], full_model, unavailable_record_ids=resolved.keys() - public_ids
            )
        ]
    else:
        resolutions = resolve_target_resolutions(
            targets, full_model, unavailable_record_ids=resolved.keys() - public_ids
        )
    expected = string_export_target_resolutions(
        resolutions,
        payload["proof"]["export_observations"],
    )
    if view is not None:
        failures = {row["target_key"]: row["reason"] for row in view.cardinality_failure.failures}
        expected = [
            {
                "target_key": row["target_key"],
                "status": "failed",
                "record_ids": [],
                "reason": failures[row["target_key"]],
            }
            if row["target_key"] in failures
            else row
            for row in expected
        ]
        expected.sort(key=canonical_json_bytes)
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
    source_inventory: ValidatedSourceInventorySeamV3 | None
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
    view = _selected_cardinality_view_v3(candidate)
    if view is None:
        full_module_owners_v3(candidate)
    validate_full_model_semantics_v3(candidate, view)
    validate_full_taint_proof_v3(candidate, view)
    validate_proof_coverage_v3(candidate, view)
    validate_export_syntax_v3(candidate, seal, view)
    validate_export_reexports_v3(candidate, seal, view)
    validate_reexport_observations_v3(candidate, seal, view)
    validate_direct_export_observations_v3(candidate, seal, view)
    validate_string_export_observations_v3(candidate, seal, view)
    validate_public_export_bindings_v3(candidate, seal, view)
    validate_public_export_coverage_v3(candidate, seal, view)
    validate_string_export_diagnostics_v3(candidate, seal, view)
    payload = candidate.semantic_payload()
    try:
        actual = validate_model(
            payload["model"] if view is None else view.model,
            max_model_records=candidate.request_frame().record()["limits"]["max_total_array_items"],
            allowed_missing_module_keys=set(view.missing_module_keys) if view is not None else None,
            allowed_missing_module_ids=set(view.component_only_module_ids)
            if view is not None
            else None,
        )
        outcome = derive_pre_budget_outcome(payload["proof"], payload["model"])
    except AssertionError as error:
        raise SemanticCandidateInvalidErrorV3("model_proof") from error
    locality = derive_post_acquisition_locality_v3(candidate, seal, view)
    context = canonical_run_context(**payload["run_context"])
    target_failure = validate_target_proof_v3(candidate, view)
    # Mint the normal seam only after the full proof/export/target/locality base.
    # Its cardinality/partition rules are unchanged and are not target exceptions.
    if view is not None:
        _validate_exception_source_view_v3(candidate, view)
        if target_failure is None:
            raise SemanticCandidateInvalidErrorV3("model_proof")
        seam = None
    else:
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
    if expected.source_inventory is None:
        if seam is not None:
            raise ValueError("exceptional Core cannot retain an available source inventory")
    else:
        if seam is None:
            raise ValueError("normal Core requires its retained source inventory")
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
