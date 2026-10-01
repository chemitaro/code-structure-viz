# 実装ブリーフ — Plan A02-3 request-bound `next-run-decision-v2`

## 1. 検証済みの実装基準

GitHubコネクタで `chemitaro/code-structure-viz` のブランチ `iss-00008-generate-nextjs-component-snapshots` を直接取得し、ブランチ先端が期待値と完全一致することを確認した。

- repository: `chemitaro/code-structure-viz`
- branch: `iss-00008-generate-nextjs-component-snapshots`
- verified full SHA: `9b5e0d0fee6f30967dcc296d0f75a1588e56842d`

このブリーフは、Requirement・Design・Planを変更する仕様ではなく、選択済みA02-3スライスを実装可能な単位へ具体化する補助文書である。実装対象、根拠、隣接境界、検証可能な完了条件を示すが、より広い作業を認可しない。 attachments-bundle

実装者プロファイルは caller-reported `gpt-6.1-sol` / reasoning `max`。モデル固有の能力仮定は追加しない。Lunaは作業順序の参考に限定し、Luna sessionや証明を主張しない。実装はprimary agent単独のTDDで行い、subagent、UI監視、モデル切替を使わない。

---

## 2. 選択スコープと出口

### 実装するもの

Plan A02-3のうち、**validated requestが既に存在するrequest-bound結果だけ**について、次を一つの閉じたreference sliceとして実装する。

1. `code-structure-viz.next-run-decision/v2` のclosed JSON Schema。
2. `RetainedRuntimeResultV2`と、同一exchangeに結合した次のいずれかを唯一の入力とするnominal owner。
   - `ValidatedSemanticDecisionV2`
   - `RejectedSemanticDecisionV2`
   - Coreへ到達しなかった閉じたruntime failureの場合のみ`None`
3. ownerからrun decisionを生成するproducer／projection。
4. producerやexpected-record builderを呼ばず、ownerから全fieldを再計算する独立validator。
5. complete、proof-backed `partial_safe`、complete-empty、Core unavailable、Core typed rejection、全通常runtime failureの正負tests。
6. 独立literal fixtureと既知hash vectors。
7. contract docs、Plan/Reportの限定的なCurrent進捗、SpecDock evidence Artifact。

Plan上、A02-3は17-slot provenance、public semantic-v2、generic dispatcher-v2、parent context、retained semantic candidate bytesまではGREENだが、run/publication/domain/root/stdoutのv2 exact-ref closureは未完了である。本スライスはそのうちrun decisionだけを閉じる。A02全体およびA03は完了扱いにしない。

### 明示的に実装しないもの

- request-independent applicability/config/source reader prefix
- `request_independent_not_applicable`
- 新ASSET policy、ASSET診断、catalog/message/outcome変更
- `next-publication-decision-v2`
- domain/root/run manifest、stdout-result-v2のexact-ref closure
- PlantUML
- filesystem persistence、transaction、selected-copy measurement
- publication seal、final stdout/stderr/exit
- actual Node、TypeScript、CLI、wheel/sdist、macOS/Linux production owner
- A03 independent Strict review
- A04/A05またはIssue全体のacceptance

同梱資材の通常I/O unavailableと立証済みinstalled-package violationの境界は未採択のままである。このスライスで解釈、診断追加、既存catalog編集をしてはならない。Requirementはrequest-bound failureで未観測値を補完しないこと、pre-response failureでtarget completenessを捏造しないことを要求している。

---

## 3. verified existingとproposed work

### 3.1 verified existing

次のownerと関数は検証済みSHAに存在する。

- `tests/contracts/next_runtime_v2_reference.py`
  - `RetainedRuntimeResultV2`
  - `retain_runtime_result_v2`
  - `RetainedRequestFrameV2.analysis_context`
  - `RetainedNextAnalysisContextV2.domain_config`
  - `RetainedNextAnalysisContextV2.run_context`
  - `RetainedNextAnalysisContextV2.analysis_intent`
  - `ValidatedSemanticDecisionV2`
  - `runtime_provenance_v2`
  - `runtime_provenance_values_v2`
- `tests/contracts/next_core_failure_v2_reference.py`
  - `RejectedSemanticDecisionV2`
  - `inspect_semantic_candidate_v2`。expected Core invariant failureとmodel-record limitだけを閉じたrejectionへ変換し、無関係なinternal errorは伝播する。
- `tests/contracts/next_runtime_v2_validation.py`
  - `validate_runtime_provenance_v2`
  - `validate_semantic_decision_v2`
  - `validate_rejected_semantic_decision_v2`
- `tests/contracts/next_public_semantic_v2_reference.py`／`validation.py`
  - Designの13-key fingerprintを、producerとvalidatorが別経路で計算している。
- `tests/contracts/next_public_artifact_v2_reference.py`
  - `RetainedPublicSemanticArtifactV2`
  - これはcandidate bytes ownerであり、filesystem publication authorityではない。

`schemas/next-run-decision-v2.schema.json`はこのコミットには存在しない。既存run decisionはv1だけである。

### 3.2 v1から継承してはならないもの

`next-run-decision-v1`には次の新runtime不整合がある。

- bound contextが、実際には未観測でも`compatibility_id`と`process_observation_digest`を非nullにする。
- context内`observed_prefix`が旧9-slotである。
- response descriptorの`canonical_json`が常に`true`である。 attachments-bundle

現行v2 runtimeは、schema-validな単一JSONでも元bytesがcanonical serializationでなければ`canonical_json=false`を保持する。既存testでもindent付きresponseのfalseが確認されている。

したがって、旧run owner、旧whole-runtime helper、旧巨大validator、v1 run schemaのbranchをコピーまたはunion化してはならない。

---

## 4. proposed file set

### 新規

| path | 役割 |
|---|---|
| `schemas/next-run-decision-v2.schema.json` | request-bound二kindだけを持つclosed schema |
| `docs/contracts/next-run-decision-v2.md` | owner、branch、nullability、fingerprint、非認定範囲 |
| `tests/contracts/next_run_decision_v2_reference.py` | nominal owner、factory、projection |
| `tests/contracts/next_run_decision_v2_validation.py` | producer非依存validator |
| `tests/contracts/test_next_run_decision_v2.py` | branch matrix、mutations、KAT |
| `tests/fixtures/next_runtime_v2/run-decision-complete.json` | 独立complete literal |
| `tests/fixtures/next_runtime_v2/run-decision-pre-spawn-failure.json` | 独立pre-spawn literal |
| `tests/fixtures/next_runtime_v2/run-decision-core-rejected.json` | 独立Core rejection literal |

### 変更

| path | 限定変更 |
|---|---|
| `tests/contracts/next_runtime_v2_reference.py` | complete valid response frameをprivate ownerとしてruntime resultへ保持 |
| `tests/contracts/next_runtime_v2_validation.py` | provenance validatorをproducer-side values helperから独立させる |
| `tests/contracts/test_next_runtime_result_v2.py` | private frame保持、immutability、repr非漏洩 |
| `tests/contracts/test_next_provenance_v2.py` | validator独立性と17-slot owner再計算 |
| `tests/contracts/test_json_schemas.py` | 新schemaのclosed/check-schema登録 |
| `docs/contracts/next-provenance-v2.md` | run2とのjoin、17-slot alias、partial A02境界 |
| `spec-dock/.../iss-00008-generate-nextjs-component-snapshots/plan.md` | A02-3の限定進捗のみ |
| `spec-dock/.../iss-00008-generate-nextjs-component-snapshots/report.md` | 実行済みgateと未認定範囲のみ |
| SpecDockが返す新Artifact path | TDD、vectors、commands、結果、checkpoint証拠 |

次は変更しない。

- `schemas/next-run-decision-v1.schema.json`
- `schemas/next-diagnostic-catalog-v1.json`
- その他のold run/publication/domain/root/stdout schema bytes
- `tests/contracts/next_reference_validation.py`
- production `src/`
- `pyproject.toml`
- `uv.lock`
- Python／SQLAlchemy golden outputs

---

## 5. nominal ownerとAPI

### 5.1 新owner

```python
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True, slots=True, init=False)
class RetainedRequestBoundRunDecisionV2:
    """One immutable request-bound run authority; not publication or production acceptance."""

    _runtime_result: RetainedRuntimeResultV2 = field(repr=False)
    _semantic_decision: (
        ValidatedSemanticDecisionV2 | RejectedSemanticDecisionV2 | None
    ) = field(repr=False)
    _record_bytes: bytes = field(repr=False)

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError(
            "request-bound run decisions are created by "
            "retain_request_bound_run_decision_v2"
        )

    def runtime_result(self) -> RetainedRuntimeResultV2: ...
    def semantic_decision(
        self,
    ) -> ValidatedSemanticDecisionV2 | RejectedSemanticDecisionV2 | None: ...
    def record(self) -> dict[str, Any]: ...
```

`record()`はfresh objectを返す。projection mutationはownerへ戻らない。`repr`にはsource、semantic payload、proof、raw response、PID、pathを出さない。

### 5.2 factoryとprojection

```python
def retain_request_bound_run_decision_v2(
    runtime_result: RetainedRuntimeResultV2,
    *,
    semantic_decision: (
        ValidatedSemanticDecisionV2 | RejectedSemanticDecisionV2 | None
    ) = None,
) -> RetainedRequestBoundRunDecisionV2:
    """Close one request-bound runtime/Core result without caller outcome fields."""


def project_request_bound_run_decision_v2(
    owner: RetainedRequestBoundRunDecisionV2,
) -> dict[str, Any]:
    """Return a fresh public reference projection after owner validation."""
```

factoryは次を引数に取らない。

- `kind`
- `status`
- `outcome`
- `payload_available`
- `exit_code`
- `stage`
- `failure_code`
- fingerprint／compatibility ID
- provenance prefix
- response descriptor
- measurement
- bool gate

これらはすべてruntime/Core ownerから導出する。

### 5.3 runtime response ownerの最小拡張

現状、successful candidate以外ではruntime resultがresponse descriptorだけを保持するため、独立validatorは`canonical_json`を元bytesから再計算できない。次のprivate保持を追加する。

```python
@dataclass(frozen=True, slots=True, init=False)
class RetainedRuntimeResultV2:
    ...
    _response_frame: RetainedResponseFrameV2 | None = field(repr=False)

    def _response_frame_for_validation(
        self,
    ) -> RetainedResponseFrameV2 | None:
        ...
```

制約は次のとおり。

- 保持できるのは既にbounded decodeとclosed response schemaを通過した`RetainedResponseFrameV2`だけ。
- `RejectedResponseFrameV2`のraw bodyは保持・公開しない。
- accessorはrun/provenance validator用のprivate seamであり、semantic authorityを与えない。
- candidateがないchild failure、binding/exit mismatch、late cleanup/driftでも、既観測complete frameのdescriptor検証にだけ使用する。
- raw bytesはrepr、run record、diagnosticへ出さない。

---

## 6. `next-run-decision-v2` schema

### 6.1 top-level closed record

必須fieldは次に固定する。

```text
schema
version
kind
status
outcome
request_independent
payload_available
exit_code
provenance
context
request
response
core_measurement
```

定数とenum:

```text
schema              = code-structure-viz.next-run-decision/v2
version             = 2
kind                = request_bound_success | request_bound_failure
status              = complete | incomplete
outcome             = complete | partial_safe | payload_unavailable
request_independent = false
exit_code           = 0 | 3
```

`fatal`、`usage`、`not_applicable`、`interrupted`、request-independent kindはこのschemaに入れない。将来branchのshapeだけを先行追加することもしない。

### 6.2 exact refs

```json
{
  "provenance": {
    "$ref": "urn:code-structure-viz:schema:next-provenance-v2"
  },
  "context": {
    "$ref": "#/$defs/request_bound_context"
  }
}
```

context内部で次を利用する。

```text
run_context
  → urn:code-structure-viz:schema:next-run-context-v1

analysis_intent.targets items
  → urn:code-structure-viz:schema:next-config-v1#/$defs/target_key

digest
  → urn:code-structure-viz:schema:next-execution-assets-v1#/$defs/digest

observed_prefix
  → urn:code-structure-viz:schema:next-provenance-v2#/$defs/observation_map
```

`next-run-context-v1`はrequested formats、budget requested/resolved/source、stdout selectorを閉じている。
digestやpathのような意味が変わらないleafだけを再利用し、旧run decision、旧provenance、旧runtime owner全体へrefしない。

### 6.3 closed branch matrix

| semantic/runtime owner | kind | status | outcome | payload | exit |
|---|---|---:|---|---:|---:|
| validated `complete` | `request_bound_success` | `complete` | `complete` | true | 0 |
| validated `partial_safe` | `request_bound_success` | `incomplete` | `partial_safe` | true | 3 |
| validated Core unavailable | `request_bound_failure` | `incomplete` | `payload_unavailable` | false | 3 |
| typed rejected Core | `request_bound_failure` | `incomplete` | `payload_unavailable` | false | 3 |
| closed child/transport/runtime failure | `request_bound_failure` | `incomplete` | `payload_unavailable` | false | 3 |

`partial_safe`はpayload availableなrequest-bound successだが、public exitは3である。Requirementのcomplete／partial-safe／payload-unavailable区別をそのまま保ち、statusやexitをcallerが与えない。

### 6.4 context

```json
{
  "request_id": "<digest>",
  "run_fingerprint": "<digest-or-null>",
  "run_context": {},
  "analysis_intent": {
    "targets": [],
    "upstream_depth": 1,
    "downstream_depth": 1
  },
  "domain_config_digest": "<digest>",
  "source_plan_digest": "<digest>",
  "source_view_fingerprint": "<digest>",
  "compatibility_id": "<digest-or-null>",
  "observed_prefix": {}
}
```

旧`process_observation_digest`は設けない。host-local process objectをpublic context identityへ戻さない。

`observed_prefix`は新しい独立authorityではなく、`provenance.observed`のexact aliasとする。

```python
value["context"]["observed_prefix"] == value["provenance"]["observed"]
```

schemaは17-slot `observation_map`へexact-refし、validatorは同じownerから全digestを再計算する。旧9-slot定義やstageから推測したprefixは受け付けない。現行provenance-v2が持つ17 slotとclosed result identityを維持する。

### 6.5 request descriptor

request-boundなので常に非null。

```json
{
  "request_id": "<RetainedRequestFrameV2.request_id>",
  "raw_sha256": "<sha256 of canonical_bytes>",
  "byte_length": 3961,
  "canonical_json": true
}
```

- hashとlengthは`RetainedRequestFrameV2.canonical_bytes`から計算する。
- `canonical_json`はrequest builderの保持bytesがpinned canonical bytesと一致するためtrue。
- request body、filesのbase64、source contentsを公開しない。

### 6.6 response descriptor

```json
{
  "raw_sha256": "<actual retained frame sha256>",
  "byte_length": 1234,
  "canonical_json": false
}
```

または`null`。

- completeな`RetainedResponseFrameV2`が実際に観測・保持された場合だけ非null。
- hash、length、canonical flagはprivate retained frameの元bytesから再計算する。
- `canonical_json`はbooleanであり、const trueではない。
- descriptorの存在はsemantic acceptanceを意味しない。unsupported child、Core rejection、foreign binding、exit mismatch、late cleanupでもcomplete frameを観測していれば存在し得る。
- decoder rejection、partial stdout、cap breach、pre-spawn failureではnull。
- decoder-owned rejected raw hash、body、measurementはprivate rejection ownerに残し、ここへ投影しない。
- controlだけをsemantic successへ昇格させない。

### 6.7 Core measurement

`core_measurement`は次のclosed unionまたはnull。

```json
{
  "kind": "entity_budget",
  "actual": 2,
  "limit": 1
}
```

```json
{
  "kind": "model_record_limit",
  "actual": 10001,
  "limit": 10000
}
```

所有規則:

| branch | core_measurement |
|---|---|
| complete／partial-safe／complete-empty | `entity_budget`。Core gateのactualとresolved |
| entity budget unavailable | `entity_budget`。実actualとresolved |
| model/proof-valid record +1 | `model_record_limit`。rejected ownerの`model_records`とrequest limit |
| target unavailable | null |
| export unavailable | null |
| Core invariant rejection | null |
| child／transport／decoder／unsupported runtime | null |

`model_records`をentity countとして補完してはならない。target/export failureで実entity countが未測定ならnullを維持する。artifact paths、target proof、private failure reason、exception messageはrun recordへ入れない。

---

## 7. 13-key run fingerprintの決定

Designで固定済みのpreimageだけを使う。

```text
source_view_fingerprint
source_plan_digest
domain_config_digest
projects
targets
formats
stdout_selector
limits
node_version
typescript_version
adapter_version
protocol
trusted_environment_digest
```

現行known literalのhashは次である。

```text
066d76ba2cfbae97b137a7a1bd59a4181dee2c0ccf31f5c013a9a1735dc8c56e
```

そのfixtureには全13 fieldが明示されている。

### nullability規則

`run_fingerprint`を非nullにできるのは、次をすべて満たす場合だけ。

1. `RetainedRuntimeResultV2.transport_candidate()`が存在する。
2. matching `ValidatedSemanticDecisionV2`または`RejectedSemanticDecisionV2`が存在する。
3. semantic ownerのcandidate、source seal、assetsがruntime resultと同一objectである。
4. candidateのactual retained runtime bindingから`node_version`を取得できる。
5. parent-held context、request、assetsから他の12 valuesを取得できる。

したがって:

| branch | run_fingerprint | compatibility_id |
|---|---|---|
| complete／partial-safe／Core target/export/entity unavailable | 13-key hash | validated decisionのcompatibility ID |
| Core typed invalid／record +1 | 13-key hash | null |
| unsupported runtime | null | null |
| protocol/bootstrap/semantic child failure | null | null |
| pre-spawn／I/O／timeout／capture／decoder failure | null | null |
| binding/echo/exit mismatch、late cleanup/drift | null | null |

Core rejectionでもwhole-exchange candidateとactual runtime bindingは存在するため、同じ13-key run identityを計算できる。一方、rejected ownerはadmitted compatibilityを保持しないため`compatibility_id`はnullとする。

complete controlやNode versionだけを観測していても、transport candidate／runtime bindingが存在しないfailureからfingerprintを生成しない。`null`を含む別preimage、新しいfailure hash family、fake binding、fake Node versionを導入しない。

TypeScript `5.9.2`はretained assetsのexpected metadataであり、実import/useの観測ではない。この限定をdocsとtestsの両方に明記する。

---

## 8. factory branchとerror contract

### 8.1 factoryの閉じた判定

```text
runtime.result_kind == success
  + ValidatedSemanticDecisionV2
      complete       → request_bound_success
      partial_safe   → request_bound_success
      payload_unavailable → request_bound_failure

runtime.result_kind == success
  + RejectedSemanticDecisionV2
      → request_bound_failure

runtime.result_kind != success/interrupted
  + semantic_decision is None
      → request_bound_failure
```

### 8.2 拒否する組合せ

| 入力 | error |
|---|---|
| direct owner constructor | `TypeError` |
| duck runtime／semantic／run owner | `TypeError` |
| runtime successだがsemantic decision無し | `ValueError` |
| runtime failureにsemantic decisionを付与 | `ValueError` |
| 別exchangeのcandidate | `ValueError` |
| 別source seal／assets | `ValueError` |
| schema-validだがownerと異なるstatus/hash/prefix | validatorの`ValueError` |
| 未知のCore gate outcome/code | `ValueError` |
| interrupt | `ValueError("terminal interrupt is outside request-bound run-decision-v2")`相当 |
| request-independent owner | `TypeError`またはclosed branch無しの`ValueError` |

`ValueError`、`RuntimeError`、`MemoryError`、`AssertionError`など、owner validatorやCoreから上がった無関係なinternal errorを`payload_unavailable`へ丸めない。factoryは既知typed ownerの分岐以外をcatchしない。

---

## 9. 独立validator

### 9.1 signature

```python
from collections.abc import Mapping
from typing import Any

def validate_request_bound_run_decision_v2(
    value: Mapping[str, Any],
    owner: RetainedRequestBoundRunDecisionV2,
) -> None:
    """Recompute the run projection from retained owners without producer reuse."""
```

### 9.2 検証順序

1. `owner`がexact nominal typeであること。
2. `next-run-decision-v2` schema validation。
3. runtime resultとsemantic decisionのnominal type、same-object joins。
4. `ValidatedSemanticDecisionV2`なら`validate_semantic_decision_v2`。
5. `RejectedSemanticDecisionV2`なら`validate_rejected_semantic_decision_v2`。
6. runtime/Core ownerからkind、status、outcome、payload、exitを再導出。
7. provenanceを17 slotそれぞれについてownerから再計算。
8. contextのrequest ID、parent intent、depths、run context、config/source digestsを再計算。
9. 13-key fingerprintのavailabilityと値を再計算。
10. compatibility IDのavailabilityと値を再計算。
11. actual request bytesからdescriptorを再計算。
12. private retained response frameからresponse descriptorを再計算。
13. Core gate／rejectionからmeasurementを再計算。
14. `context.observed_prefix == provenance.observed`を照合。
15. unexpected extra field、private data、v1 identityを拒否。

### 9.3 共有してよいもの

- pinned canonical JSON codec
- SHA-256／`digest`
- JSON Schema loader
- unchanged path／target／source／semantic ID algorithms
- existing owner validators

### 9.4 呼んではならないもの

validatorから次を呼ばない。

- `retain_request_bound_run_decision_v2`
- `project_request_bound_run_decision_v2`
- producer側expected-record builder
- `runtime_provenance_v2`
- `runtime_provenance_values_v2`
- `project_public_semantic_document_v2`
- producer側13-key preimage helper

現行`validate_runtime_provenance_v2`はproducer側`runtime_provenance_values_v2`をimportしているため、本スライスでvalidator-localなowner再計算へ変更する。17 valuesをvalidator module内のprivate helperで独立に綴り、producer側helperとは共有しない。既存schema-valid rehashがowner証拠にならない性質を維持する。

独立性testではproducer／projection／producer provenance helpersをmonkeypatchして例外を投げさせても、固定literalに対するvalidatorがpassすることを確認する。

---

## 10. test matrix

### 10.1 positive branches

| case | 特に確認する点 |
|---|---|
| complete | success、status complete、exit 0、17 observed、entity measurement |
| partial_safe | success、status incomplete、payload true、exit 3 |
| complete-empty | actual=0、空成功がsource/Core proof無しで作れない |
| target unavailable | failure、fingerprint/compatibilityあり、measurement null |
| export unavailable | failure、fingerprint/compatibilityあり、measurement null |
| entity +1 | failure、entity actual/limit |
| Core invariant invalid | failure、fingerprintあり、compatibility null、semantic suffix無し |
| model record 10,001 | model-record measurement、entity budgetと混同しない |
| unsupported runtime | response descriptorあり得るがfingerprint null |
| protocol/bootstrap/semantic child failure | actual control prefix、candidate無し |
| stage/spawn failure | process/version/response無し |
| write/read failure | request/process prefixだけ |
| stdout/stderr cap +1 | LIMIT-003、response null |
| timeout | NODE-003、version/control補完無し |
| decoder raw/decode/schema failure | response null、private rejected body非公開 |
| binding mismatch | foreign bindingを保持、親requestへ修正しない |
| echo invalid | control prefixのみ、semantic admission無し |
| exit mismatch | actual control/exit mismatch |
| cleanup unverified |既観測version/controlを消さず、candidate無し |
| candidate/assets drift | late prefixを保持、fingerprint null |

### 10.2 negative branches

最低限、次を個別mutation testにする。

- `kind`、`status`、`outcome`、`payload_available`、`exit_code`
- request-independent kind／not-applicable／interrupt
- provenance stage/codeの自由なcross product
- 17 slotそれぞれのstate/hash置換
- v1 provenance schema、version 1 observation、旧9-slot map
- `context.request_id`
- run context selector／formats／budget
- targets／upstream depth／downstream depth
- config/source plan/source view digest
- run fingerprintの各13 preimage field
- compatibility ID
- request raw hash／length／canonical flag
- response raw hash／length／canonical flag
- response null／nonnullの不正置換
- entity／model-record measurementのkind、actual、limit
- schema-validに再hashしたforeign record
- same-contentだが別runtime/Core owner
- free constructor／duck owner
- raw body、proof、base64、PID、cwd、absolute path、spawn parametersの追加
- `CSV-NEXT-ASSET-*`の追加
- valid Core dataのrejection化
- invalid Core dataのsuccess化
- unrelated internal exceptionのcatalog failure化

---

## 11. known vectors

### 維持する既存vector

- available public run fingerprint
  `066d76ba2cfbae97b137a7a1bd59a4181dee2c0ccf31f5c013a9a1735dc8c56e`
- retained public semantic bytes
  `9472` bytes、LF込みSHA-256
  `545389abfa3975b2c95083db9cca6b8efbe071c4526b90cbe55fe9bdc84b5957`
- provenance `node_candidate` observation
  `49629589791b75238da6a7744ddb40b19386eb9482a8e05a90a2bf2717870def`
- provenance `process_start` observation
  `3869aabc86551c31c55fca1229360dc3efe591ab6449bb33dc465a3b8bf6b5d4`

9472-byte vectorと既存のfocused/related gatesは直前スライスの証拠であり、このrun2候補の全suite passとして再ラベルしない。

### 新literal

1. `run-decision-complete.json`
   - existing public semantic known corpusと同じ13-key input
   - fingerprintは上記`066d...`
   - noncanonical retained responseを使い、`response.canonical_json=false`
   - full 17-slot observed prefix
   - entity measurement

2. `run-decision-pre-spawn-failure.json`
   - fingerprint／compatibility／response／measurementはnull
   - request、policyまでの実prefixだけobserved
   - `node_spawn / CSV-NEXT-NODE-002`

3. `run-decision-core-rejected.json`
   - complete transportとmatching rejected Core owner
   - fingerprintは同じ13-key inputなら`066d...`
   - compatibility null
   - response descriptorあり
   - semantic/compatibility/model/budget observationsはunobserved

literalはproducerから生成しない。test-sideで明示recordを作り、ASCII corpusについて独立に次を実施する。

```bash
jq -cS . tests/fixtures/next_runtime_v2/run-decision-complete.json \
  | tr -d '\n' \
  | shasum -a 256
```

新run recordのfull SHAは実装前に推測しない。独立計算した値をtest、contract doc、SpecDock Artifactの三箇所へ固定し、自動fixture updaterを作らない。

---

## 12. vertical Red–Green順序

### Stage 0 — 基準とEvidenceの確立

- clean tree、current branch、`HEAD=9b5e...`を確認。
- repository instructionsとSpecDock root help、Artifact作成leaf helpを直前に読む。
- SpecDockの`new artifact`経路で`A02 request-bound run-decision-v2 contract slice`のdisc/evidence Artifactを作る。
- CLIが返した実pathを保持し、空scaffoldのまま放置しない。

SpecDockではcommand-firstでArtifactを作成し、metadataやgenerated projectionを手編集しない。mutation後はsync／validateでpost-stateを検証する。

### Stage 1 — Schema RED

先に`test_next_run_decision_v2.py`へ次を追加し、schema欠落でREDにする。

- three branch matrix
- exact provenance-v2 ref
- 17-slot observed prefix
- request-independent／private fields拒否
- response `canonical_json=false`受入れ
- old-v1 refs不存在

最小の`next-run-decision-v2.schema.json`を追加しGREENにする。

### Stage 2 — Runtime owner RED/GREEN

- child／late failureでcomplete response frameを独立検証できないtestをREDにする。
- `RetainedRuntimeResultV2`へprivate frame ownerを追加。
- descriptorと元frameのhash／length／canonical flag一致を既存runtime testsへ追加。
- failure semantic payloadをpublic authorityとして扱わないことを確認。

### Stage 3 — Nominal run owner RED/GREEN

- direct constructor拒否
- runtime success without Core owner拒否
- failure with Core owner拒否
- same-content別exchange拒否
- interrupt拒否

その後、owner、factory、projectionの最小実装を追加する。

### Stage 4 — Outcome matrix RED/GREEN

complete → partial-safe → complete-empty → Core unavailable → Core rejection → runtime failuresの順に一branchずつ追加する。一度に全branchを大きなif-chainへ書かない。

各verticalで、producerの出力だけでなく、owner mismatchと一つ以上のmutation拒否を同時にGREENへする。

### Stage 5 — Independent validator RED/GREEN

- producerをmonkeypatchしてもvalidatorがliteralを検証できるtestを先にRED。
- `validate_runtime_provenance_v2`からproducer-side values helper依存を除去。
- run validatorがschema、branch、17 observations、context、descriptors、fingerprint、measurementを別々に再計算。
- expected full record dictを組み立てて単純比較する方式は使わない。

### Stage 6 — KATとprivacy hardening

- 三つのliteral fixture。
- jq/shasumによる独立hash。
- raw body、proof、base64、host-local dataの漏洩拒否。
- existing `066d...`、9472 bytes／`545389...`が不変であることを再確認。

### Stage 7 — Docs／Plan／Report／Artifact

- `docs/contracts/next-run-decision-v2.md`へ実装済みbranchだけを記述。
- `next-provenance-v2.md`へrun2 joinを追記。
- PlanはA02-3の「request-bound run-decision-v2 reference slice GREEN」の限定進捗のみ。
- Reportは実際に実行したcommands、pass数、hash、未実行gateを記録。
- ArtifactへRED、GREEN、hardening failures、最終commands、checkpoint SHAを保存。
- Requirement／Designを変更しない。

---

## 13. verification gates

### focused

```bash
uv run --group dev pytest -q \
  tests/contracts/test_next_run_decision_v2.py
```

### adjacent runtime/Core/public/schema

```bash
uv run --group dev pytest -q \
  tests/contracts/test_next_run_decision_v2.py \
  tests/contracts/test_next_runtime_result_v2.py \
  tests/contracts/test_next_provenance_v2.py \
  tests/contracts/test_next_core_failure_v2.py \
  tests/contracts/test_next_semantic_candidate_v2.py \
  tests/contracts/test_next_exchange_v2.py \
  tests/contracts/test_next_rejected_frame_v2.py \
  tests/contracts/test_next_analysis_context_v2.py \
  tests/contracts/test_next_public_semantic_v2.py \
  tests/contracts/test_next_public_artifact_v2.py \
  tests/contracts/test_json_schemas.py
```

### 既存domain不変性

```bash
uv run --group dev pytest -q \
  tests/contracts/test_python_goldens.py \
  tests/contracts/test_sqlalchemy_goldens.py
```

### Current authority pointer

```bash
uv run --group dev pytest -q \
  tests/contracts/test_next_contracts.py::test_round23_rg_18_current_schema_and_history_contract_are_explicit
```

### static／docs

```bash
uv run --group dev ruff check .
uv run --group dev ruff format --check .
uv run --group dev mypy src tests
./spec-dock/scripts/spec-dock sync --no-github --no-update-active
./spec-dock/scripts/spec-dock validate
git diff --check
```

実装開始時の既知baselineは、focused 26、related 243、doc-pointer 1、Ruff 212 files、mypy 176 files、SpecDock 10 nodes。これは9b5のretained semantic bytesスライスの証拠であり、新run2変更後の結果ではない。新しい実測数をReportへ記録し、baselineと合算しない。earlier `700d...`のbounded 1316も本candidateのwhole-suite結果として扱わない。IssueとA02は未完了である。

全pytest、全A02 gate、actual OS/TS gateはこのcheckpointの必須出口にはしない。ただし「実行していない」とReport／Artifactへ明記し、後続whole-A02 gateに残す。

---

## 14. staging、commit、push

全編集は`apply_patch`で行う。heredocによる大量上書き、advisory由来のshell write tricks、alternate index、hook bypass、force、fetch/rebaseを使わない。

SpecDock Artifactの実pathが確定した後、wildcardを使わず少なくとも次を明示stageする。

```bash
git add \
  schemas/next-run-decision-v2.schema.json \
  docs/contracts/next-run-decision-v2.md \
  docs/contracts/next-provenance-v2.md \
  tests/contracts/next_run_decision_v2_reference.py \
  tests/contracts/next_run_decision_v2_validation.py \
  tests/contracts/test_next_run_decision_v2.py \
  tests/contracts/next_runtime_v2_reference.py \
  tests/contracts/next_runtime_v2_validation.py \
  tests/contracts/test_next_runtime_result_v2.py \
  tests/contracts/test_next_provenance_v2.py \
  tests/contracts/test_json_schemas.py \
  tests/fixtures/next_runtime_v2/run-decision-complete.json \
  tests/fixtures/next_runtime_v2/run-decision-pre-spawn-failure.json \
  tests/fixtures/next_runtime_v2/run-decision-core-rejected.json \
  spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00008-generate-nextjs-component-snapshots/plan.md \
  spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00008-generate-nextjs-component-snapshots/report.md \
  <specdock-cliが返した実artifact-path>
```

続けて:

```bash
git status --short
git diff --cached --check
git diff --cached --stat
commit-codex -a
git push
git status --short
git rev-parse HEAD
git rev-parse '@{upstream}'
```

確認事項:

- unrelated pathがstageされていない。
- ignored Workbench promptをstageしていない。
- `src/`、old schema、catalog、`pyproject.toml`、`uv.lock`に差分がない。
- push後のlocal HEADとupstreamが同じ40桁SHA。
- 新SHAをArtifactとReportへ記録。
- このcommitを「A02 complete」「A03 pass」「production accepted」と表記しない。

---

## 15. 完了条件と停止境界

このスライスは、次がすべて成立した時点で完了とする。

1. request-bound success/failureだけを持つrun2 schemaがclosedである。
2. complete、partial-safe、complete-empty、Core unavailable、Core rejection、全通常runtime failureをownerから投影できる。
3. outcome、status、exit、stage、code、context、17 observationsにfree inputがない。
4. response descriptorを実frame bytesから独立再計算でき、noncanonical JSONをfalseとして保持する。
5. 13-key fingerprintの非null条件がactual transport candidate／runtime bindingに閉じ、pre-Core failureではnullである。
6. Core entity／model-record measurementを混同しない。
7. validatorがproducer、projection、producer provenance helperなしで通る。
8. literal fixturesと独立hashが固定される。
9. focused、adjacent、old-domain、static、SpecDock、diff checksがpassする。
10. ordinary commit/push後のfull SHAが記録される。

ここで停止する。reader-owned prefix、ASSET policy、publication/domain/root/stdout closure、full A02 gateが残るため、A03を開始しない。A03は基点 `f4159066f3954454ad2f0c2701fa54bf1bc7bc4a` から最終的な全A02 clean/pushed candidateを対象にした独立cumulative Strict reviewであり、`P0=0 / P1=0 / review_status=pass`が必要である。その後でのみA04 production verticalが認可される。

**検証済み基準: `chemitaro/code-structure-viz` / `iss-00008-generate-nextjs-component-snapshots` / `9b5e0d0fee6f30967dcc296d0f75a1588e56842d`。これは実装ブリーフであり、独立A03レビュー、production受入れ、A04/A05認定とは分離される。**
