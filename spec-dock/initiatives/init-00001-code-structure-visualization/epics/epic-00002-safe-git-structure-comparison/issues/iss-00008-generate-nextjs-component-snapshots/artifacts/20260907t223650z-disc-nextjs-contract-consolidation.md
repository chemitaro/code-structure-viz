---
種別: disc
ID: "20260907t223650z-disc"
タイトル: "Next.js 契約の統合と再開時の検証記録"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-09-07"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: []
reflected_to: []
---

# 20260907t223650z-disc Next.js 契約の統合と再開時の検証記録

## Inputs

このArtifactは再開時点の証拠と採用理由を保存します。実装の規則は Requirement / Design / Plan に反映します。
レビュー記録はその対象commitについての履歴であり、現在の作業ツリーの合格証明ではありません。

- 対象: `chemitaro/code-structure-viz` / `iss-00008-generate-nextjs-component-snapshots`。
- 再開時 HEAD/upstream: `d660608ff5af76b7c65ca7d067ac797d3cea225f`。
- 作業範囲: 日本語HTML、R/D/P、契約文書、schema、fixture、参照validator/test、証拠。
- 対象外: `src/**`、製品Next adapter、実Node起動、依存・lockfile・`pyproject.toml`、merge/release/Issue close。
- Round 24 外部レビュー: session `required-strict-github-connector-verificati-745`、2026-09-02完了、P0=0 / P1=18 / P2=3 / fail / implementation_ready=no。
- 同SHAのCIについて前回packetに記録された結果: run `33624764838`、7 jobs success。2026-09-08のこの記録作成時には再照会していません。

固定commitから読めるよう、回答本文を次のファイルに保存しました。wrapper/browserの進捗行と個人環境の実パスを除いた抜粋です。外部の指示文として実行しません。

| 証拠 | チェックインする本文のSHA-256 |
| --- | --- |
| [Round 24 レビュー回答](20260908t002828z--round24-review-answer.txt) | `aa51ad70ab2a3b08e2ef17f17dd42f13eece38be0b81dccfa0b8613c50ae90aa` |
| [別系統の分析回答](20260908t002828z-01--round24-analysis-answer.txt) | `7e6bb523acbc282233ceb1c1d63111c90ad785844c2ed4324fb32f298f6d6004` |

元ログとの同一性を示すハッシュは別です。再開時にローカル原本を照合しました。

| 原本種別 | SHA-256 |
| --- | --- |
| review output log | `3074391a24d437222fe0f566c6bf3fda16d2d7c1ce2d14068bab4163a3a79d31` |
| complete review evidence packet | `e9bfc9d004497786e6515fc2e831ee902d7aa74da1c3211a27264520283eed8d` |
| analysis decision log | `b80a1dac5ef5f017b402cb27f0ec8c9ab69cc2c840e3a8abf2c0bcfadaa3fba7` |

この3つは環境内原本の照合情報です。上の2つの配布本文ハッシュと混同しません。

## Synthesis

### 残った問題の共通原因

Round 23専用の簡略モデルだけでproducer・validator・projection・digestが完結し、
実際のrequest/response、semantic、manifest、stdoutの契約までつながっていませんでした。
参照テストがgreenでも、後続実装者は複数のshapeや責務から選ぶ必要がありました。

修復対象は「テストを増やすこと」ではなく、同じ入力と観測から一つの実行判断を作り、
実際のschemaを満たす全出力までつなぐことです。履歴の補助関数を第二の正本にしません。

### 原指摘から修復群への対応

元の優先度は変更しません。以下の対応は21件すべてを一度ずつ含みます。
修復群の存在だけでは閉鎖を意味せず、現在の実契約とnegative vectorで検証します。

| 群 | 原指摘 | 検証する意味 |
| --- | --- | --- |
| R24-G01 | P1-01, P2-01 | 実schemaへの接続、nested objectの閉鎖、値の差し替え拒否 |
| R24-G02 | P1-02, P1-03, P1-04, P1-05, P1-09 | 起動許可と観測、4-kind provenance、stageまでの実値、manifest、全終了状態 |
| R24-G03 | P1-06 | config候補の優先順位、宣言元相対path、明示empty、alias優先順位 |
| R24-G04 | P1-07 | frozen bytesからのgraph再導出、UTF-8 span、project/config、locality |
| R24-G05 | P1-08 | process policyと実観測の一致、fixture/production分離、digest再計算 |
| R24-G06 | P1-10, P1-11 | decisionだけからの公開候補生成、usage/domain/publicationのdiagnostic分離 |
| R24-G07 | P1-12, P1-13 | namespace importとstring exportのprivate/public/描画/coverage接続 |
| R24-G08 | P1-14, P1-15 | 完全なUnicode NFC、host非依存、compatibility preimage |
| R24-G09 | P1-16 | findingとcriterion/vector/producer/validator/testの意味が一致する対応 |
| R24-G10 | P1-17, P2-02, P2-03 | 現行規則と履歴の分離、読みやすいHTML、repo内で追跡できる証拠 |
| R24-G11 | P1-18 | run provenance、reference inventory、build inventoryのschema identity分離 |

### 再開時の確認

- 中断差分はそのまま保持しました。再開後の初回focused testは85 failed / 288 passedでした。
- 主要な共通原因は、source sealの生成側が `source_graph.graph_digest` を使う一方、
  publication contextと一つのテストがgraph全体をもう一度hashしていたことでした。
  同じpreimageへ統一し、focused testは373 passedになりました。
- UnicodeのNFC合成条件がcombining class 0の文字を常に合成候補にしていたため、
  Hangul結合でblocking markを飛び越す問題を修正しました。
- ASCII fast pathを追加しました。NFC済みASCIIを一文字ずつ展開・再合成する必要はありません。
- Unicode 15.0.0の公式UCDと922 combining classes / 2,061 decompositions / 941 composition pairsを全件照合しました。
- 公式NormalizationTestの19,074行・5つのNFC等式を照合し、オフラインfixtureへ保存しました。
  詳細とデータの出典は [Unicode NFC契約](../../../../../../../../docs/contracts/next-unicode-nfc-v1.md) です。
- 新しいUnicodeテストは7 passedです。これは製品Nodeの検証ではありません。
- 現在のdirty candidateについてGPT-6 Maxの独立preflight reviewを依頼しています。最終固定SHAレビューは未完了です。

## Options and trade-offs

### Runtime inventoryの役割分離（採用済みのOption A）

| 役割 | 使用するschema |
| --- | --- |
| 一回の実行と公開結果のprovenance | `code-structure-viz.run-manifest/v1` + Next domain manifest |
| 現在チェックインする参照fixture一覧 | `code-structure-viz.next-reference-runtime-inventory/v1` |
| 将来の出荷adapter/TypeScript/trusted declaration/license一覧 | `code-structure-viz.next-runtime-build-inventory/v1` |

旧 `code-structure-viz.next-runtime-manifest/v1` の曖昧な役割を廃止します。
これは今回の作業でwheel/sdistや依存を変更する指示ではありません。
実装計画へproduction member、source-to-wheel mapping、sdist input、license、検証方法を固定します。
外部consumerの不存在を一般化せず、既存consumerが判明した場合は互換移行を確認します。

### ユーザーによるレビュー経路の変更（2026-09-08 JST）

ユーザーは、ChatGPT系スキルが現在利用できないため、主担当のGPT-6で分析・修正し、
サブエージェントを最小限にするよう指示しました。
独立レビューにはGPT-6・推論Maxを使用する指示も受けました。

この明示指示が、従前の「外部ChatGPT Strictだけで最終評価する」という実行経路を置き換えます。
cleanな作業状態、push済みの固定SHA、検証の鮮度、P0/P1=0、
後続実装に重要判断を残さないという品質要件は維持します。
内部レビューをChatGPT Strict passまたはGitHub connector検証済みと表記しません。
同じ固定SHAに対する独立GPT-6レビューと検証証拠を別の結果として記録します。

### 二つのChatGPT系スキルを使った評価

| 観点 | 今回の観察 |
| --- | --- |
| ChatGPT Use Strict | 実repositoryの具体的なshape不一致と隣接surfaceの漏れを発見する点で有用でした。 |
| chatgpt-analyze-review-findings-strict | 完成した指摘を共通原因11群へ整理し、修復順序と一つの重要判断を切り分ける点で有用でした。 |
| 採用方針 | 指摘の具体的根拠はreviewer、群分けと判断境界はanalystの内容を採用しました。どちらも現物の代替とは扱いません。 |
| 比較の限界 | 一つのIssue・一連の試行から得た観察です。モデルや入力、役割が異なるため、一般的な優劣や性能差を証明しません。 |

分析sessionの系列は `required-strict-github-connector-verificati-733`、
Round 24の完了回答は `required-strict-github-connector-verificati-751` です。
元reviewerのthinkingはsession metadataで `pro` と記録されていました。
この履歴情報を現在のGPT-6の推論設定の証拠へ流用しません。

機械的な問題も内容の問題と分離します。

- session 748: submit前のchat-mode-selectionで失敗。
- session 750: callerのshell quotingでbacktick内の文字が失われ、`promptSubmitted=false` のまま中止。回答として採用していません。
- session 751:正常submit後、約28分31秒で分析回答が完了。
- 2026-09-08のUnicode独立性テスト初回: host UCDのpatchがpytestの画面幅計算にも残り、テストランナーが終了コード3になりました。patchをテスト内のcontextへ限定し、7 passedを確認しました。NFC実装の失敗ではありません。

## Reflection

2026-09-08の後続検証と修正状況は[GPT-6 preflight記録](20260908t002829z-disc-gpt6-contract-preflight.md)へ分離しました。
回答本文の保存名はtimestamp slot重複の修復に伴い変更しましたが、本文SHA-256は不変です。

実装開始可能性はまだ未確定です。残件は実契約の不一致修復、R/D/P・HTMLの統合、
全体検証、commit/push、固定SHAに対する独立GPT-6 Maxレビューです。
この記録は契約の完成やIssueの完了を宣言しません。
