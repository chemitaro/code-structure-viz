---
種別: 実装計画書（Issue）
ID: "iss-00006"
タイトル: "Generate SQLAlchemy ER Snapshots"
関連GitHub: ["#6"]
package_sequence_key: "ISSUE-03"
状態: "draft"
最終更新: "2026-08-24"
依存: ["requirement.md", "design.md"]
親: ["epic-00002", "init-00001"]
---

# iss-00006 Generate SQLAlchemy ER Snapshots — 実装計画

詳細: [Issue Plan Guide](../../../../../../docs/authoring/issue-plan.md)

## Planning Level

- **selected level: `strict`**
- 理由: database structure を説明する public semantic schema と privacy-sensitive redaction を導入し、誤った ORM 推測からの回復が難しいため strict を選ぶ。
- risk factor: public CLI/schema、static-analysis safety、Artifact integrity、adapter compatibility、誤比較時の広い説明影響。
- `critical` ではない理由: target repository と persistent user data を変更せず、release/commit 単位で戻せる設計である。
- 再評価条件: secret/PII exposure、target mutation、不可逆 data loss、incident response が必要な rollout を追加する場合。

## 目標

coding agent が DB や application を起動せず、SQLAlchemy declarative ORM source から table と row-level ER semantics を JSON と PlantUML で取得できる。

completion は file/technical layer の完成ではなく、次の observable chain で判定する。

```text
CLI request -> safe source acquisition -> domain semantic analysis
  -> versioned semantic JSON + domain PlantUML -> diagnostic/manifest
  -> acceptance command and exit evidence
```

## 順序・依存

- declared dependency: ISSUE-01。
- execution order: I03-PLAN-001 → 002 → 003 → 005 → 004 → 007 → 006。SQLAlchemy semanticsだけをadditiveに拡張し、ISSUE-01のcore contractをforkしない。
- static fixtures、row schema examples、renderer golden、DB/import trapsはacceptance contract固定後に並行できる。
- stop condition: table/row identity、not_applicable/incomplete、literal redaction、entity budget、determinismが成立するまでER diffへ進まない。

| Plan ID | implementation/verification step | Design trace |
| --- | --- | --- |
| I03-PLAN-001 | I03-AT-001〜007のsnapshot/status/publication fixturesを先に固定する。 | I03-DES-001 |
| I03-PLAN-002 | ISSUE-01 SourceViewとdeclarative detector/analyzer boundaryをplanned modulesへ実装する。 | I03-DES-002 |
| I03-PLAN-003 | schema.table identity、typed rows、relations、redacted defaultsのcanonical modelを実装する。 | I03-DES-003 |
| I03-PLAN-004 | SQLAlchemy semantic JSON、ER PlantUML、run manifest、atomic publicationを接続する。 | I03-DES-004 |
| I03-PLAN-005 | applicability/failureとdomain-local entity gateをstatus/exit/publicationへ接続する。 | I03-DES-005 |
| I03-PLAN-006 | DB/import/static/redaction/determinism/package/CI regressionを完了する。 | I03-DES-006 |
| I03-PLAN-007 | stdout selector grammar、stream routing、exact-byte copy、unavailable result、no-selector summary、usage no-publicationを実装・検証する。 | I03-DES-007 |

## 実装step

### I03-PLAN-001 acceptance-first contract

- normal/semantic/failure/security/determinism/applicability/entity-budget fixturesを先に作る。
- target不在とcandidate解析不能を別expected output setで固定し、501 entities/override casesとsnapshotへの`--max-changed-paths` exit 2/no-Artifact caseを追加する。

### I03-PLAN-002 static source boundary

planned modules（canonical specification 時点では未実装。実装開始時に HEAD と configured upstream を再検証し、実在 path/symbol と差異があれば Design/Plan を先に更新する）:

- `src/code_structure_viz/adapters/sqlalchemy/detector.py::DeclarativeDetector`
- `src/code_structure_viz/adapters/sqlalchemy/analyzer.py::SqlAlchemySnapshotAnalyzer`
- ISSUE-01 `SourceView`/AST reader public contract

DB connection、Alembic/runtime metadata、application importをcallできないport boundaryとexecution trapを置く。

### I03-PLAN-003 ER semantic model

- `adapters/sqlalchemy/model.py`、`redaction.py::SqlDefaultRedactor`をplanned targetとする。
- table identity、column/constraint/index/relationship rows、FK vs relationship、association/inheritanceをtyped recordsにする。
- raw defaults、URL、literalをmodelへ入れずpresence/categoryだけを比較可能にする。

### I03-PLAN-005 failure and entity gate

- no target=not_applicable、runtime-only/duplicate/broken source=incompleteを実装する。
- default 500 entity overrunはexit 3/affected payloadなし/safe manifest countあり、valid overrideはnormal、invalid valueはexit 2。snapshot pipelineへ`ChangedPathAdmissionGate`を接続せず、diff専用`--max-changed-paths`指定はexit 2・Artifactなしにする。

### I03-PLAN-004 Artifact publication

- `adapters/sqlalchemy/renderer.py`、semantic serializer、manifest descriptorをOutputTransactionへ接続する。
- canonical row order、no overwrite、final bytes SHA-256、repository-relative source provenanceを固定する。

### I03-PLAN-007 stdout selector and stream contract

- CLI parserは`--stdout`を高々1回だけ受理し、`manifest | DOMAIN:FORMAT`のclosed grammar、selected domain、requested formatをsource acquisition前に検証する。invalid/duplicate/unselected/unrequestedはexit 2、stdout空、Artifactなしとする。
- publication後はavailable selectorの公開fileをexact bytesで複製する。unavailable selectorは`stdout-result/v1` 1行、selectorなしは`run-summary/v1` 1行をcanonical key orderで出す。diagnosticはstderrだけへ出し、`--output-dir` publicationを維持する。
- complete、not_applicable、partial_safe、payload_unavailable、run fatal、handled interrupt、manifest unavailableをtable-driven fixtureで固定し、source/secret/absolute pathがstdoutへ漏れないことをnegative scanする。

### I03-PLAN-006 hardening and handoff

- DB/import traps、default/URL/secret/absolute-path scans、same-input digest、core-only offline/license/minimum/latest regressionを通し、ISSUE-04へsnapshot contractをhand offする。

## 検証

| Test ID | acceptance behavior | planned file | command |
| --- | --- | --- | --- |
| I03-AT-001 | declarative snapshot | tests/acceptance/sqlalchemy/test_snapshot_cli.py | uv run pytest tests/acceptance/sqlalchemy/test_snapshot_cli.py -q |
| I03-AT-002 | ER kinds | tests/integration/sqlalchemy/test_er_semantics.py | uv run pytest tests/integration/sqlalchemy/test_er_semantics.py -q |
| I03-AT-003 | partial_safe/payload_unavailable snapshot matrix | tests/acceptance/sqlalchemy/test_snapshot_failures.py | uv run pytest tests/acceptance/sqlalchemy/test_snapshot_failures.py -q |
| I03-AT-004 | static/redaction | tests/security/test_sqlalchemy_static_boundary.py | uv run pytest tests/security/test_sqlalchemy_static_boundary.py -q |
| I03-AT-005 | determinism | tests/acceptance/sqlalchemy/test_snapshot_determinism.py | uv run pytest tests/acceptance/sqlalchemy/test_snapshot_determinism.py -q |
| I03-AT-006 | applicability | tests/acceptance/sqlalchemy/test_applicability.py | uv run pytest tests/acceptance/sqlalchemy/test_applicability.py -q |
| I03-AT-007 | entity budget publication and diff-only option rejection | tests/acceptance/sqlalchemy/test_snapshot_budget.py | uv run pytest tests/acceptance/sqlalchemy/test_snapshot_budget.py -q |
| I03-AT-008 | stdout selector matrix | tests/acceptance/sqlalchemy/test_stdout_selector.py | uv run pytest tests/acceptance/sqlalchemy/test_stdout_selector.py -q |

### issue gate commands

```bash
uv run pytest tests/acceptance/sqlalchemy/test_snapshot_cli.py -q
uv run pytest tests/integration/sqlalchemy/test_er_semantics.py -q
uv run pytest tests/acceptance/sqlalchemy/test_snapshot_failures.py -q
uv run pytest tests/security/test_sqlalchemy_static_boundary.py -q
uv run pytest tests/acceptance/sqlalchemy/test_snapshot_determinism.py -q
uv run pytest tests/acceptance/sqlalchemy/test_applicability.py -q
uv run pytest tests/acceptance/sqlalchemy/test_snapshot_budget.py -q
uv run pytest tests/acceptance/sqlalchemy/test_stdout_selector.py -q
uv run ruff check .
uv run mypy src tests
uv run pytest
```

### Requirement → Design → Plan → acceptance → test trace

| Requirement | Design | Plan | acceptance | test |
| --- | --- | --- | --- | --- |
| I03-REQ-001 | I03-DES-001 | I03-PLAN-001 | I03-AC-001 | I03-AT-001 |
| I03-REQ-002 | I03-DES-002 | I03-PLAN-002 | I03-AC-001, I03-AC-003, I03-AC-004 | I03-AT-001, I03-AT-003, I03-AT-004 |
| I03-REQ-003 | I03-DES-003 | I03-PLAN-003 | I03-AC-001, I03-AC-002, I03-AC-005 | I03-AT-001, I03-AT-002, I03-AT-005 |
| I03-REQ-004 | I03-DES-004 | I03-PLAN-004 | I03-AC-001, I03-AC-005 | I03-AT-001, I03-AT-005 |
| I03-REQ-005 | I03-DES-005 | I03-PLAN-005 | I03-AC-003, I03-AC-006, I03-AC-007 | I03-AT-003, I03-AT-006, I03-AT-007 |
| I03-REQ-006 | I03-DES-006 | I03-PLAN-006 | I03-AC-004, I03-AC-005 | I03-AT-004, I03-AT-005 |
| I03-REQ-007 | I03-DES-007 | I03-PLAN-007 | I03-AC-008 | I03-AT-008 |

### regression boundary

- dependency Issueのacceptance suiteを再実行し、public endpoint/source/schema/manifest/exit contractを破っていないことを確認する。
- target repositoryのHEAD、branch、refs、index、status、tracked/untracked bytesがcommand前後で一致する。
- same-input deterministic rerun、output collision、invalid override、interrupt cleanupを確認する。
- Artifact、diagnostic、stdout/stderr/logをsource body、raw hunk、comment、literal、secret、absolute pathでnegative scanする。
- visual vocabularyはcolorだけでなく記号、line style、legendをgolden/semantic testで検査する。

## rollback

- persistent DB migration は N/A。本 Issue は DB を変更しない。誤解析が見つかった場合は affected pattern を incomplete へ狭める安全な forward fix を優先し、公開済み row kind を削除するときは schema version up を行う。
- rollback trigger: acceptance regression、source execution/mutation、secret/absolute path leak、incorrect successful exit、ambiguous moved の誤採用。
- rollback unit: Issue の production code、tests、schema/doc additionsを一体で revert する。dependency Issue の accepted contract は戻さない。
- forward recovery: unsafe pattern を `incomplete`/`unknown` へ狭め、誤った success を継続しない。既存 Artifact を自動 rewrite しない。
- output migration は N/A。Artifact は immutable run output であり、既存 output を上書きしない。

## exit / handoff

- I03-AC-001〜I03-AC-008 の acceptance evidence が揃う。
- Requirement→Design→Plan→test trace に gap がない。
- planned path honesty を review し、実装時点の実在 path/symbol と差異があれば Design/Plan を先に更新する。
- residual risk、unsupported static pattern、coverage limitation、explicit override を release note と manifest diagnostic contract に残す。
- downstream handoff: ISSUE-01 の common snapshot/output contract を拡張する SQLAlchemy snapshot slice。ISSUE-04 完了までは ER diff を約束しない。
- completion 後も implementation/report の実績は canonical Report に別途記録し、本 Plan を実行ログにしない。
