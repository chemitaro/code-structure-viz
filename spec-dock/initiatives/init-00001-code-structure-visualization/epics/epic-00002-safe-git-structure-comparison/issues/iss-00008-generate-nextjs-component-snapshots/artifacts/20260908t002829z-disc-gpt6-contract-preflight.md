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
2. G07: string-named exportのprivate syntax observation→coverage/diagnostic→実public contract接続。
3. G09: finding→criterion→vector→producer→validator→testの意味の一致。旧R23 surrogateとfixture-only censusの位置づけ。
4. G10: canonical Requirement/Design/Planからround追記の競合を除き、現行規則と履歴証拠を分離。
5. G11: inventoryを参照fixtureと将来buildへ分けたschema/docsをcanonical実装計画に反映。実package検証は将来実装gate。
6. 全検証、checkpoint commit/push、修復後のclean/pushed固定SHAに対する独立レビュー。

承認済み作業範囲は資料と実装前の契約・参照テストです。src、依存、lockfile、製品adapterは変更していません。
