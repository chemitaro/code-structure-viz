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
- canonical authority は exact verified current commit `867ee6929283dfc84711bce245b784d2b8e3e9e6` の accepted ADR、interview、親 R/D/P と本 Issue の current canonical textである。

| 親 requirement | この Issue の所有範囲 |
| --- | --- |
| EPIC-REQ-001 | sqlalchemy domain の snapshot を end-to-end で提供する。 |
| EPIC-REQ-002 | static analysis、read-only Git、safe endpoint/source、redaction、fail-closed を維持する。 |
| EPIC-REQ-003 | sqlalchemy の identity/member/relation/matching semantics を domain ownership のまま保つ。 |
| EPIC-REQ-004 | per-domain versioned semantic JSON、domain-specific PlantUML、`run-manifest/v1` descriptor、determinism/no-overwrite を提供する。 |
| EPIC-REQ-005 | domain status、0/1/2/3/130 exitとdomain-local entity budgetを実装・検証する。run-level changed-path budgetはdiff専用であり、本snapshot sliceでは適用しない。 |

## 観測可能な要件

| ID | 観測面 | 要件 |
| --- | --- | --- |
| I03-REQ-001 | CLI と observable outcome | coding agent が DB や application を起動せず、SQLAlchemy declarative ORM source から table と row-level ER semantics を JSON と PlantUML で取得できる。 |
| I03-REQ-002 | source acquisition | Python source を ISSUE-01 の安全な reader/AST pipeline で読み、declarative base、mapped class、association `Table` の静的 pattern だけを対象にする。 |
| I03-REQ-003 | semantic behavior | table identity は normalized schema 名と table 名。schema 無指定は explicit null namespace とし、module path は provenance であって table identity ではない。 |
| I03-REQ-004 | Artifact/output | semantic JSON は domain `sqlalchemy`、document kind `snapshot` と table/row identity、source location、coverage、diagnostic を持つ。 |
| I03-REQ-005 | failure behavior | declarative target候補があるのにDB/runtime evaluationを必要とする場合はunknown/incompleteとし、評価して補完しない。entity budget超過はdomain incomplete exit 3でaffected semantic JSON/PlantUMLを公開しない。implicit changed-path gateはdiff専用でありsnapshotでは実行せず、snapshotへの`--max-changed-paths`指定はusage error、exit 2とする。 |
| I03-REQ-006 | safety/determinism | 解析対象 module、plugin、migration、build script、application entry point を import または実行しない。 同じ source bytes、endpoint、resolved config、adapter version では entity・member・relation・diagnostic・Artifact path の順序と SHA-256 が決定的になる。 |

### I03-REQ-001

coding agent が DB や application を起動せず、SQLAlchemy declarative ORM source から table と row-level ER semantics を JSON と PlantUML で取得できる。
### I03-REQ-002

Python source を ISSUE-01 の安全な reader/AST pipeline で読み、declarative base、mapped class、association `Table` の静的 pattern だけを対象にする。
### I03-REQ-003

table identity は normalized schema 名と table 名。schema 無指定は explicit null namespace とし、module path は provenance であって table identity ではない。
### I03-REQ-004

semantic JSON は domain `sqlalchemy`、document kind `snapshot` と table/row identity、source location、coverage、diagnostic を持つ。
### I03-REQ-005

declarative target候補があるのにDB/runtime evaluationを必要とする場合はunknown/incompleteとし、評価して補完しない。entity budget超過はdomain incomplete exit 3でaffected semantic JSON/PlantUMLを公開しない。implicit changed-path gateはdiff専用でありsnapshotでは実行せず、snapshotへの`--max-changed-paths`指定はusage error、exit 2とする。
### I03-REQ-006

解析対象 module、plugin、migration、build script、application entry point を import または実行しない。 同じ source bytes、endpoint、resolved config、adapter version では entity・member・relation・diagnostic・Artifact path の順序と SHA-256 が決定的になる。


### CLI examples

```bash
code-structure-viz snapshot --repo . --domain sqlalchemy --output-dir /tmp/csv-er-snapshot
code-structure-viz snapshot --repo . --domain sqlalchemy --target path:src/models --format semantic-json --format plantuml --output-dir /tmp/csv-models-er
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
- `--stdout` を明示した場合だけ、選択した一つの Artifact または run manifest を標準出力へ複製する。通常時の stdout は machine-readable summary だけとする。

- 解析対象 module、plugin、migration、build script、application entry point を import または実行しない。
- Git repository は read-only とし、fetch、checkout、reset、stash、clean、commit、ref 更新を実行しない。すべての Git subprocess で lazy fetch、external diff、textconv、color を無効化する。
- Artifact には repository-relative path、symbol、type、signature、relation、line range だけを許可し、source body、comment、literal、secret らしい値、absolute path を含めない。
- 同じ source bytes、endpoint、resolved config、adapter version では entity・member・relation・diagnostic・Artifact path の順序と SHA-256 が決定的になる。

## 失敗・境界条件

- declarative target候補があるのにDB/runtime evaluationを必要とする場合はunknown/incompleteとし、評価して補完しない。
- 同一schema.table identityが競合する場合はduplicate diagnosticとしてincomplete。module pathをidentityへ追加して勝手に解消しない。
- entity-per-diagram budgetはdomain-local gateでdefault 500。overrideなしで超過したdomainは`incomplete`、exit 3とし、切り捨てず、そのdomainのsemantic JSONとPlantUMLを公開しない。valid core runではsafe run manifestを公開し、requested/resolved limit、actual count、diagnosticを記録する。all-domainではsuccessful sibling Artifactを保持する。positive integerの`--max-entities N`は通常公開を許可し、同じ値とcountをmanifestへ記録する。invalid overrideはexit 2。
- `not_applicable`はORM target evidence不在、`incomplete`はcandidateがあるが安全に解析できない状態であり、相互に変換しない。
- diagnosticはsource body、SQL default literal、DB URL、secret、absolute pathを含めない。
- stop condition: table/row identity、redaction、not_applicable/incomplete、DB非接続、entity budget acceptanceが成立するまでtemporal ER matchingとghost rowへ進まない。

## 受け入れ条件

| ID | 観測可能な完了条件 | acceptance test |
| --- | --- | --- |
| I03-AC-001 | declarative modelとassociation tableをtable/row semantic JSONとER PlantUMLにする。 | I03-AT-001 |
| I03-AC-002 | FKとrelationship、constraint/index、inheritanceを別kindとして保持する。 | I03-AT-002 |
| I03-AC-003 | runtime-only factory、duplicate table identity、broken declarative sourceをincompleteにする。 | I03-AT-003 |
| I03-AC-004 | DB connectorとtarget importを呼ばず、default/URL/secret literalをArtifactへ出さない。 | I03-AT-004 |
| I03-AC-005 | source declaration orderがsemanticsに影響しないrow orderingとhashを確認する。 | I03-AT-005 |
| I03-AC-006 | ORM targetなしはnot_applicable、候補あり解析不能はincompleteを区別する。 | I03-AT-006 |
| I03-AC-007 | 501 entitiesはdomain incomplete・exit 3・affected JSON/PlantUMLなし・manifest countあり、valid 600 overrideはrequested/resolved/count付きで成功する。snapshotへの`--max-changed-paths`はexit 2・Artifactなしとする。 | I03-AT-007 |

- **I03-AC-001〜I03-AC-007 がすべて満たされ、planned test command が clean checkout で成功すること。**
- Requirement、Design、Plan の trace table が一致し、unresolved acceptance gap がないこと。
- release boundary: ISSUE-01のcommon snapshot/output contractを拡張するSQLAlchemy snapshot slice。ISSUE-04完了まではER diffを約束しない。

## 制約・前提

- initial platform は macOS と Linux。native Windows は対象外。
- Core/CLI/Git/manifest/Python/SQLAlchemy は Python 3.12 以上。Next adapter 利用時だけ Node.js 22 LTS 以上。
- Git 2.39 以上。CI は minimum supported と repository で明示更新する latest stable lane を実行する。
- direct/indirect dependency は lockfile で exact resolve し、license inventory と offline runtime test を持つ。runtime に network access を要求しない。
- `pyclassuml` と `tree-git-diff` への runtime/package/CLI dependency を持たない。legacy code の直接 copy は license/provenance 未確認のまま行わず、初期実装は contract/test evidence を基に repository-owned code として再実装する。
- product HTML report generation、HTML command、Tailscale publication は本 Issue の製品 scope 外。`explanation.html` は specification Artifact である。
