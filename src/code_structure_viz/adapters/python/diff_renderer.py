from __future__ import annotations

from code_structure_viz.adapters.python.plantuml import escape_plantuml_text
from code_structure_viz.semantic.canonical_json import encode_canonical_json
from code_structure_viz.semantic.diff import (
    SemanticDelta,
    SemanticDiffResult,
)
from code_structure_viz.source.file_changes import FileChangeSet


def render_semantic_diff(
    result: SemanticDiffResult,
    file_changes: FileChangeSet,
) -> bytes:
    value: dict[str, object] = {
        "type": "semantic_diff",
        "schema": "code-structure-viz.semantic/v1",
        "domain": "python",
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
        "diagnostics": [item.to_json_value() for item in result.diagnostics],
    }
    return encode_canonical_json(value)


def render_plantuml_diff(result: SemanticDiffResult) -> bytes:
    lines = [
        "@startuml",
        "title Python semantic diff",
        "left to right direction",
        "skinparam classAttributeIconSize 0",
        "hide empty members",
    ]
    if result.status != "complete":
        lines.append(f'note "status: {result.status}" as N_DIFF_STATUS')

    entity_deltas = {item.identity: item for item in result.entities}
    before_entities = _entities_by_id(result.before.snapshot)
    after_entities = _entities_by_id(result.after.snapshot)
    members_by_owner: dict[str, list[SemanticDelta]] = {}
    member_owners: set[str] = set()
    for item in result.members:
        owner = _owner_id(item)
        if owner is not None:
            members_by_owner.setdefault(owner, []).append(item)
            member_owners.add(owner)

    relation_sources: set[str] = set()
    for delta in result.relations:
        for side in (delta.after, delta.before):
            if isinstance(side, dict) and isinstance(side.get("source_id"), str):
                relation_sources.add(side["source_id"])

    context_entities = {
        *result.seeds,
        *result.impact.upstream,
        *result.impact.downstream,
        *member_owners,
        *relation_sources,
    }
    rendered_entity_ids = set(entity_deltas) | context_entities
    for identity in sorted(rendered_entity_ids, key=lambda item: item.encode("utf-8")):
        entity_delta = entity_deltas.get(identity)
        value = (
            entity_delta.after
            if entity_delta is not None and entity_delta.after is not None
            else entity_delta.before
            if entity_delta is not None
            else after_entities.get(identity) or before_entities.get(identity)
        )
        if not isinstance(value, dict):
            continue
        label = str(value.get("qualified_name", value.get("name", identity)))
        status = (
            entity_delta.status.value
            if entity_delta is not None
            else "modified"
            if identity in member_owners or identity in relation_sources or identity in result.seeds
            else "unknown"
        )
        marker = _status_style(status)[0]
        color = _status_background(status)
        alias = _class_alias(identity)
        lines.append(f'  class "{_escape(marker + " " + label)}" as {alias} {color} {{')
        for member in sorted(members_by_owner.get(identity, ()), key=lambda item: item.identity):
            member_value = member.after if member.after is not None else member.before
            if isinstance(member_value, dict):
                member_marker, member_color = _status_style(member.status.value)
                lines.append(
                    _member_line(member_marker, member_color, member_value, member.identity)
                )
        lines.append("  }")

    for delta in result.members:
        if _owner_id(delta) in rendered_entity_ids:
            continue
        marker = _status_style(delta.status.value)[0]
        color = _status_background(delta.status.value)
        lines.append(
            f'  note "{_escape(marker + " member " + delta.identity)}" '
            f"as {_note_alias(delta.identity)} {color}"
        )
    for delta in result.relations:
        marker = _status_style(delta.status.value)[0]
        color = _status_background(delta.status.value)
        lines.append(
            f'  note "{_escape(marker + " relation " + delta.identity)}" '
            f"as {_note_alias('relation:' + delta.identity)} {color}"
        )

    lines.extend(
        (
            "legend right",
            "  + added (green, solid)",
            "  - removed (red, dashed)",
            "  ~ modified (yellow, solid)",
            "  → moved (blue, solid)",
            "  ? unknown (gray, dotted)",
            "endlegend",
            "@enduml",
        )
    )
    return ("\n".join(lines) + "\n").encode("utf-8")


def _owner_id(delta: SemanticDelta) -> str | None:
    for side in (delta.after, delta.before):
        if isinstance(side, dict) and isinstance(side.get("owner_id"), str):
            owner_id = side["owner_id"]
            return owner_id if isinstance(owner_id, str) else None
    return None


def _entities_by_id(snapshot: object) -> dict[str, dict[str, object]]:
    if snapshot is None:
        return {}
    entities = getattr(snapshot, "entities", ())
    return {
        entity.id: {
            "id": entity.id,
            "kind": entity.kind,
            "module": entity.module,
            "qualified_name": entity.qualified_name,
            "name": entity.name,
            "path": entity.path.as_posix(),
            "range": {
                "start_line": entity.range.start_line,
                "end_line": entity.range.end_line,
            },
            "decorators": [
                {"name": item.name, "called": item.called} for item in entity.decorators
            ],
        }
        for entity in entities
    }


def _member_line(
    marker: str,
    color: str,
    value: dict[str, object],
    fallback_identity: str,
) -> str:
    kind = str(value.get("kind", "member"))
    name = str(value.get("name", fallback_identity))
    if kind == "method":
        signature = value.get("signature")
        if isinstance(signature, dict):
            parameters = signature.get("parameters")
            if isinstance(parameters, list):
                rendered_parameters = ", ".join(
                    _parameter_text(item) for item in parameters if isinstance(item, dict)
                )
            else:
                rendered_parameters = ""
            returns = str(signature.get("returns") or "?")
            return (
                f"    {_escape(marker + ' method ' + name + '(' + rendered_parameters + ')')}"
                f" : {_escape(returns)} {color}"
            )
    annotation = str(value.get("annotation") or "?")
    return f"    {_escape(marker + ' ' + kind + ' ' + name)} : {_escape(annotation)} {color}"


def _parameter_text(value: dict[str, object]) -> str:
    name = str(value.get("name", "?"))
    annotation = str(value.get("annotation") or "?")
    return f"{name}: {annotation}"


def _status_style(status: str) -> tuple[str, str]:
    return {
        "added": ("+", "#PaleGreen"),
        "removed": ("-", "#MistyRose"),
        "modified": ("~", "#LightYellow"),
        "moved": ("→", "#LightBlue"),
        "unknown": ("?", "#LightGray"),
    }.get(status, ("?", "#LightGray"))


def _status_background(status: str) -> str:
    if status == "added":
        return "#E8F5E9"
    return _status_style(status)[1]


def _sha(value: str) -> str:
    import hashlib

    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _class_alias(value: str) -> str:
    return f"C_{_sha(value)}"


def _note_alias(value: str) -> str:
    return f"N_{_sha(value)}"


def _escape(value: str) -> str:
    return escape_plantuml_text(value)


__all__ = ["render_plantuml_diff", "render_semantic_diff"]
