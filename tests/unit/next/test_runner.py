from __future__ import annotations

import hashlib
import os
from importlib import import_module, resources
from pathlib import Path
from types import ModuleType

import pytest


class MemoryResource:
    def __init__(
        self,
        content: bytes,
        *,
        is_file: bool = True,
        read_error: OSError | None = None,
    ) -> None:
        self.content = content
        self.file = is_file
        self.read_error = read_error
        self.reads = 0

    def is_file(self) -> bool:
        return self.file

    def read_bytes(self) -> bytes:
        self.reads += 1
        if self.read_error is not None:
            raise self.read_error
        return self.content


class MemoryPackage:
    def __init__(self, resource: MemoryResource) -> None:
        self.resource = resource
        self.joined_paths: list[tuple[str, ...]] = []

    def joinpath(self, *descendants: str) -> MemoryResource:
        self.joined_paths.append(descendants)
        return self.resource


def _runner() -> ModuleType:
    return import_module("code_structure_viz.adapters.next.runner")


def test_identity_uses_one_packaged_read_for_version_and_digest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _runner()
    content = b"// CodeStructureViz-Adapter-Version: 0.1.0\nexport const adapter = true;\n"
    resource = MemoryResource(content)
    package = MemoryPackage(resource)
    requested_packages: list[str] = []

    def files(package_name: str) -> MemoryPackage:
        requested_packages.append(package_name)
        return package

    monkeypatch.setattr(resources, "files", files)

    identity = runner.resolve_next_adapter_identity()

    assert requested_packages == ["code_structure_viz"]
    assert package.joined_paths == [("_next_runtime", "next-adapter.mjs")]
    assert identity.version == "0.1.0"
    assert identity.sha256 == "02af3205940a46ba514388bc7b6527f3292380ddfdd8925aeed1a7ef4433c262"
    assert resource.reads == 1


def test_open_candidate_identity_hashes_and_owns_one_regular_file_fd(
    tmp_path: Path,
) -> None:
    runner = _runner()
    candidate = tmp_path / "candidate"
    content = b"candidate bytes are not executable evidence\n"
    candidate.write_bytes(content)
    candidate.chmod(0o600)
    expected = candidate.stat()

    opened = runner.open_node_candidate_identity(str(candidate))
    descriptor = opened.fileno()
    try:
        assert opened.candidate_path == str(candidate)
        assert opened.sha256 == hashlib.sha256(content).hexdigest()
        assert opened.device == expected.st_dev
        assert opened.inode == expected.st_ino
        assert os.fstat(descriptor).st_ino == expected.st_ino
        assert not os.get_inheritable(descriptor)
    finally:
        opened.close()

    with pytest.raises(OSError):
        os.fstat(descriptor)

    replacement_fd = os.open(candidate, os.O_RDONLY)
    try:
        opened.close()
        assert os.fstat(replacement_fd).st_ino == expected.st_ino
    finally:
        os.close(replacement_fd)


@pytest.mark.parametrize(
    "candidate_path",
    [
        "candidate",
        "/",
        "//tmp/candidate",
        "/tmp//candidate",
        "/tmp/./candidate",
        "/tmp/../candidate",
        "/tmp/\x00candidate",
    ],
)
def test_candidate_identity_rejects_unsafe_absolute_paths_before_open(
    monkeypatch: pytest.MonkeyPatch,
    candidate_path: str,
) -> None:
    runner = _runner()
    opened_paths: list[str] = []
    real_open = os.open

    def record_open(path: str, flags: int, *args: object, **kwargs: object) -> int:
        opened_paths.append(path)
        return real_open(path, flags, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(runner.os, "open", record_open)

    with pytest.raises(runner.NodeCandidateIdentityError):
        runner.open_node_candidate_identity(candidate_path)

    assert opened_paths == []


def test_candidate_identity_rejects_ancestor_symlink(
    tmp_path: Path,
) -> None:
    runner = _runner()
    real_directory = tmp_path / "real"
    real_directory.mkdir()
    candidate = real_directory / "candidate"
    candidate.write_bytes(b"candidate bytes\n")
    linked_directory = tmp_path / "linked"
    linked_directory.symlink_to(real_directory, target_is_directory=True)

    try:
        opened = runner.open_node_candidate_identity(str(linked_directory / "candidate"))
    except runner.NodeCandidateIdentityError:
        return

    opened.close()
    pytest.fail("candidate identity must reject an ancestor symlink")


def test_candidate_identity_rejects_final_symlink(tmp_path: Path) -> None:
    runner = _runner()
    target = tmp_path / "target"
    target.write_bytes(b"target bytes\n")
    candidate = tmp_path / "candidate"
    candidate.symlink_to(target)

    with pytest.raises(runner.NodeCandidateIdentityError):
        runner.open_node_candidate_identity(str(candidate))


def test_candidate_identity_hashes_opened_object_after_path_replacement(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    runner = _runner()
    candidate_directory = tmp_path / "candidate-directory"
    candidate_directory.mkdir()
    candidate = candidate_directory / "candidate"
    original_content = b"a" * (1024 * 1024 + 1)
    candidate.write_bytes(original_content)
    original_identity = candidate.stat()
    replacement_directory = tmp_path / "replacement-directory"
    replacement_directory.mkdir()
    (replacement_directory / "candidate").write_bytes(b"replacement bytes\n")
    moved_directory = tmp_path / "moved-original-directory"
    real_read = os.read
    replaced = False

    def replace_after_first_read(descriptor: int, count: int) -> bytes:
        nonlocal replaced
        chunk = real_read(descriptor, count)
        if not replaced:
            candidate_directory.rename(moved_directory)
            replacement_directory.rename(candidate_directory)
            replaced = True
        return chunk

    monkeypatch.setattr(runner.os, "read", replace_after_first_read)

    opened = runner.open_node_candidate_identity(str(candidate))
    try:
        assert replaced
        assert candidate.read_bytes() == b"replacement bytes\n"
        assert opened.sha256 == hashlib.sha256(original_content).hexdigest()
        assert (opened.device, opened.inode) == (
            original_identity.st_dev,
            original_identity.st_ino,
        )
    finally:
        opened.close()


def test_candidate_identity_rejects_measurable_mutation_during_hash(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    runner = _runner()
    candidate = tmp_path / "candidate"
    candidate.write_bytes(b"a" * (1024 * 1024 + 1))
    real_read = os.read
    mutated = False
    measured_descriptors: list[int] = []

    def mutate_after_first_read(descriptor: int, count: int) -> bytes:
        nonlocal mutated
        measured_descriptors.append(descriptor)
        chunk = real_read(descriptor, count)
        if chunk and not mutated:
            with candidate.open("ab") as writer:
                writer.write(b"mutation")
            mutated = True
        return chunk

    monkeypatch.setattr(runner.os, "read", mutate_after_first_read)

    try:
        opened = runner.open_node_candidate_identity(str(candidate))
    except runner.NodeCandidateIdentityError:
        pass
    else:
        opened.close()
        pytest.fail("measurable identity drift during hashing must fail closed")

    assert mutated
    assert measured_descriptors
    with pytest.raises(OSError):
        os.fstat(measured_descriptors[0])


@pytest.mark.parametrize(
    "missing_capability",
    ["O_NOFOLLOW", "O_CLOEXEC", "O_DIRECTORY", "dir_fd"],
)
def test_candidate_identity_fails_before_open_when_required_capability_is_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    missing_capability: str,
) -> None:
    runner = _runner()
    candidate = tmp_path / "candidate"
    candidate.write_bytes(b"candidate bytes\n")
    open_calls: list[str] = []
    real_open = os.open

    def record_open(path: str, flags: int, *args: object, **kwargs: object) -> int:
        open_calls.append(path)
        return real_open(path, flags, *args, **kwargs)  # type: ignore[arg-type]

    supported_dir_fd = set(os.supports_dir_fd)
    supported_dir_fd.add(record_open)
    monkeypatch.setattr(runner.os, "open", record_open)
    monkeypatch.setattr(runner.os, "supports_dir_fd", supported_dir_fd)
    if missing_capability == "dir_fd":
        supported_dir_fd.remove(record_open)
    else:
        monkeypatch.delattr(runner.os, missing_capability)

    with pytest.raises(runner.NodeCandidateIdentityError):
        runner.open_node_candidate_identity(str(candidate))

    assert open_calls == []


def test_non_file_package_resource_fails_without_reading(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _runner()
    resource = MemoryResource(
        b"// CodeStructureViz-Adapter-Version: 0.1.0\nexport const adapter = true;\n",
        is_file=False,
    )
    package = MemoryPackage(resource)
    monkeypatch.setattr(resources, "files", lambda package_name: package)

    with pytest.raises(runner.NextAdapterIdentityError):
        runner.resolve_next_adapter_identity()

    assert resource.reads == 0


def test_package_resource_read_error_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _runner()
    resource = MemoryResource(b"", read_error=OSError("permission denied"))
    package = MemoryPackage(resource)
    monkeypatch.setattr(resources, "files", lambda package_name: package)

    with pytest.raises(runner.NextAdapterIdentityError):
        runner.resolve_next_adapter_identity()

    assert resource.reads == 1


def test_missing_package_resource_fails_closed_without_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _runner()
    requested_packages: list[str] = []

    def files(package_name: str) -> object:
        requested_packages.append(package_name)
        raise ModuleNotFoundError(package_name)

    monkeypatch.setattr(resources, "files", files)

    with pytest.raises(runner.NextAdapterIdentityError):
        runner.resolve_next_adapter_identity()

    assert requested_packages == ["code_structure_viz"]


def test_resource_package_import_error_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _runner()

    def files(package_name: str) -> object:
        raise ImportError(f"cannot load {package_name}")

    monkeypatch.setattr(resources, "files", files)

    with pytest.raises(runner.NextAdapterIdentityError):
        runner.resolve_next_adapter_identity()


def test_duplicate_version_marker_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _runner()
    content = (
        b"// CodeStructureViz-Adapter-Version: 0.1.0\n// CodeStructureViz-Adapter-Version: 0.2.0\n"
    )
    resource = MemoryResource(content)
    package = MemoryPackage(resource)
    monkeypatch.setattr(resources, "files", lambda package_name: package)

    with pytest.raises(runner.NextAdapterIdentityError):
        runner.resolve_next_adapter_identity()

    assert resource.reads == 1


@pytest.mark.parametrize(
    "content",
    [
        b"",
        b"export const adapter = true;\n",
        b"source\n// CodeStructureViz-Adapter-Version: 0.1.0\n",
        b"\xef\xbb\xbf// CodeStructureViz-Adapter-Version: 0.1.0\n",
        b"// CodeStructureViz-Adapter-Version: 00.1.0\n",
        b"// CodeStructureViz-Adapter-Version: 0.01.0\n",
        b"// CodeStructureViz-Adapter-Version: 0.0.01\n",
        b"// CodeStructureViz-Adapter-Version: 1.2.3-alpha\n",
        b"// CodeStructureViz-Adapter-Version: 1.2.3+build\n",
        b"// CodeStructureViz-Adapter-Version: 1.2.3 \n",
        b"// CodeStructureViz-Adapter-Version:  1.2.3\n",
        b"// CodeStructureViz-Adapter-Version: 1.2.3\r\n",
        b"// CodeStructureViz-Adapter-Version: 1.2.\xff\n",
        b"// CodeStructureViz-Adapter-Version: 1.2.3",
    ],
)
def test_invalid_version_header_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    content: bytes,
) -> None:
    runner = _runner()
    resource = MemoryResource(content)
    package = MemoryPackage(resource)
    monkeypatch.setattr(resources, "files", lambda package_name: package)

    with pytest.raises(runner.NextAdapterIdentityError):
        runner.resolve_next_adapter_identity()


def test_resolver_does_not_accept_caller_identity_or_resource_overrides(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _runner()
    files_calls: list[str] = []

    def files(package_name: str) -> MemoryPackage:
        files_calls.append(package_name)
        raise AssertionError("caller overrides must be rejected before resource lookup")

    monkeypatch.setattr(resources, "files", files)

    with pytest.raises(TypeError):
        runner.resolve_next_adapter_identity(
            path="checkout/adapters/next/next-adapter.mjs",
            version="0.1.0.dev0",
            sha256="a" * 64,
        )

    assert files_calls == []
