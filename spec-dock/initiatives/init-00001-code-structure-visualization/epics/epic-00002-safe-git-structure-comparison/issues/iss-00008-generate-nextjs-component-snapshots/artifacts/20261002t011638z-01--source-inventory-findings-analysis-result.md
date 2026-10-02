# Binding and evidence completeness

| 項目 | 判定 |
|---|---|
| Repository | `chemitaro/code-structure-viz` |
| Target branch | `iss-00008-generate-nextjs-component-snapshots` |
| Current candidate full SHA | `a4efdc373a515801777c924a1d14675fda686955` |
| Strict GitHub verification | GitHubコネクタのrepository metadata取得後、対象branch endpointを直接取得した。分析開始時と終了直前の2回とも、branch tipは期待SHAとbyte-for-byte一致した。他branch・default branchの内容にはフォールバックしていない。 |
| Reviewed/tested SHA alignment | packet上のcurrent candidate、reviewed SHA、focused evidenceおよび既存validationはすべて同じ`a4efdc373a515801777c924a1d14675fda686955`に結合されている。attachments-bundle |
| Review source | `chatgpt-spec-review-strict`、fresh independent specification review、reviewer session `issue8-source-inventory-spec-review`、terminal exit 0、schema-valid complete JSON、`review_status=fail`、source-native P1×1、P2/P3なし。 |
| Review artifact identity | `.workbench/luna-max-implement/issue8-nextjs-snapshots/specs/source-inventory-review-result.json`、packet記載SHA-256 `2fff0ab48628233db38a58ed86ae279ba8fb3dff95601a1e247d7efc3663676b`。添付packet内の完全JSONに末尾LFを含めて再計算した値がこのdigestと一致した。 |
| Reviewer provenance | session ID、conversation ID、prompt hash、thinking input `pro`、picker verification情報がpacketに記録されている。ただしpacket自身が明記する通り、UI evidenceでありbackend model identity attestationではない。 |
| Analyst provenance | 本応答はinitial fresh analystであり、reviewer・author・implementerとは別系統、follow-up継続ではない。native analyst session IDはこの実行環境から観測できず、推測していない。retained analyst transcriptはrepository factsの根拠に使用していない。 |
| Evidence freshness | `2026-10-02T01:02:22Z`。packet作成後に未完了のreview/test laneはないとされ、最終GitHub再検証でもbranch tipは不変だった。 |
| Packet completeness | accepted objective、scope、non-goals、blocking policy、authority、review全文、finding、local trace、focused falsification、既存validation、未実装範囲、親workflow境界が揃っており、今回の設計裁定には十分である。severity、claim validity、blocking、response route、authorizationを分離する必要があるというsemantic coreにも適合する。attachments-bundle |

**保持するmaterial gaps**

1. `.workbench`のreview artifactはGitHub repository contentsとしては取得できず、GitHubコネクタでは404だった。したがってworkbench fileのrepository追跡性は未確認である。ただし、添付packetに含まれる完全JSONのbytes digestは記載digestと一致しており、今回の意味分析に必要なreview内容は確定できた。
2. focused reproduction script自体のbytes/digestはpacketに含まれない。実行結果はpacketにあるが、harness実装は独立確認できない。ただし、同じ結論は対象branchの`_record_references`、root seed導出、causal edge導出、fixed point、`validate_model`、target exceptionを直接照合して再確認した。
3. Core-v3、schema、reference、actual TypeScript producer、source sealからpublic publicationまでのintegrationは未実装・未認定である。これは現在のdocs-only SI-02段階における明示済みの将来証拠であり、今回のP1を反証する既存behavior evidenceではない。packetもこれらを未立証として明示している。attachments-bundle
4. target未指定時の最終Core-v3 routingは確定していない。旧helperは全public program Fileを暗黙targetとして`missing`へ送るため、reviewer本文の「target無しでもnominal candidateが存在しない」という表現は限定が必要である。ただし、**別のexplicit safe target**を指定した再現だけでP1の到達可能性とblocking impactは成立する。

以上のgapは、実装handoffやclosureを阻むが、今回の設計矛盾の裁定を阻まない。

# Executive disposition

**SPEC-SI-P1-01は、source-native P1のまま有効である。** reviewerの主張は、target未指定の場合については限定が必要だが、explicitly selected safe targetと、それとは独立したFile上の正当な非File rootという到達可能な条件で再現する。その条件では、現在のaccepted targetが要求する次の三命題を同時に満たせない。

1. `F_safe = F − T`であり、`T`外のsafe Fileは全件公開する。
2. `T`内のModuleおよびそのproof-only semantic recordsは公開しない。
3. 公開program Fileには対応する公開Moduleがちょうど一つ存在する。

review全文はこの衝突をP1として報告し、`review_status=fail`としている。attachments-bundle 親policyではP0/P1またはunreliable coverageが仕様gateを止めるため、**SI-02は失敗のまま、SI-03以降の実装再開はblockされる**。ローカル反証や本分析だけではgateを閉じられない。

第一の誤りはproduct implementationやtestではなく、**canonical designが「record-level taint」と「公開modelを所有関係で閉じるためのFile publication eligibility」を同じ集合として扱ったこと**である。既存authorityから訂正内容は一意に決まらないため、primary response routeは次である。

**`design-decision-required`**

推奨は、旧taint graphを変更せず、公開projection側にprogram FileとModuleのowner closureを導入する案である。これにより既存のpublic File→Module保証、taint済みsemantic recordの非公開、無関係なsafe Fileのpartial-safe公開を維持できる。一方、現在の「`F−T`のFileは例外なく公開」という新保証は変更されるため、人間の明示判断なしには採用できない。

現時点で安全に進められるのは、設計選択とcanonical文書の再作成までである。schema、reference、test、production codeへの実装handoffは認可されていない。

# Root-cause groups

| Group ID | 含む項目 | Source-native classification | 共通invariant／root cause | Primary route | Blocking |
|---|---|---|---|---|---|
| `RG-SI-001` | `SPEC-SI-P1-01`、`GAP-SI-V3-EXEC-01` | findingはP1を保持。coverage gapにはseverityを新設しない | record単位のtaint closure `T`をそのままFile公開partitionへ流用した一方、公開modelはFile→Moduleのowner-complete projectionを要求する。Moduleを非公開にする合法経路と、そのowner Fileを非公開にする一般規則が結ばれていない。 | `design-decision-required` | 仕様gateと実装再開をblock |

`GAP-SI-V3-EXEC-01`は、新Core-v3/referenceが未実装で、どの解釈がproducer behaviorとして意図されているかを実行結果から補えないという証拠gapである。これはP1の原因ではないが、曖昧な設計をimplementation behaviorで解消したと主張できないため、`RG-SI-001`へ結合する。

次は独立groupにしていない。

- target未指定時の旧helper routingは、findingの一部表現を限定するだけで、explicit safe targetによる本質的矛盾を解消しない。
- actual TypeScript、OS、CLI、package、A03以降が未実装なのは現在の計画段階どおりであり、別のreview findingではない。
- P2/P3、required local gate failure、独立した別root causeは現packetに存在しない。
- `module_relation`、`export_binding`、`boundary_derivation`は別findingではなく、同じowner-closure欠落を通る複数triggerである。

# Detailed adjudication

## `RG-SI-001` / `SPEC-SI-P1-01`

### Claim validity

**有効。ただしtarget未指定の主張を限定する。**

accepted admission-v3は、Fileについて`F_safe = F − T`を定義して全件公開を要求し、同時に旧v1のclosed root/edge ruleとtaint fixed pointを維持し、公開program File→Module基礎規則も維持している。

対象branchのreference behaviorでは次が確認できる。

- `_record_references`はModuleからProjectへのreferenceを返すが、Moduleからowner Fileへのreferenceを返さない。
- `_derive_required_root_seed_ids`は`module_relation`、`export_binding`、`boundary_derivation`等のpath-local rootについてModuleやsemantic relationをseedにできるが、一般にowner Fileをseedへ含めない。
- `derive_required_causal_edges`と`_derived_taint_fixed_point`はそのclosed edge setだけを用い、Module→Fileの逆向きedgeを生成しない。
- `validate_model`は、公開される各program Fileについて同じproject/pathのModuleがちょうど一つ存在することを要求する。
- missing Module exceptionはtyped failureとなった**selected target**に限定される。別のsafe targetを選んだ場合、無関係なorphan program Fileは例外にならない。

したがって、program File `f`とそのModule `m`について次が成立する到達可能な入力がある。

```text
program(f)
owner(m) = f
f ∉ T
m ∈ T
```

現在の契約からは次が同時に導かれる。

```text
f ∈ F_safe          because f ∉ T
f ∈ public model    because all F_safe must be published
m ∉ public model    because m ∈ T
f ∈ public model ⇒ exactly one public owner Module
```

最後の二命題が矛盾する。

packetのfocused evidenceでも、3種類のrootすべてでFileはuntainted、Moduleはtainted、explicit safe target自体はtarget failureなし、しかしpublic model validationはunrelated `src/Card.tsx/missing`で失敗している。attachments-bundle

### Trigger reachability

立証済みの最小triggerは次である。

- 互いに独立したprogram File `src/Card.tsx`と`src/Button.tsx`がある。
- `src/Card.tsx`に正当な`module_relation`、`export_binding`または`boundary_derivation` rootがある。
- root/causal fixed pointはCard ModuleをtaintするがCard Fileをtaintしない。
- explicit targetはsafeな`src/Button.tsx`である。
- target exceptionはButtonにしか関係せず、Cardのmissing Moduleを許容しない。

target未指定の場合、旧helperは全program Filesを暗黙selected targetとしCardをtyped missing failureへ送る。これは「nominal Core-v3 candidateが絶対に存在しない」と断言する根拠には使えない。しかしexplicit safe target triggerだけでfindingはreachableである。

### In-scope impact

- SI-04が要求するfull proof／全root／causal／typed taintとpublic model validationを、一つのnominal Core-v3で閉じられない。
- accepted partial-safe objectiveにおいて、影響外のsafe targetを公開できるという保証が未定義になる。
- Project safe membership、File partition counts、partition fingerprint、published/proof-only counts、public references、JSON/PlantUMLのsame-Core projectionへ連鎖する。
- SI-02の唯一の出口であるschema-valid `review_status=pass`を満たさないため、SI-03以降は開始不可である。計画も、意味変更時はSI-01へ戻り、同一objectiveを再認証するよう要求している。

### Blocking effect

source-native classificationはP1のまま保持する。親の明示policyではP1がSpecification Review gateをblockする。severityから自動的にcode changeを認可することはない。

### Violated authority and exact proposition

主に満たせないauthorityは次である。

- `SI-REQ-002`: 全取得Fileをsafe／failed／excludedへ完全かつ排他的に分け、safe Fileの任意欠落を拒否する。
- `SI-REQ-003`: full inventory上のroot／causal／taintを独立検証し、公開recordと公開referenceをsafe集合へ閉じる。
- admission-v3: `F_safe = F−T`、safe File全件公開、旧causal規則維持、public program File→Module基礎規則維持。
- Current Design SI: safe Fileは必ず公開、full proof causal規則を維持し、File→Project逆edge等の無関係な新edgeを作らない。
- accepted ADR: full inventoryとsafe semantic subsetを分離し、File seed例外を作らず、safe Fileを任意に消さない。

正確なunsatisfied propositionは次である。

> 合法なfull-proof taintでowner Moduleだけがproof-onlyになったprogram Fileについて、Fileを必ず公開し、Moduleを必ず非公開にし、かつ公開program Fileごとに公開Moduleを必須とすることはできない。

### First incorrect fault layer

**Canonical design。**

高位objectiveである「全取得inventoryと公開safe semantic subsetを分離する」こと自体は実現可能である。矛盾は、admission-v3がFile安全性を`File record ∉ T`だけで定義した後、既存public modelのowner completenessを追加条件として接続しなかった箇所で初めて具体化する。

したがって、これは単なるdocumentation typoではない。次のいずれかを決める必要がある。

- File publication eligibilityのsource of truth
- Moduleとowner Fileの責任境界
- taint graphとpublication projectionの関係
- 公開File→Module consumer contract
- partial-safeとdomain unavailableの境界

### Root cause

**Record safetyとpublication structural completenessの混同。**

`T`はproof上のrecord到達性・causal taintを表す。一方、public modelには、個々のrecordがuntaintedかだけでなく、owner／reference／cardinalityが閉じていることが必要である。現設計には「Moduleがpublicでなければ、そのprogram Fileをpublic modelへ残せるか」という一般規則がない。

### Primary response route

**`design-decision-required`**

旧taint semanticsを変える、File partitionの意味を変える、またはpublic File→Module contractを変える必要があり、いずれもcanonical design meaningの変更である。`documentation-correction`、`implementation-remediation`、`test-remediation`、`finding-rebuttal`では閉じない。

### Guarantees

現在の全保証を同時に保存する訂正は存在しない。少なくとも次の一つを変更する必要がある。

- `F−T`の全Fileを公開する保証
- public program Fileには必ずModuleがある保証
- 既存のroot／causal／taint規則
- unrelated safe subsetを公開するpartial-safe availability

# Integrated response design

最小のcoherent responseは、root種類ごとの例外追加ではなく、**Fileのsource-level safetyとpublic modelへのpublication eligibilityを分離し、program FileとModuleを一つのowner-closed projectionとして定義すること**である。

## 推奨設計：owner-closed publication projection

full proof上のtaint集合は既存どおり`T_record`として保持する。そこから直接`F_public = F − T_record`とはせず、検証済みpublic semantic setとのowner closureを追加する。

概念上は次になる。

```text
source_safe(f) :=
    f is not directly failed
    and f is not record-tainted

module_public(f) :=
    exactly one Module owned by f is admitted to the public semantic set

public_file(f) :=
    source_safe(f)
    and (
        f is non-program
        or module_public(f)
    )
```

これにより、Moduleがproof-onlyのprogram Fileは取得inventoryとprivate proofには残るが、public modelとProject safe membershipからは除外される。無関係でModuleも安全なFileは引き続きpartial-safe公開できる。

## Affected surfaces

- Current Requirementの`SI-REQ-002`／`SI-REQ-003`
- accepted ADRのFile partitionおよびsafe subsetの説明
- Current Design SIのsafe File／Module対応
- `docs/contracts/next-semantic-admission-v3.md`
  - `F_safe`の定義
  - failed／excluded集合
  - disposition reasonの意味
  - Project safe membership
  - planned acceptance matrix
- `docs/contracts/next-semantic-v3.md`
  - `source_inventory_summary.safe.files`
  - proof-only counts
  - public coverageとの関係
- partition fingerprintの入力集合とknown literals
- future Core-v3/reference/schema/test
- target、selection、unsupported frontierによる合法Module omissionの扱い

## Unaffected surfaces

推奨案では次を変更しない。

- complete source sealと全取得Project/File ownership
- 旧v1/v2 record IDs、recognition、props、relations、Unicode、trusted declarations
- `_derive_required_root_seed_ids`等の旧root／causal／fixed-point semantics
- File seed省略禁止
- private proofでの全record accounting
- A runtime、macOS/Linux、static-only境界
- ASSET ordinary-I/O policy
- public proof-only reference禁止
- Python／SQLAlchemy既存bytes
- actual production readinessの認定条件

## Ordering and state transitions

1. 人間がpublication coupling ruleを採択する。
2. SI-01へ戻り、Requirement／ADR／Design／Plan／v3 contract docsを一貫して修正する。
3. docs-only local checksを実行し、clean/pushed exact SHAを作る。
4. same reviewer `issue8-source-inventory-spec-review`へStrict follow-upする。
5. schema-valid `review_status=pass`後にだけSI-03 source seamを開始する。
6. SI-04でfull Core、SI-05でpublic/exact-ref closureへ進む。

## Expected mutations and non-mutations

最初の修復commitはdocs-onlyであるべきで、`src`、既存v1/v2 schema、tests、fixtures、dependencies、goldensを変更しない。設計pass前にModule→File edgeやtarget exceptionを実装してはならない。

将来のreference実装では、推奨案を採る場合、proof taint graphではなく新v3 publication projectionでowner closureを導出する。rootごとの分岐、selected-target限定shim、missing Moduleの広域exceptionで症状を隠さない。

## Compatibility and operational boundaries

v3は未実装・未公開なので、既存出荷consumerへのmigrationは現時点では発生していない。ただしplanned profileの意味、partition fingerprint、known literalsは変化するため、profile identityをそのまま維持できるかはcanonical decisionで明記する必要がある。

rollbackは、new v3 profileをavailableとして公開せずtyped unavailableへ戻し、旧v1/v2 recordと既存domainを不変に保つ。旧v2へ意味の異なるsafe subsetをcastしてはならない。

## Structural stop signal

この問題は、非File rootだけでなく、selection-only Module exclusion、transitive taint、target routing等でも同じowner invariantとして再発し得る。rootごとのexceptionやtarget exceptionの拡張はpatch chainingになる。state ownerを一文で説明できる単一projection ruleが採択されるまで、実装へ進めない。

# Human decisions and authorization

## Parent authorization

親boundaryは、既存authorityから一意に導け、意味・保証・risk・public contractを変えない整合修正だけを自律対応可能としている。canonical meaning、public data、taint、ownership、compatibility、recoveryをmaterialに変える場合は人間判断へ戻す。attachments-bundle

次は既存authorityから一意に決まる。

- findingは有効でP1 blockingである。
- SI-03以降を開始してはならない。
- public modelにorphan program Fileを黙って通してはならない。
- tainted Moduleをclosure目的で公開してはならない。
- target failureで無関係なbase-model矛盾を隠してはならない。
- 旧v1/v2を変更して新v3の矛盾を解消してはならない。
- 意味変更後はSI-01へ戻り、same-reviewer再認証が必要である。

一方、**どの保証を変更するかは一意に決まらない。**

## Decision options

| Option | 内容 | 主に保存する保証 | 変更・喪失する保証 | 評価 |
|---|---|---|---|---|
| **A. Owner-closed publication projection** | taint graphは維持し、program Fileの公開をowner Moduleの公開成立にも依存させる | 旧taint semantics、public File→Module、safe refs、unrelated partial-safe、consumer構造 | `F−T`のFile全件公開、partition/reason/fingerprintの現draft意味 | **最推奨**。新v3 projection内で閉じ、既存lower layerとpublic consumerへの影響が最小 |
| B. Metadata-only public File | untainted FileはModuleなしでも公開し、明示state／coverageでsemantic unavailableを表す | `F−T`全件公開、旧taint semantics | public File→Module保証、consumer contract。新state/schema/migrationが必要 | 非推奨。公開surfaceとconsumer責任が大きく増える |
| C. Module→owner File taint | proof graphに逆edge、owner seedまたは同等規則を追加し、Fileを`T`へ入れる | `F_safe=F−T`式、public File→Module | closed root／causal意味、taint到達範囲、旧algorithm再利用保証 | 非推奨。transitive over-taintと旧baseline変更のriskが高い |
| D. Domain unavailable | 一件でもowner mismatchがあれば全domainをunavailableにする | 現在のtaint、partition式、public model cardinality | unrelated safe subsetのpartial-safe availability | rollback／fail-closed候補には使えるが、accepted objectiveの最終解としては弱い |

**いずれのoptionも現在の全保証を保存しない。** したがって単なるclarificationとして自律採択できない。

Candidate text — not adopted:

> `T_record`はfull resolved view上の既存root／causal規則から導出したrecord-level taint closureとする。公開program File集合は`F−T_record`だけでは決めず、source-safeであり、かつ同一project/pathのModuleがpublic semantic setへちょうど一件admitされたFileに限定する。source-safeだがrequired Moduleがproof-onlyまたは合法的に非公開となるprogram Fileは、全取得inventoryとprivate proof/accountingには保持し、public File集合および公開Project membershipから除外する。非program FileにはModule条件を適用しない。旧root／causal／taint規則、旧v1/v2 identity、およびpublic File→Module cardinalityは変更しない。

この候補を採る場合でも、人間は次を明示決定する必要がある。

1. owner Module非公開時のFile dispositionを既存`tainted`へ含めるか、新しい内部／公開reasonを導入するか。
2. selection-only／unsupported frontierによるModule omissionも同じowner closureへ含めるか。
3. target未指定時、explicit safe target時、selected failing target時の優先順。
4. planned profile ID `next-source-inventory-safe-subset-v1`を維持するか、新identityを必要とするか。
5. `source_inventory_summary.safe.files`がsource-safe Filesかpublic-model Filesか。
6. 既存の「safe File」の用語をsource safetyとpublication safetyへ分けるか。

# Implementation handoff

**No implementation handoff is authorized.**

現在のauthorityでは、実装者が選択すべき設計が一意に定まらない。handoffが存在できるのは、次の証拠がすべて揃った後である。

1. 人間がOption A～Dまたは同等の明示案を採択する。
2. File safety、publication eligibility、Module ownership、disposition、target routingを一文および集合式で説明できる。
3. accepted ADR、Current Requirement、Current Design、Plan、admission-v3、semantic-v3が同じ意味へ更新される。
4. profile/version、partition fingerprint、counts、public reasonへの影響が決定される。
5. docs-only local validationが新しいexact SHAでpassする。
6. original reviewerが同じobjectiveのfollow-upでschema-valid `review_status=pass`を返す。

将来のhandoffは、少なくとも次の条件で直ちにstop-and-returnしなければならない。

- authority文書間の矛盾
- owner File dispositionの未決
- 新しいpublic API／schema state／reasonが必要になった
- security、data、migration、compatibility、rollback、recovery、operationへの予期しない影響
- 旧root／causal／taint contractの変更が必要になった
- target failureをbase validation bypassとして使う必要が生じた
- planned path、symbol、consumer census、count式の前提が反証された
- v1/v2または既存domainのbytes／IDsを変更する必要が生じた

本分析はread-onlyであり、編集、test実行、Git操作、review follow-up、workflow transitionを実行していない。

# Verification plan

## Supplied results

すべて`a4efdc373a515801777c924a1d14675fda686955`に結合される。

| Evidence | Supplied result |
|---|---|
| GitHub branch tip | 期待SHAと完全一致。分析終了直前にも再確認 |
| Review artifact | complete JSON、schema-valid、digest一致、P1×1、fail |
| Repository trace | Module→owner File reverse taintなし、非File root seed／causal fixed point確認 |
| Focused falsification | `module_relation`、`export_binding`、`boundary_derivation`でFile untainted／Module tainted |
| Explicit safe target | target自体はfailureなし。unrelated program FileのModule欠落でpublic model failure |
| No explicit target | 旧helperはimplicit target missingへroute。Core-v3最終意味の証明には使わない |
| Existing checks | current pointer/schema checks、baseline taint/cardinality tests、docs checker、SpecDock、precommit equivalentがpass |
| Missing | Core-v3、schema、actual TS、source seal／transport／publication integration、OS／CLI／package evidence |

packetのvalidation結果と未実装境界は明示的に分離されている。attachments-bundle

## Future obligations after an approved decision

### First Red / focused falsification

新しいcandidate SHAで、2つの独立program Filesを持つ最小fixtureを用意し、影響側Fileに各root、別Fileにexplicit safe targetを設定する。採択案どおりのpublic File／Module集合になるまで旧projectionをREDにする。

検査対象には少なくとも次を含める。

- `module_relation`
- `export_binding`
- `boundary_derivation`
- `type_symbol`
- `props_subtree`
- `component_flow`
- path付き／pathなしroot
- direct rootとtransitive cross-file taint
- 同一File内のModule／Component／Member／Relation closure

### Adjacent-path completion sweep

- legal selection-only Module exclusion
- `target_excluded`
- supported／unsupported frontier
- no target
- explicit unrelated safe target
- explicit failing target
- directory target
- multiple projects
- 全Files非公開のempty Project
- safe nonprogram File
- program FileでModuleがduplicate／missing／proof-only
- public/private reference closure
- Project双方向membership
- proof-discovered／published／proof-only／accounted counts
- model-record 10000 exact／+1
- partition fingerprint、compatibility、十四key run fingerprint
- privacy、proof payload非公開、native integer保証

### Aggregate regression

- 旧v1/v2 root／causal／KAT不変
- SI-P01～P06
- 全SI negative cases
- focused schema/reference tests
- all contract tests
- full pytest
- Ruff、format、mypy
- SpecDock sync／validate
- Markdown links、closed key counts、preimage census
- pinned PlantUML
- `git diff --check`
- 旧Python／SQLAlchemy semantic bytes不変

### Integration and runtime evidence

Core-v3が成立した後、同じsource seal／candidate／assets ownerから次を一つのimmutable chainとして確認する。

```text
full proof
→ adopted File publication projection
→ Project safe membership
→ Core-v3
→ compatibility/provenance/run
→ JSON/PlantUML/publication
```

actual TS、OS、CLI、offline package evidenceは後続A04／A05へ残し、reference passから推論しない。

### Semantic checkpoints

- program Fileのpublic admission条件を一文で説明できる。
- record taintとpublication eligibilityを混同しない。
- target failureは完全proof／base model errorを隠さない。
- public program Fileにorphan Module状態がない。
- public referenceがproof-only recordへ向かない。
- Fileを任意に消す自由入力がない。
- countsとfingerprintが採択集合から独立再導出される。

### Negative assertions

- tainted Moduleをcardinality維持のため公開しない。
- owner Fileをtarget exceptionで無関係に免除しない。
- rootごとのad hoc exceptionを作らない。
- Module→File proof edgeを暗黙追加しない。
- proof-only File／Moduleをpublic membershipやentity countへ混ぜない。
- old profile／certificateへcastしない。
- ASSET policy、early prefix partial-safe、Project taintを混入しない。

### Rollback verification

新v3 profileを無効化した場合はtyped unavailableへ戻り、旧v1/v2 schema、record、fixtures、existing domainsは同一bytesで残ることを確認する。未完成v3を旧admissionへdowngradeして公開しない。

### SHA binding

- supplied evidenceはすべて`a4efdc373a515801777c924a1d14675fda686955`。
- design decision後のdocs evidenceは新しいdocs candidate SHAに結合する。
- reference/schema/test evidenceは、その実装candidateのfull SHAに結合する。
- same-reviewer resultはreview対象のcurrent full SHAと一致しなければ無効。
- test SHA、reviewed SHA、branch tipのいずれかが異なる場合は再収集する。

# Same-reviewer re-review obligations

original reviewerは`issue8-source-inventory-spec-review`である。同じobjectiveの修正は、このreviewer lineageへのStrict follow-upで閉じる。ローカルanalyst判定だけではclosureにならない。

| Finding／Group | Reviewerが再確認する内容 | Closure state |
|---|---|---|
| `SPEC-SI-P1-01` / `RG-SI-001` | 非File rootでModuleがproof-onlyになった際、owner program File、Project membership、public cardinalityが採択ルールどおり一意に決まること | **Expected closure**: 全triggerでnominal candidateまたは採択済みtyped outcomeが矛盾なく成立 |
| 同上 | explicit unrelated safe targetでunrelated orphan Fileが残らず、safe target自体を不当に失わないこと | **Expected closure** |
| 同上 | no-target behaviorが契約上明記され、旧helper behaviorを無検証で継承していないこと | **Expected closure** |
| 同上 | `F_safe`またはFile→Module contractを変更した場合、accepted human decisionへ明示的に結合されていること | **Supersession by approved contract change**。黙示的な文言修正では閉じない |
| 同上 | reviewerがtriggerの非到達性をexact proofで示す場合 | **Disproof**。現在のexplicit-safe-target evidenceを直接反証する必要がある |
| 同上 | 3 rootだけに局所対応し、selection／transitive／target隣接経路が未確認の場合 | **Still open** |
| `GAP-SI-V3-EXEC-01` | docs-only段階として必要な意味が完全で、未実装事項を成立済みと誤記していないこと | 仕様reviewでは明示gapとして許容。SI-03以降の証拠へ持ち越す |

completion sweepでは同じroot causeを次の隣接pathでも確認する。

- 全non-File root kinds
- transitive Module taint
- selection-only semantic omission
- target無し／safe target／failing target
- nonprogram File
- empty／multi-Project membership
- public/private refs
- counts、budgets、partition hash
- proof-only record privacy
- old v1/v2 invariance

same reviewerは、findingの文面が消えたことではなく、current candidate全体で同じ矛盾が別経路に残っていないことを確認する。最終的にschema-valid `review_status=pass`が必要である。

# Parent workflow consequence

親workflowの次の結果は、**stop for human design decision**である。

現在の状態は次のとおり。

- SI-02 Specification Review: failed
- P1: 1件、open
- SI-03 source/proof reference seam: blocked
- SI-04 full Core: blocked
- SI-05以降およびA03／production: blocked
- P2/P3 follow-up: なし
- 新ASSET decision: 要求も採択もされていない

再開条件は順に次である。

1. program FileとModuleのpublication couplingを人間が採択する。
2. SI-01へ戻り、canonical docsを同じ意味へ更新する。
3. docs-only local checksを完了する。
4. clean/pushed exact SHAをGitHubで再検証する。
5. original reviewerへsame-objective follow-upを行う。
6. current SHAに対するschema-valid `review_status=pass`を得る。
7. その後にだけSI-03を開始する。

推奨Option Aを採るだけなら、accepted objective「取得inventoryとsafe subsetの分離」は維持できる可能性が高く、same-reviewer follow-upで足りる。public contract、objective、scope identityをさらに変更する案を採る場合は、親workflowがnew scope identityまたはfresh review campaignの要否を判断する。

編集、commit、push、test実行、reviewer submission、issue/thread変更、workflow transition、closureはすべて本skillの外であり、親workflowが所有する。

# Assumptions and unresolved evidence

| 種別 | 内容／invalidation condition |
|---|---|
| Analyst provenance gap | native analyst session IDは観測不能。別session lineageであることはcurrent invocationの役割分離に基づくが、backend identifierによるattestationはない。 |
| Review artifact location | `.workbench` artifactはGitHub repositoryから取得できなかった。添付完全JSONのdigest一致を根拠に内容を採用した。別bytesの原artifactが提示されdigest不一致なら再分析が必要。 |
| Harness gap | focused reproduction scriptのsourceは未提供。packet出力とrepository code traceが一致するためclaimを採用したが、harnessの全前提は未検証。 |
| Target-free uncertainty | 旧helperのimplicit-target behaviorは確認済みだが、未実装Core-v3のno-target final semanticsは未確定。findingの有効性はexplicit safe targetに依存し、no-target断定には依存しない。 |
| Breadth uncertainty | selection-only Module omission、全root kinds、transitive cross-file taintが同じ矛盾を実際に起こす範囲はcompletion sweep未実施。一般化は設計上のrisk推論であり、個別到達性は将来証拠が必要。 |
| Profile identity | docs-only段階でplanned profile IDを修正後も維持できるか、新identityが必要かは未決。 |
| Disposition reason | owner Module非公開に由来するFile exclusionを既存`tainted`へ含めるか、新reasonを設けるか未決。 |
| Compatibility impact | v3未実装のため出荷migrationは存在しないが、planned hashes、counts、known literals、consumer assumptionsへの影響は採択案確定後に再censusが必要。 |
| ASSET policy | ordinary asset I/O／corruption policy、early reader prefix partial-safeは未採択であり、本findingから承認を推論しない。attachments-bundle |
| Production evidence | actual Core-v3、TypeScript、OS、CLI、wheel／sdist、publication integrationは未認定。仕様裁定をproduction readinessとして扱わない。 |
| Branch mutation | 本応答直前のtipは期待SHAと一致した。以後branch tipが変わった場合、本packetのrepository factsと将来obligationは新SHAへ自動継承されない。 |
