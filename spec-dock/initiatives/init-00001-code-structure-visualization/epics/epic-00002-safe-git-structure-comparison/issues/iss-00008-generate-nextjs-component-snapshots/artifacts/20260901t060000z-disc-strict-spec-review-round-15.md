# Issue #8 Strict specification review — Round 15 evidence

## Status and provenance

This artifact is a durable record of the Round 15 attempts. It must not be
read as a production implementation report or as a replacement for the
historical Strict verdict.

| attempt | purpose | transcript | transcript SHA-256 | result |
| --- | --- | --- | --- | --- |
| 1 | connector-only verification | `/Users/iwasawayuuta/.oracle/sessions/issue-eight-strict-round-fifteen/artifacts/transcript.md` | `a5b7fbcb3b1b9a8655cf5bc14adea42bca9f340d589209738d64b00a2de2de19` | `OUS-R001-GITHUB-VERIFICATION-FAILED`; no content review |
| 2 | connector verification retry | `/Users/iwasawayuuta/.oracle/sessions/issue-eight-strict-round-fifteen-2/artifacts/transcript.md` | `171cf56350a4665c4f48446fe3b91c5b77f464f442024a8dc01ece306e1ab221` | exact commit verification only; not a content verdict |
| 3 | content review follow-up | `/Users/iwasawayuuta/.oracle/sessions/required-strict-github-connector-verificati-609/artifacts/transcript.md` | `85506ccacb634b1c21816032b9bd0a11fa4d3be95f6416657fab441e8011713c` | content review; fail |

The content review verified:

- repository `chemitaro/code-structure-viz`;
- branch `iss-00008-generate-nextjs-component-snapshots`;
- exact SHA `c3f8e4188ca715a29d60a7454a66390938bce496`;
- GitHub Actions run `33472932927`, 7/7 green.

The exact historical verdict is:

```text
review_status: fail
p0_count: 0
p1_count: 13
p2_count: 1
implementation_ready: no
```

Fresh current-SHA Strict is pending. Readiness is unconfirmed. The product
Next adapter/CLI implementation is absent; `src/**` remains outside this
data-only specification remediation.

## Finding → remediation → executable evidence

The following table records the review finding, the bounded contract
materialized in this round, and the local evidence intended to prevent a
prose-only closure.

| finding | materialized contract and local evidence |
| --- | --- |
| P1-1 decision was not the sole publication authority | `NextPublicationContext` is held by each decision variant with sealed SourceView/plan identity, public request/config, actual toolchain/trusted environment, run context, and fingerprint preimage. The production-shaped `_domain(decision=...)` projection is an explicit builder with no `_legacy_domain_fixture` fallback; no-payload variants derive their required empty model shell only from the decision context. Evidence: `test_validated_decision_defensively_copies_request_and_publication_context`, `test_all_decision_variants_project_without_legacy_fixture_authority`, request-independent decision test, and existing exact semantic/PlantUML mutation vectors. |
| P1-2 validated request was mutable/optional | `ValidatedResponseDecision` deep-copies a mandatory request and checks schema/id, run-context, targets, resolved limits, gate transition, and canonical target/export failure rows. Evidence: the defensive-copy test mutates nested request/model/context values and rejects inconsistent target failures. |
| P1-3 failure union lacked domain-level taxonomy | Closed `DecisionFailureKind`, stage/code set, catalog reference-permission checks, and request-independent `NextDecisionContext` preserve config/project/source/target/trust/process/limit/protocol distinctions. `pre_response_failure_decision` accepts safe path/symbol references. Evidence: pre-response matrix and request-independent context test. |
| P1-4 model/array limit authority and aggregate vector were inconsistent | Actual model counts are `published_model_records`, proof-only payload records are counted only when absent from model, and discovered is their sum. `max_model_records=10,000` remains reachable. Evidence: generated exact/+1 model wires and `test_schema_valid_model_record_limit_is_reachable_on_generated_wire`, plus `test_schema_valid_wire_aggregate_plus_one_precedes_model_and_schema_routing`; these validate the real envelope, canonical bytes, bounded decode, and boundary decisions at model/aggregate limits below the raw cap. |
| P1-5 private/capture/public stdout limits were conflated | Named limits are `max_adapter_stdout_capture_bytes`, `max_adapter_response_bytes`, and `max_selected_stdout_bytes`; `max_stdout_bytes` is only a compatibility alias. Evidence: `test_adapter_stdout_capture_is_incremental_and_disposes_overrun`, `test_capture_success_routes_schema_valid_private_response_to_one_decision`, raw response exact/+1, and `test_selected_stdout_copy_has_exact_and_plus_one_publication_boundaries`. |
| P1-6 stderr evidence was not a faithful incremental reader | `capture_adapter_stderr` consumes `Iterable[bytes]`, counts before retaining, stops after breach, sets disposal/termination/no-leak flags, and publishes zero bytes. Evidence: `test_adapter_stderr_harness_stops_before_retaining_child_text`. This is explicitly a faithful harness, not an OS process-level test. |
| P1-7 plan/view seal accepted caller-injected authority | `seal_source_acquisition(intent, reader, inventory)` derives plan and view together after a drift check and one seal. Final-plan keyword, plan-only/view-only inventory, duplicate read, revision drift, digest/size, and role mismatch are rejected. Evidence: `test_source_seal_derives_plan_and_view_from_one_intent_and_rejects_drift` and `test_source_plan_and_view_are_atomically_sealed_after_single_reads`. |
| P1-8 target stdout branch/reasons were open | Target failures are restricted by schema to `next:semantic-json` and `next:plantuml`; the eight reasons are `missing`, `component_only`, `duplicate`, `out_of_scope`, `non_program`, `control_context`, `project_ambiguity`, `selected_taint`, with one canonical row per target. Evidence: `test_stdout_target_failure_reason_enum_is_closed_for_each_resolution_failure` plus the existing bijective/mixed/non-target vectors. |
| P1-9 IdentifierName was not contextual everywhere | Checked-in Unicode 15.0.0 table is used by `is_identifier_name`, `is_binding_identifier`, and `is_declaration_key` for component, export/import, external/trusted reference, JSX, and re-export checks. Evidence: `test_round15_identifier_name_is_contextual_and_host_ucd_independent`, table digest and reserved/Other_ID/Join_Control/post-15.0 matrix. |
| P1-10 full classification KAT was absent | `identifier_classification_digest()` hashes the start/continue result bitstream for all `0..0x10ffff`; the known answer is asserted independently of host UCD. Evidence: the Round 13/15 Unicode contract test and `IDENTIFIER_CLASSIFICATION_SHA256`. |
| P1-11 source outcome vocabulary could not express non-isolatable failure | `CSV-NEXT-SOURCE-001` remains localized `partial_safe`; `CSV-NEXT-SOURCE-003` is source-specific non-isolatable `payload_unavailable`; `classify_source_failure` preserves the distinction. Evidence: parameterized `test_round15_source_failure_preserves_locality_boundary` compares localized/proven-safe, global, and tainted/unproven paths, alongside catalog/schema updates. |
| P1-12 boundary roles were contradictory and adapter-authored | Button/Card fixture roles are corrected. `derive_boundary_roles` is the authority: client seed itself is not `client_dependency`, only static value closure targets are; client app seed is not `server_candidate`; server traversal stops before client entry; dual role needs distinct closures. Evidence: `test_taint_edges_are_derived_for_boundary_and_shared_frontier` asserts the independent base/dual closure results and model validation vectors. |
| P1-13 stdout field order contradicted encoder | Canonical lexicographic JSON (`sort_keys=True`, NFC, UTF-8, LF) is the sole byte contract; target failures use the same order and no manual insertion-order encoder exists. Evidence: canonical JSON publication and stdout exact-byte vectors. |
| P2-1 HTML claimed a stale fixed limit count | HTML now uses schema-driven/drift-resistant wording, adds the Round 15 authority diagram/cards, and records exact historical verdict state. Evidence: pinned PlantUML HTML validator. |

## Changed contract surfaces

The local materialization is limited to the following ownership boundary:

- `spec-dock/.../requirement.md`, `design.md`, and `plan.md` Round 15 sections;
- `docs/contracts/next-*.md`, `docs/contracts/stdout-v1.md`, and
  `docs/contracts/diagnostic-v1.md` addenda;
- `schemas/diagnostic-v1.schema.json`, `schemas/next-adapter-response-v1.schema.json`,
  `schemas/next-diagnostic-catalog-v1.json`, `schemas/next-limits-v1.schema.json`,
  `schemas/next-semantic-v1.schema.json`, `schemas/run-manifest-v1.schema.json`,
  and `schemas/stdout-result-v1.schema.json`;
- `tests/contracts/next_reference_validation.py`,
  `tests/contracts/ecmascript_unicode_15_0.py`, and
  `tests/contracts/test_next_contracts.py` reference evidence;
- this artifact and the existing standalone Japanese HTML guide.

No production `src/**` implementation, dependency, Git operation, Strict call,
or product behavior is introduced by this artifact.

## Round 15 follow-up hardening

After the content-review materialization, the decision projection was audited
again at the boundary that had remained ambiguous. The reference projection no
longer calls `_legacy_domain_fixture(response_decision=...)` or reconstructs
source, plan, config, toolchain, trusted-environment, selector, limits, or
publication status from fixture arguments. A monkeypatched legacy fixture now
fails the test if consulted by any of the ValidatedResponseDecision,
PreResponseFailureDecision, or NotApplicableDecision paths. The immutable
publication context remains the only source for those fields; request-derived
values are used only when the context is sealed, and request-independent
failures use the closed `NextDecisionContext`.

The same follow-up reconciled canonical prose: raw private adapter bytes are
measured by `max_adapter_response_bytes` before decode, while
`max_stdout_bytes` is only the selected-output compatibility alias; the three
capture/response/selected-output limits remain distinct. BoundaryRolePropagation
is also stated consistently in Requirement/Design/Plan and the HTML: the
adapter cannot author roles, a direct client seed is not `client_dependency` or
`server_candidate`, only closure targets receive derived roles, traversal stops
before a client entry, and dual role requires distinct closures.

## Verification record

Commands are recorded as they are run during this remediation. A local green
result is not a Strict pass and does not make Issue #8 implementation-ready.

| command | result |
| --- | --- |
| `uv run pytest tests/contracts/test_next_contracts.py -q` | 161 passed after the explicit no-legacy decision projection and compatibility-descriptor authority case were added; role assertions were added to the existing boundary case |
| `uv run pytest tests/contracts/test_next_contracts.py::test_all_decision_variants_project_without_legacy_fixture_authority -q` | 1 passed; all three closed decision variants project with a monkeypatched legacy fixture that fails if called |
| focused authority/limit/source/capture selection (`uv run pytest tests/contracts/test_next_contracts.py -q -k 'source_plan_and_view_are_atomically_sealed_after_single_reads or source_seal_derives_plan_and_view_from_one_intent_and_rejects_drift or taint_edges_are_derived_for_boundary_and_shared_frontier or schema_valid_model_record_limit_is_reachable_on_generated_wire or schema_valid_wire_aggregate_plus_one_precedes_model_and_schema_routing or adapter_stdout_capture_is_incremental_and_disposes_overrun or capture_success_routes_schema_valid_private_response_to_one_decision or selected_stdout_copy_has_exact_and_plus_one_publication_boundaries or all_decision_variants_project_without_legacy_fixture_authority or validated_decision_defensively_copies_request_and_publication_context'`) | 10 passed, 151 deselected in 17.79s after the compatibility descriptor was sealed |
| focused aggregate/source/decision/capture tests | 4 passed in 4.61s before the final documentation pass; the aggregate case used a schema-valid generated response. |
| `uv run pytest tests/contracts -q` | 287 passed in 35.93s |
| `uv run pytest -q` | 1143 passed, 1 skipped in 163.87s (2:43) |
| `uv run mypy src tests` | Success: no issues found in 137 source files |
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 157 files already formatted |
| `./spec-dock/scripts/spec-dock validate` | `spec-dock: ok (validate) nodes=10` |
| `/Users/iwasawayuuta/.agents/skills/japanese-explanatory-html/scripts/validate-plantuml-html.mjs /Volumes/990p2t/offloaded/home/iwasawayuuta/.codex/worktrees/c6b6/code-structure-viz/spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00008-generate-nextjs-component-snapshots/artifacts/20260831t022707z--nextjs-component-snapshot-best-practice-guide.html` | PASS static: 7 sources; PASS browser: 7/7 diagrams; PASS zoom; VALIDATED |
| locked TypeScript trusted-profile gate | Not run: no TypeScript, trusted-profile fixture, or TypeScript production surface changed in this data-only remediation. |

The final closeout must also report `git diff --check`, an empty
`git diff --name-only -- src`, and removal of any generated `node_modules`.
Fresh current-SHA Strict remains pending after those local checks.

The final local hygiene checks passed: `git diff --check` produced no output,
`git diff --name-only -- src` was empty, and `find . -type d -name
node_modules -print` returned no generated directories. These local results do
not alter the historical Strict verdict or establish implementation readiness.
