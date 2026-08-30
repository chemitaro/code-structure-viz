---
種別: 実装計画書（Issue）
ID: "iss-00007"
タイトル: "Compare SQLAlchemy ER Changes"
関連GitHub: ["#7"]
package_sequence_key: "ISSUE-04"
状態: "ready"
最終更新: "2026-08-30"
依存: ["requirement.md", "design.md"]
親: ["epic-00002", "init-00001"]
---

# iss-00007 Compare SQLAlchemy ER Changes — 実装計画

詳細: [Issue Plan Guide](../../../../../../docs/authoring/issue-plan.md)

## Planning Level

- **selected level: `strict`**
- 理由: existing Python diff のshared publication pathへ新しいdomainを追加し、public semantic JSON/PlantUML/schemaを増やすため、回帰・redaction・failure publicationを明示的に固定する必要がある。
- 主なriskは、side failureをremovalと誤認すること、SQLAlchemy diffでsecret/raw sourceを漏らすこと、shared artifact変更でPython diffを壊すことである。
- persistent dataやtarget repositoryを変更しないため`critical`ではない。source/DB実行、secret incident、不可逆変更が必要になった場合は`critical`へ再評価する。

## 実装前提

1. taskで指定されたrepository/branch/full SHAをGitHub connectorで再検証し、root `AGENTS.md` が存在すれば読む。verification failure時は実装しない。
2. `requirement.md` / `design.md` / 本Planと親Epic、`iss-00005`、`iss-00006`のcurrent contractを確認する。
3. baselineとして次を通す。

```bash
python3 ./spec-dock/scripts/spec-dock validate
uv sync --frozen --all-groups
uv run pytest tests/acceptance/python/test_diff_cli.py tests/acceptance/sqlalchemy/test_snapshot_cli.py -q
```

baseline failureやDesign記載のplanned-new pathが既に存在する場合は、推測で上書きせずDesign/Planをcurrent codeへ同期してから進む。

## 実装順序

| Plan ID | 内容 | Trace |
| --- | --- | --- |
| I04-PLAN-001 | SQLAlchemy diffのpure behaviorとCLI acceptanceをtest-firstで固定する。 | I04-DES-002,003,005 |
| I04-PLAN-002 | SQLAlchemy exact-ID diff、impact、JSON/PlantUML renderingを実装する。 | I04-DES-002,003 |
| I04-PLAN-003 | `DiffApplication`、CLI、artifact/manifest/stream/schemaへSQLAlchemy branchを接続する。 | I04-DES-001,004 |
| I04-PLAN-004 | safety、Python diff/SQLAlchemy snapshot regression、repository-wide quality gateを完了する。 | I04-DES-005 |

## I04-PLAN-001 — tests first

新規:

```text
tests/unit/sqlalchemy/test_diff.py
tests/acceptance/sqlalchemy/test_diff_cli.py
```

既存testは必要なassertだけ追加する。

```text
tests/unit/cli/test_parser.py
tests/unit/artifacts/test_manifest.py
tests/unit/artifacts/test_writer.py
tests/unit/artifacts/test_streams.py
tests/contracts/test_json_schemas.py
tests/contracts/test_scope_exclusions.py
tests/security/test_sqlalchemy_static_boundary.py
```

最低限、次をREDで固定する。

- exact IDによるtable/row/relation added/removed/modified。ID変更はremoved+added。
- provenance-only changeはsemantic deltaにしない。
- before/after relation unionのimpactとdeleted relation edge。
- both absent、one-side absent、one-side incomplete。
- removed ghost、modified before/after、impact contextを持つPlantUML。
- `diff --domain sqlalchemy`、SQLAlchemy stdout selector、expected published paths。
- entity budget / changed-path budget / payload-unavailable publication。
- raw source/literal/secret/absolute pathなし、target import/DB/Git mutationなし。
- existing Python diff と SQLAlchemy snapshotの回帰。

expected REDはSQLAlchemy diffが未接続であることに由来するものだけとする。別のbaseline failureは先に解消する。

## I04-PLAN-002 — local SQLAlchemy diff

追加:

```text
src/code_structure_viz/adapters/sqlalchemy/diff.py
```

変更:

```text
src/code_structure_viz/adapters/sqlalchemy/semantic_json.py
src/code_structure_viz/adapters/sqlalchemy/plantuml.py
```

実装する順序:

1. `SqlAlchemySnapshotAnalyzer` + `SqlAlchemyTargetSelector.select(..., targets=())` で各SourceViewのwhole snapshot resultを得る。
2. complete/not-applicable/incompleteをDesignのreal/canonical-empty/analysis-failedへ写像する。
3. table/row/relationをexisting IDで比較し、added/removed/modifiedだけを生成する。
4. Issue #6 safe projectionからprovenance fieldだけを除いた値でmodified判定する。
5. changed table/row/relationからseedを作り、before/after internal relation unionをdepth指定で探索する。
6. entity countをunique table ID数として返す。
7. `semantic_json.py` と `plantuml.py` にdiff renderingを追加し、snapshot renderingの既存bytesは変えない。

focused:

```bash
uv run pytest tests/unit/sqlalchemy/test_diff.py -q
uv run pytest tests/unit/sqlalchemy/test_semantic_json.py tests/unit/sqlalchemy/test_plantuml.py tests/acceptance/sqlalchemy/test_snapshot_determinism.py -q
```

stop:

- heuristic rename/move、raw source/literal、runtime SQLAlchemy/DBが必要になる。
- Issue #6 IDまたはsnapshot public bytesを変更しなければ実装できない。

## I04-PLAN-003 — existing diff machineryへ接続

変更:

```text
src/code_structure_viz/core/domains.py
src/code_structure_viz/cli/parser.py
src/code_structure_viz/application/diff.py
src/code_structure_viz/artifacts/manifest.py
src/code_structure_viz/artifacts/writer.py
src/code_structure_viz/artifacts/streams.py
schemas/semantic-v1.schema.json
schemas/run-manifest-v1.schema.json
docs/contracts/cli-v1.md
docs/contracts/sqlalchemy-semantic-v1.md
docs/contracts/sqlalchemy-plantuml-v2.md
docs/contracts/run-manifest-v1.md
```

実装する順序:

1. diff domainを`python|sqlalchemy`に拡張する。option setは変更しない。
2. `DiffApplication` のendpoint/source/FileChangeSet/changed-path/transaction flowは維持し、analysis/comparison/renderingだけをdomain分岐する。
3. SQLAlchemy resultをexisting `EntityBudgetGate` と `DomainOutcome`へ写像する。
4. diff Artifact registry/staging/manifest/stdout pathをdomain-awareにする。
5. semantic/run-manifest schemaとcontract docsへSQLAlchemy diff variantを追加する。
6. Python branchはexisting differ/rendererを使い続ける。

focused:

```bash
uv run pytest tests/unit/cli/test_parser.py tests/unit/artifacts/test_manifest.py tests/unit/artifacts/test_writer.py tests/unit/artifacts/test_streams.py tests/contracts/test_json_schemas.py tests/acceptance/sqlalchemy/test_diff_cli.py -q
```

stop:

- SQLAlchemy用にsecond Git/source/publication lifecycleや汎用plugin frameworkが必要になる。
- `run-summary/v1` / `stdout-result/v1` の既存SQLAlchemy supportを壊す変更が必要になる。

## I04-PLAN-004 — safety / regression / quality gate

SQLAlchemy diff safety assertionは既存 `tests/security/test_sqlalchemy_static_boundary.py` に追加し、runtime dependency、import/execute、DB、Git mutation、raw source/literal/private pathを検査する。`tests/contracts/test_scope_exclusions.py` はSQLAlchemy diffを許可する一方、Next/all/HTML/runtime SQLAlchemy importを拒否し続ける。

focused regression:

```bash
uv run pytest tests/acceptance/sqlalchemy/test_diff_cli.py tests/acceptance/python/test_diff_cli.py tests/acceptance/sqlalchemy/test_snapshot_cli.py tests/acceptance/sqlalchemy/test_snapshot_determinism.py tests/security/test_sqlalchemy_static_boundary.py tests/contracts/test_scope_exclusions.py -q
```

repository-wide gate:

```bash
uv run pytest -q
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
dist_dir="$(mktemp -d)"
uv build --offline --out-dir "$dist_dir"
rm -rf "$dist_dir"
python3 ./spec-dock/scripts/spec-dock validate
```

`pyproject.toml` / `uv.lock` にruntime dependency差分を残さない。

## trace

| Requirement | Design | Plan | Acceptance |
| --- | --- | --- | --- |
| I04-REQ-001 | I04-DES-001,004 | I04-PLAN-001,003 | I04-AC-001,004 |
| I04-REQ-002 | I04-DES-002 | I04-PLAN-001,002 | I04-AC-001 |
| I04-REQ-003 | I04-DES-003 | I04-PLAN-001,002 | I04-AC-001,003 |
| I04-REQ-004 | I04-DES-001,004 | I04-PLAN-001,003 | I04-AC-002,004 |
| I04-REQ-005 | I04-DES-005 | I04-PLAN-004 | I04-AC-003,004,005 |

## rollback / handoff

migrationはN/A。persistent dataや既存Artifactを更新しない。

rollback triggerは false successful diff、secret/raw source leak、target/DB execution、Git mutation、Python diffまたはSQLAlchemy snapshot regressionである。rollback時はIssue #7のSQLAlchemy diff追加とshared registry/schema接続を一体で戻し、Issue #5/#6のcompleted implementationは戻さない。

matchingが安全に成立しない変更はremoved+added、side analysisが安全に成立しない場合はpayload-unavailableへ狭めることをforward recoveryとする。

handoff条件:

- I04-AC-001〜I04-AC-005を満たす。
- focused testとrepository-wide gateが成功する。
- Python diffとSQLAlchemy snapshotのpublic regressionがない。
- runtime dependency、Next/all/HTML/target-query、heuristic moveを追加していない。
- `report.md`、`.meta.json`、parent scopeは本Issue implementationで変更していない。
