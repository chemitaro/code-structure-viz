from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers.acceptance import (
    CliResult,
    initialize_fixture_repository,
    initialize_repository,
    run_cli,
)


def _published(output: Path) -> dict[str, bytes]:
    return {
        path.relative_to(output).as_posix(): path.read_bytes()
        for path in sorted(output.rglob("*"))
        if path.is_file()
    }


def _assert_same_run(
    first_result: CliResult,
    first_output: Path,
    second_result: CliResult,
    second_output: Path,
) -> None:
    assert second_result == first_result
    assert _published(second_output) == _published(first_output)


@pytest.mark.parametrize(
    ("case", "arguments"),
    [
        ("whole", ()),
        ("whole_mixed_modules", ()),
        ("zero_class", ()),
        ("dynamic_import_ignored", ()),
        ("canonical_model", ()),
        (
            "targeted",
            (
                "--target",
                "class:app.a.A",
                "--upstream-depth",
                "0",
                "--downstream-depth",
                "1",
            ),
        ),
    ],
)
def test_same_request_has_exactly_identical_files_streams_and_exit(
    tmp_path: Path,
    case: str,
    arguments: tuple[str, ...],
) -> None:
    repository = initialize_fixture_repository(tmp_path, case)
    first_output = tmp_path / "first"
    second_output = tmp_path / "second"

    first_result = run_cli(repository, first_output, *arguments)
    second_result = run_cli(repository, second_output, *arguments)

    _assert_same_run(first_result, first_output, second_result, second_output)


def test_target_and_format_argument_order_is_canonical(tmp_path: Path) -> None:
    repository = initialize_fixture_repository(tmp_path, "targeted")
    first_output = tmp_path / "first"
    second_output = tmp_path / "second"

    first_result = run_cli(
        repository,
        first_output,
        "--target",
        "class:app.a.A",
        "--format",
        "plantuml",
        "--target",
        "class:app.c.C",
        "--format",
        "semantic-json",
        "--upstream-depth",
        "1",
        "--downstream-depth",
        "1",
    )
    second_result = run_cli(
        repository,
        second_output,
        "--format",
        "semantic-json",
        "--target",
        "class:app.c.C",
        "--format",
        "plantuml",
        "--target",
        "class:app.a.A",
        "--downstream-depth",
        "1",
        "--upstream-depth",
        "1",
    )

    _assert_same_run(first_result, first_output, second_result, second_output)


def test_file_creation_order_does_not_change_snapshot_bytes(tmp_path: Path) -> None:
    contents = {
        "src/app/a.py": "from app.b import B\nclass A:\n    dependency: B\n",
        "src/app/b.py": "class B:\n    pass\n",
        "src/app/no_classes.py": "import app.b\nVALUE = 1\n",
    }
    repositories: list[Path] = []
    for name, items in (
        ("forward", tuple(contents.items())),
        ("reverse", tuple(reversed(tuple(contents.items())))),
    ):
        repository = tmp_path / name
        for relative, content in items:
            path = repository / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        initialize_repository(repository)
        repositories.append(repository)

    first_output = tmp_path / "first"
    second_output = tmp_path / "second"
    first_result = run_cli(repositories[0], first_output)
    second_result = run_cli(repositories[1], second_output)

    _assert_same_run(first_result, first_output, second_result, second_output)
