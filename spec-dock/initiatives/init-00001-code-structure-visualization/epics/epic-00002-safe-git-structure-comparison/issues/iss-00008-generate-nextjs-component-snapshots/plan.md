---
種別: 実装計画書（Issue）
ID: "iss-00008"
タイトル: "Generate Next.js Component Snapshots"
関連GitHub: ["#8"]
package_sequence_key: "ISSUE-05"
状態: "draft"
最終更新: "2026-08-24"
依存: ["requirement.md", "design.md"]
親: ["epic-00002", "init-00001"]
---

# iss-00008 Generate Next.js Component Snapshots — 実装計画

詳細: [Issue Plan Guide](../../../../../../docs/authoring/issue-plan.md)

## Planning Level

- **selected level: `strict`**
- 理由: cross-runtime versioned protocol、optional dependency、TypeScript semantic boundary、static-analysis security contract を導入し、compatibility failure の回復が難しいため strict を選ぶ。
- risk factor: public CLI/schema、static-analysis safety、Artifact integrity、adapter compatibility、誤比較時の広い説明影響。
- `critical` ではない理由: target repository と persistent user data を変更せず、release/commit 単位で戻せる設計である。
- 再評価条件: secret/PII exposure、target mutation、不可逆 data loss、incident response が必要な rollout を追加する場合。

## 目標

coding agent が first-party TypeScript adapter を通じ、Next.js repository の module、exported component、props、static relation、client boundary を JSON と PlantUML で取得できる。

completion は file/technical layer の完成ではなく、次の observable chain で判定する。

```text
CLI request -> safe source acquisition -> domain semantic analysis
  -> versioned semantic JSON + domain PlantUML -> diagnostic/manifest
  -> acceptance command and exit evidence
```

## 順序・依存

- declared dependency: ISSUE-01。
- execution order: I05-PLAN-001 → 002 → 003 → 005 → 004 → 007 → 006。Node optionality/applicabilityをprocess起動前に固定する。
- TypeScript fixtures、protocol golden、renderer golden、security trapsはcontract固定後に並行できる。
- stop condition: adapter protocol、static semantics、not_applicable/incomplete、entity budget、optional Node、determinismが成立するまでNext diffへ進まない。

| Plan ID | implementation/verification step | Design trace |
| --- | --- | --- |
| I05-PLAN-001 | I05-AT-001〜007のprotocol/status/publication fixturesを先に固定する。 | I05-DES-001 |
| I05-PLAN-002 | Python bridge、versioned protocol、first-party TypeScript adapter process boundaryを実装する。 | I05-DES-002 |
| I05-PLAN-003 | Next module/component/props/static relation/client-boundary canonical modelを実装する。 | I05-DES-003 |
| I05-PLAN-004 | adapter response validation、semantic JSON、PlantUML、manifest publicationを接続する。 | I05-DES-004 |
| I05-PLAN-005 | dynamic unknown、protocol/static failure、entity gateをstatus/exit/publicationへ接続する。 | I05-DES-005 |
| I05-PLAN-006 | build非実行、redaction、determinism、Node optionality、lock/license/offline/CIを完了する。 | I05-DES-006 |
| I05-PLAN-007 | stdout selector grammar、stream routing、exact-byte copy、unavailable result、no-selector summary、usage no-publicationを実装・検証する。 | I05-DES-007 |

## 実装step

### I05-PLAN-001 acceptance-first contract

- App/Pages Router、protocol、safe JS/JSX、Node/protocol failures、static safety、no-target optionality、entity budgetとsnapshotへの`--max-changed-paths` rejection fixturesを先に固定する。

### I05-PLAN-002 bridge and adapter boundary

planned modules（canonical specification 時点では未実装。実装開始時に HEAD と configured upstream を再検証し、実在 path/symbol と差異があれば Design/Plan を先に更新する）:

- `src/code_structure_viz/adapters/next/bridge.py::NextAdapterBridge`
- `src/code_structure_viz/adapters/next/protocol.py`
- `adapters/next/package.json`、`package-lock.json`、`tsconfig.json`
- `adapters/next/src/analyze.ts::analyzeRepository`

static target evidence不在ではNode processを起動しない。stdin/stdout exact one JSON、version/schema validation、stderr diagnostic separationを実装する。

### I05-PLAN-003 Next semantic model

- `adapters/next/src/model.ts`をplanned targetとし、module path+exported name identity、props、static/literal-dynamic imports、JSX render、use-client boundary、alias resolutionをcanonicalizeする。
- nonliteral dynamic behaviorはunknown coverageでruntime treeを生成しない。

### I05-PLAN-005 failure and entity gate

- target evidenceありのNode/config/protocol/static-analysis failureをincompleteにし、not_applicableへ変換しない。
- default 500 overrunはexit 3/affected payloadなし/safe manifest countあり、valid overrideはnormal、invalid valueはexit 2。

### I05-PLAN-004 Artifact publication

- validated adapter responseをdomain `next` semantic/v1へmapし、Next PlantUML、coverage/diagnostic、manifest descriptorをOutputTransactionへ接続する。
- literal/source/absolute path/protocol noiseをpublish前にrejectする。

### I05-PLAN-007 stdout selector and stream contract

- CLI parserは`--stdout`を高々1回だけ受理し、`manifest | DOMAIN:FORMAT`のclosed grammar、selected domain、requested formatをsource acquisition前に検証する。invalid/duplicate/unselected/unrequestedはexit 2、stdout空、Artifactなしとする。
- publication後はavailable selectorの公開fileをexact bytesで複製する。unavailable selectorは`stdout-result/v1` 1行、selectorなしは`run-summary/v1` 1行をcanonical key orderで出す。diagnosticはstderrだけへ出し、`--output-dir` publicationを維持する。
- complete、not_applicable、partial_safe、payload_unavailable、run fatal、handled interrupt、manifest unavailableをtable-driven fixtureで固定し、source/secret/absolute pathがstdoutへ漏れないことをnegative scanする。

### I05-PLAN-006 hardening and handoff

- build/config/plugin/application execution traps、same-input adapter/output equality、core-only install without Node、Next-enabled offline npm/lock/license、Node 22/latest CIを通してISSUE-06へhand offする。

## 検証

| Test ID | acceptance behavior | planned file | command |
| --- | --- | --- | --- |
| I05-AT-001 | Next snapshot | tests/acceptance/next/test_snapshot_cli.py | uv run pytest tests/acceptance/next/test_snapshot_cli.py -q |
| I05-AT-002 | adapter protocol | tests/contracts/next/test_adapter_protocol.py | uv run pytest tests/contracts/next/test_adapter_protocol.py -q |
| I05-AT-003 | safe subset | adapters/next/test/safe-subset.test.ts | npm --prefix adapters/next test -- safe-subset |
| I05-AT-004 | partial_safe/payload_unavailable adapter matrix | tests/acceptance/next/test_adapter_failures.py | uv run pytest tests/acceptance/next/test_adapter_failures.py -q |
| I05-AT-005 | static/redaction | tests/security/test_next_static_boundary.py | uv run pytest tests/security/test_next_static_boundary.py -q |
| I05-AT-006 | Node optionality | tests/acceptance/next/test_optionality.py | uv run pytest tests/acceptance/next/test_optionality.py -q |
| I05-AT-007 | entity budget publication and diff-only option rejection | tests/acceptance/next/test_snapshot_budget.py | uv run pytest tests/acceptance/next/test_snapshot_budget.py -q |
| I05-AT-008 | stdout selector matrix | tests/acceptance/next/test_stdout_selector.py | uv run pytest tests/acceptance/next/test_stdout_selector.py -q |

### issue gate commands

```bash
uv run pytest tests/acceptance/next/test_snapshot_cli.py -q
uv run pytest tests/contracts/next/test_adapter_protocol.py -q
npm --prefix adapters/next test -- safe-subset
uv run pytest tests/acceptance/next/test_adapter_failures.py -q
uv run pytest tests/security/test_next_static_boundary.py -q
uv run pytest tests/acceptance/next/test_optionality.py -q
uv run pytest tests/acceptance/next/test_snapshot_budget.py -q
uv run pytest tests/acceptance/next/test_stdout_selector.py -q
uv run ruff check .
uv run mypy src tests
uv run pytest
```

### Requirement → Design → Plan → acceptance → test trace

| Requirement | Design | Plan | acceptance | test |
| --- | --- | --- | --- | --- |
| I05-REQ-001 | I05-DES-001 | I05-PLAN-001 | I05-AC-001 | I05-AT-001 |
| I05-REQ-002 | I05-DES-002 | I05-PLAN-002 | I05-AC-002, I05-AC-004, I05-AC-006 | I05-AT-002, I05-AT-004, I05-AT-006 |
| I05-REQ-003 | I05-DES-003 | I05-PLAN-003 | I05-AC-001, I05-AC-003 | I05-AT-001, I05-AT-003 |
| I05-REQ-004 | I05-DES-004 | I05-PLAN-004 | I05-AC-001, I05-AC-002 | I05-AT-001, I05-AT-002 |
| I05-REQ-005 | I05-DES-005 | I05-PLAN-005 | I05-AC-003, I05-AC-004, I05-AC-007 | I05-AT-003, I05-AT-004, I05-AT-007 |
| I05-REQ-006 | I05-DES-006 | I05-PLAN-006 | I05-AC-005, I05-AC-006 | I05-AT-005, I05-AT-006 |
| I05-REQ-007 | I05-DES-007 | I05-PLAN-007 | I05-AC-008 | I05-AT-008 |

### regression boundary

- dependency Issueのacceptance suiteを再実行し、public endpoint/source/schema/manifest/exit contractを破っていないことを確認する。
- target repositoryのHEAD、branch、refs、index、status、tracked/untracked bytesがcommand前後で一致する。
- same-input deterministic rerun、output collision、invalid override、interrupt cleanupを確認する。
- Artifact、diagnostic、stdout/stderr/logをsource body、raw hunk、comment、literal、secret、absolute pathでnegative scanする。
- visual vocabularyはcolorだけでなく記号、line style、legendをgolden/semantic testで検査する。

## rollback

- data migration は N/A。Node adapter release は Python package と互換 matrix を固定する。protocol mismatch は adapter を incomplete として隔離し、旧 protocol reader を保持した additive fix または version up で forward recovery する。
- rollback trigger: acceptance regression、source execution/mutation、secret/absolute path leak、incorrect successful exit、ambiguous moved の誤採用。
- rollback unit: Issue の production code、tests、schema/doc additionsを一体で revert する。dependency Issue の accepted contract は戻さない。
- forward recovery: unsafe pattern を `incomplete`/`unknown` へ狭め、誤った success を継続しない。既存 Artifact を自動 rewrite しない。
- output migration は N/A。Artifact は immutable run output であり、既存 output を上書きしない。

## exit / handoff

- I05-AC-001〜I05-AC-008 の acceptance evidence が揃う。
- Requirement→Design→Plan→test trace に gap がない。
- planned path honesty を review し、実装時点の実在 path/symbol と差異があれば Design/Plan を先に更新する。
- residual risk、unsupported static pattern、coverage limitation、explicit override を release note と manifest diagnostic contract に残す。
- downstream handoff: Next snapshot preview。Python/SQLAlchemy の install/runtime requirement へ Node を持ち込まない optional adapter separation を完成させる。
- completion 後も implementation/report の実績は canonical Report に別途記録し、本 Plan を実行ログにしない。
