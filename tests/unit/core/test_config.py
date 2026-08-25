from pathlib import Path

import pytest

from code_structure_viz.cli.parser import SnapshotCliRequest, parse_cli
from code_structure_viz.core.config import ConfigResolutionError, resolve_config
from code_structure_viz.core.diagnostics import encode_diagnostic_jsonl


def _request(repo: Path, output: Path, *extra: str) -> SnapshotCliRequest:
    return parse_cli(
        [
            "snapshot",
            "--repo",
            str(repo),
            "--output-dir",
            str(output),
            "--domain",
            "python",
            *extra,
        ]
    )


def test_builtin_config_has_exact_values_sources_and_digest(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    config = resolve_config(_request(repo, tmp_path / "output"), repo)

    assert config.schema == "code-structure-viz.config/v1"
    assert config.python.source_roots == ("src", ".")
    assert config.python.include == ("**/*.py",)
    assert config.python.exclude == ()
    assert config.traversal.upstream_depth == 1
    assert config.traversal.downstream_depth == 1
    assert config.limits.max_entities == 500
    assert config.source.value == "builtin"
    assert config.value_sources.max_entities.value == "builtin"
    assert config.sha256 == "4e133650cbb25563a49d9838df964a7ceda9fc5613100678eee80a58e16de4cd"


def test_repository_config_is_replaced_by_explicit_config_then_cli_overrides(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "pkg").mkdir()
    (repo / ".code-structure-viz.toml").write_text(
        """schema = "code-structure-viz.config/v1"
[python]
source_roots = ["src"]
include = ["**/*.py"]
exclude = []
[traversal]
upstream_depth = 2
downstream_depth = 2
[limits]
max_entities = 200
""",
        encoding="utf-8",
    )
    explicit = tmp_path / "explicit.toml"
    explicit.write_text(
        """schema = "code-structure-viz.config/v1"
[python]
source_roots = ["pkg"]
include = ["**/*.py"]
exclude = ["**/generated.py"]
[traversal]
upstream_depth = 3
downstream_depth = 4
[limits]
max_entities = 300
""",
        encoding="utf-8",
    )

    config = resolve_config(
        _request(
            repo,
            tmp_path / "output",
            "--config",
            str(explicit),
            "--target",
            "module:pkg.item",
            "--upstream-depth",
            "0",
            "--max-entities",
            "600",
        ),
        repo,
    )

    assert config.python.source_roots == ("pkg",)
    assert config.python.exclude == ("**/generated.py",)
    assert config.traversal.upstream_depth == 0
    assert config.traversal.downstream_depth == 4
    assert config.limits.max_entities == 600
    assert config.source.value == "explicit"
    assert config.value_sources.upstream_depth.value == "cli"
    assert config.value_sources.downstream_depth.value == "explicit"
    assert config.value_sources.max_entities.value == "cli"


def test_unknown_config_key_uses_constant_redacted_diagnostic(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    sentinel = "/tmp/secret-do-not-emit"
    config_path = tmp_path / "malicious.toml"
    config_path.write_text(
        f'''schema = "code-structure-viz.config/v1"
[python]
source_roots = ["."]
include = ["**/*.py"]
exclude = []
[traversal]
upstream_depth = 1
downstream_depth = 1
[limits]
max_entities = 500
"{sentinel}" = true
''',
        encoding="utf-8",
    )

    with pytest.raises(ConfigResolutionError) as caught:
        resolve_config(_request(repo, tmp_path / "output", "--config", str(config_path)), repo)

    encoded = encode_diagnostic_jsonl((caught.value.diagnostic,))
    assert caught.value.diagnostic.code.value == "CSV-CONFIG-003"
    assert caught.value.diagnostic.message == "Configuration contains an unknown key."
    assert caught.value.diagnostic.domain is None
    assert caught.value.diagnostic.path is None
    assert sentinel.encode() not in encoded


@pytest.mark.parametrize(
    ("source_root", "include"),
    [("missing", "**/*.py"), (".", "[abc].py"), (".", "../*.py")],
)
def test_explicit_config_rejects_unsafe_root_or_glob(
    tmp_path: Path, source_root: str, include: str
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    config_path = tmp_path / "invalid.toml"
    config_path.write_text(
        f'''schema = "code-structure-viz.config/v1"
[python]
source_roots = ["{source_root}"]
include = ["{include}"]
exclude = []
[traversal]
upstream_depth = 1
downstream_depth = 1
[limits]
max_entities = 500
''',
        encoding="utf-8",
    )

    with pytest.raises(ConfigResolutionError) as caught:
        resolve_config(_request(repo, tmp_path / "output", "--config", str(config_path)), repo)

    assert caught.value.diagnostic.code.value == "CSV-CONFIG-004"
