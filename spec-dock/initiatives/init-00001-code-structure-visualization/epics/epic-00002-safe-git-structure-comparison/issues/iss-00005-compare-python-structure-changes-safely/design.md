---
種別: 設計書（Issue）
ID: "iss-00005"
タイトル: "Compare Python Structure Changes Safely"
関連GitHub: ["#5"]
package_sequence_key: "ISSUE-02"
状態: "draft"
最終更新: "2026-08-27"
依存: ["requirement.md"]
親: ["epic-00002", "init-00001"]
---

# iss-00005 Compare Python Structure Changes Safely — 設計

詳細: [Design Guide](../../../../../../docs/authoring/design.md)

## 1. 設計判断

この文書は実装開始前の案ではなく、Issue 5 の実装コードと公開契約を対応付ける
as-built 設計である。Issue の状態は SpecDock の完了処理前なので `draft` を維持するが、
下記の path、symbol、データ形状、検証方法は 2026-08-27 時点の実装に一致する。

| ID | 要件 | 採用した設計 |
| --- | --- | --- |
| I02-DES-001 | I02-REQ-001 | `DiffApplication` が endpoint 解決、source 固定、Python 解析、差分、Artifact 公開を 1 run として調整する。 |
| I02-DES-002 | I02-REQ-002 | `ComparisonEndpointResolver` が named endpoint と implicit base を local object だけで解決し、`WorkingTreeFreezer` が開始時の working tree を private staging に固定する。 |
| I02-DES-003 | I02-REQ-003 | `DomainPresenceResolver` と `CanonicalEmptySide` が real、canonical empty、analysis failed を区別する。 |
| I02-DES-004 | I02-REQ-004 | `FileChangeSet`、semantic delta、impact、matching、side provenance を JSON の別フィールドとして公開する。 |
| I02-DES-005 | I02-REQ-005 | changed-path gate は domain 解析前、entity gate は renderer 前に実行し、run fatal と domain incomplete を分離する。 |
| I02-DES-006 | I02-REQ-006 | Git command allowlist、固定環境、静的 AST 解析、bounded subprocess、canonical JSON、atomic publication を採用する。 |
| I02-DES-007 | I02-REQ-007 | Hunk は status、path、行範囲、ordinal、content-independent ID だけを持つ value object とする。working-tree では凍結済み bytes の `SequenceMatcher` から範囲を作る。 |
| I02-DES-008 | I02-REQ-008 | `--stdout` は closed selector を acquisition 前に検証し、公開済み bytes の複製または typed unavailable result を返す。 |

## 2. 実装コンポーネント

| path / symbol | 責務 | 状態 |
| --- | --- | --- |
| `src/code_structure_viz/application/diff.py::DiffApplication` | 1 run の orchestration、gate、publication、cancellation | 実装済み |
| `src/code_structure_viz/source/git_repository.py::GitRepositoryReader` | Git version/root/ref/tree/blob/name-status 読み取り、untracked/unmerged 列挙。固定環境で read-only 実行 | 実装済み |
| `src/code_structure_viz/source/endpoints.py::ComparisonEndpointResolver` | `from`/`to`、`head`、`working-tree`、implicit base、start HEAD anchor の解決 | 実装済み |
| `src/code_structure_viz/source/freezer.py::WorkingTreeFreezer` | working-tree source を repository 外 staging へ凍結し、再読取時に drift を検出 | 実装済み |
| `src/code_structure_viz/source/source_view.py::SourceViewBuilder` / `SourceView` | secure file read、NFC/path collision、fingerprint、inventory | 実装済み |
| `src/code_structure_viz/source/file_changes.py::FileChangeSet` / `HunkMetadata` | Git metadata と frozen bytes からの metadata-only file change evidence | 実装済み |
| `src/code_structure_viz/semantic/diff.py::DomainPresenceResolver` / `SemanticDiffer` / `ImpactExplorer` | side 分類、canonical empty、entity/member/relation delta、union impact | 実装済み |
| `src/code_structure_viz/adapters/python/matcher.py::PythonMoveMatcher` | name evidence、exact structural fingerprint、one-to-one の高信頼 move だけを採用 | 実装済み |
| `src/code_structure_viz/adapters/python/diff_renderer.py` | semantic diff JSON と member-level PlantUML の deterministic rendering | 実装済み |
| `src/code_structure_viz/artifacts/manifest.py::DiffManifestBuilder` | diff provenance、budget、side、Artifact descriptor を `run-manifest/v1` へ組み立てる | 実装済み |

`pyclassuml`、`tree-git-diff`、SQLAlchemy、Next.js、HTML/Tailscale はこの Issue の実行時依存に
含めない。既存 snapshot CLI の path と contract は維持し、diff の新規コードから既存外部 CLI を
import しない。

## 3. CLI と endpoint

```text
code-structure-viz diff --repo PATH --domain python --output-dir PATH
  [--from REF] [--to REF] [--pr-target REF]
  [--format semantic-json|plantuml] [--stdout SELECTOR]
  [--upstream-depth N] [--downstream-depth N]
  [--max-changed-paths N] [--max-entities N] [--config PATH]
```

`--repo`、`--domain python`、`--output-dir` は必須。format 省略時は semantic JSON と PlantUML の
順に生成する。`--from working-tree`、不正な ref、重複 option、未選択 format/domain は
source acquisition 前の usage error（exit 2、stdout 空、Artifact なし）である。

| `from` | `to` | before | after | resolution method |
| --- | --- | --- | --- | --- |
| なし | なし | start HEAD に対する implicit base | start 時 frozen working tree | `implicit-base-from-start-head-anchor` |
| REF | なし | REF | start 時 frozen working tree | `explicit-from-to-working-tree` |
| なし | `working-tree` | start HEAD に対する implicit base | start 時 frozen working tree | `implicit-base-from-start-head-anchor` |
| なし | `REF`/`head` | endpoint anchor に対する implicit base | REF または start HEAD | `implicit-base-from-endpoint-anchor` |
| REF | REF/`head` | REF | REF または start HEAD | `explicit-from-to` |

implicit candidate は `--pr-target`、config の target/upstream、`origin/HEAD`、local
`main`/`develop`/`master` の順で、既存 local object に merge-base があるものだけを採用する。
fetch、checkout、worktree/index/ref mutation は行わない。provenance には caller の
`requested.from`/`requested.to`、resolved object ID、start HEAD、candidate、merge-base、method を記録する。

## 4. source acquisition と cancellation

1. run 開始に Git version、repository identity、HEAD、tracked/cached/untracked path、unmerged path を取得する。
2. commit side は `ls-tree` を一度列挙し、blob bytes を一度だけ読み、`SourceView` を構築する。missing object は domain empty に変換せず fatal とし、candidate `.py` の non-blob または working-tree の non-regular/read failure は `CSV-PY-001` の failed source として記録する。
3. working-tree side は `WorkingTreeFreezer` が secure descriptor read と symlink/path/collision checks を行い、repository 外の staging へコピーする。source bytes と inventory を同じ run の証拠にする。
4. 解析中・公開直前に cancellation checkpoint を置く。Git 子プロセスは process group として bounded stdout/stderr で監視し、cancel 時は terminate/kill して exit 130 を返す。
5. working-tree 公開直前に HEAD、path enumeration、untracked、unmerged、source inventory/fingerprint を再取得して開始時と比較する。不一致は `CSV-SOURCE-001` の fatal とし、staging を公開しない。

`SourceView` の公開 fingerprint は source schema、head、file descriptor、failures の canonical bytes
から作る。working-tree の内部 `SourceInventoryEntry` は path、raw path、kind、size、digest だけを
保持し、source body、absolute staging path、Git stderr を manifest/diagnostic に渡さない。inventory の
`unavailable`/`other` は path が存在する証拠として扱い、untracked なら `?` の FileChange として
changed-path budget に含める。取得不能な path を absent または canonical empty side へ変換しない。

## 5. FileChangeSet

commit-to-commit は `git diff --no-ext-diff --no-textconv --no-color --find-renames=50% --find-copies=50% --name-status -z --format= -- <before> <after>` の name/status metadata だけを使う。working-tree は Git の patch を読み直さず、開始時に列挙した inventory と frozen before/after bytes から status（`A/M/D/R/C/T/U/?`）を決める。

通常の content hunk は `SequenceMatcher` の opcode を old/new line range へ変換する。純粋な
`parse_unified_hunks` helper は bounded（payload 16 MiB、line 128 KiB）で、Git quoted path の
UTF-8/C escape/octal を厳格に decode し、対応 path のない hunk や不正 path を成功扱いしない。
production diff lifecycle はこの raw patch helper を呼ばない。

公開 schema `code-structure-viz.file-change-set/v1` は次の形だけを許可する。

```json
{"schema":"code-structure-viz.file-change-set/v1","before":"<sha>","after":"<sha>","files":[{"status":"M","old_path":"src/app.py","new_path":"src/app.py","hunks":[{"old_start":1,"old_line_count":1,"new_start":1,"new_line_count":1,"ordinal":0,"hunk_id":"<sha256>"}]}]}
```

`hunk_id` は status/path/range/ordinal の canonical JSON の SHA-256 であり、patch body、context、
source、comment、literal、secret、absolute path を保持しない。path は repository-relative NFC
UTF-8 のみで、sort は UTF-8 bytes order とする。

## 6. Python semantic diff

各 side は既存 `PythonSnapshotAnalyzer` と `PythonTargetSelector` で immutable `SourceView` bytes
だけを AST 解析する。`SemanticDiffer` は entity、member、relation を closed identity で比較し、
class/decorator/member/relation の delta に加えて changed entity ID も seed にする。空白、comment、
import order だけの変更は seed にならない。

`DomainPresenceResolver.side` の分類は次の通り。

| before | after | status | payload |
| --- | --- | --- | --- |
| absent | absent | `not_applicable` | semantic/PlantUML なし、file-change と safe manifest のみ |
| real | real | `complete` | semantic diff JSON と PlantUML |
| real | absent | `complete` | internal canonical empty side と比較し全 removed |
| absent | real | `complete` | internal canonical empty side と比較し全 added |
| analysis failed を含む | 任意 | `incomplete/payload_unavailable` | affected semantic/PlantUML なし、safe manifest のみ |

working-tree に `U` が含まれる場合もこの行を適用する。`semantic_sides.before` は before source
を通常どおり解析できれば `real`（失敗時だけ `analysis-failed`）、`semantic_sides.after` は
`analysis-failed` とし、解析を行わない after source fingerprint を digest に使う。両 side を
根拠なく `analysis-failed` に固定しない。

canonical empty side は sorted key の canonical UTF-8 JSON（domain、document kind、空 entities/
members/relations）から毎回同じ digest を得る。endpoint/side 名や source body は含めず、standalone
Artifact として公開しない。

impact は before/after relation の union graph を使い、deleted entity の before edge も辿る。
upstream/downstream は別 frontier、default depth は各 1、depth 0 でも frontier coverage を記録する。
move は identity change、同名または同じ qualified name、exact structural fingerprint、unique
one-to-one candidate の全条件を満たすときだけ `moved`、それ以外は removed+added とする。

## 7. budget、publication、stream

- changed-path default は 1,000。超過は domain 解析前の run fatal exit 1、diagnostic と run-summary のみ、output directory は作成しない。
- Python entity default は 500。超過は domain `incomplete/payload_unavailable` exit 3、`file-changes.json` と safe `run-manifest.json` だけを公開する。
- side acquisition/static analysis failure、unmerged path、unsafe path、schema/integrity failure は affected payload を推測せず unavailable とする。
- `OutputTransaction` は staging、descriptor/hash check、collision check 後に no-replace atomic rename する。run fatal/usage/interrupt は staging を破棄する。

`--stdout` は `manifest` または `python:semantic-json`/`python:plantuml` の一回だけ。available
Artifact は公開後の exact bytes を複製し、unavailable は `stdout-result/v1`、selector 省略時は
`run-summary/v1` の canonical JSON 1 行を返す。diagnostic は stderr のみで、source/body/secret/
absolute path/Git stderr/traceback を含めない。

## 8. 公開契約と検証対象

更新した schema は `schemas/file-change-set-v1.schema.json`、`semantic-v1.schema.json`、
`run-manifest-v1.schema.json`、`diagnostic-v1.schema.json`。diff manifest は comparison、sources、
semantic_sides、file_change_set、changed_path_budget、domain budget、Artifact descriptors を含む。
diff が `payload_unavailable` の場合も run-level `file-changes.json` descriptor は保持し、domain の
semantic/PlantUML artifact paths は空にする。設定済み comparison 候補は `config.resolved.comparison`
へ `target_ref`/`upstream_ref`（未指定側は `null`）として記録し、manifest の diagnostic catalog は
`CSV-DIFF-001`〜`003` を受理する。
snapshot の既存 manifest/schema は同じ JSON serializer と契約を共有するが、snapshot fingerprint と
diff fingerprint はそれぞれの正本入力から独立に計算する。

| 観測領域 | 実装テスト |
| --- | --- |
| endpoint、working-tree、budget、CLI | `tests/acceptance/python/test_diff_cli.py`, `tests/acceptance/git/test_changed_path_budget.py` |
| domain presence、entity budget、stdout | `tests/acceptance/python/test_domain_presence_diff.py`, `test_diff_entity_budget.py`, `test_stdout_selector.py` |
| semantic seed、impact、move | `tests/acceptance/python/test_semantic_seed.py`, `tests/integration/python/test_impact_union_graph.py`, `test_move_matching.py` |
| Git/source safety、cancellation | `tests/unit/source/test_git_repository.py`, `test_source_view.py`, `tests/integration/source/test_git_repository.py`, `tests/security/test_git_read_only.py` |
| hunk redaction/protocol、schema | `tests/unit/source/test_file_changes.py`, `tests/security/test_file_change_hunk_redaction.py`, `tests/contracts/test_json_schemas.py` |

受入れの正本は test の実ファイル名と実行結果であり、未作成の仮想 test path を契約に記載しない。
HTML report、Tailscale/GitHub Pages 配信、SQLAlchemy/Next adapter、legacy CLI compatibility は後続
Issue の責務で、この Issue の成功条件には含めない。

```plantuml
@startuml
title Issue 5 Python diff lifecycle
actor "coding agent" as Agent
component "DiffApplication" as App
component "EndpointResolver" as Endpoints
component "SourceView / Freezer" as Sources
component "PythonSnapshotAnalyzer" as Analyzer
component "SemanticDiffer" as Differ
component "OutputTransaction" as Output
Agent -> App : diff request
App -> Endpoints : resolve from/to + start HEAD
Endpoints --> App : provenance + endpoint pair
App -> Sources : freeze/read immutable sides
Sources --> App : fingerprints + inventory
App -> Analyzer : parse both SourceViews
Analyzer --> Differ : snapshots + coverage
Differ --> App : semantic delta + union impact
App -> Output : stage JSON/PlantUML/manifest
Output --> Agent : atomic artifacts + stdout result
@enduml
```
