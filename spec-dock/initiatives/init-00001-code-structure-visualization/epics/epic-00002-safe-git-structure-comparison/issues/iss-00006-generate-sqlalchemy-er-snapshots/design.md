---
種別: 設計書（Issue）
ID: "iss-00006"
タイトル: "Generate SQLAlchemy ER Snapshots"
関連GitHub: ["#6"]
package_sequence_key: "ISSUE-03"
状態: "draft"
最終更新: "2026-08-24"
依存: ["requirement.md"]
親: ["epic-00002", "init-00001"]
---

# iss-00006 Generate SQLAlchemy ER Snapshots — 設計

詳細: [Design Guide](../../../../../../docs/authoring/design.md)

## 設計目標

- `sqlalchemy` domain の `snapshot` を、CLI から source acquisition、analysis、versioned JSON、PlantUML、manifest、diagnostic まで一つの vertical pipeline として設計する。
- accepted ADR の独立 product ownership、named endpoint、dual snapshot、adapter boundary、agent-first Artifact、安全な static analysis、product HTML exclusion、vertical slicing を破らない。
- common abstraction は lifecycle、diagnostic、Artifact descriptor、graph primitive に限定し、domain-specific identity/member/relation/matching を adapter が所有する。

| Design ID | Requirement trace | 判断 |
| --- | --- | --- |
| I03-DES-001 | I03-REQ-001 | SQLAlchemy snapshot application serviceがsource selection、static analyzer、ER renderer、manifestをone runで調整する。 |
| I03-DES-002 | I03-REQ-002 | Python SourceView/AST readerを再利用し、DB、mapper、target importへ到達しないdeclarative pattern boundaryを置く。 |
| I03-DES-003 | I03-REQ-003 | schema/table identityとtyped row identitiesをSQLAlchemy adapterが所有する。 |
| I03-DES-004 | I03-REQ-004 | domain `sqlalchemy` snapshot JSON、ER PlantUML、safe provenanceをOutputTransactionへ渡す。 |
| I03-DES-005 | I03-REQ-005 | unknown/runtime-only/duplicate identityとdomain-local entity budgetをtyped incompleteへ写像する。 |
| I03-DES-006 | I03-REQ-006 | DB/import execution trap、literal redaction、canonical row order、same-input digest invariantを検証する。 |

## Current / Target

### Current（verified baseline）

- exact verified current commit `867ee6929283dfc84711bce245b784d2b8e3e9e6` は本Issueのcanonical Requirement/Design/Plan、accepted ADR、interviewを含む。
- production package、CLI、domain adapter、schema implementation、acceptance fixturesは未実装であり、以下のpath/symbolはすべてplannedである。
- 本Designは親の横断contractをslice固有の構造へ具体化し、依存Issueのpublic contractを変更せずに後続sliceへ渡す。

### Target

- coding agent が DB や application を起動せず、SQLAlchemy declarative ORM source から table と row-level ER semantics を JSON と PlantUML で取得できる。
- source/body/secret を漏らさず、failure と coverage を manifest で agent が機械判定できる。
- downstream Issue はこの Design の stable interface だけへ依存し、内部 class layout を fork しない。

## 責務・Interface

### planned component responsibilities

| planned path / symbol | 状態 | 責務 |
| --- | --- | --- |
| src/code_structure_viz/adapters/sqlalchemy/detector.py::DeclarativeDetector（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/adapters/sqlalchemy/analyzer.py::SqlAlchemySnapshotAnalyzer（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/adapters/sqlalchemy/model.py（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/adapters/sqlalchemy/redaction.py::SqlDefaultRedactor（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/adapters/sqlalchemy/renderer.py（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |

### common command interface

```text
code-structure-viz snapshot --repo PATH --output-dir PATH [--domain DOMAIN] [--target SELECTOR] [--format FORMAT] [--config PATH]
code-structure-viz diff --repo PATH --output-dir PATH [--domain DOMAIN] [--from ENDPOINT] [--to ENDPOINT] [--format FORMAT] [--config PATH]
```

- `--output-dir` は必須。writer は existing file を置換せず、全 payload を staging 後に公開する。
- `--format` 未指定は semantic JSON と PlantUML。`--stdout` は output directory requirement を解除しない。
- analysis behavior を environment variable で変更しない。環境は executable discovery と locale-independent process setup にだけ使う。

### source interface

```json
{
  "contract": "code-structure-viz.source-view/v1",
  "endpoint": {"kind": "commit-or-frozen-working-tree", "digest": "sha256"},
  "files": [{"path": "repository/relative", "sha256": "digest", "media_type": "text/plain"}],
  "fingerprint": "safe-run-fingerprint",
  "diagnostics": []
}
```

SourceView は immutable value object であり、absolute temporary path を serializer へ渡さない。

### domain adapter interface

```text
analyze_snapshot(SourceView, ResolvedConfig, TargetSelection) -> DomainSnapshotResult
compare_snapshots(DomainSnapshot, DomainSnapshot, DiffPolicy) -> DomainDiffResult
render_semantic_json(DomainResult) -> bytes
render_plantuml(DomainResult, VisualVocabulary) -> bytes
```

この Issue が未使用の method は実装を強制しない。後続 slice が stable contract を additive に拡張する。

## data / failure

### ER snapshot model

`SqlAlchemySnapshot`はtable entityとcolumn/constraint/index/relationship rowを分離する。table identityはnormalized schema + table name。source module/pathはprovenanceでありidentityへ混ぜない。SQL defaultはpresence/categoryだけを保持しraw literalをanalyzer boundaryで破棄する。

### applicability, failure, and entity gate

- declarative target evidence不在は`not_applicable`。candidateがあるがruntime evaluation、duplicate identity、parse/type resolution failureを安全に解消できない場合は`incomplete`。
- safe partial snapshotをpublishする場合はpayload status/coverage/diagnosticにincompleteを明示し、unknown rowをcompleteと偽らない。
- `EntityBudgetGate`（planned）はrender前にdefault 500を検査する。超過はdomain incomplete、exit 3、affected semantic JSON/PlantUMLなし、safe run manifestへrequested/resolved/count/diagnosticを記録する。valid overrideは通常公開、invalid valueはexit 2。snapshot pipelineは`ChangedPathAdmissionGate`を構築・実行せず、diff専用`--max-changed-paths`を受けた場合はusage error、exit 2、Artifactなしとする。
- core preflight/output collisionはexit 1/2でArtifactを公開しない。

### safety and determinism

AST/static patternだけを使いDB connector、Alembic、mapper configuration、application importを呼ばない。同じsource bytes/config/adapter versionではtable/row/relation/diagnostic/orderとSHA-256を一致させる。

## 変更対象

| planned file | planned change | 存在確認 |
| --- | --- | --- |
| src/code_structure_viz/adapters/sqlalchemy/detector.py::DeclarativeDetector（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/adapters/sqlalchemy/analyzer.py::SqlAlchemySnapshotAnalyzer（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/adapters/sqlalchemy/model.py（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/adapters/sqlalchemy/redaction.py::SqlDefaultRedactor（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/adapters/sqlalchemy/renderer.py（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |

追加で planned:

- tests/fixtures/generate-sqlalchemy-er-snapshots/ に source-only fixture を置き、fixture の application code を実行しない。
- docs/contracts/ に schema と CLI behavior を配置する。これらはplanned implementation targetであり、本Designは実装済みとは扱わない。
- lockfile と license inventory を同じ Issue の acceptance に含める。

変更しない領域:

- DB introspection、live schema、Alembic revision/migration execution
- SQL text の literal 保存、server default の実行評価
- temporal ER diff と ghost row
- 非 SQLAlchemy ORM、product HTML report

## 移行・互換性・rollback

- baseline に production implementation がないため in-place data migration は N/A。
- public schema/CLI は `/v1` と preview release で開始し、同一 major 内は field の additive extension を原則とする。
- persistent DB migration は N/A。本 Issue は DB を変更しない。誤解析が見つかった場合は affected pattern を incomplete へ狭める安全な forward fix を優先し、公開済み row kind を削除するときは schema version up を行う。
- legacy CLI compatibility layer は作らない。legacy evidence の algorithm/test idea を採用するときは provenance note、license decision、CodeStructureViz-owned regression test を同じ change に含める。

## testability

| Test ID | 分類 | planned test file | command |
| --- | --- | --- | --- |
| I03-AT-001 | normal | tests/acceptance/sqlalchemy/test_snapshot_cli.py | uv run pytest tests/acceptance/sqlalchemy/test_snapshot_cli.py -q |
| I03-AT-002 | semantic kinds | tests/integration/sqlalchemy/test_er_semantics.py | uv run pytest tests/integration/sqlalchemy/test_er_semantics.py -q |
| I03-AT-003 | negative | tests/acceptance/sqlalchemy/test_snapshot_failures.py | uv run pytest tests/acceptance/sqlalchemy/test_snapshot_failures.py -q |
| I03-AT-004 | security/redaction | tests/security/test_sqlalchemy_static_boundary.py | uv run pytest tests/security/test_sqlalchemy_static_boundary.py -q |
| I03-AT-005 | determinism | tests/acceptance/sqlalchemy/test_snapshot_determinism.py | uv run pytest tests/acceptance/sqlalchemy/test_snapshot_determinism.py -q |
| I03-AT-006 | applicability | tests/acceptance/sqlalchemy/test_applicability.py | uv run pytest tests/acceptance/sqlalchemy/test_applicability.py -q |
| I03-AT-007 | entity budget / diff-only option rejection | tests/acceptance/sqlalchemy/test_snapshot_budget.py | uv run pytest tests/acceptance/sqlalchemy/test_snapshot_budget.py -q |

- unit testはdomain parser/matcher/serializerとcanonicalizationのpure functionを対象にする。
- integration testはtemporary Git repositoryまたはimmutable source fixtureを使い、Git stateとsource bytesのbefore/afterを比較する。
- acceptance testは実CLI process、output directory、manifest/checksum、exit code、stdout/stderr、published file setを観測する。
- security testはimport/build/plugin/DB execution trap、source/secret/literal/absolute path/raw hunkのnegative scan、unsafe symlink、Git mutation allowlistを検査する。
- table-driven casesはstatusだけでなくpublication、manifest presence/absence、digest、requested/resolved budget values、actual countsまでassertする。

## risk

- SQLAlchemy API は declarative expression の自由度が高い。初期 release は安全に静的同定できる pattern を列挙し、runtime evaluation を避ける。
- default literal は secret を含み得る。value を保持せず redaction category だけを出力する。
- FK と relationship を混同すると ER explanation が誤る。schema 上も renderer 上も別 kind とする。

- Re-evaluation trigger: security/privacy incident、target repository の不可逆変更、secret leak、rollback に incident response が必要な設計へ変わる場合は Planning Level を `critical` に上げる。
- Stop condition: table/row identity、redaction、not_applicable/incomplete、DB 非接続の acceptance が成立するまで temporal ER matching と ghost row へ進まない。

```plantuml
@startuml
title SQLAlchemy ER snapshot の静的解析境界
left to right direction
actor "coding agent" as Agent
component "snapshot CLI" as CLI
component "Python source AST" as AST
component "SqlAlchemySnapshotAnalyzer" as Analyzer
database "DB / runtime metadata
（使用しない）" as Database
component "ER JSON / PlantUML" as Output
Agent -> CLI : sqlalchemy domain を指定する
CLI -> AST : declarative source bytes を渡す
AST -> Analyzer : class・call・annotation node
Analyzer -> Output : table と row semantics
Analyzer -[hidden]-> Database
Output --> Agent : redacted Artifact を返す
@enduml
```

DB や Alembic を参照せず、declarative source に静的に現れた table と row だけを正確に表現します。
