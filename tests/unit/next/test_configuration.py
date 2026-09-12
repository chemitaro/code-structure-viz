from __future__ import annotations

from typing import Any, cast

import pytest

from code_structure_viz.adapters.next.configuration import (
    NextConfigurationError,
    parse_control_jsonc,
)


def test_project_control_jsonc_accepts_bom_comments_and_trailing_commas() -> None:
    payload = (
        b"\xef\xbb\xbf{\r\n"
        b"  // root comment\r\n"
        b'  "extends": "./config/base.json", /* comma before comment */\r\n'
        b'  "include": ["src/**/*.tsx", /* trailing comment */],\r\n'
        b'  "metadata": {"url": "https://example.test/a//b", "note": "/* literal */"},\r\n'
        b"}"
    )

    assert parse_control_jsonc(payload, path="tsconfig.json") == {
        "extends": "./config/base.json",
        "include": ["src/**/*.tsx"],
        "metadata": {
            "url": "https://example.test/a//b",
            "note": "/* literal */",
        },
    }


@pytest.mark.parametrize(
    "payload",
    [
        b'{"name":"first","name":"second"}',
        b'{"nested":{"name":"first","name":"second"}}',
        b'{"value":NaN}',
        b'{"value":Infinity}',
        b'{"value":-Infinity}',
        b'{"value":1e999}',
        b"\xef\xbb\xbf\xef\xbb\xbf{}",
        b'{"value": [1, /* never closed],}',
        b'{"value": "never closed}',
        b'{"value": 1,,}',
        b'{"value":\xc2\xa01}',
        b"\xff",
    ],
)
def test_project_control_jsonc_rejects_ambiguous_or_malformed_bytes(payload: bytes) -> None:
    with pytest.raises(NextConfigurationError) as error:
        parse_control_jsonc(payload, path="tsconfig.json")

    assert error.value.code == "CSV-NEXT-CONFIG-001"
    assert error.value.stage == "source_control"
    assert error.value.path == "tsconfig.json"


@pytest.mark.parametrize("payload", [b"[]", b"null", b'"object"', b"1", b"true"])
def test_project_control_jsonc_requires_an_object_root(payload: bytes) -> None:
    with pytest.raises(NextConfigurationError, match="root must be an object"):
        parse_control_jsonc(payload, path="jsconfig.json")


def test_project_control_jsonc_rejects_non_byte_observations() -> None:
    with pytest.raises(NextConfigurationError, match="frozen bytes"):
        parse_control_jsonc(cast(Any, "{}"), path="tsconfig.json")
