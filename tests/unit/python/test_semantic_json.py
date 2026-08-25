from pathlib import PurePosixPath

from code_structure_viz.adapters.python.model import (
    CoverageFrontier,
    FailedSourceFile,
    FailedStage,
    FrontierDirection,
    FrontierKind,
    FrontierReason,
    PythonCoverage,
    PythonSnapshot,
)
from code_structure_viz.adapters.python.semantic_json import (
    PythonSemanticJsonRenderer,
    render_semantic_snapshot,
)
from code_structure_viz.core.diagnostics import DiagnosticCode, diagnostic
from code_structure_viz.source.source_view import SourceView
from code_structure_viz.source.targets import ModuleTarget, PathTarget


def test_complete_semantic_json_has_exact_field_order_utf8_and_one_lf() -> None:
    source = SourceView("1" * 40, (), (), "b" * 64)
    coverage = PythonCoverage(0, 0, (), ("app.empty",), 0, ())
    snapshot = PythonSnapshot((), (), (), coverage, ())

    rendered = render_semantic_snapshot(snapshot, source, (), 1, 1)

    assert rendered == (
        b'{"type":"semantic_snapshot","schema":"code-structure-viz.semantic/v1",'
        b'"domain":"python","document_kind":"snapshot","status":"complete",'
        b'"source":{"schema":"code-structure-viz.source-view/v1","kind":"working-tree",'
        b'"head_commit":"1111111111111111111111111111111111111111",'
        b'"fingerprint":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",'
        b'"file_count":0},"request":{"targets":[],"upstream_depth":1,'
        b'"downstream_depth":1},"coverage":{"candidate_files":0,"parsed_files":0,'
        b'"failed_files":[],"selected_modules":["app.empty"],"selected_entities":0,'
        b'"frontier":[]},"entities":[],"members":[],"relations":[],"diagnostics":[]}\n'
    )


def test_semantic_json_renderer_class_preserves_the_exact_snapshot_bytes() -> None:
    source = SourceView("1" * 40, (), (), "b" * 64)
    snapshot = PythonSnapshot(
        (),
        (),
        (),
        PythonCoverage(0, 0, (), ("app.empty",), 0, ()),
        (),
    )

    rendered = PythonSemanticJsonRenderer(
        source_view=source,
        targets=(),
        upstream_depth=1,
        downstream_depth=1,
    ).render(snapshot)

    assert rendered == (
        b'{"type":"semantic_snapshot","schema":"code-structure-viz.semantic/v1",'
        b'"domain":"python","document_kind":"snapshot","status":"complete",'
        b'"source":{"schema":"code-structure-viz.source-view/v1","kind":"working-tree",'
        b'"head_commit":"1111111111111111111111111111111111111111",'
        b'"fingerprint":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",'
        b'"file_count":0},"request":{"targets":[],"upstream_depth":1,'
        b'"downstream_depth":1},"coverage":{"candidate_files":0,"parsed_files":0,'
        b'"failed_files":[],"selected_modules":["app.empty"],"selected_entities":0,'
        b'"frontier":[]},"entities":[],"members":[],"relations":[],"diagnostics":[]}\n'
    )


def test_partial_safe_semantic_json_includes_closed_failures_frontier_and_diagnostic() -> None:
    value = diagnostic(
        DiagnosticCode.PY_PARSE,
        domain="python",
        path="src/app/broken.py",
        line=2,
    )
    coverage = PythonCoverage(
        2,
        1,
        (
            FailedSourceFile(
                PurePosixPath("src/app/broken.py"),
                FailedStage.PARSE,
                DiagnosticCode.PY_PARSE,
            ),
        ),
        ("app.good",),
        0,
        (
            CoverageFrontier(
                FrontierDirection.FAILURE,
                FrontierKind.FILE,
                "src/app/broken.py",
                FrontierReason.FAILED_SOURCE,
            ),
        ),
    )
    snapshot = PythonSnapshot((), (), (), coverage, (value,), partial_safe=True)

    rendered = render_semantic_snapshot(
        snapshot,
        SourceView(None, (), (), "c" * 64),
        (
            PathTarget(PurePosixPath("src/app/good.py")),
            ModuleTarget("app.good"),
        ),
        0,
        2,
    )

    assert b'"status":"incomplete","incomplete_kind":"partial_safe","source"' in rendered
    assert (
        b'"targets":[{"kind":"path","value":"src/app/good.py"},'
        b'{"kind":"module","value":"app.good"}]' in rendered
    )
    assert b'"stage":"parse","diagnostic_code":"CSV-PY-003"' in rendered
    assert b'"direction":"failure","kind":"file"' in rendered
    assert rendered.count(b'"code":"CSV-PY-003"') == 1
    assert rendered.endswith(b"\n") and not rendered.endswith(b"\n\n")
