from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path


def create_two_commit_repository(
    tmp_path: Path,
    *,
    before_text: str,
    after_text: str | None = None,
    relative_path: str = "src/app.py",
) -> tuple[Path, str, str]:
    repository = tmp_path / "repo"
    (repository / "src").mkdir(parents=True)
    _git(repository, "init", "--quiet", "--initial-branch=main")
    source = repository / relative_path
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(before_text, encoding="utf-8")
    _git(repository, "add", ".")
    _git(repository, "commit", "--quiet", "--message=before", env=_commit_env())
    before = _head(repository)
    if after_text is None:
        after_text = before_text
    source.write_text(after_text, encoding="utf-8")
    _git(repository, "add", ".")
    _git(repository, "commit", "--quiet", "--message=after", env=_commit_env())
    return repository, before, _head(repository)


def create_two_commit_repository_from_files(
    tmp_path: Path,
    *,
    before_files: Mapping[str, str],
    after_files: Mapping[str, str],
) -> tuple[Path, str, str]:
    repository = tmp_path / "repo"
    repository.mkdir(parents=True)
    _git(repository, "init", "--quiet", "--initial-branch=main")
    _write_fixture_files(repository, before_files)
    _git(repository, "add", ".")
    _git(repository, "commit", "--quiet", "--message=before", env=_commit_env())
    before = _head(repository)
    for relative_path in set(before_files) - set(after_files):
        (repository / relative_path).unlink()
    _write_fixture_files(repository, after_files)
    _git(repository, "add", ".")
    _git(repository, "commit", "--quiet", "--message=after", env=_commit_env())
    return repository, before, _head(repository)


def create_unmerged_repository(
    tmp_path: Path,
    *,
    base_text: str = "class Order:\n    amount: int\n",
) -> tuple[Path, str]:
    """Create a repository whose current working tree has one real merge conflict."""
    repository = tmp_path / "repo"
    (repository / "src").mkdir(parents=True)
    _git(repository, "init", "--quiet", "--initial-branch=main")
    source = repository / "src/app.py"
    source.write_text(base_text, encoding="utf-8")
    _git(repository, "add", ".")
    _git(repository, "commit", "--quiet", "--message=base", env=_commit_env())
    base = _head(repository)

    _git(repository, "switch", "--quiet", "--create", "side")
    source.write_text("class Order:\n    amount: str\n", encoding="utf-8")
    _git(repository, "add", ".")
    _git(repository, "commit", "--quiet", "--message=side", env=_commit_env())

    _git(repository, "switch", "--quiet", "main")
    source.write_text("class Order:\n    amount: bytes\n", encoding="utf-8")
    _git(repository, "add", ".")
    _git(repository, "commit", "--quiet", "--message=main", env=_commit_env())
    merge = subprocess.run(
        ("git", "-C", str(repository), "merge", "--no-commit", "side"),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
    )
    if merge.returncode == 0:
        raise AssertionError("fixture merge unexpectedly succeeded")
    return repository, base


def create_gitlink_repository(tmp_path: Path) -> tuple[Path, str, Path, str]:
    """Create a parent repository with a tracked gitlink whose nested HEAD moves."""
    repository = tmp_path / "repo"
    nested = repository / "src" / "component"
    (repository / "src").mkdir(parents=True)
    nested.mkdir()
    _git(repository, "init", "--quiet", "--initial-branch=main")
    _git(nested, "init", "--quiet", "--initial-branch=main")
    (nested / "README").write_text("nested before\n", encoding="utf-8")
    _git(nested, "add", ".")
    _git(nested, "commit", "--quiet", "--message=before", env=_commit_env())
    (repository / "src" / "app.py").write_text("class Order:\n    amount: int\n", encoding="utf-8")
    _git(repository, "add", ".")
    _git(repository, "commit", "--quiet", "--message=parent", env=_commit_env())
    parent_head = _head(repository)

    (nested / "README").write_text("nested after\n", encoding="utf-8")
    _git(nested, "add", ".")
    _git(nested, "commit", "--quiet", "--message=after", env=_commit_env())
    nested_head = _head(nested)
    return repository, parent_head, nested, nested_head


def create_clean_gitlink_repository(tmp_path: Path) -> tuple[Path, str, Path, str]:
    """Create a clean parent/gitlink pair whose parent OID matches nested HEAD."""
    repository = tmp_path / "repo"
    nested = repository / "src" / "component"
    (repository / "src").mkdir(parents=True)
    nested.mkdir()
    _git(repository, "init", "--quiet", "--initial-branch=main")
    _git(nested, "init", "--quiet", "--initial-branch=main")
    (nested / "README").write_text("nested clean\n", encoding="utf-8")
    _git(nested, "add", ".")
    _git(nested, "commit", "--quiet", "--message=before", env=_commit_env())
    nested_head = _head(nested)
    (repository / "src" / "app.py").write_text("class Order:\n    amount: int\n", encoding="utf-8")
    _git(repository, "add", ".")
    _git(repository, "commit", "--quiet", "--message=parent", env=_commit_env())
    return repository, _head(repository), nested, nested_head


def create_clean_linked_gitlink_repository(
    tmp_path: Path,
) -> tuple[Path, str, Path, str, Path]:
    """Create a clean gitlink whose nested checkout is a linked worktree."""
    repository = tmp_path / "repo"
    nested = repository / "src" / "component"
    seed = tmp_path / "nested-seed"
    common = repository / ".git" / "modules" / "component"
    (repository / "src").mkdir(parents=True)
    seed.mkdir()
    _git(repository, "init", "--quiet", "--initial-branch=main")
    _git(seed, "init", "--quiet", "--initial-branch=main")
    (seed / "README").write_text("nested linked clean\n", encoding="utf-8")
    _git(seed, "add", ".")
    _git(seed, "commit", "--quiet", "--message=before", env=_commit_env())
    nested_head = _head(seed)

    common.parent.mkdir(parents=True)
    subprocess.run(
        ("git", "init", "--bare", "--quiet", str(common)),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        (
            "git",
            "--git-dir",
            str(common),
            "fetch",
            "--quiet",
            str(seed),
            "HEAD:refs/heads/main",
        ),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        (
            "git",
            "--git-dir",
            str(common),
            "worktree",
            "add",
            "--quiet",
            "--detach",
            str(nested),
            "refs/heads/main",
        ),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
    )
    (repository / "src" / "app.py").write_text(
        "class Order:\n    amount: int\n",
        encoding="utf-8",
    )
    _git(repository, "add", ".")
    _git(repository, "commit", "--quiet", "--message=parent", env=_commit_env())
    return repository, _head(repository), nested, nested_head, common


def create_raw_path_collision_repository(tmp_path: Path) -> tuple[Path, str, str]:
    """Create a commit tree containing distinct NFC/NFD spellings of one path."""
    repository = tmp_path / "repo"
    (repository / "src").mkdir(parents=True)
    _git(repository, "init", "--quiet", "--initial-branch=main")
    (repository / "src" / "app.py").write_text("class Order:\n    amount: int\n", encoding="utf-8")
    _git(repository, "add", ".")
    _git(repository, "commit", "--quiet", "--message=before", env=_commit_env())
    before = _head(repository)

    app_blob = subprocess.check_output(
        ("git", "-C", str(repository), "rev-parse", f"{before}:src/app.py"),
        text=True,
    ).strip()
    composed = "café.txt".encode()
    decomposed = "cafe\u0301.txt".encode("utf-8")
    first_blob = _git_bytes(repository, "hash-object", "-w", "--stdin", input_bytes=b"nfc\n")
    second_blob = _git_bytes(repository, "hash-object", "-w", "--stdin", input_bytes=b"nfd\n")
    docs_tree = _git_bytes(
        repository,
        "mktree",
        "-z",
        input_bytes=(
            b"100644 blob "
            + first_blob
            + b"\t"
            + composed
            + b"\0"
            + b"100644 blob "
            + second_blob
            + b"\t"
            + decomposed
            + b"\0"
        ),
    )
    root_tree = _git_bytes(
        repository,
        "mktree",
        "-z",
        input_bytes=(
            b"040000 tree "
            + docs_tree
            + b"\tdocs\0"
            + b"040000 tree "
            + _git_bytes(
                repository,
                "mktree",
                "-z",
                input_bytes=b"100644 blob " + app_blob.encode("ascii") + b"\tapp.py\0",
            )
            + b"\tsrc\0"
        ),
    )
    after = _git_bytes(
        repository,
        "commit-tree",
        root_tree.decode("ascii"),
        "-p",
        before,
        input_bytes=b"collision\n",
        env=_commit_env(),
    )
    _git(repository, "update-ref", "refs/heads/collision", after.decode("ascii"))
    return repository, before, after.decode("ascii")


def create_raw_path_transition_repository(tmp_path: Path) -> tuple[Path, str]:
    """Create a synthetic NFD before commit and an NFC-spelled working-tree index."""
    repository = tmp_path / "repo"
    (repository / "src").mkdir(parents=True)
    _git(repository, "init", "--quiet", "--initial-branch=main")
    nfc_path = repository / "src" / "café.py"
    nfc_path.write_text("class Value:\n    pass\n", encoding="utf-8")
    _git(repository, "add", ".")
    _git(repository, "commit", "--quiet", "--message=before", env=_commit_env())
    content_blob = _git_bytes(
        repository,
        "hash-object",
        "-w",
        "--stdin",
        input_bytes=b"class Value:\n    pass\n",
    )
    nfd_path = "cafe\u0301.py".encode("utf-8")
    src_tree = _git_bytes(
        repository,
        "mktree",
        "-z",
        input_bytes=b"100644 blob " + content_blob + b"\t" + nfd_path + b"\0",
    )
    root_tree = _git_bytes(
        repository,
        "mktree",
        "-z",
        input_bytes=b"040000 tree " + src_tree + b"\tsrc\0",
    )
    before = _git_bytes(
        repository,
        "commit-tree",
        root_tree.decode("ascii"),
        input_bytes=b"synthetic NFD before\n",
        env=_commit_env(),
    ).decode("ascii")
    return repository, before


def run_diff_cli(
    repository: Path,
    output: Path,
    *arguments: str,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        (
            sys.executable,
            "-m",
            "code_structure_viz",
            "diff",
            "--repo",
            str(repository),
            "--output-dir",
            str(output),
            "--domain",
            "python",
            *arguments,
        ),
        cwd=repository,
        env={**os.environ, "NO_COLOR": "1"},
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
    )


def commit_current_changes(repository: Path, message: str) -> str:
    _git(repository, "add", ".")
    _git(repository, "commit", "--quiet", f"--message={message}", env=_commit_env())
    return _head(repository)


def _commit_env() -> dict[str, str]:
    return {
        **os.environ,
        "GIT_AUTHOR_NAME": "Code Structure Viz Fixture",
        "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
        "GIT_AUTHOR_DATE": "2000-01-01T00:00:00Z",
        "GIT_COMMITTER_NAME": "Code Structure Viz Fixture",
        "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
        "GIT_COMMITTER_DATE": "2000-01-01T00:00:00Z",
    }


def _head(repository: Path) -> str:
    return subprocess.check_output(
        ("git", "-C", str(repository), "rev-parse", "HEAD"),
        text=True,
    ).strip()


def _write_fixture_files(repository: Path, files: Mapping[str, str]) -> None:
    for relative_path, content in files.items():
        path = repository / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def _git(
    repository: Path,
    *arguments: str,
    env: dict[str, str] | None = None,
) -> None:
    subprocess.run(
        ("git", "-C", str(repository), *arguments),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
        env=env,
    )


def _git_bytes(
    repository: Path,
    *arguments: str,
    input_bytes: bytes,
    env: dict[str, str] | None = None,
) -> bytes:
    completed = subprocess.run(
        ("git", "-C", str(repository), *arguments),
        input=input_bytes,
        capture_output=True,
        check=True,
        env=env,
    )
    return completed.stdout.strip()
