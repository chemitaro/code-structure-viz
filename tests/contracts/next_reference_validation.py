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
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from functools import cache, lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Any, TypedDict, TypeGuard, cast
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
RUN_CONTEXT_BUDGET_SOURCES = ("builtin", "repository", "explicit", "cli", "unobserved")
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


def _path_sort_key(value: str) -> bytes:
    """Sort path-only rows by their normalized UTF-8 bytes, never JSON escapes."""

    assert isinstance(value, str)
    normalized = unicodedata.normalize("NFC", value)
    return normalized.encode("utf-8")


class NextRunContext(TypedDict):
    """The one explicit context shared by response and publication projections."""

    requested_formats: list[str]
    budget_requested: int | None
    budget_resolved: int | None
    budget_source: str
    stdout_selector: str | None


def _freeze_request_value(value: Any) -> Any:
    """Recursively freeze a private request without inheriting from ``dict``."""

    if isinstance(value, dict):
        return MappingProxyType({key: _freeze_request_value(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_request_value(item) for item in value)
    return value


def _thaw_request_value(value: Any) -> Any:
    """Return a mutable defensive snapshot of a frozen request value."""

    if isinstance(value, Mapping):
        return {key: _thaw_request_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_request_value(item) for item in value]
    return copy.deepcopy(value)


class ValidatedAdapterRequest(Mapping[str, Any]):
    """Composition-based, immutable request authority at the trust boundary.

    The object intentionally is not a ``dict`` subclass.  Its frozen mapping
    and recursively frozen values make base-class mutation bypasses (such as
    ``dict.__setitem__``) impossible.  Readers receive defensive snapshots;
    the canonical bytes and digest are rechecked whenever an existing sealed
    request crosses a validation boundary.
    """

    _values: Mapping[str, Any]
    canonical_bytes: bytes
    canonical_sha256: str

    __slots__ = ("_values", "canonical_bytes", "canonical_sha256")

    def __init__(self, source: dict[str, Any]) -> None:
        assert isinstance(source, dict)
        candidate = copy.deepcopy(source)
        validate_request_envelope(candidate)
        canonical = canonical_json_bytes(candidate)
        object.__setattr__(self, "_values", _freeze_request_value(candidate))
        object.__setattr__(self, "canonical_bytes", canonical)
        object.__setattr__(self, "canonical_sha256", hashlib.sha256(canonical).hexdigest())

    def __setattr__(self, name: str, value: Any) -> None:
        if hasattr(self, name):
            raise TypeError("ValidatedAdapterRequest is immutable")
        object.__setattr__(self, name, value)

    def __iter__(self) -> Iterator[str]:
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)

    def __getitem__(self, key: str) -> Any:
        return _thaw_request_value(self._values[key])

    def snapshot(self) -> dict[str, Any]:
        """Return the complete mutable value for boundary revalidation."""

        return {key: self[key] for key in self}

    def __deepcopy__(self, memo: dict[int, Any]) -> ValidatedAdapterRequest:
        existing = memo.get(id(self))
        if existing is not None:
            return cast(ValidatedAdapterRequest, existing)
        copied = ValidatedAdapterRequest(self.snapshot())
        memo[id(self)] = copied
        return copied


def validate_adapter_request(
    source: dict[str, Any] | ValidatedAdapterRequest,
) -> ValidatedAdapterRequest:
    """Validate and seal one adapter request before any response bytes exist."""

    if isinstance(source, ValidatedAdapterRequest):
        candidate = source.snapshot()
        validate_request_envelope(candidate)
        canonical = canonical_json_bytes(candidate)
        assert canonical == source.canonical_bytes
        assert hashlib.sha256(canonical).hexdigest() == source.canonical_sha256
        return source
    return ValidatedAdapterRequest(source)


@dataclass(frozen=True, kw_only=True)
class NextDecisionContext:
    """Request-independent identity carried by every pre-response failure.

    A failed discovery or process launch cannot manufacture a schema-valid
    adapter request.  This small closed context keeps the run identity,
    resolved limits, and diagnostic routing available without pretending that
    an unavailable request exists.
    """

    run_context: NextRunContext
    request_id: str | None
    targets: tuple[str, ...]
    limits: dict[str, Any] | None
    stage: str
    diagnostic_code: str
    failure_kind: str
    known_counts: dict[str, int | None]
    source_failure_ledger: tuple[dict[str, Any], ...]
    outcome: str
    payload_unavailable: bool
    exit_code: int
    provenance_observation: dict[str, Any]
    provenance: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "run_context", canonical_run_context(**self.run_context))
        assert self.provenance in {"request_bound", "request_independent"}
        observations = copy.deepcopy(self.provenance_observation)
        validate_stage_dependent_provenance(observations)
        assert observations["kind"] == self.provenance
        observed = observations["observed"]
        if self.provenance == "request_bound":
            assert observations["stage"] is None
            assert observations["failure_code"] is None
        else:
            assert observations["stage"] == self.stage
            assert observations["failure_code"] == self.diagnostic_code
        if self.provenance == "request_independent":
            assert observed["request"] == {"state": "unobserved", "value": None}
        if self.run_context["budget_source"] == "unobserved":
            assert self.run_context["budget_resolved"] is None
            assert observed["budget"] == {"state": "unobserved", "value": None}
        else:
            assert self.run_context["budget_resolved"] is not None
            assert observed["budget"] == {"state": "observed", "value": True}
        object.__setattr__(self, "provenance_observation", observations)
        if self.provenance == "request_bound":
            assert self.request_id is not None
            assert self.limits is not None
        else:
            assert self.request_id is None
            assert self.limits is None
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
        ledger = tuple(copy.deepcopy(self.source_failure_ledger))
        assert ledger == tuple(sorted(ledger, key=canonical_json_bytes))
        for failure in ledger:
            assert set(failure) == {"path", "stage", "isolated", "target_tainted"}
            _assert_file_path(failure["path"])
            assert isinstance(failure["stage"], str) and failure["stage"]
            assert isinstance(failure["isolated"], bool)
            assert isinstance(failure["target_tainted"], bool)
        object.__setattr__(self, "source_failure_ledger", ledger)
        assert self.outcome in {"payload_unavailable", "not_applicable"}
        assert self.payload_unavailable is (self.outcome == "payload_unavailable")
        assert self.exit_code == (3 if self.outcome == "payload_unavailable" else 0)
        if self.diagnostic_code is not None:
            expected_kind = decision_failure_kind(self.diagnostic_code)
            assert self.failure_kind == expected_kind
            object.__setattr__(self, "failure_kind", expected_kind)

    def __getattribute__(self, name: str) -> Any:
        value = object.__getattribute__(self, name)
        if name in {
            "run_context",
            "targets",
            "limits",
            "known_counts",
            "source_failure_ledger",
            "provenance_observation",
        }:
            return copy.deepcopy(value)
        return value


@dataclass(frozen=True)
class NextPublicationContext:
    """Immutable provenance shared by all Next publication projections.

    It is deliberately a data-only object.  A production implementation must
    construct it at the same trust boundary as the run decision and pass this
    object, rather than rebuilding config/source/toolchain facts in a writer.
    """

    source_view_descriptor: dict[str, Any] | None
    source_view_fingerprint: str | None
    final_source_acquisition_plan: dict[str, Any] | None
    source_plan_digest: str | None
    seal_id: str | None
    source_acquisition_seal: SourceAcquisitionSeal | None
    public_next_config: dict[str, Any]
    public_next_request: dict[str, Any] | None
    compatibility_descriptor: dict[str, Any] | None
    toolchain: dict[str, Any] | None
    trusted_environment: dict[str, Any] | None
    semantic_projects: list[dict[str, Any]]
    semantic_files: list[dict[str, Any]]
    run_context: NextRunContext
    run_fingerprint_preimage: dict[str, Any]
    source_failure_ledger: tuple[dict[str, Any], ...]
    source_failure_ledger_seal: SourceFailureLedger | None
    process_launch_descriptor: dict[str, Any] | None
    source_failure_ledger_digest: str | None
    source_failure_ledger_evidence: dict[str, Any] | None
    observation_provenance: dict[str, Any]
    process_launch_observation: dict[str, Any] = field(init=False)

    def __post_init__(self) -> None:
        for name in (
            "source_view_descriptor",
            "final_source_acquisition_plan",
            "source_acquisition_seal",
            "public_next_config",
            "public_next_request",
            "compatibility_descriptor",
            "toolchain",
            "trusted_environment",
            "semantic_projects",
            "semantic_files",
            "run_fingerprint_preimage",
            "source_failure_ledger",
            "source_failure_ledger_seal",
            "process_launch_descriptor",
            "source_failure_ledger_evidence",
            "observation_provenance",
        ):
            object.__setattr__(self, name, copy.deepcopy(getattr(self, name)))
        object.__setattr__(self, "run_context", canonical_run_context(**self.run_context))
        ledger = tuple(self.source_failure_ledger)
        assert ledger == tuple(sorted(ledger, key=canonical_json_bytes))
        for failure in ledger:
            assert set(failure) == {"path", "stage", "isolated", "target_tainted"}
            _assert_file_path(failure["path"])
            assert isinstance(failure["stage"], str) and failure["stage"]
            assert isinstance(failure["isolated"], bool)
            assert isinstance(failure["target_tainted"], bool)
        object.__setattr__(self, "source_failure_ledger", ledger)
        ledger_digest = self.source_failure_ledger_digest
        evidence = self.source_failure_ledger_evidence
        ledger_seal = self.source_failure_ledger_seal
        if ledger_digest is None:
            assert evidence is None
            assert not ledger
            assert ledger_seal is None
        else:
            assert isinstance(ledger_seal, SourceFailureLedger)
            assert ledger_seal.ledger_digest == ledger_digest
            assert tuple(ledger_seal.failures) == ledger
            assert re.fullmatch(r"[0-9a-f]{64}", ledger_digest)
            assert isinstance(evidence, dict)
            assert set(evidence) == {
                "source_seal_id",
                "source_seal_digest",
                "source_graph",
                "failures",
                "targets",
                "proof_roots",
                "ledger_digest",
            }
            assert evidence["ledger_digest"] == ledger_digest
            assert evidence["failures"] == list(ledger)
        object.__setattr__(self, "source_failure_ledger_evidence", copy.deepcopy(evidence))
        process_observation = process_launch_observation_from_descriptor(
            self.process_launch_descriptor
        )
        validate_process_launch_observation(process_observation)
        object.__setattr__(self, "process_launch_observation", process_observation)
        seal = self.source_acquisition_seal
        provenance = self.observation_provenance
        validate_stage_dependent_provenance(provenance)
        assert provenance["kind"] in {"request_bound", "request_independent"}
        if provenance["kind"] == "request_independent":
            expected_budget = (
                {"state": "observed", "value": True}
                if self.run_context["budget_source"] != "unobserved"
                else {"state": "unobserved", "value": None}
            )
            assert provenance["observed"]["budget"] == expected_budget
        if seal is None:
            # The run stopped before a source/config/request observation was
            # available.  Null is the fact; an empty plan, trusted profile,
            # toolchain, or limit record would falsely claim observation.
            assert provenance["kind"] == "request_independent"
            assert self.source_view_descriptor is None
            assert self.source_view_fingerprint is None
            assert self.final_source_acquisition_plan is None
            assert self.source_plan_digest is None
            assert self.seal_id is None
            assert self.compatibility_descriptor is None
            assert self.toolchain is None
            assert self.trusted_environment is None
            assert self.process_launch_descriptor is None
            assert self.public_next_request is None
            assert self.public_next_config["request_independent"] is True
            preimage = self.run_fingerprint_preimage
            assert preimage["source_view_fingerprint"] is None
            assert preimage["source_plan_digest"] is None
            assert preimage["limits"] is None
            assert preimage["trusted_environment_digest"] is None
            assert preimage["node_version"] is None
            assert preimage["typescript_version"] is None
            assert preimage["adapter_version"] is None
            assert preimage["protocol"] is None
            assert preimage["process_launch_descriptor_digest"] is None
            assert preimage["targets"] == self.public_next_config["targets"]
            assert preimage["formats"] == self.run_context["requested_formats"]
            assert preimage["stdout_selector"] == self.run_context["stdout_selector"]
            assert preimage["source_failure_ledger"] == list(self.source_failure_ledger)
            assert preimage.get("source_failure_ledger_digest") == ledger_digest
            return
        assert self.source_view_descriptor is not None
        assert self.source_view_fingerprint is not None
        assert self.final_source_acquisition_plan is not None
        assert self.source_plan_digest is not None
        assert self.seal_id is not None
        assert self.compatibility_descriptor is not None
        assert self.toolchain is not None
        assert self.trusted_environment is not None
        assert self.process_launch_descriptor is not None
        assert seal.plan_digest == self.source_plan_digest
        assert seal.source_view_fingerprint == self.source_view_fingerprint
        assert seal.seal_id == self.seal_id
        validate_compatibility_descriptor(self.compatibility_descriptor)
        assert re.fullmatch(r"[0-9a-f]{64}", self.source_view_fingerprint)
        assert re.fullmatch(r"[0-9a-f]{64}", self.source_plan_digest)
        assert re.fullmatch(r"[0-9a-f]{64}", self.seal_id)
        assert self.source_view_fingerprint == digest(self.source_view_descriptor)
        assert self.source_plan_digest == digest(self.final_source_acquisition_plan)
        assert self.seal_id == digest(
            {
                "plan_digest": self.source_plan_digest,
                "source_view_fingerprint": self.source_view_fingerprint,
                "seal_operation": seal.seal_operation,
                "snapshot_id": seal.snapshot_id,
                "revision_before": seal.revision_before,
                "revision_after": seal.revision_after,
                "source_graph_digest": digest(seal.source_graph),
            }
        )
        ledger = tuple(self.source_failure_ledger)
        assert ledger == tuple(sorted(ledger, key=canonical_json_bytes))
        for failure in ledger:
            assert set(failure) == {"path", "stage", "isolated", "target_tainted"}
            _assert_file_path(failure["path"])
            assert isinstance(failure["stage"], str) and failure["stage"]
            assert isinstance(failure["isolated"], bool)
            assert isinstance(failure["target_tainted"], bool)
        object.__setattr__(self, "source_failure_ledger", ledger)
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
        assert preimage["source_failure_ledger"] == list(ledger)
        assert preimage.get("source_failure_ledger_digest") == ledger_digest
        validate_process_launch_descriptor(self.process_launch_descriptor)
        assert self.process_launch_descriptor["node_status"] == self.toolchain["node"]["status"]
        assert self.process_launch_descriptor["node_version"] == self.toolchain["node_version"]
        assert self.process_launch_descriptor["node_version"] == self.toolchain["node"]["version"]
        assert preimage["process_launch_descriptor_digest"] == digest(
            self.process_launch_descriptor
        )
        if self.public_next_request is not None:
            assert self.public_next_request["formats"] == self.run_context["requested_formats"]
            assert self.public_next_config["limits"] == self.public_next_request["limits"]
            assert self.public_next_config["targets"] == self.public_next_request["targets"]
            assert self.public_next_config["source_plan"] == self.final_source_acquisition_plan
            assert self.public_next_config["source_plan_digest"] == self.source_plan_digest

    def __getattribute__(self, name: str) -> Any:
        value = object.__getattribute__(self, name)
        if name in {
            "source_view_descriptor",
            "final_source_acquisition_plan",
            "source_acquisition_seal",
            "public_next_config",
            "public_next_request",
            "compatibility_descriptor",
            "toolchain",
            "trusted_environment",
            "semantic_projects",
            "semantic_files",
            "run_context",
            "run_fingerprint_preimage",
            "source_failure_ledger",
            "source_failure_ledger_seal",
            "source_failure_ledger_evidence",
            "process_launch_descriptor",
            "process_launch_observation",
            "observation_provenance",
        }:
            return copy.deepcopy(value)
        return value


def _decision_provenance(
    *,
    kind: str,
    stage: str,
    request: bool,
    limits: bool,
    source_plan: bool,
    toolchain: bool,
    trusted_environment: bool,
    budget: bool = True,
    failure_code: str | None = None,
) -> dict[str, Any]:
    """Build the closed stage/provenance union used by every decision context."""

    assert kind in {"request_bound", "request_independent"}
    if kind == "request_independent":
        assert isinstance(failure_code, str) and failure_code
    observed_flags = {
        "request": request,
        "limits": limits,
        "source_plan": source_plan,
        "toolchain": toolchain,
        "trusted_environment": trusted_environment,
        "compatibility": kind == "request_bound",
        "process_launch": kind == "request_bound",
        "budget": budget,
    }
    if kind == "request_bound":
        observed_flags = {name: True for name in observed_flags}
    else:
        expected = _expected_provenance_observed(stage)
        observed_flags = {
            name: name in expected or (name == "budget" and budget) for name in observed_flags
        }
    return {
        "kind": kind,
        "stage": None if kind == "request_bound" else stage,
        "failure_code": None if kind == "request_bound" else failure_code,
        "observed": {
            name: {
                "state": "observed" if observed else "unobserved",
                "value": True if observed else None,
            }
            for name, observed in observed_flags.items()
        },
    }


def _publication_provenance(
    *,
    kind: str,
    failure_stage: str | None = None,
    failure_code: str | None = None,
    budget_observed: bool,
) -> dict[str, Any]:
    """Build the closed observation union for a publication context."""

    assert kind in {"request_bound", "request_independent"}
    if kind == "request_bound":
        assert failure_stage is None and failure_code is None
        observed = {
            name: {"state": "observed", "value": True}
            for name in (
                "request",
                "limits",
                "source_plan",
                "toolchain",
                "trusted_environment",
                "compatibility",
                "process_launch",
                "budget",
            )
        }
    else:
        assert isinstance(failure_stage, str) and failure_stage
        assert isinstance(failure_code, str) and failure_code
        observed = {
            name: {
                "state": "observed"
                if name in _expected_provenance_observed(failure_stage)
                or (name == "budget" and budget_observed)
                else "unobserved",
                "value": True
                if name in _expected_provenance_observed(failure_stage)
                or (name == "budget" and budget_observed)
                else None,
            }
            for name in (
                "request",
                "limits",
                "source_plan",
                "toolchain",
                "trusted_environment",
                "compatibility",
                "process_launch",
                "budget",
            )
        }
    return {
        "kind": kind,
        "stage": failure_stage,
        "failure_code": failure_code,
        "observed": observed,
    }


@dataclass(frozen=True, kw_only=True)
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
    request: ValidatedAdapterRequest
    raw_response_bytes: bytes
    raw_response_sha256: str
    targets: tuple[str, ...] = ()
    target_failures: tuple[dict[str, Any], ...] = ()
    export_failures: tuple[dict[str, Any], ...] = ()
    publication_context: NextPublicationContext
    diagnostic_rows: tuple[dict[str, Any], ...] = field(init=False)
    public_diagnostics: tuple[dict[str, Any], ...] = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "validated_model", copy.deepcopy(self.validated_model))
        object.__setattr__(self, "validated_proof", copy.deepcopy(self.validated_proof))
        object.__setattr__(self, "run_context", canonical_run_context(**self.run_context))
        assert isinstance(self.raw_response_bytes, bytes) and self.raw_response_bytes
        assert re.fullmatch(r"[0-9a-f]{64}", self.raw_response_sha256)
        assert hashlib.sha256(self.raw_response_bytes).hexdigest() == self.raw_response_sha256
        try:
            raw_response = json.loads(self.raw_response_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise AssertionError("sealed response bytes are not JSON") from exc
        assert isinstance(raw_response, dict)
        assert canonical_json_bytes(raw_response) == self.raw_response_bytes
        assert raw_response.get("model") == self.validated_model
        assert raw_response.get("proof") == self.validated_proof
        object.__setattr__(
            self,
            "diagnostic_rows",
            tuple(copy.deepcopy(self.validated_model.get("diagnostics", []))),
        )
        request = copy.deepcopy(self.request)
        assert isinstance(request, ValidatedAdapterRequest)
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
        object.__setattr__(self, "public_diagnostics", tuple(decision_public_diagnostics(self)))
        context = self.publication_context
        assert context is not None
        assert context.run_context == self.run_context
        expected_request_snapshot = _public_request_snapshot(
            request,
            public_config=context.public_next_config,
            source_plan=context.final_source_acquisition_plan,
            source_plan_digest=context.source_plan_digest,
            domain_config_digest=context.public_next_config["domain_config_digest"],
            run_fingerprint=digest(context.run_fingerprint_preimage),
        )
        assert context.public_next_request == expected_request_snapshot
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
            "raw_response_bytes",
            "diagnostic_rows",
            "public_diagnostics",
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
        "CSV-NEXT-EXPORT-001",
        "CSV-NEXT-FLOW-001",
        "CSV-NEXT-IDENTITY-001",
        "CSV-NEXT-NODE-001",
        "CSV-NEXT-NODE-002",
        "CSV-NEXT-NODE-003",
        "CSV-NEXT-NODE-004",
        "CSV-NEXT-PROTOCOL-001",
        "CSV-NEXT-PROJECT-001",
        "CSV-NEXT-PROJECT-002",
        "CSV-NEXT-SOURCE-001",
        "CSV-NEXT-SOURCE-002",
        "CSV-NEXT-SOURCE-003",
        "CSV-NEXT-TARGET-001",
        "CSV-NEXT-TYPE-001",
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
    "CSV-NEXT-FLOW-001": "flow",
    "CSV-NEXT-TYPE-001": "type",
}


def decision_failure_kind(diagnostic_code: str) -> str:
    """Return the closed pre-response failure category for one code."""

    if diagnostic_code == "CSV-NEXT-APPLICABILITY-001":
        return "applicability"
    assert diagnostic_code in DECISION_FAILURE_CODES
    return DECISION_FAILURE_KIND_BY_CODE.get(diagnostic_code, "protocol")


# Known counters are shared by every pre-response decision, including the
# request-independent branch.
KNOWN_COUNT_KEYS = ("files", "source_bytes", "model_records", "stdout_bytes")


# The stage/code cross product is closed here rather than being inferred by
# each writer.  A code may intentionally serve more than one measurement
# point (LIMIT-003), but only the listed stages are legal for that code and
# all other combinations are rejected.
DECISION_FAILURE_MATRIX: dict[str, dict[str, Any]] = {
    code: {
        "allowed_stages": frozenset(stages),
        "diagnostic_code": code,
        "failure_kind": decision_failure_kind(code),
        "ref_permission": "catalog",
        "known_counts": KNOWN_COUNT_KEYS,
        "outcome": outcome,
        "exit_code": 3,
    }
    for code, (stages, outcome) in {
        "CSV-NEXT-CONFIG-001": (("config_validation",), "payload_unavailable"),
        "CSV-NEXT-CONFIG-002": (("config_validation",), "payload_unavailable"),
        "CSV-NEXT-PROJECT-001": (("project_validation",), "payload_unavailable"),
        "CSV-NEXT-PROJECT-002": (("project_validation",), "payload_unavailable"),
        "CSV-NEXT-SOURCE-001": (("source_read",), "partial_safe"),
        "CSV-NEXT-SOURCE-002": (("source_integrity",), "payload_unavailable"),
        "CSV-NEXT-SOURCE-003": (
            ("source_selection", "source_read", "source_integrity"),
            "payload_unavailable",
        ),
        "CSV-NEXT-TARGET-001": (("target_resolution",), "payload_unavailable"),
        "CSV-NEXT-TRUST-001": (("trust_validation",), "payload_unavailable"),
        "CSV-NEXT-TRUST-002": (("trust_validation",), "payload_unavailable"),
        "CSV-NEXT-TRUST-003": (("trust_validation",), "payload_unavailable"),
        "CSV-NEXT-NODE-001": (("node_discovery",), "payload_unavailable"),
        "CSV-NEXT-NODE-002": (("node_spawn",), "payload_unavailable"),
        "CSV-NEXT-NODE-003": (("node_timeout",), "payload_unavailable"),
        "CSV-NEXT-NODE-004": (("node_process",), "payload_unavailable"),
        "CSV-NEXT-LIMIT-001": (("source_read",), "payload_unavailable"),
        "CSV-NEXT-LIMIT-002": (("source_selection",), "payload_unavailable"),
        "CSV-NEXT-LIMIT-003": (
            (
                "adapter_stdout_capture",
                "adapter_stderr_capture",
                "response_raw_bytes",
                "response_decode",
                "public_stderr_capture",
            ),
            "payload_unavailable",
        ),
        "CSV-NEXT-LIMIT-004": (("adapter_heap",), "payload_unavailable"),
        "CSV-NEXT-LIMIT-005": (("model_validation",), "payload_unavailable"),
        "CSV-NEXT-PROTOCOL-001": (
            (
                "stdin_encode",
                "response_decode",
                "response_protocol",
                "response_schema",
                "response_validation",
            ),
            "payload_unavailable",
        ),
        "CSV-NEXT-EXPORT-001": (("response_validation",), "payload_unavailable"),
        "CSV-NEXT-IDENTITY-001": (("response_validation",), "payload_unavailable"),
        "CSV-NEXT-FLOW-001": (("response_validation",), "partial_safe"),
        "CSV-NEXT-TYPE-001": (("response_validation",), "partial_safe"),
    }.items()
}


def decision_failure_spec(diagnostic_code: str, stage: str) -> dict[str, Any]:
    """Return the catalog-derived row for one legal failure combination."""

    assert diagnostic_code in DECISION_FAILURE_MATRIX
    spec = DECISION_FAILURE_MATRIX[diagnostic_code]
    assert stage in spec["allowed_stages"]
    entry = _diagnostic_catalog()[diagnostic_code]
    assert spec["outcome"] == entry["outcome"]
    assert spec["failure_kind"] == decision_failure_kind(diagnostic_code)
    assert spec["ref_permission"] == "catalog"
    return {
        **spec,
        "ref_permission": entry["ref_permission"],
        "known_counts": KNOWN_COUNT_KEYS,
    }


PROVENANCE_FIELDS = (
    "request",
    "limits",
    "source_plan",
    "toolchain",
    "trusted_environment",
    "compatibility",
    "process_launch",
    "budget",
)
PROVENANCE_SOURCE_STAGES = frozenset({"source_selection", "source_read", "source_integrity"})
PROVENANCE_TRUST_STAGES = frozenset({"trust_validation"})
PROVENANCE_EARLY_STAGES = frozenset({"config_validation", "project_validation"})
PROVENANCE_LATE_STAGES = (
    DECISION_FAILURE_STAGES
    - PROVENANCE_SOURCE_STAGES
    - PROVENANCE_TRUST_STAGES
    - PROVENANCE_EARLY_STAGES
)


def _expected_provenance_observed(stage: str) -> frozenset[str]:
    """Return the one canonical observed prefix for a failure stage."""

    assert stage in DECISION_FAILURE_STAGES
    if stage in PROVENANCE_EARLY_STAGES:
        return frozenset()
    if stage in PROVENANCE_SOURCE_STAGES:
        return frozenset({"limits", "source_plan"})
    if stage in PROVENANCE_TRUST_STAGES:
        return frozenset(
            {
                "limits",
                "source_plan",
                "toolchain",
                "trusted_environment",
                "compatibility",
                "process_launch",
            }
        )
    # Once the source and limits have been observed, later failure rows carry
    # that prefix plus the runtime/trust observations available at the same
    # boundary.  The request remains unobserved for a request-independent
    # failure and budget is controlled separately by run_context.
    assert stage in PROVENANCE_LATE_STAGES
    return frozenset(
        {
            "limits",
            "source_plan",
            "toolchain",
            "trusted_environment",
            "compatibility",
            "process_launch",
        }
    )


def validate_stage_dependent_provenance(value: dict[str, Any]) -> None:
    """Validate the closed observed-prefix contract for one failure stage."""

    assert set(value) == {"kind", "stage", "failure_code", "observed"}
    assert value["kind"] in {"request_bound", "request_independent"}
    observed = value["observed"]
    assert set(observed) == set(PROVENANCE_FIELDS)
    for field_name in PROVENANCE_FIELDS:
        row = observed[field_name]
        assert set(row) == {"state", "value"}
        assert row["state"] in {"observed", "unobserved"}
        if row["state"] == "observed":
            assert row["value"] is True
        else:
            assert row["value"] is None
    if value["kind"] == "request_bound":
        assert value["stage"] is None and value["failure_code"] is None
        assert all(row == {"state": "observed", "value": True} for row in observed.values())
        return
    stage = value["stage"]
    code = value["failure_code"]
    assert isinstance(stage, str) and isinstance(code, str)
    decision_failure_spec(code, stage)
    expected_observed = _expected_provenance_observed(stage)
    assert observed["request"] == {"state": "unobserved", "value": None}
    for field_name in PROVENANCE_FIELDS:
        if field_name == "budget":
            continue
        expected = (
            {"state": "observed", "value": True}
            if field_name in expected_observed
            else {"state": "unobserved", "value": None}
        )
        assert observed[field_name] == expected


@dataclass(frozen=True, kw_only=True)
class PreResponseFailureDecision:
    """The sole authority when no schema-valid adapter response exists."""

    request: ValidatedAdapterRequest | None
    run_context: NextRunContext
    stage: str
    diagnostic_code: str
    diagnostic: dict[str, Any]
    known_counts: dict[str, int | None]
    outcome: str = "payload_unavailable"
    payload_available: bool = False
    artifact_paths: tuple[str, ...] = ()
    exit_code: int = 3
    decision_context: NextDecisionContext
    publication_context: NextPublicationContext

    def __post_init__(self) -> None:
        object.__setattr__(self, "request", copy.deepcopy(self.request))
        object.__setattr__(self, "run_context", canonical_run_context(**self.run_context))
        assert self.stage in DECISION_FAILURE_STAGES
        assert self.diagnostic_code in DECISION_FAILURE_CODES
        failure_spec = decision_failure_spec(self.diagnostic_code, self.stage)
        assert failure_spec["outcome"] == "payload_unavailable"
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
        request_values: dict[str, Any] = dict(self.request) if self.request is not None else {}
        decision_context = self.decision_context
        assert decision_context is not None
        assert decision_context.run_context == self.run_context
        assert decision_context.stage == self.stage
        assert decision_context.diagnostic_code == self.diagnostic_code
        assert decision_context.failure_kind == decision_failure_kind(self.diagnostic_code)
        assert decision_context.outcome == self.outcome
        assert decision_context.payload_unavailable is True
        assert decision_context.exit_code == self.exit_code
        assert decision_context.known_counts == known_counts
        if self.request is not None:
            assert self.request["run_context"] == self.run_context
            assert decision_context.request_id == request_values.get("request_id")
            assert tuple(decision_context.targets) == tuple(request_values.get("targets", ()))
            assert decision_context.limits == request_values.get("limits")
        object.__setattr__(self, "decision_context", decision_context)
        context = self.publication_context
        assert context is not None
        assert context.run_context == self.run_context
        assert tuple(context.source_failure_ledger) == tuple(decision_context.source_failure_ledger)
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


@dataclass(frozen=True, kw_only=True)
class NotApplicableDecision:
    """Closed no-Next applicability outcome with the same downstream shape."""

    request: ValidatedAdapterRequest
    run_context: NextRunContext
    diagnostic: dict[str, Any]
    known_counts: dict[str, int | None]
    outcome: str = "not_applicable"
    payload_available: bool = False
    artifact_paths: tuple[str, ...] = ()
    exit_code: int = 0
    decision_context: NextDecisionContext
    publication_context: NextPublicationContext

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
        decision_context = self.decision_context
        assert decision_context is not None
        assert decision_context.outcome == self.outcome
        assert decision_context.payload_unavailable is False
        assert decision_context.exit_code == self.exit_code
        assert decision_context.known_counts == self.known_counts
        assert decision_context.run_context == self.run_context
        assert decision_context.request_id == self.request.get("request_id")
        assert tuple(decision_context.targets) == tuple(self.request.get("targets", ()))
        assert decision_context.limits == self.request.get("limits")
        object.__setattr__(self, "decision_context", decision_context)
        context = self.publication_context
        assert context is not None
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


def is_next_run_decision(value: object) -> TypeGuard[NextRunDecision]:
    """Return whether a value is one of the three closed run decisions."""

    return isinstance(
        value, (ValidatedResponseDecision, PreResponseFailureDecision, NotApplicableDecision)
    )


def decision_public_diagnostics(decision: NextRunDecision) -> list[dict[str, Any]]:
    """Return the decision-owned public diagnostics used by every writer.

    No caller-supplied diagnostic list is accepted at the publication
    boundary.  The rows are derived from the immutable decision's validated
    failure evidence and the fixed diagnostic catalog.
    """

    assert is_next_run_decision(decision)
    if isinstance(decision, (PreResponseFailureDecision, NotApplicableDecision)):
        return [copy.deepcopy(decision.diagnostic)]
    if decision.target_failures:
        entry = _diagnostic_catalog()["CSV-NEXT-TARGET-001"]
        return [
            {
                "type": "diagnostic",
                "schema": "code-structure-viz.diagnostic/v1",
                "code": "CSV-NEXT-TARGET-001",
                "severity": entry["severity"],
                "domain": "next",
                "path": failure["target_key"].removeprefix("path:"),
                "symbol": None,
                "line": None,
                "reason": failure["reason"],
                "recoverable": entry["recoverable"],
                "message": entry["message"],
                "outcome": entry["outcome"],
                "ref_permission": entry["ref_permission"],
            }
            for failure in decision.target_failures
        ]
    if decision.export_failures:
        entry = _diagnostic_catalog()["CSV-NEXT-EXPORT-001"]
        return [
            {
                "type": "diagnostic",
                "schema": "code-structure-viz.diagnostic/v1",
                "code": "CSV-NEXT-EXPORT-001",
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
        ]
    code = decision.gate.get("diagnostic_code")
    if isinstance(code, str):
        entry = _diagnostic_catalog()[code]
        return [
            {
                "type": "diagnostic",
                "schema": "code-structure-viz.diagnostic/v1",
                "code": code,
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
        ]
    if decision.gate["outcome"] == "partial_safe":
        entry = _diagnostic_catalog()["CSV-NEXT-FLOW-001"]
        return [
            {
                "type": "diagnostic",
                "schema": "code-structure-viz.diagnostic/v1",
                "code": "CSV-NEXT-FLOW-001",
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
        ]
    return []


def _public_diagnostic_jsonl(diagnostics: list[dict[str, Any]]) -> bytes:
    """Encode decision-owned public diagnostics using canonical JSONL."""

    return b"".join(canonical_json_bytes(item) + b"\n" for item in diagnostics)


def _decision_exit_code(decision: NextRunDecision) -> int:
    """Read the sealed exit outcome without requiring one shared field shape."""

    if isinstance(decision, ValidatedResponseDecision):
        return 0 if decision.gate["outcome"] in {"complete", "not_applicable"} else 3
    return decision.exit_code


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
        "unit": "utf8_bytes_per_selected_stdout_stream",
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
        "unit": "utf8_bytes_per_selected_stdout_stream",
        "measurement": "canonical_selected_stream_encode_before_write",
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
    """Trusted snapshot reader used to model one bounded source acquisition."""

    def __init__(
        self,
        files: dict[str, bytes],
        *,
        snapshot_id: str = "snapshot-v1",
        revision: str = "revision-v1",
        revision_after: str | None = None,
        source_graph: dict[str, Any] | None = None,
        read_failures: Mapping[str, str] | None = None,
    ) -> None:
        self._files = dict(files)
        self.snapshot_id = snapshot_id
        self.revision_before = revision
        self.revision_after = revision if revision_after is None else revision_after
        self._source_graph = copy.deepcopy(source_graph)
        self._read_failures = dict(read_failures or {})
        self.read_counts: dict[str, int] = {}
        self.enumeration_calls = 0
        self.sealed = False
        self.seal_calls = 0

    def enumerate_paths(
        self, project_roots: tuple[str, ...], hard_exclusions: tuple[str, ...]
    ) -> tuple[str, ...]:
        """Enumerate the trusted snapshot; callers cannot submit this set."""

        assert not self.sealed
        self.enumeration_calls += 1
        excluded = tuple(f"{name}/" for name in hard_exclusions)
        paths = [
            path
            for path in self._files
            if any(_under(path, root) for root in project_roots)
            and not any(
                path == name or path.startswith(prefix)
                for name, prefix in zip(hard_exclusions, excluded, strict=True)
            )
        ]
        return tuple(sorted(paths, key=_path_sort_key))

    def read(self, path: str) -> bytes:
        assert not self.sealed, "SourceView is sealed; filesystem reads are forbidden"
        assert path in self._files, path
        self.read_counts[path] = self.read_counts.get(path, 0) + 1
        assert self.read_counts[path] == 1, path
        if path in self._read_failures:
            raise SourceAcquisitionError(
                self._read_failures[path],
                "source_read",
                f"trusted snapshot read failed: {path}",
            )
        return self._files[path]

    def seal(self) -> int:
        assert not self.sealed
        self.sealed = True
        self.seal_calls += 1
        return self.seal_calls

    @property
    def source_graph(self) -> dict[str, Any] | None:
        """Return the reader-owned raw graph observation, if supplied."""

        return copy.deepcopy(self._source_graph)

    @property
    def read_failures(self) -> dict[str, str]:
        """Return the typed failures observed by this reader."""

        return copy.deepcopy(self._read_failures)


class SourceAcquisitionError(AssertionError):
    """Typed fail-closed result for malformed or drifting source snapshots."""

    def __init__(self, code: str, stage: str, message: str) -> None:
        self.code = code
        self.stage = stage
        super().__init__(message)


PACKAGE_APPLICABILITY_SCHEMA = "code-structure-viz.next-package-applicability/v1"
PACKAGE_APPLICABILITY_STATES = ("applicable", "non_applicable", "malformed")
PACKAGE_APPLICABILITY_EVIDENCE = (
    "direct_next_dependency",
    "no_direct_next",
    "missing_package",
    "malformed_package",
)


@dataclass(frozen=True, kw_only=True)
class PackageApplicabilityEntry:
    """One project-root observation used to decide whether Next is applicable."""

    project_root: str
    package_path: str
    state: str
    evidence: str

    def __post_init__(self) -> None:
        _assert_path(self.project_root, allow_root=True)
        _assert_path(self.package_path)
        assert self.state in PACKAGE_APPLICABILITY_STATES
        assert self.evidence in PACKAGE_APPLICABILITY_EVIDENCE
        expected = {
            "applicable": {"direct_next_dependency"},
            "non_applicable": {"no_direct_next", "missing_package"},
            "malformed": {"malformed_package"},
        }
        assert self.evidence in expected[self.state]

    def as_dict(self) -> dict[str, str]:
        return {
            "project_root": self.project_root,
            "package_path": self.package_path,
            "state": self.state,
            "evidence": self.evidence,
        }


@dataclass(frozen=True, kw_only=True)
class PackageApplicabilityMatrix:
    """Immutable matrix derived solely from frozen package.json bytes.

    This is intentionally a separate authority from source import discovery:
    a directory name, lockfile, config file, or indirect dependency cannot
    make a project applicable.  A malformed package observation poisons the
    whole matrix; all non-applicable projects are a closed not-applicable run.
    """

    entries: tuple[PackageApplicabilityEntry, ...]
    aggregate_state: str

    def __post_init__(self) -> None:
        entries = tuple(self.entries)
        assert entries == tuple(sorted(entries, key=lambda item: _path_sort_key(item.project_root)))
        assert len({entry.project_root for entry in entries}) == len(entries)
        assert entries
        assert self.aggregate_state in PACKAGE_APPLICABILITY_STATES
        expected = (
            "malformed"
            if any(entry.state == "malformed" for entry in entries)
            else "applicable"
            if any(entry.state == "applicable" for entry in entries)
            else "non_applicable"
        )
        assert self.aggregate_state == expected
        object.__setattr__(self, "entries", entries)

    @property
    def applicable_projects(self) -> tuple[str, ...]:
        return tuple(entry.project_root for entry in self.entries if entry.state == "applicable")

    @property
    def non_applicable_projects(self) -> tuple[str, ...]:
        return tuple(
            entry.project_root for entry in self.entries if entry.state == "non_applicable"
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": PACKAGE_APPLICABILITY_SCHEMA,
            "version": 1,
            "projects": [entry.as_dict() for entry in self.entries],
            "aggregate_state": self.aggregate_state,
            "applicable_projects": list(self.applicable_projects),
            "non_applicable_projects": list(self.non_applicable_projects),
        }

    def __getattribute__(self, name: str) -> Any:
        value = object.__getattribute__(self, name)
        if name == "entries":
            return tuple(copy.deepcopy(value))
        return value


def _package_json(payload: bytes, path: str) -> dict[str, Any]:
    """Parse one package.json with duplicate-key and encoding rejection."""

    if not isinstance(payload, bytes):
        raise ValueError(f"package bytes are not bytes: {path}")

    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"duplicate package key: {key}")
            value[key] = item
        return value

    text = payload.decode("utf-8-sig")
    if text.startswith("\ufeff"):
        raise ValueError(f"multiple package BOM: {path}")
    value = json.loads(
        text,
        object_pairs_hook=reject_duplicate_keys,
        parse_constant=lambda _constant: (_ for _ in ()).throw(ValueError("non-finite")),
    )
    if not isinstance(value, dict):
        raise ValueError(f"package root is not an object: {path}")
    return value


def derive_package_applicability_matrix(
    package_bytes: Mapping[str, bytes], project_roots: tuple[str, ...] | list[str]
) -> PackageApplicabilityMatrix:
    """Derive the closed applicability matrix from observed package bytes.

    ``package_bytes`` is an observation map, not a caller-supplied state map.
    Missing package paths are a valid non-applicable observation; malformed
    bytes/table/value are globally malformed and therefore unavailable.
    """

    roots = tuple(project_roots)
    assert roots and len(roots) == len(set(roots))
    for root in roots:
        _assert_path(root, allow_root=True)
    entries: list[PackageApplicabilityEntry] = []
    for root in sorted(roots, key=_path_sort_key):
        package_path = "package.json" if root == "." else f"{root.rstrip('/')}/package.json"
        payload = package_bytes.get(package_path)
        if payload is None:
            entries.append(
                PackageApplicabilityEntry(
                    project_root=root,
                    package_path=package_path,
                    state="non_applicable",
                    evidence="missing_package",
                )
            )
            continue
        try:
            package = _package_json(payload, package_path)
            direct_next = False
            malformed = False
            for table_name in ("dependencies", "devDependencies"):
                if table_name not in package:
                    continue
                table = package[table_name]
                if not isinstance(table, dict):
                    malformed = True
                    continue
                if "next" not in table:
                    continue
                version = table["next"]
                if not isinstance(version, str) or not version.strip():
                    malformed = True
                else:
                    direct_next = True
            state = "malformed" if malformed else "applicable" if direct_next else "non_applicable"
            evidence = (
                "malformed_package"
                if malformed
                else ("direct_next_dependency" if direct_next else "no_direct_next")
            )
        except (UnicodeDecodeError, ValueError, json.JSONDecodeError):
            state = "malformed"
            evidence = "malformed_package"
        entries.append(
            PackageApplicabilityEntry(
                project_root=root,
                package_path=package_path,
                state=state,
                evidence=evidence,
            )
        )
    aggregate_state = (
        "malformed"
        if any(entry.state == "malformed" for entry in entries)
        else "applicable"
        if any(entry.state == "applicable" for entry in entries)
        else "non_applicable"
    )
    return PackageApplicabilityMatrix(entries=tuple(entries), aggregate_state=aggregate_state)


@dataclass(frozen=True)
class SourceAcquisitionSeal:
    """Atomic final-plan/source-view pair produced by the two-phase reader."""

    final_plan: dict[str, Any]
    source_view: dict[str, Any]
    plan_digest: str
    source_view_fingerprint: str
    seal_id: str
    seal_operation: int
    snapshot_id: str
    revision_before: str
    revision_after: str
    source_graph: dict[str, Any]
    captured_files: dict[str, bytes]
    package_applicability: PackageApplicabilityMatrix = field(init=False)

    def __post_init__(self) -> None:
        graph = copy.deepcopy(self.source_graph)
        assert set(graph) == {"nodes", "edges", "open_edges"}
        assert self.plan_digest == digest(self.final_plan)
        assert self.source_view_fingerprint == digest(self.source_view)
        assert self.source_view["source_graph_digest"] == digest(graph)
        assert self.seal_id == digest(
            {
                "plan_digest": self.plan_digest,
                "source_view_fingerprint": self.source_view_fingerprint,
                "seal_operation": self.seal_operation,
                "snapshot_id": self.snapshot_id,
                "revision_before": self.revision_before,
                "revision_after": self.revision_after,
                "source_graph_digest": digest(graph),
            }
        )
        object.__setattr__(self, "source_graph", graph)
        captured = {path: bytes(payload) for path, payload in self.captured_files.items()}
        assert tuple(sorted(captured, key=_path_sort_key)) == tuple(captured)
        object.__setattr__(self, "captured_files", captured)
        project_roots = tuple(project["root"] for project in self.final_plan.get("projects", ()))
        if project_roots:
            object.__setattr__(
                self,
                "package_applicability",
                derive_package_applicability_matrix(captured, project_roots),
            )
        else:
            # A malformed hand-built plan is rejected above by normal plan
            # validation in production-shaped callers; keep this constructor
            # fail-closed for legacy isolated graph fixtures as well.
            raise AssertionError("source plan must contain project roots")

    def __getattribute__(self, name: str) -> Any:
        value = object.__getattribute__(self, name)
        if name in {
            "final_plan",
            "source_view",
            "source_graph",
            "captured_files",
            "package_applicability",
        }:
            return copy.deepcopy(value)
        return value


@dataclass(frozen=True)
class SourceDiscoveryIntent:
    """Only the caller's discovery *intent*, never a resolved source plan.

    Project configuration, local ``extends``, final paths, and role mapping are
    derived by :func:`seal_source_acquisition` from the frozen control bytes
    and read-only inventory.  Keeping those values out of this object prevents
    a caller from pairing a plan/view with bytes it did not actually read.
    """

    project_roots: tuple[str, ...]
    control_candidates: tuple[str, ...]
    program_suffixes: tuple[str, ...] = SOURCE_PLAN_PROGRAM_SUFFIXES
    context_suffixes: tuple[str, ...] = SOURCE_PLAN_CONTEXT_SUFFIXES
    hard_exclusions: tuple[str, ...] = SOURCE_PLAN_HARD_EXCLUSIONS


def _default_source_graph(
    files: Mapping[str, bytes], project_roots: tuple[str, ...] = (".",)
) -> dict[str, Any]:
    """Create the reader-owned graph used when a fixture has no edge witness."""

    nodes = [
        {
            "id": digest({"kind": "source_node", "path": path}),
            "path": path,
            "project_root": next(
                (root for root in sorted(project_roots, key=_path_sort_key) if _under(path, root)),
                ".",
            ),
        }
        for path in sorted(files, key=_path_sort_key)
    ]
    return {
        "nodes": sorted(nodes, key=canonical_json_bytes),
        "edges": [],
        "open_edges": [],
    }


_RELATIVE_IMPORT_RE = re.compile(
    r"(?:from\s*|import\s*|export\s+[^;]*?\sfrom\s*)[\"'](\.{1,2}/[^\"']+)[\"']"
)


def _derive_source_graph_from_frozen_bytes(
    files: Mapping[str, bytes],
    project_roots: tuple[str, ...],
    plan: Mapping[str, Any],
) -> dict[str, Any]:
    """Derive the raw source graph from the sealed bytes, never from a caller.

    The graph is intentionally lexical and conservative at this pre-
    implementation boundary: a relative import resolves only to one exact
    inventory candidate.  Ambiguous or missing candidates remain open edges,
    which prevents a later locality proof from treating an unobserved edge as
    safe.  Config ``extends`` edges come from the same frozen plan.
    """

    graph = _default_source_graph(files, project_roots)
    nodes = list(graph["nodes"])
    node_id_by_path = {node["path"]: node["id"] for node in nodes}
    candidates_by_stem: dict[str, list[str]] = {}
    suffixes = ("", ".ts", ".tsx", ".js", ".jsx", ".d.ts")
    for path in node_id_by_path:
        if not path.endswith(SOURCE_PLAN_PROGRAM_SUFFIXES + SOURCE_PLAN_CONTEXT_SUFFIXES):
            continue
        stem = path[: -len(".d.ts")] if path.endswith(".d.ts") else path.rsplit(".", 1)[0]
        candidates_by_stem.setdefault(stem, []).append(path)
    for values in candidates_by_stem.values():
        values.sort(key=_path_sort_key)

    edges: list[dict[str, str]] = []
    open_edges: list[dict[str, str]] = []
    for source_path, source_id in sorted(
        node_id_by_path.items(), key=lambda item: _path_sort_key(item[0])
    ):
        if not source_path.endswith(SOURCE_PLAN_PROGRAM_SUFFIXES + SOURCE_PLAN_CONTEXT_SUFFIXES):
            continue
        try:
            text = files[source_path].decode("utf-8")
        except UnicodeDecodeError:
            open_edges.append({"source": source_id})
            continue
        for specifier in _RELATIVE_IMPORT_RE.findall(text):
            parent = str(Path(source_path).parent)
            raw_target = f"{parent}/{specifier}" if parent != "." else specifier
            parts: list[str] = []
            escapes = False
            for part in raw_target.split("/"):
                if part in {"", "."}:
                    continue
                if part == "..":
                    if not parts:
                        escapes = True
                        break
                    parts.pop()
                else:
                    parts.append(part)
            if escapes:
                open_edges.append({"source": source_id})
                continue
            normalized = "/".join(parts)
            possible = [
                candidate
                for candidate in (
                    normalized,
                    *(f"{normalized}{suffix}" for suffix in suffixes[1:]),
                    *(f"{normalized}/index{suffix}" for suffix in suffixes[1:]),
                )
                if candidate in node_id_by_path
            ]
            unique = tuple(dict.fromkeys(possible))
            if len(unique) == 1:
                edges.append({"source": source_id, "target": node_id_by_path[unique[0]]})
            else:
                open_edges.append({"source": source_id})

    for extension in plan.get("local_extends", ()):
        source_path = extension["config_path"]
        for target_path in extension["extends"]:
            source_id = node_id_by_path.get(source_path)
            target_id = node_id_by_path.get(target_path)
            if source_id is None or target_id is None:
                if source_id is not None:
                    open_edges.append({"source": source_id})
            else:
                edges.append({"source": source_id, "target": target_id})
    return {
        "nodes": sorted(nodes, key=canonical_json_bytes),
        "edges": sorted(edges, key=canonical_json_bytes),
        "open_edges": sorted(open_edges, key=canonical_json_bytes),
    }


def _strip_jsonc(payload: bytes, path: str) -> str:
    """Normalize the deliberately small JSONC dialect used by project controls.

    BOM, line/block comments, and trailing commas are accepted only outside
    quoted strings.  The parser remains strict JSON after this lexical pass;
    duplicate keys and non-finite numbers are rejected by ``_control_json``.
    """

    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise SourceAcquisitionError(
            "CSV-NEXT-CONFIG-002", "source_control", f"invalid UTF-8 control file: {path}"
        ) from exc
    output: list[str] = []
    index = 0
    in_string = False
    escaped = False
    while index < len(text):
        character = text[index]
        if in_string:
            output.append(character)
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            index += 1
            continue
        if character == '"':
            in_string = True
            output.append(character)
            index += 1
            continue
        if character == "/" and index + 1 < len(text) and text[index + 1] == "/":
            index += 2
            while index < len(text) and text[index] not in "\r\n":
                index += 1
            continue
        if character == "/" and index + 1 < len(text) and text[index + 1] == "*":
            index += 2
            end = text.find("*/", index)
            if end < 0:
                raise SourceAcquisitionError(
                    "CSV-NEXT-CONFIG-002", "source_control", f"unterminated comment: {path}"
                )
            index = end + 2
            continue
        if character == ",":
            lookahead = index + 1
            while lookahead < len(text) and text[lookahead].isspace():
                lookahead += 1
            if lookahead < len(text) and text[lookahead] in "]}":
                index += 1
                continue
        output.append(character)
        index += 1
    if in_string or escaped:
        raise SourceAcquisitionError(
            "CSV-NEXT-CONFIG-002", "source_control", f"unterminated string: {path}"
        )
    return "".join(output)


def _control_json(contents: dict[str, bytes], path: str) -> dict[str, Any]:
    """Decode one frozen control file; malformed control is typed failure."""

    payload = contents.get(path)
    if payload is None:
        raise SourceAcquisitionError(
            "CSV-NEXT-CONFIG-002", "source_control", f"control file was not observed: {path}"
        )

    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"duplicate control key: {key}")
            value[key] = item
        return value

    try:
        value = json.loads(
            _strip_jsonc(payload, path),
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=lambda _constant: (_ for _ in ()).throw(ValueError("non-finite")),
        )
    except (SourceAcquisitionError, ValueError, json.JSONDecodeError) as exc:
        raise SourceAcquisitionError(
            "CSV-NEXT-CONFIG-002", "source_control", f"malformed control file: {path}"
        ) from exc
    if not isinstance(value, dict):
        raise SourceAcquisitionError(
            "CSV-NEXT-CONFIG-002", "source_control", f"control file is not an object: {path}"
        )
    return value


def _normalise_control_path(value: str, *, project_root: str) -> str:
    """Resolve a config-relative path into the repository-relative form."""

    if not isinstance(value, str) or not value or value.startswith("/") or "\\" in value:
        raise AssertionError("absolute control path")
    if any(part == ".." for part in value.split("/")):
        raise AssertionError("parent traversal is not a control path")
    if any(part == "" for part in value.split("/") if part != "."):
        raise AssertionError("empty control path segment")
    candidate = value
    if project_root != "." and not candidate.startswith(f"{project_root}/"):
        candidate = f"{project_root.rstrip('/')}/{candidate}"
    parts = candidate.split("/")
    resolved: list[str] = []
    for part in parts:
        if part in {"", "."}:
            continue
        if part == "..":
            raise AssertionError("parent traversal is not a control path")
        else:
            resolved.append(part)
    result = "/".join(resolved) or "."
    _assert_path(result, allow_root=True)
    return result


def _validate_segment_glob(pattern: str, *, project_root: str) -> str:
    """Validate and normalize the intentionally small include/exclude grammar."""

    normalized = _normalise_control_path(pattern, project_root=project_root)
    segments = normalized.split("/")
    for segment in segments:
        if segment == "**":
            continue
        # A glob token is a complete path segment.  Character classes,
        # braces, extglobs and embedded ``**`` are deliberately not part of
        # the contract and must not accidentally acquire fnmatch semantics.
        if "**" in segment or any(character in segment for character in "[]{}()!+"):
            raise SourceAcquisitionError(
                "CSV-NEXT-CONFIG-002",
                "source_control",
                f"unsupported include/exclude pattern: {pattern}",
            )
    return normalized


def _segment_glob_matches(pattern: str, candidate: str) -> bool:
    """Match only ``*``, ``?`` and whole-segment ``**`` path tokens."""

    pattern_segments = tuple(pattern.split("/"))
    candidate_segments = tuple(candidate.split("/"))

    def one_segment_matches(segment_pattern: str, segment_value: str) -> bool:
        expression = "".join(
            ".*" if character == "*" else "." if character == "?" else re.escape(character)
            for character in segment_pattern
        )
        return re.fullmatch(expression, segment_value, flags=re.DOTALL) is not None

    @cache
    def visit(pattern_index: int, candidate_index: int) -> bool:
        if pattern_index == len(pattern_segments):
            return candidate_index == len(candidate_segments)
        if pattern_segments[pattern_index] == "**":
            return visit(pattern_index + 1, candidate_index) or (
                candidate_index < len(candidate_segments)
                and visit(pattern_index, candidate_index + 1)
            )
        return (
            candidate_index < len(candidate_segments)
            and one_segment_matches(
                pattern_segments[pattern_index], candidate_segments[candidate_index]
            )
            and visit(pattern_index + 1, candidate_index + 1)
        )

    return visit(0, 0)


def _segment_glob_matches_path_or_descendant(pattern: str, candidate: str) -> bool:
    """Apply a segment pattern to a path or to one of its directory prefixes."""

    candidate_segments = candidate.split("/")
    return any(
        _segment_glob_matches(pattern, "/".join(candidate_segments[:index]))
        for index in range(1, len(candidate_segments) + 1)
    )


def _derive_project_descriptors_from_control_bytes(
    project_roots: tuple[str, ...],
    contents: dict[str, bytes],
    *,
    program_suffixes: tuple[str, ...],
    context_suffixes: tuple[str, ...],
    inventory_paths: tuple[str, ...] | None = None,
) -> list[dict[str, Any]]:
    """Derive config closure and final membership from frozen control bytes.

    The inventory paths are names only; file content is read later, after this
    function has resolved ``files/include/exclude``.  Internal metadata keys
    are consumed by ``seal_source_acquisition`` before the public plan is
    constructed.
    """

    paths = tuple(inventory_paths or tuple(contents))
    path_set = set(paths)
    descriptors: list[dict[str, Any]] = []

    def control_path_for_root(root: str) -> str | None:
        candidates = [
            path
            for path in path_set
            if path
            in {
                "tsconfig.json" if root == "." else f"{root.rstrip('/')}/tsconfig.json",
                "jsconfig.json" if root == "." else f"{root.rstrip('/')}/jsconfig.json",
            }
        ]
        return next(
            (
                path
                for path in sorted(candidates, key=_path_sort_key)
                if Path(path).name == "tsconfig.json"
            ),
            next(iter(sorted(candidates, key=_path_sort_key)), None),
        )

    def control_parent_path(path: str, root: str, extends: str) -> str:
        if extends.startswith("."):
            base = str(Path(path).parent)
            candidate = f"{base}/{extends}" if base != "." else extends
            return _normalise_control_path(candidate, project_root=root)
        return _normalise_control_path(extends, project_root=root)

    def control_closure(
        path: str,
        root: str,
        visiting: set[str],
    ) -> tuple[dict[str, Any], tuple[str, ...], tuple[dict[str, Any], ...]]:
        if path in visiting:
            raise SourceAcquisitionError(
                "CSV-NEXT-CONFIG-002", "source_control", f"extends cycle: {path}"
            )
        visiting.add(path)
        control = _control_json(contents, path)
        allowed_keys = {"compilerOptions", "include", "exclude", "files", "extends"}
        if set(control) - allowed_keys:
            raise SourceAcquisitionError(
                "CSV-NEXT-CONFIG-002", "source_control", f"unknown control key: {path}"
            )
        merged: dict[str, Any] = {}
        closure: list[str] = []
        edges: list[dict[str, Any]] = []
        extends = control.get("extends")
        if extends is not None and not isinstance(extends, str):
            raise SourceAcquisitionError(
                "CSV-NEXT-CONFIG-002", "source_control", "extends must be one local path"
            )
        if isinstance(extends, str):
            parent = control_parent_path(path, root, extends)
            if parent not in path_set:
                raise SourceAcquisitionError(
                    "CSV-NEXT-CONFIG-002",
                    "source_control",
                    f"extends path was not captured: {parent}",
                )
            parent_value, parent_closure, parent_edges = control_closure(parent, root, visiting)
            merged.update(parent_value)
            closure.extend(parent_closure)
            edges.extend(parent_edges)
            edges.append({"project_root": root, "config_path": path, "extends": [parent]})
            closure.append(parent)
        parent_options = merged.get("compilerOptions", {})
        child_options = control.get("compilerOptions", {})
        if not isinstance(parent_options, dict) or not isinstance(child_options, dict):
            raise SourceAcquisitionError(
                "CSV-NEXT-CONFIG-002", "source_control", "compilerOptions is not an object"
            )
        merged["compilerOptions"] = {**parent_options, **child_options}
        for key in ("include", "exclude", "files"):
            if key in control:
                merged[key] = control[key]
        visiting.remove(path)
        closure.append(path)
        return merged, tuple(dict.fromkeys(closure)), tuple(edges)

    inventory_program_paths = [
        path
        for path in paths
        if any(_under(path, root) for root in project_roots)
        and (path.endswith(program_suffixes) or path.endswith(context_suffixes))
    ]

    for project_root in sorted(project_roots, key=_path_sort_key):
        config_path = control_path_for_root(project_root)
        # A missing control file is still represented deterministically, but
        # it is not included in the sealed bytes or control closure.
        descriptor_config_path = config_path or (
            "tsconfig.json" if project_root == "." else f"{project_root.rstrip('/')}/tsconfig.json"
        )
        if config_path is None:
            effective: dict[str, Any] = {}
            closure: tuple[str, ...] = ()
            extends_edges: tuple[dict[str, Any], ...] = ()
        else:
            effective, closure, extends_edges = control_closure(config_path, project_root, set())

        raw_options = effective.get("compilerOptions", {})
        if not isinstance(raw_options, dict):
            raise SourceAcquisitionError(
                "CSV-NEXT-CONFIG-002", "source_control", "compilerOptions is not an object"
            )
        forbidden_options = {"plugins", "typeRoots", "types"}
        if forbidden_options.intersection(raw_options):
            raise SourceAcquisitionError(
                "CSV-NEXT-CONFIG-002",
                "source_control",
                "package/plugin compiler options are not part of the closed contract",
            )
        allowed_options = {
            "allowJs",
            "checkJs",
            "jsx",
            "module",
            "moduleResolution",
            "baseUrl",
            "paths",
            "outDir",
            "rootDir",
            "declaration",
            "declarationMap",
            "sourceMap",
            "noEmit",
            "incremental",
            "composite",
            "target",
            "lib",
            "strict",
            "esModuleInterop",
            "skipLibCheck",
            "resolveJsonModule",
            "isolatedModules",
            "verbatimModuleSyntax",
        }
        if set(raw_options) - allowed_options:
            raise SourceAcquisitionError(
                "CSV-NEXT-CONFIG-002", "source_control", "unsupported compiler option"
            )
        for option_name in ("allowJs", "checkJs"):
            if option_name in raw_options and not isinstance(raw_options[option_name], bool):
                raise SourceAcquisitionError(
                    "CSV-NEXT-CONFIG-002", "source_control", f"{option_name} must be boolean"
                )
        if "module" in raw_options and raw_options["module"] != "esnext":
            raise SourceAcquisitionError(
                "CSV-NEXT-CONFIG-002", "source_control", "module must be esnext"
            )
        if "moduleResolution" in raw_options and raw_options["moduleResolution"] != "bundler":
            raise SourceAcquisitionError(
                "CSV-NEXT-CONFIG-002", "source_control", "moduleResolution must be bundler"
            )
        base_url_value = raw_options.get("baseUrl")
        if base_url_value is not None and not isinstance(base_url_value, str):
            raise SourceAcquisitionError(
                "CSV-NEXT-CONFIG-002", "source_control", "baseUrl must be a path or null"
            )
        base_url = (
            _normalise_control_path(base_url_value, project_root=project_root)
            if isinstance(base_url_value, str)
            else None
        )
        raw_paths = raw_options.get("paths", {})
        if not isinstance(raw_paths, dict):
            raise SourceAcquisitionError(
                "CSV-NEXT-CONFIG-002", "source_control", "paths must be an object"
            )
        path_aliases: dict[str, list[str]] = {}
        for key, values in raw_paths.items():
            if (
                not isinstance(key, str)
                or not isinstance(values, list)
                or not all(isinstance(value, str) for value in values)
            ):
                raise SourceAcquisitionError(
                    "CSV-NEXT-CONFIG-002", "source_control", "invalid compiler paths"
                )
            path_aliases[key] = [
                _normalise_control_path(value, project_root=project_root) for value in values
            ]
        jsx = raw_options.get("jsx", "preserve")
        if not isinstance(jsx, str) or jsx not in {
            "preserve",
            "react",
            "react-jsx",
            "react-jsxdev",
        }:
            raise SourceAcquisitionError(
                "CSV-NEXT-CONFIG-002", "source_control", "unsupported jsx compiler option"
            )
        compiler_options = {
            "allow_js": raw_options.get("allowJs", False),
            "check_js": raw_options.get("checkJs", False),
            "jsx": jsx,
            "module": "esnext",
            "module_resolution": "bundler",
            "base_url": base_url,
            "paths": path_aliases,
        }

        include = effective.get("include")
        exclude = effective.get("exclude", [])
        explicit_files = effective.get("files", [])
        for name, value in (("include", include), ("exclude", exclude), ("files", explicit_files)):
            if value is not None and (
                not isinstance(value, list) or not all(isinstance(item, str) for item in value)
            ):
                raise SourceAcquisitionError(
                    "CSV-NEXT-CONFIG-002", "source_control", f"{name} must be an array of paths"
                )
        include_values = list(include or [])
        exclude_values = list(exclude or [])
        explicit_values = list(explicit_files or [])
        include_values = [
            _validate_segment_glob(item, project_root=project_root) for item in include_values
        ]
        exclude_values = [
            _validate_segment_glob(item, project_root=project_root) for item in exclude_values
        ]
        source_roots: list[str] = []
        for pattern in include_values:
            normalized = _normalise_control_path(pattern, project_root=project_root)
            static = re.split(r"[*?]", normalized, maxsplit=1)[0].rstrip("/") or project_root
            source_roots.append(static)
        if not source_roots and explicit_values:
            source_roots = [
                _normalise_control_path(str(Path(item).parent), project_root=project_root)
                for item in explicit_values
            ]
        if not source_roots:
            default_src = "src" if project_root == "." else f"{project_root.rstrip('/')}/src"
            source_roots = [
                default_src
                if any(_under(path, default_src) for path in inventory_program_paths)
                else project_root
            ]
        source_roots = sorted(set(source_roots), key=_path_sort_key)

        def matches(pattern: str, candidate: str, *, _project_root: str = project_root) -> bool:
            normalized_pattern = _validate_segment_glob(pattern, project_root=_project_root)
            relative = (
                candidate
                if _project_root == "."
                else candidate.removeprefix(f"{_project_root.rstrip('/')}/")
            )
            relative_pattern = (
                normalized_pattern
                if _project_root == "."
                else normalized_pattern.removeprefix(f"{_project_root.rstrip('/')}/")
            )
            return _segment_glob_matches_path_or_descendant(relative_pattern, relative)

        membership: set[str] = set()
        for candidate in paths:
            if not _under(candidate, project_root):
                continue
            if explicit_values:
                included = candidate in {
                    _normalise_control_path(item, project_root=project_root)
                    for item in explicit_values
                }
            elif include_values:
                included = any(matches(item, candidate) for item in include_values)
            else:
                included = any(_under(candidate, root) for root in source_roots)
            excluded = any(matches(item, candidate) for item in exclude_values)
            if (
                included
                and not excluded
                and (candidate.endswith(program_suffixes) or candidate.endswith(context_suffixes))
            ):
                membership.add(candidate)
        control_paths = tuple(dict.fromkeys(closure))
        descriptors.append(
            {
                "root": project_root,
                "source_roots": source_roots,
                "config_path": descriptor_config_path,
                "compiler_options": compiler_options,
                "_resolved_control_paths": control_paths,
                "_local_extends": extends_edges,
                "_membership": tuple(sorted(membership, key=_path_sort_key)),
            }
        )
    return descriptors


def seal_source_acquisition(
    intent: SourceDiscoveryIntent | dict[str, Any],
    reader: InstrumentedSourceReader,
    inventory: dict[str, Any] | None = None,
    *,
    allow_partial: bool = False,
) -> SourceAcquisitionSeal:
    """Derive and atomically seal the final plan and SourceView.

    ``intent`` contains only discovery intent.  The trusted reader enumerates
    the immutable snapshot internally; callers cannot submit ``observed_paths``
    or an independent plan/view.  ``inventory`` is an optional read-only
    attestation for values such as limits and file digests.  Revision and file
    membership always come from the reader's snapshot and are checked again
    before the single atomic seal.
    """

    forbidden = {
        "final_paths",
        "source_paths",
        "config",
        "local_extends",
        "file_role_map",
        "resolved_control_paths",
        "final_plan",
        "source_view",
    }
    if isinstance(intent, SourceDiscoveryIntent):
        project_roots = tuple(intent.project_roots)
        control_candidates = tuple(intent.control_candidates)
        program_suffixes = tuple(intent.program_suffixes)
        context_suffixes = tuple(intent.context_suffixes)
        hard_exclusions = tuple(intent.hard_exclusions)
    else:
        assert not forbidden.intersection(intent), "resolved source values are not intent"
        allowed_intent_keys = {
            "project_roots",
            "control_candidates",
            "program_suffixes",
            "context_suffixes",
            "hard_exclusions",
        }
        assert set(intent) <= allowed_intent_keys
        project_roots = tuple(intent.get("project_roots", ()))
        control_candidates = tuple(intent.get("control_candidates", ()))
        program_suffixes = tuple(intent.get("program_suffixes", SOURCE_PLAN_PROGRAM_SUFFIXES))
        context_suffixes = tuple(intent.get("context_suffixes", SOURCE_PLAN_CONTEXT_SUFFIXES))
        hard_exclusions = tuple(intent.get("hard_exclusions", SOURCE_PLAN_HARD_EXCLUSIONS))
    inventory = copy.deepcopy(inventory or {})
    allowed_inventory_keys = {
        "head_commit",
        "file_digests",
        "observed_limits",
        "observed_trusted_environment_digest",
    }
    assert set(inventory) <= allowed_inventory_keys
    assert project_roots and len(project_roots) == len(set(project_roots))
    assert control_candidates == tuple(dict.fromkeys(control_candidates))
    assert all(isinstance(path, str) for path in (*project_roots, *control_candidates))
    for path in (*project_roots, *control_candidates):
        _assert_path(path, allow_root=True)
    assert program_suffixes == SOURCE_PLAN_PROGRAM_SUFFIXES
    assert context_suffixes == SOURCE_PLAN_CONTEXT_SUFFIXES
    assert hard_exclusions == SOURCE_PLAN_HARD_EXCLUSIONS
    assert reader.snapshot_id
    revision_before = reader.revision_before
    enumerated_paths = reader.enumerate_paths(project_roots, hard_exclusions)
    assert enumerated_paths == tuple(sorted(set(enumerated_paths), key=_path_sort_key))
    enumerated_set = set(enumerated_paths)
    root_control_paths = {
        path
        for root in project_roots
        for name in SOURCE_PLAN_CONTROL_PATHS
        for path in (name if root == "." else f"{root.rstrip('/')}/{name}",)
        if path in enumerated_set
    }
    assert set(control_candidates) <= root_control_paths
    # Explicit candidates narrow discovery, but never add arbitrary nested
    # config paths.  With no explicit candidates every known root candidate is
    # observed before source membership is resolved.
    # A project-root package.json is always part of the trusted control
    # observation: applicability must not become "missing" merely because a
    # caller narrowed the tsconfig/jsconfig candidate list.  Explicit
    # candidates may narrow config discovery, but cannot suppress this
    # package-owned Node optionality fact.
    package_control_paths = {
        path
        for root in project_roots
        for path in ("package.json" if root == "." else f"{root.rstrip('/')}/package.json",)
        if path in enumerated_set
    }
    selected_control_paths = tuple(
        sorted(set(control_candidates) | package_control_paths, key=_path_sort_key)
    )
    contents: dict[str, bytes] = {}
    failed_paths: set[str] = set()
    control_queue = list(selected_control_paths)
    while control_queue:
        path = control_queue.pop(0)
        if path in contents:
            continue
        try:
            contents[path] = reader.read(path)
        except SourceAcquisitionError:
            # Control bytes define the membership and applicability proof.
            # A failed control read cannot be represented as an empty config
            # or a partial project because that would change the authority
            # used to select the rest of the snapshot.
            if Path(path).name in SOURCE_PLAN_CONTROL_PATHS:
                raise
            if not allow_partial:
                raise
            failed_paths.add(path)
        if Path(path).name not in {"tsconfig.json", "jsconfig.json"}:
            continue
        control_value = _control_json(contents, path)
        extends_value = control_value.get("extends")
        if extends_value is None:
            continue
        if not isinstance(extends_value, str):
            raise SourceAcquisitionError(
                "CSV-NEXT-CONFIG-002", "source_control", "extends must be one local path"
            )
        project_root = next((root for root in project_roots if _under(path, root)), None)
        assert project_root is not None
        extend_path = (
            _normalise_control_path(
                f"{Path(path).parent}/{extends_value}", project_root=project_root
            )
            if extends_value.startswith(".")
            else _normalise_control_path(extends_value, project_root=project_root)
        )
        if extend_path not in enumerated_set:
            raise SourceAcquisitionError(
                "CSV-NEXT-CONFIG-002",
                "source_control",
                f"extends path was not captured: {extend_path}",
            )
        control_queue.append(extend_path)

    # Derive the membership closure using names from the frozen inventory and
    # bytes from the control phase.  No program/context file is read until
    # this closure has been computed.
    provisional_descriptors = _derive_project_descriptors_from_control_bytes(
        project_roots,
        contents,
        program_suffixes=program_suffixes,
        context_suffixes=context_suffixes,
        inventory_paths=enumerated_paths,
    )
    final_paths = tuple(
        sorted(
            set(contents).union(
                *(set(project.get("_membership", ())) for project in provisional_descriptors)
            ),
            key=_path_sort_key,
        )
    )
    assert final_paths
    for path in final_paths:
        if path not in contents:
            try:
                contents[path] = reader.read(path)
            except SourceAcquisitionError:
                if not allow_partial:
                    raise
                failed_paths.add(path)
    revision_after = reader.revision_after
    if revision_after != revision_before:
        raise SourceAcquisitionError(
            "CSV-NEXT-SOURCE-003",
            "source_integrity",
            "trusted source snapshot changed during acquisition",
        )

    # Re-evaluate the same closure against the now-retained bytes.  This is a
    # pure derivation pass; the reader is sealed only after all bytes and the
    # drift check are complete.
    project_descriptors = _derive_project_descriptors_from_control_bytes(
        project_roots,
        contents,
        program_suffixes=program_suffixes,
        context_suffixes=context_suffixes,
        inventory_paths=enumerated_paths,
    )
    assert project_descriptors
    package_applicability = derive_package_applicability_matrix(contents, project_roots)
    if package_applicability.aggregate_state == "malformed":
        raise SourceAcquisitionError(
            "CSV-NEXT-CONFIG-002",
            "source_control",
            "malformed package applicability evidence",
        )
    limits = copy.deepcopy(inventory.get("observed_limits"))
    trusted_environment_digest = inventory.get("observed_trusted_environment_digest")
    assert isinstance(limits, dict)
    assert isinstance(trusted_environment_digest, str)
    resolved_control_paths = [
        {"project_root": project["root"], "path": path}
        for project in project_descriptors
        for path in project.pop("_resolved_control_paths", ())
    ]
    resolved_control_paths.extend(
        {
            "project_root": next(root for root in project_roots if _under(path, root)),
            "path": path,
        }
        for path in selected_control_paths
        if path not in {row["path"] for row in resolved_control_paths}
    )
    local_extends = [
        edge for project in project_descriptors for edge in project.pop("_local_extends", ())
    ]
    memberships = {
        project["root"]: set(project.pop("_membership", ())) for project in project_descriptors
    }
    config = {
        "projects": project_descriptors,
        "limits": limits,
        "trusted_environment_digest": trusted_environment_digest,
    }

    projects_by_root = {project["root"]: project for project in project_descriptors}
    assert set(projects_by_root) == set(project_roots)
    control_names = {"package.json", "tsconfig.json", "jsconfig.json"}
    file_role_map: list[dict[str, Any]] = []
    for path in final_paths:
        project_root = next((root for root in project_roots if _under(path, root)), None)
        assert project_root is not None
        if path in contents and (
            (Path(path).name in control_names and path in root_control_paths)
            or path in resolved_control_paths
        ):
            roles = ["control"]
        elif path in memberships.get(project_root, set()) and path.endswith(context_suffixes):
            roles = ["context"]
        elif path in memberships.get(project_root, set()) and path.endswith(program_suffixes):
            roles = ["program"]
        else:
            continue
        file_role_map.append(
            {
                "project_root": project_root,
                "path": path,
                "roles": roles,
                "effective_role": roles[0],
            }
        )
    plan = source_plan_descriptor(
        config,
        resolved_control_paths=resolved_control_paths,
        local_extends=local_extends,
        file_role_map=file_role_map,
    )

    # Source-view entries are object rows, so their wire order is the shared
    # canonical JSON order.  Only path-only surfaces use normalized UTF-8
    # bytes directly (project roots/source roots/hard exclusions).
    view_files = sorted(
        [
            {
                "path": path,
                "size_bytes": len(contents[path]),
                "sha256": hashlib.sha256(contents[path]).hexdigest(),
            }
            for path in contents
        ],
        key=canonical_json_bytes,
    )
    graph_files = dict(contents)
    graph_files.update({path: b"" for path in failed_paths})
    # The reader may expose a fixture graph for isolated historical tests,
    # but acquisition never accepts that graph as authority.  Re-derive the
    # graph from exactly the frozen bytes and the sealed plan instead.
    source_graph = _derive_source_graph_from_frozen_bytes(graph_files, project_roots, plan)
    graph_digest = digest(source_graph)
    source_view = {
        "schema": "code-structure-viz.source-view/v1",
        "kind": "working-tree",
        "snapshot_id": reader.snapshot_id,
        "revision": revision_before,
        "head_commit": inventory.get("head_commit"),
        "inventory_paths": sorted(enumerated_paths, key=_path_sort_key),
        "source_graph_digest": graph_digest,
        "files": view_files,
        "file_count": len(view_files),
    }
    expected_files = inventory.get("file_digests")
    if expected_files is not None and not failed_paths:
        assert expected_files == view_files
    plan_digest = digest(plan)
    source_view_fingerprint = digest(source_view)
    seal_operation = reader.seal()
    seal_id = digest(
        {
            "plan_digest": plan_digest,
            "source_view_fingerprint": source_view_fingerprint,
            "seal_operation": seal_operation,
            "snapshot_id": reader.snapshot_id,
            "revision_before": revision_before,
            "revision_after": revision_after,
            "source_graph_digest": graph_digest,
        }
    )
    return SourceAcquisitionSeal(
        final_plan=plan,
        source_view=source_view,
        plan_digest=plan_digest,
        source_view_fingerprint=source_view_fingerprint,
        seal_id=seal_id,
        seal_operation=seal_operation,
        snapshot_id=reader.snapshot_id,
        revision_before=revision_before,
        revision_after=revision_after,
        source_graph=source_graph,
        captured_files={path: contents[path] for path in final_paths if path in contents},
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


def _target_non_program_reason(file_record: dict[str, Any]) -> str:
    """Classify a non-program target without losing control/context locality."""

    roles = set(file_record.get("roles", ()))
    return "control_context" if roles & {"control", "context"} else "non_program"


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
            _is_export_identifier(edge["imported_name"], allow_default=True, allow_keyword=True)
            or edge["imported_name"] == "*"
        )
        expanded = edge["expanded_exported_name"]
        assert expanded is None or _is_export_identifier(
            expanded, allow_default=True, allow_keyword=True
        )
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
            assert _is_export_identifier(item["name"], allow_default=True, allow_keyword=True)
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
            edge["imported_name"], allow_default=True, allow_keyword=True
        )
        assert edge["exported_name"] == "*" or _is_export_identifier(
            edge["exported_name"], allow_default=True, allow_keyword=True
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
                assert _is_export_identifier(item["name"], allow_default=True, allow_keyword=True)
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
            assert imported_name == "*" or _is_export_identifier(
                imported_name, allow_default=True, allow_keyword=True
            )
            exported_name = edge["exported_name"]
            assert exported_name == "*" or _is_export_identifier(
                exported_name, allow_default=True, allow_keyword=True
            )
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
                assert _is_export_identifier(
                    item_imported_name, allow_default=True, allow_keyword=True
                )
                item += 1
                exported_name = item_imported_name
                if item < close_brace and tokens[item]["value"] == "as":
                    assert item + 1 < close_brace
                    exported_name = cast(str, tokens[item + 1]["value"])
                    assert _is_export_identifier(
                        exported_name, allow_default=True, allow_keyword=True
                    )
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


def _process_launch_for_toolchain(
    toolchain: dict[str, Any],
    *,
    node_realpath: str | None,
    node_sha256: str | None,
    spawn_executable: str | None,
) -> dict[str, Any]:
    """Bind an explicitly observed executable to an observed toolchain.

    The reference fixture has no host probe, so callers must pass its
    deterministic observation explicitly.  Keeping these parameters required
    prevents this helper from becoming a hidden PATH/default fallback.
    """

    status = toolchain["node"]["status"]
    version = toolchain["node_version"] if status == "available" else None
    return process_launch_descriptor(
        node_status=status,
        node_realpath=node_realpath,
        node_sha256=node_sha256,
        node_version=version,
        spawn_executable=spawn_executable,
        file_identity_at_hash=(
            {
                "realpath": node_realpath,
                "sha256": node_sha256,
                "version": version,
            }
            if status == "available"
            else None
        ),
        file_identity_at_spawn=(
            {
                "realpath": node_realpath,
                "sha256": node_sha256,
                "version": version,
            }
            if status == "available"
            else None
        ),
        spawn_handle="fixture-process-group" if status == "available" else None,
    )


def process_launch_descriptor(
    *,
    node_status: str,
    node_realpath: str | None,
    node_sha256: str | None,
    node_version: str | None,
    spawn_executable: str | None,
    file_identity_at_hash: dict[str, Any] | None,
    file_identity_at_spawn: dict[str, Any] | None,
    spawn_handle: str | None,
) -> dict[str, Any]:
    """Return the closed executable/process-group policy for the adapter.

    The descriptor is intentionally explicit: a production runner must not
    resolve Node through ``PATH`` or inherit ambient locale, timezone, or file
    descriptors.  Unavailable Node has no executable identity but retains the
    same non-execution policy for the failure projection.
    """

    assert node_status in {"available", "unavailable", "not_applicable"}
    if node_status == "available":
        assert isinstance(node_realpath, str) and Path(node_realpath).is_absolute()
        assert isinstance(node_sha256, str) and re.fullmatch(r"[0-9a-f]{64}", node_sha256)
        assert isinstance(node_version, str) and re.fullmatch(r"\d+\.\d+\.\d+", node_version)
        assert spawn_executable == node_realpath
        assert file_identity_at_hash is not None
        assert file_identity_at_spawn is not None
        assert file_identity_at_hash == file_identity_at_spawn
        assert file_identity_at_hash == {
            "realpath": node_realpath,
            "sha256": node_sha256,
            "version": node_version,
        }
        assert isinstance(spawn_handle, str) and spawn_handle
    else:
        node_realpath = None
        node_sha256 = None
        node_version = None
        spawn_executable = None
        file_identity_at_hash = None
        file_identity_at_spawn = None
        spawn_handle = None
    argv = (
        [spawn_executable, "/.code-structure-viz/next-adapter.mjs"]
        if spawn_executable
        else [
            "<unavailable>",
            "/.code-structure-viz/next-adapter.mjs",
        ]
    )
    return {
        "schema": "code-structure-viz.next-process-launch/v1",
        "version": 1,
        "node_status": node_status,
        "node_realpath": node_realpath,
        "node_sha256": node_sha256,
        "node_version": node_version,
        "spawn_executable": spawn_executable,
        "host_os": "posix-fixture",
        "file_identity_at_hash": file_identity_at_hash,
        "file_identity_at_spawn": file_identity_at_spawn,
        "spawn_handle": spawn_handle,
        "spawn_path": spawn_executable,
        "symlink_policy": "resolve_and_verify_realpath",
        "argv": argv,
        "toctou_policy": "bind_verified_realpath_at_spawn",
        "shell": False,
        "cwd": "/.code-structure-viz/private-run",
        "env_allowlist": {"LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC"},
        "denied_env": ["NODE_OPTIONS", "NODE_PATH", "PATH", "npm_config_user_config"],
        "stdio": {"stdin": "pipe", "stdout": "pipe", "stderr": "pipe"},
        "fd_inheritance": {"close_fds": True, "allowed": [0, 1, 2]},
        "process_group": {"create": True, "terminate_scope": "group", "wait_after_terminate": True},
    }


def validate_process_launch_descriptor(value: dict[str, Any]) -> None:
    """Validate launch determinism/security without touching the host process."""

    assert set(value) == {
        "schema",
        "version",
        "node_status",
        "node_realpath",
        "node_sha256",
        "node_version",
        "spawn_executable",
        "host_os",
        "file_identity_at_hash",
        "file_identity_at_spawn",
        "spawn_handle",
        "spawn_path",
        "symlink_policy",
        "argv",
        "toctou_policy",
        "shell",
        "cwd",
        "env_allowlist",
        "denied_env",
        "stdio",
        "fd_inheritance",
        "process_group",
    }
    assert value["schema"] == "code-structure-viz.next-process-launch/v1"
    assert value["version"] == 1
    assert value["node_status"] in {"available", "unavailable", "not_applicable"}
    assert value["host_os"] == "posix-fixture"
    if value["node_status"] == "available":
        assert isinstance(value["node_realpath"], str)
        assert Path(value["node_realpath"]).is_absolute()
        assert isinstance(value["node_sha256"], str)
        assert re.fullmatch(r"[0-9a-f]{64}", value["node_sha256"])
        assert isinstance(value["node_version"], str)
        assert re.fullmatch(r"\d+\.\d+\.\d+", value["node_version"])
        assert value["spawn_executable"] == value["node_realpath"]
        assert value["argv"][0] == value["spawn_executable"]
        assert value["spawn_path"] == value["spawn_executable"]
        assert value["file_identity_at_hash"] == {
            "realpath": value["node_realpath"],
            "sha256": value["node_sha256"],
            "version": value["node_version"],
        }
        assert value["file_identity_at_spawn"] == value["file_identity_at_hash"]
        assert isinstance(value["spawn_handle"], str) and value["spawn_handle"]
    else:
        assert (
            value["node_realpath"] is None
            and value["node_sha256"] is None
            and value["node_version"] is None
            and value["spawn_executable"] is None
            and value["file_identity_at_hash"] is None
            and value["file_identity_at_spawn"] is None
            and value["spawn_handle"] is None
            and value["spawn_path"] is None
        )
    assert value["symlink_policy"] == "resolve_and_verify_realpath"
    assert value["toctou_policy"] == "bind_verified_realpath_at_spawn"
    assert value["argv"][1:] == ["/.code-structure-viz/next-adapter.mjs"]
    if value["node_status"] != "available":
        assert value["argv"][0] == "<unavailable>"
    assert value["shell"] is False
    assert Path(value["cwd"]).is_absolute()
    assert value["env_allowlist"] == {
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "TZ": "UTC",
    }
    assert value["denied_env"] == sorted(set(value["denied_env"]))
    assert {"PATH", "NODE_OPTIONS", "NODE_PATH"} <= set(value["denied_env"])
    assert value["stdio"] == {"stdin": "pipe", "stdout": "pipe", "stderr": "pipe"}
    assert value["fd_inheritance"] == {"close_fds": True, "allowed": [0, 1, 2]}
    assert value["process_group"] == {
        "create": True,
        "terminate_scope": "group",
        "wait_after_terminate": True,
    }


def validate_process_launch_observation(value: dict[str, Any]) -> None:
    """Validate the fixture/production observation union without host access."""

    schema_path = REPO_ROOT / "schemas" / "next-process-launch-observation-v1.schema.json"
    schema = cast(dict[str, Any], json.loads(schema_path.read_text(encoding="utf-8")))
    try:
        Draft202012Validator(schema).validate(value)
    except ValidationError as exc:
        raise AssertionError("invalid process launch observation") from exc
    if value["kind"] == "production" and value["node_status"] == "available":
        assert value["file_identity_at_hash"] == value["file_identity_at_spawn"]
        identity = value["file_identity_at_hash"]
        assert value["node_realpath"] == identity["realpath"]
        assert value["node_sha256"] == identity["sha256"]
        assert value["post_spawn_identity_check"]["identity_at_spawn"] == identity
        expected_primitive = f"{value['host_os']}-posix-spawn-verified-fd"
        assert value["spawn_primitive"] == expected_primitive
        assert value["toctou_failure_point"] == "none"


def process_launch_observation_from_descriptor(
    descriptor: dict[str, Any] | None,
) -> dict[str, Any]:
    """Project one legacy descriptor into the canonical launch observation.

    The descriptor is accepted only as a compatibility input for existing
    reference fixtures.  A request-independent branch uses an explicit
    production ``unknown`` observation with null identity fields; it never
    fabricates a path, hash, version, handle, or spawn primitive.
    """

    if descriptor is None:
        return {
            "schema": "code-structure-viz.next-process-launch-observation/v1",
            "version": 1,
            "kind": "production",
            "host_os": "unknown",
            "node_status": "unavailable",
            "argv": ["<unavailable>", "/.code-structure-viz/next-adapter.mjs"],
            "shell": False,
            "process_group": {
                "create": True,
                "terminate_scope": "group",
                "wait_after_terminate": True,
            },
            "node_realpath": None,
            "node_sha256": None,
            "node_version": None,
            "file_identity_at_hash": None,
            "file_identity_at_spawn": None,
            "verified_open_handle": None,
            "spawn_primitive": None,
            "post_spawn_identity_check": None,
            "fd_lifecycle": None,
            "toctou_failure_point": "node-discovery",
        }
    validate_process_launch_descriptor(descriptor)
    status = descriptor["node_status"]
    if status == "available":
        return {
            "schema": "code-structure-viz.next-process-launch-observation/v1",
            "version": 1,
            "kind": "fixture",
            "host_os": "fixture",
            "node_status": "available",
            "fixture_id": "reference-process-v1",
            "identity_token": descriptor["node_sha256"],
            "spawn_primitive": "recorded-fixture",
            "toctou_failure_point": "not-exercised",
            "argv": descriptor["argv"],
            "shell": False,
            "process_group": descriptor["process_group"],
        }
    return {
        "schema": "code-structure-viz.next-process-launch-observation/v1",
        "version": 1,
        "kind": "fixture",
        "host_os": "fixture",
        "node_status": status,
        "fixture_id": "reference-process-v1",
        "identity_token": "unavailable",
        "spawn_primitive": "recorded-fixture",
        "toctou_failure_point": "fixture-rejection",
        "argv": descriptor["argv"],
        "shell": False,
        "process_group": descriptor["process_group"],
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


def _public_request_snapshot(
    request: ValidatedAdapterRequest,
    *,
    public_config: dict[str, Any] | None = None,
    source_plan: dict[str, Any] | None = None,
    source_plan_digest: str | None = None,
    domain_config_digest: str | None = None,
    run_fingerprint: str | None = None,
) -> dict[str, Any]:
    """Project a private request into the public snapshot-request contract.

    The adapter request contains request identity, protocol, trusted profile,
    file bytes, and run context.  Those private fields are deliberately not
    copied into the public request.  The public snapshot is instead built
    from the sealed config and source plan; callers cannot smuggle an adapter
    payload into a manifest by reusing the private dictionary.
    """

    config = public_config or {}
    projects = copy.deepcopy(
        config.get(
            "projects",
            [
                {
                    key: copy.deepcopy(project[key])
                    for key in ("root", "source_roots", "config_path", "compiler_options")
                }
                for project in request["projects"]
            ],
        )
    )
    snapshot: dict[str, Any] = {
        "schema": "code-structure-viz.next-snapshot-request/v1",
        "projects": projects,
        "targets": copy.deepcopy(config.get("targets", request["targets"])),
        "upstream_depth": config.get("upstream_depth", 1),
        "downstream_depth": config.get("downstream_depth", 1),
        "formats": copy.deepcopy(
            config.get("formats", request["run_context"]["requested_formats"])
        ),
        "limits": copy.deepcopy(config.get("limits", request["limits"])),
        "trusted_environment_digest": config.get(
            "trusted_environment_digest", request["trusted_type_environment"]["sha256"]
        ),
        "source_plan": copy.deepcopy(
            source_plan if source_plan is not None else config.get("source_plan", {})
        ),
        "source_plan_digest": source_plan_digest or config.get("source_plan_digest", "0" * 64),
        "domain_config_digest": domain_config_digest
        or config.get("domain_config_digest", "0" * 64),
    }
    if run_fingerprint is not None:
        snapshot["run_fingerprint"] = run_fingerprint
    return snapshot


_TRUSTED_SOURCE_SEALS: dict[str, SourceAcquisitionSeal] = {}


def _validate_request_matches_source_seal(
    request: ValidatedAdapterRequest, source_seal: SourceAcquisitionSeal
) -> None:
    """Bind a validated request to the seal observed before request creation."""

    plan_projects = [
        {
            key: copy.deepcopy(project[key])
            for key in ("root", "source_roots", "config_path", "compiler_options")
        }
        for project in source_seal.final_plan["projects"]
    ]
    request_projects = [
        {
            key: copy.deepcopy(project[key])
            for key in ("root", "source_roots", "config_path", "compiler_options")
        }
        for project in request["projects"]
    ]
    assert request_projects == plan_projects
    captured = source_seal.captured_files
    request_files = {record["path"]: record for record in request["files"]}
    assert set(request_files) == set(captured)
    sealed_rows = {row["path"]: row for row in source_seal.source_view["files"]}
    assert set(sealed_rows) == set(captured)
    for path, record in request_files.items():
        payload = base64.b64decode(record["content_base64"], validate=True)
        assert payload == captured[path]
        assert record["size_bytes"] == len(payload)
        assert record["sha256"] == hashlib.sha256(payload).hexdigest()
        assert sealed_rows[path]["size_bytes"] == len(payload)
        assert sealed_rows[path]["sha256"] == record["sha256"]


def register_source_acquisition_seal(
    request: dict[str, Any] | ValidatedAdapterRequest, source_seal: SourceAcquisitionSeal
) -> None:
    """Register a trusted pre-request seal for a data-only fixture boundary."""

    validated = validate_adapter_request(request)
    _validate_request_matches_source_seal(validated, source_seal)
    _TRUSTED_SOURCE_SEALS[digest(validated.snapshot())] = copy.deepcopy(source_seal)


def _trusted_fixture_source_seal(
    request: ValidatedAdapterRequest,
    source_seal: SourceAcquisitionSeal | None,
) -> SourceAcquisitionSeal:
    """Resolve a pre-registered reference fixture seal, never derive one.

    This helper exists only for the data-only test fixture registry.  The
    production-shaped context builder below requires the explicit seal that
    was observed before the request was formed; it never rebuilds a seal from
    request files or request metadata.
    """

    resolved = source_seal or _TRUSTED_SOURCE_SEALS.get(digest(request.snapshot()))
    assert resolved is not None, "a trusted source seal must precede adapter request validation"
    _validate_request_matches_source_seal(request, resolved)
    return copy.deepcopy(resolved)


def _seal_publication_context(
    *,
    source_seal: SourceAcquisitionSeal | None,
    run_context: NextRunContext,
    public_request: ValidatedAdapterRequest | None,
    public_config: dict[str, Any],
    compatibility_descriptor: dict[str, Any] | None,
    toolchain: dict[str, Any] | None,
    trusted_environment: dict[str, Any] | None,
    semantic_projects: list[dict[str, Any]],
    semantic_files: list[dict[str, Any]],
    fingerprint_projects: list[dict[str, Any]],
    source_failure_ledger: SourceFailureLedger | tuple[dict[str, Any], ...],
    process_launch: dict[str, Any] | None,
    observation_provenance: dict[str, Any],
) -> NextPublicationContext:
    """Seal the sole immutable publication provenance object.

    Every argument is resolved before this function is called.  In
    particular, this function has no request/default/fixture fallback and no
    filesystem reads; all downstream surfaces consume this sealed object.
    """

    context = canonical_run_context(**run_context)
    ledger_object = (
        source_failure_ledger if isinstance(source_failure_ledger, SourceFailureLedger) else None
    )
    ledger_rows = tuple(
        copy.deepcopy(ledger_object.failures)
        if ledger_object is not None
        else copy.deepcopy(source_failure_ledger)
    )
    ledger_digest = ledger_object.ledger_digest if ledger_object is not None else None
    ledger_evidence = (
        {
            "source_seal_id": ledger_object.source_seal.seal_id,
            "source_seal_digest": digest(
                {
                    "seal_id": ledger_object.source_seal.seal_id,
                    "plan_digest": ledger_object.source_seal.plan_digest,
                    "source_view_fingerprint": ledger_object.source_seal.source_view_fingerprint,
                    "source_graph": ledger_object.source_seal.source_graph,
                }
            ),
            "source_graph": ledger_object.source_graph,
            "failures": list(ledger_object.failures),
            "targets": list(ledger_object.targets),
            "proof_roots": list(ledger_object.proof_roots),
            "ledger_digest": ledger_object.ledger_digest,
        }
        if ledger_object is not None
        else None
    )
    config = copy.deepcopy(public_config)
    config.setdefault("request_independent", source_seal is None)
    assert config["request_independent"] is (source_seal is None)
    if source_seal is not None:
        config["source_plan"] = copy.deepcopy(source_seal.final_plan)
        config["source_plan_digest"] = source_seal.plan_digest
    else:
        assert config.get("source_plan") is None
        assert config.get("source_plan_digest") is None
    if config.get("limits") is not None:
        config["limits"] = copy.deepcopy(config["limits"])
    config["domain_config_digest"] = digest(
        {key: value for key, value in config.items() if key != "domain_config_digest"}
    )
    request_snapshot = None
    resolved_toolchain = copy.deepcopy(toolchain)
    resolved_trusted_environment = copy.deepcopy(trusted_environment)
    launch = copy.deepcopy(process_launch)
    if launch is not None:
        validate_process_launch_descriptor(launch)
    preimage = {
        "source_view_fingerprint": source_seal.source_view_fingerprint if source_seal else None,
        "source_plan_digest": source_seal.plan_digest if source_seal else None,
        "domain_config_digest": config["domain_config_digest"],
        "projects": copy.deepcopy(fingerprint_projects),
        "targets": copy.deepcopy(config["targets"]),
        "formats": list(context["requested_formats"]),
        "stdout_selector": context["stdout_selector"],
        "limits": copy.deepcopy(config.get("limits")),
        "trusted_environment_digest": (
            resolved_trusted_environment["sha256"]
            if resolved_trusted_environment is not None
            else None
        ),
        "node_version": resolved_toolchain["node_version"] if resolved_toolchain else None,
        "typescript_version": (
            resolved_toolchain["typescript_version"] if resolved_toolchain else None
        ),
        "adapter_version": resolved_toolchain["adapter_version"] if resolved_toolchain else None,
        "protocol": resolved_toolchain["protocol"] if resolved_toolchain else None,
        "process_launch_descriptor_digest": digest(launch) if launch is not None else None,
        "source_failure_ledger": copy.deepcopy(list(ledger_rows)),
        "identifier_unicode_version": ECMASCRIPT_IDENTIFIER_UNICODE_VERSION,
        "identifier_unicode_table_digest": ECMASCRIPT_IDENTIFIER_UNICODE_TABLE_DIGEST,
    }
    if ledger_digest is not None:
        preimage["source_failure_ledger_digest"] = ledger_digest
    if public_request is not None:
        request_snapshot = _public_request_snapshot(
            public_request,
            public_config=config,
            source_plan=source_seal.final_plan if source_seal else None,
            source_plan_digest=source_seal.plan_digest if source_seal else None,
            domain_config_digest=config["domain_config_digest"],
            run_fingerprint=digest(preimage),
        )
    return NextPublicationContext(
        source_view_descriptor=copy.deepcopy(source_seal.source_view) if source_seal else None,
        source_view_fingerprint=source_seal.source_view_fingerprint if source_seal else None,
        final_source_acquisition_plan=(
            copy.deepcopy(source_seal.final_plan) if source_seal else None
        ),
        source_plan_digest=source_seal.plan_digest if source_seal else None,
        seal_id=source_seal.seal_id if source_seal else None,
        source_acquisition_seal=copy.deepcopy(source_seal) if source_seal else None,
        public_next_config=config,
        public_next_request=request_snapshot,
        compatibility_descriptor=copy.deepcopy(compatibility_descriptor),
        toolchain=resolved_toolchain,
        trusted_environment=resolved_trusted_environment,
        semantic_projects=copy.deepcopy(semantic_projects),
        semantic_files=copy.deepcopy(semantic_files),
        run_context=context,
        run_fingerprint_preimage=preimage,
        source_failure_ledger=ledger_rows,
        source_failure_ledger_seal=copy.deepcopy(ledger_object),
        process_launch_descriptor=launch,
        source_failure_ledger_digest=ledger_digest,
        source_failure_ledger_evidence=ledger_evidence,
        observation_provenance=copy.deepcopy(observation_provenance),
    )


def _publication_context_for_validated_request(
    request: ValidatedAdapterRequest,
    run_context: NextRunContext,
    *,
    source_seal: SourceAcquisitionSeal,
    toolchain: dict[str, Any],
    trusted_environment: dict[str, Any],
    projects_for_fingerprint: list[dict[str, Any]] | None = None,
    source_failure_ledger: SourceFailureLedger | tuple[dict[str, Any], ...],
    process_launch_descriptor: dict[str, Any],
) -> NextPublicationContext:
    """Resolve observations into one context and one source-acquisition seal.

    The launch descriptor is required because executable identity is observed
    at the spawn boundary.  This helper must never reconstruct it from a
    toolchain version or a global fixture.
    """

    assert isinstance(source_seal, SourceAcquisitionSeal)
    _validate_request_matches_source_seal(request, source_seal)
    project_descriptors = [
        {
            key: copy.deepcopy(project[key])
            for key in ("root", "source_roots", "config_path", "compiler_options")
        }
        for project in request["projects"]
    ]
    config = {
        "schema": "code-structure-viz.domain-config/next/v1",
        "projects": project_descriptors,
        "targets": list(request["targets"]),
        "upstream_depth": 1,
        "downstream_depth": 1,
        "formats": list(run_context["requested_formats"]),
        "limits": copy.deepcopy(request["limits"]),
        "source_plan": copy.deepcopy(source_seal.final_plan),
        "source_plan_digest": source_seal.plan_digest,
        "trusted_environment_digest": request["trusted_type_environment"]["sha256"],
    }
    return _seal_publication_context(
        source_seal=source_seal,
        run_context=run_context,
        public_request=request,
        public_config=config,
        compatibility_descriptor=_compatibility_descriptor_snapshot(),
        toolchain=toolchain,
        trusted_environment=trusted_environment,
        semantic_projects=copy.deepcopy(request["projects"]),
        semantic_files=[
            {key: copy.deepcopy(file_record[key]) for key in file_record if key != "content_base64"}
            for file_record in request["files"]
        ],
        fingerprint_projects=copy.deepcopy(
            projects_for_fingerprint
            if projects_for_fingerprint is not None
            else request["projects"]
        ),
        source_failure_ledger=source_failure_ledger,
        process_launch=copy.deepcopy(process_launch_descriptor),
        observation_provenance=_publication_provenance(kind="request_bound", budget_observed=True),
    )


def _publication_context_for_request_independent_failure(
    *,
    run_context: NextRunContext,
    decision_context: NextDecisionContext,
    stage: str,
    diagnostic_code: str,
    source_failure_ledger: SourceFailureLedger | tuple[dict[str, Any], ...],
) -> NextPublicationContext:
    """Seal only facts observed before a request-independent failure.

    The absence of an adapter request also means that limits, trusted
    environment, toolchain, and source plan are not observed by this branch.
    They remain explicit ``null`` values instead of being reconstructed from
    defaults or an unavailable fixture.
    """

    config = {
        "schema": "code-structure-viz.domain-config/next/v1",
        "request_independent": True,
        "projects": [],
        "targets": list(decision_context.targets),
        "upstream_depth": None,
        "downstream_depth": None,
        "formats": list(run_context["requested_formats"]),
        "limits": None,
        "source_plan": None,
        "source_plan_digest": None,
        "trusted_environment_digest": None,
        "failure_stage": stage,
        "failure_code": diagnostic_code,
    }
    return _seal_publication_context(
        source_seal=None,
        run_context=run_context,
        public_request=None,
        public_config=config,
        compatibility_descriptor=None,
        toolchain=None,
        trusted_environment=None,
        semantic_projects=[],
        semantic_files=[],
        fingerprint_projects=[],
        source_failure_ledger=source_failure_ledger,
        process_launch=None,
        observation_provenance=_publication_provenance(
            kind="request_independent",
            failure_stage=stage,
            failure_code=diagnostic_code,
            budget_observed=run_context["budget_source"] != "unobserved",
        ),
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
        key=lambda project: _path_sort_key(project["root"]),
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
        "hard_exclusions": sorted(SOURCE_PLAN_HARD_EXCLUSIONS, key=_path_sort_key),
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
        assert project["source_roots"] == sorted(set(project["source_roots"]), key=_path_sort_key)
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
        assert local_extend["extends"] == sorted(set(local_extend["extends"]), key=_path_sort_key)
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
    assert descriptor["hard_exclusions"] == sorted(SOURCE_PLAN_HARD_EXCLUSIONS, key=_path_sort_key)
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
        max_model_records=LIMIT_DEFAULTS["max_total_array_items"],
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
    assert request_roots == sorted(request_roots, key=_path_sort_key)
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
        project_roots = [
            source_root
            for project in model.get("projects", [])
            for source_root in project.get("source_roots", [])
        ]
        if not matching_files:
            reason = (
                "out_of_scope"
                if project_roots and not any(_under(requested_path, root) for root in project_roots)
                else "missing"
            )
        elif len(exact_files) > 1:
            reason = "duplicate"
        elif len(project_ids) != 1:
            reason = "project_ambiguity"
        elif exact_files and not _is_program_file(exact_files[0]):
            reason = _target_non_program_reason(exact_files[0])
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


def target_failure_from_proof(
    proof: dict[str, Any],
) -> NextTargetCompletenessFailure | None:
    """Promote proof-derived unavailable IDs to the typed target outcome."""

    failures = [
        {
            "target_key": canonical_target_key(row["target_key"]),
            "reason": row["reason"],
        }
        for row in proof.get("target_resolutions", [])
        if row.get("status") == "failed"
    ]
    if not failures:
        return None
    assert failures == sorted(failures, key=canonical_json_bytes)
    assert len({row["target_key"] for row in failures}) == len(failures)
    assert all(row["reason"] in TARGET_FAILURE_REASONS for row in failures)
    return NextTargetCompletenessFailure(failures)


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


def classify_source_failure(ledger: SourceFailureLedger) -> dict[str, Any]:
    """Close the source boundary from the sealed graph, never caller flags.

    ``SourceFailureLedger`` recomputes locality from its raw sealed graph.  A
    caller cannot select ``SOURCE-001`` by passing a pair of booleans; the
    only owner of that decision is this graph-derived ledger.
    """

    assert isinstance(ledger, SourceFailureLedger)
    if ledger.safe_subset_proven:
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


@dataclass(frozen=True)
class SourceFailureLedger:
    """Python-owned locality ledger derived only from one source seal.

    ``from_seal`` is the only construction path.  The graph, project roots,
    and seal identity are owned by ``SourceAcquisitionSeal``; a caller may
    submit observations (failures, requested targets, and proof roots) but may
    not replace the graph or assert a reachability boolean.
    """

    source_seal: SourceAcquisitionSeal
    failures: tuple[dict[str, Any], ...]
    targets: tuple[str, ...]
    proof_roots: tuple[dict[str, Any], ...]
    ledger_digest: str = field(init=False)

    @classmethod
    def from_seal(
        cls,
        source_seal: SourceAcquisitionSeal,
        failures: tuple[dict[str, Any], ...] | list[dict[str, Any]],
        targets: tuple[str, ...] | list[str],
        proof_roots: tuple[dict[str, Any], ...] | list[dict[str, Any]],
    ) -> SourceFailureLedger:
        assert isinstance(source_seal, SourceAcquisitionSeal)
        return cls(
            source_seal=source_seal,
            failures=tuple(failures),
            targets=tuple(targets),
            proof_roots=tuple(proof_roots),
        )

    def __post_init__(self) -> None:
        assert isinstance(self.source_seal, SourceAcquisitionSeal)
        failures = tuple(copy.deepcopy(self.failures))
        graph = copy.deepcopy(self.source_seal.source_graph)
        roots = tuple(project["root"] for project in self.source_seal.final_plan["projects"])
        targets = tuple(canonical_target_key(item) for item in self.targets)
        proof_roots = tuple(copy.deepcopy(self.proof_roots))
        assert failures == tuple(sorted(failures, key=canonical_json_bytes))
        assert set(graph) == {"nodes", "edges", "open_edges"}
        expected_seal_id = digest(
            {
                "plan_digest": self.source_seal.plan_digest,
                "source_view_fingerprint": self.source_seal.source_view_fingerprint,
                "seal_operation": self.source_seal.seal_operation,
                "snapshot_id": self.source_seal.snapshot_id,
                "revision_before": self.source_seal.revision_before,
                "revision_after": self.source_seal.revision_after,
                "source_graph_digest": digest(graph),
            }
        )
        assert self.source_seal.seal_id == expected_seal_id
        nodes = tuple(copy.deepcopy(graph["nodes"]))
        edges = tuple(copy.deepcopy(graph["edges"]))
        open_edges = tuple(copy.deepcopy(graph["open_edges"]))
        assert nodes == tuple(sorted(nodes, key=canonical_json_bytes))
        assert edges == tuple(sorted(edges, key=canonical_json_bytes))
        assert open_edges == tuple(sorted(open_edges, key=canonical_json_bytes))
        graph = {"nodes": nodes, "edges": edges, "open_edges": open_edges}
        assert roots == tuple(sorted(roots, key=_path_sort_key))
        assert targets == tuple(sorted(set(targets)))
        assert proof_roots == tuple(sorted(proof_roots, key=canonical_json_bytes))
        assert roots and len(roots) == len(set(roots))
        assert proof_roots
        proof_root_ids = {root.get("id") for root in proof_roots}
        assert all(isinstance(root_id, str) and root_id for root_id in proof_root_ids)
        node_by_id: dict[str, dict[str, Any]] = {}
        node_id_by_path: dict[str, str] = {}
        for row in nodes:
            assert set(row) == {"id", "path", "project_root"}
            assert isinstance(row["id"], str) and row["id"]
            _assert_file_path(row["path"])
            _assert_path(row["project_root"])
            assert row["project_root"] in roots
            assert row["id"] not in node_by_id
            assert row["path"] not in node_id_by_path
            node_by_id[row["id"]] = row
            node_id_by_path[row["path"]] = row["id"]
        adjacency: dict[str, tuple[str, ...]] = {node_id: () for node_id in node_by_id}
        mutable_adjacency: dict[str, list[str]] = {node_id: [] for node_id in node_by_id}
        for edge in edges:
            assert set(edge) == {"source", "target"}
            assert edge["source"] in node_by_id and edge["target"] in node_by_id
            mutable_adjacency[edge["source"]].append(edge["target"])
        open_adjacency: dict[str, int] = {node_id: 0 for node_id in node_by_id}
        for edge in open_edges:
            assert set(edge) == {"source"}
            assert edge["source"] in node_by_id
            open_adjacency[edge["source"]] += 1
        adjacency = {
            node_id: tuple(sorted(set(children), key=lambda item: item))
            for node_id, children in mutable_adjacency.items()
        }
        normalized: list[dict[str, Any]] = []
        paths: set[str] = set()
        for failure in failures:
            assert set(failure) == {"path", "stage"}
            _assert_file_path(failure["path"])
            assert isinstance(failure["stage"], str) and failure["stage"]
            assert failure["path"] not in paths
            paths.add(failure["path"])
            start = node_id_by_path.get(failure["path"])
            assert start is not None
            reached: set[str] = set()
            frontier = [start]
            while frontier:
                current = frontier.pop()
                if current in reached:
                    continue
                reached.add(current)
                frontier.extend(adjacency[current])
            reached_keys = {node_id for node_id in reached}
            reached_paths = {node_by_id[node_id]["path"] for node_id in reached}
            target_tainted = any(
                target in reached_keys
                or (target.startswith("path:") and target.removeprefix("path:") in reached_paths)
                for target in targets
            )
            target_tainted = target_tainted or any(
                node_id in reached for node_id, count in open_adjacency.items() if count
            )
            isolated = not target_tainted
            normalized.append(
                {
                    "path": failure["path"],
                    "stage": failure["stage"],
                    "isolated": isolated,
                    "target_tainted": target_tainted,
                }
            )
        normalized_tuple = tuple(sorted(normalized, key=canonical_json_bytes))
        object.__setattr__(self, "failures", normalized_tuple)
        object.__setattr__(self, "targets", targets)
        object.__setattr__(self, "proof_roots", proof_roots)
        source_seal_digest = digest(
            {
                "seal_id": self.source_seal.seal_id,
                "plan_digest": self.source_seal.plan_digest,
                "source_view_fingerprint": self.source_seal.source_view_fingerprint,
                "source_graph": graph,
            }
        )
        expected_ledger_digest = digest(
            {
                "source_seal_digest": source_seal_digest,
                "source_seal_id": self.source_seal.seal_id,
                "failures": list(normalized_tuple),
                "targets": list(targets),
                "proof_roots": list(proof_roots),
            }
        )
        object.__setattr__(self, "ledger_digest", expected_ledger_digest)

    @property
    def source_graph(self) -> dict[str, Any]:
        return self.source_seal.source_graph

    @property
    def project_roots(self) -> tuple[str, ...]:
        return tuple(project["root"] for project in self.source_seal.final_plan["projects"])

    @property
    def seal_id(self) -> str:
        return self.source_seal.seal_id

    @property
    def seal_digest(self) -> str:
        """Compatibility name for the ledger digest, never caller input."""

        return self.ledger_digest

    @property
    def safe_file_set(self) -> tuple[str, ...]:
        failed_paths = {failure["path"] for failure in self.failures}
        return tuple(
            row["path"]
            for row in self.source_seal.source_view["files"]
            if row["path"] not in failed_paths
        )

    @property
    def safe_subset_proven(self) -> bool:
        return bool(self.failures) and all(
            item["isolated"] and not item["target_tainted"] for item in self.failures
        )

    @property
    def explicit_target_tainted(self) -> bool:
        return any(item["target_tainted"] for item in self.failures)

    def __getattribute__(self, name: str) -> Any:
        value = object.__getattribute__(self, name)
        if name in {
            "source_seal",
            "failures",
            "source_graph",
            "project_roots",
            "targets",
            "proof_roots",
        }:
            return copy.deepcopy(value)
        return value


@dataclass(frozen=True, kw_only=True)
class CompleteSourceSeal:
    """Closed acquisition result when every planned file was captured."""

    seal: SourceAcquisitionSeal

    def __post_init__(self) -> None:
        assert isinstance(self.seal, SourceAcquisitionSeal)

    def __getattribute__(self, name: str) -> Any:
        value = object.__getattribute__(self, name)
        return copy.deepcopy(value) if name == "seal" else value


@dataclass(frozen=True, kw_only=True)
class PartialSourceSeal:
    """Closed acquisition result with a graph-proven safe file subset."""

    seal: SourceAcquisitionSeal
    ledger: SourceFailureLedger
    safe_file_set: tuple[str, ...]

    def __post_init__(self) -> None:
        assert isinstance(self.seal, SourceAcquisitionSeal)
        assert isinstance(self.ledger, SourceFailureLedger)
        assert self.ledger.source_seal.seal_id == self.seal.seal_id
        safe_files = tuple(self.safe_file_set)
        assert safe_files == tuple(sorted(safe_files, key=_path_sort_key))
        assert len(safe_files) == len(set(safe_files))
        assert safe_files == self.ledger.safe_file_set
        assert set(safe_files) == set(self.seal.captured_files)
        assert self.ledger.safe_subset_proven
        object.__setattr__(self, "safe_file_set", safe_files)

    def __getattribute__(self, name: str) -> Any:
        value = object.__getattribute__(self, name)
        return copy.deepcopy(value) if name in {"seal", "ledger", "safe_file_set"} else value


@dataclass(frozen=True, kw_only=True)
class SourceAcquisitionUnavailable:
    """Closed result for a source failure whose payload cannot be isolated."""

    diagnostic_code: str
    stage: str

    def __post_init__(self) -> None:
        assert self.diagnostic_code == "CSV-NEXT-SOURCE-003"
        assert self.stage in {"source_control", "source_selection", "source_read"}


@dataclass(frozen=True, kw_only=True)
class SourceIntegrityFatal:
    """Closed fail-closed result for a snapshot integrity violation."""

    diagnostic_code: str
    stage: str

    def __post_init__(self) -> None:
        assert self.diagnostic_code == "CSV-NEXT-SOURCE-003"
        assert self.stage == "source_integrity"


SourceAcquisitionResult = (
    CompleteSourceSeal | PartialSourceSeal | SourceAcquisitionUnavailable | SourceIntegrityFatal
)


@dataclass(frozen=True, kw_only=True)
class SourceAcquisitionDecisionProjection:
    """Closed semantic projection of the source-acquisition result union."""

    result_kind: str
    outcome: str
    payload_available: bool
    diagnostic_code: str | None
    stage: str | None
    exit_code: int
    manifest_available: bool
    stdout_reason: str

    def __post_init__(self) -> None:
        assert self.result_kind in {
            "complete",
            "partial_safe",
            "payload_unavailable",
            "source_integrity_fatal",
        }
        assert self.outcome in {"complete", "partial_safe", "payload_unavailable", "fatal"}
        assert self.diagnostic_code is None or self.diagnostic_code.startswith("CSV-NEXT-")
        if self.result_kind == "complete":
            assert self.outcome == "complete"
            assert self.payload_available and self.diagnostic_code is None
            assert self.stage is None and self.exit_code == 0
            assert self.manifest_available and self.stdout_reason == "complete"
        elif self.result_kind == "partial_safe":
            assert self.outcome == "partial_safe"
            assert self.payload_available
            assert self.diagnostic_code == "CSV-NEXT-SOURCE-001"
            assert self.stage == "source_read" and self.exit_code == 3
            assert self.manifest_available and self.stdout_reason == "partial_safe"
        elif self.result_kind == "payload_unavailable":
            assert self.outcome == "payload_unavailable"
            assert not self.payload_available
            assert self.diagnostic_code == "CSV-NEXT-SOURCE-003"
            assert self.stage in {"source_control", "source_selection", "source_read"}
            assert self.exit_code == 3
            assert self.manifest_available and self.stdout_reason == "domain_payload_unavailable"
        else:
            assert self.outcome == "fatal"
            assert not self.payload_available
            assert self.diagnostic_code == "CSV-NEXT-SOURCE-003"
            assert self.stage == "source_integrity" and self.exit_code == 1
            assert not self.manifest_available and self.stdout_reason == "run_fatal"

    def as_dict(self) -> dict[str, Any]:
        return {
            "result_kind": self.result_kind,
            "outcome": self.outcome,
            "payload_available": self.payload_available,
            "diagnostic_code": self.diagnostic_code,
            "stage": self.stage,
            "exit_code": self.exit_code,
            "manifest_available": self.manifest_available,
            "stdout_reason": self.stdout_reason,
        }


def source_acquisition_result_decision(
    result: SourceAcquisitionResult,
) -> SourceAcquisitionDecisionProjection:
    """Project the union once, before any manifest/stdout writer is invoked."""

    if isinstance(result, CompleteSourceSeal):
        return SourceAcquisitionDecisionProjection(
            result_kind="complete",
            outcome="complete",
            payload_available=True,
            diagnostic_code=None,
            stage=None,
            exit_code=0,
            manifest_available=True,
            stdout_reason="complete",
        )
    if isinstance(result, PartialSourceSeal):
        return SourceAcquisitionDecisionProjection(
            result_kind="partial_safe",
            outcome="partial_safe",
            payload_available=True,
            diagnostic_code="CSV-NEXT-SOURCE-001",
            stage="source_read",
            exit_code=3,
            manifest_available=True,
            stdout_reason="partial_safe",
        )
    if isinstance(result, SourceIntegrityFatal):
        return SourceAcquisitionDecisionProjection(
            result_kind="source_integrity_fatal",
            outcome="fatal",
            payload_available=False,
            diagnostic_code=result.diagnostic_code,
            stage=result.stage,
            exit_code=1,
            manifest_available=False,
            stdout_reason="run_fatal",
        )
    assert isinstance(result, SourceAcquisitionUnavailable)
    return SourceAcquisitionDecisionProjection(
        result_kind="payload_unavailable",
        outcome="payload_unavailable",
        payload_available=False,
        diagnostic_code=result.diagnostic_code,
        stage=result.stage,
        exit_code=3,
        manifest_available=True,
        stdout_reason="domain_payload_unavailable",
    )


def seal_source_acquisition_result(
    intent: SourceDiscoveryIntent | dict[str, Any],
    reader: InstrumentedSourceReader,
    inventory: dict[str, Any] | None = None,
    *,
    targets: tuple[str, ...] | list[str] = (),
    proof_roots: tuple[dict[str, Any], ...] | list[dict[str, Any]] = (),
) -> SourceAcquisitionResult:
    """Return the closed source-acquisition union without aborting on one read.

    The reader performs each read at most once.  A failed program/context read
    is retained as a graph root, while the successful bytes are sealed and
    classified by the ledger.  Control, malformed, and revision failures are
    typed unavailable/fatal results instead of being silently converted into a
    partial request.
    """

    try:
        seal = seal_source_acquisition(intent, reader, inventory, allow_partial=True)
    except SourceAcquisitionError as failure:
        if failure.stage == "source_integrity":
            return SourceIntegrityFatal(diagnostic_code="CSV-NEXT-SOURCE-003", stage=failure.stage)
        return SourceAcquisitionUnavailable(
            diagnostic_code="CSV-NEXT-SOURCE-003", stage=failure.stage
        )
    failed_paths = tuple(
        sorted(
            [path for path in reader.read_failures if reader.read_counts.get(path, 0) == 1],
            key=_path_sort_key,
        )
    )
    if not failed_paths:
        return CompleteSourceSeal(seal=seal)
    failures = tuple({"path": path, "stage": "source_read"} for path in failed_paths)
    if not proof_roots:
        return SourceAcquisitionUnavailable(
            diagnostic_code="CSV-NEXT-SOURCE-003", stage="source_read"
        )
    ledger = SourceFailureLedger.from_seal(
        seal,
        failures=failures,
        targets=targets,
        proof_roots=proof_roots,
    )
    if not ledger.safe_subset_proven:
        return SourceAcquisitionUnavailable(
            diagnostic_code="CSV-NEXT-SOURCE-003", stage="source_read"
        )
    return PartialSourceSeal(
        seal=seal,
        ledger=ledger,
        safe_file_set=ledger.safe_file_set,
    )


def request_from_partial_source_seal(
    partial: PartialSourceSeal,
    request: dict[str, Any] | ValidatedAdapterRequest,
) -> ValidatedAdapterRequest:
    """Build a safe-subset request and bind it to the same ledger identity."""

    assert isinstance(partial, PartialSourceSeal)
    validated = validate_adapter_request(request)
    safe = validated.snapshot()
    safe_paths = set(partial.safe_file_set)
    safe["files"] = [row for row in safe["files"] if row["path"] in safe_paths]
    safe["request_id"] = recompute_request_id(safe)
    safe_request = validate_adapter_request(safe)
    _validate_request_matches_source_seal(safe_request, partial.seal)
    register_source_acquisition_seal(safe_request, partial.seal)
    return safe_request


def validate_source_failure_locality(
    ledger: SourceFailureLedger, *, model: dict[str, Any], proof: dict[str, Any]
) -> dict[str, Any]:
    """Join Python source locality evidence with adapter taint evidence."""

    assert isinstance(ledger, SourceFailureLedger)
    failed_paths = {item["path"] for item in ledger.failures}
    proof_paths = {
        root.get("path_ref")
        for root in proof.get("failure_roots", [])
        if root.get("path_ref") is not None
    }
    assert failed_paths <= proof_paths or not ledger.failures
    model_paths = {record.get("path") for record in model.get("files", [])}
    assert failed_paths.isdisjoint(model_paths)
    return classify_source_failure(ledger)


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
    request: dict[str, Any] | ValidatedAdapterRequest,
    raw_response_bytes: bytes,
    source_seal: SourceAcquisitionSeal,
    targets: list[str] | tuple[str, ...] = (),
    target_failures: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
    export_failures: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
    source_failure_ledger: SourceFailureLedger | None = None,
) -> dict[str, Any]:
    """Attach the sole immutable downstream authority to a decision projection."""

    validated_request = validate_adapter_request(request)
    if source_failure_ledger is not None:
        assert source_failure_ledger.source_seal.seal_id == source_seal.seal_id

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
    gate["resolved_limits"] = copy.deepcopy(validated_request["limits"])
    canonical_targets = tuple(
        canonical_target_key(target) for target in validated_request["targets"]
    )
    assert tuple(canonical_target_key(target) for target in targets) == canonical_targets
    publication_context = _publication_context_for_validated_request(
        validated_request,
        run_context,
        source_seal=source_seal,
        toolchain=_toolchain_snapshot(),
        trusted_environment=_trusted_environment_snapshot(),
        projects_for_fingerprint=copy.deepcopy(model["projects"]),
        source_failure_ledger=source_failure_ledger or (),
        process_launch_descriptor=_process_launch_for_toolchain(
            _toolchain_snapshot(),
            node_realpath="/usr/local/bin/node",
            node_sha256="1" * 64,
            spawn_executable="/usr/local/bin/node",
        ),
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
        request=validated_request,
        raw_response_bytes=raw_response_bytes,
        raw_response_sha256=hashlib.sha256(raw_response_bytes).hexdigest(),
        publication_context=publication_context,
    )
    return projection


def validate_response_envelope(
    response_bytes: bytes,
    request: dict[str, Any] | ValidatedAdapterRequest,
    *,
    source_seal: SourceAcquisitionSeal | None = None,
    source_failure_ledger: SourceFailureLedger | None = None,
) -> dict[str, Any]:
    """Validate one adapter response only after bounded raw-byte decoding."""

    # Direct callers are upgraded at the trust boundary; all subsequent
    # validation and publication construction sees the sealed private request
    # type.  The public response boundary itself remains typed-only.
    request = validate_adapter_request(request)
    trusted_source_seal = _trusted_fixture_source_seal(request, source_seal)
    bounded = bounded_decode_json(response_bytes, limits=request["limits"])
    assert bounded["allowed"]
    response = cast(dict[str, Any], bounded["value"])
    # The exact validated wire is retained as an opaque authority.  Rejecting
    # non-canonical JSON here prevents a later publication writer from
    # replacing it with a separately rendered equivalent object.
    assert canonical_json_bytes(response) == response_bytes
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
            raw_response_bytes=response_bytes,
            source_seal=trusted_source_seal,
            targets=request["targets"],
            target_failures=target_failure.failures,
            source_failure_ledger=source_failure_ledger,
        )
    # Collection/reference/proof validation precedes the model-record gate.
    # This makes a response with both a protocol violation and an over-limit
    # model deterministic: protocol wins and no budget diagnostic can mask it.
    actual_entities = validate_model(
        model,
        max_model_records=LIMIT_DEFAULTS["max_total_array_items"],
    )
    validate_proof(response["proof"], model, request_targets=request["targets"])
    # Proof taint/exclusion is authoritative for the second target-resolution
    # pass.  A target can be complete in the raw model and unavailable only
    # after proof derives the tainted closure; that typed reason must reach
    # every downstream surface instead of being silently upgraded by the
    # entity gate.
    proof_target_failure = target_failure_from_proof(response["proof"])
    if proof_target_failure is not None:
        decision = target_failure_decision(proof_target_failure, run_context)
        decision["validated_model"] = copy.deepcopy(model)
        return _with_validated_decision(
            decision,
            model=model,
            proof=response["proof"],
            run_context=run_context,
            pre_budget_outcome="payload_unavailable",
            request=request,
            raw_response_bytes=response_bytes,
            source_seal=trusted_source_seal,
            targets=request["targets"],
            target_failures=proof_target_failure.failures,
            source_failure_ledger=source_failure_ledger,
        )
    _published, _proof_only, wire_records = response_model_record_counts(model, response["proof"])
    if wire_records > request["limits"]["max_model_records"]:
        raise ModelRecordLimitError(wire_records)
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
            raw_response_bytes=response_bytes,
            source_seal=trusted_source_seal,
            targets=request["targets"],
            export_failures=export_failure["export_failures"],
            source_failure_ledger=source_failure_ledger,
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
        raw_response_bytes=response_bytes,
        source_seal=trusted_source_seal,
        targets=request["targets"],
        source_failure_ledger=source_failure_ledger,
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
    process_launch_descriptor_digest: str | None = None,
    source_failure_ledger: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
    source_failure_ledger_digest: str | None = None,
) -> str:
    preimage = {
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
        "source_failure_ledger": copy.deepcopy(list(source_failure_ledger)),
    }
    if process_launch_descriptor_digest is not None:
        preimage["process_launch_descriptor_digest"] = process_launch_descriptor_digest
    if source_failure_ledger_digest is not None:
        preimage["source_failure_ledger_digest"] = source_failure_ledger_digest
    return digest(preimage)


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
            assert value["projects"] == sorted(model["projects"], key=lambda item: item["id"])
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
    independent = value.get("request_independent") is True
    if not independent:
        assert run_context["budget_resolved"] == value["budget"]["resolved"]
    assert run_context["budget_requested"] == value["budget"]["requested"]
    if not independent:
        assert run_context["budget_source"] == value["budget"]["source"]
    if independent:
        # This branch is intentionally explicit about absence.  No default
        # limits, trusted profile, toolchain, compatibility, or source plan
        # may be smuggled into a failure that predates their observation.
        assert value["status"] == "incomplete"
        assert value["incomplete_kind"] == "payload_unavailable"
        assert value["payload_available"] is False
        assert value["entity_count"] is None
        assert value["artifact_paths"] == []
        assert value["request"] is None
        assert value["projects"] == []
        assert value["semantic_compatibility_id"] is None
        assert value["compatibility_descriptor"] is None
        assert value["identity_versions"] is None
        assert value["source_plan_digest"] is None
        assert value["source"]["kind"] == "unavailable"
        assert value["source"]["fingerprint"] is None
        assert value["source"]["file_count"] == 0
        assert value["toolchain"] is None
        assert value["trusted_environment"] is None
        assert value["limits"] is None
        assert value["budget"]["resolved"] is None
        assert value["budget"]["source"] == "unobserved"
        assert value["budget"]["outcome"] == "payload_unavailable"
        assert value["config"]["request_independent"] is True
        assert value["config"]["projects"] == []
        assert value["config"]["limits"] is None
        assert value["config"]["trusted_environment_digest"] is None
        assert value["config"]["source_plan"] is None
        assert value["config"]["source_plan_digest"] is None
        assert value["config"]["domain_config_digest"] == resolved_config_digest(value["config"])
        _validate_public_diagnostics(value["diagnostics"])
        assert all(item["outcome"] == "payload_unavailable" for item in value["diagnostics"])
        decision = getattr(value, "validated_decision", None)
        assert is_next_run_decision(decision)
        context = decision.publication_context
        assert context is not None
        assert context.observation_provenance["kind"] == "request_independent"
        assert value["run_fingerprint"] == digest(context.run_fingerprint_preimage)
        assert value["coverage"]["counts"]["internal_entities"] == 0
        assert value["coverage"]["counts"]["published"] == 0
        assert value["coverage"]["counts"]["discovered"] == 0
        return
    validate_compatibility_descriptor(value["compatibility_descriptor"])
    assert (
        value["semantic_compatibility_id"] == value["compatibility_descriptor"]["compatibility_id"]
    )
    validate_limits_consistency(value["limits"], value["config"]["limits"])
    validate_trusted_environment(value["trusted_environment"])
    _validate_public_diagnostics(value["diagnostics"])
    decision = getattr(value, "validated_decision", None)
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
        assert project["source_roots"] == sorted(project["source_roots"], key=_path_sort_key)
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
        key=lambda project: _path_sort_key(project["root"]),
    )
    assert [project["root"] for project in expected_config_projects] == sorted(
        (project["root"] for project in value["projects"]), key=_path_sort_key
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
            reason = item.get("reason")
            assert reason in TARGET_FAILURE_REASONS
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
    decision = getattr(value, "validated_decision", None)
    launch_digest = (
        digest(decision.publication_context.process_launch_descriptor)
        if is_next_run_decision(decision)
        else None
    )
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
        process_launch_descriptor_digest=launch_digest,
        source_failure_ledger=(
            decision.publication_context.source_failure_ledger
            if is_next_run_decision(decision)
            else ()
        ),
        source_failure_ledger_digest=(
            decision.publication_context.source_failure_ledger_digest
            if is_next_run_decision(decision)
            else None
        ),
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
    # to the explicit selected-stream bound avoids two authorities while
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
    assert resolved is not None
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


class ModelRecordLimitError(AssertionError):
    """Schema/proof-valid response exceeded the configured model-record cap."""

    def __init__(self, measured: int) -> None:
        self.measured = measured
        super().__init__(f"model records exceed configured limit: {measured}")


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
    response_limit = resolved_limits["max_adapter_response_bytes"]
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
            "reason": "max_adapter_response_bytes",
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


def response_boundary_decision(
    response_bytes: bytes, request: ValidatedAdapterRequest
) -> NextRunDecision:
    """Return one closed decision for every response-boundary failure.

    A real adapter response is never routed directly to a domain projection:
    raw-byte/decode failures become a pre-response decision, while a
    schema/proof/reference failure is classified as protocol failure before
    the same decision is projected.  A valid response returns the immutable
    decision created by :func:`validate_response_envelope`.
    """

    assert isinstance(request, ValidatedAdapterRequest), (
        "response boundary requires a validated private request"
    )
    bounded = bounded_decode_json(response_bytes, limits=request["limits"])
    if not bounded["allowed"]:
        structural_reasons = {
            "max_adapter_response_bytes",
            "max_array_items",
            "max_total_array_items",
            "max_json_nesting",
            "max_json_string_bytes",
        }
        is_structural_limit = bounded["reason"] in structural_reasons
        failure_stage = (
            "response_raw_bytes"
            if bounded["reason"] == "max_adapter_response_bytes"
            else "response_decode"
        )
        failure_code = "CSV-NEXT-LIMIT-003" if is_structural_limit else "CSV-NEXT-PROTOCOL-001"
        return pre_response_failure_decision(
            request,
            stage=failure_stage,
            diagnostic_code=failure_code,
            stdout_bytes=bounded["bytes"],
            decision_context=decision_context_for_request(
                request,
                stage=failure_stage,
                diagnostic_code=failure_code,
                known_counts=_decision_known_counts(request, stdout_bytes=bounded["bytes"]),
                source_failure_ledger=(),
            ),
        )
    try:
        projection = validate_response_envelope(response_bytes, request)
    except ModelRecordLimitError as failure:
        failure_stage = "model_validation"
        failure_code = "CSV-NEXT-LIMIT-005"
        return pre_response_failure_decision(
            request,
            stage=failure_stage,
            diagnostic_code=failure_code,
            model_records=failure.measured,
            stdout_bytes=bounded["bytes"],
            decision_context=decision_context_for_request(
                request,
                stage=failure_stage,
                diagnostic_code=failure_code,
                known_counts=_decision_known_counts(
                    request,
                    stdout_bytes=bounded["bytes"],
                    model_records=failure.measured,
                ),
                source_failure_ledger=(),
            ),
        )
    except AssertionError:
        failure_stage = "response_validation"
        failure_code = "CSV-NEXT-PROTOCOL-001"
        return pre_response_failure_decision(
            request,
            stage=failure_stage,
            diagnostic_code=failure_code,
            decision_context=decision_context_for_request(
                request,
                stage=failure_stage,
                diagnostic_code=failure_code,
                known_counts=_decision_known_counts(request, stdout_bytes=bounded["bytes"]),
                source_failure_ledger=(),
            ),
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


def _canonical_measurement_value(value: Any) -> Any:
    """Make retained byte buffers explicit before canonical JSON hashing."""

    if isinstance(value, bytes):
        return {"__bytes_hex__": value.hex()}
    if isinstance(value, dict):
        return {key: _canonical_measurement_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical_measurement_value(item) for item in value]
    return value


def publication_measurement_digest(
    *,
    adapter_stdout: dict[str, Any],
    adapter_stderr: dict[str, Any],
    public_stderr: dict[str, Any],
    selected_stdout: dict[str, Any],
) -> str:
    """Bind all boundary measurements to the immutable final seal."""

    return digest(
        _canonical_measurement_value(
            {
                "adapter_stdout": adapter_stdout,
                "adapter_stderr": adapter_stderr,
                "public_stderr": public_stderr,
                "selected_stdout": selected_stdout,
            }
        )
    )


def _publication_artifact_descriptors(
    artifact_bytes: Mapping[str, bytes],
) -> dict[str, dict[str, Any]]:
    """Derive persisted artifact descriptors from the sealed byte map."""

    descriptors: dict[str, dict[str, Any]] = {}
    for path in sorted(artifact_bytes):
        payload = artifact_bytes[path]
        assert path in {"next.snapshot.semantic.json", "next.snapshot.puml"}
        assert isinstance(payload, bytes)
        format_name = "semantic-json" if path.endswith(".json") else "plantuml"
        descriptors[path] = {
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
    return descriptors


def _validate_artifacts_against_decision(
    decision: NextRunDecision,
    artifact_bytes: Mapping[str, bytes],
    *,
    payload_unavailable: bool,
) -> None:
    """Prove that sealed artifact bytes are the accepted model projection.

    A path/size/hash descriptor alone is not publication authority: a caller
    could otherwise replace a valid artifact with another schema-valid file.
    The final boundary therefore validates the exact semantic and PlantUML
    projection against the immutable decision before it exposes descriptors.
    """

    if not isinstance(decision, NextValidatedDecision):
        assert not artifact_bytes
        return
    context = decision.publication_context
    assert context.public_next_request is not None
    model = decision.validated_model
    expected_paths = set(decision.gate["artifact_paths"])
    if payload_unavailable:
        assert not artifact_bytes
        return
    assert set(artifact_bytes) == expected_paths
    status = "partial_safe" if decision.gate["outcome"] == "partial_safe" else "complete"
    assert context.compatibility_descriptor is not None
    assert context.public_next_request is not None
    compatibility_descriptor = context.compatibility_descriptor
    public_request = context.public_next_request
    for path, payload in artifact_bytes.items():
        assert isinstance(payload, bytes)
        if path == "next.snapshot.semantic.json":
            assert payload.endswith(b"\n")
            value = json.loads(payload.decode("utf-8"))
            assert isinstance(value, dict)
            validate_semantic_snapshot(value)
            assert value["status"] == ("incomplete" if status == "partial_safe" else "complete")
            if status == "partial_safe":
                assert value["incomplete_kind"] == "partial_safe"
            assert (
                value["semantic_compatibility_id"] == compatibility_descriptor["compatibility_id"]
            )
            assert value["compatibility_descriptor"] == compatibility_descriptor
            assert value["identity_versions"] == compatibility_descriptor["identity_versions"]
            assert value["source"]["fingerprint"] == context.source_view_fingerprint
            assert value["request"] == public_request
            assert value["request"]["run_fingerprint"] == digest(context.run_fingerprint_preimage)
            assert value["coverage"] == model["coverage"]
            assert value["projects"] == sorted(model["projects"], key=lambda item: item["id"])
            assert value["files"] == model["files"]
            assert value["entities"] == [*model["modules"], *model["components"]]
            assert value["members"] == model["members"]
            assert value["relations"] == model["relations"]
            assert value["facts"] == model["facts"]
            assert payload == canonical_json_bytes(value) + b"\n"
        elif path == "next.snapshot.puml":
            expected = render_plantuml(model, status=status)
            assert payload == expected
            validate_plantuml_contract(payload, model, status=status)
        else:
            raise AssertionError("unknown Next artifact path")


def publication_boundary_seal(
    *,
    semantic_decision: NextRunDecision,
    response_bytes: bytes,
    validated_request_id: str | None,
    response_sha256: str | None,
    response_model_digest: str | None,
    artifact_bytes: Mapping[str, bytes],
    artifact_descriptors: Mapping[str, dict[str, Any]],
    selector: str | None,
    selected_stdout: dict[str, Any],
    sealed_stdout_result: bytes,
    diagnostic_jsonl: bytes,
    measurement_digest: str,
) -> str:
    """Hash every byte and identity used by the final publication boundary."""

    return digest(
        {
            "decision_run_fingerprint": digest(
                semantic_decision.publication_context.run_fingerprint_preimage
            ),
            "response_bytes": _canonical_measurement_value(response_bytes),
            "validated_request_id": validated_request_id,
            "response_sha256": response_sha256,
            "response_model_digest": response_model_digest,
            "artifact_bytes": _canonical_measurement_value(dict(artifact_bytes)),
            "artifact_descriptors": copy.deepcopy(dict(artifact_descriptors)),
            "selector": selector,
            "selected_stdout": _canonical_measurement_value(selected_stdout),
            "sealed_stdout_result": _canonical_measurement_value(sealed_stdout_result),
            "diagnostic_jsonl": _canonical_measurement_value(diagnostic_jsonl),
            "measurement_digest": measurement_digest,
        }
    )


def candidate_key_for_selector(selector: str | None) -> str:
    """Return the sealed stdout candidate key for one closed selector."""

    return {
        None: "summary",
        "manifest": "manifest",
        "next:semantic-json": "next.snapshot.semantic.json",
        "next:plantuml": "next.snapshot.puml",
    }[selector]


def _publication_domain_status(decision: NextRunDecision) -> str:
    if isinstance(decision, NextValidatedDecision):
        outcome = decision.gate["outcome"]
    else:
        outcome = decision.outcome
    return {
        "complete": "complete",
        "partial_safe": "incomplete",
        "payload_unavailable": "incomplete",
        "not_applicable": "not_applicable",
    }[outcome]


def _sealed_selected_unavailable_result(
    decision: NextRunDecision,
    selector: str | None,
    candidates: Mapping[str, bytes],
    artifact_descriptors: Mapping[str, Mapping[str, Any]],
) -> bytes:
    """Build the typed selected-copy result before the boundary is sealed."""

    if selector is None:
        result: dict[str, Any] = {
            "type": "stdout_result",
            "schema": "code-structure-viz.stdout-result/v1",
            "selector": None,
            "availability": False,
            "run_status": "incomplete",
            "stable_reason": "run_summary",
            "selected_stdout_unavailable": True,
            "artifact": None,
        }
    elif selector == "manifest":
        manifest = candidates["manifest"]
        result = {
            "type": "stdout_result",
            "schema": "code-structure-viz.stdout-result/v1",
            "selector": "manifest",
            "availability": False,
            "domain_status": _publication_domain_status(decision),
            "stable_reason": "selected_artifact_unavailable",
            "selected_stdout_unavailable": True,
            "artifact": {
                "path": "run-manifest.json",
                "domain": "next",
                "format": "semantic-json",
                "media_type": "application/json",
                "size_bytes": len(manifest),
                "sha256": hashlib.sha256(manifest).hexdigest(),
            },
        }
    else:
        assert selector in {"next:semantic-json", "next:plantuml"}
        selected_path = (
            "next.snapshot.semantic.json"
            if selector == "next:semantic-json"
            else "next.snapshot.puml"
        )
        result = {
            "type": "stdout_result",
            "schema": "code-structure-viz.stdout-result/v1",
            "selector": selector,
            "availability": False,
            "domain_status": _publication_domain_status(decision),
            "stable_reason": "selected_artifact_unavailable",
            "selected_stdout_unavailable": True,
            "artifact": dict(artifact_descriptors[selected_path]),
        }
    if result.get("domain_status") == "incomplete":
        outcome = (
            decision.gate["outcome"]
            if isinstance(decision, NextValidatedDecision)
            else decision.outcome
        )
        if outcome == "partial_safe":
            result["incomplete_kind"] = "partial_safe"
    return canonical_json_bytes(result) + b"\n"


def _sealed_payload_unavailable_result(decision: NextRunDecision) -> bytes:
    """Return the canonical typed result for a transport-level failure.

    A valid selector must never turn a transport failure into an empty
    stdout stream.  The only selector-specific exception is ``null`` (the
    run-summary branch), which still carries the explicit selected-unavailable
    discriminator; all other selectors use the compact generic unavailable
    branch because no artifact descriptor was published.
    """

    selector = decision.publication_context.run_context["stdout_selector"]
    if selector is None:
        return _sealed_selected_unavailable_result(decision, selector, {"summary": b""}, {})
    result: dict[str, Any] = {
        "type": "stdout_result",
        "schema": "code-structure-viz.stdout-result/v1",
        "selector": selector,
        "availability": False,
        "domain_status": "incomplete",
        "stable_reason": "domain_payload_unavailable",
        "artifact": None,
    }
    return canonical_json_bytes(result) + b"\n"


@dataclass(frozen=True, kw_only=True)
class PublicationBoundaryDecision:
    """Final immutable publication result for every output surface.

    Capture, public-stderr encoding, and selected-artifact copying are
    measurements only until this object is sealed.  Domain, root manifest,
    stdout, stderr, and exit projections must consume this one result; a
    selected-copy failure therefore cannot rewrite the already validated
    semantic decision behind the caller's back.
    """

    semantic_decision: NextRunDecision
    artifact_bytes: dict[str, bytes]
    sealed_stdout_candidates: dict[str, bytes]
    adapter_stdout: dict[str, Any]
    adapter_stderr: dict[str, Any]
    public_stderr: dict[str, Any]
    selected_stdout: dict[str, Any]
    measurement_digest: str
    publication_outcome: str
    exit_code: int
    response_bytes: bytes = field(init=False)
    diagnostic_jsonl: bytes = field(init=False)
    validated_request_id: str | None = field(init=False)
    response_sha256: str | None = field(init=False)
    response_model_digest: str | None = field(init=False)
    artifact_descriptors: dict[str, dict[str, Any]] = field(init=False)
    selector: str | None = field(init=False)
    sealed_stdout_result: bytes = field(init=False)
    publication_seal: str = field(init=False)

    def __post_init__(self) -> None:
        assert is_next_run_decision(self.semantic_decision)
        sealed_response = (
            self.semantic_decision.raw_response_bytes
            if isinstance(self.semantic_decision, ValidatedResponseDecision)
            and self.adapter_stdout["allowed"]
            else b""
        )
        object.__setattr__(self, "response_bytes", bytes(sealed_response))
        object.__setattr__(self, "diagnostic_jsonl", bytes(self.public_stderr["payload"]))
        expected_diagnostics = decision_public_diagnostics(self.semantic_decision)
        if self.public_stderr["allowed"]:
            assert self.diagnostic_jsonl == _public_diagnostic_jsonl(expected_diagnostics)
        artifact_bytes = dict(self.artifact_bytes)
        stdout_candidates = dict(self.sealed_stdout_candidates)
        assert all(
            isinstance(path, str) and isinstance(payload, bytes)
            for path, payload in artifact_bytes.items()
        )
        assert all(
            isinstance(path, str) and isinstance(payload, bytes)
            for path, payload in stdout_candidates.items()
        )
        object.__setattr__(self, "response_bytes", bytes(self.response_bytes))
        object.__setattr__(self, "artifact_bytes", copy.deepcopy(artifact_bytes))
        object.__setattr__(self, "sealed_stdout_candidates", copy.deepcopy(stdout_candidates))
        object.__setattr__(self, "diagnostic_jsonl", bytes(self.diagnostic_jsonl))
        for name in ("adapter_stdout", "adapter_stderr", "public_stderr", "selected_stdout"):
            object.__setattr__(self, name, copy.deepcopy(getattr(self, name)))
        assert re.fullmatch(r"[0-9a-f]{64}", self.measurement_digest)
        assert self.measurement_digest == publication_measurement_digest(
            adapter_stdout=self.adapter_stdout,
            adapter_stderr=self.adapter_stderr,
            public_stderr=self.public_stderr,
            selected_stdout=self.selected_stdout,
        )
        assert self.publication_outcome in {
            "published",
            "payload_unavailable",
            "selected_artifact_unavailable",
        }
        capture_failed = not self.adapter_stdout["allowed"] or not self.adapter_stderr["allowed"]
        stderr_failed = not self.public_stderr["allowed"]
        selected_failed = not self.selected_stdout["allowed"]
        expected_outcome = (
            "payload_unavailable"
            if capture_failed or stderr_failed
            else "selected_artifact_unavailable"
            if selected_failed
            else "published"
        )
        assert self.publication_outcome == expected_outcome
        expected_exit = (
            3
            if _decision_exit_code(self.semantic_decision) == 3 or expected_outcome != "published"
            else 0
        )
        assert self.exit_code == expected_exit

        context = self.semantic_decision.publication_context
        self_selector = context.run_context["stdout_selector"]
        object.__setattr__(self, "selector", self_selector)
        if isinstance(self.semantic_decision, NextValidatedDecision):
            request = self.semantic_decision.request
            request_id = request["request_id"]
            model_digest = digest(self.semantic_decision.validated_model)
            object.__setattr__(self, "validated_request_id", request_id)
            if self.adapter_stdout["allowed"]:
                assert self.response_bytes
                assert self.adapter_stdout["retained"] == self.response_bytes
                decoded = json.loads(self.response_bytes.decode("utf-8"))
                assert isinstance(decoded, dict)
                assert canonical_json_bytes(decoded) == self.response_bytes
                assert decoded["request_id"] == request_id
                assert decoded["model_digest"] == model_digest
                object.__setattr__(
                    self,
                    "response_sha256",
                    hashlib.sha256(self.response_bytes).hexdigest(),
                )
                object.__setattr__(self, "response_model_digest", model_digest)
            else:
                assert self.response_bytes == b""
                object.__setattr__(self, "response_sha256", None)
                object.__setattr__(self, "response_model_digest", None)
            expected_paths = set(self.semantic_decision.gate["artifact_paths"])
            if expected_outcome == "payload_unavailable":
                assert artifact_bytes == {}
            else:
                assert set(artifact_bytes) == expected_paths
        else:
            assert self.response_bytes == b""
            assert artifact_bytes == {}
            object.__setattr__(self, "validated_request_id", None)
            object.__setattr__(self, "response_sha256", None)
            object.__setattr__(self, "response_model_digest", None)
        assert {"summary", "manifest"} <= set(stdout_candidates)
        for candidate_name in ("summary", "manifest"):
            candidate = stdout_candidates[candidate_name]
            parsed_candidate = json.loads(candidate.decode("utf-8"))
            assert isinstance(parsed_candidate, dict)
            assert canonical_json_bytes(parsed_candidate) + b"\n" == candidate
        if (
            isinstance(self.semantic_decision, NextValidatedDecision)
            and expected_outcome != "payload_unavailable"
        ):
            expected_paths = set(self.semantic_decision.gate["artifact_paths"])
            assert expected_paths <= set(stdout_candidates)
            assert all(stdout_candidates[path] == artifact_bytes[path] for path in expected_paths)
        _validate_artifacts_against_decision(
            self.semantic_decision,
            artifact_bytes,
            payload_unavailable=expected_outcome == "payload_unavailable",
        )
        if self_selector in {"next:semantic-json", "next:plantuml"}:
            selected_path = (
                "next.snapshot.semantic.json"
                if self_selector == "next:semantic-json"
                else "next.snapshot.puml"
            )
            if self.selected_stdout["allowed"] and expected_outcome != "payload_unavailable":
                assert selected_path in stdout_candidates
                assert self.selected_stdout["retained"] == artifact_bytes.get(selected_path, b"")
            elif expected_outcome == "selected_artifact_unavailable":
                assert selected_path in artifact_bytes
        else:
            # Summary and manifest are selected stdout streams too.  Their
            # exact bytes are supplied to the same bounded copy gate; an
            # overrun is represented by the final typed-unavailable branch,
            # never by silently treating the stream as an empty success.
            if expected_outcome == "selected_artifact_unavailable":
                assert not self.selected_stdout["allowed"]
            else:
                assert self.selected_stdout["allowed"]
                if expected_outcome == "published":
                    assert self.selected_stdout["retained"]
        assert candidate_key_for_selector(self_selector) in stdout_candidates
        if self.selected_stdout["allowed"]:
            assert (
                self.selected_stdout["retained"]
                == stdout_candidates[candidate_key_for_selector(self_selector)]
            )
        descriptors = _publication_artifact_descriptors(artifact_bytes)
        object.__setattr__(self, "artifact_descriptors", descriptors)
        sealed_result = b""
        if expected_outcome == "payload_unavailable":
            sealed_result = _sealed_payload_unavailable_result(self.semantic_decision)
        elif expected_outcome == "selected_artifact_unavailable":
            sealed_result = _sealed_selected_unavailable_result(
                self.semantic_decision,
                self.selector,
                stdout_candidates,
                descriptors,
            )
        object.__setattr__(self, "sealed_stdout_result", sealed_result)
        expected_seal = publication_boundary_seal(
            semantic_decision=self.semantic_decision,
            response_bytes=self.response_bytes,
            validated_request_id=self.validated_request_id,
            response_sha256=self.response_sha256,
            response_model_digest=self.response_model_digest,
            artifact_bytes=artifact_bytes,
            artifact_descriptors=descriptors,
            selector=self.selector,
            selected_stdout=self.selected_stdout,
            sealed_stdout_result=sealed_result,
            diagnostic_jsonl=self.diagnostic_jsonl,
            measurement_digest=self.measurement_digest,
        )
        object.__setattr__(self, "publication_seal", expected_seal)

    def __getattribute__(self, name: str) -> Any:
        value = object.__getattribute__(self, name)
        if name in {
            "response_bytes",
            "artifact_bytes",
            "diagnostic_jsonl",
            "adapter_stdout",
            "adapter_stderr",
            "public_stderr",
            "selected_stdout",
            "artifact_descriptors",
            "sealed_stdout_candidates",
            "sealed_stdout_result",
        }:
            return copy.deepcopy(value)
        return value


def _publication_rendered_candidates(
    decision: NextRunDecision,
) -> tuple[dict[str, Any], dict[str, bytes], dict[str, bytes]]:
    """Render publication candidates from the semantic decision only.

    The reference renderer is kept in the contract test module alongside the
    schema-aware domain/manifest helpers.  Importing it lazily avoids a module
    cycle during test collection while ensuring the finalizer has no caller
    supplied candidate, status, or payload authority.
    """

    from tests.contracts.test_next_contracts import (
        _domain,
        _run_manifest,
        _run_summary_value,
        _semantic_artifacts_from_decision,
    )

    domain = _domain(decision=decision)
    artifacts = _semantic_artifacts_from_decision(decision)
    manifest = _run_manifest(domain)
    summary = _run_summary_value(manifest["run"]["status"], domain)
    candidates = {
        "summary": _canonical_json_line(summary),
        "manifest": _canonical_json_line(manifest),
        **{path: bytes(payload) for path, payload in artifacts.items()},
    }
    return domain, artifacts, candidates


def _publication_failure_domain(
    decision: NextRunDecision,
    *,
    diagnostics: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Produce the single transport-failure projection used to render bytes."""

    from tests.contracts.test_next_contracts import _domain

    domain = _domain(decision=decision)
    domain["status"] = "incomplete"
    domain["incomplete_kind"] = "payload_unavailable"
    domain["payload_available"] = False
    domain["entity_count"] = None
    domain["budget"]["actual"] = None
    domain["budget"]["outcome"] = "payload_unavailable"
    domain["artifact_paths"] = []
    if diagnostics is not None:
        domain["diagnostics"] = copy.deepcopy(diagnostics)
    else:
        domain["diagnostics"] = [_public_limit_diagnostic()]
    return domain


def finalize_publication_decision(
    semantic_decision: NextRunDecision,
    *,
    adapter_stdout_chunks: Iterable[bytes],
    adapter_stderr_chunks: Iterable[bytes] = (),
    adapter_stdout_limit: int = LIMIT_DEFAULTS["max_adapter_stdout_capture_bytes"],
    adapter_stderr_limit: int = LIMIT_DEFAULTS["max_adapter_stderr_capture_bytes"],
    public_stderr_limit: int = LIMIT_DEFAULTS["max_stderr_bytes"],
    selected_stdout_limit: int = LIMIT_DEFAULTS["max_selected_stdout_bytes"],
) -> PublicationBoundaryDecision:
    """Seal all capture/publication measurements around one semantic decision.

    Artifact and stdout candidate bytes are generated after the capture gates
    from ``semantic_decision``.  They are intentionally not accepted as
    caller arguments, so a canonical but forged manifest cannot enter the
    publication seal.
    """

    assert is_next_run_decision(semantic_decision)
    selector = semantic_decision.publication_context.run_context["stdout_selector"]
    decoder: Any | None = None
    if isinstance(semantic_decision, NextValidatedDecision):
        decoder = lambda payload: response_boundary_decision(  # noqa: E731
            payload, semantic_decision.request
        )
    adapter_stdout = capture_adapter_stdout(
        adapter_stdout_chunks,
        limit=adapter_stdout_limit,
        decoder=decoder,
    )
    if isinstance(semantic_decision, NextValidatedDecision) and adapter_stdout["allowed"]:
        assert adapter_stdout["retained"] == semantic_decision.raw_response_bytes
    adapter_stderr = capture_adapter_stderr(adapter_stderr_chunks, limit=adapter_stderr_limit)
    public_stderr = render_public_diagnostic_stderr(
        decision_public_diagnostics(semantic_decision), limit=public_stderr_limit
    )
    capture_failed = not adapter_stdout["allowed"] or not adapter_stderr["allowed"]
    stderr_failed = not public_stderr["allowed"]
    if capture_failed or stderr_failed:
        failure_domain = _publication_failure_domain(
            semantic_decision,
            diagnostics=(
                public_stderr["manifest_diagnostics"]
                if stderr_failed
                else [_public_limit_diagnostic()]
            ),
        )
        from tests.contracts.test_next_contracts import (
            _run_manifest,
            _run_summary_value,
        )

        failure_manifest = _run_manifest(failure_domain)
        failure_summary = _run_summary_value(failure_manifest["run"]["status"], failure_domain)
        candidates = {
            "summary": _canonical_json_line(failure_summary),
            "manifest": _canonical_json_line(failure_manifest),
        }
        if isinstance(semantic_decision, NextValidatedDecision):
            for format_name in semantic_decision.run_context["requested_formats"]:
                candidates.setdefault(
                    "next.snapshot.semantic.json"
                    if format_name == "semantic-json"
                    else "next.snapshot.puml",
                    b"",
                )
        artifacts: dict[str, bytes] = {}
        selected_stdout = copy_selected_stdout(
            candidates[candidate_key_for_selector(selector)], limit=selected_stdout_limit
        )
        outcome = "payload_unavailable"
    else:
        _domain, artifacts, candidates = _publication_rendered_candidates(semantic_decision)
        candidate_key = candidate_key_for_selector(selector)
        selected_stdout = copy_selected_stdout(
            candidates[candidate_key], limit=selected_stdout_limit
        )
        if selected_stdout["allowed"]:
            outcome = "published"
        else:
            # Measure the successful candidate once.  On breach, persist a
            # failure manifest and emit a typed unavailable result; do not
            # copy or re-measure the failure manifest as the selected stream.
            success_manifest = json.loads(candidates["manifest"].decode("utf-8"))
            assert isinstance(success_manifest, dict)
            success_manifest["run"]["status"] = "incomplete"
            success_manifest["run"]["exit_code"] = 3
            candidates["manifest"] = canonical_json_bytes(success_manifest) + b"\n"
            failure_summary = json.loads(candidates["summary"].decode("utf-8"))
            assert isinstance(failure_summary, dict)
            failure_summary["run_status"] = "incomplete"
            failure_summary["exit_code"] = 3
            candidates["summary"] = canonical_json_bytes(failure_summary) + b"\n"
            outcome = "selected_artifact_unavailable"
    return PublicationBoundaryDecision(
        semantic_decision=semantic_decision,
        artifact_bytes=artifacts,
        sealed_stdout_candidates=candidates,
        adapter_stdout=adapter_stdout,
        adapter_stderr=adapter_stderr,
        public_stderr=public_stderr,
        selected_stdout=selected_stdout,
        measurement_digest=publication_measurement_digest(
            adapter_stdout=adapter_stdout,
            adapter_stderr=adapter_stderr,
            public_stderr=public_stderr,
            selected_stdout=selected_stdout,
        ),
        publication_outcome=outcome,
        exit_code=3 if _decision_exit_code(semantic_decision) == 3 or outcome != "published" else 0,
    )


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
    response_limit = resolved["max_adapter_response_bytes"]
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
            "diagnostic_code": "CSV-NEXT-LIMIT-003",
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
    paths = []
    for target in targets:
        path = target.removeprefix(TARGET_SELECTOR_PREFIX)
        _assert_path(path, allow_root=True)
        paths.append(path)
    normalized = [canonical_target_key(target) for target in targets]
    assert normalized == targets
    # Target selectors are path-only rows.  Compare their normalized UTF-8
    # bytes directly so JSON escaping (for example a quote) cannot change
    # request order.  Object rows elsewhere retain canonical JSON ordering.
    assert paths == sorted(paths, key=_path_sort_key)
    assert len(paths) == len(set(paths))


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
        failure_by_key = {item["target_key"]: item["reason"] for item in preflight.failures}
        return [
            {
                "target_key": canonical_target_key(target),
                "status": "failed"
                if canonical_target_key(target) in failure_by_key
                else "resolved",
                "record_ids": [],
                **(
                    {"reason": failure_by_key[canonical_target_key(target)]}
                    if canonical_target_key(target) in failure_by_key
                    else {}
                ),
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
            reason = "missing" if not matching_files else "project_ambiguity"
        elif len(exact_files) > 1:
            # Two frozen Files with one public path are an ambiguous source
            # view, even if their record IDs differ after a mutation.
            matching = []
            status = "failed"
            reason = "duplicate"
        elif exact_files and not _is_program_file(exact_files[0]):
            # A direct context/control file is provenance only.  It cannot be
            # addressed as a semantic Next target even when it is frozen.
            matching = []
            status = "failed"
            reason = _target_non_program_reason(exact_files[0])
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
                        "reason": "duplicate",
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
                reason = "selected_taint"
            else:
                status = "resolved"
        resolutions.append(
            {
                "target_key": target_key,
                "status": status,
                "record_ids": matching if status == "resolved" else [],
                **({"reason": reason} if status == "failed" else {}),
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
    budget_resolved: int | None,
    budget_source: str,
    stdout_selector: str | None,
) -> NextRunContext:
    """Construct and validate the explicit context shared by all run surfaces."""

    formats = list(requested_formats)
    _assert_formats(formats)
    assert budget_requested is None or 1 <= budget_requested <= 100000
    assert budget_source in RUN_CONTEXT_BUDGET_SOURCES
    assert stdout_selector in RUN_CONTEXT_SELECTORS
    if stdout_selector is not None and stdout_selector != "manifest":
        assert stdout_selector.removeprefix("next:") in formats
    if budget_resolved is None:
        assert budget_requested is None
        assert budget_source == "unobserved"
    else:
        assert 1 <= budget_resolved <= 100000
        assert budget_source != "unobserved"
    if budget_source == "builtin":
        assert budget_requested is None
    elif budget_source != "unobserved":
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
    request: Mapping[str, Any] | None,
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


def decision_context_for_request(
    request: ValidatedAdapterRequest,
    *,
    stage: str,
    diagnostic_code: str,
    known_counts: dict[str, int | None],
    source_failure_ledger: tuple[dict[str, Any], ...],
) -> NextDecisionContext:
    """Seal explicit pre-response identity before constructing a failure.

    ``pre_response_failure_decision`` intentionally does not reconstruct this
    context.  The caller at the failure boundary must provide the observed
    counters and source ledger that belong to the same validated request.
    """

    assert isinstance(request, ValidatedAdapterRequest)
    return NextDecisionContext(
        run_context=request["run_context"],
        request_id=request["request_id"],
        targets=tuple(request["targets"]),
        limits=copy.deepcopy(request["limits"]),
        stage=stage,
        diagnostic_code=diagnostic_code,
        failure_kind=decision_failure_kind(diagnostic_code),
        known_counts=copy.deepcopy(known_counts),
        source_failure_ledger=source_failure_ledger,
        outcome="payload_unavailable",
        payload_unavailable=True,
        exit_code=3,
        provenance_observation=_decision_provenance(
            kind="request_bound",
            stage=stage,
            request=True,
            limits=True,
            source_plan=False,
            toolchain=False,
            trusted_environment=False,
        ),
        provenance="request_bound",
    )


def pre_response_failure_decision(
    request: dict[str, Any] | ValidatedAdapterRequest | None,
    *,
    stage: str,
    diagnostic_code: str,
    known_counts: dict[str, int | None] | None = None,
    stdout_bytes: int | None = None,
    model_records: int | None = None,
    run_context: NextRunContext | None = None,
    decision_context: NextDecisionContext,
    path: str | None = None,
    symbol: str | None = None,
    source_failure_ledger: SourceFailureLedger | None = None,
    source_seal: SourceAcquisitionSeal | None = None,
) -> PreResponseFailureDecision:
    """Create the closed authority for a failure before response validation."""

    validated_request = validate_adapter_request(request) if request is not None else None
    # A request-independent failure (for example config/project discovery)
    # cannot fabricate a request.  The caller must supply its resolved run
    # context explicitly through the decision context or argument.
    context_source = (
        validated_request["run_context"]
        if validated_request is not None
        else decision_context.run_context
    )
    if run_context is not None:
        assert canonical_run_context(**run_context) == canonical_run_context(**context_source)
    context = canonical_run_context(**context_source)
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
    context_counts = decision_context.known_counts
    resolved_counts = copy.deepcopy(
        known_counts
        if known_counts is not None
        else context_counts
        if context_counts is not None
        else _decision_known_counts(
            validated_request,
            stdout_bytes=stdout_bytes,
            model_records=model_records,
        )
    )
    request_values: dict[str, Any] = (
        dict(validated_request) if validated_request is not None else {}
    )
    node_stages = {"node_discovery", "node_spawn", "node_timeout", "node_process"}
    effective_decision_context = decision_context
    assert effective_decision_context.run_context == context
    assert effective_decision_context.stage == stage
    assert effective_decision_context.diagnostic_code == diagnostic_code
    assert effective_decision_context.known_counts == resolved_counts
    if validated_request is not None:
        assert effective_decision_context.request_id == request_values.get("request_id")
        assert tuple(effective_decision_context.targets) == tuple(request_values.get("targets", ()))
        assert effective_decision_context.limits == request_values.get("limits")
    if source_failure_ledger is not None:
        assert diagnostic_code == "CSV-NEXT-SOURCE-003"
        assert effective_decision_context.source_failure_ledger == tuple(
            source_failure_ledger.failures
        )
    if validated_request is None:
        publication_context = _publication_context_for_request_independent_failure(
            run_context=context,
            decision_context=effective_decision_context,
            stage=stage,
            diagnostic_code=diagnostic_code,
            source_failure_ledger=(
                source_failure_ledger or effective_decision_context.source_failure_ledger
            ),
        )
    else:
        trusted_source_seal = _trusted_fixture_source_seal(validated_request, source_seal)
        publication_context = _publication_context_for_validated_request(
            validated_request,
            context,
            source_seal=trusted_source_seal,
            toolchain=_toolchain_snapshot(
                node_status="unavailable" if stage in node_stages else "available"
            ),
            trusted_environment=_trusted_environment_snapshot(),
            source_failure_ledger=(
                source_failure_ledger or effective_decision_context.source_failure_ledger
            ),
            process_launch_descriptor=_process_launch_for_toolchain(
                _toolchain_snapshot(
                    node_status="unavailable" if stage in node_stages else "available"
                ),
                node_realpath=None if stage in node_stages else "/usr/local/bin/node",
                node_sha256=None if stage in node_stages else "1" * 64,
                spawn_executable=None if stage in node_stages else "/usr/local/bin/node",
            ),
        )
    return PreResponseFailureDecision(
        request=validated_request,
        run_context=context,
        stage=stage,
        diagnostic_code=diagnostic_code,
        diagnostic=diagnostic,
        known_counts=resolved_counts,
        decision_context=effective_decision_context,
        publication_context=publication_context,
    )


def not_applicable_decision(request: dict[str, Any]) -> NotApplicableDecision:
    """Create the closed authority for an intentional non-Next project."""

    validated_request = validate_adapter_request(request)
    context = canonical_run_context(**validated_request["run_context"])
    decision_context = NextDecisionContext(
        run_context=context,
        request_id=validated_request["request_id"],
        targets=tuple(validated_request["targets"]),
        limits=copy.deepcopy(validated_request["limits"]),
        stage="applicability",
        diagnostic_code="CSV-NEXT-APPLICABILITY-001",
        failure_kind="applicability",
        known_counts=_decision_known_counts(validated_request),
        source_failure_ledger=(),
        outcome="not_applicable",
        payload_unavailable=False,
        exit_code=0,
        provenance_observation=_decision_provenance(
            kind="request_bound",
            stage="applicability",
            request=True,
            limits=True,
            source_plan=False,
            toolchain=False,
            trusted_environment=False,
        ),
        provenance="request_bound",
    )
    entry = _diagnostic_catalog()["CSV-NEXT-APPLICABILITY-001"]
    return NotApplicableDecision(
        request=validated_request,
        run_context=context,
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
        known_counts=_decision_known_counts(validated_request),
        decision_context=decision_context,
        publication_context=_publication_context_for_validated_request(
            validated_request,
            context,
            source_seal=_trusted_fixture_source_seal(validated_request, None),
            toolchain=_toolchain_snapshot(node_status="not_applicable"),
            trusted_environment=_trusted_environment_snapshot(),
            source_failure_ledger=(),
            process_launch_descriptor=_process_launch_for_toolchain(
                _toolchain_snapshot(node_status="not_applicable"),
                node_realpath=None,
                node_sha256=None,
                spawn_executable=None,
            ),
        ),
    )


def _validate_model_diagnostics(diagnostics: list[dict[str, Any]]) -> None:
    catalog = _diagnostic_catalog()
    _assert_canonical(diagnostics)
    aggregate_keys: list[Any] = []
    for diagnostic in diagnostics:
        entry = catalog.get(diagnostic["code"])
        assert entry is not None
        for attribute_name in ("severity", "recoverable", "outcome", "ref_permission"):
            assert diagnostic[attribute_name] == entry[attribute_name]
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
        for attribute_name in ("severity", "recoverable", "outcome", "ref_permission"):
            assert diagnostic[attribute_name] == entry[attribute_name]
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
    assert value["projects"] == sorted(value["projects"], key=lambda item: item["id"])
    entities = value["entities"]
    model = {
        "schema": "code-structure-viz.next-model/v1",
        "projects": value["projects"],
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
        for project in sorted(
            value["projects"], key=lambda item: canonical_json_bytes(item["root"])
        )
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
        assert project["source_roots"] == sorted(project["source_roots"], key=_path_sort_key)
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
        declaration_key = component["declaration_key"]
        assert declaration_key == "@anonymous-default" or is_binding_identifier(declaration_key)
        _assert_canonical(component["recognition_evidence"])
    component_keys = [
        (component["module_id"], component["declaration_key"])
        for component in component_records.values()
    ]
    _assert_unique(component_keys)
    anonymous_defaults = [key for key in component_keys if key[1] == "@anonymous-default"]
    assert len(anonymous_defaults) == len({(module_id,) for module_id, _key in anonymous_defaults})

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
    assert roots == sorted(roots, key=lambda item: _path_sort_key(item[0]))
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
            for syntax_field in ("syntax_identity", "byte_start", "byte_end"):
                if syntax_field in edge:
                    witness[syntax_field] = edge[syntax_field]
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
                observation["exported_name"], allow_default=True, allow_keyword=True
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
            if observation["expanded_exported_name"] is not None:
                assert _is_export_identifier(
                    observation["expanded_exported_name"],
                    allow_default=True,
                    allow_keyword=True,
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
            assert "reason" not in resolution
            assert resolution["record_ids"]
            assert resolution["record_ids"] == sorted(resolution["record_ids"])
            assert set(resolution["record_ids"]) <= all_discovered
            assert set(resolution["record_ids"]) <= set().union(*published.values())
        else:
            assert resolution["reason"] in TARGET_FAILURE_REASONS
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
    proof_reason_by_target = {
        item["target_key"]: item.get("reason")
        for item in proof["target_resolutions"]
        if item["status"] == "failed"
    }
    coverage_reason_by_target = {
        item["target_key"]: item.get("reason")
        for item in model["coverage"]["target_completeness"]
        if item["status"] == "failed"
    }
    assert coverage_reason_by_target == proof_reason_by_target

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


def _canonical_json_line(value: Any) -> bytes:
    """Encode a summary/manifest selector with the canonical LF terminator."""

    return canonical_json_bytes(value) + b"\n"


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
    if selector is None:
        assert stdout_result["availability"] is False
        assert stdout_result["stable_reason"] == "run_summary"
        assert stdout_result["run_status"] == run_status
        assert stdout_result["artifact"] is None
        assert stdout_bytes == _canonical_json_line(summary)
        return
    if selector == "manifest":
        assert stdout_result["availability"] is True
        assert stdout_result["stable_reason"] == "run_manifest"
        assert stdout_result["domain_status"] == run_status
        manifest_bytes = _canonical_json_line(manifest)
        assert stdout_result["artifact"]["path"] == "run-manifest.json"
        assert stdout_result["artifact"]["size_bytes"] == len(manifest_bytes)
        assert stdout_result["artifact"]["sha256"] == hashlib.sha256(manifest_bytes).hexdigest()
        assert stdout_bytes == manifest_bytes
        return
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
    root_projects = sorted((project["root"] for project in domain["projects"]), key=_path_sort_key)
    assert manifest["command"] == {
        "name": "snapshot",
        "domain": "next",
        "formats": domain["formats"],
        "stdout_selector": domain["run_context"]["stdout_selector"],
    }
    assert manifest["source"] == domain["source"]
    if domain.get("request_independent") is True:
        # Config/project/source discovery can fail before a validated adapter
        # request exists.  This branch is deliberately null/empty and must
        # never be populated from a default fixture.
        assert manifest.get("request_independent") is True
        assert manifest["request"] is None
        assert manifest["next_request"] is None
        assert manifest["next_config"] == domain["config"]
        assert manifest["domains"] == [domain]
        assert manifest["diagnostics"] == domain["diagnostics"]
        assert manifest["config"]["resolved"] == {
            "next": {
                "request_independent": True,
                "projects": [],
                "targets": domain["targets"],
                "formats": domain["formats"],
                "trusted_environment_digest": None,
            },
            "traversal": {"upstream_depth": None, "downstream_depth": None},
            "limits": None,
        }
        assert manifest["config"]["sha256"] == digest(_without(manifest["config"], "sha256"))
        assert manifest["run"] == {
            "status": domain["status"],
            "exit_code": 3,
            "fingerprint": domain["run_fingerprint"],
            "run_context": domain["run_context"],
        }
        assert manifest["artifacts"] == []
        validate_published_projection(domain, published_bytes)
        return
    assert manifest.get("request_independent", False) is False
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
    publication_boundary = getattr(domain, "publication_boundary", None)
    selected_copy_failed = (
        isinstance(publication_boundary, PublicationBoundaryDecision)
        and publication_boundary.publication_outcome == "selected_artifact_unavailable"
    )
    expected_status = "incomplete" if selected_copy_failed else domain["status"]
    expected_exit = (
        publication_boundary.exit_code
        if isinstance(publication_boundary, PublicationBoundaryDecision)
        else 0
        if domain["status"] in {"complete", "not_applicable"}
        else 3
    )
    assert manifest["run"] == {
        "status": expected_status,
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
