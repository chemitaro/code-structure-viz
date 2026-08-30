from __future__ import annotations

import ast
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

from tests.helpers.acceptance import initialize_repository
from tests.helpers.diff import commit_current_changes
from tests.helpers.sqlalchemy_snapshot import run_snapshot_cli

ROOT = Path(__file__).resolve().parents[2]
SQLALCHEMY_ADAPTER_ROOT = ROOT / "src" / "code_structure_viz" / "adapters" / "sqlalchemy"
_FORBIDDEN_IMPORT_ROOTS = frozenset(
    {
        "alembic",
        "asyncpg",
        "importlib",
        "psycopg",
        "pymysql",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "subprocess",
    }
)
_FORBIDDEN_CALLS = frozenset(
    {
        "__import__",
        "compile",
        "create_engine",
        "eval",
        "exec",
        "get_source_segment",
        "import_module",
        "literal_eval",
        "unparse",
    }
)


def _repository_state(repository: Path, git: str) -> tuple[bytes, bytes, bytes]:
    def capture(*arguments: str) -> bytes:
        return subprocess.run(
            (git, "-C", str(repository), *arguments),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=True,
        ).stdout

    index = repository / ".git" / "index"
    return (
        capture("rev-parse", "HEAD"),
        capture("status", "--porcelain=v1", "-z", "--untracked-files=all"),
        hashlib.sha256(index.read_bytes()).digest(),
    )


def test_sqlalchemy_adapter_has_no_runtime_loader_evaluator_or_side_effect_dependency() -> None:
    forbidden_imports: list[tuple[str, str]] = []
    forbidden_calls: list[tuple[str, str]] = []
    parse_calls: list[str] = []

    for path in sorted(SQLALCHEMY_ADAPTER_ROOT.glob("*.py")):
        relative = path.relative_to(ROOT).as_posix()
        tree = ast.parse(path.read_bytes(), filename=relative)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".", 1)[0] in _FORBIDDEN_IMPORT_ROOTS:
                        forbidden_imports.append((relative, alias.name))
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                if node.module.split(".", 1)[0] in _FORBIDDEN_IMPORT_ROOTS:
                    forbidden_imports.append((relative, node.module))
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in _FORBIDDEN_CALLS:
                    forbidden_calls.append((relative, node.func.id))
                elif isinstance(node.func, ast.Attribute) and node.func.attr in _FORBIDDEN_CALLS - {
                    "compile",
                    "eval",
                    "exec",
                }:
                    forbidden_calls.append((relative, node.func.attr))
                if (
                    isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "ast"
                    and node.func.attr == "parse"
                ):
                    parse_calls.append(relative)

    assert forbidden_imports == []
    assert forbidden_calls == []
    assert parse_calls == ["src/code_structure_viz/adapters/sqlalchemy/analyzer.py"]


def test_sqlalchemy_cli_never_executes_target_and_redacts_every_public_channel(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repo"
    source = repository / "src" / "models.py"
    source.parent.mkdir(parents=True)
    sentinel = repository / "TARGET_CODE_EXECUTED"
    private_literal = "DO_NOT_PUBLISH_sql_default_or_query"
    source.write_text(
        "from pathlib import Path\n"
        "import socket\n"
        "import sqlite3\n"
        "from sqlalchemy import CheckConstraint, String\n"
        "from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column\n"
        f"Path({str(sentinel)!r}).write_text('executed', encoding='utf-8')\n"
        "sqlite3.connect(':memory:')\n"
        "socket.create_connection(('example.invalid', 9))\n"
        "raise RuntimeError('target code must not execute')\n"
        "class Base(DeclarativeBase): pass\n"
        "class Safe(Base):\n"
        "    __tablename__ = 'safe'\n"
        f"    __table_args__ = (CheckConstraint({private_literal!r}, name='safe_check'),)\n"
        f"    value: Mapped[str] = mapped_column(String(255), default={private_literal!r})\n",
        encoding="utf-8",
    )
    initialize_repository(repository)
    git = shutil.which("git")
    assert git is not None
    before = _repository_state(repository, git)
    output = tmp_path / "output"

    result = run_snapshot_cli(
        repository,
        output,
        "--stdout",
        "sqlalchemy:semantic-json",
    )

    assert result.returncode == 0, result.stderr
    assert result.stderr == b""
    assert not sentinel.exists()
    assert _repository_state(repository, git) == before
    public_bytes = (
        result.stdout
        + result.stderr
        + b"".join(path.read_bytes() for path in sorted(output.iterdir()))
    )
    for private in (
        private_literal.encode(),
        str(sentinel).encode(),
        str(repository).encode(),
        str(output).encode(),
        b"TARGET_CODE_EXECUTED",
        b"target code must not execute",
        b"example.invalid",
        b":memory:",
        b"Traceback",
    ):
        assert private not in public_bytes


def test_sqlalchemy_diff_never_executes_target_or_publishes_raw_values(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repo"
    source = repository / "src" / "models.py"
    source.parent.mkdir(parents=True)
    sentinel = repository / "DIFF_TARGET_EXECUTED"
    secret = "DO_NOT_PUBLISH_SQLALCHEMY_DIFF_SECRET"
    prefix = (
        "from pathlib import Path\n"
        "from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column\n"
        f"Path({str(sentinel)!r}).write_text('executed', encoding='utf-8')\n"
        "class Base(DeclarativeBase): pass\n"
        "class User(Base):\n"
        "    __tablename__ = 'users'\n"
    )
    source.write_text(
        prefix + f"    value: Mapped[str] = mapped_column(default={secret!r}, nullable=True)\n",
        encoding="utf-8",
    )
    initialize_repository(repository)
    before_commit = subprocess.check_output(
        ("git", "-C", str(repository), "rev-parse", "HEAD"), text=True
    ).strip()
    source.write_text(
        prefix + f"    value: Mapped[str] = mapped_column(default={secret!r}, nullable=False)\n",
        encoding="utf-8",
    )
    after_commit = commit_current_changes(repository, "after")
    git = shutil.which("git")
    assert git is not None
    before_state = _repository_state(repository, git)
    output = tmp_path / "output"

    result = subprocess.run(
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
            "sqlalchemy",
            "--from",
            before_commit,
            "--to",
            after_commit,
        ),
        cwd=repository,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert not sentinel.exists()
    assert _repository_state(repository, git) == before_state
    public = (
        result.stdout
        + result.stderr
        + b"".join(path.read_bytes() for path in sorted(output.iterdir()))
    )
    for private in (
        secret.encode(),
        str(sentinel).encode(),
        str(repository).encode(),
        str(output).encode(),
        b"DIFF_TARGET_EXECUTED",
    ):
        assert private not in public
