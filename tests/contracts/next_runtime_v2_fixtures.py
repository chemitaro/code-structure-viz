"""Contract-test source fixtures, independent of runtime/process admission."""

from pathlib import Path, PurePosixPath

from code_structure_viz.adapters.next.source_acquisition import (
    SourceAcquisitionSeal,
    SourceDiscoveryIntent,
    seal_source_acquisition,
)
from code_structure_viz.source.git_repository import Commit, EnumeratedPath
from code_structure_viz.source.source_view import DescriptorAnchoredSourceReadSession


def sealed_source_fixture_v1(
    tmp_path: Path,
    *,
    trusted_digest: str,
    page_content: bytes = b"export default function Page() { return null; }",
) -> SourceAcquisitionSeal:
    """Use the existing real source acquisition; never construct a synthetic seal."""

    repository = tmp_path / "repo"
    repository.mkdir()
    files = {
        "package.json": b'{"dependencies":{"next":"15"}}',
        "tsconfig.json": b'{"include":["src/**/*"]}',
        "src/page.tsx": page_content,
        "src/global.d.ts": b"declare interface Window { marker: string; }",
    }
    for relative_path, content in files.items():
        path = repository / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    entries = tuple(
        EnumeratedPath(path, PurePosixPath(path))
        for path in sorted(files, key=lambda p: p.encode())
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
        SourceDiscoveryIntent((".",)), reader, trusted_environment_digest=trusted_digest
    )
    assert isinstance(seal, SourceAcquisitionSeal)
    return seal
