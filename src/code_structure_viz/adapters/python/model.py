from __future__ import annotations

import hashlib
import unicodedata
from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Final

from code_structure_viz.core.diagnostics import Diagnostic, DiagnosticCode


class MemberKind(StrEnum):
    FIELD = "field"
    PROPERTY = "property"
    METHOD = "method"


class MemberScope(StrEnum):
    CLASS = "class"
    INSTANCE = "instance"


class PropertyRole(StrEnum):
    GETTER = "getter"
    SETTER = "setter"
    DELETER = "deleter"


class MethodKind(StrEnum):
    INSTANCE = "instance"
    CLASS = "class"
    STATIC = "static"


class ParameterKind(StrEnum):
    POSITIONAL_ONLY = "positional_only"
    POSITIONAL_OR_KEYWORD = "positional_or_keyword"
    VAR_POSITIONAL = "var_positional"
    KEYWORD_ONLY = "keyword_only"
    VAR_KEYWORD = "var_keyword"


class RelationKind(StrEnum):
    INHERITANCE = "inheritance"
    COMPOSITION = "composition"
    TYPED_DEPENDENCY = "typed_dependency"
    IMPORT_DEPENDENCY = "import_dependency"


class TargetResolution(StrEnum):
    INTERNAL = "internal"
    EXTERNAL = "external"
    UNKNOWN = "unknown"


class TargetKind(StrEnum):
    CLASS = "class"
    MODULE = "module"
    SYMBOL = "symbol"


class FailedStage(StrEnum):
    READ = "read"
    PATH_SAFETY = "path_safety"
    ENCODING = "encoding"
    PARSE = "parse"
    MODULE_IDENTITY = "module_identity"
    MODULE_COLLISION = "module_collision"


class FrontierDirection(StrEnum):
    UPSTREAM = "upstream"
    DOWNSTREAM = "downstream"
    FAILURE = "failure"


class FrontierKind(StrEnum):
    MODULE = "module"
    CLASS = "class"
    SYMBOL = "symbol"
    FILE = "file"


class FrontierReason(StrEnum):
    DEPTH_LIMIT = "depth_limit"
    UNRESOLVED_REFERENCE = "unresolved_reference"
    FAILED_SOURCE = "failed_source"
    UNSUPPORTED_SCOPE = "unsupported_scope"
    STAR_IMPORT = "star_import"
    IDENTITY_COLLISION = "identity_collision"


_MEMBER_KIND_RANK: Final = {
    MemberKind.FIELD: 0,
    MemberKind.PROPERTY: 1,
    MemberKind.METHOD: 2,
}
_SCOPE_RANK: Final = {None: 0, MemberScope.CLASS: 1, MemberScope.INSTANCE: 2}
_PROPERTY_RANK: Final = {
    None: 0,
    PropertyRole.GETTER: 1,
    PropertyRole.SETTER: 2,
    PropertyRole.DELETER: 3,
}
_METHOD_RANK: Final = {
    None: 0,
    MethodKind.INSTANCE: 1,
    MethodKind.CLASS: 2,
    MethodKind.STATIC: 3,
}
_RELATION_RANK: Final = {
    RelationKind.INHERITANCE: 0,
    RelationKind.COMPOSITION: 1,
    RelationKind.TYPED_DEPENDENCY: 2,
    RelationKind.IMPORT_DEPENDENCY: 3,
}
_RESOLUTION_RANK: Final = {
    TargetResolution.INTERNAL: 0,
    TargetResolution.EXTERNAL: 1,
    TargetResolution.UNKNOWN: 2,
}
_TARGET_KIND_RANK: Final = {
    TargetKind.CLASS: 0,
    TargetKind.MODULE: 1,
    TargetKind.SYMBOL: 2,
}
_FRONTIER_DIRECTION_RANK: Final = {
    FrontierDirection.UPSTREAM: 0,
    FrontierDirection.DOWNSTREAM: 1,
    FrontierDirection.FAILURE: 2,
}


def _nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def _utf8(value: str) -> bytes:
    return value.encode("utf-8")


def _digest(parts: tuple[str, ...]) -> str:
    return hashlib.sha256(b"\0".join(_utf8(_nfc(part)) for part in parts)).hexdigest()


@dataclass(frozen=True, slots=True)
class SourceRange:
    start_line: int
    end_line: int

    def __post_init__(self) -> None:
        if (
            type(self.start_line) is not int
            or type(self.end_line) is not int
            or self.start_line <= 0
            or self.end_line < self.start_line
        ):
            raise ValueError("source range must contain positive ordered lines")


@dataclass(frozen=True, slots=True)
class SourceRangeWithColumns:
    start_line: int
    start_col: int
    end_line: int
    end_col: int

    def __post_init__(self) -> None:
        if (
            type(self.start_line) is not int
            or type(self.end_line) is not int
            or type(self.start_col) is not int
            or type(self.end_col) is not int
            or self.start_line <= 0
            or self.end_line < self.start_line
            or self.start_col < 0
            or self.end_col < 0
        ):
            raise ValueError("internal source range is invalid")

    def public(self) -> SourceRange:
        return SourceRange(self.start_line, self.end_line)


@dataclass(frozen=True, slots=True)
class DecoratorRef:
    name: str
    called: bool

    def __post_init__(self) -> None:
        if type(self.called) is not bool or not self.name:
            raise ValueError("decorator is invalid")
        object.__setattr__(self, "name", _nfc(self.name))


@dataclass(frozen=True, slots=True)
class Parameter:
    name: str
    kind: ParameterKind
    annotation: str | None
    has_default: bool

    def __post_init__(self) -> None:
        if not self.name or type(self.has_default) is not bool:
            raise ValueError("parameter is invalid")
        object.__setattr__(self, "name", _nfc(self.name))
        if self.annotation is not None:
            object.__setattr__(self, "annotation", _nfc(self.annotation))


@dataclass(frozen=True, slots=True)
class MethodSignature:
    async_: bool
    parameters: tuple[Parameter, ...]
    returns: str | None

    def __post_init__(self) -> None:
        if type(self.async_) is not bool:
            raise ValueError("signature async marker is invalid")
        if self.returns is not None:
            object.__setattr__(self, "returns", _nfc(self.returns))


@dataclass(frozen=True, slots=True)
class PythonClassEntity:
    id: str
    kind: str
    module: str
    qualified_name: str
    name: str
    path: PurePosixPath
    range: SourceRange
    decorators: tuple[DecoratorRef, ...]

    def __post_init__(self) -> None:
        module = _nfc(self.module)
        qualified_name = _nfc(self.qualified_name)
        expected_id = f"python:class:{module}:{qualified_name}"
        if (
            self.kind != "class"
            or self.id != expected_id
            or self.name != qualified_name.rsplit(".", 1)[-1]
        ):
            raise ValueError("class entity identity is invalid")
        object.__setattr__(self, "module", module)
        object.__setattr__(self, "qualified_name", qualified_name)
        object.__setattr__(self, "name", _nfc(self.name))

    @classmethod
    def create(
        cls,
        *,
        module: str,
        qualified_name: str,
        path: PurePosixPath,
        source_range: SourceRange,
        decorators: tuple[DecoratorRef, ...] = (),
    ) -> PythonClassEntity:
        normalized_module = _nfc(module)
        normalized_name = _nfc(qualified_name)
        return cls(
            id=f"python:class:{normalized_module}:{normalized_name}",
            kind="class",
            module=normalized_module,
            qualified_name=normalized_name,
            name=normalized_name.rsplit(".", 1)[-1],
            path=path,
            range=source_range,
            decorators=decorators,
        )


@dataclass(frozen=True, slots=True)
class PythonMember:
    id: str
    owner_id: str
    kind: MemberKind
    name: str
    scope: MemberScope | None
    property_role: PropertyRole | None
    method_kind: MethodKind | None
    annotation: str | None
    signature: MethodSignature | None
    decorators: tuple[DecoratorRef, ...]
    range: SourceRange
    declaration_ordinal: int

    def __post_init__(self) -> None:
        if type(self.declaration_ordinal) is not int or self.declaration_ordinal < 0:
            raise ValueError("member declaration ordinal is invalid")
        name = _nfc(self.name)
        annotation = _nfc(self.annotation) if self.annotation is not None else None
        expected = _member_id(
            self.owner_id,
            self.kind,
            name,
            self.scope,
            self.property_role,
            self.method_kind,
            self.declaration_ordinal,
        )
        if self.id != expected:
            raise ValueError("member identity is invalid")
        if self.kind is MemberKind.FIELD:
            if (
                self.scope is None
                or self.property_role is not None
                or self.method_kind is not None
                or self.signature is not None
                or self.declaration_ordinal != 0
            ):
                raise ValueError("field shape is invalid")
        elif self.kind is MemberKind.PROPERTY:
            if (
                self.scope is not None
                or self.property_role is None
                or self.method_kind is not None
                or self.signature is None
            ):
                raise ValueError("property shape is invalid")
        elif (
            self.scope is not None
            or self.property_role is not None
            or self.method_kind is None
            or self.signature is None
            or self.annotation is not None
        ):
            raise ValueError("method shape is invalid")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "annotation", annotation)

    @classmethod
    def create_field(
        cls,
        *,
        owner_id: str,
        name: str,
        scope: MemberScope,
        annotation: str | None,
        source_range: SourceRange,
        decorators: tuple[DecoratorRef, ...] = (),
    ) -> PythonMember:
        return cls._create(
            owner_id=owner_id,
            kind=MemberKind.FIELD,
            name=name,
            scope=scope,
            property_role=None,
            method_kind=None,
            annotation=annotation,
            signature=None,
            decorators=decorators,
            source_range=source_range,
            declaration_ordinal=0,
        )

    @classmethod
    def create_property(
        cls,
        *,
        owner_id: str,
        name: str,
        role: PropertyRole,
        annotation: str | None,
        signature: MethodSignature,
        decorators: tuple[DecoratorRef, ...],
        source_range: SourceRange,
        declaration_ordinal: int,
    ) -> PythonMember:
        return cls._create(
            owner_id=owner_id,
            kind=MemberKind.PROPERTY,
            name=name,
            scope=None,
            property_role=role,
            method_kind=None,
            annotation=annotation,
            signature=signature,
            decorators=decorators,
            source_range=source_range,
            declaration_ordinal=declaration_ordinal,
        )

    @classmethod
    def create_method(
        cls,
        *,
        owner_id: str,
        name: str,
        method_kind: MethodKind,
        signature: MethodSignature,
        decorators: tuple[DecoratorRef, ...],
        source_range: SourceRange,
        declaration_ordinal: int,
    ) -> PythonMember:
        return cls._create(
            owner_id=owner_id,
            kind=MemberKind.METHOD,
            name=name,
            scope=None,
            property_role=None,
            method_kind=method_kind,
            annotation=None,
            signature=signature,
            decorators=decorators,
            source_range=source_range,
            declaration_ordinal=declaration_ordinal,
        )

    @classmethod
    def _create(
        cls,
        *,
        owner_id: str,
        kind: MemberKind,
        name: str,
        scope: MemberScope | None,
        property_role: PropertyRole | None,
        method_kind: MethodKind | None,
        annotation: str | None,
        signature: MethodSignature | None,
        decorators: tuple[DecoratorRef, ...],
        source_range: SourceRange,
        declaration_ordinal: int,
    ) -> PythonMember:
        normalized_name = _nfc(name)
        return cls(
            id=_member_id(
                owner_id,
                kind,
                normalized_name,
                scope,
                property_role,
                method_kind,
                declaration_ordinal,
            ),
            owner_id=owner_id,
            kind=kind,
            name=normalized_name,
            scope=scope,
            property_role=property_role,
            method_kind=method_kind,
            annotation=annotation,
            signature=signature,
            decorators=decorators,
            range=source_range,
            declaration_ordinal=declaration_ordinal,
        )


def _member_id(
    owner_id: str,
    kind: MemberKind,
    name: str,
    scope: MemberScope | None,
    property_role: PropertyRole | None,
    method_kind: MethodKind | None,
    declaration_ordinal: int,
) -> str:
    value = _digest(
        (
            owner_id,
            kind.value,
            name,
            scope.value if scope is not None else "",
            property_role.value if property_role is not None else "",
            method_kind.value if method_kind is not None else "",
            str(declaration_ordinal),
        )
    )
    return f"python:member:{value}"


@dataclass(frozen=True, slots=True)
class RelationTarget:
    resolution: TargetResolution
    kind: TargetKind
    id: str | None
    name: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("relation target name is empty")
        object.__setattr__(self, "name", _nfc(self.name))
        if self.resolution is TargetResolution.INTERNAL:
            if self.id is None or self.kind is TargetKind.SYMBOL:
                raise ValueError("internal relation target requires an entity id")
        elif self.id is not None:
            raise ValueError("non-internal relation target cannot have an id")


@dataclass(frozen=True, slots=True)
class PythonRelation:
    id: str
    kind: RelationKind
    source_id: str
    target: RelationTarget
    via_member_id: str | None
    annotation: str | None
    range: SourceRange

    def __post_init__(self) -> None:
        annotation = _nfc(self.annotation) if self.annotation is not None else None
        expected = _relation_id(
            self.kind, self.source_id, self.target, self.via_member_id, annotation
        )
        if self.id != expected:
            raise ValueError("relation identity is invalid")
        object.__setattr__(self, "annotation", annotation)

    @classmethod
    def create(
        cls,
        *,
        kind: RelationKind,
        source_id: str,
        target: RelationTarget,
        via_member_id: str | None,
        annotation: str | None,
        source_range: SourceRange,
    ) -> PythonRelation:
        normalized_annotation = _nfc(annotation) if annotation is not None else None
        return cls(
            id=_relation_id(kind, source_id, target, via_member_id, normalized_annotation),
            kind=kind,
            source_id=source_id,
            target=target,
            via_member_id=via_member_id,
            annotation=normalized_annotation,
            range=source_range,
        )


def _relation_id(
    kind: RelationKind,
    source_id: str,
    target: RelationTarget,
    via_member_id: str | None,
    annotation: str | None,
) -> str:
    value = _digest(
        (
            kind.value,
            source_id,
            target.resolution.value,
            target.kind.value,
            target.id or "",
            target.name,
            via_member_id or "",
            annotation or "",
        )
    )
    return f"python:relation:{value}"


@dataclass(frozen=True, slots=True)
class FailedSourceFile:
    path: PurePosixPath
    stage: FailedStage
    diagnostic_code: DiagnosticCode


@dataclass(frozen=True, slots=True)
class CoverageFrontier:
    direction: FrontierDirection
    kind: FrontierKind
    reference: str
    reason: FrontierReason

    def __post_init__(self) -> None:
        if not self.reference:
            raise ValueError("frontier reference is empty")
        object.__setattr__(self, "reference", _nfc(self.reference))


@dataclass(frozen=True, slots=True)
class PythonCoverage:
    candidate_files: int
    parsed_files: int
    failed_files: tuple[FailedSourceFile, ...]
    selected_modules: tuple[str, ...]
    selected_entities: int
    frontier: tuple[CoverageFrontier, ...]


@dataclass(frozen=True, slots=True)
class PythonSnapshot:
    entities: tuple[PythonClassEntity, ...]
    members: tuple[PythonMember, ...]
    relations: tuple[PythonRelation, ...]
    coverage: PythonCoverage
    diagnostics: tuple[Diagnostic, ...]
    partial_safe: bool = False


def entity_sort_key(value: PythonClassEntity) -> tuple[object, ...]:
    return (
        _utf8(value.module),
        _utf8(value.qualified_name),
        _utf8(value.path.as_posix()),
        value.range.start_line,
        value.range.end_line,
        _utf8(value.id),
    )


def member_sort_key(value: PythonMember) -> tuple[object, ...]:
    return (
        _utf8(value.owner_id),
        _MEMBER_KIND_RANK[value.kind],
        _utf8(value.name),
        _SCOPE_RANK[value.scope],
        _PROPERTY_RANK[value.property_role],
        _METHOD_RANK[value.method_kind],
        value.declaration_ordinal,
        value.range.start_line,
        value.range.end_line,
        _utf8(value.id),
    )


def relation_sort_key(value: PythonRelation) -> tuple[object, ...]:
    return (
        _RELATION_RANK[value.kind],
        _utf8(value.source_id),
        _RESOLUTION_RANK[value.target.resolution],
        _TARGET_KIND_RANK[value.target.kind],
        _utf8(value.target.id or ""),
        _utf8(value.target.name),
        _utf8(value.via_member_id or ""),
        _utf8(value.annotation or ""),
        value.range.start_line,
        value.range.end_line,
        _utf8(value.id),
    )


def failed_source_sort_key(value: FailedSourceFile) -> tuple[bytes, bytes, bytes]:
    return (
        _utf8(value.path.as_posix()),
        _utf8(value.stage.value),
        _utf8(value.diagnostic_code.value),
    )


def frontier_sort_key(value: CoverageFrontier) -> tuple[object, ...]:
    return (
        _FRONTIER_DIRECTION_RANK[value.direction],
        _utf8(value.kind.value),
        _utf8(value.reference),
        _utf8(value.reason.value),
    )
