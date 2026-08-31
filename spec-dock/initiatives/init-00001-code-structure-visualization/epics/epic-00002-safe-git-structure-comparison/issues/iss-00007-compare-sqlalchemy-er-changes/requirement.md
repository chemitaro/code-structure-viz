---
種別: 要件定義書（Issue）
ID: "iss-00007"
タイトル: "Compare SQLAlchemy ER Changes"
関連GitHub: ["#7"]
package_sequence_key: "ISSUE-04"
状態: "ready"
最終更新: "2026-08-31"
親: ["epic-00002", "init-00001"]
---

# iss-00007 Compare SQLAlchemy ER Changes — 要件定義

詳細: [Requirement Guide](../../../../../../docs/authoring/requirement.md)

## 目的

coding agent が、Issue #5 の安全な Git comparison と Issue #6 の SQLAlchemy snapshot semantics を使って before/after の ER 構造を比較し、table・row・relation の意味的な差分と影響 context を semantic JSON と PlantUML で確認できるようにする。

本 Issue は SQLAlchemy 用の新しい解析器や汎用 diff framework を作ることを目的としない。既に存在する二つの SQLAlchemy snapshot を、既存の diff lifecycle に最小限接続することだけを所有する。

## 前提

- `iss-00005` で `DiffApplication`、named endpoint、working-tree freeze、metadata-only `FileChangeSet`、changed-path budget、atomic publication、stdout/stderr/exit contract が実装済みである。
- `iss-00006` で SQLAlchemy の table・row・relation identity、coverage、redaction、semantic JSON、ER semantics、PlantUML v2 が実装済みである。
- 現在の `diff` CLI と semantic differ は Python-only であり、本 Issue は `--domain sqlalchemy` を追加する。
- Issue #5/#6 の semantic JSON、ID、schemaを、本 Issue の都合だけで変更しない。PlantUML v2の
  表示上の不具合は、既存の意味を変えないrenderer-owned projectionとして修正できる。

## 観測可能な要件

| ID | 要件 |
| --- | --- |
| I04-REQ-001 | `code-structure-viz diff --domain sqlalchemy` が既存の diff CLI/source/publication lifecycle で実行でき、requested format の `sqlalchemy.diff.semantic.json` と `sqlalchemy.diff.puml` を生成できる。 |
| I04-REQ-002 | SQLAlchemy snapshot の既存 ID を基準に table・relation は `added` / `removed`、row は `added` / `removed` / `modified` を safe before/after value とともに出力する。provenance-only の table mapping と relation `source` 変更は delta を出さない。ID が変わった定義を rename/move と推測せず `removed + added` とする。 |
| I04-REQ-003 | changed table と changed row/relation の owner/source/内部 target を seed とし、before/after の内部 ER relation union を既存 upstream/downstream depth で探索して影響 context を出力する。 |
| I04-REQ-004 | parent diff truth table と Issue #5 の failure/publication contract を維持する。片側の SQLAlchemy domain が安全に absent と証明できる場合だけ canonical empty-side と比較し、片側の SQLAlchemy analysis が incomplete の場合は diff payload を生成せず `payload_unavailable` とする。 |
| I04-REQ-005 | Issue #5/#6 の安全境界を維持する。対象 source を import/executeせず、DBへ接続せず、Gitを変更せず、raw source・raw hunk・literal・secret・absolute pathを公開せず、同一入力では deterministic な結果を返す。 |

## observable behavior

### CLI

既存 diff option をそのまま使い、domain の許可値だけを `python|sqlalchemy` に拡張する。

```bash
code-structure-viz diff --repo . --output-dir /tmp/csv-er-diff --domain sqlalchemy --from origin/main --to working-tree
```

SQLAlchemy diff に `--target` や SQLAlchemy 専用 config は追加しない。`--format`、`--stdout`、depth、changed-path/entity budget の意味は既存 diff contract と同じである。

### semantic diff

- whole SQLAlchemy snapshot 同士を比較する。
- `entities` は table、`members` は Issue #6 の全 row kind、`relations` は Issue #6 の relation を表す。
- 同一 ID が片側だけにある場合は `added` / `removed`。
- table は `added` / `removed` のみとし、同一 ID の table で mapping provenance だけが変わる場合は delta を出さない。
- 同一 ID の member で safe semantic value が変わった場合は `modified`。
- relation は `added` / `removed` のみとし、同一 ID の relation で `source` だけが変わる provenance-only change は delta を出さない。
- source path/range や mapping provenance だけの変化は semantic `modified` にしない。
- delta の before/after representation は Issue #6 の redacted semantic projection を再利用する。
- move/rename heuristic、name similarity、line proximity、raw literal comparison は行わない。
- impact traversal は内部 relation だけを対象とし、削除された relation の before edge も union に残す。

### publication / exit

| condition | publication | exit |
| --- | --- | --- |
| both sides complete | `file-changes.json`、requested SQLAlchemy diff payload、`run-manifest.json` | 0 |
| both sides safely absent | `file-changes.json`、`run-manifest.json` | 0 |
| one side safely absent / other complete | canonical empty-side と real snapshot の全 added/removed diff、`file-changes.json`、`run-manifest.json` | 0 |
| either SQLAlchemy side incomplete | SQLAlchemy diff payloadなし、`file-changes.json` と safe `run-manifest.json` | 3 |
| entity budget overrun | SQLAlchemy diff payloadなし、`file-changes.json` と safe `run-manifest.json` | 3 |
| changed-path budget overrunまたはrun-level fatal | final Artifactなし | 1 |
| usage/config/stdout selector error | Artifactなし、stdout空 | 2 |
| handled interrupt | final Artifactなし | 130 |

`--stdout sqlalchemy:semantic-json|sqlalchemy:plantuml` は既存 stdout contract に従い、available payload は公開 file と exact bytes、unavailable outcome は既存 `stdout-result/v1` を返す。

### PlantUML

- changed table は `+` / `-`、changed row は `+` / `-` / `~` で識別できる。
- removed table/row は before value を ghost として残す。
- modified row は safe before/after の差が読める。
- impact context の table を変更対象と区別して表示する。
- 通常のschema/table識別子に含まれる`_`をそのまま表示し、renderer-owned escape tokenや
  schema/table区切りとの衝突は防止する。
- added tableは淡い緑`#E8F5E9`、removedは`#MistyRose`、modifiedは`#LightYellow`、contextは
  `#LightGray`の背景とし、changed rowのmarkerと文字色も保持する。
- relation の方向・種別・cardinality は Issue #6 の `build_er_view` / SQLAlchemy PlantUML v2 semantics を再利用し、新たに推測しない。
- color だけに依存して差分状態を表現しない。

## スコープ外

- table/row/relation の heuristic rename/move detection。
- diff `--target`、table selector、SQLAlchemy 専用 config。
- Alembic/migration risk、live DB、reflection、runtime mapper。
- SQLAlchemy package、DB driver、target application の import/execute。
- Next.js、`domain: all`、cross-domain relation、HTML report。
- 新しい runtime dependency、public plugin ABI、汎用 cross-domain diff framework。
- completed Python diffまたはSQLAlchemy snapshotのsemantic JSON、ID、schemaの変更。
- PlantUML v1の履歴変更、または追加背景色以外のPython diff配色・member行表現の変更。

## 受け入れ条件

| ID | 完了条件 |
| --- | --- |
| I04-AC-001 | complete before/after で table・relation の added/removed、Issue #6 row の added/removed/modified と impact context が正しく出力され、table mapping と relation source の provenance-only change は no-delta、ID変更はremoved+addedになる。 |
| I04-AC-002 | both-absent、before-only、after-only、side-incomplete が parent truth tableどおりの status、publication、exit になり、failure sideからadded/removedを捏造しない。 |
| I04-AC-003 | PlantUML が added/removed ghost/modified/impact context を判別でき、通常のschema/table識別子の`_`を可読表示し、added背景を`#E8F5E9`で統一しつつIssue #6のER relation semanticsとredactionを維持する。 |
| I04-AC-004 | changed-path/entity budget、stdout selector、atomic/no-overwrite publication が SQLAlchemy diff でも既存 contractどおり動作し、source/literal/secret/absolute pathを漏らさない。 |
| I04-AC-005 | existing Python diff と SQLAlchemy snapshot の regression が通り、Pythonの追加class/note背景だけを`#E8F5E9`へ統一し、runtime dependency・source execution・DB access・Git mutationを追加しない。 |

I04-AC-001〜I04-AC-005 がすべて成立した時点を本 Issue の実装完了条件とする。本書の `ready` は実装着手可能な仕様状態を示し、実装完了を意味しない。
