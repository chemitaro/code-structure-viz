---
種別: レポート（Issue）
ID: "iss-00004"
タイトル: "Generate Python Structure Snapshots"
関連GitHub: ["#4"]
最終更新: "2026-08-26"
依存: ["requirement.md", "design.md", "plan.md"]
親: ["epic-00002", "init-00001"]
---

# Result Summary

詳細: [Report Guide](../../../../../../docs/authoring/report.md)

## Outcome

Issue 4のPython構造スナップショット垂直スライスを実装した。対象は静的・read-onlyのPython AST解析、決定的なsemantic JSON / PlantUML / run-manifest、stdout / JSONL stderr、bounded outcome、atomic no-overwrite publication、Git SourceView、対象選択、secret/path redaction、offline packagingである。Git diff、SQLAlchemy、Next.js、HTMLレポート、target sourceのimport/実行は本Issueの対象外として維持した。

当初のplanned-history path（I01-PLAN-001〜006の6つの独立commit）は、実際の作業履歴としては観測されなかった。公開済みの実装・hardening履歴を保持するため、main orchestratorが履歴rewriteを行わないapproved as-built pathを採用した。これは当時の各boundaryでRED/GREENが実行されたことを事後的に主張するものではない。

実装・hardeningのas-built範囲は、`eaf29540c866249552600faaa31aaba5be7932f2`から`79fa0a64bcc206bff4ccc2087683c728f1a2c39e`までの12コミットである。各commitの観測可能な責務、Plan論理境界、検証または制約を次に明示する。`081a5d730ffd6cb7d24e9c5535c7364012154a4d`はこの範囲を保全するgovernance-only commitであり、製品実装のC1〜C6には含めない。

| 順序 | full SHA | subject | 観測可能な責務 | Plan boundary | 関連する検証・制約 |
| ---: | --- | --- | --- | --- | --- |
| 1 | `eaf29540c866249552600faaa31aaba5be7932f2` | `feat: Pythonコード構造可視化スナップショット機能を追加` | CLI/config、read-only SourceView、Python AST semantic model、JSON/PlantUML、manifest、atomic publication、stream、schema、fixture/golden、package/CIの初期垂直スライス | C1/C2/C3/C4/C5/C6 | acceptance、contract、security、packaging、determinism testを初期導入。planned-historyの単独green履歴は未観測 |
| 2 | `19d9d8f17f0aad0f2c743dcafa1d1e8bf8dcb132` | `feat: スナップショット契約と安全性を強化` | v1 schema/CLI契約、diagnostic、target/selection、SourceView境界、runtime/package制約の強化 | C1/C2/C3/C4/C5/C6 | schema、acceptance、source、security、packaging regressionを更新 |
| 3 | `2104974e1c1727c7be03ed7e08769c6cb9bc8a11` | `fix(python): 型参照解決の候補構築を統一` | 型参照候補の構築と解決をAST semantic pipelineで統一 | C3/C4 | `tests/unit/python/test_analyzer.py`、`test_type_expr.py`で候補・解決を検証 |
| 4 | `37f7a5e25a5227a8f7cbbe3a10d321f58daded03` | `fix(iss-00004): guard physical output containment` | 出力先の物理containment検証とpublication境界の防御 | C5/C6 | `tests/unit/artifacts/test_writer.py`で出力先逸脱を拒否 |
| 5 | `77fe2cfc58feae41a0f6920c193ed0eb265bf555` | `fix(iss-00004): bound unsafe input and publication races` | unsafe input、source drift、publication race、深い型式処理の境界を強化 | C2/C3/C5/C6 | failure、stdout、writer、type expressionの回帰を更新。履歴rewriteは行っていない |
| 6 | `778e9a9e58e56078572bfca7283534c26d680c5b` | `fix: 深い構造や不正な入力を診断エラーとして処理` | 深いAST/config/target入力をfail-closedの診断へ変換 | C1/C3/C6 | parser、config、analyzer、failure acceptanceで再帰・不正入力を検証 |
| 7 | `4e6af9a49121dc682cd40d853a920cf7192416f0` | `fix: 型式レンダリングと成果物パス検証の誤判定を修正` | 深い型式表現の反復レンダリング、artifact pathの誤判定修正 | C4/C5/C6 | `test_type_expr.py`、`test_writer.py`で深い表現とpath境界を検証 |
| 8 | `3d509c449f0df0922eeb210c606649f27ffc4065` | `fix(python): 型注釈の競合時も関連を保持する` | 型注釈競合時のrelation保持とsemantic/golden整合 | C3/C4 | analyzer unitとcanonical model goldenを更新。過去のRED/GREEN順序は主張しない |
| 9 | `0e8a2fa41c67d77b0f3011923d00f94f1e81fb40` | `fix: 入力サイズ制限と深いディレクトリ削除の問題を修正` | 任意長整数・glob、反復cleanup、large-inputのpublication安全性 | C1/C5/C6 | parser/config/writerの大規模入力・再帰制限下テストを追加 |
| 10 | `25fd4501c2a447b6f526785e7cb3e404610bb539` | `fix: パス衝突診断を大文字小文字単位で集約` | casefold collisionの診断代表とSourceView/ModuleIndexの整合 | C2/C3/C6 | module index/source viewのcollision regressionで一診断制約を検証 |
| 11 | `dae6084e9c5ea88c63db5f757e39f7b97bd692cc` | `fix: パス衝突とリポジトリ置換に対する安全性を強化` | source collision、repository identity、path replacement、長整数、property setterの防御 | C2/C3/C5/C6 | budget、analyzer、module index、Git repository、writer/source viewの回帰を更新 |
| 12 | `79fa0a64bcc206bff4ccc2087683c728f1a2c39e` | `fix: リポジトリ記述子を利用した安全なソース読み取りを追加` | 検証済みrepository descriptorにanchoredしたsource read、collision identity、config/import境界 | C2/C3/C5/C6 | schema/config/analyzer/source viewのrace・descriptor regressionを検証 |

責務とcommitの対応は一対一ではなく、上表の各行が複数boundaryに対応するmany-to-many traceである。`081a5d730ffd6cb7d24e9c5535c7364012154a4d`ではPlan/Reportだけを変更し、次のgovernance-only差分とした。

| governance SHA | 対象 | boundary | 検証 |
| --- | --- | --- | --- |
| `081a5d730ffd6cb7d24e9c5535c7364012154a4d` | approved as-built path、実履歴表、検証結果、残余リスク | C1〜C6の製品boundary外（完了統制のみ） | SpecDock validate、全issue gate、clean/upstream/GitHub SHA一致 |

## Verification

検証済み候補SHAは `79fa0a64bcc206bff4ccc2087683c728f1a2c39e` である。ローカルHEAD、configured upstream、GitHub branch tipは同一で、worktreeはcleanである。

- `uv run pytest -q`: `354 passed, 1 skipped`
- `uv run ruff format --check .`: 成功（86 files already formatted）
- `uv run ruff check .`: 成功
- `uv run mypy src tests`: 成功（78 source files）
- `uv build`: 成功
- `python3 ./spec-dock/scripts/spec-dock validate`: 成功（nodes=10）
- `git diff --check`: 成功

GitHub Actionsでは、`validate`、`product-test-minimum`、`product-test-latest`、`product-test-macos`、`product-package-offline`、`product-contract-scope`が候補SHAで成功した。

## Residual Risks / Follow-ups

- planned-history pathの各commitで単独checkoutがgreenだったこと、当時のRED/GREEN順序、C1〜C6単位のrollback境界は現行履歴から復元できない。今後のIssueでは実装開始前にこのPlanのcommit protocolを適用する。
- Final Quality Gateで報告されたpublication contract validation、非UTF-8 symlink targetの分類、stream I/O recovery、casefold collision groupingの計算量はP2 advisoryとして記録する。現行v2 gateのP0/P1 blockerではないため、Issue 4の自動修正範囲には含めない。
- 既存SHAとCI/review参照を維持し、履歴rewrite、force push、empty attestation commitは行わない。
