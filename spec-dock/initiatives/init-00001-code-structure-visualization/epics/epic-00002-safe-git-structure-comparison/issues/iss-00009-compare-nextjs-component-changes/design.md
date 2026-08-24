---
種別: 設計書（Issue）
ID: "iss-00009"
タイトル: "Compare Next.js Component Changes"
関連GitHub: ["#9"]
package_sequence_key: "ISSUE-06"
状態: "draft"
最終更新: "2026-08-24"
依存: ["requirement.md"]
親: ["epic-00002", "init-00001"]
---

# iss-00009 Compare Next.js Component Changes — 設計

詳細: [Design Guide](../../../../../../docs/authoring/design.md)

## 設計目標

- `next` domain の `diff` を、CLI から source acquisition、analysis、versioned JSON、PlantUML、manifest、diagnostic まで一つの vertical pipeline として設計する。
- accepted ADR の独立 product ownership、named endpoint、dual snapshot、adapter boundary、agent-first Artifact、安全な static analysis、product HTML exclusion、vertical slicing を破らない。
- common abstraction は lifecycle、diagnostic、Artifact descriptor、graph primitive に限定し、domain-specific identity/member/relation/matching を adapter が所有する。

| Design ID | Requirement trace | 判断 |
| --- | --- | --- |
| I06-DES-001 | I06-REQ-001 | Next diff application serviceがshared comparison spineとfirst-party adapter/differ/rendererをone runで調整する。 |
| I06-DES-002 | I06-REQ-002 | ISSUE-02のstart-HEAD endpoint、freeze、metadata-only FileChangeSet、changed-path admissionをconsumeし、両side adapterを独立実行する。 |
| I06-DES-003 | I06-REQ-003 | DomainPresenceResolverとcanonical empty-sideをNext component/member/relation differへ接続する。 |
| I06-DES-004 | I06-REQ-004 | Next diff serializerがside/adapter descriptors、semantic changes、impact、matching、safe provenanceを分離する。 |
| I06-DES-005 | I06-REQ-005 | side adapter/config/protocol failure、entity overrun、matching ambiguityをfabricated deltaなしのtyped outcomeへ写像する。 |
| I06-DES-006 | I06-REQ-006 | runtime behavior非推測、build非実行、raw-hunk/source redaction、read-only Git、determinismを検証する。 |

## Current / Target

### Current（verified baseline）

- exact verified current commit `867ee6929283dfc84711bce245b784d2b8e3e9e6` は本Issueのcanonical Requirement/Design/Plan、accepted ADR、interviewを含む。
- production package、CLI、domain adapter、schema implementation、acceptance fixturesは未実装であり、以下のpath/symbolはすべてplannedである。
- 本Designは親の横断contractをslice固有の構造へ具体化し、依存Issueのpublic contractを変更せずに後続sliceへ渡す。

### Target

- coding agent が before/after Next.js semantic snapshot から component/props/import/render/boundary change と影響 context を比較できる。
- source/body/secret を漏らさず、failure と coverage を manifest で agent が機械判定できる。
- downstream Issue はこの Design の stable interface だけへ依存し、内部 class layout を fork しない。

## 責務・Interface

### planned component responsibilities

| planned path / symbol | 状態 | 責務 |
| --- | --- | --- |
| adapters/next/src/diff.ts::diffNextSnapshots（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| adapters/next/src/matcher.ts::matchMovedComponents（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| adapters/next/src/diff-render.ts（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/adapters/next/diff_bridge.py（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/semantic/impact.py の Next relation extension（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |

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

### shared comparison and adapter boundary

ISSUE-02のendpoint/freeze/FileChangeSet/changed-path contractをconsumeし、ISSUE-05 adapterをbefore/after SourceViewへ別processで実行する。`--to working-tree` onlyではstart HEAD anchorを全side provenanceへ使う。

### Next domain presence and empty-side

`NextSide`はreal snapshot、canonical empty-side、analysis-failedのunion。empty-sideは`code-structure-viz.empty-side/v1` domain `next`のcanonical digestでstandalone publishしない。before-only/after-onlyは全removed/added、both-absentはnot_applicable、adapter/config/protocol/static-analysis failureを含むpairはincompleteでaffected diff payloadなし。

### semantic diff and unknown

component/prop/import/JSX render/use-client boundary deltaだけをseedにする。impact graphはbefore/after static relation unionで、removed componentはbefore edgeを使う。nonliteral dynamic behaviorはunknownでruntime relationを生成しない。matchingはexact identityまたはhigh-confidence unique candidateだけ。

### budget, hunk safety, publication

run-level changed-path overrunはexit 1、diagnostic only、final manifestなし。domain entity overrunはexit 3、affected JSON/PlantUMLなし、safe manifest countあり。HunkMetadataはrange/status/content-independent IDだけで、raw patch/source/comment/literal/secret/absolute pathをbridge/adapter/model/Artifact/logへ渡さない。

## 変更対象

| planned file | planned change | 存在確認 |
| --- | --- | --- |
| adapters/next/src/diff.ts::diffNextSnapshots（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| adapters/next/src/matcher.ts::matchMovedComponents（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| adapters/next/src/diff-render.ts（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/adapters/next/diff_bridge.py（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/semantic/impact.py の Next relation extension（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |

追加で planned:

- tests/fixtures/compare-nextjs-component-changes/ に source-only fixture を置き、fixture の application code を実行しない。
- docs/contracts/ に schema と CLI behavior を配置する。これらはplanned implementation targetであり、本Designは実装済みとは扱わない。
- lockfile と license inventory を同じ Issue の acceptance に含める。

変更しない領域:

- runtime render tree と hydration behavior の差分
- bundle analysis、Next build output、browser DOM diff
- cross-domain aggregation と overall exit decision
- HTML report generation

## 移行・互換性・rollback

- baseline に production implementation がないため in-place data migration は N/A。
- public schema/CLI は `/v1` と preview release で開始し、同一 major 内は field の additive extension を原則とする。
- persistent migration は N/A。adapter diff failure は domain incomplete へ隔離する。公開 contract の誤りは旧 reader/golden fixture を保持した additive fix、または adapter/semantic schema version up で回復する。
- legacy CLI compatibility layer は作らない。legacy evidence の algorithm/test idea を採用するときは provenance note、license decision、CodeStructureViz-owned regression test を同じ change に含める。

## testability

| Test ID | 分類 | planned test file | command |
| --- | --- | --- | --- |
| I06-AT-001 | normal | tests/acceptance/next/test_diff_cli.py | uv run pytest tests/acceptance/next/test_diff_cli.py -q |
| I06-AT-002 | semantic seed | tests/acceptance/next/test_semantic_seed.py | uv run pytest tests/acceptance/next/test_semantic_seed.py -q |
| I06-AT-003 | matching | tests/integration/next/test_component_matching.py | uv run pytest tests/integration/next/test_component_matching.py -q |
| I06-AT-004 | side failure | tests/acceptance/next/test_diff_failures.py | uv run pytest tests/acceptance/next/test_diff_failures.py -q |
| I06-AT-005 | impact union | tests/integration/next/test_component_impact.py | uv run pytest tests/integration/next/test_component_impact.py -q |
| I06-AT-006 | unknown dynamic | adapters/next/test/dynamic-unknown.test.ts | npm --prefix adapters/next test -- dynamic-unknown |
| I06-AT-007 | domain presence | tests/acceptance/next/test_diff_domain_presence.py | uv run pytest tests/acceptance/next/test_diff_domain_presence.py -q |
| I06-AT-008 | working-tree anchor | tests/acceptance/next/test_working_tree_anchor.py | uv run pytest tests/acceptance/next/test_working_tree_anchor.py -q |
| I06-AT-009 | hunk safety | tests/security/test_next_diff_hunk_redaction.py | uv run pytest tests/security/test_next_diff_hunk_redaction.py -q |
| I06-AT-010 | entity budget | tests/acceptance/next/test_diff_entity_budget.py | uv run pytest tests/acceptance/next/test_diff_entity_budget.py -q |

- unit testはdomain parser/matcher/serializerとcanonicalizationのpure functionを対象にする。
- integration testはtemporary Git repositoryまたはimmutable source fixtureを使い、Git stateとsource bytesのbefore/afterを比較する。
- acceptance testは実CLI process、output directory、manifest/checksum、exit code、stdout/stderr、published file setを観測する。
- security testはimport/build/plugin/DB execution trap、source/secret/literal/absolute path/raw hunkのnegative scan、unsafe symlink、Git mutation allowlistを検査する。
- table-driven casesはstatusだけでなくpublication、manifest presence/absence、digest、requested/resolved budget values、actual countsまでassertする。

## risk

- before/after compiler option 差を一方へ寄せると false diff が生じる。各 snapshot が自身の config digest と resolution context を所有する。
- component moved の誤結合は review を誤らせる。Python と同じ confidence contract を domain-owned fingerprint で実装する。
- runtime behavior の推測が agent の説明へ混入する。unknown marker と coverage limitation を一次 output にする。

- Re-evaluation trigger: security/privacy incident、target repository の不可逆変更、secret leak、rollback に incident response が必要な設計へ変わる場合は Planning Level を `critical` に上げる。
- Stop condition: Next member/relation seed、union impact、adapter partial failure、unknown dynamic behavior が acceptance で固定されるまで全 domain 集約へ進まない。

```plantuml
@startuml
title Next.js semantic diff と unknown の扱い
left to right direction
component "before component snapshot" as Before
component "after component snapshot" as After
component "Next semantic differ" as Differ
component "static relation union graph" as Graph
component "unknown diagnostic
non-literal dynamic behavior" as Unknown
component "context 限定 diff Artifact" as Output
Before -> Differ : component・props・relation
After -> Differ : component・props・relation
Differ -> Graph : semantic changed seed
Differ -> Unknown : 推測しない挙動を記録する
Graph -> Output : upstream/downstream context
Unknown -> Output : ? と coverage limitation
@enduml
```

静的に証明できる component change と impact だけを出力し、runtime 動作は unknown として明示します。
