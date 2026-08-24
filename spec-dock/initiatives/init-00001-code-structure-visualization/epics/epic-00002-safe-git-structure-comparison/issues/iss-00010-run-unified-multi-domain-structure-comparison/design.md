---
種別: 設計書（Issue）
ID: "iss-00010"
タイトル: "Run Unified Multi-Domain Structure Comparison"
関連GitHub: ["#10"]
package_sequence_key: "ISSUE-07"
状態: "draft"
最終更新: "2026-08-24"
依存: ["requirement.md"]
親: ["epic-00002", "init-00001"]
---

# iss-00010 Run Unified Multi-Domain Structure Comparison — 設計

詳細: [Design Guide](../../../../../../docs/authoring/design.md)

## 設計目標

- `all` domain の `snapshot-and-diff orchestration` を、CLI から source acquisition、analysis、versioned JSON、PlantUML、manifest、diagnostic まで一つの vertical pipeline として設計する。
- accepted ADR の独立 product ownership、named endpoint、dual snapshot、adapter boundary、agent-first Artifact、安全な static analysis、product HTML exclusion、vertical slicing を破らない。
- common abstraction は lifecycle、diagnostic、Artifact descriptor、graph primitive に限定し、domain-specific identity/member/relation/matching を adapter が所有する。

| Design ID | Requirement trace | 判断 |
| --- | --- | --- |
| I07-DES-001 | I07-REQ-001 | CLI/application boundary と domain port を分離し、observable outcome を一 run transaction にまとめる。 |
| I07-DES-002 | I07-REQ-002 | source acquisition は immutable SourceView と provenance を返し、parser が repository state を直接読まない。 |
| I07-DES-003 | I07-REQ-003 | domain-owned identity/member/relation model を common envelope から分離する。 |
| I07-DES-004 | I07-REQ-004 | ArtifactPublisher が JSON/PlantUML/manifest の staging、collision check、SHA-256、atomic publication を所有する。 |
| I07-DES-005 | I07-REQ-005 | typed diagnostic と complete/not_applicable/incomplete state machine で failure を空結果へ潰さない。 |
| I07-DES-006 | I07-REQ-006 | security invariant と budget を adapter entry/exit で検証し、unsafe result を公開しない。 |

## Current / Target

### Current（verified baseline）

- exact commit `7951ddabc2e6a3d66edb77eada7c6c16923264f7` は SpecDock 0.2.3、template 状態の canonical R/D/P、interview、8 accepted ADR を含む。
- CodeStructureViz の production package、CLI、domain adapter、semantic schema、acceptance fixtures は存在しない。
- `pyclassuml` と `tree-git-diff` は legacy evidence であり、CodeStructureViz の dependency ではない。

### Target

- coding agent が domain を省略した一回の command で Python、SQLAlchemy、Next の適用可否・成功・不完全を区別し、成功 Artifact を保持した集約 manifest と正しい exit code を得られる。
- source/body/secret を漏らさず、failure と coverage を manifest で agent が機械判定できる。
- downstream Issue はこの Design の stable interface だけへ依存し、内部 class layout を fork しない。

## 責務・Interface

### planned component responsibilities

| planned path / symbol | 状態 | 責務 |
| --- | --- | --- |
| src/code_structure_viz/application/run.py::RunCoordinator（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/application/domain_registry.py::FirstPartyDomainRegistry（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/core/outcome.py::RunOutcome（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/artifacts/manifest.py::AggregateManifestBuilder（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/artifacts/transaction.py::OutputTransaction（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/cli/exit_codes.py（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| .github/workflows/ci.yml の minimum/latest matrix（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |

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
- `domain`: `all`
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

- adapter exception を core process crash に伝播させず domain diagnostic へ正規化する。ただし protocol corruption や security invariant violation は affected domain を incomplete にする。
- output collision、invalid config、Git/Python minimum 未満、endpoint unresolved、fingerprint drift は run-level fatal/usage とし、既存 output を変更しない。
- SIGINT は temporary output を cleanup し exit 130。すでに存在した output と target repository は変更しない。
- partial failure の stdout/stderr は agent が parse できる一貫した summary と diagnostic channel を維持する。

## 変更対象

| planned file | planned change | 存在確認 |
| --- | --- | --- |
| src/code_structure_viz/application/run.py::RunCoordinator（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/application/domain_registry.py::FirstPartyDomainRegistry（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/core/outcome.py::RunOutcome（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/artifacts/manifest.py::AggregateManifestBuilder（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/artifacts/transaction.py::OutputTransaction（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| src/code_structure_viz/cli/exit_codes.py（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |
| .github/workflows/ci.yml の minimum/latest matrix（planned） | planned | この Issue の implementation target。baseline commit には未実装。 |

追加で planned:

- tests/fixtures/run-unified-multi-domain-structure-comparison/ に source-only fixture を置き、fixture の application code を実行しない。
- docs/contracts/ に schema と CLI behavior を配置する。ただし本 package は repository へ直接変更を行わない。
- lockfile と license inventory を同じ Issue の acceptance に含める。

変更しない領域:

- cross-domain semantic relation と single universal identity model
- public plugin ABI、remote execution、auto fetch
- 製品機能としての HTML report/HTML command/Tailscale publication
- native Windows、legacy CLI compatibility

## 移行・互換性・rollback

- baseline に production implementation がないため in-place data migration は N/A。
- public schema/CLI は `/v1` と preview release で開始し、同一 major 内は field の additive extension を原則とする。
- persistent data migration は N/A。rollout は intermediate release→Next opt-in preview→default all-domain の順。partial outcome/exit bug は default all-domain を無効化して明示 domain へ戻し、schema compatibility を保った forward fix を行う。
- legacy CLI compatibility layer は作らない。legacy evidence の algorithm/test idea を採用するときは provenance note、license decision、CodeStructureViz-owned regression test を同じ change に含める。

## testability

| Test ID | 分類 | planned test file | command |
| --- | --- | --- | --- |
| I07-AT-001 | normal | tests/acceptance/test_multi_domain_cli.py | uv run pytest tests/acceptance/test_multi_domain_cli.py -q |
| I07-AT-002 | partial failure | tests/acceptance/test_partial_domain_failure.py | uv run pytest tests/acceptance/test_partial_domain_failure.py -q |
| I07-AT-003 | applicability | tests/acceptance/test_multi_domain_applicability.py | uv run pytest tests/acceptance/test_multi_domain_applicability.py -q |
| I07-AT-004 | fatal | tests/acceptance/test_run_atomicity.py | uv run pytest tests/acceptance/test_run_atomicity.py -q |
| I07-AT-005 | exit contract | tests/acceptance/test_exit_codes.py | uv run pytest tests/acceptance/test_exit_codes.py -q |
| I07-AT-006 | platform | .github/workflows/ci.yml | uv run pytest && npm --prefix adapters/next test |
| I07-AT-007 | packaging | tests/packaging/test_offline_install.py | uv run pytest tests/packaging/test_offline_install.py -q |

- unit test は domain parser/matcher/serializer の pure function を対象にする。
- integration test は temporary Git repository と immutable fixture source を使い、Git state の before/after fingerprint を比較する。
- acceptance test は実際の CLI process、output directory、manifest/checksum、exit code、stdout/stderr を観測する。
- security test は import/build/plugin/DB execution trap、secret literal、absolute path、unsafe symlink、Git mutation allowlist を検査する。

## risk

- orchestrator が domain semantics を吸収すると adapter boundary が崩れる。registry は lifecycle/status/artifact descriptor だけを扱う。
- partial failure で成功 Artifact を消す、または exit 0 にする誤り。table-driven outcome tests と atomic transaction を必須にする。
- CI の latest stable が無制御に漂流する。repository-managed matrix を定期更新し、lockfile と minimum lanes を独立させる。

- Re-evaluation trigger: security/privacy incident、target repository の不可逆変更、secret leak、rollback に incident response が必要な設計へ変わる場合は Planning Level を `critical` に上げる。
- Stop condition: 三 domain の applicability、partial success retention、aggregate manifest、exit code、atomicity、minimum/latest CI が acceptance で成立するまで Initiative を完了扱いにしない。

```plantuml
@startuml
title 全 domain 実行と partial failure の保持
left to right direction
actor "coding agent" as Agent
component "RunCoordinator" as Run
component "Python adapter" as Python
component "SQLAlchemy adapter" as SQLA
component "Next adapter" as Next
component "OutputTransaction" as Output
component "aggregate manifest" as Manifest
Agent -> Run : snapshot / diff を一回実行する
Run -> Python : domain run
Run -> SQLA : domain run
Run -> Next : applicable な場合だけ domain run
Python --> Output : complete Artifact
SQLA --> Output : complete Artifact
Next --> Output : complete / not_applicable / incomplete
Output -> Manifest : status・coverage・diagnostic・SHA-256
Manifest --> Agent : exit 0 または 3 と provenance
@enduml
```

domain ごとの意味を混ぜず、一部失敗でも成功 Artifact と provenance を一つの transaction で保持します。
