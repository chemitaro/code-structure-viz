# Next semantic contract v1

Status: pre-implementation normative contract for Issue #8.

Round 12 review state: ChatGPT Use Strict returned `review_status: fail` with
P0=0, P1=8, P2=0 at exact SHA `48266f813353a7fd78e4e15d72ff6d33c4142827`
(CI `33435802167`, 7/7 success). Round 12 adds the same-model inverse-order
chain, one request-owned run context for null/manifest/semantic/PlantUML,
bounded raw-byte validation, NFC Unicode JSX tag segments, exported-name-only
re-export lookup, owner-module witness joins, shared `#` path rejection, and
separate missing/component-only/duplicate target vectors below. For a selected
program File, `missing` means the File exists but its Module and any Component referring
to the expected Module identity are absent; `component_only` means the Module is absent
while that Component remains; `duplicate` means more than one byte-identical Module row
exists for the same selected File, with only that selected identical duplicate narrowly
allowed before typed failure. All three reasons apply to file and directory targets and
project through response, diagnostic, domain, root manifest, unavailable stdout, and exit 3.
Fresh exact-SHA Strict is
pending, so readiness is unconfirmed and the production adapter/CLI remains
unimplemented. This local remediation does not change the recorded fail result.

Round 13 review state: Strict reviewed SHA `991516bf730f4f2ddb3d15067702dcfae95ec6b1`
with CI run `33446911714` (7/7 success) and returned `review_status: fail`,
P0=0, P1=9, P2=1. The local data-only response now covers exact six-collection
semantic/PlantUML publication from one immutable validated decision, proof-first
typed target routing, reason propagation, complete alias/star/cycle/conflict
vectors, bijective re-export joins, the pinned ECMAScript IdentifierName table,
shared root-or-path validation, and the pre-decode raw stdout byte cap. The
historical fail is preserved; fresh exact-SHA Strict is pending, readiness is
unconfirmed, and the production adapter/CLI is absent.

Round 14 remediation closes the remaining pre-implementation boundary. The
closed `NextRunDecision` union is the only input accepted by domain, root
manifest, stdout, and stderr projections:
`ValidatedResponseDecision` carries the schema-valid model/proof;
`PreResponseFailureDecision` owns a request-bound context when a validated
request exists, or an explicit request-independent context when it does not;
both carry a closed stage and
diagnostic, known/null counters, `payload_unavailable`, zero artifacts, and
exit 3; `NotApplicableDecision` owns the corresponding complete no-Next
outcome and exit 0. Node discovery/spawn/timeout/nonzero, adapter capture,
raw/decode/schema/reference/ID failures cannot create an independent domain
status. Fresh exact-SHA Strict is still pending, readiness is unconfirmed, and
the product implementation remains absent.

The machine-readable authority is:

- `schemas/next-semantic-v1.schema.json`
- `schemas/next-adapter-request-v1.schema.json`
- `schemas/next-adapter-response-v1.schema.json`
- `schemas/next-trusted-type-environment-v1.schema.json`
- `schemas/next-config-v1.schema.json`
- `schemas/next-domain-manifest-v1.schema.json`
- `schemas/next-limits-v1.schema.json`
- `schemas/next-source-plan-v1.schema.json`
- `schemas/next-process-launch-observation-v1.schema.json`
- `schemas/next-provenance-v1.schema.json`
- `schemas/next-compatibility-v1.schema.json`

These schemas materialize the field-level branch that will be integrated into the existing public registries during Issue #8 production implementation. They do not make the current CLI accept `--domain next` before that implementation.

The public `semantic-v1` registry is a discriminated union. Its common root
constrains only the discriminators and leaves domain payload fields to the
Python, SQLAlchemy, and Next branches. This prevents an unrelated domain's
`coverage` or entity shape from intersecting the Next branch. Contract vectors
cover complete empty, complete non-empty, and `partial_safe` Next snapshots,
plus Python-entity, wrong-status, and unknown-root mutations.

## Identity and ordering

- Module identity: project-owned repository-relative physical path.
- Component identity: Module ID plus NFC declaration key.
- Member identity: owner ID plus member-kind identity. Export aliases never create Components.
- Relation and Fact identity: kind-specific canonical tuple.
- IDs use a kind prefix and SHA-256 of canonical JSON identity bytes.
- Collections are unique and sorted by UTF-8 ID bytes. Ordered derived
  collections (`recognition_evidence`, diagnostics, `target_completeness`,
  `failed_files`, and every proof list) use canonical JSON UTF-8 bytes; the
  validator compares the submitted order directly and never sorts it first.

`identity_versions` is `{project:1,file:1,module:1,component:1,member:1,relation:1,fact:1,props_ir:1}`. `semantic_compatibility_id` is the SHA-256 of the canonical
preimage `{semantic_schema,identity_versions,algorithm_versions,semantic_profile_id}`.
The descriptor carries fixed algorithm
versions for recognition, export, props, relation, fact, and boundary
classification. A known-answer vector and an algorithm-change negative vector
are required; the value is not a self-reported opaque token.

## Members, relations, and facts

- Members are `export_binding`, `import_binding`, or `prop`.
- An `export_binding` is public only when one value export resolves uniquely to
  a Component; it carries that Component ID and never represents a value-only
  or type-only export. Before that projection, the adapter emits a complete
  independent `export_observations` stream. Python owns frozen UTF-8 source
  bytes and a closed module-level syntax census over repository-relative owner
  file, exact byte start/end span, token identity, syntax kind, canonical
  exported name, value/type role, re-export bit, and star bit. The scanner
  ignores function/class bodies, JSX, properties, regex/template/string
  literals, and comments; it accepts local lists, default alias/declaration/
  expression, `async function`, generic/type spans, multiline specifiers,
  Unicode IdentifierName (NFC), CRLF, and BOM. Body declarations terminate at
  their balanced closing brace; expression/list/star forms require a
  semicolon under the closed ASI policy. Node observations must exact-equal
  this census on syntax identity. Each observation also carries source
  specifier, imported/original name, resolved source Module, expanded exported
  name, and target declaration. Python recomputes alias, star (0..N excluding
  `default`), cycle, and conflict behavior from raw declarations and raw edges
  in `tests/fixtures/next_export_graph_raw.json`, then exact-compares public
  bindings, resolution witnesses, and `non_component_value_export_count`/
  `type_only_export_count`; omitted, duplicated, coordinated observation/
  binding/count omissions, star/type conflicts, or component substitutions are
  rejected. The data-only graph fixture
  `tests/fixtures/next_export_graph_cases.json` exercises the same independent
  resolver for explicit aliases, star expansion, cycles, and duplicate-star
  conflicts; these outcomes are canonical `component`/`value` or fail-closed
  `unknown` witnesses.
- Module relations are `static_import` and `literal_dynamic_import`.
- Component relations are `jsx_render` and internal-only `component_wrap`.
- Direct `client_entry` and `router_context` are Facts. Derived boundary roles remain Module facets.
- External and unresolved relation targets use a redacted package/export descriptor; no target source or absolute path is allowed.

## Project and reference invariants

`projects[]` and `files[]` are closed records. A project owns a disjoint root,
compiler options, and a bidirectional `file_ids` set; every file points back to
exactly one project. `effective_role` is derived from the ordered precedence
`control > context > program`, and `roles` is a unique canonical tuple. Module,
component, member, relation, and fact IDs use their own prefixes. Export/import
members belong to modules, prop members belong to components, and relation/fact
owners must exist. Internal targets must resolve to the right kind; only the
closed external/unresolved package descriptor may be a frontier. A data-only
validator enforces ownership, reference existence, collection uniqueness, and
canonical UTF-8 ID order because JSON Schema cannot express those joins.

The private adapter request additionally carries `content_base64`, byte size,
and SHA-256 for each frozen file. The same validator decodes the standard
base64 alphabet and checks `len(decoded) == size_bytes == digest preimage`.
The request envelope ID is `SHA-256(canonical-json(request without
request_id))`; the response must echo that exact ID and its `model_digest` is
`SHA-256(canonical-json(model))`.

Input/config/source-plan project projections are sorted by NFC UTF-8 root-path
bytes; semantic records and their discovered proof collections remain sorted
by record ID. Diagnostics, recognition evidence, target completeness, failed
files, and other derived arrays are canonical JSON UTF-8 order and are checked
against the submitted order without first sorting it. A two-project fixture
whose path and ID orders differ, plus a permuted CLI input, must produce equal
canonical source-plan and config digests.

`NextRunContext/v1` is the single run-level context copied through the response,
entity gate, domain manifest, root `run`, and stdout projection. It carries
`requested_formats`, `budget_requested`, `budget_resolved`, `budget_source`, and
the actual `stdout_selector`. The selector is `null` for the canonical run
summary, `manifest` for the exact committed manifest bytes, or a requested
`next:<format>` renderer. No surface fills in a missing format from
`FORMAT_ORDER` or infers provenance. The context's formats and selector are
fields of the run-fingerprint preimage, so changing either changes the
fingerprint.

Only a frozen file with `program` role and exact suffix `.ts`, `.tsx`, `.js`, or
`.jsx` (explicitly excluding `.d.ts`) may own a public Module. Components,
members, relations, and facts descend only from those program Modules. A direct
`.d.ts`, `package.json`, `tsconfig.json`, or `jsconfig.json` target therefore
fails with `CSV-NEXT-TARGET-001` and `payload_unavailable`; a directory may
retain context/control Files as provenance without creating semantic children.

## Partial-safe proof

The Node response includes the complete discovered record set, typed taints,
failure roots, causal edges, target-resolution witnesses, the independent
export-observation stream, export-resolution witnesses, and exclusions. Each
published model record appears in `proof.discovered_records` as
`{collection,record_id,taints}`; the record payload is joined by ID from the
same model. The optional `record` payload is reserved for a proof-only record
that is absent from the published model. This one-to-one shape prevents model
payload duplication from making `max_model_records` unreachable while keeping
proof-only evidence self-contained. It does not remove the separate ID item in
the proof array: the response schema therefore permits 20,000 structural proof
items, while the semantic `max_model_records` cap is 10,000 so exact and +1
model wires remain reachable below the aggregate/raw limits.
`collection`, taint kind, exclusion reason, and propagation rule are closed
vocabularies. Python derives the complete mandatory root seeds (including
the internal Component seed resolved from a path target, incoming explicit re-export/barrel Module, and
dependent bindings), causal edges, and taint fixed point from records, roots,
and the closed rule/ownership table; adapter-provided edges, taints, and counts
are not trusted. It checks that every discovered record is exactly
published/excluded/failed once, that every published reference is untainted or
a closed frontier, that request target keys/status/IDs equal the independently
resolved model, and that coverage counts equal the proof decomposition. Counts
alone are not evidence. The validator contract is versioned as
`code-structure-viz.next-reference-validation/v1` and lives in
`tests/contracts/next_reference_validation.py` until production code owns it.

### Proof reason semantics

The adapter proof vocabulary is intentionally narrower than the Python-owned
limit vocabulary. `not_selected` and selection-only `target_excluded` are
bookkeeping and preserve `complete`; they do not by themselves imply data
loss. `unsupported` is complete when the unknown frontier is represented by
`CSV-NEXT-UNSUPPORTED-001` and `unknown_relation_count`, rather than silently
dropping a promised fact. A localized `tainted`/`failed` disposition becomes
`partial_safe` only when a non-empty failure root and its causal locality proof
cover the omitted region. `over_budget` is invalid in adapter `excluded` or
`failed` records; `EntityBudgetGate` alone owns the later
`CSV-NEXT-LIMIT-005` decision. An explicit target identity failure remains
typed `payload_unavailable`.

The minimum executable matrix is: unrelated `not_selected` → complete/exit 0;
intentional unsupported → complete plus diagnostic; localized taint with a
root → partial_safe/exit 3; adapter `over_budget` → protocol rejection. The
same reason remains distinguishable in proof, coverage, diagnostics, and the
target-failure stdout result where applicable.

## PropsTypeIR/v1

The closed recursive variants are primitive, ordinal `type_parameter`,
`redacted_literals`, scope-specific `reference`, array, tuple, function,
union/intersection, object, and opaque. `redacted_literals` carries only
`base` and a positive `count`; literal values are never emitted. A tuple has
`elements[{type,optional}]`, an optional `rest: TypeNode|null`, and
`readonly`. Functions and object call signatures have `type_parameter_count`,
`this_type`, `parameters[{type,optional,rest}]`, and `return_type`; parameter
names and ordinals are never emitted. Object values include properties, index
signatures, and call signatures. Repository references use a Module ID and a
non-null export; external references use a safe bare specifier and
`IdentifierName|default`; trusted references use the fixed four-module trusted
set with a non-null export, or the bundled `typescript/lib` standard-library
namespace, which may use a null export for a global/lib symbol.
Variant mutation vectors cover every branch, wrong-scope fields, missing
function/call shape, invalid rest placement, and unsafe reference strings.

## Compatibility

The public snapshot and manifest publish `semantic_compatibility_id` and identity versions. Issue #9 may compare sides only when the compatibility ID is exact-equal. Config, source-plan, Node patch, and adapter patch differences remain provenance rather than semantic compatibility when the ID stays equal.

The trusted declaration manifest is closed to the four reserved module
specifiers (`react`, `react/jsx-runtime`, `react/jsx-dev-runtime`,
`next/dynamic`) and the three reserved globals (`Array`, `JSX`,
`ReadonlyArray`). Its ordered file and certified-symbol sets are covered by a
manifest SHA-256 over the descriptor without its `sha256` field. A target
declaration, augmentation, or path redirect for one of those namespaces is a
trust failure; target paths are also compared after NFC normalization against
the trusted virtual paths. Each physical fixture's UTF-8 bytes, size, and
SHA-256 are checked against the physical-to-virtual mapping; certified symbol
signature digests are derived by the TypeScript 5.9.2 Program AST/TypeChecker
and exact-compared with a checked-in expected inventory. The gate requires
zero parse and semantic diagnostics, and trusted TypeIR references accept only
the certified module/export identities (the bundled `typescript/lib` root is
the sole non-symbol standard-library reference). Recognition evidence is
interpreted against the same closed profile; it cannot introduce an
uncertified callable or class. The anti-shadowing witness covers all seven
reserved names.

## Exact identity preimages

An ID is `next:<kind>:<sha256>`, where the hash is over the following closed
preimage, not over serialized source text or collection position:

```text
{kind, version: 1, identity: <tuple below>}
```

| record kind | identity fields |
| --- | --- |
| Project | `root` |
| File | `project_id, path` |
| Module | `project_id, path` |
| Component | `module_id, declaration_key` |
| ExportBinding | `owner_id, exported_name, role` |
| ImportBinding | `owner_id, imported_name, role, source` |
| Prop | `owner_id, name` |
| static/dynamic relation | `kind, source_id, target, role, reexport, boundary_effect` |
| JSX relation | `kind, source_id, target` |
| wrapper relation | `kind, source_id, target_component_id` |
| Fact | `kind, owner_id, value` |

`range`, source spelling, local aliases, occurrence counts, type payload,
optional/default evidence, and ordering are not identity. Python recomputes
every ID and rejects a stale ID after any identity-field mutation. A request
project/file projection is compared to the response model exactly: compiler
options, role tuple, effective role, byte size, and SHA-256 are all included;
only private `content_base64` is omitted from the public model projection.

## Role, relation, and fact invariants

The canonical role-array order is `control`, `context`, `program`; effective
precedence is a separate `control > context > program` mapping. All seven
non-empty role subsets are valid only with the matching effective role.

`static_import` and `literal_dynamic_import` are independent discriminated
branches. A literal dynamic import is always `role=value`,
`reexport=false`, and `boundary_effect=none`. The only boundary effect is
`server_to_client_entry` on an internal static value edge whose source is a
`server_candidate` and whose target is a `client_entry`; no duplicate boundary
edge is emitted. Every Module's `client_entry` and `router_context` attributes
have an exact Fact-record mirror, with one owner per Fact kind/value.

## PropsTypeIR canonical semantics

The recursive validator applies the same rules as the schema: same-kind union
or intersection nesting is rejected (the adapter must flatten first), members
and object properties/signatures are canonical sorted and deduplicated, tuple
and function rest parameters are final and non-optional, and type parameters
use a zero-based ordinal scoped to their declaring signature. Repository
references require an existing Module ID; external references use a safe
package specifier; trusted references are limited to the certified profile.

The limits are hard boundaries: depth 16, 512 TypeIR nodes per prop, 64 union
members, 64 intersection members, 256 direct properties, 256 total nested
properties, and 16 signatures per Component. Boundary vectors cover both the
accepted limit and the first rejected value. Over-limit local type subtrees
become `opaque` with a catalog reason; they are not silently truncated.

## Independently proven partial-safe output

The adapter response includes all discovered records, typed taints, failure
roots, causal edges, target witnesses, and the published/excluded/failed
decomposition. Python derives the taint fixed point from the roots and the
closed rule/ownership table; adapter-provided `taints` and counts are not
trusted. Disconnected causal edges, illegal source/target kinds, vacuous
roots, missing/excess taints, overlaps, and stale target witnesses are
rejected.

Coverage is recomputed from that proof. `affected_ids` is the sorted taint
closure; `taint_frontier` is the sorted untainted internal reference frontier;
`failed_files` is the sorted failed file/path-reason projection;
`opaque_reason_counts` is recursively derived from every Prop TypeIR;
`unknown_relation_count` counts unresolved relation targets;
`correlation_losses`, non-component value exports, and type-only exports are
closed, sorted projections with owner/reference checks. A `partial_safe`
semantic and PlantUML pair must use the same validated subset.

For stdout target failures, the canonical projection is the sorted,
duplicate-free `target_failures: [{target_key, reason}]` array. It is present
only on the target-related `payload_unavailable` branch and preserves one row
per failed target, including repeated identical reasons on different targets.
Available, `not_applicable`, generic unavailable, fatal, and interrupted
results must not carry either `target_failures` or the legacy single `reason`
field. The branch uses stable reason `target_payload_unavailable`.

`coverage.counts.internal_entities` is recomputed as the number of published
internal Modules plus Components only. Members, relations, facts, projects,
external frontiers, and proof-only records do not consume `max_entities`; the
complete all-record cap is the separate `max_model_records` limit. Structural
model validation applies only `max_model_records` and returns the recomputed
entity count. An independent `EntityBudgetGate` runs after response
validation and before publication; an overrun emits `CSV-NEXT-LIMIT-005`,
records the actual count, produces a manifest-only `payload_unavailable`
outcome, and publishes no artifacts. Boundary vectors cover 500 success, 501
unavailable, 501 under a 600 override, and a compositional 10,001-record
model-cap failure. The resolved `max_model_records` is 10,000 so that this
cap remains reachable on the wire after the ID-only proof rows and within the
100,000 aggregate-array and 16 MiB raw-byte limits.

## Diagnostics, config, and status cross-checks

Compact semantic diagnostics are catalog projections keyed by code. Their
severity, recoverability, outcome, count, and path/symbol permission must
match `schemas/next-diagnostic-catalog-v1.json`; the fixed public message and
domain are supplied by the public diagnostic projection. Complete snapshots
may contain only `complete` diagnostics, while partial snapshots may contain
only `partial_safe` diagnostics. Unknown codes, severity/ref/status mutations,
and the historical FLOW fixture's wrong path reference are rejected.

Explicit targets use only the public canonical key
`path:<repository-relative-file-or-directory>` (NFC, non-root POSIX path value is
1--4096 UTF-8 bytes; the root directory sentinel is exactly `.`). Empty
segments, embedded `.`/`..`, trailing slash, control characters, backslash, and
non-NFC spellings are rejected before target resolution.
Internal Module/Component IDs are not public target syntax. A file resolves
its frozen file/Module/Component set only when the direct file is a program
file; a directory resolves its complete canonical descendant frozen set, and
multiple descendants are normal. A direct context/control file is not a
semantic target and fails even when frozen. File→Module `missing`/`component_only`/
`duplicate`, project-scope ambiguity, out-of-scope, or any selected
tainted/excluded/failed record is `CSV-NEXT-TARGET-001`, `payload_unavailable`,
and no artifact. For a selected program File, `missing` means the File exists
but its Module and any Component referring to the expected Module identity are
absent; `component_only` means the Module is absent while that Component remains;
`duplicate` means more than one byte-identical Module row exists for the same
selected File, with only that selected identical duplicate narrowly allowed
before typed failure. All three reasons apply to file and directory targets and
project through response, diagnostic, domain, root manifest, unavailable stdout,
and exit 3.
The adapter must return exactly one canonical resolution row per requested key,
duplicate-free; Python resolves keys against the frozen published model and
rejects missing, extra, substituted, permuted, or `failed`-as-resolved rows.

`ResolvedNextConfig` and `NextSnapshotRequest` are defined in
`docs/contracts/next-config-v1.md`. The domain manifest and root manifest
carry exact projections, recomputed project/config/source-plan/run digests,
limits, budget, artifacts, and diagnostics. Node provenance is a closed union:
`not_applicable` has no version, `available` has a Node version >=22, and
`unavailable` has a null version plus a closed failure kind.

The complete status vector ties the domain manifest, root run status/exit,
run-summary, stdout result, published bytes, artifact SHA/size, and stderr
diagnostics. Complete and `partial_safe` selectors return the exact published
bytes; `not_applicable` and `payload_unavailable` return only a typed
unavailable result. `--stdout` omitted (`None`) returns the canonical run
summary, `manifest` returns the exact committed manifest bytes, and
`next:semantic-json`/`next:plantuml` return the selected artifact or a typed
unavailable result. Fatal and interrupt runs have no manifest and cannot be
reinterpreted as a domain result; usage exits with code 2, no manifest/domain,
and an empty stdout stream.

## Round 15 decision and provenance closure

Every Next outcome is one member of the closed `NextRunDecision` union:
`ValidatedResponseDecision`, `PreResponseFailureDecision`, or
`NotApplicableDecision`. Each member carries one immutable
`NextPublicationContext` containing the sealed SourceView descriptor/fingerprint,
the FinalSourceAcquisitionPlan descriptor/digest/seal identity, public Next
config/request (when a request exists), complete compatibility descriptor and
identity versions, actual toolchain/trusted environment,
`NextRunContext`, and the run-fingerprint preimage. Domain, root manifest,
stdout, stderr, and artifact writers consume this decision only; they do not
rebuild a request or default config from a fixture. When an early failure
cannot produce an adapter request, `NextDecisionContext` carries the known
run identity, closed failure kind/stage/code, known or null counts, outcome,
payload flag, and exit code.

`ValidatedResponseDecision` deep-copies and checks the request at construction:
schema and request ID, exact run-context and target equality, gate resolved
limits, allowed pre-budget transition, and canonical target/export failure
rows. Mutating the caller's nested request, model, proof, or publication
context after construction cannot alter the decision.

The response limit authority is derived from actual wire collections:
`published_model_records` is the sum of model collection items;
`proof_only_records` counts only proof payload records absent from the model;
`discovered_records` is their sum. Submitted summary counts and the former
`proof_records or model_records` shortcut are not authoritative. Raw bytes are
checked before decode, aggregate JSON-array items before materialization, and
the model-record limit after structural response validation. The three named
byte boundaries (`max_adapter_stdout_capture_bytes`,
`max_adapter_response_bytes`, `max_selected_stdout_bytes`) have separate
exact/+1 outcomes; a selected-artifact copy failure does not rewrite the
validated semantic outcome.

Target-unavailable stdout is restricted to `next:semantic-json` and
`next:plantuml`. It carries at most one canonical sorted row per target from
the closed reasons `missing`, `component_only`, `duplicate`, `out_of_scope`,
`non_program`, `control_context`, `project_ambiguity`, and `selected_taint`.
Available, not-applicable, generic unavailable, fatal, and interrupted
branches carry neither this array nor the legacy single `reason`.

The source contract is `SourceDiscoveryIntent` → two-phase single-read → final
drift check → one `seal_source_acquisition` operation producing both plan and
view. A caller cannot inject a plan-only or view-only authority, and no
filesystem read occurs after the seal. Role/effective-role, local-extends and
control closure, file digest/size, duplicate-read, and post-drift mismatches
are fail-closed.

IdentifierName is pinned to the checked-in Unicode 15.0.0 table and used by
context-specific `is_identifier_name`, `is_binding_identifier`, and
`is_declaration_key` predicates. The table includes Other_ID sets, U+00B7,
and Join_Control; reserved words are rejected only in binding contexts. The
full scalar-range classification bitstream has a known-answer SHA-256, so
host `unicodedata.category()` changes cannot alter semantics. The same rules
cover component declarations, import/export names, external/trusted
references, JSX segments, and re-export witnesses.

`BoundaryRolePropagation/v1` is the sole role authority. A client-entry seed
itself is not a `client_dependency`; only static value-closure targets are.
A client application seed is not a `server_candidate`, and server traversal
stops before a client entry. A dual role requires two distinct closures.
Roles are recomputed from facts, router context, and static value edges and
must exactly equal submitted model roles. All public JSON and stdout-result
bytes use the existing lexicographic canonical encoder (`sort_keys=True`,
NFC, UTF-8, LF), including `target_failures`.

## Round 16 contract closure

Round 16 keeps the semantic model data-only and closes the remaining
implementation choices before a production adapter is started. The
`NextPublicationContext` is mandatory on every `NextRunDecision` variant and
binds the actual source seal, public/private request snapshots, observed
toolchain, trusted environment, compatibility descriptor, and run-fingerprint
preimage. A pre-response config/project/source failure uses a request-
independent context with nulls for unobserved values; it never invents a
project, request, or config from a fixture.

The private request is a deep-copied `ValidatedAdapterRequest`. Its request ID,
virtual files' base64/size/digest/canonical bytes, limits, targets, and run
context are checked before the response boundary accepts it. The boundary
order is raw cap, bounded decode/aggregate, closed schema, base/path/reference/
proof validation, actual model/proof-only count, model gate, entity gate, and
selected artifact copy. Structural resource overrun uses `CSV-NEXT-LIMIT-003`;
malformed, closed-schema, and proof violations use `CSV-NEXT-PROTOCOL-001`.

Record counts are derived from actual wire data: published model collections
are summed, proof-only records count only payload records absent from those
collections, and `discovered_records` is their sum. The selected artifact copy
has its own exact/+1 boundary and may become unavailable without rewriting the
validated semantic status. All capture, stderr, and selected-copy measurements
are sealed in the final publication decision before any projection is written.

Source acquisition derives the final plan and source view together from one
intent/seal operation. Source locality is represented by an immutable
`SourceFailureLedger`: independently proven local safe subsets use
`CSV-NEXT-SOURCE-001`/`partial_safe`, while non-isolatable failures use
`CSV-NEXT-SOURCE-003`/`payload_unavailable`. Target failures use the eight
closed reasons and exactly one row per failed target only on the two Next
target-unavailable selectors.

The contextual Unicode 15.0.0 table is used for binding identifiers,
declaration/export keys, JSX segments, re-export witnesses, and
external/trusted references. Other_ID sets, U+00B7, Join_Control, reserved
words, NFC/control/post-15.0 cases, and the full scalar classification digest
are known-answer tested. `BoundaryRolePropagation/v1` derives roles from
facts/router/static value closure only: a client seed is neither derived role,
server traversal stops before a client entry, and dual role requires two
distinct closures. Canonical output remains sorted-key JSON, NFC, UTF-8, LF.

Round 16 review of SHA `732477c72c7e05d3f15818ba8a3f75a4c97dc5a9` (CI
`33494926439`, 7/7 green) historically returned `P0=0 / P1=16 / P2=3 / fail`.
Fresh current-SHA Strict is pending, readiness is unconfirmed, and production
implementation is absent.

## Round 17 decision, target, and ordering closure

All semantic and publication fields are reached from the closed decision
union. The immutable `SourceFailureLedger` derives isolated/safe-subset and
target-tainted status from the sealed source graph, project ownership, target
set, failure roots, and proof roots. It does not accept caller-supplied
locality booleans. If proof introduces an unavailable target ID, resolution is
re-run against the sealed graph; `selected_taint` therefore reaches the same
typed target-unavailable branch as an initial resolver failure.

The eight target reasons are `missing`, `component_only`, `duplicate`,
`out_of_scope`, `non_program`, `control_context`, `project_ambiguity`, and
`selected_taint`. Each failed target has exactly one reason, rows are unique
and canonical-sorted, and the array is forbidden on available,
not-applicable, generic-unavailable, fatal, and interrupt branches. The
selector branch itself is a closed union of summary, manifest, semantic
artifact, PlantUML artifact, and typed unavailable output.

The complete validation contract is `raw cap -> bounded decode/aggregate ->
closed schema -> base/path/reference/proof -> actual model + proof-only count
-> model gate -> entity gate -> selected copy`. `LIMIT-003` owns configured
byte/structural resource boundaries; `PROTOCOL-001` owns malformed,
closed-schema, and proof violations. Semantic projects are ID ordered and
request/config/source-plan/root paths are root ordered; validators inspect
submitted order before canonical sorting. The full projection still uses
lexicographic sorted-key JSON, NFC, UTF-8, and LF. Fresh current-SHA Strict is
pending, readiness is unconfirmed, and production implementation is absent.

## Round 19 source, publication, and provenance closure

Round 19 requires the source seal to exist before the private request. The
trusted enumerator accepts only `SourceDiscoveryIntent` (project roots,
known control candidates, fixed rules), decodes the frozen control closure
with duplicate-key rejecting JSONC rules, and derives config, local extends,
source roots, roles, and final membership internally. The request file set is
checked against that immutable seal; no request-derived seal reconstruction
is a source authority.

Source acquisition returns the closed union
`CompleteSourceSeal | PartialSourceSeal | SourceAcquisitionUnavailable |
SourceIntegrityFatal`. `PartialSourceSeal` carries a safe file set and a
`SourceFailureLedger` derived from seal-owned raw graph reachability. Local
safe proof emits `CSV-NEXT-SOURCE-001`/`partial_safe`; an unisolated or
integrity-safe failure emits `CSV-NEXT-SOURCE-003`/`payload_unavailable`.
The same source seal and ledger identity flow into the safe request,
`ValidatedResponseDecision`, and `NextPublicationContext`.

Validated response bytes are opaque decision authority. The final
`PublicationBoundaryDecision` internally derives and seals all summary,
manifest, artifact, and typed-unavailable candidate bytes from the semantic
decision and actual measurements. No external candidate map, preselected
payload, status, or diagnostic bytes are accepted. Selected-copy exact/+1 is
two-stage and non-circular: a success candidate is measured once; overrun
disposes partial bytes and persists one failure descriptor without re-copying
it. The semantic outcome is not silently rewritten.

Process launch observation is the closed fixture/production union in
`next-process-launch-observation-v1.schema.json`. Production records
darwin/linux/windows OS identity, verified handle, hash/version, actual spawn
primitive, post-spawn equality, FD lifecycle, process group, and TOCTOU
failure point. Reference validation does not exercise a host process and is
not an OS process-level acceptance claim.

`next-provenance-v1` records an observed prefix and explicit unobserved suffix
for request-independent failures. `next-config-v1` requires a disjoint
`request_independent` boolean branch, and `NextRunContext` checks selector,
format, and budget correlations. Path-only ordering is NFC UTF-8 byte order
after `path:` removal; object rows retain canonical JSON order. Fresh
current-SHA Strict is pending, readiness is unconfirmed, and production
implementation is absent.

## Round 20 source authority and optional Node

Semantic output is considered only after `PackageApplicabilityMatrix` and the
sealed source result are known. Direct `dependencies.next` or
`devDependencies.next` is the only applicability evidence; an all-
`non_applicable` matrix produces a closed not-applicable run without a Node
probe. Malformed package/control evidence is unavailable rather than an empty
semantic model. The frozen-byte source graph and segment-grammar membership
remain the only source facts used by the semantic projection.

`SourceAcquisitionDecisionProjection` keeps complete, local partial-safe,
payload-unavailable, and fatal source outcomes distinct before the semantic
artifact is selected. The shared stage-dependent provenance validator prevents
an early failure from acquiring synthetic limits, source plan, toolchain,
trusted environment, or budget. Round 20 executable evidence is
`test_round20_package_applicability_matrix_is_direct_dependency_only`,
`test_round20_source_integrity_has_one_fatal_vs_payload_unavailable_projection`,
and `test_round20_stage_provenance_is_one_canonical_shape_and_rejects_mismatch`.
Fresh current-SHA Strict remains pending, readiness is unconfirmed, and
production implementation is absent.

## Round 21 semantic authority

Semantic publication begins only after the frozen package observations produce a valid
`PackageApplicabilityMatrix`. Direct non-empty Next declarations alone make a project applicable; an all-
non-applicable matrix produces `NotApplicableDecision` without Node probing, mixed matrices retain only
applicable roots, and malformed package evidence is global unavailable. The matrix and its project filter,
toolchain permission, diagnostic, domain/root manifest, stdout/stderr, and exit are validated as one projection.

The sealed source graph recognizes static and side-effect imports, export-from, literal dynamic import,
literal require, and `baseUrl`/`paths` aliases while excluding comment/template/regex decoys. Every unresolved,
ambiguous, unsupported, or external dependency is an `open_edge`; no omitted edge can be used as a locality
proof. Config control uses the explicit project-local `./...` extends grammar and segment include/exclude
grammar, with malformed control as typed global unavailable.

Semantic request-bound and request-independent outcomes share the catalog-derived stage/code provenance union.
The normative process evidence is `next-process-launch-observation-v1`; its darwin/linux/windows security
identity includes ephemeral values, while the stable fingerprint intentionally excludes FD/device/inode. All
downstream semantic bytes come from the decision-owned sealed model. Fresh current-SHA Strict is pending,
readiness is unconfirmed, and production implementation is absent.
