---
種別: 実装計画書（Issue）
ID: "iss-00004"
タイトル: "Generate Python Structure Snapshots"
関連GitHub: ["#4"]
package_sequence_key: "ISSUE-01"
状態: "draft"
最終更新: "2026-08-24"
依存: ["requirement.md", "design.md"]
親: ["epic-00002", "init-00001"]
---

# iss-00004 Generate Python Structure Snapshots — 実装計画

詳細: [Issue Plan Guide](../../../../../../docs/authoring/issue-plan.md)

## Planning Level

- **selected level: `strict`**
- 理由: public CLI、versioned semantic schema、Artifact redaction、後続全 adapter が依存する common foundation を同時に導入し、公開後の破壊的変更からの回復が難しいため strict を選ぶ。
- risk factor: public CLI/schema、static-analysis safety、Artifact integrity、adapter compatibility、誤比較時の広い説明影響。
- `critical` ではない理由: target repository と persistent user data を変更せず、release/commit 単位で戻せる設計である。
- 再評価条件: secret/PII exposure、target mutation、不可逆 data loss、incident response が必要な rollout を追加する場合。

## 目標

coding agent または人間が、対象 Python repository を実行せずに class 構造を semantic JSON と PlantUML で取得できる。

completion は file/technical layer の完成ではなく、次の observable chain で判定する。

```text
CLI request -> safe source acquisition -> domain semantic analysis
  -> versioned semantic JSON + domain PlantUML -> diagnostic/manifest
  -> acceptance command and exit evidence
```

## 順序・依存

- declared dependency: なし。Initiative/Epic canonical contract と exact baseline だけを前提とする。
- sibling の private parser/model/renderer implementation に依存しない。必要な cross-Issue contract は `semantic-contract.md` と親 Epic Design を正本にする。
- 並行可能: fixture authoring、schema examples、renderer golden、security trap fixture は interface acceptance 固定後に並行できる。
- 統合順: dependency contract verification → source path → semantic model → render/output transaction → acceptance/CI。
- stop condition: Python snapshot の CLI→source selection→AST analysis→semantic JSON/PlantUML→manifest→acceptance test が単独で成立する前に、Git diff、SQLAlchemy row model、Next bridge の実装へ進まない。

| Plan ID | implementation/verification step | Design trace |
| --- | --- | --- |
| I01-PLAN-001 | Requirement fixture と command/manifest contract test を先に追加し、failure/exit behavior を executable acceptance として固定する。 | I01-DES-001 |
| I01-PLAN-002 | 必要最小限の CLI/config/diagnostic/Artifact boundary を planned module に実装し、dependency Issue の public contract を再利用する。 | I01-DES-002 |
| I01-PLAN-003 | python source acquisition と domain-owned semantic analyzer/matcher を実装し、unsafe/unknown を diagnostic へ変換する。 | I01-DES-003 |
| I01-PLAN-004 | semantic JSON と PlantUML renderer、redaction、deterministic ordering、SHA-256 manifest を一つの output transaction へ接続する。 | I01-DES-004 |
| I01-PLAN-005 | negative/security/budget/determinism/partial failure test、documentation、lockfile/license/offline gate を完了し、handoff evidence を作る。 | I01-DES-005 |

## 実装step

### I01-PLAN-001 acceptance-first contract

- planned test files を先に作り、CLI arguments、output filenames、manifest fields、status、exit code を table-driven fixture で固定する。
- user-visible Artifact bytes の golden は source body/secret/absolute path がないことを同時に確認する。
- implementation 未着手時に test が expected failure になることを確認し、誤った既存 behavior を前提にしない。

### I01-PLAN-002 application boundary

- planned modules:

- pyproject.toml と uv.lock（planned）
- src/code_structure_viz/cli/main.py::main（planned）
- src/code_structure_viz/core/config.py::resolve_config（planned）
- src/code_structure_viz/core/diagnostics.py::Diagnostic（planned）
- src/code_structure_viz/artifacts/writer.py::ArtifactPublisher（planned）
- src/code_structure_viz/artifacts/manifest.py::RunManifest（planned）
- src/code_structure_viz/adapters/python/analyzer.py::PythonSnapshotAnalyzer（planned）
- src/code_structure_viz/adapters/python/model.py（planned）
- src/code_structure_viz/adapters/python/renderer.py（planned）

- すべて baseline commit には未実装であり、この Plan は候補 path/symbol を指示する。存在済みとみなさない。
- dependency injection は filesystem、Git process、clock/temp directory、Node process に限定し、domain model を framework へ依存させない。

### I01-PLAN-003 source and semantic implementation

- target 無指定では ignore と scope 設定を適用した repository 内の全 `.py` source を snapshot 対象とする。
- `path:`、`module:`、`class:` target 指定では、解決した seed から typed relation と import relation を用いて upstream/downstream を別々に探索する。
- Python 3.12 以上の syntax を `ast` で解析し、target application を import しない。parse failure は削除や空構造へ変換せず diagnostic と coverage に残す。
- symlink が repository 外へ解決する場合は追跡せず、安全な diagnostic を返す。binary、generated、vendor path は設定された ignore だけで除外し、暗黙の推測を行わない。

- class identity は normalized module path と qualified class name の組である。nested class は outer class を含む qualified name を持つ。
- entity は class、member は field、method、property、decorator metadata、relation は inheritance、composition、typed dependency、import dependency を domain-owned kind として保持する。
- type annotation と signature は正規化して保持するが、default literal、function body、docstring、comment は保持しない。
- whole-repository snapshot は全構造を所有し、targeted snapshot は seed と traversal context、coverage frontier を明示する。

- adapter input/output を immutable value とし、parse failure を empty collection や removed entity へ変換しない。
- budget は collection/render 前に検査し、partial truncation を禁止する。

### I01-PLAN-004 Artifact publication

- semantic JSON は `code-structure-viz.semantic/v1` envelope、domain `python`、document kind `snapshot` を持つ。
- PlantUML は class と field/method を表示し、relation kind を arrow と日本語 legend で区別する。
- run manifest は requested target、resolved scope、resolved config、tool/contract/adapter version、coverage、diagnostic、Artifact relative path、SHA-256 を記録する。
- 対象 Python source がない場合は domain status `not_applicable` とし、空の class diagram を成功 Artifact として捏造しない。

- staging directory は target repository 外を優先し、final fingerprint/collision check 後に rename/copy+fsync strategy で公開する。
- manifest の SHA-256 は final bytes を基準にし、path は output directory 相対とする。

### I01-PLAN-005 hardening and handoff

- `uv run ruff check .`
- `uv run mypy src tests`
- `uv run pytest`
- Next adapter を含む場合は `npm --prefix adapters/next ci --offline`、`npm --prefix adapters/next run typecheck`、`npm --prefix adapters/next test`。
- package build、minimum/latest CI、offline runtime fixture、license inventory を確認する。
- docs は CLI examples、schema version、failure/exit behavior、scope 外を更新する。product HTML command は追加しない。

## 検証

| Test ID | acceptance behavior | planned file | command |
| --- | --- | --- | --- |
| I01-AT-001 | whole repository の Python class/member/relation を JSON と PlantUML へ決定的に出力する。 | tests/acceptance/python/test_snapshot_cli.py | uv run pytest tests/acceptance/python/test_snapshot_cli.py -q |
| I01-AT-002 | path/module/class target と upstream/downstream depth が frontier を正しく制限する。 | tests/integration/python/test_targeted_snapshot.py | uv run pytest tests/integration/python/test_targeted_snapshot.py -q |
| I01-AT-003 | syntax error と unreadable file を削除扱いせず incomplete と diagnostic にする。 | tests/acceptance/python/test_snapshot_failures.py | uv run pytest tests/acceptance/python/test_snapshot_failures.py -q |
| I01-AT-004 | fixture の import side effect、secret literal、absolute path が実行・出力されない。 | tests/security/test_python_static_boundary.py | uv run pytest tests/security/test_python_static_boundary.py -q |
| I01-AT-005 | 同一入力の二回実行で semantic/PlantUML bytes と manifest artifact SHA が一致する。 | tests/acceptance/python/test_snapshot_determinism.py | uv run pytest tests/acceptance/python/test_snapshot_determinism.py -q |
| I01-AT-006 | 501 entity は無切り捨て failure、明示 600 override は成功する。 | tests/acceptance/python/test_snapshot_budget.py | uv run pytest tests/acceptance/python/test_snapshot_budget.py -q |

### issue gate commands

```bash
uv run pytest tests/acceptance/python/test_snapshot_cli.py -q
uv run pytest tests/integration/python/test_targeted_snapshot.py -q
uv run pytest tests/acceptance/python/test_snapshot_failures.py -q
uv run pytest tests/security/test_python_static_boundary.py -q
uv run pytest tests/acceptance/python/test_snapshot_determinism.py -q
uv run pytest tests/acceptance/python/test_snapshot_budget.py -q
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

- persistent data migration は N/A。release 前は Issue 単位で revert する。schema/CLI を preview 公開した後は既存 v1 reader を壊さず、v1 additive fix または新 schema version で forward recovery する。
- rollback trigger: acceptance regression、source execution/mutation、secret/absolute path leak、incorrect successful exit、ambiguous moved の誤採用。
- rollback unit: Issue の production code、tests、schema/doc additionsを一体で revert する。dependency Issue の accepted contract は戻さない。
- forward recovery: unsafe pattern を `incomplete`/`unknown` へ狭め、誤った success を継続しない。既存 Artifact を自動 rewrite しない。
- output migration は N/A。Artifact は immutable run output であり、既存 output を上書きしない。

## exit / handoff

- I01-AC-001〜I01-AC-006 の acceptance evidence が揃う。
- Requirement→Design→Plan→test trace に gap がない。
- planned path honesty を review し、実装時点の実在 path/symbol と差異があれば Design/Plan を先に更新する。
- residual risk、unsupported static pattern、coverage limitation、explicit override を release note と manifest diagnostic contract に残す。
- downstream handoff: internal foundation を兼ねる最初の利用可能 slice。ただし release milestone とはせず、Python diff 完了後に Python domain preview とする。
- completion 後も implementation/report の実績は canonical Report に別途記録し、本 Plan を実行ログにしない。
