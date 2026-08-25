import hashlib
from pathlib import PurePosixPath

from code_structure_viz.adapters.python.analyzer import (
    PythonAnalysisResult,
    PythonSnapshotAnalyzer,
)
from code_structure_viz.adapters.python.model import (
    MemberKind,
    MemberScope,
    MethodKind,
    ParameterKind,
    PropertyRole,
    RelationKind,
    TargetResolution,
)
from code_structure_viz.adapters.python.module_index import PythonModuleIndex
from code_structure_viz.core.config import PythonConfig
from code_structure_viz.source.source_view import SourceFile, SourceFileKind, SourceView


def _analyze(files: dict[str, bytes]) -> PythonAnalysisResult:
    sources = tuple(
        SourceFile(
            PurePosixPath(path),
            SourceFileKind.REGULAR,
            None,
            len(content),
            hashlib.sha256(content).hexdigest(),
            content,
        )
        for path, content in files.items()
    )
    view = SourceView(None, sources, (), "0" * 64)
    config = PythonConfig(("src",), ("**/*.py",), ())
    return PythonSnapshotAnalyzer().analyze(PythonModuleIndex.build(view, config))


def test_analyzer_discovers_direct_and_nested_classes_members_and_static_relations() -> None:
    result = _analyze(
        {
            "src/pkg/model.py": b"""
from dataclasses import dataclass as dc

@dc(frozen=True)
class Outer:
    count: int

    class Inner:
        pass

    def __init__(self, value: \"Inner\") -> None:
        self.value: Inner = value
        if value:
            self.other = value
        def local():
            self.hidden = value

    @property
    def item(self) -> Inner:
        return self.value

    @item.setter
    def item(self, value: Inner) -> None:
        self.value = value

if True:
    class Skipped:
        pass

def factory():
    class Local:
        pass
"""
        }
    )

    assert tuple(entity.id for entity in result.entities) == (
        "python:class:pkg.model:Outer",
        "python:class:pkg.model:Outer.Inner",
    )
    assert result.entities[0].decorators[0].name == "dataclasses.dataclass"
    assert result.entities[0].decorators[0].called is True
    observed_members = {
        (member.kind, member.name, member.scope, member.property_role) for member in result.members
    }
    assert (MemberKind.FIELD, "count", MemberScope.CLASS, None) in observed_members
    assert (MemberKind.FIELD, "value", MemberScope.INSTANCE, None) in observed_members
    assert (MemberKind.FIELD, "other", MemberScope.INSTANCE, None) in observed_members
    assert not any(member.name == "hidden" for member in result.members)
    assert (MemberKind.PROPERTY, "item", None, PropertyRole.GETTER) in observed_members
    assert (MemberKind.PROPERTY, "item", None, PropertyRole.SETTER) in observed_members
    assert sum(member.kind is MemberKind.METHOD for member in result.members) == 1
    assert sum(item.kind is RelationKind.COMPOSITION for item in result.relations) == 1
    assert sum(item.kind is RelationKind.TYPED_DEPENDENCY for item in result.relations) == 3
    assert all(
        item.target.resolution is TargetResolution.INTERNAL
        for item in result.relations
        if item.kind is not RelationKind.IMPORT_DEPENDENCY
    )
    assert [item.code.value for item in result.diagnostics].count("CSV-PY-009") == 2


def test_control_flow_walker_covers_try_handlers_try_star_and_match_cases() -> None:
    result = _analyze(
        {
            "src/pkg/control.py": b"""
class TryBody: pass
class ExceptBody: pass
class TryElse: pass
class TryFinally: pass
class ExceptStarBody: pass
class MatchBody: pass

class Owner:
    def assign(self, value):
        try:
            self.in_try: TryBody = value
        except Exception:
            self.in_except: ExceptBody = value
        else:
            self.in_else: TryElse = value
        finally:
            self.in_finally: TryFinally = value

        try:
            pass
        except* Exception:
            self.in_except_star: ExceptStarBody = value

        match value:
            case _:
                self.in_match: MatchBody = value
"""
        }
    )

    instance_fields = {
        member.name
        for member in result.members
        if member.kind is MemberKind.FIELD and member.scope is MemberScope.INSTANCE
    }
    assert instance_fields == {
        "in_try",
        "in_except",
        "in_else",
        "in_finally",
        "in_except_star",
        "in_match",
    }


def test_skipped_class_walker_reports_classes_in_try_handlers_and_match_cases() -> None:
    result = _analyze(
        {
            "src/pkg/skipped.py": b"""
class Safe:
    pass

try:
    pass
except Exception:
    class InExcept:
        pass

try:
    pass
except* Exception:
    class InExceptStar:
        pass

match value:
    case _:
        class InMatch:
            pass
"""
        }
    )

    skipped = [item for item in result.diagnostics if item.code.value == "CSV-PY-009"]
    assert [(item.symbol, item.line) for item in skipped] == [
        ("class:InExcept", 8),
        ("class:InExceptStar", 14),
        ("class:InMatch", 19),
    ]
    assert {
        item.reference for item in result.frontier if item.reason.value == "unsupported_scope"
    } == {
        "python:class:pkg.skipped:InExcept",
        "python:class:pkg.skipped:InExceptStar",
        "python:class:pkg.skipped:InMatch",
    }


def test_property_accessor_matching_and_type_reference_adoption_are_exact() -> None:
    result = _analyze(
        {
            "src/pkg/properties.py": """
import builtins

class Receiver: pass
class GetterExtra: pass
class GetterReturn: pass
class SetterValue: pass
class SetterExtra: pass
class SetterReturn: pass
class DeleterExtra: pass
class DeleterReturn: pass

class Owner:
    @property
    def accepted(self: Receiver, extra: GetterExtra) -> GetterReturn:
        raise NotImplementedError

    @accepted.setter
    def accepted(
        self: Receiver, value: SetterValue, ignored: SetterExtra
    ) -> SetterReturn:
        raise NotImplementedError

    @accepted.deleter
    def accepted(self: Receiver, ignored: DeleterExtra) -> DeleterReturn:
        raise NotImplementedError

    @other.setter
    def mismatched(self, value: SetterValue) -> SetterReturn:
        raise NotImplementedError

    @builtins.property
    def explicit(self) -> GetterReturn:
        raise NotImplementedError

    @property
    def caf\u00e9(self) -> GetterReturn:
        raise NotImplementedError

    @cafe\u0301.setter
    def caf\u00e9(self, value: SetterValue) -> None:
        raise NotImplementedError
""".encode("utf-8")
        }
    )

    accepted = [member for member in result.members if member.name == "accepted"]
    assert [member.property_role for member in accepted] == [
        PropertyRole.GETTER,
        PropertyRole.SETTER,
        PropertyRole.DELETER,
    ]
    assert [member.annotation for member in accepted] == [
        "GetterReturn",
        "SetterValue",
        None,
    ]
    mismatched = next(member for member in result.members if member.name == "mismatched")
    explicit = next(member for member in result.members if member.name == "explicit")
    assert (mismatched.kind, mismatched.method_kind) == (MemberKind.METHOD, MethodKind.INSTANCE)
    assert (explicit.kind, explicit.method_kind) == (MemberKind.METHOD, MethodKind.INSTANCE)
    cafe = [member for member in result.members if member.name == "caf\u00e9"]
    assert [member.property_role for member in cafe] == [
        PropertyRole.GETTER,
        PropertyRole.SETTER,
    ]

    accepted_ids = {member.id for member in accepted}
    adopted_targets = {
        relation.target.name
        for relation in result.relations
        if relation.kind is RelationKind.TYPED_DEPENDENCY and relation.via_member_id in accepted_ids
    }
    assert adopted_targets == {"pkg.properties.GetterReturn", "pkg.properties.SetterValue"}


def test_nested_quoted_forward_annotation_is_a_literal_without_reference_leak() -> None:
    result = _analyze({"src/pkg/forward.py": b"class Owner:\n    value: \"'private.Secret'\"\n"})

    assert result.members[0].annotation == "?"
    assert result.relations == ()
    assert not any(item.code.value in {"CSV-PY-008", "CSV-PY-011"} for item in result.diagnostics)
    assert "private.Secret" not in repr(result)


def test_encoding_and_parse_failures_are_isolated_per_file() -> None:
    result = _analyze(
        {
            "src/pkg/latin.py": "# coding: latin-1\nclass Café:\n    pass\n".encode("latin-1"),
            "src/pkg/encoding.py": b"# coding: ascii\nname = '\xff'\n",
            "src/pkg/syntax.py": b"class Broken(\n",
        }
    )

    assert tuple(entity.name for entity in result.entities) == ("Café",)
    assert result.parsed_file_count == 1
    assert tuple(item.stage.value for item in result.failures) == ("encoding", "parse")
    assert tuple(item.diagnostic_code.value for item in result.failures) == (
        "CSV-PY-002",
        "CSV-PY-003",
    )
    parse_diagnostic = next(item for item in result.diagnostics if item.code.value == "CSV-PY-003")
    assert parse_diagnostic.path == "src/pkg/syntax.py"
    assert parse_diagnostic.line == 1


def test_dynamic_import_calls_create_no_import_evidence() -> None:
    result = _analyze(
        {
            "src/pkg/dynamic.py": b"""
class Safe:
    pass

__import__('secret.mod')
load = __import__
load('another.mod')

def wrapper(name):
    return __import__(name)
wrapper('third.mod')
"""
        }
    )

    assert result.modules[0].bindings == ()
    assert result.relations == ()
    assert result.frontier == ()
    assert result.diagnostics == ()


def test_duplicate_class_identity_excludes_all_colliding_declarations() -> None:
    result = _analyze(
        {
            "src/pkg/duplicate.py": b"""
class Duplicate:
    pass

class Duplicate:
    pass
"""
        }
    )

    assert result.entities == ()
    assert result.members == ()
    assert len(result.class_collisions) == 1
    assert result.class_collisions[0].entity_id == "python:class:pkg.duplicate:Duplicate"
    assert [item.code.value for item in result.diagnostics] == ["CSV-PY-012"]


def test_type_references_follow_local_import_unknown_and_exclusion_priorities() -> None:
    result = _analyze(
        {
            "src/pkg/model.py": b"""
from typing import Generic, TypeVar
from ext.models import Foo as ExternalFoo

T = TypeVar('T')

class Foo:
    pass

class Outer:
    class Inner:
        pass

    same_module: list[Foo]
    nested: Inner
    missing: Missing
    external: ExternalFoo

class Box(Generic[T]):
    pass
"""
        }
    )

    composition = [item for item in result.relations if item.kind is RelationKind.COMPOSITION]
    assert tuple((item.target.resolution.value, item.target.name) for item in composition) == (
        ("internal", "pkg.model.Foo"),
        ("internal", "pkg.model.Outer.Inner"),
        ("external", "ext.models.Foo"),
        ("unknown", "Missing"),
    )
    assert not any(item.target.name in {"list", "typing.Generic", "T"} for item in result.relations)
    unknown = [item for item in result.diagnostics if item.code.value == "CSV-PY-008"]
    assert len(unknown) == 1
    assert (unknown[0].path, unknown[0].symbol) == ("src/pkg/model.py", "Missing")


def test_type_text_and_targets_share_the_closed_candidate_construction_priority() -> None:
    result = _analyze(
        {
            "src/app/types.py": b"class Internal: pass\n",
            "src/pkg/model.py": b"""
from ext import Foo
from app import types as SymbolAlias
import app as ModuleAlias
from typing import Annotated, Literal

class Foo: pass
class Literal: pass
class Annotated: pass
class Item: pass

class Owner:
    local: Foo
    symbol_binding: SymbolAlias
    module_suffix: ModuleAlias.types
    original_dotted: app.types.Internal
    literal_shadow: Literal[1]
    annotated_shadow: Annotated[Item, 1]
""",
        }
    )

    fields = {member.id: member for member in result.members if member.kind is MemberKind.FIELD}
    annotations = {member.name: member.annotation for member in fields.values()}
    targets = tuple(
        sorted(
            (
                fields[relation.via_member_id].name,
                relation.target.resolution.value,
                relation.target.kind.value,
                relation.target.name,
            )
            for relation in result.relations
            if relation.kind is RelationKind.COMPOSITION and relation.via_member_id in fields
        )
    )

    assert annotations == {
        "local": "Foo",
        "symbol_binding": "app.types",
        "module_suffix": "app.types",
        "original_dotted": "app.types.Internal",
        "literal_shadow": "Literal[?]",
        "annotated_shadow": "Annotated[Item, ?]",
    }
    assert targets == (
        ("annotated_shadow", "internal", "class", "pkg.model.Annotated"),
        ("annotated_shadow", "internal", "class", "pkg.model.Item"),
        ("literal_shadow", "internal", "class", "pkg.model.Literal"),
        ("local", "internal", "class", "pkg.model.Foo"),
        ("module_suffix", "external", "symbol", "app.types"),
        ("original_dotted", "internal", "class", "app.types.Internal"),
        ("symbol_binding", "external", "symbol", "app.types"),
    )


def test_inheritance_adopts_only_the_base_expression_outer_symbolic_head() -> None:
    result = _analyze(
        {
            "src/pkg/inheritance.py": b"""
from typing import Annotated

class A: pass
class B: pass

class UnionBase(A | B): pass
class TupleBase((A, B)): pass
class AnnotatedBase(Annotated[A, 1]): pass
class SubscriptBase(A[B]): pass
"""
        }
    )

    inheritance = tuple(
        (
            relation.source_id,
            relation.target.resolution.value,
            relation.target.name,
            relation.annotation,
        )
        for relation in result.relations
        if relation.kind is RelationKind.INHERITANCE
    )

    assert inheritance == (
        (
            "python:class:pkg.inheritance:SubscriptBase",
            "internal",
            "pkg.inheritance.A",
            "A[B]",
        ),
    )


def test_conflicting_field_annotations_merge_to_unknown_without_guessing_relations() -> None:
    result = _analyze(
        {
            "src/pkg/conflict.py": b"""
class A:
    pass
class B:
    pass
class Owner:
    value: A
    value: B
"""
        }
    )

    value = next(item for item in result.members if item.name == "value")
    assert value.annotation == "?"
    assert value.range.start_line == 7
    assert not any(item.via_member_id == value.id for item in result.relations)
    conflict = [item for item in result.diagnostics if item.code.value == "CSV-PY-013"]
    assert len(conflict) == 1
    assert conflict[0].symbol == value.id


def test_method_signatures_and_duplicate_declarations_keep_lexical_parameter_contract() -> None:
    result = _analyze(
        {
            "src/pkg/service.py": b"""
class Service:
    @staticmethod
    async def run(
        a: int, /, b: str = 'redacted', *items: bytes, flag: bool, **meta: object
    ) -> None:
        pass

    def repeat(self) -> None:
        pass

    def repeat(self, value: int) -> None:
        pass
"""
        }
    )

    run = next(item for item in result.members if item.name == "run")
    assert run.method_kind is MethodKind.STATIC
    assert run.signature is not None and run.signature.async_ is True
    assert tuple(parameter.kind for parameter in run.signature.parameters) == (
        ParameterKind.POSITIONAL_ONLY,
        ParameterKind.POSITIONAL_OR_KEYWORD,
        ParameterKind.VAR_POSITIONAL,
        ParameterKind.KEYWORD_ONLY,
        ParameterKind.VAR_KEYWORD,
    )
    assert tuple(parameter.has_default for parameter in run.signature.parameters) == (
        False,
        True,
        False,
        False,
        False,
    )
    repeats = [item for item in result.members if item.name == "repeat"]
    assert tuple(item.declaration_ordinal for item in repeats) == (0, 1)
    assert repeats[0].id != repeats[1].id


def test_static_imports_are_closed_and_ambiguous_binding_has_no_winner() -> None:
    result = _analyze(
        {
            "src/pkg/a.py": b"from . import b\n",
            "src/pkg/b.py": b"class B: pass\n",
            "src/pkg/use.py": b"""
if condition:
    import first.lib as alias
else:
    import second.lib as alias
from external.types import *

class Use:
    value: alias.Value
""",
        }
    )

    use = next(item for item in result.modules if item.module == "pkg.use")
    assert not any(item.local_name == "alias" for item in use.bindings)
    internal_import = next(
        item
        for item in result.relations
        if item.kind is RelationKind.IMPORT_DEPENDENCY and item.source_id == "python:module:pkg.a"
    )
    assert internal_import.target.name == "pkg"
    assert internal_import.target.resolution is TargetResolution.EXTERNAL
    assert any(item.reason.value == "star_import" for item in result.frontier)
    assert any(
        item.code.value == "CSV-PY-008" and item.symbol == "alias.Value"
        for item in result.diagnostics
    )


def test_unsupported_annotation_emits_one_site_diagnostic_and_no_reference() -> None:
    result = _analyze({"src/pkg/unsafe.py": b"class Safe:\n    value: factory(Secret)\n"})

    member = result.members[0]
    assert member.annotation == "?"
    assert result.relations == ()
    unsupported = [item for item in result.diagnostics if item.code.value == "CSV-PY-011"]
    assert len(unsupported) == 1
    assert unsupported[0].symbol == f"{member.id}#annotation"
