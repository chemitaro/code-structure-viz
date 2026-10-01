"""Locked semantic algorithms; the new envelope does not change their meaning."""

from typing import Any

from tests.contracts.ecmascript_unicode_15_0 import ALGORITHM_VERSION, TABLE_DIGEST
from tests.contracts.unicode_15_0_nfc import FULL_SCALAR_KAT_DIGEST, NFC_TABLE_DIGEST


def semantic_compatibility_metadata_v2() -> dict[str, Any]:
    """Fresh constant profile metadata, never a supplied runtime observation."""

    return {
        "semantic_schema": "code-structure-viz.semantic/v2",
        "identity_versions": {
            name: 1
            for name in (
                "project",
                "file",
                "module",
                "component",
                "member",
                "relation",
                "fact",
                "props_ir",
            )
        },
        "algorithm_versions": {
            "recognition": 1,
            "export": 1,
            "props": 1,
            "relation": 1,
            "fact": 1,
            "boundary": 1,
            "identifier_unicode": ALGORITHM_VERSION,
            "identifier_unicode_table_digest": TABLE_DIGEST,
        },
        "semantic_profile_id": "next-trusted-profile-v1",
        "unicode_profile": {
            "profile_id": "unicode-15.0.0-nfc-v1",
            "unicode_version": "15.0.0",
            "normalization": "NFC",
            "algorithm_version": "unicode-nfc-15.0.0",
            "table_digest": NFC_TABLE_DIGEST,
            "full_scalar_kat_digest": FULL_SCALAR_KAT_DIGEST,
        },
        "runtime_binding_profile_id": "next-public-spawn-runtime-v1",
    }
