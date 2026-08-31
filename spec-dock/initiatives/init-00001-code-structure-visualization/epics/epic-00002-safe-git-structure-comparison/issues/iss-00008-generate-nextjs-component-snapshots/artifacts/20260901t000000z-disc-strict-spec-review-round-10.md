# Issue #8 ChatGPT Use Strict specification review — Round 10

- Evidence source: `/Users/iwasawayuuta/.oracle/sessions/issue-eight-strict-round-ten/artifacts/transcript.md`
- Evidence source SHA-256: `7c1f3717659fbbf0ef8ed9e3b0fa54e67bf19c6cf58c5d8e13bd81d01b79fd6e`
- Review target: `chemitaro/code-structure-viz`
- Branch: `iss-00008-generate-nextjs-component-snapshots`
- Expected and observed full SHA: `1a7d13d365683d4e53672e467eed61aa521c8692`
- GitHub Actions: run `33414064038`, 7/7 jobs `success`
- Verdict: `review_status: fail`
- Counts: P0=0, P1=8, P2=0
- Implementation: intentionally not started; fresh Strict review is required after remediation

## Accepted findings recorded from the transcript

1. Project correspondence is keyed by immutable project ID/root. Input, config, source-plan, and root-manifest surfaces use NFC UTF-8 root-path order; semantic collections and fingerprints use record-ID order. The inverse-order two-project vector must pass through request, response, domain, root manifest, and fingerprint.
2. `EntityBudgetGate` derives a pre-budget `complete` or `partial_safe` outcome from validated proof. It has no implicit `complete` default, preserves that outcome under budget, maps either outcome to `payload_unavailable` only on overrun, and publishes only requested formats.
3. The Python frozen-byte export census recognizes the closed module-level lexical grammar, including async declarations, ASI policy, JSX/property/regular-expression/template/string/comment false positives, generic/type spans, Unicode NFC, BOM/CRLF, and exact byte spans.
4. Re-export witness resolution is independently recomputed from raw declarations and source edges. Alias, star expansion (zero or more names, excluding `default`), cycle, conflict, and mutation cases are integrated with observations, bindings, coverage, and diagnostics.
5. Public diagnostic stderr is encoded as UTF-8 JSONL with LF bytes and bounded across all lines. At the exact limit it is accepted; at limit+1 it emits no partial bytes, disposes the payload, terminates the process group, returns `CSV-NEXT-LIMIT-003`, and projects the stable diagnostic to the manifest.
6. A bounded response decoder counts object nesting, duplicate keys, string bytes, per-array items, and aggregate array items before materialization. An aggregate of 100001 is rejected even when every individual array is within its own bound.
7. One canonical POSIX path value contract rejects empty segments, embedded `.`/`..`, trailing slash, control characters, backslash, and non-NFC collisions. The root sentinel `.` is allowed only where the containing surface declares a root, and 4096 is the UTF-8 path-value byte limit.
8. Every selected program File maps to exactly one semantic Module. A missing/duplicate/component-only mapping makes file and directory targets fail closed with `CSV-NEXT-TARGET-001`, `payload_unavailable`, no artifacts, and the corresponding manifest/stdout projection.

## Readiness rule

The transcript is advisory evidence; local canonical Requirement/Design/Plan, schemas, fixtures, reference validators, and tests adjudicate it. Production Next adapter/CLI code remains intentionally absent. Readiness remains blocked until all eight findings are materialized, focused and full quality gates pass, and a fresh exact-SHA Strict review reports P0=0 and P1=0.
