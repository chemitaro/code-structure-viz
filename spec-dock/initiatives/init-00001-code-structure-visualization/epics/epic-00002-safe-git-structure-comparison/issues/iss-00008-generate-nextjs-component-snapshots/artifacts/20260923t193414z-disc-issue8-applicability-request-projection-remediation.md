---
種別: disc
ID: "20260923t193414z-disc"
タイトル: "Issue #8 applicability request-projection analysis and remediation"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-09-23"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: []
reflected_to: []
---

# 20260923t193414z-disc Issue #8 applicability request-projection analysis and remediation

このArtifactはIssue #8のpackage-applicability候補に対するStrictコードレビュー、独立Strict分析、ローカルコード・テストを統合し、P1修正の範囲と残る判断を記録する。Requirement/Designを変更するdecisionではなく、production adapterまたはNode実行の完了証明でもない。

## Scope and identity

- Repository / branch: `chemitaro/code-structure-viz` / `iss-00008-generate-nextjs-component-snapshots`
- Strict review fixed SHA: `777e554a599c2f14b71e93f4a8c32f0edaa8fc96`
- Review range: `4f49ac9e7ccdf2c5d1b4846d5345a8c209f639d4..777e554a599c2f14b71e93f4a8c32f0edaa8fc96`
- Fresh Strict review session: `required-strict-github-connector-verificati-1080`
- Review transcript SHA-256: `59463c072fb59f5e17c7df05ef6a982f5a7e0a0ac1c5b39d4a69902511b9f0eb`
- Review output-log SHA-256: `0e0ffff2bf34fd94ed0aa979bb9921fb504e333ebfc4215b74742513dacd0e3e`
- Review result: valid JSON, `review_status=fail`; one P1 and one P2. GPT-5.6 Sol model and Pro reasoning were verified in the browser picker.
- Fresh Strict findings-analysis session: `required-strict-github-connector-verificati-1081`
- Analysis transcript SHA-256: `320a3be81f7094c36f0ff58c7445c8b0d77e4eeba4f0f4692aa13aeeade133e2`
- Analysis output-log SHA-256: `6f438fc728747a1ad9da04c1881729e3d0d2ee7fbce1f23cc7988c0a276a38e1`
- Analysis model/effort evidence: GPT-5.6 Sol / Pro, both verified by the model and thinking pickers. Strict GitHub verification bound the analysis to the exact repository, branch, and SHA above.
- Remediation commit / reviewed candidate SHA: `79e77ae3af536c5f72ca6eb360c55c46bf32d156`
- Fresh post-remediation Strict code review session: `required-strict-github-connector-verificati-1082`
- Reviewed range: `777e554a599c2f14b71e93f4a8c32f0edaa8fc96..79e77ae3af536c5f72ca6eb360c55c46bf32d156`
- Code review result: valid JSON, `review_status=pass`, `findings=[]`, `overall_correctness=patch is correct`, confidence `0.96`. GPT-5.6 Sol model and Pro reasoning were verified in the browser picker. The GitHub connector re-read the exact repository/branch tip and confirmed the full candidate SHA.
- Code review transcript SHA-256: `9aa97b092f633e9fef59a6c265cd3b5cb3cf1e96e5eb92cd5b115676d9042b70`
- Code review output-log SHA-256: `9946e9648dbb79384876fde23b9885bf0fe5d79e105ad7dfc60351f1dabff4ee`
- Reviewer verification boundary: the reviewer independently inspected the fixed GitHub range but did not rerun tests; local test evidence below is from the recorded local commands.
- Primary evidence packet: `.workbench/reports/issue8-package-review-1080.md` (ignored, non-canonical; its facts were checked against tracked code and tests).
- Related earlier root-cause evidence: `20260923t163655z-disc-issue8-verified-fd-dependency-analysis.md`.

## Root-cause synthesis

### `RG-01` — private request failed to apply package permission (P1, valid)

`NextSourceAcquirer` intentionally retains every requested root, package observation, and role row in the internal `SourceAcquisitionSeal`. That evidence is needed to prove the complete inventory and package-applicability matrix. It does not grant every root permission to enter the downstream Next adapter request.

Before remediation, `build_next_adapter_request` serialized all `plan.projects` and all `file_role_map` rows, and required those rows to match the complete captured source view. It did not project the matrix's `applicable_projects`. In a mixed workspace this made the non-applicable project and its package bytes part of the private Node request. The reference validator repeated the same overbroad equality rule. Existing acquisition coverage proved full internal retention, but there was no regression at the request boundary.

The defect is in the request-construction boundary, not in the package matrix or the full internal seal. It is reachable before Node launch; lack of a production Node process does not make the request-contract violation hypothetical. Current Requirement/Design authority requires only applicable roots to proceed downstream.

### `RG-02` — ordinary package read failure classification (P2, decision required)

The observed product path maps an ordinary package read failure to `CSV-NEXT-SOURCE-003/source_read`; the reference acquisition helper maps a package observation failure to `CSV-NEXT-APPLICABILITY-002/applicability`. The behavior mismatch is real, but the proposed public code/stage change is not uniquely determined by current-v1 prose and changes diagnostic/provenance meaning. No autonomous change is authorized by this evidence. Preserve this as report-only and do not mix it into the P1 patch.

## Adjudication and bounded remediation

The Strict analyst classified `RG-01` as `implementation-remediation` and `RG-02` as `requirement-decision-required`. Only the first route is implemented here.

Preserved guarantees:

- Keep every requested root, applicability observation, package byte, source view, plan row, digest, and seal identity in the internal source seal.
- Verify every role row against the complete source view, including rows that will not be serialized.
- Keep the package matrix permission-only; do not infer Node availability, `available`, or platform support.
- Preserve existing target values instead of silently removing or rewriting a target that names a non-applicable root.
- Leave malformed-package behavior, ordinary package-read classification, public schemas, process policy, verified-FD policy, and all-non-applicable behavior unchanged.

Changed private-request contract:

1. Require package-matrix project roots to equal the complete sealed-plan roots and retain existing overlap/path/integrity checks over that complete set.
2. Build request projects only from `package_applicability.applicable_projects`.
3. Validate all sealed role rows and bytes, but serialize/count decoded request bytes only for applicable roots; require request file paths to equal the applicable role-path set.
4. Recompute the normal file/project identities and request ID from the projected payload; leave canonical target values unchanged.
5. Make the independent reference validator compare projects/files against applicable plan roots. For a partial ledger, compare request paths to `ledger.safe_file_set ∩ applicable_role_paths`, and require only that safe applicable bytes be captured. A complete seal still requires every applicable role path to be captured.

The product change is in `src/code_structure_viz/adapters/next/protocol.py`. Focused tests are in `tests/unit/next/test_protocol.py`; the separate reference-validation regression is in `tests/contracts/test_next_contracts.py`, with the implementation in `tests/contracts/next_reference_validation.py`.

## Red/Green and verification

- First Red for the mixed request test observed both `apps/web` and `packages/ui` in the private request where only `apps/web` was expected.
- The public request regression now proves: all roots/package bytes remain in the internal seal; only applicable project/file data enters the private request; an explicit non-applicable-root target is preserved byte-for-byte; non-applicable package/source bytes are absent from the request.
- A mixed-root reference-validator test accepts the applicable projection and rejects the all-project projection.
- A first post-change contract run exposed a real regression: complete-role capture was also demanded from a partial seal, whose failed file has a planned role but no captured bytes. The validator now applies the capture assertion to every applicable role only for a complete seal, and to the safe applicable intersection for a partial ledger. The existing partial-safe regression passes after this correction.

Completed focused results:

| Check | Result |
|---|---|
| `uv run --locked pytest -q -p no:cacheprovider tests/contracts/test_next_contracts.py::test_reference_source_binding_accepts_only_applicable_projects_and_files tests/unit/next/test_protocol.py::test_mixed_request_projects_only_applicable_roots_and_files` | 2 passed |
| `uv run --locked pytest -q tests/unit/next/test_protocol.py tests/unit/next/test_source_acquisition.py` | 24 passed |
| `uv run --locked pytest -q tests/unit/next/test_applicability.py` | 31 passed |
| `uv run --locked pytest -q tests/contracts/test_next_contracts.py` | 543 passed |
| Targeted existing `test_round19_partial_source_result_preserves_safe_subset_and_ledger_identity` after correction | 1 passed |
| `uv run --locked pytest -q` on final code state | 1707 passed, 1 skipped in 211.43s |
| `uv run --locked mypy src tests` | passed; 150 source files |
| `uv run --locked ruff format --check .` / `uv run --locked ruff check .` | passed; 174 files formatted, all checks passed |
| `python3 ./spec-dock/scripts/spec-dock validate` | passed; `nodes=10` |
| `git diff --check` | passed |
| Pinned PlantUML HTML validator | static 8/8; browser 8/8 inline SVG; click, keyboard, bounds, focus trap, dismissal, focus restoration passed |

The first sandboxed Chrome startup timed out after the static 8/8 check; the exact same read-only validator command was run once with the execution permission needed to launch Chrome and passed the browser and zoom gates. The HTML was not changed.

The fresh exact-SHA Strict code re-review completed successfully on `79e77ae3af536c5f72ca6eb360c55c46bf32d156`: `review_status=pass`, no findings, confidence `0.96`. This closes the bounded package-projection P1 review loop. It is not the overall I05-PLAN-008/production gate or Issue #8 completion.

## Options and trade-offs

| Option | Decision | Rationale |
|---|---|---|
| Filter only the downstream request while preserving full internal evidence | Adopted | Satisfies current authority without weakening source completeness, provenance, or integrity checks. |
| Drop non-applicable roots from the seal itself | Rejected | Loses complete applicability evidence and changes the intended internal model. |
| Reclassify ordinary package-read errors as applicability failures in the same patch | Deferred | Changes consumer-visible code/stage semantics without an unambiguous normative decision. |
| Remove explicit targets that point into a non-applicable root | Rejected | Silent target rewriting is a separate observable behavior; this bounded projection preserves caller input. |

## Residual gates

- This remediation does not certify Node launch, verified executable-FD behavior, process observations, macOS/Linux support, `available`, wheel/sdist runtime contents, or Issue #8 completion.
- The verified-FD investigation remains separate: current macOS behavior did not establish a safe spawn mechanism, so no path-based fallback is introduced here.
- P2 `RG-02` remains unresolved and requires a Requirement/Design decision before changing its code/stage behavior.
- The package-projection P1 is closed for the exact reviewed SHA above. Any follow-on change requires its own current-SHA review; this package projection review is not the overall I05-PLAN-008 or Issue #8 completion gate.

## Reflection

No durable Requirement/Design decision changed. This Artifact records evidence and a bounded implementation that restores the existing applicable-root contract. Any later P2 decision must be made in canonical authority before code changes; production/process work remains subject to the Issue plan's remaining gates.
