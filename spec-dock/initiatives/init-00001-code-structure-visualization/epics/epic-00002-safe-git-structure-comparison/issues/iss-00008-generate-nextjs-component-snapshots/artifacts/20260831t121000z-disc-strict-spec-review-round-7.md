---
種別: disc
ID: "20260831t121000z-disc"
タイトル: "Issue #8 ChatGPT Use Strict Specification Review Round 7"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-08-31"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["20260831t095500z-disc-strict-spec-review-round-6.md"]
reflected_to: ["requirement.md", "design.md", "plan.md", "20260831t022707z--nextjs-component-snapshot-best-practice-guide.html"]
---

# Issue #8 ChatGPT Use Strict Specification Review Round 7

## Fixed point

- branch: `iss-00008-generate-nextjs-component-snapshots`
- expected/observed SHA: `a5bd61e0e2670ff540aab5891317ab54c23ab41a`
- GitHub connector exact match: true
- session: `issue-eight-strict-round-seven-2`
- GPT-5.6 Sol / Pro、48 attached files、約240,041 input tokens、32m00s
- exact-SHA GitHub Actions: CI run #160 success、6 jobs success
- result: `review_status: fail`、P0=0、P1=6、P2=0

## Recovery evidence

最初のRound 7試行はChatGPT rate-limit dialogが残り、`promptSubmitted=null`、conversation/target/controller/leaseなしで送信前停止した。診断後に同時実行状態の変化を確認し、GPT-5.6 Solのbrowser smokeが`ORACLE_BROWSER_OK`で完了してから、同じsemantic inputをfresh slugで一度だけ送信した。API fallback、重複turn、model downgradeはない。

## Remaining blockers and required closure

| severity | finding | required closure |
| --- | --- | --- |
| P1 | public target grammarがRequirementの`path:`とconfig/referenceの`component/module/file:`で二重化し、failed resolutionを成功response内で受理する | 外部CLI/config/requestは`path:<repository-relative file-or-directory>`へ統一し、内部semantic target keyと分離する。directoryはfrozen path setへ解決する。0件・ambiguous・out-of-scope・tainted/excludedは`CSV-NEXT-TARGET-001`、`payload_unavailable`、Artifactなしへ結合する。 |
| P1 | export witnessが既存public ExportBindingだけから生成され、binding非生成exportの省略を検出できない | public memberと独立した全export observationを定義し、owner、exported name、role、syntax identity、resolution、optional component IDを持たせる。Pythonがpublic bindingsとcoverageを導出・照合し、省略・重複・置換を拒否する。 |
| P1 | `max_entities`がRequirementのselected internal Module+Component budgetとlimits contractの全model recordsで衝突する | `budget.actual`/`entity_count`をpublished internal Module+Componentの和として再計算し、全record上限は`max_model_records`だけにする。500/501/override/model100001構成vectorを固定する。 |
| P1 | trusted declaration実bytesがTypeScript grammar/certified symbol profileと一致せず、signature digestもAST/TypeChecker由来でない | TypeScript 5.9.2 Programで4 virtual declarationsを読み、parse/semantic diagnostic 0をCI gateにする。certified symbols/signaturesをAST/TypeCheckerから導出してknown answerとexact compareし、trusted TypeIR/recognitionは導出済みidentityだけを参照する。 |
| P1 | non-file failure rootのmandatory seed setをadapterの`record_ids`が選べる | `record_ids`をsubmitted witnessへ降格し、root kindとrecordsからPythonがseed setを導出してexact compareする。export bindingからtarget component、incoming explicit re-export、barrel module、dependent bindingを閉じ、omission/excessを負例化する。 |
| P1 | recognition evidence、diagnostics、target completeness、failed filesなどに同一意味の複数accepted order/aggregationが残る | 全ordered collectionにcanonical sort/aggregation keyを定義し、提出配列そのものをcanonical listとexact compareする。permutation、duplicate、diagnostic count splitを負例化する。 |

## Best-practice adjudication

公開targetはユーザーが理解でき、既存Requirement例と一致する`path:`だけを正本とする。file/directoryの判定と展開は凍結済みSourceViewから行い、semantic model内のModule/Component/File IDやproof keyをCLIへ露出しない。directoryの複数一致は正常なfrozen setであり、曖昧とは扱わない。一方、存在しないpath、project境界外、shadowing、tainted/excluded memberを含むselectionはpublication不可とする。

残り5件も既存のfail-closed、independent recomputation、exact-byte determinism方針を具体化するもので、新たなproduction機能追加ではない。次のStrictは全6件をdata-only contractと正本文書へ反映し、clean exact SHAで行う。
