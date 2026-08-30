from __future__ import annotations

import hashlib
import keyword
import re
import unicodedata
from dataclasses import dataclass, fields
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Final, Literal

from code_structure_viz.core.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    canonical_diagnostics,
    diagnostic,
)
from code_structure_viz.semantic.canonical_json import encode_canonical_json


class SqlAlchemyRowKind(StrEnum):
    COLUMN = "column"
    PRIMARY_KEY = "primary_key"
    UNIQUE = "unique"
    CHECK = "check"
    INDEX = "index"
    FOREIGN_KEY = "foreign_key"
    RELATIONSHIP = "relationship"
    INHERITANCE = "inheritance"
    ASSOCIATION_TABLE = "association_table"


class SqlAlchemyRelationKind(StrEnum):
    FOREIGN_KEY = "foreign_key"
    RELATIONSHIP = "relationship"
    INHERITANCE = "inheritance"
    ASSOCIATION = "association"


class SqlAlchemyTargetKind(StrEnum):
    TABLE = "table"
    MAPPED_CLASS = "mapped_class"
    UNKNOWN = "unknown"


class SqlAlchemyTargetResolution(StrEnum):
    INTERNAL = "internal"
    EXTERNAL = "external"
    UNKNOWN = "unknown"


class SqlAlchemyCardinality(StrEnum):
    SCALAR = "scalar"
    MANY = "many"
    UNKNOWN = "unknown"


class SqlAlchemyTypeCategory(StrEnum):
    INTEGER = "integer"
    STRING = "string"
    TEXT = "text"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    TIME = "time"
    DECIMAL = "decimal"
    FLOAT = "float"
    JSON = "json"
    BINARY = "binary"
    UUID = "uuid"
    ENUM = "enum"
    ARRAY = "array"
    CUSTOM = "custom"
    UNKNOWN = "unknown"


class RedactedExpressionCategory(StrEnum):
    ABSENT = "absent"
    LITERAL = "literal"
    CALLABLE = "callable"
    SQL_EXPRESSION = "sql_expression"
    COMPUTED = "computed"
    IDENTITY = "identity"
    UNKNOWN = "unknown"


class IndexTermKind(StrEnum):
    COLUMN = "column"
    EXPRESSION = "expression"


class SqlAlchemyMappingKind(StrEnum):
    DECLARATIVE_CLASS = "declarative_class"
    TABLE = "table"
    MIXED = "mixed"


class SqlAlchemyMappingSourceKind(StrEnum):
    DECLARATIVE_CLASS = "declarative_class"
    TABLE = "table"


class SqlAlchemyFailedStage(StrEnum):
    READ = "read"
    PATH_SAFETY = "path_safety"
    ENCODING = "encoding"
    PARSE = "parse"
    MODULE_IDENTITY = "module_identity"
    MODULE_COLLISION = "module_collision"


class SqlAlchemyFrontierDirection(StrEnum):
    UPSTREAM = "upstream"
    DOWNSTREAM = "downstream"
    FAILURE = "failure"


class SqlAlchemyFrontierKind(StrEnum):
    FILE = "file"
    MODULE = "module"
    CLASS = "class"
    TABLE = "table"
    ROW = "row"
    RELATION = "relation"


class SqlAlchemyFrontierReason(StrEnum):
    DEPTH_LIMIT = "depth_limit"
    FAILED_SOURCE = "failed_source"
    UNSUPPORTED_PATTERN = "unsupported_pattern"
    UNRESOLVED_REFERENCE = "unresolved_reference"
    IDENTITY_COLLISION = "identity_collision"
    TARGET_MISSING = "target_missing"
    TARGET_AMBIGUOUS = "target_ambiguous"


_TABLE_ID = re.compile(r"sqlalchemy:table:[0-9a-f]{64}\Z", flags=re.ASCII)
_ROW_ID = re.compile(r"sqlalchemy:row:[0-9a-f]{64}\Z", flags=re.ASCII)
_RELATION_ID = re.compile(r"sqlalchemy:relation:[0-9a-f]{64}\Z", flags=re.ASCII)
_OCCURRENCE_ID = re.compile(r"sqlalchemy:occurrence:[0-9a-f]{64}\Z", flags=re.ASCII)
_WINDOWS_DRIVE = re.compile(r"[A-Za-z]:")
_URI_SCHEME = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*:")
_REDACTION_RULE: Final = "code-structure-viz.sqlalchemy-redaction/v1"

_ROW_KIND_RANK: Final = {kind: rank for rank, kind in enumerate(SqlAlchemyRowKind)}
_RELATION_KIND_RANK: Final = {kind: rank for rank, kind in enumerate(SqlAlchemyRelationKind)}
_TARGET_RESOLUTION_RANK: Final = {
    kind: rank for rank, kind in enumerate(SqlAlchemyTargetResolution)
}
_MAPPING_SOURCE_RANK: Final = {kind: rank for rank, kind in enumerate(SqlAlchemyMappingSourceKind)}
_FAILED_STAGE_RANK: Final = {kind: rank for rank, kind in enumerate(SqlAlchemyFailedStage)}
_FRONTIER_DIRECTION_RANK: Final = {
    kind: rank for rank, kind in enumerate(SqlAlchemyFrontierDirection)
}
_FRONTIER_KIND_RANK: Final = {kind: rank for rank, kind in enumerate(SqlAlchemyFrontierKind)}
_FRONTIER_REASON_RANK: Final = {kind: rank for rank, kind in enumerate(SqlAlchemyFrontierReason)}


def _utf8(value: str) -> bytes:
    return value.encode("utf-8", errors="strict")


def _nfc(value: str, *, field: str, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    try:
        _utf8(value)
    except UnicodeEncodeError as error:
        raise ValueError(f"{field} must be valid UTF-8") from error
    normalized = unicodedata.normalize("NFC", value)
    if not normalized and not allow_empty:
        raise ValueError(f"{field} cannot be empty")
    if any(unicodedata.category(character) in {"Cc", "Cf"} for character in normalized):
        raise ValueError(f"{field} contains a control character")
    return normalized


def safe_structural_string(value: str, *, field: str = "structural string") -> str:
    normalized = _nfc(value, field=field)
    if (
        "/" in normalized
        or "\\" in normalized
        or "://" in normalized
        or normalized.startswith("~")
        or normalized in {".", ".."}
        or _WINDOWS_DRIVE.match(normalized) is not None
    ):
        raise ValueError(f"{field} is path-like or URI-like")
    return normalized


def safe_dotted_symbol(value: str, *, field: str = "symbol") -> str:
    normalized = _nfc(value, field=field)
    if not all(
        part.isidentifier() and not keyword.iskeyword(part) for part in normalized.split(".")
    ):
        raise ValueError(f"{field} must be a dotted identifier")
    return normalized


def safe_repository_path(value: str, *, field: str = "source path") -> str:
    normalized = _nfc(value, field=field)
    path = PurePosixPath(normalized)
    if (
        "\\" in normalized
        or path.is_absolute()
        or normalized.startswith("~")
        or normalized != path.as_posix()
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValueError(f"{field} must be repository-relative")
    return normalized


def _safe_frontier_reference(value: str) -> str:
    normalized = _nfc(value, field="frontier reference")
    if any(
        pattern.fullmatch(normalized) is not None
        for pattern in (_TABLE_ID, _ROW_ID, _RELATION_ID, _OCCURRENCE_ID)
    ):
        return normalized
    for prefix in ("module:", "class:"):
        if normalized.startswith(prefix):
            return f"{prefix}{safe_dotted_symbol(normalized.removeprefix(prefix))}"
    if normalized.endswith(".py"):
        if _URI_SCHEME.match(normalized) is not None:
            raise ValueError("frontier reference must be a safe path, symbol, or semantic id")
        try:
            return safe_repository_path(normalized, field="frontier reference")
        except ValueError as error:
            raise ValueError(
                "frontier reference must be a safe path, symbol, or semantic id"
            ) from error
    try:
        return safe_dotted_symbol(normalized, field="frontier reference")
    except ValueError as error:
        raise ValueError(
            "frontier reference must be a safe path, symbol, or semantic id"
        ) from error


def _positive_int(value: int, *, field: str) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{field} must be a positive integer")
    return value


def _non_negative_int(value: int, *, field: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return value


def _canonical_digest(value: object) -> str:
    return hashlib.sha256(encode_canonical_json(value)).hexdigest()


def _validate_table_id(value: str) -> str:
    if _TABLE_ID.fullmatch(value) is None:
        raise ValueError("SQLAlchemy table id is invalid")
    return value


def _validate_row_id(value: str) -> str:
    if _ROW_ID.fullmatch(value) is None:
        raise ValueError("SQLAlchemy row id is invalid")
    return value


def _validate_relation_id(value: str) -> str:
    if _RELATION_ID.fullmatch(value) is None:
        raise ValueError("SQLAlchemy relation id is invalid")
    return value


@dataclass(frozen=True, slots=True)
class SqlAlchemySourceRange:
    start_line: int
    end_line: int

    def __post_init__(self) -> None:
        _positive_int(self.start_line, field="source start line")
        _positive_int(self.end_line, field="source end line")
        if self.end_line < self.start_line:
            raise ValueError("source range is reversed")


@dataclass(frozen=True, slots=True)
class SqlAlchemySourceLocation:
    path: str
    range: SqlAlchemySourceRange

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", safe_repository_path(self.path))


@dataclass(frozen=True, slots=True)
class SqlAlchemyInternalDeclarationSpan:
    start_line: int
    start_utf8_byte_column: int
    end_line: int
    end_utf8_byte_column: int

    def __post_init__(self) -> None:
        _positive_int(self.start_line, field="declaration start line")
        _positive_int(self.end_line, field="declaration end line")
        _non_negative_int(
            self.start_utf8_byte_column,
            field="declaration start UTF-8 byte column",
        )
        _non_negative_int(
            self.end_utf8_byte_column,
            field="declaration end UTF-8 byte column",
        )
        if self.end_line < self.start_line:
            raise ValueError("declaration span is reversed")
        if (
            self.end_line == self.start_line
            and self.end_utf8_byte_column <= self.start_utf8_byte_column
        ):
            raise ValueError("same-line declaration span must be non-empty")


@dataclass(frozen=True, slots=True)
class RedactedExpression:
    present: bool
    category: RedactedExpressionCategory
    redacted: bool

    def __post_init__(self) -> None:
        if type(self.present) is not bool or type(self.redacted) is not bool:
            raise ValueError("redacted expression flags must be bool")
        if not self.present:
            if self.category is not RedactedExpressionCategory.ABSENT or self.redacted:
                raise ValueError("absent redacted expression has an invalid state")
        elif self.category is RedactedExpressionCategory.ABSENT or not self.redacted:
            raise ValueError("present redacted expression must be redacted")

    @classmethod
    def absent(cls) -> RedactedExpression:
        return cls(False, RedactedExpressionCategory.ABSENT, False)

    @classmethod
    def present_as(cls, category: RedactedExpressionCategory) -> RedactedExpression:
        if category is RedactedExpressionCategory.ABSENT:
            raise ValueError("a present expression cannot have the absent category")
        return cls(True, category, True)


@dataclass(frozen=True, slots=True)
class SqlAlchemyTypeDescriptor:
    category: SqlAlchemyTypeCategory
    name: str | None
    parameters: RedactedExpression

    def __post_init__(self) -> None:
        if self.name is not None:
            object.__setattr__(self, "name", safe_dotted_symbol(self.name, field="type name"))
        if self.category is not SqlAlchemyTypeCategory.UNKNOWN and self.name is None:
            raise ValueError("known SQLAlchemy type category requires a safe type name")


@dataclass(frozen=True, slots=True)
class SqlAlchemyIndexTerm:
    kind: IndexTermKind
    column_name: str | None
    expression: RedactedExpression

    def __post_init__(self) -> None:
        if self.kind is IndexTermKind.COLUMN:
            if self.column_name is None or self.expression.present:
                raise ValueError("column index term is invalid")
            object.__setattr__(
                self,
                "column_name",
                safe_structural_string(self.column_name, field="index column name"),
            )
        elif self.column_name is not None or not self.expression.present:
            raise ValueError("expression index term is invalid")

    @classmethod
    def column(cls, name: str) -> SqlAlchemyIndexTerm:
        return cls(IndexTermKind.COLUMN, name, RedactedExpression.absent())

    @classmethod
    def redacted_expression(cls, category: RedactedExpressionCategory) -> SqlAlchemyIndexTerm:
        return cls(IndexTermKind.EXPRESSION, None, RedactedExpression.present_as(category))


@dataclass(frozen=True, slots=True)
class SqlAlchemyRelationTarget:
    resolution: SqlAlchemyTargetResolution
    kind: SqlAlchemyTargetKind
    id: str | None
    schema_name: str | None
    table_name: str | None
    symbol: str | None
    display_name: str

    def __post_init__(self) -> None:
        schema_name = (
            safe_structural_string(self.schema_name, field="target schema name")
            if self.schema_name is not None
            else None
        )
        table_name = (
            safe_structural_string(self.table_name, field="target table name")
            if self.table_name is not None
            else None
        )
        symbol = (
            safe_dotted_symbol(self.symbol, field="target symbol")
            if self.symbol is not None
            else None
        )
        object.__setattr__(self, "schema_name", schema_name)
        object.__setattr__(self, "table_name", table_name)
        object.__setattr__(self, "symbol", symbol)
        if self.resolution is SqlAlchemyTargetResolution.INTERNAL:
            if (
                self.kind is not SqlAlchemyTargetKind.TABLE
                or self.id is None
                or table_name is None
                or symbol is not None
            ):
                raise ValueError("internal SQLAlchemy relation target is invalid")
            _validate_table_id(self.id)
            expected_display = _table_display(schema_name, table_name)
        elif self.resolution is SqlAlchemyTargetResolution.EXTERNAL:
            if self.id is not None:
                raise ValueError("external SQLAlchemy relation target cannot carry an id")
            if self.kind is SqlAlchemyTargetKind.TABLE:
                if table_name is None or symbol is not None:
                    raise ValueError("external table target is invalid")
                expected_display = _table_display(schema_name, table_name)
            elif self.kind is SqlAlchemyTargetKind.MAPPED_CLASS:
                if any(value is not None for value in (schema_name, table_name)) or symbol is None:
                    raise ValueError("external mapped-class target is invalid")
                expected_display = symbol
            else:
                raise ValueError("external unknown relation target is invalid")
        else:
            if self.kind is not SqlAlchemyTargetKind.UNKNOWN or any(
                value is not None for value in (self.id, schema_name, table_name, symbol)
            ):
                raise ValueError("unknown SQLAlchemy relation target is invalid")
            expected_display = "<unknown>"
        if self.display_name != expected_display:
            raise ValueError("SQLAlchemy relation target display name is invalid")

    @classmethod
    def internal_table(cls, table: SqlAlchemyTable) -> SqlAlchemyRelationTarget:
        return cls(
            SqlAlchemyTargetResolution.INTERNAL,
            SqlAlchemyTargetKind.TABLE,
            table.id,
            table.schema_name,
            table.name,
            None,
            table.display_name,
        )

    @classmethod
    def external_table(
        cls, *, schema_name: str | None, table_name: str
    ) -> SqlAlchemyRelationTarget:
        return cls(
            SqlAlchemyTargetResolution.EXTERNAL,
            SqlAlchemyTargetKind.TABLE,
            None,
            schema_name,
            table_name,
            None,
            _table_display(schema_name, table_name),
        )

    @classmethod
    def external_mapped_class(cls, symbol: str) -> SqlAlchemyRelationTarget:
        return cls(
            SqlAlchemyTargetResolution.EXTERNAL,
            SqlAlchemyTargetKind.MAPPED_CLASS,
            None,
            None,
            None,
            symbol,
            symbol,
        )

    @classmethod
    def unknown(cls) -> SqlAlchemyRelationTarget:
        return cls(
            SqlAlchemyTargetResolution.UNKNOWN,
            SqlAlchemyTargetKind.UNKNOWN,
            None,
            None,
            None,
            None,
            "<unknown>",
        )


def _table_display(schema_name: str | None, table_name: str) -> str:
    normalized_table = safe_structural_string(table_name, field="table name")
    if schema_name is None:
        return f"<default>.{normalized_table}"
    normalized_schema = safe_structural_string(schema_name, field="schema name")
    return f"{normalized_schema}.{normalized_table}"


def target_identity_value(target: SqlAlchemyRelationTarget) -> dict[str, object]:
    return {
        "resolution": target.resolution.value,
        "id": target.id,
        "schema_name": target.schema_name,
        "table_name": target.table_name,
        "symbol": target.symbol,
    }


@dataclass(frozen=True, slots=True)
class SqlAlchemyMappingSource:
    kind: SqlAlchemyMappingSourceKind
    module: str
    symbol: str
    source: SqlAlchemySourceLocation

    def __post_init__(self) -> None:
        object.__setattr__(self, "module", safe_dotted_symbol(self.module, field="module"))
        object.__setattr__(self, "symbol", safe_dotted_symbol(self.symbol, field="mapping symbol"))


def sqlalchemy_table_id(schema_name: str | None, table_name: str) -> str:
    normalized_schema = (
        safe_structural_string(schema_name, field="schema name")
        if schema_name is not None
        else None
    )
    normalized_table = safe_structural_string(table_name, field="table name")
    digest = _canonical_digest(
        {
            "schema": "code-structure-viz.sqlalchemy-table-id/v1",
            "schema_name": normalized_schema,
            "table_name": normalized_table,
        }
    )
    return f"sqlalchemy:table:{digest}"


@dataclass(frozen=True, slots=True)
class SqlAlchemyTable:
    id: str
    kind: Literal["table"]
    schema_name: str | None
    name: str
    display_name: str
    mapping_kind: SqlAlchemyMappingKind
    mapping_sources: tuple[SqlAlchemyMappingSource, ...]

    def __post_init__(self) -> None:
        schema_name = (
            safe_structural_string(self.schema_name, field="schema name")
            if self.schema_name is not None
            else None
        )
        name = safe_structural_string(self.name, field="table name")
        object.__setattr__(self, "schema_name", schema_name)
        object.__setattr__(self, "name", name)
        if self.kind != "table":
            raise ValueError("SQLAlchemy entity kind must be table")
        if self.id != sqlalchemy_table_id(schema_name, name):
            raise ValueError("SQLAlchemy table identity is invalid")
        if self.display_name != _table_display(schema_name, name):
            raise ValueError("SQLAlchemy table display name is invalid")
        if not self.mapping_sources:
            raise ValueError("SQLAlchemy table requires mapping provenance")
        if self.mapping_sources != tuple(sorted(self.mapping_sources, key=mapping_source_sort_key)):
            raise ValueError("SQLAlchemy mapping sources are not canonically ordered")
        if len(set(self.mapping_sources)) != len(self.mapping_sources):
            raise ValueError("SQLAlchemy mapping sources contain duplicates")
        source_kinds = {source.kind for source in self.mapping_sources}
        expected_mapping_kind = (
            SqlAlchemyMappingKind.MIXED
            if len(source_kinds) == 2
            else SqlAlchemyMappingKind.DECLARATIVE_CLASS
            if source_kinds == {SqlAlchemyMappingSourceKind.DECLARATIVE_CLASS}
            else SqlAlchemyMappingKind.TABLE
        )
        if self.mapping_kind is not expected_mapping_kind:
            raise ValueError("SQLAlchemy mapping kind does not match its provenance")

    @classmethod
    def create(
        cls,
        *,
        schema_name: str | None,
        name: str,
        mapping_sources: tuple[SqlAlchemyMappingSource, ...],
    ) -> SqlAlchemyTable:
        normalized_schema = (
            safe_structural_string(schema_name, field="schema name")
            if schema_name is not None
            else None
        )
        normalized_name = safe_structural_string(name, field="table name")
        sources = tuple(sorted(set(mapping_sources), key=mapping_source_sort_key))
        source_kinds = {source.kind for source in sources}
        mapping_kind = (
            SqlAlchemyMappingKind.MIXED
            if len(source_kinds) == 2
            else SqlAlchemyMappingKind.DECLARATIVE_CLASS
            if source_kinds == {SqlAlchemyMappingSourceKind.DECLARATIVE_CLASS}
            else SqlAlchemyMappingKind.TABLE
        )
        return cls(
            sqlalchemy_table_id(normalized_schema, normalized_name),
            "table",
            normalized_schema,
            normalized_name,
            _table_display(normalized_schema, normalized_name),
            mapping_kind,
            sources,
        )


def _normalized_columns(
    values: tuple[str, ...], *, field: str, sorted_set: bool
) -> tuple[str, ...]:
    normalized = tuple(safe_structural_string(value, field=field) for value in values)
    if not normalized:
        raise ValueError(f"{field} cannot be empty")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field} cannot contain duplicates")
    if sorted_set:
        normalized = tuple(sorted(normalized, key=_utf8))
    return normalized


def _normalize_optional_name(value: str | None, *, field: str = "row name") -> str | None:
    return safe_structural_string(value, field=field) if value is not None else None


def _validate_row_prefix(
    *,
    id: str,
    owner_id: str,
    kind: SqlAlchemyRowKind,
    expected_kind: SqlAlchemyRowKind,
    name: str | None,
) -> None:
    _validate_row_id(id)
    _validate_table_id(owner_id)
    if kind is not expected_kind:
        raise ValueError("SQLAlchemy row kind does not match its DTO")
    if name is not None:
        safe_structural_string(name, field="row name")


def sqlalchemy_row_id(
    owner_id: str,
    kind: SqlAlchemyRowKind,
    identity_key: dict[str, object],
) -> str:
    _validate_table_id(owner_id)
    digest = _canonical_digest(
        {
            "schema": "code-structure-viz.sqlalchemy-row-id/v1",
            "owner_id": owner_id,
            "kind": kind.value,
            "identity_key": identity_key,
        }
    )
    return f"sqlalchemy:row:{digest}"


def _row_id_for(value: SqlAlchemyRow) -> str:
    return sqlalchemy_row_id(value.owner_id, value.kind, row_identity_key(value))


@dataclass(frozen=True, slots=True)
class SqlAlchemyColumnRow:
    id: str
    owner_id: str
    kind: SqlAlchemyRowKind
    name: str | None
    source: SqlAlchemySourceLocation
    type: SqlAlchemyTypeDescriptor
    nullable: bool | None
    primary_key: bool | None
    unique: bool | None
    index: bool | None
    default: RedactedExpression
    server_default: RedactedExpression
    onupdate: RedactedExpression
    server_onupdate: RedactedExpression
    computed: RedactedExpression
    identity: RedactedExpression

    def __post_init__(self) -> None:
        _validate_row_prefix(
            id=self.id,
            owner_id=self.owner_id,
            kind=self.kind,
            expected_kind=SqlAlchemyRowKind.COLUMN,
            name=self.name,
        )
        if self.name is None:
            raise ValueError("SQLAlchemy column row requires a name")
        object.__setattr__(self, "name", safe_structural_string(self.name, field="column name"))
        for field_name in ("nullable", "primary_key", "unique", "index"):
            flag = getattr(self, field_name)
            if flag is not None and type(flag) is not bool:
                raise ValueError(f"column {field_name} must be bool or null")
        if self.id != _row_id_for(self):
            raise ValueError("SQLAlchemy column row identity is invalid")

    @classmethod
    def create(
        cls,
        *,
        owner_id: str,
        name: str,
        source: SqlAlchemySourceLocation,
        type: SqlAlchemyTypeDescriptor,
        nullable: bool | None = None,
        primary_key: bool | None = None,
        unique: bool | None = None,
        index: bool | None = None,
        default: RedactedExpression | None = None,
        server_default: RedactedExpression | None = None,
        onupdate: RedactedExpression | None = None,
        server_onupdate: RedactedExpression | None = None,
        computed: RedactedExpression | None = None,
        identity: RedactedExpression | None = None,
    ) -> SqlAlchemyColumnRow:
        normalized_name = safe_structural_string(name, field="column name")
        row_id = sqlalchemy_row_id(owner_id, SqlAlchemyRowKind.COLUMN, {"name": normalized_name})
        absent = RedactedExpression.absent
        return cls(
            row_id,
            owner_id,
            SqlAlchemyRowKind.COLUMN,
            normalized_name,
            source,
            type,
            nullable,
            primary_key,
            unique,
            index,
            default or absent(),
            server_default or absent(),
            onupdate or absent(),
            server_onupdate or absent(),
            computed or absent(),
            identity or absent(),
        )


@dataclass(frozen=True, slots=True)
class SqlAlchemyPrimaryKeyRow:
    id: str
    owner_id: str
    kind: SqlAlchemyRowKind
    name: str | None
    source: SqlAlchemySourceLocation
    columns: tuple[str, ...]

    def __post_init__(self) -> None:
        _validate_row_prefix(
            id=self.id,
            owner_id=self.owner_id,
            kind=self.kind,
            expected_kind=SqlAlchemyRowKind.PRIMARY_KEY,
            name=self.name,
        )
        object.__setattr__(self, "name", _normalize_optional_name(self.name))
        object.__setattr__(
            self,
            "columns",
            _normalized_columns(self.columns, field="primary-key columns", sorted_set=True),
        )
        if self.id != _row_id_for(self):
            raise ValueError("SQLAlchemy primary-key row identity is invalid")

    @classmethod
    def create(
        cls,
        *,
        owner_id: str,
        name: str | None,
        source: SqlAlchemySourceLocation,
        columns: tuple[str, ...],
    ) -> SqlAlchemyPrimaryKeyRow:
        normalized_name = _normalize_optional_name(name)
        normalized_columns = _normalized_columns(
            columns, field="primary-key columns", sorted_set=True
        )
        identity_key: dict[str, object] = (
            {"name": normalized_name}
            if normalized_name is not None
            else {"columns": list(normalized_columns)}
        )
        return cls(
            sqlalchemy_row_id(owner_id, SqlAlchemyRowKind.PRIMARY_KEY, identity_key),
            owner_id,
            SqlAlchemyRowKind.PRIMARY_KEY,
            normalized_name,
            source,
            normalized_columns,
        )


@dataclass(frozen=True, slots=True)
class SqlAlchemyUniqueRow:
    id: str
    owner_id: str
    kind: SqlAlchemyRowKind
    name: str | None
    source: SqlAlchemySourceLocation
    columns: tuple[str, ...]

    def __post_init__(self) -> None:
        _validate_row_prefix(
            id=self.id,
            owner_id=self.owner_id,
            kind=self.kind,
            expected_kind=SqlAlchemyRowKind.UNIQUE,
            name=self.name,
        )
        object.__setattr__(self, "name", _normalize_optional_name(self.name))
        object.__setattr__(
            self,
            "columns",
            _normalized_columns(self.columns, field="unique columns", sorted_set=True),
        )
        if self.id != _row_id_for(self):
            raise ValueError("SQLAlchemy unique row identity is invalid")

    @classmethod
    def create(
        cls,
        *,
        owner_id: str,
        name: str | None,
        source: SqlAlchemySourceLocation,
        columns: tuple[str, ...],
    ) -> SqlAlchemyUniqueRow:
        normalized_name = _normalize_optional_name(name)
        normalized_columns = _normalized_columns(columns, field="unique columns", sorted_set=True)
        identity_key: dict[str, object] = (
            {"name": normalized_name}
            if normalized_name is not None
            else {"columns": list(normalized_columns)}
        )
        return cls(
            sqlalchemy_row_id(owner_id, SqlAlchemyRowKind.UNIQUE, identity_key),
            owner_id,
            SqlAlchemyRowKind.UNIQUE,
            normalized_name,
            source,
            normalized_columns,
        )


@dataclass(frozen=True, slots=True)
class SqlAlchemyCheckRow:
    id: str
    owner_id: str
    kind: SqlAlchemyRowKind
    name: str | None
    source: SqlAlchemySourceLocation
    expression: RedactedExpression

    def __post_init__(self) -> None:
        _validate_row_prefix(
            id=self.id,
            owner_id=self.owner_id,
            kind=self.kind,
            expected_kind=SqlAlchemyRowKind.CHECK,
            name=self.name,
        )
        object.__setattr__(self, "name", _normalize_optional_name(self.name))
        if not self.expression.present or self.expression.category not in {
            RedactedExpressionCategory.SQL_EXPRESSION,
            RedactedExpressionCategory.LITERAL,
            RedactedExpressionCategory.UNKNOWN,
        }:
            raise ValueError("SQLAlchemy check expression descriptor is invalid")
        if self.id != _row_id_for(self):
            raise ValueError("SQLAlchemy check row identity is invalid")

    @classmethod
    def create(
        cls,
        *,
        owner_id: str,
        name: str | None,
        source: SqlAlchemySourceLocation,
        expression: RedactedExpression,
    ) -> SqlAlchemyCheckRow:
        normalized_name = _normalize_optional_name(name)
        identity_key: dict[str, object] = (
            {"name": normalized_name}
            if normalized_name is not None
            else {"expression_category": expression.category.value}
        )
        return cls(
            sqlalchemy_row_id(owner_id, SqlAlchemyRowKind.CHECK, identity_key),
            owner_id,
            SqlAlchemyRowKind.CHECK,
            normalized_name,
            source,
            expression,
        )


@dataclass(frozen=True, slots=True)
class SqlAlchemyIndexRow:
    id: str
    owner_id: str
    kind: SqlAlchemyRowKind
    name: str | None
    source: SqlAlchemySourceLocation
    unique: bool | None
    terms: tuple[SqlAlchemyIndexTerm, ...]

    def __post_init__(self) -> None:
        _validate_row_prefix(
            id=self.id,
            owner_id=self.owner_id,
            kind=self.kind,
            expected_kind=SqlAlchemyRowKind.INDEX,
            name=self.name,
        )
        object.__setattr__(self, "name", _normalize_optional_name(self.name))
        if self.unique is not None and type(self.unique) is not bool:
            raise ValueError("SQLAlchemy index unique flag must be bool or null")
        if not self.terms:
            raise ValueError("SQLAlchemy index requires at least one term")
        if self.id != _row_id_for(self):
            raise ValueError("SQLAlchemy index row identity is invalid")

    @classmethod
    def create(
        cls,
        *,
        owner_id: str,
        name: str | None,
        source: SqlAlchemySourceLocation,
        unique: bool | None,
        terms: tuple[SqlAlchemyIndexTerm, ...],
    ) -> SqlAlchemyIndexRow:
        normalized_name = _normalize_optional_name(name)
        identity_key: dict[str, object] = (
            {"name": normalized_name}
            if normalized_name is not None
            else {
                "unique": unique,
                "terms": [_index_term_identity(term) for term in terms],
            }
        )
        return cls(
            sqlalchemy_row_id(owner_id, SqlAlchemyRowKind.INDEX, identity_key),
            owner_id,
            SqlAlchemyRowKind.INDEX,
            normalized_name,
            source,
            unique,
            terms,
        )


@dataclass(frozen=True, slots=True)
class SqlAlchemyForeignKeyRow:
    id: str
    owner_id: str
    kind: SqlAlchemyRowKind
    name: str | None
    source: SqlAlchemySourceLocation
    local_columns: tuple[str, ...]
    target: SqlAlchemyRelationTarget
    target_columns: tuple[str, ...]
    ondelete: RedactedExpression
    onupdate: RedactedExpression

    def __post_init__(self) -> None:
        _validate_row_prefix(
            id=self.id,
            owner_id=self.owner_id,
            kind=self.kind,
            expected_kind=SqlAlchemyRowKind.FOREIGN_KEY,
            name=self.name,
        )
        object.__setattr__(self, "name", _normalize_optional_name(self.name))
        local = _normalized_columns(
            self.local_columns, field="foreign-key local columns", sorted_set=False
        )
        target = _normalized_columns(
            self.target_columns, field="foreign-key target columns", sorted_set=False
        )
        if len(local) != len(target):
            raise ValueError("foreign-key local and target column counts differ")
        object.__setattr__(self, "local_columns", local)
        object.__setattr__(self, "target_columns", target)
        if self.id != _row_id_for(self):
            raise ValueError("SQLAlchemy foreign-key row identity is invalid")

    @classmethod
    def create(
        cls,
        *,
        owner_id: str,
        name: str | None,
        source: SqlAlchemySourceLocation,
        local_columns: tuple[str, ...],
        target: SqlAlchemyRelationTarget,
        target_columns: tuple[str, ...],
        ondelete: RedactedExpression | None = None,
        onupdate: RedactedExpression | None = None,
    ) -> SqlAlchemyForeignKeyRow:
        normalized_name = _normalize_optional_name(name)
        local = _normalized_columns(
            local_columns, field="foreign-key local columns", sorted_set=False
        )
        remote = _normalized_columns(
            target_columns, field="foreign-key target columns", sorted_set=False
        )
        identity_key: dict[str, object] = (
            {"name": normalized_name}
            if normalized_name is not None
            else {
                "local_columns": list(local),
                "target": target_identity_value(target),
                "target_columns": list(remote),
            }
        )
        return cls(
            sqlalchemy_row_id(owner_id, SqlAlchemyRowKind.FOREIGN_KEY, identity_key),
            owner_id,
            SqlAlchemyRowKind.FOREIGN_KEY,
            normalized_name,
            source,
            local,
            target,
            remote,
            ondelete or RedactedExpression.absent(),
            onupdate or RedactedExpression.absent(),
        )


@dataclass(frozen=True, slots=True)
class SqlAlchemyRelationshipRow:
    id: str
    owner_id: str
    kind: SqlAlchemyRowKind
    name: str | None
    source: SqlAlchemySourceLocation
    target: SqlAlchemyRelationTarget
    cardinality: SqlAlchemyCardinality
    uselist: bool | None
    back_populates: str | None
    secondary: SqlAlchemyRelationTarget | None
    primaryjoin: RedactedExpression
    secondaryjoin: RedactedExpression
    order_by: RedactedExpression
    foreign_keys: RedactedExpression

    def __post_init__(self) -> None:
        _validate_row_prefix(
            id=self.id,
            owner_id=self.owner_id,
            kind=self.kind,
            expected_kind=SqlAlchemyRowKind.RELATIONSHIP,
            name=self.name,
        )
        if self.name is None:
            raise ValueError("SQLAlchemy relationship row requires a name")
        object.__setattr__(
            self, "name", safe_structural_string(self.name, field="relationship name")
        )
        if self.uselist is not None and type(self.uselist) is not bool:
            raise ValueError("relationship uselist must be bool or null")
        if self.back_populates is not None:
            object.__setattr__(
                self,
                "back_populates",
                safe_structural_string(self.back_populates, field="back_populates"),
            )
        if self.id != _row_id_for(self):
            raise ValueError("SQLAlchemy relationship row identity is invalid")

    @classmethod
    def create(
        cls,
        *,
        owner_id: str,
        name: str,
        source: SqlAlchemySourceLocation,
        target: SqlAlchemyRelationTarget,
        cardinality: SqlAlchemyCardinality,
        uselist: bool | None,
        back_populates: str | None,
        secondary: SqlAlchemyRelationTarget | None,
        primaryjoin: RedactedExpression | None = None,
        secondaryjoin: RedactedExpression | None = None,
        order_by: RedactedExpression | None = None,
        foreign_keys: RedactedExpression | None = None,
    ) -> SqlAlchemyRelationshipRow:
        normalized_name = safe_structural_string(name, field="relationship name")
        return cls(
            sqlalchemy_row_id(owner_id, SqlAlchemyRowKind.RELATIONSHIP, {"name": normalized_name}),
            owner_id,
            SqlAlchemyRowKind.RELATIONSHIP,
            normalized_name,
            source,
            target,
            cardinality,
            uselist,
            back_populates,
            secondary,
            primaryjoin or RedactedExpression.absent(),
            secondaryjoin or RedactedExpression.absent(),
            order_by or RedactedExpression.absent(),
            foreign_keys or RedactedExpression.absent(),
        )


@dataclass(frozen=True, slots=True)
class SqlAlchemyInheritanceRow:
    id: str
    owner_id: str
    kind: SqlAlchemyRowKind
    name: str | None
    source: SqlAlchemySourceLocation
    target: SqlAlchemyRelationTarget

    def __post_init__(self) -> None:
        _validate_row_prefix(
            id=self.id,
            owner_id=self.owner_id,
            kind=self.kind,
            expected_kind=SqlAlchemyRowKind.INHERITANCE,
            name=self.name,
        )
        if (
            self.name is not None
            or self.target.resolution is not SqlAlchemyTargetResolution.INTERNAL
        ):
            raise ValueError("SQLAlchemy inheritance row is invalid")
        if self.target.id == self.owner_id:
            raise ValueError("SQLAlchemy inheritance cannot target its owner")
        if self.id != _row_id_for(self):
            raise ValueError("SQLAlchemy inheritance row identity is invalid")

    @classmethod
    def create(
        cls,
        *,
        owner_id: str,
        source: SqlAlchemySourceLocation,
        target: SqlAlchemyRelationTarget,
    ) -> SqlAlchemyInheritanceRow:
        return cls(
            sqlalchemy_row_id(
                owner_id,
                SqlAlchemyRowKind.INHERITANCE,
                {"target": target_identity_value(target)},
            ),
            owner_id,
            SqlAlchemyRowKind.INHERITANCE,
            None,
            source,
            target,
        )


@dataclass(frozen=True, slots=True)
class SqlAlchemyAssociationTableRow:
    id: str
    owner_id: str
    kind: SqlAlchemyRowKind
    name: str | None
    source: SqlAlchemySourceLocation
    source_table: SqlAlchemyRelationTarget
    relationship_target: SqlAlchemyRelationTarget
    relationship_member_id: str

    def __post_init__(self) -> None:
        _validate_row_prefix(
            id=self.id,
            owner_id=self.owner_id,
            kind=self.kind,
            expected_kind=SqlAlchemyRowKind.ASSOCIATION_TABLE,
            name=self.name,
        )
        if self.name is None:
            raise ValueError("association-table row requires the relationship name")
        object.__setattr__(
            self, "name", safe_structural_string(self.name, field="relationship name")
        )
        if (
            self.source_table.resolution is not SqlAlchemyTargetResolution.INTERNAL
            or self.source_table.id == self.owner_id
        ):
            raise ValueError("association-table source target is invalid")
        _validate_row_id(self.relationship_member_id)
        if self.id != _row_id_for(self):
            raise ValueError("SQLAlchemy association-table row identity is invalid")

    @classmethod
    def create(
        cls,
        *,
        owner_id: str,
        name: str,
        source: SqlAlchemySourceLocation,
        source_table: SqlAlchemyRelationTarget,
        relationship_target: SqlAlchemyRelationTarget,
        relationship_member_id: str,
    ) -> SqlAlchemyAssociationTableRow:
        normalized_name = safe_structural_string(name, field="relationship name")
        return cls(
            sqlalchemy_row_id(
                owner_id,
                SqlAlchemyRowKind.ASSOCIATION_TABLE,
                {
                    "source_table": target_identity_value(source_table),
                    "relationship_member_id": relationship_member_id,
                },
            ),
            owner_id,
            SqlAlchemyRowKind.ASSOCIATION_TABLE,
            normalized_name,
            source,
            source_table,
            relationship_target,
            relationship_member_id,
        )


type SqlAlchemyRow = (
    SqlAlchemyColumnRow
    | SqlAlchemyPrimaryKeyRow
    | SqlAlchemyUniqueRow
    | SqlAlchemyCheckRow
    | SqlAlchemyIndexRow
    | SqlAlchemyForeignKeyRow
    | SqlAlchemyRelationshipRow
    | SqlAlchemyInheritanceRow
    | SqlAlchemyAssociationTableRow
)


def _index_term_identity(value: SqlAlchemyIndexTerm) -> dict[str, object]:
    if value.kind is IndexTermKind.COLUMN:
        return {"kind": "column", "column_name": value.column_name}
    return {
        "kind": "expression",
        "expression_category": value.expression.category.value,
    }


def row_identity_key(value: SqlAlchemyRow) -> dict[str, object]:
    if value.kind is SqlAlchemyRowKind.COLUMN:
        return {"name": value.name}
    if (
        value.kind
        in {
            SqlAlchemyRowKind.PRIMARY_KEY,
            SqlAlchemyRowKind.UNIQUE,
            SqlAlchemyRowKind.CHECK,
            SqlAlchemyRowKind.INDEX,
            SqlAlchemyRowKind.FOREIGN_KEY,
        }
        and value.name is not None
    ):
        return {"name": value.name}
    if isinstance(value, (SqlAlchemyPrimaryKeyRow, SqlAlchemyUniqueRow)):
        return {"columns": list(value.columns)}
    if isinstance(value, SqlAlchemyCheckRow):
        return {"expression_category": value.expression.category.value}
    if isinstance(value, SqlAlchemyIndexRow):
        return {
            "unique": value.unique,
            "terms": [_index_term_identity(term) for term in value.terms],
        }
    if isinstance(value, SqlAlchemyForeignKeyRow):
        return {
            "local_columns": list(value.local_columns),
            "target": target_identity_value(value.target),
            "target_columns": list(value.target_columns),
        }
    if isinstance(value, SqlAlchemyRelationshipRow):
        return {"name": value.name}
    if isinstance(value, SqlAlchemyInheritanceRow):
        return {"target": target_identity_value(value.target)}
    if isinstance(value, SqlAlchemyAssociationTableRow):
        return {
            "source_table": target_identity_value(value.source_table),
            "relationship_member_id": value.relationship_member_id,
        }
    raise TypeError("unknown SQLAlchemy row DTO")


@dataclass(frozen=True, slots=True)
class SqlAlchemyRowEvidence:
    row: SqlAlchemyRow
    declaration_span: SqlAlchemyInternalDeclarationSpan

    def __post_init__(self) -> None:
        if (
            self.row.source.range.start_line != self.declaration_span.start_line
            or self.row.source.range.end_line != self.declaration_span.end_line
        ):
            raise ValueError("public row range and internal declaration span differ")


def sqlalchemy_occurrence_diagnostic_symbol(
    owner_id: str,
    kind: SqlAlchemyRowKind,
    path: str,
    span: SqlAlchemyInternalDeclarationSpan,
) -> str:
    _validate_table_id(owner_id)
    normalized_path = safe_repository_path(path)
    digest = _canonical_digest(
        {
            "schema": "code-structure-viz.sqlalchemy-occurrence-diagnostic-symbol/v1",
            "owner_id": owner_id,
            "kind": kind.value,
            "path": normalized_path,
            "span": {
                "start_line": span.start_line,
                "start_utf8_byte_column": span.start_utf8_byte_column,
                "end_line": span.end_line,
                "end_utf8_byte_column": span.end_utf8_byte_column,
            },
        }
    )
    return f"sqlalchemy:occurrence:{digest}"


def _occurrence_key(value: SqlAlchemyRowEvidence) -> tuple[object, ...]:
    span = value.declaration_span
    return (
        value.row.owner_id,
        value.row.kind,
        value.row.source.path,
        span.start_line,
        span.start_utf8_byte_column,
        span.end_line,
        span.end_utf8_byte_column,
    )


def _semantic_payload(value: SqlAlchemyRow | SqlAlchemyRelation) -> tuple[object, ...]:
    return tuple(
        getattr(value, field.name) for field in fields(value) if field.name not in {"id", "source"}
    )


def _source_sort_key(value: SqlAlchemySourceLocation) -> tuple[bytes, int, int]:
    return _utf8(value.path), value.range.start_line, value.range.end_line


def _lossy_identity(value: SqlAlchemyRow) -> bool:
    return (isinstance(value, SqlAlchemyCheckRow) and value.name is None) or (
        isinstance(value, SqlAlchemyIndexRow)
        and value.name is None
        and any(term.kind is IndexTermKind.EXPRESSION for term in value.terms)
    )


def canonicalize_row_evidence(
    values: tuple[SqlAlchemyRowEvidence, ...],
) -> tuple[tuple[SqlAlchemyRow, ...], tuple[Diagnostic, ...]]:
    groups: dict[str, list[SqlAlchemyRowEvidence]] = {}
    for value in values:
        groups.setdefault(value.row.id, []).append(value)

    rows: list[SqlAlchemyRow] = []
    diagnostics: list[Diagnostic] = []
    for row_id in sorted(groups, key=_utf8):
        group = groups[row_id]
        representative = group[0].row
        occurrences: dict[tuple[object, ...], list[SqlAlchemyRowEvidence]] = {}
        for item in group:
            occurrences.setdefault(_occurrence_key(item), []).append(item)

        if _lossy_identity(representative):
            occurrence_payloads = {
                key: {_semantic_payload(item.row) for item in occurrence}
                for key, occurrence in occurrences.items()
            }
            conflict = len(occurrences) > 1 or any(
                len(payloads) != 1 for payloads in occurrence_payloads.values()
            )
        else:
            conflict = len({_semantic_payload(item.row) for item in group}) != 1

        if not conflict:
            rows.append(
                min((item.row for item in group), key=lambda row: _source_sort_key(row.source))
            )
            continue

        for occurrence in occurrences.values():
            item = min(
                occurrence,
                key=lambda evidence: (
                    _source_sort_key(evidence.row.source),
                    evidence.declaration_span.start_utf8_byte_column,
                    evidence.declaration_span.end_utf8_byte_column,
                ),
            )
            diagnostics.append(
                diagnostic(
                    DiagnosticCode.SA_ROW_UNREPRESENTABLE,
                    domain="sqlalchemy",
                    path=item.row.source.path,
                    symbol=sqlalchemy_occurrence_diagnostic_symbol(
                        item.row.owner_id,
                        item.row.kind,
                        item.row.source.path,
                        item.declaration_span,
                    ),
                    line=item.declaration_span.start_line,
                )
            )
    return tuple(sorted(rows, key=row_sort_key)), canonical_diagnostics(tuple(diagnostics))


def sqlalchemy_relation_id(
    *,
    kind: SqlAlchemyRelationKind,
    source_id: str,
    target: SqlAlchemyRelationTarget,
    via_member_id: str | None,
    role: str | None,
) -> str:
    _validate_table_id(source_id)
    if via_member_id is not None:
        _validate_row_id(via_member_id)
    normalized_role = (
        safe_structural_string(role, field="relation role") if role is not None else None
    )
    digest = _canonical_digest(
        {
            "schema": "code-structure-viz.sqlalchemy-relation-id/v1",
            "kind": kind.value,
            "source_id": source_id,
            "target": target_identity_value(target),
            "via_member_id": via_member_id,
            "role": normalized_role,
        }
    )
    return f"sqlalchemy:relation:{digest}"


@dataclass(frozen=True, slots=True)
class SqlAlchemyRelation:
    id: str
    kind: SqlAlchemyRelationKind
    source_id: str
    target: SqlAlchemyRelationTarget
    via_member_id: str | None
    role: str | None
    source: SqlAlchemySourceLocation

    def __post_init__(self) -> None:
        _validate_relation_id(self.id)
        _validate_table_id(self.source_id)
        if self.via_member_id is not None:
            _validate_row_id(self.via_member_id)
        if self.role is not None:
            object.__setattr__(
                self, "role", safe_structural_string(self.role, field="relation role")
            )
        if self.id != sqlalchemy_relation_id(
            kind=self.kind,
            source_id=self.source_id,
            target=self.target,
            via_member_id=self.via_member_id,
            role=self.role,
        ):
            raise ValueError("SQLAlchemy relation identity is invalid")
        if self.target.resolution is not SqlAlchemyTargetResolution.INTERNAL:
            raise ValueError("SQLAlchemy relation requires an internal target")
        if self.kind is SqlAlchemyRelationKind.FOREIGN_KEY:
            if self.via_member_id is None or self.role is not None:
                raise ValueError("foreign-key relation requires a member and null role")
        elif self.kind in {
            SqlAlchemyRelationKind.RELATIONSHIP,
            SqlAlchemyRelationKind.ASSOCIATION,
        }:
            if self.via_member_id is None or self.role is None:
                raise ValueError("relationship/association relation requires a member and role")
        elif any(value is not None for value in (self.via_member_id, self.role)):
            raise ValueError("inheritance relation cannot have a member or role")

    @classmethod
    def create(
        cls,
        *,
        kind: SqlAlchemyRelationKind,
        source_id: str,
        target: SqlAlchemyRelationTarget,
        via_member_id: str | None,
        role: str | None,
        source: SqlAlchemySourceLocation,
    ) -> SqlAlchemyRelation:
        return cls(
            sqlalchemy_relation_id(
                kind=kind,
                source_id=source_id,
                target=target,
                via_member_id=via_member_id,
                role=role,
            ),
            kind,
            source_id,
            target,
            via_member_id,
            role,
            source,
        )


def canonicalize_relations(
    values: tuple[SqlAlchemyRelation, ...],
) -> tuple[tuple[SqlAlchemyRelation, ...], tuple[str, ...]]:
    groups: dict[str, list[SqlAlchemyRelation]] = {}
    for value in values:
        groups.setdefault(value.id, []).append(value)
    relations: list[SqlAlchemyRelation] = []
    conflicts: list[str] = []
    for relation_id in sorted(groups, key=_utf8):
        group = groups[relation_id]
        if len({_semantic_payload(value) for value in group}) != 1:
            conflicts.append(relation_id)
            continue
        relations.append(min(group, key=lambda value: _source_sort_key(value.source)))
    return tuple(sorted(relations, key=relation_sort_key)), tuple(conflicts)


@dataclass(frozen=True, slots=True)
class SqlAlchemyFailedSource:
    path: str
    stage: SqlAlchemyFailedStage
    diagnostic_code: DiagnosticCode

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", safe_repository_path(self.path))
        allowed = {
            SqlAlchemyFailedStage.READ: DiagnosticCode.SA_READ,
            SqlAlchemyFailedStage.PATH_SAFETY: DiagnosticCode.SA_READ,
            SqlAlchemyFailedStage.ENCODING: DiagnosticCode.SA_ENCODING,
            SqlAlchemyFailedStage.PARSE: DiagnosticCode.SA_PARSE,
            SqlAlchemyFailedStage.MODULE_IDENTITY: DiagnosticCode.SA_MODULE_IDENTITY,
            SqlAlchemyFailedStage.MODULE_COLLISION: DiagnosticCode.SA_MODULE_COLLISION,
        }
        if self.diagnostic_code is not allowed[self.stage]:
            raise ValueError("SQLAlchemy failed-source stage/code pair is invalid")


@dataclass(frozen=True, slots=True)
class SqlAlchemyCoverageFrontier:
    direction: SqlAlchemyFrontierDirection
    kind: SqlAlchemyFrontierKind
    reference: str
    reason: SqlAlchemyFrontierReason

    def __post_init__(self) -> None:
        object.__setattr__(self, "reference", _safe_frontier_reference(self.reference))


@dataclass(frozen=True, slots=True)
class SqlAlchemyRedactionSummary:
    rule_version: str
    redacted_values: int

    def __post_init__(self) -> None:
        if self.rule_version != _REDACTION_RULE:
            raise ValueError("SQLAlchemy redaction rule version is invalid")
        _non_negative_int(self.redacted_values, field="redacted value count")

    @classmethod
    def create(cls, redacted_values: int) -> SqlAlchemyRedactionSummary:
        return cls(_REDACTION_RULE, redacted_values)


@dataclass(frozen=True, slots=True)
class SqlAlchemyCoverage:
    candidate_files: int
    parsed_files: int
    failed_files: tuple[SqlAlchemyFailedSource, ...]
    evidence_files: tuple[str, ...]
    selected_modules: tuple[str, ...]
    mapped_classes: int
    association_tables: int
    selected_entities: int
    unknown_declarations: int
    frontier: tuple[SqlAlchemyCoverageFrontier, ...]
    redaction: SqlAlchemyRedactionSummary

    def __post_init__(self) -> None:
        for field_name in (
            "candidate_files",
            "parsed_files",
            "mapped_classes",
            "association_tables",
            "selected_entities",
            "unknown_declarations",
        ):
            _non_negative_int(getattr(self, field_name), field=field_name)
        if self.parsed_files > self.candidate_files:
            raise ValueError("parsed SQLAlchemy files exceed candidate files")
        evidence_files = tuple(
            safe_repository_path(value, field="evidence path") for value in self.evidence_files
        )
        selected_modules = tuple(
            safe_dotted_symbol(value, field="selected module") for value in self.selected_modules
        )
        if evidence_files != tuple(sorted(set(evidence_files), key=_utf8)):
            raise ValueError("SQLAlchemy evidence files are not canonical")
        if selected_modules != tuple(sorted(set(selected_modules), key=_utf8)):
            raise ValueError("SQLAlchemy selected modules are not canonical")
        if self.failed_files != tuple(sorted(self.failed_files, key=failed_source_sort_key)):
            raise ValueError("SQLAlchemy failed files are not canonical")
        if self.frontier != tuple(sorted(set(self.frontier), key=frontier_sort_key)):
            raise ValueError("SQLAlchemy coverage frontier is not canonical")


def _redacted_expression_is_unknown(value: RedactedExpression) -> bool:
    return value.category is RedactedExpressionCategory.UNKNOWN


def _target_is_unknown(value: SqlAlchemyRelationTarget | None) -> bool:
    return value is not None and value.resolution is SqlAlchemyTargetResolution.UNKNOWN


def _row_has_unknown_value(value: SqlAlchemyRow) -> bool:
    descriptors: tuple[RedactedExpression, ...] = ()
    if isinstance(value, SqlAlchemyColumnRow):
        if value.type.category is SqlAlchemyTypeCategory.UNKNOWN:
            return True
        descriptors = (
            value.type.parameters,
            value.default,
            value.server_default,
            value.onupdate,
            value.server_onupdate,
            value.computed,
            value.identity,
        )
    elif isinstance(value, SqlAlchemyCheckRow):
        descriptors = (value.expression,)
    elif isinstance(value, SqlAlchemyIndexRow):
        descriptors = tuple(term.expression for term in value.terms)
    elif isinstance(value, SqlAlchemyForeignKeyRow):
        if _target_is_unknown(value.target):
            return True
        descriptors = (value.ondelete, value.onupdate)
    elif isinstance(value, SqlAlchemyRelationshipRow):
        if (
            _target_is_unknown(value.target)
            or _target_is_unknown(value.secondary)
            or value.cardinality is SqlAlchemyCardinality.UNKNOWN
        ):
            return True
        descriptors = (
            value.primaryjoin,
            value.secondaryjoin,
            value.order_by,
            value.foreign_keys,
        )
    elif isinstance(value, SqlAlchemyAssociationTableRow) and _target_is_unknown(
        value.relationship_target
    ):
        return True
    return any(_redacted_expression_is_unknown(item) for item in descriptors)


def _validate_relation_member(
    relation: SqlAlchemyRelation,
    members_by_id: dict[str, SqlAlchemyRow],
) -> None:
    if relation.kind is SqlAlchemyRelationKind.INHERITANCE:
        matches = [
            member
            for member in members_by_id.values()
            if isinstance(member, SqlAlchemyInheritanceRow)
            and member.owner_id == relation.source_id
            and member.target == relation.target
            and member.source == relation.source
        ]
        if len(matches) != 1:
            raise ValueError("inheritance relation has no matching inheritance row")
        return

    assert relation.via_member_id is not None
    member = members_by_id[relation.via_member_id]
    if relation.kind is SqlAlchemyRelationKind.FOREIGN_KEY:
        if not (
            isinstance(member, SqlAlchemyForeignKeyRow)
            and member.owner_id == relation.source_id
            and member.target == relation.target
            and member.source == relation.source
        ):
            raise ValueError("foreign-key relation member is inconsistent")
        return
    if relation.kind is SqlAlchemyRelationKind.RELATIONSHIP:
        if not (
            isinstance(member, SqlAlchemyRelationshipRow)
            and member.owner_id == relation.source_id
            and member.target == relation.target
            and member.name == relation.role
            and member.source == relation.source
        ):
            raise ValueError("relationship relation member is inconsistent")
        return

    if not isinstance(member, SqlAlchemyAssociationTableRow):
        raise ValueError("association relation member is inconsistent")
    relationship = members_by_id.get(member.relationship_member_id)
    if not (
        member.owner_id == relation.target.id
        and member.source_table.id == relation.source_id
        and member.name == relation.role
        and member.source == relation.source
        and isinstance(relationship, SqlAlchemyRelationshipRow)
        and relationship.owner_id == relation.source_id
        and relationship.name == member.name
        and relationship.target == member.relationship_target
        and relationship.secondary is not None
        and relationship.secondary.resolution is SqlAlchemyTargetResolution.INTERNAL
        and relationship.secondary.id == member.owner_id
    ):
        raise ValueError("association relation member is inconsistent")


@dataclass(frozen=True, slots=True)
class SqlAlchemySnapshot:
    entities: tuple[SqlAlchemyTable, ...]
    members: tuple[SqlAlchemyRow, ...]
    relations: tuple[SqlAlchemyRelation, ...]
    coverage: SqlAlchemyCoverage
    diagnostics: tuple[Diagnostic, ...]
    partial_safe: bool

    def __post_init__(self) -> None:
        if type(self.partial_safe) is not bool:
            raise ValueError("SQLAlchemy partial-safe marker must be bool")
        if self.entities != tuple(sorted(self.entities, key=table_sort_key)):
            raise ValueError("SQLAlchemy tables are not canonically ordered")
        if self.members != tuple(sorted(self.members, key=row_sort_key)):
            raise ValueError("SQLAlchemy rows are not canonically ordered")
        if self.relations != tuple(sorted(self.relations, key=relation_sort_key)):
            raise ValueError("SQLAlchemy relations are not canonically ordered")
        if self.diagnostics != canonical_diagnostics(self.diagnostics):
            raise ValueError("SQLAlchemy diagnostics are not canonical")
        if len({value.id for value in self.entities}) != len(self.entities):
            raise ValueError("SQLAlchemy table ids are not unique")
        if len({value.id for value in self.members}) != len(self.members):
            raise ValueError("SQLAlchemy row ids are not unique")
        if len({value.id for value in self.relations}) != len(self.relations):
            raise ValueError("SQLAlchemy relation ids are not unique")
        entity_ids = {value.id for value in self.entities}
        member_ids = {value.id for value in self.members}
        members_by_id = {value.id: value for value in self.members}
        if any(value.owner_id not in entity_ids for value in self.members):
            raise ValueError("SQLAlchemy row owner is absent from the snapshot")
        if any(value.source_id not in entity_ids for value in self.relations):
            raise ValueError("SQLAlchemy relation source is absent from the snapshot")
        if any(value.target.id not in entity_ids for value in self.relations):
            raise ValueError("SQLAlchemy internal relation target is absent from the snapshot")
        if any(
            value.via_member_id is not None and value.via_member_id not in member_ids
            for value in self.relations
        ):
            raise ValueError("SQLAlchemy relation member is absent from the snapshot")
        if self.coverage.selected_entities != len(self.entities):
            raise ValueError("SQLAlchemy selected-entity coverage is inconsistent")
        if self.coverage.redaction.redacted_values != redacted_value_count(self.members):
            raise ValueError("SQLAlchemy redaction coverage is inconsistent")
        for relation in self.relations:
            _validate_relation_member(relation, members_by_id)
        if not self.partial_safe:
            if self.coverage.failed_files:
                raise ValueError("complete SQLAlchemy snapshot cannot carry failed files")
            if self.coverage.unknown_declarations:
                raise ValueError("complete SQLAlchemy snapshot cannot carry unknown declarations")
            if self.diagnostics:
                raise ValueError("complete SQLAlchemy snapshot cannot carry diagnostics")
            if any(
                item.direction is SqlAlchemyFrontierDirection.FAILURE
                for item in self.coverage.frontier
            ):
                raise ValueError("complete SQLAlchemy snapshot cannot carry a failure frontier")
            if any(
                item.direction
                not in {
                    SqlAlchemyFrontierDirection.UPSTREAM,
                    SqlAlchemyFrontierDirection.DOWNSTREAM,
                }
                or item.reason is not SqlAlchemyFrontierReason.DEPTH_LIMIT
                for item in self.coverage.frontier
            ):
                raise ValueError(
                    "complete SQLAlchemy snapshot frontier must be a depth-limit frontier"
                )
            if any(_row_has_unknown_value(row) for row in self.members):
                raise ValueError("complete snapshot contains an unknown SQLAlchemy value")


def table_sort_key(value: SqlAlchemyTable) -> tuple[object, ...]:
    return (
        value.schema_name is not None,
        _utf8(value.schema_name or ""),
        _utf8(value.name),
        _utf8(value.id),
    )


def mapping_source_sort_key(value: SqlAlchemyMappingSource) -> tuple[object, ...]:
    return (
        _MAPPING_SOURCE_RANK[value.kind],
        _utf8(value.module),
        _utf8(value.symbol),
        _utf8(value.source.path),
        value.source.range.start_line,
        value.source.range.end_line,
    )


def row_sort_key(value: SqlAlchemyRow) -> tuple[object, ...]:
    return (
        _utf8(value.owner_id),
        _ROW_KIND_RANK[value.kind],
        _utf8(value.name or ""),
        _utf8(value.id),
        _utf8(value.source.path),
        value.source.range.start_line,
        value.source.range.end_line,
    )


def relation_sort_key(value: SqlAlchemyRelation) -> tuple[object, ...]:
    return (
        _utf8(value.source_id),
        _RELATION_KIND_RANK[value.kind],
        _TARGET_RESOLUTION_RANK[value.target.resolution],
        _utf8(value.target.id or value.target.display_name),
        _utf8(value.role or ""),
        _utf8(value.id),
        _utf8(value.source.path),
        value.source.range.start_line,
        value.source.range.end_line,
    )


def failed_source_sort_key(value: SqlAlchemyFailedSource) -> tuple[object, ...]:
    return (
        _utf8(value.path),
        _FAILED_STAGE_RANK[value.stage],
        _utf8(value.diagnostic_code.value),
    )


def frontier_sort_key(value: SqlAlchemyCoverageFrontier) -> tuple[object, ...]:
    return (
        _FRONTIER_DIRECTION_RANK[value.direction],
        _FRONTIER_KIND_RANK[value.kind],
        _utf8(value.reference),
        _FRONTIER_REASON_RANK[value.reason],
    )


def redacted_value_count(values: tuple[SqlAlchemyRow, ...]) -> int:
    descriptors: list[RedactedExpression] = []
    for value in values:
        if isinstance(value, SqlAlchemyColumnRow):
            descriptors.extend(
                (
                    value.type.parameters,
                    value.default,
                    value.server_default,
                    value.onupdate,
                    value.server_onupdate,
                    value.computed,
                    value.identity,
                )
            )
        elif isinstance(value, SqlAlchemyCheckRow):
            descriptors.append(value.expression)
        elif isinstance(value, SqlAlchemyIndexRow):
            descriptors.extend(term.expression for term in value.terms)
        elif isinstance(value, SqlAlchemyForeignKeyRow):
            descriptors.extend((value.ondelete, value.onupdate))
        elif isinstance(value, SqlAlchemyRelationshipRow):
            descriptors.extend(
                (
                    value.primaryjoin,
                    value.secondaryjoin,
                    value.order_by,
                    value.foreign_keys,
                )
            )
    return sum(value.present for value in descriptors)
