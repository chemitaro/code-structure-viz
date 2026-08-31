# Next semantic contract v1

Status: pre-implementation normative contract for Issue #8.

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
- Collections are unique and sorted by UTF-8 ID bytes.

`identity_versions` is `{module:1,component:1,member:1,relation:1,fact:1,props_ir:1}`. `semantic_compatibility_id` is the SHA-256 of the canonical
preimage `{semantic_schema,identity_versions,algorithm_versions,semantic_profile_id}`.
The descriptor carries fixed algorithm
versions for recognition, export, props, relation, fact, and boundary
classification. A known-answer vector and an algorithm-change negative vector
are required; the value is not a self-reported opaque token.

## Members, relations, and facts

- Members are `export_binding`, `import_binding`, or `prop`.
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

## Partial-safe proof

The Node response includes the complete discovered record set, typed taints, failure roots, causal edges, target-resolution witnesses, and exclusions. `collection`, taint kind, exclusion reason, and propagation rule are closed vocabularies. Python applies the normative taint rules, derives the published subset, checks taint closure, that every discovered record is exactly published/excluded/failed once, that every published reference is untainted or a closed frontier, that target witnesses agree with published IDs, and that coverage counts equal the proof decomposition. Counts alone are not evidence. The validator contract is versioned as `code-structure-viz.next-reference-validation/v1` and lives in `tests/contracts/next_reference_validation.py` until production code owns it.

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
the trusted virtual paths.
