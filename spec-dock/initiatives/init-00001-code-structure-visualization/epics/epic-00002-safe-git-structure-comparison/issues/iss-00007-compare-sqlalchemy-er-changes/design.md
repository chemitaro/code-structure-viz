---
種別: 設計書（Issue）
ID: "iss-00007"
タイトル: "Compare SQLAlchemy ER Changes"
関連GitHub: ["#7"]
package_sequence_key: "ISSUE-04"
状態: "draft"
最終更新: "2026-08-24"
依存: ["requirement.md"]
親: ["epic-00002", "init-00001"]
---

# iss-00007 Compare SQLAlchemy ER Changes — 設計

詳細: [Design Guide](../../../../../../docs/authoring/design.md)

## 設計目標

- `sqlalchemy` domain の `diff` を、CLI から source acquisition、analysis、versioned JSON、PlantUML、manifest、diagnostic まで一つの vertical pipeline として設計する。
- accepted ADR の独立 product ownership、named endpoint、dual snapshot、adapter boundary、agent-first Artifact、安全な static analysis、product HTML exclusion、vertical slicing を破らない。
- common abstraction は lifecycle、diagnostic、Artifact descriptor、graph primitive に限定し、domain-specific identity/member/relation/matching を adapter が所有する。

| Design ID | Requirement trace | 判断 |
| --- | --- | --- |
| I04-DES-001 | I04-REQ-001 | CLI/application boundary と domain port を分離し、observable outcome を一 run transaction にまとめる。 |
| I04-DES-002 | I04-REQ-002 | source acquisition は immutable SourceView と provenance を返し、parser が repository state を直接読まない。 |
| I04-DES-003 | I04-REQ-003 | domain-owned identity/member/relation model を common envelope から分離する。 |
| I04-DES-004 | I04-REQ-004 | ArtifactPublisher が JSON/PlantUML/manifest の staging、collision check、SHA-256、atomic publication を所有する。 |
| I04-DES-005 | I04-REQ-005 | typed diagnostic と complete/not_applicable/incomplete state machine で failure を空結果へ潰さない。 |

## Current / Target

### Current（verified baseline）

- exact commit `7951ddabc2e6a3d66edb77eada7c6c16923264f7` は SpecDock 0.2.3、template 状態の canonical R/D/P、interview、8 accepted ADR を含む。
- CodeStructureViz の production package、CLI、domain adapter、semantic schema、acceptance fixtures は存在しない。
- `pyclassuml` と `tree-git-diff` は legacy evidence であり、CodeStructureViz の dependency ではない。

### Target

- coding agent が before/after declarative ORM semantics を比較し、table と column/constraint/index/relationship の row-level delta、ghost removal、影響 context を説明できる。
- source/body/secret を漏らさず、failure と coverage を manifest で agent が機械判定できる。
- downstream Issue はこの Design の stable interface だけへ依存し、内部 class layout を fork しない。

## 責務・Interface

### planned component responsibilities

| planned path / symbol | 状態 | 責務 |
| --- | --- | --- |
| src/code_structure_viz/adapters/sqlalchemy/differ.py::SqlAlchemySemanticDiffer（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/adapters/sqlalchemy/matcher.py::SqlAlchemyMoveMatcher（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/adapters/sqlalchemy/diff_model.py（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/adapters/sqlalchemy/diff_renderer.py（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/semantic/impact.py の domain graph extension（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |

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

- 一方の endpoint の model が解析不能な場合、その table/row を removed/added と断定せず domain incomplete とする。
- ambiguous rename/move は removed+added。default literal の raw value が必要な matching は行わない。
- diagram entity 500 超過は切り捨てず nonzero。明示 override と resulting count を manifest に記録する。

## 変更対象

| planned file | planned change | 存在確認 |
| --- | --- | --- |
| src/code_structure_viz/adapters/sqlalchemy/differ.py::SqlAlchemySemanticDiffer（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/adapters/sqlalchemy/matcher.py::SqlAlchemyMoveMatcher（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/adapters/sqlalchemy/diff_model.py（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/adapters/sqlalchemy/diff_renderer.py（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/semantic/impact.py の domain graph extension（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |

追加で planned:

- tests/fixtures/compare-sqlalchemy-er-changes/ に source-only fixture を置き、fixture の application code を実行しない。
- docs/contracts/ に schema と CLI behavior を配置する。ただし本 package は repository へ直接変更を行わない。
- lockfile と license inventory を同じ Issue の acceptance に含める。

変更しない領域:

- DB migration risk の自動判定、Alembic operation の生成
- live DB schema drift、runtime mapper state
- Next.js/Python cross-domain relation
- HTML report generation

## 移行・互換性・rollback

- baseline に production implementation がないため in-place data migration は N/A。
- public schema/CLI は `/v1` と preview release で開始し、同一 major 内は field の additive extension を原則とする。
- DB migration は実行しないため N/A。誤った row kind/matching は affected analysis を incomplete に狭める forward fix を優先する。intermediate release 後の schema break は version up と compatibility fixture で回復する。
- legacy CLI compatibility layer は作らない。legacy evidence の algorithm/test idea を採用するときは provenance note、license decision、CodeStructureViz-owned regression test を同じ change に含める。

## testability

| Test ID | 分類 | planned test file | command |
| --- | --- | --- | --- |
| I04-AT-001 | normal | tests/acceptance/sqlalchemy/test_diff_cli.py | uv run pytest tests/acceptance/sqlalchemy/test_diff_cli.py -q |
| I04-AT-002 | visual | tests/acceptance/sqlalchemy/test_diff_plantuml.py | uv run pytest tests/acceptance/sqlalchemy/test_diff_plantuml.py -q |
| I04-AT-003 | matching | tests/integration/sqlalchemy/test_move_matching.py | uv run pytest tests/integration/sqlalchemy/test_move_matching.py -q |
| I04-AT-004 | negative | tests/acceptance/sqlalchemy/test_diff_failures.py | uv run pytest tests/acceptance/sqlalchemy/test_diff_failures.py -q |
| I04-AT-005 | security | tests/security/test_er_diff_redaction.py | uv run pytest tests/security/test_er_diff_redaction.py -q |
| I04-AT-006 | impact | tests/integration/sqlalchemy/test_impact_union_graph.py | uv run pytest tests/integration/sqlalchemy/test_impact_union_graph.py -q |

- unit test は domain parser/matcher/serializer の pure function を対象にする。
- integration test は temporary Git repository と immutable fixture source を使い、Git state の before/after fingerprint を比較する。
- acceptance test は実際の CLI process、output directory、manifest/checksum、exit code、stdout/stderr を観測する。
- security test は import/build/plugin/DB execution trap、secret literal、absolute path、unsafe symlink、Git mutation allowlist を検査する。

## risk

- row matching の誤結合が schema review を誤らせる。exact identity 優先、strict one-to-one moved、ambiguity は removed+added とする。
- ghost row が現行 row と混同される。red/dashed/`-` と before-only label を併用する。
- SQL default 比較が secret を漏らす。raw value を model に載せず、parser boundary で redaction する。

- Re-evaluation trigger: security/privacy incident、target repository の不可逆変更、secret leak、rollback に incident response が必要な設計へ変わる場合は Planning Level を `critical` に上げる。
- Stop condition: 全 row kind の before/after delta、ghost rendering、ambiguous matching、片側解析 failure が acceptance で固定されるまで intermediate release を宣言しない。

```plantuml
@startuml
title SQLAlchemy ER diff の row-level 表現
left to right direction
component "before ER snapshot" as Before
component "after ER snapshot" as After
component "SqlAlchemySemanticDiffer" as Differ
component "table delta" as TableDelta
component "row delta
column / constraint / index / relationship" as RowDelta
component "ghost row 付き ER PlantUML" as Diagram
Before -> Differ : before table と row
After -> Differ : after table と row
Differ -> TableDelta : entity change
Differ -> RowDelta : member change と before/after 値
TableDelta -> Diagram : + - ~ → ?
RowDelta -> Diagram : removed row を ghost 表示
@enduml
```

table 全体だけでなく、column・constraint・index・relationship の差を before/after 値と ghost row で保持します。
