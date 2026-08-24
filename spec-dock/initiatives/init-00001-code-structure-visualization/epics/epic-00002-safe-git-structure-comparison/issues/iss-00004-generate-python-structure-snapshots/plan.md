---
種別: 実装計画書（Issue）
ID: "iss-00004"
タイトル: "Generate Python Structure Snapshots"
関連GitHub: ["#4"]
package_sequence_key: "ISSUE-01"
状態: "draft"
最終更新: "2026-08-24"
依存: ["requirement.md", "design.md"]
親: ["epic-00002", "init-00001"]
---

# iss-00004 Generate Python Structure Snapshots — 実装計画

詳細: [Issue Plan Guide](../../../../../../docs/authoring/issue-plan.md)

## Planning Level

- **selected level: `strict`**
- 理由: public CLI、versioned semantic schema、Artifact redaction、後続全 adapter が依存する common foundation を同時に導入し、公開後の破壊的変更からの回復が難しいため strict を選ぶ。
- risk factor: public CLI/schema、static-analysis safety、Artifact integrity、adapter compatibility、誤比較時の広い説明影響。
- `critical` ではない理由: target repository と persistent user data を変更せず、release/commit 単位で戻せる設計である。
- 再評価条件: secret/PII exposure、target mutation、不可逆 data loss、incident response が必要な rollout を追加する場合。

## 目標

coding agent または人間が、対象 Python repository を実行せずに class 構造を semantic JSON と PlantUML で取得できる。

completion は file/technical layer の完成ではなく、次の observable chain で判定する。

```text
CLI request -> safe source acquisition -> domain semantic analysis
  -> versioned semantic JSON + domain PlantUML -> diagnostic/manifest
  -> acceptance command and exit evidence
```

## 順序・依存

- declared dependency: なし。
- execution order: I01-PLAN-001 → 002 → 003 → 005 → 004 → 007 → 006。acceptance fixtureとfailure/publication contractを先に固定し、entity gateをrenderer/publicationより前に置く。
- fixture authoring、schema example、PlantUML golden、security trapはI01-PLAN-001後に並行できる。
- stop condition: whole/targeted snapshot、not_applicable/incomplete、entity overrun publication、static safety、determinismがacceptanceで成立するまでdiff foundationへ進まない。

| Plan ID | implementation/verification step | Design trace |
| --- | --- | --- |
| I01-PLAN-001 | I01-AT-001〜006のCLI/status/publication/goldenを先に作り、未実装時のexpected failureを確認する。 | I01-DES-001 |
| I01-PLAN-002 | CLI/config/diagnostic/SourceView/Artifact minimal boundaryとplanned modulesを実装する。 | I01-DES-002 |
| I01-PLAN-003 | Python AST snapshot analyzerとdomain-owned identity/member/relation canonical modelを実装する。 | I01-DES-003 |
| I01-PLAN-004 | per-domain semantic JSON、PlantUML、safe run manifest、atomic no-overwrite publicationを接続する。 | I01-DES-004 |
| I01-PLAN-005 | not_applicable/incompleteとdefault 500 entity gate、valid/invalid override、publication/exitを実装する。 | I01-DES-005 |
| I01-PLAN-006 | static execution trap、redaction、determinism、lock/license/offline/minimum/latest regressionを完了する。 | I01-DES-006 |
| I01-PLAN-007 | stdout selector grammar、stream routing、exact-byte copy、unavailable result、no-selector summary、usage no-publicationを実装・検証する。 | I01-DES-007 |

## 実装step

### I01-PLAN-001 acceptance-first contract

- `tests/acceptance/python/test_snapshot_cli.py`、target/failure/security/determinism/budget fixturesを先に追加する。
- 501 entitiesでexit 3、affected JSON/PlantUMLなし、safe manifestにrequested/resolved/countがあること、600 overrideで通常公開することに加え、snapshotへの`--max-changed-paths`がexit 2・Artifactなしとなることをtable-drivenに固定する。

### I01-PLAN-002 application and source boundary

planned modules（canonical specification 時点では未実装。実装開始時に HEAD と configured upstream を再検証し、実在 path/symbol と差異があれば Design/Plan を先に更新する）:

- `pyproject.toml`、`uv.lock`
- `src/code_structure_viz/cli/main.py::main`
- `src/code_structure_viz/core/config.py::resolve_config`
- `src/code_structure_viz/core/diagnostics.py::Diagnostic`
- `src/code_structure_viz/source/source_view.py::SourceView`
- `src/code_structure_viz/artifacts/writer.py::ArtifactPublisher`
- `src/code_structure_viz/artifacts/manifest.py::RunManifest`

`--output-dir`必須、CLI > config file > built-in、unknown/type error exit 2、target repositoryへのdefault writeなしを固定する。

### I01-PLAN-003 Python semantic implementation

- `src/code_structure_viz/adapters/python/analyzer.py::PythonSnapshotAnalyzer`、`model.py`をplanned targetとする。
- whole repositoryとpath/module/class target、separate upstream/downstream traversal、normalized identity/member/relation、coverage frontierを実装する。
- target codeをimportせず、parse/read failureをempty successへ変換しない。

### I01-PLAN-005 failure and entity admission

- `src/code_structure_viz/core/budget.py::EntityBudgetGate`（planned）をrenderer前へ置く。
- no override overrunはdomain incomplete/exit 3/affected payloadなし/safe manifestあり、valid overrideはnormal、invalid overrideはexit 2とする。snapshot pipelineへ`ChangedPathAdmissionGate`を接続せず、diff専用`--max-changed-paths`指定はexit 2・Artifactなしにする。

### I01-PLAN-004 Artifact publication

- `src/code_structure_viz/adapters/python/renderer.py`、semantic serializer、manifest builderを一つのOutputTransactionへ接続する。
- staging → collision/integrity check → publishの順で、existing fileを上書きしない。pathはoutput-dir relative、digestはfinal bytes基準。

### I01-PLAN-007 stdout selector and stream contract

- CLI parserは`--stdout`を高々1回だけ受理し、`manifest | DOMAIN:FORMAT`のclosed grammar、selected domain、requested formatをsource acquisition前に検証する。invalid/duplicate/unselected/unrequestedはexit 2、stdout空、Artifactなしとする。
- publication後はavailable selectorの公開fileをexact bytesで複製する。unavailable selectorは`stdout-result/v1` 1行、selectorなしは`run-summary/v1` 1行をcanonical key orderで出す。diagnosticはstderrだけへ出し、`--output-dir` publicationを維持する。
- complete、not_applicable、partial_safe、payload_unavailable、run fatal、handled interrupt、manifest unavailableをtable-driven fixtureで固定し、source/secret/absolute pathがstdoutへ漏れないことをnegative scanする。

### I01-PLAN-006 hardening and handoff

- import/build/plugin trap、secret/literal/absolute-path scan、same-input byte equality、core-only offline install、license inventory、Python/Git minimum/latest CIを実行する。
- product HTML command/schema/UIを追加しない。実装結果はReportへ記録しPlanを実行logにしない。

## 検証

| Test ID | acceptance behavior | planned file | command |
| --- | --- | --- | --- |
| I01-AT-001 | whole repository Python snapshot | tests/acceptance/python/test_snapshot_cli.py | uv run pytest tests/acceptance/python/test_snapshot_cli.py -q |
| I01-AT-002 | target and traversal | tests/integration/python/test_targeted_snapshot.py | uv run pytest tests/integration/python/test_targeted_snapshot.py -q |
| I01-AT-003 | partial_safe/payload_unavailable snapshot matrix | tests/acceptance/python/test_snapshot_failures.py | uv run pytest tests/acceptance/python/test_snapshot_failures.py -q |
| I01-AT-004 | static/redaction safety | tests/security/test_python_static_boundary.py | uv run pytest tests/security/test_python_static_boundary.py -q |
| I01-AT-005 | determinism | tests/acceptance/python/test_snapshot_determinism.py | uv run pytest tests/acceptance/python/test_snapshot_determinism.py -q |
| I01-AT-006 | entity budget publication and diff-only option rejection | tests/acceptance/python/test_snapshot_budget.py | uv run pytest tests/acceptance/python/test_snapshot_budget.py -q |
| I01-AT-007 | stdout selector matrix | tests/acceptance/python/test_stdout_selector.py | uv run pytest tests/acceptance/python/test_stdout_selector.py -q |

### issue gate commands

```bash
uv run pytest tests/acceptance/python/test_snapshot_cli.py -q
uv run pytest tests/integration/python/test_targeted_snapshot.py -q
uv run pytest tests/acceptance/python/test_snapshot_failures.py -q
uv run pytest tests/security/test_python_static_boundary.py -q
uv run pytest tests/acceptance/python/test_snapshot_determinism.py -q
uv run pytest tests/acceptance/python/test_snapshot_budget.py -q
uv run pytest tests/acceptance/python/test_stdout_selector.py -q
uv run ruff check .
uv run mypy src tests
uv run pytest
```

### Requirement → Design → Plan → acceptance → test trace

| Requirement | Design | Plan | acceptance | test |
| --- | --- | --- | --- | --- |
| I01-REQ-001 | I01-DES-001 | I01-PLAN-001 | I01-AC-001 | I01-AT-001 |
| I01-REQ-002 | I01-DES-002 | I01-PLAN-002 | I01-AC-002 | I01-AT-002 |
| I01-REQ-003 | I01-DES-003 | I01-PLAN-003 | I01-AC-001, I01-AC-002 | I01-AT-001, I01-AT-002 |
| I01-REQ-004 | I01-DES-004 | I01-PLAN-004 | I01-AC-001, I01-AC-005 | I01-AT-001, I01-AT-005 |
| I01-REQ-005 | I01-DES-005 | I01-PLAN-005 | I01-AC-003, I01-AC-006 | I01-AT-003, I01-AT-006 |
| I01-REQ-006 | I01-DES-006 | I01-PLAN-006 | I01-AC-004, I01-AC-005 | I01-AT-004, I01-AT-005 |
| I01-REQ-007 | I01-DES-007 | I01-PLAN-007 | I01-AC-007 | I01-AT-007 |

### regression boundary

- dependency Issueのacceptance suiteを再実行し、public endpoint/source/schema/manifest/exit contractを破っていないことを確認する。
- target repositoryのHEAD、branch、refs、index、status、tracked/untracked bytesがcommand前後で一致する。
- same-input deterministic rerun、output collision、invalid override、interrupt cleanupを確認する。
- Artifact、diagnostic、stdout/stderr/logをsource body、raw hunk、comment、literal、secret、absolute pathでnegative scanする。
- visual vocabularyはcolorだけでなく記号、line style、legendをgolden/semantic testで検査する。

## rollback

- persistent data migration は N/A。release 前は Issue 単位で revert する。schema/CLI を preview 公開した後は既存 v1 reader を壊さず、v1 additive fix または新 schema version で forward recovery する。
- rollback trigger: acceptance regression、source execution/mutation、secret/absolute path leak、incorrect successful exit、ambiguous moved の誤採用。
- rollback unit: Issue の production code、tests、schema/doc additionsを一体で revert する。dependency Issue の accepted contract は戻さない。
- forward recovery: unsafe pattern を `incomplete`/`unknown` へ狭め、誤った success を継続しない。既存 Artifact を自動 rewrite しない。
- output migration は N/A。Artifact は immutable run output であり、既存 output を上書きしない。

## exit / handoff

- I01-AC-001〜I01-AC-007 の acceptance evidence が揃う。
- Requirement→Design→Plan→test trace に gap がない。
- planned path honesty を review し、実装時点の実在 path/symbol と差異があれば Design/Plan を先に更新する。
- residual risk、unsupported static pattern、coverage limitation、explicit override を release note と manifest diagnostic contract に残す。
- downstream handoff: internal foundation を兼ねる最初の利用可能 slice。ただし release milestone とはせず、Python diff 完了後に Python domain preview とする。
- completion 後も implementation/report の実績は canonical Report に別途記録し、本 Plan を実行ログにしない。
