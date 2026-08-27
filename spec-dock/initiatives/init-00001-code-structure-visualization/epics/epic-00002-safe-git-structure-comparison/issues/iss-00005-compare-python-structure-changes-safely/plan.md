---
種別: 実装計画書（Issue）
ID: "iss-00005"
タイトル: "Compare Python Structure Changes Safely"
関連GitHub: ["#5"]
package_sequence_key: "ISSUE-02"
状態: "draft"
最終更新: "2026-08-28"
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

初回実装後の Strict Final Quality Gate で、working-tree path-state、content hunk、U coverage、
production acceptance trace に P1 gap が見つかった。以下の remediation step はその gap を Red→Green
で閉じるために追加し、既存 public schema version は維持した。旧 step の「完了」は初回 slice の
実装結果を指し、下記 step はその後の品質ゲート対応である。

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
| I02-PLAN-009 | immutable path-state authority、canonical working-tree status、R/C/T、tracked transition、mode、U | `source/source_view.py`, `source/git_repository.py`, `source/file_changes.py`, `application/diff.py` | 完了 |
| I02-PLAN-010 | all-changed-path bounded content evidence、availability typing、terminator-preserving ranges、no fake hunk | `source/file_changes.py`, `source/freezer.py`, `application/diff.py` | 完了 |
| I02-PLAN-011 | U branch の side/coverage/diagnostic を一回の observation から構成 | `application/diff.py`, `tests/acceptance/python/test_domain_presence_diff.py` | 完了 |
| I02-PLAN-012 | AC-003/007/008/009/010 の production-route regression、drift/missing-object/publication/schema evidence | `tests/acceptance/python/test_diff_cli.py`, `tests/acceptance/python/test_diff_entity_budget.py`, `tests/unit/source/**` | 完了 |
| I02-PLAN-013 | raw Git path identity、NFC/NFD collision、duplicate canonical map、index skip-worktree state | `source/git_repository.py`, `source/source_view.py`, `source/file_changes.py`, `tests/acceptance/python/test_diff_cli.py`, `tests/unit/source/**` | 完了 |
| I02-PLAN-014 | mode `160000` gitlink の nested HEAD/tracked/staged/untracked state、親側一件 `M`、公開直前 drift | `source/git_repository.py`, `source/source_view.py`, `source/file_changes.py`, `application/diff.py`, `tests/acceptance/python/test_diff_cli.py` | 完了 |
| I02-PLAN-015 | implicit base候補の評価順・origin・resolved object・merge-base・dispositionをmanifestへ記録 | `source/endpoints.py`, `schemas/run-manifest-v1.schema.json`, `tests/acceptance/python/test_diff_cli.py`, `tests/contracts/test_json_schemas.py` | 完了 |
| I02-PLAN-016 | Strictレビューの履歴SHAと現行検証を混同しないReport/証跡運用へ同期 | `report.md`, `docs/contracts/run-manifest-v1.md`, Strict review workbench | 完了 |
| I02-PLAN-017 | cross-side raw Git path identityをcanonical map/budget前に検証し、NFC/NFD transitionをfail-closed | `source/git_repository.py`, `source/freezer.py`, `source/source_view.py`, `source/file_changes.py`, `application/diff.py`, `tests/unit/source/test_file_changes.py`, `tests/acceptance/python/test_diff_cli.py` | 完了 |
| I02-PLAN-018 | gitlinkをcomplete-only・validated binding・helper-free read-only observerへ再構成し、初期/最終診断を分離 | `source/git_repository.py`, `source/source_view.py`, `application/diff.py`, `tests/unit/source/test_git_repository.py`, `tests/acceptance/python/test_diff_cli.py` | 完了 |
| I02-PLAN-019 | P1境界（raw transition、missing/uninitialized/external gitlink、nested helper sentinel、final unreadable）をproduction CLIで回帰 | `tests/acceptance/python/test_diff_cli.py`, `tests/unit/source/test_git_repository.py`, `tests/unit/source/test_file_changes.py`, `tests/unit/source/test_source_view.py` | 完了 |
| I02-PLAN-020 | Gitの変換・属性・index flagを閉世界profileで検証し、raw worktree比較を安全な条件だけに限定。profile/tracked digestを内部stateへ束ねる | `source/git_repository.py`, `source/source_view.py`, `application/diff.py`, `tests/unit/source/test_git_repository.py`, `tests/acceptance/python/test_diff_cli.py` | 完了 |
| I02-PLAN-021 | clean baselineを使ったgitlink acceptanceと、autocrlf/eol/filter/index flag/core.filemode/profile driftのfail-closed回帰を追加 | `tests/helpers/diff.py`, `tests/acceptance/python/test_diff_cli.py`, `tests/unit/source/test_git_repository.py` | 完了 |

## 3. 実装詳細

### I02-PLAN-001 — acceptance-first

次の観測を table-driven に固定した。

- explicit `from/to`、from-only、to-only、`head`、`working-tree`、implicit base の provenance
- both-absent、before-only、after-only、analysis-failed の domain presence と公開 file set
- changed-path default/override、entity default/override、unmerged path、unreadable untracked path
- default の 1,001 changed paths と 501 changed entities、candidate non-blob/non-regular の fail-closed
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
file-change と safe manifest のみとする。payload unavailable の diff でも run-level file-change
descriptor は公開する。Git object failure、unsafe path、analysis failure、
unmerged は empty side に変換しない。transaction は usage/fatal/interrupt の staging を破棄し、
domain incomplete のときだけ safe manifest を公開する。

### I02-PLAN-006〜008 — hardening and contract

canonical JSON の key sort と UTF-8 byte order、schema additionalProperties=false、snapshot 回帰、
同一入力再実行、Git HEAD/index/ref/worktree 不変、秘密/absolute path/raw hunk 非漏えいを検証する。
`--stdout` selector は source acquisition 前に閉じた文法を検証し、available Artifact の exact bytes、
unavailable `stdout-result/v1`、selector 無指定の `run-summary/v1` を stderr diagnostic と分離して出す。

### I02-PLAN-009〜012 — Strict Final Quality Gate remediation

- I02-PLAN-009 では、開始時の path enumeration、index stage/mode/object、tracked/untracked、unmerged、
  frozen inventory を同じ内部 authority として保持し、budget 前に `U`、same-path transition、unique
  `R`/`C`、`A`/`D`/`?`、`T`、mode-only `M` を deterministic に分類した。tracked→untracked は `D+?` の二件、
  unique R/C は一件として count と manifest を同じ tuple から作る。
- I02-PLAN-010 では、changed path の全 domain を inventory から `absent`/`available`/`unavailable` に
  分け、admission 後にだけ content evidence を range へ投影した。digest、NUL、payload/line bound を
  検証し、unknown bytes を empty side にせず、LF/CRLF を含む terminator-preserving range とした。影響
  Python は safe metadata と `payload_unavailable`、非 Python は fake hunk なし、commit object 欠損は fatal
  とした。
- I02-PLAN-011 では、U path の before selection を一度だけ行い、同じ actual coverage/diagnostic と
  semantic side を safe manifest へ渡した。after は未解析 `analysis-failed` と fingerprint のみを記録し、
  synthetic coverage による上書きを除去した。
- I02-PLAN-012 では、実際の `diff` CLI 経路で tracked→untracked budget、R/C/T/mode、non-Python hunk、
  LF/CRLF、unavailable、missing commit object、working-tree drift、valid entity override、U coverage を
  検証した。unit protocol tests と schema/security suite を合わせ、publication file set と no-publication
  boundary を確認した。
- I02-PLAN-013 では、Gitのraw UTF-8 spellingをNFC canonical pathから分離した `GitPathIdentity` を導入し、
  index/tree/untracked/unmergedの異なるraw spellingが同一canonical pathへ収束した時点で
  `CSV-DIFF-003`・exit 1・公開なしとした。indexのskip-worktree flagをraw identityで照合し、欠落pathを
  `sparse-unavailable` として扱ってindex blobの再構築と実削除 `D` を防いだ。canonical map/content evidence
  のduplicate上書きも拒否した。
- I02-PLAN-014 では、mode `160000` をnested sourceへ展開せず、nested HEAD、tracked/staged diff、untracked
  dirtyを `GitlinkWorktreeState` としてread-only観測した。いずれかの変更は親側の一件の `M`、安全な再読取の
  不一致は `CSV-SOURCE-001` fatalとし、nested pathのhunk・secret・stderrを公開しない。
- I02-PLAN-015 では、implicit base候補をdeterministicにdeduplicateし、各候補のordinal/origin/reference/
  resolved object/merge-base/dispositionを `comparison.candidate_observations`へ記録した。explicit endpoint
  は空配列、implicitはselected一件を必須とし、`ComparisonEndpoints` constructorで整合性を検証した。
- I02-PLAN-016 では、過去のStrictレビューで検証したSHAを「現行SHA」と記載せず、Reportを履歴receiptとして
  明示する。現行のlocal/upstream/GitHub SHA、テスト結果、Strict pass判定は同一SHAを束ねた外部検証証跡で
  確認し、Report内の古い数値を現行証拠として再利用しない。
- I02-PLAN-017 では、commit tree と working-tree/index の raw UTF-8 spelling を `GitPathIdentity` のまま
  保持し、両側を一つの canonical-to-raw検証へ通してから map、status分類、changed-path budgetを行うように
  した。同一 raw spelling の再観測は許可し、異なる raw spelling が同じ NFC pathへ収束する場合は
  `CSV-DIFF-003`・exit 1・公開なしとした。`SourceInventoryEntry` は内部 raw pathを保持するが public schemaは
  据え置いた。
- I02-PLAN-018 では、`GitlinkWorktreeState` を initialized/current_head/binding identity必須のcomplete-only
  value objectへ変更した。nested `.git` directoryまたは bounded gitdir pointerを安全な rootへ解決し、
  `rev-parse`、`ls-tree`、`ls-files` と descriptor-based raw file hashだけで HEAD/index/worktree/untrackedを
  観測する。nested `diff`/`status` と textconv、external diff、clean/process filter、helperは呼ばない。
  初期の読取不能は `CSV-DIFF-003`、公開直前の読取不能は `CSV-SOURCE-001` として stagingを公開しない。
- I02-PLAN-019 では、missing/uninitialized/external-pointer gitlink、final observation unreadable、
  nested textconv/clean/process helper sentinel、cross-side NFC/NFD transitionを実際の `diff` CLI 経路で
  検証し、全て no-publication または安全な親側一件 `M` を確認した。unit では identity invariant、complete-only
  state、同一 raw spelling許可も固定した。
- I02-PLAN-020 では、nested repositoryのlocal/worktree config、`.gitattributes`、index identity flagを
  `--no-includes`、`check-attr -z --all`、`ls-files -v`のmetadata観測だけでprofile化した。external
  include/attributes、autocrlf/eol、filter/diff、変換系attribute、skip-worktree/assume-unchanged、未対応
  modeをclosed-worldで拒否し、raw比較を許可するprofile digestを内部stateへ含めた。`core.filemode=false`
  はregular `100644`/`100755`差だけを無視し、type/symlink差はdirtyとして扱う。profile不成立は初期
  `CSV-DIFF-003`、公開直前のprofile/tracked digest driftは`CSV-SOURCE-001`へ変換し、public schemaは変更しない。
- I02-PLAN-021 では、親OIDとnested HEAD/tree/indexが一致するclean gitlinkを基準fixtureとして分離し、
  clean baselineが既に親側をdirtyにしているためにobserver誤判定を隠すことがないようにした。production
  CLIでtracked/untracked dirty、core.filemode=false、autocrlf true/input、`.gitattributes` eol、
  skip-worktree/assume-unchanged、profile driftを回帰し、許可された差分は親側一件`M`、unsafe profileは
  `CSV-DIFF-003`・exit 1・公開なしであることを確認した。

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
| I02-REQ-009 | I02-DES-009 | I02-PLAN-013 | `test_diff_cli.py`, `test_git_repository.py`, `test_source_view.py`, `test_file_changes.py` |
| I02-REQ-010 | I02-DES-010 | I02-PLAN-014, 018〜021 | `test_diff_cli.py`, `test_git_repository.py`, `test_file_changes.py` |
| I02-REQ-011 | I02-DES-011 | I02-PLAN-015 | `test_diff_cli.py`, `test_json_schemas.py` |

P1 remediation は I02-REQ-009 → I02-DES-009 → I02-PLAN-017、I02-REQ-010 → I02-DES-010 →
I02-PLAN-018〜021 の経路で trace し、public schema versionは変更しない。

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
