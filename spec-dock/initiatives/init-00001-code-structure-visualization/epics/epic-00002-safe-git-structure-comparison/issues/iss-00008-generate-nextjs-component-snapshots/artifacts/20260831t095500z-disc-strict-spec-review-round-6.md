---
種別: disc
ID: "20260831t095500z-disc"
タイトル: "Issue #8 ChatGPT Use Strict Specification Review Round 6"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-08-31"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["20260831t073000z-disc-strict-spec-review-round-5.md"]
reflected_to: ["design.md", "plan.md", "20260831t022707z--nextjs-component-snapshot-best-practice-guide.html"]
---

# Issue #8 ChatGPT Use Strict Specification Review Round 6

## Fixed point

- branch: `iss-00008-generate-nextjs-component-snapshots`
- expected/observed SHA: `bb701f2ed4a38d0a2e8d89bc64a65530c90697c1`
- GitHub connector exact match: true
- session: `issue-eight-strict-round-six`
- GPT-5.6 Sol / Pro、39 attached files、約220,976 input tokens、36m43s
- exact-SHA GitHub Actions: CI run #159 success、6 jobs success
- result: `review_status: fail`、P0=0、P1=9、P2=2

## Closed since Round 5

- exact-SHA CIとminimum mypy blockerを解消した。
- role precedenceとencoded stdin boundary、canonical ID再計算、relation/fact基本不変条件、PropsTypeIR主要境界を実行可能にした。
- config/root projection、diagnostic catalog、PlantUML escaping、HTMLのstatic import/default evidence説明を具体化した。
- production Next adapter/CLI未実装はpre-implementation boundaryとしてfindingから除外された。

## Remaining blockers and required closure

| severity | finding | required closure |
| --- | --- | --- |
| P1 | taint closureがadapter提供causal edge集合上の到達性であり、必須edge欠落を検出しない | records、roots、closed rule/ownership tableから必須edgeとclosureをPythonが生成し、submitted edgeとexact equalityにする。frontierはset化し、edge omission、shared frontier、boundary role under-taintを負例化する。 |
| P1 | explicit targetsとproof completenessがrequestに結合されない | request targetsをcanonical keyへ変換し、proof keys/status/published IDsと完全一致させ、response envelopeからproof validationを必須化する。missing/extra/substitution/failed-as-resolvedを拒否する。 |
| P1 | non-component value exportとtype-only export coverageが構造上常に0 | 全export resolutionのwitness collectionをproofへ追加し、binding非生成exportもPythonが再計数する。非0正例とcount改変負例を追加する。 |
| P1 | resource limitsの集計単位と境界が閉じていない | 全static/model/process limitの対象・時点・UTF-8 bytes・inclusive境界・超過outcomeを固定し、limit-1/limit/limit+1 vectorsとaggregate array/model再計算を追加する。 |
| P1 | TrustedTypeEnvironmentがplaceholder digestでanti-shadowingもend-to-end未結合 | canonical declaration bytesまたは再現可能生成入力、実SHA/signature/license digest、2 physical resourcesから4 virtual filesへの展開、reserved witness結合を固定する。 |
| P1 | runtime manifestが自己参照し得てmember digestを実bytesと照合しない | inventory attestationとruntime manifestの役割を分離し、非循環digest projectionを定義し、contract fixture実bytesからsize/SHA/known answerを再計算する。 |
| P1 | stdout/status matrixがmanifest成功とselectorなしを実行契約化しない | `None | manifest | next:semantic-json | next:plantuml`を全status/exit/publication/stderr/stdout exact bytes matrixで固定する。 |
| P1 | PlantUML文書grammarがexternal relation targetを許さずrenderer/parserと不一致 | module/JSX targetに`X_<digest>`を明記し、external JSX goldenとmutationを追加する。 |
| P1 | compatibility descriptorにProject/File identity versionがない | `project`と`file`をidentity compatibility preimageへ追加し、known-answer vectorで強制する。 |
| P2 | `head_commit` regexが41〜63 hexも許可 | 40または64桁だけのalternationにし、39/41/63/65桁を負例化する。 |
| P2 | role subset数を8と誤記 | 非空subsetを7へ訂正する。 |

## Local adjudication

P1 9件はいずれもproduction実装の要求ではなく、実装前契約の完全性・独立再計算・exact-byte authorityに残る判断である。Issue #8のベストプラクティス案の意味を保ったまま、data-only schema、reference validator、fixtures、tests、contract docsへ具体化する。P2 2件も同じ修復単位で解消する。

次のStrictは、11件を反映し、ローカル全品質ゲートとGitHub CIが成功したfresh exact SHAで行う。
