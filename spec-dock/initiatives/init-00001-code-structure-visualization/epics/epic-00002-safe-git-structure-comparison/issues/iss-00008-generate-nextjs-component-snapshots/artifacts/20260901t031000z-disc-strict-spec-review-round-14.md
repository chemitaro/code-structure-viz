# ChatGPT Use Strict Round 14 review evidence

## Provenance and status

Round 14 had two materially different attempts. The first attempt stopped at
the mandatory GitHub connector verification boundary and returned only the
verification failure. The second attempt completed the independent content
review after verifying the exact branch tip. Both transcripts are preserved;
neither is treated as a substitute for a fresh review of the current branch.

| attempt | transcript | SHA-256 | result |
| --- | --- | --- | --- |
| connector verification failure | `/Users/iwasawayuuta/.oracle/sessions/issue-eight-strict-round-fourteen/artifacts/transcript.md` | `da7a78ea8c298fff4527bac48b3593f6fa8009ee2fe4f774c8dfad1978b7e4cb` | `OUS-R001-GITHUB-VERIFICATION-FAILED` only |
| successful retry/content review | `/Users/iwasawayuuta/.oracle/sessions/issue-eight-strict-round-fourteen-2/artifacts/transcript.md` | `05c802ca289681a10fb804e152c7d0ffcd20a30a8223123bede7204eb7803fc4` | review completed |

- repository: `chemitaro/code-structure-viz`
- branch: `iss-00008-generate-nextjs-component-snapshots`
- expected and observed full SHA: `cf5da416e25e76068ed99caf0d450d0e2d5b28df`
- GitHub Actions run: `33457932686` (`completed / success`, 7/7 jobs)
- reviewed implementation scope: data-only contracts; no production `src/**` implementation

The retry result was:

```text
review_status: fail
p0_count: 0
p1_count: 5
p2_count: 2
implementation_ready: no
```

This is a historical Strict result and must not be rewritten as pass. A fresh
current-SHA Strict review is pending and its readiness is unconfirmed. The
product Next adapter/CLI implementation is absent by design at this stage; it
has not been started and that absence is not itself a review defect.

## Findings from the successful retry

### P1-1 — pre-response failures had no sole decision authority

The valid-response path had an immutable validated decision, but node discovery,
spawn, timeout, non-zero exit, stderr/raw stdout cap, malformed JSON, duplicate
key, schema/ref/ID, and other failures could still be projected through
independent `_domain` values. This left request context, closed stage/code,
known/null counts, payload availability, artifacts, stdout/stderr, and exit
behavior open to separate reconstruction.

Required closure: a closed `NextRunDecision` union with
`ValidatedResponseDecision`, `PreResponseFailureDecision`, and
`NotApplicableDecision`. Every domain/root/manifest/stdout/stderr projection
must consume this union only. Pre-response failure must own request-derived
`NextRunContext`, stage/diagnostic, counts, `payload_unavailable`, zero
artifacts, and exit 3. Parameterized node/protocol/limit end-to-end vectors
must reach every projection; 16 MiB+1 must not synthesize
`_domain("incomplete")`.

### P1-2 — proof reason semantics were not closed

The response vocabulary allowed `not_selected`, `target_excluded`,
`unsupported`, `tainted`, `failed`, and `over_budget`, but the outcome helper
could lower status for any non-empty exclusion/failure set. That could turn a
semantically complete targeted result into `partial_safe`, lose intentional
unsupported coverage, or allow the adapter to bypass Python's entity budget
gate.

Required closure: `not_selected` and selection-only `target_excluded` do not
lower status; intentional `unsupported` is `complete` plus
`CSV-NEXT-UNSUPPORTED-001`/unknown coverage; localized taint/failed is
`partial_safe` only with locality proof; adapter `over_budget` is rejected and
is owned only by Python `EntityBudgetGate`; explicit target identity failure
is typed `payload_unavailable`. Four positive/negative vectors are required.

### P1-3 — IdentifierName depended on host Unicode data

The declared ECMAScript Unicode 15.0 profile was derived from the host
`unicodedata` database, so supported Python versions could disagree and
`Other_ID_Continue`/U+00B7 was not a deterministic checked-in table input.

Required closure: check in deterministic Unicode 15.0.0 ID_Start and
ID_Continue intervals/lookup data, include Other_ID_Start,
Other_ID_Continue, and Join_Control, and include the exact table byte digest
in the trusted semantic profile, compatibility preimage, and run fingerprint.
Membership must not call host `unicodedata.category()`. Cross-version full
code-point digest and post-15.0 rejection vectors are required.

### P1-4 — model/aggregate/raw limits were not mutually reachable

The response duplicated model record payloads in
`proof.discovered_records`, so aggregate array limits could be exceeded before
the declared model-record boundary. Exact model, model+1, aggregate+1, and
raw-byte+1 diagnostics and precedence were not proven on a schema-valid wire
envelope without constructing huge object graphs.

Required closure: use ID/reference evidence for public model records and allow
payload only for proof-only records, then set the mathematically reachable
`max_model_records` to 10,000 while retaining the 100,000 aggregate-array and
16 MiB raw-byte limits. The proof `discovered_records` schema array has a
separate structural `maxItems=20,000`, allowing a schema-valid cap+1 envelope
to reach semantic model-limit validation. Add generated schema-valid boundary
vectors through bounded decode, response validation, and decision construction,
with documented measurement points and fixed diagnostic precedence.

### P1-5 — child stdout was not incrementally bounded before capture

The raw response cap was checked before decode but after the complete bytes had
already been received. A child could therefore make the parent retain an
unbounded stdout prefix before rejection.

Required closure: parent-side incremental child stdout capture with a distinct
`max_adapter_stdout_capture_bytes`; count before retain, accept exact limit,
terminate the process group at +1, discard retained partial/raw bytes, and do
not call the decoder. The result is manifest-only typed unavailable stdout,
`CSV-NEXT-LIMIT-003`, exit 3. A faithful iterable chunk-reader harness (not an
OS process-level test) proves exact, +1, and unbounded-output behavior; the
production contract still requires process-group termination.

### P2-1 — stdout target failure cardinality and branches were incomplete

A single target failure could carry one reason, while multiple target failures
lost their reasons. The top-level `reason` property also left a legacy shape
that was not the canonical representation.

Required closure: canonical sorted unique
`target_failures: [{target_key, reason}]`, permitted only for target-related
payload-unavailable results and forbidden for available, not-applicable,
generic unavailable, fatal, and interrupt branches. Test one, repeated same
reason, mixed reasons, and non-target mutations. The legacy top-level field is
removed from the schema.

### P2-2 — source-plan timing was ambiguous

The canonical source-plan contract described the plan as resolved after the
SourceView freeze, while the design described a staged discovery process. The
timing of control/extends reads, drift checking, and the final role map was
therefore open to implementation choice.

Required closure:

```text
SourceDiscoveryIntent
  -> two-phase single-read acquisition
  -> FinalSourceAcquisitionPlan + SourceView (one atomic seal)
```

The final read and drift check precede the shared seal; every path is read once;
no filesystem read occurs afterward. An instrumented reader must prove the
frozen bytes, control/extends/file-role map, plan, and view are one sealed
result.

## Local remediation mapping

The following changes materialize the findings as contracts and executable
reference tests. They do not change the historical Strict verdict and do not
start production implementation.

| finding | materialized paths | executable evidence |
| --- | --- | --- |
| P1-1 | `tests/contracts/next_reference_validation.py`, `tests/contracts/test_next_contracts.py`, canonical Requirement/Design/Plan | closed decision variants; pre-response node/protocol/limit projections through domain/root/stdout/exit |
| P1-2 | `schemas/next-adapter-response-v1.schema.json`, `tests/contracts/next_reference_validation.py`, `tests/contracts/test_next_contracts.py`, `docs/contracts/next-semantic-v1.md` | four reason/outcome vectors and adapter `over_budget` rejection |
| P1-3 | `tests/contracts/ecmascript_unicode_15_0.py`, `tests/contracts/next_reference_validation.py`, compatibility/trusted schemas and tests | checked-in table digest, Other_ID/U+00B7, host-UCD independence and known-answer vectors |
| P1-4 | `schemas/next-adapter-response-v1.schema.json`, `schemas/next-limits-v1.schema.json`, `tests/contracts/next_reference_validation.py`, `tests/contracts/test_next_contracts.py`, `docs/contracts/next-limits-v1.md` | `max_model_records=10,000`; proof structural `maxItems=20,000`; generated 10,000-record schema-valid response is accepted through `bounded_decode_json` -> `validate_response_envelope` -> `response_boundary_decision`, 10,001 remains schema-valid and is specifically `CSV-NEXT-LIMIT-005`, aggregate+1 and raw+1 use actual JSON bytes |
| P1-5 | `tests/contracts/next_reference_validation.py`, `tests/contracts/test_next_contracts.py`, `schemas/next-limits-v1.schema.json`, `docs/contracts/next-limits-v1.md` | faithful iterable chunk-reader harness (explicitly not OS process-level) proves incremental exact/+1/unbounded capture, no retained over-limit bytes, no decoder call, read-stop after the breach, and termination/disposal flags |
| P2-1 | `schemas/stdout-result-v1.schema.json`, `tests/contracts/test_json_schemas.py`, `tests/contracts/test_next_contracts.py`, `docs/contracts/next-semantic-v1.md` | sorted target failure cardinality and forbidden-branch mutations |
| P2-2 | `tests/contracts/next_reference_validation.py`, `tests/contracts/test_next_contracts.py`, `docs/contracts/next-source-plan-v1.md`, canonical Design/Requirement/Plan | instrumented single-read and shared-seal vector |

The human explanation is updated at
`20260831t022707z--nextjs-component-snapshot-best-practice-guide.html` with
the same decision flow, bounded capture, proof semantics, Unicode profile,
target-failure array, and source seal. It retains the prior Round 11–13
historical states and exactly one Round 11 Pass C item.

## Criterion-to-test map

| criterion | test/evidence |
| --- | --- |
| closed decision is the only downstream input | `test_pre_response_decision_is_the_only_authority_for_manifest_stdout_and_exit`, `test_validated_decision_is_the_only_publication_authority`, and `_domain(decision=...)` guard |
| proof precedes typed target routing | `test_response_base_rejects_invalid_cross_reference_before_target_failure`, `test_response_base_rejects_invalid_cross_reference_before_duplicate_target_failure`, and `test_target_failure_validates_complete_proof_before_typed_routing` |
| reasons survive all projections | `test_round14_proof_reason_semantics_keep_selection_and_unsupported_complete`, `test_round14_adapter_proof_cannot_claim_entity_over_budget`, and target failure manifest/stdout projection tests |
| deterministic Unicode 15.0.0 | `test_round13_ecmascript_identifier_tables_are_pinned_and_complete`, trusted-profile digest vectors, and host-UCD independence assertions |
| reachable model/aggregate/raw limits | `test_schema_valid_model_record_limit_is_reachable_on_generated_wire` (10,000 exact and schema-valid 10,001), `test_actual_json_aggregate_boundary_precedes_schema_validation`, `test_model_proof_wire_budget_and_response_precedence`, `test_bounded_decoder_rejects_duplicates_depth_strings_and_aggregate_before_materializing`, and `test_raw_response_stdout_byte_cap_has_exact_and_plus_one_whole_run_projection`; `test_run_fingerprint_preimage_includes_limits_and_toolchain` proves the changed operational limit changes run identity while semantic compatibility remains separate |
| child capture precedes decoder | `test_adapter_stdout_capture_is_incremental_and_disposes_overrun` with faithful iterable chunk-reader, read-stop, decoder/disposal spies |
| source plan/view atomic seal | `test_source_plan_and_view_are_atomically_sealed_after_single_reads` |
| schema branch closure | `test_stdout_target_failures_are_bijective_sorted_and_target_only`, `test_stdout_result_schema_rejects_selector_status_and_reason_mismatches`, and target failure mutations |

## Verification status

Local verification after the accompanying contract/docs/schema edits and the
Round14 reachable-limit remediation is:

| command | result |
| --- | --- |
| `uv run pytest tests/contracts/test_next_contracts.py -q` | `140 passed in 18.18s` |
| `uv run pytest tests/contracts -q` | `266 passed in 27.72s` |
| `uv run pytest -q` | `1122 passed, 1 skipped in 146.09s` |
| `uv run mypy src tests` | `Success: no issues found in 137 source files` |
| `uv run ruff check .` | success |
| `uv run ruff format --check .` | success; 157 files already formatted |
| `./spec-dock/scripts/spec-dock validate` | success; `nodes=10` |
| `validate-plantuml-html.mjs ...20260831t022707z--nextjs-component-snapshot-best-practice-guide.html` | success; `@plantuml/core@1.2026.6`, 6/6 rendered, and zoom gate passed |
| `npm test` in `tests/contracts` using locked TypeScript | success; `TypeScript 5.9.2; diagnostics=0; symbols=14` |

The locked TypeScript gate was installed with an isolated temporary npm cache;
the generated `tests/contracts/node_modules` directory was removed after the
gate. These local results are evidence only; they cannot change the Strict
verdict above.

Canonical status remains: **fresh current-SHA Strict pending; readiness
unconfirmed; product implementation absent.**

review_status: fail; p0_count: 0; p1_count: 5; p2_count: 2; implementation_ready: no
