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
