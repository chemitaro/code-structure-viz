---
種別: ADR（Architecture Decision Record）
ID: "20261004t033836z-adr"
タイトル: "SI06 root指紋の現v2訂正と最小設定由来保持"
状態: "accepted"
作成者: "iwasawayuuta"
最終更新: "2026-10-04"
親: ["iss-00008"]
authority: "accepted"
accepted_authority: "accepted ADR"
accepted_at: "2026-10-04"
accepted_by: "iwasawayuuta"
mirror_eligible: true
derived_from: ["20261003t195656z-decision-candidate-si06-root-fingerprint-and-config-origin.md"]
reflected_to: ["../requirement.md", "../design.md", "../plan.md", "../../../../../../../../docs/contracts/next-semantic-v3.md"]
---

# 20261004t033836z-adr SI06 root指紋の現v2訂正と最小設定由来保持

2026-10-04、ユーザーは直前の推奨A案を「推奨案を採用します」と明示採択し、目的を達成する最小限のシンプルな実装を求めました。本ADRはroot指紋の現v2限定訂正を採択します。先行capture訂正の承認を遡及拡張せず、今回の判断として記録します。

## Context

matching transport/Coreを持たない正規failureでは、run-v3のsemantic指紋はnullです。domain-v2は表現できますが、root-v2の必須string制約とは両立しません。rootの新final ownerは未実装で、GitHubのRelease/tagは0件、mainにもroot-v2はありませんでした。外部利用者の不存在までは証明していません。

親の設定値はanalysis contextから取得できますが、設定を選んだ由来は全七項目について保持されていません。旧goldenのbuiltin固定をactual ownerへ流用すると虚偽の由来になります。

## Decision

1. 現`run-manifest-v2`のNext snapshot枝だけで、root `run.fingerprint`を同じrun-v3のsemantic指紋へ一致させます。matching transport/Core無しはnull、matching Core（rejectionを含む）ありは既存十四key digestです。通常のfailure全般をnullにしません。公開処理の失敗もこの値を変更しません。
2. 同じdomainの`run_fingerprint`とroot値を一致させます。指紋null時の`next_request`/domain requestは`run_fingerprint` fieldを省略します。非null時は同じ値です。request object自体は既存request-bound意味を維持します。
3. 新version/URN、別指紋field、failure専用hash、generic request hashへのfallback、移行frameworkを追加しません。旧root-v1、Python/SQLAlchemy枝と既存hash preimages/KATは維持します。
4. final ownerに不足する設定の由来だけを、親の設定選択時に値と組でimmutableに保持し、同じanalysis contextへ結びます。既存の値を再解決せず、最小の補助入力を既存final owner/validatorへ接続します。receiptの具体的責務と検証はpublic semantic-v3のroot節を正本にします。lower runtime/Core/run/candidatesのpublic契約・hashは変更しません。
5. 仕様修正と同objectiveのSpec Review Strict passを先に行い、元SI-06累積baseを維持してTDDとコードレビューを続けます。

## Options

- A（採択）：開発中の現v2のNext枝を必要なnull表現に訂正します。新しい意味の指紋や版routingを増やさず、正規failureを表現できます。
- B（今回不採択）：新root世代。現v2の不変提供義務が実在すると判明した場合の再判断候補です。
- generic指紋への分離、failure hash、ゼロdigest、failure manifest抑止は採択しません。

## Consequences

既存nonnull recordは有効なままです。新null recordは旧nonnull consumerには渡せないため、同じ候補でschema/producer/validator/vectorsを切り替えます。外部/永続consumerのv2不変義務が判明した場合は新recordの提供を止め、同時更新または新世代を再判断します。外部保存物の移行/backfillは今回実装しません。

rollbackでは新Next公開を止め、旧recordと他domainを保持します。nullを旧形式用のdummy digestへ変換しません。新しいownerや抽象化は必要なjoinに限定し、既存7項目を扱うための汎用設定frameworkや新公開schemaを作りません。

本採択は旧schema維持宣言へのroot-v2 Next枝の追加例外です。capture訂正、A runtime、source inventory/owner-closed公開は維持します。request-independent prefix、ASSET policy、製品CLI/OS/TypeScript、全A02/A03/Finalの未完了gateを省略しません。今回のadoptionは実装passではありません。

## References

- [判断候補と原分析・公開状況](20261003t195656z-decision-candidate-si06-root-fingerprint-and-config-origin.md)
- [Requirement](../requirement.md)、[Design](../design.md)、[Plan](../plan.md)
- [public semantic-v3](../../../../../../../../docs/contracts/next-semantic-v3.md)
