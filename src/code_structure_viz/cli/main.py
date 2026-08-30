from __future__ import annotations

import signal
import sys
from collections.abc import Callable, Mapping, Sequence
from types import FrameType

from code_structure_viz import __version__
from code_structure_viz.application.diff import DiffApplication
from code_structure_viz.application.snapshot import SnapshotApplication
from code_structure_viz.artifacts.streams import StderrEmitter, StdoutEmitter
from code_structure_viz.cli.parser import (
    CliUsageError,
    DiffCliRequest,
    SnapshotCliRequest,
    parse_cli,
    parse_diff_cli,
)
from code_structure_viz.core.diagnostics import (
    DiagnosticCode,
    diagnostic,
    encode_diagnostic_jsonl,
)
from code_structure_viz.core.outcomes import RunOutcome

_HELP = b"""usage: code-structure-viz snapshot \\
  --repo PATH --output-dir PATH --domain python|sqlalchemy [options]

Generate a static Python or SQLAlchemy working-tree structure snapshot.

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


def _run_application(
    request: SnapshotCliRequest | DiffCliRequest,
    *,
    cancelled: Callable[[], bool],
    artifacts_bound: Callable[[dict[str, bytes]], None],
) -> RunOutcome:
    if isinstance(request, DiffCliRequest):
        return DiffApplication(
            cancelled=cancelled,
            artifacts_bound=artifacts_bound,
        ).run(request)
    return SnapshotApplication(
        cancelled=cancelled,
        artifacts_bound=artifacts_bound,
    ).run(request)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = tuple(sys.argv[1:] if argv is None else argv)
    if arguments == ("--version",):
        _write_stdout(f"code-structure-viz {__version__}\n".encode("ascii"))
        return 0
    if arguments == ("--help",):
        _write_stdout(_HELP)
        return 0
    request: SnapshotCliRequest | DiffCliRequest
    try:
        if arguments and arguments[0] == "diff":
            request = parse_diff_cli(arguments)
        else:
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
            outcome = _run_application(
                request,
                cancelled=lambda: interrupted,
                artifacts_bound=bind_artifacts,
            )
        except KeyboardInterrupt:
            outcome = RunOutcome.interrupted((diagnostic(DiagnosticCode.INTERRUPTED),))
        except Exception:
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
