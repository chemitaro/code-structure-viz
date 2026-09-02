# Diagnostic v1 contract

`schemas/next-diagnostic-catalog-v1.json` is the single authority for the
Next diagnostic code, fixed message, severity, recoverability, outcome, and
safe reference permission. The public `schemas/diagnostic-v1.schema.json`
requires those values for every `CSV-NEXT-*` record; `run-manifest` domain and
top-level diagnostics use the same public record.

`ref_permission` is structural, not advisory:

| permission | public fields |
| --- | --- |
| `none` | `path=null`, `symbol=null` |
| `path` | non-empty relative `path`, `symbol=null` |
| `symbol` | `path=null`, non-empty safe `symbol` |
| `path_or_symbol` | exactly one of `path` and `symbol` |

All Next diagnostics use `domain=next` and `line=null`; source content,
absolute paths, compiler text, and captured stderr are never copied into the
message. The Next domain manifest may carry these public records as its
`diagnostics` array. The stderr writer emits fixed catalog messages only and
never emits raw adapter output. `stdout-result/v1` carries only the typed
outcome/reason projection and never carries a diagnostic body.

The following outcome mapping is normative:

- applicability is `not_applicable`;
- flow, source, and type-local failures are `partial_safe` when the proof
  contract succeeds;
- unsupported runtime patterns are `complete` with an informational record;
- configuration, project, target, trust, process, protocol, identity, and
  resource-limit failures are `payload_unavailable`.

## Round 15 closed failure routing

The `NextRunDecision` union is the sole authority for diagnostic stage, code,
safe references, known/null counts, outcome, and exit projection. A
request-independent `NextDecisionContext` is used when configuration or
project/source discovery fails before a schema-valid adapter request can be
made. Downstream code must not synthesize a default request or collapse a
specific catalog entry into a generic protocol assertion.

`CSV-NEXT-SOURCE-001` means a local source failure with an independently proven
safe subset (`partial_safe`, exit 3). A source failure whose impact cannot be
isolated is `CSV-NEXT-SOURCE-003` (`payload_unavailable`, path reference,
manifest-only, exit 3); `CSV-NEXT-SOURCE-002` remains the symlink-specific
unavailable code. Intentional unsupported behavior is complete with
`CSV-NEXT-UNSUPPORTED-001` and unknown coverage. `over_budget` is not an
adapter proof reason: the Python EntityBudgetGate alone emits
`CSV-NEXT-LIMIT-005`.

Target resolution uses `CSV-NEXT-TARGET-001` with one stable reason per target:
`missing`, `component_only`, `duplicate`, `out_of_scope`, `non_program`,
`control_context`, `project_ambiguity`, or `selected_taint`. References obey
the catalog's exact `none`, `path`, `symbol`, or `path_or_symbol` permission.
The reason rows are retained only by the target-related unavailable stdout
branch; generic unavailable, not-applicable, complete, fatal, and interrupt
branches cannot carry them.

The byte-limit codes have ordered measurement points: child capture first,
complete private response raw bytes before decode, aggregate arrays before
materialization, model records after schema/proof validation, and public
selected-artifact copy after rendering. Exact values are accepted; +1 is
all-or-none and never exposes partial adapter or artifact text.

## Round 16 catalog-derived routing

The failure matrix is derived from the diagnostic catalog rather than from a
free stage/code cross product. Each row fixes its failure kind, allowed stage,
diagnostic code, reference permission, known/null counts, outcome, and exit
code. A mismatched stage or outcome is a contract error; a generic assertion
must not erase a specific source, trust, schema, reference, or semantic code.

Validation precedence is raw response byte cap, bounded decode and aggregate
array measurement, closed schema, base/path/reference/proof validation, actual
model/proof-only count, model gate, and entity gate. Structural resource
overruns (per-array, aggregate, string, and depth) use
`CSV-NEXT-LIMIT-003`; malformed JSON, closed-schema violations, and proof
violations use `CSV-NEXT-PROTOCOL-001`. A compound response with both a proof
error and model overrun therefore reports the protocol error first.

`CSV-NEXT-SOURCE-001` is reserved for an independently proven local safe
subset. Non-isolatable source failure is `CSV-NEXT-SOURCE-003` and is a
schema-valid request-independent manifest-only `payload_unavailable` branch.
Intentional unsupported behavior is complete with
`CSV-NEXT-UNSUPPORTED-001`. The eight target reasons remain target-scoped and
are emitted only by the Next target-unavailable stdout branch.

## Round 17 provenance and closed routing

The diagnostic matrix is discriminated by decision failure kind and observed
stage. A request-independent failure records only values observed before that
stage and uses explicit null/absence for the rest; a later projection cannot
invent request, project, config, toolchain, trusted environment, or source
plan fields. `SourceFailureLedger` distinguishes proven local safe subset
(`CSV-NEXT-SOURCE-001`/`partial_safe`) from non-isolatable source failure
(`CSV-NEXT-SOURCE-003`/`payload_unavailable`) by sealed graph evidence, not a
caller boolean. Proof-derived target taint is resolved again and retains one
of the eight target reasons through every surface.

The catalog's precedence is raw cap, bounded decode/aggregate, closed schema,
base/path/reference/proof, actual model/proof-only count, model gate, entity
gate, and selected copy. `CSV-NEXT-LIMIT-003` is the one configured
byte/structural resource message; `CSV-NEXT-PROTOCOL-001` is reserved for
malformed, closed-schema, and proof violations. A final immutable
`PublicationBoundaryDecision` owns the diagnostic JSONL bytes and all
measurements, so stderr is projected from sealed bytes rather than re-rendered
from a separate status. Fresh current-SHA Strict is pending and production
implementation is absent.

## Round 18 closed diagnostic provenance

The diagnostic catalog is also the validator for the request-independent
branch. Its `failure_stage`, `failure_code`, reference permission, known/null
counts, outcome, and exit are one closed row; a stage/code combination not in
that row is invalid. `CSV-NEXT-TARGET-001` requires exactly one reason per
failed target, and only the eight catalog reasons are accepted:
`missing`, `component_only`, `duplicate`, `out_of_scope`, `non_program`,
`control_context`, `project_ambiguity`, and `selected_taint`. Other diagnostic
codes must omit the reason field. Target keys use the shared next path grammar
and symbols use the closed safe-ID grammar.

After proof-derived unavailable IDs are recomputed against sealed roots and
taint, the same reason is carried through resolver, proof, decision,
diagnostic, domain, root manifest, stdout, and exit. The final publication
decision owns the exact diagnostic JSONL bytes, so a writer cannot substitute a
new status or measurement. Round18 reference vectors exercise positive and
negative discriminator/reason cases, schema-valid bytes, and canonical path
ordering. Fresh current-SHA Strict is pending, readiness is unconfirmed, and
production implementation is absent.

## Round 19 closed stage provenance and source outcomes

The stage-dependent provenance schema is a closed `oneOf`. A
request-independent failure records the observed prefix together with its
stage and catalog code; every later field is explicitly
`{"state":"unobserved","value":null}`. A source-selection/read/integrity
failure may retain limits and source-plan observations only when those values
were measured before the failure. Configuration and project failures do not
receive synthetic limits, toolchain, trusted environment, process descriptor,
compatibility, budget, request, or source plan. The nested and top-level
`request_independent` discriminators are mandatory and mutually exclusive
with the normal resolved branch.

The source acquisition result is a closed union. A proven safe local subset
uses `CSV-NEXT-SOURCE-001` with `partial_safe`; an unisolated read or control
failure uses `CSV-NEXT-SOURCE-003` with `payload_unavailable`. The ledger
derives locality and target taint from the sealed raw graph and includes the
source-seal digest. It does not accept caller booleans, replacement edges, or
caller-provided seal identifiers. The safe subset request carries the same
seal and ledger identity into the response decision and publication context.

The diagnostic code and stage are validated together, before model/entity
budget routing. Structural resource boundaries use `CSV-NEXT-LIMIT-003`, and
malformed/schema/proof violations use the catalog's protocol code. Target
reason rows remain restricted to `CSV-NEXT-TARGET-001` and its selected Next
unavailable branch.

Round 19 executable evidence includes
`test_round19_stage_provenance_reference_rejects_stage_code_and_prefix_mutations`,
`test_round19_next_config_discriminator_is_required_and_disjoint`,
`test_round19_source_acquisition_union_is_typed_and_fail_closed`, and
`test_round19_partial_source_result_preserves_safe_subset_and_ledger_identity`.
Fresh current-SHA Strict is pending, readiness is unconfirmed, and production
implementation is absent.

## Round 20 closed source, applicability, and provenance projection

The source result projection is closed before diagnostic routing. A malformed
or unavailable control/package observation cannot become a partial empty config:
it is `SourceAcquisitionUnavailable` with `CSV-NEXT-SOURCE-003`,
`payload_unavailable`, manifest-only availability, and exit 3. A proven local
safe subset remains the only `CSV-NEXT-SOURCE-001`/`partial_safe` path. Revision
drift, duplicate reads, post-seal reads, and source digest/size integrity
failures are `SourceIntegrityFatal` with fatal outcome, no manifest, and exit 1.
These stage, code, outcome, payload/manifest flags, stdout reason, and exit
values are one `SourceAcquisitionDecisionProjection`, not independently chosen
surface fields.

Before that projection, `PackageApplicabilityMatrix` classifies each root from
direct package.json `dependencies.next`/`devDependencies.next` only. Missing or
non-direct roots are non-applicable; malformed package bytes, duplicate keys,
invalid tables, and invalid versions are malformed. An all-non-applicable
matrix is a closed not-applicable run and does not probe Node.

The source graph and control membership are derived from the frozen seal, not
from a caller graph or fallback fixture. The same canonical provenance validator
is used for `NextDecisionContext` and `NextPublicationContext`: stage/code is a
closed pair, observed values form a prefix, and later values are explicit
`unobserved`/`null`. The executable Round 20 evidence is
`test_round20_source_integrity_has_one_fatal_vs_payload_unavailable_projection`,
`test_round20_stage_provenance_is_one_canonical_shape_and_rejects_mismatch`, and
the package/source acquisition tests. Fresh current-SHA Strict remains pending,
readiness is unconfirmed, and production implementation is absent.
