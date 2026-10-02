# Binding and evidence completeness

## GitHub binding

GitHubコネクタで `chemitaro/code-structure-viz` の `iss-00008-generate-nextjs-component-snapshots` ブランチを直接取得しました。最終確認時点のbranch tipは次のとおりで、指定された `expected_sha` と完全一致します。他ブランチ、既定ブランチ、添付内容へのフォールバックは行っていません。

| 項目 | 値 |
|---|---|
| Repository | `chemitaro/code-structure-viz` |
| Target branch | `iss-00008-generate-nextjs-component-snapshots` |
| Expected SHA | `cd0e876410d494655b4a880543337274b9ffe948` |
| Retrieved branch-tip SHA | `cd0e876410d494655b4a880543337274b9ffe948` |
| Tree | `c0f03d49b8287e7a2e1da26ae56896ca10cd0d3a` |
| Parent | `d3cce1cb42b3c6a00d7a8d8d2b9ee4dbed2406d1` |
| SHA comparison | exact match |



Repository rootの `AGENTS.md` は、exact candidate refを指定した取得で404となり、不在を確認しました。

## Evidence lineage

| 項目 | 現在のbinding |
|---|---|
| Current candidate | `cd0e876410d494655b4a880543337274b9ffe948` |
| Source-reviewed SHA | `d3cce1cb42b3c6a00d7a8d8d2b9ee4dbed2406d1` |
| Original SI-03 base | `ce0edaa8fe63e79523fe7ad1dcb4b0a39dc02dce` |
| Current candidate relation | source-reviewed SHAの直接の子、1 commit ahead |
| Collection time | `2026-10-02T07:52:46Z` |
| Review source | ChatGPT Code Review Strict、fresh one-shot independent review |
| Reviewer session | `issue8-si03-source-inventory-review` |
| Reviewer conversation | `6abf52c7-c150-83e8-8923-5b4661b7bf16` |
| Review artifact | `reviews/si03-source-inventory-result.json` |
| Raw review SHA-256 | `9cd4663002277d8ad2bcfb8f3427550ec16d4da24f62b8803946a77511dc6670` |
| Analyst identity | `issue8-si03-source-owner-cause-adjudication` |
| Analyst continuity | same-objective follow-up to `issue8-si03-owner-cause-analysis` |
| Prior analyst conversation | `6abf57a0-d838-83ee-b8ef-1c963f134acc` |
| Continuity mode | reviewerとは別系統の、記録済みanalyst sessionへのfollow-up |

attachments-bundle

`d3cce1c...cd0e876` は1 commitの修復rangeです。current commitでは、root-origin edgeのseed外伝播を拒否する修正、回帰テスト、分析・修復証拠が追加されています。

## Reviewed/tested SHA alignment

**Source review**は `d3cce1c` を対象とし、`SI03-CR1-F1` をP1、`review_status=fail` と分類しました。これはcurrent `cd0e876` のレビュー結果ではありません。source-native classificationは変更せず保持しますが、current candidateについて同じP1が再現すると断定してはなりません。

**Current candidate evidence**は、cleanかつpush済みのexact `cd0e876` にbindしています。

| Lane | Current result |
|---|---|
| SI-03＋隣接six-module selection | 314 passed、SI-03 77 cases、large cases除外なし |
| 旧Python／SQLAlchemy＋Current pointer | 17 passed |
| Ruff | pass |
| Format | 230 files formatted |
| mypy | 188 sources pass |
| SpecDock | sync pass、validate 10 nodes |
| Probe | nonseed root edgeは拒否、direct File迂回はparse/readとも受理 |
| Identity | clean、configured upstream／live branch tip／HEADがexact `cd0e876` |

これらはparent workflowが実行したsupplied evidenceであり、本分析では再実行していません。attachments-bundle

## Packet completeness

本バッチは、次の判断には十分です。

- source-native P1の妥当性と修復状態
- current bounded repairのscope適合性
- direct File経路の現在挙動
- accepted Option Aとの整合
- root-cause grouping
- remaining correctionのauthority、route、authorization
- fresh re-review前の実装handoff

分析では、reported classification、claim validity、blocking effect、response route、authorizationを別々に扱います。P1は自動的な変更命令ではなく、reviewer recommendationもauthorityまたはauthorizationではありません。attachments-bundle

一方、**SI-03 closureには未完成**です。material gapは次のとおりです。

1. `cd0e876` はfresh Code Review Strictをまだ受けていません。
2. `CG-SI03-001` のdirect File迂回がexact current SHAで再現し、未修復です。
3. full mandatory seed集合の独立導出、全causal edge exactness、least-fixed-point taint、locality、target／export、Core／public certificationはSI-04の責任であり、本バッチでは未実行です。
4. actual TypeScript、OS process、CLI、offline packageは後続段階であり、本分析の欠落証拠ではありません。
5. review artifact digest、test log、picker provenanceはpacketのsupplied evidenceとして採用しましたが、本分析でraw bytesから再計算していません。

# Executive disposition

**Batch-level disposition:** current candidate `cd0e876` は、source-native P1の具体的なseed外root-origin bypassを正しく修復しています。しかし、同一root-cause groupに属するdirect File witness gapがexact current SHAで到達可能です。このmaterial gapはP severityを付与せず、親policyによりSI-03をblockします。

主要判断は次のとおりです。

- `SI03-CR1-F1` の元主張は `d3cce1c` に対して妥当でした。
- `cd0e876` の5行guardにより、rootからdeclared seed外への最初の伝播は拒否されます。元P1の具体的triggerはcurrent codeでは閉じています。
- `CG-SI03-001` はcurrent candidateで妥当かつ到達可能です。Fileがrootのdeclared seedであっても、`root → same-path Module → File` だけでdirect parse／read File failureを成立させられます。
- accepted Requirement／Design／admission-v3／preserved baselineは、failure rootがdeclared seedへ直接到達し、その後にrecord間伝播を行う意味を既に一意に定めています。
- したがって、remaining primary routeは **`implementation-remediation`** です。RequirementまたはDesignの変更は不要です。
- 親Planのautonomous-action boundary内で、意味を変えない限定修復が認可されています。
- safe progressは可能ですが、範囲はroot-origin witnessの局所correspondence、TDD、検証、checkpoint／push、fresh re-reviewに限定されます。

`cd0e876` はSI-03 passではありません。追加修復と、original base `ce0edaa...` からのfresh independent Code Review Strictで `P0=0 / P1=0 / review_status=pass` を得るまで、SI-04へ進めません。

# Root-cause groups

## Group map

| Group ID | Material item | Source-native classification | Current validity／status | Blocking |
|---|---|---|---|---|
| `RC-SI03-001` | `SI03-CR1-F1`: seed外root-origin edgeで別Moduleへroot kindを伝播できる | P1 | `d3cce1c` ではvalid／reachable。`cd0e876` では具体的triggerを修復済み | reviewer closure未了のためgate obligationは残る |
| `RC-SI03-001` | `CG-SI03-001`: declared File seedをdirect root edgeなしで間接到達させられる | severityなしのmaterial coverage gap | `cd0e876` でvalid／reachable | はい |
| `RC-SI03-001` | `EC-SI03-001`: 旧implementation evidenceがunrelated-root rejectionを過大に一般化 | severityなしのevidence conflict | 新Artifactで明示的にsupersede済み | いいえ |

## Shared invariant

三項目は、次の同一不変条件に属します。

> Failure rootのkindをowner／source causeとして利用するには、root-origin witnessがrootのdeclared seed集合と局所的に一致しなければならず、任意のsubmitted graph reachabilityをroot-origin certificationの代わりにしてはならない。

旧実装はroot-origin edge targetがseedであることを確認していませんでした。current repairはその**一方向**を閉じました。しかし現在も、declared seedがrootから直接witnessされるという**逆方向**を確認せず、別seedからの間接到達を代用できます。

`EC-SI03-001` を別groupに分けない理由は、独立したproduct defectではなく、同じ未検出経路に起因するevidence overclaimだからです。groupのprimary routeは一つだけ、`implementation-remediation` とします。evidence recordの訂正はsecondary supportであり、別workflow routeにはしません。

# Detailed adjudication

## `SI03-CR1-F1` — source-native P1

### Claim validity

元主張はvalidです。

`d3cce1c` では、failure rootの `record_ids=[A]` を維持したまま、同じrootからBへの許可されたedgeを追加すると、Bへroot kindが伝播し、Bのowner Fileを `excluded/failed` にできました。factoryとindependent revalidationの双方が受理していました。source reviewはこれをP1として報告しています。attachments-bundle

### Current trigger reachability

exact current `cd0e876` では、その具体的triggerは到達不能です。

`source_owner_witness_kinds_v3` は、edge sourceがfailure rootであり、targetがそのrootの `record_ids` に含まれない場合、adjacency登録前に `owner cause root-origin edge must target its declared seed` で拒否します。既存のclosed rule／kind／path検証とdownstream propagationは維持されています。

回帰テストも、`module_relation`、`export_binding`、`boundary_derivation` の三root kindと、extra root-origin edgeの有無を組み合わせています。

### In-scope impact

元P1は、任意の別Moduleをfailure原因へ接続し、そのowner Fileを非公開にできるため、owner-closed Option Aのexact File partitionを破っていました。

current修復は、その具体的な任意非公開経路を閉じています。public shape、File reason、taint、schema、profile、ID、hash、source ownerは変更していません。

### Blocking effect

P1というsource-native classificationは保持しますが、current candidateに対する未修復P1とは扱いません。

ただし、親policyはlocal修復だけでreview findingをclosedにすることを認めていません。fresh reviewerがcurrent candidateを独立に確認し、passを返すまで、P1 closure obligationは残ります。

### Violated authority

元実装が違反していた命題は次のとおりです。

- 公開可能なFile／Moduleをchildの任意edgeで非公開にしてはならない。
- untainted Fileの `excluded/failed` は、owner Moduleの検証済みfailure／root／taintへ結合されなければならない。
- File／Moduleの元taintとcausal meaningを変更してはならない。
- SI-03は偽owner原因を拒否する。

accepted Option Aは、全取得inventoryと元record-level taintを維持し、owner Moduleの立証済み原因に基づいてFile公開可否を決めることを定めています。

### First incorrect fault layer

最初のfault layerは **implementation** です。

- `source_owner_witness_kinds_v3` がedge-shape legalityをroot-origin authorityとして扱っていました。
- 隣接testは「edgeなし」を確認していましたが、「許可edgeを別Moduleへ追加する」mutationを確認していませんでした。

Requirement、accepted Design、ADR自体の誤りではありません。

### Primary response route

`implementation-remediation`。

accepted requirement／designが明確でimplementationが違反する場合のrouteです。attachments-bundle

### Preserved and changed guarantees

**Preserved**

- same request／seal／assets
- full Project／File discovery
- full-base Module owner cardinality
- 元record-level taint
- existing root kinds／rules
- Fileへの偽taint禁止
- Module→File逆taint禁止
- schema／enum／profile／version
- ID／hash／partition preimage
- SI-04責任境界

**Behavioral correction**

- failure rootはdeclared seed外へ直接root kindを伝播できません。

このcorrectionはcurrent `cd0e876` に実装済みです。

## `CG-SI03-001` — direct File witness material gap

### Claim validity

validです。severityは付与しません。

current probeは、parse／readそれぞれについて次のproofを構成しています。

- program File `F` とsame-path Module `M` をdeclared seedsに含める
- `F` と `M` に同じparse／read taintを持たせる
- `F` を `proof.failed` に置く
- root `record_ids = [F, M]`
- edgeは `root → M / file_all_records`
- downstream edgeは `M → F / file_all_records`
- `root → F` は存在しない

この入力をfactoryとindependent revalidationの双方が受理し、File dispositionを `failed` としました。

### Trigger reachability

exact `cd0e876` で到達可能です。

current `derive_source_projection_v3` は、direct parse／read rootについて次を確認しています。

- root collectionが`files`
- `path_ref`からFileを解決できる
- File IDがroot `record_ids` に含まれる
- root kindがFile taintに含まれる

その後、generic witness graph上でFileへ同kindが到達することだけを確認します。したがって、rootからのdirect edgeがなくても、Module経由でkindが到達すれば受理されます。

lower-level `_causal_edge_is_allowed` は、same-path ModuleからFileへの `file_all_records` をshape上許可します。しかし `_record_edge_rule` はModule→File edgeを独立導出せず、full baselineの `derive_required_causal_edges` は各root seedに対してrootから直接edgeを生成します。

### In-scope impact

これは、unrelated Fileを任意に非公開へ落とす元P1とは異なります。Fileはrootのdeclared seedに含まれ、path／taint／reasonも一致しています。

しかし、SI-03が認定するdirect File failureについて、**submitted downstream reachabilityがroot-local seed witnessの代替になっています**。その結果、preserved baselineが要求するroot→seed構造を欠いたproofを受理します。

影響は次のとおりです。

- mandatory File seedの「direct root witness」が欠けても `failed` を成立させられる
- full baselineが生成しないModule→File edgeを、欠落root edgeの代用品にできる
- SI-N05のsource側causal omissionを見逃す
- SI-03 seamの「local witnessのみでありfull proofではない」という境界を、欠落proofの免除へ誤用する

### Blocking effect

`CG-SI03-001` はreviewerが分類したP1ではなく、parentが特定したmaterial coverage gapです。P severityを新設しません。

親policyはmaterial gapがseverityなしでもSI-03をblockし得ると定めています。本件はaccepted source witness guaranteeに直接関係し、current SHAで再現しているため、SI-03をblockします。attachments-bundle

### Violated authority and exact proposition

既存authorityから導かれる命題は次のとおりです。

1. File自身をmandatory seedから外してはならない。
2. parse／read rootのmandatory seedsにはsame-path File自身と従属recordが含まれる。
3. failure rootはdeclared seedへroot-origin edgeで到達し、その後にrecord間propagationを行う。
4. submitted seeds／causal／taintのsource-side omissionはSI-03のnegative acceptance対象である。
5. Module→File逆taintを新設してはならない。
6. full mandatory seed集合の独立導出と全downstream edge exactnessはSI-04が所有する。

RequirementはFileをmandatory seedとして維持し、mandatory seed／causal／taint省略をnegative caseとして挙げています。

Designは元のcausal規則を維持し、Module→File逆taintを追加せず、safe subsetでfull mandatory root／causalを迂回しないと定めています。

admission-v3は、parse／read rootのmandatory seedsに同path File自身と全従属recordを含め、submitted seedsを独立導出集合と一致させ、closed root／edge／taint meaningを維持すると定めています。

PlanはSI-03でmandatory seed／causal／taint省略のsource部分と偽owner原因を拒否しつつ、全mandatory proof completenessをSI-04へ残しています。

したがって、既存authorityが一意に要求する最小命題は次です。

> SI-03はseed集合自体を独立導出しなくても、submitted `failure_root.record_ids` とsubmitted root-origin edge projectionの局所correspondenceを検証しなければならない。各declared seedは、そのrootから直接、preserved canonical root ruleでwitnessされなければならない。

これはfull SI-04 proof derivationではありません。

### First incorrect fault layer

最初のfault layerは **implementation** です。

`source_owner_witness_kinds_v3` は現在、次の一方向だけを確認します。

- root-origin edge target ⊆ root declared seeds

不足しているのは逆方向です。

- root declared seeds ⊆ root-origin edge targets

第二のfault layerは **test coverage** です。既存testはFile seed、唯一のFile edge、File taintを個別に削除しますが、`root → Module → File` のalternate pathを試していません。

### Root cause

根本原因は、**root-origin certificationとgeneric graph reachabilityの混同**です。

root kindが最終的にFileへ到達した事実だけでは、そのFileがroot-local seed witnessを持つことを証明しません。

### Primary response route

`implementation-remediation`。

DesignまたはRequirementの意味変更は不要です。

### Preserved and changed guarantees

**Preserved**

- `record_ids` の正しさをSI-03で独立導出しない
- downstream causal edge集合全体をSI-03でexact derivationしない
- least-fixed-point taintをSI-04へ残す
- source locality／target／exportをSI-04へ残す
- shared `_causal_edge_is_allowed` を変更しない
- Module→File edgeを新しいcanonical edgeとして採用しない
- File taint／reason／disposition semanticsを変えない
- public API／schema／enum／data contractを変えない

**Enforcement change**

- declared seedはdirect canonical root-origin edgeなしではroot witness済みと扱われません。
- downstream pathはmissing root edgeの代用品になりません。

## `EC-SI03-001` — historical evidence overclaim

### Validity

evidence conflictはvalidでした。

旧 `20261002t062856z-disc-si03-source-inventory-reference-seam.md` は「無関係root原因の借用を拒否」と一般化していましたが、exact `d3cce1c` probeにより反証されました。

### Current status

current remediation Artifactは、この主張を明示的にsupersedeし、旧Artifact、初回fail、旧test結果を遡及編集せず保存しています。また、direct File経路は未閉鎖であると明記しています。

### Blocking effect and route

このevidence conflict単独は現在blockしません。

secondary routeは `documentation-correction` でしたが、current candidate上で実施済みです。canonical Requirement／Designの意味は変更していません。

# Integrated response design

## Smallest coherent response

current 5行guardを維持したうえで、同じroot-causeを反対方向から閉じます。

`source_owner_witness_kinds_v3` のroot-origin部分を、次の**局所的な双方向correspondence**として検証します。

1. root-origin edgeのtargetはdeclared seedでなければならない。
2. declared seedごとに、そのrootからのdirect root-origin edgeが一件なければならない。
3. root-origin edgeはpreserved baselineのcanonical root ruleを使用しなければならない。
4. その後のrecord-to-record propagationは現行どおりとする。

概念上のexpected projectionは次です。

```text
expected root-origin edges
  = each failure root
    × each submitted root.record_ids seed
    × TAINT_ROOT_RULES[root.kind]
```

actual root-origin edgesは `causal_edges` のうち `source_id` がfailure root IDであるものだけです。

ここでexact equalityを取る対象は、**submitted root declarationとsubmitted root-origin projectionの間だけ**です。

次は行いません。

- `record_ids` 自体の正しい完全集合を独立導出する
- downstream edge集合を独立導出する
- 全taint fixed pointを認定する
- locality、target、export、budget、Coreを認定する

したがって、SI-04の責任移転ではありません。

## Affected surfaces

| Surface | Expected change |
|---|---|
| `tests/contracts/next_source_inventory_v3_validation.py::source_owner_witness_kinds_v3` | root-origin edge projectionの双方向correspondence |
| `tests/contracts/test_next_source_inventory_v3.py` | direct File alternate-path negative、multiple-root control、既存positive回帰 |
| SI-03 implementation evidence Artifact | current gap、First Red、修復、結果、新SHAを記録 |
| Plan／Report current state | fresh review pendingとして更新 |

## Unaffected surfaces

- `tests/contracts/next_source_inventory_v3_reference.py`
- `tests/contracts/next_reference_validation.py::_causal_edge_is_allowed`
- full `derive_required_causal_edges`
- SourceAcquisitionSeal
- request-v2／response-v2
- schema／enum／profile／adapter version
- File／Project／Module record shape
- ID／digest／partition preimage
- public summary
- runtime、Node、OS、CLI
- ASSET policy
- diagnostics／stderr
- persistent data、migration、recovery

## Ordering and state transition

1. current `cd0e876` でdirect File alternate pathをtracked testへ移し、First Redを保存する。
2. local root-origin correspondenceを実装する。
3. focused Greenを得る。
4. adjacent same-root-cause sweepを実行する。
5. aggregate／static／docs checksを実行する。
6. explicit pathsだけをcheckpoint／pushする。
7. post-commit exact new SHAへchecksをbindする。
8. original base `ce0edaa...` からnew SHAまでfresh independent Code Review Strictを実行する。
9. pass後だけSI-03を閉じる。

## Expected mutations and non-mutations

**Expected mutation**

- malformed proofのrejection条件が一つ強化されます。
- direct File bypass inputは受理からbounded rejectionへ変わります。

**Expected non-mutation**

- 正規proofのFile disposition、safe Files、Project membership、counts、partition hashは変わりません。
- valid direct root→File／root→Module proofは引き続き受理されます。
- downstream Module→File edgeをSI-03で全面禁止する必要はありません。ただし、そのedgeはmissing root→File edgeを代替できません。

## Compatibility and operational boundaries

対象はtest-only reference seamの局所validationです。

- public API変更なし
- schema変更なし
- persisted data変更なし
- migrationなし
- runtime／operation変更なし
- security／privacy boundary変更なし
- rollback data処理なし

code revertは機械的には可能ですが、P1またはmaterial gapを再導入するため、gate closureとしては使用できません。

## Structural stop signals

次の場合はpatch chainingを停止します。

- accepted positive caseがdirect root→declared-seed edgeなしを正当なproofとして必要とする
- `failure_root.record_ids` の意味変更が必要になる
- shared `_causal_edge_is_allowed` の一般契約変更が必要になる
- full mandatory seed集合または全downstream edge derivationが必要になる
- Module→Fileを新canonical causal meaningとして採択する必要が生じる
- schema、enum、API、data、security、migration、compatibility、rollback、recovery、operationへ影響する
- 新state、dual gate、exception、shimが必要になる
- root causeを一文で説明できなくなる

同一invariantが別経路で再発しているため、File専用例外を追加するだけではなく、root-origin projectionの一つの局所correspondenceとして修正します。構造的signalがある場合はauthorityへ戻るというskill要件にも整合します。attachments-bundle

# Human decisions and authorization

## Parent authorization source

approved Planと現在のuser taskは、次を認可しています。

- accepted SI-03 contract内の一意なmeaning-preserving P0／P1 correction
- TDD
- required local verification
- explicit-path checkpoint
- normal push
- fresh independent re-review

analysis自体はread-onlyであり、新しいpermissionを生成しません。attachments-bundle

## Uniquely determined correction

次は既存authorityから一意に導けるため、human decisionなしで実行できます。

- root-origin edge targetとdeclared seedsの双方向correspondence
- direct File seedに対するdirect root-origin witness
- preserved canonical root ruleの使用
- exact current bypassのTDD
- same-root-cause completion sweep
- evidence update
- fresh re-review

このcorrectionはconsumer rights、risk、public contract、data、compatibility、operational burdenを変更しません。

## Human decisionを要する境界

次は今回のauthorization外です。

- full seed集合をSI-03で独立導出する
- full causal edge exactnessをSI-03へ移す
- least-fixed-point taintをSI-03へ移す
- shared v1 helperの意味を変える
- Module→File reverse taint／canonical edgeを新設する
- Requirement／Design／responsibility allocationを変更する
- public API、schema、enumを変更する
- security、privacy、data、migration、compatibility、rollback、recovery、operationを変更する
- ASSET policyを採択する

これらが必要になった時点で `design-decision-required` または `requirement-decision-required` へ切り替えます。

canonical wordingの変更案は提示しません。現行authorityは実装修復に十分です。

# Implementation handoff

## Authorization status

**実装handoffを認可します。**

認可範囲は、`RC-SI03-001` のroot-origin witness correspondenceを閉じる一つのbounded correctionだけです。

## Bounded objective

Failure rootのsubmitted `record_ids` とsubmitted root-origin causal edgesを局所的に一致させ、declared File seedをdirect root edgeなしで間接到達させるparse／read bypassを拒否します。

full mandatory proofは実装しません。

## Exact verified paths and symbols

### Modify

1. `tests/contracts/next_source_inventory_v3_validation.py`
   - `source_owner_witness_kinds_v3`

2. `tests/contracts/test_next_source_inventory_v3.py`
   - `test_owner_cause_cannot_borrow_a_root_from_an_independent_module`
   - `test_direct_file_failure_keeps_its_source_seed_edge_and_typed_taint`
   - direct File alternate-pathを明示する新しいfocused negative test

### Reference only; do not modify

3. `tests/contracts/next_reference_validation.py`
   - `TAINT_ROOT_RULES`
   - `_causal_edge_is_allowed`
   - `_record_edge_rule`
   - `derive_required_causal_edges`

baseline validatorは、declared seedごとにrootから直接edgeを生成し、その後にrecord間edgeを展開します。

## Ordered changes

1. **First Red**
   - exact current SHA `cd0e876410d494655b4a880543337274b9ffe948` を記録する。
   - parse／readそれぞれについて、File `F` とsame-path Module `M` をroot `record_ids`へ含める。
   - edgesを `root→M` と `M→F` のみにする。
   - `root→F` は置かない。
   - factory rejectionを期待するtracked testを追加する。
   - current codeでは受理されるため、genuine Redになることを保存する。
   - independent revalidationも現在passすることを証拠へ含める。

2. **Local implementation**
   - root IDごとにactual root-origin edgesを抽出する。
   - declared seed ID集合とactual root-origin target集合を比較する。
   - existing nonseed guardを維持するか、双方向exact checkへ統合する。
   - root-origin ruleがpreserved `TAINT_ROOT_RULES[root["kind"]]` と一致することを確認する。
   - existing `_causal_edge_is_allowed` を引き続き適用する。
   - downstream adjacency／kind propagationは変更しない。

3. **Focused Green**
   - parse／read bypassがbounded rejectionになる。
   - current nonseed A→B bypassも引き続き拒否される。
   - valid direct root→F／root→M positiveが通る。

4. **Adjacent completion sweep**
   - 同じFileへparse rootとread rootがあるcase
   - 同kind複数roots
   - 各rootが同じFileをseedとするcase
   - rootごとにdirect witnessが必要であること
   - wrong root-origin rule
   - same-path／different-path
   - factory／independent revalidation

5. **Aggregate verification**
   - current 314-selection相当＋新test
   - current 17-selection
   - Ruff
   - format
   - mypy
   - SpecDock
   - local links
   - `git diff --check`

6. **Checkpoint**
   - explicit in-scope pathsだけをstageする。
   - commit／push後のnew full SHAを取得する。
   - clean worktree、configured upstream、live branch tipを一致確認する。

7. **Fresh review**
   - base `ce0edaa8fe63e79523fe7ad1dcb4b0a39dc02dce`
   - headはnew repair full SHA
   - fresh one-shot independent conversation
   - old reviewer conversationへのfollow-upは行わない

## Explicit non-goals

- `record_ids` の独立導出
- full mandatory causal edge derivation
- downstream edge exactness
- least-fixed-point taint
- source locality
- target／selection／export
- record／entity budget terminal routing
- Core／public certification
- schema／API／enum追加
- reverse Module→File taint
- actual TS／Node／OS／CLI
- ASSET policy
- diagnostics／stderr
- unrelated P2／P3改善

## Preserved guarantees

- same owner chain
- full acquired inventory
- original taints
- exact File partition
- Project two-view semantics
- no child metadata authority
- no reverse taint
- existing IDs／hashes／KAT
- old v1／v2 bytes
- SI-04 responsibility

## Prohibited choices

- root `record_ids` をactual edgesに合わせて拡張または縮小する
- File／Module taintを削除する
- dispositionを変更してtestだけ通す
- Module→Fileを新canonical edgeとして採択する
- shared helperを変更する
- schema／state／enum／diagnosticを追加する
- missing root edgeをspecial-case booleanで免除する
- full proof passを主張する
- reviewer recommendationだけをauthorityとして扱う
-旧evidenceを遡及的に書き換える

## First-red evidence requirements

実装者が返すevidenceには、次を含めます。

- current SHA `cd0e876410d494655b4a880543337274b9ffe948`
- exact test node ID
- parse／readの各fixture
- root `record_ids`
- actual root-origin edges
- missing `root→F`
- present `root→M→F`
- expected rejection
- actual current admission
- factory result
- independent revalidation result
- terminal command、exit code、failure excerpt

## Stop-and-return conditions

次のいずれかで通常実装を停止します。

- verified path／symbolが想定と異なる
- accepted positive caseがmissing direct root→seed edgeを必要とする
- canonical root ruleが一意に決まらない
- lower-layer shared contract変更が必要
- full mandatory proof derivationが必要
- public API、schema、data、security、migration、compatibility、rollback、recovery、operation影響が発生する
- responsibility boundaryを変える必要がある
- local correspondence後も別経路で同じinvariantを破れる
- File専用例外またはdual gateなしでは解決できない

## Evidence destination and format

親workflowへ次を返します。

1. Issueの `artifacts/` 配下に、timestamped Markdown `disc` Artifact
   - group ID
   - source finding ID
   - First Red
   - implementation delta
   - preserved／changed guarantees
   - deviations
   - focused／aggregate results
   - exact new SHA
   - residual gaps

2. Workbenchのfresh review artifacts
   - raw JSON
   - complete log
   - artifact SHA-256
   - reviewer session／conversation provenance
   - model／thinking provenance
   - base／head full SHA
   - `review_status`

旧Artifactは削除または遡及修正せず、新Artifactでsupersede関係を記録します。

# Verification plan

## Supplied results

| Lane | Supplied result | Binding |
|---|---|---|
| GitHub branch identity | expected SHAとtipが完全一致 | `cd0e876410d494655b4a880543337274b9ffe948` |
| Source review | one P1、`review_status=fail` | `d3cce1cb42b3c6a00d7a8d8d2b9ee4dbed2406d1` |
| Nonseed First Red | extra root edgeあり3 casesがDID NOT RAISE | repair前tree |
| Nonseed Green | 6 passed | bounded repair tree |
| Current nonseed probe | control reject、extra nonseed root edge reject | exact `cd0e876` |
| Current direct File probe | parse／readともdirect root→Fileなしでadmit | exact `cd0e876` |
| SI-03＋adjacent | 314 passed | exact clean `cd0e876` |
| Old-domain／pointer | 17 passed | exact clean `cd0e876` |
| Static／docs | Ruff、format、mypy、SpecDock、links、whitespace pass | exact clean `cd0e876` |

current direct File出力は、parse／readの双方で `admitted=true`、`direct_root_file_edge=false`、`independent_revalidation=passed` です。

## Future obligations

| Verification | Required result | Required SHA binding |
|---|---|---|
| Direct File First Red | current admissionによりtracked testがfailure | `cd0e876410d494655b4a880543337274b9ffe948` |
| Focused Green | missing direct root→Fileをreject | new repair full SHA |
| Existing P1 regression | nonseed root edgeをreject | new repair full SHA |
| Positive control | direct root→F／Mをadmit | new repair full SHA |
| Multiple-root control | rootごとにdirect seed witnessが必要 | new repair full SHA |
| Wrong-rule control | canonical root rule以外をreject | new repair full SHA |
| Aggregate regression | current 314相当＋新tests | new repair full SHA |
| Old-domain regression | 17 pass | new repair full SHA |
| Static／docs | Ruff、format、mypy、SpecDock、links、whitespace | new repair full SHA |
| Repository identity | clean HEAD／upstream／live branch equality | new repair full SHA |
| Fresh review | P0=0、P1=0、`review_status=pass` | same new repair full SHA |

## Semantic checkpoints

- root-origin target集合とdeclared seed集合が一致する
- declared File seedはrootからdirectにwitnessされる
- canonical root ruleが維持される
- downstream pathはmissing root edgeを代替しない
- owner Module reason／taintは不変
- File reason／dispositionは不変
- Project safe projectionは不変
- partition hash／counts／KATは正常caseで不変
- full proof認定を主張しない

## Negative assertions

- root-origin nonseed targetを受理しない
- declared seedのdirect edge omissionを受理しない
- wrong root ruleを受理しない
- File seedをModule経由だけでdirect failedにしない
- root declarationを修復側で変更しない
- File taintを偽造しない
- reverse causal meaningを追加しない
- shared helperを変更しない
- schema／API／enumを追加しない
- SI-04の責任を前倒ししない

## Integration and runtime evidence

この修復のintegration boundaryは次です。

- real `SourceAcquisitionSeal`
- retained execution assets
- request-v2
- transport candidate
- synthetic semantic proof fixture
- factory
- independent revalidation

actual TS parser、Node process、OS、CLIはこのpartial reference unitのrequired evidenceではありません。probeがactual production behaviorを証明するとは扱いません。

## Rollback verification

修復はcode／testの局所deltaであり、persistent migrationやrecoveryは不要です。

ただしrollbackするとP1またはmaterial gapを再導入するため、rollback後の状態をSI-03 closureとして扱ってはなりません。

# Same-reviewer re-review obligations

このheadingの「Same-reviewer」は、親policyに従い、**同じspecialized Code Review Strict roleによるfresh independent one-shot review**を意味します。元conversationへのfollow-upではありません。

Review rangeは次です。

```text
ce0edaa8fe63e79523fe7ad1dcb4b0a39dc02dce..<new repair full SHA>
```

## Re-review map

| Source／group | Independent re-check | Expected disposition |
|---|---|---|
| `SI03-CR1-F1` / `RC-SI03-001` | root seedがAだけのときroot→Bを追加してもBへkindを伝播できない | expected closure |
| `CG-SI03-001` / `RC-SI03-001` | File FとModule Mがseedsでも、root→M→Fだけではdirect failureを成立させられない | expected closure |
| `CG-SI03-001` / `RC-SI03-001` | direct root→F／root→Mの正規parse／read caseが通る | expected closure |
| `EC-SI03-001` / `RC-SI03-001` | 新Artifactが旧overclaimをsupersedeし、履歴を保持している | expected closure |
| Responsibility boundary | full seed derivation／downstream exactnessがSI-04に残る | expected closure |
| Shared surfaces | helper、schema、API、ID、hash、taint meaningに不要な変更がない | expected closure |

## Completion sweep

fresh reviewerは、同じroot causeについて少なくとも次を確認します。

- `module_relation`
- `export_binding`
- `boundary_derivation`
- `parse_file`
- `read_file`
- root→declared Module
- root→declared File
- root→nonseed
- declared seedへのmissing root edge
- same Fileへのmultiple roots
- same kind multiple roots
- same-path／different-path
- wrong root rule
- downstream M→Fがmissing root edgeを代替しないこと
- factory
- independent revalidation
- current tests、KAT、counts、Project views

## Closure states

**Expected closure**

- current specific P1 bypassが閉じている
- direct File material gapが閉じている
- adjacent completion sweepで同じroot causeが残っていない
- `P0=0 / P1=0 / review_status=pass`

**Disproof**

- reviewerがcurrent triggerを到達不能と立証する場合。ただし、supplied exact probeと矛盾するため、具体的なcode pathまたはfixture invalidityの提示が必要です。

**Supersession**

- approved Requirement／Design変更がroot／seed／edge meaningを変更した場合だけです。その場合は通常修復closureではなく、人間判断と必要なfresh campaignへ戻ります。

**Still open**

- missing direct seed edgeの代替経路が残る
- valid positiveが壊れる
- full proof責任をSI-03へ移さなければ解決できない
- shared helper変更が必要
- fresh reviewがfail
- current SHAとtested／reviewed SHAが一致しない

# Parent workflow consequence

current candidate `cd0e876410d494655b4a880543337274b9ffe948` は、次の理由でSI-03 blockedです。

1. `CG-SI03-001` がcurrent SHAでvalidかつreachableです。
2. source-native P1の具体的repairはlocal evidence上成立していますが、fresh reviewer closureがありません。
3. 親policyが要求するcurrent `review_status=pass` をまだ得ていません。

親workflowが次に所有するconsequenceは、**bounded implementation-remediation → exact-SHA verification → fresh independent re-review** です。

前提条件は次のとおりです。

- direct File First Redをcurrent `cd0e876` にbindする
- local root-origin correspondenceだけを修復する
- current required checksをnew repair SHAで再実行する
- clean／pushed exact SHAを取得する
- original base `ce0edaa...` を維持してfresh reviewする
- P0／P1なし、passを得る

現時点ではhuman decisionは不要です。stop conditionが発生した場合だけ、人間判断へ戻します。

引き続きblockされるものは次です。

- SI-04 full Core reference
- SI-05 public／exact refs
- SI-06 diagnostics
- full A02
- cumulative A03
- production TypeScript／OS／CLI
- offline package
- Final Quality Gate
- Issue closure

本skillの外にある行為は、編集、test実行、Git操作、Artifact永続化、commit、push、review起動、Issue変更、workflow transition、closureです。これらはparent workflowが所有します。attachments-bundle

# Assumptions and unresolved evidence

| 種別 | 内容 | Invalidation／required action |
|---|---|---|
| Verified fact | final GitHub確認時のbranch tipはexact `cd0e876410d494655b4a880543337274b9ffe948` | branch移動時は全repository factを再検証 |
| Verified fact | current nonseed root-origin guardはexact codeに存在する | 後続変更時は再照合 |
| Verified fact | parse／read direct File alternate pathはcurrent probeで受理される | tracked First Redで再現し、fixture validityも確認 |
| Source-native classification | `SI03-CR1-F1` はP1のまま保持 | analystがseverityを変更しない |
| Unclassified gap | `CG-SI03-001` にP severityはない | fabricated severityを追加しない |
| Evidence limitation | 314／17／static／docs結果はparent supplied evidenceで、本分析では実行していない | parentがnew SHAで再実行 |
| Evidence limitation | probeはreal source ownerとsynthetic semantic proofを使用し、actual TS／Core／public runtimeを証明しない | 後続SI-04／A04 evidenceと混同しない |
| Evidence limitation | source reviewは`d3cce1c`だけをreviewし、`cd0e876`をreviewしていない | new repair SHAでfresh review |
| Evidence limitation | review JSON digest、logs、picker provenanceを本分析でraw bytesから再計算していない | parentの保存原本が不一致なら再収集 |
| Reasoned conclusion | submitted seedsとroot-origin edge projectionの局所exactnessは、Current authorityとpreserved baselineから一意に導かれる | accepted positive caseが反証した場合は実装停止 |
| Scope boundary | submitted seed集合自体の独立導出はSI-04 | SI-03で前倒ししない |
| Scope boundary | downstream causal edge exactnessとleast-fixed-point taintはSI-04 | local修復をfull certificateと表現しない |
| Residual risk | root-origin ruleのwrong-rule mutationが現行testsで未網羅の可能性がある | completion sweepへ追加 |
| Residual risk | multiple rootsが同一seedを共有するcaseの局所correspondenceが未網羅の可能性がある | completion sweepへ追加 |
| Historical conflict | 旧implementation evidenceの一般的closure主張は反証済み | current superseding Artifactを使用 |
| Stop condition | shared helper、schema、API、data、security、migration、compatibility、recovery、operation変更が必要になる | 通常修復を停止し、人間判断へ返す |
