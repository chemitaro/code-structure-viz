from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from difflib import SequenceMatcher
from enum import StrEnum
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


class ContentSideState(StrEnum):
    ABSENT = "absent"
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class ContentEvidence:
    state: ContentSideState
    content: bytes | None = None

    def __post_init__(self) -> None:
        if self.state is ContentSideState.AVAILABLE:
            if not isinstance(self.content, bytes):
                raise ValueError("available content evidence requires bytes")
        elif self.content is not None:
            raise ValueError("non-available content evidence cannot retain bytes")


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
    before_contents: Mapping[PurePosixPath, ContentEvidence],
    after_contents: Mapping[PurePosixPath, ContentEvidence],
    before: str | None = None,
    after: str | None = None,
) -> FileChangeSet:
    """Create metadata-only hunks from already-frozen bytes without a Git patch."""
    result: list[FileChange] = []
    for change in changes:
        left = _content_side(change.old_path, before_contents)
        right = _content_side(change.new_path, after_contents)
        hunks: list[HunkMetadata] = []
        if (
            change.status not in {"T", "U"}
            and left.state is not ContentSideState.UNAVAILABLE
            and right.state is not ContentSideState.UNAVAILABLE
        ):
            left_content = left.content if left.state is ContentSideState.AVAILABLE else b""
            right_content = right.content if right.state is ContentSideState.AVAILABLE else b""
            assert left_content is not None
            assert right_content is not None
            for old_start, old_count, new_start, new_count in _line_ranges(
                left_content, right_content
            ):
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
    before: str | None = None,
    after: str | None = None,
) -> FileChangeSet:
    """Build a working-tree change inventory without invoking Git's conversion filters."""
    before_map = {item.path: item for item in before_inventory}
    after_map = {item.path: item for item in after_inventory}
    changes: list[FileChange] = []
    deleted: dict[PurePosixPath, Any] = {}
    added: dict[PurePosixPath, Any] = {}
    classified_same_paths: set[PurePosixPath] = set()
    for path in sorted(
        set(before_map) | set(after_map),
        key=lambda item: item.as_posix().encode("utf-8"),
    ):
        left = before_map.get(path)
        right = after_map.get(path)
        if any(
            item is not None and bool(getattr(item, "unmerged", False)) for item in (left, right)
        ):
            changes.append(FileChange("U", path, path))
            classified_same_paths.add(path)
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
            assert right is not None
            added[path] = right
            continue
        if not right_exists:
            assert left is not None
            deleted[path] = left
            continue
        left_tracking = getattr(left, "tracking_state", "tracked")
        right_tracking = getattr(right, "tracking_state", "tracked")
        if left_tracking == "tracked" and right_tracking == "untracked":
            changes.extend((FileChange("D", path, None), FileChange("?", None, path)))
            classified_same_paths.add(path)
            continue
        left_kind = getattr(left, "kind", None)
        right_kind = getattr(right, "kind", None)
        if left_kind != right_kind:
            status = (
                "T"
                if left_kind in {"regular", "symlink", "gitlink"}
                and right_kind in {"regular", "symlink", "gitlink"}
                else "M"
            )
            changes.append(FileChange(status, path, path))
            classified_same_paths.add(path)
            continue
        if getattr(left, "git_mode", None) != getattr(right, "git_mode", None) or getattr(
            left, "digest", None
        ) != getattr(right, "digest", None):
            changes.append(FileChange("M", path, path))
            classified_same_paths.add(path)

    sources_by_identity: dict[tuple[str, str], list[PurePosixPath]] = {}
    additions_by_identity: dict[tuple[str, str], list[PurePosixPath]] = {}
    for path, state in before_map.items():
        if path in classified_same_paths:
            continue
        identity = _cross_path_identity(state)
        if identity is not None:
            sources_by_identity.setdefault(identity, []).append(path)
    for path, state in added.items():
        identity = _cross_path_identity(state)
        if identity is not None:
            additions_by_identity.setdefault(identity, []).append(path)

    consumed_deleted: set[PurePosixPath] = set()
    consumed_added: set[PurePosixPath] = set()
    for new_path in sorted(added, key=lambda item: item.as_posix().encode("utf-8")):
        identity = _cross_path_identity(added[new_path])
        if identity is None:
            continue
        candidates = sorted(
            sources_by_identity.get(identity, ()),
            key=lambda item: item.as_posix().encode("utf-8"),
        )
        if len(candidates) != 1:
            continue
        old_path = candidates[0]
        if old_path in deleted:
            if len(additions_by_identity.get(identity, ())) != 1:
                continue
            changes.append(FileChange("R", old_path, new_path))
            consumed_deleted.add(old_path)
            consumed_added.add(new_path)
            continue
        retained = after_map.get(old_path)
        if retained is None or _cross_path_identity(retained) != identity:
            continue
        changes.append(FileChange("C", old_path, new_path))
        consumed_added.add(new_path)

    for path in sorted(deleted, key=lambda item: item.as_posix().encode("utf-8")):
        if path not in consumed_deleted:
            changes.append(FileChange("D", path, None))
    for path in sorted(added, key=lambda item: item.as_posix().encode("utf-8")):
        if path not in consumed_added:
            tracking_state = getattr(added[path], "tracking_state", "tracked")
            changes.append(FileChange("?" if tracking_state == "untracked" else "A", None, path))
    return FileChangeSet(tuple(sorted(changes, key=_change_sort_key)), before=before, after=after)


def _cross_path_identity(value: Any) -> tuple[str, str] | None:
    kind = getattr(value, "kind", None)
    digest = getattr(value, "digest", None)
    if kind not in {"regular", "symlink", "gitlink"} or not isinstance(digest, str):
        return None
    return kind, digest


def _line_ranges(before: bytes, after: bytes) -> tuple[tuple[int, int, int, int], ...]:
    left = before.splitlines(keepends=True)
    right = after.splitlines(keepends=True)
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


def content_evidence_from_inventory(
    inventory: Iterable[Any],
) -> dict[PurePosixPath, ContentEvidence]:
    evidence: dict[PurePosixPath, ContentEvidence] = {}
    for item in inventory:
        availability = getattr(item, "availability", "unavailable")
        content = getattr(item, "content", None)
        digest = getattr(item, "digest", None)
        if availability == "absent":
            evidence[item.path] = ContentEvidence(ContentSideState.ABSENT)
            continue
        if (
            availability == "available"
            and isinstance(content, bytes)
            and isinstance(digest, str)
            and hashlib.sha256(content).hexdigest() == digest
            and b"\0" not in content
            and len(content) <= _MAX_UNIFIED_DIFF_BYTES
            and all(
                len(line) <= _MAX_UNIFIED_DIFF_LINE_BYTES
                for line in content.splitlines(keepends=True)
            )
        ):
            evidence[item.path] = ContentEvidence(ContentSideState.AVAILABLE, content)
            continue
        evidence[item.path] = ContentEvidence(ContentSideState.UNAVAILABLE)
    return evidence


def unavailable_content_paths(
    changes: Iterable[FileChange],
    *,
    before_contents: Mapping[PurePosixPath, ContentEvidence],
    after_contents: Mapping[PurePosixPath, ContentEvidence],
) -> tuple[frozenset[PurePosixPath], frozenset[PurePosixPath]]:
    before_paths: set[PurePosixPath] = set()
    after_paths: set[PurePosixPath] = set()
    for change in changes:
        if change.status in {"T", "U"}:
            continue
        if (
            change.old_path is not None
            and _content_side(change.old_path, before_contents).state
            is ContentSideState.UNAVAILABLE
        ):
            before_paths.add(change.old_path)
        if (
            change.new_path is not None
            and _content_side(change.new_path, after_contents).state is ContentSideState.UNAVAILABLE
        ):
            after_paths.add(change.new_path)
    return frozenset(before_paths), frozenset(after_paths)


def _content_side(
    path: PurePosixPath | None,
    contents: Mapping[PurePosixPath, ContentEvidence],
) -> ContentEvidence:
    if path is None:
        return ContentEvidence(ContentSideState.ABSENT)
    return contents.get(path, ContentEvidence(ContentSideState.UNAVAILABLE))


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
    "ContentEvidence",
    "ContentSideState",
    "FileChange",
    "FileChangeSet",
    "HunkMetadata",
    "attach_content_hunks",
    "build_file_change_set",
    "build_working_tree_file_change_set",
    "content_evidence_from_inventory",
    "parse_name_status",
    "parse_unified_hunks",
    "unavailable_content_paths",
]
