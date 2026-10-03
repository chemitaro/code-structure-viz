"""Public catalog diagnostics from the actual v3 run/Core/runtime owners."""

import hashlib
import json
from importlib import import_module, util
from pathlib import Path

import pytest
from jsonschema import ValidationError  # type: ignore[import-untyped]

from tests.contracts.next_final_publication_v2_fixtures import (
    complete_candidates_v3,
    entity_budget_candidates_v3,
    export_failure_candidates_v3,
    rejected_candidates_v3,
    source_failure_candidates_v3,
    stage_failed_candidates_v3,
    target_failure_candidates_v3,
)
from tests.contracts.test_next_semantic_core_v3 import MODULE_IDS

NODE_002_JSONL = (
    b'{"code":"CSV-NEXT-NODE-002","domain":"next","line":null,'
    b'"message":"The Next.js adapter process could not be started.",'
    b'"outcome":"payload_unavailable","path":null,"recoverable":false,'
    b'"ref_permission":"none","schema":"code-structure-viz.diagnostic/v1",'
    b'"severity":"error","symbol":null,"type":"diagnostic"}\n'
)


def test_stage_failure_public_diagnostic_has_catalog_owned_literal_bytes(tmp_path: Path) -> None:
    run = stage_failed_candidates_v3(tmp_path).run_decision()
    module = "tests.contracts.next_public_diagnostic_v3_reference"
    assert util.find_spec(module) is not None, "actual run has no v3 public diagnostic seam"
    diagnostics = import_module(module).derive_public_diagnostics_v3(run)
    encoded = b"".join(
        json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode() + b"\n"
        for row in diagnostics
    )
    assert encoded == NODE_002_JSONL
    assert len(encoded) == 304
    assert hashlib.sha256(encoded).hexdigest() == (
        "ad6bbccccd3625a88f2b4f0f00bcb9dd3597296198c28fe785a6fcd5171b8a9d"
    )


def test_diagnostic_validator_rejects_message_substitution(tmp_path: Path) -> None:
    run = stage_failed_candidates_v3(tmp_path).run_decision()
    module = "tests.contracts.next_public_diagnostic_v3_validation"
    assert util.find_spec(module) is not None, "public diagnostics have no independent validator"
    validate = import_module(module).validate_public_diagnostics_v3
    row = json.loads(NODE_002_JSONL)
    validate((row,), run)
    with pytest.raises((AssertionError, ValueError)):
        validate(({**row, "message": "private child stderr"},), run)


@pytest.mark.parametrize("kind", ["parse_file", "read_file"])
def test_source_unavailable_diagnostic_projects_only_the_actual_failure_root(
    tmp_path: Path, kind: str
) -> None:
    run = source_failure_candidates_v3(tmp_path, kind).run_decision()
    derive = import_module(
        "tests.contracts.next_public_diagnostic_v3_reference"
    ).derive_public_diagnostics_v3
    validate = import_module(
        "tests.contracts.next_public_diagnostic_v3_validation"
    ).validate_public_diagnostics_v3
    expected = (
        {
            "type": "diagnostic",
            "schema": "code-structure-viz.diagnostic/v1",
            "domain": "next",
            "code": "CSV-NEXT-SOURCE-003",
            "severity": "error",
            "recoverable": False,
            "message": "A Next.js source failure cannot be isolated to a safe subset.",
            "outcome": "payload_unavailable",
            "ref_permission": "path",
            "path": "src/value.ts",
            "symbol": None,
            "line": None,
        },
    )
    diagnostics = derive(run)
    assert diagnostics == expected
    validate(expected, run)
    with pytest.raises((ValueError, AssertionError)):
        validate(({**expected[0], "path": "src/button.tsx"},), run)


def test_target_failure_diagnostic_retains_the_proven_path_and_reason(tmp_path: Path) -> None:
    run = target_failure_candidates_v3(tmp_path).run_decision()
    derive = import_module(
        "tests.contracts.next_public_diagnostic_v3_reference"
    ).derive_public_diagnostics_v3
    validate = import_module(
        "tests.contracts.next_public_diagnostic_v3_validation"
    ).validate_public_diagnostics_v3
    expected = (
        {
            "type": "diagnostic",
            "schema": "code-structure-viz.diagnostic/v1",
            "domain": "next",
            "code": "CSV-NEXT-TARGET-001",
            "severity": "error",
            "recoverable": False,
            "message": "An explicit Next.js target cannot be resolved uniquely.",
            "outcome": "payload_unavailable",
            "ref_permission": "path_or_symbol",
            "path": "src/button.tsx",
            "symbol": None,
            "line": None,
            "reason": "missing",
        },
    )
    assert derive(run) == expected
    validate(expected, run)
    with pytest.raises((ValueError, AssertionError)):
        validate(({**expected[0], "reason": "out_of_scope"},), run)


def test_export_failure_diagnostic_exposes_only_the_validated_owner_module(tmp_path: Path) -> None:
    run = export_failure_candidates_v3(tmp_path).run_decision()
    derive = import_module(
        "tests.contracts.next_public_diagnostic_v3_reference"
    ).derive_public_diagnostics_v3
    validate = import_module(
        "tests.contracts.next_public_diagnostic_v3_validation"
    ).validate_public_diagnostics_v3
    expected = (
        {
            "type": "diagnostic",
            "schema": "code-structure-viz.diagnostic/v1",
            "domain": "next",
            "code": "CSV-NEXT-EXPORT-001",
            "severity": "error",
            "recoverable": False,
            "message": "A component export cannot be resolved uniquely.",
            "outcome": "payload_unavailable",
            "ref_permission": "symbol",
            "path": None,
            "symbol": MODULE_IDS["src/value.ts"],
            "line": None,
        },
    )
    assert derive(run) == expected
    validate(expected, run)
    with pytest.raises((ValueError, AssertionError)):
        validate(({**expected[0], "symbol": MODULE_IDS["src/button.tsx"]},), run)


def test_entity_budget_diagnostic_contains_no_private_count_or_ref(tmp_path: Path) -> None:
    run = entity_budget_candidates_v3(tmp_path).run_decision()
    derive = import_module(
        "tests.contracts.next_public_diagnostic_v3_reference"
    ).derive_public_diagnostics_v3
    validate = import_module(
        "tests.contracts.next_public_diagnostic_v3_validation"
    ).validate_public_diagnostics_v3
    expected = (
        {
            **json.loads(NODE_002_JSONL),
            "code": "CSV-NEXT-LIMIT-005",
            "message": "The semantic model or entity count exceeded its configured limit.",
        },
    )
    assert derive(run) == expected
    validate(expected, run)
    with pytest.raises(ValidationError):
        validate(({**expected[0], "count": 4},), run)


def test_complete_core_diagnostic_is_the_catalog_projection_of_its_safe_symbol(
    tmp_path: Path,
) -> None:
    run = complete_candidates_v3(tmp_path).run_decision()
    derive = import_module(
        "tests.contracts.next_public_diagnostic_v3_reference"
    ).derive_public_diagnostics_v3
    validate = import_module(
        "tests.contracts.next_public_diagnostic_v3_validation"
    ).validate_public_diagnostics_v3
    expected = (
        {
            **json.loads(NODE_002_JSONL),
            "code": "CSV-NEXT-UNSUPPORTED-001",
            "severity": "info",
            "recoverable": True,
            "message": "A runtime-dependent pattern is intentionally represented as unknown.",
            "outcome": "complete",
            "ref_permission": "symbol",
            "symbol": MODULE_IDS["src/value.ts"],
        },
    )
    assert derive(run) == expected
    validate(expected, run)
    with pytest.raises((ValueError, AssertionError)):
        validate(({**expected[0], "symbol": MODULE_IDS["src/index.ts"]},), run)


@pytest.mark.parametrize("kind", ["parse_file", "read_file"])
def test_isolated_source_diagnostic_preserves_partial_safe_root_without_proof_leak(
    tmp_path: Path, kind: str
) -> None:
    run = source_failure_candidates_v3(tmp_path, kind, isolated=True).run_decision()
    derive = import_module(
        "tests.contracts.next_public_diagnostic_v3_reference"
    ).derive_public_diagnostics_v3
    validate = import_module(
        "tests.contracts.next_public_diagnostic_v3_validation"
    ).validate_public_diagnostics_v3
    expected = (
        {
            **json.loads(NODE_002_JSONL),
            "code": "CSV-NEXT-SOURCE-001",
            "recoverable": True,
            "message": "A source file could not be analyzed safely.",
            "outcome": "partial_safe",
            "ref_permission": "path",
            "path": "src/value.ts",
        },
    )
    assert derive(run) == expected
    validate(expected, run)
    with pytest.raises(ValidationError):
        validate(({**expected[0], "affected_paths": ["src/value.ts"]},), run)


def test_rejected_core_diagnostic_uses_only_the_closed_rejection_classification(
    tmp_path: Path,
) -> None:
    run = rejected_candidates_v3(tmp_path).run_decision()
    derive = import_module(
        "tests.contracts.next_public_diagnostic_v3_reference"
    ).derive_public_diagnostics_v3
    validate = import_module(
        "tests.contracts.next_public_diagnostic_v3_validation"
    ).validate_public_diagnostics_v3
    expected = (
        {
            **json.loads(NODE_002_JSONL),
            "code": "CSV-NEXT-PROTOCOL-001",
            "message": "The Next.js adapter response violates the private protocol.",
        },
    )
    assert derive(run) == expected
    validate(expected, run)
    assert expected[0]["path"] is None and expected[0]["symbol"] is None
