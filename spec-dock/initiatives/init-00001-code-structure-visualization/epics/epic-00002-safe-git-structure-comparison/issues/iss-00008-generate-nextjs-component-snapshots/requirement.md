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
- transport/processは20,000 files、4 MiB/file、64 MiB decoded source、96 MiB encoded stdin、JSON nesting 64、8 MiB/string、100,000 total/20,000 per collection array items、100,000 model records、16 MiB stdout、64 KiB stderr、60秒、512 MiB V8 old-spaceをv1上限とし、超過はsilent truncationせず`payload_unavailable`とする。総RSS上限はv1で保証しない。

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

### semantic contract

- entityはphysical-path `ModuleEntity`とdeclaration-anchored `ComponentEntity`。named declarationまたは`@anonymous-default`でComponentを識別し、range/export/route/wrapper/propsをidentityに含めない。
- memberは`ExportBindingMember`、`ImportBindingMember`、`PropMember`。barrel/re-export/aliasはbindingを増やすがComponentを複製しない。adapterは凍結UTF-8 source bytesからowner file、byte span、token identity、syntax kind、exported name、value/type role、re-export/starを持つ完全な独立observationを返し、Pythonがcensusとresolution（component/value/type/unknown）を照合する。public `ExportBindingMember`はvalue exportが一意なComponentへ解決した場合だけで、value/type/unknownはcoverage-onlyとする。export/route rootからproven render/wrapperで到達するlocal Componentだけを`reachable_local`として含める。
- Component認定はsafe React callable/construct signature、closed React class provenance、recognized UI route default、proven JSX output-flow、closed wrapper allowlistのpositive evidenceを要求し、PascalCaseだけで認定しない。
- propsはTypeCheckerのeffective signatureから取得し、primitive/type-parameter/redacted-literal/reference/array/tuple/union/intersection/function/object/opaqueのclosed type IRへ正規化する。literal value、function parameter名、generic名を公開せず、complexity limitはtruncationではなくopaque+coverageで表す。
- relationはmodule planeの`static_import`/`literal_dynamic_import`とcomponent planeの`jsx_render`/`component_wrap`を分離する。lexical scanやruntime tree推測をせず、return outputへ流れるbounded expressionだけを追う。
- client boundaryはdirect `client_entry` fact、router context、static value edgeから導く`client_dependency`/`server_candidate` role、`unknown`で表す。同一Moduleのdual roleを許し、no directiveをserverと断定しない。boundary crossingはunderlying edgeのfacetとする。

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

有効な selector の対象が `not_applicable`、`payload_unavailable`、run fatal、または handled interrupt により利用不能な場合、stdout は次の `code-structure-viz.stdout-result/v1` JSONを決定的な1行で出す。field order は `type`、`schema`、`selector`、`availability`、`domain_status` または `run_status`、`stable_reason`、`artifact` とし、`availability` は false、`artifact` は null である。domain selector で domain outcome が確定している場合だけ `domain_status`、run-level outcome では `run_status` を使う。`manifest` selector も final manifest が存在しない場合は同じ規則を使う。既存の exit 0/1/3/130 を変更しない。

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
