---
種別: 要件定義書（Issue）
ID: "iss-00008"
タイトル: "Generate Next.js Component Snapshots"
関連GitHub: ["#8"]
package_sequence_key: "ISSUE-05"
状態: "draft"
最終更新: "2026-09-01"
親: ["epic-00002", "init-00001"]
---

# iss-00008 Generate Next.js Component Snapshots — 要件定義

詳細: [Requirement Guide](../../../../../../docs/authoring/requirement.md)

## 目的

coding agent が first-party TypeScript adapter を通じ、Next.js repository の module、exported component、props、static relation、client boundary を JSON と PlantUML で取得できる。

利用者 story: coding agent として、Next.js application を build/execute せず、TypeScript compiler の静的意味情報から component structure と server/client boundary を把握したい。

この Issue は技術 layer の完成ではなく、利用者が command を実行して source acquisition、domain analysis、semantic JSON、PlantUML、diagnostic、acceptance evidence まで確認できる一つの vertical outcome を所有する。

## 背景

- 親 Initiative は三 domain の code structure を静的に可視化する。
- 親 Epic は安全な Git comparison と agent-first Artifact contract を一つの product outcome として統合する。
- この slice の declared dependency は ISSUE-01。依存 Issue の public contract だけを利用し、unfinished sibling の内部実装には依存しない。
- canonical authority は stable scope ID、本 Issue と親 scope の repository-relative R/D/P path、accepted ADR、interview、latest user decisions である。採用・実装開始時に HEAD と configured upstream を再検証し、current commit SHA を本文の自己 authority として固定しない。

| 親 requirement | この Issue の所有範囲 |
| --- | --- |
| EPIC-REQ-001 | next domain の snapshot を end-to-end で提供する。 |
| EPIC-REQ-002 | static analysis、read-only Git、safe endpoint/source、redaction、fail-closed を維持する。 |
| EPIC-REQ-003 | next の identity/member/relation/matching semantics を domain ownership のまま保つ。 |
| EPIC-REQ-004 | per-domain versioned semantic JSON、domain-specific PlantUML、`run-manifest/v1` descriptor、determinism/no-overwrite を提供する。 |
| EPIC-REQ-005 | domain status、0/1/2/3/130 exitとdomain-local entity budgetを実装・検証する。run-level changed-path budgetはdiff専用であり、本snapshot sliceでは適用しない。 |
| EPIC-REQ-009 | closed stdout selector、exact-byte copy、unavailable result、stderr diagnostic、usage no-publicationをsliceのpublic CLI contractとして実装・検証する。 |

## 観測可能な要件

| ID | 観測面 | 要件 |
| --- | --- | --- |
| I05-REQ-001 | CLI と observable outcome | coding agent が明示した Next project/targetについて、module、component declaration、export binding、props、static relation、client boundaryをJSONとPlantUMLで取得できる。 |
| I05-REQ-002 | source acquisition | Python coreはapplicabilityをNode起動前に判定し、domain-owned planでGit source bytesを一度だけ凍結する。one-shot first-party Node adapterはstdin virtual files、bundled TypeScript、versioned closed TrustedTypeEnvironmentだけを解析し、target repositoryを直接読まない。Node.js 22 LTS以上はapplicable Next runだけで要求する。 |
| I05-REQ-003 | semantic behavior | Component identityはphysical declaration moduleとdeclaration keyで安定化し、export/re-export/aliasは別bindingとして保持する。propsはclosed normalized type IR、relationはmodule/componentの二平面、client boundaryはpositive evidenceに基づくfact/roleとして表現する。 |
| I05-REQ-004 | Artifact/output | Node adapterは`code-structure-viz.next-adapter/v1`のexact one response JSONを返し、Python coreがuntrusted responseのschema/path/ref/redaction/order/ID/count/digestを検証・再計算して`code-structure-viz.semantic/v1`と`code-structure-viz.plantuml/next/v1`を生成する。 |
| I05-REQ-005 | failure behavior | non-literal dynamic behaviorはrelationを捏造せずunknown diagnosticとcoverage limitationにする。Node/protocol/static analysis failureはincomplete、entity budget超過はdomain incomplete exit 3でaffected semantic JSON/PlantUMLを公開しない。implicit changed-path gateはdiff専用でありsnapshotでは実行せず、snapshotへの`--from`/`--to`/`--pr-target`/`--max-changed-paths`指定はusage error、exit 2とする。 |
| I05-REQ-006 | safety/determinism | 解析対象codeを実行しない。source view/plan、domain config、project/target/limits、Node/TypeScript/adapter/protocol、TrustedTypeEnvironmentが同じなら全record/order/digest/outputが決定的になる。finite memoryはtransport/decoder/model/V8 old-spaceのclosed上限で保証し、総RSSはv1非保証とする。 |
| I05-REQ-007 | stdout contract | `--stdout SELECTOR`を高々1回のclosed selectorとして検証し、available exact bytes、unavailable result、selectorなしsummary、stderr diagnostics、exit 2 no-publicationを提供する。 |

### I05-REQ-001

coding agent が first-party TypeScript adapter を通じ、Next.js repository の module、exported component、props、static relation、client boundary を JSON と PlantUML で取得できる。
### I05-REQ-002

Python coreは明示project rootの`package.json`にあるdirect `next` dependencyからapplicabilityを判定し、domain-owned acquisition planでGit source bytesを一度だけ凍結する。one-shot first-party Node adapterはstdin virtual files、bundled TypeScript、versioned closed TrustedTypeEnvironmentだけを解析する。Node.js 22 LTS以上はapplicable Next runだけで要求する。
### I05-REQ-003

Component identityはrepository-relative physical declaration moduleとdeclaration key。named bindingまたはmodule-local `@anonymous-default` slotを使う。export/re-export/alias/defaultは`ExportBindingMember`、route pathとrouter contextはattributeとし、identityに含めない。
### I05-REQ-004

Node adapterは`code-structure-viz.next-adapter/v1`のexact one response JSONをstdoutへ返す。Python coreはresponseをuntrusted inputとしてschema/path/ref/redaction/order/ID/count/digest/target completenessを検証し、public semantic JSONとPlantUMLを自身で生成する。
### I05-REQ-005

non-literal dynamic behaviorはrelationを捏造せずunknown diagnosticとcoverage limitationにする。Node/protocol/static analysis failureはincomplete、entity budget超過はdomain incomplete exit 3でaffected semantic JSON/PlantUMLを公開しない。implicit changed-path gateはdiff専用でありsnapshotでは実行せず、snapshotへの`--from`/`--to`/`--pr-target`/`--max-changed-paths`指定はusage error、exit 2とする。
### I05-REQ-006

解析対象 module、plugin、migration、build script、application entry pointをimportまたは実行しない。source view fingerprint、source plan digest、domain config digest、projects、targets、limits、Node/TypeScript/adapter/protocol version、TrustedTypeEnvironment digestが同じなら全record/order/run fingerprint/model digest/Artifact bytesとdigestが決定的になる。


### I05-REQ-007

`--stdout SELECTOR`を高々1回のclosed selectorとして検証し、available exact bytes、unavailable result、selectorなしsummary、stderr diagnostics、exit 2 no-publicationを提供する。

### CLI examples

```bash
code-structure-viz snapshot --repo . --domain next --output-dir /tmp/csv-next-snapshot
code-structure-viz snapshot --repo . --domain next --project apps/web --target path:apps/web/app/dashboard --upstream-depth 1 --downstream-depth 2 --output-dir /tmp/csv-dashboard
code-structure-viz snapshot --repo . --domain next --project apps/web --target path:apps/web/components/index.ts --output-dir /tmp/csv-components
code-structure-viz snapshot --repo . --domain next --format semantic-json --stdout next:semantic-json --output-dir /tmp/csv-stdout
```

### source acquisition contract

- `--repo`はexact Git rootのまま、repeatable `--project REPOSITORY_RELATIVE_DIRECTORY`でNext project rootを明示する。CLI指定はconfig `[next].projects[].root`を置換し、root固有source/configはproject descriptorから解決する。default projectは`.`。monorepo/workspaceを自動探索しない。
- project root直下`package.json`のdirect `dependencies.next`または`devDependencies.next`にnon-empty stringがある場合だけapplicableとする。`next.config.*`、directory名、source import、lockfile indirect entryをevidenceにしない。
- domain-owned immutable SourceAcquisitionPlanに従い、Python coreがprogram/control/context bytesを一度だけSourceViewへ凍結する。Nodeへtarget root path/cwdを渡さない。
- program filesはTS/TSX/JS/JSX、`.d.ts`はcontext-only。`.git`、`node_modules`、`.next`、`out`、`dist`、`build`、`coverage`はhard exclude。test/spec/storyはdefault excludeにしない。
- config lookupは`tsconfig.json`、`jsconfig.json`、versioned built-in safe configの順。repository-local `extends`、`baseUrl`、`paths`だけをfrozen SourceView内で解決し、package-based extendsやtarget `node_modules`を暗黙に読まない。
- one-shot Node adapterはrequest virtual files、bundled TypeScript standard library、`code-structure-viz.next-trusted-types/v1`だけを読むin-memory CompilerHostを使う。TrustedTypeEnvironmentはminimal JSX/React/Next wrapper declarations、exact version/digest/licenseを持ち、target type roots/node_modules/networkを参照しない。Node.js 22 LTS以上はapplicable runだけで要求する。
- transport/processは20,000 files、4 MiB/file、64 MiB decoded source、96 MiB encoded stdin、JSON nesting 64、8 MiB/string、100,000 total/20,000 per collection array items、10,000 model records、`max_adapter_stdout_capture_bytes`・`max_adapter_response_bytes`・`max_selected_stdout_bytes`の三つの16 MiB境界、64 KiB stderr、60秒、512 MiB V8 old-spaceをv1上限とし、超過はsilent truncationせず`payload_unavailable`とする。旧`max_stdout_bytes`はselected stdoutの互換aliasに限る。総RSS上限はv1で保証しない。

### public target grammar

`--target`、resolved config、private requestで公開するtargetは
`path:<repository-relative-path>`だけとする。これは内部のModule/Component
IDやsemantic keyとは別の利用者向けアドレスであり、`component:`、`module:`、
`file:`形式は公開しない。frozen SourceViewのfile pathは、対応するFileが
`program` roleかつsuffix `.ts`、`.tsx`、`.js`、`.jsx` のときだけ、そのfile・
Module・Component集合へ解決する。`.d.ts`、`package.json`、`tsconfig.json`、
`jsconfig.json` はcontext/control provenanceであり、direct targetにはできない。
directory pathは全canonical descendant集合へ解決する。
directoryの複数descendantは正常で、曖昧さではない。missing、project-scope
ambiguity、out-of-scope、または選択集合のtainted/excluded/failed recordが一つでも
あれば、domain全体を`CSV-NEXT-TARGET-001`・`payload_unavailable`・no-artifact
とし、manifest/stdoutのunavailable vectorをexactに出す。

### Round 8 review state

ChatGPT Use Strict Round 8 は `review_status: fail`、P0=0、P1=4、P2=0 だった。
4件は、(1) Next root manifestのpath-only domain branch、(2) frozen source bytesから
独立導出する完全なexport syntax census、(3) response validation後に適用する
`EntityBudgetGate`、(4) program fileだけをsemantic ownerとするtarget/module境界、
としてdata-only schema・reference validator・fixture・testへ反映した。fresh
exact-SHA Strictはまだ実行・通過しておらず、readinessは未確定である。製品の
Next adapter/CLI実装は開始していない。

### Round 9 review state

ChatGPT Use Strict Round 9 は `review_status: fail`、P0=0、P1=7、P2=1 だった。
追加7 P1/1 P2は実装前data-only contractへ反映し、fresh exact-SHA Strictは未実行・
未通過、readinessは未確定、production adapter/CLIは未着手のままとする。

- export syntax censusはlocal export list、default alias/declaration/expression、
  multiple/multiline specifier、comment、Unicode IdentifierName NFC、CRLF、BOMを
  含む閉じたtoken grammarとexact UTF-8 byte spanで固定し、positive/omission/mutation
  vectorを持つ。
- re-exportはsyntax identity、source specifier、imported/original name、resolved
  source Module、expanded exported name、target declarationを独立witnessへ記録する。
  Pythonはfrozen module graphからalias/star/cycle/conflictを再計算し、Node observation、
  public binding、coverage countをexact比較する。
- EntityBudgetGateはpre-budget outcomeを保持する。complete/partial_safeはunder
  budgetでそのまま、overrunだけpayload_unavailableとし、override通過でもpartial_safe
  をcompleteへ昇格させない。
- `max_adapter_stderr_capture_bytes`とpublic diagnostic emission bound、
  `max_total_array_items`と`max_collection_items`を分離する。captureはincremental
  UTF-8 byte count、limit/+1、process-group termination、raw/partial disposal、stable
  diagnostic、manifest projectionを固定し、array aggregateはpre-materializationで数える。
- closed SourceAcquisitionPlan/v1 descriptorはresolved control paths、local extends、
  file-role map、projects、suffixes、exclusions、limits、trusted digestの全fieldをhashし、
  known-answer mutationを持つ。input/config/source-planはNFC UTF-8 root-path order、
  semantic record collectionはrecord-ID orderとする。
- staleなpublic component selector表現は削除し、path targetから解決したinternal
  Component seedだけをtaint/traversal witnessで扱う。

### Round 10 review state and Pass A remediation

ChatGPT Use Strict Round 10 は `review_status: fail`、P0=0、P1=8、P2=0 だった。
証拠は `20260901t000000z-disc-strict-spec-review-round-10.md` に固定し、fresh
exact-SHA Strictは未実行・未通過、readinessは未確定、production adapter/CLIは未着手
のままとする。Pass Aでは、project対応をID/rootで比較して各surfaceの順序を独立検証し、
EntityBudgetGateの暗黙のcompleteを廃止し、canonical POSIX path値（root `.` は文脈限定、
path本体UTF-8 4096 bytes）とprogram File→exactly one Moduleをdata-only契約へ反映した。
Pass Bでは、closed module-level export grammar、raw declaration/edgeから独立再計算する
re-export witness、公開diagnostic stderrのUTF-8 JSONL gate、実response bytesを
materializeせず検査するbounded decoderをdata-only契約へ反映した。fresh Strictはまだ
実行・通過しておらず、実装開始可能性は未確定である。

### Round 10 Pass B remediation (実装前契約)

- export scannerは、深さ0かつ`.`のpropertyではないmodule-level `export`だけを認識する。
  local list、default alias/declaration/expression、`async function`、generic/type span、
  複数・改行specifier、CRLF/BOM、NFC Unicodeを閉じた字句規則で処理し、function/class
  body、JSX、property、regex、template、string、comment中の単語はfalse positiveにしない。
  body declarationは閉じ波括弧を終端とし、expression/list/re-export/starはsemicolonを
  要求するというASI方針を固定し、source bytesのexact span/token digestを比較する。
- re-exportはpublic bindingから逆算せず、Python所有のraw declarationsとraw edgesから
  alias、star（0..N、default除外）、cycle、conflictを再計算する。各結果はsyntax identity、
  source specifier、imported/original name、resolved source Module、expanded name、target
  declaration、resolutionを持ち、main response proofのobservation/binding/countと
  exact-equalにする。valueで一意にComponentへ解決したものだけpublic bindingとする。
- public diagnostic stderrは全diagnosticをcanonical JSON + LFのUTF-8 bytesへ先にencode
  してから判定する。limitはinclusive、limit+1はpartial write 0、安定した
  `CSV-NEXT-LIMIT-003`だけをmanifestへ投影し、adapter raw textを漏らさない。child capture
  の`max_adapter_stderr_capture_bytes`とは別のcounterである。
- responseはbounded streaming decoderでduplicate object key、nesting、string UTF-8 bytes、
  各array、全array aggregateをmaterialize前に数える。各array 100,000内でもaggregate
  100,001を拒否し、reason/counter/materialized=falseを証人として残す。成功時も同じ
  decoderをresponse envelope validation前段で通す。

### Round 11 review state and Pass C remediation

ChatGPT Use Strict Round 11 は exact SHA
`75ac0e0b34347b825c0bec2e6fbf9ff2068d9a1b`、CI run `33422630936`（7/7 success）に対して
`review_status: fail`、P0=0、P1=8、P2=0を返した。証拠とtranscript SHA-256は
`20260901t010000z-disc-strict-spec-review-round-11.md`へ固定した。Pass Cでは、(1) root-path
orderとrecord-ID orderを逆転させる二projectをprivate requestからresponse、domain、root
manifest、fingerprintまで通す、(2) requested formats、budget requested/resolved/source、
stdout selectorを一つのcanonical run contextとして全projectionへ渡す、(3) UTF-8 byte境界を
含む一つのPOSIX path helperを全path surfaceで使う、(4) selected program File→exactly one
Moduleの欠落・重複・Component-onlyをtyped `CSV-NEXT-TARGET-001`へ投影する、という
data-only契約を反映した。Pass Dでは、(5) module-level JSX lexical scanner、(6) raw
declaration/edgeからのre-export witness、(7) public diagnostic stderrのbounded JSONL gate、
(8) raw response bytes専用のbounded decoderを追加で反映した。これらはローカル契約の修復であり、
fresh exact-SHA Strictは未実行・未通過、readinessは未確定、production adapter/CLIは未着手である。

Pass Cの固定事項:

- projectはimmutable ID/rootで対応付け、input/config/source-planはNFC UTF-8 root-path order、
  semantic modelはrecord-ID orderとする。順序を混同したrequest/response/domain/rootの各
  mutationは拒否し、formatsとstdout selectorもrun fingerprint preimageに含める。
- run contextの`requested_formats`、`budget_requested`、`budget_resolved`、`budget_source`、
  `stdout_selector`をresponse、EntityBudgetGate、domain、root runへ同じ値で投影する。
  requested formatを暗黙のFORMAT_ORDERから補わない。selectorは`null`（省略）、`manifest`、または
  requested set内の`next:semantic-json`/`next:plantuml`のいずれかである。
- `next-path-v1`の`maxLength`は補助的な文字数検査に留め、NFC・UTF-8 bytes・root `.`の文脈
  規則を共有helperで再検証する。4095/4096 bytesは受理し、4097 bytes、NFC collision、
  ordinary file surfaceのroot `.`は拒否する。
- target failureはmodel assertionへ逃がさず、file/directory両方でmissing、duplicate、
  Component-onlyをpre-model typed failureとして扱う。選択された集合は全体を
  `payload_unavailable`、no artifact、manifest/stdout unavailable、exit 3へ投影する。

Pass Dの固定事項:

- export scannerはself-closing/fragment/nested same-name JSX、attribute expression内の
  string/template/comment/regex、propertyやliteral内の偽`export`を無視し、async/generic/typeの
  declaration spanをBOM/CRLFを含む凍結UTF-8 byte範囲として再計算する。ASIを暗黙に補わず、閉じた文法の
  semicolon終端を要求する。
- re-exportは公開ExportBindingから導出せず、凍結raw declaration/edgeを独立再計算する。aliasは何段でも
  追跡し、starはdefaultを除く0..N行へ展開する。cycle/conflict/missing sourceは元のexport名と理由を
  witnessへ残し、component bindingとvalue/type coverageを同じ独立結果から投影する。
- public diagnostic stderrは全JSONLをUTF-8 encodeしてからinclusive limitを測る。limitは全行を出し、
  limit+1はpartial write 0、`CSV-NEXT-LIMIT-003`だけをmanifestへ投影する。adapter captureとは別の
  counterであり、raw responseはbytesを入口とするbounded decoderでduplicate key、depth、decoded string、
  per-array、aggregateをmaterialize前に拒否する。

### Round 12 review state and remediation contract

ChatGPT Use Strict Round 12 は exact SHA `48266f813353a7fd78e4e15d72ff6d33c4142827`、CI run
`33435802167`（7/7 success）に対して `review_status: fail`、P0=0、P1=8、P2=0を返した。詳細な
原文は `artifacts/20260901t020000z-disc-strict-spec-review-round-12.md` に保存する。これは受理済みの
data-only修復範囲であり、fresh exact-SHA Strictは未実行・未通過、readinessは未確定、Next
production adapter/CLI実装は未着手のままとする。

1. 逆順二projectは同じvalidated response modelをdomain、budget/coverage、published bytes、root
   manifest、run fingerprintまで通し、各surfaceのroot-path orderとrecord-ID orderを別々に検証する。
2. `NextRunContext/v1` は `null | manifest | next:semantic-json | next:plantuml` を表し、requested
   formats、budget requested/resolved/source、実selectorをprivate requestからresponseへexact echoする。
   EntityBudgetGateはcontextだけをauthorityにし、fallbackやprovenance推測をしない。
3. raw response bytesはbounded decode後にclosed response schema、安全なNFC/UTF-8 path/ref/count基礎検証、
   typed target precedenceの順で一つの入口から検証する。wrong schema、extra field、unsafe compound
   mutationはtarget failureへ再分類しない。
4. JSX censusはNFC Unicode IdentifierNameのpaired/nested/member/namespace tagをmodule-level lexerで
   認識し、属性式とtext内の偽exportを除外する。re-exportはexported-nameだけでlookupし、declaration key
   をfallbackにしない。owner Moduleとphysical targetをwitnessへ保持し、component targetを必須にする。
5. double alias/star（default除外、0..N、value/type/unknown coverage）とcycle/conflictをschema-valid
   proofから`CSV-NEXT-EXPORT-001`、domain/root manifest、stdout unavailable、exit 3まで投影する。
6. 全path surfaceはshared `next-path-v1` helperで`#`、非NFC、UTF-8 byte boundaryを拒否する。File→Module
   のtyped target failureはfile/directoryそれぞれで三分類する。`missing`は選択されたprogram Fileが
   存在するがModuleがなく、期待されるModule identityを参照するComponentもない純粋な欠落、
   `component_only`はModuleがない一方で期待されるModule identityを参照するComponentが残る状態、
   `duplicate`は同じ選択Fileにbyte-identicalなModule行が複数ある状態である。`duplicate`だけは
   typed failureへ進む前に選択対象の同一行に限って許可する狭い例外とし、三分類すべてをresponse→diagnostic→
   domain→root manifest→stdout unavailable→exit 3へ完全に投影する。

### Round 13 review state and remediation contract

ChatGPT Use Strict Round 13 は対象SHA `991516bf730f4f2ddb3d15067702dcfae95ec6b1`、CI run
`33446911714`（7/7 success）に対して `review_status: fail`、P0=0、P1=9、P2=1を返した。
詳細は `artifacts/20260901t040000z-disc-strict-spec-review-round-13.md` に保存し、履歴のfailを
passへ書き換えない。以下はdata-only契約・schema・fixture・reference validator・説明資料へ
反映する受入条件である。fresh exact-SHA Strictは未実行・未通過、readinessは未確定、production
Next adapter/CLI実装は未着手のままとする。

1. semantic六collectionとPlantUMLは一つのimmutable validated modelから生成し、schema-validな
   order/payload mutationでも実bytes、Artifact SHA-256、root descriptorが不一致として拒否される。
2. response検証済みの `NextValidatedDecision`（model、proof、request-owned context、pre-budget
   outcome、gate decision）だけをdomain/root/stdoutの入力とし、後段のstatus・target・format・budget・
   selector再構成や独立model指定を許さない。
3. target failureの `missing`・`component_only`・`duplicate` をresponse coverage、diagnostic、
   domain/root coverage、manifest、unavailable stdoutまで同じdecisionから保持する。file/directoryの
   六ケースを固定し、typed `CSV-NEXT-TARGET-001` とexit 3へ投影する。
4. typed target routingの前にproof-baseを検証し、collection shape/order、ID/ref、causal edge、
   export-owner join、target completenessを完全一致させる。複合mutationはschema-validでも拒否する。
5. double alias、empty/multi star（default除外）、cycle、conflictをschema-valid request/responseから
   domain、root manifest、diagnostic、stdout unavailable、exit 3まで実行し、cycleとconflictは別の
   `CSV-NEXT-EXPORT-001` whole-run vectorとする。
6. re-export observation/raw-edge joinはowner、source/imported/original/exported name、syntax identity、
   exact byte spanをキーとして全件を一対一で消費し、`Foo as A`・`Foo as B`・反復形を区別する。
7. ECMAScript IdentifierNameのID_Start/ID_Continue/Other_ID_Start/Other_ID_Continue表を固定し、
   Unicode 15.0.0（U+00B7を含む）とprofile versionをcompatibilityおよびrun-fingerprint preimageへ含める。
8. shared root-or-path schemaを全source-root/path surfaceへ適用し、root文脈の`.`を受理する一方、
   非root unsafe pathを拒否する。
9. private adapter response全bytesの `max_adapter_response_bytes` をdecode/materialize前に測定し、16 MiBは受理、
   16 MiB+1はpartial writeなしのunavailable/manifest-only/exit 3へ通す。`max_stdout_bytes` は公開selected
   stdoutのv1互換aliasであり、private responseの判定には使わない。
10. 人間向けHTMLの重複Round 11 Pass C itemを一つだけ残す。上記のlocal修復・テスト成功はfresh
    Strict passやIssue完了を意味しない。

### Round 14 review state and remediation contract

Round 14 Strict は、初回connector検証失敗（`issue-eight-strict-round-fourteen`、証跡は
`/Users/iwasawayuuta/.oracle/sessions/issue-eight-strict-round-fourteen/artifacts/transcript.md`、
SHA-256 `da7a78ea8c298fff4527bac48b3593f6fa8009ee2fe4f774c8dfad1978b7e4cb`）と、再試行で得た
content review（`issue-eight-strict-round-fourteen-2`、証跡は
`/Users/iwasawayuuta/.oracle/sessions/issue-eight-strict-round-fourteen-2/artifacts/transcript.md`、
SHA-256 `05c802ca289681a10fb804e152c7d0ffcd20a30a8223123bede7204eb7803fc4`）を分けて記録する。
再試行は対象SHA `cf5da416e25e76068ed99caf0d450d0e2d5b28df`、GitHub Actions run `33457932686`
（7/7 success）を確認し、`review_status: fail`、P0=0、P1=5、P2=2、
`implementation_ready: no`を返した。fresh current-SHA Strictは未実行・未確認、readinessは未確定、
production adapter/CLI実装は未着手である。詳細とローカル修復の対応表は
`artifacts/20260901t031000z-disc-strict-spec-review-round-14.md`を正本の証跡とする。

Round 14で追加する実行可能な受入条件は次のとおりである。

1. `NextRunDecision`を`ValidatedResponseDecision`、`PreResponseFailureDecision`、
   `NotApplicableDecision`からなるclosed unionとする。pre-response variantはrequest-derived
   `NextRunContext`、closed stage/diagnostic、knownまたはnull counts、`payload_unavailable`、
   artifact 0件、exit behaviorを所有する。domain/root/manifest/stdout/stderrはこのunionだけを
   入力とし、Node discovery/spawn/timeout/nonzero、stderr/raw stdout cap、malformed JSON、duplicate
   key、schema/ref/ID failureを別の`_domain` authorityから作らない。
2. proof reasonをclosed semanticsにする。`not_selected`とselection-only `target_excluded`は
   statusを下げず、intentional `unsupported`はunknown coverageと`CSV-NEXT-UNSUPPORTED-001`を伴う
   completeとする。localized taint/failedはlocality proofがある場合だけpartial_safeとし、
   adapterの`over_budget`は拒否してPython-owned `EntityBudgetGate`だけが予算超過を所有する。
   explicit target identity failureはtyped `payload_unavailable`とする。
3. ECMAScript IdentifierNameはhost `unicodedata.category()`を使わず、Unicode 15.0.0の
   ID_Start/ID_ContinueとOther_ID sets、U+00B7、Join_Controlを含むchecked-in tableで判定する。
   table bytesのdigest、compatibility preimage、run fingerprintを同じprofileへ固定し、Python
   3.12と最新対応Pythonの全code point digestを一致させる。
4. model/aggregate/raw limitsは実wire envelopeで相互に到達可能にする。`max_model_records`は
   10,000へ固定し、proofは公開model recordをpayload重複しないID/reference evidenceで表し、
   proof-only recordだけpayloadを許す。9,999件のcompact context Fileと1件のProjectからなる
   schema-valid streamでmodel exact/+1、aggregate+1、raw-byte+1をbounded decode→response
   validation→decisionへ通し、diagnostic precedenceを固定する。`proof.discovered_records`の
   schema上限は構造上限として20,000にし、10,001件をschema-validのままmodel-limitへ到達させる。
   巨大なPython object graphは作らない。
5. 親processはchild stdoutをincrementalにcaptureし、`max_adapter_stdout_capture_bytes`をretain前に
   数える。exactは受理し、+1はprocess groupを停止してpartial/raw bytesを破棄し、decoderを呼ばず、
   `CSV-NEXT-LIMIT-003`、manifest-only、typed unavailable stdout、exit 3へ進める。
6. stdoutのtarget failureはcanonical sorted `target_failures:[{target_key,reason}]`で一対一に保持し、
   target-related `domain_payload_unavailable` branchだけで許可する。available、not_applicable、
   generic unavailable、fatal、interrupt branchはtarget failureを拒否する。single、同一理由複数、
   異なる理由複数、非target mutationを固定する。
7. source acquisitionは`SourceDiscoveryIntent`から始め、two-phase single-read acquisitionの最後に
   `FinalSourceAcquisitionPlan`と`SourceView`を同じseal operationで確定する。final read/drift check後の
   filesystem readを禁止し、instrumented readerで各path一回、frozen bytesとのplan/view一致、共有sealを
   検証する。

これらの受入条件は`tests/contracts/test_next_contracts.py`、`tests/contracts/test_json_schemas.py`、
`tests/contracts/next_reference_validation.py`、関連JSON Schema、Markdown contract、fixture、HTMLへ
反映し、local passをStrict passやIssue完了と解釈しない。

### semantic contract

- entityはphysical-path `ModuleEntity`とdeclaration-anchored `ComponentEntity`。named declarationまたは`@anonymous-default`でComponentを識別し、range/export/route/wrapper/propsをidentityに含めない。
- memberは`ExportBindingMember`、`ImportBindingMember`、`PropMember`。barrel/re-export/aliasはbindingを増やすがComponentを複製しない。adapterは凍結UTF-8 source bytesからowner file、byte span、token identity、syntax kind、exported name、value/type role、re-export/starを持つ完全な独立observationを返し、Pythonがcensusとresolution（component/value/type/unknown）を照合する。public `ExportBindingMember`はvalue exportが一意なComponentへ解決した場合だけで、value/type/unknownはcoverage-onlyとする。export/route rootからproven render/wrapperで到達するlocal Componentだけを`reachable_local`として含める。
- Component認定はsafe React callable/construct signature、closed React class provenance、recognized UI route default、proven JSX output-flow、closed wrapper allowlistのpositive evidenceを要求し、PascalCaseだけで認定しない。
- propsはTypeCheckerのeffective signatureから取得し、primitive/type-parameter/redacted-literal/reference/array/tuple/union/intersection/function/object/opaqueのclosed type IRへ正規化する。literal value、function parameter名、generic名を公開せず、complexity limitはtruncationではなくopaque+coverageで表す。
- relationはmodule planeの`static_import`/`literal_dynamic_import`とcomponent planeの`jsx_render`/`component_wrap`を分離する。lexical scanやruntime tree推測をせず、return outputへ流れるbounded expressionだけを追う。
- client boundaryはdirect `client_entry` fact、router context、static value edgeから導く`client_dependency`/`server_candidate` role、`unknown`で表す。client-entry seed自身は`client_dependency`でも`server_candidate`でもなく、dual roleは異なるclosureのpositive evidenceが揃う場合だけ許す。no directiveをserverと断定しない。boundary crossingはunderlying edgeのfacetとする。

### output contract

- private adapter protocolは`code-structure-viz.next-adapter/v1`、public filesは`next.snapshot.semantic.json`と`next.snapshot.puml`、PlantUML contractは`code-structure-viz.plantuml/next/v1`とする。
- Python coreはadapter responseをuntrusted inputとして検証し、ID/count/digestを再計算してpublic payloadをrenderする。protocol noise、closed schema mismatch、unsafe path/ref/redactionはresponse全体を拒否する。
- manifestはNode/TypeScript/adapter/protocol version、project/config path、source acquisition plan/config/source digest、coverage、diagnostic、target/depth/budget、Artifact hashをsafe metadataとして記録する。
- entity budgetはselected internal Module+Componentだけを数え、member/relation/external/frontier/project descriptorを数えない。responseの構造・参照・`max_model_records`検証が成功した後、Pythonの独立`EntityBudgetGate`がactualを再計算してpublicationを判定する。超過は`CSV-NEXT-LIMIT-005`付き`payload_unavailable`、actualを残すmanifest-onlyであり、semantic JSON/PlantUMLを公開しない。
- Next project不在を証明できた場合はNodeを要求せずnot_applicable。applicable projectでComponent 0はcomplete empty。applicableでNode/adapter unavailableはpayload_unavailable、exit 3。

### snapshot and diff option separation

`snapshot` は一つの run-start immutable `SourceView` を解析する use case であり、implicit base、start HEAD merge-base anchor、`FileChangeSet`、`ChangedPathAdmissionGate` を構築または参照しない。`snapshot` と `--from`、`--to`、`--pr-target`、`--max-changed-paths` のいずれかを併用した場合は source acquisition/publication 前の usage error、exit 2、stdout 空、Artifact 0件とする。implicit baseを解決できない repository、または1,001件以上の changed pathsが存在する working treeでも、snapshotの結果はそれらに影響されない。snapshotにはdomain-local entity budgetだけを適用する。

### incomplete publication contract

`incomplete` は `incomplete_kind` により次の二種類へ分ける。`not_applicable`、run-level fatal、usage error と混同しない。

| incomplete_kind | 判定条件 | affected domain payload | single-domain manifest | exit |
| --- | --- | --- | --- | --- |
| `partial_safe` | failure が局所的に隔離でき、残る subset が semantic に安全で、coverage と diagnostic が欠落範囲を明示し、全 requested payload が redaction を満たし、explicit target completenessとentity budgetを満たす。 | status `incomplete` の requested semantic JSON と PlantUML を同じ安全 subset として公開する。truncationをしない。 | `payload_available: true`、`incomplete_kind`、coverage、diagnostic、Artifact descriptorを記録する。 | 3 |
| `payload_unavailable` | safe subset がない、explicit target failure、global config/program/Node/protocol/schema/security/identity failure、source/transport/entity budget超過。 | affected domain の semantic JSON と PlantUML を公開しない。 | run-level fatalでない限りsingle-domain manifestに`payload_available: false`、`incomplete_kind`、coverage/diagnostic/countを記録する。 | 3 |

snapshot の一部 file parse/read/type-resolution failure は、失敗 file を隔離し安全 subset と欠落 coverageを証明できる場合だけ `partial_safe` になれる。diff は before/after のどちらか一方でも source acquisition または static analysis が失敗した時点で `payload_unavailable` とし、added/removed を生成しない。both-side snapshot が完全に成立した後の局所的な context failureだけが、上の全条件を満たす場合に限り `partial_safe` になれる。


### stdout selector contract

`--stdout SELECTOR` は省略可能で、command line 全体で高々1回だけ指定できる。`SELECTOR` の文法は次の二形式に閉じる。

- `manifest`
- `DOMAIN:FORMAT`。`DOMAIN` は `python`、`sqlalchemy`、`next` のいずれか、`FORMAT` は `semantic-json`、`plantuml` のいずれか。

boolean flag、path、alias、略記、大小文字違い、値省略は受理しない。`--stdout` の重複、文法不正、resolved selected domains に含まれない domain、resolved requested formats に含まれない format は、source acquisition と publication の前に usage error として確定する。結果は exit 2、stdout 空、safe diagnostic は stderr、semantic JSON・PlantUML・final run manifest を含む Artifact は0件である。

`--stdout` を省略した場合、stdout は `code-structure-viz.run-summary/v1` の決定的な UTF-8 JSON 1行だけとする。summary は schema、run status、exit code、domain status、final manifest の relative path または null を持ち、source body、literal、secret、absolute path を持たない。diagnostic は stdout に混在させず stderr へ出す。

有効な selector の対象 Artifact が公開可能な場合、stdout は output directory に公開した対象 file と正確に同じ bytes だけを出す。前後に summary、label、diagnostic を付けない。`--output-dir` は引き続き必須であり、stdout は永続 Artifact の代替ではなく複製である。

有効な selector の対象が `not_applicable`、`payload_unavailable`、run fatal、または handled interrupt により利用不能な場合、stdout は次の `code-structure-viz.stdout-result/v1` JSONをcanonical encoderで決定的な1行にする。object keyは既存のlexicographic `sort_keys=True`、文字列はNFC、encodingはUTF-8、行末はLF一つとし、専用の手書きfield orderは持たない。`availability` は false、`artifact` は null である。domain selector で domain outcome が確定している場合だけ `domain_status`、run-level outcome では `run_status` を使う。`manifest` selector も final manifest が存在しない場合は同じ規則を使う。既存の exit 0/1/3/130 を変更しない。

```json
{"type":"stdout_result","schema":"code-structure-viz.stdout-result/v1","selector":"next:semantic-json","availability":false,"domain_status":"not_applicable","stable_reason":"domain_not_applicable","artifact":null}
```

| case | stdout | stderr | exit | publication |
| --- | --- | --- | --- | --- |
| selector なし、complete/not_applicable/incomplete/fatal/interrupt | `run-summary/v1` JSON 1行 | diagnostic のみ | 0/1/3/130 | outcome contract に従う |
| available `DOMAIN:FORMAT` | 対象 Artifact の exact bytes | diagnostic のみ | 0 または `partial_safe` の3 | output-dir へ通常公開 |
| available `manifest` | final run manifest の exact bytes | diagnostic のみ | 0 または3 | output-dir へ通常公開 |
| domain not_applicable | `stdout_result/v1` 1行、`domain_status: not_applicable`、`stable_reason: domain_not_applicable` | diagnostic のみ | 0 | domain payload なし、manifest は通常規則 |
| domain payload_unavailable | `stdout_result/v1` 1行、`domain_status: incomplete`、`stable_reason: domain_payload_unavailable` | diagnostic のみ | 3 | affected payloadなし、single-domain safe manifest |
| run fatal または final manifest 不在 | `stdout_result/v1` 1行、`run_status: fatal`、reason は `run_fatal` または `final_manifest_unavailable` | diagnostic のみ | 1 | final manifestを含めrun-level Artifactなし |
| handled interrupt | `stdout_result/v1` 1行、`run_status: interrupted`、`stable_reason: run_interrupted` | diagnostic のみ | 130 | staging cleanup |
| duplicate/invalid/unselected-domain/unrequested-format | 空 | usage diagnostic | 2 | Artifactなし |

## スコープ

### 対象

- `next` domain の `snapshot` use case を CLI input から acceptance test まで届ける。
- common CLI/config/diagnostic/Artifact contract は、この slice に必要な範囲だけ導入または拡張する。
- repository-owned implementation、tests、fixtures、documentation、lockfile、CI lane を含む。

### 対象外

- runtime component tree、hydration result、browser rendering、React Server Components の実行
- non-literal dynamic import の推測、Next build/plugin 実行
- temporal component diff
- public plugin ABI、product HTML report

### 親契約として変更しない境界

- `--repo PATH` で解析対象 repository を明示し、`--output-dir PATH` を必須とする。
- `--format semantic-json|plantuml` は複数指定でき、未指定時は semantic JSON と PlantUML の両方を生成する。
- `--config PATH` を受け付ける。優先順位は CLI、`.code-structure-viz.toml`、built-in default であり、unknown key と型不正は exit 2 とする。
- 出力は一時 staging directory で完成させ、既存 path との衝突を検査してから atomic に公開する。既存 file は上書きしない。
- `--stdout SELECTOR` は高々1回のclosed grammarであり、exact-byte/unavailable-result/no-selector-summary/usage-error contractは下記sectionを正本とする。

- 解析対象 module、plugin、migration、build script、application entry point を import または実行しない。
- Git repository は read-only とし、fetch、checkout、reset、stash、clean、commit、ref 更新を実行しない。すべての Git subprocess で lazy fetch、external diff、textconv、color を無効化する。
- Artifact には repository-relative path、symbol、type、signature、relation、line range だけを許可し、source body、comment、literal、secret らしい値、absolute path を含めない。
- source view/plan、domain config、projects/targets/limits、Node/TypeScript/adapter/protocol、TrustedTypeEnvironmentが同じならrecord order、run/model/Artifact digestが決定的になる。

## 失敗・境界条件

- non-literal dynamic behaviorはrelationを捏造せずunknown diagnosticとcoverage limitationにする。
- complete/partialはdiagnostic有無ではなくpromised v1 semanticsの欠落で決める。intentional unsupportedをunknownとして完全表現できる場合はdiagnostic付きcompleteを許す。
- TypeScript parse/type resolutionの局所failureをfile/component/relation単位で隔離し、安全subset、exact coverage、全requested rendererの同一subset、safe diagnostic、redaction、explicit target completeness、entity-budget passを証明できる場合だけ`partial_safe` JSON+PlantUML+manifestを公開する。証明できない場合は`payload_unavailable` manifest-onlyとする。
- Node起動不能、adapter stdoutのprotocol外text、global schema mismatch、security invariant violation、unexpected absolute pathはresponse全体を拒否し`payload_unavailable`とする。局所的なalias/relation unresolvedは安全subsetとcoverageを証明できる場合だけ`partial_safe`を許す。
- explicit project/targetのmissing、project-scope ambiguity、out-of-scope、control/context direct target、または選択集合のtainted/excluded/failed recordは全projectへfallbackせず`CSV-NEXT-TARGET-001`の`payload_unavailable`とする。directoryはcontrol/context File provenanceを保持してもsemantic childを作らない。
- entity-per-diagram budgetはselected internal Module+Componentのdomain-local gateでdefault 500。overrideなしで501以上のdomainは`incomplete/payload_unavailable`、exit 3とし、切り捨てず、そのdomainのsemantic JSONとPlantUMLを公開しない。safe run manifestにrequested/resolved limit、actual count、diagnosticを記録する。
- malformed manifest/configでNext不在を証明できない場合はnot_applicableへ変換せずpayload_unavailableとする。
- stop condition: first-party adapter protocol、TS/TSX coverage、JS/JSX safe subset、client boundary、Node optionality、entity budgetがacceptanceで成立するまでNext diffへ進まない。

## 受け入れ条件

| ID | 観測可能な完了条件 | acceptance test |
| --- | --- | --- |
| I05-AC-001 | App/Pages RouterのTS/TSXでdeclaration identity、export binding、reachable local Component、closed props IR、two-plane relation、positive-evidence client rolesを出力し、barrel/aliasでComponentを複製しない。 | I05-AT-001 |
| I05-AC-002 | two-phase single-read freezeでcontrol/program/contextを再読せず凍結し、closed request/response/model schema、self-field除外digest preimage、versioned exact-one JSON、Python側validation/ID/coverage再計算を検証する。 | I05-AT-002 |
| I05-AC-003 | finite recognition、default/alias/star export、JS/JSX props matrix、complete PropsTypeIR、exact wrapper/dynamic/render flowを解析し、証明不能behaviorは捏造せずunknown/coverageにする。 | I05-AT-003 |
| I05-AC-004 | typed taint propagationとPython再計算可能なcount/ref/target proofを満たす場合だけ`partial_safe` JSON+PlantUML+manifest、満たさないglobal/identity/limit/target failureは`payload_unavailable` manifest-only、exit 3とする。failure-root seed、causal edge、frontierはrecordsから独立導出し、submitted witnessと完全一致させる。 | I05-AT-004 |
| I05-AC-005 | target path/cwd/node_modules/network/npm/npx/build/config/plugin/application moduleを利用せず、literal/body/comment/secret/absolute path/raw compiler textをoutput/diagnosticへ出さない。 | I05-AT-005 |
| I05-AC-006 | explicit project rootsだけを対象とし、direct `next` dependencyがない場合はNode probeなしnot_applicable、applicableでComponent 0はcomplete empty、malformed evidenceはpayload_unavailableとする。 | I05-AT-006 |
| I05-AC-007 | valid responseの後にselected/published internal Module+Componentを独立再計算し、501 entitiesならdomain `incomplete_kind: payload_unavailable`・`CSV-NEXT-LIMIT-005`・exit 3・affected JSON/PlantUMLなし・actual count付きmanifestとunavailable stdoutを出し、valid 600 overrideはrequested/resolved/count付きで成功する。all-record capは`max_model_records`として別に再計算し、snapshotへの`--from`/`--to`/`--pr-target`/`--max-changed-paths`はexit 2・Artifactなしとする。 | I05-AT-007 |
| I05-AC-008 | stdout selectorのvalid/invalid/duplicate/domain/format、exact-byte、not_applicable/payload_unavailable/fatal/interrupt result、selectorなしsummaryをtable-drivenに満たす。 | I05-AT-008 |
| I05-AC-009 | target `node_modules`/type roots/networkなしでTrustedTypeEnvironmentを使い、reserved module/global/pathのshadow/augmentation/mergeをfail-closedで拒否し、実fixture bytesのmanifest/version/digest/license、TypeScript 5.9.2 Programのparse/semantic diagnostics 0、AST/TypeChecker由来certified symbolを検証する。 | I05-AT-009 |
| I05-AC-010 | Next semantic/private protocol/diagnostic/manifest/stdout/PlantUML/writerのclosed schema/grammar/pathをmutation testで固定し、wheel/sdistにcompiled runtime/trusted declarations/lock/licenseを正しく収録してcheckout外offline Next runが成功する。 | I05-AT-010 |
| I05-AC-011 | domain config/source-plan projectionにより、Next追加前後で既存Python/SQLAlchemyのsource/config/run fingerprint、semantic JSON、PlantUML、manifest、stdout、stderrがbyte-for-byte不変である。 | I05-AT-011 |

- **I05-AC-001〜I05-AC-011がすべて満たされ、planned test commandがclean checkoutで成功すること。**
- Requirement、Design、Plan の trace table が一致し、unresolved acceptance gap がないこと。
- release boundary: Next snapshot preview。Python/SQLAlchemyのinstall/runtime requirementへNodeを持ち込まないoptional adapter separationを完成させる。

## 制約・前提

- initial platform は macOS と Linux。native Windows は対象外。
- Core/CLI/Git/manifest/Python/SQLAlchemy は Python 3.12 以上。Next adapter 利用時だけ Node.js 22 LTS 以上。
- Git 2.39 以上。CI は minimum supported と repository で明示更新する latest stable lane を実行する。
- direct/indirect dependency は lockfile で exact resolve し、license inventory と offline runtime test を持つ。runtime に network access を要求しない。
- `pyclassuml` と `tree-git-diff` への runtime/package/CLI dependency を持たない。legacy code の直接 copy は license/provenance 未確認のまま行わず、初期実装は contract/test evidence を基に repository-owned code として再実装する。
- product HTML report generation、HTML command、Tailscale publication は本 Issue の製品 scope 外。`explanation.html` は specification Artifact である。

### Round 15 review state and remediation contract

Round 15 content review は、三つのStrict試行を別物として扱う。初回connector-only試行
`issue-eight-strict-round-fifteen` の transcript SHA-256 は
`a5b7fbcb3b1b9a8655cf5bc14adea42bca9f340d589209738d64b00a2de2de19`、verification-only retry
`issue-eight-strict-round-fifteen-2` は `171cf56350a4665c4f48446fe3b91c5b77f464f442024a8dc01ece306e1ab221`、
content review follow-up `required-strict-github-connector-verificati-609` は
`85506ccacb634b1c21816032b9bd0a11fa4d3be95f6416657fab441e8011713c` である。最後のレビューは
対象SHA `c3f8e4188ca715a29d60a7454a66390938bce496`、CI `33472932927`（7/7 green）を確認したうえで
`review_status: fail`、P0=0、P1=13、P2=1、`implementation_ready: no`を返した。
このfailは履歴として保存し、fresh current-SHA Strictはpending、readinessは未確認、production
implementationは未着手とする。

Round 15で実装前に閉じる契約は次のとおりである。

1. 全 `NextRunDecision` variant が同じ immutable `NextPublicationContext` を保持する。contextは
   sealed SourceView descriptor/fingerprint、FinalSourceAcquisitionPlan descriptor/digest/seal identity、
   public Next config/request、semantic compatibility descriptor/identity versions、実toolchain/trusted
   environment、run context、run-fingerprint preimageを含む。
   domain/root/manifest/stdout/stderr/publicationはdecision以外から値を再構成しない。
2. `ValidatedResponseDecision` はschema/id、run context、targets、gate resolved limits、許可された
   pre-budget→gate transition、canonical target/export failureを検証したrequestのdeep copyを必須とする。
   元のnested request、model/proof、publication bytesを後から変更してもdecisionは変化しない。
3. response前の失敗をconfig/project/source/target/trust/process/limit/protocolのclosed
   `DecisionFailureKind` とし、requestを作れない段階はrequest-independent `NextDecisionContext` で
   run identity、stage、code、known/null counts、outcome、exitを保持する。具体的なcatalog code/ref
   permissionをAssertionErrorへ丸めず、`SOURCE-003`などの意味を失わない。
4. response count authorityは実model collectionの合計を`published_model_records`、modelに存在しない
   proof payloadだけを`proof_only_records`、その合計を`discovered_records`とする。`proof_records or
   model_records`やsubmitted countは権威にしない。model exact、model+1、aggregate+1、raw+1は、
   schema-valid wireを実際にbounded decode→schema/gate→decisionへ通し、raw→aggregate→modelの優先順位を
   固定する。`max_model_records=10,000`は、10,000件の実wireがaggregate/raw cap内で到達可能であることを
   testで示す。
5. `max_adapter_stdout_capture_bytes`（child capture）、`max_adapter_response_bytes`（完全capture後の
   private response）、`max_selected_stdout_bytes`（public selected artifact copy）を分離する。各境界は
   exactを許可し、+1は測定点で全量破棄し、decoder/publicationへpartial bytesを渡さない。public copy失敗は
   semantic outcomeを改変せず、selected artifactだけのpublication resultとして記録する。
6. child stderr harnessは`Iterable[bytes]`をchunkごとにcount-before-retainし、超過時read-stop、dispose、
   process-group termination flag、text leakなし、zero publicationを証明する。これはOS process-level test
   ではないことを明記する。
7. Source acquisitionはcaller-injected final plan/viewを受けず、`SourceDiscoveryIntent`、two-phase
   single-read、final drift checkから `seal_source_acquisition(intent, reader, inventory)` がplan/viewを
   同一sealで導出する。role/effective-role、extends/control closure、digest/size、duplicate/post-drift
   readの不一致をnegative testで拒否する。
8. target unavailable stdoutはNextの `next:semantic-json|next:plantuml` だけに許可し、reasonは
   `missing`、`component_only`、`duplicate`、`out_of_scope`、`non_program`、`control_context`、
   `project_ambiguity`、`selected_taint` のclosed enumから一件一理由をcanonical sortedに出す。
   available、not_applicable、generic unavailable、fatal、interruptには出さない。
9. IdentifierName判定は全surfaceでcontext-specificな`is_identifier_name`、`is_binding_identifier`、
   `is_declaration_key`を使うUnicode 15.0.0 checked-in tableに統一する。Other_ID sets、U+00B7、Join_Control、
   reserved word、non-NFC、control、post-15.0を検証し、0..0x10FFFF bitstreamのknown-answer SHA-256を
   minimum/latest Python laneで再確認する。host UCD依存や暗黙のsupport縮小は認めない。
10. source failureがlocal safe subsetへ隔離不能なら`CSV-NEXT-SOURCE-003`/payload_unavailable、
    local proofがある場合だけ`SOURCE-001`/partial_safeとする。同じ失敗のlocal/global差をfixtureで示す。
11. `BoundaryRolePropagation/v1`だけがrole authorityである。client seed自身はclient_dependencyではなく、
    value-closure targetだけがそうなる。client app seedはserver_candidateでなく、server traversalはclient
    entry直前で止まり、dual roleは別closureの和だけで生じる。facts/router/static edgesから再計算し、
    submitted modelとexact compareする。
12. stdout/result bytesは既存のcanonical lexicographic JSON（`sort_keys=True`、NFC、UTF-8、LF）を使う。
    手書きfield order encoderを導入せず、`target_failures`も同じcanonical orderでgolden化する。
13. HTMLは固定個数のlimitsを断定せず、schema-driven resource contractを説明し、上記のdecision/count/
    capture/seal/Unicode/role/target/orderingをPlantUMLとともに図示する。Round 15の三試行・SHA・CI・fail
    count・fresh Strict pendingを新規durable artifactへ保存し、過去のfail verdictを上書きしない。

これらはproduction implementationの完了宣言ではない。全てのlocal contract testがgreenでも、fresh
current-SHA Strictの`P0=0/P1=0`と`review_status=pass`が確認されるまで実装開始可能性は未確定である。

### Round 16 review state and remediation contract

Round 16 Strictは、verification-onlyの`issue-eight-strict-round-sixteen`とcontent reviewの
`required-strict-github-connector-verificati-627`を別の証跡として扱う。前者のtranscript SHA-256は
`e9027c5ce26d0f5f953a84a8dc10ef78252f65aed65ac47c22a82346991afb74`、後者は
`0a1fdfda86bf46e12cd3e1547ce05c1208209265a8d6e8b8a6ac6a3cccf8d895`である。content reviewは対象SHA
`732477c72c7e05d3f15818ba8a3f75a4c97dc5a9`、CI `33494926439`（7/7 green）を確認し、
`review_status: fail`、P0=0、P1=16、P2=3、`implementation_ready: no`を返した。この履歴は
`artifacts/20260901t090000z-disc-strict-spec-review-round-16.md`へ保存し、fresh current-SHA Strictは
pending、readinessは未確認、production implementationは未着手とする。

Round 16で実装前に閉じる要件は次のとおりである。

1. `SourceDiscoveryIntent`はproject roots、control candidates、固定されたdiscovery rulesだけを持つ。
   config、local extends、final paths、role mapは、凍結したcontrol bytesとinventoryから
   `seal_source_acquisition(intent, reader, inventory)`内で導出する。callerがfinal plan/viewを注入する経路、
   plan-only/view-onlyの再構成、seal後のfilesystem readを許さない。
2. 全`NextRunDecision` variantは実際の`SourceAcquisitionSeal`、resolved public request/config、観測済み
   toolchain、検証済みtrusted environment、compatibility descriptor、versioned process launch descriptorから
   一度だけ構築した`NextPublicationContext`を必須保持する。private `ValidatedAdapterRequest`とpublic request snapshotを
   分離し、fixture/default合成をdomain/root/manifest/stdout/stderr/publicationのauthorityにしない。
   `process_launch_descriptor`は省略不可であり、そのdigestをrun-fingerprintへ含める。
   pre-response/not-applicable variantの`NextDecisionContext`も省略不可で、known/null countsやfailure stage/codeを
   writerが後から再構成してはならない。
3. adapter requestはresponse前にschema、request ID、filesのbase64/size/digest/canonical bytes、limitsを検証・
   immutable sealし、response boundaryは`ValidatedAdapterRequest`だけを受ける。private responseは
   `max_adapter_response_bytes`を使い、旧`max_stdout_bytes`へfallbackしない。
4. requestを作れないconfig/project/source-discovery失敗には、invented project/request/configを持たない
   schema-validなrequest-independent `payload_unavailable` domain/root manifest branchを使う。known countsは
   実測できない項目をnull、artifactsは空、exitは3とし、stderr/stdoutも同じdecisionから投影する。
5. source localityの契約は、Python-owned immutable `SourceFailureLedger`をsealed contextへ含め、proof/modelと
   独立照合する方式とする。isolatedかつtarget-taintedでないsubsetだけ`CSV-NEXT-SOURCE-001`/`partial_safe`、
   非分離は`CSV-NEXT-SOURCE-003`/`payload_unavailable`、explicit target taintは全体unavailableとする。
6. failureはcatalog-derived closed matrix（kind、allowed stage、code、ref permission、known counts、outcome、
   exit）からのみ選ぶ。stage/codeの自由なcross product、意味を失う`AssertionError`への丸めを禁止する。
7. validation順序は、raw cap → bounded decode/aggregate → closed schema → base/path/ref/proof → actual
   model/proof-only count → model gate → entity gateとし、schema/ref invalidとmodel+1の複合入力はprotocolを先に返す。
8. per-array、aggregate、string、depthの超過はconfigured structural resource limitとして`CSV-NEXT-LIMIT-003`へ
   統一し、malformed/closed-schema/proof violationだけを`CSV-NEXT-PROTOCOL-001`とする。precedenceとmessageは
   catalog、docs、classifier、goldenで同じにする。
9. `selected_stdout_unavailable`はschema-validなcomplete/partial_safeのselected artifact branchとし、保存済み
   artifact descriptorを維持する。exact/+1 copyを検査し、copy failureでvalidated semantic outcomeを書き換えない。
10. child stdout/stderr capture、public stderr、selected copyのmeasurementsを一つのimmutable
    `PublicationBoundaryDecision`へsealしてから、domain/root/manifest/stdout/stderr/artifact/exitを投影する。
    これらのprojectionはboundary decisionだけを受け、semantic decisionと独立したpublication outcome・measurement map・
    retained bytesを受け取らない。faithful iterable harnessはread-stop、dispose、process-group termination flag、child text非漏洩を
    検査するが、OS process-level試験とは主張しない。
11. stdout field orderはmanual encoderを持たず、既存のcanonical JSON（sort_keys=True、NFC、UTF-8、LF）だけを使う。
    `target_failures`も同じorderでexact UTF-8+LF golden化する。
12. Component declarationには`@anonymous-default`を許可し、moduleごとに高々一つとする。通常のbinding positionは
    reserved wordを除く`is_binding_identifier`、property/export keyは`is_declaration_key`、明示的defaultは専用規則を使う。
13. import/export/re-export、external/trusted reference、JSX tag segmentを含む全identifier contextへUnicode 15.0.0
    checked-in tableを適用し、Other_ID、U+00B7、Join_Control、reserved、non-NFC、control、post-15.0を拒否/受理表で固定する。
    full scalar bitstream digestをminimum/latest CI laneでknown-answer検査する。
14. resolverはsealed roots/taintからmissing、component_only、duplicate、out_of_scope、non_program、control_context、
    project_ambiguity、selected_taintの8理由を導出し、失敗targetごとに一つだけreasonを要求する。混在targetの
    resolver→proof→decision→diagnostic→domain→root→stdoutを検査する。
15. `BoundaryRolePropagation/v1`はfacts/router/static value closureからのみ導出する。client entry seed自身は
    `client_dependency`でも`server_candidate`でもなく、server traversalはclient entry前で停止する。dual roleは別の
    closureが両方を証明した場合だけ許し、PlantUMLのstale allowanceを残さない。
16. process launch descriptorはverified absolute Node realpath、symlink policy、argv、固定env allowlist/denied env、
    stdio、FD inheritance、process groupをversion付きでsealする。available/unavailable/not-applicable各variantで
    toolchainのnode statusと一致する実測descriptorを明示し、PATH shadow、symlink、hostile env、locale/TZ、extra FD、
    descriptor省略・preimage差し替えをclosed schema/reference testで拒否する。

これらの要件は後続実装の完了宣言ではない。local契約がgreenでも、fresh current-SHA StrictのP0=0/P1=0と
`review_status: pass`が確認されるまでreadinessは未確認のままとする。
