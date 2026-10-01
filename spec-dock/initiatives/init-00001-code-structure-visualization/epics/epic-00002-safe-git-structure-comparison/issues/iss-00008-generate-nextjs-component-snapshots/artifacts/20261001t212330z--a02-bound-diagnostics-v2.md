# 決定package — A02-3 request-bound公開診断／64 KiB境界

## 1. 結論

**指定SHAのGitHub検証は成功しました。ただし、今回指定された全範囲を、そのままready-to-implement briefにはできません。**

blockerは64 KiBのbyte判定ではありません。依頼範囲に含まれる**「検証済み`parse_file`／`read_file` rootから、正規Core/run2を経由して公開診断を生成する正例」**が、現行CoreのFile correspondenceと維持するtaint/proof規則を同時に満たせないことです。診断層でSOURCEコードを付与するだけでは解消できず、下位のrequest-bound source/proof契約を先に整理するか、このcheckpointから当該正例を明示的に分離する判断が必要です。

添付`brief.md`の停止条件に従い、以下は**実行可能ブリーフではなく、確認した矛盾、必要な判断、変更不要な境界、独立計算済みの64 KiB test構成をまとめた決定package**です。

### GitHub検証

GitHubコネクタの利用可能操作を確認し、指定repositoryの指定branch endpointを直接取得しました。branch名とfull tip SHAは完全一致しています。他branchへのfallbackは行っていません。

| 項目 | 確認値 |
|---|---|
| Repository | `chemitaro/code-structure-viz` |
| Branch | `iss-00008-generate-nextjs-component-snapshots` |
| Expected SHA | `987d0ebc7244c0ea0d2b0400f013cc220e7cccb3` |
| Observed tip SHA | `987d0ebc7244c0ea0d2b0400f013cc220e7cccb3` |
| Parent SHA | `5cba0ec791ea4b9e48f036fd3043807ef7ef2a53` |

今回のcheckpoint baseは`987d0eb…`です。A02全体baseの`710eb49a2a3143e31b8a91580700d16839d9070d`と累積A03固定点の`f4159066f3954454ad2f0c2701fa54bf1bc7bc4a`は変更しません。

著者指定は`GPT-5.6 Sol / Pro`、実装者指定はcaller-reported `gpt-6.1-sol`／`max`です。指定プロフィールの記録であり、backend identityの確認ではありません。本件はBlue authorの継続する分析で、独立レビューではありません。

---

## 2. blocker：Fileの保持場所とfile-rootのtaint規則が衝突しています

### 2.1 直接確認した規則

| 規則 | 現行実装・文書 |
|---|---|
| requestの全Fileはmodelへ一致させる | `next_runtime_v2_validation.py::validate_semantic_candidate_v2`は、request filesから`content_base64`だけを除いた配列を`payload["model"]["files"]`と比較します。不一致は`file_correspondence`です。 |
| proof-only Fileを追加できない | 同関数は、`proof.discovered_records`の`projects`／`files`に`record`がある場合、`proof_source_owner`で拒否します。 |
| file-rootは同一pathのFile自身もseedにする | 旧referenceの`_derive_required_root_seed_ids`は`parse_file`／`read_file`について、同じowner path上の全recordをseedにします。`_record_project_path`はFile自身のpathも返します。 |
| tainted recordはpublished modelへ残せない | `validate_proof`はpublished recordのtaintsが空であることと、taint closureとpublished集合が交わらないことを要求します。 |

最初の二規則は現行v2 Coreの実コードで確認しました。

file-rootのseed規則とFileのpath解決も確認しました。

published／taintedの非交差は`validate_proof`の明示的な検証です。

文書側の`docs/contracts/next-semantic-admission-v2.md`も、全frozen project/fileをmodel correspondenceへ含め、proof-only sourceで別の観測sourceを追加しない契約を記述しています。単なる新diagnostic producerの不足ではありません。

### 2.2 なぜ診断層だけでは解消できないか

同じrequestに含まれるFileを`F`、そのpathを`p`とします。

```text
request File F
  → Core correspondenceによりFはmodel.filesに存在する
  → pに対するparse_file/read_file rootの必須seedにFが入る
  → Fはtaint closureに入る
  → validate_proofはFがpublished modelにも存在するため拒否する
```

Fをmodelから取り除けば、先行する`file_correspondence`で拒否されます。Fをproof-onlyへ移す経路も現在の`proof_source_owner`規則に反します。rootのseedからFを抜く方法は、独立再導出する必須seed集合との不一致になります。

target例外経路も迂回路ではありません。`_validate_target_exception_proof_base`は、discovered／publishedの対応とtaint非交差を検証しています。target failureを添えてfile-rootの不整合を隠すことはできません。

これは**確認したコードからの静的な帰結**です。repository testを実行した観測結果ではありません。

### 2.3 run2での再分類も解決になりません

現行run2はmatching Core ownerを再検証します。Core invariant rejectionは`RejectedSemanticDecisionV2`として扱われ、その通常公開原因はprotocol rejectionです。これを診断層で`CSV-NEXT-SOURCE-001`へ読み替えると、保持ownerの原因と公開診断が分離します。

また、旧`_decision_semantic_diagnostics`にparse/read rootをSOURCE-001へ投影する処理が存在することは、**現行v2 Coreからその入力を生成できる証拠ではありません**。旧ownerへの変換、任意のmodel diagnostic追加、直接constructor、cache改変で正例を作る方法は採用できません。

---

## 3. 必要な判断と推奨

**推奨は、request-bound File/source evidenceとtaint dispositionの整合を、診断byte境界とは別の先行unitとして確定することです。** 新ASSET policyやrequest-independent reader実装を、この問題へ混ぜる必要はありません。

| 選択肢 | 内容 | 影響 |
|---|---|---|
| **先行unitで契約を整理する：推奨** | 失敗したFileのsource evidenceをどこに保持し、safe model／proof dispositionとどう照合するかをCurrentで確定します。その後、正規Core/run2によるfile-root正例を作ります。 | 今回指定された最終的な診断範囲を維持できます。ただし、診断層だけの変更では済みません。 |
| 今回のcheckpointからfile-root正例を明示的に分離する | 現在成立するsemantic診断、target/export、entity/model-record、child/transport、および固定64 KiB境界だけへscopeを変更します。 | 小さい診断checkpointは進められますが、元の指定範囲を満たしたことにはできません。file-rootはA02の残課題です。 |

先行unitで決める中心は、次の所有権です。

> **取得済みFileのsource inventoryと、safe semantic modelへ残せるFileの集合を同一とするのか。別にする場合、request／Project.file_ids／model.files／proof-only records／countsをどの集合へ結合するのか。**

例えば、失敗Fileをproof-onlyへ移してrequestとのcorrespondenceをunionで検証する案は考えられます。しかし、**`model.files`の比較を一箇所緩めるだけでは不十分**です。Project correspondenceもrequestとmodelのproject record全体を比較し、`validate_model`はProjectの`file_ids`をmodel側File集合へ一致させています。public semanticのFile集合やcountsにも影響するため、この回答で採択済み扱いにはしません。

次の回避策は不採用です。

- file-rootを無視して任意のSOURCE-001だけを生成する方法です。
- tainted Fileをpublishedへ残す例外を、診断実装に紛れ込ませる方法です。
- 新v2 ownerを旧`NextRunDecision`へ変換する方法です。
- 正規factoryを通らないfixtureを、file-root admissionの正例として数える方法です。

**この判断が未確定のため、診断ownerの完成版schema／factory／TDD／commit手順を「そのまま実行可能」として提示する段階ではありません。**

---

## 4. 判断を変えずに維持できる公開診断契約

file-rootのblockerと、既に確認できる公開診断規則は分離できます。

### 診断の導出

| 原因 | 維持する導出元・優先関係 |
|---|---|
| validated target failure | matching Core gateのtarget failure行と検証済みtarget proofです。pathは実`target_key`から、reasonはその行から取得します。 |
| validated export failure | 失敗したsyntax identityと、検証済みexport observation／reexport witnessの`owner_module_id`を結合します。historical fixtureのsymbol fallbackは新経路へ移しません。 |
| entity/model-record limit、typed Core rejection、child/transport failure | matching Core／runtimeとrun2 provenanceの閉じたstage/codeです。未知内部errorをこの分岐へ丸めません。 |
| available semantic diagnostics | 検証済みmodel診断と、その実record/reference ownerです。fixed属性はcatalogと再照合します。 |
| parse/read root由来SOURCE-001 | 投影規則はbaselineにありますが、現行v2の正規admissionが前節のblockerです。 |

旧公開producerは、target failure、export failure、no-ref gate failureを優先し、それ以外でsemantic診断を投影しています。新経路で、unavailable時にavailable側の診断集合を無条件に連結してはいけません。

公開rowの固定属性はcatalogが所有します。`domain="next"`、`line=null`、固定message、severity、recoverable、outcome、ref_permissionを維持します。model側の`count`は公開rowへ出さず、target以外へreasonを追加しません。整数をbool／floatへcoerceして一致扱いにすることも避ける必要があります。

### 固定64 KiB境界

`render_public_diagnostic_stderr`の維持意味は明確です。

| 判定前JSONLの実byte数 | 出力可能stderr bytes | manifest用診断 |
|---:|---|---|
| 0〜65,536 | 全JSONLです。空集合なら`b""`です。 | 元の安全診断集合です。 |
| 65,537以上 | `b""`です。partialは0です。 | catalog-owned `CSV-NEXT-LIMIT-003`一件だけです。 |

overflow replacementはstderrへ出す代替行ではありません。baselineのこの経路では`scope="publication"`も追加せず、domain側の固定LIMIT-003をmanifest用へ残します。selected-copy failureのpublication-scope診断とは区別します。

元run2のsemantic outcome、Core measurement、fingerprint、provenance、既存candidate descriptorsをoverflowによって作り直す必要はありません。adapter stderr captureのcounter、child停止、実OS write、最終publication exit／sealも、このbyte境界から推測しません。

---

## 5. 実65,536／65,537 bytesへ到達するtest構成

**64 KiB境界については、任意diagnostic listや小capをfactoryへ渡さずに検証する構成を具体化できました。** 以下の長さとhashは独立計算済みです。ただし、repositoryの正規Core/run2経路を実行した結果ではありません。

### 5.1 正規入力の構成

既存`tests/contracts/test_next_semantic_candidate_v2.py::core_inputs`のCard corpusを利用し、request生成前に16個のmissing targetを与える構成です。

各`i=00…15`のtarget pathを次の規則で作ります。

```text
p_i =
  "src/missing/" + 二桁i + "/"
  + ("a"を200文字 + "/")を18回
  + "b"を120文字
  + ".tsx"
```

各pathはASCIIの**3,757 bytes**です。segmentは最大200文字で、4096-byte path上限内に収まります。targetは`"path:" + p_i`です。

これは公開diagnosticへのpaddingではなく、**実際にrequestへ渡す有効なtarget path**です。sealed sourceにこれらのpathを追加しません。source-root内に存在しないことから、現行`target_completeness_failure`が`missing`を導出する構成です。

正規testの経路は次です。

```text
実source seal
  → 16 targetsを持つ実request
  → 同じmodelと、16件のfailed/missing target proof
  → retained response／実bytesに一致するreference observation
  → retain_runtime_result_v2
  → そのruntimeの同一candidateからCore decision
  → retain_request_bound_run_decision_v2
  → 将来のrun-only public diagnostic factory
```

proof行とcoverage行は、それぞれ実targetに対する`status="failed"`、`record_ids=[]`、`reason="missing"`で一致させます。通常のmodel／proof検証を省略せず、model digestも更新します。別に生成した同値candidateをruntimeへ結合しません。

この構成ではfile-rootを使わないため、今回見つかったblockerから独立しています。target gateのentity actualは未測定のnullのままです。

### 5.2 byte計算

path以外の固定公開row、JSON構文、末尾LFの合計は**339 bytes**です。

```text
1行 = 339 + 3757 = 4096 bytes
16行 = 16 × 4096 = 65536 bytes
```

+1 caseは、最後のtarget `p_15`の末尾部分だけを`"b"×121`へ変更します。変更したrequest／proof／coverageから別の正規ownerを生成します。

```text
15行 × 4096 + 1行 × 4097 = 65537 bytes
```

target配列のcanonical JSONは、それぞれ60,241／60,242 bytesです。16 target rowsであり、長いsource fileや10,001 model recordsを必要としません。private wireの正確なlengthや全lower gateの合格は、実装環境のtestで確認する必要があります。

### 5.3 独立known vectors

key-sort／compact／UTF-8、各公開row末尾LF一つで計算しました。

| 対象 | bytes | SHA-256 |
|---|---:|---|
| exactの公開JSONL全集合 | 65,536 | `702dbbfdd93207ea5e659026f9706d8278a3568eaf401394f57adfda56411216` |
| +1の公開JSONL全集合 | 65,537 | `c9373a44926510bbf4508a8702e0f8f9b217764ea4f1f7979f342c61b3e3a08b` |
| exactのrequest targets配列、LFなし | 60,241 | `28ecb3b271908a668a6784f7dd13f1b0da87688ef1ac788bfd4d409ea2b36975` |
| +1のrequest targets配列、LFなし | 60,242 | `202edea2fb3f5a9aeb2eca6f85c238d541c96c0fd9b4e083ad21e86efa53e583` |
| 空stderr | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

overflow時のmanifest用replacement rowは次です。

```json
{"code":"CSV-NEXT-LIMIT-003","domain":"next","line":null,"message":"A configured byte or structural resource limit was exceeded at a bounded processing boundary.","outcome":"payload_unavailable","path":null,"recoverable":false,"ref_permission":"none","schema":"code-structure-viz.diagnostic/v1","severity":"error","symbol":null,"type":"diagnostic"}
```

このrow＋LFは349 bytes、SHA-256は次です。

```text
f0ccb6a1a16b372801b650f05f8457d04468b7027980ef252c4bd29407cf5ad9
```

**この349 bytesをoverflow時のstderrへ出してはいけません。** stderrは空で、replacementはmanifest用診断の値です。

---

## 6. 再開に必要な検証と非循環接続

### file-root側の再検証条件

先行unitまたはscope変更の採否を決める前に、最低限次を区別して確認する必要があります。

| ケース | 現行コードから予測される結果 |
|---|---|
| request Fileをmodelに残し、同pathの正しいparse/read rootと必須taintを与える | published／tainted非交差に違反します。 |
| root対象Fileをmodelから取り除く | `file_correspondence`で拒否されます。 |
| root対象Fileをproof-onlyへ移す | 現在のsource correspondence／proof-only source拒否規則を変更しない限り成立しません。 |
| Fileをroot seedから省略する | 必須seedの独立再導出結果と不一致になります。 |
| SOURCE-001をmodelへ追加するだけ | proof-backed parse/read rootのadmission証拠にはなりません。 |

これらは未実行の検証項目です。直接constructorや内部collaboratorのmock／monkeypatchで通す正例にはしません。

### 診断unitを再開できる条件

必要なのは、次のどちらかを明示することです。

1. **file-rootを正規Coreでadmitするsource/proof契約と、その先行unitが確定することです。**
2. **今回のcheckpointからfile-root正例を分離するscope変更が確定することです。**

それまでは、全範囲を認定する新schema、実行順序、focused／adjacent gate、ordinary commit／pushを一式のready briefとして提示しません。既存の748件や旧PlantUML83件、old goldens等のpassは、この欠けたadmissionの証拠にはなりません。Report自身も全A02／A03とは区別しています。attachments-bundle

判断後の依存方向は変えません。

```text
同じrun2
  ├─ requested publication candidates
  └─ catalog-owned pre-bound diagnostics
       → 固定64 KiBの安全診断bytes/accounting
       → 後続safe domain/root/summary/typed-unavailable候補
       → 全selectorのpre-copy／一回のselected-copy
       → final disposition／single final owner
       → publication/domain/root/stdout-v2 exact refs
```

診断ownerを最終publicationへ改名せず、後段から元run2や診断入力を逆に再構成する依存も作りません。

---

## 7. 実施範囲と停止

本回答で実施したのは、GitHubコネクタによる指定branch／SHAと関連コードの参照、添付Current仕様・契約の照合、ASCII literalのbyte length／SHA計算です。**repository tests、実装、commit、push、独立レビューは未実行です。**

root `AGENTS.md`の取得は404でした。local user AGENTS／`user.rules`／`use-workbench`を確認したとは主張しません。今回、外部状態を変更する操作やSpecDock mutationは行っていません。

未採択ASSET policyへの再質問・採択、新code／catalog変更、request-independent reader、fatal／usage／interrupt意味の変更は行いません。解決が必要なのは、今回要求されたfile-root正例と既存request-bound Core契約の整合です。

**検証済み基準は`chemitaro/code-structure-viz`／`iss-00008-generate-nextjs-component-snapshots`／`987d0ebc7244c0ea0d2b0400f013cc220e7cccb3`です。A02は未完了で、独立A03、production A04、実TypeScript／OS／package、Final A05の認定とは分離します。**
