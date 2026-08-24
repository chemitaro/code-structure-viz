---
種別: 要件定義書（Issue）
ID: "iss-00006"
タイトル: "Generate SQLAlchemy ER Snapshots"
関連GitHub: ["#6"]
package_sequence_key: "ISSUE-03"
状態: "draft"
最終更新: "2026-08-24"
親: ["epic-00002", "init-00001"]
---

# iss-00006 Generate SQLAlchemy ER Snapshots — 要件定義

詳細: [Requirement Guide](../../../../../../docs/authoring/requirement.md)

## 目的

coding agent が DB や application を起動せず、SQLAlchemy declarative ORM source から table と row-level ER semantics を JSON と PlantUML で取得できる。

利用者 story: coding agent として、migration/runtime metadata に依存せず、repository に宣言された ORM model の table、column、constraint、index、relationship を安全に説明したい。

この Issue は技術 layer の完成ではなく、利用者が command を実行して source acquisition、domain analysis、semantic JSON、PlantUML、diagnostic、acceptance evidence まで確認できる一つの vertical outcome を所有する。

## 背景

- 親 Initiative は三 domain の code structure を静的に可視化する。
- 親 Epic は安全な Git comparison と agent-first Artifact contract を一つの product outcome として統合する。
- この slice の declared dependency は ISSUE-01。依存 Issue の public contract だけを利用し、unfinished sibling の内部実装には依存しない。
- canonical authority は stable scope ID、本 Issue と親 scope の repository-relative R/D/P path、accepted ADR、interview、latest user decisions である。採用・実装開始時に HEAD と configured upstream を再検証し、current commit SHA を本文の自己 authority として固定しない。

| 親 requirement | この Issue の所有範囲 |
| --- | --- |
| EPIC-REQ-001 | sqlalchemy domain の snapshot を end-to-end で提供する。 |
| EPIC-REQ-002 | static analysis、read-only Git、safe endpoint/source、redaction、fail-closed を維持する。 |
| EPIC-REQ-003 | sqlalchemy の identity/member/relation/matching semantics を domain ownership のまま保つ。 |
| EPIC-REQ-004 | per-domain versioned semantic JSON、domain-specific PlantUML、`run-manifest/v1` descriptor、determinism/no-overwrite を提供する。 |
| EPIC-REQ-005 | domain status、0/1/2/3/130 exitとdomain-local entity budgetを実装・検証する。run-level changed-path budgetはdiff専用であり、本snapshot sliceでは適用しない。 |
| EPIC-REQ-009 | closed stdout selector、exact-byte copy、unavailable result、stderr diagnostic、usage no-publicationをsliceのpublic CLI contractとして実装・検証する。 |

## 観測可能な要件

| ID | 観測面 | 要件 |
| --- | --- | --- |
| I03-REQ-001 | CLI と observable outcome | coding agent が DB や application を起動せず、SQLAlchemy declarative ORM source から table と row-level ER semantics を JSON と PlantUML で取得できる。 |
| I03-REQ-002 | source acquisition | Python source を ISSUE-01 の安全な reader/AST pipeline で読み、declarative base、mapped class、association `Table` の静的 pattern だけを対象にする。 |
| I03-REQ-003 | semantic behavior | table identity は normalized schema 名と table 名。schema 無指定は explicit null namespace とし、module path は provenance であって table identity ではない。 |
| I03-REQ-004 | Artifact/output | semantic JSON は domain `sqlalchemy`、document kind `snapshot` と table/row identity、source location、coverage、diagnostic を持つ。 |
| I03-REQ-005 | failure behavior | declarative target候補があるのにDB/runtime evaluationを必要とする場合はunknown/incompleteとし、評価して補完しない。entity budget超過はdomain incomplete exit 3でaffected semantic JSON/PlantUMLを公開しない。implicit changed-path gateはdiff専用でありsnapshotでは実行せず、snapshotへの`--from`/`--to`/`--pr-target`/`--max-changed-paths`指定はusage error、exit 2とする。 |
| I03-REQ-006 | safety/determinism | 解析対象 module、plugin、migration、build script、application entry point を import または実行しない。 同じ source bytes、endpoint、resolved config、adapter version では entity・member・relation・diagnostic・Artifact path の順序と SHA-256 が決定的になる。 |
| I03-REQ-007 | stdout contract | `--stdout SELECTOR`を高々1回のclosed selectorとして検証し、available exact bytes、unavailable result、selectorなしsummary、stderr diagnostics、exit 2 no-publicationを提供する。 |

### I03-REQ-001

coding agent が DB や application を起動せず、SQLAlchemy declarative ORM source から table と row-level ER semantics を JSON と PlantUML で取得できる。
### I03-REQ-002

Python source を ISSUE-01 の安全な reader/AST pipeline で読み、declarative base、mapped class、association `Table` の静的 pattern だけを対象にする。
### I03-REQ-003

table identity は normalized schema 名と table 名。schema 無指定は explicit null namespace とし、module path は provenance であって table identity ではない。
### I03-REQ-004

semantic JSON は domain `sqlalchemy`、document kind `snapshot` と table/row identity、source location、coverage、diagnostic を持つ。
### I03-REQ-005

declarative target候補があるのにDB/runtime evaluationを必要とする場合はunknown/incompleteとし、評価して補完しない。entity budget超過はdomain incomplete exit 3でaffected semantic JSON/PlantUMLを公開しない。implicit changed-path gateはdiff専用でありsnapshotでは実行せず、snapshotへの`--from`/`--to`/`--pr-target`/`--max-changed-paths`指定はusage error、exit 2とする。
### I03-REQ-006

解析対象 module、plugin、migration、build script、application entry point を import または実行しない。 同じ source bytes、endpoint、resolved config、adapter version では entity・member・relation・diagnostic・Artifact path の順序と SHA-256 が決定的になる。


### I03-REQ-007

`--stdout SELECTOR`を高々1回のclosed selectorとして検証し、available exact bytes、unavailable result、selectorなしsummary、stderr diagnostics、exit 2 no-publicationを提供する。

### CLI examples

```bash
code-structure-viz snapshot --repo . --domain sqlalchemy --output-dir /tmp/csv-er-snapshot
code-structure-viz snapshot --repo . --domain sqlalchemy --target path:src/models --format semantic-json --format plantuml --output-dir /tmp/csv-models-er
code-structure-viz snapshot --repo . --domain sqlalchemy --format semantic-json --stdout sqlalchemy:semantic-json --output-dir /tmp/csv-stdout
```

### source acquisition contract

- Python source を ISSUE-01 の安全な reader/AST pipeline で読み、declarative base、mapped class、association `Table` の静的 pattern だけを対象にする。
- DB 接続、engine、Session、Alembic、`MetaData.create_all()`、import side effect、runtime mapper inspection を使用しない。
- modern `DeclarativeBase`/`Mapped`/`mapped_column` と、静的に同定できる classic declarative/`Column` pattern を扱う。曖昧な factory return は推測しない。
- repository 内 source が ORM target を持たない場合は `not_applicable`。target 候補があるが syntax/alias 解決で安全に解析できない場合は `incomplete`。

### semantic contract

- table identity は normalized schema 名と table 名。schema 無指定は explicit null namespace とし、module path は provenance であって table identity ではない。
- table entity に column、primary/foreign/unique/check constraint、index、relationship、inheritance、association table を typed row member として保持する。
- row identity は domain kind と declarative name/structural key。order は semantics から除外し、source order だけの変更を semantic change にしない。
- column type、nullable、PK/FK/unique、index、relationship target/cardinality/back_populates を安全に正規化する。SQL/default literal は `redacted` と presence/category だけを保持する。
- ForeignKey と `relationship()` は別 relation kind とし、同一の意味へ畳み込まない。

### output contract

- semantic JSON は domain `sqlalchemy`、document kind `snapshot` と table/row identity、source location、coverage、diagnostic を持つ。
- PlantUML ER は table を entity、column/constraint/index/relationship を row として表示し、FK と ORM relationship の線・label を分離する。
- source default literal、connection URL、absolute path は出力せず、redaction count と rule version を manifest に記録する。

### snapshot and diff option separation

`snapshot` は一つの run-start immutable `SourceView` を解析する use case であり、implicit base、start HEAD merge-base anchor、`FileChangeSet`、`ChangedPathAdmissionGate` を構築または参照しない。`snapshot` と `--from`、`--to`、`--pr-target`、`--max-changed-paths` のいずれかを併用した場合は source acquisition/publication 前の usage error、exit 2、stdout 空、Artifact 0件とする。implicit baseを解決できない repository、または1,001件以上の changed pathsが存在する working treeでも、snapshotの結果はそれらに影響されない。snapshotにはdomain-local entity budgetだけを適用する。

### incomplete publication contract

`incomplete` は `incomplete_kind` により次の二種類へ分ける。`not_applicable`、run-level fatal、usage error と混同しない。

| incomplete_kind | 判定条件 | affected domain payload | manifest / sibling | exit |
| --- | --- | --- | --- | --- |
| `partial_safe` | failure が局所的に隔離でき、残る subset が semantic に安全で、coverage と diagnostic が欠落範囲を明示し、全 requested payload が redaction を満たし、entity budget 内である。 | status `incomplete` の requested semantic JSON と PlantUML を安全 subset として公開する。truncation や failure entity の added/removed 推測はしない。 | `payload_available: true`、`incomplete_kind`、coverage、diagnostic、Artifact descriptor を記録する。all-domain は健全 sibling とともに保持する。 | 3 |
| `payload_unavailable` | safe subset がない、global source acquisition/protocol/schema/security/unsafe-path failure、entity budget 超過、または diff のいずれかの side acquisition/static analysis failureである。 | affected domain の semantic JSON と PlantUML を公開しない。 | run-level fatalでない限りsafe core/aggregate manifestに `payload_available: false`、`incomplete_kind`、coverage/diagnostic/countを記録し、健全 siblingを保持する。 | 3 |

snapshot の一部 file parse/read/type-resolution failure は、失敗 file を隔離し安全 subset と欠落 coverageを証明できる場合だけ `partial_safe` になれる。diff は before/after のどちらか一方でも source acquisition または static analysis が失敗した時点で `payload_unavailable` とし、added/removed を生成しない。both-side snapshot が完全に成立した後の局所的な context failureだけが、上の全条件を満たす場合に限り `partial_safe` になれる。


### stdout selector contract

`--stdout SELECTOR` は省略可能で、command line 全体で高々1回だけ指定できる。`SELECTOR` の文法は次の二形式に閉じる。

- `manifest`
- `DOMAIN:FORMAT`。`DOMAIN` は `python`、`sqlalchemy`、`next` のいずれか、`FORMAT` は `semantic-json`、`plantuml` のいずれか。

boolean flag、path、alias、略記、大小文字違い、値省略は受理しない。`--stdout` の重複、文法不正、resolved selected domains に含まれない domain、resolved requested formats に含まれない format は、source acquisition と publication の前に usage error として確定する。結果は exit 2、stdout 空、safe diagnostic は stderr、semantic JSON・PlantUML・final run manifest を含む Artifact は0件である。

`--stdout` を省略した場合、stdout は `code-structure-viz.run-summary/v1` の決定的な UTF-8 JSON 1行だけとする。summary は schema、run status、exit code、domain status、final manifest の relative path または null を持ち、source body、literal、secret、absolute path を持たない。diagnostic は stdout に混在させず stderr へ出す。

有効な selector の対象 Artifact が公開可能な場合、stdout は output directory に公開した対象 file と正確に同じ bytes だけを出す。前後に summary、label、diagnostic を付けない。`--output-dir` は引き続き必須であり、stdout は永続 Artifact の代替ではなく複製である。

有効な selector の対象が `not_applicable`、`payload_unavailable`、run fatal、または handled interrupt により利用不能な場合、stdout は次の `code-structure-viz.stdout-result/v1` JSONを決定的な1行で出す。field order は `type`、`schema`、`selector`、`availability`、`domain_status` または `run_status`、`stable_reason`、`artifact` とし、`availability` は false、`artifact` は null である。domain selector で domain outcome が確定している場合だけ `domain_status`、run-level outcome では `run_status` を使う。`manifest` selector も final manifest が存在しない場合は同じ規則を使う。既存の exit 0/1/3/130 を変更しない。

```json
{"type":"stdout_result","schema":"code-structure-viz.stdout-result/v1","selector":"sqlalchemy:semantic-json","availability":false,"domain_status":"not_applicable","stable_reason":"domain_not_applicable","artifact":null}
```

| case | stdout | stderr | exit | publication |
| --- | --- | --- | --- | --- |
| selector なし、complete/not_applicable/incomplete/fatal/interrupt | `run-summary/v1` JSON 1行 | diagnostic のみ | 0/1/3/130 | outcome contract に従う |
| available `DOMAIN:FORMAT` | 対象 Artifact の exact bytes | diagnostic のみ | 0 または `partial_safe` の3 | output-dir へ通常公開 |
| available `manifest` | final run manifest の exact bytes | diagnostic のみ | 0 または3 | output-dir へ通常公開 |
| domain not_applicable | `stdout_result/v1` 1行、`domain_status: not_applicable`、`stable_reason: domain_not_applicable` | diagnostic のみ | 0 | domain payload なし、manifest は通常規則 |
| domain payload_unavailable | `stdout_result/v1` 1行、`domain_status: incomplete`、`stable_reason: domain_payload_unavailable` | diagnostic のみ | 3 | affected payload なし、safe manifest/sibling は通常規則 |
| run fatal または final manifest 不在 | `stdout_result/v1` 1行、`run_status: fatal`、reason は `run_fatal` または `final_manifest_unavailable` | diagnostic のみ | 1 | final manifestを含めrun-level Artifactなし |
| handled interrupt | `stdout_result/v1` 1行、`run_status: interrupted`、`stable_reason: run_interrupted` | diagnostic のみ | 130 | staging cleanup |
| duplicate/invalid/unselected-domain/unrequested-format | 空 | usage diagnostic | 2 | Artifactなし |

## スコープ

### 対象

- `sqlalchemy` domain の `snapshot` use case を CLI input から acceptance test まで届ける。
- common CLI/config/diagnostic/Artifact contract は、この slice に必要な範囲だけ導入または拡張する。
- repository-owned implementation、tests、fixtures、documentation、lockfile、CI lane を含む。

### 対象外

- DB introspection、live schema、Alembic revision/migration execution
- SQL text の literal 保存、server default の実行評価
- temporal ER diff と ghost row
- 非 SQLAlchemy ORM、product HTML report

### 親契約として変更しない境界

- `--repo PATH` で解析対象 repository を明示し、`--output-dir PATH` を必須とする。
- `--format semantic-json|plantuml` は複数指定でき、未指定時は semantic JSON と PlantUML の両方を生成する。
- `--config PATH` を受け付ける。優先順位は CLI、`.code-structure-viz.toml`、built-in default であり、unknown key と型不正は exit 2 とする。
- 出力は一時 staging directory で完成させ、既存 path との衝突を検査してから atomic に公開する。既存 file は上書きしない。
- `--stdout SELECTOR` は高々1回のclosed grammarであり、exact-byte/unavailable-result/no-selector-summary/usage-error contractは下記sectionを正本とする。

- 解析対象 module、plugin、migration、build script、application entry point を import または実行しない。
- Git repository は read-only とし、fetch、checkout、reset、stash、clean、commit、ref 更新を実行しない。すべての Git subprocess で lazy fetch、external diff、textconv、color を無効化する。
- Artifact には repository-relative path、symbol、type、signature、relation、line range だけを許可し、source body、comment、literal、secret らしい値、absolute path を含めない。
- 同じ source bytes、endpoint、resolved config、adapter version では entity・member・relation・diagnostic・Artifact path の順序と SHA-256 が決定的になる。

## 失敗・境界条件

- declarative target候補の一部がDB/runtime evaluationを必要としても、該当modelを隔離し、残るtable subset、coverage、safe diagnostic、redaction、entity-budget passを証明できる場合だけ`partial_safe` JSON+PlantUML+manifestを公開する。safe subset不在、global acquisition/schema/security/unsafe-path failureは`payload_unavailable` manifest-onlyとし、runtime評価で補完しない。
- 同一schema.table identity競合が局所隔離できない場合は`payload_unavailable`とする。安全な非競合subsetを明示的に隔離できる場合だけ`partial_safe`を許し、module pathをidentityへ追加して勝手に解消しない。
- entity-per-diagram budgetはdomain-local gateでdefault 500。overrideなしで超過したdomainは`incomplete`、exit 3とし、切り捨てず、そのdomainのsemantic JSONとPlantUMLを公開しない。valid core runではsafe run manifestを公開し、requested/resolved limit、actual count、diagnosticを記録する。all-domainではsuccessful sibling Artifactを保持する。positive integerの`--max-entities N`は通常公開を許可し、同じ値とcountをmanifestへ記録する。invalid overrideはexit 2。
- `not_applicable`はORM target evidence不在、`incomplete`はcandidateがあるが安全に解析できない状態であり、相互に変換しない。
- diagnosticはsource body、SQL default literal、DB URL、secret、absolute pathを含めない。
- stop condition: table/row identity、redaction、not_applicable/incomplete、DB非接続、entity budget acceptanceが成立するまでtemporal ER matchingとghost rowへ進まない。

## 受け入れ条件

| ID | 観測可能な完了条件 | acceptance test |
| --- | --- | --- |
| I03-AC-001 | declarative modelとassociation tableをtable/row semantic JSONとER PlantUMLにする。 | I03-AT-001 |
| I03-AC-002 | FKとrelationship、constraint/index、inheritanceを別kindとして保持する。 | I03-AT-002 |
| I03-AC-003 | isolated runtime-only/broken/duplicate candidateは`partial_safe` JSON+PlantUML+manifest、safe subset不在またはglobal schema/security failureは`payload_unavailable` manifest-onlyとし、runtime評価やidentity改変で補完せずexit 3にする。 | I03-AT-003 |
| I03-AC-004 | DB connectorとtarget importを呼ばず、default/URL/secret literalをArtifactへ出さない。 | I03-AT-004 |
| I03-AC-005 | source declaration orderがsemanticsに影響しないrow orderingとhashを確認する。 | I03-AT-005 |
| I03-AC-006 | ORM targetなしはnot_applicable、候補あり解析不能はincompleteを区別する。 | I03-AT-006 |
| I03-AC-007 | 501 entitiesはdomain `incomplete_kind: payload_unavailable`・exit 3・affected JSON/PlantUMLなし・manifest countあり、valid 600 overrideはrequested/resolved/count付きで成功する。snapshotへの`--from`/`--to`/`--pr-target`/`--max-changed-paths`はexit 2・Artifactなしとする。 | I03-AT-007 |
| I03-AC-008 | stdout selectorのvalid/invalid/duplicate/domain/format、exact-byte、not_applicable/payload_unavailable/fatal/interrupt result、selectorなしsummaryをtable-drivenに満たす。 | I03-AT-008 |

- **I03-AC-001〜I03-AC-008 がすべて満たされ、planned test command が clean checkout で成功すること。**
- Requirement、Design、Plan の trace table が一致し、unresolved acceptance gap がないこと。
- release boundary: ISSUE-01のcommon snapshot/output contractを拡張するSQLAlchemy snapshot slice。ISSUE-04完了まではER diffを約束しない。

## 制約・前提

- initial platform は macOS と Linux。native Windows は対象外。
- Core/CLI/Git/manifest/Python/SQLAlchemy は Python 3.12 以上。Next adapter 利用時だけ Node.js 22 LTS 以上。
- Git 2.39 以上。CI は minimum supported と repository で明示更新する latest stable lane を実行する。
- direct/indirect dependency は lockfile で exact resolve し、license inventory と offline runtime test を持つ。runtime に network access を要求しない。
- `pyclassuml` と `tree-git-diff` への runtime/package/CLI dependency を持たない。legacy code の直接 copy は license/provenance 未確認のまま行わず、初期実装は contract/test evidence を基に repository-owned code として再実装する。
- product HTML report generation、HTML command、Tailscale publication は本 Issue の製品 scope 外。`explanation.html` は specification Artifact である。
