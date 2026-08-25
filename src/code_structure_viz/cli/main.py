from __future__ import annotations

import signal
import sys
from collections.abc import Mapping, Sequence
from types import FrameType

from code_structure_viz import __version__
from code_structure_viz.application.snapshot import SnapshotApplication
from code_structure_viz.artifacts.streams import StderrEmitter, StdoutEmitter
from code_structure_viz.cli.parser import CliUsageError, parse_cli
from code_structure_viz.core.diagnostics import DiagnosticCode, diagnostic, encode_diagnostic_jsonl

_HELP = b"""usage: code-structure-viz snapshot \\
  --repo PATH --output-dir PATH --domain python [options]

Generate a static Python working-tree structure snapshot.

meta options:
  --help
  --version
"""


def _write_stdout(value: bytes) -> None:
    sys.stdout.buffer.write(value)
    sys.stdout.buffer.flush()


def _write_stderr(value: bytes) -> None:
    sys.stderr.buffer.write(value)
    sys.stderr.buffer.flush()


def main(argv: Sequence[str] | None = None) -> int:
    arguments = tuple(sys.argv[1:] if argv is None else argv)
    if arguments == ("--version",):
        _write_stdout(f"code-structure-viz {__version__}\n".encode("ascii"))
        return 0
    if arguments == ("--help",):
        _write_stdout(_HELP)
        return 0
    try:
        request = parse_cli(arguments)
    except CliUsageError as exc:
        _write_stderr(encode_diagnostic_jsonl((exc.diagnostic,)))
        return 2

    interrupted = False

    def handle_interrupt(_signal_number: int, _frame: FrameType | None) -> None:
        nonlocal interrupted
        interrupted = True

    previous_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, handle_interrupt)
    published_artifacts: Mapping[str, bytes] | None = None

    def bind_artifacts(artifacts: dict[str, bytes]) -> None:
        nonlocal published_artifacts
        published_artifacts = artifacts

    try:
        try:
            outcome = SnapshotApplication(
                cancelled=lambda: interrupted,
                artifacts_bound=bind_artifacts,
            ).run(request)
        except KeyboardInterrupt:
            from code_structure_viz.core.outcomes import RunOutcome

            outcome = RunOutcome.interrupted((diagnostic(DiagnosticCode.INTERRUPTED),))
        except Exception:
            from code_structure_viz.core.outcomes import RunOutcome

            outcome = RunOutcome.fatal((diagnostic(DiagnosticCode.INTERNAL_INVARIANT),))

        _write_stdout(
            StdoutEmitter().render(
                outcome,
                request.stdout_selector,
                request.output_dir,
                published_artifacts=published_artifacts,
            )
        )
        _write_stderr(StderrEmitter().render(outcome))
        return outcome.exit_code
    finally:
        signal.signal(signal.SIGINT, previous_handler)
