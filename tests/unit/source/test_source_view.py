from pathlib import Path, PurePosixPath

import pytest

from code_structure_viz.core.config import PythonConfig
from code_structure_viz.source.git_repository import Commit, EnumeratedPath, Unborn
from code_structure_viz.source.source_view import (
    SourceDriftError,
    SourceFileKind,
    SourceViewBuilder,
)


def _entry(path: str) -> EnumeratedPath:
    return EnumeratedPath(path, PurePosixPath(path))


def test_build_freezes_only_in_scope_python_files_and_has_exact_fingerprint(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    (repo / "src/domain").mkdir(parents=True)
    (repo / "src/domain/order.py").write_bytes(b"abc")
    (repo / "src/excluded.py").write_bytes(b"excluded")
    (repo / "src/types.pyi").write_bytes(b"stub")
    (repo / "root.py").write_bytes(b"outside root")
    (repo / "src/directory.py").mkdir()
    staging = tmp_path / "private-stage"
    config = PythonConfig(
        source_roots=("src",),
        include=("**/*.py",),
        exclude=("src/excluded.py",),
    )

    view = SourceViewBuilder(repo, staging).build(
        Commit("1" * 40),
        (
            _entry("src/domain/order.py"),
            _entry("src/excluded.py"),
            _entry("src/types.pyi"),
            _entry("root.py"),
            _entry("src/deleted.py"),
            _entry("src/directory.py"),
        ),
        config,
    )

    assert view.head_commit == "1" * 40
    assert len(view.files) == 1
    source = view.files[0]
    assert source.path == PurePosixPath("src/domain/order.py")
    assert source.kind is SourceFileKind.REGULAR
    assert source.resolved_target is None
    assert source.size_bytes == 3
    assert source.sha256 == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert source.content == b"abc"
    assert view.failures == ()
    assert view.fingerprint == "3f35282e8940cdf7c783adc4880d7797eaf6d6b8d1bb78b49d5c9e237f09b531"
    assert (staging / "source/src/domain/order.py").read_bytes() == b"abc"
    assert staging.stat().st_mode & 0o777 == 0o700


def test_unborn_source_view_has_null_head_commit(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    view = SourceViewBuilder(repo, tmp_path / "stage").build(
        Unborn("refs/heads/main"), (), PythonConfig(("src", "."), ("**/*.py",), ())
    )

    assert view.head_commit is None
    assert view.files == ()
    assert view.failures == ()


def test_nfc_collision_becomes_one_failure_and_neither_path_wins(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    config = PythonConfig((".",), ("**/*.py",), ())
    composed = PurePosixPath("caf\u00e9.py")

    view = SourceViewBuilder(repo, tmp_path / "stage").build(
        Commit("2" * 40),
        (
            EnumeratedPath("caf\u00e9.py", composed),
            EnumeratedPath("cafe\u0301.py", composed),
        ),
        config,
    )

    assert view.files == ()
    assert len(view.failures) == 1
    failure = view.failures[0]
    assert failure.path == composed
    assert failure.stage.value == "path_safety"
    assert failure.diagnostic_code.value == "CSV-SOURCE-004"


def test_internal_symlink_is_frozen_but_outside_symlink_is_a_failure(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "shared").mkdir()
    (repo / "shared/model.txt").write_bytes(b"class Model: pass\n")
    (repo / "src/model.py").symlink_to("../shared/model.txt")
    outside = tmp_path / "outside.py"
    outside.write_bytes(b"secret")
    (repo / "src/outside.py").symlink_to(outside)

    view = SourceViewBuilder(repo, tmp_path / "stage").build(
        Commit("3" * 40),
        (_entry("src/model.py"), _entry("src/outside.py")),
        PythonConfig(("src",), ("**/*.py",), ()),
    )

    assert len(view.files) == 1
    assert view.files[0].kind is SourceFileKind.SYMLINK
    assert view.files[0].resolved_target == PurePosixPath("shared/model.txt")
    assert view.files[0].content == b"class Model: pass\n"
    assert len(view.failures) == 1
    assert view.failures[0].path == PurePosixPath("src/outside.py")
    assert view.failures[0].diagnostic_code.value == "CSV-SOURCE-002"


def test_prepublication_probe_detects_source_byte_drift(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    source = repo / "src/model.py"
    source.write_bytes(b"before")
    entries = (_entry("src/model.py"),)
    config = PythonConfig(("src",), ("**/*.py",), ())
    builder = SourceViewBuilder(repo, tmp_path / "stage")
    initial = builder.build(Commit("4" * 40), entries, config)
    source.write_bytes(b"after!")

    with pytest.raises(SourceDriftError) as caught:
        builder.assert_unchanged(initial, Commit("4" * 40), entries, config)

    assert caught.value.diagnostic.code.value == "CSV-SOURCE-001"
    assert (caught.value.diagnostic.path, caught.value.diagnostic.symbol) == (None, None)


def test_prepublication_probe_detects_head_drift(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    config = PythonConfig((".",), ("**/*.py",), ())
    builder = SourceViewBuilder(repo, tmp_path / "stage")
    initial = builder.build(Commit("5" * 40), (), config)

    with pytest.raises(SourceDriftError):
        builder.assert_unchanged(initial, Commit("6" * 40), (), config)
