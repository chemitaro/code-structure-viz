---
種別: disc
ID: "20260921t102546z-disc"
タイトル: "Issue #8 Fixed-SHA Review Finding: Membership Path Origin"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-09-21"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: []
reflected_to: []
---

# 20260921t102546z-disc Issue #8 Fixed-SHA Review Finding: Membership Path Origin

複数の証拠を統合し、選択肢と trade-off を整理します。一つの source の調査は `research` を使います。

## Inputs

- 統合する evidence:
  - Fixed-SHA review result returned by the completed independent reviewer task issue8_fixed_sha_review: candidate 736539dea2297e29a0e3989456f683c1e8f73742; review_status=pass, P0=0, P1=0, P2=1.
  - The P2 is a documentation/traceability finding: Requirement and docs/contracts/next-config-v1.md do not state the raw membership path base; the newer membership-origin analysis concludes that A is unadopted and asks for another human decision.
  - Current Requirement lines 18-47, Design lines 17-60 and 498-510, and Plan lines 17-49 establish current-v1 authority precedence: current normative text and its specified schema/reference/test chain supersede historical Round text and advisory Artifacts.
  - tests/contracts/next_reference_validation.py preserves the declaring path for each include/exclude/files field and resolves each value from that declaration location before repository-relative normalization and project containment.
  - tests/contracts/test_next_contracts.py::test_config_inheritance_retains_origins_through_actual_source_seal exercises root and nested projects, files/include, inherited config origins, excludes, same-name root files, child empty override, and single-read behavior.
  - The original Artifact 20260921t075443z-disc-membership-origin-analysis.md is retained as advisory evidence; this Artifact records the review-based reconciliation without rewriting that history.

## Synthesis

- 一致する事実と未確定事項:
  - The review found no P0/P1 and accepted the package-only applicability scope; the sole P2 is explanatory traceability, not a request to change behavior.
  - The statement that membership option A is not adopted is not supported by the repository's current-v1 authority-selection rule. The current reference validator and regression test already choose declaring-config-directory-relative resolution.
  - Canonical rule: resolve each files/include/exclude value from the directory of the config file that declares it, including inherited controls; normalize the resolved value to a repository-relative POSIX path; reject unsafe path grammar and values outside the selected project root. Resolution base and canonical representation are distinct.
  - This is a documentation correction to expose an existing current-v1 semantic join. It adds no new TypeScript compatibility promise, filesystem behavior, or path-policy relaxation. No human product decision is required by this evidence.

## Options and trade-offs

- 選択肢と利点・制約:
  - Adopt the reviewer's documentation-correction recommendation: clarify Requirement, Design, Plan, and the current next-config contract, and add a direct trace to the existing source-seal regression.
  - Do not change the reference algorithm, production behavior, JSON schemas, or historical Round sections. Keep the 20260921 membership-origin Artifact unchanged as advisory history.
  - Do not retain the unsupported conclusion that A needs a new human decision; that would contradict the current authority-selection rule and executable current-v1 evidence.

## Remediation and verification

- Canonical files clarified: issue Requirement, Design, and Plan current-v1 sections; docs/contracts/next-config-v1.md current-v1 contract.
- Direct regression trace: test_config_inheritance_retains_origins_through_actual_source_seal.
- Behavior changes: none.
- Verification commands and results on the local candidate (2026-09-21, Asia/Tokyo):
  - `uv run pytest tests/contracts/test_next_contracts.py tests/unit/next/test_configuration.py -q -k 'config_inheritance_retains_origins_through_actual_source_seal or project_membership_rejects_declaring_config_escape or project_configuration_rejects_observed_root_config_omitted_from_candidates'` — 6 passed, 539 deselected.
  - `./spec-dock/scripts/spec-dock validate` — `spec-dock: ok (validate) nodes=10`.
  - `git diff --check` — passed for the tracked diff after final edits; the Issue Artifact was also included in successful SpecDock tree validation.
- Remaining gates: current-tree full pytest, full quality checks, pinned PlantUML, clean/pushed exact candidate, and fresh fixed-SHA independent review are not established by these focused checks.
- Re-certification: pending a fresh fixed-SHA independent review of the corrected candidate. This result does not certify Issue #8 implementation or CLI-to-Artifact acceptance.

## Reflection

- durable な結論を Requirement / Design / Plan または accepted ADR に再記述する。
  - Rewritten in the current-v1 Requirement, Design, Plan, and next-config contract as an explanation of the existing reference/test authority; no ADR or product-decision change is introduced.
  - The original review pass remains applicable to candidate 736539d only. This documentation correction creates a new candidate and requires fresh review before the fixed-SHA finding is considered re-certified.
