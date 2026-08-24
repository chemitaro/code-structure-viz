---
種別: 設計書（Issue）
ID: "iss-00008"
タイトル: "Generate Next.js Component Snapshots"
関連GitHub: ["#8"]
package_sequence_key: "ISSUE-05"
状態: "draft"
最終更新: "2026-08-24"
依存: ["requirement.md"]
親: ["epic-00002", "init-00001"]
---

# iss-00008 Generate Next.js Component Snapshots — 設計

詳細: [Design Guide](../../../../../../docs/authoring/design.md)

## 設計目標

- `next` domain の `snapshot` を、CLI から source acquisition、analysis、versioned JSON、PlantUML、manifest、diagnostic まで一つの vertical pipeline として設計する。
- accepted ADR の独立 product ownership、named endpoint、dual snapshot、adapter boundary、agent-first Artifact、安全な static analysis、product HTML exclusion、vertical slicing を破らない。
- common abstraction は lifecycle、diagnostic、Artifact descriptor、graph primitive に限定し、domain-specific identity/member/relation/matching を adapter が所有する。

| Design ID | Requirement trace | 判断 |
| --- | --- | --- |
| I05-DES-001 | I05-REQ-001 | Next snapshot application serviceがapplicability、bridge、adapter、per-domain outputをone runで調整する。 |
| I05-DES-002 | I05-REQ-002 | first-party Node processをversioned stdin/stdout protocolでisolateし、target evidence不在時は起動しない。 |
| I05-DES-003 | I05-REQ-003 | module path + exported component name identityとprops/static relations/client boundaryをNext adapterが所有する。 |
| I05-DES-004 | I05-REQ-004 | next-adapter/v1 responseをvalidateしてsemantic/v1 domain `next`へlossless mappingする。 |
| I05-DES-005 | I05-REQ-005 | dynamic unknown、protocol/static-analysis failure、domain-local entity overrunをtyped incompleteへ写像する。 |
| I05-DES-006 | I05-REQ-006 | build/config/plugin/application non-execution、literal/path redaction、protocol determinism、optional Node separationを検証する。 |

## Current / Target

### Current（verified baseline）

- exact verified current commit `867ee6929283dfc84711bce245b784d2b8e3e9e6` は本Issueのcanonical Requirement/Design/Plan、accepted ADR、interviewを含む。
- production package、CLI、domain adapter、schema implementation、acceptance fixturesは未実装であり、以下のpath/symbolはすべてplannedである。
- 本Designは親の横断contractをslice固有の構造へ具体化し、依存Issueのpublic contractを変更せずに後続sliceへ渡す。

### Target

- coding agent が first-party TypeScript adapter を通じ、Next.js repository の module、exported component、props、static relation、client boundary を JSON と PlantUML で取得できる。
- source/body/secret を漏らさず、failure と coverage を manifest で agent が機械判定できる。
- downstream Issue はこの Design の stable interface だけへ依存し、内部 class layout を fork しない。

## 責務・Interface

### planned component responsibilities

| planned path / symbol | 状態 | 責務 |
| --- | --- | --- |
| src/code_structure_viz/adapters/next/bridge.py::NextAdapterBridge（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/adapters/next/protocol.py（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| adapters/next/package.json と package-lock.json（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| adapters/next/tsconfig.json（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| adapters/next/src/analyze.ts::analyzeRepository（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| adapters/next/src/model.ts（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| adapters/next/src/render.ts（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |

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

### adapter protocol and semantic model

Python bridgeは`code-structure-viz.next-adapter/v1` requestをstdinへ送り、stdoutのexact one JSON documentをvalidateする。adapterはTypeScript compiler APIだけを使い、build/config plugin/applicationを実行しない。responseのmodule/export/component/prop/import/render/client-boundary recordsをdomain `next` snapshotへcanonical mapする。

### applicability and failure

- static Next target evidence不在は`not_applicable`でNode probeなし。
- target evidenceがあるNode missing、protocol noise/schema mismatch、tsconfig resolution/static analysis failureは`incomplete`。safe partial snapshotをpublishする場合はstatus/coverage/diagnosticをpayloadへ明示する。
- nonliteral dynamic behaviorはunknown diagnosticとcoverage countで、runtime tree/relationを作らない。

### entity budget and publication

`EntityBudgetGate`（planned）はNext diagram entity countをrender前にdefault 500と比較する。超過はdomain incomplete exit 3、affected JSON/PlantUMLなし、safe run manifestへrequested/resolved/count/diagnosticを記録する。valid overrideは通常公開、invalid valueはexit 2。snapshot pipelineは`ChangedPathAdmissionGate`を構築・実行せず、diff専用`--max-changed-paths`を受けた場合はusage error、exit 2、Artifactなしとする。OutputTransactionはabsolute path/protocol noise/unsafe fieldをpublish前に拒否する。

### determinism and optionality

same source bytes、tsconfig aliases、compiler/adapter/contract version、resolved configではresponse orderingとpublished digestが一致する。Node/npm dependencyはNext applicable runにだけ必要で、core-only install/testから分離する。

## 変更対象

| planned file | planned change | 存在確認 |
| --- | --- | --- |
| src/code_structure_viz/adapters/next/bridge.py::NextAdapterBridge（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/adapters/next/protocol.py（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| adapters/next/package.json と package-lock.json（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| adapters/next/tsconfig.json（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| adapters/next/src/analyze.ts::analyzeRepository（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| adapters/next/src/model.ts（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| adapters/next/src/render.ts（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |

追加で planned:

- tests/fixtures/generate-nextjs-component-snapshots/ に source-only fixture を置き、fixture の application code を実行しない。
- docs/contracts/ に schema と CLI behavior を配置する。これらはplanned implementation targetであり、本Designは実装済みとは扱わない。
- lockfile と license inventory を同じ Issue の acceptance に含める。

変更しない領域:

- runtime component tree、hydration result、browser rendering、React Server Components の実行
- non-literal dynamic import の推測、Next build/plugin 実行
- temporal component diff
- public plugin ABI、product HTML report

## 移行・互換性・rollback

- baseline に production implementation がないため in-place data migration は N/A。
- public schema/CLI は `/v1` と preview release で開始し、同一 major 内は field の additive extension を原則とする。
- data migration は N/A。Node adapter release は Python package と互換 matrix を固定する。protocol mismatch は adapter を incomplete として隔離し、旧 protocol reader を保持した additive fix または version up で forward recovery する。
- legacy CLI compatibility layer は作らない。legacy evidence の algorithm/test idea を採用するときは provenance note、license decision、CodeStructureViz-owned regression test を同じ change に含める。

## testability

| Test ID | 分類 | planned test file | command |
| --- | --- | --- | --- |
| I05-AT-001 | normal | tests/acceptance/next/test_snapshot_cli.py | uv run pytest tests/acceptance/next/test_snapshot_cli.py -q |
| I05-AT-002 | protocol | tests/contracts/next/test_adapter_protocol.py | uv run pytest tests/contracts/next/test_adapter_protocol.py -q |
| I05-AT-003 | safe subset | adapters/next/test/safe-subset.test.ts | npm --prefix adapters/next test -- safe-subset |
| I05-AT-004 | failure | tests/acceptance/next/test_adapter_failures.py | uv run pytest tests/acceptance/next/test_adapter_failures.py -q |
| I05-AT-005 | security | tests/security/test_next_static_boundary.py | uv run pytest tests/security/test_next_static_boundary.py -q |
| I05-AT-006 | optionality | tests/acceptance/next/test_optionality.py | uv run pytest tests/acceptance/next/test_optionality.py -q |
| I05-AT-007 | entity budget / diff-only option rejection | tests/acceptance/next/test_snapshot_budget.py | uv run pytest tests/acceptance/next/test_snapshot_budget.py -q |

- unit testはdomain parser/matcher/serializerとcanonicalizationのpure functionを対象にする。
- integration testはtemporary Git repositoryまたはimmutable source fixtureを使い、Git stateとsource bytesのbefore/afterを比較する。
- acceptance testは実CLI process、output directory、manifest/checksum、exit code、stdout/stderr、published file setを観測する。
- security testはimport/build/plugin/DB execution trap、source/secret/literal/absolute path/raw hunkのnegative scan、unsafe symlink、Git mutation allowlistを検査する。
- table-driven casesはstatusだけでなくpublication、manifest presence/absence、digest、requested/resolved budget values、actual countsまでassertする。

## risk

- Python/Node 二 runtime で protocol drift が起きる。versioned schema、golden fixtures、strict parser で境界を固定する。
- Next/React static patterns は幅広い。初期 release は根拠のある static subset を列挙し、runtime tree を推測しない。
- Node を core 必須にすると Python/SQLAlchemy 利用を壊す。applicability preflight 後だけ adapter を要求する。

- Re-evaluation trigger: security/privacy incident、target repository の不可逆変更、secret leak、rollback に incident response が必要な設計へ変わる場合は Planning Level を `critical` に上げる。
- Stop condition: first-party adapter protocol、TS/TSX coverage、JS/JSX safe subset、client boundary、Node optionality が acceptance で成立するまで Next diff へ進まない。

```plantuml
@startuml
title Next.js component snapshot の adapter 境界
left to right direction
actor "coding agent" as Agent
component "Python snapshot CLI" as CLI
component "NextAdapterBridge" as Bridge
component "repository-owned TypeScript adapter" as Adapter
component "TypeScript compiler API" as Compiler
component "component JSON / PlantUML" as Output
Agent -> CLI : next domain を指定する
CLI -> Bridge : versioned request JSON
Bridge -> Adapter : stdin で request を渡す
Adapter -> Compiler : TS/TSX と safe JS/JSX を解析する
Compiler --> Adapter : symbol と static relation
Adapter --> Bridge : versioned response JSON
Bridge -> Output : common envelope へ格納する
Output --> Agent : manifest 付き Artifact
@enduml
```

Next 固有 semantics は repository-owned TypeScript adapter が所有し、Python core とは versioned JSON だけで接続します。
