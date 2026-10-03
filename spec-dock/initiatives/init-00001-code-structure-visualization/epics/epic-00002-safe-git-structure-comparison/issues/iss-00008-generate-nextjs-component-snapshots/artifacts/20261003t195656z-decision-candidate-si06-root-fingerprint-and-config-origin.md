---
種別: decision-candidate
ID: "20261003t195656z-decision-candidate"
タイトル: "SI-06 root指紋の未認定表現と親設定の証拠"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-10-03"
親: ["iss-00008"]
template: "decision-candidate"
authority: "draft"
derived_from: []
reflected_to: []
---

# SI-06 root指紋の未認定表現と親設定の証拠

本資料は**未採択の判断候補**です。Requirement/Design/Planの受入仕様の意味、accepted ADR、schemaを変更しません。Plan/Reportには分析の進捗だけを追記します。人間向け図解は[説明HTML](20261003t195656z-si06-root-fingerprint-explanation.html)です。

## 結論と判断してほしいこと

解析結果が未認定の実行でも、その失敗内容をmanifestへ正直に公開します。同じsemantic指紋をrootへ投影する意味を維持するなら、Nextのroot指紋を「認定済みdigest／未認定null」で表す必要があります。失敗用の別hashやゼロ埋めで解消してはいけません。

本件の第一候補は**A：Next枝に限定した現run-manifest-v2のnullable訂正**です。ただし、現v2を不変として提供する外部・永続consumerへの義務がないこと、schema/producer/validator/consumerを同時切替できることが条件です。この条件を確認できない、または既存の不変保証があるなら**B：新root世代**を選びます。Bは安全な互換性手段ですが、実在が未確認のDB/cacheを移行対象と断定して新世代を必須にはしません。

今回の人間判断は、2026-10-03に採択したadapter capture二fieldの訂正とは**別**です。その採択をroot指紋や親設定originの追加設計へ拡張解釈しません。どちらの案でも親設定originの証拠設計を先に具体化し、仕様の独立レビュー後にroot実装を始めます。

## 現在の実装と認定状態

- 対象はIssue #8 / SI-06 reference-only。分析対象のclean/pushed SHAは `fca99a91c11f33de5199e67996be1be671e10298`、元累積Code Review baseは `af6f5d33f9487a33dabf2ddfe41df85b3d8267fb` です。
- このcheckpointで、publication-v2のnullable capture pair、catalog-owned診断、artifact-selectorのfinal owner、stderr 64KiBとselected stdout 16MiBの実参照owner exact/+1を追加しました。
- 元Green16805は2 passed/2887.68s。小規模15 passed/2 deselectedは当時まだ実行中だった同large casesを別jobへ分離した結果で、large casesを省略した全体passではありません。native/cache/foreign/null/zero/公開privacyの追加focused testsもpassです。件数を合算しません。
- summary/manifest/domain/rootのCurrent final ownerは未完了。all-contract/full pytest、SI-06全体のfresh独立Code Review、製品TypeScript/OS/CLI/package、Final Quality Gate、Issue完了は未認定です。
- 現物のroot producerが失敗したテストではありません。未実装rootへ進む前の契約整合確認で差分が見つかりました。artifact-selectorの正規failureを否定するものでもありません。

## 用語と責務

| 値 | 意味と保持元 | 証明しないこと |
| --- | --- | --- |
| source fingerprint | 同じSourceView/sealが読んだ入力集合のidentity | Node実行、compiler使用、解析成功 |
| semantic run fingerprint | 同じrequestとmatching transport/Coreの14-key family | complete成功、実TypeScript import/useの独立attestation |
| generic run-fingerprint/v1 | 既存Python/SQLAlchemyの入力・request・config等の七key identity | Nextのsemantic familyとの同一性 |
| publication seal / measurement digest | 最終公開recordと実bytes/計測の整合性 | semantic admissionや解析成功 |

Nextの実14キーは [next-semantic-v3.md](../../../../../../../../docs/contracts/next-semantic-v3.md) と、run3 producer/独立validatorに一致します。

```text
source_view_fingerprint, source_plan_digest, domain_config_digest,
projects, targets, formats, stdout_selector, limits,
node_version, typescript_version, adapter_version, protocol,
trusted_environment_digest, semantic_admission_profile_id
```

`typescript_version=5.9.2`はlocked expected metadataであり、実compiler使用の証明ではありません。結果partition/count、response body、PID、host path、captureをpreimageへ加えません。

## 確認済みの契約差分

| 正本・現物 | 現在の制約 | Core/transport無しでの結果 |
| --- | --- | --- |
| [next-run-decision-v2.md](../../../../../../../../docs/contracts/next-run-decision-v2.md) のFingerprint節＋v3継承 | matching transport/Core無しではsemantic fingerprint=null。failure用hashを合成しない | nullが正しい |
| [next-domain-manifest-v2.schema.json](../../../../../../../../schemas/next-domain-manifest-v2.schema.json) | domain.run_fingerprintはdigestまたはnull | 表現可能 |
| [next-config-v1.schema.json](../../../../../../../../schemas/next-config-v1.schema.json) のsnapshot_request | run_fingerprintはoptional digest。null値は不可 | 未認定時はfieldを省略する方向。joinを明文化する |
| [run-manifest-v2.schema.json](../../../../../../../../schemas/run-manifest-v2.schema.json) のrun | fingerprintは必須nonnull digest | nullを拒否 |
| [旧root helper](../../../../../../../../tests/contracts/test_next_contracts.py) の_run_manifest | root.run.fingerprintにdomain値をそのままコピー | そのjoinのままでは衝突 |
| [旧独立validator](../../../../../../../../tests/contracts/next_reference_validation.py) のvalidate_run_manifest | root/domain fingerprintの一致を検査 | 未認定nullを別hashで救済する定義ではない |

限定probeは同じ実stage_failed request/runtime/run/candidatesから、旧joinを保持した**run blockだけ**を現schemaへ渡しました。唯一のerrorはfingerprintのNoneがstringではないというものです。probe原script/JSONは既存[中間Artifact](20261003t181426z-disc-si06-publication-progress-root-fingerprint.md)を参照してください。

## 正常・失敗の具体例

| 実branch | capture | semantic fingerprint | payload / exitの意味 |
| --- | --- | --- | --- |
| 起動準備stage_failed | 未観測null/null | null | 解析payload無し。失敗情報は公開可能、exit3 |
| timeout、実0 byte観測 | object/object、実測0 | null | 解析payload無し。nullと0を混同しない、exit3 |
| matching transportからCore rejected | 観測済みobject/object | 非null | semantic familyは識別できるが、解析payloadは不採用、exit3 |
| validated TARGET/EXPORT/entity等unavailable | 観測済みobject/object | 非null | 正しい認定familyでもpayload無し、exit3 |
| complete / partial_safe | 観測済みobject/object | 非null | completeはexit0、partial_safeはexit3 |
| final stderr/capture overflow | actual ownerどおり | 元runの値を保持 | publication自体のfailure。response=null、artifacts空 |

指紋がnullかどうかは「失敗一般」ではなく、matching transport/Coreの有無で決めます。captureとsemanticの**意味**は別ですが、到達可能な組合せは下位ownerの不変条件にも従います。Current success/Coreを未観測captureへ結ぶ正例は作りません。

## もう一つの未完了設計：親設定の選択元

root configは値だけでなく、設定の選択元も必須です。

- `config.source` は `builtin / repository / explicit`。
- Nextの七field `value_sources` は各project/target/format/depth/limits/trusted settingの選択元。ここでは `cli` も使え、limits/trustedには `unobserved` 枝があります。
- actual `RetainedNextAnalysisContextV2` はresolved intent、run_context、domain config、同seal/assetを保持します。しかし全七fieldのCLI/builtin/repository/explicit originを受け取る入力はありません。
- sealの `config_resolution` はTypeScript configのdeclaring paths/membership等です。CLI設定の選択元と同義ではありません。budget_source一つを全limitsのoriginへ流用しません。
- old root helperはPython goldenを読み、sourceと多くのoriginをbuiltinに固定します。これを新actual ownerの観測と呼んではいけません。
- productionのgeneric ResolvedConfigはPython向け六fieldのoriginで、Next七fieldへそのままcastできません。

これは「repository全体にorigin ownerが存在しない」と断定する調査ではありません。**今のCurrent retained chainからrootが必要とする全originを正当に導出できたという証拠が無い**という限定結論です。

採択後のDesignでは、親設定解決時に値とoriginを一緒に保持するbounded reference owner、同request/contextへのjoin、final ownerのinput責務を明記します。下位runtime/Core/run/candidatesのhashや意味は変更せず、必要な追加owner/inputが既存単一authority契約とどう整合するかをSpec Review対象にします。schemaを通すためのfree metadataやunknownのbuiltin置換は不可です。製品CLI resolverが未実装なら、その実観測認定とは区別します。

## 選択肢と推奨理由

| 案 | 変更 | 利点 | コスト・採用条件 |
| --- | --- | --- | --- |
| A：現v2・Next枝限定訂正（第一候補） | rootのsemantic指紋だけdigest/nullへ。正常digestの14-key意味は不変。domain=null / request field省略 / root=nullのjoinを明記 | 新hash/field/URNを増やさず、未認定を正直に表現する。今回のpre-production scopeに小さい | 旧nonnull consumerはnullを拒否する。外部不変保証無し・同時切替可能を確認。既存非Next枝はnonnullのまま |
| B：新root世代（互換性保証が必要なら推奨） | Next nullable表現を新identityへ隔離。最小affected exact-ref closureを設計 | 旧contract bytes/consumerの不変保証を守る。新/旧世代を識別できる | schema/URN/dispatcher/reader/vectorsの版routingが増える。既存保存recordを再解釈しない |
| C：全Next rootをgeneric request fingerprintへ分離 | semantic指紋との同値joinを変更。入力identityとsemanticを別契約へ | Core前の失敗にもnonnull入力identityが必要なら合理的 | exact preimageとconfig-origin owner、reader/cache意味の新判断。今回の最小修正としては非推奨 |
| D：Core無しのmanifest抑止、失敗専用hash、ゼロdigest | schema conflictを避ける／別値を入れる | 表面上は小さい | 通常failure公開やsemantic null契約を壊すため不採用 |

本件ではCurrent root ownerがまだ未実装で、new rootは認定前の参照契約です。ローカルのidentity文字列censusはschema、tests、Issue artifactsにhitし、src/docsのproduction v2 writerは見つかりませんでした。ただし動的loader、過去配布物、repository外利用者を完全に調べた証明ではありません。sdistはschemas/docsを含む構成なので、外部consumerが無いとも断言できません。

したがって、外部回答の「新versionが必須」という一般論をそのまま実装せず、**不変提供義務の有無**を判断条件にします。Aでも破壊的影響がゼロになるわけではなく、旧object/non-null validatorの同時切替は必要です。外部義務があるならAを選びません。

## 外部分析の実行証拠と採否

fresh ChatGPT Use Strict、native `issue8-si06-root-contract-analysis`、original exec87072はterminal0、2026-10-03T19:49:37Zに完了しました。GPT-5.6 Sol / Proの両UI picker verified=true、backend未attestedです。回答は同branch/full SHAのGitHub connector確認を宣言し、tree SHAもローカル一致。wrapperはmachine-readable connector attestationを返しません。

原回答は778行を全読し、rawを一文字も訂正せず保存しました。

- [原回答gzip](20261003t195655z--si06-root-fingerprint-result.md.gz)、SHA256（展開後）：`ca13e015ee38356479af4ca606d18aa8fb0bb8ae1ae487deba63f44de6b0eccf`。
- [原log gzip](20261003t195655z-01--si06-root-fingerprint-oracle.log.gz)、SHA256（展開後）：`c3621ebe7995587101eaec679ce0dd0fa9a66695c66989627a8ca82be44193b3`。
- [lineage](20261003t195655z-02--si06-root-fingerprint-lineage.json)。transcript answerはraw一致。prompt差分はOracleが末尾へ加えた22-file ZIP展開案内だけで、exact文字列まで照合しました。最初の「options promptと完全同一」検査はこの案内を考慮しない準備ミスで、セッション障害ではありません。

| 外部の内容 | ローカル採否 |
| --- | --- |
| semantic null対root nonnullの差分、generic hash自動fallback禁止、origin捏造禁止 | exact source/schema/actual ownerへ照合して採用する事実 |
| 十四key列挙のartifact_id/run_id/runtime_identity/compiler_identity等 | 正本と不一致。不採用。上記の実14-keyだけを使う |
| Coreあり＋未観測captureを正例にするnegative-vector案 | Current runtime success→response→complete observed captureと両立しない。不採用 |
| root config.sourceにcliを含むという表現 | schema上はbuiltin/repository/explicit。value_sourcesのcliと区別して訂正 |
| old helperはcompleteだけを扱うという断定 | functionは無条件copyで、旧test全体のfailure不在を証明していない。Current v3 owner認定無しという限定事実だけ採用 |
| 新version最推奨、外部DB/index/cacheへの影響 | 互換性リスクとして検討。実在するconsumerや義務とは断定しない |
| old writerへ戻せばrollbackできる | Core無しnullは旧rootでも表現できない。Next新writer停止と旧record保存を基本にし、旧形式へのfake変換は禁止 |
| 指紋の非null＝compiler/OS/解析成功 | そのように認定しない。Current locked metadata/reference ownerの証拠範囲を維持 |

この回答はCode/Spec Reviewではありません。formal findings/severity/review_statusは発行せず、実行可能brief、採択ADR、品質gate passへ昇格しません。追加の同じconsultは行っていません。

## 採択後に実施する具体的順序

1. 人間がA/Bを選択し、現v2不変義務があるかを確認します。無回答をA採択にしません。
2. accepted ADRとCurrent Requirement/Design/Plan/public contractを先に訂正します。root fieldの意味、null/nonnull predicate、request fieldのomit、非Next枝不変、config-origin owner/input責務、migration/rollback/停止条件を閉じます。
3. 現物schemaを変更する前に、docsのkey集合・ref closure・ローカルlinks・SpecDockを検証し、clean/pushed exact SHAへ独立Spec Review Strictを実施します。valid passまでroot codeを開始しません。
4. 具体化した仕様からbounded briefを抽出し、schema→same-owner producer→独立validator→cross-document literalをvertical TDDします。元SI-06累積baseを動かしません。
5. null＋任意/generic/ゼロhash、Coreあり＋null、Core rejection＋null、domain/request/root不一致、same-content foreign owner、origin捏造、resealed cache/native数値、privacy、旧非Next bytesの負例を検証します。
6. whole SI-06 closure後、全selectorとconfigured64KiB/16MiB exact/+1を含むall-contract/full pytest、statics/docs、fresh Code Review Strictを同じclean SHAで実行します。部分pass/分析/旧SI-05を代用しません。
7. rollbackは新Next公開を止め、旧recordとPython/SQLAlchemyを保全します。nullを旧形式のdummy digestへ変換せず、既存保存物の移行/backfillを発明しません。

## 後続AIへの禁止事項と再開点

- このdraft、外部原回答、HTMLだけからroot nullable、新root version、origin owner/input変更を実装しないでください。
- 原14-key誤列挙を転載しないでください。実source/正本を使ってください。
- Root manifestのsource/configをgoldenや旧巨大referenceからactual ownerへcastしないでください。
- 共有run defsを無条件にnullableへ緩めてPython/SQLAlchemyを変えないでください。
- サブエージェントレビュー/実装、UI progress monitoring、live job重複、強制Git操作は行いません。現在の外部jobはterminalで、再待機不要です。
- 人間採択後は正本→Spec Review→TDDの順。SI-06/全A02/A03/製品/Final/Issueは未完了です。
