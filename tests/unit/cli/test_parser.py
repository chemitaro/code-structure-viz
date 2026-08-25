from pathlib import Path

import pytest

from code_structure_viz.cli.main import main
from code_structure_viz.cli.parser import CliUsageError, DomainFormatSelector, parse_cli
from code_structure_viz.source.targets import ModuleTarget


def test_snapshot_requires_python_domain_and_resolves_default_formats() -> None:
    request = parse_cli(
        [
            "snapshot",
            "--repo",
            ".",
            "--output-dir",
            "../output",
            "--domain",
            "python",
        ]
    )

    assert request.domain == "python"
    assert request.repo == Path.cwd()
    assert request.output_dir == Path.cwd().parent / "output"
    assert request.formats == ("semantic-json", "plantuml")
    assert request.targets == ()


def test_snapshot_canonicalizes_repeatable_formats_and_targets() -> None:
    request = parse_cli(
        [
            "snapshot",
            "--repo",
            ".",
            "--output-dir",
            "../output",
            "--domain",
            "python",
            "--target",
            "module:domain.order",
            "--format",
            "plantuml",
            "--format",
            "semantic-json",
            "--upstream-depth",
            "0",
            "--downstream-depth",
            "2",
            "--max-entities",
            "600",
            "--stdout",
            "python:semantic-json",
        ]
    )

    assert request.formats == ("semantic-json", "plantuml")
    assert request.targets == (ModuleTarget("domain.order"),)
    assert request.upstream_depth_override == 0
    assert request.downstream_depth_override == 2
    assert request.max_entities_override == 600
    assert request.stdout_selector == DomainFormatSelector(domain="python", format="semantic-json")


@pytest.mark.parametrize(
    ("extra", "code", "message"),
    [
        (
            ["--repo", "."],
            "CSV-USAGE-002",
            "Single-value option '--repo' was specified more than once.",
        ),
        (
            ["--from", "HEAD"],
            "CSV-USAGE-003",
            "Snapshot does not accept diff-only option '--from'.",
        ),
        (
            ["--stdout", "PYTHON:semantic-json"],
            "CSV-USAGE-004",
            "Stdout selector is not valid for snapshot v1.",
        ),
    ],
)
def test_snapshot_rejects_closed_grammar_violations(
    extra: list[str], code: str, message: str
) -> None:
    argv = [
        "snapshot",
        "--repo",
        ".",
        "--output-dir",
        "../output",
        "--domain",
        "python",
        *extra,
    ]

    with pytest.raises(CliUsageError) as caught:
        parse_cli(argv)

    assert caught.value.diagnostic.code.value == code
    assert caught.value.diagnostic.message == message


@pytest.mark.parametrize("value", ["0", "-1", "+1", "1.0", "1e2", " 1", "1_0"])
def test_max_entities_accepts_only_positive_ascii_decimal(value: str) -> None:
    with pytest.raises(CliUsageError) as caught:
        parse_cli(
            [
                "snapshot",
                "--repo",
                ".",
                "--output-dir",
                "../output",
                "--domain",
                "python",
                "--max-entities",
                value,
            ]
        )

    assert caught.value.diagnostic.code.value == "CSV-USAGE-001"


def test_stdout_selector_must_name_a_requested_format() -> None:
    with pytest.raises(CliUsageError) as caught:
        parse_cli(
            [
                "snapshot",
                "--repo",
                ".",
                "--output-dir",
                "../output",
                "--domain",
                "python",
                "--format",
                "plantuml",
                "--stdout",
                "python:semantic-json",
            ]
        )

    assert caught.value.diagnostic.code.value == "CSV-USAGE-005"


def test_explicit_depth_requires_a_target() -> None:
    with pytest.raises(CliUsageError) as caught:
        parse_cli(
            [
                "snapshot",
                "--repo",
                ".",
                "--output-dir",
                "../output",
                "--domain",
                "python",
                "--upstream-depth",
                "1",
            ]
        )

    assert caught.value.diagnostic.code.value == "CSV-USAGE-001"


def test_version_is_an_exact_meta_operation_without_diagnostics(
    capsysbinary: pytest.CaptureFixture[bytes],
) -> None:
    exit_code = main(["--version"])

    captured = capsysbinary.readouterr()
    assert exit_code == 0
    assert captured.out == b"code-structure-viz 0.1.0.dev0\n"
    assert captured.err == b""


def test_usage_failure_writes_one_canonical_diagnostic_and_empty_stdout(
    capsysbinary: pytest.CaptureFixture[bytes],
) -> None:
    exit_code = main(["snapshot", "--repo", "."])

    captured = capsysbinary.readouterr()
    assert exit_code == 2
    assert captured.out == b""
    assert captured.err == (
        b'{"type":"diagnostic","schema":"code-structure-viz.diagnostic/v1",'
        b'"code":"CSV-USAGE-001","severity":"error","domain":null,"path":null,'
        b'"symbol":null,"line":null,"recoverable":false,'
        b'"message":"Command line does not match the snapshot v1 grammar."}\n'
    )
