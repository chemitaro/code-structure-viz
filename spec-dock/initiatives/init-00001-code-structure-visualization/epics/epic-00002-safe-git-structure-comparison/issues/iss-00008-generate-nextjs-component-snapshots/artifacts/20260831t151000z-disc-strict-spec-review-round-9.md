# ChatGPT Use Strict specification review — Round 9

- Collected: 2026-08-31T15:10:00Z
- Session: `issue-eight-strict-round-nine`
- Model: GPT-5.6 Sol
- Browser thinking time: Pro
- Review target: `chemitaro/code-structure-viz`
- Branch: `iss-00008-generate-nextjs-component-snapshots`
- Expected and observed full SHA: `ccc5fe222b906ac2b8e54c931566125f7381ae24`
- GitHub Actions: run `33403892456`, 7/7 jobs `success`
- Verdict: `review_status: fail`
- Counts: P0=0, P1=7, P2=1
- Implementation readiness: blocked pending contract remediation and a fresh exact-SHA Strict pass

## Binding and recovery evidence

The Strict wrapper verified a clean local branch and exact local/upstream SHA equality before submission. ChatGPT then used the GitHub connector and reported exact repository, branch, and full-SHA equality. The verified GitHub commit was treated as authority over the attachment bundle.

The first foreground harvest stayed at `response streaming` without UI progress for 20 minutes. Browser recovery diagnostics proved `promptSubmitted=true`, GPT-5.6 Sol model selection verified, a stable conversation ID and URL, and no duplicate submission. The foreground wait was cancelled without sending a second prompt. `oracle session issue-eight-strict-round-nine` reattached to the same conversation, restored three prior turns, captured the terminal assistant response, validated the transcript, and marked the original session completed. The durable Oracle transcript SHA-256 begins `7b2f8b6a36ce`.

## Findings accepted for remediation

### P1-1 — Export syntax census is not closed over the normative grammar

The Python-owned scanner currently recognizes only a narrow line-oriented ASCII subset. It does not close the documented surface for local export lists, aliased default exports, default declarations or expressions, multiple or multiline specifiers, comments, Unicode IdentifierName, CRLF, and BOM. Node and Python could therefore omit the same valid export and still exact-match.

Closure decision: define and materialize a closed frozen-token grammar for every accepted export syntax, with exact UTF-8 byte spans and positive, omission, and mutation vectors. Do not broaden production behavior beyond the documented Issue #8 grammar.

### P1-2 — Remote re-export, alias, and star resolution lack an independent witness

`ExportObservation` lacks the source specifier and imported/original declaration identity needed to prove remote bindings. Star observations are forced to `unknown`, and the existing resolution witness is derived from public bindings rather than an independent frozen module graph. Barrel aliases, star expansion, cycles, and conflicts remain underdetermined.

Closure decision: add a closed source-edge/declaration witness that binds syntax identity to source specifier, imported/original name, resolved source Module, exported name, and target declaration. Python must recompute alias/star/cycle/conflict behavior from the frozen graph and exact-compare Node observations, public bindings, and coverage counts.

### P1-3 — EntityBudgetGate can upgrade `partial_safe` to `complete`

The current gate returns `complete` for every under-budget model, ignoring an independently derived pre-budget `partial_safe` result. This could turn semantic loss into exit 0.

Closure decision: make the budget decision outcome-preserving. Under budget retains `complete` or `partial_safe`; over budget maps either to manifest-only `payload_unavailable`; an override that passes also retains the original outcome. Add response-to-domain-to-manifest/stdout vectors for all compositions.

### P1-4 — stderr capture and public diagnostic limits are conflated

Design describes a 64 KiB child adapter stderr capture cap with process termination, while the executable limit table describes a diagnostic encode-before-write cap. These are different trust boundaries.

Closure decision: separate `max_adapter_stderr_capture_bytes` from any public diagnostic output bound. Freeze incremental byte counting at limit and limit+1, process-group termination, raw/partial byte disposal, stable diagnostic, and manifest projection.

### P1-5 — JSON array aggregate and per-collection limits are conflated

R/D describe 100,000 total array items and 20,000 per collection, while the executable contract treats the former as a per-array bound. Decoder memory and `CSV-NEXT-LIMIT-003` are therefore ambiguous.

Closure decision: define distinct aggregate and collection counters. Add a nested response whose individual arrays are within bounds but aggregate items reach 100,001, and define the pre-materialization counting algorithm.

### P1-6 — `source_plan_digest` preimage is incomplete

Design claims a digest over the resolved `SourceAcquisitionPlan`, including resolved control paths and file roles. The executable preimage fixes only the three root control paths and omits local `extends` closure and role assignments.

Closure decision: add a closed `SourceAcquisitionPlan/v1` descriptor and schema. Hash every resolved field, including canonical control paths, file-role map, projects, suffixes, exclusions, limits, and trusted environment digest. Add known-answer mutations for local extends, control-path identity, and role changes.

### P1-7 — Multi-project order differs between root paths and hashed Project IDs

Design sorts project roots by NFC UTF-8 path bytes; executable projections require Project ID order. Hashed IDs do not preserve path order, so request bytes and digests can diverge.

Closure decision: make ordering surface-specific and explicit: input/config/source-plan projections use canonical root-path order, while semantic record collections use canonical record-ID order. Add two roots whose path and ID orders are reversed, CLI permutation, and digest equality vectors.

### P2-1 — Stale `component target` prose remains

`SelectionAndTraversal/v1` still says `component target` although the public target grammar is path-only.

Closure decision: replace it with an internal Component seed resolved from a path target, and remove any remaining public path/component selector wording.

## Confirmed closed from Round 8

- Snapshot + Next root manifests discriminate `path:` string targets while Python/SQLAlchemy retain legacy object targets.
- Public semantic owners are program-role `.ts/.tsx/.js/.jsx` Files only; direct `.d.ts` and control-file targets fail.
- Structural validation applies `max_model_records` before the entity publication gate, and an entity overrun is manifest-only `payload_unavailable`.
- Export census ownership moved to Python-frozen source bytes, but grammar completeness and remote resolution independence still require P1-1/P1-2 closure.

## Readiness rule

This review is not Issue implementation completion. Product Next adapter/CLI code remains intentionally unimplemented. Readiness requires all accepted findings to be reflected in canonical R/D/P, human HTML, normative docs, schemas, frozen fixtures, reference validators, and contract tests; local and exact-SHA GitHub CI must pass; and a fresh independent Strict review must return P0=0 and P1=0.
