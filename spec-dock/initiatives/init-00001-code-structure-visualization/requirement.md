---
種別: 要件定義書（Initiative）
ID: "init-00001"
タイトル: "Visualize Code Structure Changes"
関連GitHub: ["#1"]
状態: "draft"
最終更新: "2026-08-24"
---

# init-00001 Visualize Code Structure Changes — 要件定義

詳細: [Requirement Guide](../../docs/authoring/requirement.md)

## 目的

CodeStructureViz を、coding agent が source structure と変更影響を安全かつ再利用可能な Artifact として取得する独立 CLI product として成立させる。agent 自身の機械的理解と、人間へ説明するための domain-specific 図の両方を一つの contract で提供する。

本 Initiative は Python class、SQLAlchemy declarative ER、Next.js/React component の三 domain を一つの投資境界に含める。snapshot と temporal diff は別 use case とし、diff は Git text diff ではなく before/after semantic snapshot を正本とする。

## 背景

- code review の入口として構造図は有用だが、既存の `pyclassuml` と `tree-git-diff` は個別目的の legacy reference であり、将来 product の runtime boundary ではない。
- Git hunk、rename/copy status、runtime reflection だけでは semantic change、削除 entity の relation、partial failure を正確に扱えない。
- 主利用者は Codex 等の coding agent であり、machine-readable schema、deterministic output、failure provenance、safe redaction が必要である。
- canonical authority は stable scope ID、repository-relative canonical R/D/P path、accepted ADR、interview、latest user decisions で識別する。production implementation は未着手であり、実装開始時に作業 branch の HEAD と configured upstream を再検証してから domain presence、budget、aggregation、endpoint、redaction、traceability contract を適用する。canonical 文書自身へ current commit SHA を固定しない。

## 観測可能な要件

| ID | 観測面 | Initiative requirement |
| --- | --- | --- |
| INIT-REQ-001 | 三 domain の利用者成果 | coding agent と人間が Python class、SQLAlchemy ER、Next.js/React component の snapshot と temporal diff を静的に取得できる。 |
| INIT-REQ-002 | 安全な独立 product | CodeStructureViz は legacy tool から独立し、target application と mutable Git operation を実行しない。 |
| INIT-REQ-003 | semantic diff | diff は before/after immutable semantic snapshot を正本とし、FileChangeSet と SemanticChangeSet を分離する。 |
| INIT-REQ-004 | agent-first output | versioned semantic JSON、domain-specific PlantUML、provenance manifest を生成し、redaction と SHA-256 を保証する。 |
| INIT-REQ-005 | failure/status | not_applicable と incomplete を区別し、partial success Artifact を保持して 0/1/2/3/130 exit contract を提供する。 |
| INIT-REQ-006 | platform/operability | macOS/Linux、Python 3.12+、Git 2.39+、Next 利用時 Node 22 LTS+、minimum/latest CI、offline runtime を満たす。 |
| INIT-REQ-007 | delivery milestones | Python+SQLAlchemy 完了を intermediate release、Next と all-domain orchestration 完了を Initiative completion とする。 |
| INIT-REQ-008 | scope exclusion | product HTML report/command/publication、runtime tree、DB/Alembic execution、native Windows、public plugin ABI、legacy CLI compatibility を対象外とする。 |
| INIT-REQ-009 | stdout contract | `--stdout SELECTOR` のclosed grammar、exact-byte copy、unavailable result、stream separation、usage failureを一意にする。 |

### outcome boundaries

- **INIT-REQ-001**: 一つの CLI product として三 domain を扱い、domain ごとの identity/member/relation/matching semantics は失わない。
- **INIT-REQ-003**: snapshot は whole structure または targeted dependency context を所有し、diff diagram は changed seed と configured context だけを所有する。
- **INIT-REQ-004**: JSON と PlantUML は selectable、format 未指定は両方。manifest は endpoint、fingerprint、version、coverage、diagnostic、relative path、SHA-256 を持つ。
- **INIT-REQ-005**: empty/unknown/error を同一視しない。diff の片側 domain 不在は canonical empty-side と比較する complete added/removed、両側不在は not_applicable、解析失敗は incomplete とし、agent が status、publication、exit code から次 action を決定できる。
- **INIT-REQ-004**: domain 無指定でも semantic payload は domain ごとに保ち、aggregate は `code-structure-viz.run-manifest/v1` だけとする。
- **INIT-REQ-005**: `incomplete` は `partial_safe` と `payload_unavailable` を区別し、safe subsetだけを公開する。
- **INIT-REQ-009**: stdout selectorはexactly one optional closed selectorであり、永続output-dir、diagnostic stderr、既存exit contractを変更しない。

## スコープ

### 対象

- Python 3.12+ core/CLI/Git/manifest/Python/SQLAlchemy implementation。
- repository-owned TypeScript/Node Next adapter と versioned JSON bridge。
- snapshot/diff、safe source acquisition、domain analysis、semantic JSON、PlantUML、diagnostic、manifest、acceptance/CI/packaging。
- macOS/Linux local repository analysis。Git 2.39+。Node は Next target の解析時だけ必要。
- explicit CLI/config behavior、budgets、redaction、accessibility-aware visual vocabulary。

### 対象外

- product feature としての HTML report generation、HTML command、Tailscale/public publication。将来の別 Epic 候補に留める。
- DB connection、Alembic/runtime metadata、migration execution、target application/module/plugin/build script 実行。
- Next runtime component tree、non-literal dynamic behavior の推測、browser DOM/bundle analysis。
- native Windows、public third-party plugin ABI、remote execution、legacy CLI compatibility。
- `pyclassuml` と `tree-git-diff` への runtime/package/CLI dependency。

### specification HTML との分離

`explanation.html` は R/D/P を理解するための standalone specification Artifact である。製品が生成・配信する HTML ではなく、製品 CLI/schema/runtime scope に含めない。

## 失敗・境界条件

- implicit base を安全に解決できない場合、initial commit へ fallback せず fail closed。auto fetch しない。
- working tree は必要 source を repository 外へ freeze し、開始/終了 fingerprint drift では success Artifact を公開しない。`--to working-tree` だけを指定した場合は開始時 HEAD を implicit-base anchor とする。
- U path は metadata-only `FileChangeSet` evidence に残せるが affected semantic analysis は incomplete。raw hunk body は保持・公開しない。
- source body、comment、literal、secret、absolute path を Artifact に含めない。SQL default literal は parser boundary で redact し、initial release に `--include-literals` を設けない。
- output directory は必須。既存 file を上書きせず、target repository へ default write しない。

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

### budget outcome contract

| budget | gate / default | override なしの超過 | publication | valid override |
| --- | --- | --- | --- | --- |
| implicit changed paths | domain comparison 前の run-level admission gate。default 1,000。implicit comparison の actual changed-path count に適用する。 | fatal analysis/environment、exit 1。domain analysis を開始しない。safe machine-readable diagnostic を stderr に出す。 | semantic JSON、PlantUML、final run manifest を一切公開せず、staging を破棄する。 | positive integer の `--max-changed-paths N` で通常処理を許可する。公開 manifest に requested value、resolved value、actual changed-path count、config source を記録する。 |
| entities per diagram | domain semantic result 生成後かつ renderer/publication 前の domain-local gate。default 500。 | affected domain を `incomplete_kind: payload_unavailable` とし、単一 domain run も all-domain run も exit 3。切り捨てない。 | affected domain の semantic JSON と PlantUML は公開しない。successful sibling Artifact と aggregate run manifest は保持し、diagnostic、requested/resolved limit、actual entity count を記録する。 | positive integer の `--max-entities N` で通常公開を許可し、manifest に requested value、resolved value、actual entity count、config source を記録する。 |

override の zero、negative、non-integer、型不正、unknown config key は usage/config error、exit 2 であり、Artifact を公開しない。depth の default は upstream/downstream 各 1 で、depth は graph context を制限するだけで budget 超過の truncation 手段にはしない。

### FileChangeSet hunk safety contract

`FileChangeSet` の hunk evidence は metadata だけである。各 hunk は repository-relative old/new path、file status、old/new start line、old/new line count、同一 file 内の ordinal、および content-independent な `hunk_id` を持てる。`hunk_id` はこれら metadata の canonical tuple から SHA-256 で生成し、source bytes を入力にしない。

raw patch line、context line、added/deleted line、source body、comment、literal、secret、absolute path を memory-owned model、semantic JSON、PlantUML、manifest、diagnostic、logへ保持または公開してはならない。Git diff streamを range extraction に読む実装は、metadata を抽出した時点で本文を破棄し、serializer へ本文型を渡さない。negative acceptance test は secret-like patch、comment、literal、absolute temporary path が全 output channel に存在しないことを確認する。

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

## 受け入れ条件

| ID | Initiative completion evidence | trace |
| --- | --- | --- |
| INIT-AC-001 | Python snapshot/diff が exact semantic and safety contract で受け入れられる。 | ISSUE-01, ISSUE-02 |
| INIT-AC-002 | SQLAlchemy snapshot/diff と row-level ghost/before-after contract が受け入れられる。 | ISSUE-03, ISSUE-04 |
| INIT-AC-003 | ISSUE-04 完了時に Python+SQLAlchemy intermediate release gate が通る。 | ISSUE-04 / I04-AT-001〜006 |
| INIT-AC-004 | Next snapshot/diff が first-party TypeScript adapter と optional Node contract で受け入れられる。 | ISSUE-05, ISSUE-06 |
| INIT-AC-005 | domain presence truth table、internal empty-side provenance、partial success retention、`code-structure-viz.run-manifest/v1` のみの aggregate、0/3 exit contract が受け入れられる。 | I02/I04/I06/I07 domain-presence and aggregation tests |
| INIT-AC-006 | read-only Git、start-HEAD working-tree anchor、metadata-only hunks、static execution trap、redaction、determinism、run-level/domain-local budget publication matrix が全 domain で通る。 | I01/I02/I03/I04/I05/I06/I07 security/negative/budget tests |
| INIT-AC-007 | minimum/latest CI、lockfiles、license inventory、offline runtime test が通る。 | I07-AT-006, I07-AT-007 |
| INIT-AC-008 | 製品 R/D/P と CLI に HTML runtime output を導入していない。 | EPIC-AC-008 と scope scan |
| INIT-AC-009 | stdout selector grammar、exact-byte output、unavailable `stdout_result/v1`、selectorなしsummary、exit 2 no-publication matrixが全7 sliceで受け入れられる。 | I01/I02/I03/I04/I05/I06/I07 stdout acceptance |

Initiative complete は `INIT-AC-001`〜`INIT-AC-009` がすべて成立し、exactly one Epic の completion report がこれを確認した時点とする。Next 未完の Python+SQLAlchemy release は intermediate milestone であり Initiative completion ではない。

## 制約・前提

- authority order: accepted ADR、interview、latest user scope、verified repository facts。解消不能な material question だけ `open-questions.md` に置く。
- dependency は exact lockfile、license review、offline runtime を必要とする。optional Next dependency は core install/runtime から分離する。
- CI は minimum supported version と repository-managed latest stable version を明示 matrix で実行する。floating `latest` label だけを再現性根拠にしない。
- Git repository は read-only。fetch/checkout/reset/stash/clean/ref/index/worktree mutation を禁止する。
- diagram は code/test review の代替ではなく、source provenance と coverage を持つ review entry point である。
- existing metadata `.meta.json` は package から直接変更しない。adoption は SpecDock commands と whole-file copy/import gate に従う。
