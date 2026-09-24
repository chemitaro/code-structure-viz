---
種別: disc
ID: "20260924t021633z-disc"
タイトル: "Issue #8 Strict dependency root-cause analysis"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-09-24"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: []
reflected_to: ["requirement.md", "design.md", "plan.md"]
---

# 20260924t021633z-disc Issue #8 Strict dependency root-cause analysis

複数の証拠を統合し、選択肢と trade-off を整理します。一つの source の調査は `research` を使います。

## Inputs

- 統合する evidence:
  - Exact Strict analysis of `chemitaro/code-structure-viz`, branch `iss-00008-generate-nextjs-component-snapshots`, GitHub tip `977feb02c05b908d5a25a97181138abe1ef54bd9`.
  - Oracle session `issue8-dependency-root-cause`; requested/resolved model `GPT-5.6 Sol`, reasoning `Pro`; both UI selections verified. Transcript SHA-256: `162e1dcc5edd1de5f32e1366423b70616f8d4b65b5bb0d9dd3a0082c1f88c1ac`.
  - Fresh Strict package-request projection review session `required-strict-github-connector-verificati-1096`; exact same candidate SHA; `review_status=pass`, `findings=[]`, confidence `0.96`. Its scope excluded overall Issue #8 readiness, adapter identity, package shipping, and runtime process execution.
  - Current-v1 Requirement, Design, Plan, schemas, production source and test files attached to the analysis; exact GitHub commit is authoritative over attachments.
  - Existing package-applicability remediation Artifact `20260923t193414z-disc-issue8-applicability-request-projection-remediation.md` and adapter-identity analysis Artifact `20260924t002133z-disc-issue8-strict-dependency-adapter-identity.md`.

## Synthesis

- Strict connector verification succeeded: repository, target branch, and full expected/tip SHA matched exactly; no default-branch or other-branch fallback. The answer records direct repository/branch/tip/tree/file/compare/check-run operations. Existing CI run `35941300614` is green 7/7; that is not runtime/package acceptance.
- Missing third-party Python/npm installation dependency is **not** the cause. Node is intentionally required only for applicable Next analysis. The missing production object is a first-party bundled adapter resource plus its identity owner.
- RG-01 was a real mixed-workspace P1: the private request included non-applicable roots despite a complete internal source seal. The applicable-only request projection fix is reviewed `pass` at this candidate; complete internal evidence and explicit targets remain intact. This narrow pass is not overall Issue certification.
- A second applicability mismatch exists: current Requirement/Design say either valid non-empty direct declaration is applicable, and two valid declarations are applicable regardless of whether their strings match. Production `applicability.py` and its unit/reference expectations instead classify two valid `dependencies.next` plus `devDependencies.next` entries as malformed. The current tests preserve the implementation error rather than the normative contract.
- RG-02 is a real production/reference mismatch. The production preflight maps an ordinary `package.json` read failure to `CSV-NEXT-SOURCE-003/source_read`; the reference acquisition helper maps it to `CSV-NEXT-APPLICABILITY-002/applicability`. The Strict recommendation is to classify failure to observe the permission evidence at the applicability stage, fail closed, and keep later source-file failures as `SOURCE-003/source_read`.
- The exact candidate contains no production `runner.py` or `_next_runtime` resource. Existing process policy needs adapter schema/version/SHA-256, but canonical authority does not close the package resource locator or stable version owner. This is a first-party resource/identity contract gap, not an install dependency failure.
- The old mypy failure was a variable type-flow collision in the reference validator and is fixed; it is not causal to the current dependency/applicability defects.
- The user adopted the package-applicability recommendations for current-v1. Requirement/Design/Plan now distinguish two valid direct declarations from malformed evidence and classify an ordinary root-package `READ` failure at applicability stage. Exact adapter resource locator/version/hash ownership remains recommended contract work for a later unit; actual adapter/process implementation remains behind `I05-PLAN-008`. No local test was run by the Strict analyst.

## Options and trade-offs

- Adopt the following outcomes in current-v1 authority, then implement in Red → Green order:
  1. Both valid direct `next` declarations are applicable, regardless of equality. Only a malformed table/value/key or invalid package encoding/JSON is malformed.
  2. An ordinary read failure of the root `package.json` is an applicability-evidence failure: `CSV-NEXT-APPLICABILITY-002`, stage `applicability`, `payload_unavailable`, non-recoverable, no public path reference, and no config/source/Node observation. A proven missing package remains `CSV-NEXT-APPLICABILITY-001` / non-applicable. Ordinary program/context source read failures remain `CSV-NEXT-SOURCE-003` / `source_read`; integrity drift remains the fatal integrity code.
  3. Expand the `APPLICABILITY-002` catalog message to cover inability to read or validate applicability evidence; do not publish raw `OSError`, absolute paths, or adapter data. Existing provenance schema already permits the stage/code pair; preserve the downstream unobserved/null suffix.
  4. Own adapter identity at `importlib.resources.files("code_structure_viz").joinpath("_next_runtime", "next-adapter.mjs")`, with one strict first-line marker `// code-structure-viz-next-adapter-version: 0.1.0\n`. Parse a stable `MAJOR.MINOR.PATCH` version from those exact bytes and hash the same complete unmodified entrypoint bytes, including marker and LF. Do not derive adapter version from Python package `0.1.0.dev0`, add a second version authority, or fall back to checkout paths, fixtures, or caller metadata.
  5. Keep portable resource identity separate from process execution identity. If resource materialization is needed, retain the `importlib.resources.as_file()` context through child exit and prove the hashed file is the one actually executed. Do not weaken same-file/verified-open policy to make a platform appear available.
- The user-authorized package-applicability clarification was added to current-v1 Requirement/Design/Plan before the corresponding source edits. Historical Round prose was preserved. Catalog and diagnostic schema were also aligned with the broader APP-002 message.
- Smallest implementation sequence:
  - Complete the current-v1 package applicability correction: RED/GREEN dual-valid declarations at production/reference public boundaries, then RED/GREEN package `READ` classification and no-downstream-read behavior while preserving other failure kinds.
  - Before production adapter work, close the exact resource locator/version/hash ownership in current-v1 Design/Plan and schemas; keep it behind the existing `I05-PLAN-008` gate.
  - After that gate, implement a pure fail-closed adapter identity resolver before any process spawn; cover absent/non-file/empty resource, BOM/CRLF/duplicate or misplaced marker, invalid/prerelease/build/leading-zero versions, byte count/hash, and no fallback.
  - Later prove actual adapter build output, wheel/sdist membership and byte reproducibility, offline installed-wheel execution, and OS process observation as separate gates. Do not claim runtime availability from the pure resolver.
- No new external Python dependency is needed for applicability or resource hashing; use existing standard-library facilities. Add/lock a Node build dependency only if the selected real adapter build demonstrably requires it.
- Remaining human-owned decision: if Darwin cannot satisfy the accepted same-file/verified-open process binding, keep it unavailable until a product owner explicitly changes platform/security scope. This unit must not introduce path-only hash/spawn or a security fallback.

## Reflection

- The user adopted the two package-applicability recommendations. Current-v1 changes: `requirement.md`, `design.md`, and `plan.md`; public diagnostic wording: `schemas/next-diagnostic-catalog-v1.json` and `schemas/diagnostic-v1.schema.json`; behavior and independent reference: `src/code_structure_viz/adapters/next/applicability.py`, `src/code_structure_viz/adapters/next/source_acquisition.py`, `tests/contracts/next_reference_validation.py`, `tests/contracts/test_next_contracts.py`, `tests/fixtures/next_contract_vectors.json`, `tests/unit/next/test_applicability.py`, and `tests/unit/next/test_source_acquisition.py`. No historical Round prose was changed.
- TDD evidence after canonical reflection: dual-valid Red failed 2/2 for the intended malformed result, then Green passed 2/2; package-read Red failed because production returned `CSV-NEXT-SOURCE-003/source_read`; Green plus preservation cases passed 7/7. Combined Next applicability/source-acquisition unit tests passed 57; contract applicability and early-failure tests passed 42; JSON Schema tests passed 119; Ruff passed; mypy passed 59 source files; full pytest passed 1716 with 1 skipped; SpecDock validation passed with 10 nodes. These are local candidate checks, not Strict review or Issue completion.
- Static Strict analysis establishes repository facts at its exact GitHub SHA only. It did not execute local tests, spawn Node, validate a wheel/sdist, prove process/FD behavior, or certify Issue #8 completion. The adapter resource identity contract and implementation/runtime/package gates remain open.
