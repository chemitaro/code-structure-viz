---
種別: 要件定義書（Issue）
ID: "iss-00005"
タイトル: "Compare Python Structure Changes Safely"
関連GitHub: ["#5"]
package_sequence_key: "ISSUE-02"
状態: "draft"
最終更新: "2026-08-24"
親: ["epic-00002", "init-00001"]
---

# iss-00005 Compare Python Structure Changes Safely — 要件定義

詳細: [Requirement Guide](../../../../../../docs/authoring/requirement.md)

## 目的

coding agent が named endpoint で before/after Python semantic snapshot を安全に固定し、意味のある class/member/relation change と影響 context だけを比較できる。

利用者 story: coding agent として、Git hunk の見かけではなく before/after の Python semantics を基準に、変更 class と upstream/downstream impact を説明したい。

この Issue は技術 layer の完成ではなく、利用者が command を実行して source acquisition、domain analysis、semantic JSON、PlantUML、diagnostic、acceptance evidence まで確認できる一つの vertical outcome を所有する。

## 背景

- 親 Initiative は三 domain の code structure を静的に可視化する。
- 親 Epic は安全な Git comparison と agent-first Artifact contract を一つの product outcome として統合する。
- この slice の declared dependency は ISSUE-01。依存 Issue の public contract だけを利用し、unfinished sibling の内部実装には依存しない。
- canonical authority は exact commit `7951ddabc2e6a3d66edb77eada7c6c16923264f7` の accepted ADR と interview、および本 package の親 R/D/P である。

| 親 requirement | この Issue の所有範囲 |
| --- | --- |
| EPIC-REQ-001 | python domain の diff を end-to-end で提供する。 |
| EPIC-REQ-002 | static analysis、read-only Git、redaction、fail-closed を維持する。 |
| EPIC-REQ-003 | versioned semantic JSON、domain-specific PlantUML、manifest を生成する。 |
| EPIC-REQ-004 | complete/not_applicable/incomplete と exit contract を slice の範囲で実装する。 |

## 観測可能な要件

| ID | 観測面 | 要件 |
| --- | --- | --- |
| I02-REQ-001 | CLI と observable outcome | coding agent が named endpoint で before/after Python semantic snapshot を安全に固定し、意味のある class/member/relation change と影響 context だけを比較できる。 |
| I02-REQ-002 | source acquisition | flag なしは implicit base→開始時 frozen working-tree、`--from REF` は REF→frozen working-tree、`--to REF` はその endpoint に対して解決した implicit base→REF、両方指定は exact REF→REF とする。 |
| I02-REQ-003 | semantic behavior | before と after の immutable Python semantic snapshot を ISSUE-01 の schema で生成し、その snapshot digest を diff の入力 identity とする。 |
| I02-REQ-004 | Artifact/output | semantic diff JSON は before/after snapshot digest、FileChangeSet、SemanticChangeSet、seed、upstream/downstream context、matching evidence を分離する。 |
| I02-REQ-005 | failure behavior | endpoint unresolved、missing Git object、fingerprint drift、implicit path budget 超過では semantic success Artifact を公開せず nonzero とする。 |
| I02-REQ-006 | safety/determinism | 解析対象 module、plugin、migration、build script、application entry point を import または実行しない。 同じ source bytes、endpoint、resolved config、adapter version では entity・member・relation・diagnostic・Artifact path の順序と SHA-256 が決定的になる。 |
| I02-REQ-007 | slice-specific boundary | FileChangeSet は A/M/D/R/C/T/U/? と hunk を evidence として保持するが、SemanticChangeSet の真実源にしない。implicit changed path は既定 1,000、超過時は `--max-changed-paths` 明示 override を要求する。 |

### I02-REQ-001

coding agent が named endpoint で before/after Python semantic snapshot を安全に固定し、意味のある class/member/relation change と影響 context だけを比較できる。
### I02-REQ-002

flag なしは implicit base→開始時 frozen working-tree、`--from REF` は REF→frozen working-tree、`--to REF` はその endpoint に対して解決した implicit base→REF、両方指定は exact REF→REF とする。
### I02-REQ-003

before と after の immutable Python semantic snapshot を ISSUE-01 の schema で生成し、その snapshot digest を diff の入力 identity とする。
### I02-REQ-004

semantic diff JSON は before/after snapshot digest、FileChangeSet、SemanticChangeSet、seed、upstream/downstream context、matching evidence を分離する。
### I02-REQ-005

endpoint unresolved、missing Git object、fingerprint drift、implicit path budget 超過では semantic success Artifact を公開せず nonzero とする。
### I02-REQ-006

解析対象 module、plugin、migration、build script、application entry point を import または実行しない。 同じ source bytes、endpoint、resolved config、adapter version では entity・member・relation・diagnostic・Artifact path の順序と SHA-256 が決定的になる。
### I02-REQ-007

FileChangeSet は A/M/D/R/C/T/U/? と hunk を evidence として保持するが、SemanticChangeSet の真実源にしない。implicit changed path は既定 1,000、超過時は `--max-changed-paths` 明示 override を要求する。


### CLI examples

```bash
code-structure-viz diff --repo . --domain python --output-dir /tmp/csv-python-diff
code-structure-viz diff --repo . --domain python --from origin/main --to head --output-dir /tmp/csv-pr-head
code-structure-viz diff --repo . --domain python --from v1.0.0 --to v1.1.0 --upstream-depth 2 --downstream-depth 1 --output-dir /tmp/csv-release-diff
```

### source acquisition contract

- flag なしは implicit base→開始時 frozen working-tree、`--from REF` は REF→frozen working-tree、`--to REF` はその endpoint に対して解決した implicit base→REF、両方指定は exact REF→REF とする。
- `--to head` は開始時 HEAD commit、`--to working-tree` は開始時 frozen working tree、`--from working-tree` は usage error とする。
- implicit base は `--pr-target`、configured comparison target/upstream、`origin/HEAD`、local main/develop/master candidate の順で endpoint commit との merge-base を試し、解決不能なら fail closed とする。
- before commit source は Git object database から read-only に読み、working-tree 側の必要 source は repository 外 temporary area へ copy する。開始・終了 fingerprint が異なる場合は final output directory を変更しない。
- FileChangeSet は A/M/D/R/C/T/U/? と hunk を evidence として保持するが、SemanticChangeSet の真実源にしない。implicit changed path は既定 1,000、超過時は `--max-changed-paths` 明示 override を要求する。

### semantic contract

- before と after の immutable Python semantic snapshot を ISSUE-01 の schema で生成し、その snapshot digest を diff の入力 identity とする。
- class、field、method、property、decorator metadata、relation の semantic delta がある entity だけを changed seed とする。空白、comment、import order だけの変化は seed にしない。
- impact graph は before/after relation の union。upstream と downstream を別 frontier とし、既定 depth は各 1。削除 class は before relation から context を復元する。
- moved は high-confidence one-to-one、rename/name evidence、structural fingerprint、unique candidate をすべて満たす場合だけ採用し、それ以外は removed+added とする。
- diff diagram は seed と指定 depth の context だけを所有し、whole structure を再掲しない。

### output contract

- semantic diff JSON は before/after snapshot digest、FileChangeSet、SemanticChangeSet、seed、upstream/downstream context、matching evidence を分離する。
- Python PlantUML は class と field/method を member-level で added `+`、removed `-`、modified `~`、moved `→`、unknown `?` と色・線種の両方で示す。
- manifest は requested/resolved endpoint、base method、start HEAD、worktree fingerprint、resolved config、Artifact hash を保持する。
- working tree U path は file evidence へ残すが、その path が関係する semantic domain は incomplete とする。

## スコープ

### 対象

- `python` domain の `diff` use case を CLI input から acceptance test まで届ける。
- common CLI/config/diagnostic/Artifact contract は、この slice に必要な範囲だけ導入または拡張する。
- repository-owned implementation、tests、fixtures、documentation、lockfile、CI lane を含む。

### 対象外

- SQLAlchemy row semantics と Next component semantics
- auto fetch、checkout、worktree/index/refs の変更
- Git R/C を semantic moved と同一視すること
- legacy pyclassuml/tree-git-diff CLI compatibility

### 親契約として変更しない境界

- `--repo PATH` で解析対象 repository を明示し、`--output-dir PATH` を必須とする。
- `--format semantic-json|plantuml` は複数指定でき、未指定時は semantic JSON と PlantUML の両方を生成する。
- `--config PATH` を受け付ける。優先順位は CLI、`.code-structure-viz.toml`、built-in default であり、unknown key と型不正は exit 2 とする。
- 出力は一時 staging directory で完成させ、既存 path との衝突を検査してから atomic に公開する。既存 file は上書きしない。
- `--stdout` を明示した場合だけ、選択した一つの Artifact または run manifest を標準出力へ複製する。通常時の stdout は machine-readable summary だけとする。

- 解析対象 module、plugin、migration、build script、application entry point を import または実行しない。
- Git repository は read-only とし、fetch、checkout、reset、stash、clean、commit、ref 更新を実行しない。すべての Git subprocess で lazy fetch、external diff、textconv、color を無効化する。
- Artifact には repository-relative path、symbol、type、signature、relation、line range だけを許可し、source body、comment、literal、secret らしい値、absolute path を含めない。
- 同じ source bytes、endpoint、resolved config、adapter version では entity・member・relation・diagnostic・Artifact path の順序と SHA-256 が決定的になる。

## 失敗・境界条件

- endpoint unresolved、missing Git object、fingerprint drift、implicit path budget 超過では semantic success Artifact を公開せず nonzero とする。
- 一部 Python source の安全な解析が不可能でも unaffected snapshot/diff が成立する場合は incomplete、成功 Artifact と diagnostic を保持し exit 3 とする。
- moved 候補が複数ある場合は unknown moved を捏造せず removed+added と matching diagnostic を返す。

- `not_applicable` は target 不在、`incomplete` は target があるが安全に解析できない状態であり、相互に変換しない。
- failure diagnostic は stable code、severity、domain、safe repository-relative location、recoverability、human-readable message を持つ。source body と secret は含めない。
- stop condition: before/after snapshot の独立再生成、endpoint/fingerprint provenance、semantic seed、impact union、failure matrix が acceptance test で固定されるまで SQLAlchemy/Next diff の共通化へ進まない。

## 受け入れ条件

| ID | 観測可能な完了条件 | acceptance test |
| --- | --- | --- |
| I02-AC-001 | 全 `--from`/`--to` 組合せで requested/resolved endpoint と snapshot digest が一致する。 | I02-AT-001 |
| I02-AC-002 | deleted class の before edge と union graph で upstream/downstream depth 1 を別々に選ぶ。 | I02-AT-002 |
| I02-AC-003 | base 解決不能、U path、missing object、fingerprint drift で fail closed になる。 | I02-AT-003 |
| I02-AC-004 | 全 Git invocation が read-only allowlist 内で、refs/index/worktree fingerprint を変更しない。 | I02-AT-004 |
| I02-AC-005 | whitespace/comment/import-order only は seed 0、member/relation delta は seed になる。 | I02-AT-005 |
| I02-AC-006 | 一意な rename+fingerprint だけ moved、ambiguous candidate は removed+added になる。 | I02-AT-006 |
| I02-AC-007 | implicit 1,001 path は無切り捨て failure、明示 override は manifest に残る。 | I02-AT-007 |

- **I02-AC-001〜I02-AC-007 がすべて満たされ、planned test command が clean checkout で成功すること。**
- Requirement、Design、Plan の trace table が一致し、unresolved acceptance gap がないこと。
- release boundary: ISSUE-01 と合わせて Python domain preview。Git comparison foundation は後続 domain diff が再利用するが、Python 固有 matching は adapter 内に残す。

## 制約・前提

- initial platform は macOS と Linux。native Windows は対象外。
- Core/CLI/Git/manifest/Python/SQLAlchemy は Python 3.12 以上。Next adapter 利用時だけ Node.js 22 LTS 以上。
- Git 2.39 以上。CI は minimum supported と repository で明示更新する latest stable lane を実行する。
- direct/indirect dependency は lockfile で exact resolve し、license inventory と offline runtime test を持つ。runtime に network access を要求しない。
- `pyclassuml` と `tree-git-diff` への runtime/package/CLI dependency を持たない。legacy code の直接 copy は license/provenance 未確認のまま行わず、初期実装は contract/test evidence を基に repository-owned code として再実装する。
- product HTML report generation、HTML command、Tailscale publication は本 Issue の製品 scope 外。`explanation.html` は specification Artifact である。
