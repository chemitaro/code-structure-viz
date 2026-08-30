import pytest

from code_structure_viz.core.outcomes import (
    DomainOutcome,
    DomainStatus,
    IncompleteKind,
    RunOutcome,
    RunStatus,
)


@pytest.mark.parametrize(
    "kwargs",
    [
        {
            "domain": "python",
            "status": DomainStatus.NOT_APPLICABLE,
            "incomplete_kind": None,
            "payload_available": True,
            "payload": object(),
            "artifact_paths": (),
        },
        {
            "domain": "python",
            "status": DomainStatus.INCOMPLETE,
            "incomplete_kind": None,
            "payload_available": False,
            "payload": None,
            "artifact_paths": (),
        },
        {
            "domain": "python",
            "status": DomainStatus.INCOMPLETE,
            "incomplete_kind": IncompleteKind.PARTIAL_SAFE,
            "payload_available": False,
            "payload": None,
            "artifact_paths": (),
        },
        {
            "domain": "python",
            "status": DomainStatus.INCOMPLETE,
            "incomplete_kind": IncompleteKind.PAYLOAD_UNAVAILABLE,
            "payload_available": False,
            "payload": None,
            "artifact_paths": ("python.snapshot.semantic.json",),
        },
    ],
)
def test_domain_outcome_rejects_impossible_payload_combinations(
    kwargs: dict[str, object],
) -> None:
    with pytest.raises(ValueError):
        DomainOutcome(**kwargs)  # type: ignore[arg-type]


def test_domain_outcome_constructors_create_closed_variants() -> None:
    payload = object()

    complete = DomainOutcome.complete(payload, domain="python")
    not_applicable = DomainOutcome.not_applicable(domain="python")
    partial = DomainOutcome.partial_safe(payload, domain="python")
    unavailable = DomainOutcome.payload_unavailable(domain="python")

    assert (complete.status, complete.payload_available) == (DomainStatus.COMPLETE, True)
    assert (not_applicable.status, not_applicable.payload_available) == (
        DomainStatus.NOT_APPLICABLE,
        False,
    )
    assert partial.incomplete_kind is IncompleteKind.PARTIAL_SAFE
    assert unavailable.incomplete_kind is IncompleteKind.PAYLOAD_UNAVAILABLE


def test_sqlalchemy_domain_accepts_only_its_snapshot_and_diff_paths() -> None:
    outcome = DomainOutcome.complete(
        object(),
        domain="sqlalchemy",
        artifact_paths=(
            "sqlalchemy.diff.semantic.json",
            "sqlalchemy.diff.puml",
        ),
    )

    assert outcome.artifact_paths == (
        "sqlalchemy.diff.semantic.json",
        "sqlalchemy.diff.puml",
    )


@pytest.mark.parametrize(
    ("domain", "artifact_path"),
    [
        ("python", "sqlalchemy.snapshot.semantic.json"),
        ("sqlalchemy", "python.snapshot.semantic.json"),
    ],
)
def test_domain_outcome_rejects_cross_domain_artifact_paths(
    domain: str, artifact_path: str
) -> None:
    with pytest.raises(ValueError):
        DomainOutcome.complete(
            object(),
            domain=domain,  # type: ignore[arg-type]
            artifact_paths=(artifact_path,),
        )


def test_run_outcome_maps_status_to_exact_exit_and_manifest_contract() -> None:
    complete = RunOutcome.completed(
        (DomainOutcome.complete(object(), domain="python"),),
        manifest_relative_path="run-manifest.json",
    )
    incomplete = RunOutcome.incomplete(
        (DomainOutcome.payload_unavailable(domain="python"),),
        manifest_relative_path="run-manifest.json",
    )
    fatal = RunOutcome.fatal()
    usage = RunOutcome.usage()
    interrupted = RunOutcome.interrupted()

    assert (complete.status, complete.exit_code, complete.manifest_relative_path) == (
        RunStatus.COMPLETE,
        0,
        "run-manifest.json",
    )
    assert (incomplete.status, incomplete.exit_code) == (RunStatus.INCOMPLETE, 3)
    assert (fatal.status, fatal.exit_code, fatal.manifest_relative_path) == (
        RunStatus.FATAL,
        1,
        None,
    )
    assert usage.exit_code == 2
    assert interrupted.exit_code == 130


def test_run_fatal_cannot_carry_a_manifest() -> None:
    with pytest.raises(ValueError):
        RunOutcome(
            status=RunStatus.FATAL,
            exit_code=1,
            domains=(),
            manifest_relative_path="run-manifest.json",
        )
