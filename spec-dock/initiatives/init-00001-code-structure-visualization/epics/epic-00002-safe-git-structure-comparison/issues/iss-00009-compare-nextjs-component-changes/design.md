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
| I06-DES-001 | I06-REQ-001 | CLI/application boundary と domain port を分離し、observable outcome を一 run transaction にまとめる。 |
| I06-DES-002 | I06-REQ-002 | source acquisition は immutable SourceView と provenance を返し、parser が repository state を直接読まない。 |
| I06-DES-003 | I06-REQ-003 | domain-owned identity/member/relation model を common envelope から分離する。 |
| I06-DES-004 | I06-REQ-004 | ArtifactPublisher が JSON/PlantUML/manifest の staging、collision check、SHA-256、atomic publication を所有する。 |
| I06-DES-005 | I06-REQ-005 | typed diagnostic と complete/not_applicable/incomplete state machine で failure を空結果へ潰さない。 |

## Current / Target

### Current（verified baseline）

- exact commit `7951ddabc2e6a3d66edb77eada7c6c16923264f7` は SpecDock 0.2.3、template 状態の canonical R/D/P、interview、8 accepted ADR を含む。
- CodeStructureViz の production package、CLI、domain adapter、semantic schema、acceptance fixtures は存在しない。
- `pyclassuml` と `tree-git-diff` は legacy evidence であり、CodeStructureViz の dependency ではない。

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

### semantic envelope

- `schema`: `code-structure-viz.semantic/v1`
- `document_kind`: `snapshot` または `diff`
- `domain`: `next`
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

- 片側 adapter failure、config unresolved、protocol mismatch は incomplete。removed/added への誤変換を禁止する。
- nonliteral dynamic import は unknown relation diagnostic。domain 全体を fatal にしないが coverage に未解決件数を記録する。
- entity budget 超過は無切り捨て nonzero、明示 override のみ許可する。

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
- docs/contracts/ に schema と CLI behavior を配置する。ただし本 package は repository へ直接変更を行わない。
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
| I06-AT-002 | semantic | adapters/next/test/semantic-seed.test.ts | npm --prefix adapters/next test -- semantic-seed |
| I06-AT-003 | matching | adapters/next/test/move-matching.test.ts | npm --prefix adapters/next test -- move-matching |
| I06-AT-004 | negative | tests/acceptance/next/test_diff_failures.py | uv run pytest tests/acceptance/next/test_diff_failures.py -q |
| I06-AT-005 | impact | tests/integration/next/test_impact_union_graph.py | uv run pytest tests/integration/next/test_impact_union_graph.py -q |
| I06-AT-006 | unknown | adapters/next/test/dynamic-unknown.test.ts | npm --prefix adapters/next test -- dynamic-unknown |

- unit test は domain parser/matcher/serializer の pure function を対象にする。
- integration test は temporary Git repository と immutable fixture source を使い、Git state の before/after fingerprint を比較する。
- acceptance test は実際の CLI process、output directory、manifest/checksum、exit code、stdout/stderr を観測する。
- security test は import/build/plugin/DB execution trap、secret literal、absolute path、unsafe symlink、Git mutation allowlist を検査する。

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
