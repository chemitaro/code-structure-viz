---
種別: ADR（Architecture Decision Record）
ID: "20261003t142223z-adr"
タイトル: "SI06 未観測captureを現publication v2へ限定訂正"
状態: "accepted"
作成者: "iwasawayuuta"
最終更新: "2026-10-03"
親: ["iss-00008"]
authority: "accepted"
accepted_authority: "accepted ADR"
accepted_at: "2026-10-03"
accepted_by: "iwasawayuuta"
mirror_eligible: true
derived_from: ["20261003t085617z-decision-candidate-si06-capture-observation-contract.md"]
reflected_to: ["../requirement.md", "../design.md", "../plan.md", "../../../../../../../../docs/contracts/next-semantic-v3.md"]
---

# 20261003t142223z-adr SI06 未観測captureを現publication v2へ限定訂正

2026-10-03、ユーザーは「現v2への限定訂正を採用します。タスク再開して下さい」と明示しました。本ADRはその採択を固定します。旧decision candidateと原分析は採択前の履歴として保持し、過去のオプションA採択や外部助言から今回の承認を推定しません。仕様review pass、schema実装、SI-06/Issue全体の完成は別の証拠です。

## Context

正規request-bound `stage_failed`では起動/captureが未観測となり、同じruntime→run-v3→candidates-v3の両captureがnullです。現publication-v2の常時object必須は、この合法状態を表せません。計測objectの0は観測済み0であり、nullの代用品ではありません。

actual-owner probeと独立Analyze Review Findings Strictを現source/schemaへ照合して、この表現欠落を確認しました。下位ownerの変更、zero-fill、架空overflow、当該branchの除外は既存の観測/coverage契約を壊します。別のresponse保持に関する懸念は、解析結果と公開処理結果を分ける既存意味内の説明訂正です。

## Decision

現`next-publication-decision-v2` target contractへ限定訂正を加えます。`schema=code-structure-viz.next-publication-decision/v2`、version2、URNと既存outer exact refsを保持し、後継version、dual reader/write、別wireを追加しません。

- `measurements.adapter_stdout`と`adapter_stderr`は、同じcandidates-v3のcapture未観測時に限り両方nullです。観測済みは両方従来のclosed計測objectです。片側nullは禁止します。
- nullは未観測だけを表します。観測済み0、allowed=false、overflow、EOF、成功の補完にはしません。独立validatorは同じownerのcapture有無と実値を照合します。
- `public_stderr`と`selected_stdout`は引き続き実測objectです。native整数、actual bytes、configured caps、privacy、single final owner、一回のselected-copyを維持します。
- runtime-v2/run-v3/candidates-v3/Coreの契約、semantic outcome、diagnostic catalog、source/File/Module保証、hash preimagesは変更しません。自由計測の注入、再capture、再計測、cast/downgradeで埋めません。

この訂正だけが、SIの「旧v1/v2を変更しない」という維持宣言に対する明示的なpublication-v2例外です。旧publication-v1、旧admission/public/runtime-v2、既存Python/SQLAlchemy、旧KAT/原certificateは不変です。

## Options

1. **現v2の限定訂正：採択**。新final ownerが未実装の段階で、必要な未観測状態を最小の表現訂正で閉じ、既存refsを維持します。
2. 後継版への移行：今回不採択。既存v2不変を要求する外部/永続consumerが判明した場合の再判断候補です。番号/URN/切替を暗黙に決めません。
3. zero-fill、架空overflow、branch除外：不採択。未観測/0またはrequired coverageを変えるためです。

## Consequences

既存object/object recordは訂正後もvalidです。一方、旧object-only validatorは新null/null recordを拒否します。したがって「すべての旧consumerと後方互換」とは扱わず、schema/producer/validator/vectorsを同じcandidateで切り替えます。未更新の旧consumerへ新null recordを送る運用は承認しません。

repo内censusだけではrelease済みrecord、外部schema利用、永続consumerの不存在を証明できません。外部/永続consumerに既存v2不変が必要と判明したら切替を止め、同時更新または後継版移行を人間判断へ戻します。今回、外部サービスや保存済みrecordの移行は行いません。

rollbackもschema/producer/validator/vectorsを一緒に扱います。null producerだけを旧object-only schemaへ戻すmixed stateは認めません。三つ目のcapture状態、片側未観測、新wire/diagnostic、lower contract変更が必要なら局所修復を続けません。

Current R/D/Pとpublic semantic-v3の対応範囲を先に更新し、docs-only checks、通常checkpoint/push、同objectiveの記録済みSpec Review Strictを行います。有効passの後だけ、改訂briefに基づくschema/final-ownerのvertical TDDへ進みます。元SI-06 base `af6f5d33f9487a33dabf2ddfe41df85b3d8267fb`は固定します。

SI-05のexact `6d52ff7949d64e747235eef870631cd8cc29b273`の原passは当時のsource/schema/scopeの証拠として残します。訂正後のcapture契約の証明には流用せず、新candidateのschema/owner/negative vectorsと必須checks/fresh累積Code Reviewで当該範囲だけをsupersedeします。別ASSET policy、reader prefix、production、全A02/A03/Finalは今回認定しません。

## References

- 採択前の[判断資料と原証拠](20261003t085617z-decision-candidate-si06-capture-observation-contract.md)。
- [Requirement](../requirement.md)、[Design](../design.md)、[Plan](../plan.md)のCurrent SI-06節。
- [public semantic-v3](../../../../../../../../docs/contracts/next-semantic-v3.md)のouter publication契約。
- この採択は[owner-closed公開ADR](20261002t041350z-adr-issue8-owner-closed-file-module-publication.md)を取り消さず、capture表現だけを補足します。
