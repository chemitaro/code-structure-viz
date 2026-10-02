# Binding and evidence completeness

## GitHub binding

GitHubコネクタで `chemitaro/code-structure-viz` の `iss-00008-generate-nextjs-component-snapshots` ブランチを直接取得し、branch tipが指定されたfull SHAと完全一致することを確認しました。他ブランチ、既定ブランチ、添付ファイル、過去会話へのフォールバックは行っていません。

| 項目 | 値 |
|---|---|
| Repository | `chemitaro/code-structure-viz` |
| Target branch | `iss-00008-generate-nextjs-component-snapshots` |
| Expected SHA | `b2a5fb2a89aa22a25e3b56e8b6f8905158b700f2` |
| Retrieved tip SHA | `b2a5fb2a89aa22a25e3b56e8b6f8905158b700f2` |
| Tree | `92a4627def17cd98d703724bbc16957e7d752c16` |
| Parent | `cd0e876410d494655b4a880543337274b9ffe948` |
| SHA comparison | exact byte-for-byte match |



Repository rootの `AGENTS.md` はexact refで取得を試みて404となり、同一commitのroot listingにも存在しませんでした。repository-specific authorityとしてはCurrent Requirement／Design／Plan、accepted ADR、v3 contractsを使用します。

## Evidence lineage and freshness

| 項目 | Binding |
|---|---|
| Current candidate | `b2a5fb2a89aa22a25e3b56e8b6f8905158b700f2` |
| Reviewed SHA | 同じ `b2a5fb2...` |
| Tested SHA | 同じ `b2a5fb2...` |
| Original SI-03 base／merge-base | `ce0edaa8fe63e79523fe7ad1dcb4b0a39dc02dce` |
| Cumulative review range | `ce0edaa8...b2a5fb2`、3 commits |
| Collection time | `2026-10-02T09:29:20Z` |
| Review source | ChatGPT Code Review Strict |
| Reviewer session | `issue8-si03-root-origin-review` |
| Reviewer conversation | `6abf731f-0108-83ee-a449-b4bd03cbfad1` |
| Raw review SHA-256 | `c43cff734592873afc6b53df3a45e8f568fc7b28912366c6b5a7e5c290c06289` |
| Source reviewer level | `extra-high`、argv／native meta／pickerで直接確認 |
| Analyst identity | `issue8-si03-source-owner-cause-adjudication` |
| Analyst continuity | `required-strict-github-connector-verificati-1401` へのsame-objective follow-up |
| Continuity distinction | reviewerとは別系統。旧Code Review conversationへのfollow-upではない |

Local HEAD、configured upstream、live branch SHAは一致し、current publication後もworktreeはcleanと記録されています。すべてのcurrent review、test、validation、probe laneは本分析前にterminalです。attachments-bundle

本分析では、source-native classification、claim validity、blocking effect、response route、authorizationを別々に判断します。P1という分類は自動的な変更命令ではなく、reviewer recommendationはauthorityでもauthorizationでもありません。attachments-bundle

## Current review and test alignment

Current source reviewは、同じexact SHA `b2a5fb2...` に対して次の一件を報告しています。

- Finding ID: `SI03-CR2-F1`
- Source-native classification: P1／priority 1
- Title: `type_nodeのModule参照がD/M閉包から漏れる`
- Location: `tests/contracts/next_source_inventory_v3_validation.py` lines 163–168
- Review status: `fail`
- P0／P2／P3: なし
- Reviewer-declared separate material coverage gap: なし

ReviewerはCurrent R/D/P、accepted ADR、v3 contracts、三つのSI-03 source／validation／test files、直接依存するowner／source／causal helperを確認しています。外部reviewer自身はローカルtestsを実行していません。attachments-bundle

Parent-supplied exact-current evidenceは次のとおりです。

| Lane | Result |
|---|---|
| SI-03＋隣接six-module selection | 328 passed、large-case relevant exclusionなし |
| 旧Python／SQLAlchemy goldens＋Current pointer | 17 passed |
| Ruff | pass |
| Format | 230 files pass |
| mypy | 188 sources pass |
| SpecDock | sync pass、validate 10 nodes |
| Focused type-reference probe | 8 cases terminal、4 defect admissionsを再現 |
| Repository identity | clean、pushed、HEAD／upstream／live SHA一致 |

これらはparent workflowが実行したsupplied evidenceです。本分析では再実行していません。attachments-bundle

## Batch completeness

本バッチは、`SI03-CR2-F1` の妥当性、到達可能性、scope内impact、fault layer、root cause、primary route、authorization、およびbounded implementation handoffを決定するために十分です。

Material itemsは次の二群です。

1. 先行するroot-origin witness群 `RC-SI03-001`
   - `SI03-CR1-F1`、source-native P1
   - `CG-SI03-001`、direct File witnessのseverityなしmaterial gap
   - `EC-SI03-001`、旧evidence overclaim
   - current candidateではbounded repairと回帰が実装済み

2. 現在のrecord-reference closure群 `RC-SI03-002`
   - `SI03-CR2-F1`、source-native P1
   - `CG-SI03-002`、全PropsTypeIR位置・全D/M viewを機械的に網羅するtest censusのseverityなしmaterial gap

SI-04が所有するfull mandatory seed／causal exactness、least-fixed-point taint、full type semantics、target／export／selection／locality、budget terminal routingは意図的なscope外です。actual TypeScript、OS process、CLI、package、whole A02／A03／Finalも後続gateであり、今回のmissing evidenceとして扱いません。Current authorityとscopeはpacketに明示されています。attachments-bundle

# Executive disposition

**Current candidate `b2a5fb2a89aa22a25e3b56e8b6f8905158b700f2` はSI-03 gateでblockedです。**

`SI03-CR2-F1` は妥当かつ到達可能なin-scope P1です。`prop.type_node` 内のrepository-scoped Module referenceが現在のD/M closure列挙から漏れ、次の不正candidateをfactoryとindependent revalidationの双方が受理します。

- proof-only／private PropからDに存在しないModuleへの参照
- public PropからDには存在するがMには存在しないproof-only Moduleへの参照

一方、次の二つは正規positiveです。

- public Propからpublic Moduleへの参照
- private PropからD内のproof-only Moduleへの参照

Focused probeはflat referenceと`array.element`の双方でこの区別を再現しており、4件の不正admissionと4件のcontrol admissionがすべてcurrent codeを通過しています。attachments-bundle

最初に誤っているfault layerは **implementation** です。SI-03が、旧taint／causal処理向けの `_record_references()` を「すべてのrepository record referenceを列挙するhelper」として再利用しています。しかし同helperはPropについて `owner_id` だけを返し、`type_node` の再帰的Module referenceを列挙しません。現行のprivate D closureとpublic M closureはこのhelperに依存しています。

Primary response routeは **`implementation-remediation`** です。

既存authorityは次を明確に要求しています。

- private semantic referencesはDへ閉じる
- public referencesはMへ閉じる
- SI-N08でprivate dangling／public-to-proof-onlyを拒否する
- この局所reference closureはSI-03の責任である
- full type grammar validationおよびfull Core certificationはSI-04に残す

したがってRequirement／Design変更や責任再配分は不要です。shared legacy helperを変更せず、SI-03固有のcomplete closure-reference enumeratorを追加するbounded correctionが一意に導かれます。

親Planは、この意味を変えないin-scope P1修復、TDD、検証、checkpoint／normal push、fresh independent re-reviewを既に認可しています。human decisionは現時点で不要です。

Safe progressは可能ですが、次の範囲に限られます。

1. v3-local record-reference列挙の実装
2. PropsTypeIR全positionとD/M viewのTDD
3. required regression／static／docs checks
4. exact new SHAへのpost-commit binding
5. original base `ce0edaa...` からのfresh one-shot Code Review Strict

fresh current reviewが `P0=0 / P1=0 / review_status=pass` を返すまで、SI-04へ進めません。Material coverage gapもP severityを捏造せずgateをblockし得るというshared semantic coreに従います。attachments-bundle

# Root-cause groups

## Group map

| Group ID | Material item | Source-native classification | Current status | Blocking |
|---|---|---|---|---|
| `RC-SI03-001` | `SI03-CR1-F1`: seed外root-origin edgeで別Moduleへroot kindを伝播 | P1 | current candidateで修復・回帰済み。現reviewで再指摘なし | 単独のcurrent blockerではない |
| `RC-SI03-001` | `CG-SI03-001`: direct File seedを間接経路だけでwitnessできる | severityなしmaterial gap | current candidateでdirect seed edge／canonical rule対応を実装・検証済み | 単独のcurrent blockerではない |
| `RC-SI03-001` | `EC-SI03-001`: 旧Artifactのunrelated-root rejection過大一般化 | severityなしevidence conflict | superseding evidenceでreconcile済み | いいえ |
| `RC-SI03-002` | `SI03-CR2-F1`: nested PropsTypeIR Module referenceがD/M closureから漏れる | P1 | valid／reachable／current | はい |
| `RC-SI03-002` | `CG-SI03-002`: retained PropsTypeIRの全nested positionと4 viewのcoverage censusが未実装 | severityなしmaterial gap | current | はい |

## Group separation

`RC-SI03-001` と `RC-SI03-002` は統合しません。

- `RC-SI03-001` のinvariantは、failure rootとdeclared seed／canonical root-origin edgeのcorrespondenceです。
- `RC-SI03-002` のinvariantは、semantic recordが保持するrepository record referencesの完全列挙とD/M closureです。

両者はともにSI-03 admissionの局所完全性に関係しますが、データ構造、fault location、修復surface、verification matrixが異なります。共通groupへ統合すると、causal witnessとsemantic reference closureを一つのhelperまたはfull-proof gateへ誤って集約する危険があります。

## Deliberate non-grouping

次はsemantic root-cause itemへ分類しません。

- 途中probeのfixture spelling errorやschema abort
- 過去のunknown／lost job
- pre-commit tree-aligned checks
- actual TS／OS／CLI未実行
- SI-04以降の未実装surface

これらはcurrent P1の原因ではなく、mechanical historyまたは明示されたfuture scopeです。

# Detailed adjudication

## `RC-SI03-001` — prior root-origin witness obligations

### Current adjudication

先行 `SI03-CR1-F1` は当時のcandidateに対してvalidなP1でした。failure rootのdeclared seed外へroot kindを伝播でき、別Moduleとowner Fileを任意に非公開側へ落とせたためです。

その後のbounded repairsは次を追加しています。

- root-origin targetがdeclared seed外ならreject
- 各declared seedにroot-origin edgeを要求
- canonical root ruleとのjoin
- direct File root→File witness
- wrong-rule negatives
- same-kind／mixed multiple-root hardening

current reviewerはwhole cumulative rangeを確認し、root-origin群をcurrent findingとして報告していません。packet上も、current candidateでは先行obligationsのFirst Red→Greenと回帰結果が完了しています。attachments-bundle

### Blocking effect

`RC-SI03-001` はcurrent primary blockerではありません。

ただし、SI-03全体のformal closureはcurrent reviewがfailであるため未成立です。次回fresh reviewでは同groupをregression completion sweepへ含めます。これは新たな修復要求ではなく、closed invariantの再発防止義務です。

### Violated authority and fault layer

当時違反していたauthorityは、偽owner原因拒否、mandatory File seed維持、original root／causal／taint semanticsでした。最初のfault layerはimplementation、その次がtest coverageでした。

### Primary response route

歴史的primary routeは `implementation-remediation` で、current candidateに実装済みです。追加のimplementation handoffはありません。

### Preserved guarantees

- full acquired inventory
- original record-level taint
- no Module→File reverse taint
- schema／enum／ID／hash／preimage
- SI-04 responsibility
- existing root-rule vocabulary

### Current residual obligation

fresh reviewerが、current reference-closure修復によってroot-origin guardsが弱体化していないことを再確認する必要があります。

## `RC-SI03-002` / `SI03-CR2-F1`

### Claim validity

**Validです。**

Current `derive_source_projection_v3` は、full private viewについて各recordの `_record_references(record)` がD内に閉じること、public modelについて同helperの結果がM内に閉じることを検証します。

しかしshared `_record_references()` はPropについて `owner_id` だけを返し、`type_node` に埋め込まれたrepository Module referenceを返しません。同helperのdocstringと既存利用箇所は、主に「recordがtaintedな場合にunsafeになるdeclared references」を表しており、complete semantic-reference censusとは異なる役割です。

そのため、次のrecordはshape、ID再計算、通常owner closureを満たしたままD/M closureだけを回避できます。

- private Prop → nonexistent Module
- public Prop → proof-only Module

さらにProp identityは`type_node`全体をidentity preimageに含めないため、record IDの再計算だけではこの漏れを検出できません。current reviewはこの経路をP1として報告しています。attachments-bundle

### Trigger reachability

**Reachableです。**

Exact current SHAのfocused probeは次の8 casesを通しています。

| Prop view | Target Module view | Flat | `array.element` | Expected |
|---|---|---:|---:|---|
| public | public M | admitted | admitted | valid positive |
| private／proof-only | missing from D | admitted | admitted | defect |
| private／proof-only | proof-only in D | admitted | admitted | valid positive |
| public | proof-only in D, absent M | admitted | admitted | defect |

Factoryとindependent revalidationの双方が全8 casesを受理しています。既存owner-cause guardが原因を覆い隠さないよう、proof-only Module側には正規のnonFile failure witnessが構成されています。attachments-bundle

### In-scope impact

この欠陥は、owner-closed safe subsetへ次を通します。

1. private proof graphに存在しないModuleを参照するProp
2. public modelから非公開Moduleを参照するProp
3. closure済みと表示されるが、実際にはDまたはMに閉じていないrecord graph

public Propからproof-only Moduleへの参照は、public modelだけでは解決できないため、consumer側のclosed public graph保証を破ります。private danglingはfull proofの内部整合を破ります。

これは単なる型意味の精度問題ではなく、SI-03が明示的に所有するrecord-reference closureの欠落です。

### Blocking effect

Source-native P1をそのまま保持します。

親policyではvalid P1がSI-03をblockし、fresh current `review_status=pass` までSI-04へ進めません。current local testsがすべてpassしていても、missing negative coverageによってP1 triggerが到達可能である以上、blockは解除されません。

### Violated authority and exact proposition

違反する命題は次のとおりです。

> Full private discovered view内のすべてのrepository record referenceはDへ閉じ、public model内のすべてのrepository record referenceはMへ閉じなければならない。

Requirement SI-REQ-003はpublic referencesをpublic集合へ閉じることを要求し、negative acceptanceにはprivate danglingおよびpublic proof-only reference rejectionが含まれます。Current PlanではSI-N08がSI-03 scopeへ明示的に割り当てられています。

`next-semantic-admission-v3.md` も、private semantic referencesはD、public referencesはMへ閉じることをaccepted targetとして定めています。

### First incorrect fault layer

**Implementation**です。

具体的には、次の二つの意味を同じhelperへ重ねたことが誤りです。

1. legacy `_record_references`
   record-level taint／causal dependencyに使用する限定的reference集合

2. SI-03 closure-reference census
   recordが保持するすべてのrepository record IDs

第二のfault layerはtestです。既存 `test_references_close_in_the_correct_public_or_private_view` はComponent→Moduleの通常top-level referenceを検証していますが、Propのnested PropsTypeIR referenceを検証していません。

Requirement、Design、Planの矛盾ではありません。

### Root cause

**Semantic contract overloadingと、closed PropsTypeIRに対する不完全なreference census**です。

SI-03はshared helperをshape互換だから再利用しましたが、そのsemantic contractがclosure検証に十分かを分離しませんでした。結果として、ordinary owner referencesは閉じてもnested repository Module referencesが漏れました。

### Reviewer recommendation adjudication

Reviewer recommendationは**採用しますが、次のように限定します**。

採用する内容:

- recursiveなcomplete record-reference enumeration
- private dangling negative
- public-to-proof-only negative
- all retained PropsTypeIR reference positionsのcensus

採用しない拡張:

- shared `_record_references()` の意味変更
- full `_validate_type_node()` をSI-03 admissionへ移すこと
- type grammar、type identity、taint／causal semanticsの変更
- external／trusted referenceをrepository record IDとして扱うこと
- SI-04 full semantic validationの前倒し

### Primary response route

`implementation-remediation`。

Accepted authorityは明確で、current implementationが違反しています。shared skillのroute定義にも一致します。attachments-bundle

### Preserved guarantees

- existing PropsTypeIR grammar
- existing Module／Prop IDsとpreimages
- old v1／v2 taint and causal meanings
- `_record_references()` の既存consumer behavior
- external／trusted module string semantics
- source owner、File partition、Project views
- schema、wire version、profile、adapter version
- public API、diagnostics、data、compatibility
- SI-04 responsibility

### Changed enforcement

repository-scoped Module IDsを持つPropsTypeIRのすべてのnested positionが、private Dまたはpublic M closureの対象になります。

## `RC-SI03-002` / `CG-SI03-002`

### Classification

P severityは付与しません。これはseverityなしのmaterial coverage gapです。

### Gap

Focused probeはflat referenceと`array.element`を再現していますが、retained closed PropsTypeIRには他の再帰位置があります。

- reference type arguments
- tuple element
- tuple rest
- function `this_type`
- function parameter type
- function return type
- union members
- intersection members
- object property type
- object index-signature value type
- object call-signature `this_type`
- object call-signature parameter type
- object call-signature return type

既存full semantic validatorはこれらのclosed positionsを再帰走査していますが、SI-03 closure seamはその完全なcensusを持っていません。

### Blocking effect

一つのflat／array caseだけを修復しても、同じinvariantが別variantから再発します。shared semantic coreは、同じinvariantが別経路で繰り返す場合にpatch chainingを止め、root cause単位のcoherent responseを要求します。attachments-bundle

したがって、全closed grammar positionと全viewのtest censusが揃うまで、`RC-SI03-002` は閉じません。

# Integrated response design

## Smallest coherent response

SI-03 validation module内に、**v3-local complete closure-reference enumerator**を追加します。

概念上は二層です。

1. record-level enumerator
   - existing `_record_references(record)` からordinary owner／relation referencesを取得
   - `record["kind"] == "prop"` の場合にPropsTypeIR repository Module referencesを追加

2. type-node enumerator
   - closed `kind` discriminatorに基づくexplicit dispatch
   - `scope == "repository"` のreferenceだけからModule record IDを収集
   - closed child positionsへ再帰
   - external／trusted module stringsは収集しない

そのenumeratorを、`derive_source_projection_v3` の次の両方で使用します。

- private resolved records → D closure
- public model records → M closure

## Why local rather than shared

Shared `_record_references()` はold taint dependency、causal rule、legacy semantic validationから利用されています。その意味を「すべてのnested record reference」へ広げると、旧taint closureやcausal behaviorが変わる可能性があります。

したがって、current correctionは次を行いません。

- shared helperの変更
- shared helperへのoptional mode追加
- caller-dependent dual semantics
- full type validatorの呼出し

v3-local helperによって責務を分離するのが最小です。

## Explicit grammar traversal

実装はgenericなdict／list全走査にしてはなりません。generic scanは、type name、external module string、literal、property nameなどをrecord IDと誤認する可能性があります。

現行closed grammarのchild positionsをexplicitに扱います。

| Kind／position | Recurse or collect |
|---|---|
| repository reference | canonical Module IDをcollect |
| reference type arguments | 各argumentへrecurse |
| array | `element`へrecurse |
| tuple | 各element typeおよびrestへrecurse |
| function | `this_type`、parametersのtype、`return_type` |
| union | members |
| intersection | members |
| object property | property type |
| object index signature | `value_type` |
| object call signature | `this_type`、parameter types、`return_type` |
| primitive／literal等のleaf | empty set |
| external／trusted reference | record refをcollectしない |

Field名とleaf kind集合は、実装前にcurrent `_validate_type_node()` とcurrent schemaから機械的にcensusし、独自に推測してはなりません。

## Affected surfaces

1. `tests/contracts/next_source_inventory_v3_validation.py`
   - `derive_source_projection_v3`
   - 新しいv3-local helper

2. `tests/contracts/test_next_source_inventory_v3.py`
   - existing public／private reference closure tests
   - PropsTypeIR reference position／view matrix

3. New implementation evidence Artifact
   - current review、First Red、delta、checks、new SHA、residual scopeを記録

## Unaffected surfaces

- `tests/contracts/next_source_inventory_v3_reference.py`
- `tests/contracts/next_reference_validation.py::_record_references`
- `tests/contracts/next_reference_validation.py::_validate_type_node`
- schemas
- Current Requirement／Design／Plan
- accepted ADR
- ID／digest／partition preimage
- root-origin witness implementation
- source File partition／Project projection
- runtime、Node、OS、CLI、package
- ASSET policy
- diagnostics／stderr
- persistent data／migration／recovery

## State transition

1. exact current `b2a5fb2` でfocused tracked First Redを作成
2. v3-local complete enumeratorを追加
3. private D／public M closureで使用
4. all-view／all-position focused Green
5. root-origin and ordinary-reference regression
6. aggregate／static／docs checks
7. checkpoint／normal push
8. post-commit exact SHA checks
9. original baseからfresh one-shot Code Review
10. pass後にのみSI-03 closure

## Expected mutations

- private dangling PropsTypeIR Module referenceはrejectされる
- public-to-proof-only PropsTypeIR Module referenceはrejectされる

## Expected non-mutations

- public-to-public referenceはadmit
- private-to-proof-only D referenceはadmit
- external／trusted referencesはrecord closure対象にならない
- record ID、model digest計算規則、type semanticsは不変
- valid source／owner／partition outputsは不変
- root-origin testsは不変

## Compatibility and operational boundaries

この変更はtest-only reference seamのvalidation strengtheningです。

- public API変更なし
- wire／schema変更なし
- persistent data変更なし
- migrationなし
- runtime／operation変更なし
- rollback data処理なし
- security／privacy model変更なし

Git revertは技術的には可能ですが、P1を再導入するためgate closureには使用できません。

## Structural stop signals

次のいずれかが発生した場合は局所修復を停止します。

- shared `_record_references()` の意味変更が必要
- `_validate_type_node()` のfull semantic validationをSI-03へ移す必要
- PropsTypeIR grammarまたは`scope` meaningの変更が必要
- external／trusted referenceをrecord IDへ再分類する必要
- Prop ID／preimage変更が必要
- schema／wire／API変更が必要
- full Core／taint／causal責任をSI-03へ移す必要
- type-node以外の未定義nested reference conceptを新設する必要
- public、security、data、compatibility、migration、recovery、operation意味が変わる

これらは通常のimplementation remediationではなく、人間判断の境界です。

# Human decisions and authorization

## Authorization source

Current Planおよび継続中のuser taskは、既存authorityから一意に導かれる意味不変のSI-03 P1 correction、TDD、verification、explicit-path checkpoint、normal push、fresh reviewを認可しています。分析およびseverity自体は新しいpermissionを作りません。attachments-bundle

## Autonomously authorized correction

次は既存authorityから一意に決まるため、人間判断なしで進められます。

- PropsTypeIR内のrepository-scoped Module referencesを完全列挙する
- ordinary record refsとunionする
- private D／public M closureに使用する
- four-view matrixを検証する
- retained closed grammarの全nested positionsをtestする
- shared helperとfull type validatorを不変に保つ

このcorrectionはconsumer rights、risk、public contract、operational burden、responsibility allocationを変更しません。

## Human decision required boundary

次の場合は実装せず、人間判断へ戻します。

- complete reference closureのsource of truthをshared helperへ移す
- old taint／causal semanticsを変更する
- type grammar／scope semanticsを変更する
- PropsTypeIR内のexternal／trusted referencesをrecord identityへ変える
- Prop IDまたはtype identity algorithmを変更する
- public schema／API／wireを変更する
- data／migration／compatibility／rollback／recovery／operationを変更する
- SI-03とSI-04の責任を再配分する

canonical wordingの変更案は提示しません。現行authorityはbounded implementationに十分です。

# Implementation handoff

## Authorization status

**実装handoffを認可します。**

## Bounded objective

SI-03 source/proof reference seamにおいて、Propが保持するclosed PropsTypeIR内のrepository-scoped Module IDsを完全に列挙し、private recordsではD、public recordsではMへのclosureを検証します。

旧taint／causal helper、full type validation、schema、ID、public contractは変更しません。

## Exact verified paths and symbols

### Modify

1. `tests/contracts/next_source_inventory_v3_validation.py`
   - `derive_source_projection_v3`
   - private D closure
   - public M closure
   - v3-local type／record reference helperを追加

2. `tests/contracts/test_next_source_inventory_v3.py`
   - `test_references_close_in_the_correct_public_or_private_view`
   - 新規parameterized PropsTypeIR closure tests
   - 必要に応じてtype-node fixture builder

### Reference only — do not modify

3. `tests/contracts/next_reference_validation.py`
   - `_record_references`
   - `_validate_type_node`

4. `docs/contracts/next-semantic-admission-v3.md`
   - D／M closure
   - SI-N08

候補helper名は非canonicalです。

- `_type_node_repository_module_references_v3`
- `_record_closure_references_v3`

名前は既存命名規則に合わせて実装者が決定できますが、役割を混合してはなりません。

## Ordered changes

### 1. First Red on exact current SHA

Exact base:

`b2a5fb2a89aa22a25e3b56e8b6f8905158b700f2`

Probeの4 defect classesをtracked testsへ移します。

| Prop view | Target view | Expected |
|---|---|---|
| private／proof-only | Module absent from D | reject |
| public | Module proof-only in D, absent from M | reject |

各caseを、少なくとも次のpositionsでparameterizeします。

1. flat repository reference
2. reference type argument
3. array element
4. tuple element
5. tuple rest
6. function `this_type`
7. function parameter
8. function return
9. union member
10. intersection member
11. object property
12. object index-signature value
13. object call-signature `this_type`
14. object call-signature parameter
15. object call-signature return

Current codeがこれらのnegativeを受理するため、testはFirst Redになります。

### 2. Positive controls

同じposition matrixで次を維持します。

| Prop view | Target view | Expected |
|---|---|---|
| public | Module in M | admit |
| private／proof-only | Module proof-only in D | admit |

加えて次を確認します。

- external referenceはrecord membershipを要求しない
- trusted referenceはrecord membershipを要求しない
- multiple repository referencesは全件collectされる
- duplicate referencesはsetとして安定する
- leaf type nodesは空reference集合
- ordinary Component→Module closureは維持される

### 3. Implement local exhaustive walker

- explicit `kind` dispatchを使用
- current closed grammarのchild fieldsだけを再帰
- repository scopeだけModule IDをcollect
- external／trusted stringsは無視
- unknown kindを暗黙にempty扱いしない
- generic dict／list scanを使用しない

### 4. Implement record closure helper

- ordinary refsはexisting `_record_references(record)` から取得
- Propの場合だけtype-node refsを追加
- legacy helper自体は変更しない

### 5. Replace SI-03 closure calls

`derive_source_projection_v3` のprivate D／public M両方でlocal complete helperを使用します。

### 6. Focused Green

- all negative matrix rejects
- all positive matrix admits
- factoryとindependent revalidationの双方で一致
- error reasonは既存 `proof_references` boundaryを維持
- 新public diagnostic／codeは追加しない

### 7. Aggregate checks

- SI-03＋隣接six-module selection
- 旧Python／SQLAlchemy＋Current pointer
- Ruff
- format
- mypy
- SpecDock sync／validate
- Artifact local links
- `git diff --check`

### 8. Checkpoint and exact-SHA binding

- explicit in-scope pathsだけをstage
- normal commit／push
- new full SHAを取得
- clean worktree確認
- HEAD／upstream／live branch tip一致
- required checksをpost-commit exact new SHAで再実行

### 9. Fresh review

Review range:

`ce0edaa8fe63e79523fe7ad1dcb4b0a39dc02dce..<new repair full SHA>`

旧reviewer conversationへfollow-upせず、fresh independent one-shotを使用します。

## Explicit non-goals

- full PropsTypeIR semantic validation
- type depth／node budget enforcementの移動
- full mandatory root／causal exactness
- least-fixed-point taint
- target／export／selection／locality
- Core／public certification
- shared helper変更
- schema／wire／enum／diagnostic追加
- Prop identity変更
- runtime／Node／OS／CLI
- ASSET policy
- unrelated P2／P3改善

## Preserved guarantees

- same source seal／request／assets owner
- full inventory
- owner-closed Option A
- File partition／Project two views
- root-origin repairs
- old taint／causal semantics
- PropsTypeIR grammar
- external／trusted meaning
- IDs／hashes／preimages
- old Python／SQLAlchemy bytes
- SI-04 responsibility

## Prohibited choices

- `_record_references()` を直接拡張する
- `_validate_type_node()` をSI-03から呼び出してfull admissionを代替する
- arbitrary recursive scanを使う
-すべての`module`文字列をrecord IDとして扱う
- external／trusted refsをD/M membershipへ結合する
- invalid candidateをtest fixture側で削除してGreenにする
- Prop IDへtype contentを追加する
- schema／profile／adapter versionを変更する
- current P1をSI-04へ先送りする
- reviewer recommendationだけをauthorityとして扱う

## First-red evidence

Implementation evidenceには次を記録します。

- exact base SHA
- test node IDs
- PropsTypeIR position
- Prop public／private state
- target ModuleのD／M state
- expected rejection
- actual current admission
- factory result
- independent revalidation result
- command
- terminal exit code
- failure excerpt
- current probeとの対応

## Stop-and-return conditions

次のいずれかで通常実装を停止します。

- current schema／validatorのclosed grammarとpacketのposition censusが一致しない
- repository scopeのModule-ID fieldが一意でない
- Prop以外のrecordにも新たなnested repository referenceが見つかり、現行authorityから扱いが一意に決まらない
- shared helperまたはlower-layer contract変更が必要
- full type semanticsを実行しないとclosureを判定できない
- schema、API、ID、data、security、migration、compatibility、rollback、recovery、operationへ影響する
- current positive private-to-proof-only caseを維持できない
- root-origin／File partitionにunexpected regressionが出る

## Evidence destination and format

Parent workflowは次を保存します。

1. Issue `artifacts/` 配下のtimestamped Markdown `disc`
   - `RC-SI03-002`
   - `SI03-CR2-F1`
   - `CG-SI03-002`
   - First Red
   - implementation delta
   - grammar／view census
   - preserved／changed guarantees
   - checks
   - exact new SHA
   - residual scope

2. Fresh review artifacts
   - raw JSON
   - complete log
   - raw artifact SHA-256
   - reviewer session／conversation provenance
   - model／thinking provenance
   - base／head SHA
   - `review_status`

旧review、旧analysis、旧evidenceは遡及編集せず、new Artifactからsupersessionまたはclosure relationを記録します。

# Verification plan

## Supplied evidence

| Lane | Supplied result | SHA binding |
|---|---|---|
| GitHub identity | branch tip exact match | `b2a5fb2...` |
| Fresh current review | `SI03-CR2-F1` P1、fail | `b2a5fb2...` |
| Focused probe | 8 admissions、4 valid controls／4 defects | `b2a5fb2...` |
| Six-module regression | 328 passed | `b2a5fb2...` |
| Old-domain regression | 17 passed | `b2a5fb2...` |
| Static checks | Ruff／format／mypy pass | `b2a5fb2...` |
| Docs checks | SpecDock、diff／links pass | `b2a5fb2...` |
| Repository state | clean、pushed、HEAD／upstream／live一致 | `b2a5fb2...` |

Focused evidenceでは、private danglingとpublic-to-proof-onlyがflat／array双方でfactoryおよびindependent revalidationを通過しています。attachments-bundle

## Future verification obligations

| Lane | Required result | Binding |
|---|---|---|
| First Red | tracked negative matrixがcurrent codeでfail | exact `b2a5fb2...` |
| Focused Green | private dangling／public-to-proof-onlyを全positionsでreject | new repair SHA |
| Positive views | public→public、private→D-onlyを全positionsでadmit | new repair SHA |
| Scope controls | external／trusted refsにrecord membershipを要求しない | new repair SHA |
| Factory | expected admission／rejection | new repair SHA |
| Independent revalidation | factoryと同じ結果 | new repair SHA |
| Existing reference tests | ordinary Component／Module closure維持 | new repair SHA |
| Prior root-origin group | all current controls green | new repair SHA |
| Aggregate | current 328相当＋新tests | new repair SHA |
| Old domains | 17 pass | new repair SHA |
| Static／docs | all required lanes pass | new repair SHA |
| Identity | clean HEAD／upstream／live equality | new repair SHA |
| Fresh review | P0=0、P1=0、`review_status=pass` | same new repair SHA |

## Semantic checkpoints

- private repository refs ⊆ D
- public repository refs ⊆ M
- private Prop → D-only Moduleはvalid
- public Prop → D-only Moduleはinvalid
- private Prop → missing Moduleはinvalid
- repository scopeだけrecord IDsとしてcollect
- ordinary refsとnested type refsをunion
- root-origin and File partition invariants remain unchanged
- no full type or Core certification claim

## Negative assertions

- nested `array`だけのspecial caseにしない
- unknown grammar kindをsilent leafにしない
- external module stringをrecord IDとしない
- trusted module stringをrecord IDとしない
- shared taint helperを変えない
- full type validatorを再利用して責任を移さない
- record ID／preimageを変えない
- schema／API／wireを変えない
- public proof-only referenceを許さない
- private dangling referenceを許さない

## Integration／runtime evidence

このSI-03修復に必要なintegration boundaryは次です。

- real source acquisition／seal
- retained request／assets
- decoded transport candidate
- synthetic semantic proof input
- public factory
- independent revalidator

actual TS、Node、OS process、CLI、package evidenceはこのpartial reference seamのrequired verificationではありません。probeをproduction certificateとして扱いません。

## Rollback verification

変更はvalidation／testの局所deltaであり、persistent migrationやdata recoveryは不要です。

ただしrollbackするとP1を再導入するため、rollback状態をgate closureとして認めません。

# Same-reviewer re-review obligations

このheadingは、親policyに従い**同じspecialized Code Review Strict roleによるfresh independent one-shot review**を意味します。旧review conversationへのfollow-upではありません。

Review rangeは次です。

`ce0edaa8fe63e79523fe7ad1dcb4b0a39dc02dce..<new repair full SHA>`

## Finding／group map

| Source item | Group | Reviewer re-check |
|---|---|---|
| `SI03-CR2-F1` P1 | `RC-SI03-002` | all nested repository Module refsがD/M closure対象になったこと |
| `CG-SI03-002` unclassified gap | `RC-SI03-002` | retained PropsTypeIR全positionと4 viewのcompletion sweep |
| `SI03-CR1-F1` historical P1 | `RC-SI03-001` | nonseed root-origin edgeが引き続きrejectされること |
| `CG-SI03-001` historical material gap | `RC-SI03-001` | each declared seed direct witness／canonical root ruleが維持されること |
| `EC-SI03-001` evidence conflict | `RC-SI03-001` | current evidence chainが旧overclaimを正しくsupersedeしていること |

## `RC-SI03-002` completion sweep

Reviewerは少なくとも次を独立に確認します。

- flat repository reference
- reference type arguments
- array element
- tuple element／rest
- function this／parameter／return
- union／intersection
- object property
- object index-signature value
- object call-signature this／parameter／return
- multiple／duplicate references
- external／trusted references
- private dangling
- private to D-only positive
- public to public positive
- public to proof-only negative
- factory
- independent revalidation
- no shared helper mutation
- no full type admission transfer

## Closure status distinctions

**Expected closure**

- all invalid views reject
- all valid views admit
- prior root-origin invariants remain green
- no P0／P1
- `review_status=pass`

**Disproof**

Findingを反証するには、focused probeのcandidateがschemaまたはaccepted fixture contract上不正であり、D/M closureへ到達していないことを具体的に示す必要があります。現在のfactory／independent revalidation evidenceと矛盾するため、抽象的な反論では足りません。

**Supersession**

approved Requirement／Design変更がPropsTypeIR repository referenceまたはD/M closureの意味を変更した場合だけです。その場合は通常のrepair closureではなく、人間判断と必要なfresh campaignへ戻ります。

**Still open**

次のいずれかならstill-openです。

- 一つでもnested positionが漏れる
- private danglingまたはpublic proof-onlyが通る
- external／trusted positiveを壊す
- shared helper変更が必要
- full type semanticsをSI-03へ移す
- exact new SHAとtested／reviewed SHAが一致しない
- fresh reviewがfail

# Parent workflow consequence

Current `b2a5fb2a89aa22a25e3b56e8b6f8905158b700f2` はSI-03でblockedです。

次のparent-owned consequenceは、**bounded `implementation-remediation`、exact-SHA verification、fresh independent re-review** です。

前提は次のとおりです。

1. exact current SHAでtracked First Redを保存
2. v3-local complete closure-reference enumeratorを実装
3. full grammar／view matrixをGreen化
4. required aggregate／static／docs checks
5. explicit-path checkpoint／normal push
6. post-commit exact SHAへchecksをbind
7. original unit baseからfresh Code Review
8. `P0=0 / P1=0 / review_status=pass`

現時点でhuman decisionは不要です。分析objective、accepted scope、governing authority meaningは変わっていないため、新しいanalysis campaignも不要です。Code Review sessionだけはpolicyどおりfresh one-shotにします。

引き続きblockedなのは次です。

- SI-04 full Core reference
- SI-05 public／exact refs
- SI-06 diagnostics
- full A02
- cumulative A03
- actual TS／OS／CLI
- offline package
- Final Quality Gate
- Issue closure

本skillの外にある行為は、永続化、編集、test実行、Git操作、reviewer起動、Issue／thread変更、workflow transition、closureです。これらはparent workflowが所有します。attachments-bundle

# Assumptions and unresolved evidence

| 種別 | 内容 | Invalidation／required action |
|---|---|---|
| Verified fact | final GitHub確認時のbranch tipはexact `b2a5fb2...` | branch移動時は全repository factを再検証 |
| Verified fact | current review／tested SHAは同じ `b2a5fb2...` | 後続変更後はnew SHAへ再bind |
| Source-native classification | `SI03-CR2-F1` はP1のまま保持 | analystがseverityを変更しない |
| Unclassified gap | `CG-SI03-002` にP severityはない | severityを捏造しない |
| Supplied evidence | 328／17／static／docs resultsはparent実行記録 | 本分析では再実行していない |
| Supplied evidence | raw review digest／probe digest／picker provenanceはpacket由来 | 原本不一致時は再収集 |
| Verified behavior | flat／arrayの4 defect casesはfactory／revalidatorでadmit | tracked First Redで再現する |
| Reasoned conclusion | complete v3-local reference censusはexisting SI-N08から一意に導ける | exact grammar inspectionが矛盾を示した場合は停止 |
| Discovery prerequisite | helper実装前にcurrent closed PropsTypeIR kind／child-field censusを機械的に確定する | 独自推測でfieldを追加しない |
| Residual risk | packetで列挙されたpositions以外にrepository record IDを保持するclosed child fieldが存在する可能性 | `_validate_type_node`／schemaの全branch censusで確認 |
| Residual risk | Prop以外のrecord kindにnested repository record IDsが存在する可能性 | 発見時、既存closure命題から一意なら同groupへ追加。意味変更なら停止 |
| Preserved boundary | shared `_record_references` はtaint／causal helperであり、complete closure helperではない | shared semantic変更を行わない |
| Preserved boundary | full type grammar semantics、depth／node limits、Module existenceのfull admissionはSI-04 | SI-03修復をCore certificateと表現しない |
| Scope limitation | actual TypeScript／OS／CLI／packageは未認定 | 後続gateの証拠と混同しない |
| Stop condition | API、schema、ID、security、data、migration、compatibility、rollback、recovery、operationまたはresponsibility変更が必要 | ordinary remediationを停止し、人間判断へ返す |
