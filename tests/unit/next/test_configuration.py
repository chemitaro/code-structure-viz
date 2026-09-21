from __future__ import annotations

from typing import Any, cast

import pytest

from code_structure_viz.adapters.next.configuration import (
    NextConfigurationError,
    parse_control_jsonc,
    resolve_compiler_options,
    resolve_control_closure,
    resolve_membership,
    resolve_project_configuration,
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


def test_project_membership_resolves_files_from_declaring_config() -> None:
    closure = resolve_control_closure(
        {
            "apps/web/config/base.json": (
                b'{"files":["component.tsx","legacy.jsx"],"exclude":["ignored.tsx"]}'
            ),
            "apps/web/tsconfig.json": b'{"extends":"./config/base.json"}',
        },
        project_root="apps/web",
        config_path="apps/web/tsconfig.json",
    )

    resolved = resolve_membership(
        closure,
        project_root="apps/web",
        inventory_paths=(
            "apps/web/config/component.tsx",
            "apps/web/config/legacy.jsx",
            "apps/web/config/ignored.tsx",
            "apps/web/component.tsx",
        ),
    )

    assert resolved.kind == "files"
    assert resolved.patterns == (
        "apps/web/config/component.tsx",
        "apps/web/config/legacy.jsx",
    )
    assert resolved.exclude == ()
    assert resolved.source_roots == ("apps/web/config",)
    assert resolved.paths == (
        "apps/web/config/component.tsx",
        "apps/web/config/legacy.jsx",
    )


def test_project_membership_applies_segment_globs_and_excludes_to_descendants() -> None:
    closure = resolve_control_closure(
        {
            "apps/web/config/base.json": (
                b'{"include":["src/**/*.tsx"],"exclude":["src/**/*-ignored.tsx"]}'
            ),
            "apps/web/tsconfig.json": b'{"extends":"./config/base.json"}',
        },
        project_root="apps/web",
        config_path="apps/web/tsconfig.json",
    )

    resolved = resolve_membership(
        closure,
        project_root="apps/web",
        inventory_paths=(
            "apps/web/config/src/index.tsx",
            "apps/web/config/src/pages/home.tsx",
            "apps/web/config/src/pages/home-ignored.tsx",
            "apps/web/config/src/pages/types.d.ts",
            "apps/web/src/root-home.tsx",
        ),
    )

    assert resolved.kind == "include"
    assert resolved.patterns == ("apps/web/config/src/**/*.tsx",)
    assert resolved.exclude == ("apps/web/config/src/**/*-ignored.tsx",)
    assert resolved.source_roots == ("apps/web/config/src",)
    assert resolved.paths == (
        "apps/web/config/src/index.tsx",
        "apps/web/config/src/pages/home.tsx",
    )


def test_project_membership_question_mark_matches_one_character() -> None:
    closure = resolve_control_closure(
        {"tsconfig.json": b'{"include":["src/page?.tsx"]}'},
        project_root=".",
        config_path="tsconfig.json",
    )

    resolved = resolve_membership(
        closure,
        project_root=".",
        inventory_paths=("src/page1.tsx", "src/page.tsx", "src/page12.tsx"),
    )

    assert resolved.patterns == ("src/page?.tsx",)
    assert resolved.paths == ("src/page1.tsx",)


def test_project_membership_defaults_to_src_and_respects_allow_js() -> None:
    closure = resolve_control_closure(
        {
            "apps/web/tsconfig.json": (
                b'{"compilerOptions":{"allowJs":false},"exclude":["src/**/excluded-*.tsx"]}'
            )
        },
        project_root="apps/web",
        config_path="apps/web/tsconfig.json",
    )

    resolved = resolve_membership(
        closure,
        project_root="apps/web",
        inventory_paths=(
            "apps/web/src/app.tsx",
            "apps/web/src/global.d.ts",
            "apps/web/src/legacy.js",
            "apps/web/src/legacy.jsx",
            "apps/web/src/pages/excluded-private.tsx",
            "apps/web/pages/outside-src.tsx",
        ),
    )

    assert resolved.kind == "default"
    assert resolved.patterns == ("apps/web/src",)
    assert resolved.exclude == ("apps/web/src/**/excluded-*.tsx",)
    assert resolved.source_roots == ("apps/web/src",)
    assert resolved.paths == ("apps/web/src/app.tsx", "apps/web/src/global.d.ts")


@pytest.mark.parametrize(
    ("authority", "expected_source_root"),
    [("files", "apps/web"), ("include", "apps/web/src")],
)
def test_project_membership_empty_authority_does_not_select_default_files(
    authority: str, expected_source_root: str
) -> None:
    closure = resolve_control_closure(
        {"apps/web/tsconfig.json": f'{{"{authority}":[]}}'.encode()},
        project_root="apps/web",
        config_path="apps/web/tsconfig.json",
    )

    resolved = resolve_membership(
        closure,
        project_root="apps/web",
        inventory_paths=("apps/web/src/app.tsx", "apps/web/app.tsx"),
    )

    assert resolved.kind == authority
    assert resolved.patterns == ()
    assert resolved.exclude == ()
    assert resolved.source_roots == (expected_source_root,)
    assert resolved.paths == ()


@pytest.mark.parametrize(
    "payload",
    [
        b'{"files":[],"include":[]}',
        b'{"include":"src/**/*.tsx"}',
        b'{"include":["src/foo**/nested.tsx"]}',
        b'{"include":["src/[ab].tsx"]}',
        b'{"files":["src/**/*.tsx"]}',
    ],
)
def test_project_membership_rejects_ambiguous_or_unsupported_patterns(payload: bytes) -> None:
    closure = resolve_control_closure(
        {"tsconfig.json": payload}, project_root=".", config_path="tsconfig.json"
    )

    with pytest.raises(NextConfigurationError) as error:
        resolve_membership(closure, project_root=".", inventory_paths=("src/app.tsx",))

    assert error.value.code == "CSV-NEXT-CONFIG-001"
    assert error.value.stage == "source_control"
    assert error.value.path == "tsconfig.json"


def test_project_membership_rejects_declaring_config_escape() -> None:
    closure = resolve_control_closure(
        {"apps/web/tsconfig.json": b'{"include":["../../shared/**/*.tsx"]}'},
        project_root="apps/web",
        config_path="apps/web/tsconfig.json",
    )

    with pytest.raises(NextConfigurationError) as error:
        resolve_membership(
            closure,
            project_root="apps/web",
            inventory_paths=("apps/web/src/app.tsx",),
        )

    assert error.value.code == "CSV-NEXT-CONFIG-001"
    assert error.value.stage == "source_control"
    assert error.value.path == "apps/web/tsconfig.json"


@pytest.mark.parametrize(
    "inventory_paths",
    [
        ("src//app.tsx",),
        ("src/cafe\u0301.tsx",),
        ("src/app.tsx", "src/app.tsx"),
    ],
)
def test_project_membership_rejects_noncanonical_or_duplicated_inventory_paths(
    inventory_paths: tuple[str, ...],
) -> None:
    closure = resolve_control_closure(
        {"tsconfig.json": b"{}"}, project_root=".", config_path="tsconfig.json"
    )

    with pytest.raises(NextConfigurationError) as error:
        resolve_membership(closure, project_root=".", inventory_paths=inventory_paths)

    assert error.value.code == "CSV-NEXT-CONFIG-001"
    assert error.value.stage == "source_control"


def test_project_configuration_seals_selected_config_and_derived_membership() -> None:
    resolved = resolve_project_configuration(
        {
            "apps/web/tsconfig.json": b'{"extends":"./config/base.json"}',
            "apps/web/jsconfig.json": b"{",
            "apps/web/config/base.json": (
                b'{"include":["src/**/*.tsx"],"compilerOptions":{"allowJs":false}}'
            ),
        },
        project_root="apps/web",
        control_candidates=("jsconfig.json", "tsconfig.json"),
        inventory_paths=(
            "apps/web/config/src/app.tsx",
            "apps/web/src/not-selected.tsx",
        ),
    )

    assert resolved.config_path == "apps/web/tsconfig.json"
    assert resolved.control_paths == (
        "apps/web/config/base.json",
        "apps/web/tsconfig.json",
    )
    assert resolved.extends_edges == (("apps/web/tsconfig.json", "apps/web/config/base.json"),)
    assert resolved.project_value() == {
        "root": "apps/web",
        "source_roots": ["apps/web/config/src"],
        "config_path": "apps/web/tsconfig.json",
        "compiler_options": {
            "allow_js": False,
            "check_js": False,
            "jsx": "preserve",
            "module": "esnext",
            "module_resolution": "bundler",
            "base_url": None,
            "paths": {},
        },
    }
    assert resolved.config_resolution_value() == {
        "project_root": "apps/web",
        "config_path": "apps/web/tsconfig.json",
        "declaring_paths": [
            {"option": "allowJs", "path": "apps/web/config/base.json"},
            {"option": "include", "path": "apps/web/config/base.json"},
        ],
        "membership": {
            "kind": "include",
            "patterns": ["apps/web/config/src/**/*.tsx"],
            "exclude": [],
        },
        "path_resolution_order": [],
    }


def test_project_configuration_uses_builtin_defaults_when_no_candidate_is_observed() -> None:
    resolved = resolve_project_configuration(
        {},
        project_root=".",
        control_candidates=(),
        inventory_paths=("src/app.tsx", "pages/app.tsx"),
    )

    assert resolved.config_path is None
    assert resolved.control_paths == ()
    assert resolved.project_value() == {
        "root": ".",
        "source_roots": ["src"],
        "config_path": None,
        "compiler_options": {
            "allow_js": True,
            "check_js": False,
            "jsx": "preserve",
            "module": "esnext",
            "module_resolution": "bundler",
            "base_url": None,
            "paths": {},
        },
    }
    assert resolved.config_resolution_value() == {
        "project_root": ".",
        "config_path": None,
        "declaring_paths": [],
        "membership": {"kind": "default", "patterns": ["src"], "exclude": []},
        "path_resolution_order": [],
    }


def test_project_configuration_rejects_observed_root_config_omitted_from_candidates() -> None:
    with pytest.raises(NextConfigurationError) as error:
        resolve_project_configuration(
            {"apps/web/tsconfig.json": b"{}"},
            project_root="apps/web",
            control_candidates=(),
            inventory_paths=(),
        )

    assert error.value.code == "CSV-NEXT-CONFIG-001"
    assert error.value.stage == "source_control"


def test_project_configuration_can_select_jsconfig_without_reading_tsconfig() -> None:
    resolved = resolve_project_configuration(
        {
            "jsconfig.json": b'{"compilerOptions":{"allowJs":false}}',
        },
        project_root=".",
        control_candidates=("jsconfig.json",),
        inventory_paths=("src/app.jsx", "src/app.tsx"),
    )

    assert resolved.config_path == "jsconfig.json"
    assert resolved.control_paths == ("jsconfig.json",)
    assert resolved.compiler_options.allow_js is False
    assert resolved.membership.paths == ("src/app.tsx",)


@pytest.mark.parametrize(
    "control_candidates",
    [("package.json",), ("tsconfig.json", "tsconfig.json")],
)
def test_project_configuration_rejects_open_or_duplicated_control_candidates(
    control_candidates: tuple[str, ...],
) -> None:
    with pytest.raises(NextConfigurationError) as error:
        resolve_project_configuration(
            {},
            project_root=".",
            control_candidates=control_candidates,
            inventory_paths=(),
        )

    assert error.value.code == "CSV-NEXT-CONFIG-001"
    assert error.value.stage == "source_control"


def test_project_compiler_options_apply_defaults_and_declaring_config_paths() -> None:
    closure = resolve_control_closure(
        {
            "apps/web/config/base.json": (
                b'{"compilerOptions":{"jsx":"react-jsx","baseUrl":".",'
                b'"paths":{"@shared/*":["src/shared/*"]}}}'
            ),
            "apps/web/tsconfig.json": (
                b'{"extends":"./config/base.json","compilerOptions":{"allowJs":false}}'
            ),
        },
        project_root="apps/web",
        config_path="apps/web/tsconfig.json",
    )

    resolved = resolve_compiler_options(closure, project_root="apps/web")

    assert resolved.as_dict() == {
        "allow_js": False,
        "check_js": False,
        "jsx": "react-jsx",
        "module": "esnext",
        "module_resolution": "bundler",
        "base_url": "apps/web/config",
        "paths": {"@shared/*": ["apps/web/config/src/shared/*"]},
    }
    assert resolved.path_resolution_order == ("@shared/*",)


def test_project_compiler_options_allow_paths_replacement_at_nested_project_root() -> None:
    closure = resolve_control_closure(
        {"apps/web/tsconfig.json": (b'{"compilerOptions":{"paths":{"@app":["."]}}}')},
        project_root="apps/web",
        config_path="apps/web/tsconfig.json",
    )

    resolved = resolve_compiler_options(closure, project_root="apps/web")

    assert resolved.as_dict()["paths"] == {"@app": ["apps/web"]}


def test_project_compiler_options_use_closed_defaults_without_a_base_url() -> None:
    closure = resolve_control_closure(
        {"tsconfig.json": b"{}"}, project_root=".", config_path="tsconfig.json"
    )

    resolved = resolve_compiler_options(closure, project_root=".")

    assert resolved.as_dict() == {
        "allow_js": True,
        "check_js": False,
        "jsx": "preserve",
        "module": "esnext",
        "module_resolution": "bundler",
        "base_url": None,
        "paths": {},
    }
    assert resolved.path_resolution_order == ()


def test_project_compiler_options_order_path_aliases_by_specificity() -> None:
    closure = resolve_control_closure(
        {
            "tsconfig.json": (
                b'{"compilerOptions":{"paths":{"@*":["src/*"],'
                b'"@ui/*":["ui/*"],"@ui/Button":["button"]}}}'
            )
        },
        project_root=".",
        config_path="tsconfig.json",
    )

    resolved = resolve_compiler_options(closure, project_root=".")

    assert resolved.path_resolution_order == ("@ui/Button", "@ui/*", "@*")
    assert resolved.as_dict()["paths"] == {
        "@*": ["src/*"],
        "@ui/*": ["ui/*"],
        "@ui/Button": ["button"],
    }


def test_project_compiler_options_validate_ignored_build_options_without_using_them() -> None:
    closure = resolve_control_closure(
        {
            "tsconfig.json": (
                b'{"compilerOptions":{"noEmit":true,"outDir":"dist",'
                b'"target":"ES2022","lib":["ES2022"]}}'
            )
        },
        project_root=".",
        config_path="tsconfig.json",
    )

    resolved = resolve_compiler_options(closure, project_root=".")

    assert resolved.as_dict() == {
        "allow_js": True,
        "check_js": False,
        "jsx": "preserve",
        "module": "esnext",
        "module_resolution": "bundler",
        "base_url": None,
        "paths": {},
    }
    assert "compilerOptions.noEmit" in closure.declaring_paths


@pytest.mark.parametrize(
    ("payload", "expected_code"),
    [
        (b'{"compilerOptions":{"plugins":[]}}', "CSV-NEXT-CONFIG-002"),
        (b'{"compilerOptions":{"typeRoots":["types"]}}', "CSV-NEXT-CONFIG-002"),
        (b'{"compilerOptions":{"types":[]}}', "CSV-NEXT-CONFIG-002"),
        (b'{"compilerOptions":{"unknownOption":true}}', "CSV-NEXT-CONFIG-001"),
        (b'{"compilerOptions":{"allowJs":"yes"}}', "CSV-NEXT-CONFIG-001"),
        (b'{"compilerOptions":{"checkJs":null}}', "CSV-NEXT-CONFIG-001"),
        (b'{"compilerOptions":{"jsx":"automatic"}}', "CSV-NEXT-CONFIG-001"),
        (b'{"compilerOptions":{"jsx":[]}}', "CSV-NEXT-CONFIG-001"),
        (b'{"compilerOptions":{"module":"commonjs"}}', "CSV-NEXT-CONFIG-001"),
        (b'{"compilerOptions":{"moduleResolution":"node"}}', "CSV-NEXT-CONFIG-001"),
        (b'{"compilerOptions":{"baseUrl":"../outside"}}', "CSV-NEXT-CONFIG-001"),
        (b'{"compilerOptions":{"declaration":"yes"}}', "CSV-NEXT-CONFIG-001"),
        (b'{"compilerOptions":{"lib":"ES2022"}}', "CSV-NEXT-CONFIG-001"),
        (b'{"compilerOptions":{"paths":null}}', "CSV-NEXT-CONFIG-001"),
        (b'{"compilerOptions":{"paths":{"@/*":[]}}}', "CSV-NEXT-CONFIG-001"),
        (b'{"compilerOptions":{"paths":{"@app":["."]}}}', "CSV-NEXT-CONFIG-001"),
        (
            b'{"compilerOptions":{"paths":{"@/*":["../outside/*"]}}}',
            "CSV-NEXT-CONFIG-001",
        ),
    ],
)
def test_project_compiler_options_reject_unsupported_values(
    payload: bytes, expected_code: str
) -> None:
    closure = resolve_control_closure(
        {"tsconfig.json": payload}, project_root=".", config_path="tsconfig.json"
    )

    with pytest.raises(NextConfigurationError) as error:
        resolve_compiler_options(closure, project_root=".")

    assert error.value.code == expected_code
    assert error.value.stage == "source_control"


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
