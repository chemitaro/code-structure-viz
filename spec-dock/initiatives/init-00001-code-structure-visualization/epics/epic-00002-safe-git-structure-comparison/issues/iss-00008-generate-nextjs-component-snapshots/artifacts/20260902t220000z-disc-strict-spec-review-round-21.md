# Issue #8 Round 21 Strict specification remediation record

## Scope and status

これはIssue #8のproduction implementationではない。Round 21 Strictで確認された仕様・契約上の
findingを、canonical Requirement/Design/Plan、contract docs、schemas、fixture、reference tests、
人間向けHTMLへ反映したdata-only remediationの記録である。Next adapter/CLI、Node実行、依存追加、
Git publicationはこの作業の範囲外であり、production implementationは未着手である。

fresh current-SHA Strictは pending、implementation readinessは unconfirmed のままである。過去の
Round 18/19/20 artifactとhistorical verdictは上書きしない。ここに記録するlocal green checksも
Strict passやimplementation readinessを意味しない。

## Reviewed fixed point and Strict provenance

| item | exact value |
| --- | --- |
| repository | `chemitaro/code-structure-viz` |
| branch | `iss-00008-generate-nextjs-component-snapshots` |
| reviewed SHA | `67351f970835afe05b3f4db1aa40b73b3abf0198` |
| verification-only session | `issue-eight-strict-round-twenty-3` |
| full Strict review session | `required-strict-github-connector-verificati-704` |
| transcript/evidence path | supplied transcript artifact pathなし。未提供のpathやhashは推測しない |
| CI run for reviewed SHA | `33578613432` — 7/7 success |

The full review verdict is historical and exact:

```text
review_status: fail
p0_count: 0
p1_count: 5
p2_count: 1
implementation_ready: no
```

The verification-only session and full review session are recorded separately; neither is represented as a
fresh pass. A fresh current-SHA Strict review remains pending.

## Findings, remediation, and executable evidence

### R21-P1-01 — PackageApplicabilityMatrix is the end-to-end authority

`PackageApplicabilityMatrix` is derived once from each frozen project-root `package.json`. Only a non-empty
direct `dependencies.next` or `devDependencies.next` string is `applicable`; missing/no-direct Next is
`non_applicable`; duplicate/conflicting direct declarations, invalid encoding/JSON, dependency tables, or
values are `malformed`. All-non-applicable roots produce `NotApplicableDecision` with Node permission
`prohibited` and `performed=false`; mixed matrices publish applicable roots only; malformed state is globally
unavailable and does not probe Node. Matrix observations and the decision, toolchain, domain, root manifest,
stdout, stderr, and exit are one projection. The schema is
`schemas/next-applicability-decision-v1.schema.json`.

Evidence: `test_round21_applicability_matrix_owns_filter_probe_and_all_public_surfaces` is table-driven over
applicable/non-applicable/malformed/mixed cases and validates every public surface. Its malformed and
conflicting-direct-dependency rows are negative evidence. `test_round21_applicability_source_observation_precedes_node_and_is_read_once`
proves the package observation precedes optional Node probing and each package path is read once. Vector IDs
are `round21-applicability-end-to-end` and `round21-applicability-malformed-no-node`.

### R21-P1-02 — Config inheritance and membership use a closed grammar

Only known project-root controls are read. JSONC accepts UTF-8 BOM, comments, and trailing commas outside
strings, including comma→comment→closing-delimiter; duplicate keys and invalid types fail closed. `extends`
is exactly one project-local explicit `./...` string. Bare/package, array, absolute, `../`, URL-like,
ambiguous, and cyclic forms are rejected. `plugins`, `typeRoots`, `types`, invalid `module`/
`moduleResolution`, and unsafe patterns are rejected. `include`/`exclude` use segment `*`, `?`, and
whole-segment `**`, not `fnmatch`. Control read/parse failure is global unavailable, never `{}` or empty
membership.

Evidence: `test_round21_jsonc_extends_grammar_is_closed_and_trailing_comment_is_deterministic` covers the
accepted JSONC composition and the rejection table, including forbidden compiler options and cycle. Vector
IDs are `round21-config-closed-grammar` and `round21-config-extends-injection`.

### R21-P1-03 — Source locality is sealed module-plane evidence

The source graph is derived from sealed frozen bytes, resolved local imports/extends, `baseUrl`/`paths`, and
project ownership. The deterministic scanner recognizes static imports, side-effect imports, export-from,
literal dynamic `import()`, and supported literal `require()`. Comments, templates, and regex literals are
not syntax evidence. Unsupported, ambiguous, unresolved, or external dependencies remain explicit
`open_edge`; dropping an edge cannot establish `partial_safe`. Reader/request graph injection and
edge-deletion plus digest recomputation are not authority.

Evidence: `test_round21_source_graph_scanner_closes_supported_import_planes_and_open_edges` asserts the
supported forms, alias resolution, lexical false positives, unresolved/ambiguous open edges, and schema-valid
sealed plan. Vector IDs are `round21-source-graph-module-plane` and `round21-source-open-edge`.

### R21-P1-04 — Provenance is one catalog-derived union

Request-bound and request-independent contexts share one closed `{kind, stage, failure_code, observed}`
shape. The catalog constrains stage/code pairs, including explicit `source_control`; observed values form a
prefix and later values are `unobserved`/`null`. Request, limits, source plan, toolchain, trusted environment,
process, compatibility, and budget are not synthesized after an early failure. The same validator covers
project validation, source control, Node/process, response, and model stages, and project control failure
projects through provenance/domain/root/stdout/exit.

Evidence: `test_round21_provenance_catalog_has_single_request_independent_source_control_union` validates
representative catalog pairs and rejects stage/code and observed-prefix mutations. Vector IDs are
`round21-provenance-stage-union` and `round21-provenance-stage-mismatch`.

### R21-P1-05 — Process observation is the sole process authority

`next-process-launch-observation-v1` is the normative `fixture | production` union. Production supports
darwin/linux/windows and requires OS-native verified-open/execution binding, Node realpath/hash/version,
hash-time and spawn-time identity, concrete spawn primitive, post-spawn equality, argv/cwd/environment,
stdio/FD lifecycle, process group, and fail-closed TOCTOU. Unavailable/not-applicable branches carry no fake
identity. The older launch descriptor is only a mechanically derived compatibility view. Security observation
retains host-ephemeral FD/device/inode, while `stable_fingerprint` excludes those values and is checked for
cross-machine stability.

Evidence: `test_round21_process_observation_is_normative_and_fingerprint_excludes_ephemeral_identity` covers
unavailable, Linux production, Windows production, executable substitution, and ephemeral identity mutation.
It validates the schema without opening/spawning a host executable; it is not an OS process-level acceptance
claim. Vector IDs are `round21-process-observation-fingerprint` and `round21-process-identity-substitution`.

### R21-P2-01 — Coverage mapping is executable and bidirectional

`tests/fixtures/next_contract_vectors.json` contains positive/negative vector IDs, exact substantive test
names, and validator identifiers for every Round21 criterion. The reference coverage check verifies that each
named test exists, its body contains the required vector IDs and mutation assertions, and the criterion map and
evidence index agree. A mutated missing negative vector is rejected, including for the coverage criterion itself;
HTML/schema existence is not evidence.

Evidence: `test_round21_coverage_index_is_bidirectional_and_self_validating`. Vector IDs are
`round21-coverage-index` and `round21-coverage-mapping-mutation`.

## Cross-surface contract changes

The canonical Requirement/Design/Plan and contract docs now describe this single chain:

```text
frozen package/control observations
  -> PackageApplicabilityMatrix
  -> strict config/membership and sealed module-plane graph
  -> source result + catalog provenance
  -> validated request/response + normative process observation
  -> NextRunDecision / publication boundary
  -> exact domain/root/manifest/stdout/stderr/artifact/exit projections
```

The human HTML adds a Japanese Round 21 explanation without adding a diagram. It retains exactly eight
existing PlantUML diagrams and the pinned renderer behavior. No production implementation or readiness pass
is claimed.

## Verification record

The required local gates are recorded after the final synchronization:

| check | result |
| --- | --- |
| focused Round 21: `uv run pytest tests/contracts/test_next_contracts.py tests/contracts/test_json_schemas.py -q --tb=short -k 'round21'` | 7 passed, 325 deselected in 0.14s |
| `uv run pytest tests/contracts/test_next_contracts.py tests/contracts/test_json_schemas.py -q --tb=short` | 332 passed in 43.11s |
| `uv run pytest tests/contracts -q --tb=short` | 355 passed in 51.08s |
| `uv run pytest -q --tb=short` | 1211 passed, 1 skipped in 164.33s |
| `uv run mypy src tests` | Success: no issues found in 137 source files |
| `uv run ruff check . --output-format concise` | All checks passed! |
| `uv run ruff format --check .` | 158 files already formatted |
| `./spec-dock/scripts/spec-dock validate` | spec-dock: ok (validate) nodes=10 |
| Japanese HTML validator | escalated browser validation: static PASS 8, browser 8/8 inline SVG, zoom操作PASS |
| `git diff --check` | exit 0 |
| `git diff --name-only -- src` | empty output |
| `find . -type d -name node_modules -print` | empty output |

Passing local checks do not change the historical Strict verdict. Fresh current-SHA Strict remains pending,
readiness is unconfirmed, and production implementation is absent.
