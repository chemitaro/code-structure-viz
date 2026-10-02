## GitHub検証結果

指定されたGitHubコネクタで、他ブランチへフォールバックせずに対象を確認しました。

| 項目 | 確認値 |
|---|---|
| Repository | `chemitaro/code-structure-viz` |
| Branch | `iss-00008-generate-nextjs-component-snapshots` |
| Expected SHA | `f8d5c41e4c379b1ac471fa7f14f15ea75745cdbd` |
| GitHub branch tip | `f8d5c41e4c379b1ac471fa7f14f15ea75745cdbd` |
| 判定 | byte-for-byteで一致 |



そのrefから、Issue rootの`requirement.md`、`design.md`、`plan.md`のCurrent normative authority、現行契約、指定されたvalidator範囲を取得しました。

---

# 結論

採択済み方針は、次の一つの移行単位として具体化するのが最小かつ一貫しています。

> **取得済みsource inventoryは親request/source sealが完全所有し、公開modelはそのinventoryから独立に検証されたsafe semantic subsetだけを所有する。proofは両者の完全な対応関係を証明するが、Project/Fileのsource metadataを新たに供給する権限を持たない。**

現在の矛盾は、全request Fileをmodelへ要求する一方、同じFileをmandatory taint seedとして公開禁止にしていることにあります。Fileをmodelから外す、File seedを省く、proofに自由metadataを足す、という三つの回避はいずれも既存guardに拒否されています。attachments-bundle

したがって、候補の選択肢1を正式ADRとして採択し、次を行います。

1. request/response transport v2と既存proof wire shapeは変更しない。
2. v1のProject/File/entity record、ID algorithm、semantic algorithm、trusted profileは変更しない。
3. 親側Core admissionと公開文書だけを、一つの同期したv3世代へ移す。
4. 旧`next-semantic-admission-v2.md`、旧schema、旧KATは歴史的referenceとして残し、意味を遡及変更しない。
5. 新ASSET failure policy、early reader prefix、File seedの省略、protocol rejectionのSOURCE化は採択しない。

これはcandidateで推奨されていた「inventoryとsafe subsetの区別、Project membershipの分離、countの分離、source/proof/version closure」をそのまま規範化する案です。attachments-bundle

---

# 1. 新accepted ADRへ記録する決定

## 決定文

**取得inventoryとsafe semantic subsetの所有権を分離する。**

全取得Project/Fileのcanonical source recordは、同じ`SourceAcquisitionSeal`、同じ親request、同じretained ownerだけをauthorityとする。公開modelは、完全inventoryからmandatory root、seed、causal edge、taint closure、failure dispositionを独立導出した結果として安全と認定されたFileおよびsemantic recordだけを含む。

proof内のProject/File discovered rowはIDだけを運び、`record=null`とする。親validatorがrequestからcanonical source recordを再構成する。childによるProject/File metadata供給は、内容が偶然一致していても拒否する。

## 非決定事項

このADRは次を変更しません。

- ASSET failure policy
- seal成立前のreader I/O failure
- partial prefixの採用
- mandatory File seed
- causal closure
- target/export failure code
- Python／SQLAlchemy v1文書
- A02、A03、A04の受入れ境界
- 実Node／TypeScript／OS／CLIのproduction認定

candidate文書はdraft履歴のまま保持し、`状態`や本文をacceptedへ書き換えません。新しいaccepted ADRが`derived_from`でcandidateを参照します。

---

# 2. Requirementへ差し込む規則

以下をCurrent Requirementへ規範規則として追加します。

| ID | 規則 |
|---|---|
| **R-SI-001 Inventory authority** | 全取得Project/Fileは、completeな同一source sealから作られた親requestだけが所有しなければならない。disk再read、child metadata、synthetic bytes/hash、別requestからの補完を禁止する。 |
| **R-SI-002 Exact source partition** | 全取得Fileは、`safe`、`failed`、`excluded`のいずれか一つに必ず属さなければならない。欠落、重複、複数disposition、inventory外Fileを拒否する。 |
| **R-SI-003 No arbitrary omission** | untaintedかつfailedでない取得Fileは、必ずsafe modelに含まれなければならない。利用者、child、budget gateによる任意除外を禁止する。 |
| **R-SI-004 Full-inventory proof** | root、mandatory seed、causal edge、taint、target、Module owner、export/source-graph witnessは、safe subsetではなく完全取得inventory上で検証しなければならない。 |
| **R-SI-005 Safe publication** | 公開recordはすべてuntaintedでなければならず、公開Project membershipと全公開referenceはsafe published ID集合内に閉じなければならない。 |
| **R-SI-006 Stage separation** | bytes/hash取得済みFileのparse／post-acquisition read failureと、seal成立前のreader I/O failureを分離する。後者はsource-integrity terminalであり、partial-safeへ昇格させない。 |
| **R-SI-007 Independent accounting** | acquired count/bytes、proof discovered count、published＋proof-only model-record count、published entity countを別々に測定しなければならない。 |
| **R-SI-008 Budget non-bypass** | proof-only recordは`record=null`であってもmodel-record予算へ一件として算入する。taintedでないrecordをproof-onlyへ移してentity予算を回避することを禁止する。 |
| **R-SI-009 Selected target** | selected targetに必要なFile／Moduleがfailedまたはexcludedなら、完全proof base検証後にtyped target failureとし、partial-safe payloadを公開してはならない。 |
| **R-SI-010 Historical immutability** | v1/v2 schema、ID、algorithm、profile、KAT、既存Python／SQLAlchemy bytesを遡及変更しない。新しい意味は新しいadmission profileとpublic document versionで表す。 |

現行v2は、全frozen Project/Fileをmodel correspondenceへ含め、proof-only source metadataも例外にしない前提です。また、proof検証後にpublished＋proof-only model-record量を判定します。今回の変更は、この全inventory ownershipを弱めるのではなく、model correspondenceを安全投影へ分離するものです。attachments-bundle

---

# 3. Designへ差し込む契約

## 3.1 File集合の定義

次の集合を、IDで一意な集合として定義します。

- `F_acquired`: retained requestに含まれる全取得File
- `F_safe`: 公開modelに含まれるFile
- `F_failed`: 独立導出されたdirect failure dispositionを持つ取得File
- `F_excluded`: taint closureへ入ったがdirect failedではない取得File

必須関係は次です。

\[
F_{acquired}
=
F_{safe}
\;\dot{\cup}\;
F_{failed}
\;\dot{\cup}\;
F_{excluded}
\]

ここで`\dot{\cup}`は重複のない完全合併です。

さらに、

\[
F_{safe}
=
F_{acquired}
-
(F_{failed}\cup F_{excluded})
\]

とし、`failed`と`excluded`はchildが自由選択する値ではなく、root、mandatory seed、causal edge、taint closure、既存のdirect-failure規則から親validatorが導出します。

概念上の`published`は新しいproof wire fieldではありません。File IDがmodelに存在すればpublished、modelになく既存proofの`failed`にあればfailed、`excluded`にあればexcluded、と親が判定します。

## 3.2 discovered recordの親再構成

proof wireの既存`discovered_records`と`record=null`をそのまま使用します。新しいsource record fieldやdisposition enumは追加しません。現行response v2はv1 model/proof defsを参照しているため、この分離はwire shapeを変えずに表現できます。attachments-bundle

親validatorは各discovered rowを次のように解決します。

| discovered row | 解決規則 |
|---|---|
| Project ID | `record`は必ず`null`。同一requestのcanonical acquired Projectを使用する。 |
| File ID | `record`は必ず`null`。同一requestのcanonical acquired Fileを使用する。 |
| Project/FileでないID、`record=null` | 同じIDのmodel recordを使用する。modelに存在しなければ拒否する。 |
| Project/FileでないID、`record`あり | ID、kind、preimage、referenceを検証し、proof-only semantic recordとして使用する。 |
| Project/Fileで`record`あり | 値がrequestと一致していても`proof_source_owner`で拒否する。 |

解決後のproof discovered ID集合を`D`、公開model ID集合を`M`とすると、

\[
D = M \;\dot{\cup}\; (D-M)
\]

でなければなりません。`D-M`がproof-only model-record集合です。

同じIDがproof discoveryとmodelの両方に現れることは重複ではなく、discoveryとpublicationの対応です。ただし各collection内ではIDは一度だけでなければなりません。

## 3.3 File metadata equality

safe Fileについては、model Fileとrequest Fileの次の値を完全一致させます。

- `id`
- `project_id`
- `path`
- `role`
- `size_bytes`
- `sha256`
- その他v1 File recordに存在する全field

proof-only Fileについては、これらをproofから受け取りません。親requestから解決したcanonical recordを使用します。

したがって、次をすべて拒否します。

- inventory外File
- requestと異なるpath／role／size／hash
- 同じpathを別Projectへ移したFile
- synthetic bytes/hashに基づくFile
- proofの自由metadata
- safeであるFileの恣意的欠落

## 3.4 Projectの二つのview

Projectは、source inventory viewとsafe publication viewを分けます。

### Canonical acquired Project

proof内で解決するProjectはrequestと完全一致し、全取得`file_ids`を保持します。

### Safe Project projection

modelおよび公開文書のProjectは、同じcanonical Projectから次のように導出します。

- `id`、root、config path、compiler options、include/exclude、source roots、config digest等はrequestと完全一致
- `file_ids`だけを、元のcanonical順序を保ったまま`F_safe`へfilterする

すなわち、

\[
P_{public}.file\_ids
=
[f \in P_{acquired}.file\_ids \mid f \in F_{safe}]
\]

とします。

Project ID algorithm v1とproject config digest algorithmは変更しません。File membershipを安全投影しても、Projectのroot identityやconfig identityを新しいものとして再発行しません。

### 全File除外Project

一つのProjectの全Fileがproof-onlyになった場合でも、そのProjectは公開modelに一件残し、`file_ids=[]`とします。

このprofileではProject自体をfailed／excluded／taintedにすることを認めません。Project exclusionを将来必要とする場合は、同じprofileを拡張せず、別のadmission profileとして判断します。

### 複数Project

各Projectのpartitionを独立に検証します。

- Project AのfailureはProject Bのmembershipを書き換えない
- Fileは元のProjectから移動できない
- 全Projectが公開modelに一度ずつ存在する
- 一方が`file_ids=[]`でも他方のsafe membershipは維持する

現行public v2 schemaはProjectを少なくとも一件要求し、File配列自体は空を許す形です。新v3でもこの下限を維持できます。attachments-bundle

## 3.5 taint、causal、target、witness

検証対象となるfull resolved viewは、次で構成します。

1. requestから再構成した全Project/File
2. model内のsafe semantic record
3. proof内のproof-only semantic record
4. proof roots、causal edges、export observations、target completeness

そのfull viewに対して、現在のmandatory rootとcausal closureを適用します。

- `parse_file`／post-acquisition `read_file` rootは、同path Fileをmandatory seedから外さない
- submitted seed集合は独立導出集合と完全一致する
- causal edgeを省略してuntaintedへ見せることを認めない
- tainted recordは公開modelに存在できない
- untainted recordをproof-onlyへ移すことを認めない

### selected target

selected targetのFileまたは必要Moduleがproof-onlyなら、proof全体が正しいことを確認した後に`CSV-NEXT-TARGET-001`とし、payloadを公開しません。

無関係な不正record、欠落seed、dangling reference、偽metadataをtarget failureで隠してはなりません。

### Module owner

- 全Moduleのowner Fileは`F_acquired`に属するprogram Fileでなければならない
- 公開Moduleのowner Fileは`F_safe`に存在しなければならない
- proof-only Moduleは取得済みprogram Fileに結合できるが、公開referenceの対象にはできない
- non-program Fileはsafe Fileとして公開できるが、Module ownerにはできない

### export/source-graph witness

export observationとsource graph witnessはfull resolved inventoryに対して検証します。その後でsafe graphへ投影します。

公開member、relation、fact、export reference、Project membershipは、すべてpublished ID集合内に閉じなければなりません。safe subsetだけを見て「sourceが完全だった」と推論することは禁止します。source completenessは、completeなsource sealとrequest inventoryによってのみ成立します。

---

# 4. statusとfailure段階

| 状況 | 結果 |
|---|---|
| 全source acquisitionがcomplete、proof-only recordなし、target/export正常 | `complete` |
| acquisitionはcomplete、未選択Fileに検証済みfailure／taintがあり、safe modelが閉じる | `incomplete / partial_safe` |
| 全Fileがproof-only、target指定なし、Projectは空membershipで安全 | `incomplete / partial_safe` |
| 全Fileがproof-onlyでselected targetがその中にある | `CSV-NEXT-TARGET-001`、payloadなし |
| selected File／Moduleがfailedまたはexcluded | `CSV-NEXT-TARGET-001`、payloadなし |
| export witnessがunknown／invalid | 既存typed export unavailable、空成功へ変換しない |
| seal成立前のreader I/O failure | source-integrity terminal、semantic payloadなし |
| no failureでentityが0件 | `complete-empty`を認める |
| proof付きpartial-safeでentityが0件 | `partial_safe`を認めるが、completeへ昇格しない |
| model-record／entity limit超過 | 既存typed limit failure、proofの除外で回避しない |

ここで`read_file` semantic rootは「既にsealされたbytesを後段解析で読めなかった」事象です。bytes/hashが存在しないacquisition reader failureとは別です。

---

# 5. count、予算、public summary

## 5.1 独立測定値

| 測定 | 定義 | authority |
|---|---|---|
| `acquired_project_count` | request内のapplicable Project数 | source seal／request |
| `acquired_file_count` | `F_acquired`件数 | source seal／request |
| `acquired_file_bytes` | sealed bytesの実length合計 | source seal。request size/hashと独立照合 |
| `proof_discovered_record_count` | proof discovered IDのglobal unique件数 | validated proof |
| `published_model_record_count` | model内のglobal unique record件数 | safe model |
| `proof_only_model_record_count` | `D-M`の件数 | validated proof partition |
| `accounted_model_record_count` | published＋proof-only | 親validator |
| `published_entity_count` | 公開Module＋Component件数 | safe model |
| `public_summary` | 上記実測値の閉じた投影 | immutable v3 decision |

必須等式は次です。

\[
accounted\_model\_record\_count
=
published\_model\_record\_count
+
proof\_only\_model\_record\_count
=
proof\_discovered\_record\_count
\]

`record=null`のFile／Projectも一件として数えます。proof-onlyへ移せば予算から消える、という扱いは禁止します。

### 予算

- `max_model_records`は`accounted_model_record_count`へ適用する
- exactは受理、+1は既存typed `ModelRecordLimitError`または対応するclosed limit rejection
- `max_entities`は`published_entity_count`へ適用する
- ただしpublishedからの除外は独立taint導出と完全一致しなければならないため、budget目的の恣意除外は先にprotocol rejectionとなる
- 不正proofをlimit failureで隠さない

現行v2でもpublished＋proof-only model-record量をproof検証後に判定する順序が採用されています。新契約は、特に`record=null`のsource recordがこの件数から漏れないことを明文化します。attachments-bundle

## 5.2 public `source_inventory_summary`

新しいpublic semantic v3に、closed objectとして次を追加します。

| field | 内容 |
|---|---|
| `profile_id` | `next-source-inventory-safe-subset-v1` |
| `source_partition_fingerprint` | 後述のpartition digest |
| `acquired.projects` | acquired Project数 |
| `acquired.files` | acquired File数 |
| `acquired.file_bytes` | acquired bytes合計 |
| `safe.projects` | safe Project projection数 |
| `safe.files` | safe File数 |
| `proof_only.failed_files` | proof-only failed File数 |
| `proof_only.excluded_files` | proof-only excluded File数 |
| `records.proof_discovered` | proof discovered record数 |
| `records.published` | published model record数 |
| `records.proof_only` | proof-only model record数 |
| `records.accounted` | model-record budget測定値 |
| `published_entities.modules` | 公開Module数 |
| `published_entities.components` | 公開Component数 |
| `published_entities.total` | 上二つの合計 |

すべてnative nonnegative integerとし、float、bool coercion、caller supplied countを拒否します。proof-onlyのID、path、bytes、failure messageはsummaryへ公開しません。

---

# 6. hash preimageとfingerprint

## 6.1 新`source_partition_fingerprint/v1`

canonical preimageは次のfieldだけで構成します。

| field | 内容 |
|---|---|
| `profile_id` | `next-source-inventory-safe-subset-v1` |
| `request_id` | 同じretained request v2のID |
| `projects` | request canonical Project順の配列 |
| `projects[].project_id` | acquired Project ID |
| `projects[].safe_file_ids` | request file orderをfilterしたsafe IDs |
| `projects[].failed_file_ids` | 同じorderのfailed IDs |
| `projects[].excluded_file_ids` | 同じorderのexcluded IDs |

各Projectで三つのFile配列が取得`file_ids`の完全・非重複partitionでなければ、fingerprint計算以前に拒否します。

codecは既存semantic canonical codecを維持します。

- Unicode 15.0.0 NFC
- object key sort
- compact UTF-8 JSON
- float／NaN禁止
- 末尾LFなし
- SHA-256

path、size、hash、bytesをpreimageへ重複収録しません。`request_id`がそれらを含むrequest全体へ結合しているためです。これはrun固有partition identityであり、File ID、Project ID、semantic entity ID、toolchain attestationではありません。

## 6.2 compatibility v3

現行compatibility v2は、public semantic schemaとv1 algorithm/profileを分離した9-field preimageです。attachments-bundle

新compatibility v3では次だけを変更します。

- `schema = code-structure-viz.next-semantic-compatibility/v3`
- `semantic_schema = code-structure-viz.semantic/v3`
- `semantic_admission_profile_id = next-source-inventory-safe-subset-v1`を追加
- compatibility preimageを10 fieldsにする

以下は変更しません。

- `identity_versions`
- `algorithm_versions`
- `semantic_profile_id = next-trusted-profile-v1`
- Unicode profile
- runtime binding profile
- TypeScript 5.9.2 identity
- trusted type environment digestの意味
- portable toolchain fingerprintの意味

source、request、target、partition結果はcompatibilityへ入れません。

## 6.3 public run fingerprint v3

現行v2の13-key preimageは、source、plan、config、projects、targets、formats、stdout selector、limits、runtime/trusted metadataから構成されています。attachments-bundle

v3では、これに次の一fieldだけを追加します。

- `semantic_admission_profile_id`

したがって14-key preimageです。

`source_partition_fingerprint`、status、failure、entity countはrun intent identityではなく結果なので、run fingerprintへは入れません。

## 6.4 `model_digest`

algorithmは変更しません。safe model全体を現在のcanonical model digestでhashします。

旧all-File modelと新safe modelでは値が変わりますが、hash algorithm versionを変える理由にはしません。

---

# 7. 最小のversion／schema closure

新versionは一つの同期したpublic semantic世代に限定します。

| 対象 | 処置 |
|---|---|
| `next-adapter-request-v2` wire/schema/request ID/KAT | **維持** |
| `next-adapter-response-v2` wire/schema/raw-byte hash | **維持** |
| responseが参照するv1 model/proof defs | **shapeを維持** |
| Project/File/entity record defs v1 | **維持** |
| Project/File/entity ID algorithms v1 | **維持** |
| semantic algorithms/profile v1 | **維持** |
| trusted declaration profile | **維持** |
| `next-semantic-admission-v2.md` | **歴史的referenceとして保存**。意味を書き換えない |
| `next-semantic-admission-v3.md` | **新規**。本source-inventory profileのCore admission正本 |
| `next-semantic-v3.md` | **新規**。safe Project/Fileとpublic summaryの正本 |
| `schemas/next-semantic-v3.schema.json` | **新規**。v1 record defsをexact refし、summaryだけ追加 |
| `next-compatibility-v3.md`／schema | **新規**。10-field compatibility preimage |
| `schemas/semantic-v3.schema.json` | **新規**。Python／SQLAlchemy v1 branch＋exact Next-v3 branch |
| `source_partition_fingerprint/v1` | **新規** |
| public run fingerprint v3 | **新規14-key preimage** |
| publication artifact descriptor | versionless closed descriptorを**維持** |
| v1/v2 fixture/KAT/hash | **変更禁止** |
| v3 fixture/KAT | independent literalとして**新規追加** |

public v3を旧dispatcherや旧compatibilityへdowngradeするfallbackは作りません。逆に、旧Next-v2文書をv3として読み替えるfallbackも作りません。

公開publication／provenance／domain／root／stdout層で`semantic/v2`またはcompatibility v2をexact-refしている箇所は、repository-wide census後にv3 siblingまたはv3 exact refを追加します。ただし未実装層の空placeholder schemaを先に増やしません。

---

# 8. Current indexと実装状態の分離

`I/design.md`のCurrent contract indexには、少なくとも次の三列を置きます。

| contract | authority state | implementation/evidence state |
|---|---|---|
| admission/public v2 | `historical-reference` | `existing-v2-reference-pass` |
| admission/public v3 | `accepted-target` | 当初`not-implemented` |
| v3 spec | `accepted-target` | `spec-review-strict-pending`または`passed` |
| v3 reference | `accepted-target` | `reference-red`／`local-reference-pass` |
| A02 closure | `accepted-target` | `a02-local-pass`になるまで未認定 |
| A03 closure | `accepted-target` | `code-review-strict-pass`になるまで未認定 |

次の表記は禁止します。

- 単独の「pass」
- 旧v2 test passを新v3 spec passとする表記
- Spec Review StrictをA03 Code Review Strictとする表記
- Round NをCurrent authorityとする表記
- reference passをproduction passとする表記

現行v2自身も、既知corpusのreference契約であり、任意TS入力や実production compiler、public全chain、A03を認定しないと明記しています。attachments-bundle

---

# 9. 受入条件

## 正例

| ID | 入力 | 必須結果 |
|---|---|---|
| **P1** | 未選択File Aがparse failure、隣接File BのComponentは安全 | Aはproof-only、BとB由来recordだけ公開。Projectの公開`file_ids`はBのみ。`partial_safe` |
| **P2** | failure pathと同じ取得File自身 | Fileはmodelから除外され、proof rowは`record=null`。親requestからmetadataを完全再構成 |
| **P3** | selected Fileがfailed／excluded | 完全proof検証後、`CSV-NEXT-TARGET-001`。payloadなし |
| **P4** | 全Fileおよび派生semantic recordがtainted | 各Projectを`file_ids=[]`で保持。targetがなければ`partial_safe`、対象targetがあればtarget failure |
| **P5** | Project Aはpartial、Project Bは完全 | 両Projectを公開。Aだけmembershipをfilterし、Bは完全一致 |
| **P6** | acquisition正常、failureなし、Module／Component 0件 | `complete-empty`。空成功をsource failureの代用にしない |
| **P7** | safeなnon-program File | Fileは公開するがModule ownerを生成しない |
| **P8** | proof-only null recordを含むmodel-record exact/+1 | null source rowも一件として数え、exact受理、+1拒否 |
| **P9** | 同じsource seal、同じrequest、別fresh validator | 同じpartition、counts、fingerprint、statusを独立再導出 |

## 負例

| ID | 拒否対象 |
|---|---|
| **N1 欠落** | 取得Fileがmodelにもproof-onlyにも存在しない |
| **N2 重複** | 同じIDのdiscovered row重複、failed/excluded重複、複数collectionへの重複 |
| **N3 偽metadata** | model Fileのpath／role／size／hash差し替え、Project config差し替え |
| **N4 source injection** | Project/File discovered rowにnon-null `record`を付ける |
| **N5 under-taint** | mandatory File seed、causal edge、tainted IDの省略 |
| **N6 恣意除外** | untainted File／Module／Componentをmodelから外す |
| **N7 budget bypass** | proof-only null rowをcountしない、または安全recordをproofへ移してentity数を下げる |
| **N8 dangling** | private proofまたはpublic modelのreference先がdiscovered／published集合にない |
| **N9 public excluded reference** | Project.file_ids、Module owner、member、relation、fact、exportがproof-only IDを参照 |
| **N10 selected downgrade** | selected failureを`partial_safe`として公開 |
| **N11 false completeness** | safe subsetだけからsource completenessやexport completenessを主張 |
| **N12 reader prefix** | seal前の取得済みprefixをpartial-safe inventoryへ昇格 |
| **N13 cross-project** | Fileを別Projectへ移動、またはProject間でmembershipを共有 |
| **N14 Project omission** | 全File除外Projectをmodelから消す、Project自体をfailed/excludedにする |
| **N15 nonprogram owner** | non-program FileをModule ownerにする |

closed rejection reasonは、既存reasonを優先して次のように整理します。

- File metadata不一致: `file_correspondence`
- Project safe projection不一致: `project_correspondence`
- source record注入: `proof_source_owner`
- taint、causal、dangling: `model_proof`
- partition欠落／重複／disposition不一致: 新しい固定reason `source_inventory_partition`

public codeは通常`CSV-NEXT-PROTOCOL-001`のままとし、SOURCE failureへ読み替えません。

---

# 10. Planへ差し込む実装順序

## P-SI-01 仕様checkpoint

対象SHA `f8d5c41e...`を根拠に、次だけを変更します。

- 新accepted ADR
- Current Requirement
- Current Design
- Current Plan
- Current contract index
- v3契約文書とschema案
- hash preimage定義

candidate、v1/v2契約、product code、testsは変更しません。ASSET policyを混ぜません。

## P-SI-02 local specification checks

最低限、次を通します。

- SpecDock sync／validate
- Current pointer検証
- Markdown link検証
- JSON Schema meta-validation
- `$id`／`$ref` closure
- exact-ref census
- canonical preimage field census
- formatter／lint
- `git diff --check`
- v1/v2 fixtureおよびknown hashが無変更であること

一つでも失敗したら仕様checkpointをpassと呼びません。

## P-SI-03 fresh independent Spec Review Strict

exactな仕様commitを対象に、freshな`chatgpt-spec-review-strict`を実行します。

要求結果はpassです。指摘がある場合はR/D/Pへ戻り、同じreview結果を再利用しません。これはA03の代用ではありません。

## P-SI-04 最小reference TDD

次の順でRedを作り、最小実装します。

1. Project/File null source resolver
2. File exact partition
3. Project safe membership projection
4. full-inventory root／seed／causal／taint
5. arbitrary omission拒否
6. model-record accounting
7. selected target
8. Module owner
9. export/source-graph witness
10. immutable v3 decisionと独立validator

この段階ではpublic artifactやstderr診断へ先行しません。

## P-SI-05 public依存refs

Core referenceがgreenになった後、次を閉じます。

- public semantic v3
- compatibility v3
- dispatcher v3
- `source_partition_fingerprint/v1`
- 14-key run fingerprint v3
- public summary
- artifact bytes／descriptor
- publication、provenance、domain、root、stdoutの既存exact-ref消費者
- independent literal KAT

旧fixtureをproducerで自動再生成して追従させません。

## P-SI-06 元diagnostic／stderr unitへ復帰

source/proof矛盾がreferenceで解消された後にだけ、元のdiagnostic／stderr unitを再開します。

- protocol failureをSOURCEへ変更しない
- 64 KiB exact/+1規則を変更しない
- diagnostic encoderでCore不整合を隠さない
- source acquisition failureとsemantic parse/read failureを分離する

## P-SI-07 全A02 local gate

全A02 reference closure、schema、known vectors、negative tests、exact/+1を実行します。A02はreference-onlyです。

A02 base `710eb49a2a3143e31b8a91580700d16839d9070d`という履歴anchorを変更せず、今回の追加commitでその意味を再定義しません。attachments-bundle

## P-SI-08 累積A03

全A02とlocal gateの後、独立した累積Code Review Strictを実行します。

- A03は全A02 closureを含む
- Spec Review Strictを流用しない
- A03 fixed point `f4159066f3954454ad2f0c2701fa54bf1bc7bc4a`を履歴上維持する
- 新しい累積review対象commitを明示する
- 未解決指摘が一件でもあればA04へ進まない

## P-SI-09 A04／A05

A03 pass後にのみ、production受入れへ進みます。

- actual first-party TypeScript Compiler API
- fixed TypeScript 5.9.2
- explicit stable Node 22+
- macOS／Linux
- actual CLI/process/capture/interrupt
- target code/config/plugins/scripts/node_modulesをload／executeしないこと
- installed/offline package
- publication／manifest／stdout／stderr／exit
- A05 final closure

現行candidate自身も、source/proof整合、public全refs、A02、A03、actual TS/OS/package等を未完了として停止しています。attachments-bundle

---

# 11. 停止条件

以下のいずれかが生じたら、その段階で停止します。

- Project/File source recordにchild metadataが必要になる
- File mandatory seedを弱めないと正例が通らない
- untainted Fileの任意除外が必要になる
- Project自体をproof-onlyにする必要が出る
- v1 ID algorithmまたは旧record意味の変更が必要になる
- request／response wire v3が必要になる
- ASSET policy判断が混入する
- seal前prefixをpartial-safeへする必要が出る
- model-record予算からproof-only null rowが漏れる
- public referenceがproof-only IDを必要とする
- schema／exact-ref closureが未完了
- independent KATが作れない
- local check、Spec Review Strict、A02、A03のいずれかがnon-pass
- old v2 passしか証拠がない

その場合は実装guardを緩和せず、新しい人間判断へ戻します。

---

## 唯一、仕様commit前に固定すべき非意味論値

現行fixtureにはadapter version `0.1.0`がありますが、repository全体のrelease-version policyは今回の指定範囲から正本を取得していません。新producer behaviorを旧adapter versionのまま発行することは認めず、**旧all-File correspondence実装とは異なるadapter versionをtrusted asset／request KATへ固定する**ことを必須とします。

semanticな推奨はminor bumpですが、具体的なliteralはrepositoryのrelease policyに従ってP-SI-01で固定し、未確定のままSpec Review Strictへ出してはなりません。これはsource/proof ownershipに関する追加product判断ではなく、release identityの確定です。

---

この案は、採択済み方針をR/D/Pへ記録できる粒度まで具体化した**設計提案**です。まだrepositoryへ反映された正本、Spec Review Strict pass、reference test pass、A02/A03 pass、実装開始可能性の認定ではありません。
