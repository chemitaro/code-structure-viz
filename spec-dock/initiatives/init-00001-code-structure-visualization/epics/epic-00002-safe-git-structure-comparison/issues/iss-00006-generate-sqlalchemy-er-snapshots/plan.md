---
種別: 実装計画書（Issue）
ID: "iss-00006"
タイトル: "Generate SQLAlchemy ER Snapshots"
関連GitHub: ["#6"]
package_sequence_key: "ISSUE-03"
状態: "draft"
最終更新: "2026-08-29"
依存: ["requirement.md", "design.md"]
親: ["epic-00002", "init-00001"]
---

# iss-00006 Generate SQLAlchemy ER Snapshots — 実装計画

詳細: [Issue Plan Guide](../../../../../../docs/authoring/issue-plan.md)

## Planning Level

- **selected level: `strict`**
- 理由: untrusted sourceを扱うstatic analyzer、public CLI/schema、privacy-sensitive redaction、hardened atomic writer、Issue 7が消費するstable identityを同時に変更するためである。
- risk factor: target execution、DB access、secret/literal leak、false success、Python public regression、cross-domain schema混線、partial publication、offline package regression。
- `critical`ではない理由: target repository/dataを変更せず、public release前にIssue単位でrevertできる。
- `critical`再評価条件: source execution、secret/PII incident、target mutation、不可逆publication、data loss、incident responseを要するrolloutを追加または観測した場合。

## 目標

一人のGPT-5.6 Luna Max coderが、Requirement/DesignにないProduct、Policy、Security、schema、CLI、identity、failure classification、acceptance判断を補完せず、次を完成できる状態にする。

```text
existing validated snapshot CLI/config
  -> existing immutable SourceView
  -> closed snapshot domain adapter dispatch
  -> SQLAlchemy static AST analysis + target selection
  -> table budget + typed outcome
  -> canonical SQLAlchemy JSON / closed ER PlantUML
  -> existing manifest / atomic transaction / stdout-stderr-exit
  -> exact Python regression / security / offline package / CI evidence
```

completionはfile作成数やparser単体ではなく、`I03-AC-001`〜`I03-AC-010`、full trace、no-scope-creep、clean verificationで判定する。

## authority / writer boundary

- canonical R/D/Pのadoption、`.meta.json`、`report.md`、accepted ADR、parent/Issue 4/5 canonical文書の編集はmain orchestrator/userのsingle-writer authorityである。
- product coderは本Planに列挙したproduction/test/schema/contract pathだけを変更する。SpecDock canonical fileをimplementation commitへ混在させない。
- current branchに既存未コミット変更がある場合、所有者を解決せずstash/reset/clean/overwriteしない。
- Design外のpublic contractが必要になった場合、code/schema/goldenを先に変更せずstop conditionとして返す。
- 本Planは将来の実行手順であり、未実施のRED/GREEN、commit、test、CI結果を実施済みと主張しない。実績は完了後のcanonical `report.md`へ別途記録する。

## I03-PLAN-000 — implementation preflight（tracked product/canonical writeなし）

### exact repository / branch / SHA

1. taskが指定したrepository `chemitaro/code-structure-viz`、target branch、full expected SHAをGitHub connectorとlocal checkoutでbyte-for-byte比較する。
2. branch不存在、connector failure、full SHA mismatch、別repositoryの場合はdefault branch、short SHA、attachment、public webへfallbackせず停止する。
3. `git rev-parse --show-toplevel`と`git rev-parse HEAD`を確認し、task authorityと一致しないcheckoutへ変更を書かない。変更前full SHAをshell/session外の安全な作業メモへ`BASELINE_SHA`として記録し、final auditはcurrent HEADではなくこのbaselineとのtree diffを使う。
4. configured upstreamは参考として記録できるが、HEAD authorityへ置き換えずfetchしない。
5. repository rootから`AGENTS.md`を探索し、存在すれば最初に読む。verified baselineではroot `AGENTS.md`はないが実装開始時に再確認する。
6. `git status --short`を確認する。既存変更、untracked fixture、generated outputを自分の変更として扱わない。

### canonical / baseline assertions

```bash
python3 ./spec-dock/scripts/spec-dock validate

: "${EXPECTED_SHA:?strict task expected full SHA is required}"
BASELINE_SHA="$(git rev-parse HEAD)"
test "$BASELINE_SHA" = "$EXPECTED_SHA"

test -f spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00006-generate-sqlalchemy-er-snapshots/requirement.md
test -f spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00006-generate-sqlalchemy-er-snapshots/design.md
test -f spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00006-generate-sqlalchemy-er-snapshots/plan.md

test -f src/code_structure_viz/application/snapshot.py
test -f src/code_structure_viz/artifacts/writer.py
test -f schemas/semantic-v1.schema.json
test -f tests/acceptance/python/test_snapshot_cli.py
test -f tests/acceptance/python/test_diff_cli.py
test ! -e src/code_structure_viz/adapters/sqlalchemy
```

- 最後のabsence assertionがfailした場合、partial implementationの所有者と実装状態を確認し、verified-baselineの`new`分類を黙って`existing`へ読み替えて重ねない。
- Issue 4/5 reportとcurrent testsがgreenでない場合、SQLAlchemy implementationへ進む前にbaseline defectとして分離する。

### toolchain / dependency preflight

```bash
python3 --version
git --version
uv --version
uv sync --frozen --all-groups
uv run pytest -q
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
baseline_dist="$(mktemp -d)"
uv build --offline --out-dir "$baseline_dist"
rm -rf "$baseline_dist"
```

- Python <3.12、Git <2.39、`uv`不在、frozen sync failure、baseline test failureはblockerである。
- P0でdependency追加、Git mutation、target repository executionを行わない。package managerのdevelopment dependency取得はrepository既定workflowに従うが、product runtime/offline buildはnetworkへ接続しない。

## test-first / change protocol

各Plan stepは次の順序で実行する。

1. **Expectation first**: step固有fixture/test/golden expectationを先に追加し、未実装または既存behaviorとの差により狙ったfailureになることを確認する。
2. **Minimal implementation**: Designでverified baselineに対し`existing — modify`または`new — add`と分類したpathだけを変更する。
3. **Refactor under green**: duplicate/invariant/typeを整理するが、public bytesとtest expectationを都合よく同時変更しない。
4. **Focused gate**: step commandを通す。
5. **Python/shared regression**:そのstepが触れたexisting contractのPython regressionを通す。
6. **Scope/security review**: SQLAlchemy import、DB、diff、HTML、Next、all-domain、new config key、dependencyが混入していないことを差分で確認する。
7. **Commit boundary**: repository workflowがcommitを要求する場合だけ、greenなlogical stepを一commitにする。red-only、empty attestation、`--no-verify`、force push、unrelated amendを行わない。

RED/GREEN履歴は実行時に観測するものであり、本Planの記述自体を実施証拠にしない。

## 実装順序

| order | Plan ID | causal outcome | Requirement / Design trace |
| --- | --- | --- | --- |
| 0 | I03-PLAN-000 | exact preflight、authority、green baseline | all |
| 1 | I03-PLAN-001 | acceptance fixtures、golden/schema expectations、failure/publication matrixを先に固定 | I03-REQ-001〜010 / I03-DES-010, 012 |
| 2 | I03-PLAN-002 | domain-aware snapshot port、CLI/outcome/budget/diagnostic、Python exact compatibility | I03-REQ-001, 002, 007, 009 / I03-DES-001, 002, 008, 011 |
| 3 | I03-PLAN-003 | shared Python source index、SQLAlchemy immutable model、static analyzer | I03-REQ-003〜006, 008 / I03-DES-003, 004, 005, 007 |
| 4 | I03-PLAN-004 | target selection、applicability、partial/payload unavailable、table budget | I03-REQ-002, 003, 005, 007, 008 / I03-DES-006, 008 |
| 5 | I03-PLAN-005 | canonical SQLAlchemy semantic JSON、closed PlantUML、schemas/contracts | I03-REQ-004〜006, 008, 009 / I03-DES-005, 007, 009 |
| 6 | I03-PLAN-006 | SnapshotApplication、manifest、writer、streamsへのend-to-end接続 | I03-REQ-001, 006, 007, 009 / I03-DES-001, 008, 009, 011 |
| 7 | I03-PLAN-007 | security/redaction、offline package、scope docs、full regressions | I03-REQ-008〜010 / I03-DES-010, 012 |
| 8 | I03-PLAN-008 | final quality gate、trace、handoff、clean status | all |

実装順は固定する。特にshared portを入れる前にSQLAlchemy専用second application/writerを作らず、renderer/publicationをsemantic model確定前に実装しない。

## I03-PLAN-001 — acceptance-first contract and fixtures

### prerequisite

- P0 green。
- replacement Requirement/Designがadopt済みで、current Issue 6 `.meta.json`を変更していない。

### owned paths

**new**:

```text
tests/helpers/sqlalchemy_snapshot.py
tests/fixtures/sqlalchemy_snapshot/
tests/golden/sqlalchemy_snapshot/
tests/acceptance/sqlalchemy/__init__.py
tests/acceptance/sqlalchemy/test_snapshot_cli.py
tests/acceptance/sqlalchemy/test_snapshot_targets.py
tests/acceptance/sqlalchemy/test_snapshot_failures.py
tests/acceptance/sqlalchemy/test_snapshot_determinism.py
tests/acceptance/sqlalchemy/test_snapshot_budget.py
tests/acceptance/sqlalchemy/test_stdout_selector.py
tests/integration/sqlalchemy/__init__.py
tests/integration/sqlalchemy/test_er_semantics.py
tests/security/test_sqlalchemy_static_boundary.py
tests/contracts/test_sqlalchemy_goldens.py
```

**existing — modify only for test registration/schema expectation**:

```text
tests/contracts/test_json_schemas.py
tests/contracts/test_scope_exclusions.py
tests/packaging/test_distribution.py
```

### expectation-first cases

1. modern DeclarativeBase + Mapped/mapped_column complete default-both run。
2. classic `declarative_base` + `Column`、module-level `Table`、exact `__table__` link。
3. column/PK/unique/check/index/FK/relationship/inheritance/secondary association row/relation kinds。
4. path/module/class target、multi-target union、up/down depth/frontier、missing/ambiguous target。
5. safe abstract/base-only SQLAlchemy evidence、table 0のcomplete empty payloadと、safe Python-only repoのnot_applicableを別caseで固定する。
6. safe table + parse/dynamic/table collision partial_safeと、ordinary non-lossy exact duplicateが`complete`のままrow exactly 1件へcanonicalizeされるcontrol case。
7. `lossy_expression_identity_conflict`: one safe table/column、same-category unnamed check 2件、same ordered expression-category termsのunnamed index 2件。expectedは`incomplete / partial_safe`、exit 3、payload + manifest、`CSV-SA-009` exactly 4件、final member count 1、check/index row count各0。同一AST occurrenceのmulti-pass rediscoveryは追加row/diagnostic 0。
8. safe tableなし + failed/dynamic evidence、explicit target miss payload_unavailable。
9. 500/501 tables、valid 600 override、invalid zero/non-integer、snapshot diff-only option rejection。
10. stdout no-selector/exact manifest/exact semantic/exact PlantUML/not_applicable/payload unavailable/fatal/interrupt/invalid duplicate。
11. `type_parameter_redaction`: other redacted boundaryなしで`String(255)`と`Numeric(10, 2, asdecimal=True)`を使い、各constructor count 1、run count 2、JSON/PlantUML/manifestのrule/count equality、column `type_parameters=[redacted:literal]` exactly once。
12. `plantuml_escape_collision`: user label `" -> _U0022_`、literal user label `_U0022_ -> _U005F_U0022_U005F_`をgolden/securityでdistinctに固定する。
13. secret-like defaults、URL、check/join body、source comment、absolute temporary pathが全channelに存在しない。
14. same-input rerunとdeclaration/import/enumeration order variants。
15. SQLAlchemy未installのoffline wheel source。

fixture sourceは実行されるとsentinel file作成またはexceptionを起こすようにしてよいが、expected resultはsentinel未発火である。

### expected initial failure

- `--domain sqlalchemy` usage error、module不存在、schema invalid、golden不存在のいずれかでfailする。
- testをskip/xfailせず、false successをexpectedにしない。
- red-only stateをcommitしない。次step以降と同じlogical change内でgreenへ戻す。

### focused command

```bash
uv run pytest tests/acceptance/sqlalchemy/test_snapshot_cli.py \
  tests/acceptance/sqlalchemy/test_snapshot_targets.py \
  tests/acceptance/sqlalchemy/test_snapshot_failures.py \
  tests/contracts/test_json_schemas.py \
  tests/contracts/test_sqlalchemy_goldens.py -q
```

### stop conditions

- existing helperではactual subprocess/stdout/stderr/published bytesを観測できず、大規模test harness rewriteが必要。
- Requirementのfield/order/statusをfixture作者が追加判断しなければexpectedを作れない。
- SQLAlchemy package installがfixture作成に必要。

## I03-PLAN-002 — shared snapshot port, CLI, outcomes, diagnostics

### prerequisite

- I03-PLAN-001 expectationsが狙った理由でfailしている。
- Python baseline goldensを保存し、shared refactor前後のexact comparisonが可能。

### owned paths

**new**:

```text
src/code_structure_viz/core/domains.py
src/code_structure_viz/application/snapshot_domain.py
src/code_structure_viz/adapters/python/snapshot_adapter.py
```

**existing — modify**:

```text
src/code_structure_viz/cli/parser.py
src/code_structure_viz/cli/main.py
src/code_structure_viz/application/snapshot.py
src/code_structure_viz/application/diff.py
src/code_structure_viz/core/outcomes.py
src/code_structure_viz/core/budget.py
src/code_structure_viz/core/diagnostics.py
tests/unit/cli/test_parser.py
tests/unit/core/test_outcomes.py
tests/unit/core/test_budget.py
tests/unit/core/test_diagnostics.py
```

### expectation first

- `SnapshotCliRequest.domain` accepts exact `python|sqlalchemy`; diff remains Python-only。
- existing TargetSpec validates SQLAlchemy targets without directory grammar extension。
- SQLAlchemy selector accepted only for selected SQLAlchemy/requested format。
- `DomainOutcome.domain` required; impossible mismatches rejected。
- EntityBudgetGate returns domain-specific code。
- SA diagnostic context table rejects raw/invalid context。
- Python adapter through new port returns exact existing payload/manifest/stdout bytes。

### implementation

1. `core/domains.py`へDesign exact closed domain vocabularyを追加し、`application/snapshot_domain.py`へDesign exact `SnapshotAdapterContract`、`SnapshotAnalysis`、`SnapshotDomainAdapter`、`snapshot_adapter_for`を追加する。
2. existing Python analyzer/selector/renderersを`PythonSnapshotDomainAdapter`へwrapする。logicやoutput DTOをforkしない。
3. `SnapshotApplication`へclosed adapter factoryを追加するが、SQLAlchemy adapterが未実装の間はtyped internal/unavailableを偽装せずtest boundary内で段階的に接続する。
4. parser domain、selector compatibility、helpをadditiveに更新する。diff parserはSQLAlchemyを拒否する。
5. `DomainOutcome` factory全call siteへ`domain="python"`を明示する。`application/diff.py`はこのinternal argument追加だけに限定し、Python diff goldensでbytes/status/Git behaviorを固定する。shared summary/manifest testsを更新する。
6. SA diagnostic enum/spec/contextとbudget mappingを追加する。

### focused gate

```bash
uv run pytest tests/unit/cli/test_parser.py \
  tests/unit/core/test_outcomes.py \
  tests/unit/core/test_budget.py \
  tests/unit/core/test_diagnostics.py -q

uv run pytest tests/acceptance/python/test_snapshot_cli.py \
  tests/acceptance/python/test_stdout_selector.py \
  tests/contracts/test_python_goldens.py -q

uv run mypy src tests
```

### stop conditions

- Python snapshot exact bytes/path/statusが変わる。
- public plugin registry、domain `all`、new commandが必要になる。
- `DomainOutcome`へSQLAlchemy-owned fieldを追加する必要がある。
- parserがnew SQLAlchemy-specific target syntaxを必要とする。

## I03-PLAN-003 — PythonSourceIndex, SQLAlchemy model, static analyzer

### prerequisite

- I03-PLAN-002 shared port/CLI/core tests green。
- SQLAlchemy test fixture sourceはproduct runtime dependencyなしでreadできる。

### owned paths

**new**:

```text
src/code_structure_viz/source/python_modules.py
src/code_structure_viz/adapters/sqlalchemy/__init__.py
src/code_structure_viz/adapters/sqlalchemy/model.py
src/code_structure_viz/adapters/sqlalchemy/analyzer.py
src/code_structure_viz/adapters/sqlalchemy/snapshot_adapter.py
tests/unit/sqlalchemy/__init__.py
tests/unit/sqlalchemy/test_model.py
tests/unit/sqlalchemy/test_analyzer.py
```

**existing — modify**:

```text
src/code_structure_viz/adapters/python/module_index.py
```

### expectation first

- existing Python module mapping/collision/failure diagnostics/order/candidate count exact regression。
- SQLAlchemy import alias、relative import、cross-module Base、classic base、rebind/star ambiguity。
- table/schema identity、exact `__table__` merge、unrelated collision。
- modern/classic/Table columns、constraint/index/FK/relationship/inheritance/association。
- raw default/check/join/URL sentinelがmodel field/repr/diagnosticに存在しない。
- ID preimage、closed enum、sort、ordinary non-lossy dedupe、lossy unnamed check/index occurrence conflict invariant。
- `lossy_expression_identity_conflict`のstatus/exit、`CSV-SA-009` 4件、member/check/index exact countとsame-occurrence rediscovery control。
- parse/source failureによるapplicabilityとcoverage count。

### implementation

1. current module path algorithmを`PythonSourceIndex`へ移し、filesystem/Git/diagnostic emissionを持たないlanguage valueにする。
2. `PythonModuleIndex.build`をwrapper化し、existing DTO/diagnostic/orderを同じに保つ。
3. SQLAlchemy model enums/dataclasses、ID factory、sort key、redaction DTO、coverage DTOを実装する。
4. analyzerをDesignの8 passで実装する。direct static AST patternだけを認識し、`ast.literal_eval`/unparse/source segmentを使わない。
5. source/index/parse failureを`CSV-SA-001`〜`005`へmapする。
6. row canonicalizerをnon-lossyとlossyへ分ける。lossyはunnamed checkとexpression termを含むunnamed indexだけとし、same occurrence key + same payloadだけをdedupe、distinct occurrence groupはpayload一致でも全除外する。
7. declarative/table/row/relation unknown/collisionを`CSV-SA-006`〜`010`へmapし、lossy conflictは各distinct occurrenceへ`CSV-SA-009` exactly oneを出してsafe subsetを保持する。
8. `SqlAlchemySnapshotDomainAdapter.analyze`はこのstepではwhole-mode analysis resultまで接続し、render/publicationは後stepへ残す。

### focused gate

```bash
uv run pytest tests/unit/sqlalchemy/test_model.py \
  tests/unit/sqlalchemy/test_analyzer.py \
  tests/integration/sqlalchemy/test_er_semantics.py -q

uv run pytest tests/unit/python/test_module_index.py \
  tests/unit/python/test_analyzer.py \
  tests/acceptance/python/test_snapshot_cli.py \
  tests/contracts/test_python_goldens.py -q

uv run ruff check src/code_structure_viz/source/python_modules.py \
  src/code_structure_viz/adapters/sqlalchemy \
  src/code_structure_viz/adapters/python/module_index.py
uv run mypy src tests
```

`tests/unit/python/test_module_index.py`はverified commitに存在するexisting pathであり、同fileをPythonSourceIndex extractionのexact regression gateとして使用する。

### stop conditions

- runtime SQLAlchemy import、target module import、DB connectionが必要。
- schema/table identityをmodule/pathでdisambiguateしなければcompleteにできない。
- arbitrary expression evaluationまたはsource text retentionが必要。
- PythonSourceIndex extractionでexisting Python diagnostics/orderが変わる。

## I03-PLAN-004 — target selection, applicability, outcome, budget

### prerequisite

- I03-PLAN-003 whole analysis/model tests green。
- model IDs/sort/redaction shapeがfrozen。

### owned paths

**new**:

```text
src/code_structure_viz/adapters/sqlalchemy/selection.py
tests/unit/sqlalchemy/test_selection.py
```

**new at verified baseline — continue modifying after I03-PLAN-001/003**:

```text
src/code_structure_viz/adapters/sqlalchemy/snapshot_adapter.py
tests/acceptance/sqlalchemy/test_snapshot_targets.py
tests/acceptance/sqlalchemy/test_snapshot_failures.py
tests/acceptance/sqlalchemy/test_snapshot_budget.py
```

### expectation first

- whole mode、path/module/class target、multiple target union。
- same module/unique simple class/ambiguous class resolution。
- up/down separate BFS、depth 0/1/2、frontier、no synthetic table。
- no evidence+no failure=not_applicable。safe supported base evidence+table 0+failure/unknown 0=complete empty payload。
- safe table+failure=partial_safe、safe tableなし+failure/unknown=payload_unavailable。
- explicit missing/ambiguous targetはpayload_unavailableでwhole fallbackなし。
- 500 admitted、501 denied、600 override admitted、selected table countがbudget actualと一致。

### implementation

1. `SqlAlchemyTargetSelector`へexact TargetSpec resolutionとgraph selectionを実装する。
2. selectorはfull safe snapshotを入力にし、source/Git/ASTを再読しない。
3. relation graphはinternal FK/relationship/inheritance/associationだけ。BFSはrequested depthとtable setで有限化する。
4. coverage selected modules/entities/frontierをselection resultへ反映する。
5. adapterが`SnapshotAnalysis`のstatus/incomplete_kind/payload/entity_countを一意に構築する。
6. common application budget gateへselected table countを渡す。selector/analyzerはtruncateしない。

### focused gate

```bash
uv run pytest tests/unit/sqlalchemy/test_selection.py \
  tests/acceptance/sqlalchemy/test_snapshot_targets.py \
  tests/acceptance/sqlalchemy/test_snapshot_failures.py \
  tests/acceptance/sqlalchemy/test_snapshot_budget.py -q

uv run pytest tests/unit/core/test_budget.py tests/unit/core/test_outcomes.py -q
```

### stop conditions

- directory/glob/table-name targetなどDesign外grammarが必要。
- runtime relationship graphまたはDB FK resolutionが必要。
- depthをbudget truncationとして使う必要。
- target failureをnot_applicableへ変換しなければtestを通せない。

## I03-PLAN-005 — semantic JSON, PlantUML, schemas, contracts

### prerequisite

- selected immutable snapshotとstatus/coverageがgreen。
- ID/order/redaction shapeを変更しない。

### owned paths

**new**:

```text
src/code_structure_viz/adapters/sqlalchemy/semantic_json.py
src/code_structure_viz/adapters/sqlalchemy/plantuml.py
docs/contracts/sqlalchemy-semantic-v1.md
docs/contracts/sqlalchemy-plantuml-v1.md
tests/unit/sqlalchemy/test_semantic_json.py
tests/unit/sqlalchemy/test_plantuml.py
tests/contracts/test_sqlalchemy_goldens.py
tests/golden/sqlalchemy_snapshot/
```

**existing — modify**:

```text
schemas/diagnostic-v1.schema.json
schemas/semantic-v1.schema.json
schemas/run-manifest-v1.schema.json
schemas/run-summary-v1.schema.json
schemas/stdout-result-v1.schema.json
tests/contracts/test_json_schemas.py
```

### expectation first

- exact field order、final LF、no BOM、closed additionalProperties。
- complete/partial_safe SQLAlchemy semantic document、not_applicable/payload unavailable document不存在。
- each row-kind schema oneOfとcross-kind field rejection。
- SQLAlchemy snapshot only; SQLAlchemy diff invalid。
- exact PlantUML skeleton、table alias hex、row/edge/legend、external/unknown no synthetic node。
- every column lineの`type_parameters=<token|->` exactly once。`String(255)`とmulti-argument type constructorを各一件だけcountする。
- `legend right`直後のexact rule/count metadata linesとJSON/manifest coverageとのequality。
- quote/backslash/control/injection-like identifier escaping、および`"`/`_U0022_` collision pairのinjective output。
- default/check/join/source/path sentinel absence。
- existing Python semantic/diff goldens continue valid and exact。

### implementation

1. semantic rendererはmodelのalready-sorted tupleをclosed DTOへ変換し、再解析/dedupeしない。
2. PlantUML rendererはDesign skeletonとclosed line vocabularyだけを生成し、column `type_parameters`、legend先頭のrule/count metadataを`SqlAlchemySnapshot.coverage.redaction`から出す。
3. `escape_plantuml_label`のpassthroughからunderscoreを除き、input `_`を`_U005F_`へencodeする。renderer-owned syntaxはescape functionへ渡さない。
4. semantic schema rootをclosed Python existing branch + SQLAlchemy snapshot branchへ再構成する。Python branchのrequired/const/additionalPropertiesをcopyではなくexact testで保護する。
5. diagnostic/manifest/summary/stdout schemaへSQLAlchemy closed variantsを追加する。
6. SQLAlchemy semantic/PlantUML contract docsへfield、ID preimage、sort、lossy dedupe、escaping、redaction metadata placementを記録する。
7. goldensはactual renderer bytesからreviewして固定し、schemaをgoldenに合わせてpermissiveにしない。

### focused gate

```bash
uv run pytest tests/unit/sqlalchemy/test_semantic_json.py \
  tests/unit/sqlalchemy/test_plantuml.py \
  tests/contracts/test_json_schemas.py \
  tests/contracts/test_sqlalchemy_goldens.py \
  tests/contracts/test_python_goldens.py -q
```

### stop conditions

- free-form metadata/raw AST/source fieldが必要。
- PlantUML validatorをarbitrary text許可へ緩和する必要。
- Python schema/goldenを変更しなければSQLAlchemy branchを追加できない。
- raw literalをID、label、diagnosticへ入れなければ意味を表せない。

## I03-PLAN-006 — application, manifest, writer, streams integration

### prerequisite

- analyzer/selector/renderers/schema単体がgreen。
- exact artifact filenames/media typesがfrozen。

### owned paths

**existing at verified baseline — modify**:

```text
src/code_structure_viz/application/snapshot.py
src/code_structure_viz/artifacts/manifest.py
src/code_structure_viz/artifacts/writer.py
src/code_structure_viz/artifacts/streams.py
src/code_structure_viz/cli/main.py
tests/unit/artifacts/test_manifest.py
tests/unit/artifacts/test_writer.py
tests/unit/artifacts/test_streams.py
```

**new at verified baseline — continue modifying after earlier steps**:

```text
src/code_structure_viz/adapters/sqlalchemy/snapshot_adapter.py
src/code_structure_viz/adapters/python/snapshot_adapter.py
tests/acceptance/sqlalchemy/test_snapshot_cli.py
tests/acceptance/sqlalchemy/test_stdout_selector.py
```

### expectation first

- default both/one format complete paths/descriptors/SHA。
- not_applicable/payload_unavailable manifest-only、partial_safe payload+manifest。
- output path exists/inside repo/symlink/private path/invalid Puml/collision/interrupt/drift no-publication。SQLAlchemy Pumlはmetadata欠落/重複/順序違い/rule違い/non-canonical count/column `type_parameters`欠落をinvalidとする。
- manifest adapter/domain/contracts/request/coverage/budget/artifact cross-check。semantic JSON、PlantUML、manifestはsame immutable redaction summaryを参照する。
- SQLAlchemy summary、exact domain bytes、manifest bytes、unavailable result、usage stdout empty。
- Python snapshot and diff exact full artifacts unchanged。

### implementation

1. `SnapshotApplication.run`をDesign lifecycleへgeneric化し、SourceView/transactionを一回だけ作る。
2. `ArtifactDescriptor.create_snapshot`と`OutputTransaction.stage_snapshot_payload`をclosed registryで実装する。
3. writerへSQLAlchemy paths、private path scan、closed PlantUML validatorを追加する。validatorはlegend直後のexact rule/count lines、canonical nonnegative decimal、column `type_parameters` field、allowed escaped label grammarを検証し、existing descriptor/fsync/no-replace flowを変更しない。
4. `RunManifestBuilder`をsnapshot adapter/coverage-awareにし、SQLAlchemy manifest coverageはrendererと同じimmutable redaction summaryをserializeする。Python snapshot exact order/bytesを維持する。`DiffManifestBuilder`は必要なtype adjustment以外変更せず、golden bytesを維持する。
5. stream emitterは`DomainOutcome.domain`とartifact_pathsをcross-checkし、SQLAlchemy paths/resultを処理する。
6. staged bytesをbindしてからcommitするexisting exact stdout mechanismを維持する。

### focused gate

```bash
uv run pytest tests/unit/artifacts/test_manifest.py \
  tests/unit/artifacts/test_writer.py \
  tests/unit/artifacts/test_streams.py \
  tests/acceptance/sqlalchemy/test_snapshot_cli.py \
  tests/acceptance/sqlalchemy/test_stdout_selector.py -q

uv run pytest tests/acceptance/python \
  tests/contracts/test_python_goldens.py \
  tests/security/test_python_static_boundary.py -q
```

### stop conditions

- SQLAlchemy専用OutputTransaction、second SourceView、second manifest commandが必要。
- Python artifact bytes/path/orderingが変わる。
- payload_unavailableにdomain payloadを公開しなければならない。
- writerのclosed path/validator/private path checkを弱める必要。

## I03-PLAN-007 — security, packaging, docs, regression hardening

### prerequisite

- production CLIのSQLAlchemy end-to-end matrixがgreen。
- no open schema/field/identity question。

### owned paths

**existing at verified baseline — modify**:

```text
docs/contracts/cli-v1.md
docs/contracts/config-v1.md
docs/contracts/run-manifest-v1.md
docs/contracts/stdout-v1.md
tests/contracts/test_scope_exclusions.py
tests/packaging/test_distribution.py
```

**new at verified baseline — complete/modify after I03-PLAN-001**:

```text
tests/security/test_sqlalchemy_static_boundary.py
```

**existing — verify unchanged**:

```text
pyproject.toml
uv.lock
THIRD_PARTY_LICENSES.md
.github/workflows/ci.yml
src/code_structure_viz/semantic/diff.py
src/code_structure_viz/source/endpoints.py
src/code_structure_viz/source/freezer.py
src/code_structure_viz/source/file_changes.py
src/code_structure_viz/source/git_repository.py
src/code_structure_viz/source/targets.py
src/code_structure_viz/semantic/canonical_json.py
src/code_structure_viz/adapters/python/analyzer.py
src/code_structure_viz/adapters/python/selection.py
src/code_structure_viz/adapters/python/semantic_json.py
src/code_structure_viz/adapters/python/plantuml.py
```

### expectation first

- source fixture module import、fake SQLAlchemy package import、DB connect、socket/network、build/plugin sentinel未発火。
- Git HEAD/ref/index/status/tracked/untracked bytes不変。
- source/comment/default/server_default/check/join/URL/token/private absolute pathがJSON/Puml/manifest/stdout/stderr/logへない。
- `String(255)`とother type parameter boundaryがconstructorごとに一件だけcountされ、JSON/Puml/manifestのrule/countがexact一致する。
- PlantUML collision pairは`_U0022_`と`_U005F_U0022_U005F_`としてdistinctで、raw user quote/underscoreがlabelへ通らない。
- `ast.Import` scanでproduct sourceに`sqlalchemy`/Alembic/DB driver dependencyなし。
- CLI scopeはPython/SQLAlchemy snapshotとPython diffだけ。Next/HTML/all/SQLAlchemy diffなし。
- wheel metadata Requires-Distなし、offline install/run、schemas/tests/spec-dock/private contentがwheelへ混入しない。
- lock/license inventory exact equality。
- existing CI jobsを変更せずnew testsを実行できる。

### implementation

1. scope exclusion testを「SQLAlchemy directory/CLI全面禁止」から「SQLAlchemy snapshotは許可、runtime import/diff/HTML/Nextは拒否」へ正確に変更する。
2. packaging testにSQLAlchemy未installのoffline source snapshotを追加する。
3. CLI/config/manifest/stdout docsを実装済みsurfaceへ同期する。
4. security trapとnegative scanを全output channelへ適用する。
5. `pyproject.toml`/lock/license/CIに不要な差分があれば戻し、dependency/job追加なしでgateを通す。

### focused gate

```bash
uv run pytest tests/security/test_sqlalchemy_static_boundary.py \
  tests/security/test_python_static_boundary.py \
  tests/security/test_git_read_only.py \
  tests/security/test_file_change_hunk_redaction.py -q

uv run pytest tests/contracts/test_scope_exclusions.py \
  tests/contracts/test_json_schemas.py \
  tests/contracts/test_sqlalchemy_goldens.py \
  tests/contracts/test_python_goldens.py -q

uv run pytest tests/packaging/test_distribution.py -q
package_dist="$(mktemp -d)"
uv build --offline --out-dir "$package_dist"
rm -rf "$package_dist"
```

### stop conditions

- runtime dependency/lock/license変更が必要。
- network、target import、DB、Git mutationが必要。
- existing CI job追加やrelease/upload jobが必要。
- source/literal/private path leakをvalidatorで除去できない。

## I03-PLAN-008 — final quality gate and handoff

### prerequisite

- I03-PLAN-001〜007 focused gates green。
- product diffにDesign外pathなし。

### focused aggregate gate

```bash
uv run pytest tests/unit/sqlalchemy \
  tests/integration/sqlalchemy \
  tests/acceptance/sqlalchemy \
  tests/security/test_sqlalchemy_static_boundary.py \
  tests/contracts/test_sqlalchemy_goldens.py -q

uv run pytest tests/unit/cli/test_parser.py \
  tests/unit/core/test_budget.py \
  tests/unit/core/test_diagnostics.py \
  tests/unit/core/test_outcomes.py \
  tests/unit/artifacts/test_manifest.py \
  tests/unit/artifacts/test_writer.py \
  tests/unit/artifacts/test_streams.py -q

uv run pytest tests/acceptance/python \
  tests/acceptance/git \
  tests/unit/python \
  tests/unit/source \
  tests/integration/python \
  tests/integration/source \
  tests/contracts/test_python_goldens.py \
  tests/security/test_python_static_boundary.py \
  tests/security/test_git_read_only.py \
  tests/security/test_file_change_hunk_redaction.py -q
```

### repository-wide gate

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
uv run pytest -q
release_dist="$(mktemp -d)"
uv build --offline --out-dir "$release_dist"
rm -rf "$release_dist"
uv run pytest tests/packaging/test_distribution.py -q
python3 ./spec-dock/scripts/spec-dock validate
: "${BASELINE_SHA:?set to the verified pre-change full SHA from I03-PLAN-000}"
git diff --check "$BASELINE_SHA" --
git status --short
```

### manual diff audit

```bash
: "${BASELINE_SHA:?set to the verified pre-change full SHA from I03-PLAN-000}"
git diff --name-status "$BASELINE_SHA" --
git diff "$BASELINE_SHA" -- pyproject.toml uv.lock THIRD_PARTY_LICENSES.md .github/workflows/ci.yml
git diff "$BASELINE_SHA" -- src/code_structure_viz/application/diff.py src/code_structure_viz/semantic/diff.py
git diff "$BASELINE_SHA" -- spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00006-generate-sqlalchemy-er-snapshots/.meta.json
git diff "$BASELINE_SHA" -- spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00004-generate-python-structure-snapshots spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00005-compare-python-structure-changes-safely
```

expected:

- dependency/lock/license/workflowは差分なし。
- `application/diff.py`の差分は`DomainOutcome` factoryへの`domain="python"`明示と必要なimportだけで、semantic/output/Git behavior差分なし。`semantic/diff.py`は差分0。
- `.meta.json`、Issue 4/5 canonical、parent/ADR/reportは差分なし。
- generated caches、temporary output、venv、secret、fixture sentinel artifactsはtracked/untrackedに残らない。

### completion / handoff

- I03-AC-001〜010のactual evidence、command、result、residual unsupported patternsをfuture `report.md`へ記録する。
- Issue 7へ、SQLAlchemy snapshot public schema/IDs/coverage/diagnosticsとadapter modelをhandoffする。diff/matching/empty-sideは実装しない。
- owner decisionなしで完了できなかったstop conditionは、推測で埋めず明示blockerとして返す。

## acceptance test IDs

| Test ID | owning path | observable behavior |
| --- | --- | --- |
| I03-AT-001 | `tests/acceptance/sqlalchemy/test_snapshot_cli.py` | modern/classic/Table/`__table__` complete CLI、paths、manifest、exit。 |
| I03-AT-002 | `tests/integration/sqlalchemy/test_er_semantics.py` | row/relation kinds、cross-module resolution、identity/order、non-lossy dedupe、lossy check/index conflictのstatus/diagnostic/row count。 |
| I03-AT-003 | `tests/acceptance/sqlalchemy/test_snapshot_targets.py` | path/module/class targets、union、depth/frontier、missing/ambiguous。 |
| I03-AT-004 | `tests/acceptance/sqlalchemy/test_snapshot_failures.py` | complete-empty/not_applicable/partial_safe/payload_unavailable/collision matrix。lossy conflict fixtureはpartial_safe/exit 3を固定する。 |
| I03-AT-005 | `tests/security/test_sqlalchemy_static_boundary.py`, `tests/unit/sqlalchemy/test_plantuml.py`, `tests/unit/artifacts/test_writer.py` | no execution/DB/Git mutation、redaction count/rule cross-artifact equality、PlantUML metadata validation、escape collision、all-channel negative scan。 |
| I03-AT-006 | `tests/acceptance/sqlalchemy/test_snapshot_determinism.py` | same input bytes/SHA、semantic order/ID stability。 |
| I03-AT-007 | `tests/acceptance/sqlalchemy/test_snapshot_budget.py` | 500/501/override/invalid/diff-only options。 |
| I03-AT-008 | `tests/acceptance/sqlalchemy/test_stdout_selector.py` | exact bytes、summary、unavailable、usage、stderr separation。 |
| I03-AT-009 | `tests/contracts/test_json_schemas.py`, `test_sqlalchemy_goldens.py`, existing Python goldens | closed schema unionとPython compatibility。 |
| I03-AT-010 | full suite + `tests/packaging/test_distribution.py` + CI | runtime dependency 0、offline package、platform/toolchain/scope。 |

## Requirement → Design → Plan → acceptance trace

| Requirement | Design | Plan | Acceptance | Test |
| --- | --- | --- | --- | --- |
| I03-REQ-001 | I03-DES-001 | I03-PLAN-001, 002, 006 | I03-AC-001 | I03-AT-001 |
| I03-REQ-002 | I03-DES-002, 006 | I03-PLAN-002, 004 | I03-AC-003, 007, 008 | I03-AT-003, 007, 008 |
| I03-REQ-003 | I03-DES-003, 004 | I03-PLAN-003, 004 | I03-AC-001, 004 | I03-AT-001, 004 |
| I03-REQ-004 | I03-DES-004, 005 | I03-PLAN-003, 005 | I03-AC-001, 002, 009 | I03-AT-001, 002, 009 |
| I03-REQ-005 | I03-DES-004, 005, 006 | I03-PLAN-003, 004, 005 | I03-AC-002, 003, 004 | I03-AT-002, 003, 004 |
| I03-REQ-006 | I03-DES-007, 009 | I03-PLAN-003, 005, 006, 007 | I03-AC-005 | I03-AT-005 |
| I03-REQ-007 | I03-DES-008, 009 | I03-PLAN-002, 004, 006 | I03-AC-004, 007, 008 | I03-AT-004, 007, 008 |
| I03-REQ-008 | I03-DES-003, 004, 007, 009, 010 | I03-PLAN-003, 004, 005, 006, 007 | I03-AC-005, 006, 010 | I03-AT-005, 006, 010 |
| I03-REQ-009 | I03-DES-001, 002, 009, 011 | I03-PLAN-002, 005, 006, 008 | I03-AC-008, 009 | I03-AT-008, 009 |
| I03-REQ-010 | I03-DES-010, 012 | I03-PLAN-001, 007, 008 | I03-AC-010 | I03-AT-010 |

## rollback / forward recovery

- persistent DB/data migrationはN/A。
- source execution、secret/private path leak、false complete、Python public regression、atomic publication regressionはrelease stopである。
- unsafe SQLAlchemy patternはcompleteを維持するために推測せず、unknown/partial_safe/payload_unavailableへ狭める。
- schema field/row kindを削除する必要がある場合、same `/v1` silently breakせずversion reviewを行う。
- rollbackはSQLAlchemy adapter + shared additive extensions + schemas/docs/testsを一体で戻し、Issue 4/5 accepted contractを維持する。
- existing immutable Artifactを自動rewriteしない。

## final stop conditions

次のいずれかが残る場合、本 Issue をcompleteとしない。

- any acceptance ID未実装、skip、xfail、golden未review、schema validation gap。
- target import/DB/runtime SQLAlchemy/network/Git mutationが必要または発火。
- source/default/check/join/secret/private pathがどれかのoutput channelへ漏れる。
- Python snapshot/diff exact public bytes/path/status/exitが変わる。
- SQLAlchemy diff、Next、all-domain、HTML、新config key、runtime dependencyが混入。
- `.meta.json`、report、accepted ADR、Issue 4/5/parent canonical文書をcoderが編集。
- Designにないowner decisionを実装者が暗黙に選択。
