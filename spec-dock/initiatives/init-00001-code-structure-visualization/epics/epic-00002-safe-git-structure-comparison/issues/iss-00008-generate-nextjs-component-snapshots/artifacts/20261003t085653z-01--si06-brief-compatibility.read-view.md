# Binding and evidence completeness

## GitHub binding

| 項目 | 検証結果 |
|---|---|
| repository | `chemitaro/code-structure-viz` |
| target branch | `iss-00008-generate-nextjs-component-snapshots` |
| expected full SHA | `af6f5d33f9487a33dabf2ddfe41df85b3d8267fb` |
| GitHub branch-tip full SHA | `af6f5d33f9487a33dabf2ddfe41df85b3d8267fb` |
| SHA comparison | byte-for-byte一致 |
| fallback branch | 使用なし |
| repository source | 接続済みGitHubコネクタのみ |

GitHubコネクタでは、repository metadata取得、対象repository内のbranch検索、対象branchのexact endpoint取得、当該commitおよび当該commit上の正本・schema・reference・test取得を実施した。対象branch endpointが返したtipは期待SHAと完全一致した。別branch、default branchへのfallback、添付からのSHA代用は行っていない。

`af6f5d33f9487a33dabf2ddfe41df85b3d8267fb`は親commit `6d52ff7949d64e747235eef870631cd8cc29b273`に対するSI-05認定記録のdocs-only checkpointである。GitHub上のcommit file listでは、contract文書、Issue artifact、Plan、Report等が変更され、SI-06の`src/**`、`tests/**`、`schemas/**`実装は追加されていない。したがって、現在のrepository factsは`af6f...`に固定する一方、`6d52...`で取得されたコード試験結果を`af6f...`のSI-06実装試験へ昇格させない。

## Review source and artifact identity

今回のcurrent batchは次で構成される。

- analysis identity: `issue8-si06-final-owner-brief-admission`
- primary packet: 添付`si06-brief-compatibility-packet.md`
- raw author brief: `briefs/si06-diagnostics-final-owner.md`
- raw brief length: 2251 LF lines
- raw brief SHA-256: `89874d1617df851ada743baf716a6c32b835ca59b2773cf09a813d066ef8ad8f`
- completed recovery log SHA-256: `639a3bd15c9f6537a6c482b81dd84f90f3523f3d1e1fbc4c1789a0e651c21af0`
- probe script SHA-256: `7cb78da88a3364ddad67b47db9fec806d82c7eba17d6581c675871500d20905f`
- probe output SHA-256: `eac06a1e3128c6e578d60d02ad4f214dea1541aab6a1fa19ecd9136b13ac64be`

source authorはnative `issue8-si06-final-publicatio`、Blue conversation `6abf39d9-bdc0-83ee-96f7-79bde716eb7f`である。元wrapperのmechanical timeoutは同一会話内のrecoveryで回収され、matching user turnとpaired terminal answerが確認された。元briefはGitHub commit内のauthorityではなく、Workbench supplied evidenceとしてのみ扱った。attachments-bundle

review sourceは、完了済みImplementation Brief Strict advisoryと、そのbriefに対するprimaryの二つのadmission observationである。これはformal Code Review Strictのpass/fail結果ではなく、`review_status`もsource-native P severityも発行されていない。したがって本分析でもP0/P1/P2/P3を捏造しない。primaryはOracle reviewerではなくlocal read-only admission/probeであるため、primary reviewerのthinking levelは不明である。attachments-bundle

analyst provenanceは、同analysis identityに対するinitial fresh independent sessionであり、Blue author、previous reviewer、別SI analystの会話をrepository factとして流用していない。requested analyst modelは`gpt-5.6-sol / thinking pro`であるが、backend identityの独立attestationは本packetにない。

## Candidate, reviewed, and tested SHA alignment

- current candidate SHA: `af6f5d33f9487a33dabf2ddfe41df85b3d8267fb`
- brief reviewed base: `af6f5d33f9487a33dabf2ddfe41df85b3d8267fb`
- primary admission observationsの対象: 同じ`af6f...`
- read-only compatibility probe: clean `af6f...`を対象としたsupplied evidence
- SI-05 broad code testsとfresh review: `6d52ff7949d64e747235eef870631cd8cc29b273`
- SI-06 implementation/tested SHA: 存在しない
- SI-06 formal Code Review Strict SHA: 存在しない

したがって、**brief・primary observations・probeのidentityはcurrent candidateと整合しているが、SI-06実装closureとしてのreviewed/tested SHA alignmentは未成立**である。これはbrief-admission段階では予期された状態であり、現在のfindingへseverityを付与する理由ではない。probeもfinal-owner testやCode Review findingではなく、既存lower ownerとactual schema fragment間の表現可能性確認に限られる。attachments-bundle

## Authority inspected at the verified commit

次を`af6f...`上で直接確認した。

- Current `requirement.md`
- Current `design.md`
- Current `plan.md`
- accepted ADR参照とcurrent contract boundary
- `schemas/next-publication-decision-v2.schema.json`
- `schemas/next-publication-candidates-v3.schema.json`
- `schemas/next-domain-manifest-v2.schema.json`
- `schemas/stdout-result-v2.schema.json`
- `tests/contracts/next_publication_candidates_v3_reference.py`
- `tests/contracts/next_publication_candidates_v3_validation.py`
- `tests/contracts/next_run_decision_v3_reference.py`
- `tests/contracts/test_next_run_decision_v3.py`
- `tests/contracts/next_semantic_core_v3_reference.py`
- `tests/contracts/next_runtime_v2_reference.py`
- `tests/contracts/next_reference_validation.py`
- `tests/contracts/test_next_public_family_v3_schemas.py`

Current Requirementは、失敗stage以後の未観測値を`unobserved/null`として保持し、取得していない値や成功statusを補完しないこと、semantic statusを維持したままselected stdoutをfinal publicationで一度だけ測定することを正本命題としている。

Current Designは、既存public schema、`tests/contracts/next_reference_validation.py`、fixture/testの対応を維持baselineとし、semantic decisionとpublication decisionを分離し、capture・response・stderr・selected-copy measurementsを単一final ownerへsealする原則を維持している。

Current Planは、SI-06をcatalog-owned diagnostic/stderrとfinal single publication ownerのunitとし、reader prefix、新ASSET policy、production、全A02/A03を対象外にしている。SI-06 acceptanceにはruntime-only branch、64 KiB stderr境界、selected-copy境界、元captureとの分離が含まれる。

## Batch completeness and material gaps

このbatchは、**completed briefのadmissionを判断する目的にはcomplete**である。二件のcurrent observation、source-native classification、実際のtrigger、probe、parent policy、authority、scope、先行認定、実装制約、review provenanceが揃っており、whole-batch分析を開始できる。classification、claim validity、blocking effect、response route、authorizationを別々に判断するというattached semantic coreにも適合する。attachments-bundle

残るmaterial gapは一件である。

- `CG-01`: paired-null captureをpublic final publication contractへ採用する際、既存`next-publication-decision-v2`を明示的に訂正・supersedeするか、successor versionを導入するか、およびconsumer compatibilityをどう扱うかについてcanonical human decisionがない。

次はmaterial gapではなく、future closure obligationである。

- SI-06 final-owner implementation、focused tests、aggregate tests、runtime/integration evidence、fresh Code Review Strictは未実施である。current objectiveは実装前brief admissionなので、これをcurrent review failureへ変換しない。
- primary sourceはformal code reviewではないため、same-reviewer pass/fail closureは存在しない。
- packetが主張するlocal worktree clean状態はsupplied evidenceであり、GitHub connectorが検証したのはremote branch tipとcommit内容である。

# Executive disposition

**Batch-level disposition: SI-06実装ブリーフは現状のままではadmit不可。`RC-01`について`requirement-decision-required`で停止し、人間によるpublic-contract／compatibility判断を先行させる。**

`SI06-BA-F1`は実在する問題である。到達可能なrequest-bound `stage_failed` branchではlower candidateが`adapter_stdout=null`、`adapter_stderr=null`を正しく所有する一方、current outer publication schemaは両fieldにnon-null measurement objectを必須とする。現在のbriefどおりにfinal ownerを実装すると、0埋め、架空overflow、branch除外、またはschema違反のいずれかを選ばざるを得ない。これはaccepted null/zero distinctionとpublic contractのmaterial conflictであり、parent policy上、SI-06 final-owner implementationをblockする。source-native P severityはunsetのまま維持する。attachments-bundle

`SI06-BA-F2`は、二つに分けて判断する。

1. `publication_outcome=payload_unavailable` branchが`response=null`を強制するという事実は正しい。
2. validated Core unavailableのすべてをそのpublication branchへ送る、という前提は正しくない。

Current Designと維持baselineはsemantic/run outcomeとfinal publication outcomeを分離している。final capture・public stderr・selected-copy boundaryが成功した場合、semantic outcomeが`payload_unavailable`かつexit 3でもpublication outcomeは`published`でよい。`ValidatedSemanticDecisionV3`であれば同じvalidated retained responseのlinkを保持できる。したがってF2はmaterial design conflictではなく、briefのoutcome mappingを既存意味に合わせる`documentation-correction`で一意に閉じられる。attachments-bundle

認可状態は次のとおりである。

- F2のbrief clarification: 既存authorityから一意であり、consumer rights、risk、guaranteeを変えないためparentがadvisory wordingへ採択可能。
- F1のpublic schema／version／consumer compatibility変更: analyst、author、reviewerのいずれにも自律実装権限なし。人間決定、canonical spec反映、Spec Review Strictが必要。
- 現時点のimplementation handoff: **認可なし**。
- 現時点で安全に進められる作業: F1 decision packageの採択、canonical spec/schema-version方針の決定、F2 brief wordingの訂正準備まで。

# Root-cause groups

| Group ID | Source item / gap | Source-native classification | Shared invariant / root cause | Primary route | Blocking / authorization |
|---|---|---|---|---|---|
| `RC-01` | `SI06-BA-F1`, `CG-01` | `primary-observed representability gap; P severity unset` | lower ownerが保持する「未観測」と「観測済み0」を、outer final publication contractが別状態として表現できない。物理schemaがaccepted observation-state modelを一状態へ潰している。 | `requirement-decision-required` | SI-06 implementation admissionをblock。public contract／compatibilityの人間決定が必要。 |
| `RC-02` | `SI06-BA-F2` | `primary-observed conditional mismatch needing adjudication; P severity unset` | briefがsemantic availabilityとpublication boundary outcomeを同一軸のように記述し、validated response eligibilityとfinal publication failureを混同している。 | `documentation-correction` | 単独ではblockしない。既存authority内の一意なclarificationとして採択可能。 |

## Deliberate non-grouping

- empty SHAの不完全なprose exampleはsource自身がnon-oracleと明記しており、実装・schema・policyへ到達しない。current batchのmaterial itemではなく、briefを再発行する場合の単純なtext correctionに限る。
- optional publication back-referenceをlive bytesから省略する点は、current optional fieldと非再帰sealに整合し、第三findingとして成立していない。
- SI-06実装・test・review evidenceの不存在は、brief-admission段階のexpected stateである。current semantic findingへ変換せず、future verification obligationとして扱う。
- F1とF2は同じfinal owner周辺に現れるが、root causeは異なる。F1はpublic state representation、F2はoutcome-axisのbrief説明であり、同一patchとしてまとめない。
- F1のzero-fill、branch exclusion、schema-wide relaxationは別groupではなく、`RC-01`に対する不正な症状patchである。

# Detailed adjudication

## RC-01 — Capture observation-state collapse

### Claim validity

claimは成立する。

current candidate ownerは、runtime observationの`capture`が存在する場合にだけcapture objectを生成し、`capture is None`の場合は`adapter_stdout`と`adapter_stderr`をともに`None`へする。

independent validatorも、同じretained runtime observationからexpected valueを再導出し、capture absentなら`None`、presentならactual integer counts、EOF、limitを要求する。producerのcacheやcaller-supplied defaultをauthorityにしていない。

candidate schemaは両captureをそれぞれnullableにしつつ、closed `oneOf`で「両方null」または「両方capture object」の二状態だけを許す。片側nullは認めない。

一方、`next-publication-decision-v2`は`measurements.adapter_stdout`、`adapter_stderr`、`public_stderr`、`selected_stdout`の四つを必須とし、各fieldを`allowed:boolean`、`measured_bytes:integer`、`retained_bytes:integer`を持つnon-null measurement objectに固定している。

したがって、lower ownerの合法stateをouter contractへlosslessに写像できない。

### Trigger reachability

exact repository test path `tests/contracts/test_next_run_decision_v3.py::test_runtime_only_run_has_no_core_fingerprint_or_semantic_suffix`の`stage_failed` caseは、次を構成する。

- `spawn=None`
- `capture=None`
- `exit_code=None`
- provenance stage `node_spawn`
- failure code `CSV-NEXT-NODE-002`
- run outcome `payload_unavailable`
- Core、run fingerprint、compatibility suffixなし

そのrunからcandidates-v3を構成するとcapture measurementsはpaired nullになる。

supplied probeも同じ既存owner pathを使用し、`runtime_capture=null`、candidate captures両null、publication measurement null reject、zero object acceptを確認している。これはlive production OS proofではないが、current reference/integration contract内での到達性とschema不整合を示すのに十分である。attachments-bundle

### In-scope impact and blocking effect

影響はSI-06のaccepted scope内である。Current Planとbriefはlower runtime-only failureをpositive coverageに含み、final ownerがdomain/root/summary/stdout/stderr/exitを一元投影することを要求する。stage_failedだけをfinal ownerから外すと、SI-06のruntime-only coverageとsingle-owner guaranteeを狭める。

current schemaへ合わせるための次の処理はいずれも不正である。

- `null`を`measured_bytes=0`へ変換する: 未観測を観測済み0へ捏造する。
- `null`を`allowed=false, measured_bytes=0`へ変換する: 未観測をcapture boundary failureへ捏造する。
- limit+1値を合成する: 実際に存在しないoverflow observationを作る。
- stage_failed branchをfinal publicationから除外する: required coverageとsingle-owner projectionを破る。
- lower runtime/candidates schemaをobject-onlyへ戻す: accepted null/zero distinctionを壊す。
- broad `anyOf`や`additionalProperties`でschema全体を緩和する: intended paired-null invariantを失う。

よってparent policyの「material authority conflictが残る場合のみSI-06をblockする」に該当する。blockingはseverityによるものではなく、accepted stateを正直に表現できる実装が現契約内に存在しないことによる。

### Violated authority and exact proposition

違反している命題は次である。

1. 観測していない値は補完せず、失敗stage以後は`unobserved/null`とする。
2. actual missing observationとacquired zeroを区別する。
3. final ownerはlower captureを再実行せず、同じretained ownerから投影する。
4. 全public projectionは単一final publication ownerのsealed resultから出す。
5. required runtime-only branchを除外しない。

Current Requirementは未観測値を補完しないことを明記し、Current Designはsemantic/publication single-ownerと実captureのsealを要求する。

不満足な物理命題は、`schemas/next-publication-decision-v2.schema.json#/$defs/measurements`が、`next-publication-candidates-v3.capture_measurements`の合法paired-null stateを表現できないことである。

### First incorrect fault layer

最初に誤っているlayerは、lower runtime、run-v3、candidates-v3、test fixtureではない。これらは同じownerからpaired nullを保持し、independent validatorも再導出している。

最初のfault layerは、**public integration contract／schema projection**である。具体的には`next-publication-decision-v2`の`$defs.measurements`が、既存observation-state modelの一状態を欠落させた点である。author briefのsection 16/32はそのschemaを前提に「すべてnative integer」と書いたため、二次的に同じ欠落を継承している。

### Root cause

root causeは、「measurement value」と「measurement existence」を一つのobject shapeに統合したことである。

- observed 0: measurementは存在し、その値が0
- unobserved: measurement自体が存在しない
- observed overflow: measurementは存在し、`allowed=false`

これら三状態を、常に存在する`allowed/measured/retained` objectだけでは正確に表現できない。

### Primary response route

`requirement-decision-required`

semantic directionは既存authorityから一意であるが、修正対象がversioned public contractであり、consumer acceptance、schema versioning、compatibility、既認定SI-05 contractのsupersessionを伴う。attached semantic coreはpublic contract、data semantics、migration、compatibilityの変更をhuman decisionへ返す。attachments-bundle

### Preserved and changed guarantees

**保持する保証**

- missing observationとobserved zeroの区別
- paired capture状態
- no recapture
- lower runtime/run/candidates owner identity
- observed measurementのnative integer／bool
- semantic outcomeとpublication outcomeの分離
- stage_failedのexisting code/stage
- single immutable final owner
- no partial selected stdout
- no raw child stderr/private proof publication

**変更を要する可能性がある保証**

- `next-publication-decision-v2.measurements.adapter_stdout`と`adapter_stderr`のaccepted public shape
- 旧consumerが「常にobject」と仮定できるという互換性
- in-place訂正の場合、SI-05 schema certificationのsupersession状態
- successor versionの場合、outer exact refsとconsumer migration範囲

### Existing-authority result for the stage_failed branch

public contractの採択後に満たすべき意味は一意である。

- semantic/run outcome: `payload_unavailable`
- final `response`: `null`
- artifacts: empty
- adapter capture measurements: paired `null`
- public stderr measurement: actual object
- selected stdout measurement: actual pre-copy object
- final publication outcome: final publication boundariesが成功すれば`published`
- exit code: `3`
- selected output: selectorに応じたsummary／manifest／typed unavailable
- `null` capture自体を`payload_unavailable` publication failureとして数えない

これは新policyではない。current baselineはpublication outcomeをcapture overflow、public stderr failure、selected-copy failureから決め、semantic exit 3だけではpublication outcomeを失敗へ変えない。current schemaも`published`とexit 3の組合せを許している。

ただし、この意味をどのschema versionへ採用するかは未決定である。

## RC-02 — Semantic outcome / publication outcome conflation

### Claim validity

F2の事実部分は成立する。current schemaの`publication_outcome=payload_unavailable` branchは、`response=null`、artifact empty、stdout unavailableを要求する。

ただし、「validated Core unavailableはすべてpublication `payload_unavailable`になる」という前提はrepository authorityにない。current schemaは`published`にexit 3を許し、responseをnon-nullにできる。current maintained baselineの`PublicationBoundaryDecision`は、semantic decisionのexitとpublication boundary outcomeを別に計算する。

したがって、

- conditional mismatchの観測: valid
- unconditional schema contradiction: unsupported
- validated semantic unavailableのmapping全体が未立証というprimaryの留保: correct
- existing authorityを追跡した後の結論: 一意に解消可能

### Reachable trigger classes

validated Core unavailableとして扱うbranchは次である。

- `CSV-NEXT-SOURCE-003`
- `CSV-NEXT-TARGET-001`
- `CSV-NEXT-EXPORT-001`
- entity budget `CSV-NEXT-LIMIT-005`

これらは`ValidatedSemanticDecisionV3`を保持し、`gate.payload_available=false`でもvalidated transport candidate、request identity、canonical response receipt、validated model digestを失わない。

別classとして次がある。

- `RejectedSemanticDecisionV3`
- model-record limit rejection
- runtime-only failure
- pre-response/stage failure

これらをvalidated semantic response authorityへ昇格させてはならない。Current V3 Coreは`ValidatedSemanticDecisionV3`と`RejectedSemanticDecisionV3`をnominally分離している。

### Exact authority proposition

current baselineではpublication outcomeは次のpriorityで決まる。

1. 観測済みadapter captureのbyte-boundary failure、またはfinal public-stderr failure
   → `payload_unavailable`
2. selected-copy failure
   → `selected_artifact_unavailable`
3. それ以外
   → `published`

semantic decisionのexitが3でも、3番目ならpublicationは`published`、exitだけ3になる。`response`は、validated response bytesが存在し、final publication outcomeが`payload_unavailable`でない場合に保持される。

このpriorityをV3 ownerへ適用すると次になる。

| Semantic owner / boundary | Final publication outcome | response | artifacts | exit |
|---|---|---|---|---|
| Validated Core available、全boundary成功 | `published` | non-null | requested artifacts | semantic exit |
| Validated Core unavailable、全boundary成功 | `published` | non-null | empty | `3` |
| Rejected Core、全boundary成功 | `published` | null | empty | `3` |
| runtime-only failure、全boundary成功 | `published` | null | empty | `3` |
| selected-copy failure | `selected_artifact_unavailable` | validated Coreなら保持、otherwise null | semantic artifactsは保持可能 | `3` |
| observed capture overflow | `payload_unavailable` | null | empty | `3` |
| final public-stderr overflow | `payload_unavailable` | null | empty | `3` |
| selected failure diagnostic追加後のstderr overflow | `payload_unavailable` | null | empty | `3` |

`published`は「semantic payloadがavailable」という意味ではなく、「final publication boundaryが結果を正常にseal・publishできた」という意味である。

### Response / outcome priority

final ownerは次の順で決めなければならない。

1. semantic owner typeからresponse eligibilityを決める。
   - exact `ValidatedSemanticDecisionV3`: eligible
   - `RejectedSemanticDecisionV3`または`None`: ineligible
2. validated Coreの場合だけ、同じ`ValidatedTransportCandidateV2`から`request_id`、canonical raw response SHA-256、validated `model_digest`、byte lengthを導出する。
3. final publication outcomeを、semantic outcomeではなくactual boundary measurementsから決める。
4. final outcomeが`payload_unavailable`なら、eligible responseもpublic projectionでは`null`へ落とし、artifactも空にする。
5. `published`または`selected_artifact_unavailable`なら、eligible response linkを保持する。

lower run receiptだけからrejected modelの`model_digest`を合成してはならない。

### First incorrect fault layer

最初のfault layerは**documentation／advisory brief**である。

- physical schemaは`published + exit3 + non-null response`を許す。
- maintained baseline finalizerはsemantic outcomeとpublication outcomeを分離する。
- brief section 17はvalidated unavailableでresponse保持を正しく示す。
- brief section 20/32がnormal unavailable publication outcomeを明示しないため、section 17との関係が曖昧になっている。

schema、lower owner、accepted designを変更せず、briefのmappingを明文化すれば閉じられる。

### Primary response route

`documentation-correction`

これはbehaviorやaccepted meaningを変えず、advisory recordだけを正すrouteである。parentは既存authorityに沿うclarificationとして採択できる。新wire、新policy、schema変更はF2解決には不要である。

### Preserved and changed guarantees

**保持する保証**

- validated response identity
- rejected/runtime responseの非昇格
- semantic outcomeの不変
- final boundary failure時のresponse null
- artifact unavailability
- exit 3
- selected-copyとsemantic decisionの分離
- exact retained bytesからのlink導出

**変更する保証**

- なし。変更対象はbriefの説明だけである。

# Integrated response design

## Smallest coherent response

whole batchへの最小coherent responseは、二段階である。

1. `RC-01`について、paired-nullをpublic final publication contractへどう採用するかを人間が決定し、canonical specとschema-version policyへ反映する。
2. その採択済み意味を前提としてbriefを改訂し、同時に`RC-02`のsemantic/publication outcome mappingを明文化する。

F2だけを訂正してSI-06実装へ進むことはできない。F1を0埋め等で局所patchすることもできない。

## Capture-state projection

採択後のbounded designは次のclosed mappingである。

| Lower candidates-v3 state | Final adapter measurement state |
|---|---|
| stdout/stderrとも`null` | stdout/stderrとも`null` |
| stdout/stderrともcapture object | stdout/stderrともmeasurement object |
| 片側のみ`null` | reject |
| callerが合成したmeasurement | reject |
| fresh equal-content foreign owner | reject |

observed capture objectの変換は次に限定する。

- `measured_bytes = captured_bytes`
- `retained_bytes = capture_retained_bytes`
- `allowed = captured_bytes <= limit_bytes`
- `eof`やruntime terminal causeをcapture byte-overflowへ再分類しない
- `allowed`、count、limit、retained bytesをcaller引数として受けない
- independent validatorがsame runtime/candidates ownerから再導出する

`timeout`、`write_failed`、`read_failed`、child protocol failureは、それぞれの既存failure identityを維持する。capture objectが存在しbyte cap内なら、別failureであることを理由に`allowed=false`へ変えない。

## Final outcome state transition

1. same candidates-v3 ownerをvalidateする。
2. semantic owner typeとrun outcomeを保持する。
3. base catalog diagnosticsを導出する。
4. immutable domain/root/summary/stdout candidatesを構成する。
5. selectorが選ぶ**pre-copy candidate**を確定する。
6. `len(pre_copy_candidate)`を一度だけ測定する。
7. selected-copy failureならpublication-level `CSV-NEXT-LIMIT-003`を追加する。
8. 追加後のfinal diagnostic setをcanonical JSONLへencodeし、public stderrを一度だけ測定する。
9. response eligibility、artifact retention、publication outcome、exitを決定する。
10. pre-copy candidate measurementと、最終stdout/stderr bytesのdigestを別々にfinal sealへ含める。
11. domain/root/summary/stdout/stderr/exitの全getterはsealed resultだけを返す。

selected-copy failure後のfailure manifestやtyped unavailable bytesを、再びselected-copy gateへ渡してはならない。pre-copy measurementは元candidateに対する一回の測定であり、final bytesはその結果から構成される別projectionである。

## Pre-copy versus final bytes boundary

### Success

- measurement target: pre-copy candidate
- selected retained bytes: pre-copy candidateとbyte-identical
- final stdout bytes: retained pre-copy bytes
- result digest: actual final stdout bytes

### Selected-copy failure

- measurement target: 元pre-copy candidate
- measured size/hash: 元candidateの値を保持
- retained selected bytes: 0
- partial bytes: 0
- semantic decision: 不変
- artifact descriptor: 不変
- publication outcome: `selected_artifact_unavailable`
- final stdout bytes: canonical typed unavailable result
- failure manifest/summary: final statusを反映して構成可能だが、再measure／recopyしない

### Final public-stderr failure

- final diagnostic set全体を一度だけ測定
- 65,537 bytesならstderrはempty、partial 0
- manifest diagnosticsはreplacement `CSV-NEXT-LIMIT-003`一件
- replacement rowをstderrへ出さない
- publication outcomeは`payload_unavailable`
- nested semantic/run identityは変更しない

## Expected mutations

人間がin-place v2訂正を採択した場合のconditional affected surfacesは次である。

- `schemas/next-publication-decision-v2.schema.json`
  - `$defs.measurements`
  - adapter stdout/stderrのpaired nullable rule
- `tests/contracts/test_next_public_family_v3_schemas.py`
  - paired-null positive vector
  - one-sided-null／zero-substitution negative vectors
- planned `tests/contracts/next_final_publication_v2_reference.py`
- planned `tests/contracts/next_final_publication_v2_validation.py`
- planned `tests/contracts/next_final_publication_v2_fixtures.py`
- planned `tests/contracts/test_next_final_publication_v2.py`
- adopted spec/contract record
- revised SI-06 brief

successor versionを採択した場合は、加えてそのversionを参照するouter schemaとconsumer exact refsがaffected surfaceになる。これはin-place案より広く、暗黙には行わない。

## Required non-mutations

次は変更しない。

- `RetainedRuntimeResultV2`
- `RetainedRequestBoundRunDecisionV3`
- `RetainedRequestBoundPublicationCandidatesV3`
- candidates-v3 paired-null semantics
- `ValidatedSemanticDecisionV3`／`RejectedSemanticDecisionV3`
- source/proof/Core semantics
- catalog code/message/ref permission
- SOURCE/TARGET/EXPORT/LIMIT/PROTOCOL/NODE identity
- reader-owned prefix
- 未採択ASSET policy
- run-level usage/fatal/interrupted policy
- `src/**`
- TypeScript、Node、OS、CLI、package、dependency、lock、license
- legacy ownerへのcast
- old schema/KAT/golden
- optional backrefの新fixed-point rule

planned final owner pathはverified `af6f...`には存在せず、packetでもnew planned pathsとして定義されている。attachments-bundle

## Compatibility and rollback implications

### In-place v2 correction

利点は変更surfaceが最小で、現在のouter exact refsを維持できることにある。既存object-only recordは引き続きvalidにできる。

ただし、古いconsumer validatorは新しいpaired-null recordを拒否するため、「producer側だけのbackward-compatible変更」ではない。採択には次の明示が必要である。

- SI-05 v2 contract certificateを訂正後schemaでsupersedeすること
- production／external consumerが未存在、または同時更新されること
- schema、producer、validator、fixturesを同一candidateで切り替えること

rollbackはschema、producer、validator、exact referenceを一緒に戻す。producerだけpaired-nullを出し、consumerが旧object-only schemaのままになるmixed stateを許さない。

### Successor version

既存v2を不変にできるが、新schema identity、outer exact refs、consumer selection、migration／rollback ruleが必要になる。新wireやdual pathをSI-06内で暗黙に発明してはならない。

## Structural stop signals

次が判明した場合は局所patchを中止し、再びhuman decisionへ返す。

- paired null以外の第三capture stateが必要
- adapter stdout/stderrの片側だけunobservedが必要
- 新しいstate discriminator、API、persistence、migration、dual readerが必要
- lower ownerのmeaning変更が必要
- final owner以外にstatus/count/hash authorityを追加する必要
- recursive backref/fixed-point hashが必要
- schema changeがouter public contract全体へ連鎖する
- state owner、source of truth、pre-copy commit pointを一文で説明できない

# Human decisions and authorization

## Parent authorization source and limits

parentは、既存authorityから一意でconsumer guaranteeを変えないclarificationのみ自律採択できる。materialなdesign、public data/API、compatibility、migration、security、policy変更はhuman decisionと先行spec checkを要する。reviewer recommendationやfinding classificationは編集許可ではない。attachments-bundle

analystはread-onlyであり、schema、brief、test、code、Git、Issue、review stateを変更しない。

## Uniquely determined corrections

次は新しいproduct decisionを要しない。

- missing captureはzeroではない。
- paired nullを片側objectへ変えない。
- stage_failed branchを除外しない。
- lower ownerを再captureしない。
- normal validated semantic unavailableは、final boundary成功時にpublication `published`／exit 3とする。
- validated Coreだけがresponse link eligibleである。
- final `payload_unavailable`ではresponseをnullにする。
- selected-copy overrunはsemantic outcomeを変更しない。
- pre-copy candidateを一回だけ測定する。
- rejected/runtime modelをvalidated semantic responseへ昇格しない。

F2 brief clarificationはこの範囲である。

## Material human decisions

人間が決める必要があるのは次である。

1. paired-nullをcurrent `next-publication-decision-v2`へin-place採用するか。
2. 既存versionのimmutabilityまたはconsumer compatibility上、successor publication-decision versionを作るか。
3. in-placeの場合、SI-05 certificateをどのcanonical artifactでsupersedeするか。
4. successorの場合、outer四schemaとconsumer exact refsをどの単位で移行するか。
5. external／persistent consumerが存在するか、および同時更新、compatibility、rollbackをどう保証するか。

**推奨**は、production final ownerとexternal consumerが未存在であることをparentが確認できる場合に限り、v2をtargeted paired-null ruleで訂正し、SI-05 schema/public exact-ref認定を明示的にsupersedeしてfresh spec/schema reviewを取り直す案である。これは最小surfaceであるが、human adoption前には実行できない。

versioned public contractを一度認定した後は不変とするpolicy、または既存consumerの存在が確認された場合は、successor versionを選ぶべきである。その場合は新wireを暗黙に導入せず、別途migration decisionを採択する。

次の文言はdecision候補であり、正本ではない。

Candidate text — not adopted: `next-publication-decision`の`measurements.adapter_stdout`と`measurements.adapter_stderr`は、対応する`next-publication-candidates/v3.capture_measurements`が両方`null`の場合に限り、両方`null`とする。`null`はprocess captureが未観測であることを表し、0-byte observation、`allowed=false`、capture overflowのいずれも意味しない。片側だけの`null`、`null`のzero object化、final ownerによる再captureは禁止する。`public_stderr`と`selected_stdout`は常にmeasurement objectとする。

Candidate text — not adopted: final publication outcomeは、観測済みadapter captureのbyte-boundary failureまたはfinal public-stderr failureなら`payload_unavailable`、selected-copy failureなら`selected_artifact_unavailable`、それ以外は`published`とする。selected-copy failure用diagnosticを含むfinal stderrがoverflowした場合は`payload_unavailable`を優先する。paired-null captureはcapture failureと数えない。semantic/run outcomeはdomain/root statusとexitへ保持し、normal publication outcomeへ流用しない。

Candidate text — not adopted: exact `ValidatedSemanticDecisionV3`が`payload_available=false`でも、final publication boundaryが成功した場合は`publication_outcome=published`、`exit_code=3`とし、同じretained transport candidate由来のresponse linkを保持する。artifactsはemptyとし、selected domain outputはtyped unavailableとする。`RejectedSemanticDecisionV3`、runtime-only failure、またはfinal `publication_outcome=payload_unavailable`では`response=null`とする。

Candidate text — not adopted: response linkの`request_id`、`raw_sha256`、`model_digest`、`byte_length`は同一`ValidatedSemanticDecisionV3.transport_candidate()`が所有するcanonical responseからのみ導出する。lower run descriptor、caller input、rejected child payload、equal-content foreign ownerから補完しない。

いずれかのpublic contract文言を採択した場合、実装前にcanonical R/D/Pまたはaccepted contract artifactへ反映し、Spec Review Strictを通す必要がある。

# Implementation handoff

**現時点ではimplementation handoffを認可しない。**

理由は、`RC-01`のcorrect semantic directionは確定しているものの、public schema version、consumer compatibility、SI-05 certification supersessionが未決定だからである。implementerへ「v2を変更する」「v3を作る」のどちらかを選ばせることは、scope、public contract、migration、risk acceptanceを委譲することになる。

implementation handoffが成立するために必要な先行条件は次である。

1. paired-null semanticsとpublication outcome priorityのhuman adoption。
2. in-place v2またはsuccessor versionの明示決定。
3. compatibility、consumer、rollbackのcanonical decision。
4. R/D/P、accepted ADRまたはcurrent contractへの反映。
5. そのspec candidateに対するSpec Review Strict pass。
6. 新しいexact full SHAのGitHub connector再検証。
7. 採択済みcontractに合わせて改訂されたSI-06 brief。
8. parentからの独立したimplementation authorization。

採択後のhandoffが対象にできるverified existing symbolsは次である。

- `schemas/next-publication-decision-v2.schema.json#/$defs/measurement`
- `schemas/next-publication-decision-v2.schema.json#/$defs/measurements`
- `RetainedRequestBoundPublicationCandidatesV3`
- `retain_request_bound_publication_candidates_v3`
- `validate_request_bound_publication_candidates_v3`
- `RetainedRequestBoundRunDecisionV3`
- `ValidatedSemanticDecisionV3`
- `RejectedSemanticDecisionV3`
- `ValidatedTransportCandidateV2`
- `test_runtime_only_run_has_no_core_fingerprint_or_semantic_suffix`

conditional planned targetsは次である。

- `tests/contracts/next_public_diagnostic_v3_reference.py`
- `tests/contracts/next_public_diagnostic_v3_validation.py`
- `tests/contracts/next_final_publication_v2_reference.py`
- `tests/contracts/next_final_publication_v2_validation.py`
- `tests/contracts/next_final_publication_v2_fixtures.py`
- `tests/contracts/test_next_public_diagnostic_v3.py`
- `tests/contracts/test_next_final_publication_v2.py`

handoff作成後も次は禁止する。

- nullの0埋め
- stage_failed branchの除外
- caller-supplied status／count／hash／outcome
- old ownerへのcast
- lower captureの再実行
- broad schema relaxation
-片側nullable
- 新ASSET policy
- reader-prefix実装
- catalog code/message変更
- production `src/**`変更
- small limit overrideによる64 KiB／16 MiB境界の代用
- private response、raw stderr、source proof、host stateの公開

次を検出したimplementerは変更を継続せず、parentへstop-and-returnしなければならない。

- adopted authorityとの矛盾
- canonical decisionの欠落
- unexpected public API／data／security／migration／compatibility impact
- rollback／recovery／operational guaranteeの追加必要性
- lower-layer contract変更の必要性
- verified path／symbol／owner assumptionの反証
- paired-nullでは表現できない合法state
-新しいwire versionまたはdual pathの必要性

将来のimplementerが返すevidence packetには、少なくともexact base/head SHA、changed paths、Red/Green command、original terminal result、focused/aggregate counts、schema vector、consumer census、negative assertions、artifact/log digest、known unavailable environment、deviation、fresh review destinationを含める。実装者自身はclosureを宣言しない。

# Verification plan

## Supplied results

| Evidence | SHA binding | Status and limit |
|---|---|---|
| GitHub repository／branch／tip | `af6f5d33f9487a33dabf2ddfe41df85b3d8267fb` | exact match |
| Current R/D/P、schema、reference、test inspection | `af6f...` | 実施済み |
| stage_failed/schema-fragment probe | `af6f...` | terminal 0、F1/F2の限定確認 |
| SI-05 contracts/full/statics review evidence | `6d52ff7949d64e747235eef870631cd8cc29b273` | SI-05の範囲のみ |
| `af6f...` SI-06 focused tests | なし | 未実施 |
| `af6f...` SI-06 aggregate tests | なし | 未実施 |
| SI-06 runtime／integration／consumer certificate | なし | 未実施 |
| SI-06 Code Review Strict | なし | 未実施 |

supplied probeは、paired nullの実在とschema rejection、`payload_unavailable` branchでのnon-null response rejectionを証明する。しかし、planned final ownerの全behaviorやnormal validated unavailableのlive conformanceを証明しない。attachments-bundle

## Future SHA discipline

以下で、`S_spec`を採択済みspec/schema candidateのfull SHA、`S_impl`をclean pushed final SI-06 implementation candidateのfull SHAとする。

- Spec Review結果は`S_spec`へbindする。
- focused、aggregate、runtime、integration、consumer resultはすべて同一`S_impl`へbindする。
- fresh Code Review Strictはbase `af6f...`からhead `S_impl`の全rangeへbindする。
- `6d52...`または`af6f...`の旧resultを`S_impl`のpassへ流用しない。
- branch tipが変わった場合は、保持したrepository factsを使用する前に再検証する。

## First Red / focused falsification

### RC-01 Red

adopted contractに応じて、最初に次をRedとして固定する。

1. actual existing `stage_failed` ownerからrun-v3、candidates-v3を作る。
2. captureがpaired nullであることを確認する。
3. current final publication schema／planned final ownerがpaired nullを表現できず失敗することを記録する。
4. fixture construction error、import error、collection errorをRedに数えない。

### RC-01 minimum Green

- final adapter measurementsがpaired nullを保持する。
- public stderrとselected stdoutはactual measurement objectである。
- stage_failed publicationがschema-validになる。
- response null、artifacts empty、exit 3になる。
- final boundaries成功時のpublication outcomeは`published`になる。
- zero-fill、one-sided null、foreign ownerを拒否する。

### Observed-zero control

別testで実capture objectの0 bytesを作り、

- adapter measurementsはnullではなくobject
- `measured_bytes=0`
- `retained_bytes=0`
- byte cap内なら`allowed=true`

であることを確認する。paired nullと同じserialized valueになってはならない。

## Response/outcome matrix

同一`S_impl`で次を独立に検証する。

| Case | Required assertions |
|---|---|
| SOURCE-003 validated Core | `published`, exit 3, response non-null, artifacts empty |
| TARGET-001 validated Core | `published`, exit 3, response non-null、target typed unavailable |
| EXPORT-001 validated Core | `published`, exit 3, response non-null |
| entity LIMIT-005 validated Core | `published`, exit 3, response non-null、actual entity measurement保持 |
| model-record LIMIT-005 rejected Core | response null、model digest非昇格 |
| protocol/rejected Core | response null |
| runtime-only with observed capture | response null、existing stage/code保持 |
| stage_failed paired null | response null、no zero fill |
| adapter capture overflow | `payload_unavailable`, response null, artifacts empty |
| selected-copy +1 | `selected_artifact_unavailable`, validated response保持、artifact descriptor不変 |
| selected failure + stderr overflow | `payload_unavailable`, response null、stderr empty |
| public stderr 65,536 | whole emission |
| public stderr 65,537 | empty stderr、partial 0、replacement LIMIT-003一件 |

## Pre-copy and final-byte checkpoints

validatorはproducer helperをexpected oracleとして使わず、次を独立再導出する。

- selectorからpre-copy candidate identityを特定
- pre-copy byte length/hash
- configured selected limit
- selected `allowed`
- retained byte length
- final typed unavailable bytes
- failure manifest/root status
- final stderr bytes
- publication outcome
- response eligibility
- final seal

selected-copy failureでは、pre-copy candidate hashとfinal stdout hashが異なることを許す一方、どちらを何のdigestとしてsealしたかを明確にする。final failure bytesを再measureして元selected measurementへ上書きしてはならない。

## Schema and consumer verification

in-place v2案では次を確認する。

- old object/object vectorsは引き続きvalid
- paired null/null vectorはvalid
- null/objectとobject/nullはinvalid
- nullをzero objectへ置換したrehashed recordはindependent validatorでinvalid
- public_stderr／selected_stdout nullはinvalid
- bool／float countsはinvalid
- all exact refs resolve
- current outer consumer projectionsがpaired nullを処理する
-旧consumer compatibilityの扱いが採択済みdecisionと一致する

successor案では、上記に加えて次を確認する。

- old v2 schemaとfixturesはbyte/meaning不変
- successor URNとversionが一意
- outer exact refsが混在しない
- dual write/readを暗黙に追加しない
- migration／rollback testが採択済みdecisionと一致する

## Aggregate regression obligations

`S_impl`で、briefが指定する少なくとも次のlaneを実行する。

- public diagnostic focused tests
- final publication focused tests
- actual 65,536／65,537 stderr tests
- actual 16 MiB／16 MiB+1 selected-copy tests
- SI-03 source inventory regression
- SI-04 Core regression
- SI-05 public/run/candidates/schema regression
- lower runtime／response receipt regression
- legacy wire-independent publication regression
- Python／SQLAlchemy golden regression
- `pytest tests/contracts`
- full `pytest`
- Ruff check
- Ruff format check
- mypy
- SpecDock sync／validate
- `git diff --check`
- exact changed-path guard

large boundary testsをmark、deselect、skipしてGreen扱いしない。

## Negative assertions

明示的に、次が起きていないことを検査する。

- 0埋め
- branch exclusion
- observed failureのstage/code relabel
- target failureの他branchへの流用
- legacy owner cast
- new free status/count/hash/outcome input
- re-capture
- re-render／re-measure／re-copy
- schema-wide relaxation
- unvalidated model digest publication
- raw child stderr／source body／private proof／host path leakage
- optional publication backrefの新fixed-point rule
- reader-prefix／ASSET policy混入
- production／dependency変更

## Rollback verification

in-place案では、旧object-only recordが訂正後schemaでもvalidであり、paired-null producerだけを旧schemaへ戻したmixed stateが検出・拒否されることを確認する。

successor案では、v2 consumerへsuccessor recordが誤って流れないこと、successor exact refsを戻せばv2 fixtureへ一貫して復帰できることを確認する。

## Review verification

local evidenceがすべて同一`S_impl`へbindし、clean non-force push後にのみ、fresh independent Code Review Strictを実施する。

- review base: `af6f5d33f9487a33dabf2ddfe41df85b3d8267fb`
- review head: `S_impl`
- required result: `review_status=pass`, `P0=0`, `P1=0`
- author、analyst、advisory primary observationはそのreviewを代替しない
- P2/P3はparent policyどおりreport-only

# Same-reviewer re-review obligations

current sourceはformal Code Review Strict reviewerではなく、primary admission observerである。したがって、same-reviewer再確認はadmission observationのclosure確認には使えるが、SI-06のformal passやunit closureを発行できない。

| Source / group | Original observerが再確認する内容 | Expected disposition |
|---|---|---|
| `SI06-BA-F1` / `RC-01` | adopted contractがpaired-nullを表現し、stage_failedを除外せず、zero-fillせず、one-sided nullを拒否すること | 現在は`still-open`。in-place訂正ならexpected closure、successor contractならapproved contract changeによるsupersession |
| `CG-01` / `RC-01` | version、consumer compatibility、rollback、SI-05 certificate supersessionがcanonical decisionへ記録されたこと | human decisionまでは`still-open` |
| `SI06-BA-F2` / `RC-02` | briefがsemantic outcomeとpublication outcomeを分離し、validated unavailableを`published`／exit3／response保持へmappingすること | unconditional contradiction部分は`disproved`、brief ambiguityはwording訂正後にexpected closure |
| `OBS-01` | empty SHA proseをoracleに使わないこと | non-blocking、再発行時のみtext correction |
| optional backrefs observation | live recursive populationを新要件にしていないこと | findingなしのまま維持 |

## Completion sweep for adjacent paths

original observerは、同じroot causeが隣接pathへ残っていないことを少なくとも次で確認する。

- `stage_failed`／`spawn_failed`
- observed zero capture
- stdout capture overflow
- stderr capture overflow
- timeout
- write failure
- read failure
- protocol／bootstrap／semantic child failure
- SOURCE-003
- TARGET-001
- EXPORT-001
- entity LIMIT-005
- model-record rejection
- selected-copy exact／+1
- selected-copy failure後のdiagnostic stderr exact／+1
- selector null／manifest／semantic-json／plantuml
- response non-null／null branch
- paired-null schema vectors
- foreign equal-content／rehashed-cache substitution

same primary observerの確認後も、parent workflowは別のfresh independent Code Review Strictを必要とする。current policyはSI-06 review attemptごとにfresh reviewを要求し、author-session reviewやreview follow-upで代用しない。

# Parent workflow consequence

parent-owned next consequenceは、**SI-06 implementation開始ではなく、RC-01 public-contract decisionの取得**である。

順序は次でなければならない。

1. F1 decision packageをhuman ownerへ提示する。
2. in-place v2訂正またはsuccessor versionを採択する。
3. compatibility、consumer、rollback、SI-05 supersessionを決定する。
4. canonical R/D/P／contractへ反映する。
5. Spec Review Strictを実行し、採択済みmeaningを再認証する。
6. exact SHAをGitHub connectorで再検証する。
7. F1/F2を反映したSI-06 briefを採択する。
8. bounded implementation handoffを発行する。
9. focused Red→Green、aggregate、runtime、consumer evidenceを同一candidateで取得する。
10. task-scoped commit、normal non-force pushを行う。
11. base `af6f...`からfinal candidateまでfresh independent Code Review Strictを実施する。
12. pass／P0=P1=0後にだけSI-06 closureをparentが判断する。

現時点でblockされるものは次である。

- SI-06 final-owner implementation admission
- SI-06 unit closure
- SI-07 reader-prefix／全A02
- A03 cumulative review
- production TypeScript／OS／CLI
- package／offline／license
- Final／Issue #8 acceptance

F2のdocumentation correctionだけを先行準備することはできるが、それによってF1 blockerは解除されない。

人間がin-place訂正を採択した場合でも、旧SI-05 reviewを自動的に有効なままとみなさない。public schema meaningを変更するため、fresh spec/schema checksと、その後のSI-06 cumulative code reviewが必要である。

successor version、新consumer migration、またはscope拡大が採択された場合、parentは既存SI-06 campaignを継続できるか、新scope identity／fresh campaignが必要かを決定する。analystはそのworkflow transitionを所有しない。

このskill外のactionsは、編集、test実行、Git操作、Issue変更、review submission、same-reviewer連絡、workflow transition、認定、merge、closureである。自動再提出や認証設定変更は行わない。

# Assumptions and unresolved evidence

1. GitHub bindingは本応答時に取得したbranch tip `af6f5d33f9487a33dabf2ddfe41df85b3d8267fb`に限る。branch tipが変われば、本packetのrepository factを再利用する前に再検証が必要である。
2. Workbench packet、raw brief、probe logはsupplied evidenceであり、verified commit内のcanonical authorityではない。
3. packetが報告するlocal clean worktreeはGitHub connectorでは独立検証していない。
4. `af6f...`にSI-06実装、focused test、aggregate test、runtime/integration certificate、formal Code Review Strictは存在しない。
5. SI-05 broad test結果は`6d52...`へbindしており、`af6f...`のdocs-only natureはrepository diffで確認したが、その結果を`af6f...`のSI-06 passへ拡張しない。
6. public contract versionをin-place訂正できるというimmutability policy、external consumer不存在、release済みrecord不存在は立証されていない。これが`CG-01`のhuman decisionを必要とする主要因である。
7. in-place訂正を推奨する条件は、production／external consumerが未存在、または同時更新可能であることがparentにより確認される場合に限る。
8. successor versionを選択する場合のexact version number、URN、outer schema migration、dual-read/write policyは未決定であり、本分析はそれらを発明していない。
9. normal validated semantic unavailableを`published`へmappingする結論は、Current Designが維持authorityに指定するexisting baseline finalizerとcurrent schemaからの推論である。SI-06 V3 final ownerの実行結果ではない。
10. `ValidatedSemanticDecisionV3`からresponse linkを構成するexact implementationは未作成であり、同一transport candidateからの独立再導出をfuture testで証明する必要がある。
11. request-bound stage_failedのreference/test到達性は確認したが、actual macOS/Linux Node spawn failure integration evidenceは未取得である。
12. primary admission observerはformal Oracle reviewerではなく、thinking levelは不明である。source authorのrequested model／effort provenanceをprimary reviewerのprovenanceへ転用していない。
13. analyst requested modelのbackend identityは外部attestationされていない。
14. current authorityが将来、missing captureをzero observationと定義する、stage_failedをSI-06 final owner外へ移す、またはsemantic unavailableをpublication `payload_unavailable`へ統合するよう正式変更された場合、本dispositionは無効になる。ただし、現在確認したauthorityはそのいずれも支持していない。
15. optional publication backrefsの省略が将来mandatoryになる場合は、self-reference／hash／copy contractの別decisionが必要であり、今回のRC-01/F2 patchへ混ぜられない。
16. no persistent user-data migrationは現packetから確認できる範囲の見立てであり、external stored publication recordsの有無は未検証である。
