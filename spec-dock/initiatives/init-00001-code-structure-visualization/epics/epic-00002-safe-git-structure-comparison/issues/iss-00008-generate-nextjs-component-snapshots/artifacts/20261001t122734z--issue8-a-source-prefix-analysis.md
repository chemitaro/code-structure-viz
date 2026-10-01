# A02限定設計分析

## 1. exact repository / branch / SHA の確認

開始時と回答直前の2回、GitHubコネクタで次を直接確認しました。

| 項目 | 確認結果 |
|---|---|
| repository | `chemitaro/code-structure-viz` |
| target branch | `iss-00008-generate-nextjs-component-snapshots` |
| expected SHA | `e15033d6f9d6cdd9c47bda21d568c71c62b689e0` |
| 開始時branch tip | `e15033d6f9d6cdd9c47bda21d568c71c62b689e0` |
| 回答直前branch tip | `e15033d6f9d6cdd9c47bda21d568c71c62b689e0` |
| tree SHA | `8aca537f4cfda6cb8e27678de27def6075896d04` |
| SHA比較 | exact match |

回答直前のbranch objectでも、指定branchのtipは期待値とbyte-for-byte一致しています。

実際に試みたGitHub操作は、repository metadata取得、対象branch検索、対象branch REST取得、exact commit tree取得、対象commitをrefにしたファイル取得です。default branchや他branchへのfallbackは行っていません。

### 読んだ範囲

exact commitから主に次を確認しました。

- Current normative authorityのRequirement、Design、Plan
- `docs/contracts/next-provenance-v2.md`
- `docs/contracts/next-execution-assets-v1.md`
- `docs/contracts/next-trusted-type-environment-v2.md`
- `schemas/next-provenance-v2.schema.json`
- `src/code_structure_viz/adapters/next/source_acquisition.py`
- `src/code_structure_viz/source/source_view.py`
- `tests/contracts/next_runtime_v2_reference.py`
- `tests/contracts/next_runtime_v2_validation.py`
- `tests/contracts/test_next_runtime_v2_contracts.py`
- core diagnostic catalogの現状

添付bundleは補助資料として扱いましたが、相違時は指定どおりexact GitHub commitを優先しました。添付側でもCurrent normative authorityがRound Nを履歴とし、AのmacOS/Linux、Python 3.12以上、明示Node stable major 22以上、同一process version観測、非適用時のruntime未観測を正本としていました。attachments-bundle

### 未確認・未認定

次は確認・認定していません。

- actual Node spawn、actual TypeScript 5.9.2利用、actual trusted declarations利用
- macOS/Linuxのproduction process時系列
- A03 Code Review certificate
- public domain/root/semantic/stdout exact-ref closure
- wheel/sdist/offline package受入れ
- 831KB超の旧巨大validator全行の逐語レビュー
- テストの再実行

ユーザー提示の「583 related、120 schema/doc-pointer、Ruff/mypy/SpecDock pass」は今回再実行していません。exact Planでは、Core/provenance 88 passと、reader-owned prefix・public exact refs・A03・actual OS/TSが未完了であることを確認しました。

これはA02の設計advisoryであり、A03 certificateではありません。

---

## 2. 結論

最小かつ正確な推奨は次です。

1. **保持済みexpected metadataを捨てない。**
   applicable permission後にexecution assets ownerとreadonly trusted descriptorが成立しているなら、source/config/program failureでも、v2 prefixの`runtime_bundle`と`trusted_environment`を`observed`にします。

2. `trusted_environment`の意味を、現在のv2どおり**expected declaration metadata**に限定します。
   これはactual Node、actual TypeScript import、actual child useの観測ではありません。

3. `node_candidate`、`request`、`launch_policy`、`process_start`、`node_version`、`control_response`、`semantic_payload`、`compatibility`、`model`、`budget`は、source failureでは引き続き`unobserved/null`です。

4. package-only preflight後のtarget `package.json` bytesは、同一`DescriptorAnchoredSourceReadSession`に結び付いたopaque permission ownerからcached replayし、**二度目の物理readをしない**方式でよいです。

5. ただしcached readerだけでは不十分です。config parse、membership、file count、decoded-totalなど、readerより上位で決まる状態を正確に保持するため、実acquisition engine自身が生成する**immutable milestone journal**が必要です。

6. execution assetsの取得・検証失敗を、`TRUST-*`、`NODE-002`、`SOURCE-*`へ押し込むのは不適切です。少なくとも新しい`execution_assets` stageと、availabilityとpackage correctnessを分ける2コードが必要です。

7. current production sealはcomplete-onlyです。reader prefixは`PartialSourceSeal`でもsafe-subset certificateでもありません。program/context ordinary READは、現状では`SOURCE-003/payload_unavailable`です。

8. Designのnormative mappingはdecoded source totalを`LIMIT-002`としていますが、exact source codeは累積total exhaustionを`TOO_LARGE`、さらに`LIMIT-001`へ分類し得ます。これは今回のprefix contractで分離すべき既存不整合です。

---

## 3. 論点1：expected metadataを捨てるか、v2早期prefixに残すか

### 現在の矛盾

Current Requirement item 11は、source failureでrequest/runtime/toolchain/trusted-environment等を作らないとしています。一方、Design Aとtrusted v2 contractは、次の順序です。

```text
package-only applicability permission
  -> applicable時だけexecution assetsを一度保持
  -> 同じownerのreadonly trusted descriptorをCoreへ渡す
  -> descriptor digestを含むsource sealを作る
  -> request / staging / spawn
```

Designは明示的に、execution Moduleがpackage permission後に資材を保持し、source seal前にreadonly trusted descriptorをCoreへ渡すとしています。

trusted v2 contractも、descriptorを「期待する宣言profileのmetadata」と定義し、actual child利用と区別したうえで、同じownerをsource sealへ結合しています。

一方、Requirement item 11の最後はsource failureで`trusted-environment`観測を作らないとしています。

これはtrust modelそのものの矛盾ではありません。**expected metadataとactual runtime useを、古い「trusted environment観測」という一語で扱っている語彙上の矛盾**です。

### 比較

| 案 | 利点 | 問題 |
|---|---|---|
| expected metadataをsource failure時に捨てる | 旧item 11の表面的な記述と一致する | source planへ実際に入れたtrusted digestのownerがprovenanceから消える。後段が再構成しやすくなり、same-owner joinを弱める |
| expected metadataをv2 prefixに残す | 実際の因果順、source-plan digest、retained ownerを忠実に表す。別ownerへの差替えを検出できる | `observed`がactual TS useと誤読されない文言修正が必要 |
| actual-use用の別slotを追加する | expected/actualを外形上分けられる | 現在はactual trusted useを直接証明するownerがなく、未観測値を新slotで作るだけになる。17-slot closureを不要に広げる |

### 推奨

**expected metadataをv2早期prefixに保持します。**

applicable permission後、資材保持とdescriptor生成まで成功したsource failureでは、次を固定します。

```text
runtime_bundle       = observed
trusted_environment  = observed  # expected readonly descriptor
node_candidate       = unobserved
request              = unobserved
launch_policy        = unobserved
process_start        = unobserved
node_version         = unobserved
control_response     = unobserved
semantic_payload     = unobserved
compatibility        = unobserved
model                = unobserved
budget               = unobserved
```

現行v2 contractは、`trusted_environment`を「retained declarationsから導出したreadonly expected descriptor」であり、TS import/useの観測ではないと既に定義しています。`runtime_bundle`も同じretained asset descriptorです。

また現行schemaの`request_independent_failure` branchは、request以後のslotをunobservedに固定していますが、`trusted_environment`と`runtime_bundle`を強制的にunobservedにはしていません。したがって**17-slot追加やschema identity変更は不要**で、producer/validatorとCurrent文言を閉じるのが最小です。

### 機械的clarificationと人間判断

| 種別 | 内容 |
|---|---|
| 機械的clarification | applicable permission後にasset ownerが成立したら`runtime_bundle=observed` |
| 機械的clarification | expected descriptorが成立したら`trusted_environment=observed` |
| 機械的clarification | source failureではNode/request/process/semantic suffixをすべてunobserved |
| 機械的clarification | `trusted_environment`をactual TS useと表現しない |
| 機械的clarification | source planのtrusted digestと同一owner descriptorを再検証する |
| 追加の人間判断 | slot名を`expected_trusted_environment`へ変更するか |
| 推奨 | slot名は変更しない。v2 docsとvalidator messageでexpected semanticsを明記する。名前変更はpublic closureを不要に拡大する |

Requirement冒頭の因果鎖も、次のように修正すべきです。

```text
target package bytes
  -> PackageApplicabilityMatrix / applicable permission
  -> installed execution assets retention
  -> readonly expected trusted descriptor
  -> source acquisition/config/graph/seal
  -> request
  -> explicit runtime candidate/policy
  -> actual process/control observation
  -> Core admission
  -> publication
```

---

## 4. 論点2：cached package reader coordinator

### 安全性の評価

提案は基本的に安全です。ただし、二種類の「package」を区別する必要があります。

- **target package bytes**: 対象repositoryの各root `package.json`
- **execution assets**: CodeStructureViz package内のadapter、TypeScript libs、trusted declarations

cached readerが再利用するのは前者です。execution Moduleが保持するのは後者です。

現行`DescriptorAnchoredSourceReadSession`は、pathごとの`read_once`、read attemptの重複拒否、file/total/count limit、descriptor read、最後のinventory/head/file-signature drift check、one-shot sealを持っています。

一方、現行`seal_source_acquisition`は内部で再びpackage preflightを始め、`trusted_environment_digest`を入口で要求し、config/source/graph/sealまで一度に行います。成功する`SourceAcquisitionSeal`は`SourceView.failures`を許さないcomplete-onlyです。

したがって、同一sessionで先に読んだpackageを二度目に物理readさせず、現行sealへ渡すprivate cached readerは整合します。

### 最推奨の内部構造

```text
DescriptorAnchoredSourceReadSession
  -> ReaderOwnedPackagePreflightV2
       - same session stamp
       - frozen target package bytes
       - applicability matrix
       - actual read-attempt evidence

  -> all non-applicable
       - stop
       - execution Moduleを作らない

  -> applicable permission
       -> RetainedNextExecutionModuleV2
            - RetainedExecutionAssets
            - readonly expected trusted descriptor
            - permission ownerへのopaque join
            - Node candidateはまだ無し

       -> CachedPackageDelegatingReaderV2
            - exact package pathsだけpreflight bytesを返す
            - physical read countは増やさない
            - config/source/sealは同じunderlying sessionへdelegate

       -> SourceAcquisitionEngineV2
            - actual reader trace
            - derived milestone journal
            - existing seal logic
            - complete seal / typed failure / fatal / interrupt
```

### 小さいreference moduleとInterface

提案するreference-only pathは、たとえば次です。

```text
tests/contracts/next_source_prefix_v2_reference.py
tests/contracts/next_source_prefix_v2_validation.py
tests/contracts/test_next_source_prefix_v2_contracts.py
```

巨大な`next_reference_validation.py`へ追加するより、現在のA02方針に合います。

Interfaceは次の程度で十分です。

```python
preflight_package_permission_v2(
    intent: SourceDiscoveryIntent,
    session: DescriptorAnchoredSourceReadSession,
) -> (
    ReaderOwnedApplicablePermissionV2
    | ReaderOwnedNotApplicableV2
    | ReaderOwnedPackageFailureV2
)

retain_execution_module_v2(
    permission: ReaderOwnedApplicablePermissionV2,
    installed_resources: InstalledExecutionResourceReader,
) -> RetainedNextExecutionModuleV2 | ExecutionAssetFailureV1

coordinate_source_phase_v2(
    permission: ReaderOwnedApplicablePermissionV2,
    module: RetainedNextExecutionModuleV2,
    *,
    max_entities: int,
) -> SourcePhaseOutcomeV2
```

#### opaque ownerの責務

`ReaderOwnedApplicablePermissionV2`

- private constructor
- 同じ`DescriptorAnchoredSourceReadSession`へのopaque stamp
- intent identity
- frozen inventory/head anchor
- target package bytes
- applicability matrix
- package read-attempt trace
- caller提供のphase/stage/codeを受けない

`RetainedNextExecutionModuleV2`

- permission成立後だけfactory生成
- `RetainedExecutionAssets`を保持
- readonly trusted descriptorを同じownerから導出
- asset descriptor/header/staging bytesを別lookupしない
- Node candidate、request、process観測を含めない

`ReaderOwnedSourceTraceV2`

- ordered immutable events
- `physical_read`と`cached_reuse`を区別
- phaseはcoordinatorが実call位置から記録
- success時はsize/digest
- failure時はclosed failure kindと安全なmeasurement
- raw source、OS error、absolute pathを含めない

`SourcePhaseOutcomeV2`

- `complete_seal`
- `payload_unavailable`
- `source_integrity_fatal`
- `interrupted`

のclosed unionにします。`partial_safe` variantはまだ置きません。

### cached readerだけでは足りない点

reader traceだけでは次を完全には表せません。

- JSONC parseの成功・失敗
- local extends closure
- resolved membership
- selected file count
- total decoded countの境界
- graph derivation milestone
- plan構築開始・完了

これらはreaderより上の`seal_source_acquisition`内部で決まります。

したがって、実engine自身がprivateに生成する次のjournalが必要です。

```text
SourceAcquisitionMilestoneJournalV2
  applicability_derived
  expected_resources_joined
  config_control_closed
  membership_resolved
  selection_measured
  source_reads_completed
  graph_derived
  drift_check_started
  seal_completed
```

callerはjournal、phase、stage、codeを注入できません。

### 現行APIを壊さない方法

既存のpublic signatureはcompatibility façadeとして維持できます。

```text
seal_source_acquisition(...)
  -> internal SourceAcquisitionEngineV2.run(...)
  -> complete resultなら既存SourceAcquisitionSealを返す
  -> failureなら既存typed exceptionを再送出
```

新coordinatorだけがengineのopaque attempt ownerを受け取ります。これにより、

- success logicを二重実装しない
- v1 callerを変えない
- A02 reference producerがactual acquisition callへ結び付く
- failure stageをexception文字列から推測しない

という条件を同時に満たせます。

### single-read / drift / partial-control / membershipへの影響

| 項目 | 評価 |
|---|---|
| target package physical read | preflightで1回。seal内のpackage要求はcache replay。二度目の物理readは禁止 |
| logical applicability derivation | 同じbytesから再検証してよい。ただしpreflight matrixとseal matrixのexact equalityを要求する |
| final drift check | same sessionのinventory/head/file signaturesで実施。packageをcache replayしても、最初のphysical read signatureは最終check対象 |
| config/local extends | underlying sessionで各path一度だけ |
| partial control | 読めたcontrolのdigestと失敗attemptだけ保持。resolved configやmembershipを合成しない |
| selected membership | actual config closureからengineが導出。callerのpaths/roles/membershipを受けない |
| trusted digest | free stringではなくmoduleのreadonly descriptorからのみ渡す |
| safe subset | prefixから導出しない。別のsealed graph/ledger certificateが必要 |
| post-seal reads | sessionがclosed。assetsもtarget sourceも再lookupしない |

### より単純な代案

A04でproduction実装を整理する段階では、`NextSourceAcquirer`自体を一つのtransaction ownerとして保持し、

```text
preflight
-> asset retention
-> continue config/source/seal
```

と継続する方式の方が、cached replayを不要にでき、概念上はさらに単純です。

ただしこれは現行sealの内部構造を大きく組み替えます。A02のreference closureとしては、**cached reader＋内部journal**の方が差分が小さく、既存seal regressionを維持しやすいです。

### 避ける案

- target packageを二度物理readする
- callerから`dict[path, bytes]`を自由入力する
- callerからphase/stage/codeを渡す
- caller supplied `SourceAcquisitionSeal`やv1 provenanceをv2 authorityにする
- trusted digestをsource seal後に後付けする
- final plan/membership/role mapをcallerから注入する
- reader prefixを`partial_safe` certificateとして使う

---

## 5. 論点3：execution assets取得・検証失敗のclosed mapping

### 既存catalogだけでは不十分

| 既存code | 本来の意味 | asset失敗への流用が不適切な理由 |
|---|---|---|
| `CSV-NEXT-TRUST-001` | expected/actual trusted digest mismatch | installed member欠落、resource I/O、adapter header不正とは異なる |
| `CSV-NEXT-TRUST-002` | target declarationによるshadow/augment | source graphとtarget declarationsが必要。assets取得前には成立しない |
| `CSV-NEXT-TRUST-003` | target pathとtrusted virtual pathのcollision | source membership後のtarget-side問題 |
| `CSV-NEXT-NODE-002` | process spawn不能 | assets failureではspawnを試みていない |
| `CSV-NEXT-SOURCE-*` | target repository source acquisition | product package resourceの問題ではない |
| `CSV-INTERNAL-001` | 予期しない内部invariant failure | 想定可能なresource不在やI/Oまで内部bugにすると原因と回復性を失う |

現行v2 provenance schemaにも`execution_assets` stageや対応codeはありません。

### 最小提案

コード名は未採択の提案です。

| proposed code | stage | 意味 | outcome |
|---|---|---|---|
| `CSV-NEXT-ASSET-001` | `execution_assets` | installed execution resourceを取得できないが、product package contract違反を証明できない | domain `payload_unavailable`、exit 3、safe failure manifest可 |
| `CSV-NEXT-ASSET-002` | `execution_assets` | locked installed package/profileが自己契約を満たさない | terminal fatal、exit 1、semantic/failure manifestなし |
| `CSV-INTERNAL-001` | core terminal | closed理由へ分類できない内部error、owner invariant違反 | fatal、exit 1 |

固定messageの例は次です。

```text
CSV-NEXT-ASSET-001
The bundled Next.js execution assets could not be acquired.

CSV-NEXT-ASSET-002
The bundled Next.js execution assets violate the installed package contract.
```

どちらもpublic diagnostic path/refは無し、raw OS error無しとします。

### closed reasonの割当て

| 原因 | 推奨code |
|---|---|
| resource backend上、存在するmemberの通常read I/O不能 | `ASSET-001` |
| locked必須memberが存在しない | `ASSET-002` |
| memberがsymlink/non-regular | `ASSET-002` |
| installed inventory shape/order/duplicate不正 | `ASSET-002` |
| adapter header/version marker不正 | `ASSET-002` |
| role集合不正 | `ASSET-002` |
| trusted declarationのsize/hash/profile不一致 | `ASSET-002` |
| adapter / TS library / trusted declarations間のlocked identity不一致 | `ASSET-002` |
| 原因をclosed evidenceへ分類できない例外 | `CSV-INTERNAL-001` |

execution assets contractは、retained bytes、descriptor、adapter header、staging contentを同じownerから導出し、metadataだけの再hashをbyte joinとして受け入れない設計です。

### package correctness fatalとdomain unavailable

推奨基準は次です。

- **環境上の取得不能**: domain unavailable
- **本製品が自ら約束したinstalled package contract違反**: fatal
- **予期しない実装bug**: internal fatal

固定memberがない、header/profile/roleが壊れている場合を単なるNext unavailableにすると、壊れた製品packageを正常な環境不在と誤表示します。source substitutionやinventory driftをfatalにする既存方針とも整合しません。

ただし、これをfatalにすると将来のmulti-domain runでPython/SQLAlchemyまでrun-level停止する可能性があります。Issue #8は現在single-domainなので、**fatal境界の採択はownerによる明示判断が必要**です。私の推奨は上記の二分です。

### provenance v2の変更点

17-slotは増やさないことを推奨します。

`ASSET-001`の場合:

```text
applicability       = observed
runtime_bundle      = unobserved  # complete ownerをmintできていない
trusted_environment = unobserved
node_candidate      = unobserved
request以後          = unobserved
stage               = execution_assets
failure_code        = CSV-NEXT-ASSET-001
```

部分的に読んだasset bytesやraw read errorは、privateな`ExecutionAssetFailureV1` ownerだけに保持します。`runtime_bundle`はcomplete retained descriptorのslotなので、partial resource attemptを入れて意味を広げません。

`ASSET-002`と`CSV-INTERNAL-001`はfatal terminal branchへ進め、ordinary `next-provenance/v2`を生成しない方が、source-integrity fatalと一貫します。

必要なschema修正は次です。

1. `request_independent_failure.stage`へ`execution_assets`追加
2. `CSV-NEXT-ASSET-001` / `execution_assets` pair追加
3. applicable observationを必須observedにするconditional
4. `runtime_bundle`と`trusted_environment`の状態をopaque owner成立状況から検証
5. request以後をすべてunobserved
6. `ASSET-002`と`INTERNAL-001`はordinary provenanceのfailure matrixへ追加しない

---

## 6. source phaseの固定表

以下をA02のnormative matrixにすることを推奨します。

| case | 実際に観測する値 | 明示的absence | code / stage / outcome | reader・resource・Node |
|---|---|---|---|---|
| successful seal | applicability matrix、resolved config、SourceView fingerprint、limits、final source plan、runtime bundle、expected trusted descriptor | Node candidate、request、process、actual version/control、semantic/proofはまだ無し | source phase complete。まだ`request_bound_success`ではない | sessionはseal後closed。assets保持済み。Node spawnはまだ不可 |
| all non-applicable | applicability matrixだけ | execution assets、trusted descriptor、config、source、Nodeすべて無し | `APP-001` / `applicability` / `not_applicable` / exit 0 | package preflight後停止。asset factoryもNodeも呼ばない |
| malformed package | package bytes identityとmalformed applicability observation | assets/config/source/Node無し | `APP-002` / `applicability` / unavailable / exit 3 | package read以後停止 |
| package ordinary READ | failed package read-attempt identity。bytesは無し | matrixの成功値、assets/config/source/Node無し | `APP-002` / `applicability` / unavailable / exit 3 | actual attemptだけ。再read禁止 |
| root config ordinary READ | applicability、runtime bundle、expected descriptor、実control read failure prefix | resolved config、membership、source、limits/source plan、request/Node無し | `SOURCE-003` / `source_control` / unavailable / exit 3 | 同じsession。assetsはcleanup用保持、実行禁止 |
| malformed config / local extends | applicability、runtime bundle、expected descriptor、読めたcontrol bytes identityとparse/extends failure | source、plan、request/Node無し | typed `CONFIG-001`または`CONFIG-002` / `config_validation`または`source_control` / unavailable | 空configへ置換しない |
| program/context ordinary READ | applicability、runtime bundle、expected descriptor、resolved config、selected membership、actual source-read failure prefix | complete SourceView、limits/source-plan row、request/runtime/proof無し | 現状は`SOURCE-003` / `source_read` / unavailable / exit 3 | current complete-only。prefixだけでpartial-safeにしない |
| per-file byte limit | 上記prefix＋path-safe file size、configured file limit、actual boundary | complete source/plan/request/Node無し | `LIMIT-001` / `source_read` / unavailable / exit 3 | raw partial bytesを保持しない |
| decoded total limit | 上記prefix＋total-before、next size、configured total、actual total boundary | complete source/plan/request/Node無し | **`LIMIT-002` / `source_read`** / unavailable / exit 3 | current codeの`TOO_LARGE`→`LIMIT-001`は修正対象 |
| file-count limit | applicability、assets、expected descriptor、config/membership、selected actual countとlimit | source bytes/seal/request/Node無し | `LIMIT-002` / `source_selection` / unavailable / exit 3 | selected setをcallerから受けない |
| selected symlink | 失敗前prefix＋symlink check result。content無し | seal/request/Node無し | `SOURCE-002` / `source_integrity` / unavailable / exit 3 | symlink targetを読まない |
| unsafe path / normalized collision | inventory/path-safety observationだけ。unsafe content無し | 後続全部無し | 既存common path-safety terminal mapping。Next `SOURCE-002`へ一律統合しない | reader開始前または初期inventoryで停止 |
| inventory/content drift | private anchor、read signatures、actual drift comparison | ordinary provenance、request、semantic、failure manifest無し | `SOURCE-INTEGRITY-001` / `source_integrity` / fatal / exit 1 | session terminal close。Node禁止 |
| handled interrupt | interruptまでに実在したprivate ownersだけ | ordinary Next provenance、未観測suffix、成功status、proof/measurement補完無し | `CSV-INTERRUPT-001` / core terminal / interrupted / exit 130 | 新規read/resource/spawn停止、cleanupのみ |

### decoded-totalの既存不整合

Current Designは次を明記しています。

```text
file bytes          -> LIMIT-001
file count          -> LIMIT-002
decoded source total -> LIMIT-002
```

一方、exact sourceでは、

- sessionの`remaining`不足も`TOO_LARGE`
- `_GuardedSourceReader`は`TOO_LARGE`を`LIMIT-001`
- `seal_source_acquisition`のtotal超過も`LIMIT-001`

となっています。

最小修正は、reader failure evidenceを次のように分けることです。

```text
file_bytes_exceeded
decoded_total_exceeded
file_count_exceeded
```

少なくともprivate evidenceに、

```text
limit_kind
configured_limit
actual_before
attempted_increment
actual_at_failure
```

を持たせます。publicには安全なcountだけを投影し、pathやbytesを出しません。

さらにprovenance schemaは、`LIMIT-002`のallowed stageへ`source_read`を追加する必要があります。現状は`source_selection`だけです。

### partial_safeについて

現行`SourceAcquisitionSeal`は、`SourceView.failures`が存在すると拒否します。現行result unionも`NextNotApplicableAcquisition | SourceAcquisitionSeal`で、`PartialSourceSeal`を実装していません。

したがって、

```text
ordinary program/context READ
  -> reader prefix exists
  -> SOURCE-003 / payload_unavailable
```

が現在の認定可能範囲です。

将来`SOURCE-001/partial_safe`へ進めるには、別のopaque ownerとして、

```text
PartialSourceSealCertificateV2
  - actual sealed graph
  - SourceFailureLedger
  - safe subset
  - target taint
  - closure completeness
```

が必要です。`ReaderOwnedSourcePrefixV2`にこの能力を持たせてはいけません。

---

## 7. Current R/D/P/schema/docsへの変更一覧

### Requirement

1. 冒頭の因果鎖を、expected resourcesがsource seal前に来る順序へ修正
2. item 11の「trusted-environment観測無し」を、次に置換

```text
actual Node/TS/process observationは無し。
ただしapplicable permission後に同じexecution Moduleが保持した
runtime bundleとreadonly expected trusted descriptorは、
source failure prefixへ保持する。
```

3. all non-applicable、package failureではassets/trusted metadataを観測しないことを維持
4. `execution_assets` failure branchを追加
5. total decoded limitを`LIMIT-002/source_read`として明示
6. reader prefixがsafe-subset certificateでないことを明記

### Design

1. Aのsequenceで、target `package.json`とinstalled execution assetsを別名称にする
2. readonly descriptorのexpected semanticsをCurrent authority本文へ移す
3. source failure paragraphから、expected trusted metadataまで一律nullにする記述を削除
4. `ReaderOwnedApplicablePermissionV2`
5. `RetainedNextExecutionModuleV2`
6. `CachedPackageDelegatingReaderV2`
7. `SourceAcquisitionMilestoneJournalV2`
8. `SourcePhaseOutcomeV2`
9. `ExecutionAssetFailureV1`
10. complete prefixとpartial-safe certificateを明確に分離
11. per-file/total/file-count failureを別measurementとして固定

### Plan

A02-3のexitへ次を追加します。

```text
reader-owned request-independent prefix
readonly expected-resource prefix
execution-assets failure mapping
single physical package read
same-session final drift
file/total/count measurement distinction
```

A02-4へ次を追加します。

```text
source-prefix independent reference module
positive/negative owner joins
terminal drift/interrupt vectors
legacy v1 exact invariance
public exact-ref closure
```

現状Planが示すとおり、これらが閉じるまでA03/A04へ進めません。

### Schema

`next-provenance-v2.schema.json`

- `execution_assets` stage追加
- `ASSET-001/execution_assets` pair追加
- `LIMIT-002/source_read`追加
- post-permission source failureにおける`runtime_bundle` / `trusted_environment` state条件
- source-phase failureでrequest以後をunobservedに固定
- not-applicableでは両resource slotをunobservedのまま維持
- fatal asset-integrity/internalはordinary provenanceから除外

新規private schema候補:

```text
next-package-preflight-evidence-v2.schema.json
next-source-acquisition-evidence-v2.schema.json
next-execution-asset-failure-v1.schema.json
```

ただしopaque Python owner自体をJSON objectで代替しません。schemaはownerから得た検証用projectionだけを検査します。

### Diagnostic catalog

次を同期します。

- fixed code
- severity
- recoverability
- fixed message
- path/ref permission
- stage
- outcome
- exit
- manifest permission

core catalogの`CSV-INTERNAL-001`は既に内部invariant failure用です。予測可能なresource failureへ流用しません。

### Contract docs

修正対象は最低限次です。

```text
docs/contracts/next-provenance-v2.md
docs/contracts/next-execution-assets-v1.md
docs/contracts/next-trusted-type-environment-v2.md
docs/contracts/next-source-plan-v1.md
docs/contracts/diagnostic-v1.md
```

新規候補:

```text
docs/contracts/next-source-prefix-v2.md
```

### 変更しないもの

- accepted Aのtrust model
- macOS/Linux
- Python 3.12+
- explicit user-managed Node stable major >=22
- same-child bootstrap / one response
- TypeScript 5.9.2
- Unicode 15.0.0
- old-space 512 MiB
- no target code/config/scripts/plugins/node_modules execution
- hostile same-UID、verified-FD、actual-image、hard RSSの非目標
- legacy process/provenance v1 schema、fixture、hash
- source/semantic identity algorithm v1
- Python/SQLAlchemy behavior

---

## 8. focused TDD vectors

以下は提案するテスト名です。現時点で実装済みとは扱いません。

| group | positive | negative |
|---|---|---|
| permission/order | `test_source_prefix_retains_assets_only_after_applicable_permission` | non-applicableでasset factoryが一度でも呼ばれたらfail |
| package single-read | `test_cached_package_replay_uses_one_physical_read_and_same_session` | underlying package read 2回、別session cache、caller bytes mapをreject |
| expected/actual | `test_source_failure_preserves_expected_resources_without_runtime_observation` | asset owner成立後にresource rowsを落とす、Node/TS actual slotを合成するmutationをreject |
| owner join | `test_source_prefix_requires_same_permission_asset_and_reader_owners` | 同一digestの別owner、duck owner、直接constructor、再hash metadataをreject |
| config/extends | `test_root_and_local_extends_failures_retain_actual_control_prefix` | caller phase、caller resolved config、空config fallbackをreject |
| membership | `test_selected_membership_is_engine_derived_before_source_reads` | caller supplied paths/roles/count、config declaration-origin欠落をreject |
| program READ | `test_program_read_failure_is_unavailable_without_partial_certificate` | prefixだけから`SOURCE-001/partial_safe`をmintする操作をreject |
| per-file limit | `test_file_limit_exact_and_plus_one_are_limit_001` | actual size無し、limit値差替え、partial bytes保持をreject |
| decoded total | `test_decoded_total_exact_and_plus_one_are_limit_002_source_read` | `TOO_LARGE`として`LIMIT-001`へ分類するmutationをreject |
| file count | `test_file_count_exact_and_plus_one_are_limit_002_source_selection` | attempted read数をselected membership countとして代用するmutationをreject |
| assets unavailable | `test_unreadable_execution_member_maps_to_asset_001_without_runtime_bundle` | `TRUST-001`、`NODE-002`、`SOURCE-003`への再分類をreject |
| package integrity | `test_missing_or_invalid_locked_member_maps_to_asset_002_terminal` | fatal branchからfailure manifestやordinary provenanceを作るmutationをreject |
| internal error | `test_unclassified_internal_error_remains_internal_terminal` | internal errorをASSET-001へ丸めるmutationをreject |
| privacy | `test_source_prefix_public_projection_excludes_raw_bytes_errors_and_absolute_paths` | source body、asset bytes、private package path、OS error textをnegative scan |
| measurement | `test_failure_measurement_is_derived_from_actual_reader_and_engine_counters` | free `actual`、free count、stage由来のsynthetic measurementをreject |
| drift | `test_package_read_then_asset_retention_then_source_drift_is_terminal` | cache replayをfresh readとしてdriftを隠すmutationをreject |
| interrupt | `test_source_phase_interrupt_has_no_ordinary_next_provenance` | Next failure code、成功status、後続measurement補完をreject |
| legacy v1 | `test_reader_prefix_v2_leaves_all_v1_schema_fixture_and_hash_bytes_unchanged` | v1 schemaへのadditive union、v1 digest再計算をreject |
| existing domains | `test_source_prefix_v2_does_not_change_python_or_sqlalchemy_vectors` | Next-only defaultsを既存domain fingerprintへ混入するmutationをreject |

既存A-runtime tests自身も「data-only contracts; no Node execution or product admission」と明記しています。したがって新testがgreenでもactual runtimeやA03の認定にはなりません。

---

## 9. 実装順

推奨順は次です。

1. **owner decisionを短いADR/adjudicationへ固定**
   - expected resource rowsをsource prefixへ保持
   - `ASSET-001/002`の名称
   - package integrity fatal境界
   - `execution_assets` stage
   - total decodedを`LIMIT-002/source_read`

2. **First Red**
   - source failureでresource rowsが落ちる
   - package physical reread
   - total limitがLIMIT-001になる
   - existing TRUST/NODE codeへasset failureを潰す
   - prefixからpartial-safeを生成する

3. **小さいreference ownerを実装**
   - permission
   - module/assets
   - cached reader
   - reader trace
   - milestone journal
   - asset failure owner
   - source phase result union

4. **producer/validatorを閉じる**
   - same-owner identity
   - actual events
   - no free stage/code/count
   - no raw data leakage

5. **schema/catalogを同期**
   - provenance stage/code
   - private evidence projections
   - diagnostics

6. **Current R/D/P/docsを同期**
   - historical Round Nは変更しない
   - legacy v1 contractは変更しない

7. **focused testsをGreen**
   - owner joins
   - limit exact/+1
   - terminal routes
   - privacy
   - legacy invariance

8. **related/full quality gates**
   - relevant Core/provenance
   - related contracts
   - schema/doc-pointer
   - Ruff/format/mypy
   - SpecDock
   - `git diff --check`

9. **public exact-ref closure**
   - run/publication/domain/semantic/root/stdout v2
   - source prefixのpublic measurement
   - terminal selector matrix

10. **clean/push後の新exact SHAでA03**
    - `P0=0`
    - `P1=0`
    - `review_status=pass`

11. **その後にA04**
    - actual installed resources
    - actual Node/TS
    - macOS/Linux
    - process/cleanup
    - CLI/publication

---

## 10. 残る人間判断

### 必須

1. **新diagnostic codeの正式名称**
   - 推奨: `CSV-NEXT-ASSET-001/002`

2. **installed package correctnessのfatal境界**
   - 推奨: locked member欠落、header/profile/role/mismatchはfatal
   - 通常resource I/Oだけdomain unavailable

### 任意だが推奨を固定できるもの

3. **stageを一つにするか**
   - 推奨: `execution_assets`一つ
   - acquisition/validationの違いはprivate reason enumで表す

4. **`trusted_environment` slotを改名するか**
   - 推奨: 改名しない
   - docsで`readonly expected descriptor; not actual use`を固定

5. **A04でcached replayを残すか、transactional acquirerへ整理するか**
   - A02: cached reader＋journal
   - A04: production実装時にtransaction ownerへの内部refactorを再評価

### 人間判断を追加しなくてよい点

- source failure後もexpected descriptorを保持すること
- actual Node/TS/processを補完しないこと
- same underlying sessionを使うこと
-二度目の物理package readをしないこと
- caller supplied phase/stage/seal/provenanceを拒否すること
- reader prefixをsafe-subset certificateにしないこと
- legacy v1を不変にすること

これらはaccepted A、現行v2 expected-metadata semantics、source-planのtrusted digest、same-owner原則から機械的に導けます。

**最終推奨は、17-slotを維持したままexpected `runtime_bundle` / `trusted_environment`をsource早期prefixへ保持し、same-session cached package replayとengine-owned journalを組み合わせ、asset availabilityとinstalled package integrityに新しいclosed mappingを設ける案です。** expected metadataを捨てる案、既存TRUST/NODE codeへ潰す案、prefixをpartial-safe証明へ流用する案は避けるべきです。
