---
種別: disc
ID: "20261003t163442z-disc"
タイトル: "SI-06 capture限定訂正の改訂brief採用とTDD着手"
状態: "completed"
作成者: "iwasawayuuta"
最終更新: "2026-10-04"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: []
reflected_to: []
---

# 20261003t163442z-disc SI-06 capture限定訂正の改訂brief採用とTDD着手

現v2のcapture pair限定訂正について、改訂実装ブリーフを全文確認し、採択済み仕様とローカルの実owner chainに照合した実行記録です。外部回答は実装手順のadvisoryで、要件変更やコード認定ではありません。`completed`はこの採用分析の完了だけを示します。

## Inputs

- accepted capture ADR: [現v2への限定訂正](20261003t142223z-adr-si06-capture-observation-current-v2.md)。publication-v2のidentityを維持し、adapter capture二fieldだけをpaired null/objectへ訂正します。
- specification gate: [Spec Review Strict passの証拠](20261003t145358z-01-disc-si06-capture-spec-review-pass.md)。exact `26d3ce1e9f68a25ca60e0f55827bd539d952e56f`の十文書についてvalid pass/findings0であり、後続コードの認定ではありません。
- fresh authorの固定候補: `c0a1dd2a35326f1656d87ea9a0b907f45a8b123f`。元SI-06累積Code Review baseは`af6f5d33f9487a33dabf2ddfe41df85b3d8267fb`のままです。
- [原回答1545行/45節のlossless gzip](20261003t163441z--si06-capture-brief-result.md.gz)。展開後SHA256は`e0e1262d686ae777838167208afda7bc3827ed406201f252c13151af10dde3bf`。
- [原Oracle logのlossless gzip](20261003t163441z-01--si06-capture-brief-oracle.log.gz)。展開後SHA256は`8e7c2cb7aa36f68ed87b2376f39815a3ce95d52a4823a84a153d0df74a81c788`。
- [author lineage](20261003t163441z-02--si06-capture-brief-lineage.json)と[全文確認後のローカル採用記録](20261003t163441z-03--si06-capture-brief-admission.md)。四generic importsはWorkbenchのsourceとbyte-preservedで、SpecDockのartifact publicationはGit commitとは別です。

## Synthesis

- original exec `13118`はexit0、native session `issue8-si06-capture-brief`、conversation `6ac11bcc-0b60-83e8-98c2-ab92f7bf0d44`。実行時間は`2026-10-03T15:13:41.045Z`から`15:44:41.467Z`まで31分00秒です。jobはterminalで、再送や監視用UI操作はしていません。
- authorはGPT-5.6 Sol / Extra HighをUI pickerで確認しました。backend attestationはありません。DOM fingerprintは`1e07c46de27b7595631330d97fbaea7c721cd6f973b763bb32e9d082fca127ed`で、raw promptのhashではありません。
- 依頼時のimplementer設定はGPT-6.1 Sol / Maxでした。人間の後続指定により現在のcaller-visible primaryはGPT-6 Astra / Maxです。原§43にmodel-specific capabilityへの依存がないため手順を再利用し、原回答は改変しません。Luna workflowは順序の参照で、スキルによるmodel変更・backend証明・厳密Luna実行を主張しません。
- 先行schema-only TDDは、正規stage_failed runtime2→run3→candidates3が両nullになることを確認した上で意図したRed（1 failed）→限定Green（1 passed）を実行しました。旧object/objectを含むschema familyは24 passedで、片側null二件とpublic measurement null二件を拒否しました。これはfinal ownerの証明ではありません。
- 公開診断はcatalog固定metadataと実Core/runのsource-owner参照を使用します。NODE-002の独立304-byte literal、SOURCE-003実parse/read root、TARGETの実path/reason、EXPORTの実Module、entity LIMIT-005、complete/partial_safe、typed rejectedについて各Red→Greenを実行し、new diagnostic moduleの11件が170.59秒でpassしました。独立validatorはproducerをexpected builderに呼びません。
- 最終公開ownerは通常artifact selectorの成功ケースをRed→Greenで追加しました。actual候補の同じartifact bytes、descriptor、公開診断stderrを保持する1件が33.61秒でpassしました。これは初スライスで、未観測captureのfinal projectionや他の失敗・上限・seal hardeningはまだ未認定です。

## Options and trade-offs

- 採用: 改訂briefの順序で、paired-null schema→catalog-owned diagnostics→single final publication ownerを一behaviorずつ閉じます。既存source/runtime/Core/run/candidatesのguardを維持し、fake Core、zero-fill、producer期待値による自己認定を避けます。
- 不採用: 原briefのschema変更なし/ready宣言、下位ownerへの型cast、未更新object-only consumerへのnull送信、上限縮小やartifact paddingによる境界test。これらは採択済み意味または実owner証拠と一致しません。
- 未完了: final ownerのnull/nullと実capture0/object/object、foreign owner/cache-aligned/native数値拒否、semantic/publication独立軸、actual stderr64KiB/selected16MiBのinclusive/+1、privacy/partial-write0/一回計測、全必須unit checks。同じcandidateの通常commit/push後、元af6fからfresh Code Review Strictを行うまでSI-06を認定しません。

## Reflection

- 現v2の限定訂正は既存accepted ADRとCurrent Requirement/Design/Planが正本であり、本Artifactは新たなProduct/Policy決定を追加しません。
- 先行SI-05の認定は原exact SHAの範囲で保持します。focused passをall-contract/full pytest/whole Issue/production/Final Quality Gateへ昇格しません。
- reader-prefix、未採択ASSET policy、production/OS/TypeScript/CLI/packageはこのunitに含めません。外部または永続consumerのimmutable v2要求が新たに確認されたら、契約切替を止めて人間判断へ戻します。
