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
- canonical authority は exact verified current commit `867ee6929283dfc84711bce245b784d2b8e3e9e6` の accepted ADR、interview、親 R/D/P と本 Issue の current canonical textである。

| 親 requirement | この Issue の所有範囲 |
| --- | --- |
| EPIC-REQ-001 | python domain の diff を end-to-end で提供する。 |
| EPIC-REQ-002 | static analysis、read-only Git、safe endpoint/source、redaction、fail-closed を維持する。 |
| EPIC-REQ-003 | python の identity/member/relation/matching semantics を domain ownership のまま保つ。 |
| EPIC-REQ-004 | per-domain versioned semantic JSON、domain-specific PlantUML、`run-manifest/v1` descriptor、determinism/no-overwrite を提供する。 |
| EPIC-REQ-005 | domain status、0/1/2/3/130 exit、run-level changed-path budget、domain-local entity budgetを slice の範囲で実装・検証する。 |

## 観測可能な要件

| ID | 観測面 | 要件 |
| --- | --- | --- |
| I02-REQ-001 | CLI と observable outcome | coding agent が named endpoint で before/after Python semantic snapshot を安全に固定し、意味のある class/member/relation change と影響 context だけを比較できる。 |
| I02-REQ-002 | source acquisition | flagなしはimplicit base→開始時frozen working-tree、`--from REF`はREF→frozen working-tree、`--to REF`はendpoint commit anchorに対して解決したimplicit base→REF、両方指定はexact REF→REFとする。`--to working-tree`だけの場合はrun開始時HEADをanchorにする。 |
| I02-REQ-003 | semantic behavior | before/afterのimmutable Python semantic sideを比較する。domainが片側だけに存在するときはreal snapshotとinternal canonical empty-sideを比較して全added/removedとし、両側不在はnot_applicable、target evidenceがあるsideのacquisition/analysis failureはincompleteとする。 |
| I02-REQ-004 | Artifact/output | semantic diff JSONはbefore/after side descriptorとdigest、metadata-only FileChangeSet、SemanticChangeSet、seed、upstream/downstream context、matching evidenceを分離し、raw hunk本文を保持しない。 |
| I02-REQ-005 | failure behavior | endpoint unresolved、missing Git object、fingerprint drift、implicit changed-path admission超過はrun-level fatal exit 1でsemantic JSON、PlantUML、final run manifestを公開しない。entity budget超過またはside analysis failureはdomain incomplete exit 3でaffected domain Artifactを公開しない。 |
| I02-REQ-006 | safety/determinism | 解析対象 module、plugin、migration、build script、application entry point を import または実行しない。 同じ source bytes、endpoint、resolved config、adapter version では entity・member・relation・diagnostic・Artifact path の順序と SHA-256 が決定的になる。 |
| I02-REQ-007 | slice-specific boundary | FileChangeSetはA/M/D/R/C/T/U/?とold/new line-range metadata、content-independent hunk IDだけをevidenceとして保持する。implicit changed-path default 1,000とentity default 500は別gateで、valid explicit overrideとactual countをmanifestへ記録する。 |

### I02-REQ-001

coding agent が named endpoint で before/after Python semantic snapshot を安全に固定し、意味のある class/member/relation change と影響 context だけを比較できる。
### I02-REQ-002

flagなしはimplicit base→開始時frozen working-tree、`--from REF`はREF→frozen working-tree、`--to REF`はendpoint commit anchorに対して解決したimplicit base→REF、両方指定はexact REF→REFとする。`--to working-tree`だけの場合はrun開始時HEADをanchorにする。
### I02-REQ-003

before/afterのimmutable Python semantic sideを比較する。domainが片側だけに存在するときはreal snapshotとinternal canonical empty-sideを比較して全added/removedとし、両側不在はnot_applicable、target evidenceがあるsideのacquisition/analysis failureはincompleteとする。
### I02-REQ-004

semantic diff JSONはbefore/after side descriptorとdigest、metadata-only FileChangeSet、SemanticChangeSet、seed、upstream/downstream context、matching evidenceを分離し、raw hunk本文を保持しない。
### I02-REQ-005

endpoint unresolved、missing Git object、fingerprint drift、implicit changed-path admission超過はrun-level fatal exit 1でsemantic JSON、PlantUML、final run manifestを公開しない。entity budget超過またはside analysis failureはdomain incomplete exit 3でaffected domain Artifactを公開しない。
### I02-REQ-006

解析対象 module、plugin、migration、build script、application entry point を import または実行しない。 同じ source bytes、endpoint、resolved config、adapter version では entity・member・relation・diagnostic・Artifact path の順序と SHA-256 が決定的になる。
### I02-REQ-007

FileChangeSetはA/M/D/R/C/T/U/?とold/new line-range metadata、content-independent hunk IDだけをevidenceとして保持する。implicit changed-path default 1,000とentity default 500は別gateで、valid explicit overrideとactual countをmanifestへ記録する。
### CLI examples

```bash
code-structure-viz diff --repo . --domain python --output-dir /tmp/csv-python-diff
code-structure-viz diff --repo . --domain python --from origin/main --to head --output-dir /tmp/csv-pr-head
code-structure-viz diff --repo . --domain python --from v1.0.0 --to v1.1.0 --upstream-depth 2 --downstream-depth 1 --output-dir /tmp/csv-release-diff
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
| target evidenceあり | いずれかのsideでacquisition/static analysis失敗 | `incomplete` | added/removedを推測せず、affected domain diff JSON/PlantUMLを公開しない。safe manifest diagnostic/coverage/provenanceのみ。 | 3 |

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
- `--stdout` を明示した場合だけ、選択した一つの Artifact または run manifest を標準出力へ複製する。通常時の stdout は machine-readable summary だけとする。

- 解析対象 module、plugin、migration、build script、application entry point を import または実行しない。
- Git repository は read-only とし、fetch、checkout、reset、stash、clean、commit、ref 更新を実行しない。すべての Git subprocess で lazy fetch、external diff、textconv、color を無効化する。
- Artifact には repository-relative path、symbol、type、signature、relation、line range だけを許可し、source body、comment、literal、secret らしい値、absolute path を含めない。
- 同じ source bytes、endpoint、resolved config、adapter version では entity・member・relation・diagnostic・Artifact path の順序と SHA-256 が決定的になる。

## 失敗・境界条件

- moved候補が複数ある場合はunknown movedを捏造せずremoved+addedとmatching diagnosticを返す。
- diff domain presenceは上記truth tableに従う。analysis failureをdomain absenceへ変換しない。
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
| I02-AC-010 | 501 diagram entitiesはdomain incomplete・exit 3・affected JSON/PlantUMLなし・manifest countあり、valid 600 overrideは通常公開する。 | I02-AT-010 |

- **I02-AC-001〜I02-AC-010 がすべて満たされ、planned test command が clean checkout で成功すること。**
- Requirement、Design、Plan の trace table が一致し、unresolved acceptance gap がないこと。
- release boundary: ISSUE-01と合わせてPython domain preview。shared Git comparison contractを後続diff slicesへ渡す。

## 制約・前提

- initial platform は macOS と Linux。native Windows は対象外。
- Core/CLI/Git/manifest/Python/SQLAlchemy は Python 3.12 以上。Next adapter 利用時だけ Node.js 22 LTS 以上。
- Git 2.39 以上。CI は minimum supported と repository で明示更新する latest stable lane を実行する。
- direct/indirect dependency は lockfile で exact resolve し、license inventory と offline runtime test を持つ。runtime に network access を要求しない。
- `pyclassuml` と `tree-git-diff` への runtime/package/CLI dependency を持たない。legacy code の直接 copy は license/provenance 未確認のまま行わず、初期実装は contract/test evidence を基に repository-owned code として再実装する。
- product HTML report generation、HTML command、Tailscale publication は本 Issue の製品 scope 外。`explanation.html` は specification Artifact である。
