---
種別: 要件定義書（Issue）
ID: "iss-00009"
タイトル: "Compare Next.js Component Changes"
関連GitHub: ["#9"]
package_sequence_key: "ISSUE-06"
状態: "draft"
最終更新: "2026-08-31"
親: ["epic-00002", "init-00001"]
---

# iss-00009 Compare Next.js Component Changes — 要件定義

詳細: [Requirement Guide](../../../../../../docs/authoring/requirement.md)

## 目的

coding agent が before/after Next.js semantic snapshot から component/props/import/render/boundary change と影響 context を比較できる。

利用者 story: coding agent として、TS/TSX の textual diff ではなく component declaration、export binding、static relation の意味変化を識別し、runtime tree を捏造せず review へ使いたい。

この Issue は技術 layer の完成ではなく、利用者が command を実行して source acquisition、domain analysis、semantic JSON、PlantUML、diagnostic、acceptance evidence まで確認できる一つの vertical outcome を所有する。

## 背景

- 親 Initiative は三 domain の code structure を静的に可視化する。
- 親 Epic は安全な Git comparison と agent-first Artifact contract を一つの product outcome として統合する。
- この slice の declared dependency は ISSUE-02, ISSUE-05。依存 Issue の public contract だけを利用し、unfinished sibling の内部実装には依存しない。
- canonical authority は stable scope ID、本 Issue と親 scope の repository-relative R/D/P path、accepted ADR、interview、latest user decisions である。採用・実装開始時に HEAD と configured upstream を再検証し、current commit SHA を本文の自己 authority として固定しない。

| 親 requirement | この Issue の所有範囲 |
| --- | --- |
| EPIC-REQ-001 | next domain の diff を end-to-end で提供する。 |
| EPIC-REQ-002 | static analysis、read-only Git、safe endpoint/source、redaction、fail-closed を維持する。 |
| EPIC-REQ-003 | next の identity/member/relation/matching semantics を domain ownership のまま保つ。 |
| EPIC-REQ-004 | per-domain versioned semantic JSON、domain-specific PlantUML、`run-manifest/v1` descriptor、determinism/no-overwrite を提供する。 |
| EPIC-REQ-005 | domain status、0/1/2/3/130 exit、run-level changed-path budget、domain-local entity budgetを slice の範囲で実装・検証する。 |
| EPIC-REQ-009 | closed stdout selector、exact-byte copy、unavailable result、stderr diagnostic、usage no-publicationをsliceのpublic CLI contractとして実装・検証する。 |

## 観測可能な要件

| ID | 観測面 | 要件 |
| --- | --- | --- |
| I06-REQ-001 | CLI と observable outcome | coding agent が before/after Next.js semantic snapshot から component/props/import/render/boundary change と影響 context を比較できる。 |
| I06-REQ-002 | source acquisition | ISSUE-02のnamed endpoint、`--to working-tree` start-HEAD anchor、read-only Git、freeze、fingerprint、metadata-only FileChangeSet、run-level changed-path gateを使い、両sideでISSUE-05 adapterを独立実行する。 |
| I06-REQ-003 | semantic behavior | Component declaration identity、ExportBinding、Prop、primitive import/render/wrapper/client-entry/router edge の semantic delta を changed seed とする。derived boundary role、format、comment、range、order、local alias、diagnostic だけは primary seed にしない。 |
| I06-REQ-004 | Artifact/output | Next diff JSON は before/after adapter contract/version/config digest、component/member/relation change、matching evidence、impact context を持つ。 |
| I06-REQ-005 | failure behavior | Next targetが片側だけに存在する場合はreal snapshotとcanonical empty-sideを比較して全added/removedとする。片側adapter/config/protocol/static analysis failureはdomain absenceやremoved/addedへ変換せずincompleteとする。 |
| I06-REQ-006 | safety/determinism | 解析対象 module、plugin、migration、build script、application entry point を import または実行しない。 同じ source bytes、endpoint、resolved config、adapter version では entity・member・relation・diagnostic・Artifact path の順序と SHA-256 が決定的になる。 |
| I06-REQ-007 | stdout contract | `--stdout SELECTOR`を高々1回のclosed selectorとして検証し、available exact bytes、unavailable result、selectorなしsummary、stderr diagnostics、exit 2 no-publicationを提供する。 |

### I06-REQ-001

coding agent が before/after Next.js semantic snapshot から component/props/import/render/boundary change と影響 context を比較できる。
### I06-REQ-002

ISSUE-02のnamed endpoint、`--to working-tree` start-HEAD anchor、read-only Git、freeze、fingerprint、metadata-only FileChangeSet、run-level changed-path gateを使い、両sideでISSUE-05 adapterを独立実行する。
### I06-REQ-003

Component declaration identity、ExportBinding、Prop、primitive import/render/wrapper/client-entry/router edge の semantic delta を changed seed とする。derived boundary role、format、comment、range、order、local alias、diagnostic だけは primary seed にしない。
### I06-REQ-004

Next diff JSON は before/after adapter contract/version/config digest、component/member/relation change、matching evidence、impact context を持つ。
### I06-REQ-005

Next targetが片側だけに存在する場合はreal snapshotとcanonical empty-sideを比較して全added/removedとする。片側adapter/config/protocol/static analysis failureはdomain absenceやremoved/addedへ変換せずincompleteとする。
### I06-REQ-006

解析対象 module、plugin、migration、build script、application entry point を import または実行しない。 同じ source bytes、endpoint、resolved config、adapter version では entity・member・relation・diagnostic・Artifact path の順序と SHA-256 が決定的になる。


### I06-REQ-007

`--stdout SELECTOR`を高々1回のclosed selectorとして検証し、available exact bytes、unavailable result、selectorなしsummary、stderr diagnostics、exit 2 no-publicationを提供する。

### CLI examples

```bash
code-structure-viz diff --repo . --domain next --from origin/main --to working-tree --output-dir /tmp/csv-next-diff
code-structure-viz diff --repo . --domain next --from release/1 --to head --upstream-depth 2 --downstream-depth 1 --output-dir /tmp/csv-next-impact
code-structure-viz diff --repo . --domain next --format semantic-json --stdout next:semantic-json --output-dir /tmp/csv-stdout
```

### source acquisition contract

- ISSUE-02のnamed endpoint、read-only Git、external working-tree freeze、fingerprint、metadata-only FileChangeSet、changed-path admissionを再利用し、両sideでISSUE-05 adapterを独立実行する。
- `--to working-tree` を `--from` なしで指定した場合、run開始時にworking treeをfreezeし、同時点の`HEAD^{commit}`をimplicit-base merge-baseのendpoint commit anchorにする。priorityはexplicit PR target、configured comparison target/upstream、`origin/HEAD`、local `main`/`develop`/`master`。provenanceはrequested endpoints、frozen digest、start HEAD anchor、selected candidate、merge-base、`resolution_method: "implicit-base-from-start-head-anchor"`を持つ。initial-commit fallback、auto fetch、checkoutを行わない。
- domain absenceだけをcanonical empty-sideへ写像し、Node/adapter/config/protocol/static-analysis failureをabsenceへ変換しない。
- `FileChangeSet` hunkはmetadataだけを持つ。許可項目はrepository-relative old/new path、file status、old/new start line、old/new line count、ordinal、これらのcanonical tupleから生成したcontent-independent SHA-256 `hunk_id`である。raw patch/context/added/deleted lines、source body、comment、literal、secret、absolute pathをmodel、JSON、PlantUML、manifest、diagnostic、logへ保持・公開しない。
- implicit changed-path budgetはdomain比較前のrun-level admission gateでdefault 1,000。overrideなしでactual countが超過したrunはfatal analysis/environment、exit 1、safe machine-readable diagnosticのみとし、semantic JSON、PlantUML、final run manifestを公開しない。positive integerの`--max-changed-paths N`は通常処理を許可し、manifestへrequested/resolved/count/config sourceを記録する。invalid overrideはexit 2。

### semantic contract

- Componentのexact identityはISSUE-05 `ComponentDeclarationResolution/v1`が定めるdeclaration identityであり、export aliasやroute/range/order/diagnosticをidentityへ混ぜない。
- `ExportBindingResolution/v1`のdirect/default/re-export/star bindingはComponentとは別memberとして比較する。barrel移動、alias変更、default/named再公開はExportBinding deltaであり、同じdeclaration Componentのremoved/addedへ変換しない。
- Propとprimitive relation（value/type import、render、component_wrap、client_entry、router context）をprimary semantic deltaとする。`client_dependency`、`server_candidate`、dual role、`boundary_effect`はprimitive factから再計算するcontextであり、exact matchingまたはprimary seedにしない。
- before/after各sideは自身の`SourceAcquisitionPlan/v1`、`domain_config_projection("next")`/digest、TrustedTypeEnvironment digest、adapter/protocol/model versionを所有し、他sideのconfigへ寄せない。
- format、comment、range、order、local alias、diagnosticだけの変化はprimary seedにしない。

| before domain evidence | after domain evidence | status | comparison / publication | exit |
| --- | --- | --- | --- | --- |
| absent | absent | `not_applicable` | statusとsafe diagnosticのみ。semantic JSON/PlantUMLなし。 | 0 |
| present・analysis成功 | present・analysis成功 | `complete` | real snapshot同士を比較し、domain diff JSON/PlantUMLを公開する。 | 0 |
| present・analysis成功 | absent | `complete` | real beforeとcanonical empty-sideを比較し、全entity/member/relationをremovedとして公開する。 | 0 |
| absent | present・analysis成功 | `complete` | canonical empty-sideとreal afterを比較し、全entity/member/relationをaddedとして公開する。 | 0 |
| target evidenceあり | いずれかのsideでacquisition/static analysis失敗 | `incomplete` / `payload_unavailable` | added/removedを推測せず、affected domain diff JSON/PlantUMLを公開しない。safe manifestへ`incomplete_kind: "payload_unavailable"`、`payload_available: false`、diagnostic/coverage/provenanceを記録する。 | 3 |

- internal canonical empty-side は `code-structure-viz.empty-side/v1` の canonical UTF-8 JSONである。`domain`、`document_kind: "internal-diff-side"`、空の `entities`/`members`/`relations` を持ち、endpointやside名を含めない。同一domain/versionではSHA-256が一定で、manifestのbefore/after side descriptorに`kind: "canonical-empty-side"`として記録する。standalone snapshot、semantic Artifact、empty diagramとして公開しない。
- component matchingはdeclaration exact identityを最優先する。exact identityが片側に存在しない場合だけ、rename evidence、structural fingerprint、unique candidateをすべて満たす高信頼候補をmovedとする。ExportBinding、route、range、order、diagnostic、derived boundary roleはmoved判定のidentity/evidenceに使わない。
- impact graphはbefore/after static relation unionで、removed componentはbefore edgeを使う。nonliteral dynamic behaviorはunknownでruntime relationを捏造しない。

### output contract

- Next diff JSONはbefore/after side kind/schema/digest、adapter contract/version/config digest、component/member/relation change、matching evidence、impact context、metadata-only FileChangeSetを持つ。
- PlantUMLはcomponent、props、imports/render/client boundaryをmember/relation-level vocabularyで示す。
- manifestはrequested/resolved endpoint、start HEAD anchor、frozen digest、candidate、merge-base、side digests、budget requested/resolved/count、coverage、diagnostic、Artifact hashを記録する。
- raw hunk、source body、comment、literal、secret、absolute pathを含めない。

### incomplete publication contract

`incomplete` は `incomplete_kind` により次の二種類へ分ける。`not_applicable`、run-level fatal、usage error と混同しない。

| incomplete_kind | 判定条件 | affected domain payload | manifest / sibling | exit |
| --- | --- | --- | --- | --- |
| `partial_safe` | failure が局所的に隔離でき、残る subset が semantic に安全で、coverage と diagnostic が欠落範囲を明示し、全 requested payload が redaction を満たし、entity budget 内である。 | status `incomplete` の requested semantic JSON と PlantUML を安全 subset として公開する。truncation や failure entity の added/removed 推測はしない。 | `payload_available: true`、`incomplete_kind`、coverage、diagnostic、Artifact descriptor を記録する。 | 3 |
| `payload_unavailable` | safe subset がない、global source acquisition/protocol/schema/security/unsafe-path failure、entity budget 超過、または diff のいずれかの side acquisition/static analysis failureである。 | affected domain の semantic JSON と PlantUML を公開しない。 | run-level fatalでない限りsafe core manifestに `payload_available: false`、`incomplete_kind`、coverage/diagnostic/countを記録する。 | 3 |

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
{"type":"stdout_result","schema":"code-structure-viz.stdout-result/v1","selector":"next:semantic-json","availability":false,"domain_status":"not_applicable","stable_reason":"domain_not_applicable","artifact":null}
```

| case | stdout | stderr | exit | publication |
| --- | --- | --- | --- | --- |
| selector なし、complete/not_applicable/incomplete/fatal/interrupt | `run-summary/v1` JSON 1行 | diagnostic のみ | 0/1/3/130 | outcome contract に従う |
| available `DOMAIN:FORMAT` | 対象 Artifact の exact bytes | diagnostic のみ | 0 または `partial_safe` の3 | output-dir へ通常公開 |
| available `manifest` | final run manifest の exact bytes | diagnostic のみ | 0 または3 | output-dir へ通常公開 |
| domain not_applicable | `stdout_result/v1` 1行、`domain_status: not_applicable`、`stable_reason: domain_not_applicable` | diagnostic のみ | 0 | domain payload なし、manifest は通常規則 |
| domain payload_unavailable | `stdout_result/v1` 1行、`domain_status: incomplete`、`stable_reason: domain_payload_unavailable` | diagnostic のみ | 3 | affected payload なし、safe manifest は通常規則 |
| run fatal または final manifest 不在 | `stdout_result/v1` 1行、`run_status: fatal`、reason は `run_fatal` または `final_manifest_unavailable` | diagnostic のみ | 1 | final manifestを含めrun-level Artifactなし |
| handled interrupt | `stdout_result/v1` 1行、`run_status: interrupted`、`stable_reason: run_interrupted` | diagnostic のみ | 130 | staging cleanup |
| duplicate/invalid/unselected-domain/unrequested-format | 空 | usage diagnostic | 2 | Artifactなし |

## スコープ

### 対象

- `next` domain の `diff` use case を CLI input から acceptance test まで届ける。
- common CLI/config/diagnostic/Artifact contract は、この slice に必要な範囲だけ導入または拡張する。
- repository-owned implementation、tests、fixtures、documentation、lockfile、CI lane を含む。

### 対象外

- runtime render tree と hydration behavior の差分
- bundle analysis、Next build output、browser DOM diff
- cross-domain aggregation と overall exit decision
- HTML report generation

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

- diff domain presenceは上記truth tableに従う。片側target absenceはcomplete全added/removed、side adapter/config/protocol/static-analysis failureはincomplete。
- このdiff sliceではbefore/afterのいずれかのsource acquisitionまたはstatic analysisが失敗した場合、常に`incomplete_kind: payload_unavailable`、affected JSON/PlantUMLなし、safe manifestのみ、exit 3とする。failure sideをcanonical empty-sideへ置換せず、`partial_safe`へ降格しない。
- nonliteral dynamic importはunknown relation diagnosticとcoverageへ残し、runtime relationを生成しない。
- implicit changed-path budgetはdomain比較前のrun-level admission gateでdefault 1,000。overrideなしでactual countが超過したrunはfatal analysis/environment、exit 1、safe machine-readable diagnosticのみとし、semantic JSON、PlantUML、final run manifestを公開しない。positive integerの`--max-changed-paths N`は通常処理を許可し、manifestへrequested/resolved/count/config sourceを記録する。invalid overrideはexit 2。
- entity-per-diagram budgetはdomain-local gateでdefault 500。overrideなしで超過したdomainは`incomplete`、exit 3とし、切り捨てず、そのdomainのsemantic JSONとPlantUMLを公開しない。valid core runではsafe run manifestを公開し、requested/resolved limit、actual count、diagnosticを記録する。all-domainではsuccessful sibling Artifactを保持する。positive integerの`--max-entities N`は通常公開を許可し、同じ値とcountをmanifestへ記録する。invalid overrideはexit 2。
- `--to working-tree` start-HEAD anchor/provenanceとmetadata-only hunk boundaryをISSUE-02から変更しない。
- stop condition: Next member/relation seed、truth table、union impact、endpoint/hunk safety、budget/publication、unknown dynamic behaviorがacceptanceで固定されるまでall-domain集約へ進まない。

- slice-local consumer acceptance は `--domain next` の implicit 1,001 changed pathsをfan-out前exit 1、safe diagnosticのみ、semantic JSON/PlantUML/final manifestなしとし、valid `--max-changed-paths` overrideのrequested/resolved/count/config sourceをmanifest provenanceで検証する。

## 受け入れ条件

| ID | 観測可能な完了条件 | acceptance test |
| --- | --- | --- |
| I06-AC-001 | component/prop/import/render/boundary changeをmember-level JSONとPlantUMLにする。 | I06-AT-001 |
| I06-AC-002 | format/comment/import-order onlyはseedにならずstatic relation changeはseedになる。 | I06-AT-002 |
| I06-AC-003 | 一意component moveだけmoved、ambiguous candidateはremoved+added。 | I06-AT-003 |
| I06-AC-004 | target evidenceがある片側adapter/config/protocol failureをdomain absenceやremovalへ変換せずincompleteにする。 | I06-AT-004 |
| I06-AC-005 | removed componentのbefore edgeをunion graph contextに保持する。 | I06-AT-005 |
| I06-AC-006 | nonliteral dynamic behaviorをunknownとしruntime relationを生成しない。 | I06-AT-006 |
| I06-AC-007 | both-absent、both-present、before-only、after-only、side failureのtruth tableでstatus/delta/publication/exit/empty-side digestが一致する。 | I06-AT-007 |
| I06-AC-008 | `--to working-tree`だけでstart HEAD anchor、frozen digest、candidate、merge-base、resolution methodを記録する。 | I06-AT-008 |
| I06-AC-009 | reused FileChangeSetがrange/status/content-independent IDだけを持ち、raw patch/context/sourceを出さない。 | I06-AT-009 |
| I06-AC-010 | 501 entitiesはdomain `incomplete_kind: payload_unavailable`・exit 3・affected JSON/PlantUMLなし・manifest countあり、valid overrideは通常公開する。 | I06-AT-010 |
| I06-AC-011 | `--domain next`のimplicit 1,001 changed pathsはfan-out前exit 1、safe diagnosticのみ、semantic JSON/PlantUML/final manifestなし。有効overrideは通常処理しrequested/resolved/countをmanifest provenanceへ記録する。 | I06-AT-011 |
| I06-AC-012 | stdout selectorのvalid/invalid/duplicate/domain/format、available exact-byte、not_applicable/payload_unavailable/fatal/interrupt result、selectorなしsummaryをtable-drivenに満たす。 | I06-AT-012 |

- **I06-AC-001〜I06-AC-012 がすべて満たされ、planned test command が clean checkout で成功すること。**
- Requirement、Design、Plan の trace table が一致し、unresolved acceptance gap がないこと。
- release boundary: Next domain diff preview。ISSUE-07統合前でも`--domain next`の単独利用が可能なacceptance boundary。

## 制約・前提

- initial platform は macOS と Linux。native Windows は対象外。
- Core/CLI/Git/manifest/Python/SQLAlchemy は Python 3.12 以上。Next adapter 利用時だけ Node.js 22 LTS 以上。
- Git 2.39 以上。CI は minimum supported と repository で明示更新する latest stable lane を実行する。
- direct/indirect dependency は lockfile で exact resolve し、license inventory と offline runtime test を持つ。runtime に network access を要求しない。
- `pyclassuml` と `tree-git-diff` への runtime/package/CLI dependency を持たない。legacy code の直接 copy は license/provenance 未確認のまま行わず、初期実装は contract/test evidence を基に repository-owned code として再実装する。
- product HTML report generation、HTML command、Tailscale publication は本 Issue の製品 scope 外。`explanation.html` は specification Artifact である。
