---
種別: 要件定義書（Epic）
ID: "epic-00002"
タイトル: "Establish Safe Git Structure Comparison"
関連GitHub: ["#2"]
状態: "draft"
最終更新: "2026-08-24"
親: ["init-00001"]
---

# epic-00002 Establish Safe Git Structure Comparison — 要件定義

詳細: [Requirement Guide](../../../../docs/authoring/requirement.md)

## 目的

safe Git structure comparison を product spine とし、三 domain の static snapshot/diff を coding agent が一貫して利用できる状態を一つの Epic で届ける。Epic は domain implementation を横断 layer に分解せず、observable vertical outcomes と stable cross-Issue contract を定める。

## 背景

- 親 Initiative の全 product scope を本 Epic 一つが担う。既存 title は保持するが、Git comparison だけでなく snapshot、domain semantics、Artifact、partial failure、packaging まで不足なく含む。
- existing `iss-00003` は provisional horizontal scaffold で、Issue boundary の authority ではない。
- accepted ADR は dual snapshot、named endpoint、adapter ownership、agent-first Artifact、安全 boundary、vertical slicing を要求する。

## 観測可能な要件

| ID | contract area | Epic requirement |
| --- | --- | --- |
| EPIC-REQ-001 | vertical domain delivery | Python、SQLAlchemy、Next の snapshot/diff と all-domain orchestration を seven independently acceptable vertical Issues で届ける。 |
| EPIC-REQ-002 | safe comparison spine | named endpoints、immutable SourceView、working-tree freeze、read-only Git、dual semantic snapshot、impact union を横断 contract にする。 |
| EPIC-REQ-003 | semantic ownership | common envelope と domain-owned identity/member/relation/matching を分離する。 |
| EPIC-REQ-004 | Artifact/output | per-domain JSON/PlantUML selectable default-both、`run-manifest/v1` provenance、redaction、determinism、no overwrite を全 slice で維持し、`domain: all` semantic payload を生成しない。 |
| EPIC-REQ-005 | failure and budgets | diff domain presence truth table、canonical empty-side、complete/not_applicable/incomplete、partial success、0/1/2/3/130、run-level 1000、domain-local 500、depth 1+1 default を維持する。 |
| EPIC-REQ-006 | platform/dependency | Python 3.12+ core、Node 22+ optional Next、Git 2.39+、macOS/Linux、lock/license/offline/minimum/latest CI を提供する。 |
| EPIC-REQ-007 | release order | ISSUE-04 を intermediate release、ISSUE-07 を Initiative completion boundary とする。 |
| EPIC-REQ-008 | exclusions | product HTML、runtime/DB/build execution、Windows、plugin ABI、legacy dependency/compatibility を実装しない。 |

### Issue ownership

| Stable key | title | observable outcome | dependency |
| --- | --- | --- | --- |
| ISSUE-01 | Generate Python Structure Snapshots | coding agent または人間が、対象 Python repository を実行せずに class 構造を semantic JSON と PlantUML で取得できる。 | なし |
| ISSUE-02 | Compare Python Structure Changes Safely | coding agent が named endpoint で before/after Python semantic snapshot を安全に固定し、意味のある class/member/relation change と影響 context だけを比較できる。 | ISSUE-01 |
| ISSUE-03 | Generate SQLAlchemy ER Snapshots | coding agent が DB や application を起動せず、SQLAlchemy declarative ORM source から table と row-level ER semantics を JSON と PlantUML で取得できる。 | ISSUE-01 |
| ISSUE-04 | Compare SQLAlchemy ER Changes | coding agent が before/after declarative ORM semantics を比較し、table と column/constraint/index/relationship の row-level delta、ghost removal、影響 context を説明できる。 | ISSUE-02, ISSUE-03 |
| ISSUE-05 | Generate Next.js Component Snapshots | coding agent が first-party TypeScript adapter を通じ、Next.js repository の module、exported component、props、static relation、client boundary を JSON と PlantUML で取得できる。 | ISSUE-01 |
| ISSUE-06 | Compare Next.js Component Changes | coding agent が before/after Next.js semantic snapshot から component/props/import/render/boundary change と影響 context を比較できる。 | ISSUE-02, ISSUE-05 |
| ISSUE-07 | Run Unified Multi-Domain Structure Comparison | coding agent が domain を省略した一回の command で Python、SQLAlchemy、Next の適用可否・成功・不完全を区別し、成功 Artifact を保持した集約 manifest と正しい exit code を得られる。 | ISSUE-04, ISSUE-06 |

## スコープ

### 対象

- source acquisition、snapshot、semantic diff、impact traversal、three first-party domain adapters、JSON/PlantUML/manifest、diagnostic、CI/package。
- Issue 間の versioned contract と rollout/integration order。
- intermediate release と final Initiative completion gate。

### 対象外

- contract-only/source-freezer-only/parser-only/renderer-only の horizontal Issue。
- product HTML report/command/publication とその schema/UI/distribution。
- runtime analysis、mutable Git、DB/Alembic/build execution、legacy dependency/compatibility。

## 失敗・境界条件

- sibling internals が安定しないまま共有される場合は integration を停止し、parent Design の stable contract を更新する。
- cross-domain universal semantics や runtime relation を Issue が独自に発明しない。

### diff domain presence truth table

この表は `python`、`sqlalchemy`、`next` の各 diff と domain 無指定 run に同じ意味で適用する。`present` は静的な target evidence が存在すること、`absent` はその evidence が存在しないことを表す。source acquisition または static analysis の失敗を `absent` と解釈してはならない。

| before | after | domain status | semantic comparison | publication | single-domain exit / all-domain effect |
| --- | --- | --- | --- | --- | --- |
| absent | absent | `not_applicable` | 比較しない。 | status と safe diagnostic だけを run manifest に記録し、その domain の semantic JSON と PlantUML は公開しない。 | exit 0。all-domain overall を `incomplete` にしない。 |
| present、解析成功 | present、解析成功 | `complete` | 二つの実 snapshot を比較する。 | domain semantic diff JSON、domain-specific PlantUML、run manifest descriptor を公開する。 | exit 0。 |
| present、解析成功 | absent | `complete` | 実 before snapshot と internal canonical empty-side snapshot を比較し、before の全 entity/member/relation を `removed` とする。 | domain semantic diff JSON、domain-specific PlantUML、run manifest descriptor を公開する。empty-side 自体は公開しない。 | exit 0。 |
| absent | present、解析成功 | `complete` | internal canonical empty-side snapshot と実 after snapshot を比較し、after の全 entity/member/relation を `added` とする。 | domain semantic diff JSON、domain-specific PlantUML、run manifest descriptor を公開する。empty-side 自体は公開しない。 | exit 0。 |
| target evidence あり | いずれかの side で source acquisition または static analysis 失敗 | `incomplete` | added/removed を推測しない。 | affected domain の semantic JSON と PlantUMLを公開しない。safe diagnostic、coverage、side provenance を run manifest に記録し、成功 sibling Artifact は保持する。 | single-domain exit 3。all-domain overall `incomplete`、exit 3。 |

internal canonical empty-side snapshot の canonical bytes は、key sort・UTF-8・余分な空白なしで直列化した `code-structure-viz.empty-side/v1` document とする。document は `domain`、`document_kind: "internal-diff-side"`、空の `entities`/`members`/`relations` だけを持ち、endpoint や side 名を含めない。同じ domain と contract version では常に同じ SHA-256 になる。manifest の該当 side descriptor は `kind: "canonical-empty-side"`、schema、domain、SHA-256 を記録する。この internal document を成功した standalone snapshot、empty semantic Artifact、empty diagram として公開してはならない。

### `--to working-tree` implicit anchor

`--to working-tree` を `--from` なしで指定した場合は、run 開始時に working tree を repository 外へ freeze し、同じ開始時点の `HEAD^{commit}` を implicit-base candidate の merge-base 計算に使う endpoint commit anchor とする。candidate priority は explicit PR target、configured comparison target/upstream、`origin/HEAD`、local `main`/`develop`/`master` の順であり、`merge-base(candidate, start_head_anchor)` を最初に安全に解決できた結果を before endpoint とする。initial commit fallback、auto fetch、checkout は行わない。

provenance は requested `from`/`to`、frozen working-tree SHA-256 digest、start HEAD anchor、selected base candidate、resolved merge-base、`resolution_method: "implicit-base-from-start-head-anchor"` を必須とする。run 終了時 fingerprint が変化した場合は success Artifact を公開しない。

### budget outcome contract

| budget | gate / default | override なしの超過 | publication | valid override |
| --- | --- | --- | --- | --- |
| implicit changed paths | domain comparison 前の run-level admission gate。default 1,000。implicit comparison の actual changed-path count に適用する。 | fatal analysis/environment、exit 1。domain analysis を開始しない。safe machine-readable diagnostic を stderr に出す。 | semantic JSON、PlantUML、final run manifest を一切公開せず、staging を破棄する。 | positive integer の `--max-changed-paths N` で通常処理を許可する。公開 manifest に requested value、resolved value、actual changed-path count、config source を記録する。 |
| entities per diagram | domain semantic result 生成後かつ renderer/publication 前の domain-local gate。default 500。 | affected domain を `incomplete` とし、単一 domain run も all-domain run も exit 3。切り捨てない。 | affected domain の semantic JSON と PlantUML は公開しない。successful sibling Artifact と aggregate run manifest は保持し、diagnostic、requested/resolved limit、actual entity count を記録する。 | positive integer の `--max-entities N` で通常公開を許可し、manifest に requested value、resolved value、actual entity count、config source を記録する。 |

override の zero、negative、non-integer、型不正、unknown config key は usage/config error、exit 2 であり、Artifact を公開しない。depth の default は upstream/downstream 各 1 で、depth は graph context を制限するだけで budget 超過の truncation 手段にはしない。

### FileChangeSet hunk safety contract

`FileChangeSet` の hunk evidence は metadata だけである。各 hunk は repository-relative old/new path、file status、old/new start line、old/new line count、同一 file 内の ordinal、および content-independent な `hunk_id` を持てる。`hunk_id` はこれら metadata の canonical tuple から SHA-256 で生成し、source bytes を入力にしない。

raw patch line、context line、added/deleted line、source body、comment、literal、secret、absolute path を memory-owned model、semantic JSON、PlantUML、manifest、diagnostic、logへ保持または公開してはならない。Git diff streamを range extraction に読む実装は、metadata を抽出した時点で本文を破棄し、serializer へ本文型を渡さない。negative acceptance test は secret-like patch、comment、literal、absolute temporary path が全 output channel に存在しないことを確認する。

### all-domain output boundary

all-domain orchestration は `code-structure-viz.semantic/v1` の `domain: all` payload を生成しない。各 adapter が own domain の semantic JSON と domain-specific PlantUML を所有する。aggregate は `code-structure-viz.run-manifest/v1` だけであり、run status、domain status、Artifact descriptor、diagnostic、coverage、provenance、budget values/counts、safe graph summary counts を持つ。run manifest の root または domain summary に domain-owned `entities`、`members`、`relations`、matching record を統合しない。cross-domain identity または relation を推測しない。

## 受け入れ条件

| ID | Epic completion evidence |
| --- | --- |
| EPIC-AC-001 | ISSUE-01 の Python snapshot acceptance が成立。 |
| EPIC-AC-002 | ISSUE-02 の Python dual-snapshot diff、domain presence/empty-side、start-HEAD anchor、metadata-only FileChangeSet、two-level budget、Git safety acceptance が成立。 |
| EPIC-AC-003 | ISSUE-03/04 の SQLAlchemy snapshot/row diff、shared domain presence/endpoint/hunk/budget acceptance と intermediate release gate が成立。 |
| EPIC-AC-004 | ISSUE-05/06 の Next snapshot/diff、shared domain presence/endpoint/hunk/budget、protocol、Node optionality acceptance が成立。 |
| EPIC-AC-005 | ISSUE-07 の per-domain-only semantic output、aggregate `run-manifest/v1`、cross-domain presence/budget matrix、partial success/exit acceptance が成立。 |
| EPIC-AC-006 | 全 Issue の Requirement→Design→Plan→test trace と DAG が完全。 |
| EPIC-AC-007 | read-only/static/redaction/determinism/budget/platform/package regression が全体で成功。 |
| EPIC-AC-008 | product HTML scope exclusion と specification HTML separation が維持。 |

`EPIC-AC-001`〜`EPIC-AC-008` の全条件と `INIT-AC-001`〜`INIT-AC-008` trace が成立したときだけ Epic complete とする。

## 制約・前提

- Issue stable key は package/adoption sequencing 用であり、SpecDock が割り当てる実 node ID を偽らない。
- existing `iss-00003` は semantic material を ISSUE-02 へ反映するが、managed metadata を直接 rename できる根拠がないため node 自体は supersede 推奨。
- planned production path/symbol は baseline に存在しない。Issue Plan の候補であり、実装時に repository facts と照合する。
- common dependency、version pin、license、lockfile、offline runtime、optional Node separation を各 Issue acceptance に含める。
