---
種別: 設計書（Epic）
ID: "epic-00002"
タイトル: "Establish Safe Git Structure Comparison"
関連GitHub: ["#2"]
状態: "draft"
最終更新: "2026-08-24"
依存: ["requirement.md"]
親: ["init-00001"]
---

# epic-00002 Establish Safe Git Structure Comparison — 設計

詳細: [Design Guide](../../../../docs/authoring/design.md)

## 設計目標

- one Epic の中で safe source comparison spine と three domain semantics を seven independently acceptable vertical slices にする。
- first slice に common foundation を必要最小限だけ含め、後続 slice は stable contract を additive に拡張する。
- each Issue は CLI input、source acquisition、domain analysis、JSON、PlantUML、diagnostic、acceptance test を end-to-end で所有する。
- cross-Issue contract は versioned schema/port とし、private implementation/class/module layout を dependency にしない。

| Design ID | Requirement trace | Epic decision |
| --- | --- | --- |
| EPIC-DES-001 | EPIC-REQ-001, EPIC-REQ-007 | seven vertical slice DAG と two release gates を採用する。 |
| EPIC-DES-002 | EPIC-REQ-002 | SourceView/FileChangeSet/DualSnapshot/ImpactGraph を reusable spine にする。 |
| EPIC-DES-003 | EPIC-REQ-003 | minimal common envelope と three domain-owned adapters を分離する。 |
| EPIC-DES-004 | EPIC-REQ-004, EPIC-REQ-005 | OutputTransaction、manifest、status/exit aggregation を cross-Issue contract にする。 |
| EPIC-DES-005 | EPIC-REQ-006 | Python package と optional Next workspace、two lockfiles、CI matrix を採用する。 |
| EPIC-DES-006 | EPIC-REQ-008 | HTML/runtime/legacy/public plugin boundary を product architecture 外に置く。 |

## Current / Target

Current は one Initiative/one Epic/one provisional Issue の template scaffold。Target は exactly one Epic の下に seven vertical Issues、intermediate/final release、acyclic dependency、full traceability を持つ product plan。

```plantuml
@startuml
title Epic の vertical Issue dependency DAG
left to right direction
rectangle "ISSUE-01
Python snapshot" as I01
rectangle "ISSUE-02
Python diff" as I02
rectangle "ISSUE-03
SQLAlchemy snapshot" as I03
rectangle "ISSUE-04
SQLAlchemy diff
intermediate release" as I04
rectangle "ISSUE-05
Next snapshot" as I05
rectangle "ISSUE-06
Next diff" as I06
rectangle "ISSUE-07
all-domain run
Initiative completion" as I07
I01 --> I02
I01 --> I03
I02 --> I04
I03 --> I04
I01 --> I05
I02 --> I06
I05 --> I06
I04 --> I07
I06 --> I07
@enduml
```

## 責務・Interface

| Cross-Issue contract | Introduced/owned by | Consumers |
| --- | --- | --- |
| CLI/config/diagnostic/Artifact minimal v1 | ISSUE-01 | ISSUE-02〜07 |
| named endpoint/read-only Git/freeze/FileChangeSet/dual diff | ISSUE-02 | ISSUE-04, ISSUE-06, ISSUE-07 |
| SQLAlchemy table/row snapshot | ISSUE-03 | ISSUE-04, ISSUE-07 |
| SQLAlchemy row diff/ghost/matching | ISSUE-04 | ISSUE-07 |
| Next adapter protocol/component snapshot | ISSUE-05 | ISSUE-06, ISSUE-07 |
| Next component diff/matching/unknown | ISSUE-06 | ISSUE-07 |
| domain registry/outcome aggregation/output transaction | ISSUE-07 | final CLI release |

### package architecture (planned)

```text
src/code_structure_viz/
  cli/                 command grammar and exit mapping
  application/         snapshot/diff/run coordination
  core/                config, diagnostic, status, budget
  source/              read-only Git, endpoint, freezer, SourceView, FileChangeSet
  semantic/            envelope, graph primitive, diff/impact ports
  artifacts/           JSON/PlantUML descriptors, manifest, output transaction
  adapters/python/     Python-owned semantics
  adapters/sqlalchemy/ SQLAlchemy-owned semantics
  adapters/next/       Python bridge only
adapters/next/
  src/                 repository-owned TypeScript semantics
  test/                compiler/protocol fixtures
tests/                 unit/integration/acceptance/security/packaging
```

すべて planned path であり、baseline に存在すると主張しない。

## data / failure

- common envelope and manifest are detailed in `package/artifacts/semantic-contract.md`.
- endpoint combinations and exit/failure examples are detailed in `package/artifacts/cli-behavior-matrix.md`.
- `DomainResult` is a discriminated union complete/not_applicable/incomplete, never `None`/empty ambiguity.
- `RunOutcome` maps core fatal/usage/interrupt before domain aggregation; domain incomplete after a valid core run maps exit 3.
- OutputTransaction stages all selected domain payloads and publishes only after collision/fingerprint/integrity verification.

## 変更対象

- Initiative/Epic canonical R/D/P whole-file replacement through adoption gate。
- seven new Issue node creation and whole-file R/D/P copy。
- explanation HTML and package artifacts are evidence imports, not product runtime files。
- production code/tests/docs/CI roots are created during Issue implementation, not by this specification package。

## 移行・互換性・rollback

- existing `iss-00003` は silent rename せず supersede し、Git comparison concern は ISSUE-02 が所有する。
- Issue rollout は topological order で進める。downstream Issue は Plan 内で parent acceptance や dependency direction を変更できない。
- intermediate release after ISSUE-04 is maintained while Next work proceeds.
- rollback removes the latest vertical slice while retaining prior accepted CLI/schema compatibility; public break requires version up.

## testability

- each Issue has independent acceptance commands and stop condition.
- Epic integration runs dependency contract fixtures, all acceptance suites, cross-domain partial failure, package/offline/license/CI matrix.
- verticality check rejects an Issue that cannot produce user-visible JSON/PlantUML/diagnostic without unfinished sibling internals.
- DAG and trace matrix are machine-checkable from MANIFEST.json and artifacts.

## risk

| Risk | Control |
| --- | --- |
| ISSUE-01 becomes a framework project | Only implement foundation exercised by Python snapshot acceptance. |
| duplicate diff implementations drift | Reuse source/endpoint ports; keep matching/render semantics adapter-owned. |
| ISSUE-07 becomes horizontal integration only | Require one-command multi-domain observable result, partial Artifact retention, manifest/exit acceptance. |
| provisional Issue history misleads | Supersede iss-00003 with explicit mapping to ISSUE-02. |
| release gate hidden in implementation | Record M2/M4 in Epic Requirement/Plan and acceptance matrix. |
