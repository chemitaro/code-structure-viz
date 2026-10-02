---
種別: ADR（Architecture Decision Record）
ID: "20261002t001435z-adr"
タイトル: "Issue8 取得inventoryとsafe semantic subsetの所有権分離"
状態: "accepted"
作成者: "iwasawayuuta"
最終更新: "2026-10-02"
親: ["iss-00008"]
authority: "accepted"
accepted_authority: "accepted ADR"
accepted_at: "2026-10-02"
accepted_by: "iwasawayuuta"
mirror_eligible: true
derived_from: ["20261001t212340z-decision-candidate-a02-file-source-inventory-taint.md", "20261002t001435z-01--source-inventory-authoring-result.md"]
reflected_to: ["../requirement.md", "../design.md", "../plan.md"]
---

# 20261002t001435z-adr Issue8 取得inventoryとsafe semantic subsetの所有権分離

2026-10-02、ユーザーが取得inventoryとsafe semantic subsetを分離する推奨案を採択し、先に要件・設計・計画を修正/チェックしてから実装再開するよう指示しました。採択の記録であり、仕様レビューpass・実装完成の証拠ではありません。

## Context

旧Core-v2は全request Fileをmodelへ要求します。一方、parse/read file rootは同じFile自身をmandatory taint seedに含め、safe modelはtainted recordを公開できません。診断encodeでは解消できず、model correspondenceとproof所有権の整合が必要です。再現と採択前候補は旧Artifactへ保存済みで、後からacceptedへ書き換えません。

## Decision

全取得Project/Fileは同じcomplete source seal/親requestだけが所有します。公開modelは、full inventoryに対するmandatory roots/causal/taint/target/exportとsource graph localityを独立検証したsafe subsetです。File自身をtaintから除く例外は作りません。

proofのProject/File rowは`record`keyを省略し、親がrequestからcanonical metadataを再構成します。自由payloadとliteral nullは拒否します。全取得Fileはsafe/failed/excludedへ完全に分割し、safe Fileを任意に消せません。公開Projectは同じID/configとsafe `file_ids`を持ち、取得Projectの全membershipとは別viewです。全File除外でもProjectを空membershipで保持します。

新admission profile `next-source-inventory-safe-subset-v1`とpublic/Core-v3で意味を区別し、旧v1/v2 record/schema/KATを変更しません。private transport-v2と不変entity/ID/trusted/Unicode leafをshape/algorithmとして再利用し、旧certificateへcastしません。具体的な版/ref/preimage/予算はCurrent Designと新三契約文書に固定します。planned producer headerは0.2.0で旧0.1.0のcorpusと区別します。

## Options

1. **採択**: 完全取得inventoryと公開safe subsetの所有権を分離し、両保証を維持する。
2. 不採択: file-rootを後回しにするだけでは矛盾が残り、Issue完了を認定できない。
3. 不採択: File metadataをtaint例外にする案は公開safe recordの意味を変え、今回の分離判断とは異なる。

## Consequences

Projectの二view、proof-only source resolution、count/budget、public summary/hash/compatibilityとexact refsを一つのclosureへ整合します。仕様をfresh独立Spec Review Strictで確認してからreference TDDを再開し、全A02/累積A03後にproductionへ進みます。

通常reader I/Oとintegrity fatal、selection-only semantic exclusion、A runtime/static-only/macOS/Linux、privacy/single-owner、旧Python/SQLAlchemy bytesは維持します。未採択ASSET failure policyとseal前prefixのpartial-safe採用は含みません。新しいchild metadata authority、File seed例外、Project自体のtaint/除外が必要なら、このADRの暗黙拡張ではなく再判断します。

## References

- 採択前候補: `20261001t212340z-decision-candidate-a02-file-source-inventory-taint.md`。
- exact f8d5c41へのGPT-5.6 Sol/Pro Strict設計相談: `20261002t001435z-01--source-inventory-authoring-result.md`。独立reviewではない。
- 助言の補正・検証: `20261002t001451z-disc-source-inventory-specification-adjudication.md`。
- 正本: Current Requirement SI要件、Design SI / new contract docs、Plan SI単位。
