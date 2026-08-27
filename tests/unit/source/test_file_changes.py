from __future__ import annotations

from pathlib import PurePosixPath

import pytest

from code_structure_viz.source.file_changes import (
    FileChange,
    build_working_tree_file_change_set,
    parse_name_status,
    parse_unified_hunks,
)
from code_structure_viz.source.source_view import SourceInventoryEntry


def _inventory(path: str, digest: str) -> SourceInventoryEntry:
    return SourceInventoryEntry(PurePosixPath(path), path, "regular", 1, digest)


def test_working_tree_change_set_counts_untracked_and_unmerged_paths() -> None:
    before = (_inventory("src/changed.py", "a"),)
    after = (
        _inventory("src/changed.py", "b"),
        _inventory("src/new.txt", "c"),
        _inventory("src/conflict.py", "d"),
    )

    result = build_working_tree_file_change_set(
        before,
        after,
        untracked_paths=(PurePosixPath("src/new.txt"),),
        unmerged_paths=(PurePosixPath("src/conflict.py"),),
    )

    assert [(item.status, item.path) for item in result] == [
        ("M", PurePosixPath("src/changed.py")),
        ("U", PurePosixPath("src/conflict.py")),
        ("?", PurePosixPath("src/new.txt")),
    ]


def test_unified_hunk_parser_rejects_unbounded_metadata() -> None:
    change = FileChange("M", PurePosixPath("src/app.py"), PurePosixPath("src/app.py"))

    with pytest.raises(ValueError):
        parse_unified_hunks(
            (b"x" * (16 * 1024 * 1024 + 1)),
            (change,),
        )


def test_unified_hunk_parser_decodes_git_quoted_utf8_paths() -> None:
    path = PurePosixPath("src/café.py")
    change = parse_name_status("M\0src/café.py\0".encode())[0]

    result = parse_unified_hunks(
        b'diff --git "a/src/caf\\303\\251.py" "b/src/caf\\303\\251.py"\n'
        b'--- "a/src/caf\\303\\251.py"\n'
        b'+++ "b/src/caf\\303\\251.py"\n'
        b"@@ -1 +1 @@\n",
        (change,),
    )

    assert result[0].path == path
    assert result[0].hunks[0].old_start == 1
    with pytest.raises(ValueError):
        parse_unified_hunks(
            b"diff --git a/src/app.py b/src/app.py\n"
            b"--- a/src/app.py\n"
            b"+++ b/src/app.py\n"
            b"@@ -1 +1 @@\n" + (b"x" * (128 * 1024 + 1)),
            (change,),
        )
