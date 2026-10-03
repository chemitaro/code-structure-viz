# Next.js source inventory / safe subset admission v3

## Authorityと現在地

Issue #8 Current Requirement/Design/Planとaccepted ADR `20261002t001435z-adr-issue8-source-inventory-safe-subset.md`、A案補足ADR `20261002t041350z-adr-issue8-owner-closed-file-module-publication.md`に基づく**accepted target**です。2026-10-02のA案採択で、untainted File全件公開をowner-closed公開条件へ変更しました。source seamはSI-03、full CoreはSI-04 exact d6bbbcfでreference認定済み、public/schemaはSI-05候補で独立step review未認定、productionは未実装です。旧[admission v2](next-semantic-admission-v2.md)の通過証拠は旧referenceのままです。

新profileは`next-source-inventory-safe-subset-v1`です。typed transport candidate v2、同じcomplete `SourceAcquisitionSeal`、同じretained execution assetsを入力とし、nominal `ValidatedSemanticDecisionV3`または`RejectedSemanticDecisionV3`を生成します。これらはreference APIとして実在し、製品APIや実TypeScript実行の認定ではありません。free request/model/status/countや別exchangeのownerは認めません。

## 二つのviewとwire境界

- **取得view**: 同じ親requestの全Projectと、`content_base64`だけを除いた全File metadata。取得bytes/size/hash/roles/config/membershipをsource sealへ結合します。
- **公開view**: 安全と認定したFileとsemantic record、取得Projectから導出したsafe membershipです。取得viewの代わりにsource completenessを証明しません。
- request/responseのtransport v2とv1 model/proofの**構造定義だけ**を再利用します。旧admission certificateや旧runtime/public全objectへ変換しません。
- proof rowの`record`はoptional objectです。Project/File rowではこのkeyを**省略**します。`record:null`は旧wire schemaにも違反するため拒否します。`row.get("record") is None`という内部処理とwireのnull許可を混同しません。
- 新compiled producerのversionは`0.2.0`に固定し、header/全bytesのidentityを同じretained assets→request→controlに結合します。旧`0.1.0`のcorpusを新profileへ自動振り替えしません。product packageの`0.1.0.dev0`とは別のidentityです。profile選択は親が固定したadapter/version契約であり、childの自由なprofile宣言ではありません。

## 完全なdiscovered recordの解決

`D`をproof discoveryのglobal unique record IDs、`M`を公開model IDsとします。全collectionでkind/ID/preimage/order、一件一ID、一件一dispositionを検証します。

| row | 親validatorが解決するrecord |
| --- | --- |
| Project / File | `record`key無しを要求し、同じrequestから完全な取得recordを再構成。inventory外IDを拒否。 |
| その他、modelにも同じIDがある | `record`key無しを要求し、同じmodel recordをjoin。 |
| その他、modelにIDがない | 必須の`record`objectを検証し、proof-only recordとして保持。kind/ID、sourceと宣言owner、全referencesを検証。 |

`M ⊆ D`、`D = M ⊎ (D−M)`を検証します。全取得Project/Fileは必ずDへ一度含まれます。modelとdiscoveryの同IDは一件のpublication対応であり二重課金しません。proof payload注入、published recordのpayload二重記載、discovery重複を拒否します。

Projectの取得recordと公開recordは同じIDですがviewが異なります。proofのroot/causal/ownershipには取得recordを使い、public equalityだけは下記safe projectionと比較します。Fileは全metadataが両viewで一致します。別のsource observationを導入しません。

## Fileのexact partition

`F`はrequestの全取得File IDs、`T`はfull resolved view上で独立導出した**record-level** taint closureです。`F_program`は同じrequest rolesでprogramを持つFiles、`E_module`はfull discovered base、T、既存selection/unsupported witnessから親が独立導出した公開可能Modulesです。正常baseの`owner(f)`は同project/pathの正規Module一件です。submitted modelの有無やchild自由boolをE_moduleの根拠にしません。公開ModulesとE_moduleのexact equalityを検証します。

1. `F_source_safe = F − T`はsource情報の安全集合であり、公開集合ではありません。
2. `F_safe = (F_source_safe − F_program) ∪ {f ∈ F_source_safe ∩ F_program | owner(f) ∈ E_module}`。非program FileにはModule条件を加えません。全F_safeは公開必須で、任意のFile/Module同時省略は不正です。
3. `F_failed`は`F ∩ T`のうち、validated `parse_file`/`read_file` rootの`path_ref`に対応するdirect failed Fileです。reasonはその実root kindへ結合します。複数root kindが同じFileにある場合、canonical `TAINT_ORDER`（`parse_file`が`read_file`より先）の最初をfailed reasonとして一つだけ保持します。
4. `F_excluded = F − (F_safe ∪ F_failed)`。下表の優先順で各Fileのreasonを一つ独立導出します。
5. `F = F_safe ⊎ F_failed ⊎ F_excluded`。各集合のdiscovery、model、failed/excluded dispositionを完全一致させます。counts一致だけでは認定しません。
6. safe Fileの全fieldはrequest Fileから`content_base64`のみを除いたrecordと完全一致します。`roles`/`effective_role`、path、project、size/hashなどを自由補完しません。

| 優先順 / File条件 | dispositionとreason |
| --- | --- |
| direct validated parse/read root | `failed` / 上記root kind。 |
| File自身がT内、direct failedではない | `excluded / tainted`。 |
| File自身はT外、owner Moduleがfailure/taintで公開不能 | `excluded / failed`。ownerの検証済みfailure/root/taintで原因を立証。 |
| File自身はT外、owner Moduleが合法selection/unsupportedで公開不能 | ownerに独立検証した同じ`not_selected`/`target_excluded`/`unsupported`で`excluded`。failure/taintが併存すれば前の行を優先。 |
| source-safeでowner-closed条件成立 | `published`、reason無し。 |

既存response-v1のexcluded enumをwire-v2で使用し、新key/stateは追加しません。Module原因はfull proofと親certificateで保持/再導出します。Fileに偽taint、逆causal edge、`proof.failed`、直接read/parse failureを足しません。owner原因を立証できないuntainted File除外、Module discoveryの欠落/重複、両者の任意省略は拒否します。既存selected cardinality限定例外は完全proof baseを確認したtyped target unavailable専用で、available公開modelの一対一保証を緩める根拠にはしません。

File以外のsemantic recordに対する既存の`not_selected`、selection-only `target_excluded`、表現済みunsupported frontierは維持します。新profileはそれらを一律taintやprotocol failureへ変更しません。恣意的な除外と実selection witnessに基づく除外を区別し、budget目的の除外は既存規則どおり拒否します。

## Projectのsafe projection

全取得Projectをmodelへ一度ずつ残します。requestのProject順はroot-path順、modelのProject順はID順の既存規則です。

- `file_ids`以外の全field（`id`、root、config path/digest、compiler options、include/exclude、source roots）はrequestと完全一致。
- `model_project.file_ids`はrequest Projectの取得`file_ids`から`F_safe`だけをfilterしたsorted ID列。Project/Fileの双方向membershipとproject containmentを検証します。
- proof内のcanonical Projectは全取得`file_ids`を保持します。公開Projectはsafe membershipだけを持ちます。
- `identity_preimage`のProjectはroot、Fileはproject ID/pathのままです。`project_config_digest`はroot/source_roots/config_path/compiler_optionsのままで、membershipを含めません。ID/config digestのpreimageは変更しません。
- 全Fileが除外されたProjectも`file_ids=[]`で公開します。Project自体のtaint/failed/excludedはこのclosed profileでは認めません。現行mandatory rootとrecord referencesでもFile→Project逆taint edgeは導出しません。
- 複数Projectのmembershipを混ぜません。片方の空membershipは他方のsafe Filesを消す理由になりません。

## Full-inventory proofとlocality

完全取得Project/File、published semantic record、proof-only semantic recordからfull resolved viewを作り、同じseal-owned source graphへ結合します。公開subsetを入力にroot集合を縮めません。

- `parse_file`/`read_file` rootのmandatory seedsには同path File自身と全従属recordを含めます。submitted seedsは独立導出集合と完全一致。
- closed root/edge rule table、causal edges、typed taintsの固定点はv1のwire非依存意味を保持します。child edgesやtaint boolはauthorityではありません。File seed省略や下位algorithmへの例外注入をしません。
- 全Moduleは取得program Fileに対応。正常full baseの同project/path Module cardinalityを先に検証し、公開Module eligibilityを独立導出してからFile partitionを計算します。public Moduleはsafe Fileに対応し、available公開program Fileは正規Module一件を必ず持ちます。非program FileにModuleを生成しません。Module→Fileの逆taintは追加しません。
- private semantic referencesはDへ、public referencesはMへ閉じます。Projectの取得membershipはprivate view、公開membershipはpublic viewの規則で別に照合します。closed external/unresolved frontierの既存例外を維持します。
- export syntax census、resolution/re-export witness、selection/target witnessは同じfull inventory/frozen bytes/source graphから独立検証した後、safe graph/coverageへ投影します。proof-only recordのexportを公開成功に数えません。
- source file-rootのpartial-safeには同じsealからPythonが導出するlocality evidenceが必須です。既存`SourceFailureLedger.from_seal`のresolved/open graph、failure closure、target-taintの意味を維持し、free isolated boolや安全subsetだけでは認定しません。graphのopen edge等で切り分け不能なら既存`CSV-NEXT-SOURCE-003`/payload unavailableへ進みます。rootとledgerのpath/reason、tainted regionの整合も照合します。
- completeな構造/proof baseの確認前にtarget/export/予算failureへ逃がしません。既存selected cardinalityの限定例外（missing/component-only/byte-identical duplicate）は、その完全proof baseを検証してtyped target failureにする範囲だけ維持します。任意不正recordやFile partition欠落の例外ではありません。

## 判定順序と段階

1. nominal same-owner transport/source/assets/context、wire/echo/model digestを再検証。
2. 全取得source correspondence、full discovered view、record構造/ID/ownership/reference/canonical order、正常File/Module cardinalityを検証。selected cardinality限定例外も完全proof baseを確認。
3. mandatory root/causal/taint、full export/target/selection witness、locality evidenceを独立検証。公開可能Module集合を先に導出し、exact File partition/理由、Project projection、全public references、coverageを照合。typed target unavailable専用例外をavailable公開へ持ち込まない。
4. 立証済みtarget失敗は既存`CSV-NEXT-TARGET-001`、payload無し。proof不足をtarget失敗へ読み替えない。
5. 通常validated model/proofのactual wire model-record数を10000 exact/+1へ照合。不正proofをcount failureで隠さない。
6. export unavailableとsource非local unavailableを既存意味で処理。安全に切り分けた取得済みfile-rootと、既存の正規semantic failureは`partial_safe`。owner非公開のuntainted Fileも除外し、File→Module不整合を作らない。selection-only/表現済みunsupported frontierだけでpartial-safeへ変えず、既存reason/outcomeを維持。
7. available modelのModule＋Component実数をentity gateへ。partial-safeをcompleteへ昇格しない。

取得済みbytesを後段で解析する`parse_file`/`read_file` rootと、seal以前のreader失敗を区別します。通常reader I/Oは既存stage/codeによるrequest-independent unavailable、実integrity driftだけrun-level fatalです。package READ special case、config/extends/source failure分類、未観測suffix、target proof無し、complete-only seal、新ASSET未採択の境界を維持します。

全Fileがfailure/taintまたはowner Module原因で合法的にproof-onlyとなる場合も、正規failureがありtarget無しかつlocality成立なら空membership Projectと`partial_safe`を公開できます。独立safe targetは無関係なModule/Fileの非公開でunavailableにしません。locality不成立はSOURCE-003、selected failing targetはTARGET-001です。failure無しでentities0のcomplete-empty、合法selection-only exclusionは別正例です。countsだけでoutcomeを捏造しません。

## Countとimmutable decision

| 実測値 | 定義 / 予算 |
| --- | --- |
| acquired Projects / Files / bytes | 同じrequest全inventoryとseal bytes。source file/decoded byte capsは全取得分に適用。`SourceView.file_count`とrequest applicable File数を混同しない。 |
| proof discovered | Dの件数（正常unique base）。coverageのdiscoveredと同一。 |
| published model records | model七collectionの実array items合計。 |
| proof-only model records | modelにないdiscovered rowsの実件数。`record`省略source rowも一件。 |
| accounted model records | published＋proof-only。通常unique baseではD件数と一致。既存限定duplicate-target branchを全体のunique count例外へ広げない。 |
| published entities | safe modelのModules＋Components。既存entity gate。selection/taint無しの恣意除外で減らせない。 |

限度値、raw/aggregate/collection caps、count優先順を変えません。producer cacheの一致は実証ではなく、独立validatorが同じownerの実record/bytesから再導出します。v3 Core ownerは同じcandidate/source/assets、検証済みfull proof・partition・gate・compatibility・measurementをimmutableに保持します。Core failureのraw response破棄/receipt境界は旧runtimeから維持し、public producerはavailable ownerのみ受けます。

## Partition fingerprint

`SHA256(CJ15(preimage))`。CJ15はpinned Unicode15 NFC、key sort、compact UTF-8、末尾LF無し。preimageは次のexact三keysです。

| key | 値 |
| --- | --- |
| `profile_id` | `next-source-inventory-safe-subset-v1` |
| `request_id` | 同じretained request v2のID |
| `projects` | request Projectのroot-path順。各rowは`project_id`、`safe_file_ids`、`failed_file_ids`、`excluded_file_ids`のexact四keys。各IDsは元Project.file_idsからfilterしたsorted列。 |

各rowの三File集合は取得membershipの完全partitionです。request IDがbytes/config/membershipへbindするため、path/hashを重複preimageへ追加しません。これは結果identityであり、entity ID、run intent identity、compatibility、actual-image attestationではありません。

## Planned acceptance matrix

| ID | 正例 / 必須結果 |
| --- | --- |
| SI-P01 | 正規seal/transport、未選択Aのparse root、localityで独立のB。A File自身と全tainted recordはproof-only、Bのsafe componentとsafe control/context Filesを公開、Project membershipをfilter、partial-safe。 |
| SI-P02 | post-acquisition read rootでも同じFile seed/partition保証。実acquisition read失敗の正例として流用しない。 |
| SI-P03 | selected Aが失敗：完全proof後TARGET-001、no payload。safe subset公開へ降格しない。 |
| SI-P04 | 全FileがFile taintまたはowner Module原因で合法proof-only、正規failure/locality成立/target無し：Project空membership、partial-safe。複数Projectでは安全側を維持。locality不能はSOURCE-003。 |
| SI-P05 | failure無しcomplete-empty、安全な非program File、既存selection-only exclusion / unsupported frontierのcomplete意味を維持。合法Module除外時もFile/Project公開条件を一致。 |
| SI-P06 | 同じsource/request/proofの独立再検証で同じpartition/count/hash。実model-record10000/+1にproof-only source rowsを含める。 |
| SI-P07 | module_relation / export_binding / boundary_derivationでFileはT外、ModuleはT内。両者proof-only、Fileはexcluded/failedで偽taint無し、独立safe targetは公開、全件予算/refs/summary/hash一致。 |

SI-N01欠落、N02重複/複数disposition、N03偽File/Project metadata、N04source `record`注入/null、N05mandatory seed/causal/taint省略、N06公開可能File/Moduleの任意除外、N07予算迂回、N08private dangling/public proof-only reference、N09target失敗のpartial-safe降格、N10safe subsetによるfalse completeness、N11early reader prefix昇格、N12cross-project/Project欠落、N13非program Module、N14locality偽造/open dependency見落とし、N15owner原因偽造/欠落・Module欠落/重複隠蔽・偽File taint/direct failureを個別に拒否します。既存の合法selection-only exclusionをN06へ誤分類しません。

rejection labelsは`file_correspondence`、`project_correspondence`、`proof_source_owner`、`proof_module_owner`、`proof_references`、`model_proof`と新fixed `source_inventory_partition`。payload invariant rejectionのpublic codeは既存PROTOCOL-001です。立証済みsemantic/source/target失敗とは別で、diagnostic encoderはCore rejectionをSOURCEに読み替えません。
