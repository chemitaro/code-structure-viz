---
種別: disc
ID: "20261002t102327z-disc"
タイトル: "SI-03型参照のD/M閉包分析と限定修復"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-10-02"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["20261002t100432z--si03-root-origin-review-result.json", "20261002t100433z-02--si03-type-reference-read-view.md"]
reflected_to: ["plan.md", "report.md"]
---

# 20261002t102327z-disc SI-03型参照のD/M閉包分析と限定修復

## 結論と現在の境界

`SI03-CR2-F1`はsource-native P1のまま、現物で妥当かつ到達可能と確認しました。private Propの型からDに存在しないModule、public Propの型からMに存在しないproof-only Moduleへ参照できる不具合です。仕様不足ではなく、taint依存用の旧helperを全参照閉包の列挙にも使った実装層の不一致です。

採択済みSI-N08とD/M規則の範囲で、v3-localの完全参照列挙をTDDで追加しました。Current R/D/accepted ADR、旧helper、full型validator、schema、ID、taint/causal意味、File partition/Project二viewは不変です。原SI-03 baseは`ce0edaa8fe63e79523fe7ad1dcb4b0a39dc02dce`、この修復のparentは`b2a5fb2a89aa22a25e3b56e8b6f8905158b700f2`です。

working-tree completion sweepは106 passed（73.27s）、六module回帰は412 passed（274.08s、large cases除外無し）、旧domain/Current pointerの別selectionは17 passed（6.36s）です。Ruff check/format230 files、mypy188 sourcesもpassです。fresh current Code Review passはまだありません。SI-04/full Core/public/production/Issueの完了とは扱いません。

## Inputs

- 統合する evidence:
  - [今回のraw Strict review JSON](20261002t100432z--si03-root-origin-review-result.json)。exact b2a5fb2、元range ce0edaa..b2a5fb2、native session `issue8-si03-root-origin-review` / conversation `6abf731f-0108-83ee-a449-b4bd03cbfad1`、terminal exit10/17m54s。GPT-5.6 Sol/Extra Highの両picker verified=true。raw SHA256 `c43cff734592873afc6b53df3a45e8f568fc7b28912366c6b5a7e5c290c06289`。外部reviewerはtests未実行。
  - [exact-parent probe原コード](20261002t100432z-01--si03-type-reference-probe.py) / [最終8件出力](20261002t100433z--si03-type-reference-probe-output-v3.txt)。実source seal/assets/request/transportとsynthetic proofを使用し、flat/arrayの不正4件・正常4件すべてがfactory/independent revalidationを通ることを再現しました。コードSHA `c904abdfdb3c47647831be0fa9d6b802b1347378fc457500e93241d059d26bf2`、出力SHA `6e4b044b682116eb5532e58ae81bde262f74a3893edef9bd3e4babd3dbe6da40`。actual TS/OS証明ではありません。
  - [専用analystへ渡したcomplete packet](20261002t100433z-03--si03-type-reference-packet.md)。source-native review JSON値、parent/authority、全terminal検証、先行義務、probeのschema spelling失敗とowner guard検出履歴を保持しています。
  - [analyst原回答のlossless gzip](20261002t100433z-01--si03-type-reference-original.md.gz) / [人間向けread view](20261002t100433z-02--si03-type-reference-read-view.md)。同identity `issue8-si03-source-owner-cause-adjudication`、valid parent1401への専用Strict followup1403、同conversation `6abf57a0-d838-83ee-b8ef-1c963f134acc`。terminal exit0/661460ms、1000行/11個のordered H1を全読。exact GitHub b2a5fb2 bindingを確認。
  - Requested `gpt-5.6-sol/pro`は明示。followupではmodel pickerがskip/unverifiedのためfresh model選択は主張しません。Pro pickerはalready-selected/verified=true。submitted prompt SHA `382c9ad7c233c2414e904b6d409a34b05dd868d1b80a675fd888e5cdcfc85c46`。
  - Analyst raw decoded SHA `74831d17d9eff4ac70a4d51507a5b1d1e33a14bce624a2ce6f148a149e35239b`。read view SHA `ebb120ff0cfaad785c4ad58508dedb2b29cb684d778fd9385e12f223aa3b1829`。read viewだけ行末horizontal whitespaceを正規化し、原本/旧Artifactは未変更です。
  - 先行root-origin群の限定修復/残る責任は[前回disc](20261002t084121z-disc-si03-direct-root-seed-witness-remediation.md)。RC-SI03-001はcurrent reviewで再指摘なしですが、whole-unit failのためformal SI-03 closureとは扱いません。

## Synthesis

- 一致する事実と未確定事項:
  - `RC-SI03-002`はcurrent P1とseverityなしの`CG-SI03-002`（全型参照位置/四view census）をまとめます。先行`RC-SI03-001`のroot-origin joinとは別invariantで、同じhelperへ統合しません。
  - shared `_record_references`はPropのownerだけを列挙します。新 `_record_closure_references_v3`はordinary refsを維持し、Propだけclosed PropsTypeIRを明示的に走査します。repository scopeのModule IDをD/Mへjoinし、external/trusted文字列をrecord IDとは扱いません。それらのtype arguments内のrepository参照は検査します。
  - schema/full型validatorから11 kindと15参照位置を照合しました。leafはprimitive/type_parameter/redacted_literals/opaqueで、plain literal kindはありません。scope/canonicality/depth/意味のfull認定はSI-04に残ります。
  - unknown kindを空集合にしません。arbitrary dict/list scan、shared helper変更、full `_validate_type_node`呼び出しによる責任移動は行いません。public factoryとpublic independent validatorは同じ局所導出を再実行します。

### 型位置/公開集合の完了census

| 型の位置 | 検証位置 |
| --- | --- |
| reference | root、type_arguments |
| array/tuple | element、elements.type、rest |
| function | this_type、parameters.type、return_type |
| union/intersection | members |
| object | properties.type、index_signatures.value_type |
| object call signature | this_type、parameters.type、return_type |

各15位置にpublic→public、private→D-onlyのpositive、private→D missing、public→D-onlyのnegativeを置いた60件です。さらにexternal/trustedとrepository type argumentの16件、複数/重複/後方にある参照4件、reference-free leaf4件で、計84件の追加ケースです。positiveはfactoryとindependent revalidationを実行し、negativeはfactoryのD/M別rejectionを明示確認します。旧Component参照/root-origin controlsもsweepに含めました。

正規factoryが拒否したcandidateから有効なseamを作れないため、Green後のnegative再検証用にprivate constructorやmockでseamを偽造しません。修復前のexact probeは誤admission後のindependent検証まで実行済みです。Green後のnegativeに同じ再検証実行をしたと水増ししません。

### Red→Greenとverification

governing `tdd`の一behaviorずつの順序を優先し、advisoryの全negative一括First Redを採用しません。初回flat Redはparent実装でDID NOT RAISE、type argument Redも同様です。後続kindのpositive Redは一時的なunknown-kind拒否で、実装を足して正常型を許すことを検証しました。最終60件matrixでnegativeを一緒に確認します。後続Redをexact parentでの全matrix Redとは表記しません。

| cycle | Red | 同じselectionのGreen |
| --- | --- | --- |
| flat repository | 1 DID NOT RAISE /0.69s | 1 pass |
| reference type argument | 1 DID NOT RAISE /0.91s | 1 pass /0.85s |
| array | 1 valid-positive unknown-kind failure /0.74s | 1 pass /0.76s |
| tuple element/rest | 2 failures /1.28s | 2 pass /1.40s |
| primitive/redacted/opaque leaves | 3 failures /1.74s | 3 pass /2.04s |
| function this/parameter/return | 3 failures /1.87s | 3 pass /2.18s |
| scoped type parameter | 1 failure /0.87s | 1 pass /0.74s |
| union/intersection | 2 failures /1.44s | 2 pass /1.71s |
| object property/index/call | 5 failures /3.16s | 5 pass /3.29s |

completion sweep106 pass/73.27sは重複するselected casesで、後続aggregateと足し合わせません。scope/multiple controlsは既にgreenのhardeningで、別のRed cycleを捏造しません。full pytest/all A02/A03/actual TS/OSは今回の部分unitでは実行していません。

working-treeの最終検証（すべて元jobのterminal exit0）:

- `uv run --locked --group dev pytest -q --tb=short tests/contracts/test_next_source_inventory_v3.py tests/contracts/test_next_semantic_candidate_v2.py tests/contracts/test_next_request_frame_v2.py tests/contracts/test_next_exchange_v2.py tests/contracts/test_next_trusted_environment_v2.py tests/contracts/test_json_schemas.py`: 412 passed（274.08s）。実10000/10001 records、stdin等のlarge casesを除外していません。
- `uv run --locked --group dev pytest -q --tb=short tests/contracts/test_python_goldens.py tests/contracts/test_sqlalchemy_goldens.py tests/contracts/test_next_contracts.py::test_round23_rg_18_current_schema_and_history_contract_are_explicit`: 17 passed（6.36s）。上記selectionと合算しません。文書status更新後のpointerと、commit後の同じselectionは別途確認します。
- `uv run --locked --group dev ruff check .`、`ruff format --check .`（230 files）、`mypy src tests`（188 sources）はpass。各commandは同じlocked dev環境です。checkpointの新SHAでrequired checksを再実行してからreviewへ渡します。
- Plan/Report status更新後、Current pointerの同じ単独testは1 passed（0.23s）。SpecDock `sync --no-github --no-update-active` / `validate`（10 nodes）、tracked diff-check、new discの7 local links、四raw importのbyte一致、gzip decode/raw hash、read viewの明示whitespace変換、packet内review JSON値一致を確認しました。raw import/read view/new discにtrailing whitespaceやextra EOF blankはありません。

## Options and trade-offs

- 選択肢と利点・制約:
  - 旧helperを広げる案: 旧taint/causal closureの意味が変わる可能性があるため不採用。
  - full型validatorをSI-03へ移す案: SI-04の責任/予算/意味検証を前倒しするため不採用。
  - flat/arrayだけの追加: 同じ不変条件が別位置で漏れるため不採用。
  - 採用: v3-localのexplicit closed-kind walkerとordinary refsのunion。既存SI-N08を実装し、仕様/API/互換/運用の意味を変えません。新しいProduct/Security判断は不要です。

## Reflection

- Current Requirement/Design/accepted ADRは変更不要です。Planは既存SI-03→fresh step review→SI-04のgateを維持し、Reportへ部分unitの観測結果だけを要約します。このdisc/外部回答はcanonical authorityではありません。
- 次は全required checksを閉じ、task-scoped checkpoint/normal push、exact new SHAで再検証後、元ce0edaaからfresh independent ChatGPT Code Review Strict（GPT-5.6 Sol/Extra High）です。valid current passまでSI-04へ進みません。
- shared helper、schema/ID、type semantics、責任境界、public/data/security/migration/recovery/operation変更が必要になった場合は局所修復を停止し、人間判断へ返します。
- 原analysis attempt1402はChat/Work mode判定でpre-send失敗し、valid lineageを更新しませんでした。元会話をno-recover harvestで照合し、旧completed回答/空composer/送信前stage/owner無しを確認後、一回のcontrolled同identity followup1403を実施しました。復旧に限ったCUA read-only observationを使用し、長時間jobのUI監視・二重送信・API fallback・profile/source削除はありません。operational recovery成立だけで、Oracle根因修正は主張しません。failed原logはWorkbenchに保存しています。
