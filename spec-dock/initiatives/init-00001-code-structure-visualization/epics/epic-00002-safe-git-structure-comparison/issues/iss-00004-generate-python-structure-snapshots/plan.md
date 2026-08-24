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
| 3 | I01-PLAN-003 | `feat(iss-00004): extract Python AST semantic snapshots` | module index、safe types、TypeReference resolution、entity/member/relation | REQ-004/006, DES-004/007 |
| 4 | I01-PLAN-004 | `feat(iss-00004): render canonical Python snapshot artifacts` | semantic JSON/PlantUML exact bytes、classless module layout + test/build-time schemas/goldens | REQ-004/005/007, DES-005/008 |
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
- `tests/unit/core/test_diagnostics.py`
- `tests/unit/core/test_outcomes.py`
- `tests/contracts/test_json_schemas.py`のschema load/closed properties最小case

先に固定するcase:

- exact required command/option、domain mandatory python、domain omission/all/sqlalchemy/next rejection。
- duplicate single-value option、duplicate format、invalid integer、depth without target。
- diff subcommandと`--from/--to/--pr-target/--max-changed-paths` rejection。
- stdout grammarとselected format pre-source rejection。
- config discovery/precedence、unknown key/type/schema/glob/root validation。quoted unknown key `"/tmp/secret"`相当はexact constant `CSV-CONFIG-003`一件、all context nullで、raw/normalized key sentinelをstdout/stderr/logへ出さない。
- outcome impossible combination constructor rejection。
- diagnostic schema/order、run-level fail-fast selection、closed code default/context skeleton。unknown key selectionはinternal sortだけで、message builderへkeyを渡さない。
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
uv run pytest tests/unit/cli/test_parser.py tests/unit/core/test_config.py tests/unit/core/test_diagnostics.py tests/unit/core/test_outcomes.py -q
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

- `tests/unit/source/test_git_repository.py`
- `tests/unit/source/test_source_view.py`
- `tests/unit/source/test_targets.py`
- `tests/integration/source/test_git_repository.py`
- `tests/helpers/fixture_repo.py`
- fixture `not_applicable`、`unicode_paths`、`unborn_many_changes`の最小source

case:

- exact repo root/nested/non-Git/bare。
- HEAD return matrix: valid 40/64-hex commit、`symbolic-ref` strict UTF-8 round-trip + `refs/heads/*` + `check-ref-format`成功 + `show-ref` missingだけがunborn、invalid refname、existing refだがmissing/non-commit object、detached invalid HEAD、malformed/protocol/subprocess failure。`rev-parse -> symbolic-ref -> check-ref-format -> show-ref`のargument vector、return-code branch、fixed env、stderr非依存をassertする。
- Git allowlistとfixed env。write commandがportから到達不能。
- tracked + nonignored untracked `.py`、deleted/ignored untracked/`.pyi`除外。
- built-in source root mapping、explicit root nonexistent、include/exclude glob。
- raw NUL-delimited path bytesのstrict UTF-8 success/failure。non-UTF-8は`CSV-SOURCE-003` exactly one、domain/path/symbol/line null、SourceView/fingerprint/staging/final Artifact 0件。surrogate/replacement/hash path 0件。
- NFC valid path、normalization/case collisionは`CSV-SOURCE-004` payload_unavailable。一方をwinnerにしない。
- regular/internal symlink/outside symlink/cycle。
- initial freeze mutation、pre-publication drift probe。
- path/module/class syntax normalizationとcanonical sort。

### GREEN implementation

追加:

```text
src/code_structure_viz/source/{__init__.py,git_repository.py,source_view.py,targets.py}
docs/contracts/source-view-v1.md
tests/fixtures/python_snapshot/{not_applicable,unicode_paths,unborn_many_changes}/repo/...
```

- `GitRepositoryReader`のcommand builderを一箇所にし、testはargument vector/env exact equalityをassertする。
- `HeadState.Commit|Unborn`以外を返さず、`head_commit=null`はUnborn constructorからだけ作る。
- non-UTF-8 enumeration errorはSourceView型へ入れずrun fatal port errorにする。
- private stagingはtest-provided output parent内に作る。
- SourceView fingerprint exampleをdoc/testで固定する。
- targetはsyntax parseまで。module/class semantic resolutionをC3へ先送りするがfree-form stringをapplicationへ渡さない。

### target gate

```bash
uv run pytest tests/unit/source/test_git_repository.py tests/unit/source/test_source_view.py tests/unit/source/test_targets.py -q
uv run pytest tests/integration/source/test_git_repository.py -q
uv run pytest tests/unit tests/integration/source tests/contracts -q
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
python3 ./spec-dock/scripts/spec-dock validate
git diff --check
```

### C2 stop conditions

- source freezeにcheckout/worktree/fetch/stash等が必要になる。
- unborn判定をGit stderr text、単一nonzero return、`check-ref-format`なしの`show-ref` return 1、filesystemの`.git/HEAD`直接推測へ依存させる必要がある。
- source bytesをrepository pathからanalyzerが再読する設計になる。
- output destinationをrepo内に許可しないとtestが成立しない。
- non-UTF8 pathをsurrogate/hash/replacementでcanonicalize、またはunsafe symlink/normalization collisionをsilent skipする必要が生じる。

## I01-PLAN-003 — Python AST semantic model / selection

### RED

追加:

- `tests/unit/python/test_model.py`
- `tests/unit/python/test_module_index.py`
- `tests/unit/python/test_type_expr.py`
- `tests/unit/python/test_analyzer.py`
- `tests/unit/python/test_selection.py`
- `tests/integration/python/test_targeted_snapshot.py`
- fixture `whole`、`canonical_model`、`annotation_references`、`module_only`、`targeted`、`target_absence`、`partial_safe`、`failed_seed`、`module_collision`、`class_collision`、`diagnostics`、`zero_class`

case matrix:

- module mapping: `src`, `.`, `__init__.py`, namespace、Unicode identifier、keyword/invalid segment、collision。
- AST grammar fixed 3.12、PEP 263/BOM、syntax/encoding/read classification。
- direct module/nested class、module/class control-flow内classとfunction-local classのexclusion、duplicate class identity collision。
- class/instance field merge、canonical occurrence winner range、conflicting annotation一field一diagnostic、tuple/list target、AugAssign、nested lexical scope exclusion。
- field/property/methodのexact occurrence identityとcollector duplicate winner、method/property same-base identityのfull location orderと0-based declaration ordinal、async、getter/setter/deleter、static/class method、decorator call redaction。
- enum rankとexact entity/member sort tuple。input/collector orderをreverseして同じID/order/rangeになる。
- closed type grammar: `()`, `(T,)`, `(T1, T2)`, subscript tuple arguments、nested union left-to-right flatten/no redundant parentheses、forward ref、Literal arity redaction、Annotated metadata collapse、unsupported site一diagnostic。
- TypeReference closed table: Name/Attribute、subscript base/argument、union/tuple、Literal/Annotated、inheritance head-only adoption、field/parameter/return adoption。same-module top-level/nested longest-prefix、import alias、absolute internal、unknownのpriorityとexact target.name。
- exclusion vectors: unqualified builtin set、`builtins.`/`typing.`/`typing_extensions.` helper、PEP 695/legacy TypeVar registry。`Missing`、`list[Foo]`、`Generic[T]`、external aliasのrelation/diagnostic exact count。
- import alias/relative/star/external/unknown。ambiguous import bindingはwinnerを選ばず、externalだけはwarning 0、unknownだけが`CSV-PY-008`。
- relation identity/direction。same identityが異なるlineにあるcaseでoccurrence key最小rangeをwinner、different member/annotationは保持、exact relation sort tuple。
- whole mode、path/module/class target、longest module prefix、multiple target union。classless `app.a -> app.b` module targetはselected module二件、entity/member 0、internal import relation一件。
- **not_applicableはtarget 0 + candidate 0だけ**。no-Python repoのpath/module/class target、zero-class repoのmissing class targetは`CSV-PY-006` per target + payload_unavailable。
- upstream/downstream depth 0/1/2、membership zero cost、frontier、unrelated exclusion。depth-limit frontierだけではdiagnostic/stderrを作らない。
- missing/ambiguous/failed seed payload unavailable。file/collision diagnosticとtarget diagnosticの双方のcardinality/context。
- non-seed failure partial_safe precondition。

### GREEN implementation

追加:

```text
src/code_structure_viz/adapters/{__init__.py,python/__init__.py}
src/code_structure_viz/adapters/python/{model.py,module_index.py,type_expr.py,analyzer.py,selection.py}
docs/contracts/python-semantic-v1.md
```

- model constructor、enum rank、identity digest preimage、occurrence key、sort function、dedupe winnerを先に実装する。TypeReference occurrence、type-parameter registry、resolver priority、target mappingは`type_expr.py`/`analyzer.py`のpure value/functionとして固定する。
- `ast.unparse`をpublic type/decorator outputへ直接使わない。
- analyzer outputはfull safe index、selector outputはselected `PythonSnapshot`とcoverage。
- `NotApplicable` constructorをwhole-mode predicateに限定し、targeted request型から呼べないようにする。
- diagnostic builderはDesignのcode/cardinality/context keyで生成し、depth frontierからdiagnosticを作らない。
- renderer/publicationはまだ接続しない。

### target gate

```bash
uv run pytest tests/unit/python/test_model.py tests/unit/python/test_module_index.py tests/unit/python/test_type_expr.py tests/unit/python/test_analyzer.py tests/unit/python/test_selection.py -q
uv run pytest tests/integration/python/test_targeted_snapshot.py -q
uv run pytest tests/unit/core/test_diagnostics.py tests/unit/python tests/integration/python tests/contracts -q
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
python3 ./spec-dock/scripts/spec-dock validate
git diff --check
```

### C3 stop conditions

- class/member/relation identity、sort tuple、occurrence winner、type grammar、TypeReference extraction/adoption/resolution/exclusion/target.nameをDesignから変更する必要がある。
- target code import/runtime type evaluationが必要になる。
- unknown relationを架空internal entityへ補完する必要がある。
- explicit target failureをnot_applicableまたはsafe target subsetへ縮退しないとtestが通らない。
- depth frontierに新diagnostic codeを追加しないとtestが通らない。
- target selectionにdiff/changed-path/before-after graphが必要になる。

## I01-PLAN-004 — semantic JSON / PlantUML exact bytes

### RED

追加:

- `tests/unit/python/test_semantic_json.py`
- `tests/unit/python/test_plantuml.py`
- `schemas/semantic-v1.schema.json`
- `docs/contracts/python-plantuml-v1.md`
- golden `whole`、`canonical_model`、`annotation_references`、`module_only`、`targeted`、`partial_safe`のsemantic/PlantUML payload

case:

- complete/partial_safe top-level field presence/order。
- all nested field order、nullable field、exact entity/member/relation sort tuple、NFC、no-space、one LF。
- Schema `additionalProperties:false`。dev-only validatorでSchema self-check、全golden、positive constructor vector、field/type/nullability mutation negative vectorをtest/build-timeに検証する。production renderer/runtimeはSchema file/validatorをloadしない。
- member ID/ordinal/merge winner range、relation ID/dedupe winner range、exact safe type strings、TypeReference target resolution/name/exclusion。
- PlantUML exact preamble/package/class/member/relation/legend/end order。
- parameter grammar: positional-only `/`、keyword-only `*`、`*args`、`**kwargs`、annotation null、`has_default` exact ` = …`、receiver removal/recalculated separators。
- escape table: backslash、quote、LF/CR/TAB、Cc/Cf/Cs/Zl/Zpのexact printable sequence。raw directive/newline/surrogate encoding failure 0件。
- same kind/source/target/label relationはvisual line一件、different kindは別line。representative relation sort minimum、semantic JSON relation count不変。
- alias full SHA、internal-only relation、partial_safe note。classless selected moduleごとのdeclared package alias + `N_EMPTY_` note、全package後のmodule import relation、global zero-class note禁止。
- no timestamp/body/comment/default literal/secret/absolute/temp path。

REDではgoldenをproduction outputで自動更新せず、Design exampleからreviewed expected bytesを置く。

### GREEN implementation

追加:

```text
src/code_structure_viz/adapters/python/{semantic_json.py,plantuml.py}
schemas/semantic-v1.schema.json
docs/contracts/python-plantuml-v1.md
tests/golden/python_snapshot/{whole,canonical_model,annotation_references,module_only,targeted,partial_safe}/...
```

- rendererはbytesを返すpure function。
- semantic rendererとPlantUML rendererは互いのoutputをparseしない。同じsnapshot modelを読む。
- visual dedupeはPlantUML renderer内の`VisualRelationKey`だけへ適用し、semantic modelをmutateしない。
- JSON Schema validation helperは`tests/contracts`だけに置く。production packageはvalidator port、schema loader、schema resource lookup、`jsonschema` importを持たず、typed constructorとclosed serializer invariantだけをruntime gateにする。acceptance subprocess outputはtest側がcapture後にSchemaへvalidateする。

### target gate

```bash
uv run pytest tests/unit/python/test_semantic_json.py tests/unit/python/test_plantuml.py -q
uv run pytest tests/contracts/test_json_schemas.py -q
uv run pytest tests/unit/python tests/integration tests/contracts -q
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
git diff --check
```

### golden update review

必要な場合だけ:

```bash
uv run python -m tests.helpers.golden --update-golden whole
uv run python -m tests.helpers.golden --update-golden canonical_model
uv run python -m tests.helpers.golden --update-golden annotation_references
uv run python -m tests.helpers.golden --update-golden module_only
uv run python -m tests.helpers.golden --update-golden targeted
uv run python -m tests.helpers.golden --update-golden partial_safe
git diff -- tests/golden/python_snapshot
uv run pytest tests/unit/python/test_semantic_json.py tests/unit/python/test_plantuml.py tests/contracts/test_json_schemas.py -q
```

- update command実行だけをgolden正当化にしない。Design/schemaとhuman diffを確認する。

### C4 stop conditions

- schema field/order/filename、member/relation sort/winner、TypeReference/type text、parameter token、escape sequence、classless module layout、visual duplicate policyを追加・変更する必要がある。
- PlantUML binary/serverまたはJSON Schema validator/loaderをruntimeへ導入する必要がある。
- external/unknown relationを架空nodeとして描かないとtestが通らない。
- source literalをtype/signature/decorator/default displayへ保持する必要がある。

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

| case | request/selector | domain/run | published files | stdout | stderr | exit |
| --- | --- | --- | --- | --- | --- | --- |
| whole | both / none | complete | JSON/Puml/manifest | summary | empty | 0 |
| canonical_model / annotation_references | both / none | complete | JSON/Puml/manifest | summary | exact model/reference warnings | 0 |
| module_only target `app.a`, downstream 1 | both / none | complete | zero-entity JSON/Puml/manifest | summary | empty | 0 |
| whole semantic | semantic / python:semantic-json | complete | JSON/manifest | exact JSON | empty | 0 |
| whole puml | puml / python:plantuml | complete | Puml/manifest | exact Puml | empty | 0 |
| manifest | both / manifest | complete | all | exact manifest | empty | 0 |
| whole no-Python | both / none | not_applicable | manifest | summary | empty | 0 |
| no-Python + explicit path/module/class | both / selected payload | incomplete/payload_unavailable | manifest | unavailable result | one `CSV-PY-006` per target, exact context | 3 |
| zero-class whole | both / none | complete | zero JSON/Puml/manifest | summary | empty | 0 |
| zero-class + missing class target | both / selected payload | incomplete/payload_unavailable | manifest | unavailable result | `CSV-PY-006` | 3 |
| partial safe | both / selected payload | incomplete/partial_safe | all | exact payload | parse + exact target-independent diagnostics | 3 |
| failed seed | both / selected payload | incomplete/payload_unavailable | manifest | unavailable result | file/collision + target diagnostics | 3 |
| entity 501 | both / none | incomplete/payload_unavailable | manifest | summary | one budget diagnostic | 3 |
| normalization collision | both / none | incomplete/payload_unavailable | manifest | summary/result | one group diagnostic | 3 |
| valid unborn fixture | both / none | complete | JSON/Puml/manifest with `head_commit:null` | summary | empty | 0 |
| existing-ref corrupt or invalid detached HEAD | n/a / none | fatal | none | summary | one `CSV-REPO-002`, null context | 1 |
| non-UTF-8 Git path | both / none or manifest | fatal | none | summary/result | one `CSV-SOURCE-003`, all context null | 1 |
| invalid selector/config/option | n/a | usage | none | empty | exactly one selected usage/config diagnostic | 2 |
| malicious quoted unknown config key | n/a | usage/config | none | empty | constant `CSV-CONFIG-003`, all context null, key sentinel absent | 2 |
| output exists/inside repo | n/a / none | fatal | none | summary | exactly one output diagnostic | 1 |
| drift | n/a / manifest | fatal | none | unavailable result | one source drift diagnostic | 1 |
| handled SIGINT pre-rename | n/a / none or manifest | interrupted | none | summary/result | one interrupt diagnostic | 130 |

budget testはgenerated 500/501/600 classを使用する。snapshot/no diff testはtrue unborn HEAD + 1,001 non-Python changesでnormal snapshotが進み、diff-only optionだけがpre-source exit2になることをspyで確認する。

diagnostic goldenは各codeのexact count、domain/path/symbol/line、dedupe/orderをassertする。unknown key goldenはkey bytesを一切含まないconstant messageである。targeted depth-only caseの`stderr.jsonl`はzero bytesである。

acceptance subprocessが生成したsemantic/manifest/summary/result/diagnostic JSONはtest processがcapture後にdev-only Schema helperへ渡す。installed runtime側のschema open/import/call countは0でなければならない。

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

1. `EntityBudgetGate`とoutcome constructors。whole-only NotApplicable predicateを再assertする。
2. artifact descriptorsとmanifest builder/run fingerprint。
3. `OutputTransaction` stage/typed invariant/closed serializer invariant/redaction/fsync/rename/cleanup。JSON Schema validationは行わない。
4. `StderrEmitter` JSONL。Designのcardinality/context済みdiagnostic value以外を発明しない。
5. `StdoutEmitter` summary/result/exact file copy。
6. `SnapshotApplication` lifecycle接続。HEAD/non-UTF-8 fatalはdomain/manifest pathへ入れない。
7. SIGINT cancellation checkpoint。
8. installed CLI subprocess acceptance。

- no selector summaryはpublication後のcommitted outcome、またはrun fatal/interrupted outcomeから作る。
- available selectorはfinal output fileをbinary readし、そのbytesを`sys.stdout.buffer`へwriteする。
- publication後にpayload/manifestをmemory再serializeしてstdoutへ出さない。
- manifest exact bytesをstdoutへ出すcaseでもself descriptorを追加しない。

### target gate

```bash
uv run pytest tests/unit/core/test_budget.py tests/unit/core/test_diagnostics.py tests/unit/artifacts -q
uv run pytest tests/acceptance/python/test_snapshot_cli.py -q
uv run pytest tests/acceptance/python/test_snapshot_failures.py -q
uv run pytest tests/acceptance/python/test_snapshot_budget.py -q
uv run pytest tests/acceptance/python/test_stdout_selector.py -q
uv run pytest tests/integration/source/test_git_repository.py tests/integration/python/test_targeted_snapshot.py -q
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
- targeted absenceをnot_applicable、またはsafe target subsetへ縮退する必要がある。
- non-UTF-8 pathをmanifestへ表現するためsynthetic path fieldが必要になる。
- partial_safeとpayload_unavailableを同じpublicationへ潰す必要がある。
- entity overrunをtruncateしないと処理できない。
- diagnostic count/contextをtestごとに任意変更しないとgreenにできない。
- runtime schema validator/loaderまたはwheelへの`jsonschema` dependencyを追加しないとgreenにできない。

## I01-PLAN-006 — security / determinism / packaging / CI / scope

### RED

追加:

- `tests/security/test_python_static_boundary.py`
- `tests/acceptance/python/test_snapshot_determinism.py`
- `tests/packaging/test_distribution.py`
- `tests/contracts/test_scope_exclusions.py`
- fixture `security`、`unborn_many_changes`、`canonical_model`、`annotation_references`、`module_only`、runtime invalid-HEAD/non-UTF-8/outside-symlink/malicious-config helper
- `THIRD_PARTY_LICENSES.md`
- `ci/latest-python.txt`
- `ci/toolchains/git-2.39.5.Dockerfile`
- `ci/toolchains/git-2.39.5.sha256`

security assertions:

- monkeypatch/spyで`importlib`, `py_compile`, `compileall`, `exec`, `eval`, `runpy`, target subprocess、entry point/plugin loadingへ到達しない。production sourceのstatic scanで直接`compile(...)` callが0件であることを確認し、parser spyで`ast.parse(..., feature_version=(3, 12))`だけがAST生成経路であることを確認する。
- fixture top-level marker fileが作られない。
- Git command logがDesign allowlistだけ。valid commit/unborn/invalid refname/existing corrupt ref/detached failureごとに必要commandだけを実行し、`check-ref-format`を省略せず、stderr text classificationをしない。
- HEAD、refs、index、status、tracked/untracked bytesがtool実行前後で同じ。outputはrepo外。
- payload、manifest、stdout、stderr、PlantUML、captured logにsecret sentinel、source statement、comment、default literal、malicious unknown config key `/tmp/secret`、repo absolute path、temp path、tracebackがない。`CSV-CONFIG-003`はconstant bytesだけ。
- unsafe pathはsuccessへ変換されない。non-UTF-8 raw pathはSourceView/manifest/synthetic pathなしのfatal、NFC collisionは`CSV-SOURCE-004` payload_unavailable。
- PlantUML escape table後のbytesだけが出力され、raw quote/backslash/control/format/line separator/directive injectionが0件。classless module aliasは全てpackage phaseで一回宣言され、module import lineにundeclared aliasがない。

determinism assertions:

- separate nonexistent output dirsへ同一requestを2回実行し、relative file set、各bytes、stdout/stderr、exitが同じ。
- file creation order、filesystem/AST collector iteration order、CLI target/format orderの意味的同値caseでcanonical outputが同じ。member/relation winner、TypeReference resolution/target.name、diagnostic cardinality/context、classless module alias/layout、visual relation representativeを個別assertする。
- Python 3.12/3.14 laneでchecked-in whole/targeted goldenが同じ。

scope assertions:

- CLI help/schemaに`diff`, `sqlalchemy`, `next`, `html` command/formatが登録されていない。ただしusage rejection code/test stringとdocsのout-of-scope記述はallowlistする。
- production imports/dependenciesにSQLAlchemy、Node bridge、HTML renderer、`pyclassuml`、`tree-git-diff`がない。
- `src/code_structure_viz`に`diff`/SQLAlchemy/Next implementation packageを作っていない。

### GREEN hardening/package/CI

- no runtime dependenciesをwheel metadataでassertする。production import graphに`jsonschema`、schema loader、validator portがなく、wheel memberにroot `schemas/`またはpackage schema resourceが0件で、fresh venvのinstalled wheelからSchema fileを参照しなくてもCLIが成功することをspy/isolated filesystemでassertする。sdistはroot `schemas/`をcontract artifactとして含めてよいがruntime codeから参照しない。
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
| whole | golden | golden | golden | summary/exact variants | empty | 0 | complete |
| canonical_model | exact sort/dedupe/type golden | parameter/escape/visual-dedupe golden | golden | summary/exact | exact code/context golden | 0 | complete |
| annotation_references | exact target resolution/name/exclusion golden | internal relation only golden | golden | summary/exact | unknown only exact warning | 0 | complete |
| module_only targeted | zero entity/member + one module import relation | two declared classless packages + one import line | golden | summary/exact | empty | 0 | complete |
| targeted depth-only | golden | golden | golden | summary | **empty** | 0 | complete + frontier only |
| zero_class whole | golden empty entities | golden note | golden | summary | empty | 0 | complete |
| not_applicable whole | none | none | golden | summary/result/manifest | empty | 0 | not_applicable |
| explicit target + no Python | none | none | golden | result/summary | one target diagnostic each | 3 | payload_unavailable |
| explicit missing class + zero_class | none | none | golden | result/summary | target diagnostic | 3 | payload_unavailable |
| partial_safe | golden safe subset | golden incomplete note | golden | exact/summary | parse diagnostic exact context | 3 | partial_safe |
| failed_seed | none | none | golden | result/summary | file/collision + target diagnostic | 3 | payload_unavailable |
| module_collision nonseed/seed | golden safe subset or none | golden or none | golden | summary/result | one group + optional target diagnostic | 3 | partial_safe / payload_unavailable |
| class_collision whole/seed | golden safe subset or none | golden or none | golden | summary/result | one identity group + optional target diagnostic | 3 | partial_safe / payload_unavailable |
| unsafe symlink | none | none | golden | result/summary | one source diagnostic per path | 3 | payload_unavailable |
| normalization collision | none | none | golden | result/summary | one `CSV-SOURCE-004` group diagnostic | 3 | payload_unavailable |
| entity501 | none | none | golden | result/summary | one budget diagnostic | 3 | payload_unavailable |
| true unborn fixture | golden | golden | golden with `head_commit:null` | summary | empty | 0 | complete valid source state |
| invalid HEAD | none | none | none | summary/result | one `CSV-REPO-002`, null context | 1 | fatal |
| non-UTF-8 Git path | none | none | none | summary/result | one `CSV-SOURCE-003`, null context | 1 | fatal |
| drift/output collision | none | none | none | summary/result | one run diagnostic | 1 | fatal |
| usage/config/diff option | none | none | none | empty | exactly one selected usage/config diagnostic | 2 | usage |
| malicious unknown config key | none | none | none | empty | constant `CSV-CONFIG-003`, key absent | 2 | usage/config |
| interrupt | none | none | none | summary/result | one interrupt diagnostic | 130 | interrupted |

published-files goldenはlexical relative path一行一file、末尾LF。Artifact 0件caseはzero-byte file。exit-code goldenはdecimal一行、末尾LF。diagnostic goldenはline countと全nullable context fieldをbyte equalityで検証する。

## issue gate commands

C6後、次をrepository rootのclean checkoutで順に実行する。

```bash
uv sync --frozen --all-groups
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
uv run pytest tests/unit -q
uv run pytest tests/integration/source/test_git_repository.py -q
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
| I01-REQ-004 | I01-DES-004 | I01-PLAN-003, I01-PLAN-004 | I01-AC-001, I01-AC-002, I01-AC-005 | I01-AT-001, I01-AT-002, I01-AT-005 |
| I01-REQ-005 | I01-DES-005 | I01-PLAN-001, I01-PLAN-004, I01-PLAN-005 | I01-AC-001, I01-AC-007, I01-AC-009 | I01-AT-001, I01-AT-007, I01-AT-009 |
| I01-REQ-006 | I01-DES-006, I01-DES-007 | I01-PLAN-002, I01-PLAN-003, I01-PLAN-005, I01-PLAN-006 | I01-AC-003, I01-AC-004, I01-AC-005, I01-AC-006 | I01-AT-003, I01-AT-004, I01-AT-005, I01-AT-006 |
| I01-REQ-007 | I01-DES-008, I01-DES-009 | I01-PLAN-001, I01-PLAN-004, I01-PLAN-005, I01-PLAN-006 | I01-AC-008, I01-AC-009 | I01-AT-008, I01-AT-009 |

### independent Red P1 closure trace

| closure | canonical decision | Plan boundary | fixture/golden | acceptance/test |
| --- | --- | --- | --- | --- |
| P1-01 explicit target absence | not_applicableはwhole target0/source0だけ。targeted unresolvedはpayload_unavailable | C3/C5 | `target_absence-no-python`, `target_absence-zero-class` | AC-002/003, AT-002/003 |
| P1-02 unborn HEAD | rev-parse/symbolic-ref/check-ref-format/show-ref return matrix。invalid refname/existing corrupt/detached failureはfatal | C2/C5 | `unborn_many_changes`, runtime `invalid_head` | AC-003, AT-003 |
| P1-03 non-UTF-8 path | SourceView前run fatal、path context null、Artifact 0 | C2/C5/C6 | runtime `non_utf8_path` fatal golden | AC-003/004, AT-003/004 |
| P1-04 semantic canonicalization | exact member/relation sort tuple、occurrence winner、closed type grammar | C3/C4/C6 | `canonical_model` JSON golden | AC-001/005, AT-001/005 |
| P1-05 diagnostics/depth | code別cardinality/context、depth_limitはfrontier-only/empty stderr | C1/C3/C5 | `diagnostics`, `targeted/stderr.jsonl` | AC-002/007, AT-002/007 |
| P1-06 PlantUML bytes | parameter token grammar、escape table、visual-line dedupe | C4/C6 | `canonical_model` PlantUML golden | AC-001/004/005, AT-001/004/005 |

### independent Red v2 P1 closure trace

| closure | canonical decision | Plan boundary | fixture/golden | acceptance/test |
| --- | --- | --- | --- | --- |
| V2-P1-01 annotation TypeReference | closed extraction/adoption table、lexical/import/absolute/unknown priority、exact target.name、builtin/typing/type-parameter exclusion | C3/C4/C6 | `annotation_references` semantic/PlantUML/diagnostic golden | AC-001/002/005, AT-001/002/005 |
| V2-P1-02 classless module PlantUML | every selected module declares package alias、classless module gets deterministic note、all packages precede module import relation | C3/C4/C5/C6 | `module_only` semantic/PlantUML/manifest golden | AC-001/002/005, AT-001/002/005 |
| V2-P1-03 schema validation boundary | JSON Schema is test/build-time only; runtime uses typed/closed invariants and has validator/schema-loader/runtime dependency 0 | C1/C4/C5/C6 | schema positive/negative vectors + captured CLI JSON + offline wheel | AC-008/009, AT-008/009 |
| V2-P1-04 unknown config key redaction | `CSV-CONFIG-003` constant message、all context null、raw/normalized unknown key absent from every channel | C1/C5/C6 | `unknown_config_key/stderr.jsonl` | AC-004/007/009, AT-004/007/009 |

trace gap、orphan Requirement/Design/Plan/Test、同じIDの意味違い、上記10件のP1 closureのfixture/golden欠落をcontract testまたはreviewで拒否する。

## regression boundary

- target repositoryのHEAD、refs、index、status、tracked/untracked bytesをtoolが変更しない。
- output dirはrepo外、destination absent、one directory rename。rerun to same outputはcollision fatalで既存bytes不変。
- same-input byte equality、format/target canonicalization、member/relation occurrence winner、TypeReference extraction/resolution/exclusion/target.name、type grammar、diagnostic cardinality/context/order、classless module package alias/layout、PlantUML parameter/escape/visual dedupeを維持する。
- no-Python wholeだけをnot_applicableとし、explicit target + no-Python/zero-classをpayload_unavailableにする。partial_safe/payload_unavailableをempty successへ潰さない。
- entity 501をtruncateせず、changed-path 1,001やimplicit base absenceをsnapshot failureにしない。
- selector invalid時はsource/Git/staging spy call 0件。
- source body/comment/literal/secret/absolute/temp path/traceback/raw exception/Git stderr/non-UTF-8 raw bytes/surrogate・replacement・hash synthetic pathを全channelへ出さない。
- visual semanticsはarrow/text/legendで区別し、colorだけに依存しない。
- package runtime dependency 0、runtime schema validator/loader 0、Node/DB/HTML/legacy dependency 0。unknown config key raw bytesは全channel 0。
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
- source execution、Git write、unborn/corrupt HEAD誤分類、non-UTF-8 pathのsynthetic identity、secret/path leak、truncation、overwrite、partial publication、canonical bytesのnondeterminismを観測する。
- runtime dependency、runtime schema validator/loader、diff、SQLAlchemy、Next、HTML、release publishが必要になる。
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
