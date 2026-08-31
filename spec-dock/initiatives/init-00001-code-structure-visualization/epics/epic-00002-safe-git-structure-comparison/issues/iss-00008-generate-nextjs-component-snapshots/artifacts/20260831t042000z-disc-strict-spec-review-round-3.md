---
種別: disc
ID: "20260831t042000z-disc"
タイトル: "Issue #8 ChatGPT Use Strict Specification Review Round 3"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-08-31"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["20260831t034100z-disc-strict-spec-review-round-2.md"]
reflected_to: ["requirement.md", "design.md", "plan.md"]
---

# Issue #8 ChatGPT Use Strict Specification Review Round 3

## Fixed point

- branch: `iss-00008-generate-nextjs-component-snapshots`
- expected/observed SHA: `1828a00913813c515912bf2c4f8f0aea9feb1225`
- connector exact match: true
- session: `required-strict-github-connector-verificati-511`
- GPT-5.6 Sol / Pro、17 files、約148,768 input tokens
- result: `review_status: fail`、P0=0、P1=8、P2=1

## Findings and adopted closure

| finding | closure |
| --- | --- |
| machine-checkable contract artifact不在、Plan gate逆転 | actual JSON Schemas、contract docs、catalog、contract testsを追加しStrictをPLAN-001後へ移す。 |
| multi-project compiler state/request role不足 | projectsごとのcompiler options/file IDs、filesのproject ID/roles/effective role、projectごとProgram一件を固定。 |
| ImportBinding/external renderをclosed modelが表現不能 | import member variant、external/unresolved render target、internal-only wrapを固定。 |
| Props variant/props_state/JS merge未決 | variant decision tree、Component props_state、JS grammar/precedence/default optionalityを固定。 |
| raw JSX defaultとrecognition矛盾 | raw JSX valueはnon-component export coverage、explicit Component targetはunavailable。 |
| partial-safe proofがadapter自己申告 | full discovered records/taints/failure roots/causal edges/target witnessを返し、Pythonがsubsetを生成・exact比較。 |
| LIMIT-002/005 catalog欠落 | exact code/message/severity/recoverabilityとresource mappingを追加。 |
| Issue #9 SourceView/empty facts/compatibility producer欠落 | exact `working-tree|commit`、empty `facts:[]`、Issue #8 identity versions/compatibility ID preimageを固定。 |

P2の旧config vocabularyもDesign/HTMLから除去する。次のStrictはactual contract filesを含むfresh exact SHAで行う。
