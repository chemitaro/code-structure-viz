# Issue #8 Strict specification review evidence — Round 16

## Scope and status

This artifact records the Round 16 data-only remediation for Issue #8,
“Generate Nextjs Component Snapshots”. It is evidence for the canonical
Requirement, Design, Plan, contract documents, schemas, fixtures, and
executable reference tests. It does not represent production implementation,
and it does not overwrite an earlier Strict verdict.

The fixed review point was branch
`iss-00008-generate-nextjs-component-snapshots`, repository
`chemitaro/code-structure-viz`, commit
`732477c72c7e05d3f15818ba8a3f75a4c97dc5a9`. GitHub Actions run
`33494926439` was green (`7/7`). CI green is recorded as provenance only and
is not a correctness or readiness claim.

## Strict provenance

The available Round 16 records are preserved separately:

| attempt | session | transcript SHA-256 | observed result |
| --- | --- | --- | --- |
| verification-only | `issue-eight-strict-round-sixteen` | `e9027c5ce26d0f5f953a84a8dc10ef78252f65aed65ac47c22a82346991afb74` | `GITHUB_VERIFIED` and exact SHA `732477c72c7e05d3f15818ba8a3f75a4c97dc5a9` |
| content review | `required-strict-github-connector-verificati-627` | `0a1fdfda86bf46e12cd3e1547ce05c1208209265a8d6e8b8a6ac6a3cccf8d895` | exact-SHA review completed; historical fail below |

The content-review transcript is retained at
`/Users/iwasawayuuta/.oracle/sessions/required-strict-github-connector-verificati-627/artifacts/transcript.md`.
The verification-only transcript is retained at
`/Users/iwasawayuuta/.oracle/sessions/issue-eight-strict-round-sixteen/artifacts/transcript.md`.
Only these two Round 16 transcript files were available at authoring time;
no third Round 16 session is invented. Earlier Round 15 three-attempt
provenance remains in
`20260901t060000z-disc-strict-spec-review-round-15.md` and is not relabeled as
Round 16.

The historical content-review result was:

```text
review_status: fail
p0_count: 0
p1_count: 16
p2_count: 3
implementation_ready: no
```

The review explicitly treated the absence of product code under `src/**` as
intentional scope, not as a defect. Fresh current-SHA Strict after this
remediation is pending; readiness remains unconfirmed and production
implementation is absent.

## Finding → remediation → executable evidence

The following table preserves the review's actionable findings and records
the local contract closure. Test names are executable reference tests in
`tests/contracts/test_next_contracts.py`; schema and document paths are part
of the same acceptance surface.

| finding | local remediation | executable evidence |
| --- | --- | --- |
| P1-1 `SourceDiscoveryIntent` injected final closure | Intent now carries roots/control candidates/rules only; one seal derives plan, view, roles, and extends closure from frozen bytes and inventory. | `test_source_seal_derives_plan_and_view_from_one_intent_and_rejects_drift`; `docs/contracts/next-source-plan-v1.md`; `schemas/next-source-plan-v1.schema.json` |
| P1-2 publication context had synthetic authority | All decision projections use the immutable publication context; resolved request/config, source seal, toolchain, trust, compatibility, and fingerprint inputs are decision-owned. | `test_all_decision_variants_project_without_legacy_fixture_authority`; `test_validated_decision_defensively_copies_request_and_publication_context` |
| P1-3 request was not a typed validated boundary | `ValidatedAdapterRequest` validates ID, files, base64/size/digest/canonical bytes, limits, targets, and context before response processing; no private-limit alias fallback. | `test_response_validation_accepts_only_the_bounded_raw_bytes_entrypoint`; `test_raw_response_mutations_all_cross_the_same_bounded_entrypoint` |
| P1-4 no schema-valid request-independent branch | Config/project/source pre-response failure uses explicit null/known facts, empty artifacts, `payload_unavailable`, exit 3, and no invented public request/project/config. | `test_round16_request_independent_source_failure_projects_schema_valid_whole_run`; `schemas/next-domain-manifest-v1.schema.json`; `schemas/run-manifest-v1.schema.json` |
| P1-5 source locality was disconnected | Immutable Python-owned `SourceFailureLedger` distinguishes local safe `SOURCE-001`/`partial_safe` from non-isolatable `SOURCE-003`/unavailable and target taint. | `test_round15_source_failure_preserves_locality_boundary`; `test_round16_request_independent_source_failure_projects_schema_valid_whole_run` |
| P1-6 stage/code was a free cross product | Catalog-derived closed failure matrix fixes kind, stage, code, reference permission, counts, outcome, and exit. | `test_round16_failure_matrix_is_catalog_derived_and_rejects_cross_product`; `docs/contracts/diagnostic-v1.md`; `schemas/next-diagnostic-catalog-v1.json` |
| P1-7 model limit ran before proof/schema | Boundary is raw cap → decode/aggregate → schema → base/path/ref/proof → actual model/proof-only count → model/entity gates. | `test_raw_response_mutations_all_cross_the_same_bounded_entrypoint`; `test_actual_json_aggregate_boundary_precedes_schema_validation`; `test_schema_valid_model_record_limit_is_reachable_on_generated_wire` |
| P1-8 aggregate/resource code conflicted | Per-array, aggregate, string, and depth resource overruns use `CSV-NEXT-LIMIT-003`; malformed/closed-schema/proof violations use `CSV-NEXT-PROTOCOL-001`. | `test_actual_json_aggregate_boundary_precedes_schema_validation`; `test_next_diagnostic_catalog_is_the_public_and_manifest_authority` |
| P1-9 selected stdout +1 lacked schema branch | `stdout-result/v1` has complete/partial selected-artifact-unavailable branches with persisted descriptor and stable reason; semantic status is not rewritten. | `test_selected_stdout_copy_has_exact_and_plus_one_publication_boundaries`; `schemas/stdout-result-v1.schema.json` |
| P1-10 helpers independently changed publication outcome | Capture, stderr, and selected-copy measurements are sealed by one final publication decision before projections. | `test_round16_final_publication_decision_seals_capture_stderr_and_selected_copy`; `test_adapter_stderr_harness_stops_before_retaining_child_text` |
| P1-11 stdout field order contradicted canonical bytes | Removed special order as authority; all JSON uses sorted keys, NFC, UTF-8, LF, including target failures. | `test_publication_bytes_are_exact_model_payloads_and_digest_roots`; `test_canonical_digest_normalizes_unicode_before_hashing`; `docs/contracts/stdout-v1.md` |
| P1-12 anonymous default failed binding validator | Exact module-local `@anonymous-default` is an allowed declaration key, at most once; normal bindings still reject reserved words. | `test_round16_identifier_contexts_cover_reserved_exports_and_anonymous_default`; `schemas/next-semantic-v1.schema.json` |
| P1-13 Unicode context differed by syntax surface | Context-specific predicates are shared across binding, declaration/export key, import/re-export, JSX, and trusted/external references; Unicode 15.0.0 table is checked in. | `test_round15_identifier_name_is_contextual_and_host_ucd_independent`; `test_round16_identifier_contexts_cover_reserved_exports_and_anonymous_default`; `tests/contracts/ecmascript_unicode_15_0.py` |
| P1-14 target reasons were dropped | Resolver emits exactly one of eight closed reasons per failed target; only Next target-unavailable stdout carries sorted rows. | `test_round16_target_resolution_exposes_all_closed_failure_reasons`; `test_stdout_target_failure_reason_enum_is_closed_for_each_resolution_failure`; `schemas/stdout-result-v1.schema.json` |
| P1-15 PlantUML allowed stale client-entry dual role | Direct client seed is neither derived role; only distinct closures may yield client-dependency/server-candidate dual role. | `test_taint_edges_are_derived_for_boundary_and_shared_frontier`; `docs/contracts/next-plantuml-v1.md` |
| P1-16 process launch trust boundary was open | Versioned descriptor closes verified Node realpath/symlink policy, argv/cwd, env allowlist/denied variables, stdio/FDs, and process group. | `test_round16_process_launch_descriptor_is_closed_and_security_deterministic`; `schemas/next-process-launch-v1.schema.json`; `docs/contracts/next-process-launch-v1.md` |
| P2-1 HTML repeated one ambiguous stdout limit | HTML now refers to schema/docs by named boundary and explains capture/private response/selected copy without a fixed single-limit inventory. | `test_round16_html_has_no_fixed_limit_inventory`; HTML PlantUML validator |
| P2-2 vector index omitted later rounds | `next_contract_vectors.json` includes Round14/15/16 IDs and a bidirectional criterion→test mapping checked against declared test functions. | `test_contract_fixture_index_materializes_plan_008_vectors`; `tests/fixtures/next_contract_vectors.json` |
| P2-3 LIMIT-003 message was narrow | Catalog/docs define the code as the common configured byte-limit diagnostic across measurement points, with exact/+1 all-or-none behavior. | `test_next_diagnostic_catalog_is_the_public_and_manifest_authority`; `docs/contracts/diagnostic-v1.md`; `docs/contracts/next-limits-v1.md` |

## Round 16 follow-up closure: mandatory launch provenance and final publication authority

The follow-up audit found two authority gaps in the first local Round 16
materialization. They are closed here without changing the historical Strict
verdict or claiming a new Strict review:

| follow-up | contract closure | executable evidence |
| --- | --- | --- |
| A. launch descriptor/default context | `NextPublicationContext.process_launch_descriptor` is mandatory, validated against the observed toolchain Node status, included by digest in the run-fingerprint preimage, and has no default/fallback. `PreResponseFailureDecision` and `NotApplicableDecision` also require an explicit `NextDecisionContext`; the failure factory no longer reconstructs one from a missing argument. | `test_round16_publication_context_requires_explicit_launch_and_decision_context`; `test_all_decision_variants_project_without_legacy_fixture_authority`; `docs/contracts/next-process-launch-v1.md` |
| B. final publication sole input | `PublicationBoundaryDecision` seals child stdout, child stderr, public stderr, and selected-copy measurements, plus a digest over those four records. Domain, root manifest, artifact bytes/descriptors, selected stdout, public stderr, and exit projections accept that immutable boundary object only; independent outcome/measurement maps or changed retained bytes are rejected. Exact and +1 vectors cover each boundary and the full schema/reference chain. | `test_round16_final_publication_decision_seals_capture_stderr_and_selected_copy`; `tests/contracts/test_next_contracts.py` projection helpers; `docs/contracts/stdout-v1.md` |

The local reference tests are contract materialization, not product
implementation. The selected-copy overrun preserves the semantic decision and
persisted artifact descriptor while the root publication result becomes
incomplete with exit 3. Child capture or public-stderr overrun discards raw
and artifact bytes and projects typed unavailable with exit 3. No projection
accepts a caller-supplied replacement status or measurement.

No new Strict/Oracle session was run for this follow-up. Fresh current-SHA
Strict remains pending, readiness is unconfirmed, and production
implementation is absent.

## Round 16 contract inventory

The canonical artifacts now include:

- R/D/P Round 16 sections with source-intent, decision/context, request,
  failure matrix, validation order, limits, selected-copy, Unicode, roles,
  process descriptor, and readiness boundaries.
- `docs/contracts/next-process-launch-v1.md` plus its closed schema.
- Updated semantic, config, diagnostic, stdout, runtime, compatibility,
  source-plan, and PlantUML contract documents.
- Human HTML Round 16 diagram and Japanese explanation with pinned PlantUML
  contract metadata; no fixed `stdout 16 MiB` inventory.
- Schema and reference-validator/fixture tests for all accepted branches,
  including request-independent failure and final publication outcomes.
- Follow-up authority tests prove launch-descriptor and decision-context
  omission/substitution rejection, and drive every publication surface from
  one immutable `PublicationBoundaryDecision`.

## Verification record

The following commands are the required final record. Results are filled only
from the current worktree; a green local check is not Strict approval.

| command | result |
| --- | --- |
| `uv run pytest tests/contracts/test_next_contracts.py -q --tb=short` | 170 passed (33.93s) |
| `uv run pytest tests/contracts -q --tb=short` | 297 passed (43.75s) |
| `uv run pytest -q --tb=short` | 1153 passed, 1 skipped (153.32s) |
| `uv run mypy src tests` | success; no issues in 137 files |
| `uv run ruff check .` | success; all checks passed |
| `uv run ruff format --check .` | success; 158 files already formatted |
| `./spec-dock/scripts/spec-dock validate` | success; nodes=10 |
| `node /Users/iwasawayuuta/.agents/skills/japanese-explanatory-html/scripts/validate-plantuml-html.mjs spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00008-generate-nextjs-component-snapshots/artifacts/20260831t022707z--nextjs-component-snapshot-best-practice-guide.html --chrome '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'` | success; static 8/8, browser 8/8, zoom contract passed |
| TypeScript trusted-profile gate (if affected) | not applicable; no TypeScript adapter/runtime source changed |
| `git diff --check` | success |
| `git diff --name-only -- src` | empty |

Generated `node_modules` must be absent before handoff. Fresh current-SHA
Strict remains pending, readiness is unconfirmed, and product implementation
is absent even if every local command becomes green.
