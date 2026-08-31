# Next semantic contract v1

Status: pre-implementation normative contract for Issue #8.

Round 8 review state: ChatGPT Use Strict returned `review_status: fail` with
P0=0, P1=4, P2=0. The four findings are reflected below and in the data-only
schemas/reference vectors; a fresh exact-SHA Strict review is pending, so
readiness is unconfirmed and the production adapter/CLI remains unimplemented.

The machine-readable authority is:

- `schemas/next-semantic-v1.schema.json`
- `schemas/next-adapter-request-v1.schema.json`
- `schemas/next-adapter-response-v1.schema.json`
- `schemas/next-trusted-type-environment-v1.schema.json`
- `schemas/next-config-v1.schema.json`
- `schemas/next-domain-manifest-v1.schema.json`
- `schemas/next-limits-v1.schema.json`
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
  independent `export_observations` stream. Python owns a frozen UTF-8 source
  byte fixture and a closed syntax census over repository-relative owner file,
  exact byte start/end span, token identity, syntax kind, canonical exported
  name, value/type role, re-export bit, and star bit. Node observations must
  exact-equal this census on syntax identity. Their
  `component|value|type|unknown` resolution and optional Component ID are then
  cross-checked against the model/TypeChecker witness. Python derives and
  exact-compares public bindings, resolution witnesses, and
  `non_component_value_export_count`/`type_only_export_count`; omitted,
  duplicated, coordinated observation/binding/count omissions, star/type
  conflicts, or component substitutions are rejected.
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

Only a frozen file with `program` role and exact suffix `.ts`, `.tsx`, `.js`, or
`.jsx` (explicitly excluding `.d.ts`) may own a public Module. Components,
members, relations, and facts descend only from those program Modules. A direct
`.d.ts`, `package.json`, `tsconfig.json`, or `jsconfig.json` target therefore
fails with `CSV-NEXT-TARGET-001` and `payload_unavailable`; a directory may
retain context/control Files as provenance without creating semantic children.

## Partial-safe proof

The Node response includes the complete discovered record set, typed taints,
failure roots, causal edges, target-resolution witnesses, the independent
export-observation stream, export-resolution witnesses, and exclusions.
`collection`, taint kind, exclusion reason, and propagation rule are closed
vocabularies. Python derives the complete mandatory root seeds (including
export target Component, incoming explicit re-export/barrel Module, and
dependent bindings), causal edges, and taint fixed point from records, roots,
and the closed rule/ownership table; adapter-provided edges, taints, and counts
are not trusted. It checks that every discovered record is exactly
published/excluded/failed once, that every published reference is untainted or
a closed frontier, that request target keys/status/IDs equal the independently
resolved model, and that coverage counts equal the proof decomposition. Counts
alone are not evidence. The validator contract is versioned as
`code-structure-viz.next-reference-validation/v1` and lives in
`tests/contracts/next_reference_validation.py` until production code owns it.

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

`coverage.counts.internal_entities` is recomputed as the number of published
internal Modules plus Components only. Members, relations, facts, projects,
external frontiers, and proof-only records do not consume `max_entities`; the
complete all-record cap is the separate `max_model_records` limit. Structural
model validation applies only `max_model_records` and returns the recomputed
entity count. An independent `EntityBudgetGate` runs after response
validation and before publication; an overrun emits `CSV-NEXT-LIMIT-005`,
records the actual count, produces a manifest-only `payload_unavailable`
outcome, and publishes no artifacts. Boundary vectors cover 500 success, 501
unavailable, 501 under a 600 override, and a compositional 100001-record
model-cap failure.

## Diagnostics, config, and status cross-checks

Compact semantic diagnostics are catalog projections keyed by code. Their
severity, recoverability, outcome, count, and path/symbol permission must
match `schemas/next-diagnostic-catalog-v1.json`; the fixed public message and
domain are supplied by the public diagnostic projection. Complete snapshots
may contain only `complete` diagnostics, while partial snapshots may contain
only `partial_safe` diagnostics. Unknown codes, severity/ref/status mutations,
and the historical FLOW fixture's wrong path reference are rejected.

Explicit targets use only the public canonical key
`path:<repository-relative-file-or-directory>` (NFC, 1--4096 characters).
Internal Module/Component IDs are not public target syntax. A file resolves
its frozen file/Module/Component set only when the direct file is a program
file; a directory resolves its complete canonical descendant frozen set, and
multiple descendants are normal. A direct context/control file is not a
semantic target and fails even when frozen. Missing,
project-scope ambiguity, out-of-scope, or any selected tainted/excluded/failed
record is `CSV-NEXT-TARGET-001`, `payload_unavailable`, and no artifact.
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
