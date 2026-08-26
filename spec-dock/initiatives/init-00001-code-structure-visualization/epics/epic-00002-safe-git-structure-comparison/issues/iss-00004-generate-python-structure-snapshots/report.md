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

実装・hardeningのas-built範囲は次の通りである。

| 範囲 | commit | 概要 |
| --- | --- | --- |
| 実装開始 | `eaf29540c866249552600faaa31aaba5be7932f2` | CLI、config、SourceView、Python AST、renderer、manifest、publication、test、packageの初期実装 |
| 契約・安全性 | `19d9d8f`〜`2104974` | snapshot契約、型参照解決、schemaおよび安全性の強化 |
| SourceView / publication hardening | `37f7a5e`〜`dae6084` | containment、race、深い入力、cleanup、collision、path置換、長整数の修正 |
| 最終安全性修正 | `79fa0a64bcc206bff4ccc2087683c728f1a2c39e` | 検証済みrepository descriptorに固定したソース読み取り |

責務とcommitの対応は一対一ではなく、C1（CLI/config/contracts）、C2（read-only Git/SourceView）、C3（AST semantic extraction）、C4（JSON/PlantUML rendering）、C5（publication/stream/outcome）、C6（security/package/CI hardening）のmany-to-many traceとしてPlanの論理境界を維持する。

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
