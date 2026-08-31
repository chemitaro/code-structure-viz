# Next runtime manifest v1

`schemas/next-runtime-manifest-v1.schema.json` is the checked-in compatibility
unit inventory. `members` are sorted by safe wheel-relative path and unique;
`licenses` are sorted by `(ecosystem,name,version,license_id)` and unique.
Member paths are confined to `src/code_structure_viz/_next_runtime/` and may
not contain traversal segments. Each member and license carries a SHA-256
digest, while the manifest has no untracked files.

The digest preimages are exact canonical JSON:

```text
build_input_digest  = SHA-256(canonical-json({members, licenses}))
build_output_digest = SHA-256(canonical-json({members}))
```

Canonical JSON is UTF-8, NFC-normalized, sorted object keys, compact
separators, and no floating-point values. The data-only vectors in
`tests/contracts/test_next_contracts.py` include known-answer and traversal,
duplicate, and digest-negative cases. The existing Python/SQLAlchemy runtime
inventory remains outside this Next section and is not rewritten by Issue #8.
