# Next.js private exchange v2

## 全chainのdata-only入口

`retain_transport_candidate_v2(source_seal, retained_assets, request_frame, policy, observation, response_frame)`がreferenceの通常入口です。`validate_transport_exchange_v2`は同じchainを独立に検証します。単体のschema pass、metadata-only binding、`transport_payload_admissible=true`だけではcandidateを生成しません。

| seam | 必須join |
| --- | --- |
| `validate_launch_policy_request_v2` | actual source/request/asset owner、policyのrequest ID・runtime requirement・seal-owned limits、保持adapter/trusted profile |
| `validate_observation_request_v2` | policy/observation self join、prepared canonical stdin bytes長。captureのsent量はencoded量以下、正常終了は全量sentという既存data gateを合わせて検証 |
| `validate_response_request_v2` | nominal retained response owner、request-owned limitsでのbounded decode、adapter version、bound request ID、success payloadのtrusted digest/limits/context exact echo |
| `validate_response_frame_observation_v2` | raw bytesのSHA・control・observed stdout全量。再serialize hashや独立counterへの置換は不可 |
| `validate_transport_exchange_v2` | 上記全joinとnormal success/supported same-child control/exit/full capture/cleanup/drift gateのAND |

responseのunbound protocol failureはrequest IDをechoしません。その他のclosed child failureにもmodel/proofを作らず、request/response echo validatorはnull payloadをnullのまま扱います。正常captureでchild failureが届いてもsemantic candidateはありません。既観測control/version/hash prefixは保存可能ですが、late drift/cleanup failureの後にcandidateをmintしたりtarget-completenessを補完したりしません。

## Opaque transport owner

`ValidatedTransportCandidateV2`はtyped request/response frameとportable runtime bindingのimmutable snapshotを保持します。通常constructorは閉じ、whole-exchange factoryだけで作ります。request ID、保持frame、fresh binding/payload projectionを提供し、raw/source bytesをreprへ出しません。外部policy/observationやprojectionの後続変更を保持identityへ反映しません。

名前の`Validated`は**data joinsの検証**を指します。Coreのmodel digest・project/file correspondence・ID/reference/proof/target検証、entity gate、semantic/publication decisionを意味しません。reference pid/version/測定量はsynthetic inputです。実OS/TSが実行された証拠、hard RSS、same-UID confinement、actual-image attestationではありません。TS/installed bundle acceptanceは別gateです。

v1 bindingのmetadata projection helperは純粋な計算として残しますが、compatibility v2の通常生成入口はそれをcallerが任意に渡せるAPIにしません。whole exchangeを閉じたownerが必要です。

## Known identity / negative vectors

header-only adapter＋locked 4 declarationsのsynthetic asset集合は`asset_set_id=50923cb225647685051b2f46f14fe8fc4adc02b168906595e7ed5a518cd479a7`。candidate hash=`2`×64、control Node 22.10.0、fixed TS identity、trusted v2 profileで、portable runtime binding fingerprintは`2654b8357780949c2f53254993c9bcbfd911c2222d3a69b6d1a6e4028330b888`です。literal content/member/binding preimagesをjq/shasumで独立計算しました。compilerの無いfixtureを実製品bundleに読み替えません。

private wire testsは、単体data gateがtrueでもstdin/stdout counts、echo、保持ownerに不一致があれば拒否することを示します。closed protocol/unsupported/bootstrap/semantic failure、late candidate/assets drift、cleanup未確認もcandidateを生成しません。echo-only positive fixtureのmodel hashは意図的に`0`×64で、Core acceptanceには使えません。
