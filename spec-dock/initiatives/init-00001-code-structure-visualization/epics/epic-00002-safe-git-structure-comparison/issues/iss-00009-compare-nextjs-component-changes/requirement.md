---
種別: 要件定義書（Issue）
ID: "iss-00009"
タイトル: "Compare Next.js Component Changes"
関連GitHub: ["#9"]
package_sequence_key: "ISSUE-06"
状態: "draft"
最終更新: "2026-08-24"
親: ["epic-00002", "init-00001"]
---

# iss-00009 Compare Next.js Component Changes — 要件定義

詳細: [Requirement Guide](../../../../../../docs/authoring/requirement.md)

## 目的

coding agent が before/after Next.js semantic snapshot から component/props/import/render/boundary change と影響 context を比較できる。

利用者 story: coding agent として、TS/TSX の textual diff ではなく exported component と static relation の意味変化を識別し、runtime tree を捏造せず review へ使いたい。

この Issue は技術 layer の完成ではなく、利用者が command を実行して source acquisition、domain analysis、semantic JSON、PlantUML、diagnostic、acceptance evidence まで確認できる一つの vertical outcome を所有する。

## 背景

- 親 Initiative は三 domain の code structure を静的に可視化する。
- 親 Epic は安全な Git comparison と agent-first Artifact contract を一つの product outcome として統合する。
- この slice の declared dependency は ISSUE-02, ISSUE-05。依存 Issue の public contract だけを利用し、unfinished sibling の内部実装には依存しない。
- canonical authority は exact commit `7951ddabc2e6a3d66edb77eada7c6c16923264f7` の accepted ADR と interview、および本 package の親 R/D/P である。

| 親 requirement | この Issue の所有範囲 |
| --- | --- |
| EPIC-REQ-001 | next domain の diff を end-to-end で提供する。 |
| EPIC-REQ-002 | static analysis、read-only Git、redaction、fail-closed を維持する。 |
| EPIC-REQ-003 | versioned semantic JSON、domain-specific PlantUML、manifest を生成する。 |
| EPIC-REQ-004 | complete/not_applicable/incomplete と exit contract を slice の範囲で実装する。 |

## 観測可能な要件

| ID | 観測面 | 要件 |
| --- | --- | --- |
| I06-REQ-001 | CLI と observable outcome | coding agent が before/after Next.js semantic snapshot から component/props/import/render/boundary change と影響 context を比較できる。 |
| I06-REQ-002 | source acquisition | ISSUE-02 の named endpoint、read-only Git、working-tree freeze、fingerprint、FileChangeSet を使い、両 endpoint で ISSUE-05 adapter を独立実行する。 |
| I06-REQ-003 | semantic behavior | module/exported component/prop/import/relation/use client boundary の semantic delta を changed seed とする。format、comment、import order だけは seed にしない。 |
| I06-REQ-004 | Artifact/output | Next diff JSON は before/after adapter contract/version/config digest、component/member/relation change、matching evidence、impact context を持つ。 |
| I06-REQ-005 | failure behavior | 片側 adapter failure、config unresolved、protocol mismatch は incomplete。removed/added への誤変換を禁止する。 |
| I06-REQ-006 | safety/determinism | 解析対象 module、plugin、migration、build script、application entry point を import または実行しない。 同じ source bytes、endpoint、resolved config、adapter version では entity・member・relation・diagnostic・Artifact path の順序と SHA-256 が決定的になる。 |

### I06-REQ-001

coding agent が before/after Next.js semantic snapshot から component/props/import/render/boundary change と影響 context を比較できる。
### I06-REQ-002

ISSUE-02 の named endpoint、read-only Git、working-tree freeze、fingerprint、FileChangeSet を使い、両 endpoint で ISSUE-05 adapter を独立実行する。
### I06-REQ-003

module/exported component/prop/import/relation/use client boundary の semantic delta を changed seed とする。format、comment、import order だけは seed にしない。
### I06-REQ-004

Next diff JSON は before/after adapter contract/version/config digest、component/member/relation change、matching evidence、impact context を持つ。
### I06-REQ-005

片側 adapter failure、config unresolved、protocol mismatch は incomplete。removed/added への誤変換を禁止する。
### I06-REQ-006

解析対象 module、plugin、migration、build script、application entry point を import または実行しない。 同じ source bytes、endpoint、resolved config、adapter version では entity・member・relation・diagnostic・Artifact path の順序と SHA-256 が決定的になる。


### CLI examples

```bash
code-structure-viz diff --repo . --domain next --from origin/main --to working-tree --output-dir /tmp/csv-next-diff
code-structure-viz diff --repo . --domain next --from release/1 --to head --upstream-depth 2 --downstream-depth 1 --output-dir /tmp/csv-next-impact
```

### source acquisition contract

- ISSUE-02 の named endpoint、read-only Git、working-tree freeze、fingerprint、FileChangeSet を使い、両 endpoint で ISSUE-05 adapter を独立実行する。
- before/after の tsconfig/jsconfig と source set を各 snapshot provenance に固定し、after config を before source 解決へ流用しない。
- Node adapter が片側で unavailable/invalid response の場合は component removal/addition を推測せず incomplete。

### semantic contract

- module/exported component/prop/import/relation/use client boundary の semantic delta を changed seed とする。format、comment、import order だけは seed にしない。
- props、static import、literal dynamic import、JSX render、client/server boundary を member/relation-level に色分けする。
- component moved は one-to-one、module rename/name evidence、structural fingerprint、unique candidate の全条件を満たす場合だけ採用し、曖昧なら removed+added。
- impact graph は before/after static relation union。removed component は before import/render edge を使い、upstream/downstream を別 depth で探索する。
- non-literal dynamic behavior と runtime component tree は unknown/coverage limitation のまま比較し、推測による relation delta を作らない。

### output contract

- Next diff JSON は before/after adapter contract/version/config digest、component/member/relation change、matching evidence、impact context を持つ。
- PlantUML は component と props/import/relation を `+ - ~ → ?` と green/red/yellow/blue/gray、removed dashed で表示する。
- adapter 部分 failure でも Python/SQLAlchemy 等の sibling Artifact を消さないための domain status を返せる。

## スコープ

### 対象

- `next` domain の `diff` use case を CLI input から acceptance test まで届ける。
- common CLI/config/diagnostic/Artifact contract は、この slice に必要な範囲だけ導入または拡張する。
- repository-owned implementation、tests、fixtures、documentation、lockfile、CI lane を含む。

### 対象外

- runtime render tree と hydration behavior の差分
- bundle analysis、Next build output、browser DOM diff
- cross-domain aggregation と overall exit decision
- HTML report generation

### 親契約として変更しない境界

- `--repo PATH` で解析対象 repository を明示し、`--output-dir PATH` を必須とする。
- `--format semantic-json|plantuml` は複数指定でき、未指定時は semantic JSON と PlantUML の両方を生成する。
- `--config PATH` を受け付ける。優先順位は CLI、`.code-structure-viz.toml`、built-in default であり、unknown key と型不正は exit 2 とする。
- 出力は一時 staging directory で完成させ、既存 path との衝突を検査してから atomic に公開する。既存 file は上書きしない。
- `--stdout` を明示した場合だけ、選択した一つの Artifact または run manifest を標準出力へ複製する。通常時の stdout は machine-readable summary だけとする。

- 解析対象 module、plugin、migration、build script、application entry point を import または実行しない。
- Git repository は read-only とし、fetch、checkout、reset、stash、clean、commit、ref 更新を実行しない。すべての Git subprocess で lazy fetch、external diff、textconv、color を無効化する。
- Artifact には repository-relative path、symbol、type、signature、relation、line range だけを許可し、source body、comment、literal、secret らしい値、absolute path を含めない。
- 同じ source bytes、endpoint、resolved config、adapter version では entity・member・relation・diagnostic・Artifact path の順序と SHA-256 が決定的になる。

## 失敗・境界条件

- 片側 adapter failure、config unresolved、protocol mismatch は incomplete。removed/added への誤変換を禁止する。
- nonliteral dynamic import は unknown relation diagnostic。domain 全体を fatal にしないが coverage に未解決件数を記録する。
- entity budget 超過は無切り捨て nonzero、明示 override のみ許可する。

- `not_applicable` は target 不在、`incomplete` は target があるが安全に解析できない状態であり、相互に変換しない。
- failure diagnostic は stable code、severity、domain、safe repository-relative location、recoverability、human-readable message を持つ。source body と secret は含めない。
- stop condition: Next member/relation seed、union impact、adapter partial failure、unknown dynamic behavior が acceptance で固定されるまで全 domain 集約へ進まない。

## 受け入れ条件

| ID | 観測可能な完了条件 | acceptance test |
| --- | --- | --- |
| I06-AC-001 | component/prop/import/render/boundary change を member-level JSON と PlantUML にする。 | I06-AT-001 |
| I06-AC-002 | format/comment/import-order only は seed にならず static relation change は seed になる。 | I06-AT-002 |
| I06-AC-003 | 一意 component move だけ moved、ambiguous candidate は removed+added。 | I06-AT-003 |
| I06-AC-004 | 片側 adapter/config failure を removal にせず incomplete にする。 | I06-AT-004 |
| I06-AC-005 | removed component の before edge を union graph context に保持する。 | I06-AT-005 |
| I06-AC-006 | nonliteral dynamic behavior を unknown とし runtime relation を生成しない。 | I06-AT-006 |

- **I06-AC-001〜I06-AC-006 がすべて満たされ、planned test command が clean checkout で成功すること。**
- Requirement、Design、Plan の trace table が一致し、unresolved acceptance gap がないこと。
- release boundary: Next domain diff preview。ISSUE-07 の統合前でも `--domain next` の単独利用が可能な acceptance boundary。

## 制約・前提

- initial platform は macOS と Linux。native Windows は対象外。
- Core/CLI/Git/manifest/Python/SQLAlchemy は Python 3.12 以上。Next adapter 利用時だけ Node.js 22 LTS 以上。
- Git 2.39 以上。CI は minimum supported と repository で明示更新する latest stable lane を実行する。
- direct/indirect dependency は lockfile で exact resolve し、license inventory と offline runtime test を持つ。runtime に network access を要求しない。
- `pyclassuml` と `tree-git-diff` への runtime/package/CLI dependency を持たない。legacy code の直接 copy は license/provenance 未確認のまま行わず、初期実装は contract/test evidence を基に repository-owned code として再実装する。
- product HTML report generation、HTML command、Tailscale publication は本 Issue の製品 scope 外。`explanation.html` は specification Artifact である。
