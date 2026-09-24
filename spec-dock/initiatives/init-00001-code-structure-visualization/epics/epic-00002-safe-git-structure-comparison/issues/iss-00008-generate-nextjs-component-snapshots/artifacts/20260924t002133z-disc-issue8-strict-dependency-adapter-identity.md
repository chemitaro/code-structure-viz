---
種別: disc
ID: "20260924t002133z-disc"
タイトル: "Issue #8 Strict dependency and adapter identity analysis"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-09-24"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: []
reflected_to: []
---

# 20260924t002133z-disc Issue #8 Strict dependency and adapter identity analysis

複数の証拠を統合し、選択肢と trade-off を整理します。一つの source の調査は `research` を使います。

## Inputs

- 統合する evidence:
  - canonical Requirement / Design / current-v1 Plan at `904ca3b4d8a4b759ba70a31659dc9fa0b6cc3d11`.
  - `schemas/next-process-launch-policy-v1.schema.json`, `schemas/next-process-launch-observation-v1.schema.json`, `schemas/next-provenance-v1.schema.json`.
  - current production source: `src/code_structure_viz/adapters/next/{applicability.py,source_acquisition.py,protocol.py}`; there is no production runner or `_next_runtime` resource at the fixed point.
  - local-only Strict analysis session `required-strict-github-connector-verificati-1092` (GPT-5.6 Sol / Pro, UI verified); transcript SHA-256 `0753dbe350ad4aed097118c6417272195ff30ba24d382a24db8ac7f678089cf2`.
  - local-only Strict brief session `required-strict-github-connector-verificati-1093`; transcript SHA-256 `ea7e08ec383387117d8cd592c2d40c3424c7932c0fe0adfa9ac0f2c0029ccbc2`.
  - local-only expanded-scope Strict brief session `required-strict-github-connector-verificati-1094` (GPT-5.6 Sol / Extra High, model and thinking picker verified); transcript SHA-256 `b261cd6d1477e12b9152504b32d03e4c815e9c1fd35d20c92a56c09564ae1819`.
  - local-only current-checkpoint Strict analysis session `required-strict-github-connector-verificati-1095` (GPT-5.6 Sol / Pro, both UI selections verified); transcript SHA-256 `244c564380b2f92d789aab4dde5552e9ed8fb6e9ecd84ac595c9b6ec17caa8aa`.
  - current exact-SHA review evidence: Strict sessions 1090 (GPT-5.6 Sol / Pro) and 1091 (GPT-6 Pro / Pro, UI Latest / Pro) both pass; neither 1091 nor the internal GPT-6 Astra/Max-assigned fresh review is relabeled as an observed Max setting. The fresh independent review returned P0/P1/P2=0, pass, on `f4159066f3954454ad2f0c2701fa54bf1bc7bc4a..904ca3b4d8a4b759ba70a31659dc9fa0b6cc3d11`.
  - local CI evidence from `gh run view`: run `35928499565` succeeded all 7 jobs at `904ca3b4d8a4b759ba70a31659dc9fa0b6cc3d11`; run `35938390976` succeeded all 7 jobs at `9dbd3ae1649ed0e3c1b418756b7d33a4aa8883e1`; latest run `35940465837` succeeded all 7 jobs at `36dc45eb2c01b57a0d0f42f3ef79e8ede6f003bd`. Historical run `35924354504` at `946653238a776a55ac301f8d357343e145dd7efb` failed `product-test-minimum` at mypy, while package sync/offline wheel-sdist job passed.
- Current-checkpoint inspection: HEAD and configured upstream both equal `36dc45eb2c01b57a0d0f42f3ef79e8ede6f003bd`; tracked worktree clean after push. Strict session 1095 verified the preceding code candidate `9dbd3ae1649ed0e3c1b418756b7d33a4aa8883e1`; commits `9dbd3ae` and `36dc45e` only add/update this evidence Artifact. Requirement/Design/Plan and production source remain unchanged from `904ca3b4d8a4b759ba70a31659dc9fa0b6cc3d11`.
- All Oracle transcripts and reviewer session logs above are local operational evidence outside the Git commit; they are not GitHub artifacts.
- Strict connector verification in sessions 1092 and 1094 confirmed repository `chemitaro/code-structure-viz`, branch `iss-00008-generate-nextjs-component-snapshots`, and exact tip SHA `904ca3b4d8a4b759ba70a31659dc9fa0b6cc3d11`. Session 1095 confirmed exact branch tip SHA `9dbd3ae1649ed0e3c1b418756b7d33a4aa8883e1` on the same repository/branch.

## Synthesis

- 確認できた原因:
  - The historical CI failure was not caused by a missing Python/Node dependency or lockfile drift. `tests/contracts/next_reference_validation.py` rebound a non-optional `source_view` local to an optional union, triggering strict mypy. The current SHA contains the narrowly scoped rename to `sealed_source_view`; current CI is green. Do not add dependencies, widen types, suppress mypy, or weaken checks for that failure.
  - Python core and Next runtime have intentionally different dependency boundaries. `PackageApplicabilityMatrix` decides applicability only from direct `dependencies.next` / `devDependencies.next`; Node is required only for applicable Next analysis. The checked-in reference runtime inventory does not prove that a production adapter is shipped.
  - The remaining implementation blocker is a missing production adapter identity owner, not a failing package install: the process policy schema requires `adapter.schema`, `adapter.version`, and `adapter.sha256`, but the fixed commit has no installed production adapter resource under `src/code_structure_viz/_next_runtime/` and no corresponding machine-readable version owner.
  - Design fixes the resource directory as `src/code_structure_viz/_next_runtime/` and the planned resolver as `runner.py` using `importlib.resources` without checkout fallback; process argv fixes the virtual basename `/.code-structure-viz/next-adapter.mjs`. Neither source fixes the installed resource's exact relative locator or how its stable version is derived.
  - `pyproject.toml` currently declares Python distribution version `0.1.0.dev0`; the adapter policy schema accepts only stable `x.y.z`. The distribution version therefore cannot be copied into `adapter.version` without a new mapping rule or schema change.
- Strict review progression:
  - Session 1093 correctly rejected a host-independent-only `ProcessLaunchPolicy` builder because production Node / adapter identities and private cwd were not owned by that slice.
  - The user-authorized scope expansion for session 1094 resolved the scope blocker by moving the first slice to pre-launch host/resource resolution. Session 1094 still found the adapter resource/version owner absent. Node realpath/hash/version resolution and private empty cwd can be owned by that resolver, but they do not substitute for adapter identity.
  - Keep four stages distinct: (1) resolve/open/hash the exact Node and adapter resources, (2) probe and validate stable Node `>=22`, (3) construct `ProcessLaunchPolicy`, (4) perform the actual adapter spawn and create `ProcessLaunchObservation`. The first three do not prove stage 4 or production availability.
- 未確定事項:
  - The exact `importlib.resources` locator for the production adapter entrypoint and the source of `adapter.version` are not fixed in production source or current package inventory.
  - Test fixture `tests/fixtures/next_runtime/adapter.js`, fixture version/hash values, caller-provided metadata, and future G11 runtime build inventory are not valid substitutes for an existing production resource.
  - Strict session 1095, on exact pushed SHA `9dbd3ae1649ed0e3c1b418756b7d33a4aa8883e1`, independently concluded the locator/version/hash owner is a material design/ownership gap, not an implementation detail uniquely derivable from the current specs. Its answer identifies the exact human decision below.

## Options and trade-offs

- 選択肢と利点・制約:
  - **Recommended decision candidate (not yet accepted):** use exactly `importlib.resources.files("code_structure_viz").joinpath("_next_runtime", "next-adapter.mjs")`, with no checkout fallback. Store a strict stable-semver marker in that entrypoint's first line, then compute `adapter.sha256` over the identical unmodified complete bytes, including the header. This gives path, version, and hash one byte owner, keeps caller values and test fixtures out of the trust chain, matches the fixed virtual argv basename and already-planned resource directory, and needs no extra dependency. A proposed initial value is `0.1.0` (stable x.y.z aligned with the existing package's 0.1.0 base, but not derived from its `0.1.0.dev0` metadata); this initial value still requires explicit adoption. G11 must later prove the resource is present in wheel/sdist and reproducible; this choice does not claim that package acceptance has already happened.
  - Alternative: use a sidecar version manifest in `_next_runtime/`. This can be easier for build tooling, but its relation to the executable bytes must be specified and validated, and its exact resource identity becomes a second authority.
  - Alternative: equate adapter version with the Python distribution version. This avoids a sidecar but couples an independently versioned runtime adapter to the whole Python package and is not specified by current R/D/P.
  - No-go alternatives: fixture/dummy identities, caller-supplied path/version/hash, source-file hash for different compiled bytes, or claiming the future build inventory exists now.
- Narrow decision needed before production implementation:
  - Accept/reject the complete candidate: exact locator above; first-line header with stable `x.y.z`; version parsed from that same entrypoint; SHA-256 of the identical unmodified full bytes; initial value `0.1.0`. Alternatively provide an exact locator, machine-readable version owner, same-byte hash rule, and initial value.
  - Strict 1095's next executable unit after the decision is `I05-PLAN-002A — bundled adapter identity resolver`, with production path `src/code_structure_viz/adapters/next/runner.py` and focused test `tests/unit/next/test_runner.py`. It should resolve the exact package resource, read/hold bytes once, parse the closed header, hash those same bytes, and fail closed on missing/non-file/read/header errors. The brief's suggested negative cases include missing resource, directory, empty bytes, header missing/duplicated/not first, prerelease/build metadata, `0.1.0.dev0`, extra whitespace/BOM/CRLF/invalid encoding, caller override, checkout fallback, and fixture fallback.
  - If accepted, update the canonical Design/Plan at the implementation boundary, then run this resolver unit TDD. Do not edit the public schema solely to make the missing owner appear resolved.
- Other implementation constraints remain unchanged:
  - Do not add/update Python/npm dependencies or locks as a response to the historical mypy failure.
  - Node probe, policy materialization, adapter process observation, and `production available` must remain separate observable stages.
  - No adapter process spawn, production observation, production availability claim, or wheel/sdist acceptance can be inferred from pre-launch identity resolution.

## Reflection

- durable な結論を Requirement / Design / Plan または accepted ADR に再記述する。
- This artifact records evidence and a decision candidate only. It does not amend or supersede Requirement, Design, Plan, schemas, or their accepted process-security guarantees. Canonical reflection is pending the user's decision on the exact resource locator, header/version source and initial stable version, and same-byte hash rule.
