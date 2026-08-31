---
種別: disc
ID: "20260831t034100z-disc"
タイトル: "Issue #8 ChatGPT Use Strict Specification Review Round 2"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-08-31"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["20260831t031600z-disc-strict-spec-review-round-1.md"]
reflected_to: ["requirement.md", "design.md", "plan.md", "../iss-00009/requirement.md", "../iss-00009/design.md", "../iss-00009/plan.md"]
---

# Issue #8 ChatGPT Use Strict Specification Review Round 2

## Fixed review point

- repository: `chemitaro/code-structure-viz`
- branch: `iss-00008-generate-nextjs-component-snapshots`
- expected/observed SHA: `550215223d63bc15ec5fd4d7d4bc03b41669d2df`
- exact match: true
- session: `required-strict-github-connector-verificati-509`
- model/reasoning: GPT-5.6 Sol / Pro
- evidence: 17 files、約143,160 input tokens
- tests executed by reviewer: false
- result: `review_status: fail`、P0=0、P1=9、P2=2

GitHub connectorがbranch tipとexpected SHAの完全一致を確認し、fallback sourceを使わずレビューした。
出力はadvisoryであり、修復判断はcanonical R/D/P、current source/schema/testsと照合して採用する。

## Closure achieved since round 1

- Round 1 P0のdeclaration source欠落は`TrustedTypeEnvironment/v1`によりP0として解消した。
- stdout parserを再実装しない方針は閉じた。
- declaration identityとExportBindingの分離、project/applicability/target matrix、two-plane graph、single-domain outcome、extension surface列挙は改善した。

## Residual P1 findings and adopted remediation

| ID | residual blocker | adopted closure |
| --- | --- | --- |
| R2-P1-1 | trusted declarationsのshadow/augmentation/paths hijack | reserved virtual paths/specifiers/global、anti-shadowing rejection、closed diagnostic、negative fixturesを固定する。 |
| R2-P1-2 | recognition循環、`export default Identifier`、star expansion | candidate収集からfinite fixed-pointまでの単調algorithm、default/alias/call matrix、Component-only star bindingを固定する。 |
| R2-P1-3 | project-owned source/config/module resolution/symlink | per-project descriptorへsource roots/configを移し、JSONC/glob/resolution/default/symlink policyを閉じる。 |
| R2-P1-4 | one-freeze、protocol IDs、digest preimage、limits | control bytesを再読しないtwo-phase freeze、family/request/response schema、self-field除外preimage、determinism tuple、全decoder/model limitを固定する。 |
| R2-P1-5 | PropsTypeIR/JS props shape | recursive recordをfield-levelで閉じ、TS/TSX/JS/JSX props-source matrix、unknown/no-props/any、overload coverageを固定する。 |
| R2-P1-6 | alias/dynamic/client seedのalgorithm矛盾 | alias edge最大64、exact wrapper AST/symbol patterns、client app seed role、logical/map traversalを固定する。 |
| R2-P1-7 | partial-safe subset証明なし | typed taint graph、target別partial matrix、coverage/count reconciliation、Python再計算predicateを固定する。 |
| R2-P1-8 | public schema/config/packageがimplementation stepへ先送り | field-level public contract authoringをStrict前gateに置き、schema/grammar/projection/build/license manifestを正本化する。 |
| R2-P1-9 | Issue #9 presence/target/fact/version/source mismatch | domain absenceだけempty-side、diff project/target、typed fact/member/relation delta、current SourceView、compatibility matrix、single-domain wordingへ修復する。 |

## P2

- managed metadataの`Nextjs`表記はSpecDock所有のためraw editせず、SpecDock commandで直す。
- Node test path、packaging owner、offline build、format gateを一意にする。

## Gate

- 上記をcanonical authorityへ反映する。
- SpecDock/HTML/format validation後、commit/pushしclean exact upstream SHAを作る。
- fresh ChatGPT Use StrictでP0/P1=0、`review_status: pass`を確認する。
- passはproduction implementation完了ではなくimplementation-readinessである。
