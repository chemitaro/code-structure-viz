# Issue #8 Round 18 Strict specification remediation record

## Scope and status

これはIssue #8のproduction implementationではない。Round 18 Strict content reviewの
findingsを、canonical Requirement/Design/Plan、contract docs、schemas、fixture、reference
tests、人間向けHTMLで機械検証可能な契約へ閉じた記録である。production adapter/CLIは未実装で、
このartifactはGit publicationやfresh Strict passを宣言しない。

fresh current-SHA Strictは pending、implementation readinessは unconfirmed のままである。
local checksがgreenでも `P0=0 / P1=0 / review_status: pass` のfresh Strict証拠が得られるまで、
後続のproduction implementationを開始しない。過去のhistorical verdictは上書きしない。

## Reviewed fixed point and provenance

| item | exact value |
| --- | --- |
| repository | `chemitaro/code-structure-viz` |
| branch | `iss-00008-generate-nextjs-component-snapshots` |
| reviewed SHA | `885352347d250cc34aef0bd52e1fe27063288c05` |
| CI run | `33543204992` (7/7 green) |
| Strict session | `required-strict-github-connector-verificati-680` |
| transcript | `/Users/iwasawayuuta/.oracle/sessions/required-strict-github-connector-verificati-680/artifacts/transcript.md` |
| transcript SHA-256 | `400431ed1fb444b3bd2509edf14ce557b8f292b0f011f281e74ffa241db8cec8` |

The reviewed transcript's terminal historical verdict was:

```text
review_status: fail
p0_count: 0
p1_count: 7
p2_count: 1
implementation_ready: no
```

The transcript/session, reviewed SHA, and CI run are provenance only. A fresh review of the current
post-remediation SHA has not run and must not be inferred from the local results below.

## Finding to remediation and executable evidence

### R18-P1-01 — SourceAcquisitionSeal caller path authority

`SourceDiscoveryIntent` accepts only roots, control candidates, and fixed rules. Inventory is
observation-only. The trusted enumerator derives config/compiler options/source roots/local extends,
final paths, roles, and plan/view descriptors from frozen control bytes under snapshot/revision, then
performs one seal. Caller `observed_paths`, derived path membership, malformed control, revision drift,
duplicate reads, and plan-only/view-only reconstruction fail closed.

Evidence: `test_round18_source_seal_rejects_caller_membership_and_typed_drift`,
`test_source_seal_derives_plan_and_view_from_one_intent_and_rejects_drift`,
`test_round17_source_inventory_accepts_observations_only`.

### R18-P1-02 — SourceFailureLedger caller reachability authority

The ledger stores raw graph nodes/edges, failure roots, project roots, targets, proof roots, and source
seal identity. Reachability, closure, safe subset, and target taint are recomputed from those facts and
bound to the seal digest; boolean-equivalent caller fields are not accepted. `SOURCE-001` is reserved
for independently proven localized partial-safe failure; non-isolatable failure is `SOURCE-003`.
Request-independent provenance records only observations made before the failure and marks later facts
`unobserved`/null.

Evidence: `test_round18_source_failure_ledger_recomputes_reachability`,
`test_round17_source_failure_ledger_derives_locality_without_caller_booleans`,
`test_round18_request_independent_provenance_is_explicitly_unobserved`.

### R18-P1-03 — validated response raw-byte authority

`ValidatedAdapterRequest` is a composed immutable authority. Before the response boundary, request
schema/id, canonical request bytes/digest, file base64/size/digest, targets, run context, and limits
are rechecked. `ValidatedResponseDecision` retains the exact canonical raw response bytes and SHA-256;
finalization derives diagnostic bytes from that decision and accepts no independent response or
diagnostic payload.

Evidence: `test_round17_validated_request_is_composed_and_revalidated`,
`test_response_validation_accepts_only_the_bounded_raw_bytes_entrypoint`,
`test_round18_validated_response_raw_bytes_are_opaque_authority`.

### R18-P1-04 / R18-P1-06 — final publication exact-byte authority

`PublicationBoundaryDecision` seals the validated request ID, response/model digest, exact summary,
root-manifest, selected-artifact and typed-unavailable candidates, diagnostic JSONL, all capture/stderr/
selected-copy measurements, and the overall seal. Domain, root manifest, stdout, stderr, artifact, and
exit projections consume that final object only. They cannot receive an independent outcome, counter,
retained buffer, or `selected_payload`; successful projection returns the sealed candidate bytes and
limit+1 returns a typed unavailable branch without partial bytes.

Evidence: `test_round17_publication_artifacts_are_bound_to_the_immutable_decision`,
`test_round16_final_publication_decision_seals_capture_stderr_and_selected_copy`,
`test_round18_publication_projections_return_sealed_candidate_bytes`.

### R18-P1-05 — Node observation-to-spawn identity

The versioned process descriptor requires supported-OS identity, verified absolute Node realpath,
file identity/hash/version, actual spawn identity/handle, fixed argv/cwd/environment/FD/process-group,
and TOCTOU policy. PATH shadowing, symlink replacement, hostile environment, locale/TZ changes, extra
FDs, omission, or substitution fail closed. Reference tests validate the descriptor and mutations only;
they do not touch a host executable and explicitly do not claim OS process-level acceptance. Production
must add that process-level acceptance later.

Evidence: `test_round18_process_descriptor_requires_os_identity_and_spawn_binding`,
`test_round16_process_launch_descriptor_is_closed_and_security_deterministic`,
`test_round16_publication_context_requires_explicit_launch_and_decision_context`.

### R18-P1-07 — closed stdout result union

stdout is a closed union: selector null summary, manifest, `next:semantic-json`, `next:plantuml`, or
typed unavailable. Each selector has an exact descriptor path/format/media type, and forbidden fields
are rejected. `target_failures` is legal only for target-related Next unavailable and has exactly one
closed reason per target. All candidates are measured by the named selected-output limit; exact bytes
are retained and limit+1 is zero-publication for that stream.

Evidence: `test_round18_stdout_union_rejects_partial_discriminator_and_wrong_next_descriptor`,
`test_round17_final_publication_stdout_union_seals_summary_manifest_exact_and_plus_one`.

### R18-P2-01 — HTML validation-order drift

The Japanese standalone HTML keeps the existing eight pinned PlantUML diagrams and exposes the exact
ordered validation pipeline: raw cap, bounded decode/aggregate, closed schema, base/path/reference/proof,
actual model+proof-only count, model gate, entity gate, selected copy. The contract test checks strict
index order and a reversed mutation fails.

Evidence: `test_round18_html_validation_order_is_strict_and_reverse_mutation_fails`, plus the pinned
HTML PlantUML validator.

## Cross-finding follow-up closures

The Round 18 remediation also closes the previously identified provenance/order seams. Run-manifest
request-independent is a required closed boolean discriminator with condition-specific fields;
`CSV-NEXT-TARGET-001` requires its reason and other codes forbid it. Target/path values use the shared
next path grammar and closed safe symbol IDs. Proof-derived target failures are resolved again from
sealed roots/taint. Semantic projects and records use ID order; root/config/source-plan path-only rows
use NFC UTF-8 byte order, while object rows use canonical JSON bytes. Submitted order is validated
before normalization, including quote-containing inverse vectors. Canonical JSON remains
`sort_keys=True`, NFC, UTF-8, and LF.

Evidence: `test_round18_run_manifest_and_diagnostic_discriminators_are_closed`,
`test_round17_proof_derived_target_failure_is_typed_and_sorted`,
`test_round18_path_only_order_is_nfc_utf8_and_object_rows_are_canonical_json`,
`test_round18_target_reason_is_required_and_forbidden_for_other_diagnostics`.

## Verification record

Results below are filled only after running the commands on this remediation worktree. Fresh Strict is
intentionally not listed as a local check and remains pending.

| check | result |
| --- | --- |
| focused Round18 contract/schema tests (`uv run pytest tests/contracts/test_next_contracts.py tests/contracts/test_json_schemas.py -q --tb=short -k 'round18'`) | PASS — `11 passed, 285 deselected in 0.26s` |
| `uv run pytest tests/contracts -q --tb=short` | PASS — `319 passed in 45.87s` |
| `uv run pytest -q --tb=short` | PASS — `1175 passed, 1 skipped in 160.39s` |
| `uv run mypy src tests` | PASS — `Success, 137 source files` |
| `uv run ruff check . --output-format concise` | PASS — `All checks passed` |
| `uv run ruff format --check .` | PASS — `158 files already formatted` |
| `./spec-dock/scripts/spec-dock validate` | PASS — `ok, nodes=10` |
| Japanese HTML PlantUML validator | PASS — `static 8, browser 8/8 inline SVG, zoom click/keyboard/bounds/focus trap/dismissal/focus restoration, VALIDATED` |
| `git diff --check` | PASS |
| `git diff --name-only -- src` | PASS — `empty` |
| `find . -type d -name node_modules -print` | PASS — `empty` |

## Implementation boundary

Changed material is limited to Issue #8 specifications, contract documentation, schemas, fixture
vectors, reference tests, human HTML, and this durable artifact. No `src/**` production implementation,
Git write, dependency, or Strict call belongs to this Round 18 remediation. Historical review failure is
preserved exactly; fresh current-SHA Strict, readiness, and product implementation remain unconfirmed.
