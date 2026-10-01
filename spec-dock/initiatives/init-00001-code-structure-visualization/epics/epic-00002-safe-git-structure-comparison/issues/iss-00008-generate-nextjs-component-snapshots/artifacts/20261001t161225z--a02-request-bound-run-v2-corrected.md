# 修正版実装ブリーフ — A02-3 request-bound `next-run-decision-v2`

## 1. 結論・検証基準・訂正範囲

**前回§5.3の`RetainedRuntimeResultV2._response_frame`と`_response_frame_for_validation()`の追加案は撤回します。** child／transport failureで完全なresponse frameをprivateに保持することは、Currentが要求するfailure raw bufferの破棄と両立しません。修正では、**元frameが生きている間の独立byte検証**と、**破棄後のdescriptor-only receipt／owner照合**を分離します。Currentの破棄規則は変更しません。

### GitHub検証結果

GitHubコネクタの利用可能操作を確認し、指定repositoryの指定branch endpointを直接取得しました。返されたbranch名とfull tip SHAは、指定値に完全一致しています。他branchへのfallbackは行っていません。

| 項目 | 検証値 |
|---|---|
| Repository | `chemitaro/code-structure-viz` |
| Branch | `iss-00008-generate-nextjs-component-snapshots` |
| Expected SHA | `9b5e0d0fee6f30967dcc296d0f75a1588e56842d` |
| Observed tip SHA | `9b5e0d0fee6f30967dcc296d0f75a1588e56842d` |
| 判定 | 完全一致 |

継続するauthoring purposeは`issue8-a-bound-run-brief`です。著者プロファイルのcaller指定は`GPT-5.6 Sol / Pro`、実装者はcaller-reported `gpt-6.1-sol`／`max`、表示名では`GPT-6.1 Sol / Max`として記録します。これはcaller指定の記録であり、backend identityやpickerを実測したという主張ではありません。Luna sessionの主張、モデル切替、subagent、新たな独立レビューは含めません。

本書は、ローカルで採否を確認した後に前回ブリーフを置き換える候補です。Requirement／Design／Planの改訂や、広い実装範囲の認可ではありません。

### 前回から失効する助言

| 前回の箇所 | 今回の置換 |
|---|---|
| §5.3、§12 Stage 2 | failure frame保持を廃止し、live検証済みdescriptor-only receiptに置換します。 |
| §6.6、§9.2のresponse再計算 | retained candidateがある経路だけ元bytesから再計算します。破棄済みfailureはreceipt照合です。 |
| §10のfailure別response null指定 | failure名だけで決めず、実際に認定済みcomplete frameを観測したかで決めます。 |
| §14のGit手順 | `git add --`、staged diff全文確認、直接の`commit-codex -a`、明示branchへの通常pushに修正します。 |
| checkpointの記録先 | commit後SHAはignored Workbenchへ記録します。同じcommitのtracked Reportへ自己SHAを書き戻す循環を作りません。 |

---

## 2. authority・現在の実装・選択スコープ

以下をIssue文書ディレクトリとします。

```text
spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00008-generate-nextjs-component-snapshots
```

同ディレクトリの`requirement.md`は要件、`design.md`は採択済み設計、`plan.md`は実装順序、`report.md`は証拠として扱います。accepted ADRは`artifacts/20261001t024645z-adr-issue8-trusted-toolchain-launch-model.md`です。Currentを優先し、維持部分はschema/reference indexから追跡します。Round N、Report、前回回答、ignored correction promptをfallback authorityにしません。

添付の`.workbench/luna-max-implement/issue8-nextjs-snapshots/briefs/a02-request-bound-run-v2-correction-prompt.md`は全12行を確認しました。これは今回の訂正指示・ローカル文脈であり、verified commit内の仕様ではありません。

### 検証済みの既存実装

| Path／symbol | 現在の責務 |
|---|---|
| `tests/contracts/next_runtime_v2_reference.py`の`retain_runtime_result_v2` | live frameを観測へjoinし、descriptorを計算します。transport-admissibleな成功だけcandidateを保持します。 |
| 同`RetainedRuntimeResultV2` | source/assets/request、immutable policy/observation、response descriptor、nullable candidate／decoder rejectionを保持します。failure frame用fieldはありません。 |
| 同`RetainedRequestFrameV2.analysis_context()` | 親の`RetainedNextAnalysisContextV2`を保持します。 |
| 同`ValidatedSemanticDecisionV2` | matching candidate、source/assets、Core gate／compatibilityを保持します。 |
| `tests/contracts/next_core_failure_v2_reference.py`の`RejectedSemanticDecisionV2` | matching private candidateとtyped Core rejection metadataを保持します。 |
| `tests/contracts/next_runtime_v2_validation.py` | request／frame／observation／transport／Coreの検証を担います。現在のprovenance validatorには`runtime_provenance_values_v2`依存があります。 |
| `tests/contracts/next_public_semantic_v2_validation.py` | parent contextとDesignの13-key fingerprintを照合します。 |

特に既存`retain_runtime_result_v2`は、元frameを使える時点で`raw_sha256`、`byte_length`、`canonical_json`を導出し、failure結果にはframe自体を保持しません。この性質を維持したまま検証境界を明示化します。

### 今回の出口

request-boundに限定し、run2 schema、nominal run owner、descriptor-only receipt、producer、独立validator、literal vectors、正負tests、限定docs／Plan／Report／evidenceを閉じます。

**対象外**は、request-independent reader prefix／not-applicable、新ASSET policy・catalog・message、production journal、PlantUML、final manifests／stdout／publication finalizer、filesystem transaction、selected-copy／final-exit seal、actual Node／TypeScript／OS／package、独立A03／Finalです。

`assets_drift`の既存runtime failure写像は維持しますが、これは未採択のpackage acquisition／integrity policyを決定することではありません。A02全体のclosureは引き続き未完了です。

---

## 3. 訂正の中心：破棄前検証とdescriptor-only receipt

### 3.1 三つの状態を分けます

| 状態 | 後段へ残せるresponse evidence | 後段で可能な検証 |
|---|---|---|
| admissible transport成功＋matching Core owner | 既存candidate内のframe、receipt、Core owner | 元frameのlen／SHA／canonical flag、Core gate／rejectionを再検証できます。 |
| closed child／transport failureでcomplete frameを認定済み | closed observation内のcontrol/versionとdescriptor-only receipt | receiptの型・同一owner・metadata・capture/control joinsを照合できます。元bodyの再検証はできません。 |
| partial／unobserved／decoder-rejected response | complete-frame receiptはありません。decoder rejectionは既存private metadataのみです。 | 既存rejection／capture joinsを検証します。public responseはnullです。 |

**transport failureと、transport成功後のCore unavailable／rejectedは区別します。** 後者の既存Core ownerが再検証用candidateを保持する契約は維持します。そのcandidateをfailure receiptへ持ち込むことはありません。attachments-bundle

### 3.2 新規内部型：`RetainedObservedResponseReceiptV2`

配置先は`tests/contracts/next_runtime_v2_reference.py`です。

nominal、immutable、closed constructor、payloadを出さないreprとします。**receiptが新たに保存する値は、既存の三field descriptorだけ**です。結合には、親requestとruntime resultが保持する同一immutable observation snapshotを利用します。

| 内部field | 型・用途 |
|---|---|
| `_request` | `RetainedRequestFrameV2`。同じ親requestへの参照です。 |
| `_observation_bytes` | `bytes`。そのruntime result用に一度だけ生成した、既存closed observationのimmutable snapshotと**同じobject**です。 |
| `_descriptor_bytes` | `bytes`。`raw_sha256`／`byte_length`／`canonical_json`だけのcanonical metadataです。 |

interfaceは次に限定します。

| Interface | 契約 |
|---|---|
| `RetainedObservedResponseReceiptV2(...)` | 通常constructorは常に`TypeError`です。 |
| `request_frame() -> RetainedRequestFrameV2` | 元の親requestを返します。 |
| `control() -> dict[str, Any]` | 保持observationのclosed controlをfresh copyで返します。 |
| `descriptor() -> dict[str, Any]` | 三field descriptorをfresh copyで返します。 |

`_observation_bytes`はraw responseではなく、既存schemaで閉じたcontrol／capture／cleanup等のmetadataです。sourceやsemantic payloadを追加しません。receipt内にruntime resultへのback-referenceも作りません。これにより成功resultのcandidateをreceipt経由で間接保持する経路も避けます。

禁止する保持物は、元frame、raw stdout/stderr、parsed response、semantic payload、proof、body由来echoのコピー、memoryview、frameを捕捉したclosure／partial／generator、再読用path、例外traceback、global cacheです。

receipt ID、nonce、receipt専用hash、`validated=true`、`disposed=true`などの証明用boolは追加しません。`canonical_json`だけは、元bytesから実際に計算する既存descriptor fieldです。

### 3.3 same-runtime結合

既存runtime factory内でpolicy／observationをsnapshot化し、**その同一observation bytes objectをreceiptとruntime resultで共有**します。receiptを作った後に同じ値を再serializeし、別objectをresultへ保存してはいけません。

後段では、少なくとも次を同時に要求します。

- receiptがexact nominal typeです。
- receiptは`result.observed_response_receipt()`が返す同じobjectです。
- receiptのrequestは`result.request_frame()`と同じobjectです。
- receiptの`_observation_bytes`はresultの`_observation_bytes`と同じobjectです。
- snapshotの内容が、resultのpolicy／request／source/assetsと既存validatorで整合します。

snapshotはfactory呼出しごとに新規生成し、intern／deduplicate／cacheしません。同一request・同一内容で別runtime resultを二つ作った場合にも、観測snapshotのobject identityが異なることをtestで固定します。これは実際の保持metadataへの結合であり、新しいpublic identityではありません。

### 3.4 factory／validator interface

以下は新規のinterface契約です。実装本体は本書に含めません。

| Symbol | Signature・役割 |
|---|---|
| `_retain_observed_response_receipt_v2` | `(request: RetainedRequestFrameV2, observation_snapshot: bytes, frame: RetainedResponseFrameV2) -> RetainedObservedResponseReceiptV2`。runtime factory内部専用です。free descriptorやcontrolを受けません。 |
| `validate_observed_response_receipt_before_disposal_v2` | `(receipt: RetainedObservedResponseReceiptV2, frame: RetainedResponseFrameV2, *, request: RetainedRequestFrameV2, observation_snapshot: bytes, policy: dict[str, Any], seal: SourceAcquisitionSeal, assets: RetainedExecutionAssets) -> None`。live frameから独立再計算します。 |
| `validate_observed_response_receipt_v2` | `(receipt: RetainedObservedResponseReceiptV2, result: RetainedRuntimeResultV2) -> None`。保持済みmetadataとsame-object joinsを検証します。 |
| `validate_runtime_result_v2` | `(result: RetainedRuntimeResultV2) -> None`。result全体の保持状態と分岐別joinsを検証します。 |

新validatorは`tests/contracts/next_runtime_v2_validation.py`へ配置します。receiptを一時構築しても、live validatorが完了する前にfactory外へ返しません。

### 3.5 既存runtime factoryへの限定変更

`retain_runtime_result_v2(seal, assets, request, policy, observation, response) -> RetainedRuntimeResultV2`のpublic signatureは維持します。

変更点は次だけです。

- `_response_descriptor_bytes`を`_response_receipt: RetainedObservedResponseReceiptV2 | None`へ置き換えます。descriptorの二重正本を残しません。
- `observed_response_receipt() -> RetainedObservedResponseReceiptV2 | None`を追加します。
- 既存`response_descriptor()`は、receiptのfresh descriptorまたはnullを返す互換accessorとして維持します。
- `_from_joined_observations`は、factoryが確定したimmutable snapshotとreceiptをそのまま保持します。free descriptorを受ける内部経路は廃止します。
- `_candidate`と`_rejected_frame`の既存分離は維持します。
- `_response_frame`、`_response_frame_for_validation()`、その代替の隠し参照は追加しません。

factory内の順序は、snapshot化、既存owner／observation検証、live frame検証、receiptの独立検証、成功時だけcandidate生成、result構築、保持状態検証、返却です。

失敗結果へframe／parsed payloadを移さず、factory終了後の返却object graphから到達できない構造にします。callerが別途保持するtest入力の消去や、Python heapのzeroizationを保証したとは表現しません。

---

## 4. 各検証時点の責任とerror contract

### 4.1 live validatorで必ず完了する検証

`validate_observed_response_receipt_before_disposal_v2`はproducerのdescriptor計算helperを呼ばず、次を検証します。

1. request／source／assets／policy／observationの既存joins。
2. 元frameのexact nominal type、request-owned limitsでのbounded decodeとclosed response schema。
3. `SHA256(frame.raw_bytes)`、実`len(frame.raw_bytes)`、元bytesとpinned canonical JSON bytesの完全一致。
4. 再計算SHAと、frameの保持SHA、observationのresponse SHA、receiptのSHAの一致。
5. complete stdout、capture byte count、rawから読んだcontrolとobservation／receipt controlの一致。
6. branch固有の実証。foreign binding、control/exit不一致、response echo違反を、単なるfailure labelで認定しません。

既存のrequest／frame／observation検証は分離されています。特に`validate_response_request_v2`はadapter、request binding、trusted digest／limits／run contextのechoを検査しています。

`response_invalid`では、ownerとschemaの検証を先に完了し、上記の具体的なecho不一致をliveで確認します。既存factoryの広い`except ValueError`を、新しいreceipt成立の根拠として使いません。無関係なowner／internal errorを「echo違反が証明された」と扱わない制御へ整理します。receiptへ不正echo値やpayloadのコピーを保存する必要はありません。

### 4.2 破棄後にできること・できないこと

| 検証対象 | 破棄後のfailure validator |
|---|---|
| descriptorのclosed keys／型／canonical metadata表現 | 再検証できます。 |
| receiptとresultの同一request／観測snapshot | object identityと既存owner joinsで検証できます。 |
| SHA／lengthと保持済みobservation／captureの一致 | 照合できます。 |
| control内のversion表現・eligibility・binding・exit対応 | 保持済みclosed metadataから再検証できます。 |
| 元responseのraw SHA／length／canonical flag | **元bytesからの再計算はできません。live検証済みreceiptへ照合します。** |
| `response_invalid`の元payload echo違反 | **再判定できません。liveで当該観測snapshotへ結合した検証結果を引き継ぎます。** |
| `control_response`等のprovenance observation hash | 保持済みcontrol＋descriptorから、既存observation-v2 preimageを再計算できます。 |
| retained candidateがある成功transport | candidateの元frameから、byte-level検証を再実行できます。 |

後段の独立性は「producerの写像を共有せず保持ownerから照合すること」です。破棄済みデータを再生できることではありません。

### 4.3 保持数値を破棄証明にしません

transport terminal failureに対する既存のraw retained-byte count規則は維持します。一方、正常captureでclosed child failureを受けたときのcapture-stage countを、receipt導入のためだけにゼロへ書き換えません。**capture時点の計測値、resultの非保持、物理memory消去は別の事実です。**

### 4.4 error contract

| 条件 | 処理 |
|---|---|
| direct constructor、duck owner、異なるnominal type | `TypeError`です。 |
| schema-invalid record | schema validation errorを伝播します。 |
| foreign receipt／request／snapshot、field不一致、必要receipt欠落 | `ValueError`です。 |
| success runtimeにCore ownerがない | `ValueError`です。 |
| child／transport failureへCore ownerを付ける | `ValueError`です。 |
| 未知outcome／terminal identity、未対応分岐 | 拒否します。通常failureへdefaultしません。 |
| interrupt | run2 factoryで拒否します。ordinary provenance／run recordを生成しません。 |
| 無関係な`ValueError`／`RuntimeError`／`MemoryError`等 | 通常catalog failureへ変換せず伝播します。 |

frozen／nominal型は通常APIの誤用やowner置換を防ぐ境界です。反射的に全内部fieldを書き換えるhostile same-UID actorへの耐性は主張しません。採択済みAもその保証を含みません。

---

## 5. single-owner run decisionとclosed schema

### 5.1 新規run ownerとinterface

配置先は`tests/contracts/next_run_decision_v2_reference.py`です。

`RetainedRequestBoundRunDecisionV2`は、exact runtime result、nullable matching Core owner、immutableなrun record bytesを保持します。通常constructorは閉じ、getterはowner参照またはfresh projectionを返します。

| Symbol | Signature |
|---|---|
| `retain_request_bound_run_decision_v2` | `(runtime_result: RetainedRuntimeResultV2, *, semantic_decision: ValidatedSemanticDecisionV2 | RejectedSemanticDecisionV2 | None = None) -> RetainedRequestBoundRunDecisionV2` |
| `project_request_bound_run_decision_v2` | `(owner: RetainedRequestBoundRunDecisionV2) -> dict[str, Any]` |
| `validate_request_bound_run_decision_v2` | `(value: Mapping[str, Any], owner: RetainedRequestBoundRunDecisionV2) -> None` |

run ownerのaccessorは`runtime_result()`、`semantic_decision()`、`record()`です。validatorは`tests/contracts/next_run_decision_v2_validation.py`へ分離します。

factoryはfreeなstatus、outcome、exit、stage、code、hash、prefix、descriptor、measurement、bool gateを引数に取りません。

fixtureでも、**runtime resultを先に生成し、その`transport_candidate()`からCore ownerを作ります。** `candidate_for(...)`等で別candidateを生成してからruntime resultへ合わせる方法は使いません。同一contentでも別exchange ownerは拒否します。

### 5.2 root schema

新規pathは`schemas/next-run-decision-v2.schema.json`です。

| 項目 | 固定内容 |
|---|---|
| `$schema` | JSON Schema Draft 2020-12 |
| `$id` | `urn:code-structure-viz:schema:next-run-decision-v2` |
| `schema` | `code-structure-viz.next-run-decision/v2` |
| `version` | `2` |
| `request_independent` | `false` |
| `kind` | `request_bound_success`／`request_bound_failure` |
| `status` | `complete`／`incomplete` |
| `outcome` | `complete`／`partial_safe`／`payload_unavailable` |
| `exit_code` | `0`／`3` |

root必須fieldは次です。

```text
schema, version, kind, status, outcome, request_independent,
payload_available, exit_code, provenance, context, request,
response, core_measurement
```

rootと新規nested objectは`additionalProperties:false`です。request-independent、not-applicable、usage、fatal、interruptedのbranchは追加しません。将来branchのshapeだけを先行収録する必要もありません。

ここでの`exit_code`は保持run outcomeのreference projectionです。実際のCLI終了や、selected-copy失敗を含むfinal publication exitを確定するものではありません。

### 5.3 exact refs

| 対象 | Reference |
|---|---|
| `provenance` | `urn:code-structure-viz:schema:next-provenance-v2` |
| `context` | `#/$defs/request_bound_context` |
| `context.run_context` | `urn:code-structure-viz:schema:next-run-context-v1` |
| `context.observed_prefix` | `urn:code-structure-viz:schema:next-provenance-v2#/$defs/observation_map` |
| digest leaf | `urn:code-structure-viz:schema:next-execution-assets-v1#/$defs/digest` |
| target item | `urn:code-structure-viz:schema:next-config-v1#/$defs/target_key` |
| request descriptor | 新schema内`#/$defs/request_descriptor` |
| response descriptor | 新schema内`#/$defs/observed_response_descriptor` |
| measurement | 新schema内のclosed union |

既存provenance-v2には四kindがありますが、run2側でrequest-bound二kindへ絞ります。旧run／provenance／process全objectをrefしません。旧response descriptorの`canonical_json=true`も流用しません。

receiptのためのpublic field、schema、hash familyは追加しません。

### 5.4 五つの排他的branch

| Branch | kind／status／outcome | payload／exit | fingerprint／compatibility |
|---|---|---|---|
| Core complete | success／complete／complete | true／0 | 両方非null |
| Core partial-safe | success／incomplete／partial_safe | true／3 | 両方非null |
| validated Core unavailable | failure／incomplete／payload_unavailable | false／3 | 両方非null |
| typed Core rejected | failure／incomplete／payload_unavailable | false／3 | fingerprint非null、compatibility null |
| closed runtime failure | failure／incomplete／payload_unavailable | false／3 | 両方null |

schemaでは少なくとも次を閉じます。

- completeとpartial-safeはprovenance success、全17 observations、response非nullです。
- validated Core unavailableはTARGET／EXPORT／entity LIMITの対応だけです。
- typed Core rejectionは`response_validation / CSV-NEXT-PROTOCOL-001`、または`model_validation / CSV-NEXT-LIMIT-005`です。semantic／compatibility／model／budget observationsはunobservedです。
- runtime failureもsemantic suffix四slotはunobservedです。許可stage/codeは次節のruntime matrixに限定します。
- top-level kindとprovenance kindは一致させます。
- response nullなら`control_response`と`node_version`はunobservedです。response非nullでもruntime未観測のcontrolはあり得ます。
- cross-field equalityや数値大小比較はowner validatorでも検証します。schemaだけのpassをadmissionにしません。

---

## 6. field ownership・nullability・failure matrix

### 6.1 context

context必須fieldは次です。

```text
request_id, run_fingerprint, run_context, analysis_intent,
domain_config_digest, source_plan_digest, source_view_fingerprint,
compatibility_id, observed_prefix
```

| Field | Owner・nullability |
|---|---|
| `request_id` | 同じ`RetainedRequestFrameV2.request_id`です。常に非nullです。child bindingとは区別します。 |
| `run_context` | `request.analysis_context().run_context()`です。selector／formats／budgetを補完しません。 |
| `analysis_intent` | 同じcontextのtargets／upstream_depth／downstream_depthです。depthは既存の整数0..64を維持します。 |
| `domain_config_digest` | 同じheld configの自身のdigest fieldだけを除いて再計算します。 |
| `source_plan_digest` | 同じsource sealのfinal planから再計算します。 |
| `source_view_fingerprint` | 同じsource viewから取得・検証します。 |
| `run_fingerprint` | §7の条件で13-key hashまたはnullです。 |
| `compatibility_id` | matching validated Core ownerからだけ取得します。rejected／runtime failureはnullです。 |
| `observed_prefix` | `provenance.observed`のexact aliasです。別authorityではありません。 |

旧`process_observation_digest`は追加しません。host-local process objectをpublic contextへ戻しません。

### 6.2 request／response

| Field | 契約 |
|---|---|
| `request` | 常に非nullです。`request_id`、元`canonical_bytes`の`raw_sha256`／`byte_length`、`canonical_json=true`だけです。 |
| `response` | live検証済みreceiptがある場合だけ、`raw_sha256`／`byte_length`／boolean `canonical_json`を投影します。それ以外はnullです。 |

responseの非nullは、**完全なframeを観測してdescriptorを検証した**という意味に限定します。semantic acceptance、binding成功、runtime対応、Core成功を意味しません。

decoder-rejected bytesのhash／lengthは既存private rejection metadataに残りますが、public complete-response descriptorへ流用しません。

### 6.3 Core measurement

`core_measurement`はnull、または次の三field objectです。

| `kind` | `actual` | `limit` |
|---|---|---|
| `entity_budget` | matching validated Core gateの`actual` | 同じrequestの`limits.max_entities`。held `run_context.budget_resolved`との一致も検証します。 |
| `model_record_limit` | matching rejected Core ownerの`failure().model_records` | 同じrequestの`limits.max_model_records` |

target／export unavailable、Core invariant rejection、runtime failureはnullです。record-limit rejectionだけが`model_record_limit`であり、model-record countをentity countに置き換えません。型はboolではない整数として検証します。

complete-emptyでもCore gateの実測を使います。**Component数が0であることからModule＋Componentのentity countも0だとは推測しません。** 実測0のcorpusの場合だけ`actual=0`です。既存Core testsでもmodel-record数とentity数は別に測定されています。

### 6.4 failure matrix

以下のcodeは既存の`CSV-NEXT-`付き識別子です。新catalogは作りません。

| Owner evidence | stage | failure code |
|---|---|---|
| `unsupported_runtime` | `runtime_validation` | `CSV-NEXT-NODE-001` |
| `protocol_failure` | `response_protocol` | `CSV-NEXT-PROTOCOL-001` |
| `bootstrap_failure` | `bootstrap` | `CSV-NEXT-NODE-004` |
| `semantic_failure` | `semantic_analysis` | `CSV-NEXT-NODE-004` |
| `stage_failed`／`spawn_failed` | `node_spawn` | `CSV-NEXT-NODE-002` |
| `write_failed`／`read_failed` | `node_process` | `CSV-NEXT-NODE-004` |
| `stdout_limit`／`stderr_limit` | `adapter_stdout_capture`／`adapter_stderr_capture` | `CSV-NEXT-LIMIT-003` |
| `timeout` | `node_timeout` | `CSV-NEXT-NODE-003` |
| decoder raw-byte limit | `response_raw_bytes` | `CSV-NEXT-LIMIT-003` |
| decoder structural limit | `response_decode` | `CSV-NEXT-LIMIT-003` |
| malformed／duplicate／closed-schema rejection | `response_decode`／`response_schema` | `CSV-NEXT-PROTOCOL-001` |
| `binding_mismatch`／`response_invalid` | `response_validation` | `CSV-NEXT-PROTOCOL-001` |
| `exit_mismatch` | `node_process` | `CSV-NEXT-NODE-004` |
| `cleanup_unverified`／`candidate_drift`／`assets_drift` | `node_process` | `CSV-NEXT-NODE-004` |
| validated Core target／export／entity unavailable | `target_resolution`／`response_validation`／`model_validation` | TARGET-001／EXPORT-001／LIMIT-005 |
| typed Core invariant rejection／record +1 | `response_validation`／`model_validation` | PROTOCOL-001／LIMIT-005 |

responseとprefixは、この表のstageから推測しません。例えばstderr cap、timeout等でも、既存validatorが認めるcomplete controlを既に観測していればreceiptを残せます。未観測ならnullです。stdout cap breachやdecoder rejectionからcomplete controlを補完してはいけません。

target proof未成立のfailureに、target-completeness行、target failure reason、`CSV-NEXT-TARGET-001`を生成しません。

---

## 7. 13-key fingerprintと17-slot provenance

### 7.1 fingerprintは既存familyを維持します

preimageは次の13 keysだけです。

| Key | 導出元 |
|---|---|
| `source_view_fingerprint` | 同じsource seal |
| `source_plan_digest` | 同じfinal plan |
| `domain_config_digest` | held parent config |
| `projects` | private requestのsemantic project rows |
| `targets` | held intentと一致するrequest targets |
| `formats` | held run contextの`requested_formats` |
| `stdout_selector` | held run contextの実selector |
| `limits` | 同じseal／request limits |
| `node_version` | 実際に保持・検証したcandidate runtime binding |
| `typescript_version` | retained assetsに結合した固定expected metadata |
| `adapter_version` | 同じassets header／request |
| `protocol` | 同じadapter identity／request |
| `trusted_environment_digest` | 同じretained declarations由来descriptor |

この13-key構造は現行public semantic validatorでも使用されています。旧whole-runtime helperやprocess-v1追加fieldへ戻しません。

runtime resultにadmitted transport candidateとmatching Core ownerがある場合だけ非nullにします。Core rejectionでもtransport bindingは保持されているため同じfamilyを使用できますが、admitted compatibilityはないため`compatibility_id=null`です。

child／transport failureでは、controlにversionが見えていてもcandidate／bindingを生成せず、`run_fingerprint=null`です。`node_version:null`を含めた別preimage、failure専用hash、fake bindingは作りません。このnullabilityは今回の訂正指示とも一致します。

TypeScript `5.9.2`はexpected metadataです。実import／使用の証明へ昇格させません。

### 7.2 observation preimage

観測済みrowは、既存の次のfamilyを維持します。

```text
SHA256(CJ15({
  schema: "code-structure-viz.next-observation/v2",
  version: 2,
  field: <slot name>,
  value: <actual held value or defined portable projection>
}))
```

`CJ15`は既存pinned canonical codecです。未観測rowは`state=unobserved, value=null`です。

| Slot | 実値のowner |
|---|---|
| `applicability` | sealのpackage applicability observation |
| `config` | final planのresolved projects |
| `source` | source viewのfingerprint value |
| `limits` | final plan limits |
| `source_plan` | final plan |
| `trusted_environment` | request／assets／sealへjoinしたexpected descriptor |
| `runtime_bundle` | retained assets descriptor |
| `node_candidate` | policyのcandidate content SHAだけ |
| `request` | 同じretained request record |
| `launch_policy` | 既存portable policy projection |
| `process_start` | 実spawn primitive／parametersのportable projection、spawn無しならnull |
| `node_version` | receipt／observationのcontrol.runtime、未観測ならnull |
| `control_response` | 認定済みclosed control＋receipt descriptor、receipt無しならnull |
| `semantic_payload` | matching validated Core ownerだけ |
| `compatibility` | matching validated Core ownerだけ |
| `model` | matching validated Core ownerだけ |
| `budget` | matching validated Core gateのactualが非nullの場合だけ |

Core rejectionでは最後の四slotを生成しません。validated target／export unavailableではsemantic／compatibility／modelは保持Coreから導出できますが、未測定budgetはnullです。

portable projectionは既存規則を維持し、host path／PID／PGID／concrete cwd／local policy digestを新たに流入させません。17 slotsは固定長の時系列prefixではありません。attachments-bundle

---

## 8. 独立validatorの実装方針

### 8.1 今回、producer-helper依存を除去します

`validate_runtime_provenance_v2`の`runtime_provenance_values_v2`依存は、このsliceで除去します。先送りして「独立検証済み」とは表現しません。

validator側に、保持ownerから17 valuesを再導出するprivate helperを置きます。producerはそのhelperを利用しません。run validatorもproducerのrun record／fingerprint builderを呼びません。

新しい検証経路で共有するのは、immutableなslot／profile定数、canonical codec、SHA primitive、offline schema loader、既存source／semantic algorithms、nominal owner accessorsとowner validatorsです。

`trusted_environment`の期待値構築には、producerのprovenance値生成を使わず、検証済みrequestのdescriptorと同じassets／seal joinsを利用します。既存下位validator内部を含む全製品の独立性を、この限定変更だけで認定したとは表現しません。

### 8.2 run validatorの順序

1. exact run ownerとclosed run2 schemaを確認します。
2. runtime resultを分岐別に検証します。failureはreceipt照合、candidate有りは元frame／bindingも再検証します。
3. matching Core ownerのtype、candidate、source、assetsのobject identityを確認し、既存Core validatorを呼びます。
4. outcome／status／payload／exitと、provenance kind／stage／codeを別経路で導出します。
5. 17 slotのstateとhashを保持ownerから再計算します。
6. parent context、request／config／source identities、depth／selector／budgetを照合します。
7. fingerprintの非null条件と13-key digest、compatibilityの非null条件を検証します。
8. request descriptorを元request bytesから再計算します。
9. responseは§4の時点別責任で検証します。
10. Core measurementの種別／actual／limitと、observed-prefix aliasを照合します。

public recordと`owner.record()`の単純一致だけで検証を終えてはいけません。

### 8.3 独立性test

保持ownersを正常生成した後、以下のproducer helpersを呼ぶと例外になるよう差し替えても、固定literalに対するprovenance／run validatorがpassすることを確認します。

- `runtime_provenance_values_v2`
- `runtime_provenance_v2`
- `portable_launch_value_v2`
- run producer／projection／producer側preimage helper

live receipt validatorもreceipt producerのdescriptor helperを使わず、意図的に誤らせたdescriptorを元bytesとの不一致で拒否します。

---

## 9. 変更ファイル・literal KAT・TDD

### 9.1 ファイル計画

| 種別 | Path・変更内容 |
|---|---|
| 新規 | `schemas/next-run-decision-v2.schema.json` |
| 新規 | `docs/contracts/next-run-decision-v2.md` |
| 新規 | `tests/contracts/next_run_decision_v2_reference.py` |
| 新規 | `tests/contracts/next_run_decision_v2_validation.py` |
| 新規 | `tests/contracts/test_next_run_decision_v2.py` |
| 新規 | `tests/contracts/test_next_observed_response_receipt_v2.py` |
| 新規fixture | `tests/fixtures/next_runtime_v2/observed-response-protocol-failure.json` |
| 新規fixture | `tests/fixtures/next_runtime_v2/observed-response-protocol-failure-preimage.json` |
| 新規fixture | `tests/fixtures/next_runtime_v2/run-decision-complete.json` |
| 新規fixture | `tests/fixtures/next_runtime_v2/run-decision-pre-spawn-failure.json` |
| 新規fixture | `tests/fixtures/next_runtime_v2/run-decision-core-rejected.json` |
| 既存変更 | `tests/contracts/next_runtime_v2_reference.py`：receiptとsnapshot保持。failure frameは追加しません。 |
| 既存変更 | `tests/contracts/next_runtime_v2_validation.py`：live／post validators、provenance独立化。 |
| 既存変更 | `tests/contracts/test_next_runtime_result_v2.py`、`test_next_provenance_v2.py` |
| 既存変更 | `tests/contracts/test_json_schemas.py`：新schemaチェック。 |
| 既存変更 | `docs/contracts/next-provenance-v2.md`：破棄前後の検証責任を追記します。破棄規則は変更しません。 |
| 限定変更 | Issueの`plan.md`／`report.md`と、SpecDockが作成するevidence Artifact。 |

旧schema bytes、`next-diagnostic-catalog-v1.json`、巨大`next_reference_validation.py`、production `src/`、`pyproject.toml`、`uv.lock`、既存Python／SQLAlchemy outputsは変更しません。receipt seamのためにRequirement／Design／accepted ADRを改訂しません。

### 9.2 維持する既知vector

| 対象 | 固定値 |
|---|---|
| available 13-key fingerprint | `066d76ba2cfbae97b137a7a1bd59a4181dee2c0ccf31f5c013a9a1735dc8c56e` |
| retained semantic artifact | LF込み`9472` bytes |
| 同artifact SHA-256 | `545389abfa3975b2c95083db9cca6b8efbe071c4526b90cbe55fe9bdc84b5957` |
| `node_candidate` observation KAT | `49629589791b75238da6a7744ddb40b19386eb9482a8e05a90a2bf2717870def` |
| `process_start` observation KAT | `3869aabc86551c31c55fca1229360dc3efe591ab6449bb33dc465a3b8bf6b5d4` |

既存public recordとartifact bytesのhashでは末尾LFの有無を混同しません。attachments-bundle

### 9.3 新しいfailure-frame literal KAT

次のASCII一行の、表示上の改行を除いた262 bytesを`C`とします。

```json
{"control":{"adapter_version":"0.1.0","binding":{"request_id":null,"state":"unbound"},"protocol":"code-structure-viz.next-adapter/v2","result_kind":"protocol_failure","runtime":null},"schema":"code-structure-viz.next-adapter-response/v2","semantic_payload":null}
```

`observed-response-protocol-failure.json`は、`C`にLFを一つ付けた263 bytesとします。これは新producer出力ではなく、独立した固定literalです。

| 入力 | bytes | raw SHA-256 | `canonical_json` |
|---|---:|---|---|
| `C`、LF無し | 262 | `a1b2f3c703021e2c41f095771e4d16bb23fc1b4ce9ebea0edaa32dc8dc251407` | true |
| `C`＋LF一つ | 263 | `39f69e2d4585d53c3ff3ac4db463beba675bf4fa908b6f984f08927631150a25` | false |

このcontrolと各descriptorを既存`control_response` observation-v2 preimageへ入れたhashは次です。

| 入力descriptor | observation SHA-256 |
|---|---|
| LF無し | `fcb066cbc493a50d2403ac3f179c09167705dbcf390cce752e5f5a1837cf0164` |
| LF一つ | `6edadd2c0fcf54ca5477efc71e258580b669f26d92e2767fc5032d3af4f601d3` |

上記の長さとhashは、本回答でrepository producerを使わずASCII literalと標準ライブラリから計算しました。repositoryのschema／contract testsを実行した結果ではありません。実装時に通常のframe→runtime→receipt経路と独立validatorへ通して固定します。

このvectorでは、親requestはrequest-boundのまま、child controlはunbound、`node_version`はunobserved、`control_response`はobserved、run fingerprint／compatibilityはnullです。

full run literalsは、既知source/Core corpusと明示した期待fieldからtest側で作り、独立canonical化でfull hashを固定します。producerからfixtureを生成する更新器は作りません。まだ構築していないfull run literalのhashは捏造しません。

### 9.4 必須tests

| 群 | 観測可能な合格条件 |
|---|---|
| live descriptor検証 | raw SHA／length／canonical flag／control／captureの個別変異を拒否します。元frame.shaだけに依存しません。 |
| receipt owner置換 | 別request、別runtime snapshot、同一contentの別result、duck／direct constructorを拒否します。 |
| disposal | child／foreign binding／exit mismatch／late cleanup・drift結果から元frame／payload／proofへ到達できません。closure等も保持しません。 |
| post-disposal | 元frameへアクセスすると失敗するtestでも、failureのreceipt／provenance／run検証が成立します。 |
| descriptor mutation | public projectionの`canonical_json`だけを書き換えても、変更されていないreceiptとの不一致で拒否します。 |
| success | matching candidate frameからdescriptorを再計算し、receiptとも一致します。 |
| Core outcomes | complete、proof-backed partial-safe、complete-empty、target／export／entity unavailable、typed invariant／record +1を区別します。 |
| failure matrix | §6.4の各既存分岐と、control有無を実観測から導出します。 |
| fingerprint/context | 13-key各値、depth、selector、budget、source/config、compatibilityの再hash置換を拒否します。 |
| provenance | 17各slotのstate/hash、旧9-slot／v1 identity、suffix補完、prefix alias差し替えを拒否します。 |
| privacy／scope | body、proof、base64、host path、PID、spawn metadata、ASSET code、独立branchをrun2へ追加できません。 |
| errors | unrelated internal errorをordinary failureへ変換しません。interruptからrun2を生成しません。 |

破棄後に、反射的にreceiptと全関連ownerを同時改竄した攻撃をraw bytesから発見できる、というtestは要求しません。通常APIの閉包、liveでのproducer誤計算検出、後段projection／owner置換拒否を検証対象にします。

### 9.5 vertical Red–Green順序

| 段階 | 実施内容 |
|---|---|
| 0 | base／linked worktree／instructionsを確認し、SpecDock evidenceを作成します。 |
| 1 | receiptの新interface欠落を選択testでREDにし、最小nominal型とlive独立検証を追加します。 |
| 2 | runtime resultのreceipt joinを追加します。既存のfailure非保持が既にGREENなら、新規REDと偽称しません。 |
| 3 | foreign receipt、同content別snapshot、failure後frameアクセス禁止を一件ずつRED→GREENにします。 |
| 4 | run2 schemaのbranch／refs／nullabilityをRED→GREENにします。 |
| 5 | completeを最初のrun verticalとして、factory→owner→projection→独立validatorを閉じます。 |
| 6 | partial-safe／empty、Core unavailable／rejected、通常runtime failuresを順次追加します。 |
| 7 | provenance producer-helper依存を除去し、独立性test、rehash mutations、privacy、KATを閉じます。 |
| 8 | adjacent gates、docs、Current Plan／Report、evidence、ordinary checkpointへ進みます。 |

---

## 10. 品質gate・SpecDock・checkpoint

### 10.1 実装環境で確認する指示

このcommitのroot`AGENTS.md`取得は404でした。対応する非省略root treeにも`AGENTS.md`はありません。local user／linked worktreeのAGENTS全文を確認したとは主張しません。実装者は書込み前にローカルで適用される指示を確認してください。

以下のGit規則は、今回のcorrection promptで明示されたものです。

SpecDockのrepository skillは確認済みです。root helpと該当leaf helpを直前に確認し、`new artifact`で作成した実pathへ本書の採否／訂正根拠／実装証拠を記入します。metadataやgenerated storageを手編集しません。

### 10.2 focused／adjacent gates

依存・lockfile変更を起こさない設定で実行します。

```bash
uv run --locked --group dev pytest -q \
  tests/contracts/test_next_observed_response_receipt_v2.py \
  tests/contracts/test_next_run_decision_v2.py
```

```bash
uv run --locked --group dev pytest -q \
  tests/contracts/test_next_runtime_result_v2.py \
  tests/contracts/test_next_provenance_v2.py \
  tests/contracts/test_next_exchange_v2.py \
  tests/contracts/test_next_process_observation_v2.py \
  tests/contracts/test_next_response_frame_v2.py \
  tests/contracts/test_next_rejected_frame_v2.py \
  tests/contracts/test_next_core_failure_v2.py \
  tests/contracts/test_next_semantic_candidate_v2.py \
  tests/contracts/test_next_analysis_context_v2.py \
  tests/contracts/test_next_public_semantic_v2.py \
  tests/contracts/test_next_public_artifact_v2.py \
  tests/contracts/test_json_schemas.py
```

```bash
uv run --locked --group dev pytest -q \
  tests/contracts/test_python_goldens.py \
  tests/contracts/test_sqlalchemy_goldens.py
```

```bash
uv run --locked --group dev pytest -q \
  tests/contracts/test_next_contracts.py::test_round23_rg_18_current_schema_and_history_contract_are_explicit
```

以下も個別に実行し、結果を保存します。

```text
uv run --locked --group dev ruff check .
uv run --locked --group dev ruff format --check .
uv run --locked --group dev mypy src tests
./spec-dock/scripts/spec-dock sync --no-github --no-update-active
./spec-dock/scripts/spec-dock validate
git diff --check
```

SpecDock引数は直前のhelpで再確認します。未対応なら別の非公開手段で迂回せず、停止して記録します。

baselineのfocused26、related243、doc-pointer1、Ruff/format212、mypy176、SpecDock10は、既存semantic-bytes sliceの証拠です。新candidateの結果として転記しません。earlier `700d...`のbounded1316も再利用しません。新しい実測数、失敗、skip／deselectをそのまま記録します。

全pytest／全A02 gateは後続に残し、このsliceのpassをwhole-A02 passと表記しません。

### 10.3 docs／evidenceの範囲

新contract docには、receiptの内部性、live/post責任、failure非保持、nullability、13-key／17-slot、実装済みbranch、未認定範囲を記載します。

`next-provenance-v2.md`には検証時点の説明を追記しますが、既存のfailure disposal文言を緩めません。Planは限定進捗、Reportは実施済み結果のみです。evidenceには前回§5.3／Stage 2等の失効と、今回の採否を明示します。

### 10.4 ordinary staging／commit／push

全編集は`apply_patch`で行います。Git writeは、確認済みlinked worktreeを`workdir`にした**直接tool call一回につき一操作**です。shell連結やwrapperで複数writeをまとめません。

既存indexに無関係なstaged変更がないことを先に確認します。次のようにin-scope pathを明示stageします。

```bash
git add -- \
  schemas/next-run-decision-v2.schema.json \
  docs/contracts/next-run-decision-v2.md \
  docs/contracts/next-provenance-v2.md \
  tests/contracts/next_run_decision_v2_reference.py \
  tests/contracts/next_run_decision_v2_validation.py \
  tests/contracts/test_next_run_decision_v2.py \
  tests/contracts/test_next_observed_response_receipt_v2.py \
  tests/contracts/next_runtime_v2_reference.py \
  tests/contracts/next_runtime_v2_validation.py \
  tests/contracts/test_next_runtime_result_v2.py \
  tests/contracts/test_next_provenance_v2.py \
  tests/contracts/test_json_schemas.py \
  tests/fixtures/next_runtime_v2/observed-response-protocol-failure.json \
  tests/fixtures/next_runtime_v2/observed-response-protocol-failure-preimage.json \
  tests/fixtures/next_runtime_v2/run-decision-complete.json \
  tests/fixtures/next_runtime_v2/run-decision-pre-spawn-failure.json \
  tests/fixtures/next_runtime_v2/run-decision-core-rejected.json \
  spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00008-generate-nextjs-component-snapshots/plan.md \
  spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00008-generate-nextjs-component-snapshots/report.md
```

SpecDock Artifactも、CLIが返した**実path**を使う別の直接`git add -- <実path>`でstageします。placeholder、directory一括、wildcard、`git add .`は使いません。

その後、以下を個別に確認します。

```text
git status --short
git diff --cached --check
git diff --cached --
```

**staged diffは全文を確認します。`--stat`だけで代用しません。** truncationされた出力なら全範囲を読み終えるまでcommitしません。旧schema／catalog／production／依存／goldenの非変更もbaseと比較します。

次のwriteもそれぞれ別の直接tool callです。

```text
commit-codex -a
```

```text
git push -- origin iss-00008-generate-nextjs-component-snapshots
```

push後はlocal branch、clean状態、`git rev-parse HEAD`と、次のexact remote refを照合します。

```text
git ls-remote --exit-code origin refs/heads/iss-00008-generate-nextjs-component-snapshots
```

新full SHAとlocal／remote一致はignored Workbenchへ記録します。tracked Report／Artifactは実行対象のpre-commit treeとbase、commands、結果を記録し、commit後に自分自身のSHAを書き戻すための追加commitは作りません。

force、manual commit message、alternate index、hook bypass、fetch／rebase、history rewrite、認証設定変更、model switch、UI監視は行いません。

---

## 11. 完了条件・不確実性・停止位置

この訂正案は、既存の破棄規則を変更せず実装できます。receiptは新しいProduct／Policy／Security判断ではなく、**既存のlive検証と保持metadataの境界を型とtestsで明示する内部設計**です。未採択ASSET policyを決める必要はありません。

sliceの出口は、次の同時成立です。

- failure結果とreceiptから元frame／payload／proofへ到達できません。
- live validatorが実bytesとdescriptor／control／capture joinsを独立検証します。
- post-disposal validatorはreceipt照合だけを行い、できないbyte／echo再計算を主張しません。
- run2の全選択branch、owner joins、13-key/nullability、17-slot、measurement、privacyが正負testsで閉じています。
- provenance／run validatorからproducerのexpected-value helper依存が除去されています。
- literal KAT、focused／adjacent／static／SpecDock gates、旧成果物不変性が確認されています。
- ordinary commit／push後のexact full SHAと未実施gateが記録されています。

本回答ではrepository変更、repository tests、commit、push、独立レビューを実行していません。実行した計算は§9.3の独立literal長／hash確認です。実装者によるローカル採否と実測は残っています。

**ここで停止します。** request-independent prefix、新ASSET policy、全public exact-ref／finalizer closure、全A02 gate、累積base `f4159066f3954454ad2f0c2701fa54bf1bc7bc4a`からの独立A03は未完了です。本sliceからA03、A04 production、A05／Finalへ自動進行しません。

**connector検証済み基準：`chemitaro/code-structure-viz`／`iss-00008-generate-nextjs-component-snapshots`／`9b5e0d0fee6f30967dcc296d0f75a1588e56842d`です。本書はreference-onlyのA02-3訂正ブリーフであり、A02全体完了、独立A03レビュー通過、production／OS／TypeScript／package受入れの認定ではありません。**
