from __future__ import annotations

import ctypes
import json
import os
import re
import secrets
import stat
import sys
import unicodedata
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from typing import Protocol

from code_structure_viz.artifacts.manifest import (
    ArtifactDescriptor,
    ArtifactFormat,
)
from code_structure_viz.core.diagnostics import Diagnostic, DiagnosticCode, diagnostic
from code_structure_viz.core.domains import DomainName
from code_structure_viz.core.path_safety import has_symlink_component, lexical_absolute
from code_structure_viz.semantic.canonical_json import encode_canonical_json, parse_json_integer

_FINAL_PATHS = frozenset(
    {
        "python.snapshot.semantic.json",
        "python.snapshot.puml",
        "sqlalchemy.snapshot.semantic.json",
        "sqlalchemy.snapshot.puml",
        "python.diff.semantic.json",
        "python.diff.puml",
        "sqlalchemy.diff.semantic.json",
        "sqlalchemy.diff.puml",
        "file-changes.json",
        "run-manifest.json",
    }
)
_PLANTUML_RELATION = re.compile(
    r"(?:C|M)_[0-9a-f]{64} (?:<\|--|\*--|\.\.>) (?:C|M)_[0-9a-f]{64} : "
    r"(?:継承|合成|型依存|import依存)"
)
_SQLALCHEMY_ALIAS = r"T_[0-9a-f]{64}"
_SQLALCHEMY_ENTITY = re.compile(rf'^entity "(.+)" as ({_SQLALCHEMY_ALIAS}) \{{$')
_SQLALCHEMY_RELATION = re.compile(
    "^("
    + _SQLALCHEMY_ALIAS
    + r") ((?:\|\||\|o|\}o|\}\|)(?:--|\.\.)(?:\|\||o\||o\{|\|\{)) ("
    + _SQLALCHEMY_ALIAS
    + r") : (foreign_key|relationship) (.+)$"
)
_SQLALCHEMY_UNKNOWN_RELATION = re.compile(
    rf"^({_SQLALCHEMY_ALIAS}) (--|\.\.) ({_SQLALCHEMY_ALIAS}) : "
    r"(foreign_key|relationship) (.+) \[source=(1|0\.\.1|0\.\.N|1\.\.N|\?) "
    r"target=(1|0\.\.1|0\.\.N|1\.\.N|\?)\]$"
)
_SQLALCHEMY_INHERITANCE = re.compile(
    rf"^({_SQLALCHEMY_ALIAS}) --\|> ({_SQLALCHEMY_ALIAS}) : inheritance$"
)
_SQLALCHEMY_ASSOCIATION = re.compile(
    rf"^({_SQLALCHEMY_ALIAS}) \.\. ({_SQLALCHEMY_ALIAS}) : association "
    r"(.+) \[source=\? target=\?\]$"
)
_SQLALCHEMY_ESCAPE = re.compile(r"_U([0-9A-F]{4,6})_")
_SQLALCHEMY_REDACTED = re.compile(
    r"\[redacted:(?:literal|callable|sql_expression|computed|identity|unknown)\]"
)
_SQLALCHEMY_BOOL = frozenset({"true", "false", "?"})
_SQLALCHEMY_TYPE_CATEGORIES = (
    "integer|string|text|boolean|date|datetime|time|decimal|float|json|binary|uuid|"
    "enum|array|custom|unknown"
)
_SQLALCHEMY_HEADER = (
    "@startuml",
    "title SQLAlchemy ER snapshot",
    "top to bottom direction",
    "hide circle",
    "skinparam linetype ortho",
    "hide methods",
)
_SQLALCHEMY_LEGEND_TAIL = (
    "  ||--|| exactly_one",
    "  |o--o| zero_or_one",
    "  }o--o{ zero_or_many",
    "  }|--|{ one_or_many",
    "  -- foreign_key (solid)",
    "  .. relationship (dotted)",
    "  --|> inheritance (not cardinality)",
    "  .. association metadata (cardinality unknown)",
    "  [?] evidence insufficient; plain line retained",
    "  [redacted] literal/expression value omitted",
    "endlegend",
    "@enduml",
)
_PRIVATE_PATH_BOUNDARIES = frozenset(" \t\r\n\"'=:([]{<")


class OutputTransactionError(RuntimeError):
    def __init__(self, value: Diagnostic) -> None:
        self.diagnostic = value
        super().__init__(value.message)


class PublicationInterrupted(OutputTransactionError):
    pass


class _DirectoryScanner(Protocol):
    def __next__(self) -> os.DirEntry[str]: ...

    def close(self) -> None: ...


def _error(code: DiagnosticCode) -> OutputTransactionError:
    return OutputTransactionError(diagnostic(code))


def _is_within(path: Path, root: Path) -> bool:
    try:
        return os.path.commonpath((str(path), str(root))) == str(root)
    except ValueError:
        return False


def _stat_identity(value: os.stat_result) -> tuple[int, int]:
    return value.st_dev, value.st_ino


def _directory_flags() -> int:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    return flags


def _read_flags() -> int:
    flags = os.O_RDONLY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    return flags


def _open_directory_without_symlinks(path: Path) -> int:
    absolute = lexical_absolute(path)
    descriptor = os.open(absolute.anchor, _directory_flags())
    try:
        for component in absolute.parts[1:]:
            before = os.stat(component, dir_fd=descriptor, follow_symlinks=False)
            if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode):
                raise OSError
            child = os.open(component, _directory_flags(), dir_fd=descriptor)
            after = os.fstat(child)
            if _stat_identity(before) != _stat_identity(after):
                os.close(child)
                raise OSError
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _descriptor_is_within(descriptor: int, root: Path) -> bool:
    root_identity = _stat_identity(root.stat())
    current = os.dup(descriptor)
    try:
        while True:
            current_identity = _stat_identity(os.fstat(current))
            if current_identity == root_identity:
                return True
            parent = os.open("..", _directory_flags(), dir_fd=current)
            parent_identity = _stat_identity(os.fstat(parent))
            if parent_identity == current_identity:
                os.close(parent)
                return False
            os.close(current)
            current = parent
    finally:
        os.close(current)


def _descriptor_matches_path(descriptor: int, path: Path) -> bool:
    if has_symlink_component(path):
        return False
    try:
        path_stat = path.stat(follow_symlinks=False)
    except OSError:
        return False
    return stat.S_ISDIR(path_stat.st_mode) and _stat_identity(path_stat) == _stat_identity(
        os.fstat(descriptor)
    )


def _entry_exists(directory_descriptor: int, name: str) -> bool:
    try:
        os.stat(name, dir_fd=directory_descriptor, follow_symlinks=False)
    except FileNotFoundError:
        return False
    return True


def _read_file(directory_descriptor: int, name: str) -> bytes:
    descriptor = os.open(name, _read_flags(), dir_fd=directory_descriptor)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise OSError
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, 64 * 1024):
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _remove_directory_contents(descriptor: int) -> None:
    stack: list[tuple[int, int | None, str | None, _DirectoryScanner]] = [
        (descriptor, None, None, os.scandir(descriptor))
    ]
    try:
        while stack:
            current, parent, name, scanner = stack[-1]
            try:
                entry = next(scanner)
            except StopIteration:
                stack.pop()
                closed = False
                try:
                    scanner.close()
                    os.fsync(current)
                    if parent is not None and name is not None:
                        os.close(current)
                        closed = True
                        os.rmdir(name, dir_fd=parent)
                finally:
                    if parent is not None and not closed:
                        with suppress(OSError):
                            os.close(current)
                continue
            entry_stat = os.stat(entry.name, dir_fd=current, follow_symlinks=False)
            if stat.S_ISDIR(entry_stat.st_mode) and not stat.S_ISLNK(entry_stat.st_mode):
                child = os.open(entry.name, _directory_flags(), dir_fd=current)
                try:
                    child_scanner = os.scandir(child)
                except BaseException:
                    os.close(child)
                    raise
                stack.append((child, current, entry.name, child_scanner))
            else:
                os.unlink(entry.name, dir_fd=current)
    finally:
        for current, parent, _name, scanner in reversed(stack):
            with suppress(OSError):
                scanner.close()
            if parent is not None:
                with suppress(OSError):
                    os.close(current)


def _rename_noreplace(
    source_directory_descriptor: int,
    source_name: str,
    destination_directory_descriptor: int,
    destination_name: str,
) -> None:
    library = ctypes.CDLL(None, use_errno=True)
    source_bytes = os.fsencode(source_name)
    destination_bytes = os.fsencode(destination_name)
    if sys.platform == "darwin":
        operation = library.renameatx_np
        operation.argtypes = (
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        )
        operation.restype = ctypes.c_int
        result = operation(
            source_directory_descriptor,
            source_bytes,
            destination_directory_descriptor,
            destination_bytes,
            0x00000004,
        )
    elif sys.platform.startswith("linux"):
        operation = library.renameat2
        operation.argtypes = (
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        )
        operation.restype = ctypes.c_int
        result = operation(
            source_directory_descriptor,
            source_bytes,
            destination_directory_descriptor,
            destination_bytes,
            1,
        )
    else:
        raise OSError("atomic no-replace publication is unsupported")
    if result != 0:
        error_number = ctypes.get_errno()
        raise OSError(error_number, os.strerror(error_number), destination_name)


def _canonical_json_bytes(content: bytes) -> bool:
    try:
        if content.startswith(b"\xef\xbb\xbf") or not content.endswith(b"\n"):
            return False
        if content.endswith(b"\n\n"):
            return False
        value = json.loads(content.decode("utf-8", errors="strict"), parse_int=parse_json_integer)
        return encode_canonical_json(value) == content
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
        return False


def _contains_private_path_token(value: str, private_path: str) -> bool:
    start = 0
    while (index := value.find(private_path, start)) >= 0:
        before = value[index - 1] if index else ""
        end = index + len(private_path)
        after = value[end] if end < len(value) else ""
        if (not before or before in _PRIVATE_PATH_BOUNDARIES) and (
            not after or after == "/" or after in _PRIVATE_PATH_BOUNDARIES
        ):
            return True
        start = end
    return False


def _contains_private_path(value: object, private_paths: tuple[str, ...]) -> bool:
    if isinstance(value, str):
        return any(_contains_private_path_token(value, path) for path in private_paths)
    if isinstance(value, dict):
        return any(
            _contains_private_path(key, private_paths)
            or _contains_private_path(item, private_paths)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_private_path(item, private_paths) for item in value)
    return False


def _contains_private_paths(
    relative_path: str,
    content: bytes,
    private_paths: tuple[str, ...],
) -> bool:
    try:
        text = content.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return False
    if relative_path in {
        "python.snapshot.puml",
        "python.diff.puml",
        "sqlalchemy.snapshot.puml",
        "sqlalchemy.diff.puml",
    }:
        return any(_contains_private_path_token(text, path) for path in private_paths)
    try:
        value = json.loads(text)
    except (json.JSONDecodeError, TypeError, ValueError):
        return False
    return _contains_private_path(value, private_paths)


def _valid_python_plantuml(content: bytes) -> bool:
    try:
        text = content.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return False
    if not text.endswith("\n") or text.endswith("\n\n"):
        return False
    lines = text[:-1].split("\n")
    if not lines or lines[0] != "@startuml" or lines[-1] != "@enduml":
        return False
    allowed_exact = {
        "@startuml",
        "@enduml",
        "title Python structure snapshot",
        "title Python semantic diff",
        "left to right direction",
        "skinparam classAttributeIconSize 0",
        "hide empty members",
        "legend right",
        "  <|-- 継承",
        "  *-- 合成",
        "  ..> 型依存",
        "  package ..> package import依存",
        "endlegend",
        "}",
        "  }",
    }
    allowed_prefixes = (
        'note "不完全なsnapshot:',
        'note "status: ',
        'note "',
        'package "',
        '  note "classなし" as N_EMPTY_',
        '  class "',
        "    field ",
        "    property ",
        "    method ",
        "    + ",
        "    - ",
        "    ~ ",
        "    → ",
        "    ? ",
        "  class " + '"',
        "  + ",
        "  - ",
        "  ~ ",
        "  → ",
        "  ? ",
        "  note " + '"',
        "  + added",
        "  - removed",
        "  ~ modified",
        "  → moved",
        "  ? unknown",
    )
    return all(
        line in allowed_exact
        or line.startswith(allowed_prefixes)
        or _PLANTUML_RELATION.fullmatch(line) is not None
        for line in lines
    )


def _valid_sqlalchemy_escaped_component(value: str) -> bool:
    if not value or unicodedata.normalize("NFC", value) != value:
        return False
    index = 0
    while index < len(value):
        escaped = _SQLALCHEMY_ESCAPE.match(value, index)
        if escaped is not None:
            scalar = int(escaped.group(1), 16)
            if scalar > 0x10FFFF or 0xD800 <= scalar <= 0xDFFF:
                return False
            character = chr(scalar)
            if unicodedata.category(character)[0] in {"L", "N"} or character in {
                " ",
                "-",
                "/",
                "$",
            }:
                return False
            index = escaped.end()
            continue
        character = value[index]
        if unicodedata.category(character)[0] not in {"L", "N"} and character not in {
            " ",
            "-",
            "/",
            "$",
            "_",
        }:
            return False
        index += 1
    return True


def _valid_sqlalchemy_display(value: str) -> bool:
    if value == "<unknown>":
        return True
    components = value.split(".")
    return len(components) in {1, 2} and all(
        _valid_sqlalchemy_escaped_component(item) for item in components
    )


def _valid_sqlalchemy_name(value: str) -> bool:
    return value == "<unnamed>" or _valid_sqlalchemy_escaped_component(value)


def _valid_sqlalchemy_redacted(value: str) -> bool:
    return value == "-" or _SQLALCHEMY_REDACTED.fullmatch(value) is not None


def _valid_sqlalchemy_columns(value: str) -> bool:
    return bool(value) and all(
        _valid_sqlalchemy_escaped_component(item) for item in value.split(",")
    )


def _valid_sqlalchemy_row(line: str) -> bool:
    if line == "  --":
        return True

    column = re.fullmatch(
        rf"  (\* )?(.+?) : ({_SQLALCHEMY_TYPE_CATEGORIES})"
        r"(?: \((.+?)\))? <<(.+)>>",
        line,
    )
    if column is not None:
        _mandatory, name, _category, type_name, markers = column.groups()
        marker_values = tuple(value.strip() for value in markers.split(","))
        allowed_markers = {"PK", "FK", "UQ", "IX", "NN", "NULL", "?NULL"}
        return (
            _valid_sqlalchemy_name(name)
            and (type_name is None or _valid_sqlalchemy_escaped_component(type_name))
            and bool(marker_values)
            and all(value in allowed_markers for value in marker_values)
            and len(set(marker_values)) == len(marker_values)
        )

    simple_columns = re.fullmatch(r"  (primary_key|unique) (.+?) columns=(.+)", line)
    if simple_columns is not None:
        _kind, name, columns = simple_columns.groups()
        return (
            _valid_sqlalchemy_name(name)
            and columns.startswith("(")
            and columns.endswith(")")
            and _valid_sqlalchemy_columns(columns[1:-1])
        )

    check = re.fullmatch(r"  check (.+?) expression=(\S+)", line)
    if check is not None:
        name, expression = check.groups()
        return _valid_sqlalchemy_name(name) and _valid_sqlalchemy_redacted(expression)

    index = re.fullmatch(r"  index (.+?) unique=(true|false|\?) terms=(.+)", line)
    if index is not None:
        name, unique, terms_value = index.groups()
        terms = terms_value.split(",")
        return (
            _valid_sqlalchemy_name(name)
            and unique in _SQLALCHEMY_BOOL
            and bool(terms)
            and all(
                (
                    _valid_sqlalchemy_escaped_component(term.removeprefix("column:"))
                    if term.startswith("column:")
                    else _SQLALCHEMY_REDACTED.fullmatch(term) is not None
                )
                for term in terms
            )
        )

    foreign_key = re.fullmatch(
        r"  foreign_key (.+?) local=\((.+?)\) references=(.+?)\((.+?)\) "
        r"ondelete=(\S+) onupdate=(\S+)",
        line,
    )
    if foreign_key is not None:
        name, local, target, remote, ondelete, onupdate = foreign_key.groups()
        return (
            _valid_sqlalchemy_name(name)
            and _valid_sqlalchemy_columns(local)
            and _valid_sqlalchemy_display(target)
            and _valid_sqlalchemy_columns(remote)
            and _valid_sqlalchemy_redacted(ondelete)
            and _valid_sqlalchemy_redacted(onupdate)
        )

    relationship = re.fullmatch(
        r"  relationship (.+?) : (scalar|many|unknown) target=(.+?) "
        r"uselist=(true|false|\?) back_populates=(.+?) secondary=(\S+)",
        line,
    )
    if relationship is not None:
        name, _cardinality, target, uselist, back_populates, secondary = relationship.groups()
        return (
            _valid_sqlalchemy_name(name)
            and _valid_sqlalchemy_display(target)
            and uselist in _SQLALCHEMY_BOOL
            and (back_populates == "-" or _valid_sqlalchemy_escaped_component(back_populates))
            and (secondary == "-" or _valid_sqlalchemy_display(secondary))
        )

    inheritance = re.fullmatch(r"  inheritance target=(.+)", line)
    if inheritance is not None:
        return _valid_sqlalchemy_display(inheritance.group(1))

    association = re.fullmatch(
        r"  association_table (.+?) source=(.+?) target=(.+)",
        line,
    )
    if association is not None:
        name, source, target = association.groups()
        return (
            _valid_sqlalchemy_name(name)
            and _valid_sqlalchemy_display(source)
            and _valid_sqlalchemy_display(target)
        )
    return False


def _valid_sqlalchemy_relation(line: str, aliases: set[str]) -> bool:
    relation = _SQLALCHEMY_RELATION.fullmatch(line)
    if relation is not None:
        source, edge, target, kind, label = relation.groups()
        left, style, right = edge[:2], edge[2:4], edge[4:]
        return (
            source in aliases
            and target in aliases
            and left in {"||", "|o", "}o", "}|"}
            and style in {"--", ".."}
            and right in {"||", "o|", "o{", "|{"}
            and _valid_sqlalchemy_name(label)
            and (
                (kind == "foreign_key" and style == "--")
                or (kind == "relationship" and style == "..")
            )
        )
    unknown = _SQLALCHEMY_UNKNOWN_RELATION.fullmatch(line)
    if unknown is not None:
        source, style, target, kind, label, _source_multiplicity, _target_multiplicity = (
            unknown.groups()
        )
        return (
            source in aliases
            and target in aliases
            and kind in {"foreign_key", "relationship"}
            and style in {"--", ".."}
            and _valid_sqlalchemy_name(label)
        )
    inheritance = _SQLALCHEMY_INHERITANCE.fullmatch(line)
    if inheritance is not None:
        source, target = inheritance.groups()
        return source in aliases and target in aliases
    association = _SQLALCHEMY_ASSOCIATION.fullmatch(line)
    if association is not None:
        source, target, label = association.groups()
        return source in aliases and target in aliases and _valid_sqlalchemy_name(label)
    return False


def _valid_sqlalchemy_plantuml(content: bytes) -> bool:
    try:
        text = content.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return False
    if not text.endswith("\n") or text.endswith("\n\n"):
        return False
    lines = text[:-1].split("\n")
    if tuple(lines[: len(_SQLALCHEMY_HEADER)]) != _SQLALCHEMY_HEADER:
        return False
    if lines.count("legend right") != 1:
        return False
    legend = lines.index("legend right")
    if lines[legend + 1 : legend + 2] != [
        "  rule_version=code-structure-viz.sqlalchemy-redaction/v1"
    ]:
        return False
    if (
        legend + 2 >= len(lines)
        or re.fullmatch(r"  redacted_values=(?:0|[1-9][0-9]*)", lines[legend + 2]) is None
    ):
        return False
    if tuple(lines[legend + 3 :]) != _SQLALCHEMY_LEGEND_TAIL:
        return False

    aliases: set[str] = set()
    in_entity = False
    relations_started = False
    for line in lines[len(_SQLALCHEMY_HEADER) : legend]:
        if in_entity:
            if line == "}":
                in_entity = False
            elif not _valid_sqlalchemy_row(line):
                return False
            continue
        entity = _SQLALCHEMY_ENTITY.fullmatch(line)
        if entity is not None:
            if relations_started:
                return False
            display, alias = entity.groups()
            if alias in aliases or not _valid_sqlalchemy_display(display):
                return False
            aliases.add(alias)
            in_entity = True
            continue
        relations_started = True
        if not _valid_sqlalchemy_relation(line, aliases):
            return False
    return not in_entity


def _valid_sqlalchemy_diff_plantuml(content: bytes) -> bool:
    try:
        text = content.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return False
    if not text.endswith("\n") or text.endswith("\n\n"):
        return False
    lines = text[:-1].split("\n")
    header = [
        "@startuml",
        "title SQLAlchemy ER diff",
        "top to bottom direction",
        "hide circle",
        "skinparam linetype ortho",
        "skinparam classAttributeIconSize 0",
    ]
    tail = [
        "legend right",
        "  + added",
        "  - removed (ghost)",
        "  ~ modified (before/after)",
        "  context impact context",
        "endlegend",
        "@enduml",
    ]
    if lines[: len(header)] != header or lines[-len(tail) :] != tail:
        return False
    in_entity = False
    aliases: set[str] = set()
    for line in lines[len(header) : -len(tail)]:
        if line == "}":
            if not in_entity:
                return False
            in_entity = False
        elif line.startswith('entity "') and (
            entity := re.fullmatch(rf'entity ".+" as ({_SQLALCHEMY_ALIAS}) #[A-Za-z]+ \{{', line)
        ):
            if in_entity:
                return False
            aliases.add(entity.group(1))
            in_entity = True
        elif (in_entity and line.startswith(("  + ", "  - ", "  ~ "))) or (
            not in_entity
            and (
                line.startswith('note "status: ')
                or re.fullmatch(r'note ".+" as N_[0-9a-f]{64}', line)
                or _valid_sqlalchemy_relation(line, aliases)
            )
        ):
            continue
        else:
            return False
    return not in_entity


class OutputTransaction:
    def __init__(
        self,
        repository: Path,
        output_dir: Path,
        *,
        repository_identity: tuple[int, int] | None = None,
    ) -> None:
        parent_descriptor: int | None = None
        repository_descriptor: int | None = None
        try:
            self.repository = repository.resolve(strict=True)
            repository_descriptor = _open_directory_without_symlinks(self.repository)
            if (
                repository_identity is not None
                and _stat_identity(os.fstat(repository_descriptor)) != repository_identity
            ):
                raise OSError
            self.output_dir = lexical_absolute(output_dir)
            if has_symlink_component(self.output_dir):
                raise OSError
            parent = self.output_dir.parent
            if not self.output_dir.name:
                raise OSError
            parent_descriptor = _open_directory_without_symlinks(parent)
            physically_inside_repository = _descriptor_is_within(parent_descriptor, self.repository)
            parent_is_current = _descriptor_matches_path(parent_descriptor, parent)
            repository_is_current = _descriptor_matches_path(repository_descriptor, self.repository)
            destination_exists = _entry_exists(parent_descriptor, self.output_dir.name)
        except OSError as error:
            if parent_descriptor is not None:
                os.close(parent_descriptor)
            if repository_descriptor is not None:
                os.close(repository_descriptor)
            raise _error(DiagnosticCode.OUTPUT_DESTINATION) from error
        if _is_within(self.output_dir, self.repository) or physically_inside_repository:
            os.close(parent_descriptor)
            os.close(repository_descriptor)
            raise _error(DiagnosticCode.OUTPUT_INSIDE_REPO)
        if destination_exists or not parent_is_current or not repository_is_current:
            os.close(parent_descriptor)
            os.close(repository_descriptor)
            raise _error(DiagnosticCode.OUTPUT_DESTINATION)
        self.parent = parent
        self._repository_descriptor: int | None = repository_descriptor
        self._parent_descriptor: int | None = parent_descriptor
        self._staging_root: Path | None = None
        self._staging_name: str | None = None
        self._staging_descriptor: int | None = None
        self._source_descriptor: int | None = None
        self._artifacts_descriptor: int | None = None
        self._descriptors: dict[str, ArtifactDescriptor] = {}
        self._manifest_staged = False
        self._committed = False

    @property
    def staging_root(self) -> Path:
        if self._staging_root is None:
            raise RuntimeError("output transaction has not begun")
        return self._staging_root

    @property
    def staging_root_descriptor(self) -> int:
        if self._staging_descriptor is None:
            raise RuntimeError("output transaction has not begun")
        return self._staging_descriptor

    @property
    def repository_descriptor(self) -> int:
        if self._repository_descriptor is None:
            raise RuntimeError("output transaction repository is closed")
        return self._repository_descriptor

    def begin(self) -> Path:
        if self._staging_root is not None:
            raise RuntimeError("output transaction already began")
        parent_descriptor = self._require_parent_descriptor()
        try:
            for _ in range(128):
                staging_name = f".code-structure-viz-staging-{secrets.token_hex(16)}"
                try:
                    os.mkdir(staging_name, mode=0o700, dir_fd=parent_descriptor)
                except FileExistsError:
                    continue
                break
            else:
                raise OSError
            self._staging_name = staging_name
            self._staging_root = self.parent / staging_name
            self._staging_descriptor = os.open(
                staging_name,
                _directory_flags(),
                dir_fd=parent_descriptor,
            )
            os.fchmod(self._staging_descriptor, 0o700)
            os.mkdir("source", mode=0o700, dir_fd=self._staging_descriptor)
            os.mkdir("artifacts", mode=0o700, dir_fd=self._staging_descriptor)
            self._source_descriptor = os.open(
                "source",
                _directory_flags(),
                dir_fd=self._staging_descriptor,
            )
            self._artifacts_descriptor = os.open(
                "artifacts",
                _directory_flags(),
                dir_fd=self._staging_descriptor,
            )
            if (
                not self._repository_is_current()
                or not self._parent_is_current()
                or not _descriptor_matches_path(self._staging_descriptor, self._staging_root)
            ):
                raise OSError
        except OSError as error:
            self.abort()
            raise _error(DiagnosticCode.OUTPUT_DESTINATION) from error
        return self._staging_root

    def stage_payload(self, format_value: ArtifactFormat, content: bytes) -> ArtifactDescriptor:
        return self.stage_snapshot_payload("python", format_value, content)

    def stage_snapshot_payload(
        self,
        domain: DomainName,
        format_value: ArtifactFormat,
        content: bytes,
    ) -> ArtifactDescriptor:
        descriptor = ArtifactDescriptor.create_snapshot(domain, format_value, content)
        if descriptor.path in self._descriptors:
            raise _error(DiagnosticCode.INTERNAL_INVARIANT)
        self._validate_content(descriptor.path, content)
        self._write(descriptor.path, content)
        self._descriptors[descriptor.path] = descriptor
        return descriptor

    def stage_diff_payload(
        self,
        domain: DomainName,
        format_value: ArtifactFormat,
        content: bytes,
    ) -> ArtifactDescriptor:
        if format_value not in {"semantic-json", "plantuml", "file-change-set"}:
            raise _error(DiagnosticCode.INTERNAL_INVARIANT)
        descriptor = ArtifactDescriptor.create_diff(domain, format_value, content)
        if descriptor.path in self._descriptors:
            raise _error(DiagnosticCode.INTERNAL_INVARIANT)
        self._validate_content(descriptor.path, content)
        self._write(descriptor.path, content)
        self._descriptors[descriptor.path] = descriptor
        return descriptor

    def stage_manifest(self, content: bytes) -> None:
        if self._manifest_staged:
            raise _error(DiagnosticCode.INTERNAL_INVARIANT)
        self._validate_content("run-manifest.json", content)
        self._write("run-manifest.json", content)
        self._manifest_staged = True

    @property
    def descriptors(self) -> tuple[ArtifactDescriptor, ...]:
        rank = {"file-change-set": 0, "semantic-json": 1, "plantuml": 2}
        return tuple(
            sorted(
                self._descriptors.values(),
                key=lambda item: (rank[item.format], item.path.encode("utf-8")),
            )
        )

    def read_staged_artifacts(self) -> dict[str, bytes]:
        if not self._manifest_staged:
            raise _error(DiagnosticCode.INTERNAL_INVARIANT)
        artifacts_descriptor = self._require_artifacts_descriptor()
        paths = [descriptor.path for descriptor in self.descriptors]
        paths.append("run-manifest.json")
        contents: dict[str, bytes] = {}
        try:
            for relative_path in paths:
                content = _read_file(artifacts_descriptor, relative_path)
                self._validate_content(relative_path, content)
                contents[relative_path] = content
        except OutputTransactionError:
            raise
        except OSError as error:
            raise _error(DiagnosticCode.OUTPUT_DESTINATION) from error
        return contents

    def commit(self, cancelled: Callable[[], bool] | None = None) -> None:
        if self._committed or not self._manifest_staged:
            raise _error(DiagnosticCode.INTERNAL_INVARIANT)
        cancellation_probe = cancelled or (lambda: False)
        parent_descriptor = self._require_parent_descriptor()
        staging_descriptor = self._require_staging_descriptor()
        try:
            if not self._repository_is_current() or not self._parent_is_current():
                raise _error(DiagnosticCode.OUTPUT_DESTINATION)
            self._remove_frozen_source()
            os.fsync(self._require_artifacts_descriptor())
            if cancellation_probe():
                raise PublicationInterrupted(diagnostic(DiagnosticCode.INTERRUPTED))
            if (
                not self._repository_is_current()
                or not self._parent_is_current()
                or _entry_exists(parent_descriptor, self.output_dir.name)
            ):
                raise _error(DiagnosticCode.OUTPUT_DESTINATION)
            _rename_noreplace(
                staging_descriptor,
                "artifacts",
                parent_descriptor,
                self.output_dir.name,
            )
            self._committed = True
        except PublicationInterrupted:
            self.abort()
            raise
        except OutputTransactionError:
            self.abort()
            raise
        except OSError as error:
            self.abort()
            raise _error(DiagnosticCode.OUTPUT_DESTINATION) from error

        self._close_descriptor("_artifacts_descriptor")
        self._close_descriptor("_staging_descriptor")
        with suppress(OSError):
            if self._staging_name is not None:
                os.rmdir(self._staging_name, dir_fd=parent_descriptor)
        with suppress(OSError):
            os.fsync(parent_descriptor)
        self._close_descriptor("_parent_descriptor")
        self._close_descriptor("_repository_descriptor")

    def abort(self) -> None:
        if self._committed:
            self._close_all_descriptors()
            return
        self._close_descriptor("_source_descriptor")
        self._close_descriptor("_artifacts_descriptor")
        staging_descriptor = self._staging_descriptor
        parent_descriptor = self._parent_descriptor
        if staging_descriptor is not None:
            with suppress(OSError):
                _remove_directory_contents(staging_descriptor)
        self._close_descriptor("_staging_descriptor")
        if parent_descriptor is not None and self._staging_name is not None:
            with suppress(OSError):
                os.rmdir(self._staging_name, dir_fd=parent_descriptor)
        self._close_descriptor("_parent_descriptor")
        self._close_descriptor("_repository_descriptor")

    def _write(self, relative_path: str, content: bytes) -> None:
        if relative_path not in _FINAL_PATHS or type(content) is not bytes:
            raise _error(DiagnosticCode.INTERNAL_INVARIANT)
        artifacts_descriptor = self._require_artifacts_descriptor()
        try:
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            if hasattr(os, "O_CLOEXEC"):
                flags |= os.O_CLOEXEC
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            fd = os.open(relative_path, flags, 0o600, dir_fd=artifacts_descriptor)
            try:
                remaining = memoryview(content)
                while remaining:
                    written = os.write(fd, remaining)
                    if written <= 0:
                        raise OSError
                    remaining = remaining[written:]
                os.fsync(fd)
            finally:
                os.close(fd)
        except OSError as error:
            raise _error(DiagnosticCode.OUTPUT_DESTINATION) from error

    def _validate_content(self, relative_path: str, content: bytes) -> None:
        private_paths = (
            str(self.repository),
            str(self.staging_root),
        )
        if b"\0" in content or _contains_private_paths(relative_path, content, private_paths):
            raise _error(DiagnosticCode.INTERNAL_INVARIANT)
        valid = (
            _valid_python_plantuml(content)
            if relative_path in {"python.snapshot.puml", "python.diff.puml"}
            else _valid_sqlalchemy_plantuml(content)
            if relative_path == "sqlalchemy.snapshot.puml"
            else _valid_sqlalchemy_diff_plantuml(content)
            if relative_path == "sqlalchemy.diff.puml"
            else _canonical_json_bytes(content)
        )
        if not valid:
            raise _error(DiagnosticCode.INTERNAL_INVARIANT)

    def _remove_frozen_source(self) -> None:
        source_descriptor = self._source_descriptor
        staging_descriptor = self._require_staging_descriptor()
        if source_descriptor is None:
            raise _error(DiagnosticCode.INTERNAL_INVARIANT)
        try:
            _remove_directory_contents(source_descriptor)
            self._close_descriptor("_source_descriptor")
            os.rmdir("source", dir_fd=staging_descriptor)
            os.fsync(staging_descriptor)
        except OSError as error:
            raise _error(DiagnosticCode.OUTPUT_DESTINATION) from error

    def _parent_is_current(self) -> bool:
        descriptor = self._parent_descriptor
        return descriptor is not None and _descriptor_matches_path(descriptor, self.parent)

    def _repository_is_current(self) -> bool:
        descriptor = self._repository_descriptor
        return descriptor is not None and _descriptor_matches_path(descriptor, self.repository)

    def _require_parent_descriptor(self) -> int:
        if self._parent_descriptor is None:
            raise _error(DiagnosticCode.OUTPUT_DESTINATION)
        return self._parent_descriptor

    def _require_staging_descriptor(self) -> int:
        if self._staging_descriptor is None:
            raise _error(DiagnosticCode.INTERNAL_INVARIANT)
        return self._staging_descriptor

    def _require_artifacts_descriptor(self) -> int:
        if self._artifacts_descriptor is None:
            raise _error(DiagnosticCode.INTERNAL_INVARIANT)
        return self._artifacts_descriptor

    def _close_descriptor(self, attribute: str) -> None:
        descriptor = getattr(self, attribute)
        if descriptor is not None:
            setattr(self, attribute, None)
            with suppress(OSError):
                os.close(descriptor)

    def _close_all_descriptors(self) -> None:
        self._close_descriptor("_source_descriptor")
        self._close_descriptor("_artifacts_descriptor")
        self._close_descriptor("_staging_descriptor")
        self._close_descriptor("_parent_descriptor")
        self._close_descriptor("_repository_descriptor")
