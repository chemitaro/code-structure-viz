---
種別: disc
ID: "20261001t150558z-disc"
タイトル: "A公開semantic bytes v2契約スライス"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-10-02"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["../requirement.md", "../design.md", "../plan.md"]
reflected_to: ["../plan.md", "../report.md"]
---

# 20261001t150558z-disc A公開semantic bytes v2契約スライス

これはA02-3のreference-only契約スライスの実装・検証記録です。新しいProduct/Security判断、独立レビューpass、実TS/CLIまたはfilesystem公開の認定ではありません。

## Inputs

- unit base: `700d0dfa2de38bdfcdfde6a7151756b0bfa6c7a2`、branch `iss-00008-generate-nextjs-component-snapshots`。実装前のclean local/upstreamを照合しました。
- 正本はR/D/P `Current normative authority`とaccepted A ADR。既存source/semantic/canonical bytes/descriptorの意味を変えず、single-owner seamへ限定します。
- この単位は具体的な正本と現物symbolからexecutable briefを機械的に抽出しました。追加の外部分析は実施しておらず、過去Pro advisoryを本単位の独立certificateとして扱いません。
- caller-reported implementation actor GPT-6.1 Sol / Max、backend未検証。Luna workflowの順序を参照しただけでモデル変更はしていません。サブエージェント無し。
- `docs/contracts/next-semantic-v2.md`、`next_public_artifact_v2_reference.py`、`next_public_artifact_v2_validation.py`、`test_next_public_artifact_v2.py`が具体的な契約・実装・検証面です。

## Synthesis

- 入力はavailable nominal `ValidatedSemanticDecisionV2`一つ。公開recordをcanonical UTF-8/key-sort/compact/pinned NFC JSON＋LF一つへserializeし、same decisionとimmutable bytesを保持します。caller bytes/status/descriptorを受け付けません。
- 固定path/domain/format/media_typeとactual candidate bytesのlen/hashを六field descriptorへ導出します。fresh getter、閉じたconstructor、opaque reprを使い、元source diskを再readしません。
- 独立validatorはproducerを呼ばず、保持bytesをpublic2 schema/Core ownerへ照合し、canonical bytesとdescriptorを再計算します。v1 publication schemaはversionless descriptor fragmentだけを再利用し、旧full record/runtimeへのfallbackを作りません。
- 正常に自己hashされたnoncanonical bytesや別source/request/coverageでも不一致を拒否します。完全に同じpublic bytesを持つ別Core objectへのrebindも拒否します。
- complete-emptyにもactual source/request/Core proofが必要です。export不明のunavailable decisionから空の成功bytesを生成しません。

## TDDと独立known vector

- formal RED: selected test bodyの新reference module importで`ModuleNotFoundError`、1 failed。collection errorではありません。
- 最小producer/nominal owner/独立validatorを追加し、同じselectionが1 passed（1.36s）。後続hardeningは既にGREENのguardsと区別します。
- 初回hardeningは23 passed / 3 failed（28.53s）。fixture親directoryの作成漏れ、実fixtureの`repo/` path忘れ、未許可target grammarが原因でした。directory/pathを正し、既存valid unknown-export Core fixtureを使いました。ガード・public failure意味は変更していません。
- focused26 passed（30.57s）。owner/immutability/complete-empty/unavailable/source保持、rehashed noncanonical8 cases、foreign record3 cases、descriptor8 casesを含みます。
- 独立`jq -cS . tests/fixtures/next_runtime_v2/public-semantic.json | wc -c`は9472 bytes、同bytesの`shasum -a 256`は`545389abfa3975b2c95083db9cca6b8efbe071c4526b90cbe55fe9bdc84b5957`。期待bytesをproducerから生成せず、既存固定literalをtest-side ASCII codecで照合しました。
- 旧full record KAT `d9cd6519...`はLF無し、新candidate KATはLF込みです。別preimageを旧hash identityへ上書きしていません。

## 検証

- `uv run --group dev pytest -q tests/contracts/test_next_public_artifact_v2.py`: exit0、26 passed（30.57s）。
- `uv run --group dev ruff check .`: exit0。
- `uv run --group dev ruff format --check .`: exit0、212 files already formatted。
- `uv run --group dev mypy src tests`: exit0、176 source files。
- `uv run --group dev pytest -q tests/contracts/test_next_public_artifact_v2.py tests/contracts/test_next_public_semantic_v2.py tests/contracts/test_next_analysis_context_v2.py tests/contracts/test_next_semantic_candidate_v2.py tests/contracts/test_json_schemas.py`: original exec13488 exit0、243 passed（145.36s）。focusedと重複するため合算しません。
- `uv run --group dev pytest -q tests/contracts/test_next_contracts.py::test_round23_rg_18_current_schema_and_history_contract_are_explicit`: exit0、1 passed（0.17s）。
- SpecDock fresh help確認後、`sync --no-github --no-update-active` / `validate`がexit0、nodes=10。active pointerを更新していません。`git diff --check`もpass。
- baseに対する`src`、`pyproject.toml`、`uv.lock`、schemas全体、旧semantic doc、旧巨大reference validatorのdiffは空です。
- 全pytest/全contracts-securityの再実行は本スライスでは行いません。基点700d0dfのbounded1316は保存済みですが、変更後candidateの全gateへ流用せず、whole-A02 gateで改めて実施します。
- ここまでの確定結果はpre-commitのin-scope working treeへ結びます。checkpoint hashとclean/upstream/full-SHA equalityはcommit/push後のWorkbench記録へ残し、未実施の認定を追加しません。

## Options and trade-offs

- 今回のcanonical候補の保持は、後段finalizerが同じbytesを再renderせず受け取るための前段seamです。旧巨大publication ownerを複製せず、必要なbytes/descriptor joinsだけを小さいmoduleへ限定しました。
- descriptorはcandidate属性で、persisted Artifactの存在を証明しません。selection/transaction/final publicationやstdout availability/exitを単独ownerへ追加してgateを先取りしません。
- 新ASSET failure政策は未採択のままです。catalog/message/stage/outcomeに反映していません。

## Reflection

- Plan A02-3のlimited progress、Reportの実測結果、public2 contract docへ反映しました。Requirement/Designの意味は変更しません。
- reader-owned early prefix、新asset policy、PlantUML/run/publication/domain/root/stdout exact refsとterminal matrix、全A02 gate、A03独立Strict、A04実製品、A05両OS/offline package/Finalは残ります。
- A03 cumulative fixed pointは`f4159066f3954454ad2f0c2701fa54bf1bc7bc4a`から最終clean/pushed candidateへ固定したままです。途中checkpointでwhole A02完了やreview passを自己認定しません。
