---
種別: disc
ID: "20260831t073000z-disc"
タイトル: "Issue #8 ChatGPT Use Strict Specification Review Round 5"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-08-31"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["20260831t050000z-disc-strict-spec-review-round-4.md"]
reflected_to: ["design.md", "plan.md", "20260831t022707z--nextjs-component-snapshot-best-practice-guide.html"]
---

# Issue #8 ChatGPT Use Strict Specification Review Round 5

## Fixed point

- branch: `iss-00008-generate-nextjs-component-snapshots`
- expected/observed SHA: `c8c5a9931895f8c37c3bef82635e96c0c9757426`
- GitHub connector exact match: true
- session: `required-strict-github-connector-verificati-524`
- GPT-5.6 Sol / Pro、35 files、約190,537 input tokens、41m20s
- result: `review_status: fail`、P0=0、P1=11、P2=1

## Closed since Round 4

- public `semantic-v1` のNext branchは独立したdiscriminated branchとなり、旧P0を解消した。
- Project record、typed ID prefix、Fact kind/value、PropsTypeIR field shape、unified limits record、public diagnostic branch、run/stdout Next enum、compatibility descriptor、PLAN-008 data-only suiteは実体化した。
- production adapter/CLI未実装とcurrent CLIのNext拒否はpre-implementation boundaryであり、findingではない。

## Remaining blockers and required closure

| severity | finding | required closure |
| --- | --- | --- |
| P1 | exact-SHA CIのminimum laneがmypy 13 errorsで失敗 | `uv run mypy src tests`の型境界を修復し、minimum pytest/offline buildまでCIを完走させる。 |
| P1 | role precedenceが逆でencoded stdin aggregate未検証 | `control > context > program`を正しく実装し、exact request bytesの96 MiB境界vectorを追加する。 |
| P1 | typed ID prefixのみでcanonical identity digestを再計算せず、request/response projectionも未結合 | kind別identity preimageから全IDを再計算し、requestのproject/file/compiler/role/digestとresponse modelを照合する。 |
| P1 | relation/factが不可能なsemantic stateを受理 | static/dynamic relationをdiscriminateし、boundary facetとModule/Fact exact mirrorをcross-record検証する。 |
| P1 | PropsTypeIR canonicalizationと上限が未実行 | flatten/sort/dedup、rest/optional/type-parameter、depth/node/member/property上限をrecursive validatorと境界vectorで固定する。 |
| P1 | partial-safeがadapter申告taintを独立導出しない | failure rootとcausal rulesからPythonがtaint fixed point、subset、coverage、target witnessを再計算する。 |
| P1 | config/domain manifest/root manifestが異なるshapeで横断再計算不能 | canonical ResolvedNextConfig/NextSnapshotRequestとprojection/digestを定義し、whole-run validatorとNode probe state unionを追加する。 |
| P1 | run-summary/stdout-resultとmanifest outcomeの横断整合がない | manifest/domain/summary/stdout/published bytes/stderrを一つのstatus vectorで検証する。 |
| P1 | semantic compact diagnosticがcatalogを迂回 | public diagnosticを共用するかexact catalog projectionを検証し、status/outcome/ref permissionを照合する。 |
| P1 | trusted/runtime profileがexact v1 setを固定しない | required declarations/certified symbols/runtime members/licensesのknown-answer exact setとdigest結合を固定する。 |
| P1 | PlantUML contract docとreference rendererのexact bytesが不一致 | grammar/order/marker/relation facetsを一つのauthorityへ統一し、goldenと独立parserを一致させる。 |

## Optional finding and closure

P2は人間向けHTMLの`static_import` value/type/re-export説明と`default_evidence` enumの同期不足だった。commit `ed87207051c889707c773a381db98b86a5803ed9`で修正し、5/5 PlantUML描画とzoom/accessibility gateを再検証した。

## Local adjudication

11件はいずれもproduction implementation不在の指摘ではなく、pre-implementation contractの独立再計算、projection equality、canonicalization、exact-byte authorityに残る実装判断である。既存Designの意味を変更せず、data-only reference validator、schema、docs、fixtures、testsを修復する。

次のStrictは、11件の修復とclean minimum CIを含むfresh exact SHAで行う。
