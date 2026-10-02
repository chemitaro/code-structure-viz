---
種別: disc
ID: "20261002t143402z-01-disc"
タイトル: "SI-04 selected-cardinality実装ブリーフの採用と境界"
状態: "completed"
作成者: "iwasawayuuta"
最終更新: "2026-10-02"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["20261002t143402z--si04-target-exception.md"]
reflected_to: ["../plan.md", "../report.md"]
---

# 20261002t143402z-01-disc SI-04 selected-cardinality実装ブリーフの採用と境界

## 結論と位置付け

通常の取得source所有権とowner-closed公開を緩めず、既存selected `missing` / `component_only` / byte-identical `duplicate`だけを、完全検証後のTARGET-001/no-payload専用経路として実装するブリーフを採用します。Current R/D/P、accepted二ADR、v3契約の意味は変えません。この採用は実装方法の具体化で、仕様認証・SI-04完了・step review passではありません。

[原回答](20261002t143402z--si04-target-exception.md)は1956行 / 45378 bytes、SHA-256 `a8db83f078b0dc60db7847447c6627574a56b96b2cc3f41ad945ee366aa73ad4`。全行を読んで現物へ照合し、command-first generic importで原bytesを保持しました。verified inputは中間 `4b50c815c4875696b04df8f14a8f681ba0c52566`、元SI-04 review baseは `caf38329826ae34f8e3cb330b83b97e0357b7dc5` のままです。

authorityは[Current Plan](../plan.md)、[admission-v3](../../../../../../../../docs/contracts/next-semantic-admission-v3.md)、[source分離ADR](20261002t001435z-adr-issue8-source-inventory-safe-subset.md)、[owner-closed補足ADR](20261002t041350z-adr-issue8-owner-closed-file-module-publication.md)です。原助言はauthorityを置換しません。

## 来歴と独立性

| 項目 | 実際の証拠 |
| --- | --- |
| workflow | ChatGPT Implementation Brief Strict、同authorの直接継続 |
| 原job | exec87437、exit0、21m29s |
| native session | `issue8-si04-target-exception-brief`、親 `issue8-si04-full-core-correction` |
| conversation | `6abf39d9-bdc0-83ee-96f7-79bde716eb7f` |
| requested inputs | `gpt-5.6-sol` / Extra High、browser-only/select/attachments always |
| 今回の実picker | model inherited/skipped、verified=false。Extra High already-selected、verified=true |
| submission | promptSubmitted=true、hash `7d41cf25b3c73a3f54f3c701444739cbc59312d65a6d53a18b3e74349003ae64` |
| connector | repository/branch/expected full SHA/current full tipのexact matchを回答で明示 |
| implementer target | caller-visible GPT-6.1 Sol/Max、actor identityの独立検証ではない |

親authorの過去Sol picker検証と今回のmodel検証欠如を区別します。これはauthorの実装助言で、独立review verdictではありません。UIで進捗を監視せず原job/logだけを静かに待機し、重複送信・subagent・別モデルfallbackはありません。

## 採用する実装境界

1. same candidate/source/assetsを実identityで保持。internal validation-only viewはcertificateではなくfresh getter dataだけを使用し、fake candidate/Module/sealは作りません。
2. classificationのProjects/Filesは全取得request由来。proof-onlyの実Moduleを「missing」に誤分類せず、既存pure target helpersのdefault selectionを維持します。
3. normal `full_module_owners_v3` / `resolve_discovered_v3` / SI-03 factoryは不変。unrelated source/cardinality、exact discovery、省略source payload、ID/order、private Props、D/M refs、partition/reason/Project projection、full root/causal/typed taint、coverage/localityを例外でも検証します。
4. selected missing/component-onlyのsourceもsame-seal bytesでscan。internal source slotはModule recordとしてDへ挿入しません。owner無しexport observationとorphan Componentのexport successを捏造せず、source-only declaration tableをincoming reexport graphへ含めます。
5. identical duplicateはraw model二row、D discovery一row。検証用copyだけcollapseしraw counters/digestは別に照合。contradictory duplicate、duplicate discovery、無関係なdangling/omissionはTARGETで隠しません。
6. 例外decisionはsame owners/compatibility-v3、`source_inventory_seam=None`、両measurement null、no payload。available partition certificateをmintせず、独立validatorは同branchを再導出します。

原回答Section57のgeneric `git push origin HEAD:...` は採用しません。host/user rulesを優先し、明示path add、`commit-codex -a`、direct `git push -- origin iss-00008-generate-nextjs-component-snapshots` と正規escalationを使用します。これはmechanical correctionで、Product判断ではありません。

## 次の検証と未認定範囲

まずselected missing一behaviorのintended Red→minimum Green、続いてcomponent-only/duplicate/compound negativesを一件ずつ追加します。fixture/collection failureや既にGreenのcontrolをRedと呼びません。複数Project、unsupported frontier、budget×invalid/target優先など残acceptanceを確認し、normal全正負・実10000/+1・entity500/+1、affected regression、旧goldens、static/SpecDockを同candidateへ揃えます。

元caf3832からfresh Code Review Strict Sol/Extra High passまでSI-04は未認定です。findingは専用分析を先に行います。原回答はlocal tests未実行で、助言をtest passとして数えません。SI-05/06、全A02/SI-07、累積A03、production TS/OS/CLI/package、未採択ASSET新policy、Final/Issue全体も未完了です。
