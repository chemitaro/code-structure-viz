---
種別: disc
ID: "20260923t221959z-disc"
タイトル: "Issue #8 Strict Review P1 Type-Flow Remediation"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-09-23"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: []
reflected_to: []
---

# Issue #8 Strict Review P1 Type-Flow Remediation

## 要旨

今回の障害は依存パッケージの欠落ではない。以前のStrict分析で特定した本来のIssue #8 blocker（production OS backendでの実行ファイルFD同一性・同一inode検証の受入証拠不足）とも別件である。今回の直接のP1原因は、contract validator内で異なるnullabilityを持つ2つの値に同じローカル名を再利用したため、必須の strict mypy gate が失敗したことである。

GPT-5.6 Pro相当（GPT-5.6 Sol、Pro reasoning）の独立Strictレビュー指摘分析は、このP1を実在・再現可能・ブロッキングと裁定し、request-bound側の値だけを `sealed_source_view` と命名する局所修正を推奨した。推奨どおり変更し、対象型ゲートと回帰テスト、全体テスト、静的解析、offline build、SpecDock validationが成功した。修正後のGit commit、push、GitHub Actions、同一レビュアーによる新SHAの再レビューはこの記録作成時点では未実施であり、完了条件として残る。

このArtifactは分析と実装証拠であり、Requirement／Design／Planを変更・置換するものではない。Issue #8全体の完了、production readiness、未解決のbackend受入証拠を閉じるものでもない。

## 統合した証拠

### 既存のIssue #8 blockerとの区別

- 以前のStrict分析 sessions `required-strict-github-connector-verificati-1083`, `-1084`, `-1086` は、依存ライブラリの欠落ではなく、production OS process backendが検証済み実行ファイルFDから実行イメージを特定し、実行中も同一inodeであることを保証した証拠がない点を本来のproduction blockerとして識別した。
- 同じ先行作業では、mixed-workspace publicationで完全なsource plan/digestを保持し、公開対象だけをapplicable rootsへ射影するvalidator修正を行った。該当コードはcommit `946653238a776a55ac301f8d357343e145dd7efb` に含まれる。
- そのcommitに対する新しいP1は、本来のproduction backend blockerやpackage dependencyとは異なる、テスト／reference-validatorの静的型検査不具合である。両方の論点を混同しない。

### Strict code review と独立分析

- Repository / branch: `chemitaro/code-structure-viz` / `iss-00008-generate-nextjs-component-snapshots`
- Strict code-review対象SHA: `946653238a776a55ac301f8d357343e145dd7efb`
- 元のStrict code-review session: `required-strict-github-connector-verificati-1088`。結果は `review_status=fail`、P1は1件。
- 指摘: `[P1] source_view の再利用で最小環境の型検査が失敗する`。
- レビューtranscript SHA-256: `b60585e0f4a4b83c6ae769b078c70ee54a9d2c9b567c933341d259ba91c612db`
- 独立したStrict指摘分析 session: `required-strict-github-connector-verificati-1089`。fresh initial lineage、GPT-5.6 Sol / Pro。対象branch tipの完全SHA一致をGitHub connectorで確認してから分析した。
- 分析transcript SHA-256: `a10d50372bbfafcbfae1ceded3346e698a244990611830acd7955028d2232475`
- 分析output log SHA-256: `1a999ebc6bc8556e69ae1f73b9e521b794a8c9c9e6a84cf442847c2c368f4239`
- 完全なレビュー指摘分析packet SHA-256: `60501801993571b1cc1ec45a1b03322101ec3b2eac783039677d8cd53263ae26`。session artifactsとpacketはこの実行環境の `.oracle` / `/private/tmp` に保存されている。主要裁定と根拠はこのArtifactにも記録する。

### 根本原因と影響

`tests/contracts/next_reference_validation.py` の `validate_domain_manifest` 内で、先行するrequest-independent branchは非Optionalの `dict[str, Any]` を `source_view` に束縛する。一方、request-bound branchは `dict[str, Any] | None` の `publication_context.source_view_descriptor` を同じローカル名へ再代入していた。後続の `isinstance` assertionは代入後のnarrowingなので、代入時点のstrict mypy incompatible-assignment errorを解消できない。

同一SHA上の `uv run --locked mypy src tests` は、行10121で次のエラーを返した。

```text
Incompatible types in assignment (expression has type "dict[str, Any] | None", variable has type "dict[str, Any]") [assignment]
Found 1 error in 1 file (checked 150 source files)
```

GitHub Actions run `35924354504` / `product-test-minimum` job `107395740317` でも同じSHAで同じmypy gateが失敗し、同jobのpytestおよびoffline buildは未実行になった。CIは `mypy src tests` をpytest・offline buildより先に実行するので、これは必須minimum jobを止めるP1である。runtime/public behavior障害の証拠ではなく、required static quality gateの失敗である。

### 選択肢と決定

| 選択肢 | 評価 |
|---|---|
| request-bound descriptorを別名 `sealed_source_view` にする | 採用。意味とnullabilityの分離が名前にも表れ、先行値や契約を変更しない最小修正。 |
| 共有ローカルを最初からOptionalに広げる | 不採用。意味の異なる値を結合し、先行branchまで不要に型拡張する。 |
| `cast`、`type: ignore`、mypy strict緩和、CI対象縮小 | 不採用。根本衝突を隠すか必須品質ゲートを弱める。 |
| assertionや期待値を変更する | 不採用。validator contractを弱めるので本質的修正ではない。 |

独立分析はclassification P1を維持し、primary routeを `implementation-remediation` とした。既存authorityが局所修正を一意に定めるため、新たな人間の要件・設計判断は不要とした。

## 実施した最小修正

対象ファイルは `tests/contracts/next_reference_validation.py` の `validate_domain_manifest` のみ。request-bound側の代入、Optional判定、source辞書の4項目参照を `sealed_source_view` に分離した。

変更していないもの:

- 先行するrequest-independent `source_view` とその検証
- `assert`、比較値、分岐条件、エラー意味
- complete source plan / digest、sealed SourceView count、applicable-only public projection、domain/semantic source summary equality
- test fixture、schema、CI/mypy config、dependency/lockfile、production code、production `available` semantics
- production OS backend、verified executable identity/FD、Windows受入証拠

この修正はpackage追加・更新ではない。修正を必要とした原因と対策を区別して記録する。

## 修正後の検証

| 検証 | 結果 |
|---|---|
| `uv run --locked mypy src tests` | pass — `Success: no issues found in 150 source files` |
| focused mixed-publication regression | pass — `1 passed` |
| `uv run --locked pytest -q tests/contracts/test_next_contracts.py` | pass — `544 passed` |
| `uv run --locked pytest -q` | pass — `1708 passed, 1 skipped in 197.98s` |
| `uv run --locked ruff format --check .` | pass — `174 files already formatted` |
| `uv run --locked ruff check .` | pass — `All checks passed!` |
| `uv build --offline` | pass — sdist / wheel build成功 |
| `python3 ./spec-dock/scripts/spec-dock validate` | pass — `nodes=10` |

初回に `spec-dock validate` をPATH上のコマンドとして呼んだが、CLIがPATHに存在せず実行されなかった。その後、repository-local canonical commandで検証し成功した。これはvalidation失敗ではなくcommand discoveryの誤りである。

## 残作業と完了判定境界

- 現在の修正はworking tree上の未commit変更で、修正後の完全SHAはまだ存在しない。
- 明示stage・diff確認後に通常のローカルcommit、ブランチへの非force pushを行う。
- 修正後の同一完全SHAを対象にGitHub Actions required jobsを実行し、特にminimum jobでmypy、pytest、offline buildがすべて完了し成功することを確認する。
- 同じStrict code-review workflowへfresh再レビューを依頼し、修正SHAに対して `review_status=pass` かつP0/P1なしを得る。
- 上記が終わるまでP1 closure / required product gate passとして扱わない。
- Strict reviewerもIssue #8全体の完了へ結論を広げてはならない。production OS backend、verified executable identity / verified-FD、Windows受入の未充足は別gateとしてopenのまま保持する。
- PR作成、merge、Issue closeはこの作業に含めない。
