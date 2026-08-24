---
種別: 実装計画書（Issue）
ID: "iss-00007"
タイトル: "Compare SQLAlchemy ER Changes"
関連GitHub: ["#7"]
package_sequence_key: "ISSUE-04"
状態: "draft"
最終更新: "2026-08-24"
依存: ["requirement.md", "design.md"]
親: ["epic-00002", "init-00001"]
---

# iss-00007 Compare SQLAlchemy ER Changes — 実装計画

詳細: [Issue Plan Guide](../../../../../../docs/authoring/issue-plan.md)

## Planning Level

- **selected level: `strict`**
- 理由: schema review に用いる row-level public contract、redaction、moved matching、intermediate release boundary を導入し、誤判定からの回復コストが高いため strict を選ぶ。
- risk factor: public CLI/schema、static-analysis safety、Artifact integrity、adapter compatibility、誤比較時の広い説明影響。
- `critical` ではない理由: target repository と persistent user data を変更せず、release/commit 単位で戻せる設計である。
- 再評価条件: secret/PII exposure、target mutation、不可逆 data loss、incident response が必要な rollout を追加する場合。

## 目標

coding agent が before/after declarative ORM semantics を比較し、table と column/constraint/index/relationship の row-level delta、ghost removal、影響 context を説明できる。

completion は file/technical layer の完成ではなく、次の observable chain で判定する。

```text
CLI request -> safe source acquisition -> domain semantic analysis
  -> versioned semantic JSON + domain PlantUML -> diagnostic/manifest
  -> acceptance command and exit evidence
```

## 順序・依存

- declared dependency: ISSUE-02, ISSUE-03。
- execution order: I04-PLAN-001 → 002 → 003 → 005 → 004 → 006。shared endpoint/hunk/budget contractを再実装せずconsumer contract testで固定する。
- truth-table fixture、row golden、matching、security scanはdependency contract verification後に並行できる。
- stop condition: row deltas/ghosts、domain presence、start-HEAD anchor、metadata-only hunk、two-level budget、union impactが成立するまでintermediate releaseを宣言しない。

| Plan ID | implementation/verification step | Design trace |
| --- | --- | --- |
| I04-PLAN-001 | I04-AT-001〜010のrow/truth/endpoint/hunk/budget fixturesを先に固定する。 | I04-DES-001 |
| I04-PLAN-002 | ISSUE-02 comparison source contractをconsumeし、ER adapterへimmutable sidesを渡す。 | I04-DES-002 |
| I04-PLAN-003 | canonical empty-side、table/row differ、matching、union impactを実装する。 | I04-DES-003 |
| I04-PLAN-004 | side/table/row/matching/hunkを分離したJSON、ghost PlantUML、manifest publicationを接続する。 | I04-DES-004 |
| I04-PLAN-005 | side failure、changed-path/entity budgets、ambiguityをstatus/exit/publicationへ写像する。 | I04-DES-005 |
| I04-PLAN-006 | DB/import/Git/redaction/determinism/atomicity regressionとintermediate release gateを完了する。 | I04-DES-006 |

## 実装step

### I04-PLAN-001 acceptance-first contract

- table/row deltas、ghost before values、matching、side failure、redaction、impact、five-row presence、working-tree anchor、hunk safety、entity budgetをplanned testsで先に固定する。

### I04-PLAN-002 shared comparison source

planned domain modules（current commit `867ee6929283dfc84711bce245b784d2b8e3e9e6` には未実装）:

- `src/code_structure_viz/adapters/sqlalchemy/differ.py::SqlAlchemySemanticDiffer`
- `matcher.py::SqlAlchemyMoveMatcher`
- `diff_model.py`
- `diff_renderer.py`
- `semantic/impact.py` domain graph extension

ISSUE-02のendpoint/freezer/FileChangeSet/changed-path gateをcontract fixturesでconsumeし、`--to working-tree` onlyのstart HEAD anchorを変更しない。

### I04-PLAN-003 ER presence and semantic diff

- `code-structure-viz.empty-side/v1` domain `sqlalchemy` canonical bytes/digestをgolden固定する。
- before-only/after-onlyは全removed/added、both-absentはnot_applicable、analysis failureはincomplete no affected payload。
- table/typed-row delta、ghost、matching、before/after union impactを実装する。

### I04-PLAN-005 failure and budgets

- run-level changed-path overrunはexit 1/final manifestなし。ER entity overrunはexit 3/affected payloadなし/safe manifest countあり。
- default literalに依存するmatchingを禁止し、ambiguous moveはremoved+added。

### I04-PLAN-004 Artifact publication

- side descriptors/digests、metadata-only FileChangeSet、table/row deltas、redacted before/after、matching、impactをseparate fieldsへserializeする。
- ghost visual vocabulary、no overwrite、fingerprint/integrity gate、final SHA-256を実装する。

### I04-PLAN-006 hardening and intermediate handoff

- DB/import/Git mutation traps、raw patch lines/default/source/secret/path scans、determinism、ISSUE-01〜04 full suite、offline/license/minimum/latest gatesを通し、Python+SQLAlchemy intermediate release evidenceを作る。

## 検証

| Test ID | acceptance behavior | planned file | command |
| --- | --- | --- | --- |
| I04-AT-001 | table/row delta | tests/acceptance/sqlalchemy/test_diff_cli.py | uv run pytest tests/acceptance/sqlalchemy/test_diff_cli.py -q |
| I04-AT-002 | ghost visuals | tests/golden/sqlalchemy/test_row_visuals.py | uv run pytest tests/golden/sqlalchemy/test_row_visuals.py -q |
| I04-AT-003 | matching | tests/integration/sqlalchemy/test_er_matching.py | uv run pytest tests/integration/sqlalchemy/test_er_matching.py -q |
| I04-AT-004 | side failure | tests/acceptance/sqlalchemy/test_diff_failures.py | uv run pytest tests/acceptance/sqlalchemy/test_diff_failures.py -q |
| I04-AT-005 | redaction | tests/security/test_sqlalchemy_diff_redaction.py | uv run pytest tests/security/test_sqlalchemy_diff_redaction.py -q |
| I04-AT-006 | union impact | tests/integration/sqlalchemy/test_er_impact.py | uv run pytest tests/integration/sqlalchemy/test_er_impact.py -q |
| I04-AT-007 | domain presence | tests/acceptance/sqlalchemy/test_diff_domain_presence.py | uv run pytest tests/acceptance/sqlalchemy/test_diff_domain_presence.py -q |
| I04-AT-008 | working-tree anchor | tests/acceptance/sqlalchemy/test_working_tree_anchor.py | uv run pytest tests/acceptance/sqlalchemy/test_working_tree_anchor.py -q |
| I04-AT-009 | hunk safety | tests/security/test_sqlalchemy_diff_hunk_redaction.py | uv run pytest tests/security/test_sqlalchemy_diff_hunk_redaction.py -q |
| I04-AT-010 | entity budget publication | tests/acceptance/sqlalchemy/test_diff_entity_budget.py | uv run pytest tests/acceptance/sqlalchemy/test_diff_entity_budget.py -q |

### issue gate commands

```bash
uv run pytest tests/acceptance/sqlalchemy/test_diff_cli.py -q
uv run pytest tests/golden/sqlalchemy/test_row_visuals.py -q
uv run pytest tests/integration/sqlalchemy/test_er_matching.py -q
uv run pytest tests/acceptance/sqlalchemy/test_diff_failures.py -q
uv run pytest tests/security/test_sqlalchemy_diff_redaction.py -q
uv run pytest tests/integration/sqlalchemy/test_er_impact.py -q
uv run pytest tests/acceptance/sqlalchemy/test_diff_domain_presence.py -q
uv run pytest tests/acceptance/sqlalchemy/test_working_tree_anchor.py -q
uv run pytest tests/security/test_sqlalchemy_diff_hunk_redaction.py -q
uv run pytest tests/acceptance/sqlalchemy/test_diff_entity_budget.py -q
uv run ruff check .
uv run mypy src tests
uv run pytest
```

### Requirement → Design → Plan → acceptance → test trace

| Requirement | Design | Plan | acceptance | test |
| --- | --- | --- | --- | --- |
| I04-REQ-001 | I04-DES-001 | I04-PLAN-001 | I04-AC-001, I04-AC-002 | I04-AT-001, I04-AT-002 |
| I04-REQ-002 | I04-DES-002 | I04-PLAN-002 | I04-AC-008, I04-AC-009 | I04-AT-008, I04-AT-009 |
| I04-REQ-003 | I04-DES-003 | I04-PLAN-003 | I04-AC-001, I04-AC-002, I04-AC-003, I04-AC-006, I04-AC-007 | I04-AT-001, I04-AT-002, I04-AT-003, I04-AT-006, I04-AT-007 |
| I04-REQ-004 | I04-DES-004 | I04-PLAN-004 | I04-AC-001, I04-AC-002, I04-AC-005, I04-AC-009 | I04-AT-001, I04-AT-002, I04-AT-005, I04-AT-009 |
| I04-REQ-005 | I04-DES-005 | I04-PLAN-005 | I04-AC-003, I04-AC-004, I04-AC-007, I04-AC-010 | I04-AT-003, I04-AT-004, I04-AT-007, I04-AT-010 |
| I04-REQ-006 | I04-DES-006 | I04-PLAN-006 | I04-AC-005, I04-AC-009, I04-AC-010 | I04-AT-005, I04-AT-009, I04-AT-010 |

### regression boundary

- dependency Issueのacceptance suiteを再実行し、public endpoint/source/schema/manifest/exit contractを破っていないことを確認する。
- target repositoryのHEAD、branch、refs、index、status、tracked/untracked bytesがcommand前後で一致する。
- same-input deterministic rerun、output collision、invalid override、interrupt cleanupを確認する。
- Artifact、diagnostic、stdout/stderr/logをsource body、raw patch lines、comment、literal、secret、absolute pathでnegative scanする。
- visual vocabularyはcolorだけでなく記号、line style、legendをgolden/semantic testで検査する。

## rollback

- DB migration は実行しないため N/A。誤った row kind/matching は affected analysis を incomplete に狭める forward fix を優先する。intermediate release 後の schema break は version up と compatibility fixture で回復する。
- rollback trigger: acceptance regression、source execution/mutation、secret/absolute path leak、incorrect successful exit、ambiguous moved の誤採用。
- rollback unit: Issue の production code、tests、schema/doc additionsを一体で revert する。dependency Issue の accepted contract は戻さない。
- forward recovery: unsafe pattern を `incomplete`/`unknown` へ狭め、誤った success を継続しない。既存 Artifact を自動 rewrite しない。
- output migration は N/A。Artifact は immutable run output であり、既存 output を上書きしない。

## exit / handoff

- I04-AC-001〜I04-AC-010 の acceptance evidence が揃う。
- Requirement→Design→Plan→test trace に gap がない。
- planned path honesty を review し、実装時点の実在 path/symbol と差異があれば Design/Plan を先に更新する。
- residual risk、unsupported static pattern、coverage limitation、explicit override を release note と manifest diagnostic contract に残す。
- downstream handoff: ISSUE-01〜04 で Python class と SQLAlchemy ER の snapshot/diff が利用可能となる intermediate release milestone。
- completion 後も implementation/report の実績は canonical Report に別途記録し、本 Plan を実行ログにしない。
