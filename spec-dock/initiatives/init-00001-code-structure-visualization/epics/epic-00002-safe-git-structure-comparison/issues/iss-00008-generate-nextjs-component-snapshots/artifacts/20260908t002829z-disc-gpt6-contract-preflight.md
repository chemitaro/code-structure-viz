---
種別: disc
ID: "20260908t002829z-disc"
タイトル: "GPT-6 契約 preflight と修復記録"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-09-08"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: []
reflected_to: []
---

# GPT-6 Max 独立preflightと修復状況（2026-09-08）

この記録は作業ツリーのpreflightです。clean/pushed固定SHAの最終レビューではありません。
基点は d660608ff5af76b7c65ca7d067ac797d3cea225f。対象はIssue #8の実装前契約と参照テストで、製品実装は含みません。
レビュアーは別のGPT-6 Astra / reasoning Max agent（current_contract_review）。主担当が修正し、レビュアーはread-onlyです。
ユーザー指示により外部ChatGPT系スキルは呼び出していません。外部Strict passとは表記しません。

## 初回の再現と処置

| ID | 原群 | 重要度 | 独立レビューで確認した再現 | 現在の処置 |
| --- | --- | --- | --- | --- |
| GPT6-P1-01 | G04 | P1 | export宣言内requireをskip。literal先頭+式のimportをliteral扱い。dep読取失敗でもentryがsafe | export bodyを走査、引数全体を確認、不確定module planeからfalse-partialを拒否する回帰候補 |
| GPT6-P1-02 | G03 | P1 | 親configのfiles/baseUrl/pathsが子rootで再解釈される | field originを継承し宣言元から一度だけ解決、nested local extendsをsingle read |
| GPT6-P1-03 | G03 | P1 | exact aliasとwildcard両方の既存fileを同格候補としambiguous | exact→非wildcard文字数→同順位宣言順、最初の存在するreplacementへ固定 |
| GPT6-P1-04 | G03 | P1 | base_url='.'・@aliasがconfig/source-planだけ通りrequest/semanticで拒否 | compiler-optionsをnext-config-v1の共通定義へ$ref。実request→response→semantic回帰 |
| GPT6-P1-05 | G02 | P1 | entity超過のLIMIT-005がresponse_validation。failure移行で実値digestをmarkerへ戻す。異なる不正raw応答が同じpending digest | model_validationへ固定、観測prefixを保持、actual raw bytesの観測digestへ。未観測suffix全般の監査は継続 |
| GPT6-P1-06 | G02 | P1 | package matrixにnode_status=availableだけ渡すとcomplete/validated responseを生成 | package projectionからnode_status入力とsuccess分岐を除去。permissionのみ。caller-forged successをschema/validatorで拒否 |
| GPT6-P1-07 | G02 | P1 | malformed package/configをSOURCE-003へ書換え、stage union外でassert | 元のcatalog code/stageを保存しtyped source結果へ投影 |
| GPT6-P1-08 | G05 | P1 | production process observationがwrong argv/cwd/env/versionをhash更新だけで受理 | 独立したpolicyを必須化。Node/adapter/argv/cwd/env/FD/group/limits/versionを照合。contextにもpolicyを封印。再hash mutation 12例を追加 |
| GPT6-P1-09 | G06 | P1 | actual publicationのselector None/manifest/非可用domainでschema-invalidまたはKeyError | 4 selector × 4 semantic状態のactual finalizer/schema/全出力回帰。未生成artifactはcopy未試行＋typed resultへ。capture失敗の追加検証中 |
| GPT6-P1-10 | G07 | P1 | namespace imported_name=nullはschema通過してもmodel validator/rendererで失敗 | 候補修正済み。local_name/binding_kindをID・duplicate keyへ追加し、type/value各2 aliasをactual publicationまで検証。独立再確認待ち |
| GPT6-P1-11 | G07 | P1 | string-named exportがactual scannerでassertまたはdisposition欠落 | 未修復。private syntax observationとcoverage/diagnostic/public nameの結合 |
| GPT6-P2-01 | G03 | P2 | shadowed jsconfigのmalformedでtsconfigも失敗。builtinをnot_applicable・fake tsconfigと表示 | config選択を読取前に固定。builtinはconfig_path=null/default membership |
| GPT6-P2-02 | G06 | P2 | summary/manifest overflowのsizeが旧candidate、shaが新candidate | copy計測時のsha256をmeasurementへ封印し、最終manifest descriptorと分離。selected-size/shaとfinal-result-size/shaを実bytesで確認 |
| GPT6-P2-03 | G04 | P2 | unsafe specifierのopaque IDにsource content/spanがなくoccurrenceを混同 | source content hashとUTF-8 spanをpreimageへ追加 |

既知未完了事項: usage/fatal/interruptのactual decision全経路、early failure observed-prefix全般、
finding-level coverage registry、compatibilityの実content preimage、inventory文書と将来package検証計画、
R/D/Pの現行規則とhistorical proseの統合。これらを未実装adapterの証拠不足として除外しません。

## G03/G04再レビューで追加された例

| ID | 再現 | 修正候補 |
| --- | --- | --- |
| GPT6-R01 | jsconfigのみのcontrol_candidatesでtsconfigを隠せる | candidatesは選択権限でない。tsconfig優先を全候補名から決定 |
| GPT6-R02 | export {x}の後にsemicolonなしのconst x=require(...)を置くとskip | local exportはclosing braceで走査を戻す |
| GPT6-R03 | ab*bcがabcにprefix/suffix重複で一致 | specifier長 >= prefix長+suffix長 |
| GPT6-R04 | (require)(...), require?.(...), const load=requireがopenにならない | require値参照の不確実性をmodule_planeへ伝播 |
| GPT6-R05 | import dep = require(...)がimport-from走査で消える | import-equalsの実行式を走査し続ける |
| GPT6-R06 | .tsの<number>1をJSXと誤認して後続requireを消す | .tsはJSXとして扱わず、未閉鎖JSXもopenにする |
| GPT6-R07 | paths replacement '.'がschema-invalid成功になる | 現行non-root path grammarどおりCONFIG-001へ |
| GPT6-R08 | files/includeで正規化後同一pathになると裸assert | 正規化後の順序保持dedupe |

R01〜R03はレビュアーが修正有効性を再確認済み。
R04〜R08も修正候補を反映し、同じレビュアーが5件の解消を限定再確認（16 passed）。
主担当focused testsは27 passed（source失敗/applicability等）と24 passed（追加scanner/config/provenance例）。
これらは互いに一部重複するため合算して全件数とはしません。

## 文書・Unicode

人間向けHTMLは24 round分の履歴追記を本文から外し、8図の一貫した説明へ再構成。
過去レビューは証拠リンクとして保持。取得union・厳密なvalidation順序も折りたたみで説明します。
最初の再構成時のPlantUML検証は8/8表示・拡大/keyboard/focus trap検証pass。
その後の本文追記も再検証し8/8＋拡大操作pass。sandbox内のChrome起動は15秒timeoutとなり、承認付きの同一validator再実行で完了しました。
既存のTailscale preview entryを再利用し、同一のauthoritative HTMLを公開しました。
preview: http://100.85.74.8:8765/20260831t022707z--nextjs-component-snapshot-best-practice-guide.html

Unicode 15.0.0の公式19,074行をオフラインfixtureで検証し、7 passed。
scalar単体KATだけでは複数字符号点の正規化を証明できないため、公式multi-scalar行も保持しました。
出典・license・生成規則はdocs/contracts/next-unicode-nfc-v1.md。

## 中間時点の確認履歴

修正中の全契約テストはlegacy fixtureのresponse observation欠落を検出しました。
actual wrapperは緩めず、legacy fixtureにも明示的な応答bytesを渡すよう修正し、414 passed。
その後、G04のfrozen bytes再導出接続を追加した時点でNext/schema 407 passed（Unicodeを含まない）。
以降の追加G04/G05/G06回帰を含めた全品質gateは再実行が必要です。部分実行件数を合算して全件数とはしません。
commit/push、全品質gate、最終固定SHAレビュー、implementation readinessはまだ完了していません。

## G04 constructor・partial requestの追跡

SourceAcquisitionSealはgraph、plan、viewの自己hash一致だけでなく、captured bytesからgraphを再導出します。
同じinventory/control bytesからconfig option origins、membership、role mapも照合します。
read failureはviewの閉じたread_failuresに封印し、失敗nodeのcontent_sha256はnullです。空bytes hashを観測として合成しません。
ledgerは封印read_failuresとexact一致し、callerのfailure追加/削除/stage変更を拒否します。
過去のraw graph fixture helperは、実files＋実read failureを経由するfixtureへ置換しました。

追加の独立レビューで、以下を再現しました。

| ID | 重要度 | 再現 | 修正・検証 |
| --- | --- | --- | --- |
| GPT6-R09 | P1 | path:src/path:.が失敗descendantを含んでもpartial | segment ancestryでtarget集合を判定。file/directory/root/safe target 4例 |
| GPT6-R10 | P1 | constructor引数のplan/viewを後から変更できるmutable alias | constructor入口でもdefensive copy。呼出し元と返却値の双方を変更する検証 |
| GPT6-R11 | P2 | failed dependencyの正常importerを除外するとPartialSourceSealが裸assert | captured minus failure closureとexact結合。request bindingにも同一ledgerを渡す |
| GPT6-R12 | P2 | partial requestはfilesを除くがprojects.file_idsを残す | retained filesからfile_idsを再生成後にrequest_idを計算。有効な未filter requestを入力しresponse→contextまで検証 |

R09〜R11の修正は独立レビュアーが10 passedを確認。R12も実importerを含むrequest→response→contextについて独立再確認済み。
source graphのedge削除/target/span交換、config origin変更をschema-validかつ全hash再計算で試し、拒否を確認しました。

## G06 公開時の診断の区別

selected-copy超過は元のsemantic/domain/artifactsを書き換えず、runをincomplete/exit 3とします。
同じCSV-NEXT-LIMIT-003 familyにscope=publicationを明記し、root manifest/stderrだけへ追加します。
既存domain診断は保持し、diagnostic.outcomeのpayload_unavailableはこのscopeの公開payloadを指します。
capture/public-stderr超過はdomain payloadを公開できない別branchです。
copy測定対象のsize/sha、最終manifestのsize/sha、typed resultのsize/shaを別々に保持します。

## 現在の到達点（2026-09-08 追記）

この節は上記の時点別記録を更新します。全群の閉鎖、固定SHA review pass、実装開始可能を宣言しません。

### G05/G06の追加独立指摘と修正候補

前回の限定レビューは42 passedでしたが、独立レビュアーが既存ケース外で次の5件を再現しました。

| ID | 重要度 | 再現 | 主担当の修正と回帰 |
| --- | --- | --- | --- |
| GPT6-R13 | P1 | finalizer引数がsealed capture capを拡大し、同一requestから公開可否を変更する | capをcontextから導出。指定値は正整数かつsealed値以下だけ。4種の拡大を拒否 |
| GPT6-R14 | P1 | actual parse_file partial proofに無関係なFLOW-001/symbol=nullを生成し4selectorともassert | validated model診断とfile-local failure rootからSOURCE-001/pathを導出。actual partial response→全4selector→public surfacesを検証 |
| GPT6-R15 | P2 | capture countersを差替え、measurement hashを再計算すれば実bytes長と不一致でも受理 | constructorでallowed、failure、cap、captured/retained/raw/manifest bytesの関係を照合。3再hash mutation |
| GPT6-R16 | P2 | wire stdout.candidateが計測時ではなく診断追加後のmanifestを参照 | 測定時candidate size/shaをwireへ投影。最終artifact descriptorと区別 |
| GPT6-R17 | P2 | capture失敗とselected cap超過の同時発生でassert | payload_unavailableを先行状態として維持。4selector×3capture failure×2selected capの24ケース |

G05の固定policyからの観測差替え拒否は独立確認済みです。
policyとobservation双方を別のowner許可済みNodeへ変更することを偽装とは扱いません。
ownerがprivate cwdの所有・mode・target separationを確認してからpolicyをsealする構築前提を文書化しました。
verified handleはstdio 0..2と区別しnumber>=3に限定。追加mutationを含め13ケースです。
実OS上でのhandle execution・process group・killは製品実装時の必須確認で、現在の参照fixtureでは証明しません。

export failure診断はvalidated reexport witnessのowner moduleを参照します。
旧status-only fixtureは記録済みmodel診断を持つよう明示しましたが、空proofの旧fixtureをactual adapter証拠へ昇格しません。
finalizerとconstructorのmaterialization重複、test helperへのrenderer逆依存は構造上の残課題です。

### G07 namespaceとG08 compatibility

- namespace importはimported_name=null、local_component_id=null。local_nameとbinding_kindをidentity/duplicate判定へ追加。
- type/valueそれぞれで同一moduleを指す2 aliasをclosed census fixtureへ追加し、request→response→semantic→PlantUML/publicationを検証。
- string-named exportのactual scanner/disposition接続はまだ未修復です。namespaceだけの成功でG07全体を閉じません。
- compatibilityは実trusted environment digest、Node status/version/content SHA、adapter schema/version/content SHA、TypeScript identityから再導出。
- portable toolchain preimageからhost path、OS、FD、cwd、limitsを除外。観測contentの変更は互換性を変え、host/limitだけの変更は変えません。
- raw responseのcompatibility descriptorをcontextとexact照合し、自己hashだけ整合した別content由来descriptorを拒否。
- fixtureのNode/adapter SHAは明示したテスト値です。現在のOS上の実binaryを取得した証明ではありません。
- docs/contracts/next-compatibility-v1.mdに独立known-answerを記録。Unicode公式19,074行の検証も保持しています。

### 最新の直接実行結果

| コマンド | 結果 |
| --- | --- |
| uv run pytest tests/contracts/test_next_contracts.py tests/contracts/test_json_schemas.py tests/contracts/test_unicode_15_0_nfc.py -q --tb=line | 492 passed in 69.16s |
| uv run ruff format --check . | 162 files already formatted |
| uv run ruff check . | All checks passed |
| uv run mypy src tests | 139 source files, no issues |
| uv run pytest -q --tb=line | R18修正後: 1377 passed, 1 skipped in 193.12s。修正前の履歴値は1371 passed, 1 skipped |
| python3 ./spec-dock/scripts/spec-dock validate | 命名修復後: ok, nodes=10 |

部分実行件数は重複するため合算しません。上記はdirty candidateの証拠です。
R13〜R17は同じ独立GPT-6 Max reviewerが反例の閉鎖を確認しました（指定57 passed in 12.86s）。
G05補足とG07 namespaceも新規findingなし。G08では次の追加P1を確認しました。

### GPT6-R18: raw envelopeを再構築した場合の互換性差し替え

通常のresponse boundaryはforeign compatibilityを拒否しましたが、正常decisionのraw_response_bytesとSHAを
replaceするとconstructorがmodel/proof一致だけで受理し、finalizerがpublishedへ進みました。
その際、finalizerの再decodeはfailure decisionを返しても戻り値が捨てられていました。
これは実OS証拠不足ではなく、現在の参照公開経路のP1です。

主担当はconstructorと通常response boundaryへ同じ全envelope metadata/request結合を適用しました。
constructorはcompatibility descriptorとsealed context、response観測identityと実bytesも照合します。
旧status fixtureにも全wire metadataを持たせ、空proofをbindingの例外にしていません。
ただし空proofを持つ旧status fixtureのG09上の位置づけは未完了です。

finalizerは既にvalidated decisionを受けるAPIなので、不要な二度目のresponse decodeを外しました。
初回bounded capture→decode→decisionは専用回帰で検証し、finalizerはcapture bytesと封印wireの一致を確認します。
foreign descriptorに加え、観測digest更新を伴う6種のwire metadata差替えを拒否する回帰を追加しました。
focused 55 passed。型注釈の不整合1件をテスト呼出しで修正しmypy139 files pass。
独立レビュアーがR18の閉鎖を確認しました（25 passed in 6.48s）。
protocol、identity_versions、limits、run_context、extra field、必須field削除も再hash・観測更新後に拒否しました。
二度目decodeが呼ばれないこと、別capture bytesの拒否、初回capture→decisionも確認しています。
これは限定preflightの閉鎖であり、G02/G07 string export/G09や固定SHA review passには一般化しません。
全repository再実行は1377 passed, 1 skipped。ruff format/check、mypy139files、SpecDock nodes=10、git diff --checkも通過しました。
skipはLinux専用のphysical Unicode spelling契約です。該当integration fileの再確認は5 passed, 1 skipped（0.43s）でした。
issue active showはiss-00008を確認。src、pyproject.toml、uv.lockのdiffは空です。
この検証済み候補を中間checkpointとしてcommit/pushします。既知未完了群は維持し、最終認定のcommitとは区別します。

### Artifact命名の修復

前作業で同秒slotを3ファイルに割り当てていたためvalidateと通常Artifact allocationが停止しました。
この作業で作った未commitの2回答とpreflight記録を、内容を保持して確認済みignored Workbenchへ退避し、
通常のartifact import file / new artifact discで保存し直しました。
回答本文のSHA-256は統合Artifactの2値と一致します。削除・短縮はしていません。
このファイルのIDはCLIが返した値を使用しています。import結果のcommittedはArtifact publicationを指し、Git commitではありません。

### 未完了の順序

1. G02: early failureの実観測prefix、package permission→actual decision、usage/fatal/interruptのNextRunDecision全経路。
2. G07: 下記の限定再検証で閉鎖。全体の固定SHA認定とは区別する。
3. G09: finding→criterion→vector→producer→validator→testの意味の一致。旧R23 surrogateとfixture-only censusの位置づけ。
4. G10: canonical Requirement/Design/Planからround追記の競合を除き、現行規則と履歴証拠を分離。
5. G11: inventoryを参照fixtureと将来buildへ分けたschema/docsをcanonical実装計画に反映。実package検証は将来実装gate。
6. 全検証、checkpoint commit/push、修復後のclean/pushed固定SHAに対する独立レビュー。

承認済み作業範囲は資料と実装前の契約・参照テストです。src、依存、lockfile、製品adapterは変更していません。

## G07 string exports・R22 privacyの限定閉鎖

基点はpush済み`00abcf9b090aac6e65e10c8d10b6e7967ad6587b`。上記のstring export未修復という
時点別記録をこの節で更新する。独立レビュアーは同じGPT-6 Max agentであり、外部Strictは利用していない。

G07のprivate occurrenceをactual `next-adapter-response-v1`のclosed branchへ接続した。
凍結fixtureのraw UTF-8 span/token identity、decoded UTF-16BE name digest、form/safe_identifier、
resolution/basis/dispositionを保持する。生のstring名はpublic bindingへ変換しない。
list export、quoted imported name、string-named namespace export、type-only、empty/escaped/control/
補助平面文字を検証する。文字列内の`type`・`}`・`,`を構文として消費しない。

3経路は次のとおり。以前のcaller booleanだけのR23 helperは閉鎖根拠に使わない。

| 条件 | actual結果 |
| --- | --- |
| 明示path targetのownerに該当 | TARGET-001 / unsupported_export / unavailable / exit 3 |
| 非component/valueまたはtype-onlyの証明あり | UNSUPPORTED-001 / complete / exit 0。既存value/type coverageとinfo countへ計上 |
| component、可能性あり、未解決 | EXPORT-001 / unavailable / exit 3。private evidence保持、public binding/artifactsなし |

参照分類は閉じたfixture grammarのもので、汎用AST/TypeCheckerの実装証明ではない。
`docs/contracts/next-export-observations-v1.md`にwire fields、根拠、優先順位、制限、製品経路の将来gateを記載した。

### GPT6-R22（P1）: private envelopeのpublic sidecar漏出

G07の新しい公開bytes検査で発見し、レビュアーが基点00abcf9にも存在する既存の漏れと確認した。
旧`next_run_decision_projection`がrequest.snapshot()とdecoded response全体をpublic decisionへコピーし、
domain/root manifestにsource `content_base64`とprivate proofを公開していた。public schemaもこれを許可していた。
Requirementのsource body/comment/literal/secret禁止、public/private requestの区別、semanticのcontent除外と矛盾する。

修正はpublic projectionとそのschemaに限定し、request/responseを実canonical bytesのSHA-256・byte length・
canonical flag（requestにはrequest_idも）のdescriptorへ変更した。private request/raw/proofとR18の全bindingは維持する。
safe semantic recordsやsource-graph frontier全体を一律hash化する変更ではない。

### 検証と独立判断

- 主担当: `-k 'string_export or public_decision_exports'`は37 passed（3.55s）。
- lexical hardening後の広めのexport/privacy回帰は71 passed（4.63s）。
- 直前のNext+schema全体は522 passed（63.64s）。最新テスト追加前に収集した実行なので最新版全体の件数とはしない。
- 独立レビュアー: 修正後36 passed（3.49s）。追加probeで6 source cases × auto/explicit × 4 selectorsの48 publicationと、
  不正private response × 4 selectorsの4 publicationを確認。private source/proof/string_namesの流出なし。
- 独立probeでname metadata/解決根拠の協調偽装7件を拒否。request/raw response/proofの内部保持も確認。
- 新規privacy testの初回4件は必須引数不足のTypeError。既存`_run_context`の利用へ修正後に通過。失敗を隠していない。
- 独立判断はG07 string exports＋R22に限るP0/P1=0。dirty candidateの限定preflightであり、全体の固定SHA passではない。
- 全repository実行: 1414 passed, 1 skipped（180.78s）。最後のkeyword/type token hardeningは、この実行の開始後に変更したため、最新版のfocused 71 passedに加えNext+schema全体も再実行し、528 passed（64.82s）を確認した。
- ruff format/check、mypy139 files、SpecDock validate nodes=10、active iss-00008、git diff --checkを確認。
- `src`、`pyproject.toml`、`uv.lock`のdiffは空。新規ファイル名はlowercaseのみ。

### G02で独立再確認した未修復P1

同じ基点に対するread-only独立調査で、以下の3件を確認した。関連既存テスト20 passed（0.74s）でも残る。

| ID | 現在の再現 | 必要な修正 |
| --- | --- | --- |
| GPT6-R19 | apps/a、apps/bでpackage読取後のmalformed configがcode/stageだけになり、異なる実観測値が同じmarker digestへ戻る（schema-valid） | 早期取得結果に実観測prefixを保持し、decision/publicationへ渡す。未観測suffixのみnull |
| GPT6-R20 | actual NotApplicableDecisionがmatrixを受けず、applicable/malformedからもNA・exit 0を生成可能。request-bound互換constructorにも矛盾 | actual matrixをsealし、non_applicableだけ許可。malformedは専用failureへ接続 |
| GPT6-R21 | usage/fatalはSourceAcquisitionDecisionProjectionで止まり、NextRunDecision/finalizerへ接続せず、interruptの実variantもない | 既存RunOutcomeへの対応を含む純粋run-level→publication契約を定義・検証 |

実Git reader、Node非起動の実観測、OS signal/process-group、CLI filesystem/stdout/stderr/exitは実装時gateへ分離できる。
上の値レベルの矛盾は未実装adapterの証拠不足として除外しない。次はR19–R21、G09、G10、G11を閉じる。
人間向けHTMLは今回未変更で、既存の8図検証済み資料を保持。製品実装には着手していない。

## G02 R19/R20: 実観測から公開結果への接続候補

G07/R22の検証済みcheckpointは`af151dd2620eeda084a780ea335ec80bcf2c95e6`として通常commit/push済み。
parentは`00abcf9b090aac6e65e10c8d10b6e7967ad6587b`。branch維持とリモートSHA一致を確認した。
以下はその後の候補修正であり、独立再レビューが完了するまで閉鎖とは扱わない。

### 変更と根拠

- R20: actual NA constructorは`PackageApplicabilityMatrix`を必須化。non_applicableだけを許可し、
  applicable/malformed/mixedを拒否する。requestを引数にする旧NA互換constructorを削除した。
  `NotApplicableDecision`自体でrequest保持を拒否し、matrixと両contextの観測identityを照合する。
- R19: readerは実読取bytes・実読取失敗・列挙したroot/pathを保持。失敗後の再readをせず、
  packageのread/failed/missing/unobserved、configのpath/size/SHA/failureからidentityを作る。
  package観測が未完了ならmatrixを合成しない。成功して読んだことと解析成功を区別する。
- `SourceAcquisitionUnavailable`の早期実結果はprovenanceを保持し、
  `source_acquisition_failure_decision`でactual `PreResponseFailureDecision`へ接続する。
  provenanceなしのstatus-only fixtureはこのseamを通れない。対象はapplicability/source_controlのみ。
- publicationはdecision contextの観測をそのまま保持する。独立run fingerprintへ
  `observation_provenance_digest`を加え、別root/別取得bytesを区別する。未読sourceだけの変更は区別しない。
- actual公開までテストした結果、root manifestのdiagnostic enumにAPPLICABILITY-002が欠落していると判明。
  当該1codeを追加した。またcontrol read failureのSOURCE-003に必要なpathをtyped resultへ保持した。
  不正packageは専用APPLICABILITY-002 / exit 3へ進み、NA / exit 0にはならない。
- raw source/control本文は公開していない。取得前のrequest/source plan/limits/runtime/budgetを作らない。

### 直接検証

- R20の新規7ケースは未接続時のTypeErrorでREDを確認。その後、NAと既存publication関連30 passed。
- actual early failure 16ケース（4原因×4selector）とmatrix/identity関連は36 passed（2.74s）。
- その初回実行は12 failed。8件はAPPLICABILITY-002のroot schema欠落、4件はSOURCE-003のpath欠落。
  上記の契約不整合を修正して通過させた。schemaを外して回避していない。
- Next/schema全体: `uv run pytest -q tests/contracts/test_next_contracts.py tests/contracts/test_json_schemas.py --tb=short`
  は552 passed（68.14s）。この時点の全repositoryは1438 passed, 1 skipped（188.63s）。
- ruff check、ruff format --check（163 files）、mypy（139 files）、SpecDock validate（nodes=10）、
  active iss-00008、git diff --checkを確認。src/pyproject.toml/uv.lockの差分なし。
- 存在しない`test_schema_examples.py`を指定した実行はcollection前exit 4で検証0件。
  実在する`test_json_schemas.py`へ訂正した上記552件と区別する。

### private evidenceの追加結合

最初の限定独立再レビューはP0=0/P1=2で、R19/R20はまだ閉じなかった。指定25 passedと正常公開8例でも、
次の協調差替えが残っていた。新しい別findingではなく同じ2件の未完部分として扱う。

| ID | 独立再現 | 補強 |
| --- | --- | --- |
| R19 | tsconfigが`{`の結果へ`[`のprovenanceを交換して4selectorで公開。read failure pathを未読fileへ変更しても公開 | private `EarlySourceReadPrefix`に凍結bytes・実failure・rootsを保持し、provenanceをinit=Falseで導出。code/stage/pathを同じ原本と照合 |
| R20 | 実Next dependencyのmatrixでentry/aggregateをnon_applicableへ協調変更し、4selectorでNA exit 0を公開 | missingを含むprivate package bytesを保持し、constructorとNA入口で分類を再導出。bytesなしのpublic構造検証用matrixにはNA authorityを与えない |

補強後のfocused回帰は50 passed（3.07s）、ruff/mypy139 files pass。
通常replaceに加え、object.__setattr__によるprovenance/path/分類差替えを入口で拒否する。
frozen tupleの内側もtupleとbytesに制限し、mutableな観測原本を受け取らない。
公開するmatrix identityはpackageのraw digest/sizeも含むが、package/control本文は非公開のままである。
上記1438件は補強前の証拠なので、最終全体検証として再利用せず再実行する。独立再判定も依頼済み。

次の限定再判定は指定28 passed・正常公開8例を確認したが、同根P1が2つ残った。
prefix.pathとresult.pathの同時交換（実failed_readsは変更しない）と、NA作成後の呼出元matrixの3fields交換である。
前者はprefix.provenance()でも構造とfailure path所属を再検証し、prefixのconstructor/getterの所有コピーで補強した。
後者はNotApplicableDecisionがmatrixをconstructor/getter双方でコピーし、外部aliasから切り離した。
回帰には呼出元・返却matrixの全fields変更後も元のNAの公開bytesが変わらないことを追加した。
再度focused50 passed（3.27s）、ruff/mypy pass。555件のNext/schema実行はこのalias補強前なので、最終候補と区別する。

最終の限定独立再確認でR19/R20はP0/P1=0となった。対象回帰28 passedと正常公開8例を確認し、
prefix.path/result.pathの協調偽装・直接不正prefixを拒否、constructor/getter両側のalias隔離、
呼出元/返却matrixの変更後も封印済みNAと公開bytesが不変、4selectorのschema/privacyを確認した。
dirty candidateの限定閉鎖であり、R21・後段source・G09・全体固定SHA認定は対象外である。
R19/R20候補時点の基礎全repositoryテストは`1441 passed, 1 skipped`（201.45秒）で完了した。
R21追加後の最終候補ではNext/schema全体が`573 passed`、全repositoryが`1459 passed, 1 skipped`
（177.17秒）となった。ruff check、ruff format --check（163 files）、mypy（139 files）、
SpecDock validate（nodes=10）、`git diff --cached --check`も通過した。製品adapter、CLI、依存関係は変更していない。

### R21の独立設計助言（参照seam実装済み／製品未実装）

同じGPT-6 Max reviewerが、既存`src/code_structure_viz/core/outcomes.py`の`RunOutcome`と
`artifacts/streams.py`の`StdoutEmitter`を使う最小経路を確認した。terminal結果をNext semantic
finalizerの手前で分岐させ、新しい包括unionや同じstatus決定表を増やさない方針を推奨する。

| 原因 | 既存結果 | 診断 |
| --- | --- | --- |
| 実root overlap | RunOutcome.usage、exit 2、domain/manifestなし | CSV-NEXT-PROJECT-001 |
| 実snapshot revision drift | RunOutcome.fatal、exit 1、domain/manifestなし | CSV-NEXT-SOURCE-INTEGRITY-001 |
| 捕捉済みPublicationInterrupted / KeyboardInterrupt | RunOutcome.interrupted、exit 130 | CSV-INTERRUPT-001 |

referenceに小さい`next_terminal_run_publication(cause, selector)`を置き、既存outcomeと
stdout/stderr bytesを返す案。Next diagnosticは現時点のcore enumに押し込まず、既存reference catalogと
JSONL rendererで構築・schema照合する。interruptは既存core stderrを利用できる。

参照seamでは`CSV-NEXT-PROJECT-001`のcatalog/schema outcomeをusageへ修正し、
`next_terminal_run_publication(cause, selector)`を追加した。root overlapは`RunOutcome.usage`/exit 2、
source-integrityは`RunOutcome.fatal`/exit 1、捕捉済みPublicationInterrupted/KeyboardInterruptは
`RunOutcome.interrupted`/exit 130へ分岐し、既存`StdoutEmitter`とcore interrupt `StderrEmitter`を再利用する。
terminal branchはdecoder/finalizer/artifact readを呼ばず、fatal/interruptのselector省略はsummary、
指定selectorはtyped unavailable、usageは全selectorでstdout空を返す。`validate_run_status_vector`は
terminalの余計なpublished bytesを拒否し、emitterのfield orderとcore/Next stderr JSONLを区別して検証する。
初回の独立レビューはP1=1だった。PublicationInterruptedに付属するDiagnosticのmessage/pathを
そのまま公開できるalias漏れを、canonical core `CSV-INTERRUPT-001`の再構築へ修正し、secret path/message
のnegative回帰を追加した。修正後の独立再レビューはP0/P1=0。R21関連回帰は18 passed（4原因×4selector、
artifact注入拒否、Diagnostic各欄の差し替え耐性）である。これはreference seamの契約証拠であり、OS
signal/process-group/cleanup/実プロセスおよび製品adapterの実装・証明ではない。

R19/R20の限定独立判定はP0/P1=0で閉じ、R21は参照seamの限定回帰まで実装したが、これはdirty candidateの
限定preflightである。次はOS/process境界を含むR21後段、G09の証拠対応、G10のcanonical R/D/P統合、
G11の将来package計画、ならびに全体の固定SHA認定である。
このcheckpointで全体P0/P1=0、外部Strict pass、implementation readiness、Issue完了を宣言しない。

### G09 executable coverage bijection (2026-09-08)

R23のcoverage helperが全18 criterionを同じ`runtime_vector_round23_applicability` producer、同じ
validator、同じcoverage meta-test、synthetic `r23-positive/negative` vectorで埋めていた。これは
criterion→vector→producer→validator→testの実体を検証せず、fixture-only surrogateを通してしまうため、
実装前のG09 gapとして扱った。

`tests/contracts/next_reference_validation.py`にcriterionごとのsubstantive test名を固定し、登録済み
`R23_RUNTIME_VECTOR_REGISTRY`からpositive/negative pair、positive producer、共通validatorを導出する
`_r23_registry_coverage_entries`へ置き換えた。`validate_r23_executable_coverage`は、criterion prefix、
全vectorの一意所有、polarity/expected_valid、producer/validator一致、test名一致を双方向に検証する。
古いstructural checkerはhistorical synthetic fixture用に残すが、current registry validatorはsurrogate
を受理しない。producer差替え、fixture vector差替え、substantive test差替えをnegativeで確認した。

検証: G09 focused 2 passed（coverage/runtime registry）、Next/schema 573 passed、全repository 1459 passed
1 skipped、ruff check、ruff format 163 files、mypy 139 files、SpecDock validate nodes=10。これはR23/G09の
限定的なローカル契約修復であり、R21実OS/process、G10 canonical R/D/P整理、G11 package計画、全体の
fixed-SHA Strict reviewは未完了。製品adapter/CLI/依存/lockfileは変更していない。

### G09 independent review follow-up (2026-09-08)

固定SHA `354fe76cd94f4a2832955daf86fa40526abad2af` に対する独立GPT-6 Maxレビューは、
metadataの双方向検査自体は通過（P0=0）したが、current registryに旧Round23 surrogateを
認定しているP1を検出した。RG-02/05/06/08のpositive producerは現行
`next-config-v1`、`next-provenance-v1`、`next-run-decision-v1`、
`next-publication-decision-v1`へ適合せず、publication mappingは実際の
`finalize_publication_decision`を呼ばなかった。これはproduction adapterの不具合ではなく、
currentとhistoricalのregistry境界が誤っていた証拠である。

最小修復として旧Round23 36レコードを`historical_runtime_vector_registry`へ移し、
`runtime_vector_registry`を現行v1 reference chainを表すRound22レコードだけに限定した。
Round23のsubstantive testsとcoverage evidenceは歴史的registryを明示的なauthorityとして
実行し、current v1の実装可能性を主張しない。旧round専用modelを第二のcurrent authorityへ
修理・拡張することは行わない。

同レビューのP2指摘（fixture evidenceのvector重複、およびpositive/negative catalogの
誤配置）も、配列の一意性、catalog相互排他、registry polarityとの一致を検証することで修復した。
追加negative回帰は両方のmutationを拒否する。

検証: G09 focused `2 passed`、contracts/schema `573 passed`、全repository `1459 passed, 1 skipped`
（174.70秒）、current registry 16 records、historical Round23 registry 36 records、ruff
check/format、mypy 139 files、SpecDock validate nodes=10、git diff hygieneを修復後に再実行して
通過した。独立レビューで残ったP1/P2はこの修正範囲では解消したが、R21実OS/process、G10
canonical R/D/P、G11 package計画、全体fixed-SHA review、production adapter実装は未完了である。

### G09 authority and catalog API closure (2026-09-08)

レビューの追加反例を受け、registry実行APIのauthorityを自由なiterable注入から
`current` / `historical_r23` の二択へ閉じた。validatorとexecutorは同じ一度だけ解決した
authority snapshotを使うため、iterableの二重消費や、current IDを旧R23 producerへ協調差替えする
経路を受け付けない。current registryの16件とhistorical registryの36件は、既定経路と明示経路を
分離したまま defensive copyを返す。

current/historical共通のfixture catalog検査は、引数が`None`かどうかで有効化を判定し、空配列も
検査対象とする。各authorityのpositive/negative ID集合、catalog内重複、相互交差、registry polarity
を完全照合するため、Round22にもpolarity誤配置のnegative回帰を追加した。Round23 evidenceにも
空catalog拒否回帰を追加した。

修復後の確認は focused G09 `2 passed`、全repository `1459 passed, 1 skipped`（198.71秒）、
ruff check/format、mypy 139 files、SpecDock validate nodes=10、diff hygiene pass。これは
次の固定SHAレビューへ渡すreference-contract候補であり、外部Strict pass、production adapter、
実OS/process、G10/G11、Issue完了を意味しない。

### G09 single-snapshot closure (2026-09-08)

固定SHA `98c3719` の再レビューで、authority selector自体は閉じているものの、validatorと
executorがresolverを各1回呼ぶため「同一snapshotを一度だけ」の要件が未達と判定された。
private `_validate_runtime_vector_registry_snapshot` を分離し、executorが一度だけ取得した
current/historical snapshotを検証・producer実行・最終集合比較へ共有する構造へ修正した。
Round22 focused regressionはresolver呼出し回数が1であることを固定する。

修復後の証拠は focused G09 `2 passed`、全repository `1459 passed, 1 skipped`（193.30秒）、
ruff check/format、mypy 139 files、SpecDock validate nodes=10、diff hygiene pass。修復候補は
次の固定SHAで独立レビューを再実施する。P0/P1の未解決、production adapter、実OS/process、
G10/G11、Issue完了は主張しない。

### G09 final independent review (2026-09-08)

固定SHA `18084874777ac7c62640c9e53697cba847a53294` に対する独立GPT-6 Maxレビューは
`P0=0 / P1=0 / P2=0`、Standards/Spec指摘なしで閉じた。HEADとconfigured upstreamは一致し、
開始・終了ともcleanだった。current 16件とhistorical 36件の双方でauthority resolverとprivate
snapshot validatorは各1回、同一snapshotをproducer実行と最終集合比較まで共有する。
不正authority、旧iterable、surrogate協調差替え、catalog重複/交差/空/欠落/polarity誤配置は
78拒否、producer呼出し0、historical全producer遮断下でもcurrentは通過した。reviewer回帰は
19 passed。

これはG09 executable coverage authority境界の限定閉鎖である。R21実OS/process、production
Next adapter、G10 canonical R/D/P、G11 package計画、全体fixed-SHA Strict、Issue完了は
未認定のまま保持する。

### G10 canonical R/D/P consolidation (2026-09-08)

現行の要件・設計・計画を履歴追記の集合から選択できるよう、3文書のcurrent-v1直後に
canonical indexを追加した。Round 8〜24の過去の判定・件数と過去Artifactは保持し、現行参照行だけを
current-v1の経路に合わせて更新した。新しい選択規則は、(1) current-v1 authority、(2) stable ID、
(3) schema、(4) reference validator/testの順に解決し、履歴節・旧API・旧registryを
実装入力やfallbackに使わないことを明記する。

RequirementはI05-REQ-001〜007をschema/validator/testと対応させ、current
`runtime_vector_registry` 16件とhistorical `historical_runtime_vector_registry` 36件を
分離した。Designはpackage/source、semantic graph、process/compatibility、decision、
publication/stdout、runtime resourceのowner mapを追加した。Planは
I05-PLAN-000→001→008→002〜007の停止条件を明示し、現在のdata-only契約と将来の
production adapterを混同しないようにした。

### G11 package/build/license acceptance boundary (2026-09-08)

`code-structure-viz.next-reference-runtime-inventory/v1`（チェックイン4 fixture）と
`code-structure-viz.next-runtime-build-inventory/v1`（将来の出荷archive）を別identityとして
Planへ反映した。後者について、locked recipe、source→package mapping、wheel/sdistの実member
列挙、bytes/size/SHA-256、license notice、自己参照metadata除外、symlink/traversal/重複防止、
再build一致、checkout外offline install、missing/extra/hash/role/license mutationを受入れ
順序として固定した。さらにclean virtualenvへwheelをinstallした後、checkout外でinstalled CLIを
実行し、正常applicable fixtureは必ず`complete`・exit 0でsemantic JSON・PlantUML・run/domain
manifestの存在とdigestをassertし、Node欠落・不正targetなどのunavailableは別の負例として
status/exit 3をassertする手順を追加した。target側の`node_modules`、config、script、networkを読まないこともsecurity trapで確認する。
target側の`node_modules`、config、script、networkを読まないこともsecurity trapで確認する。
future test pathは`tests/packaging/test_next_runtime_inventory.py`と
明記したが、未作成テスト・実package build・`pyproject.toml`・依存・`uv.lock`の変更は
current evidenceへ含めていない。

G11のschema曖昧性を一つ解消するため、`next-runtime-build-inventory-v1` のmemberへ
`source_kind`→`role` の条件（adapter、typescript→typescript_lib、trusted declaration、
license）を追加し、4つの不一致を `test_next_runtime_build_inventory_binds_source_kind_to_role`
で拒否するreference testを追加した。これは将来inventoryのshapeを閉じる契約であり、実archive
の存在・同梱・再現性を証明するものではない。

この追記後の確認対象は、文書の差分check、SpecDock/schema/contract/full quality gate、
clean push、固定SHAに対する独立GPT-6 Max reviewである。G10/G11は契約の読み取りと将来
受入れを具体化したもので、R21実OS/process、production adapter、Issue完了を宣言しない。

### Final fixed-SHA independent review (2026-09-08)

修正コミット `332429ec9b10db937a1a34f1ebac57dda14a4316` を対象に、独立GPT-6 Maxレビューを
clean worktreeで実施した。local HEAD、configured upstream、GitHub remoteはすべて同一SHAで、
レビューの判定は `P0=0 / P1=0 / P2=0`、Standards/Spec指摘なし（pass）だった。前回のP2で
あった「履歴本文を無改変」と実差分の不一致は、過去の判定・件数と過去Artifactを保持しつつ
現行参照行だけを更新した、という記録へ修正して解消した。

同レビューはcurrent 16件／historical 36件のregistry境界、role mapping、G09 snapshot共有、
G11の正常成功必須・unavailable負例分離と未実装境界を再確認した。最終検証は契約テスト
`574 passed`、全repository `1460 passed, 1 skipped`、SpecDock validate、diff hygieneを
含む。これはIssue #8を実装可能な状態にするreference-contract/documentation gateの完了で
あり、production Next adapter、実OS/process、実wheel/sdist、Issueの完了・クローズを意味しない。
