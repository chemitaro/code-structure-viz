---
種別: 要件定義書（Issue）
ID: "iss-00004"
タイトル: "Generate Python Structure Snapshots"
関連GitHub: ["#4"]
package_sequence_key: "ISSUE-01"
状態: "draft"
最終更新: "2026-08-24"
親: ["epic-00002", "init-00001"]
---

# iss-00004 Generate Python Structure Snapshots — 要件定義

詳細: [Requirement Guide](../../../../../../docs/authoring/requirement.md)

## 目的

coding agent または人間が、対象 Python repository を実行せずに class 構造を semantic JSON と PlantUML で取得できる。

利用者 story: coding agent として、変更前の構造や調査対象 class の周辺を機械可読かつ図示可能な形で把握し、source 全文を外部 Artifact へ複製せずに実装判断へ使いたい。

この Issue は技術 layer の完成ではなく、利用者が command を実行して source acquisition、domain analysis、semantic JSON、PlantUML、diagnostic、acceptance evidence まで確認できる一つの vertical outcome を所有する。

## 背景

- 親 Initiative は三 domain の code structure を静的に可視化する。
- 親 Epic は安全な Git comparison と agent-first Artifact contract を一つの product outcome として統合する。
- この slice の declared dependency は なし。依存 Issue の public contract だけを利用し、unfinished sibling の内部実装には依存しない。
- canonical authority は exact verified current commit `867ee6929283dfc84711bce245b784d2b8e3e9e6` の accepted ADR、interview、親 R/D/P と本 Issue の current canonical textである。

| 親 requirement | この Issue の所有範囲 |
| --- | --- |
| EPIC-REQ-001 | python domain の snapshot を end-to-end で提供する。 |
| EPIC-REQ-002 | static analysis、read-only Git、safe endpoint/source、redaction、fail-closed を維持する。 |
| EPIC-REQ-003 | python の identity/member/relation/matching semantics を domain ownership のまま保つ。 |
| EPIC-REQ-004 | per-domain versioned semantic JSON、domain-specific PlantUML、`run-manifest/v1` descriptor、determinism/no-overwrite を提供する。 |
| EPIC-REQ-005 | domain status、0/1/2/3/130 exitとdomain-local entity budgetを実装・検証する。run-level changed-path budgetはdiff専用であり、本snapshot sliceでは適用しない。 |

## 観測可能な要件

| ID | 観測面 | 要件 |
| --- | --- | --- |
| I01-REQ-001 | CLI と observable outcome | coding agent または人間が、対象 Python repository を実行せずに class 構造を semantic JSON と PlantUML で取得できる。 |
| I01-REQ-002 | source acquisition | target 無指定では ignore と scope 設定を適用した repository 内の全 `.py` source を snapshot 対象とする。 |
| I01-REQ-003 | semantic behavior | class identity は normalized module path と qualified class name の組である。nested class は outer class を含む qualified name を持つ。 |
| I01-REQ-004 | Artifact/output | semantic JSON は `code-structure-viz.semantic/v1` envelope、domain `python`、document kind `snapshot` を持つ。 |
| I01-REQ-005 | failure behavior | repository、Python version、config、output collisionのcore preflight failureはArtifactを公開せずexit 1または2とする。entity-per-diagram budget超過はdomain `incomplete`、exit 3で、affected semantic JSON/PlantUMLを公開せずsafe run manifestへcountとdiagnosticを残す。implicit changed-path gateはdiff専用でありsnapshotでは実行せず、snapshotへの`--max-changed-paths`指定はusage error、exit 2とする。 |
| I01-REQ-006 | safety/determinism | 解析対象 module、plugin、migration、build script、application entry point を import または実行しない。 同じ source bytes、endpoint、resolved config、adapter version では entity・member・relation・diagnostic・Artifact path の順序と SHA-256 が決定的になる。 |

### I01-REQ-001

coding agent または人間が、対象 Python repository を実行せずに class 構造を semantic JSON と PlantUML で取得できる。
### I01-REQ-002

target 無指定では ignore と scope 設定を適用した repository 内の全 `.py` source を snapshot 対象とする。
### I01-REQ-003

class identity は normalized module path と qualified class name の組である。nested class は outer class を含む qualified name を持つ。
### I01-REQ-004

semantic JSON は `code-structure-viz.semantic/v1` envelope、domain `python`、document kind `snapshot` を持つ。
### I01-REQ-005

repository、Python version、config、output collisionのcore preflight failureはArtifactを公開せずexit 1または2とする。entity-per-diagram budget超過はdomain `incomplete`、exit 3で、affected semantic JSON/PlantUMLを公開せずsafe run manifestへcountとdiagnosticを残す。implicit changed-path gateはdiff専用でありsnapshotでは実行せず、snapshotへの`--max-changed-paths`指定はusage error、exit 2とする。
### I01-REQ-006

解析対象 module、plugin、migration、build script、application entry point を import または実行しない。 同じ source bytes、endpoint、resolved config、adapter version では entity・member・relation・diagnostic・Artifact path の順序と SHA-256 が決定的になる。


### CLI examples

```bash
code-structure-viz snapshot --repo . --domain python --output-dir /tmp/csv-python-snapshot
code-structure-viz snapshot --repo . --domain python --target path:src/domain/order.py --upstream-depth 1 --downstream-depth 1 --output-dir /tmp/csv-order
code-structure-viz snapshot --repo . --domain python --target module:domain.order --target class:domain.order.Order --format semantic-json --output-dir /tmp/csv-order-json
```

### source acquisition contract

- target 無指定では ignore と scope 設定を適用した repository 内の全 `.py` source を snapshot 対象とする。
- `path:`、`module:`、`class:` target 指定では、解決した seed から typed relation と import relation を用いて upstream/downstream を別々に探索する。
- Python 3.12 以上の syntax を `ast` で解析し、target application を import しない。parse failure は削除や空構造へ変換せず diagnostic と coverage に残す。
- symlink が repository 外へ解決する場合は追跡せず、安全な diagnostic を返す。binary、generated、vendor path は設定された ignore だけで除外し、暗黙の推測を行わない。

### semantic contract

- class identity は normalized module path と qualified class name の組である。nested class は outer class を含む qualified name を持つ。
- entity は class、member は field、method、property、decorator metadata、relation は inheritance、composition、typed dependency、import dependency を domain-owned kind として保持する。
- type annotation と signature は正規化して保持するが、default literal、function body、docstring、comment は保持しない。
- whole-repository snapshot は全構造を所有し、targeted snapshot は seed と traversal context、coverage frontier を明示する。

### output contract

- semantic JSON は `code-structure-viz.semantic/v1` envelope、domain `python`、document kind `snapshot` を持つ。
- PlantUML は class と field/method を表示し、relation kind を arrow と日本語 legend で区別する。
- run manifest は requested target、resolved scope、resolved config、tool/contract/adapter version、coverage、diagnostic、Artifact relative path、SHA-256 を記録する。
- 対象 Python source がない場合は domain status `not_applicable` とし、空の class diagram を成功 Artifact として捏造しない。

## スコープ

### 対象

- `python` domain の `snapshot` use case を CLI input から acceptance test まで届ける。
- common CLI/config/diagnostic/Artifact contract は、この slice に必要な範囲だけ導入または拡張する。
- repository-owned implementation、tests、fixtures、documentation、lockfile、CI lane を含む。

### 対象外

- temporal diff、Git endpoint 解決、moved matching
- SQLAlchemy 固有 ER semantics、Next.js component semantics
- Python module の import 実行、runtime reflection、bytecode analysis
- 製品機能としての HTML report generation

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

- repository、Python version、config、output collisionのcore preflight failureはArtifactを公開せずexit 1または2とする。
- 一部sourceのparse/read failureで安全なpartial snapshotを表現できる場合はdomain `incomplete`、明示的にincompleteであるsemantic Artifactとdiagnosticを保持しexit 3とする。target不在へ変換しない。
- entity-per-diagram budgetはdomain-local gateでdefault 500。overrideなしで超過したdomainは`incomplete`、exit 3とし、切り捨てず、そのdomainのsemantic JSONとPlantUMLを公開しない。valid core runではsafe run manifestを公開し、requested/resolved limit、actual count、diagnosticを記録する。all-domainではsuccessful sibling Artifactを保持する。positive integerの`--max-entities N`は通常公開を許可し、同じ値とcountをmanifestへ記録する。invalid overrideはexit 2。
- `not_applicable`はPython target evidence不在、`incomplete`はtarget evidenceがあるが安全に完了できない状態であり、相互に変換しない。
- diagnosticはstable code、severity、domain、safe repository-relative location、recoverability、human-readable messageを持ち、source body、secret、absolute pathを含めない。
- stop condition: Python snapshotのCLI→source selection→AST analysis→semantic JSON/PlantUML→manifest→acceptance testが単独で成立する前にGit diff、SQLAlchemy row model、Next bridgeへ進まない。

## 受け入れ条件

| ID | 観測可能な完了条件 | acceptance test |
| --- | --- | --- |
| I01-AC-001 | whole repositoryのPython class/member/relationをJSONとPlantUMLへ決定的に出力する。 | I01-AT-001 |
| I01-AC-002 | path/module/class targetとupstream/downstream depthがfrontierを正しく制限する。 | I01-AT-002 |
| I01-AC-003 | syntax errorとunreadable fileをtarget不在や削除扱いせずincompleteとdiagnosticにする。 | I01-AT-003 |
| I01-AC-004 | fixtureのimport side effect、secret literal、absolute pathが実行・出力されない。 | I01-AT-004 |
| I01-AC-005 | 同一入力の二回実行でsemantic/PlantUML bytesとmanifest Artifact SHAが一致する。 | I01-AT-005 |
| I01-AC-006 | 501 entitiesはdomain incomplete・exit 3・affected JSON/PlantUMLなし・manifestにcountを記録し、明示600 overrideは成功してrequested/resolved/countを記録する。snapshotへの`--max-changed-paths`はsilent no-opにせずexit 2・Artifactなしとする。 | I01-AT-006 |

- **I01-AC-001〜I01-AC-006 がすべて満たされ、planned test command が clean checkout で成功すること。**
- Requirement、Design、Plan の trace table が一致し、unresolved acceptance gap がないこと。
- release boundary: internal foundationを兼ねる最初の利用可能slice。ただしrelease milestoneとはせず、Python diff完了後にPython domain previewとする。

## 制約・前提

- initial platform は macOS と Linux。native Windows は対象外。
- Core/CLI/Git/manifest/Python/SQLAlchemy は Python 3.12 以上。Next adapter 利用時だけ Node.js 22 LTS 以上。
- Git 2.39 以上。CI は minimum supported と repository で明示更新する latest stable lane を実行する。
- direct/indirect dependency は lockfile で exact resolve し、license inventory と offline runtime test を持つ。runtime に network access を要求しない。
- `pyclassuml` と `tree-git-diff` への runtime/package/CLI dependency を持たない。legacy code の直接 copy は license/provenance 未確認のまま行わず、初期実装は contract/test evidence を基に repository-owned code として再実装する。
- product HTML report generation、HTML command、Tailscale publication は本 Issue の製品 scope 外。`explanation.html` は specification Artifact である。
