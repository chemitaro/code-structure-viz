---
種別: 実装計画書（Issue）
ID: "iss-00009"
タイトル: "Compare Next.js Component Changes"
関連GitHub: ["#9"]
package_sequence_key: "ISSUE-06"
状態: "draft"
最終更新: "2026-08-24"
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

- declared dependency: ISSUE-02, ISSUE-05
- sibling の private parser/model/renderer implementation に依存しない。必要な cross-Issue contract は `semantic-contract.md` と親 Epic Design を正本にする。
- 並行可能: fixture authoring、schema examples、renderer golden、security trap fixture は interface acceptance 固定後に並行できる。
- 統合順: dependency contract verification → source path → semantic model → render/output transaction → acceptance/CI。
- stop condition: Next member/relation seed、union impact、adapter partial failure、unknown dynamic behavior が acceptance で固定されるまで全 domain 集約へ進まない。

| Plan ID | implementation/verification step | Design trace |
| --- | --- | --- |
| I06-PLAN-001 | Requirement fixture と command/manifest contract test を先に追加し、failure/exit behavior を executable acceptance として固定する。 | I06-DES-001 |
| I06-PLAN-002 | 必要最小限の CLI/config/diagnostic/Artifact boundary を planned module に実装し、dependency Issue の public contract を再利用する。 | I06-DES-002 |
| I06-PLAN-003 | next source acquisition と domain-owned semantic analyzer/matcher を実装し、unsafe/unknown を diagnostic へ変換する。 | I06-DES-003 |
| I06-PLAN-004 | semantic JSON と PlantUML renderer、redaction、deterministic ordering、SHA-256 manifest を一つの output transaction へ接続する。 | I06-DES-004 |
| I06-PLAN-005 | negative/security/budget/determinism/partial failure test、documentation、lockfile/license/offline gate を完了し、handoff evidence を作る。 | I06-DES-005 |

## 実装step

### I06-PLAN-001 acceptance-first contract

- planned test files を先に作り、CLI arguments、output filenames、manifest fields、status、exit code を table-driven fixture で固定する。
- user-visible Artifact bytes の golden は source body/secret/absolute path がないことを同時に確認する。
- implementation 未着手時に test が expected failure になることを確認し、誤った既存 behavior を前提にしない。

### I06-PLAN-002 application boundary

- planned modules:

- adapters/next/src/diff.ts::diffNextSnapshots（planned）
- adapters/next/src/matcher.ts::matchMovedComponents（planned）
- adapters/next/src/diff-render.ts（planned）
- src/code_structure_viz/adapters/next/diff_bridge.py（planned）
- src/code_structure_viz/semantic/impact.py の Next relation extension（planned）

- すべて baseline commit には未実装であり、この Plan は候補 path/symbol を指示する。存在済みとみなさない。
- dependency injection は filesystem、Git process、clock/temp directory、Node process に限定し、domain model を framework へ依存させない。

### I06-PLAN-003 source and semantic implementation

- ISSUE-02 の named endpoint、read-only Git、working-tree freeze、fingerprint、FileChangeSet を使い、両 endpoint で ISSUE-05 adapter を独立実行する。
- before/after の tsconfig/jsconfig と source set を各 snapshot provenance に固定し、after config を before source 解決へ流用しない。
- Node adapter が片側で unavailable/invalid response の場合は component removal/addition を推測せず incomplete。

- module/exported component/prop/import/relation/use client boundary の semantic delta を changed seed とする。format、comment、import order だけは seed にしない。
- props、static import、literal dynamic import、JSX render、client/server boundary を member/relation-level に色分けする。
- component moved は one-to-one、module rename/name evidence、structural fingerprint、unique candidate の全条件を満たす場合だけ採用し、曖昧なら removed+added。
- impact graph は before/after static relation union。removed component は before import/render edge を使い、upstream/downstream を別 depth で探索する。
- non-literal dynamic behavior と runtime component tree は unknown/coverage limitation のまま比較し、推測による relation delta を作らない。

- adapter input/output を immutable value とし、parse failure を empty collection や removed entity へ変換しない。
- budget は collection/render 前に検査し、partial truncation を禁止する。

### I06-PLAN-004 Artifact publication

- Next diff JSON は before/after adapter contract/version/config digest、component/member/relation change、matching evidence、impact context を持つ。
- PlantUML は component と props/import/relation を `+ - ~ → ?` と green/red/yellow/blue/gray、removed dashed で表示する。
- adapter 部分 failure でも Python/SQLAlchemy 等の sibling Artifact を消さないための domain status を返せる。

- staging directory は target repository 外を優先し、final fingerprint/collision check 後に rename/copy+fsync strategy で公開する。
- manifest の SHA-256 は final bytes を基準にし、path は output directory 相対とする。

### I06-PLAN-005 hardening and handoff

- `uv run ruff check .`
- `uv run mypy src tests`
- `uv run pytest`
- Next adapter を含む場合は `npm --prefix adapters/next ci --offline`、`npm --prefix adapters/next run typecheck`、`npm --prefix adapters/next test`。
- package build、minimum/latest CI、offline runtime fixture、license inventory を確認する。
- docs は CLI examples、schema version、failure/exit behavior、scope 外を更新する。product HTML command は追加しない。

## 検証

| Test ID | acceptance behavior | planned file | command |
| --- | --- | --- | --- |
| I06-AT-001 | component/prop/import/render/boundary change を member-level JSON と PlantUML にする。 | tests/acceptance/next/test_diff_cli.py | uv run pytest tests/acceptance/next/test_diff_cli.py -q |
| I06-AT-002 | format/comment/import-order only は seed にならず static relation change は seed になる。 | adapters/next/test/semantic-seed.test.ts | npm --prefix adapters/next test -- semantic-seed |
| I06-AT-003 | 一意 component move だけ moved、ambiguous candidate は removed+added。 | adapters/next/test/move-matching.test.ts | npm --prefix adapters/next test -- move-matching |
| I06-AT-004 | 片側 adapter/config failure を removal にせず incomplete にする。 | tests/acceptance/next/test_diff_failures.py | uv run pytest tests/acceptance/next/test_diff_failures.py -q |
| I06-AT-005 | removed component の before edge を union graph context に保持する。 | tests/integration/next/test_impact_union_graph.py | uv run pytest tests/integration/next/test_impact_union_graph.py -q |
| I06-AT-006 | nonliteral dynamic behavior を unknown とし runtime relation を生成しない。 | adapters/next/test/dynamic-unknown.test.ts | npm --prefix adapters/next test -- dynamic-unknown |

### issue gate commands

```bash
uv run pytest tests/acceptance/next/test_diff_cli.py -q
npm --prefix adapters/next test -- semantic-seed
npm --prefix adapters/next test -- move-matching
uv run pytest tests/acceptance/next/test_diff_failures.py -q
uv run pytest tests/integration/next/test_impact_union_graph.py -q
npm --prefix adapters/next test -- dynamic-unknown
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

- persistent migration は N/A。adapter diff failure は domain incomplete へ隔離する。公開 contract の誤りは旧 reader/golden fixture を保持した additive fix、または adapter/semantic schema version up で回復する。
- rollback trigger: acceptance regression、source execution/mutation、secret/absolute path leak、incorrect successful exit、ambiguous moved の誤採用。
- rollback unit: Issue の production code、tests、schema/doc additionsを一体で revert する。dependency Issue の accepted contract は戻さない。
- forward recovery: unsafe pattern を `incomplete`/`unknown` へ狭め、誤った success を継続しない。既存 Artifact を自動 rewrite しない。
- output migration は N/A。Artifact は immutable run output であり、既存 output を上書きしない。

## exit / handoff

- I06-AC-001〜I06-AC-006 の acceptance evidence が揃う。
- Requirement→Design→Plan→test trace に gap がない。
- planned path honesty を review し、実装時点の実在 path/symbol と差異があれば Design/Plan を先に更新する。
- residual risk、unsupported static pattern、coverage limitation、explicit override を release note と manifest diagnostic contract に残す。
- downstream handoff: Next domain diff preview。ISSUE-07 の統合前でも `--domain next` の単独利用が可能な acceptance boundary。
- completion 後も implementation/report の実績は canonical Report に別途記録し、本 Plan を実行ログにしない。
