---
種別: 実装計画書（Issue）
ID: "iss-00005"
タイトル: "Compare Python Structure Changes Safely"
関連GitHub: ["#5"]
package_sequence_key: "ISSUE-02"
状態: "draft"
最終更新: "2026-08-27"
依存: ["requirement.md", "design.md"]
親: ["epic-00002", "init-00001"]
---

# iss-00005 Compare Python Structure Changes Safely — 実装計画

詳細: [Plan Guide](../../../../../../docs/authoring/plan.md)

## 1. 実装方針

本計画は TDD の red→green→refactor 順で実施した実装計画と、完了した step の検証方法を
記録する。実装は既存 snapshot pipeline を壊さず、diff の vertical slice を
`CLI → endpoint → immutable source → Python semantic diff → Artifact/publication` の順に接続する。
各 step は同じ branch 上で小さなテストを先に追加し、最後に全体回帰を行う。

## 2. Step 台帳

| Step | 内容 | 対象 | 状態 |
| --- | --- | --- | --- |
| I02-PLAN-001 | endpoint matrix、presence、budget、hunk、stdout の受入れテストを先に固定 | `tests/acceptance/**`, `tests/integration/python/**`, `tests/security/**` | 完了 |
| I02-PLAN-002 | Git reader、start HEAD anchor、working-tree freezer、secure SourceView、drift/cancellation | `source/git_repository.py`, `source/endpoints.py`, `source/freezer.py`, `source/source_view.py` | 完了 |
| I02-PLAN-003 | Python side presence、canonical empty、semantic delta、seed、union impact、move matching | `semantic/diff.py`, `adapters/python/matcher.py` | 完了 |
| I02-PLAN-004 | file-change、semantic JSON、PlantUML、manifest の versioned publication | `source/file_changes.py`, `adapters/python/diff_renderer.py`, `artifacts/manifest.py` | 完了 |
| I02-PLAN-005 | changed-path/entity gate と incomplete/fatal/usage/interrupt の exit/publication matrix | `application/diff.py`, `core/budget.py`, `core/outcomes.py` | 完了 |
| I02-PLAN-006 | schema、contract docs、redaction、determinism、Git immutability、package regression | `schemas/**`, `docs/contracts/**`, tests | 完了 |
| I02-PLAN-007 | bounded unified hunk helper と Git quoted path validation | `source/file_changes.py`, `source/git_repository.py` | 完了 |
| I02-PLAN-008 | `--stdout` closed grammar、exact bytes、unavailable result、stderr routing | `cli/parser.py`, `cli/main.py`, `artifacts/streams.py`, acceptance tests | 完了 |

## 3. 実装詳細

### I02-PLAN-001 — acceptance-first

次の観測を table-driven に固定した。

- explicit `from/to`、from-only、to-only、`head`、`working-tree`、implicit base の provenance
- both-absent、before-only、after-only、analysis-failed の domain presence と公開 file set
- changed-path default/override、entity default/override、unmerged path
- class/member/decorator/entity seed、before/after relation union、曖昧な move
- metadata-only hunk、quoted non-ASCII path、raw patch/body/secret の非漏えい
- selector なし、available exact bytes、unavailable result、invalid/duplicate selector

### I02-PLAN-002 — source acquisition

`GitRepositoryReader` は Git 2.39 以上を検証し、`GIT_OPTIONAL_LOCKS=0`、
`GIT_CONFIG_NOSYSTEM=1`、`GIT_CONFIG_GLOBAL=/dev/null`、`GIT_NO_LAZY_FETCH=1`、
`GIT_NO_REPLACE_OBJECTS=1` などの固定環境で allowlist command だけを実行する。
commit side は tree と blob を一度ずつ読み、working-tree side は descriptor-based secure read と
private staging を使う。untracked/unmerged を開始時と公開直前に再列挙し、差分を成功扱いしない。
subprocess stdout/stderr は 64 MiB、unified helper は 16 MiB/line 128 KiB で bounded にする。

### I02-PLAN-003 — semantic

`PythonSnapshotAnalyzer`/`PythonTargetSelector` の結果を `DomainPresenceResolver` へ渡す。
`SemanticDiffer` は entity/member/relation の状態を deterministic に並べ、class/decorator と
その他 semantic delta の entity ID を seed 化する。`ImpactExplorer` は before/after relation
union を深さ別に走査する。`PythonMoveMatcher` は名前の証拠と構造 fingerprint の unique
one-to-one を全て満たす場合だけ move とする。

### I02-PLAN-004 — artifacts

`FileChangeSet` は `file-changes.json`、semantic result は `python.diff.semantic.json`、
PlantUML は `python.diff.puml`、run metadata は `run-manifest.json` として同一 transaction で
stage する。semantic JSON は side、digest、file-change、semantic change、seed、impact、matching
を別 field に保持し、renderer は source body を受け取らない。`DiffManifestBuilder` は caller の
requested endpoint と resolved side/provenance を分けて記録する。

### I02-PLAN-005 — gates

changed-path は domain analysis 前に default 1,000、entity は render 前に default 500 とする。
前者の超過は run fatal/exit 1/公開なし、後者は domain `incomplete/payload_unavailable`/exit 3/
file-change と safe manifest のみとする。Git object failure、unsafe path、analysis failure、
unmerged は empty side に変換しない。transaction は usage/fatal/interrupt の staging を破棄し、
domain incomplete のときだけ safe manifest を公開する。

### I02-PLAN-006〜008 — hardening and contract

canonical JSON の key sort と UTF-8 byte order、schema additionalProperties=false、snapshot 回帰、
同一入力再実行、Git HEAD/index/ref/worktree 不変、秘密/absolute path/raw hunk 非漏えいを検証する。
`--stdout` selector は source acquisition 前に閉じた文法を検証し、available Artifact の exact bytes、
unavailable `stdout-result/v1`、selector 無指定の `run-summary/v1` を stderr diagnostic と分離して出す。

## 4. 受入れテストとコマンド

| 領域 | 実ファイル | コマンド |
| --- | --- | --- |
| diff CLI/endpoint/working tree | `tests/acceptance/python/test_diff_cli.py` | `uv run pytest tests/acceptance/python/test_diff_cli.py -q` |
| changed path/fail closed | `tests/acceptance/git/test_changed_path_budget.py`, `test_diff_fail_closed.py` | `uv run pytest tests/acceptance/git -q` |
| presence/entity/selector | `tests/acceptance/python/test_domain_presence_diff.py`, `test_diff_entity_budget.py`, `test_stdout_selector.py` | `uv run pytest tests/acceptance/python/test_domain_presence_diff.py tests/acceptance/python/test_diff_entity_budget.py tests/acceptance/python/test_stdout_selector.py -q` |
| semantic/impact/move | `tests/acceptance/python/test_semantic_seed.py`, `tests/integration/python/test_impact_union_graph.py`, `test_move_matching.py` | `uv run pytest tests/acceptance/python/test_semantic_seed.py tests/integration/python/test_impact_union_graph.py tests/integration/python/test_move_matching.py -q` |
| source/Git safety | `tests/unit/source/test_git_repository.py`, `test_source_view.py`, `tests/integration/source/test_git_repository.py`, `tests/security/test_git_read_only.py` | `uv run pytest tests/unit/source tests/integration/source tests/security/test_git_read_only.py -q` |
| hunk/redaction/schema | `tests/unit/source/test_file_changes.py`, `tests/security/test_file_change_hunk_redaction.py`, `tests/contracts/test_json_schemas.py` | `uv run pytest tests/unit/source/test_file_changes.py tests/security/test_file_change_hunk_redaction.py tests/contracts/test_json_schemas.py -q` |

Issue gate は次の順に実行する。

```bash
uv run ruff check .
uv run mypy src tests
uv run pytest -q
uv build
python3 ./spec-dock/scripts/spec-dock validate
git diff --check
```

## 5. traceability と handoff

| Requirement | Design | Plan | 主なテスト |
| --- | --- | --- | --- |
| I02-REQ-001 | I02-DES-001 | I02-PLAN-001〜004 | `test_diff_cli.py`, `test_impact_union_graph.py` |
| I02-REQ-002 | I02-DES-002 | I02-PLAN-002 | `test_diff_cli.py`, `test_diff_fail_closed.py`, `test_git_repository.py` |
| I02-REQ-003 | I02-DES-003 | I02-PLAN-003 | `test_domain_presence_diff.py`, `test_semantic_seed.py` |
| I02-REQ-004 | I02-DES-004 | I02-PLAN-004 | `test_json_schemas.py`, `test_file_changes.py`, `test_diff_cli.py` |
| I02-REQ-005 | I02-DES-005 | I02-PLAN-005 | `test_changed_path_budget.py`, `test_diff_entity_budget.py` |
| I02-REQ-006 | I02-DES-006 | I02-PLAN-006 | `test_git_read_only.py`, `test_file_change_hunk_redaction.py`, snapshot regression |
| I02-REQ-007 | I02-DES-007 | I02-PLAN-007 | `test_file_changes.py`, `test_diff_cli.py` |
| I02-REQ-008 | I02-DES-008 | I02-PLAN-008 | `test_stdout_selector.py`, `test_diff_fail_closed.py` |

Downstream Issue は `docs/contracts/source-view-v1.md`、`docs/contracts/file-change-set-v1.md`、
`docs/contracts/python-semantic-v1.md`、`docs/contracts/run-manifest-v1.md`、`docs/contracts/stdout-v1.md`
と schema を consume する。HTML report、Tailscale/GitHub Pages 配信、SQLAlchemy/Next adapter、
legacy CLI compatibility は後続 Issue に handoff し、この slice の completion gate には含めない。

## 6. rollback / stop condition

source mutation、secret/absolute path leak、誤った successful exit、fingerprint drift の見逃し、
schema mismatch、ambiguous move の誤採用が検出されたら output release を停止し、Issue の production
code/tests/schema/docs を一体で revert する。公開済み Artifact は自動 rewrite しない。

完了条件は、上記 Issue gate が全て成功し、実装 path とこの Design/Plan が一致し、Strict Final
Quality Gate が同一 pushed commit に対して pass することである。
