from pathlib import PurePosixPath

import pytest

from code_structure_viz.adapters.python.model import (
    DecoratorRef,
    MemberKind,
    MemberScope,
    MethodKind,
    MethodSignature,
    PythonClassEntity,
    PythonMember,
    PythonRelation,
    RelationKind,
    RelationTarget,
    SourceRange,
    TargetKind,
    TargetResolution,
    member_sort_key,
    relation_sort_key,
)


def test_class_and_range_are_normalized_immutable_values() -> None:
    entity = PythonClassEntity.create(
        module="pkg.cafe\u0301",
        qualified_name="Outer.Inner",
        path=PurePosixPath("src/pkg/caf\u00e9.py"),
        source_range=SourceRange(3, 8),
        decorators=(DecoratorRef("deco\u0301rator", False),),
    )

    assert entity.id == "python:class:pkg.caf\u00e9:Outer.Inner"
    assert entity.name == "Inner"
    assert entity.module == "pkg.caf\u00e9"
    assert entity.decorators == (DecoratorRef("dec\u00f3rator", False),)
    with pytest.raises(AttributeError):
        entity.name = "Changed"  # type: ignore[misc]
    with pytest.raises(ValueError):
        SourceRange(0, 1)
    with pytest.raises(ValueError):
        SourceRange(2, 1)


def test_member_id_is_sha256_of_the_closed_identity_tuple() -> None:
    member = PythonMember.create_field(
        owner_id="python:class:pkg.mod:Thing",
        name="value",
        scope=MemberScope.CLASS,
        annotation="pkg.mod.Other",
        source_range=SourceRange(4, 4),
    )

    assert member.id == (
        "python:member:a336e97c4baa49f3c545bd38b28c8f9419db069344fda1d6b18ddd65510489a9"
    )
    assert member.kind is MemberKind.FIELD
    assert member.declaration_ordinal == 0
    assert member.signature is None


def test_member_sort_uses_closed_enum_ranks_before_source_range() -> None:
    owner = "python:class:pkg.mod:Thing"
    field = PythonMember.create_field(
        owner_id=owner,
        name="z",
        scope=MemberScope.INSTANCE,
        annotation=None,
        source_range=SourceRange(20, 20),
    )
    method = PythonMember.create_method(
        owner_id=owner,
        name="a",
        method_kind=MethodKind.INSTANCE,
        signature=MethodSignature(False, (), None),
        decorators=(),
        source_range=SourceRange(1, 1),
        declaration_ordinal=0,
    )

    assert sorted((method, field), key=member_sort_key) == [field, method]


def test_relation_id_and_sort_follow_closed_semantic_identity() -> None:
    target = RelationTarget(
        TargetResolution.INTERNAL,
        TargetKind.CLASS,
        "python:class:pkg.mod:Other",
        "pkg.mod.Other",
    )
    relation = PythonRelation.create(
        kind=RelationKind.COMPOSITION,
        source_id="python:class:pkg.mod:Thing",
        target=target,
        via_member_id="python:member:abc",
        annotation="pkg.mod.Other",
        source_range=SourceRange(6, 6),
    )
    import_relation = PythonRelation.create(
        kind=RelationKind.IMPORT_DEPENDENCY,
        source_id="python:module:pkg.mod",
        target=RelationTarget(
            TargetResolution.EXTERNAL,
            TargetKind.MODULE,
            None,
            "outside.lib",
        ),
        via_member_id=None,
        annotation=None,
        source_range=SourceRange(1, 1),
    )

    assert relation.id == (
        "python:relation:11818a04becebd5395a55dc1fc92c74a14156beceeef7ff910fe8161107332cd"
    )
    assert sorted((import_relation, relation), key=relation_sort_key) == [relation, import_relation]
