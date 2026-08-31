---
種別: 設計書（Issue）
ID: "iss-00009"
タイトル: "Compare Next.js Component Changes"
関連GitHub: ["#9"]
package_sequence_key: "ISSUE-06"
状態: "draft"
最終更新: "2026-08-31"
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
| I06-DES-007 | I06-REQ-007 | closed stdout selectorをsource acquisition前に検証し、publication後exact bytesまたはtyped unavailable resultをstderr diagnosticsと分離して出す。 |

## Current / Target

### Current（canonical specification state）

- 本 Issue の canonical state は stable scope ID と repository-relative Requirement/Design/Plan path、accepted ADR、interviewで識別する。採用・実装開始時に HEAD と configured upstream を再検証し、current commit SHA を本文へ固定しない。
- production Python package、snapshot/diff CLI、common schema/writer/source infrastructureは実装済みである。Next snapshot/diff adapter、Next schema、Next acceptance fixturesは未実装であり、以下のNext固有path/symbolはplannedである。
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
code-structure-viz snapshot --repo PATH --output-dir PATH [--domain DOMAIN] [--target SELECTOR] [--format FORMAT] [--config PATH] [--stdout SELECTOR]
code-structure-viz diff --repo PATH --output-dir PATH [--domain DOMAIN] [--from ENDPOINT] [--to ENDPOINT] [--format FORMAT] [--config PATH] [--stdout SELECTOR]
```

- `--output-dir` は必須。writer は existing file を置換せず、全 payload を staging 後に公開する。
- `--format` 未指定は semantic JSON と PlantUML。`--stdout` は output directory requirement を解除しない。
- analysis behavior を environment variable で変更しない。環境は executable discovery と locale-independent process setup にだけ使う。

### stdout selector and stream routing

CLI parser は `--stdout` を optional single-value option として一度だけ受理し、closed grammar `manifest | DOMAIN:FORMAT` を `StdoutSelector` valueへ正規化する。domain/format の resolved selection が確定した直後、source acquisition より前に selector compatibility を検証する。boolean、path、alias、略記、大小文字違い、値省略、重複、未選択 domain、未要求 format は `UsageError` とし、source acquisition と publication の前に exit 2、stdout 空、Artifact 0件で終了する。`OutputTransaction` は開始しない。

通常 publication 後、既存 CLI/application boundary 内の stdout emitter は次のいずれか一つだけを行う。新しい command または独立 architecture layer は追加しない。

1. selector なしなら `run-summary/v1` を canonical JSON 1行として出す。
2. selected Artifact が利用可能なら、公開 file を binary read して exact bytes を複製する。
3. selected Artifact が利用不能なら、`RunOutcome`/`DomainOutcome` から `stdout-result/v1` 1行を構築する。

stdout emitter は diagnostic renderer と分離し、diagnostic は stderr だけへ出す。exact-byte copy に summary、BOM、改行補正を加えない。`stdout-result/v1` は status と stable reason だけを参照し、source content、absolute path、secret を受け取る field を持たない。handled SIGINT は cleanup 完了後に `run_status: interrupted` を返せる場合だけ exit 130 の result line を出す。process を強制終了された場合の出力は契約外である。

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

### incomplete classes and publication

`DomainOutcome` は `status` に加え、status が `incomplete` の場合だけ `incomplete_kind: partial_safe | payload_unavailable` と `payload_available` を持つ。

- `partial_safe` は isolated failure set、safe subset、explicit coverage frontier、safe diagnostics、redaction pass、entity-budget pass、requested renderer passをすべて満たす場合だけ生成する。requested domain payload と manifest descriptor を同一 transaction で公開する。
- `payload_unavailable` は safe subset不在、global acquisition/protocol/schema/security/unsafe-path failure、entity overrun、または diff side failureで生成する。affected payload descriptorは空とし、safe core manifestだけを許す。
- 本IssueのNext単独runはどちらも`incomplete`/exit 3へ写像する。run-level fatalだけがfinal manifestを含む全stagingを破棄する。all-domain aggregationとhealthy sibling保持はISSUE-07が所有する。

serializer と manifest builder は `incomplete_kind` と `payload_available` の整合を検証する。`partial_safe` なのにrequested descriptorが欠ける状態、`payload_unavailable` なのにaffected descriptorがある状態はinternal contract failureとしてpublication前に拒否する。

このdiff sliceではside acquisition/static analysis failureを必ず`payload_unavailable`に固定し、canonical empty-sideまたは`partial_safe`として比較を継続しない。
## data / failure

### shared comparison and adapter boundary

ISSUE-02のendpoint/freeze/FileChangeSet/changed-path contractをconsumeし、ISSUE-05 adapterをbefore/after SourceViewへ別processで実行する。`--to working-tree` onlyではrequested endpoint、frozen digest、start HEAD anchor、selected candidate、merge-base、resolution methodを全side provenanceへ共有する。

### Next domain presence and empty-side

`NextSide`はreal snapshot、canonical empty-side、analysis-failedのunion。empty-sideは`code-structure-viz.empty-side/v1` domain `next`のcanonical digestでstandalone publishしない。before-only/after-onlyは全removed/added、both-absentはnot_applicable、adapter/config/protocol/static-analysis failureを含むpairはincompleteでaffected diff payloadなし。

### ISSUE-05 handoff and semantic diff

各sideはISSUE-05のversioned contractをそのまま消費する。

- Componentのprimary keyは`ComponentDeclarationResolution/v1`が生成するdeclaration identityである。export alias、route、range、order、diagnosticはidentityへ含めない。
- `ExportBindingResolution/v1`のdirect/default/re-export/star bindingはComponentと別memberとして比較する。barrel移動、export alias変更、default/named再公開はbinding deltaであり、同じdeclaration Componentのremoved/addedを生成しない。
- Propとprimitive relation（value/type import、render、component_wrap、client_entry、router context）をprimary delta/seedにする。
- `BoundaryRolePropagation/v1`が導出する`client_dependency`、`server_candidate`、dual role、`boundary_effect`はcontextとして再計算する。derived role単独の変化をmatching keyやprimary seedにしない。
- exact declaration identityが片側に存在しない場合だけ、rename evidence、structural fingerprint、unique candidateをすべて満たす候補をmovedとする。ExportBinding、route、range、order、diagnostic、derived roleはmoved evidenceに使わない。
- 各sideは独立した`SourceAcquisitionPlan/v1`、`domain_config_projection("next")`/digest、TrustedTypeEnvironment digest、adapter/protocol/model versionを持つ。一方のcompiler/config/type environmentを他方へ適用しない。
- sideのsource acquisition、protocol、schema、config、TrustedTypeEnvironment、static analysisが失敗した場合はdiff payloadをunavailableとし、canonical empty-side、removed/added、movedを捏造しない。

impact graphはbefore/after primitive static relation unionで、removed componentはbefore edgeを使う。nonliteral dynamic behaviorはunknownでruntime relationを生成しない。

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
| I06-AT-011 | slice-local changed-path admission | tests/acceptance/next/test_diff_changed_path_admission.py | 1,001 fatal/no-publicationとoverride provenance |
| I06-AT-012 | stdout selector matrix | tests/acceptance/next/test_stdout_selector.py | selector grammar、exact bytes、unavailable result、summary、stderr、exit/publication |

- unit testはdomain parser/matcher/serializerとcanonicalizationのpure functionを対象にする。
- integration testはtemporary Git repositoryまたはimmutable source fixtureを使い、Git stateとsource bytesのbefore/afterを比較する。
- acceptance testは実CLI process、output directory、manifest/checksum、exit code、stdout/stderr、published file setを観測する。
- security testはimport/build/plugin/DB execution trap、source/secret/literal/absolute path/raw hunkのnegative scan、unsafe symlink、Git mutation allowlistを検査する。
- table-driven casesはstatusだけでなくpublication、manifest presence/absence、digest、requested/resolved budget values、actual countsまでassertする。

- `--domain next` consumer wiringで1,001-path gate bypassがないこととvalid override provenanceをslice-local acceptanceで検証する。

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
