from __future__ import annotations

import base64
import json
from pathlib import Path, PurePosixPath

import pytest

from code_structure_viz.adapters.next.protocol import build_next_adapter_request
from code_structure_viz.adapters.next.source_acquisition import (
    SourceAcquisitionSeal,
    SourceDiscoveryIntent,
    seal_source_acquisition,
)
from code_structure_viz.source.git_repository import Commit, EnumeratedPath
from code_structure_viz.source.source_view import DescriptorAnchoredSourceReadSession
from tests.contracts.next_reference_validation import (
    canonical_json_bytes,
    recompute_request_id,
    validate_request_envelope,
)
from tests.contracts.test_json_schemas import _validator


def _source_seal(tmp_path: Path) -> SourceAcquisitionSeal:
    repository = tmp_path / "repo"
    repository.mkdir()
    source_files = {
        "package.json": b'{"dependencies":{"next":"15"}}',
        "tsconfig.json": b'{"include":["src/**/*"]}',
        "src/page.tsx": b"export default function Page() { return null; }",
        "src/global.d.ts": b"declare interface Window { marker: string; }",
    }
    for relative_path, content in source_files.items():
        path = repository / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    entries = tuple(
        EnumeratedPath(path, PurePosixPath(path))
        for path in sorted(source_files, key=lambda value: value.encode("utf-8"))
    )
    head = Commit("1" * 40)
    reader = DescriptorAnchoredSourceReadSession(
        repository,
        entries,
        head_state=head,
        current_entries=lambda: entries,
        current_head_state=lambda: head,
        max_files=20_000,
        max_file_bytes=4 * 1024 * 1024,
        max_total_bytes=64 * 1024 * 1024,
    )
    seal = seal_source_acquisition(
        SourceDiscoveryIntent((".",)),
        reader,
        trusted_environment_digest="e" * 64,
    )
    assert isinstance(seal, SourceAcquisitionSeal)
    return seal


def test_request_is_derived_from_one_source_seal_and_matches_closed_contract(
    tmp_path: Path,
) -> None:
    seal = _source_seal(tmp_path)
    request = build_next_adapter_request(
        seal,
        adapter_version="1.0.0",
        trusted_type_environment={
            "schema": "code-structure-viz.next-trusted-types/v1",
            "environment_version": "1",
            "semantic_profile_id": "next-trusted-profile-v1",
            "sha256": "e" * 64,
        },
        targets=("path:src/page.tsx",),
        run_context={
            "requested_formats": ["semantic-json"],
            "budget_requested": None,
            "budget_resolved": 500,
            "budget_source": "builtin",
            "stdout_selector": None,
        },
    )

    payload = json.loads(request.canonical_bytes)
    validate_request_envelope(payload)
    _validator("next-adapter-request-v1.schema.json").validate(payload)

    assert request.request_id == recompute_request_id(payload)
    assert request.source_seal_id == seal.seal_id
    assert request.canonical_bytes == canonical_json_bytes(payload)
    assert [project["root"] for project in payload["projects"]] == ["."]
    assert [file["id"] for file in payload["files"]] == sorted(
        file["id"] for file in payload["files"]
    )
    assert {file["path"] for file in payload["files"]} == {
        item.path.as_posix() for item in seal.source_view.files
    }
    assert payload["targets"] == ["path:src/page.tsx"]
    assert {
        file["path"]: base64.b64decode(file["content_base64"], validate=True)
        for file in payload["files"]
    } == {item.path.as_posix(): item.content for item in seal.source_view.files}
    assert len(request.canonical_bytes) <= payload["limits"]["max_encoded_stdin_bytes"]


def test_request_builder_rejects_unhashable_stdout_selector(tmp_path: Path) -> None:
    seal = _source_seal(tmp_path)

    with pytest.raises(ValueError, match="run context source or selector"):
        build_next_adapter_request(
            seal,
            adapter_version="1.0.0",
            trusted_type_environment={
                "schema": "code-structure-viz.next-trusted-types/v1",
                "environment_version": "1",
                "semantic_profile_id": "next-trusted-profile-v1",
                "sha256": "e" * 64,
            },
            targets=("path:src/page.tsx",),
            run_context={
                "requested_formats": ["semantic-json"],
                "budget_requested": None,
                "budget_resolved": 500,
                "budget_source": "builtin",
                "stdout_selector": [],
            },
        )
