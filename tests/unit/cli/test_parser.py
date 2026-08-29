import json
from pathlib import Path

import pytest

from code_structure_viz.application.snapshot_domain import snapshot_adapter_for
from code_structure_viz.cli.main import main
from code_structure_viz.cli.parser import (
    CliUsageError,
    DomainFormatSelector,
    parse_cli,
    parse_diff_cli,
)
from code_structure_viz.core.domains import DIFF_DOMAINS, SNAPSHOT_DOMAINS
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


def test_closed_domain_vocabulary_dispatches_both_snapshot_adapters() -> None:
    assert SNAPSHOT_DOMAINS == ("python", "sqlalchemy")
    assert DIFF_DOMAINS == ("python",)
    assert snapshot_adapter_for("python").contract.domain == "python"
    assert snapshot_adapter_for("sqlalchemy").contract.domain == "sqlalchemy"


def test_snapshot_accepts_sqlalchemy_domain_and_domain_matching_stdout_selector() -> None:
    request = parse_cli(
        [
            "snapshot",
            "--repo",
            ".",
            "--output-dir",
            "../output",
            "--domain",
            "sqlalchemy",
            "--format",
            "semantic-json",
            "--stdout",
            "sqlalchemy:semantic-json",
        ]
    )

    assert request.domain == "sqlalchemy"
    assert request.stdout_selector == DomainFormatSelector(
        domain="sqlalchemy", format="semantic-json"
    )


@pytest.mark.parametrize(
    ("domain", "selector"),
    [
        ("python", "sqlalchemy:semantic-json"),
        ("sqlalchemy", "python:semantic-json"),
        ("sqlalchemy", "next:semantic-json"),
    ],
)
def test_snapshot_rejects_cross_domain_stdout_selector(domain: str, selector: str) -> None:
    with pytest.raises(CliUsageError) as caught:
        parse_cli(
            [
                "snapshot",
                "--repo",
                ".",
                "--output-dir",
                "../output",
                "--domain",
                domain,
                "--stdout",
                selector,
            ]
        )

    assert caught.value.diagnostic.code.value == "CSV-USAGE-005"


def test_diff_remains_python_only() -> None:
    with pytest.raises(CliUsageError) as caught:
        parse_diff_cli(
            [
                "diff",
                "--repo",
                ".",
                "--output-dir",
                "../output",
                "--domain",
                "sqlalchemy",
            ]
        )

    assert caught.value.diagnostic.code.value == "CSV-USAGE-001"


def test_diff_resolves_closed_endpoint_and_output_format_grammar() -> None:
    request = parse_diff_cli(
        [
            "diff",
            "--repo",
            ".",
            "--output-dir",
            "../output",
            "--domain",
            "python",
            "--from",
            "origin/main",
            "--to",
            "head",
            "--max-changed-paths",
            "42",
            "--format",
            "plantuml",
            "--stdout",
            "python:plantuml",
        ]
    )

    assert request.from_ref == "origin/main"
    assert request.to_ref == "head"
    assert request.max_changed_paths_override == 42
    assert request.formats == ("plantuml",)
    assert request.stdout_selector == DomainFormatSelector(domain="python", format="plantuml")


@pytest.mark.parametrize(
    "extra",
    [
        ["--from", "working-tree"],
        ["--stdout", "python:semantic-json", "--stdout", "manifest"],
        ["--max-changed-paths", "0"],
        ["--format", "semantic-json", "--stdout", "python:plantuml"],
    ],
)
def test_diff_rejects_invalid_endpoint_budget_or_selector_before_execution(
    extra: list[str],
) -> None:
    with pytest.raises(CliUsageError):
        parse_diff_cli(
            [
                "diff",
                "--repo",
                ".",
                "--output-dir",
                "../output",
                "--domain",
                "python",
                *extra,
            ]
        )


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


def test_cli_paths_keep_lexical_symlink_identity_for_boundary_validation(
    tmp_path: Path,
) -> None:
    real_parent = tmp_path / "real"
    real_parent.mkdir()
    linked_parent = tmp_path / "linked"
    linked_parent.symlink_to(real_parent, target_is_directory=True)
    config = linked_parent / "config.toml"

    request = parse_cli(
        [
            "snapshot",
            "--repo",
            str(linked_parent / "repo"),
            "--output-dir",
            str(linked_parent / "output"),
            "--domain",
            "python",
            "--config",
            str(config),
        ]
    )

    assert request.repo == linked_parent / "repo"
    assert request.output_dir == linked_parent / "output"
    assert request.config_path == config


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


def test_arbitrarily_long_decimal_is_parsed_without_conversion_exception() -> None:
    request = parse_cli(
        [
            "snapshot",
            "--repo",
            ".",
            "--output-dir",
            "../output",
            "--domain",
            "python",
            "--max-entities",
            "9" * 10_000,
        ]
    )

    assert request.max_entities_override is not None
    assert request.max_entities_override.bit_length() > 30_000


@pytest.mark.parametrize(
    ("extra", "code", "message"),
    [
        (
            ["--repo", ".", "--unknown", "value"],
            "CSV-USAGE-001",
            "Command line does not match the snapshot v1 grammar.",
        ),
        (
            ["--from", "HEAD", "--repo", "."],
            "CSV-USAGE-002",
            "Single-value option '--repo' was specified more than once.",
        ),
        (
            ["--stdout", "invalid", "--to", "HEAD"],
            "CSV-USAGE-003",
            "Snapshot does not accept diff-only option '--to'.",
        ),
        (
            [
                "--format",
                "plantuml",
                "--stdout",
                "python:semantic-json",
                "--stdout",
                "invalid",
            ],
            "CSV-USAGE-002",
            "Single-value option '--stdout' was specified more than once.",
        ),
    ],
)
def test_usage_diagnostics_follow_closed_phase_priority_across_mixed_argv(
    extra: list[str], code: str, message: str
) -> None:
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
                *extra,
            ]
        )

    assert caught.value.diagnostic.code.value == code
    assert caught.value.diagnostic.message == message


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


def test_help_names_both_snapshot_domains_without_advertising_sqlalchemy_diff(
    capsysbinary: pytest.CaptureFixture[bytes],
) -> None:
    exit_code = main(["--help"])

    captured = capsysbinary.readouterr()
    assert exit_code == 0
    assert b"--domain python|sqlalchemy" in captured.out
    assert b"Python or SQLAlchemy working-tree structure snapshot" in captured.out
    assert b"diff" not in captured.out
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


def test_surrogateescaped_target_is_a_canonical_usage_error_without_traceback(
    capsysbinary: pytest.CaptureFixture[bytes],
) -> None:
    surrogateescaped = chr(0xDCFF)

    exit_code = main(
        [
            "snapshot",
            "--repo",
            ".",
            "--output-dir",
            "../output",
            "--domain",
            "python",
            "--target",
            f"path:src/{surrogateescaped}.py",
        ]
    )

    captured = capsysbinary.readouterr()
    assert exit_code == 2
    assert captured.out == b""
    assert json.loads(captured.err) == {
        "type": "diagnostic",
        "schema": "code-structure-viz.diagnostic/v1",
        "code": "CSV-USAGE-001",
        "severity": "error",
        "domain": None,
        "path": None,
        "symbol": None,
        "line": None,
        "recoverable": False,
        "message": "Command line does not match the snapshot v1 grammar.",
    }
    assert b"Traceback" not in captured.err
