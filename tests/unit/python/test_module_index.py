import hashlib
from pathlib import PurePosixPath

from code_structure_viz.adapters.python.module_index import PythonModuleIndex
from code_structure_viz.core.config import PythonConfig
from code_structure_viz.core.diagnostics import DiagnosticCode
from code_structure_viz.source.source_view import (
    AcquisitionStage,
    SourceAcquisitionFailure,
    SourceFile,
    SourceFileKind,
    SourceView,
)


def _source(path: str, content: bytes = b"pass\n") -> SourceFile:
    return SourceFile(
        path=PurePosixPath(path),
        kind=SourceFileKind.REGULAR,
        resolved_target=None,
        size_bytes=len(content),
        sha256=hashlib.sha256(content).hexdigest(),
        content=content,
    )


def _view(
    *files: SourceFile,
    failures: tuple[SourceAcquisitionFailure, ...] = (),
) -> SourceView:
    return SourceView(None, files, failures, "0" * 64)


def test_module_mapping_uses_longest_root_and_init_rules() -> None:
    index = PythonModuleIndex.build(
        _view(
            _source("src/pkg/__init__.py"),
            _source("src/ns/mod.py"),
            _source("src/日本.py"),
            _source("__init__.py"),
        ),
        PythonConfig(("src", "."), ("**/*.py",), ()),
    )

    assert tuple((item.path, item.module) for item in index.modules) == (
        (PurePosixPath("__init__.py"), "__init__"),
        (PurePosixPath("src/ns/mod.py"), "ns.mod"),
        (PurePosixPath("src/pkg/__init__.py"), "pkg"),
        (PurePosixPath("src/日本.py"), "日本"),
    )
    assert index.failures == ()
    assert index.diagnostics == ()


def test_invalid_keyword_and_non_identifier_paths_are_file_local_failures() -> None:
    index = PythonModuleIndex.build(
        _view(_source("src/class.py"), _source("src/bad-name.py")),
        PythonConfig(("src",), ("**/*.py",), ()),
    )

    assert index.modules == ()
    assert tuple(item.path.as_posix() for item in index.failures) == (
        "src/bad-name.py",
        "src/class.py",
    )
    assert {item.stage.value for item in index.failures} == {"module_identity"}
    assert [item.code.value for item in index.diagnostics] == ["CSV-PY-004", "CSV-PY-004"]


def test_duplicate_module_identity_excludes_every_candidate_without_a_winner() -> None:
    index = PythonModuleIndex.build(
        _view(_source("src/domain/order.py"), _source("domain/order.py")),
        PythonConfig(("src", "."), ("**/*.py",), ()),
    )

    assert index.modules == ()
    assert tuple(item.path.as_posix() for item in index.failures) == (
        "domain/order.py",
        "src/domain/order.py",
    )
    assert all(item.stage.value == "module_collision" for item in index.failures)
    assert len(index.diagnostics) == 1
    assert index.diagnostics[0].code.value == "CSV-PY-005"
    assert index.diagnostics[0].symbol == "python:module:domain.order"
    assert index.collided_modules == ("domain.order",)


def test_source_acquisition_failure_is_preserved_in_domain_coverage() -> None:
    failure = SourceAcquisitionFailure(
        PurePosixPath("src/link.py"),
        AcquisitionStage.PATH_SAFETY,
        DiagnosticCode.SOURCE_SYMLINK,
    )

    index = PythonModuleIndex.build(
        _view(failures=(failure,)), PythonConfig(("src",), ("**/*.py",), ())
    )

    assert index.candidate_file_count == 1
    assert index.failures[0].path == PurePosixPath("src/link.py")
    assert index.failures[0].stage.value == "path_safety"
    assert index.diagnostics[0].code.value == "CSV-SOURCE-002"
