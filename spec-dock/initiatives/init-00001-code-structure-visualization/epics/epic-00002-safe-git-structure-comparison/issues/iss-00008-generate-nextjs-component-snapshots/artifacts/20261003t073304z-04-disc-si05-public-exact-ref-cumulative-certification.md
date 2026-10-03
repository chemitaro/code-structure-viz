---
種別: disc
ID: "20261003t073304z-04-disc"
タイトル: "SI-05 public exact-ref累積認定と指摘分析"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-10-03"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["20261003t073303z--si05-public-family.result.json", "20261003t073303z-01--si05-public-family-complete-object.result.json", "20261003t073304z--si05-public-family-packet.md", "20261003t073304z-01--si05-public-family.md.gz", "20261003t073304z-02--si05-public-family.read-view.md", "20261003t073304z-03--si05-candidate-checks.md", "20261003t074057z--si05-public-family-packet.md.gz"]
reflected_to: ["../plan.md", "../report.md"]
---

# 20261003t073304z-04-disc SI-05 public exact-ref累積認定と指摘分析

## 結論と固定点

SI-05のpublic/exact-ref reference契約を、exact `6d52ff7949d64e747235eef870631cd8cc29b273`で認定しました。同じclean候補の必須ローカルチェックとfresh独立ChatGPT Code Review Strictがpassし、findingsは0件です。Issue #8、全A02/A03、productionとFinalは未完了です。

- repository: `chemitaro/code-structure-viz`
- branch: `iss-00008-generate-nextjs-component-snapshots`
- 元SI-05 unit base: `2efb54c370ac05ac4da0d9b0bfe717a13b62380c`。認定対象のdirect parentであり、途中のレビューや後続docs checkpointへ移動しません。
- 累積range: 元baseからexact6d52まで、1 commit / 38 owned paths / 13583 insertions / 9 deletions。
- コード候補は通常の`commit-codex -a`と現在upstreamへのnon-force pushで公開済み。レビュー前後のlocal HEAD / tracking upstream / live GitHub full SHAが一致し、tracked worktreeはcleanでした。
- 下記認定を記録するdocs-only checkpointは新たなコード認定ではありません。SI-06はそのclean/pushed checkpointを新unit baseにします。

## 認定対象と除外

十closed schemasの物理identityとrecursive offline exact-ref closure、および同じ実source/runtime/Core由来のpublic semantic JSON/PlantUML、artifact bytes、17-slot provenance、五run categories、publication candidatesのreference/独立validatorを認定しました。新六familyとouter四schemaを区別します。

- 新family: `next-compatibility-v3`、`next-semantic-v3`、`semantic-v3`、`next-provenance-v3`、`next-run-decision-v3`、`next-publication-candidates-v3`。
- outer: `next-domain-manifest-v2`、`next-publication-decision-v2`、`run-manifest-v2`、`stdout-result-v2`。完全なclosed/ref/literal vectorの検証だけであり、final immutable owner、selected-copy、catalog stderrの実行可能証明ではありません。
- owner-closed File/Module eligibility、取得/safe/proof-onlyの七key summary、actual counts、partition、native-number拒否、foreign owner・再hash cache・旧whole-Next certificateのdowngrade拒否、privacyを対象に含みます。
- 正規corpusの取得1 Project / 6 Files / 246 bytes、records17/17/0/17、entities3/1/4は不変。partition `c543f59be0403f3bcf1cf13510f065f6a7e152e555aa394a42960d02a31d6d9f`、十key compatibility `ecf055ae84276a9209e8cb65addabd0cbf4d882e0b76f54cc6f06208fa95880f`を独立照合しました。
- 別のstandalone ASCII十四key KATは`0e7bdc459bf01e9b42e4f416e565c8636b6a5dffde226aeca7beb4deee7207f0`。通常corpusのrun hashとは別です。旧十三key KATを上書きしていません。
- production `src`、dependencies/lock、旧schemas/KAT/goldensは変更していません。旧algorithmはwire非依存の意味だけ再利用し、旧whole certificateのcastで新gateを通していません。
- consumer censusは459 matchesをnew exact / unchanged leaf / legacy / historicalへ分類し、new laneのunexpected stale consumerは0でした。これは将来のreader/finalizer/productionの全closureではありません。

## 同じexact候補のローカル検証

元serial session48020はexit0、2026-10-03T04:26:02.460458Z〜06:19:05.648780Zでした。before/afterのfull HEAD・branch・clean status・全candidate file hashが一致し、レビュー終了後も同じsnapshotであることを再確認しました。詳細argv、時刻、実duration、log hashesは[検証メモ](20261003t073304z-03--si05-candidate-checks.md)を参照します。

| 実行コマンド | 結果 |
| --- | --- |
| `uv run --locked --group dev pytest tests/contracts -q --tb=short` | 1995 passed、exit0、pytest3472.79s |
| `uv run --locked --group dev pytest -q` | 3064 passed / 1 skipped、exit0、pytest3309.09s |
| `uv run --locked --group dev ruff check .` | pass |
| `uv run --locked --group dev ruff format --check .` | 249 files、pass |
| `uv run --locked --group dev mypy src tests` | 207 source files、pass |
| `python3 spec-dock/scripts/spec-dock validate` | nodes=10、pass |

large-case除外optionはありません。full-suiteの唯一のskipは、Darwinで既存Linux専用physical Unicode spelling testがskipされることを、同じHEADのnamed test / `-q -rs`で確認しました（1 skipped / 0.02s）。Linux実行passではなく、SI-05の件数に加算しません。

先行focused元81335はpre-commit時点のbase2efbにowned変更を載せた候補で実行しました。新family253、source/Core282、旧v2六module350、goldens16、pointer1の各selectionがpass。focused後とcommitted broad前の全file mapsはPlan/Report/candidate discの三進捗文書だけ異なり、実装/schema/test/literalのhashは全一致です。focusedを「6d52で実行」と読み替えず、重複selectionを合算しません。元aggregate6766のstdout fixture-only五失敗は既存guardを変更せず訂正し、原logを保持しています。

## 初回P1の実体照合と独立分析

[初回review原JSON](20261003t073303z--si05-public-family.result.json)はvalid fail（P1一件）として保存し、書き換え・severity変更・waiveしていません。source finding IDは`SI05-CR1-F1`です。先頭の`$schema`/titleを根拠に、run-manifest-v2のroot `$id`欠落とfamily test失敗を主張しました。

ローカルの完全objectとexact Git blobでは、正しいroot `$id`が3755行中3754行目に一つ存在します。

- blob: `0fb9af64bd1908b4a109f77fc205ef6326f753f6`
- 完全blob / worktree SHA256: `5e1e6ae6ab0e2d66459582941919c89a109990411920d7bdfe560df1b28c783a`
- direct `git show 6d52ff7949d64e747235eef870631cd8cc29b273:schemas/run-manifest-v2.schema.json | jq -e '.["$id"] == "urn:code-structure-viz:schema:run-manifest-v2"'`はtrue / exit0。
- loaderはUTF-8 `json.loads`とtype castだけで、IDを注入しません。named family testは完全parsed objectのidentity、十URNのunique性とoffline refsを検査します。同じclean6d52で再実行して1 passed / 0.33s、source/schema/test mutation無しでした。

[分析入力packet](20261003t073304z--si05-public-family-packet.md)へ元review JSONを原bytesのまま埋め込み、別analystのChatGPT Analyze Review Findings Strict / Sol / Proへ渡しました。元62768 exit0 / 450693ms、native `issue8-si05-urn-analysis`、conversation `6ac0a695-428c-83ec-a584-ea9038d5e67d`。全293行 / required11 H1を読み、exact GitHub6d52と完全objectによる独立反証を照合しました。routeは`finding-rebuttal`、groupは`SI05-RCG-01`で、code修復や新policyは不要と採用しました。

反証のためにIDの並べ替え/複製、schema/guard/test緩和は行いませんでした。初回reviewerが実際にどの観測過程で誤認したかは未確認で、connector truncation等を原因と断定しません。分析冒頭のfocused-tested SHAを6d52とまとめた表現は採用せず、上記pre-commit focusedとexact broadの区別を正本の進捗へ反映します。

## fresh累積レビューによる出口

初回failを分析だけでpassに変更せず、同じ元base / exact6d52 / 全SI-05 objectiveのfresh独立Code Review Strictを実行しました。入力は従来promptと事実を追記した補助検証メモだけで、前review/analystの結論やlocal diffをauthorityとして渡していません。

- 元session17455: exit0 / 966820ms、2026-10-03T07:21:01.170Z完了。
- native: `issue8-si05-complete-family`
- conversation: `6ac0a92b-d160-83e8-a1b9-e3ef6420e9d1`
- [原JSON](20261003t073303z-01--si05-public-family-complete-object.result.json): `review_status=pass`、findings=[]、confidence0.97。公式output-contract checkerもexit0。
- reviewerはGitHubのexact SHA、Current R/D/P、二ADR、十schemas、直接のlower owners、reference/validator/tests/互換経路を累積参照したと報告しています。重大coverage gapはありませんでした。
- reviewer自身はtests未実行。ローカルtest実行の証拠とreviewerのstatic判断を混同しません。

初回reviewは元39905 exit10 / 1349982ms、native `issue8-si05-public-family-review`、conversation `6ac09f9a-3ef8-83e8-90fc-822af6fee582`でした。初回reviewとfresh reviewはSol / Extra High、専用analystはSol / Proで、各回ともmodel/effortのUI picker verified=trueです。これはUI設定の観測であり、内部backend modelの証明ではありません。

## provenanceと再開可能な証跡

七件はCurrent `artifact import file --issue iss-00008`によるgeneric opaque importで、import直後のsourceとdestinationの`cmp`がすべて一致しました。`canonical=false`は自動採用を意味しません。raw分析はMarkdownのhard-break末尾空白を含むため、原bytesをlossless gzipとして保存し、可読版だけ六行の末尾spaces/tabsを除去しました。改行・本文・意味は変更していません。`gzip -dc | cmp`と`sed 's/[[:blank:]]*$//' | cmp`の両方がexit0です。

入力packetの最初のstaged diff-checkはEOFの余分な空行一つを検出しました。原入力bytesは追加の[lossless gzip](20261003t074057z--si05-public-family-packet.md.gz)へ保存し、既存の新規packet Markdownは可読viewとしてその末尾空行一つだけ除去しました。gzip展開のraw入力一致とread-view差分を確認し、元review JSONの埋め込みbytes・本文は変更していません。下表ではraw入力と可読viewを分けます。これは証跡の表示形式の修正で、review入力やcodeの変更ではありません。

| 証跡 | SHA256 |
| --- | --- |
| 初回review JSON | `f3d84d9db3a10865a2738ec0d2e723e6fe26556ab8fa6419337e6d0af74ee420` |
| fresh pass JSON | `3cc7d7a7d68c4de26a4347f6a5d2ec0dc1b947c7567c54a67efd6796f3a543e5` |
| 分析入力packet原bytes（gzip展開） | `160e303bb45c460d3d7b4a2464b87ade16614d8c0bb2b53fb3177a17464fc95c` |
| packet raw gzip | `a2240adab8e53bab7624bd09383abaf400b5fb0dbfd2b3ac4fe526077a8b64e7` |
| packet可読Markdown | `60a5dde53d3bd73a75327bc6532ba8e04c9d847b3339aa259280b2b03e413895` |
| [原分析gzip](20261003t073304z-01--si05-public-family.md.gz) | `e0e6d286e6c648ab68109deac03ff67aa7dd59924b277c2f8159a54eac5f2fad` |
| 展開後の原分析 | `7c4f33df82c07c790c2e278b6422743c1b303674caaa1922435fd34935f8074c` |
| [可読分析](20261003t073304z-02--si05-public-family.read-view.md) | `c743827f5e851dbeae1f6083e3a1368f805bf74029a456848527002c6ae397e0` |
| exact candidate検証メモ | `c69e55f622cfd1af3346ea1418e2143172b85544c14e75d0144ed697c2fc990b` |

WBの元Oracle logsは保持しています。first / analyst / fresh log hashesはそれぞれ`2b5864740463b8935da78fac2f992bbd279190d6cf153b5fd6cb0b9b263cc2f2`、`8100a590db64c219d9ebe2f716d6ec26f102e1f7b9509ddfd493ed69224207e8`、`cc906070082af65597fdb1dab0ae9e680dd20e94eb22775bb5a98dc27e7bc546`です。submitted prompt hashesはfirst `9e8a272cd870195dac8fa740d500752e3ad8788ceca9621caaf527638087845f`、analyst `73406d81c385a53f2db02de0fd7202bc52f4d7f41ae1412af9283a96928c26da`、fresh `c6bb816228712c9955f1b14a255cad5c293211ef75b83cb04abff4143783ebeb`。

同じobjective/authority/scopeの次の指摘分析はnative `issue8-si05-urn-analysis`をfollowupし、author/reviewerへ戻しません。SHA変更だけで分析identityをresetしません。

## skill利用の観測と限界

今回Analyze Review Findings Strictは、claimの事実性、source finding identity、primary gateと新fresh reviewの必要性を分離し、不必要なcode変更を避ける判断に役立ちました。一方、通常のChatGPT Use Strictへ同じ入力を与えた比較実験はSI-05では行っていないため、両skillの総合優劣は断定しません。分析のfocused-SHA表現はlocal履歴で補正しました。primary側の最初のH1検査がrole-document titleまで数えた誤りは、期待値をrequired11出力見出しに直して解消し、skill出力失敗として扱いません。

`luna-max-implement`はspec→mechanical brief→TDD→local checks→independent review→記録の順序のreferenceとして使用しました。primaryはユーザー指定GPT-6.1 Sol/Max設定であり、Luna実行やbackend検証を主張しません。サブエージェントとUI progress monitoringは使用していません。

## 残るgate

SI-06のdiagnostic/stderrとsingle final-owner/copy、reader-owned request-independent prefix、別の未採択ASSET failure policy、全A02/A03、actual TypeScript/OS/CLI、checkout外offline package/license、Final Quality Gate v2が残ります。旧SI-04 P2はreport-onlyのままです。本Artifactとthin Plan/Report更新は結果を記録するだけで、Requirement/Design/ADRの意味、受入条件、失敗policy、元baseを変更しません。

## 認定記録の文書チェック

このdocs-only記録候補で`pytest tests/contracts/test_json_schemas.py -q --tb=short`は133 passed / 3.94s、Current normative pointerのnamed testは1 passed / 0.13sでした。いずれも`uv run --locked --group dev`を使用しました。Ruff check、format249、mypy207、SpecDock `sync --no-github --no-update-active` / validate10、訂正後diff-checkもpassです。本Artifactの相対リンクは全実在、上記importの原bytes保存とgzip/read-view整合を確認しました。文書更新のためだけに先の全suiteを再実行しておらず、6d52のコード認定を新docs SHAへ拡張しません。
