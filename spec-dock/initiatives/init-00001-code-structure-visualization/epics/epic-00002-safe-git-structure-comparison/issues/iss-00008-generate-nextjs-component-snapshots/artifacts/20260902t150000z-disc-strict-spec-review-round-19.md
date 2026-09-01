# Issue #8 Round 19 Strict specification remediation record

## Scope and status

これはIssue #8のproduction implementationではない。Round 19 Strict content reviewで
確認された仕様・契約上のfindingを、canonical Requirement/Design/Plan、contract docs、
schemas、fixture、reference tests、人間向けHTMLで機械検証可能にした記録である。
production Next adapter/CLIは未実装であり、Git publication、Strict pass、implementation
readinessを宣言しない。

fresh current-SHA Strictは pending、implementation readinessは unconfirmed のままである。
過去のRound 18 artifactとhistorical verdictは上書きしない。

## Reviewed fixed point and Strict provenance

| item | exact value |
| --- | --- |
| repository | `chemitaro/code-structure-viz` |
| branch | `iss-00008-generate-nextjs-component-snapshots` |
| reviewed SHA | `0b80bff7706ca4bec770dbdf25620fbb5d2ecc2d` |
| CI run | `33557963556` (7/7 success) |
| Strict session | `required-strict-github-connector-verificati-687` |
| transcript | `/Users/iwasawayuuta/.oracle/sessions/required-strict-github-connector-verificati-687/artifacts/transcript.md` |
| transcript SHA-256 | `a64f04b5948db0df3106803c659cc27c6ee8edd5abf300afa15e81d64691e351` |

The reviewed transcript returned exactly:

```text
review_status: fail
p0_count: 0
p1_count: 5
p2_count: 1
implementation_ready: no
```

This is a historical fail verdict. A fresh review of the current post-remediation SHA is
still pending and must not be inferred from local checks.

## Findings, remediation, and executable evidence

### R19-P1-01 — SourceAcquisitionSeal must precede the request

`SourceDiscoveryIntent` now contains only project roots, known project-root control candidates,
and fixed discovery rules. A trusted frozen inventory/snapshot is read before request creation.
The bounded JSONC parser accepts BOM, comments, and trailing commas only outside strings, rejects
duplicate keys and invalid types, resolves one local `extends` string, and derives include/exclude/
files/source roots/effective roles/final membership from the frozen control bytes. Final
control/program/context membership is read once, drift and digest/size are checked, and plan plus
view are sealed atomically. Request files must equal the already captured seal set; no request-led
seal reconstruction is an authority path.

Evidence: `test_source_seal_derives_plan_and_view_from_one_intent_and_rejects_drift`,
`test_round18_source_seal_rejects_caller_membership_and_typed_drift`, and the Round 19 source
partial/union tests. Negative mutations cover injected paths/roles/plan, duplicate reads,
malformed control, extends arrays, and revision drift.

### R19-P1-02 — SourceFailureLedger is seal-owned

`SourceFailureLedger.from_seal(seal, failures, targets, proof_roots)` is the only construction
route. Raw graph nodes/edges, project roots, failure roots, and the source seal identity remain
owned by `SourceAcquisitionSeal`; reachability, safe subset, and target taint are recomputed
inside the ledger. Caller booleans, replacement graph edges, `seal_id`, and digest claims are
not accepted. The ledger digest includes the source-seal digest.

The acquisition result is a closed union:
`CompleteSourceSeal | PartialSourceSeal | SourceAcquisitionUnavailable | SourceIntegrityFatal`.
A single isolated program/context read failure produces `PartialSourceSeal` with a safe file set
instead of a comprehension abort. That safe request and its ledger identity propagate into the
validated decision and publication context. Non-isolatable/control failures use
`CSV-NEXT-SOURCE-003`/`payload_unavailable`; proven local failures use
`CSV-NEXT-SOURCE-001`/`partial_safe`.

Evidence: `test_round18_source_failure_ledger_recomputes_reachability`,
`test_round19_partial_source_result_preserves_safe_subset_and_ledger_identity`, and
`test_round19_source_acquisition_union_is_typed_and_fail_closed`. Edge deletion, caller
locality booleans, malformed control, and drift are executable negative cases.

### R19-P1-03 — publication candidates and bytes are decision-owned

Validated response bytes and their SHA-256 remain opaque authority in the response decision.
Child adapter chunks are capture observations only. The finalizer accepts no external
`stdout_candidates`, preselected payload, independent status, or public diagnostics. It derives
summary, root manifest, semantic/PlantUML artifacts, and typed unavailable bytes once from the
semantic decision and actual measurements, then seals exact candidate bytes and digests in the
`PublicationBoundaryDecision`.

The selected-copy algorithm measures a successful candidate once. Exact bytes are retained; a
limit+1 breach disposes partial bytes, persists one failure-manifest descriptor, and emits one
schema-valid typed unavailable result without re-copying or re-measuring that failure manifest.
An empty stdout is a usage/no-publication case. The semantic outcome is not silently rewritten by
a selected-copy failure.

Evidence: `test_round18_validated_response_raw_bytes_are_opaque_authority`,
`test_round18_publication_projections_return_sealed_candidate_bytes`, and
`test_round16_final_publication_decision_seals_capture_stderr_and_selected_copy`. Exact/+1 and
candidate/substitution mutation cases are retained in those tests.

### R19-P1-04 — process observation is a closed OS identity contract

`schemas/next-process-launch-observation-v1.schema.json` separates named reference `fixture`
observations from `production`. Production is limited to `darwin` and `linux` and requires
absolute verified Node realpath, hash/version, file identity at hash and spawn, verified open
handle, OS-specific spawn primitive, equal post-spawn identity, FD lifecycle, process-group
policy, and an explicit TOCTOU failure point. A mismatch fails closed; a fixture cannot stand in
for production.

Reference schema/validator tests do not open or spawn a host executable. They do not claim OS
process-level acceptance. The Plan retains a later production process-level acceptance gate.

Evidence: `test_round19_process_observation_is_fixture_or_supported_os_production`,
`test_round18_process_descriptor_requires_os_identity_and_spawn_binding`, and the existing
faithful iterable capture tests (explicitly not OS process-level tests).

### R19-P1-05 — stage-dependent provenance and discriminators

`schemas/next-provenance-v1.schema.json` uses a closed `oneOf` with stage/code and one
`{state,value}` row per authority field. Request-independent failures preserve only the observed
prefix; later request, limits, source plan, toolchain, trusted environment, compatibility,
process-launch, and budget values are `unobserved`/`null`. Source stages may retain limits and
source plan only when actually observed before failure. `next-config-v1` requires the
`request_independent` boolean and makes normal/independent branches disjoint. `next-run-context`
checks selector/format and budget source/resolved correlations.

Evidence: `test_round19_stage_provenance_reference_rejects_stage_code_and_prefix_mutations`,
`test_round19_next_config_discriminator_is_required_and_disjoint`, and
`test_round19_stage_provenance_is_closed_and_preserves_observed_prefix`.

### R19-P2-01 — path-only ordering uses UTF-8 bytes

For public path targets, remove `path:` and compare NFC-normalized UTF-8 path bytes. Canonical
JSON bytes remain the comparator for object rows only. The quote inverse vector demonstrates that
JSON escaping cannot reorder target paths; submitted order is checked before any normalization.

Evidence: `test_round19_target_path_order_uses_nfc_utf8_bytes_not_json_escaping` and
`test_round18_path_only_order_is_nfc_utf8_and_object_rows_are_canonical_json`.

### Partial-safe follow-up closure

The prior content-review partial-safe gap is closed by the acquisition result union and the
`request_from_partial_source_seal` boundary. A safe subset request is filtered from the sealed
captured set, registered against the same source seal, and passed with the same ledger identity
to response validation and `NextPublicationContext`. A failed read is represented as typed
source evidence rather than an unhandled dictionary-comprehension exception.

Evidence: `test_round19_partial_source_result_preserves_safe_subset_and_ledger_identity` and
`test_round19_source_acquisition_union_is_typed_and_fail_closed`.

## Verification record

The following local checks are required for this remediation. They verify the pre-implementation
contract only; they are not a Strict pass.

| check | result |
| --- | --- |
| `uv run pytest tests/contracts/test_next_contracts.py tests/contracts/test_json_schemas.py -q --tb=short -k 'round19 or source_seal or source_inventory or process_observation or request_independent or contract_fixture_index'` | 15 passed, 291 deselected in 0.68s |
| `uv run pytest tests/contracts/test_next_contracts.py tests/contracts/test_json_schemas.py -q --tb=short` | 306 passed in 43.88s |
| `uv run pytest tests/contracts -q --tb=short` | 329 passed in 68.49s (0:01:08) |
| `uv run pytest -q --tb=short` | 1185 passed, 1 skipped in 191.86s (0:03:11) |
| `uv run mypy src tests` | Success: no issues found in 137 source files |
| `uv run ruff check . --output-format concise` | All checks passed |
| `uv run ruff format --check .` | 158 files already formatted |
| `./spec-dock/scripts/spec-dock validate` | spec-dock: ok (validate) nodes=10 |
| Japanese HTML PlantUML validator | static 8; browser 8/8; zoom click/keyboard/bounds/focus trap/dismissal/focus restoration; VALIDATED |
| `git diff --check` | PASS |
| `git diff --name-only -- src` | empty |
| `find . -type d -name node_modules -print` | empty |

## Implementation boundary

Round 19 changes are limited to Issue #8 specifications, contract documentation, schemas,
fixtures, reference tests, the existing human HTML, and this durable artifact. No `src/**`
production implementation, dependency, Git write, or Strict call belongs to this remediation.
Fresh current-SHA Strict remains pending; readiness is unconfirmed; production implementation is
absent.
