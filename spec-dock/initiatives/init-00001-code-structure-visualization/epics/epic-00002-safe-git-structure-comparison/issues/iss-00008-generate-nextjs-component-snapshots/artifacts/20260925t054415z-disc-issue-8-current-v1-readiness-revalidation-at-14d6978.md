---
種別: disc
ID: "20260925t054415z-disc"
タイトル: "Issue #8 Current-v1 Readiness Revalidation at 14d6978"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-09-25"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: []
reflected_to: []
---

# 20260925t054415z-disc Issue #8 Current-v1 Readiness Revalidation at 14d6978

複数の証拠を統合し、選択肢と trade-off を整理します。一つの source の調査は `research` を使います。

## Inputs

- 統合する evidence:
  - Repository `chemitaro/code-structure-viz`, branch `iss-00008-generate-nextjs-component-snapshots`, exact current candidate `14d69788678b6ddd85b6fd0c1d37eca3fa1a29e2`.
  - Local Git: clean worktree; `HEAD` and configured upstream equal the candidate SHA.
  - ChatGPT Use Strict session `required-strict-github-connector-verificati-1201`; connector verified the exact repository, branch, and SHA. Requested model `gpt-6-pro`; picker target/resolved label `Latest`, verified; reasoning `Pro`, verified. Transcript: `/Users/iwasawayuuta/.oracle/sessions/required-strict-github-connector-verificati-1201/artifacts/transcript.md`.
  - Exact-SHA CI run `36095842229`: completed success, 7/7 jobs.
  - Bounded package-prefix Code Review Strict session `required-strict-github-connector-verificati-1200`: valid `review_status=pass`, `findings=[]`, confidence 0.90. It covers only the package-prefix remediation, not all of I05-PLAN-008.
  - Current canonical Issue #8 Requirement/Design/Plan and linked adapter-identity Artifact `20260924t002133z-disc-issue8-strict-dependency-adapter-identity.md`.
  - SpecDock observations: active scope ends at `iss-00008`; `deps check --id iss-00008 --github --json` reports Issue #8 open and ready, Issue #4 done, no dependency blockers.
  - Same-candidate local commands run during this continuation: focused contract/source suite, full pytest, Ruff check/format check, mypy, SpecDock validate, `git diff --check`, and pinned HTML/PlantUML browser validation.

## Synthesis

- 一致する事実と未確定事項:
  - **外部依存のインストール不足が現在の停止原因ではない。** SpecDock issue dependency is ready. The historical technical defects concern internal current-v1 evidence flow: reader-owned phase/failure classification, provenance and run-schema union alignment, publication-chain coverage, and registry traceability.
  - Some bounded repairs are present at the current candidate. In particular, `next-run-decision-v1` permits the constrained pre-seal observation union, and the latest package-prefix guard requires the corresponding early read prefix and binds it to the decision. Prior findings are historical evidence and must not be represented as still reproducible without current-SHA proof.
  - Full readiness is nevertheless **not proven**: successful tests/CI and the package-only Strict pass do not replace a fresh, full-scope I05-PLAN-008 review and finding closure on one candidate.
  - The current normative Plan says I05-PLAN-008 requires an independent GPT-6 Max review. The user explicitly prohibits subagent reviews and authorizes ChatGPT Code Review Strict with GPT-6 Pro. The review route is settled by user instruction, but the Plan still needs canonical reconciliation. Preserve fixed-SHA binding, complete current-v1 scope, quality gates, finding traceability, and `P0=0 / P1=0 / review_status=pass`.
  - The adapter resource/version/hash owner is a separate, unaccepted design decision. No production `runner.py` or `_next_runtime/` exists. This blocks the production resolver unit, not the current reference-contract verification.
  - Strict picker evidence records requested `gpt-6-pro` but resolved label `Latest`; do not claim more exact backend identity than the transcript establishes.

### Same-candidate local verification

| Check | Result |
| --- | --- |
| `uv run --locked pytest -q tests/contracts/test_json_schemas.py tests/contracts/test_next_contracts.py tests/unit/next/test_source_acquisition.py` | `838 passed in 105.22s` |
| `uv run --locked pytest -q` | `1866 passed, 1 skipped in 250.98s` |
| `uv run --locked ruff check .` | pass |
| `uv run --locked ruff format --check .` | pass; 174 files formatted |
| `uv run --locked mypy src tests` | pass; 150 source files |
| `./spec-dock/scripts/spec-dock validate` | pass; `nodes=10` |
| `git diff --check` | pass |
| `validate-plantuml-html.mjs` on Issue #8 best-practice HTML | static 8/8; browser 8/8 inline SVG; zoom, keyboard, bounds, focus trap, dismissal, and focus restoration pass |

The Strict analyst itself ran no tests. The table above records separate local executions against the clean candidate. This Artifact does not mark I05-PLAN-008 or Issue #8 complete.

## Options and trade-offs

- 選択肢と利点・制約:
  - **Review-route reconciliation — recommended and already authorized by the user:** update the normative Plan and current closure record to use one fresh ChatGPT Code Review Strict invocation requested as GPT-6 Pro, with no subagent review. Preserve the existing acceptance threshold and exact-SHA requirements. Historical GPT-6 Max observations remain unchanged as historical evidence. Until the normative text is reconciled and a valid full-scope review passes, I05-PLAN-008 stays open.
  - **Full-gate fixed point — requires explicit user selection before invocation.** Existing local work records identify `f4159066f3954454ad2f0c2701fa54bf1bc7bc4a` as the cumulative I05-PLAN-008 base (17 commits through current HEAD); `977feb02c05b908d5a25a97181138abe1ef54bd9` was used for the narrower package-only review (12 commits through current HEAD). Both resolve as ancestors. The Code Review Strict skill requires a user-supplied fixed point; do not silently choose either. Recommendation: confirm `f415906...` for the full current-v1 gate.
  - **Adapter identity — requires explicit adoption or replacement values before production resolver work.** Recommended complete candidate: `importlib.resources.files("code_structure_viz").joinpath("_next_runtime", "next-adapter.mjs")` with no checkout fallback; strict stable `x.y.z` marker on the entrypoint's first line as version owner; SHA-256 of that identical complete, unmodified byte sequence; initial version `0.1.0`. A sidecar manifest or Python distribution-version mapping is possible but creates a second authority or coupling and must be specified explicitly.
  - **Do not install additional dependencies to resolve these gates.** Installing packages cannot close schema/evidence qualification, satisfy the outdated review wording, or establish an adapter identity owner.

## Reflection

- durable な結論を Requirement / Design / Plan または accepted ADR に再記述する。
- User-selected review routing still needs reflection in the normative Plan; that edit has not been made in this checkpoint.
- No new product semantic decision is indicated for the already specified current-v1 repairs. Escalate only if future findings require changing public failure semantics, schema, privacy/security guarantees, or platform commitments.
- Worktree source/spec implementation state was not edited during the revalidation; the new Artifact is the only tracked change created by this continuation so far. The active goal remains Issue #8 completion.
