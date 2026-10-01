---
種別: disc
ID: "20261001t045200z-disc"
タイトル: "a-execution-assets-contract-slice"
状態: "final"
作成者: "iwasawayuuta"
最終更新: "2026-10-01"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["20261001t024645z-adr-issue8-trusted-toolchain-launch-model.md", "20261001t040605z-disc-issue8-a-runtime-contract-analysis-adjudication.md"]
reflected_to: ["design.md", "plan.md", "report.md"]
---

# 20261001t045200z-disc a-execution-assets-contract-slice

採択済みAのA02-1を、execution assets content identityと保持bytesのowner joinまで具体化したdata-only証拠です。製品ランナー、実TypeScript、完全な出荷profile、A03レビューを証明しません。

## Inputs

- baseline branch `iss-00008-generate-nextjs-component-snapshots`、pre-change clean/pushed HEAD `1d2c732052b512c18d98258a90ac276c433c0504`。
- accepted ADR、A runtime closure Strict advisoryのローカルadjudication、採択済みpackage entrypoint/header規則。
- 新leaf `schemas/next-execution-assets-v1.schema.json`、`docs/contracts/next-execution-assets-v1.md`、synthetic `tests/fixtures/next_runtime_v2/execution-assets.json`。
- 小さい独立reference `tests/contracts/next_runtime_v2_reference.py`と`next_runtime_v2_validation.py`。旧20k-line validatorはimport/複製/変更していません。

## Synthesis

- portable descriptorのself hashと、ownerが保持した実bytesへのjoinを別にしました。再hashした偽metadataは自己整合していてもbyte joinで拒否します。
- descriptor、adapter header identity、staging contentは同じimmutable snapshotから導出します。caller mapping/返したdescriptorの後続改変、free version/hash、非byteからの暗黙生成を使いません。
- paths/roles/member order/unique paths/entrypoint membershipはclosed contractです。host-local fieldsは許可しません。license資材は出荷inventoryへ残し、実行content identityからだけ除きます。
- identity leafはcomplete runtime profileの認証ではありません。fixtureの`reference compiler\n`は実compilerとして起動しません。保持宣言/TS profile、request、observation、compatibilityへの残りのjoinsは後続unitで検証します。
- independent known vector: entrypoint 43 bytesのhash `a0a769eddee8f677bcabbf0b1884c32c509c8b7ebccd9f41cf3473a5f67a57b4`、synthetic compiler 19 bytesのhash `4b507a55c78e8cab287c0c8385ad7e3c72acabd93dc616d9fda9aa98883a17b6`、key-sorted/no-LF literal preimageのhash `516ab8709db31afdb0b1906a14b9aff17d8106e6827674f3b453660ec0d9c856`。期待値はreference producerで生成せず、`printf`したliteralと`shasum -a256`で固定しました。

### Red → Greenと回帰

- 実行したfocused RED: 新leaf/schema・producer seamの欠落、self digest不一致、self digestが正しいreordered/duplicate/wrong-entrypoint-role、entrypoint欠落のowner入力、再hash偽metadataとbytesの不一致、非byte入力、重複header、policyのasset ID/free version不一致。それぞれ最小修正後に同じselectionをGREENにしました。fixture欠落の初期試行はschema behaviorの証拠とせず、fixtureを用意してschema欠落の実test failureを確認しました。
- producer→policy接続testは短縮protocol `next-adapter/v2`をschemaのconstで拒否しました。参照producer/期待値をauthorityの`code-structure-viz.next-adapter/v2`へ整合してGREEN。既存schemaや旧v1を弱めて通していません。
- focused: `uv run --locked pytest -q tests/contracts/test_next_runtime_v2_contracts.py` — **60 passed**。
- 既存schema/doc-pointer含むselection: 上記suite＋`tests/contracts/test_json_schemas.py`＋`test_round23_rg_18_current_schema_and_history_contract_are_explicit` — **180 passed**（4.07s）。
- `uv run --locked ruff check src tests`、`ruff format --check src tests` — pass（155 files）。`mypy src tests` — pass（155 source files）。SpecDock validate — pass（nodes=10）。`git diff --check` — pass。
- production `src`、`pyproject.toml`、`uv.lock`、既存tracked v1 schema、旧reference validatorのdiffは空。全suite/OS/CLI/package/独立Strictはこのsliceでは再実行していません。

## Options and trade-offs

- 採用: 一回保持したbytesからportable descriptorとprivate配置用contentを導出し、metadata-onlyとbyte-boundの検証を分離する。呼び出し側が勝手にversion/hashを確定できない。
- 不採用: old v1のhash定義変更、metadata resolver後のresource再read、host stat/PID/private pathのportable ID混入、synthetic member集合からcomplete runtime availableを推論すること。
- このreferenceの入力mapping/APIはdata-only test seamです。productionでは実行Module内のretained ownerが資材/metadata/request/stagingを所有し、source sealとruntime選択から一つの実行入口へ接続する設計を維持します。

## Reflection

- DesignのA02 current closure、PlanのA02-1進捗、Reportへ反映しました。新contract docが詳細record/hash/joinの正本です。
- runtime binding/observation、private wire/compatibility、trusted/provenance/public refsのclosure後にA02 full gateへ進みます。この部分的GREENをA02完了/A03 passやproduction実装と呼びません。
