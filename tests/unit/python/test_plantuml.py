from pathlib import PurePosixPath

from code_structure_viz.adapters.python.model import (
    MemberScope,
    MethodKind,
    MethodSignature,
    Parameter,
    ParameterKind,
    PropertyRole,
    PythonClassEntity,
    PythonCoverage,
    PythonMember,
    PythonRelation,
    PythonSnapshot,
    RelationKind,
    RelationTarget,
    SourceRange,
    TargetKind,
    TargetResolution,
)
from code_structure_viz.adapters.python.plantuml import (
    escape_plantuml_text,
    render_plantuml,
)


def test_escape_plantuml_text_is_a_single_pass_closed_escape() -> None:
    value = 'e\u0301\\"\n\r\t\x01\u200b\u2028\U000e0001\ud800'

    assert escape_plantuml_text(value) == (
        '\u00e9\\\\\\"\\n\\r\\t\\u0001\\u200B\\u2028\\U000E0001\\uD800'
    )


def test_zero_class_modules_have_declared_packages_notes_and_internal_import() -> None:
    relation = PythonRelation.create(
        kind=RelationKind.IMPORT_DEPENDENCY,
        source_id="python:module:app.a",
        target=RelationTarget(
            TargetResolution.INTERNAL,
            TargetKind.MODULE,
            "python:module:app.b",
            "app.b",
        ),
        via_member_id=None,
        annotation=None,
        source_range=SourceRange(1, 1),
    )
    snapshot = PythonSnapshot(
        (),
        (),
        (relation,),
        PythonCoverage(2, 2, (), ("app.a", "app.b"), 0, ()),
        (),
    )

    expected = (
        "@startuml\n"
        "title Python structure snapshot\n"
        "left to right direction\n"
        "skinparam classAttributeIconSize 0\n"
        "hide empty members\n"
        'package "app.a" as '
        "M_de20bf4b2586afea89ef156114cfa20a8ab0be066d2bf05ac7397b7a78dd6927 {\n"
        '  note "classなし" as '
        "N_EMPTY_39a88b3cc6fc7c56c7083dd86b17c058d373d69c247f51bd2d3698023d2ef416\n"
        "}\n"
        'package "app.b" as '
        "M_f364321d2d7256bdb44d3eb1171ee961729680b6d8b193029dc5e051e167f0e1 {\n"
        '  note "classなし" as '
        "N_EMPTY_7819976ce0ccf98ef3d25e3d19355928ff58f9f7af0b886545a1d4bba0f2ae68\n"
        "}\n"
        "M_de20bf4b2586afea89ef156114cfa20a8ab0be066d2bf05ac7397b7a78dd6927"
        " ..> "
        "M_f364321d2d7256bdb44d3eb1171ee961729680b6d8b193029dc5e051e167f0e1"
        " : import依存\n"
        "legend right\n"
        "  <|-- 継承\n"
        "  *-- 合成\n"
        "  ..> 型依存\n"
        "  package ..> package import依存\n"
        "endlegend\n"
        "@enduml\n"
    )

    assert render_plantuml(snapshot) == expected.encode()


def test_members_use_closed_parameter_grammar_and_visual_relations_are_deduped() -> None:
    owner = PythonClassEntity.create(
        module="app.service",
        qualified_name="Service",
        path=PurePosixPath("src/app/service.py"),
        source_range=SourceRange(1, 20),
    )
    target = PythonClassEntity.create(
        module="app.service",
        qualified_name="Item",
        path=PurePosixPath("src/app/service.py"),
        source_range=SourceRange(22, 23),
    )
    field = PythonMember.create_field(
        owner_id=owner.id,
        name="item",
        scope=MemberScope.INSTANCE,
        annotation="app.service.Item",
        source_range=SourceRange(2, 2),
    )
    prop = PythonMember.create_property(
        owner_id=owner.id,
        name="current",
        role=PropertyRole.GETTER,
        annotation="app.service.Item",
        signature=MethodSignature(
            False,
            (Parameter("self", ParameterKind.POSITIONAL_OR_KEYWORD, None, False),),
            "app.service.Item",
        ),
        decorators=(),
        source_range=SourceRange(4, 5),
        declaration_ordinal=0,
    )
    method = PythonMember.create_method(
        owner_id=owner.id,
        name="find",
        method_kind=MethodKind.INSTANCE,
        signature=MethodSignature(
            False,
            (
                Parameter("self", ParameterKind.POSITIONAL_ONLY, None, False),
                Parameter("key", ParameterKind.POSITIONAL_ONLY, "str", False),
                Parameter(
                    "fallback",
                    ParameterKind.POSITIONAL_OR_KEYWORD,
                    "app.service.Item",
                    True,
                ),
                Parameter("items", ParameterKind.VAR_POSITIONAL, "bytes", False),
                Parameter("required", ParameterKind.KEYWORD_ONLY, "bool", True),
                Parameter("options", ParameterKind.VAR_KEYWORD, "object", False),
            ),
            "app.service.Item | None",
        ),
        decorators=(),
        source_range=SourceRange(7, 10),
        declaration_ordinal=0,
    )
    target_ref = RelationTarget(
        TargetResolution.INTERNAL,
        TargetKind.CLASS,
        target.id,
        "app.service.Item",
    )
    relations = tuple(
        PythonRelation.create(
            kind=RelationKind.COMPOSITION,
            source_id=owner.id,
            target=target_ref,
            via_member_id=member.id,
            annotation="app.service.Item",
            source_range=member.range,
        )
        for member in (field, prop)
    )
    snapshot = PythonSnapshot(
        (owner, target),
        (field, prop, method),
        relations,
        PythonCoverage(1, 1, (), ("app.service",), 2, ()),
        (),
        partial_safe=True,
    )

    rendered = render_plantuml(snapshot).decode("utf-8")

    assert (
        'note "不完全なsnapshot: 除外fileとcoverageはrun-manifest.jsonを参照" as N_INCOMPLETE'
        in rendered
    )
    assert "    field item : app.service.Item" in rendered
    assert "    property current(getter) : app.service.Item" in rendered
    assert (
        "    method find(key: str, /, fallback: app.service.Item = …, "
        "*items: bytes, required: bool = …, **options: object) : "
        "app.service.Item | None" in rendered
    )
    assert rendered.count(" : 合成") == 1
