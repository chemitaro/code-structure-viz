---
種別: disc
ID: "20261002t084121z-disc"
タイトル: "SI-03 root-originの宣言seed直接witness修復とStrict分析照合"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-10-02"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["20261002t072235z-disc", "20261002t082608z--si03-direct-file-original.md.gz", "20261002t082608z-01--si03-direct-file-read-view.md", "20261002t082608z-02--si03-direct-file-packet.md", "20261002t085251z--si03-direct-file-packet.md.gz"]
reflected_to: ["../plan.md", "../report.md"]
---

# 20261002t084121z-disc SI-03 root-originの宣言seed直接witness修復とStrict分析照合

SI-03の局所修復とその範囲を記録するevidenceです。新仕様、full Core proof、production、Issue完了の認定ではありません。Requirement/Designとaccepted ADRの意味は変更しません。

## Inputs

- 受入正本: [Requirement](../requirement.md)、[Design](../design.md)、[Plan](../plan.md)、[owner-closed A案のaccepted ADR](20261002t041350z-adr-issue8-owner-closed-file-module-publication.md)、`docs/contracts/next-semantic-admission-v3.md`。
- 前回の判定と修復: [072235z disc](20261002t072235z-disc-si03-root-origin-adjudication-and-remediation.md)。元unit baseは`ce0edaa8fe63e79523fe7ad1dcb4b0a39dc02dce`を維持します。
- 分析対象のclean/pushed SHA: `cd0e876410d494655b4a880543337274b9ffe948`（parent `d3cce1cb42b3c6a00d7a8d8d2b9ee4dbed2406d1`）。前回のP1再現入力を拒否した一方、Fileの直接edgeをModule経由の経路で代用できることをこのSHAで測定しました。
- [専用Strict分析の原bytes gzip](20261002t082608z--si03-direct-file-original.md.gz)、[全文可読view](20261002t082608z-01--si03-direct-file-read-view.md)、[入力packet](20261002t082608z-02--si03-direct-file-packet.md)。外部回答はadvisoryで、ローカルの正本・旧helper・テストと照合して採用範囲を限定しています。

## 外部分析の来歴と保存

同じanalysis identity `issue8-si03-source-owner-cause-adjudication`、記録済み親`issue8-si03-owner-cause-analysis`へfollowupしました。native sessionは`required-strict-github-connector-verificati-1401`、conversationは`6abf57a0-d838-83ee-b8ef-1c963f134acc`を維持しています。元実行75828はexit0、所要622903ms（10m23s）、開始07:58:28.078Z/終了08:08:51.368Zです。

- 要求: browser-only / GPT-5.6 Sol / Pro / select。model pickerはfollowup継承のためskipped・verified=falseで、初回のverified結果を今回の再選択証明には流用しません。Pro pickerはalready-selected・verified=trueでした。
- `promptSubmitted=true`、提出prompt SHA256は`e7add7571edbd3b8c14bd91e76460209fcf3078841b0f8634625a18492d5ffc8`。
- 回答890行を全文読み、必須11 H1の順序・single decision packetを確認しました。原bytes SHA256は`fe9cac54b8ce91a15a116b73de7f5fd32703f4984d835ec9791a8fcb9bf5385a`で、保存gzipを展開したbytesも一致します。
- 可読Markdownは二行の末尾spacesだけ除去しています。可読viewのSHA256は`94eac2a744fbc010359814cb59a4a31ddcf9514712e9f911f9993881dfdb2bcb`。原回答や既存のreview/probe Artifactは変更していません。
- 入力packetの原bytesは[別gzip](20261002t085251z--si03-direct-file-packet.md.gz)で保持し、展開後SHA256は`17a7094737fa39e8e7be0e3bc0e6e4fa627415a454e9bd7df6c9a8453c6fb328`です。可読packetだけ末尾の追加空行一つを除去し、通常のdiff-checkに適合させています。可読packet SHA256は`a7138a0a393d79b2ddb216b6b6571f91c53ae2b913527ae4098ddce7ac9e7d1a`。提出したWB原packetは変更しません。

## Synthesis

### source-native分類と閉鎖境界

| identity | 原分類 / 現在の扱い |
| --- | --- |
| `SI03-CR1-F1` / `RC-SI03-001` | 元`d3cce1c`のsource-native P1。declared seeds外のroot-origin targetは前回`cd0e876`のguardで局所拒否済みですが、fresh独立reviewによるgroup closureはまだ認定しません。 |
| `CG-SI03-001` | source-native未分類のmaterial coverage gap。現在SHAでも到達可能なdirect File witness不足と専用分析が判定。勝手にP1/P2等へ分類せず、SI-03出口を阻む局所不具合として修復します。 |
| `EC-SI03-001` | 旧062856z evidenceの一般的「無関係root借用拒否」主張は072235zでsupersede済み。履歴は残し、新しい限定証拠と混同しません。 |

### なぜ既存仕様内の修復か

既存canonical root規則は`tests/contracts/next_reference_validation.py`の`TAINT_ROOT_RULES`とmandatory root builderにあります。parse/readは`file_all_records`、module/export/boundaryはそれぞれ`relation_dependency` / `incoming_reexport` / `boundary_closure`です。

SI-03は提出されたrootの宣言seedと、提出されたroot-origin edgeの局所対応を確認します。既存guardが「実target ⊆ 宣言seed」を確認するのに対し、今回不足したのは「宣言seed ⊆ そのrootの直接target」とcanonical rule一致でした。File seedを宣言してもroot→Module→Fileだけなら、直接witnessを満たしません。別rootの同種witnessも代用できません。

この修復は正しいseed集合そのものの独立導出や全causal graphのexactnessを意味しません。mandatory seed導出、downstream exactness、least-fixed-point taint、source locality、target/export/selection、budget routingのfull admissionはSI-04です。shape helperが許すdownstream Module→File edgeを全体から禁止する変更も行いません。

### 変更範囲

- 新SI-03 validatorに、既存adjacency上のreverse seed inclusion（7行）とcanonical root-rule join（import＋4行）を追加。前回のroot-origin target membership guardは維持します。
- テストのnonFile正例等の四箇所にあった`identity_dependency`は、shape helper上は許可されてもmandatory root builderのcanonical規則ではありませんでした。独立literal mapに沿う正規edgeへ整合し、File taint/state/metadata/outputの期待値は変更していません。wrong-rule guardより前に同じ13件がpassしたことを確認しています。
- 公開factory、独立revalidator、full source/owner/partition/count/hashの契約を維持。shared旧helper、schema、`src`、wire/adapter/profile/ID/既存KAT、依存/lockfile、goldensを変更しません。

## TDDと直接検証

| 公開seamでのbehavior | 実行と結果 |
| --- | --- |
| parse/read File seedに直接edgeがなくModule経由だけ | `test_direct_file_seed_cannot_borrow_an_indirect_module_witness`。first Red72274: 2 failed / 77 deselected（1.38s、両方DID NOT RAISE）。7行のreverse inclusion後、同じselection Green77338: 2 passed / 77 deselected（1.33s）。 |
| 正規nonFile fixtureの同じ公開/除外結果 | wrong-rule guardを入れる前の直接検証94277: 13 passed / 66 deselected（8.11s）。fixture整合は新機能のRed→Greenとは数えません。 |
| shape上は許可されるがcanonicalでないroot-origin規則 | `test_owner_root_rejects_a_noncanonical_rule_even_when_its_shape_is_allowed`。三kindのfirst Red62626: 3 failed / 79 deselected（2.58s）。4行join後、同じselection Green17827: 3 passed / 79 deselected（2.59s）。 |
| same Fileのparse+read/same-kind二root、各File直接edge欠落 | `test_every_root_keeps_its_own_direct_file_seed_witness`の九case。正例はliteral実counts・failed reason・Project safe membership・独立revalidationを確認し、負例は各rootの欠落を拒否。追加時からgreenのhardeningで、架空のfirst Redは主張しません。 |
| 上記と元P1・正規三kindのまとめ | 元84790はexit0、23 passed / 68 deselected（13.93s）。関連selection同士は重複し、件数を合算しません。 |

実source acquisition/request/assetsを通したreference seamの証拠です。synthetic semantic responseを使っており、実TypeScript解析やOS実行の測定ではありません。

## 関連回帰と次のgate

現在treeでの六module selection64396はexit0、328 passed（210.00s）。SourceInventory/semantic-candidate/request/exchange/trusted-environment/schemaを含み、actual 10000/10001等のlarge casesを除外していません。旧Python/SQLAlchemy16 goldens＋Current pointer1の別selection55345はexit0、17 passed（7.10s）。Ruff check/format（全230 files）、mypy188 sourcesはpassです。両selectionは合算せず、全pytestを実行したとは主張しません。前checkpointのexact `cd0e876`では314 passed（211.05s）と別17 passed（7.55s）でしたが、今回の修復treeへその旧結果を流用していません。

```sh
uv run --locked --group dev pytest -q --tb=short tests/contracts/test_next_source_inventory_v3.py tests/contracts/test_next_semantic_candidate_v2.py tests/contracts/test_next_request_frame_v2.py tests/contracts/test_next_exchange_v2.py tests/contracts/test_next_trusted_environment_v2.py tests/contracts/test_json_schemas.py
uv run --locked --group dev pytest -q --tb=short tests/contracts/test_python_goldens.py tests/contracts/test_sqlalchemy_goldens.py tests/contracts/test_next_contracts.py::test_round23_rg_18_current_schema_and_history_contract_are_explicit
uv run --locked --group dev ruff check .
uv run --locked --group dev ruff format --check .
uv run --locked --group dev mypy src tests
```

SpecDock sync（`--no-github --no-update-active`）/validate10 nodes、当Artifactの9 local links、両原gzip展開後の`cmp`、回答可読viewが二行の末尾spaces除去だけ/packet可読viewが末尾追加空行除去だけであることを確認しました。通常のstaged diff-checkを通し、guardは回避しません。これらはcheckpoint前の最終code treeの検証であり、commit/push後のexact-SHA結合とfresh Code Reviewは未完了です。

## Options and trade-offs

- 採用: 提出root宣言とcanonical root-origin witnessの局所双方向join。既存仕様で一意に決まる受入内修復であり、新しい人間判断やR/Dの意味変更を必要としません。
- 不採用: root-origin seed結合を省いて間接経路/同種rootだけでcauseを認める。再現済みの誤受理を残します。
- 今回は行わない: full proof/Coreの独立導出までSI-03へ拡大する。SI-04のowner・semantic admission・全negative coverageを先取りし、局所修復の証拠境界を壊します。

## Reflection

Plan/Reportは現在の局所修復状態・残るgateだけ更新します。Requirement/Design/accepted ADRの意味はそのままです。元unit baseから新candidate全体へのfresh独立ChatGPT Code Review Strict（GPT-5.6 Sol / Extra High）でvalid passを得るまでSI-04へ進みません。旧reviewerへのfollowupや旧回答添付によるclosure誘導は行いません。全A02、累積A03、production、Final/Issue完了は未認定です。
