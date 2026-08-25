from __future__ import annotations

import argparse
import tempfile
from dataclasses import dataclass
from pathlib import Path

from tests.helpers.acceptance import initialize_fixture_repository, run_cli

ROOT = Path(__file__).resolve().parents[2]
GOLDEN_CASES = (
    "whole",
    "whole_mixed_modules",
    "zero_class",
    "dynamic_import_ignored",
    "canonical_model",
    "annotation_references",
    "module_only",
    "targeted",
    "partial_safe",
)


@dataclass(frozen=True, slots=True)
class GoldenRequest:
    targets: tuple[str, ...]
    upstream_depth: int
    downstream_depth: int


_REQUESTS = {
    "whole": GoldenRequest((), 1, 1),
    "whole_mixed_modules": GoldenRequest((), 1, 1),
    "zero_class": GoldenRequest((), 1, 1),
    "dynamic_import_ignored": GoldenRequest((), 1, 1),
    "canonical_model": GoldenRequest((), 1, 1),
    "annotation_references": GoldenRequest((), 1, 1),
    "module_only": GoldenRequest(("module:app.a",), 0, 1),
    "targeted": GoldenRequest(("class:app.a.A",), 0, 1),
    "partial_safe": GoldenRequest(("module:app.good",), 1, 1),
}


def render_case(case: str) -> dict[str, bytes]:
    if case not in GOLDEN_CASES:
        raise ValueError("golden case is not in the closed allowlist")
    request = _REQUESTS[case]
    with tempfile.TemporaryDirectory(prefix="code-structure-viz-golden-") as directory:
        temporary = Path(directory)
        repository = initialize_fixture_repository(temporary, case)
        output = temporary / "output"
        arguments = tuple(value for target in request.targets for value in ("--target", target))
        if request.targets:
            arguments += (
                "--upstream-depth",
                str(request.upstream_depth),
                "--downstream-depth",
                str(request.downstream_depth),
            )
        result = run_cli(repository, output, *arguments)
        published_names = tuple(
            sorted(
                (path.name for path in output.iterdir() if path.is_file()),
                key=lambda value: value.encode("utf-8"),
            )
        )
        rendered = {name: (output / name).read_bytes() for name in published_names}
        rendered.update(
            {
                "stdout.run-summary.jsonl": result.stdout,
                "stderr.jsonl": result.stderr,
                "published-files.txt": b"".join(
                    name.encode("utf-8") + b"\n" for name in published_names
                ),
                "exit-code.txt": f"{result.returncode}\n".encode("ascii"),
            }
        )
        return rendered


def _main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--update-golden", choices=GOLDEN_CASES, required=True)
    arguments = parser.parse_args()
    destination = ROOT / "tests" / "golden" / "python_snapshot" / arguments.update_golden
    destination.mkdir(parents=True, exist_ok=True)
    for name, content in render_case(arguments.update_golden).items():
        (destination / name).write_bytes(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
