from __future__ import annotations

import hashlib
from collections.abc import Mapping
from pathlib import PurePosixPath

from code_structure_viz.adapters.python.analyzer import PythonSnapshotAnalyzer
from code_structure_viz.adapters.python.model import PythonSnapshot
from code_structure_viz.adapters.python.module_index import PythonModuleIndex
from code_structure_viz.adapters.python.selection import PythonTargetSelector
from code_structure_viz.core.config import PythonConfig
from code_structure_viz.source.source_view import SourceFile, SourceFileKind, SourceView


def snapshot_from_text(text: str) -> PythonSnapshot:
    return snapshot_from_files({"src/app.py": text})


def snapshot_from_files(files: Mapping[str, str]) -> PythonSnapshot:
    sources = []
    for raw_path, text in files.items():
        path = PurePosixPath(raw_path)
        content = text.encode("utf-8")
        sources.append(
            SourceFile(
                path=path,
                kind=SourceFileKind.REGULAR,
                resolved_target=None,
                size_bytes=len(content),
                sha256=hashlib.sha256(content).hexdigest(),
                content=content,
            )
        )
    view = SourceView(None, tuple(sources), (), "a" * 64)
    config = PythonConfig(("src",), ("**/*.py",), ())
    analysis = PythonSnapshotAnalyzer().analyze(PythonModuleIndex.build(view, config))
    selection = PythonTargetSelector().select(analysis, (), 1, 1)
    assert selection.snapshot is not None
    return selection.snapshot
