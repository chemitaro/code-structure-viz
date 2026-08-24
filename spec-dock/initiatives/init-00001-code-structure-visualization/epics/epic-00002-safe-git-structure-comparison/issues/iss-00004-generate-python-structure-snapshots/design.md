---
種別: 設計書（Issue）
ID: "iss-00004"
タイトル: "Generate Python Structure Snapshots"
関連GitHub: ["#4"]
package_sequence_key: "ISSUE-01"
状態: "draft"
最終更新: "2026-08-24"
依存: ["requirement.md"]
親: ["epic-00002", "init-00001"]
---

# iss-00004 Generate Python Structure Snapshots — 設計

詳細: [Design Guide](../../../../../../docs/authoring/design.md)

## 設計目標

- `python` domain の `snapshot` を、CLI から source acquisition、analysis、versioned JSON、PlantUML、manifest、diagnostic まで一つの vertical pipeline として設計する。
- accepted ADR の独立 product ownership、named endpoint、dual snapshot、adapter boundary、agent-first Artifact、安全な static analysis、product HTML exclusion、vertical slicing を破らない。
- common abstraction は lifecycle、diagnostic、Artifact descriptor、graph primitive に限定し、domain-specific identity/member/relation/matching を adapter が所有する。

| Design ID | Requirement trace | 判断 |
| --- | --- | --- |
| I01-DES-001 | I01-REQ-001 | CLI/application boundaryとPython domain portを分離し、snapshot outcomeをone run transactionにまとめる。 |
| I01-DES-002 | I01-REQ-002 | immutable SourceViewとtarget selectionを返し、parserがmutable repository stateを直接読まない。 |
| I01-DES-003 | I01-REQ-003 | Python-owned identity/member/relation modelをcommon envelopeから分離する。 |
| I01-DES-004 | I01-REQ-004 | ArtifactPublisherがper-domain JSON/PlantUML/run manifestのstaging、collision、SHA-256、atomic publicationを所有する。 |
| I01-DES-005 | I01-REQ-005 | core preflightとdomain-local entity budgetを別gateにし、incomplete publicationを型で表す。 |
| I01-DES-006 | I01-REQ-006 | static execution trap、redaction、canonical ordering、same-input digest invariantをadapter entry/serializerで検証する。 |

## Current / Target

### Current（verified baseline）

- exact verified current commit `867ee6929283dfc84711bce245b784d2b8e3e9e6` は本Issueのcanonical Requirement/Design/Plan、accepted ADR、interviewを含む。
- production package、CLI、domain adapter、schema implementation、acceptance fixturesは未実装であり、以下のpath/symbolはすべてplannedである。
- 本Designは親の横断contractをslice固有の構造へ具体化し、依存Issueのpublic contractを変更せずに後続sliceへ渡す。

### Target

- coding agent または人間が、対象 Python repository を実行せずに class 構造を semantic JSON と PlantUML で取得できる。
- source/body/secret を漏らさず、failure と coverage を manifest で agent が機械判定できる。
- downstream Issue はこの Design の stable interface だけへ依存し、内部 class layout を fork しない。

## 責務・Interface

### planned component responsibilities

| planned path / symbol | 状態 | 責務 |
| --- | --- | --- |
| pyproject.toml と uv.lock（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/cli/main.py::main（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/core/config.py::resolve_config（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/core/diagnostics.py::Diagnostic（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/artifacts/writer.py::ArtifactPublisher（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/artifacts/manifest.py::RunManifest（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/adapters/python/analyzer.py::PythonSnapshotAnalyzer（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/adapters/python/model.py（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/adapters/python/renderer.py（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |

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

### semantic snapshot model

`PythonSnapshot`は`code-structure-viz.semantic/v1`、domain `python`、document kind `snapshot`を持つimmutable valueである。identityはnormalized module path + qualified class name。field/method/property/decoratorとtyped/import relationsをdomain-owned recordsとしてcanonical sortする。default literal、body、docstring、commentをmodelへ入れない。

### state, publication, and entity budget

```text
request -> core preflight -> SourceView -> Python analysis -> entity gate -> render -> stage -> publish
             | fatal/usage                     | incomplete      | incomplete | fatal
```

- core preflight failureはexit 1または2でfile Artifactを公開しない。
- target evidence不在は`not_applicable`、status/diagnosticのみ。parse/read failureでsafe partial snapshotを生成できる場合はpayload自体に`incomplete`を明示しexit 3。
- `EntityBudgetGate`（planned）はsemantic entity countをrender前に検査する。default 500超過はdomain incomplete、exit 3、semantic JSON/PlantUMLなし、safe run manifestへrequested/resolved/count/diagnosticを記録する。valid `--max-entities`は通常公開を許可する。invalid valueはexit 2。snapshot pipelineは`ChangedPathAdmissionGate`を構築・実行せず、diff専用`--max-changed-paths`を受けた場合はusage error、exit 2、Artifactなしとする。
- `OutputTransaction`はcollision/fingerprint/integrityをpublish前に検査し、failed stagingをcleanupする。

### safety and determinism

SourceViewはrepository-relative pathとcontent digestだけをdomain serializerへ渡す。same source bytes、target、resolved config、adapter versionではentity/member/relation/diagnostic/Artifact descriptor順序とpublished bytesのSHA-256が一致する。

## 変更対象

| planned file | planned change | 存在確認 |
| --- | --- | --- |
| pyproject.toml と uv.lock（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/cli/main.py::main（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/core/config.py::resolve_config（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/core/diagnostics.py::Diagnostic（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/artifacts/writer.py::ArtifactPublisher（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/artifacts/manifest.py::RunManifest（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/adapters/python/analyzer.py::PythonSnapshotAnalyzer（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/adapters/python/model.py（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/adapters/python/renderer.py（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |

追加で planned:

- tests/fixtures/generate-python-structure-snapshots/ に source-only fixture を置き、fixture の application code を実行しない。
- docs/contracts/ に schema と CLI behavior を配置する。これらはplanned implementation targetであり、本Designは実装済みとは扱わない。
- lockfile と license inventory を同じ Issue の acceptance に含める。

変更しない領域:

- temporal diff、Git endpoint 解決、moved matching
- SQLAlchemy 固有 ER semantics、Next.js component semantics
- Python module の import 実行、runtime reflection、bytecode analysis
- 製品機能としての HTML report generation

## 移行・互換性・rollback

- baseline に production implementation がないため in-place data migration は N/A。
- public schema/CLI は `/v1` と preview release で開始し、同一 major 内は field の additive extension を原則とする。
- persistent data migration は N/A。release 前は Issue 単位で revert する。schema/CLI を preview 公開した後は既存 v1 reader を壊さず、v1 additive fix または新 schema version で forward recovery する。
- legacy CLI compatibility layer は作らない。legacy evidence の algorithm/test idea を採用するときは provenance note、license decision、CodeStructureViz-owned regression test を同じ change に含める。

## testability

| Test ID | 分類 | planned test file | command |
| --- | --- | --- | --- |
| I01-AT-001 | normal | tests/acceptance/python/test_snapshot_cli.py | uv run pytest tests/acceptance/python/test_snapshot_cli.py -q |
| I01-AT-002 | boundary | tests/integration/python/test_targeted_snapshot.py | uv run pytest tests/integration/python/test_targeted_snapshot.py -q |
| I01-AT-003 | negative | tests/acceptance/python/test_snapshot_failures.py | uv run pytest tests/acceptance/python/test_snapshot_failures.py -q |
| I01-AT-004 | security | tests/security/test_python_static_boundary.py | uv run pytest tests/security/test_python_static_boundary.py -q |
| I01-AT-005 | determinism | tests/acceptance/python/test_snapshot_determinism.py | uv run pytest tests/acceptance/python/test_snapshot_determinism.py -q |
| I01-AT-006 | entity budget / diff-only option rejection | tests/acceptance/python/test_snapshot_budget.py | uv run pytest tests/acceptance/python/test_snapshot_budget.py -q |

- unit testはdomain parser/matcher/serializerとcanonicalizationのpure functionを対象にする。
- integration testはtemporary Git repositoryまたはimmutable source fixtureを使い、Git stateとsource bytesのbefore/afterを比較する。
- acceptance testは実CLI process、output directory、manifest/checksum、exit code、stdout/stderr、published file setを観測する。
- security testはimport/build/plugin/DB execution trap、source/secret/literal/absolute path/raw hunkのnegative scan、unsafe symlink、Git mutation allowlistを検査する。
- table-driven casesはstatusだけでなくpublication、manifest presence/absence、digest、requested/resolved budget values、actual countsまでassertする。

## risk

- 最初の slice に common foundation を入れすぎると後続 adapter が不要な抽象へ拘束される。domain-neutral envelope、diagnostic、Artifact publication だけに限定する。
- Python typing 表現の正規化が過剰だと source semantics を失う。raw source ではなく安全な canonical type expression と unresolved marker を併記する。
- whole repository 解析の breadth が大きい。entity budget と deterministic traversal で fail closed にする。

- Re-evaluation trigger: security/privacy incident、target repository の不可逆変更、secret leak、rollback に incident response が必要な設計へ変わる場合は Planning Level を `critical` に上げる。
- Stop condition: Python snapshot の CLI→source selection→AST analysis→semantic JSON/PlantUML→manifest→acceptance test が単独で成立する前に、Git diff、SQLAlchemy row model、Next bridge の実装へ進まない。

```plantuml
@startuml
title Python 構造 snapshot の正常な流れ
left to right direction
actor "coding agent" as Agent
component "snapshot CLI" as CLI
component "安全な source 選択" as Source
component "PythonSnapshotAnalyzer" as Analyzer
component "semantic JSON / PlantUML" as Output
Agent -> CLI : repository と output directory を指定する
CLI -> Source : target と scope を解決する
Source -> Analyzer : source bytes と provenance を渡す
Analyzer -> Output : class・member・relation を生成する
Output --> Agent : manifest 付き Artifact を返す
@enduml
```

target application を実行せず、source bytes から二形式の Artifact までを一つの acceptance boundary として届けます。
