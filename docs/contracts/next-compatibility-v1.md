# Next semantic compatibility descriptor v1

Round 12 review state: `review_status: fail` (P0=0, P1=8, P2=0) at exact SHA
`48266f813353a7fd78e4e15d72ff6d33c4142827` (CI `33435802167`, 7/7 success).
Round 12's data-only remediation keeps project and file identity versions in the
compatibility preimage and preserves the same exact-SHA Strict gate. A fresh
exact-SHA Strict review is pending, readiness is unconfirmed, and production
implementation has not started. The historical Round 11 result remains evidence,
not a pass.

Round 13 review state: Strict reviewed SHA `991516bf730f4f2ddb3d15067702dcfae95ec6b1`
with CI run `33446911714` (7/7 success) and returned `review_status: fail`,
P0=0, P1=9, P2=1. The local data-only contract pins the IdentifierName
implementation to the checked-in Unicode 15.0.0 profile, including
`Other_ID_Start`, `Other_ID_Continue`, and U+00B7, and includes that profile
version in compatibility and run-fingerprint preimages. Fresh exact-SHA Strict
is pending, readiness is unconfirmed, and production implementation has not
started; the historical fail remains unchanged.

Round 14 closes the implementation provenance: the profile is a checked-in,
dependency-free interval table in
`tests/contracts/ecmascript_unicode_15_0.py`, with table digest
`c9336daa555ce98e93cbd48e6b91df22f50a221881bd10b3ed79cf9180297969`.
The table is based on Unicode 15.0.0 `ID_Start`/`ID_Continue` plus the
explicit `Other_ID_Start`, `Other_ID_Continue` (including U+00B7), and
join-control sets. Runtime classification must not call the host Python UCD;
the profile version and exact table digest are checked in the trusted
environment, compatibility descriptor, and run-fingerprint preimage. The
TypeScript 5.9.2 scanner remains the pinned semantic consumer; changing the
table requires a new compatibility/profile version and known-answer digest.
Operational resource limits such as `max_model_records` are intentionally
excluded from this semantic compatibility preimage. They are included in the
request/run-fingerprint preimages, so changing the resolved limit changes run
identity while leaving semantic compatibility unchanged.

`code-structure-viz.next-semantic-compatibility/v1` is a closed descriptor,
not a caller-supplied label. It contains the public semantic schema ID, the
eight identity versions (project, file, module, component, member, relation,
fact, and PropsTypeIR), the recognition/export/props/relation/fact/boundary
algorithm versions, and the trusted semantic profile ID.

The compatibility ID is the digest of this exact preimage (the descriptor's
transport `schema` and `compatibility_id` fields are not in the preimage):

```text
SHA-256(canonical-json({
  semantic_schema,
  identity_versions,
  algorithm_versions,
  semantic_profile_id,
}))
```

Canonical JSON uses UTF-8, NFC strings, sorted object keys, no insignificant
whitespace, and integer versions. The known-answer vector in
`tests/contracts/test_next_contracts.py` must remain stable. Changing an
identity or algorithm version changes the ID; changing only a Node or adapter
patch version, source/config digest, or content-only environment digest does
not. Issue #9 may compare snapshots only when this ID is exactly equal.

## Round 15 semantic identity closure

The checked-in Unicode table is the semantic source of truth for
IdentifierName classification. Its exact byte digest is
`c9336daa555ce98e93cbd48e6b91df22f50a221881bd10b3ed79cf9180297969`, and the
algorithm version is `ecma-unicode-15.0`. The table includes Unicode 15.0.0
ID_Start/ID_Continue plus Other_ID_Start, Other_ID_Continue (including
U+00B7), and Join_Control. Context-specific binding/declaration-key checks
share this data while applying reserved-word rules by context. The full
scalar-range classification bitstream has a known-answer SHA-256 test and
does not consult host `unicodedata.category()` or host UCD classification;
shared NFC canonicalization remains an explicit transport rule.

The table version and digest are part of the trusted semantic profile,
compatibility preimage, and run-fingerprint preimage. A table or algorithm
change therefore requires an explicit compatibility version change; changing
only operational limits or a Node/adapter patch does not change the semantic
compatibility ID.

All semantic and publication projections also carry the immutable
`NextPublicationContext` through their `NextRunDecision`. This context binds
the sealed source-view/plan identity, resolved request/config, the complete
compatibility descriptor and identity versions, toolchain, trusted
environment, and run-fingerprint inputs, so an artifact cannot claim
semantic compatibility while silently using a different source, identity, or
trust profile.

## Round 16 provenance and contextual semantics

The compatibility descriptor is owned by the sealed `NextPublicationContext`.
The checked-in Unicode 15.0.0 table digest, identity/algorithm versions, and
trusted semantic profile are part of its preimage; the observed process-launch
descriptor is separately included in the run fingerprint. A writer must not
replace either value with a host-derived or fixture-derived default.

IdentifierName checks are contextual: binding identifiers exclude reserved
words, declaration/export property keys may use them, and explicit anonymous
default declarations use the reserved `@anonymous-default` slot at most once
per module. The same table covers import/export, JSX, re-export, and trusted
reference names. Round 16 keeps this as a data-only contract; fresh Strict is
pending and the historical verdict remains fail.
