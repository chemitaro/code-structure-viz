---
種別: research
ID: "20260831t024052z-research"
タイトル: "Issue #8 Next.js Snapshot Zero-Base Investigation Record"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-08-31"
親: ["iss-00008"]
template: "research"
authority: "evidence"
derived_from: []
reflected_to: []
---

# 20260831t024052z-research Issue #8 Next.js Snapshot Zero-Base Investigation Record

Issue #8 の仕様を一度白紙に戻し、current repository の code、tests、canonical docs、親 product boundary を
同じ source set として読み直した調査記録である。推奨設計の本文は companion decision-candidate、
人間向けの図解は companion HTML に分離し、本 Artifact は「何を読み、何が事実で、どの推論を行い、
何をまだ実装で証明する必要があるか」を残す。

この Artifact は `authority: evidence` であり、canonical Requirement / Design / Plan の代替ではない。
調査時点の commit は再現用 evidence であり、仕様の恒久 authority ではない。

## Question

- Next.js component snapshot を既存 CodeStructureViz core に追加するとき、次を同時に満たす最小で安全な
  vertical slice は何か。
  - target repository の code を実行しない。
  - Git から凍結した同一 source bytes を解析する。
  - Next/React の static semantics を過剰推測しない。
  - Issue #9 の temporal diff で identity が不必要に揺れない。
  - Python / SQLAlchemy の既存 contract と bytes を壊さない。
  - Node / TypeScript の optional runtime、protocol、failure、publication を fail-closed にする。
- 現行 canonical docs のどの前提が current implementation と不整合または不十分か。
- 後続 implementer と ChatGPT Strict reviewer が、追加調査なしに仕様意図、棄却案、acceptance 観点を
  復元できるか。

## Source

### Investigation point

- repository: `chemitaro/code-structure-viz`
- worktree branch: `iss-00008-generate-nextjs-component-snapshots`
- pre-adoption HEAD: `f9e9c4ae845aab8c846807a7f7395acd407bb5f5`
- inspected on: `2026-08-31`
- method: local read-only inspection of tracked code/spec/tests plus the newly created draft Artifacts。
- public Web research: 未実施。Next/TypeScript の version-sensitive vendor factsを本調査だけで確定していない。

### Canonical scope sources

- `.meta.json`: Issue #8、GitHub #8、dependency `iss-00004`、managed metadata を確認。
- `requirement.md`: current observable contract、failure/publication、stdout、budget、acceptance を確認。
- `design.md`: planned adapter boundary、current/target、planned paths、testability を確認。
- `plan.md`: strict planning level、step ordering、test trace、rollback/handoff を確認。
- `report.md`: implementation evidence はまだ存在しないことを確認。
- `artifacts/rules.md`: research / decision-candidate は evidence/draft であり、採用は canonical reflection が必要。

### Current implementation sources

| path | 調べた責務 | 調査への含意 |
| --- | --- | --- |
| `src/code_structure_viz/source/source_view.py` | immutable source bytes、inventory、fingerprint、drift、安全な read | acquisition は `.py` と `PythonConfig` に具体依存しており、Next のために domain-owned plan が必要。 |
| `src/code_structure_viz/source/targets.py` | `path/module/class` の closed Python target | generic parser を緩めず、domain-aware target grammar を追加すべき。 |
| `src/code_structure_viz/core/config.py` | closed TOML、`PythonConfig`、traversal、limits、digest/value sources | `[next]` branch を closed schema と provenance に明示追加する必要。 |
| `src/code_structure_viz/core/domains.py` | `DomainName`、snapshot/diff domain tuple | current domain は `python/sqlalchemy` のみ。Next は snapshot registry だけへ先に追加する。 |
| `src/code_structure_viz/application/snapshot_domain.py` | adapter contract と domain dispatch | current registry は Python/SQLAlchemy 固定。Next contract/version/path を closed branch として追加する。 |
| `src/code_structure_viz/application/snapshot.py` | acquisition、analysis、budget、render、publication orchestration | Node boundary を追加しても core-owned outcome/publication を維持する必要。 |
| `src/code_structure_viz/core/outcomes.py` | domain/run status、payload availability、artifact path invariant | Next path を追加し、既存 `partial_safe/payload_unavailable` algebra を再利用できる。 |
| `src/code_structure_viz/artifacts/manifest.py` | run fingerprint、coverage encoder、artifact descriptor | Next-specific coverage/provenance encoder と source plan digest が必要。 |
| `src/code_structure_viz/artifacts/streams.py` | closed stdout path registry と exact-byte routing | Next snapshot paths を明示追加する必要。 |
| `src/code_structure_viz/artifacts/writer.py` | final path allowlist、redaction、PlantUML validation、atomic no-replace | Next final paths と Next PlantUML vocabulary を閉じて追加する必要。 |

### Current verification sources

- `tests/contracts/test_json_schemas.py`: schemas は `additionalProperties: false` と outcome/artifact consistency を検証。
- `tests/unit/source/test_source_view.py`: source acquisition の immutable / safety behavior。
- `tests/unit/source/test_targets.py`: Python target の closed grammar。
- `tests/unit/core/test_config.py`: config key/type/value/value-source の fail-closed behavior。
- `tests/unit/artifacts/test_manifest.py`、`test_streams.py`、`test_writer.py`: manifest、stdout、publication contract。
- `tests/security/test_python_static_boundary.py`: production subprocess call が Git runner だけという current invariant。
- `tests/security/test_sqlalchemy_static_boundary.py`: static non-execution と subprocess boundary。
- Python / SQLAlchemy snapshot golden: Next 追加による既存 bytes drift を検出する regression authority。

### Prior product boundary evidence

current source と再照合した historical design boundary:

- CodeStructureViz の価値は code structure / dependency snapshot と Git 上の temporal change の可視化。
- common kernel は Git endpoint、immutable SourceView、read-only safety、diagnostic、Artifact publication を所有。
- domain adapter は identity、member、relation、matching、traversal、rendering semantics を所有。
- snapshot と diff は別 use case。
- Next relation は runtime component tree ではなく static JSX render relation。

historical repository SHA や旧未コミット状態は current fact として採用せず、上の低変動 product boundary だけを
current source/canonical docs と照合して利用した。

## Findings

### 1. Current implementation facts

1. production package、CLI、schema、SourceView、Python snapshot/diff、SQLAlchemy snapshot/diff、manifest、
   stdout、writer は既に存在する。現行 `design.md` の「production package、CLI は未実装」という記述は stale。
2. Next domain production adapter は未実装。
3. `DomainName` と adapter/output registries は closed で、Next を additive に明示する必要がある。
4. source acquisition は `.py` と `PythonConfig` に直接結合しており、Next file set を ad hoc conditional で
   追加すると domain leakage が起きる。
5. target parser は Python semantics に閉じている。既存 grammar を変更すると Python contract を壊す。
6. config、schemas、outcomes、artifact paths、stdout path、writer path は fail-closed allowlist である。
   Next 対応のためにこれらを open map や `additionalProperties: true` にしてはならない。
7. subprocess は現在 Git read-only runner に限定される。Node runner は exact second trusted runner として
   security test に狭く追加すべきで、任意 subprocess を許可してはならない。
8. existing core outcome は `not_applicable`、`complete`、`incomplete/partial_safe`、
   `incomplete/payload_unavailable`、usage、fatal、interrupt を表現できる。
9. existing writer は final path allowlist と domain-specific PlantUML validation を持つ。Next renderer も同じ
   publication trust boundary に接続すべき。
10. existing golden と schema tests は backward compatibility を byte / structure で検出できる。

### 2. Source acquisition findings

#### Fact

- 同一 run の analysis と publication を一つの immutable `SourceView` fingerprint に固定する既存基盤がある。
- `.py` candidate 判定が source layer 内で Python config を直接参照している。

#### Inference

- Next adapter が target repository を直接読むと、Python が固定した bytes と Node が読む bytes が異なる
  source drift を起こし得る。
- target cwd、symlink、package resolution、`node_modules`、tsconfig package extends が Python core の
  trust boundary 外へ出る。

#### Adopted implication

- domain が immutable `SourceAcquisitionPlan/Profile` を返し、Python core がその plan に従って bytes を凍結する。
- Node request は repository-relative path、base64 content、digest、resolved project/config/target/limit だけを持つ。
- Node に repository root path や target cwd を渡さない。
- Next program files は `.ts/.tsx/.js/.jsx`、`.d.ts` は context-only。
- hard exclude は `.git/node_modules/.next/out/dist/build/coverage`。
- test/spec/story は default exclude にせず、tsconfig/jsconfig または explicit config に委ねる。

### 3. Project applicability findings

#### Alternatives examined

- repository 全走査による workspace/package 自動発見。
- `next.config.*`、`app/`、`pages/`、source import による heuristic。
- explicit project root と direct package dependency evidence。

#### Risk comparison

- 自動発見は unrelated package、workspace semantics、generated directory を拾い、同じ repository でも
  package-manager state により結果が揺れる。
- `next.config.*` を evidence にすると config execution の誘惑が生じ、directory 名だけでは偽陽性が多い。

#### Adopted implication

- `--repo` は exact Git root のまま。
- repeatable `--project REPOSITORY_RELATIVE_DIRECTORY` を追加し、CLI は `[next].project_roots` を置換。
- default project root は `.`。
- project root 直下 `package.json` が direct `dependencies.next` または `devDependencies.next` に
  non-empty string を持つ場合だけ applicable。
- shared package は `[next].source_roots` で opt-in。
- applicable 0 + explicit target なしは Node probe なし `not_applicable`。
- applicable project で Component 0 は `complete empty`。
- malformed manifest/config は absence を証明できないため `payload_unavailable`。

### 4. Identity findings

#### Problem found in current canonical candidate

current Requirement/Design は Component identity を `module path + exported component name` とする。
この identity は次の semantic-preserving change で揺れる。

- direct export から barrel re-export へ移す。
- exported alias を変更する。
- 同じ declaration を複数 module/name から re-export する。
- default export を named binding で公開し直す。

このまま Issue #9 に渡すと、一つの Component declaration が false remove/add または duplicate entity になる。

#### Adopted model

- `ModuleEntity`: repository-relative physical module path。
- `ComponentEntity`: Module ID + declaration key。named binding または module-local `@anonymous-default` slot。
- `ExportBindingMember`: owner Module + exported name。target Component ID を payload に持つ。
- `ImportBindingMember`: owner Module と imported origin/name/role。local alias/order/range は identity 外。
- `PropMember`: Component ID + prop name。
- route、router kind、source range、export alias、wrapper、props type は Component identity 外。
- barrel/re-export は binding を増やすが Component を複製しない。
- exported/route root から proven render/wrapper で到達する module-local component だけを
  `reachable_local` として含める。

### 5. Component recognition findings

#### Rejected

- PascalCase 名だけによる認定。
- JSX syntax が一度現れた function をすべて Component とする。
- custom HOC の一般推論。

#### Adopted positive evidence

- safe React-compatible callable/construct signature。
- closed React class provenance。
- recognized App/Pages UI entry default export。
- bounded return output-flow で JSX/React element を証明。
- closed wrapper allowlist: `memo`、`forwardRef`、`lazy`、literal-pattern `next/dynamic`。

証明不能は unknown/coverage limitation とし、entity を捏造しない。

### 6. Props findings

#### Fact and risk

- TypeChecker は alias/import/generic/union/intersection/overload を解決できるが、`typeToString()` は
  compiler version、source spelling、literal、alias name を public output に漏らし得る。

#### Adopted implication

- effective call/construct signature から props を得る。
- closed normalized type IR を Python public schema にする。
- literal value、function parameter name、generic parameter name を redaction/ordinal 化。
- Unicode NFC、canonical sort/dedup、alpha normalization。
- `children` / `ref` は public signature に実在するときだけ。
- complexity limit 到達は silent truncation せず subtree `opaque` + partial coverage。
- candidate limits: depth 16、nodes/prop 512、union/intersection 64、nested props 256、
  signatures/component 16。

### 7. Relation findings

#### Problem

module import と Component render を同じ graph plane で fan-out すると、import した module 内の全 Component を
render したような false relation が生まれる。lexical JSX scan は event handler や render prop の未実行 body も拾う。

#### Adopted model

- module plane: `static_import`、`literal_dynamic_import`。
- component plane: `jsx_render`、`component_wrap`。
- containment は ownership / zero-hop。
- relation ID は source/kind/target/semantic role。range/order/local alias/syntax は payload。
- Component return、concise arrow、class render、single-assignment const への bounded backward flow を追う。
- conditional/logical/array/JSX children、安全な Array/ReadonlyArray map/flatMap、exact React
  `createElement` を閉じた形で扱う。
- event handler、render prop/function child、arbitrary helper、ambiguous symbol、nonliteral import は relation にしない。
- external target は frontier descriptor で止め、internal entity を捏造しない。
- downstream は source→dependency/render target、upstream は逆方向。

### 8. Client boundary findings

#### Rejected

- `"use client"` がない module を server と断定。
- client/server を排他的な一つの enum にする。
- runtime bundle/hydration tree を推定。
- boundary crossing を underlying import と別の traversal edge にする。

#### Adopted primitive/derived model

- direct fact `client_entry`: exact directive prologue。
- direct fact `router_context`: app UI、pages UI、pages API、app route handler、none。
- derived `client_dependency`: client_entry から internal static value import/re-export で到達。
- derived `server_candidate`: closed App Router UI seed から client entry の直前まで到達。
- `unknown`: positive evidence なし。Pages Router も自動 server 扱いしない。
- 同じ Module に client_dependency/server_candidate の dual role を許す。
- type-only、dynamic、JSX、external/unresolved edge は propagation に使わない。
- boundary は underlying value edge の `boundary_effect` facet。
- Issue #9 は primitive facts/edges を primary diff とし、derived cascade を増幅しない。

### 9. Protocol and process findings

#### Rejected

- Node が target repository を直接読む。
- npm/npx を runtime に呼ぶ。
- persistent daemon/cache。
- adapter stdout の best-effort JSON extraction。

#### Adopted boundary

- one request/one response/one process。
- fixed executable/entrypoint argv、`shell=false`、private empty cwd、minimal env。
- `NODE_OPTIONS`/`NODE_PATH` を除去し、target node_modules/network/package script を使わない。
- compiled first-party adapter + exact TypeScript runtime + lockfile + license inventory を bundle。
- custom in-memory `CompilerHost` は request virtual files と bundled TS lib だけを読む。
- exact one `code-structure-viz.next-adapter/v1` JSON document。stdout noise は全 response reject。
- Python は version/schema/path/ref/redaction/order/ID/count/digest/target completeness を検証・再計算。
- protocol validation failure は partial に downgrade しない。

candidate transport/process limits:

| item | candidate | over-limit result |
| --- | ---: | --- |
| file bytes | 4 MiB | payload unavailable |
| total bytes | 64 MiB | payload unavailable |
| files | 20,000 | payload unavailable |
| stdout | 16 MiB | payload unavailable |
| stderr capture | 64 KiB | safe summary only |
| wall time | 60 s | process-group termination + unavailable |
| Node old-space | 512 MiB | unavailable |

数値は実装 fixture の実測で調整可能だが、unbounded と silent truncation は不可。

### 10. Outcome and publication findings

complete/partial の基準は diagnostic の存在ではなく、promised v1 semantics の欠落である。

| condition | status | publication | exit |
| --- | --- | --- | ---: |
| Next project 不在を証明 | not_applicable | manifest | 0 |
| applicable、entity 0、complete | complete empty | requested empty payloads + manifest | 0 |
| intentional unsupported を unknown で完全表現 | complete + diagnostic | payloads + manifest | 0 |
|局所欠落、安全 subset/coverage/renderers を証明 | incomplete/partial_safe | JSON + PlantUML + manifest | 3 |
| explicit target failure、global config/Program/Node/protocol/schema/security/identity/budget failure | incomplete/payload_unavailable | manifest only | 3 |
| CLI/config grammar/value error | usage | Artifact 0 | 2 |
| Git/SourceView/source drift/writer transaction invariant | fatal | Artifact 0 | 1 |
| handled interrupt | interrupted | cleanup、Artifact 0 | 130 |

- explicit targets は all-or-nothing。fallback 禁止。
- requested formats は atomic all-or-none。
- default 500 budget は selected internal Module + Component だけを count。
- 501 は truncation せず payload unavailable。
- output files: `next.snapshot.semantic.json`、`next.snapshot.puml`。
- adapter protocol は private v1、public semantic は existing v1、PlantUML は `next/v1`、manifest は existing v1。
- closed registries/schema/allowlist を additive に更新し、open-ended fallback は導入しない。

### 11. CLI/target findings

adopted candidate grammar:

```text
snapshot --repo GIT_ROOT --domain next --output-dir PATH
  [--project REPOSITORY_RELATIVE_DIRECTORY]...
  [--target path:REPO_REL_FILE_OR_DIR]...
  [--target component:EXPORTING_MODULE#EXPORTED_NAME]...
  [--upstream-depth N] [--downstream-depth N]
  [--config PATH]
  [--format semantic-json|plantuml]...
  [--max-entities N]
  [--stdout manifest|next:semantic-json|next:plantuml]
```

- existing Python target grammar はそのまま。
- `path:` は exact file または lexical directory subtree。
- `component:` は user-facing export address だが、resolution 後は declaration identity を選ぶ。
- multiple target は normalized/deduplicated union。
- depth は target と同時だけ。
- route selector は v1 non-goal。

### 12. Implementation sequencing findings

推奨順序:

1. decision adoption と canonical R/D/P correction。
2. acceptance/schema/protocol/outcome fixtures first。
3. domain-owned SourceAcquisitionPlan、Next config/project/target parser。
4. Python hardened runner と private protocol。
5. TS adapter: identity → recognition → props → relation → boundary roles。
6. Python strict validator と Next JSON/PlantUML renderer。
7. closed registries、manifest、stdout、outcome、writer、atomic publication。
8. security/limits/offline packaging/lock/license/Node CI。
9. deterministic golden、full regression、Issue #9 handoff。

### 13. Planned path honesty findings

current canonical Design の planned `adapters/next/...` はまだ存在しない。一方、core path は既に実装済みである。
canonical Design/Plan は次を区別する必要がある。

- existing extension points: source/config/targets/domains/snapshot/artifacts/outcomes/schema/tests。
- new planned Python package: `src/code_structure_viz/adapters/next/`。
- new planned first-party Node workspace: exact path は packaging layout を current build config と照合して決める。
- planned test/fixture paths。

存在しない symbol を current と書かず、既存 production package を未実装とも書かない。

### 14. Risks not eliminated by design

- React/Next static patterns は広く、closed v1 subset 外の code は残る。
- TypeScript bundled lib と target compiler expectation の差は compatibility risk。
- package-based tsconfig extends を安全に閉じると、実 repository coverage が下がる可能性。
- 64 MiB/20k files/60s/512 MiB の候補値は実測前。
- App/Pages router path classification の exact closed table は fixture でさらに固定が必要。
- public semantic schema の concrete fields と diagnostic code catalog は implementation-first ではなく
  contract fixture で確定する必要。

これらは推測で埋めず、acceptance fixture、Strict review、実装時の local evidence に戻す。

### 15. Companion artifacts

- `20260831t022358z-decision-candidate-nextjs-component-snapshot-best-practice.md`
  - 全推奨 contract、PlantUML、stop condition、acceptance matrix。
- `20260831t022707z--nextjs-component-snapshot-best-practice-guide.html`
  - 人間向けの5図入り説明資料。PlantUML browser validation済み。
- 本 research Artifact
  - source、事実、推論、棄却案、リスク、canonical reflection trace。

## Reflection

- User decision on `2026-08-31`: companion candidate の四つの中心判断と、調査内容を canonical docs と
  durable Artifact に残す方針を承認。
- Requirement へ反映するもの:
  - explicit project selection/applicability。
  - frozen-bytes-only Node boundary。
  - declaration identity + export binding。
  - two-plane relations と positive-evidence boundary roles。
  - closed outcomes、target all-or-nothing、budget counting。
- Design へ反映するもの:
  - current implementation truth。
  - SourceAcquisitionPlan、request/response trust boundary、domain model、props IR、relation flow、security limits。
  - existing/new path map、closed registry integration。
- Plan へ反映するもの:
  - adoption → acceptance-first → acquisition → runner → analyzer → validator/renderers → integration → hardening。
  - concrete tests、regression boundary、Strict review gate、Issue #9 handoff。
- Report はまだ implementation evidence を持たない。spec authoring、validation、commit/push、Strict review の
  実績だけを必要に応じて Report へ記録し、未実行 test を成功扱いしない。
- companion decision-candidate は adoption source として保持し、canonical reflection 後に
  `reflected_to` を mechanically safe な方法が定義されていない限り手編集で authority を偽装しない。
