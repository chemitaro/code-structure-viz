from __future__ import annotations

import hashlib
from collections.abc import Iterable

from code_structure_viz.adapters.python.model import PythonClassEntity, PythonMember
from code_structure_viz.semantic.canonical_json import encode_canonical_json


class PythonMoveMatcher:
    """Match only unique classes with an exact, safe structural fingerprint."""

    def match(
        self,
        before: Iterable[PythonClassEntity],
        after: Iterable[PythonClassEntity],
        before_members: Iterable[PythonMember] = (),
        after_members: Iterable[PythonMember] = (),
    ) -> list[dict[str, object]]:
        before_values = tuple(before)
        after_values = tuple(after)
        before_members_by_owner: dict[str, list[PythonMember]] = {}
        after_members_by_owner: dict[str, list[PythonMember]] = {}
        for member in before_members:
            before_members_by_owner.setdefault(member.owner_id, []).append(member)
        for member in after_members:
            after_members_by_owner.setdefault(member.owner_id, []).append(member)
        before_fingerprints = {
            item.id: _fingerprint(item, before_members_by_owner.get(item.id, ()))
            for item in before_values
        }
        after_fingerprints = {
            item.id: _fingerprint(item, after_members_by_owner.get(item.id, ()))
            for item in after_values
        }
        before_ids = {item.id for item in before_values}
        after_ids = {item.id for item in after_values}
        unmatched_before = tuple(item for item in before_values if item.id not in after_ids)
        unmatched_after = tuple(item for item in after_values if item.id not in before_ids)
        matches: list[dict[str, object]] = []
        for before_item in unmatched_before:
            candidates = [
                after_item
                for after_item in unmatched_after
                if _has_identity_change(before_item, after_item)
                and before_fingerprints[before_item.id] == after_fingerprints[after_item.id]
            ]
            if len(candidates) != 1:
                continue
            candidate = candidates[0]
            competing = [
                item
                for item in unmatched_before
                if item.id != before_item.id
                and before_fingerprints[item.id] == after_fingerprints[candidate.id]
            ]
            if competing:
                continue
            matches.append(
                {
                    "before_id": before_item.id,
                    "after_id": candidate.id,
                    "reason": "unique-structural-fingerprint",
                    "fingerprint": before_fingerprints[before_item.id],
                }
            )
        return sorted(matches, key=lambda item: str(item["after_id"]).encode("utf-8"))

    def find_matches(
        self,
        before: Iterable[PythonClassEntity],
        after: Iterable[PythonClassEntity],
        before_members: Iterable[PythonMember] = (),
        after_members: Iterable[PythonMember] = (),
    ) -> tuple[dict[str, object], ...]:
        return tuple(self.match(before, after, before_members, after_members))


def _fingerprint(entity: PythonClassEntity, members: Iterable[PythonMember]) -> str:
    value = {
        "kind": entity.kind,
        "decorators": [(item.name, item.called) for item in entity.decorators],
        "members": sorted(
            (_member_fingerprint(item) for item in members),
            key=lambda item: encode_canonical_json(item),
        ),
    }
    return hashlib.sha256(encode_canonical_json(value)).hexdigest()


def _has_identity_change(before: PythonClassEntity, after: PythonClassEntity) -> bool:
    """Require evidence that a structurally equal class changed identity."""
    return (
        before.module != after.module
        or before.qualified_name != after.qualified_name
        or before.name != after.name
        or before.path != after.path
    )


def _member_fingerprint(member: PythonMember) -> dict[str, object]:
    signature = None
    if member.signature is not None:
        signature = {
            "async": member.signature.async_,
            "parameters": [
                (item.name, item.kind.value, item.annotation, item.has_default)
                for item in member.signature.parameters
            ],
            "returns": member.signature.returns,
        }
    return {
        "kind": member.kind.value,
        "name": member.name,
        "scope": member.scope.value if member.scope else None,
        "property_role": member.property_role.value if member.property_role else None,
        "method_kind": member.method_kind.value if member.method_kind else None,
        "annotation": member.annotation,
        "signature": signature,
        "decorators": [(item.name, item.called) for item in member.decorators],
        "declaration_ordinal": member.declaration_ordinal,
    }


__all__ = ["PythonMoveMatcher"]
