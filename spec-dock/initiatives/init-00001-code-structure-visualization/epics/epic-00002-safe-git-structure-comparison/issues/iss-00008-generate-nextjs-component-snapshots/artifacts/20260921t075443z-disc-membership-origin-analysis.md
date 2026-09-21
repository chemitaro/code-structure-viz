---
種別: disc
ID: "20260921t075443z-disc"
タイトル: "Issue #8 Membership-Origin Root Cause and Recommendation"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-09-21"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["20260912t065527z-disc-next-compiler-options-implementation.md"]
reflected_to: []
---

# 20260921t075443z-disc Issue #8 Membership-Origin Root Cause and Recommendation

複数の証拠を統合し、選択肢と trade-off を整理します。一つの source の調査は `research` を使います。

## Inputs

- Issue #8 のcurrent-v1正本: `requirement.md:12-47,25`、`design.md:12-54`、`plan.md:12-49`。
- 誤読されやすい履歴文: `design.md:986,1045`。先頭のcurrent-v1規則は、すべての`Round N`節をhistorical evidence（非normative）と定める。
- 実行可能なreference/test: `tests/contracts/next_reference_validation.py:4051-4445`、`tests/contracts/test_next_contracts.py:12843-12916`。
- Production境界: `src/code_structure_viz/adapters/next/configuration.py`、`schemas/next-config-v1.schema.json`、`schemas/next-source-plan-v1.schema.json`、`docs/contracts/next-config-v1.md`。
- ChatGPT相談: Oracle session `next-config-origin`、GPT-5.6 Sol、ChatGPT UIでPro推論を選択した証拠あり。8ファイルを添付し、約119,880 tokensを投入。回答は助言としてローカル証拠へ照合した。
- 一次資料: [TypeScript TSConfig `extends`](https://www.typescriptlang.org/tsconfig/extends.html)、[TypeScript TSConfig reference](https://www.typescriptlang.org/tsconfig/)。2026-09-21に公式サイトで確認。

## Synthesis

### 結論

問題はproductionのmembership resolverの誤動作ではなく、実装前契約の説明不足とtraceability driftである。技術上の最推奨は、`files`、`include`、`exclude`をそれぞれ宣言したconfigのディレクトリ相対で解決し、repository-relative POSIX pathへ正規化した後にselected project root内へ制限する方式（A）である。ただし、利用者が以前の質問1〜7の回答を破棄してゼロベース検討を求めたため、Aはまだ採択済みpolicyではない。canonical文書・membership実装を変更する前に、一度だけ明示決定を得る。

### 確認された証拠

1. **current-v1 Requirementの欠落:** `requirement.md:25`は閉じたJSONC、local `extends`、declaring config path、`files`/`include`排他、宣言場所相対の`baseUrl`/`paths`を定めるが、membership 3項目のraw相対path baseを定めない。
2. **曖昧な履歴文:** `design.md:1045`は`files`を「project-relative」と書く。しかし同じDesignの`design.md:17`以降は後続の`Round N`節を非normativeとしているため、これはcurrent-v1より優先する新しい契約ではない。なお「project-relative」が解決基準か、解決後のproject-containedな格納表現かも区別されていない。
3. **reference/testはAを実行:** referenceの`control_closure`は`files/include/exclude`各宣言元pathを保持し、membership値を宣言元pathから解決する。`test_config_inheritance_retains_origins_through_actual_source_seal`はroot `.`/`apps/web`、`files`/`include`、継承元`config/base.json`、`exclude`、同名root fileとの競合、空のchild overrideを検証する。`config/component.tsx`をcaptureしrootの`component.tsx`を読まないこともassertする。
4. **Productionの未実装境界:** `configuration.py`の`ResolvedControlClosure`はraw control値と`declaring_paths`を保持し、`resolve_compiler_options`は`baseUrl`/`paths`を処理する。一方、`files/include/exclude`のpath resolution、glob membership、source sealとの統合はまだproduction実装に存在しない。したがって現在は挙動バグではなく、着手前に閉じるべきcontract gapである。
5. **schemaの役割:** source-plan/config schemaは`declaring_paths`と解決済み`membership.patterns/exclude`を個別に形状検証するが、raw value・declaring path・解決結果の意味的なjoinをschema単体では保証しない。この対応はreference/source-seal testの実行可能な不変条件で所有する必要がある。
6. **外部一次資料:** TypeScript公式は「configで見つかったすべての相対pathを、それを宣言したconfigを基準に解決する」とし、extends先からの`files/include/exclude`継承と上書きを説明する。Issue #8のclosed subsetはTypeScriptのpath grammar全体を採用する義務までは持たない。特に既存の`..`禁止とproject containmentは別の安全制約として残る。

### 根本原因の推論

「相対値の解決基準」と「解決後のcanonical表示形式」を一語の`project-relative`へ畳み込んだことが、最も可能性の高いauthoring原因である。compiler-option resolverで導入したorigin保持がreferenceのmembershipへ拡張された一方、Requirement/Planのcurrent-v1説明とtrace mapが追従しなかったと推定する。これはコードから導いた推論であり、変更履歴上の意図を証明するものではない。

## Options and trade-offs

| 案 | 意味 | 評価 |
| --- | --- | --- |
| **A — 宣言元config相対** | 全membership値をdeclaring config directoryから解決し、canonical repository-relative値へ変換後、selected project root containmentを検査 | **技術的推奨。** TypeScript公式、reference、regression test、production closureのorigin情報と一致。 |
| B — project-root相対 | 継承元configの相対値もproject rootから解決 | 現Design履歴文とは読めるが、reference/testとTypeScript期待を変更する。Aより安全上の優位は確認できない。 |
| C — literal `files`とglobで異なる基準 | membership種類により解決基準を分ける | 公式根拠なしに非対称性と分岐を増やし、説明・実装・負例試験を複雑にする。 |

**提案:** Aを利用者に提示して採択確認を得る。解決元、格納形式、containmentを別フィールドの意味として明記する。Aでも`..`は拒否し続けるため、別directoryの共有base configからproject root外へ戻る設定はv1対象外となり得る。これを緩和するかは今回のorigin判断へ混ぜず、必要性を確認した別decisionにする。

## Recommended next steps

1. 利用者に一問だけ確認する: 「Issue #8 v1では、`files`・`include`・`exclude`を宣言元config directory相対で解決し、repository-relativeへ正規化後selected project root外を拒否するA案で固定してよいですか。」
2. 採択された場合、新しいdecision artifactに決定と根拠を残す。過去のpending artifactは当時の記録として維持する。
3. current-v1 Requirement、Design、Plan、`docs/contracts/next-config-v1.md`を同期し、`project-relative`をresolution baseとcanonical representationに分ける。Round 2などのhistorical節は上書きせず、current-v1から明示的にsupersedeする。
4. 既存source-seal testをRequirement/Planの独立criterionへtraceする。root/nested × files/include × inherited exclude、root同名ファイル、child empty override、read-onceをpositive/negative testsにする。`..`、absolute path、backslash、project escape拒否も固定する。
5. 別論点として、parent `include`とchild `files`のようなcross-kind extends時にcurrent referenceが両方を残して排他エラーにする挙動が、意図したclosed-subset policyかを確認し、既存契約内で明記・試験する。scopeを拡張してTypeScript完全互換を実装しない。
6. schema shapeは意味的joinの代替とせず、必要最小の文言補足に留める。contract-only境界でfocused/contract tests、SpecDock、ruff、mypy、full pytest、該当時PlantUMLを検証し、新しいexact SHAで独立reviewする。
7. contract gate後にpure production membership resolver、その後にsource-seal統合を別checkpointにする。今回の判断やresolver追加だけでIssue #8全体を完了扱いしない。

## Consultation and verification boundary

- ChatGPT session slugは`next-config-origin`。UI観測記録ではrequested/resolved model `GPT-5.6 Sol`、requested/resolved thinking `Pro`、どちらもverifiedである。回答はlocal branch、Requirement/Design/Plan、schema、tests/reference excerptに基づくadvisoryである。
- ChatGPT回答はGitHub connectorがlive branch SHAを`b8819dc18bdff7699e8d3dea936511074a9127e5`と報告したが、今回ローカルで独立確認したのはbranch名、clean working tree、HEADおよびlocal `origin/...` tracking refの同SHAまでであり、live GitHub SHAではない。このconnector報告は結論の根拠に使用していない。
- 公式TypeScriptページは今回webで直接確認した。引用リンクは上記Inputsに記録した。
- 今回は調査とこのevidence Artifact作成だけを行い、Requirement/Design/Plan/production sourceは変更していない。今回新たにテストを実行していない。

## Reflection

- Durableな製品判断は未確定。利用者の明示決定後にのみcurrent-v1 Requirement / Design / Planへ反映する。
- confidence: Aが最善である技術判断は高い。利用者がそのpolicyを承認したかは未確認。
- 未解決事項: Aの承認、`..`禁止下の共有base-config coverage、cross-kind membership inheritance、current HEADでのcontract review。
