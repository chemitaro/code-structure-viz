# Next.js public semantic document v2

## 対象と境界

`schemas/next-semantic-v2.schema.json`は`domain=next`、`document_kind=snapshot`、`schema=code-structure-viz.semantic/v2`のclosed public recordです。compatibilityはv2へのexact ref、entity/proof/source/path/config/run-context/limitsの意味とID algorithmはv1を保持します。旧Next semantic文書全体をv2として検証するfallbackは作りません。

これはA02のreference data契約です。public record単体ではArtifact作成、末尾LF付きpublication bytes、実measurement、PlantUML、run/domain/root manifest、stdout/stderr/exit、実Node/TypeScript/CLI、installed packageは認定しません。新資材failure policyもここで採択しません。次節のretained candidate bytesもfilesystem publicationの認定とは別です。

## 親が保持する入力と公開可能性

`project_public_semantic_document_v2(decision)`の唯一の入力は、`validate_semantic_decision_v2`で再照合できるnominal `ValidatedSemanticDecisionV2`です。transport shape、caller hash、duck owner、Core rejectionを公開authorityにしません。

- `payload_available=true`かつCore `complete`だけがpublic `status=complete`。
- 証明付き`partial_safe`だけが`status=incomplete / incomplete_kind=partial_safe`。
- target失敗、unknown export、entity +1などのCore unavailableは生成を拒否し、空の成功へ変換しません。
- complete-emptyでもactual source seal、request、model/proof、Core gate、compatibilityが必要です。空のentitiesは入力失敗の代替ではありません。

request frameは同じ`RetainedNextAnalysisContextV2`を保持します。公開requestのprojectsはseal-derived config descriptor、targets/depth/formatsは保持intent、source-plan/limits/trusted digestは同じseal/assets由来です。private requestのprojectsと公開modelのprojectsはsemantic rowsであり、config descriptorと混同しません。domain-config/v1のdigestは自身のdigest fieldだけを除いたcanonical objectです。

private context stampはwire fieldではありません。同じwire bytesでも異なるdepth intentへのowner差し替えを拒否します。保持depthはresolved intentで、任意depthの解析実行や選択graphを証明しません。実compiler/query-selectionの受入れは別gateです。

## 新public run fingerprint

Designの閉じた13-key preimageを、保持ownerから導出してcanonical SHA-256にします。旧whole-runtime helperのprocess-v1/追加fieldsを流用しません。新document versionのhash contractであり、旧v1 hashを別preimageで再定義しません。

| key | authority |
| --- | --- |
| `source_view_fingerprint` | 同じsource sealのlogical SourceView |
| `source_plan_digest` | 同じsealのfinal source plan |
| `domain_config_digest` | 親が保持するanalysis contextのclosed config |
| `projects` | private requestのsemantic project rows |
| `targets` | 保持intent / requestの同じcanonical targets |
| `formats` | canonical run contextの`requested_formats` |
| `stdout_selector` | 同じrun contextの実selector。nullを補完しない |
| `limits` | seal / requestの同じlimits |
| `node_version` | 同じruntime bindingのNode観測値 |
| `typescript_version` | 同じretained trusted manifestの固定expected metadata |
| `adapter_version` | 同じ保持entrypoint header / request |
| `protocol` | 同じ保持adapter identity / requestのv2 protocol |
| `trusted_environment_digest` | 同じ宣言bytes ownerのlogical descriptor |

TypeScript 5.9.2というmetadataは実TS import/useの観測ではありません。candidate hash、PID、path、cwd、concrete launch policy、request/response bytes hash、compatibility/provenance IDはこのpreimageへ追加しません。limits変更はrun identityを変え、semantic entity ID algorithmは変えません。

## Producerと独立validator

producerはCore gateを再検証し、source/request/compatibility/modelをfresh recordへ投影します。modules/componentsだけをfull IDのUTF-8 byte順へmergeし、他のcollectionはCoreで認定済みの順序を維持します。raw source、base64、proof、private control/stamp、host process fieldsを公開しません。

`validate_public_semantic_document_v2(record, decision)`はproducerや共有expected-record builderを呼ばず、schema、同じsource/assets/request/context、config digest、13-key fingerprint、Core outcome、compatibility、collections/orderを独立joinします。shape-validな別source/coverage/order/status、再hashした別intent/compatibilityも拒否します。canonical codec、SHA-256、変更しないentity/source algorithmsだけを共有します。

## 同じ判定から一度保持するsemantic candidate bytes

`retain_public_semantic_artifact_v2(decision)`は同じavailable Core ownerだけを受け、上のpublic recordをUnicode 15.0.0 NFC・key-sort・compact UTF-8 JSON＋末尾LF一つへ一度serializeします。caller bytes、descriptor、status、measurementを引数にしません。nominal `RetainedPublicSemanticArtifactV2`はconstructorを閉じ、同じdecision・immutable bytes・canonical descriptor bytesを保持します。descriptor getterはfresh objectで、source diskの再readを行いません。

descriptorの六fieldは`path=next.snapshot.semantic.json`、`domain=next`、`format=semantic-json`、`media_type=application/json`、保持bytesの実`size_bytes`と`sha256`です。旧publication schemaのversionless `$defs/artifact_descriptor`だけをclosed shapeとして再利用し、旧publication decision全体・旧runtime validatorへ変換しません。

`validate_public_semantic_artifact_v2(artifact, decision)`はexact nominal typeとsame-object Core ownerを確認し、保持bytesをdecodeして独立public-record validatorへjoinします。元bytesがcanonical JSON＋LFと完全一致すること、closed descriptorのconstants・実len/hashを検証します。別recordやnoncanonical bytesのsize/hashだけを再計算しても拒否します。producerや共有expected-record builderを呼ばずに検証します。

固定ASCII public literalを独立`jq -cS . <file>`でserializeすると、LF込み9472 bytes、SHA-256は`545389abfa3975b2c95083db9cca6b8efbe071c4526b90cbe55fe9bdc84b5957`です。これは保持candidate bytesのknown vectorで、未実施のfilesystem persist・selected-copy measurement・final publication sealの代用ではありません。requested formatの実publication、PlantUML、全manifest/stdout/exitとselected stdout exact/+1は後続finalizer gateへ残します。persisted artifactにselected-stdout capを先行適用しません。

## Generic dispatcher v2

`schemas/semantic-v2.schema.json`は二つのexclusive branchでroutingします。

- Python／SQLAlchemyはdomain限定の旧generic semantic-v1 branch。保存済みsnapshot/diff文書のwire identityとbytesはv1のままです。
- Nextはexact Next semantic-v2 branch。旧Next-v1、旧compatibilityとの混在、新Nextを旧schemaへdowngradeしたrecordは拒否します。

`validate_semantic_dispatcher_v2(record)`はofflineのrouting/shape検証だけです。旧generic schemaは既存bytesを変えず、registryのretrieval URIへ登録します。任意remote retrievalやv1 Nextへのfallbackはありません。dispatcherのpassはCore owner admissionやpublication certificateではありません。

## 独立known vectorと残るgate

`tests/fixtures/next_runtime_v2/public-semantic-run-preimage.json`と`public-semantic.json`は既知ASCII source/Core corpusから明示したtest-side期待recordを固定したliteralです。新producerからfixtureを生成していません。初回固定後の更新は自動生成で追従させず、仕様と独立計算へ戻します。

独立`jq -cS . <file> | tr -d '\n' | shasum -a 256`ではpreimageが`066d76ba2cfbae97b137a7a1bd59a4181dee2c0ccf31f5c013a9a1735dc8c56e`、public recordが`d9cd6519d5911be7f043dfcec3ddb96a71cfaaccc11532a74191cedb99b3b13e`です。record hashは末尾LF無しのreference KATで、Artifact bytes/sealではありません。既存request known vectorの3961 bytes、request ID、wire SHA-256は不変です。

reader-owned early prefix、asset policy、run/publication/domain/root/stdout v2全chain、網羅gate、A03独立StrictとA04/A05の実製品受入れは残ります。旧runtime passやこのreference KATを完了証拠へ昇格しません。
