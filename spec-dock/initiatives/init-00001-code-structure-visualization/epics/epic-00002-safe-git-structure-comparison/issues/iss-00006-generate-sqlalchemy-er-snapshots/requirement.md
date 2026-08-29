---
種別: 要件定義書（Issue）
ID: "iss-00006"
タイトル: "Generate SQLAlchemy ER Snapshots"
関連GitHub: ["#6"]
package_sequence_key: "ISSUE-03"
状態: "draft"
最終更新: "2026-08-29"
親: ["epic-00002", "init-00001"]
---

# iss-00006 Generate SQLAlchemy ER Snapshots — 要件定義

詳細: [Requirement Guide](../../../../../../docs/authoring/requirement.md)

## 目的

coding agent または人間が、対象 Git repository の application、SQLAlchemy、database、migration を起動せず、run 開始時に固定した Python source を静的に解析し、SQLAlchemy declarative ORM の table、column、constraint、index、foreign key、relationship、inheritance、association table を versioned semantic JSON と ER PlantUML で取得できる。

利用者 story: coding agent として、runtime mapper、database reflection、Alembic、import side effect に依存せず、repository に宣言された ORM 構造と解析 coverage を、安全で決定的な Artifact として取得し、設計・実装・review の入力にしたい。

この Issue は parser や renderer の単独完成ではなく、次の一つの vertical outcome を所有する。

```text
snapshot CLI request
  -> existing usage/config/output preflight
  -> existing immutable working-tree SourceView
  -> SQLAlchemy-owned static AST analysis and target selection
  -> domain-local table budget
  -> sqlalchemy semantic JSON / SQLAlchemy ER PlantUML / run manifest
  -> exact stdout / JSONL stderr / exit / atomic publication acceptance
```

SQLAlchemy temporal diff、ghost row、before/after matching は後続 `iss-00007` の責務であり、本 Issue の完了条件へ含めない。

## 正本・依存・現行 repository facts

### canonical authority

- stable package key は `ISSUE-03`、SpecDock Issue ID は `iss-00006`、GitHub Issue は `#6` である。
- declared dependency は `iss-00004` / `ISSUE-01` だけである。`iss-00005` の Python diff 実装は regression 対象だが、本 Issue の機能依存ではない。
- 本 directory 直下の `requirement.md`、`design.md`、`plan.md` と、親 Initiative/Epic canonical R/D/P、accepted ADR が実装 authority である。
- `.meta.json`、`report.md`、accepted ADR、Issue 4/5 canonical 文書、親 canonical 文書、generated projection は本 Issue の実装者が編集しない。
- canonical 文書へ一時的な branch tip SHA を固定しない。実装開始時に task が指定する repository、branch、full SHA と root `AGENTS.md` の有無を再検証し、別 branch や default branch へ置換しない。

### verified current implementation

現行 repository の Issue 4/5 hardened common spine と Issue 6 の実装 checkpoint には、次の境界が既に存在する。以降の実装者はこの状態を入力として受け取り、実装前の不存在を仮定して second path や別 lifecycle を作らない。

- `src/code_structure_viz/application/snapshot.py::SnapshotApplication` は Python/SQLAlchemy snapshot の source acquisition、analysis、budget、render、manifest、drift check、atomic publication を一つの lifecycle として所有する。
- `src/code_structure_viz/application/diff.py::DiffApplication` と `src/code_structure_viz/source/{endpoints,freezer,file_changes,git_repository}.py` は hardened Python diff/Git safety boundary を所有し、SQLAlchemy diff は登録しない。
- `src/code_structure_viz/adapters/sqlalchemy/` の analyzer、selector、immutable model、semantic JSON/PlantUML renderer、snapshot adapter、および SQLAlchemy acceptance/integration/security/unit tests が存在し、frozen `.py` AST だけから ER snapshot を構成する。
- CLI request、manifest、writer、stream、schema、contract docs は `sqlalchemy` domain と SQLAlchemy artifact path を closed additive branch として実装済みであり、既存 Python public bytes/path/status は回帰で固定される。
- runtime dependency は 0 件であり、`pyproject.toml`、`uv.lock`、`THIRD_PARTY_LICENSES.md` は SQLAlchemy package を含まない。offline wheel でも target ORM を import しない。
- 実装開始時は repository root の `AGENTS.md` の有無と指定された repository/branch/full SHA を再確認する。現在の checkpoint では root `AGENTS.md` は存在しない。

### 旧 Issue 6 記述から置き換える事項

| 旧・不整合な記述 | 本書の replacement contract |
| --- | --- |
| production package、CLI、schema、acceptance fixture は未実装 | Python snapshot/diff と hardened common spine は実装済み。SQLAlchemy は既存 lifecycle へ additive に接続する。 |
| SQLAlchemy 用に独立した application service と writer を作る | `SnapshotApplication`、`SourceViewBuilder`、`DomainOutcome`、`EntityBudgetGate`、`RunManifestBuilder`、`OutputTransaction`、stream emitter を domain-aware に拡張し、source/publication lifecycle を複製しない。 |
| `--target path:src/models` | 現行 `TargetSpec` に存在しない directory target なので受理しない。`path:` は repository-relative `.py` file、`module:` は dotted module、`class:` は dotted class target に限定する。 |
| planned `detector.py`、`redaction.py`、generic `renderer.py` | Design に列挙する現行 architecture と最小の新規 module/symbol を正本とする。不要な layer は作らない。 |
| config に SQLAlchemy 専用 section を追加する可能性 | `code-structure-viz.config/v1` の既存 `[python]` source selection を、Python source を読む `python`/`sqlalchemy` 両 domain で共有する。新しい config key は追加しない。 |
| SQLAlchemy package を parser として利用できる | runtime/build/test のいずれでも target ORM の import・mapper inspection に利用しない。product runtime dependency は 0 件を維持する。 |

## 親 requirement / accepted ADR との境界

| authority | 本 Issue が維持する境界 |
| --- | --- |
| EPIC-REQ-001 / Vertical Issue Slicing | `snapshot --domain sqlalchemy` を CLI から Artifact、stream、exit、acceptance まで単独で完了する。 |
| EPIC-REQ-002 / Static Analysis Safety Boundary | target code、SQLAlchemy、DB driver、Alembic、plugin、build scriptを import・compile・executeせず、Gitをread-onlyで扱う。 |
| EPIC-REQ-003 / Domain Adapter Boundaries | common layerはlifecycle/source/outcome/budget/artifactに限定し、table/row/relation identity、static recognition、selection、redaction、renderingはSQLAlchemy adapterが所有する。 |
| EPIC-REQ-004 / Agent First Artifact Contract | `sqlalchemy.snapshot.semantic.json`、`sqlalchemy.snapshot.puml`、`run-manifest.json`、relative path、SHA-256、redaction、determinism、no-overwriteを提供する。 |
| EPIC-REQ-005 | `complete` / `not_applicable` / `incomplete`、`partial_safe` / `payload_unavailable`、exit 0/1/2/3/130、default 500 table gateを維持する。changed-path gateはdiff専用である。 |
| EPIC-REQ-006 | Python 3.12+、Git 2.39+、macOS/Linux、lock/license/offline/minimum/latest CIを維持し、NodeやSQLAlchemy packageを追加しない。 |
| EPIC-REQ-008 / Exclude Product HTML Reports | HTML command、format、schema、renderer、publicationを追加しない。 |
| EPIC-REQ-009 | closed stdout selector、exact-byte copy、typed unavailable result、selectorなしsummary、stderr diagnostic、usage no-publicationを維持する。 |
| Independent Product Ownership | `pyclassuml`、`tree-git-diff`、SQLAlchemy runtimeへのpackage/CLI dependencyとlegacy compatibility layerを作らない。 |
| Named Git Comparison Endpoints / Dual Snapshot Semantic Diff | `snapshot` は一つの working-tree SourceViewだけを扱い、endpoint resolver、FileChangeSet、canonical empty side、semantic diffを呼ばない。 |

## 観測可能な要件

| ID | 観測面 | 要件 |
| --- | --- | --- |
| I03-REQ-001 | vertical CLI outcome | `code-structure-viz snapshot --domain sqlalchemy` が safe source acquisition、SQLAlchemy analysis、target selection、requested payload、manifest、stream、exitまでを一回のrunとして完結する。 |
| I03-REQ-002 | CLI/config compatibility | 既存 snapshot grammar、target grammar、format、stdout、config precedence、positive entity overrideを再利用し、SQLAlchemy snapshotに必要なdomain acceptanceだけをadditiveに拡張する。 |
| I03-REQ-003 | source/applicability | 既存 immutable SourceViewの`.py` bytesだけを解析する。domain evidence不在を証明できる場合だけ`not_applicable`とし、失敗やdynamic evidenceをabsenceへ変換しない。 |
| I03-REQ-004 | table identity | table entityはstatic schema名またはnullとstatic table名で同定し、module、path、mapped class名をidentityへ混ぜない。無関係な宣言が同一identityへ収束した場合はwinnerを選ばない。 |
| I03-REQ-005 | row/relation semantics | column、primary key、unique、check、index、foreign key、relationship、inheritance、association tableをtyped row/relationとして区別し、FKとrelationshipを同一kindへ畳み込まない。redaction categoryだけでidentityを作るunnamed check/unnamed expression indexは、同一AST declarationの再発見だけをdedupeし、同一物理行のsiblingを含むdistinct declaration occurrenceをequivalent duplicateとみなさない。各distinct conflict occurrenceはcurrent diagnostic schema上で別の`CSV-SA-009`として保持する。 |
| I03-REQ-006 | redaction/output | default、server_default、computed、check/join expression等の値・本文を保持せず、presence/category/redacted markerとcountだけをJSON、PlantUML、manifest coverageへ出す。type constructor parametersはconstructorごとに一件と数え、JSON、PlantUML、manifestが同一rule/countを公開する。 |
| I03-REQ-007 | status/publication/budget | local failure、safe subset不在、explicit target failure、table collision、entity overrun、run fatal、usage、interruptを区別し、statusに対応するpayload/manifest/exit matrixを満たす。 |
| I03-REQ-008 | safety/determinism/bounded analysis | import/DB/Git mutationを行わず、解析をfrozen source、有限AST、有限class graph、requested traversal depth、table budget内に閉じる。同じ入力ではID、order、diagnostic、bytes、SHA-256が決定的になる。 |
| I03-REQ-009 | stdout/schema/public compatibility | SQLAlchemy selector、summary、unavailable result、schema、manifest、writerをclosed unionとして拡張し、同じPython入力に対する既存public bytes/path/statusを変えない。 |
| I03-REQ-010 | implementation acceptance | repository-owned unit/integration/acceptance/security/contract/packaging testsと既存CI gateが、runtime dependency 0件、offline wheel、no HTML、no SQLAlchemy diffを確認する。 |

## CLI contract

### command grammar

本 Issue が追加する利用可能な command shape は次である。

```text
code-structure-viz snapshot \
  --repo PATH \
  --output-dir PATH \
  --domain sqlalchemy \
  [--config PATH] \
  [--target path:REPOSITORY_RELATIVE_FILE.py]... \
  [--target module:DOTTED_MODULE]... \
  [--target class:DOTTED_MODULE_AND_CLASS]... \
  [--upstream-depth NON_NEGATIVE_INT] \
  [--downstream-depth NON_NEGATIVE_INT] \
  [--format semantic-json|plantuml]... \
  [--max-entities POSITIVE_INT] \
  [--stdout manifest|sqlalchemy:semantic-json|sqlalchemy:plantuml]
```

- `snapshot`、`--repo`、`--output-dir`、`--domain sqlalchemy` は必須である。domain省略、`all`、`next`、大小文字違い、alias、short optionはusage errorとする。
- `diff --domain sqlalchemy` は本Issueで登録しない。`DiffCliRequest.domain` は `python` のまま維持し、SQLAlchemy diffはsource acquisition前のusage error、exit 2、stdout空、Artifact 0件とする。
- `snapshot` と `--from`、`--to`、`--pr-target`、`--max-changed-paths` の併用は既存 `CSV-USAGE-003` 境界で拒否する。implicit baseやworking-tree changed path数はSQLAlchemy snapshot結果へ影響しない。
- `--target` は既存 `TargetSpec` grammarを変更しない。`path:` はexact `.py` fileだけであり、directory、glob、absolute path、`..`を受理しない。`module:`/`class:` はNFC正規化したPython dotted identifierだけを受理する。
- 同一normalized targetは一つへ畳む。path/module targetは複数tableを選択できる。class targetはexact mapped classを一つへ解決できなければ`payload_unavailable`とする。
- `--upstream-depth`/`--downstream-depth` は少なくとも一つの`--target`がある場合だけ受理する。defaultは各1。whole modeで明示depthはusage errorとする。
- `--format` 未指定時は `semantic-json`、`plantuml` の順で両方を生成する。同一format重複、unknown format、`html`はusage errorとする。
- `--max-entities` はASCII base-10の1以上だけを受理する。zero、negative、sign、float、scientific notation、whitespace、underscoreはusage errorとする。
- `--stdout` は高々1回。selector domainはselected domain、formatはrequested formatと一致しなければならない。
- `--help` はPython/SQLAlchemy snapshotの実装済みsurfaceだけを表示する。Python diffの既存command/contractは維持するが、本Issueのsnapshot helpへは追加しない（scope exclusion contract）。このhelp拡張は本Issueの意図したadditive public changeである。`--version`は既存exact lineを維持する。

### examples

```bash
code-structure-viz snapshot --repo . --output-dir /tmp/csv-er --domain sqlalchemy

code-structure-viz snapshot --repo . --output-dir /tmp/csv-user-er --domain sqlalchemy \
  --target path:src/models/user.py --upstream-depth 1 --downstream-depth 1

code-structure-viz snapshot --repo . --output-dir /tmp/csv-module-er --domain sqlalchemy \
  --target module:app.models --format semantic-json

code-structure-viz snapshot --repo . --output-dir /tmp/csv-stdout --domain sqlalchemy \
  --format semantic-json --stdout sqlalchemy:semantic-json
```

## config / source acquisition contract

### config compatibility

- `code-structure-viz.config/v1` のschemaと必須top-level keyは変更しない。
- `[python].source_roots`、`[python].include`、`[python].exclude` はv1では「Python source acquisition scope」であり、`python` class snapshot/diffと`sqlalchemy` snapshotの両方に適用する。SQLAlchemy専用config section、pattern allowlist、environment overrideを追加しない。
- built-in → repository root `.code-structure-viz.toml` またはexplicit `--config`のexactly one source → CLI depth/max-entities override、という既存解決順を維持する。repository configとexplicit configをmergeしない。
- `[comparison]` が存在してもsnapshotは参照しない。manifestには既存config descriptorを同じ形で記録できるが、comparison endpointを解決しない。
- unknown key、型不正、schema不一致、unsafe source root/globはexit 2、stdout空、Artifact 0件とする。

### SourceView reuse

- `GitRepositoryReader` と `SourceViewBuilder` の既存working-tree snapshot経路を一回だけ使用する。SQLAlchemy用にsecond freeze、target import、Git blob fallback、database sourceを作らない。
- SourceViewはrepository-relative `.py` path、bytes、digest、failure、head/fingerprintだけをadapterへ渡す。absolute repository/staging pathをadapter DTOへ渡さない。
- source fileはPython 3.12 grammarでstatic parseする。encoding detection、module identity、collision、parse failureはtyped coverage/diagnosticへ変換する。
- run公開直前のHEAD/path/source fingerprint driftは既存run-level fatal、exit 1、final manifestを含むArtifact 0件とする。

## applicability and static recognition contract

### evidence rule

SQLAlchemy domain evidenceは、allowlisted SQLAlchemy bindingまたはfully-qualified symbolが次のsupported declaration shapeで実際に使用された場合に限る。import文だけをdomain presenceとしない。

- `DeclarativeBase` のdirect subclassまたはrepository内で静的に解決できるtransitive subclass。
- module top-levelで一つのnameへ束縛したdirect `declarative_base(...)` callと、そのbaseを継承するclass。
- proven declarative class内のliteral `__tablename__`、supported `__table__`、`Mapped`、`mapped_column`、`Column`、`relationship` declaration。
- module top-levelのsupported `Table(...)` assignment。
- star import自体はdomain evidenceではない。ただしstar import後の`Column`、`Mapped`、`relationship`等をsupported declaration位置で使用し、binding originを証明できない場合はunknown SQLAlchemy evidenceとして`incomplete`候補にする。ambiguous/rebound alias、dynamic factory、call resultをbaseとするpatternも同様に推測しない。

全candidate fileを安全にparse/indexでき、supportedまたはunknown SQLAlchemy evidenceが一件もない場合だけ`not_applicable`とする。read/encoding/module/parse failureが一件でもありdomain absenceを証明できない場合、safe tableがなければ`payload_unavailable`、safe tableがあれば`partial_safe`とする。

### recognized declarative patterns

- allowlisted bindingはstatic `ast.Import` / `ast.ImportFrom`だけから構築し、star import、conditional/runtime mutation、`getattr`、`importlib`、call returnの型推測を行わない。
- repository内module/class/base bindingはmodule pathとstatic import aliasから固定点計算し、class候補数を超えるiterationを行わない。
- table identityを作るには、module top-levelのproven declarative classのdirect static string `__tablename__`、direct `Table(static_name, ...)`、またはstatic `Table` bindingへの`__table__`参照が必要である。function/local/nested class内のdeclarative declarationはinitial releaseの対象外で、supported tableへmergeしない。
- schemaはdirect `Table(..., schema=STATIC_STRING)`、またはliteral `__table_args__` mapping/tuple末尾mappingの`schema`だけを受理する。schema指定なしはJSONの`null`であり、displayでは`<default>`を使う。
- module-level `Table(static_name, metadata, ...)`はtable entity候補である。mapped classがexact `__table__` bindingで同じTableを参照するときだけ一つのentityへ統合する。
- automap、imperative mapper、runtime registry inspection、`MetaData.reflect`、deferred reflection、Alembic、SQL text parsingは対象外である。

## target selection contract

- targetなしは安全に解析できた全table entityを選択するwhole modeである。
- `path:` はprovenance pathがexact一致するtable、`module:` はmapping source moduleがexact一致するtable、`class:` はmapped classのcanonical dotted nameがexact一致するtableをseedとする。
- multiple targetはseed unionである。明示targetが0件へ解決、またはclass targetが複数候補へ解決した場合は`payload_unavailable`であり、whole modeや他tableへfallbackしない。
- internal table graphのedgeはforeign key、relationship、inheritance、association relationである。downstreamはsource tableからtarget table、upstreamはreverse edgeを指定depthまで走査する。
- selected payloadはseedとdepth内context tableを含む。depth境界を越えるinternal relationはcoverage frontierへ記録し、存在しないtableを生成しない。
- table entity budgetはtarget traversal後のselected table数へ適用する。depthをbudget truncationに使わない。

## SQLAlchemy semantic contract

### table identity

- public table identity tupleは `schema_name: str | null` と `table_name: str` だけである。両stringはstrict UTF-8をNFC正規化し、empty/NUL/control character、`\`、absolute/path-like spelling、URI-like `://`を拒否する。同じsafe structural string規則をcolumn/constraint/index/relationship/back_populates/FK target segmentへ適用する。
- public `id` は上記tupleを `code-structure-viz.sqlalchemy-table-id/v1` のcanonical JSONとしてencodingし、そのSHA-256を `sqlalchemy:table:<64 lowercase hex>` に付加した値とする。
- display nameはschema nullなら `<default>.<table>`、それ以外は `<schema>.<table>`。`<default>`はdisplay markerであり、schemaの実値ではない。
- module、path、source range、mapped class、local Table bindingは`mapping_sources` provenanceでありidentityへ含めない。
- unrelated declarationが同一table identityへ収束した場合、module/pathをidentityへ足したり、first/last winnerを選んだりしない。exact `__table__` bindingで同じTableを参照するproven declarationだけを統合する。

### rows and relations

SQLAlchemy semantic JSONはcommon envelopeの`entities`、`members`、`relations`を使用する。tableはentity、次の構造はtyped member rowとして表す。

| row kind | 必須の安全な意味 |
| --- | --- |
| `column` | static column name、closed type category、optional safe type symbol、nullable/primary_key/unique/indexのstatic boolまたはunknown、redacted default descriptors。 |
| `primary_key` | optional static constraint name、static column names。 |
| `unique` | optional static name、static column names。 |
| `check` | optional static name、closed redacted expression descriptor。expression bodyと参照column推測は保持しない。 |
| `index` | optional static name、ordered column/expression term、static unique boolまたはunknown。expression termはclosed redacted descriptorとしbodyを保持しない。 |
| `foreign_key` | local column names、static `table.column`または`schema.table.column` target、internal/external/unknown resolution。 |
| `relationship` | mapped attribute name、safe target class/table resolution、scalar/many/unknown cardinality、static `uselist`、static `back_populates`、static secondary table identity。join/order/foreign-key expression bodyは保持しない。 |
| `inheritance` | child tableから静的に解決したlocal parent mapped tableへの参照。runtime mapper strategyを推測しない。 |
| `association_table` | relationshipのstatic `secondary`として使用されたmodule-level Tableのmarker。standalone Tableを根拠なくassociation tableと呼ばない。 |

- `Mapped[T]`、`mapped_column(...)`、classic `Column(...)`、`Table(..., Column(...))`をsupported形として扱う。bare `Mapped[T]`はproven declarative class内だけcolumn候補とする。annotation内のquoted forward referenceはwhole stringがsafe dotted identifierの場合だけsymbolとして扱い、string expressionをparse/evalしない。
- type categoryは `integer|string|text|boolean|date|datetime|time|decimal|float|json|binary|uuid|enum|array|custom|unknown` に閉じる。length、precision、enum values、constructor argumentsは出力しない。
- foreign keyとrelationshipは別row、別relation kindである。relationshipからforeign keyを推測せず、foreign keyからrelationshipを合成しない。
- classがmapped parentを継承してもown table identityを持たない場合、single-table/mixin/abstractを推測せず、そのclass固有rowをparentへ自動mergeしない。static `__abstract__ = true` はbase evidenceとして利用できるがtable entityにはしない。
- row IDはowner table ID、row kind、kind別stable structural keyから `sqlalchemy:row:<sha256>` を作る。relation IDもkind、source、target、via row、roleのcanonical tupleから作る。source path、line、declaration order、raw literal、expression bodyをIDへ含めない。
- non-lossy structural identityを持つrow/relationでは、同一IDかつ`id`/`source`を除くpublic semantic payloadが同一のevidenceを一つへcanonicalizeできる。payloadが異なる場合はwinnerを選ばず、全該当evidenceを除外して各source occurrenceへ`CSV-SA-009`を出す。
- redactionによりmany-to-oneとなるlossy structural identity、すなわちunnamed `check`と、少なくとも一つのexpression termを含むunnamed `index`では、同一owner/kind/pathとfrozen AST metadata由来のfull declaration span `(start_line,start_utf8_byte_column,end_line,end_utf8_byte_column)` が一致する同一AST declarationの再発見だけをdedupeできる。public `SqlAlchemySourceLocation`は従来どおりpathとstart/end lineだけを持ち、UTF-8 byte columnはadapter-internal evidenceに限定してJSON、PlantUML、manifest、diagnostic fieldへ公開しない。同一物理行の別sibling declarationはbyte column spanが異なるためdistinct occurrenceである。異なるoccurrenceが同じlossy IDへ収束した場合はpublic payloadが同一でも全該当rowを除外し、各occurrenceへ`CSV-SA-009`を出してdomainを`incomplete`にする。ordinary named row、column-termだけのunnamed index、その他non-lossy identityのexact semantic dedupeは維持する。
- lossy conflictの`CSV-SA-009`はexisting diagnostic shape `domain/path/symbol/line`を変更せず、Designで固定するowner/kind/path/full internal AST spanのcanonical framed SHA-256から`sqlalchemy:occurrence:<64 lowercase hex>`を`symbol`として生成する。同一occurrenceの再発見は同じsymbol、同一行の別siblingを含むdistinct occurrenceは別symbolとなり、existing `canonical_diagnostics`で一件へ潰れない。symbolへraw source、semantic identifier、column値、byte column decimalを直書きしない。
- entity、row、relation、mapping source、coverage、diagnosticはDesignのUTF-8 byte sort tupleで決定的に並べる。source declaration orderだけの変更はIDとsemantic array orderを変えない。provenance rangeは実sourceに追従するためArtifact SHA自体は変わり得る。

### redaction

- `default`、`server_default`、`onupdate`、`server_onupdate`、`Computed`、`Identity`、check expression、relationship join/order/foreign_keys、arbitrary SQL expressionはraw AST text、literal、reprをmodelへ入れない。
- default-like valueは `{present, category, redacted}` だけを持つ。categoryは `absent|literal|callable|sql_expression|computed|identity|unknown` に閉じ、presentな値は常に`redacted: true`とする。
- type constructorにargument/keywordが一つ以上ある場合、constructor全体を一つの`type.parameters` redacted boundaryとする。`String(255)`は1件、`Numeric(10, 2, asdecimal=True)`も1件であり、argument、keyword、nested literal/node数を重複計上しない。
- structural identifierとして必要なtable/schema/column/constraint/index/relationship/back_populates/FK target名だけを、safe static stringとして出力できる。connection URL、password、token、SQL/check/default bodyはstructural identifierとして扱わない。
- coverageは `rule_version: code-structure-viz.sqlalchemy-redaction/v1` とrun内の`redacted_values` countを持つ。semantic JSON coverage、SQLAlchemy PlantUML metadata、manifest domain coverageは同じsummaryのrule/countを公開し、不一致を成功として公開しない。
- SQLAlchemy PlantUMLは`legend right`直後にrenderer-owned line `  rule_version=code-structure-viz.sqlalchemy-redaction/v1`、続けて`  redacted_values=<0またはleading zeroなしのpositive ASCII decimal>`をexactly once出す。table 0件でも省略しない。
- initial releaseに`--include-literals`、debug source dump、raw AST outputを設けない。

## Artifact / schema / publication contract

### published paths

| outcome | published files |
| --- | --- |
| `complete`、default formats | `sqlalchemy.snapshot.semantic.json`、`sqlalchemy.snapshot.puml`、`run-manifest.json` |
| `complete`（table 0件のapplicable emptyを含む）、one requested format | requested SQLAlchemy payload、`run-manifest.json` |
| `incomplete / partial_safe` | requested SQLAlchemy payload、`run-manifest.json`、exit 3 |
| `not_applicable` | `run-manifest.json`だけ、exit 0 |
| `incomplete / payload_unavailable` | `run-manifest.json`だけ、exit 3 |
| run fatal / usage / interrupt | final output directoryとfinal manifestを含むArtifact 0件、exit 1/2/130 |

- semantic JSONは `type: semantic_snapshot`、`schema: code-structure-viz.semantic/v1`、`domain: sqlalchemy`、`document_kind: snapshot`を持ち、media typeは`application/json`である。SQLAlchemy diff documentはschemaへ追加しない。
- SQLAlchemy PlantUML contractは `code-structure-viz.plantuml/sqlalchemy/v1`、exact titleは `SQLAlchemy ER snapshot`、media typeは`text/vnd.plantuml; charset=utf-8`とする。column lineは`type=<type.name|->`の直後に`type_parameters=<redacted token|->`をexactly once持つ。
- user-controlled PlantUML label escapingはinjectiveでなければならない。input underscoreはすべて`_U005F_`、input dotはすべて`_U002E_`へencodeし、renderer-owned alias、keyword、metadata key、placeholderのunderscoreと、schema/table componentを結ぶrenderer-owned separatorのliteral `.`だけをsyntaxとして残す。schema/table componentは個別にescapeしてからseparatorで結合するため、`(schema=a, table=b.c)`は`a.b_U002E_c`、`(schema=a.b, table=c)`は`a_U002E_b.c`となり衝突しない。input quote `"`の`_U0022_`、literal input `_U0022_`の`_U005F_U0022_U005F_`、input dotの`_U002E_`も相互に区別される。
- run manifestはadapter `{domain: sqlalchemy, name: sqlalchemy-ast, version: "1"}`、SQLAlchemy PlantUML contract、command/request/source/config/run/domain/artifact descriptorを持つ。
- semantic JSON、manifest、summary、stdout resultはexisting canonical JSON encoderのUTF-8/no BOM/no extra space/final LFを用いる。PlantUMLもUTF-8/final LF/no double final LFとする。
- JSON Schemaはtest/build-time gateであり、runtimeはschema fileや`jsonschema`をloadしない。
- writerはclosed SQLAlchemy filenamesとclosed PlantUML grammarだけをadditiveに許可し、arbitrary filename/lineへ緩和しない。
- output directoryはrepository外のnonexistent pathで、same-parent private stagingからno-replace atomic renameする。existing pathを上書きしない。

## status / failure / publication contract

| condition | domain/run status | payload | manifest | exit |
| --- | --- | --- | --- | --- |
| 全candidateを安全に解析し、一件以上のselected tableがbudget内 | `complete` | requested JSON/PlantUML | あり | 0 |
| supported SQLAlchemy evidenceはあるがtable entityが0件で、failure/unknownがなくtargetなし（例: abstract declarative baseだけ） | `complete` | empty `entities`/`members`/`relations`のrequested JSON/PlantUML | あり | 0 |
| 全candidateを安全に解析し、SQLAlchemy evidenceなし、targetなし | `not_applicable` | なし | あり | 0 |
| safe selected tableが一件以上あり、失敗file/dynamic declaration/unknown row/relation/collisionを局所隔離できる | `incomplete / partial_safe` | safe subsetのrequested JSON/PlantUML | あり | 3 |
| safe selected tableなし、domain absenceを証明不能、explicit target失敗、全selected identity collision、safe subsetなし | `incomplete / payload_unavailable` | なし | あり | 3 |
| selected table数がresolved max-entities超過 | `incomplete / payload_unavailable` | なし。切り捨てない | requested/resolved/actual/sourceとdiagnosticを記録 | 3 |
| invalid CLI/config/selector/override/SQLAlchemy diff request | `usage` | なし | なし | 2 |
| Git/repository/output/source drift/internal serializer/security/atomic invariant failure | run `fatal` | なし | なし | 1 |
| handled SIGINT | run `interrupted` | なし | なし | 130 |

- `partial_safe` はsafe subset、欠落coverage、safe diagnostic、redaction pass、entity budget pass、全requested renderer passを同時に満たす場合だけ許可する。
- `payload_unavailable`にaffected artifact descriptorを持たせない。`partial_safe`なのにrequested descriptorが欠ける状態もpublication前internal invariant failureとする。
- not_applicableはdiagnosticなしを原則とし、failureやunknownをnot_applicableへ変換しない。
- table entity budgetはdefault 500。row/memberはPython memberと同様に別public budgetを設けないが、frozen sourceを一回だけ有限ASTへ変換し、fixed-pointとtarget traversalをcandidate/class/depthで有限化し、source外へ展開しない。truncationは行わない。

## stdout / stderr contract

- selector grammarは `manifest | DOMAIN:FORMAT` に閉じる。parserは将来selector token `next:*`をsyntax上認識できても、selected SQLAlchemy runでは`sqlalchemy:*`または`manifest`以外をcompatibility errorにする。
- selectorなしstdoutは `code-structure-viz.run-summary/v1` 1行で、domainは実際の`sqlalchemy`、manifestは`run-manifest.json`またはnullとする。
- available domain selectorは公開fileのexact bytesだけをstdoutへ複製する。summary、label、BOM、改行補正を付けない。
- not_applicableまたはpayload_unavailableでは `code-structure-viz.stdout-result/v1` 1行を返し、`domain_status`とstable reasonを持つ。partial_safeはpayload availableなのでexact bytesを返し、exit 3を維持する。
- fatal/interrupt/manifest unavailableはrun statusのunavailable resultを返す。usage errorだけはstdout空である。
- diagnosticはcanonical JSONLとしてstderrだけへ出す。source body、literal、secret、absolute path、Git stderrを含めない。

## safety / compatibility / deterministic boundary

- product sourceは`sqlalchemy`、DB driver、Alembic、target repository moduleをimportしない。`ast.parse`、`tokenize`、immutable DTO、canonical serializerだけを使用する。
- `eval`、`exec`、`compile`、`ast.literal_eval`によるarbitrary tree evaluation、`inspect`、`importlib`、mapper configuration、engine/session/connection、metadata reflectionを使用しない。
- Git command allowlist、fixed environment、repository identity、HEAD/source drift、symlink/path collision、output descriptor checksを変更または弱化しない。
- same Python snapshot/diff inputに対するfilenames、semantic JSON、PlantUML、manifest、summary、stdout result、diagnostic、exitはbyte-for-byte互換を維持する。schema extensionはclosed `oneOf`追加であり、Python branchの`additionalProperties: false`を緩和しない。
- `src/code_structure_viz/semantic/diff.py`、`DiffApplication`、FileChangeSet、canonical empty sideへSQLAlchemy logicを追加しない。
- `pyproject.toml`のruntime dependenciesは空、`uv.lock`とlicense inventoryはdependency追加なしを維持する。wheelはSQLAlchemy未installのoffline environmentでSQLAlchemy source snapshotを実行できる。
- product HTML、Next、all-domain orchestration、SQLAlchemy diff、unrelated refactorを追加しない。

## スコープ

### 対象

- `snapshot --domain sqlalchemy` のwhole/targeted working-tree use case。
- static declarative base/class/Table/column/constraint/index/FK/relationship/inheritance/association recognition。
- SQLAlchemy-owned immutable model、selection、redaction、semantic JSON、PlantUML。
- existing CLI/config/source/outcome/budget/manifest/writer/stream/schemaへの最小additive extension。
- unit/integration/acceptance/security/contract/packaging regression、fixtures/goldens、contract docs。

### 対象外

- SQLAlchemy diff、matching、ghost rows、impact over before/after endpoints。
- DB connection/reflection、engine/session、runtime mapper、automap、imperative mapping、Alembic execution、migration parsing。
- SQL expression evaluation、check/default/join bodyの保存、literal opt-in。
- non-SQLAlchemy ORM、Next.js、domain省略/all-domain orchestration、cross-domain relation。
- product HTML、browser UI、remote execution、native Windows、public plugin ABI。
- `pyclassuml`、`tree-git-diff`、SQLAlchemy packageへのruntime dependency。

## 受け入れ条件

| ID | 観測可能な完了条件 | acceptance evidence |
| --- | --- | --- |
| I03-AC-001 | modern/classic declarative class、module-level Table、exact `__table__` bindingをoffline CLIでtable snapshotへ変換する。 | I03-AT-001 |
| I03-AC-002 | column、PK/unique/check/index/FK/relationship/inheritance/associationをclosed row/relation kindで出力し、identity/order/dedupe contractを満たす。lossy unnamed check/indexはfull internal AST declaration spanでsame-line siblingを区別し、各distinct conflict occurrenceの`CSV-SA-009`を保持する。ordinary non-lossy exact duplicateだけをcanonicalizeする。 | I03-AT-002 |
| I03-AC-003 | path/module/class target、target union、upstream/downstream depth、frontier、explicit missing/ambiguous targetをcontractどおり処理する。 | I03-AT-003 |
| I03-AC-004 | no evidenceはnot_applicable、safeなabstract base等のapplicable zero-tableはcomplete empty payload、isolated failureはpartial_safe、safe subsetなし/absence証明不能/collisionはpayload_unavailableとし、published file setとexitを一致させる。lossy identity conflictはsafe tableを残せる場合`partial_safe`とする。 | I03-AT-004 |
| I03-AC-005 | DB/import/build/plugin execution trapが発火せず、default/URL/token/check/join/source/absolute pathが全output channelへ存在しない。type parameterをconstructorごとに一件だけ数え、redaction rule/countをJSON、PlantUML、manifestで一致させる。underscore/quote/dotを含むuser componentとrenderer-owned separatorをinjectiveに分離し、PlantUML label/component split collisionを生じさせない。 | I03-AT-005 |
| I03-AC-006 | declaration order、import alias、filesystem enumeration orderを変えてもsemantic ID/array orderが安定し、same-input rerunの全Artifact bytes/SHA-256が一致する。 | I03-AT-006 |
| I03-AC-007 | default 501 selected tablesはpayload_unavailable/exit 3/payloadなし/manifest countあり、valid 600 overrideは成功し、invalid overrideとdiff-only optionはexit 2/Artifactなしとなる。 | I03-AT-007 |
| I03-AC-008 | stdout selectorのvalid/invalid/duplicate/domain/format、available exact bytes、not_applicable/payload_unavailable/fatal/interrupt result、selectorなしsummaryをtable-drivenに満たす。 | I03-AT-008 |
| I03-AC-009 | semantic/manifest/diagnostic/summary/stdout schemaがSQLAlchemy snapshotをclosed unionとして受理し、既存Python goldensとdiff contractsをbyte-for-byte維持する。 | I03-AT-009 |
| I03-AC-010 | full unit/integration/acceptance/security/package suite、ruff、mypy、offline build、SpecDock validate、minimum/latest/macOS CIがruntime dependency 0件で成功する。 | I03-AT-010 |

次のacceptance fixtureはexact outcomeを固定する。

- `lossy_expression_identity_conflict`: one safe tableとone safe columnに、同じredaction categoryへ縮退するdistinct unnamed checkを2件、同じordered expression-category termsへ縮退するdistinct unnamed indexを2件置く。expectedはdomain `incomplete / partial_safe`、exit 3、safe payload + manifest、`CSV-SA-009` exactly 4件、final `members`はsafe column exactly 1件で`check`/`index` rowは各0件である。同じAST declarationを複数passで再発見したevidenceは追加row/diagnosticを生まない。separate non-lossy exact duplicate caseは`complete`のままrow exactly 1件へcanonicalizeする。
- `lossy_same_line_siblings`: one safe tableとone safe columnを保ち、同じredaction categoryへ縮退する2件のunnamed `CheckConstraint`と、同じordered expression-term identityへ縮退する2件のunnamed expression `Index`のouter construction callを同一物理行へ置く。4件はstart/end UTF-8 byte columnが異なるdistinct occurrenceであり、expectedはdomain `incomplete / partial_safe`、exit 3、safe payload + manifest、distinct occurrence symbolを持つ`CSV-SA-009` exactly 4件、final `members` exactly 1件、`check` row 0件、`index` row 0件である。public source locationとdiagnostic schemaにはbyte column fieldを追加しない。
- `type_parameter_redaction`: other redacted boundaryを持たないtableで`String(255)`と`Numeric(10, 2, asdecimal=True)`を使い、各constructorの`type.parameters`をexactly 1件、run totalを`redacted_values=2`とする。semantic JSON、PlantUMLの`rule_version`/`redacted_values` metadata、manifest domain coverageがexactly同じrule/countを持ち、各column lineが`type_parameters=[redacted:literal]`を一度だけ持つ。
- `plantuml_escape_collision`: user label `"`は`_U0022_`、user label `_U0022_`は`_U005F_U0022_U005F_`となり、golden bytes上でdistinctである。raw user underscore/quoteはlabelへ通さず、renderer-owned syntaxは変更しない。
- `plantuml_component_split_collision`: `(schema=a, table=b.c)`と`(schema=a.b, table=c)`を同じsnapshotへ置き、entity/target displayがそれぞれexact `a.b_U002E_c`と`a_U002E_b.c`になってdistinctであることを固定する。input dotはrawで通さず、二componentを結ぶrenderer-owned separator `.`だけをliteralで出す。

- `I03-AC-001`〜`I03-AC-010` がすべて成立し、Requirement→Design→Plan→acceptance→test traceにgapがない場合だけ実装ready/completeと判定する。
- Issue 7へ渡すのはimmutable SQLAlchemy snapshot model、public semantic JSON/PlantUML/manifest contract、stable IDs、coverage/diagnosticsである。diff implementationは渡さない。

## unresolved blockers / owner decisions

現行 repository、親 canonical contract、accepted ADR、Issue 4/5 public implementationから、本 Issue の実装を開始するために残るmaterial owner decisionはない。

実装中に次のいずれかが必要になった場合はDesign外の判断であり、code/schemaを先に変更せずblockerとして停止する。

- target codeまたはSQLAlchemy runtimeのimport/execution、DB接続、Alembic実行。
- 新しいconfig key、runtime dependency、public plugin ABI、SQLAlchemy diff、HTML、all-domain orchestration。
- schema/table identityへmodule/pathを混ぜる、dynamic expressionを推測する、literalを公開する。
- existing Python snapshot/diff public bytesまたはGit/output safety invariantの変更。

## 制約・前提

- initial platformはmacOS/Linux、Python 3.12+、Git 2.39+。native Windowsは対象外。
- runtime network accessを要求しない。Git auto-fetch/lazy-fetch、external diff/textconv、target buildを行わない。
- direct/indirect dependencyはexisting lockfile/license inventoryと一致させる。本Issueでは新規dependencyを想定しない。
- Artifactはreview entry pointであり、database schema、migration history、runtime mapperの完全な代替ではない。coverageとdiagnosticを伴わないfalse successを許可しない。
