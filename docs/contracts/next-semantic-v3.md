# Next.js public semantic v3 — accepted target

公開する安全subsetと取得一覧を混同しない新document世代です。[admission v3](next-semantic-admission-v3.md)と[compatibility v3](next-compatibility-v3.md)に依存します。SI-05のschema/public/exact-ref referenceは、2026-10-03のexact 6d52ff7で必須aggregateとfresh独立step reviewがpassしました。SI-06 final-ownerとactual productionは未認定/未実装です。旧[semantic v2](next-semantic-v2.md)のpassやKATは新仕様のpassではありません。

## Closed public record

planned `schemas/next-semantic-v3.schema.json`は既存v2のexact root keysに**必須**`source_inventory_summary`を一つ追加します。`schema`は`code-structure-viz.semantic/v3`、compatibilityはv3 exact refに変更します。type/domain/document_kind/status/incomplete_kindと全entity/File/Project leafのshape/ID、source/request/coverage/diagnosticのshapeは維持します。Project.file_idsとFile集合は新admission profileのowner-closed safe viewです。program FileはFile自身と正規Moduleの公開可能性を確認した場合だけ公開し、untaintedでもowner Moduleが合法的に非公開ならFileも非公開です。Fileに偽taintを付けず、公開program File→Module一件の保証を維持します。取得membershipはpublic requestのseal-derived configに残り、model Projectsのsafe membershipと一致する必要はありません。

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

`acquired.files = safe.files + proof_only.failed_files + proof_only.excluded_files`、`records.accounted = records.published + records.proof_only = records.proof_discovered`（正常unique base）、`published_entities.total = modules+components`。`safe.files`は公開File実数で、F−Tの件数ではありません。`excluded_files`はFile自身のtaintと、owner Module原因のuntainted File除外の両方を含みます。Module原因だけのFileを`failed_files`や直接read/parse診断へ計上しません。schema shapeだけでこの等式やowner joinsを認定しません。summaryに新keyやproof-only paths/IDs/bytes/messagesを追加しません。public coverageの既存redacted/path/ref方針は変更しません。

## Hash / fingerprint

run fingerprintは旧v2十三区分のpreimageへ`semantic_admission_profile_id`だけを加えた**exact十四keys**です。

`source_view_fingerprint`、`source_plan_digest`、`domain_config_digest`、`projects`、`targets`、`formats`、`stdout_selector`、`limits`、`node_version`、`typescript_version`、`adapter_version`、`protocol`、`trusted_environment_digest`、`semantic_admission_profile_id`。

取得Projectの全membershipを`projects`へ入れます。source_partition_fingerprint、outcome/count、response body/process/host観測は結果であり追加しません。旧v2 hashをこのpreimageで再定義しません。model digest codecは不変ですが、safe modelの値は変わります。

semantic bytesはCJ15＋末尾LF一つ、同じCore ownerから一度保持。六field artifact descriptorのpath/domain/format/media-type/size/hash shapeは不変です。JSON/PlantUMLのrequested candidatesをselectorで削らず、candidate capとfinal selected-copy capを別ownerで一度測定します。

## Exact-ref migration closure

次はSI-05で追加したpaths/URN suffixです。十schemaとbounded public/exact-ref referencesはexact 6d52ff7で認定済みですが、outer四schemaのshape/ref通過をfinal-owner・finalizer・productionの成功証拠に数えません。旧schemaの維持宣言に対し、2026-10-03採択は現publication-v2のcapture二field、2026-10-04採択は現root-v2のNext指紋を限定訂正します。以下の「未作成」は採択時点の呼称です。

| owner / planned target | 変更と接続先 |
| --- | --- |
| `next-compatibility-v3` | 新十key compatibility。変えないleaf refsを保持。 |
| `next-semantic-v3` | compatibility-v3 exact ref、新summary、safe membership。 |
| `semantic-v3` | exact Next-v3 branchと既存Python/SQLAlchemy-v1 branch。既存generic semantic-v1とretrieval URIを保持し、bytesを変更しない。 |
| `next-provenance-v3` | 17 slots/kind/stage/codeは維持。semantic/compatibility/model/budgetはmatching Core-v3のactual values。observation wrapperは`next-observation/v3`、version3にして旧v2 digest/KATを保持。その他slotsの値は同じruntime-v2 ownersから取得。 |
| `next-run-decision-v3` | provenance-v3 exact ref、新Core-v3、十四key fingerprint。五branch categories/context/receipt/count優先順を維持。validated Core unavailable groupに、正しいproofだが同じsealのlocality不成立というSOURCE-003/source_readを加え、target/exportと同様にcompatibility/fingerprintは保持、entity budget実測はnull。旧run2 ownerをcastしない。 |
| `next-publication-candidates-v3` | run-decision-v3 exact ref、同じCoreのsemantic-v3/PlantUML、versionless artifact descriptorとcapture計測意味を維持。 |
| 未作成 `next-domain-manifest-v2` | legacy domain-v1に代わる新chainを直接compatibility-v3/provenance-v3/十四key familyへ接続。新しくv2を作るが旧v1は不変。 |
| 未作成 `next-publication-decision-v2` | run-v3、candidate-v3を同じfinal immutable ownerへjoin。未観測captureは両null、観測済みは両計測object。selected copy exact/+1、artifact descriptors保持、partial write0を維持。 |
| 未作成 `run-manifest-v2` | Next domain/publication新exact refs。同じrun-v3のsemantic指紋をdigest/nullで投影。Python/SQLAlchemy v1枝のnonnullと既存root所有権を維持。 |
| 未作成 `stdout-result-v2` | 新publication-v2 exact refからsummary/manifest/selected/typed unavailable/exit/stderrを一度投影。 |

上記各schemaのURNは`urn:code-structure-viz:schema:<target>`、wire schema identityは対応する`code-structure-viz.<target base>/vN`です。generic dispatcher自身はrouting URNであり、各domainのwire identityを上書きしません。既存`next-publication-candidates-v2`のartifact descriptor shapeだけはversionless leafとして使用できます。

**維持集合**: source/config/path/limits/run-context/applicability-v1、execution-assets/runtime-binding-v1、trusted manifest/descriptor-v2、process policy/observation-v2、private request/response-v2とcontrol、v1 entity/ID/recognition/export/props/relation/boundary/Unicode profiles。new adapter header0.2.0によるasset/request/control hashの新corpusと、旧0.1.0 KAT保存を分けます。runtime raw receipt/transport ownerを新public証明に昇格しません。

これはaffected-schema closureの契約です。SI-05の十schema・public/run/candidatesのreference ownerと独立validatorを追加し、outer四schemaはclosed literal/ref vectorsで検証します。publication-v2の必須`candidates`はcandidate-v3 exact ref、domain-v2の必須`schema`は新wire identity、trusted environmentはv2 descriptor leafです。domain/run/publicationの別tree間の実owner join、catalog-owned stderrと一回のfinal copyはSI-06以降で検証します。schema-only vectorの仮seal値はその認定ではありません。A03前に全consumerをcensusし、空placeholder schemaやadditive fallback union、旧文書へのdowngradeでは閉じません。

## Final publication capture observation — 現v2限定訂正

2026-10-03の[accepted ADR](../../spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00008-generate-nextjs-component-snapshots/artifacts/20261003t142223z-adr-si06-capture-observation-current-v2.md)により、`next-publication-decision-v2.measurements.adapter_stdout`と`adapter_stderr`をnullable pairへ限定訂正します。wire identity/version2/URN、outer exact refs/keys、旧measurement objectのshape/意味を維持し、新version/fallback unionを追加しません。

同じcandidates-v3がcaptureを保持しない場合だけnull/null、保持する場合はobject/objectです。nullは未観測、objectの0は実capture済み0です。片側null、元ownerのcapture有無/実値との不一致、未観測zero-fill、再capture、free値の注入を拒否します。`public_stderr`/`selected_stdout`は実測objectのままです。元stage/code/semantic outcomeを保持し、capture未観測だけをpublication overflowへ変えません。schemaのpair制約と独立owner/実bytes検証を分離します。

解析がunavailableでも結果を正しく公開できればpublicationは`published`/exit3です。validated Core unavailableで同じcandidateに適格なresponse linkがあれば保持し、rejected Core/runtime-onlyからresponseを補完しません。actual capture/final-stderr overflowでpublication自体が`payload_unavailable`になればresponse=null/artifacts空です。selected-copy overflowは元semantic status/descriptorを維持し、後続stderr failureは最終公開failureを優先します。pre-copy実測と置換stdoutは別で、再測定しません。

物理schemaへの反映とfinal ownerは先行Spec Review後のSI-06 TDD/gatesで証明します。既存object/object recordは新schemaでもvalidですが、旧object-only validatorは新null recordを拒否します。schema/producer/validator/vectorsを同時切替/rollbackし、未更新consumerへ新null recordを送らず、外部/永続consumerのv2不変要求が判明したら切替を止めて再判断します。旧SI-05 certificateの原bytes/passを保持し、訂正後capture契約に流用しません。下位runtime/Core/run/candidates、旧leaf/旧KAT、既存domains、別ASSET policyは変更しません。

## Root manifest fingerprint and parent configuration — 現v2限定訂正

2026-10-04の[accepted ADR](../../spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00008-generate-nextjs-component-snapshots/artifacts/20261004t033836z-adr-si06-root-fingerprint-current-v2.md)が正本です。SI-06のrequest-bound Next snapshotに必要な最小訂正として、`run-manifest-v2`のwire identity/URN/keysを維持し、Next枝の`run.fingerprint`にdigest/nullを認めます。旧root-v1、Python/SQLAlchemyのnonnull制約とbytesは維持します。共有defsをnullableにするだけで全domainを緩めてはいけません。

### 同じsemantic指紋の投影

`root.run.fingerprint == domain.run_fingerprint == run-v3.context.run_fingerprint`を同じrun ownerから導出し、独立validatorで照合します。fingerprintの定義は上記のexact十四keyのままです。

| 同じrunが保持する状態 | root/domain指紋 | domain request / root next_requestの指紋field |
| --- | --- | --- |
| matching transport/Core無し（stage failure、timeout等） | null | `run_fingerprint` fieldを省略 |
| matching Core rejection | 十四key digest | 同じdigest |
| validated Core unavailable（SOURCE/TARGET/EXPORT/entity等） | 十四key digest | 同じdigest |
| complete / partial-safe | 十四key digest | 同じdigest |

request-boundのrequest/config objectは指紋nullでも保持します。省略するのはoptional指紋fieldだけで、field値をnullにしてschemaを緩めません。public semantic payloadを公開できないfailureにpayloadを生成しません。final capture/stderr/selected-copy failureも元runの指紋を変えません。指紋非nullは解析成功や実compiler使用の証明ではありません。

### 親設定の由来を最小限保持する

rootの`config.resolved`は同じanalysis contextのdomain configとrun contextから投影します。必要なのはその値の選択元だけです。親の設定解決時に、全体の`config.source`と七項目それぞれの「実際に選択した値・選択元」をimmutableな補助入力へ一度保持します。referenceではこの親側選択結果を明示的な入力境界とし、実CLI/file readの証明とは区別します。親の選択結果からoriginを取り出す処理と、最終rootへ投影する処理を混同しません。

- 全体の`config.source`は`builtin / repository / explicit`です。CLI上書きがあっても全体sourceを`cli`にはしません。
- 七項目は`next_projects / next_targets / formats / upstream_depth / downstream_depth / limits / trusted_environment`です。各選択元は既存enumの`builtin / repository / explicit / cli`を保持します。値が既定値と等しいことからbuiltinを推定せず、実際の選択元を使います。
- 選択したproject roots、targets、formats、depths、limits、trusted digestは同じcontextの値へ完全一致させます。same-contentでも別analysis contextへ転用しません。SI-06 request-boundではlimits/trustは観測済みなので`unobserved`を受け付けません。request-independentの既存unobserved意味は後続reader-prefix unitで扱います。
- 完成するfinal ownerは全selectorでこの補助入力を保持し、同じcandidatesのrequest.analysis_contextへ結合します。入力不足時は通常factoryで拒否し、builtin/golden/TypeScript configのdeclaring pathから補いません。既存artifact-selectorのfixtureも正当な親の選択入力を保持するよう更新し、root無しの別final ownerや自動builtin fallbackを残しません。
- 独立validatorは元の親選択結果とcontextからroot値・七originを別経路で照合します。producerのexpected-record生成やcached rootの一致だけで受理しません。root `config.sha256`は既存rootの式、すなわち自身のsha256 fieldを除くconfig全体のcanonical digestです。新hash familyは作りません。

この入力追加は内部の親設定由来だけを補うものです。既存analysis context/runtime/Core/run/candidatesのpublic契約・hashにfieldを足さず、最終公開は引き続き一つの`RetainedFinalPublicationV2`が所有します。既存final reference/validator内の小さい型/関数で実装し、新public receipt/schemaや汎用config frameworkは追加しません。設定値とoriginが同じ親の選択から来ることをreferenceで検証した後、A04の実CLI resolverをその入力へ接続します。

### 切替・受入れ

schema/producer/validator/vectorsを同じ候補で切り替えます。外部v2不変義務が判明した場合は新Next recordの提供を止め、再判断します。rollbackでは旧record/他domainを維持し、nullを旧形式用の偽hashへ変換しません。新version、dual reader/write、外部保存物の移行は追加しません。

SI-P09/SI-N17は全selectorでnull/nonnull predicateとroot/domain/request join、任意・generic・ゼロhash、別owner、既存非Next null拒否を検証します。SI-P10/SI-N18は正当な親選択元、偽origin・値不一致・別context・cacheを含む改変を検証します。configured64KiB/16MiBの既存境界を省略せず、schema shapeとactual final owner/bytesの証拠を分けます。旧SI-05 passは当時の証拠として保持し、訂正範囲は新SI-06 candidateの検証と累積Code Reviewで認定します。
