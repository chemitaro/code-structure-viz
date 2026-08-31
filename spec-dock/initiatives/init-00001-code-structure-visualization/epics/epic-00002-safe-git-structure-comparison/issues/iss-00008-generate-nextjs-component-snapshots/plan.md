---
種別: 実装計画書（Issue）
ID: "iss-00008"
タイトル: "Generate Next.js Component Snapshots"
関連GitHub: ["#8"]
package_sequence_key: "ISSUE-05"
状態: "draft"
最終更新: "2026-08-31"
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

- declared dependency: ISSUE-01。
- execution order: I05-PLAN-000 → 001 → 008 → 002 → 003 → 005 → 004 → 007 → 006。canonical adoptionとmachine-checkable contractをmaterializeし、そのexact commitのStrict pass後にproduction実装へ進む。
- TypeScript fixtures、protocol golden、renderer golden、security trapsはcontract固定後に並行できる。
- stop condition: adapter protocol、static semantics、not_applicable/incomplete、entity budget、optional Node、determinismが成立するまでNext diffへ進まない。

| Plan ID | implementation/verification step | Design trace |
| --- | --- | --- |
| I05-PLAN-000 | implementation判断を残さないfield-level identity/source/protocol/type/taint/public schema/config/package contractをcanonical Designへ固定する。 | I05-DES-001〜007 |
| I05-PLAN-001 | identity/export、project/target、protocol、type IR、relations/boundary、outcome/publication、TrustedTypeEnvironment、packaging/regressionのI05-AT-001〜011 fixtures/schemaを先に固定する。 | I05-DES-001〜007 |
| I05-PLAN-008 | actual schema/docs/catalog/golden/mutation fixtureを含むclean pushed exact SHAでChatGPT Use Strictを再実行し、P0/P1=0をproduction implementation gateとする。 | I05-DES-001〜007 |
| I05-PLAN-002 | domain-owned SourceAcquisitionPlan、Next config/project/target parser、frozen-bytes request、hardened one-shot Node boundaryを実装する。 | I05-DES-002, I05-DES-006 |
| I05-PLAN-003 | declaration identity、bindings、Component recognition、closed props IR、two-plane relations、positive-evidence boundaryを実装する。 | I05-DES-003 |
| I05-PLAN-004 | untrusted response strict validation/ID再計算、semantic JSON、PlantUML、manifest、closed registry/publicationを接続する。 | I05-DES-004 |
| I05-PLAN-005 | intentional unknown、partial_safe、payload_unavailable、explicit target all-or-nothing、entity/transport/type limitsをoutcomeへ接続する。 | I05-DES-005 |
| I05-PLAN-006 | non-execution/redaction、determinism、Node optionality、offline bundle、lock/license、resource cap、CI、full regressionを完了する。 | I05-DES-006 |
| I05-PLAN-007 | parserに部分実装済みのNext stdout syntaxをdomain/format/schema/stream pathと一貫して有効化し、exact-byte copy、unavailable result、no-selector summary、usage no-publicationを検証する。 | I05-DES-007 |

## 実装step

### I05-PLAN-000 canonical adoption

- `20260831t024052z-research-nextjs-snapshot-zero-base-investigation.md`のsource facts、
  `20260831t022358z-decision-candidate-nextjs-component-snapshot-best-practice.md`のapproved decisions、
  人間向けHTMLのvisual explanationをcanonical R/D/Pへ反映する。
- current production package/core pathsを`未実装`とするstale記述を修正し、existing extension pointとnew planned pathを分離する。
- anti-shadowing、finite recognition/export、per-project config/module resolution、two-phase freeze、protocol/digest、PropsTypeIR/JS extraction、flow/boundary、partial-safe taint proof、public schema/config/package contractをfield-levelでcanonical Designへ固定する。これをproduction implementation後の判断へ先送りしない。

### I05-PLAN-001 acceptance-first contract

- App/Pages Router、named/default/anonymous default、barrel/re-export/alias、reachable/unreachable local Componentをfixture化する。
- inline/interface/alias/import/destructured/FC/class/forwardRef/generic/union/intersection propsとcomplexity opaqueをfixture化する。
- static/literal dynamic/render conditional/collection/createElement、ambiguous/nonliteral unknownをfixture化する。
- client entry/dependency/server candidate/dual role/boundary effectをfixture化する。
- targetless/path/component target/depth/missing/ambiguous/out-of-scopeをfixture化する。
- not_applicable、complete empty、complete+diagnostic、partial_safe、payload_unavailable、usage/fatal/interrupt、entity/transport limits、stdout selectorをtable-drivenに固定する。
- TrustedTypeEnvironment、private request/response、PropsTypeIR、PlantUML、diagnostic、wheel/sdist/offline、domain config/source projectionのpositive/negative fixturesを固定する。
- Designで固定したv1 normative source/process/type/flow limitをboundary fixtureで検証し、変更が必要ならproduction実装前にcanonical DesignとStrict gateを更新する。

### I05-PLAN-008 machine-checkable contract Strict gate

- private request/response/model、TrustedTypeEnvironment、Next semantic/domain manifest/config/runtime member/licenseのJSON Schema、diagnostic catalog、semantic/PlantUML contract docs、positive/negative mutation vectorsを実ファイルとして固定する。
- SpecDock/schema/HTML/format validation、clean commit/push、exact upstream SHA binding後にChatGPT Use StrictでP0/P1とcontract gapをレビューする。
- findingをcanonical authority/current sourceへ照合して修復し、fresh exact SHAでP0/P1=0まで再レビューする。passはIssue実装完了ではない。

### I05-PLAN-002 bridge and adapter boundary

existing extension points:

- `src/code_structure_viz/source/source_view.py`
- `src/code_structure_viz/source/targets.py`
- `src/code_structure_viz/core/config.py`
- `src/code_structure_viz/core/domains.py`
- `src/code_structure_viz/application/snapshot_domain.py`
- `src/code_structure_viz/application/snapshot.py`

new planned modules（実装開始時にcurrent build/package layoutを再確認する）:

- `src/code_structure_viz/adapters/next/bridge.py::NextAdapterBridge`
- `src/code_structure_viz/adapters/next/protocol.py`
- `adapters/next/package.json`、`package-lock.json`、`tsconfig.json`
- `adapters/next/src/analyze.ts::analyzeRepository`
- `src/code_structure_viz/_next_runtime/`（compiled adapter、TypeScript libs、TrustedTypeEnvironment wheel resources）

explicit project rootのdirect Next dependencyをPythonで判定し、不在を証明した場合はNode processを起動しない。domain-owned planでprogram/control/context bytesを一度だけ凍結し、Nodeへtarget path/cwdを渡さない。stdin/stdout exact one JSON、fixed argv/private cwd/minimal env、process/time/byte/memory capを実装する。

### I05-PLAN-003 Next semantic model

- physical-path Module、declaration-key Component、Export/Import binding、Prop identityをcanonicalizeし、barrel/aliasでComponentを複製しない。
- positive evidenceによるComponent recognition、closed wrapper allowlist、effective signatureからのclosed props IRを実装する。
- module/component two-plane graphとbounded JSX output-flowを実装し、event handler/render prop/arbitrary helper/nonliteral dynamicからedgeを捏造しない。
- direct client/router factsとclient dependency/server candidate derived rolesを実装し、no directiveをserverと断定しない。

### I05-PLAN-005 failure and entity gate

- intentional unsupportedをunknownとして完全表現できる場合はcomplete+diagnostic。promised semanticsの局所欠落はsafe subset/exact coverage/same-renderer-subset/redaction/target/budgetをすべて証明した場合だけpartial_safe。
- explicit target、malformed applicability/config、global Program、Node/protocol/schema/security/identity/limit failureはpayload unavailableとし、not_applicable/fallbackへ変換しない。
- default 500はselected internal Module+Componentだけを数え、501以上はexit 3/affected payloadなし/safe manifest countあり。valid overrideはnormal、invalid valueはexit 2。

### I05-PLAN-004 Artifact publication

- adapter responseをuntrusted inputとしてclosed schema/path/ref/redaction/order/ID/count/digest/target completenessをPythonで検証・再計算する。
- `next.snapshot.semantic.json`と`next.snapshot.puml`を同一validated modelからrenderし、Next coverage/provenance、manifest descriptor、stdout paths、writer final path/PlantUML validationをclosed registryへ追加する。
- literal/source/comment/secret/absolute path/raw compiler text/protocol noiseをpublish前にrejectする。

### I05-PLAN-007 stdout selector and stream contract

- current CLI parserがsyntax上受理済みの`next:semantic-json|next:plantuml`を重複実装せず、NextのDomainName、selected domain/requested format compatibility、schema、stream pathと一貫して有効化する。`--stdout`は高々1回、invalid/duplicate/unselected/unrequestedはsource acquisition前にexit 2、stdout空、Artifactなしとする。
- publication後はavailable selectorの公開fileをexact bytesで複製する。unavailable selectorは`stdout-result/v1` 1行、selectorなしは`run-summary/v1` 1行をcanonical key orderで出す。diagnosticはstderrだけへ出し、`--output-dir` publicationを維持する。
- complete、not_applicable、partial_safe、payload_unavailable、run fatal、handled interrupt、manifest unavailableをtable-driven fixtureで固定し、source/secret/absolute pathがstdoutへ漏れないことをnegative scanする。

### I05-PLAN-006 hardening and handoff

- target cwd/node_modules/network/npm/npx/build/config/plugin/application execution traps、same-input adapter/output equality、core-only install without Node、Next-enabled offline bundle/lock/license、Node 22/latest CIを通す。
- current security testのsubprocess allowlistをexact Git runner + exact Next runnerへ狭く更新し、任意subprocessを許可しない。
- Python/SQLAlchemyのsemantic/PlantUML/manifest/stdout golden bytesを維持してIssue #9へhandoffする。

## 検証

| Test ID | acceptance behavior | planned file | command |
| --- | --- | --- | --- |
| I05-AT-001 | Next snapshot | tests/acceptance/next/test_snapshot_cli.py | uv run pytest tests/acceptance/next/test_snapshot_cli.py -q |
| I05-AT-002 | adapter protocol | tests/contracts/next/test_adapter_protocol.py | uv run pytest tests/contracts/next/test_adapter_protocol.py -q |
| I05-AT-003 | safe subset | adapters/next/test/safe-subset.test.ts | npm --prefix adapters/next test -- safe-subset |
| I05-AT-004 | partial_safe/payload_unavailable adapter matrix | tests/acceptance/next/test_adapter_failures.py | uv run pytest tests/acceptance/next/test_adapter_failures.py -q |
| I05-AT-005 | static/redaction | tests/security/test_next_static_boundary.py | uv run pytest tests/security/test_next_static_boundary.py -q |
| I05-AT-006 | Node optionality | tests/acceptance/next/test_optionality.py | uv run pytest tests/acceptance/next/test_optionality.py -q |
| I05-AT-007 | entity budget publication and diff-only option rejection | tests/acceptance/next/test_snapshot_budget.py | uv run pytest tests/acceptance/next/test_snapshot_budget.py -q |
| I05-AT-008 | stdout selector matrix | tests/acceptance/next/test_stdout_selector.py | uv run pytest tests/acceptance/next/test_stdout_selector.py -q |
| I05-AT-009 | TrustedTypeEnvironment / no target types | tests/acceptance/next/test_trusted_type_environment.py | uv run pytest tests/acceptance/next/test_trusted_type_environment.py -q |
| I05-AT-010 | closed contracts / wheel/sdist / offline/license | tests/packaging/test_distribution.py + test_next_distribution.py | uv run pytest tests/contracts/next tests/packaging/test_distribution.py tests/packaging/test_next_distribution.py -q |
| I05-AT-011 | Python/SQLAlchemy byte compatibility | tests/regression/test_next_domain_compatibility.py | uv run pytest tests/regression/test_next_domain_compatibility.py -q |

### issue gate commands

```bash
uv run pytest tests/acceptance/next/test_snapshot_cli.py -q
uv run pytest tests/contracts/next/test_adapter_protocol.py -q
npm --prefix adapters/next test -- safe-subset
uv run pytest tests/acceptance/next/test_adapter_failures.py -q
uv run pytest tests/security/test_next_static_boundary.py -q
uv run pytest tests/acceptance/next/test_optionality.py -q
uv run pytest tests/acceptance/next/test_snapshot_budget.py -q
uv run pytest tests/acceptance/next/test_stdout_selector.py -q
uv run pytest tests/acceptance/next/test_trusted_type_environment.py -q
uv run pytest tests/contracts/next tests/packaging/test_distribution.py tests/packaging/test_next_distribution.py -q
uv run pytest tests/regression/test_next_domain_compatibility.py -q
uv build --offline
./spec-dock/scripts/spec-dock validate
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pytest
```

### Requirement → Design → Plan → acceptance → test trace

| Requirement | Design | Plan | acceptance | test |
| --- | --- | --- | --- | --- |
| I05-REQ-001 | I05-DES-001 | I05-PLAN-001 | I05-AC-001 | I05-AT-001 |
| I05-REQ-002 | I05-DES-002 | I05-PLAN-002 | I05-AC-002, I05-AC-004, I05-AC-006, I05-AC-009 | I05-AT-002, I05-AT-004, I05-AT-006, I05-AT-009 |
| I05-REQ-003 | I05-DES-003 | I05-PLAN-003 | I05-AC-001, I05-AC-003 | I05-AT-001, I05-AT-003 |
| I05-REQ-004 | I05-DES-004 | I05-PLAN-004 | I05-AC-001, I05-AC-002, I05-AC-010 | I05-AT-001, I05-AT-002, I05-AT-010 |
| I05-REQ-005 | I05-DES-005 | I05-PLAN-005 | I05-AC-003, I05-AC-004, I05-AC-007 | I05-AT-003, I05-AT-004, I05-AT-007 |
| I05-REQ-006 | I05-DES-006 | I05-PLAN-006 | I05-AC-005, I05-AC-006, I05-AC-009, I05-AC-010, I05-AC-011 | I05-AT-005, I05-AT-006, I05-AT-009, I05-AT-010, I05-AT-011 |
| I05-REQ-007 | I05-DES-007 | I05-PLAN-007 | I05-AC-008 | I05-AT-008 |

### regression boundary

- dependency Issueのacceptance suiteを再実行し、public endpoint/source/schema/manifest/exit contractを破っていないことを確認する。
- target repositoryのHEAD、branch、refs、index、status、tracked/untracked bytesがcommand前後で一致する。
- same-input deterministic rerun、output collision、invalid override、interrupt cleanupを確認する。
- Artifact、diagnostic、stdout/stderr/logをsource body、raw hunk、comment、literal、secret、absolute pathでnegative scanする。
- visual vocabularyはcolorだけでなく記号、line style、legendをgolden/semantic testで検査する。

## rollback

- data migration は N/A。Node adapter release は Python package と互換 matrix を固定する。protocol mismatch は adapter を incomplete として隔離し、旧 protocol reader を保持した additive fix または version up で forward recovery する。
- rollback trigger: acceptance regression、source execution/mutation、secret/absolute path leak、incorrect successful exit、ambiguous moved の誤採用。
- rollback unit: Issue の production code、tests、schema/doc additionsを一体で revert する。dependency Issue の accepted contract は戻さない。
- forward recovery: unsafe pattern を `incomplete`/`unknown` へ狭め、誤った success を継続しない。既存 Artifact を自動 rewrite しない。
- output migration は N/A。Artifact は immutable run output であり、既存 output を上書きしない。

## exit / handoff

- I05-AC-001〜I05-AC-011のacceptance evidenceが揃う。
- Requirement→Design→Plan→test trace に gap がない。
- planned path honesty を review し、実装時点の実在 path/symbol と差異があれば Design/Plan を先に更新する。
- residual risk、unsupported static pattern、coverage limitation、explicit override を release note と manifest diagnostic contract に残す。
- downstream handoff: Next snapshot preview。Python/SQLAlchemy の install/runtime requirement へ Node を持ち込まない optional adapter separation を完成させる。
- completion 後も implementation/report の実績は canonical Report に別途記録し、本 Plan を実行ログにしない。
