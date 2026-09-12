import hashlib
import json
import unicodedata
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest
from jsonschema import Draft202012Validator, ValidationError  # type: ignore[import-untyped]
from referencing import Registry, Resource

from code_structure_viz.adapters.next.applicability import (
    PackageApplicabilityEvidence,
    PackageApplicabilityState,
    derive_package_applicability_matrix,
)
from code_structure_viz.core.unicode_15_0_nfc import (
    NFC_TABLE_DIGEST as PRODUCT_NFC_TABLE_DIGEST,
)
from code_structure_viz.core.unicode_15_0_nfc import (
    normalize_nfc as normalize_product_nfc,
)
from code_structure_viz.core.unicode_15_0_nfc import (
    verify_full_scalar_kat as verify_product_nfc_full_scalar_kat,
)
from tests.contracts.unicode_15_0_nfc import (
    NFC_TABLE_DIGEST as REFERENCE_NFC_TABLE_DIGEST,
)
from tests.contracts.unicode_15_0_nfc import (
    normalize_nfc as normalize_reference_nfc,
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


@pytest.mark.parametrize("payload", ["not bytes", 7])
def test_non_byte_package_input_is_rejected_as_invalid_observation(payload: object) -> None:
    package_bytes = cast(Any, {"package.json": payload})

    with pytest.raises(ValueError, match="frozen bytes or be missing"):
        derive_package_applicability_matrix(package_bytes, (".",))


def test_package_json_recursion_error_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_recursion_error(*_args: Any, **_kwargs: Any) -> Any:
        raise RecursionError("injected parser recursion limit")

    with monkeypatch.context() as scoped_monkeypatch:
        scoped_monkeypatch.setattr(json, "loads", raise_recursion_error)
        matrix = derive_package_applicability_matrix({"package.json": b"{}"}, (".",))

    assert matrix.aggregate_state is PackageApplicabilityState.MALFORMED
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
    path_schema = cast(
        dict[str, Any],
        json.loads((ROOT / "schemas/next-path-v1.schema.json").read_text()),
    )
    root_path_schema = cast(
        dict[str, Any],
        json.loads((ROOT / "schemas/next-root-or-path-v1.schema.json").read_text()),
    )
    matrix = derive_package_applicability_matrix(
        {"apps/web/package.json": b'{"dependencies":{"next":"15"}}'},
        ("apps/web",),
    )
    registry = (
        Registry()
        .with_resource(
            "urn:code-structure-viz:schema:next-path-v1",
            Resource.from_contents(path_schema),
        )
        .with_resource(
            "urn:code-structure-viz:schema:next-root-or-path-v1",
            Resource.from_contents(root_path_schema),
        )
    )

    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, registry=registry)
    value = matrix.as_dict()
    validator.validate(value)

    fragment_path = matrix.as_dict()
    fragment_path["projects"][0]["project_root"] = "apps/web#x"
    with pytest.raises(ValidationError):
        validator.validate(fragment_path)

    oversized_path = matrix.as_dict()
    oversized_path["projects"][0]["package_path"] = "x" * 4097
    with pytest.raises(ValidationError):
        validator.validate(oversized_path)


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


def test_observed_package_rows_reject_mutable_inner_lists() -> None:
    payload = b'{"dependencies":{"next":"15"}}'
    matrix = derive_package_applicability_matrix({"package.json": payload}, (".",))
    row: list[Any] = ["package.json", payload]

    with pytest.raises(ValueError, match="immutable rows"):
        replace(matrix, _observed_package_bytes=cast(Any, (row,)))

    row[1] = b"{}"
    assert (
        matrix.observation_value()["packages"][0]["sha256"] == hashlib.sha256(payload).hexdigest()
    )


@pytest.mark.parametrize(
    "project_root",
    [
        "",
        "/absolute",
        "apps//web",
        "apps/../web",
        "apps/./web",
        "apps/web#x",
        r"apps\web",
        "cafe\u0301",
    ],
)
def test_project_roots_must_be_canonical_repository_relative_paths(project_root: str) -> None:
    with pytest.raises(ValueError):
        derive_package_applicability_matrix({}, (project_root,))


def test_project_and_package_paths_enforce_inclusive_4096_byte_limit() -> None:
    accepted_root = "apps/" + "x" * 4078
    rejected_root = "apps/" + "x" * 4079

    matrix = derive_package_applicability_matrix({}, (accepted_root,))

    assert len(matrix.entries[0].package_path.encode("utf-8")) == 4096
    with pytest.raises(ValueError):
        derive_package_applicability_matrix({}, (rejected_root,))


def test_project_roots_use_the_frozen_unicode_15_nfc_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = "apps/\U000105d2\u0307"

    assert PRODUCT_NFC_TABLE_DIGEST == REFERENCE_NFC_TABLE_DIGEST
    assert normalize_product_nfc(root) == normalize_reference_nfc(root) == root

    def reject_host_normalization(*_args: Any, **_kwargs: Any) -> str:
        raise AssertionError("host Unicode normalization must not be consulted")

    with monkeypatch.context() as scoped_monkeypatch:
        scoped_monkeypatch.setattr(unicodedata, "normalize", reject_host_normalization)
        matrix = derive_package_applicability_matrix({}, (root,))

    assert matrix.entries[0].project_root == root


def test_product_unicode_15_nfc_matches_the_full_scalar_known_answer() -> None:
    verify_product_nfc_full_scalar_kat()


def test_duplicate_project_roots_are_rejected() -> None:
    with pytest.raises(ValueError, match="unique"):
        derive_package_applicability_matrix({}, (".", "."))
