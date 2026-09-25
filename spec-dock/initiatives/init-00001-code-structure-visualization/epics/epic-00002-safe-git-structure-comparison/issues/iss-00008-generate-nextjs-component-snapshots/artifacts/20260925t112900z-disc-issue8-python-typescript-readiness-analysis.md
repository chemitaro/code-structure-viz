---
種別: disc
ID: "20260925t112900z-disc"
タイトル: "Issue #8 Python-TypeScript architecture and readiness analysis"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-09-25"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: []
reflected_to: ["design.md", "plan.md"]
---

# 20260925t112900z-disc Issue #8 Python-TypeScript architecture and readiness analysis

複数の証拠を統合し、選択肢と trade-off を整理します。一つの source の調査は `research` を使います。

## Inputs

- 統合する evidence:
  - ChatGPT Use Strict session `required-strict-github-connector-verificati-1222`; GitHub connector confirmed `chemitaro/code-structure-viz`, branch `iss-00008-generate-nextjs-component-snapshots`, exact tip `d01852d0f53b14bcada03f92408864ad52a2396a`, parent `54bf763f230cd89159542204562daa8ca0835754`.
  - User-requested model/effort was GPT-5.6 Pro. Oracle picker evidence recorded resolved model `GPT-5.6 Sol` and thinking `Pro`, both verified. Following the user's clarification, this Sol + Pro-effort selection is treated as the requested GPT-5.6 Pro analysis; the UI record is retained verbatim rather than claiming a distinct backend identity.
  - Current Requirement, Design, Plan, `next-process-launch-policy-v1.schema.json`, `next-diagnostic-catalog-v1.json`, and current production source/tests.
  - Prior evidence: `20260924t002133z-disc-issue8-strict-dependency-adapter-identity.md` and `20260925t075208z-disc-issue8-current-v1-cumulative-strict-review-54bf763.md`.
  - Current source inventory: Python `applicability.py`, `configuration.py`, `protocol.py`, `source_acquisition.py`, and `source_graph.py`; no production `runner.py`, `bridge.py`, TypeScript `analyze.ts`, packaged `_next_runtime/next-adapter.mjs`, or `tests/acceptance/next/` suite.
  - Read-only SpecDock dependency check reported Issue #8 `open`, active `iss-00008`, `ready=true`, no blockers. Local HEAD and live GitHub branch tip both matched `d01852d...`; worktree was clean before this Artifact and canonical edits.

## Synthesis

- 一致する事実と未確定事項:
  - **推奨architectureはPython CLI/core + TypeScript semantic adapterである。** PythonはCLI、domain selection/applicability、source acquisition/sealing、Node process policy/observation、private protocolの検証、public JSON/PlantUML/manifest/stdout publicationを所有する。TypeScript adapterだけがNext固有のProgram/AST/TypeChecker semanticsを所有し、Pythonが検証可能なversioned private JSONで連携する。
  - これは新規のlanguage split提案ではない。Designは「Next固有semanticsはfirst-party TypeScript adapter」「source bytes、process trust、public validation/rendering、outcome/publicationはPython core」と定める。RequirementはpropsをTypeCheckerのeffective signatureから閉じたtype IRへ写す。全PythonはTypeScript symbol/type semanticsを再実装するリスクがあり、全TypeScriptは既存Python CLI/core/publicationを置換してNode dependencyを広げる。どちらもcurrent-v1の責務境界に劣る。
  - TypeScript Compiler APIを選ぶだけでは安全性は成立しない。default compiler hostで対象filesystemへアクセスさせず、sealed bytesとbundled trusted declarationsを使うin-memory CompilerHostが必要である。Nextアプリ、config/plugin、build、target `node_modules`、networkを実行・参照しない契約を維持する。
  - Python側にはapplicability/configuration/source acquisition/protocolの先行実装と、contract/schema/reference validator/testsがある。一方、production TypeScript analyzer、Python-to-Node runner/bridge、adapter packaged resource、response-to-publicationの実経路、CLI acceptance/security/offline packaging testsは存在しない。従ってIssue #8は実装完了ではない。
  - 現行process policy schemaは`adapter.schema`, stable `adapter.version`, `adapter.sha256`を要求し、Node policy/runtime identityとadapter identityを実行・検証の根拠にする。`pyproject.toml`の`0.1.0.dev0`はstable adapter versionではない。
  - 現在のcumulative Code Review passは`54bf763...`までである。current tip `d01852d...`はそのreview evidence Artifactを追加した先端で、今回のUse Strictは設計分析であってCode Review passではない。過去review pass、green CI、Issue open/ready、production completionは別々の証拠である。

## Options and trade-offs

- 選択肢と利点・制約:
  - **Pythonのみ:** CLI/coreとの統合は単純に見えるが、TypeScriptのsymbol alias、re-export、effective type、JSX semanticsをPythonで再実装するか、結局Node/TypeScriptを呼ぶ必要がある。前者は意味差・保守負荷、後者は実質hybridになる。
  - **TypeScriptのみ:** compiler semanticsとimplementation languageを揃えられるが、既存Python CLI/Git/source safety/outcome/publicationを置換し、Nodeを共通利用の必須依存にしやすい。今回必要なNext semanticsだけに責務を絞れない。
  - **Python orchestration + TypeScript adapter（推奨）:** TypeScript固有意味解析をTypeScript Compiler APIへ置き、既存Python coreの安全な取得・プロセス制御・検証・公開を再利用する。NodeはNext projectが適用対象である場合だけ要求する。
  - **Adapter identity decision:** 直前に提示したcandidateを採択する。locatorは`importlib.resources.files("code_structure_viz").joinpath("_next_runtime", "next-adapter.mjs")`のみ。entrypointの先頭ASCII行`// CodeStructureViz-Adapter-Version: <MAJOR>.<MINOR>.<PATCH>\n`からstable canonical SemVerを読み、同一の保持bytes全体（header含む）をSHA-256にする。初期versionは`0.1.0`。sidecar、Python distribution version、caller override、checkout/fixture fallbackは使わない。
  - この判断はpre-launch resource identityに限る。Node version probe、process policy、実spawn/ProcessLaunchObservation、wheel/sdist同梱、offline successful Next runは後続gateで個別に証明する。identity resolver successだけでproduction availabilityを主張しない。

## Reflection

- 2026-09-25のユーザーによる「作業を進めてください」を直前のidentity candidate採択として解釈し、Designの`Production adapter identity`とPlanの`I05-PLAN-002A`へcanonical反映した。このArtifactは分析evidenceであり、Design/Plan/schemaのauthorityを置き換えない。
- 同candidateのcanonical updateはSpecDock `validate`（nodes=10）と関連contract/schemaテスト808件を通過した。fresh exact-current-SHA ChatGPT Code Review Strictはこれらのcanonical変更後に実行する。passになるまでproduction resolver codeを開始しない。
- 続く実装単位は`I05-PLAN-002A`、`src/code_structure_viz/adapters/next/runner.py`と`tests/unit/next/test_runner.py`。TDDでsingle package resource, stable header, same-byte hash, fail-closed casesを検証する。サブエージェントは使用しない。
