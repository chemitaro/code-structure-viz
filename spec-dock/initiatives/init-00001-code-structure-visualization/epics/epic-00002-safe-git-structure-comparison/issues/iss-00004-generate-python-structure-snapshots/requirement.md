---
種別: 要件定義書（Issue）
ID: "iss-00004"
タイトル: "Generate Python Structure Snapshots"
関連GitHub: ["#4"]
package_sequence_key: "ISSUE-01"
状態: "draft"
最終更新: "2026-08-25"
親: ["epic-00002", "init-00001"]
---

# iss-00004 Generate Python Structure Snapshots — 要件定義

詳細: [Requirement Guide](../../../../../../docs/authoring/requirement.md)

## 目的

coding agent または人間が、対象 Git repository の Python application code を import・bytecode compile・実行せず、run 開始時に固定した working-tree source を AST-only parser で解析し、class 構造を versioned semantic JSON と PlantUML で取得できる。

利用者 story: coding agent として、repository 全体または明示した path/module/class 周辺の class、member、relation、解析 coverage を、source 本文を外部 Artifact へ複製せず、決定的な machine-readable Artifact と人間向け図として取得し、実装判断の入力にしたい。

この Issue は技術 layer の完成ではなく、次の一つの vertical outcome を所有する。

```text
snapshot CLI request
  -> usage/config/core preflight
  -> immutable working-tree SourceView
  -> Python 3.12 grammar の static AST analysis
  -> whole/targeted semantic selection
  -> entity budget
  -> semantic JSON / PlantUML / run manifest
  -> stdout/stderr/exit/publication acceptance evidence
```

## 正本・権威・現行状態

### canonical authority

- stable package key は `ISSUE-01`、SpecDock Issue ID は `iss-00004`、GitHub Issue は `#4` である。
- 本 Issue の canonical 文書は、この directory 直下の `requirement.md`、`design.md`、`plan.md` である。
- 親 `init-00001` / `epic-00002` の canonical R/D/P と accepted ADR を変更せず、その制約内で本 Issue の未確定事項を閉じる。
- `artifacts/` 配下、添付、説明 HTML、research、interview、draft、historical Artifact は evidence であり、canonical 文書ではない。矛盾時は accepted ADR、親 canonical R/D/P、本 Issue canonical R/D/P の整合する現行契約を採る。
- canonical 文書自身へ一時的な branch tip SHA を固定しない。実装開始時は repository、branch、HEAD、configured upstream、root `AGENTS.md` の有無を再検証する。

### noncanonical Artifact から明示的に置き換える契約

次の旧記述は本書の現行契約ではない。

| 旧・曖昧な記述 | 本 Issue の canonical contract |
| --- | --- |
| actual SpecDock Issue ID は adoption 時に割り当てる | actual ID は `iss-00004`、stable key は `ISSUE-01`。両者を混同しない。 |
| Requirement は `I01-REQ-001`〜`006` | stdout contract を所有する `I01-REQ-007` を含む。 |
| entity 500超過は単に nonzero | default 500、501以上は `incomplete` / `payload_unavailable`、exit 3、affected payloadなし、safe manifestあり。positive `--max-entities` でのみ明示拡張できる。 |
| parse/read failure では成功 Artifact を一律保持 | `partial_safe` の全条件を満たす場合だけ incomplete payload を保持し、それ以外は `payload_unavailable` とする。 |
| planned path/symbol は参考候補 | canonical Design/Plan に列挙した path/symbol を本 Issue の実装 target とし、変更が必要なら code より先に Design/Plan を更新する。 |
| HTML説明が製品出力の参考になる | specification HTML は evidence に限る。製品 command、format、schema、renderer、publication として HTML を予約・実装しない。 |

### verified baseline から直接確認できる Current

- production package、product CLI、Python adapter、public schema、acceptance fixture、product lockfile は未実装である。
- root CI は SpecDock workspace validation のみを持つ。
- 本 Issue の declared dependency は **なし**。unfinished sibling の内部実装へ依存してはならない。
- `.meta.json` は SpecDock managed metadata であり、本 Issue で編集しない。

## 親 requirement / accepted ADR との境界

| 親または ADR | 本 Issue が維持する境界 |
| --- | --- |
| EPIC-REQ-001 / Vertical Issue Slicing | CLIからArtifactとacceptanceまでを単独で完了する。contract-only、SourceView-only、parser-only、renderer-onlyの完成をIssue完了としない。 |
| EPIC-REQ-002 / Static Analysis Safety Boundary | target codeを実行せず、Gitをread-onlyで扱い、run-start working treeをimmutable SourceViewへ固定する。 |
| EPIC-REQ-003 / Domain Adapter Boundaries | common layerはlifecycle/config/diagnostic/source/artifactに限定し、Python identity/member/relation/selection/renderingはPython adapterが所有する。 |
| EPIC-REQ-004 / Agent First Artifact Contract | per-domain semantic JSON、Python PlantUML、`run-manifest/v1`、relative path、SHA-256、redaction、determinism、no-overwriteを実装する。 |
| EPIC-REQ-005 | `complete` / `not_applicable` / `incomplete`、exit 0/1/2/3/130、default 500 entity gate、targeted depth 1+1を実装する。changed-path gateはdiff専用である。 |
| EPIC-REQ-006 | macOS/Linux、Python 3.12+、Git 2.39+、lock/license/offline/minimum/latest CIを本sliceに必要な範囲で成立させる。Nodeは導入しない。 |
| EPIC-REQ-008 / Exclude Product HTML Reports | product HTML command/format/schema/UI/publicationを作らない。 |
| EPIC-REQ-009 | closed stdout selector、exact-byte copy、typed unavailable result、selectorなしsummary、stderr diagnostic、usage no-publicationを実装する。 |
| Independent Product Ownership | `pyclassuml` / `tree-git-diff` をruntime/package/CLI dependencyにせず、旧CLI互換を作らない。 |
| Named Git Comparison Endpoints / Dual Snapshot Semantic Diff | endpoint/diff contractを本Issueでは実装しない。snapshotにdiff-only optionが来た場合の拒否だけを実装する。 |

## 観測可能な要件

| ID | 観測面 | 要件 |
| --- | --- | --- |
| I01-REQ-001 | vertical CLI outcome | `code-structure-viz snapshot --domain python` が、safe source acquisition、Python analysis、requested payload、manifest、stream、exitまでを一回のrunとして完結する。 |
| I01-REQ-002 | CLI/config/source selection | CLI grammar、重複、default、config precedence、path safety、whole source scopeを本書のclosed contractどおりに検証する。 |
| I01-REQ-003 | SourceView/target resolution | run-start working treeをrepository外へ固定し、valid commitと真正なunborn branchをread-onlyで一意判定する。明示targetはsource/class不在より優先して解決し、未解決・曖昧・failed seedを必ず`payload_unavailable`にする。 |
| I01-REQ-004 | Python semantic behavior | class identity、nested class、field/method/property/decorator、inheritance/composition/typed/import dependency、safe type/signatureをPython-owned modelで表し、member/relationのexact sort tuple、dedupe winner、type text grammarに加え、annotation `TypeReference`の抽出・採用・解決順位・builtin/typing/type-parameter除外を一意にする。 |
| I01-REQ-005 | Artifact/stream contract | exact filename、canonical JSON bytes、manifest descriptor、stdout exact bytes/result/summary、diagnostic cardinality/contextを含むstderr JSONL、parameter/escape/visual-dedupeとclassless selected module layoutまで閉じたPlantUML vocabularyをversioned contractとして提供する。 |
| I01-REQ-006 | failure/budget/safety/determinism | whole-mode absence、explicit-target failure、isolated failure、unsafe/global failure、non-UTF-8 Git path、invalid HEAD、entity overrun、collision、drift、interruptを区別し、target execution・canonical path捏造・secret/absolute path leak・truncation・overwriteを許さない。 |
| I01-REQ-007 | implementation acceptance | repository-owned package、lockfile、schema/docs、fixture/golden、unit/integration/acceptance/security/packaging test、minimum/latest CIがclean checkoutで再現できる。JSON Schemaはtest/build-time contract gateで検証し、runtimeはschema loader/validatorと第三者runtime dependencyを持たない。 |

## CLI contract

### command grammar

本 Issue が登録するproduct commandは次の一つだけである。

```text
code-structure-viz snapshot \
  --repo PATH \
  --output-dir PATH \
  --domain python \
  [--config PATH] \
  [--target TARGET]... \
  [--upstream-depth NON_NEGATIVE_INT] \
  [--downstream-depth NON_NEGATIVE_INT] \
  [--format semantic-json|plantuml]... \
  [--max-entities POSITIVE_INT] \
  [--stdout manifest|python:semantic-json|python:plantuml]
```

- `snapshot`、`--repo`、`--output-dir`、`--domain python` は必須である。
- domain省略によるall-domain orchestrationは `ISSUE-07` の責務であり、本Issueでは省略、`all`、`sqlalchemy`、`next` をusage errorにする。
- `diff` subcommandを登録しない。`snapshot` と `--from`、`--to`、`--pr-target`、`--max-changed-paths` のいずれかを併用した場合は、unknown optionへ丸めず `diff_option_on_snapshot` のusage errorにする。
- positional target、boolean `--stdout`、option alias、大小文字違い、短縮形を受理しない。
- `--repo`、`--output-dir`、`--domain`、`--config`、各depth、`--max-entities`、`--stdout` はそれぞれ高々1回。重複は最後の値を採らずexit 2とする。
- `--target` は0回以上、`--format` は1回以上の反復を許す。同一normalized targetは一つへ畳み、同一formatの重複はusage errorとする。
- `--format` 未指定時は `semantic-json` と `plantuml` の両方。指定順にかかわらずresolved orderは `semantic-json`、`plantuml` の順である。
- depthのdefaultはupstream/downstream各1。CLIでdepthを明示する場合は少なくとも一つの`--target`を必要とし、whole modeでの明示depthはusage errorとする。
- `--max-entities` は1以上のbase-10 integerだけを許す。zero、negative、符号だけ、float、scientific notation、leading/trailing whitespaceを受理しない。
- `--help` と `--version` はmeta operationであり、source acquisitionとpublicationを行わずexit 0。`--version` は `code-structure-viz <package-version>\n` の一行とする。

### path/preflight

- relative `--repo` / `--output-dir` / `--config`はinvocation current working directoryを基準に一度だけ解決する。
- `--repo` は存在するordinary directoryで、`git rev-parse --show-toplevel`のcanonical real pathと一致するworking-tree rootでなければならない。nested path、bare repository、non-Git directoryは受理しない。
- HEADはDesignのread-only四command判定で`commit`または`unborn`へ分類する。`HEAD^{commit}`が40桁または64桁のfull object IDへ解決できた場合だけcommitとする。解決不能時は`symbolic-ref`の出力を正規化せずround-trip可能なstrict UTF-8として読み、`refs/heads/*`であることと`check-ref-format`成功を確認した後、そのexact refが`show-ref --verify --quiet`で不存在の場合だけunbornとする。unbornではmanifestの`head_commit`を`null`とし、implicit baseを探索しない。
- ref形式不正、refが存在するのにcommitへpeelできない、detached/malformed HEAD、missing/corrupt object、Git command/protocol errorはunbornへ丸めず`CSV-REPO-002`のrun-level fatal、exit 1、Artifact 0件とする。Git stderr文字列の一致で分類しない。
- `--output-dir` はrun開始時に存在してはならず、そのparentは存在するordinary directoryでなければならない。
- symlinkを解決した`--output-dir`は`--repo`と同一または配下であってはならない。明示指定でもtarget repositoryへArtifactを作らない。
- output destination collision、unsafe parent、cross-device publication不能、write permission不足はrun-level fatal、exit 1、Artifact 0件とする。

### examples

```bash
code-structure-viz snapshot --repo . --output-dir /tmp/csv-python --domain python
code-structure-viz snapshot --repo . --output-dir /tmp/csv-order --domain python \
  --target path:src/domain/order.py --upstream-depth 1 --downstream-depth 1
code-structure-viz snapshot --repo . --output-dir /tmp/csv-target --domain python \
  --target module:domain.order --target class:domain.order.Order --format semantic-json
code-structure-viz snapshot --repo . --output-dir /tmp/csv-stdout --domain python \
  --format semantic-json --stdout python:semantic-json
```

## config contract

### discovery and precedence

1. built-in defaultを作る。
2. `--config PATH`があれば、その一つだけを読む。repository rootの`.code-structure-viz.toml`とはmergeしない。
3. `--config`がなく、`<repo>/.code-structure-viz.toml`があれば読む。
4. CLIのdepth/max-entitiesを最後に上書きする。

user-global config、environment variable、current working directoryの別config、implicit profileを読まない。explicit configとrepository configはいずれもordinary non-symlink fileだけを許し、explicit configはrepository外でも明示指定なら読める。unknown table/key、duplicate TOML key、型不正、unsafe path、schema不一致はexit 2、stdout空、Artifact 0件とする。unknown keyのraw spelling、quoted spelling、NFC value、dotted pathはstdout、stderr、manifest、logへ出さない。`CSV-CONFIG-003`のmessageはexact constant `Configuration contains an unknown key.`、`domain/path/symbol/line`はすべて`null`である。複数unknown keyから最初のfailureを選ぶ比較値はprocess内だけで使用し、diagnosticへ埋め込まない。

### exact v1 shape

```toml
schema = "code-structure-viz.config/v1"

[python]
source_roots = ["src", "."]
include = ["**/*.py"]
exclude = []

[traversal]
upstream_depth = 1
downstream_depth = 1

[limits]
max_entities = 500
```

- `schema` は必須でexact match。
- `python.source_roots` はnon-emptyなrepository-relative POSIX directoryのarray。`"."`を許す。absolute、`..`、backslash、empty、repository外symlinkを拒否する。
- `python.include` はnon-empty、`python.exclude` はempty可。patternはrepository-relative POSIX globで、`*`は一segment内、`**`はzero以上のsegment、`?`は一文字。`!`、character class、brace expansion、absolute、backslashを許さない。excludeが常に優先する。
- built-in defaultは上記exact value。暗黙のvendor/generated directory推測を追加しない。Gitが返すtracked fileと`--exclude-standard`を通るuntracked fileにconfig scopeを追加適用する。
- source rootの存在判定では最長matching rootを優先する。built-inの`src`が存在しなくてもerrorにしない。explicit configに存在しないrootがある場合はconfig errorとする。
- resolved configとそのcanonical SHA-256、各値のsource `builtin|repository|explicit|cli` をmanifestへ記録する。absolute config pathは記録しない。

## SourceView と source acquisition contract

- snapshotはrun-start working tree一つだけを解析する。commit endpoint、merge-base、FileChangeSet、ChangedPathAdmissionGateを構築・参照しない。
- Git 2.39以上を要求し、target repositoryに対するGit commandはDesignのread-only allowlistだけを使用する。fetch、checkout、reset、stash、clean、commit、update-ref、worktree add/remove、submodule updateを実行しない。
- candidateはtracked fileとstandard ignoreを通るuntracked fileの和集合から、存在する`.py`だけを取り、configのsource root/include/excludeを適用する。`.pyi`、deleted working-tree file、directory、special fileは対象外。
- Gitが返したNUL-delimited path bytesは各entryをstrict UTF-8 decodeしてからUnicode NFC、POSIX `/`へ正規化する。**一件でもstrict UTF-8 decodeできないpathがあれば、canonical path、replacement character、surrogate escape、raw-byte hash、ordinalを発明しない。SourceViewを構築せず、`CSV-SOURCE-003`一件、run-level fatal、exit 1、stdoutのfatal contract、final manifestを含むArtifact 0件で停止する。**
- strict UTF-8 decode後にNFC normalization collision、またはcase-insensitive filesystemで同一inodeへ複数のcanonical logical pathが対応する場合は`CSV-SOURCE-004`のunsafe path identity failureとする。representableなcollision groupはdomain `payload_unavailable`としてsafe manifestへ記録できるが、一方をwinnerとして解析しない。
- source fileは読取り前後のmetadataとbytesを確認し、output parent内のprivate staging rootへcopyしてSHA-256を固定する。domain analyzerはmutable repository pathを再読せず、immutable SourceViewのbytesだけを受け取る。
- symlink `.py` はlinkとresolved targetを検査する。repository外、non-regular target、cycleはunsafe sourceとして`payload_unavailable`。repository内ordinary fileだけをlogical path identityのままfreezeできる。
- SourceView fingerprintはschema、endpoint kind `working-tree`、Designで一意判定したrun-start HEAD commitまたはnull、sorted successful file descriptor（path、kind、resolved repository-relative targetまたはnull、size、SHA-256）、sorted representable acquisition failure descriptor（path、stage、diagnostic code）のcanonical JSON bytesのSHA-256である。non-UTF-8 path fatalではSourceViewもfingerprintも存在しない。
- initial freeze完了時とpublication直前に、HEADと同じsource scopeのfingerprintを再確認する。drift時はrun-level fatal、exit 1、staging cleanup、final manifestを含むArtifact 0件とする。
- target 0件のwhole modeでPython source candidateが0件の場合だけdomain `not_applicable`、exit 0、run manifestだけを公開する。empty semantic JSON/empty PlantUMLを捏造しない。
- 明示targetが一件以上あるtargeted modeは`not_applicable`へ遷移しない。Python source candidateが0件でもtarget resolution failureを優先し、各targetを`CSV-PY-006`へ対応させてdomain `incomplete` / `payload_unavailable`、exit 3、safe manifest onlyとする。
- Python sourceが存在し全fileにclassが0件の場合、target 0件のwhole modeはdomain `complete`、entity count 0のsemantic JSONと「classなし」を示すPlantUMLをrequested formatに従って公開する。明示class/module/path targetが未解決ならこのzero-class completeよりtarget failureを優先する。

## target resolution contract

### selector grammar

- `path:<repo-relative-posix-.py-path>`: exact logical SourceView path一件。
- `module:<dotted-module-name>`: exact normalized module一件。
- `class:<dotted-module>.<qualified-class-name>`: discovered moduleの最長prefixをmodule、残りをqualified class nameとしてexact解決する。

syntaxが不正、absolute/backslash/`..`、`.py`以外、empty segment、Python identifierでないmodule/class segmentはusage error、exit 2、Artifact 0件とする。

### module identity

- source rootからのrelative pathを使い、`.py`を除き、`/`を`.`へ変換する。
- `pkg/__init__.py`は`pkg`、source root直下の`__init__.py`は`__init__`とする。
- namespace packageを許し、`__init__.py`の存在をmodule成立条件にしない。
- path componentはUnicodeの`str.isidentifier()`を満たしPython keywordでないこと。満たさないfileは解析失敗coverageへ残す。
- 同じmodule identityへ複数fileが解決した場合、該当fileを安全subsetから除外する。requested seedに関わるcollisionは`payload_unavailable`、それ以外は条件を満たせば`partial_safe`。

### resolution/outcome

判定順は次に固定し、`not_applicable`とexplicit target failureを交換しない。

| request mode | scoped Python source / class evidence | target resolution | domain outcome |
| --- | --- | --- | --- |
| whole（target 0件） | source 0件 | 実行しない | `not_applicable`、payloadなし、manifest only、exit 0 |
| targeted（target 1件以上） | source 0件 | 全target未解決 | `incomplete/payload_unavailable`、targetごとの`CSV-PY-006`、manifest only、exit 3 |
| whole | source 1件以上、解析成功、class 0件 | 実行しない | `complete`、zero-class semantic/PlantUML、exit 0 |
| targeted | source 1件以上でもrequested path/module/classが0件、曖昧、またはfailed seedだけへ対応 | failure | `incomplete/payload_unavailable`、manifest only、exit 3 |
| targeted | 全targetが一意なsafe seedへ解決 | success | selection/coverage/budgetに従い`complete`または`partial_safe` |

- target 0件はwhole modeで、safeに解析できた全classを含める。
- targetはcanonical unionとして扱い、path/module targetはそのmoduleと全class、class targetはそのclassをseedにする。
- syntactically valid targetが0件へ解決、複数へ曖昧解決、またはfailed seed fileだけへ解決した場合はusage successやnot_applicableへせず、domain `incomplete` / `payload_unavailable`、exit 3、safe manifestのみとする。複数targetのうち一件でも失敗した時点で部分target成功へ縮退しない。
- unresolved targetはrequestに残し、Designのtarget context規則で`CSV-PY-006`を一target一件生成する。NFC/case path identity collisionに対応するpath target、module collisionに対応するmodule/class target、class identity collisionに対応するclass targetは、group diagnosticに加えて`CSV-PY-007`を一target一件生成する。
- relation directionはdependent `source` からdependency `target`。downstreamはforward、upstreamはreverse。
- graph nodeはmoduleとclass。classとdeclaring moduleのmembershipはdepthを消費しない。inheritance、composition、typed dependency、import dependencyの一辺がdepth 1を消費する。
- module nodeを選択した場合はそのmoduleの全class、class nodeを選択した場合はそのdeclaring moduleを同じdepthでselectionへ含める。
- local relationのnext-hopがdepth外ならcoverage frontierへ記録し、payloadへentityを追加しない。`depth_limit` frontierは正常なselection境界でありdiagnosticを生成しない。external/unresolved relationはpayloadへsafe symbolic referenceとして残すがtraversalしない。
- parse/read failureのfileはupstream候補を隠し得るため、targeted snapshotでもcoverage failureへ残す。requested seedが成立し、残るsubset・frontier・diagnosticが安全な場合だけ`partial_safe`にできる。

## Python semantic contract

- v1が保証するtarget grammarはPython 3.12。Python 3.12以上のruntimeで`ast.parse(..., feature_version=(3, 12), type_comments=False)`相当を使い、3.13以降固有syntaxを成功扱いしない。
- target moduleをimportせず、`py_compile`、`compileall`、code objectを作る直接`compile`、`exec`、`eval`、`runpy`、plugin loading、entry point loading、migration/build command、target subprocessを呼ばない。`ast.parse`内部の`PyCF_ONLY_AST`相当のAST-only parseだけは許可し、bytecodeを生成・実行しない。
- `# type:` type commentはcomment-only changeをsemantic changeへ昇格させないためPython semantic v1では無視する。annotationはPython syntax上のannotation nodeだけから得る。
- entityは`Module.body`または別`ClassDef.body`のdirect statementである`ClassDef`。module/class levelの`if`/`try`/loop等control-flow block内、function/lambda/comprehension内のclassへは降りず、safe diagnostic/coverageに残す。
- class identityは`normalized module path + lexical qualified class name`。nested classは`Outer.Inner`のようにouter classを含む。
- 同じclass identityへ複数の`ClassDef`が解決した場合は一方を勝たせずcollisionとして除外する。requested class/module/path seedに関われば`payload_unavailable`、whole/非seed targetで他のsafe entityがあれば`partial_safe`、safe entityがなければ`payload_unavailable`。
- memberは次を扱う。
  - class bodyの`Assign` / `AnnAssign`によるfield。simple nameとtuple/list destructuring内のsimple nameを対象とし、default expression/literalは保持しない。`AugAssign`と`Delete`は新規field declarationにしない。
  - method body内の`Assign` / `AnnAssign` / `AugAssign`で、attribute targetがliteral receiver名`self`または`cls`の`self.<name>` / `cls.<name>`であるsyntactic assignmentをinstance/class fieldとして扱う。tuple/list target内も同ruleで走査し、body自体は保持しない。
  - class body直下のsync/async method。method内field検出は`if`/`for`/`while`/`try`/`with`/`match`等のcontrol-flow bodyへ再帰するが、nested function、lambda、nested class、comprehensionのscopeへは降りない。
  - `property`、`<name>.setter`、`<name>.deleter` accessor。
  - class/member decoratorのsafe symbolic callee名とcall有無。argument/keyword/literalは保持しない。
- signatureはparameter name/kind/annotation/`has_default`、async、return annotationを構造化する。default値、docstring、comment、function bodyは保持しない。
- type expressionはDesignのclosed grammarだけをcanonical stringへ変換する。tupleは`()` / `(T,)` / `(T1, T2)`、subscript argumentは`Base[T1, T2]`、unionはnested `|`をleft-to-rightにflattenして`A | B | C`とし冗長parenthesisを保持しない。literal/Annotated metadataはclosed redaction ruleで`?`へ変換し、unsupported annotation siteは一site一件の`CSV-PY-011`を生成する。

### annotation TypeReference contract

annotationからrelation候補へ変換する`TypeReference`はsource textを保持せず、supported ASTのsymbolだけから作る。抽出とrelationへの採用は次のclosed tableに従う。

| annotation shape | reference extraction | relationへの採用 |
| --- | --- | --- |
| `Name` / dotted `Attribute` | current roleでsafe symbol一件を抽出する。annotation rootのdefault roleは`head`、`Subscript` slice配下は`argument` | fieldでは`composition`、parameter/return/propertyでは`typed_dependency`、inheritance baseではそのbase expressionのouter `head`だけを`inheritance` |
| symbolic-base `Subscript` | baseを`head`、sliceをleft-to-rightに`argument`として再帰抽出。slice `Tuple`はargument container | field/parameter/return/propertyはretained `head`と`argument`を採用。inheritanceはouter base `head`だけを採用しgeneric argumentはv1 relationにしない |
| tuple / `A | B` | element/union leafをleft-to-rightに再帰抽出 | site kindのruleで各retained referenceを採用 |
| alias-resolved `Literal[...]` | helperと全literal argumentをreferenceにしない | relationなし。type textだけarityを`?`で保持 |
| alias-resolved `Annotated[T, ...]` | helperとmetadataをreferenceにせず、first argument `T`だけ再帰抽出 | `T`のretained referenceだけをsite kindのruleで採用 |
| `None` / Ellipsis / literal / unsupported subtree | referenceなし | relationなし。unsupported siteはtype text `?`と`CSV-PY-011` |

`Literal` / `Annotated` special form判定はgeneric `Subscript` extractionより先に行う。baseのfirst segmentにexact `ImportBinding`があれば一度だけ展開し、なければoriginal dotted baseをそのままcanonical baseとする。canonical baseがexact `typing.Literal` / `typing_extensions.Literal` / `typing.Annotated` / `typing_extensions.Annotated`のいずれかである場合だけspecial formとする。未importのunqualified `Literal` / `Annotated`を推測でspecial formにしない。

除外はresolutionより前後のevidenceを使い、次へ閉じる。

- lexical PEP 695 type parameter、およびsimple name assignmentのcalleeがexplicit alias resolutionで`typing.TypeVar`、`typing.ParamSpec`、`typing.TypeVarTuple`または同じ`typing_extensions`名へ解決するlegacy type parameterはrelation候補から除外する。call argument/literalは読まない。
- explicit local classまたはimport bindingに解決しないunqualified symbolが次のexact `builtin-annotation-name-v1`に一致する場合は除外する。

```text
BaseException, Exception, bool, bytearray, bytes, complex, dict, float,
frozenset, int, list, memoryview, object, range, set, slice, str, tuple, type
```

- alias展開後またはoriginal dotted symbolがexact prefix `builtins.`、`typing.`、`typing_extensions.`を持つ場合、そのsymbol自体はrelation targetにしない。subscript argumentは上表どおり独立に処理する。
- 除外referenceはrelation、coverage frontier、`CSV-PY-008`を生成しない。

retained symbolは**candidate construction**と**classification**の二段階で解決する。source orderやdictionary iterationで分岐しない。

candidate construction:

| priority | evidence / action | candidate |
| --- | --- | --- |
| 0 | enclosing class chainをlongestからemptyへ縮め、`<current-module>.<prefix>.<spelling>`のexact classを探す。同じmoduleのtop-level classはempty prefixで探す | exact internal class candidate。ここで成立した場合は後続候補を見ない |
| 1 | first segmentにexact explicit `ImportBinding`がある | binding canonical name + remaining segments。`explicit_import=true` |
| 2 | original dotted spellingをlongest exact module prefix + qualified remainderへ分割できる | original absolute candidate |
| 3 | 上記なし | original normalized dotted spelling candidate |

candidate construction前に、original spellingがsingle segmentでactive lexical type parameter registryにmatchした場合は即時excludedとし、candidateを構築しない。その他のcandidateへclassificationを次の順で適用する。

| order | predicate | public result |
| --- | --- | --- |
| A | candidateがexact SourceView class | `resolution=internal`, `kind=class`, `id=<class-id>`, `name=<module>.<qualified_name>` |
| B | candidateがmodule bindingそのものかつexact SourceView module | `resolution=internal`, `kind=module`, `id=python:module:<module>`, `name=<module>` |
| C | A/Bではなく、unqualified exact builtin set、またはcanonical prefix `builtins.` / `typing.` / `typing_extensions.`にmatch | excluded。relation、frontier、diagnosticなし |
| D | `explicit_import=true` | `resolution=external`。module bindingそのものは`kind=module`、suffixまたはsymbol bindingは`kind=symbol`、`id=null`, `name=<alias-expanded absolute dotted name>` |
| E | その他 | `resolution=unknown`, `kind=symbol`, `id=null`, `name=<original normalized dotted spelling>`。current module prefixを補わない |

この順序により、same-module/local class `list`はAでinternalになり、`from typing import Generic as G`の`G`はCで除外され、`from ext.models import Foo as F`の`F`はDでexternalになる。unknownだけがoccurrence単位の`CSV-PY-008`と`unresolved_reference` frontierを生成し、explicit import evidenceを持つexternalはwarningにしない。

closed example:

| annotation/import context | retained relation target |
| --- | --- |
| `field: Missing` | unknown symbol `Missing` + `CSV-PY-008` |
| `field: list[Foo]`、same-module `Foo` classあり | `list`は除外、internal class `<module>.Foo`だけ |
| `class Box(Generic[T])`、`Generic`は`typing.Generic` alias、`T`はrecognized type parameter | relationなし |
| `from ext.models import Foo as F`; `field: F` | external symbol `ext.models.Foo`、warningなし |

- relationは以下の4種だけである。
  - `inheritance`: classからbase class/symbol。
  - `composition`: owner classからfield annotation内class/symbol。
  - `typed_dependency`: owner classからmethod/property parameter/return annotation内class/symbol。
  - `import_dependency`: importing moduleからimported module。
- import alias、relative import、namespace moduleを静的に解決する。star/conditional/dynamicな解決不能部分を事実として補完せず、external/unknown referenceとcoverageへ残す。annotation symbolは上記TypeReference tableのpriorityだけで解決し、same-module/nested/import aliasの順位を実装都合で入れ替えない。
- entity、member、relationはDesignのexplicit enum rankとexact tupleでsortする。member declaration ordinalはfull source locationとsyntactic origin rankのcanonical orderで割り当て、merged fieldのpublic rangeはcanonical first occurrenceを採る。relation identityが同じ複数occurrenceはfull source locationとorigin rankからなるcanonical occurrence key最小のrangeをwinnerにし、collector/source iteration orderで勝者を変えない。same occurrenceにcollectorが矛盾するpayloadを付けた場合はwinnerを発明せずinternal invariant failureとする。
- semantic JSONはidentityの異なるrelationを保持する。PlantUMLで同じkind/source/target/fixed labelへ落ちる複数relationだけをvisual lineとして一行へ畳み、semantic relationを削除しない。

## Artifact / stdout / stderr contract

### exact published paths

`--output-dir`のatomic publication後に存在できるfileはrequested outcomeに応じて次だけである。

| path | 条件 |
| --- | --- |
| `python.snapshot.semantic.json` | `semantic-json` requestedかつpayload available |
| `python.snapshot.puml` | `plantuml` requestedかつpayload available |
| `run-manifest.json` | usage/run-level fatal/handled interruptではなく、valid core runのdomain outcomeが確定した場合 |

manifestは自身のdigestを内包しない。semantic/PlantUML descriptorだけを持ち、自己参照digestを発明しない。

### canonical bytes

- JSONはUTF-8、BOMなし、LF、schema-defined field order、配列のcanonical sort、余分なspaceなし、末尾LFちょうど1つ。runtime serializerはtyped constructor、closed field/type/nullability/order invariant、structural redactionだけを実行し、checked-in JSON Schemaをopen/load/parseせず、`jsonschema`その他validatorをimportしない。JSON Schema self-check、positive/negative vector、golden、captured CLI outputのvalidationはdev dependencyを使うtest/build-time gateで行う。
- PlantUMLはUTF-8、BOMなし、LF、末尾LFちょうど1つ。timestamp、absolute path、source literalを含めない。
- SHA-256はpublished exact bytes（末尾LFを含む）のlowercase 64 hex。
- same source bytes/path set、HEAD、target、resolved config、tool/contract/adapter versionでは、payload bytes、diagnostic order、descriptor order、path、SHA-256が同じでなければならない。

### stdout selector

`--stdout` は高々1回のclosed selectorである。

- `manifest`
- `python:semantic-json`
- `python:plantuml`

selected domain/formatに含まれないselector、invalid grammar、duplicateはsource acquisition前のusage error、exit 2、stdout空、safe diagnosticはstderr、Artifact 0件。

- selectorなし: `code-structure-viz.run-summary/v1` canonical JSON一行だけ。
- available domain selector: published fileとexactly同じbytesだけ。summary、label、追加newlineを付けない。
- available `manifest`: final `run-manifest.json`とexactly同じbytesだけ。
- domain `not_applicable` / `payload_unavailable`: `code-structure-viz.stdout-result/v1`一行、domain statusとclosed stable reason、artifact null。
- final manifest unavailableのfatal/interrupt: `stdout-result/v1`一行、run statusとclosed stable reason、artifact null。
- selectorなしのfatal/interrupt: manifest nullの`run-summary/v1`一行。
- handled SIGINTはfinal rename前のcancellation checkpointまでならstagingをcleanupしexit 130。final rename開始後はcommit tailをnon-cancellableとして確定済みoutcomeをemitし、受信signalでexit/statusを130へ巻き戻さない。強制kill、またはOSがstdout writeを途中終了したbytesは契約外。

### stderr

- diagnosticは`code-structure-viz.diagnostic/v1`のcanonical JSON Linesだけをstderrへ出す。Designはcodeごとの発生単位、最大cardinality、`domain/path/symbol/line`をclosed tableとして定め、implementationはfileごと・collision groupごと・targetごと等の単位を変更しない。
- `not_applicable`、zero-class complete、**depth-limit frontierだけを持つtargeted complete**は正常状態なのでdiagnosticを生成せずstderrはempty bytesとする。`coverage.frontier.reason = depth_limit`を`CSV-PY-008`へ変換しない。
- stdoutへdiagnosticを混在させない。stderrへsource body、literal、secret、absolute path、temporary path、raw non-UTF-8 bytes、surrogate/hashによる架空path、tracebackを出さない。
- internal exception tracebackはdefaultで抑止しstable internal diagnosticへ変換する。開発用debug flagをpublic CLIへ追加しない。

### PlantUML

- `coverage.selected_modules`の各moduleをUTF-8順に必ず一つのdeclared package aliasとして配置し、classを持つmoduleはfield/property/methodをclass blockへ表示する。classを持たないselected moduleもpackage aliasを省略しない。
- method parameterはDesignのclosed grammarで、parameter kind、annotation、`has_default`、`/`、`*`、`*args`、`**kwargs`、implicit receiver除外をexact bytesへ写像する。default literalは表示せず` = …`だけを使う。
- package/class/member/typeに由来するtextはDesignのNFC code-point escape tableだけで変換し、raw quote、backslash、line separator、control/format character、PlantUML directiveを注入できないようにする。
- classless selected moduleのpackage blockは、module alias `M_<sha256("python:module:" + module)>`を宣言し、そのblock内にexactly one `note "classなし" as N_EMPTY_<sha256("python:module-empty:" + module)>`を置く。全package blockをrelationより先に出すため、classless module間のinternal `import_dependency`も宣言済みmodule alias同士の一行として描く。
- internal inheritance、composition、typed dependency、module import dependencyを異なるarrowと日本語label/legendで区別する。
- 同じsemantic snapshot内で複数relationが同一visual key（kind、rendered source、rendered target、fixed label）へ落ちる場合、representative relation sort key最小の一行だけを描く。relation kindが異なるlineは畳まない。semantic JSONのrelation arrayは変更しない。
- semanticsはcolorだけに依存しない。v1 snapshotはdiff color vocabularyを実装しない。
- external/unknown relationはsemantic JSON/coverageに保持し、PlantUMLへ架空classとして補完しない。
- zero-class completeではglobal `N_EMPTY`へ置換せず、selected moduleごとのclassless package/noteを持つvalid diagramを生成する。not_applicable/payload_unavailableではdiagramなし。

## status / failure / exit contract

| condition | run/domain outcome | publication | stdout | exit |
| --- | --- | --- | --- | --- |
| whole mode、candidate Python source 0件かつsource failure 0件 | domain `not_applicable` | manifest only | summary or unavailable domain result; manifest selectorはexact bytes | 0 |
| targeted mode、source 0件またはrequested path/module/class未解決・曖昧・failed seed | domain `incomplete`, `payload_unavailable`, `payload_available: false` | manifest only | unavailable domain resultまたはsummary/manifest | 3 |
| whole mode、source 1件以上、解析成功、class 0件 | domain `complete` | requested zero-class payload + manifest | selector contract | 0 |
| all requested analysis/render complete | domain `complete` | requested payload + manifest | selector contract | 0 |
| isolated read/encoding/parse/module failure、requested seed成立、安全subsetあり、coverage明示、redaction/render/budget pass | domain `incomplete`, `partial_safe`, `payload_available: true` | requested incomplete payload + manifest | payload exact bytesまたはsummary/manifest | 3 |
| safe subsetなし、unsafe symlink、representable path identity collision、requested seed failure/ambiguity、entity overrun | domain `incomplete`, `payload_unavailable`, `payload_available: false` | manifest only | unavailable domain resultまたはsummary/manifest | 3 |
| invalid CLI/config/stdout/diff option | usage/config | Artifact 0件 | empty | 2 |
| non-UTF-8 Git path bytes、invalid/non-unborn HEAD、Python/Git/repository/output/staging/internal invariant/source drift fatal | run `fatal` | Artifact 0件 | summaryまたはunavailable run result | 1 |
| handled SIGINT before publication | run `interrupted` | Artifact 0件 | summaryまたはunavailable run result | 130 |

priority invariants:

1. usage/config errorはsource acquisitionより前に確定する。
2. non-UTF-8 pathとHEAD classification failureはdomain outcomeを作らないrun fatalである。
3. targeted modeはwhole-mode absenceより優先され、`not_applicable`にならない。
4. valid targeted seed成立後に限りfile-local failureを`partial_safe`へ評価できる。
5. entity gateはselection後、renderer前に評価する。

### entity budget

- actual countはtarget selection後のPython class entity数。module package、member、external reference、relationはcountしない。
- default/resolved limitは500。actual 501以上でoverrideなしならtruncationせず`payload_unavailable`、exit 3、manifestにrequested null、resolved 500、actual count、config source、diagnosticを記録する。
- positive `--max-entities N` はCLI sourceとしてresolved limitを置換する。actualがN以下なら通常publication、N超過なら同じpayload_unavailable。
- depthをbudget回避の暗黙truncationとして変更しない。

## スコープ

### 対象

- `python` domainの`working-tree snapshot`一つ。
- Issue outcomeに必要なcommon CLI/config/diagnostic/outcome/SourceView/Artifact transactionの最小v1。
- repository-owned Python package、entry point、lockfile、contract schema/docs、fixture/golden、tests、product CI jobs。
- static AST extraction、whole/targeted selection、semantic JSON、PlantUML、manifest、stdout/stderr/exit。

### 対象外

- `diff` command、temporal comparison、Git endpoint/base/merge-base、FileChangeSet、ChangedPathAdmissionGate、rename/moved matching、impact union。
- SQLAlchemy entity/row/ER semantics、DB、Alembic、runtime metadata。
- Next.js/React/TypeScript/Node adapter、bridge、protocol、Node dependency。
- product HTML command/format/schema/UI/report/publication、Tailscale/public hosting。
- target import/runtime reflection/bytecode、plugin ABI、remote execution、native Windows。
- legacy CLI compatibility、`pyclassuml` / `tree-git-diff` runtime/package/CLI dependency。
- release publication。ISSUE-01はinternal foundationを兼ねる最初のusable sliceであり、Python domain preview milestoneはISSUE-02完了後である。

## 受け入れ条件

| ID | 観測可能な完了条件 | acceptance test |
| --- | --- | --- |
| I01-AC-001 | whole repository fixtureのclass/member/relationをexact semantic JSONとPlantUMLへ出す。member/relation sort tuple、field merge range、relation dedupe winner、tuple/union/subscript type text、annotation TypeReference extraction/resolution/exclusion、method parameter grammar、escape、duplicate visual line policyとmanifest descriptor/hashがgoldenに一致する。 | I01-AT-001 |
| I01-AC-002 | path/module/class target、multiple target union、depth 0/1/2、upstream/downstream、frontierをcontractどおり処理する。whole no-Pythonだけをnot_applicableとし、no-Python/zero-class repositoryで明示targetが未解決なら必ずpayload_unavailableにする。classless module targetではselected module package aliasを全て宣言し、selected module間import relationをexact PlantUML一行で描く。depth-limit frontierだけではstderrを出さない。 | I01-AT-002 |
| I01-AC-003 | no-Python whole、zero-class whole、explicit target absence、partial_safe、payload_unavailable、unsafe symlink、normalization/module/class collision、source driftをstatus/publication/exit matrixどおり処理する。valid commit/unborn/invalid HEADをread-onlyで判別し、non-UTF-8 Git pathはpathを捏造せずrun fatal・Artifact 0件にする。 | I01-AT-003 |
| I01-AC-004 | import/bytecode-compile/exec/subprocess side effect trapが発火せず、AST-only parse以外のcode generationが0件であり、全channelのnegative scanでsource body、secret literal、malicious unknown config key、absolute/temp path、raw non-UTF-8 bytes、surrogate/hash path、tracebackが0件。Git/target bytes/stateをtoolが変更しない。 | I01-AT-004 |
| I01-AC-005 | 同一fixtureを別の空output pathで二回実行し、payload/manifest/stdout/stderr bytesとSHA-256が一致する。file/collector orderを反転してもmember/relation winner、TypeReference resolution、diagnostic cardinality、classless module alias/layout、PlantUML visual dedupeが同一で、macOS/Linux、Python 3.12/latest laneでcontract差分がない。 | I01-AT-005 |
| I01-AC-006 | 500成功、501 payload_unavailable、600 override成功、invalid override exit 2。snapshotはimplicit base不在と1,001 non-Python changesに影響されず、diff-only optionだけをexit 2で拒否する。 | I01-AT-006 |
| I01-AC-007 | stdout selectorのgrammar、duplicate、unselected/unrequested、exact-byte、not_applicable、partial_safe、payload_unavailable、fatal、interrupt、selectorなしsummary、stderr分離をtable-drivenに満たす。全diagnostic codeのcardinality/context golden、malicious quoted unknown keyに対するconstant `CSV-CONFIG-003`、depth-only frontierのempty stderrを検証する。 | I01-AT-007 |
| I01-AC-008 | wheel/sdistをbuildし、wheelをnetworkなし・runtime dependencyなしでfresh venvへinstallし、`jsonschema`とruntime schema resource/loaderなしでfixture CLIが成功する。lock/license inventory、Python 3.12/3.14、Git 2.39+、Ubuntu/macOS CIが通る。 | I01-AT-008 |
| I01-AC-009 | checked-in JSON Schemaをtest/build-timeだけでself-validateし、全golden、captured CLI JSON/JSONL、negative mutation vectorへ適用してtyped runtime outputとの一致を証明する。runtimeはschema file/validatorをloadせず、forbidden scope symbol/command/dependency/HTML formatが存在しない。SpecDock validationも維持する。 | I01-AT-009 |

**I01-AC-001〜I01-AC-009をすべて満たし、Planのissue gate commandがclean checkoutで成功するまでIssueをcompleteにしない。**

## 制約・前提

- initial platformはmacOS/Linux。native Windowsは対象外。
- runtimeはPython 3.12以上。v1 source grammarはPython 3.12へ固定する。latest compatibility laneはPython 3.14 seriesを使う。
- Git 2.39以上。snapshot implementationはGit version固有のwrite behaviorを利用しない。
- runtime dependencyは0件を目標ではなくcontractとする。stdlib `argparse`、`ast`、`tokenize`、`tomllib`、`json`、`hashlib`、`pathlib`、`subprocess`等で成立させる。runtimeでJSON Schema file/validatorをloadしない。`jsonschema`を含むbuild/dev dependencyはlockfileでexact resolveし、test/build-time contract gateだけで使用する。
- product code/licenseのpublic release decisionは本Issueで発明しない。public publish jobを作らず、dependency license inventoryとlegacy provenance確認だけを完了する。
- same-output保証は同じtool/contract/adapter versionと同じresolved inputに対するもの。schema v1を破壊する変更はv1 fieldの意味変更ではなくversion upで行う。

## hard stop conditions

次のいずれかが必要または観測された時点で実装を停止し、canonical R/D/Pまたはaccepted ADRへ戻る。

- public field、CLI option、filename、diagnostic code、status、exit、PlantUML meaningを本書/Designにない形で発明する必要がある。
- diff、SQLAlchemy、Next、product HTML、runtime executionを実装しないとacceptanceを通せない。
- target repositoryへのwrite、Git mutation、source execution、non-UTF-8 pathのsurrogate/hash/replacementによるcanonical path捏造、secret/absolute path leak、silent truncation、overwrite、nondeterministic bytesが発生する。
- dependency license/provenanceを確認できない、runtime dependency 0件を維持できない、またはruntime schema validation/loaderを導入しないと成立しない。
- verified implementation baselineが「production codeなし」から変わり、planned path/symbolと衝突する。
- parent canonical contractまたはaccepted ADRと矛盾し、Issue内だけでは解消できない。
