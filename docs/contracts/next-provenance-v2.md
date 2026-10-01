# Next.js owner-derived provenance v2

## 境界と現在の実装範囲

`code-structure-viz.next-provenance/v2`は旧v1へfieldsを足した互換viewではありません。17 named observations、same-process control、readonly expected resources、Core admissionを別に扱います。旧12 slots/observation-v1は履歴・回帰のまま保持します。

現在のreference laneは、actual `SourceAcquisitionSeal`から作ったrequestとretained assets、policy、process observation、complete frameをjoinする`RetainedRuntimeResultV2`を入力にします。これは**referenceデータの保持・検証owner**であり、OS spawnやTypeScript実行の証明ではありません。実OS ownerはA04の受入れで実装・検証します。

schemaは四つのkindを区別します。runtime reference producer/validatorで検証済みなのはrequest-boundの正常child/control、timeout、late cleanup/driftとmatching Core ownerです。request-independent reader phase/source failure、その他transport failure、invalid Core/record-limit failure、run/publication/public exact refsは後続A02 gateです。shapeにbranchがあることを、未実装branchの認定にしません。

## Runtime結果の保持

- 成功時はwhole-exchange `ValidatedTransportCandidateV2`だけを保持します。transport successをsemantic completeへ昇格させません。
- child failureは`protocol_failure`/`unsupported_runtime`/`bootstrap_failure`/`semantic_failure`のclosed controlと元frameのdescriptorを保持し、semantic candidateはnullです。
- transport failureでcomplete frameを既検証ならcontrol/version prefixを保持できます。ただしraw failure stdout/stderr buffersとsemantic candidateを保持しません。partial/unobserved frameからcontrolを補完せず、観測にないframeを付けません。
- foreign child request bindingはそのままfailure evidenceへ保持し、親request IDへ修正しません。`binding_mismatch`というlabelだけでは足りず、元frameの実foreign bindingを必要とします。
- descriptorは`raw_sha256`、`byte_length`、`canonical_json`だけです。SHA/lengthは元bytes、flagはpinned canonical JSON bytesと元bytesの全量一致です。whitespace/LFを許可したframeでflagがfalseでも、別digestにreserializeしません。
- 直接constructor、duck owner、free capture/control/hash、mutable input aliasesはauthorityになりません。取得したprojectionはfresh copyです。private constructor helperはtrusted Python内部用であり、hostile same-UIDへのsecurity boundaryではありません。

## Observationのpreimage

観測済みrowは`state=observed`とdescriptor、未観測rowは`state=unobserved,value=null`です。観測済みdescriptorは次です。

```json
{"schema":"code-structure-viz.next-observation/v2","version":2,"sha256":"<64 lowercase hex>"}
```

digestは次の**全preimage**から生成します。`CJ15`は既存pinned Unicode 15.0.0 NFC・key-sort・compact UTF-8・LF無しcodecです。

```text
SHA256(CJ15({
  schema: "code-structure-viz.next-observation/v2",
  version: 2,
  field: <closed slot name>,
  value: <actual retained value / specified portable projection>
}))
```

rowはnamed observation-valueのdescriptorであり、portable projectionを元policy/observation schemaの完全objectとして偽装しません。field名だけのmarker、failure stageから推測した値、空success/default modelをhashしません。値本文は公開せず、source/partial stdout/stderr/private proofも公開しません。

| slot | 同じownerから取得する実値 | 観測無し |
| --- | --- | --- |
| applicability | matrixのpackage bytes identityを含むobservation value | reader-owned permission前 |
| config | seal-owned resolved project/config rows | resolution前の詳細は後続reader-prefix契約 |
| source | sealed SourceView fingerprint value | seal前は後続reader-prefix契約 |
| limits / source_plan | 同じsealのlimits / final plan | 未導出を生成しない |
| trusted_environment | retained declarationsから導出した**readonly expected** descriptor v2 | expected owner未取得。TS import/useの観測ではない |
| runtime_bundle | 同じretained asset descriptor | 未保持 |
| node_candidate | 親が候補として測ったcontent SHAだけ | 候補未計測 |
| request | 同じparent-generated request record v2 | validated request無し |
| launch_policy | 下記portable projection | policy無し |
| process_start | 実spawn primitiveと実parametersのportable projection | spawn無し |
| node_version | complete joined controlのruntime observation | control/runtime未観測 |
| control_response | complete joined control＋元response descriptor | complete frame未検証 |
| semantic_payload | matching Core ownerが検証したprivate payload（hashのみ公開） | Core未認定 |
| compatibility | 同じCore/transport ownerのparent compatibility v2 | Core未認定 |
| model | 同じCore ownerのmodel（hashのみ公開） | Core未認定 |
| budget | 同じCore gateの実measurement | target/export failure等でactual=null |

slotsの表示順は実時系列の代用ではありません。例えばbootstrap/protocol failureにcontrolがあってruntimeがnullなら、`node_version=unobserved`・`control_response=observed`です。stageだけで固定長prefixを再構築しません。

`request_bound`は**親がvalidated requestを持つ**意味で、childがそのrequestをbindしたという保証ではありません。child bindingはcontrolで別に検証します。presemantic failureにはtarget-resolution proof/completeness rowsを生成しません。

## Portableとhost-local

policy全object、concrete path/argv、platform、policy digest、PID/PGID、cleanup detailsはhost-local private ownerに保持します。それらをpublic observation preimageへ流しません。候補content hashはactual-image attestationではありません。

launch-policy valueはproducer、candidate content SHA、runtime requirement、asset ID、adapter logical identity、expected TS/trusted identity、shell/env/stdio/FD/group/limitsを保持します。argv executableは`{kind:node_candidate,sha256}`、entrypointは`{kind:execution_member,package_path}`、cwdは`{kind:empty_private_directory}`へ置換します。absolute/private paths、platform、request ID、local policy digestを除きます。

process-start valueはspawn primitiveと、実spawn parametersの同じlogical projectionだけです。expected TS/trusted metadataをPopenへ渡したparametersと呼びません。PID/PGIDは含めません。これはprovenanceの値であり、semantic compatibility/runtime bindingのfingerprintとは別です。

独立ASCII KAT（fixed candidate SHA=`2`×64、checked-in policy）:

- `node_candidate`: `49629589791b75238da6a7744ddb40b19386eb9482a8e05a90a2bf2717870def`
- `process_start`: `3869aabc86551c31c55fca1229360dc3efe591ab6449bb33dc465a3b8bf6b5d4`

同じcandidate/assets/request/frameでhost paths/PIDだけ変えるとhost-local policy digestは変わり、public provenanceは変わりません。Node binary内容/versionの違いをOS間で一致させる保証ではありません。

## Outcomeと検証

| 実result / Core gate | kind / stage / catalog code |
| --- | --- |
| unsupported runtime | bound failure / runtime_validation / NODE-001 |
| protocol failure | bound failure / response_protocol / PROTOCOL-001 |
| bootstrap failure | bound failure / bootstrap / NODE-004 |
| catastrophic semantic failure | bound failure / semantic_analysis / NODE-004 |
| timeout | bound failure / node_timeout / NODE-003 |
| late cleanup/candidate/assets drift | bound failure / node_process / NODE-004 |
| Core target/export/entity unavailable | bound failure / target_resolution・response_validation・model_validation / TARGET-001・EXPORT-001・LIMIT-005 |
| matching Core complete/partial_safe | bound success / null / null |

codeは表中の短縮名に`CSV-NEXT-`を付けます。新stageはv2の閉じた対応であり、旧v1 matrix/schemaを変更しません。failureはobserved prefixを保持し、未観測suffixをsuccess defaultで埋めません。target/export gateのentity actualがnullならbudget rowもnullです。

`runtime_provenance_v2`はmatching opaque runtime/Core ownersから生成します。`validate_runtime_provenance_v2`はclosed schema、kind/stage/code、17 states/digestsを同じretained valuesから再検証します。別exchangeのCore owner、free status、schema-valid rehashed row、v1 identity/slotsを拒否します。known corpusによるCore reference evidenceを、任意sourceの実TS意味認定やA03/Issue全体のpassへ読み替えません。
