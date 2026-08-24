---
種別: 要件定義書（Issue）
ID: "iss-00010"
タイトル: "Run Unified Multi-Domain Structure Comparison"
関連GitHub: ["#10"]
package_sequence_key: "ISSUE-07"
状態: "draft"
最終更新: "2026-08-24"
親: ["epic-00002", "init-00001"]
---

# iss-00010 Run Unified Multi-Domain Structure Comparison — 要件定義

詳細: [Requirement Guide](../../../../../../docs/authoring/requirement.md)

## 目的

coding agent が domain を省略した一回の command で Python、SQLAlchemy、Next の適用可否・成功・不完全を区別し、成功 Artifact を保持した集約 manifest と正しい exit code を得られる。

利用者 story: coding agent として、repository の複数 domain を一度に調査し、一部 adapter が失敗しても利用可能な JSON/PlantUML を失わず、人間へ説明できる provenance と diagnostic を受け取りたい。

この Issue は技術 layer の完成ではなく、利用者が command を実行して source acquisition、domain analysis、semantic JSON、PlantUML、diagnostic、acceptance evidence まで確認できる一つの vertical outcome を所有する。

## 背景

- 親 Initiative は三 domain の code structure を静的に可視化する。
- 親 Epic は安全な Git comparison と agent-first Artifact contract を一つの product outcome として統合する。
- この slice の declared dependency は ISSUE-04, ISSUE-06。依存 Issue の public contract だけを利用し、unfinished sibling の内部実装には依存しない。
- canonical authority は exact verified current commit `867ee6929283dfc84711bce245b784d2b8e3e9e6` の accepted ADR、interview、親 R/D/P と本 Issue の current canonical textである。

| 親 requirement | この Issue の所有範囲 |
| --- | --- |
| EPIC-REQ-001 | all-domain orchestration を end-to-end で提供する。 |
| EPIC-REQ-002 | static analysis、read-only Git、safe endpoint/source、redaction、fail-closed を維持する。 |
| EPIC-REQ-003 | all selected domains の identity/member/relation/matching semantics を domain ownership のまま保つ。 |
| EPIC-REQ-004 | per-domain versioned semantic JSON、domain-specific PlantUML、`run-manifest/v1` descriptor、determinism/no-overwrite を提供する。 |
| EPIC-REQ-005 | domain status、0/1/2/3/130 exit、run-level changed-path budget、domain-local entity budgetを slice の範囲で実装・検証する。 |

## 観測可能な要件

| ID | 観測面 | 要件 |
| --- | --- | --- |
| I07-REQ-001 | CLI と observable outcome | coding agent が domain を省略した一回の command で Python、SQLAlchemy、Next の適用可否・成功・不完全を区別し、成功 Artifact を保持した集約 manifest と正しい exit code を得られる。 |
| I07-REQ-002 | source acquisition | domain無指定ではpython、sqlalchemy、nextをdeterministic orderで選び、one runのpreflight、endpoint resolution、working-tree freeze、start-HEAD anchor、metadata-only FileChangeSet、changed-path admissionを共有する。 |
| I07-REQ-003 | semantic behavior | common contractはrun/domain status、Artifact descriptor、diagnostic、coverage、provenance、budget、safe graph summary countsだけを共有する。domain identity/member/relation/matchingを統合せず、`code-structure-viz.semantic/v1`の`domain: all` payloadを生成しない。 |
| I07-REQ-004 | Artifact/output | 各complete domainはown semantic JSONとdomain-specific PlantUMLを生成する。not_applicableはstatus/diagnosticのみ。side failureまたはentity budgetによるincomplete domainはaffected JSON/PlantUMLを生成しない。aggregateは`code-structure-viz.run-manifest/v1`だけとする。 |
| I07-REQ-005 | failure behavior | 各domainは共通presence truth tableに従う。run-level changed-path overrunはexit 1で全Artifact/final manifestなし、domain-local entity overrunはaffected domain incomplete・exit 3でsibling Artifactとaggregate manifestを保持する。 |
| I07-REQ-006 | safety/determinism | 解析対象 module、plugin、migration、build script、application entry point を import または実行しない。 同じ source bytes、endpoint、resolved config、adapter version では entity・member・relation・diagnostic・Artifact path の順序と SHA-256 が決定的になる。 |
| I07-REQ-007 | slice-specific boundary | 一つの output transaction で domain Artifact と run manifest を staging し、fingerprint と collision gate 後に公開する。 |

### I07-REQ-001

coding agent が domain を省略した一回の command で Python、SQLAlchemy、Next の適用可否・成功・不完全を区別し、成功 Artifact を保持した集約 manifest と正しい exit code を得られる。
### I07-REQ-002

domain無指定ではpython、sqlalchemy、nextをdeterministic orderで選び、one runのpreflight、endpoint resolution、working-tree freeze、start-HEAD anchor、metadata-only FileChangeSet、changed-path admissionを共有する。
### I07-REQ-003

common contractはrun/domain status、Artifact descriptor、diagnostic、coverage、provenance、budget、safe graph summary countsだけを共有する。domain identity/member/relation/matchingを統合せず、`code-structure-viz.semantic/v1`の`domain: all` payloadを生成しない。
### I07-REQ-004

各complete domainはown semantic JSONとdomain-specific PlantUMLを生成する。not_applicableはstatus/diagnosticのみ。side failureまたはentity budgetによるincomplete domainはaffected JSON/PlantUMLを生成しない。aggregateは`code-structure-viz.run-manifest/v1`だけとする。
### I07-REQ-005

各domainは共通presence truth tableに従う。run-level changed-path overrunはexit 1で全Artifact/final manifestなし、domain-local entity overrunはaffected domain incomplete・exit 3でsibling Artifactとaggregate manifestを保持する。
### I07-REQ-006

解析対象 module、plugin、migration、build script、application entry point を import または実行しない。 同じ source bytes、endpoint、resolved config、adapter version では entity・member・relation・diagnostic・Artifact path の順序と SHA-256 が決定的になる。
### I07-REQ-007

一つの output transaction で domain Artifact と run manifest を staging し、fingerprint と collision gate 後に公開する。


### CLI examples

```bash
code-structure-viz diff --repo . --output-dir /tmp/csv-all-diff
code-structure-viz snapshot --repo . --output-dir /tmp/csv-all-snapshot
code-structure-viz diff --repo . --domain python --domain sqlalchemy --from origin/main --to head --stdout manifest --output-dir /tmp/csv-backend-diff
```

### source acquisition contract

- domain無指定ならpython、sqlalchemy、nextをdeterministic orderで実行する。snapshotも同じdefault、明示domainで絞り込める。
- core preflight、endpoint resolution、working-tree freeze、resolved config、metadata-only FileChangeSet、changed-path admissionはone runで共有するが、各adapterはdomain-owned source selectionとsemantic modelを保持する。
- `--to working-tree` を `--from` なしで指定した場合、run開始時にworking treeをfreezeし、同時点の`HEAD^{commit}`をimplicit-base merge-baseのendpoint commit anchorにする。priorityはexplicit PR target、configured comparison target/upstream、`origin/HEAD`、local `main`/`develop`/`master`。provenanceはrequested endpoints、frozen digest、start HEAD anchor、selected candidate、merge-base、`resolution_method: "implicit-base-from-start-head-anchor"`を持つ。initial-commit fallback、auto fetch、checkoutを行わない。
- Next target evidence不在ならNodeを要求しない。target evidenceがあるNode/adapter failureはincompleteで、not_applicableへ変換しない。
- `FileChangeSet` hunkはmetadataだけを持つ。許可項目はrepository-relative old/new path、file status、old/new start line、old/new line count、ordinal、これらのcanonical tupleから生成したcontent-independent SHA-256 `hunk_id`である。raw patch/context/added/deleted lines、source body、comment、literal、secret、absolute pathをmodel、JSON、PlantUML、manifest、diagnostic、logへ保持・公開しない。
- implicit changed-path budgetはdomain比較前のrun-level admission gateでdefault 1,000。overrideなしでactual countが超過したrunはfatal analysis/environment、exit 1、safe machine-readable diagnosticのみとし、semantic JSON、PlantUML、final run manifestを公開しない。positive integerの`--max-changed-paths N`は通常処理を許可し、manifestへrequested/resolved/count/config sourceを記録する。invalid overrideはexit 2。

### semantic contract

- domain statusは`complete`、`not_applicable`、`incomplete`。all selected domainsがcomplete/not_applicableならoverall complete、少なくとも一つincompleteならoverall incomplete。
- Python、SQLAlchemy、Nextのdiffは同じpresence truth tableとcanonical empty-side contractを使う。

| before domain evidence | after domain evidence | status | comparison / publication | exit |
| --- | --- | --- | --- | --- |
| absent | absent | `not_applicable` | statusとsafe diagnosticのみ。semantic JSON/PlantUMLなし。 | 0 |
| present・analysis成功 | present・analysis成功 | `complete` | real snapshot同士を比較し、domain diff JSON/PlantUMLを公開する。 | 0 |
| present・analysis成功 | absent | `complete` | real beforeとcanonical empty-sideを比較し、全entity/member/relationをremovedとして公開する。 | 0 |
| absent | present・analysis成功 | `complete` | canonical empty-sideとreal afterを比較し、全entity/member/relationをaddedとして公開する。 | 0 |
| target evidenceあり | いずれかのsideでacquisition/static analysis失敗 | `incomplete` | added/removedを推測せず、affected domain diff JSON/PlantUMLを公開しない。safe manifest diagnostic/coverage/provenanceのみ。 | 3 |

- internal canonical empty-side は `code-structure-viz.empty-side/v1` の canonical UTF-8 JSONである。`domain`、`document_kind: "internal-diff-side"`、空の `entities`/`members`/`relations` を持ち、endpointやside名を含めない。同一domain/versionではSHA-256が一定で、manifestのbefore/after side descriptorに`kind: "canonical-empty-side"`として記録する。standalone snapshot、semantic Artifact、empty diagramとして公開しない。
- FileChangeSetはrun-level evidence、SemanticChangeSetはdomain-level ownership。domain identity/member/relation/matchingとcross-domain relationを統合・推測しない。
- aggregate manifestのgraph summaryはdomainごとのentity/member/relation/changed-seed countsなどsafe primitiveだけとし、semantic recordsを複製しない。

### output contract

- all-domain runは`code-structure-viz.semantic/v1`の`domain: all`を生成しない。complete domainごとにown semantic JSONとdomain-specific PlantUMLを生成する。
- `not_applicable` domainはstatus/diagnosticのみ。side acquisition/analysis failureまたはentity budget超過による`incomplete` domainはaffected semantic JSON/PlantUMLを公開しない。別のpartial-safe snapshot caseがdomain contract上Artifactを許す場合もstatus `incomplete`をpayload/manifestに明示する。
- aggregateは`code-structure-viz.run-manifest/v1`だけで、run/domain status、Artifact descriptors、diagnostics、coverage、endpoint/empty-side provenance、budget requested/resolved/count、safe graph summary countsを持つ。rootにentities/members/relations/matchingを持たない。
- output transactionはdomain payloadとmanifestをstagingし、fingerprint/collision/integrity gate後に公開する。exit 3ではsuccessful siblingsとsafe manifestを保持し、run-level fatalではfinal manifestも公開しない。

## スコープ

### 対象

- `all` domain の `snapshot-and-diff orchestration` use case を CLI input から acceptance test まで届ける。
- common CLI/config/diagnostic/Artifact contract は、この slice に必要な範囲だけ導入または拡張する。
- repository-owned implementation、tests、fixtures、documentation、lockfile、CI lane を含む。

### 対象外

- cross-domain semantic relation と single universal identity model
- public plugin ABI、remote execution、auto fetch
- 製品機能としての HTML report/HTML command/Tailscale publication
- native Windows、legacy CLI compatibility

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

- adapter exceptionはcore crashへ伝播させずdomain diagnosticへ正規化する。protocol corruption/security invariant violationはaffected domain incomplete。
- domain presenceは上記truth tableに従い、before-only/after-onlyをcomplete全removed/added、both-absentをnot_applicable、side failureをincompleteとする。
- implicit changed-path budgetはdomain比較前のrun-level admission gateでdefault 1,000。overrideなしでactual countが超過したrunはfatal analysis/environment、exit 1、safe machine-readable diagnosticのみとし、semantic JSON、PlantUML、final run manifestを公開しない。positive integerの`--max-changed-paths N`は通常処理を許可し、manifestへrequested/resolved/count/config sourceを記録する。invalid overrideはexit 2。
- entity-per-diagram budgetはdomain-local gateでdefault 500。overrideなしで超過したdomainは`incomplete`、exit 3とし、切り捨てず、そのdomainのsemantic JSONとPlantUMLを公開しない。valid core runではsafe run manifestを公開し、requested/resolved limit、actual count、diagnosticを記録する。all-domainではsuccessful sibling Artifactを保持する。positive integerの`--max-entities N`は通常公開を許可し、同じ値とcountをmanifestへ記録する。invalid overrideはexit 2。
- output collision、invalid config、minimum runtime不足、endpoint unresolved、fingerprint driftはrun-level fatal/usage。SIGINTはstaging cleanup、exit 130。
- all-domain semantic payloadを作らず、metadata-only hunk/redactionを全domain descriptorとdiagnosticで再検証する。
- stop condition: 三domainのpresence matrix、two-level budget publication、per-domain output、aggregate `run-manifest/v1`、partial success、endpoint provenance、exit/atomicity、minimum/latest CIがacceptanceで成立するまでInitiativeを完了扱いにしない。

## 受け入れ条件

| ID | 観測可能な完了条件 | acceptance test |
| --- | --- | --- |
| I07-AC-001 | domain無指定で三domainを順に実行し、per-domain semantic JSON/PlantUMLと一つの`run-manifest/v1`を出力し、`domain: all` semantic payloadを生成しない。 | I07-AT-001 |
| I07-AC-002 | Next incomplete、Python/SQLAlchemy completeでsuccessful Artifactとaggregate manifestを保持しexit 3にする。 | I07-AT-002 |
| I07-AC-003 | Next both-absentはNode未導入でもnot_applicable、domain Artifactなし、overall exit 0。 | I07-AT-003 |
| I07-AC-004 | endpoint/fingerprint/output collisionのrun-level failureでsemantic JSON、PlantUML、final manifestを公開しない。 | I07-AT-004 |
| I07-AC-005 | 0/1/2/3/130とstdout/stderr/manifest/publicationの組合せをtable-drivenに検証する。 | I07-AT-005 |
| I07-AC-006 | macOS/Linux、Python 3.12とlatest stable、Git 2.39とlatest、Next選択時Node 22とlatestをCIで確認する。 | I07-AT-006 |
| I07-AC-007 | uv lock/npm lock、license inventory、offline runtime install fixtureを検証する。 | I07-AT-007 |
| I07-AC-008 | 各domainのboth-absent/both-present/before-only/after-only/side failureを組み合わせ、domain/overall status、empty-side digest、publication、exitがtruth tableどおりになる。 | I07-AT-008 |
| I07-AC-009 | changed-path overrunはexit 1・final manifestなし、entity overrunはaffected domain incomplete・exit 3・sibling/manifest保持、valid overridesはrequested/resolved/countを記録する。 | I07-AT-009 |
| I07-AC-010 | `--to working-tree`だけのrunでstart HEAD anchor、frozen digest、candidate、merge-base、resolution methodを全domain provenanceへ共有する。 | I07-AT-010 |
| I07-AC-011 | FileChangeSetとaggregate manifestがrange/status/content-independent hunk IDだけを持ち、raw patch/context/source/comment/literal/secret/absolute pathを出さない。 | I07-AT-011 |

- **I07-AC-001〜I07-AC-011 がすべて満たされ、planned test command が clean checkout で成功すること。**
- Requirement、Design、Plan の trace table が一致し、unresolved acceptance gap がないこと。
- release boundary: Next.js対応とmulti-domain orchestrationの完了をもってInitiative完了。Python+SQLAlchemy intermediate releaseからのadditive extensionとする。

## 制約・前提

- initial platform は macOS と Linux。native Windows は対象外。
- Core/CLI/Git/manifest/Python/SQLAlchemy は Python 3.12 以上。Next adapter 利用時だけ Node.js 22 LTS 以上。
- Git 2.39 以上。CI は minimum supported と repository で明示更新する latest stable lane を実行する。
- direct/indirect dependency は lockfile で exact resolve し、license inventory と offline runtime test を持つ。runtime に network access を要求しない。
- `pyclassuml` と `tree-git-diff` への runtime/package/CLI dependency を持たない。legacy code の直接 copy は license/provenance 未確認のまま行わず、初期実装は contract/test evidence を基に repository-owned code として再実装する。
- product HTML report generation、HTML command、Tailscale publication は本 Issue の製品 scope 外。`explanation.html` は specification Artifact である。
