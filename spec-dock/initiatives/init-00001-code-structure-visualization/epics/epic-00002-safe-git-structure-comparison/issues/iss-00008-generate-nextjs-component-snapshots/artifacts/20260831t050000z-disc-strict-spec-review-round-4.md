---
種別: disc
ID: "20260831t050000z-disc"
タイトル: "Issue #8 ChatGPT Use Strict Specification Review Round 4"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-08-31"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["20260831t042000z-disc-strict-spec-review-round-3.md"]
reflected_to: ["requirement.md", "design.md", "plan.md"]
---

# Issue #8 ChatGPT Use Strict Specification Review Round 4

## Fixed point

- branch: `iss-00008-generate-nextjs-component-snapshots`
- expected/observed SHA: `6d3e03d62b34426bcae47860375758a8789e480c`
- GitHub connector exact match: true
- session: `required-strict-github-connector-verificati-515`
- GPT-5.6 Sol / Pro、21 files、約127,210 input tokens、26m09s
- result: `review_status: fail`、P0=1、P1=12、P2=0

## Findings and required closure

| severity | finding | required closure |
| --- | --- | --- |
| P0 | public `semantic-v1` のroot制約とNext child branchが交差し、有効なNext instanceを作れない | domainごとのclosed discriminated branchへ分離し、public rootへcomplete-empty/non-empty/partialとcross-domain mutationを通す。 |
| P1 | Project collection不在、汎用IDでkind違い参照を受理、Fact kind/value非連動 | closed `projects[]`、kind別ID/ref、参照存在・ownership・Fact discriminant validatorを追加する。 |
| P1 | PropsTypeIR schemaがDesignのliteral/tuple/function/reference規範と不一致 | Round 2で固定した全variant shapeへschemaを一致させ、variant mutation vectorsを追加する。 |
| P1 | adapter multi-project ownership、role precedence、order、base64/digestを局所schemaしか検証しない | cross-record invariantをversioned reference validatorとdata-only vectorsで固定する。 |
| P1 | partial-safe proofのrule/reason/count/set decompositionがopen | closed rule/reason/collection enumと集合等式、target witness一致をreference validatorで検証する。 |
| P1 | config/request/manifestでresource limit集合が分断 | 一つのresolved limits recordを全projectionとfingerprint preimageへ伝播する。 |
| P1 | Next diagnostic catalogがpublic diagnostic契約へ未接続 | catalogをcode/severity/recoverable/message/domain/ref permission/outcomeの単一authorityにする。 |
| P1 | public run-manifestのrequest/config/source/status/budget/toolchain/formatがNext規範と不整合 | Next snapshot専用の完全branchと全status full-manifest vectorsを追加する。 |
| P1 | run-summary/stdout-resultがNext selector/domainを拒否 | public schemas/docs/goldensをNextへ拡張する。 |
| P1 | TrustedTypeEnvironment/runtime manifestのexact set、ref、path、order、digest preimageが未固定 | exact profile、safe path、unique order、known-answer digest、shadow/augmentation negative vectorsを追加する。 |
| P1 | PlantUML contractがexact statement grammar/template/escape/marker/orderを未定義 | 行単位grammarとrendering table、complete-empty/non-empty/partial/attack goldensを固定する。 |
| P1 | semantic compatibility IDがself-reportedでalgorithm descriptorを欠く | closed descriptorとPython-side recomputation、known-answer vectorを追加する。 |
| P1 | Planがproduction前gateにしたdata-only contract vectorsが未実体化 | `tests/contracts` / fixturesに全主要規範のpositive/negative vectorsを作り、PLAN-008を実行可能にする。 |

## Local adjudication

P0は、public rootの既存property制約がNext `$ref` と同時適用されるため、ローカルschema構造からも再現可能な真のblockerである。P1もproduction実装不在そのものではなく、事前契約の不一致・open shape・cross-record invariant・exact-byte規範の未実体化を指しているため、PLAN-008完了前に修復する。

次のStrictは、public semantic/run/diagnostic/stdout接続とdata-only contract suiteを含むfresh exact SHAで行う。
