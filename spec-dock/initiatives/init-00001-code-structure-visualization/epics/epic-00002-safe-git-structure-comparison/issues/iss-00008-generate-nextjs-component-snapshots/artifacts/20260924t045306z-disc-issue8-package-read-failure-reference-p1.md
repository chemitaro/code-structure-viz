---
種別: disc
ID: "20260924t045306z-disc"
タイトル: "Issue #8 package read failure reference P1 remediation"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-09-24"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: []
reflected_to: []
---

# Issue #8 package read failure reference P1 remediation

## 要旨

Issue #8 の `I05-PLAN-001-APP` 修正候補に対する exact-SHA Strict code review は、有効な P1 を一件報告した。原因はPython/npmの依存パッケージ不足でもproduction classifierでもなく、独立したcontract reference readerがsource failure kindを保持せず、indexed `package.json` のどの `SourceAcquisitionError` も `CSV-NEXT-APPLICABILITY-002/applicability` に再分類していたことだった。

GPT-5.6 Pro相当の二つのStrict分析はfindingを有効・到達可能・unit-blockingと判定し、現行current-v1 authorityに従い「reference readerがfailure kindを保持し、ordinary READだけをAPP-002に変換し、非READ failureを閉じたmatrixで検証する」ことを推奨した。推奨を実装し、productionコード・canonical Requirement/Design/Plan・dependency lockは変更していない。最初の再現テストは誤変換を確認してRed、修正後のpackage failure matrixと早期failure回帰はGreenになった。

このArtifactはレビュー分析・実装・検証の証拠であり、canonical requirement/design/planやIssue #8全体の受入を置き換えない。unitのP1 closeには修正後candidateのpush、同一SHA CI、fresh exact-SHA Strict reviewがなお必要である。

## Strict evidence lineage

- Repository / branch: `chemitaro/code-structure-viz` / `iss-00008-generate-nextjs-component-snapshots`。
- 元のStrict review対象 SHA: `29d928969e3daed8e20449db45a8be9138da7787`; fixed point `977feb02c05b908d5a25a97181138abe1ef54bd9`。
- Reviewer session: `required-strict-github-connector-verificati-1097`; fresh exact-SHA `chatgpt-code-review-strict`; UIでGPT-5.6 Sol / Extra Highを確認。schema-valid `review_status=fail`, exit `10`, P1 1件。Reviewer transcript SHA-256: `0dfcbacea1f5847bdbc5069e5301803220f92fc7d11a76431e1aa471549ef3ee`。
- Independent ChatGPT Use Strict root-cause session: `required-strict-github-connector-verificati-1098`; branch/tip SHAを前後に確認し、UIでGPT-5.6 Sol / Proを確認。Transcript SHA-256: `02ccb260cf302df5d4c72b14a13562131023d3e86e49d2de28aaedeaabaadda1`。
- Specialized Strict review-finding analysis: `required-strict-github-connector-verificati-1099`; separate fresh analyst session、UIでGPT-5.6 Sol / Proを確認。Transcript SHA-256: `ab6cc0270f631a3d467dd7b819e14ac31206c42222a4963aa4dfa2fd61da9c0b`。
- Full finding packet and complete analyst outputs are retained in ignored `.workbench/luna-max-implement/issue-8-dependency-remediation/evidence/I05-PLAN-001-package-applicability/`; hashes and exact observations are recorded in `strict-review-findings-packet-29d9289.md`.

## 根本原因と影響

Reviewer finding `[P1] referenceが非READ package failureをAPP-002へ潰す` は、`tests/contracts/next_reference_validation.py::seal_source_acquisition` のpackage applicability loopを指摘した。loopは全 `SourceAcquisitionError` をcatchし、failure kind/code/stageを検査せずAPP-002へ置き換えていた。contract fake `InstrumentedSourceReader` の `read_failures` はcode stringしか表せず、既存regressionは通常read failure一種類しか注入していない。その結果、current-v1の「ordinary READだけをAPP-002へ移し、limit/integrity/path-safety/non-regular/raced-missingは従来分類に残す」要件を独立referenceとテストが保証できなかった。

productionの `_GuardedSourceReader` は `SourceReadFailureKind` を分岐し、ordinary READ、limit、integrity、path-safety等を既に異なるoutcomeへ送る。故にこのP1は依存追加やproduction変更ではなく、独立test/reference oracleの欠落である。Strict分析はcanonical authority間のmaterial conflictや新しい人間判断を見つけず、primary routeを `test-remediation` とした。

## Authorityとの照合と公開outcome

current-v1 `requirement.md` はindexed packageの通常READをAPP-002/applicability/refなしとし、source drift、limits、unsafe path、symlink、non-regular、raced-missingには既存failure classを維持すると定める。`design.md` の `PackageApplicabilityMatrix` も同じ区別を定める。したがってspec変更は不要である。

| reference側に注入する原因 | current-v1公開outcome | path |
|---|---|---|
| ordinary READ | `CSV-NEXT-APPLICABILITY-002 / applicability` | なし |
| too large / too many files | `CSV-NEXT-LIMIT-001 / source_read` | なし |
| unsafe path / symlink / non-regular / raced missing | `CSV-NEXT-SOURCE-003 / source_read` | catalogが許可するrepository-relative path |
| integrity drift | `CSV-NEXT-SOURCE-INTEGRITY-001 / source_integrity` | なし |

LIMIT-001についてproduction readerの内部 `limits` labelと公開decision stageを混同しない。独立referenceの `DECISION_FAILURE_MATRIX` は `LIMIT-001` の公開stageを `source_read` または `stdin_encode` に限定し、diagnostic catalogはpublic path referenceを禁止する。この修正はpublic contract projectionを検証する。

## 推奨対策と実装

採用した対策:

1. 独立referenceだけに `ReferenceSourceFailureKind` の閉じた分類を設け、ordinary READ、too-large、too-many-files、unsafe path、symlink、non-regular、raced missing、integrity driftを識別する。
2. `SourceAcquisitionError` にreference側failure-kindを保持する。互換のstring-only fixtureは通常READを意味し、分類不明failureはAPP-002へ変換せずfail closedとする。
3. package loopは `ORDINARY_READ` だけをAPP-002へ投影し、その他は元のfailure code/stage/pathを保持したまま再送出する。
4. public contract testを8種のfailure matrixへ広げ、診断code/stage/path permission/exit codeと、packageだけ一度読む・後続config/sourceを読まない・sealしないことを検証する。
5. production classifier、dependency、lockfile、schema、catalog、canonical specは変更しない。

TDD evidence:

- Red: `uv run --group dev pytest -q tests/contracts/test_next_contracts.py -k package_limit_failure_is_not_reclassified_as_applicability` — 1 failed。期待したLIMIT-001/source_read/refなしに対して、実際はAPP-002/applicability/pathなしとなり、findingを再現した。
- Green: `uv run --group dev pytest -q tests/contracts/test_next_contracts.py -k 'package_read_failure_preserves_its_distinct_reference_outcome or actual_early_failure_preserves_observations_through_publication or actual_acquisition_failure_preserves_its_catalog_stage_and_code'` — 27 passed。
- Focused retest after final test shape: `uv run --group dev pytest -q tests/contracts/test_next_contracts.py -k 'package_read_failure or actual_early_failure_preserves_observations_through_publication'` — 24 passed。
- Entire Next contract module: `uv run --group dev pytest -q tests/contracts/test_next_contracts.py` — 552 passed。
- Final-shape full suite: `uv run --group dev pytest -q` — 1724 passed, 1 skipped in 251.91s.
- Final-shape Ruff format check and lint passed; `mypy src tests` passed with 150 source files; `uv build --offline` built sdist and wheel; SpecDock validation passed with `nodes=10`.

## 検証と残gate

修正差分は `tests/contracts/next_reference_validation.py` と `tests/contracts/test_next_contracts.py` に加え、このevidence Artifactのみに限定される。final-shape full suite、Ruff format check/lint、`mypy src tests`、offline wheel/sdist build、SpecDock validation (`nodes=10`) は成功した。修正後commit/push、修正SHA CI、fresh exact-SHA Strict reviewはまだ未完了である。

P1はローカル修正や全テスト通過だけでは閉じない。fresh reviewが新candidateに対し `review_status=pass` と `P0=0/P1=0` を示すまで `I05-PLAN-001-APP` は未認証のままである。`I05-PLAN-008`、runtime/package/platform gates、およびIssue #8 final certificationも未完了のまま維持する。
