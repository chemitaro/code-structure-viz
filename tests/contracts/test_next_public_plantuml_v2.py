"""A fixed worked literal and independent grammar protect retained PlantUML."""

import hashlib
import json
from copy import copy
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Literal, cast

import pytest
from jsonschema import ValidationError  # type: ignore[import-untyped]

from tests.contracts import next_public_artifact_v2_reference as leaf_reference
from tests.contracts import next_runtime_v2_reference as runtime_reference
from tests.contracts.next_public_artifact_v2_validation import validate_public_plantuml_artifact_v2
from tests.contracts.next_publication_candidates_v2_fixtures import (
    independent_record_id,
    unavailable_core_run,
)
from tests.contracts.test_next_core_failure_v2 import runtime_for_core_wire
from tests.contracts.test_next_provenance_v2 import complete_core_runtime
from tests.contracts.test_next_public_semantic_v2 import CARD_COMPONENT_ID
from tests.contracts.test_next_semantic_candidate_v2 import (
    CARD_MODULE_ID,
    COLLECTIONS,
    core_inputs,
    update_model_digest,
)

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def complete_plantuml(
    tmp_path_factory: pytest.TempPathFactory,
) -> leaf_reference.RetainedPublicPlantumlArtifactV2:
    _, core = complete_core_runtime(tmp_path_factory.mktemp("plantuml-known"))
    return leaf_reference.retain_public_plantuml_artifact_v2(core)


def rehashed_plantuml(
    original: leaf_reference.RetainedPublicPlantumlArtifactV2, wire: bytes
) -> leaf_reference.RetainedPublicPlantumlArtifactV2:
    """Malformed cached owner as conformance input, not a public mutation API."""

    bad = copy(original)
    descriptor = original.descriptor()
    descriptor.update(size_bytes=len(wire), sha256=hashlib.sha256(wire).hexdigest())
    object.__setattr__(bad, "_wire_bytes", wire)
    object.__setattr__(bad, "_descriptor_bytes", json.dumps(descriptor).encode())
    return bad


def test_plantuml_leaf_retains_the_same_core_and_worked_literal(tmp_path: Path) -> None:
    _, core = complete_core_runtime(tmp_path)

    from tests.contracts.next_public_artifact_v2_reference import retain_public_plantuml_artifact_v2

    artifact = retain_public_plantuml_artifact_v2(core)
    literal = (ROOT / "tests/fixtures/next_runtime_v2/public-plantuml-card.puml").read_bytes()
    assert (len(literal), literal.count(b"\n"), hashlib.sha256(literal).hexdigest()) == (
        1082,
        24,
        "0bce98e4e12b722ff2685a76c52bddba7bca735af090ad735d94bbfc9e50c2a9",
    )
    assert artifact.semantic_decision() is core
    assert artifact.wire_bytes() == literal
    assert artifact.descriptor() == {
        "path": "next.snapshot.puml",
        "domain": "next",
        "format": "plantuml",
        "media_type": "text/vnd.plantuml; charset=utf-8",
        "size_bytes": 1082,
        "sha256": "0bce98e4e12b722ff2685a76c52bddba7bca735af090ad735d94bbfc9e50c2a9",
    }


@pytest.mark.parametrize(
    "mutation",
    [
        "bom",
        "crlf",
        "no_lf",
        "extra_lf",
        "blank",
        "comment",
        "unicode_separator",
        "marker",
        "relation",
        "order",
        "extra",
        "label",
        "invalid_utf8",
    ],
)
def test_rehashing_changed_encoding_or_grammar_cannot_certify_plantuml(
    complete_plantuml: leaf_reference.RetainedPublicPlantumlArtifactV2, mutation: str
) -> None:
    wire = complete_plantuml.wire_bytes()
    lines = wire.splitlines(keepends=True)
    if mutation == "bom":
        changed = b"\xef\xbb\xbf" + wire
    elif mutation == "crlf":
        changed = wire.replace(b"\n", b"\r\n")
    elif mutation == "no_lf":
        changed = wire[:-1]
    elif mutation == "extra_lf":
        changed = wire + b"\n"
    elif mutation == "blank":
        changed = wire.replace(b"legend\n", b"legend\n\n", 1)
    elif mutation == "comment":
        changed = wire.replace(b"@enduml\n", b"'private comment\n@enduml\n")
    elif mutation == "unicode_separator":
        changed = wire.replace(b"\n", "\u2028".encode(), 1)
    elif mutation == "marker":
        changed = b"".join(
            line for line in lines if not line.startswith(b"N_M_") or b"marker=" not in line
        )
    elif mutation == "relation":
        changed = b"".join(line for line in lines if not line.endswith(b" : contains\n"))
    elif mutation == "order":
        lines[-2], lines[-3] = lines[-3], lines[-2]
        changed = b"".join(lines)
    elif mutation == "extra":
        changed = wire.replace(b"@enduml\n", b"note top: extra\n@enduml\n")
    elif mutation == "label":
        changed = wire.replace(b"M:src/Card.tsx", b"M:src/Other.tsx")
    else:
        changed = wire + b"\xff"
    bad = rehashed_plantuml(complete_plantuml, changed)
    with pytest.raises((ValueError, AssertionError, IndexError)):
        validate_public_plantuml_artifact_v2(bad, complete_plantuml.semantic_decision())


@pytest.mark.parametrize("value", [1082.0, True])
def test_plantuml_descriptor_preserves_integer_type(
    complete_plantuml: leaf_reference.RetainedPublicPlantumlArtifactV2, value: object
) -> None:
    bad = copy(complete_plantuml)
    descriptor = bad.descriptor()
    descriptor["size_bytes"] = value
    object.__setattr__(bad, "_descriptor_bytes", json.dumps(descriptor).encode())
    with pytest.raises((ValueError, ValidationError)):
        validate_public_plantuml_artifact_v2(bad, bad.semantic_decision())


def test_missing_prop_facet_is_rejected_after_a_valid_same_core_leaf(tmp_path: Path) -> None:
    # A source-bound reference corpus, not evidence of actual TS component recognition.
    seal, assets, request, policy, wire = core_inputs(tmp_path)
    model = wire["semantic_payload"]["model"]
    model["components"] = [
        {
            "kind": "component",
            "id": CARD_COMPONENT_ID,
            "module_id": CARD_MODULE_ID,
            "declaration_key": "Card",
            "recognition_evidence": ["trusted_callable"],
            "props_state": "known",
        }
    ]
    model["members"] = [
        {
            "kind": "prop",
            "owner_id": CARD_COMPONENT_ID,
            "name": "title",
            "id": independent_record_id(
                "prop", {"owner_id": CARD_COMPONENT_ID, "name": "title"}, "member"
            ),
            "type_node": {"kind": "primitive", "name": "string"},
            "optional": False,
            "readonly": True,
            "default_evidence": "none",
        }
    ]
    counts = {name: len(model[name]) for name in COLLECTIONS}
    model["coverage"]["counts"].update(
        **counts,
        internal_entities=2,
        published=sum(counts.values()),
        discovered=sum(counts.values()),
    )
    wire["semantic_payload"]["proof"]["discovered_records"] = [
        {"collection": name, "record_id": row["id"], "taints": []}
        for name in COLLECTIONS
        for row in model[name]
    ]
    update_model_digest(wire)
    runtime = runtime_for_core_wire(seal, assets, request, policy, wire)
    candidate = runtime.transport_candidate()
    assert candidate is not None
    core = runtime_reference.decide_semantic_candidate_v2(candidate, seal, assets)
    leaf = leaf_reference.retain_public_plantuml_artifact_v2(core)
    validate_public_plantuml_artifact_v2(leaf, core)
    assert b"|optional=false|readonly=true|default=none" in leaf.wire_bytes()
    bad = rehashed_plantuml(leaf, leaf.wire_bytes().replace(b"|readonly=true", b"", 1))
    with pytest.raises((ValueError, AssertionError)):
        validate_public_plantuml_artifact_v2(bad, core)


def test_plantuml_leaf_is_nominal_frozen_private_and_same_core_only(
    complete_plantuml: leaf_reference.RetainedPublicPlantumlArtifactV2,
) -> None:
    leaf = complete_plantuml
    with pytest.raises(TypeError):
        leaf_reference.RetainedPublicPlantumlArtifactV2(leaf.semantic_decision(), leaf.wire_bytes())
    with pytest.raises(FrozenInstanceError):
        cast(Any, leaf)._wire_bytes = b"private"
    assert repr(leaf) == "RetainedPublicPlantumlArtifactV2()"
    descriptor = leaf.descriptor()
    descriptor["sha256"] = "0" * 64
    assert leaf.descriptor()["sha256"] != "0" * 64
    core = leaf.semantic_decision()
    foreign = runtime_reference.decide_semantic_candidate_v2(
        core.transport_candidate(), core.source_seal(), core.execution_assets()
    )
    with pytest.raises(ValueError, match="retained Core owner"):
        validate_public_plantuml_artifact_v2(leaf, foreign)
    with pytest.raises(TypeError):
        validate_public_plantuml_artifact_v2(cast(Any, SimpleNamespace()), core)


@pytest.mark.parametrize("branch", ["target", "export", "entity", "rejected"])
def test_unavailable_or_rejected_core_cannot_create_plantuml_leaf(
    tmp_path: Path, branch: Literal["target", "export", "entity", "rejected"]
) -> None:
    run = unavailable_core_run(tmp_path, branch)
    with pytest.raises((TypeError, ValueError)):
        leaf_reference.retain_public_plantuml_artifact_v2(cast(Any, run.semantic_decision()))
