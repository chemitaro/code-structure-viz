# Next.js private response v2

## 単一frameと所有権

wireはUTF-8の単一JSON objectです。rootは`schema=code-structure-viz.next-adapter-response/v2`、`control`、`semantic_payload`だけです。protocol、compiled adapter version、request binding、同一processのNode version、closed result kindは[control契約](next-process-observation-v2.md)へ統一し、banner・別probe・第2のJSONを許可しません。

`success`だけが非nullのsemantic payloadを必要とします。他の4 result kindはnullです。childはruntime binding/compatibilityやpresemantic target-completenessをrootへ追加しません。unsupportedはTS import前、bootstrap/protocol/controlled catastrophic semantic failureはmodel/proof生成前の結果です。partial-safe/target failureはtransport successのpayloadをCoreが判定します。

payloadは固定TS/trusted identity、identity versions、limits、run context、model、proof、model digestを持ちます。既存v1の**要素/model/proofのdefsだけ**を参照し、旧response envelopeや旧runtime compatibilityをadmitしません。document/wire版が2でもsemantic ID/props algorithmは1のままです。

## Bytesからの入口

referenceの`retain_response_frame_v2(raw, limits=...)`が唯一の通常生成入口です。immutable bytesだけを受け、bounded JSON→closed frame schema→control整合を検証して`RetainedResponseFrameV2`へ保持します。public constructor、mutable input、callerのhash/control metadataによる置換は許可しません。readonly bytes/hashとfresh control/payload projectionを提供し、raw bytesをreprへ出しません。

保持するidentityは受信した**元bytes全体**のSHA-256です。再serializeしたJSONのhashではありません。末尾LF/許容JSON whitespaceもraw measurement/hashに含めます。BOM/banner/複数JSON/partial JSON、duplicate keys、既存nesting/string/array/total-array capを拒否します。16 MiB raw response capはJSON decode/materializationより先に測り、whitespace paddingもexact受理/+1拒否です。

bounded JSONは変更しない既存のwire非依存`bounded_decode_json`を再利用しています。旧runtime validator・record・coverage certificateは使用しません。このreference helper依存とpayload defs参照を明示し、旧v1 runtimeのpassをv2受入れとして数えません。

## 観測へのjoinと残るgate

`validate_response_frame_observation_v2`はtyped retained frameを受け、policy/data observation検証とbounded frame再検証後、response SHA・control projection・stdout observed bytesを同じ保持bytesへ全量joinします。SHAだけが正しくても別versionのcontrolや偽capture countを拒否します。caller metadataのduck objectをtyped ownerの代用にしません。

これはrequest/semantic/OS admissionのcertificateではありません。success candidateのshapeがvalidでもmodel digest/proof/source/target対応が成立するとは限りません。opaque validated request、stdin/request ID/limits/context/trusted identity、Coreの独立model/proof/hash検証、compatibility/public closureが後続A02-2/3の必須gateです。reference Schema/ValueErrorをproductionのpublic診断へ直接出さず、catalog-owned failureへ分類します。

terminal failureではparentが既検証control/hash prefixだけを保存し、raw stdout/stderr・retained semantic frameを採用/公開しません。後続cleanup failureでversionを補完も消去もしません。このsliceはbyte/dataの検証であり、actual capture/cleanupとresource postconditionはA04の実OS owner受入れで証明します。

## Known byte vector

`test_next_response_frame_v2.py::failure_frame`はunsupported Node 20.19.5、bound request、null payload、末尾LFのsynthetic closed responseです。full bytesのSHA-256は`f0bbb753ad4ae8fa9304279c4075b2388e1b01a11d92d1ae457e23f76551b6ce`。これは実Nodeの応答ではありません。
