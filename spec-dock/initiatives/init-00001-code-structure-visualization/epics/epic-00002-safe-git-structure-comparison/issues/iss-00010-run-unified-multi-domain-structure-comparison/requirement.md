---
種別: 要件定義書（Issue）
ID: "iss-00010"
タイトル: "Run Unified Multi-Domain Structure Comparison"
関連GitHub: ["#10"]
package_sequence_key: "ISSUE-07"
状態: "draft"
最終更新: "2026-08-24"
親: ["epic-00002", "init-00001"]
---

# iss-00010 Run Unified Multi-Domain Structure Comparison — 要件定義

詳細: [Requirement Guide](../../../../../../docs/authoring/requirement.md)

## 目的

coding agent が domain を省略した一回の command で Python、SQLAlchemy、Next の適用可否・成功・不完全を区別し、成功 Artifact を保持した集約 manifest と正しい exit code を得られる。

利用者 story: coding agent として、repository の複数 domain を一度に調査し、一部 adapter が失敗しても利用可能な JSON/PlantUML を失わず、人間へ説明できる provenance と diagnostic を受け取りたい。

この Issue は技術 layer の完成ではなく、利用者が command を実行して source acquisition、domain analysis、semantic JSON、PlantUML、diagnostic、acceptance evidence まで確認できる一つの vertical outcome を所有する。

## 背景

- 親 Initiative は三 domain の code structure を静的に可視化する。
- 親 Epic は安全な Git comparison と agent-first Artifact contract を一つの product outcome として統合する。
- この slice の declared dependency は ISSUE-04, ISSUE-06。依存 Issue の public contract だけを利用し、unfinished sibling の内部実装には依存しない。
- canonical authority は exact commit `7951ddabc2e6a3d66edb77eada7c6c16923264f7` の accepted ADR と interview、および本 package の親 R/D/P である。

| 親 requirement | この Issue の所有範囲 |
| --- | --- |
| EPIC-REQ-001 | all domain の snapshot-and-diff orchestration を end-to-end で提供する。 |
| EPIC-REQ-002 | static analysis、read-only Git、redaction、fail-closed を維持する。 |
| EPIC-REQ-003 | versioned semantic JSON、domain-specific PlantUML、manifest を生成する。 |
| EPIC-REQ-004 | complete/not_applicable/incomplete と exit contract を slice の範囲で実装する。 |

## 観測可能な要件

| ID | 観測面 | 要件 |
| --- | --- | --- |
| I07-REQ-001 | CLI と observable outcome | coding agent が domain を省略した一回の command で Python、SQLAlchemy、Next の適用可否・成功・不完全を区別し、成功 Artifact を保持した集約 manifest と正しい exit code を得られる。 |
| I07-REQ-002 | source acquisition | diff で domain 無指定なら python、sqlalchemy、next を deterministic order で実行する。snapshot も同じ default を採用し、明示 domain で絞り込める。 |
| I07-REQ-003 | semantic behavior | common envelope は run/domain status、artifact descriptor、diagnostic、coverage、graph primitive だけを共有し、domain identity/member/relation/matching を統一 model へ押し込まない。 |
| I07-REQ-004 | Artifact/output | format 未指定時は complete/incomplete domain ごとに versioned semantic JSON と domain-specific PlantUML を生成する。not_applicable domain は status/diagnostic のみ。 |
| I07-REQ-005 | failure behavior | adapter exception を core process crash に伝播させず domain diagnostic へ正規化する。ただし protocol corruption や security invariant violation は affected domain を incomplete にする。 |
| I07-REQ-006 | safety/determinism | 解析対象 module、plugin、migration、build script、application entry point を import または実行しない。 同じ source bytes、endpoint、resolved config、adapter version では entity・member・relation・diagnostic・Artifact path の順序と SHA-256 が決定的になる。 |
| I07-REQ-007 | slice-specific boundary | 一つの output transaction で domain Artifact と run manifest を staging し、fingerprint と collision gate 後に公開する。 |

### I07-REQ-001

coding agent が domain を省略した一回の command で Python、SQLAlchemy、Next の適用可否・成功・不完全を区別し、成功 Artifact を保持した集約 manifest と正しい exit code を得られる。
### I07-REQ-002

diff で domain 無指定なら python、sqlalchemy、next を deterministic order で実行する。snapshot も同じ default を採用し、明示 domain で絞り込める。
### I07-REQ-003

common envelope は run/domain status、artifact descriptor、diagnostic、coverage、graph primitive だけを共有し、domain identity/member/relation/matching を統一 model へ押し込まない。
### I07-REQ-004

format 未指定時は complete/incomplete domain ごとに versioned semantic JSON と domain-specific PlantUML を生成する。not_applicable domain は status/diagnostic のみ。
### I07-REQ-005

adapter exception を core process crash に伝播させず domain diagnostic へ正規化する。ただし protocol corruption や security invariant violation は affected domain を incomplete にする。
### I07-REQ-006

解析対象 module、plugin、migration、build script、application entry point を import または実行しない。 同じ source bytes、endpoint、resolved config、adapter version では entity・member・relation・diagnostic・Artifact path の順序と SHA-256 が決定的になる。
### I07-REQ-007

一つの output transaction で domain Artifact と run manifest を staging し、fingerprint と collision gate 後に公開する。


### CLI examples

```bash
code-structure-viz diff --repo . --output-dir /tmp/csv-all-diff
code-structure-viz snapshot --repo . --output-dir /tmp/csv-all-snapshot
code-structure-viz diff --repo . --domain python --domain sqlalchemy --from origin/main --to head --stdout manifest --output-dir /tmp/csv-backend-diff
```

### source acquisition contract

- diff で domain 無指定なら python、sqlalchemy、next を deterministic order で実行する。snapshot も同じ default を採用し、明示 domain で絞り込める。
- core preflight、endpoint resolution、working-tree freeze、resolved config は一 run で共有するが、各 adapter は domain-owned source selection と semantic model を保持する。
- Next target 不在なら Node を要求しない。domain applicability preflight は source presence と safe static indicator だけで行い、application を実行しない。
- 一つの output transaction で domain Artifact と run manifest を staging し、fingerprint と collision gate 後に公開する。

### semantic contract

- common envelope は run/domain status、artifact descriptor、diagnostic、coverage、graph primitive だけを共有し、domain identity/member/relation/matching を統一 model へ押し込まない。
- domain status は `complete`、`not_applicable`、`incomplete`。overall は全 selected domain が complete/not_applicable なら complete、少なくとも一つ incomplete かつ core run が成立すれば incomplete。
- FileChangeSet は run-level evidence、SemanticChangeSet は domain-level ownership。cross-domain relation を初期 release で推測しない。
- resolved config、version、endpoint、fingerprint、domain status、coverage、diagnostic、各 Artifact relative path/SHA-256 を一つの manifest に集約する。

### output contract

- format 未指定時は complete/incomplete domain ごとに versioned semantic JSON と domain-specific PlantUML を生成する。not_applicable domain は status/diagnostic のみ。
- exit 0 は overall complete、1 は core fatal analysis/environment、2 は usage/config、3 は domain incomplete、130 は interrupt。
- exit 3 でも complete domain の Artifact と manifest を保持する。fatal fingerprint drift や unresolved endpoint では success Artifact を公開しない。
- manifest の Artifact path は output directory 相対、SHA-256 は公開 bytes に対して計算し、absolute path を含めない。

## スコープ

### 対象

- `all` domain の `snapshot-and-diff orchestration` use case を CLI input から acceptance test まで届ける。
- common CLI/config/diagnostic/Artifact contract は、この slice に必要な範囲だけ導入または拡張する。
- repository-owned implementation、tests、fixtures、documentation、lockfile、CI lane を含む。

### 対象外

- cross-domain semantic relation と single universal identity model
- public plugin ABI、remote execution、auto fetch
- 製品機能としての HTML report/HTML command/Tailscale publication
- native Windows、legacy CLI compatibility

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

- adapter exception を core process crash に伝播させず domain diagnostic へ正規化する。ただし protocol corruption や security invariant violation は affected domain を incomplete にする。
- output collision、invalid config、Git/Python minimum 未満、endpoint unresolved、fingerprint drift は run-level fatal/usage とし、既存 output を変更しない。
- SIGINT は temporary output を cleanup し exit 130。すでに存在した output と target repository は変更しない。
- partial failure の stdout/stderr は agent が parse できる一貫した summary と diagnostic channel を維持する。

- `not_applicable` は target 不在、`incomplete` は target があるが安全に解析できない状態であり、相互に変換しない。
- failure diagnostic は stable code、severity、domain、safe repository-relative location、recoverability、human-readable message を持つ。source body と secret は含めない。
- stop condition: 三 domain の applicability、partial success retention、aggregate manifest、exit code、atomicity、minimum/latest CI が acceptance で成立するまで Initiative を完了扱いにしない。

## 受け入れ条件

| ID | 観測可能な完了条件 | acceptance test |
| --- | --- | --- |
| I07-AC-001 | domain 無指定で三 domain を順に実行し、一つの aggregate manifest を出力する。 | I07-AT-001 |
| I07-AC-002 | Next incomplete、Python/SQLAlchemy complete で Artifact を保持し exit 3 にする。 | I07-AT-002 |
| I07-AC-003 | Next target なしは Node 未導入でも not_applicable、overall exit 0。 | I07-AT-003 |
| I07-AC-004 | endpoint/fingerprint/output collision の run-level failure で success Artifact を公開しない。 | I07-AT-004 |
| I07-AC-005 | 0/1/2/3/130 と stdout/stderr/manifest の組合せを table-driven に検証する。 | I07-AT-005 |
| I07-AC-006 | macOS/Linux、Python 3.12 と latest stable、Git 2.39 と latest、Next 選択時 Node 22 と latest を CI で確認する。 | I07-AT-006 |
| I07-AC-007 | uv lock/npm lock、license inventory、offline runtime install fixture を検証する。 | I07-AT-007 |

- **I07-AC-001〜I07-AC-007 がすべて満たされ、planned test command が clean checkout で成功すること。**
- Requirement、Design、Plan の trace table が一致し、unresolved acceptance gap がないこと。
- release boundary: Next.js 対応と multi-domain orchestration の完了をもって Initiative 完了。Python+SQLAlchemy intermediate release からの additive extension とする。

## 制約・前提

- initial platform は macOS と Linux。native Windows は対象外。
- Core/CLI/Git/manifest/Python/SQLAlchemy は Python 3.12 以上。Next adapter 利用時だけ Node.js 22 LTS 以上。
- Git 2.39 以上。CI は minimum supported と repository で明示更新する latest stable lane を実行する。
- direct/indirect dependency は lockfile で exact resolve し、license inventory と offline runtime test を持つ。runtime に network access を要求しない。
- `pyclassuml` と `tree-git-diff` への runtime/package/CLI dependency を持たない。legacy code の直接 copy は license/provenance 未確認のまま行わず、初期実装は contract/test evidence を基に repository-owned code として再実装する。
- product HTML report generation、HTML command、Tailscale publication は本 Issue の製品 scope 外。`explanation.html` は specification Artifact である。
