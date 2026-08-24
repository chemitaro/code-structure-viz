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

- declared dependency: ISSUE-01
- sibling の private parser/model/renderer implementation に依存しない。必要な cross-Issue contract は `semantic-contract.md` と親 Epic Design を正本にする。
- 並行可能: fixture authoring、schema examples、renderer golden、security trap fixture は interface acceptance 固定後に並行できる。
- 統合順: dependency contract verification → source path → semantic model → render/output transaction → acceptance/CI。
- stop condition: before/after snapshot の独立再生成、endpoint/fingerprint provenance、semantic seed、impact union、failure matrix が acceptance test で固定されるまで SQLAlchemy/Next diff の共通化へ進まない。

| Plan ID | implementation/verification step | Design trace |
| --- | --- | --- |
| I02-PLAN-001 | Requirement fixture と command/manifest contract test を先に追加し、failure/exit behavior を executable acceptance として固定する。 | I02-DES-001 |
| I02-PLAN-002 | 必要最小限の CLI/config/diagnostic/Artifact boundary を planned module に実装し、dependency Issue の public contract を再利用する。 | I02-DES-002 |
| I02-PLAN-003 | python source acquisition と domain-owned semantic analyzer/matcher を実装し、unsafe/unknown を diagnostic へ変換する。 | I02-DES-003 |
| I02-PLAN-004 | semantic JSON と PlantUML renderer、redaction、deterministic ordering、SHA-256 manifest を一つの output transaction へ接続する。 | I02-DES-004 |
| I02-PLAN-005 | negative/security/budget/determinism/partial failure test、documentation、lockfile/license/offline gate を完了し、handoff evidence を作る。 | I02-DES-005 |
| I02-PLAN-006 | CI minimum/latest lane と full regression を通し、rollback/forward recovery 条件を review する。 | I02-DES-006 |

## 実装step

### I02-PLAN-001 acceptance-first contract

- planned test files を先に作り、CLI arguments、output filenames、manifest fields、status、exit code を table-driven fixture で固定する。
- user-visible Artifact bytes の golden は source body/secret/absolute path がないことを同時に確認する。
- implementation 未着手時に test が expected failure になることを確認し、誤った既存 behavior を前提にしない。

### I02-PLAN-002 application boundary

- planned modules:

- src/code_structure_viz/source/endpoints.py::ComparisonEndpointResolver（planned）
- src/code_structure_viz/source/freezer.py::WorkingTreeFreezer（planned）
- src/code_structure_viz/source/git_repository.py::ReadOnlyGitRepository（planned）
- src/code_structure_viz/source/file_changes.py::FileChangeSet（planned）
- src/code_structure_viz/semantic/diff.py::SemanticDiffer（planned）
- src/code_structure_viz/semantic/impact.py::ImpactExplorer（planned）
- src/code_structure_viz/adapters/python/matcher.py::PythonMoveMatcher（planned）
- src/code_structure_viz/adapters/python/diff_renderer.py（planned）

- すべて baseline commit には未実装であり、この Plan は候補 path/symbol を指示する。存在済みとみなさない。
- dependency injection は filesystem、Git process、clock/temp directory、Node process に限定し、domain model を framework へ依存させない。

### I02-PLAN-003 source and semantic implementation

- flag なしは implicit base→開始時 frozen working-tree、`--from REF` は REF→frozen working-tree、`--to REF` はその endpoint に対して解決した implicit base→REF、両方指定は exact REF→REF とする。
- `--to head` は開始時 HEAD commit、`--to working-tree` は開始時 frozen working tree、`--from working-tree` は usage error とする。
- implicit base は `--pr-target`、configured comparison target/upstream、`origin/HEAD`、local main/develop/master candidate の順で endpoint commit との merge-base を試し、解決不能なら fail closed とする。
- before commit source は Git object database から read-only に読み、working-tree 側の必要 source は repository 外 temporary area へ copy する。開始・終了 fingerprint が異なる場合は final output directory を変更しない。
- FileChangeSet は A/M/D/R/C/T/U/? と hunk を evidence として保持するが、SemanticChangeSet の真実源にしない。implicit changed path は既定 1,000、超過時は `--max-changed-paths` 明示 override を要求する。

- before と after の immutable Python semantic snapshot を ISSUE-01 の schema で生成し、その snapshot digest を diff の入力 identity とする。
- class、field、method、property、decorator metadata、relation の semantic delta がある entity だけを changed seed とする。空白、comment、import order だけの変化は seed にしない。
- impact graph は before/after relation の union。upstream と downstream を別 frontier とし、既定 depth は各 1。削除 class は before relation から context を復元する。
- moved は high-confidence one-to-one、rename/name evidence、structural fingerprint、unique candidate をすべて満たす場合だけ採用し、それ以外は removed+added とする。
- diff diagram は seed と指定 depth の context だけを所有し、whole structure を再掲しない。

- adapter input/output を immutable value とし、parse failure を empty collection や removed entity へ変換しない。
- budget は collection/render 前に検査し、partial truncation を禁止する。

### I02-PLAN-004 Artifact publication

- semantic diff JSON は before/after snapshot digest、FileChangeSet、SemanticChangeSet、seed、upstream/downstream context、matching evidence を分離する。
- Python PlantUML は class と field/method を member-level で added `+`、removed `-`、modified `~`、moved `→`、unknown `?` と色・線種の両方で示す。
- manifest は requested/resolved endpoint、base method、start HEAD、worktree fingerprint、resolved config、Artifact hash を保持する。
- working tree U path は file evidence へ残すが、その path が関係する semantic domain は incomplete とする。

- staging directory は target repository 外を優先し、final fingerprint/collision check 後に rename/copy+fsync strategy で公開する。
- manifest の SHA-256 は final bytes を基準にし、path は output directory 相対とする。

### I02-PLAN-006 hardening and handoff

- `uv run ruff check .`
- `uv run mypy src tests`
- `uv run pytest`
- Next adapter を含む場合は `npm --prefix adapters/next ci --offline`、`npm --prefix adapters/next run typecheck`、`npm --prefix adapters/next test`。
- package build、minimum/latest CI、offline runtime fixture、license inventory を確認する。
- docs は CLI examples、schema version、failure/exit behavior、scope 外を更新する。product HTML command は追加しない。

## 検証

| Test ID | acceptance behavior | planned file | command |
| --- | --- | --- | --- |
| I02-AT-001 | 全 `--from`/`--to` 組合せで requested/resolved endpoint と snapshot digest が一致する。 | tests/acceptance/python/test_diff_cli.py | uv run pytest tests/acceptance/python/test_diff_cli.py -q |
| I02-AT-002 | deleted class の before edge と union graph で upstream/downstream depth 1 を別々に選ぶ。 | tests/integration/python/test_impact_union_graph.py | uv run pytest tests/integration/python/test_impact_union_graph.py -q |
| I02-AT-003 | base 解決不能、U path、missing object、fingerprint drift で fail closed になる。 | tests/acceptance/git/test_diff_fail_closed.py | uv run pytest tests/acceptance/git/test_diff_fail_closed.py -q |
| I02-AT-004 | 全 Git invocation が read-only allowlist 内で、refs/index/worktree fingerprint を変更しない。 | tests/security/test_git_read_only.py | uv run pytest tests/security/test_git_read_only.py -q |
| I02-AT-005 | whitespace/comment/import-order only は seed 0、member/relation delta は seed になる。 | tests/acceptance/python/test_semantic_seed.py | uv run pytest tests/acceptance/python/test_semantic_seed.py -q |
| I02-AT-006 | 一意な rename+fingerprint だけ moved、ambiguous candidate は removed+added になる。 | tests/integration/python/test_move_matching.py | uv run pytest tests/integration/python/test_move_matching.py -q |
| I02-AT-007 | implicit 1,001 path は無切り捨て failure、明示 override は manifest に残る。 | tests/acceptance/git/test_changed_path_budget.py | uv run pytest tests/acceptance/git/test_changed_path_budget.py -q |

### issue gate commands

```bash
uv run pytest tests/acceptance/python/test_diff_cli.py -q
uv run pytest tests/integration/python/test_impact_union_graph.py -q
uv run pytest tests/acceptance/git/test_diff_fail_closed.py -q
uv run pytest tests/security/test_git_read_only.py -q
uv run pytest tests/acceptance/python/test_semantic_seed.py -q
uv run pytest tests/integration/python/test_move_matching.py -q
uv run pytest tests/acceptance/git/test_changed_path_budget.py -q
uv run ruff check .
uv run mypy src tests
uv run pytest
```

### regression boundary

- dependency Issue の acceptance suite を再実行し、public JSON/manifest/exit contract を破っていないことを確認する。
- target repository の HEAD、branch、refs、index、status、tracked/untracked bytes が command 前後で一致する。
- same-input deterministic rerun と output collision negative test を実行する。
- visual vocabulary は color、記号、line style、legend を golden/semantic test で検査する。

## rollback

- persistent migration は N/A。fingerprint や endpoint contract に不具合があれば release を停止して Issue 全体を revert する。公開済み schema は旧 snapshot digest を読める additive correction または schema version up で forward recovery する。
- rollback trigger: acceptance regression、source execution/mutation、secret/absolute path leak、incorrect successful exit、ambiguous moved の誤採用。
- rollback unit: Issue の production code、tests、schema/doc additionsを一体で revert する。dependency Issue の accepted contract は戻さない。
- forward recovery: unsafe pattern を `incomplete`/`unknown` へ狭め、誤った success を継続しない。既存 Artifact を自動 rewrite しない。
- output migration は N/A。Artifact は immutable run output であり、既存 output を上書きしない。

## exit / handoff

- I02-AC-001〜I02-AC-007 の acceptance evidence が揃う。
- Requirement→Design→Plan→test trace に gap がない。
- planned path honesty を review し、実装時点の実在 path/symbol と差異があれば Design/Plan を先に更新する。
- residual risk、unsupported static pattern、coverage limitation、explicit override を release note と manifest diagnostic contract に残す。
- downstream handoff: ISSUE-01 と合わせて Python domain preview。Git comparison foundation は後続 domain diff が再利用するが、Python 固有 matching は adapter 内に残す。
- completion 後も implementation/report の実績は canonical Report に別途記録し、本 Plan を実行ログにしない。
