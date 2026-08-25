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
