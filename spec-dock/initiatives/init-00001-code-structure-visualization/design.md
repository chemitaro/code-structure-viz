---
種別: 設計書（Initiative）
ID: "init-00001"
タイトル: "Visualize Code Structure Changes"
関連GitHub: ["#1"]
状態: "draft"
最終更新: "2026-08-24"
依存: ["requirement.md"]
---

# init-00001 Visualize Code Structure Changes — 設計

詳細: [Design Guide](../../docs/authoring/design.md)

## 設計目標

- repository state を変更せず、target code を実行せず、before/after semantics を明示 provenance で可視化する。
- agent-first JSON と人間向け PlantUML を同じ domain result から生成し、一方だけを真実源にしない。
- common core の役割を source/provenance、lifecycle、diagnostic、Artifact、graph primitive に限定し、domain semantics を adapter が所有する。
- failure、unknown、not applicable を empty success へ潰さず、atomic publication と exit contract で agent の誤判断を防ぐ。

| Design ID | Requirement trace | Initiative-level decision |
| --- | --- | --- |
| INIT-DES-001 | INIT-REQ-001, INIT-REQ-007 | 一つの Epic 配下で domain snapshot/diff slice と all-domain orchestration を順に統合する。 |
| INIT-DES-002 | INIT-REQ-002, INIT-REQ-003 | read-only source layer、immutable snapshot、FileChangeSet/SemanticChangeSet 分離を product spine とする。 |
| INIT-DES-003 | INIT-REQ-001, INIT-REQ-004 | minimal core + domain-owned adapter model + versioned Artifact envelope を採用する。 |
| INIT-DES-004 | INIT-REQ-005 | typed outcome state、atomic output transaction、partial success retention を横断 contract にする。 |
| INIT-DES-005 | INIT-REQ-006 | Python core と optional first-party Node adapter、lockfile/license/offline CI を分離する。 |
| INIT-DES-006 | INIT-REQ-008 | product HTML を architecture から除外し、specification HTML を evidence として別管理する。 |

## Current / Target

### Current

- baseline commit `7951ddabc2e6a3d66edb77eada7c6c16923264f7` に production implementation はなく、SpecDock canonical nodes は template state。
- accepted ADR は product ownership、endpoint、adapter boundary、Artifact、dual snapshot、安全性、HTML exclusion、vertical slice を固定済み。
- legacy references は read-only/source-static/Git safety/test ideas の evidence だが、license、package、CLI compatibility を継承しない。

### Target architecture

```plantuml
@startuml
title CodeStructureViz の target architecture
top to bottom direction
actor "coding agent / local user" as User
component "CLI / RunCoordinator
Python 3.12+" as CLI
component "read-only Git と SourceView" as Source
component "common lifecycle / manifest / diagnostic" as Core
component "Python adapter" as Python
component "SQLAlchemy adapter" as SQLA
component "Next bridge" as Bridge
component "first-party TypeScript adapter
Node 22+ when applicable" as Next
component "semantic JSON / PlantUML" as Artifact
User -> CLI : snapshot または diff
CLI -> Source : endpoint と source を固定する
CLI -> Core : config・budget・output transaction
Core -> Python : domain request
Core -> SQLA : domain request
Core -> Bridge : applicable な場合だけ request
Bridge -> Next : versioned JSON
Python -> Artifact : domain result
SQLA -> Artifact : domain result
Next -> Bridge : versioned JSON
Bridge -> Artifact : domain result
Artifact --> User : manifest と exit status
@enduml
```

Target は one Epic、seven vertical Issues で段階的に成立する。Python/SQLAlchemy completion 後に intermediate release、Next/all-domain completion 後に Initiative complete。

## 責務・Interface

| Boundary | Owns | Does not own |
| --- | --- | --- |
| CLI / application | command grammar、config precedence、run coordination、exit mapping | domain identity/member/relation の意味 |
| read-only source | endpoint resolution、Git object read、working-tree freeze、fingerprint、FileChangeSet | semantic changed seed |
| common core | diagnostic、status、coverage、Artifact descriptor、graph primitive、budget | domain matching fingerprint |
| Python adapter | module/class identity、field/method/property/decorator、Python relation/move | SQLAlchemy/Next semantics |
| SQLAlchemy adapter | schema.table、column/constraint/index/relationship row、ER move/redaction | DB/Alembic runtime |
| Next adapter | module/exported component/props/static relation/client boundary/move | runtime component tree |
| Artifact transaction | serialization、deterministic ordering、collision、SHA-256、atomic publication | source acquisition or analysis |

### cross-Epic/Issue stable contracts

- `code-structure-viz.source-view/v1`
- `code-structure-viz.semantic/v1`
- `code-structure-viz.next-adapter/v1`
- `code-structure-viz.run-manifest/v1`
- visual vocabulary v1 and exit code contract

## data / failure

### immutable snapshot and diff

```text
SourceView(endpoint A) -> DomainSnapshot A --+
                                            +-> DomainSemanticDiff -> impact union graph
SourceView(endpoint B) -> DomainSnapshot B --+

Git status/hunk/R/C -> FileChangeSet evidence -----> candidate/provenance only
```

DomainSnapshot は content-addressed immutable document。DomainSemanticDiff は二つの snapshot digest を参照し、raw source や mutable repository path を持たない。

### outcome aggregation

| domain state | 意味 | overall effect |
| --- | --- | --- |
| complete | selected target を contract 範囲で完了 | complete 候補 |
| not_applicable | target が存在しない | complete を妨げない |
| incomplete | target はあるが安全な解析が完了しない | overall exit 3、成功 sibling Artifact 保持 |
| core fatal | run-level source/config/output invariant failure | exit 1/2、success Artifact 非公開 |

## 変更対象

planned product roots:

- `pyproject.toml`, `uv.lock`, `src/code_structure_viz/`, `tests/`, `docs/contracts/`
- `adapters/next/package.json`, `package-lock.json`, `tsconfig.json`, `src/`, `test/`
- `.github/workflows/ci.yml` minimum/latest matrix and package/security gates

baseline には上記 production roots が存在しないため、すべて planned として扱う。SpecDock runtime 自体を product implementation の一部へ変更しない。

## 移行・互換性・rollback

- data migration は N/A。新規 product であり target repository を変更しない。
- rollout は Python preview、Python+SQLAlchemy intermediate release、Next opt-in preview、all-domain default の四段階。
- legacy CLI compatibility は提供しない。CodeStructureViz v1 schema/CLI の compatibility だけを release 後に管理する。
- rollback は release/Issue 単位。unsafe false success がある場合は affected adapter を incomplete/not available へ狭める forward recovery を優先する。

## testability

- source execution trap、Git state before/after、secret/absolute path scan、dual-snapshot golden、matching ambiguity、budget、determinism、output atomicity を first-class acceptance とする。
- domain fixture と contract fixture を分離し、common test が domain model の private field に依存しない。
- CI は macOS/Linux、Python minimum/latest、Git minimum/latest capable fixture、Node minimum/latest Next lane を持つ。
- end-to-end command の stdout/stderr、exit、manifest、Artifact bytes を同時に検証する。

## risk

| Risk | Impact | Mitigation / review trigger |
| --- | --- | --- |
| generic semantic model の肥大 | domain precision と保守性低下 | minimal core rule。domain field が core に増えたら ADR review。 |
| false success | agent が誤った変更説明を作る | fail closed、incomplete、coverage、negative tests。 |
| source mutation/execution | target repository damage/security incident | read-only allowlist、trap fixtures、fingerprint。 |
| secret leakage | Artifact の二次利用で情報露出 | early redaction、schema denylist、output scan。 |
| cross-runtime drift | Next adapter incompatibility | versioned protocol、lockfiles、contract fixtures。 |
| Issue horizontalization | 受け入れ不能な中間状態 | 各 Issue の CLI-to-Artifact verticality gate。 |
