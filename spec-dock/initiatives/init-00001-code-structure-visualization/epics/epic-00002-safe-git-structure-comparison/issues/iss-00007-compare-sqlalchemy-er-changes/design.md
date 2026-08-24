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
| I04-DES-001 | I04-REQ-001 | SQLAlchemy diff application serviceがshared comparison spineとER matcher/rendererをone observable runで調整する。 |
| I04-DES-002 | I04-REQ-002 | ISSUE-02のstart-HEAD endpoint、freeze、metadata-only FileChangeSet、changed-path admission contractをそのままconsumeする。 |
| I04-DES-003 | I04-REQ-003 | DomainPresenceResolverとcanonical empty-sideをtyped ER table/row differへ接続する。 |
| I04-DES-004 | I04-REQ-004 | ER diff serializerがside descriptors、table/row delta、ghost/before-after、matching、safe provenanceを分離する。 |
| I04-DES-005 | I04-REQ-005 | side analysis failure、domain-local entity overrun、matching ambiguityをfabricated deltaなしのtyped outcomeへ写像する。 |
| I04-DES-006 | I04-REQ-006 | DB/import execution trap、literal/raw-hunk redaction、read-only Git、determinism/atomicityを検証する。 |

## Current / Target

### Current（verified baseline）

- exact verified current commit `867ee6929283dfc84711bce245b784d2b8e3e9e6` は本Issueのcanonical Requirement/Design/Plan、accepted ADR、interviewを含む。
- production package、CLI、domain adapter、schema implementation、acceptance fixturesは未実装であり、以下のpath/symbolはすべてplannedである。
- 本Designは親の横断contractをslice固有の構造へ具体化し、依存Issueのpublic contractを変更せずに後続sliceへ渡す。

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

### shared source/endpoint boundary

ISSUE-02の`ComparisonEndpointResolver`、`WorkingTreeFreezer`、`ChangedPathAdmissionGate`、`FileChangeSet<HunkMetadata>`をpublic contractとしてconsumeする。`--to working-tree`だけの場合はstart HEAD anchorを使い、ER adapterが別anchorを選ばない。

### ER side pair and empty-side

`SqlAlchemySide`は`real snapshot`、`canonical-empty-side`、`analysis-failed`のunion。empty-sideは`code-structure-viz.empty-side/v1`、domain `sqlalchemy`、empty recordsのcanonical digestで、standalone publishしない。before-onlyは全removed、after-onlyは全added、both-absentはnot_applicable、analysis-failedを含むpairはincompleteでdelta payloadを作らない。

### row diff/output model

`ErSemanticDiff`はtable deltaとcolumn/constraint/index/relationship row deltaを別collectionで持つ。removed rowはbefore representationをghostとして持ち、modified rowはredacted normalized before/afterを持つ。matching evidenceはexact identityまたはhigh-confidence one-to-oneだけ。

### budget, redaction, publication

- run-level changed-path overrunはISSUE-02同様exit 1、diagnostic only、final manifestなし。
- ER diagram entity overrunはdomain incomplete exit 3、affected JSON/PlantUMLなし、safe manifestへcount/limitを記録。valid overrideは通常公開。
- HunkMetadataはranges/status/content-independent IDだけ。SQL default/source/raw patch/comment/literal/secret/absolute pathをmodel/Artifact/logへ入れない。
- side acquisition/static analysis failureとentity overrunはsuccessful siblingのないsingle-domain runでもsafe run manifestを公開しexit 3にする。

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
- docs/contracts/ に schema と CLI behavior を配置する。これらはplanned implementation targetであり、本Designは実装済みとは扱わない。
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
| I04-AT-001 | row delta | tests/acceptance/sqlalchemy/test_diff_cli.py | uv run pytest tests/acceptance/sqlalchemy/test_diff_cli.py -q |
| I04-AT-002 | ghost rendering | tests/golden/sqlalchemy/test_row_visuals.py | uv run pytest tests/golden/sqlalchemy/test_row_visuals.py -q |
| I04-AT-003 | matching | tests/integration/sqlalchemy/test_er_matching.py | uv run pytest tests/integration/sqlalchemy/test_er_matching.py -q |
| I04-AT-004 | side failure | tests/acceptance/sqlalchemy/test_diff_failures.py | uv run pytest tests/acceptance/sqlalchemy/test_diff_failures.py -q |
| I04-AT-005 | redaction | tests/security/test_sqlalchemy_diff_redaction.py | uv run pytest tests/security/test_sqlalchemy_diff_redaction.py -q |
| I04-AT-006 | impact union | tests/integration/sqlalchemy/test_er_impact.py | uv run pytest tests/integration/sqlalchemy/test_er_impact.py -q |
| I04-AT-007 | domain presence | tests/acceptance/sqlalchemy/test_diff_domain_presence.py | uv run pytest tests/acceptance/sqlalchemy/test_diff_domain_presence.py -q |
| I04-AT-008 | working-tree anchor | tests/acceptance/sqlalchemy/test_working_tree_anchor.py | uv run pytest tests/acceptance/sqlalchemy/test_working_tree_anchor.py -q |
| I04-AT-009 | hunk safety | tests/security/test_sqlalchemy_diff_hunk_redaction.py | uv run pytest tests/security/test_sqlalchemy_diff_hunk_redaction.py -q |
| I04-AT-010 | entity budget | tests/acceptance/sqlalchemy/test_diff_entity_budget.py | uv run pytest tests/acceptance/sqlalchemy/test_diff_entity_budget.py -q |

- unit testはdomain parser/matcher/serializerとcanonicalizationのpure functionを対象にする。
- integration testはtemporary Git repositoryまたはimmutable source fixtureを使い、Git stateとsource bytesのbefore/afterを比較する。
- acceptance testは実CLI process、output directory、manifest/checksum、exit code、stdout/stderr、published file setを観測する。
- security testはimport/build/plugin/DB execution trap、source/secret/literal/absolute path/raw hunkのnegative scan、unsafe symlink、Git mutation allowlistを検査する。
- table-driven casesはstatusだけでなくpublication、manifest presence/absence、digest、requested/resolved budget values、actual countsまでassertする。

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
