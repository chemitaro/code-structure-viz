from pathlib import Path

from code_structure_viz.artifacts.streams import StderrEmitter, StdoutEmitter
from code_structure_viz.cli.parser import DomainFormatSelector, ManifestSelector
from code_structure_viz.core.diagnostics import DiagnosticCode, diagnostic
from code_structure_viz.core.outcomes import DomainOutcome, RunOutcome


def test_no_selector_emits_exact_committed_summary() -> None:
    outcome = RunOutcome.completed(
        (DomainOutcome.complete(object()),),
        manifest_relative_path="run-manifest.json",
    )

    assert StdoutEmitter().render(outcome, None, Path("/unused")) == (
        b'{"type":"run_summary","schema":"code-structure-viz.run-summary/v1",'
        b'"run_status":"complete","exit_code":0,"domains":'
        b'[{"domain":"python","status":"complete"}],'
        b'"manifest":"run-manifest.json"}\n'
    )


def test_available_selector_copies_final_artifact_exactly(tmp_path: Path) -> None:
    payload = b"@startuml\n@enduml\n"
    (tmp_path / "python.snapshot.puml").write_bytes(payload)
    outcome = RunOutcome.completed(
        (DomainOutcome.complete(object(), artifact_paths=("python.snapshot.puml",)),),
        manifest_relative_path="run-manifest.json",
    )

    assert (
        StdoutEmitter().render(
            outcome,
            DomainFormatSelector("python", "plantuml"),
            tmp_path,
        )
        == payload
    )


def test_unavailable_domain_and_manifest_fatal_use_closed_result_variants(
    tmp_path: Path,
) -> None:
    unavailable = RunOutcome.incomplete(
        (DomainOutcome.payload_unavailable(),),
        manifest_relative_path="run-manifest.json",
    )
    fatal = RunOutcome.fatal((diagnostic(DiagnosticCode.REPO_HEAD),))

    assert StdoutEmitter().render(
        unavailable,
        DomainFormatSelector("python", "semantic-json"),
        tmp_path,
    ) == (
        b'{"type":"stdout_result","schema":"code-structure-viz.stdout-result/v1",'
        b'"selector":"python:semantic-json","availability":false,'
        b'"domain_status":"incomplete","stable_reason":"domain_payload_unavailable",'
        b'"artifact":null}\n'
    )
    assert StdoutEmitter().render(fatal, ManifestSelector(), tmp_path) == (
        b'{"type":"stdout_result","schema":"code-structure-viz.stdout-result/v1",'
        b'"selector":"manifest","availability":false,"run_status":"fatal",'
        b'"stable_reason":"final_manifest_unavailable","artifact":null}\n'
    )


def test_stderr_is_canonical_jsonl_for_domain_and_run_diagnostics() -> None:
    domain_diagnostic = diagnostic(DiagnosticCode.PY_ENTITY_BUDGET, domain="python")
    outcome = RunOutcome.incomplete(
        (DomainOutcome.payload_unavailable(diagnostics=(domain_diagnostic,)),),
        manifest_relative_path="run-manifest.json",
    )

    rendered = StderrEmitter().render(outcome)

    assert rendered.count(b"\n") == 1
    assert b'"code":"CSV-PY-010"' in rendered
    assert b'"domain":"python"' in rendered
