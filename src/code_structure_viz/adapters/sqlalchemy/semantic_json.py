from __future__ import annotations

from typing import TYPE_CHECKING

from code_structure_viz.adapters.sqlalchemy.model import (
    RedactedExpression,
    SqlAlchemyAssociationTableRow,
    SqlAlchemyCheckRow,
    SqlAlchemyColumnRow,
    SqlAlchemyCoverage,
    SqlAlchemyCoverageFrontier,
    SqlAlchemyFailedSource,
    SqlAlchemyForeignKeyRow,
    SqlAlchemyIndexRow,
    SqlAlchemyIndexTerm,
    SqlAlchemyInheritanceRow,
    SqlAlchemyMappingSource,
    SqlAlchemyPrimaryKeyRow,
    SqlAlchemyRelation,
    SqlAlchemyRelationshipRow,
    SqlAlchemyRelationTarget,
    SqlAlchemyRow,
    SqlAlchemySnapshot,
    SqlAlchemySourceLocation,
    SqlAlchemyTable,
    SqlAlchemyTypeDescriptor,
    SqlAlchemyUniqueRow,
)
from code_structure_viz.semantic.canonical_json import encode_canonical_json
from code_structure_viz.source.file_changes import FileChangeSet
from code_structure_viz.source.source_view import SourceView
from code_structure_viz.source.targets import (
    ClassTarget,
    ModuleTarget,
    PathTarget,
    TargetSpec,
    target_sort_key,
)

if TYPE_CHECKING:
    from code_structure_viz.adapters.sqlalchemy.diff import SqlAlchemyDiffResult


def render_semantic_snapshot(
    snapshot: SqlAlchemySnapshot,
    source_view: SourceView,
    targets: tuple[TargetSpec, ...],
    upstream_depth: int,
    downstream_depth: int,
) -> bytes:
    if not isinstance(snapshot, SqlAlchemySnapshot):
        raise ValueError("SQLAlchemy semantic renderer requires a SQLAlchemy snapshot")
    value: dict[str, object] = {
        "type": "semantic_snapshot",
        "schema": "code-structure-viz.semantic/v1",
        "domain": "sqlalchemy",
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
            "entities": [_table_value(item) for item in snapshot.entities],
            "members": [_row_value(item) for item in snapshot.members],
            "relations": [_relation_value(item) for item in snapshot.relations],
            "diagnostics": [item.to_json_value() for item in snapshot.diagnostics],
        }
    )
    return encode_canonical_json(value)


def render_sqlalchemy_diff(result: SqlAlchemyDiffResult, file_changes: FileChangeSet) -> bytes:
    """Render one SQLAlchemy semantic diff using the existing safe projections."""
    value = {
        "type": "semantic_diff",
        "schema": "code-structure-viz.semantic/v1",
        "domain": "sqlalchemy",
        "document_kind": "diff",
        "status": result.status,
        "before": result.before.to_json_value(),
        "after": result.after.to_json_value(),
        "before_snapshot_sha256": result.before.digest,
        "after_snapshot_sha256": result.after.digest,
        "file_change_set": file_changes.to_json_value(),
        "semantic_change_set": {
            "entities": [item.to_json_value() for item in result.entities],
            "members": [item.to_json_value() for item in result.members],
            "relations": [item.to_json_value() for item in result.relations],
            "seeds": list(result.seeds),
            "impact": result.impact.to_json_value(),
            "matching": list(result.matching),
        },
        "diagnostics": [],
    }
    return encode_canonical_json(value)


class SqlAlchemySemanticJsonRenderer:
    """Render selected SQLAlchemy semantic v1 snapshot bytes."""

    def __init__(
        self,
        *,
        source_view: SourceView,
        targets: tuple[TargetSpec, ...],
        upstream_depth: int,
        downstream_depth: int,
    ) -> None:
        self._source_view = source_view
        self._targets = targets
        self._upstream_depth = upstream_depth
        self._downstream_depth = downstream_depth

    def render(self, snapshot: SqlAlchemySnapshot) -> bytes:
        return render_semantic_snapshot(
            snapshot,
            self._source_view,
            self._targets,
            self._upstream_depth,
            self._downstream_depth,
        )


def target_value(value: TargetSpec) -> dict[str, str]:
    if isinstance(value, PathTarget):
        return {"kind": "path", "value": value.value.as_posix()}
    if isinstance(value, ModuleTarget):
        return {"kind": "module", "value": value.value}
    assert isinstance(value, ClassTarget)
    return {"kind": "class", "value": value.raw}


def _failed_file_value(value: SqlAlchemyFailedSource) -> dict[str, object]:
    return {
        "path": value.path,
        "stage": value.stage.value,
        "diagnostic_code": value.diagnostic_code.value,
    }


def _frontier_value(value: SqlAlchemyCoverageFrontier) -> dict[str, object]:
    return {
        "direction": value.direction.value,
        "kind": value.kind.value,
        "reference": value.reference,
        "reason": value.reason.value,
    }


def coverage_value(value: SqlAlchemyCoverage) -> dict[str, object]:
    return {
        "candidate_files": value.candidate_files,
        "parsed_files": value.parsed_files,
        "failed_files": [_failed_file_value(item) for item in value.failed_files],
        "evidence_files": list(value.evidence_files),
        "selected_modules": list(value.selected_modules),
        "mapped_classes": value.mapped_classes,
        "association_tables": value.association_tables,
        "selected_entities": value.selected_entities,
        "unknown_declarations": value.unknown_declarations,
        "frontier": [_frontier_value(item) for item in value.frontier],
        "redaction": {
            "rule_version": value.redaction.rule_version,
            "redacted_values": value.redaction.redacted_values,
        },
    }


def _source_value(value: SqlAlchemySourceLocation) -> dict[str, object]:
    return {
        "path": value.path,
        "range": {
            "start_line": value.range.start_line,
            "end_line": value.range.end_line,
        },
    }


def _redacted_value(value: RedactedExpression) -> dict[str, object]:
    return {
        "present": value.present,
        "category": value.category.value,
        "redacted": value.redacted,
    }


def _type_value(value: SqlAlchemyTypeDescriptor) -> dict[str, object]:
    return {
        "category": value.category.value,
        "name": value.name,
        "parameters": _redacted_value(value.parameters),
    }


def _index_term_value(value: SqlAlchemyIndexTerm) -> dict[str, object]:
    return {
        "kind": value.kind.value,
        "column_name": value.column_name,
        "expression": _redacted_value(value.expression),
    }


def _target_value(value: SqlAlchemyRelationTarget) -> dict[str, object]:
    return {
        "resolution": value.resolution.value,
        "kind": value.kind.value,
        "id": value.id,
        "schema_name": value.schema_name,
        "table_name": value.table_name,
        "symbol": value.symbol,
        "display_name": value.display_name,
    }


def _mapping_source_value(value: SqlAlchemyMappingSource) -> dict[str, object]:
    return {
        "kind": value.kind.value,
        "module": value.module,
        "symbol": value.symbol,
        "source": _source_value(value.source),
    }


def _table_value(value: SqlAlchemyTable) -> dict[str, object]:
    return {
        "id": value.id,
        "kind": value.kind,
        "schema_name": value.schema_name,
        "name": value.name,
        "display_name": value.display_name,
        "mapping_kind": value.mapping_kind.value,
        "mapping_sources": [_mapping_source_value(item) for item in value.mapping_sources],
    }


def _row_prefix(value: SqlAlchemyRow) -> dict[str, object]:
    return {
        "id": value.id,
        "owner_id": value.owner_id,
        "kind": value.kind.value,
        "name": value.name,
        "source": _source_value(value.source),
    }


def _row_value(value: SqlAlchemyRow) -> dict[str, object]:
    result = _row_prefix(value)
    if isinstance(value, SqlAlchemyColumnRow):
        result.update(
            {
                "type": _type_value(value.type),
                "nullable": value.nullable,
                "primary_key": value.primary_key,
                "unique": value.unique,
                "index": value.index,
                "default": _redacted_value(value.default),
                "server_default": _redacted_value(value.server_default),
                "onupdate": _redacted_value(value.onupdate),
                "server_onupdate": _redacted_value(value.server_onupdate),
                "computed": _redacted_value(value.computed),
                "identity": _redacted_value(value.identity),
            }
        )
    elif isinstance(value, (SqlAlchemyPrimaryKeyRow, SqlAlchemyUniqueRow)):
        result["columns"] = list(value.columns)
    elif isinstance(value, SqlAlchemyCheckRow):
        result["expression"] = _redacted_value(value.expression)
    elif isinstance(value, SqlAlchemyIndexRow):
        result.update(
            {
                "unique": value.unique,
                "terms": [_index_term_value(item) for item in value.terms],
            }
        )
    elif isinstance(value, SqlAlchemyForeignKeyRow):
        result.update(
            {
                "local_columns": list(value.local_columns),
                "target": _target_value(value.target),
                "target_columns": list(value.target_columns),
                "ondelete": _redacted_value(value.ondelete),
                "onupdate": _redacted_value(value.onupdate),
            }
        )
    elif isinstance(value, SqlAlchemyRelationshipRow):
        result.update(
            {
                "target": _target_value(value.target),
                "cardinality": value.cardinality.value,
                "uselist": value.uselist,
                "back_populates": value.back_populates,
                "secondary": (
                    _target_value(value.secondary) if value.secondary is not None else None
                ),
                "primaryjoin": _redacted_value(value.primaryjoin),
                "secondaryjoin": _redacted_value(value.secondaryjoin),
                "order_by": _redacted_value(value.order_by),
                "foreign_keys": _redacted_value(value.foreign_keys),
            }
        )
    elif isinstance(value, SqlAlchemyInheritanceRow):
        result["target"] = _target_value(value.target)
    elif isinstance(value, SqlAlchemyAssociationTableRow):
        result.update(
            {
                "source_table": _target_value(value.source_table),
                "relationship_target": _target_value(value.relationship_target),
                "relationship_member_id": value.relationship_member_id,
            }
        )
    else:
        raise TypeError("unknown SQLAlchemy row DTO")
    return result


def _relation_value(value: SqlAlchemyRelation) -> dict[str, object]:
    return {
        "id": value.id,
        "kind": value.kind.value,
        "source_id": value.source_id,
        "target": _target_value(value.target),
        "via_member_id": value.via_member_id,
        "role": value.role,
        "source": _source_value(value.source),
    }
