# ChatGPT Use Strict Round 13 review evidence

## Provenance

- source transcript: `/Users/iwasawayuuta/.oracle/sessions/issue-eight-strict-round-thirteen/artifacts/transcript.md`
- source transcript SHA-256: `035f574ec4365f2b87fa9226c39ccf58d576a56686c758f4daa40c86c721bf51`
- repository: `chemitaro/code-structure-viz`
- branch: `iss-00008-generate-nextjs-component-snapshots`
- expected and observed full SHA: `991516bf730f4f2ddb3d15067702dcfae95ec6b1`
- CI run: `33446911714` (`completed / success`, 7/7 jobs success)

This artifact preserves the independent Strict review result. The reviewed
commit is the authority for the result; local remediation must not rewrite the
recorded failure as a pass.

## Verdict

```text
review_status: fail
P0: 0
P1: 9
P2: 1
production_next_adapter_cli_absence_is_a_defect: false
implementation_agent_can_implement_without_new_material_decision: false
implementation_readiness: blocked
```

## Findings

### P1-1 — Published-byte oracle is a placeholder

`tests/contracts/test_next_contracts.py::_published_bytes` and
`tests/contracts/next_reference_validation.py::recompute_publication_projection_digest`
validate a digest note and a three-field semantic JSON rather than the closed
`code-structure-viz.semantic/v1` and `code-structure-viz.plantuml/next/v1`
payloads. Module, Component, Member, Relation, and Fact payload/order
mutations can therefore pass. The reference renderer must consume the exact
validated model and drive bytes, SHA-256, and root Artifact descriptors.

### P1-2 — Downstream run authority is reconstructed

`_domain` receives `validated_model` but separately rebuilds formats, budget,
provenance, selector, and context. A single immutable decision containing the
validated model/proof, request-owned context, pre-budget outcome, and gate
decision is required as the only input to domain/root/stdout publication.

### P1-3 — Target failure reason is lost after response routing

The response and semantic target-completeness schemas retain only target key,
status, and record IDs. `missing`, `component_only`, and `duplicate` are not
carried through domain/root/stdout projections. The closed reason vocabulary
and file/directory six-case whole-run vectors must be derived from the same
decision, not reconstructed downstream.

### P1-4 — Typed target failure can bypass proof validation

`validate_response_envelope` returns `target_failure_decision` before
`validate_proof`. A target failure must still pass a target-exception-aware
proof-base validator for collection shape/order, IDs/refs, failure-root and
causal refs, owner joins, and exact request target rows. Invalid causal edge,
export owner, or extra target-row compound mutations must fail before the
typed `CSV-NEXT-TARGET-001` result.

### P1-5 — Export graph cases do not run through a complete response

Double alias, empty/multi star, default exclusion, cycle, and conflict exist
only in simplified graph fixtures or direct helper calls. Each case must be
embedded in a schema-valid request/response and run through raw response
validation, immutable decision, domain, root manifest, stdout, diagnostic,
and exit-code publication. Cycle and conflict require separate
`CSV-NEXT-EXPORT-001` whole-run vectors.

### P1-6 — Re-export observation/raw-edge join is not bijective

`expected_export_reexport_witness` keys observations by owner, source
specifier, and imported name, omitting exported name and using first-match
lookup. Legal `export { Foo as A, Foo as B } from "./source";` can therefore
share a syntax row. Include exported/original names and stable syntax identity
in the key, consume every observation/edge exactly once, and test repeated
same-shape statements and coordinated substitutions.

### P1-7 — ECMAScript IdentifierName Unicode behavior is incomplete and unversioned

The current Python category approximation omits `Other_ID_Continue`, such as
U+00B7 MIDDLE DOT, and depends on the runtime Unicode database version. A
version-fixed ID_Start/ID_Continue/Other_ID_Start/Other_ID_Continue table or
equivalent implementation is required for JSX and export identifiers, with
the algorithm/table version included in compatibility and run-fingerprint
preimages and positive/negative vectors.

### P1-8 — Root `.` allowance conflicts with schemas

Normative docs and helper rules allow `.` for an explicitly root/source-root
field, while source-root arrays in config/request/source-plan/semantic schemas
reference the non-root-only path schema. Introduce one shared root-or-path
schema and use it on every applicable surface, with consistent fixtures.

### P1-9 — Raw response byte cap is absent before decoding

`bounded_decode_json` does not enforce `max_stdout_bytes` on the complete raw
response before UTF-8 decode/parser materialization. Add exact 16 MiB and
16 MiB+1 whitespace-safe vectors through the same response/domain/manifest/
diagnostic/stderr/stdout-unavailable/exit-3 path without tracking a huge
fixture.

## P2-1

The human HTML contains the same Round 11 Pass C list item twice. Remove one
copy without changing the PlantUML diagrams.

## Cross-authority conclusion

Requirement, Design, Plan, normative docs, schemas, fixtures, reference
validator, and tests were judged conceptually aligned but insufficiently
executable for implementation readiness because of the nine P1 gaps above.
Fresh exact-SHA Strict remains pending after local remediation; readiness is
unconfirmed and production implementation has not started.

## Local remediation ledger (not a review verdict)

The following data-only contract work records the local response to the nine
P1 findings and P2-1. It does not alter the historical verdict above and does
not establish a fresh Strict result.

- P1-1: the reference publication path now renders the full six-collection
  semantic payload and PlantUML from one validated model; exact bytes,
  artifact SHA-256 values, root descriptors, and schema-valid order/payload
  mutations are checked.
- P1-2: a frozen `NextValidatedDecision` carries the validated model, proof,
  request-owned context, pre-budget outcome, and gate decision; domain/root/
  stdout projections reject independently supplied authority fields.
- P1-3: the closed reason vocabulary `missing`, `component_only`, and
  `duplicate` is retained in response coverage, diagnostics, domain coverage,
  root manifest, and unavailable stdout projections.
- P1-4: typed target failures validate the proof base first, including exact
  causal edges, export-owner joins, and complete target rows; compound
  mutations are rejected before typed routing.
- P1-5: complete schema-valid graph vectors cover double alias, empty/multi
  star with default exclusion, and separate cycle/conflict whole-run failure
  projections through decision, domain, root, stdout, diagnostic, and exit 3.
- P1-6: re-export observations and raw edges are joined bijectively by owner,
  source/imported/original/exported names, syntax identity, and byte span;
  repeated `Foo as A`/`Foo as B` forms are consumed exactly once.
- P1-7: IdentifierName handling is pinned to the checked-in Unicode 15.0.0
  profile, including `Other_ID_Start`, `Other_ID_Continue`, and U+00B7; the
  compatibility and run-fingerprint preimages include the profile version.
- P1-8: all applicable source-root surfaces use the shared root-or-path
  schema, accepting `.` only in root context and rejecting non-root unsafe
  forms consistently.
- P1-9: raw response `max_stdout_bytes` is checked before UTF-8 decode and
  materialization, with exact-limit and limit+1 unavailable vectors.
- P2-1: the duplicate Round 11 Pass C HTML item is removed.

Local verification reports `244 passed` for `tests/contracts` and `1100 passed,
1 skipped` for the full pytest suite. `mypy`, `ruff check`, `ruff format --check`,
SpecDock validation (`nodes=10`), the HTML PlantUML/zoom validator (5/5), and
the TypeScript 5.9.2 trusted-profile gate (diagnostics=0; symbols=14) also
passed. These are local contract/evidence gates only; a fresh exact-SHA Strict
review remains pending. Canonical status therefore remains: fresh Strict
pending, readiness unconfirmed, and production implementation absent.
