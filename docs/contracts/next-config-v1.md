# Next configuration and request projection v1

Issue #8 uses one canonical configuration value object and one canonical
snapshot request projection.  The same values are copied into the domain
manifest and the root run manifest; a consumer must not reconstruct Next
settings from the legacy root `request`/`config` fields.

## Canonical shapes

`ResolvedNextConfig` is the closed object in
`schemas/next-config-v1.schema.json`:

```json
{
  "schema": "code-structure-viz.domain-config/next/v1",
  "projects": [{"root":".","source_roots":["src"],"config_path":"tsconfig.json","compiler_options":{}}],
  "targets": [],
  "upstream_depth": 1,
  "downstream_depth": 1,
  "formats": ["semantic-json", "plantuml"],
  "limits": "<object conforming to next-limits-v1>",
  "trusted_environment_digest": "<sha256>",
  "source_plan_digest": "<sha256>",
  "domain_config_digest": "<sha256>"
}
```

`NextSnapshotRequest` is the same value projection with
`schema=code-structure-viz.next-snapshot-request/v1` and, on public semantic
and manifest projections, `run_fingerprint`.  The private adapter request is
a separate transport envelope: it adds frozen `files[]` and a request ID but
does not replace this canonical config/request value.

The root run manifest carries `next_config` and `next_request` byte-for-byte.
Its legacy `request` and `config.resolved.next` fields are explicit lossy
projections for the existing root registry: projects are root paths there,
while the complete project/compiler/source-plan information is in the Next
fields.  `domains[0].config` and `domains[0].request` must equal these Next
fields exactly.

## Digest preimages

All digests use compact canonical JSON: NFC-normalized strings, UTF-8,
lexicographically sorted object keys, no insignificant whitespace, and no
floating-point values.

```text
project.config_digest = SHA-256(canonical-json({
  root, source_roots, config_path, compiler_options
}))

source_plan_digest = SHA-256(canonical-json({
  schema: "code-structure-viz.source-acquisition-plan/next/v1",
  version: "1",
  projects,
  program_suffixes: [".js", ".jsx", ".ts", ".tsx"],
  context_suffixes: [".d.ts"],
  control_paths: ["package.json", "tsconfig.json", "jsconfig.json"],
  hard_exclusions: [".git", "node_modules", ".next", "out", "dist", "build", "coverage"],
  limits,
  trusted_type_environment_digest
}))

domain_config_digest = SHA-256(canonical-json(ResolvedNextConfig
  without domain_config_digest))
```

Project descriptors are sorted by their kind-prefixed IDs in semantic records;
the configuration projection is sorted by the same canonical project order.
Targets use NFC UTF-8 order and formats use the fixed order
`semantic-json`, `plantuml`.  Changing project/compiler/source-plan/limits or
trusted-environment inputs changes the corresponding digest and the run
fingerprint.

## Roles and transport boundary

Every frozen file has a unique canonical role tuple in wire order
`control`, `context`, `program`.  The effective role is selected separately
by precedence `control > context > program`; it is never derived from the
last array element.  There are seven valid non-empty role subsets, and each
must carry the matching effective role.  Program suffixes are `.js/.jsx/.ts/.tsx`, declaration
files are context-only, and fixed hard exclusions are applied before the
request is built.

Explicit targets are canonicalized before they enter the request using only
`path:<repository-relative-path>`. This is a public address, distinct from
internal Module/Component IDs and semantic keys; `component:`, `module:`, and
`file:` are not public syntax. A file path resolves its frozen file, Module,
and Component set. A directory path resolves the complete canonical descendant
set, so multiple descendants are expected and are not ambiguous. Paths are
NFC-normalized, bounded to 1--4096 characters, and reject traversal,
backslashes, control characters, and `#`.

Missing path, project-scope ambiguity, out-of-scope path, or any selected
tainted/excluded/failed record makes the whole domain
`CSV-NEXT-TARGET-001`/`payload_unavailable`, publishes no domain artifacts,
and uses the exact manifest/stdout unavailable vector. The response proof has
one canonical resolution row per request target; Python resolves the row's
status and published IDs independently against the frozen model.

The adapter receives exactly `canonical_json(request)` as UTF-8 stdin, with no
BOM and no implicit source path/cwd.  Its byte length is inclusive of the
`max_encoded_stdin_bytes` limit (96 MiB in v1): `limit-1` and `limit` are
accepted, `limit+1` is rejected before process start.  Boundary tests use
arithmetic measurements rather than allocating a 96 MiB fixture.

The data-only reference validator and mutation vectors are the executable
authority for projection equality, digest recomputation, role precedence, and
encoded-byte limits until the production adapter is implemented.
