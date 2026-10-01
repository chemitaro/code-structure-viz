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

採択・実測checkpointは`710eb49a2a3143e31b8a91580700d16839d9070d`でcommit/push済みです。このexact SHAへGPT-5.6 Sol / Proのfresh ChatGPT Use Strict分析を完了し、同一SHAと実pickerのverified結果を確認しました。助言をローカルref/hashへ照合し、必要なstdout/generic semantic/trusted descriptorの版移行を補正しました。A02を小さい契約から進めていますが、A03独立コードレビューは未通過です。

## Verification

- macOS 27.0.1 arm64 / Python 3.12.11 / Node 22.10.0・24.14.0、Linux arm64 / Python 3.12.14 / Node 22.0.0・22.23.3で、synthetic bootstrap/spawnの8 checksをpass。
- Node 20.19.5（macOS）/20.19.4（Linux）はanalyzer初期化前に拒否を確認。harnessは期待した拒否を検証してexit 0、子はexit 66。
- 実16 MiB stdout / 64 KiB stderrのexact/+1、TERM-resistant親/子を含むtimeout cleanup、別private cwd、env/継承FDを確認。実TypeScriptのacceptanceではありません。
- 詳細・失敗試行・未確認点: `artifacts/20261001t030614z-disc-issue8-a-launch-feasibility-evidence.md`。
- Strict advisoryと採否: `artifacts/20261001t040546z--a-runtime-contract-analysis-result.md`、`artifacts/20261001t040605z-disc-issue8-a-runtime-contract-analysis-adjudication.md`。Oracle0.21.3/session `issue8-a-runtime-closure`はexit0 completed、requested/resolved GPT-5.6 Sol / Pro、両picker verified=true。巨大reference全通読やtest再実行、製品認定は外部分析では行っていません。
- `710eb49...` checkpointのローカル回帰: `uv run --locked pytest -q`が1907 passed / 1 skipped、Ruff/format、mypy（152 source files）、SpecDock sync/validate（nodes=10）、`git diff --check`がpass。旧文書見出しの固定assertを採択済み正本名とADR参照へ更新し、失敗した1 testのfocused GREENと全suite再実行を確認しました。
- A02 policy初スライス: v2 prelaunch policy＋runtime requirement leaf、独立した小さいreference validator、明示reference fixtureを追加。schema欠落、argv/candidate mismatch、private layout mismatchをfocused RED→最小GREENで処理。current focusedは25 passed、既存schema/doc-pointerとの関連selectionは145 passed（4.43s）、Ruff/format/mypy154 files、SpecDock validate、diff-checkがpass。全suite再実行はA02の全closure後gateとして残しています。
- A02 execution assets slice: 新leaf、immutable byte owner、独立known hash、metadata-only/byte-bound検証、policy asset/adapter joinsを追加。改変metadataを再hashしてもowner不一致を拒否。current focusedは60 passed、既存schema/doc-pointer込み180 passed、Ruff/format/mypy155 files、SpecDock validate、diff-checkがpass。詳細は`artifacts/20261001t045200z-disc-a-execution-assets-contract-slice.md`。fixtureのsynthetic compilerは実TypeScriptではなく、製品のstaging/実行は行っていません。
- A02 observation/binding slice: host-local観測とsuccess-only portable identityを追加し、phase/control/exit/capture/cleanup/drift/retained identityのdata joinsを検証。focused 147 passed、関連selection 811 passed / 144 deselected、current-doc pointer 1 passed、Ruff/format（184 files）/mypy（156 source files）、SpecDock sync/validate、diff-checkがpass。初回Ruffの長いtest名E501は短縮してGREEN。詳細は`artifacts/20261001t060157z-disc-a-runtime-observation-binding-contract-slice.md`。response SHA/PID/bytesはsyntheticで、actual raw-frame/counters/trusted profile joinと実OS ownerは未完了です。
- A02 response-byte初スライス: single closed control/nullable payload、bounded immutable frame owner、raw SHA/control/stdout量のdata joinsを追加。新wire focused 19 tests、関連selection 287 passed（6.56s）、Ruff/format（186 files）/mypy（157 source files）、SpecDock sync/validate、diff-checkがpass。private request/stdin/context/trusted/Core proof/compatibility joinsと実OSは未完了。evidenceは`artifacts/20261001t062630z-disc-a-response-frame-v2-contract-slice.md`。旧helperはwire非依存JSON grammarだけを再利用し、v1 runtimeを認定経路にしていません。
- A02 trusted v2 slice: logical descriptorとpackage mapping manifestのidentityを分離し、同じretained ownerの4 declaration/14 symbols、両hash、実source-seal/v1とpolicyのdata joinsを検証。変更/欠落/余分/role違い、再hashした偽profile/mapping、fake ownerを拒否します。新runtime関連199 passed、source/旧request/schema/doc regression込み359 passed（11.46s）、Ruff/format（190 files）/mypy（160 source files）、SpecDock sync/validate、diff-checkがpass。詳細は`artifacts/20261001t065813z-disc-a-trusted-environment-v2-contract-slice.md`。実TS/installed package/source-phase順序/child利用とA03は未認定です。
- A02 request v2 slice: actual source seal/retained asset ownerからintent-only requestを生成し、source/config/roles/bytes・context budget・canonical bytes/ID・private owner stampsを検証。新focused 28 passed、runtime/source/旧request/schema/doc-pointer関連388 passed（12.48s）、Ruff/format（192 files）/mypy（161 source files）、SpecDock sync/validate（nodes=10）、diff-checkがpass。独立literalのwireは3961 bytes、request IDは`364ae1c7...`、full-wire SHAは`2775c51c...`。実96 MiB exact/+1、構造制限、再hashされた別source/asset/config等を検証します。evidenceは`artifacts/20261001t073352z-disc-a-request-frame-v2-contract-slice.md`。stdin capture/response echo/Core proof/compatibility/public全chainは未完了で、実Node/TS/CLIを実行していません。
- `710eb49...`では`src`、schemas、`pyproject.toml`、`uv.lock`の差分は無し。続くA02初スライスは新schema/reference/docsだけで、旧v1 schemaとproduction `src`/依存/lockfileを変更していません。実機コードは非production evidenceだけで、既存の製品実装を新runtimeへ接続していません。

## Residual Risks / Follow-ups

- A-02の新version schema/reference/compatibility/provenance closure、A-03のfresh独立Strict、production TDD、両OS実CLI/offline package、Final Quality Gateが残っています。
- Darwinの終了済みgroup確認は公開libproc APIを使った試作候補です。製品cleanupの全条件・全対応OS/architectureを認定したものではありません。
- trusted user toolchainはsame-UID敵対改変・未知runtime exploit・hard RSS隔離を保証しません。これは採択済みscopeであり、不足する実装を成功と見なす免除ではありません。
