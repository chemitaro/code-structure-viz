from __future__ import annotations

import hashlib
import json
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Any

_SCHEMA = "code-structure-viz.next-package-applicability/v1"


class PackageApplicabilityState(StrEnum):
    APPLICABLE = "applicable"
    NON_APPLICABLE = "non_applicable"
    MALFORMED = "malformed"


class PackageApplicabilityEvidence(StrEnum):
    DIRECT_NEXT_DEPENDENCY = "direct_next_dependency"
    NO_DIRECT_NEXT = "no_direct_next"
    MISSING_PACKAGE = "missing_package"
    MALFORMED_PACKAGE = "malformed_package"


@dataclass(frozen=True, slots=True)
class PackageApplicabilityEntry:
    project_root: str
    package_path: str
    state: PackageApplicabilityState
    evidence: PackageApplicabilityEvidence

    def __post_init__(self) -> None:
        _validate_project_root(self.project_root)
        expected_path = (
            "package.json" if self.project_root == "." else f"{self.project_root}/package.json"
        )
        if self.package_path != expected_path:
            raise ValueError("package path must be the selected project's direct package.json")
        try:
            state = PackageApplicabilityState(self.state)
            evidence = PackageApplicabilityEvidence(self.evidence)
        except ValueError as error:
            raise ValueError("package applicability entry is invalid") from error
        expected_evidence = {
            PackageApplicabilityState.APPLICABLE: {
                PackageApplicabilityEvidence.DIRECT_NEXT_DEPENDENCY
            },
            PackageApplicabilityState.NON_APPLICABLE: {
                PackageApplicabilityEvidence.NO_DIRECT_NEXT,
                PackageApplicabilityEvidence.MISSING_PACKAGE,
            },
            PackageApplicabilityState.MALFORMED: {PackageApplicabilityEvidence.MALFORMED_PACKAGE},
        }
        if evidence not in expected_evidence[state]:
            raise ValueError("package applicability evidence does not match its state")
        object.__setattr__(self, "state", state)
        object.__setattr__(self, "evidence", evidence)

    def as_dict(self) -> dict[str, str]:
        return {
            "project_root": self.project_root,
            "package_path": self.package_path,
            "state": self.state.value,
            "evidence": self.evidence.value,
        }


@dataclass(frozen=True, slots=True)
class PackageApplicabilityMatrix:
    entries: tuple[PackageApplicabilityEntry, ...]
    aggregate_state: PackageApplicabilityState
    _observed_package_bytes: tuple[tuple[str, bytes | None], ...] = field(repr=False)

    def __post_init__(self) -> None:
        entries = tuple(self.entries)
        try:
            aggregate_state = PackageApplicabilityState(self.aggregate_state)
        except ValueError as error:
            raise ValueError("package applicability aggregate state is invalid") from error
        if not entries:
            raise ValueError("package applicability requires at least one project")
        roots = tuple(entry.project_root for entry in entries)
        if len(roots) != len(set(roots)):
            raise ValueError("package applicability project roots must be unique")
        if entries != tuple(sorted(entries, key=lambda entry: entry.project_root.encode("utf-8"))):
            raise ValueError("package applicability projects must use canonical path order")
        if aggregate_state is not _aggregate_state(entries):
            raise ValueError("package applicability aggregate state does not match its entries")

        observations = tuple(self._observed_package_bytes)
        expected_paths = tuple(_package_path(root) for root in roots)
        if tuple(path for path, _payload in observations) != expected_paths:
            raise ValueError("package observations must exactly match the project roots")
        if any(
            payload is not None and not isinstance(payload, bytes) for _, payload in observations
        ):
            raise ValueError("package observations must contain frozen bytes or be missing")
        expected_entries = _derive_entries(dict(observations), roots)
        if entries != expected_entries:
            raise ValueError("package applicability must be derived from observed package bytes")

        object.__setattr__(self, "entries", entries)
        object.__setattr__(self, "aggregate_state", aggregate_state)
        object.__setattr__(self, "_observed_package_bytes", observations)

    @property
    def applicable_projects(self) -> tuple[str, ...]:
        return tuple(
            entry.project_root
            for entry in self.entries
            if entry.state is PackageApplicabilityState.APPLICABLE
        )

    @property
    def non_applicable_projects(self) -> tuple[str, ...]:
        return tuple(
            entry.project_root
            for entry in self.entries
            if entry.state is PackageApplicabilityState.NON_APPLICABLE
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": _SCHEMA,
            "version": 1,
            "projects": [entry.as_dict() for entry in self.entries],
            "aggregate_state": self.aggregate_state.value,
            "applicable_projects": list(self.applicable_projects),
            "non_applicable_projects": list(self.non_applicable_projects),
        }

    def observation_value(self) -> dict[str, Any]:
        """Expose safe byte identities without publishing package contents."""

        return {
            "matrix": self.as_dict(),
            "packages": [
                {
                    "path": path,
                    "state": "read" if payload is not None else "missing",
                    "sha256": (
                        hashlib.sha256(payload).hexdigest() if payload is not None else None
                    ),
                    "size_bytes": len(payload) if payload is not None else None,
                    "failure_code": None,
                }
                for path, payload in self._observed_package_bytes
            ],
        }


def _validate_project_root(project_root: str) -> None:
    if not isinstance(project_root, str):
        raise ValueError("project root must be a string")
    try:
        project_root.encode("utf-8", errors="strict")
    except UnicodeEncodeError as error:
        raise ValueError("project root must be valid UTF-8") from error
    if project_root == ".":
        return
    path = PurePosixPath(project_root)
    if (
        not project_root
        or unicodedata.normalize("NFC", project_root) != project_root
        or "\\" in project_root
        or path.is_absolute()
        or path.as_posix() != project_root
        or any(part in {"", ".", ".."} for part in project_root.split("/"))
        or any(ord(character) < 0x20 or ord(character) == 0x7F for character in project_root)
    ):
        raise ValueError("project root must be a canonical repository-relative path")


def _package_path(project_root: str) -> str:
    return "package.json" if project_root == "." else f"{project_root}/package.json"


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate package key")
        value[key] = item
    return value


def _parse_package(payload: bytes) -> dict[str, Any]:
    text = payload.decode("utf-8-sig")
    if text.startswith("\ufeff"):
        raise ValueError("package.json contains multiple byte-order marks")
    value = json.loads(
        text,
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=lambda _constant: (_ for _ in ()).throw(ValueError("non-finite value")),
    )
    if not isinstance(value, dict):
        raise ValueError("package.json root must be an object")
    return value


def _derive_entries(
    package_bytes: Mapping[str, bytes | None], project_roots: tuple[str, ...]
) -> tuple[PackageApplicabilityEntry, ...]:
    entries: list[PackageApplicabilityEntry] = []
    for project_root in sorted(project_roots, key=lambda value: value.encode("utf-8")):
        package_path = _package_path(project_root)
        payload = package_bytes.get(package_path)
        if payload is None:
            entries.append(
                PackageApplicabilityEntry(
                    project_root,
                    package_path,
                    PackageApplicabilityState.NON_APPLICABLE,
                    PackageApplicabilityEvidence.MISSING_PACKAGE,
                )
            )
            continue

        try:
            package = _parse_package(payload)
            direct_versions: list[str] = []
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
                    direct_versions.append(version.strip())
            if len(direct_versions) > 1:
                malformed = True
        except (UnicodeDecodeError, ValueError):
            malformed = True
            direct_versions = []

        state = (
            PackageApplicabilityState.MALFORMED
            if malformed
            else PackageApplicabilityState.APPLICABLE
            if direct_versions
            else PackageApplicabilityState.NON_APPLICABLE
        )
        evidence = {
            PackageApplicabilityState.APPLICABLE: (
                PackageApplicabilityEvidence.DIRECT_NEXT_DEPENDENCY
            ),
            PackageApplicabilityState.NON_APPLICABLE: PackageApplicabilityEvidence.NO_DIRECT_NEXT,
            PackageApplicabilityState.MALFORMED: PackageApplicabilityEvidence.MALFORMED_PACKAGE,
        }[state]
        entries.append(PackageApplicabilityEntry(project_root, package_path, state, evidence))
    return tuple(entries)


def _aggregate_state(
    entries: tuple[PackageApplicabilityEntry, ...],
) -> PackageApplicabilityState:
    if any(entry.state is PackageApplicabilityState.MALFORMED for entry in entries):
        return PackageApplicabilityState.MALFORMED
    if any(entry.state is PackageApplicabilityState.APPLICABLE for entry in entries):
        return PackageApplicabilityState.APPLICABLE
    return PackageApplicabilityState.NON_APPLICABLE


def derive_package_applicability_matrix(
    package_bytes: Mapping[str, bytes], project_roots: tuple[str, ...] | list[str]
) -> PackageApplicabilityMatrix:
    """Derive and retain the direct-Next evidence for selected project roots."""

    roots = tuple(project_roots)
    if not roots:
        raise ValueError("at least one project root is required")
    for project_root in roots:
        _validate_project_root(project_root)
    if len(roots) != len(set(roots)):
        raise ValueError("project roots must be unique")
    frozen_bytes = tuple(
        (_package_path(project_root), package_bytes.get(_package_path(project_root)))
        for project_root in sorted(roots, key=lambda value: value.encode("utf-8"))
    )
    entries = _derive_entries(dict(frozen_bytes), roots)
    return PackageApplicabilityMatrix(
        entries=entries,
        aggregate_state=_aggregate_state(entries),
        _observed_package_bytes=frozen_bytes,
    )
