"""Immutable locks for unchanged trusted-profile-v1 semantics, without file I/O.

This reference metadata is not a TypeScript runtime, shipping license inventory,
or production certificate. Its declarations and symbol inventory are cross-
checked against the separately preserved v1 fixtures by contract tests.
"""

from typing import Any

from tests.contracts.ecmascript_unicode_15_0 import TABLE_DIGEST

TRUSTED_PACKAGE_PREFIX = "code_structure_viz/_next_runtime/trusted/"
TRUSTED_VIRTUAL_PREFIX = "/.code-structure-viz/trusted/v1/"
PROFILE_DECLARATIONS = (
    (
        "jsx-runtime.d.ts",
        206,
        "183bcc7eba1b976a64ade01e69fdf5afd1e950875a10b249fb0f4249af31f2f9",
        "MIT",
    ),
    (
        "lib.d.ts",
        291,
        "105f7ededf9f525497cb630ecb83f4c3a9b4c794d556ecc81354b17c52d18612",
        "Apache-2.0",
    ),
    (
        "next-dynamic.d.ts",
        101,
        "fce0a8ae25c2ded5c8150382c252069c5ee2aeac2846aa9aec24a9e05cc5c496",
        "MIT",
    ),
    (
        "react.d.ts",
        306,
        "951003ddcbcc330f98cdfd5fda390cadb745f7ba606d46bf73657f50dc9b67eb",
        "MIT",
    ),
)
RESERVED_MODULES = ("react", "react/jsx-runtime", "react/jsx-dev-runtime", "next/dynamic")
RESERVED_GLOBALS = ("Array", "JSX", "ReadonlyArray")
# source kind, source name, export name, declaration basename, symbol kind,
# signature digest. Order is the unchanged v1 symbol-key order.
PROFILE_SYMBOLS = (
    (
        "global",
        "Array",
        "flatMap",
        "lib.d.ts",
        "method",
        "ce26c01a0913f0e1789d723203f97bc685782061f5e1887d912d0bf8ed030243",
    ),
    (
        "global",
        "Array",
        "map",
        "lib.d.ts",
        "method",
        "2a4fc05abc17216b5f78b70a9862f1ba4e9e66e572d95ee68579f801f16abe3e",
    ),
    (
        "global",
        "JSX",
        "Element",
        "lib.d.ts",
        "interface",
        "03ea2064bad083bfe241623533099136e79e0f10a0aaa4565e832cadf37df6ae",
    ),
    (
        "global",
        "ReadonlyArray",
        "flatMap",
        "lib.d.ts",
        "method",
        "8dce2a540376e4c013c130151b9b86f02669f799ca4448a12ffbdc6d9c9707cf",
    ),
    (
        "global",
        "ReadonlyArray",
        "map",
        "lib.d.ts",
        "method",
        "7807241ac0924f4ec44a0b5d085bc0072458e7f40f0fe76d7c17153bf59b9cfd",
    ),
    (
        "module",
        "next/dynamic",
        "default",
        "next-dynamic.d.ts",
        "function",
        "136ffae8c0d221bf9c8f24344489768c4190761d2445fb1db83637db1c7921d2",
    ),
    (
        "module",
        "react",
        "Component",
        "react.d.ts",
        "class",
        "1a1abfd545db8d313c360c5f4036071adc2fa259fda8cd710746fa9ed165f936",
    ),
    (
        "module",
        "react",
        "createElement",
        "react.d.ts",
        "function",
        "c7fd9c7ed6977b44cef35675ec68bf794577f587d55ce2ebe6e64249addc1000",
    ),
    (
        "module",
        "react",
        "forwardRef",
        "react.d.ts",
        "function",
        "a47df2a57427b421e9627713d631486d76fda38f9364270293d467f6cbae2f3a",
    ),
    (
        "module",
        "react",
        "lazy",
        "react.d.ts",
        "function",
        "c2b6970e4b9be52581842a2426b8b311fe3ff64d9b9c617262e8677be33a6376",
    ),
    (
        "module",
        "react",
        "memo",
        "react.d.ts",
        "function",
        "90ff99f96e7779f65b9c9612a949a14f3a7de6db2071336096c2ab76a771c0d4",
    ),
    (
        "module",
        "react/jsx-runtime",
        "Fragment",
        "jsx-runtime.d.ts",
        "variable",
        "dcb27ea3d78837b2225d8da2c1421d643f3c8c5e2e331344a3eb36011e21f8c9",
    ),
    (
        "module",
        "react/jsx-runtime",
        "jsx",
        "jsx-runtime.d.ts",
        "function",
        "a449b678c50d76ff600c731ef6f8697cb96ee0ce4a8de7a3e1cad7caca15bdb1",
    ),
    (
        "module",
        "react/jsx-runtime",
        "jsxs",
        "jsx-runtime.d.ts",
        "function",
        "fb58326dc9e6d1d99d0aeb63c2076921c47dc1c2df3f50fb027bf3753033e0dd",
    ),
)


def trusted_profile_metadata_v1() -> dict[str, Any]:
    """Fresh reference projection of the fixed profile, not caller metadata."""

    declaration_hashes = {name: sha for name, _size, sha, _license in PROFILE_DECLARATIONS}
    return {
        "typescript_version": "5.9.2",
        "identifier_unicode_table_digest": TABLE_DIGEST,
        "license_inventory_digest": (
            "473c908d234c02e497c4f0ff5bcc7a626dd8b488e487ec3c7f7202ae1c9e1ea8"
        ),
        "reserved_module_specifiers": list(RESERVED_MODULES),
        "reserved_global_names": list(RESERVED_GLOBALS),
        "certified_symbols": [
            {
                "source_kind": kind,
                "source_name": name,
                "export_path": [export],
                "declaration_sha256": declaration_hashes[declaration],
                "symbol_kind": symbol_kind,
                "signature_digest": signature,
            }
            for kind, name, export, declaration, symbol_kind, signature in PROFILE_SYMBOLS
        ],
        "anti_shadowing_witness": [
            {"source_kind": kind, "source_name": name, "decision": "reserved"}
            for kind, names in (("module", RESERVED_MODULES), ("global", RESERVED_GLOBALS))
            for name in names
        ],
    }
