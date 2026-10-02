# Issue #8 SI-04 selected-cardinality no-payload Core reference 実装ブリーフ

## 1. 固定点と結論

GitHub connector で次を再検証済みです。

| 項目 | 検証値 |
|---|---|
| repository | `chemitaro/code-structure-viz` |
| target branch | `iss-00008-generate-nextjs-component-snapshots` |
| expected SHA | `4b50c815c4875696b04df8f14a8f681ba0c52566` |
| current full tip | `4b50c815c4875696b04df8f14a8f681ba0c52566` |
| SHA comparison | exact match |
| original SI-04 review base | `caf38329826ae34f8e3cb330b83b97e0357b7dc5` |

repository root の `AGENTS.md` は current commit に存在せず、root listing でも不在です。repository-local command instruction として `.agents/skills/spec-dock/SKILL.md` を確認済みです。

この checkpoint から残る selected-cardinality seam は、**Current authority を変更せず実装可能**です。新しい Product / Security 判断は不要です。

実装の中心は、normal `ValidatedTransportCandidateV2` を偽造・差し替えず、current candidate の retained bytes から **validation-only view** を内部生成し、`missing` / `component_only` / byte-identical `duplicate` に必要な限定例外だけをその view に適用することです。

通常の `full_module_owners_v3()`、`resolve_discovered_v3()`、`retain_source_inventory_seam_v3()` は変更しません。

成果物は authoritative plan の一選択単位を current code へ具体化する companion であり、要件・設計・計画を変更せず、具体的 target と observable completion evidence を明示する必要があります。:chatgpt-content-reference{index="0"}

caller-visible implementer target は **GPT-6.1 Sol / Max** です。runtime model identity の独立検証済み事実としては扱いません。

---

## 2. authoritative boundary

正本は次です。

```text
spec-dock/.../iss-00008-generate-nextjs-component-snapshots/requirement.md
spec-dock/.../iss-00008-generate-nextjs-component-snapshots/design.md
spec-dock/.../iss-00008-generate-nextjs-component-snapshots/plan.md

artifacts/20261002t001435z-adr-issue8-source-inventory-safe-subset.md
artifacts/20261002t041350z-adr-issue8-owner-closed-file-module-publication.md

docs/contracts/next-semantic-admission-v3.md
docs/contracts/next-semantic-v3.md
docs/contracts/next-compatibility-v3.md
```

`requirement.md` / `design.md` / `plan.md` は `Current normative authority` とその Current SI section だけを authority とします。後続 Round sections は historical evidence です。

Current authority から今回固定する不変条件は以下です。

- 全取得 Project/File は same seal/request が所有する。
- Project/File proof row は `record` key を省略する。
- normal available program File は canonical Module exactly one。
- Module 欠落/重複を child model absence で合法化しない。
- selected cardinality 例外は **完全 proof 後の typed TARGET-001/no-payload 専用**。
- selected 例外を available owner-closed partition へ転用しない。
- File mandatory seed、causal、typed taint、locality、export/target witness は維持する。
- reverse Module→File taint、File→Project taintを追加しない。
- proof-only refs は D、public refs は M に閉じる。
- invalid proof は target/budget failure より先に拒否する。
- target failure は model/entity budget stage へ進まない。
- compatibility-v3 は same candidate の parent-owned ten-key preimage。
- public SI-05 schema/consumer は今回作らない。

---

## 3. current checkpoint の確認結果

current `4b50c815...` は original base `caf3832...` より 2 commits ahead です。

SI-04 の product/reference code として追加済みなのは:

```text
tests/contracts/next_semantic_core_v3_reference.py
tests/contracts/next_semantic_core_v3_validation.py
tests/contracts/test_next_semantic_core_v3.py
```

evidence/status として:

```text
artifacts/20261002t121923z--si04-full-core.md
artifacts/20261002t121923z-01--si04-full-core-corrected.md
artifacts/20261002t121924z--si04-brief-literal-probe.py
artifacts/20261002t121924z-01--si04-brief-literal-probe.txt
artifacts/20261002t121924z-02-disc-si04-full-core-brief-adoption.md
artifacts/20261002t135356z-disc-si04-core-intermediate-reference-evidence.md
plan.md
report.md
```

が存在します。

current evidence Artifact 自身も、この checkpoint が SI-04 pass ではなく、残件が dedicated selected cardinality path であることを明示しています。

---

## 4. current code の具体的な blocker

`tests/contracts/next_semantic_core_v3_validation.py::_validate_semantic_candidate_v3()` の current order は概略:

```text
lower-owner validation
→ source record / metadata
→ full_module_owners_v3(candidate)
→ full model
→ taint/proof
→ export
→ locality
→ target
→ retain_source_inventory_seam_v3(...)
→ TARGET gate
→ record budget
→ export/source gate
→ entity gate
```

です。

したがって selected File の Module が:

```text
missing
component_only
duplicate
```

の場合、`full_module_owners_v3()` が target routing より前に正常に拒否します。

これは normal path では正しい挙動です。

修正すべきなのは normal guard ではなく、**その三状態だけを識別した別 validation route** です。

---

# 5. 実装方針: nominal candidate と validation-only view を分離する

`ValidatedTransportCandidateV2` の fake instance、duck object、内容差し替えは作りません。

新たに `next_semantic_core_v3_validation.py` 内部だけで使用する view を設けます。

proposed internal types:

```python
@dataclass(frozen=True, slots=True)
class SelectedCardinalityContextV3:
    failure: NextTargetCompletenessFailure
    missing_module_keys: frozenset[tuple[str, str]]
    component_only_module_ids: frozenset[str]
    duplicate_module_keys: frozenset[tuple[str, str]]


@dataclass(frozen=True, slots=True)
class CoreValidationViewV3:
    request: dict[str, Any]
    raw_model: dict[str, Any]
    validation_model: dict[str, Any]
    proof: dict[str, Any]
    resolved: dict[str, dict[str, Any]]
    cardinality: SelectedCardinalityContextV3 | None
```

これらは retained owner / certificate ではありません。

authority は常に:

```text
candidate
seal
assets
```

です。

view は getter から得た fresh data の検証用 projection に限定します。

---

## 6. 新規/変更 symbol

`tests/contracts/next_semantic_core_v3_validation.py` に proposed:

```python
CARDINALITY_TARGET_REASONS_V3 = frozenset(
    {"missing", "component_only", "duplicate"}
)

def selected_cardinality_context_v3(
    candidate: ValidatedTransportCandidateV2,
) -> SelectedCardinalityContextV3 | None: ...

def resolve_selected_exception_view_v3(
    candidate: ValidatedTransportCandidateV2,
    context: SelectedCardinalityContextV3,
) -> CoreValidationViewV3: ...

def validate_selected_exception_references_v3(
    view: CoreValidationViewV3,
) -> None: ...

def validate_selected_exception_source_projection_v3(
    view: CoreValidationViewV3,
) -> None: ...

def validate_selected_exception_export_v3(
    view: CoreValidationViewV3,
    seal: SourceAcquisitionSeal,
) -> None: ...

def validate_selected_exception_target_proof_v3(
    view: CoreValidationViewV3,
    seal: SourceAcquisitionSeal,
) -> NextTargetCompletenessFailure: ...

def validate_selected_cardinality_exception_v3(
    candidate: ValidatedTransportCandidateV2,
    seal: SourceAcquisitionSeal,
    assets: RetainedExecutionAssets,
    context: SelectedCardinalityContextV3,
) -> CoreValidationResultV3: ...
```

加えて current candidate-oriented validators のロジックを小さい internal pure helper へ factor します。

例:

```python
def _validate_full_taint_proof_for_view_v3(view: CoreValidationViewV3) -> None: ...
def _validate_proof_coverage_for_view_v3(view: CoreValidationViewV3) -> None: ...
def _validate_full_model_for_view_v3(view: CoreValidationViewV3) -> None: ...
def _derive_locality_for_view_v3(
    view: CoreValidationViewV3,
    seal: SourceAcquisitionSeal,
) -> dict[str, Any]: ...
```

normal wrapper は current behavior を維持してこれらへ delegation します。

旧 `_validate_target_exception_proof_base()` は呼びません。

---

# 7. exception detection は source-safe view からではなく full source selection で行う

selected cardinality を raw public source omissionから導出してはいけません。

まず classification 用 model を作ります。

```text
classification Projects = request-derived acquired Projects
classification Files    = request-derived acquired Files
classification semantic arrays = raw candidate semantic arrays
```

Project/File は `content_base64` を除く parent-derived records です。

その model へ existing:

```python
target_completeness_failure(...)
```

を適用します。

これにより File 自体を child が model から消しても:

```text
Module missing
```

を File missing に誤分類しません。

---

## 8. narrow exception set

existing generic helpers:

```python
_target_missing_module_exceptions(...)
_target_duplicate_module_exceptions(...)
```

をそのまま使います。

これらが返す set だけを許可します。

意味は:

```text
missing:
selected program File の expected Module が full semantic baseに存在しない

component_only:
expected Module は存在しないが、
expected Module ID を module_id とする Component が残る

duplicate:
selected program File に同project/pathの
byte-identical Module row が raw model上で複数ある
```

です。

non-selected missing/duplicate は exception set に入りません。

---

# 9. implicit/default selection

existing `target_completeness_failure()` は `targets=[]` の場合:

```text
all program Files
```

を implicit selected set とします。

Current v3 は「existing selected cardinality exception」を維持するとしているため、SI-04 内で explicit-only の新 classifier を作りません。

したがって:

```text
request.targets == []
```

でも program File の missing/component_only/duplicate があれば、既存 helper semantics に従い `path:<file>` の typed target failure になり得ます。

この behavior を一件 regression として固定します。

---

# 10. missing と tainted を混同しない

exception detection は **full semantic D の欠落**を見ます。

次は `missing` ではありません。

```text
Module が public M に無い
しかし full D には proof-only Module として存在する
```

この場合 Module は missing ではなく、taint/selection/unavailable record です。

normal proof/target resolution へ進めます。

特に:

```text
Module exists in D + tainted
```

を child/public model absenceだけ見て `missing` に再分類してはいけません。

同様に File taintを消して clean missing caseへ変換しません。

---

# 11. exceptional resolved D

normal `resolve_discovered_v3()` は duplicate raw modelを `_validate_model_collections()` で拒否するため、exception branch では直接使いません。

ただしその ownership semantics は維持します。

`resolve_selected_exception_view_v3()` は次を行います。

### Project/File

proof row:

```text
record key absent
```

を要求し、same requestから parent record を再構成します。

全 acquired Project/File ID が exactly once 必須です。

### normal semantic records

validation model に同じ ID がある場合:

```text
record key absent
```

で join。

proof-only の場合:

```text
record object required
```

で ID/preimage を再計算。

### global discovery

```text
one global record ID
one collection
one discovery row
canonical order
```

を要求します。

duplicate target の duplicate Module raw rowsを、duplicate discovery rowsへ変換してはいけません。

---

# 12. raw model と validation model を分ける

exception branch では二つを明示的に分離します。

### raw model

実際の child model。

model digest はこれに対して検証します。

duplicate case なら duplicate Module を **二行**保持します。

### validation model

full semantic grammarを適用するための private copy。

変更を許すのは:

```text
selected byte-identical duplicate Moduleの余分なraw rowをcollapse
```

だけです。

missing/component_only では Module を補いません。

validation model を candidate に書き戻しません。

---

# 13. duplicate count の扱い

byte-identical duplicate case は最重要です。

current normal corpus は 17 model records です。

duplicate fixture は Button Module の同一rowを raw model に一件追加するため:

```text
raw model records = 18
unique D records  = 17
```

とします。

必須:

```text
raw coverage.counts.modules
  = raw model module array length = 4

raw coverage.counts.published
  = raw seven collections = 18

proof discovery
  = globally unique 17 records
```

duplicate Module を proof discovery に二回入れて count を合わせるのは禁止です。

validation-only model では duplicate rowを一件へ collapse し、generic semantic validator に渡す counts だけを validation view の実数へ作り直します。

その値を raw candidateへ書き戻しません。

target failure は stage 4 で終わるため:

```text
measurements.model_records = null
measurements.entity_budget = null
```

です。

18 を model-record budgetの actual として後段へ流しません。

---

# 14. contradictory duplicate

`_target_duplicate_module_exceptions()` が許可するのは canonical bytes が全て identical な場合だけです。

例:

```text
duplicate[0].client_entry = false
duplicate[1].client_entry = true
```

は同じ Module identity/key でも exception ではありません。

結果:

```text
PROTOCOL-001
model_proof または proof_module_owner
```

で閉じます。

TARGET-001 にしてはいけません。

---

# 15. full model grammar

exception validation model は existing:

```python
validate_model(
    model,
    max_model_records=<structural wide cap>,
    allowed_missing_module_keys=...,
    allowed_missing_module_ids=...,
)
```

を利用します。

### missing

```text
allowed_missing_module_keys
  = selected missing File keys

allowed_missing_module_ids
  = empty
```

したがって Component が expected missing Module ID を参照すれば拒否です。

### component_only

```text
allowed_missing_module_keys
  = selected component_only File keys

allowed_missing_module_ids
  = exact expected Module IDs
```

この ID exemption は **Component.module_id ownership joinだけ**です。

PropsTypeIR の repository reference、Fact owner、Member owner、Relation source/target の dangling Module exemptionにはしません。

---

# 16. component_only の private Props negative

component_only fixture へ orphan Button Componentを残した上で、例えば Prop:

```text
owner_id = BUTTON_ID
type_node =
  reference(
    scope="repository",
    module=<missing Button Module ID>,
    exported_name="Props"
  )
```

を追加した case は拒否します。

理由:

```text
Component.module_id missing exception
≠
arbitrary Props repository reference exception
```

です。

これは private D reference closure / Props semantics が TARGET-001 に隠れないことの証拠にします。

---

# 17. disposition と unrelated source projection

exception branch は normal source seam を作りません。

ただし selected exceptional File 以外については current owner-closed rulesを全て検証します。

`validate_selected_exception_source_projection_v3()` は:

- 全 acquired Project/File discovery を確認。
- Project/File parent metadataを確認。
- exceptional File以外のprogram Fileは canonical Module exactly one。
- nonprogram File rulesを維持。
- unrelated Module taint/selectionから File dispositionを導出。
- unrelated safe Fileの任意省略を拒否。
- unrelated excluded/failed File reasonを exact compare。
- Project metadata/membershipの unrelated subsetを exact compare。
- cross-project ownershipを拒否。

selected exceptional File/Module は normal `F_safe` certificateに数えません。

ただし target classification のため raw candidate に source File row があっても、それは **available publication の証明ではありません**。

結果が no-payload なので `ValidatedSourceInventorySeamV3` は作りません。

---

# 18. exceptional File に新 disposition を作らない

次のような wire inventionは禁止です。

```text
excluded / module_missing
failed / missing_module
tainted / target_missing
```

新state/reason/codeは authority にありません。

exceptional Fileは retained request/D に存在したまま、target-only validation pathで扱います。

そのためこの branch は partition fingerprint / source inventory seam を生成しません。

---

# 19. source-bound export: Module が無くても source File を scan する

current normal export pipeline は full-D Modulesを起点に scan します。

exception branch は acquired program Fileごとの internal **source module slot** を作ります。

proposed:

```python
@dataclass(frozen=True, slots=True)
class SourceModuleSlotV3:
    file_id: str
    project_id: str
    path: str
    expected_module_id: str
    module: dict[str, Any] | None
    exception_reason: str | None
```

これは Module record ではありません。

D に挿入しません。

---

## 20. source slot の構築

全 acquired program Fileについて:

```text
expected_module_id =
recompute_record_id({
  kind: "module",
  project_id: file.project_id,
  path: file.path
})
```

を独立計算します。

normal:

```text
module = actual unique D Module
```

missing/component_only:

```text
module = None
```

duplicate:

```text
module = validation copyでdedupeしたactual Module
```

です。

---

# 21. same-seal bytes

slot の source bytes は必ず:

```python
seal.source_view.files[*].content
```

から取得します。

request の:

```text
path
size_bytes
sha256
content_base64
```

との same-owner join を維持します。

caller bytes、old export fixture、filesystem rereadを使いません。

---

# 22. ownerless selected source の syntax census

missing/component_only の Fileでも:

```python
_scan_export_file(path, same_seal_bytes)
```

を実行します。

したがって selected File の source syntaxを「Moduleが無いから scanしない」とはしません。

ただし semantic Module owner が存在しないため:

```text
proof.export_observations
```

へ fake `owner_module_id` を作りません。

expected missing Module IDを observation ownerとして捏造するのは禁止です。

この source syntax は exception validator 内部の source-only evidence です。

---

# 23. source-only direct declaration table

`recompute_export_graph_case()` 用 direct table は source slot 単位で作れます。

Module無しslotの direct declaration は:

```text
type syntax
  → type

positive primitive const bytes
  → value

その他 value declaration
  → unknown
```

です。

特に:

```text
export function Button() { ... }
```

で Module が missing/component_only の場合、orphan Component を使って `component` success にしません。

結果:

```text
Button -> unknown
```

です。

Component-only Component は Module の代替ではありません。

---

# 24. missing source を old fixed export facadeへ落とさない

次は使用禁止です。

```text
_export_census_for_model
_export_syntax_rows_for_model
_reexport_graph_index
expected_export_observations
validate_export_observations
expected_export_reexport_witness
```

current v3-local source-bound primitivesを、validation view/slotから再利用します。

---

# 25. missing/component_only の re-export worked result

current actual source:

```text
src/index.ts:
export { Button as Primary } from "./button";
```

current independent literal:

```text
syntax_identity =
export:src/index.ts:9:26:reexport:Primary

token_identity =
0629e28100820ed2c813333c1cb6ee468df1cbe8342568cf400c347d27bc7317
```

Button Module が missing/component_only でも physical source:

```text
src/button.tsx
```

は acquired されています。

source-only tableを graph case に含めるため、re-export graph は physical source pathを見失いません。

ただし semantic Module ownerはありません。

expected semantic witness:

```text
owner_module_id = src/index.ts の actual Module ID
resolved_source_module_id = null
expanded_exported_name = "Button"
target_declaration_id = null
resolution = "unknown"
diagnostic = null
```

public `Primary` ExportBinding はありません。

orphan Button Component が component_only case に残っていても、これを re-export successへ使用しません。

---

# 26. ownerless source 自身の observation

missing Button sourceの direct:

```text
export function Button() { return null; }
```

は internal census では確認します。

しかし Module ownerが無いため、proofへ:

```text
owner_module_id = expected missing Module ID
```

の observationを要求・許可しません。

もし child がその fake owner observationを出せば dangling private ref として拒否します。

これは source syntaxを skipすることと異なります。

---

# 27. duplicate export behavior

duplicate case では validation view に canonical Module一件が存在します。

したがって export evidence は normal 17-record corpusと同じ一回だけです。

duplicate raw Module rowの数に合わせて:

```text
Button export observation ×2
```

を作ってはいけません。

同様に:

```text
export reexport witness
export resolution witness
ExportBinding
```

も重複させません。

physical source syntaxは一ファイル一回です。

---

# 28. target proof

exception target rowsは structural classifier と full proof の両方を通した後に比較します。

例:

```json
{
  "target_key": "path:src/button.tsx",
  "status": "failed",
  "record_ids": [],
  "reason": "missing"
}
```

component_only / duplicate も reasonだけ変更します。

coverage:

```json
{
  "target_key": "path:src/button.tsx",
  "status": "failed",
  "record_ids": [],
  "reason": "missing"
}
```

と exact-equal。

extra target row、wrong reason、resolved IDs付きfailureを拒否します。

---

# 29. mixed targets

requestに複数targetがある場合:

- cardinality failure targetは failed row。
- その他 targetは validation viewから通常解決。
- unrelated safe targetを勝手に消さない。
-一 targetでも failureなら final gateは TARGET-001/no-payload。

submitted proof row 全体を canonical exact compareします。

---

# 30. result owner

exceptional validation success は:

```text
ValidatedSemanticDecisionV3
```

です。

rejection ownerではありません。

その gate:

```text
diagnostic_code = CSV-NEXT-TARGET-001
outcome = payload_unavailable
payload_available = false
allowed = false
actual = null
artifact_paths = []
target_failures = exact rows
```

を持ちます。

同じ real:

```text
candidate
seal
assets
```

を保持します。

compatibility-v3 も normal decision と同じ candidate から生成します。

---

# 31. `source_inventory_seam=None`

`CoreValidationResultV3` を:

```python
@dataclass(frozen=True, slots=True)
class CoreValidationResultV3:
    source_inventory: ValidatedSourceInventorySeamV3 | None
    gate: dict[str, Any]
    locality: dict[str, Any]
    measurements: dict[str, Any]
```

へ変更します。

`ValidatedSemanticDecisionV3._source_inventory` も:

```python
ValidatedSourceInventorySeamV3 | None
```

にします。

getter:

```python
def source_inventory_seam(
    self,
) -> ValidatedSourceInventorySeamV3 | None:
    ...
```

normal route は従来通り non-null。

selected-cardinality routeだけ `None`。

---

# 32. measurements

selected-cardinality route は target failureで stage 4 終了です。

必ず:

```json
{
  "model_records": null,
  "entity_budget": null
}
```

です。

duplicate raw modelの18 itemsを、TARGET-001後に model-record limit measurementへ変換しません。

---

# 33. locality

完全 proof と locality は TARGET routing より前に検証します。

`derive_post_acquisition_locality_v3()` の candidate-specific resolution部分を internal view helperへ factorし:

```python
_derive_locality_for_view_v3(view, seal)
```

を normal/exception両方で使用します。

pure cardinality fixture は failure roots 0 のため通常:

```text
localized = true
affected_paths = []
reverse_affected_paths = []
```

になります。

しかし compound source failureがある場合は actual same-seal graphを通常通り再導出します。

locality corruptionを TARGET-001 で隠しません。

---

# 34. normal path の ordering

normal path は現状を維持します。

```text
owner/echo
→ source rows
→ strict full_module_owners_v3
→ full proof/model/export/locality/target
→ retain_source_inventory_seam_v3
→ target
→ record budget
→ export/source unavailable
→ entity
```

exception pathだけ:

```text
owner/echo
→ source rows
→ cardinality classification
→ narrow exception set
→ validation-only full D/model
→ full proof/model/refs
→ source-bound export
→ coverage/locality
→ target proof
→ TARGET-001
```

とします。

---

# 35. branch selection pseudocode

`_validate_semantic_candidate_v3()` の冒頭を概念上:

```python
validate_lower_owner(...)
validate_source_record_payloads_v3(candidate)
validate_public_source_metadata_v3(candidate)

cardinality = selected_cardinality_context_v3(candidate)

if cardinality is not None:
    return validate_selected_cardinality_exception_v3(
        candidate,
        seal,
        assets,
        cardinality,
    )

return _validate_normal_semantic_candidate_v3(
    candidate,
    seal,
    assets,
)
```

の二 branch にします。

normal body は current code を極力移動するだけで意味変更しません。

---

# 36. independent decision revalidation

`validate_semantic_decision_v3()` は candidateから branchを再判定します。

expected result が:

```text
source_inventory is None
```

なら retained decision も `None` 必須。

normal expected が non-nullなら current:

```text
validate_source_inventory_seam_v3(...)
same candidate/seal/assets identity
```

をそのまま実行します。

exception decisionへ後から normal seamを差し込んでも拒否します。

compatibility descriptorは両branchとも独立再導出します。

---

# 37. worked actual-source fixture: missing

base:

```python
seal, assets, request, policy, wire = core_inputs_v3(
    tmp_path,
    targets=["path:src/button.tsx"],
)
```

actual selected source:

```text
src/button.tsx
SHA-256:
1dc7a2111f31e37e693b6b6befa5c7141411471168e20a2fc93c886382dfb862

expected Module ID:
next:module:4130a3bcc0554a01d2f7111d613cdf150e6e3104575fe6a46ee5b057c6414b7d
```

mutation:

```text
remove Button Module
remove Button router-context Fact
remove Button Component
remove Button/Primary ExportBindings
remove index→button semantic static_import Relation
```

source Fileは削除しません。

source bytesも変更しません。

full source censusは Button / index / value の実bytesを引き続きscanします。

expected model records:

```text
Project     1
Files       6
Modules     2
Components  0
Members     0
Relations   0
Facts       2
total       11
```

target:

```text
path:src/button.tsx -> missing
```

expected:

```text
TARGET-001
source_inventory_seam = None
model_records = null
entity_budget = null
```

---

# 38. worked actual-source fixture: component_only

同じ actual source/sealを使います。

mutation:

```text
remove Button Module
remove Button router-context Fact
keep Button Component
remove Button/Primary ExportBindings
remove index→button semantic static_import Relation
```

Button Component ID:

```text
next:component:56983cafa7d11d2d42ecdca27a9061799006d6154f77cb9e4ee2a954d95659e8
```

は expected missing Module IDを `module_id` に持ったままです。

expected model records:

```text
Project     1
Files       6
Modules     2
Components  1
Members     0
Relations   0
Facts       2
total       12
```

target:

```text
path:src/button.tsx -> component_only
```

orphan Component は target reasonの証拠にはなりますが、Moduleの代わりに export/public successを生成しません。

---

# 39. worked actual-source fixture: byte-identical duplicate

base 17-record corpusを維持します。

raw:

```python
wire["semantic_payload"]["model"]["modules"].append(
    deepcopy(button_module)
)
```

二 Module row は byte-identical。

proof discoveryは追加しません。

expected:

```text
raw model total = 18
unique D = 17

raw modules = 4
validation modules = 3
```

source export evidence:

```text
normal baseと同じ一セット
```

target:

```text
path:src/button.tsx -> duplicate
```

result:

```text
TARGET-001
source_inventory_seam = None
measurements = null/null
```

---

# 40. first TDD cycles

一 behavior ずつ進めます。

### Cycle 1 — missing

先に current behaviorを Red として観測します。

```bash
uv run --locked --group dev pytest \
  tests/contracts/test_next_semantic_core_v3.py::test_v3_core_selected_missing_module_routes_after_full_exception_proof \
  -q
```

current code が `full_module_owners_v3()` で target前に落ちることが intended Red です。

fixture/setup failure は Red に数えません。

minimum Green は missing branchだけです。

### Cycle 2 — component_only

```bash
uv run --locked --group dev pytest \
  tests/contracts/test_next_semantic_core_v3.py::test_v3_core_selected_component_only_routes_after_full_exception_proof \
  -q
```

minimum Green。

### Cycle 3 — duplicate

```bash
uv run --locked --group dev pytest \
  tests/contracts/test_next_semantic_core_v3.py::test_v3_core_selected_identical_duplicate_routes_without_duplicate_discovery \
  -q
```

minimum Green。

---

# 41. required compound negatives

three Green の後、一件ずつ Red→Green で追加します。

| Case | Expected |
|---|---|
| missing + unrelated dangling Relation | protocol invariant, not TARGET |
| missing + source proof row missing | protocol invariant |
| missing + fake Project/File metadata | protocol invariant |
| missing + source `record` payload | protocol invariant |
| missing + stale export witness | protocol invariant |
| component_only + Prop repo ref to missing Module | protocol invariant |
| component_only + unrelated dangling Fact | protocol invariant |
| component_only + wrong Component Module ID | protocol invariant |
| duplicate + contradictory duplicate bytes | protocol invariant |
| duplicate + duplicate discovery row | protocol invariant |
| duplicate + raw module count lies | protocol invariant |
| duplicate + unrelated Module missing | protocol invariant |
| any exception + extra causal edge | protocol invariant |
| any exception + missing mandatory edge/taint | protocol invariant |
| any exception + extra target proof row | protocol invariant |
| any exception + forged export owner/witness | protocol invariant |

TARGET-001 はこれらを隠しません。

---

# 42. missing-vs-tainted regression

追加:

```text
selected Button Module is absent from M
but exists in D as tainted/proof-only
```

case。

これは `missing` exceptionではありません。

normal full owner exists。

target unavailable reasonは validated taint/selection semanticsから導出します。

exception context の:

```text
missing_module_keys
component_only_module_ids
```

へ入ってはいけません。

---

# 43. implicit selection regression

`targets=[]` で Button Moduleを missing にした caseを一件追加します。

existing helper の default-selection semanticsどおり:

```text
path:src/button.tsx / missing
```

が classification failureとして導出されることを固定します。

新 explicit-only policy は作りません。

---

# 44. duplicate raw-vs-D regression

明示的に assert:

```python
assert len(raw_model["modules"]) == 4
assert unique_discovered_module_count == 3
```

とします。

さらに:

```text
proof discovered duplicate Module rowを追加
```

した case が拒否されることを確認します。

raw duplicateとproof duplicateを混同しません。

---

# 45. exceptional owner revalidation

exception decisionについて:

```python
decision = decide_semantic_candidate_v3(...)
assert decision.source_inventory_seam() is None
validate_semantic_decision_v3(decision)
```

を通す testを追加します。

その後 test-only mutationで:

```text
gate
locality
measurements
compatibility
source_inventory
```

のいずれかを偽装し、independent validatorが拒否することを一件ずつではなく、最小 representative set で確認します。

own-class mockや fake constructor は使いません。

---

# 46. current SI acceptance の残り

current exact sourceを確認した範囲では、`test_next_semantic_core_v3.py` に normal Core用として以下の surface は既に substantive tests が存在します。

```text
same-seal full positive
source-bound export omission/mutation
mandatory causal
private Props grammar
localized parse/read
open source dependency
selected File failure
actual record 10000/+1
unknown export
compatibility
owner revalidation
reverse importer
selection-only
complete-empty / nonprogram
all Files proof-only
entity500/+1
three nonFile roots
```

これは test source の存在確認であり、今回それらを実行して pass を認定したという意味ではありません。

current sourceから直接確認できる SI-04 の bounded gaps は:

```text
P03:
selected Module missing/component_only/duplicate専用Core path

N02:
duplicate raw Module と duplicate discovery の分離

N05:
cardinality + malformed mandatory root/causal/taint compound

N06:
selected exceptionで unrelated owner omissionを隠さない

N08:
component_only の narrow missing ownerと arbitrary private refを区別

N14:
cardinality route前にも locality/full-source evidenceが成立すること

N15:
missing/duplicate隠蔽、contradictory duplicate、orphan Component substitution拒否

owner:
source_inventory_seam=None の independent decision revalidation

selection:
targets=[] のexisting default selection behavior

export:
Module無しselected sourceをsame-seal bytesでscanし、
fake Module無しでfull source graph evidenceへ含める
```

これらを閉じた後に current normal matrix と required regression evidenceを一 candidateへまとめます。

---

# 47. focused unit verification

new unit:

```bash
uv run --locked --group dev pytest \
  tests/contracts/test_next_semantic_core_v3.py \
  -q
```

actual 10000/+1、entity500/+1を test selection から除外しません。

---

# 48. directly affected regressions

```bash
uv run --locked --group dev pytest \
  tests/contracts/test_next_source_inventory_v3.py \
  tests/contracts/test_next_semantic_candidate_v2.py \
  tests/contracts/test_next_core_failure_v2.py \
  tests/contracts/test_next_request_frame_v2.py \
  tests/contracts/test_next_exchange_v2.py \
  -q
```

selected-target generic algorithm:

```bash
uv run --locked --group dev pytest \
  tests/contracts/test_next_contracts.py \
  -q \
  -k 'program_file_requires_exactly_one_module_for_file_and_directory_targets \
      or round11_target_completeness_is_typed_and_projects_to_unavailable_run \
      or target_failure_validates_complete_proof_before_typed_routing \
      or response_base_rejects_invalid_cross_reference_before_target_failure \
      or response_base_rejects_invalid_cross_reference_before_duplicate_target_failure \
      or round17_proof_derived_target_failure_is_typed_and_sorted'
```

current old helper semanticsを回帰させるための selection です。

---

# 49. old goldens

```bash
uv run --locked --group dev pytest \
  tests/contracts/test_python_goldens.py \
  tests/contracts/test_sqlalchemy_goldens.py \
  -q
```

旧 bytes を更新して Green にしません。

---

# 50. static checks

```bash
uv run --locked --group dev ruff check .
uv run --locked --group dev ruff format --check .
uv run --locked --group dev mypy src tests
```

`pyproject.toml` / `uv.lock` 変更なしを確認します。

---

# 51. SpecDock

`.agents/skills/spec-dock/SKILL.md` の指示どおり、使用直前に current help を読みます。

```bash
python3 ./spec-dock/scripts/spec-dock --help
python3 ./spec-dock/scripts/spec-dock sync --help
python3 ./spec-dock/scripts/spec-dock validate --help
```

その後:

```bash
python3 ./spec-dock/scripts/spec-dock sync \
  --no-github \
  --no-update-active

python3 ./spec-dock/scripts/spec-dock validate

git diff --check
```

実装/TDD evidenceを Artifact として永続化する場合は current SpecDock commandで作成し、Plan/Reportには limited progress/statusだけを反映します。

Artifactは authority に昇格しません。

---

# 52. whole `tests/contracts` は SI-04 unit gate にしない

今回の SI-04 completion evidence は:

```text
focused new Core unit
direct affected regressions
selected generic algorithm regressions
old goldens
ruff
format
mypy
SpecDock
diff-check
```

です。

```bash
pytest tests/contracts
```

を今回の unit必須gateへ追加しません。

Current Plan上の broad all-contract/full gate は SI-07 / full A02 closure 側です。

demonstrated shared-helper risk が発生した場合のみ、その affected surfaceを追加します。

---

# 53. expected diff boundary

Core code は引き続き:

```text
tests/contracts/next_semantic_core_v3_reference.py
tests/contracts/next_semantic_core_v3_validation.py
tests/contracts/test_next_semantic_core_v3.py
```

の三ファイル内を優先します。

変更禁止:

```text
src/
schemas/
pyproject.toml
uv.lock
tests/contracts/next_source_inventory_v3_reference.py
tests/contracts/next_source_inventory_v3_validation.py
tests/contracts/next_reference_validation.py
old v1/v2 KAT/fixtures
Python/SQLAlchemy goldens
```

既存 generic helperを変更する必要が出た場合は、その必要性を先に再評価します。

---

# 54. stop conditions

次が必要になったら implementationを止めます。

```text
normal full_module_owners_v3 の緩和
normal resolve_discovered_v3 のduplicate許可
normal source seam のexception parameter
fake Module record
expected missing ModuleをDへ挿入
fake SourceAcquisitionSeal
legacy SourceFailureLedgerへのpost-acquisition failure注入
Module→File reverse taint
File→Project taint
新File disposition reason
新diagnostic code/state
child source metadata authority
proof source record payload
public proof-only ref
old export fixture facade fallback
empty export observations fallback
old KAT/schema/golden rewrite
production TypeScript/src変更
dependency/ASSET policy変更
SI-05 schema/public consumer追加
```

これらは current authority の機械的実装ではありません。

---

# 55. staging

checkpoint 前に:

```bash
git status --short
git branch --show-current
git rev-parse HEAD
git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}'
```

current branch/upstream が:

```text
iss-00008-generate-nextjs-component-snapshots
origin/iss-00008-generate-nextjs-component-snapshots
```

であることを確認します。

Core files は explicit pathだけ stage:

```bash
git add -- \
  tests/contracts/next_semantic_core_v3_reference.py \
  tests/contracts/next_semantic_core_v3_validation.py \
  tests/contracts/test_next_semantic_core_v3.py
```

SpecDock が返した authorized evidence/Plan/Report pathがある場合も、**返された具体pathだけ**別途 `git add --` します。

`git add .` / `git add -A` は使いません。

---

# 56. full staged diff

commit前に:

```bash
git diff --cached --check
git diff --cached --
git status --short
```

を実行し、`git diff --cached --` の全内容を読みます。

stat/name-onlyだけで commit しません。

---

# 57. commit / push

installed host contractどおり:

```bash
commit-codex -a
```

を使います。

generic manual commitへfallbackしません。

normal hooksを維持します。

push前に upstream を再確認した後:

```bash
git push origin \
  HEAD:refs/heads/iss-00008-generate-nextjs-component-snapshots
```

を使用します。

禁止:

```text
bare git push fallback
--force
--force-with-lease
history rewrite
new checkout
```

push後:

```bash
git rev-parse HEAD
git status --short
```

を確認します。

---

# 58. SI-04 Code Review Strict

selected seamだけを途中reviewへ出しません。

以下が **同じ clean pushed candidate** に揃ってから unit reviewを行います。

```text
normal Core evidence
selected missing/component_only/duplicate
compound negatives
owner revalidation
focused required checks
old affected regressions
old goldens
static checks
SpecDock/diff-check
```

review range は常に:

```text
base:
caf38329826ae34f8e3cb330b83b97e0357b7dc5

head:
final pushed SI-04 unit candidate
```

です。

current intermediate `4b50c815...` を新baseにしません。

review:

```text
fresh Code Review Strict
GPT-5.6 Sol
Extra High
```

だけを使用します。

reviewer は author と分離します。

subagentを使用しません。

Browser Use/CUAでreview job進捗を監視しません。

---

# 59. 完了条件

この remaining seam は、同一candidateで次が成立した場合に実装完了です。

1. normal `full_module_owners_v3()` が変更されていない。
2. normal `resolve_discovered_v3()` が変更されていない。
3. normal `retain_source_inventory_seam_v3()` が変更されていない。
4. missing selected Module が full proof後 TARGET-001。
5. component_only が full proof後 TARGET-001。
6. byte-identical duplicate が full proof後 TARGET-001。
7. contradictory duplicate は protocol invariant rejection。
8. non-selected missing/duplicate は exceptionにならない。
9. duplicate raw model rowは二件、D discoveryは一件。
10. duplicate discovery rowは拒否。
11. every acquired Project/File discoveryは same requestからexact once。
12. Project/File proof rowに `record` keyが無い。
13. fake source metadata/payloadはTARGET前に拒否。
14. exception validation modelは nominal candidateを偽造しない。
15. missing Moduleを synthetic recordとして補わない。
16. component_only の missing Module ID exemptionは Component ownershipだけ。
17. Props repository refへその exemptionを流用しない。
18. unrelated refsはD/M closureを満たす。
19. mandatory roots/causal/typed fixed pointをTARGET前に検証。
20. unrelated invalid causal/taint proofをTARGETで隠さない。
21. same-seal source bytesから selected missing Fileも export scanする。
22. missing owner用 fake export observationを作らない。
23. source-only export slotをre-export graphへ含める。
24. orphan Componentをexport successへ使用しない。
25. duplicate Moduleで export observationを重複させない。
26. stale/forged export witnessをTARGETで隠さない。
27. target proof/coverageは exact reason/order。
28. existing empty-target default selection semanticsを維持。
29. full-Dに実在するtainted Moduleを missing と誤分類しない。
30. unrelated source projection/owner cardinalityを維持。
31. exceptional branchで normal partition seamをmintしない。
32. `source_inventory_seam() is None`。
33. model-record measurementは null。
34. entity measurementは null。
35. compatibility-v3は same candidate由来で保持。
36. independent decision validatorが exception branchを再導出。
37. exception decisionへ seam/gate/compatibilityを差し替えると拒否。
38. current normal Core testsを壊さない。
39. SI-03/old v2 affected regressionsを壊さない。
40. old Python/SQLAlchemy goldensを変更しない。
41. `src/` / schema / deps / lock を変更しない。
42. focused pytest、ruff、format、mypy、SpecDock、diff-checkが candidate上で実行される。
43. full staged diff確認後 `commit-codex -a`。
44. verified current origin branchへ explicit non-force push。
45. original `caf3832` から final candidateへの fresh GPT-5.6 Sol/Extra High Code Review Strictが pass。

この完了は **SI-04 full Core reference unit** の認定までです。

以下は引き続き未認定です。

```text
SI-05 public/exact refs
SI-06 diagnostics/final publication
whole A02 / SI-07
cumulative A03
production TypeScript
OS/process
CLI
wheel/sdist/package
new ASSET policy
Issue #8 Final
```
