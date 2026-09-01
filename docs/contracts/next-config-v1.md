# Next configuration and request projection v1

Round 12 review state: `review_status: fail` (P0=0, P1=8, P2=0) at exact SHA
`48266f813353a7fd78e4e15d72ff6d33c4142827` (CI `33435802167`, 7/7 success).
The Round 12 data-only contract adds one exact request-owned run context,
bounded raw-response validation, shared `#`-rejecting path validation, and
distinct `missing`/`component_only`/`duplicate` target evidence while preserving the
domain-discriminated target projection and surface-specific ordering below. For a selected
program File, `missing` means that the File exists but its Module and any Component referring
to the expected Module identity are absent; `component_only` means that the Module is absent
while such a Component remains; `duplicate` means more than one byte-identical Module row
exists for the same selected File. Only that selected, identical duplicate is narrowly allowed
before typed failure. All three reasons apply to file and directory targets and project through
response, diagnostic, domain, root manifest, unavailable stdout, and exit 3.
Fresh exact-SHA Strict is pending, readiness is unconfirmed, and production
implementation has not started. The Round 12 fail result is not rewritten as a
pass.

Round 13 review state: Strict reviewed SHA `991516bf730f4f2ddb3d15067702dcfae95ec6b1`
with CI run `33446911714` (7/7 success) and returned `review_status: fail`,
P0=0, P1=9, P2=1. The data-only remediation keeps request-owned context and
the immutable validated decision authoritative, propagates the three typed
target reasons, and applies the shared root-or-path schema to every applicable
configuration/request/source-root surface. This does not rewrite the failure:
fresh exact-SHA Strict is pending, readiness is unconfirmed, and production
implementation has not started.

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
  "source_plan": "<object conforming to next-source-plan-v1>",
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

For `command.name=snapshot` and `command.domain=next`, the root
`request.targets` is a domain-discriminated projection: it is the same unique,
canonical, sorted array of `path:<repository-relative-path>` strings as
`next_request.targets`, `next_config.targets`, `config.resolved.next.targets`,
and `domains[0].targets`. The common run-manifest schema still accepts the
legacy object target grammar for Python and SQLAlchemy; it is not a Next target
grammar. Python reference validation performs the exact projection and
ordering comparison because JSON Schema cannot express that join.

Round 10 Pass A fixes the path value boundary: all ordinary Next path values
use the shared `next-path-v1` schema and helper, while `.` is accepted only by
fields that explicitly denote a project/root. The 4096 limit counts UTF-8 path
value bytes and excludes the `path:` selector prefix.

## Digest preimages

All digests use compact canonical JSON: NFC-normalized strings, UTF-8,
lexicographically sorted object keys, no insignificant whitespace, and no
floating-point values.

```text
project.config_digest = SHA-256(canonical-json({
  root, source_roots, config_path, compiler_options
}))

source_plan_digest = SHA-256(canonical-json(SourceAcquisitionPlan/v1))

domain_config_digest = SHA-256(canonical-json(ResolvedNextConfig
  without domain_config_digest))
```

Project descriptors are sorted by their kind-prefixed IDs in semantic records;
input/config/source-plan projections are sorted by NFC UTF-8 root-path bytes.
Targets use NFC UTF-8 order and formats use the fixed order
`semantic-json`, `plantuml`.  Changing project/compiler/source-plan/limits or
trusted-environment inputs changes the corresponding digest and the run
fingerprint.

The closed SourceAcquisitionPlan includes resolved control paths, local
`extends` closure, file-role assignments, projects, suffixes, exclusions,
limits, and trusted digest. Every one of those fields is part of the digest;
the reference vectors mutate each independently. Semantic model arrays still
use record-ID order, so path order and ID order are intentionally distinct
surfaces for multi-project requests.

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
`file:` are not public syntax. A file path resolves its frozen File and the
Module/Component set only when the file has program role and an exact
`.ts/.tsx/.js/.jsx` suffix. A directory path resolves the complete canonical
descendant set; context/control files may remain as File provenance, but they
never contribute semantic Modules or children. Multiple descendants are
expected and are not ambiguous. Every path-bearing request, response, proof,
domain, root-manifest, and raw-graph field calls the same canonical helper.
The value is NFC-normalized, uses UTF-8, is bounded to 1--4096 bytes (the
`path:` prefix is not counted), and rejects empty segments, traversal,
backslashes, control characters, trailing slash, and `#`. JSON Schema
`maxLength` is only an auxiliary character-count guard; it never replaces the
helper. The root sentinel `.` is accepted only by fields that explicitly
declare a project/source root, and is rejected for ordinary file paths.

Missing path, a File→Module `missing`/`component_only`/`duplicate` cardinality failure,
project-scope ambiguity, out-of-scope path, or any selected
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

`NextRunContext/v1` is the one explicit context used after request resolution:
`requested_formats`, `budget_requested`, `budget_resolved`, `budget_source`, and
the actual `stdout_selector` are copied unchanged through the adapter response,
EntityBudgetGate, domain manifest, root run, and stdout result. The selector is
`null` for the canonical run summary, `manifest` for the exact committed
manifest bytes, or a requested `next:<format>` renderer; no projection uses an
implicit format-order fallback or infers provenance. Formats and selector are
also included in the run-fingerprint preimage.

## Round 15 authority and limits

The resolved config and request are copied into the immutable
`NextPublicationContext` held by every `NextRunDecision`; publication code does
not reconstruct them from defaults. `ValidatedResponseDecision` requires a
deep-copied request whose schema/id, run context, targets, and limits exactly
match the gate. A pre-response failure that cannot own a request uses
`NextDecisionContext` with the known run context and null fields for facts that
were not measurable.

The three 16 MiB byte boundaries are distinct even when their v1 values match:
`max_adapter_stdout_capture_bytes` counts child chunks before retain,
`max_adapter_response_bytes` counts complete private response bytes before
decode, and `max_selected_stdout_bytes` counts public artifact bytes before
selected copy. The historical `max_stdout_bytes` name is retained only as the
selected-output compatibility alias. Raw bytes precede aggregate arrays, and
aggregate arrays precede model-record validation. `max_model_records=10,000`
is proven reachable by generated schema-valid exact/+1 envelopes below the
aggregate/raw caps.

Target failure rows are canonical sorted `{target_key, reason}` pairs from the
closed eight-reason enum and are legal only for the Next unavailable target
stdout branch. All other result branches reject them. Source acquisition
consumes one `SourceDiscoveryIntent` and atomically seals plan plus view after
the final drift check; caller-injected final paths/plan/view are not an
authority.

## Round 16 typed request and failure context

`SourceDiscoveryIntent` is intentionally not a resolved config. It contains
only project roots, control candidates, and fixed discovery rules. The sealed
source acquisition derives config, local `extends` closure, final paths, and
effective roles from frozen bytes and inventory in one operation. The returned
seal is copied into the mandatory `NextPublicationContext` of every decision.

The private adapter request is a separate immutable
`ValidatedAdapterRequest`. It is deep-copied and checked for schema, request
ID, file base64/size/digest/canonical bytes, limits, targets, and run context
before it can enter the response boundary. That boundary accepts no untyped
request and never falls back from `max_adapter_response_bytes` to the legacy
`max_stdout_bytes` alias. If config, project, or source discovery fails before
a request exists, the request-independent branch carries only observed values,
explicit nulls, a closed failure stage/code, and `payload_unavailable`/exit 3;
it does not synthesize public project/request/config fields.

The final publication decision seals child capture, private response, public
stderr, and selected summary/manifest/artifact stream-copy results. This keeps
the semantic outcome stable when a selected copy is unavailable. The process launch descriptor is a
separate versioned provenance value covering verified Node realpath, fixed
argv/environment/FDs, and process-group behavior.

The descriptor is not optional: every `NextPublicationContext`, including
request-independent pre-response and not-applicable decisions, carries the
validated process-launch descriptor explicitly and fingerprints it. Likewise,
`PreResponseFailureDecision` and `NotApplicableDecision` carry an explicit
`NextDecisionContext`; their constructors do not rebuild a context from a
fixture, default limits, or a later writer.

After the measurements are sealed, all publication surfaces consume only the
single `PublicationBoundaryDecision`. A projection API cannot combine a
semantic decision with an independently supplied publication outcome,
capture measurement, stderr status, or selected-copy status. Child capture or
public stderr failure produces the typed unavailable/no-artifact branch; a
selected-copy failure preserves the semantic decision and persisted artifact
descriptor while the root publication result reports exit 3.

## Round 17 closed provenance and request authority

The request-independent branch is discriminated by observed stage and
provenance. It contains no invented request, project, config, limits,
toolchain, trusted environment, source plan, or process descriptor; values not
observed before the failure are explicit `null`/`unobserved`. A
`NextDecisionContext` is frozen, keyword-only, and complete for that stage.
All other fields are owned by a single immutable `NextPublicationContext`.

`ValidatedAdapterRequest` is a composed frozen authority, not a `dict`
subclass. Before response validation it rechecks schema, request ID, canonical
request bytes and digest, file base64/size/digest, targets, run context, and
resolved limits. The response boundary accepts this type only, so a mutable
mapping or an independently rebuilt request cannot bypass the trust boundary.

The publication result is a closed union: selector `null` yields the run
summary, `manifest` yields the exact root manifest, `next:semantic-json` or
`next:plantuml` yields the selected artifact, and the typed unavailable branch
contains no partial bytes. All three selected streams use the common
`max_selected_stdout_bytes` boundary; exact bytes are retained, while limit+1
is unavailable. The manifest unavailable branch keeps its `run-manifest.json`
descriptor, and the domain branch keeps its persisted artifact descriptor.
`target_failures` is present only for a Next target-related unavailable result,
with one sorted row per failed target.
Proof-derived unavailable IDs are resolved again against the sealed roots and
taint before this branch is selected; the reason propagates unchanged through
proof, decision, diagnostic, domain, root manifest, stdout, and exit.

Surface ordering is intentional: semantic projects and model records use
canonical ID order, while request/config/source-plan/root project descriptors
use canonical root-path order. Submitted order is validated before sorting.
The existing lexicographic canonical JSON encoder remains the only byte
encoder. Fresh current-SHA Strict is pending, readiness is unconfirmed, and
production implementation is absent.

## Round 18 provenance and closed request-independent context

Every `NextRunDecision` owns one immutable `NextPublicationContext` and one
stage-discriminated `NextDecisionContext` where a request-independent failure
is required. The latter is constructed only from observations available at
that stage: request, limits, source plan, toolchain, trusted environment,
compatibility, process launch, and budget are represented as explicit
observed/unobserved rows. An unobserved budget is `null` with source
`unobserved`; it is never a default resolved value. Omitted/invented rows and
later fixture reconstruction are invalid.

The private `ValidatedAdapterRequest` is composition-based and immutable. It
rechecks request ID, canonical request bytes/digest, file base64/size/digest,
targets, run context, and resolved limits at the response boundary. The
validated response retains the exact canonical raw bytes and SHA-256 as
opaque authority; callers cannot inject another response byte string or
diagnostic JSONL.

The final `PublicationBoundaryDecision` seals exact summary, manifest,
selected artifact candidates, typed-unavailable bytes, diagnostic JSONL, and
capture/stderr/selected-copy measurements. Domain, root manifest, stdout,
stderr, artifact, and exit projections consume only that object and return
sealed bytes; they do not re-render or accept an independent outcome/map.
Selector, target-failure reason, path grammar, safe symbol IDs, and
request-independent fields are all closed schema branches. Path-only order is
NFC UTF-8 byte order; object rows use canonical JSON bytes. Fresh current-SHA
Strict is pending, readiness is unconfirmed, and production implementation is
absent.

## Round 19 configuration discriminator and provenance

The resolved Next config has a required boolean `request_independent`. The
normal branch is `request_independent=false` and must contain non-empty
projects, resolved limits, trusted environment, source plan, and matching
digests. The request-independent branch is `request_independent=true`, must
contain `failure_stage` and `failure_code`, and must use empty projects,
null limits, null trusted environment, null source plan/digest, and null
depths. These branches are a disjoint JSON-Schema `oneOf`; omission or mixing
normal values into the independent branch is invalid.

`schemas/next-provenance-v1.schema.json` gives the failure-stage observation
prefix its own closed union. A config/project failure cannot invent later
limits, source-plan, toolchain, trusted-environment, compatibility, process,
or budget observations. Source-selection/read/integrity branches retain the
limits and source-plan values already observed, while later values remain
`unobserved`/`null`. `NextRunContext` independently checks the budget source
and requested/resolved values and requires a selected Next format to be in
`requested_formats`.

Round 19's executable negative coverage is
`test_round19_next_config_discriminator_is_required_and_disjoint` and
`test_round19_stage_provenance_reference_rejects_stage_code_and_prefix_mutations`.
Fresh current-SHA Strict is pending, readiness is unconfirmed, and production
implementation is absent.
