# Next runtime manifest v1

Round 10 review state: `review_status: fail` (P0=0, P1=8, P2=0). Runtime and
trusted fixture attestation is synchronized as data-only remediation; fresh
exact-SHA Strict is pending, readiness is unconfirmed, and production
implementation has not started. Pass B's public stderr and bounded response decoder
contracts are locally reflected. Fresh Strict remains pending.

`schemas/next-runtime-manifest-v1.schema.json` is the checked-in compatibility
unit inventory. `members` are sorted by safe wheel-relative path and unique;
`licenses` are sorted by `(ecosystem,name,version,license_id)` and unique.
Member paths are confined to `src/code_structure_viz/_next_runtime/` and may
not contain traversal segments. Each member carries the physical fixture path,
the virtual runtime path, its actual UTF-8 byte size, and its SHA-256 digest;
the manifest has no untracked files. The physical-to-virtual mapping is
closed and is validated against the checked-in fixture bytes, so a path
substitution cannot pass by changing only metadata.

The v1 filesystem set is exact, not a minimum:

| checked-in fixture bytes | virtual path | role |
| --- | --- | --- |
| `tests/fixtures/next_runtime/adapter.js` | `src/code_structure_viz/_next_runtime/adapter.js` | `adapter` |
| `tests/fixtures/next_runtime/manifest.json` | `src/code_structure_viz/_next_runtime/manifest.json` | `manifest` |
| `tests/fixtures/next_runtime/trusted.d.ts` | `src/code_structure_viz/_next_runtime/trusted.d.ts` | `trusted_declaration` |
| `tests/fixtures/next_runtime/typescript-lib.d.ts` | `src/code_structure_viz/_next_runtime/typescript-lib.d.ts` | `typescript_lib` |

The data-only validator requires exactly these four paths and four distinct
roles. Removal, addition, duplicate path, role substitution, unsafe path, or
filesystem-set drift is rejected. The trusted declaration files and certified
symbols are the exact four-file/14-symbol profile described by
`next-semantic-v1`; their per-file SHA-256 and license ID are checked before
the environment digest is accepted.

The v1 license inventory is exactly two rows: npm `typescript@5.9.2` under
Apache-2.0 and the CodeStructureViz trusted-types resource under MIT. Source
URLs are HTTPS, content/lock digests are 64 lowercase hex characters, and the
ordered inventory digest is reused by the trusted environment and this
runtime manifest. A missing, extra, reordered, or changed license row is a
contract failure.

The digest preimages are exact canonical JSON:

```text
build_input_digest  = SHA-256(canonical-json({members, licenses}))
build_output_digest = SHA-256(canonical-json({members}))
manifest_sha256     = SHA-256(canonical-json(manifest without manifest_sha256))
```

`inventory_attestation` repeats the exact sorted `members` array and carries
`SHA-256(canonical-json({members}))`. The manifest digest deliberately excludes
only `manifest_sha256`; it includes the attestation, while the attestation
does not include the manifest digest. This acyclic construction permits an
independent known-answer check for every member's real bytes, size, and hash.

Canonical JSON is UTF-8, NFC-normalized, sorted object keys, compact
separators, and no floating-point values. The data-only vectors in
`tests/contracts/test_next_contracts.py` include known-answer and traversal,
duplicate, and digest-negative cases. The existing Python/SQLAlchemy runtime
inventory remains outside this Next section and is not rewritten by Issue #8.
