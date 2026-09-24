---
種別: disc
ID: "20260924t104417z-disc"
タイトル: "Issue #8 current-v1 dependency/readiness root-cause analysis at 985922b"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-09-24"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: []
reflected_to: ["requirement.md", "design.md"]
---

# 20260924t104417z-disc Issue #8 current-v1 dependency/readiness root-cause analysis at 985922b

現在の `I05-PLAN-008` readiness blocker を、candidate `985922b` に固定された一次証拠と独立レビューから adjudicate し、bounded remediation を記録します。本 Artifact は evidence であり、Requirement / Design / Plan の意味を独立に変更しません。

## Inputs

- Repository / branch: `chemitaro/code-structure-viz`, `iss-00008-generate-nextjs-component-snapshots`.
- Exact reviewed candidate: `985922bcaab0be25674db9402f36539d4cd2f375`; fixed point: `1df6c4e8c8b76bf1ebc02590600d98f8fa6491a8`.
- ChatGPT Strict analysis: Oracle session `required-strict-github-connector-verificati-1131`, requested and UI-verified `GPT-5.6 Sol / Pro`; GitHub connector verified repository, target branch, and expected/tip full SHA equality immediately before response. Stored transcript: `/Users/iwasawayuuta/.oracle/sessions/required-strict-github-connector-verificati-1131/artifacts/transcript.md`, SHA-256 `baeb504f48f89a2d7915afb866f9b23659999b0e7d3a4f41675bfacbcd01a20a`.
- ChatGPT Strict review: fresh browser session `required-strict-github-connector-verificati-1127`, exact same candidate, schema-valid `review_status=fail`; source-native findings P1 and P2 are preserved below.
- Independent GPT-6 Max review: read-only review of the same candidate; `P0=0 / P1=1 / P2=1`, readiness fail. Preserve configured identity and source-native priorities; do not attribute UI picker evidence to this reviewer.
- Authoritative inputs: current Issue #8 Requirement / Design / Plan; `next-provenance-v1`, `next-run-decision-v1`, `next-publication-decision-v1` schemas; `tests/contracts/next_reference_validation.py`, `tests/contracts/test_next_contracts.py`, and `tests/fixtures/next_contract_vectors.json` at the verified commit. Exact GitHub commit supersedes conflicting attachment text.
- Prior context: `20260924t085449z-disc-issue8-i05-plan008-review-findings-analysis-strict.md` and `20260924t021633z-disc-issue8-dependency-root-cause-strict.md`; their earlier candidate-specific claims are historical unless revalidated here.
- Test and CI evidence recorded in the input packet: exact-HEAD pytest `1797 passed, 1 skipped`; focused independent review run `105 passed, 520 deselected`; GitHub Actions run `35983077528` green 7/7. This analysis did not execute pytest, Node, or production runtime.

## Synthesis

### Strict exact-SHA result

GitHub connector で `chemitaro/code-structure-viz` の対象 branch tip が expected SHA `985922bcaab0be25674db9402f36539d4cd2f375` と byte-for-byte 完全一致した。回答直前にも branch tip を再取得して一致を確認した。default branch や別 branch は根拠にしていない。

総合判定は `I05-PLAN-008` readiness blocked。CI green はレビュー gate の代替ではない。今回の原因は外部 package install の不足ではない。

### Findings adjudication

| Source / severity | 判定 | 最初の不整合箇所 | 根本影響 |
| --- | --- | --- | --- |
| ChatGPT Strict P1: pathless `CSV-NEXT-LIMIT-001` の phase substitution | 有効。通常の reader は正しい phase を記録する一方、検証可能な private object を `dataclasses.replace` 等で改変できる | `EarlySourceReadPrefix.__post_init__` | `path=None` では `read_phases` の trigger row と `phase` を照合しない。`provenance()` が caller-supplied phase から観測prefixを決め、未観測config/sourceの合成または実prefixの消去が可能。reader-owned evidence invariant を壊す。 |
| ChatGPT Strict P2: current registry 20/26不一致 | 有効。実fixtureとPlanは26、RequirementとDesignは20 | Requirement / Designのcurrent authority記述 | 6件の追加evidenceが現行必須か逸脱か一意でなく、後続coverage gateとレビュー判定が不安定。これは実行時障害ではない。 |
| GPT-6 P1: 通常生成pre-seal failureのrun/publication schema rejection | 有効かつ通常経路で到達可能。証拠改変は不要 | `schemas/next-run-decision-v1.schema.json` のrequest-independent `source_read` branch | `next-provenance-v1` は `early_observed` / `config_observed` / `preseal_source_observed` を許すが、run decisionは `early_observed` のみに制限。run projectionが最初にschema-invalidとなり、nested decisionを使うpublicationもinvalid。 |
| GPT-6 P2: 改ざんしたpathless prefixがpublicationまで通る | 有効。ChatGPT Strict P1と同じ defectで、別root causeに数えない | `EarlySourceReadPrefix.__post_init__` | severity差はそのまま記録する。GPT-6は正常構築経路の正しさを重視してP2、Strictはvalidation boundaryのevidence forgeryを重視してP1。 |

### Root cause

1. **private evidence と public redaction の混同**: 公開pathの秘匿を理由に、private failed path / read-phase rowの検証まで省略している。public `path=None` と private trigger identityは独立に扱う必要がある。
2. **current-v1 schema union drift**: provenance schemaの許容範囲を広げた一方、run-decision schemaの対応unionを同期していない。publication rejectionはこの不一致の下流症状。
3. **coverage chainの早期終了**: existing phase-matrix coverageはreader resultとprefixまでで、decision projection・run schema・finalizer・publication schemaを通さない。よってgreen CI/full pytestと実在defectは矛盾しない。
4. **重複したregistry count**: Requirement/Designの20は、必要な6 vectorsの追加後も残ったstale baseline。Planと実fixtureの26を削除する根拠はなく、historical Round23の36件とも混ぜない。

### 依存関係の因果判定

この問題は `InstrumentedSourceReader → EarlySourceReadPrefix → provenance schema → run-decision schema → publication schema → runtime-vector coverage` だけで発生する。Node、npm、`node_modules`、wheel/sdist、production adapterはこの経路に関与しない。packageを追加installしてもprivate phase bindingやschema unionは直らず、必要条件でも十分条件でもない。将来のadapter resource identityやruntime/package acceptanceは別gateであり、今回のI05-PLAN-008範囲へ持ち込まない。

## Options and trade-offs

### 採用する bounded remediation

1. **Reader evidenceを唯一のphase authorityとする。** Pathless diagnosticでもprivate `failed_reads` のtrigger rowを決定し、そのpathの`read_phases`とfailure code/kind/stageを検証する。公開pathはcatalogの`ref_permission`どおりredactするが、private bindingを省略しない。構築済みprefixへの `dataclasses.replace` で異なるphaseを設定するnegative testsを追加する。
2. **run-decision schemaを既存current-v1 provenance unionへ同期する。** request-independent pre-seal `source_read` の観測prefixを、限定された `early_observed | config_observed | preseal_source_observed` とする。seal済み `source_observed` branchは既存の別branchのままにし、広い`observation_map`へ弱めない。まず現行 `next-publication-decision-v1` を再検証し、必要性を証明できない限り直接変更しない。
3. **既存phase-matrix registry pairをpublication chainまで強化する。** 新規recordを足さずcurrent registry 26件を維持する。各reader resultを provenance → decision → run schema → finalizer → publication projection/schemaまで通し、positiveとmutation negative双方を検証する。
4. **Requirement / Designのcurrent registry数を26へ同期する。** Planとfixtureは26件のまま、historical Round23 registryは36件のまま。Round履歴の文章・件数は書き換えない。

### Ordered Red → Green sequence

1. **RED A:** `TOO_LARGE` / `TOO_MANY_FILES` を使い、5種類の正当phase（applicability、root_config、local_extends、program、context）から全ての別phaseへ置換する。`failed_reads`と`read_phases`は改変しない。最初の拒否箇所はprivate prefix invariantとする。
2. **GREEN A:** private trigger rowからactual phaseを導出または同値検証し、pathlessでも偽装を拒否する。honest prefixとpathful unsafe/symlink/non-regular/raced-missing regressionを維持する。
3. **RED B:** actual readerから `4 phases × 6 non-integrity failure kinds × 4 selectors = 96` casesを作る。provenance schemaは有効だがrun decisionが無効となる現在の最初のfailureを固定する。
4. **GREEN B:** 96件すべてをrun-decisionおよびpublication schemaまで通す。root_config/local_extendsはapplicability+config、program/contextはapplicability+config+sourceを観測し、後続limits/source-plan/request/toolchain/trust/process/response/budgetはunobserved/null。run/publication outcome、exit、selectorごとのstdout、no-artifact/no-partial-payloadを確認する。
5. **Registry blind spot:** `round22-runtime-phase-failure-matrix` とそのmutation pairをchain全体へ拡張し、registryは26件を維持する。
6. **Count:** Requirement / Design / Plan / fixture = 26、historical R23 = 36を検証する。
7. **Regression gates:** sealed-source failure、root package ordinary READのAPP-002、actual integrity terminal、program/context ordinary READ routing、full selectorsを再検証する。

この順序は推奨計画であり、Strict analystがテストを実行したという意味ではない。

## Reflection

### Scope boundary

今回含むのはreference contract/tests/fixture、`next-run-decision-v1` schema、Requirement/Designのcount整合、新しいadjudication Artifactまで。Planは意味を広げず整合確認する。

以下は明示的にdeferする: production `src/**`、Next adapter、Node discovery/spawn/実行、OS process acceptance、Python/npm dependency manifest、lockfile、package install、wheel/sdist/build inventory/offline package acceptance、release、PR merge、Issue close、新しいpublic field/code/stage/outcome/schema version、historical Roundの改変。

本Artifactで選択した実装範囲は既存Planのreader-owned pre-seal prefix契約に従う。新規public semanticsは追加しない。current registry count 26への同期は現行Requirement/Designに反映する。

### 現時点の実装・gate状態

- Strict analysis時点ではcandidate `985922b` がreadiness blocked。Strict分析自身はpytest/Node/runtimeを実行していない。
- TDD Red: pathless limit phase mutation testは当初、現行prefix constructorが拒否しない10ケースを確認。implementation後Greenは `10 passed`。
- Schema Red: `root_config × TOO_LARGE × omitted selector` は `next-run-decision-v1` validationで失敗し、provenanceのconfig observationがrun schemaのearly-only branchで拒否されることを確認。existing prefix unionとのschema同期後、focused first sliceは `4 passed`。
- Expanded Green: 4 phases × 6 non-integrity failure kinds × 4 selectors = 96件が provenance → run-decision schema → finalizer → publication-decision schema → publication-chain validationまで通過。
- Focused regression set: `131 passed`。含むものはphase mutation、96-case matrix、ordinary package-read distinction、all-phase integrity terminal、current runtime registry execution。
- 全repository `uv run --group dev pytest -q`: `1879 passed, 1 skipped in 262.22s`。
- `uv run --group dev ruff check .`: pass; `uv run --group dev ruff format --check .`: 174 files already formatted; `uv run --group dev mypy src`: no issues in 59 source files; `./spec-dock/scripts/spec-dock validate`: pass, nodes=10; `git diff --check`: pass.
- 現在の修正はreference contract/test/schema/docsに限定し、production `src/**`、dependency/lockfile、Node実行は変更・実施していない。
- Commit / non-force push、およびこの修正後のfresh same-fixed-point ChatGPT Strictと独立GPT-6 Max reviewsはこれから。成功まではI05-PLAN-008 readiness blockedのまま扱う。
- Production plans `I05-PLAN-002`〜`007` は、同一candidateでfresh ChatGPT Strictと独立GPT-6 Max reviewの双方が`P0=0 / P1=0 / review_status=pass`になるまでblocked。I05-PLAN-008通過もIssue #8全体の完成・release acceptanceを意味しない。
