from __future__ import annotations

from typing import cast

import pytest

from code_structure_viz.semantic.canonical_json import encode_canonical_json
from code_structure_viz.source.file_changes import build_file_change_set, parse_name_status


def test_file_change_set_keeps_ranges_and_drops_raw_patch_content() -> None:
    name_status = b"M\0src/app.py\0"
    patch = (
        b"diff --git a/src/app.py b/src/app.py\n"
        b"--- a/src/app.py\n"
        b"+++ b/src/app.py\n"
        b"@@ -1,1 +1,1 @@\n"
        b"-API_TOKEN=super-secret\n"
        b"+API_TOKEN=rotated-secret\n"
    )

    value = build_file_change_set(name_status, patch).to_json_value()
    encoded = encode_canonical_json(value)
    files = cast(list[dict[str, object]], value["files"])
    file_value = files[0]
    hunks = cast(list[dict[str, object]], file_value["hunks"])

    assert file_value["old_path"] == "src/app.py"
    assert file_value["new_path"] == "src/app.py"
    assert file_value["hunks"] == [
        {
            "old_start": 1,
            "old_line_count": 1,
            "new_start": 1,
            "new_line_count": 1,
            "ordinal": 0,
            "hunk_id": hunks[0]["hunk_id"],
        }
    ]
    assert b"super-secret" not in encoded
    assert b"rotated-secret" not in encoded
    assert b"@@" not in encoded


def test_hunk_id_is_independent_of_patch_body() -> None:
    name_status = b"M\0src/app.py\0"
    first = build_file_change_set(
        name_status,
        b"--- a/src/app.py\n+++ b/src/app.py\n@@ -3 +3 @@\n-old\n+new\n",
    )
    second = build_file_change_set(
        name_status,
        b"--- a/src/app.py\n+++ b/src/app.py\n@@ -3 +3 @@\n-secret-a\n+secret-b\n",
    )

    assert first.to_json_value() == second.to_json_value()


@pytest.mark.parametrize(
    "payload",
    (
        b"M100\0src/app.py\0",
        b"R999\0src/old.py\0src/new.py\0",
        b"M\0src/../app.py\0",
        b"M\0src/unsafe\nname.py\0",
    ),
)
def test_name_status_protocol_rejects_ambiguous_or_unsafe_metadata(payload: bytes) -> None:
    with pytest.raises(ValueError):
        parse_name_status(payload)
