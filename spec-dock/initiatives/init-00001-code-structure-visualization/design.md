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
| INIT-DES-002 | INIT-REQ-002, INIT-REQ-003 | read-only source layer、immutable real/empty-side snapshot、metadata-only FileChangeSet、SemanticChangeSet 分離を product spine とする。 |
| INIT-DES-003 | INIT-REQ-001, INIT-REQ-004 | minimal core + domain-owned adapter model + per-domain semantic Artifact + `run-manifest/v1` aggregate を採用し、`domain: all` semantic payload を禁止する。 |
| INIT-DES-004 | INIT-REQ-005 | typed outcome state、run-level changed-path admission、domain-local entity gate、atomic output transaction、partial success retention を横断 contract にする。 |
| INIT-DES-005 | INIT-REQ-006 | Python core と optional first-party Node adapter、lockfile/license/offline CI を分離する。 |
| INIT-DES-006 | INIT-REQ-008 | product HTML を architecture から除外し、specification HTML を evidence として別管理する。 |

## Current / Target

### Current

- exact verified current commit `867ee6929283dfc84711bce245b784d2b8e3e9e6` は one Initiative、exactly one Epic、seven active vertical Issues、interview、8 accepted ADR と canonical R/D/P を含む。
- production package、CLI、adapter、schema implementation はまだ存在しない。実装開始前に domain presence、budget publication、all-domain envelope、working-tree anchor、hunk redaction、trace を authority layer で一意にする。
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
SourceView(endpoint A) -> real DomainSnapshot A --------+
internal empty-side A (domain absent) ------------------+-> DomainSemanticDiff -> impact union graph
SourceView(endpoint B) -> real DomainSnapshot B --------+
internal empty-side B (domain absent) ------------------+

Git status/range/R/C -> metadata-only FileChangeSet -----> candidate/provenance only
```

DomainSnapshot は content-addressed immutable document。DomainSemanticDiff は二つの side descriptor と snapshot digest を参照し、raw source、patch body、mutable repository path を持たない。target evidence が存在する side の acquisition/analysis failure を empty-side に置換しない。

### diff domain presence truth table

この表は `python`、`sqlalchemy`、`next` の各 diff と domain 無指定 run に同じ意味で適用する。`present` は静的な target evidence が存在すること、`absent` はその evidence が存在しないことを表す。source acquisition または static analysis の失敗を `absent` と解釈してはならない。

| before | after | domain status | semantic comparison | publication | single-domain exit / all-domain effect |
| --- | --- | --- | --- | --- | --- |
| absent | absent | `not_applicable` | 比較しない。 | status と safe diagnostic だけを run manifest に記録し、その domain の semantic JSON と PlantUML は公開しない。 | exit 0。all-domain overall を `incomplete` にしない。 |
| present、解析成功 | present、解析成功 | `complete` | 二つの実 snapshot を比較する。 | domain semantic diff JSON、domain-specific PlantUML、run manifest descriptor を公開する。 | exit 0。 |
| present、解析成功 | absent | `complete` | 実 before snapshot と internal canonical empty-side snapshot を比較し、before の全 entity/member/relation を `removed` とする。 | domain semantic diff JSON、domain-specific PlantUML、run manifest descriptor を公開する。empty-side 自体は公開しない。 | exit 0。 |
| absent | present、解析成功 | `complete` | internal canonical empty-side snapshot と実 after snapshot を比較し、after の全 entity/member/relation を `added` とする。 | domain semantic diff JSON、domain-specific PlantUML、run manifest descriptor を公開する。empty-side 自体は公開しない。 | exit 0。 |
| target evidence あり | いずれかの side で source acquisition または static analysis 失敗 | `incomplete` | added/removed を推測しない。 | affected domain の semantic JSON と PlantUMLを公開しない。safe diagnostic、coverage、side provenance を run manifest に記録し、成功 sibling Artifact は保持する。 | single-domain exit 3。all-domain overall `incomplete`、exit 3。 |

internal canonical empty-side snapshot の canonical bytes は、key sort・UTF-8・余分な空白なしで直列化した `code-structure-viz.empty-side/v1` document とする。document は `domain`、`document_kind: "internal-diff-side"`、空の `entities`/`members`/`relations` だけを持ち、endpoint や side 名を含めない。同じ domain と contract version では常に同じ SHA-256 になる。manifest の該当 side descriptor は `kind: "canonical-empty-side"`、schema、domain、SHA-256 を記録する。この internal document を成功した standalone snapshot、empty semantic Artifact、empty diagram として公開してはならない。

### `--to working-tree` implicit anchor

`--to working-tree` を `--from` なしで指定した場合は、run 開始時に working tree を repository 外へ freeze し、同じ開始時点の `HEAD^{commit}` を implicit-base candidate の merge-base 計算に使う endpoint commit anchor とする。candidate priority は explicit PR target、configured comparison target/upstream、`origin/HEAD`、local `main`/`develop`/`master` の順であり、`merge-base(candidate, start_head_anchor)` を最初に安全に解決できた結果を before endpoint とする。initial commit fallback、auto fetch、checkout は行わない。

provenance は requested `from`/`to`、frozen working-tree SHA-256 digest、start HEAD anchor、selected base candidate、resolved merge-base、`resolution_method: "implicit-base-from-start-head-anchor"` を必須とする。run 終了時 fingerprint が変化した場合は success Artifact を公開しない。

### budget outcome contract

| budget | gate / default | override なしの超過 | publication | valid override |
| --- | --- | --- | --- | --- |
| implicit changed paths | domain comparison 前の run-level admission gate。default 1,000。implicit comparison の actual changed-path count に適用する。 | fatal analysis/environment、exit 1。domain analysis を開始しない。safe machine-readable diagnostic を stderr に出す。 | semantic JSON、PlantUML、final run manifest を一切公開せず、staging を破棄する。 | positive integer の `--max-changed-paths N` で通常処理を許可する。公開 manifest に requested value、resolved value、actual changed-path count、config source を記録する。 |
| entities per diagram | domain semantic result 生成後かつ renderer/publication 前の domain-local gate。default 500。 | affected domain を `incomplete` とし、単一 domain run も all-domain run も exit 3。切り捨てない。 | affected domain の semantic JSON と PlantUML は公開しない。successful sibling Artifact と aggregate run manifest は保持し、diagnostic、requested/resolved limit、actual entity count を記録する。 | positive integer の `--max-entities N` で通常公開を許可し、manifest に requested value、resolved value、actual entity count、config source を記録する。 |

override の zero、negative、non-integer、型不正、unknown config key は usage/config error、exit 2 であり、Artifact を公開しない。depth の default は upstream/downstream 各 1 で、depth は graph context を制限するだけで budget 超過の truncation 手段にはしない。

### FileChangeSet hunk safety contract

`FileChangeSet` の hunk evidence は metadata だけである。各 hunk は repository-relative old/new path、file status、old/new start line、old/new line count、同一 file 内の ordinal、および content-independent な `hunk_id` を持てる。`hunk_id` はこれら metadata の canonical tuple から SHA-256 で生成し、source bytes を入力にしない。

raw patch line、context line、added/deleted line、source body、comment、literal、secret、absolute path を memory-owned model、semantic JSON、PlantUML、manifest、diagnostic、logへ保持または公開してはならない。Git diff streamを range extraction に読む実装は、metadata を抽出した時点で本文を破棄し、serializer へ本文型を渡さない。negative acceptance test は secret-like patch、comment、literal、absolute temporary path が全 output channel に存在しないことを確認する。

### all-domain output boundary

all-domain orchestration は `code-structure-viz.semantic/v1` の `domain: all` payload を生成しない。各 adapter が own domain の semantic JSON と domain-specific PlantUML を所有する。aggregate は `code-structure-viz.run-manifest/v1` だけであり、run status、domain status、Artifact descriptor、diagnostic、coverage、provenance、budget values/counts、safe graph summary counts を持つ。run manifest の root または domain summary に domain-owned `entities`、`members`、`relations`、matching record を統合しない。cross-domain identity または relation を推測しない。

### outcome aggregation

| state | 意味 | overall/publication effect |
| --- | --- | --- |
| `complete` | selected target を contract 範囲で完了。片側 domain 不在の全 added/removed を含む。 | domain Artifact を公開。all-domain overall complete 候補。 |
| `not_applicable` | diff の両 endpoint、または snapshot target に domain evidence がない。 | status/diagnostic のみ。semantic JSON/PlantUML なし。overall complete を妨げない。 |
| `incomplete` | target evidence はあるが安全な acquisition/analysis または domain-local entity gate を完了できない。 | affected domain Artifact なし、safe manifest entry あり、successful siblings 保持、exit 3。 |
| run-level fatal | endpoint/fingerprint/output invariant または implicit changed-path admission failure。 | exit 1、semantic/PlantUML/final manifest 非公開。 |
| usage/config | CLI/config/override type error。 | exit 2、Artifact 非公開。 |
| interrupt | user interrupt。 | staging cleanup、exit 130。 |

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

- source execution trap、Git state before/after、secret/absolute path/raw hunk scan、dual real/empty-side snapshot golden、matching ambiguity、two-level budget publication matrix、`--to working-tree` start-HEAD anchor、per-domain-only semantic output、determinism、output atomicity を first-class acceptance とする。
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
