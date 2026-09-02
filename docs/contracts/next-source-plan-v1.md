# Next SourceAcquisitionPlan v1

Round 12 review state: `review_status: fail` (P0=0, P1=8, P2=0) at exact SHA
`48266f813353a7fd78e4e15d72ff6d33c4142827` (CI `33435802167`, 7/7 success).
The closed descriptor and digest vectors below are local data-only remediation;
the inverse-order model chain, request-owned run context, bounded raw-response
path, shared path helper, and typed target outcomes are also reflected. Fresh
exact-SHA Strict review is pending, readiness is unconfirmed, and the production
adapter/CLI has not been started. The Round 12 fail result is not a pass.

Round 13 review state: Strict reviewed SHA `991516bf730f4f2ddb3d15067702dcfae95ec6b1`
with CI run `33446911714` (7/7 success) and returned `review_status: fail`,
P0=0, P1=9, P2=1. The data-only contract now uses the shared root-or-path
schema on every source-root surface, accepting `.` only as the explicit root
sentinel and keeping unsafe non-root forms rejected. This is a local
remediation record, not a pass: fresh exact-SHA Strict is pending, readiness is
unconfirmed, and the production adapter/CLI has not started.

`schemas/next-source-plan-v1.schema.json` defines the complete
`code-structure-viz.source-acquisition-plan/next/v1` descriptor. It is carried
inside the canonical Next config and snapshot request and is hashed as a
whole; `source_plan_digest` is never computed from a hand-picked subset.

The descriptor contains these resolved values:

- project roots, source roots, compiler options, and config paths;
- every resolved control path and the local `extends` closure;
- the repository-relative file-role map (`control`, `context`, `program`) and
  its effective-role result;
- exact program/context suffix sets and hard exclusions;
- the complete resolved limits object; and
- the trusted type-environment digest.

All strings are NFC-normalized UTF-8. Projects in the input, config, and
source-plan surfaces are sorted by canonical root-path bytes. The file-role,
control-path, and extends collections are sorted by canonical JSON bytes;
semantic record collections remain sorted by kind-prefixed record ID. The
descriptor is therefore invariant under CLI/project permutation while a real
change to a path, role, extends edge, suffix, exclusion, limit, or trusted
digest changes the SHA-256 answer. The reference validator also rejects
duplicate, out-of-scope, non-canonical, or role-precedence-inconsistent rows.

```text
source_plan_digest = SHA-256(canonical-json(SourceAcquisitionPlan/v1))
```

Acquisition is a two-phase, single-read protocol. `SourceDiscoveryIntent`
records the selected project roots and descriptor-safe control candidates.
Phase 1 reads each candidate control/config/`extends` path once and retains
its bytes; the resolver computes the local extends closure and role intent from
those retained bytes. Phase 2 reads each final program/context path once and
performs the final inventory/drift check. Only after that check does the
implementation atomically seal `FinalSourceAcquisitionPlan` and `SourceView`
with one seal operation and their digests. The adapter receives that sealed
pair and no filesystem path; no filesystem read is permitted after the seal.
An already-read path is never read again when it appears in both phases.

A phase or inventory drift, descriptor/path mismatch, duplicate read, or
post-seal read is a fatal source-integrity failure. A digest mismatch is a
payload-unavailable protocol failure; no semantic or PlantUML artifact is
published. Known-answer mutations cover local extends, control-path identity,
file-role assignment, project order, single-read counts, drift rejection, and
the atomic plan/view seal.

## Round 15 single-seal authority

The only supported acquisition entry point is
`seal_source_acquisition(intent, reader, inventory)`. It accepts a
`SourceDiscoveryIntent`, not a caller-supplied final plan or a caller-supplied
SourceView. The function reads the union of discovery and final paths once,
checks the before/after inventory revision, derives the final role map and
local-extends closure from the frozen bytes/config, computes both descriptors,
and invokes exactly one seal operation. The returned
`SourceAcquisitionSeal` is the sole owner of `final_plan`, `source_view`, both
digests, and `seal_id`.

The negative contract is executable: a final-plan keyword is rejected, a
plan-only or view-only reconstruction is rejected, duplicate paths within a
phase are rejected, post-drift revisions are rejected, and inventory
file-digest/size, role/effective-role, control-path, or extends-closure
mismatches are rejected. Once sealed, an instrumented reader fails every
subsequent filesystem read. Cross-phase overlap is allowed only because the
path is read once and shared by both phases. Domain and publication contexts
carry the resulting descriptors/fingerprints; downstream writers never reopen
the repository.

## Round 16 intent and single authority

`SourceDiscoveryIntent` is deliberately smaller than the final plan. It may
contain only explicit project roots, control candidates, and fixed discovery
rules. It cannot contain caller-chosen resolved config, local-extends closure,
final file paths, or a role map. `seal_source_acquisition(intent, reader,
inventory)` derives those values from frozen control bytes and the inventory,
then seals the resulting `SourceView` and `FinalSourceAcquisitionPlan` in one
operation. A caller-injected plan/view, plan-only or view-only reconstruction,
role/effective-role substitution, control/extends closure substitution,
digest/size mutation, duplicate read, or post-drift read is rejected.

The seal is the input to `NextPublicationContext`; all decision variants carry
the same sealed source descriptor, plan digest, and seal identity. If source
selection or discovery fails before a validated adapter request exists, the
request-independent decision keeps only the source facts and known/null
measurements that were actually observed. It must not invent a project,
request, config, or source plan from a default fixture. This is a
pre-implementation contract; fresh current-SHA Strict is pending and product
implementation is absent.

## Round 17 observation-only inventory

Round 17 closes the acquisition trust boundary further. `SourceDiscoveryIntent`
is limited to project roots, control candidates, and fixed discovery rules.
`inventory` may report observations (revision/head, bytes actually read,
observed file digests/sizes, and independently observed environment/limit
attestations), but it may not supply project descriptors, compiler options,
source roots, config or `extends` closure, final paths, role maps, plan digests,
or source-view fingerprints. `seal_source_acquisition` derives those values
from the frozen control bytes and the observed inventory, then seals the plan
and view together. A request-owned copy of a derived value is checked against
that seal and cannot override it.

An early failure uses explicit provenance: a request-independent context keeps
only measurements made before the failure and uses `null`/`unobserved` for
limits, toolchain, trusted environment, process launch, compatibility, or
source-plan fields that were not yet observable. No fixture, default project,
or synthetic plan is allowed. The same sealed source graph also derives the
immutable `SourceFailureLedger`; locality, safe-subset proof, and target taint
are graph consequences, never caller booleans.

The normative acquisition sequence is therefore:

```text
SourceDiscoveryIntent
  -> frozen control observations
  -> derived config/extends/paths/roles
  -> final source read and drift check
  -> one atomic SourceAcquisitionSeal(plan + SourceView)
```

The reference tests reject injected inventory fields, plan-only/view-only
reconstruction, role or closure substitution, duplicate reads, post-drift
reads, and request-derived mutations. This remains a data-only
pre-implementation contract; fresh current-SHA Strict is pending and product
implementation is absent.

## Round 18 sealed source and locality authority

`SourceDiscoveryIntent` remains limited to project roots, control candidates,
and fixed discovery rules. `SourceAcquisitionSeal` owns the trusted enumerated
paths: the enumerator reads the frozen control closure and final source bytes,
checks the snapshot/revision before and after the read, derives config,
extends, final paths, effective roles, and plan/view digests internally, and
performs one atomic seal. Caller-provided `observed_paths`, final paths,
derived descriptors, or a second plan/view seal are not authority.

Source failure locality is likewise seal-owned. The immutable
`SourceFailureLedger` stores raw graph nodes/edges, failure roots, project
roots, targets, and proof roots. Reachability, closure completeness, safe
subset, and target taint are recomputed from those facts and bound to the
source seal ID/digest; boolean-equivalent caller claims are rejected. A
localized proven subset uses `CSV-NEXT-SOURCE-001`/`partial_safe`, while a
non-isolatable failure uses `CSV-NEXT-SOURCE-003`/`payload_unavailable`.

If acquisition fails before a request exists, the decision carries only
observed facts. Its stage-discriminated provenance marks each later fact as
`{state: "unobserved", value: null}`; no fixture/default supplies a project,
request, limits, toolchain, trusted environment, process descriptor, or source
plan. The reference tests cover malformed controls, revision drift, duplicate
reads, caller-derived mutations, ledger substitution, and the local/global
failure split. This is a data-only contract: fresh current-SHA Strict is
pending, readiness is unconfirmed, and production implementation is absent.

## Round 19 trusted enumeration and source-result union

Round 19 closes the remaining request-to-seal ambiguity. The only source
authority is a seal created before the private adapter request. A request is
checked against that already sealed identity and captured file set; no
request-derived helper may construct a replacement `SourceAcquisitionSeal`.
The reference fixture registry is only a lookup for an observation that was
created before the request and is not a production source of paths or bytes.

The trusted enumerator follows this order:

1. Accept `SourceDiscoveryIntent` containing only project roots, known
   project-root control candidates, and fixed discovery rules.
2. Observe each candidate from the frozen snapshot once. Decode the limited
   JSONC dialect (UTF-8 BOM, comments, and trailing commas outside strings),
   reject duplicate keys and non-object/type-invalid values, and resolve one
   local `extends` string. Arrays, package-based extends, unknown nested
   configuration, path escapes, and malformed controls fail closed.
3. Derive include/exclude/files, source roots, effective roles, control
   closure, and final membership from those frozen control bytes. Suffixes do
   not select a role by themselves, and string values are never coerced to
   booleans.
4. Read the final control/program/context membership once, perform the
   revision and digest/size checks, then atomically seal
   `FinalSourceAcquisitionPlan` and `SourceView` together. The request file set
   must equal the seal's captured set exactly.

The result is a closed union:

| result | evidence and next action |
| --- | --- |
| `CompleteSourceSeal` | all planned reads and checks succeeded; create the normal request |
| `PartialSourceSeal` | one or more program/context reads failed, and the seal-owned graph proves an isolated safe subset; create a filtered request with the same seal and ledger identity |
| `SourceAcquisitionUnavailable` | control or non-isolatable source failure; manifest-only `CSV-NEXT-SOURCE-003`/`payload_unavailable` |
| `SourceIntegrityFatal` | revision drift, seal/digest inconsistency, duplicate read, or post-seal read; fail closed without a publication |

`SourceFailureLedger.from_seal(seal, failures, targets, proof_roots)` is the
only ledger constructor. It recomputes reachability, safe subset, and target
taint from the seal-owned raw graph; caller booleans, graph replacement,
`seal_id`, and digest claims are not accepted. The ledger digest includes the
source-seal digest. `CSV-NEXT-SOURCE-001` is emitted only for the proven
localized partial branch; `CSV-NEXT-SOURCE-003` covers the unavailable and
integrity-safe failure branches. Reference evidence includes
`test_round19_partial_source_result_preserves_safe_subset_and_ledger_identity`
and `test_round19_source_acquisition_union_is_typed_and_fail_closed`.

Round 19 remains a data-only contract. Fresh current-SHA Strict is pending,
readiness is unconfirmed, and the production adapter/CLI is absent.

## Round 20 trusted applicability and derivation

`PackageApplicabilityMatrix` is a separate, seal-owned observation used before
Node optionality is decided. For every project root, parse its frozen
`package.json` exactly once. Only a non-empty direct
`dependencies.next`/`devDependencies.next` string is `applicable`; a missing
package or no direct Next is `non_applicable`; duplicate keys, invalid encoding
or JSON, malformed dependency tables, and invalid `next` values are
`malformed`. The matrix is sorted by root path and has a deterministic aggregate
state. It is invalid to infer applicability from lockfiles, transitive packages,
directory names, or arbitrary config. An all-`non_applicable` matrix terminates
as `NotApplicableDecision` without starting Node, while any malformed root is a
typed unavailable acquisition result.

The trusted enumerator reads only known controls at project roots before it can
derive membership. It parses the closed JSONC dialect (BOM, comments, and
trailing commas outside strings), rejects duplicate keys and invalid value types,
and permits only one local string `extends`. `..` escapes, package/array
extends, `plugins`, `typeRoots`, `types`, invalid module/moduleResolution, and
unsupported compiler options fail closed. Include/exclude patterns use the
segment grammar `*`, `?`, and whole-segment `**`; `fnmatch` semantics are not
part of this contract. A control read or parse failure is never represented by
an empty config or empty membership.

After control closure and final membership have been derived, the source graph
is recomputed from the frozen bytes, resolved relative imports/extends, and
project ownership. The reader's optional graph observation is intentionally not
authority. The source result is one of
`CompleteSourceSeal`, `PartialSourceSeal`, `SourceAcquisitionUnavailable`, or
`SourceIntegrityFatal`; the corresponding `SourceAcquisitionDecisionProjection`
fixes stage, diagnostic code, payload/manifest availability, stdout reason, and
exit. The reference mutation test proves that an injected graph or an
edge-deletion-plus-digest-recompute cannot change the sealed graph.

Round 20 evidence is
`test_round20_package_applicability_matrix_is_direct_dependency_only`,
`test_round20_package_applicability_matrix_rejects_encoding_duplicates_and_mixed_state`,
`test_round20_explicit_config_candidates_cannot_hide_package_applicability`,
`test_round20_source_control_uses_segment_grammar_and_fail_closed_control_reads`,
`test_round20_source_graph_is_derived_from_frozen_bytes_not_reader_injection`, and
`test_round20_source_integrity_has_one_fatal_vs_payload_unavailable_projection`.
Fresh current-SHA Strict is pending, readiness is unconfirmed, and production
implementation is absent.
