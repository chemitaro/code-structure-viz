---
種別: disc
ID: "20261003t025644z-disc"
タイトル: "SI-05 公開v3契約とexact-ref closureの実装候補・検証境界"
状態: "implemented-candidate-review-pending"
作成者: "iwasawayuuta"
最終更新: "2026-10-03"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["20261003t015026z-02-disc-si05-public-exact-refs-brief-adoption.md", "20261003t010147z-03-disc-si04-cumulative-core-review-pass.md"]
reflected_to: ["../plan.md", "../report.md"]
---

# 20261003t025644z-disc SI-05 公開v3契約とexact-ref closureの実装候補・検証境界

## 結論と認定範囲

オプションAの採択済みCurrent R/D/P・二ADRに沿うSI-05のreference候補です。元unit baseは`2efb54c370ac05ac4da0d9b0bfe717a13b62380c`で固定し、SI-04はexact d6bbbcfの認定だけを継承します。SI-05のfresh累積Strict Code Reviewは未実施で、production・全A02/A03・Final Quality Gate v2・Issue全体は未完了です。

実装範囲は十physical schemaとpublic semantic/JSON/PlantUML/provenance/run/candidatesのnominal reference owner・独立validatorです。`src/**`、dependencies、旧schema/KAT/goldens、既存algorithmの意味は変更しません。fixtureのbudget/formats/selector引数追加は同じactual source seal/requestを生成するためで、既存default corpusは不変です。外部authorの原回答と独立probe・採否は前掲Artifactへ保存しました。

## 十schemaとowner chain

```text
same retained runtime-v2 + SI-04 Core-v3
  -> compatibility-v3 / public semantic-v3 / semantic-v3 dispatcher
  -> same-Core JSON + PlantUML immutable candidate bytes
  -> provenance-v3 (17 slots, observation-v3 wrappers)
  -> request-bound run-v3 (five categories, 14-key fingerprint)
  -> publication-candidates-v3 (requested formats, actual capture)
  -> outer schema-only: domain-v2 / publication-v2 / root-v2 / stdout-v2
```

六つのv3 schemaはv2の必要な新generationを追加し、whole Next-v1/v2 certificateへfallbackしません。versionless descriptorとsource/config/entity/ID等の変えないleafのみ既存exact refを再利用します。四つのouter-v2は完全なclosed siblingで、既存selector/status/diagnostic/descriptorの意味を維持します。

- domain-v2は必須`schema=code-structure-viz.next-domain-manifest/v2`を持ち、compatibility-v3/run-v3/publication-v2とtrusted environment-v2 descriptorへ接続します。Core未観測のrun指紋はnullを許します。
- publication-v2は旧final decision shapeを維持し、run-v3と必須`candidates`のcandidate-v3 exact refへ接続します。
- root-v2はdomain-v2/run-v3/publication-v2、Next semantic-v3を宣言し、Python/SQLAlchemy semantic-v1の枝は維持します。旧root-v1 producer/golden bytesは変更しません。new root-v2へのliteral再包はbranch shape検証であり、旧producerのnew root出力を主張しません。
- stdout-v2はpublication-v2 exact refと既存closed selector unionを維持します。TARGET専用のfailure rowsをSOURCE/rejection/runtimeのgeneric unavailableへ付けません。

outerのliteral final metadataにはshape-only仮seal値を明示します。実run/Core/candidate入力を使用しますが、final copy・stderr encoding・seal再導出・tree間same-owner joinsの実装証明ではありません。これらはSI-06。request-independent reader prefixと新ASSET policyはSI-07以降または人間判断です。

## 実count、hashとfail-closed

公開summaryはexact七keys、全nested objectもclosedです。同じ取得Project/File/actual sealed bytes、safe model、full discovery/dispositionからproducerが投影し、validatorはrequest/sealed bytes/proof/modelからpartitionと実countを独立再導出します。safe membershipで取得requestを書き換えません。

- first corpus: acquired `1/6/246`、safe `1/6`、records `17/17/0/17`、entities `3/1/4`。partition `c543f59be0403f3bcf1cf13510f065f6a7e152e555aa394a42960d02a31d6d9f`。
- compatibility十key: `ecf055ae84276a9209e8cb65addabd0cbf4d882e0b76f54cc6f06208fa95880f`。schema/self ID/public countsをpreimageへ足しません。
- 別ASCII十四key KAT: `0e7bdc459bf01e9b42e4f416e565c8636b6a5dffde226aeca7beb4deee7207f0`。旧十三区分fixture不変。実first corpusのrun hashとこの別literalを混同しません。
- complete-empty、safe nonprogram Files、selection-only complete、全File proof-only partial-safe、二Projectの片方空membershipを区別します。
- available/validated Core unavailableだけがcompatibilityを保持。Core rejectionは14-key fingerprintと実control prefixを残しsemantic suffixを未観測にし、runtime-only failureはfingerprintもnullです。
- TARGET/SOURCE/EXPORT unavailableはentity実測null。entity-budget unavailableはactual4/limit3を保持。model-record rejectionは実10,001/10,000を保持します。
- 元runtimeのstage/codeを維持。EXPORTは`response_validation`、entity limitは`model_validation`、SOURCE-003は`source_read`です。

JSONはCJ15とLF一つ、PlantUMLは既存grammar validatorで同じsafe Coreへ照合します。requested formatsをselectorで減らしません。返却treeの変更、同内容の別owner、metadata cacheを正しく再hashした偽count/hash/capture/artifact、float/bool/closed-key/privacy/downgradeを検証します。JSON Schema shape/refの通過をnative owner validationへ昇格しません。

## TDDとcontrolsの実証

すべて元sessionのlogs/exitをWorkbenchへ保存しました。new seamの意図したRedと、既存Greenの保護controls、fixture/command失敗を分けます。

| 境界 | Red | 同selection Green |
| --- | --- | --- |
| public summary | 67680: 1 failed 0.82s、actual Core成立後のmissing API | 99918: 1 passed 1.68s |
| dispatcher | 98897: 1 failed 1.73s | 52448: 1 passed 2.17s |
| paired artifacts | 65307: 1 failed 1.66s | 78027: 1 passed 3.62s |
| provenance17 | 48903: 1 failed 1.59s | 70696: 1 passed 3.44s |
| run14 | 71996: 1 failed 1.59s | 8875: 1 passed 8.53s |
| SOURCE unavailable | 23290: 2 failed 5.57s | 68408: 2 passed 16.47s |
| TARGET unavailable | 19515: 1 failed 3.19s | 12209: exit0 |
| Core rejection / actual10001 | 48138: 2 failed 74.40s | 32595: 2 passed 258.92s、large除外なし |
| requested candidates | 91720: 1 failed 7.31s | 14391: 1 passed 16.40s |
| runtime-only failure | 66182: 10 failed 6.52s | 68189: 10 passed 15.59s |
| export/entity unavailable | 31883: 2 failed 7.62s | 33937: 2 passed 16.63s |
| offline schema/ref closure | fixed registry欠落→outer physical schema欠落を確認 | first outer schema closure 1 passed、全ten URN/ref resolve |

最初のruntime Greenでfixture `group_stop=not_started`が既存schemaへ違反したため、元7334の1 failed/9 passedを保持し、現物の`not_required`へ訂正しました。public controlsの初回はmembership key誤り、literal234 bytes、failed-file sortを訂正し、元51581で7 passed12.78s。outer vectorsは実response frame APIの名前とtrusted descriptor fragmentを訂正し、元6983で11 passed18.44s。run cache/foreign/partial controlsは6749で8 passed/18 deselected76.55s。

owner controlsの元81965は28 passed/1 failed284.50sです。失敗はreversed formatsというfixture入力が保持しているv1 canonical orderへ違反したもので、guardを変更せず、正規orderのpositiveとreversed-input negativeへ分離しました。元49958で4 passed/10 deselected50.83s、後述aggregateでも通過しました。controlsをnew Redとして数えず、selectionを合算しません。

元aggregate6766は248 passed/5 failed895.20sでした。新stdout fixtureが既存枝で禁止された`incomplete_kind`と既存enumにない`unsupported_kind`/`tainted`を与えていました。旧/new schemaとguardを変えず、kind無し・正規`unsupported_export`/`selected_taint`へ訂正し、kind追加を拒否する保護も確認しました。同じstdout selectionは5 passed/14 deselected0.18sです。これはfixture訂正で、schemaの新Redや仕様変更ではありません。

## チェックポイント前の検証結果

同じ未コミット候補を元serial job81335で検証し、before/afterのbranch・HEAD・tracked/untracked候補全file SHA-256一致を確認しました。元base/HEADは2efb54cです。commandの共通prefixは`uv run --locked --group dev`、各logの元exitは0です。大きな実測例を除外するoptionはありません。

| pytest selection | 結果 / 元log SHA-256 |
| --- | --- |
| 新public/artifact/provenance/run/candidates-v3、`test_next_public_family_v3_schemas.py`、`test_json_schemas.py`全件 `-q` | 253 passed829.10s。`53ce82bafd943f23f362bfc2a23b0233c7f9115931c62c363ff7f28b164bb018` |
| `test_next_source_inventory_v3.py test_next_semantic_core_v3.py -q` | 282 passed466.44s。実10000/10001、500/501含む。`0e62c90f3fa13efe090f827d5c513cfcdd3d0b5b791d5d850d0430f250ed21dd` |
| 旧public semantic/artifact/PlantUML/provenance/run/candidates-v2の六module `-q` | 350 passed1715.89s。実large cases含む。`7c8566dd9db4872d0afd0984b79d29f24adb7089b93006eb8e87d7fcfdf62eae` |
| `test_python_goldens.py test_sqlalchemy_goldens.py -q` | 16 passed5.24s。expectedを更新せず既存bytes維持。`1524003c084908ca87c8b5bc0af3b3bf6b965a94c96fb67840176d00a372789c` |
| `test_next_contracts.py::test_round23_rg_18_current_schema_and_history_contract_are_explicit -q` | 1 passed0.14s。`09229b326b028651d725fa47cd1bae9fd8e0145ff8779bdb84ae2762c00ab737` |

Workbenchの`evidence/si05-focused-gates.json`はcommand argv、開始/終了、exit、log hashと候補全file hashを保持します。上記は重なるselectionを含むため合算しません。チェックポイント前の全Ruff/check、format/check（249 files）、mypy（207 sources）もexit0です。clean checkpointに対するall-contract/full pytestと独立レビューはまだ未実施です。

## Consumer censusの分類

採用brief §27と同じ式で`schemas tests docs`を検査しました。元2efbの`git grep`は331 matches、未stageの新fileも含む後段`rg -n`は459（schemas164/tests254/docs41）です。後者を使う理由は未stageの新physical schemas/validatorsを落とさないためです。元log SHA-256はbefore `f9cabeb2bc1173443bf443cd44ca4fdb9ebedc43fecd959cb8f63a1ab81ad7f7`、after `0e22839732a5e6bcbf37b46f7d086bc23780be57d5c24a1b76d2e8342dd9da9a`です。

- new exact refs: 十new schemas、new public/provenance/run/candidates validators、fixed offline registry、new exact-ref/downgrade vectors。全recursive refsはoffline解決し、旧whole Next certificateへfallbackしません。
- unchanged leaf refs: new semanticのv1 entity/source/request/coverage等のfragmentsと、artifact validatorの二箇所の`next-publication-decision-v1#/$defs/artifact_descriptor`。descriptor shape再利用であり旧publication ownerを受理しません。
- legacy regression only: 旧v1/v2 schemas、old validators/tests/vectors、下位runtime-v2のprivate wire/leaf。旧schema/referenceの意味を改変せず、新public laneのowner証明として使いません。generic semantic-v1はPython/SQLAlchemy限定branchです。
- retained baseline/historical docs: 旧Next契約とCLIのplanned Next-v1説明はCurrent R/D/P SI・accepted二ADRによる版置換対象の履歴です。current CLIのPython/SQLAlchemy、shared leaf/algorithmの正本まで捨てません。三v3 docsは新laneのstatusを記録します。
- unexpected stale consumer: SI-05 new laneのinspectionで0件。reader prefix/final owner/productionの移植完了を主張する値ではありません。all-A02/A03前の全consumer censusは別gateです。

## 未認定ゲートと引継ぎ

SI-05全selection、source/Core regressions、old-v2/public regressions、old domain bytes、all-contract/full pytest、Ruff/format/mypy、SpecDock、Current pointers、consumer census、diffの必須gateとfresh cumulative Code Reviewを同じfinal candidateへ揃えます。original baseは固定し、先にscope-isolated checkpointをcommit/non-force pushしてexact SHAを確認します。stepレビューは独立fresh GPT-5.6 Sol/Extra High、semantic findingは別GPT-5.6 Sol/Pro分析後に応答。P2/P3はreport-onlyで自動修復・backlog・再review条件にしません。

サブエージェント・UI progress monitoring・新policy・production・Issue完了の主張はありません。Luna Max workflowは既存unit/TDD/Strict/Final順序の参照であり、caller-visible GPT-6.1 Sol/Maxを選択または認証したという意味ではありません。
