from __future__ import annotations

from typing import Any, cast

import pytest

from code_structure_viz.adapters.next.configuration import (
    NextConfigurationError,
    parse_control_jsonc,
    resolve_control_closure,
)


def test_project_control_jsonc_accepts_bom_comments_and_trailing_commas() -> None:
    payload = (
        b"\xef\xbb\xbf{\r\n"
        b"  // root comment\r\n"
        b'  "extends": "./config/base.json", /* comma before comment */\r\n'
        b'  "include": ["src/**/*.tsx", /* trailing comment */],\r\n'
        b'  "count": 1/* separating comment */, /* trailing comment */\r\n'
        b'  "metadata": {"url": "https://example.test/a//b", "note": "/* literal */"},\r\n'
        b"}"
    )

    assert parse_control_jsonc(payload, path="tsconfig.json") == {
        "extends": "./config/base.json",
        "include": ["src/**/*.tsx"],
        "count": 1,
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
        b'{"value":1/* comment */2}',
        b'{"value":1// comment\n2}',
        b"{,}",
        b'{"value":[,]}',
        b'{"value":[1,,]}',
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


def test_project_control_closure_resolves_local_extends_from_frozen_bytes() -> None:
    shared = "apps/web/config/shared.json"
    base = "apps/web/config/base.json"
    child = "apps/web/tsconfig.json"
    resolved = resolve_control_closure(
        {
            child: (
                b'{"extends":"./config/base.json",'
                b'"compilerOptions":{"jsx":"react-jsx",'
                b'"paths":{"@app/*":["src/*"]}},"exclude":[".next/**"]}'
            ),
            base: (
                b'{"extends":"./shared.json",'
                b'"compilerOptions":{"module":"esnext","baseUrl":"..",'
                b'"paths":{"@base/*":["base/*"]}},"include":["src/**/*.tsx"]}'
            ),
            shared: (
                b'{"compilerOptions":{"allowJs":false,"jsx":"preserve",'
                b'"baseUrl":"."},"include":["shared/**/*.tsx"],'
                b'"exclude":["dist/**"]}'
            ),
        },
        project_root="apps/web",
        config_path=child,
    )

    assert resolved.values == {
        "compilerOptions": {
            "allowJs": False,
            "jsx": "react-jsx",
            "baseUrl": "..",
            "module": "esnext",
            "paths": {"@app/*": ["src/*"]},
        },
        "include": ["src/**/*.tsx"],
        "exclude": [".next/**"],
    }
    assert resolved.declaring_paths == {
        "compilerOptions.allowJs": shared,
        "compilerOptions.jsx": child,
        "compilerOptions.baseUrl": base,
        "compilerOptions.module": base,
        "compilerOptions.paths": child,
        "include": base,
        "exclude": child,
    }
    assert resolved.control_paths == (shared, base, child)
    assert resolved.extends_edges == ((base, shared), (child, base))


def test_project_control_closure_preserves_explicit_empty_membership_values() -> None:
    resolved = resolve_control_closure(
        {
            "tsconfig.base.json": b'{"include":["src/**/*.tsx"],"exclude":["dist/**"]}',
            "tsconfig.json": b'{"extends":"./tsconfig.base.json","include":[]}',
        },
        project_root=".",
        config_path="tsconfig.json",
    )

    assert resolved.values["include"] == []
    assert resolved.values["exclude"] == ["dist/**"]
    assert resolved.declaring_paths["include"] == "tsconfig.json"


@pytest.mark.parametrize(
    ("payload", "expected_code"),
    [
        (b'{"extends":null}', "CSV-NEXT-CONFIG-001"),
        (b'{"extends":["./base.json"]}', "CSV-NEXT-CONFIG-001"),
        (b'{"extends":"../base.json"}', "CSV-NEXT-CONFIG-001"),
        (b'{"extends":"./config/../base.json"}', "CSV-NEXT-CONFIG-001"),
        (b'{"extends":"/base.json"}', "CSV-NEXT-CONFIG-001"),
        (b'{"extends":"./config//base.json"}', "CSV-NEXT-CONFIG-001"),
        (b'{"extends":"./"}', "CSV-NEXT-CONFIG-001"),
        (b'{"extends":"base.json"}', "CSV-NEXT-CONFIG-002"),
        (b'{"extends":"@shared/tsconfig"}', "CSV-NEXT-CONFIG-002"),
        (b'{"extends":"https://example.test/tsconfig.json"}', "CSV-NEXT-CONFIG-002"),
        (b'{"extends":"./https://example.test/tsconfig.json"}', "CSV-NEXT-CONFIG-002"),
    ],
)
def test_project_control_closure_rejects_non_local_extends(
    payload: bytes, expected_code: str
) -> None:
    with pytest.raises(NextConfigurationError) as error:
        resolve_control_closure(
            {"tsconfig.json": payload}, project_root=".", config_path="tsconfig.json"
        )

    assert error.value.code == expected_code
    assert error.value.stage == "source_control"
    assert error.value.path == "tsconfig.json"


def test_project_control_closure_rejects_missing_parent_and_cycles() -> None:
    with pytest.raises(NextConfigurationError, match="not captured") as missing:
        resolve_control_closure(
            {"tsconfig.json": b'{"extends":"./missing.json"}'},
            project_root=".",
            config_path="tsconfig.json",
        )

    assert missing.value.code == "CSV-NEXT-CONFIG-001"

    with pytest.raises(NextConfigurationError, match="cycle") as cycle:
        resolve_control_closure(
            {
                "tsconfig.json": b'{"extends":"./base.json"}',
                "base.json": b'{"extends":"./tsconfig.json"}',
            },
            project_root=".",
            config_path="tsconfig.json",
        )

    assert cycle.value.code == "CSV-NEXT-CONFIG-001"


def test_project_control_closure_requires_controls_inside_the_selected_project() -> None:
    with pytest.raises(NextConfigurationError, match="outside the project root"):
        resolve_control_closure(
            {"apps/admin/tsconfig.json": b"{}"},
            project_root="apps/web",
            config_path="apps/admin/tsconfig.json",
        )

    with pytest.raises(NextConfigurationError, match="not captured"):
        resolve_control_closure({}, project_root="apps/web", config_path="apps/web/tsconfig.json")


@pytest.mark.parametrize(
    "payload",
    [
        b'{"extends":"./base.json","unknown":true}',
        b'{"extends":"./base.json","compilerOptions":null}',
    ],
)
def test_project_control_closure_rejects_open_control_shapes(payload: bytes) -> None:
    with pytest.raises(NextConfigurationError) as error:
        resolve_control_closure(
            {"tsconfig.json": payload, "base.json": b"{}"},
            project_root=".",
            config_path="tsconfig.json",
        )

    assert error.value.code == "CSV-NEXT-CONFIG-001"
