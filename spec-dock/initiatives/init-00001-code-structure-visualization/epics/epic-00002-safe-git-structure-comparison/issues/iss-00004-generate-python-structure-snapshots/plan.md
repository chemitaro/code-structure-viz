---
種別: 実装計画書（Issue）
ID: "iss-00004"
タイトル: "Generate Python Structure Snapshots"
関連GitHub: ["#4"]
package_sequence_key: "ISSUE-01"
状態: "draft"
最終更新: "2026-08-25"
依存: ["requirement.md", "design.md"]
親: ["epic-00002", "init-00001"]
---

# iss-00004 Generate Python Structure Snapshots — 実装計画

詳細: [Issue Plan Guide](../../../../../../docs/authoring/issue-plan.md)

## Planning Level

- **selected level: `strict`**
- 理由: first product CLI、versioned public schema、stdout exact bytes、security/redaction、atomic Artifact publication、後続全domainが利用するminimal common contractを導入する。公開後のfield/meaning/exit互換破壊からの回復が難しい。
- risk factor: untrusted source parsing、public CLI/schema、source/secret leakage、false success、partial publication、package/toolchain compatibility。
- `critical`ではない理由: target repositoryとpersistent user dataを変更せず、public release前のIssue単位revertが可能である。
- `critical`再評価条件: source execution、secret/PII exposure、target mutation、不可逆publication、data loss、incident responseが必要なrolloutを追加または観測した場合。

## 目標

単一の実装者が、Requirement/Designにないpublic contractを補完せず、test-firstで次のobservable chainを完成できる状態にする。

```text
validated CLI/config
  -> immutable working-tree SourceView
  -> Python AST semantic snapshot
  -> whole/targeted selection + budget
  -> canonical JSON / PlantUML / run manifest
  -> atomic publication
  -> exact stdout / JSONL stderr / exit
  -> package/offline/CI/security evidence
```

completionはfile作成数ではなく、`I01-AC-001`〜`I01-AC-009`、trace matrix、issue gate command、scope exclusion、clean Git stateで判定する。

## authority と実装者境界

- canonical Requirement/Design/Planのadoptionはmain orchestrator / userのsingle-writer authorityで行う。本Planのproduct commit sequenceへcanonical R/D/P replacement commitを混ぜない。
- 実装者はcanonical R/D/P、accepted ADR、parent R/D/P、`.meta.json`、noncanonical Artifactを勝手に編集しない。
- public contract変更が必要ならcode/schema/goldenを先に変更せず、stop conditionとしてorchestratorへ返す。
- noncanonical explanation Artifactを実装source of truthにしない。特にIssue ID、Requirement数、entity overrun、partial publication、planned pathの古い記述を採用しない。
- 実装結果、実行log、残余riskは完了後にcanonical `report.md`へ別途記録する。本Planをexecution logへ変えない。

## 実装開始前 preflight（P0、repository writeなし）

### exact repository/ref verification

1. taskが指定したrepository、target branch、full expected SHAをconnector/ローカルの両方でexact比較する。default branch、別branch、short SHAへfallbackしない。
2. `git rev-parse --show-toplevel`が意図したrepository rootであることを確認する。
3. `git rev-parse HEAD`とtask expected SHAが一致しない場合はcodeを変更せず停止する。
4. configured upstreamが存在する場合はname/SHAを記録するが、HEAD authorityの代替にしない。fetchしない。
5. root `AGENTS.md`を探索し、存在すれば最初に読む。verified baselineではroot `AGENTS.md`は存在しないが、実装開始時の事実を再確認する。
6. `git status --short`がcleanでない場合、既存変更の所有者とscopeを解決せずに上書き・stash・cleanしない。

### canonical/baseline verification

```bash
python3 ./spec-dock/scripts/spec-dock validate
test -f spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00004-generate-python-structure-snapshots/requirement.md
test -f spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00004-generate-python-structure-snapshots/design.md
test -f spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00004-generate-python-structure-snapshots/plan.md
test ! -e pyproject.toml
test ! -e src/code_structure_viz
test ! -e tests/fixtures/python_snapshot
```

- 最後のproduction-absence assertionがfailした場合は「既存実装あり」にbaselineが変化している。planned treeを重ねず、Design/Planを先に再評価する。
- existing `.github/workflows/ci.yml` のSpecDock `validate` jobを確認し、replacementではなくadditive updateにする。
- repository-owned product licenseがない場合もimplementation/buildは継続できるが、public publish/release jobは作らない。

### toolchain preflight

```bash
python3 --version
git --version
uv --version
```

- Python <3.12、Git <2.39、`uv`不在は実装環境blockerとして停止し、project dependencyへ暗黙追加しない。
- P0でpackage manager install、network fetch、Git mutationを行わない。

## TDD / commit protocol

各commit boundaryで次を同じ順序で行う。

1. **RED**: そのboundaryのpublic/private behaviorをassertするtest/fixture/golden expectationを先に追加し、狙った理由でfailすることを確認する。
2. **GREEN**: Designのexact path/symbol/contractだけを最小実装する。
3. **REFACTOR**: type/invariant/duplicateを整理し、public bytesを変えない。
4. **TARGET GATE**: boundary固有commandを通す。
5. **REGRESSION GATE**: その時点で存在する全test、SpecDock validate、`git diff --check`を通す。
6. **SCOPE REVIEW**: diff/SQLAlchemy/Next/HTML/runtime dependency/source executionが混入していないことを差分で確認する。
7. **COMMIT**: tracked deliverableとtestだけを一commitにする。failing test、`xfail`で隠したintended behavior、cache、temp output、generated venv、secretをcommitしない。

REDの一時状態はworking tree内で観測し、red-only commitを作らない。各listed commitは単独checkoutでその時点の全testがgreenでなければならない。`--no-verify`、automatic `git add -A`、unrelated amend、force pushを実装手順に含めない。

## 順序・commit boundaries

| order | Plan ID | commit message | vertical progress | Requirement/Design trace |
| --- | --- | --- | --- | --- |
| 0 | I01-PLAN-000 | commitなし | preflight / authority / baseline | all |
| 1 | I01-PLAN-001 | `build(iss-00004): bootstrap snapshot CLI contracts` | package、CLI/config/diagnostic/outcome/schema foundation | REQ-001/002/005/007, DES-001/002/005/008 |
| 2 | I01-PLAN-002 | `feat(iss-00004): freeze working tree and resolve Python targets` | read-only Git、SourceView、path/module/class target | REQ-002/003/006, DES-003/007 |
| 3 | I01-PLAN-003 | `feat(iss-00004): extract Python AST semantic snapshots` | module index、safe types、entity/member/relation | REQ-004/006, DES-004/007 |
| 4 | I01-PLAN-004 | `feat(iss-00004): render canonical Python snapshot artifacts` | semantic JSON/PlantUML exact bytes + schemas/goldens | REQ-004/005, DES-005 |
| 5 | I01-PLAN-005 | `feat(iss-00004): publish snapshot outcomes and stream contracts` | budget/outcome/manifest/atomic publication/stdout/stderr/end-to-end | REQ-001/005/006, DES-001/005/006 |
| 6 | I01-PLAN-006 | `test(iss-00004): harden package safety and CI` | security/determinism/package/offline/min/latest/scope gate | REQ-006/007, DES-007/008/009 |

- execution orderは固定。C2はC1、C3はC2、C4はC3、C5はC4、C6はC5のgreen commitを前提とする。
- fixture source authoringは各owning stepのRED内で行う。later behaviorのtestを早期に大量commitしてbranchをredにしない。
- C4のrendererとC5のtransactionを一commitへ潰さない。exact payload bytesとpublication/stream failureを独立review可能にする。
- C6より前にdiff foundation、SQLAlchemy、Next、HTML、release workflowへ進まない。

## I01-PLAN-001 — package / CLI / config / contract bootstrap

### RED

追加するtest:

- `tests/unit/cli/test_parser.py`
- `tests/unit/core/test_config.py`
- `tests/unit/core/test_outcomes.py`
- `tests/contracts/test_json_schemas.py`のschema load/closed properties最小case

先に固定するcase:

- exact required command/option、domain mandatory python、domain omission/all/sqlalchemy/next rejection。
- duplicate single-value option、duplicate format、invalid integer、depth without target。
- diff subcommandと`--from/--to/--pr-target/--max-changed-paths` rejection。
- stdout grammarとselected format pre-source rejection。
- config discovery/precedence、unknown key/type/schema/glob/root validation。
- outcome impossible combination constructor rejection。
- `--version` exact line、meta operation no publication。

expected REDはmodule/file不存在またはasserted parser/config value不一致であり、test importをskipしない。

### GREEN implementation

追加/変更:

```text
.python-version
pyproject.toml
uv.lock
src/code_structure_viz/{__init__.py,__main__.py,py.typed}
src/code_structure_viz/cli/{__init__.py,main.py,parser.py}
src/code_structure_viz/application/{__init__.py,snapshot.py}
src/code_structure_viz/core/{__init__.py,config.py,diagnostics.py,outcomes.py}
src/code_structure_viz/semantic/{__init__.py,canonical_json.py}
schemas/{diagnostic,run-summary,stdout-result}-v1.schema.json
docs/contracts/{cli-v1,config-v1,stdout-v1}.md
```

- `SnapshotApplication`はこのcommitではvalidated requestを受けた後、stable internal fatal outcomeを返してよいが、complete/Artifactを偽装しない。
- entry pointのruntime dependencyは0件。
- initial project versionは`0.1.0.dev0`。
- `uv lock`後に`uv.lock`のdirect/transitive dependencyとsourceをreviewする。

### target gate

```bash
uv sync --frozen --all-groups
uv run pytest tests/unit/cli/test_parser.py tests/unit/core/test_config.py tests/unit/core/test_outcomes.py -q
uv run pytest tests/contracts/test_json_schemas.py -q
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
python3 ./spec-dock/scripts/spec-dock validate
git diff --check
```

### C1 stop conditions

- argparse/library defaultをpublic duplicate/abbreviation behaviorとして受け入れざるを得ない。
- configにDesign外keyを追加する必要がある。
- runtime dependencyが必要になる。
- existing product pathと衝突する。

## I01-PLAN-002 — Git reader / SourceView / targets

### RED

追加するtest/fixture:

- `tests/unit/source/test_source_view.py`
- `tests/unit/source/test_targets.py`
- `tests/helpers/fixture_repo.py`
- fixture `not_applicable`、`unicode_paths`の最小source

case:

- exact repo root/nested/non-Git/bare/unborn HEAD。
- Git allowlistとfixed env。write commandがportから到達不能。
- tracked + nonignored untracked `.py`、deleted/ignored untracked/`.pyi`除外。
- built-in source root mapping、explicit root nonexistent、include/exclude glob。
- strict UTF-8/NFC、normalization collision。
- regular/internal symlink/outside symlink/cycle。
- initial freeze mutation、pre-publication drift probe。
- path/module/class syntax normalizationとcanonical sort。

### GREEN implementation

追加:

```text
src/code_structure_viz/source/{__init__.py,git_repository.py,source_view.py,targets.py}
docs/contracts/source-view-v1.md
tests/fixtures/python_snapshot/not_applicable/repo/...
```

- `GitRepositoryReader`のcommand builderを一箇所にし、testはargument vector/env exact equalityをassertする。
- private stagingはtest-provided output parent内に作る。
- SourceView fingerprint exampleをdoc/testで固定する。
- targetはsyntax parseまで。module/class semantic resolutionをC3へ先送りするがfree-form stringをapplicationへ渡さない。

### target gate

```bash
uv run pytest tests/unit/source/test_source_view.py tests/unit/source/test_targets.py -q
uv run pytest tests/unit tests/contracts -q
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
python3 ./spec-dock/scripts/spec-dock validate
git diff --check
```

### C2 stop conditions

- source freezeにcheckout/worktree/fetch/stash等が必要になる。
- source bytesをrepository pathからanalyzerが再読する設計になる。
- output destinationをrepo内に許可しないとtestが成立しない。
- non-UTF8/unsafe symlinkをsilent skipする必要が生じる。

## I01-PLAN-003 — Python AST semantic model / selection

### RED

追加:

- `tests/unit/python/test_module_index.py`
- `tests/unit/python/test_type_expr.py`
- `tests/unit/python/test_analyzer.py`
- `tests/unit/python/test_selection.py`
- `tests/integration/python/test_targeted_snapshot.py`
- fixture `whole`、`targeted`、`partial_safe`、`failed_seed`、`module_collision`、`class_collision`、`zero_class`

case matrix:

- module mapping: `src`, `.`, `__init__.py`, namespace、Unicode identifier、keyword/invalid segment、collision。
- AST grammar fixed 3.12、PEP 263/BOM、syntax/encoding/read classification。
- direct module/nested class、module/class control-flow内classとfunction-local classのexclusion、duplicate class identity collision。
- class/instance field merge、conflicting annotation warning、tuple/list target、AugAssign、nested lexical scope exclusion、method overload ordinal、async、property getter/setter/deleter、static/class method、decorator call redaction。
- safe type Name/Attribute/Subscript/tuple/union/forward ref/Literal/Annotated/unsupported。
- import alias/relative/star/external/unknown。
- inheritance/composition/typed/import relation identity/direction/dedupe。
- whole mode、path/module/class target、longest module prefix、multiple target union。
- upstream/downstream depth 0/1/2、membership zero cost、frontier、unrelated exclusion。
- missing/ambiguous/failed seed payload unavailable precondition。
- non-seed failure partial_safe precondition。

### GREEN implementation

追加:

```text
src/code_structure_viz/adapters/{__init__.py,python/__init__.py}
src/code_structure_viz/adapters/python/{model.py,module_index.py,type_expr.py,analyzer.py,selection.py}
docs/contracts/python-semantic-v1.md
```

- model constructorとID/sort functionを先に実装する。
- `ast.unparse`をpublic type/decorator outputへ直接使わない。
- analyzer outputはfull safe index、selector outputはselected `PythonSnapshot`とcoverage。
- renderer/publicationはまだ接続しない。

### target gate

```bash
uv run pytest tests/unit/python -q
uv run pytest tests/integration/python/test_targeted_snapshot.py -q
uv run pytest tests/unit tests/integration tests/contracts -q
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
python3 ./spec-dock/scripts/spec-dock validate
git diff --check
```

### C3 stop conditions

- class/member/relation identityをDesignから変更する必要がある。
- target code import/runtime type evaluationが必要になる。
- unknown relationを架空internal entityへ補完する必要がある。
- target selectionにdiff/changed-path/before-after graphが必要になる。

## I01-PLAN-004 — semantic JSON / PlantUML exact bytes

### RED

追加:

- `tests/unit/python/test_semantic_json.py`
- `tests/unit/python/test_plantuml.py`
- `schemas/semantic-v1.schema.json`
- `docs/contracts/python-plantuml-v1.md`
- golden `whole`、`targeted`、`partial_safe`のsemantic/PlantUML payload

case:

- complete/partial_safe top-level field presence/order。
- all nested field order、nullable field、array sort、NFC、no-space、one LF。
- Schema `additionalProperties:false`。
- entity/member/relation ID and exact safe type strings。
- PlantUML exact preamble/package/class/member/relation/legend/end order。
- alias full SHA、escape injection、internal-only relation。
- partial_safe note、zero-class note。
- no timestamp/body/comment/default/secret/absolute/temp path。

REDではgoldenをproduction outputで自動更新せず、Design exampleからreviewed expected bytesを置く。

### GREEN implementation

追加:

```text
src/code_structure_viz/adapters/python/{semantic_json.py,plantuml.py}
schemas/semantic-v1.schema.json
docs/contracts/python-plantuml-v1.md
tests/golden/python_snapshot/{whole,targeted,partial_safe}/...
```

- rendererはbytesを返すpure function。
- semantic rendererとPlantUML rendererは互いのoutputをparseしない。同じsnapshot modelを読む。
- JSON Schema validation helperはtest/dev pathに置き、runtime dependencyにしない。productionはtyped constructor/invariantを信頼し、publication前testable validator portでschema checkできる設計にする。

### target gate

```bash
uv run pytest tests/unit/python/test_semantic_json.py tests/unit/python/test_plantuml.py -q
uv run pytest tests/contracts/test_json_schemas.py -q
uv run pytest tests/unit tests/integration tests/contracts -q
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
git diff --check
```

### golden update review

必要な場合だけ:

```bash
uv run python -m tests.helpers.golden --update-golden whole
uv run python -m tests.helpers.golden --update-golden targeted
uv run python -m tests.helpers.golden --update-golden partial_safe
git diff -- tests/golden/python_snapshot
uv run pytest tests/unit/python/test_semantic_json.py tests/unit/python/test_plantuml.py tests/contracts/test_json_schemas.py -q
```

- update command実行だけをgolden正当化にしない。Design/schemaとhuman diffを確認する。

### C4 stop conditions

- schema field/order/filenameを追加・変更する必要がある。
- PlantUML binary/serverをruntimeへ導入する必要がある。
- external/unknown relationを架空nodeとして描かないとtestが通らない。
- source literalをtype/signature/decoratorへ保持する必要がある。

## I01-PLAN-005 — budget / manifest / atomic publication / streams / E2E

### RED

追加:

- `tests/unit/core/test_budget.py`
- `tests/unit/artifacts/test_manifest.py`
- `tests/unit/artifacts/test_writer.py`
- `tests/unit/artifacts/test_streams.py`
- `tests/acceptance/python/test_snapshot_cli.py`
- `tests/acceptance/python/test_snapshot_failures.py`
- `tests/acceptance/python/test_snapshot_budget.py`
- `tests/acceptance/python/test_stdout_selector.py`
- `schemas/run-manifest-v1.schema.json`
- `tests/golden/python_snapshot`のmanifest/stdout/stderr/file-list/exit

minimum table-driven matrix:

| case | formats | selector | domain | files | stdout | exit |
| --- | --- | --- | --- | --- | --- | --- |
| whole | both | none | complete | JSON/Puml/manifest | summary | 0 |
| whole semantic | semantic | python:semantic-json | complete | JSON/manifest | exact JSON | 0 |
| whole puml | puml | python:plantuml | complete | Puml/manifest | exact Puml | 0 |
| manifest | both | manifest | complete | all | exact manifest | 0 |
| not applicable | both | none | not_applicable | manifest | summary | 0 |
| not applicable selected payload | semantic | python:semantic-json | not_applicable | manifest | unavailable result | 0 |
| partial safe | both | selected payload | incomplete/partial_safe | all | exact payload | 3 |
| failed seed | both | selected payload | incomplete/payload_unavailable | manifest | unavailable result | 3 |
| entity 501 | both | none | incomplete/payload_unavailable | manifest | summary | 3 |
| invalid selector/config/option | n/a | n/a | usage | none | empty | 2 |
| output exists/inside repo | n/a | none | fatal | none | summary | 1 |
| drift | n/a | manifest | fatal | none | unavailable result | 1 |
| handled SIGINT pre-rename | n/a | none/manifest | interrupted | none | summary/result | 130 |

budget testはgenerated 500/501/600 classを使用する。snapshot/no diff testはunborn HEAD + 1,001 non-Python changesでnormal snapshotが進み、diff-only optionだけがpre-source exit2になることをspyで確認する。

### GREEN implementation

追加:

```text
src/code_structure_viz/core/budget.py
src/code_structure_viz/artifacts/{__init__.py,manifest.py,writer.py,streams.py}
schemas/run-manifest-v1.schema.json
docs/contracts/run-manifest-v1.md
```

変更:

```text
src/code_structure_viz/application/snapshot.py
src/code_structure_viz/cli/main.py
```

implementation order:

1. `EntityBudgetGate`とoutcome constructors。
2. artifact descriptorsとmanifest builder/run fingerprint。
3. `OutputTransaction` stage/validate/fsync/rename/cleanup。
4. `StderrEmitter` JSONL。
5. `StdoutEmitter` summary/result/exact file copy。
6. `SnapshotApplication` lifecycle接続。
7. SIGINT cancellation checkpoint。
8. installed CLI subprocess acceptance。

- no selector summaryはpublication後のcommitted outcomeから作る。
- available selectorはfinal output fileをbinary readし、そのbytesを`sys.stdout.buffer`へ一回でwriteする。
- publication後にpayload/manifestをmemory再serializeしてstdoutへ出さない。
- manifest exact bytesをstdoutへ出すcaseでもself descriptorを追加しない。

### target gate

```bash
uv run pytest tests/unit/core/test_budget.py tests/unit/artifacts -q
uv run pytest tests/acceptance/python/test_snapshot_cli.py -q
uv run pytest tests/acceptance/python/test_snapshot_failures.py -q
uv run pytest tests/acceptance/python/test_snapshot_budget.py -q
uv run pytest tests/acceptance/python/test_stdout_selector.py -q
uv run pytest tests/unit tests/integration tests/acceptance tests/contracts -q
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
python3 ./spec-dock/scripts/spec-dock validate
git diff --check
```

### C5 stop conditions

- final outputをdirectory renameでatomicにできないpath contractが必要になる。
- manifest self-hash/self descriptorが必要になる。
- stdout exact bytesにsummary/newlineを足す必要がある。
- partial_safeとpayload_unavailableを同じpublicationへ潰す必要がある。
- entity overrunをtruncateしないと処理できない。

## I01-PLAN-006 — security / determinism / packaging / CI / scope

### RED

追加:

- `tests/security/test_python_static_boundary.py`
- `tests/acceptance/python/test_snapshot_determinism.py`
- `tests/packaging/test_distribution.py`
- `tests/contracts/test_scope_exclusions.py`
- fixture `security`、`unborn_many_changes`、runtime outside symlink helper
- `THIRD_PARTY_LICENSES.md`
- `ci/latest-python.txt`
- `ci/toolchains/git-2.39.5.Dockerfile`
- `ci/toolchains/git-2.39.5.sha256`

security assertions:

- monkeypatch/spyで`importlib`, `py_compile`, `compileall`, `exec`, `eval`, `runpy`, target subprocess、entry point/plugin loadingへ到達しない。production sourceのstatic scanで直接`compile(...)` callが0件であることを確認し、parser spyで`ast.parse(..., feature_version=(3, 12))`だけがAST生成経路であることを確認する。
- fixture top-level marker fileが作られない。
- Git command logがDesign allowlistだけ。
- HEAD、refs、index、status、tracked/untracked bytesがtool実行前後で同じ。outputはrepo外。
- payload、manifest、stdout、stderr、PlantUML、captured logにsecret sentinel、source statement、comment、default literal、repo absolute path、temp path、tracebackがない。
- unsafe pathはsuccessへ変換されない。

determinism assertions:

- separate nonexistent output dirsへ同一requestを2回実行し、relative file set、各bytes、stdout/stderr、exitが同じ。
- file creation order、filesystem iteration order、CLI target/format orderの意味的同値caseでcanonical outputが同じ。
- Python 3.12/3.14 laneでchecked-in whole/targeted goldenが同じ。

scope assertions:

- CLI help/schemaに`diff`, `sqlalchemy`, `next`, `html` command/formatが登録されていない。ただしusage rejection code/test stringとdocsのout-of-scope記述はallowlistする。
- production imports/dependenciesにSQLAlchemy、Node bridge、HTML renderer、`pyclassuml`、`tree-git-diff`がない。
- `src/code_structure_viz`に`diff`/SQLAlchemy/Next implementation packageを作っていない。

### GREEN hardening/package/CI

- no runtime dependenciesをwheel metadataでassertする。
- wheel/sdist file listにtests fixture、temp source、secret、SpecDock docsを含めない。
- fresh venvへwheelを`pip install --no-index <wheel>`し、outside temporary Git fixtureでCLIを実行する。
- network trapはsocket connectをfailさせ、runtimeがnetwork不要であることを検証する。
- `.github/workflows/ci.yml`のexisting `validate` jobを保持し、Designの5 product jobsを追加する。
- CI-only Git 2.39.5 source archive URL/checksumをpinし、container build logでversionをassertする。
- Python latest laneは`ci/latest-python.txt`=`3.14`をreadし、hard-coded重複を避ける。
- lock/license checkerは`uv.lock`と`THIRD_PARTY_LICENSES.md`の差分をfailさせる。

### target gate

```bash
uv run pytest tests/security/test_python_static_boundary.py -q
uv run pytest tests/acceptance/python/test_snapshot_determinism.py -q
uv run pytest tests/packaging/test_distribution.py -q
uv run pytest tests/contracts/test_scope_exclusions.py tests/contracts/test_json_schemas.py -q
uv build
```

fresh offline verification:

```bash
rm -rf .tmp/iss-00004-offline-venv .tmp/iss-00004-dist
mkdir -p .tmp/iss-00004-dist
cp dist/*.whl .tmp/iss-00004-dist/
python3 -m venv .tmp/iss-00004-offline-venv
.tmp/iss-00004-offline-venv/bin/python -m pip install --no-index .tmp/iss-00004-dist/*.whl
.tmp/iss-00004-offline-venv/bin/code-structure-viz --version
uv run pytest tests/packaging/test_distribution.py -q
rm -rf .tmp/iss-00004-offline-venv .tmp/iss-00004-dist
```

### C6 stop conditions

- wheel metadataにruntime dependencyが現れる。
- dependency/license/provenanceを確認できない。
- minimum Git laneを実行せずversion checkだけで済ませようとする。
- security negative scan、target mutation、determinism、offline installのいずれかがfailする。
- CI existing SpecDock validateを削除・弱体化する必要がある。
- release upload/publish credentialが必要になる。

## acceptance fixture / golden completion checklist

| fixture/case | semantic | PlantUML | manifest | stdout | stderr | exit | required classification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| whole | golden | golden | golden | summary/exact variants | empty or stable warnings | 0 | complete |
| targeted | golden | golden | golden | summary | stable frontier warnings | 0 | complete |
| zero_class | golden empty entities | golden note | golden | summary | empty | 0 | complete |
| not_applicable | none | none | golden | summary/result/manifest | empty | 0 | not_applicable |
| partial_safe | golden safe subset | golden incomplete note | golden | exact/summary | parse diagnostic | 3 | partial_safe |
| failed_seed | none | none | golden | result/summary | target/parse diagnostic | 3 | payload_unavailable |
| module_collision nonseed | golden safe subset | golden | golden | summary | collision diagnostic | 3 | partial_safe |
| class_collision whole/seed | golden safe subset or none | golden or none | golden | summary/result | identity collision diagnostic | 3 | partial_safe / payload_unavailable |
| unsafe symlink | none | none | golden | result/summary | source diagnostic | 3 | payload_unavailable |
| entity501 | none | none | golden | result/summary | budget diagnostic | 3 | payload_unavailable |
| drift/output collision | none | none | none | summary/result | run diagnostic | 1 | fatal |
| usage/config/diff option | none | none | none | empty | usage/config diagnostic | 2 | usage |
| interrupt | none | none | none | summary/result | interrupt diagnostic | 130 | interrupted |

published-files goldenはlexical relative path一行一file、末尾LF。exit-code goldenはdecimal一行、末尾LF。

## issue gate commands

C6後、次をrepository rootのclean checkoutで順に実行する。

```bash
uv sync --frozen --all-groups
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
uv run pytest tests/unit -q
uv run pytest tests/integration/python/test_targeted_snapshot.py -q
uv run pytest tests/acceptance/python/test_snapshot_cli.py -q
uv run pytest tests/acceptance/python/test_snapshot_failures.py -q
uv run pytest tests/security/test_python_static_boundary.py -q
uv run pytest tests/acceptance/python/test_snapshot_determinism.py -q
uv run pytest tests/acceptance/python/test_snapshot_budget.py -q
uv run pytest tests/acceptance/python/test_stdout_selector.py -q
uv run pytest tests/packaging/test_distribution.py -q
uv run pytest tests/contracts -q
uv run pytest -q
uv build
python3 ./spec-dock/scripts/spec-dock validate
git diff --check
```

追加確認:

```bash
git status --short
git diff --stat
git diff -- . ':!spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00004-generate-python-structure-snapshots/requirement.md' ':!spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00004-generate-python-structure-snapshots/design.md' ':!spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00004-generate-python-structure-snapshots/plan.md'
```

- issue gate完了時はcache/temp/distをcleanupし、tracked差分だけをreviewする。
- `dist/`はverification outputでありcommitしない。

## Requirement → Design → Plan → acceptance → test trace

| Requirement | Design | Plan | Acceptance | Test |
| --- | --- | --- | --- | --- |
| I01-REQ-001 | I01-DES-001 | I01-PLAN-001, I01-PLAN-005 | I01-AC-001 | I01-AT-001 |
| I01-REQ-002 | I01-DES-002 | I01-PLAN-001, I01-PLAN-002 | I01-AC-002, I01-AC-006, I01-AC-007 | I01-AT-002, I01-AT-006, I01-AT-007 |
| I01-REQ-003 | I01-DES-003 | I01-PLAN-002, I01-PLAN-003 | I01-AC-002, I01-AC-003 | I01-AT-002, I01-AT-003 |
| I01-REQ-004 | I01-DES-004 | I01-PLAN-003, I01-PLAN-004 | I01-AC-001, I01-AC-002 | I01-AT-001, I01-AT-002 |
| I01-REQ-005 | I01-DES-005 | I01-PLAN-004, I01-PLAN-005 | I01-AC-001, I01-AC-007, I01-AC-009 | I01-AT-001, I01-AT-007, I01-AT-009 |
| I01-REQ-006 | I01-DES-006, I01-DES-007 | I01-PLAN-002, I01-PLAN-003, I01-PLAN-005, I01-PLAN-006 | I01-AC-003, I01-AC-004, I01-AC-005, I01-AC-006 | I01-AT-003, I01-AT-004, I01-AT-005, I01-AT-006 |
| I01-REQ-007 | I01-DES-008, I01-DES-009 | I01-PLAN-001, I01-PLAN-006 | I01-AC-008, I01-AC-009 | I01-AT-008, I01-AT-009 |

trace gap、orphan Requirement/Design/Plan/Test、同じIDの意味違いをcontract testまたはreviewで拒否する。

## regression boundary

- target repositoryのHEAD、refs、index、status、tracked/untracked bytesをtoolが変更しない。
- output dirはrepo外、destination absent、one directory rename。rerun to same outputはcollision fatalで既存bytes不変。
- same-input byte equality、format/target canonicalization、diagnostic orderを維持する。
- no-Python、zero-class、partial_safe、payload_unavailableをempty successへ潰さない。
- entity 501をtruncateせず、changed-path 1,001やimplicit base absenceをsnapshot failureにしない。
- selector invalid時はsource/Git/staging spy call 0件。
- source body/comment/literal/secret/absolute/temp path/traceback/raw exception/Git stderrを全channelへ出さない。
- visual semanticsはarrow/text/legendで区別し、colorだけに依存しない。
- package runtime dependency 0、Node/DB/HTML/legacy dependency 0。
- existing SpecDock CI/validationを維持する。

## rollback / forward recovery

### migration

- persistent data migration: **N/A**。本productはread-only analyzerでbaseline production/dataがない。
- output migration: **N/A**。Artifactはimmutable run outputでexisting outputをrewriteしない。

### rollback trigger

- false complete/exit0、target execution/Git mutation、secret/absolute path leak、schema/golden drift、partial publication、overwrite、nondeterminism、offline/package/license failure。

### rollback unit/order

1. rollout/releaseは存在しないため停止。
2. latest green implementation commitから逆順にIssue commitをrevertする。
3. public schema/CLI previewがまだないためC1〜C6を一体revertできる。
4. parent R/D/P、accepted ADR、SpecDock metadata、noncanonical Artifactはrevert対象にしない。
5. canonical R/D/P adoption自体を戻す場合はorchestratorがexact replacement commitをwhole-file revertする。

### forward recovery

- unsafe patternをcompleteへ残さず、`partial_safe`または`payload_unavailable`へ狭める。
- v1 bytes/meaningを破壊する修正はv1 overwriteでなくnew contract versionを検討する。
- affected existing outputを自動scan/rewrite/deleteしない。
- security/privacy incidentに該当する場合はPlanning Levelをcriticalへ上げる。

## final stop conditions

実装中、次の一つでも成立したら次commitへ進まず、現在のgreen commit/working diffと根拠を引き渡す。

- repository/branch/SHA/root instructionsをexact再検証できない。
- canonical Requirement/Designのpublic contractが矛盾または不足し、実装者判断で補う必要がある。
- planned path/symbolが既存production implementationと衝突する。
- REDが想定した理由でfailしない、またはGREENがunrelated behaviorを壊す。
- source execution、Git write、secret/path leak、truncation、overwrite、partial publication、nondeterminismを観測する。
- runtime dependency、diff、SQLAlchemy、Next、HTML、release publishが必要になる。
- accepted ADR/parent R/D/Pを変更しないと成立しない。
- lock/license/provenance、minimum/latest/offline gateを証明できない。
- issue gate commandのいずれかをskip/xfail/allow-failureにしないとgreenにできない。

## exit / handoff

Issue implementation-readyおよびimplementation completeの判定を分ける。

### implementation-ready

- canonical replacementがadopt済み。
- P0 verificationが成功。
- public contract、path/symbol、fixture/golden、test、command、commit、stop conditionにopen decisionがない。
- product codeなしbaselineが維持される。

### implementation complete

- C1〜C6がlisted message/責務で存在し、各commit単独でgreen。
- I01-AC-001〜I01-AC-009のevidenceが揃う。
- issue gate全成功、clean status、forbidden scope 0件。
- wheel/offline/minimum/latest/macOS/security/determinism/SpecDock validation成功。
- residual risk、unsupported static pattern、dependency/license inventory、implementation evidenceをReportへ渡す。
- Python diff、SQLAlchemy、Next、all-domain、product HTMLへは進まず、ISSUE-02へversioned contractだけをhandoffする。
