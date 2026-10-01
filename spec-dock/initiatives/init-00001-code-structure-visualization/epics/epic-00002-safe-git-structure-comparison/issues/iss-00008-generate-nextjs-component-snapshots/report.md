---
種別: レポート（Issue）
ID: "iss-00008"
タイトル: "Generate Nextjs Component Snapshots"
関連GitHub: ["#8"]
最終更新: "2026-10-01"
依存: ["requirement.md", "design.md", "plan.md"]
親: ["epic-00002", "init-00001"]
---

# Result Summary

詳細: [Report Guide](../../../../../../docs/authoring/report.md)

## Outcome

Issue #8は未完了です。2026-10-01にA runtime modelを採択し、非productionのpublic-spawn feasibilityを両OSで確認しました。採択はADR/R/D/P、実験結果とコードはArtifactへ保存しました。製品のTypeScript解析、Next CLI公開、package同梱、新runtime契約のStrict認定はまだ完了していません。

## Verification

- macOS 27.0.1 arm64 / Python 3.12.11 / Node 22.10.0・24.14.0、Linux arm64 / Python 3.12.14 / Node 22.0.0・22.23.3で、synthetic bootstrap/spawnの8 checksをpass。
- Node 20.19.5（macOS）/20.19.4（Linux）はanalyzer初期化前に拒否を確認。harnessは期待した拒否を検証してexit 0、子はexit 66。
- 実16 MiB stdout / 64 KiB stderrのexact/+1、TERM-resistant親/子を含むtimeout cleanup、別private cwd、env/継承FDを確認。実TypeScriptのacceptanceではありません。
- 詳細・失敗試行・未確認点: `artifacts/20261001t030614z-disc-issue8-a-launch-feasibility-evidence.md`。
- checkpointのローカル回帰: `uv run --locked pytest -q`が1907 passed / 1 skipped、Ruff/format、mypy（152 source files）、SpecDock sync/validate（nodes=10）、`git diff --check`がpass。旧文書見出しの固定assertを採択済み正本名とADR参照へ更新し、失敗した1 testのfocused GREENと全suite再実行を確認しました。
- `src`、schemas、`pyproject.toml`、`uv.lock`の差分は無し。今回の実機コードは非production evidenceだけで、既存の製品実装を新runtimeへ接続していません。

## Residual Risks / Follow-ups

- A-02の新version schema/reference/compatibility/provenance closure、A-03のfresh独立Strict、production TDD、両OS実CLI/offline package、Final Quality Gateが残っています。
- Darwinの終了済みgroup確認は公開libproc APIを使った試作候補です。製品cleanupの全条件・全対応OS/architectureを認定したものではありません。
- trusted user toolchainはsame-UID敵対改変・未知runtime exploit・hard RSS隔離を保証しません。これは採択済みscopeであり、不足する実装を成功と見なす免除ではありません。
