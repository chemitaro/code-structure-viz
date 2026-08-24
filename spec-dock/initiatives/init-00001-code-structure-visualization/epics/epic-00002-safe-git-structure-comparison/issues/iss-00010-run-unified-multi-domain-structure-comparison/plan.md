---
種別: 実装計画書（Issue）
ID: "iss-00010"
タイトル: "Run Unified Multi-Domain Structure Comparison"
関連GitHub: ["#10"]
package_sequence_key: "ISSUE-07"
状態: "draft"
最終更新: "2026-08-24"
依存: ["requirement.md", "design.md"]
親: ["epic-00002", "init-00001"]
---

# iss-00010 Run Unified Multi-Domain Structure Comparison — 実装計画

詳細: [Issue Plan Guide](../../../../../../docs/authoring/issue-plan.md)

## Planning Level

- **selected level: `strict`**
- 理由: 複数 adapter の failure isolation、atomic output、aggregate manifest、public exit code、cross-platform packaging を統合し、運用上の blast radius と回復難度が高いため strict を選ぶ。
- risk factor: public CLI/schema、static-analysis safety、Artifact integrity、adapter compatibility、誤比較時の広い説明影響。
- `critical` ではない理由: target repository と persistent user data を変更せず、release/commit 単位で戻せる設計である。
- 再評価条件: secret/PII exposure、target mutation、不可逆 data loss、incident response が必要な rollout を追加する場合。

## 目標

coding agent が domain を省略した一回の command で Python、SQLAlchemy、Next の適用可否・成功・不完全を区別し、成功 Artifact を保持した集約 manifest と正しい exit code を得られる。

completion は file/technical layer の完成ではなく、次の observable chain で判定する。

```text
CLI request -> safe source acquisition -> domain semantic analysis
  -> versioned semantic JSON + domain PlantUML -> diagnostic/manifest
  -> acceptance command and exit evidence
```

## 順序・依存

- declared dependency: ISSUE-04, ISSUE-06。
- execution order: I07-PLAN-001 → 002 → 003 → 005 → 004 → 007 → 006。per-domain result ownershipとrun/domain failure boundaryを先に固定する。
- multi-domain fixtures、manifest schema examples、package/CI lanesはdependency contract verification後に並行できる。
- stop condition: per-domain-only semantic output、aggregate run-manifest/v1、cross-domain presence/budget matrix、partial success、endpoint/hunk safety、atomicity、platform/package traceが成立するまでInitiativeをcompleteにしない。

| Plan ID | implementation/verification step | Design trace |
| --- | --- | --- |
| I07-PLAN-001 | I07-AT-001〜011のrun/domain status、file set、manifest、exit fixturesを先に固定する。 | I07-DES-001 |
| I07-PLAN-002 | one run endpoint/freeze/metadata-only FileChangeSet/changed-path admissionとdomain registry fan-outを実装する。 | I07-DES-002 |
| I07-PLAN-003 | domain semanticsを統合せずDomainResult/summary/empty-side provenanceをaggregateする。 | I07-DES-003 |
| I07-PLAN-004 | per-domain semantic JSON/PlantUMLとrun-manifest/v1だけを構築する。 | I07-DES-004 |
| I07-PLAN-005 | presence truth table、run/domain budgets、partial success、0/1/2/3/130をRunOutcomeへ接続する。 | I07-DES-005 |
| I07-PLAN-006 | static/read-only/redaction/determinism/platform/package/offline/full trace regressionを完了する。 | I07-DES-006 |
| I07-PLAN-007 | OutputTransactionのrun-fatal全破棄とdomain-incomplete safe subset publicationを実装する。 | I07-DES-007 |

## 実装step

### I07-PLAN-001 acceptance-first contract

- per-domain output/no-domain-all、partial failure、applicability、run atomicity、exit codes、platform/package、cross-domain presence/budget、working-tree anchor、hunk redaction fixturesを先に固定する。
- each caseはstdout/stderr、published paths、manifest presence/schema/domain entries、digests、countsまでassertする。

### I07-PLAN-002 shared run source and domain fan-out

planned modules（current commit `867ee6929283dfc84711bce245b784d2b8e3e9e6` には未実装）:

- `src/code_structure_viz/application/run.py::RunCoordinator`
- `application/domain_registry.py::FirstPartyDomainRegistry`
- `core/outcome.py::RunOutcome`
- ISSUE-02 endpoint/freezer/metadata-only FileChangeSet/changed-path public contracts

one start-HEAD anchor/frozen digest/selected candidate/merge-base/resolution methodを全domain provenanceへ共有し、domain順をpython→sqlalchemy→nextでdeterministicにする。

### I07-PLAN-003 domain-owned result aggregation

- domain registryは`DomainResult` status、Artifact descriptors、coverage、diagnostics、provenance、safe countsだけを受け取る。
- Python/SQLAlchemy/Next identity/member/relation/matchingをcopy/unionせず、domain all semantic model/cross-domain graphを実装しない。
- each diff domainのempty-side digestとpresence outcomeをmanifestへ保持する。

### I07-PLAN-005 outcome and budget aggregation

- both-absent/before-only/after-only/side-failure combinationsからdomain/overall statusを算出する。
- changed-path overrunはfan-out前exit 1/final manifestなし。entity overrunはaffected domain incomplete/exit 3/affected payloadなし/sibling+manifest保持。valid overridesはrequested/resolved/count、invalid valuesはexit 2。

### I07-PLAN-004 per-domain output and run manifest

- complete domainごとにown semantic JSON/PlantUMLを参照し、`code-structure-viz.run-manifest/v1`を構築する。
- manifest root/domain summaryにentities/members/relations/matchingを置かず、safe graph countsだけを置く。`code-structure-viz.semantic/v1`の`domain: all`を生成しない。

### I07-PLAN-007 output transaction

- `artifacts/manifest.py::AggregateManifestBuilder`、`transaction.py::OutputTransaction`、`cli/exit_codes.py`をplanned targetとする。
- run fatalは全stagingを破棄しfinal manifestなし。domain incompleteはaffected payloadを除外しsuccessful siblings+safe manifestをfingerprint/collision/integrity後にpublishする。
- SIGINTはstaging cleanup、exit 130、existing output/target repositoryを変更しない。

### I07-PLAN-006 hardening and completion handoff

- all dependency suites、Git/build/DB/plugin traps、raw-patch-line/source/secret/path scans、determinism、one Epic/seven DAG/trace check、macOS/Linux、Python/Git/Node minimum/latest、core/Next offline/lock/licenseを通す。
- product HTML command/schema/UI/publicationがないことをscope scanし、completion evidenceをEpic/Initiative Reportへhand offする。

## 検証

| Test ID | acceptance behavior | planned file | command |
| --- | --- | --- | --- |
| I07-AT-001 | per-domain output/no domain-all semantic | tests/acceptance/test_multi_domain_cli.py | uv run pytest tests/acceptance/test_multi_domain_cli.py -q |
| I07-AT-002 | partial sibling retention | tests/acceptance/test_partial_domain_failure.py | uv run pytest tests/acceptance/test_partial_domain_failure.py -q |
| I07-AT-003 | not_applicable/Node optionality | tests/acceptance/test_multi_domain_applicability.py | uv run pytest tests/acceptance/test_multi_domain_applicability.py -q |
| I07-AT-004 | run fatal atomicity | tests/acceptance/test_run_atomicity.py | uv run pytest tests/acceptance/test_run_atomicity.py -q |
| I07-AT-005 | exit/publication matrix | tests/acceptance/test_exit_codes.py | uv run pytest tests/acceptance/test_exit_codes.py -q |
| I07-AT-006 | platform matrix | .github/workflows/ci.yml | uv run pytest && npm --prefix adapters/next test |
| I07-AT-007 | offline/lock/license | tests/packaging/test_offline_install.py | uv run pytest tests/packaging/test_offline_install.py -q |
| I07-AT-008 | cross-domain presence matrix | tests/acceptance/test_multi_domain_presence_matrix.py | uv run pytest tests/acceptance/test_multi_domain_presence_matrix.py -q |
| I07-AT-009 | two-level budget matrix | tests/acceptance/test_multi_domain_budget_matrix.py | uv run pytest tests/acceptance/test_multi_domain_budget_matrix.py -q |
| I07-AT-010 | shared working-tree anchor | tests/acceptance/test_multi_domain_working_tree_anchor.py | uv run pytest tests/acceptance/test_multi_domain_working_tree_anchor.py -q |
| I07-AT-011 | hunk/output redaction | tests/security/test_multi_domain_hunk_redaction.py | uv run pytest tests/security/test_multi_domain_hunk_redaction.py -q |

### issue gate commands

```bash
uv run pytest tests/acceptance/test_multi_domain_cli.py -q
uv run pytest tests/acceptance/test_partial_domain_failure.py -q
uv run pytest tests/acceptance/test_multi_domain_applicability.py -q
uv run pytest tests/acceptance/test_run_atomicity.py -q
uv run pytest tests/acceptance/test_exit_codes.py -q
uv run pytest && npm --prefix adapters/next test
uv run pytest tests/packaging/test_offline_install.py -q
uv run pytest tests/acceptance/test_multi_domain_presence_matrix.py -q
uv run pytest tests/acceptance/test_multi_domain_budget_matrix.py -q
uv run pytest tests/acceptance/test_multi_domain_working_tree_anchor.py -q
uv run pytest tests/security/test_multi_domain_hunk_redaction.py -q
uv run ruff check .
uv run mypy src tests
uv run pytest
```

### Requirement → Design → Plan → acceptance → test trace

| Requirement | Design | Plan | acceptance | test |
| --- | --- | --- | --- | --- |
| I07-REQ-001 | I07-DES-001 | I07-PLAN-001 | I07-AC-001, I07-AC-002, I07-AC-003 | I07-AT-001, I07-AT-002, I07-AT-003 |
| I07-REQ-002 | I07-DES-002 | I07-PLAN-002 | I07-AC-004, I07-AC-010, I07-AC-011 | I07-AT-004, I07-AT-010, I07-AT-011 |
| I07-REQ-003 | I07-DES-003 | I07-PLAN-003 | I07-AC-001, I07-AC-008 | I07-AT-001, I07-AT-008 |
| I07-REQ-004 | I07-DES-004 | I07-PLAN-004 | I07-AC-001, I07-AC-002, I07-AC-003 | I07-AT-001, I07-AT-002, I07-AT-003 |
| I07-REQ-005 | I07-DES-005 | I07-PLAN-005 | I07-AC-002, I07-AC-004, I07-AC-005, I07-AC-008, I07-AC-009 | I07-AT-002, I07-AT-004, I07-AT-005, I07-AT-008, I07-AT-009 |
| I07-REQ-006 | I07-DES-006 | I07-PLAN-006 | I07-AC-006, I07-AC-007, I07-AC-011 | I07-AT-006, I07-AT-007, I07-AT-011 |
| I07-REQ-007 | I07-DES-007 | I07-PLAN-007 | I07-AC-002, I07-AC-004, I07-AC-005, I07-AC-009 | I07-AT-002, I07-AT-004, I07-AT-005, I07-AT-009 |

### regression boundary

- dependency Issueのacceptance suiteを再実行し、public endpoint/source/schema/manifest/exit contractを破っていないことを確認する。
- target repositoryのHEAD、branch、refs、index、status、tracked/untracked bytesがcommand前後で一致する。
- same-input deterministic rerun、output collision、invalid override、interrupt cleanupを確認する。
- Artifact、diagnostic、stdout/stderr/logをsource body、raw patch lines、comment、literal、secret、absolute pathでnegative scanする。
- visual vocabularyはcolorだけでなく記号、line style、legendをgolden/semantic testで検査する。

## rollback

- persistent data migration は N/A。rollout は intermediate release→Next opt-in preview→default all-domain の順。partial outcome/exit bug は default all-domain を無効化して明示 domain へ戻し、schema compatibility を保った forward fix を行う。
- rollback trigger: acceptance regression、source execution/mutation、secret/absolute path leak、incorrect successful exit、ambiguous moved の誤採用。
- rollback unit: Issue の production code、tests、schema/doc additionsを一体で revert する。dependency Issue の accepted contract は戻さない。
- forward recovery: unsafe pattern を `incomplete`/`unknown` へ狭め、誤った success を継続しない。既存 Artifact を自動 rewrite しない。
- output migration は N/A。Artifact は immutable run output であり、既存 output を上書きしない。

## exit / handoff

- I07-AC-001〜I07-AC-011 の acceptance evidence が揃う。
- Requirement→Design→Plan→test trace に gap がない。
- planned path honesty を review し、実装時点の実在 path/symbol と差異があれば Design/Plan を先に更新する。
- residual risk、unsupported static pattern、coverage limitation、explicit override を release note と manifest diagnostic contract に残す。
- downstream handoff: Next.js 対応と multi-domain orchestration の完了をもって Initiative 完了。Python+SQLAlchemy intermediate release からの additive extension とする。
- completion 後も implementation/report の実績は canonical Report に別途記録し、本 Plan を実行ログにしない。
