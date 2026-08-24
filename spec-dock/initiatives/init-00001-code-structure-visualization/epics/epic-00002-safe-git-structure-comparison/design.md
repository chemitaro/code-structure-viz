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
| EPIC-DES-007 | EPIC-REQ-005, EPIC-REQ-009 | incomplete classとstdout selector/stream routingをOutcome/CLI/OutputTransactionのshared contractとして実装可能にする。 |

## Current / Target

canonical specification tree は exactly one Epic と seven active vertical Issue nodes、および各 canonical R/D/P を含むが、production implementation は未着手である。current revision は採用・実装開始時に HEAD と configured upstream から再検証し、本文へ固定しない。Target は同じ one-Epic/seven-Issue DAG を維持しつつ、domain presence、budget outcomes、all-domain output、working-tree anchor、hunk safety、traceability を一意にした product plan とする。

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
- `OutputTransaction` は selected domain payload と aggregate manifest を staging するが、run-level fatal では final manifest も公開しない。domain-local `partial_safe` はsafe incomplete payloadとmanifestを公開し、`payload_unavailable`だけaffected payloadを除外してsafe manifestとsuccessful siblingsを公開する。

### stdout selector and stream routing

CLI parser は `--stdout` を optional single-value option として一度だけ受理し、closed grammar `manifest | DOMAIN:FORMAT` を `StdoutSelector` valueへ正規化する。domain/format の resolved selection が確定した直後、source acquisition より前に selector compatibility を検証する。boolean、path、alias、略記、大小文字違い、値省略、重複、未選択 domain、未要求 format は `UsageError` とし、source acquisition と publication の前に exit 2、stdout 空、Artifact 0件で終了する。`OutputTransaction` は開始しない。

通常 publication 後、既存 CLI/application boundary 内の stdout emitter は次のいずれか一つだけを行う。新しい command または独立 architecture layer は追加しない。

1. selector なしなら `run-summary/v1` を canonical JSON 1行として出す。
2. selected Artifact が利用可能なら、公開 file を binary read して exact bytes を複製する。
3. selected Artifact が利用不能なら、`RunOutcome`/`DomainOutcome` から `stdout-result/v1` 1行を構築する。

stdout emitter は diagnostic renderer と分離し、diagnostic は stderr だけへ出す。exact-byte copy に summary、BOM、改行補正を加えない。`stdout-result/v1` は status と stable reason だけを参照し、source content、absolute path、secret を受け取る field を持たない。handled SIGINT は cleanup 完了後に `run_status: interrupted` を返せる場合だけ exit 130 の result line を出す。process を強制終了された場合の出力は契約外である。

### diff domain presence truth table

この表は `python`、`sqlalchemy`、`next` の各 diff と domain 無指定 run に同じ意味で適用する。`present` は静的な target evidence が存在すること、`absent` はその evidence が存在しないことを表す。source acquisition または static analysis の失敗を `absent` と解釈してはならない。

| before | after | domain status | semantic comparison | publication | single-domain exit / all-domain effect |
| --- | --- | --- | --- | --- | --- |
| absent | absent | `not_applicable` | 比較しない。 | status と safe diagnostic だけを run manifest に記録し、その domain の semantic JSON と PlantUML は公開しない。 | exit 0。all-domain overall を `incomplete` にしない。 |
| present、解析成功 | present、解析成功 | `complete` | 二つの実 snapshot を比較する。 | domain semantic diff JSON、domain-specific PlantUML、run manifest descriptor を公開する。 | exit 0。 |
| present、解析成功 | absent | `complete` | 実 before snapshot と internal canonical empty-side snapshot を比較し、before の全 entity/member/relation を `removed` とする。 | domain semantic diff JSON、domain-specific PlantUML、run manifest descriptor を公開する。empty-side 自体は公開しない。 | exit 0。 |
| absent | present、解析成功 | `complete` | internal canonical empty-side snapshot と実 after snapshot を比較し、after の全 entity/member/relation を `added` とする。 | domain semantic diff JSON、domain-specific PlantUML、run manifest descriptor を公開する。empty-side 自体は公開しない。 | exit 0。 |
| target evidence あり | いずれかの side で source acquisition または static analysis 失敗 | `incomplete` / `payload_unavailable` | added/removed を推測しない。 | affected domain の semantic JSON と PlantUMLを公開しない。run manifest に `incomplete_kind: "payload_unavailable"`、`payload_available: false`、safe diagnostic、coverage、side provenance を記録し、成功 sibling Artifact は保持する。 | single-domain exit 3。all-domain overall `incomplete`、exit 3。 |

internal canonical empty-side snapshot の canonical bytes は、key sort・UTF-8・余分な空白なしで直列化した `code-structure-viz.empty-side/v1` document とする。document は `domain`、`document_kind: "internal-diff-side"`、空の `entities`/`members`/`relations` だけを持ち、endpoint や side 名を含めない。同じ domain と contract version では常に同じ SHA-256 になる。manifest の該当 side descriptor は `kind: "canonical-empty-side"`、schema、domain、SHA-256 を記録する。この internal document を成功した standalone snapshot、empty semantic Artifact、empty diagram として公開してはならない。

### `--to working-tree` implicit anchor

`--to working-tree` を `--from` なしで指定した場合は、run 開始時に working tree を repository 外へ freeze し、同じ開始時点の `HEAD^{commit}` を implicit-base candidate の merge-base 計算に使う endpoint commit anchor とする。candidate priority は explicit PR target、configured comparison target/upstream、`origin/HEAD`、local `main`/`develop`/`master` の順であり、`merge-base(candidate, start_head_anchor)` を最初に安全に解決できた結果を before endpoint とする。initial commit fallback、auto fetch、checkout は行わない。

provenance は requested `from`/`to`、frozen working-tree SHA-256 digest、start HEAD anchor、selected base candidate、resolved merge-base、`resolution_method: "implicit-base-from-start-head-anchor"` を必須とする。run 終了時 fingerprint が変化した場合は success Artifact を公開しない。

### budget outcome contract

| budget | gate / default | override なしの超過 | publication | valid override |
| --- | --- | --- | --- | --- |
| implicit changed paths | domain comparison 前の run-level admission gate。default 1,000。implicit comparison の actual changed-path count に適用する。 | fatal analysis/environment、exit 1。domain analysis を開始しない。safe machine-readable diagnostic を stderr に出す。 | semantic JSON、PlantUML、final run manifest を一切公開せず、staging を破棄する。 | positive integer の `--max-changed-paths N` で通常処理を許可する。公開 manifest に requested value、resolved value、actual changed-path count、config source を記録する。 |
| entities per diagram | domain semantic result 生成後かつ renderer/publication 前の domain-local gate。default 500。 | affected domain を `incomplete_kind: payload_unavailable` とし、単一 domain run も all-domain run も exit 3。切り捨てない。 | affected domain の semantic JSON と PlantUML は公開しない。successful sibling Artifact と aggregate run manifest は保持し、diagnostic、requested/resolved limit、actual entity count を記録する。 | positive integer の `--max-entities N` で通常公開を許可し、manifest に requested value、resolved value、actual entity count、config source を記録する。 |

override の zero、negative、non-integer、型不正、unknown config key は usage/config error、exit 2 であり、Artifact を公開しない。depth の default は upstream/downstream 各 1 で、depth は graph context を制限するだけで budget 超過の truncation 手段にはしない。

### FileChangeSet hunk safety contract

`FileChangeSet` の hunk evidence は metadata だけである。各 hunk は repository-relative old/new path、file status、old/new start line、old/new line count、同一 file 内の ordinal、および content-independent な `hunk_id` を持てる。`hunk_id` はこれら metadata の canonical tuple から SHA-256 で生成し、source bytes を入力にしない。

raw patch line、context line、added/deleted line、source body、comment、literal、secret、absolute path を memory-owned model、semantic JSON、PlantUML、manifest、diagnostic、logへ保持または公開してはならない。Git diff streamを range extraction に読む実装は、metadata を抽出した時点で本文を破棄し、serializer へ本文型を渡さない。negative acceptance test は secret-like patch、comment、literal、absolute temporary path が全 output channel に存在しないことを確認する。

### incomplete classes and publication

`DomainOutcome` は `status` に加え、status が `incomplete` の場合だけ `incomplete_kind: partial_safe | payload_unavailable` と `payload_available` を持つ。

- `partial_safe` は isolated failure set、safe subset、explicit coverage frontier、safe diagnostics、redaction pass、entity-budget pass、requested renderer passをすべて満たす場合だけ生成する。requested domain payload と manifest descriptor を同一 transaction で公開する。
- `payload_unavailable` は safe subset不在、global acquisition/protocol/schema/security/unsafe-path failure、entity overrun、または diff side failureで生成する。affected payload descriptorは空とし、safe core manifestだけを許す。
- all-domain `RunOutcome` はどちらもoverall `incomplete`/exit 3へ集約するが、`partial_safe` payloadと健全 siblingを捨てない。run-level fatalだけがfinal manifestを含む全stagingを破棄する。

serializer と manifest builder は `incomplete_kind` と `payload_available` の整合を検証する。`partial_safe` なのにrequested descriptorが欠ける状態、`payload_unavailable` なのにaffected descriptorがある状態はinternal contract failureとしてpublication前に拒否する。

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
