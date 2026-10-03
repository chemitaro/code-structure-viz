# Issue #8 SI-05 public/exact-ref reference/schema closure 実装ブリーフ

## 1. 固定点と結論

GitHub connector で次を直接確認済みです。

| 項目 | 固定値 |
|---|---|
| repository | `chemitaro/code-structure-viz` |
| branch | `iss-00008-generate-nextjs-component-snapshots` |
| verified branch tip / SI-05 original unit base | `2efb54c370ac05ac4da0d9b0bfe717a13b62380c` |
| SHA comparison | expected SHA と byte-for-byte 一致 |
| certified preceding SI-04 | `d6bbbcf337ee4008d5925a6294a9065ca167a0e2` |
| SI-05 review base | **常に `2efb54c370ac05ac4da0d9b0bfe717a13b62380c`** |

repository root の `AGENTS.md` はこの commit に存在せず、root listing でも不在です。`.agents/skills/spec-dock/SKILL.md` は確認済みで、SpecDock 操作は current CLI help を先に読み、canonical files / command result を authority とし、raw filesystem/GitHub fallback で guard を迂回しない契約です。

本 unit に material な仕様矛盾は見つかっていません。**SI-05 は ready-to-implement な reference/schema closure として進められます。**

添付 `brief.md` の役割どおり、以下は Current Requirement/Design/Plan を変更するものではなく、一つの selected milestone を current code へ実行可能な粒度で具体化する companion です。whole supplied specification と verified commit の code/tests に grounding し、実装境界・completion evidence・停止条件を分離します。:chatgpt-content-reference{index="0"}

caller-visible primary implementer は **GPT-6.1 Sol / Max** です。これは caller policy 上の作業設定であり、backend/model identity を本ブリーフが独立認証したという意味ではありません。

---

## 2. authority と selected scope

現在の authority は次です。

```text
spec-dock/initiatives/init-00001-code-structure-visualization/
  epics/epic-00002-safe-git-structure-comparison/
  issues/iss-00008-generate-nextjs-component-snapshots/
    requirement.md
    design.md
    plan.md
    artifacts/20261002t001435z-adr-issue8-source-inventory-safe-subset.md
    artifacts/20261002t041350z-adr-issue8-owner-closed-file-module-publication.md

docs/contracts/next-semantic-admission-v3.md
docs/contracts/next-semantic-v3.md
docs/contracts/next-compatibility-v3.md
```

`requirement.md` / `design.md` / `plan.md` は `Current normative authority` と Current SI section が正本です。`Round N` 等は historical evidence であり fallback authority にしません。

先行 evidence は次の意味に限定します。

- SI-01/02 specification gate: `bcae9548ef515e4a7662de1ad648171622c6a437`
- SI-03 source seam: `23072c288fc203071c10bfe3305e6ec5d3b055fe`
- SI-04 full Core: `d6bbbcf337ee4008d5925a6294a9065ca167a0e2`
- SI-04 certificate: `artifacts/20261003t010147z-03-disc-si04-cumulative-core-review-pass.md`

SI-04 certificate は Core107、旧5 modules278、shared52、schema/goldens139、static/docs checks、および original SI-04 base からの fresh cumulative Strict pass / P0=P1=0 を記録しています。残る ordinary-open-edge P2 は report-only availability risk であり、**SI-05 の remediation authority、backlog、test criterion、re-review trigger にしません。**

### Selected unit

Current Plan の **SI-05 public/exact refs** だけを実装します。

```text
Core-v3
  -> compatibility-v3
  -> public semantic-v3 / generic semantic-v3
  -> provenance-v3
  -> run-decision-v3
  -> publication-candidates-v3
  -> domain-manifest-v2
  -> publication-decision-v2
  -> run-manifest-v2
  -> stdout-result-v2
```

出口は Current Plan の記載どおりです。

```text
全ref/consumer census
source_inventory_summary の actual counts / partition / hash
compatibility ten-key literal
run fourteen-key literal
same-Core JSON + PlantUML
native numeric representation
foreign owner rejection
privacy closure
existing Python / SQLAlchemy bytes unchanged
```

---

## 3. 明示的な対象外

今回変更しません。

```text
src/**
actual TypeScript analyzer
OS process / Node launch implementation
CLI production wiring
package/wheel/sdist
pyproject.toml
uv.lock
old v1/v2 schema identity/KAT/goldens
SI-04 P2 ordinary-open-edge policy
unadopted ASSET failure policy
reader-prefix closure
SI-06 catalog diagnostic execution
SI-06 public stderr 64KiB execution
SI-06 product finalizer / executable final-owner completion
SI-07 all-A02 / cumulative A03
SI-08 production / Final
```

特に `next-publication-decision-v2` / `run-manifest-v2` / `stdout-result-v2` は **SI-05 で closed schema と recursive exact-ref contract を作る**必要がありますが、product の diagnostic/stderr/finalizer をここで実装しません。

これは silent deferral ではありません。Current Plan が SI-05 の exact-ref closure と SI-06 の diagnostic/stderr/final single publication owner executable completion を明示的に分けています。

---

# 4. Current Core owner をそのまま境界にする

現存する v3 Core API は次です。

`tests/contracts/next_semantic_core_v3_reference.py`:

```python
compatibility_descriptor_v3(
    candidate: ValidatedTransportCandidateV2,
) -> dict[str, Any]

decide_semantic_candidate_v3(
    candidate: ValidatedTransportCandidateV2,
    seal: SourceAcquisitionSeal,
    assets: RetainedExecutionAssets,
) -> ValidatedSemanticDecisionV3

inspect_semantic_candidate_v3(
    candidate: ValidatedTransportCandidateV2,
    seal: SourceAcquisitionSeal,
    assets: RetainedExecutionAssets,
) -> ValidatedSemanticDecisionV3 | RejectedSemanticDecisionV3
```

`ValidatedSemanticDecisionV3` は同じ:

```text
ValidatedTransportCandidateV2
SourceAcquisitionSeal
RetainedExecutionAssets
full validated Core result
compatibility-v3
source_inventory_seam: ValidatedSourceInventorySeamV3 | None
```

を保持します。

normal available branch では `source_inventory_seam()` は non-null。

selected cardinality TARGET-001 branch では:

```text
source_inventory_seam() is None
model_records measurement = null
entity measurement = null
```

です。

SI-05 は **この型を public authority として受ける**こと。

禁止:

```text
ValidatedSemanticDecisionV3
  -> ValidatedSemanticDecisionV2 cast

V3 Core
  -> legacy whole-ledger certificate

transport candidate
  -> public semantic success inference
```

---

## 5. source seam から使う existing facts

`ValidatedSourceInventorySeamV3` の current API:

```python
request_id
transport_candidate()
source_seal()
execution_assets()
source_records()
file_dispositions()
eligible_module_ids()
safe_files()
safe_projects()
counts()
profile_id
partition_preimage()
partition_fingerprint
```

`SourceInventoryCountsV3`:

```text
acquired_projects
acquired_files
acquired_file_bytes
proof_discovered
published_records
proof_only_records
accounted_records
published_modules
published_components
published_entities
```

SI-05 producer は publication eligibility を再判断しません。

normal public projection は Core が保持する seam と safe model を投影し、independent validator は retained Core owner から別経路で再導出します。

---

# 6. ten-schema closure

新規 schema は **ちょうど次の10個**です。

| # | file / URN | closed change | exact consumer |
|---:|---|---|---|
| 1 | `schemas/next-compatibility-v3.schema.json` / `urn:code-structure-viz:schema:next-compatibility-v3` | ten-key compatibility-v3、wire `code-structure-viz.next-semantic-compatibility/v3` | Core/public semantic |
| 2 | `schemas/next-semantic-v3.schema.json` / `...:next-semantic-v3` | semantic-v2 shapeを維持し required `source_inventory_summary`、compatibility-v3 exact ref | `semantic-v3`, JSON artifact |
| 3 | `schemas/semantic-v3.schema.json` / `...:semantic-v3` | generic dispatcher。Next は exact next-semantic-v3。Python/SQLAlchemy branch meaningは不変 | generic semantic consumer |
| 4 | `schemas/next-provenance-v3.schema.json` / `...:next-provenance-v3` | 17 slots、`next-observation/v3` version3、request-bound SOURCE-003 Core unavailable | run-v3 |
| 5 | `schemas/next-run-decision-v3.schema.json` / `...:next-run-decision-v3` | five request-bound categories、provenance-v3、14-key fingerprint | candidates-v3 / domain/publication |
| 6 | `schemas/next-publication-candidates-v3.schema.json` / `...:next-publication-candidates-v3` | run-v3 exact ref、same-Core candidate descriptors/capture meaning | publication-v2 typed owner dependency |
| 7 | `schemas/next-domain-manifest-v2.schema.json` / `...:next-domain-manifest-v2` | compatibility-v3 / run-v3 / publication-v2 familyへ移行 | run-manifest-v2 |
| 8 | `schemas/next-publication-decision-v2.schema.json` / `...:next-publication-decision-v2` | run-v3をexact ref、candidate-v3をfinal reference owner入力として要求する新generation | domain/root/stdout |
| 9 | `schemas/run-manifest-v2.schema.json` / `...:run-manifest-v2` | Next domain-v2 / run-v3 / publication-v2 refs。legacy domain semanticsは維持 | root manifest consumer |
| 10 | `schemas/stdout-result-v2.schema.json` / `...:stdout-result-v2` | publication-v2 exact ref、既存closed selector union意味を維持 | stdout result consumer |

`next-observation/v3` は `next-provenance-v3` 内の versioned observation wrapper identity であり、11個目の standalone schema を新設しません。

### schema hardening

全新objectは closed。

```text
additionalProperties: false
exact required set
closed discriminator/oneOf
native numeric constraints
exact refs
no legacy Next fallback union
```

旧schemaへ fieldを足してv3を通す方式は禁止です。

---

# 7. schema migration の具体的なルール

## `next-compatibility-v3`

current `compatibility_descriptor_v3()` が既に生成する値を schema 化します。

ten-key preimage:

```text
semantic_schema
identity_versions
algorithm_versions
semantic_profile_id
unicode_profile
runtime_binding_profile_id
typescript_identity
trusted_type_environment_digest
portable_toolchain_fingerprint
semantic_admission_profile_id
```

hash:

```text
compatibility_id = SHA256(CJ15(ten-key preimage))
```

含めない:

```text
schema
compatibility_id itself
request/source/targets
partition
status
model digest
host path/PID
```

## `next-semantic-v3`

既存 v2 の public shape/leaf意味を保持し、次を変更します。

```text
schema = code-structure-viz.semantic/v3
compatibility_descriptor -> exact next-compatibility-v3
source_inventory_summary -> required exact 7-key object
Project.file_ids -> safe membership
files -> actual safe Files
```

`source_inventory_summary` exact shape:

```json
{
  "profile_id": "...",
  "source_partition_fingerprint": "...",
  "acquired": {"projects": 0, "files": 0, "file_bytes": 0},
  "safe": {"projects": 0, "files": 0},
  "proof_only": {"failed_files": 0, "excluded_files": 0},
  "records": {
    "proof_discovered": 0,
    "published": 0,
    "proof_only": 0,
    "accounted": 0
  },
  "published_entities": {"modules": 0, "components": 0, "total": 0}
}
```

数値は `type(value) is int` かつ `value >= 0`。

`bool` と `1.0` を受理しません。

## `semantic-v3`

新 dispatcher は:

```text
Next -> next-semantic-v3
Python -> existing v1 branch
SQLAlchemy -> existing v1 branch
```

Next-v1/v2 を semantic-v3 の fallback として受けません。

legacy `semantic-v1` / `semantic-v2` 自体は変更しません。

---

# 8. provenance-v3

新 reference lane は `RetainedRuntimeResultV2` を lower runtime ownerとして維持し、V3 Coreだけを新しく joinします。

proposed:

```python
runtime_provenance_v3(
    runtime: RetainedRuntimeResultV2,
    *,
    semantic_decision:
        ValidatedSemanticDecisionV3
        | RejectedSemanticDecisionV3
        | None,
) -> dict[str, Any]

validate_runtime_provenance_v3(
    value: dict[str, Any],
    runtime: RetainedRuntimeResultV2,
    *,
    semantic_decision:
        ValidatedSemanticDecisionV3
        | RejectedSemanticDecisionV3
        | None,
) -> None
```

17 slot名は v2 と同じ:

```text
applicability
config
source
limits
source_plan
trusted_environment
runtime_bundle
node_candidate
request
launch_policy
process_start
node_version
control_response
semantic_payload
compatibility
model
budget
```

wrapperだけ:

```json
{
  "schema": "code-structure-viz.next-observation/v3",
  "version": 3,
  "sha256": "..."
}
```

へ移行します。

producer/validator は v2 provenance producerの期待値を呼びません。

lower runtime values、V3 Core owner、canonical hash primitiveは再利用可。

---

# 9. run-decision-v3 の five categories

proposed API:

```python
@dataclass(frozen=True, slots=True, init=False)
class RetainedRequestBoundRunDecisionV3: ...

retain_request_bound_run_decision_v3(
    runtime: RetainedRuntimeResultV2,
    *,
    semantic_decision:
        ValidatedSemanticDecisionV3
        | RejectedSemanticDecisionV3
        | None = None,
) -> RetainedRequestBoundRunDecisionV3

project_request_bound_run_decision_v3(
    owner: RetainedRequestBoundRunDecisionV3,
) -> dict[str, Any]

validate_request_bound_run_decision_v3(
    value: dict[str, Any],
    owner: RetainedRequestBoundRunDecisionV3,
) -> None
```

branchは five-category のままです。

| category | fingerprint | compatibility | measurement |
|---|---|---|---|
| Core complete | non-null | non-null v3 | entity actual |
| Core partial_safe | non-null | non-null v3 | entity actual |
| validated Core unavailable: TARGET / EXPORT / SOURCE-003 / entity LIMIT | non-null | non-null v3 | target/export/SOURCE=null、entity LIMITのみ actual |
| typed V3 Core rejection | non-null | null | record-limit rejectionだけ actual model records、protocol rejection null |
| lower runtime/transport failure | null | null | null |

SOURCE-003 validated Core unavailable は:

```text
stage = source_read
failure_code = CSV-NEXT-SOURCE-003
semantic_payload = observed
compatibility = observed
model = observed
budget = unobserved
entity measurement = null
```

とします。

これを request-independent reader prefixと混同しません。

---

# 10. run fingerprint v3

exact 14 keys:

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
semantic_admission_profile_id
```

含めない:

```text
source_partition_fingerprint
status/outcome
counts
response body
process/PID/host fields
```

`projects` は public safe Projectではなく、**acquired request Project full membership**です。

---

# 11. publication candidates v3

v2 classをcastしません。

proposed:

```python
@dataclass(frozen=True, slots=True, init=False)
class RetainedRequestBoundPublicationCandidatesV3: ...

retain_request_bound_publication_candidates_v3(
    run_decision: RetainedRequestBoundRunDecisionV3,
) -> RetainedRequestBoundPublicationCandidatesV3

validate_request_bound_publication_candidates_v3(
    owner: RetainedRequestBoundPublicationCandidatesV3,
) -> None
```

candidate leaf:

```text
RetainedPublicSemanticArtifactV3
RetainedPublicPlantumlArtifactV3
```

available complete / partial-safe のみ bytes を保持。

以下は空tuple:

```text
TARGET-001
EXPORT-001
SOURCE-003
entity overrun
Core rejection
runtime failure
```

selector は requested candidate set を縮めません。

artifact descriptor は既存 versionless six-field意味だけを再利用します。

```text
path
domain
format
media_type
size_bytes
sha256
```

---

# 12. public semantic / artifact reference modules

追加する reference code の中心は次です。

```text
tests/contracts/next_public_semantic_v3_reference.py
tests/contracts/next_public_semantic_v3_validation.py

tests/contracts/next_public_artifact_v3_reference.py
tests/contracts/next_public_artifact_v3_validation.py

tests/contracts/next_provenance_v3_reference.py
tests/contracts/next_provenance_v3_validation.py

tests/contracts/next_run_decision_v3_reference.py
tests/contracts/next_run_decision_v3_validation.py

tests/contracts/next_publication_candidates_v3_reference.py
tests/contracts/next_publication_candidates_v3_validation.py
```

tests:

```text
tests/contracts/test_next_public_semantic_v3.py
tests/contracts/test_next_public_artifact_v3.py
tests/contracts/test_next_provenance_v3.py
tests/contracts/test_next_run_decision_v3.py
tests/contracts/test_next_publication_candidates_v3.py
tests/contracts/test_next_public_exact_refs_v3.py
```

`test_json_schemas.py` も exact offline registry / schema list を更新します。

outer v2 schemasの executable product producerをこの unitで作る必要はありません。`test_next_public_exact_refs_v3.py` で complete closed literal recordsとrecursive refsを検証し、SI-06 ownerを先取りしないこと。

---

# 13. public semantic producer

proposed:

```python
project_public_semantic_document_v3(
    decision: ValidatedSemanticDecisionV3,
) -> dict[str, Any]

validate_public_semantic_document_v3(
    value: dict[str, Any],
    decision: ValidatedSemanticDecisionV3,
) -> None

validate_semantic_dispatcher_v3(
    value: dict[str, Any],
) -> None
```

precondition:

```text
type(decision) is ValidatedSemanticDecisionV3
gate.payload_available == true
decision.source_inventory_seam() is not None
```

selected cardinality TARGET branch (`seam=None`) を complete-empty として公開しません。

projector は:

```text
source / request       -> same retained parent context
compatibility          -> decision.compatibility_descriptor()
projects/files         -> validated source seam safe view
modules/.../facts      -> validated candidate safe model
status                 -> Core gate
source_inventory_summary -> seam/count/partition + safe model entity counts
```

からだけ作ります。

validator は projectorを expected oracle として呼びません。

---

# 14. first public seam — Red → minimum Green

最初の public behavior は normal `core_inputs_v3(tmp_path)` の complete decision です。

既にGreenの control:

```text
adapter version = 0.2.0
same real SourceAcquisitionSeal
same real ValidatedTransportCandidateV2
Core gate outcome = complete
Core actual entities = 4
accounted records = 17
```

これらを新SI-05 Redだと偽装しません。

### First Red

新test:

```text
test_v3_public_semantic_projects_real_source_inventory_summary
```

を作り、実 `core_inputs_v3()` → `candidate_for()` → `decide_semantic_candidate_v3()` を通します。

Red は:

```text
project_public_semantic_document_v3
```

が存在せず、この V3 Coreから closed public-v3 recordを生成できないこと。

fixture/import/setup failureをRedとは数えません。

### Minimum Green

最低限:

```text
next-compatibility-v3 schema
next-semantic-v3 schema
project_public_semantic_document_v3
independent validator
```

だけを実装し、この一件をGreenにします。

dispatcher、provenance、run、candidates、outer schemasは次cycleです。

---

# 15. first seam の独立 literal

current `core_inputs_v3()` の source bytes:

```text
package.json       30
tsconfig.json      24
src/button.tsx     42
src/index.ts       46
src/value.ts       59
src/global.d.ts    45
---------------------
total             246
```

public complete case の expected summary は literal:

```json
{
  "profile_id": "next-source-inventory-safe-subset-v1",
  "source_partition_fingerprint": "c543f59be0403f3bcf1cf13510f065f6a7e152e555aa394a42960d02a31d6d9f",
  "acquired": {
    "projects": 1,
    "files": 6,
    "file_bytes": 246
  },
  "safe": {
    "projects": 1,
    "files": 6
  },
  "proof_only": {
    "failed_files": 0,
    "excluded_files": 0
  },
  "records": {
    "proof_discovered": 17,
    "published": 17,
    "proof_only": 0,
    "accounted": 17
  },
  "published_entities": {
    "modules": 3,
    "components": 1,
    "total": 4
  }
}
```

この値を新 public producerから生成して expected に使ってはいけません。

---

# 16. first seam partition KAT

同じ current fixture input から独立再構成した request ID:

```text
4c19dcf0e98eb6df4e58af251216f4a06764cb5edf3217f7298c00995efff122
```

partition preimage:

```json
{
  "profile_id": "next-source-inventory-safe-subset-v1",
  "request_id": "4c19dcf0e98eb6df4e58af251216f4a06764cb5edf3217f7298c00995efff122",
  "projects": [
    {
      "project_id": "next:project:530b20c858c6039c19737f386f96cfabdadda6b8a0a1c98b5ca639beb2765c25",
      "safe_file_ids": [
        "next:file:4d7ea21c5296aea27a6fd1ea2b3ec895bd40dfc5c827e1759e0a401af1ecaf30",
        "next:file:6e5a491cdd30e69e4cf115a95b99ad11d83beac749f4f20d7fa12cb26d9f7c0c",
        "next:file:7d940b2adbc319b4843ed7495d2cfce15c2f5f3450ee587273b53f4f8d5ac2b5",
        "next:file:8cb22e35356bd13a3869a5dd8bd680300b8f8ba5bd33bcdbfc7653cc1eba3e76",
        "next:file:b2257b187308437ce03e40f7793970289bdb1aa71c5167b7796501cf91efa6ac",
        "next:file:c891008136a6466799eb75e12e6b6d7b2bdb35587cb8c2f96b3b5a720da870bf"
      ],
      "failed_file_ids": [],
      "excluded_file_ids": []
    }
  ]
}
```

CJ15 SHA-256:

```text
c543f59be0403f3bcf1cf13510f065f6a7e152e555aa394a42960d02a31d6d9f
```

この derivation は current request-v2 contractと current fixture literalsだけから独立構築します。production/public-v3 helperは使用しません。

同じ再構成方法が既存 SI-03 KAT:

```text
request_id =
8a550469363d2d92f6c55345cb8cc0c2f540109cafd4e8b507cfb5cf25de175d

partition =
0c380fdc863eab3e029cec9129a8fa000bb0695321221a559025757060d48b83
```

へ一致することも regression control にします。

---

# 17. compatibility ten-key KAT

既存 Core の independent literalを維持します。

```text
compatibility_id =
ecf055ae84276a9209e8cb65addabd0cbf4d882e0b76f54cc6f06208fa95880f
```

`tests/contracts/test_next_semantic_core_v3.py::test_v3_core_retains_independent_ten_key_compatibility_literal`

が current evidenceです。

SI-05 schema testではこの literal descriptor をそのまま schemaへ通し、field mutation / extra / wrong type / old v2 schema IDを拒否します。

新 compatibility producerから expected を作りません。

---

# 18. run fourteen-key KAT

legacy literal:

```text
tests/fixtures/next_runtime_v2/public-semantic-run-preimage.json
```

自体は変更しません。

新 v3 ASCII KAT は別fixtureとして手書きします。

v2 literalの13 fieldsを保ち:

```text
adapter_version:
  0.1.0 -> 0.2.0

add:
  semantic_admission_profile_id =
    next-source-inventory-safe-subset-v1
```

だけを新accepted contractに合わせます。

expected fourteen-key SHA-256:

```text
0e7bdc459bf01e9b42e4f416e565c8636b6a5dffde226aeca7beb4deee7207f0
```

新producerからこのhashを取得してexpectedへ代入してはいけません。

新fixture例:

```text
tests/fixtures/next_runtime_v3/public-semantic-run-preimage.json
```

legacy fixtureのautomatic rewriteはしません。

独立確認:

```bash
uv run --locked --group dev python -c \
'import hashlib,json,pathlib; p=pathlib.Path("tests/fixtures/next_runtime_v3/public-semantic-run-preimage.json"); v=json.loads(p.read_text()); b=json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode(); print(hashlib.sha256(b).hexdigest())'
```

expected output:

```text
0e7bdc459bf01e9b42e4f416e565c8636b6a5dffde226aeca7beb4deee7207f0
```

---

# 19. same-Core JSON / PlantUML

V3 artifact ownersはV2 ownerをcastせず兄弟型を作ります。

```python
RetainedPublicSemanticArtifactV3
retain_public_semantic_artifact_v3(
    decision: ValidatedSemanticDecisionV3,
) -> RetainedPublicSemanticArtifactV3

RetainedPublicPlantumlArtifactV3
retain_public_plantuml_artifact_v3(
    decision: ValidatedSemanticDecisionV3,
) -> RetainedPublicPlantumlArtifactV3
```

JSON:

```text
project_public_semantic_document_v3(decision)
-> CJ15
-> one terminal LF
```

PlantUML:

```text
same decision.transport_candidate().semantic_payload()["model"]
same gate outcome
-> existing unchanged render_plantuml / statement grammar
```

allowed reuse:

```text
render_plantuml
validate_plantuml_contract
canonical JSON codec
SHA-256 primitive
six-field descriptor meaning
```

forbidden reuse:

```text
RetainedPublicSemanticArtifactV2 as V3 certificate
RetainedPublicPlantumlArtifactV2 as V3 certificate
ValidatedSemanticDecisionV2
old public document as new expected record
```

---

# 20. required semantic cases

SI-05 testsは current Core factory/mutation意味を再利用し、own-class mockや forged seal/graph/decision を作りません。

| case | public expectation |
|---|---|
| full normal complete | summary literal above、JSON/PlantUML両方 |
| legitimate proof-only / owner Module failure | untainted Fileがexcluded/failed、proof-only count増加、safe ownerだけ公開 |
| nonprogram safe File | Moduleを生成せず safe.files に含む |
| complete-empty | Projects/Filesは意味どおり保持、entities=0、status complete |
| selection-only `not_selected` / `target_excluded` | completeを維持、failure/partialへ変えない |
| all Files private | Projectは空`file_ids`でpublic、partial_safe、proof-only source recordsをcount |
| multi-project | private側Projectを空にしても independent safe Projectを消さない |
| SOURCE-003 | public artifact無し、run fingerprint/compatibility保持、entity measurement null |
| TARGET-001 | public artifact無し、seam=Noneもempty successへ変えない |
| Core rejection | compatibility public suffix無し、candidate無し |
| runtime failure | compatibility/fingerprint無し、candidate無し、descriptor-only response semantics維持 |

current SI-04 testsを expected-value generatorとして呼ばず、その fixture construction semanticsを参考にSI-05 test-side inputsを構築します。

---

# 21. native-number negatives

JSON Schemaの `integer` だけでは Python上の `1.0` 等を十分に区別できません。

independent validatorは少なくとも次を recursive に拒否します。

```text
summary counts: 1.0
summary count: true
artifact size_bytes: 9472.0
capture measured bytes: false
run budget: 500.0
observation version: 3.0
publication version: true
```

原値がintなら `type(value) is int` を要求します。

boolをintとして受けません。

coercion:

```python
int(value)
bool(value)
```

で「直す」のは禁止です。

---

# 22. owner/substitution negatives

最低限:

```text
equal-content Core from another exchange
foreign SourceAcquisitionSeal
foreign RetainedExecutionAssets
foreign RetainedRuntimeResultV2
foreign V3 Core
foreign run-v3 owner
foreign artifact leaf
```

を拒否します。

同じJSON/hashでも object identity / retained owner chain が違えば不正です。

### rehashed-cache negative

典型:

```text
nested fieldをforeign valueへ変更
↓
compatibility/run/artifact hashを正しく再hash
↓
owner cacheも同じwrong valueへ揃える
```

状態でも independent validator は retained parentから再導出し拒否します。

「cache同士が一致」が certificateになってはいけません。

---

# 23. downgrade negatives

新chainから以下を拒否します。

```text
next-compatibility-v2 -> v3
next-semantic-v2 -> semantic-v3 Next branch
next-provenance-v2 -> run-v3
next-run-decision-v2 -> candidates-v3
next-publication-candidates-v2 -> publication-v2 owner
next-domain-manifest-v1 -> new Next root branch
next-publication-decision-v1 -> stdout-v2 Next ref
old Next semantic-v1 bypass
```

legacy schema/tests自体は引き続きGreenであること。

つまり「旧schemaを壊す」のではなく、「新chainからdowngradeできない」が要件です。

---

# 24. privacy negatives

public JSON、candidate metadata、domain/root/stdout schema vectorに次を許可しません。

```text
content_base64
source body
proof
failure roots / causal edges
private control
raw response body
raw stderr
absolute repository/tmp path
PID / PGID / FD
private cwd
host-local process details
proof-only record payload
```

safe repository-relative path、closed diagnostic/ref、hash/countはauthority範囲内のみ。

nested mutationでも拒否します。

---

# 25. outer four v2 schemas と SI-06 境界

次を **complete closed schemaとして今回追加**します。

```text
next-domain-manifest-v2
next-publication-decision-v2
run-manifest-v2
stdout-result-v2
```

ただし `retain/finalize` product ownerを新設してSI-06を先取りしません。

SI-05で検証するもの:

```text
wire identity
required/closed keys
recursive exact refs
status/incomplete/payload correlation
artifact descriptor shape
run-v3 nesting
publication-v2 nesting
domain-v2 nesting
stdout selector closed union
TARGET failure rows only on target branch
SOURCE/rejection/runtime generic unavailable branch
no old Next ref
native numeric shape
privacy
```

SI-06に残すもの:

```text
catalog-owned diagnostic production
actual public stderr encode/64KiB exact/+1
diagnostic-to-stderr execution
single executable publication finalizer
persist/copy behavior
final product exit/stderr closure
```

この区分を schema test名/Artifactにも明記します。

---

# 26. exact-ref test helper

current `tests/contracts/test_json_schemas.py::_validator()` は固定offline registryです。

SI-05では新10 URNを registryへ追加し、少なくとも次を testします。

```text
every new schema Draft202012-valid
every $ref offline resolvable
all ten URNs unique
old URNs unchanged
no new schema refs an old whole Next certificate where a new generation is required
no legacy Next branch accepted by new dispatcher
```

schema syntax passだけで owner correctnessを認定しません。

reference validatorsと両方向で確認します。

---

# 27. consumer census

実装前・実装後に同じ census を行います。

```bash
git grep -n -E \
'next-(compatibility|semantic|provenance|run-decision|publication-candidates|domain-manifest|publication-decision)-v[123]|semantic-v[123]|run-manifest-v[12]|stdout-result-v[12]' \
-- schemas tests docs
```

分類:

```text
new exact ref
unchanged leaf ref
legacy regression only
historical docs only
unexpected stale consumer
```

unexpected stale Next consumerが一件でもあれば unit未完了です。

---

# 28. TDD順序

1 behavior = 1 Red → minimum Green とします。

| cycle | behavior |
|---:|---|
| 1 | compatibility-v3 physical schemaが無い → current Core ten-key descriptorをexact accept |
| 2 | first public semantic-v3 seam → literal summary/partition/hash |
| 3 | public validator independently rederives summary / owner |
| 4 | semantic-v3 dispatcher routes Next-v3 and rejects old Next bypass |
| 5 | same-Core canonical JSON retained artifact |
| 6 | same-Core PlantUML retained artifact |
| 7 | proof-only owner-closed partial-safe public projection |
| 8 | nonprogram + complete-empty |
| 9 | selection-only remains complete |
| 10 | all-files-private Project empty membership |
| 11 | multi-project independent safe side |
| 12 | provenance-v3 17 observation identities |
| 13 | run-v3 complete / partial categories |
| 14 | TARGET unavailable, compatibility/fingerprint retained, entity null |
| 15 | SOURCE-003 unavailable with same rule |
| 16 | Core rejection category |
| 17 | lower runtime failure category |
| 18 | fourteen-key independent KAT |
| 19 | candidates-v3 requested JSON |
| 20 | candidates-v3 same-Core PlantUML/both/order |
| 21 | unavailable/rejection/runtime produce no candidates |
| 22 | int/bool/float negatives |
| 23 | cross-exchange equal-content negatives |
| 24 | rehashed-cache substitution |
| 25 | downgrade/privacy negatives |
| 26 | four outer v2 schemas / recursive ref vectors |
| 27 | full ref/consumer census |

既にGreenの SI-04 invariantsを新Redとして報告しません。

documentation/ref censusも fake Redを作らず、inspection/checkとして記録します。

---

# 29. proposed focused test names

最低限、意図が分かる名前にします。

```text
test_v3_public_semantic_projects_real_source_inventory_summary
test_v3_public_semantic_matches_independent_partition_literal
test_v3_public_semantic_refuses_unavailable_or_seamless_core
test_v3_dispatcher_preserves_old_domains_and_rejects_old_next_bypass
test_v3_public_artifacts_share_exact_same_core_owner
test_v3_public_artifacts_reject_foreign_equal_content_core
test_v3_public_summary_uses_actual_proof_only_owner_closed_counts
test_v3_public_complete_empty_and_nonprogram_file_are_not_unavailable
test_v3_public_selection_only_preserves_complete
test_v3_public_all_private_files_keep_empty_project
test_v3_public_multi_project_keeps_independent_safe_project

test_v3_provenance_rederives_all_seventeen_observations
test_v3_run_retains_independent_fourteen_key_literal
test_v3_run_source003_has_compatibility_but_no_entity_measurement
test_v3_run_target_failure_has_no_empty_success
test_v3_run_core_rejection_has_no_admitted_compatibility
test_v3_run_runtime_failure_has_no_fake_fingerprint
test_v3_run_rejects_equal_content_foreign_exchange
test_v3_run_rejects_rehashed_cache_substitution

test_v3_candidates_keep_requested_same_core_json_and_plantuml
test_v3_candidates_do_not_shrink_to_stdout_selector
test_v3_candidates_are_empty_for_source_target_rejection_runtime_failure
test_v3_candidates_reject_float_bool_and_foreign_owner

test_v3_exact_ref_closure_resolves_all_ten_schemas_offline
test_v3_exact_ref_closure_rejects_legacy_next_downgrade
test_v3_outer_schemas_reject_private_and_cross_generation_fields
```

---

# 30. expected-value rule

新producerをexpected oracleにしません。

許可:

```text
literal JSON
existing accepted fixture input
current Core retained owners
independent stdlib json/hashlib
existing canonical codec primitive for validation
existing immutable identity literals
existing PlantUML parser/statement grammar
```

禁止:

```text
expected = new_producer(...)
expected_hash = new_producer(...).sha256
expected_summary = projector(decision)["source_inventory_summary"]
automatic rewrite of old KAT/fixture
```

mutation helperがhashを直してnegative inputをschema-validにすることは許容しますが、それをpositive oracleにしません。

---

# 31. focused commands

各Red/Green:

```bash
uv run --locked --group dev pytest \
  tests/contracts/test_next_public_semantic_v3.py \
  -q -k 'test_v3_public_semantic_projects_real_source_inventory_summary'
```

次に新SI-05全体:

```bash
uv run --locked --group dev pytest \
  tests/contracts/test_next_public_semantic_v3.py \
  tests/contracts/test_next_public_artifact_v3.py \
  tests/contracts/test_next_provenance_v3.py \
  tests/contracts/test_next_run_decision_v3.py \
  tests/contracts/test_next_publication_candidates_v3.py \
  tests/contracts/test_next_public_exact_refs_v3.py \
  tests/contracts/test_json_schemas.py \
  -q
```

---

# 32. Core / source regression

```bash
uv run --locked --group dev pytest \
  tests/contracts/test_next_source_inventory_v3.py \
  tests/contracts/test_next_semantic_core_v3.py \
  -q
```

actual 10000/10001、500/501 を excludeしません。

---

# 33. old v2 public/run regression

```bash
uv run --locked --group dev pytest \
  tests/contracts/test_next_public_semantic_v2.py \
  tests/contracts/test_next_public_artifact_v2.py \
  tests/contracts/test_next_public_plantuml_v2.py \
  tests/contracts/test_next_provenance_v2.py \
  tests/contracts/test_next_run_decision_v2.py \
  tests/contracts/test_next_publication_candidates_v2.py \
  -q
```

旧v2がGreenであることは新v3 passの代替ではありません。

---

# 34. existing domain bytes

```bash
uv run --locked --group dev pytest \
  tests/contracts/test_python_goldens.py \
  tests/contracts/test_sqlalchemy_goldens.py \
  -q
```

golden updateでGreenにしません。

Python/SQLAlchemy byte diffが出たら原因を調べ、SI-05都合でexpectedを更新しません。

---

# 35. contract / full candidate gates

SI-05 clean candidate では、focused evidence後に broad regressionも実行します。

```bash
uv run --locked --group dev pytest tests/contracts -q --tb=short
```

続いて:

```bash
uv run --locked --group dev pytest -q
```

これを「全A02/A03 pass」とは呼びません。SI-05 candidate の regression evidenceです。

large casesをskip/deselectする専用optionを加えません。

---

# 36. static gates

```bash
uv run --locked --group dev ruff check .
uv run --locked --group dev ruff format --check .
uv run --locked --group dev mypy src tests
```

expected:

```text
src/** diff empty
pyproject.toml diff empty
uv.lock diff empty
```

---

# 37. SpecDock

実行直前に help:

```bash
python3 spec-dock/scripts/spec-dock --help
python3 spec-dock/scripts/spec-dock sync --help
python3 spec-dock/scripts/spec-dock validate --help
```

その current help が user-supplied syntaxを維持していることを確認後:

```bash
python3 spec-dock/scripts/spec-dock sync --no-github --no-update-active
python3 spec-dock/scripts/spec-dock validate
```

SpecDock mutationが必要なら CLI 経由のみ。

metadataを手編集してCLI guardを迂回しません。

---

# 38. PlantUML verification

SI-05 で必要なのは same-Core candidate semantics です。

必須:

```bash
uv run --locked --group dev pytest \
  tests/contracts/test_next_public_artifact_v3.py \
  -q
```

ここで existing `validate_plantuml_contract` を使い:

```text
UTF-8
BOM無し
CR無し
LF-only
terminal LF一つ
one statement/line
model/outcome exact
descriptor size/hash exact
```

を検証します。

current expected SI-05 diffでは tracked human explanation HTML を変更しないため、repository内で command textを確認できなかった外部/pinned HTML renderer commandを推測・downloadして追加しません。

将来この unitで explanation HTML を変更する必要が生じた場合は、current authorized pinned validatorの実instructionを確認してから実行し、未確認なら `未実行` と記録します。

---

# 39. final diff checks

```bash
git diff --check
git diff --name-only -- src
git diff -- pyproject.toml uv.lock
find . -type d -name node_modules -print
git status --short
```

期待:

```text
git diff --name-only -- src  -> empty
pyproject/uv.lock             -> empty
node_modules                  -> empty
```

---

# 40. expected implementation surface

主な許容surface:

```text
schemas/<new ten schemas>

tests/contracts/next_public_semantic_v3_reference.py
tests/contracts/next_public_semantic_v3_validation.py
tests/contracts/next_public_artifact_v3_reference.py
tests/contracts/next_public_artifact_v3_validation.py
tests/contracts/next_provenance_v3_reference.py
tests/contracts/next_provenance_v3_validation.py
tests/contracts/next_run_decision_v3_reference.py
tests/contracts/next_run_decision_v3_validation.py
tests/contracts/next_publication_candidates_v3_reference.py
tests/contracts/next_publication_candidates_v3_validation.py

tests/contracts/test_next_public_semantic_v3.py
tests/contracts/test_next_public_artifact_v3.py
tests/contracts/test_next_provenance_v3.py
tests/contracts/test_next_run_decision_v3.py
tests/contracts/test_next_publication_candidates_v3.py
tests/contracts/test_next_public_exact_refs_v3.py
tests/contracts/test_json_schemas.py

tests/fixtures/next_runtime_v3/...   # hand-authored literal/KAT only
```

SpecDock evidence/Plan/Reportを更新する場合は current CLI が返した exact pathだけを追加します。

---

# 41. stop conditions

以下のどれかが必要になったら implementationを止め、exact conflictを報告します。

```text
Requirement/Design/Plan意味の変更
new diagnostic code/reason/state
new ASSET policy
SI-04 P2 policy変更
normal V3 Core guardの緩和
source_inventory_seamの意味変更
Module→File reverse taint
Project taint
old identity/hash preimage変更
old v1/v2 schemaを書換えないと進めない
Python/SQLAlchemy golden変更が必要
public proof-only referenceが必要
source/body/raw proofを公開する必要
ValidatedSemanticDecisionV2へのcastが必要
fake SourceAcquisitionSeal/graph/decisionが必要
caller supplied status/measurementが必要
outer v2 schemaを閉じるために未採択wire fieldが必要
SI-06 diagnostic/stderr executionがなければschema meaningを定義不能
production src/dependency/Node executionが必要
```

最後の二つが実際に発生した場合だけ、SI-05/SI-06 separationの authority conflictとして bounded decision packageへ切り替えます。

---

# 42. staging

checkpoint前:

```bash
git status --short
git branch --show-current
git rev-parse HEAD
git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}'
```

branch:

```text
iss-00008-generate-nextjs-component-snapshots
```

であること。

stage は explicit pathsのみ。

例:

```bash
git add -- \
  schemas/next-compatibility-v3.schema.json \
  schemas/next-semantic-v3.schema.json \
  schemas/semantic-v3.schema.json \
  schemas/next-provenance-v3.schema.json \
  schemas/next-run-decision-v3.schema.json \
  schemas/next-publication-candidates-v3.schema.json \
  schemas/next-domain-manifest-v2.schema.json \
  schemas/next-publication-decision-v2.schema.json \
  schemas/run-manifest-v2.schema.json \
  schemas/stdout-result-v2.schema.json
```

続けて実際に変更した `tests/contracts/...` と SpecDock-returned exact pathsを `git add -- <explicit paths>` します。

禁止:

```text
git add .
git add -A
alternate index
settings workaround
permission bypass
```

---

# 43. commit

commit前に全staged diff:

```bash
git diff --cached --check
git diff --cached --
git status --short
```

全内容を読むこと。

commitは installed authorization contractどおり直接:

```bash
commit-codex -a
```

manual message route、`--no-verify`、hook bypassへfallbackしません。

---

# 44. push

push前に upstream を再確認。

通常push:

```bash
git push -- origin iss-00008-generate-nextjs-component-snapshots
```

禁止:

```text
--force
--force-with-lease
history rewrite
new checkout
extra ref mutation
PR/merge
```

push後:

```bash
git rev-parse HEAD
git status --short
git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}'
```

clean/current-upstream を確認します。

---

# 45. fresh cumulative SI-05 Code Review Strict

review base は途中checkpointへ移しません。

```text
base:
2efb54c370ac05ac4da0d9b0bfe717a13b62380c

head:
final clean pushed SI-05 candidate
```

required local evidenceが同じ candidateへ揃った後だけ:

```text
fresh Code Review Strict
GPT-5.6 Sol
Extra High
```

を実行します。

primary authorとreviewerを混同しません。

subagentは使いません。

UI/Browserによるprogress monitoringをしません。

P2/P3を自動remediation/backlog化しません。特に既知SI-04 P2をSI-05変更理由にしません。

進行条件は scoped review の:

```text
P0 = 0
P1 = 0
review_status = pass
```

です。

---

# 46. SI-05 completion checklist

SI-05 は以下が同一 clean pushed candidateで成立したとき完了です。

1. new ten schema files が全て存在する。
2. 全10 URNがunique。
3. 全recursive `$ref` がoffline解決する。
4. legacy v1/v2 schemaはbyte/meaning不変。
5. V3 Coreだけが new public authority。
6. `source_inventory_summary` exact seven-key closed。
7. normal fixture summaryが `1/6/246`, `17/17/0/17`, entities `3/1/4`。
8. partition literalが `c543f59...`。
9. compatibility KATが `ecf055ae...`。
10. run fourteen-key KATが `0e7bdc45...`。
11. public Project/Fileはsource seam safe viewと一致。
12. owner-closed proof-only Fileをsafe countへ混ぜない。
13. all-files-privateでもProjectを消さない。
14. multi-project safe sideを消さない。
15. complete-empty/nonprogramがfalse unavailableにならない。
16. selection-onlyがfalse partial_safeにならない。
17. SOURCE-003がempty successにならない。
18. TARGET-001/seam=Noneがempty public semanticにならない。
19. Core rejectionにcompatibilityを捏造しない。
20. runtime failureにrun fingerprintを捏造しない。
21. source unavailable/target/exportでentity measurementはnull。
22. entity LIMITだけactual entity measurementを保持。
23. JSONとPlantUMLが同一V3 Core owner。
24. selectorがrequested candidate setを縮めない。
25. public numeric valuesはnative int、bool/float拒否。
26. equal-content foreign exchangeを拒否。
27. rehashed cache substitutionを拒否。
28. new dispatcherからlegacy Next downgrade不可。
29. source/proof/control/host/private data非公開。
30. Python/SQLAlchemy old bytes/goldens不変。
31. `src/**`差分なし。
32. deps/lock差分なし。
33. focused SI-05 tests green。
34. SI-04/source regression green。
35. old public/run v2 regression green。
36. contracts suite green。
37. full pytest green。
38. Ruff/format/mypy green。
39. SpecDock sync/validate green。
40. `git diff --check` green。
41. explicit-path staging/full staged diff確認済み。
42. `commit-codex -a` normal hooks成功。
43. same configured branchへnon-force push済み。
44. original `2efb54c...` → final candidate の fresh cumulative SI-05 Strictがpass。

ここまでが **SI-05 public/exact-ref reference/schema closure** です。

以下は引き続き未完了です。

```text
SI-06 catalog diagnostics
SI-06 stderr exact/+1
SI-06 executable final publication owner
reader-prefix closure
unadopted ASSET decision
whole A02 / SI-07
cumulative A03
production TypeScript / OS / CLI
package/offline acceptance
Final / Issue #8 completion
```
