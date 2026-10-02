# Binding and evidence completeness

**GitHub binding.** GitHubコネクタで `chemitaro/code-structure-viz` のブランチ `iss-00008-generate-nextjs-component-snapshots` を直接取得し、最終確認時点の先端が `d3cce1cb42b3c6a00d7a8d8d2b9ee4dbed2406d1` であることを確認した。これは指定された `expected_sha` と40文字すべてで一致する。コミットの親は `ce0edaa8fe63e79523fe7ad1dcb4b0a39dc02dce`、treeは `2d6bf11af83bc2d3d5ff99efb9ef5f0c96ff4d04` である。他ブランチの内容へのフォールバックは行っていない。

**対象と来歴。**

| 項目 | 確認内容 |
|---|---|
| Repository | `chemitaro/code-structure-viz` |
| Branch | `iss-00008-generate-nextjs-component-snapshots` |
| Current candidate SHA | `d3cce1cb42b3c6a00d7a8d8d2b9ee4dbed2406d1` |
| Original SI-03 base | `ce0edaa8fe63e79523fe7ad1dcb4b0a39dc02dce` |
| Review source | ChatGPT Code Review Strict、fresh one-shot independent conversation |
| Reviewer session | `issue8-si03-source-inventory-review` |
| Reviewer conversation | `6abf52c7-c150-83e8-8923-5b4661b7bf16` |
| Review artifact | `reviews/si03-source-inventory-result.json` |
| Raw review SHA-256 | `9cd4663002277d8ad2bcfb8f3427550ec16d4da24f62b8803946a77511dc6670` |
| Analyst identity | `issue8-si03-source-owner-cause-adjudication` |
| Continuity | initial、fresh analyst conversation。reviewer、author、implementerとは別系統 |
| Evidence collection time | `2026-10-02T07:03:21Z` |

これらのbinding、reviewer provenance、artifact identity、fresh analyst lineageはcurrent evidence packetに明示されている。attachments-bundle

**reviewed／tested SHA整合。**

- Code Reviewはcurrent candidate `d3cce1cb42b3c6a00d7a8d8d2b9ee4dbed2406d1` を対象とし、source-native結果は `SI03-CR1-F1`、P1、`review_status=fail` である。reviewer自身はローカルテストを実行していない。attachments-bundle
- 309件の関連selection、17件の旧domain／Current pointer、Ruff、format、mypy、SpecDock等は、最終code/docs treeをcommit前に検証し、そのtreeを変更せず `d3cce1c` としてcommitしたという**tree-aligned evidence**である。commit後に同じコマンドを再実行してSHAを直接bindした証拠ではない。attachments-bundle
- focused bypass probeはcleanなexact `d3cce1c` 上で実行され、controlは拒否、rootから別Moduleへのedgeを一つ加えたbypassはfactoryとindependent revalidationの双方で受理された。これはcurrent findingの実到達性をSHA-bindしている。attachments-bundle
- 本分析ではテストを実行していない。既存結果をsupplied evidenceとして裁定している。

**authority completeness.** Current Requirement／Design／Plan、二つのaccepted ADR、`next-semantic-admission-v3.md`、`next-semantic-v3.md`、`next-compatibility-v3.md` が揃っている。accepted designは、同じsource seal／requestが全取得inventoryを所有し、公開modelはfull proofから独立に立証されたowner-closed safe subsetであること、Module原因をFile自身のtaintや直接failureへ偽装しないこと、公開可能なFile／Moduleの恣意的省略を拒否することを定めている。

**packet completenessの判断。** `SI03-CR1-F1` の主張、局所再現、到達経路、影響、canonical authority、実装箇所、既存テスト、親policyは裁定に十分である。一方、次のmaterial gapを保持する。

1. direct File failureについて、rootがFileをdeclared seedとして保持しつつ、`root → same-path Module → File` の迂回だけでFile witnessを成立させられるかは未再現である。既存negative testはrootからの唯一のedgeを除去するだけで、迂回経路を試していない。attachments-bundle
2. 309件の回帰結果はtree-alignedだが、commit後のexact SHA実行ではない。
3. review artifactのSHA-256とraw JSONはpacketから確認したが、本分析でartifactファイルのdigestを再計算してはいない。
4. SI-04が所有するfull mandatory edge completeness、least-fixed-point taint、source locality、target／export、Core／public certification、production runtimeは意図的なscope外であり、SI-03の欠落証拠として扱わない。

# Executive disposition

**Batch-level conclusion:** `SI03-CR1-F1` は妥当で、current candidate上で到達可能なin-scope P1である。`d3cce1cb42b3c6a00d7a8d8d2b9ee4dbed2406d1` はSI-03 step gateを通過できず、`review_status=pass` までブロックされる。

主原因は、`source_owner_witness_kinds_v3` が「edgeの閉包・rule・target-kindが許可されていること」と「そのrootが当該targetをdeclared seedとして原因付けする権限を持つこと」を同一視した点である。rootの `record_ids` がD内へ閉じることは検証しているが、root-origin edgeのtargetがそのrootの `record_ids` に含まれることを確認せず、root kindを伝播している。

**Primary response route:** `implementation-remediation`。Requirement／accepted design／Planの意味は十分に明確であり、実装がそれに違反している。severity、claim validity、blocking effect、response route、authorizationは別判断であり、P1という分類自体は変更命令ではないが、親Planがこの一意のin-scope修復を明示的に許可している。attachments-bundle attachments-bundle

安全に進められるのは、次の範囲だけである。

- root-origin edgeが、そのrootのdeclared `record_ids` 外へroot kindを持ち出すことを、SI-03局所witness境界で拒否する。
- exact bypassのTDD regressionを追加する。
- direct Fileの迂回経路をfocused falsificationする。
- full mandatory proof、shared v1 helperの一般契約、schema、public API、data、security、compatibility、recovery、運用意味には進出しない。

direct Fileに追加の「必ずrootからFileへの直接edgeを要求する」規則を実装することは、現時点では未認可である。まず迂回経路を再現し、SI-03の局所witness義務だけから一意に拒否できるかを確認する必要がある。full mandatory edge completenessを新たにSI-03へ移す必要が生じるなら、人間判断へ戻す。

# Root-cause groups

| Group ID | 含まれるmaterial item | Source-native classification | 状態 |
|---|---|---|---|
| `RC-SI03-001` | `SI03-CR1-F1` — seed外のroot-origin edgeで別Moduleへroot kindを伝播し、そのowner Fileを `excluded/failed` にできる | P1、reviewer confidence 0.99 | 妥当・到達可能・blocking |
| `RC-SI03-001` | `CG-SI03-001` — direct File rootのsame-path Module経由迂回が未検証 | severityなしのmaterial coverage gap | 未解決。focused falsification必須 |
| `RC-SI03-001` | `EC-SI03-001` — SI-03実装証拠Artifactは「無関係root借用を拒否」と記録しているが、exact-SHA probeが反証 | severityなしのevidence conflict | current candidateのclosure根拠として使用不可 |

三項目を一群とする理由は、すべて同じ不変条件、すなわち**root kindの最初の伝播先は、そのrootが宣言し権限を持つorigin／seedに結合されなければならない**ことに関係するためである。`CG-SI03-001` はreviewerによる第二のfindingでもP1でもなく、同じroot causeの隣接経路に関するcoverage gapである。severityは追加しない。

`EC-SI03-001` はcanonical designの誤りではなく、実装証拠がcurrent behaviorを過大に記述した結果である。実装証拠Artifactは、unrelated-root borrowingを拒否したとする一方で、同時にwitnessがsubmitted closed edgesに沿う局所joinでありfull mandatory proofではないと説明している。current probeにより前者だけが反証された。

別groupへ分ける項目、重複finding、独立したP2／P3、別のcurrent test failureはない。

# Detailed adjudication

## `RC-SI03-001` / `SI03-CR1-F1`

**Claim validity:** valid。

`source_owner_witness_kinds_v3` はrootsとrecordsを作り、各rootの `record_ids` がrecords内へ閉じることを確認する。その後、各submitted edgeについてtargetの存在と `_causal_edge_is_allowed()` だけを確認し、`adjacency[source_id]` にtargetを登録する。初期状態ではroot ID自身にroot kindを置き、adjacencyに沿ってkindを伝播する。root-origin edgeのtargetが、そのrootの `record_ids` に含まれるかは確認していない。

`derive_source_projection_v3` は、このwitness集合をModule taintの正当化に利用する。したがって、root Aの `record_ids=[A]` を維持したまま、rule／target-kind上許可される `root A → Module B` edgeを提出すると、BがAのroot kindを取得し、Bのtaintおよびowner Fileの `excluded/failed` が正当化される。

focused probeでは、edgeをBへ追加しないcontrolは `owner cause requires matching retained failure roots` で拒否された。一方、そのedgeだけを追加した入力は受理され、二つのowner Filesが除外され、independent revalidationもpassした。attachments-bundle

**Trigger reachability:** reachable。

これはunused helperやdead pathではない。`retain_source_inventory_seam_v3` が `derive_source_projection_v3` を呼び、同じderivationは `validate_source_inventory_seam_v3` のindependent revalidationでも再実行される。したがってproducer cacheだけの問題ではなく、SI-03 factoryと独立再検証の双方が同じ不正入力を認める。

**In-scope impact:** accepted owner-closed Option Aが要求する「untainted program Fileは、正規owner Moduleが立証済みの理由で公開不能な場合だけ除外できる」という保証を破る。許可されたroot kind／target kindの範囲内で、別Moduleとそのowner Fileを任意に非公開側へ落とせるため、exact File partitionと「公開可能Fileの任意欠落拒否」が成立しない。Requirementはexact partitionと正当化済みowner-closed exclusionを要求し、Plan SI-03は偽owner原因の拒否を出口条件としている。

**Blocking effect:** source-native P1をそのまま保持する。親policyではvalid P0／P1がSI-03 step gateをblockし、fresh reviewの `review_status=pass` まで認定しない。ローカルの反証・修復判断だけではgateを閉じられない。attachments-bundle

**Violated authority and exact proposition:**

1. 全取得inventoryと元taint／causal意味は保持し、public eligibilityをchildの自由な提出物から決めない。
2. untainted Fileの `excluded/failed` は、そのowner Moduleに対する検証済みfailure／root／taintへ結合されなければならない。
3. 公開可能なFile／Moduleを恣意的に省略してはならない。
4. SI-03はfull mandatory edge completenessを認定しないが、SI-03がowner causeとして実際に利用するwitnessは偽造されてはならない。

accepted ADRは、childの提出modelの不在を除外根拠にせず、Module原因をFile自身のtaintや直接failureへ偽装せず、公開可能なFile／Moduleを必ず公開すると定めている。

**First incorrect fault layer:** implementation。

最初に誤っているのは `tests/contracts/next_source_inventory_v3_validation.py::source_owner_witness_kinds_v3` である。Requirement、accepted ADR、Current Design、Planは、偽owner原因を許可していない。shared helper `_causal_edge_is_allowed` はedgeのclosed rule／kind／pathを検査するための下位helperであり、その単独結果をroot-origin権限として採用したSI-03側の組合せが誤りである。

第二のfaultはtest coverageである。既存 `test_owner_cause_cannot_borrow_a_root_from_an_independent_module` はBへのedgeが存在しないcaseを拒否するが、同じrootからBへの許可edgeを追加するmutationを含まない。

**Root cause:** edge-shape legalityとroot-origin authorityの混同。rootの `record_ids` は単なるD内reference集合として確認され、伝播の最初のhopを制限するauthorityとして使われていない。

**Primary response route:** `implementation-remediation`。accepted requirement／designが明確で、SI-03 implementationが違反している場合のrouteである。attachments-bundle

**Preserved guarantees:**

- 同じrequest／seal／assets owner。
- full Project／File discoveryとfull Module owner cardinality。
- 元record-level taint。
- 既存root kinds、edge rules、wire、enums。
- Fileへの偽taint禁止。
- Module→File逆taint禁止。
- selection／unsupported reasons。
- exact partition、Project safe projection、counts、KAT。
- SI-04が所有するfull proof／locality／Core boundary。

**Changed guarantee:** submitted edgeがrule上許可されるだけではroot kindのoriginになれず、root-origin targetがそのrootのdeclared seedである場合にだけ最初の伝播を開始できる。

## `RC-SI03-001` / `CG-SI03-001`

**Claim validity:** direct Fileの迂回受理は未確定。

current codeはdirect parse／read failureについて、File IDがrootの `record_ids` に含まれること、root kind／path／File taintが一致することを別途確認する。その後、同じgeneric witness graphでFileへroot kindが到達することを要求する。

既存testは、File seedの欠落、root-origin edge全体の欠落、File taintの欠落を拒否する。しかし、Fileをrootのdeclared seedに残したまま、`root → same-path Module → File` とし、`root → File` だけを除くcaseを試していない。

**Authority conflict／境界:** admission-v3はparse／read rootのmandatory seedsに同path File自身と従属recordsを含めること、File seed省略を認めないことを要求する。一方、full submitted seeds／edgesの完全一致とleast-fixed-point proof全体はSI-04の責任である。

したがって、現時点で一意に認可されるのはfocused falsificationまでである。迂回が受理された場合でも、「SI-03局所File witnessとしてrootからFileへの直接edgeが必要」という既存命題だけで拒否できるかを確認する必要がある。full mandatory edge集合をSI-03へ前倒しする、shared helperの一般意味を変える、または新たなedge completeness契約を定義する必要があるなら、通常修復を停止する。

**Blocking effect:**新たなP severityは付けない。ただし、generic nonseed guardだけを実装してこの隣接経路を未確認のままroot-cause groupのclosureを宣言することはできない。fresh re-reviewへ渡す前に、disproof、既存authorityに基づく限定修復、またはstill-open stopのいずれかを記録する必要がある。

## `RC-SI03-001` / `EC-SI03-001`

SI-03 evidence Artifactは「無関係root原因の借用を拒否」と記録しているが、exact-SHA probeはその主張を反証する。これはcanonical requirement／designの意味衝突ではなく、当時のテストがmutationを十分に覆わなかったことによるevidence recordの過大記述である。

この項目のためにcanonical docsを変更してはならない。親workflowは、旧Artifactを黙って正しかったことにせず、新しい修復証拠でcurrent statusを明示的にsupersedeする。

# Integrated response design

最小でcoherentなresponseは、SI-03 witness graphの**最初のroot-origin hopだけ**をdeclared seedへ結合することである。

## Affected surface

1. `tests/contracts/next_source_inventory_v3_validation.py`
   - `source_owner_witness_kinds_v3`
2. `tests/contracts/test_next_source_inventory_v3.py`
   - exact two-Module bypassのregression。
   - direct File迂回のfocused falsification。
3. 修復後の新しいSI-03 implementation evidence record。

通常は `tests/contracts/next_source_inventory_v3_reference.py` に変更は不要である。factoryやimmutable seamの公開形状は変えない。

## Required state transition

1. current candidate上で、rootの `record_ids=[A]` を維持しつつ `root→B` を追加したexact negative testを追加し、現在は受理されるためREDになることを保存する。
2. `source_owner_witness_kinds_v3` のedge loopで、`source_id` がfailure rootである場合、その `record_id` が当該rootの `record_ids` に含まれなければ、adjacencyへ追加する前にbounded rejectionとする。
3. 既存 `_causal_edge_is_allowed` のrule／kind／path検査を引き続き実行する。
4. root→declared seedの既存positive casesを維持する。
5. exact bypassが拒否されるGREENを得る。
6. direct File迂回caseを構成し、generic guard後の実挙動を確認する。
7. focused、aggregate、static、document checksを新SHAへbindする。
8. original base `ce0edaa...` を維持したfresh one-shot Code Review Strictへ進む。

このlocal guardは、「declared seedすべてにedgeが存在する」「全mandatory edge集合が完全である」「child edge集合が独立導出集合と一致する」とは主張しない。そのためSI-04のfull proof責任を取り込まない。

## Expected non-mutations

変更してはならないものは次のとおり。

- root kind、rule、taint、disposition、reason、wire enum。
- schema、profile、producer version、public record。
- shared v1 helperの一般契約。
- Module→File／File→Projectの逆causal edge。
- SourceAcquisitionSeal、request-v2、transport candidate、assets binding。
- count／partition fingerprint preimage。
- source locality、target、export、budget routing、Core／public gate。
- ASSET failure policy、runtime、Node、CLI、package、diagnostics。

## Compatibility and operations

対象はtest-only reference seamの局所validationであり、正常なdeclared-seed witnessの出力bytes、public API、persistent data、migration、security model、runtime、rollback protocolを変える理由はない。これらへの影響が発生した時点で、本response designの境界を超える。

rollbackはcode／test commitのrevertだけで機械的に可能であり、data migrationはない。ただしrollbackするとP1を再導入するため、gate closure手段にはならない。

## Structural stop signals

次のいずれかが生じた場合はpatch chainingを停止する。

- shared `_causal_edge_is_allowed` の意味変更が必要になる。
- full mandatory seeds／edgesの独立導出が必要になる。
- root `record_ids` とcausal edgeの役割を再定義する必要がある。
- new state、schema、wire field、enum、diagnostic、APIが必要になる。
- accepted legitimate caseがnonseed root edgeを必要としている。
- direct File迂回の拒否にSI-04全体のproof completenessが必要になる。
- public、data、security、compatibility、rollback、recovery、operationの意味が変わる。

これらはcanonical design判断を要するsignalであり、local exceptionやdual gateを増やして回避してはならない。attachments-bundle

# Human decisions and authorization

**Parent authorization source:** approved Planと継続中のuser taskは、accepted SI-03 contract内で意味を変えない一意のP0／P1修復、TDD、local verification、明示pathのcheckpoint／push、fresh independent re-reviewを許可している。分析自体はread-onlyであり、新しいauthorizationを作らない。attachments-bundle

**人間判断なしで一意に実行できること:**

- nonseed root-origin edgeの拒否。
- exact A／B bypassのregression test。
- declared-seed positive control。
- direct File迂回のfocused falsification。
- 同じscopeの検証とfresh review。
- 旧evidenceをsupersedeする新しい実装証拠の記録。

**現時点で認可されないこと:**

- direct Fileについて追加のdirect-edge ruleを、再現やauthority照合なしに実装すること。
- shared v1 helperへroot seed membershipを一般規則として移すこと。
- SI-04のmandatory proof completenessをSI-03へ移すこと。
- source of truth、root／seed／edgeの責任分配を変更すること。
- public API、schema、wire、data、security、migration、compatibility、rollback、recovery、operation、risk acceptanceを変更すること。
- 新ASSET policy、diagnostic、production runtimeを同時に扱うこと。

direct File迂回が受理され、既存SI-03 authorityだけではdirect-edge要求を一意に導けない場合、必要なのはhuman design decisionである。具体的には「SI-03 local witnessがroot→Fileの直接edgeまで認定するのか、それともその完全性をSI-04だけが所有するのか」を決める必要がある。

canonical wordingの変更案は提案しない。現行authorityはproven P1の修復には十分である。

# Implementation handoff

**Authorization status:** 次のbounded objectiveに限り実装handoffを認可する。

## Bounded objective

`source_owner_witness_kinds_v3` がowner causeとして利用するroot-origin propagationについて、failure rootからdeclared `record_ids` 外のtargetへroot kindが最初に伝播することを拒否し、`SI03-CR1-F1` のexact cross-Module bypassを閉じる。full mandatory proofを実装しない。

## Exact verified paths and symbols

1. `tests/contracts/next_source_inventory_v3_validation.py`
   - `source_owner_witness_kinds_v3`
   - source-native review location: lines 323–327周辺。
2. `tests/contracts/test_next_source_inventory_v3.py`
   - `test_owner_cause_cannot_borrow_a_root_from_an_independent_module`
   - `test_direct_file_failure_keeps_its_source_seed_edge_and_typed_taint`
3. 変更を原則禁止する共有surface:
   - `tests/contracts/next_reference_validation.py::_causal_edge_is_allowed`
4. 変更不要であるべきsurface:
   - `tests/contracts/next_source_inventory_v3_reference.py`

## Ordered changes

1. **First Red:** 二つのprogram Modules A／Bとowner Filesを用意する。root kindは `module_relation`、rootの `record_ids` はAだけとする。controlの `root→A` に加えて、同じrootからBへの許可された `identity_dependency` edgeを追加する。Bを `tainted/module_relation`、owner Fileを `excluded/failed` とする。factoryが拒否することを期待するtestを追加し、current `d3cce1c` では受理されるREDを保存する。
2. **Local fix:** edgeの `source_id` がfailure rootで、target `record_id` がそのrootの `record_ids` に含まれなければ、adjacency登録前にrejectする。既存 `_causal_edge_is_allowed` はその後または同じvalidation branchで維持する。
3. **Focused Green:** exact bypassが拒否され、control positiveが引き続き通ることを確認する。
4. **Independent revalidation:** factoryで作成可能な正常seamが再検証を通ること、不正seamがfactory時点で作成されないことを確認する。
5. **Direct File falsification:** rootのdeclared seedsにFileとsame-path Moduleを含め、`root→Module` と `Module→File` だけを持ち、`root→File` を持たないcaseを構成する。まず現挙動を記録する。これを拒否する追加実装は、SI-03局所authorityだけから一意に導ける場合に限る。それ以外は停止して返す。
6. **Regression:**既存SI-03 module、隣接v2 semantic／request／exchange／trusted／schema、旧domain／Current pointerを再実行する。
7. **Quality checks:** Ruff check、Ruff format check、mypy、SpecDock sync／validate、Artifact link check、`git diff --check` を新candidateへbindする。
8. **Checkpoint:** explicit pathsだけをstageし、新full SHAを得てpushする。
9. **Fresh review:** original base `ce0edaa8fe63e79523fe7ad1dcb4b0a39dc02dce` と新headのrangeを、fresh one-shot reviewer conversationへ渡す。

## Explicit non-goals

- full mandatory root／seed／edge derivation。
- least-fixed-point taintの独立導出。
- source graph locality、target、selection、export。
- record／entity budget terminal routing。
- Core／public／production certification。
- schema／API／wire／enum／diagnostic追加。
- reverse Module→File taint。
- runtime、Node、OS、CLI、package、ASSET policy。
- P2／P3や別scopeの改善。

## Prohibited choices

- rootの `record_ids` をedgeに合わせて広げる。
- BのtaintやFile dispositionを消してtestだけ通す。
- submitted taint／edgeを新authorityにする。
- shared helperを広く変更して隣接契約へ影響を拡散する。
- nonseed edgeを許すfallback、special-case、dual pathを追加する。
- reviewer recommendationだけを根拠にdirect File ruleを新設する。
- old evidence Artifactを黙って書き換え、当時から正しかったように扱う。

## First-red evidence

返却証拠には少なくとも次を含める。

- test node ID。
- current SHA `d3cce1cb42b3c6a00d7a8d8d2b9ee4dbed2406d1`。
- exact fixture mutation。
- expected rejectionと実際のacceptance。
- excluded owner File IDsまたはpaths。
- factoryとindependent revalidationの結果。
- terminal command、exit code、failure excerpt。

## Stop-and-return conditions

次のいずれかで実装を停止し、analyst／人間判断へ返す。

- verified pathまたはsymbolが存在しない、または想定と異なる。
- accepted positive fixtureがnonseed root-origin edgeを意図的に必要とする。
- shared lower-layer helperの契約変更が必要。
- full mandatory edge completenessが必要。
- direct Fileのdirect-edge意味をcurrent authorityから一意に決められない。
- unexpected public API、schema、data、security、migration、compatibility、rollback、recovery、operation影響が現れる。
- root／seed／edgeの責任分配を変更しなければ修復できない。
- generic guard後にも別経路で同じinvariantが破られ、単一のroot-origin規則で説明できない。

## Evidence destination and format

実装者は親workflowへ、次の二種類を返す。

1. **新しいtimestamped Markdown implementation-evidence Artifact**
   旧 `20261002t062856z-disc-si03-source-inventory-reference-seam.md` を黙って書き換えず、finding ID、group ID、first Red、実装delta、deviation、focused／aggregate results、新full SHA、残存gapを記録する。
2. **fresh review artifacts**
   Workbenchのreview JSON、complete log、reviewer session／conversation provenance、artifact SHA-256、model／thinking provenance、base／head full SHA、`review_status` を保存する。

# Verification plan

## Supplied results

| Lane | Supplied result | Binding |
|---|---|---|
| GitHub identity | branch tipとexpected SHAが完全一致 | exact `d3cce1cb42b3c6a00d7a8d8d2b9ee4dbed2406d1` |
| Source review | `SI03-CR1-F1`、P1、`review_status=fail` | reviewed SHA `d3cce1c` |
| Focused falsification | control reject、extra root→B edgeでfactory／revalidation accept | clean exact `d3cce1c` |
| Unit／adjacent regression | 309 passed | final tree aligned、commit後再実行ではない |
| Old-domain regression | 17 passed | final tree aligned |
| Static／docs checks | Ruff、format、mypy、SpecDock等pass | final tree aligned |

supplied local checksとfocused probeの詳細はpacketに保存されている。attachments-bundle

## Future obligations

| Verification lane | 必須結果 | SHA binding |
|---|---|---|
| First Red | exact A／B bypass testがcurrent codeでfailureする | current `d3cce1c` |
| Focused Green | nonseed root-origin edgeをbounded rejection | new repair full SHA |
| Positive control | root→declared seedのModule failure caseは維持 | new repair full SHA |
| Direct File falsification | `root→Module→File`、root→Fileなしの実挙動を記録 | new repair full SHA |
| Aggregate regression | 旧309 selection相当＋新tests、旧17件 | new repair full SHA |
| Independent validation | valid seam再導出pass、不正原因を再生成しない | new repair full SHA |
| Static checks | Ruff、format、mypy | new repair full SHA |
| Repository checks | SpecDock、links、whitespace、clean worktree | new repair full SHA |
| Fresh strict review | P0=0、P1=0、`review_status=pass` | exact same new repair SHA |

**Semantic checkpoints:**

- root-origin targetはrootのdeclared seedである。
- downstream record-to-record propagation規則は変更しない。
- owner Moduleのtaint／failure理由は変えない。
- owner Fileは偽taintを受けず、正規の `excluded/failed` semanticsを維持する。
- exact File partitionとProject projectionの正常結果は不変。
- full proof認定を主張しない。

**Negative assertions:**

- rootの `record_ids` 外のModule、File、その他recordへroot kindを直接伝播できない。
- FileやModuleを恣意的に非公開へ落とせない。
- root `record_ids`、submitted taint、public modelの欠落を修復側が書き換えない。
- reverse taint、新field、新enum、新diagnostic、新schema、新APIを追加しない。
- shared helperのconsumerへ意味変更を漏らさない。

**Integration／runtime evidence:** SI-03はtest-only source/proof reference seamであるため、実Node、OS process、CLI、production adapter evidenceはこの修復の必須laneではない。同じreal `SourceAcquisitionSeal` fixture、retained request／assets、factory、independent revalidationが現在のintegration boundaryである。

**Rollback verification:** 新commitが単一のbounded code／test deltaであり、revertにmigrationやpersistent recoveryを要しないことを確認する。ただしrevert後はP1が再発するため、rollback状態でgateをpassさせてはならない。

# Same-reviewer re-review obligations

このheadingの「same-reviewer」は、親policyに従い**旧conversationへのfollow-upではなく、同じspecialized Code Review Strict roleによるfresh one-shot独立conversation**として実行する。original base `ce0edaa8fe63e79523fe7ad1dcb4b0a39dc02dce`、同じSI-03 scope、修復後のcurrent headを使う。attachments-bundle

| Source／group | reviewerが独立に再確認する内容 | 許される結果 |
|---|---|---|
| `SI03-CR1-F1` / `RC-SI03-001` | root `record_ids=[A]` のままroot→Bを追加してもBとowner Fileを非公開にできない | expected closure |
| `SI03-CR1-F1` / `RC-SI03-001` | root→declared Aの正常failure witnessを過剰拒否しない | expected closure |
| `CG-SI03-001` / `RC-SI03-001` | direct Fileのsame-path Module迂回を再現し、direct witness義務との整合を確認 | disproof、evidence-backed closure、またはstill-open |
| `EC-SI03-001` / `RC-SI03-001` | 新evidenceが旧「unrelated root borrowing拒否」主張を正しくsupersedeしている | record reconciliation |
| Group completion sweep | 同じroot causeが隣接root kinds／targetsに残らない | expected closureまたは新finding |

completion sweepには少なくとも次を含める。

- `module_relation`、`export_binding`、`boundary_derivation` のModule owner causes。
- parse／read File roots。
- root→Module、root→File、root→他semantic record。
- 同kindの複数roots。
- 同pathと異pathのtarget。
- root `record_ids` がFile＋Moduleを含むcase。
- factoryとindependent revalidation。
- submitted edge orderやcanonicalizationに依存しないこと。

**Closure:** fresh reviewerがcurrent SHAについてfindingを閉じ、P0／P1なし、`review_status=pass` を返した場合だけclosureとなる。

**Disproof:** direct File迂回がgeneric guard後に成立しないことをexact testで示せた場合は、`CG-SI03-001` をdisproofとして閉じられる。

**Supersession:** approved canonical contract changeがroot／seed／edgeの意味を変更した場合に限る。その場合、通常の修復reviewではなく、decision記録と必要に応じたfresh campaignが要る。

**Still-open:** direct File迂回が成立し、SI-03とSI-04の責任境界をcurrent authorityから一意に決められない場合、finding groupはstill-openである。ローカル修復やanalyst判断だけでreview gateを閉じない。

# Parent workflow consequence

current candidate `d3cce1cb42b3c6a00d7a8d8d2b9ee4dbed2406d1` はSI-03でblockedのままである。SI-04、SI-05以降、全A02、累積A03、production、Final Quality Gateへ進めない。

親workflowは次に、認可済みのbounded implementation-remediationを実行できる。前提は次のとおり。

1. exact cross-Module First Redを保存する。
2. root-origin targetのdeclared-seed guardだけを実装する。
3. direct File迂回をfocused falsificationする。
4. 新full SHAへ全required evidenceをbindする。
5. clean／pushed exact SHAでfresh one-shot Code Review Strictを実行する。
6. `P0=0 / P1=0 / review_status=pass` を得る。

proven generic fixには新たな人間判断は不要である。ただし、direct Fileのdirect-edge要求、shared helper変更、full mandatory proofのSI-03前倒し、またはpublic／data／security／compatibility／recovery／operation意味変更が必要になった場合は、親workflowを停止し、人間判断を要求する。

本skillの外にある行為は、編集、テスト実行、Git操作、Artifact永続化、commit／push、reviewer起動、Issue／thread変更、workflow transition、closureである。親workflowがこれらを所有する。attachments-bundle

# Assumptions and unresolved evidence

| 種別 | 内容 | 無効化条件 |
|---|---|---|
| Verified fact | final確認時のtarget branch tipはexact `d3cce1cb42b3c6a00d7a8d8d2b9ee4dbed2406d1` | branch tipが移動した場合、全repository factを再検証する |
| Assumption | packet記載のreview JSON、digest、terminal outputs、test countsを真正なsupplied evidenceとして扱う | artifact bytesまたはlogsとの不一致が見つかる |
| Evidence limitation | 309／17件とstatic checksはfinal tree alignedだが、commit後exact SHA再実行ではない | repair後はpost-commit SHA-bound evidenceを要求する |
| Verified conflict | implementation evidence Artifactの「無関係root借用拒否」主張とexact-SHA probeが矛盾する | 新repair evidenceがsupersedeするまで旧主張はclosure根拠にならない |
| Unsupported claim | direct Fileの `root→same-path Module→File` 迂回が現在受理されるか | focused falsificationで確定する |
| Unsupported claim | direct Fileにroot→File直接edgeを要求することがSI-03だけから一意に導けるか | current canonical propositionの照合が必要 |
| Scope boundary | full mandatory edge completeness、least-fixed-point taint、locality、target、export、CoreはSI-04所有 | authority変更なしにSI-03へ取り込まない |
| Residual risk | `module_relation` 以外の許可root kindsにも同じnonseed propagation patternが残る可能性 | fresh completion sweepで確認する |
| Residual risk | local guardが、既存fixture内の意図しないnonseed root-origin edgeを顕在化させる可能性 | その場合はfixtureを機械的に直さず、authorityとproducer契約を再確認する |
| Stop condition | shared helper、schema、public contract、data、security、migration、compatibility、rollback、recovery、operationへの影響 | 通常修復を停止し、human decisionへ返す |
