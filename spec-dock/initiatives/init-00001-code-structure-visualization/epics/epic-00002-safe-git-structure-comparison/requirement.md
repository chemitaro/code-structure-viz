---
種別: 要件定義書（Epic）
ID: "epic-00002"
タイトル: "Establish Safe Git Structure Comparison"
関連GitHub: ["#2"]
状態: "draft"
最終更新: "2026-08-24"
親: ["init-00001"]
---

# epic-00002 Establish Safe Git Structure Comparison — 要件定義

詳細: [Requirement Guide](../../../../docs/authoring/requirement.md)

## 目的

safe Git structure comparison を product spine とし、三 domain の static snapshot/diff を coding agent が一貫して利用できる状態を一つの Epic で届ける。Epic は domain implementation を横断 layer に分解せず、observable vertical outcomes と stable cross-Issue contract を定める。

## 背景

- 親 Initiative の全 product scope を本 Epic 一つが担う。既存 title は保持するが、Git comparison だけでなく snapshot、domain semantics、Artifact、partial failure、packaging まで不足なく含む。
- existing `iss-00003` は provisional horizontal scaffold で、Issue boundary の authority ではない。
- accepted ADR は dual snapshot、named endpoint、adapter ownership、agent-first Artifact、安全 boundary、vertical slicing を要求する。

## 観測可能な要件

| ID | contract area | Epic requirement |
| --- | --- | --- |
| EPIC-REQ-001 | vertical domain delivery | Python、SQLAlchemy、Next の snapshot/diff と all-domain orchestration を seven independently acceptable vertical Issues で届ける。 |
| EPIC-REQ-002 | safe comparison spine | named endpoints、immutable SourceView、working-tree freeze、read-only Git、dual semantic snapshot、impact union を横断 contract にする。 |
| EPIC-REQ-003 | semantic ownership | common envelope と domain-owned identity/member/relation/matching を分離する。 |
| EPIC-REQ-004 | Artifact/output | JSON/PlantUML selectable default-both、manifest provenance、redaction、determinism、no overwrite を全 slice で維持する。 |
| EPIC-REQ-005 | failure and budgets | complete/not_applicable/incomplete、partial success、0/1/2/3/130、1000/500/depth 1+1 default を維持する。 |
| EPIC-REQ-006 | platform/dependency | Python 3.12+ core、Node 22+ optional Next、Git 2.39+、macOS/Linux、lock/license/offline/minimum/latest CI を提供する。 |
| EPIC-REQ-007 | release order | ISSUE-04 を intermediate release、ISSUE-07 を Initiative completion boundary とする。 |
| EPIC-REQ-008 | exclusions | product HTML、runtime/DB/build execution、Windows、plugin ABI、legacy dependency/compatibility を実装しない。 |

### Issue ownership

| Stable key | title | observable outcome | dependency |
| --- | --- | --- | --- |
| ISSUE-01 | Generate Python Structure Snapshots | coding agent または人間が、対象 Python repository を実行せずに class 構造を semantic JSON と PlantUML で取得できる。 | なし |
| ISSUE-02 | Compare Python Structure Changes Safely | coding agent が named endpoint で before/after Python semantic snapshot を安全に固定し、意味のある class/member/relation change と影響 context だけを比較できる。 | ISSUE-01 |
| ISSUE-03 | Generate SQLAlchemy ER Snapshots | coding agent が DB や application を起動せず、SQLAlchemy declarative ORM source から table と row-level ER semantics を JSON と PlantUML で取得できる。 | ISSUE-01 |
| ISSUE-04 | Compare SQLAlchemy ER Changes | coding agent が before/after declarative ORM semantics を比較し、table と column/constraint/index/relationship の row-level delta、ghost removal、影響 context を説明できる。 | ISSUE-02, ISSUE-03 |
| ISSUE-05 | Generate Next.js Component Snapshots | coding agent が first-party TypeScript adapter を通じ、Next.js repository の module、exported component、props、static relation、client boundary を JSON と PlantUML で取得できる。 | ISSUE-01 |
| ISSUE-06 | Compare Next.js Component Changes | coding agent が before/after Next.js semantic snapshot から component/props/import/render/boundary change と影響 context を比較できる。 | ISSUE-02, ISSUE-05 |
| ISSUE-07 | Run Unified Multi-Domain Structure Comparison | coding agent が domain を省略した一回の command で Python、SQLAlchemy、Next の適用可否・成功・不完全を区別し、成功 Artifact を保持した集約 manifest と正しい exit code を得られる。 | ISSUE-04, ISSUE-06 |

## スコープ

### 対象

- source acquisition、snapshot、semantic diff、impact traversal、three first-party domain adapters、JSON/PlantUML/manifest、diagnostic、CI/package。
- Issue 間の versioned contract と rollout/integration order。
- intermediate release と final Initiative completion gate。

### 対象外

- contract-only/source-freezer-only/parser-only/renderer-only の horizontal Issue。
- product HTML report/command/publication とその schema/UI/distribution。
- runtime analysis、mutable Git、DB/Alembic/build execution、legacy dependency/compatibility。

## 失敗・境界条件

- sibling internals が安定しないまま共有される場合は integration を停止し、parent Design の stable contract を更新する。
- domain target の applicability/failure を overall empty result へ潰さない。
- fingerprint drift、endpoint unresolved、output collision は run-level publication stop。adapter failure は domain incomplete と partial success retention。
- budget 超過を truncation で成功扱いしない。
- cross-domain universal semantics や runtime relation を Issue が独自に発明しない。

## 受け入れ条件

| ID | Epic completion evidence |
| --- | --- |
| EPIC-AC-001 | ISSUE-01 の Python snapshot acceptance が成立。 |
| EPIC-AC-002 | ISSUE-02 の Python dual-snapshot diff/Git safety acceptance が成立。 |
| EPIC-AC-003 | ISSUE-03/04 の SQLAlchemy snapshot/row diff acceptance と intermediate release gate が成立。 |
| EPIC-AC-004 | ISSUE-05/06 の Next snapshot/diff、protocol、Node optionality acceptance が成立。 |
| EPIC-AC-005 | ISSUE-07 の all-domain/partial success/exit/manifest acceptance が成立。 |
| EPIC-AC-006 | 全 Issue の Requirement→Design→Plan→test trace と DAG が完全。 |
| EPIC-AC-007 | read-only/static/redaction/determinism/budget/platform/package regression が全体で成功。 |
| EPIC-AC-008 | product HTML scope exclusion と specification HTML separation が維持。 |

`EPIC-AC-001`〜`EPIC-AC-008` の全条件と `INIT-AC-001`〜`INIT-AC-008` trace が成立したときだけ Epic complete とする。

## 制約・前提

- Issue stable key は package/adoption sequencing 用であり、SpecDock が割り当てる実 node ID を偽らない。
- existing `iss-00003` は semantic material を ISSUE-02 へ反映するが、managed metadata を直接 rename できる根拠がないため node 自体は supersede 推奨。
- planned production path/symbol は baseline に存在しない。Issue Plan の候補であり、実装時に repository facts と照合する。
- common dependency、version pin、license、lockfile、offline runtime、optional Node separation を各 Issue acceptance に含める。
