# Issue #8 Round 20 Strict specification remediation record

## Scope and status

これはIssue #8のproduction implementationではない。Round 20 Strictで確認された
仕様・契約上のfindingを、canonical Requirement/Design/Plan、contract docs、schemas、
fixture、reference tests、人間向けHTMLへ反映したdata-only remediationの記録である。
Next adapter/CLI、Node実行、依存追加、Git publicationはこの作業の範囲外であり、production
implementationは未着手である。

fresh current-SHA Strictは pending、implementation readinessは unconfirmed のままである。
過去のRound 18/19 artifactとhistorical verdictは上書きしない。ここに記録するlocal green
checksもStrict passやimplementation readinessを意味しない。

## Reviewed fixed point and Strict provenance

| item | exact value |
| --- | --- |
| repository | `chemitaro/code-structure-viz` |
| branch | `iss-00008-generate-nextjs-component-snapshots` |
| reviewed SHA | `aba6509ae818f8b959aa31276a6e8f5d6956680a` |
| Strict review session | `required-strict-github-connector-verificati-692` |
| Strict verification session | `issue-eight-strict-round-twenty` |
| transcript | no transcript artifact was available |
| evidence: meta | `/Users/iwasawayuuta/.oracle/sessions/required-strict-github-connector-verificati-692/meta.json` |
| meta SHA-256 | `ff3ea44790e02a2dd5bcf6f2cc85dc43195edb119ff001472e7456005ddb40ce` |
| evidence: output | `/Users/iwasawayuuta/.oracle/sessions/required-strict-github-connector-verificati-692/output.log` |
| output SHA-256 | `b07348d8d7eacfc1a3e64d720a4204ff8cffe9bd0996eefc7d43169c2594dfa6` |
| evidence: model | `/Users/iwasawayuuta/.oracle/sessions/required-strict-github-connector-verificati-692/models/gpt-5.6-sol.json` |
| model SHA-256 | `96a4fc6796e81fb765711532c9f8b5b17a3bccf7a53d3e8bc89ac717f3282252` |

The reviewed Strict verdict is historical and exact:

```text
review_status: fail
p0_count: 0
p1_count: 6
p2_count: 1
implementation_ready: no
```

No CI run identifier was supplied with this Round 20 review evidence; this record does not
invent one. A fresh current-SHA Strict review remains pending.

## Findings, remediation, and executable evidence

### R20-P1-01 — PackageApplicabilityMatrix is direct-dependency authority

Applicability is derived once per frozen project-root `package.json`. A non-empty string in direct
`dependencies.next` or `devDependencies.next` is `applicable`; missing package or no direct Next is
`non_applicable`; duplicate keys, invalid UTF-8/BOM/JSON, invalid dependency-table types, and empty
or non-string `next` values are `malformed`. The aggregate is malformed if any root is malformed,
otherwise applicable if any root is applicable, otherwise non-applicable. Lockfiles, indirect
dependencies, directory names, and config files are not evidence. All-non-applicable roots select
the closed not-applicable path without a Node probe.

The closed shape is `schemas/next-package-applicability-v1.schema.json`; acquisition derives it
from captured bytes and stores it on `SourceAcquisitionSeal`. Evidence is
`test_round20_package_applicability_matrix_is_direct_dependency_only`,
`test_round20_package_applicability_matrix_rejects_encoding_duplicates_and_mixed_state`, and
`test_round20_explicit_config_candidates_cannot_hide_package_applicability`.
The tests include table-driven applicable/non-applicable/malformed cases and schema validation.

### R20-P1-02 — Config inheritance and source membership are strict

Only known project-root control candidates are read before membership derivation. The JSONC
boundary accepts UTF-8 BOM, comments, and trailing commas outside strings, rejects duplicate keys,
unsafe `..`, package or array `extends`, `plugins`, `typeRoots`, `types`, invalid module or
moduleResolution, and unsupported types. Include/exclude uses the explicit segment grammar
(`*`, `?`, and whole-segment `**`) rather than `fnmatch`. A control read/parse failure is typed
fail-closed; it is never substituted with an empty config or empty partial membership.

Evidence is `test_round20_source_control_uses_segment_grammar_and_fail_closed_control_reads`.
It checks positive nested include/exclude membership, unsafe pattern rejection, and a failed
control read even when partial mode is requested.

### R20-P1-03 — Source graph is derived from frozen bytes

The source graph is recomputed from the sealed frozen file bytes, resolved relative imports and
local extends, and project ownership. An optional reader graph is observation-only and cannot
override the result. Removing an edge and recomputing a digest does not create a valid source
seal. This keeps SourceFailureLedger locality evidence tied to the same source authority.

Evidence is `test_round20_source_graph_is_derived_from_frozen_bytes_not_reader_injection`.
It supplies an attacker graph, checks that the exact import edge is derived from source bytes,
and rejects a replacement graph on the immutable seal.

### R20-P1-04 — Source integrity has one closed decision projection

Acquisition uses the closed union
`CompleteSourceSeal | PartialSourceSeal | SourceAcquisitionUnavailable | SourceIntegrityFatal`.
Revision drift, duplicate/post-seal reads, and source integrity mismatch are fatal. Control or
non-isolatable source failures are `CSV-NEXT-SOURCE-003`/`payload_unavailable` with manifest-only
availability and exit 3. A proof-backed local safe subset remains
`CSV-NEXT-SOURCE-001`/`partial_safe`. The stage, diagnostic code, outcome, payload/manifest
availability, stdout reason, and exit are fixed together by
`SourceAcquisitionDecisionProjection`, rather than independently reconstructed by surfaces.

Evidence is `test_round20_source_integrity_has_one_fatal_vs_payload_unavailable_projection`.
It asserts exact fatal and unavailable projections and rejects a fatal result with a non-integrity
stage, leaving no uncovered fatal branch.

### R20-P1-05 — Process observation is explicit and no-fake-identity

`next-process-launch-observation-v1` is a closed `fixture | production` union. Production is
limited to darwin/linux and requires the observed Node version, absolute realpath, hash-time and
spawn-time OS file identities, verified-open handle, concrete OS-specific spawn primitive,
`argv[0]`, post-spawn identity equality, fixed cwd/environment/FD/process-group policy, and a
TOCTOU failure point. Unavailable/not-applicable branches use explicit null identity fields; a
default executable, PATH result, or fixture cannot fill them. The reference test does not touch a
host executable and does not claim OS process-level acceptance.

Evidence is `test_round20_process_observation_has_explicit_unavailable_union_and_no_fake_identity`.
It validates the schema and mutation rejection for fabricated identity and checks deterministic
fixture observation conversion.

### R20-P1-06 — Provenance is one canonical stage-dependent shape

`NextDecisionContext` and `NextPublicationContext` use the same closed provenance shape:
`{kind, stage, failure_code, observed}`. The failure stage/code pair comes from the catalog.
Values observed before the failure form the prefix; all later request, limits, source plan,
toolchain, trusted environment, process, compatibility, and budget values are explicit
`unobserved`/`null`. Requested formats, selector, and budget requested/resolved/source correlations
remain checked. `next-config.request_independent` is a required disjoint boolean branch.

Evidence is the existing Round 19 matrix test
`test_round19_stage_provenance_reference_rejects_stage_code_and_prefix_mutations` plus
`test_round20_stage_provenance_is_one_canonical_shape_and_rejects_mismatch`. They validate the
canonical object shape, valid source-stage observed prefix, and stage/code or prefix mutations.

### R20-P2-01 — Coverage index points to substantive tests

`tests/fixtures/next_contract_vectors.json` now includes Round 20 positive and negative vector
IDs and exact criterion-to-test mappings. The reference check requires the expected map, resolves
each named test in the source, and verifies that the mapped body contains substantive negative
evidence (mutation rejection, malformed input, or a dedicated Round 20 authority assertion).
An HTML/schema existence check alone cannot satisfy the map.

Evidence is `test_round20_fixture_coverage_index_is_substantive`; the fixture index also lists
the seven Round 20 positive and seven negative vector IDs.

## Cross-surface contract changes

The canonical Requirement/Design/Plan, `docs/contracts/next-config-v1.md`,
`next-source-plan-v1.md`, `next-process-launch-v1.md`, `next-runtime-manifest-v1.md`,
`next-plantuml-v1.md`, `next-semantic-v1.md`, `diagnostic-v1.md`, and `stdout-v1.md` now
describe the same authority chain:

```text
frozen package/control observations
  -> applicability + strict config/membership
  -> sealed source plan/view/graph
  -> closed source result and stage provenance
  -> process observation / decision projection
  -> domain, root manifest, stdout, stderr, artifact, exit
```

The human HTML section `#round20` explains the seven findings in Japanese without adding a
ninth PlantUML diagram. The document keeps exactly the existing eight PlantUML diagrams and
retains pinned PlantUML behavior. It does not reproduce a brittle numeric limit inventory.

## Verification record

The checks below are the required local pre-implementation gates. Their final values are recorded
after the Round 20 docs/artifact synchronization; they do not change the historical Strict verdict.

| check | result |
| --- | --- |
| focused Round 20 tests: `uv run pytest tests/contracts/test_next_contracts.py tests/contracts/test_json_schemas.py -q --tb=short -k 'round20 or contract_fixture_index'` | 18 passed, 306 deselected in 0.40s |
| `uv run pytest tests/contracts/test_next_contracts.py tests/contracts/test_json_schemas.py -q --tb=short` | 324 passed in 49.89s |
| `uv run pytest tests/contracts -q --tb=short` | 347 passed in 60.55s (0:01:00) |
| `uv run pytest -q --tb=short` | 1203 passed, 1 skipped in 216.78s (0:03:36) |
| `uv run mypy src tests` | Success: no issues found in 137 source files |
| `uv run ruff check . --output-format concise` | All checks passed! |
| `uv run ruff format --check .` | 158 files already formatted |
| `./spec-dock/scripts/spec-dock validate` | spec-dock: ok (validate) nodes=10 |
| Japanese HTML PlantUML/browser validator | PASS static: 8; PASS browser: 8/8; PASS zoom: click, keyboard, bounds, focus trap, dismissal, focus restoration; VALIDATED |
| `git diff --check` | PASS |
| `git diff --name-only -- src` | empty |
| `find . -type d -name node_modules -print` | empty |

## Implementation boundary

Round 20 changes are limited to specifications, contract docs, schemas, fixture index,
reference tests, and the existing human HTML plus this durable artifact. No `src/**` production
implementation, dependency, Git write, or Strict call belongs to this remediation. Fresh
current-SHA Strict remains pending; readiness is unconfirmed; production implementation is absent.
