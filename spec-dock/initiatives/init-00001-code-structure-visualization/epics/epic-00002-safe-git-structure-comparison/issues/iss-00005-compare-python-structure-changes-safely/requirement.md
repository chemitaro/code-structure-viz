---
種別: 要件定義書（Issue）
ID: "iss-00005"
タイトル: "Compare Python Structure Changes Safely"
関連GitHub: ["#5"]
package_sequence_key: "ISSUE-02"
状態: "draft"
最終更新: "2026-08-24"
親: ["epic-00002", "init-00001"]
---

# iss-00005 Compare Python Structure Changes Safely — 要件定義

詳細: [Requirement Guide](../../../../../../docs/authoring/requirement.md)

## 目的

coding agent が named endpoint で before/after Python semantic snapshot を安全に固定し、意味のある class/member/relation change と影響 context だけを比較できる。

利用者 story: coding agent として、Git hunk の見かけではなく before/after の Python semantics を基準に、変更 class と upstream/downstream impact を説明したい。

この Issue は技術 layer の完成ではなく、利用者が command を実行して source acquisition、domain analysis、semantic JSON、PlantUML、diagnostic、acceptance evidence まで確認できる一つの vertical outcome を所有する。

## 背景

- 親 Initiative は三 domain の code structure を静的に可視化する。
- 親 Epic は安全な Git comparison と agent-first Artifact contract を一つの product outcome として統合する。
- この slice の declared dependency は ISSUE-01。依存 Issue の public contract だけを利用し、unfinished sibling の内部実装には依存しない。
- canonical authority は stable scope ID、本 Issue と親 scope の repository-relative R/D/P path、accepted ADR、interview、latest user decisions である。採用・実装開始時に HEAD と configured upstream を再検証し、current commit SHA を本文の自己 authority として固定しない。

| 親 requirement | この Issue の所有範囲 |
| --- | --- |
| EPIC-REQ-001 | python domain の diff を end-to-end で提供する。 |
| EPIC-REQ-002 | static analysis、read-only Git、safe endpoint/source、redaction、fail-closed を維持する。 |
| EPIC-REQ-003 | python の identity/member/relation/matching semantics を domain ownership のまま保つ。 |
| EPIC-REQ-004 | per-domain versioned semantic JSON、domain-specific PlantUML、`run-manifest/v1` descriptor、determinism/no-overwrite を提供する。 |
| EPIC-REQ-005 | domain status、0/1/2/3/130 exit、run-level changed-path budget、domain-local entity budgetを slice の範囲で実装・検証する。 |
| EPIC-REQ-009 | closed stdout selector、exact-byte copy、unavailable result、stderr diagnostic、usage no-publicationをsliceのpublic CLI contractとして実装・検証する。 |

## 観測可能な要件

| ID | 観測面 | 要件 |
| --- | --- | --- |
| I02-REQ-001 | CLI と observable outcome | coding agent が named endpoint で before/after Python semantic snapshot を安全に固定し、意味のある class/member/relation change と影響 context だけを比較できる。 |
| I02-REQ-002 | source acquisition | flagなしはimplicit base→開始時frozen working-tree、`--from REF`はREF→frozen working-tree、`--to REF`はendpoint commit anchorに対して解決したimplicit base→REF、両方指定はexact REF→REFとする。`--to working-tree`だけの場合はrun開始時HEADをanchorにする。 |
| I02-REQ-003 | semantic behavior | before/afterのimmutable Python semantic sideを比較する。domainが片側だけに存在するときはreal snapshotとinternal canonical empty-sideを比較して全added/removedとし、両側不在はnot_applicable、target evidenceがあるsideのacquisition/analysis failureはincompleteとする。 |
| I02-REQ-004 | Artifact/output | semantic diff JSONはbefore/after side descriptorとdigest、metadata-only FileChangeSet、SemanticChangeSet、seed、upstream/downstream context、matching evidenceを分離し、raw hunk本文を保持しない。 |
| I02-REQ-005 | failure behavior | endpoint unresolved、missing Git object、fingerprint drift、implicit changed-path admission超過はrun-level fatal exit 1でsemantic JSON、PlantUML、final run manifestを公開しない。entity budget超過またはside acquisition/static analysis failureはdomain `incomplete_kind: payload_unavailable`、exit 3でaffected domain Artifactを公開しない。 |
| I02-REQ-006 | safety/determinism | 解析対象 module、plugin、migration、build script、application entry point を import または実行しない。 同じ source bytes、endpoint、resolved config、adapter version では entity・member・relation・diagnostic・Artifact path の順序と SHA-256 が決定的になる。 |
| I02-REQ-007 | slice-specific boundary | FileChangeSetはA/M/D/R/C/T/U/?とold/new line-range metadata、content-independent hunk IDだけをevidenceとして保持する。implicit changed-path default 1,000とentity default 500は別gateで、valid explicit overrideとactual countをmanifestへ記録する。 |
| I02-REQ-008 | stdout contract | `--stdout SELECTOR`を高々1回のclosed selectorとして検証し、available exact bytes、unavailable result、selectorなしsummary、stderr diagnostics、exit 2 no-publicationを提供する。 |

### I02-REQ-001

coding agent が named endpoint で before/after Python semantic snapshot を安全に固定し、意味のある class/member/relation change と影響 context だけを比較できる。
### I02-REQ-002

flagなしはimplicit base→開始時frozen working-tree、`--from REF`はREF→frozen working-tree、`--to REF`はendpoint commit anchorに対して解決したimplicit base→REF、両方指定はexact REF→REFとする。`--to working-tree`だけの場合はrun開始時HEADをanchorにする。
### I02-REQ-003

before/afterのimmutable Python semantic sideを比較する。domainが片側だけに存在するときはreal snapshotとinternal canonical empty-sideを比較して全added/removedとし、両側不在はnot_applicable、target evidenceがあるsideのacquisition/analysis failureはincompleteとする。
### I02-REQ-004

semantic diff JSONはbefore/after side descriptorとdigest、metadata-only FileChangeSet、SemanticChangeSet、seed、upstream/downstream context、matching evidenceを分離し、raw hunk本文を保持しない。
### I02-REQ-005

endpoint unresolved、missing Git object、fingerprint drift、implicit changed-path admission超過はrun-level fatal exit 1でsemantic JSON、PlantUML、final run manifestを公開しない。entity budget超過またはside acquisition/static analysis failureはdomain `incomplete_kind: payload_unavailable`、exit 3でaffected domain Artifactを公開しない。
### I02-REQ-006

解析対象 module、plugin、migration、build script、application entry point を import または実行しない。 同じ source bytes、endpoint、resolved config、adapter version では entity・member・relation・diagnostic・Artifact path の順序と SHA-256 が決定的になる。
### I02-REQ-007

FileChangeSetはA/M/D/R/C/T/U/?とold/new line-range metadata、content-independent hunk IDだけをevidenceとして保持する。implicit changed-path default 1,000とentity default 500は別gateで、valid explicit overrideとactual countをmanifestへ記録する。
### I02-REQ-008

`--stdout SELECTOR`を高々1回のclosed selectorとして検証し、available exact bytes、unavailable result、selectorなしsummary、stderr diagnostics、exit 2 no-publicationを提供する。

## 2026-08-27 のレビュー対応決定

Red/Blue レビューで確認した境界を、実装と受入れの共通 authority として次のように固定する。

- working-tree の内部 inventory は、repository-relative path と canonical digest に加えて、tracking state、Git mode/type、object identity、content availability、unmerged 状態を保持する。これは public SourceView/manifest の新規フィールドではなく、開始時 state fingerprint と FileChangeSet 分類の内部証拠である。
- 同一 path の tracked→untracked は `D` と `?` の二つの canonical record とし、actual changed-path count も二件とする。mode-only は `M`、regular/symlink/gitlink 間の type transition は `T` とする。cross-path は identity が一意なら rename/copy をそれぞれ `R`/`C` 一件へまとめ、候補が曖昧なら安全な `D`/`A`/`?` へ戻し、source path を再利用しない。
- hunk の content evidence は `absent`、`available`、`unavailable` を区別する。取得できない、digest が一致しない、binary/上限超過の bytes を `b\"\"` として扱わず、available bytes のみから行範囲を計算する。affected Python path は `payload_unavailable`・exit 3・safe file-change/manifest のみ、非 Python path は偽の hunk を出さない。commit blob/object の欠損または read failure は run fatal・exit 1・公開なしとする。
- unmerged (`U`) は before side を一度だけ実際に解析し、その同じ observation の semantic side、coverage、diagnostic から safe manifest を構成する。after は未解析 `analysis-failed` として記録し、synthetic zero coverage で before の実測結果を上書きしない。
- `[comparison].upstream_ref` は既存 config contract どおり参照名前空間として deterministic に子 ref へ展開する。explicit target、展開した候補、built-in 候補の順序と merge-base は provenance に記録し、fetch/checkout/ref mutation は行わない。

上記は既存 `file-change-set/v1`、`source-view/v1`、`run-manifest/v1` の public schema version を変更しない。レビュー対応の acceptance は production CLI/application 経路で status、budget、hunk、U coverage、missing-object、drift、valid override、schema/publication を検証する。

### CLI examples

```bash
code-structure-viz diff --repo . --domain python --output-dir /tmp/csv-python-diff
code-structure-viz diff --repo . --domain python --from origin/main --to head --output-dir /tmp/csv-pr-head
code-structure-viz diff --repo . --domain python --from v1.0.0 --to v1.1.0 --upstream-depth 2 --downstream-depth 1 --output-dir /tmp/csv-release-diff
code-structure-viz diff --repo . --domain python --format semantic-json --stdout python:semantic-json --output-dir /tmp/csv-stdout
```

### source acquisition contract

- flagなしはimplicit base→開始時frozen working-tree、`--from REF`はREF→frozen working-tree、`--to REF`はresolved endpoint commit anchorに対して解決したimplicit base→REF、両方指定はexact REF→REFとする。
- `--to head`は開始時HEAD commit、`--to working-tree`は開始時frozen working tree、`--from working-tree`はusage error、exit 2とする。
- `--to working-tree` を `--from` なしで指定した場合、run開始時にworking treeをfreezeし、同時点の`HEAD^{commit}`をimplicit-base merge-baseのendpoint commit anchorにする。priorityはexplicit PR target、configured comparison target/upstream、`origin/HEAD`、local `main`/`develop`/`master`。provenanceはrequested endpoints、frozen digest、start HEAD anchor、selected candidate、merge-base、`resolution_method: "implicit-base-from-start-head-anchor"`を持つ。initial-commit fallback、auto fetch、checkoutを行わない。
- before commit sourceはGit object databaseからread-onlyに読み、working-tree sourceはrepository外temporary areaへfreezeする。開始/終了fingerprint driftではfinal outputを変更しない。
- `FileChangeSet` hunkはmetadataだけを持つ。許可項目はrepository-relative old/new path、file status、old/new start line、old/new line count、ordinal、これらのcanonical tupleから生成したcontent-independent SHA-256 `hunk_id`である。raw patch/context/added/deleted lines、source body、comment、literal、secret、absolute pathをmodel、JSON、PlantUML、manifest、diagnostic、logへ保持・公開しない。
- implicit changed-path budgetはdomain比較前のrun-level admission gateでdefault 1,000。overrideなしでactual countが超過したrunはfatal analysis/environment、exit 1、safe machine-readable diagnosticのみとし、semantic JSON、PlantUML、final run manifestを公開しない。positive integerの`--max-changed-paths N`は通常処理を許可し、manifestへrequested/resolved/count/config sourceを記録する。invalid overrideはexit 2。

### semantic contract

- before/after sideはimmutable digestで識別する。both-presentはreal snapshots、before-only/after-onlyはreal snapshotとcanonical empty-sideを比較する。

| before domain evidence | after domain evidence | status | comparison / publication | exit |
| --- | --- | --- | --- | --- |
| absent | absent | `not_applicable` | statusとsafe diagnosticのみ。semantic JSON/PlantUMLなし。 | 0 |
| present・analysis成功 | present・analysis成功 | `complete` | real snapshot同士を比較し、domain diff JSON/PlantUMLを公開する。 | 0 |
| present・analysis成功 | absent | `complete` | real beforeとcanonical empty-sideを比較し、全entity/member/relationをremovedとして公開する。 | 0 |
| absent | present・analysis成功 | `complete` | canonical empty-sideとreal afterを比較し、全entity/member/relationをaddedとして公開する。 | 0 |
| target evidenceあり | いずれかのsideでacquisition/static analysis失敗 | `incomplete` / `payload_unavailable` | added/removedを推測せず、affected domain diff JSON/PlantUMLを公開しない。safe manifestへ`incomplete_kind: "payload_unavailable"`、`payload_available: false`、diagnostic/coverage/provenanceを記録する。 | 3 |

- internal canonical empty-side は `code-structure-viz.empty-side/v1` の canonical UTF-8 JSONである。`domain`、`document_kind: "internal-diff-side"`、空の `entities`/`members`/`relations` を持ち、endpointやside名を含めない。同一domain/versionではSHA-256が一定で、manifestのbefore/after side descriptorに`kind: "canonical-empty-side"`として記録する。standalone snapshot、semantic Artifact、empty diagramとして公開しない。
- class、field、method、property、decorator metadata、relationのsemantic deltaがあるentityだけをchanged seedとする。空白、comment、import orderだけの変化はseedにしない。
- impact graphはbefore/after relationのunion。upstream/downstreamを別frontierとし、default depthは各1。削除classはbefore relationからcontextを復元する。
- movedはhigh-confidence one-to-one、rename/name evidence、structural fingerprint、unique candidateをすべて満たす場合だけ採用し、それ以外はremoved+addedとする。
- diff diagramはseedと指定depthのcontextだけを所有する。

### output contract

- semantic diff JSONはbefore/after side kind/schema/digest、metadata-only FileChangeSet、SemanticChangeSet、seed、upstream/downstream context、matching evidenceを分離する。
- Python PlantUMLはclassとfield/methodをmember-levelでadded `+`、removed `-`、modified `~`、moved `→`、unknown `?`と色・線種の両方で示す。
- manifestはrequested/resolved endpoint、base method、start HEAD anchor、candidate、merge-base、frozen worktree digest、resolved config、budget requested/resolved/count、Artifact hashを保持する。
- working tree U pathはsafe file metadataへ残すが、そのpathが関係するsemantic domainはincompleteとする。
- raw patch/context/source/comment/literal/secret/absolute pathは全Artifactとdiagnosticに含めない。

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

- `python` domain の `diff` use case を CLI input から acceptance test まで届ける。
- common CLI/config/diagnostic/Artifact contract は、この slice に必要な範囲だけ導入または拡張する。
- repository-owned implementation、tests、fixtures、documentation、lockfile、CI lane を含む。

### 対象外

- SQLAlchemy row semantics と Next component semantics
- auto fetch、checkout、worktree/index/refs の変更
- Git R/C を semantic moved と同一視すること
- legacy pyclassuml/tree-git-diff CLI compatibility

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

- moved候補が複数ある場合はunknown movedを捏造せずremoved+addedとmatching diagnosticを返す。
- diff domain presenceは上記truth tableに従う。analysis failureをdomain absenceへ変換しない。
- このdiff sliceではbefore/afterのいずれかのsource acquisitionまたはstatic analysisが失敗した場合、常に`incomplete_kind: payload_unavailable`、affected JSON/PlantUMLなし、safe manifestのみ、exit 3とする。failure sideをcanonical empty-sideへ置換せず、`partial_safe`へ降格しない。
- implicit changed-path budgetはdomain比較前のrun-level admission gateでdefault 1,000。overrideなしでactual countが超過したrunはfatal analysis/environment、exit 1、safe machine-readable diagnosticのみとし、semantic JSON、PlantUML、final run manifestを公開しない。positive integerの`--max-changed-paths N`は通常処理を許可し、manifestへrequested/resolved/count/config sourceを記録する。invalid overrideはexit 2。
- entity-per-diagram budgetはdomain-local gateでdefault 500。overrideなしで超過したdomainは`incomplete`、exit 3とし、切り捨てず、そのdomainのsemantic JSONとPlantUMLを公開しない。valid core runではsafe run manifestを公開し、requested/resolved limit、actual count、diagnosticを記録する。all-domainではsuccessful sibling Artifactを保持する。positive integerの`--max-entities N`は通常公開を許可し、同じ値とcountをmanifestへ記録する。invalid overrideはexit 2。
- endpoint unresolved、missing object、fingerprint drift、output collisionはrun-level fatal exit 1。invalid CLI/config/overrideはexit 2。interruptはexit 130。
- diagnosticはstable code、severity、domain、safe repository-relative location、recoverability、human-readable messageを持ち、source body、raw hunk、secretを含めない。
- stop condition: independent side generation、empty-side provenance、endpoint/fingerprint provenance、metadata-only FileChangeSet、semantic seed、impact union、budget/publication matrixがacceptanceで固定されるまでSQLAlchemy/Next diffへ進まない。

## 受け入れ条件

| ID | 観測可能な完了条件 | acceptance test |
| --- | --- | --- |
| I02-AC-001 | 全`--from`/`--to`組合せをtable-drivenに検証し、`--to working-tree`のみではstart HEAD anchor、frozen digest、candidate、merge-base、resolution methodが一致する。 | I02-AT-001 |
| I02-AC-002 | deleted classのbefore edgeとunion graphでupstream/downstream depth 1を別々に選ぶ。 | I02-AT-002 |
| I02-AC-003 | base解決不能、U path、missing object、fingerprint driftでfail closedになる。 | I02-AT-003 |
| I02-AC-004 | 全Git invocationがread-only allowlist内で、refs/index/worktree fingerprintを変更しない。 | I02-AT-004 |
| I02-AC-005 | whitespace/comment/import-order onlyはseed 0、member/relation deltaはseedになる。 | I02-AT-005 |
| I02-AC-006 | 一意なrename+fingerprintだけmoved、ambiguous candidateはremoved+addedになる。 | I02-AT-006 |
| I02-AC-007 | implicit 1,001 pathsはexit 1・diagnostic only・semantic/PlantUML/final manifestなし、valid overrideはrequested/resolved/count付きで成功する。 | I02-AT-007 |
| I02-AC-008 | both-absent、both-present、before-only、after-only、side failureのtruth tableでstatus、delta、publication、exit、empty-side digestが一致する。 | I02-AT-008 |
| I02-AC-009 | FileChangeSet hunkがrange/status/content-independent IDだけを持ち、raw patch/context/source/comment/literal/secret/absolute pathを全channelへ出さない。 | I02-AT-009 |
| I02-AC-010 | 501 diagram entitiesはdomain `incomplete_kind: payload_unavailable`・exit 3・affected JSON/PlantUMLなし・manifest countあり、valid 600 overrideは通常公開する。 | I02-AT-010 |
| I02-AC-011 | stdout selectorのvalid/invalid/duplicate/domain/format、available exact-byte、not_applicable/payload_unavailable/fatal/interrupt result、selectorなしsummaryをtable-drivenに満たす。 | I02-AT-011 |

- **I02-AC-001〜I02-AC-011 がすべて満たされ、planned test command が clean checkout で成功すること。**
- Requirement、Design、Plan の trace table が一致し、unresolved acceptance gap がないこと。
- release boundary: ISSUE-01と合わせてPython domain preview。shared Git comparison contractを後続diff slicesへ渡す。

## 制約・前提

- initial platform は macOS と Linux。native Windows は対象外。
- Core/CLI/Git/manifest/Python/SQLAlchemy は Python 3.12 以上。Next adapter 利用時だけ Node.js 22 LTS 以上。
- Git 2.39 以上。CI は minimum supported と repository で明示更新する latest stable lane を実行する。
- direct/indirect dependency は lockfile で exact resolve し、license inventory と offline runtime test を持つ。runtime に network access を要求しない。
- `pyclassuml` と `tree-git-diff` への runtime/package/CLI dependency を持たない。legacy code の直接 copy は license/provenance 未確認のまま行わず、初期実装は contract/test evidence を基に repository-owned code として再実装する。
- product HTML report generation、HTML command、Tailscale publication は本 Issue の製品 scope 外。`explanation.html` は specification Artifact である。
