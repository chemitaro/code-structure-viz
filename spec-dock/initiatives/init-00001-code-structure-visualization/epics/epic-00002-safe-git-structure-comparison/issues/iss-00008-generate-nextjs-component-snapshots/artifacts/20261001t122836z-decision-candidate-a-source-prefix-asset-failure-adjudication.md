---
種別: decision-candidate
ID: "20261001t122836z-decision-candidate"
タイトル: "a-source-prefix-asset-failure-adjudication"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-10-01"
親: ["iss-00008"]
template: "decision-candidate"
authority: "draft"
derived_from: ["20261001t122734z--issue8-a-source-prefix-analysis.md", "20261001t024645z-adr-issue8-trusted-toolchain-launch-model.md"]
reflected_to: ["requirement.md", "design.md", "plan.md", "report.md"]
---

# 20261001t122836z-decision-candidate a-source-prefix-asset-failure-adjudication

このArtifactは、固定SHAの外部助言をローカル正本へ照合した結果と、未採択の資材failure policyを分けて保存します。`authority: draft`です。Reflection先へ反映するのは確認済み事実と採択済みAの機械的clarificationだけで、新code/outcomeを採用したという意味ではありません。

## Context

### 現在地

- Issue #8は未完了。A02のreference data契約を整備中です。実TypeScript analyzer、新runtimeの製品Node/CLI接続、両OS製品受入れ、A03独立Strict、Final Quality Gateは未完了です。
- 分析対象: repository `chemitaro/code-structure-viz`、branch `iss-00008-generate-nextjs-component-snapshots`、exact SHA `e15033d6f9d6cdd9c47bda21d568c71c62b689e0`。分析開始前にclean worktree、local/upstream/live GitHub tipのfull SHA一致を確認し、実行中は対象branchを変更していません。
- ChatGPT回答も開始時・回答直前の同SHA照合とtree SHA `8aca537f4cfda6cb8e27678de27def6075896d04`を報告しています。コネクタ操作自体は回答者の報告であり、主担当がその内部実行を再現したという主張ではありません。
- session `issue8-a-source-prefix`、conversation `6abe4c65-c328-83e9-b536-f0f094414b29`、original exec session `66979`。2026-10-01T12:04:39.787Z開始、12:18:32.334Z completed、元実行exit 0。quiet jobを再送せず、元session/logだけで待機しました。Browser/Computer Useによる監視、API fallback、サブエージェントなし。
- model picker: requested/resolved `GPT-5.6 Sol`、select/already-selected、verified=true、capturedAt `2026-10-01T12:04:45.011Z`。thinking picker: requested `pro`/resolved `Pro`、already-selected、verified=true、strictFailClosed=true、capturedAt `12:04:45.185Z`。これはWeb UI選択観測で、backend identityの証明ではありません。
- `promptSubmitted=true`、submittedPromptHash `109f10f29664e76553d8d61b1e32e12dd5ad3ecebac300c94f228ff8d8efc8f2`。23添付、native input estimate 236,277 tokens。保存回答全843行を読み、助言の採否を下記で分離しました。

### 証跡と保存時の正規化

- 原回答の保存先: `20261001t122734z--issue8-a-source-prefix-analysis.md`。`artifact import file`でexplicit regular fileをopaque evidenceとして取り込み、`canonical=false`を確認しました。CLIの`committed/publication_state=committed`はArtifact保存のcommit pointであり、Git commit済みの意味ではありません。
- 元回答: Workbench `reports/issue8-a-source-prefix-analysis.md`、SHA-256 `11a8d5aff2ccef34310b0433607a684d82486fd00d800b89588ca78d2c0c5139`。元回答とOracleログは変更していません。
- tracked copyだけ、元回答64/77/178/515行の行末空白を削除しました。本文、順序、提案、判断は変更していません。保存copy SHA-256 `fbc511aff3a7ea25844fc9a6a1317da82bf086537b6fbf6e7c923a4fbc6fc86e`。元回答と保存copyのhash差はこの正規化によるものです。
- native transcript SHA-256 `0b3700e27d37d4391cb20aac12bfb012e3972afcebc69505d63bc794f79d9613`、native output.log SHA-256 `b4d5832d59b6ef7ab9c86a9c1bfa1e5b01cb3d73ee79f8deaf040589beec86a7`。native filesはローカルOracle sessionの証跡で、製品packageや公開run Artifactへ同梱するものではありません。
- 今回は設計advisoryです。test再実行、実Node/TS認定、A03 Code Reviewの`review_status=pass`を返したものではありません。

### ローカル照合した事実

| 論点 | 確認した現物 | 判定 |
| --- | --- | --- |
| 期待metadataの取得順 | Current Design A: package permission後にModuleが資材を保持し、readonly trusted descriptorをsource sealへ渡す | seal前にexpected metadataが実在する。source失敗時に一律消す旧文言をv2について補正する |
| expectedとactual | `next-trusted-type-environment-v2.md`、`next-provenance-v2.md`: expected descriptorと実child利用を分離 | `trusted_environment` slotは改名せず、expected metadataの意味を維持。actual Node/TS使用は補完しない |
| early prefix schema | `next-provenance-v2.schema.json`: request-independent failureでresource slotsを一律unobservedにはしていない | 17-slotを増やさず、同じownerからの観測値だけ保持する。producer/checkerの実装は残る |
| 完了seal | production `SourceAcquisitionSeal.__post_init__`は`source_view.failures`を拒否 | current productionはcomplete-only。read prefixはsafe-subset certificateではない |
| source budget | catalog v1のLIMIT-002 fixed messageはfile count **or decoded source total**。Current Designのmappingも同じ | decoded total → LIMIT-002は新policyではなく既存仕様への整合 |
| 実装・schemaとの差 | production readerはfile/total両方をTOO_LARGE、acquirerはLIMIT-001/source_read。provenance v2はLIMIT-002/source_selectionだけ | file/totalの実measurementと分類を分離し、v2 stage matrixを修正する必要がある。未修正 |
| 資材failure | catalog v1にASSET codeなし。TRUST-001はtrusted digest mismatch、NODE-002はspawn failure | 資材I/O・欠落・header不正を既存TRUST/NODE/SOURCEへ丸めるのは意味不一致 |

`SourceReadFailure(path, kind)`だけから「実際に上限+1 bytesを読んだ」「totalを測定した」とは言えません。旧exceptionに存在しないactual count、attempted increment、resolved config、membershipをstageやfailure名から合成しません。

### 採択済みAから導出できるclarification

1. 適用permission後に完全なasset ownerが成立したsource failureでは、`runtime_bundle`とreadonly expected `trusted_environment`を同じownerの値で残す。
2. 非適用、package failure、資材保持が完了していないbranchでは、それらをobservedにしない。
3. source failureでは、未作成request/Node candidate/policy/process/version/control/semantic/compatibility/model/budgetを補完しない。実測済みsource prefixは削除しない。
4. 同じanchored sessionから読んだtarget package bytesを利用し、別sessionのcacheや自由入力bytesで差し替えない。最終drift checkに最初のpackage signatureを含める。
5. phase-local read traceと上位のconfig/membership/selection/seal milestoneを区別する。callerがphase/stage/count/journalを作ることは許さない。
6. complete-only sealからpartial-safeを生成しない。partial-safeには別途検証済みgraph/ledger/safe-subset/taint certificateが必要。
7. 旧v1 schema/fixture/hashとPython/SQLAlchemyの挙動は変更しない。

これらはCurrent R/D/Pへclarificationとして反映します。ただしreader prefixの実装・受入れ完了を宣言しません。

## Options

### 人間判断が必要な資材failure境界

target repositoryの`package.json`と、本製品が同梱するadapter/TypeScript/trusted declarationsは別の資材です。今回の未決事項は**本製品の同梱資材**に限ります。

| 案 | 通常のresource I/O不能 | locked member欠落・header/profile/role/hash不正 | 利点 | 代償 |
| --- | --- | --- | --- | --- |
| A: 二分する（推奨） | Next `payload_unavailable`、exit 3、安全なfailure manifest可 | run-level fatal、exit 1、manifest/semantic Artifactなし | 環境上の取得不能と壊れた製品packageを区別し、製品の自己契約違反を隠さない | 将来multi-domainでも製品破損はrun全体を止める |
| B: すべてNext unavailable | exit 3、failure manifest可 | 同左 | 将来の他domainを停止させにくい | broken installed packageが通常のdomain可用性失敗に見える |
| C: すべてfatal | exit 1、manifestなし | 同左 | 最も保守的で単純 | 一時的・通常のI/O不能でもrun全体停止し、回復性情報を失う |

既存source-integrity fatalとの整合、本製品packageを信頼するAの前提、原因に応じた復旧案を示せる点からAを推奨します。現Issueはsingle-domainですが、fatalはrun-level契約なので、将来のmulti-domainにも影響する重要判断です。

### 推奨Aの具体案（未採択）

| code | stage / 私的reason | 公開結果 | 復旧の方向 |
| --- | --- | --- | --- |
| `CSV-NEXT-ASSET-001` | `execution_assets` / closed resource acquisition failure | severity error、recoverable=false、ref/pathなし、Next unavailable、exit 3、failure manifest可 | インストール先のアクセス権・ストレージ・通常I/Oを確認して再実行 |
| `CSV-NEXT-ASSET-002` | `execution_assets` / proven installed package contract violation | severity error、recoverable=false、ref/pathなし、fatal、exit 1、ordinary Next provenanceとmanifestなし | 正常なpackageへの再インストール・build/package修正。自動取得はしない |
| `CSV-INTERNAL-001` | core terminal / closed reasonへ分類できない実装・owner invariant error | 既存internal fatal | 実装bugとして調査。ASSET-001へcatch-all変換しない |

固定message候補:

```text
CSV-NEXT-ASSET-001
The bundled Next.js execution assets could not be acquired.

CSV-NEXT-ASSET-002
The bundled Next.js execution assets violate the installed package contract.
```

- `ASSET-001`: 通常resource I/Oで必要bytesを取得できず、installed contract violationを立証できない場合。raw OS error、private install path、部分的なasset bytesは公開しない。
- `ASSET-002`: locked必須member欠落、symlink/non-regular、inventory shape/order/duplicate不正、adapter header/version不正、role集合不正、trusted profileのsize/hash不一致、資材間locked identity不一致を**実evidenceで立証**した場合。
- arbitrary `OSError`、permission error、検証helperの任意`ValueError`だけから欠落・破損を推測しない。closed evidenceで分類できない内部bugは既存internal terminalを維持する。
- 完全asset ownerをmintできなかった`ASSET-001`では、applicabilityだけを含む実prefixとし、`runtime_bundle`/`trusted_environment`はunobserved。半端なdescriptorで観測行を埋めない。
- `ASSET-002`はterminal selector契約に渡す。普通のfailure provenanceへfatalを混ぜない。どのselectorもsemantic decoder/finalizer/Artifact readを呼ばない。

### 外部助言からの補正・留保

1. **catalogを同じv1 identityのまま拡張しない。** 新code採択後はA chain用`next-diagnostic-catalog/v2`を追加し、旧v1 entries/message/bytesと旧consumerを維持する方針を推奨。generic diagnostic wire versionを無条件に変更せず、exact code/refの依存closureを検証する。原助言の「catalog同期」を旧v1上書きと解釈しない。
2. **A02でproduction façade/journalを改造しない。** 外部案の`seal_source_acquisition`内部engine refactorはproduction変更を伴う。Current PlanはA03の後にA04 production実装を許可する。A02ではreference-only producer/validator/evidence modelを閉じ、actual reader milestoneの接続・実measurementはA04で検証する。reference journalを現productionの実journalと呼ばない。
3. **cached replayはA02の小さい候補であり、製品の最終APIを過剰固定しない。** A04では、一つのtransaction ownerがpreflight→資材保持→source sealを継続する方式も比較する。いずれもsame session、one physical read、actual milestones、final drift、single success algorithmを維持する。
4. **decoded-total mappingは助言どおりローカル仕様で裏付けられた。** LIMIT-002/source_readが既存意味に合う。ただし現productionのactual measurementsとschema matrixは未整合。legacy v1 fixtureを書き換えて見かけ上揃えない。

## Candidate

判断依頼は一つのpolicy packageです:

> 通常の資材I/O不能は`ASSET-001`/Next unavailable/exit 3、同梱資材の立証済み欠落・破損は`ASSET-002`/run-level fatal/exit 1に分け、旧catalog v1を維持してA用catalog v2へ定義する推奨Aを採択するか。

未回答を採択済みとしてschema/code/outcomeへ反映しません。`trusted_environment`改名や17-slot増設は提案せず、採択済みAに沿うclarificationだけを先に記録します。

## Reflection

### 採択後の小さい実装順

1. 明示回答をaccepted ADRまたはCurrent R/D/Pへ固定。code/message/stage/outcome/ref/exit/manifestのclosed matrixを同期する。
2. source-phase seamを一つずつTDD: applicable後だけ資材保持、expected metadata prefix、same-session one-read、config/extends/selected membership実evidence、file/total/count exact/+1、no partial-safe without certificate、drift/interrupt terminal。
3. 小さい独立reference owner/validatorへclosed constructors、private immutable bytes、fresh projections、same-owner joins、no free stage/countを実装。privacyと同digest別ownerのnegative vectorsを追加する。
4. `next-provenance-v2`へ採択したasset branchとLIMIT-002/source_readを追加。ordinary unavailableとfatal/internalの経路を分離し、旧v1不変性を検証する。
5. run/publication/domain/semantic/root/generic/stdout v2 exact refs、全4selectors、actual known measurement/public bytesを閉じる。
6. related/full local品質gate、clean/ordinary commit/push/full SHA一致の後に、指定固定点`f4159066f3954454ad2f0c2701fa54bf1bc7bc4a`からのA03累積ChatGPT Code Review Strictを主担当が直接実施。新advisoryはcertificateの代替にしない。
7. A03 pass後にA04 actual resources/reader journal/Node/TS/CLIへ接続し、A05両OS/offline wheel/sdist/license/Finalへ進む。

### 今回の検証範囲

外部回答全読とローカル正本/source/schemaのread-only照合、Artifact保存、mechanical documentation clarificationだけです。新source-prefix testのRED/GREEN、実OS/TS、A02全suite、A03は実施していません。直前e15033dのCore/provenance88・関連583・schema/doc-pointer120（重複あり）と静的gateの既存結果を、この未実装prefixや新policyのpassとして使いません。

このdocument-only checkpointのfresh検証: JSON Schema 119 passed（4.20s）、Current authority/history doc-pointer 1 passed（0.13s）、SpecDock sync（no-GitHub/no-active-update）/validate（10 nodes）pass、diff whitespace check pass。tracked回答と元回答の差分は明記した4行の行末空白だけと確認しました。source/schema/dependency/package/legacy fixtureの変更はなく、コード全suiteや実OS/TSを再実行したという主張ではありません。
