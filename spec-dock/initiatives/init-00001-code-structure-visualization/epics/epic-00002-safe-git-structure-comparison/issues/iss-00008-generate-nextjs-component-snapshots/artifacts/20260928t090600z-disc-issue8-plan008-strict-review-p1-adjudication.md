---
種別: disc
ID: "20260928t090600z-disc"
タイトル: "Issue #8 I05-PLAN-008 Strict Review P1 Adjudication"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-09-28"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: []
reflected_to: []
---

# 20260928t090600z-disc Issue #8 I05-PLAN-008 Strict Review P1 Adjudication

## Provenance

- Repository: `chemitaro/code-structure-viz`.
- Branch: `iss-00008-generate-nextjs-component-snapshots`.
- Reviewed candidate SHA: `9f4f4af36b7ca88a52e1557c9ebc6e366128c2c5`.
- Fixed point: `f4159066f3954454ad2f0c2701fa54bf1bc7bc4a`.
- Review range: `f4159066f3954454ad2f0c2701fa54bf1bc7bc4a..9f4f4af36b7ca88a52e1557c9ebc6e366128c2c5`.
- Oracle session: `required-strict-github-connector-verificati-1324`; conversation `6ab9f258-810c-83e8-8b76-c2e2afe3ae26`.
- Oracle metadata records requested and resolved model `GPT-5.6 Sol`, model selection verified, and `Extra High` effort. Do not infer a stronger backend identity than those observations.
- The original wrapper remained waiting. The same conversation was recovered with `oracle session ... --live`; output reported `Capture identity: matched`, one assistant turn, and `State: completed`. This is not evidence that the original wrapper returned its own validated exit status.
- This artifact records the recovered source finding and its local adjudication. It is not a review pass, implementation-completion record, or Issue #8 acceptance.

## Source-native finding

The recovered Strict response returned `review_status: fail`, one P1, and no P0. The P1 states that I05-PLAN-008 requires a fresh current-SHA pass before starting I05-PLAN-002A, while the reviewed range already adds `src/code_structure_viz/adapters/next/runner.py::resolve_next_adapter_identity()` and its focused tests. It recommends removing that resolver, its test, and the production static-import allowlist from the PLAN-008 candidate, then submitting the slice only after the gate passes.

The reviewer reports exact GitHub verification of repository `chemitaro/code-structure-viz`, branch `iss-00008-generate-nextjs-component-snapshots`, and tip `9f4f4af36b7ca88a52e1557c9ebc6e366128c2c5`. Its response is advisory evidence; canonical Plan and local files determine the adjudication.

## Adjudication

**Finding accepted as valid P1.** Current `plan.md` makes I05-PLAN-008 precede I05-PLAN-002A and explicitly excludes new Next production behavior and a Node adapter from I05-PLAN-008. The reviewed commit `da70fd6ba360706b30f88d87d6ff69519bc1f1dc` adds the production resolver, `tests/unit/next/test_runner.py`, and an exception in `tests/security/test_python_static_boundary.py`. Those changes are the exact out-of-order slice named by the finding.

No canonical-plan rewrite is warranted. The bounded correction is to remove that resolver slice from this candidate while preserving the remaining Issue work and the original cumulative fixed point. This does not authorize starting I05-PLAN-002A early; that work remains gated by a fresh exact-SHA Strict pass.

## Correction and verification

The working-tree correction removes:

- `src/code_structure_viz/adapters/next/runner.py`;
- `tests/unit/next/test_runner.py`;
- the `importlib.resources` exception for the deleted production module from `tests/security/test_python_static_boundary.py`.

Focused verification after correction: 66 tests passed across the Python static-boundary test and Next applicability/source-acquisition unit tests. Full pytest passed: 1,866 passed, 1 skipped. `ruff format --check`, `ruff check`, `mypy`, SpecDock validation (`nodes=10`), and offline source/wheel build passed. These checks apply to the corrected working tree; they do not establish GitHub CI or Strict review for its not-yet-committed SHA.

The correction is not yet committed or pushed. A new review must use the same fixed point and the corrected clean, pushed full SHA. I05-PLAN-008 and Issue #8 remain incomplete until the required fresh review and all later plan steps are completed.
