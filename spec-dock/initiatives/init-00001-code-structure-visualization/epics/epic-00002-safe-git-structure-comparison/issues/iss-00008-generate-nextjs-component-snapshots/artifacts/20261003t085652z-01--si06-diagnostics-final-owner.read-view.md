GitHub 検証は成功しています。以下が、`af6f5d33f9487a33dabf2ddfe41df85b3d8267fb` を固定 base とする SI-06 実装ブリーフです。

# Issue #8 — SI-06 catalog-owned diagnostic / stderr / single final publication owner 実装ブリーフ

## 1. 固定点

GitHub connector で次を直接確認済みです。

| 項目 | 固定値 |
|---|---|
| repository | `chemitaro/code-structure-viz` |
| branch | `iss-00008-generate-nextjs-component-snapshots` |
| verified branch tip | `af6f5d33f9487a33dabf2ddfe41df85b3d8267fb` |
| SI-06 original unit base | `af6f5d33f9487a33dabf2ddfe41df85b3d8267fb` |
| SHA comparison | expected SHA と byte-for-byte 一致 |
| SI-05 certified code candidate | `6d52ff7949d64e747235eef870631cd8cc29b273` |

`6d52ff7949d64e747235eef870631cd8cc29b273..af6f5d33f9487a33dabf2ddfe41df85b3d8267fb` を connector で比較すると、変更は `docs/contracts/**` と Issue の review/evidence/Plan/Report に限定され、`src/**`、`tests/**`、`schemas/**` の実装変更はありません。したがって `af6f5d3` は SI-05 review/certification を記録した docs-only checkpoint であり、SI-05 の認定範囲を拡張しません。

repository root の `AGENTS.md` は exact commit に存在せず、root listing でも不在です。`.agents/skills/spec-dock/SKILL.md` は存在し、SpecDock について current CLI help、canonical files、command result を authority とし、失敗した command を raw filesystem/Git/GitHub 操作で迂回しないことを確認済みです。

本ブリーフは、添付 `brief.md` が指定する「一つの selected milestone の practical companion」であり、Requirement / Design / Plan を修正せず、verified commit の仕様・code/testsに grounding し、existing / proposed work と隣接 unit の境界を分けるものです。:chatgpt-content-reference{index="0"}

実装 actor の作業設定は caller-visible **GPT-6.1 Sol / Max** です。backend identity は本ブリーフでは独立検証していません。

---

## 2. authority

正本は exact commit の次です。

```text
spec-dock/initiatives/init-00001-code-structure-visualization/
  epics/epic-00002-safe-git-structure-comparison/
  issues/iss-00008-generate-nextjs-component-snapshots/
    requirement.md
    design.md
    plan.md
    artifacts/20261001t024645z-adr-issue8-trusted-toolchain-launch-model.md
    artifacts/20261002t001435z-adr-issue8-source-inventory-safe-subset.md
    artifacts/20261002t041350z-adr-issue8-owner-closed-file-module-publication.md

docs/contracts/next-semantic-admission-v3.md
docs/contracts/next-semantic-v3.md
docs/contracts/next-compatibility-v3.md
```

優先順位は:

```text
Current Requirement
→ Current Design
→ Current Plan の SI 実装順序
→ accepted ADR
→ current contract docs
→ current schema / reference / executable tests
→ certification artifacts（進捗証拠のみ）
→ historical Round sections（非normative）
```

です。

`docs/contracts/diagnostic-v1.md` に残る Round23 umbrella の記述は Current R/D/P の「round専用umbrellaをauthorityにしない」と衝突するため、SI-06 authority として採用しません。そこから再利用できるのは catalog-owned fixed message、privacy、canonical JSONL 等の現行schema/catalogと一致する wire-independent semantics だけです。

---

## 3. 先行認定と依存

既認定:

```text
SI-01/02 specification:
bcae9548ef515e4a7662de1ad648171622c6a437

SI-03 source/proof:
23072c288fc203071c10bfe3305e6ec5d3b055fe

SI-04 full Core:
d6bbbcf337ee4008d5925a6294a9065ca167a0e2

SI-05 public/exact-ref:
6d52ff7949d64e747235eef870631cd8cc29b273
```

SI-05 certificate:

```text
spec-dock/initiatives/init-00001-code-structure-visualization/
epics/epic-00002-safe-git-structure-comparison/
issues/iss-00008-generate-nextjs-component-snapshots/
artifacts/20261003t073304z-04-disc-si05-public-exact-ref-cumulative-certification.md
```

SI-05 は同じ clean candidate で:

```text
tests/contracts: 1995 passed
full pytest:     3064 passed, 1 existing Linux-only skip
Ruff:            pass
format:          249 files
mypy:            207 sources
SpecDock:        nodes=10
fresh cumulative Code Review Strict: pass / findings 0
```

を記録しています。

以前の `run-manifest-v2` `$id` 欠落 finding は誤認であり、actual complete schema object に:

```text
$id = urn:code-structure-viz:schema:run-manifest-v2
```

が一度存在することを再reviewで確認済みです。

**SI-06 で `$id` relocation、duplicate、repair を行いません。**

---

# 4. selected unit

Current Plan の **SI-06 diagnostic/stderr/final-owner** だけです。

成果:

```text
RetainedRequestBoundRunDecisionV3
  ↓
RetainedRequestBoundPublicationCandidatesV3
  ↓
catalog-owned public diagnostics
  ↓
public diagnostic stderr boundary
  ↓
one final selected-copy measurement
  ↓
single immutable final publication owner
  ↓
next-publication-decision/v2
  ↓
next-domain-manifest/v2
run-manifest/v2
run-summary/v1
stdout-result/v2 / exact selected bytes
stderr bytes
exit code
```

SI-06 の observable exit は:

1. 正規 `parse_file` / `read_file` semantic root が Core-v3 / run-v3 から `CSV-NEXT-SOURCE-001` public diagnostic へ到達する。
2. nonlocal source は `CSV-NEXT-SOURCE-003` のまま。
3. TARGET / EXPORT / entity-limit / record-limit / protocol / runtime failure は既存 code/stage/count authorityを変えない。
4. public diagnostic stderr は実 65,536 bytes inclusive、65,537 bytesは stderr `b""` / partial 0 / manifest `CSV-NEXT-LIMIT-003` 一件。
5. selected stdout は actual configured 16 MiBで一度だけ測定する。
6. selected copy +1 では semantic decision と persisted artifact descriptor を保持し、publicationだけ incomplete / exit 3。
7. domain/root/summary/typed unavailable/stderr/exit は同じ final owner からしか投影できない。

---

## 5. 明示的な対象外

今回実装しません。

```text
reader-owned request-independent prefix
pre-seal acquisition failure semantics
new ASSET failure policy
source-integrity terminal redesign
usage/fatal/interruptedの新policy
SI-04 report-only P2/P3 remediation
actual TypeScript adapter
actual Node/OS process execution
CLI wiring
src/**
package/dependency/lock/license
wheel/sdist
all-A02 closure
A03 cumulative review
A04 production
A05 / Final / whole Issue acceptance
```

run-level usage/fatal/interrupted は semantic/finalizer より前で一度分岐する既存境界を維持します。

SI-06 factory は request-bound `RetainedRequestBoundPublicationCandidatesV3` だけを入力にし、reader-prefixやterminal objectを受理するAPIを作りません。

---

# 6. confirmed SI-05 owners

## run-v3

`tests/contracts/next_run_decision_v3_reference.py`:

```python
class RetainedRequestBoundRunDecisionV3

retain_request_bound_run_decision_v3(
    runtime_result: RetainedRuntimeResultV2,
    *,
    semantic_decision:
        ValidatedSemanticDecisionV3
        | RejectedSemanticDecisionV3
        | None = None,
) -> RetainedRequestBoundRunDecisionV3

project_request_bound_run_decision_v3(
    owner: RetainedRequestBoundRunDecisionV3,
) -> dict[str, Any]
```

independent validator:

```text
tests/contracts/next_run_decision_v3_validation.py
validate_request_bound_run_decision_v3
```

この owner は:

```text
same RetainedRuntimeResultV2
same V3 Core
14-key run fingerprint
provenance-v3
actual entity / model-record measurement
response receipt descriptor
```

を既に閉じています。

## candidates-v3

`tests/contracts/next_publication_candidates_v3_reference.py`:

```python
class RetainedRequestBoundPublicationCandidatesV3

retain_request_bound_publication_candidates_v3(
    run_decision: RetainedRequestBoundRunDecisionV3,
) -> RetainedRequestBoundPublicationCandidatesV3

project_request_bound_publication_candidates_v3(
    owner: RetainedRequestBoundPublicationCandidatesV3,
) -> dict[str, Any]
```

getter:

```text
run_decision()
artifacts()
record()
artifact_bytes("semantic-json" | "plantuml")
```

independent validator:

```text
tests/contracts/next_publication_candidates_v3_validation.py
validate_request_bound_publication_candidates_v3
```

既に:

- stdout selector は requested formats を縮小しない。
- available Core のみ requested JSON/PlantUML bytesを保持する。
- target/source/Core-rejection/runtime failure は artifact tuple 空。
- lower runtime capture measurements は actual runtime observation / request-owned limits へjoinする。
- equal-content foreign run、cache-aligned mutation、float countを拒否する。

したがって SI-06 は candidate bytesやchild captureを再取得・再render・再measureしません。

---

# 7. lower owner を再認定しない

確認済み下位owner:

```text
RetainedRuntimeResultV2
ValidatedTransportCandidateV2
RetainedObservedResponseReceiptV2
SourceAcquisitionSeal
RetainedExecutionAssets
```

SI-06 は:

```text
runtime2 → Core3 → run3 → candidates3
```

という既認定chainを使用します。

禁止:

```text
ValidatedSemanticDecisionV3 → ValidatedSemanticDecisionV2 cast
run3 → run2 cast
candidates3 → candidates2 cast
legacy NextRunDecision surrogate
caller bool から source locality を作る
caller status/hash/count を finalizerへ渡す
fake SourceAcquisitionSeal
同値の別exchangeをownerとして使う
```

---

# 8. catalog baseline

固定catalog:

```text
schemas/next-diagnostic-catalog-v1.json
schemas/diagnostic-v1.schema.json
```

代表 mapping:

| code | ref | outcome |
|---|---|---|
| `CSV-NEXT-SOURCE-001` | `path` | `partial_safe` |
| `CSV-NEXT-SOURCE-003` | `path` | `payload_unavailable` |
| `CSV-NEXT-TARGET-001` | `path_or_symbol` + reason | `payload_unavailable` |
| `CSV-NEXT-EXPORT-001` | `symbol` | `payload_unavailable` |
| `CSV-NEXT-LIMIT-003` | none | `payload_unavailable` |
| `CSV-NEXT-LIMIT-005` | none | `payload_unavailable` |
| `CSV-NEXT-PROTOCOL-001` | none | `payload_unavailable` |
| `CSV-NEXT-NODE-*` | none | `payload_unavailable` |

fixed message、severity、recoverable、outcome、ref permission は catalog からのみ取得します。

raw exception text、child stderr text、compiler messageを message fieldへ渡しません。

---

# 9. planned small implementation targets

以下は **現在存在しない planned paths** として追加します。

```text
tests/contracts/next_public_diagnostic_v3_reference.py
tests/contracts/next_public_diagnostic_v3_validation.py

tests/contracts/next_final_publication_v2_reference.py
tests/contracts/next_final_publication_v2_validation.py

tests/contracts/next_final_publication_v2_fixtures.py

tests/contracts/test_next_public_diagnostic_v3.py
tests/contracts/test_next_final_publication_v2.py
```

**expected schema changes: none**。

次も変更しません。

```text
schemas/next-diagnostic-catalog-v1.json
schemas/diagnostic-v1.schema.json
SI-05 ten schemas
legacy v1/v2 schemas
old KAT/goldens
```

required branch が current outer schemasで表現不能と判明した場合は schema をその場で緩和せず Stop 条件へ進みます。

---

# 10. planned public diagnostic API

`next_public_diagnostic_v3_reference.py`:

```python
def project_public_diagnostics_v3(
    run_decision: RetainedRequestBoundRunDecisionV3,
) -> tuple[dict[str, Any], ...]:
    ...
```

`next_public_diagnostic_v3_validation.py`:

```python
def validate_public_diagnostics_v3(
    value: tuple[dict[str, Any], ...],
    run_decision: RetainedRequestBoundRunDecisionV3,
) -> None:
    ...
```

producerへの自由入力は `run_decision` 一個だけです。

禁止引数:

```text
diagnostic_code
status
path
symbol
reason
message
count
outcome
raw stderr
```

validator は projector を expected oracle として呼びません。

---

# 11. diagnostic derivation

## available complete / partial Core

Core:

```text
run.semantic_decision()
  is ValidatedSemanticDecisionV3
```

なら、candidate model/proofは full Core validator 通過済みです。

### normal semantic diagnostic

`payload["model"]["diagnostics"]` のvalidated internal rowから:

```text
code
path_ref
symbol_ref
reason if allowed
```

だけを取り、固定属性を catalog から再取得します。

internal `count` を public diagnostic-v1へ追加しません。

### parse_file / read_file

`proof.failure_roots` の:

```text
kind in {"parse_file", "read_file"}
path_ref
```

を owner evidence とします。

public row:

```json
{
  "type": "diagnostic",
  "schema": "code-structure-viz.diagnostic/v1",
  "code": "CSV-NEXT-SOURCE-001",
  "severity": "error",
  "domain": "next",
  "path": "src/value.ts",
  "symbol": null,
  "line": null,
  "recoverable": true,
  "message": "A source file could not be analyzed safely.",
  "outcome": "partial_safe",
  "ref_permission": "path"
}
```

File root kind自体を公開messageへ入れません。

同じpathに複数rootがあれば public wire row は canonical valueでdedupeし、異なるpathは canonical JSON bytes順に保持します。

## SOURCE-003

Core gate:

```text
diagnostic_code = CSV-NEXT-SOURCE-003
payload_available = false
```

の場合、同じvalidated `failure_roots` の parse/read pathだけを使用します。

`locality.affected_paths` や任意graph pathから新しい診断pathを発明しません。

SOURCE-001へdowngradeしません。

## TARGET-001

authority:

```text
core.gate()["target_failures"]
```

および同じ validated proof。

一target一row:

```text
path = target_key.removeprefix("path:")
reason = validated reason
```

reason enum は current Core/schema validator に従い、SI-06側で古い八理由表を別に再定義しません。

## EXPORT-001

symbol は:

```text
validated export_reexport_witness
validated export_observations
```

から `owner_module_id` を導出します。

gateへ自由に付いたsymbolやpublic bindingから逆算しません。

## entity LIMIT-005

一件の no-ref catalog row。

actual entity countは diagnostic rowではなく:

```text
run.record()["core_measurement"]
```

をauthorityにします。

## model-record LIMIT-005

`RejectedSemanticDecisionV3` の:

```text
failure.model_records
```

および nested run measurementを維持します。

entity countへ変換しません。

## PROTOCOL / runtime-only

run-v3 provenance の:

```text
stage
failure_code
```

をそのまま分類し、catalog固定rowを生成します。

semantic/source codeへrelabelしません。

---

# 12. first observable Red

最初のTDD behavior は **取得完了後の real parse/read root → public SOURCE-001** です。

planned test:

```text
test_post_acquisition_file_root_projects_catalog_source001
```

fixture:

```python
seal, assets, request, policy, wire = core_inputs_v3(tmp_path)
exclude_value_module_with_root_v3(wire, request, kind)
runtime = runtime_for_core_wire(seal, assets, request, policy, wire)
core = decide_semantic_candidate_v3(
    runtime.transport_candidate(),
    seal,
    assets,
)
run = retain_request_bound_run_decision_v3(
    runtime,
    semantic_decision=core,
)
```

`kind` は:

```text
parse_file
read_file
```

をparameterizeします。

既存Greenとして先に確認:

```text
Core outcome       = partial_safe
payload_available  = true
failed File reason = parse_file | read_file
source seal failure list = empty
```

つまり reader failure ではなく post-acquisition semantic failureです。

First Red は planned:

```text
project_public_diagnostics_v3(run)
```

が未存在で public rowへ到達不能なこと。

fixture construction error、import typo、collection failureを Red と数えません。

### minimum Green

この一件だけのために:

1. catalog read
2. nominal run-v3 owner check
3. parse/read root extraction
4. SOURCE-001 fixed row
5. independent validator

だけを実装します。

final publication owner、stderr limit、selected copyはこのcycleへ混ぜません。

---

# 13. diagnostic negative cycles

次の順で一つずつ Red→Green。

```text
nonlocal parse/read root -> SOURCE-003
selected failed target   -> TARGET-001 + exact reason
export failure           -> EXPORT-001 + validated Module symbol
entity budget            -> LIMIT-005 + run entity measurement
record limit 10001       -> LIMIT-005 + model-record measurement
model/proof rejection    -> PROTOCOL-001
runtime child failure    -> existing NODE/PROTOCOL/LIMIT code
```

各testは current Core/run fixtureを通し、直接 diagnostic objectをfactoryへ注入しません。

---

# 14. planned final owner API

`next_final_publication_v2_reference.py`:

```python
@dataclass(frozen=True, slots=True, init=False)
class RetainedFinalPublicationV2:
    ...

    def publication_candidates(
        self,
    ) -> RetainedRequestBoundPublicationCandidatesV3: ...

    def run_decision(
        self,
    ) -> RetainedRequestBoundRunDecisionV3: ...

    def publication_decision(self) -> dict[str, Any]: ...

    def domain_manifest(self) -> dict[str, Any]: ...

    def run_manifest(self) -> dict[str, Any]: ...

    def run_summary(self) -> dict[str, Any]: ...

    def stdout_result(self) -> dict[str, Any] | None: ...

    def stdout_bytes(self) -> bytes: ...

    def stderr_bytes(self) -> bytes: ...

    def artifact_bytes(
        self,
        format_name: Literal["semantic-json", "plantuml"],
    ) -> bytes | None: ...

    @property
    def exit_code(self) -> int: ...
```

factory:

```python
def retain_final_publication_v2(
    candidates: RetainedRequestBoundPublicationCandidatesV3,
) -> RetainedFinalPublicationV2:
    ...
```

唯一の caller input は `candidates` です。

禁止:

```text
run
Core
status
diagnostics
artifact map
selector
limit
count
hash
stdout bytes
stderr bytes
publication outcome
```

を別引数で受けること。

direct constructor は閉じます。

---

# 15. final owner の入力関係

factory冒頭:

```text
validate_request_bound_publication_candidates_v3
→ validate_request_bound_run_decision_v3
→ existing Core/runtime validators
```

を通します。

identity:

```text
candidates.run_decision() is final_owner.run_decision()
```

を必須にします。

fresh equal-content owner は拒否します。

---

# 16. lower capture は再実行しない

`candidates-v3` が既に所有する:

```text
capture_measurements.adapter_stdout
capture_measurements.adapter_stderr
```

を final owner が再検証します。

publication-v2 の measurement へ:

```text
allowed
measured_bytes
retained_bytes
```

を変換します。

`allowed` は当該 capture byte boundary の実measurementから導出します。

timeout/read/write/child protocol failureを「capture failure」に再分類しません。

特に finalizer は:

```text
adapter_stdout_chunks
adapter_stderr_chunks
adapter_stdout_limit
adapter_stderr_limit
```

を引数にしません。

旧 `finalize_publication_decision()` の再capture contractを新certificateへコピーしないこと。

---

# 17. response link

final `next-publication-decision/v2.response` は:

### ValidatedSemanticDecisionV3

同じ retained responseから:

```text
request_id
raw_sha256
model_digest
byte_length
```

を生成できます。

SOURCE-003 / TARGET-001 / EXPORT-001 / entity LIMIT-005 も Core自体は validated なので、このresponse linkを維持できます。

### RejectedSemanticDecisionV3

`response = null`

とします。

lower run-v3 の descriptor-only receiptは維持しますが、不正model/proofの `model_digest` を final semantic response authorityへ昇格させません。

### runtime-only failure

同じく:

```text
response = null
```

です。

---

# 18. requested artifact set

available Coreの場合:

```text
artifacts = candidates.artifacts()
```

のみ。

selectorで減らしません。

例:

```text
requested:
  semantic-json
  plantuml

selector:
  next:plantuml
```

でも persisted artifact set は:

```text
semantic-json
plantuml
```

の両方です。

SOURCE/TARGET/export/entity/rejection/runtime unavailableでは既存 candidates ownerが空tupleなので、finalizerもartifactを捏造しません。

---

# 19. domain projection

`next-domain-manifest-v2` は final ownerからのみ取得します。

### ValidatedSemanticDecisionV3

Coreが検証済みなので、overlap fieldsは:

```text
candidate semantic model
source seal
run analysis context
source inventory safe Project projection
coverage
compatibility-v3
run-v3 measurement
```

から導出します。

available branchは `project_public_semantic_document_v3()` と共通値が一致することを検証します。

unavailable branchでは public semantic artifactを作りませんが、validated Coreの:

```text
Project/coverage
target rows
source
request/config
budget measurement
```

は同じownerから安全に投影できます。

### Core rejection / runtime-only failure

unvalidated child model/proofをdomainへコピーしません。

public semantic collectionsはempty shellとし、request/source-owned Project metadataだけをsafe public contextとして使います。

`target_completeness=[]`。

record-limit actualは nested run measurementへ保持し、entity countへ変換しません。

---

# 20. status ownership

semantic/run outcome:

```text
complete
partial_safe
payload_unavailable
```

は run-v3 が所有します。

### normal publication success

domain status = semantic status。

### selected-copy failure

**domain semantic statusを変更しません。**

例:

```text
semantic outcome = complete
domain status     = complete
publication       = selected_artifact_unavailable
root run status   = incomplete
exit              = 3
```

partial-safeなら:

```text
domain status         = incomplete
domain incomplete_kind = partial_safe
publication            = selected_artifact_unavailable
root run status        = incomplete
exit                   = 3
```

### public stderr boundary failure

これは publication safety failure なので final public domain projectionだけ:

```text
status          = incomplete
incomplete_kind = payload_unavailable
payload_available = false
artifact_paths  = []
```

へ進めます。

ただし nested run-v3/Core recordは変更しません。

---

# 21. final selected stream construction

run contextの selectorだけを使用します。

```text
null
manifest
next:semantic-json
next:plantuml
```

### selector null

pre-copy candidate:

```text
canonical run-summary/v1 + LF
```

### manifest

pre-copy candidate:

```text
canonical run-manifest/v2 + LF
```

### available domain artifact

pre-copy candidate:

```text
candidate ownerが保持する exact artifact bytes
```

### semantic/domain unavailable

pre-copy candidate:

```text
canonical stdout-result/v2 + LF
```

TARGET branchだけ `target_failures` を持ちます。

SOURCE / export / entity / rejection / runtime-only を target unavailableへrelabelしません。

---

# 22. selected-copy measurement

configured authority:

```text
run.runtime_result()
   .request_frame()
   .record()["limits"]["max_selected_stdout_bytes"]
```

を使います。

factoryへlimit overrideを受けません。

実測:

```text
len(pre_copy_candidate)
```

で一度だけ判定します。

### exact

```text
measured = 16_777_216
allowed  = true
retained = exact full bytes
```

### +1

```text
measured       = 16_777_217
allowed        = false
retained_bytes = 0
partial bytes  = 0
```

その後 candidateを再render/re-measure/re-copyしません。

---

# 23. selected-copy failure

selected artifact / manifest candidateの +1 では:

```text
semantic Core/run status       unchanged
requested artifacts            unchanged
persisted semantic artifacts   unchanged
artifact descriptors           unchanged
publication outcome            selected_artifact_unavailable
root run status                incomplete
exit                           3
stdout                         stdout-result/v2
```

final diagnostic setへ:

```text
CSV-NEXT-LIMIT-003
scope = publication
```

を一件追加します。

これは domain semantic diagnosticではなく publication-level diagnosticです。

---

# 24. public diagnostic stderr の順序

selected-copy結果が確定してから final diagnostic setを一度決めます。

```text
base catalog diagnostics
+
publication LIMIT-003 if selected copy failed
```

その **最終集合全部** を:

```text
canonical JSON
+ LF per row
+ UTF-8
```

へencodeします。

その後に一回だけ:

```text
max_stderr_bytes = 65536
```

を測ります。

旧helperのように base stderr を一度測り、selected-copy後にもう一度測る二重measurementを新final certificateへ持ち込みません。

---

# 25. public stderr exact / +1

## exact

```text
encoded = 65_536
allowed = true
stderr  = entire JSONL
partial = 0
```

## +1

```text
encoded = 65_537
allowed = false
stderr  = b""
partial = 0
```

final manifest diagnostics は元集合を出さず:

```text
CSV-NEXT-LIMIT-003
scopeなし
```

一件だけにします。

この replacement rowをstderrへ出してはいけません。

publication:

```text
outcome = payload_unavailable
exit    = 3
artifacts persisted = none
```

nested Core/run identityは変更しません。

---

# 26. actual 64 KiB fixture

旧decision packetは authority ではありませんが、source/proof conflict解消前に作った **入力到達性と独立byte literal** は current catalog/wire semantics と整合する regression evidenceです。

SI-06では同じ構成を **V3 Core/run/candidates** に通し直します。

16 missing targets:

```text
p_i =
  "src/missing/" + two-digit i + "/"
  + ("a"*200 + "/") * 18
  + "b"*120
  + ".tsx"

i = 00..15
target = "path:" + p_i
```

各path:

```text
3757 bytes
```

proof / coverage:

```json
{
  "target_key": "...",
  "status": "failed",
  "record_ids": [],
  "reason": "missing"
}
```

を同じ16 targetへexactに構成します。

経路:

```text
real source seal
→ real request with 16 targets
→ semantic proof/coverage
→ retained runtime2
→ ValidatedSemanticDecisionV3
→ RetainedRequestBoundRunDecisionV3
→ RetainedRequestBoundPublicationCandidatesV3
→ planned public diagnostic projection
→ planned final owner
```

### independent literals

exact:

```text
diagnostic JSONL bytes:
65536

SHA-256:
702dbbfdd93207ea5e659026f9706d8278a3568eaf401394f57adfda56411216
```

+1 は最後のpath末尾を:

```text
"b"*121
```

へ変更。

```text
diagnostic JSONL bytes:
65537

SHA-256:
c9373a44926510bbf4508a8702e0f8f9b217764ea4f1f7979f342c61b3e3a08b
```

request target arrays の independent controls:

```text
exact:
60241 bytes
28ecb3b271908a668a6784f7dd13f1b0da87688ef1ac788bfd4d409ea2b36975

+1:
60242 bytes
202edea2fb3f5a9aeb2eca6f85c238d541c96c0fd9b4e083ad21e86efa53e583
```

empty stderr:

```text
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649c7810b?
```

**注意:** expected empty SHA は test で `hashlib.sha256(b"").hexdigest()` と既知標準値を比較し、上記 prose をoracleにしないこと。checked-in literalは正しい64-hexを一度独立生成して固定します。

overflow replacement row＋LF は既存evidenceで:

```text
349 bytes

f0ccb6a1a16b372801b650f05f8457d04468b7027980ef252c4bd29407cf5ad9
```

です。

replacementはmanifest用で、stderr bytesにはなりません。

---

# 27. actual selected-copy 16 MiB fixture

旧v2の:

```text
tests/contracts/next_publication_candidates_v2_fixtures.py
```

には actual source-bound 1000 Module corpusを長い合法repository pathで構築し、semantic JSONを 16 MiB / +1 へ到達させる test-only方法があります。

**旧V2 owner/certificateは再利用しません。**

SI-06 test fixtureとしてV3 siblingを作ります。

planned:

```text
tests/contracts/next_final_publication_v2_fixtures.py
```

### construction

1. real temp repository。
2. actual:
   ```text
   package.json
   tsconfig.json
   src/global.d.ts
   1000 real Card.tsx files
   ```
3. 各long pathは 4096-byte path上限内。
4. adapter retained asset headerは `0.2.0`。
5. real `SourceAcquisitionSeal`。
6. actual request-v2。
7. independently calculated Module/Fact IDs。
8. full discovered proof。
9. V3 Core。
10. run-v3。
11. candidates-v3。
12. test-side independent public-v3 recordを stdlib JSON/hashlib で綴る。
13. path prefix長と実context file bytesだけを調整し、expected semantic JSON exact bytesを:
    ```text
    16_777_216
    16_777_217
    ```
    にする。

artifact paddingは禁止です。

fake file metadataも禁止です。

実source path/file contentによってbytesを到達させます。

### controls

両caseで:

```text
private response < max_adapter_response_bytes
request bytes < max_encoded_stdin_bytes
model records <= 10000
entities = 1000
resolved entity budget = 1000
selected stdout limit = 16777216
Core payload_available = true
```

をassertします。

---

# 28. selected-copy first boundary tests

planned:

```text
test_selected_semantic_json_actual_16mib_is_copied_once
test_selected_semantic_json_actual_16mib_plus_one_keeps_artifact_and_emits_unavailable
```

exact:

```text
stdout bytes == candidate artifact exact bytes
descriptor len/hash == actual bytes
publication outcome == published
exit == 0
```

+1:

```text
candidate artifact still retained
persisted artifact descriptor unchanged
semantic run remains complete
selected retained bytes == 0
publication outcome == selected_artifact_unavailable
exit == 3
stdout is canonical stdout-result/v2
partial bytes == 0
```

producerのartifact bytesから expected artifact bytesを作りません。

test-side independent V3 record bytesとexact比較します。

---

# 29. summary / manifest selected branches

run-summaryはcurrent schema上小さいcontrol recordであり、16 MiB +1を人工small-limit overrideで作りません。

同様に `public_stderr_limit=1` や `selected_stdout_limit=len(x)-1` は **SI-06 acceptance evidence にしません**。

summary / manifestについては:

```text
actual candidate byte count
configured max_selected_stdout_bytes
one-copy identity
canonical bytes
```

を検証します。

境界+1が current legal inputで到達不能なら「small overrideで+1」と偽装せず、actual reachable artifact boundaryをSI-06のlarge-case証拠とします。

---

# 30. outer-v2 live projection rule

既存 schemas:

```text
next-domain-manifest-v2
next-publication-decision-v2
run-manifest-v2
stdout-result-v2
```

は変更しません。

`next-publication-decision-v2` の required exact refs:

```text
semantic_decision -> next-run-decision-v3
candidates        -> next-publication-candidates-v3
```

を live final ownerが必ず埋めます。

---

# 31. optional back-reference と循環回避

SI-05 の schema vectors は:

```text
domain.publication
root.next_publication
stdout.publication
```

の exact-ref resolution も検証していますが、それらは schema上 optional で、SI-05自身も「future single finalizer のcertificateではない」と明記しています。

live SI-06 bytesで final publication recordをこれらに再帰埋込すると:

```text
publication
→ stdout/result bytes
→ manifest/stdout-result
→ publication
```

という自己参照hash/copy cycleになります。

したがって live producer は:

```text
domain.decision      = run-v3 record       # 可
root.next_decision   = run-v3 record       # 可

domain.publication   = omitted
root.next_publication = omitted
stdout.publication   = omitted
```

を一貫して使用します。

final publication recordとの結合は Pythonの `RetainedFinalPublicationV2` object identity と independent validator が担います。

SI-05 schema ref vectorは変更しません。

**もし current product contract がこれら optional publication backrefs の live populationを必須と要求すると判明した場合は Stop。** 自己参照hashの新ルールをこのunitで発明しません。

---

# 32. publication-v2 record

final owner は少なくとも:

```text
schema
version
semantic_decision
candidates
response
artifacts
stdout
stderr
measurements
publication_outcome
exit_code
seal
```

を生成します。

### artifacts

安全にpersistする actual bytes＋six-field descriptor。

selected-copy failureでも保持。

public-stderr failureではempty。

### stderr

```text
available
bytes_base64
size_bytes
sha256
diagnostics_sha256
```

`diagnostics_sha256` は final diagnostic row set の canonical logical representationから独立再導出します。

raw child stderrとは無関係です。

### measurements

```text
adapter_stdout
adapter_stderr
public_stderr
selected_stdout
```

すべて native integer。

---

# 33. final seal

SI-06で新fieldは追加しません。

現行schemaの:

```text
seal.algorithm
seal.sha256
seal.preimage_sha256
```

を使用します。

implementation choiceとして、自己参照を避けるため logical preimage と exact-byte sealを分離します。

### logical preimage

```text
run-v3 record
candidates-v3 record
validated response link or null
artifact descriptors
selector
all four measurements
final diagnostic rows
publication_outcome
exit_code
```

をCJ15でhashし:

```text
preimage_sha256
```

とします。

### exact-byte owner seal

次のdigest/sizeを別のclosed objectとしてhashします。

```text
preimage_sha256
artifact exact size/hash map
domain manifest CJ15 hash
run-manifest exact LF-byte hash
run-summary exact LF-byte hash
stdout exact byte hash
stderr exact byte hash
```

これを:

```text
seal.sha256
```

とします。

validatorはこの二hashをproducer helperを呼ばず再導出します。

この選択は schema field/Requirement outcomeを変更せず、「final ownerが全public bytesとmeasurementsを一度sealする」という Current Designを具体化するものです。

---

# 34. root/domain/summary projection

全getterは final owner に保持した immutable bytes/recordから fresh projectionを返します。

下流へ:

```text
status
diagnostics
measurements
artifact map
selected bytes
```

を別引数で渡しません。

## domain

semantic/Core statusを所有。

selected-copy失敗でsemantic statusを変更しない。

public-stderr failureだけ publication-level payload-unavailable projection。

## root run-manifest

run-level public status:

```text
semantic complete + publication success     -> complete / 0
semantic partial                            -> incomplete / 3
semantic unavailable                        -> incomplete / 3
selected-copy failure                       -> incomplete / 3
public-stderr failure                       -> incomplete / 3
```

## run-summary

selectorなしは:

```text
code-structure-viz.run-summary/v1
```

canonical JSON＋LF。

## stdout-result-v2

以下だけ:

```text
semantic/domain unavailable
selected-copy unavailable
```

で生成。

TARGETだけ `target_failures`。

SOURCE/export/entity/protocol/runtimeはgeneric domain unavailable。

---

# 35. publication diagnostics placement

### ordinary semantic diagnostic

domain diagnostics + root diagnostics + stderrに同じ catalog-owned rows。

### selected-copy failure

domain semantic diagnosticsは不変。

root diagnostics / stderr:

```text
original diagnostics
+
CSV-NEXT-LIMIT-003 scope=publication
```

### public stderr overflow

final domain/root diagnostics:

```text
CSV-NEXT-LIMIT-003
```

一件のみ。

scopeは付けません。

stderrは空。

元のdiagnostic rowsはfinal public payloadへ流しません。

---

# 36. target rows

TARGET-001 run の:

```text
gate.target_failures
coverage.target_completeness
```

は同じ V3 Core proofへ結合します。

final owner は:

```text
domain.coverage.target_completeness
stdout-result-v2.target_failures
diagnostic-v1 reason
```

を independently cross-checkします。

target failureを SOURCE / LIMIT / PROTOCOL branchへ流用しません。

public-stderr publication failureが後から起きても、validated coverage rows自体を捏造/消去して別semantic resultへ変えません。

---

# 37. positive coverage

最低限:

1. complete available。
2. localized `parse_file` partial-safe。
3. localized `read_file` partial-safe。
4. owner-closed nonFile failure partial-safe。
5. all-files-private Project empty membership。
6. complete-empty。
7. nonprogram safe File。
8. selection-only complete。
9. SOURCE-003 nonlocal unavailable。
10. TARGET-001。
11. EXPORT-001。
12. entity LIMIT-005。
13. model-record 10001 rejection。
14. PROTOCOL-001 rejection。
15. lower runtime-only failure。
16. requested JSON+PlantUML with selector selecting one。
17. actual public stderr 65,536。
18. actual public stderr 65,537。
19. actual selected JSON 16 MiB。
20. actual selected JSON 16 MiB+1。

---

# 38. negative coverage

## owner

```text
foreign equal-content run
foreign candidates owner
foreign Core through run
foreign runtime
foreign seal/assets
```

を拒否。

## cache-aligned rehash

次を変更しhash/cacheを整合させても拒否:

```text
diagnostic code/path/reason
candidate descriptor
capture count
selected measurement
response hash/length
publication status
exit
domain status
manifest diagnostic
stdout-result target row
seal digest
```

independent validatorは retained ownersから再導出します。

## native types

拒否:

```text
version = 2.0
exit_code = 3.0
size_bytes = 1.0
measured_bytes = true
retained_bytes = false
line = 1.0
capture eof = 1
```

int/bool/floatをcoerceしません。

## privacy

最終 public tree / bytes 全体をscanし、次を拒否:

```text
content_base64
source body
private proof
failure_root payload
raw child stderr
raw private response body
absolute path
tmp path
cwd
PID
PGID
FD
OS exception message
compiler raw message
```

validated public semantic artifact bytesは別途許可されたpublic payloadです。

---

# 39. existing legacy helper の扱い

`tests/contracts/next_reference_validation.py` の:

```text
decision_public_diagnostics
render_public_diagnostic_stderr
copy_selected_stdout
PublicationBoundaryDecision
finalize_publication_decision
publication_boundary_seal
```

は **新certificateとして呼ばない**。

再利用可能:

```text
catalog semantics
canonical JSONL semantics
all-or-none stderr arithmetic
selected-copy all-or-none arithmetic
six-field descriptor meaning
single-owner/seal idea
```

です。

新 run3/Core3 ownerを旧 `NextRunDecision`へ変換してこれらを通すのは禁止です。

---

# 40. TDD sequence

各cycleで intended Red → 同じtestの minimum Green。

| cycle | behavior |
|---:|---|
| 1 | parse/read post-acquisition root → SOURCE-001 |
| 2 | nonlocal source → SOURCE-003 |
| 3 | TARGET rows/reason |
| 4 | EXPORT owner symbol |
| 5 | entity / record LIMIT-005の区別 |
| 6 | protocol/runtime failure identity |
| 7 | immutable final owner basic complete |
| 8 | partial-safe final domain/root |
| 9 | semantic unavailable manifest-only |
| 10 | actual 65,536 stderr |
| 11 | actual 65,537 stderr → empty/LIMIT003 |
| 12 | selected exact artifact one copy |
| 13 | actual 16MiB selected |
| 14 | actual 16MiB+1 → descriptor retained/unavailable |
| 15 | requested set not shrunk by selector |
| 16 | root/domain/summary/stdout exact owner projection |
| 17 | foreign owner / rehashed cache |
| 18 | float/bool/native type |
| 19 | privacy |
| 20 | outer-v2 schema validation + legacy regressions |

already-Green SI-03/04/05 behaviorを新Redと呼びません。

---

# 41. proposed test names

```text
test_post_acquisition_file_root_projects_catalog_source001
test_nonlocal_file_root_keeps_source003_unavailable
test_target_diagnostic_rows_are_bijective_with_validated_core_failures
test_export_diagnostic_uses_validated_witness_owner
test_entity_and_record_limits_keep_distinct_measurement_authority
test_protocol_and_runtime_failures_keep_existing_catalog_identity

test_final_publication_is_created_only_from_candidates_v3
test_final_publication_preserves_partial_safe_semantic_status
test_final_publication_projects_source003_without_artifacts
test_final_publication_actual_stderr_65536_is_emitted_whole
test_final_publication_actual_stderr_65537_emits_zero_partial_bytes
test_final_publication_selected_json_16mib_copies_once
test_final_publication_selected_json_16mib_plus_one_preserves_artifact_descriptor
test_final_publication_selector_never_shrinks_requested_artifacts

test_final_publication_rejects_equal_content_foreign_candidates
test_final_publication_rejects_rehashed_cache_aligned_substitution
test_final_publication_rejects_float_bool_measurements
test_final_publication_contains_no_private_source_proof_or_child_stderr
test_final_publication_live_projections_validate_against_outer_v2_schemas
```

---

# 42. focused commands

最初のRed/Green:

```bash
uv run --locked --group dev pytest \
  tests/contracts/test_next_public_diagnostic_v3.py \
  -q -k post_acquisition_file_root
```

diagnostic unit:

```bash
uv run --locked --group dev pytest \
  tests/contracts/test_next_public_diagnostic_v3.py \
  -q
```

final owner:

```bash
uv run --locked --group dev pytest \
  tests/contracts/test_next_final_publication_v2.py \
  -q
```

actual large boundaries:

```bash
uv run --locked --group dev pytest \
  tests/contracts/test_next_final_publication_v2.py \
  -q -k 'actual_stderr_65536 or actual_stderr_65537 or selected_json_16mib'
```

large caseをmark/deselect/skipしてGreen扱いしません。

---

# 43. SI-03〜05 dependency regression

```bash
uv run --locked --group dev pytest \
  tests/contracts/test_next_source_inventory_v3.py \
  tests/contracts/test_next_semantic_core_v3.py \
  tests/contracts/test_next_public_semantic_v3.py \
  tests/contracts/test_next_public_artifact_v3.py \
  tests/contracts/test_next_provenance_v3.py \
  tests/contracts/test_next_run_decision_v3.py \
  tests/contracts/test_next_publication_candidates_v3.py \
  tests/contracts/test_next_public_family_v3_schemas.py \
  -q
```

---

# 44. lower runtime / catalog regression

```bash
uv run --locked --group dev pytest \
  tests/contracts/test_next_runtime_result_v2.py \
  tests/contracts/test_next_observed_response_receipt_v2.py \
  tests/contracts/test_json_schemas.py \
  -q
```

legacy wire-independent publication semantics:

```bash
uv run --locked --group dev pytest \
  tests/contracts/test_next_contracts.py \
  -q
```

この旧test群のGreenを新final-owner certificateの代わりにはしません。

---

# 45. existing domains

```bash
uv run --locked --group dev pytest \
  tests/contracts/test_python_goldens.py \
  tests/contracts/test_sqlalchemy_goldens.py \
  -q
```

golden updateで通しません。

---

# 46. required broad gates

```bash
uv run --locked --group dev pytest tests/contracts -q --tb=short
```

続いて:

```bash
uv run --locked --group dev pytest -q
```

これらは SI-06 regression evidenceであり、全A02/A03認定ではありません。

---

# 47. statics

```bash
uv run --locked --group dev ruff check .
uv run --locked --group dev ruff format --check .
uv run --locked --group dev mypy src tests
```

---

# 48. SpecDock

repo-local skillに従い、先に current help:

```bash
python3 spec-dock/scripts/spec-dock --help
python3 spec-dock/scripts/spec-dock sync --help
python3 spec-dock/scripts/spec-dock validate --help
```

caller指定optionがcurrent helpに存在することを確認してから:

```bash
python3 spec-dock/scripts/spec-dock sync --no-github --no-update-active
python3 spec-dock/scripts/spec-dock validate
```

CLI failureをmetadata手編集で迂回しません。

---

# 49. diff guards

SI-06 reference unitでは次を期待します。

```bash
git diff --check

git diff --name-only \
  af6f5d33f9487a33dabf2ddfe41df85b3d8267fb..HEAD \
  -- src pyproject.toml uv.lock schemas
```

期待:

```text
empty
```

特に:

```text
src/**          unchanged
pyproject.toml  unchanged
uv.lock         unchanged
schemas/**      unchanged
```

です。

outer schema変更が必要なら Stop。

---

# 50. checkpoint boundary

実装中checkpointは current branch内だけです。

stage:

```bash
git add -- \
  tests/contracts/next_public_diagnostic_v3_reference.py \
  tests/contracts/next_public_diagnostic_v3_validation.py \
  tests/contracts/next_final_publication_v2_reference.py \
  tests/contracts/next_final_publication_v2_validation.py \
  tests/contracts/next_final_publication_v2_fixtures.py \
  tests/contracts/test_next_public_diagnostic_v3.py \
  tests/contracts/test_next_final_publication_v2.py
```

実際に必要なtracked evidence pathがSpecDock workflowで生成された場合だけ、その exact pathを別の `git add --` で追加します。

禁止:

```text
git add .
git add -A
alternate index
--no-verify
force
history rewrite
new branch
PR
merge
```

commitは現在許可された commit workflowをそのまま使い、hook bypass/manual fallbackへ切り替えません。

push:

```bash
git push -- origin iss-00008-generate-nextjs-component-snapshots
```

non-forceのみ。

---

# 51. fresh SI-06 Code Review Strict

local required evidenceとclean/pushed candidateが一致した後だけ実行します。

review range:

```text
base:
af6f5d33f9487a33dabf2ddfe41df85b3d8267fb

head:
final clean pushed SI-06 candidate
```

review:

```text
fresh independent Code Review Strict
GPT-5.6 Sol
Extra High
```

既存 authorized workflowを使います。確認していない wrapper commandを本ブリーフでは捏造しません。

SI-06認定条件:

```text
P0 = 0
P1 = 0
review_status = pass
```

P2/P3や既知SI-04 report-only findingは自動remediation/backlog/re-review loopにしません。

subagent、UI job progress monitoring、mechanical wait質問を使用しません。

---

# 52. stop conditions

以下のどれかが必要になったら実装を停止します。

1. `next-domain-manifest-v2` / `next-publication-decision-v2` / `run-manifest-v2` / `stdout-result-v2` の変更。
2. catalog code/message/ref permissionの追加・変更。
3. optional publication backrefをlive bytesへ必須化する新wire decision。
4. self-referential manifest/publication hashの新fixed-point規則。
5. `ValidatedSemanticDecisionV3`をV2 certificateへcast。
6. run/candidates owner以外からstatus/count/hashを注入。
7. public diagnosticを作るためのfake File taint/direct failure。
8. SOURCE-003をSOURCE-001へ変更。
9. TARGET/export/limit/protocol/runtime codeを別codeへrelabel。
10. pre-seal reader prefixの実装。
11. new ASSET failure policy/code。
12. run-level usage/fatal/interrupted policy変更。
13. SI-04 P2/P3 remediation。
14. production `src/**`変更。
15. TypeScript/Node/OS/CLI/package/dependency/license変更。
16. old schema/KAT/goldenを書き換えないとGreenにできない。
17. actual 64KiB / 16MiB boundaryをsmall overrideで代用する必要。
18. raw child stderr/source/private proof/host stateをpublic fieldへ出す必要。

この場合は exact conflicting propositions と必要decisionを bounded decision packageとして返し、SI-06 ready/completeを主張しません。

---

# 53. completion conditions

SI-06 は同一 clean pushed candidateで次が全部成立したときだけclose可能です。

- `parse_file` / `read_file` real post-acquisition rootsがSOURCE-001になる。
- nonlocal sourceはSOURCE-003のまま。
- TARGET reason rowsがCore proofと一対一。
- export symbolがvalidated witness owner。
- entity countとmodel-record countを混同しない。
- protocol/runtime failureをrelabelしない。
- catalog fixed attributes/messageだけを使用。
- final factoryの唯一の入力が candidates-v3。
- direct constructorが閉じている。
- requested artifactsをselectorで削らない。
- child captureを再実行しない。
- response linkはvalidated V3 Coreだけ。
- rejected/runtime responseをsemantic responseへ昇格しない。
- actual stderr 65,536 whole emission。
- actual stderr 65,537 → stderr empty / partial0 / LIMIT003一件。
- overflow replacement rowをstderrへ出さない。
- selected copyを一回だけ測定。
- actual 16MiB selected artifactをwhole copy。
- actual 16MiB+1でpartial0。
- selected overflow時もartifact descriptor/semantic status不変。
- publication/rootはincomplete/exit3。
- final ownerだけがdomain/root/summary/stdout/stderr/exitを投影。
- target rowsはtarget branchだけ。
- native int/bool typeを厳密に維持。
- foreign/equal-content/cache-aligned owner substitution拒否。
- source/proof/raw stderr/host state非公開。
- outer four v2 schemasがlive projectionsをaccept。
- SI-05 ten schemas byte/meaning不変。
- Python/SQLAlchemy goldens不変。
- `src/**`、deps、lock、schemas差分なし。
- focused tests Green。
- actual large tests Green。
- SI-03/04/05 regressions Green。
- contracts/full pytest Green。
- Ruff/format/mypy Green。
- SpecDock Green。
- `git diff --check` Green。
- clean current branchへnormal commit/non-force push。
- original base `af6f5d33f9487a33dabf2ddfe41df85b3d8267fb` から final candidate 全rangeの fresh SI-06 Strictが pass / P0=P1=0。

ここまでが **SI-06 catalog-owned diagnostic/stderr + single final publication owner** の範囲です。

次は依然として別unitです。

```text
SI-07 reader-owned prefix
unadopted ASSET decision
all-A02 closure
A03
production TypeScript / OS / CLI
package/offline/license
Final / Issue #8 acceptance
```
