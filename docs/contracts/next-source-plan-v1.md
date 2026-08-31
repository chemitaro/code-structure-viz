# Next SourceAcquisitionPlan v1

Round 11 review state: `review_status: fail` (P0=0, P1=8, P2=0) at exact SHA
`75ac0e0b34347b825c0bec2e6fbf9ff2068d9a1b`. The closed descriptor and digest vectors below are
local data-only remediation; a fresh
exact-SHA Strict review is pending, readiness is unconfirmed, and the
production adapter/CLI has not been started; Pass A/B path/order, export, stderr, and
bounded-decoder remediations and Pass C surface-order/path/target remediations plus Pass D
export/stderr/raw-response remediations are locally reflected. Fresh Strict remains pending.

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

The source plan is resolved after the SourceView freeze and before the adapter
starts. It does not re-read control files during analysis. A digest mismatch
is a payload-unavailable protocol failure; no semantic or PlantUML artifact is
published. Known-answer mutations cover local extends, control-path identity,
file-role assignment, and project order.
