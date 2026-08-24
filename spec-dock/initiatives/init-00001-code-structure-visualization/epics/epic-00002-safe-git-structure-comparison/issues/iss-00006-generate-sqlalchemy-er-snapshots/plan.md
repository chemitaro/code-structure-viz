---
種別: 実装計画書（Issue）
ID: "iss-00006"
タイトル: "Generate SQLAlchemy ER Snapshots"
関連GitHub: ["#6"]
package_sequence_key: "ISSUE-03"
状態: "draft"
最終更新: "2026-08-24"
依存: ["requirement.md", "design.md"]
親: ["epic-00002", "init-00001"]
---

# iss-00006 Generate SQLAlchemy ER Snapshots — 実装計画

詳細: [Issue Plan Guide](../../../../../../docs/authoring/issue-plan.md)

## Planning Level

- **selected level: `strict`**
- 理由: database structure を説明する public semantic schema と privacy-sensitive redaction を導入し、誤った ORM 推測からの回復が難しいため strict を選ぶ。
- risk factor: public CLI/schema、static-analysis safety、Artifact integrity、adapter compatibility、誤比較時の広い説明影響。
- `critical` ではない理由: target repository と persistent user data を変更せず、release/commit 単位で戻せる設計である。
- 再評価条件: secret/PII exposure、target mutation、不可逆 data loss、incident response が必要な rollout を追加する場合。

## 目標

coding agent が DB や application を起動せず、SQLAlchemy declarative ORM source から table と row-level ER semantics を JSON と PlantUML で取得できる。

completion は file/technical layer の完成ではなく、次の observable chain で判定する。

```text
CLI request -> safe source acquisition -> domain semantic analysis
  -> versioned semantic JSON + domain PlantUML -> diagnostic/manifest
  -> acceptance command and exit evidence
```

## 順序・依存

- declared dependency: ISSUE-01
- sibling の private parser/model/renderer implementation に依存しない。必要な cross-Issue contract は `semantic-contract.md` と親 Epic Design を正本にする。
- 並行可能: fixture authoring、schema examples、renderer golden、security trap fixture は interface acceptance 固定後に並行できる。
- 統合順: dependency contract verification → source path → semantic model → render/output transaction → acceptance/CI。
- stop condition: table/row identity、redaction、not_applicable/incomplete、DB 非接続の acceptance が成立するまで temporal ER matching と ghost row へ進まない。

| Plan ID | implementation/verification step | Design trace |
| --- | --- | --- |
| I03-PLAN-001 | Requirement fixture と command/manifest contract test を先に追加し、failure/exit behavior を executable acceptance として固定する。 | I03-DES-001 |
| I03-PLAN-002 | 必要最小限の CLI/config/diagnostic/Artifact boundary を planned module に実装し、dependency Issue の public contract を再利用する。 | I03-DES-002 |
| I03-PLAN-003 | sqlalchemy source acquisition と domain-owned semantic analyzer/matcher を実装し、unsafe/unknown を diagnostic へ変換する。 | I03-DES-003 |
| I03-PLAN-004 | semantic JSON と PlantUML renderer、redaction、deterministic ordering、SHA-256 manifest を一つの output transaction へ接続する。 | I03-DES-004 |
| I03-PLAN-005 | negative/security/budget/determinism/partial failure test、documentation、lockfile/license/offline gate を完了し、handoff evidence を作る。 | I03-DES-005 |

## 実装step

### I03-PLAN-001 acceptance-first contract

- planned test files を先に作り、CLI arguments、output filenames、manifest fields、status、exit code を table-driven fixture で固定する。
- user-visible Artifact bytes の golden は source body/secret/absolute path がないことを同時に確認する。
- implementation 未着手時に test が expected failure になることを確認し、誤った既存 behavior を前提にしない。

### I03-PLAN-002 application boundary

- planned modules:

- src/code_structure_viz/adapters/sqlalchemy/detector.py::DeclarativeDetector（planned）
- src/code_structure_viz/adapters/sqlalchemy/analyzer.py::SqlAlchemySnapshotAnalyzer（planned）
- src/code_structure_viz/adapters/sqlalchemy/model.py（planned）
- src/code_structure_viz/adapters/sqlalchemy/redaction.py::SqlDefaultRedactor（planned）
- src/code_structure_viz/adapters/sqlalchemy/renderer.py（planned）

- すべて baseline commit には未実装であり、この Plan は候補 path/symbol を指示する。存在済みとみなさない。
- dependency injection は filesystem、Git process、clock/temp directory、Node process に限定し、domain model を framework へ依存させない。

### I03-PLAN-003 source and semantic implementation

- Python source を ISSUE-01 の安全な reader/AST pipeline で読み、declarative base、mapped class、association `Table` の静的 pattern だけを対象にする。
- DB 接続、engine、Session、Alembic、`MetaData.create_all()`、import side effect、runtime mapper inspection を使用しない。
- modern `DeclarativeBase`/`Mapped`/`mapped_column` と、静的に同定できる classic declarative/`Column` pattern を扱う。曖昧な factory return は推測しない。
- repository 内 source が ORM target を持たない場合は `not_applicable`。target 候補があるが syntax/alias 解決で安全に解析できない場合は `incomplete`。

- table identity は normalized schema 名と table 名。schema 無指定は explicit null namespace とし、module path は provenance であって table identity ではない。
- table entity に column、primary/foreign/unique/check constraint、index、relationship、inheritance、association table を typed row member として保持する。
- row identity は domain kind と declarative name/structural key。order は semantics から除外し、source order だけの変更を semantic change にしない。
- column type、nullable、PK/FK/unique、index、relationship target/cardinality/back_populates を安全に正規化する。SQL/default literal は `redacted` と presence/category だけを保持する。
- ForeignKey と `relationship()` は別 relation kind とし、同一の意味へ畳み込まない。

- adapter input/output を immutable value とし、parse failure を empty collection や removed entity へ変換しない。
- budget は collection/render 前に検査し、partial truncation を禁止する。

### I03-PLAN-004 Artifact publication

- semantic JSON は domain `sqlalchemy`、document kind `snapshot` と table/row identity、source location、coverage、diagnostic を持つ。
- PlantUML ER は table を entity、column/constraint/index/relationship を row として表示し、FK と ORM relationship の線・label を分離する。
- source default literal、connection URL、absolute path は出力せず、redaction count と rule version を manifest に記録する。

- staging directory は target repository 外を優先し、final fingerprint/collision check 後に rename/copy+fsync strategy で公開する。
- manifest の SHA-256 は final bytes を基準にし、path は output directory 相対とする。

### I03-PLAN-005 hardening and handoff

- `uv run ruff check .`
- `uv run mypy src tests`
- `uv run pytest`
- Next adapter を含む場合は `npm --prefix adapters/next ci --offline`、`npm --prefix adapters/next run typecheck`、`npm --prefix adapters/next test`。
- package build、minimum/latest CI、offline runtime fixture、license inventory を確認する。
- docs は CLI examples、schema version、failure/exit behavior、scope 外を更新する。product HTML command は追加しない。

## 検証

| Test ID | acceptance behavior | planned file | command |
| --- | --- | --- | --- |
| I03-AT-001 | declarative model と association table を table/row semantic JSON と ER PlantUML にする。 | tests/acceptance/sqlalchemy/test_snapshot_cli.py | uv run pytest tests/acceptance/sqlalchemy/test_snapshot_cli.py -q |
| I03-AT-002 | FK と relationship、constraint/index、inheritance を別 kind として保持する。 | tests/integration/sqlalchemy/test_semantic_rows.py | uv run pytest tests/integration/sqlalchemy/test_semantic_rows.py -q |
| I03-AT-003 | runtime-only factory、duplicate table identity、broken declarative source を incomplete にする。 | tests/acceptance/sqlalchemy/test_snapshot_failures.py | uv run pytest tests/acceptance/sqlalchemy/test_snapshot_failures.py -q |
| I03-AT-004 | DB connector と target import を呼ばず、default/URL/secret literal を Artifact へ出さない。 | tests/security/test_sqlalchemy_static_boundary.py | uv run pytest tests/security/test_sqlalchemy_static_boundary.py -q |
| I03-AT-005 | source declaration order が semantics に影響しない row ordering と hash を確認する。 | tests/acceptance/sqlalchemy/test_snapshot_determinism.py | uv run pytest tests/acceptance/sqlalchemy/test_snapshot_determinism.py -q |
| I03-AT-006 | ORM target なしは not_applicable、候補あり解析不能は incomplete を区別する。 | tests/acceptance/sqlalchemy/test_applicability.py | uv run pytest tests/acceptance/sqlalchemy/test_applicability.py -q |

### issue gate commands

```bash
uv run pytest tests/acceptance/sqlalchemy/test_snapshot_cli.py -q
uv run pytest tests/integration/sqlalchemy/test_semantic_rows.py -q
uv run pytest tests/acceptance/sqlalchemy/test_snapshot_failures.py -q
uv run pytest tests/security/test_sqlalchemy_static_boundary.py -q
uv run pytest tests/acceptance/sqlalchemy/test_snapshot_determinism.py -q
uv run pytest tests/acceptance/sqlalchemy/test_applicability.py -q
uv run ruff check .
uv run mypy src tests
uv run pytest
```

### regression boundary

- dependency Issue の acceptance suite を再実行し、public JSON/manifest/exit contract を破っていないことを確認する。
- target repository の HEAD、branch、refs、index、status、tracked/untracked bytes が command 前後で一致する。
- same-input deterministic rerun と output collision negative test を実行する。
- visual vocabulary は color、記号、line style、legend を golden/semantic test で検査する。

## rollback

- persistent DB migration は N/A。本 Issue は DB を変更しない。誤解析が見つかった場合は affected pattern を incomplete へ狭める安全な forward fix を優先し、公開済み row kind を削除するときは schema version up を行う。
- rollback trigger: acceptance regression、source execution/mutation、secret/absolute path leak、incorrect successful exit、ambiguous moved の誤採用。
- rollback unit: Issue の production code、tests、schema/doc additionsを一体で revert する。dependency Issue の accepted contract は戻さない。
- forward recovery: unsafe pattern を `incomplete`/`unknown` へ狭め、誤った success を継続しない。既存 Artifact を自動 rewrite しない。
- output migration は N/A。Artifact は immutable run output であり、既存 output を上書きしない。

## exit / handoff

- I03-AC-001〜I03-AC-006 の acceptance evidence が揃う。
- Requirement→Design→Plan→test trace に gap がない。
- planned path honesty を review し、実装時点の実在 path/symbol と差異があれば Design/Plan を先に更新する。
- residual risk、unsupported static pattern、coverage limitation、explicit override を release note と manifest diagnostic contract に残す。
- downstream handoff: ISSUE-01 の common snapshot/output contract を拡張する SQLAlchemy snapshot slice。ISSUE-04 完了までは ER diff を約束しない。
- completion 後も implementation/report の実績は canonical Report に別途記録し、本 Plan を実行ログにしない。
