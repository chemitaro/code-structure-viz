# Issue #8 Round 17 Strict specification remediation record

## Scope and status

これはIssue #8のproduction実装ではなく、Round 17 Strict content reviewで確認された
仕様・schema・reference contractの閉包を記録するdurable artifactである。local contractが
greenになっても、fresh current-SHA Strictの再実行と `P0=0`、`P1=0`、
`review_status: pass` が確認されるまで実装readinessは未確認である。production
implementationは未着手である。

## Reviewed fixed point and provenance

| item | exact value |
| --- | --- |
| repository | `chemitaro/code-structure-viz` |
| branch | `iss-00008-generate-nextjs-component-snapshots` |
| reviewed SHA | `032c8d7e2f7786fb443fd2a49566c5a6ad9815d5` |
| CI run | `33514033888` (7/7 green) |
| Strict recovery session | `required-strict-github-connector-verificati-667` |
| transcript | `/Users/iwasawayuuta/.oracle/sessions/required-strict-github-connector-verificati-667/artifacts/transcript.md` |
| transcript SHA-256 | `6689d7384bcd1a7a7d1238dbcd61224ef0cf774176a83bd6bbb003b843ef0703` |

The transcript was read in full. Its terminal historical verdict is

```text
review_status: fail
p0_count: 0
p1_count: 9
p2_count: 3
implementation_ready: no
```

このartifactはこのfail verdictを上書きしない。fresh current-SHA Strictは pending、
readinessは unconfirmed とする。別の過去Roundのconnector-only/verification-only証跡は
各Roundのimmutable artifactに保持されており、本Roundに存在しない試行やhashを推測しない。

## Finding to remediation and executable evidence

### P1-1 — SourceAcquisitionSealのcaller-derived authority

`SourceDiscoveryIntent`をproject roots、control candidates、fixed discovery rulesだけに
限定した。inventoryはrevision/head、実読取bytes、digest/size、独立観測したattestation
だけを受け、project descriptors、compiler options、source roots、config/local extends、
final paths、role map、plan digest、source-view fingerprintを拒否する。seal内で凍結control
bytesからplan/view/config/rolesを導出し、request-owned derived valueとの不一致を拒否する。

Evidence: `test_round17_source_inventory_accepts_observations_only`,
`test_round17_request_owned_derived_source_claims_cannot_override_control_bytes`,
`test_source_seal_derives_plan_and_view_from_one_intent_and_rejects_drift`。

### P1-2 — request-independent provenanceのsynthetic fallback

requestが作れないfailureはstage-discriminated `NextDecisionContext`を使う。未観測のlimits、
trusted environment、toolchain、source plan、process launch、compatibilityは明示的な
`null`/`unobserved`とし、fixture/defaultからrequest/project/config/sealを合成しない。
各decision variantは必須のimmutable `NextPublicationContext` と closed contextを保持する。

Evidence: `test_request_independent_pre_response_decision_keeps_closed_context`,
`test_round16_request_independent_source_failure_projects_schema_valid_whole_run`、および
request-independent schema/reference projection vectors。

### P1-3 — mutable/dict-inheritance ValidatedAdapterRequest

`ValidatedAdapterRequest`をcomposition-based immutable authorityにし、`dict` base-class
bypassを除去した。schema、request ID、canonical bytes/digest、file base64/size/digest、
targets、run context、resolved limitsをresponse boundaryで再検証する。

Evidence: `test_round17_validated_request_is_composed_and_revalidated`,
`test_response_validation_accepts_only_the_bounded_raw_bytes_entrypoint`。

### P1-4 — source localityのcaller boolean

`SourceFailureLedger`はsealed source graph、project ownership、targets、failure roots、
proof rootsからisolated/safe subset/target taintを導出する。これらの結論をcaller boolean
として受け付けず、local safeのみSOURCE-001、非分離はSOURCE-003とする。

Evidence: `test_round17_source_failure_ledger_derives_locality_without_caller_booleans`,
`test_round15_source_failure_preserves_locality_boundary`。

### P1-5 — process launch identityの未結合

versioned `process_launch_descriptor`をobserved Node realpath、executable digest/version、
actual spawn executable、fixed argv/cwd/env/FD/process-group、TOCTOU policyへbindする。
default/PATH/fake digestやtoolchainからのfallbackを持たず、descriptorをtoolchainと
fingerprintへ含める。reference fixture値は観測値を表すテストデータでありproduction実装ではない。

Evidence: `test_round16_process_launch_descriptor_is_closed_and_security_deterministic`,
`test_round16_publication_context_requires_explicit_launch_and_decision_context`。

### P1-6 — PublicationBoundaryDecisionの因果的bind不足

final immutable decisionがactual response bytes、validated request ID、model digest、
requested artifactのexact byte map/descriptors、selector bytes、diagnostic JSONL、全measurement
を同時にsealする。domain/root/manifest/stdout/stderr/artifact/exit projectionはこのdecision
だけを受け、再renderや独立status/measurement mapを受けない。artifact bytesのmodel、digest、
PlantUML、transport unavailableとの整合もconstructorで検証する。

Evidence: `test_round17_publication_artifacts_are_bound_to_the_immutable_decision`,
`test_round16_final_publication_decision_seals_capture_stderr_and_selected_copy`。

### P1-7 — final stdoutのclosed union不足

stdoutをsummary（selector `null`）、manifest、selected semantic/PlantUML artifact、typed
unavailableのclosed unionにした。三つのselected streamは共通
`max_selected_stdout_bytes`で測定し、exact bytesはfinal decisionへsealして返し、limit+1は
partial bytesなしでschema-valid unavailableへ進む。manifestは`run-manifest.json` descriptor、
domainはpersisted Artifact descriptor、nullはrun statusを保持する。これらを同一final
decisionから投影し、`target_failures`はNext target-related unavailableだけに一target一reason
で許可する。

Evidence: `test_next_stdout_matrix_has_exact_bytes_for_core_outcomes`,
`test_next_stdout_matrix_usage_is_empty_and_manifest_free`,
`test_round17_final_publication_stdout_union_seals_summary_manifest_exact_and_plus_one`,
`test_round16_final_publication_decision_seals_capture_stderr_and_selected_copy`。

### P1-8 — proof-derived selected_taintの未到達

proof後にderived unavailable IDをsealed roots/taintでtarget resolutionへ再入力し、
`selected_taint`を含む8理由のtyped target failureとしてdecisionへ到達させる。reasonは
diagnostic、domain、root manifest、stdout、exitまで保存し、理由配列の重複・欠落・順序逆転を拒否する。

Evidence: `test_round17_proof_derived_target_failure_is_typed_and_sorted`,
`test_round16_target_resolution_exposes_all_closed_failure_reasons`。

### P1-9 — semantic project orderの二重定義

semantic project/model collectionsはID order、request/config/source-plan/root descriptorsは
canonical root-path orderに固定する。validatorはsubmitted semantic orderをsortする前に検査し、
逆転vectorをexact bytes/digestまで検証する。全surfaceは同一lexicographic canonical encoder
（sort_keys/NFC/UTF-8/LF）を使う。

Evidence: `test_round11_inverse_project_order_reaches_response_domain_root_and_fingerprint`,
`test_project_surface_order_is_root_path_while_semantic_records_remain_id_order`。

### P2-1 — incompleteなNextDecisionContext型

`NextDecisionContext`をfrozen、keyword-only、defaultなしのstage-discriminated contextとして
扱い、request-independent failureのnull provenanceと同じ契約へ統合した。writerが後から
defaultを補う経路を設けない。

Evidence: `test_round16_failure_matrix_is_catalog_derived_and_rejects_cross_product`,
`test_round16_publication_context_requires_explicit_launch_and_decision_context`。

### P2-2 — LIMIT-003 message範囲の誤記

catalog/schema/docsの固定messageをbyteだけでなくstructural resource boundaryも説明する
文面へ同期した。raw/capture、aggregate/per-array、string/depthなどconfigured resource
overrunはLIMIT-003、malformed/closed-schema/proofはPROTOCOL-001とする。

Evidence: `test_next_diagnostic_catalog_is_the_public_and_manifest_authority`,
`test_actual_json_aggregate_boundary_precedes_schema_validation`。

### P2-3 — human HTMLのvalidation order省略

既存8 PlantUML diagramを維持し、Round 16 diagramのresponse boundaryとRound 17説明を
`raw cap → bounded decode/aggregate → closed schema → base/path/reference/proof → actual
model+proof-only count → model gate → entity gate → selected copy`へ展開した。固定個数の
limit inventoryはHTMLに重複せず、pinned PlantUML contractを維持する。

Evidence: `test_round17_html_has_validation_pipeline_and_round17_state`、HTMLのpinned
PlantUML validator。

## Verification record

The following checks are the required Round 17 gates. Results are filled only with commands
actually executed on the remediation worktree; a future Strict review is intentionally not
claimed here.

| check | result |
| --- | --- |
| focused Next contract tests (`uv run pytest tests/contracts/test_next_contracts.py -q --tb=short`) | PASS — `181 passed in 40.41s` |
| Round17-focused tests (`uv run pytest tests/contracts/test_next_contracts.py -q --tb=short -k 'round17_'`) | PASS — `11 passed, 170 deselected in 0.60s` |
| schema tests (`uv run pytest tests/contracts/test_json_schemas.py -q --tb=short`) | PASS — `104 passed in 3.70s` |
| `uv run pytest tests/contracts -q` | PASS — `308 passed in 49.79s` |
| `uv run pytest -q` | PASS — `1164 passed, 1 skipped in 168.35s` |
| `uv run mypy src tests` | PASS — `Success: no issues found in 137 source files` |
| `uv run ruff check .` | PASS — `All checks passed!` |
| `uv run ruff format --check .` | PASS — `158 files already formatted` |
| `./spec-dock/scripts/spec-dock validate` | PASS — `spec-dock: ok (validate) nodes=10` |
| Japanese HTML PlantUML validator | PASS — 8 sources, 8/8 inline SVG, zoom/focus/dismissal checks |
| `git diff --check` | PASS — no whitespace errors |
| `git diff --name-only -- src` | PASS — empty (no `src/**` changes) |
| generated `node_modules` | PASS — absent |

## Implementation boundary

このRoundの変更はcanonical Requirement/Design/Plan、contract docs、schemas、fixture index、
reference tests、human HTML、durable evidenceに限定する。`src/**`のproduction implementation、
Git publication、fresh Strictはこのartifactのscope外であり、Strict pass確認後に親agentが別途判断する。
