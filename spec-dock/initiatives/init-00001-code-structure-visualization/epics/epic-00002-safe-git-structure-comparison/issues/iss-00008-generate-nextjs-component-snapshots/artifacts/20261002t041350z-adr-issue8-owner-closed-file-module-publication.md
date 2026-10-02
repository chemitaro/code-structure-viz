---
種別: ADR（Architecture Decision Record）
ID: "20261002t041350z-adr"
タイトル: "Issue8 program FileとModuleのowner-closed公開条件"
状態: "accepted"
作成者: "iwasawayuuta"
最終更新: "2026-10-02"
親: ["iss-00008"]
authority: "accepted"
accepted_authority: "accepted ADR"
accepted_at: "2026-10-02"
accepted_by: "iwasawayuuta"
mirror_eligible: true
derived_from: ["20261002t011638z-03-decision-candidate-source-inventory-file-module-publication-decision.md", "20261002t011638z--source-inventory-review-result.json", "20261002t011638z-01--source-inventory-findings-analysis-result.md"]
reflected_to: ["../requirement.md", "../design.md", "../plan.md"]
---

# 20261002t041350z-adr Issue8 program FileとModuleのowner-closed公開条件

2026-10-02、ユーザーは「オプションAを採用することにしました。オプションAで進めてください」と明示しました。本ADRは取得inventory分離ADRを補足し、新v3 targetのFile公開条件だけを更新します。レビューpass・実装完了を意味しません。元のdecision-candidateと外部回答は採択前の証拠として保持します。

## Context

関係・export・境界の導出失敗では、Moduleだけがtaintedになり、所有Fileのmetadataはuntaintedのままになる正規経路があります。旧causal規則を維持するためModule→Fileの逆taintはありません。「全untainted File公開」「tainted Module非公開」「公開program Fileに正規Module一件」は同時成立しません。独立safe targetを持つ三つのnonFile rootで旧validatorの拒否を再現しました。

## Decision

**A: owner-closed公開投影**を採択します。全取得File/Projectは同じsource seal/request/full proofに保持し、元のrecord-level taint集合を変更しません。非program Fileはsource-safeなら公開。program Fileはsource-safeで、同project/pathの正規Moduleもfull proofと既存selection/unsupported規則から独立に公開可能な場合だけ公開します。公開可能なFile/Moduleは必ず公開し、childの提出modelに存在しないことを除外の根拠にしません。

File自身のdirect parse/readは従来の`failed`、それ以外のFile自身のtaintは`excluded / tainted`です。File自身がuntaintedで、必要Moduleの失敗/taintが非公開原因なら`excluded / failed`、合法selection/unsupportedが原因なら同じ立証済み`not_selected`/`target_excluded`/`unsupported`です。原因の優先順と完全partitionはadmission-v3へ固定します。Module由来の除外をFile自身のtaint、`proof.failed`、直接読込失敗へ偽装しません。

Module discoveryの欠落/重複や不正referenceをowner-closureで隠さず、完全baseで拒否します。既存のselected cardinality限定例外は立証済みtyped target unavailable専用として維持し、available公開modelのFile→Module保証を緩めません。

変更する保証は「全untainted取得Fileを公開」から「全公開可能な取得Fileを公開」への一点です。全取得所有権/予算、元のtaint/causal、公開File→正規Module、全Project保持、source locality、安全な独立部分のpartial-safeを維持します。明示targetに必要な構造が失敗なら完全proof検証後TARGET-001 unavailable、target無しの合法failureは既存locality条件を満たしたpartial-safeです。

## Options

1. **A 採択**: 公開構造の所有関係を閉じる。問題のfault layerである公開条件だけを変え、全取得記録を失わない。
2. B 不採択: Module無しFileを公開し、利用側の一対一保証を変える。
3. C 不採択: Module→Fileの逆taintを追加し、closed causal/taintの意味を変える。
4. D 不採択: domain全体unavailableにし、無関係な安全部分の可用性を失う。

## Consequences

Current Requirement SI-REQ-002/003と正負acceptance、Design SI、admission/public/compatibility-v3、Plan SIを同じ意味へ整合します。Project公開membershipと`safe.files`、excluded File数、partition/hash/KATは実際の公開集合から導出します。全取得bytes/recordsの予算を減らしません。公開summaryに新fieldやprivate owner原因を追加しません。

v3/profile `next-source-inventory-safe-subset-v1`/producer `0.2.0`は未実装・未出荷targetのまま維持し、旧v1/v2のschema/reference/goldensを遡及変更しません。private wireの既存excluded enumを使用します。実装で新state/code/wire generationが必要と判明した場合は暗黙追加せず再判断します。A runtime/static-only/privacy/macOS/Linux、reader integrity境界、別ASSET未採択を維持します。

docs-only checksと通常commit/push後、同じreviewer `issue8-source-inventory-spec-review`へStrict followupを行います。schema-valid `review_status=pass`後だけSI-03へ進み、全A02/累積A03/production/Finalは別gateとして残します。same objectiveの修復であり新review campaignへ切り替えません。

## References

- 元のaccepted分離ADR: [取得inventoryとsafe subset](20261002t001435z-adr-issue8-source-inventory-safe-subset.md)。その取得所有権/taint規則は維持し、Fileの公開可能性は本ADRで具体化・更新します。
- 採択前判断資料: [File/Module公開条件](20261002t011638z-03-decision-candidate-source-inventory-file-module-publication-decision.md)。draftのまま履歴として保持。
- 正本: [Requirement](../requirement.md)、[Design](../design.md)、[Plan](../plan.md)のSI節と、三つのv3契約文書。
