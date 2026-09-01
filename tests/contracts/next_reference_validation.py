"""Data-only reference checks for the Issue #8 pre-implementation contract.

The production adapter is intentionally absent.  These checks model the
Python-side validation boundary that will consume an untrusted adapter
response and are kept in tests so that the contract can be exercised now.
"""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, TypedDict, cast
from urllib.parse import urlparse

from jsonschema import Draft202012Validator, ValidationError  # type: ignore[import-untyped]
from referencing import Registry, Resource

from tests.contracts.ecmascript_unicode_15_0 import (
    ALGORITHM_VERSION as _ECMASCRIPT_IDENTIFIER_UNICODE_VERSION,
)
from tests.contracts.ecmascript_unicode_15_0 import (
    ID_CONTINUE_INTERVALS as ECMASCRIPT_ID_CONTINUE_INTERVALS,
)
from tests.contracts.ecmascript_unicode_15_0 import (
    ID_START_INTERVALS as ECMASCRIPT_ID_START_INTERVALS,
)
from tests.contracts.ecmascript_unicode_15_0 import (
    JOIN_CONTROL as ECMASCRIPT_JOIN_CONTROL,
)
from tests.contracts.ecmascript_unicode_15_0 import (
    OTHER_ID_CONTINUE as ECMASCRIPT_OTHER_ID_CONTINUE_CODEPOINTS,
)
from tests.contracts.ecmascript_unicode_15_0 import (
    OTHER_ID_START as ECMASCRIPT_OTHER_ID_START_CODEPOINTS,
)
from tests.contracts.ecmascript_unicode_15_0 import (
    TABLE_DIGEST as _ECMASCRIPT_IDENTIFIER_UNICODE_TABLE_DIGEST,
)
from tests.contracts.ecmascript_unicode_15_0 import (
    contains as _unicode_table_contains,
)

ECMASCRIPT_IDENTIFIER_UNICODE_VERSION: str = _ECMASCRIPT_IDENTIFIER_UNICODE_VERSION
ECMASCRIPT_IDENTIFIER_UNICODE_TABLE_DIGEST: str = _ECMASCRIPT_IDENTIFIER_UNICODE_TABLE_DIGEST

VALIDATOR_SCHEMA = "code-structure-viz.next-reference-validation/v1"
CATALOG_PATH = Path(__file__).resolve().parents[2] / "schemas" / "next-diagnostic-catalog-v1.json"
COLLECTIONS = ("projects", "files", "modules", "components", "members", "relations", "facts")
# There are seven non-empty subsets of the three closed roles.  Keep this
# tuple in wire order; the subset/effective-role invariant is checked below.
ROLES = ("control", "context", "program")
ROLE_ORDER = {role: index for index, role in enumerate(ROLES)}
# The tuple above is the canonical wire order.  Precedence is intentionally a
# separate mapping: a lower sort index is the stronger role, while the
# effective role is selected by precedence rather than by whichever role was
# appended last.
ROLE_PRECEDENCE = {"control": 3, "context": 2, "program": 1}
FORMAT_ORDER = ("semantic-json", "plantuml")
FORMAT_ORDER_INDEX = {format_name: index for index, format_name in enumerate(FORMAT_ORDER)}
RUN_CONTEXT_BUDGET_SOURCES = ("builtin", "repository", "explicit", "cli")
RUN_CONTEXT_SELECTORS = (None, "manifest", *(f"next:{format_name}" for format_name in FORMAT_ORDER))
TAINTS = {
    "parse_file",
    "read_file",
    "type_symbol",
    "export_binding",
    "props_subtree",
    "component_flow",
    "module_relation",
    "boundary_derivation",
}
TAINT_ORDER = (
    "parse_file",
    "read_file",
    "type_symbol",
    "export_binding",
    "props_subtree",
    "component_flow",
    "module_relation",
    "boundary_derivation",
)
TAINT_ORDER_INDEX = {taint: index for index, taint in enumerate(TAINT_ORDER)}
ROOT_EDGE_TARGET_KINDS = {
    "type_symbol": {"component", "prop"},
    "props_subtree": {"component", "prop"},
    "export_binding": {
        "module",
        "component",
        "export_binding",
        "import_binding",
        "static_import",
    },
    "component_flow": {"component", "jsx_render", "component_wrap"},
    "module_relation": {"module", "static_import", "literal_dynamic_import"},
    "boundary_derivation": {
        "module",
        "static_import",
        "literal_dynamic_import",
        "client_entry",
        "router_context",
    },
}
ID_RE = re.compile(r"^next:(project|file|module|component|member|relation|fact):[0-9a-f]{64}$")
# A path value is a repository-relative POSIX path.  ``.`` is reserved for a
# project/source root; ordinary file and symbol references use the non-root
# form.  Keep the lexical contract in one helper so every surface rejects the
# same aliases (``a//b``, ``a/./b``, ``a/`` and control characters).
PATH_RE = re.compile(
    r"^(?!/)(?!.*#)(?!.*//)(?!.*(?:^|/)\.{1,2}(?:/|$))(?!.*\/$)(?!.*\\)(?!.*[\x00-\x1f\x7f]).+$"
)
PATH_VALUE_MAX_BYTES = 4096
TARGET_SELECTOR_PREFIX = "path:"
PACKAGE_RE = re.compile(r"^(@[a-z0-9._-]+/)?[a-z0-9._-]+(?:/[a-z0-9._-]+)*$")
TRUSTED_MODULES = ("react", "react/jsx-runtime", "react/jsx-dev-runtime", "next/dynamic")
TRUSTED_REFERENCE_MODULES = (*TRUSTED_MODULES, "typescript/lib")
TRUSTED_GLOBALS = ("Array", "JSX", "ReadonlyArray")
LIMIT_DEFAULTS = {
    "max_files": 20000,
    "max_file_bytes": 4194304,
    "max_decoded_bytes": 67108864,
    "max_encoded_stdin_bytes": 100663296,
    "max_json_nesting": 64,
    "max_json_string_bytes": 8388608,
    "max_array_items": 100000,
    "max_total_array_items": 100000,
    "max_collection_items": 20000,
    "max_model_records": 10000,
    # ``max_stdout_bytes`` is retained as the v1 compatibility alias for the
    # public selected-artifact limit.  New boundaries use the three explicit
    # names below so private adapter response bytes can never be confused with
    # public output bytes.
    "max_stdout_bytes": 16777216,
    "max_adapter_response_bytes": 16777216,
    "max_selected_stdout_bytes": 16777216,
    "max_stderr_bytes": 65536,
    "max_adapter_stderr_capture_bytes": 65536,
    "max_adapter_stdout_capture_bytes": 16777216,
    "timeout_seconds": 60,
    "v8_old_space_mib": 512,
    "max_type_depth": 16,
    "max_type_nodes_per_prop": 512,
    "max_union_members": 64,
    "max_intersection_members": 64,
    "max_nested_properties": 256,
    "max_signatures_per_component": 16,
    "max_flow_visits": 10000,
    "max_alias_edges": 64,
}
DEFAULT_MAX_ENTITIES = 500


class NextRunContext(TypedDict):
    """The one explicit context shared by response and publication projections."""

    requested_formats: list[str]
    budget_requested: int | None
    budget_resolved: int
    budget_source: str
    stdout_selector: str | None


@dataclass(frozen=True)
class NextDecisionContext:
    """Request-independent identity carried by every pre-response failure.

    A failed discovery or process launch cannot manufacture a schema-valid
    adapter request.  This small closed context keeps the run identity,
    resolved limits, and diagnostic routing available without pretending that
    an unavailable request exists.
    """

    run_context: NextRunContext
    request_id: str | None = None
    targets: tuple[str, ...] = ()
    limits: dict[str, Any] | None = None
    stage: str | None = None
    diagnostic_code: str | None = None
    failure_kind: str | None = None
    known_counts: dict[str, int | None] | None = None
    outcome: str = "payload_unavailable"
    payload_unavailable: bool = True
    exit_code: int = 3

    def __post_init__(self) -> None:
        object.__setattr__(self, "run_context", canonical_run_context(**self.run_context))
        object.__setattr__(
            self, "targets", tuple(canonical_target_key(item) for item in self.targets)
        )
        if self.limits is not None:
            object.__setattr__(self, "limits", copy.deepcopy(self.limits))
        if self.known_counts is not None:
            object.__setattr__(self, "known_counts", copy.deepcopy(self.known_counts))
            assert set(self.known_counts) == set(KNOWN_COUNT_KEYS)
            assert all(
                value is None or (isinstance(value, int) and value >= 0)
                for value in self.known_counts.values()
            )
        assert self.outcome in {"payload_unavailable", "not_applicable"}
        assert self.payload_unavailable is (self.outcome == "payload_unavailable")
        assert self.exit_code == (3 if self.outcome == "payload_unavailable" else 0)
        if self.diagnostic_code is not None:
            expected_kind = decision_failure_kind(self.diagnostic_code)
            assert self.failure_kind in {None, expected_kind}
            object.__setattr__(self, "failure_kind", expected_kind)

    def __getattribute__(self, name: str) -> Any:
        value = object.__getattribute__(self, name)
        if name in {"run_context", "targets", "limits", "known_counts"}:
            return copy.deepcopy(value)
        return value


@dataclass(frozen=True)
class NextPublicationContext:
    """Immutable provenance shared by all Next publication projections.

    It is deliberately a data-only object.  A production implementation must
    construct it at the same trust boundary as the run decision and pass this
    object, rather than rebuilding config/source/toolchain facts in a writer.
    """

    source_view_descriptor: dict[str, Any]
    source_view_fingerprint: str
    final_source_acquisition_plan: dict[str, Any]
    source_plan_digest: str
    seal_id: str
    public_next_config: dict[str, Any]
    public_next_request: dict[str, Any] | None
    compatibility_descriptor: dict[str, Any]
    toolchain: dict[str, Any]
    trusted_environment: dict[str, Any]
    run_context: NextRunContext
    run_fingerprint_preimage: dict[str, Any]

    def __post_init__(self) -> None:
        for name in (
            "source_view_descriptor",
            "final_source_acquisition_plan",
            "public_next_config",
            "public_next_request",
            "compatibility_descriptor",
            "toolchain",
            "trusted_environment",
            "run_fingerprint_preimage",
        ):
            object.__setattr__(self, name, copy.deepcopy(getattr(self, name)))
        object.__setattr__(self, "run_context", canonical_run_context(**self.run_context))
        validate_compatibility_descriptor(self.compatibility_descriptor)
        assert re.fullmatch(r"[0-9a-f]{64}", self.source_view_fingerprint)
        assert re.fullmatch(r"[0-9a-f]{64}", self.source_plan_digest)
        assert re.fullmatch(r"[0-9a-f]{64}", self.seal_id)
        assert self.source_view_fingerprint == digest(self.source_view_descriptor)
        assert self.source_plan_digest == digest(self.final_source_acquisition_plan)
        assert self.seal_id == digest(
            {
                "source_plan_digest": self.source_plan_digest,
                "source_view_fingerprint": self.source_view_fingerprint,
                "operation": "decision-boundary-seal-v1",
            }
        )
        preimage = self.run_fingerprint_preimage
        assert preimage["source_view_fingerprint"] == self.source_view_fingerprint
        assert preimage["source_plan_digest"] == self.source_plan_digest
        assert preimage["targets"] == self.public_next_config["targets"]
        assert preimage["formats"] == self.run_context["requested_formats"]
        assert preimage["stdout_selector"] == self.run_context["stdout_selector"]
        assert preimage["limits"] == self.public_next_config["limits"]
        assert preimage["trusted_environment_digest"] == self.trusted_environment["sha256"]
        assert preimage["node_version"] == self.toolchain["node_version"]
        assert preimage["typescript_version"] == self.toolchain["typescript_version"]
        assert preimage["adapter_version"] == self.toolchain["adapter_version"]
        assert preimage["protocol"] == self.toolchain["protocol"]
        if self.public_next_request is not None:
            assert self.public_next_request["run_context"] == self.run_context
            assert self.public_next_config["limits"] == self.public_next_request["limits"]
            assert self.public_next_config["targets"] == self.public_next_request["targets"]
            assert self.public_next_config["source_plan"] == self.final_source_acquisition_plan
            assert self.public_next_config["source_plan_digest"] == self.source_plan_digest

    def __getattribute__(self, name: str) -> Any:
        value = object.__getattribute__(self, name)
        if name in {
            "source_view_descriptor",
            "final_source_acquisition_plan",
            "public_next_config",
            "public_next_request",
            "compatibility_descriptor",
            "toolchain",
            "trusted_environment",
            "run_context",
            "run_fingerprint_preimage",
        }:
            return copy.deepcopy(value)
        return value


@dataclass(frozen=True)
class ValidatedResponseDecision:
    """Immutable trust-boundary decision consumed by every publication surface.

    The response validator is the only constructor.  Downstream projections
    receive this object instead of accepting a second model/context/budget
    supplied by a caller.  The dictionaries are defensive copies at
    construction; ``frozen`` prevents replacing the decision's authoritative
    inputs after validation.
    """

    validated_model: dict[str, Any]
    validated_proof: dict[str, Any]
    run_context: NextRunContext
    pre_budget_outcome: str
    gate: dict[str, Any]
    request: dict[str, Any]
    targets: tuple[str, ...] = ()
    target_failures: tuple[dict[str, Any], ...] = ()
    export_failures: tuple[dict[str, Any], ...] = ()
    publication_context: NextPublicationContext | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "validated_model", copy.deepcopy(self.validated_model))
        object.__setattr__(self, "validated_proof", copy.deepcopy(self.validated_proof))
        object.__setattr__(self, "run_context", canonical_run_context(**self.run_context))
        request = copy.deepcopy(self.request)
        assert isinstance(request, dict)
        assert request.get("schema") == "code-structure-viz.next-adapter-request/v1"
        assert isinstance(request.get("request_id"), str)
        assert request["run_context"] == self.run_context
        object.__setattr__(self, "request", request)
        gate = copy.deepcopy(self.gate)
        if "resolved_limits" in gate:
            assert gate["resolved_limits"] == request["limits"]
        else:
            gate["resolved_limits"] = copy.deepcopy(request["limits"])
        assert gate.get("outcome") in {
            "complete",
            "partial_safe",
            "payload_unavailable",
            "not_applicable",
        }
        assert self.pre_budget_outcome in {
            "complete",
            "partial_safe",
            "payload_unavailable",
            "not_applicable",
        }
        original_outcome = gate.get("original_outcome", self.pre_budget_outcome)
        assert original_outcome in {
            "complete",
            "partial_safe",
            "payload_unavailable",
            "not_applicable",
        }
        allowed_transitions = {
            "complete": {"complete"},
            "partial_safe": {"partial_safe"},
            "payload_unavailable": {"complete", "partial_safe", "payload_unavailable"},
            "not_applicable": {"not_applicable"},
        }
        assert self.pre_budget_outcome in allowed_transitions[original_outcome]
        if gate["outcome"] == "complete":
            assert original_outcome == "complete" and self.pre_budget_outcome == "complete"
        elif gate["outcome"] == "partial_safe":
            assert original_outcome == "partial_safe" and self.pre_budget_outcome == "partial_safe"
        elif gate["outcome"] == "not_applicable":
            assert original_outcome == "not_applicable"
        object.__setattr__(self, "gate", gate)
        normalized_targets = tuple(canonical_target_key(target) for target in self.targets)
        assert list(normalized_targets) == sorted(normalized_targets)
        assert len(normalized_targets) == len(set(normalized_targets))
        assert (
            tuple(canonical_target_key(target) for target in request["targets"])
            == normalized_targets
        )
        object.__setattr__(self, "targets", normalized_targets)
        target_failures = tuple(copy.deepcopy(self.target_failures))
        assert target_failures == tuple(sorted(target_failures, key=canonical_json_bytes))
        assert len({item.get("target_key") for item in target_failures}) == len(target_failures)
        for failure in target_failures:
            assert set(failure) == {"target_key", "reason"}
            assert canonical_target_key(failure["target_key"]) in normalized_targets
            assert failure["reason"] in TARGET_FAILURE_REASONS
        if target_failures:
            assert gate["outcome"] == "payload_unavailable"
            assert gate.get("diagnostic_code") == "CSV-NEXT-TARGET-001"
        export_failures = tuple(copy.deepcopy(self.export_failures))
        assert export_failures == tuple(sorted(export_failures, key=canonical_json_bytes))
        assert len({item.get("syntax_identity") for item in export_failures}) == len(
            export_failures
        )
        if export_failures:
            assert gate["outcome"] == "payload_unavailable"
            assert gate.get("diagnostic_code") == "CSV-NEXT-EXPORT-001"
        object.__setattr__(self, "target_failures", target_failures)
        object.__setattr__(self, "export_failures", export_failures)
        context = self.publication_context or _publication_context_from_request(
            request, self.run_context
        )
        assert context.run_context == self.run_context
        assert context.public_next_request == request
        object.__setattr__(self, "publication_context", context)

    def __getattribute__(self, name: str) -> Any:
        """Return defensive snapshots so nested containers cannot be mutated."""

        value = object.__getattribute__(self, name)
        if name in {
            "validated_model",
            "validated_proof",
            "run_context",
            "gate",
            "targets",
            "target_failures",
            "export_failures",
            "request",
            "publication_context",
        }:
            return copy.deepcopy(value)
        return value


# Compatibility alias for the Round 13 name.  New code should type against
# ``ValidatedResponseDecision`` or the closed ``NextRunDecision`` union.
NextValidatedDecision = ValidatedResponseDecision


DECISION_FAILURE_STAGES = frozenset(
    {
        "config_validation",
        "project_validation",
        "source_selection",
        "source_read",
        "source_integrity",
        "target_resolution",
        "trust_validation",
        "stdin_encode",
        "adapter_heap",
        "node_discovery",
        "node_spawn",
        "node_timeout",
        "node_process",
        "adapter_stderr_capture",
        "adapter_stdout_capture",
        "response_raw_bytes",
        "response_decode",
        "response_protocol",
        "response_schema",
        "response_validation",
        "model_validation",
        "public_stderr_capture",
    }
)
DECISION_FAILURE_CODES = frozenset(
    {
        "CSV-NEXT-LIMIT-001",
        "CSV-NEXT-LIMIT-002",
        "CSV-NEXT-LIMIT-003",
        "CSV-NEXT-LIMIT-004",
        "CSV-NEXT-LIMIT-005",
        "CSV-NEXT-CONFIG-001",
        "CSV-NEXT-CONFIG-002",
        "CSV-NEXT-NODE-001",
        "CSV-NEXT-NODE-002",
        "CSV-NEXT-NODE-003",
        "CSV-NEXT-NODE-004",
        "CSV-NEXT-PROTOCOL-001",
        "CSV-NEXT-PROJECT-001",
        "CSV-NEXT-PROJECT-002",
        "CSV-NEXT-SOURCE-002",
        "CSV-NEXT-SOURCE-003",
        "CSV-NEXT-TARGET-001",
        "CSV-NEXT-TRUST-001",
        "CSV-NEXT-TRUST-002",
        "CSV-NEXT-TRUST-003",
    }
)
DECISION_FAILURE_KIND_BY_CODE = {
    "CSV-NEXT-CONFIG-001": "config",
    "CSV-NEXT-CONFIG-002": "config",
    "CSV-NEXT-PROJECT-001": "project",
    "CSV-NEXT-PROJECT-002": "project",
    "CSV-NEXT-SOURCE-001": "source",
    "CSV-NEXT-SOURCE-002": "source",
    "CSV-NEXT-SOURCE-003": "source",
    "CSV-NEXT-TARGET-001": "target",
    "CSV-NEXT-TRUST-001": "trust",
    "CSV-NEXT-TRUST-002": "trust",
    "CSV-NEXT-TRUST-003": "trust",
    "CSV-NEXT-NODE-001": "node",
    "CSV-NEXT-NODE-002": "node",
    "CSV-NEXT-NODE-003": "node",
    "CSV-NEXT-NODE-004": "node",
    "CSV-NEXT-LIMIT-001": "limit",
    "CSV-NEXT-LIMIT-002": "limit",
    "CSV-NEXT-LIMIT-003": "limit",
    "CSV-NEXT-LIMIT-004": "limit",
    "CSV-NEXT-LIMIT-005": "limit",
    "CSV-NEXT-PROTOCOL-001": "protocol",
    "CSV-NEXT-EXPORT-001": "export",
    "CSV-NEXT-IDENTITY-001": "identity",
}


def decision_failure_kind(diagnostic_code: str) -> str:
    """Return the closed pre-response failure category for one code."""

    if diagnostic_code == "CSV-NEXT-APPLICABILITY-001":
        return "applicability"
    assert diagnostic_code in DECISION_FAILURE_CODES
    return DECISION_FAILURE_KIND_BY_CODE.get(diagnostic_code, "protocol")


KNOWN_COUNT_KEYS = ("files", "source_bytes", "model_records", "stdout_bytes")


@dataclass(frozen=True)
class PreResponseFailureDecision:
    """The sole authority when no schema-valid adapter response exists."""

    request: dict[str, Any] | None
    run_context: NextRunContext
    stage: str
    diagnostic_code: str
    diagnostic: dict[str, Any]
    known_counts: dict[str, int | None]
    outcome: str = "payload_unavailable"
    payload_available: bool = False
    artifact_paths: tuple[str, ...] = ()
    exit_code: int = 3
    decision_context: NextDecisionContext | None = None
    publication_context: NextPublicationContext | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "request", copy.deepcopy(self.request))
        object.__setattr__(self, "run_context", canonical_run_context(**self.run_context))
        assert self.stage in DECISION_FAILURE_STAGES
        assert self.diagnostic_code in DECISION_FAILURE_CODES
        assert set(self.known_counts) == set(KNOWN_COUNT_KEYS)
        assert all(
            value is None or (isinstance(value, int) and value >= 0)
            for value in self.known_counts.values()
        )
        assert self.outcome == "payload_unavailable"
        assert self.payload_available is False
        assert self.artifact_paths == ()
        assert self.exit_code == 3
        assert self.diagnostic["code"] == self.diagnostic_code
        catalog_entry = _diagnostic_catalog()[self.diagnostic_code]
        permission = catalog_entry["ref_permission"]
        path = self.diagnostic["path"]
        symbol = self.diagnostic["symbol"]
        if permission == "none":
            assert path is None and symbol is None
        elif permission == "path":
            assert path is not None and symbol is None
            _assert_file_path(path)
        elif permission == "symbol":
            assert path is None and symbol is not None
            _id_kind(symbol)
        else:
            assert permission == "path_or_symbol"
            assert (path is None) != (symbol is None)
            if path is not None:
                _assert_file_path(path)
            if symbol is not None:
                _id_kind(symbol)
        known_counts = copy.deepcopy(self.known_counts)
        decision_context = self.decision_context or NextDecisionContext(
            run_context=self.run_context,
            request_id=(self.request or {}).get("request_id"),
            targets=tuple((self.request or {}).get("targets", ())),
            limits=copy.deepcopy((self.request or {}).get("limits")),
            stage=self.stage,
            diagnostic_code=self.diagnostic_code,
            known_counts=known_counts,
        )
        if decision_context.known_counts is None or (
            self.request is not None and decision_context.limits is None
        ):
            decision_context = NextDecisionContext(
                run_context=decision_context.run_context,
                request_id=decision_context.request_id
                if decision_context.request_id is not None
                else (self.request or {}).get("request_id"),
                targets=decision_context.targets or tuple((self.request or {}).get("targets", ())),
                limits=decision_context.limits
                if decision_context.limits is not None
                else copy.deepcopy((self.request or {}).get("limits")),
                stage=decision_context.stage,
                diagnostic_code=decision_context.diagnostic_code,
                failure_kind=decision_context.failure_kind,
                known_counts=known_counts,
                outcome=decision_context.outcome,
                payload_unavailable=decision_context.payload_unavailable,
                exit_code=decision_context.exit_code,
            )
        assert decision_context.run_context == self.run_context
        assert decision_context.stage == self.stage
        assert decision_context.diagnostic_code == self.diagnostic_code
        assert decision_context.failure_kind == decision_failure_kind(self.diagnostic_code)
        assert decision_context.outcome == self.outcome
        assert decision_context.payload_unavailable is True
        assert decision_context.exit_code == self.exit_code
        assert (
            decision_context.known_counts is None or decision_context.known_counts == known_counts
        )
        if self.request is not None:
            assert self.request["run_context"] == self.run_context
            assert decision_context.request_id == self.request.get("request_id")
            assert tuple(decision_context.targets) == tuple(self.request.get("targets", ()))
            if decision_context.limits is not None:
                assert decision_context.limits == self.request.get("limits")
        object.__setattr__(self, "decision_context", decision_context)
        context = self.publication_context or _publication_context_from_request(
            self.request, self.run_context, decision_context=decision_context
        )
        assert context.run_context == self.run_context
        object.__setattr__(self, "publication_context", context)

    def __getattribute__(self, name: str) -> Any:
        value = object.__getattribute__(self, name)
        if name in {
            "request",
            "run_context",
            "diagnostic",
            "known_counts",
            "artifact_paths",
            "decision_context",
            "publication_context",
        }:
            return copy.deepcopy(value)
        return value


@dataclass(frozen=True)
class NotApplicableDecision:
    """Closed no-Next applicability outcome with the same downstream shape."""

    request: dict[str, Any]
    run_context: NextRunContext
    diagnostic: dict[str, Any]
    known_counts: dict[str, int | None]
    outcome: str = "not_applicable"
    payload_available: bool = False
    artifact_paths: tuple[str, ...] = ()
    exit_code: int = 0
    decision_context: NextDecisionContext | None = None
    publication_context: NextPublicationContext | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "request", copy.deepcopy(self.request))
        object.__setattr__(self, "run_context", canonical_run_context(**self.run_context))
        assert self.diagnostic["code"] == "CSV-NEXT-APPLICABILITY-001"
        assert set(self.known_counts) == set(KNOWN_COUNT_KEYS)
        assert all(
            value is None or (isinstance(value, int) and value >= 0)
            for value in self.known_counts.values()
        )
        assert self.outcome == "not_applicable"
        assert self.payload_available is False
        assert self.artifact_paths == ()
        assert self.exit_code == 0
        assert self.request["run_context"] == self.run_context
        decision_context = self.decision_context or NextDecisionContext(
            run_context=self.run_context,
            request_id=self.request.get("request_id"),
            targets=tuple(self.request.get("targets", ())),
            limits=copy.deepcopy(self.request.get("limits")),
            diagnostic_code="CSV-NEXT-APPLICABILITY-001",
            outcome="not_applicable",
            payload_unavailable=False,
            exit_code=0,
            known_counts=copy.deepcopy(self.known_counts),
        )
        if decision_context.known_counts is None:
            decision_context = NextDecisionContext(
                run_context=decision_context.run_context,
                request_id=decision_context.request_id,
                targets=decision_context.targets,
                limits=decision_context.limits,
                stage=decision_context.stage,
                diagnostic_code=decision_context.diagnostic_code,
                failure_kind=decision_context.failure_kind,
                known_counts=copy.deepcopy(self.known_counts),
                outcome=decision_context.outcome,
                payload_unavailable=decision_context.payload_unavailable,
                exit_code=decision_context.exit_code,
            )
        assert decision_context.outcome == self.outcome
        assert decision_context.payload_unavailable is False
        assert decision_context.exit_code == self.exit_code
        assert (
            decision_context.known_counts is None
            or decision_context.known_counts == self.known_counts
        )
        object.__setattr__(self, "decision_context", decision_context)
        context = self.publication_context or _publication_context_from_request(
            self.request, self.run_context, decision_context=decision_context
        )
        assert context.run_context == self.run_context
        object.__setattr__(self, "publication_context", context)

    def __getattribute__(self, name: str) -> Any:
        value = object.__getattribute__(self, name)
        if name in {
            "request",
            "run_context",
            "diagnostic",
            "known_counts",
            "artifact_paths",
            "decision_context",
            "publication_context",
        }:
            return copy.deepcopy(value)
        return value


NextRunDecision = ValidatedResponseDecision | PreResponseFailureDecision | NotApplicableDecision


def is_next_run_decision(value: object) -> bool:
    """Return whether a value is one of the three closed run decisions."""

    return isinstance(
        value, (ValidatedResponseDecision, PreResponseFailureDecision, NotApplicableDecision)
    )


# Every limit has an explicit measurement contract.  The production adapter
# must use the same unit, measurement point, inclusive boundary, and stable
# outcome; these records are intentionally data-only and cheap to exercise.
LIMIT_CONTRACTS: dict[str, dict[str, Any]] = {
    "max_entities": {
        "unit": "published_internal_modules_and_components",
        "measurement": "after_target_projection_before_publication",
        "encoding": "not_applicable",
        "inclusive": True,
        "outcome": "payload_unavailable",
    },
    "max_files": {
        "unit": "files",
        "measurement": "after_safe_source_selection_before_read",
        "encoding": "not_applicable",
        "inclusive": True,
        "outcome": "payload_unavailable",
    },
    "max_file_bytes": {
        "unit": "utf8_bytes_per_file",
        "measurement": "after_read_before_base64",
        "encoding": "utf8",
        "inclusive": True,
        "outcome": "payload_unavailable",
    },
    "max_decoded_bytes": {
        "unit": "utf8_bytes_per_request",
        "measurement": "sum_after_decode_before_adapter_spawn",
        "encoding": "utf8",
        "inclusive": True,
        "outcome": "payload_unavailable",
    },
    "max_encoded_stdin_bytes": {
        "unit": "utf8_bytes_per_stdin_payload",
        "measurement": "canonical_json_encode_before_adapter_spawn",
        "encoding": "utf8",
        "inclusive": True,
        "outcome": "payload_unavailable",
    },
    "max_json_nesting": {
        "unit": "json_nesting_levels",
        "measurement": "parser_depth_before_child_descent",
        "encoding": "utf8",
        "inclusive": True,
        "outcome": "payload_unavailable",
    },
    "max_json_string_bytes": {
        "unit": "utf8_bytes_per_json_string",
        "measurement": "parser_decode_before_materialization",
        "encoding": "utf8",
        "inclusive": True,
        "outcome": "payload_unavailable",
    },
    "max_array_items": {
        "unit": "items_per_json_array",
        "measurement": "parser_item_count_before_append",
        "encoding": "not_applicable",
        "inclusive": True,
        "outcome": "payload_unavailable",
    },
    "max_total_array_items": {
        "unit": "items_across_json_arrays_per_response",
        "measurement": "streaming_counter_before_array_item_materialization",
        "encoding": "not_applicable",
        "inclusive": True,
        "outcome": "payload_unavailable",
    },
    "max_collection_items": {
        "unit": "records_per_model_collection",
        "measurement": "adapter_record_emission_before_append",
        "encoding": "not_applicable",
        "inclusive": True,
        "outcome": "payload_unavailable",
    },
    "max_model_records": {
        "unit": "records_per_model",
        "measurement": "adapter_model_assembly_before_publication",
        "encoding": "not_applicable",
        "inclusive": True,
        "outcome": "payload_unavailable",
    },
    "max_stdout_bytes": {
        "unit": "utf8_bytes_per_stdout_payload",
        "measurement": "compatibility_alias_for_max_selected_stdout_bytes",
        "encoding": "utf8",
        "inclusive": True,
        "outcome": "payload_unavailable",
    },
    "max_adapter_response_bytes": {
        "unit": "utf8_bytes_per_adapter_response_payload",
        "measurement": "complete_child_capture_before_decode",
        "encoding": "utf8",
        "inclusive": True,
        "outcome": "payload_unavailable",
    },
    "max_selected_stdout_bytes": {
        "unit": "utf8_bytes_per_selected_artifact_payload",
        "measurement": "canonical_output_encode_before_write",
        "encoding": "utf8",
        "inclusive": True,
        "outcome": "payload_unavailable",
    },
    "max_stderr_bytes": {
        "unit": "utf8_bytes_per_stderr_payload",
        "measurement": "diagnostic_encode_before_write",
        "encoding": "utf8",
        "inclusive": True,
        "outcome": "payload_unavailable",
    },
    "max_adapter_stderr_capture_bytes": {
        "unit": "utf8_bytes_per_adapter_stderr_capture",
        "measurement": "incremental_process_group_capture_before_append",
        "encoding": "utf8",
        "inclusive": True,
        "outcome": "payload_unavailable",
    },
    "max_adapter_stdout_capture_bytes": {
        "unit": "utf8_bytes_per_adapter_stdout_capture",
        "measurement": "incremental_process_group_capture_before_append",
        "encoding": "utf8",
        "inclusive": True,
        "outcome": "payload_unavailable",
    },
    "timeout_seconds": {
        "unit": "wall_clock_seconds_per_adapter_run",
        "measurement": "monotonic_deadline_at_process_wait",
        "encoding": "not_applicable",
        "inclusive": True,
        "outcome": "payload_unavailable",
    },
    "v8_old_space_mib": {
        "unit": "binary_mib_heap_limit",
        "measurement": "adapter_process_start_flag",
        "encoding": "not_applicable",
        "inclusive": True,
        "outcome": "payload_unavailable",
    },
    "max_type_depth": {
        "unit": "type_ir_levels_per_prop",
        "measurement": "validator_before_child_descent",
        "encoding": "not_applicable",
        "inclusive": True,
        "outcome": "partial_safe",
    },
    "max_type_nodes_per_prop": {
        "unit": "type_ir_nodes_per_prop",
        "measurement": "validator_before_node_visit",
        "encoding": "not_applicable",
        "inclusive": True,
        "outcome": "partial_safe",
    },
    "max_union_members": {
        "unit": "members_per_union",
        "measurement": "validator_before_union_member_visit",
        "encoding": "not_applicable",
        "inclusive": True,
        "outcome": "partial_safe",
    },
    "max_intersection_members": {
        "unit": "members_per_intersection",
        "measurement": "validator_before_intersection_member_visit",
        "encoding": "not_applicable",
        "inclusive": True,
        "outcome": "partial_safe",
    },
    "max_nested_properties": {
        "unit": "properties_per_prop_tree",
        "measurement": "validator_before_property_visit",
        "encoding": "not_applicable",
        "inclusive": True,
        "outcome": "partial_safe",
    },
    "max_signatures_per_component": {
        "unit": "signatures_per_component",
        "measurement": "validator_before_signature_visit",
        "encoding": "not_applicable",
        "inclusive": True,
        "outcome": "partial_safe",
    },
    "max_flow_visits": {
        "unit": "flow_visits_per_component",
        "measurement": "flow_traversal_before_node_visit",
        "encoding": "not_applicable",
        "inclusive": True,
        "outcome": "partial_safe",
    },
    "max_alias_edges": {
        "unit": "alias_edges_per_module",
        "measurement": "alias_graph_before_edge_append",
        "encoding": "not_applicable",
        "inclusive": True,
        "outcome": "partial_safe",
    },
}

IDENTITY_VERSIONS = {
    "project": 1,
    "file": 1,
    "module": 1,
    "component": 1,
    "member": 1,
    "relation": 1,
    "fact": 1,
    "props_ir": 1,
}
RECORD_ID_PREFIX = {
    "project": "project",
    "file": "file",
    "module": "module",
    "component": "component",
    "export_binding": "member",
    "import_binding": "member",
    "prop": "member",
    "static_import": "relation",
    "literal_dynamic_import": "relation",
    "jsx_render": "relation",
    "component_wrap": "relation",
    "client_entry": "fact",
    "router_context": "fact",
}

# The v1 trusted profile is deliberately small and closed.  The declaration
# bytes live in checked-in data-only fixtures.  Keeping the physical-to-virtual
# mapping here makes the attestation independently reproducible before the
# production adapter exists.
REPO_ROOT = Path(__file__).resolve().parents[2]
TRUSTED_PROFILE_PHYSICAL_TO_VIRTUAL = (
    (
        "tests/fixtures/next_trusted_profile/jsx-runtime.d.ts",
        "/.code-structure-viz/trusted/v1/jsx-runtime.d.ts",
    ),
    (
        "tests/fixtures/next_trusted_profile/lib.d.ts",
        "/.code-structure-viz/trusted/v1/lib.d.ts",
    ),
    (
        "tests/fixtures/next_trusted_profile/next-dynamic.d.ts",
        "/.code-structure-viz/trusted/v1/next-dynamic.d.ts",
    ),
    (
        "tests/fixtures/next_trusted_profile/react.d.ts",
        "/.code-structure-viz/trusted/v1/react.d.ts",
    ),
)
TRUSTED_PROFILE_LICENSE_INPUTS = (
    "npm:typescript@5.9.2:Apache-2.0",
    "resource:code-structure-viz-next-trusted-types@1:MIT",
)
TRUSTED_PROFILE_LICENSES: tuple[dict[str, str], ...] = (
    {
        "ecosystem": "npm",
        "name": "typescript",
        "version": "5.9.2",
        "license_id": "Apache-2.0",
        "source_url": "https://www.npmjs.com/package/typescript",
        "content_or_lock_digest": hashlib.sha256(
            TRUSTED_PROFILE_LICENSE_INPUTS[0].encode("utf-8")
        ).hexdigest(),
    },
    {
        "ecosystem": "resource",
        "name": "code-structure-viz-next-trusted-types",
        "version": "1",
        "license_id": "MIT",
        "source_url": "https://github.com/chemitaro/code-structure-viz",
        "content_or_lock_digest": hashlib.sha256(
            TRUSTED_PROFILE_LICENSE_INPUTS[1].encode("utf-8")
        ).hexdigest(),
    },
)
TRUSTED_PROFILE_FILES = (
    "/.code-structure-viz/trusted/v1/jsx-runtime.d.ts",
    "/.code-structure-viz/trusted/v1/lib.d.ts",
    "/.code-structure-viz/trusted/v1/next-dynamic.d.ts",
    "/.code-structure-viz/trusted/v1/react.d.ts",
)
TRUSTED_PROFILE_FILE_LICENSES = {
    TRUSTED_PROFILE_FILES[0]: "MIT",
    TRUSTED_PROFILE_FILES[1]: "Apache-2.0",
    TRUSTED_PROFILE_FILES[2]: "MIT",
    TRUSTED_PROFILE_FILES[3]: "MIT",
}
TRUSTED_PROFILE_FILE_SHA256 = {
    virtual_path: hashlib.sha256((REPO_ROOT / physical_path).read_bytes()).hexdigest()
    for physical_path, virtual_path in TRUSTED_PROFILE_PHYSICAL_TO_VIRTUAL
}
TRUSTED_PROFILE_FILE_SIZES = {
    virtual_path: (REPO_ROOT / physical_path).stat().st_size
    for physical_path, virtual_path in TRUSTED_PROFILE_PHYSICAL_TO_VIRTUAL
}
TRUSTED_PROFILE_INVENTORY_PATH = (
    REPO_ROOT / "tests/fixtures/next_trusted_profile/expected_inventory.json"
)
TRUSTED_PROFILE_EXPECTED_INVENTORY: tuple[dict[str, Any], ...] = tuple(
    cast(
        list[dict[str, Any]], json.loads(TRUSTED_PROFILE_INVENTORY_PATH.read_text(encoding="utf-8"))
    )
)
TRUSTED_PROFILE_SHADOWING_WITNESS = tuple(
    [
        {
            "source_kind": "module",
            "source_name": module,
            "decision": "reserved",
        }
        for module in TRUSTED_MODULES
    ]
    + [
        {
            "source_kind": "global",
            "source_name": global_name,
            "decision": "reserved",
        }
        for global_name in TRUSTED_GLOBALS
    ]
)


def _trusted_inventory_symbol_key(row: dict[str, Any]) -> tuple[str, str, tuple[str, ...]]:
    return (row["source_kind"], row["source_name"], tuple(row["export_path"]))


TRUSTED_PROFILE_MODULE_SYMBOLS = tuple(
    (_trusted_inventory_symbol_key(row)[1], _trusted_inventory_symbol_key(row)[2])
    for row in TRUSTED_PROFILE_EXPECTED_INVENTORY
    if row["source_kind"] == "module"
)
TRUSTED_PROFILE_GLOBAL_SYMBOLS = tuple(
    (_trusted_inventory_symbol_key(row)[1], _trusted_inventory_symbol_key(row)[2])
    for row in TRUSTED_PROFILE_EXPECTED_INVENTORY
    if row["source_kind"] == "global"
)
_TRUSTED_PROFILE_VIRTUAL_BY_BASENAME = {
    Path(virtual_path).name: virtual_path for virtual_path in TRUSTED_PROFILE_FILES
}
TRUSTED_PROFILE_CERTIFIED_SYMBOLS: tuple[dict[str, Any], ...] = tuple(
    {
        "source_kind": row["source_kind"],
        "source_name": row["source_name"],
        "export_path": row["export_path"],
        "declaration_sha256": TRUSTED_PROFILE_FILE_SHA256[
            _TRUSTED_PROFILE_VIRTUAL_BY_BASENAME[row["declaration_file"]]
        ],
        "symbol_kind": row["symbol_kind"],
        "signature_digest": row["signature_digest"],
    }
    for row in sorted(TRUSTED_PROFILE_EXPECTED_INVENTORY, key=_trusted_inventory_symbol_key)
)
TRUSTED_PROFILE_CERTIFIED_MODULE_KEYS = {
    (row["source_name"], tuple(row["export_path"]))
    for row in TRUSTED_PROFILE_EXPECTED_INVENTORY
    if row["source_kind"] == "module"
}
RUNTIME_REQUIRED_MEMBER_ROLES = {
    "adapter",
    "manifest",
    "trusted_declaration",
    "typescript_lib",
}
RUNTIME_REQUIRED_PATHS = {
    "src/code_structure_viz/_next_runtime/adapter.js": "adapter",
    "src/code_structure_viz/_next_runtime/manifest.json": "manifest",
    "src/code_structure_viz/_next_runtime/trusted.d.ts": "trusted_declaration",
    "src/code_structure_viz/_next_runtime/typescript-lib.d.ts": "typescript_lib",
}
RUNTIME_PHYSICAL_TO_VIRTUAL = (
    ("tests/fixtures/next_runtime/adapter.js", "src/code_structure_viz/_next_runtime/adapter.js"),
    (
        "tests/fixtures/next_runtime/manifest.json",
        "src/code_structure_viz/_next_runtime/manifest.json",
    ),
    (
        "tests/fixtures/next_runtime/trusted.d.ts",
        "src/code_structure_viz/_next_runtime/trusted.d.ts",
    ),
    (
        "tests/fixtures/next_runtime/typescript-lib.d.ts",
        "src/code_structure_viz/_next_runtime/typescript-lib.d.ts",
    ),
)
SOURCE_PLAN_PROGRAM_SUFFIXES = (".js", ".jsx", ".ts", ".tsx")
SOURCE_PLAN_CONTEXT_SUFFIXES = (".d.ts",)
SOURCE_PLAN_HARD_EXCLUSIONS = (".git", "node_modules", ".next", "out", "dist", "build", "coverage")
SOURCE_PLAN_CONTROL_PATHS = ("package.json", "tsconfig.json", "jsconfig.json")
SOURCE_PLAN_VERSION = "1"
# ECMAScript IdentifierName uses a checked-in Unicode 15.0.0 table rather
# than the host Python Unicode database.  The table digest is included in
# the trusted profile, compatibility descriptor, and run fingerprint so a
# table replacement is an explicit compatibility change.
ECMASCRIPT_OTHER_ID_START = frozenset(
    chr(codepoint) for codepoint in ECMASCRIPT_OTHER_ID_START_CODEPOINTS
)
ECMASCRIPT_OTHER_ID_CONTINUE = frozenset(
    chr(codepoint) for codepoint in ECMASCRIPT_OTHER_ID_CONTINUE_CODEPOINTS
)
SOURCE_PLAN_FILE_ROLE_MAP: tuple[dict[str, Any], ...] = (
    {
        "project_root": ".",
        "path": "jsconfig.json",
        "roles": ["control"],
        "effective_role": "control",
    },
    {
        "project_root": ".",
        "path": "package.json",
        "roles": ["control"],
        "effective_role": "control",
    },
    {
        "project_root": ".",
        "path": "src/Button.tsx",
        "roles": ["program"],
        "effective_role": "program",
    },
    {
        "project_root": ".",
        "path": "src/Card.tsx",
        "roles": ["program"],
        "effective_role": "program",
    },
    {
        "project_root": ".",
        "path": "src/types.d.ts",
        "roles": ["context"],
        "effective_role": "context",
    },
    {
        "project_root": ".",
        "path": "tsconfig.json",
        "roles": ["control"],
        "effective_role": "control",
    },
)
PUBLIC_TARGET_RE = re.compile(r"^path:([^#]+)$")
EXPORT_CENSUS_PATH = REPO_ROOT / "tests/fixtures/next_export_census.json"
EXPORT_CENSUS_SCHEMA = "code-structure-viz.next-export-census/v1"
EXPORT_GRAPH_PATH = REPO_ROOT / "tests/fixtures/next_export_graph.json"
EXPORT_GRAPH_SCHEMA = "code-structure-viz.next-export-graph/v1"
EXPORT_GRAPH_RAW_PATH = REPO_ROOT / "tests/fixtures/next_export_graph_raw.json"
EXPORT_GRAPH_RAW_SCHEMA = "code-structure-viz.next-export-graph-raw/v1"
EXPORT_GRAPH_CASES_PATH = REPO_ROOT / "tests/fixtures/next_export_graph_cases.json"
EXPORT_GRAPH_CASES_SCHEMA = "code-structure-viz.next-export-graph-cases/v1"


class InstrumentedSourceReader:
    """Small reference reader that makes accidental post-seal reads visible."""

    def __init__(self, files: dict[str, bytes]) -> None:
        self._files = dict(files)
        self.read_counts: dict[str, int] = {}
        self.sealed = False
        self.seal_calls = 0

    def read(self, path: str) -> bytes:
        assert not self.sealed, "SourceView is sealed; filesystem reads are forbidden"
        assert path in self._files, path
        self.read_counts[path] = self.read_counts.get(path, 0) + 1
        assert self.read_counts[path] == 1, path
        return self._files[path]

    def seal(self) -> int:
        assert not self.sealed
        self.sealed = True
        self.seal_calls += 1
        return self.seal_calls


@dataclass(frozen=True)
class SourceAcquisitionSeal:
    """Atomic final-plan/source-view pair produced by the two-phase reader."""

    final_plan: dict[str, Any]
    source_view: dict[str, Any]
    plan_digest: str
    source_view_fingerprint: str
    seal_id: str
    seal_operation: int


@dataclass(frozen=True)
class SourceDiscoveryIntent:
    """Sealed description of what the two-phase source read intends to do."""

    discovery_paths: tuple[str, ...]
    final_paths: tuple[str, ...]
    config: dict[str, Any] | None = None
    local_extends: tuple[dict[str, Any], ...] = ()
    file_role_map: tuple[dict[str, Any], ...] = ()


def seal_source_acquisition(
    intent: SourceDiscoveryIntent | dict[str, Any],
    reader: InstrumentedSourceReader,
    inventory: dict[str, Any] | None = None,
) -> SourceAcquisitionSeal:
    """Derive and atomically seal the final plan and SourceView.

    ``intent`` contains only discovery intent.  The final plan is derived from
    its frozen config and the acquired bytes; callers cannot submit an
    independent plan or view.  ``inventory`` is an optional read-only witness
    used to prove the final revision, role map, extends closure, and
    digest/size values match what was actually read.
    """

    if isinstance(intent, SourceDiscoveryIntent):
        discovery_paths = tuple(intent.discovery_paths)
        final_paths = tuple(intent.final_paths)
        config = copy.deepcopy(intent.config)
        local_extends = list(copy.deepcopy(intent.local_extends))
        file_role_map = list(copy.deepcopy(intent.file_role_map))
    else:
        discovery_paths = tuple(intent.get("discovery_paths", intent.get("control_paths", ())))
        final_paths = tuple(intent.get("final_paths", intent.get("source_paths", ())))
        config = copy.deepcopy(cast(dict[str, Any] | None, intent.get("config")))
        local_extends = list(copy.deepcopy(intent.get("local_extends", ())))
        file_role_map = list(copy.deepcopy(intent.get("file_role_map", ())))
    inventory = copy.deepcopy(inventory or {})
    # Duplicate entries within either phase would make the read contract
    # ambiguous.  Cross-phase overlap is intentional and is read once by the
    # union below.
    assert len(discovery_paths) == len(set(discovery_paths))
    assert len(final_paths) == len(set(final_paths))
    discovery_paths = tuple(dict.fromkeys(discovery_paths))
    final_paths = tuple(dict.fromkeys(final_paths))
    assert discovery_paths == tuple(str(path) for path in discovery_paths)
    assert final_paths == tuple(str(path) for path in final_paths)
    all_paths = tuple(dict.fromkeys((*discovery_paths, *final_paths)))
    assert all_paths
    contents = {path: reader.read(path) for path in all_paths}
    before = inventory.get("revision_before", inventory.get("revision", "inventory-v1"))
    after = inventory.get("revision_after", before)
    assert after == before

    assert config is not None, "source intent must provide derivable config"
    plan = source_plan_descriptor(
        config,
        local_extends=local_extends or None,
        file_role_map=file_role_map or None,
    )

    view_files = [
        {
            "path": path,
            "size_bytes": len(contents[path]),
            "sha256": hashlib.sha256(contents[path]).hexdigest(),
        }
        for path in sorted(contents)
    ]
    source_view = {
        "schema": "code-structure-viz.source-view/v1",
        "files": view_files,
        "file_count": len(view_files),
    }
    expected_files = inventory.get("file_digests")
    if expected_files is not None:
        assert expected_files == view_files
    expected_roles = inventory.get("file_role_map")
    if expected_roles is not None:
        assert plan["file_role_map"] == sorted(expected_roles, key=canonical_json_bytes)
    expected_extends = inventory.get("local_extends")
    if expected_extends is not None:
        assert plan["local_extends"] == sorted(expected_extends, key=canonical_json_bytes)
    plan_digest = digest(plan)
    source_view_fingerprint = digest(source_view)
    if inventory.get("plan_digest") is not None:
        assert inventory["plan_digest"] == plan_digest
    if inventory.get("source_view_fingerprint") is not None:
        assert inventory["source_view_fingerprint"] == source_view_fingerprint
    seal_operation = reader.seal()
    seal_id = digest(
        {
            "plan_digest": plan_digest,
            "source_view_fingerprint": source_view_fingerprint,
            "seal_operation": seal_operation,
        }
    )
    return SourceAcquisitionSeal(
        final_plan=plan,
        source_view=source_view,
        plan_digest=plan_digest,
        source_view_fingerprint=source_view_fingerprint,
        seal_id=seal_id,
        seal_operation=seal_operation,
    )


_IDENTIFIER_RE = r"[A-Za-z_$][A-Za-z0-9_$]*"
_EXPORT_KEYWORDS = {
    "as",
    "async",
    "class",
    "const",
    "default",
    "export",
    "from",
    "function",
    "interface",
    "let",
    "type",
    "var",
}


def _jsx_tag_end(text: str, start: int) -> tuple[int, str | None, bool, bool] | None:
    """Parse one JSX tag while ignoring ``>`` inside attributes.

    The scanner does not attempt to parse JavaScript expressions.  It only
    needs a lexical boundary for a tag, so quoted attributes and balanced
    ``{...}`` expressions are consumed as opaque regions.  The returned tuple
    is ``(end, name, closing, self_closing)``; ``name`` is ``None`` for a
    fragment tag.
    """

    if not text.startswith("<", start):
        return None
    if text.startswith("</>", start):
        return start + 3, None, True, False
    if text.startswith("<>", start):
        return start + 2, None, False, False

    closing = text.startswith("</", start)
    cursor = start + (2 if closing else 1)
    name_result = _jsx_tag_name(text, cursor)
    if name_result is None:
        return None
    name, cursor = name_result
    last_significant = ""
    while cursor < len(text):
        character = text[cursor]
        if character in "'\"`":
            cursor = _jsx_quoted_end(text, cursor)
            continue
        if character == "{":
            expression_end = _jsx_expression_end(text, cursor)
            if expression_end is None:
                return None
            cursor = expression_end
            continue
        if character == ">":
            self_closing = last_significant == "/" and not closing
            return cursor + 1, name, closing, self_closing
        if not character.isspace():
            last_significant = character
        cursor += 1
    return None


def _jsx_tag_name(text: str, start: int) -> tuple[str, int] | None:
    """Read a JSX IdentifierName with member/namespace segments.

    JSX permits Unicode IdentifierName characters and the punctuation ``.``
    and ``:`` for member/namespace names.  Hyphens are retained for intrinsic
    HTML names.  Keeping this lexer independent from the export identifier
    regex prevents Unicode tag text from being mistaken for module-level
    ``export`` declarations.
    """

    cursor = start
    segments: list[str] = []
    while True:
        if cursor >= len(text):
            return None
        first = text[cursor]
        if not _is_jsx_identifier_start(first):
            return None
        segment_start = cursor
        cursor += 1
        while cursor < len(text):
            character = text[cursor]
            if _is_jsx_identifier_part(character) or character == "-":
                cursor += 1
                continue
            break
        segments.append(text[segment_start:cursor])
        if cursor >= len(text) or text[cursor] not in ".:":
            break
        cursor += 1
    name = ".".join(segments)
    # The helper above preserves separators as segment boundaries.  Rebuild
    # them from the source span so ``Foo.Bar`` and ``ns:Tag`` remain distinct.
    name = text[start:cursor]
    if unicodedata.normalize("NFC", name) != name:
        return None
    return name, cursor


def _is_jsx_identifier_start(character: str) -> bool:
    """Recognize an ECMAScript IdentifierStart character."""

    return len(character) == 1 and (
        character in "$_"
        or ord(character) in ECMASCRIPT_OTHER_ID_START_CODEPOINTS
        or _unicode_table_contains(ECMASCRIPT_ID_START_INTERVALS, ord(character))
    )


def _is_jsx_identifier_part(character: str) -> bool:
    """Recognize IdentifierPart, including Unicode combining marks.

    Python's ``str.isidentifier`` intentionally describes a complete
    identifier, so a combining mark is false when tested by itself even
    though it is a valid continuation.  ECMAScript's IdentifierPart includes
    Unicode ``Mn``/``Mc`` marks, decimal digits, connector punctuation, and
    the join controls.
    """

    return len(character) == 1 and (
        _is_jsx_identifier_start(character)
        or ord(character) in ECMASCRIPT_OTHER_ID_CONTINUE_CODEPOINTS
        or ord(character) in ECMASCRIPT_JOIN_CONTROL
        or _unicode_table_contains(ECMASCRIPT_ID_CONTINUE_INTERVALS, ord(character))
    )


# These sets are intentionally lexical/contextual rather than derived from
# Python's keyword table.  The adapter and the Python boundary must agree on
# the same ECMAScript IdentifierName grammar even when the host UCD changes.
_ECMASCRIPT_RESERVED_WORDS = frozenset(
    {
        "await",
        "break",
        "case",
        "catch",
        "class",
        "const",
        "continue",
        "debugger",
        "default",
        "delete",
        "do",
        "else",
        "enum",
        "export",
        "extends",
        "false",
        "finally",
        "for",
        "function",
        "if",
        "implements",
        "import",
        "in",
        "instanceof",
        "interface",
        "let",
        "new",
        "null",
        "package",
        "private",
        "protected",
        "public",
        "return",
        "static",
        "super",
        "switch",
        "this",
        "throw",
        "true",
        "try",
        "typeof",
        "var",
        "void",
        "while",
        "with",
        "yield",
    }
)


def is_identifier_name(value: str) -> bool:
    """Return whether *value* is a canonical ECMAScript IdentifierName."""

    if not isinstance(value, str) or not value:
        return False
    if unicodedata.normalize("NFC", value) != value:
        return False
    return _is_jsx_identifier_start(value[0]) and all(
        _is_jsx_identifier_part(character) for character in value[1:]
    )


def is_binding_identifier(value: str) -> bool:
    """Return whether *value* can be used as a lexical binding name."""

    return is_identifier_name(value) and value not in _ECMASCRIPT_RESERVED_WORDS


def is_declaration_key(value: str) -> bool:
    """Return whether *value* is an IdentifierName used as a property key.

    Property/export keys may be reserved words; they still cannot contain a
    non-canonical form or a character outside the pinned Unicode table.
    """

    return is_identifier_name(value)


@lru_cache(maxsize=1)
def identifier_classification_bitstream() -> bytes:
    """Encode the full Unicode range as one byte per code point.

    Bit 0 is IdentifierStart and bit 1 is IdentifierPart.  The fixed
    code-point order and byte encoding make the known-answer digest
    independent of Python's host Unicode database.
    """

    return bytes(
        (1 if _is_jsx_identifier_start(chr(codepoint)) else 0)
        | (2 if _is_jsx_identifier_part(chr(codepoint)) else 0)
        for codepoint in range(0x110000)
    )


IDENTIFIER_CLASSIFICATION_SHA256 = (
    "2b5d2feba3292a321e8c2497969be9e03ca24113de9e7f4803791ce4b645b1fa"
)


def identifier_classification_digest() -> str:
    """Return the known-answer SHA-256 for the complete classification map."""

    return hashlib.sha256(identifier_classification_bitstream()).hexdigest()


def _jsx_quoted_end(text: str, start: int) -> int:
    """Skip one JSX attribute or JavaScript string/template literal."""

    quote = text[start]
    assert quote in "'\"`"
    cursor = start + 1
    escaped = False
    while cursor < len(text):
        character = text[cursor]
        if escaped:
            escaped = False
        elif character == "\\":
            escaped = True
        elif character == quote:
            return cursor + 1
        cursor += 1
    return len(text)


def _jsx_regex_can_start(previous_character: str, previous_word: str | None) -> bool:
    """Use a conservative lexical test before skipping a JSX regex literal."""

    if previous_word in {
        "await",
        "case",
        "delete",
        "do",
        "else",
        "in",
        "instanceof",
        "of",
        "return",
        "throw",
        "typeof",
        "void",
        "yield",
    }:
        return True
    return not previous_character or previous_character in "([{=,:;!?&|+-*%^~<>"


def _jsx_expression_end(text: str, start: int) -> int | None:
    """Skip a balanced JSX attribute/child expression.

    Strings, templates, comments, and regular expressions are opaque inside
    the expression.  This prevents a literal ``}`` or ``export`` from
    changing the JSX stack used by the outer lexical scanner.
    """

    assert text[start] == "{"
    depth = 1
    cursor = start + 1
    line_comment = False
    block_comment = False
    previous_character = ""
    previous_word: str | None = None
    while cursor < len(text):
        character = text[cursor]
        if line_comment:
            if character in "\r\n":
                line_comment = False
            cursor += 1
            continue
        if block_comment:
            if text.startswith("*/", cursor):
                block_comment = False
                cursor += 2
            else:
                cursor += 1
            continue
        if text.startswith("//", cursor):
            line_comment = True
            cursor += 2
            continue
        if text.startswith("/*", cursor):
            block_comment = True
            cursor += 2
            continue
        if character in "'\"`":
            cursor = _jsx_quoted_end(text, cursor)
            previous_character = "literal"
            previous_word = None
            continue
        if character == "/" and _jsx_regex_can_start(previous_character, previous_word):
            regex_end = _regex_literal_end(text, cursor)
            if regex_end is not None:
                cursor = regex_end
                previous_character = "literal"
                previous_word = None
                continue
        if character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return cursor + 1
        if character.isspace():
            cursor += 1
            continue
        if _is_jsx_identifier_start(character):
            word_start = cursor
            cursor += 1
            while cursor < len(text) and _is_jsx_identifier_part(text[cursor]):
                cursor += 1
            previous_word = text[word_start:cursor]
            previous_character = "identifier"
            continue
        previous_word = None
        previous_character = character
        cursor += 1
    return None


def _jsx_element_end(text: str, start: int) -> int | None:
    """Return the end of a complete JSX element, if one starts here.

    A stack is required here: a first matching ``</Item>`` is not necessarily
    the close for ``<Item>`` when JSX nests same-name elements.  Self-closing
    tags and fragments are stack entries too, and attribute expressions are
    skipped before the next child tag is considered.  A valid TypeScript
    generic/comparison expression still returns ``None`` because it has no
    matching JSX close.
    """

    opening = _jsx_tag_end(text, start)
    if opening is None:
        return None
    cursor, name, closing, self_closing = opening
    if closing:
        return None
    if self_closing:
        return cursor
    stack: list[str | None] = [name]
    while cursor < len(text):
        if text[cursor] == "{":
            expression_end = _jsx_expression_end(text, cursor)
            if expression_end is None:
                return None
            cursor = expression_end
            continue
        if text.startswith("{/*", cursor):
            expression_end = _jsx_expression_end(text, cursor)
            if expression_end is None:
                return None
            cursor = expression_end
            continue
        if text.startswith("<!--", cursor):
            comment_end = text.find("-->", cursor + 4)
            if comment_end < 0:
                return None
            cursor = comment_end + 3
            continue
        if text[cursor] != "<":
            cursor += 1
            continue
        tag = _jsx_tag_end(text, cursor)
        if tag is None:
            cursor += 1
            continue
        tag_end, tag_name, tag_closing, tag_self_closing = tag
        if tag_closing:
            if not stack or stack[-1] != tag_name:
                return None
            stack.pop()
            cursor = tag_end
            if not stack:
                return cursor
            continue
        if not tag_self_closing:
            stack.append(tag_name)
        cursor = tag_end
    return None


def _regex_literal_end(text: str, start: int) -> int | None:
    """Return the end of a regex literal, preserving words inside its body."""

    index = start + 1
    in_class = False
    escaped = False
    while index < len(text):
        character = text[index]
        if escaped:
            escaped = False
        elif character == "\\":
            escaped = True
        elif character == "[":
            in_class = True
        elif character == "]" and in_class:
            in_class = False
        elif character == "/" and not in_class:
            index += 1
            while index < len(text) and (text[index].isidentifier() or text[index] == "$"):
                index += 1
            return index
        elif character in "\r\n":
            return None
        index += 1
    return None


def _regex_can_start(previous: dict[str, Any] | None) -> bool:
    if previous is None:
        return True
    if previous["kind"] == "identifier":
        return previous["value"] in {
            "await",
            "case",
            "delete",
            "do",
            "else",
            "in",
            "instanceof",
            "of",
            "return",
            "throw",
            "typeof",
            "void",
            "yield",
        }
    return previous["value"] in "([{=,:;!?&|+-*%^~<>"


def _is_program_file(file_record: dict[str, Any]) -> bool:
    """Return whether a frozen file can own semantic Next records."""

    path = file_record["path"]
    return (
        "program" in file_record["roles"]
        and not path.endswith(".d.ts")
        and path.endswith(SOURCE_PLAN_PROGRAM_SUFFIXES)
    )


def load_export_census_fixture() -> tuple[dict[str, Any], ...]:
    """Load and validate the immutable source bytes used by the reference census."""

    payload = json.loads(EXPORT_CENSUS_PATH.read_text(encoding="utf-8"))
    assert set(payload) == {"schema", "files"}
    assert payload["schema"] == EXPORT_CENSUS_SCHEMA
    files = cast(list[dict[str, Any]], payload["files"])
    assert files
    paths = [item["path"] for item in files]
    assert paths == sorted(paths)
    assert len(paths) == len(set(paths))
    result: list[dict[str, Any]] = []
    for item in files:
        assert set(item) == {"path", "content_base64"}
        _assert_file_path(item["path"])
        encoded = item["content_base64"]
        content = base64.b64decode(encoded, validate=True)
        assert base64.b64encode(content).decode("ascii") == encoded
        content.decode("utf-8")
        result.append({"path": item["path"], "content": content})
    return tuple(result)


def load_export_graph_fixture() -> tuple[dict[str, Any], ...]:
    """Load the independent frozen module graph used for re-export closure."""

    payload = json.loads(EXPORT_GRAPH_PATH.read_text(encoding="utf-8"))
    assert set(payload) == {"schema", "edges"}
    assert payload["schema"] == EXPORT_GRAPH_SCHEMA
    edges = cast(list[dict[str, Any]], payload["edges"])
    for edge in edges:
        assert set(edge) == {
            "owner_file_path",
            "source_specifier",
            "imported_name",
            "resolved_source_file_path",
            "expanded_exported_name",
            "target_declaration_key",
            "resolution",
        }
        _assert_file_path(edge["owner_file_path"])
        assert edge["source_specifier"]
        assert edge["source_specifier"].startswith(".")
        if edge["resolved_source_file_path"] is not None:
            _assert_file_path(edge["resolved_source_file_path"])
        assert (
            _is_export_identifier(edge["imported_name"], allow_default=True)
            or edge["imported_name"] == "*"
        )
        expanded = edge["expanded_exported_name"]
        assert expanded is None or _is_export_identifier(expanded, allow_default=True)
        declaration = edge["target_declaration_key"]
        assert declaration is None or _is_export_identifier(declaration)
        assert edge["resolution"] in {"component", "value", "type", "unknown"}
    edge_keys = [
        (edge["owner_file_path"], edge["source_specifier"], edge["imported_name"]) for edge in edges
    ]
    assert edge_keys == sorted(edge_keys)
    assert len(edge_keys) == len(set(edge_keys))
    return tuple(edges)


def load_export_graph_raw_fixture() -> dict[str, Any]:
    """Load raw declarations and re-export edges for independent recomputation."""

    payload = json.loads(EXPORT_GRAPH_RAW_PATH.read_text(encoding="utf-8"))
    assert set(payload) == {"schema", "modules", "edges"}
    assert payload["schema"] == EXPORT_GRAPH_RAW_SCHEMA
    modules = cast(list[dict[str, Any]], payload["modules"])
    assert modules
    module_paths = [module["path"] for module in modules]
    assert module_paths == sorted(module_paths)
    assert len(module_paths) == len(set(module_paths))
    for module in modules:
        assert set(module) == {"path", "exports"}
        _assert_file_path(module["path"])
        exports = cast(list[dict[str, Any]], module["exports"])
        export_names = [item["name"] for item in exports]
        assert export_names == sorted(export_names)
        assert len(export_names) == len(set(export_names))
        for item in exports:
            assert set(item) == {"name", "resolution", "target_declaration_key"}
            assert _is_export_identifier(item["name"], allow_default=True)
            assert item["resolution"] in {"component", "value", "type", "unknown"}
            if item["resolution"] == "component":
                assert _is_export_identifier(item["target_declaration_key"])
            else:
                assert item["target_declaration_key"] is None
    edges = cast(list[dict[str, Any]], payload["edges"])
    edge_keys: list[tuple[str, str, str, str, str, int | None, int | None]] = []
    for edge in edges:
        assert set(edge) <= {
            "owner_file_path",
            "source_specifier",
            "imported_name",
            "exported_name",
            "syntax_identity",
            "byte_start",
            "byte_end",
        }
        assert {
            "owner_file_path",
            "source_specifier",
            "imported_name",
            "exported_name",
        } <= set(edge)
        assert edge["owner_file_path"] in set(module_paths)
        assert edge["source_specifier"].startswith(".")
        assert edge["imported_name"] == "*" or _is_export_identifier(
            edge["imported_name"], allow_default=True
        )
        assert edge["exported_name"] == "*" or _is_export_identifier(
            edge["exported_name"], allow_default=True
        )
        assert (edge["imported_name"] == "*") is (edge["exported_name"] == "*")
        syntax_identity = edge.get("syntax_identity", "")
        if syntax_identity:
            assert isinstance(syntax_identity, str)
            assert unicodedata.normalize("NFC", syntax_identity) == syntax_identity
            assert not any(
                ord(character) < 0x20 or ord(character) == 0x7F for character in syntax_identity
            )
            assert isinstance(edge.get("byte_start"), int)
            assert isinstance(edge.get("byte_end"), int)
            assert 0 <= edge["byte_start"] < edge["byte_end"]
        else:
            assert "byte_start" not in edge and "byte_end" not in edge
        edge_keys.append(
            (
                edge["owner_file_path"],
                edge["source_specifier"],
                edge["imported_name"],
                edge["exported_name"],
                syntax_identity,
                edge.get("byte_start"),
                edge.get("byte_end"),
            )
        )
    assert edge_keys == sorted(edge_keys)
    assert len(edge_keys) == len(set(edge_keys))
    return {"modules": modules, "edges": edges}


def load_export_graph_cases() -> tuple[dict[str, Any], ...]:
    """Load closed alias/star/cycle/conflict graph witnesses."""

    payload = json.loads(EXPORT_GRAPH_CASES_PATH.read_text(encoding="utf-8"))
    assert set(payload) == {"schema", "cases"}
    assert payload["schema"] == EXPORT_GRAPH_CASES_SCHEMA
    cases = cast(list[dict[str, Any]], payload["cases"])
    names = [case["name"] for case in cases]
    assert names == sorted(names)
    assert len(names) == len(set(names))
    for case in cases:
        assert set(case) == {"name", "modules", "edges"}
        assert isinstance(case["name"], str) and case["name"]
        modules = cast(list[dict[str, Any]], case["modules"])
        assert modules
        module_paths = [module["path"] for module in modules]
        assert module_paths == sorted(module_paths)
        assert len(module_paths) == len(set(module_paths))
        module_path_set = set(module_paths)
        for module in modules:
            assert set(module) == {"path", "exports"}
            _assert_file_path(module["path"])
            exports = cast(list[dict[str, Any]], module["exports"])
            export_names = [item["name"] for item in exports]
            assert export_names == sorted(export_names)
            assert len(export_names) == len(set(export_names))
            for item in exports:
                assert set(item) == {"name", "resolution", "target_declaration_key"}
                assert _is_export_identifier(item["name"], allow_default=True)
                assert item["resolution"] in {"component", "value", "type", "unknown"}
                if item["resolution"] == "component":
                    assert _is_export_identifier(item["target_declaration_key"])
                else:
                    assert item["target_declaration_key"] is None
        edges = cast(list[dict[str, Any]], case["edges"])
        edge_keys = []
        for edge in edges:
            assert set(edge) <= {
                "owner_file_path",
                "source_specifier",
                "imported_name",
                "exported_name",
                "syntax_identity",
                "byte_start",
                "byte_end",
            }
            assert {
                "owner_file_path",
                "source_specifier",
                "imported_name",
                "exported_name",
            } <= set(edge)
            assert edge["owner_file_path"] in module_path_set
            assert edge["source_specifier"].startswith(".")
            imported_name = edge["imported_name"]
            assert imported_name == "*" or _is_export_identifier(imported_name, allow_default=True)
            exported_name = edge["exported_name"]
            assert exported_name == "*" or _is_export_identifier(exported_name, allow_default=True)
            assert (imported_name == "*") is (exported_name == "*")
            syntax_identity = edge.get("syntax_identity", "")
            if syntax_identity:
                assert unicodedata.normalize("NFC", syntax_identity) == syntax_identity
                assert isinstance(edge.get("byte_start"), int)
                assert isinstance(edge.get("byte_end"), int)
                assert 0 <= edge["byte_start"] < edge["byte_end"]
            else:
                assert "byte_start" not in edge and "byte_end" not in edge
            edge_keys.append(
                (
                    edge["owner_file_path"],
                    edge["source_specifier"],
                    imported_name,
                    exported_name,
                    syntax_identity,
                )
            )
        assert edge_keys == sorted(edge_keys)
        assert len(edge_keys) == len(set(edge_keys))
    return tuple(cases)


def _is_export_identifier(
    value: str, *, allow_default: bool = False, allow_keyword: bool = False
) -> bool:
    if allow_default and value == "default":
        return True
    if allow_keyword:
        return is_declaration_key(value)
    return is_binding_identifier(value)


def _export_tokens(content: bytes) -> tuple[list[dict[str, Any]], str, list[int]]:
    """Tokenize the closed fixture grammar while retaining UTF-8 byte spans.

    This is intentionally a small lexical scanner, not a TypeScript parser.
    Comments and whitespace are discarded only for recognition; every token
    retains its source range so the resulting census remains tied to immutable
    bytes.  The accepted grammar is closed by ``scan_export_syntax_census``.
    """

    text = content.decode("utf-8")
    offsets = [0]
    for character in text:
        offsets.append(offsets[-1] + len(character.encode("utf-8")))
    tokens: list[dict[str, Any]] = []
    previous: dict[str, Any] | None = None
    brace_depth = 0
    paren_depth = 0
    bracket_depth = 0

    def append_token(token: dict[str, Any]) -> None:
        nonlocal previous
        token.update(
            {
                "brace_depth": brace_depth,
                "paren_depth": paren_depth,
                "bracket_depth": bracket_depth,
            }
        )
        tokens.append(token)
        previous = token

    index = 1 if text.startswith("\ufeff") else 0
    length = len(text)
    while index < length:
        character = text[index]
        if character.isspace():
            index += 1
            continue
        if text.startswith("//", index):
            newline = text.find("\n", index + 2)
            index = length if newline < 0 else newline + 1
            continue
        if text.startswith("/*", index):
            end = text.find("*/", index + 2)
            assert end >= 0, "unterminated block comment"
            index = end + 2
            continue
        if character == "`":
            # Template literals are outside the closed export grammar.  Skip
            # the complete literal so an ``export`` word in its text (or in a
            # template interpolation) cannot become a false census row.
            index += 1
            while index < length:
                if text[index] == "\\":
                    index += 2
                    continue
                if text[index] == "`":
                    index += 1
                    break
                index += 1
            else:
                raise AssertionError("unterminated template literal")
            continue
        if character == "<":
            jsx_end = _jsx_element_end(text, index)
            if jsx_end is not None:
                index = jsx_end
                continue
        if character == "/" and _regex_can_start(previous):
            regex_end = _regex_literal_end(text, index)
            if regex_end is not None:
                index = regex_end
                continue
        start = index
        if character in "'\"":
            quote = character
            index += 1
            value_chars: list[str] = []
            while index < length:
                current = text[index]
                if current in "\r\n":
                    raise AssertionError("newline in export string")
                if current == quote:
                    index += 1
                    break
                if current == "\\":
                    index += 1
                    assert index < length
                    value_chars.append(text[index])
                    index += 1
                    continue
                value_chars.append(current)
                index += 1
            else:
                raise AssertionError("unterminated export string")
            append_token(
                {
                    "kind": "string",
                    "value": "".join(value_chars),
                    "char_start": start,
                    "char_end": index,
                }
            )
            continue
        if _is_jsx_identifier_start(character):
            index += 1
            while index < length:
                current = text[index]
                if _is_jsx_identifier_part(current):
                    index += 1
                else:
                    break
            value = text[start:index]
            assert _is_export_identifier(
                value,
                allow_default=value == "default",
                allow_keyword=True,
            ), value
            append_token(
                {
                    "kind": "identifier",
                    "value": value,
                    "char_start": start,
                    "char_end": index,
                }
            )
            continue
        if text.startswith("...", index):
            index += 3
            value = "..."
        else:
            index += 1
            value = character
        if value in "})]":
            if value == "}":
                assert brace_depth > 0
                brace_depth -= 1
            elif value == ")":
                assert paren_depth > 0
                paren_depth -= 1
            else:
                assert bracket_depth > 0
                bracket_depth -= 1
        append_token(
            {
                "kind": "punctuation",
                "value": value,
                "char_start": start,
                "char_end": index,
            }
        )
        if value in "({[":
            if value == "(":
                paren_depth += 1
            elif value == "[":
                bracket_depth += 1
            else:
                brace_depth += 1
    return tokens, text, offsets


def _token_end(tokens: list[dict[str, Any]], index: int) -> int:
    assert 0 <= index < len(tokens)
    return cast(int, tokens[index]["char_end"])


def _find_statement_end(tokens: list[dict[str, Any]], index: int) -> int:
    """Return the inclusive token index for a semicolon-terminated statement."""

    depth = 0
    for position in range(index, len(tokens)):
        value = tokens[position]["value"]
        if (
            position > index
            and value == "export"
            and tokens[position]["brace_depth"] == 0
            and tokens[position]["paren_depth"] == 0
            and tokens[position]["bracket_depth"] == 0
        ):
            raise AssertionError("export statement must end before the next module declaration")
        if value in "{[(":
            depth += 1
        elif value in "}])":
            depth -= 1
            assert depth >= 0
        elif value == ";" and depth == 0:
            return position
    # The closed grammar requires a semicolon for expressions and export
    # lists.  Declaration bodies are handled separately by _find_decl_end.
    raise AssertionError("export statement must end with semicolon")


def _matching_angle_end(tokens: list[dict[str, Any]], start: int) -> int | None:
    """Find the closing ``>`` for a declaration's generic parameter list."""

    assert tokens[start]["value"] == "<"
    depth = 0
    for position in range(start, len(tokens)):
        value = tokens[position]["value"]
        if value == "<":
            depth += 1
        elif value == ">":
            depth -= 1
            if depth == 0:
                return position
            if depth < 0:
                return None
    return None


def _matching_paren_end(tokens: list[dict[str, Any]], start: int) -> int | None:
    """Find a function parameter list's closing parenthesis."""

    assert tokens[start]["value"] == "("
    depth = 0
    for position in range(start, len(tokens)):
        value = tokens[position]["value"]
        if value == "(":
            depth += 1
        elif value == ")":
            depth -= 1
            if depth == 0:
                return position
            if depth < 0:
                return None
    return None


def _declaration_body_start(tokens: list[dict[str, Any]], index: int) -> int | None:
    """Locate a declaration body without mistaking a generic type literal for it."""

    declaration_kind = tokens[index]["value"]
    if declaration_kind == "async":
        declaration_kind = "function"
    if declaration_kind not in {"function", "class", "interface"}:
        return None

    cursor = index + 1
    if declaration_kind == "function" and tokens[index]["value"] == "async":
        assert cursor < len(tokens) and tokens[cursor]["value"] == "function"
        cursor += 1
    if cursor < len(tokens) and tokens[cursor]["value"] == "*":
        cursor += 1
    if cursor >= len(tokens) or tokens[cursor]["kind"] != "identifier":
        return None
    cursor += 1
    if cursor < len(tokens) and tokens[cursor]["value"] == "<":
        generic_end = _matching_angle_end(tokens, cursor)
        if generic_end is None:
            return None
        cursor = generic_end + 1

    if declaration_kind == "function":
        parameter_start = next(
            (
                position
                for position in range(cursor, len(tokens))
                if tokens[position]["value"] == "("
                and tokens[position]["brace_depth"] == tokens[index]["brace_depth"]
            ),
            None,
        )
        if parameter_start is None:
            return None
        parameter_end = _matching_paren_end(tokens, parameter_start)
        if parameter_end is None:
            return None
        cursor = parameter_end + 1

    base_brace_depth = tokens[index]["brace_depth"]
    # A top-level type literal can occur in a generic constraint or in a
    # function return annotation.  The declaration body follows a type-literal
    # close, so punctuation that can only introduce a type is skipped.  This
    # is deliberately conservative: unsupported syntax falls through to the
    # closed semicolon rule rather than producing a truncated span.
    type_introducers = {":", "|", "&", "=>", "extends", "implements", "=", "<", ","}
    for position in range(cursor, len(tokens)):
        token = tokens[position]
        if token["value"] == "export" and token["brace_depth"] == base_brace_depth:
            break
        if token["value"] != "{" or token["brace_depth"] != base_brace_depth:
            continue
        previous = tokens[position - 1]["value"] if position > 0 else None
        if previous in type_introducers:
            continue
        return position
    return None


def _find_decl_end(tokens: list[dict[str, Any]], index: int) -> int:
    """Find a declaration's balanced body, or its required semicolon."""

    declaration_kind = tokens[index]["value"]
    if declaration_kind == "async":
        declaration_kind = "function"
    if declaration_kind == "type":
        # Generic constraints may contain object types before the alias
        # equals sign.  Treat the whole type alias as a semicolon-terminated
        # statement instead of mistaking the first constraint brace for its
        # declaration body.
        return _find_statement_end(tokens, index)
    brace_start = _declaration_body_start(tokens, index)
    if brace_start is None:
        return _find_statement_end(tokens, index)
    depth = 0
    for position in range(brace_start, len(tokens)):
        value = tokens[position]["value"]
        if value == "{":
            depth += 1
        elif value == "}":
            depth -= 1
            if depth == 0:
                return position
    raise AssertionError("unbalanced export declaration")


def _export_string(tokens: list[dict[str, Any]], index: int) -> str:
    assert tokens[index]["kind"] == "string"
    value = cast(str, tokens[index]["value"])
    assert value and "\n" not in value and "\r" not in value
    return value


def _export_observation_row(
    *,
    path: str,
    content: bytes,
    offsets: list[int],
    start_token: dict[str, Any],
    end_token: dict[str, Any],
    syntax_kind: str,
    exported_name: str,
    role: str,
    reexport: bool,
    star: bool = False,
    source_specifier: str | None = None,
    imported_name: str | None = None,
    target_declaration_id: str | None = None,
) -> dict[str, Any]:
    char_start = cast(int, start_token["char_start"])
    char_end = cast(int, end_token["char_end"])
    byte_start = offsets[char_start]
    byte_end = offsets[char_end]
    token_bytes = content[byte_start:byte_end]
    token_identity = digest(
        {
            "owner_file_path": path,
            "byte_start": byte_start,
            "byte_end": byte_end,
            "token_bytes_sha256": hashlib.sha256(token_bytes).hexdigest(),
            "imported_name": imported_name,
            "exported_name": exported_name,
        }
    )
    return {
        "owner_file_path": path,
        "byte_start": byte_start,
        "byte_end": byte_end,
        "token_identity": token_identity,
        "syntax_identity": (f"export:{path}:{byte_start}:{byte_end}:{syntax_kind}:{exported_name}"),
        "syntax_kind": syntax_kind,
        "exported_name": exported_name,
        "role": role,
        "reexport": reexport,
        "star": star,
        "source_specifier": source_specifier,
        "imported_name": imported_name,
        "target_declaration_id": target_declaration_id,
    }


def _scan_export_file(path: str, content: bytes) -> list[dict[str, Any]]:
    tokens, _text, offsets = _export_tokens(content)
    rows: list[dict[str, Any]] = []
    position = 0
    while position < len(tokens):
        if (
            tokens[position]["value"] != "export"
            or tokens[position]["brace_depth"] != 0
            or tokens[position]["paren_depth"] != 0
            or tokens[position]["bracket_depth"] != 0
            or (position > 0 and tokens[position - 1]["value"] in {".", "?."})
        ):
            position += 1
            continue
        export_token = tokens[position]
        cursor = position + 1
        role = "value"
        if cursor < len(tokens) and tokens[cursor]["value"] == "type":
            role = "type"
            cursor += 1
        assert cursor < len(tokens)
        source_specifier: str | None = None
        if tokens[cursor]["value"] == "*":
            assert cursor + 2 < len(tokens)
            assert tokens[cursor + 1]["value"] == "from"
            source_specifier = _export_string(tokens, cursor + 2)
            end = cursor + 2
            if end + 1 < len(tokens) and tokens[end + 1]["value"] == ";":
                end += 1
            else:
                raise AssertionError("export-all statement must end with semicolon")
            rows.append(
                _export_observation_row(
                    path=path,
                    content=content,
                    offsets=offsets,
                    start_token=export_token,
                    end_token=tokens[end],
                    syntax_kind="export_all",
                    exported_name="*",
                    role=role,
                    reexport=True,
                    star=True,
                    source_specifier=source_specifier,
                    imported_name="*",
                )
            )
            position = end + 1
            continue
        if tokens[cursor]["value"] == "{":
            open_brace = cursor
            close_brace = next(
                (
                    candidate
                    for candidate in range(open_brace + 1, len(tokens))
                    if tokens[candidate]["value"] == "}"
                ),
                None,
            )
            assert close_brace is not None
            after = close_brace + 1
            if after < len(tokens) and tokens[after]["value"] == "from":
                assert after + 1 < len(tokens)
                source_specifier = _export_string(tokens, after + 1)
                end = after + 1
            else:
                end = close_brace
            if end + 1 < len(tokens) and tokens[end + 1]["value"] == ";":
                end += 1
            elif source_specifier is not None:
                raise AssertionError("re-export list must end with semicolon")
            else:
                raise AssertionError("export list must end with semicolon")
            item = open_brace + 1
            while item < close_brace:
                if tokens[item]["value"] == ",":
                    item += 1
                    continue
                item_start = item
                item_role = role
                if tokens[item]["value"] == "type":
                    item_role = "type"
                    item += 1
                assert item < close_brace
                item_imported_name = cast(str, tokens[item]["value"])
                assert tokens[item]["kind"] == "identifier"
                assert _is_export_identifier(item_imported_name, allow_default=True)
                item += 1
                exported_name = item_imported_name
                if item < close_brace and tokens[item]["value"] == "as":
                    assert item + 1 < close_brace
                    exported_name = cast(str, tokens[item + 1]["value"])
                    assert _is_export_identifier(exported_name, allow_default=True)
                    item += 2
                item_end = item - 1
                rows.append(
                    _export_observation_row(
                        path=path,
                        content=content,
                        offsets=offsets,
                        start_token=tokens[item_start],
                        end_token=tokens[item_end],
                        syntax_kind="reexport" if source_specifier is not None else "named_export",
                        exported_name=exported_name,
                        role=item_role,
                        reexport=source_specifier is not None,
                        source_specifier=source_specifier,
                        imported_name=item_imported_name,
                    )
                )
                assert item < len(tokens)
                if tokens[item]["value"] == ",":
                    item += 1
                elif item != close_brace:
                    raise AssertionError("invalid export list separator")
            position = end + 1
            continue
        if tokens[cursor]["value"] == "default":
            cursor += 1
            assert cursor < len(tokens)
            next_value = tokens[cursor]["value"]
            imported_name: str | None = None
            if next_value == "async":
                assert cursor + 1 < len(tokens) and tokens[cursor + 1]["value"] == "function"
                declaration_cursor = cursor + 2
                if declaration_cursor < len(tokens) and tokens[declaration_cursor]["value"] == "*":
                    declaration_cursor += 1
                if (
                    declaration_cursor < len(tokens)
                    and tokens[declaration_cursor]["kind"] == "identifier"
                ):
                    imported_name = cast(str, tokens[declaration_cursor]["value"])
                end = _find_decl_end(tokens, cursor)
            elif next_value in {"function", "class"}:
                declaration_cursor = cursor + 1
                if declaration_cursor < len(tokens) and tokens[declaration_cursor]["value"] == "*":
                    declaration_cursor += 1
                if (
                    declaration_cursor < len(tokens)
                    and tokens[declaration_cursor]["kind"] == "identifier"
                ):
                    imported_name = cast(str, tokens[declaration_cursor]["value"])
                end = _find_decl_end(tokens, cursor)
            else:
                if (
                    tokens[cursor]["kind"] == "identifier"
                    and cursor + 1 < len(tokens)
                    and tokens[cursor + 1]["value"] == ";"
                ):
                    imported_name = cast(str, tokens[cursor]["value"])
                end = _find_statement_end(tokens, cursor)
            rows.append(
                _export_observation_row(
                    path=path,
                    content=content,
                    offsets=offsets,
                    start_token=export_token,
                    end_token=tokens[end],
                    syntax_kind="default_export",
                    exported_name="default",
                    role="value",
                    reexport=False,
                    imported_name=imported_name,
                )
            )
            position = end + 1
            continue
        declaration = cast(str, tokens[cursor]["value"])
        if declaration == "async":
            assert cursor + 1 < len(tokens) and tokens[cursor + 1]["value"] == "function"
            declaration = "function"
        type_name_direct = role == "type" and tokens[cursor]["kind"] == "identifier"
        if type_name_direct:
            declaration = "type"
        if declaration in {"const", "let", "var", "function", "class", "type", "interface"}:
            if type_name_direct:
                declaration_cursor = cursor
            elif declaration == "function" and tokens[cursor]["value"] == "async":
                declaration_cursor = cursor + 2
            else:
                declaration_cursor = cursor + 1
            if (
                declaration in {"function", "class"}
                and declaration_cursor < len(tokens)
                and tokens[declaration_cursor]["value"] == "*"
            ):
                declaration_cursor += 1
            assert declaration_cursor < len(tokens)
            declared_name = cast(str, tokens[declaration_cursor]["value"])
            assert tokens[declaration_cursor]["kind"] == "identifier"
            assert _is_export_identifier(declared_name)
            declaration_start = cursor - 1 if type_name_direct else cursor
            end = (
                _find_decl_end(tokens, declaration_start)
                if declaration in {"function", "class", "type", "interface"}
                else _find_statement_end(tokens, cursor)
            )
            rows.append(
                _export_observation_row(
                    path=path,
                    content=content,
                    offsets=offsets,
                    start_token=export_token,
                    end_token=tokens[end],
                    syntax_kind="type_export"
                    if role == "type" or declaration in {"type", "interface"}
                    else "named_export",
                    exported_name=declared_name,
                    role="type"
                    if role == "type" or declaration in {"type", "interface"}
                    else "value",
                    reexport=False,
                    imported_name=declared_name,
                )
            )
            position = end + 1
            continue
        raise AssertionError(f"unsupported export syntax: {declaration}")
    return rows


def scan_export_syntax_census() -> list[dict[str, Any]]:
    """Derive the closed export grammar census from immutable UTF-8 bytes."""

    rows: list[dict[str, Any]] = []
    for fixture in load_export_census_fixture():
        rows.extend(_scan_export_file(cast(str, fixture["path"]), cast(bytes, fixture["content"])))
    rows.sort(key=canonical_json_bytes)
    assert len({row["token_identity"] for row in rows}) == len(rows)
    assert len({row["syntax_identity"] for row in rows}) == len(rows)
    return rows


# The propagation vocabulary is closed.  A failure root first reaches its
# declared seed records (or every record on its path for a file failure), then
# this table derives only ownership/reference edges from the reachable set.
TAINT_ROOT_RULES = {
    "parse_file": "file_all_records",
    "read_file": "file_all_records",
    "type_symbol": "type_subtree",
    "props_subtree": "type_subtree",
    "export_binding": "incoming_reexport",
    "component_flow": "component_flow",
    "module_relation": "relation_dependency",
    "boundary_derivation": "boundary_closure",
}
TAINT_EDGE_RULES = (
    "file_all_records",
    "incoming_reexport",
    "value_import_dependency",
    "component_flow",
    "boundary_closure",
    "type_subtree",
    "identity_dependency",
    "relation_dependency",
)


def _canonicalize(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [_canonicalize(item) for item in value]
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            assert isinstance(key, str)
            normalized_key = unicodedata.normalize("NFC", key)
            assert normalized_key not in normalized
            normalized[normalized_key] = _canonicalize(item)
        return normalized
    return value


def canonical_json_bytes(value: Any) -> bytes:
    """Return the v1 canonical JSON byte representation used by digests."""

    return json.dumps(
        _canonicalize(value),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _trusted_environment_snapshot() -> dict[str, Any]:
    """Return the checked-in trusted profile used by decision projections."""

    environment: dict[str, Any] = {
        "schema": "code-structure-viz.next-trusted-types/v1",
        "environment_version": "1",
        "semantic_profile_id": "next-trusted-profile-v1",
        "typescript_version": "5.9.2",
        "identifier_unicode_table_digest": ECMASCRIPT_IDENTIFIER_UNICODE_TABLE_DIGEST,
        "license_inventory_digest": TRUSTED_PROFILE_LICENSE_DIGEST,
        "files": [
            {
                "physical_path": physical_path,
                "virtual_path": virtual_path,
                "size_bytes": TRUSTED_PROFILE_FILE_SIZES[virtual_path],
                "sha256": TRUSTED_PROFILE_FILE_SHA256[virtual_path],
                "license_id": TRUSTED_PROFILE_FILE_LICENSES[virtual_path],
            }
            for physical_path, virtual_path in TRUSTED_PROFILE_PHYSICAL_TO_VIRTUAL
        ],
        "reserved_module_specifiers": list(TRUSTED_MODULES),
        "reserved_global_names": list(TRUSTED_GLOBALS),
        "certified_symbols": copy.deepcopy(list(TRUSTED_PROFILE_CERTIFIED_SYMBOLS)),
        "anti_shadowing_witness": list(TRUSTED_PROFILE_SHADOWING_WITNESS),
    }
    environment["sha256"] = digest(environment)
    return environment


def _toolchain_snapshot(*, node_status: str = "available") -> dict[str, Any]:
    """Return the closed toolchain descriptor owned by the run decision."""

    node_available = node_status == "available"
    node_failure_kind = None if node_available or node_status == "not_applicable" else "missing"
    return {
        "node": {
            "status": node_status,
            "version": "22.14.0" if node_available else None,
            "failure_kind": node_failure_kind,
        },
        "node_version": "22.14.0" if node_available else None,
        "typescript_version": "5.9.2",
        "adapter_version": "1.0.0",
        "protocol": "code-structure-viz.next-adapter/v1",
    }


def _compatibility_descriptor_snapshot() -> dict[str, Any]:
    """Return the pinned semantic descriptor sealed into each run decision."""

    descriptor: dict[str, Any] = {
        "schema": "code-structure-viz.next-semantic-compatibility/v1",
        "semantic_schema": "code-structure-viz.semantic/v1",
        "identity_versions": copy.deepcopy(IDENTITY_VERSIONS),
        "algorithm_versions": {
            "recognition": 1,
            "export": 1,
            "props": 1,
            "relation": 1,
            "fact": 1,
            "boundary": 1,
            "identifier_unicode": ECMASCRIPT_IDENTIFIER_UNICODE_VERSION,
            "identifier_unicode_table_digest": ECMASCRIPT_IDENTIFIER_UNICODE_TABLE_DIGEST,
        },
        "semantic_profile_id": "next-trusted-profile-v1",
    }
    descriptor["compatibility_id"] = digest(
        {
            "semantic_schema": descriptor["semantic_schema"],
            "identity_versions": descriptor["identity_versions"],
            "algorithm_versions": descriptor["algorithm_versions"],
            "semantic_profile_id": descriptor["semantic_profile_id"],
        }
    )
    return descriptor


def _publication_context_from_request(
    request: dict[str, Any] | None,
    run_context: NextRunContext,
    *,
    decision_context: NextDecisionContext | None = None,
    toolchain: dict[str, Any] | None = None,
    trusted_environment: dict[str, Any] | None = None,
    projects_for_fingerprint: list[dict[str, Any]] | None = None,
) -> NextPublicationContext:
    """Construct the immutable publication provenance at the boundary.

    This helper exists only for the data-only reference contract.  It is
    intentionally the *single* place that fills provenance when a fixture
    does not provide an already sealed context; writers never get to rebuild
    these values independently.
    """

    context = canonical_run_context(**run_context)
    source_request = copy.deepcopy(request) if request is not None else {}
    limits = copy.deepcopy(
        source_request.get("limits")
        or (decision_context.limits if decision_context is not None else None)
        or {**LIMIT_DEFAULTS, "max_entities": context["budget_resolved"]}
    )
    limits = {**LIMIT_DEFAULTS, **limits}
    limits["max_entities"] = context["budget_resolved"]
    projects = copy.deepcopy(source_request.get("projects", []))
    project_descriptors = [
        {
            key: copy.deepcopy(project[key])
            for key in ("root", "source_roots", "config_path", "compiler_options")
        }
        for project in projects
        if isinstance(project, dict)
        and {"root", "source_roots", "config_path", "compiler_options"} <= set(project)
    ]
    trusted_digest = (
        source_request.get("trusted_environment_digest")
        or source_request.get("trusted_type_environment", {}).get("sha256")
        or ("0" * 64)
    )
    plan_input = {
        "projects": project_descriptors,
        "limits": limits,
        "trusted_environment_digest": trusted_digest,
    }
    supplied_plan = source_request.get("source_plan")
    if isinstance(supplied_plan, dict):
        final_plan = copy.deepcopy(supplied_plan)
        _validate_source_plan_descriptor(final_plan)
    elif project_descriptors:
        final_plan = source_plan_descriptor(plan_input)
    else:
        # A request-independent failure has no source plan.  Keep a closed,
        # digestable descriptor rather than inventing a filesystem authority.
        final_plan = {
            "schema": "code-structure-viz.source-acquisition-plan/next/v1",
            "version": SOURCE_PLAN_VERSION,
            "projects": [],
            "resolved_control_paths": [],
            "local_extends": [],
            "file_role_map": [],
            "program_suffixes": list(SOURCE_PLAN_PROGRAM_SUFFIXES),
            "context_suffixes": list(SOURCE_PLAN_CONTEXT_SUFFIXES),
            "hard_exclusions": sorted(SOURCE_PLAN_HARD_EXCLUSIONS),
            "limits": limits,
            "trusted_environment_digest": trusted_digest,
        }
    source_files = [
        {
            "path": file_record.get("path"),
            "size_bytes": file_record.get("size_bytes", 0),
            "sha256": file_record.get("sha256", "0" * 64),
        }
        for file_record in source_request.get("files", [])
        if isinstance(file_record, dict) and file_record.get("path") is not None
    ]
    source_view = {
        "schema": "code-structure-viz.source-view/v1",
        "kind": "working-tree",
        "head_commit": None,
        "files": sorted(source_files, key=canonical_json_bytes),
        "file_count": len(source_files),
    }
    source_view_fingerprint = digest(source_view)
    source_plan_digest = digest(final_plan)
    seal_id = digest(
        {
            "source_plan_digest": source_plan_digest,
            "source_view_fingerprint": source_view_fingerprint,
            "operation": "decision-boundary-seal-v1",
        }
    )
    public_config = {
        "schema": "code-structure-viz.domain-config/next/v1",
        "projects": project_descriptors,
        "targets": list(
            source_request.get("targets", decision_context.targets if decision_context else ())
        ),
        "upstream_depth": 1,
        "downstream_depth": 1,
        "formats": list(context["requested_formats"]),
        "limits": limits,
        "source_plan": copy.deepcopy(final_plan),
        "source_plan_digest": source_plan_digest,
        "trusted_environment_digest": trusted_digest,
    }
    public_config["domain_config_digest"] = digest(
        {key: value for key, value in public_config.items() if key != "domain_config_digest"}
    )
    compatibility_descriptor = _compatibility_descriptor_snapshot()
    resolved_toolchain = copy.deepcopy(toolchain or source_request.get("toolchain", {}))
    resolved_toolchain.setdefault(
        "node",
        {"status": "unavailable", "version": None, "failure_kind": "missing"},
    )
    resolved_toolchain.setdefault("node_version", None)
    resolved_toolchain.setdefault("typescript_version", "5.9.2")
    resolved_toolchain.setdefault("adapter_version", source_request.get("adapter_version", "1.0.0"))
    resolved_toolchain.setdefault(
        "protocol", source_request.get("protocol", "code-structure-viz.next-adapter/v1")
    )
    resolved_trusted_environment = copy.deepcopy(
        trusted_environment
        or source_request.get("trusted_environment")
        or source_request.get("trusted_type_environment")
        or {"sha256": trusted_digest}
    )
    run_fingerprint_preimage = {
        "source_view_fingerprint": source_view_fingerprint,
        "source_plan_digest": source_plan_digest,
        "domain_config_digest": public_config["domain_config_digest"],
        "projects": copy.deepcopy(
            projects_for_fingerprint
            if projects_for_fingerprint is not None
            else source_request.get("projects", [])
        ),
        "targets": public_config["targets"],
        "formats": public_config["formats"],
        "stdout_selector": context["stdout_selector"],
        "limits": limits,
        "trusted_environment_digest": resolved_trusted_environment["sha256"],
        "node_version": resolved_toolchain["node_version"],
        "typescript_version": resolved_toolchain["typescript_version"],
        "adapter_version": resolved_toolchain["adapter_version"],
        "protocol": resolved_toolchain["protocol"],
        "identifier_unicode_version": ECMASCRIPT_IDENTIFIER_UNICODE_VERSION,
        "identifier_unicode_table_digest": ECMASCRIPT_IDENTIFIER_UNICODE_TABLE_DIGEST,
    }
    return NextPublicationContext(
        source_view_descriptor=source_view,
        source_view_fingerprint=source_view_fingerprint,
        final_source_acquisition_plan=final_plan,
        source_plan_digest=source_plan_digest,
        seal_id=seal_id,
        public_next_config=public_config,
        public_next_request=source_request or None,
        compatibility_descriptor=compatibility_descriptor,
        toolchain=resolved_toolchain,
        trusted_environment=resolved_trusted_environment,
        run_context=context,
        run_fingerprint_preimage=run_fingerprint_preimage,
    )


TRUSTED_PROFILE_LICENSE_DIGEST = digest(list(TRUSTED_PROFILE_LICENSES))


def resolved_config_digest(config: dict[str, Any]) -> str:
    return digest({key: value for key, value in config.items() if key != "domain_config_digest"})


def project_config_digest(project: dict[str, Any]) -> str:
    return digest(
        {
            "root": project["root"],
            "source_roots": project["source_roots"],
            "config_path": project["config_path"],
            "compiler_options": project["compiler_options"],
        }
    )


def _source_plan_projects(config_or_request: dict[str, Any]) -> list[dict[str, Any]]:
    """Canonicalize project roots for the input/config/source-plan surface."""

    return sorted(
        copy.deepcopy(config_or_request["projects"]),
        key=lambda project: canonical_json_bytes(unicodedata.normalize("NFC", project["root"])),
    )


def source_plan_descriptor(
    config_or_request: dict[str, Any],
    *,
    resolved_control_paths: list[dict[str, Any]] | None = None,
    local_extends: list[dict[str, Any]] | None = None,
    file_role_map: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the closed, reproducible SourceAcquisitionPlan/v1 descriptor."""

    if (
        "source_plan" in config_or_request
        and resolved_control_paths is None
        and local_extends is None
        and file_role_map is None
    ):
        existing = cast(dict[str, Any], copy.deepcopy(config_or_request["source_plan"]))
        _validate_source_plan_descriptor(existing)
        return existing

    projects = _source_plan_projects(config_or_request)
    default_control_paths = [
        {
            "project_root": project["root"],
            "path": (path if project["root"] == "." else f"{project['root'].rstrip('/')}/{path}"),
        }
        for project in projects
        for path in SOURCE_PLAN_CONTROL_PATHS
    ]
    default_file_role_map = [
        {
            **file_role,
            "project_root": project["root"],
            "path": (
                file_role["path"]
                if project["root"] == "."
                else f"{project['root'].rstrip('/')}/{file_role['path']}"
            ),
        }
        for project in projects
        for file_role in SOURCE_PLAN_FILE_ROLE_MAP
    ]
    descriptor = {
        "schema": "code-structure-viz.source-acquisition-plan/next/v1",
        "version": SOURCE_PLAN_VERSION,
        "projects": projects,
        "resolved_control_paths": sorted(
            copy.deepcopy(
                resolved_control_paths
                if resolved_control_paths is not None
                else [
                    *default_control_paths,
                ]
            ),
            key=canonical_json_bytes,
        ),
        "local_extends": sorted(copy.deepcopy(local_extends or []), key=canonical_json_bytes),
        "file_role_map": sorted(
            copy.deepcopy(file_role_map if file_role_map is not None else default_file_role_map),
            key=canonical_json_bytes,
        ),
        "program_suffixes": list(SOURCE_PLAN_PROGRAM_SUFFIXES),
        "context_suffixes": list(SOURCE_PLAN_CONTEXT_SUFFIXES),
        "hard_exclusions": sorted(SOURCE_PLAN_HARD_EXCLUSIONS),
        "limits": copy.deepcopy(config_or_request["limits"]),
        "trusted_environment_digest": config_or_request["trusted_environment_digest"],
    }
    _validate_source_plan_descriptor(descriptor)
    return descriptor


def _validate_source_plan_descriptor(descriptor: dict[str, Any]) -> None:
    assert set(descriptor) == {
        "schema",
        "version",
        "projects",
        "resolved_control_paths",
        "local_extends",
        "file_role_map",
        "program_suffixes",
        "context_suffixes",
        "hard_exclusions",
        "limits",
        "trusted_environment_digest",
    }
    assert descriptor["schema"] == "code-structure-viz.source-acquisition-plan/next/v1"
    assert descriptor["version"] == SOURCE_PLAN_VERSION
    assert descriptor["projects"] == _source_plan_projects({"projects": descriptor["projects"]})
    project_roots = {project["root"] for project in descriptor["projects"]}
    for project in descriptor["projects"]:
        _assert_path(project["root"])
        assert project["source_roots"] == sorted(set(project["source_roots"]))
        for source_root in project["source_roots"]:
            _assert_path(source_root)
            assert _under(source_root, project["root"])
        if project["config_path"] is not None:
            _assert_file_path(project["config_path"])
            assert _under(project["config_path"], project["root"])
    assert descriptor["resolved_control_paths"] == sorted(
        descriptor["resolved_control_paths"], key=canonical_json_bytes
    )
    for control_path in descriptor["resolved_control_paths"]:
        assert set(control_path) == {"project_root", "path"}
        assert control_path["project_root"] in project_roots
        _assert_path(control_path["project_root"])
        _assert_file_path(control_path["path"])
        assert _under(control_path["path"], control_path["project_root"])
    assert descriptor["local_extends"] == sorted(
        descriptor["local_extends"], key=canonical_json_bytes
    )
    for local_extend in descriptor["local_extends"]:
        assert set(local_extend) == {"project_root", "config_path", "extends"}
        assert local_extend["project_root"] in project_roots
        _assert_path(local_extend["project_root"])
        _assert_file_path(local_extend["config_path"])
        assert _under(local_extend["config_path"], local_extend["project_root"])
        assert local_extend["extends"] == sorted(set(local_extend["extends"]))
        for extend in local_extend["extends"]:
            _assert_file_path(extend)
            assert _under(extend, local_extend["project_root"])
    assert descriptor["file_role_map"] == sorted(
        descriptor["file_role_map"], key=canonical_json_bytes
    )
    role_keys: list[tuple[str, str]] = []
    for file_role in descriptor["file_role_map"]:
        assert set(file_role) == {"project_root", "path", "roles", "effective_role"}
        assert file_role["project_root"] in project_roots
        _assert_path(file_role["project_root"])
        _assert_file_path(file_role["path"])
        assert _under(file_role["path"], file_role["project_root"])
        assert file_role["roles"]
        assert file_role["roles"] == sorted(set(file_role["roles"]), key=ROLE_ORDER.__getitem__)
        assert set(file_role["roles"]) <= set(ROLES)
        assert file_role["effective_role"] == max(
            file_role["roles"], key=ROLE_PRECEDENCE.__getitem__
        )
        role_keys.append((file_role["project_root"], file_role["path"]))
    assert len(role_keys) == len(set(role_keys))
    assert descriptor["program_suffixes"] == list(SOURCE_PLAN_PROGRAM_SUFFIXES)
    assert descriptor["context_suffixes"] == list(SOURCE_PLAN_CONTEXT_SUFFIXES)
    assert descriptor["hard_exclusions"] == sorted(SOURCE_PLAN_HARD_EXCLUSIONS)
    validate_limits(descriptor["limits"])
    assert re.fullmatch(r"[0-9a-f]{64}", descriptor["trusted_environment_digest"])


def source_plan_digest(config_or_request: dict[str, Any]) -> str:
    """Hash every resolved SourceAcquisitionPlan field, never a partial proxy."""

    descriptor = config_or_request.get("source_plan")
    if descriptor is None:
        descriptor = source_plan_descriptor(config_or_request)
    else:
        descriptor = copy.deepcopy(descriptor)
        _validate_source_plan_descriptor(descriptor)
        assert descriptor["projects"] == _source_plan_projects(config_or_request)
        assert descriptor["limits"] == config_or_request["limits"]
        assert (
            descriptor["trusted_environment_digest"]
            == config_or_request["trusted_environment_digest"]
        )
    return digest(descriptor)


def _without(value: dict[str, Any], key: str) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result.pop(key, None)
    return result


def identity_preimage(record: dict[str, Any]) -> dict[str, Any]:
    """Return the closed, content-independent identity preimage for a record.

    The preimage is intentionally made from semantic identity fields only;
    ranges, ordering, aliases, source text and other payload fields cannot
    change an entity's identity.  A caller must still validate ownership and
    cross-record references separately.
    """

    kind = record["kind"]
    if kind == "project":
        identity: dict[str, Any] = {"root": record["root"]}
    elif kind in {"file", "module"}:
        identity = {"project_id": record["project_id"], "path": record["path"]}
    elif kind == "component":
        identity = {"module_id": record["module_id"], "declaration_key": record["declaration_key"]}
    elif kind == "export_binding":
        identity = {
            "owner_id": record["owner_id"],
            "exported_name": record["exported_name"],
            "role": record["role"],
        }
    elif kind == "import_binding":
        identity = {
            "owner_id": record["owner_id"],
            "imported_name": record["imported_name"],
            "role": record["role"],
            "source": record["source"],
        }
    elif kind == "prop":
        identity = {"owner_id": record["owner_id"], "name": record["name"]}
    elif kind in {"static_import", "literal_dynamic_import"}:
        identity = {
            "kind": kind,
            "source_id": record["source_id"],
            "target": record["target"],
            "role": record["role"],
            "reexport": record["reexport"],
            "boundary_effect": record["boundary_effect"],
        }
    elif kind == "jsx_render":
        identity = {"kind": kind, "source_id": record["source_id"], "target": record["target"]}
    elif kind == "component_wrap":
        identity = {
            "kind": kind,
            "source_id": record["source_id"],
            "target_component_id": record["target_component_id"],
        }
    elif kind in {"client_entry", "router_context"}:
        # Fact values are semantic: a router context mutation must not retain
        # a stale ID even though the owner remains the same.
        identity = {"kind": kind, "owner_id": record["owner_id"], "value": record["value"]}
    else:
        raise AssertionError(f"unknown Next record kind: {kind}")
    return {
        "kind": kind,
        "version": IDENTITY_VERSIONS[RECORD_ID_PREFIX[kind]],
        "identity": identity,
    }


def recompute_record_id(record: dict[str, Any]) -> str:
    """Compute the kind-prefixed SHA-256 ID mandated by Next semantic v1."""

    kind = record["kind"]
    return f"next:{RECORD_ID_PREFIX[kind]}:{digest(identity_preimage(record))}"


def recompute_compatibility_id(descriptor: dict[str, Any]) -> str:
    """Recompute the compatibility ID from the normative, content-independent preimage."""

    return digest(
        {
            "semantic_schema": descriptor["semantic_schema"],
            "identity_versions": descriptor["identity_versions"],
            "algorithm_versions": descriptor["algorithm_versions"],
            "semantic_profile_id": descriptor["semantic_profile_id"],
        }
    )


def recompute_request_id(request: dict[str, Any]) -> str:
    return digest(_without(request, "request_id"))


def validate_request_envelope(request: dict[str, Any]) -> None:
    trusted = request["trusted_type_environment"]
    assert set(trusted) == {"schema", "environment_version", "semantic_profile_id", "sha256"}
    assert trusted["schema"] == "code-structure-viz.next-trusted-types/v1"
    assert trusted["environment_version"] == "1"
    assert trusted["semantic_profile_id"] == "next-trusted-profile-v1"
    assert re.fullmatch(r"[0-9a-f]{64}", trusted["sha256"])
    assert request["request_id"] == recompute_request_id(request)
    context = canonical_run_context(**request["run_context"])
    assert context["budget_resolved"] == request["limits"]["max_entities"]
    validate_limits(request["limits"])
    validate_request_files(request)
    assert canonical_json_bytes(request) == canonical_json_bytes(_canonicalize(request))
    validate_encoded_stdin_size(request)


def _validate_closed_response_schema(response: dict[str, Any]) -> None:
    """Apply the checked-in closed response schema after bounded decoding.

    This is deliberately kept at the raw-response trust boundary.  The
    adapter response is not allowed to choose a looser object shape merely
    because a later typed target failure will be returned.
    """

    registry = Registry()
    schema_dir = REPO_ROOT / "schemas"
    for schema_path in schema_dir.glob("*.schema.json"):
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        schema_id = schema.get("$id")
        if isinstance(schema_id, str):
            registry = registry.with_resource(
                schema_id,
                Resource.from_contents(cast(dict[str, Any], schema)),
            )
    validator = Draft202012Validator(
        json.loads(
            (schema_dir / "next-adapter-response-v1.schema.json").read_text(encoding="utf-8")
        ),
        registry=registry,
    )
    try:
        validator.validate(response)
    except ValidationError as exc:
        raise AssertionError("adapter response violates its closed schema") from exc


def _validate_response_base(
    response: dict[str, Any],
    *,
    allowed_missing_module_keys: set[tuple[str, str]] | None = None,
    allowed_missing_module_ids: set[str] | None = None,
    allowed_duplicate_module_keys: set[tuple[str, str]] | None = None,
) -> None:
    """Validate path, order, and counter invariants before typed target routing.

    File-to-Module cardinality is intentionally *not* checked here: that one
    relation is the typed target-failure branch below.  All other inexpensive
    response invariants must be checked first so an unsafe compound response
    cannot be relabelled as ``CSV-NEXT-TARGET-001``.
    """

    model = response["model"]
    for project in model["projects"]:
        _assert_path(project["root"])
        for source_root in project["source_roots"]:
            _assert_path(source_root)
        if project["config_path"] is not None:
            _assert_file_path(project["config_path"])
    for file_record in model["files"]:
        _assert_file_path(file_record["path"])
    for module in model["modules"]:
        _assert_file_path(module["path"])
    _validate_model_diagnostics(model["diagnostics"])

    counts = model["coverage"]["counts"]
    for collection in COLLECTIONS:
        assert counts[collection] == len(model[collection])
    assert counts["published"] == sum(len(model[collection]) for collection in COLLECTIONS)
    assert counts["discovered"] >= counts["published"]
    assert counts["internal_entities"] == len(model["modules"]) + len(model["components"])

    proof = response["proof"]
    for root in proof["failure_roots"]:
        if root["path_ref"] is not None:
            _assert_file_path(root["path_ref"])
    for observation in proof["export_observations"]:
        _assert_file_path(observation["owner_file_path"])
    for witness in proof["export_reexport_witness"]:
        _assert_file_path(witness["owner_file_path"])
    for resolution in proof["target_resolutions"]:
        canonical_target_key(resolution["target_key"])
    base_model = _deduplicated_model_for_base_validation(
        model,
        allowed_duplicate_module_keys or set(),
    )
    validate_model(
        base_model,
        max_model_records=response["limits"]["max_model_records"],
        allowed_missing_module_keys=allowed_missing_module_keys,
        allowed_missing_module_ids=allowed_missing_module_ids,
    )


def _validate_target_exception_proof_base(
    proof: dict[str, Any],
    model: dict[str, Any],
    request_targets: list[str],
    failure: NextTargetCompletenessFailure,
) -> None:
    """Validate the complete proof base before typed target routing.

    A selected File→Module cardinality failure is the only model exception.
    The proof still has to be a complete, independently joined witness: every
    model record is present exactly once (apart from the one permitted
    byte-identical duplicate), all roots/edges and taint dispositions close,
    and export observations/witnesses agree with the same reduced model.  This
    makes an unrelated dangling reference unable to hide behind the typed
    ``CSV-NEXT-TARGET-001`` outcome.
    """

    _validate_proof_reason_semantics(proof, model)
    duplicate_keys = _target_duplicate_module_exceptions(model, request_targets, failure)
    base_model = _deduplicated_model_for_base_validation(model, duplicate_keys)
    expected_by_collection = {
        collection: {record["id"]: record for record in base_model[collection]}
        for collection in COLLECTIONS
    }
    discovered: dict[str, dict[str, dict[str, Any]]] = {
        collection: {} for collection in COLLECTIONS
    }
    discovered_ids: set[str] = set()
    discovered_order: list[tuple[str, str]] = []
    for item in proof["discovered_records"]:
        collection = item["collection"]
        record_id = item["record_id"]
        assert collection in COLLECTIONS
        assert record_id not in discovered_ids
        assert record_id not in discovered[collection]
        assert _id_kind(record_id) == collection.removesuffix("s")
        supplied_record = item.get("record")
        if supplied_record is None:
            assert record_id in expected_by_collection[collection]
            record = expected_by_collection[collection][record_id]
        else:
            # Published model records are referenced by ID only.  A payload is
            # allowed solely for a proof-only discovered record that cannot be
            # present in the published model.
            assert record_id not in expected_by_collection[collection]
            record = supplied_record
            assert record["id"] == record_id
        assert recompute_record_id(record) == record_id
        assert all(taint in TAINTS for taint in item["taints"])
        assert item["taints"] == sorted(item["taints"], key=TAINT_ORDER_INDEX.__getitem__)
        discovered[collection][record_id] = {**item, "record": record}
        discovered_ids.add(record_id)
        discovered_order.append((collection, record_id))
    assert all(
        set(discovered[collection]) == set(expected_by_collection[collection])
        for collection in COLLECTIONS
    )
    expected_order = [
        (collection, record["id"])
        for collection in COLLECTIONS
        for record in base_model[collection]
    ]
    assert discovered_order == expected_order

    failure_ids = {root["id"] for root in proof["failure_roots"]}
    assert len(failure_ids) == len(proof["failure_roots"])
    for root in proof["failure_roots"]:
        assert root["record_ids"] == sorted(set(root["record_ids"]))
        assert set(root["record_ids"]) <= discovered_ids
        assert root["collection"] in COLLECTIONS
        assert root["kind"] in TAINTS
        if root["path_ref"] is not None:
            _assert_file_path(root["path_ref"])
    all_sources = discovered_ids | failure_ids
    assert proof["causal_edges"] == derive_required_causal_edges(proof, discovered)
    for edge in proof["causal_edges"]:
        assert edge["source_id"] in all_sources
        assert edge["record_id"] in discovered_ids

    published = {collection: set(expected_by_collection[collection]) for collection in COLLECTIONS}
    excluded: dict[str, set[str]] = {collection: set() for collection in COLLECTIONS}
    failed: dict[str, set[str]] = {collection: set() for collection in COLLECTIONS}
    for item in proof["excluded"]:
        collection = item["collection"]
        record_id = item["record_id"]
        assert record_id in discovered[collection]
        assert record_id not in published[collection]
        assert record_id not in excluded[collection]
        excluded[collection].add(record_id)
    for item in proof["failed"]:
        collection = item["collection"]
        record_id = item["record_id"]
        assert record_id in discovered[collection]
        assert record_id not in published[collection]
        assert record_id not in failed[collection]
        failed[collection].add(record_id)
    for collection in COLLECTIONS:
        assert excluded[collection].isdisjoint(failed[collection])
        assert set(discovered[collection]) == (
            published[collection] | excluded[collection] | failed[collection]
        )
    tainted_ids = {
        record_id
        for records in discovered.values()
        for record_id, item in records.items()
        if item["taints"]
    }
    assert _derived_taint_fixed_point(proof, discovered) == tainted_ids
    assert not tainted_ids.intersection(set().union(*published.values()))

    for observation in proof["export_observations"]:
        assert observation["owner_module_id"] in discovered_ids
        assert observation["owner_module_id"].startswith("next:module:")
        if observation["resolved_source_module_id"] is not None:
            assert observation["resolved_source_module_id"] in discovered_ids
        if observation["component_id"] is not None:
            assert observation["component_id"] in discovered_ids
    for witness in proof["export_reexport_witness"]:
        assert witness["owner_module_id"] in discovered_ids
        if witness["resolved_source_module_id"] is not None:
            assert witness["resolved_source_module_id"] in discovered_ids
        if witness["target_declaration_id"] is not None:
            assert witness["target_declaration_id"] in discovered_ids
    validate_export_observations(proof["export_observations"], base_model)
    assert proof["export_resolution_witness"] == expected_export_resolution_witness(base_model)
    assert proof["export_reexport_witness"] == expected_export_reexport_witness(base_model)

    effective_targets = list(request_targets) or [
        f"path:{file_record['path']}"
        for file_record in model["files"]
        if _is_program_file(file_record)
    ]
    failed_by_key = {item["target_key"]: item["reason"] for item in failure.failures}
    expected_target_rows: list[dict[str, Any]] = []
    for target in effective_targets:
        target_key = canonical_target_key(target)
        if target_key in failed_by_key:
            expected_target_rows.append(
                {
                    "target_key": target_key,
                    "status": "failed",
                    "record_ids": [],
                    "reason": failed_by_key[target_key],
                }
            )
        else:
            rows = resolve_target_resolutions([target], base_model)
            assert len(rows) == 1
            expected_target_rows.append(rows[0])
    expected_target_rows.sort(key=canonical_json_bytes)
    assert proof["target_resolutions"] == expected_target_rows
    expected_target_coverage = [
        {
            "target_key": row["target_key"],
            "status": "complete" if row["status"] == "resolved" else "failed",
            "record_ids": row["record_ids"],
            **({"reason": row["reason"]} if row.get("reason") in TARGET_FAILURE_REASONS else {}),
        }
        for row in expected_target_rows
    ]
    assert model["coverage"]["target_completeness"] == expected_target_coverage


def _validate_project_correspondence(
    request_projects: list[dict[str, Any]], model_projects: list[dict[str, Any]]
) -> None:
    """Compare projects by immutable ID/root, then validate each wire order."""

    request_by_id = {project["id"]: project for project in request_projects}
    model_by_id = {project["id"]: project for project in model_projects}
    assert len(request_by_id) == len(request_projects)
    assert len(model_by_id) == len(model_projects)
    assert set(request_by_id) == set(model_by_id)
    for project_id, request_project in request_by_id.items():
        model_project = model_by_id[project_id]
        assert model_project == request_project
        assert model_project["root"] == request_project["root"]
    request_roots = [project["root"] for project in request_projects]
    assert request_roots == sorted(request_roots, key=canonical_json_bytes)
    model_ids = [project["id"] for project in model_projects]
    assert model_ids == sorted(model_ids)


class NextTargetCompletenessFailure(AssertionError):
    """Typed pre-model failure for a selected program File→Module mapping."""

    def __init__(self, failures: list[dict[str, Any]]) -> None:
        self.failures = failures
        super().__init__("selected target has no unique program File→Module mapping")


TARGET_FAILURE_REASONS = frozenset(
    {
        "missing",
        "component_only",
        "duplicate",
        "out_of_scope",
        "non_program",
        "control_context",
        "project_ambiguity",
        "selected_taint",
    }
)


def target_completeness_failure(
    model: dict[str, Any], targets: list[str]
) -> NextTargetCompletenessFailure | None:
    """Check target completeness before strict model validation can assert.

    This intentionally reads the raw discovered arrays.  A duplicate module ID
    is still classified as a target failure rather than escaping as an opaque
    collection assertion; the public outcome is therefore deterministic.
    """

    files = list(model.get("files", []))
    modules = list(model.get("modules", []))
    components = list(model.get("components", []))
    modules_by_key: dict[tuple[Any, Any], list[dict[str, Any]]] = {}
    for module in modules:
        modules_by_key.setdefault((module.get("project_id"), module.get("path")), []).append(module)
    component_module_ids = {component.get("module_id") for component in components}
    selected_targets = list(targets)
    if not selected_targets:
        selected_targets = [
            f"path:{file_record.get('path')}"
            for file_record in files
            if _is_program_file(file_record)
        ]
    failures: list[dict[str, Any]] = []
    for target in selected_targets:
        target_key = canonical_target_key(target)
        requested_path = target_key.removeprefix(TARGET_SELECTOR_PREFIX)
        exact_files = [file for file in files if file.get("path") == requested_path]
        matching_files = exact_files or [
            file for file in files if _under(file.get("path", ""), requested_path)
        ]
        project_ids = {file.get("project_id") for file in matching_files}
        selected_program_files = [file for file in matching_files if _is_program_file(file)]
        reason = None
        if not matching_files:
            reason = "missing"
        elif len(project_ids) != 1 or len(exact_files) > 1:
            reason = "project_ambiguity"
        elif exact_files and not _is_program_file(exact_files[0]):
            reason = "non_program"
        elif not selected_program_files:
            reason = "control_context"
        else:
            for file in selected_program_files:
                key = (file.get("project_id"), file.get("path"))
                matching_modules = modules_by_key.get(key, [])
                if len(matching_modules) != 1:
                    expected_module_id = recompute_record_id(
                        {
                            "kind": "module",
                            "project_id": key[0],
                            "path": key[1],
                        }
                    )
                    if not matching_modules and expected_module_id in component_module_ids:
                        reason = "component_only"
                    elif not matching_modules:
                        reason = "missing"
                    else:
                        reason = "duplicate"
                    break
                module_id = matching_modules[0].get("id")
                if module_id not in {module.get("id") for module in modules}:
                    reason = "missing"
                    break
        if reason is not None:
            failures.append({"target_key": target_key, "reason": reason})
    return NextTargetCompletenessFailure(failures) if failures else None


def _target_missing_module_exceptions(
    model: dict[str, Any],
    targets: list[str],
    failure: NextTargetCompletenessFailure | None,
) -> tuple[set[tuple[str, str]], set[str]]:
    """Return only selected File→Module gaps permitted by typed target routing.

    A target failure does not make the rest of the response structurally
    untrusted.  The sole exception is the selected program File→Module
    cardinality gap: an absent Module is the typed ``missing`` case, and its
    one orphan Component is the typed ``component_only`` case.  Every other
    missing or duplicate relation remains a base-validation failure.
    """

    if failure is None:
        return set(), set()
    failure_reasons = {item["target_key"]: item["reason"] for item in failure.failures}
    selected_targets = list(targets)
    if not selected_targets:
        selected_targets = [
            f"path:{file_record.get('path')}"
            for file_record in model.get("files", [])
            if _is_program_file(file_record)
        ]
    modules_by_key: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for module in model["modules"]:
        modules_by_key.setdefault((module["project_id"], module["path"]), []).append(module)
    allowed_keys: set[tuple[str, str]] = set()
    allowed_ids: set[str] = set()
    files = list(model["files"])
    for target in selected_targets:
        target_key = canonical_target_key(target)
        if failure_reasons.get(target_key) not in {"missing", "component_only"}:
            continue
        requested_path = target_key.removeprefix(TARGET_SELECTOR_PREFIX)
        exact_files = [file for file in files if file["path"] == requested_path]
        matching_files = exact_files or [
            file for file in files if _under(file["path"], requested_path)
        ]
        for file_record in matching_files:
            if not _is_program_file(file_record):
                continue
            module_key = (file_record["project_id"], file_record["path"])
            if modules_by_key.get(module_key):
                continue
            allowed_keys.add(module_key)
            if failure_reasons[target_key] == "component_only":
                allowed_ids.add(
                    recompute_record_id(
                        {
                            "kind": "module",
                            "project_id": file_record["project_id"],
                            "path": file_record["path"],
                        }
                    )
                )
    return allowed_keys, allowed_ids


def _target_duplicate_module_exceptions(
    model: dict[str, Any],
    targets: list[str],
    failure: NextTargetCompletenessFailure | None,
) -> set[tuple[str, str]]:
    """Return only byte-identical duplicate Modules for failed targets.

    The duplicate is a typed File→Module cardinality failure, but the rest of
    the response must still pass ordinary collection/reference validation.
    Therefore this helper grants no general duplicate exemption: it identifies
    the selected program-file keys whose duplicate rows are exactly identical,
    and the caller removes only the extra copies in a validation copy.  Any
    non-selected, inconsistent, or otherwise unrelated duplicate remains a
    base-validation failure.
    """

    if failure is None:
        return set()
    failure_reasons = {item["target_key"]: item["reason"] for item in failure.failures}
    selected_targets = list(targets)
    if not selected_targets:
        selected_targets = [
            f"path:{file_record.get('path')}"
            for file_record in model.get("files", [])
            if _is_program_file(file_record)
        ]
    modules_by_key: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for module in model["modules"]:
        modules_by_key.setdefault((module["project_id"], module["path"]), []).append(module)
    files = list(model["files"])
    allowed: set[tuple[str, str]] = set()
    for target in selected_targets:
        target_key = canonical_target_key(target)
        if failure_reasons.get(target_key) != "duplicate":
            continue
        requested_path = target_key.removeprefix(TARGET_SELECTOR_PREFIX)
        exact_files = [file for file in files if file["path"] == requested_path]
        matching_files = exact_files or [
            file for file in files if _under(file["path"], requested_path)
        ]
        for file_record in matching_files:
            if not _is_program_file(file_record):
                continue
            module_key = (file_record["project_id"], file_record["path"])
            candidates = modules_by_key.get(module_key, [])
            if len(candidates) <= 1:
                continue
            encoded = canonical_json_bytes(candidates[0])
            if all(canonical_json_bytes(candidate) == encoded for candidate in candidates[1:]):
                allowed.add(module_key)
    return allowed


def _deduplicated_model_for_base_validation(
    model: dict[str, Any], duplicate_keys: set[tuple[str, str]]
) -> dict[str, Any]:
    """Copy a model while removing only validated extra duplicate Module rows."""

    if not duplicate_keys:
        return model
    candidate = copy.deepcopy(model)
    modules: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    removed = 0
    for module in candidate["modules"]:
        module_key = (module["project_id"], module["path"])
        if module_key not in duplicate_keys or module_key not in seen:
            modules.append(module)
            seen.add(module_key)
            continue
        removed += 1
    assert removed >= 1
    candidate["modules"] = modules
    counts = candidate["coverage"]["counts"]
    for collection in COLLECTIONS:
        counts[collection] = len(candidate[collection])
    counts["published"] = sum(len(candidate[collection]) for collection in COLLECTIONS)
    counts["discovered"] = max(counts["published"], counts["discovered"] - removed)
    counts["internal_entities"] = len(candidate["modules"]) + len(candidate["components"])
    return candidate


def target_failure_decision(
    failure: NextTargetCompletenessFailure, run_context: NextRunContext
) -> dict[str, Any]:
    """Return the stable response-envelope projection for a target failure."""

    context = canonical_run_context(**run_context)
    assert failure.failures
    normalized_failures = [
        {"target_key": canonical_target_key(item["target_key"]), "reason": item["reason"]}
        for item in failure.failures
    ]
    assert all(item["reason"] in TARGET_FAILURE_REASONS for item in normalized_failures)
    assert normalized_failures == sorted(normalized_failures, key=canonical_json_bytes)
    assert len({item["target_key"] for item in normalized_failures}) == len(normalized_failures)
    return {
        "actual": None,
        "resolved": context["budget_resolved"],
        "allowed": False,
        "payload_available": False,
        "original_outcome": "payload_unavailable",
        "outcome": "payload_unavailable",
        "diagnostic_code": "CSV-NEXT-TARGET-001",
        "run_context": context,
        "requested_formats": context["requested_formats"],
        "budget_requested": context["budget_requested"],
        "budget_source": context["budget_source"],
        "stdout_selector": context["stdout_selector"],
        "artifact_paths": [],
        "target_failures": normalized_failures,
    }


def export_reexport_failure_rows(proof: dict[str, Any]) -> list[dict[str, Any]]:
    """Select fail-closed cycle/conflict rows from the validated graph witness."""

    rows = [
        {
            "syntax_identity": witness["syntax_identity"],
            "original_exported_name": witness["original_exported_name"],
            "exported_name": witness["exported_name"],
            "diagnostic": witness["diagnostic"],
        }
        for witness in proof["export_reexport_witness"]
        if witness["diagnostic"] in {"cycle", "conflict"}
    ]
    rows.sort(key=canonical_json_bytes)
    return rows


def export_failure_decision(
    proof: dict[str, Any], run_context: NextRunContext
) -> dict[str, Any] | None:
    """Project graph cycle/conflict evidence to a stable unavailable outcome."""

    failures = export_reexport_failure_rows(proof)
    if not failures:
        return None
    context = canonical_run_context(**run_context)
    return {
        "actual": None,
        "resolved": context["budget_resolved"],
        "allowed": False,
        "payload_available": False,
        "original_outcome": "payload_unavailable",
        "outcome": "payload_unavailable",
        "diagnostic_code": "CSV-NEXT-EXPORT-001",
        "run_context": context,
        "requested_formats": context["requested_formats"],
        "budget_requested": context["budget_requested"],
        "budget_source": context["budget_source"],
        "stdout_selector": context["stdout_selector"],
        "artifact_paths": [],
        "export_failures": failures,
    }


def derive_pre_budget_outcome(proof: dict[str, Any], model: dict[str, Any]) -> str:
    """Derive status from the closed proof-reason semantics.

    Selection bookkeeping (``not_selected`` and ``target_excluded``) and an
    intentionally unknown unsupported frontier do not imply information loss.
    Only a localized taint/failure or an already partial semantic diagnostic
    lowers the outcome; entity over-budget is owned by the later Python gate.
    """

    _validate_proof_reason_semantics(proof, model)
    if (
        proof["failure_roots"]
        or any(item["reason"] in {"tainted", "failed"} for item in proof["excluded"])
        or proof["failed"]
    ):
        return "partial_safe"
    if any(diagnostic["outcome"] == "partial_safe" for diagnostic in model["diagnostics"]):
        return "partial_safe"
    return "complete"


def classify_source_failure(*, localized: bool, safe_subset_proven: bool) -> dict[str, Any]:
    """Close the source failure boundary before semantic projection.

    `SOURCE-001` is reserved for a proven local omission.  Any source failure
    that can affect an unbounded dependency or target set is a typed
    `SOURCE-003` unavailable result; it must not be downgraded to a misleading
    partial snapshot.
    """

    if localized and safe_subset_proven:
        return {
            "diagnostic_code": "CSV-NEXT-SOURCE-001",
            "outcome": "partial_safe",
            "payload_available": True,
            "exit_code": 3,
        }
    return {
        "diagnostic_code": "CSV-NEXT-SOURCE-003",
        "outcome": "payload_unavailable",
        "payload_available": False,
        "exit_code": 3,
    }


def _validate_proof_reason_semantics(proof: dict[str, Any], model: dict[str, Any]) -> None:
    """Keep proof dispositions and outcome ownership mutually reachable."""

    excluded_reasons = {item["reason"] for item in proof["excluded"]}
    failed_reasons = {item["reason"] for item in proof["failed"]}
    assert "over_budget" not in excluded_reasons
    assert "over_budget" not in failed_reasons
    if "unsupported" in excluded_reasons:
        assert any(
            diagnostic["code"] == "CSV-NEXT-UNSUPPORTED-001" and diagnostic["outcome"] == "complete"
            for diagnostic in model["diagnostics"]
        )
        coverage = model.get("coverage")
        if isinstance(coverage, dict):
            assert coverage.get("unknown_relation_count", 0) >= 1
    lowers_outcome = bool(proof["failure_roots"] or failed_reasons or "tainted" in excluded_reasons)
    if lowers_outcome:
        # A reason alone is not locality proof.  At least one immutable failure
        # root must witness the bounded region that is being omitted.
        roots = proof["failure_roots"]
        assert roots
        assert all(isinstance(root, dict) and root.get("id") for root in roots)


def _with_validated_decision(
    projection: dict[str, Any],
    *,
    model: dict[str, Any],
    proof: dict[str, Any],
    run_context: NextRunContext,
    pre_budget_outcome: str,
    request: dict[str, Any],
    targets: list[str] | tuple[str, ...] = (),
    target_failures: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
    export_failures: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
) -> dict[str, Any]:
    """Attach the sole immutable downstream authority to a decision projection."""

    gate = {
        key: copy.deepcopy(projection[key])
        for key in (
            "actual",
            "resolved",
            "allowed",
            "payload_available",
            "original_outcome",
            "outcome",
            "diagnostic_code",
            "run_context",
            "requested_formats",
            "budget_requested",
            "budget_source",
            "stdout_selector",
            "artifact_paths",
        )
        if key in projection
    }
    gate["resolved_limits"] = copy.deepcopy(request["limits"])
    canonical_targets = tuple(canonical_target_key(target) for target in request["targets"])
    assert tuple(canonical_target_key(target) for target in targets) == canonical_targets
    publication_context = _publication_context_from_request(
        request,
        run_context,
        toolchain=_toolchain_snapshot(),
        trusted_environment=_trusted_environment_snapshot(),
        projects_for_fingerprint=copy.deepcopy(model["projects"]),
    )
    projection["validated_decision"] = NextValidatedDecision(
        validated_model=model,
        validated_proof=proof,
        run_context=run_context,
        pre_budget_outcome=pre_budget_outcome,
        gate=gate,
        targets=tuple(targets),
        target_failures=tuple(target_failures),
        export_failures=tuple(export_failures),
        request=request,
        publication_context=publication_context,
    )
    return projection


def validate_response_envelope(
    response_bytes: bytes,
    request: dict[str, Any],
) -> dict[str, Any]:
    """Validate one adapter response only after bounded raw-byte decoding."""

    bounded = bounded_decode_json(response_bytes, limits=request["limits"])
    assert bounded["allowed"]
    response = cast(dict[str, Any], bounded["value"])
    _validate_closed_response_schema(response)
    model = response["model"]
    target_failure = target_completeness_failure(model, request["targets"])
    allowed_missing_module_keys, allowed_missing_module_ids = _target_missing_module_exceptions(
        model,
        request["targets"],
        target_failure,
    )
    allowed_duplicate_module_keys = _target_duplicate_module_exceptions(
        model,
        request["targets"],
        target_failure,
    )
    _validate_response_base(
        response,
        allowed_missing_module_keys=allowed_missing_module_keys,
        allowed_missing_module_ids=allowed_missing_module_ids,
        allowed_duplicate_module_keys=allowed_duplicate_module_keys,
    )
    assert response["protocol"] == request["protocol"] == "code-structure-viz.next-adapter/v1"
    assert response["request_id"] == request["request_id"]
    assert response["adapter_version"] == request["adapter_version"]
    assert response["model_digest"] == digest(response["model"])
    validate_compatibility_descriptor(response["compatibility_descriptor"])
    assert (
        response["semantic_compatibility_id"]
        == response["compatibility_descriptor"]["compatibility_id"]
    )
    assert (
        response["identity_versions"] == response["compatibility_descriptor"]["identity_versions"]
    )
    assert (
        response["trusted_type_environment_digest"] == request["trusted_type_environment"]["sha256"]
    )
    validate_limits_consistency(request["limits"], response["limits"])
    request_context = canonical_run_context(**request["run_context"])
    run_context = canonical_run_context(**response["run_context"])
    assert run_context == request_context
    _validate_project_correspondence(request["projects"], model["projects"])
    request_files = [
        {key: item for key, item in file_record.items() if key != "content_base64"}
        for file_record in request["files"]
    ]
    assert model["files"] == request_files
    if target_failure is not None:
        _validate_target_exception_proof_base(
            response["proof"], model, request["targets"], target_failure
        )
        decision = target_failure_decision(target_failure, run_context)
        decision["validated_model"] = copy.deepcopy(model)
        return _with_validated_decision(
            decision,
            model=model,
            proof=response["proof"],
            run_context=run_context,
            pre_budget_outcome="payload_unavailable",
            request=request,
            targets=request["targets"],
            target_failures=target_failure.failures,
        )
    actual_entities = validate_model(
        model,
        max_model_records=request["limits"]["max_model_records"],
    )
    validate_proof(response["proof"], model, request_targets=request["targets"])
    export_failure = export_failure_decision(response["proof"], run_context)
    if export_failure is not None:
        export_failure["validated_model"] = copy.deepcopy(model)
        export_failure["validated_proof"] = copy.deepcopy(response["proof"])
        return _with_validated_decision(
            export_failure,
            model=model,
            proof=response["proof"],
            run_context=run_context,
            pre_budget_outcome="payload_unavailable",
            request=request,
            targets=request["targets"],
            export_failures=export_failure["export_failures"],
        )
    pre_budget_outcome = derive_pre_budget_outcome(response["proof"], model)
    decision = entity_budget_gate(
        actual_entities,
        original_outcome=pre_budget_outcome,
        run_context=run_context,
    )
    decision["validated_model"] = copy.deepcopy(model)
    decision["validated_proof"] = copy.deepcopy(response["proof"])
    return _with_validated_decision(
        decision,
        model=model,
        proof=response["proof"],
        run_context=run_context,
        pre_budget_outcome=pre_budget_outcome,
        request=request,
        targets=request["targets"],
    )


def recompute_run_fingerprint(
    *,
    source_view_fingerprint: str,
    source_plan_digest: str,
    domain_config_digest: str,
    projects: list[dict[str, Any]],
    targets: list[str],
    formats: list[str] | tuple[str, ...],
    stdout_selector: str | None,
    limits: dict[str, Any],
    node_version: str | None,
    typescript_version: str,
    adapter_version: str,
    protocol: str,
    trusted_environment_digest: str,
    identifier_unicode_version: str = ECMASCRIPT_IDENTIFIER_UNICODE_VERSION,
    identifier_unicode_table_digest: str = ECMASCRIPT_IDENTIFIER_UNICODE_TABLE_DIGEST,
) -> str:
    return digest(
        {
            "source_view_fingerprint": source_view_fingerprint,
            "source_plan_digest": source_plan_digest,
            "domain_config_digest": domain_config_digest,
            "projects": projects,
            "targets": targets,
            "formats": list(formats),
            "stdout_selector": stdout_selector,
            "limits": limits,
            "node_version": node_version,
            "typescript_version": typescript_version,
            "adapter_version": adapter_version,
            "protocol": protocol,
            "trusted_environment_digest": trusted_environment_digest,
            "identifier_unicode_version": identifier_unicode_version,
            "identifier_unicode_table_digest": identifier_unicode_table_digest,
        }
    )


def recompute_publication_projection_digest(domain: dict[str, Any]) -> str:
    """Hash the complete validated publication input, not a count proxy."""

    decision = getattr(domain, "validated_decision", None)
    model = decision.validated_model if isinstance(decision, NextValidatedDecision) else None
    return digest(
        {
            "model": model
            if isinstance(model, dict)
            else {
                "projects": domain["projects"],
                "coverage": domain["coverage"],
            },
            "targets": domain["targets"],
            "formats": domain["formats"],
            "run_context": domain["run_context"],
            "run_fingerprint": domain["run_fingerprint"],
        }
    )


def validate_published_projection(
    domain: dict[str, Any], published_bytes: dict[str, bytes]
) -> None:
    """Validate actual semantic/PlantUML bytes from the accepted model."""

    decision = getattr(domain, "validated_decision", None)
    if isinstance(decision, (PreResponseFailureDecision, NotApplicableDecision)):
        assert published_bytes == {}
        assert domain["artifact_paths"] == []
        return
    assert isinstance(decision, NextValidatedDecision), "publication has no validated decision"
    model = decision.validated_model
    expected_entities = [*model["modules"], *model["components"]]
    for path, payload in published_bytes.items():
        if path.endswith(".json"):
            value = json.loads(payload.decode("utf-8"))
            validate_semantic_snapshot(value)
            assert value["projects"] == sorted(
                model["projects"], key=lambda item: canonical_json_bytes(item["root"])
            )
            assert value["files"] == model["files"]
            assert value["entities"] == expected_entities
            assert value["members"] == model["members"]
            assert value["relations"] == model["relations"]
            assert value["facts"] == model["facts"]
            assert value["coverage"] == model["coverage"]
            assert value["request"] == domain["request"]
            assert value["source"] == domain["source"]
        else:
            validate_plantuml_contract(
                payload,
                model,
                status="partial_safe" if domain["status"] == "incomplete" else "complete",
            )


def validate_domain_manifest(value: dict[str, Any]) -> None:
    assert value["domain"] == "next"
    run_context = canonical_run_context(**value["run_context"])
    assert run_context["requested_formats"] == value["formats"]
    assert run_context["budget_resolved"] == value["budget"]["resolved"]
    assert run_context["budget_requested"] == value["budget"]["requested"]
    assert run_context["budget_source"] == value["budget"]["source"]
    validate_compatibility_descriptor(value["compatibility_descriptor"])
    assert (
        value["semantic_compatibility_id"] == value["compatibility_descriptor"]["compatibility_id"]
    )
    validate_limits_consistency(value["limits"], value["config"]["limits"])
    validate_trusted_environment(value["trusted_environment"])
    _validate_public_diagnostics(value["diagnostics"])
    node = value["toolchain"]["node"]
    if value["status"] == "not_applicable":
        assert node == {"status": "not_applicable", "version": None, "failure_kind": None}
        assert value["toolchain"]["node_version"] is None
    elif value["status"] == "incomplete" and value["incomplete_kind"] == "payload_unavailable":
        if node["status"] == "unavailable":
            assert node["version"] is None
            assert node["failure_kind"] in {
                "missing",
                "unsupported_version",
                "spawn_failed",
                "timeout",
                "process_failed",
            }
            assert value["toolchain"]["node_version"] is None
        else:
            assert node["status"] == "available"
            assert node["version"] == value["toolchain"]["node_version"]
            assert node["failure_kind"] is None
    else:
        assert node["status"] == "available"
        assert node["version"] == value["toolchain"]["node_version"]
        assert node["failure_kind"] is None
        assert value["toolchain"]["node_version"] is not None
    if value["status"] == "complete":
        allowed_outcomes = {"complete"}
        assert value["budget"]["outcome"] == "complete"
    elif value["status"] == "not_applicable":
        allowed_outcomes = {"not_applicable"}
        assert value["budget"]["outcome"] == "not_applicable"
    else:
        allowed_outcomes = {value["incomplete_kind"]}
        assert value["budget"]["outcome"] == value["incomplete_kind"]
    assert {diagnostic["outcome"] for diagnostic in value["diagnostics"]} <= allowed_outcomes
    assert value["config"]["trusted_environment_digest"] == value["trusted_environment"]["sha256"]
    assert value["config"]["domain_config_digest"] == resolved_config_digest(value["config"])
    assert value["config"]["domain_config_digest"] == value["domain_config_digest"]
    assert value["config"]["source_plan_digest"] == value["source_plan_digest"]
    assert value["config"]["source_plan"] == source_plan_descriptor(value["config"])
    assert value["request"]["source_plan"] == value["config"]["source_plan"]
    assert value["config"]["source_plan_digest"] == source_plan_digest(value["config"])
    project_records = _assert_sorted_unique(value["projects"], "projects")
    roots: list[tuple[str, str]] = []
    for project in project_records.values():
        assert project["kind"] == "project"
        assert project["config_digest"] == project_config_digest(project)
        _assert_path(project["root"])
        for other_root, other_id in roots:
            assert not _under(project["root"], other_root)
            assert not _under(other_root, project["root"])
            assert project["id"] != other_id
        roots.append((project["root"], project["id"]))
        assert project["source_roots"] == sorted(project["source_roots"])
        assert len(project["source_roots"]) == len(set(project["source_roots"]))
        for source_root in project["source_roots"]:
            _assert_path(source_root)
            assert _under(source_root, project["root"])
        if project["config_path"] is not None:
            _assert_file_path(project["config_path"])
            assert _under(project["config_path"], project["root"])
        assert project["file_ids"] == sorted(set(project["file_ids"]))
        assert all(_id_kind(file_id) == "file" for file_id in project["file_ids"])
    assert value["source"]["file_count"] == sum(
        len(project["file_ids"]) for project in value["projects"]
    )
    expected_config_projects = sorted(
        [
            {
                "root": project["root"],
                "source_roots": project["source_roots"],
                "config_path": project["config_path"],
                "compiler_options": project["compiler_options"],
            }
            for project in value["projects"]
        ],
        key=lambda project: canonical_json_bytes(project["root"]),
    )
    assert [project["root"] for project in expected_config_projects] == sorted(
        project["root"] for project in value["projects"]
    )
    assert value["config"]["projects"] == expected_config_projects
    assert value["request"]["projects"] == expected_config_projects
    assert value["request"]["targets"] == value["targets"]
    assert value["config"]["targets"] == value["targets"]
    assert value["config"]["formats"] == value["formats"]
    assert value["config"]["upstream_depth"] == value["request"]["upstream_depth"]
    assert value["config"]["downstream_depth"] == value["request"]["downstream_depth"]
    _assert_target_keys(value["targets"])
    _assert_formats(value["formats"])
    assert value["request"]["formats"] == value["formats"]
    assert value["request"]["limits"] == value["limits"]
    assert value["request"]["trusted_environment_digest"] == value["trusted_environment"]["sha256"]
    assert value["request"]["source_plan_digest"] == value["source_plan_digest"]
    assert value["request"]["domain_config_digest"] == value["domain_config_digest"]
    assert value["request"]["run_fingerprint"] == value["run_fingerprint"]
    coverage_internal_entities = value["coverage"]["counts"]["internal_entities"]
    assert value["budget"]["resolved"] == value["limits"]["max_entities"]
    target_completeness = value["coverage"]["target_completeness"]
    _assert_canonical(target_completeness)
    target_rows = {item["target_key"]: item for item in target_completeness}
    assert set(target_rows) == set(value["targets"])
    assert all(item["record_ids"] == sorted(item["record_ids"]) for item in target_completeness)
    for item in target_completeness:
        if item["status"] == "failed":
            # Typed program File→Module failures carry the closed reason
            # vocabulary.  A direct context/control-file rejection (for
            # example `.d.ts`) is a separate target-classification failure
            # and intentionally has no typed cardinality reason.
            reason = item.get("reason")
            assert reason is None or reason in TARGET_FAILURE_REASONS
        else:
            assert "reason" not in item
    failed_targets = [item for item in target_completeness if item["status"] == "failed"]
    assert all(not item["record_ids"] for item in failed_targets)
    if failed_targets:
        assert value["status"] == "incomplete"
        assert value["incomplete_kind"] == "payload_unavailable"
        assert value["payload_available"] is False
        assert value["artifact_paths"] == []
        assert any(
            diagnostic["code"] == "CSV-NEXT-TARGET-001" for diagnostic in value["diagnostics"]
        )
    expected_artifacts = {
        "semantic-json": "next.snapshot.semantic.json",
        "plantuml": "next.snapshot.puml",
    }
    if value["status"] == "not_applicable":
        assert value["payload_available"] is False
        assert value["entity_count"] == 0
        assert "incomplete_kind" not in value
        assert value["artifact_paths"] == []
        assert value["diagnostics"]
    elif value["status"] == "complete":
        assert value["payload_available"] is True
        assert "incomplete_kind" not in value
        assert value["entity_count"] is not None
        assert value["artifact_paths"] == [expected_artifacts[fmt] for fmt in value["formats"]]
    else:
        assert value["status"] == "incomplete"
        assert value["incomplete_kind"] in {"partial_safe", "payload_unavailable"}
        if value["incomplete_kind"] == "partial_safe":
            assert value["payload_available"] is True
            assert value["entity_count"] is not None
            assert value["artifact_paths"] == [expected_artifacts[fmt] for fmt in value["formats"]]
        else:
            assert value["payload_available"] is False
            assert value["entity_count"] is None
            assert value["artifact_paths"] == []
        assert value["diagnostics"]
    if value["budget"]["actual"] is not None:
        assert value["budget"]["actual"] == coverage_internal_entities
        if value["budget"]["actual"] > value["budget"]["resolved"]:
            assert value["status"] == "incomplete"
            assert value["incomplete_kind"] == "payload_unavailable"
            assert value["payload_available"] is False
            assert value["entity_count"] is None
            assert value["artifact_paths"] == []
            assert any(
                diagnostic["code"] == "CSV-NEXT-LIMIT-005" for diagnostic in value["diagnostics"]
            )
        elif value["payload_available"]:
            assert value["entity_count"] == value["budget"]["actual"]
            assert coverage_internal_entities == value["entity_count"]
    assert value["run_fingerprint"] == recompute_run_fingerprint(
        source_view_fingerprint=value["source"]["fingerprint"],
        source_plan_digest=value["source_plan_digest"],
        domain_config_digest=value["domain_config_digest"],
        projects=value["projects"],
        targets=value["targets"],
        formats=run_context["requested_formats"],
        stdout_selector=run_context["stdout_selector"],
        limits=value["limits"],
        node_version=value["toolchain"]["node_version"],
        typescript_version=value["toolchain"]["typescript_version"],
        adapter_version=value["toolchain"]["adapter_version"],
        protocol=value["toolchain"]["protocol"],
        trusted_environment_digest=value["trusted_environment"]["sha256"],
    )


def validate_compatibility_descriptor(descriptor: dict[str, Any]) -> None:
    assert descriptor["schema"] == "code-structure-viz.next-semantic-compatibility/v1"
    assert descriptor["semantic_schema"] == "code-structure-viz.semantic/v1"
    assert descriptor["semantic_profile_id"] == "next-trusted-profile-v1"
    assert descriptor["identity_versions"] == {
        "project": 1,
        "file": 1,
        "module": 1,
        "component": 1,
        "member": 1,
        "relation": 1,
        "fact": 1,
        "props_ir": 1,
    }
    assert descriptor["algorithm_versions"] == {
        "recognition": 1,
        "export": 1,
        "props": 1,
        "relation": 1,
        "fact": 1,
        "boundary": 1,
        "identifier_unicode": ECMASCRIPT_IDENTIFIER_UNICODE_VERSION,
        "identifier_unicode_table_digest": ECMASCRIPT_IDENTIFIER_UNICODE_TABLE_DIGEST,
    }
    assert descriptor["compatibility_id"] == recompute_compatibility_id(descriptor)


def validate_limits(limits: dict[str, Any]) -> None:
    assert set(limits) == {"max_entities", *LIMIT_DEFAULTS}
    assert 1 <= limits["max_entities"] <= 100000
    for name, expected in LIMIT_DEFAULTS.items():
        assert limits[name] == expected, name
    # ``max_stdout_bytes`` is the historical public alias.  Keeping it equal
    # to the explicit selected-artifact bound avoids two authorities while
    # allowing old v1 request fixtures to remain readable.
    assert limits["max_stdout_bytes"] == limits["max_selected_stdout_bytes"]
    validate_limit_contracts()


def validate_limit_contracts() -> None:
    """Ensure every resolved limit has a closed measurement contract."""

    assert set(LIMIT_CONTRACTS) == {"max_entities", *LIMIT_DEFAULTS}
    for contract in LIMIT_CONTRACTS.values():
        assert set(contract) == {"unit", "measurement", "encoding", "inclusive", "outcome"}
        assert contract["unit"]
        assert contract["measurement"]
        assert contract["encoding"] in {"utf8", "not_applicable"}
        assert contract["inclusive"] is True
        assert contract["outcome"] in {"partial_safe", "payload_unavailable"}


def limit_boundary_allowed(limit: int, measured: int) -> bool:
    """Model an inclusive non-negative counter boundary without allocation."""

    return measured >= 0 and measured <= limit


def internal_entity_count(model: dict[str, Any]) -> int:
    """Count only published internal Module and Component records."""

    return len(model["modules"]) + len(model["components"])


def entity_budget_allowed(measured: int, resolved: int) -> bool:
    """Apply the inclusive max_entities boundary to internal entities."""

    return measured >= 0 and resolved >= 1 and measured <= resolved


def entity_budget_gate(
    measured: int,
    *,
    original_outcome: str,
    run_context: NextRunContext,
) -> dict[str, Any]:
    """Compose the entity gate without upgrading a pre-budget outcome.

    ``original_outcome`` is derived before the publication gate (for example
    ``partial_safe`` when a bounded type traversal lost detail).  The gate is
    allowed to make a payload unavailable, but it must never turn a safe
    partial result into a complete result merely because the entity count fits.
    """

    assert original_outcome in {"complete", "partial_safe"}
    context = canonical_run_context(**run_context)
    formats = context["requested_formats"]
    expected_artifacts = {
        "semantic-json": "next.snapshot.semantic.json",
        "plantuml": "next.snapshot.puml",
    }
    resolved = context["budget_resolved"]
    allowed = entity_budget_allowed(measured, resolved)
    outcome = original_outcome if allowed else "payload_unavailable"
    return {
        "actual": measured,
        "resolved": resolved,
        "allowed": allowed,
        "payload_available": allowed,
        "original_outcome": original_outcome,
        "outcome": outcome,
        "diagnostic_code": None if allowed else "CSV-NEXT-LIMIT-005",
        "run_context": context,
        "requested_formats": formats,
        "budget_requested": context["budget_requested"],
        "budget_source": context["budget_source"],
        "stdout_selector": context["stdout_selector"],
        "artifact_paths": [expected_artifacts[format_name] for format_name in formats]
        if allowed
        else [],
    }


def compose_entity_budget_outcome(
    measured: int,
    *,
    original_outcome: str,
    run_context: NextRunContext,
) -> dict[str, Any]:
    """Return the manifest-facing status fields produced by EntityBudgetGate."""

    return entity_budget_gate(
        measured,
        original_outcome=original_outcome,
        run_context=run_context,
    )


def total_array_items_allowed(measured: int, resolved: int) -> bool:
    """Apply the aggregate JSON-array item boundary without materialization."""

    return 0 <= measured <= resolved


def count_array_items_before_materialization(
    array_lengths: list[int],
    *,
    max_array_items: int = LIMIT_DEFAULTS["max_array_items"],
    max_total_array_items: int = LIMIT_DEFAULTS["max_total_array_items"],
) -> dict[str, Any]:
    """Count nested arrays incrementally and stop before an over-limit append."""

    total = 0
    for index, length in enumerate(array_lengths):
        assert length >= 0
        if length > max_array_items:
            return {
                "allowed": False,
                "total": total + length,
                "failed_at": index,
                "reason": "max_array_items",
            }
        total += length
        if not total_array_items_allowed(total, max_total_array_items):
            return {
                "allowed": False,
                "total": total,
                "failed_at": index,
                "reason": "max_total_array_items",
            }
    return {"allowed": True, "total": total, "failed_at": None, "reason": None}


class _BoundedJsonDecodeFailure(Exception):
    """Internal early-exit marker for the streaming JSON contract."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class _BoundedJsonDecoder:
    """Bound a raw JSON response before constructing its Python object."""

    def __init__(self, payload: bytes, limits: dict[str, int]) -> None:
        self.payload = payload
        self.limits = limits
        self.index = 0
        self.total_array_items = 0
        self.array_count = 0
        self.max_array_items = 0
        self.max_nesting = 0
        self.max_string_bytes = 0

    def _fail(self, reason: str) -> None:
        raise _BoundedJsonDecodeFailure(reason)

    def _skip_whitespace(self) -> None:
        while self.index < len(self.payload) and self.payload[self.index] in b" \t\r\n":
            self.index += 1

    def _scan_string(self) -> tuple[int, int]:
        """Scan one JSON string and count decoded UTF-8 bytes incrementally."""

        assert self.payload[self.index] == ord('"')
        self.index += 1
        decoded_bytes = 0
        hex_digits = b"0123456789abcdefABCDEF"
        while self.index < len(self.payload):
            byte = self.payload[self.index]
            if byte == ord('"'):
                self.index += 1
                return self.index, decoded_bytes
            if byte < 0x20:
                self._fail("invalid_json")
            if byte == ord("\\"):
                self.index += 1
                if self.index >= len(self.payload):
                    self._fail("invalid_json")
                escape = self.payload[self.index]
                if escape in b'"\\/bfnrt':
                    decoded_bytes += 1
                    self.index += 1
                    continue
                if escape != ord("u"):
                    self._fail("invalid_json")
                if self.index + 4 >= len(self.payload):
                    self._fail("invalid_json")
                digits = self.payload[self.index + 1 : self.index + 5]
                if any(digit not in hex_digits for digit in digits):
                    self._fail("invalid_json")
                codepoint = int(digits.decode("ascii"), 16)
                self.index += 5
                if 0xD800 <= codepoint <= 0xDBFF:
                    # JSON requires a high surrogate to be followed by a
                    # second escaped low surrogate.  Count the combined code
                    # point without constructing the decoded string.
                    if self.payload[self.index : self.index + 2] != b"\\u":
                        self._fail("invalid_json")
                    if self.index + 6 > len(self.payload):
                        self._fail("invalid_json")
                    low_digits = self.payload[self.index + 2 : self.index + 6]
                    if any(digit not in hex_digits for digit in low_digits):
                        self._fail("invalid_json")
                    low = int(low_digits.decode("ascii"), 16)
                    if not 0xDC00 <= low <= 0xDFFF:
                        self._fail("invalid_json")
                    self.index += 6
                    decoded_bytes += len(
                        chr(0x10000 + ((codepoint - 0xD800) << 10) + low - 0xDC00).encode("utf-8")
                    )
                elif 0xDC00 <= codepoint <= 0xDFFF:
                    self._fail("invalid_json")
                else:
                    decoded_bytes += len(chr(codepoint).encode("utf-8"))
                continue
            if byte < 0x80:
                decoded_bytes += 1
                self.index += 1
                continue
            if 0xC2 <= byte <= 0xDF:
                width = 2
            elif 0xE0 <= byte <= 0xEF:
                width = 3
            elif 0xF0 <= byte <= 0xF4:
                width = 4
            else:
                self._fail("invalid_json")
            sequence = self.payload[self.index : self.index + width]
            if len(sequence) != width or any((item & 0xC0) != 0x80 for item in sequence[1:]):
                self._fail("invalid_json")
            try:
                sequence.decode("utf-8")
            except UnicodeDecodeError:
                self._fail("invalid_json")
            decoded_bytes += width
            self.index += width
        self._fail("invalid_json")
        raise AssertionError("unreachable")

    def _parse_string(self, *, materialize: bool) -> str | None:
        """Scan a string before its value is materialized.

        Object keys are materialized only after their decoded size has passed
        the bound because duplicate-key detection needs the key value.  JSON
        values remain byte-only during the structural pass; the complete
        object is decoded once, after every bound has passed.
        """

        start = self.index
        end, decoded_bytes = self._scan_string()
        self.max_string_bytes = max(self.max_string_bytes, decoded_bytes)
        if decoded_bytes > self.limits["max_json_string_bytes"]:
            self._fail("max_json_string_bytes")
        if not materialize:
            return None
        try:
            value = json.loads(self.payload[start:end].decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._fail("invalid_json")
        assert isinstance(value, str)
        return value

    def _parse_number_or_literal(self) -> None:
        start = self.index
        while self.index < len(self.payload) and self.payload[self.index] not in b" \t\r\n,]}:":
            self.index += 1
        if start == self.index:
            self._fail("invalid_json")
        token = self.payload[start : self.index]
        try:
            value = json.loads(
                token.decode("ascii"),
                parse_constant=lambda _constant: (_ for _ in ()).throw(ValueError),
            )
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
            self._fail("invalid_json")
        assert value is None or isinstance(value, (bool, int, float))

    def _parse_value(self, depth: int) -> None:
        self.max_nesting = max(self.max_nesting, depth)
        if depth > self.limits["max_json_nesting"]:
            self._fail("max_json_nesting")
        self._skip_whitespace()
        if self.index >= len(self.payload):
            self._fail("invalid_json")
        byte = self.payload[self.index]
        if byte == ord('"'):
            self._parse_string(materialize=False)
            return
        if byte == ord("{"):
            self._parse_object(depth)
            return
        if byte == ord("["):
            self._parse_array(depth)
            return
        self._parse_number_or_literal()

    def _parse_object(self, depth: int) -> None:
        self.index += 1
        keys: set[str] = set()
        self._skip_whitespace()
        if self.index < len(self.payload) and self.payload[self.index] == ord("}"):
            self.index += 1
            return
        while True:
            self._skip_whitespace()
            if self.index >= len(self.payload) or self.payload[self.index] != ord('"'):
                self._fail("invalid_json")
            key = self._parse_string(materialize=True)
            assert key is not None
            if key in keys:
                self._fail("duplicate_object_key")
            keys.add(key)
            self._skip_whitespace()
            if self.index >= len(self.payload) or self.payload[self.index] != ord(":"):
                self._fail("invalid_json")
            self.index += 1
            self._parse_value(depth + 1)
            self._skip_whitespace()
            if self.index >= len(self.payload):
                self._fail("invalid_json")
            delimiter = self.payload[self.index]
            if delimiter == ord("}"):
                self.index += 1
                return
            if delimiter != ord(","):
                self._fail("invalid_json")
            self.index += 1

    def _parse_array(self, depth: int) -> None:
        self.index += 1
        self.array_count += 1
        length = 0
        self._skip_whitespace()
        if self.index < len(self.payload) and self.payload[self.index] == ord("]"):
            self.index += 1
            return
        while True:
            length += 1
            self.max_array_items = max(self.max_array_items, length)
            if length > self.limits["max_array_items"]:
                self._fail("max_array_items")
            self.total_array_items += 1
            if self.total_array_items > self.limits["max_total_array_items"]:
                self._fail("max_total_array_items")
            self._parse_value(depth + 1)
            self._skip_whitespace()
            if self.index >= len(self.payload):
                self._fail("invalid_json")
            delimiter = self.payload[self.index]
            if delimiter == ord("]"):
                self.index += 1
                return
            if delimiter != ord(","):
                self._fail("invalid_json")
            self.index += 1

    def decode(self) -> dict[str, Any]:
        try:
            self._parse_value(0)
            self._skip_whitespace()
            if self.index != len(self.payload):
                self._fail("invalid_json")

            # The structural pass above is the trust-boundary gate.  Only
            # after duplicate keys, nesting, string bytes, and array counts
            # have passed do we materialize the response used by the schema
            # and envelope validator.  ``object_pairs_hook`` keeps this
            # invariant explicit even if the scanner is changed later.
            def reject_duplicate_keys(
                pairs: list[tuple[str, Any]],
            ) -> dict[str, Any]:
                value: dict[str, Any] = {}
                for key, item in pairs:
                    if key in value:
                        self._fail("duplicate_object_key")
                    value[key] = item
                return value

            value = json.loads(self.payload, object_pairs_hook=reject_duplicate_keys)
            if not isinstance(value, dict):
                self._fail("response_not_object")
        except _BoundedJsonDecodeFailure as failure:
            return {
                "allowed": False,
                "bytes": len(self.payload),
                "total_array_items": self.total_array_items,
                "array_count": self.array_count,
                "max_array_items": self.max_array_items,
                "max_nesting": self.max_nesting,
                "max_string_bytes": self.max_string_bytes,
                "failed_at_byte": self.index,
                "reason": failure.reason,
                "materialized": False,
            }
        except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
            return {
                "allowed": False,
                "bytes": len(self.payload),
                "total_array_items": self.total_array_items,
                "array_count": self.array_count,
                "max_array_items": self.max_array_items,
                "max_nesting": self.max_nesting,
                "max_string_bytes": self.max_string_bytes,
                "failed_at_byte": self.index,
                "reason": "invalid_json",
                "materialized": False,
            }
        return {
            "allowed": True,
            "bytes": len(self.payload),
            "total_array_items": self.total_array_items,
            "array_count": self.array_count,
            "max_array_items": self.max_array_items,
            "max_nesting": self.max_nesting,
            "max_string_bytes": self.max_string_bytes,
            "failed_at_byte": None,
            "reason": None,
            "materialized": True,
            "value": value,
        }


def bounded_decode_json(
    response: bytes,
    *,
    limits: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Decode only raw response bytes through the bounded trust boundary."""

    assert isinstance(response, bytes)
    payload = response
    resolved_limits = {**LIMIT_DEFAULTS, **(limits or {})}
    # This is the sole raw-response entry point.  Measure the complete byte
    # stream before UTF-8 decoding, parser construction, or object
    # materialization so whitespace-only padding cannot evade the private
    # adapter-response limit.
    response_limit = resolved_limits.get(
        "max_adapter_response_bytes", resolved_limits["max_stdout_bytes"]
    )
    if len(payload) > response_limit:
        return {
            "allowed": False,
            "bytes": len(payload),
            "total_array_items": 0,
            "array_count": 0,
            "max_array_items": 0,
            "max_nesting": 0,
            "max_string_bytes": 0,
            "failed_at_byte": response_limit,
            # Keep the historical decoder reason as a wire-compatibility
            # label; the selected limit is resolved above by name.
            "reason": "max_stdout_bytes",
            "materialized": False,
        }
    for name in (
        "max_json_nesting",
        "max_json_string_bytes",
        "max_array_items",
        "max_total_array_items",
    ):
        assert isinstance(resolved_limits[name], int)
        assert resolved_limits[name] >= 1
    return _BoundedJsonDecoder(payload, resolved_limits).decode()


def response_boundary_decision(response_bytes: bytes, request: dict[str, Any]) -> NextRunDecision:
    """Return one closed decision for every response-boundary failure.

    A real adapter response is never routed directly to a domain projection:
    raw-byte/decode failures become a pre-response decision, while a
    schema/proof/reference failure is classified as protocol failure before
    the same decision is projected.  A valid response returns the immutable
    decision created by :func:`validate_response_envelope`.
    """

    bounded = bounded_decode_json(response_bytes, limits=request["limits"])
    if not bounded["allowed"]:
        reason = bounded["reason"]
        classification = classify_response_limit(
            raw_bytes=bounded["bytes"],
            aggregate_array_items=bounded["total_array_items"],
            model_records=0,
            limits=request["limits"],
        )
        code = classification["diagnostic_code"] or "CSV-NEXT-PROTOCOL-001"
        stage = classification["stage"] or (
            "response_raw_bytes" if reason == "max_stdout_bytes" else "response_decode"
        )
        return pre_response_failure_decision(
            request,
            stage=stage,
            diagnostic_code=code,
            stdout_bytes=bounded["bytes"],
        )
    decoded = bounded["value"]
    if isinstance(decoded, dict):
        model = decoded.get("model")
        proof = decoded.get("proof")
        published_model_records, proof_only_records, discovered_records = (
            response_model_record_counts(model, proof)
            if isinstance(model, dict) and isinstance(proof, dict)
            else (0, 0, 0)
        )
        classification = classify_response_limit(
            raw_bytes=bounded["bytes"],
            aggregate_array_items=bounded["total_array_items"],
            model_records=published_model_records,
            proof_only_records=proof_only_records,
            limits=request["limits"],
        )
        if not classification["allowed"]:
            return pre_response_failure_decision(
                request,
                stage=classification["stage"],
                diagnostic_code=classification["diagnostic_code"],
                model_records=discovered_records,
                stdout_bytes=bounded["bytes"],
            )
    try:
        projection = validate_response_envelope(response_bytes, request)
    except AssertionError:
        return pre_response_failure_decision(
            request,
            stage="response_validation",
            diagnostic_code="CSV-NEXT-PROTOCOL-001",
        )
    decision = projection.get("validated_decision")
    assert isinstance(
        decision,
        (ValidatedResponseDecision, PreResponseFailureDecision, NotApplicableDecision),
    )
    return decision


def capture_adapter_stderr(
    chunks: Iterable[bytes],
    *,
    limit: int = LIMIT_DEFAULTS["max_adapter_stderr_capture_bytes"],
) -> dict[str, Any]:
    """Model bounded adapter stderr capture and disposal semantics.

    The iterable is the runner's faithful incremental read boundary.  The
    counter is byte-based and increments before retaining a chunk.  A breach
    stops reading, requests process-group termination, and disposes both raw
    and partial stderr, so no adapter text can reach public diagnostics.  This
    reference does not claim to exercise an OS process.
    """

    assert limit >= 1
    captured = 0
    for chunk_index, chunk in enumerate(chunks):
        assert isinstance(chunk, bytes)
        captured += len(chunk)
        if captured > limit:
            return {
                "allowed": False,
                "captured_bytes": captured,
                "failed_at": chunk_index,
                "process_group_terminated": True,
                "raw_disposed": True,
                "partial_disposed": True,
                "read_stopped": True,
                "child_text_leaked": False,
                "process_group_disposed": True,
                "diagnostic_code": "CSV-NEXT-LIMIT-003",
                "outcome": "payload_unavailable",
                "manifest_stderr_bytes": 0,
            }
    return {
        "allowed": True,
        "captured_bytes": captured,
        "failed_at": None,
        "process_group_terminated": False,
        "raw_disposed": False,
        "partial_disposed": False,
        "read_stopped": False,
        "child_text_leaked": False,
        "process_group_disposed": False,
        "diagnostic_code": None,
        "outcome": "complete",
        "manifest_stderr_bytes": 0,
    }


def capture_adapter_stdout(
    chunks: Iterable[bytes],
    *,
    limit: int = LIMIT_DEFAULTS["max_adapter_stdout_capture_bytes"],
    decoder: Any | None = None,
) -> dict[str, Any]:
    """Capture child stdout incrementally before any decoder sees bytes.

    The parent counts each chunk before retaining it.  A breach terminates the
    process group and disposes every retained byte, so a decoder can only be
    invoked after a bounded, complete capture succeeds.  The iterable models
    the runner's chunk reads; this reference function does not claim to spawn
    or terminate an operating-system process.
    """

    assert limit >= 1
    captured = 0
    retained: list[bytes] = []
    for chunk_index, chunk in enumerate(chunks):
        assert isinstance(chunk, bytes)
        captured += len(chunk)
        if captured > limit:
            return {
                "allowed": False,
                "captured_bytes": captured,
                "retained_bytes": 0,
                "retained": b"",
                "failed_at": chunk_index,
                "process_group_terminated": True,
                "raw_disposed": True,
                "partial_disposed": True,
                "read_stopped": True,
                "process_group_disposed": True,
                "decoder_called": False,
                "diagnostic_code": "CSV-NEXT-LIMIT-003",
                "outcome": "payload_unavailable",
                "manifest_stdout_bytes": 0,
            }
        retained.append(chunk)
    payload = b"".join(retained)
    assert len(payload) == captured <= limit
    decoder_called = False
    if decoder is not None:
        decoder(payload)
        decoder_called = True
    return {
        "allowed": True,
        "captured_bytes": captured,
        "retained_bytes": len(payload),
        "retained": payload,
        "failed_at": None,
        "process_group_terminated": False,
        "raw_disposed": False,
        "partial_disposed": False,
        "read_stopped": False,
        "process_group_disposed": False,
        "decoder_called": decoder_called,
        "diagnostic_code": None,
        "outcome": "complete",
        "manifest_stdout_bytes": len(payload),
    }


def _public_limit_diagnostic() -> dict[str, Any]:
    """Build the catalog-owned replacement emitted after a public byte breach."""

    entry = _diagnostic_catalog()["CSV-NEXT-LIMIT-003"]
    return {
        "type": "diagnostic",
        "schema": "code-structure-viz.diagnostic/v1",
        "code": "CSV-NEXT-LIMIT-003",
        "severity": entry["severity"],
        "domain": "next",
        "path": None,
        "symbol": None,
        "line": None,
        "recoverable": entry["recoverable"],
        "message": entry["message"],
        "outcome": entry["outcome"],
        "ref_permission": entry["ref_permission"],
    }


def _public_diagnostic_jsonl(diagnostics: list[dict[str, Any]]) -> bytes:
    """Encode the complete public diagnostic stream before any write occurs."""

    return b"".join(canonical_json_bytes(diagnostic) + b"\n" for diagnostic in diagnostics)


def render_public_diagnostic_stderr(
    diagnostics: list[dict[str, Any]],
    *,
    limit: int = LIMIT_DEFAULTS["max_stderr_bytes"],
) -> dict[str, Any]:
    """Apply the public diagnostic UTF-8 byte gate with an all-or-none write.

    The complete JSONL payload is encoded and measured before writing.  An
    exact-boundary payload is emitted; a payload one byte over the boundary
    emits zero partial bytes and projects only the stable catalog diagnostic
    into the manifest.
    """

    assert limit >= 1
    _validate_public_diagnostics(diagnostics)
    payload = _public_diagnostic_jsonl(diagnostics)
    if len(payload) <= limit:
        return {
            "allowed": True,
            "encoded_bytes": len(payload),
            "emitted_bytes": len(payload),
            "partial_write_bytes": 0,
            "process_group_terminated": False,
            "raw_disposed": False,
            "partial_disposed": False,
            "diagnostic_code": None,
            "outcome": "complete",
            "manifest_only": False,
            "manifest_diagnostics": copy.deepcopy(diagnostics),
            "stderr_diagnostics": copy.deepcopy(diagnostics),
            "payload": payload,
        }
    replacement = _public_limit_diagnostic()
    return {
        "allowed": False,
        "encoded_bytes": len(payload),
        "emitted_bytes": 0,
        "partial_write_bytes": 0,
        "process_group_terminated": False,
        "raw_disposed": True,
        "partial_disposed": True,
        "diagnostic_code": "CSV-NEXT-LIMIT-003",
        "outcome": "payload_unavailable",
        "manifest_only": True,
        "manifest_diagnostics": [replacement],
        "stderr_diagnostics": [],
        "payload": b"",
    }


def copy_selected_stdout(
    payload: bytes,
    *,
    limit: int = LIMIT_DEFAULTS["max_selected_stdout_bytes"],
) -> dict[str, Any]:
    """Apply the public selected-artifact byte gate as an all-or-none copy.

    A copy failure is a publication result, not a semantic-domain rewrite:
    the validated domain decision remains immutable and the caller publishes
    an unavailable selected artifact with no partial bytes.
    """

    assert isinstance(payload, bytes)
    assert limit >= 1
    if len(payload) <= limit:
        return {
            "allowed": True,
            "bytes": len(payload),
            "retained": payload,
            "retained_bytes": len(payload),
            "partial_disposed": False,
            "publication_outcome": "published_artifact",
            "diagnostic_code": None,
        }
    return {
        "allowed": False,
        "bytes": len(payload),
        "retained": b"",
        "retained_bytes": 0,
        "partial_disposed": True,
        "publication_outcome": "selected_artifact_unavailable",
        "diagnostic_code": "CSV-NEXT-LIMIT-003",
    }


def model_record_budget_allowed(measured: int, limit: int) -> bool:
    """Apply max_model_records without allocating a model-sized fixture."""

    return measured >= 0 and limit >= 1 and measured <= limit


def model_wire_record_count(model_records: int, proof_only_records: int = 0) -> int:
    """Count published model records plus proof-only evidence records.

    ``discovered_records`` is a bijective observation of model IDs.  It is
    not another payload copy.  Only a proof ID absent from the model consumes
    an additional record budget.
    """

    assert model_records >= 0
    assert proof_only_records >= 0
    return model_records + proof_only_records


def response_model_record_counts(
    model: dict[str, Any], proof: dict[str, Any]
) -> tuple[int, int, int]:
    """Return ``(published, proof_only, discovered)`` from actual wire IDs."""

    model_ids = {
        record["id"]
        for collection in COLLECTIONS
        for record in model.get(collection, [])
        if isinstance(record, dict) and isinstance(record.get("id"), str)
    }
    published = sum(
        len(model.get(collection, []))
        for collection in COLLECTIONS
        if isinstance(model.get(collection), list)
    )
    proof_rows = proof.get("discovered_records", []) if isinstance(proof, dict) else []
    proof_only = sum(
        1 for row in proof_rows if isinstance(row, dict) and row.get("record_id") not in model_ids
    )
    return published, proof_only, model_wire_record_count(published, proof_only)


def classify_response_limit(
    *,
    raw_bytes: int,
    aggregate_array_items: int,
    model_records: int,
    proof_only_records: int = 0,
    limits: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Apply the fixed response limit precedence without materializing records."""

    resolved = {**LIMIT_DEFAULTS, **(limits or {})}
    assert raw_bytes >= 0
    assert aggregate_array_items >= 0
    measured_model_records = model_wire_record_count(model_records, proof_only_records)
    response_limit = resolved.get("max_adapter_response_bytes", resolved["max_stdout_bytes"])
    if raw_bytes > response_limit:
        return {
            "allowed": False,
            "diagnostic_code": "CSV-NEXT-LIMIT-003",
            "stage": "response_raw_bytes",
            "measured": raw_bytes,
        }
    if aggregate_array_items > resolved["max_total_array_items"]:
        return {
            "allowed": False,
            "diagnostic_code": "CSV-NEXT-PROTOCOL-001",
            "stage": "response_decode",
            "measured": aggregate_array_items,
        }
    if measured_model_records > resolved["max_model_records"]:
        return {
            "allowed": False,
            "diagnostic_code": "CSV-NEXT-LIMIT-005",
            "stage": "model_validation",
            "measured": measured_model_records,
        }
    return {"allowed": True, "diagnostic_code": None, "stage": None, "measured": None}


def assert_limit_boundary(limit: int, *, at_limit: bool, over_limit: bool) -> None:
    assert limit >= 1
    assert limit_boundary_allowed(limit, limit - 1)
    assert limit_boundary_allowed(limit, limit) is at_limit
    assert limit_boundary_allowed(limit, limit + 1) is over_limit


def validate_limits_consistency(*projections: dict[str, Any]) -> None:
    assert projections
    for projection in projections:
        validate_limits(projection)
    first = projections[0]
    assert all(projection == first for projection in projections[1:])


def encoded_request_bytes(request: dict[str, Any]) -> bytes:
    """Return the exact UTF-8 bytes sent to the adapter's stdin."""

    return canonical_json_bytes(request)


def validate_encoded_stdin_size(request: dict[str, Any], encoded: bytes | None = None) -> int:
    """Validate the request byte cap and return the measured size.

    The boundary helper accepts precomputed bytes so tests can exercise
    limit-1/limit/limit+1 without allocating a 96 MiB payload.
    """

    measured = len(encoded if encoded is not None else encoded_request_bytes(request))
    limit = request["limits"]["max_encoded_stdin_bytes"]
    assert encoded_stdin_allowed(measured, limit)
    return measured


def encoded_stdin_allowed(measured: int, limit: int) -> bool:
    return 0 <= measured <= limit


def assert_encoded_stdin_boundary(measured: int, limit: int, expected: bool) -> None:
    """Model the exact inclusive byte boundary without constructing bytes."""

    assert measured >= 0
    assert encoded_stdin_allowed(measured, limit) is expected


def _id_kind(record_id: str) -> str:
    match = ID_RE.fullmatch(record_id)
    assert match, record_id
    return match.group(1)


def _assert_path(path: str, *, allow_root: bool = True) -> None:
    assert isinstance(path, str)
    assert unicodedata.normalize("NFC", path) == path
    encoded_length = len(path.encode("utf-8"))
    assert 1 <= encoded_length <= PATH_VALUE_MAX_BYTES
    if allow_root and path == ".":
        return
    assert PATH_RE.fullmatch(path), path


def _assert_file_path(path: str) -> None:
    """Validate a path value that cannot be the root sentinel."""

    _assert_path(path, allow_root=False)


def _under(path: str, root: str) -> bool:
    return root == "." or path == root or path.startswith(root.rstrip("/") + "/")


def _assert_sorted_unique(
    records: list[dict[str, Any]], collection: str
) -> dict[str, dict[str, Any]]:
    ids = [record["id"] for record in records]
    assert ids == sorted(ids), collection
    assert len(ids) == len(set(ids)), collection
    assert all(_id_kind(record_id) == collection.removesuffix("s") for record_id in ids)
    for record in records:
        assert recompute_record_id(record) == record["id"]
    return {record_id: record for record_id, record in zip(ids, records, strict=True)}


def _assert_unique(values: list[Any]) -> None:
    encoded = [canonical_json_bytes(value) for value in values]
    assert len(encoded) == len(set(encoded))


def _assert_canonical(values: list[Any]) -> None:
    encoded = [canonical_json_bytes(value) for value in values]
    assert encoded == sorted(encoded)
    assert len(encoded) == len(set(encoded))


def _assert_target_keys(targets: list[str]) -> None:
    assert all(target.startswith(TARGET_SELECTOR_PREFIX) for target in targets)
    for target in targets:
        _assert_path(target.removeprefix(TARGET_SELECTOR_PREFIX), allow_root=True)
    normalized = [canonical_target_key(target) for target in targets]
    assert normalized == targets
    _assert_canonical(targets)


def canonical_target_key(target: str) -> str:
    """Canonicalize the public path target before proof comparison.

    ``path:`` is the only public target grammar.  Component/module IDs and
    semantic keys remain private model identifiers and are never accepted as
    request syntax.
    """

    assert unicodedata.normalize("NFC", target) == target
    normalized = target
    match = PUBLIC_TARGET_RE.fullmatch(normalized)
    assert match is not None
    path = match.group(1)
    _assert_path(path, allow_root=True)
    assert "#" not in path
    return f"path:{path}"


def resolve_target_resolutions(
    targets: list[str],
    model: dict[str, Any],
    *,
    unavailable_record_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Resolve public file/directory paths against the frozen published model.

    A file target selects its file, matching module, and all components owned
    by that module.  A directory target selects the complete descendant set;
    multiple descendants are expected and are not ambiguous.  More than one
    project in the selected set is a project-scope failure.
    """

    preflight = target_completeness_failure(model, targets)
    if preflight is not None:
        failed_keys = {item["target_key"] for item in preflight.failures}
        return [
            {
                "target_key": canonical_target_key(target),
                "status": "failed" if canonical_target_key(target) in failed_keys else "resolved",
                "record_ids": [],
            }
            for target in sorted(targets, key=canonical_target_key)
        ]
    collections = _validate_model_collections(model)
    unavailable = unavailable_record_ids or set()
    resolutions: list[dict[str, Any]] = []
    for target in targets:
        target_key = canonical_target_key(target)
        requested_path = target_key.removeprefix("path:")
        exact_files = [
            record for record in collections["files"].values() if record["path"] == requested_path
        ]
        matching_files = exact_files or [
            record
            for record in collections["files"].values()
            if _under(record["path"], requested_path)
        ]
        project_ids = {record["project_id"] for record in matching_files}
        if not matching_files or len(project_ids) != 1:
            matching: list[str] = []
            status = "failed"
        elif len(exact_files) > 1:
            # Two frozen Files with one public path are an ambiguous source
            # view, even if their record IDs differ after a mutation.
            matching = []
            status = "failed"
        elif exact_files and not _is_program_file(exact_files[0]):
            # A direct context/control file is provenance only.  It cannot be
            # addressed as a semantic Next target even when it is frozen.
            matching = []
            status = "failed"
        else:
            file_keys = {(record["project_id"], record["path"]) for record in matching_files}
            matching_modules = [
                record
                for record in collections["modules"].values()
                if (record["project_id"], record["path"]) in file_keys
                and _is_program_file(
                    next(
                        (
                            file
                            for file in collections["files"].values()
                            if file["project_id"] == record["project_id"]
                            and file["path"] == record["path"]
                        ),
                        {"roles": [], "path": record["path"]},
                    )
                )
            ]
            module_ids = {record["id"] for record in matching_modules}
            program_files = [record for record in matching_files if _is_program_file(record)]
            module_counts = {
                (record["project_id"], record["path"]): sum(
                    candidate["project_id"] == record["project_id"]
                    and candidate["path"] == record["path"]
                    for candidate in matching_modules
                )
                for record in program_files
            }
            if any(count != 1 for count in module_counts.values()):
                matching = []
                status = "failed"
                resolutions.append(
                    {
                        "target_key": target_key,
                        "status": status,
                        "record_ids": matching,
                    }
                )
                continue
            matching_components = [
                record
                for record in collections["components"].values()
                if record["module_id"] in module_ids
            ]
            matching = sorted(
                [
                    *[record["id"] for record in matching_files],
                    *[record["id"] for record in matching_modules],
                    *[record["id"] for record in matching_components],
                ]
            )
            if not matching or unavailable.intersection(matching):
                matching = []
                status = "failed"
            else:
                status = "resolved"
        resolutions.append(
            {
                "target_key": target_key,
                "status": status,
                "record_ids": matching if status == "resolved" else [],
            }
        )
    return sorted(resolutions, key=canonical_json_bytes)


def _assert_formats(formats: list[str]) -> None:
    assert formats
    assert len(formats) == len(set(formats))
    assert all(format_name in FORMAT_ORDER_INDEX for format_name in formats)
    assert formats == sorted(formats, key=FORMAT_ORDER_INDEX.__getitem__)


def canonical_run_context(
    *,
    requested_formats: list[str] | tuple[str, ...],
    budget_requested: int | None,
    budget_resolved: int,
    budget_source: str,
    stdout_selector: str | None,
) -> NextRunContext:
    """Construct and validate the explicit context shared by all run surfaces."""

    formats = list(requested_formats)
    _assert_formats(formats)
    assert budget_requested is None or 1 <= budget_requested <= 100000
    assert 1 <= budget_resolved <= 100000
    assert budget_source in RUN_CONTEXT_BUDGET_SOURCES
    assert stdout_selector in RUN_CONTEXT_SELECTORS
    if stdout_selector is not None and stdout_selector != "manifest":
        assert stdout_selector.removeprefix("next:") in formats
    if budget_source == "builtin":
        assert budget_requested is None
    else:
        assert budget_requested is not None
    return {
        "requested_formats": formats,
        "budget_requested": budget_requested,
        "budget_resolved": budget_resolved,
        "budget_source": budget_source,
        "stdout_selector": stdout_selector,
    }


def _assert_external_target(target: dict[str, Any]) -> None:
    assert target["kind"] in {"external", "unresolved"}
    assert PACKAGE_RE.fullmatch(target["safe_specifier"]), target
    exported_name = target["exported_name"]
    assert exported_name is None or exported_name == "default" or is_declaration_key(exported_name)


def _validate_type_node(
    node: dict[str, Any],
    module_ids: set[str],
    *,
    _depth: int = 1,
    _type_parameter_scope: int | None = None,
    _state: dict[str, int] | None = None,
) -> None:
    """Validate the complete PropsTypeIR grammar and its finite limits."""

    state = (
        _state
        if _state is not None
        else {
            "nodes": 0,
            "properties": 0,
            "union_members": 0,
            "intersection_members": 0,
            "signatures": 0,
        }
    )
    assert 1 <= _depth <= LIMIT_DEFAULTS["max_type_depth"]
    state["nodes"] += 1
    assert state["nodes"] <= LIMIT_DEFAULTS["max_type_nodes_per_prop"]
    kind = node["kind"]
    if kind == "primitive":
        assert set(node) == {"kind", "name"}
    elif kind == "type_parameter":
        assert set(node) == {"kind", "ordinal"}
        assert _type_parameter_scope is not None
        assert 0 <= node["ordinal"] < _type_parameter_scope
    elif kind == "redacted_literals":
        assert set(node) == {"kind", "base", "count"}
        assert node["base"] in {"boolean", "bigint", "number", "string"}
        assert node["count"] >= 1
    elif kind == "reference":
        assert set(node) == {"kind", "scope", "module", "exported_name", "type_arguments"}
        scope = node["scope"]
        if scope == "repository":
            assert node["module"] in module_ids
            assert node["exported_name"] == "default" or is_declaration_key(node["exported_name"])
        elif scope == "external":
            assert PACKAGE_RE.fullmatch(node["module"])
            assert node["exported_name"] == "default" or is_declaration_key(node["exported_name"])
        else:
            assert scope == "trusted"
            assert node["module"] in TRUSTED_REFERENCE_MODULES
            if node["module"] != "typescript/lib":
                assert node["exported_name"] is not None
                assert (
                    node["module"],
                    (node["exported_name"],),
                ) in TRUSTED_PROFILE_CERTIFIED_MODULE_KEYS
            else:
                # The bundled standard-library root is the one non-symbol
                # trusted reference.  Its declarations are covered by the
                # TypeScript Program inventory's certified global rows.
                assert node["exported_name"] is None
            assert (
                node["exported_name"] is None
                or node["exported_name"] == "default"
                or is_declaration_key(node["exported_name"])
            )
        for child in node["type_arguments"]:
            _validate_type_node(
                child,
                module_ids,
                _depth=_depth + 1,
                _type_parameter_scope=_type_parameter_scope,
                _state=state,
            )
    elif kind == "array":
        assert set(node) == {"kind", "element", "readonly"}
        _validate_type_node(
            node["element"],
            module_ids,
            _depth=_depth + 1,
            _type_parameter_scope=_type_parameter_scope,
            _state=state,
        )
    elif kind == "tuple":
        assert set(node) == {"kind", "elements", "rest", "readonly"}
        optional_seen = False
        for element in node["elements"]:
            assert set(element) == {"type", "optional"}
            if element["optional"]:
                optional_seen = True
            elif optional_seen:
                raise AssertionError("required tuple element follows optional element")
            _validate_type_node(
                element["type"],
                module_ids,
                _depth=_depth + 1,
                _type_parameter_scope=_type_parameter_scope,
                _state=state,
            )
        if node["rest"] is not None:
            _validate_type_node(
                node["rest"],
                module_ids,
                _depth=_depth + 1,
                _type_parameter_scope=_type_parameter_scope,
                _state=state,
            )
    elif kind == "function":
        assert set(node) == {
            "kind",
            "type_parameter_count",
            "this_type",
            "parameters",
            "return_type",
        }
        parameter_scope = node["type_parameter_count"]
        assert 0 <= parameter_scope <= LIMIT_DEFAULTS["max_signatures_per_component"]
        state["signatures"] += 1
        assert state["signatures"] <= LIMIT_DEFAULTS["max_signatures_per_component"]
        if node["this_type"] is not None:
            _validate_type_node(
                node["this_type"],
                module_ids,
                _depth=_depth + 1,
                _type_parameter_scope=parameter_scope,
                _state=state,
            )
        optional_seen = False
        rest_seen = False
        for parameter in node["parameters"]:
            assert set(parameter) == {"type", "optional", "rest"}
            assert not rest_seen
            if parameter["rest"]:
                assert not parameter["optional"]
                rest_seen = True
            elif parameter["optional"]:
                optional_seen = True
            else:
                assert not optional_seen
            _validate_type_node(
                parameter["type"],
                module_ids,
                _depth=_depth + 1,
                _type_parameter_scope=parameter_scope,
                _state=state,
            )
        _validate_type_node(
            node["return_type"],
            module_ids,
            _depth=_depth + 1,
            _type_parameter_scope=parameter_scope,
            _state=state,
        )
    elif kind in {"union", "intersection"}:
        assert set(node) == {"kind", "members"}
        assert node["members"]
        assert len(node["members"]) <= LIMIT_DEFAULTS[f"max_{kind}_members"]
        assert all(child["kind"] != kind for child in node["members"])
        _assert_canonical(node["members"])
        for child in node["members"]:
            _validate_type_node(
                child,
                module_ids,
                _depth=_depth + 1,
                _type_parameter_scope=_type_parameter_scope,
                _state=state,
            )
    elif kind == "object":
        assert set(node) == {"kind", "properties", "index_signatures", "call_signatures"}
        assert len(node["properties"]) <= LIMIT_DEFAULTS["max_nested_properties"]
        _assert_canonical([prop["name"] for prop in node["properties"]])
        _assert_canonical([item["key_type"] for item in node["index_signatures"]])
        assert len(node["call_signatures"]) <= LIMIT_DEFAULTS["max_signatures_per_component"]
        _assert_canonical(node["call_signatures"])
        for prop in node["properties"]:
            assert set(prop) == {"name", "type", "optional", "readonly"}
            assert unicodedata.normalize("NFC", prop["name"]) == prop["name"]
            state["properties"] += 1
            assert state["properties"] <= LIMIT_DEFAULTS["max_nested_properties"]
            _validate_type_node(
                prop["type"],
                module_ids,
                _depth=_depth + 1,
                _type_parameter_scope=_type_parameter_scope,
                _state=state,
            )
        for signature in node["index_signatures"]:
            assert set(signature) == {"key_type", "value_type", "readonly"}
            _validate_type_node(
                signature["value_type"],
                module_ids,
                _depth=_depth + 1,
                _type_parameter_scope=_type_parameter_scope,
                _state=state,
            )
        for signature in node["call_signatures"]:
            assert set(signature) == {
                "type_parameter_count",
                "this_type",
                "parameters",
                "return_type",
            }
            signature_scope = signature["type_parameter_count"]
            assert 0 <= signature_scope <= LIMIT_DEFAULTS["max_signatures_per_component"]
            state["signatures"] += 1
            assert state["signatures"] <= LIMIT_DEFAULTS["max_signatures_per_component"]
            if signature["this_type"] is not None:
                _validate_type_node(
                    signature["this_type"],
                    module_ids,
                    _depth=_depth + 1,
                    _type_parameter_scope=signature_scope,
                    _state=state,
                )
            optional_seen = False
            rest_seen = False
            for parameter in signature["parameters"]:
                assert set(parameter) == {"type", "optional", "rest"}
                assert not rest_seen
                if parameter["rest"]:
                    assert not parameter["optional"]
                    rest_seen = True
                elif parameter["optional"]:
                    optional_seen = True
                else:
                    assert not optional_seen
                _validate_type_node(
                    parameter["type"],
                    module_ids,
                    _depth=_depth + 1,
                    _type_parameter_scope=signature_scope,
                    _state=state,
                )
            _validate_type_node(
                signature["return_type"],
                module_ids,
                _depth=_depth + 1,
                _type_parameter_scope=signature_scope,
                _state=state,
            )
    else:
        assert kind == "opaque"
        assert set(node) == {"kind", "reason"}


def _opaque_reason_counts(node: dict[str, Any]) -> dict[str, int]:
    """Project every opaque TypeIR reason without trusting adapter counts."""

    if node["kind"] == "opaque":
        return {node["reason"]: 1}
    children: list[dict[str, Any]] = []
    if node["kind"] == "array":
        children = [node["element"]]
    elif node["kind"] == "tuple":
        children = [element["type"] for element in node["elements"]]
        if node["rest"] is not None:
            children.append(node["rest"])
    elif node["kind"] == "function":
        children = [parameter["type"] for parameter in node["parameters"]]
        children.append(node["return_type"])
        if node["this_type"] is not None:
            children.append(node["this_type"])
    elif node["kind"] in {"union", "intersection"}:
        children = list(node["members"])
    elif node["kind"] == "object":
        children = [prop["type"] for prop in node["properties"]]
        children.extend(signature["value_type"] for signature in node["index_signatures"])
        for signature in node["call_signatures"]:
            children.extend(parameter["type"] for parameter in signature["parameters"])
            children.append(signature["return_type"])
            if signature["this_type"] is not None:
                children.append(signature["this_type"])
    result: dict[str, int] = {}
    for child in children:
        for reason, count in _opaque_reason_counts(child).items():
            result[reason] = result.get(reason, 0) + count
    return result


def _validate_model_collections(model: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    result: dict[str, dict[str, dict[str, Any]]] = {}
    for collection in COLLECTIONS:
        result[collection] = _assert_sorted_unique(model[collection], collection)
    return result


def derive_boundary_roles(model: dict[str, Any]) -> dict[str, list[str]]:
    """Recompute BoundaryRolePropagation/v1 from facts, router, and value edges.

    ``derived_roles`` is output evidence, never an input to this calculation.
    Client-entry seeds are deliberately excluded from ``client_dependency``;
    the forward closure contains only their internal static value targets.
    Server traversal starts at non-client ``app_ui`` modules and at explicit
    server-to-client edge sources, and stops before entering a client entry.
    The two independently computed closures may overlap and therefore produce
    a legitimate dual role.
    """

    modules = {
        module["id"]: module for module in model.get("modules", []) if isinstance(module, dict)
    }
    client_entries = {
        module_id for module_id, module in modules.items() if module.get("client_entry") is True
    }
    router_contexts = {
        module_id: module.get("router_context") for module_id, module in modules.items()
    }
    for fact in model.get("facts", []):
        if not isinstance(fact, dict) or fact.get("owner_id") not in modules:
            continue
        if fact.get("kind") == "client_entry":
            assert fact.get("value") is True
            client_entries.add(fact["owner_id"])
        elif fact.get("kind") == "router_context":
            router_contexts[fact["owner_id"]] = fact.get("value")

    value_edges: dict[str, set[str]] = {module_id: set() for module_id in modules}
    server_seeds: set[str] = {
        module_id
        for module_id, context in router_contexts.items()
        if context == "app_ui" and module_id not in client_entries
    }
    for relation in model.get("relations", []):
        if not isinstance(relation, dict) or relation.get("kind") != "static_import":
            continue
        source_id = relation.get("source_id")
        target = relation.get("target")
        if (
            relation.get("role") != "value"
            or not isinstance(source_id, str)
            or source_id not in modules
            or not isinstance(target, dict)
            or target.get("kind") != "internal"
            or target.get("module_id") not in modules
        ):
            continue
        target_id = target["module_id"]
        if not isinstance(target_id, str):
            continue
        value_edges[source_id].add(target_id)
        if relation.get("boundary_effect") == "server_to_client_entry":
            assert source_id not in client_entries
            assert target_id in client_entries
            server_seeds.add(source_id)

    client_dependency: set[str] = set()
    pending = list(sorted(client_entries))
    visited: set[str] = set(client_entries)
    while pending:
        source_id = pending.pop(0)
        for target_id in sorted(value_edges.get(source_id, ())):
            if target_id not in client_entries:
                client_dependency.add(target_id)
            if target_id not in visited:
                visited.add(target_id)
                pending.append(target_id)

    server_candidate: set[str] = set()
    pending = list(sorted(server_seeds))
    visited = set()
    while pending:
        source_id = pending.pop(0)
        if source_id in visited or source_id not in modules:
            continue
        visited.add(source_id)
        if source_id in client_entries:
            continue
        server_candidate.add(source_id)
        for target_id in sorted(value_edges.get(source_id, ())):
            if target_id in client_entries:
                continue
            pending.append(target_id)

    return {
        module_id: sorted(
            role
            for role, members in (
                ("client_dependency", client_dependency),
                ("server_candidate", server_candidate),
            )
            if module_id in members
        )
        for module_id in sorted(modules)
    }


def _diagnostic_catalog() -> dict[str, dict[str, Any]]:
    return {
        entry["code"]: entry
        for entry in json.loads(CATALOG_PATH.read_text(encoding="utf-8"))["entries"]
    }


def _decision_known_counts(
    request: dict[str, Any] | None,
    *,
    stdout_bytes: int | None = None,
    model_records: int | None = None,
) -> dict[str, int | None]:
    """Derive bounded counters owned by a pre-response decision."""

    files = request.get("files") if request is not None else None
    return {
        "files": len(files) if isinstance(files, list) else None,
        "source_bytes": (
            sum(item.get("size_bytes", 0) for item in files)
            if isinstance(files, list) and all(isinstance(item, dict) for item in files)
            else None
        ),
        "model_records": model_records,
        "stdout_bytes": stdout_bytes,
    }


def pre_response_failure_decision(
    request: dict[str, Any] | None,
    *,
    stage: str,
    diagnostic_code: str,
    known_counts: dict[str, int | None] | None = None,
    stdout_bytes: int | None = None,
    model_records: int | None = None,
    run_context: NextRunContext | None = None,
    decision_context: NextDecisionContext | None = None,
    path: str | None = None,
    symbol: str | None = None,
) -> PreResponseFailureDecision:
    """Create the closed authority for a failure before response validation."""

    # A request-independent failure (for example config/project discovery)
    # cannot fabricate a request.  Prefer the closed decision context as the
    # source of run identity when one is supplied, then fall back to the
    # explicit context used by the legacy fixture path.
    context_source = (
        request["run_context"]
        if request is not None
        else (decision_context.run_context if decision_context is not None else run_context)
    )
    context = canonical_run_context(
        **(
            context_source
            or {
                "requested_formats": ["semantic-json", "plantuml"],
                "budget_requested": None,
                "budget_resolved": DEFAULT_MAX_ENTITIES,
                "budget_source": "builtin",
                "stdout_selector": "next:semantic-json",
            }
        )
    )
    entry = _diagnostic_catalog()[diagnostic_code]
    assert entry["outcome"] == "payload_unavailable"
    permission = entry["ref_permission"]
    if permission == "none":
        assert path is None and symbol is None
    elif permission == "path":
        assert path is not None and symbol is None
        _assert_file_path(path)
    elif permission == "symbol":
        assert path is None and symbol is not None
        _id_kind(symbol)
    else:
        assert permission == "path_or_symbol"
        assert (path is None) != (symbol is None)
        if path is not None:
            _assert_file_path(path)
        if symbol is not None:
            _id_kind(symbol)
    diagnostic = {
        "type": "diagnostic",
        "schema": "code-structure-viz.diagnostic/v1",
        "code": diagnostic_code,
        "severity": entry["severity"],
        "domain": "next",
        "path": path,
        "symbol": symbol,
        "line": None,
        "recoverable": entry["recoverable"],
        "message": entry["message"],
        "outcome": entry["outcome"],
        "ref_permission": entry["ref_permission"],
    }
    context_counts = decision_context.known_counts if decision_context is not None else None
    resolved_counts = copy.deepcopy(
        known_counts
        if known_counts is not None
        else context_counts
        if context_counts is not None
        else _decision_known_counts(
            request,
            stdout_bytes=stdout_bytes,
            model_records=model_records,
        )
    )
    node_stages = {"node_discovery", "node_spawn", "node_timeout", "node_process"}
    publication_context = _publication_context_from_request(
        request,
        context,
        decision_context=decision_context,
        toolchain=_toolchain_snapshot(
            node_status="unavailable" if stage in node_stages else "available"
        ),
        trusted_environment=_trusted_environment_snapshot(),
    )
    return PreResponseFailureDecision(
        request=request,
        run_context=context,
        stage=stage,
        diagnostic_code=diagnostic_code,
        diagnostic=diagnostic,
        known_counts=resolved_counts,
        decision_context=decision_context
        or NextDecisionContext(
            run_context=context,
            request_id=(request or {}).get("request_id"),
            targets=tuple((request or {}).get("targets", ())),
            limits=copy.deepcopy((request or {}).get("limits")),
            stage=stage,
            diagnostic_code=diagnostic_code,
        ),
        publication_context=publication_context,
    )


def not_applicable_decision(request: dict[str, Any]) -> NotApplicableDecision:
    """Create the closed authority for an intentional non-Next project."""

    entry = _diagnostic_catalog()["CSV-NEXT-APPLICABILITY-001"]
    return NotApplicableDecision(
        request=request,
        run_context=canonical_run_context(**request["run_context"]),
        diagnostic={
            "type": "diagnostic",
            "schema": "code-structure-viz.diagnostic/v1",
            "code": "CSV-NEXT-APPLICABILITY-001",
            "severity": entry["severity"],
            "domain": "next",
            "path": None,
            "symbol": None,
            "line": None,
            "recoverable": entry["recoverable"],
            "message": entry["message"],
            "outcome": entry["outcome"],
            "ref_permission": entry["ref_permission"],
        },
        known_counts=_decision_known_counts(request),
        publication_context=_publication_context_from_request(
            request,
            canonical_run_context(**request["run_context"]),
            toolchain=_toolchain_snapshot(node_status="not_applicable"),
            trusted_environment=_trusted_environment_snapshot(),
        ),
    )


def _validate_model_diagnostics(diagnostics: list[dict[str, Any]]) -> None:
    catalog = _diagnostic_catalog()
    _assert_canonical(diagnostics)
    aggregate_keys: list[Any] = []
    for diagnostic in diagnostics:
        entry = catalog.get(diagnostic["code"])
        assert entry is not None
        for field in ("severity", "recoverable", "outcome", "ref_permission"):
            assert diagnostic[field] == entry[field]
        if "reason" in diagnostic:
            assert diagnostic["code"] == "CSV-NEXT-TARGET-001"
            assert diagnostic["reason"] in TARGET_FAILURE_REASONS
        assert diagnostic["count"] >= 1
        permission = entry["ref_permission"]
        path_ref = diagnostic["path_ref"]
        symbol_ref = diagnostic["symbol_ref"]
        if permission == "none":
            assert path_ref is None and symbol_ref is None
        elif permission == "path":
            assert path_ref is not None and symbol_ref is None
            _assert_file_path(path_ref)
        elif permission == "symbol":
            assert path_ref is None and symbol_ref is not None
            _id_kind(symbol_ref)
        else:
            assert permission == "path_or_symbol"
            assert (path_ref is None) != (symbol_ref is None)
            if path_ref is not None:
                _assert_file_path(path_ref)
            if symbol_ref is not None:
                _id_kind(symbol_ref)
        aggregate_keys.append(
            (
                diagnostic["code"],
                diagnostic["path_ref"],
                diagnostic["symbol_ref"],
                diagnostic["outcome"],
                diagnostic.get("reason"),
            )
        )
    assert len(aggregate_keys) == len(set(aggregate_keys))


def _validate_public_diagnostics(diagnostics: list[dict[str, Any]]) -> None:
    catalog = _diagnostic_catalog()
    _assert_canonical(diagnostics)
    aggregate_keys: list[Any] = []
    for diagnostic in diagnostics:
        entry = catalog.get(diagnostic["code"])
        assert entry is not None
        assert diagnostic["type"] == "diagnostic"
        assert diagnostic["schema"] == "code-structure-viz.diagnostic/v1"
        assert diagnostic["domain"] == "next"
        assert diagnostic["line"] is None
        assert diagnostic["message"] == entry["message"]
        for field in ("severity", "recoverable", "outcome", "ref_permission"):
            assert diagnostic[field] == entry[field]
        if "reason" in diagnostic:
            assert diagnostic["code"] == "CSV-NEXT-TARGET-001"
            assert diagnostic["reason"] in TARGET_FAILURE_REASONS
        permission = entry["ref_permission"]
        path = diagnostic["path"]
        symbol = diagnostic["symbol"]
        if permission == "none":
            assert path is None and symbol is None
        elif permission == "path":
            assert path is not None and symbol is None
            _assert_file_path(path)
        elif permission == "symbol":
            assert path is None and symbol is not None
            _id_kind(symbol)
        else:
            assert permission == "path_or_symbol"
            assert (path is None) != (symbol is None)
            if path is not None:
                _assert_file_path(path)
            if symbol is not None:
                _id_kind(symbol)
        aggregate_keys.append(
            (
                diagnostic["code"],
                diagnostic["path"],
                diagnostic["symbol"],
                diagnostic["outcome"],
                diagnostic.get("reason"),
            )
        )
    assert len(aggregate_keys) == len(set(aggregate_keys))


def validate_semantic_snapshot(value: dict[str, Any]) -> None:
    """Validate public Next projection and its status/diagnostic agreement."""

    assert value["type"] == "semantic_snapshot"
    assert value["schema"] == "code-structure-viz.semantic/v1"
    assert value["domain"] == "next"
    assert value["document_kind"] == "snapshot"
    head_commit = value["source"]["head_commit"]
    assert head_commit is None or re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", head_commit)
    status = value["status"]
    if status == "complete":
        assert "incomplete_kind" not in value
        allowed_outcomes = {"complete"}
    else:
        assert status == "incomplete"
        assert value["incomplete_kind"] == "partial_safe"
        allowed_outcomes = {"partial_safe"}
    _validate_model_diagnostics(value["diagnostics"])
    assert {item["outcome"] for item in value["diagnostics"]} <= allowed_outcomes
    entities = value["entities"]
    model = {
        "schema": "code-structure-viz.next-model/v1",
        "projects": sorted(value["projects"], key=lambda item: item["id"]),
        "files": value["files"],
        "modules": [item for item in entities if item["kind"] == "module"],
        "components": [item for item in entities if item["kind"] == "component"],
        "members": value["members"],
        "relations": value["relations"],
        "facts": value["facts"],
        "coverage": value["coverage"],
        "diagnostics": value["diagnostics"],
    }
    actual_entities = validate_model(
        model,
        max_model_records=value["request"]["limits"]["max_model_records"],
    )
    assert entity_budget_allowed(actual_entities, value["request"]["limits"]["max_entities"])
    expected_projects = [
        {
            "root": project["root"],
            "source_roots": project["source_roots"],
            "config_path": project["config_path"],
            "compiler_options": project["compiler_options"],
        }
        for project in value["projects"]
    ]
    assert value["request"]["projects"] == expected_projects
    _assert_target_keys(value["request"]["targets"])
    _assert_formats(value["request"]["formats"])
    assert value["source"]["file_count"] == len(value["files"])


def _record_references(record: dict[str, Any]) -> set[str]:
    """Return declared record IDs that make ``record`` unsafe when tainted."""

    references: set[str] = set()
    kind = record["kind"]
    if kind in {"file", "module"}:
        references.add(record["project_id"])
    elif kind == "project":
        pass
    elif kind == "component":
        references.add(record["module_id"])
    elif kind == "export_binding":
        references.update((record["owner_id"], record["target_component_id"]))
    elif kind == "import_binding":
        references.add(record["owner_id"])
        if record["local_component_id"] is not None:
            references.add(record["local_component_id"])
        if record["source"]["kind"] == "internal":
            references.add(record["source"]["module_id"])
    elif kind in {"prop", "client_entry", "router_context"}:
        references.add(record["owner_id"])
    elif kind in {"static_import", "literal_dynamic_import", "jsx_render"}:
        references.add(record["source_id"])
        target = record["target"]
        target_id_key = (
            "module_id" if kind in {"static_import", "literal_dynamic_import"} else "component_id"
        )
        if target["kind"] == "internal":
            references.add(target[target_id_key])
    else:
        assert kind == "component_wrap"
        references.update((record["source_id"], record["target_component_id"]))
    return references


def _taint_dependency_closure(
    discovered: dict[str, dict[str, dict[str, Any]]],
    tainted_ids: set[str],
) -> set[str]:
    """Expand file/project and declared-reference taint to all dependent records."""

    closure = set(tainted_ids)
    changed = True
    while changed:
        changed = False
        tainted_projects = {
            record_id for record_id, item in discovered["projects"].items() if record_id in closure
        }
        for records in discovered.values():
            for record_id, item in records.items():
                record = item["record"]
                if record_id in closure:
                    continue
                if (
                    record["kind"] in {"file", "module"}
                    and record["project_id"] in tainted_projects
                ):
                    closure.add(record_id)
                    changed = True
                    continue
                if _record_references(record) & closure:
                    closure.add(record_id)
                    changed = True
        tainted_files = [
            item["record"]
            for records in discovered.values()
            for item in records.values()
            if item["record"]["kind"] == "file" and item["record"]["id"] in closure
        ]
        for records in discovered.values():
            for record_id, item in records.items():
                record = item["record"]
                if record_id in closure or record["kind"] != "module":
                    continue
                if any(
                    record["project_id"] == file_record["project_id"]
                    and record["path"] == file_record["path"]
                    for file_record in tainted_files
                ):
                    closure.add(record_id)
                    changed = True
    return closure


def _record_index(discovered: dict[str, dict[str, dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    return {
        record_id: item["record"]
        for records in discovered.values()
        for record_id, item in records.items()
    }


def _record_project_path(
    record: dict[str, Any], records: dict[str, dict[str, Any]]
) -> tuple[str, str] | None:
    """Resolve the owning project/path used by ``file_all_records``."""

    kind = record["kind"]
    if kind == "project":
        return None
    if kind in {"file", "module"}:
        return (record["project_id"], record["path"])
    if kind == "component":
        owner = records.get(record["module_id"])
    elif kind in {"export_binding", "import_binding"}:
        owner = records.get(record["owner_id"])
    elif kind == "prop":
        component = records.get(record["owner_id"])
        owner = records.get(component["module_id"]) if component is not None else None
    elif kind in {"static_import", "literal_dynamic_import"}:
        owner = records.get(record["source_id"])
    elif kind in {"jsx_render", "component_wrap"}:
        component = records.get(record["source_id"])
        owner = records.get(component["module_id"]) if component is not None else None
    else:
        assert kind in {"client_entry", "router_context"}
        owner = records.get(record["owner_id"])
    if owner is None:
        return None
    return (owner["project_id"], owner["path"])


def _root_edge_is_allowed(root: dict[str, Any], target: dict[str, Any], rule: str) -> bool:
    """Keep root-to-record edges in the closed v1 taint vocabulary."""

    root_kind = root["kind"]
    target_kind = target["kind"]
    if root["collection"] == "files":
        return (
            root_kind in {"parse_file", "read_file"}
            and rule == "file_all_records"
            and target_kind
            in {
                "file",
                "module",
                "component",
                "export_binding",
                "import_binding",
                "prop",
                "static_import",
                "literal_dynamic_import",
                "jsx_render",
                "component_wrap",
                "client_entry",
                "router_context",
            }
        )
    allowed_rules = {
        "type_symbol": {"type_subtree", "identity_dependency"},
        "props_subtree": {"type_subtree", "identity_dependency"},
        "export_binding": {"incoming_reexport", "identity_dependency"},
        "component_flow": {"component_flow", "identity_dependency"},
        "module_relation": {
            "value_import_dependency",
            "relation_dependency",
            "identity_dependency",
        },
        "boundary_derivation": {"boundary_closure", "relation_dependency", "identity_dependency"},
        "parse_file": {"file_all_records"},
        "read_file": {"file_all_records"},
    }
    return rule in allowed_rules.get(
        root_kind, set()
    ) and target_kind in ROOT_EDGE_TARGET_KINDS.get(root_kind, set())


def _causal_edge_is_allowed(
    edge: dict[str, Any],
    records: dict[str, dict[str, Any]],
    failure_roots: dict[str, dict[str, Any]],
) -> bool:
    """Check a causal edge against the closed v1 propagation rules."""

    source_id = edge["source_id"]
    target_id = edge["record_id"]
    target = records[target_id]
    rule = edge["rule"]
    if source_id in failure_roots:
        root = failure_roots[source_id]
        if not _root_edge_is_allowed(root, target, rule):
            return False
        if root["kind"] in {"parse_file", "read_file"} and root["path_ref"] is not None:
            target_path = _record_project_path(target, records)
            if target_path is None or target_path[1] != root["path_ref"]:
                return False
        return True

    if source_id not in records:
        return False
    source = records[source_id]
    if source_id == target_id:
        return False
    if rule == "file_all_records":
        if source["kind"] not in {"file", "module"} or target["kind"] == "project":
            return False
        source_path = _record_project_path(source, records)
        target_path = _record_project_path(target, records)
        return source_path is not None and source_path == target_path
    if rule == "incoming_reexport":
        return (
            source["kind"] in {"module", "export_binding", "import_binding"}
            and target["kind"] in {"module", "export_binding", "import_binding"}
            and (source_id in _record_references(target) or target_id in _record_references(source))
            and (
                target.get("reexport") is True
                or source.get("reexport") is True
                or target["kind"] == "module"
            )
        )
    if rule == "value_import_dependency":
        return (
            target["kind"] in {"import_binding", "static_import"}
            and target.get("role") == "value"
            and source_id in _record_references(target)
        )
    if rule == "component_flow":
        return (
            source["kind"] == "component"
            and target["kind"] in {"jsx_render", "component_wrap"}
            and target.get("source_id") == source_id
        ) or (
            target["kind"] == "component"
            and source["kind"] in {"jsx_render", "component_wrap"}
            and target_id in _record_references(source)
        )
    if rule == "boundary_closure":
        return (
            source["kind"] in {"module", "static_import"}
            and target["kind"]
            in {
                "module",
                "static_import",
                "literal_dynamic_import",
                "client_entry",
                "router_context",
            }
            and (source_id in _record_references(target) or target_id in _record_references(source))
        )
    if rule == "type_subtree":
        return (
            source["kind"] in {"component", "prop"}
            and target["kind"] in {"component", "prop"}
            and _record_project_path(source, records) == _record_project_path(target, records)
        )
    if rule == "identity_dependency":
        return source_id in _record_references(target)
    if rule == "relation_dependency":
        return source["kind"] in {
            "static_import",
            "literal_dynamic_import",
            "jsx_render",
            "component_wrap",
        } and target_id in _record_references(source)
    return False


def _record_edge_rule(source: dict[str, Any], target: dict[str, Any]) -> str | None:
    """Return the one closed rule for a reachable record pair."""

    if source["id"] == target["id"]:
        return None
    source_kind = source["kind"]
    target_kind = target["kind"]
    if (
        source_kind == "component"
        and target_kind in {"jsx_render", "component_wrap"}
        and target.get("source_id") == source["id"]
    ):
        return "component_flow"
    if (
        source_kind in {"jsx_render", "component_wrap"}
        and target_kind == "component"
        and target["id"] in _record_references(source)
    ):
        return "relation_dependency"
    if (
        source_kind in {"component", "prop"}
        and target_kind in {"component", "prop"}
        and (
            (source_kind == "component" and target.get("owner_id") == source["id"])
            or (target_kind == "component" and target["id"] == source.get("owner_id"))
        )
    ):
        return "type_subtree"
    if (
        source_kind in {"module", "static_import", "literal_dynamic_import"}
        and target_kind
        in {"module", "static_import", "literal_dynamic_import", "client_entry", "router_context"}
        and (
            source.get("boundary_effect") == "server_to_client_entry"
            or target.get("boundary_effect") == "server_to_client_entry"
        )
        and (
            target["id"] in _record_references(source) or source["id"] in _record_references(target)
        )
    ):
        return "boundary_closure"
    if source_kind in {"static_import", "literal_dynamic_import"} and target[
        "id"
    ] in _record_references(source):
        return "relation_dependency"
    if (
        target_kind in {"import_binding", "static_import"}
        and target.get("role") == "value"
        and source["id"] in _record_references(target)
    ):
        return "value_import_dependency"
    if source["id"] in _record_references(target):
        return "identity_dependency"
    return None


def _derive_required_root_seed_ids(
    root: dict[str, Any], records: dict[str, dict[str, Any]]
) -> list[str]:
    """Derive a root's complete mandatory seed set from records.

    ``failure_root.record_ids`` is only a submitted witness.  In particular,
    an export failure must seed its target component, the explicit incoming
    re-export/barrel path, and bindings that depend on the affected module or
    component; accepting a caller-selected subset would permit under-taint.
    """

    path_ref = root["path_ref"]
    if path_ref is None:
        if root["kind"] == "boundary_derivation":
            return sorted(
                record_id
                for record_id, record in records.items()
                if record["kind"] == "module"
                and "server_candidate" in record.get("derived_roles", [])
            )
        if root["kind"] == "export_binding":
            return sorted(
                record_id
                for record_id, record in records.items()
                if record["kind"] == "export_binding"
            )
        if root["kind"] in {"type_symbol", "props_subtree"}:
            return sorted(
                record_id
                for record_id, record in records.items()
                if record["kind"] in {"component", "prop"}
            )
        if root["kind"] == "component_flow":
            return sorted(
                record_id for record_id, record in records.items() if record["kind"] == "component"
            )
        if root["kind"] == "module_relation":
            return sorted(
                record_id for record_id, record in records.items() if record["kind"] == "module"
            )
        return []

    def on_path(record: dict[str, Any]) -> bool:
        record_path = _record_project_path(record, records)
        return record_path is not None and record_path[1] == path_ref

    if root["kind"] in {"parse_file", "read_file"}:
        return sorted(record_id for record_id, record in records.items() if on_path(record))

    if root["kind"] in {"type_symbol", "props_subtree"}:
        return sorted(
            record_id
            for record_id, record in records.items()
            if on_path(record) and record["kind"] in {"component", "prop"}
        )

    if root["kind"] == "export_binding":
        modules = {
            record_id
            for record_id, record in records.items()
            if record["kind"] == "module" and on_path(record)
        }
        exports = {
            record_id: record
            for record_id, record in records.items()
            if record["kind"] == "export_binding" and record["owner_id"] in modules
        }
        seed: set[str] = set(modules) | set(exports)
        target_components = {
            record["target_component_id"]
            for record in exports.values()
            if record["resolution_kind"] == "component"
        }
        seed.update(target_components)
        target_modules = {
            records[component_id]["module_id"]
            for component_id in target_components
            if component_id in records
        }
        seed.update(target_modules)

        # An explicit re-export is represented by the incoming static edge;
        # include the barrel and its binding records as root evidence too.
        incoming_reexports = {
            record_id: record
            for record_id, record in records.items()
            if record["kind"] == "static_import"
            and record.get("reexport") is True
            and record.get("target", {}).get("kind") == "internal"
            and record["target"].get("module_id") in (modules | target_modules)
        }
        seed.update(incoming_reexports)
        barrel_modules = {record["source_id"] for record in incoming_reexports.values()}
        seed.update(barrel_modules)
        seed.update(
            record_id
            for record_id, record in records.items()
            if record["kind"] in {"export_binding", "import_binding"}
            and record["owner_id"] in barrel_modules
        )

        # Include consumer bindings that explicitly refer to the affected
        # module/component, regardless of where the consumer file lives.
        seed.update(
            record_id
            for record_id, record in records.items()
            if record["kind"] == "import_binding"
            and (
                record.get("local_component_id") in target_components
                or (
                    record.get("source", {}).get("kind") == "internal"
                    and record["source"].get("module_id") in (modules | target_modules)
                )
            )
        )
        seed.update(
            record["owner_id"]
            for record in records.values()
            if record["kind"] == "import_binding"
            and record["id"] in seed
            and record["owner_id"] in records
        )
        return sorted(seed)

    kind_to_records = {
        "component_flow": {"component", "jsx_render", "component_wrap"},
        "module_relation": {"module", "static_import", "literal_dynamic_import"},
        "boundary_derivation": {
            "module",
            "static_import",
            "literal_dynamic_import",
            "client_entry",
            "router_context",
        },
    }
    allowed = kind_to_records.get(root["kind"], set())
    return sorted(
        record_id
        for record_id, record in records.items()
        if on_path(record) and record["kind"] in allowed
    )


def derive_required_causal_edges(
    proof: dict[str, Any], discovered: dict[str, dict[str, dict[str, Any]]]
) -> list[dict[str, str]]:
    """Generate the mandatory taint witness from roots and record ownership.

    This is deliberately independent of adapter-provided ``taints`` and
    ``causal_edges``.  Only records reachable from a root are expanded, while
    every expansion rule is selected from the closed table above.
    """

    records = _record_index(discovered)
    roots = {root["id"]: root for root in proof["failure_roots"]}
    edges: dict[tuple[str, str], dict[str, str]] = {}
    pending: list[str] = []
    reachable: set[str] = set()

    for root_id in sorted(roots):
        root = roots[root_id]
        seed_ids = root["record_ids"]
        assert seed_ids == sorted(set(seed_ids))
        assert all(seed_id in records for seed_id in seed_ids)
        required_seed_ids = _derive_required_root_seed_ids(root, records)
        assert seed_ids == required_seed_ids
        candidates = [records[seed_id] for seed_id in required_seed_ids]
        for target in sorted(candidates, key=lambda item: item["id"]):
            root_rule = TAINT_ROOT_RULES[root["kind"]]
            assert root_rule in TAINT_EDGE_RULES
            edge = {
                "source_id": root_id,
                "record_id": target["id"],
                "rule": root_rule,
            }
            assert _causal_edge_is_allowed(edge, records, roots)
            edges[(root_id, target["id"])] = edge
            if target["id"] not in reachable:
                reachable.add(target["id"])
                pending.append(target["id"])

    while pending:
        source_id = pending.pop()
        source = records[source_id]
        for target in sorted(records.values(), key=lambda item: item["id"]):
            edge_rule = _record_edge_rule(source, target)
            if edge_rule is None:
                continue
            assert edge_rule in TAINT_EDGE_RULES
            edge = {
                "source_id": source_id,
                "record_id": target["id"],
                "rule": edge_rule,
            }
            assert _causal_edge_is_allowed(edge, records, roots)
            key = (source_id, target["id"])
            if key not in edges:
                edges[key] = edge
            if target["id"] not in reachable:
                reachable.add(target["id"])
                pending.append(target["id"])
    result = list(edges.values())
    result.sort(key=canonical_json_bytes)
    return result


def _derived_taint_fixed_point(
    proof: dict[str, Any],
    discovered: dict[str, dict[str, dict[str, Any]]],
) -> set[str]:
    """Derive tainted records solely from roots and validated causal edges."""

    records = _record_index(discovered)
    roots = {root["id"]: root for root in proof["failure_roots"]}
    assert len(roots) == len(proof["failure_roots"])
    edges = proof["causal_edges"]
    assert edges == derive_required_causal_edges(proof, discovered)
    adjacency: dict[str, set[str]] = {}
    for edge in edges:
        assert edge["record_id"] in records
        assert _causal_edge_is_allowed(edge, records, roots)
        adjacency.setdefault(edge["source_id"], set()).add(edge["record_id"])

    reachable: set[str] = set()
    reachable_sources = set(roots)
    pending = list(roots)
    while pending:
        source_id = pending.pop()
        for target_id in adjacency.get(source_id, set()):
            if target_id in reachable:
                continue
            reachable.add(target_id)
            reachable_sources.add(target_id)
            pending.append(target_id)
    assert all(edge["source_id"] in reachable_sources for edge in edges)
    expected_taints: dict[str, set[str]] = {}
    pending_pairs = [(root_id, roots[root_id]["kind"]) for root_id in roots if root_id in adjacency]
    while pending_pairs:
        source_id, taint = pending_pairs.pop()
        for target_id in adjacency.get(source_id, set()):
            taints = expected_taints.setdefault(target_id, set())
            if taint in taints:
                continue
            taints.add(taint)
            pending_pairs.append((target_id, taint))
    for record_id in (
        record_id
        for records_by_collection in discovered.values()
        for record_id in records_by_collection
    ):
        proof_item = next(
            proof_item
            for proof_item in proof["discovered_records"]
            if proof_item["record_id"] == record_id
        )
        assert set(proof_item["taints"]) == expected_taints.get(record_id, set())
    return reachable


def validate_model(
    model: dict[str, Any],
    *,
    max_model_records: int = LIMIT_DEFAULTS["max_model_records"],
    allowed_missing_module_keys: set[tuple[str, str]] | None = None,
    allowed_missing_module_ids: set[str] | None = None,
) -> int:
    allowed_missing_module_keys = allowed_missing_module_keys or set()
    allowed_missing_module_ids = allowed_missing_module_ids or set()
    collections = _validate_model_collections(model)
    project_records = collections["projects"]
    file_records = collections["files"]
    module_records = collections["modules"]
    component_records = collections["components"]
    member_records = collections["members"]
    relation_records = collections["relations"]
    fact_records = collections["facts"]

    roots: list[tuple[str, str]] = []
    for project in project_records.values():
        assert project["kind"] == "project"
        assert project["config_digest"] == project_config_digest(project)
        _assert_path(project["root"])
        for other_root, other_id in roots:
            assert not _under(project["root"], other_root)
            assert not _under(other_root, project["root"])
            assert project["id"] != other_id
        roots.append((project["root"], project["id"]))
        assert project["file_ids"] == sorted(project["file_ids"])
        assert all(_id_kind(file_id) == "file" for file_id in project["file_ids"])
        assert project["source_roots"] == sorted(project["source_roots"])
        assert len(project["source_roots"]) == len(set(project["source_roots"]))
        for source_root in project["source_roots"]:
            _assert_path(source_root)
            assert _under(source_root, project["root"])
        if project["config_path"] is not None:
            _assert_file_path(project["config_path"])
            assert _under(project["config_path"], project["root"])

    files_by_project: dict[str, list[str]] = {project_id: [] for project_id in project_records}
    for file_record in file_records.values():
        assert file_record["kind"] == "file"
        assert file_record["project_id"] in project_records
        _assert_file_path(file_record["path"])
        matching_roots = [
            project_id for root, project_id in roots if _under(file_record["path"], root)
        ]
        assert matching_roots == [file_record["project_id"]]
        roles = file_record["roles"]
        assert roles and set(roles) <= set(ROLES)
        assert len(roles) == len(set(roles))
        assert roles == sorted(roles, key=ROLE_ORDER.__getitem__)
        assert file_record["effective_role"] == max(roles, key=ROLE_PRECEDENCE.__getitem__)
        files_by_project[file_record["project_id"]].append(file_record["id"])
    for project_id, project in project_records.items():
        assert project["file_ids"] == sorted(files_by_project[project_id])

    files_by_key = {(file["project_id"], file["path"]): file for file in file_records.values()}
    assert len(files_by_key) == len(file_records)
    modules_by_key: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for module in module_records.values():
        modules_by_key.setdefault((module["project_id"], module["path"]), []).append(module)
    for module in module_records.values():
        assert module["kind"] == "module"
        assert module["project_id"] in project_records
        _assert_file_path(module["path"])
        assert module["derived_roles"] == sorted(module["derived_roles"])
        assert len(module["derived_roles"]) == len(set(module["derived_roles"]))
        owner_file = files_by_key.get((module["project_id"], module["path"]))
        assert owner_file is not None
        assert _is_program_file(owner_file)
    invalid_module_keys = [
        key
        for key, candidates in modules_by_key.items()
        if len(candidates) > 1 or (len(candidates) == 0 and key not in allowed_missing_module_keys)
    ]
    if invalid_module_keys:
        module_target_reasons = {
            key: "duplicate" if len(candidates) > 1 else "missing"
            for key, candidates in modules_by_key.items()
        }
        raise NextTargetCompletenessFailure(
            [
                {
                    "target_key": f"path:{path}",
                    "reason": module_target_reasons[(project_id, path)],
                }
                for project_id, path in invalid_module_keys
            ]
        )
    for file_record in file_records.values():
        module_key = (file_record["project_id"], file_record["path"])
        if _is_program_file(file_record) and (
            len(modules_by_key.get(module_key, [])) != 1
            and module_key not in allowed_missing_module_keys
        ):
            raise NextTargetCompletenessFailure(
                [
                    {
                        "target_key": f"path:{file_record['path']}",
                        "reason": (
                            "component_only"
                            if any(
                                component["module_id"]
                                == recompute_record_id(
                                    {
                                        "kind": "module",
                                        "project_id": file_record["project_id"],
                                        "path": file_record["path"],
                                    }
                                )
                                for component in component_records.values()
                            )
                            else "missing"
                        ),
                    }
                ]
            )
    for component in component_records.values():
        assert component["kind"] == "component"
        assert (
            component["module_id"] in module_records
            or component["module_id"] in allowed_missing_module_ids
        )
        assert is_binding_identifier(component["declaration_key"])
        _assert_canonical(component["recognition_evidence"])
    _assert_unique(
        [
            (component["module_id"], component["declaration_key"])
            for component in component_records.values()
        ]
    )

    member_keys: list[Any] = []
    component_signature_counts: dict[str, int] = {}
    for member in member_records.values():
        if member["kind"] == "export_binding":
            assert member["owner_id"] in module_records
            assert _is_export_identifier(
                member["exported_name"], allow_default=True, allow_keyword=True
            )
            assert member["resolution_kind"] in {"component", "value", "type"}
            if member["resolution_kind"] == "component":
                assert member["role"] == "value"
                assert member["target_component_id"] in component_records
            elif member["resolution_kind"] == "value":
                assert member["role"] == "value"
                assert member["target_component_id"] is None
            else:
                assert member["role"] == "type"
                assert member["target_component_id"] is None
            member_keys.append((member["kind"], member["owner_id"], member["exported_name"]))
        elif member["kind"] == "import_binding":
            assert member["owner_id"] in module_records
            assert _is_export_identifier(
                member["imported_name"], allow_default=True, allow_keyword=True
            )
            if member["local_component_id"] is not None:
                assert member["local_component_id"] in component_records
            source = member["source"]
            if source["kind"] == "internal":
                assert source["module_id"] in module_records
            else:
                _assert_external_target(source)
            member_keys.append(
                (
                    member["kind"],
                    member["owner_id"],
                    member["imported_name"],
                    member["role"],
                    tuple(sorted(source.items())),
                )
            )
        else:
            assert member["kind"] == "prop"
            assert member["owner_id"] in component_records
            assert is_declaration_key(member["name"])
            type_state: dict[str, int] = {
                "nodes": 0,
                "properties": 0,
                "union_members": 0,
                "intersection_members": 0,
                "signatures": 0,
            }
            _validate_type_node(member["type_node"], set(module_records), _state=type_state)
            component_signature_counts[member["owner_id"]] = (
                component_signature_counts.get(member["owner_id"], 0) + type_state["signatures"]
            )
            assert (
                component_signature_counts[member["owner_id"]]
                <= LIMIT_DEFAULTS["max_signatures_per_component"]
            )
            member_keys.append((member["kind"], member["owner_id"], member["name"]))
    _assert_unique(member_keys)

    relation_keys: list[Any] = []
    for relation in relation_records.values():
        if relation["kind"] in {"static_import", "literal_dynamic_import"}:
            assert relation["source_id"] in module_records
            target = relation["target"]
            if target["kind"] == "internal":
                assert target["module_id"] in module_records
            else:
                _assert_external_target(target)
            if relation["kind"] == "literal_dynamic_import":
                assert relation["role"] == "value"
                assert relation["reexport"] is False
                assert relation["boundary_effect"] == "none"
            elif relation["boundary_effect"] == "server_to_client_entry":
                assert relation["role"] == "value"
                assert target["kind"] == "internal"
                assert module_records[relation["source_id"]]["client_entry"] is False
                assert "server_candidate" in module_records[relation["source_id"]]["derived_roles"]
                assert module_records[target["module_id"]]["client_entry"] is True
            else:
                assert relation["boundary_effect"] == "none"
            assert relation["role"] in {"value", "type"}
            assert isinstance(relation["reexport"], bool)
            relation_keys.append(
                (
                    relation["kind"],
                    relation["source_id"],
                    relation["role"],
                    relation["reexport"],
                    relation["boundary_effect"],
                    tuple(sorted(target.items())),
                )
            )
        elif relation["kind"] == "jsx_render":
            assert relation["source_id"] in component_records
            target = relation["target"]
            if target["kind"] == "internal":
                assert target["component_id"] in component_records
            else:
                _assert_external_target(target)
            assert relation["occurrence_count"] >= 1
            assert relation["contexts"] == sorted(set(relation["contexts"]))
            relation_keys.append(
                (
                    relation["kind"],
                    relation["source_id"],
                    tuple(sorted(target.items())),
                )
            )
        else:
            assert relation["kind"] == "component_wrap"
            assert relation["source_id"] in component_records
            assert relation["target_component_id"] in component_records
            assert relation["occurrence_count"] >= 1
            assert relation["contexts"] == ["direct"]
            relation_keys.append(
                (
                    relation["kind"],
                    relation["source_id"],
                    relation["target_component_id"],
                )
            )
    _assert_unique(relation_keys)

    fact_keys: list[Any] = []
    for fact in fact_records.values():
        assert fact["owner_id"] in module_records
        if fact["kind"] == "client_entry":
            assert fact["value"] is True
            assert module_records[fact["owner_id"]]["client_entry"] is True
        else:
            assert fact["kind"] == "router_context"
            assert fact["value"] in {"app_ui", "app_route_handler", "pages_ui", "pages_api", "none"}
            assert module_records[fact["owner_id"]]["router_context"] == fact["value"]
        fact_keys.append((fact["kind"], fact["owner_id"]))
    _assert_unique(fact_keys)

    expected_facts = {
        ("client_entry", module_id, True)
        for module_id, module in module_records.items()
        if module["client_entry"]
    }
    expected_facts.update(
        ("router_context", module_id, module["router_context"])
        for module_id, module in module_records.items()
    )
    actual_facts = {
        (fact["kind"], fact["owner_id"], fact["value"]) for fact in fact_records.values()
    }
    assert actual_facts == expected_facts

    expected_boundary_roles = derive_boundary_roles(model)
    for module_id, module in module_records.items():
        assert module["derived_roles"] == expected_boundary_roles[module_id]

    _validate_model_diagnostics(model["diagnostics"])

    counts = model["coverage"]["counts"]
    opaque_counts: dict[str, int] = {}
    for member in member_records.values():
        if member["kind"] != "prop":
            continue
        for reason, count in _opaque_reason_counts(member["type_node"]).items():
            opaque_counts[reason] = opaque_counts.get(reason, 0) + count
    assert model["coverage"]["opaque_reason_counts"] == opaque_counts
    for collection in COLLECTIONS:
        assert counts[collection] == len(collections[collection])
        assert counts[collection] <= LIMIT_DEFAULTS["max_collection_items"]
    assert counts["internal_entities"] == len(module_records) + len(component_records)
    assert counts["published"] == sum(len(collections[collection]) for collection in COLLECTIONS)
    assert counts["published"] <= counts["discovered"]
    assert counts["discovered"] <= max_model_records
    assert counts["excluded"] >= 0
    assert counts["failed"] >= 0
    return len(module_records) + len(component_records)


def validate_request_files(request: dict[str, Any]) -> None:
    _assert_target_keys(request["targets"])
    assert len(request["files"]) <= LIMIT_DEFAULTS["max_files"]
    project_ids = [project["id"] for project in request["projects"]]
    assert len(project_ids) == len(set(project_ids))
    assert all(_id_kind(project_id) == "project" for project_id in project_ids)
    roots = [(project["root"], project["id"]) for project in request["projects"]]
    assert roots == sorted(roots, key=lambda item: canonical_json_bytes(item[0]))
    for index, (root, project_id) in enumerate(roots):
        assert request["projects"][index]["kind"] == "project"
        assert request["projects"][index]["config_digest"] == project_config_digest(
            request["projects"][index]
        )
        assert recompute_record_id(request["projects"][index]) == project_id
        _assert_path(root)
        for source_root in request["projects"][index]["source_roots"]:
            _assert_path(source_root)
            assert _under(source_root, root)
        config_path = request["projects"][index]["config_path"]
        if config_path is not None:
            _assert_file_path(config_path)
            assert _under(config_path, root)
        for other_root, other_id in roots[:index]:
            assert project_id != other_id
            assert not _under(root, other_root)
            assert not _under(other_root, root)
    file_ids = [file_record["id"] for file_record in request["files"]]
    assert file_ids == sorted(file_ids)
    assert len(file_ids) == len(set(file_ids))
    assert all(_id_kind(file_id) == "file" for file_id in file_ids)
    project_set = set(project_ids)
    files_by_project: dict[str, list[str]] = {project_id: [] for project_id in project_ids}
    file_keys: list[tuple[str, str]] = []
    total_decoded_bytes = 0
    for file_record in request["files"]:
        assert file_record["kind"] == "file"
        assert recompute_record_id(file_record) == file_record["id"]
        assert file_record["project_id"] in project_set
        _assert_file_path(file_record["path"])
        matching_roots = [
            project_id for root, project_id in roots if _under(file_record["path"], root)
        ]
        assert matching_roots == [file_record["project_id"]]
        roles = file_record["roles"]
        assert roles and set(roles) <= set(ROLES)
        assert len(roles) == len(set(roles))
        assert roles == sorted(roles, key=ROLE_ORDER.__getitem__)
        assert file_record["effective_role"] == max(roles, key=ROLE_PRECEDENCE.__getitem__)
        files_by_project[file_record["project_id"]].append(file_record["id"])
        file_keys.append((file_record["project_id"], file_record["path"]))
        encoded = file_record["content_base64"]
        decoded = base64.b64decode(encoded, validate=True)
        assert base64.b64encode(decoded).decode("ascii") == encoded
        assert file_record["size_bytes"] == len(decoded)
        assert len(decoded) <= LIMIT_DEFAULTS["max_file_bytes"]
        assert hashlib.sha256(decoded).hexdigest() == file_record["sha256"]
        total_decoded_bytes += len(decoded)
    _assert_unique(file_keys)
    assert total_decoded_bytes <= LIMIT_DEFAULTS["max_decoded_bytes"]
    for project in request["projects"]:
        assert project["file_ids"] == sorted(files_by_project[project["id"]])


def _resolve_export_source_path(owner_path: str, source_specifier: str) -> str | None:
    """Resolve only the closed relative source specifier grammar."""

    if not source_specifier.startswith("."):
        return None
    owner_directory = owner_path.rsplit("/", 1)[0] if "/" in owner_path else ""
    candidate = f"{owner_directory}/{source_specifier}" if owner_directory else source_specifier
    parts: list[str] = []
    for part in candidate.split("/"):
        if part in {"", "."}:
            continue
        if part == "..":
            if not parts:
                return None
            parts.pop()
        else:
            parts.append(part)
    return "/".join(parts)


def recompute_export_graph_case(case: dict[str, Any]) -> dict[str, Any]:
    """Recompute re-export closure from frozen module declarations and edges.

    This resolver is deliberately independent of ``ExportBinding``.  It
    resolves explicit aliases, expands stars (excluding ``default``), and
    converts cycles or duplicate star names into an ``unknown`` result.  The
    returned witness is deterministic and is suitable for exact comparison
    with an adapter's graph observation.
    """

    modules = {module["path"]: module for module in case["modules"]}
    edges_by_owner: dict[str, list[dict[str, Any]]] = {path: [] for path in modules}
    for edge in case["edges"]:
        edges_by_owner[edge["owner_file_path"]].append(edge)
    for edges in edges_by_owner.values():
        edges.sort(key=canonical_json_bytes)

    def resolve_source(owner_path: str, source_specifier: str) -> str | None:
        candidate = _resolve_export_source_path(owner_path, source_specifier)
        if candidate is None:
            return None
        for suffix in ("", ".ts", ".tsx", ".js", ".jsx"):
            path = candidate if suffix == "" else candidate + suffix
            if path in modules:
                return path
        return None

    cycles: set[tuple[str, str]] = set()
    conflicts: set[tuple[str, str]] = set()

    cycle_reachability: dict[str, bool] = {}

    def reaches_cycle(module_path: str, visiting: set[str] | None = None) -> bool:
        """Determine whether a module's export graph reaches a module cycle."""

        cached = cycle_reachability.get(module_path)
        if cached is not None:
            return cached
        active = visiting or set()
        if module_path in active:
            return True
        active = active | {module_path}
        result = any(
            source_path is not None and reaches_cycle(source_path, active)
            for edge in edges_by_owner[module_path]
            for source_path in [resolve_source(module_path, edge["source_specifier"])]
        )
        cycle_reachability[module_path] = result
        return result

    def unknown(source_path: str | None, reason: str) -> dict[str, Any]:
        return {
            "source_file_path": source_path,
            "expanded_exported_name": None,
            "target_declaration_key": None,
            "resolution": "unknown",
            "reason": reason,
        }

    def module_exports(
        module_path: str,
        active_symbols: set[tuple[str, str]],
        active_modules: set[str],
    ) -> dict[str, dict[str, Any]]:
        if module_path in active_modules:
            cycles.add((module_path, "*"))
            return {}
        module = modules[module_path]
        candidates: dict[str, list[dict[str, Any]]] = {}
        for direct in module["exports"]:
            candidates.setdefault(direct["name"], []).append(
                {
                    "source_file_path": module_path,
                    "expanded_exported_name": direct["name"],
                    "target_declaration_key": direct["target_declaration_key"],
                    "resolution": direct["resolution"],
                    "reason": None,
                }
            )
        next_modules = active_modules | {module_path}
        for edge in edges_by_owner[module_path]:
            source_path = resolve_source(module_path, edge["source_specifier"])
            if source_path is None:
                if edge["imported_name"] == "*":
                    candidates.setdefault("*", []).append(unknown(None, "missing_source"))
                else:
                    candidates.setdefault(edge["exported_name"], []).append(
                        unknown(None, "missing_source")
                    )
                continue
            if edge["imported_name"] == "*":
                source_exports = module_exports(source_path, active_symbols, next_modules)
                for name, candidate in source_exports.items():
                    if name != "default":
                        candidates.setdefault(name, []).append(candidate)
                continue
            symbol = (source_path, edge["imported_name"])
            if symbol in active_symbols:
                cycles.add(symbol)
                candidate = unknown(source_path, "cycle")
            else:
                source_exports = module_exports(
                    source_path,
                    active_symbols | {(module_path, edge["exported_name"])},
                    next_modules,
                )
                resolved_candidate = source_exports.get(edge["imported_name"])
                if resolved_candidate is None:
                    resolved_candidate = unknown(source_path, "missing_export")
                candidate = resolved_candidate
            candidates.setdefault(edge["exported_name"], []).append(candidate)

        resolved: dict[str, dict[str, Any]] = {}
        for name, candidate_list in candidates.items():
            if name == "*":
                continue
            if len(candidate_list) != 1:
                conflicts.add((module_path, name))
                resolved[name] = unknown(module_path, "conflict")
            else:
                resolved[name] = candidate_list[0]
        return resolved

    tables = {path: module_exports(path, set(), set()) for path in sorted(modules)}
    witnesses: list[dict[str, Any]] = []
    for edge in case["edges"]:
        owner = edge["owner_file_path"]
        source_path = resolve_source(owner, edge["source_specifier"])
        owner_exports = tables[owner]
        expanded_names: list[str | None]
        if edge["imported_name"] == "*":
            expanded_names = cast(
                list[str | None],
                sorted(
                    name
                    for name in (tables[source_path] if source_path is not None else {})
                    if name != "default"
                ),
            )
            if not expanded_names and (source_path is None or reaches_cycle(source_path)):
                expanded_names = [None]
        else:
            expanded_names = [edge["exported_name"]]
        for expanded_name in expanded_names:
            result: dict[str, Any] | None
            if expanded_name is None:
                result = unknown(
                    source_path,
                    "cycle"
                    if source_path is not None and reaches_cycle(source_path)
                    else "missing_source",
                )
            else:
                result = owner_exports.get(expanded_name)
            if result is None:
                result = unknown(source_path, "missing_export")
            witness = {
                "owner_file_path": owner,
                "source_specifier": edge["source_specifier"],
                "imported_name": edge["imported_name"],
                "original_exported_name": edge["exported_name"],
                "exported_name": expanded_name,
                "resolved_source_file_path": source_path,
                "expanded_exported_name": result["expanded_exported_name"],
                "target_declaration_key": result["target_declaration_key"],
                "resolution": result["resolution"],
                "diagnostic": result["reason"],
            }
            for field in ("syntax_identity", "byte_start", "byte_end"):
                if field in edge:
                    witness[field] = edge[field]
            witnesses.append(witness)
    return {
        "exports": [
            {
                "module_file_path": path,
                "exported_name": name,
                **table[name],
            }
            for path, table in tables.items()
            for name in sorted(table)
        ],
        "witnesses": sorted(witnesses, key=canonical_json_bytes),
        "cycles": [
            {"module_file_path": path, "exported_name": name} for path, name in sorted(cycles)
        ],
        "conflicts": [
            {"module_file_path": path, "exported_name": name} for path, name in sorted(conflicts)
        ],
    }


def _reexport_join_key(row: dict[str, Any]) -> tuple[str, str, str, str, str, int, int]:
    """Return the physical identity shared by syntax rows and raw graph edges."""

    return (
        row["owner_file_path"],
        row["source_specifier"],
        row["imported_name"],
        row.get("original_exported_name", row["exported_name"]),
        row["syntax_identity"],
        row["byte_start"],
        row["byte_end"],
    )


def join_reexport_observations_to_edges(
    syntax_rows: list[dict[str, Any]],
    raw_edges: list[dict[str, Any]],
    *,
    owner_paths: set[str] | None = None,
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Perform a bijective physical join of source observations and raw edges.

    ``(owner, specifier, imported, exported, syntax identity, byte span)`` is
    intentionally stronger than a semantic name lookup.  It distinguishes
    ``Foo as A`` from ``Foo as B`` and also distinguishes repeated ``Foo as A``
    statements.  Every selected syntax row and every selected raw edge is
    consumed exactly once; an empty-star edge is still joined even though it
    later expands to zero witness rows.
    """

    selected_syntax = [
        row
        for row in syntax_rows
        if row.get("reexport") and (owner_paths is None or row["owner_file_path"] in owner_paths)
    ]
    selected_edges = [
        edge for edge in raw_edges if owner_paths is None or edge["owner_file_path"] in owner_paths
    ]
    syntax_by_key: dict[tuple[str, str, str, str, str, int, int], dict[str, Any]] = {}
    for row in selected_syntax:
        key = _reexport_join_key(row)
        assert key not in syntax_by_key
        syntax_by_key[key] = row
    edges_by_key: dict[tuple[str, str, str, str, str, int, int], dict[str, Any]] = {}
    for edge in selected_edges:
        key = _reexport_join_key(edge)
        assert key not in edges_by_key
        edges_by_key[key] = edge
    assert set(syntax_by_key) == set(edges_by_key)
    return [
        (syntax_by_key[key], edges_by_key[key])
        for key in sorted(syntax_by_key, key=canonical_json_bytes)
    ]


def _reexport_graph_index() -> dict[tuple[str, str, str, str, str, int, int], list[dict[str, Any]]]:
    """Derive the main fixture graph from raw declarations and edges."""

    raw = load_export_graph_raw_fixture()
    result = recompute_export_graph_case(raw)
    index: dict[tuple[str, str, str, str, str, int, int], list[dict[str, Any]]] = {}
    for witness in result["witnesses"]:
        key = _reexport_join_key(witness)
        index.setdefault(key, []).append(witness)
    for witnesses in index.values():
        witnesses.sort(key=canonical_json_bytes)
    return index


def _terminal_export_source_path(
    graph_witness: dict[str, Any], graph_result: dict[str, Any]
) -> str | None:
    """Follow one graph export to its physical declaration module.

    ``resolved_source_file_path`` identifies the immediate module named by
    the edge.  An alias chain can continue through that module, so component
    identity and the public witness must use the terminal ``source_file_path``
    from the independently recomputed export table.
    """

    immediate_path = cast(str | None, graph_witness["resolved_source_file_path"])
    if immediate_path is None:
        return None
    lookup_name = cast(
        str | None,
        (
            graph_witness["expanded_exported_name"]
            if graph_witness["imported_name"] == "*"
            else graph_witness["imported_name"]
        ),
    )
    if lookup_name is None:
        return immediate_path
    for export in graph_result["exports"]:
        if export["module_file_path"] == immediate_path and export["exported_name"] == lookup_name:
            return cast(str, export["source_file_path"])
    return immediate_path


def _export_syntax_rows_for_model(model: dict[str, Any]) -> list[dict[str, Any]]:
    """Scan the frozen fixture bytes under each model module's exact path."""

    fixture_by_path = {item["path"]: item for item in load_export_census_fixture()}
    rows: list[dict[str, Any]] = []
    for module in model["modules"]:
        fixture = fixture_by_path.get(module["path"])
        if fixture is None:
            fixture = next(
                (
                    item
                    for path, item in fixture_by_path.items()
                    if module["path"].endswith(f"/{path}")
                ),
                None,
            )
        assert fixture is not None
        rows.extend(
            _scan_export_file(
                cast(str, module["path"]),
                cast(bytes, fixture["content"]),
            )
        )
    return sorted(rows, key=canonical_json_bytes)


def _export_census_for_model(model: dict[str, Any]) -> list[dict[str, Any]]:
    """Bind frozen source syntax rows to modules and a separate graph witness."""

    files_by_path = {(file["project_id"], file["path"]): file for file in model["files"]}
    modules_by_path = {module["path"]: module for module in model["modules"]}
    assert len(modules_by_path) == len(model["modules"])
    fixture_by_path = {item["path"]: item for item in load_export_census_fixture()}
    for module in model["modules"]:
        file = files_by_path.get((module["project_id"], module["path"]))
        assert file is not None
        assert _is_program_file(file)
        fixture = fixture_by_path.get(module["path"])
        if fixture is None:
            fixture = next(
                (
                    item
                    for path, item in fixture_by_path.items()
                    if module["path"].endswith(f"/{path}")
                ),
                None,
            )
        assert fixture is not None
        content = cast(bytes, fixture["content"])
        assert file["size_bytes"] == len(content)
        assert file["sha256"] == hashlib.sha256(content).hexdigest()

    components_by_module: dict[str, list[dict[str, Any]]] = {}
    for component_record in model["components"]:
        components_by_module.setdefault(component_record["module_id"], []).append(component_record)
    for components in components_by_module.values():
        components.sort(key=canonical_json_bytes)
    graph = _reexport_graph_index()
    graph_result = recompute_export_graph_case(load_export_graph_raw_fixture())
    syntax_rows = _export_syntax_rows_for_model(model)
    module_paths = set(modules_by_path)
    raw_edges = load_export_graph_raw_fixture()["edges"]
    raw_owner_paths = {edge["owner_file_path"] for edge in raw_edges} & module_paths
    joined_reexports = join_reexport_observations_to_edges(
        syntax_rows,
        raw_edges,
        owner_paths=raw_owner_paths,
    )
    edge_by_syntax_key = {_reexport_join_key(syntax): edge for syntax, edge in joined_reexports}

    observations: list[dict[str, Any]] = []
    for syntax in _export_syntax_rows_for_model(model):
        module = modules_by_path.get(syntax["owner_file_path"])
        if module is None:
            # Context/control and grammar-only fixtures are scanned but do not
            # acquire semantic Module ownership.
            continue
        candidates = components_by_module.get(module["id"], [])
        graph_witnesses: list[dict[str, Any]] | None
        if syntax["reexport"]:
            edge = edge_by_syntax_key.get(_reexport_join_key(syntax))
            if edge is None:
                # A rebased/independent project can contain the same fixture
                # bytes under a different physical owner path.  It remains a
                # valid source observation, but no frozen raw graph edge owns
                # that path and therefore no graph witness may be borrowed.
                graph_witnesses = []
            else:
                graph_key = _reexport_join_key(edge)
                graph_witnesses = [
                    witness
                    for key, witnesses in graph.items()
                    if key == graph_key
                    for witness in witnesses
                ]
            if not syntax["star"] and edge is not None:
                assert len(graph_witnesses) == 1
        else:
            graph_witnesses = None
        source_path = (
            _terminal_export_source_path(graph_witnesses[0], graph_result)
            if graph_witnesses
            else _resolve_export_source_path(syntax["owner_file_path"], syntax["source_specifier"])
            if syntax["source_specifier"] is not None
            else None
        )
        source_module = modules_by_path.get(source_path) if source_path is not None else module
        source_components = (
            components_by_module.get(source_module["id"], []) if source_module else []
        )
        declaration_key = (
            graph_witnesses[0]["target_declaration_key"]
            if graph_witnesses and not syntax["star"]
            else syntax["imported_name"]
            if syntax["imported_name"] not in {None, "*", "default"}
            else syntax["exported_name"]
        )
        component: dict[str, Any] | None = None
        if syntax["role"] == "value" and not syntax["star"]:
            component = next(
                (
                    candidate
                    for candidate in source_components
                    if candidate["declaration_key"] == declaration_key
                ),
                None,
            )
            if (
                component is None
                and syntax["exported_name"] == "default"
                and source_module is module
                and len(candidates) == 1
            ):
                component = candidates[0]
        if graph_witnesses and not syntax["star"]:
            resolution = graph_witnesses[0]["resolution"]
            expanded_name = graph_witnesses[0]["expanded_exported_name"]
        else:
            resolution = (
                "component"
                if component is not None
                else "type"
                if syntax["role"] == "type"
                else "unknown"
                if syntax["star"]
                else "value"
            )
            expanded_name = None if syntax["star"] else syntax["exported_name"]
        target_component_id = component["id"] if resolution == "component" and component else None
        observations.append(
            {
                "owner_module_id": module["id"],
                **syntax,
                "resolution": resolution,
                "component_id": target_component_id,
                "target_declaration_id": target_component_id,
                "resolved_source_module_id": source_module["id"] if source_module else None,
                "expanded_exported_name": expanded_name,
            }
        )
    observations.sort(key=canonical_json_bytes)
    return observations


def expected_export_resolution_witness(model: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the TypeChecker resolution witness for public component bindings."""

    public = _export_binding_projection_for_model(model)
    members = {
        (
            member["owner_id"],
            member["exported_name"],
            member["role"],
        ): member
        for member in model["members"]
        if member["kind"] == "export_binding"
    }
    witnesses = []
    for binding in public:
        member = members.get((binding["owner_id"], binding["exported_name"], binding["role"]))
        assert member is not None
        witnesses.append(
            {
                "member_id": member["id"],
                "resolution": "component",
                "component_id": binding["target_component_id"],
            }
        )
    witnesses.sort(key=canonical_json_bytes)
    return witnesses


def expected_export_reexport_witness(model: dict[str, Any]) -> list[dict[str, Any]]:
    """Derive re-export identity from raw declarations and edges only.

    This deliberately does not consume the submitted observation stream.  A
    star edge may produce zero, one, or many witnesses, while an explicit edge
    produces exactly one witness; all cases retain the one source syntax
    identity that introduced the edge.
    """

    module_by_path = {module["path"]: module for module in model["modules"]}
    components_by_module_decl = {
        (component["module_id"], component["declaration_key"]): component["id"]
        for component in model["components"]
    }
    raw_fixture = load_export_graph_raw_fixture()
    raw_result = recompute_export_graph_case(raw_fixture)
    raw_owner_paths = {edge["owner_file_path"] for edge in raw_fixture["edges"]} & set(
        module_by_path
    )
    joined_reexports = join_reexport_observations_to_edges(
        _export_syntax_rows_for_model(model),
        raw_fixture["edges"],
        owner_paths=raw_owner_paths,
    )
    syntax_by_edge = {_reexport_join_key(syntax): syntax for syntax, _edge in joined_reexports}
    witnesses: list[dict[str, Any]] = []
    for graph_witness in raw_result["witnesses"]:
        owner_module = module_by_path.get(graph_witness["owner_file_path"])
        if owner_module is None:
            continue
        syntax_key = _reexport_join_key(graph_witness)
        matched_syntax = syntax_by_edge.get(syntax_key)
        assert matched_syntax is not None
        terminal_source_path = _terminal_export_source_path(graph_witness, raw_result)
        source_module = module_by_path.get(terminal_source_path)
        target_component_id = (
            components_by_module_decl.get(
                (source_module["id"], graph_witness["target_declaration_key"])
            )
            if source_module is not None
            and graph_witness["resolution"] == "component"
            and graph_witness["target_declaration_key"] is not None
            else None
        )
        witnesses.append(
            {
                "owner_module_id": owner_module["id"],
                "owner_file_path": graph_witness["owner_file_path"],
                "byte_start": matched_syntax["byte_start"],
                "byte_end": matched_syntax["byte_end"],
                "token_identity": matched_syntax["token_identity"],
                "syntax_identity": matched_syntax["syntax_identity"],
                "source_specifier": graph_witness["source_specifier"],
                "imported_name": graph_witness["imported_name"],
                "original_exported_name": graph_witness["original_exported_name"],
                "exported_name": graph_witness["exported_name"],
                "resolved_source_module_id": source_module["id"] if source_module else None,
                "expanded_exported_name": graph_witness["expanded_exported_name"],
                "target_declaration_id": target_component_id,
                "resolution": graph_witness["resolution"],
                "diagnostic": graph_witness["diagnostic"],
            }
        )
    return sorted(witnesses, key=canonical_json_bytes)


def expected_export_observations(model: dict[str, Any]) -> list[dict[str, Any]]:
    """Build observations from the frozen source census, not public bindings."""

    return _export_census_for_model(model)


def _export_binding_projection_from_observations(
    observations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Project observed exports into the public binding identity tuple."""

    projected: list[dict[str, Any]] = []
    for observation in observations:
        resolution = observation["resolution"]
        if resolution != "component":
            # Only a value export resolved to one Component is public.  Value,
            # type, and unknown observations remain coverage-only evidence.
            continue
        target_component_id = observation["component_id"]
        identity = {
            "owner_id": observation["owner_module_id"],
            "exported_name": observation["exported_name"],
            "role": "value",
        }
        projected.append(
            {
                "kind": "export_binding",
                "id": (
                    "next:member:"
                    f"{digest({'kind': 'export_binding', 'version': 1, 'identity': identity})}"
                ),
                "owner_id": observation["owner_module_id"],
                "exported_name": observation["exported_name"],
                "role": "value",
                "target_component_id": target_component_id,
                "resolution_kind": "component",
                "reexport": observation["reexport"],
            }
        )
    projected.sort(key=canonical_json_bytes)
    return projected


def _export_binding_projection_for_model(model: dict[str, Any]) -> list[dict[str, Any]]:
    """Project local and independently expanded re-export Components."""

    observations = _export_census_for_model(model)
    # A re-export observation is syntax evidence only.  Its public binding is
    # derived from the raw declaration/edge graph below, so a coordinated
    # observation+binding mutation cannot make the graph disappear.
    projected = _export_binding_projection_from_observations(
        [observation for observation in observations if not observation["reexport"]]
    )
    for witness in expected_export_reexport_witness(model):
        if witness["resolution"] != "component":
            continue
        component_id = witness["target_declaration_id"]
        assert component_id is not None
        identity = {
            "owner_id": witness["owner_module_id"],
            "exported_name": witness["exported_name"],
            "role": "value",
        }
        projected.append(
            {
                "kind": "export_binding",
                "id": (
                    "next:member:"
                    f"{digest({'kind': 'export_binding', 'version': 1, 'identity': identity})}"
                ),
                "owner_id": witness["owner_module_id"],
                "exported_name": witness["exported_name"],
                "role": "value",
                "target_component_id": component_id,
                "resolution_kind": "component",
                "reexport": True,
            }
        )
    projected.sort(key=canonical_json_bytes)
    keys = [(item["owner_id"], item["exported_name"], item["role"]) for item in projected]
    assert len(keys) == len(set(keys))
    return projected


def expected_export_coverage_counts(model: dict[str, Any]) -> dict[str, int]:
    """Count value/type coverage from local observations and graph rows once."""

    observations = _export_census_for_model(model)
    counts = {
        "value": sum(
            observation["resolution"] == "value"
            for observation in observations
            if not observation["reexport"]
        ),
        "type": sum(
            observation["resolution"] == "type"
            for observation in observations
            if not observation["reexport"]
        ),
    }
    for witness in expected_export_reexport_witness(model):
        if witness["resolution"] in counts:
            counts[witness["resolution"]] += 1
    return {
        "non_component_value_export_count": counts["value"],
        "type_only_export_count": counts["type"],
    }


def validate_export_observations(observations: list[dict[str, Any]], model: dict[str, Any]) -> None:
    """Validate the complete source census and its independent resolution."""

    modules = {item["id"]: item for item in model["modules"]}
    components = {item["id"]: item for item in model["components"]}
    expected = expected_export_observations(model)
    syntax_fields = (
        "owner_file_path",
        "byte_start",
        "byte_end",
        "token_identity",
        "syntax_identity",
        "syntax_kind",
        "exported_name",
        "role",
        "reexport",
        "star",
        "source_specifier",
        "imported_name",
        "resolution",
        "component_id",
        "target_declaration_id",
        "resolved_source_module_id",
        "expanded_exported_name",
    )
    assert [
        tuple(observation[field] for field in syntax_fields) for observation in observations
    ] == [tuple(observation[field] for field in syntax_fields) for observation in expected]
    assert observations == sorted(observations, key=canonical_json_bytes)
    observation_keys: list[tuple[str, str, str, str]] = []
    for observation in observations:
        assert observation["owner_module_id"] in modules
        assert observation["owner_file_path"] == modules[observation["owner_module_id"]]["path"]
        assert 0 <= observation["byte_start"] < observation["byte_end"]
        assert observation["syntax_kind"] in {
            "default_export",
            "named_export",
            "type_export",
            "reexport",
            "export_all",
        }
        assert re.fullmatch(r"[0-9a-f]{64}", observation["token_identity"])
        if observation["star"]:
            assert observation["syntax_kind"] == "export_all"
            assert observation["exported_name"] == "*"
            assert observation["reexport"] is True
            assert observation["resolution"] == "unknown"
            assert observation["component_id"] is None
        else:
            assert observation["exported_name"] == "default" or _is_export_identifier(
                observation["exported_name"], allow_default=True
            )
        assert (
            unicodedata.normalize("NFC", observation["exported_name"])
            == observation["exported_name"]
        )
        assert observation["role"] in {"value", "type"}
        assert isinstance(observation["reexport"], bool)
        if observation["reexport"]:
            assert observation["source_specifier"]
            assert observation["imported_name"] is not None
            assert (
                observation["resolved_source_module_id"] is None
                or observation["resolved_source_module_id"] in modules
            )
            assert (
                observation["expanded_exported_name"] is None
                or unicodedata.normalize("NFC", observation["expanded_exported_name"])
                == observation["expanded_exported_name"]
            )
        else:
            assert observation["source_specifier"] is None
        assert observation["target_declaration_id"] == observation["component_id"]
        assert (
            observation["resolved_source_module_id"] is None
            or observation["resolved_source_module_id"] in modules
        )
        assert observation["syntax_identity"]
        assert (
            unicodedata.normalize("NFC", observation["syntax_identity"])
            == observation["syntax_identity"]
        )
        assert not any(
            ord(char) < 0x20 or ord(char) == 0x7F for char in observation["syntax_identity"]
        )
        resolution = observation["resolution"]
        assert resolution in {"component", "value", "type", "unknown"}
        if resolution == "component":
            assert observation["role"] == "value"
            assert observation["component_id"] in components
            assert observation["star"] is False
        else:
            assert observation["component_id"] is None
        if resolution == "value":
            assert observation["role"] == "value"
        if resolution == "type":
            assert observation["role"] == "type"
        observation_keys.append(
            (
                observation["owner_module_id"],
                observation["exported_name"],
                observation["role"],
                observation["syntax_identity"],
            )
        )
    assert len(observation_keys) == len(set(observation_keys))
    expected_public = sorted(
        [member for member in model["members"] if member["kind"] == "export_binding"],
        key=canonical_json_bytes,
    )
    assert _export_binding_projection_for_model(model) == expected_public


def validate_proof(
    proof: dict[str, Any],
    model: dict[str, Any],
    expected_targets: dict[str, tuple[str, ...]] | None = None,
    request_targets: list[str] | None = None,
) -> None:
    model_collections = _validate_model_collections(model)
    _validate_proof_reason_semantics(proof, model)
    discovered: dict[str, dict[str, dict[str, Any]]] = {
        collection: {} for collection in COLLECTIONS
    }
    for item in proof["discovered_records"]:
        collection = item["collection"]
        record_id = item["record_id"]
        assert collection in COLLECTIONS
        supplied_record = item.get("record")
        if supplied_record is None:
            assert record_id in model_collections[collection]
            record = model_collections[collection][record_id]
        else:
            assert record_id not in model_collections[collection]
            record = supplied_record
            assert record["id"] == record_id
        assert record_id not in discovered[collection]
        assert _id_kind(record_id) == collection.removesuffix("s")
        assert recompute_record_id(record) == record_id
        assert all(taint in TAINTS for taint in item["taints"])
        assert item["taints"] == sorted(item["taints"], key=TAINT_ORDER_INDEX.__getitem__)
        discovered[collection][record_id] = {**item, "record": record}

    published = {collection: set(records) for collection, records in model_collections.items()}
    for collection, record_ids in published.items():
        assert record_ids <= set(discovered[collection])
        for record_id in record_ids:
            discovered_record = discovered[collection][record_id]["record"]
            assert discovered_record == model_collections[collection][record_id]
            assert discovered[collection][record_id]["taints"] == []

    tainted_ids = {
        record_id
        for records in discovered.values()
        for record_id, item in records.items()
        if item["taints"]
    }

    failure_ids = {root["id"] for root in proof["failure_roots"]}
    assert len(failure_ids) == len(proof["failure_roots"])
    all_discovered_ids = set().union(*(set(records) for records in discovered.values()))
    assert len(all_discovered_ids) == model["coverage"]["counts"]["discovered"]
    for root in proof["failure_roots"]:
        assert root["id"].startswith("next:failure:")
        assert root["collection"] in COLLECTIONS
        assert root["kind"] in TAINTS
        expected_collections = {
            "parse_file": {"files"},
            "read_file": {"files"},
            "type_symbol": {"components", "members"},
            "props_subtree": {"components", "members"},
            "export_binding": {"members", "modules"},
            "component_flow": {"components", "relations"},
            "module_relation": {"modules", "relations"},
            "boundary_derivation": {"modules", "relations", "facts"},
        }
        assert root["collection"] in expected_collections[root["kind"]]
        record_ids = root["record_ids"]
        assert record_ids == sorted(set(record_ids))
        assert record_ids
        assert set(record_ids) <= all_discovered_ids
        if root["collection"] == "files":
            assert root["path_ref"] is not None
        if root["path_ref"] is not None:
            _assert_file_path(root["path_ref"])
    taint_closure = _derived_taint_fixed_point(proof, discovered)
    assert taint_closure == tainted_ids
    assert not any(
        record_id in taint_closure for record_ids in published.values() for record_id in record_ids
    )

    excluded: dict[str, set[str]] = {collection: set() for collection in COLLECTIONS}
    for item in proof["excluded"]:
        collection = item["collection"]
        record_id = item["record_id"]
        assert record_id in discovered[collection]
        assert record_id not in excluded[collection]
        assert record_id not in published[collection]
        if item["reason"] == "tainted":
            assert discovered[collection][record_id]["taints"]
        excluded[collection].add(record_id)

    failed: dict[str, set[str]] = {collection: set() for collection in COLLECTIONS}
    for item in proof["failed"]:
        collection = item["collection"]
        record_id = item["record_id"]
        assert record_id in discovered[collection]
        assert record_id not in failed[collection]
        assert record_id not in published[collection]
        failed[collection].add(record_id)

    for collection in COLLECTIONS:
        assert excluded[collection].isdisjoint(failed[collection])
        assert (
            set(discovered[collection])
            == published[collection] | excluded[collection] | failed[collection]
        )

    excluded_reasons = {
        (item["collection"], item["record_id"]): item["reason"] for item in proof["excluded"]
    }
    failed_reasons = {
        (item["collection"], item["record_id"]): item["reason"] for item in proof["failed"]
    }
    assert len(excluded_reasons) == len(proof["excluded"])
    assert len(failed_reasons) == len(proof["failed"])
    for collection, records in discovered.items():
        for record_id, item in records.items():
            disposition = (collection, record_id)
            if item["taints"]:
                assert disposition in excluded_reasons or disposition in failed_reasons
            if disposition in excluded_reasons and excluded_reasons[disposition] == "tainted":
                assert item["taints"]
            if disposition in failed_reasons:
                reason = failed_reasons[disposition]
                assert reason in item["taints"]

    assert taint_closure <= {
        record_id
        for collection in COLLECTIONS
        for record_id in (excluded[collection] | failed[collection])
    }

    all_discovered = set().union(*(set(records) for records in discovered.values()))
    _assert_canonical(proof["causal_edges"])
    for edge in proof["causal_edges"]:
        assert edge["source_id"] in all_discovered | failure_ids
        assert edge["record_id"] in all_discovered

    assert all(
        root["id"] in {edge["source_id"] for edge in proof["causal_edges"]}
        for root in proof["failure_roots"]
    )

    assert proof["causal_edges"] == derive_required_causal_edges(proof, discovered)

    validate_export_observations(proof["export_observations"], model)
    assert {
        "non_component_value_export_count": model["coverage"]["non_component_value_export_count"],
        "type_only_export_count": model["coverage"]["type_only_export_count"],
    } == expected_export_coverage_counts(model)
    assert proof["export_resolution_witness"] == expected_export_resolution_witness(model)
    assert proof["export_reexport_witness"] == expected_export_reexport_witness(model)

    target_keys = [item["target_key"] for item in proof["target_resolutions"]]
    assert proof["target_resolutions"] == sorted(
        proof["target_resolutions"], key=canonical_json_bytes
    )
    assert len(target_keys) == len(set(target_keys))
    for resolution in proof["target_resolutions"]:
        if resolution["status"] == "resolved":
            assert resolution["record_ids"]
            assert resolution["record_ids"] == sorted(resolution["record_ids"])
            assert set(resolution["record_ids"]) <= all_discovered
            assert set(resolution["record_ids"]) <= set().union(*published.values())
        else:
            assert resolution["record_ids"] == []
    if expected_targets is not None:
        actual_targets = {
            resolution["target_key"]: (
                resolution["status"],
                tuple(resolution["record_ids"]),
            )
            for resolution in proof["target_resolutions"]
        }
        for target_key, expected_ids in expected_targets.items():
            assert actual_targets[target_key] == ("resolved", expected_ids)
    if request_targets is not None:
        canonical_targets = [canonical_target_key(target) for target in request_targets]
        assert canonical_targets == request_targets
        discovered_model = {
            collection: [item["record"] for _record_id, item in sorted(records.items())]
            for collection, records in discovered.items()
        }
        unavailable_ids = tainted_ids | {
            record_id
            for collection in COLLECTIONS
            for record_id in (excluded[collection] | failed[collection])
        }
        assert proof["target_resolutions"] == resolve_target_resolutions(
            request_targets,
            discovered_model,
            unavailable_record_ids=unavailable_ids,
        )
    coverage_targets = {
        item["target_key"]: (item["status"], tuple(item["record_ids"]))
        for item in model["coverage"]["target_completeness"]
    }
    assert model["coverage"]["target_completeness"] == sorted(
        model["coverage"]["target_completeness"], key=canonical_json_bytes
    )
    assert len(coverage_targets) == len(model["coverage"]["target_completeness"])
    proof_targets = {
        item["target_key"]: (
            "complete" if item["status"] == "resolved" else "failed",
            tuple(item["record_ids"]),
        )
        for item in proof["target_resolutions"]
    }
    assert coverage_targets == proof_targets

    for collection, count in model["coverage"]["counts"].items():
        if collection in COLLECTIONS:
            assert count == len(model_collections[collection])
    assert model["coverage"]["counts"]["discovered"] == sum(
        len(records) for records in discovered.values()
    )
    assert model["coverage"]["counts"]["excluded"] == sum(
        len(records) for records in excluded.values()
    )
    assert model["coverage"]["counts"]["failed"] == sum(len(records) for records in failed.values())

    coverage = model["coverage"]
    assert coverage["affected_ids"] == sorted(taint_closure)
    tainted_records = {
        record_id: records[record_id]["record"]
        for records in discovered.values()
        for record_id in records
        if record_id in taint_closure
    }
    expected_frontier = sorted(
        {
            referenced_id
            for record in tainted_records.values()
            for referenced_id in _record_references(record)
            if referenced_id in all_discovered
            and referenced_id not in taint_closure
            and _id_kind(referenced_id) != "project"
        }
    )
    assert coverage["taint_frontier"] == expected_frontier
    expected_failed_files = sorted(
        {
            (discovered["files"][record_id]["record"]["path"], reason)
            for (collection, record_id), reason in failed_reasons.items()
            if collection == "files"
        }
    )
    assert coverage["failed_files"] == sorted(coverage["failed_files"], key=canonical_json_bytes)
    assert [(item["path"], item["reason"]) for item in coverage["failed_files"]] == (
        expected_failed_files
    )

    opaque_counts: dict[str, int] = {}
    for member in model["members"]:
        if member["kind"] != "prop":
            continue
        for reason, count in _opaque_reason_counts(member["type_node"]).items():
            opaque_counts[reason] = opaque_counts.get(reason, 0) + count
    assert coverage["opaque_reason_counts"] == opaque_counts
    losses = coverage["correlation_losses"]
    _assert_canonical(losses)
    component_ids = set(model_collections["components"])
    prop_records = {member["id"]: member for member in model["members"] if member["kind"] == "prop"}
    for loss in losses:
        assert loss["component_id"] in component_ids
        assert loss["prop_ids"] == sorted(loss["prop_ids"])
        assert loss["prop_ids"]
        assert loss["signature_count"] <= LIMIT_DEFAULTS["max_signatures_per_component"]
        assert all(
            prop_records[prop_id]["owner_id"] == loss["component_id"]
            for prop_id in loss["prop_ids"]
        )
    assert coverage["unknown_relation_count"] == sum(
        relation["target"]["kind"] == "unresolved"
        for relation in model["relations"]
        if "target" in relation
    )
    assert {
        "non_component_value_export_count": coverage["non_component_value_export_count"],
        "type_only_export_count": coverage["type_only_export_count"],
    } == expected_export_coverage_counts(model)


def validate_trusted_environment(
    environment: dict[str, Any], target_paths: list[str] | None = None
) -> None:
    assert environment["environment_version"] == "1"
    assert environment["semantic_profile_id"] == "next-trusted-profile-v1"
    assert environment["typescript_version"] == "5.9.2"
    assert (
        environment["identifier_unicode_table_digest"] == ECMASCRIPT_IDENTIFIER_UNICODE_TABLE_DIGEST
    )
    assert environment["license_inventory_digest"] == TRUSTED_PROFILE_LICENSE_DIGEST
    assert environment["reserved_module_specifiers"] == list(TRUSTED_MODULES)
    assert environment["reserved_global_names"] == list(TRUSTED_GLOBALS)
    files = environment["files"]
    assert [item["virtual_path"] for item in files] == list(TRUSTED_PROFILE_FILES)
    assert len({item["virtual_path"] for item in files}) == len(files)
    assert files == [
        {
            "physical_path": physical_path,
            "virtual_path": path,
            "size_bytes": TRUSTED_PROFILE_FILE_SIZES[path],
            "sha256": TRUSTED_PROFILE_FILE_SHA256[path],
            "license_id": TRUSTED_PROFILE_FILE_LICENSES[path],
        }
        for physical_path, path in TRUSTED_PROFILE_PHYSICAL_TO_VIRTUAL
    ]
    file_digests = {item["sha256"] for item in files}
    for item in files:
        physical_path = item["physical_path"]
        assert physical_path in {
            physical for physical, _virtual in TRUSTED_PROFILE_PHYSICAL_TO_VIRTUAL
        }
        physical_file = REPO_ROOT / physical_path
        assert physical_file.is_file()
        content = physical_file.read_bytes()
        assert item["size_bytes"] == len(content)
        assert item["sha256"] == hashlib.sha256(content).hexdigest()
        virtual_path = item["virtual_path"]
        assert unicodedata.normalize("NFC", virtual_path) == virtual_path
        assert re.fullmatch(
            r"/\.code-structure-viz/trusted/v1/[A-Za-z0-9._/-]+\.d\.ts", virtual_path
        )
        assert "//" not in virtual_path
        assert ".." not in virtual_path.split("/")
    for target_path in target_paths or []:
        _assert_file_path(target_path)
        normalized = unicodedata.normalize("NFC", target_path)
        assert not any(normalized == item["virtual_path"] for item in files)
    symbols = environment["certified_symbols"]
    assert symbols == list(TRUSTED_PROFILE_CERTIFIED_SYMBOLS)
    symbol_keys = [
        (item["source_kind"], item["source_name"], tuple(item["export_path"])) for item in symbols
    ]
    expected_symbol_keys = sorted(
        [("global", source, export_path) for source, export_path in TRUSTED_PROFILE_GLOBAL_SYMBOLS]
        + [
            ("module", source, export_path)
            for source, export_path in TRUSTED_PROFILE_MODULE_SYMBOLS
        ]
    )
    assert symbol_keys == expected_symbol_keys
    assert len(symbol_keys) == len(set(symbol_keys))
    expected_inventory = {
        _trusted_inventory_symbol_key(row): row for row in TRUSTED_PROFILE_EXPECTED_INVENTORY
    }
    assert len(expected_inventory) == len(TRUSTED_PROFILE_EXPECTED_INVENTORY)
    for symbol in symbols:
        assert symbol["declaration_sha256"] in file_digests
        key = _trusted_inventory_symbol_key(symbol)
        expected = expected_inventory[key]
        assert symbol["symbol_kind"] == expected["symbol_kind"]
        assert symbol["signature_digest"] == expected["signature_digest"]
        declaration_path = _TRUSTED_PROFILE_VIRTUAL_BY_BASENAME[expected["declaration_file"]]
        assert symbol["declaration_sha256"] == TRUSTED_PROFILE_FILE_SHA256[declaration_path]
    assert environment["anti_shadowing_witness"] == list(TRUSTED_PROFILE_SHADOWING_WITNESS)
    assert environment["sha256"] == digest(_without(environment, "sha256"))


def validate_no_trusted_shadowing(
    declarations: list[dict[str, str]], environment: dict[str, Any]
) -> list[dict[str, str]]:
    """Reject target declarations that could augment a trusted namespace."""

    reserved_modules = set(environment["reserved_module_specifiers"])
    reserved_globals = set(environment["reserved_global_names"])
    witness: list[dict[str, str]] = []
    for declaration in declarations:
        assert set(declaration) == {"source_kind", "source_name", "operation"}
        assert declaration["source_kind"] in {"module", "global"}
        assert declaration["operation"] in {"declare", "augment", "redirect"}
        if declaration["source_kind"] == "module":
            reserved = declaration["source_name"] in reserved_modules
        else:
            reserved = declaration["source_name"] in reserved_globals
        decision = "reject" if reserved else "allow"
        witness.append({**declaration, "decision": decision})
        assert not reserved
    return witness


def validate_runtime_manifest(manifest: dict[str, Any]) -> None:
    members = manifest["members"]
    assert [item["path"] for item in members] == sorted(item["path"] for item in members)
    assert len({item["path"] for item in members}) == len(members)
    assert {item["path"]: item["role"] for item in members} == RUNTIME_REQUIRED_PATHS
    assert {item["role"] for item in members} == RUNTIME_REQUIRED_MEMBER_ROLES
    expected_members: list[dict[str, Any]] = []
    for physical_path, virtual_path in RUNTIME_PHYSICAL_TO_VIRTUAL:
        content = (REPO_ROOT / physical_path).read_bytes()
        expected_members.append(
            {
                "physical_path": physical_path,
                "path": virtual_path,
                "size_bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
                "role": RUNTIME_REQUIRED_PATHS[virtual_path],
            }
        )
    expected_members.sort(key=lambda item: item["path"])
    assert members == expected_members
    for item in members:
        physical_path = item["physical_path"]
        assert physical_path in {path for path, _virtual in RUNTIME_PHYSICAL_TO_VIRTUAL}
        assert (REPO_ROOT / physical_path).is_file()
        _assert_file_path(item["path"])
        assert item["path"].startswith("src/code_structure_viz/_next_runtime/")
        assert "//" not in item["path"]
        assert ".." not in item["path"].split("/")
    licenses = manifest["licenses"]
    license_keys = [
        (item["ecosystem"], item["name"], item["version"], item["license_id"]) for item in licenses
    ]
    assert license_keys == sorted(license_keys)
    assert len(license_keys) == len(set(license_keys))
    for license_record in licenses:
        parsed = urlparse(license_record["source_url"])
        assert parsed.scheme == "https" and parsed.netloc
    assert licenses == list(TRUSTED_PROFILE_LICENSES)
    assert manifest["license_inventory_digest"] == TRUSTED_PROFILE_LICENSE_DIGEST
    assert manifest["inventory_attestation"] == {
        "schema": "code-structure-viz.next-runtime-inventory/v1",
        "members": members,
        "sha256": digest({"members": members}),
    }
    assert manifest["build_input_digest"] == digest({"members": members, "licenses": licenses})
    assert manifest["build_output_digest"] == digest({"members": members})
    assert manifest["manifest_sha256"] == digest(_without(manifest, "manifest_sha256"))


def validate_run_status_vector(
    manifest: dict[str, Any] | None,
    summary: dict[str, Any],
    stdout_result: dict[str, Any] | None,
    published_bytes: dict[str, bytes],
    stdout_bytes: bytes | None,
    manifest_diagnostics: list[dict[str, Any]],
    *,
    stderr_bytes: bytes,
    public_stderr_diagnostics: list[dict[str, Any]] | None = None,
) -> None:
    """Validate status while keeping emitted stderr separate from manifest data."""

    if public_stderr_diagnostics is None:
        public_stderr_diagnostics = manifest_diagnostics
    assert stderr_bytes == _public_diagnostic_jsonl(public_stderr_diagnostics)

    run_status = summary["run_status"]
    expected_exit = {
        "complete": 0,
        "not_applicable": 0,
        "incomplete": 3,
        "fatal": 1,
        "usage": 2,
        "interrupted": 130,
    }[run_status]
    assert summary["exit_code"] == expected_exit
    if run_status == "usage":
        assert manifest is None
        assert summary["domains"] == []
        assert summary["manifest"] is None
        assert stdout_result is None
        assert stdout_bytes == b""
        assert manifest_diagnostics == []
        return
    if run_status in {"fatal", "interrupted"}:
        assert manifest is None
        assert summary["domains"] == []
        assert summary["manifest"] is None
        assert stdout_result is not None
        assert stdout_result["availability"] is False
        assert stdout_result["run_status"] == run_status
        assert stdout_result["artifact"] is None
        assert stdout_bytes == canonical_json_bytes(stdout_result) + b"\n"
        assert manifest_diagnostics == []
        return

    assert manifest is not None
    assert manifest["run"]["status"] == run_status
    assert manifest["run"]["exit_code"] == expected_exit
    assert summary["manifest"] == "run-manifest.json"
    assert len(summary["domains"]) == 1
    summary_domain = summary["domains"][0]
    domain = manifest["domains"][0]
    assert summary_domain["domain"] == domain["domain"] == "next"
    assert summary_domain["status"] == domain["status"] == run_status
    if run_status == "incomplete":
        assert summary_domain["incomplete_kind"] == domain["incomplete_kind"]
    assert manifest["next_request"] == domain["request"]
    assert manifest["next_config"] == domain["config"]
    artifact_paths = set(domain["artifact_paths"])
    assert set(published_bytes) == artifact_paths
    artifact_records = {artifact["path"]: artifact for artifact in manifest["artifacts"]}
    assert set(artifact_records) == artifact_paths
    for path, payload in published_bytes.items():
        descriptor = artifact_records[path]
        assert descriptor["size_bytes"] == len(payload)
        assert descriptor["sha256"] == hashlib.sha256(payload).hexdigest()
    assert manifest_diagnostics == manifest["diagnostics"]

    assert stdout_result is not None
    selector = stdout_result["selector"]
    assert selector in {"next:semantic-json", "next:plantuml"}
    assert selector.removeprefix("next:") in manifest["run"]["run_context"]["requested_formats"]
    assert stdout_result["domain_status"] == run_status
    format_name = selector.removeprefix("next:")
    expected_path = (
        "next.snapshot.semantic.json" if format_name == "semantic-json" else "next.snapshot.puml"
    )
    if run_status == "not_applicable" or domain.get("incomplete_kind") == "payload_unavailable":
        assert stdout_result["availability"] is False
        assert stdout_result["artifact"] is None
        assert "incomplete_kind" not in stdout_result
        assert stdout_result["stable_reason"] in {
            "domain_not_applicable",
            "domain_payload_unavailable",
            "target_payload_unavailable",
        }
        target_diagnostics = [
            diagnostic
            for diagnostic in manifest_diagnostics
            if diagnostic["code"] == "CSV-NEXT-TARGET-001"
        ]
        target_failures = [
            {
                "target_key": f"path:{diagnostic['path']}",
                "reason": diagnostic["reason"],
            }
            for diagnostic in target_diagnostics
            if "reason" in diagnostic
        ]
        if target_failures:
            assert stdout_result["target_failures"] == sorted(
                target_failures, key=canonical_json_bytes
            )
            assert "reason" not in stdout_result
        else:
            assert "reason" not in stdout_result
            assert "target_failures" not in stdout_result
        assert stdout_bytes == canonical_json_bytes(stdout_result) + b"\n"
    else:
        assert expected_path in published_bytes
        assert stdout_result["availability"] is True
        assert stdout_result["stable_reason"] == "published_artifact"
        assert stdout_result["artifact"] == artifact_records[expected_path]
        if run_status == "incomplete":
            assert stdout_result["incomplete_kind"] == "partial_safe"
        assert stdout_bytes == published_bytes[expected_path]


def validate_run_manifest(
    manifest: dict[str, Any],
    domain: dict[str, Any],
    published_bytes: dict[str, bytes],
) -> None:
    """Validate the whole-run Next projection, not only its domain entry."""

    validate_domain_manifest(domain)
    assert manifest["type"] == "run_manifest"
    assert manifest["schema"] == "code-structure-viz.run-manifest/v1"
    assert manifest["contracts"]["plantuml"] == "code-structure-viz.plantuml/next/v1"
    assert manifest["adapters"] == [{"domain": "next", "name": "next-typescript", "version": "1"}]
    root_projects = sorted(
        (project["root"] for project in domain["projects"]), key=canonical_json_bytes
    )
    assert manifest["command"] == {
        "name": "snapshot",
        "domain": "next",
        "formats": domain["formats"],
        "stdout_selector": domain["run_context"]["stdout_selector"],
    }
    assert manifest["source"] == domain["source"]
    assert manifest["next_request"] == domain["request"]
    assert manifest["next_config"] == domain["config"]
    assert manifest["domains"] == [domain]
    assert manifest["diagnostics"] == domain["diagnostics"]
    assert manifest["request"] == {
        "projects": root_projects,
        "targets": domain["targets"],
        "formats": domain["formats"],
        "upstream_depth": domain["request"]["upstream_depth"],
        "downstream_depth": domain["request"]["downstream_depth"],
    }
    resolved_next = manifest["config"]["resolved"]["next"]
    assert resolved_next == {
        "projects": root_projects,
        "targets": domain["targets"],
        "formats": domain["formats"],
        "trusted_environment_digest": domain["trusted_environment"]["sha256"],
    }
    assert manifest["config"]["resolved"]["traversal"] == {
        "upstream_depth": domain["request"]["upstream_depth"],
        "downstream_depth": domain["request"]["downstream_depth"],
    }
    assert manifest["config"]["resolved"]["limits"] == domain["limits"]
    assert manifest["config"]["sha256"] == digest(_without(manifest["config"], "sha256"))
    expected_exit = 0 if domain["status"] in {"complete", "not_applicable"} else 3
    assert manifest["run"] == {
        "status": domain["status"],
        "exit_code": expected_exit,
        "fingerprint": domain["run_fingerprint"],
        "run_context": domain["run_context"],
    }
    expected_artifacts = []
    for path in domain["artifact_paths"]:
        payload = published_bytes[path]
        format_name = "semantic-json" if path.endswith(".json") else "plantuml"
        expected_artifacts.append(
            {
                "path": path,
                "domain": "next",
                "format": format_name,
                "media_type": (
                    "application/json"
                    if format_name == "semantic-json"
                    else "text/vnd.plantuml; charset=utf-8"
                ),
                "size_bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    assert manifest["artifacts"] == expected_artifacts
    validate_published_projection(domain, published_bytes)


def escape_plantuml_label(value: str) -> str:
    normalized = unicodedata.normalize("NFC", value)
    escaped: list[str] = []
    for character in normalized:
        codepoint = ord(character)
        if character == "\\":
            escaped.append("\\\\")
        elif character == '"':
            escaped.append('\\"')
        elif character == "\t":
            escaped.append("\\t")
        elif character == "\r":
            escaped.append("\\r")
        elif character == "\n":
            escaped.append("\\n")
        elif character == ";":
            escaped.append("\\;")
        elif character in "<>" or codepoint < 0x20 or codepoint == 0x7F:
            escaped.append(f"\\u{codepoint:04x}")
        else:
            escaped.append(character)
    return "".join(escaped)


def external_target_digest(target: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(target)).hexdigest()


def render_plantuml(model: dict[str, Any], status: str = "complete") -> bytes:
    """Render the small exact-byte contract fixture, not production output."""

    assert status in {"complete", "partial_safe"}
    external_targets: dict[str, dict[str, Any]] = {}
    for member in model["members"]:
        source = member.get("source")
        if source is not None and source["kind"] != "internal":
            external_targets[external_target_digest(source)] = source
    for relation in model["relations"]:
        target = relation.get("target")
        if target is not None and target["kind"] != "internal":
            external_targets[external_target_digest(target)] = target

    lines = [
        "@startuml",
        "title CodeStructureViz Next snapshot",
        f"note top: status={status}; coverage={status}",
        "legend",
        "N_P project",
        "N_M module",
        "N_C component",
        "<<export_binding>> export member",
        "<<import_binding>> import member",
        "<<prop>> prop member",
        "--> static_import|literal_dynamic_import",
        "..> jsx_render|component_wrap",
        "facet=role:<value|type>|reexport=<true|false>|boundary=<none|server_to_client_entry>",
        "marker=client_entry|router_context=<context>|client_dependency|server_candidate|unknown",
        "marker=partial_safe",
        "external=cloud-after-components-before-members",
        "sort=kind-prefixed-id-utf8",
        "endlegend",
    ]
    for project in sorted(model["projects"], key=lambda item: item["id"]):
        project_alias = project["id"].split(":")[-1]
        lines.append(f'package "P:{project["id"]}" as N_P_{project_alias} {{')
        lines.append("}")
    for module in sorted(model["modules"], key=lambda item: item["id"]):
        module_alias = module["id"].split(":")[-1]
        lines.append(f'component "M:{escape_plantuml_label(module["path"])}" as N_M_{module_alias}')
        markers = ["client_entry"] if module["client_entry"] else []
        if module["router_context"] != "none":
            markers.append(f"router_context={module['router_context']}")
        markers.extend(sorted(module["derived_roles"]))
        lines.append(f"N_M_{module_alias} : marker={'|'.join(markers or ['unknown'])}")
    for component in sorted(model["components"], key=lambda item: item["id"]):
        alias = component["id"].split(":")[-1]
        lines.append(
            f'rectangle "C:{escape_plantuml_label(component["declaration_key"])}" as N_C_{alias}'
        )
    for module in sorted(model["modules"], key=lambda item: item["id"]):
        module_alias = module["id"].split(":")[-1]
        project = next(item for item in model["projects"] if item["id"] == module["project_id"])
        project_alias = project["id"].split(":")[-1]
        lines.append(f"N_P_{project_alias} .. N_M_{module_alias} : contains")
    for component in sorted(model["components"], key=lambda item: item["id"]):
        component_alias = component["id"].split(":")[-1]
        module_alias = component["module_id"].split(":")[-1]
        lines.append(f"N_M_{module_alias} .. N_C_{component_alias} : contains")
    for target_digest in sorted(external_targets):
        target = external_targets[target_digest]
        label = f"external:{target['safe_specifier']}"
        if target.get("exported_name") is not None:
            label += f"#{target['exported_name']}"
        lines.append(f'cloud "{escape_plantuml_label(label)}" as X_{target_digest}')
    if status == "partial_safe":
        lines.append("note top: marker=partial_safe")
    for member in sorted(model["members"], key=lambda item: item["id"]):
        if member["kind"] == "prop":
            owner = f"N_C_{member['owner_id'].split(':')[-1]}"
            label = f"prop {escape_plantuml_label(member['name'])}"
            stereotype = "prop"
            facets = (
                f"optional={str(member['optional']).lower()}|readonly={str(member['readonly']).lower()}"
                f"|default={member['default_evidence']}"
            )
        elif member["kind"] == "export_binding":
            owner = f"N_M_{member['owner_id'].split(':')[-1]}"
            label = f"export {escape_plantuml_label(member['exported_name'])}"
            stereotype = "export_binding"
            facets = f"role={member['role']}|reexport={str(member['reexport']).lower()}"
        else:
            owner = f"N_M_{member['owner_id'].split(':')[-1]}"
            label = f"import {escape_plantuml_label(member['imported_name'])}"
            stereotype = "import_binding"
            source = member["source"]
            source_descriptor = source["kind"]
            if source["kind"] == "internal":
                source_descriptor += f"#{source['module_id']}"
            else:
                source_descriptor += f"#{source['safe_specifier']}"
                if source.get("exported_name") is not None:
                    source_descriptor += f"#{source['exported_name']}"
            facets = f"role={member['role']}|source={source_descriptor}"
        lines.append(f'{owner} .. "{label}" <<{stereotype}>> : {member["id"]}|{facets}')
    for relation in sorted(model["relations"], key=lambda item: item["id"]):
        if relation["kind"] in {"static_import", "literal_dynamic_import"}:
            source = f"N_M_{relation['source_id'].split(':')[-1]}"
            target = relation["target"]
            target_alias = (
                f"N_M_{target['module_id'].split(':')[-1]}"
                if target["kind"] == "internal"
                else f"X_{external_target_digest(target)}"
            )
            lines.append(
                f"{source} --> {target_alias} : {relation['kind']}|role={relation['role']}"
                f"|reexport={str(relation['reexport']).lower()}|boundary={relation['boundary_effect']}"
            )
        elif relation["kind"] == "jsx_render":
            source = f"N_C_{relation['source_id'].split(':')[-1]}"
            target = relation["target"]
            target_alias = (
                f"N_C_{target['component_id'].split(':')[-1]}"
                if target["kind"] == "internal"
                else f"X_{external_target_digest(target)}"
            )
            lines.append(
                f"{source} ..> {target_alias} : jsx_render|occurrences="
                f"{relation['occurrence_count']}"
                f"|contexts={','.join(relation['contexts'])}"
            )
        else:
            source = f"N_C_{relation['source_id'].split(':')[-1]}"
            target = f"N_C_{relation['target_component_id'].split(':')[-1]}"
            lines.append(
                f"{source} ..> {target} : component_wrap|occurrences={relation['occurrence_count']}"
                f"|contexts={','.join(relation['contexts'])}"
            )
    lines.append("@enduml")
    return ("\n".join(lines) + "\n").encode("utf-8")


def plantuml_aliases_are_safe(data: bytes) -> None:
    text = data.decode("utf-8")
    assert not text.startswith("\ufeff")
    assert text.endswith("\n")
    assert "\r" not in text
    aliases = re.findall(r"\bas ((?:N_[PMC]|X)_[0-9a-f]{64})\b", text)
    assert len(aliases) == len(set(aliases))
    for line in text.splitlines():
        assert "../" not in line
        if not line.startswith("note top: "):
            assert all(
                character != ";" or (index > 0 and line[index - 1] == "\\")
                for index, character in enumerate(line)
            )


def validate_plantuml_contract(
    data: bytes, model: dict[str, Any], status: str = "complete"
) -> None:
    """Parse the exact statement sequence independently of PlantUML itself."""

    assert status in {"complete", "partial_safe"}
    plantuml_aliases_are_safe(data)
    lines = data.decode("utf-8").splitlines()
    legend = [
        "legend",
        "N_P project",
        "N_M module",
        "N_C component",
        "<<export_binding>> export member",
        "<<import_binding>> import member",
        "<<prop>> prop member",
        "--> static_import|literal_dynamic_import",
        "..> jsx_render|component_wrap",
        "facet=role:<value|type>|reexport=<true|false>|boundary=<none|server_to_client_entry>",
        "marker=client_entry|router_context=<context>|client_dependency|server_candidate|unknown",
        "marker=partial_safe",
        "external=cloud-after-components-before-members",
        "sort=kind-prefixed-id-utf8",
        "endlegend",
    ]
    prefix = [
        "@startuml",
        "title CodeStructureViz Next snapshot",
        f"note top: status={status}; coverage={status}",
        *legend,
    ]
    assert lines[: len(prefix)] == prefix
    cursor = len(prefix)

    for project in sorted(model["projects"], key=lambda item: item["id"]):
        suffix = project["id"].split(":")[-1]
        assert lines[cursor] == (f'package "P:{project["id"]}" as N_P_{suffix} {{')
        assert lines[cursor + 1] == "}"
        cursor += 2
    for module in sorted(model["modules"], key=lambda item: item["id"]):
        suffix = module["id"].split(":")[-1]
        expected_label = escape_plantuml_label(module["path"])
        assert lines[cursor] == f'component "M:{expected_label}" as N_M_{suffix}'
        cursor += 1
        markers = ["client_entry"] if module["client_entry"] else []
        if module["router_context"] != "none":
            markers.append(f"router_context={module['router_context']}")
        markers.extend(sorted(module["derived_roles"]))
        assert lines[cursor] == f"N_M_{suffix} : marker={'|'.join(markers or ['unknown'])}"
        cursor += 1
    for component in sorted(model["components"], key=lambda item: item["id"]):
        suffix = component["id"].split(":")[-1]
        expected_label = escape_plantuml_label(component["declaration_key"])
        assert lines[cursor] == f'rectangle "C:{expected_label}" as N_C_{suffix}'
        cursor += 1

    for module in sorted(model["modules"], key=lambda item: item["id"]):
        module_suffix = module["id"].split(":")[-1]
        project = next(item for item in model["projects"] if item["id"] == module["project_id"])
        project_suffix = project["id"].split(":")[-1]
        assert lines[cursor] == f"N_P_{project_suffix} .. N_M_{module_suffix} : contains"
        cursor += 1
    for component in sorted(model["components"], key=lambda item: item["id"]):
        component_suffix = component["id"].split(":")[-1]
        module_suffix = component["module_id"].split(":")[-1]
        assert lines[cursor] == f"N_M_{module_suffix} .. N_C_{component_suffix} : contains"
        cursor += 1

    external_targets: dict[str, dict[str, Any]] = {}
    for member in model["members"]:
        source = member.get("source")
        if source is not None and source["kind"] != "internal":
            external_targets[external_target_digest(source)] = source
    for relation in model["relations"]:
        target = relation.get("target")
        if target is not None and target["kind"] != "internal":
            external_targets[external_target_digest(target)] = target
    for target_digest in sorted(external_targets):
        target = external_targets[target_digest]
        label = f"external:{target['safe_specifier']}"
        if target.get("exported_name") is not None:
            label += f"#{target['exported_name']}"
        assert lines[cursor] == (f'cloud "{escape_plantuml_label(label)}" as X_{target_digest}')
        cursor += 1
    if status == "partial_safe":
        assert lines[cursor] == "note top: marker=partial_safe"
        cursor += 1

    for member in sorted(model["members"], key=lambda item: item["id"]):
        suffix = member["owner_id"].split(":")[-1]
        owner_prefix = "N_C" if member["kind"] == "prop" else "N_M"
        if member["kind"] == "prop":
            label = f"prop {escape_plantuml_label(member['name'])}"
            stereotype = "prop"
            facets = (
                f"optional={str(member['optional']).lower()}|readonly={str(member['readonly']).lower()}"
                f"|default={member['default_evidence']}"
            )
        elif member["kind"] == "export_binding":
            label = f"export {escape_plantuml_label(member['exported_name'])}"
            stereotype = "export_binding"
            facets = f"role={member['role']}|reexport={str(member['reexport']).lower()}"
        else:
            label = f"import {escape_plantuml_label(member['imported_name'])}"
            stereotype = "import_binding"
            source = member["source"]
            source_descriptor = source["kind"]
            if source["kind"] == "internal":
                source_descriptor += f"#{source['module_id']}"
            else:
                source_descriptor += f"#{source['safe_specifier']}"
                if source.get("exported_name") is not None:
                    source_descriptor += f"#{source['exported_name']}"
            facets = f"role={member['role']}|source={source_descriptor}"
        expected_member = (
            f'{owner_prefix}_{suffix} .. "{label}" <<{stereotype}>> : {member["id"]}|{facets}'
        )
        assert lines[cursor] == expected_member
        cursor += 1
    for relation in sorted(model["relations"], key=lambda item: item["id"]):
        if relation["kind"] in {"static_import", "literal_dynamic_import"}:
            source = f"N_M_{relation['source_id'].split(':')[-1]}"
            target = relation["target"]
            target_alias = (
                f"N_M_{target['module_id'].split(':')[-1]}"
                if target["kind"] == "internal"
                else f"X_{external_target_digest(target)}"
            )
            expected = (
                f"{source} --> {target_alias} : {relation['kind']}|role={relation['role']}"
                f"|reexport={str(relation['reexport']).lower()}|boundary={relation['boundary_effect']}"
            )
        elif relation["kind"] == "jsx_render":
            source = f"N_C_{relation['source_id'].split(':')[-1]}"
            target = relation["target"]
            target_alias = (
                f"N_C_{target['component_id'].split(':')[-1]}"
                if target["kind"] == "internal"
                else f"X_{external_target_digest(target)}"
            )
            expected = (
                f"{source} ..> {target_alias} : jsx_render|occurrences="
                f"{relation['occurrence_count']}"
                f"|contexts={','.join(relation['contexts'])}"
            )
        else:
            expected = (
                f"N_C_{relation['source_id'].split(':')[-1]} ..> "
                f"N_C_{relation['target_component_id'].split(':')[-1]} : component_wrap"
                f"|occurrences={relation['occurrence_count']}|contexts={','.join(relation['contexts'])}"
            )
        assert lines[cursor] == expected
        cursor += 1
    assert lines[cursor] == "@enduml"
    assert cursor + 1 == len(lines)
