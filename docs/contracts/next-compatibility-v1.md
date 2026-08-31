# Next semantic compatibility descriptor v1

`code-structure-viz.next-semantic-compatibility/v1` is a closed descriptor,
not a caller-supplied label. It contains the public semantic schema ID, the
six identity versions, the recognition/export/props/relation/fact/boundary
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
