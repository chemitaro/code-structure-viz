---
種別: disc
ID: "20260923t035054z-disc"
タイトル: "Issue #8 Pre-response Target Completeness Decision"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-09-23"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["20260923t015416z-disc"]
reflected_to: ["requirement.md", "design.md", "plan.md"]
---

# 20260923t035054z-disc Issue #8 Pre-response Target Completeness Decision

このdiscussion artifactは、レビュー指摘RC-TGT-002に関する選択と根拠を記録するevidenceです。耐久する規範はCurrent v1 Requirement / Design / Planに反映し、このArtifact単独を仕様 authorityにはしません。

## Inputs

- Issue #8 Current v1 `requirement.md`、`design.md`、`plan.md`、public schema、reference validator、contract tests。
- `artifacts/20260923t015416z-disc-issue8-i05-plan008-review-findings-adjudication-20260923.md` のRC-TGT-002 analysisとOptions and trade-offs。
- 2026-09-23のユーザー判断: 「推奨案を採用します。」これはOption A（target-resolution proofのないpre-response failureでは未評価rowを生成しない）の採択である。

## Synthesis

- validated requestが明示targetを持っていても、validated semantic responseまたはtarget-resolution proofがなければ、各targetがcompleteかfailedかを証明できない。
- target failure enumにresponse-unavailable相当の理由はなく、`CSV-NEXT-TARGET-001`は個別target解決failureの診断である。pre-response failureへ流用するとfailureの意味を誤る。
- 既存schema shapeを変えず、requested target identityはrequest/config/run identityに残し、`coverage.target_completeness`にはproof由来のrowだけを出す。
- 空配列だけではtargetless requestと未評価targetを区別しないため、明示target identity、既存pre-response status、failure diagnosticと合わせて読む。空配列はcomplete/failedを表す代用ではない。

## Options and trade-offs

- **採用: Option A — proofのないpre-response failureではtarget-completeness rowを出さない。** 既存schemaとreason enumを維持し、個別targetのsemantic failureを捏造しない。明示target identityはrequest/config/run identityに保持する。
- Option B（`not_evaluated` row variantを追加）はevaluation stateをrow単位で表せるが、schema version、consumer compatibility、migrationの設計が必要となる。
- Option C（各targetをfailedとする）はresponse全体の不成立を個別target failureに誤分類し、現行reason enumにも表現がない。

## Reflection

- 採択範囲はvalidated request後、validated semantic responseとtarget-resolution proofより前のfailureです。通常のvalidated responseではtarget-completenessは従来のproofから生成します。
- source-read observed-prefix loss（RC-OBS-001）は別の実装修正ですが、同じpre-response publication unitで回帰検証します。compiler-option parity（RC-CFG-003）はreport-onlyのまま対象外です。
- Durable wordingはRequirement I05-REQ-004/Current v1 decision 10、Design Current v1 normative authority、Plan I05-PLAN-008へ反映済みです。schema shape、reason enum、診断catalogに新しいpublic variantを追加しません。
