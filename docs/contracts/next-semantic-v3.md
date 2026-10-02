# Next.js public semantic v3 — accepted target

公開する安全subsetと取得一覧を混同しない新document世代です。[admission v3](next-semantic-admission-v3.md)と[compatibility v3](next-compatibility-v3.md)に依存します。schema/reference/actual productionは未実装です。旧[semantic v2](next-semantic-v2.md)のpassやKATは新仕様のpassではありません。

## Closed public record

planned `schemas/next-semantic-v3.schema.json`は既存v2のexact root keysに**必須**`source_inventory_summary`を一つ追加します。`schema`は`code-structure-viz.semantic/v3`、compatibilityはv3 exact refに変更します。type/domain/document_kind/status/incomplete_kindと全entity/File/Project leafのshape/ID、source/request/coverage/diagnosticのshapeは維持します。Project.file_idsとFile集合は新admission profileのsafe viewです。取得membershipはpublic requestのseal-derived configに残り、model Projectsのsafe membershipと一致する必要はありません。

`source`は同じsealed SourceViewの観測identityと全SourceView file count。`request`は同じ親intent/config/source plan/targets/depth/limits。safe subsetからsource/requestを再構成しません。public refsはsafe集合内に閉じ、private proof/record/source bytes/base64、control、host paths/PID/raw stderrは出しません。既存公開coverageのsafe・excluded・failed countsは検証済みproofを投影し、新summaryだけをもう一つの正本にしません。

available complete/partial-safeのnominal Core ownerだけから公開します。unavailable/rejected/null suffixをcomplete-emptyへ変えません。数値はnative nonnegative integerで、float/boolからのcoercionを拒否します。

## source_inventory_summary

exact七keysのclosed objectです。全nested objectも次のexact keysだけを持ちます。

| key | exact value / nested keys |
| --- | --- |
| `profile_id` | `next-source-inventory-safe-subset-v1` |
| `source_partition_fingerprint` | 検証済みpartitionのSHA-256 |
| `acquired` | `projects`、`files`、`file_bytes`：同じapplicable request inventoryとsealed bytes実測。 |
| `safe` | `projects`、`files`：公開Projects/Files。projectsはacquired.projectsと一致。 |
| `proof_only` | `failed_files`、`excluded_files`：File partitionの実件数。 |
| `records` | `proof_discovered`、`published`、`proof_only`、`accounted`：admissionの実record counts。 |
| `published_entities` | `modules`、`components`、`total`：safe model実数。 |

`acquired.files = safe.files + proof_only.failed_files + proof_only.excluded_files`、`records.accounted = records.published + records.proof_only = records.proof_discovered`（正常unique base）、`published_entities.total = modules+components`。schema shapeだけでこの等式やowner joinsを認定しません。summaryにproof-only paths/IDs/bytes/messagesを追加しません。public coverageの既存redacted/path/ref方針は変更しません。

## Hash / fingerprint

run fingerprintは旧v2十三区分のpreimageへ`semantic_admission_profile_id`だけを加えた**exact十四keys**です。

`source_view_fingerprint`、`source_plan_digest`、`domain_config_digest`、`projects`、`targets`、`formats`、`stdout_selector`、`limits`、`node_version`、`typescript_version`、`adapter_version`、`protocol`、`trusted_environment_digest`、`semantic_admission_profile_id`。

取得Projectの全membershipを`projects`へ入れます。source_partition_fingerprint、outcome/count、response body/process/host観測は結果であり追加しません。旧v2 hashをこのpreimageで再定義しません。model digest codecは不変ですが、safe modelの値は変わります。

semantic bytesはCJ15＋末尾LF一つ、同じCore ownerから一度保持。六field artifact descriptorのpath/domain/format/media-type/size/hash shapeは不変です。JSON/PlantUMLのrequested candidatesをselectorで削らず、candidate capとfinal selected-copy capを別ownerで一度測定します。

## Exact-ref migration closure

次は実装時に追加するplanned paths/URN suffixです。未作成のschemaを成功証拠に数えず、既存schemaを上書きしません。

| owner / planned target | 変更と接続先 |
| --- | --- |
| `next-compatibility-v3` | 新十key compatibility。変えないleaf refsを保持。 |
| `next-semantic-v3` | compatibility-v3 exact ref、新summary、safe membership。 |
| `semantic-v3` | exact Next-v3 branchと既存Python/SQLAlchemy-v1 branch。既存generic semantic-v1とretrieval URIを保持し、bytesを変更しない。 |
| `next-provenance-v3` | 17 slots/kind/stage/codeは維持。semantic/compatibility/model/budgetはmatching Core-v3のactual values。observation wrapperは`next-observation/v3`、version3にして旧v2 digest/KATを保持。その他slotsの値は同じruntime-v2 ownersから取得。 |
| `next-run-decision-v3` | provenance-v3 exact ref、新Core-v3、十四key fingerprint。五branch categories/context/receipt/count優先順を維持。validated Core unavailable groupに、正しいproofだが同じsealのlocality不成立というSOURCE-003/source_readを加え、target/exportと同様にcompatibility/fingerprintは保持、entity budget実測はnull。旧run2 ownerをcastしない。 |
| `next-publication-candidates-v3` | run-decision-v3 exact ref、同じCoreのsemantic-v3/PlantUML、versionless artifact descriptorとcapture計測意味を維持。 |
| 未作成 `next-domain-manifest-v2` | legacy domain-v1に代わる新chainを直接compatibility-v3/provenance-v3/十四key familyへ接続。新しくv2を作るが旧v1は不変。 |
| 未作成 `next-publication-decision-v2` | run-v3、candidate-v3を同じfinal immutable ownerへjoin。selected copy exact/+1、artifact descriptors保持、partial write0を維持。 |
| 未作成 `run-manifest-v2` | Next domain/publication新exact refs。Python/SQLAlchemy v1枝と既存root所有権を維持。 |
| 未作成 `stdout-result-v2` | 新publication-v2 exact refからsummary/manifest/selected/typed unavailable/exit/stderrを一度投影。 |

上記各schemaのURNは`urn:code-structure-viz:schema:<target>`、wire schema identityは対応する`code-structure-viz.<target base>/vN`です。generic dispatcher自身はrouting URNであり、各domainのwire identityを上書きしません。既存`next-publication-candidates-v2`のartifact descriptor shapeだけはversionless leafとして使用できます。

**維持集合**: source/config/path/limits/run-context/applicability-v1、execution-assets/runtime-binding-v1、trusted manifest/descriptor-v2、process policy/observation-v2、private request/response-v2とcontrol、v1 entity/ID/recognition/export/props/relation/boundary/Unicode profiles。new adapter header0.2.0によるasset/request/control hashの新corpusと、旧0.1.0 KAT保存を分けます。runtime raw receipt/transport ownerを新public証明に昇格しません。

これはaffected-schema closureの計画です。物理schemaとproducer/validator/fixture/全selectorの機械的closureはA02後続TDDで検証し、A03前に全consumerをcensusします。空placeholder schemaやadditive fallback union、旧文書へのdowngradeでは閉じません。
