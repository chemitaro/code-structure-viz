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


def test_next_target_accepts_repository_relative_directory_paths() -> None:
    assert parse_target("path:src/app", domain="next") == PathTarget(PurePosixPath("src/app"))


def test_next_target_accepts_repository_root_sentinel() -> None:
    assert parse_target("path:.", domain="next") == PathTarget(PurePosixPath("."))


def test_next_target_rejects_fragment_like_hashes_from_the_shared_path_grammar() -> None:
    with pytest.raises(ValueError):
        parse_target("path:src/app#section", domain="next")


@pytest.mark.parametrize("character", ["\x00", "\x1f", "\x7f"])
def test_next_target_rejects_ascii_controls_from_the_shared_path_grammar(
    character: str,
) -> None:
    with pytest.raises(ValueError):
        parse_target(f"path:src/{character}app", domain="next")


def test_next_target_enforces_the_inclusive_4096_utf8_byte_limit() -> None:
    with pytest.raises(ValueError):
        parse_target(f"path:{'a' * 4097}", domain="next")


def test_next_target_accepts_a_path_exactly_4096_utf8_bytes_long() -> None:
    target = parse_target(f"path:{'a' * 4096}", domain="next")
    assert isinstance(target, PathTarget)
    assert len(target.value.as_posix().encode("utf-8")) == 4096


@pytest.mark.parametrize("value", ["module:src.app", "class:src.app.Page"])
def test_next_target_rejects_python_module_and_class_selectors(value: str) -> None:
    with pytest.raises(ValueError):
        parse_target(value, domain="next")


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
