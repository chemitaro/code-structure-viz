---
種別: 実装計画書（Issue）
ID: "iss-00008"
タイトル: "Generate Next.js Component Snapshots"
関連GitHub: ["#8"]
package_sequence_key: "ISSUE-05"
状態: "draft"
最終更新: "2026-08-24"
依存: ["requirement.md", "design.md"]
親: ["epic-00002", "init-00001"]
---

# iss-00008 Generate Next.js Component Snapshots — 実装計画

詳細: [Issue Plan Guide](../../../../../../docs/authoring/issue-plan.md)

## Planning Level

- **selected level: `strict`**
- 理由: cross-runtime versioned protocol、optional dependency、TypeScript semantic boundary、static-analysis security contract を導入し、compatibility failure の回復が難しいため strict を選ぶ。
- risk factor: public CLI/schema、static-analysis safety、Artifact integrity、adapter compatibility、誤比較時の広い説明影響。
- `critical` ではない理由: target repository と persistent user data を変更せず、release/commit 単位で戻せる設計である。
- 再評価条件: secret/PII exposure、target mutation、不可逆 data loss、incident response が必要な rollout を追加する場合。

## 目標

coding agent が first-party TypeScript adapter を通じ、Next.js repository の module、exported component、props、static relation、client boundary を JSON と PlantUML で取得できる。

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
- stop condition: first-party adapter protocol、TS/TSX coverage、JS/JSX safe subset、client boundary、Node optionality が acceptance で成立するまで Next diff へ進まない。

| Plan ID | implementation/verification step | Design trace |
| --- | --- | --- |
| I05-PLAN-001 | Requirement fixture と command/manifest contract test を先に追加し、failure/exit behavior を executable acceptance として固定する。 | I05-DES-001 |
| I05-PLAN-002 | 必要最小限の CLI/config/diagnostic/Artifact boundary を planned module に実装し、dependency Issue の public contract を再利用する。 | I05-DES-002 |
| I05-PLAN-003 | next source acquisition と domain-owned semantic analyzer/matcher を実装し、unsafe/unknown を diagnostic へ変換する。 | I05-DES-003 |
| I05-PLAN-004 | semantic JSON と PlantUML renderer、redaction、deterministic ordering、SHA-256 manifest を一つの output transaction へ接続する。 | I05-DES-004 |
| I05-PLAN-005 | negative/security/budget/determinism/partial failure test、documentation、lockfile/license/offline gate を完了し、handoff evidence を作る。 | I05-DES-005 |

## 実装step

### I05-PLAN-001 acceptance-first contract

- planned test files を先に作り、CLI arguments、output filenames、manifest fields、status、exit code を table-driven fixture で固定する。
- user-visible Artifact bytes の golden は source body/secret/absolute path がないことを同時に確認する。
- implementation 未着手時に test が expected failure になることを確認し、誤った既存 behavior を前提にしない。

### I05-PLAN-002 application boundary

- planned modules:

- src/code_structure_viz/adapters/next/bridge.py::NextAdapterBridge（planned）
- src/code_structure_viz/adapters/next/protocol.py（planned）
- adapters/next/package.json と package-lock.json（planned）
- adapters/next/tsconfig.json（planned）
- adapters/next/src/analyze.ts::analyzeRepository（planned）
- adapters/next/src/model.ts（planned）
- adapters/next/src/render.ts（planned）

- すべて baseline commit には未実装であり、この Plan は候補 path/symbol を指示する。存在済みとみなさない。
- dependency injection は filesystem、Git process、clock/temp directory、Node process に限定し、domain model を framework へ依存させない。

### I05-PLAN-003 source and semantic implementation

- Python core は repository-owned Node bridge を明示 protocol で起動し、TypeScript compiler API を使う。Node.js 22 LTS 以上は Next domain target が存在し、adapter を実行するときだけ要求する。
- TS/TSX を必須対応、JS/JSX は compiler API で安全に parse/type-resolve できる subset を扱う。App Router と Pages Router の repository path を静的に分類する。
- `tsconfig.json`/`jsconfig.json` の extends、baseUrl、paths alias を repository 内で解決する。plugin、build script、Next config function、application module は実行しない。
- static import、literal `dynamic()`/`import()`、static JSX render だけを relation candidate とする。non-literal dynamic path、runtime conditional tree、React reconciliation result は推測しない。

- component identity は repository-relative module path と exported component name。default export は stable exported name metadata を持ち、route path は identity ではなく attribute とする。
- entity は exported component/module、member は props、import/export、client/server boundary metadata、relation は static import、literal dynamic import、JSX render、boundary crossing を domain-owned kind で保持する。
- `"use client"` directive を module boundary として保持し、server/client を推測できない module は unknown とする。
- props は TypeScript type information から name、optional、safe normalized type を保持する。default literal、JSX text/body、comment は保持しない。

- adapter input/output を immutable value とし、parse failure を empty collection や removed entity へ変換しない。
- budget は collection/render 前に検査し、partial truncation を禁止する。

### I05-PLAN-004 Artifact publication

- Node adapter は `code-structure-viz.next-adapter/v1` request/response JSON を stdin/stdout で交換し、Python core が `code-structure-viz.semantic/v1` envelope へ格納する。
- PlantUML component diagram は exported component、props、static import/render relation、use client boundary を表示する。
- Node/TypeScript/package version、adapter contract version、tsconfig path、coverage、diagnostic、Artifact hash を manifest に記録する。
- Next target 不在は Node を要求せず not_applicable。target あり Node/adapter unavailable は incomplete と exit 3。

- staging directory は target repository 外を優先し、final fingerprint/collision check 後に rename/copy+fsync strategy で公開する。
- manifest の SHA-256 は final bytes を基準にし、path は output directory 相対とする。

### I05-PLAN-005 hardening and handoff

- `uv run ruff check .`
- `uv run mypy src tests`
- `uv run pytest`
- Next adapter を含む場合は `npm --prefix adapters/next ci --offline`、`npm --prefix adapters/next run typecheck`、`npm --prefix adapters/next test`。
- package build、minimum/latest CI、offline runtime fixture、license inventory を確認する。
- docs は CLI examples、schema version、failure/exit behavior、scope 外を更新する。product HTML command は追加しない。

## 検証

| Test ID | acceptance behavior | planned file | command |
| --- | --- | --- | --- |
| I05-AT-001 | App/Pages Router の TS/TSX component、props、static relation、use client を出力する。 | tests/acceptance/next/test_snapshot_cli.py | uv run pytest tests/acceptance/next/test_snapshot_cli.py -q |
| I05-AT-002 | versioned stdin/stdout JSON と Python envelope mapping を contract fixture で検証する。 | tests/contract/next/test_bridge_protocol.py | uv run pytest tests/contract/next/test_bridge_protocol.py -q |
| I05-AT-003 | JS/JSX safe subset は解析し、unsafe dynamic behavior は unknown にする。 | adapters/next/test/javascript-safe-subset.test.ts | npm --prefix adapters/next test -- --runInBand |
| I05-AT-004 | Node missing、schema mismatch、protocol noise、tsconfig alias failure を incomplete にする。 | tests/acceptance/next/test_snapshot_failures.py | uv run pytest tests/acceptance/next/test_snapshot_failures.py -q |
| I05-AT-005 | build/config/plugin/application module を実行せず、literal/body/absolute path を出力しない。 | tests/security/test_next_static_boundary.py | uv run pytest tests/security/test_next_static_boundary.py -q |
| I05-AT-006 | Next target なしでは Node probe を行わず not_applicable。 | tests/acceptance/next/test_applicability.py | uv run pytest tests/acceptance/next/test_applicability.py -q |

### issue gate commands

```bash
uv run pytest tests/acceptance/next/test_snapshot_cli.py -q
uv run pytest tests/contract/next/test_bridge_protocol.py -q
npm --prefix adapters/next test -- --runInBand
uv run pytest tests/acceptance/next/test_snapshot_failures.py -q
uv run pytest tests/security/test_next_static_boundary.py -q
uv run pytest tests/acceptance/next/test_applicability.py -q
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

- data migration は N/A。Node adapter release は Python package と互換 matrix を固定する。protocol mismatch は adapter を incomplete として隔離し、旧 protocol reader を保持した additive fix または version up で forward recovery する。
- rollback trigger: acceptance regression、source execution/mutation、secret/absolute path leak、incorrect successful exit、ambiguous moved の誤採用。
- rollback unit: Issue の production code、tests、schema/doc additionsを一体で revert する。dependency Issue の accepted contract は戻さない。
- forward recovery: unsafe pattern を `incomplete`/`unknown` へ狭め、誤った success を継続しない。既存 Artifact を自動 rewrite しない。
- output migration は N/A。Artifact は immutable run output であり、既存 output を上書きしない。

## exit / handoff

- I05-AC-001〜I05-AC-006 の acceptance evidence が揃う。
- Requirement→Design→Plan→test trace に gap がない。
- planned path honesty を review し、実装時点の実在 path/symbol と差異があれば Design/Plan を先に更新する。
- residual risk、unsupported static pattern、coverage limitation、explicit override を release note と manifest diagnostic contract に残す。
- downstream handoff: Next snapshot preview。Python/SQLAlchemy の install/runtime requirement へ Node を持ち込まない optional adapter separation を完成させる。
- completion 後も implementation/report の実績は canonical Report に別途記録し、本 Plan を実行ログにしない。
