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
- canonical authority は stable scope ID、本 Issue と親 scope の repository-relative R/D/P path、accepted ADR、interview、latest user decisions である。採用・実装開始時に HEAD と configured upstream を再検証し、current commit SHA を本文の自己 authority として固定しない。

| 親 requirement | この Issue の所有範囲 |
| --- | --- |
| EPIC-REQ-001 | python domain の snapshot を end-to-end で提供する。 |
| EPIC-REQ-002 | static analysis、read-only Git、safe endpoint/source、redaction、fail-closed を維持する。 |
| EPIC-REQ-003 | python の identity/member/relation/matching semantics を domain ownership のまま保つ。 |
| EPIC-REQ-004 | per-domain versioned semantic JSON、domain-specific PlantUML、`run-manifest/v1` descriptor、determinism/no-overwrite を提供する。 |
| EPIC-REQ-005 | domain status、0/1/2/3/130 exitとdomain-local entity budgetを実装・検証する。run-level changed-path budgetはdiff専用であり、本snapshot sliceでは適用しない。 |
| EPIC-REQ-009 | closed stdout selector、exact-byte copy、unavailable result、stderr diagnostic、usage no-publicationをsliceのpublic CLI contractとして実装・検証する。 |

## 観測可能な要件

| ID | 観測面 | 要件 |
| --- | --- | --- |
| I01-REQ-001 | CLI と observable outcome | coding agent または人間が、対象 Python repository を実行せずに class 構造を semantic JSON と PlantUML で取得できる。 |
| I01-REQ-002 | source acquisition | target 無指定では ignore と scope 設定を適用した repository 内の全 `.py` source を snapshot 対象とする。 |
| I01-REQ-003 | semantic behavior | class identity は normalized module path と qualified class name の組である。nested class は outer class を含む qualified name を持つ。 |
| I01-REQ-004 | Artifact/output | semantic JSON は `code-structure-viz.semantic/v1` envelope、domain `python`、document kind `snapshot` を持つ。 |
| I01-REQ-005 | failure behavior | repository、Python version、config、output collisionのcore preflight failureはArtifactを公開せずexit 1または2とする。entity-per-diagram budget超過はdomain `incomplete`、exit 3で、affected semantic JSON/PlantUMLを公開せずsafe run manifestへcountとdiagnosticを残す。implicit changed-path gateはdiff専用でありsnapshotでは実行せず、snapshotへの`--from`/`--to`/`--pr-target`/`--max-changed-paths`指定はusage error、exit 2とする。 |
| I01-REQ-006 | safety/determinism | 解析対象 module、plugin、migration、build script、application entry point を import または実行しない。 同じ source bytes、endpoint、resolved config、adapter version では entity・member・relation・diagnostic・Artifact path の順序と SHA-256 が決定的になる。 |
| I01-REQ-007 | stdout contract | `--stdout SELECTOR`を高々1回のclosed selectorとして検証し、available exact bytes、unavailable result、selectorなしsummary、stderr diagnostics、exit 2 no-publicationを提供する。 |

### I01-REQ-001

coding agent または人間が、対象 Python repository を実行せずに class 構造を semantic JSON と PlantUML で取得できる。
### I01-REQ-002

target 無指定では ignore と scope 設定を適用した repository 内の全 `.py` source を snapshot 対象とする。
### I01-REQ-003

class identity は normalized module path と qualified class name の組である。nested class は outer class を含む qualified name を持つ。
### I01-REQ-004

semantic JSON は `code-structure-viz.semantic/v1` envelope、domain `python`、document kind `snapshot` を持つ。
### I01-REQ-005

repository、Python version、config、output collisionのcore preflight failureはArtifactを公開せずexit 1または2とする。entity-per-diagram budget超過はdomain `incomplete`、exit 3で、affected semantic JSON/PlantUMLを公開せずsafe run manifestへcountとdiagnosticを残す。implicit changed-path gateはdiff専用でありsnapshotでは実行せず、snapshotへの`--from`/`--to`/`--pr-target`/`--max-changed-paths`指定はusage error、exit 2とする。
### I01-REQ-006

解析対象 module、plugin、migration、build script、application entry point を import または実行しない。 同じ source bytes、endpoint、resolved config、adapter version では entity・member・relation・diagnostic・Artifact path の順序と SHA-256 が決定的になる。


### I01-REQ-007

`--stdout SELECTOR`を高々1回のclosed selectorとして検証し、available exact bytes、unavailable result、selectorなしsummary、stderr diagnostics、exit 2 no-publicationを提供する。

### CLI examples

```bash
code-structure-viz snapshot --repo . --domain python --output-dir /tmp/csv-python-snapshot
code-structure-viz snapshot --repo . --domain python --target path:src/domain/order.py --upstream-depth 1 --downstream-depth 1 --output-dir /tmp/csv-order
code-structure-viz snapshot --repo . --domain python --target module:domain.order --target class:domain.order.Order --format semantic-json --output-dir /tmp/csv-order-json
code-structure-viz snapshot --repo . --domain python --format semantic-json --stdout python:semantic-json --output-dir /tmp/csv-stdout
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
{"type":"stdout_result","schema":"code-structure-viz.stdout-result/v1","selector":"python:semantic-json","availability":false,"domain_status":"not_applicable","stable_reason":"domain_not_applicable","artifact":null}
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
- `--stdout SELECTOR` は高々1回のclosed grammarであり、exact-byte/unavailable-result/no-selector-summary/usage-error contractは下記sectionを正本とする。

- 解析対象 module、plugin、migration、build script、application entry point を import または実行しない。
- Git repository は read-only とし、fetch、checkout、reset、stash、clean、commit、ref 更新を実行しない。すべての Git subprocess で lazy fetch、external diff、textconv、color を無効化する。
- Artifact には repository-relative path、symbol、type、signature、relation、line range だけを許可し、source body、comment、literal、secret らしい値、absolute path を含めない。
- 同じ source bytes、endpoint、resolved config、adapter version では entity・member・relation・diagnostic・Artifact path の順序と SHA-256 が決定的になる。

## 失敗・境界条件

- repository、Python version、config、output collisionのcore preflight failureはArtifactを公開せずexit 1または2とする。
- 一部sourceのparse/read failureをfile単位で隔離でき、安全subset、coverage frontier、safe diagnostic、redaction、entity-budget passを証明できる場合は`incomplete_kind: partial_safe`としてincomplete semantic JSON、PlantUML、manifestを公開しexit 3とする。safe subsetがないglobal acquisition/security/unsafe-path failureは`payload_unavailable`としてaffected JSON/PlantUMLを公開せずsafe manifestだけを公開しexit 3とする。どちらもtarget不在へ変換しない。
- entity-per-diagram budgetはdomain-local gateでdefault 500。overrideなしで超過したdomainは`incomplete`、exit 3とし、切り捨てず、そのdomainのsemantic JSONとPlantUMLを公開しない。valid core runではsafe run manifestを公開し、requested/resolved limit、actual count、diagnosticを記録する。all-domainではsuccessful sibling Artifactを保持する。positive integerの`--max-entities N`は通常公開を許可し、同じ値とcountをmanifestへ記録する。invalid overrideはexit 2。
- `not_applicable`はPython target evidence不在、`incomplete`はtarget evidenceがあるが安全に完了できない状態であり、相互に変換しない。
- diagnosticはstable code、severity、domain、safe repository-relative location、recoverability、human-readable messageを持ち、source body、secret、absolute pathを含めない。
- stop condition: Python snapshotのCLI→source selection→AST analysis→semantic JSON/PlantUML→manifest→acceptance testが単独で成立する前にGit diff、SQLAlchemy row model、Next bridgeへ進まない。

## 受け入れ条件

| ID | 観測可能な完了条件 | acceptance test |
| --- | --- | --- |
| I01-AC-001 | whole repositoryのPython class/member/relationをJSONとPlantUMLへ決定的に出力する。 | I01-AT-001 |
| I01-AC-002 | path/module/class targetとupstream/downstream depthがfrontierを正しく制限する。 | I01-AT-002 |
| I01-AC-003 | isolated syntax/read failureは`partial_safe` JSON+PlantUML+manifest、safe subset不在またはglobal/unsafe failureは`payload_unavailable` manifest-onlyとし、どちらもtarget不在や削除へ変換せずexit 3にする。 | I01-AT-003 |
| I01-AC-004 | fixtureのimport side effect、secret literal、absolute pathが実行・出力されない。 | I01-AT-004 |
| I01-AC-005 | 同一入力の二回実行でsemantic/PlantUML bytesとmanifest Artifact SHAが一致する。 | I01-AT-005 |
| I01-AC-006 | 501 entitiesはdomain `incomplete_kind: payload_unavailable`・exit 3・affected JSON/PlantUMLなし・manifestにcountを記録し、明示600 overrideは成功してrequested/resolved/countを記録する。snapshotへの`--from`/`--to`/`--pr-target`/`--max-changed-paths`はsilent no-opにせずexit 2・Artifactなしとする。 | I01-AT-006 |
| I01-AC-007 | stdout selectorのvalid/invalid/duplicate/domain/format、exact-byte、not_applicable/payload_unavailable/fatal/interrupt result、selectorなしsummaryをtable-drivenに満たす。 | I01-AT-007 |

- **I01-AC-001〜I01-AC-007 がすべて満たされ、planned test command が clean checkout で成功すること。**
- Requirement、Design、Plan の trace table が一致し、unresolved acceptance gap がないこと。
- release boundary: internal foundationを兼ねる最初の利用可能slice。ただしrelease milestoneとはせず、Python diff完了後にPython domain previewとする。

## 制約・前提

- initial platform は macOS と Linux。native Windows は対象外。
- Core/CLI/Git/manifest/Python/SQLAlchemy は Python 3.12 以上。Next adapter 利用時だけ Node.js 22 LTS 以上。
- Git 2.39 以上。CI は minimum supported と repository で明示更新する latest stable lane を実行する。
- direct/indirect dependency は lockfile で exact resolve し、license inventory と offline runtime test を持つ。runtime に network access を要求しない。
- `pyclassuml` と `tree-git-diff` への runtime/package/CLI dependency を持たない。legacy code の直接 copy は license/provenance 未確認のまま行わず、初期実装は contract/test evidence を基に repository-owned code として再実装する。
- product HTML report generation、HTML command、Tailscale publication は本 Issue の製品 scope 外。`explanation.html` は specification Artifact である。
