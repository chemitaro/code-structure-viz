---
種別: disc
ID: "20261001t114128z-disc"
タイトル: "a-core-rejection-v2-contract-closure"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-10-01"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["requirement.md", "design.md", "plan.md", "20261001t040546z--a-runtime-contract-analysis-result.md"]
reflected_to: ["design.md", "plan.md", "report.md"]
---

# 20261001t114128z-disc a-core-rejection-v2-contract-closure

採択済みAのA02 Core-invalid / model-record-limit failureを閉じるreference契約です。production/実TS/A03の認定ではありません。

## Inputs

- 開始checkpointはclean/pushed `e16f407901619b534ea0e831562f392bea0c63c6`（parent `9a151f1...`）。local HEAD/upstream/live GitHub SHA一致、通常commit/pushを確認。前sliceの新40 testsを含む関連505 tests、Ruff/format202/mypy167、SpecDock10 nodesがpass。
- Current R/D/P、accepted A、Pro advisoryのwire-independent semantic再利用/owner joinsがauthorityです。累積Strict固定点は`f4159066f3954454ad2f0c2701fa54bf1bc7bc4a`。src/旧v1/依存/lockfileは対象外です。

## Synthesis

- transport-admissibleとCore-admittedは別です。shape-valid model digest/source correspondence/proof/record違反は`response_validation / CSV-NEXT-PROTOCOL-001`。model/proof-validなactual wire record 10001は`model_validation / CSV-NEXT-LIMIT-005`で、実countを保持します。不正proofはcount gateより先に拒否します。
- `RejectedSemanticDecisionV2`は同じprivate candidate/source/assetsとclosed failure metadataをimmutableに保持します。admitted gate/compatibility/semantic/model projectionは持ちません。provenanceはsame-runtime候補とのobject joinを要求し、実control/version prefixを残してsemantic/compatibility/model/budgetはunobservedです。record実countはprivate failure measurementでありentity budget rowを捏造しません。
- expected child payload invariantの専用`SemanticCandidateInvalidErrorV2`だけをprotocol拒否へ変換します。owner錯誤や無関係のValueError/RuntimeError/MemoryError、検証入口の内部AssertionErrorを通常診断へ潰しません。既存のwire-independent invariant helpersのdata assertionsは従来どおりCoreのclosed-invariant検証として扱います。
- validatorはcandidateを再検証し、nominal type、実failure/code/reason/count/closed keysを照合します。private constructor helperはtrusted Python用であり、同一UID hostileへのsecurity boundaryではありません。

## Options and trade-offs

- accepted semantic algorithm/catalogを増やさず、新wireのtyped rejected ownerへ閉じます。old v1 runtime/envelope/publication decisionを認定の代用にせず、旧count fixtureはactual source-owned generated modelのtest fixtureへ抽出して再利用します。
- Core validationのexpected data exceptionと任意内部exceptionを分離し、保守上のbugをユーザー入力不正として隠すbroad catchを採りません。

## TDD / verification

- missing inspection API、既存payload invariantがplain ValueErrorのまま、record +1がexceptionのみ、Core rejectionをprovenanceへjoinできない各focused REDを確認。opaque union/専用error/実count/prefix joinsを最小変更してGREEN。
- generated model +1の初回GREENは40.58s（same original job exit0）で、invalid proofの優先順も検証。短いfailure-owner/metadata/内部fault/別runtime hardeningは19 passed（7.83s）。新20 testsを含むCore/provenance selectionは88 passed（163.43s）、actual 10000/10001とrecord-limit provenance joinの再検証も含みます。
- type narrowing/format後のruntime/source/Core関連selectionは583 passed、3 deselected（69.92s）。除外3件は直前88件で検証済みのgenerated large record casesで、静的typing/formatのみの後に同じ重いtestを繰り返していません。schema/doc-pointerは120 passed（4.20s）。各selectionは重複し、件数を合算しません。
- Ruff/check/format（204 files）、canonical `mypy src tests`（169 source files）、SpecDock sync/validate（nodes=10）とdiff-checkがpass。初回`mypy .`はSpecDock active symlinkから同じartifact moduleを重複検出したため、既存CIと同じ`src tests`へ訂正しました。union narrowing/local variable名の型エラーとformatを修正してGREEN。プロジェクト設定/ignoreを変えていません。
- 明示paths staging、complete staged diff検査、通常commit/pushでcheckpoint化します。new SHAとclean upstream/live equalityは次slice Inputsへ保存します。長時間jobは元sessionのexit0を保持し、quietを理由に重複起動していません。
- A02全体/full-suite、reader-owned prefix/public全refs、actual OS/TS/A03は未完了です。

## Reflection

- Current Design/Plan、契約文書と薄いReportへ完了範囲だけを反映し、reader/public closure・全A02 gate・A03・productionへ継続します。
