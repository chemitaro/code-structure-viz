---
種別: 実装計画書（Issue）
ID: "iss-00005"
タイトル: "Compare Python Structure Changes Safely"
関連GitHub: ["#5"]
package_sequence_key: "ISSUE-02"
状態: "draft"
最終更新: "2026-08-24"
依存: ["requirement.md", "design.md"]
親: ["epic-00002", "init-00001"]
---

# iss-00005 Compare Python Structure Changes Safely — 実装計画

詳細: [Issue Plan Guide](../../../../../../docs/authoring/issue-plan.md)

## Planning Level

- **selected level: `strict`**
- 理由: named endpoint、read-only Git、working-tree freeze、public diff schema、semantic moved 判定を導入し、誤比較の blast radius と契約変更からの回復コストが高いため strict を選ぶ。
- risk factor: public CLI/schema、static-analysis safety、Artifact integrity、adapter compatibility、誤比較時の広い説明影響。
- `critical` ではない理由: target repository と persistent user data を変更せず、release/commit 単位で戻せる設計である。
- 再評価条件: secret/PII exposure、target mutation、不可逆 data loss、incident response が必要な rollout を追加する場合。

## 目標

coding agent が named endpoint で before/after Python semantic snapshot を安全に固定し、意味のある class/member/relation change と影響 context だけを比較できる。

completion は file/technical layer の完成ではなく、次の observable chain で判定する。

```text
CLI request -> safe source acquisition -> domain semantic analysis
  -> versioned semantic JSON + domain PlantUML -> diagnostic/manifest
  -> acceptance command and exit evidence
```

## 順序・依存

- declared dependency: ISSUE-01。
- execution order: I02-PLAN-001 → 002 → 007 → 003 → 005 → 004 → 008 → 006。endpoint/freezeとmetadata-only hunkをsemantic comparison前に固定する。
- fixture authoring、endpoint matrix、empty-side golden、hunk redaction、renderer goldenはI02-PLAN-001後に並行できる。
- stop condition: all endpoint combinations、five-row domain presence、two-level budget、metadata-only hunk、union impact、matching、read-only Gitがacceptanceで成立するまでconsumer diff sliceへhand offしない。

| Plan ID | implementation/verification step | Design trace |
| --- | --- | --- |
| I02-PLAN-001 | I02-AT-001〜010のtable-driven CLI/status/publication fixturesを先に固定する。 | I02-DES-001 |
| I02-PLAN-002 | ComparisonEndpointResolver、WorkingTreeFreezer、ReadOnlyGitRepositoryとstart-HEAD provenanceを実装する。 | I02-DES-002 |
| I02-PLAN-003 | DomainPresenceResolver、canonical empty-side、Python semantic differ/impact/matcherを実装する。 | I02-DES-003 |
| I02-PLAN-004 | side/FileChangeSet/SemanticChangeSetを分離したJSON、PlantUML、manifest publicationを接続する。 | I02-DES-004 |
| I02-PLAN-005 | run-level changed-path gateとdomain-local entity gateをexit/publication matrixへ接続する。 | I02-DES-005 |
| I02-PLAN-006 | read-only/static/redaction/determinism/atomicity/CI/package regressionを完了する。 | I02-DES-006 |
| I02-PLAN-007 | HunkMetadata parser/value/serializerをrange/status/content-independent IDだけに限定しnegative testを通す。 | I02-DES-007 |
| I02-PLAN-008 | stdout selector grammar、stream routing、exact-byte copy、unavailable result、no-selector summary、usage no-publicationを実装・検証する。 | I02-DES-008 |

## 実装step

### I02-PLAN-001 acceptance-first contract

- endpoint matrixにflagなし、from-only、to-ref-only、to-head-only、to-working-tree-only、from+to、invalid from-working-treeを含める。
- five-row domain presence、changed-path/entity budgets、hunk redaction、manifest presence/absenceをexpected file setまで固定する。

### I02-PLAN-002 endpoint and immutable source

planned modules（canonical specification 時点では未実装。実装開始時に HEAD と configured upstream を再検証し、実在 path/symbol と差異があれば Design/Plan を先に更新する）:

- `src/code_structure_viz/source/endpoints.py::ComparisonEndpointResolver`
- `src/code_structure_viz/source/freezer.py::WorkingTreeFreezer`
- `src/code_structure_viz/source/git_repository.py::ReadOnlyGitRepository`
- `src/code_structure_viz/source/source_view.py::SourceView`

`--to working-tree` onlyではfreezeとstart HEAD anchor解決を同じrun-start boundaryで行い、requested endpoint、frozen working-tree digest、start HEAD anchor、selected candidate、merge-base、resolution methodをprovenanceへ記録する。auto fetch/checkout/fallbackは禁止する。

### I02-PLAN-007 metadata-only FileChangeSet

- `src/code_structure_viz/source/file_changes.py::FileChangeSet`、`HunkMetadata`をplanned targetとする。
- Git diff streamからold/new ranges/status/ordinalを抽出し、content-independent canonical metadata SHA-256を`hunk_id`にする。raw patch/context/added/deleted linesをvalue objectへ保存しない。
- secret-like patch fixtureでArtifact、manifest、diagnostic、stdout/stderr、logをnegative scanする。

### I02-PLAN-003 domain presence and Python semantic diff

- `src/code_structure_viz/semantic/diff.py::DomainPresenceResolver`、`CanonicalEmptySide`、`SemanticDiffer`、`ImpactExplorer`、Python matcherをplanned targetとする。
- absent/absent=not_applicable、real/empty=all removed、empty/real=all added、analysis failure=incomplete no affected payloadを実装する。
- empty-side canonical bytes/digestをdomain/versionごとにgolden固定しstandalone publishしない。

### I02-PLAN-005 budget and failure mapping

- implicit changed paths default 1,000をdomain fan-out前に検査し、overrunはexit 1/diagnostic only/final manifestなし。
- Python diagram entities default 500をrender前に検査し、overrunはexit 3/affected payloadなし/safe manifestあり。valid overridesはrequested/resolved/count、invalid valuesはexit 2。

### I02-PLAN-004 Artifact publication

- side descriptors/digests、metadata-only FileChangeSet、SemanticChangeSet、seed、union impact、matching evidenceを別fieldでserializeする。
- staging/collision/fingerprint/integrity gate後にpublishし、run fatalでは全stagingを破棄、domain incompleteではsafe manifestのみpublishする。

### I02-PLAN-008 stdout selector and stream contract

- CLI parserは`--stdout`を高々1回だけ受理し、`manifest | DOMAIN:FORMAT`のclosed grammar、selected domain、requested formatをsource acquisition前に検証する。invalid/duplicate/unselected/unrequestedはexit 2、stdout空、Artifactなしとする。
- publication後はavailable selectorの公開fileをexact bytesで複製する。unavailable selectorは`stdout-result/v1` 1行、selectorなしは`run-summary/v1` 1行をcanonical key orderで出す。diagnosticはstderrだけへ出し、`--output-dir` publicationを維持する。
- complete、not_applicable、payload_unavailable、run fatal、handled interrupt、manifest unavailableをtable-driven fixtureで固定し、side failureが`partial_safe`にならないこととsource/secret/absolute pathがstdoutへ漏れないことをnegative scanする。

### I02-PLAN-006 hardening and handoff

- read-only Git allowlist、refs/index/worktree byte equality、static execution trap、same-input output equality、minimum/latest/offline/license regressionを通す。
- shared contract fixturesをISSUE-04/06/07がconsumeできる形でversioned docs/testsへhand offする。

## 検証

| Test ID | acceptance behavior | planned file | command |
| --- | --- | --- | --- |
| I02-AT-001 | endpoint matrix and start-HEAD anchor | tests/acceptance/python/test_diff_cli.py | uv run pytest tests/acceptance/python/test_diff_cli.py -q |
| I02-AT-002 | union impact | tests/integration/python/test_impact_union_graph.py | uv run pytest tests/integration/python/test_impact_union_graph.py -q |
| I02-AT-003 | fail closed | tests/acceptance/git/test_diff_fail_closed.py | uv run pytest tests/acceptance/git/test_diff_fail_closed.py -q |
| I02-AT-004 | Git immutability | tests/security/test_git_read_only.py | uv run pytest tests/security/test_git_read_only.py -q |
| I02-AT-005 | semantic seeds | tests/acceptance/python/test_semantic_seed.py | uv run pytest tests/acceptance/python/test_semantic_seed.py -q |
| I02-AT-006 | move matching | tests/integration/python/test_move_matching.py | uv run pytest tests/integration/python/test_move_matching.py -q |
| I02-AT-007 | changed-path admission | tests/acceptance/git/test_changed_path_budget.py | uv run pytest tests/acceptance/git/test_changed_path_budget.py -q |
| I02-AT-008 | domain presence/empty-side | tests/acceptance/python/test_domain_presence_diff.py | uv run pytest tests/acceptance/python/test_domain_presence_diff.py -q |
| I02-AT-009 | hunk redaction | tests/security/test_file_change_hunk_redaction.py | uv run pytest tests/security/test_file_change_hunk_redaction.py -q |
| I02-AT-010 | entity budget publication | tests/acceptance/python/test_diff_entity_budget.py | uv run pytest tests/acceptance/python/test_diff_entity_budget.py -q |
| I02-AT-011 | stdout selector matrix | tests/acceptance/python/test_stdout_selector.py | uv run pytest tests/acceptance/python/test_stdout_selector.py -q |

### issue gate commands

```bash
uv run pytest tests/acceptance/python/test_diff_cli.py -q
uv run pytest tests/integration/python/test_impact_union_graph.py -q
uv run pytest tests/acceptance/git/test_diff_fail_closed.py -q
uv run pytest tests/security/test_git_read_only.py -q
uv run pytest tests/acceptance/python/test_semantic_seed.py -q
uv run pytest tests/integration/python/test_move_matching.py -q
uv run pytest tests/acceptance/git/test_changed_path_budget.py -q
uv run pytest tests/acceptance/python/test_domain_presence_diff.py -q
uv run pytest tests/security/test_file_change_hunk_redaction.py -q
uv run pytest tests/acceptance/python/test_diff_entity_budget.py -q
uv run pytest tests/acceptance/python/test_stdout_selector.py -q
uv run ruff check .
uv run mypy src tests
uv run pytest
```

### Requirement → Design → Plan → acceptance → test trace

| Requirement | Design | Plan | acceptance | test |
| --- | --- | --- | --- | --- |
| I02-REQ-001 | I02-DES-001 | I02-PLAN-001 | I02-AC-001, I02-AC-002 | I02-AT-001, I02-AT-002 |
| I02-REQ-002 | I02-DES-002 | I02-PLAN-002 | I02-AC-001, I02-AC-003, I02-AC-004 | I02-AT-001, I02-AT-003, I02-AT-004 |
| I02-REQ-003 | I02-DES-003 | I02-PLAN-003 | I02-AC-002, I02-AC-005, I02-AC-008 | I02-AT-002, I02-AT-005, I02-AT-008 |
| I02-REQ-004 | I02-DES-004 | I02-PLAN-004 | I02-AC-001, I02-AC-008, I02-AC-009 | I02-AT-001, I02-AT-008, I02-AT-009 |
| I02-REQ-005 | I02-DES-005 | I02-PLAN-005 | I02-AC-003, I02-AC-007, I02-AC-008, I02-AC-010 | I02-AT-003, I02-AT-007, I02-AT-008, I02-AT-010 |
| I02-REQ-006 | I02-DES-006 | I02-PLAN-006 | I02-AC-004, I02-AC-005, I02-AC-006, I02-AC-009 | I02-AT-004, I02-AT-005, I02-AT-006, I02-AT-009 |
| I02-REQ-007 | I02-DES-007 | I02-PLAN-007 | I02-AC-007, I02-AC-009 | I02-AT-007, I02-AT-009 |
| I02-REQ-008 | I02-DES-008 | I02-PLAN-008 | I02-AC-011 | I02-AT-011 |

### regression boundary

- dependency Issueのacceptance suiteを再実行し、public endpoint/source/schema/manifest/exit contractを破っていないことを確認する。
- target repositoryのHEAD、branch、refs、index、status、tracked/untracked bytesがcommand前後で一致する。
- same-input deterministic rerun、output collision、invalid override、interrupt cleanupを確認する。
- Artifact、diagnostic、stdout/stderr/logをsource body、raw patch lines、comment、literal、secret、absolute pathでnegative scanする。
- visual vocabularyはcolorだけでなく記号、line style、legendをgolden/semantic testで検査する。

## rollback

- persistent migration は N/A。fingerprint や endpoint contract に不具合があれば release を停止して Issue 全体を revert する。公開済み schema は旧 snapshot digest を読める additive correction または schema version up で forward recovery する。
- rollback trigger: acceptance regression、source execution/mutation、secret/absolute path leak、incorrect successful exit、ambiguous moved の誤採用。
- rollback unit: Issue の production code、tests、schema/doc additionsを一体で revert する。dependency Issue の accepted contract は戻さない。
- forward recovery: unsafe pattern を `incomplete`/`unknown` へ狭め、誤った success を継続しない。既存 Artifact を自動 rewrite しない。
- output migration は N/A。Artifact は immutable run output であり、既存 output を上書きしない。

## exit / handoff

- I02-AC-001〜I02-AC-011 の acceptance evidence が揃う。
- Requirement→Design→Plan→test trace に gap がない。
- planned path honesty を review し、実装時点の実在 path/symbol と差異があれば Design/Plan を先に更新する。
- residual risk、unsupported static pattern、coverage limitation、explicit override を release note と manifest diagnostic contract に残す。
- downstream handoff: ISSUE-01 と合わせて Python domain preview。Git comparison foundation は後続 domain diff が再利用するが、Python 固有 matching は adapter 内に残す。
- completion 後も implementation/report の実績は canonical Report に別途記録し、本 Plan を実行ログにしない。
