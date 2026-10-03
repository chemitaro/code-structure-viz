---
種別: disc
ID: "20261003t001847z-02-disc"
タイトル: "SI-04 locality累積レビュー指摘分析とP1限定修復"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-10-03"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["20261002t152812z-disc"]
reflected_to: ["plan.md", "report.md"]
---

# 20261003t001847z-02-disc SI-04 locality累積レビュー指摘分析とP1限定修復

オプションAのCurrent R/D/Pとaccepted ADRの意味を変えず、SI-04累積レビューのP1を限定修復しました。これは**参照実装の修正候補と判断記録**であり、SI-04の認定ではありません。修正後checkpointのexact HEADで全必須ローカルチェックを実行し、元unit baseからfresh独立レビューがpassするまでSI-05へ進みません。Issue全体・productionは未完了です。

## Inputs

- 正本: [Current Requirement](../requirement.md)、[Current Design](../design.md)、[Current Plan](../plan.md)、[admission-v3](../../../../../../../../docs/contracts/next-semantic-admission-v3.md)のSI-P01 / SI-N14。仕様認証bcae954、SI-03認証23072c2、元SI-04 base `caf38329826ae34f8e3cb330b83b97e0357b7dc5`を維持します。
- [修復前のfull Core候補・受入対応](20261002t152812z-disc-si04-full-core-acceptance.md)。当時のローカル101件等のpassは58864bf修復前の履歴で、新候補の回帰結果ではありません。
- [初回累積Code Review原JSON](20261003t001846z--si04-full-core-58864bf.result.json): exact `58864bf0223e35c6cf31ca09b0d9040954e3d9cc`、caf3832からの四commit累積range、元exec84957 terminal10、`review_status=fail`、P1一件/P2一件。native session `issue8-si04-full-core-58864bf`、conversation `6ac03f58-17e8-83e8-b469-0c0b5010d7b6`。GPT-5.6 Sol / Extra Highの両picker verified=true。reviewer自身はtestsを実行していません。
- 独立した指摘分析の[原bytes・lossless gzip](20261003t002926z--si04-locality-result.md.gz)と[可読Markdown](20261003t001846z-01--si04-locality-result.md): same exact58864bf、元exec51481 terminal0、native session `issue8-si04-locality-analysis`、conversation `6ac045ed-5ad4-83ee-93d3-5a70bf2edd9e`。GPT-5.6 Sol / Proの両picker verified=true。全409行を読み、11必須H1と順序を検証し、現物へ照合しました。可読版だけ四行の末尾spaceを除き、解凍原bytes一致と別digestを記録します。回答内の`attachments-bundle`表記は変更せず、正本や閲覧可能な引用へ書き換えません。
- 分析identity `issue8-si04-source-locality-findings`はcandidate SHAと分離します。採択scope/authorityが不変の追加分析は同じ専用analystへfollowupし、元reviewer/authorの会話を分析役に転用しません。caller所有lineageはignored Workbenchに保存済みです。
- [clean58864bfでの読取専用probe](20261003t001847z--si04-locality-58864bf-probe.py)、[四観測の原出力](20261003t001847z-01--si04-locality-58864bf-probe.log)。実source bytesを取得・sealし、retained assets/request/candidate/public Core factoryを使います。semantic/compilerは参照fixtureであり、実TypeScriptの実行ではありません。

| 原bytes | SHA-256 |
| --- | --- |
| review JSON | `040560ee8ee23fe3ee420dbfbb6cdf61f1afebd2d089d2bdbc27ca068f71ecb2` |
| 専用分析回答 | `46382e591ee67c7d326f44cb35b78860b95dd87e7d102ffcf08c098a87440c99` |
| 分析原bytes gzip | `02fbe3c1f8a28c21290e6cb20ebd901abb3dcc4fd397d67debd8a22ca375bc6f` |
| 分析可読版（四行の末尾spaceだけ除去） | `3b63e54f3b5c05e4dd4e3e2bb7867d2d27b35c0158d8b0a69eaee677b07dc531` |
| probe Python | `5cb7b8c55a237393b7640af9fd55468fe58dffc0ae47d4a39c7e0556159c5347` |
| probe出力 | `4ef98460bae37766a7798876a140323abdab3a244da6d5a7c22c0edb6ca688d0` |

## Synthesis

### P1の原因と判定

source-native `R1`（分析group `RG-SI04-01`）はin-scopeで到達可能な実装不具合です。first fault layerはv3のpost-acquisition locality判定で、Requirement/Design/accepted ADRの欠落ではありません。

障害対象`src/value.ts`をcontext Fileの`src/global.d.ts`がimportすると、同じsealのresolved graphの逆方向closureには両Fileが入ります。修復前はModuleを持つpathしか検査せず、非programのcontext Fileは検査から漏れました。一方、合法なrecord taint/partition規則ではそのcontextへ偽の逆taintやModuleを追加できず、公開Fileに残ります。結果として「障害の影響範囲に残っている公開File」を独立なsafe subsetと誤判定しました。

元probe67676はterminal0でしたが、これは現象を確認するため誤挙動の成立をassertした観測で、受入テストのpassでもRedでもありません。

| 同じ取得済みsourceの条件 | parse_file / read_file両方の修復前観測 |
| --- | --- |
| contextがvalueをimportしない | reverse closureはvalueのみ。contextは公開に残り、`localized=true / partial_safe`。これは維持する正例。 |
| contextがvalueをresolved importする | reverse closureはcontextとvalue。contextはuntainted/publicのまま、誤って`localized=true / partial_safe`。独立decision validatorも誤判定を受理。 |

### 最小修復と不変条件

`tests/contracts/next_semantic_core_v3_validation.py::derive_post_acquisition_locality_v3`に、**全rootから累積した逆closureと同じcandidateの実際の公開File pathの交差**を追加しました。交差が残れば既存のlocality failureとして扱い、既存SOURCE-003 / unavailable / no-artifact経路へ閉じます。formatter後のhelper差分は7追加/1置換行です。

- Fileのeligibilityと実際の公開集合を区別し、full request/source inventoryを公開集合の代用にしません。
- File taint、Module、source graph、partition、Project membership、targets、実counts、exportsを修復のために捏造・変更しません。
- 出力field/diagnostic/state/ownerを増やしません。通常SI-03 seam factory、native acquisition/seal、旧codec/algorithm/runtime/schema/依存/goldensは不変です。
- old whole `SourceFailureLedger`へnative sealを偽ownerとして渡しません。保持対象は意味であり、旧owner certificateの流用ではありません。
- 新predicateはP1の公開残存だけを閉じます。通常open-edge predicateはtextually unchangedで、下記P2を同時修復していません。

### P2と証拠の限界

source-native `R2`（分析group `RG-SI04-02`）のseverityは**P2のまま**です。通常open edgeをforward/reverseのunionで評価する現在のpredicateが旧ledger意味より保守的であることはsource比較で裏付けられます。ただしreverse-only importerのopen edgeと独立safe targetを同時に使うfull Core compoundの新実行証拠はこの分析batchでは提出していません。この限界を保ったまま、PlanのP2/P3 report-only規則に従い報告対象とします。P1へ昇格せず、自動修復・新受入義務・別backlog・review loopを作りません。

## Options and trade-offs

| 処置 | 判断と理由 |
| --- | --- |
| 同じpublic File projectionとの残存交差でSOURCE-003へ閉じる | 採用。既存のsource localityを保つ一意のbounded implementation-remediation。既存仕様の意味変更や人間の新判断は不要。 |
| contextへ偽Module/逆taintを追加する、partitionから任意に落とす | 不採用。owner-closed/source inventoryの採択済み規則を破り、別の偽証明を作る。 |
| P2も同時に修復する | 今回は行わない。独立groupかつP2で、親の実装権限・必須gateを広げる理由にならない。 |

### TDDと保護チェック

実際のpublic seamは`decide_semantic_candidate_v3`のimmutable decisionです。自作classのmockやfake graph/seal/candidate/Moduleは使用せず、期待値はliteralで固定しました。

| phase / 元job | 実行結果 |
| --- | --- |
| first Red /1116 | 新`cannot_publish_a_context_file_in_the_reverse_failure_closure`のparse/read二例: **2 failed /101 deselected、1.69s、exit1**。resolved graph、合法なcontext、public factory成立後に`localized=True is False`で失敗。fixture/collectionエラーではない。 |
| minimum Green /54612 | 同じ二例: **2 passed /101 deselected、2.02s、exit0**。SOURCE-003/no-payload/no-artifact、context partition/Module不変、独立decision再検証を確認。 |
| 保護selection /29976 | 新六例と既存isolated parse/read・module_plane: **9 passed /98 deselected、7.88s、exit0**。追加controlはすでにGreenで、追加Red cycleと称しない。 |
| focused statics | 二変更ファイルのRuff check、format-check、diff-checkはpass。初回format-checkの書式二件は通常formatterで整え、semantic guardを弱めない。 |

保護例は、forward-only contextならpartial-safe、二hopの逆context importerならunavailable、複数rootでまだ公開contextが残ればunavailable、context自体が正当なdirect read rootでproof-onlyなら独立safe側を保持する条件です。元Redは新predicateを省くと症状が戻ることの証拠で、破壊的Git rollbackやunsafe互換modeは作りません。

実行コマンド（full aggregateとは別selection）:

```text
uv run --locked --group dev pytest tests/contracts/test_next_semantic_core_v3.py -q -k cannot_publish_a_context_file_in_the_reverse_failure_closure
uv run --locked --group dev pytest tests/contracts/test_next_semantic_core_v3.py -q -k 'cannot_publish_a_context_file_in_the_reverse_failure_closure or context_safety_depends_on_reverse_not_forward_reachability or multiple_roots_use_the_actual_public_file_projection or keeps_localized_acquired_file_failure_partial_safe or rejects_partial_publication_when_failed_source_has_open_dependency'
uv run --locked --group dev ruff check tests/contracts/next_semantic_core_v3_validation.py tests/contracts/test_next_semantic_core_v3.py
uv run --locked --group dev ruff format --check tests/contracts/next_semantic_core_v3_validation.py tests/contracts/test_next_semantic_core_v3.py
```

元TDD/controlログとtest-only初稿diff digestはignored Workbenchの`evidence/si04-locality-p1-*`に保持します。上記二selectionを合算してcoverageとはしません。

## Reflection

- Plan/Reportへはレビューfail、P1-only修復、P2 report-only、次の必須gateという**進捗だけ**を反映します。Requirement/Design/accepted ADRの意味や元unit baseを変更しません。
- 修正後のcheckpoint exact HEADで、全Core（現在107例）、旧五module、共有algorithm16selector、schema/goldens、全Ruff/format/mypy、SpecDock、Current pointerを元processの終了結果付きで検証します。実10000/10001等のlarge casesを除外しません。現時点では未実施です。
- 元base `caf38329826ae34f8e3cb330b83b97e0357b7dc5..fixed-head`に対する**fresh独立ChatGPT Code Review Strict / Sol / Extra High**が必要です。58864bfからのrepair diffだけを認証しません。旧reviewer/analyst回答を新criteriaやreview inputへ転用しません。
- 分析skillの利用記録: Code Review Strictは全unitの欠陥検出、Analyze Review Findings Strictはbatch全体のgroup化・first fault layer・現行authority・bounded処置の判定を担いました。後者は実装の許可そのものではなく、原助言をprimaryのsource/probe/TDDへ照合して採用しました。通常Use Strictとの同一課題A/B比較は行っておらず、「どちらが優れる」とは認定しません。原回答保存・11 H1検証は成功し、今回の機械的出力欠落はありません。
- SI-04 step pass、SI-05以降、全A02/A03、actual TypeScript/OS/CLI/publication/package、Final、Issue完了はまだ認定していません。
