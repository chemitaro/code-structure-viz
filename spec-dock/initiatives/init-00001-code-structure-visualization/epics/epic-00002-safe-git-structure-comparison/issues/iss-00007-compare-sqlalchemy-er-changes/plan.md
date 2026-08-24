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

- declared dependency: ISSUE-02, ISSUE-03
- sibling の private parser/model/renderer implementation に依存しない。必要な cross-Issue contract は `semantic-contract.md` と親 Epic Design を正本にする。
- 並行可能: fixture authoring、schema examples、renderer golden、security trap fixture は interface acceptance 固定後に並行できる。
- 統合順: dependency contract verification → source path → semantic model → render/output transaction → acceptance/CI。
- stop condition: 全 row kind の before/after delta、ghost rendering、ambiguous matching、片側解析 failure が acceptance で固定されるまで intermediate release を宣言しない。

| Plan ID | implementation/verification step | Design trace |
| --- | --- | --- |
| I04-PLAN-001 | Requirement fixture と command/manifest contract test を先に追加し、failure/exit behavior を executable acceptance として固定する。 | I04-DES-001 |
| I04-PLAN-002 | 必要最小限の CLI/config/diagnostic/Artifact boundary を planned module に実装し、dependency Issue の public contract を再利用する。 | I04-DES-002 |
| I04-PLAN-003 | sqlalchemy source acquisition と domain-owned semantic analyzer/matcher を実装し、unsafe/unknown を diagnostic へ変換する。 | I04-DES-003 |
| I04-PLAN-004 | semantic JSON と PlantUML renderer、redaction、deterministic ordering、SHA-256 manifest を一つの output transaction へ接続する。 | I04-DES-004 |
| I04-PLAN-005 | negative/security/budget/determinism/partial failure test、documentation、lockfile/license/offline gate を完了し、handoff evidence を作る。 | I04-DES-005 |

## 実装step

### I04-PLAN-001 acceptance-first contract

- planned test files を先に作り、CLI arguments、output filenames、manifest fields、status、exit code を table-driven fixture で固定する。
- user-visible Artifact bytes の golden は source body/secret/absolute path がないことを同時に確認する。
- implementation 未着手時に test が expected failure になることを確認し、誤った既存 behavior を前提にしない。

### I04-PLAN-002 application boundary

- planned modules:

- src/code_structure_viz/adapters/sqlalchemy/differ.py::SqlAlchemySemanticDiffer（planned）
- src/code_structure_viz/adapters/sqlalchemy/matcher.py::SqlAlchemyMoveMatcher（planned）
- src/code_structure_viz/adapters/sqlalchemy/diff_model.py（planned）
- src/code_structure_viz/adapters/sqlalchemy/diff_renderer.py（planned）
- src/code_structure_viz/semantic/impact.py の domain graph extension（planned）

- すべて baseline commit には未実装であり、この Plan は候補 path/symbol を指示する。存在済みとみなさない。
- dependency injection は filesystem、Git process、clock/temp directory、Node process に限定し、domain model を framework へ依存させない。

### I04-PLAN-003 source and semantic implementation

- ISSUE-02 の named endpoint、read-only Git、external working-tree freeze、fingerprint、FileChangeSet を再利用する。
- 各 endpoint で ISSUE-03 の immutable SQLAlchemy snapshot を独立生成し、片側だけの parse success を削除として補完しない。
- domain target 不在は not_applicable、target 存在かつ一方の snapshot が安全に作れない場合は incomplete。

- table entity と column/constraint/index/relationship row の added/removed/modified/moved を before/after value とともに保持する。
- removed row は after diagram に ghost row として残し、赤・破線・`-`、before value を表示する。modified row は before/after の安全な normalized value を併記する。
- table/member identity の一対一 matching は exact identity を優先し、rename evidence+structural fingerprint+unique candidate の全条件を満たす場合だけ moved とする。
- table または row relation delta を changed seed とし、before/after ER graph union 上で upstream/downstream を別々に探索する。
- SQL default literal は両 endpoint と diff でも redacted のままとし、value comparison は presence/category の安全な差だけに限定する。

- adapter input/output を immutable value とし、parse failure を empty collection や removed entity へ変換しない。
- budget は collection/render 前に検査し、partial truncation を禁止する。

### I04-PLAN-004 Artifact publication

- ER diff JSON は table delta と typed row delta を分離し、各 delta に before/after representation、matching evidence、source provenance を持たせる。
- PlantUML は table-level と row-level の visual vocabulary を同時に示し、removed row を ghost 表示する。
- manifest は両 snapshot digest、adapter version、coverage、diagnostic、partial failure、Artifact hash を記録する。

- staging directory は target repository 外を優先し、final fingerprint/collision check 後に rename/copy+fsync strategy で公開する。
- manifest の SHA-256 は final bytes を基準にし、path は output directory 相対とする。

### I04-PLAN-005 hardening and handoff

- `uv run ruff check .`
- `uv run mypy src tests`
- `uv run pytest`
- Next adapter を含む場合は `npm --prefix adapters/next ci --offline`、`npm --prefix adapters/next run typecheck`、`npm --prefix adapters/next test`。
- package build、minimum/latest CI、offline runtime fixture、license inventory を確認する。
- docs は CLI examples、schema version、failure/exit behavior、scope 外を更新する。product HTML command は追加しない。

## 検証

| Test ID | acceptance behavior | planned file | command |
| --- | --- | --- | --- |
| I04-AT-001 | table と各 row kind の added/removed/modified を before/after 値付きで出力する。 | tests/acceptance/sqlalchemy/test_diff_cli.py | uv run pytest tests/acceptance/sqlalchemy/test_diff_cli.py -q |
| I04-AT-002 | removed row が ghost row、modified row が before/after 表記、記号と線種を持つ。 | tests/acceptance/sqlalchemy/test_diff_plantuml.py | uv run pytest tests/acceptance/sqlalchemy/test_diff_plantuml.py -q |
| I04-AT-003 | 一意 structural match だけ moved、ambiguous table/row は removed+added。 | tests/integration/sqlalchemy/test_move_matching.py | uv run pytest tests/integration/sqlalchemy/test_move_matching.py -q |
| I04-AT-004 | 片側 parse failure を削除にせず incomplete にする。 | tests/acceptance/sqlalchemy/test_diff_failures.py | uv run pytest tests/acceptance/sqlalchemy/test_diff_failures.py -q |
| I04-AT-005 | before/after/diff の default literal と absolute path が redacted される。 | tests/security/test_er_diff_redaction.py | uv run pytest tests/security/test_er_diff_redaction.py -q |
| I04-AT-006 | deleted table の before edge を union graph context に保持する。 | tests/integration/sqlalchemy/test_impact_union_graph.py | uv run pytest tests/integration/sqlalchemy/test_impact_union_graph.py -q |

### issue gate commands

```bash
uv run pytest tests/acceptance/sqlalchemy/test_diff_cli.py -q
uv run pytest tests/acceptance/sqlalchemy/test_diff_plantuml.py -q
uv run pytest tests/integration/sqlalchemy/test_move_matching.py -q
uv run pytest tests/acceptance/sqlalchemy/test_diff_failures.py -q
uv run pytest tests/security/test_er_diff_redaction.py -q
uv run pytest tests/integration/sqlalchemy/test_impact_union_graph.py -q
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

- DB migration は実行しないため N/A。誤った row kind/matching は affected analysis を incomplete に狭める forward fix を優先する。intermediate release 後の schema break は version up と compatibility fixture で回復する。
- rollback trigger: acceptance regression、source execution/mutation、secret/absolute path leak、incorrect successful exit、ambiguous moved の誤採用。
- rollback unit: Issue の production code、tests、schema/doc additionsを一体で revert する。dependency Issue の accepted contract は戻さない。
- forward recovery: unsafe pattern を `incomplete`/`unknown` へ狭め、誤った success を継続しない。既存 Artifact を自動 rewrite しない。
- output migration は N/A。Artifact は immutable run output であり、既存 output を上書きしない。

## exit / handoff

- I04-AC-001〜I04-AC-006 の acceptance evidence が揃う。
- Requirement→Design→Plan→test trace に gap がない。
- planned path honesty を review し、実装時点の実在 path/symbol と差異があれば Design/Plan を先に更新する。
- residual risk、unsupported static pattern、coverage limitation、explicit override を release note と manifest diagnostic contract に残す。
- downstream handoff: ISSUE-01〜04 で Python class と SQLAlchemy ER の snapshot/diff が利用可能となる intermediate release milestone。
- completion 後も implementation/report の実績は canonical Report に別途記録し、本 Plan を実行ログにしない。
