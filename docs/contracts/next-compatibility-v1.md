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
