from __future__ import annotations

import email
import json
import os
import subprocess
import sys
import tarfile
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _build(tmp_path: Path) -> tuple[Path, Path]:
    distribution = tmp_path / "dist"
    result = subprocess.run(
        ("uv", "build", "--offline", "--out-dir", str(distribution)),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
        cwd=ROOT,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    return next(distribution.glob("*.whl")), next(distribution.glob("*.tar.gz"))


def _archive_members(wheel: Path, sdist: Path) -> tuple[list[str], list[str]]:
    with zipfile.ZipFile(wheel) as archive:
        wheel_members = archive.namelist()
    with tarfile.open(sdist, "r:gz") as archive:
        sdist_members = [member.name for member in archive.getmembers()]
    return wheel_members, sdist_members


def test_distribution_has_no_runtime_dependencies_or_private_repository_content(
    tmp_path: Path,
) -> None:
    wheel, sdist = _build(tmp_path)
    wheel_members, sdist_members = _archive_members(wheel, sdist)

    with zipfile.ZipFile(wheel) as archive:
        metadata_name = next(name for name in wheel_members if name.endswith(".dist-info/METADATA"))
        metadata = email.message_from_bytes(archive.read(metadata_name))
        wheel_content = b"".join(archive.read(name) for name in wheel_members)
    assert metadata.get_all("Requires-Dist") in (None, [])
    assert not any("schemas/" in name or name.startswith("schemas/") for name in wheel_members)

    forbidden_segments = ("/tests/", "/spec-dock/", "/.tmp/", "/dist/")
    assert not any(
        any(segment in f"/{name}" for segment in forbidden_segments) for name in wheel_members
    )
    assert not any(
        any(segment in f"/{name}" for segment in forbidden_segments) for name in sdist_members
    )
    assert b"do-not-publish" not in wheel_content
    with tarfile.open(sdist, "r:gz") as archive:
        for member in archive.getmembers():
            if member.isfile():
                stream = archive.extractfile(member)
                assert stream is not None
                assert b"do-not-publish" not in stream.read()


def test_wheel_installs_offline_and_cli_runs_outside_checkout_with_network_trapped(
    tmp_path: Path,
) -> None:
    wheel, _sdist = _build(tmp_path)
    environment = tmp_path / "venv"
    subprocess.run((sys.executable, "-m", "venv", str(environment)), check=True)
    python = environment / "bin" / "python"
    executable = environment / "bin" / "code-structure-viz"
    subprocess.run(
        (str(python), "-m", "pip", "install", "--no-index", str(wheel)),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
        cwd=tmp_path,
    )
    version = subprocess.run(
        (str(executable), "--version"),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
        cwd=tmp_path,
    )
    assert version.returncode == 0
    assert version.stdout == b"code-structure-viz 0.1.0.dev0\n"
    assert version.stderr == b""

    trap = tmp_path / "network-trap"
    trap.mkdir()
    (trap / "sitecustomize.py").write_text(
        "import socket\n"
        "def blocked(*args, **kwargs):\n"
        "    raise RuntimeError('network access is forbidden')\n"
        "socket.create_connection = blocked\n"
        "class BlockedSocket(socket.socket):\n"
        "    def connect(self, *args, **kwargs):\n"
        "        return blocked(*args, **kwargs)\n"
        "socket.socket = BlockedSocket\n",
        encoding="utf-8",
    )
    repository = tmp_path / "outside-repository"
    source = repository / "src" / "app" / "model.py"
    source.parent.mkdir(parents=True)
    source.write_text("class Model:\n    pass\n", encoding="utf-8")
    subprocess.run(("git", "init", "--quiet", str(repository)), check=True)
    output = tmp_path / "outside-output"
    run = subprocess.run(
        (
            str(executable),
            "snapshot",
            "--repo",
            str(repository),
            "--output-dir",
            str(output),
            "--domain",
            "python",
        ),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(trap), "NO_COLOR": "1"},
    )
    assert run.returncode == 0
    assert run.stderr == b""
    assert sorted(path.name for path in output.iterdir()) == [
        "python.snapshot.puml",
        "python.snapshot.semantic.json",
        "run-manifest.json",
    ]
    assert json.loads((output / "run-manifest.json").read_bytes())["source"]["head_commit"] is None


def test_lock_and_third_party_license_inventory_match_exactly() -> None:
    lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    locked = {
        (package["name"], package["version"])
        for package in lock["package"]
        if package["name"] != "code-structure-viz"
    }
    inventory = ROOT / "THIRD_PARTY_LICENSES.md"
    text = inventory.read_text(encoding="utf-8")
    assert "Runtime dependencies: none." in text
    rows = {
        (columns[1].strip(), columns[2].strip())
        for line in text.splitlines()
        if line.startswith("|") and (columns := line.split("|"))[1].strip() not in {"name", "---"}
    }
    assert rows == locked
    for line in text.splitlines():
        if not line.startswith("|") or line.startswith("| name") or line.startswith("| ---"):
            continue
        columns = [column.strip() for column in line.split("|")[1:-1]]
        assert len(columns) == 4
        assert columns[2] not in {"", "UNKNOWN"}
        assert columns[3].startswith("https://")


def test_pep517_backend_and_transitive_build_requirements_are_exactly_pinned() -> None:
    expected = {
        "hatchling": "1.27.0",
        "packaging": "26.3",
        "pathspec": "1.1.1",
        "pluggy": "1.6.0",
        "trove-classifiers": "2026.6.1.19",
    }
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    exact_requirements = {f"{name}=={version}" for name, version in expected.items()}

    assert set(project["build-system"]["requires"]) == exact_requirements
    assert set(project["dependency-groups"]["build"]) == exact_requirements

    lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    locked = {package["name"]: package["version"] for package in lock["package"]}
    assert {name: locked.get(name) for name in expected} == expected
    project_package = next(
        package for package in lock["package"] if package["name"] == "code-structure-viz"
    )
    build_group = project_package["dev-dependencies"]["build"]
    assert {dependency["name"] for dependency in build_group} == set(expected)

    hatchling = next(package for package in lock["package"] if package["name"] == "hatchling")
    assert {dependency["name"] for dependency in hatchling["dependencies"]} == {
        "packaging",
        "pathspec",
        "pluggy",
        "trove-classifiers",
    }
