---
種別: disc
ID: "20260831t141500z-disc"
タイトル: "Issue #8 ChatGPT Use Strict Specification Review Round 8"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-08-31"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["20260831t121000z-disc-strict-spec-review-round-7.md"]
reflected_to: ["requirement.md", "design.md", "plan.md", "20260831t022707z--nextjs-component-snapshot-best-practice-guide.html"]
---

# Issue #8 ChatGPT Use Strict Specification Review Round 8

## Fixed point

- branch: `iss-00008-generate-nextjs-component-snapshots`
- expected/observed SHA: `89a9d53fb4fbd4bd8d89acf02279de188b9f11c8`
- GitHub connector exact match: true
- session: `issue-eight-strict-round-eight`
- GPT-5.6 Sol / Pro、43 attached files、約217,660 input tokens、33m50s
- exact-SHA GitHub Actions: run `33394598930` / run number 161 success、7 jobs success
- result: `review_status: fail`、P0=0、P1=4、P2=0

## Closed since Round 7

- Trusted TypeScript 5.9.2 profile、AST/TypeChecker certified inventory、failure-root seed/causal edge独立導出、canonical order/duplicate/diagnostic aggregationは実質的に閉じた。
- production Next adapter/CLI未実装はfindingではない。

## Remaining blockers and required closure

| severity | finding | required closure |
| --- | --- | --- |
| P1 | Next non-empty targetのroot run manifestがcommon object target schemaとNext string validatorを同時に満たせない | `snapshot + next` branchだけroot `request.targets`を`next-config-v1#/$defs/target_key` string arrayへdiscriminateし、Python/SQLAlchemyのobject grammarを維持する。non-empty正例、object/mixed/old/order/duplicate負例、全projection equalityを追加する。 |
| P1 | ExportObservationがpublic bindingから再生成され、observation/binding/countの協調省略を検出できず、value/typeをpublic bindingへ戻す | frozen source bytesからPythonがsource-level export token/span censusを独立導出し、Node observationのsyntax identity・owner・name・role・resolutionと完全照合する。public ExportBindingはComponentへ一意解決したvalue exportだけ。value/type/unknownはcoverage-only。coordinated omission、type/value/unknown/star conflict/substitutionを拒否する。 |
| P1 | `max_entities` 501件を`payload_unavailable`へ分類する前にmodel validatorがassert rejectする | model構造/count validationは`max_model_records`だけを適用しinternal entity countを返す。publication前の独立EntityBudgetGateが`max_entities`を適用し、`CSV-NEXT-LIMIT-005`、actual count、manifest-only outcomeへ変換する。500/501/override/100001 response-to-outcome vectorを追加する。 |
| P1 | context-only `.d.ts` がModule/Component/member/relation/factとして公開・target選択可能 | public Moduleはprogram roleかつ`.ts/.tsx/.js/.jsx`だけ。全semantic childrenはprogram Module由来だけ。`.d.ts`、package.json、tsconfig/jsconfig direct targetは`CSV-NEXT-TARGET-001`/payload unavailable。directory proofではprovenance Fileを含めてもsemantic entity化しない。 |

## Best-practice adjudication

Nextのroot run-manifest requestはdomain-discriminated branchで`path:` stringを正本とし、既存Python/SQLAlchemy target objectを変更しない。

ExportObservationの独立性は別のadapter自己申告streamでは成立しない。Pythonが凍結済みsource bytesに対するclosed syntax censusを所有し、各export observationのrepository-relative owner、byte span、syntax kind、exported name、role/re-export属性を照合する。TypeChecker resolutionはNodeが提示できるが、syntax observationの欠落はPython censusで拒否する。public bindingは一意なComponent value exportだけに限定する。

entity budgetはvalid modelのpublication policyでありprotocol validityではない。context/control filesはprovenanceとcompiler contextとして保持するが、semantic entity ownerにはしない。

次のStrictはこの4件を正本・schema・data-only executable contract・HTMLへ反映したclean exact SHAで行う。
