"""Offline NFC conformance against the official Unicode 15.0.0 vectors."""

from __future__ import annotations

import base64
import hashlib
import json
import unicodedata
import zlib
from pathlib import Path

import pytest

from tests.contracts.unicode_15_0_nfc import normalize_nfc

FIXTURE = Path(__file__).parents[1] / "fixtures" / "unicode_15_0_nfc_normalization.json"


def test_official_unicode_15_nfc_conformance(monkeypatch: pytest.MonkeyPatch) -> None:
    """Check all five NFC equalities, including multi-scalar ordering/blocking."""

    def reject_host_database(*args: object, **kwargs: object) -> None:
        raise AssertionError("the frozen NFC profile must not use the host UCD")

    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert fixture["unicode_version"] == "15.0.0"
    assert fixture["source_sha256"] == (
        "fb9ac8cc154a80cad6caac9897af55a4e75176af6f4e2bb6edc2bf8b1d57f326"
    )
    assert fixture["encoding"] == "base64+zlib+utf8"
    raw = zlib.decompress(base64.b64decode(fixture["rows"], validate=True))
    assert hashlib.sha256(raw).hexdigest() == fixture["rows_sha256"]
    rows = raw.decode("utf-8").splitlines()
    assert len(rows) == fixture["row_count"] == 19074
    # Restore the host functions before pytest renders its own result; its
    # terminal-width calculation legitimately uses unicodedata.normalize().
    with monkeypatch.context() as isolated:
        for name in ("normalize", "combining", "decomposition"):
            isolated.setattr(unicodedata, name, reject_host_database)
        for number, row in enumerate(rows, 1):
            columns = [
                "".join(chr(int(codepoint, 16)) for codepoint in column.split())
                for column in row.split(";")
            ]
            assert len(columns) == 5
            expected = [columns[1], columns[1], columns[1], columns[3], columns[3]]
            for source, target in zip(columns, expected, strict=True):
                assert normalize_nfc(source) == target, (number, source, target)


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("日本語/か\u3099.tsx", "日本語/が.tsx"),
        ("\u1100\u1161\u11a8", "각"),
        ("\u1100\u0301\u1161", "\u1100\u0301\u1161"),
        ("a\u0315\u0300", "à\u0315"),
        ("\u0344", "\u0308\u0301"),
        ("Ω\u0301", "Ώ"),
    ],
)
def test_nfc_combines_only_unblocked_pairs(source: str, expected: str) -> None:
    assert normalize_nfc(source) == expected
    assert normalize_nfc(expected) == expected
