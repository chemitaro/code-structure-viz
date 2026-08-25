from __future__ import annotations

import hashlib
import unicodedata
from collections.abc import Iterable

from code_structure_viz.adapters.python.model import (
    MemberKind,
    MethodKind,
    Parameter,
    ParameterKind,
    PythonClassEntity,
    PythonMember,
    PythonRelation,
    PythonSnapshot,
    RelationKind,
    TargetKind,
    TargetResolution,
    entity_sort_key,
    member_sort_key,
    relation_sort_key,
)

_RELATION_RANK = {
    RelationKind.INHERITANCE: 0,
    RelationKind.COMPOSITION: 1,
    RelationKind.TYPED_DEPENDENCY: 2,
    RelationKind.IMPORT_DEPENDENCY: 3,
}
_LEGEND = (
    "legend right",
    "  <|-- 継承",
    "  *-- 合成",
    "  ..> 型依存",
    "  package ..> package import依存",
    "endlegend",
)


def escape_plantuml_text(value: str) -> str:
    escaped: list[str] = []
    for character in unicodedata.normalize("NFC", value):
        codepoint = ord(character)
        if character == "\\":
            escaped.append("\\\\")
        elif character == '"':
            escaped.append('\\"')
        elif character == "\n":
            escaped.append("\\n")
        elif character == "\r":
            escaped.append("\\r")
        elif character == "\t":
            escaped.append("\\t")
        elif unicodedata.category(character) in {"Cc", "Cf", "Cs", "Zl", "Zp"}:
            if codepoint <= 0xFFFF:
                escaped.append(f"\\u{codepoint:04X}")
            else:
                escaped.append(f"\\U{codepoint:08X}")
        else:
            escaped.append(character)
    return "".join(escaped)


def render_plantuml(snapshot: PythonSnapshot) -> bytes:
    if snapshot.coverage.selected_entities != len(snapshot.entities):
        raise ValueError("PlantUML coverage entity count is inconsistent")
    lines = [
        "@startuml",
        "title Python structure snapshot",
        "left to right direction",
        "skinparam classAttributeIconSize 0",
        "hide empty members",
    ]
    if snapshot.partial_safe:
        lines.append(
            'note "不完全なsnapshot: 除外fileとcoverageはrun-manifest.jsonを参照" as N_INCOMPLETE'
        )

    entities = tuple(sorted(snapshot.entities, key=entity_sort_key))
    members = tuple(sorted(snapshot.members, key=member_sort_key))
    entities_by_module: dict[str, list[PythonClassEntity]] = {}
    for entity in entities:
        entities_by_module.setdefault(entity.module, []).append(entity)
    for module in sorted(snapshot.coverage.selected_modules, key=lambda item: item.encode("utf-8")):
        lines.append(f'package "{escape_plantuml_text(module)}" as {_module_alias(module)} {{')
        module_entities = entities_by_module.get(module, [])
        if not module_entities:
            lines.append(f'  note "classなし" as {_empty_module_alias(module)}')
        else:
            for entity in module_entities:
                lines.extend(_class_lines(entity, members))
        lines.append("}")

    lines.extend(_relation_lines(snapshot.relations))
    lines.extend(_LEGEND)
    lines.append("@enduml")
    return ("\n".join(lines) + "\n").encode("utf-8")


class PythonPlantUmlRenderer:
    """Render Python PlantUML v1 bytes."""

    def render(self, snapshot: PythonSnapshot) -> bytes:
        return render_plantuml(snapshot)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _module_alias(module: str) -> str:
    return f"M_{_sha256(f'python:module:{module}')}"


def _class_alias(entity_id: str) -> str:
    return f"C_{_sha256(entity_id)}"


def _empty_module_alias(module: str) -> str:
    return f"N_EMPTY_{_sha256(f'python:module-empty:{module}')}"


def _class_lines(entity: PythonClassEntity, members: tuple[PythonMember, ...]) -> tuple[str, ...]:
    lines = [
        f'  class "{escape_plantuml_text(entity.qualified_name)}" as {_class_alias(entity.id)} {{'
    ]
    lines.extend(_member_line(item) for item in members if item.owner_id == entity.id)
    lines.append("  }")
    return tuple(lines)


def _member_line(member: PythonMember) -> str:
    name = escape_plantuml_text(member.name)
    annotation = escape_plantuml_text(member.annotation or "?")
    if member.kind is MemberKind.FIELD:
        return f"    field {name} : {annotation}"
    if member.kind is MemberKind.PROPERTY:
        assert member.property_role is not None
        return f"    property {name}({member.property_role.value}) : {annotation}"
    assert member.signature is not None
    parameters = _display_parameters(member)
    returns = escape_plantuml_text(member.signature.returns or "?")
    return f"    method {name}({', '.join(parameters)}) : {returns}"


def _display_parameters(member: PythonMember) -> tuple[str, ...]:
    assert member.signature is not None
    parameters = list(member.signature.parameters)
    expected_receiver: str | None
    if member.kind is MemberKind.PROPERTY:
        expected_receiver = None
        if parameters and parameters[0].name in {"self", "cls"}:
            expected_receiver = parameters[0].name
    elif member.method_kind is MethodKind.INSTANCE:
        expected_receiver = "self"
    elif member.method_kind is MethodKind.CLASS:
        expected_receiver = "cls"
    else:
        expected_receiver = None
    if (
        expected_receiver is not None
        and parameters
        and parameters[0].name == expected_receiver
        and parameters[0].kind
        in {ParameterKind.POSITIONAL_ONLY, ParameterKind.POSITIONAL_OR_KEYWORD}
    ):
        parameters.pop(0)

    tokens: list[str] = []
    has_var_positional = False
    inserted_keyword_marker = False
    for index, parameter in enumerate(parameters):
        if (
            parameter.kind is ParameterKind.KEYWORD_ONLY
            and not has_var_positional
            and not inserted_keyword_marker
        ):
            tokens.append("*")
            inserted_keyword_marker = True
        tokens.append(_parameter_token(parameter))
        if parameter.kind is ParameterKind.VAR_POSITIONAL:
            has_var_positional = True
        if parameter.kind is ParameterKind.POSITIONAL_ONLY and (
            index + 1 == len(parameters)
            or parameters[index + 1].kind is not ParameterKind.POSITIONAL_ONLY
        ):
            tokens.append("/")
    return tuple(tokens)


def _parameter_token(parameter: Parameter) -> str:
    name = escape_plantuml_text(parameter.name)
    annotation = escape_plantuml_text(parameter.annotation or "?")
    if parameter.kind is ParameterKind.VAR_POSITIONAL:
        return f"*{name}: {annotation}"
    if parameter.kind is ParameterKind.VAR_KEYWORD:
        return f"**{name}: {annotation}"
    default = " = …" if parameter.has_default else ""
    return f"{name}: {annotation}{default}"


def _relation_lines(relations: Iterable[PythonRelation]) -> tuple[str, ...]:
    visual: dict[tuple[object, ...], tuple[PythonRelation, str]] = {}
    for relation in sorted(relations, key=relation_sort_key):
        if relation.target.resolution is not TargetResolution.INTERNAL:
            continue
        line_parts = _relation_line_parts(relation)
        if line_parts is None:
            continue
        source_alias, arrow, target_alias, label = line_parts
        key = (
            _RELATION_RANK[relation.kind],
            source_alias,
            target_alias,
            label.encode("utf-8"),
        )
        visual.setdefault(
            key,
            (relation, f"{source_alias} {arrow} {target_alias} : {label}"),
        )
    return tuple(item[1] for item in visual.values())


def _relation_line_parts(
    relation: PythonRelation,
) -> tuple[str, str, str, str] | None:
    target_id = relation.target.id
    if target_id is None:
        return None
    if relation.kind is RelationKind.IMPORT_DEPENDENCY:
        return (
            _module_alias(relation.source_id.removeprefix("python:module:")),
            "..>",
            _module_alias(target_id.removeprefix("python:module:")),
            "import依存",
        )
    source_alias = _class_alias(relation.source_id)
    if relation.target.kind is TargetKind.MODULE:
        if not target_id.startswith("python:module:"):
            raise ValueError("internal module relation target has an invalid id")
        target_alias = _module_alias(target_id.removeprefix("python:module:"))
    else:
        if relation.target.kind is not TargetKind.CLASS or not target_id.startswith(
            "python:class:"
        ):
            raise ValueError("internal class relation target has an invalid id")
        target_alias = _class_alias(target_id)
    if relation.kind is RelationKind.INHERITANCE:
        return target_alias, "<|--", source_alias, "継承"
    if relation.kind is RelationKind.COMPOSITION:
        return source_alias, "*--", target_alias, "合成"
    if relation.kind is RelationKind.TYPED_DEPENDENCY:
        return source_alias, "..>", target_alias, "型依存"
    return None
