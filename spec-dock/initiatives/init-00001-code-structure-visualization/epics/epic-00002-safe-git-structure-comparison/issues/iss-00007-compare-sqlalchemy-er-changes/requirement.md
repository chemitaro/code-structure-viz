---
種別: 要件定義書（Issue）
ID: "iss-00007"
タイトル: "Compare SQLAlchemy ER Changes"
関連GitHub: ["#7"]
package_sequence_key: "ISSUE-04"
状態: "draft"
最終更新: "2026-08-24"
親: ["epic-00002", "init-00001"]
---

# iss-00007 Compare SQLAlchemy ER Changes — 要件定義

詳細: [Requirement Guide](../../../../../../docs/authoring/requirement.md)

## 目的

coding agent が before/after declarative ORM semantics を比較し、table と column/constraint/index/relationship の row-level delta、ghost removal、影響 context を説明できる。

利用者 story: coding agent として、Git の行差分ではなく ER semantics の追加・削除・変更・移動を識別し、削除された定義の before value も失わずに review 資料へ使いたい。

この Issue は技術 layer の完成ではなく、利用者が command を実行して source acquisition、domain analysis、semantic JSON、PlantUML、diagnostic、acceptance evidence まで確認できる一つの vertical outcome を所有する。

## 背景

- 親 Initiative は三 domain の code structure を静的に可視化する。
- 親 Epic は安全な Git comparison と agent-first Artifact contract を一つの product outcome として統合する。
- この slice の declared dependency は ISSUE-02, ISSUE-03。依存 Issue の public contract だけを利用し、unfinished sibling の内部実装には依存しない。
- canonical authority は exact commit `7951ddabc2e6a3d66edb77eada7c6c16923264f7` の accepted ADR と interview、および本 package の親 R/D/P である。

| 親 requirement | この Issue の所有範囲 |
| --- | --- |
| EPIC-REQ-001 | sqlalchemy domain の diff を end-to-end で提供する。 |
| EPIC-REQ-002 | static analysis、read-only Git、redaction、fail-closed を維持する。 |
| EPIC-REQ-003 | versioned semantic JSON、domain-specific PlantUML、manifest を生成する。 |
| EPIC-REQ-004 | complete/not_applicable/incomplete と exit contract を slice の範囲で実装する。 |

## 観測可能な要件

| ID | 観測面 | 要件 |
| --- | --- | --- |
| I04-REQ-001 | CLI と observable outcome | coding agent が before/after declarative ORM semantics を比較し、table と column/constraint/index/relationship の row-level delta、ghost removal、影響 context を説明できる。 |
| I04-REQ-002 | source acquisition | ISSUE-02 の named endpoint、read-only Git、external working-tree freeze、fingerprint、FileChangeSet を再利用する。 |
| I04-REQ-003 | semantic behavior | table entity と column/constraint/index/relationship row の added/removed/modified/moved を before/after value とともに保持する。 |
| I04-REQ-004 | Artifact/output | ER diff JSON は table delta と typed row delta を分離し、各 delta に before/after representation、matching evidence、source provenance を持たせる。 |
| I04-REQ-005 | failure behavior | 一方の endpoint の model が解析不能な場合、その table/row を removed/added と断定せず domain incomplete とする。 |
| I04-REQ-006 | safety/determinism | 解析対象 module、plugin、migration、build script、application entry point を import または実行しない。 同じ source bytes、endpoint、resolved config、adapter version では entity・member・relation・diagnostic・Artifact path の順序と SHA-256 が決定的になる。 |

### I04-REQ-001

coding agent が before/after declarative ORM semantics を比較し、table と column/constraint/index/relationship の row-level delta、ghost removal、影響 context を説明できる。
### I04-REQ-002

ISSUE-02 の named endpoint、read-only Git、external working-tree freeze、fingerprint、FileChangeSet を再利用する。
### I04-REQ-003

table entity と column/constraint/index/relationship row の added/removed/modified/moved を before/after value とともに保持する。
### I04-REQ-004

ER diff JSON は table delta と typed row delta を分離し、各 delta に before/after representation、matching evidence、source provenance を持たせる。
### I04-REQ-005

一方の endpoint の model が解析不能な場合、その table/row を removed/added と断定せず domain incomplete とする。
### I04-REQ-006

解析対象 module、plugin、migration、build script、application entry point を import または実行しない。 同じ source bytes、endpoint、resolved config、adapter version では entity・member・relation・diagnostic・Artifact path の順序と SHA-256 が決定的になる。


### CLI examples

```bash
code-structure-viz diff --repo . --domain sqlalchemy --from origin/main --to working-tree --output-dir /tmp/csv-er-diff
code-structure-viz diff --repo . --domain sqlalchemy --from release/1 --to release/2 --upstream-depth 1 --downstream-depth 1 --output-dir /tmp/csv-er-release
```

### source acquisition contract

- ISSUE-02 の named endpoint、read-only Git、external working-tree freeze、fingerprint、FileChangeSet を再利用する。
- 各 endpoint で ISSUE-03 の immutable SQLAlchemy snapshot を独立生成し、片側だけの parse success を削除として補完しない。
- domain target 不在は not_applicable、target 存在かつ一方の snapshot が安全に作れない場合は incomplete。

### semantic contract

- table entity と column/constraint/index/relationship row の added/removed/modified/moved を before/after value とともに保持する。
- removed row は after diagram に ghost row として残し、赤・破線・`-`、before value を表示する。modified row は before/after の安全な normalized value を併記する。
- table/member identity の一対一 matching は exact identity を優先し、rename evidence+structural fingerprint+unique candidate の全条件を満たす場合だけ moved とする。
- table または row relation delta を changed seed とし、before/after ER graph union 上で upstream/downstream を別々に探索する。
- SQL default literal は両 endpoint と diff でも redacted のままとし、value comparison は presence/category の安全な差だけに限定する。

### output contract

- ER diff JSON は table delta と typed row delta を分離し、各 delta に before/after representation、matching evidence、source provenance を持たせる。
- PlantUML は table-level と row-level の visual vocabulary を同時に示し、removed row を ghost 表示する。
- manifest は両 snapshot digest、adapter version、coverage、diagnostic、partial failure、Artifact hash を記録する。

## スコープ

### 対象

- `sqlalchemy` domain の `diff` use case を CLI input から acceptance test まで届ける。
- common CLI/config/diagnostic/Artifact contract は、この slice に必要な範囲だけ導入または拡張する。
- repository-owned implementation、tests、fixtures、documentation、lockfile、CI lane を含む。

### 対象外

- DB migration risk の自動判定、Alembic operation の生成
- live DB schema drift、runtime mapper state
- Next.js/Python cross-domain relation
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

- 一方の endpoint の model が解析不能な場合、その table/row を removed/added と断定せず domain incomplete とする。
- ambiguous rename/move は removed+added。default literal の raw value が必要な matching は行わない。
- diagram entity 500 超過は切り捨てず nonzero。明示 override と resulting count を manifest に記録する。

- `not_applicable` は target 不在、`incomplete` は target があるが安全に解析できない状態であり、相互に変換しない。
- failure diagnostic は stable code、severity、domain、safe repository-relative location、recoverability、human-readable message を持つ。source body と secret は含めない。
- stop condition: 全 row kind の before/after delta、ghost rendering、ambiguous matching、片側解析 failure が acceptance で固定されるまで intermediate release を宣言しない。

## 受け入れ条件

| ID | 観測可能な完了条件 | acceptance test |
| --- | --- | --- |
| I04-AC-001 | table と各 row kind の added/removed/modified を before/after 値付きで出力する。 | I04-AT-001 |
| I04-AC-002 | removed row が ghost row、modified row が before/after 表記、記号と線種を持つ。 | I04-AT-002 |
| I04-AC-003 | 一意 structural match だけ moved、ambiguous table/row は removed+added。 | I04-AT-003 |
| I04-AC-004 | 片側 parse failure を削除にせず incomplete にする。 | I04-AT-004 |
| I04-AC-005 | before/after/diff の default literal と absolute path が redacted される。 | I04-AT-005 |
| I04-AC-006 | deleted table の before edge を union graph context に保持する。 | I04-AT-006 |

- **I04-AC-001〜I04-AC-006 がすべて満たされ、planned test command が clean checkout で成功すること。**
- Requirement、Design、Plan の trace table が一致し、unresolved acceptance gap がないこと。
- release boundary: ISSUE-01〜04 で Python class と SQLAlchemy ER の snapshot/diff が利用可能となる intermediate release milestone。

## 制約・前提

- initial platform は macOS と Linux。native Windows は対象外。
- Core/CLI/Git/manifest/Python/SQLAlchemy は Python 3.12 以上。Next adapter 利用時だけ Node.js 22 LTS 以上。
- Git 2.39 以上。CI は minimum supported と repository で明示更新する latest stable lane を実行する。
- direct/indirect dependency は lockfile で exact resolve し、license inventory と offline runtime test を持つ。runtime に network access を要求しない。
- `pyclassuml` と `tree-git-diff` への runtime/package/CLI dependency を持たない。legacy code の直接 copy は license/provenance 未確認のまま行わず、初期実装は contract/test evidence を基に repository-owned code として再実装する。
- product HTML report generation、HTML command、Tailscale publication は本 Issue の製品 scope 外。`explanation.html` は specification Artifact である。
