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

- declared dependency: ISSUE-04, ISSUE-06
- sibling の private parser/model/renderer implementation に依存しない。必要な cross-Issue contract は `semantic-contract.md` と親 Epic Design を正本にする。
- 並行可能: fixture authoring、schema examples、renderer golden、security trap fixture は interface acceptance 固定後に並行できる。
- 統合順: dependency contract verification → source path → semantic model → render/output transaction → acceptance/CI。
- stop condition: 三 domain の applicability、partial success retention、aggregate manifest、exit code、atomicity、minimum/latest CI が acceptance で成立するまで Initiative を完了扱いにしない。

| Plan ID | implementation/verification step | Design trace |
| --- | --- | --- |
| I07-PLAN-001 | Requirement fixture と command/manifest contract test を先に追加し、failure/exit behavior を executable acceptance として固定する。 | I07-DES-001 |
| I07-PLAN-002 | 必要最小限の CLI/config/diagnostic/Artifact boundary を planned module に実装し、dependency Issue の public contract を再利用する。 | I07-DES-002 |
| I07-PLAN-003 | all source acquisition と domain-owned semantic analyzer/matcher を実装し、unsafe/unknown を diagnostic へ変換する。 | I07-DES-003 |
| I07-PLAN-004 | semantic JSON と PlantUML renderer、redaction、deterministic ordering、SHA-256 manifest を一つの output transaction へ接続する。 | I07-DES-004 |
| I07-PLAN-005 | negative/security/budget/determinism/partial failure test、documentation、lockfile/license/offline gate を完了し、handoff evidence を作る。 | I07-DES-005 |
| I07-PLAN-006 | CI minimum/latest lane と full regression を通し、rollback/forward recovery 条件を review する。 | I07-DES-006 |

## 実装step

### I07-PLAN-001 acceptance-first contract

- planned test files を先に作り、CLI arguments、output filenames、manifest fields、status、exit code を table-driven fixture で固定する。
- user-visible Artifact bytes の golden は source body/secret/absolute path がないことを同時に確認する。
- implementation 未着手時に test が expected failure になることを確認し、誤った既存 behavior を前提にしない。

### I07-PLAN-002 application boundary

- planned modules:

- src/code_structure_viz/application/run.py::RunCoordinator（planned）
- src/code_structure_viz/application/domain_registry.py::FirstPartyDomainRegistry（planned）
- src/code_structure_viz/core/outcome.py::RunOutcome（planned）
- src/code_structure_viz/artifacts/manifest.py::AggregateManifestBuilder（planned）
- src/code_structure_viz/artifacts/transaction.py::OutputTransaction（planned）
- src/code_structure_viz/cli/exit_codes.py（planned）
- .github/workflows/ci.yml の minimum/latest matrix（planned）

- すべて baseline commit には未実装であり、この Plan は候補 path/symbol を指示する。存在済みとみなさない。
- dependency injection は filesystem、Git process、clock/temp directory、Node process に限定し、domain model を framework へ依存させない。

### I07-PLAN-003 source and semantic implementation

- diff で domain 無指定なら python、sqlalchemy、next を deterministic order で実行する。snapshot も同じ default を採用し、明示 domain で絞り込める。
- core preflight、endpoint resolution、working-tree freeze、resolved config は一 run で共有するが、各 adapter は domain-owned source selection と semantic model を保持する。
- Next target 不在なら Node を要求しない。domain applicability preflight は source presence と safe static indicator だけで行い、application を実行しない。
- 一つの output transaction で domain Artifact と run manifest を staging し、fingerprint と collision gate 後に公開する。

- common envelope は run/domain status、artifact descriptor、diagnostic、coverage、graph primitive だけを共有し、domain identity/member/relation/matching を統一 model へ押し込まない。
- domain status は `complete`、`not_applicable`、`incomplete`。overall は全 selected domain が complete/not_applicable なら complete、少なくとも一つ incomplete かつ core run が成立すれば incomplete。
- FileChangeSet は run-level evidence、SemanticChangeSet は domain-level ownership。cross-domain relation を初期 release で推測しない。
- resolved config、version、endpoint、fingerprint、domain status、coverage、diagnostic、各 Artifact relative path/SHA-256 を一つの manifest に集約する。

- adapter input/output を immutable value とし、parse failure を empty collection や removed entity へ変換しない。
- budget は collection/render 前に検査し、partial truncation を禁止する。

### I07-PLAN-004 Artifact publication

- format 未指定時は complete/incomplete domain ごとに versioned semantic JSON と domain-specific PlantUML を生成する。not_applicable domain は status/diagnostic のみ。
- exit 0 は overall complete、1 は core fatal analysis/environment、2 は usage/config、3 は domain incomplete、130 は interrupt。
- exit 3 でも complete domain の Artifact と manifest を保持する。fatal fingerprint drift や unresolved endpoint では success Artifact を公開しない。
- manifest の Artifact path は output directory 相対、SHA-256 は公開 bytes に対して計算し、absolute path を含めない。

- staging directory は target repository 外を優先し、final fingerprint/collision check 後に rename/copy+fsync strategy で公開する。
- manifest の SHA-256 は final bytes を基準にし、path は output directory 相対とする。

### I07-PLAN-006 hardening and handoff

- `uv run ruff check .`
- `uv run mypy src tests`
- `uv run pytest`
- Next adapter を含む場合は `npm --prefix adapters/next ci --offline`、`npm --prefix adapters/next run typecheck`、`npm --prefix adapters/next test`。
- package build、minimum/latest CI、offline runtime fixture、license inventory を確認する。
- docs は CLI examples、schema version、failure/exit behavior、scope 外を更新する。product HTML command は追加しない。

## 検証

| Test ID | acceptance behavior | planned file | command |
| --- | --- | --- | --- |
| I07-AT-001 | domain 無指定で三 domain を順に実行し、一つの aggregate manifest を出力する。 | tests/acceptance/test_multi_domain_cli.py | uv run pytest tests/acceptance/test_multi_domain_cli.py -q |
| I07-AT-002 | Next incomplete、Python/SQLAlchemy complete で Artifact を保持し exit 3 にする。 | tests/acceptance/test_partial_domain_failure.py | uv run pytest tests/acceptance/test_partial_domain_failure.py -q |
| I07-AT-003 | Next target なしは Node 未導入でも not_applicable、overall exit 0。 | tests/acceptance/test_multi_domain_applicability.py | uv run pytest tests/acceptance/test_multi_domain_applicability.py -q |
| I07-AT-004 | endpoint/fingerprint/output collision の run-level failure で success Artifact を公開しない。 | tests/acceptance/test_run_atomicity.py | uv run pytest tests/acceptance/test_run_atomicity.py -q |
| I07-AT-005 | 0/1/2/3/130 と stdout/stderr/manifest の組合せを table-driven に検証する。 | tests/acceptance/test_exit_codes.py | uv run pytest tests/acceptance/test_exit_codes.py -q |
| I07-AT-006 | macOS/Linux、Python 3.12 と latest stable、Git 2.39 と latest、Next 選択時 Node 22 と latest を CI で確認する。 | .github/workflows/ci.yml | uv run pytest && npm --prefix adapters/next test |
| I07-AT-007 | uv lock/npm lock、license inventory、offline runtime install fixture を検証する。 | tests/packaging/test_offline_install.py | uv run pytest tests/packaging/test_offline_install.py -q |

### issue gate commands

```bash
uv run pytest tests/acceptance/test_multi_domain_cli.py -q
uv run pytest tests/acceptance/test_partial_domain_failure.py -q
uv run pytest tests/acceptance/test_multi_domain_applicability.py -q
uv run pytest tests/acceptance/test_run_atomicity.py -q
uv run pytest tests/acceptance/test_exit_codes.py -q
uv run pytest && npm --prefix adapters/next test
uv run pytest tests/packaging/test_offline_install.py -q
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

- persistent data migration は N/A。rollout は intermediate release→Next opt-in preview→default all-domain の順。partial outcome/exit bug は default all-domain を無効化して明示 domain へ戻し、schema compatibility を保った forward fix を行う。
- rollback trigger: acceptance regression、source execution/mutation、secret/absolute path leak、incorrect successful exit、ambiguous moved の誤採用。
- rollback unit: Issue の production code、tests、schema/doc additionsを一体で revert する。dependency Issue の accepted contract は戻さない。
- forward recovery: unsafe pattern を `incomplete`/`unknown` へ狭め、誤った success を継続しない。既存 Artifact を自動 rewrite しない。
- output migration は N/A。Artifact は immutable run output であり、既存 output を上書きしない。

## exit / handoff

- I07-AC-001〜I07-AC-007 の acceptance evidence が揃う。
- Requirement→Design→Plan→test trace に gap がない。
- planned path honesty を review し、実装時点の実在 path/symbol と差異があれば Design/Plan を先に更新する。
- residual risk、unsupported static pattern、coverage limitation、explicit override を release note と manifest diagnostic contract に残す。
- downstream handoff: Next.js 対応と multi-domain orchestration の完了をもって Initiative 完了。Python+SQLAlchemy intermediate release からの additive extension とする。
- completion 後も implementation/report の実績は canonical Report に別途記録し、本 Plan を実行ログにしない。
