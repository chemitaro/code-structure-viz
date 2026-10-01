# 実装ブリーフ — A02-3 request-bound publication candidate／measurement reference closure

## 1. 結論と検証済み基準

**次のcheckpointは、既存run2を唯一の入口にして、requested semantic JSON／PlantUMLの候補bytes、実descriptor、既存capture observationから導出する計測metadataを一つのimmutable ownerへ閉じる単位とします。**

ここで閉じる計測は、**候補artifactの実byte length／SHA-256と、既存runtime ownerが保持するcapture accounting**です。public stderrの最終診断集合、selected stdout copy、publication outcome／最終exit／publication sealは、このownerの後段へ分離します。未生成のmanifestやstdout-resultを仮置きして、最終publicationが成立したことにはしません。

GitHubコネクタで指定branch endpointを直接取得し、branch名と先端full SHAの完全一致を確認しました。他branchへのfallbackは行っていません。

| 項目 | 値 |
|---|---|
| Repository | `chemitaro/code-structure-viz` |
| Branch | `iss-00008-generate-nextjs-component-snapshots` |
| Expected／observed full SHA | `5cba0ec791ea4b9e48f036fd3043807ef7ef2a53` |
| 今回のcheckpoint起点 | 同上 |
| A02全体のbase | `710eb49a2a3143e31b8a91580700d16839d9070d` |
| 累積A03固定点 | `f4159066f3954454ad2f0c2701fa54bf1bc7bc4a` |

著者指定プロフィールは`GPT-5.6 Sol / Pro`、実装者はcaller-reported `gpt-6.1-sol`／`max`です。これは指定表示の記録であり、backend identityの検証結果ではありません。Blue authorの継続する実装ブリーフであり、独立Code Reviewではありません。モデル切替、subagent、UI監視は行いません。

本書は選択された実装単位の補助文書です。Requirement／Design／Planを変更せず、実装本体も提供しません。

---

## 2. authority、実装範囲、除外

### authority

Issue文書ディレクトリは次です。

```text
spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00008-generate-nextjs-component-snapshots
```

`requirement.md`は要件、`design.md`は採択済み設計、`plan.md`は実行順序、`report.md`は証拠として扱います。各Currentを優先し、維持意味はcanonical indexが指すschema／reference／testsで照合します。accepted ADRは同ディレクトリの`artifacts/20261001t024645z-adr-issue8-trusted-toolchain-launch-model.md`です。採択済みAのtrust model、static-only、同一process bootstrap、版移行、未観測値を補完しない原則は変更しません。

Round N、Report、過去助言、ignored promptは現在の仕様を上書きしません。A02の後に独立A03、その後にproduction A04がある順序も維持します。attachments-bundle

### 今回実装するもの

| 対象 | 出口 |
|---|---|
| PlantUML candidate leaf | 同じavailable Core ownerから、既存`code-structure-viz.plantuml/next/v1`のbytesと実descriptorを保持します。 |
| request-bound candidate-set owner | run2からrequested formatsだけを生成し、同じrun／Core／contextに結合します。 |
| candidate metadata schema | run2へのexact ref、artifact descriptor、実capture accountingだけを閉じます。 |
| 独立validator | producer／renderer／共有expected-record builderを呼ばず、ownerと保持bytesから照合します。 |
| tests／literal KAT | formats、outcomes、owner、型、bytes、privacy、実サイズ境界を検証します。 |
| docs／evidence | 新contract doc、限定Current Plan／Report、SpecDock evidenceを更新します。 |

### 今回実装しないもの

request-independent reader prefix、not-applicable、新ASSET policy／code／catalog／message、terminal fatal／usage／interruptの変更、production journal、filesystem transaction、最終manifest／stdout-result／publication finalizer、selected-copy disposition、最終exit／sealは対象外です。

production `src/`、依存／lockfile／package、actual Node／TypeScript／OS／CLI／wheel／sdist、旧schema／catalog／巨大reference／既存goldensも変更しません。新ASSET policyの回答待ちは、このrequest-bound単位を進めるために解消する必要はありません。

---

## 3. 検証した既存seamと再利用判断

| 検証済みの既存実装 | 今回の扱い |
|---|---|
| `next_run_decision_v2_reference.py`の`RetainedRequestBoundRunDecisionV2`、factory／projection | 今回の唯一の上位入力として再利用します。五branch、13-key fingerprint、17-slot provenance、Core measurementを再定義しません。 |
| `next_run_decision_v2_validation.py` | run2の保持recordと実runtime／Core／parentを検証する既存入口として再利用します。 |
| `next_public_artifact_v2_reference.py`の`RetainedPublicSemanticArtifactV2` | JSON candidate leafとして再利用します。 |
| `next_public_artifact_v2_validation.py` | JSON bytes／descriptor検証を再利用し、必要な型忠実性の確認だけを追加します。 |
| `next_public_semantic_v2_validation.py` | public recordと同じCore／contextの独立照合を再利用します。 |
| 旧referenceの`render_plantuml`、`validate_plantuml_contract` | 変更しないmodel-based renderer／独立parserとして限定再利用します。 |

現在のrun2は、transport successにmatching Core ownerを要求し、child／transport failureにCore ownerを付けず、interruptを拒否しています。新candidate factoryでもその分岐を保ちます。

既存JSON leafはCore ownerだけからcanonical JSON＋LFを生成し、実len／SHAをdescriptorへ保存しています。caller bytesやdescriptorを受け取る経路はありません。

### 旧巨大referenceから再利用しないもの

`PublicationBoundaryDecision`、`finalize_publication_decision`、`_publication_rendered_candidates`、旧run／domain／manifest全体への変換は使いません。これらは旧owner、旧public record、capture引数、test-side domain／manifest builderに依存しています。旧publication projectionの`bool(...)`／`int(...)`によるcoercionも新経路へコピーしません。

`render_public_diagnostic_stderr`、`copy_selected_stdout`、`publication_measurement_digest`は、後段の境界を理解するために確認したもので、今回のcandidate factoryから呼びません。特に旧measurement digestは四つのboundary measurementを入力にするため、未実施のpublic stderr／selected stdoutをゼロ値で埋めて利用してはいけません。attachments-bundle

---

## 4. 新しい内部ownerとinterface

以下はすべて**新規提案**です。現時点で存在するsymbolとして扱いません。

### 4.1 PlantUML leaf

既存の小さい`next_public_artifact_v2_reference.py`へ追加します。

| Symbol／interface | 契約 |
|---|---|
| `RetainedPublicPlantumlArtifactV2` | closed constructor、immutable、opaque reprを持ちます。 |
| `semantic_decision() -> ValidatedSemanticDecisionV2` | 元の同じCore ownerを返します。 |
| `wire_bytes() -> bytes` | 保持済みのexact bytesを返します。 |
| `descriptor() -> dict[str, Any]` | 六field descriptorのfresh copyを返します。 |
| `retain_public_plantuml_artifact_v2(decision: ValidatedSemanticDecisionV2) -> RetainedPublicPlantumlArtifactV2` | availableなCore ownerだけを受けます。status／model／bytes／descriptorの自由入力はありません。 |
| `validate_public_plantuml_artifact_v2(artifact: RetainedPublicPlantumlArtifactV2, decision: ValidatedSemanticDecisionV2) -> None` | 同一Core owner、保持bytes、既存grammar、実descriptorを独立検証します。 |

生成時は、検証済みCore gateから`complete`または`partial_safe`を取得し、同じcandidateのmodelを`render_plantuml(model, status=...)`へ渡します。public JSONの`status="incomplete"`をPlantUML rendererへそのまま渡してはいけません。

JSON leafと同様、このleaf単体はcontentのownerです。**requestednessを所有するのは次のaggregate**であり、leafの存在だけで「要求された」「公開された」と認定しません。

### 4.2 request-bound publication candidates

新規`tests/contracts/next_publication_candidates_v2_reference.py`へ配置します。

`RetainedRequestBoundPublicationCandidatesV2`の保持内容は次に限定します。

| 内部保持内容 | 意味 |
|---|---|
| 元の`RetainedRequestBoundRunDecisionV2` | 同じrun authorityです。 |
| artifact ownerのimmutable tuple | `RetainedPublicSemanticArtifactV2`／`RetainedPublicPlantumlArtifactV2`の必要な組だけです。 |
| canonical metadata bytes | §5のclosed reference recordです。 |

外部からraw response、Core、context、formats、limits、capture countsを再注入させません。failure bodyを持つfield、frame再読用closure、global cache、publication sealは追加しません。

| Interface | 契約 |
|---|---|
| `retain_request_bound_publication_candidates_v2(run_decision: RetainedRequestBoundRunDecisionV2) -> RetainedRequestBoundPublicationCandidatesV2` | 唯一の生成入口です。 |
| `run_decision() -> RetainedRequestBoundRunDecisionV2` | 元の同じrun objectを返します。 |
| `artifacts() -> tuple[RetainedPublicSemanticArtifactV2 \| RetainedPublicPlantumlArtifactV2, ...]` | requested format順の保持ownerを返します。 |
| `record() -> dict[str, Any]` | closed metadataのfresh copyを返します。 |
| `artifact_bytes(format_name: Literal["semantic-json", "plantuml"]) -> bytes \| None` | 対応する保持bytesだけを返します。未要求／unavailableは`None`です。 |
| `project_request_bound_publication_candidates_v2(owner: RetainedRequestBoundPublicationCandidatesV2) -> dict[str, Any]` | 保持metadataだけを投影します。 |
| `validate_request_bound_publication_candidates_v2(value: Mapping[str, Any], owner: RetainedRequestBoundPublicationCandidatesV2, *, run_decision: RetainedRequestBoundRunDecisionV2) -> None` | 別moduleで、期待する元run objectまで含めて独立照合します。 |

validatorへ渡す`value`は検証対象であってauthorityではありません。期待run objectを別に渡すことで、同値recordを持つ別runへのrebindも検証できます。

`artifact_bytes()`に未知formatを渡した場合は拒否します。`None`を`b""`へ変換しません。これにより「候補なし」と「存在するゼロbyte artifact」を混同しません。

### 4.3 factoryの分岐

factoryはrun2 validatorを通し、同じCore／contextから次を導出します。

| run2のbranch | artifact candidates |
|---|---|
| Core complete | requested formatsの全候補です。 |
| proof-backed partial-safe | 同じsafe subsetからrequested formatsの全候補です。 |
| complete-empty | 実際のCore modelに従う候補です。JSON／PlantUML自体は空bytesではありません。 |
| validated Core unavailable | 空tupleです。 |
| typed Core rejected | 空tupleです。 |
| closed child／transport failure | 空tupleです。 |
| interrupt／request-independent／未知branch | 入力拒否です。 |

formatsはheld `run_context.requested_formats`から取得します。JSON-only、PlantUML-only、両方を扱い、set化やソートで不正な順序を修復しません。両方の場合も、別Coreを作成せず同じCore objectを各leafへ渡します。

---

## 5. candidate schemaとfield ownership

### 5.1 新schema

新規pathは`schemas/next-publication-candidates-v2.schema.json`です。

これは**内部reference checkpointのmetadata schema**です。CLI output、最終publication record、新しい利用者向けformatではありません。

| 項目 | 定義 |
|---|---|
| `$id` | `urn:code-structure-viz:schema:next-publication-candidates-v2` |
| `schema` | `code-structure-viz.next-publication-candidates/v2` |
| `version` | integer `2` |
| 必須fields | `schema`, `version`, `run_decision`, `artifacts`, `capture_measurements` |
| 閉包 | rootと新nested objectsは`additionalProperties:false`です。 |

exact refsは次です。

| Field | Reference／制約 |
|---|---|
| `run_decision` | `urn:code-structure-viz:schema:next-run-decision-v2` |
| `artifacts.items` | `urn:code-structure-viz:schema:next-publication-decision-v1#/$defs/artifact_descriptor`をleafとして参照し、JSON／PlantUMLの二つの正しいconstant組へ絞ります。 |
| digestの補助定義が必要な場合 | 既存の変更しないdigest leafだけを参照します。 |
| `capture_measurements` | このschema内の小さいclosed定義です。旧四slot measurement全体は参照しません。 |

六field artifact descriptorは意味を変えず再利用できます。一方、旧measurementは`allowed`とretained量の制約まで含むため、単なるcapture accountingや未計測のpublic boundaryを表す型として流用しません。attachments-bundle attachments-bundle

`run-manifest.json`は今回のartifact descriptorに許可しません。leafが許可していても、今回のlocal branchで除外します。

### 5.2 artifacts

`artifacts`は**descriptorだけの配列**です。bytes／base64をmetadataへ埋め込みません。

| format | path | media_type |
|---|---|---|
| `semantic-json` | `next.snapshot.semantic.json` | `application/json` |
| `plantuml` | `next.snapshot.puml` | `text/vnd.plantuml; charset=utf-8` |

各descriptorは`domain="next"`、実保持bytesの`size_bytes`と`sha256`を持ちます。

available branchでは、requested formatsとdescriptor配列を順序付きで完全一致させます。unavailable branchでは配列を空にします。schemaでは可能な三format組とavailable／unavailableを閉じ、same-ownerやbytesへの一致はvalidatorで閉じます。

descriptorの存在はfilesystemへの保存やselected stdout availabilityを証明しません。

### 5.3 capture_measurements

必須keysは`adapter_stdout`、`adapter_stderr`だけです。それぞれ、実captureがなければnull、存在すれば次のclosed objectです。

| Field | authority |
|---|---|
| `captured_bytes` | 同じruntime observationの`capture.stdout_bytes`／`stderr_bytes`です。 |
| `capture_retained_bytes` | 同じobservationの`stdout_retained_bytes`／`stderr_retained_bytes`です。 |
| `eof` | 同じobservationの`stdout_eof`／`stderr_eof`です。 |
| `limit_bytes` | 同じrequest／policyに結合した`max_adapter_stdout_capture_bytes`／`max_adapter_stderr_capture_bytes`です。 |

`capture=None`なら両slotをnullにします。未観測をゼロbyte成功へ変換しません。

`capture_retained_bytes`は**既存capture observationの計測値**です。新candidate ownerがraw bodyを保持している量ではなく、heap zeroizationの証拠でもありません。正常captureのclosed child failureで計測値が残っていても、failure bodyの保持を追加しません。

`allowed`、`published`、`copy_status`は付けません。byte数がlimit以下であることだけでは、EOF、cleanup、semantic admission、publicationの成功を意味しないためです。

### 5.4 今回のschemaに入れないfields

`public_stderr`、`selected_stdout`、`stdout`、`publication_outcome`、最終`exit_code`、`seal`、publication専用hashは追加しません。未計測値をnullやゼロで埋めた「最終measurement map」も作りません。

元run2の`exit_code`、fingerprint、compatibility、17-slot provenance、entity／model-record measurementは、`run_decision`のexact refと同じownerの検証で維持します。候補setが空でも、それらを消したり成功へ変更したりしません。

---

## 6. bytes契約と独立validation

### JSON

既存のUnicode 15.0 NFC、key-sort、compact UTF-8 JSON＋LF一つを維持します。public recordは同じCore／parent contextから導出し、private responseのbytesをartifactとして使いません。

JSONのvalidatorは既存の独立public-record validatorを利用します。ただし、現行実装には保持値との通常のPython equality比較があるため、今回要求されたnumeric fidelityを維持する箇所は、**canonical JSON表現の一致または型を区別する比較**へ限定的に補強します。source count、request depths／limits、identity versions、collections／coverageの整数を、同値のfloatやboolへ置換して受理してはいけません。これは有効な出力の変更ではありません。

### PlantUML

`render_plantuml`はmodel／statusからbytesを生成し、`validate_plantuml_contract`はrendererを呼ばずstatement sequenceを照合しています。変更しないescape／external-target digest等のleaf共有は維持できます。

新leaf validatorでは、既存parserに加えて、UTF-8、BOMなし、LF-only、末尾LF一つ、blank／comment／余分なstatementなしというraw encoding条件を確認します。`splitlines()`による一致だけで、非LF区切りや余分な末尾行をexact-byteとして認めないようにします。契約のstatement順序、escaping、markers、member facets、relationsは変更しません。attachments-bundle

### aggregate validatorの順序

1. candidate ownerと期待runのexact nominal type、および`owner.run_decision() is run_decision`を確認します。
2. candidate schemaと、metadata cacheのcanonical表現を確認します。
3. 既存run2 validatorで、embedded run recordと実runtime／Core／parentを照合します。
4. held Core outcomeから、候補が存在すべきかを独立に判定します。
5. held requested formatsと、artifact ownerの型・順序・path集合を照合します。
6. 各artifactが同じCore objectを保持することを確認します。
7. JSONは独立public-record validator、PlantUMLは独立grammar parserで内容を検証します。
8. 全descriptorについて、constants、実len／SHA、整数型を再計算・照合します。
9. capture metadataを同じruntime observationとrequest-owned limitsから導出し、数値・boolの型も含めて照合します。
10. unavailable branchのartifact owner／bytes混入、private metadata追加、未実装publication fieldsを拒否します。

cacheと提出recordの一致は最初の照合にすぎません。producerとcacheを同時に同じ誤値へ合わせたconformance inputも、owner由来の検証で拒否します。

validatorから、新candidate producer、JSON／PlantUML renderer、producerのdescriptor／measurement expected-builderを呼びません。既存run2 validator、既存public validators、canonical codec、SHA primitive、schema loader、変更しないsemantic algorithmsは再利用できます。

### error contract

| 条件 | 処理 |
|---|---|
| direct constructor／duck owner／未知format型 | `TypeError`等で拒否します。 |
| foreign run／Core／artifact、field／bytes不一致 | `ValueError`で拒否します。 |
| schema-invalid metadata | schema validation errorを伝播します。 |
| 正規unavailable run | 空候補setを正常に生成します。空の成功ではありません。 |
| unknown/internal owner error、renderer invariant failure | 通常failureへcatch変換せず伝播します。 |
| interrupt／request-independent | このfactoryでは拒否します。terminal policyを追加しません。 |

---

## 7. 循環しない依存順序

### 今回閉じる依存

```text
既存runtime／receipt／Core／parent context
  → 既存run2
  → requested artifact leaf owners
      ├─ semantic JSON bytes
      └─ PlantUML bytes
  → 実artifact descriptors ＋ 既存capture accounting
  → RetainedRequestBoundPublicationCandidatesV2
  → metadata／bytesのreadonly projection
```

candidate schemaはrun2とdescriptor leafだけへ依存し、future publication／domain／root／stdout schemaへ依存しません。artifact bytesもcandidate metadataや将来のpublication sealを含みません。したがって今回の生成・検証には循環がありません。

Python moduleでも、validatorがproducerを実行する循環を作りません。型参照には`TYPE_CHECKING`やnominal type確認用の限定importを使い、producerは別validatorへ検証を委ねる既存の小さいmodule構成を踏襲します。

### 後続closureへの接続条件

以下は後続単位の依存契約であり、今回の実装認可ではありません。

| 順序 | 必要な後続closure |
|---|---|
| 1 | 同じrun2／Coreからcatalog-owned公開診断を導出し、public stderrの実JSONLと64 KiB exact／+1を閉じます。 |
| 2 | 同じcandidate-set ownerからsafe domain／root／summaryとtyped unavailableの候補を構築し、必要なv2 exact refsを閉じます。 |
| 3 | held selectorで一つのpre-copy streamを選び、actual `max_selected_stdout_bytes`で一度だけcopy判定します。 |
| 4 | copy／public stderrの結果から最終publication dispositionを確定します。semantic decisionを変更しません。 |
| 5 | 最終domain／root／summary／stdout／stderr bytes、measurements、descriptorを一つのfinal ownerへsealします。 |
| 6 | publication-v2 recordと全public projectionsは、そのfinal ownerの保持bytes／metadataだけを返します。 |

重要な非循環条件は次です。

**第一に、pre-copy candidateと最終結果を区別します。** manifest copyが+1だった場合、測定した元manifest候補のdescriptorを、publication failureを反映した最終manifestのdescriptorにすり替えません。成功候補を再copyしてstatusを収束させる処理は作りません。旧referenceにも、pre-copy candidateと後で保存するfailure-status manifestを区別する処理があります。

**第二に、final publicationのfull record／seal／selected result bytesを、それ自身がhashするroot／stdout bytesへ再帰埋込みしません。** 後続schema移行では、既存optional publication参照のrequirednessを勝手に強めず、同じownerからの非循環projectionを選びます。schemaの参照可能性と、実recordの自己包含は別です。dummy seal、空hash、固定点探索で穴埋めしません。

**第三に、今回のcandidate metadataを最終publication recordへ改名しません。** 後続は`next-publication-decision-v2`とdomain／root／stdoutの正しい依存closureを別に完成させます。旧run／runtime ownerへdowngradeして通す経路はありません。

---

## 8. 独立literalと既知hash

### 8.1 既存vectorを維持します

| 対象 | 固定値 |
|---|---|
| JSON-only public semantic bytes | LF込み`9472` bytes |
| 同SHA-256 | `545389abfa3975b2c95083db9cca6b8efbe071c4526b90cbe55fe9bdc84b5957` |
| 同13-key fingerprint | `066d76ba2cfbae97b137a7a1bd59a4181dee2c0ccf31f5c013a9a1735dc8c56e` |
| known complete raw response | `6320` bytes。public semantic bytesとは別です。 |

既存三run literalsも変更しません。これらはreference recordのKATであり、publication sealやpersisted artifactの証明ではありません。

**9472-byte fixtureはJSON-only contextです。** 両formatを要求するtestでは、正規の新context→request→runtime→matching Core→run2を生成します。formatsはconfig／request／13-key fingerprintに結合するため、両formatのJSONへ既存9472／`066d...`を無条件に期待してはいけません。 attachments-bundle

### 8.2 PlantUMLのworked ASCII literal

新規fixture案は`tests/fixtures/next_runtime_v2/public-plantuml-card.puml`です。

同じknown Card modelの、一つのProject、一つのModule、Component／member／relationなしに対応するliteralは次です。末尾LFを一つ含めます。

```text
@startuml
title CodeStructureViz Next snapshot
note top: status=complete; coverage=complete
legend
N_P project
N_M module
N_C component
<<export_binding>> export member
<<import_binding>> import member
<<prop>> prop member
--> static_import|literal_dynamic_import
..> jsx_render|component_wrap
facet=role:<value|type>|reexport=<true|false>|boundary=<none|server_to_client_entry>
marker=client_entry|router_context=<context>|client_dependency|server_candidate|unknown
marker=partial_safe
external=cloud-after-components-before-members
sort=kind-prefixed-id-utf8
endlegend
package "P:next:project:530b20c858c6039c19737f386f96cfabdadda6b8a0a1c98b5ca639beb2765c25" as N_P_530b20c858c6039c19737f386f96cfabdadda6b8a0a1c98b5ca639beb2765c25 {
}
component "M:src/Card.tsx" as N_M_824683f7952e8b11fdeb41f85419fe44398dac828c221140a11bd31e433df71e
N_M_824683f7952e8b11fdeb41f85419fe44398dac828c221140a11bd31e433df71e : marker=unknown
N_P_530b20c858c6039c19737f386f96cfabdadda6b8a0a1c98b5ca639beb2765c25 .. N_M_824683f7952e8b11fdeb41f85419fe44398dac828c221140a11bd31e433df71e : contains
@enduml
```

独立計算値は、**1082 bytes／24 LF**、SHA-256は次です。

```text
0bce98e4e12b722ff2685a76c52bddba7bca735af090ad735d94bbfc9e50c2a9
```

これは本回答で、契約のliteral statementと固定IDから標準ライブラリで計算した値です。repository rendererやrepository testsを実行して得た値ではありません。実装時には正規owner経路、既存独立parser、実descriptorの三者へ照合します。

### 8.3 candidate metadata literals

次を新規fixture候補にします。

```text
tests/fixtures/next_runtime_v2/publication-candidates-json-only.json
tests/fixtures/next_runtime_v2/publication-candidates-both.json
tests/fixtures/next_runtime_v2/publication-candidates-pre-spawn-failure.json
```

JSON-onlyは既存complete run literal、既知JSON descriptor、同じ入力から独立に綴ったcapture accountingを組み合わせます。bothは新しい正規contextに対応する期待値を独立作成します。pre-spawnは既存failure run literal、`artifacts=[]`、両capture slot nullです。

新producer／projectionから期待fixtureを生成しません。初回固定値はtest-sideの明示preimage、既知literal、独立ASCII JSON codec／SHAから作り、`jq`／`shasum`でも確認します。未作成metadata literalのfull hashを本書では推測しません。

---

## 9. testsと実サイズ境界

### 必須の観測面

| 群 | 検証内容 |
|---|---|
| requestedness | JSON-only、PlantUML-only、両方、正しい順序、余分／欠落／重複format拒否です。 |
| selector | 各requested setで有効なnull／manifest／domain selectorを保持します。selectorだけでartifact集合を減らしません。stdout成功は主張しません。 |
| outcomes | complete、proof-backed partial-safe、complete-empty、target／export／entity unavailable、typed Core rejection、通常runtime failureです。 |
| owner | foreign run、同contentの別run、別Core、別artifact、別parent contextを拒否します。 |
| bytes | rehashed noncanonical JSON、改変PlantUML、欠落marker／facet／relation、順序変更、余分な行を拒否します。 |
| numeric fidelity | version／size／capture count／limit／Core-derived integerのbool／float置換を拒否します。 |
| privacy | raw body、proof、base64 source、PID、host path、spawn metadataがcandidate metadata／reprへ混入しません。 |
| retained source | source filesystem変更後も元owner由来の候補は不変です。新たに対象sourceを再読しません。 |
| failure disposal | failure raw frameを新ownerへ追加せず、receipt後のmetadataだけで候補なしを保持します。 |
| cache-aligned mutations | 不正conformance inputとして、metadata cacheも合わせた偽descriptor／計測値をowner検証で拒否します。 |

内部collaboratorのmock／monkeypatch、private call-count／order testは使いません。独立性は、別の検証実装、worked literals、owner不一致、rehash mutationsで確認します。filesystem等の本来の外部seamの代替だけを許可します。

### 実サイズ境界

resource schemaではbyte上限が定数です。正常ownerを作るために小さい任意limitを注入したり、sealを改変したりしてはいけません。

| 境界 | 今回の扱い |
|---|---|
| 元response／captureの16 MiB exact／+1 | 既存の実byte境界testをadjacent gateに含め、新candidateへの計測引継ぎを確認します。actual bytesとobservation-derived countsを混同しません。 |
| JSON candidateの16 MiB exact／+1 | **どちらも保持対象です。** selected stdout capをcandidate作成capとして適用しないことを、正規available ownerからの実候補で確認します。 |
| selected stdoutの16 MiB exact／+1 | 後続finalizer gateです。今回はcopy結果／exit／typed stdoutを認定しません。 |
| public stderrの64 KiB exact／+1 | 後続の公開診断集合・byte gateです。child stderr captureとは別です。 |

large JSON candidate testは、bytesにpaddingを足した偽artifactでは作りません。test-only fixture helperで、実source seal、長いが有効なrelative paths、実project／file／Module rows、完全なproof、正規entity overrideを使い、public source-plan/config投影を含むcandidateが境界へ到達する入力を構成します。各path／string、raw response、model-record、aggregateの上限内でCore admissionを通した後、独立test-side codecで期待sizeを調整します。

このlarge fixtureの到達性とexact値は本回答では実行検証していません。実装者の完了条件です。先行gateで拒否された入力や、不正ownerへ埋め込んだ巨大bytesを「available candidateの16 MiB検証」に数えません。到達性を成立させられない場合は、その技術的blockerを記録し、縮小overrideへ置き換えて完了扱いにしません。

---

## 10. 変更ファイルとvertical TDD順序

### 最小の変更集合

| 種別 | Path |
|---|---|
| 新規schema | `schemas/next-publication-candidates-v2.schema.json` |
| 新規doc | `docs/contracts/next-publication-candidates-v2.md` |
| 新規producer／owner | `tests/contracts/next_publication_candidates_v2_reference.py` |
| 新規validator | `tests/contracts/next_publication_candidates_v2_validation.py` |
| 新規tests | `tests/contracts/test_next_publication_candidates_v2.py` |
| 新規PlantUML tests | `tests/contracts/test_next_public_plantuml_v2.py` |
| 新規test-only fixture helper | `tests/contracts/next_publication_candidates_v2_fixtures.py` |
| 既存leaf拡張 | `tests/contracts/next_public_artifact_v2_reference.py` |
| 既存leaf検証拡張 | `tests/contracts/next_public_artifact_v2_validation.py` |
| numeric fidelityの限定補強 | `tests/contracts/next_public_semantic_v2_validation.py` |
| schema登録test | `tests/contracts/test_json_schemas.py` |
| 続く境界への参照追記 | `docs/contracts/next-semantic-v2.md` |
| 新規fixtures | §8の四filesです。 |
| 限定進捗／実測 | Issueの`plan.md`／`report.md`とSpecDock evidenceです。 |

run2／receipt／runtimeの意味変更は予定しません。新testの都合だけでそれらのguardを弱めません。

### TDDの実行順

| 段階 | 一つずつ閉じるobservable behavior |
|---|---|
| 1 | JSON-only run2から既存9472-byte candidateだけを保持・投影します。 |
| 2 | 新PlantUML leafを正規Core ownerから生成し、1082-byte literalと独立parserへ照合します。 |
| 3 | PlantUML-only／両formatを同じrun／Coreへ結びます。 |
| 4 | partial-safe／complete-emptyを実proofと同じsubsetで保持します。 |
| 5 | 各unavailable branchを空候補setとして保ちます。 |
| 6 | capture absent／present、実counts／limits／EOFを導出します。 |
| 7 | foreign owners、rehash／cache-aligned mutation、numeric fidelity、privacyを閉じます。 |
| 8 | 実サイズ境界、既存adjacent gates、docs／evidenceを完成させます。 |

各段階は、一つのselected test bodyを実行して意図した欠落をREDとして確認し、最小変更で同じselectionをGREENにします。collection error、zero selected、fixture準備失敗をfeature REDに数えません。未実装schema分岐を一括で想像して先に大量追加しません。

---

## 11. 品質gate

### focused

```bash
uv run --locked --group dev pytest -q \
  tests/contracts/test_next_publication_candidates_v2.py \
  tests/contracts/test_next_public_plantuml_v2.py
```

### current owner／wire／Core／public隣接gate

```bash
uv run --locked --group dev pytest -q \
  tests/contracts/test_next_run_decision_v2.py \
  tests/contracts/test_next_observed_response_receipt_v2.py \
  tests/contracts/test_next_runtime_result_v2.py \
  tests/contracts/test_next_provenance_v2.py \
  tests/contracts/test_next_core_failure_v2.py \
  tests/contracts/test_next_semantic_candidate_v2.py \
  tests/contracts/test_next_exchange_v2.py \
  tests/contracts/test_next_process_observation_v2.py \
  tests/contracts/test_next_rejected_frame_v2.py \
  tests/contracts/test_next_request_frame_v2.py \
  tests/contracts/test_next_response_frame_v2.py \
  tests/contracts/test_next_analysis_context_v2.py \
  tests/contracts/test_next_public_semantic_v2.py \
  tests/contracts/test_next_public_artifact_v2.py \
  tests/contracts/test_json_schemas.py
```

### 維持するPlantUML／既存domain／Current pointer

```bash
uv run --locked --group dev pytest -q \
  tests/contracts/test_next_contracts.py -k plantuml
```

```bash
uv run --locked --group dev pytest -q \
  tests/contracts/test_python_goldens.py \
  tests/contracts/test_sqlalchemy_goldens.py \
  tests/contracts/test_next_contracts.py::test_round23_rg_18_current_schema_and_history_contract_are_explicit
```

`-k plantuml`はselected testsが実際に存在し実行されたことを確認します。新candidate gateの代用ではなく、変更しないrenderer/parser意味の回帰です。

### static／SpecDock

```text
uv run --locked --group dev ruff check .
uv run --locked --group dev ruff format --check .
uv run --locked --group dev mypy src tests
./spec-dock/scripts/spec-dock sync --no-github --no-update-active
./spec-dock/scripts/spec-dock validate
git diff --check
```

SpecDock引数は直前のlocal helpで確認します。

current baseの637 passed／730.28s、別selectionの17 passed／6.10s、Ruff/format217、mypy180、SpecDock10は保存済み証拠です。今回変更後の結果として再利用せず、新しい実測結果を記録します。重複selectionを合算しません。全pytest／全A02／A03 passでもありません。

---

## 12. docs、SpecDock、ordinary checkpoint

### 適用指示の確認

今回、root `AGENTS.md`の取得は404で、verified treeにも同fileはありませんでした。local user AGENTS／`user.rules`／`use-workbench`全文を確認したとは主張しません。実装者はlinked worktreeで書込み前にそれらを確認します。repository内の`.agents/skills/spec-dock/SKILL.md`は確認済みです。

ignored作業メモは、local `use-workbench`の実指示で安全に解決したpathを使います。未確認のCLI syntaxや別の固定pathを本書から作りません。

### durable evidence

local SpecDockのroot helpと`new artifact` leaf helpを読み、Issue配下にevidence Artifactを作成して実内容を記入します。metadata／generated storageを手編集するfallbackは使いません。

記録内容は、選択scope、採否、真のRED／GREEN、fixture不備との区別、literal preimages／hash、実行commands／results、型・privacy検証、未実施gateです。Planは限定進捗、Reportは実測だけを記載します。Requirement／Design／ADRを変更して今回の実装に合わせません。

### staging／commit／push

編集は`apply_patch`です。Git writeは、確認済みlinked worktreeを`workdir`にした直接tool callで、一回につき一コマンドだけ実行します。

```bash
git add -- \
  schemas/next-publication-candidates-v2.schema.json \
  docs/contracts/next-publication-candidates-v2.md \
  docs/contracts/next-semantic-v2.md \
  tests/contracts/next_publication_candidates_v2_reference.py \
  tests/contracts/next_publication_candidates_v2_validation.py \
  tests/contracts/next_publication_candidates_v2_fixtures.py \
  tests/contracts/test_next_publication_candidates_v2.py \
  tests/contracts/test_next_public_plantuml_v2.py \
  tests/contracts/next_public_artifact_v2_reference.py \
  tests/contracts/next_public_artifact_v2_validation.py \
  tests/contracts/next_public_semantic_v2_validation.py \
  tests/contracts/test_json_schemas.py \
  tests/fixtures/next_runtime_v2/public-plantuml-card.puml \
  tests/fixtures/next_runtime_v2/publication-candidates-json-only.json \
  tests/fixtures/next_runtime_v2/publication-candidates-both.json \
  tests/fixtures/next_runtime_v2/publication-candidates-pre-spawn-failure.json \
  spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00008-generate-nextjs-component-snapshots/plan.md \
  spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00008-generate-nextjs-component-snapshots/report.md
```

SpecDockが返した実Artifact pathも、別の直接`git add --`で明示stageします。無関係な既存staged作業を取り込みません。

次を個別に確認します。

```text
git status --short
git diff --cached --check
git diff --cached --
```

**staged diffは全文を確認します。** `--stat`のみ、truncated出力のみでcommitしません。旧schema／catalog／巨大reference／goldens、`src/`、`pyproject.toml`、`uv.lock`の非変更もbaseと比較します。

その後、それぞれ別の直接tool callで実行します。

```text
commit-codex -a
```

```text
git push -- origin iss-00008-generate-nextjs-component-snapshots
```

configured upstreamが指定branchを指すことを確認したうえで、clean local、local HEAD、対応upstream、live remoteのfull SHAを照合します。live確認は指定refだけに限定します。

```text
git ls-remote --exit-code origin refs/heads/iss-00008-generate-nextjs-component-snapshots
```

post-commit SHA／push結果／clean・upstream・live一致はignored Workbenchへ記録します。tracked Reportへ同じcommit自身のSHAを書き戻すための循環commitは作りません。

manual commit message、force、hook bypass、alternate index、fetch／rebase、history rewrite、shell-write trick、認証設定変更は行いません。

---

## 13. 完了条件と停止位置

このcheckpointの完了条件は、**run2を入力とする全選択branchについて、requested候補集合・実bytes・実descriptor・capture accountingが同じownerへ結合し、独立validatorと正負testsで閉じること**です。

加えて、正規available candidateの実サイズ境界、numeric fidelity、retained source、privacy、既存goldens不変性、focused／adjacent／static／SpecDock gates、ordinary commit／push後のfull-SHA一致を記録します。満たせなかった検証を、schema shape、fixture存在、縮小override、過去passで代替しません。

この範囲を成立させるための新Product／ASSET policy判断は確認していません。後続のpublic stderr、全selectorのselected-copy、publication／domain／root／stdout-v2 exact-ref closure、final sealは依然として必要です。**今回のcandidate ownerを最終成果の代替にはしません。**

本回答でrepository変更、repository tests、commit、push、独立レビューは実行していません。独立計算したのは、既存ASCII public JSONの9472-byte確認と、提示したPlantUML literalの1082-byte／SHAです。実装とlocal acceptanceは実装者の作業です。

**ここで停止します。A02全体完了、独立A03、production A04、両OS／TypeScript／package／Final A05へ自動進行しません。検証済み基準は`chemitaro/code-structure-viz`／`iss-00008-generate-nextjs-component-snapshots`／`5cba0ec791ea4b9e48f036fd3043807ef7ef2a53`です。**
