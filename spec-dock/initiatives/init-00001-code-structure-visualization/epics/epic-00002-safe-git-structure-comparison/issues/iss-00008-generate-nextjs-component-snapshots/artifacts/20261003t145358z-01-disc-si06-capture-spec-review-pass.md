---
種別: disc
ID: "20261003t145358z-01-disc"
タイトル: "SI-06 現publication-v2 capture限定訂正の仕様再レビュー通過"
状態: "completed"
作成者: "iwasawayuuta"
最終更新: "2026-10-04"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["20261003t145358z--si06-capture-correction-result.json", "20261003t150340z--si06-capture-correction-oracle.log.gz", "20261003t145930z--si06-capture-correction-lineage.json"]
reflected_to: ["../plan.md", "../report.md"]
---

# 20261003t145358z-01-disc SI-06 現publication-v2 capture限定訂正の仕様再レビュー通過

ユーザーが採択した現publication-v2 capture限定訂正について、先行仕様gateの結果を記録します。これは新しい設計判断や実装認定ではありません。

## Inputs

- 正本はCurrent Requirement/Design/Plan、source inventory・owner-closed・capture限定訂正の三accepted ADR、admission/public/compatibility-v3契約、補助CONTEXTです。
- reviewed full SHA: `26d3ce1e9f68a25ca60e0f55827bd539d952e56f`、repository `chemitaro/code-structure-viz`、branch `iss-00008-generate-nextjs-component-snapshots`。clean/pushedの同候補で依頼し、reviewerはGitHub connectorからfull branch tipとの完全一致を報告しました。connector検証はprompt-enforcedで、wrapperから独立した機械的attestationは提供されません。
- 同objective/記録済みreviewerへのSpec Review Strict followupです。親session `issue8-source-inventory-spec-review`、今回native `issue8-si06-capture-spec-review`、同じconversation `6abefcca-0874-83ee-8647-5b0518e3106d`、元unified exec `59720`。author/analyst会話と分離した既存reviewer lineageを保持しました。
- 元controllerは2026-10-03T14:51:30Zにexit0、native status completed、所要540359 ms。無出力中も元sessionで静かに待ち、再送・UI進捗監視・別モデルfallbackはしていません。
- [原JSON](20261003t145358z--si06-capture-correction-result.json)は3882 bytes、SHA-256 `877f21c23f9c0074399ddfa2f94d8455280a9b49483d3987e19208016e17dfb7`。[元logのlossless gzip](20261003t150340z--si06-capture-correction-oracle.log.gz)は圧縮SHA-256 `5515f0994c6b6b8a96e858f794143e58582edc774ded7494aa4d297a25e957dd`、展開後7797 bytes／SHA-256 `701ac7d658ba96e5be7043a85f911d138b47b8e7c677262b5e2f8e2782805abe`。SpecDock generic importでbyte-preserved保存し、genericの`committed`はartifact publication状態でありGit commit済みという意味ではありません。
- [同reviewer lineage](20261003t145930z--si06-capture-correction-lineage.json)はSHA-256 `8b945a847834e5c570663701d6facd82a08238353a0fb53baf30b707df62bb92`。対象十文書、元base、native/exec identity、実pickerの観測限界と原hashを保持します。
- `.gitignore`の既存`*.log`により最初のraw-log importはGit管理外です。lineage内の`log_artifact`はそのlocal publication時のsnapshotを指します。GitHubへ渡す同じ原bytesの実体は上のgzipで、ignore変更やforce-addは行いません。

## Synthesis

- 原JSON全体を読み、一つのJSON object・duplicate keyなし・installed `chatgpt-spec-review-strict/references/output-schema.json`適合を独立検証しました。`review_status=pass`、findings0、confidence0.91。P0/P1だけでなくP2/P3も報告なしです。
- paired-null未観測とobject/object実測0、片側null/zero-fill/別owner拒否、public stderr/selected stdoutのnonnull、semantic unavailableとpublication failureの独立軸、response保持、selectedコピーと後続stderrの優先関係を確認したpassです。旧object-only consumerへの影響、coordinated切替/rollback、未知の外部・永続consumerの不変要求が判明した場合の再判断も評価されています。
- 要求modelは`gpt-5.6-sol`、推論は`pro`です。followupのmodel pickerはinherited/skipped/verified=false/source=configで、新しいモデル検証ではありません。Pro pickerだけはalready-selected/verified=true/strictFailClosed=trueと観測しました。backend model identityはattestedではありません。
- native `promptSubmitted=true`、DOM fingerprint `9cacfc8292a3ccbaf97a6ffb55deee2ac6d554d367d95fd154de7e4e49c56332`。保存済みnative promptのraw SHA `0adbbf4bcd36cb6d051cad12fb9a94902e7a8de398e3b7237d50de8bd695f219`とは別の値です。Oracleのfingerprintは`JSON [messageId, DOM text]`をhashするので、raw prompt SHAとの一致を判定条件にしません。native transcriptのPrompt/Answerは保存options/原JSONへtrim一致を確認しました。DOM fingerprintの独立再計算は未実施です。

## Options and trade-offs

- このpassによりSI-01/02再訪の仕様gateを閉じ、改訂SI-06 briefとvertical TDDへ進めます。物理publication-v2 schemaのcapture二fieldはまだobject必須で、実装で修復する既知差分です。reviewerはtestsを実行していません。
- 外部・永続consumerの利用実態は未調査です。不存在、無条件送信、保存済みrecordの移行許可を認定していません。
- 元SI-06累積review base `af6f5d33f9487a33dabf2ddfe41df85b3d8267fb`を維持します。旧SI-05 certificateは元SHAの歴史的範囲のままで、訂正後schema/final ownerの証明に使いません。

## Reflection

- Plan/Reportに仕様gate通過と次の未完了gateだけを薄く反映しました。accepted scope、URN/exact refs、lower owner、予算、privacy、ASSET未採択は変更していません。
- 次は改訂実行可能brief、正規stage-failure/candidatesからのpaired-null schema Red→Green、diagnostic/stderr/final single ownerです。その後同候補のrequired checksと元af6fからのfresh Code Review Strictを要します。
- SI-06コード認定、全A02/A03、reader prefix、実TypeScript/OS/CLI/package、production、Final Quality Gate、Issue #8完了の証拠ではありません。
- 証拠checkpointのdirect checksは、原JSON/schema validation、四generic importsのbytes／gzip roundtrip／公開リンク、Current pointer別selection1 passed（0.16s）、SpecDock sync/validate10 nodes、diff-checkです。既にpassしたdocs-only schema133/静的解析はcode/schema不変のため再実行・新コードのpass扱いをしません。
