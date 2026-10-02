# Issue #8 Plan SI-03 実装ブリーフ

## 1. 実装判断

Plan SI-03 は、現在の authoritative specification の範囲内で実装可能です。必須依存の欠落、authority conflict、仕様変更を必要とする blocker は、検証した `ce0edaa8fe63e79523fe7ad1dcb4b0a39dc02dce` では確認されませんでした。

GitHub connector で `chemitaro/code-structure-viz` の `iss-00008-generate-nextjs-component-snapshots` を直接解決し、作業開始時と最終確認時の branch tip がともに次の full SHA と完全一致することを確認済みです。

```text
ce0edaa8fe63e79523fe7ad1dcb4b0a39dc02dce
```

この SHA を **SI-03 original unit base** とします。現在の commit はレビュー原本 JSON、レビュー evidence、`design.md` / `plan.md` / `report.md` の状態・次工程ポインタだけを変更しており、owner-closed Option A の authority meaning 自体は `bcae9548ef515e4a7662de1ad648171622c6a437` で Strict Spec Review pass 済みの仕様から変更されていません。

repository root の `AGENTS.md` はこの commit には存在しません。root contents を確認したうえで `.agents/skills/spec-dock/SKILL.md` を repository-local instruction として確認済みです。SpecDock 操作では CLI の current help と canonical files を authority とし、`sync` / `validate` 後の state verification を必要とします。

添付 `brief.md` が要求する「whole specification set と verified commit の実装を根拠にし、existing behavior と proposed work を区別し、TDD と observable completion evidence を具体化する」という契約に従います。:chatgpt-content-reference{index="0"}

実装者指定は **GPT-6.1 Sol / Max** です。これは作業分解の粒度を高く保つための caller guidance としてのみ扱い、実 runtime/model identity の検証済み事実とは扱いません。

---

## 2. SI-03 の目的と非目的

SI-03 の目的は、新しい public/Core v3 全体を作ることではありません。**同じ v2 request/source owner と transport candidate に結合した source/proof reference seam を一つだけ成立させること**です。

完了時に機械的に観測できる必要があるものは次です。

| 項目 | SI-03 で成立させる保証 |
|---|---|
| acquired inventory | 同じ `SourceAcquisitionSeal` / `RetainedRequestFrameV2` が所有する全 Project/File。再読込、child 自由 metadata、safe subset からの再構成を禁止 |
| discovered source rows | proof の Project/File row は `record` key 自体を持たず、親 request から完全 record を解決。`record:null` も object payload も拒否 |
| full File/Module base | acquired program File と full discovered Module の正規 `(project_id, path)` ownership を、public model の有無より先に解決 |
| Module eligibility | public model の存在を根拠にせず、full discovered base、既存 taint/disposition/selection semantics から `E_module` を導出 |
| File partition | 全 acquired File を `published` / direct `failed` / `excluded` の排他的完全 partition にする |
| reason | direct parse/read、tainted、owner failure、既存 selection/unsupported reason の優先順を再導出 |
| Project two views | proof/acquired Project は全 membership、model Project は同じ Project の `F_safe` filter |
| count | acquired project/file/bytes、proof discovered、published/proof-only/accounted records、published Module/Component/entity を実 array / retained bytes から測定 |
| partition identity | `next-source-inventory-safe-subset-v1` の exact 3-key preimage から CJ15/SHA-256 を独立再導出 |

**SI-03 では認定しないもの**は、mandatory root seed の完全性、全 causal edge、taint fixed point の正当性、source-graph locality、TARGET-001 routing、export failure、model-record/entity budget の受入判定、`ValidatedSemanticDecisionV3`、compatibility/public/provenance/run/publication v3、actual TypeScript、OS process、CLI、package/wheel/sdist です。これらは SI-04 以降の gate に残します。

したがって SI-03 では proof の `taints` / failure roots / existing selection disposition を source partition の入力として検査できますが、それらが full roots/causal graph から正しく生成されたことまでを certification してはいけません。そこを `validate_proof()` や `_derived_taint_fixed_point()` で丸ごと通すと SI-04 を先取りします。

---

## 3. authority と実装境界

実装中は次の優先順位を固定します。

1. `requirement.md` の Current SI requirements。
2. `design.md` の `SI: Source inventory / safe subsetのtarget design`。
3. `plan.md` の `SI-03 source/proof reference seam`。
4. accepted ADR:
   - `artifacts/20261002t001435z-adr-issue8-source-inventory-safe-subset.md`
   - `artifacts/20261002t041350z-adr-issue8-owner-closed-file-module-publication.md`
5. `docs/contracts/next-semantic-admission-v3.md`。
6. downstream shape/boundary確認用の `next-semantic-v3.md` と `next-compatibility-v3.md`。
7. `20261002t044942z-disc-owner-closed-spec-review-pass.md` は gate evidence であり、新しい normative rule ではない。

特に `next-semantic-admission-v3.md` の以下を変えてはいけません。

```text
F_source_safe = F − T

F_safe =
  (F_source_safe − F_program)
  ∪
  { f ∈ F_source_safe ∩ F_program | owner(f) ∈ E_module }
```

File disposition の優先順位も固定です。

| 優先 | 条件 | disposition / reason |
|---:|---|---|
| 1 | File 自身に対応する validated `parse_file` / `read_file` direct root | `failed / <root kind>`。両方なら既存 `TAINT_ORDER` に従い `parse_file` 優先 |
| 2 | File 自身が tainted、direct failure ではない | `excluded / tainted` |
| 3 | File は untainted、owner Module が failure/taint により非公開 | `excluded / failed` |
| 4 | File は untainted、owner Module が既存 selection/unsupported により非公開 | `excluded / not_selected`, `target_excluded`, `unsupported` の立証済み reason をそのまま使用 |
| 5 | source-safe かつ owner-closed | `published`、reason なし |

Module の failure を File の fake `parse_file` / `read_file`、fake File taint、逆向き Module→File causal edge に変換してはいけません。

---

## 4. 現在存在する seam と再利用方針

### 再利用する existing symbols

以下は verified commit に実在します。

| path / symbol | SI-03 での用途 |
|---|---|
| `tests/contracts/next_runtime_v2_reference.py::RetainedExecutionAssets` | immutable asset owner |
| `retain_execution_assets_v1()` | 新 `0.2.0` test-only asset bytes の保持 |
| `RetainedExecutionAssets.adapter_identity()` | retained header/version/hash から adapter identity を取得 |
| `RetainedRequestFrameV2` | same-parent request owner |
| `build_request_frame_v2()` | `SourceAcquisitionSeal` + retained assets から v2 request を生成。disk reopen 禁止を既に実装 |
| `ValidatedTransportCandidateV2` | SI-03 へ渡す typed transport owner |
| `retain_transport_candidate_v2()` | request/response/observation の既存 data-only join |
| `next_runtime_v2_validation.validate_request_source_binding_v2()` | request の Project/File/bytes/roles を source seal へ独立 join |
| `validate_request_frame_v2()` | request/source/assets owner identity、canonical bytes、request ID の再検証 |
| `validate_response_request_v2()` | retained response を同じ request/source/assets へ join |
| `next_reference_validation.COLLECTIONS` | v1 collection vocabulary を維持 |
| `TAINT_ORDER`, `TAINT_ORDER_INDEX` | direct File reason の既存優先順 |
| `identity_preimage()`, `recompute_record_id()` | Project/File/Module の既存 identity を変更せず再検証 |
| `canonical_json_bytes()`, `digest()` | pinned Unicode 15 NFC / compact JSON / SHA-256 の既存 codec |
| `_is_program_file()` | request role から `F_program` を決める既存意味 |
| `_record_references()` | private/public reference closure の record-level ID 抽出 |
| `response_model_record_counts()` | published/proof-only/accounted の既存 wire-independent count semantics |

underscore symbol は `tests/contracts` 内の reference implementation であることを理解した上で限定利用します。production API へ昇格させません。

### SI-03 の certificate として使用してはいけない existing symbols

次は旧 v2 全 Core の certificate なので、SI-03 の成功条件として丸ごと呼んではいけません。

```text
next_runtime_v2_validation.validate_semantic_candidate_v2()
next_reference_validation.validate_model()
next_reference_validation.validate_proof()
next_reference_validation._derived_taint_fixed_point()
next_reference_validation.validate_source_failure_locality()
next_runtime_v2_reference.decide_semantic_candidate_v2()
```

特に `validate_semantic_candidate_v2()` は旧仕様の「全 request File == public model File」を検査するため、owner-closed v3 seam を旧 v2 exception で通す用途には使用できません。

`SourceFailureLedger.from_seal` の locality 意味も維持対象ですが、SI-03 で locality pass を認定してはいけません。SI-04 の full Core gate で接続します。

---

## 5. 新規作業対象

verified commit の `tests/contracts/` を確認した結果、次の三 path は **現在存在しません**。

```text
tests/contracts/next_source_inventory_v3_reference.py
tests/contracts/next_source_inventory_v3_validation.py
tests/contracts/test_next_source_inventory_v3.py
```

SI-03 の通常差分はこの三ファイルだけに閉じます。既存ファイル変更が必須に見えた場合は、その場で「新仕様が必要なのか」「単に新 seam 内へロジックを置けるのか」を再確認し、後述の停止条件に該当するなら実装範囲を広げません。

### 提案する新規 symbols

以下は **proposed API** であり、現在の repository に存在するとは扱いません。

`next_source_inventory_v3_reference.py`:

```python
SOURCE_INVENTORY_PROFILE_ID = "next-source-inventory-safe-subset-v1"

class SourceInventoryCountsV3: ...
class FileDispositionV3: ...
class ValidatedSourceInventorySeamV3: ...

def retain_source_inventory_seam_v3(
    candidate: ValidatedTransportCandidateV2,
    seal: SourceAcquisitionSeal,
    assets: RetainedExecutionAssets,
) -> ValidatedSourceInventorySeamV3: ...
```

`ValidatedSourceInventorySeamV3` は名前に `Validated` があっても **Core/public certificate ではありません**。docstring に `SI-03 source/proof seam only; not ValidatedSemanticDecisionV3/public admission` を明記します。direct constructor を閉じ、factory だけから生成する既存 reference-owner pattern を維持します。

最低限の観測 surface は次で十分です。

```python
request_id: str
partition_fingerprint: str

transport_candidate() -> ValidatedTransportCandidateV2
source_seal() -> SourceAcquisitionSeal
execution_assets() -> RetainedExecutionAssets

eligible_module_ids() -> tuple[str, ...]
safe_projects() -> tuple[dict[str, Any], ...]
safe_files() -> tuple[dict[str, Any], ...]
file_dispositions() -> tuple[FileDispositionV3, ...]
counts() -> SourceInventoryCountsV3
```

mutable dict/list を内部 authority にしないため、既存 reference owners と同様、canonical bytes または immutable tuples で保持し、getter は fresh projection を返します。

`next_source_inventory_v3_validation.py`:

```python
class SourceInventoryInvalidErrorV3(ValueError):
    reason: str

def validate_source_inventory_seam_v3(
    value: ValidatedSourceInventorySeamV3,
) -> None: ...
```

内部 decomposition は次を推奨します。

```python
_resolve_discovered_records_v3(...)
_validate_full_module_ownership_v3(...)
_derive_module_eligibility_v3(...)
_derive_file_partition_v3(...)
_project_safe_projects_v3(...)
_validate_reference_closure_v3(...)
_derive_source_inventory_counts_v3(...)
_derive_partition_fingerprint_v3(...)
```

これらの名前も proposed です。validation 側は producer の cached partition/count/hash helper を expected-value oracle として呼ばず、same retained owners から独立再導出します。

`SourceInventoryInvalidErrorV3.reason` は新しい public reason vocabulary を作りません。既存の rejection label だけを使います。

```text
file_correspondence
project_correspondence
proof_source_owner
proof_module_owner
proof_references
model_proof
source_inventory_partition
```

public diagnostic code の発行は SI-03 の責務ではありません。後続 Core での invariant rejection は既存 `CSV-NEXT-PROTOCOL-001` のままです。

---

## 6. reference fixture: 0.2.0 を old KAT から分離する

既存 `tests/contracts/test_next_trusted_environment_v2.py::profile_members()` は adapter body を次に固定しています。

```text
// CodeStructureViz-Adapter-Version: 0.1.0
```

`test_next_request_frame_v2.py` の known-answer request も `adapter_version == "0.1.0"` を明示しているため、これを書き換えてはいけません。

新テスト内に test-local fixture を作ります。例:

```python
def source_inventory_assets_v3() -> RetainedExecutionAssets:
    members = profile_members()
    members[ENTRYPOINT_MEMBER] = (
        "adapter",
        b"// CodeStructureViz-Adapter-Version: 0.2.0\n",
    )
    return retain_execution_assets_v1(members)
```

その asset owner から既存経路をそのまま通します。

```text
source_inventory_assets_v3()
  -> trusted_environment_manifest_v2(assets)
  -> sealed_source_fixture_v1(...)
  -> analysis_context_fixture_v2(...)
  -> build_request_frame_v2(...)
  -> policy_fixture() を actual request/assets identity へ更新
  -> shape_wire(request) を fixture scaffold として使用
  -> v3 source/proof case に必要な model/proof だけ構成
  -> retain_response_frame_v2(...)
  -> reference_process_observation_v2(...)
  -> retain_transport_candidate_v2(...)
  -> retain_source_inventory_seam_v3(...)
```

`schemas/next-adapter-request-v2.schema.json` の `adapter_version` は stable SemVer pattern で、`0.2.0` を schema 上受理できます。response control も request の actual adapter version を echo/join する既存経路です。したがって旧 `0.1.0` request KAT を改名・再hash・上書きする必要はありません。

`shape_wire()` は既存コメントどおり「synthetic echo-only candidate」であり、Core certificate ではありません。fixture scaffolding としてのみ使用します。

---

## 7. source/proof seam の導出順序

### 7.1 owner preflight

最初に exact type と owner join を閉じます。

- `candidate` は exact `ValidatedTransportCandidateV2`。
- `seal` は candidate request が実際に bind された complete `SourceAcquisitionSeal`。
- `assets` は request が実際に bind された `RetainedExecutionAssets`。
- `validate_request_frame_v2()` と `validate_response_request_v2()` で同じ owner を再検証。
- `payload["model_digest"] == digest(payload["model"])` を再検証。
- free request dict、duck object、別 seal、別 asset set から seam を mint しない。

early reader prefix は `SourceAcquisitionSeal` ではないためここで admission できません。N11 をこの型境界で閉じます。

### 7.2 full discovered base `D`

`proof["discovered_records"]` から一意の full base を作ります。

Project/File:

- `record` key が **存在しないこと**を検査する。`row.get("record") is None` では不十分。
- `record:null` も object payload も拒否。
- `record_id` は request の acquired Project/File に必ず存在。
- Project は request の full acquired membership を使う。
- File は request File から `content_base64` だけを除いた record を使う。
- path/roles/effective_role/size/hash/project ownership を request から自由補完し直さず、same request と完全一致させる。

その他の collection:

- public model に同 ID があるなら `record` key を省略し、その model record に join。
- model にないなら `record` object 必須。
- proof-only record の ID/kind/preimage を `recompute_record_id()` で確認。
- duplicate ID、collection-kind mismatch、published record の payload 二重記載を拒否。

この段階で `M ⊆ D`、Project/File の全 acquired ID が D に一度ずつ存在することを保証します。

### 7.3 full File→Module ownership

public Modules を見る前に full discovered `modules` を indexing します。

```text
key = (project_id, path)
```

正常 seam では、

- Module は必ず acquired **program File** を一件 owner に持つ。
- non-program File に Module が存在したら拒否。
- program File の正規 Module は正常 available base で一件。
- Module の missing/duplicate を File と同時に model から省略して隠せない。

selected-target cardinality の旧例外をここで available success に変えてはいけません。missing/duplicate がその narrow target route に該当し得ても、SI-03 は TARGET-001 を発行せず、**source seam success object を生成しない**ところまでに留めます。typed target routing は SI-04 です。

### 7.4 `E_module`

`E_module` は submitted public `model["modules"]` から作りません。

full discovered Module を基準に、各 Module の既存 proof state から publication eligibility を導出します。

- taint/failure がある Module: ineligible。
- legal `not_selected` / `target_excluded` / `unsupported`: ineligible、既存 reason を保持。
- taint/failure/selection exclusion がなく source/full-base 上 publishable: eligible。
- public `model["modules"]` の ID 集合は、この独立 `E_module` と exact equality を要求。

ここで taint が正しい root/causal fixed point かどうかは認定しません。SI-03 が認定するのは **その retained proof state に対する publication eligibility と source owner closure** です。

### 7.5 File partition

`F` は request の全 acquired File IDs です。

`F_program` は `_is_program_file(request_file)` だけから決めます。

direct failed File は、少なくとも同じ File path に結合する `parse_file` / `read_file` root があり、File 自身が tainted であることを要求します。両 kind がある場合は `TAINT_ORDER` の既存順序で一つに決めます。

その後、仕様式どおり `F_safe` / `F_failed` / `F_excluded` を計算し、

```text
F = F_safe ⊎ F_failed ⊎ F_excluded
```

を ID 集合として検証します。

提出された、

- `model["files"]`
- `proof["failed"]` の File rows
- `proof["excluded"]` の File rows

は derived partition と完全一致させます。count の一致だけでは成功にしません。

特に P07 では、nonFile root により Module のみ tainted なら、

```text
File taints = []
Module taints != []
File disposition = excluded / failed
```

です。File に `tainted` を付けたり、File を `failed / parse_file` にしたりしてはいけません。

### 7.6 Project safe projection

Project 自体は全 acquired Project を一件ずつ保持します。

model Project は request Project と比較し、

- `file_ids` 以外は完全一致。
- `file_ids` は acquired `file_ids` を `F_safe` で filter した sorted IDs。
- proof 側の reconstructed Project は full acquired `file_ids`。
- 全 File が proof-only でも Project は `file_ids=[]` で public model に残る。
- Project を failed/excluded/tainted にしない。
- Project 間で File membership を移動しない。

Project ID と `project_config_digest` の preimage は変更しません。

### 7.7 reference closure

`_record_references()` を利用し、

- private proof-only record references は `D` 内へ閉じる。
- public record references は `M` 内へ閉じる。
- public record が proof-only Module/Component/member 等を参照しない。
- source Project の full membership と public Project の safe membership を同一 view として比較しない。

N08 の source/proof seam 部分をここで閉じます。

### 7.8 counts

producer cache ではなく actual structures から測定します。

`SourceInventoryCountsV3` は少なくとも次を保持します。

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

関係は次です。

```text
accounted_records = published_records + proof_only_records

正常 unique base:
accounted_records = proof_discovered

published_entities =
  published_modules + published_components
```

`response_model_record_counts()` の既存意味を再利用できますが、validator は actual model/proof IDs から同じ値を再導出します。

SI-P06 の 10,000/+1 は **measurement だけ** SI-03 で確認して構いません。10,001 を `CSV-NEXT-LIMIT-005` に route して Core rejection を認定するのは SI-04 です。proof-only source row を省略して 10,000 以下へ見せることは拒否します。

### 7.9 partition fingerprint

profile は固定です。

```text
next-source-inventory-safe-subset-v1
```

preimage の top-level keys は exact 三つだけです。

```json
{
  "profile_id": "...",
  "request_id": "...",
  "projects": [...]
}
```

Project rows は request Project の **root-path order** で、各 row は exact 四 keys:

```json
{
  "project_id": "...",
  "safe_file_ids": [],
  "failed_file_ids": [],
  "excluded_file_ids": []
}
```

三 ID arrays は元 `Project.file_ids` を partition で filter した sorted IDs です。

hash は、

```text
SHA256(CJ15(preimage))
```

で、CJ15 は pinned Unicode 15 NFC、key sort、compact UTF-8、末尾 LF なしです。既存 `canonical_json_bytes()` / `digest()` の codec 意味を変更しません。

validator は producer の cached `partition_fingerprint` を expected value として使わず、same request + independently derived partition から再計算します。

---

## 8. TDD の実行順序

一度に多数の guard を実装せず、下表の順に **各 test 一件を Red → minimum Green → same test Green** にします。複数行を先にまとめて Green にする実装は避けます。

| 順序 | proposed test | 主に閉じる契約 |
|---:|---|---|
| 1 | `test_v3_reference_uses_0_2_0_retained_assets_without_relabeling_v2_kat` | 新 producer identity、旧 KAT 不変 |
| 2 | `test_source_rows_are_resolved_from_same_request_without_record_payload` | SI-REQ-001、Project/File source resolution |
| 3 | `test_source_record_key_null_or_payload_is_rejected` | SI-N04 |
| 4 | `test_missing_or_duplicate_acquired_source_discovery_is_rejected` | SI-N01/N02 |
| 5 | `test_full_module_base_is_derived_before_public_model_projection` | owner cardinality、SI-N06/N13/N15 |
| 6 | `test_parse_file_root_partitions_direct_failed_file_and_safe_sibling` | SI-P01 source seam |
| 7 | `test_read_file_root_uses_read_file_direct_reason` | SI-P02 source seam |
| 8 | `test_nonfile_module_taint_excludes_untainted_owner_file_without_fake_file_taint` | SI-P07。`module_relation` / `export_binding` / `boundary_derivation` parameterization |
| 9 | `test_all_proof_only_files_keep_project_with_empty_safe_membership` | SI-P04 source seam |
| 10 | `test_nonprogram_source_safe_file_is_published_without_module` | SI-P05 |
| 11 | `test_owner_selection_exclusion_preserves_existing_reason` | legal selection/unsupported を taint/partial に変えない |
| 12 | `test_cross_project_and_public_to_proof_only_references_are_rejected` | SI-N08/N12 |
| 13 | `test_selected_module_cardinality_exception_cannot_mint_available_source_seam` | SI-N09。TARGET-001 自体は SI-04 |
| 14 | `test_safe_subset_cannot_replace_full_acquired_inventory` | SI-N10/N11 |
| 15 | `test_owner_reason_missing_or_forged_and_hidden_module_cardinality_are_rejected` | SI-N15 |
| 16 | `test_counts_include_every_proof_only_source_record` | SI-P06 source count / SI-N07 |
| 17 | `test_partition_fingerprint_matches_independent_ascii_kat` | exact preimage/order/hash |

N05 は SI-03 では「File discovery/partition に必要な source row を seed/disposition 操作で消せない」部分だけを閉じます。mandatory root set、全 causal edges、taint fixed point の完全再導出は SI-04 です。

N14 locality/open dependency は SI-03 の完了条件に数えません。

---

## 9. 独立 KAT と mutation strategy

hash/count expected value を producer 自身から取得してはいけません。

partition fingerprint については ASCII だけで構成した一つの worked fixture を選び、実装 helper とは別に canonical preimage literal を固定します。たとえば実際の fixture IDs を埋めた literal に対し、repository shell で次のように SHA-256 を計算して expected literal を test に貼ります。

```bash
PREIMAGE='{"profile_id":"next-source-inventory-safe-subset-v1","projects":[...],"request_id":"..."}'
printf '%s' "$PREIMAGE" | shasum -a 256
```

ASCII fixture にすることで、この cross-check は Unicode normalizer の同じ実装を再利用しません。Unicode 15 NFC 自体の既存 KAT は変更しません。

negative mutation は「mutation 後に producer hash も一緒に再生成して通るか」を確認するものを含めます。特に、

- fake Project/File metadata を変更して self-consistent ID/hash を再生成。
- File と Module を同時に model から消す。
- File taint を新たに付けて owner failure を偽装。
- Module owner reason を `not_selected` 等へすり替える。
- partition counts だけを正しく合わせ、実 ID partition を不正にする。
- partition fingerprint を mutation 後に再hashする。
- public model から proof-only record への dangling reference を作る。

といった coordinated mutation が必要です。単純な hash mismatch だけで落ちる negative test に限定しません。

own class の mock、`SimpleNamespace` を成功 owner として使う経路、expected hash を production helper から取得する test は作りません。

---

## 10. 実行コマンド

dependency を変更しません。verified `uv.lock` は少なくとも `pytest 8.4.2`、`pytest-cov 7.1.0`、`mypy 1.20.2`、`ruff 0.16.4`、`jsonschema 4.26.0` を pin しています。最初に frozen environment を使います。

```bash
uv sync --frozen --all-groups
```

### 各 Red → Green

最初の behavior:

```bash
uv run pytest tests/contracts/test_next_source_inventory_v3.py -q \
  -k test_v3_reference_uses_0_2_0_retained_assets_without_relabeling_v2_kat
```

source resolution:

```bash
uv run pytest tests/contracts/test_next_source_inventory_v3.py -q \
  -k test_source_rows_are_resolved_from_same_request_without_record_payload
```

owner-closed P07:

```bash
uv run pytest tests/contracts/test_next_source_inventory_v3.py -q \
  -k test_nonfile_module_taint_excludes_untainted_owner_file_without_fake_file_taint
```

count:

```bash
uv run pytest tests/contracts/test_next_source_inventory_v3.py -q \
  -k test_counts_include_every_proof_only_source_record
```

partition KAT:

```bash
uv run pytest tests/contracts/test_next_source_inventory_v3.py -q \
  -k test_partition_fingerprint_matches_independent_ascii_kat
```

その他の各 proposed test も同じく一 test selection ずつ Red → Green にします。

Red evidence は「test が intended invariant の未実装を理由に fail したこと」を確認します。unrelated import error、fixture construction error、旧 KAT failure を Red evidence に数えません。

### 新 seam の focused completion

```bash
uv run pytest tests/contracts/test_next_source_inventory_v3.py -q
```

### 直接隣接する既存 regression

```bash
uv run pytest \
  tests/contracts/test_next_request_frame_v2.py \
  tests/contracts/test_next_semantic_candidate_v2.py \
  -q
```

旧 schema/reference seam:

```bash
uv run pytest \
  tests/contracts/test_json_schemas.py \
  tests/contracts/test_next_contracts.py \
  -q
```

Python / SQLAlchemy bytes の regression:

```bash
uv run pytest \
  tests/contracts/test_python_goldens.py \
  tests/contracts/test_sqlalchemy_goldens.py \
  -q
```

SI-03 の final contract regression:

```bash
uv run pytest tests/contracts -q
```

### type / lint

```bash
uv run mypy src tests
uv run ruff check .
uv run ruff format --check .
```

### SpecDock

repository-local skill の規則に従い、実行直前に current help を読みます。

```bash
python3 ./spec-dock/scripts/spec-dock --help
python3 ./spec-dock/scripts/spec-dock sync --help
python3 ./spec-dock/scripts/spec-dock validate --help
```

その後、CI と同じ操作を実行します。

```bash
python3 ./spec-dock/scripts/spec-dock sync
python3 ./spec-dock/scripts/spec-dock validate
```

最後に diff integrity:

```bash
git diff --check
git status --short
```

SI-03 単位では production/actual OS/CLI/package の Issue-wide acceptance command を pass 証拠に数えません。`uv run pytest` 全体、offline build、PlantUML、A03/A04/A05 は後続 gate の責務です。

---

## 11. 差分制約の確認

original base を固定します。

```bash
BASE=ce0edaa8fe63e79523fe7ad1dcb4b0a39dc02dce
```

実装完了前に差分を確認します。

```bash
git diff --name-only "$BASE"
```

通常の期待差分は次の三 path だけです。

```text
tests/contracts/next_source_inventory_v3_reference.py
tests/contracts/next_source_inventory_v3_validation.py
tests/contracts/test_next_source_inventory_v3.py
```

次の既存領域には差分を許しません。

```bash
git diff --exit-code "$BASE" -- \
  src \
  pyproject.toml \
  uv.lock \
  schemas \
  tests/fixtures/next_runtime_v2 \
  tests/fixtures/next_trusted_profile \
  tests/contracts/test_python_goldens.py \
  tests/contracts/test_sqlalchemy_goldens.py
```

旧 v1/v2 request/response/schema/reference/KAT の変更で SI-03 を成立させてはいけません。

---

## 12. commit / push / Strict review

すべての local evidence が Green の後にのみ coherent paths を stage します。

```bash
git add \
  tests/contracts/next_source_inventory_v3_reference.py \
  tests/contracts/next_source_inventory_v3_validation.py \
  tests/contracts/test_next_source_inventory_v3.py

git diff --cached --check
git diff --cached --name-only

git commit -m "test: add SI-03 source inventory v3 reference seam"
```

通常 hook をそのまま通します。`--no-verify` を使いません。

現在の branch から non-force push します。

```bash
git push origin iss-00008-generate-nextjs-component-snapshots
```

push 後:

```bash
git status --short
git rev-parse HEAD
```

Strict unit review の base は、実装後 HEAD の親や最後の修復 commit に変更せず、常にこの brief の original SI-03 base:

```text
ce0edaa8fe63e79523fe7ad1dcb4b0a39dc02dce
```

と cumulative `HEAD` の全範囲です。

repository 内では ChatGPT Code Review Strict wrapper の具体的な実行コマンドを確認できなかったため、存在しない CLI/API command はここで作りません。主担当が既に認可されている Strict workflow を直接使い、

```text
repository = chemitaro/code-structure-viz
branch     = iss-00008-generate-nextjs-component-snapshots
base       = ce0edaa8fe63e79523fe7ad1dcb4b0a39dc02dce
head       = pushed cumulative HEAD
scope      = entire base..head SI-03 range
```

を固定して review します。

修復が必要でも history rewrite / force push / new checkout は行わず、同じ branch に additive fix commit を積み、original base → 新 cumulative HEAD 全体を再レビューします。API fallback、non-Strict review、manual pass への置換はしません。サブエージェントと browser progress monitoring も使用しません。

---

## 13. 停止条件

以下のいずれかが必要になった時点で SI-03 実装を止めます。既存仕様を暗黙拡張してはいけません。

| 必要になった変更 | 判断 |
|---|---|
| child が Project/File metadata や eligibility bool を authority として送る必要がある | blocker |
| File を mandatory seed / record-level taint から除外する必要がある | blocker |
| Module→File の逆 taint edge が必要 | blocker |
| owner failure を File の direct parse/read failure に変換する必要がある | blocker |
| Project 自体を tainted/failed/excluded にする必要がある | blocker |
| Project/File/Module identity preimage を変更する必要がある | blocker |
| 新しい File disposition/reason/diagnostic code が必要 | blocker |
| selected-cardinality exception を available success に流用する必要がある | blocker |
| early reader prefix を partial-safe certificate にする必要がある | blocker |
| 新 ASSET failure policy を採択しないと進めない | blocker |
| old `0.1.0` KAT/schema/reference を `0.2.0` として relabel する必要がある | blocker |
| public-v3 / run-v3 / compatibility-v3 を実装しないと source seam が通らない | SI-05 への越境。停止 |
| full root/causal/locality/target/export/budget gate が必要 | SI-04 への越境。停止 |
| `src/`, dependency/lock、production adapter、actual TS/OS/CLI/package の変更が必要 | A04/A05 への越境。停止 |

---

## 14. 完了条件

SI-03 は、次のすべてが実測された時だけ完了とします。

1. 新規三ファイルのみで reference seam が成立している。
2. `0.2.0` fixture が実際の retained asset identity → request → response control → transport candidate に bind され、旧 `0.1.0` KAT は byte-for-byte の既存回帰として残っている。
3. full acquired Project/File discovery が same request から解決され、source `record` payload/null、欠落、重複、fake metadata を拒否する。
4. full program File/Module ownership を public model より先に検証し、`E_module` が model absence/child bool から導出されていない。
5. `F_safe/F_failed/F_excluded` が acquired Files の完全排他的 partition で、owner-closed Option A の reason priority と一致する。
6. P07 の三 nonFile root 系で File を fake-taint/direct-failure にせず owner Module 原因で除外できる。
7. safe Project membership が request membership の `F_safe` filter であり、全 File 除外時も empty Project が残る。
8. private/public references がそれぞれ D/M に閉じる。
9. actual counts が proof-only source rows を含み、safe subset への縮退で budget measurement を減らせない。
10. partition fingerprint が exact 3-key / 4-key-row preimage と独立 KAT に一致する。
11. SI-P01/P02/P04/P05/P06/P07 の **source seam 部分**、SI-N01〜N13/N15 が Green。
12. N14 locality、full root/causal/target/budget を Green と主張していない。
13. focused tests、adjacent v2 regression、contract regression、Python/SQLAlchemy goldens、mypy、Ruff、SpecDock、`git diff --check` がすべて成功している。
14. normal hooks を通した coherent commit が current branch へ non-force push 済みで、worktree が clean。
15. Strict unit review は original base `ce0edaa8fe63e79523fe7ad1dcb4b0a39dc02dce` から pushed cumulative HEAD 全体を対象にし、部分的な旧 v2 pass や Spec Review pass を SI-03 implementation review の代用にしていない。

この完了状態が意味するのは **SI-03 source/proof reference seam が成立したことだけ**です。`ValidatedSemanticDecisionV3`、full Core admission、public-v3、production runtime、Issue #8 全体の certification は未完了のまま SI-04 以降へ渡します。
