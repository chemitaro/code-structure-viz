---
種別: disc
ID: "20260921t152339z-disc"
タイトル: "Issue #8 I05-PLAN-008 Current Review Findings Analysis"
状態: "draft"
作成者: "Codex"
最終更新: "2026-09-22"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["iss-00008"]
reflected_to: []
---

# Issue #8 I05-PLAN-008 Current Review Findings Analysis

## Provenance and status

- Status: advisory evidence; not adopted as canonical requirement, design, or plan.
- Candidate: `707fefe47717dbed4afd3a9e266ced9a55f9d06b`; fixed point: `c6b7f161c4971c620f221c3faa82098ee3510be6`.
- Analyst: Oracle session `required-strict-github-connector-verificati-1058`; requested and UI-verified model `GPT-5.6 Sol`, thinking level `Pro`.
- Analyst transcript SHA-256: `4bf1d41a52e083b2c036e3f7544684671675e77595ac5f0086153b2455e222bc`.
- Strict reviewer: `required-strict-github-connector-verificati-1057`; independent I05-PLAN-008 review: `/root/issue8_plan008_gpt6_max_review`.
- Primary evidence packet: `.workbench/luna-max-implement/issue8-nextjs-snapshots/evidence/707fefe-current-review-batch.md` (SHA-256 `901611b6ca9d3310f9501019083602fc142c6fdf8f7bf0a1ba9b0ee7a4023ac1`).
- Oracle source transcript: `/Users/iwasawayuuta/.oracle/sessions/required-strict-github-connector-verificati-1058/artifacts/transcript.md`.
- No product or canonical-specification change and no Issue-state transition is adopted by this artifact. It is a traceability record; the proposed Option A wording below remains unadopted pending the user's decision.

## Full ChatGPT decision packet (verbatim)

# Binding and evidence completeness

## GitHub binding

GitHub connector verificationは成功しました。検証対象と結果は次のとおりです。

| 項目                        | 確定内容                                                                                 |
| ------------------------- | ------------------------------------------------------------------------------------ |
| Repository                | `chemitaro/code-structure-viz`                                                       |
| Target branch             | `iss-00008-generate-nextjs-component-snapshots`                                      |
| Expected SHA              | `707fefe47717dbed4afd3a9e266ced9a55f9d06b`                                           |
| Connector取得branch-tip SHA | `707fefe47717dbed4afd3a9e266ced9a55f9d06b`                                           |
| SHA比較                     | byte-for-byteで完全一致                                                                   |
| Commit tree               | `d38b81aac41f03c7faaab06cca462d80b29d884f`                                           |
| Fixed point / merge-base  | `c6b7f161c4971c620f221c3faa82098ee3510be6`                                           |
| Reviewed range            | `c6b7f161c4971c620f221c3faa82098ee3510be6..707fefe47717dbed4afd3a9e266ced9a55f9d06b` |

実施したconnector操作は、GitHub操作のdiscovery、対象repositoryの取得、対象branch名による検索、対象branch endpointの直接取得、対象commitの直接取得、commit treeおよび同一SHAを指定したauthority・実装ファイルの取得です。対象branch以外のbranchおよびdefault branchは参照していません。Repository、branch、tip SHAはいずれもconnectorから直接確認済みです。

## Review・test証拠の整合

次の証拠はすべて候補SHA `707fefe47717dbed4afd3a9e266ced9a55f9d06b` に結び付いています。

| 証拠                                 |   SHA整合 | 結果                                          |
| ---------------------------------- | ------: | ------------------------------------------- |
| Strict review                      |      一致 | `review_status=fail`, `P0=0/P1=1/P2=0/P3=0` |
| Independent GPT-6 review           |      一致 | `review_status=fail`, `P0=0/P1=1/P2=1/P3=0` |
| Local focused/reference/full tests |      一致 | 記録上pass。ただし本分析では再実行していません                   |
| GitHub Actions run `35613537584`   |      一致 | 記録上7 jobsすべてsuccess                         |
| Pinned HTML/PlantUML               | **不一致** | `c6b7f161...`での過去結果のみで、候補SHAでは未実行           |

Primary packetの収集時刻は2026年9月21日15:00 UTC、すなわち2026年9月22日00:00 JSTです。レビュー生成自体は完了しており、Strict reviewの全文JSON、GPT-6 reviewの全文、再現条件、test結果、既知のcoverage gapが一つのbatchとして提示されています。

Review sourceとprovenanceは次のとおりです。

* Strict reviewer session: `required-strict-github-connector-verificati-1057`
* Strict transcript SHA-256: `c92adf14894b93511e52ae418bed22d2370c1893a72d1175556b645a0fa3d341`
* Strict reviewer: GPT-5.6 Sol、thinking level Extra High。session metadataと`output.log`による確認とされています
* Independent review artifact: `/root/issue8_plan008_gpt6_max_review`
* Independent lane: GPT-6 Astra / Maxを要求。完全な結果はpacketに含まれますが、browser pickerの直接証拠はありません
* Analyst session: 本応答のGPT-5.6 Sol Proによるinitial fresh analysis
* Continuity mode: fresh。以前のanalyst sessionをrepository factsの根拠には使用していません
* 本analyst sessionの外部session IDまたはtranscript digestは提供されていません

## Repository authority

正本はexact commit tree上のIssue #8 `requirement.md`、`design.md`、`plan.md`にある`Current v1 normative authority`です。実際のtracked pathは、`spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00008-generate-nextjs-component-snapshots/`配下です。

Current v1の主要命題は次のとおりです。

* Provenanceはrequest-independent not-applicable/failureとrequest-bound failure/successから成るclosed unionです。
* Observed rowは実際に観測した値のschema/versionとdigestを保持します。
* Failure stageより後のsuffixだけが`unobserved/null`になります。
* すべての公開surfaceは同じimmutable decision/final publicationを使用し、別経路で意味を再構築しません。
* `NextDecisionContext`と`NextPublicationContext`は、variantをまたいで同じsealed valueとstage-aware observed prefixを保持する設計です。
* I05-PLAN-008は、production unitであるI05-PLAN-002から007を開始する前に、固定SHAで`P0=0/P1=0/review_status=pass`を満たす必要があります。

Root `AGENTS.md`と`docs/contracts/next-publication-v1.md`はexact candidate treeに存在しないため、その内容はauthorityとして採用していません。Root tree自体はconnectorで確認済みです。

## Completeness判定

このbatchは、根本原因、response route、authorization境界を決めるには十分です。一方、readinessをpassと判定するには不完全です。Material gapは次の二点です。

1. Request-bound pre-response failureにおけるtarget completenessのcanonical semanticsが未確定です。
2. Candidate SHAに結び付いたpinned HTML/PlantUML evidenceがありません。

Production Node/OS/package実測は今回のreference-only gateの明示的non-goalであり、このbatchにおけるmaterial coverage gapとは扱いません。

# Executive disposition

**Batch-level dispositionはfailです。I05-PLAN-002からI05-PLAN-007は引き続き開始禁止です。**

Blocking要因は三つあります。

1. Strict finding S1は有効なsource-native P1です。`source_read` failureで、provenanceはsource/config/limits/source-planをobservedとする一方、publication contextとpublic projectionは同じ値をnullとし、Current v1のobserved-prefix contractに自己矛盾があります。
2. GPT-6 finding G1は有効なsource-native P1です。Validated requestが存在し、validated semantic responseが存在しないfailureで、rendererはtarget completenessを空にしますが、validatorはrequested targetsとの完全一致を要求します。
3. Candidate SHAでpinned HTML/PlantUML acceptanceを実行した証拠がなく、親policy上のmaterial coverage gapです。これにP severityは付与しません。

GPT-6のcompiler-option parity P2は、親policy上report-onlyであり、本gateを追加でblockせず、自動修正も認可しません。

主要な次の行動は、G1についてpublic target-completeness semanticsを人間が決定し、その決定後にS1とG1を一つのcoherentなreference-contract remediationとして扱うことです。その後、新しいclean pushed candidateに対するexact-SHA検証、candidate-bound acceptance、StrictおよびGPT-6のsame-reviewer re-reviewが必要です。

RC-OBS-001の意味上の修正は既存authorityから一意に導けます。しかしRC-TGT-002はpublic data semanticsが未確定です。同じpre-response state modelへ局所patchを重ねることはpatch chainingの構造シグナルに該当するため、現時点で分割実装へ進むことは推奨しません。

本分析invocationはread-onlyです。現在安全に進められるのはhuman decision packageの確定までであり、編集、test実行、Git操作、reviewer再実行、workflow進行は認可されていません。

# Root-cause groups

| Group ID      | 対応するitem                                                                         | Source-native classification | Root cause                                                                                               |            Blocking effect | Primary route                   | Authorization                                               |
| ------------- | -------------------------------------------------------------------------------- | ---------------------------- | -------------------------------------------------------------------------------------------------------- | -------------------------: | ------------------------------- | ----------------------------------------------------------- |
| `RC-OBS-001`  | Strict S1、およびprovenanceとpublication projection間のcross-view validation gap        | P1                           | Failure stageではなく「source sealの有無」と「request-independent」を同一視したため、observed prefixがpublication contextで消失する |                   Blocking | `implementation-remediation`    | 意味上は既存authorityから一意。ただし本invocationはread-onlyで、統合handoffは未認可 |
| `RC-TGT-002`  | GPT-6 G1、およびrequest-bound pre-response target completenessのcanonical gap         | P1                           | Request identityとsemantic target-resolution結果の区別がcanonical public contractで定義されていない                      |                   Blocking | `requirement-decision-required` | Human decision必須                                            |
| `RC-CFG-003`  | GPT-6 compiler-option parity finding。Source側にfinding IDなし                        | P2                           | Productionとreferenceのmalformed ignored-option acceptanceがdriftしている                                       | Non-blocking / report-only | `out-of-scope-follow-up`        | 本scopeでは変更未認可                                               |
| `RC-EVID-004` | Candidate-bound pinned HTML/PlantUML evidence欠落。Source finding IDおよびP severityなし | Material coverage gap        | Acceptance evidenceがcurrent candidateにfreshness-bindされていない                                               |                   Blocking | `finding-rebuttal`              | Code remediation不要。Exact-SHA evidence取得が必要                  |

S1とG1は、どちらもpre-response projectionを扱う点では関連しますが、同じgroupには統合しません。

* S1は、既に観測済みのsource/config/limits/source-plan値が別surfaceで失われる問題です。Canonical semanticsは明確です。
* G1は、request target identityは存在するがsemantic responseがない場合に、target completeness rowを何と意味付けるかという未決のpublic contract問題です。

GPT-6の「source_read remediation: pass」は独立findingではありません。また、run-decision provenanceや既存testがpassしたことを示していても、provenanceとpublication context/public config間のcross-view equalityを確認した証拠は提示されていないため、Strict S1をdisproveしません。

# Detailed adjudication

## `RC-OBS-001` — Stage-aware observed prefixの消失

### Claim validityとreachability

Strict S1のclaimは有効です。

Exact candidateの`source_acquisition_failure_decision()`は、実在する`result.seal`を要求し、`_source_read_failure_provenance(result.seal)`でsource/config/limits/source-planをobservedとして検証した後、requestを`None`としてpre-response failureを構築します。

その後のrequest-independent publication pathは、source sealが実在するにもかかわらず、publication contextへ`source_seal=None`を渡します。`NextPublicationContext`側も、sealがない場合はsource fingerprint、source plan、config-derived valuesをすべてnullとする一方、sealがある場合はtoolchainやtrusted environmentまで存在することを要求しています。すなわち現在のstate modelは、少なくとも次の三状態を表現できていません。

1. Source seal取得前のrequest-independent failure
2. Source seal取得後、request生成前の`source_read` failure
3. Source seal取得後、request-bound process/response pathへ進んだ状態

このため、`source_read` failureで実際に観測したprefixだけを保持し、後続suffixをnullにするCurrent v1のstage modelが、「sealなし」か「post-launch相当の完全seal context」の二択へ縮退しています。`NextPublicationContext`の現在の不変条件もこの二値化を強制しています。

Triggerはno-proof-rootおよびunsafe-proof-root、4 selectorsの全8経路で到達可能です。Explicit targetがある場合でもrequestは生成されず、target resolutionを主張しないというRG-01の境界と両立します。

### In-scope impactとblocking effect

影響はCurrent v1のmachine-checkable reference contractに直接及びます。同一wire内で次が同時に成立します。

* `decision_context.provenance_observation.observed`ではsource/config/limits/source-planがobserved
* `publication_context`およびpublic configでは同じ観測対象がnull
* `_validate_publication_chain()`はその矛盾を受理

これは単なる説明文の不一致ではなく、公開projectionの自己矛盾です。Source-native classification P1を維持し、親policyによりblockingと判定します。

### Violated authority

違反しているauthority propositionは次です。

> 実際に観測したstageまでの値は、そのactual valueに対応するdigestを持つobserved prefixとして保持し、failure stageより後のsuffixだけを`unobserved/null`にする。

Requirementとdesignはいずれもこの命題を明示しており、requestの有無とsource observationの有無を同一視する根拠はありません。

### First incorrect fault layerとroot cause

最初に誤っているfault layerは**reference implementation / generated projection state model**です。Requirementやcanonical designの意味は十分に明確です。

具体的なroot causeは、次の内部不変条件の誤りです。

* `request_independent == (source_seal is None)`と扱っている
* `source_seal is not None`なら、source-readより後のtoolchain/trusted-environment/process contextまで存在することを要求している
* Provenanceでobservedになったfieldとpublication context/public projectionをcross-checkしていない

Test不足は二次的です。既存testは各schemaを通すことを確認していますが、同じ観測値がsurface間で同じdigest/valueとして保持されることを確認していません。

### Primary response route

Primary routeは`implementation-remediation`です。

修正後も保持すべき保証は次です。

* Adapter requestは生成しない
* Semantic target resolution rowは生成しない
* Explicit target identityはdomain/config側に保持する
* `SOURCE-003`、`payload_unavailable`、exit 3、artifact不在を維持する
* Source/proof redaction、read-once、catalog path制約を維持する
* Public schema、diagnostic catalog、reason enum、APIを変更しない
* Production `src/`へ変更を波及させない

変更すべき保証は、「request-independentならsource-related contextはすべてnull」という誤った内部保証です。これを、「failure stageまでのobserved prefixを保持し、それ以後だけをnullにする」stage-awareな保証へ置き換える必要があります。

## `RC-TGT-002` — Request-bound pre-response target completenessの未定義

### Claim validityとreachability

GPT-6 G1のclaimは有効です。

Exact candidateのrendererは、すべての`PreResponseFailureDecision`に対してtarget resolution rowsを空配列として返します。

一方、reference validatorは、公開されたtarget rowsのkey集合がrequestの`targets`集合と完全一致することを要求します。さらにfailed rowにはclosed enum内の`reason`を要求します。

したがって、次の実pathで不整合が到達します。

* Validated adapter requestが存在する
* Explicit targetが一件以上存在する
* Response decodeまたはresponse validationで失敗する
* Validated semantic responseは存在しない
* 4 selectorsすべて

Response-decode failureとresponse-validation failureを合わせて8経路です。Targetless caseはpassします。

この問題はfixed point `c6b7f161...`にも存在していたため、`707fefe...`が新たに導入したregressionではありません。しかしI05-PLAN-008全体のCurrent v1 readinessをblockする既存P1です。

### Violated authorityとauthority gap

現在のlower-level artifactsには次の矛盾があります。

* Renderer: semantic responseがないのでtarget completeness rowsを空にする
* Validator: requestにtargetがあればtarget rowsを必須とする
* Schema: failed rowにはclosed reasonが必要
* Closed reason enum: 「requestは存在するがresponse以前なのでtargetを評価していない」という意味のreasonが存在しない

Higher authorityは、validated adapter responseに対するtarget completenessを要求しています。しかし、validated requestが存在し、validated semantic responseが存在しない中間状態について、次のいずれを採用するかを明示していません。

1. Rowsを空にし、request/config側だけにtarget identityを保持する
2. 各requested targetについてfailed rowを生成する
3. `unresolved`等の別variantを公開する

このため、違反命題を一意に定義できません。Current implementationの矛盾は確実ですが、正しいpublic meaningはauthorityから一意に導けません。

### First incorrect fault layerとroot cause

最初に誤っているfault layerは**requirement / canonical public-contract semantics**です。

Root causeは、次の二つの概念が区別されていないことです。

* Requestがどのtargetを要求したかというidentity
* Validated semantic responseに基づいて各targetがresolved/failedであったかというevaluation result

Requestが存在するだけではsemantic target resolutionは証明できません。しかし現在のvalidatorはrequest identityをそのままrow completeness obligationへ変換しています。

### Primary response route

Primary routeは`requirement-decision-required`です。

Public target-completeness data semantics、closed reason enum、consumer expectation、schema compatibilityに関わるため、reviewer recommendationだけで決定できません。Synthetic reasonを追加したり、既存reasonを意味不一致のまま流用したりすることも認可されません。

## `RC-CFG-003` — Compiler-option parity drift

GPT-6が報告した次の入力について、productionとreferenceが異なる結果を出すというclaimは、packet内のprobe結果により支持されています。

* `strict: []`
* `declaration: "yes"`
* `lib: "ES2022"`

Productionは`CONFIG-001/source_control`としてfail-closedに拒否し、referenceは`CompleteSourceSeal`として受理します。

Source-native classificationはP2です。Triggerはmalformedかつ未使用のoption shapeに限定され、productionはfail-closedであるため、親policy上はnon-blockingです。

最初のfault layerはreference parser/validation parityです。ただしRG-02 compiler-option parity repairは明示的non-goalであり、primary routeは`out-of-scope-follow-up`です。Production behavior、reference behavior、testsのどれを正本へ合わせるかは、別scopeでauthorityを再確認する必要があります。本batchでは変更しません。

## `RC-EVID-004` — Exact-candidate pinned evidenceの欠落

Planはpinned PlantUMLを含むacceptance evidenceを要求しています。

Packetにあるpinned HTML/PlantUML結果はfixed point `c6b7f161...`のものだけであり、candidate `707fefe...`では再実行されていません。変更がtest-onlyであることや、過去のrenderがpassしたことから、current candidateでもpassすると推定することはできません。

このitemにはsource-native P severityを付与しません。Parent policyがmaterial coverage gapを独立にblockすると定めているため、blockingです。

Primary routeは`finding-rebuttal`です。ここでrebutする対象は「現candidateのacceptance evidenceが完全である」という主張です。Product codeを変更する理由にはなりません。必要なのはexact candidateにbindしたfresh evidenceの取得であり、evidence collection自体を新しいremediation routeとして扱いません。

# Integrated response design

最小でcoherentなresponseは、次の順序です。

1. **現candidateをfailed baselineとして固定する。**
   `707fefe...`に対するS1、G1、test結果、coverage gapを履歴として保持し、既存結果を書き換えません。

2. **RC-TGT-002のpublic semanticsを人間が決定する。**
   Request identityとtarget evaluation resultの境界、pre-response failure時のrow obligation、schema/reason enumへの影響を確定します。

3. **必要なcanonical textを先に、または同一atomic change内で更新する。**
   意味を変える決定をimplementationだけに埋め込まず、Current v1 requirement/design/planから一意に読める状態にします。

4. **RC-OBS-001と承認済みRC-TGT-002を一つのreference-contract repairとして実装する。**
   Stage-aware observed-prefix projectionと、承認済みtarget-completeness ruleを同じpre-response state model上で整合させます。個別のif分岐、selector固有shim、source_read専用例外を積み増しません。

5. **Cross-view validationとstage-matrix testsを追加する。**
   Schema passだけでなく、provenance、publication context、public config、domain projectionの同一観測値が一致することを検証します。

6. **新しいcandidate SHAへすべてのverificationを再bindする。**
   Focused test、aggregate test、CI、pinned HTML/PlantUMLを同一の40文字SHAへ結び付けます。

7. **StrictおよびGPT-6のsame-reviewer re-reviewを独立に実施する。**
   Local analysisだけでP1をclosed扱いにしません。

## Affected surfaces

Human decision後に変更対象となり得るsurfaceは次です。

* `tests/contracts/next_reference_validation.py`

  * `source_acquisition_failure_decision`
  * `_publication_context_for_request_independent_failure`
  * `_seal_publication_context`
  * `NextPublicationContext.__post_init__`
  * `pre_response_failure_decision`
  * `_validate_publication_chain`
* `tests/contracts/test_next_contracts.py`

  * `_decision_target_resolutions`
  * source-read failure matrix
  * request-bound response-decode/response-validation matrix
* Issue #8 Current v1 `requirement.md`、`design.md`、必要に応じて`plan.md`

Option Aを採用する限り、次は変更対象外です。

* Production `src/`
* Node adapter、CLI、OS/runtime integration
* Public JSON shapeとschema version
* Diagnostic catalog、failure code、reason enum
* Compiler-option parity P2
* Issue state、workflow state、review history

Option BまたはCを採用する場合は、public schema、reason enum、versioning、consumer compatibilityまで影響範囲が広がるため、現在のbounded repairとは別のauthorizationまたはfresh scopeが必要です。

## State transitionとordering

想定されるstate transitionは次です。

`decision stop`
→ humanによるcanonical rule採択
→ reference-only repair authorization
→ First Redの固定
→ implementationとtests
→ exact-SHA verification
→ clean commit/push
→ same-reviewer re-review
→ gate判定

Human decisionより前にimplementationへ進める順序は認めません。

## Rollback・recovery

Option Aの範囲ではpersistent data、migration、external recovery procedureはありません。Rollbackはcanonical text、reference implementation、testsを同一単位でrevertすることで成立します。

ただし、canonical textだけ、またはimplementationだけを個別にrevertするとauthorityとbehaviorが再び分離するため、部分rollbackは禁止すべきです。Rollback後はcurrent failure probesが再現することを確認し、そのSHAを記録する必要があります。

## Patch chainingを止める構造シグナル

今回、同じpre-response invariantが次の別経路で繰り返し破れています。

* Request-independent `source_read` failure
* Request-bound response-decode/response-validation failure

さらに、現在の内部state ownerは「source sealの有無」「requestの有無」「validated responseの有無」「semantic target evaluationの有無」を一つの二値条件へ縮約しています。これは局所patchではなく、stage-aware state modelへ戻るべき構造シグナルです。

# Human decisions and authorization

## Parent authorization

既存のparent authorizationは、Issue #8のscoped implementationおよびcommit/push workflowを対象としています。しかし、次の制限があります。

* 本分析invocationはread-onlyです。
* 以前のauthorizationはbounded RG-01 projection correctionに対するものでした。
* Reviewer recommendationはpublic contract変更のauthorizationではありません。
* Public target-completeness semantics、reason enum、schema compatibilityを新たに決める権限は含まれていません。

RC-OBS-001のsemantic correctionは既存authorityから一意に導けます。一方、RC-TGT-002はhuman decisionが必要です。

## Decision package for `RC-TGT-002`

### Reproducible condition

Validated requestにexplicit targetが存在し、response decodeまたはresponse validationで失敗し、validated semantic responseが存在しない場合です。Rendererはrowsを空にし、validatorはrequested targetとの完全一致を要求します。

### 選択肢

| Option                                      | 意味                                                                                       | 保持する保証                                                 | 変更する保証・影響                                                                                              |
| ------------------------------------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------ |
| **A: pre-responseではrowsを空にする**              | Target identityはrequest/configに保持し、validated semantic responseがない限りresolved/failedを表明しない | False resolutionを避ける。新reason、schema field、version追加が不要 | Validatorのtarget completeness obligationをstage-awareに限定する。既存consumerが「空rows＝targetなし」と解釈している場合は説明更新が必要 |
| **B: requested targetごとにfailed rowを出す**     | Pre-response failureを各targetのfailureとして公開する                                              | Rowsとrequest targetの完全一致を維持                            | 適切な既存reasonがなく、新reasonまたは意味不一致の流用が必要。Public schema・compatibility decisionが必要                           |
| **C: unresolved/pre-response variantを追加する** | Resolution未実施をpublicに明示する                                                                | Target identityとevaluation stateを最も明確に分離               | Public schema、version、consumer、migration/compatibility範囲が最大になる                                         |

### 推奨

Option Aを推奨します。

理由は、validated semantic responseなしに各targetのresolved/failedを主張しないという既存RG-01の安全境界を維持し、synthetic reasonやpublic schema expansionを避けられるためです。一方で、これはvalidatorが現在表現しているpublic obligationを変更するため、人間による明示的採択が必要です。

**Candidate text — not adopted:** 検証済みadapter requestが存在しても、検証済みsemantic responseが存在しないpre-response failureでは、requested targetsはrequestおよびconfig identityに保持する一方、target completeness rowsは空とし、各targetのresolvedまたはfailedを表明してはならない。Target completeness rowsのtarget key集合をrequested targetsと完全一致させる義務は、validated semantic responseが存在するstageから適用する。

この文言を採用する場合、少なくとも次を明示する必要があります。

* `response_decode`と`response_validation`の両stageに適用すること
* 4 selectorsすべてで同じ意味を持つこと
* Empty rowsが「requested targetsなし」を意味しないこと
* Requested targets自体はrequest/config identityから失われないこと
* Requestだけからsemantic resolutionを再構築しないこと
* Existing failure reasonを意味不一致で流用しないこと

Option BまたはCを採用する場合は、public schema version、consumer compatibility、migration方針、既存artifactの扱いを追加決定しなければなりません。その場合は現在のrepair scopeを超えます。

# Implementation handoff

**現時点では、本batchに対するimplementation handoffは認可されません。**

理由は次の二点です。

1. `RC-TGT-002`のpublic-contract meaningが未決です。
2. `RC-OBS-001`だけを先行して同じpre-response state modelへ追加patchすることは、再発している同一invariantに対するpatch chainingとなります。

Implementation handoffが成立するための必要条件は、すべて次のとおりです。

1. Human ownerがOption A、B、Cのいずれかを明示的に採択すること。
2. Option BまたはCの場合、schema version、reason enum、compatibility、migration、既存consumerへの影響を別途承認すること。
3. Parent workflowが、RC-OBS-001と採択済みRC-TGT-002を一つのbounded reference-contract repairとして扱うことを承認すること。
4. 新しいimplementation invocationの冒頭で、repository、target branch、branch-tip full SHAを再検証すること。
5. Exact candidate上で対象pathとsymbolの存在を再確認すること。
6. Current candidate `707fefe...`で両First Redを再現し、その後の結果を新SHAへbindできること。

将来のhandoffで禁止すべき選択は次です。

* Existing reasonを意味不一致で流用する
* Request targetsからsemantic resolutionを推測する
* `source_read`専用またはselector専用のshimを追加してstate modelを回避する
* Public schema、API、diagnostic catalog、reason enumを無断変更する
* Production `src/`へscopeを拡張する
* P2 compiler-option parityを同じrepairへ混在させる
* Historical review resultを上書きする

次のいずれかが発生した場合、将来のimplementerは変更を続けず、parent workflowへstop-and-returnしなければなりません。

* Current authority間の新たな矛盾
* Public API、schema、data、security、migration、compatibility、rollback、recovery、operationへの予期しない影響
* Lower-layer contract変更が必要になった場合
* 対象pathまたはsymbolが存在しない、または前提と異なる場合
* First Redがcurrent candidateで再現しない場合
* Branch tipが検証済みSHAから移動した場合
* Option Aであるにもかかわらず新reasonまたはschema versionが必要になった場合

将来のimplementerが返す証拠は、parent-owned evidence packetに、full 40-character SHA、変更path/symbol、差分要約、各commandとexit status、test結果、artifact pointer/digest、想定との差異、stop conditionの有無を記録する形式でなければなりません。

# Verification plan

## Supplied results

以下はpacketから供給された結果であり、本分析では再実行していません。すべてcandidate `707fefe47717dbed4afd3a9e266ced9a55f9d06b`にbindされています。

| Evidence                        | Supplied result                                                 |
| ------------------------------- | --------------------------------------------------------------- |
| Source-read First Red           | 8 intended failures。Failed target rowにrequired `reason`がないことを確認 |
| Source-read focused Green       | 8 passed、462 deselected                                         |
| Reference module                | 470 passed                                                      |
| Current schema + reference gate | 589 passed                                                      |
| Full repository suite           | 1590 passed、1 skipped                                           |
| Ruff check / format check       | pass                                                            |
| Mypy                            | pass、145 source files                                           |
| SpecDock validate               | pass、nodes=10                                                   |
| Whitespace                      | `git diff --check` pass                                         |
| GPT-6 review suite              | 704 passed                                                      |
| GitHub Actions                  | Exact candidate SHA、7 jobsすべてsuccess                            |
| Pinned HTML/PlantUML            | Current candidateでは未実行                                          |

これらのgreen resultは、S1のcross-view contradictionまたはG1のexplicit-target pre-response pathを網羅していないため、両findingをdisproveしません。

## Future First Red / focused falsification

### `FR-OBS-001`

Current baseline `707fefe...`に対して、次のcross-view invariant testがfailureになることを示す必要があります。

* No-proof-root / unsafe-proof-root
* Targetなし / explicit targetあり
* 4 selectors
* Source-read failure stage

各caseで、少なくとも次を比較します。

* Provenance observed rowのschema/version/digest
* Publication contextのsource fingerprint、source-plan digest、limits/config value
* Public next config
* Public domain projection

同じobserved valueは同じidentityとして一致し、source-readより後のsuffixだけがnullでなければなりません。

### `FR-TGT-002`

Current baseline `707fefe...`に対して、次の8 failureを固定します。

* `response_decode` / `response_validation`
* Explicit targetあり
* 4 selectors

Targetless control 8件は引き続きpassすることを確認します。Human decision後は、採択されたruleに基づくassertionへ変更し、新candidateでgreenにします。

## Aggregate regression

新candidateの一つのfull SHAに対して、少なくとも次を再実行する必要があります。

* Focused source-read and request-bound pre-response tests
* `tests/contracts/test_next_contracts.py`
* `tests/contracts/test_json_schemas.py`
* `tests/unit/next`
* Full `pytest`
* `ruff check`
* `ruff format --check`
* `mypy src tests`
* `spec-dock validate`
* `git diff --check`

過去SHAでの結果を新candidateへcarry-forwardしてはなりません。

## Integration / runtime evidence

* GitHub Actionsのrequired jobsを新candidate full SHAにbindする
* Pinned HTML/PlantUMLを新candidateで実行する
* Generated artifactのpathまたはdigestを保存する
* Exact tested SHA、実行時刻、command、exit statusを保存する

Production Node、OS/package、CLI-to-Artifact acceptanceは現在のreference-only remediation scope外です。今回のpass条件へ暗黙に追加せず、production unit開始後の別gateに保持します。

## Semantic checkpoints

新candidateでは、次を機械的に確認する必要があります。

1. Observed prefixはactual valueのdigestを保持する。
2. Failure stageより後だけが`unobserved/null`になる。
3. Request absenceとsource-seal absenceを同一視しない。
4. Request target identityとsemantic target evaluationを同一視しない。
5. Source-read failureではrequestおよびsemantic target rowsを生成しない。
6. Request-bound pre-response failureでは、採択されたtarget-completeness ruleを全selectorで一貫して適用する。
7. 同一decisionから各public surfaceが生成され、別経路の再構築を行わない。

## Negative assertions

* Request未生成stageでrequestを捏造しない
* Validated semantic responseなしにtarget resolutionを主張しない
* Synthetic reasonを追加しない
* Option Aの場合、schema version、reason enum、public APIを変更しない
* Source bytes、proof、secret pathを公開しない
* Source rereadまたは暗黙retryを追加しない
* Selectorごとに異なるsemantic ruleを持たせない
* Compiler-option P2を同じchangeへ混在させない

## Rollback verification

Rollback手順は、canonical text、reference implementation、testsを同一commit単位でrevertするものとします。Rollback SHAで次を確認します。

* `FR-OBS-001`または`FR-TGT-002`が再び再現する
* Unrelated regression suiteは元の結果へ戻る
* Persistent data、migration、external recovery actionが存在しない
* Partial rollbackでauthorityとbehaviorが分離していない

すべてのfuture resultは、実行対象のfull 40-character SHAを明示しなければなりません。

# Same-reviewer re-review obligations

| Source item / group      | Original reviewer lane                                                     | 独立して再確認すべき内容                                                                                                                | Closureの扱い                                                                                                         |
| ------------------------ | -------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Strict S1 / `RC-OBS-001` | Strict reviewer lineage `required-strict-github-connector-verificati-1057` | Source-read matrix、observed-prefixとpublication context/public projectionの一致、request未生成、semantic target row未生成               | 修正を独立確認した場合はexpected closure。Claimが誤りと実証された場合のみdisproof。Authority変更がない限りsupersessionでは閉じない                         |
| GPT-6 G1 / `RC-TGT-002`  | Independent GPT-6 Astra/Max lane                                           | Response-decode/validation × 4 selectors、explicit-target/targetless controls、採択されたcanonical rule、consumer-visible semantics | Option Aで修正された場合はexpected closure。Option B/Cならapproved contract changeによるsupersessionとして明示。Decision未採択ならstill open |
| GPT-6 P2 / `RC-CFG-003`  | Independent GPT-6 lane                                                     | 本repairでは再確認を要求しない。Historical findingとして保持                                                                                  | Report-onlyかつstill open。別scopeでのみclosure可能                                                                         |
| `RC-EVID-004`            | Parent acceptance lane                                                     | New candidateでのpinned HTML/PlantUML command、result、artifact identity/digest                                                 | Exact-SHA evidenceが揃った場合のみcoverage closure。Semantic reviewerの意見だけでは閉じない                                            |

Same-reviewer re-reviewでは、個別findingだけでなく、同じroot causeのcompletion sweepが必要です。Sweep対象は次です。

* Applicability failure
* Source-control failure
* Source-read failure
* Process launch / budget failure
* Response-decode failure
* Response-validation failure
* Request-independent not-applicable/failure
* Request-bound failure/success
* Targetなし / explicit targetあり
* 4 selectors
* Observed-prefix consistency
* Target-completeness consistency
* Validated-decisionおよびnot-applicable既存projectionへの非回帰

Re-reviewは新しいclean pushed candidateのfull SHAに対して行い、現在のfail結果を上書きせず履歴として保持します。

# Parent workflow consequence

Parent-owned next consequenceは**stop for human decision**です。

次に必要なのは、`RC-TGT-002`についてOption A、B、Cのいずれをcanonical public contractとして採択するかの決定です。推奨はOption Aです。

Option Aが採択された場合は、次の順で現review campaignを継続できます。

1. Canonical textの採択
2. Bounded reference-contract repairのauthorization
3. RC-OBS-001とRC-TGT-002のcoherent implementation
4. Exact-SHA verification
5. Pinned HTML/PlantUML evidence取得
6. StrictおよびGPT-6 same-reviewer re-review
7. `P0=0/P1=0/review_status=pass`とmaterial coverage closureの確認
8. 親workflowによる次stage判定

Option BまたはCが採択された場合は、public schema、version、reason enum、consumer compatibilityが変わるため、現在のscope identityがsupersededされる可能性があります。その場合、fresh requirement/design approvalとfresh review campaignの要否をparent workflowが決めなければなりません。

次は引き続きblockedです。

* I05-PLAN-002からI05-PLAN-007
* Production adapter / Node / CLI work
* Issue #8 completion claim
* Current gateのpassまたはclosure
* P2の自動修正

次の操作は本skillの外です。

* Canonical artifactの編集
* Test実行
* Git commit/push
* Issue・PR・review thread操作
* Reviewerの再呼出し
* Workflow transition
* Gate closure
* Issue closure

# Assumptions and unresolved evidence

| 項目                               | 現在の扱い / invalidation condition                                                                                                                 |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| Branch-tip stability             | Connector確認時点では`707fefe...`と一致しています。Branch tipが移動した時点で、本packetのrepository bindingとpath/symbol exactnessは失効します                                  |
| Supplied test results            | Packetの証拠として採用しましたが、本分析ではcommandを再実行していません                                                                                                     |
| Strict transcript                | Packetに記載されたSHA-256を採用しています。Transcript本体は本分析で独立取得していません                                                                                        |
| GPT-6 reviewer provenance        | Requested laneと完全な結果はpacketにありますが、browser picker evidenceは未確認です                                                                                |
| Primary packet digest            | Artifact pathは提供されていますが、packet自体のdigestは提供されていません                                                                                              |
| Strict S1とGPT-6のsource-read pass | 異なるassertion範囲と解釈しています。GPT-6 raw evidenceがpublication context/public projectionとのcross-view equalityを明示的に検証していた場合、S1 adjudicationを再評価する必要があります |
| G1 semantics                     | 未決です。Option Aは推奨にすぎず、採択されていません                                                                                                                 |
| External consumers               | Empty target rows、reason enum、schema versionを利用するrepository外consumerの一覧と期待値は提供されていません。Option B/Cでは追加調査が必須です                                    |
| Pinned HTML/PlantUML             | Current candidateにbindした結果がなく、material coverage gapのままです                                                                                       |
| Compiler-option P2               | Packetのprobe結果を採用していますが、本分析では独立再現していません                                                                                                        |
| Production runtime evidence      | Node、OS、package、CLI-to-Artifact evidenceは未提供です。ただし現在のreference-only scopeではnon-goalです                                                          |
| Missing paths                    | Root `AGENTS.md`と`docs/contracts/next-publication-v1.md`はexact candidate treeに存在しません。内容を推定していません                                               |
| Future path/symbol exactness     | 本packetのpathとsymbolは`707fefe...`に対してのみ検証済みです。新candidateでは再発見・再確認が必要です                                                                          |
| Option A residual risk           | Empty rowsが「request targetsなし」と誤解される可能性があります。Target identityを別fieldで保持し、canonical textとconsumer checksで区別する必要があります                             |
| Closure authority                | Local remediation analysisはP1をcloseできません。Parent policyに従うsame-reviewerのcurrent-candidate passが必要です                                             |

## Parent verification notes (not part of the generated response)

- The exact-candidate Current v1 Design states that `NextDecisionContext` and `NextPublicationContext` carry the same sealed values across variants and that observed-prefix values retain actual-value digests. The Current v1 Plan includes pinned PlantUML among the pre-implementation acceptance checks. The reviewed range `c6b7f161..707fefe` changes provenance documentation and reference/test code, but not the pinned HTML artifact.
- The response labels the missing pinned-HTML evidence `finding-rebuttal`. The shared analysis contract treats evidence collection as a prerequisite, not a response route; preserve this as a parent acceptance-evidence obligation, with no P severity and no product-code remedy. The old result may only be reused if the parent establishes exact artifact identity and accepts that evidence; otherwise rerun the pinned check against the current candidate.
- The response's Option A is a recommendation, not an adopted contract decision. No production or canonical specification change is authorized by this analysis artifact.
