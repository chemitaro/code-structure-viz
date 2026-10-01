# Next.js request-bound run decision v2

## 対象と境界

`schemas/next-run-decision-v2.schema.json`は、validated requestを保持する親の結果を表すclosed reference recordです。`schema=code-structure-viz.next-run-decision/v2`、`version=2`、`request_independent=false`に固定し、request-bound success/failureだけを扱います。旧run/provenance/process全objectへのfallbackはありません。

これはA02のdata-only契約です。`exit_code`は保持outcomeの投影で、実CLI終了やpublication後の最終exitではありません。recordのpassだけでは実Node/TypeScript、OSの時系列、package同梱、filesystem publication、selected stdout、Issue全体を認定しません。request-independent reader prefix、新ASSET failure policy、publication/domain/root/stdout全chainは別の未完了gateです。

## 同じownerからの生成

`retain_request_bound_run_decision_v2(runtime_result, *, semantic_decision=None)`は、exact `RetainedRuntimeResultV2`とnullable matching Core ownerだけを受けます。status/outcome/exit、hash、descriptor、prefix、measurementの自由入力はありません。

- transport successには、同じcandidate/source/assetsの`ValidatedSemanticDecisionV2`または`RejectedSemanticDecisionV2`が必須です。同じcontent/request IDでも別exchangeのCoreを結合しません。
- child/transport failureにはCore ownerを付けません。transportの観測済みcontrol/versionを、semantic acceptanceやsuccess-only bindingに昇格しません。
- interruptはCore terminal routeです。この通常run factoryでは拒否し、普通のfailure recordを生成しません。
- 無関係のowner/internal errorをcatchして通常failureへ変換しません。直接constructor/duck ownerもauthorityになりません。

nominal `RetainedRequestBoundRunDecisionV2`はruntime/Core参照とcanonical record bytesをimmutableに保持します。`runtime_result()`、`semantic_decision()`は同じownerを返し、`record()`と`project_request_bound_run_decision_v2(owner)`はfresh objectを返します。reprにpayloadを出しません。これは通常APIの保持・照合境界であり、反射的な全field書換えを行うhostile same-UIDへの保証ではありません。

## 五つの排他的branch

| 保持evidence | kind / status / outcome | payload / exit | fingerprint / compatibility |
| --- | --- | --- | --- |
| validated Core complete | success / complete / complete | true / 0 | 両方非null |
| proof-backed Core partial-safe | success / incomplete / partial_safe | true / 3 | 両方非null |
| validated Core target/export/entity unavailable | failure / incomplete / payload_unavailable | false / 3 | 両方非null |
| typed Core invariant/record-limit rejection | failure / incomplete / payload_unavailable | false / 3 | fingerprint非null、compatibility null |
| closed child/transport failure | failure / incomplete / payload_unavailable | false / 3 | 両方null |

表のkindは`request_bound_`接頭辞を省略しています。schemaは五つの`oneOf`を持ち、対応stage/codeをexact provenance-v2へjoinします。将来のrequest-independent/not-applicable、usage、fatal、interruptedのshapeを先行追加しません。

complete/partial-safeは全17 observationsとresponseが必要です。validated Core unavailableはTARGET/EXPORT/entity LIMITの既存対応だけで、typed rejectionではsemantic/compatibility/model/budgetの四suffixをunobservedに保ちます。runtime failureも同じ四suffixを生成しません。既存codeは`CSV-NEXT-`付きで、stage/codeの写像は[provenance-v2](next-provenance-v2.md)を維持します。

## Contextとdescriptor

contextの九fieldは、同じ親request/context/sourceから導出します。

`request_id`、`run_fingerprint`、`run_context`、`analysis_intent`、`domain_config_digest`、`source_plan_digest`、`source_view_fingerprint`、`compatibility_id`、`observed_prefix`。

run contextのformats/selector/budget、intentのtargets/depthを補完・coerceしません。config digestは自身のdigest fieldだけを除いて再計算します。source plan/view identitiesは同じsealから照合します。`observed_prefix`は`provenance.observed`のexact aliasで、別のauthorityではありません。

request descriptorは元`canonical_bytes`のrequest ID、実SHA/len、`canonical_json=true`だけです。response descriptorはlive検証済みreceiptの三field（SHA/len/canonical flag）だけ、receipt無しならnullです。flagはbooleanで、元frameに空白/LFがあればfalseも認めます。decoder rejectionのprivate raw hash/lengthからcomplete-response descriptorを捏造しません。

response nullならnode-version/control-response observationsはunobservedです。非nullでも、protocol/bootstrap controlのruntimeはnullになり得ます。stage名だけではresponse/prefixのnullabilityを決めません。

transport failureでは、live byte検証後のdescriptor-only receiptとclosed metadataだけを照合し、破棄済みbodyのSHA/len/echoを再計算しません。transport成功後のCore unavailable/rejectedは別経路で、既存candidateを使った再検証を維持します。新run ownerにfailure body再読経路を追加しません。capture計測、返却ownerの非保持、物理heap zeroizationも混同しません。

## Core measurement

`core_measurement`は次のclosed三field objectかnullです。

| kind | actual | limit |
| --- | --- | --- |
| `entity_budget` | validated Core gateの実entity count | 同じrequestの`max_entities` / held `budget_resolved` |
| `model_record_limit` | typed rejectionの実model-record count | 同じrequestの`max_model_records` |

target/export unavailable、Core invariant rejection、runtime failureではnullです。実record 10001/limit 10000をentity countに置き換えません。complete-emptyもgateの実測0だけを用い、Component数0からModule＋Componentのentity countを推測しません。数値はbool/floatではない整数として照合し、byte lengthやintent/budgetも保持入力の整数表現を維持します。

## Fingerprintとprovenanceの独立検証

fingerprintは[semantic-v2の13-key family](next-semantic-v2.md)だけです。matching admitted transport candidateとCore ownerがある場合だけ非nullにし、Core rejectionでも同じtransport familyを使います。child/transport failureは、control.versionが見えていてもnullです。failure専用hash、fake binding、process/PID/path/capture fieldsを追加しません。TypeScript 5.9.2はlocked expected metadataであり、実import/useの観測ではありません。

`validate_request_bound_run_decision_v2(value, owner)`は、新run producer/projectionや共有expected-record builderを呼びません。cache一致は保持recordへのjoinにすぎず、その後にruntime/Core exact typeとsame-object joins、outcome、provenanceの17 states/hash、context、13-key fingerprint、compatibility、実request bytes、response receipt、Core measurementを別経路で照合します。producerと同じ誤ったrecordをcacheへ入れても、owner由来の値との不一致を拒否します。

`validate_runtime_provenance_v2`もproducerの`runtime_provenance_values_v2`、`runtime_provenance_v2`、`portable_launch_value_v2`を呼ばず、validator-localに17 valuesとportable policy/spawn projectionを再導出します。canonical codec/SHA、offline schema loader、変えないsource/semantic algorithms、下位owner validatorsの共有は維持します。この限定変更を全製品の独立性認定とは表現しません。

root/nested新objectsはclosed、provenance/observed-prefixはv2 exact refsです。run-context-v1、config-v1 target item、execution-assets-v1 digestは意味を変えないleafとしてだけ再利用します。

## 独立literal vectors

三つのASCII literalは固定corpusとtest-side worked expectationから作り、新run/provenance producerから生成していません。`independent_ascii_run_literal`は元owner inputsから17-slot値を明示してstd JSON/SHAで計算します。初回固定後は自動更新で生成処理へ追従させません。

| fixture | canonical JSON bytes（LF無し） | SHA-256（LF無し） |
| --- | ---: | --- |
| `run-decision-complete.json` | 7763 | `673215084459eee6f9bb8bad68d450af15bd3b3f0ec83cdaea2f14142a4418f1` |
| `run-decision-pre-spawn-failure.json` | 5671 | `b075ae42f25d307d3a7aa3adffcaecc5af7634a90650bc806a526ecc177abfbf` |
| `run-decision-core-rejected.json` | 6644 | `bae073c0520dbe79823dda41d583626d773071a1dcfe58857b6ed7138af16e6c` |

fixturesは`tests/fixtures/next_runtime_v2/`の一行JSON＋LF一つです。`jq -cjS . <file> | shasum -a 256`の独立計算で上のLF無しhashを確認します。fileそのもののhashは順に`1371006299668af69f7a04bc0d179ed162f9089a00a2f4dbd640847cbd1bf24f`、`05e6d22d9565a57a938ecff753ddeab71cc3a5bd19eb368f5b8f4216be151017`、`ee65f475d92172ddc2b0f8dbf2e3f88182bf897ae7420e13ab67da2adcd17622`です。これはreference recordのKATで、persisted Artifactやpublication sealではありません。

既知13-key fingerprint、process-start/candidate observations、retained public semantic bytesの9472 bytes/SHAは不変です。run responseのraw bytes（known completeでは6320）はpublic semantic bytes（9472）ではありません。request3961 bytesの既存corpusとCard request3902 bytesも別corpusで、混同しません。
