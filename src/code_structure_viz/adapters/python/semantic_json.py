from __future__ import annotations

from code_structure_viz.adapters.python.model import (
    CoverageFrontier,
    FailedSourceFile,
    MethodSignature,
    Parameter,
    PythonClassEntity,
    PythonCoverage,
    PythonMember,
    PythonRelation,
    PythonSnapshot,
    entity_sort_key,
    failed_source_sort_key,
    frontier_sort_key,
    member_sort_key,
    relation_sort_key,
)
from code_structure_viz.core.diagnostics import canonical_diagnostics
from code_structure_viz.semantic.canonical_json import encode_canonical_json
from code_structure_viz.source.source_view import SourceView
from code_structure_viz.source.targets import (
    ClassTarget,
    ModuleTarget,
    PathTarget,
    TargetSpec,
    target_sort_key,
)


def render_semantic_snapshot(
    snapshot: PythonSnapshot,
    source_view: SourceView,
    targets: tuple[TargetSpec, ...],
    upstream_depth: int,
    downstream_depth: int,
) -> bytes:
    if snapshot.coverage.selected_entities != len(snapshot.entities):
        raise ValueError("semantic coverage entity count is inconsistent")
    value: dict[str, object] = {
        "type": "semantic_snapshot",
        "schema": "code-structure-viz.semantic/v1",
        "domain": "python",
        "document_kind": "snapshot",
        "status": "incomplete" if snapshot.partial_safe else "complete",
    }
    if snapshot.partial_safe:
        value["incomplete_kind"] = "partial_safe"
    value.update(
        {
            "source": {
                "schema": source_view.schema,
                "kind": source_view.kind,
                "head_commit": source_view.head_commit,
                "fingerprint": source_view.fingerprint,
                "file_count": len(source_view.files),
            },
            "request": {
                "targets": [target_value(item) for item in sorted(targets, key=target_sort_key)],
                "upstream_depth": upstream_depth,
                "downstream_depth": downstream_depth,
            },
            "coverage": coverage_value(snapshot.coverage),
            "entities": [
                _entity_value(item) for item in sorted(snapshot.entities, key=entity_sort_key)
            ],
            "members": [
                _member_value(item) for item in sorted(snapshot.members, key=member_sort_key)
            ],
            "relations": [
                _relation_value(item) for item in sorted(snapshot.relations, key=relation_sort_key)
            ],
            "diagnostics": [
                item.to_json_value() for item in canonical_diagnostics(snapshot.diagnostics)
            ],
        }
    )
    return encode_canonical_json(value)


def target_value(value: TargetSpec) -> dict[str, str]:
    if isinstance(value, PathTarget):
        return {"kind": "path", "value": value.value.as_posix()}
    if isinstance(value, ModuleTarget):
        return {"kind": "module", "value": value.value}
    assert isinstance(value, ClassTarget)
    return {"kind": "class", "value": value.raw}


def _failed_file_value(value: FailedSourceFile) -> dict[str, object]:
    return {
        "path": value.path.as_posix(),
        "stage": value.stage.value,
        "diagnostic_code": value.diagnostic_code.value,
    }


def _frontier_value(value: CoverageFrontier) -> dict[str, object]:
    return {
        "direction": value.direction.value,
        "kind": value.kind.value,
        "reference": value.reference,
        "reason": value.reason.value,
    }


def coverage_value(value: PythonCoverage) -> dict[str, object]:
    return {
        "candidate_files": value.candidate_files,
        "parsed_files": value.parsed_files,
        "failed_files": [
            _failed_file_value(item)
            for item in sorted(value.failed_files, key=failed_source_sort_key)
        ],
        "selected_modules": sorted(value.selected_modules, key=lambda item: item.encode("utf-8")),
        "selected_entities": value.selected_entities,
        "frontier": [
            _frontier_value(item) for item in sorted(set(value.frontier), key=frontier_sort_key)
        ],
    }


def _range_value(start_line: int, end_line: int) -> dict[str, int]:
    return {"start_line": start_line, "end_line": end_line}


def _decorator_value(name: str, called: bool) -> dict[str, object]:
    return {"name": name, "called": called}


def _entity_value(value: PythonClassEntity) -> dict[str, object]:
    return {
        "id": value.id,
        "kind": value.kind,
        "module": value.module,
        "qualified_name": value.qualified_name,
        "name": value.name,
        "path": value.path.as_posix(),
        "range": _range_value(value.range.start_line, value.range.end_line),
        "decorators": [_decorator_value(item.name, item.called) for item in value.decorators],
    }


def _parameter_value(value: Parameter) -> dict[str, object]:
    return {
        "name": value.name,
        "kind": value.kind.value,
        "annotation": value.annotation,
        "has_default": value.has_default,
    }


def _signature_value(value: MethodSignature) -> dict[str, object]:
    return {
        "async": value.async_,
        "parameters": [_parameter_value(item) for item in value.parameters],
        "returns": value.returns,
    }


def _member_value(value: PythonMember) -> dict[str, object]:
    return {
        "id": value.id,
        "owner_id": value.owner_id,
        "kind": value.kind.value,
        "name": value.name,
        "scope": value.scope.value if value.scope is not None else None,
        "property_role": (value.property_role.value if value.property_role is not None else None),
        "method_kind": value.method_kind.value if value.method_kind is not None else None,
        "annotation": value.annotation,
        "signature": _signature_value(value.signature) if value.signature is not None else None,
        "decorators": [_decorator_value(item.name, item.called) for item in value.decorators],
        "range": _range_value(value.range.start_line, value.range.end_line),
    }


def _relation_value(value: PythonRelation) -> dict[str, object]:
    return {
        "id": value.id,
        "kind": value.kind.value,
        "source_id": value.source_id,
        "target": {
            "resolution": value.target.resolution.value,
            "kind": value.target.kind.value,
            "id": value.target.id,
            "name": value.target.name,
        },
        "via_member_id": value.via_member_id,
        "annotation": value.annotation,
        "range": _range_value(value.range.start_line, value.range.end_line),
    }
