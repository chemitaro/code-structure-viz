import os
from pathlib import Path

import pytest

from code_structure_viz.artifacts.writer import OutputTransaction, OutputTransactionError
from code_structure_viz.core.diagnostics import DiagnosticCode


def test_output_transaction_publishes_the_closed_file_set_by_directory_rename(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    output = tmp_path / "result"
    transaction = OutputTransaction(repository, output)
    transaction.begin()

    descriptor = transaction.stage_payload("semantic-json", b"{}\n")
    transaction.stage_manifest(b'{"type":"run_manifest"}\n')
    staging_root = transaction.staging_root
    transaction.commit()

    assert descriptor.path == "python.snapshot.semantic.json"
    assert sorted(path.name for path in output.iterdir()) == [
        "python.snapshot.semantic.json",
        "run-manifest.json",
    ]
    assert (output / "python.snapshot.semantic.json").read_bytes() == b"{}\n"
    assert not staging_root.exists()


def test_output_transaction_rejects_existing_or_inside_repository_destination(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    existing = tmp_path / "existing"
    existing.mkdir()

    with pytest.raises(OutputTransactionError) as existing_error:
        OutputTransaction(repository, existing)
    assert existing_error.value.diagnostic.code is DiagnosticCode.OUTPUT_DESTINATION

    with pytest.raises(OutputTransactionError) as inside_error:
        OutputTransaction(repository, repository / "artifacts")
    assert inside_error.value.diagnostic.code is DiagnosticCode.OUTPUT_INSIDE_REPO


def test_output_transaction_rejects_alternate_case_physical_repository_alias(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "Repository"
    repository.mkdir()
    alternate_spelling = tmp_path / "repository"
    if not alternate_spelling.exists() or not os.path.samefile(repository, alternate_spelling):
        pytest.skip("filesystem is case-sensitive")
    output = alternate_spelling / "artifacts"

    with pytest.raises(OutputTransactionError) as caught:
        OutputTransaction(repository, output)

    assert caught.value.diagnostic.code is DiagnosticCode.OUTPUT_INSIDE_REPO
    assert not output.exists()


def test_output_transaction_parent_swap_cannot_redirect_staging_into_repository(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    parent = tmp_path / "safe-parent"
    parent.mkdir()
    displaced_parent = tmp_path / "displaced-parent"
    transaction = OutputTransaction(repository, parent / "result")
    real_mkdir = os.mkdir
    swapped = False

    def swap_parent_before_staging(
        path: os.PathLike[str] | str,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> None:
        nonlocal swapped
        if not swapped and Path(path).name.startswith(".code-structure-viz-staging-"):
            parent.rename(displaced_parent)
            parent.symlink_to(repository, target_is_directory=True)
            swapped = True
        if dir_fd is None:
            real_mkdir(path, mode)
        else:
            real_mkdir(path, mode, dir_fd=dir_fd)

    monkeypatch.setattr(os, "mkdir", swap_parent_before_staging)

    try:
        with pytest.raises(OutputTransactionError) as caught:
            transaction.begin()
    finally:
        transaction.abort()

    assert caught.value.diagnostic.code is DiagnosticCode.OUTPUT_DESTINATION
    assert swapped is True
    assert list(repository.iterdir()) == []
    assert list(displaced_parent.iterdir()) == []


def test_output_transaction_parent_swap_cannot_redirect_artifacts_or_publication(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    parent = tmp_path / "safe-parent"
    parent.mkdir()
    displaced_parent = tmp_path / "displaced-parent"
    transaction = OutputTransaction(repository, parent / "result")
    transaction.begin()
    staging_name = transaction.staging_root.name

    parent.rename(displaced_parent)
    parent.symlink_to(repository, target_is_directory=True)
    shadow_staging = repository / staging_name
    (shadow_staging / "source").mkdir(parents=True)
    (shadow_staging / "artifacts").mkdir()
    marker = shadow_staging / "marker"
    marker.write_bytes(b"unchanged")
    transaction.stage_payload("semantic-json", b"{}\n")
    transaction.stage_manifest(b'{"type":"run_manifest"}\n')

    try:
        with pytest.raises(OutputTransactionError) as caught:
            transaction.commit()
    finally:
        transaction.abort()

    assert caught.value.diagnostic.code is DiagnosticCode.OUTPUT_DESTINATION
    assert marker.read_bytes() == b"unchanged"
    assert list((shadow_staging / "artifacts").iterdir()) == []
    assert not (repository / "result").exists()
    assert list(displaced_parent.iterdir()) == []


def test_output_transaction_abort_removes_frozen_source_and_payload_bytes(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    transaction = OutputTransaction(repository, tmp_path / "result")
    transaction.begin()
    (transaction.staging_root / "source" / "secret.py").write_bytes(b"secret")
    transaction.stage_payload("plantuml", b"@startuml\n@enduml\n")
    staging_root = transaction.staging_root

    transaction.abort()

    assert not staging_root.exists()
    assert not (tmp_path / "result").exists()


def test_output_transaction_never_replaces_destination_created_at_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    output = tmp_path / "result"
    transaction = OutputTransaction(repository, output)
    transaction.begin()
    transaction.stage_payload("semantic-json", b"{}\n")
    transaction.stage_manifest(b'{"type":"run_manifest"}\n')

    real_stat = os.stat
    raced = False
    existing_inode: int | None = None

    def create_destination_during_final_absence_check(
        path: os.PathLike[str] | str,
        *,
        dir_fd: int | None = None,
        follow_symlinks: bool = True,
    ) -> os.stat_result:
        nonlocal existing_inode, raced
        if path == output.name and dir_fd is not None and not raced:
            raced = True
            output.mkdir()
            existing_inode = real_stat(output).st_ino
            raise FileNotFoundError
        return real_stat(path, dir_fd=dir_fd, follow_symlinks=follow_symlinks)

    monkeypatch.setattr(os, "stat", create_destination_during_final_absence_check)

    with pytest.raises(OutputTransactionError) as caught:
        transaction.commit()

    assert caught.value.diagnostic.code is DiagnosticCode.OUTPUT_DESTINATION
    assert output.is_dir()
    assert output.stat().st_ino == existing_inode
    assert list(output.iterdir()) == []
