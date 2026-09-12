import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest
from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from code_structure_viz.adapters.next.applicability import (
    PackageApplicabilityEvidence,
    PackageApplicabilityState,
    derive_package_applicability_matrix,
)

ROOT = Path(__file__).resolve().parents[3]


def test_applicability_uses_only_direct_next_dependencies_and_canonical_order() -> None:
    matrix = derive_package_applicability_matrix(
        {
            "apps/plain/package.json": (
                b'{"name":"plain","optionalDependencies":{"next":"15"},'
                b'"peerDependencies":{"next":"15"}}'
            ),
            "apps/web/package.json": b'{"devDependencies":{"next":"^15"}}',
        },
        ("apps/plain", "apps/web", "."),
    )

    assert matrix.aggregate_state is PackageApplicabilityState.APPLICABLE
    assert tuple(item.project_root for item in matrix.entries) == (
        ".",
        "apps/plain",
        "apps/web",
    )
    assert tuple(item.state for item in matrix.entries) == (
        PackageApplicabilityState.NON_APPLICABLE,
        PackageApplicabilityState.NON_APPLICABLE,
        PackageApplicabilityState.APPLICABLE,
    )
    assert matrix.as_dict() == {
        "schema": "code-structure-viz.next-package-applicability/v1",
        "version": 1,
        "projects": [
            {
                "project_root": ".",
                "package_path": "package.json",
                "state": "non_applicable",
                "evidence": "missing_package",
            },
            {
                "project_root": "apps/plain",
                "package_path": "apps/plain/package.json",
                "state": "non_applicable",
                "evidence": "no_direct_next",
            },
            {
                "project_root": "apps/web",
                "package_path": "apps/web/package.json",
                "state": "applicable",
                "evidence": "direct_next_dependency",
            },
        ],
        "aggregate_state": "applicable",
        "applicable_projects": ["apps/web"],
        "non_applicable_projects": [".", "apps/plain"],
    }


@pytest.mark.parametrize(
    "payload",
    [
        b"{",
        b"\xff",
        b"\xef\xbb\xbf\xef\xbb\xbf{}",
        b"[]",
        b'{"dependencies":[]}',
        b'{"dependencies":{"next":"  "}}',
        b'{"dependencies":{"next":"15"},"devDependencies":{"next":"15"}}',
        b'{"dependencies":{"next":"15","next":"16"}}',
        b'{"name":"plain","name":"duplicate"}',
        b'{"dependencies":{"next":NaN}}',
    ],
)
def test_malformed_package_bytes_fail_closed(payload: bytes) -> None:
    matrix = derive_package_applicability_matrix({"package.json": payload}, (".",))

    assert matrix.aggregate_state is PackageApplicabilityState.MALFORMED
    assert matrix.entries[0].state is PackageApplicabilityState.MALFORMED
    assert matrix.entries[0].evidence == "malformed_package"


def test_valid_single_bom_package_and_dependencies_next_are_applicable() -> None:
    matrix = derive_package_applicability_matrix(
        {"package.json": b'\xef\xbb\xbf{"dependencies":{"next":"15"}}'},
        (".",),
    )

    assert matrix.aggregate_state is PackageApplicabilityState.APPLICABLE
    assert matrix.entries[0].evidence == "direct_next_dependency"


def test_observation_value_exposes_only_safe_package_byte_identities() -> None:
    payload = b'{"dependencies":{"next":"15"}}'
    matrix = derive_package_applicability_matrix({"package.json": payload}, (".",))

    assert matrix.observation_value() == {
        "matrix": matrix.as_dict(),
        "packages": [
            {
                "path": "package.json",
                "state": "read",
                "sha256": hashlib.sha256(payload).hexdigest(),
                "size_bytes": len(payload),
                "failure_code": None,
            }
        ],
    }
    assert payload.decode() not in json.dumps(matrix.observation_value())


def test_matrix_matches_the_checked_in_closed_schema() -> None:
    schema = cast(
        dict[str, Any],
        json.loads((ROOT / "schemas/next-package-applicability-v1.schema.json").read_text()),
    )
    matrix = derive_package_applicability_matrix(
        {"apps/web/package.json": b'{"dependencies":{"next":"15"}}'},
        ("apps/web",),
    )

    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(matrix.as_dict())


def test_observed_bytes_prevent_forging_the_derived_applicability() -> None:
    matrix = derive_package_applicability_matrix(
        {"package.json": b'{"dependencies":{"next":"15"}}'},
        (".",),
    )
    forged_entry = replace(
        matrix.entries[0],
        state=PackageApplicabilityState.NON_APPLICABLE,
        evidence=PackageApplicabilityEvidence.NO_DIRECT_NEXT,
    )

    with pytest.raises(ValueError, match="derived from observed package bytes"):
        replace(
            matrix,
            entries=(forged_entry,),
            aggregate_state=PackageApplicabilityState.NON_APPLICABLE,
        )


@pytest.mark.parametrize(
    "project_root",
    ["", "/absolute", "apps//web", "apps/../web", "apps/./web", r"apps\web", "cafe\u0301"],
)
def test_project_roots_must_be_canonical_repository_relative_paths(project_root: str) -> None:
    with pytest.raises(ValueError):
        derive_package_applicability_matrix({}, (project_root,))


def test_duplicate_project_roots_are_rejected() -> None:
    with pytest.raises(ValueError, match="unique"):
        derive_package_applicability_matrix({}, (".", "."))
