---
種別: disc
ID: "20261003t015026z-02-disc"
タイトル: "SI-05公開契約ブリーフの採用と固定値照合"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-10-03"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["20261003t010147z-03-disc"]
reflected_to: ["plan.md", "report.md"]
---

# 20261003t015026z-02-disc SI-05公開契約ブリーフの採用と固定値照合

clean/pushed着手点2efb54c370ac05ac4da0d9b0bfe717a13b62380cをSI-05の元baseに固定しました。外部ブリーフ全1728行を読み、現行仕様と実Coreへ照合して採用します。仕様の意味は変更しません。実装前の準備であり、SI-05・全A02/A03・production・Final・Issue全体のpassではありません。

## Inputs

- [Current Requirement](../requirement.md)、[Design](../design.md)、[Plan](../plan.md)とsource inventoryの二accepted ADR・三v3 leaf契約がauthorityです。
- [SI-04 exact d6bbbcf認定](20261003t010147z-03-disc-si04-cumulative-core-review-pass.md)を前提に、docs closeout checkpoint2efb54cを元baseへ固定します。
- [外部ブリーフ原文1728行](20261003t015026z--si05-public-exact-refs.md)はbyte-preservedで、主担当が全行読了しました。
- [実Coreのread-only literal probe](20261003t015026z-01--si05-first-literal-probe.py)は既存same-seal source/transport/Coreから事実だけを採取します。公開v3 producerによる期待値生成ではありません。

## Synthesis

### 外部分析の実行と限界

Implementation Brief Strictの元exec73909はexit0、21分48.883秒でした。native sessionはissue8-si05-public-exact-refs、親はissue8-si04-target-exception-brief、同author conversationは6abf39d9-bdc0-83ee-96f7-79bde716eb7fです。目的/authorityを維持するSI-03〜SI-05のauthor継続で、独立レビューではありません。回答はGitHub connector上のexact2efb54cとCurrent文書・Coreのbindingを明記しました。

要求GPT-5.6 Sol / Extra High / browser-onlyに対し、今回model pickerはinherited/skipped/verified=false、Extra Highはalready-selected/verified=trueでした。親のモデル確認を今回のfresh確認に読み替えません。promptSubmitted=true、submitted hashは6a31ad585ccb02351e12b765fde2642e6c33ac56b6c590ceff9c997f708a3926です。caller-visible実装設定GPT-6.1 Sol/Maxもskillで選択・検証したものではありません。サブエージェント・UI進捗監視・重複送信は使用していません。

| 証拠 | SHA-256 |
| --- | --- |
| 原文ブリーフ | 05af1e893e98acef0080e93bd92a206320012a5b37f47a7c430865bc9adac37e |
| 元Oracle log | f49410f54c0679e25c2d13eb23d4d4afd2228c7be8859f6e8874ce42260cf742 |
| literal probe原文 | 0c0b080066efb9df19b6c6d31d1a3d604fdc96873bda365c3d7cf6f56b1cf14b |
| literal probe実行log | 05adc6b1e3ef7b8622db710dbbdfbc30622f63fa4efd6ba60c952db3396d26ed |

### 独立照合した最初の実fixture

正しいrunpy probeはexit0です。初回の相対module指定エラーは実行方法の機械的失敗で、TDDのRedではありません。

| 値 | 実fixtureの観測 |
| --- | --- |
| request_id | 4c19dcf0e98eb6df4e58af251216f4a06764cb5edf3217f7298c00995efff122 |
| acquired projects/files/bytes | 1 / 6 / 246 |
| safe projects/files、failed/excluded files | 1 / 6、0 / 0 |
| proof discovered/published/proof-only/accounted | 17 / 17 / 0 / 17 |
| modules/components/entities | 3 / 1 / 4 |
| outcome | complete |
| source partition SHA-256 | c543f59be0403f3bcf1cf13510f065f6a7e152e555aa394a42960d02a31d6d9f |
| compatibility_id | ecf055ae84276a9209e8cb65addabd0cbf4d882e0b76f54cc6f06208fa95880f |

partitionは取得Projectの全File membershipによる手組みpreimageを標準json/hashlibで再計算し、Core seamへ一致させました。source六件は30/24/42/46/59/45 bytes、合計246です。closed source summary七key・内部十count・十key互換descriptorを新公開契約へ渡す際の独立literalです。

別の十四key ASCII KATは既存v2 preimageのadapter_version=0.2.0とsemantic_admission_profile_idだけを明示したjq -cjSの独立計算で、0e7bdc459bf01e9b42e4f416e565c8636b6a5dffde226aeca7beb4deee7207f0でした。standalone vectorであり、上の実normal fixtureのrun fingerprintではありません。旧fixtureは不変、新v3 KATは別fixtureへ作成します。

## Options and trade-offs

採用する実装具体化は既存SI-05の範囲を変更しません。

- compatibility/public/dispatcher/provenance/run/candidatesの六v3 schemasと未作成domain/publication/root/stdoutの四v2 schemasを、closed exact refs/offline registry/URN/consumer census/正負literalへ整合します。旧Next public v2へのadditive fallbackはありません。
- public v3 documentとJSON/PlantUML bytesは同じValidatedSemanticDecisionV3だけから生成し、summary実counts/partition/hashとowner identityを独立validatorで再導出します。
- 最初は実lower-owner fixture成功後の一public projection behaviorをRedにし、必要compatibility/schemaとprojector/validatorだけを最小Greenにします。ブリーフのschema先行表とpublic seam先行指示はこの順序で整合します。
- internal candidates validatorは既存value/owner/run_decision署名に沿わせても意味を変えません。説明用省略署名は新製品契約ではありません。
- 外側四schemaの契約/ref/literalはSI-05、実行可能catalog/stderr/final single publication ownerは既存PlanどおりSI-06です。未採択material wire意味が必要なら人間判断へ戻します。
- 十schema横断変更に対応する全contract/full pytest回帰はSI-05 evidenceです。全A02の残reader-prefix/ASSET判断やA03認定の代用にはしません。

SI-04のP2はreport-onlyのままです。新ASSET policy、production src/dependencies、旧schema意味/旧KAT、stderr/finalizer、未採択early prefix promotionは対象外です。HTMLを変更しないunitで外部HTML validatorを推測追加しません。既存PlantUML parserは確認し、全A02のpinned gateは後続へ残します。

## Reflection

Plan/Reportへ元base・準備完了・証明限界だけを薄く反映します。Requirement/Design/accepted ADRの意味は不変です。SI-05の必須チェックと元2efb54cからのfresh独立累積Code Review Strictが同じ候補でpassするまで次unitへ進みません。全Issueゴールはactiveです。
