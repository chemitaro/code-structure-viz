from __future__ import annotations

import ast
import hashlib
import json
import os
import shutil
import stat
import subprocess
from pathlib import Path, PurePosixPath

import pytest

from code_structure_viz.adapters.python.analyzer import PythonSnapshotAnalyzer
from code_structure_viz.adapters.python.module_index import PythonModuleIndex
from code_structure_viz.core.config import PythonConfig
from code_structure_viz.source.source_view import SourceFile, SourceFileKind, SourceView
from tests.helpers.acceptance import initialize_fixture_repository, run_cli

ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = ROOT / "src" / "code_structure_viz"
_FORBIDDEN_IMPORT_ROOTS = frozenset(
    {
        "compileall",
        "importlib",
        "jsonschema",
        "py_compile",
        "runpy",
        "sqlalchemy",
        "pyclassuml",
        "tree_git_diff",
    }
)
_FORBIDDEN_DIRECT_CALLS = frozenset(
    {"__import__", "compile", "eval", "exec", "import_module", "load_entry_point"}
)


def _production_trees() -> list[tuple[Path, ast.Module]]:
    return [
        (path, ast.parse(path.read_text(encoding="utf-8"), filename=str(path)))
        for path in sorted(SOURCE_ROOT.rglob("*.py"))
    ]


def _repository_state(repository: Path, git: str) -> tuple[bytes, bytes, bytes, bytes]:
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
        capture("show-ref", "--head"),
        capture("status", "--porcelain=v1", "-z", "--untracked-files=all"),
        hashlib.sha256(index.read_bytes()).digest(),
    )


def test_production_has_one_closed_ast_path_and_no_target_execution_loader() -> None:
    forbidden_imports: list[tuple[str, str]] = []
    forbidden_calls: list[tuple[str, str]] = []
    subprocess_calls: list[str] = []
    ast_calls: list[str] = []

    for path, tree in _production_trees():
        relative = path.relative_to(ROOT).as_posix()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".", 1)[0]
                    if root in _FORBIDDEN_IMPORT_ROOTS:
                        forbidden_imports.append((relative, alias.name))
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                root = node.module.split(".", 1)[0]
                if root in _FORBIDDEN_IMPORT_ROOTS:
                    forbidden_imports.append((relative, node.module))
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in _FORBIDDEN_DIRECT_CALLS:
                    forbidden_calls.append((relative, node.func.id))
                elif isinstance(node.func, ast.Attribute) and node.func.attr in {
                    "import_module",
                    "load_entry_point",
                }:
                    forbidden_calls.append((relative, node.func.attr))
                if (
                    isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "subprocess"
                    and node.func.attr == "run"
                ):
                    subprocess_calls.append(relative)
                if (
                    isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "ast"
                    and node.func.attr == "parse"
                ):
                    ast_calls.append(relative)

    assert forbidden_imports == []
    assert forbidden_calls == []
    assert subprocess_calls == ["src/code_structure_viz/source/git_repository.py"]
    assert ast_calls == [
        "src/code_structure_viz/adapters/python/analyzer.py",
        "src/code_structure_viz/adapters/python/type_expr.py",
    ]


def test_analyzer_uses_python_312_ast_parse_and_ignores_dynamic_import_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = b"""
import app.static
class Safe:
    pass
__import__('secret.module')
importlib.import_module('another.module')
loader = __import__
loader('third.module')
"""
    source_file = SourceFile(
        PurePosixPath("src/app/dynamic.py"),
        SourceFileKind.REGULAR,
        None,
        len(source),
        hashlib.sha256(source).hexdigest(),
        source,
    )
    view = SourceView(None, (source_file,), (), "0" * 64)
    config = PythonConfig(("src",), ("**/*.py",), ())
    original_parse = ast.parse
    observed: list[dict[str, object]] = []

    def parse_spy(
        source_text: str | bytes,
        filename: str = "<unknown>",
        mode: str = "exec",
        *,
        type_comments: bool = False,
        feature_version: int | tuple[int, int] | None = None,
    ) -> ast.AST:
        observed.append(
            {
                "filename": filename,
                "mode": mode,
                "type_comments": type_comments,
                "feature_version": feature_version,
            }
        )
        return original_parse(
            source_text,
            filename=filename,
            mode=mode,
            type_comments=type_comments,
            feature_version=feature_version,
        )

    monkeypatch.setattr(ast, "parse", parse_spy)
    result = PythonSnapshotAnalyzer().analyze(PythonModuleIndex.build(view, config))

    assert observed == [
        {
            "filename": "src/app/dynamic.py",
            "mode": "exec",
            "type_comments": False,
            "feature_version": (3, 12),
        }
    ]
    assert [binding.local_name for binding in result.modules[0].bindings] == ["app"]
    assert all("secret" not in relation.target.name for relation in result.relations)
    assert all("another" not in item.reference for item in result.frontier)
    assert all("third" not in item.message for item in result.diagnostics)


def test_cli_never_executes_security_fixture_and_preserves_repository_and_git_allowlist(
    tmp_path: Path,
) -> None:
    repository = initialize_fixture_repository(tmp_path, "security")
    output = tmp_path / "output"
    real_git = shutil.which("git")
    assert real_git is not None
    before = _repository_state(repository, real_git)
    shim = tmp_path / "bin" / "git"
    shim.parent.mkdir()
    shim.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        "with open(os.environ['CSV_GIT_LOG'], 'a', encoding='utf-8') as stream:\n"
        "    stream.write(json.dumps(sys.argv[1:], separators=(',', ':')) + '\\n')\n"
        "os.execv(os.environ['CSV_REAL_GIT'], [os.environ['CSV_REAL_GIT'], *sys.argv[1:]])\n",
        encoding="utf-8",
    )
    shim.chmod(shim.stat().st_mode | stat.S_IXUSR)
    command_log = tmp_path / "git-commands.jsonl"

    result = run_cli(
        repository,
        output,
        environment={
            "PATH": f"{shim.parent}{os.pathsep}{os.environ['PATH']}",
            "CSV_GIT_LOG": str(command_log),
            "CSV_REAL_GIT": real_git,
        },
    )

    assert result.returncode == 0
    assert result.stderr == b""
    assert not (repository / "TARGET_CODE_EXECUTED").exists()
    assert _repository_state(repository, real_git) == before
    public_bytes = (
        result.stdout
        + result.stderr
        + b"".join(path.read_bytes() for path in sorted(output.iterdir()))
    )
    for private in (
        b"do-not-publish",
        b"TARGET_CODE_EXECUTED",
        b"target code must not execute",
        str(repository).encode(),
        str(output).encode(),
        b"Traceback",
    ):
        assert private not in public_bytes

    commands = [json.loads(line) for line in command_log.read_text(encoding="utf-8").splitlines()]
    allowed_suffixes = {
        ("--version",),
        ("rev-parse", "--show-toplevel"),
        ("rev-parse", "--verify", "HEAD^{commit}"),
        ("ls-files", "-z", "--cached", "--others", "--exclude-standard"),
    }
    observed_suffixes: list[tuple[str, ...]] = []
    for command in commands:
        assert isinstance(command, list)
        values = tuple(str(value) for value in command)
        suffix: tuple[str, ...]
        if values == ("--version",):
            suffix = values
        else:
            assert values[:4] == ("-C", str(repository), "-c", "core.fsmonitor=false")
            suffix = values[4:]
        assert suffix in allowed_suffixes
        observed_suffixes.append(suffix)
    assert observed_suffixes == [
        ("--version",),
        ("rev-parse", "--show-toplevel"),
        ("rev-parse", "--verify", "HEAD^{commit}"),
        ("ls-files", "-z", "--cached", "--others", "--exclude-standard"),
        ("rev-parse", "--verify", "HEAD^{commit}"),
        ("ls-files", "-z", "--cached", "--others", "--exclude-standard"),
    ]


def test_classless_plantuml_declares_every_module_alias_before_relations(tmp_path: Path) -> None:
    repository = initialize_fixture_repository(tmp_path, "module_only")
    output = tmp_path / "output"

    result = run_cli(
        repository,
        output,
        "--target",
        "module:app.a",
        "--upstream-depth",
        "0",
        "--downstream-depth",
        "1",
    )

    assert result.returncode == 0
    lines = (output / "python.snapshot.puml").read_text(encoding="utf-8").splitlines()
    declarations = [
        line.rsplit(" as ", 1)[1].removesuffix(" {")
        for line in lines
        if line.startswith('package "')
    ]
    relations = [line for line in lines if " ..> " in line and line.startswith("M_")]
    assert len(declarations) == len(set(declarations)) == 2
    assert len(relations) == 1
    left, right = relations[0].split(" ..> ", 1)
    assert left in declarations
    assert right.split(" : ", 1)[0] in declarations
