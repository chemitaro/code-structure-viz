import json
from pathlib import Path

from tests.helpers.acceptance import initialize_repository, run_cli


def _repository_with_classes(tmp_path: Path, count: int) -> Path:
    repository = tmp_path / "repo"
    source = repository / "src" / "app" / "entities.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        "\n\n".join(f"class Entity{index}:\n    pass" for index in range(count)) + "\n",
        encoding="utf-8",
    )
    initialize_repository(repository)
    return repository


def test_default_entity_budget_admits_exactly_500_classes(tmp_path: Path) -> None:
    repository = _repository_with_classes(tmp_path, 500)
    output = tmp_path / "output"

    result = run_cli(repository, output)

    assert result.returncode == 0
    assert result.stderr == b""
    manifest = json.loads((output / "run-manifest.json").read_bytes())
    assert manifest["domains"][0]["budget"] == {
        "name": "max_entities",
        "requested": None,
        "resolved": 500,
        "actual": 500,
        "source": "builtin",
    }


def test_default_entity_budget_rejects_501_without_truncation_or_payload(
    tmp_path: Path,
) -> None:
    repository = _repository_with_classes(tmp_path, 501)
    output = tmp_path / "output"

    result = run_cli(repository, output)

    assert result.returncode == 3
    assert sorted(path.name for path in output.iterdir()) == ["run-manifest.json"]
    assert json.loads(result.stderr)["code"] == "CSV-PY-010"
    manifest = json.loads((output / "run-manifest.json").read_bytes())
    domain = manifest["domains"][0]
    assert domain["incomplete_kind"] == "payload_unavailable"
    assert domain["entity_count"] == 501
    assert domain["coverage"]["selected_entities"] == 501
    assert domain["budget"]["actual"] == 501


def test_positive_cli_budget_override_admits_600_classes(tmp_path: Path) -> None:
    repository = _repository_with_classes(tmp_path, 600)
    output = tmp_path / "output"

    result = run_cli(repository, output, "--max-entities", "600")

    assert result.returncode == 0
    manifest = json.loads((output / "run-manifest.json").read_bytes())
    assert manifest["domains"][0]["budget"] == {
        "name": "max_entities",
        "requested": 600,
        "resolved": 600,
        "actual": 600,
        "source": "cli",
    }


def test_arbitrarily_long_cli_budget_reaches_config_digest_and_publication(
    tmp_path: Path,
) -> None:
    repository = _repository_with_classes(tmp_path, 1)
    output = tmp_path / "output"
    value = "9" * 10_000

    result = run_cli(repository, output, "--max-entities", value)

    assert result.returncode == 0, result.stderr
    manifest = (output / "run-manifest.json").read_bytes()
    assert b'"requested":' + value.encode("ascii") in manifest
    assert b'"resolved":' + value.encode("ascii") in manifest


def test_invalid_cli_budget_is_usage_error_before_output(tmp_path: Path) -> None:
    repository = _repository_with_classes(tmp_path, 1)
    output = tmp_path / "output"

    result = run_cli(repository, output, "--max-entities", "0")

    assert result.returncode == 2
    assert result.stdout == b""
    assert json.loads(result.stderr)["code"] == "CSV-USAGE-001"
    assert not output.exists()
