# Issue #8: control READ Strict指摘とOracle回収記録

作成日: 2026-09-28
対象Issue: `iss-00008-generate-nextjs-component-snapshots`
対象実装段階: `I05-PLAN-008`
基準SHA: `f4159066f3954454ad2f0c2701fa54bf1bc7bc4a`
レビュー対象SHA: `4debc6a6b1075539cc77e37d5a6af11993768df0`

## 結論

Oracleサービスそのものが利用不能だったわけではない。最初のStrict Code Review会話は回答を生成したが、回答本文にChatGPTのinline citation tokenがJSON内へ付加され、Strict wrapperが出力契約違反として受理できなかった。新しいStrict review会話では、ChatGPTは応答を生成していたがOracle側が完了を検出できず、通常のforeground controllerが長時間応答待ちになった。controller/ChromeのPIDとtab leaseが消えたあともsession metadataは`running`のまま残った。保存済みの同一ChatGPT会話へ`oracle session ... --live`で再接続すると、会話IDとcapture identityが一致したcompleted assistant turnを回収できた。API fallbackや別会話への重複再送は行っていない。

これらはOracle/browserのtransport・capture問題であり、コードレビューのsemantic判定とは別である。Oracle controllerがorphan化した根本原因は未特定であり、再現テストやOracle修正を行っていないため「根本原因を修正済み」とは扱わない。

## Strict Code Review結果

- Reviewer: ChatGPT Code Review Strict、Oracle session `required-strict-github-connector-verificati-1331`。
- ChatGPT conversation: `6aba3a24-4d08-83ee-8951-9cd49595d73c`。復旧結果は`state=completed`、1 assistant turn、`Capture identity: matched`。
- 選択モデル: GPT-5.6 Sol。session metadataで`verified=true`。
- 推論レベル: wrapper argvは`--browser-thinking-time extra-high`。回収時に`Thinking effort Extra High`と表示。元session metadataに`thinkingSelection` objectはない。
- Strict GitHub verification: 対象branch tipは`4debc6a6b1075539cc77e37d5a6af11993768df0`と一致。固定点/merge-baseは`f4159066f3954454ad2f0c2701fa54bf1bc7bc4a`。
- Review artifact: `/Users/iwasawayuuta/.oracle/sessions/required-strict-github-connector-verificati-1331/output.log`。
- Artifact SHA-256: `d025487ae9559f8637f784ba53752650ea85f03c00c543135296bb2340732dfe`。
- 結果: `review_status=fail`、P1が1件。Strict review自体はstatic reviewであり、テストを実行していない。

### P1: control READをsource_readへ誤分類

現行`src/code_structure_viz/adapters/next/source_acquisition.py::_GuardedSourceReader.read_once`は、package applicability pathでない通常`READ`を一律`CSV-NEXT-SOURCE-003/source_read`へ変換する。このためreachableなroot configまたはlocal `extends`のordinary READが、current-v1の`source_control`ではなく`source_read`として報告される。P1のsource-native classificationを変更せず記録する。

期待される境界は次のとおり。

| 実際のread phase | ordinary READ outcome |
| --- | --- |
| root `package.json` preflight | `CSV-NEXT-APPLICABILITY-002 / applicability`、public pathなし |
| root config / local `extends` | `CSV-NEXT-SOURCE-003 / source_control`、失敗control path |
| program / context | `CSV-NEXT-SOURCE-003 / source_read`、失敗source path |

限度、path-safety、symlink/non-regular/raced-missing、integrity driftはordinary READと混同せず既存outcomeを維持する。

## Strict指摘分析

- Analyst: ChatGPT Analyze Review Findings Strict、Oracle session `required-strict-github-connector-verificati-1337`。reviewerとは別の新規conversation。
- Conversation ID: `6aba68e0-cb68-83e8-8286-c3e91cfe3f54`。
- 分析結果artifact: `/Users/iwasawayuuta/.oracle/sessions/required-strict-github-connector-verificati-1337/artifacts/transcript.md`。
- Artifact SHA-256: `fedf033f6165d632c18d67c5a388327f0b1e7a112e8c0f7132fa461acf2cbb3e`。
- selected model/effort: GPT-5.6 Sol / Extra High。Oracle session metadataで両方verified。
- connectorはanalysis中にrepository、target branch、full SHAを検証し、expected SHAと一致した。
- disposition: `implementation-remediation`。current-v1 requirement/design/planとproduction pathおよび独立reference validatorが同じ意味を定めるため、canonical変更やhuman decisionは不要。
- first incorrect layer: `source_acquisition.py` production acquisition classification。package ordinary READのAPP-002とprogram/context source_readは保持し、control ordinary READだけsource_controlへ修正する。
- P1は修正後、同一reviewerによるfresh exact-SHA cumulative Strict passまでopen/blocking。既存green testやanalyst判定でclosureしない。

## 実装・検証記録

実装単位は`I05-PLAN-008-R1-control-read-stage`。変更はproduction acquisitionとproduction adapter unit testsに限定し、reference model/schema/diagnostic catalogやI05-PLAN-002Aは変更しない。

| 検証 | 結果 |
| --- | --- |
| 追加したroot-config/local-extends ordinary READ testの実装前Red | 2 failed。実際のstageが`source_read`であり、期待`source_control`と不一致 |
| 同じfocused testのGreen | 2 passed |
| `uv run pytest -q tests/unit/next/test_source_acquisition.py tests/contracts/test_next_contracts.py::test_nonordinary_read_failure_preserves_classification_and_actual_phase_prefix tests/contracts/test_next_contracts.py::test_package_read_failure_preserves_its_distinct_reference_outcome` | 104 passed |
| `uv run --group dev pytest -q` | 1,870 passed, 1 skipped |
| `uv run --group dev ruff format --check .` | 174 files already formatted |
| `uv run --group dev ruff check .` | pass |
| `uv run --group dev mypy src tests` | 150 source files、issueなし |
| `uv build --offline` | sdist/wheel build成功 |
| `python3 ./spec-dock/scripts/spec-dock validate` | pass、nodes=10 |
| `git diff --check` | pass |

上記はR1の未公開worktree候補での検証結果。commit、push、fresh Strict re-review、CIはこの記録作成時点では未実施である。したがってR1は実装・local validation完了に限られ、I05-PLAN-008 pass、Issue #8完了、I05-PLAN-002A開始可能、production/runtime readinessを意味しない。

## 先行候補の既知CI情報

修正前候補`4debc6a6b1075539cc77e37d5a6af11993768df0`について、先行記録ではGitHub Actions run `36402766531`の7 jobsがsuccessとされている。ただし今回のStrict analystはconnector応答からrun head SHAを独立再取得できず、run-to-candidate bindingはlocal packet evidence依存と明記した。R1 candidateのCIは別途実行・SHA照合する。

## 次のゲート

1. branch、HEAD、worktreeを再確認し、この実装単位のtracked変更だけをcommitし、許可済みのnon-force pushを行う。
2. 新candidateのlocal/upstream/live GitHub branch SHA一致とclean stateを検証する。
3. fixed point `f4159066f3954454ad2f0c2701fa54bf1bc7bc4a`からの累積範囲についてfresh Strict Code Reviewを同じreviewer方針で実行する。
4. P0/P1が0で`review_status=pass`になるまでI05-PLAN-002Aへ進まない。
5. Issue #8全計画のcompletionとFinal Quality Gate Strict v2を別ゲートとして完了する。
