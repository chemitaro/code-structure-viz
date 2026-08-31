# Issue #8 ChatGPT Use Strict specification review — Round 12

- Evidence source: `/Users/iwasawayuuta/.oracle/sessions/issue-eight-strict-round-twelve/artifacts/transcript.md`
- Evidence source SHA-256: `758795cee71a49c2a3c5e07cd42daa43c6a3fbd248e9c6b7ee3cdc36bfd89185`
- Review target: `chemitaro/code-structure-viz`
- Branch: `iss-00008-generate-nextjs-component-snapshots`
- Expected and observed full SHA: `48266f813353a7fd78e4e15d72ff6d33c4142827`
- GitHub Actions: run `33435802167`, 7/7 jobs `success`
- Verdict: `review_status: fail`
- Counts: `P0=0, P1=8, P2=0`
- Implementation: intentionally not started; fresh Strict review remains required after remediation

## Findings recorded from the authoritative transcript

1. The inverse-order two-project fixture must use one validated model through
   response, domain, root manifest, publication bytes, and fingerprint. Counts,
   budget, coverage, and project correspondence must be independently recomputed
   and mutation-tested at every projection.
2. One canonical run context must represent `null`, `manifest`, semantic JSON,
   and PlantUML stdout states. It must be request-owned and exact-echoed, or
   Python-owned as one authority. No format fallback, provenance inference, or
   duplicate resolved-budget gate argument is permitted.
3. Raw response bytes must pass a bounded decoder, closed response schema, safe
   base validation, and typed target precedence. Wrong schema, extra fields, and
   unsafe compound mutations need the same raw-byte path and deterministic result.
4. The module-level JSX lexer must recognize NFC Unicode IdentifierName segments,
   including paired/nested/member/namespace tags, while ignoring export-like text
   in JSX, properties, regexes, templates, strings, and comments.
5. Re-export lookup is by public exported name only. A declaration key is never a
   fallback lookup key; hidden declaration-key mutations must fail closed.
6. Re-export witnesses need `owner_module_id` and an exact observation join.
   Physical target declarations must propagate through aliases and stars; a
   component resolution always has a non-null component target. Double aliases,
   stars, cycles, and conflicts must reach the response, binding/coverage,
   domain, root, and `CSV-NEXT-EXPORT-001` failure projection.
7. One shared NFC/UTF-8 POSIX path helper and schema contract must reject `#` on
   every path-bearing request, response, proof, raw graph, domain, and root
   surface, including mutations.
8. File-to-Module target failures must distinguish pure `missing` from
   `component_only`, for both file and directory targets, and project through
   response, diagnostic, domain, root, stdout, and exit code 3.

## Adjudication

The transcript is advisory evidence and is reconciled against the local
canonical Requirement/Design/Plan, normative contracts, schemas, fixtures,
reference validator, and tests. The production Next adapter and CLI are
intentionally absent and are not a finding. The implementation-readiness gate
remains blocked until the eight findings are materialized, all local quality
checks pass, and a fresh exact-SHA Strict review reports `P0=0` and `P1=0`.
