# Issue Slicing Assessment

## 結論

`PROPOSED_ISSUE_CANDIDATES`。親 Epic `epic-00002` は一つの coherent product outcome だが、snapshot と temporal diff、三 domain、all-domain partial-success orchestration に独立 acceptance/rollback boundary があるため、最小の実装可能な proposal は seven vertical Issues とする。

これは package/adoption proposal であり、SpecDock node/GitHub Issue を作成・採用した事実ではない。

## Parent contract

- one Initiative `init-00001`、exactly one Epic `epic-00002`。
- Python class、SQLAlchemy ER、Next component の static snapshot/diff。
- named endpoint、immutable dual snapshot、read-only Git、FileChangeSet/SemanticChangeSet separation。
- JSON/PlantUML/manifest、redaction、determinism、partial success、exit/budget/platform contract。
- Python+SQLAlchemy intermediate release、Next/all-domain Initiative completion。
- product HTML report は scope 外。

## 候補分割の比較

| 案 | 境界 | 評価 |
| --- | --- | --- |
| A: 3 domain mega-Issues + integration | Python、SQLAlchemy、Next ごとに snapshot/diff を一つへまとめる | 各 domain は大きく、snapshot と diff の acceptance/rollback が独立するため review と recovery が粗い。 |
| B: 6 domain/use-case Issues | 各 domain の snapshot と diff を分離 | 良い vertical boundary だが、domain 無指定 partial success/aggregate manifest が sibling 内部へ埋もれる。 |
| C: 7 Issues（採用） | B に all-domain observable run を追加 | 最小限の独立 acceptance を保ち、final Initiative outcome を単独検証できる。 |
| D: 10+ technical layer Issues | contract/freezer/parser/renderer/manifest を分離 | horizontal fragment で単独利用価値がなく、accepted ADR に反する。 |

### 却下した horizontal boundaries

- source freezer-only: observable semantic Artifact がなく単独 acceptance value がない。
- parser-only: user/coding agent が結果を利用できず renderer/manifest sibling に依存する。
- renderer-only: semantic truth/source failure を所有せず、誤った成功を単独で判定できない。
- contract-only: schema document は各 vertical slice の acceptance fixture として導入し、独立 Issue にしない。
- cleanup/documentation-only: behavior-preserving work は owning vertical Issue の completion gate に含める。

## 採用分割

| Key | Title | Observable outcome | Dependencies |
| --- | --- | --- | --- |
| ISSUE-01 | Generate Python Structure Snapshots | coding agent または人間が、対象 Python repository を実行せずに class 構造を semantic JSON と PlantUML で取得できる。 | なし |
| ISSUE-02 | Compare Python Structure Changes Safely | coding agent が named endpoint で before/after Python semantic snapshot を安全に固定し、意味のある class/member/relation change と影響 context だけを比較できる。 | ISSUE-01 |
| ISSUE-03 | Generate SQLAlchemy ER Snapshots | coding agent が DB や application を起動せず、SQLAlchemy declarative ORM source から table と row-level ER semantics を JSON と PlantUML で取得できる。 | ISSUE-01 |
| ISSUE-04 | Compare SQLAlchemy ER Changes | coding agent が before/after declarative ORM semantics を比較し、table と column/constraint/index/relationship の row-level delta、ghost removal、影響 context を説明できる。 | ISSUE-02, ISSUE-03 |
| ISSUE-05 | Generate Next.js Component Snapshots | coding agent が first-party TypeScript adapter を通じ、Next.js repository の module、exported component、props、static relation、client boundary を JSON と PlantUML で取得できる。 | ISSUE-01 |
| ISSUE-06 | Compare Next.js Component Changes | coding agent が before/after Next.js semantic snapshot から component/props/import/render/boundary change と影響 context を比較できる。 | ISSUE-02, ISSUE-05 |
| ISSUE-07 | Run Unified Multi-Domain Structure Comparison | coding agent が domain を省略した一回の command で Python、SQLAlchemy、Next の適用可否・成功・不完全を区別し、成功 Artifact を保持した集約 manifest と正しい exit code を得られる。 | ISSUE-04, ISSUE-06 |

## Verticality check

| Issue | CLI input | source acquisition | domain analysis | outputs | acceptance evidence | stop condition |
| --- | --- | --- | --- | --- | --- | --- |
| ISSUE-01 | yes | yes | python | semantic JSON + PlantUML | I01-AT-001 | Python snapshot の CLI→source selection→AST analysis→semantic JSON/PlantUML→manifest→acceptance test が単独で成立する前に、Git diff、SQLAlchemy row model、Next bridge の実装へ進まない。 |
| ISSUE-02 | yes | yes | python | semantic JSON + PlantUML | I02-AT-001 | before/after snapshot の独立再生成、endpoint/fingerprint provenance、semantic seed、impact union、failure matrix が acceptance test で固定されるまで SQLAlchemy/Next diff の共通化へ進まない。 |
| ISSUE-03 | yes | yes | sqlalchemy | semantic JSON + PlantUML | I03-AT-001 | table/row identity、redaction、not_applicable/incomplete、DB 非接続の acceptance が成立するまで temporal ER matching と ghost row へ進まない。 |
| ISSUE-04 | yes | yes | sqlalchemy | semantic JSON + PlantUML | I04-AT-001 | 全 row kind の before/after delta、ghost rendering、ambiguous matching、片側解析 failure が acceptance で固定されるまで intermediate release を宣言しない。 |
| ISSUE-05 | yes | yes | next | semantic JSON + PlantUML | I05-AT-001 | first-party adapter protocol、TS/TSX coverage、JS/JSX safe subset、client boundary、Node optionality が acceptance で成立するまで Next diff へ進まない。 |
| ISSUE-06 | yes | yes | next | semantic JSON + PlantUML | I06-AT-001 | Next member/relation seed、union impact、adapter partial failure、unknown dynamic behavior が acceptance で固定されるまで全 domain 集約へ進まない。 |
| ISSUE-07 | yes | yes | all | semantic JSON + PlantUML | I07-AT-001 | 三 domain の applicability、partial success retention、aggregate manifest、exit code、atomicity、minimum/latest CI が acceptance で成立するまで Initiative を完了扱いにしない。 |

すべての Issue は CLI→source→domain semantics→JSON/PlantUML→diagnostic/manifest→acceptance test を持つ。ISSUE-07 も単なる integration phase ではなく、domain 無指定一回実行、partial Artifact retention、aggregate manifest、exit contract という利用者可視 outcome を所有する。

## Dependency DAG

```plantuml
@startuml
title vertical Issue の依存 DAG
left to right direction
rectangle "ISSUE-01
Python snapshot" as I01
rectangle "ISSUE-02
Python diff" as I02
rectangle "ISSUE-03
SQLAlchemy snapshot" as I03
rectangle "ISSUE-04
SQLAlchemy diff" as I04
rectangle "ISSUE-05
Next snapshot" as I05
rectangle "ISSUE-06
Next diff" as I06
rectangle "ISSUE-07
all-domain run" as I07
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

Topological order は `ISSUE-01, ISSUE-02, ISSUE-03, ISSUE-04, ISSUE-05, ISSUE-06, ISSUE-07`。ただし ISSUE-03/ISSUE-05 は ISSUE-01 後、ISSUE-04/ISSUE-06 は各 dependency 後に並行可能。cycle はない。

## Intermediate release

- ISSUE-04 完了: Python snapshot/diff + SQLAlchemy snapshot/diff が利用可能。intermediate release。
- ISSUE-06 完了: Next standalone snapshot/diff preview。
- ISSUE-07 完了: domain 無指定 orchestration、partial success、aggregate manifest、platform/package gate。Initiative completion。

## Parent acceptance coverage

| Initiative acceptance | Owning Issue(s) | Ownership |
| --- | --- | --- |
| INIT-AC-001 | ISSUE-01, ISSUE-02 | owned |
| INIT-AC-002 | ISSUE-03, ISSUE-04 | owned |
| INIT-AC-003 | ISSUE-04 | owned release gate |
| INIT-AC-004 | ISSUE-05, ISSUE-06 | owned |
| INIT-AC-005 | ISSUE-07 | owned |
| INIT-AC-006 | ISSUE-01〜07 | shared invariant, slice-specific tests |
| INIT-AC-007 | ISSUE-07; earlier Issues contribute locks/tests | final owned + shared evidence |
| INIT-AC-008 | ISSUE-01〜07 and parent scope | shared exclusion |

## Trade-off

- 7 Issues は 4 mega-Issues より node overhead が大きいが、snapshot/diff の separate use case、rollback、acceptance、releaseability を明確にする。
- Python diff spine を SQLAlchemy/Next diff が再利用するため、後続 Issue は Git horizontal Issue を必要としない。
- all-domain Issue を追加することで final behavior を独立受け入れできるが、domain semantics を orchestration へ移さない governance が必要。

## 仮定と未解決 evidence

- accepted decisions と user scope で material Issue count/boundary は確定可能。
- existing `iss-00003` managed metadata を安全に rename する SpecDock command は確認できていないため、node は supersede、concern は ISSUE-02 へ採用する。
- legacy source の license file は提供 evidence にない。直接 code copy を計画しないため Issue implementation blocker にはしない。
