---
種別: disc
ID: "20261002t052906z-disc"
タイトル: "SI03 owner bindingの最初のTDD checkpoint"
状態: "final"
作成者: "iwasawayuuta"
最終更新: "2026-10-02"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["20261002t051850z--si03-source-inventory.md", "20261002t044942z-disc-owner-closed-spec-review-pass.md"]
reflected_to: []
---

# 20261002t052906z-disc SI03 owner bindingの最初のTDD checkpoint

SI-03の最初のowner-binding TDDだけのcheckpointです。SI-03全体の完了やCore/public admissionは認定しません。

## Inputs

- [新Strict実装ブリーフ](20261002t051850z--si03-source-inventory.md)は同じclean/pushed `ce0edaa8fe63e79523fe7ad1dcb4b0a39dc02dce`のGitHub実装を分析したadvisoryです。802行すべてを読み、親owner/取得経路/旧schemaと照合しました。
- Oracle `issue8-si03-source-inventory-brief`、conversation `6abf39d9-bdc0-83ee-96f7-79bde716eb7f`、元handle79366 terminal exit0（17m20s）。requested GPT-5.6 Sol/Extra Highはnativeの両picker verified=trueです。implementer targetは人間指定GPT-6.1 Sol/Maxであり、実actor設定の証明ではありません。
- 新しい三reference/testファイルだけで実装を開始。旧v1/v2のcode/schema/KAT、production、依存は変えていません。

## Synthesis

- `.2.0`のretained bytesからadapter identityを取得し、同じproduction `SourceAcquisitionSeal` / request-v2 / transport candidateに結合できました。旧`.1.0` KATは不変です。
- 最初のfocused Redはfactory未実装の意図したassertion failure一件（collection errorではない）、Greenは一件pass。型不正・別seal・同version別assets・直接生成・readonlyの拒否も確認しましたが、既存guardの確認を新しいRed実績には数えません。
- 同じrequestのProject/File getterは親canonical metadataから生成し、Fileの`content_base64`を除きます。全source discovery、Module eligibility、partition、projection、refs、counts/hashはこのcheckpoint時点では未完了です。

## Options and trade-offs

- 既存nominal owner/transport検証だけを再利用し、旧Core validator全体は使いません。source seam成功をfull roots/causal/locality/target/budgetの認証と混同しないためです。
- ブリーフの直接`git commit -m`等はadvisoryで、実行には明示path `git add --` / `commit-codex -a` / normal pushのユーザー規則を優先します。旧test-only seal同名型ではなくproduction owner型を使用しています。

## Reflection

- SI-03元baseは`ce0edaa8fe63e79523fe7ad1dcb4b0a39dc02dce`のまま、全単位の修復を含むStrict reviewまで維持します。最初の小さなGreenだけで次のSI-04へ移行しません。
- 65件のaffected regressionはformat前にpass。その後のhandle59244はcontinuation時に参照不能、process確認で実行中pytestなし、exit未取得です。passと表記せず、最終変更後に必要regressionを実行します。
- Current PlanのSI-03開始条件に従った実装着手証拠です。仕様変更はありません。全A02、累積A03、production、Final、Issue #8は未完了。新ASSET policyは未採択です。
