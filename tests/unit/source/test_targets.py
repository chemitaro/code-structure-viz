import unicodedata
from pathlib import PurePosixPath

import pytest

from code_structure_viz.cli.parser import CliUsageError, parse_cli
from code_structure_viz.source.targets import (
    ClassTarget,
    ModuleTarget,
    PathTarget,
    parse_target,
)


def test_parse_target_returns_typed_normalized_values() -> None:
    decomposed = "mo\u0301dulo"

    assert parse_target("path:src/domain/order.py") == PathTarget(
        PurePosixPath("src/domain/order.py")
    )
    assert parse_target(f"module:{decomposed}.order") == ModuleTarget(
        f"{unicodedata.normalize('NFC', decomposed)}.order"
    )
    assert parse_target("class:domain.order.Outer.Inner") == ClassTarget(
        raw="domain.order.Outer.Inner"
    )


@pytest.mark.parametrize(
    "value",
    [
        "",
        "path:/absolute.py",
        "path:../outside.py",
        r"path:src\module.py",
        "path:src/module.pyi",
        "module:bad-name.module",
        "module:pkg..item",
        "class:pkg.module.not-valid",
        "class:pkg.module.",
        "unknown:pkg.item",
    ],
)
def test_parse_target_rejects_values_outside_the_closed_grammar(value: str) -> None:
    with pytest.raises(ValueError):
        parse_target(value)


def test_cli_deduplicates_and_sorts_typed_targets() -> None:
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
            "class:pkg.item.Item",
            "--target",
            "path:src/pkg/item.py",
            "--target",
            "module:pkg.item",
            "--target",
            "module:pkg.item",
        ]
    )

    assert request.targets == (
        PathTarget(PurePosixPath("src/pkg/item.py")),
        ModuleTarget("pkg.item"),
        ClassTarget(raw="pkg.item.Item"),
    )


def test_cli_maps_invalid_target_syntax_to_usage_failure() -> None:
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
                "--target",
                "module:pkg..item",
            ]
        )

    assert caught.value.diagnostic.code.value == "CSV-USAGE-001"
