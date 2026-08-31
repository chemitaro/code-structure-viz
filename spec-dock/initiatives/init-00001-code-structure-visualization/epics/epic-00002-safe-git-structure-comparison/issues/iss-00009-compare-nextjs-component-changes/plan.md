---
種別: 実装計画書（Issue）
ID: "iss-00009"
タイトル: "Compare Next.js Component Changes"
関連GitHub: ["#9"]
package_sequence_key: "ISSUE-06"
状態: "draft"
最終更新: "2026-08-31"
依存: ["requirement.md", "design.md"]
親: ["epic-00002", "init-00001"]
---

# iss-00009 Compare Next.js Component Changes — 実装計画

詳細: [Issue Plan Guide](../../../../../../docs/authoring/issue-plan.md)

## Planning Level

- **selected level: `strict`**
- 理由: cross-runtime dual snapshot、component moved、member-level visual contract、unknown behavior policy を公開し、誤比較の回復コストが高いため strict を選ぶ。
- risk factor: public CLI/schema、static-analysis safety、Artifact integrity、adapter compatibility、誤比較時の広い説明影響。
- `critical` ではない理由: target repository と persistent user data を変更せず、release/commit 単位で戻せる設計である。
- 再評価条件: secret/PII exposure、target mutation、不可逆 data loss、incident response が必要な rollout を追加する場合。

## 目標

coding agent が before/after Next.js semantic snapshot から component/props/import/render/boundary change と影響 context を比較できる。

completion は file/technical layer の完成ではなく、次の observable chain で判定する。

```text
CLI request -> safe source acquisition -> domain semantic analysis
  -> versioned semantic JSON + domain PlantUML -> diagnostic/manifest
  -> acceptance command and exit evidence
```

## 順序・依存

- declared dependency: ISSUE-02, ISSUE-05。
- execution order: I06-PLAN-001 → 002 → 003 → 005 → 004 → 007 → 006。shared endpoint/hunk/budget contractとadapter protocolをconsumer fixturesで先に固定する。
- presence/matching/impact/renderer/security fixturesはdependency contract verification後に並行できる。
- stop condition: Next presence truth table、start-HEAD anchor、metadata-only hunk、two-level budget、static semantic diff/unknownが成立するまでall-domainへhand offしない。

| Plan ID | implementation/verification step | Design trace |
| --- | --- | --- |
| I06-PLAN-001 | I06-AT-001〜010のsemantic/truth/endpoint/hunk/budget fixturesを先に固定する。 | I06-DES-001 |
| I06-PLAN-002 | ISSUE-02 source contractとISSUE-05 adapterを両sideへ接続する。 | I06-DES-002 |
| I06-PLAN-003 | canonical empty-side、Next differ/matcher/union impactを実装する。 | I06-DES-003 |
| I06-PLAN-004 | side/adapter/semantic/hunkを分離したJSON、PlantUML、manifest publicationを接続する。 | I06-DES-004 |
| I06-PLAN-005 | side failure、changed-path/entity budgets、ambiguity/unknownをstatus/exit/publicationへ写像する。 | I06-DES-005 |
| I06-PLAN-006 | build非実行、Git/hunk/source redaction、determinism、Node/package/CI regressionを完了する。 | I06-DES-006 |
| I06-PLAN-007 | stdout selector grammar、stream routing、exact-byte copy、unavailable result、no-selector summary、usage no-publicationを実装・検証する。 | I06-DES-007 |

## 実装step

### I06-PLAN-001 acceptance-first contract

- declaration Component/member/primitive relation delta、ExportBinding、derived role、seed、matching、side failure、impact、dynamic unknown、five-row presence、working-tree anchor、hunk safety、entity budgetをplanned testsで先に固定する。
- barrel移動、export alias変更、default/named再公開ではExportBindingだけが変化し、同じdeclaration Componentをremoved/addedにしないfixtureを先に固定する。FactDelta/MemberDelta/RelationDeltaを別collectionで検証する。

### I06-PLAN-002 shared source and adapter

planned modules（canonical specification 時点では未実装。実装開始時に HEAD と configured upstream を再検証し、実在 path/symbol と差異があれば Design/Plan を先に更新する）:

- `adapters/next/src/diff.ts::diffNextSnapshots`
- `adapters/next/src/matcher.ts::matchMovedComponents`
- `adapters/next/src/diff-render.ts`
- `src/code_structure_viz/adapters/next/diff_bridge.py`
- `src/code_structure_viz/semantic/impact.py` Next relation extension

ISSUE-02 endpoint/freezer/FileChangeSet/changed-path gateとISSUE-05 `SourceAcquisitionPlan/v1`、`domain_config_projection("next")`/digest、TrustedTypeEnvironment、adapter request/response protocolを両sideで独立にconsumeする。diffのrepeatable `--project`/`--target`を両sideへ同じnormalized selectionとして渡す。`--to working-tree` onlyのrequested endpoint、frozen digest、start HEAD anchor、selected candidate、merge-base、resolution methodをprovenanceへ記録する。

### I06-PLAN-003 Next presence and semantic diff

- canonical empty-side domain `next` bytes/digestをgolden固定する。
- `domain_absent|real_snapshot|target_resolution_failed|analysis_failed`のcross-productを固定し、domain absenceだけをempty-sideへ写像する。target/config/adapter/protocol failureはincomplete no payload。
- side semantic compatibility IDのexact/mismatch、environment/adapter version差、config/source plan差をmatrixで固定する。
- exact declaration identityを最優先し、片側にexact identityがない場合だけhigh-confidence unique candidateをmovedにする。ExportBinding、route、range、order、diagnostic、derived boundary roleをmatching key/evidenceにしない。
- Component、ExportBinding、Prop、primitive relationをprimary seed、derived boundary roleを再計算contextとして扱い、union impactとunknown dynamic behaviorを実装する。

### I06-PLAN-005 failure and budgets

- run-level changed-path overrunはexit 1/final manifestなし。Next entity overrunはexit 3/affected payloadなし/safe manifest countあり。
- adapter/config/protocol failureをabsenceへ変換せず、ambiguous moveをremoved+addedにする。

### I06-PLAN-004 Artifact publication

- side/adapter descriptors、metadata-only FileChangeSet、semantic changes、impact、matching、coverageをseparate fieldsへserializeする。
- source/raw patch lines/comment/literal/secret/absolute pathをbridge/adapter/Artifact/logへ渡さない。

### I06-PLAN-007 stdout selector and stream contract

- CLI parserは`--stdout`を高々1回だけ受理し、`manifest | DOMAIN:FORMAT`のclosed grammar、selected domain、requested formatをsource acquisition前に検証する。invalid/duplicate/unselected/unrequestedはexit 2、stdout空、Artifactなしとする。
- publication後はavailable selectorの公開fileをexact bytesで複製する。unavailable selectorは`stdout-result/v1` 1行、selectorなしは`run-summary/v1` 1行をcanonical key orderで出す。diagnosticはstderrだけへ出し、`--output-dir` publicationを維持する。
- complete、not_applicable、payload_unavailable、run fatal、handled interrupt、manifest unavailableをtable-driven fixtureで固定し、side failureが`partial_safe`にならないこととsource/secret/absolute pathがstdoutへ漏れないことをnegative scanする。

### I06-PLAN-006 hardening and handoff

- Git/build/plugin traps、hunk/source redaction、same-input output equality、Node 22/latest、offline npm/lock/license、dependency suitesを通してISSUE-07へhand offする。

## 検証

| Test ID | acceptance behavior | planned file | command |
| --- | --- | --- | --- |
| I06-AT-001 | Next diff | tests/acceptance/next/test_diff_cli.py | uv run pytest tests/acceptance/next/test_diff_cli.py -q |
| I06-AT-002 | declaration/export/primitive semantic seedsとderived role非primary | tests/acceptance/next/test_semantic_seed.py | uv run pytest tests/acceptance/next/test_semantic_seed.py -q |
| I06-AT-003 | declaration exact identity、barrel/alias/default-named binding、high-confidence moved | tests/integration/next/test_component_matching.py | uv run pytest tests/integration/next/test_component_matching.py -q |
| I06-AT-004 | side presence/failure/compatibility | tests/acceptance/next/test_diff_failures.py | uv run pytest tests/acceptance/next/test_diff_failures.py -q |
| I06-AT-005 | primitive union impactとderived boundary cascade | tests/integration/next/test_component_impact.py | uv run pytest tests/integration/next/test_component_impact.py -q |
| I06-AT-006 | unknown dynamic | adapters/next/test/dynamic-unknown.test.ts | npm --prefix adapters/next test -- dynamic-unknown |
| I06-AT-007 | SidePresence cross-product + project/target | tests/acceptance/next/test_diff_domain_presence.py | uv run pytest tests/acceptance/next/test_diff_domain_presence.py -q |
| I06-AT-008 | working-tree anchor | tests/acceptance/next/test_working_tree_anchor.py | uv run pytest tests/acceptance/next/test_working_tree_anchor.py -q |
| I06-AT-009 | hunk safety | tests/security/test_next_diff_hunk_redaction.py | uv run pytest tests/security/test_next_diff_hunk_redaction.py -q |
| I06-AT-010 | entity budget publication | tests/acceptance/next/test_diff_entity_budget.py | uv run pytest tests/acceptance/next/test_diff_entity_budget.py -q |
| I06-AT-011 | next diff 1,001-path fatal and valid override provenance | tests/acceptance/next/test_diff_changed_path_admission.py | uv run pytest tests/acceptance/next/test_diff_changed_path_admission.py -q |
| I06-AT-012 | stdout selector matrix | tests/acceptance/next/test_stdout_selector.py | uv run pytest tests/acceptance/next/test_stdout_selector.py -q |

### issue gate commands

```bash
uv run pytest tests/acceptance/next/test_diff_cli.py -q
uv run pytest tests/acceptance/next/test_semantic_seed.py -q
uv run pytest tests/integration/next/test_component_matching.py -q
uv run pytest tests/acceptance/next/test_diff_failures.py -q
uv run pytest tests/integration/next/test_component_impact.py -q
npm --prefix adapters/next test -- dynamic-unknown
uv run pytest tests/acceptance/next/test_diff_domain_presence.py -q
uv run pytest tests/acceptance/next/test_working_tree_anchor.py -q
uv run pytest tests/security/test_next_diff_hunk_redaction.py -q
uv run pytest tests/acceptance/next/test_diff_entity_budget.py -q
uv run pytest tests/acceptance/next/test_diff_changed_path_admission.py -q
uv run pytest tests/acceptance/next/test_stdout_selector.py -q
uv run ruff check .
uv run mypy src tests
uv run pytest
```

### Requirement → Design → Plan → acceptance → test trace

| Requirement | Design | Plan | acceptance | test |
| --- | --- | --- | --- | --- |
| I06-REQ-001 | I06-DES-001 | I06-PLAN-001 | I06-AC-001, I06-AC-002 | I06-AT-001, I06-AT-002 |
| I06-REQ-002 | I06-DES-002 | I06-PLAN-002 | I06-AC-008, I06-AC-009, I06-AC-011 | I06-AT-008, I06-AT-009, I06-AT-011 |
| I06-REQ-003 | I06-DES-003 | I06-PLAN-003 | I06-AC-001, I06-AC-002, I06-AC-003, I06-AC-005, I06-AC-006, I06-AC-007 | I06-AT-001, I06-AT-002, I06-AT-003, I06-AT-005, I06-AT-006, I06-AT-007 |
| I06-REQ-004 | I06-DES-004 | I06-PLAN-004 | I06-AC-001, I06-AC-005, I06-AC-009 | I06-AT-001, I06-AT-005, I06-AT-009 |
| I06-REQ-005 | I06-DES-005 | I06-PLAN-005 | I06-AC-003, I06-AC-004, I06-AC-007, I06-AC-010 | I06-AT-003, I06-AT-004, I06-AT-007, I06-AT-010 |
| I06-REQ-006 | I06-DES-006 | I06-PLAN-006 | I06-AC-006, I06-AC-009, I06-AC-010 | I06-AT-006, I06-AT-009, I06-AT-010 |
| I06-REQ-007 | I06-DES-007 | I06-PLAN-007 | I06-AC-012 | I06-AT-012 |

### regression boundary

- dependency Issueのacceptance suiteを再実行し、public endpoint/source/schema/manifest/exit contractを破っていないことを確認する。
- target repositoryのHEAD、branch、refs、index、status、tracked/untracked bytesがcommand前後で一致する。
- same-input deterministic rerun、output collision、invalid override、interrupt cleanupを確認する。
- Artifact、diagnostic、stdout/stderr/logをsource body、raw patch lines、comment、literal、secret、absolute pathでnegative scanする。
- visual vocabularyはcolorだけでなく記号、line style、legendをgolden/semantic testで検査する。

## rollback

- persistent migration は N/A。adapter diff failure は domain incomplete へ隔離する。公開 contract の誤りは旧 reader/golden fixture を保持した additive fix、または adapter/semantic schema version up で回復する。
- rollback trigger: acceptance regression、source execution/mutation、secret/absolute path leak、incorrect successful exit、ambiguous moved の誤採用。
- rollback unit: Issue の production code、tests、schema/doc additionsを一体で revert する。dependency Issue の accepted contract は戻さない。
- forward recovery: unsafe pattern を `incomplete`/`unknown` へ狭め、誤った success を継続しない。既存 Artifact を自動 rewrite しない。
- output migration は N/A。Artifact は immutable run output であり、既存 output を上書きしない。

## exit / handoff

- I06-AC-001〜I06-AC-012 の acceptance evidence が揃う。
- Requirement→Design→Plan→test trace に gap がない。
- planned path honesty を review し、実装時点の実在 path/symbol と差異があれば Design/Plan を先に更新する。
- residual risk、unsupported static pattern、coverage limitation、explicit override を release note と manifest diagnostic contract に残す。
- downstream handoff: Next domain diff preview。ISSUE-07 の統合前でも `--domain next` の単独利用が可能な acceptance boundary。
- completion 後も implementation/report の実績は canonical Report に別途記録し、本 Plan を実行ログにしない。
