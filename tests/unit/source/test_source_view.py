import os
import unicodedata
from contextlib import suppress
from pathlib import Path, PurePosixPath
from typing import cast

import pytest

from code_structure_viz.core.config import PythonConfig
from code_structure_viz.source.freezer import build_commit_source_view
from code_structure_viz.source.git_repository import (
    Commit,
    CommitTreeEntry,
    EnumeratedPath,
    GitRepositoryReader,
    Unborn,
)
from code_structure_viz.source.source_view import (
    SourceDriftError,
    SourceFileKind,
    SourceInterruptedError,
    SourceViewBuilder,
    SourceViewBuildError,
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
    assert len(view.failures) == 1
    assert view.failures[0].path == PurePosixPath("src/directory.py")
    assert view.failures[0].diagnostic_code.value == "CSV-PY-001"
    assert view.fingerprint == "47b91366ff6f1436643bf1cc62f7ac70b7c9cd671a1a980c1cd7ab29924eb8d9"
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


def test_commit_source_view_rejects_non_blob_python_candidate() -> None:
    class Reader:
        def enumerate_commit_tree(self, _commit: str) -> tuple[CommitTreeEntry, ...]:
            return (
                CommitTreeEntry(
                    PurePosixPath("src/component.py"),
                    "a" * 40,
                    "160000",
                    "commit",
                ),
            )

        def read_commit_blob(self, _commit: str, _path: PurePosixPath) -> bytes:
            raise AssertionError("a non-blob candidate must not be read as a blob")

    view = build_commit_source_view(
        cast(GitRepositoryReader, Reader()),
        Commit("b" * 40),
        PythonConfig(("src",), ("**/*.py",), ()),
    )

    assert view.files == ()
    assert view.failures[0].path == PurePosixPath("src/component.py")
    assert view.failures[0].diagnostic_code.value == "CSV-PY-001"


def test_commit_source_view_preserves_raw_git_path_spelling_in_inventory() -> None:
    raw_path = "src/cafe\u0301.py"
    canonical_path = PurePosixPath("src/café.py")

    class Reader:
        def enumerate_commit_tree(self, _commit: str) -> tuple[CommitTreeEntry, ...]:
            return (
                CommitTreeEntry(
                    canonical_path,
                    "a" * 40,
                    "100644",
                    "blob",
                    raw_path,
                ),
            )

        def read_blob_object(self, _object_id: str) -> bytes:
            return b"class Value:\n    pass\n"

    view = build_commit_source_view(
        cast(GitRepositoryReader, Reader()),
        Commit("b" * 40),
        PythonConfig(("src",), ("**/*.py",), ()),
    )

    assert view.inventory[0].path == canonical_path
    assert view.inventory[0].raw_path == raw_path


def test_descriptor_anchored_source_read_survives_repository_path_swap(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    (repository / "module.py").write_bytes(b"class Original:\n    pass\n")
    alternate = tmp_path / "alternate"
    alternate.mkdir()
    (alternate / "module.py").write_bytes(b"class Alternate:\n    pass\n")
    repository_descriptor = os.open(repository, os.O_RDONLY)
    displaced = tmp_path / "displaced"
    try:
        repository.rename(displaced)
        alternate.rename(repository)
        view = SourceViewBuilder(
            repository,
            tmp_path / "stage",
            repository_descriptor=repository_descriptor,
        ).build(
            Commit("1" * 40),
            (_entry("module.py"),),
            PythonConfig((".",), ("**/*.py",), ()),
        )
    finally:
        os.close(repository_descriptor)

    assert view.files[0].content == b"class Original:\n    pass\n"


def test_nfc_collision_is_run_fatal_before_candidate_filtering(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    config = PythonConfig((".",), ("**/*.py",), ())
    composed = PurePosixPath("caf\u00e9.py")

    with pytest.raises(SourceViewBuildError) as caught:
        SourceViewBuilder(repo, tmp_path / "stage", fatal_path_identity_collisions=True).build(
            Commit("2" * 40),
            (
                EnumeratedPath("caf\u00e9.py", composed),
                EnumeratedPath("cafe\u0301.py", composed),
            ),
            config,
        )

    assert caught.value.diagnostic.code.value == "CSV-DIFF-003"


def test_non_python_nfc_collision_is_run_fatal_before_candidate_filtering(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    composed = PurePosixPath("docs/caf\u00e9.txt")

    with pytest.raises(SourceViewBuildError) as caught:
        SourceViewBuilder(repo, tmp_path / "stage", fatal_path_identity_collisions=True).build(
            Commit("2" * 40),
            (
                EnumeratedPath("docs/caf\u00e9.txt", composed),
                EnumeratedPath("docs/cafe\u0301.txt", composed),
            ),
            PythonConfig(("src",), ("**/*.py",), ()),
        )

    assert caught.value.diagnostic.code.value == "CSV-DIFF-003"


def test_casefold_samefile_collision_keeps_each_canonical_path_descriptor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "Foo.py").write_bytes(b"class Foo:\n    pass\n")
    (repo / "foo.py").write_bytes(b"class foo:\n    pass\n")

    monkeypatch.setattr(os.path, "samefile", lambda _left, _right: True)

    view = SourceViewBuilder(repo, tmp_path / "stage").build(
        Commit("2" * 40),
        (_entry("Foo.py"), _entry("foo.py")),
        PythonConfig((".",), ("**/*.py",), ()),
    )

    assert view.files == ()
    assert tuple(item.path.as_posix() for item in view.failures) == ("Foo.py", "foo.py")
    assert all(item.diagnostic_code.value == "CSV-SOURCE-004" for item in view.failures)


def test_mixed_nfc_and_casefold_collision_is_run_fatal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    canonical = "É.py"
    decomposed = "E\u0301.py"
    lower = "é.py"
    for name in (canonical, decomposed, lower):
        (repo / name).write_bytes(b"class Value:\n    pass\n")

    def samefile(left: os.PathLike[str] | str, right: os.PathLike[str] | str) -> bool:
        return {Path(left).name, Path(right).name} == {decomposed, lower}

    monkeypatch.setattr(os.path, "samefile", samefile)

    with pytest.raises(SourceViewBuildError) as caught:
        SourceViewBuilder(repo, tmp_path / "stage", fatal_path_identity_collisions=True).build(
            Commit("2" * 40),
            (
                EnumeratedPath(canonical, PurePosixPath(canonical)),
                EnumeratedPath(decomposed, PurePosixPath(unicodedata.normalize("NFC", decomposed))),
                EnumeratedPath(lower, PurePosixPath(lower)),
            ),
            PythonConfig((".",), ("**/*.py",), ()),
        )

    assert caught.value.diagnostic.code.value == "CSV-DIFF-003"


def test_independent_nfc_collision_groups_are_run_fatal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    names = ("É.py", "E\u0301.py", "é.py", "e\u0301.py")
    for name in names:
        (repo / name).write_bytes(b"class Value:\n    pass\n")
    monkeypatch.setattr(os.path, "samefile", lambda _left, _right: False)

    with pytest.raises(SourceViewBuildError) as caught:
        SourceViewBuilder(repo, tmp_path / "stage", fatal_path_identity_collisions=True).build(
            Commit("2" * 40),
            tuple(
                EnumeratedPath(name, PurePosixPath(unicodedata.normalize("NFC", name)))
                for name in names
            ),
            PythonConfig((".",), ("**/*.py",), ()),
        )

    assert caught.value.diagnostic.code.value == "CSV-DIFF-003"


def test_single_physical_spelling_is_read_without_replacing_it_with_logical_identity(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    raw_path = "cafe\u0301.py"
    canonical_path = PurePosixPath("café.py")
    (repo / raw_path).write_bytes(b"class Physical:\n    pass\n")

    view = SourceViewBuilder(repo, tmp_path / "stage").build(
        Commit("3" * 40),
        (EnumeratedPath(raw_path, canonical_path),),
        PythonConfig((".",), ("**/*.py",), ()),
    )

    assert tuple(item.path for item in view.files) == (canonical_path,)
    assert view.files[0].content == b"class Physical:\n    pass\n"
    assert (tmp_path / "stage/source" / canonical_path).read_bytes() == view.files[0].content


def test_parent_symlink_component_is_rejected_without_reading_outside_repository(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.py").write_bytes(b"SECRET_OUTSIDE_REPOSITORY")
    (repo / "linked").symlink_to(outside, target_is_directory=True)

    view = SourceViewBuilder(repo, tmp_path / "stage").build(
        Commit("3" * 40),
        (_entry("linked/secret.py"),),
        PythonConfig((".",), ("**/*.py",), ()),
    )

    assert view.files == ()
    assert len(view.failures) == 1
    assert view.failures[0].path == PurePosixPath("linked/secret.py")
    assert view.failures[0].diagnostic_code.value == "CSV-SOURCE-002"
    assert not (tmp_path / "stage/source/linked/secret.py").exists()


def test_parent_directory_swap_never_reads_repository_external_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    source_parent = repo / "src"
    source_parent.mkdir(parents=True)
    (source_parent / "model.py").write_bytes(b"class Safe:\n    pass\n")
    outside = tmp_path / "outside"
    outside.mkdir()
    secret = b"SECRET_OUTSIDE_REPOSITORY"
    (outside / "model.py").write_bytes(secret)
    moved_parent = repo / "original-src"
    real_open = os.open
    swapped = False
    unanchored_leaf_open = False

    def swap_before_leaf_open(
        path: os.PathLike[str] | str,
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> int:
        nonlocal swapped, unanchored_leaf_open
        if not swapped and (Path(path) == source_parent / "model.py" or path == "model.py"):
            source_parent.rename(moved_parent)
            source_parent.symlink_to(outside, target_is_directory=True)
            swapped = True
            unanchored_leaf_open = dir_fd is None
        return real_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(os, "open", swap_before_leaf_open)

    with suppress(SourceDriftError):
        SourceViewBuilder(repo, tmp_path / "stage").build(
            Commit("3" * 40),
            (_entry("src/model.py"),),
            PythonConfig(("src",), ("**/*.py",), ()),
        )

    assert swapped
    assert not unanchored_leaf_open


def test_repeated_double_star_pattern_on_a_deep_path_is_bounded_and_non_recursive(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    staging = tmp_path / "staging"
    depth = 600
    path = "/".join(["d"] * depth + ["target.py"])
    pattern = "/".join(["**"] * depth + ["never.py"])

    view = SourceViewBuilder(repository, staging).build(
        Unborn("refs/heads/main"),
        (EnumeratedPath(path, PurePosixPath(path)),),
        PythonConfig((".",), (pattern,), ()),
    )

    assert view.files == ()
    assert view.failures == ()


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


def test_source_freeze_honors_cancellation_before_reading(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    builder = SourceViewBuilder(repo, tmp_path / "stage", cancelled=lambda: True)

    with pytest.raises(SourceInterruptedError):
        builder.build(
            Unborn("refs/heads/main"),
            (),
            PythonConfig((".",), ("**/*.py",), ()),
        )
