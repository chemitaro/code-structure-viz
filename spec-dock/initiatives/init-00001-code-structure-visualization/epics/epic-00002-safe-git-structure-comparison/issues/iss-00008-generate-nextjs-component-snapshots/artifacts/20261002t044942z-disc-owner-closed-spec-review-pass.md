---
種別: disc
ID: "20261002t044942z-disc"
タイトル: "Owner-closed A案の仕様再認証とSI-03再開境界"
状態: "final"
作成者: "iwasawayuuta"
最終更新: "2026-10-02"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["20261002t044926z--owner-closed-review-result.json", "20261002t041350z-adr-issue8-owner-closed-file-module-publication.md"]
reflected_to: ["../design.md", "../plan.md", "../report.md"]
---

# 20261002t044942z-disc Owner-closed A案の仕様再認証とSI-03再開境界

人間採択Aを反映した仕様commit `bcae9548ef515e4a7662de1ad648171622c6a437`（親`34d457f6d5706f40edf57e88fc591f14d472ad7c`）の再認証証拠です。9文書だけをcommit/pushし、src/schema/tests/依存/旧goldensは変更していません。

## Inputs

- 正本: Current Requirement/Design/PlanのSI節、取得inventory分離ADR、owner-closed補足ADR、admission/public/compatibility-v3のaccepted target。
- 同じreview identity: `iss-00008 / source-inventory-safe-subset-specification / R-D-P and required contract closure`。
- 元レビュアー: `issue8-source-inventory-spec-review`。作成会話やfindings分析とは別会話です。
- 今回のStrict followup Oracle session: `required-strict-github-connector-verificati-1400`。native metaのfollowupSessionIdは元レビュアー、conversation IDは同じ`6abefcca-0874-83ee-8647-5b0518e3106d`です。
- 実行元handle26721はterminal exit0（10m49s）。元jobだけを待機し、再送・CUA/browser監視・サブエージェントは行っていません。
- [原回答JSON](20261002t044926z--owner-closed-review-result.json)はSHA256 `390f837b60e39ce61ed1d5b5d0c020832b137f85d80bb66692fa1f4061e67b89`、Workbench原本とcmp一致。fence/preface/余分なJSON/duplicate keyなしでinstalled output-schemaへvalidateしています。

## Synthesis

`review_status=pass`、findings0、confidence0.9です。GitHub connectorでrepo/branch/full SHAを取得して完全一致を確認したというreview scopeと、選択9文書および必要baselineの全体再評価が回答に明記されています。前回P1は閉じると判定されました。

ローカルで、untainted Fileの公開条件をsource-safeとowner-closedへ分ける式、独立E_module導出とexact public equality、reason優先順、任意同時省略/偽taint拒否、typed target限定例外、Project二view、summary/count/hash、後続gateを修正commitへ照合しました。外部助言を旧codeの実装完成や全pytestの代わりにはしていません。findingsと重要な仕様coverage gapが無いため、追加のsemantic findings分析/修復は不要です。

### 実モデル設定の観測限界

毎回答turnに`--model gpt-5.6-sol --browser-thinking-time pro`を明示。native metaもdesiredModel=GPT-5.6 Sol/thinkingTime=proを保持し、promptSubmitted=true、submittedPromptHash=`ac8be7bdbe754c7219b08a4c242b2c4f88a11f7bb9dd07799e92bb4683f887e4`です。

今回のmodel pickerはfollowupのため`status=skipped / verified=false / resolvedLabel=null / source=config`です。Pro pickerは`already-selected / verified=true / strictFailClosed=true`。初回レビュアーの両picker verifiedは歴史的直接証拠ですが、今回のモデル再選択確認やバックエンド証明とは表現しません。モデル名/回答品質から推測せず、明示要求/同会話来歴/実観測を分けます。

## Local verification and limits

- 文書限定checker: 9文書/20 links、run14/compatibility10/summary7/partition3 keys、二つのaccepted ADR/RDP対応、旧src/schema/tests/依存不変。
- 既存schema meta/closed限定selection: 33 passed（0.77s）。Current schema/history doc pointerは別selectionで1 passed（0.17s）。
- Ruff checkとformat: 227 files。SpecDock sync/validate: 10 nodes。diff-check pass。
- 上記は文書checkpointの確認。新v3 schema/semantic validator、PlantUML render、全pytest、actual TypeScript/CLI/OSは未実行です。

## Reflection

SI-01/02はこのexact仕様SHAで成立しました。次はSI-03の実行可能briefを用意し、新source/proof reference seamを一behaviorずつTDDします。このpassはSI-03の開始条件だけです。

SI-03〜SI-08、新v3全schema/consumer closure、全A02、累積A03、production、Finalは未認定です。別の新ASSET policyは未採択で実装しません。Issue #8とgoalは未完了。前回a4efdc3のfail/P1と採択前candidateを歴史的証拠として保持します。
