---
種別: 設計書（Epic）
ID: "epic-00002"
タイトル: "Establish Safe Git Structure Comparison"
関連GitHub: ["#2"]
状態: "draft"
最終更新: "2026-08-24"
依存: ["requirement.md"]
親: ["init-00001"]
---

# epic-00002 Establish Safe Git Structure Comparison — 設計

詳細: [Design Guide](../../../../docs/authoring/design.md)

## 設計目標

- one Epic の中で safe source comparison spine と three domain semantics を seven independently acceptable vertical slices にする。
- first slice に common foundation を必要最小限だけ含め、後続 slice は stable contract を additive に拡張する。
- each Issue は CLI input、source acquisition、domain analysis、JSON、PlantUML、diagnostic、acceptance test を end-to-end で所有する。
- cross-Issue contract は versioned schema/port とし、private implementation/class/module layout を dependency にしない。

| Design ID | Requirement trace | Epic decision |
| --- | --- | --- |
| EPIC-DES-001 | EPIC-REQ-001, EPIC-REQ-007 | seven vertical slice DAG と two release gates を採用する。 |
| EPIC-DES-002 | EPIC-REQ-002 | SourceView、start-HEAD anchored endpoint、metadata-only FileChangeSet、real/empty-side DualSnapshot、ImpactGraph を reusable spine にする。 |
| EPIC-DES-003 | EPIC-REQ-003 | minimal common envelope と three domain-owned adapters を分離し、all-domain semantic envelope を設けない。 |
| EPIC-DES-004 | EPIC-REQ-004, EPIC-REQ-005 | run-level changed-path gate、domain-local entity gate、OutputTransaction、`run-manifest/v1`、status/exit aggregation を cross-Issue contract にする。 |
| EPIC-DES-005 | EPIC-REQ-006 | Python package と optional Next workspace、two lockfiles、CI matrix を採用する。 |
| EPIC-DES-006 | EPIC-REQ-008 | HTML/runtime/legacy/public plugin boundary を product architecture 外に置く。 |

## Current / Target

Current commit `867ee6929283dfc84711bce245b784d2b8e3e9e6` は exactly one Epic と seven active vertical Issue nodes、および各 canonical R/D/P を含むが、production implementation は未着手である。Target は同じ one-Epic/seven-Issue DAG を維持しつつ、domain presence、budget outcomes、all-domain output、working-tree anchor、hunk safety、traceability を一意にした product plan とする。

```plantuml
@startuml
title Epic の vertical Issue dependency DAG
left to right direction
rectangle "ISSUE-01
Python snapshot" as I01
rectangle "ISSUE-02
Python diff" as I02
rectangle "ISSUE-03
SQLAlchemy snapshot" as I03
rectangle "ISSUE-04
SQLAlchemy diff
intermediate release" as I04
rectangle "ISSUE-05
Next snapshot" as I05
rectangle "ISSUE-06
Next diff" as I06
rectangle "ISSUE-07
all-domain run
Initiative completion" as I07
I01 --> I02
I01 --> I03
I02 --> I04
I03 --> I04
I01 --> I05
I02 --> I06
I05 --> I06
I04 --> I07
I06 --> I07
@enduml
```

## 責務・Interface

| Cross-Issue contract | Introduced/owned by | Consumers |
| --- | --- | --- |
| CLI/config/diagnostic/Artifact minimal v1 | ISSUE-01 | ISSUE-02〜07 |
| named endpoint/read-only Git/freeze/FileChangeSet/dual diff | ISSUE-02 | ISSUE-04, ISSUE-06, ISSUE-07 |
| SQLAlchemy table/row snapshot | ISSUE-03 | ISSUE-04, ISSUE-07 |
| SQLAlchemy row diff/ghost/matching | ISSUE-04 | ISSUE-07 |
| Next adapter protocol/component snapshot | ISSUE-05 | ISSUE-06, ISSUE-07 |
| Next component diff/matching/unknown | ISSUE-06 | ISSUE-07 |
| domain registry/outcome aggregation/output transaction | ISSUE-07 | final CLI release |

### package architecture (planned)

```text
src/code_structure_viz/
  cli/                 command grammar and exit mapping
  application/         snapshot/diff/run coordination
  core/                config, diagnostic, status, budget
  source/              read-only Git, endpoint, freezer, SourceView, FileChangeSet
  semantic/            envelope, graph primitive, diff/impact ports
  artifacts/           JSON/PlantUML descriptors, manifest, output transaction
  adapters/python/     Python-owned semantics
  adapters/sqlalchemy/ SQLAlchemy-owned semantics
  adapters/next/       Python bridge only
adapters/next/
  src/                 repository-owned TypeScript semantics
  test/                compiler/protocol fixtures
tests/                 unit/integration/acceptance/security/packaging
```

すべて planned path であり、baseline に存在すると主張しない。

## data / failure

- `DomainResult` は `complete`/`not_applicable`/`incomplete` の discriminated union で、`None`/empty ambiguity を許さない。
- `RunOutcome` は domain aggregation より前に usage、interrupt、run-level fatal changed-path admission を処理する。valid core run 後の domain incomplete/entity overrun は exit 3。
- `OutputTransaction` は selected domain payload と aggregate manifest を staging するが、run-level fatal では final manifest も公開しない。domain-local incomplete では affected payload を除外し、safe manifest と successful siblings を公開する。

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

## 変更対象

- Initiative/Epic canonical R/D/P と seven Issue trace contract の整合を adoption gate で検証する。
- seven active Issue のcanonical R/D/Pとtrace contractを整合させる。.meta.json、report、accepted ADR、interviewは変更対象外とする。
- explanation HTML and package artifacts are evidence imports, not product runtime files。
- production code/tests/docs/CI rootsは各Issue implementationで作成するplanned targetであり、canonical specificationの更新を実装完了と扱わない。

## 移行・互換性・rollback

- existing `iss-00003` は silent rename せず supersede し、Git comparison concern は ISSUE-02 が所有する。
- Issue rollout は topological order で進める。downstream Issue は Plan 内で parent acceptance や dependency direction を変更できない。
- intermediate release after ISSUE-04 is maintained while Next work proceeds.
- rollback removes the latest vertical slice while retaining prior accepted CLI/schema compatibility; public break requires version up.

## testability

- each Issue has independent acceptance commands and stop condition.
- Epic integration runs dependency contract fixtures, all acceptance suites, cross-domain partial failure, package/offline/license/CI matrix.
- verticality check rejects an Issue that cannot produce user-visible JSON/PlantUML/diagnostic without unfinished sibling internals.
- DAG と各 Issue の Requirement→Design→Plan→acceptance→test matrix を machine-checkable にし、EPIC-REQ-003/004/005 の親 mapping と全 slice-specific boundary を検査する。

## risk

| Risk | Control |
| --- | --- |
| ISSUE-01 becomes a framework project | Only implement foundation exercised by Python snapshot acceptance. |
| duplicate diff implementations drift | Reuse source/endpoint ports; keep matching/render semantics adapter-owned. |
| ISSUE-07 becomes horizontal integration only | Require one-command multi-domain observable result, partial Artifact retention, manifest/exit acceptance. |
| provisional Issue history misleads | Supersede iss-00003 with explicit mapping to ISSUE-02. |
| release gate hidden in implementation | Record M2/M4 in Epic Requirement/Plan and acceptance matrix. |
