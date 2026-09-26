from __future__ import annotations

from importlib import import_module, resources
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
