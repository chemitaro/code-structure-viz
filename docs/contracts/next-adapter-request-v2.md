# Next.js private request v2

## Intentと保持されたowner

rootは`schema=code-structure-viz.next-adapter-request/v2`、`protocol=code-structure-viz.next-adapter/v2`のclosed objectです。runtime requirementはstable Node major≥22という**期待条件**で、実Node version、candidate path/hash、runtime binding、compatibilityを持ちません。実versionは同じchild processのresponse controlで初めて観測します。

referenceの`build_request_frame_v2(source_seal, retained_assets, targets=..., run_context=...)`が通常生成入口です。実`SourceAcquisitionSeal`と同じimmutable execution asset ownerを要求します。trusted descriptor v2は保持宣言のreadonly metadataから導出し、sealのopaque digestとjoinします。adapter versionも同じ保持entrypointのheaderから導出し、callerのfree identityを受け取りません。このmetadataはchildのTS利用・起動成功を証明しません。

projects/filesはsealのfinal plan、applicable project集合、凍結済みSourceViewから導出します。target repositoryやinstalled packageを再readしません。非applicable projectを除き、project root/config/options、file membership/role/base64 bytes/size/hashを独立validatorでsealへjoinします。roles、entity ID、project config digest、path/targetのcanonical orderとNFCは維持するsemantic/source algorithm v1です。

targets/run contextはanalysis intentです。builderは入力順を黙って並べ替えず、canonical orderを要求します。resolved budgetはseal-owned `limits.max_entities`と等しい値でなければ拒否します。validatorはschema shapeだけでなく、run-context/source/entity invariantを検証します。

## Canonical bytesとdigest

`request_id`はself fieldだけを除く**新request全体**のdigestです。unchanged Unicode 15.0.0 NFC、sorted keys、compact UTF-8、float/NaN禁止というsemantic canonical codecを使います。実runtime identityを後からrequestへ補完しません。wire bytesはrequest_idを含むcanonical JSON一つで、末尾LF無しです。request preimage digestとfull wire bytesのSHAは別です。

`RetainedRequestFrameV2`はimmutable canonical bytes/request ID、非serialized source-seal ID/execution-asset-set IDを保持し、fresh record projectionを返します。直接constructorやduck frameをadmissionに使いません。private owner stampにより、同じversion header/trusted profileを持つ別adapter bodyへの再bindingを拒否します。これはsame-UID敵対者へのsecurity boundaryではなく、owner間の整合契約です。raw source bytesとprivate stampをreprへ出しません。

`validate_request_record_v2`はself-consistentなデータまで、`validate_request_source_binding_v2`は実sealと保持adapter/trusted metadataへの独立joinまで、`validate_request_frame_v2`はtyped owner stampとcanonical bytesまでを検証します。validatorはbuilderで期待requestを再生成しません。旧v1 request envelope/runtime gateへ変換もしません。再利用する旧reference helpersは変更しないsource/entity ID、canonical codec、context/files invariantだけです。

## 生成・送信の限界

generated JSONはhash/schema処理より前にdepth 64、各array 100,000、key/value各UTF-8 string 8 MiBを検証します。response-onlyのaggregate-array 100,000をrequestへ適用しません。encoded stdinは**実bytes長**96 MiB（100,663,296）以下を要求し、保持frameをdecodeするときも先に測定します。response 16 MiB capとの混同、callerのlimit緩和、silent truncationを許しません。

referenceのJSON-bound validatorとbyte-bound validatorは異なるseamです。96 MiB exact/+1 testは実bytesを測定しますが、padding自体はvalid requestではありません。valid request shape/canonical/source-bound generationは別testsで証明します。productionのincremental stdin write、sent counters、deadline/cleanup、public typed failure mappingは後続gateです。referenceのSchema/ValueErrorをそのまま公開診断へ出しません。

## Independent known vector

`tests/fixtures/next_runtime_v2/source-sealed-request.json`はfixture repositoryの4 files、`.` project、`src/**/*` include、target `path:src/page.tsx`、semantic-json/builtin budget 500、adapter 0.1.0のliteralです。known hashesはbuilderではなく、literal preimagesを`jq -cjnS`でencodeし`shasum -a 256`で独立計算しました。全値がASCIIなのでUnicode profile差はこのvectorにはありません。

| 対象 | literal |
| --- | --- |
| project ID algorithm v1 | `next:project:530b20c858c6039c19737f386f96cfabdadda6b8a0a1c98b5ca639beb2765c25` |
| project config digest | `382ca8954a897ab23fcde46fc2c166ff7f3db5a453165aac875627f281525c05` |
| request_id | `364ae1c7150c97541f990bffc4a864ebc405cdf5d0472f3c250434a8f1375197` |
| canonical wire byte count | `3961` |
| full wire SHA-256 | `2775c51cb98c3a0c024521007b9c3473c65720ae592597fb9f4c7a9e675ce44f` |

data-only sliceです。request/policy/stdin capture、response request binding/context/limits/trusted echo、Core proof/hash、compatibility/public closure、実OS/TS/CLI/installed packageの認定はこのknown vectorから推測しません。
