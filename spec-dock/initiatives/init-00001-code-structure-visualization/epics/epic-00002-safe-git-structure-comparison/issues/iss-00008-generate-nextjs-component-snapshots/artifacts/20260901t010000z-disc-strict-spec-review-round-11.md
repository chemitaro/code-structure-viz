# Issue #8 ChatGPT Use Strict specification review — Round 11

- Evidence source: `/Users/iwasawayuuta/.oracle/sessions/issue-eight-strict-round-eleven/artifacts/transcript.md`
- Evidence source SHA-256: `e9e053db62948e391071915171450f12f664bb37d66ab3b545da5db4348dca8b`
- Review target: `chemitaro/code-structure-viz`
- Branch: `iss-00008-generate-nextjs-component-snapshots`
- Expected and observed full SHA: `75ac0e0b34347b825c0bec2e6fbf9ff2068d9a1b`
- GitHub Actions: run `33422630936`, 7/7 jobs `success`
- Verdict: `review_status: fail`
- Counts: `P0=0, P1=8, P2=0`
- Implementation: intentionally not started; fresh Strict review is required after remediation

## Accepted findings recorded from the transcript

1. The inverse-order two-project vector must carry complete files, modules, proof, response, domain, root manifest, and run fingerprint. Project correspondence is keyed by immutable ID/root while each surface retains its independent canonical order.
2. A single explicit run context must carry requested formats, budget requested/resolved/source, and the actual stdout selector through response validation, `EntityBudgetGate`, domain/root manifests, stdout, and the fingerprint preimage. No implicit `FORMAT_ORDER` fallback is allowed.
3. The module-level export scanner must close JSX lexical contexts, including self-closing and nested same-name elements, while retaining async declarations, ASI, generic/type spans, false-positive contexts, and exact UTF-8 byte spans.
4. Re-export witnesses must be independently recomputed from raw declarations and edges. Star expansion is zero-or-more with `default` excluded; aliases, cycles, conflicts, observations, bindings, coverage, diagnostics, and failure projections must agree exactly.
5. Public diagnostic stderr must be an exact bounded UTF-8 JSONL stream. Exact-limit output is accepted; limit+1 produces no partial bytes, `CSV-NEXT-LIMIT-003`, payload disposal, process-group termination, and manifest-only projection.
6. A bounded decoder must be the sole raw-response path, counting duplicate keys, nesting, decoded string bytes, per-array items, and aggregate array items before materialization; aggregate 100001 remains rejected even when individual arrays fit.
7. One canonical POSIX path value contract must be used across every path-bearing surface. NFC, UTF-8 byte length, root sentinel rules, and 4095/4096/4097 boundary mutations must be identical; schema `maxLength` is auxiliary only.
8. Every selected program File must map to exactly one semantic Module. Missing, duplicate, or component-only mappings must become typed target failures for both file and directory targets, projecting `CSV-NEXT-TARGET-001`, `payload_unavailable`, zero artifacts, manifest/stdout failure, and exit 3.

## Readiness rule

The transcript is advisory evidence; local canonical Requirement/Design/Plan, schemas, fixtures, reference validators, and tests adjudicate it. Production Next adapter/CLI code remains intentionally absent. Readiness remains blocked until all eight findings are materialized, focused and full quality gates pass, and a fresh exact-SHA Strict review reports P0=0 and P1=0.
