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
- canonical authority は exact commit `7951ddabc2e6a3d66edb77eada7c6c16923264f7` の accepted ADR と interview、および本 package の親 R/D/P である。

| 親 requirement | この Issue の所有範囲 |
| --- | --- |
| EPIC-REQ-001 | python domain の snapshot を end-to-end で提供する。 |
| EPIC-REQ-002 | static analysis、read-only Git、redaction、fail-closed を維持する。 |
| EPIC-REQ-003 | versioned semantic JSON、domain-specific PlantUML、manifest を生成する。 |
| EPIC-REQ-004 | complete/not_applicable/incomplete と exit contract を slice の範囲で実装する。 |

## 観測可能な要件

| ID | 観測面 | 要件 |
| --- | --- | --- |
| I01-REQ-001 | CLI と observable outcome | coding agent または人間が、対象 Python repository を実行せずに class 構造を semantic JSON と PlantUML で取得できる。 |
| I01-REQ-002 | source acquisition | target 無指定では ignore と scope 設定を適用した repository 内の全 `.py` source を snapshot 対象とする。 |
| I01-REQ-003 | semantic behavior | class identity は normalized module path と qualified class name の組である。nested class は outer class を含む qualified name を持つ。 |
| I01-REQ-004 | Artifact/output | semantic JSON は `code-structure-viz.semantic/v1` envelope、domain `python`、document kind `snapshot` を持つ。 |
| I01-REQ-005 | failure behavior | repository、Python version、config、output collision の core preflight failure は Artifact を公開せず exit 1 または 2 とする。 |
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

repository、Python version、config、output collision の core preflight failure は Artifact を公開せず exit 1 または 2 とする。
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

- repository、Python version、config、output collision の core preflight failure は Artifact を公開せず exit 1 または 2 とする。
- 一部 source の parse/read failure で安全な残りを表現できる場合は domain `incomplete`、成功した Artifact と diagnostic を保持し exit 3 とする。
- entity 数が既定 500 を超える場合は切り捨てず nonzero とし、`--max-entities` の明示 override を診断に記録する。

- `not_applicable` は target 不在、`incomplete` は target があるが安全に解析できない状態であり、相互に変換しない。
- failure diagnostic は stable code、severity、domain、safe repository-relative location、recoverability、human-readable message を持つ。source body と secret は含めない。
- stop condition: Python snapshot の CLI→source selection→AST analysis→semantic JSON/PlantUML→manifest→acceptance test が単独で成立する前に、Git diff、SQLAlchemy row model、Next bridge の実装へ進まない。

## 受け入れ条件

| ID | 観測可能な完了条件 | acceptance test |
| --- | --- | --- |
| I01-AC-001 | whole repository の Python class/member/relation を JSON と PlantUML へ決定的に出力する。 | I01-AT-001 |
| I01-AC-002 | path/module/class target と upstream/downstream depth が frontier を正しく制限する。 | I01-AT-002 |
| I01-AC-003 | syntax error と unreadable file を削除扱いせず incomplete と diagnostic にする。 | I01-AT-003 |
| I01-AC-004 | fixture の import side effect、secret literal、absolute path が実行・出力されない。 | I01-AT-004 |
| I01-AC-005 | 同一入力の二回実行で semantic/PlantUML bytes と manifest artifact SHA が一致する。 | I01-AT-005 |
| I01-AC-006 | 501 entity は無切り捨て failure、明示 600 override は成功する。 | I01-AT-006 |

- **I01-AC-001〜I01-AC-006 がすべて満たされ、planned test command が clean checkout で成功すること。**
- Requirement、Design、Plan の trace table が一致し、unresolved acceptance gap がないこと。
- release boundary: internal foundation を兼ねる最初の利用可能 slice。ただし release milestone とはせず、Python diff 完了後に Python domain preview とする。

## 制約・前提

- initial platform は macOS と Linux。native Windows は対象外。
- Core/CLI/Git/manifest/Python/SQLAlchemy は Python 3.12 以上。Next adapter 利用時だけ Node.js 22 LTS 以上。
- Git 2.39 以上。CI は minimum supported と repository で明示更新する latest stable lane を実行する。
- direct/indirect dependency は lockfile で exact resolve し、license inventory と offline runtime test を持つ。runtime に network access を要求しない。
- `pyclassuml` と `tree-git-diff` への runtime/package/CLI dependency を持たない。legacy code の直接 copy は license/provenance 未確認のまま行わず、初期実装は contract/test evidence を基に repository-owned code として再実装する。
- product HTML report generation、HTML command、Tailscale publication は本 Issue の製品 scope 外。`explanation.html` は specification Artifact である。
