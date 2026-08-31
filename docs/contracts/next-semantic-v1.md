# Next semantic contract v1

Status: pre-implementation normative contract for Issue #8.

The machine-readable authority is:

- `schemas/next-semantic-v1.schema.json`
- `schemas/next-adapter-request-v1.schema.json`
- `schemas/next-adapter-response-v1.schema.json`
- `schemas/next-trusted-type-environment-v1.schema.json`
- `schemas/next-config-v1.schema.json`
- `schemas/next-domain-manifest-v1.schema.json`

These schemas materialize the field-level branch that will be integrated into the existing public registries during Issue #8 production implementation. They do not make the current CLI accept `--domain next` before that implementation.

## Identity and ordering

- Module identity: project-owned repository-relative physical path.
- Component identity: Module ID plus NFC declaration key.
- Member identity: owner ID plus member-kind identity. Export aliases never create Components.
- Relation and Fact identity: kind-specific canonical tuple.
- IDs use a kind prefix and SHA-256 of canonical JSON identity bytes.
- Collections are unique and sorted by UTF-8 ID bytes.

`identity_versions` is `{module:1,component:1,member:1,relation:1,fact:1,props_ir:1}`. `semantic_compatibility_id` is the SHA-256 defined in Issue #8 Design and changes whenever identity or payload semantics change.

## Members, relations, and facts

- Members are `export_binding`, `import_binding`, or `prop`.
- Module relations are `static_import` and `literal_dynamic_import`.
- Component relations are `jsx_render` and internal-only `component_wrap`.
- Direct `client_entry` and `router_context` are Facts. Derived boundary roles remain Module facets.
- External render targets use a redacted package/export descriptor; no target source or absolute path is allowed.

## Partial-safe proof

The Node response includes the complete discovered record set, typed taints, failure roots, causal edges, target-resolution witnesses, and exclusions. Python applies the normative taint rules, derives the published subset, checks all references and count reconciliation, and requires exact equality with the adapter-proposed model. Counts alone are not evidence.

## Compatibility

The public snapshot and manifest publish `semantic_compatibility_id` and identity versions. Issue #9 may compare sides only when the compatibility ID is exact-equal. Config, source-plan, Node patch, and adapter patch differences remain provenance rather than semantic compatibility when the ID stays equal.
