from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import PurePosixPath
from typing import Any

from code_structure_viz.semantic.canonical_json import encode_canonical_json

_HUNK = re.compile(
    rb"^@@ -(?P<old_start>[0-9]+)(?:,(?P<old_count>[0-9]+))? "
    rb"\+(?P<new_start>[0-9]+)(?:,(?P<new_count>[0-9]+))? @@"
)
_STATUSES = frozenset({"A", "M", "D", "R", "C", "T", "U", "?"})
_RENAME_STATUS = re.compile(r"[RC](?:[0-9]{1,3})?\Z", flags=re.ASCII)
_MAX_UNIFIED_DIFF_BYTES = 16 * 1024 * 1024
_MAX_UNIFIED_DIFF_LINE_BYTES = 128 * 1024


@dataclass(frozen=True, slots=True)
class HunkMetadata:
    old_start: int
    old_line_count: int
    new_start: int
    new_line_count: int
    ordinal: int
    old_path: PurePosixPath | None = None
    new_path: PurePosixPath | None = None
    status: str = "M"

    def __post_init__(self) -> None:
        if (
            type(self.old_start) is not int
            or type(self.old_line_count) is not int
            or type(self.new_start) is not int
            or type(self.new_line_count) is not int
            or type(self.ordinal) is not int
            or self.old_start < 0
            or self.new_start < 0
            or self.old_line_count < 0
            or self.new_line_count < 0
            or self.ordinal < 0
            or self.status not in _STATUSES
        ):
            raise ValueError("hunk metadata is invalid")
        for path in (self.old_path, self.new_path):
            if path is not None:
                _validate_path(path)

    @property
    def hunk_id(self) -> str:
        value = {
            "status": self.status,
            "old_path": self.old_path.as_posix() if self.old_path is not None else None,
            "new_path": self.new_path.as_posix() if self.new_path is not None else None,
            "old_start": self.old_start,
            "old_line_count": self.old_line_count,
            "new_start": self.new_start,
            "new_line_count": self.new_line_count,
            "ordinal": self.ordinal,
        }
        return hashlib.sha256(encode_canonical_json(value)).hexdigest()

    def to_json_value(self) -> dict[str, object]:
        return {
            "old_start": self.old_start,
            "old_line_count": self.old_line_count,
            "new_start": self.new_start,
            "new_line_count": self.new_line_count,
            "ordinal": self.ordinal,
            "hunk_id": self.hunk_id,
        }


@dataclass(frozen=True, slots=True)
class FileChange:
    status: str
    old_path: PurePosixPath | None
    new_path: PurePosixPath | None
    hunks: tuple[HunkMetadata, ...] = ()

    def __post_init__(self) -> None:
        if self.status not in _STATUSES:
            raise ValueError("file change status is invalid")
        for path in (self.old_path, self.new_path):
            if path is not None:
                _validate_path(path)

    @property
    def path(self) -> PurePosixPath | None:
        return self.new_path or self.old_path

    def to_json_value(self) -> dict[str, object]:
        return {
            "status": self.status,
            "old_path": self.old_path.as_posix() if self.old_path is not None else None,
            "new_path": self.new_path.as_posix() if self.new_path is not None else None,
            "hunks": [item.to_json_value() for item in self.hunks],
        }


@dataclass(frozen=True, slots=True)
class FileChangeSet:
    """Run-level, metadata-only Git evidence for a comparison."""

    files: tuple[FileChange, ...]
    before: str | None = None
    after: str | None = None

    @property
    def changes(self) -> tuple[FileChange, ...]:
        return self.files

    @property
    def count(self) -> int:
        return len(self.files)

    def __iter__(self) -> Iterator[FileChange]:
        return iter(self.files)

    def to_json_value(self) -> dict[str, object]:
        return {
            "schema": "code-structure-viz.file-change-set/v1",
            "before": self.before,
            "after": self.after,
            "files": [item.to_json_value() for item in self.files],
        }


def parse_name_status(payload: bytes) -> tuple[FileChange, ...]:
    """Parse ``git diff --name-status -z`` without retaining patch content."""
    fields = payload.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()
    changes: list[FileChange] = []
    index = 0
    try:
        while index < len(fields):
            status_raw = fields[index].decode("ascii", errors="strict")
            index += 1
            if not status_raw or status_raw[0] not in _STATUSES:
                raise ValueError
            status = status_raw[0]
            if status in {"R", "C"}:
                if _RENAME_STATUS.fullmatch(status_raw) is None:
                    raise ValueError
                if len(status_raw) > 1 and int(status_raw[1:]) > 100:
                    raise ValueError
            elif status_raw != status:
                raise ValueError
            if status in {"R", "C"}:
                old_path: PurePosixPath | None = _decode_path(fields[index])
                new_path: PurePosixPath | None = _decode_path(fields[index + 1])
                index += 2
            else:
                path = _decode_path(fields[index])
                index += 1
                old_path = None if status == "A" else path
                new_path = None if status == "D" else path
            changes.append(FileChange(status, old_path, new_path))
    except (IndexError, UnicodeDecodeError, ValueError) as error:
        raise ValueError("invalid Git name-status protocol") from error
    return tuple(sorted(changes, key=_change_sort_key))


def parse_unified_hunks(
    payload: bytes,
    changes: tuple[FileChange, ...],
) -> tuple[FileChange, ...]:
    """Attach only line-range metadata parsed from a unified diff."""
    if not changes:
        return ()
    if len(payload) > _MAX_UNIFIED_DIFF_BYTES:
        raise ValueError("Git unified diff exceeds the bounded metadata input")
    by_pair = {(item.old_path, item.new_path): item for item in changes}
    by_path = {item.path: item for item in changes if item.path is not None}
    current: FileChange | None = None
    hunks: dict[FileChange, list[HunkMetadata]] = {item: [] for item in changes}
    old_path: PurePosixPath | None = None
    new_path: PurePosixPath | None = None
    in_hunk = False
    for line in payload.splitlines():
        if len(line) > _MAX_UNIFIED_DIFF_LINE_BYTES:
            raise ValueError("Git unified diff line is too long")
        if line.startswith(b"diff --git "):
            current = None
            old_path = None
            new_path = None
            in_hunk = False
            continue
        if not in_hunk and line.startswith(b"--- "):
            old_path = _patch_path(line[4:])
            continue
        if not in_hunk and line.startswith(b"+++ "):
            new_path = _patch_path(line[4:])
            current = by_pair.get((old_path, new_path))
            if current is None:
                current = (by_path.get(new_path) if new_path is not None else None) or (
                    by_path.get(old_path) if old_path is not None else None
                )
            continue
        match = _HUNK.match(line)
        if match is None:
            continue
        if current is None:
            raise ValueError("Git hunk has no matching changed path")
        in_hunk = True
        old_start = int(match["old_start"])
        old_count = int(match["old_count"] or b"1")
        new_start = int(match["new_start"])
        new_count = int(match["new_count"] or b"1")
        ordinal = len(hunks[current])
        hunks[current].append(
            HunkMetadata(
                old_start,
                old_count,
                new_start,
                new_count,
                ordinal,
                current.old_path,
                current.new_path,
                current.status,
            )
        )
    return tuple(
        FileChange(item.status, item.old_path, item.new_path, tuple(hunks[item]))
        for item in changes
    )


def build_file_change_set(
    name_status: bytes,
    patch: bytes,
    *,
    before: str | None = None,
    after: str | None = None,
) -> FileChangeSet:
    changes = parse_name_status(name_status)
    return FileChangeSet(parse_unified_hunks(patch, changes), before=before, after=after)


def attach_content_hunks(
    changes: Iterable[FileChange],
    *,
    before_contents: Mapping[PurePosixPath, bytes],
    after_contents: Mapping[PurePosixPath, bytes],
    before: str | None = None,
    after: str | None = None,
) -> FileChangeSet:
    """Create metadata-only hunks from already-frozen bytes without a Git patch."""
    result: list[FileChange] = []
    for change in changes:
        left = before_contents.get(change.old_path, b"") if change.old_path is not None else b""
        right = after_contents.get(change.new_path, b"") if change.new_path is not None else b""
        hunks: list[HunkMetadata] = []
        for old_start, old_count, new_start, new_count in _line_ranges(left, right):
            hunks.append(
                HunkMetadata(
                    old_start,
                    old_count,
                    new_start,
                    new_count,
                    len(hunks),
                    change.old_path,
                    change.new_path,
                    change.status,
                )
            )
        result.append(FileChange(change.status, change.old_path, change.new_path, tuple(hunks)))
    return FileChangeSet(tuple(sorted(result, key=_change_sort_key)), before=before, after=after)


def build_working_tree_file_change_set(
    before_inventory: Iterable[Any],
    after_inventory: Iterable[Any],
    *,
    untracked_paths: Iterable[PurePosixPath] = (),
    unmerged_paths: Iterable[PurePosixPath] = (),
    before_contents: Mapping[PurePosixPath, bytes] | None = None,
    after_contents: Mapping[PurePosixPath, bytes] | None = None,
    before: str | None = None,
    after: str | None = None,
) -> FileChangeSet:
    """Build a working-tree change inventory without invoking Git's conversion filters."""
    before_map = {item.path: item for item in before_inventory}
    after_map = {item.path: item for item in after_inventory}
    untracked = set(untracked_paths)
    unmerged = set(unmerged_paths)
    changes: list[FileChange] = []
    for path in sorted(
        set(before_map) | set(after_map),
        key=lambda item: item.as_posix().encode("utf-8"),
    ):
        left = before_map.get(path)
        right = after_map.get(path)
        if path in unmerged:
            changes.append(FileChange("U", path, path))
            continue
        # Inventory entries preserve path presence even when content acquisition failed.
        # Only an explicit ``missing`` entry (or no entry) is absent; treating
        # ``unavailable`` as absent would drop an unreadable untracked path from
        # the changed-path budget and make the final drift evidence incomplete.
        left_exists = left is not None and getattr(left, "kind", "missing") != "missing"
        right_exists = right is not None and getattr(right, "kind", "missing") != "missing"
        if not left_exists and not right_exists:
            continue
        if not left_exists:
            changes.append(FileChange("?" if path in untracked else "A", None, path))
            continue
        if not right_exists:
            changes.append(FileChange("D", path, None))
            continue
        if getattr(left, "kind", None) != getattr(right, "kind", None) or getattr(
            left, "digest", None
        ) != getattr(right, "digest", None):
            changes.append(FileChange("M", path, path))
    return attach_content_hunks(
        changes,
        before_contents=before_contents or {},
        after_contents=after_contents or {},
        before=before,
        after=after,
    )


def _line_ranges(before: bytes, after: bytes) -> tuple[tuple[int, int, int, int], ...]:
    left = before.splitlines()
    right = after.splitlines()
    ranges: list[tuple[int, int, int, int]] = []
    for tag, old_start, old_end, new_start, new_end in SequenceMatcher(
        a=left,
        b=right,
        autojunk=False,
    ).get_opcodes():
        if tag == "equal":
            continue
        old_count = old_end - old_start
        new_count = new_end - new_start
        ranges.append(
            (
                old_start if old_count == 0 else old_start + 1,
                old_count,
                new_start if new_count == 0 else new_start + 1,
                new_count,
            )
        )
    return tuple(ranges)


def _decode_path(value: bytes) -> PurePosixPath:
    text = value.decode("utf-8", errors="strict")
    normalized_text = unicodedata.normalize("NFC", text)
    path = PurePosixPath(normalized_text)
    if (
        not text
        or normalized_text != text
        or path.is_absolute()
        or "\\" in text
        or "\x00" in text
        or any(ord(character) < 0x20 or ord(character) == 0x7F for character in text)
        or path.as_posix() != text
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValueError
    return path


def _validate_path(path: PurePosixPath) -> None:
    text = path.as_posix()
    if (
        path.is_absolute()
        or "\\" in text
        or "\x00" in text
        or any(ord(character) < 0x20 or ord(character) == 0x7F for character in text)
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValueError("file change path is invalid")


def _patch_path(value: bytes) -> PurePosixPath | None:
    token = value.split(b"\t", 1)[0]
    if token.startswith(b'"'):
        token = _decode_git_quoted_path(token)
    if token == b"/dev/null":
        return None
    if token.startswith(b"a/") or token.startswith(b"b/"):
        token = token[2:]
    try:
        return _decode_path(token)
    except (UnicodeDecodeError, ValueError):
        raise ValueError("Git patch path is not a safe UTF-8 path") from None


def _decode_git_quoted_path(value: bytes) -> bytes:
    if len(value) < 2 or value[-1:] != b'"':
        raise ValueError("Git patch path is not a closed quoted path")
    encoded = value[1:-1]
    decoded = bytearray()
    index = 0
    escapes = {
        ord("a"): 0x07,
        ord("b"): 0x08,
        ord("t"): 0x09,
        ord("n"): 0x0A,
        ord("v"): 0x0B,
        ord("f"): 0x0C,
        ord("r"): 0x0D,
    }
    while index < len(encoded):
        byte = encoded[index]
        index += 1
        if byte != ord("\\"):
            decoded.append(byte)
            continue
        if index >= len(encoded):
            raise ValueError("Git patch path has a dangling escape")
        escaped = encoded[index]
        index += 1
        if escaped in escapes:
            decoded.append(escapes[escaped])
            continue
        if escaped in {ord('"'), ord("\\")}:
            decoded.append(escaped)
            continue
        if escaped not in b"01234567" or index + 1 >= len(encoded):
            raise ValueError("Git patch path has an unsupported escape")
        octal = bytes((escaped, encoded[index], encoded[index + 1]))
        if any(character not in b"01234567" for character in octal):
            raise ValueError("Git patch path has an invalid octal escape")
        decoded.append(int(octal, 8))
        index += 2
    return bytes(decoded)


def _change_sort_key(value: FileChange) -> bytes:
    path = value.path
    return (path.as_posix() if path is not None else "").encode("utf-8")


__all__ = [
    "FileChange",
    "FileChangeSet",
    "HunkMetadata",
    "attach_content_hunks",
    "build_file_change_set",
    "build_working_tree_file_change_set",
    "parse_name_status",
    "parse_unified_hunks",
]
