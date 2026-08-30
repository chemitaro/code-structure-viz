---
種別: 設計書（Issue）
ID: "iss-00007"
タイトル: "Compare SQLAlchemy ER Changes"
関連GitHub: ["#7"]
package_sequence_key: "ISSUE-04"
状態: "ready"
最終更新: "2026-08-30"
依存: ["requirement.md"]
親: ["epic-00002", "init-00001"]
---

# iss-00007 Compare SQLAlchemy ER Changes — 設計

詳細: [Design Guide](../../../../../../docs/authoring/design.md)

## 設計方針

SQLAlchemy diff のために新しい shared diff framework は作らない。現在の `DiffApplication` に narrow `sqlalchemy` branch を追加し、SQLAlchemy 固有の比較ロジックだけを adapter package 内の一つの新規 module に置く。

Python diff の `src/code_structure_viz/semantic/diff.py` は `PythonSnapshot` と Python semantic types に結合しているため、Issue #7 では一般化しない。SQLAlchemy は Issue #6 の model/selection/semantic/ER projection を直接再利用する。

| Design ID | Requirement | 判断 |
| --- | --- | --- |
| I04-DES-001 | I04-REQ-001,004,005 | existing `DiffApplication`、artifact transaction、manifest、stream lifecycleを共有し、domain分岐だけを追加する。 |
| I04-DES-002 | I04-REQ-002 | SQLAlchemy diff は Issue #6 の stable IDs と safe semantic projectionを比較し、heuristic move matchingを実装しない。 |
| I04-DES-003 | I04-REQ-003 | impact は SQLAlchemy relation の before/after union を local pure logic で探索する。 |
| I04-DES-004 | I04-REQ-001,004 | existing artifact/schema registriesをSQLAlchemy diff pathへ最小拡張する。 |
| I04-DES-005 | I04-REQ-005 | Issue #5/#6 の source/Git/redaction/runtime-dependency boundaryを変更しない。 |

## Current

現行 HEAD で必要な seam は次のとおりである。

- `src/code_structure_viz/core/domains.py::DIFF_DOMAINS` は `("python",)`。
- `src/code_structure_viz/cli/parser.py::DiffCliRequest`、`_validate_diff_argv`、`parse_diff_cli` は Python diff だけを受理する。
- `src/code_structure_viz/application/diff.py::DiffApplication` は endpoint resolution、SourceView、FileChangeSet、budget、publicationを既に所有するが、analysis/comparison/rendering を Python implementation へ直接接続している。
- `src/code_structure_viz/semantic/diff.py` は Python-specific である。
- `src/code_structure_viz/adapters/sqlalchemy/{analyzer,model,selection,semantic_json,er_semantics,plantuml,snapshot_adapter}.py` に Issue #6 の snapshot semantics が実装済みである。
- `src/code_structure_viz/artifacts/{manifest,writer,streams}.py` の diff path/adapter metadata は Python に閉じている。
- `schemas/semantic-v1.schema.json` と `schemas/run-manifest-v1.schema.json` は SQLAlchemy diff をまだ受理しない。

## 最小変更セット

### existing — modify

| path | 変更 |
| --- | --- |
| `src/code_structure_viz/core/domains.py` | `DIFF_DOMAINS` を `python|sqlalchemy` に拡張する。 |
| `src/code_structure_viz/cli/parser.py` | `DiffCliRequest.domain` と diff domain/stdout compatibilityを `python|sqlalchemy` にする。option setは変更しない。 |
| `src/code_structure_viz/application/diff.py` | shared source/publication lifecycleはそのままに、Python existing path と SQLAlchemy path を domain で分岐する。 |
| `src/code_structure_viz/adapters/sqlalchemy/semantic_json.py` | Issue #6 の safe table/row/relation projectionをdiffから再利用できる小さな内部 helper と SQLAlchemy diff JSON renderingを追加する。snapshot bytesは不変とする。 |
| `src/code_structure_viz/adapters/sqlalchemy/plantuml.py` | existing escaping/row formatting/ER projectionを使う diff rendering entry pointを追加する。snapshot PlantUML v2 bytesは不変とする。 |
| `src/code_structure_viz/artifacts/manifest.py` | diff Artifact contract、domain、adapter metadata、PlantUML contractをrequest domainで選ぶ。 |
| `src/code_structure_viz/artifacts/writer.py` | `sqlalchemy.diff.semantic.json` / `sqlalchemy.diff.puml` をclosed final pathとして追加し、diff stagingをdomain-awareにする。 |
| `src/code_structure_viz/artifacts/streams.py` | SQLAlchemy diff selectorをSQLAlchemy diff pathへ解決する。 |
| `schemas/semantic-v1.schema.json` | SQLAlchemy `semantic_diff` branchを追加する。 |
| `schemas/run-manifest-v1.schema.json` | `diff + domain: sqlalchemy` のadapter/artifact contractを追加する。 |
| `docs/contracts/cli-v1.md` | `diff --domain python|sqlalchemy` とSQLAlchemy diff pathsを記述する。 |
| `docs/contracts/sqlalchemy-semantic-v1.md` | SQLAlchemy diff projectionを追加する。 |
| `docs/contracts/sqlalchemy-plantuml-v2.md` | snapshot v2 semanticsを再利用するdiff projectionを追加する。 |
| `docs/contracts/run-manifest-v1.md` | SQLAlchemy diff manifestをvalid variantとして記述する。 |

### planned new

| path | 責務 |
| --- | --- |
| `src/code_structure_viz/adapters/sqlalchemy/diff.py` | SQLAlchemy side、exact-ID delta、canonical empty-side、impact union、entity countを所有する。 |
| `tests/unit/sqlalchemy/test_diff.py` | pure comparison、presence、impact、determinismを検証する。 |
| `tests/acceptance/sqlalchemy/test_diff_cli.py` | CLIからArtifact/manifest/stdout/exitまでの最小end-to-end matrixを検証する。 |

### existing — reuse unchanged

- `src/code_structure_viz/semantic/diff.py`
- `src/code_structure_viz/adapters/python/matcher.py`
- `src/code_structure_viz/adapters/python/diff_renderer.py`
- `src/code_structure_viz/adapters/sqlalchemy/model.py`
- `src/code_structure_viz/adapters/sqlalchemy/analyzer.py`
- `src/code_structure_viz/adapters/sqlalchemy/selection.py`
- `src/code_structure_viz/adapters/sqlalchemy/er_semantics.py`
- `src/code_structure_viz/source/*`
- `src/code_structure_viz/core/{budget,config,outcomes,diagnostics}.py`
- `pyproject.toml` / `uv.lock`

既存 test では `tests/unit/cli/test_parser.py`、`tests/unit/artifacts/test_{manifest,writer,streams}.py`、`tests/contracts/test_json_schemas.py`、`tests/contracts/test_scope_exclusions.py`、`tests/security/test_sqlalchemy_static_boundary.py` を必要箇所だけ拡張する。

## SQLAlchemy diff flow

```text
DiffApplication
  -> existing before/after SourceView + FileChangeSet
  -> SqlAlchemySnapshotAnalyzer
  -> SqlAlchemyTargetSelector.select(..., targets=())
  -> SQLAlchemy diff exact-ID comparison
  -> before/after relation union impact
  -> existing entity budget
  -> SQLAlchemy semantic JSON / PlantUML
  -> existing manifest / OutputTransaction / stdout-stderr
```

`targets=()` は Issue #6 selector の whole-selection contractを使う。diff CLIにtargetを追加しない。

### side mapping

| Issue #6 selection | diff side |
| --- | --- |
| `complete` | real snapshot |
| `not_applicable` | parent canonical empty-side |
| `incomplete / partial_safe` | analysis-failed |
| `incomplete / payload_unavailable` | analysis-failed |

diff sideが一つでもanalysis-failedなら comparisonを行わず、domain outcomeは `incomplete / payload_unavailable` とする。

## comparison model

`src/code_structure_viz/adapters/sqlalchemy/diff.py` は SQLAlchemy 固有の小さな immutable resultだけを持つ。shared Protocolやfactoryは追加しない。

semantic collectionsは Issue #6 と同じ `entities` / `members` / `relations` とする。

```text
delta:
  status: added | removed | modified
  id
  before: safe value | null
  after: safe value | null
```

algorithm:

1. before/after を既存 ID でmapする。
2. 片側だけのIDはadded/removed。
3. 両側に同じIDがあり、safe semantic valueが異なればmodified。
4. IDが異なる候補を再対応付けしない。rename/table move/member moveはremoved+added。
5. deltaはIDのUTF-8 byte orderで決定的に並べる。

safe semantic equalityは Issue #6 semantic JSON projectionを基準にし、tableの`mapping_sources`とrow/relationの`source`だけをprovenanceとして比較対象から除く。before/after value自体にはそのsafe provenanceを残す。raw expression/sourceを新たに参照しない。

side digestは Issue #6 のsafe `entities` / `members` / `relations` projectionをcanonical JSON化したSHA-256とする。canonical empty-sideのshape/digest ruleはparent contractをそのまま使う。

## impact

seedは次のunique table IDである。

- changed entity の table ID。
- changed member の `owner_id`。
- changed relation の `source_id` と、targetがinternal tableならそのtarget ID。

before/after のinternal relationをunionし、upstreamはreverse edge、downstreamはforward edgeを既存depthまでBFSする。削除relationのbefore edgeを残し、external/unknown targetはgraph nodeにしない。

`entity_count` は changed/impact に含まれるunique table ID数とし、既存 `EntityBudgetGate` に渡す。truncationは行わない。

## rendering / schema

### semantic JSON

rootは既存 Python diff と同じ semantic diff envelopeを使い、`domain: "sqlalchemy"` とする。

```text
type: semantic_diff
schema: code-structure-viz.semantic/v1
domain: sqlalchemy
document_kind: diff
status: complete
before / after
before_snapshot_sha256 / after_snapshot_sha256
file_change_set
semantic_change_set:
  entities
  members
  relations
  seeds
  impact
  matching: []
diagnostics
```

`matching` は本 Issue では常に空配列である。SQLAlchemy branchのdelta statusはadded/removed/modifiedだけを許可する。

### PlantUML

`code-structure-viz.plantuml/sqlalchemy/v2` のescape、table alias、row vocabulary、`build_er_view` のrelation/cardinality evidenceを再利用する。

- changed row/tableは `+` / `-` / `~` markerを付ける。
- removed itemはbefore valueをghostとして表示する。
- modified rowはsafe before/after差を表示する。
- impact-only tableはcontextとしてmarkerなしまたは固定context markerで表示する。
- before/after relation unionを描き、removed relationはbefore evidence、current relationはafter evidenceを使う。
- relation/cardinalityをdiff layerで再推論しない。

snapshot rendererの既存header/legend/outputは変更しない。diff pathだけ別skeletonをwriterでvalidateする。

## Artifact / manifest / streams

closed diff pathsを次にする。

```text
python      semantic-json -> python.diff.semantic.json
python      plantuml      -> python.diff.puml
sqlalchemy  semantic-json -> sqlalchemy.diff.semantic.json
sqlalchemy  plantuml      -> sqlalchemy.diff.puml
shared      file changes  -> file-changes.json
```

`ArtifactDescriptor.create_diff` と `OutputTransaction.stage_diff_payload` はdomainを明示的に受け取る形へ狭く拡張する。Python call siteも同APIへ移すが、path/media type/contentは変えない。

`DiffManifestBuilder` は request domain に応じて次だけを切り替える。

- domain
- adapter: `python-ast/1` または `sqlalchemy-ast/1`
- PlantUML contract
- diff Artifact path
- coverage value

endpoint/source/FileChangeSet/budget/run fingerprint/publication structureはexisting diff contractを維持する。

`StdoutEmitter` は selected domain + format からdiff pathを引く。`run-summary/v1` と `stdout-result/v1` schemaは既にSQLAlchemy domain/selectorを受理するため変更しない。

## failure / compatibility

- SQLAlchemy side incomplete、entity budget overrunは `payload_unavailable`。SQLAlchemy diff payloadをstageしない。
- changed-path overrun、endpoint/source/output/drift/internal failureはexisting run-fatal behaviorを使う。
- usage/stdout compatibilityはsource acquisition前に確定する。
- Python diff pathは既存 implementationを使い、shared registry/API変更によるpublic output差分を認めない。
- SQLAlchemy snapshot semantic JSON/PlantUML v2 output差分を認めない。
- migrationはN/A。persistent dataを持たず、既存Artifactを書き換えない。
- false positiveを避けるため、将来move matchingを追加したくなっても本Issue内では行わない。
