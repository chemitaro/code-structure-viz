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
| I03-DES-001 | I03-REQ-001 | CLI/application boundary と domain port を分離し、observable outcome を一 run transaction にまとめる。 |
| I03-DES-002 | I03-REQ-002 | source acquisition は immutable SourceView と provenance を返し、parser が repository state を直接読まない。 |
| I03-DES-003 | I03-REQ-003 | domain-owned identity/member/relation model を common envelope から分離する。 |
| I03-DES-004 | I03-REQ-004 | ArtifactPublisher が JSON/PlantUML/manifest の staging、collision check、SHA-256、atomic publication を所有する。 |
| I03-DES-005 | I03-REQ-005 | typed diagnostic と complete/not_applicable/incomplete state machine で failure を空結果へ潰さない。 |

## Current / Target

### Current（verified baseline）

- exact commit `7951ddabc2e6a3d66edb77eada7c6c16923264f7` は SpecDock 0.2.3、template 状態の canonical R/D/P、interview、8 accepted ADR を含む。
- CodeStructureViz の production package、CLI、domain adapter、semantic schema、acceptance fixtures は存在しない。
- `pyclassuml` と `tree-git-diff` は legacy evidence であり、CodeStructureViz の dependency ではない。

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

### semantic envelope

- `schema`: `code-structure-viz.semantic/v1`
- `document_kind`: `snapshot` または `diff`
- `domain`: `sqlalchemy`
- `status`: `complete`、`not_applicable`、`incomplete`
- `entities`、`members`、`relations`: domain-owned payload
- `coverage`: selected/discovered/analyzed/skipped/unknown counts と frontier
- `diagnostics`: stable code、severity、scope、recoverability、safe location
- `provenance`: tool/contract/adapter version、endpoint digest、resolved config digest

### visual vocabulary

| 意味 | 色 | 記号/線 |
| --- | --- | --- |
| added | green | `+` |
| removed | red | `-` と dashed |
| modified | yellow | `~` |
| moved | blue | `→` |
| unknown | gray | `?` |

色は補助であり、dark mode でも legend、記号、線種、text label を維持する。

### state and failure taxonomy

```text
requested -> preflight -> source_acquired -> analyzed -> rendered -> staged -> verified -> published
                 |              |              |           |          |
                 +-> usage/fatal+-> incomplete +-> incomplete+-> fatal+-> fatal
```

- usage/config: invalid option、unknown config key、type error。exit 2。
- core fatal: invalid repository、endpoint unresolved、fingerprint drift、output collision、minimum runtime 不足。exit 1。
- domain incomplete: target があるが parse/protocol/semantic coverage を安全に完了できない。exit 3。
- interrupt: staging を cleanup、exit 130。

- declarative target 候補があるのに DB/runtime evaluation を必要とする場合は unknown/incomplete とし、評価して補完しない。
- 同一 schema.table identity が競合する場合は duplicate diagnostic として incomplete。勝手に module path を identity へ追加して解消しない。
- entity budget 超過は無切り捨て nonzero、明示 `--max-entities` override のみ許可する。

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
- docs/contracts/ に schema と CLI behavior を配置する。ただし本 package は repository へ直接変更を行わない。
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
| I03-AT-002 | semantic | tests/integration/sqlalchemy/test_semantic_rows.py | uv run pytest tests/integration/sqlalchemy/test_semantic_rows.py -q |
| I03-AT-003 | negative | tests/acceptance/sqlalchemy/test_snapshot_failures.py | uv run pytest tests/acceptance/sqlalchemy/test_snapshot_failures.py -q |
| I03-AT-004 | security | tests/security/test_sqlalchemy_static_boundary.py | uv run pytest tests/security/test_sqlalchemy_static_boundary.py -q |
| I03-AT-005 | determinism | tests/acceptance/sqlalchemy/test_snapshot_determinism.py | uv run pytest tests/acceptance/sqlalchemy/test_snapshot_determinism.py -q |
| I03-AT-006 | applicability | tests/acceptance/sqlalchemy/test_applicability.py | uv run pytest tests/acceptance/sqlalchemy/test_applicability.py -q |

- unit test は domain parser/matcher/serializer の pure function を対象にする。
- integration test は temporary Git repository と immutable fixture source を使い、Git state の before/after fingerprint を比較する。
- acceptance test は実際の CLI process、output directory、manifest/checksum、exit code、stdout/stderr を観測する。
- security test は import/build/plugin/DB execution trap、secret literal、absolute path、unsafe symlink、Git mutation allowlist を検査する。

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
