import json
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import pytest
from jsonschema import Draft202012Validator, ValidationError  # type: ignore[import-untyped]
from referencing import Registry, Resource

from code_structure_viz.adapters.sqlalchemy.model import (
    SqlAlchemyCoverage,
    SqlAlchemyRedactionSummary,
    SqlAlchemySnapshot,
)
from code_structure_viz.adapters.sqlalchemy.semantic_json import render_semantic_snapshot
from code_structure_viz.source.source_view import SourceView
from tests.helpers.acceptance import (
    initialize_fixture_repository,
    initialize_repository,
    run_cli,
)
from tests.helpers.diff import create_two_commit_repository_from_files, run_diff_cli
from tests.helpers.sqlalchemy_snapshot import (
    initialize_sqlalchemy_fixture_repository,
)
from tests.helpers.sqlalchemy_snapshot import (
    run_snapshot_cli as run_sqlalchemy_snapshot_cli,
)

ROOT = Path(__file__).resolve().parents[2]
SEMANTIC_GOLDEN_ROOT = ROOT / "tests" / "golden" / "python_snapshot"


def _schema(name: str) -> dict[str, object]:
    return cast(
        dict[str, object],
        json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8")),
    )


def _validator(name: str) -> Draft202012Validator:
    diagnostic_schema = _schema("diagnostic-v1.schema.json")
    registry = Registry().with_resource(
        "urn:code-structure-viz:schema:diagnostic-v1",
        Resource.from_contents(diagnostic_schema),
    )
    return Draft202012Validator(_schema(name), registry=registry)


@pytest.mark.parametrize(
    "name",
    [
        "diagnostic-v1.schema.json",
        "file-change-set-v1.schema.json",
        "run-manifest-v1.schema.json",
        "run-summary-v1.schema.json",
        "semantic-v1.schema.json",
        "stdout-result-v1.schema.json",
    ],
)
def test_checked_in_schema_is_valid_and_closed(name: str) -> None:
    schema = _schema(name)

    Draft202012Validator.check_schema(schema)
    assert schema["additionalProperties"] is False


def test_diagnostic_schema_accepts_exact_vector_and_rejects_extra_field() -> None:
    value = {
        "type": "diagnostic",
        "schema": "code-structure-viz.diagnostic/v1",
        "code": "CSV-PY-003",
        "severity": "error",
        "domain": "python",
        "path": "src/broken.py",
        "symbol": None,
        "line": 7,
        "recoverable": True,
        "message": "Python source could not be parsed with the v1 Python 3.12 grammar.",
    }
    _validator("diagnostic-v1.schema.json").validate(value)

    with pytest.raises(ValidationError):
        _validator("diagnostic-v1.schema.json").validate({**value, "source": "secret"})


@pytest.mark.parametrize(
    "code_message",
    (
        (
            "CSV-DIFF-001",
            "Comparison endpoint or implicit base could not be resolved safely.",
        ),
        (
            "CSV-DIFF-002",
            "Changed path count exceeds the resolved comparison limit.",
        ),
        (
            "CSV-DIFF-003",
            "Git changed-path metadata could not be read safely.",
        ),
    ),
)
def test_diagnostic_schema_accepts_diff_diagnostic_vectors(
    code_message: tuple[str, str],
) -> None:
    code, message = code_message
    _validator("diagnostic-v1.schema.json").validate(
        {
            "type": "diagnostic",
            "schema": "code-structure-viz.diagnostic/v1",
            "code": code,
            "severity": "error",
            "domain": None,
            "path": None,
            "symbol": None,
            "line": None,
            "recoverable": False,
            "message": message,
        }
    )


@pytest.mark.parametrize(
    ("name", "value"),
    [
        (
            "run-summary-v1.schema.json",
            {
                "type": "run_summary",
                "schema": "code-structure-viz.run-summary/v1",
                "run_status": "fatal",
                "exit_code": 1,
                "domains": [],
                "manifest": None,
            },
        ),
        (
            "run-summary-v1.schema.json",
            {
                "type": "run_summary",
                "schema": "code-structure-viz.run-summary/v1",
                "run_status": "complete",
                "exit_code": 0,
                "domains": [{"domain": "sqlalchemy", "status": "complete"}],
                "manifest": "run-manifest.json",
            },
        ),
        (
            "stdout-result-v1.schema.json",
            {
                "type": "stdout_result",
                "schema": "code-structure-viz.stdout-result/v1",
                "selector": "python:semantic-json",
                "availability": False,
                "domain_status": "not_applicable",
                "stable_reason": "domain_not_applicable",
                "artifact": None,
            },
        ),
        (
            "stdout-result-v1.schema.json",
            {
                "type": "stdout_result",
                "schema": "code-structure-viz.stdout-result/v1",
                "selector": "sqlalchemy:plantuml",
                "availability": False,
                "domain_status": "incomplete",
                "stable_reason": "domain_payload_unavailable",
                "artifact": None,
            },
        ),
        (
            "stdout-result-v1.schema.json",
            {
                "type": "stdout_result",
                "schema": "code-structure-viz.stdout-result/v1",
                "selector": "manifest",
                "availability": False,
                "run_status": "fatal",
                "stable_reason": "final_manifest_unavailable",
                "artifact": None,
            },
        ),
    ],
)
def test_stream_contract_schema_accepts_closed_positive_vectors(
    name: str, value: dict[str, object]
) -> None:
    _validator(name).validate(value)


def test_semantic_schema_accepts_zero_class_vector_and_rejects_shape_mutations() -> None:
    value = {
        "type": "semantic_snapshot",
        "schema": "code-structure-viz.semantic/v1",
        "domain": "python",
        "document_kind": "snapshot",
        "status": "complete",
        "source": {
            "schema": "code-structure-viz.source-view/v1",
            "kind": "working-tree",
            "head_commit": None,
            "fingerprint": "b" * 64,
            "file_count": 2,
        },
        "request": {"targets": [], "upstream_depth": 1, "downstream_depth": 1},
        "coverage": {
            "candidate_files": 2,
            "parsed_files": 2,
            "failed_files": [],
            "selected_modules": ["app.a", "app.b"],
            "selected_entities": 0,
            "frontier": [],
        },
        "entities": [],
        "members": [],
        "relations": [],
        "diagnostics": [],
    }
    validator = _validator("semantic-v1.schema.json")
    validator.validate(value)

    with pytest.raises(ValidationError):
        validator.validate({**value, "absolute_path": "/private/secret"})
    with pytest.raises(ValidationError):
        validator.validate({**value, "status": "incomplete"})
    with pytest.raises(ValidationError):
        validator.validate({**value, "entities": None})


def _sqlalchemy_semantic_vector() -> dict[str, Any]:
    table_id = f"sqlalchemy:table:{'1' * 64}"
    target_table_id = f"sqlalchemy:table:{'2' * 64}"
    row_ids = [f"sqlalchemy:row:{index:064x}" for index in range(1, 10)]
    source = {"path": "src/models.py", "range": {"start_line": 1, "end_line": 1}}
    absent = {"present": False, "category": "absent", "redacted": False}
    present = {"present": True, "category": "literal", "redacted": True}
    internal_target = {
        "resolution": "internal",
        "kind": "table",
        "id": target_table_id,
        "schema_name": None,
        "table_name": "target",
        "symbol": None,
        "display_name": "<default>.target",
    }
    source_target = {
        "resolution": "internal",
        "kind": "table",
        "id": table_id,
        "schema_name": None,
        "table_name": "source",
        "symbol": None,
        "display_name": "<default>.source",
    }
    common = {"owner_id": table_id, "name": None, "source": source}
    members = [
        {
            "id": row_ids[0],
            **common,
            "kind": "column",
            "name": "id",
            "type": {
                "category": "integer",
                "name": "sqlalchemy.Integer",
                "parameters": absent,
            },
            "nullable": False,
            "primary_key": True,
            "unique": False,
            "index": False,
            "default": present,
            "server_default": absent,
            "onupdate": absent,
            "server_onupdate": absent,
            "computed": absent,
            "identity": absent,
        },
        {"id": row_ids[1], **common, "kind": "primary_key", "columns": ["id"]},
        {"id": row_ids[2], **common, "kind": "unique", "columns": ["email"]},
        {"id": row_ids[3], **common, "kind": "check", "expression": present},
        {
            "id": row_ids[4],
            **common,
            "kind": "index",
            "unique": False,
            "terms": [
                {"kind": "column", "column_name": "email", "expression": absent},
                {"kind": "expression", "column_name": None, "expression": present},
            ],
        },
        {
            "id": row_ids[5],
            **common,
            "kind": "foreign_key",
            "local_columns": ["target_id"],
            "target": internal_target,
            "target_columns": ["id"],
            "ondelete": absent,
            "onupdate": absent,
        },
        {
            "id": row_ids[6],
            **common,
            "kind": "relationship",
            "name": "target",
            "target": internal_target,
            "cardinality": "scalar",
            "uselist": False,
            "back_populates": None,
            "secondary": None,
            "primaryjoin": present,
            "secondaryjoin": absent,
            "order_by": absent,
            "foreign_keys": absent,
        },
        {
            "id": row_ids[7],
            **common,
            "kind": "inheritance",
            "target": internal_target,
        },
        {
            "id": row_ids[8],
            **common,
            "owner_id": target_table_id,
            "kind": "association_table",
            "name": "target",
            "source_table": source_target,
            "relationship_target": internal_target,
            "relationship_member_id": row_ids[6],
        },
    ]
    mapping_source = {
        "kind": "declarative_class",
        "module": "models",
        "symbol": "models.Source",
        "source": source,
    }
    return {
        "type": "semantic_snapshot",
        "schema": "code-structure-viz.semantic/v1",
        "domain": "sqlalchemy",
        "document_kind": "snapshot",
        "status": "incomplete",
        "incomplete_kind": "partial_safe",
        "source": {
            "schema": "code-structure-viz.source-view/v1",
            "kind": "working-tree",
            "head_commit": None,
            "fingerprint": "b" * 64,
            "file_count": 1,
        },
        "request": {
            "targets": [{"kind": "class", "value": "models.Source"}],
            "upstream_depth": 1,
            "downstream_depth": 2,
        },
        "coverage": {
            "candidate_files": 1,
            "parsed_files": 1,
            "failed_files": [],
            "evidence_files": ["src/models.py"],
            "selected_modules": ["models"],
            "mapped_classes": 1,
            "association_tables": 1,
            "selected_entities": 2,
            "unknown_declarations": 1,
            "frontier": [
                {
                    "direction": "failure",
                    "kind": "row",
                    "reference": f"sqlalchemy:occurrence:{'a' * 64}",
                    "reason": "unsupported_pattern",
                }
            ],
            "redaction": {
                "rule_version": "code-structure-viz.sqlalchemy-redaction/v1",
                "redacted_values": 4,
            },
        },
        "entities": [
            {
                "id": table_id,
                "kind": "table",
                "schema_name": None,
                "name": "source",
                "display_name": "<default>.source",
                "mapping_kind": "declarative_class",
                "mapping_sources": [mapping_source],
            },
            {
                "id": target_table_id,
                "kind": "table",
                "schema_name": None,
                "name": "target",
                "display_name": "<default>.target",
                "mapping_kind": "table",
                "mapping_sources": [
                    {
                        **mapping_source,
                        "kind": "table",
                        "symbol": "models.target_table",
                    }
                ],
            },
        ],
        "members": members,
        "relations": [
            {
                "id": f"sqlalchemy:relation:{'3' * 64}",
                "kind": "relationship",
                "source_id": table_id,
                "target": internal_target,
                "via_member_id": row_ids[6],
                "role": "target",
                "source": source,
            }
        ],
        "diagnostics": [
            {
                "type": "diagnostic",
                "schema": "code-structure-viz.diagnostic/v1",
                "code": "CSV-SA-009",
                "severity": "warning",
                "domain": "sqlalchemy",
                "path": "src/models.py",
                "symbol": f"sqlalchemy:occurrence:{'a' * 64}",
                "line": 1,
                "recoverable": True,
                "message": "SQLAlchemy row declaration could not be represented safely.",
            }
        ],
    }


def test_semantic_schema_accepts_closed_sqlalchemy_snapshot_variants() -> None:
    validator = _validator("semantic-v1.schema.json")
    partial = _sqlalchemy_semantic_vector()
    validator.validate(partial)

    complete = deepcopy(partial)
    complete["status"] = "complete"
    complete.pop("incomplete_kind")
    complete["diagnostics"] = []
    complete["coverage"]["unknown_declarations"] = 0
    complete["coverage"]["frontier"] = []
    validator.validate(complete)


def test_semantic_schema_rejects_unknown_sqlalchemy_values_from_complete_snapshot() -> None:
    validator = _validator("semantic-v1.schema.json")
    complete = _sqlalchemy_semantic_vector()
    complete["status"] = "complete"
    complete.pop("incomplete_kind")
    complete["diagnostics"] = []
    complete["coverage"]["unknown_declarations"] = 0
    complete["coverage"]["frontier"] = []

    mutations = []
    unknown_type = deepcopy(complete)
    unknown_type["members"][0]["type"] = {
        "category": "unknown",
        "name": None,
        "parameters": {"present": False, "category": "absent", "redacted": False},
    }
    mutations.append(unknown_type)
    unknown_descriptor = deepcopy(complete)
    unknown_descriptor["members"][0]["default"] = {
        "present": True,
        "category": "unknown",
        "redacted": True,
    }
    mutations.append(unknown_descriptor)
    unknown_target = deepcopy(complete)
    unknown_target["members"][6]["target"] = {
        "resolution": "unknown",
        "kind": "unknown",
        "id": None,
        "schema_name": None,
        "table_name": None,
        "symbol": None,
        "display_name": "<unknown>",
    }
    mutations.append(unknown_target)
    unknown_cardinality = deepcopy(complete)
    unknown_cardinality["members"][6]["cardinality"] = "unknown"
    mutations.append(unknown_cardinality)

    for mutation in mutations:
        with pytest.raises(ValidationError):
            validator.validate(mutation)

    partial = _sqlalchemy_semantic_vector()
    partial["members"][6]["cardinality"] = "unknown"
    validator.validate(partial)


@pytest.mark.parametrize(
    "reference",
    [
        "/private/secret.py",
        "../secret.py",
        "src/../secret.py",
        "https://example.invalid/secret",
        "C:/secret.py",
        "src\\secret.py",
        "row\u0000secret",
    ],
)
def test_semantic_schema_rejects_unsafe_sqlalchemy_frontier_reference(
    reference: str,
) -> None:
    value = _sqlalchemy_semantic_vector()
    value["coverage"]["frontier"][0]["reference"] = reference

    with pytest.raises(ValidationError):
        _validator("semantic-v1.schema.json").validate(value)


def test_semantic_schema_accepts_actual_sqlalchemy_renderer_bytes() -> None:
    coverage = SqlAlchemyCoverage(
        candidate_files=0,
        parsed_files=0,
        failed_files=(),
        evidence_files=(),
        selected_modules=(),
        mapped_classes=0,
        association_tables=0,
        selected_entities=0,
        unknown_declarations=0,
        frontier=(),
        redaction=SqlAlchemyRedactionSummary.create(0),
    )
    snapshot = SqlAlchemySnapshot((), (), (), coverage, (), partial_safe=False)
    rendered = render_semantic_snapshot(
        snapshot,
        SourceView(None, (), (), "b" * 64),
        (),
        1,
        1,
    )

    _validator("semantic-v1.schema.json").validate(json.loads(rendered))


def test_semantic_schema_rejects_sqlalchemy_cross_domain_and_raw_shape_mutations() -> None:
    validator = _validator("semantic-v1.schema.json")
    value = _sqlalchemy_semantic_vector()

    mutations = []
    sql_diff = deepcopy(value)
    sql_diff["type"] = "semantic_diff"
    sql_diff["document_kind"] = "diff"
    mutations.append(sql_diff)
    diff_field_in_snapshot = deepcopy(value)
    diff_field_in_snapshot["before"] = {
        "kind": "real",
        "domain": "python",
        "schema": "code-structure-viz.semantic/v1",
        "digest": "0" * 64,
        "head_commit": None,
        "file_count": 0,
    }
    mutations.append(diff_field_in_snapshot)
    not_applicable = deepcopy(value)
    not_applicable["status"] = "not_applicable"
    mutations.append(not_applicable)
    unknown_row = deepcopy(value)
    unknown_row["members"][0]["kind"] = "unknown"
    mutations.append(unknown_row)
    cross_kind = deepcopy(value)
    cross_kind["members"][0]["columns"] = ["id"]
    mutations.append(cross_kind)
    raw_expression = deepcopy(value)
    raw_expression["members"][0]["default"]["raw"] = "DO_NOT_LEAK"
    mutations.append(raw_expression)
    internal_column = deepcopy(value)
    internal_column["members"][0]["source"]["range"]["start_utf8_byte_column"] = 0
    mutations.append(internal_column)
    python_diagnostic = deepcopy(value)
    python_diagnostic["diagnostics"][0]["code"] = "CSV-PY-003"
    mutations.append(python_diagnostic)
    wrong_failure = deepcopy(value)
    wrong_failure["coverage"]["failed_files"] = [
        {"path": "src/broken.py", "stage": "parse", "diagnostic_code": "CSV-SA-002"}
    ]
    mutations.append(wrong_failure)
    cross_domain = deepcopy(value)
    cross_domain["domain"] = "python"
    mutations.append(cross_domain)

    for mutation in mutations:
        with pytest.raises(ValidationError):
            validator.validate(mutation)


def test_diagnostic_schema_accepts_closed_sqlalchemy_occurrence_vector() -> None:
    value = _sqlalchemy_semantic_vector()["diagnostics"][0]

    _validator("diagnostic-v1.schema.json").validate(value)

    invalid = deepcopy(value)
    invalid["start_utf8_byte_column"] = 0
    with pytest.raises(ValidationError):
        _validator("diagnostic-v1.schema.json").validate(invalid)


def test_package_root_relative_import_renders_schema_valid_semantic_artifact(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    (repository / "app.py").write_text("from ...foo import Bar\n", encoding="utf-8")
    initialize_repository(repository)
    output = tmp_path / "output"

    result = run_cli(repository, output)

    assert result.returncode == 0
    semantic = json.loads((output / "python.snapshot.semantic.json").read_bytes())
    _validator("semantic-v1.schema.json").validate(semantic)
    relation = semantic["relations"][0]
    assert relation["kind"] == "import_dependency"
    assert relation["target"] == {
        "resolution": "external",
        "kind": "module",
        "id": None,
        "name": "relative-import",
    }


@pytest.mark.parametrize(
    "path",
    sorted(SEMANTIC_GOLDEN_ROOT.glob("*/python.snapshot.semantic.json")),
    ids=lambda path: path.parent.name,
)
def test_semantic_schema_accepts_every_reviewed_golden(path: Path) -> None:
    value = json.loads(path.read_text(encoding="utf-8"))

    _validator("semantic-v1.schema.json").validate(value)


@pytest.mark.parametrize(
    "path",
    sorted(SEMANTIC_GOLDEN_ROOT.glob("*/run-manifest.json")),
    ids=lambda path: path.parent.name,
)
def test_manifest_schema_accepts_every_reviewed_golden(path: Path) -> None:
    value = json.loads(path.read_text(encoding="utf-8"))

    _validator("run-manifest-v1.schema.json").validate(value)


@pytest.mark.parametrize(
    "path",
    sorted(SEMANTIC_GOLDEN_ROOT.glob("*/stdout.run-summary.jsonl")),
    ids=lambda path: path.parent.name,
)
def test_run_summary_schema_accepts_every_reviewed_golden(path: Path) -> None:
    value = json.loads(path.read_text(encoding="utf-8"))

    _validator("run-summary-v1.schema.json").validate(value)


@pytest.mark.parametrize(
    "path",
    sorted(SEMANTIC_GOLDEN_ROOT.glob("*/stderr.jsonl")),
    ids=lambda path: path.parent.name,
)
def test_diagnostic_schema_accepts_every_reviewed_golden_line(path: Path) -> None:
    validator = _validator("diagnostic-v1.schema.json")

    for line in path.read_text(encoding="utf-8").splitlines():
        validator.validate(json.loads(line))


def test_schemas_accept_captured_complete_and_unavailable_cli_json(
    tmp_path: Path,
) -> None:
    complete_root = tmp_path / "complete"
    repository = initialize_fixture_repository(complete_root, "whole")
    complete_output = complete_root / "output"
    complete = run_cli(repository, complete_output)
    assert complete.returncode == 0

    _validator("run-summary-v1.schema.json").validate(json.loads(complete.stdout))
    _validator("semantic-v1.schema.json").validate(
        json.loads((complete_output / "python.snapshot.semantic.json").read_bytes())
    )
    _validator("run-manifest-v1.schema.json").validate(
        json.loads((complete_output / "run-manifest.json").read_bytes())
    )

    unavailable_root = tmp_path / "unavailable"
    unavailable_root.mkdir()
    unavailable_repository = unavailable_root / "repo"
    initialize_repository(unavailable_repository)
    unavailable_output = unavailable_root / "output"
    unavailable = run_cli(
        unavailable_repository,
        unavailable_output,
        "--target",
        "module:missing.module",
        "--stdout",
        "python:semantic-json",
    )
    assert unavailable.returncode == 3

    _validator("stdout-result-v1.schema.json").validate(json.loads(unavailable.stdout))
    _validator("diagnostic-v1.schema.json").validate(json.loads(unavailable.stderr))
    manifest = json.loads((unavailable_output / "run-manifest.json").read_bytes())
    validator = _validator("run-manifest-v1.schema.json")
    validator.validate(manifest)
    with pytest.raises(ValidationError):
        validator.validate({**manifest, "absolute_path": "/private/secret"})
    with pytest.raises(ValidationError):
        validator.validate({**manifest, "artifacts": [{"path": "run-manifest.json"}]})


def test_manifest_and_stream_schemas_accept_closed_sqlalchemy_cli_output(
    tmp_path: Path,
) -> None:
    repository = initialize_sqlalchemy_fixture_repository(tmp_path, "canonical_model")
    output = tmp_path / "output"

    result = run_sqlalchemy_snapshot_cli(repository, output)

    assert result.returncode == 0, result.stderr
    _validator("run-summary-v1.schema.json").validate(json.loads(result.stdout))
    _validator("semantic-v1.schema.json").validate(
        json.loads((output / "sqlalchemy.snapshot.semantic.json").read_bytes())
    )
    manifest = json.loads((output / "run-manifest.json").read_bytes())
    validator = _validator("run-manifest-v1.schema.json")
    validator.validate(manifest)

    mutations = []
    sql_diff = deepcopy(manifest)
    sql_diff["command"]["name"] = "diff"
    mutations.append(sql_diff)
    python_adapter = deepcopy(manifest)
    python_adapter["adapters"][0] = {
        "domain": "python",
        "name": "python-ast",
        "version": "1",
    }
    mutations.append(python_adapter)
    cross_artifact = deepcopy(manifest)
    cross_artifact["artifacts"][0]["path"] = "python.snapshot.semantic.json"
    mutations.append(cross_artifact)
    wrong_contract = deepcopy(manifest)
    wrong_contract["contracts"]["plantuml"] = "code-structure-viz.plantuml/python/v1"
    mutations.append(wrong_contract)

    for mutation in mutations:
        with pytest.raises(ValidationError):
            validator.validate(mutation)


def test_schemas_accept_captured_complete_diff_json(tmp_path: Path) -> None:
    repository, before, after = create_two_commit_repository_from_files(
        tmp_path,
        before_files={"src/app.py": "class Order:\n    amount: int\n"},
        after_files={"src/app.py": "class Order:\n    amount: str\n"},
    )
    output = tmp_path / "output"
    result = run_diff_cli(repository.resolve(), output, "--from", before, "--to", after)

    assert result.returncode == 0
    _validator("file-change-set-v1.schema.json").validate(
        json.loads((output / "file-changes.json").read_bytes())
    )
    _validator("semantic-v1.schema.json").validate(
        json.loads((output / "python.diff.semantic.json").read_bytes())
    )
    manifest = json.loads((output / "run-manifest.json").read_bytes())
    validator = _validator("run-manifest-v1.schema.json")
    validator.validate(manifest)
    missing_observations = deepcopy(manifest)
    missing_observations["comparison"].pop("candidate_observations")
    with pytest.raises(ValidationError):
        validator.validate(missing_observations)
    before = manifest["comparison"]["resolved"]["before"]
    manifest["comparison"]["candidate_observations"] = [
        {
            "ordinal": 0,
            "origin": "config-upstream",
            "reference": "refs/remotes/upstream/a",
            "resolved_object": before,
            "merge_base": None,
            "disposition": "no-merge-base",
        },
        {
            "ordinal": 1,
            "origin": "config-upstream",
            "reference": "refs/remotes/upstream/b",
            "resolved_object": before,
            "merge_base": before,
            "disposition": "selected",
        },
    ]
    validator.validate(manifest)
    with pytest.raises(ValidationError):
        validator.validate(
            {
                **manifest,
                "comparison": {
                    **manifest["comparison"],
                    "candidate_observations": [
                        {**manifest["comparison"]["candidate_observations"][0], "origin": "other"}
                    ],
                },
            }
        )
    with pytest.raises(ValidationError):
        validator.validate(
            {
                **manifest,
                "comparison": {
                    **manifest["comparison"],
                    "candidate_observations": [
                        {
                            **manifest["comparison"]["candidate_observations"][0],
                            "extra": True,
                        }
                    ],
                },
            }
        )


def test_manifest_schema_accepts_incomplete_diff_descriptor_and_comparison_config(
    tmp_path: Path,
) -> None:
    repository, before, after = create_two_commit_repository_from_files(
        tmp_path,
        before_files={
            "src/app.py": ("class Order:\n    amount: int\n\nclass Customer:\n    name: str\n")
        },
        after_files={
            "src/app.py": ("class Order:\n    amount: bytes\n\nclass Customer:\n    name: bytes\n")
        },
    )
    config = tmp_path / "config.toml"
    config.write_text(
        """schema = \"code-structure-viz.config/v1\"
[python]
source_roots = [\"src\"]
include = [\"**/*.py\"]
exclude = []
[traversal]
upstream_depth = 1
downstream_depth = 1
[limits]
max_entities = 500
[comparison]
target_ref = \"refs/heads/main\"
upstream_ref = \"refs/remotes/origin\"
""",
        encoding="utf-8",
    )
    output = tmp_path / "output"

    result = run_diff_cli(
        repository,
        output,
        "--from",
        before,
        "--to",
        after,
        "--config",
        str(config),
        "--max-entities",
        "1",
    )

    assert result.returncode == 3, result.stderr.decode("utf-8", errors="replace")
    manifest = json.loads((output / "run-manifest.json").read_bytes())
    _validator("run-manifest-v1.schema.json").validate(manifest)
    assert [item["path"] for item in manifest["artifacts"]] == ["file-changes.json"]
    assert manifest["config"]["resolved"]["comparison"] == {
        "target_ref": "refs/heads/main",
        "upstream_ref": "refs/remotes/origin",
    }
    assert manifest["domains"][0]["artifact_paths"] == []
    with_diff_diagnostic = {
        **manifest,
        "diagnostics": [
            {
                "type": "diagnostic",
                "schema": "code-structure-viz.diagnostic/v1",
                "code": "CSV-DIFF-002",
                "severity": "error",
                "domain": None,
                "path": None,
                "symbol": None,
                "line": None,
                "recoverable": False,
                "message": "Changed path count exceeds the resolved comparison limit.",
            }
        ],
    }
    _validator("run-manifest-v1.schema.json").validate(with_diff_diagnostic)


def test_semantic_schema_rejects_member_and_relation_target_discriminant_mutations() -> None:
    validator = _validator("semantic-v1.schema.json")
    whole = json.loads(
        (SEMANTIC_GOLDEN_ROOT / "whole" / "python.snapshot.semantic.json").read_text(
            encoding="utf-8"
        )
    )
    annotation_references = json.loads(
        (
            SEMANTIC_GOLDEN_ROOT / "annotation_references" / "python.snapshot.semantic.json"
        ).read_text(encoding="utf-8")
    )

    mutations: list[dict[str, object]] = []
    field_scope = deepcopy(whole)
    next(item for item in field_scope["members"] if item["kind"] == "field")["scope"] = None
    mutations.append(field_scope)
    property_signature = deepcopy(whole)
    next(item for item in property_signature["members"] if item["kind"] == "property")[
        "signature"
    ] = None
    mutations.append(property_signature)
    method_annotation = deepcopy(whole)
    next(item for item in method_annotation["members"] if item["kind"] == "method")[
        "annotation"
    ] = "Secret"
    mutations.append(method_annotation)
    internal_id = deepcopy(whole)
    next(item for item in internal_id["relations"] if item["target"]["resolution"] == "internal")[
        "target"
    ]["id"] = None
    mutations.append(internal_id)
    external_id = deepcopy(whole)
    next(item for item in external_id["relations"] if item["target"]["resolution"] == "external")[
        "target"
    ]["id"] = "python:module:secret"
    mutations.append(external_id)
    unknown_kind = deepcopy(annotation_references)
    next(item for item in unknown_kind["relations"] if item["target"]["resolution"] == "unknown")[
        "target"
    ]["kind"] = "module"
    mutations.append(unknown_kind)
    unknown_diagnostic = deepcopy(annotation_references)
    unknown_diagnostic["diagnostics"][0]["code"] = "CSV-UNKNOWN-999"
    mutations.append(unknown_diagnostic)
    wrong_diagnostic_metadata = deepcopy(annotation_references)
    wrong_diagnostic_metadata["diagnostics"][0]["severity"] = "error"
    mutations.append(wrong_diagnostic_metadata)

    for mutation in mutations:
        with pytest.raises(ValidationError):
            validator.validate(mutation)


def test_manifest_schema_rejects_status_exit_artifact_and_catalog_mutations() -> None:
    validator = _validator("run-manifest-v1.schema.json")
    complete = json.loads(
        (SEMANTIC_GOLDEN_ROOT / "whole" / "run-manifest.json").read_text(encoding="utf-8")
    )
    partial = json.loads(
        (SEMANTIC_GOLDEN_ROOT / "partial_safe" / "run-manifest.json").read_text(encoding="utf-8")
    )

    mutations: list[dict[str, object]] = []
    wrong_exit = deepcopy(complete)
    wrong_exit["run"]["exit_code"] = 3
    mutations.append(wrong_exit)
    missing_payload_artifacts = deepcopy(complete)
    missing_payload_artifacts["domains"][0]["artifact_paths"] = []
    missing_payload_artifacts["artifacts"] = []
    mutations.append(missing_payload_artifacts)
    mismatched_artifact = deepcopy(complete)
    mismatched_artifact["artifacts"][0]["format"] = "plantuml"
    mutations.append(mismatched_artifact)
    mismatched_status = deepcopy(partial)
    mismatched_status["run"]["status"] = "complete"
    mismatched_status["run"]["exit_code"] = 0
    mutations.append(mismatched_status)
    unknown_diagnostic = deepcopy(partial)
    unknown_diagnostic["domains"][0]["diagnostics"][0]["code"] = "CSV-UNKNOWN-999"
    mutations.append(unknown_diagnostic)
    wrong_diagnostic_message = deepcopy(partial)
    wrong_diagnostic_message["domains"][0]["diagnostics"][0]["message"] = "arbitrary"
    mutations.append(wrong_diagnostic_message)

    for mutation in mutations:
        with pytest.raises(ValidationError):
            validator.validate(mutation)


def test_run_summary_schema_rejects_status_exit_domain_and_manifest_mismatches() -> None:
    validator = _validator("run-summary-v1.schema.json")
    complete = json.loads(
        (SEMANTIC_GOLDEN_ROOT / "whole" / "stdout.run-summary.jsonl").read_text(encoding="utf-8")
    )
    mutations = []
    for key, value in (
        ("exit_code", 3),
        ("run_status", "fatal"),
        ("manifest", None),
    ):
        mutation = deepcopy(complete)
        mutation[key] = value
        mutations.append(mutation)
    wrong_domain = deepcopy(complete)
    wrong_domain["domains"][0]["status"] = "not_applicable"
    mutations.append(wrong_domain)

    for mutation in mutations:
        with pytest.raises(ValidationError):
            validator.validate(mutation)


def test_stdout_result_schema_rejects_selector_status_and_reason_mismatches() -> None:
    validator = _validator("stdout-result-v1.schema.json")
    unavailable = {
        "type": "stdout_result",
        "schema": "code-structure-viz.stdout-result/v1",
        "selector": "python:semantic-json",
        "availability": False,
        "domain_status": "not_applicable",
        "stable_reason": "domain_not_applicable",
        "artifact": None,
    }
    mutations = []
    for key, value in (
        ("selector", "manifest"),
        ("domain_status", "incomplete"),
        ("stable_reason", "run_fatal"),
    ):
        mutation = {**unavailable, key: value}
        mutations.append(mutation)

    for mutation in mutations:
        with pytest.raises(ValidationError):
            validator.validate(mutation)


def test_diagnostic_schema_rejects_catalog_metadata_and_context_mismatches() -> None:
    validator = _validator("diagnostic-v1.schema.json")
    value = {
        "type": "diagnostic",
        "schema": "code-structure-viz.diagnostic/v1",
        "code": "CSV-PY-003",
        "severity": "error",
        "domain": "python",
        "path": "src/broken.py",
        "symbol": None,
        "line": 7,
        "recoverable": True,
        "message": "Python source could not be parsed with the v1 Python 3.12 grammar.",
    }
    mutations = []
    for key, changed in (
        ("severity", "info"),
        ("domain", None),
        ("symbol", "secret"),
        ("recoverable", False),
        ("message", "arbitrary message"),
    ):
        mutations.append({**value, key: changed})

    for mutation in mutations:
        with pytest.raises(ValidationError):
            validator.validate(mutation)
