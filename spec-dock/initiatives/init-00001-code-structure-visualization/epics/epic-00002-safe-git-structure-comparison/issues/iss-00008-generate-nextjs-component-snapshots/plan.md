---
種別: 実装計画書（Issue）
ID: "iss-00008"
タイトル: "Generate Next.js Component Snapshots"
関連GitHub: ["#8"]
package_sequence_key: "ISSUE-05"
状態: "draft"
最終更新: "2026-09-02"
依存: ["requirement.md", "design.md"]
親: ["epic-00002", "init-00001"]
---

# iss-00008 Generate Next.js Component Snapshots — 実装計画

詳細: [Issue Plan Guide](../../../../../../docs/authoring/issue-plan.md)

## Current v1 normative authority

この節が唯一の現在の実装順序・受入正本です。後続の`Round N`節はhistorical evidence（非normative）として保存し、実装計画を上書きしません。新たなmaterial requirement/security/platform判断は追加せず、採択済みのIssue #8契約と実行可能なR23 registryだけをmaterializeします。

```text
package bytes
  -> applicability matrix (Node permission)
  -> frozen control closure + source graph seal
  -> one provenance union + validated request/response
  -> semantic decision
  -> final publication decision (bytes and one measurement)
  -> domain/root/manifest/stdout/stderr/exit
```

実装前の順序は、(1) package-only preflight、(2) project-relative controlsとJSONC/local-extends/membership、(3) source graph resolved/open/privacy、(4) process policy/observation、(5) provenance stage matrix、(6) semantic and publication projection、(7) executable coverage registryです。各段階はpositive/negative vector、schema、reference validatorを同時に追加し、caller-supplied graph/paths/roles/status/bytesを拒否します。`files`/`include`の空配列も明示値として扱い、defaultsは双方が無いときだけです。

受入では、contract focused test、all contract/full pytest、mypy、ruff、SpecDock、pinned PlantUMLを順に実行します。Windows/OS process-level/将来wheel・s​​distはproductionまたは別migrationの計画契約として記録しますが、現時点で実測済みとは主張しません。fresh current-SHA Strictが`P0=0 / P1=0 / review_status=pass`になるまでproduction実装を開始せず、readinessを未確認のまま維持します。

## Planning Level

- **selected level: `strict`**
- 理由: cross-runtime versioned protocol、optional dependency、TypeScript semantic boundary、static-analysis security contract を導入し、compatibility failure の回復が難しいため strict を選ぶ。
- risk factor: public CLI/schema、static-analysis safety、Artifact integrity、adapter compatibility、誤比較時の広い説明影響。
- `critical` ではない理由: target repository と persistent user data を変更せず、release/commit 単位で戻せる設計である。
- 再評価条件: secret/PII exposure、target mutation、不可逆 data loss、incident response が必要な rollout を追加する場合。

### Round 19 remediation plan

Round 19 Strict content reviewの固定点は SHA `0b80bff7706ca4bec770dbdf25620fbb5d2ecc2d`、CI
`33557963556`（7/7 success）、判定 `P0=0 / P1=5 / P2=1 / fail /
implementation_ready=no` である。session `required-strict-github-connector-verificati-687` の
transcript SHA-256は `a64f04b5948db0df3106803c659cc27c6ee8edd5abf300afa15e81d64691e351` とする。
Round18 artifactは履歴として保持し、Round19 artifactにfinding、修復、executable evidence、検証結果を追記する。
fresh current-SHA Strictはpending、readinessは未確認、production implementationは未着手である。

実装前の作業順と受入証拠は次のとおりである。

1. **source seal:** `SourceDiscoveryIntent`をroots/control candidates/fixed rulesに限定し、trusted
   frozen inventoryからknown control closureを先に観測する。duplicate-key rejecting JSONC、single local
   extends、include/exclude/files/source_roots、effective role、final membershipをseal内で導出し、request
   filesとのset/digest/sizeを照合する。malformed control、revision drift、duplicate/post-seal read、callerの
   derived paths/roles/plansはfail-closedとする。`seal_source_acquisition`が一つのplan/view sealを返す。
   Evidence: `test_source_seal_derives_plan_and_view_from_one_intent_and_rejects_drift`、
   `test_round18_source_seal_rejects_caller_membership_and_typed_drift`。
2. **source result union:** 一件のprogram/context read failureを `CompleteSourceSeal | PartialSourceSeal |
   SourceAcquisitionUnavailable | SourceIntegrityFatal` に分類する。`PartialSourceSeal`だけが同一sealに結び付いた
   `SourceFailureLedger`とsafe file setを持ち、ledgerはraw graphからlocalityとtarget taintを再計算する。
   Evidence: `test_round19_partial_source_result_preserves_safe_subset_and_ledger_identity`、
   `test_round19_source_acquisition_union_is_typed_and_fail_closed`。
3. **request/response authority:** private requestはcomposition-based `ValidatedAdapterRequest`としてcanonical
   id/bytes、file base64/size/digest、limitsをresponse boundaryで再検証する。request起点のsource seal再構築を
   行わず、request前に観測済みのseal identityとfile setを一致させる。validated response raw bytes/SHAをdecisionへ
   sealし、独立のcandidate/status/diagnostic bytesを受け取らない。Evidence: existing raw-byte boundary tests and
   the partial-safe propagation test.
4. **publication:** semantic decisionからsummary/root manifest/artifact/typed unavailable candidatesを一度だけ
  生成し、capture→stderr→selected-copyの測定を`PublicationBoundaryDecision`へsealする。success candidate超過時は
   persisted failure-manifest descriptorを一度生成し、再copyしない。exactは全量、+1はpartial bytesなしのclosed
   unavailable。空stdoutはusage errorのみとし、target failure reasonをtarget selector以外へ出さない。
   Evidence: `test_round16_final_publication_decision_seals_capture_stderr_and_selected_copy`、
   `test_round18_publication_projections_return_sealed_candidate_bytes`。
5. **process identity:** `next-process-launch-observation-v1`のfixture/production unionを検証する。productionは
   darwin/linuxを対象にし、OS-native file identity、verified handle、hash/version、actual spawn primitive、
   post-spawn equality、FD lifecycle、process group、TOCTOU pointを必須にする。referenceではhostを操作せず、
   faithful harnessをprocess-level acceptanceと主張しない。Evidence: `test_round19_process_observation_is_fixture_or_supported_os_production`。
6. **provenance and schema:** `next-provenance-v1`のstage/code/observed prefixをclosed oneOfにし、normal/
   request-independent `next-config` branch、run-context budget/selector correlation、catalog code pairを同期する。
   path-only rowsはNFC UTF-8 bytes、object rowsはcanonical JSON bytesで、quote inverseをrejectする。
   Evidence: `test_round19_stage_provenance_reference_rejects_stage_code_and_prefix_mutations`、
   `test_round19_next_config_discriminator_is_required_and_disjoint`、
   `test_round19_target_path_order_uses_nfc_utf8_bytes_not_json_escaping`。
7. **document and gate:** Requirement/Design/Plan、`docs/contracts/next-*`、関連schema、fixture、human HTML、
   durable Round19 artifactを同じ語彙へ同期する。focused Next tests、contracts/full pytest、mypy、ruff、SpecDock、
   pinned PlantUML、`git diff --check`、`src` diff empty、`node_modules` absentを記録する。これらはpre-implementation
   evidenceであり、fresh Strict passやproduct implementationを意味しない。

#### Round 19 criterion → executable evidence

| criterion | reference evidence |
| --- | --- |
| R19-P1-01 source seal and control closure | `test_source_seal_derives_plan_and_view_from_one_intent_and_rejects_drift`; `test_round18_source_seal_rejects_caller_membership_and_typed_drift` |
| R19-P1-02 ledger seal-owned locality | `test_round18_source_failure_ledger_recomputes_reachability`; `test_round19_partial_source_result_preserves_safe_subset_and_ledger_identity` |
| R19-P1-03 opaque response/publication authority | `test_round18_validated_response_raw_bytes_are_opaque_authority`; `test_round18_publication_projections_return_sealed_candidate_bytes` |
| R19-P1-04 process observation identity | `test_round19_process_observation_is_fixture_or_supported_os_production`; `test_round18_process_descriptor_requires_os_identity_and_spawn_binding` |
| R19-P1-05 stage-dependent provenance | `test_round19_stage_provenance_reference_rejects_stage_code_and_prefix_mutations`; `test_round19_next_config_discriminator_is_required_and_disjoint` |
| R19-P2-01 path byte ordering | `test_round19_target_path_order_uses_nfc_utf8_bytes_not_json_escaping`; `test_round18_path_only_order_is_nfc_utf8_and_object_rows_are_canonical_json` |
| R19 partial-safe follow-up | `test_round19_source_acquisition_union_is_typed_and_fail_closed`; `test_round19_partial_source_result_preserves_safe_subset_and_ledger_identity` |

Production implementation remains outside this plan. Do not start I05-PLAN-002 or claim readiness until a fresh
current-SHA Strict review returns `P0=0 / P1=0 / review_status=pass`.

## 目標

coding agent が first-party TypeScript adapter を通じ、Next.js repository の module、exported component、props、static relation、client boundary を JSON と PlantUML で取得できる。

completion は file/technical layer の完成ではなく、次の observable chain で判定する。

```text
CLI request -> safe source acquisition -> domain semantic analysis
  -> versioned semantic JSON + domain PlantUML -> diagnostic/manifest
  -> acceptance command and exit evidence
```

## 順序・依存

- declared dependency: ISSUE-01。
- execution order: I05-PLAN-000 → 001 → 008 → 002 → 003 → 005 → 004 → 007 → 006。canonical adoptionとmachine-checkable contractをmaterializeし、そのexact commitのStrict pass後にproduction実装へ進む。
- TypeScript fixtures、protocol golden、renderer golden、security trapsはcontract固定後に並行できる。
- stop condition: adapter protocol、static semantics、not_applicable/incomplete、entity budget、optional Node、determinismが成立するまでNext diffへ進まない。

### Round 8 review state

ChatGPT Use Strict Round 8 は `review_status: fail`、P0=0、P1=4、P2=0 だった。
実装開始前に、root manifestのNext path-only projection、Python-owned frozen export
census、response検証後の独立EntityBudgetGate、program-only semantic ownershipを
data-only contractへ反映する。修復後のfresh exact-SHA Strictは未実行・未通過で、
readinessは未確定、production adapter/CLIは未着手のままとする。

### Round 9 review state and remediation gate

ChatGPT Use Strict Round 9 は `review_status: fail`、P0=0、P1=7、P2=1 だった。
fresh exact-SHA Strictは未実行・未通過で、readinessは未確定、production adapter/CLIは
未着手である。以下のdata-only契約修復を実装前に完了し、focused/full test、schema/
SpecDock/HTML検証、clean exact-SHA Strict passを経て初めてproduction実装へ進む。

| Round 9 finding | 固定する実装前証拠 |
| --- | --- |
| P1-1 export grammar | Python frozen tokenizer/censusがlocal list、default alias/declaration/expression、multiline/comments、NFC Unicode、CRLF/BOM、exact byte spanをpositive/omission/mutationで閉包する。 |
| P1-2 re-export witness | source specifier/imported name/source Module/expanded name/target declarationを独立graph witnessへ記録し、alias/star/cycle/conflictをPython再計算してNode/public/countと比較する。 |
| P1-3 budget composition | complete/partial_safe under budgetを保持し、overrunのみpayload_unavailable。override passでも元outcomeを保持し、response→domain→manifest/stdoutをvector化する。 |
| P1-4 stderr boundary | capture boundとpublic diagnostic boundを別名・別計数にし、limit/+1、process-group termination、raw/partial disposal、stable code、manifest projectionをvector化する。 |
| P1-5 array boundary | total array aggregate、individual array、semantic collectionを分離し、individual内でもaggregate 100001をpre-materializationで拒否する。 |
| P1-6 source plan | closed SourceAcquisitionPlan/v1 schema/descriptorを追加し、control/extends/file roles/projects/suffixes/exclusions/limits/trusted digestを全hash、known-answer mutationを持つ。 |
| P1-7 ordering / P2-1 target prose | input/config/source-planはNFC UTF-8 root-path、semantic recordsはrecord-ID order。public component selectorは削除し、pathから解決したinternal Component seedだけを扱う。 |

### Round 10 review state and two-pass remediation

ChatGPT Use Strict Round 10 は `review_status: fail`、P0=0、P1=8、P2=0 だった。
証拠と8件の要求は `20260901t000000z-disc-strict-spec-review-round-10.md` に固定する。
fresh exact-SHA Strictは未実行・未通過、readinessは未確定、production adapter/CLIは未着手
である。Pass Aではproject surface order、outcome-preserving EntityBudgetGate、canonical
path、File→Module完全性を実装前validator/schema/testへ反映した。Pass Bではclosed export
grammar、独立re-export witness、public diagnostic stderr、bounded response decoderを
validator/schema/fixture/testへ反映した。focused/full quality gates後にfresh Strictへ
戻すが、現時点ではfresh exact-SHA Strict未実行・未通過、readiness未確定である。

### Round 11 review state and Pass C remediation

Round 11 は exact SHA `75ac0e0b34347b825c0bec2e6fbf9ff2068d9a1b`、CI run
`33422630936`（7/7 success）に対し `review_status: fail`、P0=0、P1=8、P2=0だった。証拠は
`20260901t010000z-disc-strict-spec-review-round-11.md`へ固定する。Pass Cでは、逆順二projectの
full-chain vector、explicit `NextRunContext`のresponse→gate→domain→root/stdout propagation、
shared UTF-8/NFC path helper、File→Module typed target failureをdata-only contractへ反映した。
Pass Dでは、module-level JSX lexical scanner、raw declaration/edgeからの独立re-export witness、
public diagnostic stderrのbounded JSONL gate、raw response bytes専用のbounded decoderを
data-only contractへ追加反映した。fresh exact-SHA Strict、readiness確認は未実施であり、
production adapter/CLIは未着手のままとする。

Pass Cの実行項目:

- immutable project ID/root correspondenceとsurfaceごとのroot-path/record-ID orderを独立検証し、
  request、response、domain、root manifest、fingerprintの各mutationをrejectする。
- requested formats、budget requested/resolved/source、stdout selectorを一つのcontextで受け渡し、
  requested formatを暗黙のFORMAT_ORDERから補わず、formatsとselectorをfingerprintへ含める。
- `next-path-v1`を全path-bearing surfaceの補助schema refとして使い、helperでNFC/UTF-8 bytes、
  root `.`文脈、4095/4096/4097 boundaryを検証する。
- file/directory targetのmissing、duplicate、component-onlyをpre-model typed failureにし、
  `CSV-NEXT-TARGET-001`、payload unavailable、no artifacts、manifest/stdout、exit 3を通す。

Pass Dの実行項目:

- JSXをmodule-level lexical grammarとして走査し、self-closing/fragment/nested same-name、属性式内の
  string/template/comment/regex、property/literal/comment内の偽`export`を除外する。async/generic/type
  span、semicolon/ASI、BOM/CRLF、NFC、exact UTF-8 byte spanをsource censusとgoldenで固定する。
- raw declarations/edgesからre-exportを独立再計算し、double alias、star 0..N/default exclusion、
  cycle/conflict/missing sourceをoriginal/exported name付きwitnessへ記録する。starのcomponent行を
  public bindingへ、value/type行をcoverageへ投影し、response proofのmutationを拒否する。
- public stderrはcanonical JSONLを全行UTF-8 encodeしてからlimit判定し、limit+1をpartial write 0、
  `CSV-NEXT-LIMIT-003`、manifest-onlyへ投影する。raw response bytesはbounded decoder一つを入口とし、
  duplicate key、depth、decoded string、per-array、aggregateをmaterialization前に数える。

Pass D実装後もRound 11の `review_status: fail`（P0=0、P1=8、P2=0）は履歴として保持する。
fresh exact-SHA Strictは未実施・未通過で、readinessは未確定、production adapter/CLIは未着手である。

### Round 12 remediation gate

ChatGPT Use Strict Round 12 は exact SHA `48266f813353a7fd78e4e15d72ff6d33c4142827`、CI run
`33435802167`（7/7 success）で `review_status: fail`、P0=0、P1=8、P2=0だった。証拠は
`artifacts/20260901t020000z-disc-strict-spec-review-round-12.md` に固定し、failをpassへ書き換えない。
受理済みのdata-only修復は次の実装前gateを満たす必要があるが、fresh exact-SHA Strictは未実行・
未通過、readinessは未確定、production adapter/CLIは未着手である。

1. inverse-order二projectを同じvalidated modelでresponseからdomain、publication、root manifest、
   fingerprintまで通し、project ID/root correspondence、surface-specific order、counts/budget/coverageと
   publication digestのmutationを拒否する。
2. request-owned `NextRunContext`（selector `null|manifest|next:semantic-json|next:plantuml`）をprivate
   request ID preimageへ含め、response/gate/domain/root/stdoutへexact echoする。resolved budgetやselectorの
   fallback・provenance inference・gate duplicate argumentを残さない。
3. raw-byte bounded decoder、closed response schema、shared path helper、安全な基礎検証、typed target
   precedenceを一つの実行順序へ固定する。wrong schema/extra/unsafe compound mutationはtyped target
   failureへ落とさない。
4. Unicode JSX lexical states、exported-name-only re-export lookup、owner/physical target witness、
   component non-null target、double-alias/star binding+coverage、cycle/conflict unavailable vector、
   shared `#` path rejection、file/directoryのFile→Module typed failure三分類をschema・reference testへ
   反映する。`missing`は選択program FileがあるがModuleも期待identityを参照するComponentもない状態、
   `component_only`はModuleがなくComponentだけが期待identityを参照する状態、`duplicate`は同じ選択Fileに
   byte-identicalなModule行が複数ある状態である。`duplicate`の許可は選択対象の同一行だけに限定し、三分類を
   response→diagnostic→domain→root manifest→stdout unavailable→exit 3まで通す。

Pass Bの実行条件:

- scannerはmodule-level深さ0だけを対象に、async declaration、generic/type span、semicolon
  とASI終端、JSX/property/regex/template/string/comment false positive除外、NFC/CRLF/BOM、
  exact byte spanを閉じたfixtureから再計算する。
- raw export declarations/edgesから独立graphを再計算し、explicit alias、star 0..N/default
  exclusion、cycle/conflictをmain response witnessへ統合する。public ExportBindingから
  witnessを導出せず、component resolution/count mutationも拒否する。
- public stderrはcanonical diagnostic JSONLのUTF-8 encoded bytesをwrite前に一括測定し、
  limitは受理、+1は0 bytes出力・固定`CSV-NEXT-LIMIT-003`・manifest-onlyとする。adapter
  captureとのcounter混同を許さない。
- bounded decoderは実response bytesをobject化せず、duplicate key、nesting/string、個別
  array、aggregate counterをincrementalに数え、aggregate 100001をpre-materializationで
  拒否する。response envelope validationの前段で成功経路にも適用する。

Pass Aの実行条件:

- request/modelのprojectはID/root対応を比較し、各surfaceのroot-path orderまたはrecord-ID
  orderをsubmitted順のまま別々に検証する。root manifestのproject listとfingerprintへ
  逆順二project fixtureを通す。
- response proofからpre-budget outcomeを一意に導出し、`EntityBudgetGate`は暗黙の
  `complete`を持たない。under budgetのcomplete/partial_safeは保持し、overrunだけを
  `payload_unavailable`へ変換し、requested formatのartifactだけを選ぶ。
- `next-path-v1`の非root値はNFC UTF-8 bytesで1--4096、root sentinel `.`はroot文脈だけ
  とする。empty/`.`/`..` segment、trailing slash、control、backslash、NFC collisionを
  全Next surfaceで拒否する。
- modelとtarget resolverは、選択されたprogram Fileすべてに同一project/pathのModuleが
  exactly oneあることを要求する。missing/duplicate/component-onlyは全domain unavailable
  の投影へ進める。

この表の全行がdata-only validator/fixtures/docs/schemaへ反映されるまで、Next
adapter/CLIの`src/**`実装を開始しない。

| Plan ID | implementation/verification step | Design trace |
| --- | --- | --- |
### Round 13 review state and remediation gate

Round 13 Strict は対象SHA `991516bf730f4f2ddb3d15067702dcfae95ec6b1`、CI run `33446911714`
（7/7 success）で `review_status: fail`、P0=0、P1=9、P2=1だった。証拠は
`artifacts/20260901t040000z-disc-strict-spec-review-round-13.md` に固定し、failをpassへ書き換えない。
data-only契約のfocused/full gateが通っても、fresh exact-SHA Strictは未実行・未通過、readinessは
未確定、production adapter/CLIは未着手である。

Round 13のproduction実装前チェックリスト:

1. full semantic六collection/PlantUML publicationを一つのimmutable validated decisionから生成し、
   schema-validなorder/payload mutation、artifact hash、root descriptor mutationを拒否する。
2. proof-base（IDs/refs/order、causal edge、export-owner join、target completeness）をtyped target
   routingより先に検証し、`missing`/`component_only`/`duplicate`をresponse→diagnostic→domain→root→
   stdoutへ保持する。
3. double alias、empty/multi star（default除外）、cycle/conflictを別whole-run vectorsとして
   `CSV-NEXT-EXPORT-001`、unavailable、exit 3まで通す。re-export joinは全observation/raw edgeを
   original/exported name、syntax identity、byte span込みで一対一消費する。
4. IdentifierName表をUnicode 15.0.0へ固定し、Other_ID_Start/ContinueとU+00B7を含め、profile version
   をcompatibility/run-fingerprint preimageへ含める。shared root-or-path schemaは全適用面でroot `.`を
   許可し、private adapter response `max_adapter_response_bytes`はdecode/materialize前に16 MiB境界を検査する。
   `max_stdout_bytes`は公開selected stdoutのv1互換aliasとしてのみ扱う。
5. P2-1のHTML重複項目を除き、artifactへ対象SHA、CI、P0/P1/P2 fail counts、fresh Strict pending/readiness
   unconfirmed/product absentを記録する。これらを満たしfresh StrictがP0/P1=0になるまで I05-PLAN-002以降の
   production implementationへ進まない。

### Round 14 remediation gate

Round 14は、初回connector検証失敗と成功した再試行を別証跡として
`artifacts/20260901t031000z-disc-strict-spec-review-round-14.md`へ保存する。成功した再試行の固定点は
SHA `cf5da416e25e76068ed99caf0d450d0e2d5b28df`、CI run `33457932686`（7/7 success）であり、判定は
`review_status: fail; p0_count: 0; p1_count: 5; p2_count: 2; implementation_ready: no`である。
fresh current-SHA Strictはpending/readiness unconfirmed、production implementation absentと記録する。

実装開始前に次の順序で契約を閉じる。

1. `NextRunDecision`（validated response / pre-response failure / not applicable）のclosed unionを定義し、
   全projectionをdecision-onlyにする。P1-1のnode/protocol/pre-response limit parameterized E2Eを追加する。
2. proof reason semantics、Unicode 15.0 checked-in table、`max_model_records=10,000`を含む
   model/aggregate/raw reachable limits、bounded child stdout captureをschema・reference validator・
   negative/positive testへ反映する（P1-2〜P1-5）。`proof.discovered_records`は構造上限20,000とし、
   9,999 compact context Files + 1 Projectのschema-valid responseをexact boundary、10,001件を
   schema-valid model-limit boundaryとして実wireで検証する。
3. canonical `target_failures` cardinality/branch、source intent→single-read→atomic sealを反映する（P2-1〜P2-2）。
4. focused/full tests、mypy、ruff、SpecDock、HTML PlantUML、TS trusted gateを実行し、Round14 artifactへ
   command/resultとcriterion→test mapを追記する。fresh exact-current-SHA StrictがP0/P1=0を返すまで
   I05-PLAN-002以降を開始しない。

| I05-PLAN-000 | implementation判断を残さないfield-level identity/source/protocol/type/taint/public schema/config/package contractをcanonical Designへ固定する。 | I05-DES-001〜007 |
| I05-PLAN-001 | identity/export、project/target、protocol、type IR、relations/boundary、outcome/publication、TrustedTypeEnvironment、packaging/regressionのI05-AT-001〜011 fixtures/schemaを先に固定する。 | I05-DES-001〜007 |
| I05-PLAN-008 | actual schema/docs/catalog/golden/mutation fixtureを含むclean pushed exact SHAでChatGPT Use Strictを再実行し、P0/P1=0をproduction implementation gateとする。 | I05-DES-001〜007 |
| I05-PLAN-002 | domain-owned SourceAcquisitionPlan、Next config/project/target parser、frozen-bytes request、hardened one-shot Node boundaryを実装する。 | I05-DES-002, I05-DES-006 |
| I05-PLAN-003 | declaration identity、bindings、Component recognition、closed props IR、two-plane relations、positive-evidence boundaryを実装する。 | I05-DES-003 |
| I05-PLAN-004 | untrusted response strict validation/ID再計算、semantic JSON、PlantUML、manifest、closed registry/publicationを接続する。 | I05-DES-004 |
| I05-PLAN-005 | intentional unknown、partial_safe、payload_unavailable、explicit target all-or-nothing、entity/transport/type limitsをoutcomeへ接続する。 | I05-DES-005 |
| I05-PLAN-006 | non-execution/redaction、determinism、Node optionality、offline bundle、lock/license、resource cap、CI、full regressionを完了する。 | I05-DES-006 |
| I05-PLAN-007 | parserに部分実装済みのNext stdout syntaxをdomain/format/schema/stream pathと一貫して有効化し、exact-byte copy、unavailable result、no-selector summary、usage no-publicationを検証する。 | I05-DES-007 |

## 実装step

### I05-PLAN-000 canonical adoption

- `20260831t024052z-research-nextjs-snapshot-zero-base-investigation.md`のsource facts、
  `20260831t022358z-decision-candidate-nextjs-component-snapshot-best-practice.md`のapproved decisions、
  人間向けHTMLのvisual explanationをcanonical R/D/Pへ反映する。
- current production package/core pathsを`未実装`とするstale記述を修正し、existing extension pointとnew planned pathを分離する。
- anti-shadowing、finite recognition/export、per-project config/module resolution、two-phase freeze、protocol/digest、PropsTypeIR/JS extraction、flow/boundary、partial-safe taint proof、public schema/config/package contractをfield-levelでcanonical Designへ固定する。これをproduction implementation後の判断へ先送りしない。

### I05-PLAN-001 acceptance-first contract

- App/Pages Router、named/default/anonymous default、barrel/re-export/alias、reachable/unreachable local Componentをfixture化する。
- inline/interface/alias/import/destructured/FC/class/forwardRef/generic/union/intersection propsとcomplexity opaqueをfixture化する。
- static/literal dynamic/render conditional/collection/createElement、ambiguous/nonliteral unknownをfixture化する。
- client entry/dependency/server candidate/dual role/boundary effectをfixture化する。
- targetless/path(file+directory complete descendants)/depth/missing/project-scope ambiguity/out-of-scope/tainted-selectionをfixture化する。公開target文法は`path:<repository-relative-path>`だけとし、内部component/module/file keyを受理しない。snapshot+next root manifestはNext request/domain/resolved-configと同じunique canonical path-string setへ投影し、module/class/object/mixed/old/permutation/duplicate mutationを拒否する。
- not_applicable、complete empty、complete+diagnostic、partial_safe、payload_unavailable、usage/fatal/interrupt、entity/transport limits、stdout selectorをtable-drivenに固定する。
- TrustedTypeEnvironment、private request/response、Python-owned frozen UTF-8 source bytes/export syntax census、独立export observation、PropsTypeIR、PlantUML、diagnostic、wheel/sdist/offline、domain config/source projectionのpositive/negative fixturesを固定する。censusはowner file、exact byte span/token identity、syntax kind、exported name、role、re-export/starを閉じて導出し、Node syntax identityとexact比較する。TypeScript 5.9.2 Programのparse/semantic diagnostics 0とAST/TypeChecker certified inventoryをNode contract gateで検証する。
- public Moduleはprogram roleかつ`.ts/.tsx/.js/.jsx`のFileだけから生成し、`.d.ts`、`package.json`、`tsconfig.json`、`jsconfig.json` direct targetとsemantic childをnegative vectorで固定する。directoryはcontext/control provenanceを許すがsemantic childを増やさない。
- production adapterを追加せず、`tests/contracts/next_reference_validation.py` のdata-only validator、`tests/contracts/test_next_contracts.py` のmutation/golden vectors、`tests/fixtures/next_contract_vectors.json` のPLAN-008 indexで、JSON Schemaでは表現できないownership、taint closure、digest、order、status、renderer、compatibility invariantを実行可能にする。
- Designで固定したv1 normative source/process/type/flow limitをboundary fixtureで検証し、変更が必要ならproduction実装前にcanonical DesignとStrict gateを更新する。

### I05-PLAN-008 machine-checkable contract Strict gate

- private request/response/model、TrustedTypeEnvironment、Next semantic/domain manifest/config/runtime member/licenseのJSON Schema、diagnostic catalog、semantic/PlantUML contract docs、positive/negative mutation vectorsを実ファイルとして固定する。
- P0/P1 closureのローカル証拠は、`tests/contracts/test_json_schemas.py`（schema registry、既存Python/SQLAlchemy golden、public Next branch）と `tests/contracts/test_next_contracts.py`（cross-record reference validator、status matrix、known-answer/golden vectors）で再実行できる形にする。新しいNext production behavior、Node adapter、依存関係はこのstepへ含めない。
- SpecDock/schema/HTML/format validation、clean commit/push、exact upstream SHA binding後にChatGPT Use StrictでP0/P1とcontract gapをレビューする。
- findingをcanonical authority/current sourceへ照合して修復し、fresh exact SHAでP0/P1=0まで再レビューする。passはIssue実装完了ではない。

### I05-PLAN-002 bridge and adapter boundary

existing extension points:

- `src/code_structure_viz/source/source_view.py`
- `src/code_structure_viz/source/targets.py`
- `src/code_structure_viz/core/config.py`
- `src/code_structure_viz/core/domains.py`
- `src/code_structure_viz/application/snapshot_domain.py`
- `src/code_structure_viz/application/snapshot.py`

new planned modules（実装開始時にcurrent build/package layoutを再確認する）:

- `src/code_structure_viz/adapters/next/bridge.py::NextAdapterBridge`
- `src/code_structure_viz/adapters/next/protocol.py`
- `adapters/next/package.json`、`package-lock.json`、`tsconfig.json`
- `adapters/next/src/analyze.ts::analyzeRepository`
- `src/code_structure_viz/_next_runtime/`（compiled adapter、TypeScript libs、TrustedTypeEnvironment wheel resources）

explicit project rootのdirect Next dependencyをPythonで判定し、不在を証明した場合はNode processを起動しない。domain-owned planでprogram/control/context bytesを一度だけ凍結し、Nodeへtarget path/cwdを渡さない。stdin/stdout exact one JSON、fixed argv/private cwd/minimal env、process/time/byte/memory capを実装する。

### I05-PLAN-003 Next semantic model

- physical-path Module、declaration-key Component、Export/Import binding、Prop identityをcanonicalizeし、barrel/aliasでComponentを複製しない。
- positive evidenceによるComponent recognition、closed wrapper allowlist、effective signatureからのclosed props IRを実装する。
- module/component two-plane graphとbounded JSX output-flowを実装し、event handler/render prop/arbitrary helper/nonliteral dynamicからedgeを捏造しない。
- direct client/router factsとclient dependency/server candidate derived rolesを実装し、no directiveをserverと断定しない。

### I05-PLAN-005 failure and entity gate

- intentional unsupportedをunknownとして完全表現できる場合はcomplete+diagnostic。promised semanticsの局所欠落はsafe subset/exact coverage/same-renderer-subset/redaction/target/budgetをすべて証明した場合だけpartial_safe。
- explicit target、malformed applicability/config、global Program、Node/protocol/schema/security/identity/limit failureはpayload unavailableとし、not_applicable/fallbackへ変換しない。
- model structural/reference validationは`max_model_records=10,000`を適用してactual internal Module+Component countを返す。publication直前の独立EntityBudgetGateがselected/published Module+Componentだけを数え、default 500は受理、501は`CSV-NEXT-LIMIT-005`付きexit 3/affected payloadなし/actual付きmanifest-only、600 overrideで501は成功とする。10,001 total model recordsはentity budgetと別の`max_model_records` failureとして固定し、invalid valueはexit 2。ID-only proof rowを含む実wireでexact 10,000と10,001をbounded decode→response validation→decisionへ通す。

### I05-PLAN-004 Artifact publication

- adapter responseをuntrusted inputとしてclosed schema/path/ref/redaction/order/ID/count/digest/target completenessをPythonで検証・再計算する。
- `next.snapshot.semantic.json`と`next.snapshot.puml`を同一validated modelからrenderし、Next coverage/provenance、manifest descriptor、stdout paths、writer final path/PlantUML validationをclosed registryへ追加する。
- literal/source/comment/secret/absolute path/raw compiler text/protocol noiseをpublish前にrejectする。

### I05-PLAN-007 stdout selector and stream contract

- current CLI parserがsyntax上受理済みの`next:semantic-json|next:plantuml`を重複実装せず、NextのDomainName、selected domain/requested format compatibility、schema、stream pathと一貫して有効化する。`--stdout`は高々1回、invalid/duplicate/unselected/unrequestedはsource acquisition前にexit 2、stdout空、Artifactなしとする。
- publication後はavailable selectorの公開fileをexact bytesで複製する。unavailable selectorは`stdout-result/v1` 1行、selectorなしは`run-summary/v1` 1行をcanonical key orderで出す。diagnosticはstderrだけへ出し、`--output-dir` publicationを維持する。
- complete、not_applicable、partial_safe、payload_unavailable、run fatal、handled interrupt、manifest unavailableをtable-driven fixtureで固定し、source/secret/absolute pathがstdoutへ漏れないことをnegative scanする。

### I05-PLAN-006 hardening and handoff

- target cwd/node_modules/network/npm/npx/build/config/plugin/application execution traps、same-input adapter/output equality、core-only install without Node、Next-enabled offline bundle/lock/license、Node 22/latest CIを通す。
- current security testのsubprocess allowlistをexact Git runner + exact Next runnerへ狭く更新し、任意subprocessを許可しない。
- Python/SQLAlchemyのsemantic/PlantUML/manifest/stdout golden bytesを維持してIssue #9へhandoffする。

## 検証

| Test ID | acceptance behavior | planned file | command |
| --- | --- | --- | --- |
| I05-AT-001 | Next snapshot | tests/acceptance/next/test_snapshot_cli.py | uv run pytest tests/acceptance/next/test_snapshot_cli.py -q |
| I05-AT-002 | adapter protocol | tests/contracts/next/test_adapter_protocol.py | uv run pytest tests/contracts/next/test_adapter_protocol.py -q |
| I05-AT-003 | safe subset | adapters/next/test/safe-subset.test.ts | npm --prefix adapters/next test -- safe-subset |
| I05-AT-004 | partial_safe/payload_unavailable adapter matrix | tests/acceptance/next/test_adapter_failures.py | uv run pytest tests/acceptance/next/test_adapter_failures.py -q |
| I05-AT-005 | static/redaction | tests/security/test_next_static_boundary.py | uv run pytest tests/security/test_next_static_boundary.py -q |
| I05-AT-006 | Node optionality | tests/acceptance/next/test_optionality.py | uv run pytest tests/acceptance/next/test_optionality.py -q |
| I05-AT-007 | entity budget publication and diff-only option rejection | tests/acceptance/next/test_snapshot_budget.py | uv run pytest tests/acceptance/next/test_snapshot_budget.py -q |
| I05-AT-008 | stdout selector matrix | tests/acceptance/next/test_stdout_selector.py | uv run pytest tests/acceptance/next/test_stdout_selector.py -q |
| I05-AT-009 | TrustedTypeEnvironment / no target types | tests/acceptance/next/test_trusted_type_environment.py | uv run pytest tests/acceptance/next/test_trusted_type_environment.py -q |
| I05-AT-010 | closed contracts / wheel/sdist / offline/license | tests/packaging/test_distribution.py + test_next_distribution.py | uv run pytest tests/contracts/next tests/packaging/test_distribution.py tests/packaging/test_next_distribution.py -q |
| I05-AT-011 | Python/SQLAlchemy byte compatibility | tests/regression/test_next_domain_compatibility.py | uv run pytest tests/regression/test_next_domain_compatibility.py -q |

### issue gate commands

```bash
uv run pytest tests/acceptance/next/test_snapshot_cli.py -q
uv run pytest tests/contracts/next/test_adapter_protocol.py -q
npm --prefix adapters/next test -- safe-subset
uv run pytest tests/acceptance/next/test_adapter_failures.py -q
uv run pytest tests/security/test_next_static_boundary.py -q
uv run pytest tests/acceptance/next/test_optionality.py -q
uv run pytest tests/acceptance/next/test_snapshot_budget.py -q
uv run pytest tests/acceptance/next/test_stdout_selector.py -q
uv run pytest tests/acceptance/next/test_trusted_type_environment.py -q
uv run pytest tests/contracts/next tests/packaging/test_distribution.py tests/packaging/test_next_distribution.py -q
uv run pytest tests/regression/test_next_domain_compatibility.py -q
uv build --offline
./spec-dock/scripts/spec-dock validate
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pytest
```

### Requirement → Design → Plan → acceptance → test trace

| Requirement | Design | Plan | acceptance | test |
| --- | --- | --- | --- | --- |
| I05-REQ-001 | I05-DES-001 | I05-PLAN-001 | I05-AC-001 | I05-AT-001 |
| I05-REQ-002 | I05-DES-002 | I05-PLAN-002 | I05-AC-002, I05-AC-004, I05-AC-006, I05-AC-009 | I05-AT-002, I05-AT-004, I05-AT-006, I05-AT-009 |
| I05-REQ-003 | I05-DES-003 | I05-PLAN-003 | I05-AC-001, I05-AC-003 | I05-AT-001, I05-AT-003 |
| I05-REQ-004 | I05-DES-004 | I05-PLAN-004 | I05-AC-001, I05-AC-002, I05-AC-010 | I05-AT-001, I05-AT-002, I05-AT-010 |
| I05-REQ-005 | I05-DES-005 | I05-PLAN-005 | I05-AC-003, I05-AC-004, I05-AC-007 | I05-AT-003, I05-AT-004, I05-AT-007 |
| I05-REQ-006 | I05-DES-006 | I05-PLAN-006 | I05-AC-005, I05-AC-006, I05-AC-009, I05-AC-010, I05-AC-011 | I05-AT-005, I05-AT-006, I05-AT-009, I05-AT-010, I05-AT-011 |
| I05-REQ-007 | I05-DES-007 | I05-PLAN-007 | I05-AC-008 | I05-AT-008 |

### regression boundary

- dependency Issueのacceptance suiteを再実行し、public endpoint/source/schema/manifest/exit contractを破っていないことを確認する。
- target repositoryのHEAD、branch、refs、index、status、tracked/untracked bytesがcommand前後で一致する。
- same-input deterministic rerun、output collision、invalid override、interrupt cleanupを確認する。
- Artifact、diagnostic、stdout/stderr/logをsource body、raw hunk、comment、literal、secret、absolute pathでnegative scanする。
- visual vocabularyはcolorだけでなく記号、line style、legendをgolden/semantic testで検査する。

## rollback

- data migration は N/A。Node adapter release は Python package と互換 matrix を固定する。protocol mismatch は adapter を incomplete として隔離し、旧 protocol reader を保持した additive fix または version up で forward recovery する。
- rollback trigger: acceptance regression、source execution/mutation、secret/absolute path leak、incorrect successful exit、ambiguous moved の誤採用。
- rollback unit: Issue の production code、tests、schema/doc additionsを一体で revert する。dependency Issue の accepted contract は戻さない。
- forward recovery: unsafe pattern を `incomplete`/`unknown` へ狭め、誤った success を継続しない。既存 Artifact を自動 rewrite しない。
- output migration は N/A。Artifact は immutable run output であり、既存 output を上書きしない。

## exit / handoff

- I05-AC-001〜I05-AC-011のacceptance evidenceが揃う。
- Requirement→Design→Plan→test trace に gap がない。
- planned path honesty を review し、実装時点の実在 path/symbol と差異があれば Design/Plan を先に更新する。
- residual risk、unsupported static pattern、coverage limitation、explicit override を release note と manifest diagnostic contract に残す。
- downstream handoff: Next snapshot preview。Python/SQLAlchemy の install/runtime requirement へ Node を持ち込まない optional adapter separation を完成させる。
- completion 後も implementation/report の実績は canonical Report に別途記録し、本 Plan を実行ログにしない。

### Round 15 remediation plan (pre-implementation gate)

Round 15の三試行（connector-only、verification-only retry、content review follow-up）は
`artifacts/20260901t060000z-disc-strict-spec-review-round-15.md`へ個別のtranscript path/SHAとして保存する。
固定点は branch `iss-00008-generate-nextjs-component-snapshots` のSHA
`c3f8e4188ca715a29d60a7454a66390938bce496`、CI `33472932927`（7/7 green）であり、content reviewの
historical verdictは P0=0/P1=13/P2=1、`review_status=fail`、`implementation_ready=no`である。
fresh current-SHA Strictはpending/readiness unconfirmed/product implementation absentとして扱う。

実装前の作業順は次のとおりである。

1. `NextPublicationContext`（semantic compatibility descriptor/identity versionsを含む）とclosed
   `NextRunDecision`をreference validatorで閉じる。validated responseは
   requestをdeep-copyし、schema/id、run_context、targets、resolved limits、gate transition、target/export
   failure consistencyをconstructor invariantにする。request-independent failureには
   `NextDecisionContext`を使い、domain/root/manifest/stdout/stderr/publicationをdecision-onlyへ限定する。
2. catalogに基づくfailure kind/stage/ref/count/outcome/exit matrixを全config/project/source/target/trust/process/
   limit/protocolへ適用する。SOURCE-001（local partial）とSOURCE-003（global unavailable）、unsupported complete、
   adapter over_budget rejection、Python EntityBudgetGateを別テストで固定する。
3. response actual-wire gateを実装する。`published_model_records + proof_only_records = discovered_records`を
   authorityとし、`max_model_records=10,000` exact/+1、aggregate+1、raw+1をschema-valid generated responseで
   bounded decode→response boundary decisionへ通す。`max_adapter_stdout_capture_bytes`、
   `max_adapter_response_bytes`、`max_selected_stdout_bytes`を各々exact/+1で測定し、child stderrも同じ
   count-before-retain/read-stop/disposal contractにする。
4. `seal_source_acquisition(intent, reader, inventory)`にplan/viewの生成を一本化し、single-read、drift、role、
   extends、digest/sizeのnegative/positive fixtureを追加する。target failureのeight-reason canonical array、
   Next selector branch、canonical sorted JSON bytesをschemas/goldensへ同期する。
5. Unicode 15.0 checked-in classification tableを全identifier contextへ配線し、Other_ID/U+00B7/Join_Control/
   reserved/non-NFC/control/post-15.0とfull scalar bitstream digestをminimum/latest laneで検査する。BoundaryRolePropagation
   はfacts/router/static value closureから独立再計算し、Button/Card fixtureを修正する。
6. Requirement/Design/Plan、関連contract docs、schema/catalog、human HTML、Round15 artifactを同期後、focused
   contracts、full pytest、mypy、ruff、SpecDock、HTML PlantUML、TS trusted gateを実行する。`src/**`差分、
   generated `node_modules`、未知のproduction implementationがないことを確認する。fresh StrictのP0/P1=0 passまで
   I05-PLAN-002以降のproduction implementationへ進まない。

#### Round 15 criterion → executable evidence

| criterion | reference evidence |
| --- | --- |
| P1-1 decision-only authority/context | `test_validated_decision_defensively_copies_request_and_publication_context`, `test_request_independent_pre_response_decision_keeps_closed_context`, existing decision projection vectors |
| P1-2 reason/outcome ownership | `test_round14_proof_reason_semantics_keep_selection_and_unsupported_complete`, adapter `over_budget` rejection and source failure vectors |
| P1-3/P1-9 Unicode contextual and pinned table | `test_round15_identifier_name_is_contextual_and_host_ucd_independent`, full table digest KAT |
| P1-4 count and reachable limits | generated model exact/+1 and `test_schema_valid_wire_aggregate_plus_one_precedes_model_and_schema_routing` |
| P1-5/P1-6 capture boundaries | stdout/stderr faithful iterable exact/+1 tests and selected stdout copy boundary |
| P1-7 source seal | `test_source_seal_derives_plan_and_view_from_one_intent_and_rejects_drift` |
| P1-8/P2-1 target failure branch | `test_stdout_target_failure_reason_enum_is_closed_for_each_resolution_failure` and bijective whole-run vector |
| P1-10 full Unicode bitstream | `identifier_classification_digest()` known-answer assertion |
| P1-11 source-specific unavailable | `classify_source_failure` local/global matrix |
| P1-12 boundary role sole authority | `derive_boundary_roles` independent recomputation and Button/Card fixtures |
| P1-13 canonical stdout bytes | canonical JSON exact-byte and target-failure goldens |
| HTML/evidence durability | pinned PlantUML validator and Round15 artifact hash/provenance table |

#### Round 16 remediation plan and executable trace

Round 16 content reviewの固定点は SHA
`732477c72c7e05d3f15818ba8a3f75a4c97dc5a9`、CI `33494926439`（7/7 green）、
判定 `P0=0 / P1=16 / P2=3 / fail / implementation_ready=no` である。
verification-onlyとcontent reviewのtranscriptは新規Round16 artifactへ保存し、
fresh current-SHA Strictはpending、readinessは未確認、production implementationは
未着手とする。

実装前に次の順でdata-only contractを閉じる。

1. `SourceDiscoveryIntent`をroots/control candidates/fixed rulesだけに縮小し、
   frozen control bytes + inventoryからconfig、extends closure、final paths、role mapを
   一回の`seal_source_acquisition`で導出する。plan/view caller injection、duplicate read、
   drift後のreadをnegative testする。
2. 実SourceAcquisitionSeal、resolved public/private request、observed toolchain、trusted
   environment、compatibility descriptor、versioned process-launch observationからimmutable
   `NextPublicationContext`を一度だけ構築し、全decision variantと全projectionへ渡す。
   descriptorは省略不可でtoolchainのNode statusと一致し、fingerprint preimageへ含める。
   pre-response/not-applicableの`NextDecisionContext`も明示的にsealし、後段のfallbackを
   禁止する。`ValidatedAdapterRequest`はdeep copyし、ID/files/base64/size/digest/canonical
   bytes/limitsをresponse前に検証する。
3. request-independent config/project/source failure branch、SourceFailureLedger、catalog
   derived failure matrixを固定する。locality proof付きSOURCE-001/partialと非分離SOURCE-003/
   unavailable、unsupported complete、adapter over_budget rejectionを全surfaceへ写す。
4. raw cap→decode/aggregate→schema→base/path/ref/proof→actual model/proof-only→model gate→
   entity gate→selected copyの順を守る。structural overrunはLIMIT-003、malformed/schema/
   proofはPROTOCOL-001。child capture、private response、public stderr、selected copyの
   測定を一つの`PublicationBoundaryDecision`へsealし、そのdecisionだけをdomain/root
   manifest/stdout/stderr/artifact/exit projectionへ渡す。独立status/measurement mapを
   受け付けず、selected copy failureはsemantic statusを変えずpublication resultへsealする。
5. target failure eight reasonsの一target一行、Unicode 15.0 contextual predicates/full
   scalar KAT、BoundaryRolePropagationのclient seed/server traversal規則、canonical
   sort_keys/NFC/UTF-8/LF bytes、versioned process launch observationを各golden/schemaへ
   同期する。faithful capture harnessはOS process-level testと主張しない。
6. Round 16 artifactへ三試行の利用可能なprovenance、findings→remediation→test map、全gate
   command/resultを追記する。artifactのhistorical failは上書きせず、fresh Strict passまで
   I05-PLAN-002以降のproduction implementationを開始しない。

| Round 16 criterion | executable evidence |
| --- | --- |
| P1-1 SourceDiscoveryIntent / atomic seal | `test_source_seal_derives_plan_and_view_from_one_intent_and_rejects_drift` |
| P1-2 PublicationContext sole authority | `test_all_decision_variants_project_without_legacy_fixture_authority`; `test_round16_publication_context_requires_explicit_launch_and_decision_context` |
| P1-3 validated private request | `test_response_validation_accepts_only_the_bounded_raw_bytes_entrypoint` |
| P1-4 request-independent unavailable | `test_round16_request_independent_source_failure_projects_schema_valid_whole_run` |
| P1-5 SourceFailureLedger locality | `test_round15_source_failure_preserves_locality_boundary` |
| P1-6 closed failure matrix | `test_round16_failure_matrix_is_catalog_derived_and_rejects_cross_product` |
| P1-7 validation precedence | `test_raw_response_mutations_all_cross_the_same_bounded_entrypoint` |
| P1-8 structural limit code | `test_actual_json_aggregate_boundary_precedes_schema_validation` |
| P1-9 selected stdout branch | `test_selected_stdout_copy_has_exact_and_plus_one_publication_boundaries` |
| P1-10 final publication seal | `test_round16_final_publication_decision_seals_capture_stderr_and_selected_copy` (final boundary-only projections, exact/+1, substitution rejection) |
| P1-11 canonical bytes | `test_publication_bytes_are_exact_model_payloads_and_digest_roots` |
| P1-12 anonymous default/context | `test_round16_identifier_contexts_cover_reserved_exports_and_anonymous_default` |
| P1-13 Unicode context | `test_round15_identifier_name_is_contextual_and_host_ucd_independent` |
| P1-14 target reason cardinality | `test_round16_target_resolution_exposes_all_closed_failure_reasons` |
| P1-15 boundary roles | `test_taint_edges_are_derived_for_boundary_and_shared_frontier` |
| P1-16 process launch descriptor | `test_round16_process_launch_descriptor_is_closed_and_security_deterministic`; `test_round16_publication_context_requires_explicit_launch_and_decision_context` |
| P2-1 HTML drift resistance | `test_round16_html_has_no_fixed_limit_inventory` |
| P2-2 vector index bijection | `test_contract_fixture_index_materializes_plan_008_vectors` |
| P2-3 limit message/catalog | `test_next_diagnostic_catalog_is_the_public_and_manifest_authority` |

### Round 17 remediation plan and executable trace

固定点は SHA `032c8d7e2f7786fb443fd2a49566c5a6ad9815d5`、CI
`33514033888`（7/7 green）。Strict content reviewのhistorical verdictは
`P0=0 / P1=9 / P2=3 / fail / implementation_ready=no`であり、fresh
current-SHA Strictはpending、readinessは未確認、production implementationは未着手とする。

1. Intent/inventoryを観測専用にし、frozen control bytesからplan/view/config/extends/
   paths/rolesをsingle-sealで導出する。request-owned derived mutationとplan/view-only
   injectionを拒否する。
2. request-independent failureをstage-discriminated null provenanceへ固定し、
   `ValidatedAdapterRequest`をcomposition/frozen authorityとしてcanonical requestを再検証する。
3. SourceFailureLedgerをsealed graphから導出し、proof-derived target IDを再解決する。
   target unavailableはclosed eight reasonsの一target一rowとする。
4. observed process descriptorをactual spawnへbindし、PublicationBoundaryDecisionへ
   response/request/model/artifact/selector/diagnostic/measurementをsealする。summary、manifest、
   selected artifactのselected-stream exact bytesも同じcopy boundaryで測定し、全surfaceは
   final objectだけを投影入力とする。exactは全bytes、limit+1はpartial bytesなしのtyped
   unavailableへ進み、manifest/domain descriptorを規則に従って保持する。
5. raw cap → bounded decode/aggregate → closed schema → base/path/reference/proof →
   actual model+proof-only count → model gate → entity gate → selected copyを固定する。
   semanticはID order、config/source-plan/rootはroot-path order、submitted orderはsort前検査する。
6. R/D/P、schemas、catalog、fixture index、HTMLをRound 17状態へ同期し、focused/contracts/full
   pytest、mypy、ruff、SpecDock、PlantUML、diff cleanlinessを実行する。

| criterion | executable evidence |
| --- | --- |
| round17.p1-1 inventory and source authority | `test_round17_source_inventory_accepts_observations_only`; `test_round17_request_owned_derived_source_claims_cannot_override_control_bytes`; `test_source_seal_derives_plan_and_view_from_one_intent_and_rejects_drift` |
| round17.p1-2 request-independent provenance | `test_request_independent_pre_response_decision_keeps_closed_context`; `test_round16_request_independent_source_failure_projects_schema_valid_whole_run` |
| round17.p1-3 composed request | `test_round17_validated_request_is_composed_and_revalidated`; `test_response_validation_accepts_only_the_bounded_raw_bytes_entrypoint` |
| round17.p1-4 graph-derived locality | `test_round17_source_failure_ledger_derives_locality_without_caller_booleans`; `test_round15_source_failure_preserves_locality_boundary` |
| round17.p1-5 observed launch identity | `test_round16_process_launch_descriptor_is_closed_and_security_deterministic`; `test_round16_publication_context_requires_explicit_launch_and_decision_context` |
| round17.p1-6 final publication authority | `test_round17_publication_artifacts_are_bound_to_the_immutable_decision`; `test_round16_final_publication_decision_seals_capture_stderr_and_selected_copy` |
| round17.p1-7 stdout union | `test_round17_final_publication_stdout_union_seals_summary_manifest_exact_and_plus_one`; `test_next_stdout_matrix_usage_is_empty_and_manifest_free`; `test_round16_final_publication_decision_seals_capture_stderr_and_selected_copy` |
| round17.p1-8 proof target reroute | `test_round17_proof_derived_target_failure_is_typed_and_sorted`; `test_round16_target_resolution_exposes_all_closed_failure_reasons` |
| round17.p1-9 surface ordering | `test_round11_inverse_project_request_order`; `test_project_surface_order_is_root_path_while_semantic_records_remain_id_order` |
| round17.p2-1 closed decision context | `test_round16_failure_matrix_is_catalog_derived_and_rejects_cross_product`; `test_round16_publication_context_requires_explicit_launch_and_decision_context` |
| round17.p2-2 LIMIT-003 authority | `test_next_diagnostic_catalog_is_the_public_and_manifest_authority`; `test_actual_json_aggregate_boundary_precedes_schema_validation` |
| round17.p2-3 HTML pipeline | `test_round17_html_has_validation_pipeline_and_round17_state` |

Production implementation remains outside this remediation plan. Strict pass with
P0/P1=0 is still required before I05-PLAN-002 implementation work.

### Round 18 remediation plan and executable trace

固定点は SHA `885352347d250cc34aef0bd52e1fe27063288c05`、CI
`33543204992`（7/7 green）、Strict session
`required-strict-github-connector-verificati-680`（transcript SHA-256
`400431ed1fb444b3bd2509edf14ce557b8f292b0f011f281e74ffa241db8cec8`）である。
historical verdictは `P0=0 / P1=7 / P2=1 / fail / implementation_ready=no` として保存し、
fresh current-SHA Strictはpending、readinessは未確認、production implementationは未着手とする。

1. Source acquisitionを `DiscoveryIntent → frozen control observation → internal derivation →
   single SourceAcquisitionSeal` に固定する。inventory injection、caller observed paths、malformed
   control、revision drift、plan/view-only、duplicate/post-seal readをnegative testする。
2. SourceFailureLedgerをsealed raw graphから再計算し、locality/taintをcaller booleanから切り離す。
   request-independent provenanceはstageごとの observed/unobserved rowsだけを保持し、未観測のlimits/
   toolchain/trusted env/source plan/processをsynthetic generationしない。
3. `ValidatedAdapterRequest`をcomposition/frozen authorityとしてrequest id、canonical bytes/digest、
   file evidence、targets、run context、limitsをresponse boundaryで再検証する。validated responseの
   raw bytes/SHAとdecision-owned diagnosticsをopaque authorityとして保持する。
4. raw cap → bounded decode/aggregate → closed schema → base/path/ref/proof → actual model/proof-only
   count → model gate → entity gate → selected copyを一つのcatalog orderで実行する。structural resource
   はLIMIT-003、malformed/schema/proofはPROTOCOL-001とし、schema/ref invalid + model+1のprotocol precedence
   をgenerated wireで検証する。
5. `PublicationBoundaryDecision`をfinal publication authorityとし、summary/manifest/artifact/typed
   unavailableのexact bytes、selector、diagnostic JSONL、capture/stderr/selected-copy measurementsを一度
   sealする。全projectionから独立 outcome/map/payloadを削り、exact/+1 substitution testを通す。
6. `next-process-launch-observation-v1`はOS identity/hash/versionとactual spawn handle/TOCTOU、fixed argv/env/FD/
   process groupをrequiredにする。referenceではhost processを実行せず、faithful iterable capture testと
   production OS acceptance boundaryを明記する。
7. stdout union、target reason、schema discriminator、shared path grammar/safe-ID、NFC UTF-8 path orderと
   canonical JSON object-row orderをschemas/docs/fixtureへ同期する。HTML validation orderをstrict indexで
   検証し、reverse mutationをnegative testする。

| criterion | executable evidence |
| --- | --- |
| R18-P1-01 source seal authority | `test_round18_source_seal_rejects_caller_membership_and_typed_drift`; `test_source_seal_derives_plan_and_view_from_one_intent_and_rejects_drift` |
| R18-P1-02 source locality authority | `test_round18_source_failure_ledger_recomputes_reachability`; `test_round18_request_independent_provenance_is_explicitly_unobserved` |
| R18-P1-03 response raw-byte authority | `test_round18_validated_response_raw_bytes_are_opaque_authority` |
| R18-P1-04 publication raw-byte authority | `test_round18_validated_response_raw_bytes_are_opaque_authority` |
| R18-P1-06 publication byte authority | `test_round18_publication_projections_return_sealed_candidate_bytes`; `test_round17_publication_artifacts_are_bound_to_the_immutable_decision` |
| R18-P1-05 process identity | `test_round18_process_descriptor_requires_os_identity_and_spawn_binding`; `test_round16_process_launch_descriptor_is_closed_and_security_deterministic` |
| R18-P1-07 closed stdout union | `test_round18_stdout_union_rejects_partial_discriminator_and_wrong_next_descriptor`; `test_round17_final_publication_stdout_union_seals_summary_manifest_exact_and_plus_one` |
| R18-P2-01 HTML order | `test_round18_html_validation_order_is_strict_and_reverse_mutation_fails` |
| R18 follow-up provenance/order | `test_round18_run_manifest_and_diagnostic_discriminators_are_closed`; `test_round18_path_only_order_is_nfc_utf8_and_object_rows_are_canonical_json` |

Verification must include focused Round18 tests, `uv run pytest tests/contracts -q --tb=short`, full
`uv run pytest -q`, `uv run mypy src tests`, `uv run ruff check .`, `uv run ruff format --check .`,
SpecDock validation, pinned HTML PlantUML validation, `git diff --check`, and an empty `src/**` diff.
No generated `node_modules` may remain. These checks validate the pre-implementation contract only and do
not constitute a Strict pass or product implementation readiness.

### Round 20 remediation plan and executable trace

Round 20のreviewed fixed pointは SHA `aba6509ae818f8b959aa31276a6e8f5d6956680a`、historical
Strict verdictは `P0=0 / P1=6 / P2=1 / fail / implementation_ready=no` である。fresh
current-SHA Strictはpending、readinessは未確認、production implementationは未着手とする。
Strict review sessionは `issue-eight-strict-round-twenty`、verification sessionは
`required-strict-github-connector-verificati-692` である。transcript artifactは存在しないため、
artifactのmeta/output/modelログとそのSHA-256だけをprovenanceとして記録し、未提供のCI番号や
transcriptを推測しない。

実装順序は、まずNode optionalityとsource acquisitionのauthorityを閉じ、その後にfailure projection、
provenance、fixture index、docs/HTMLを同期する。各stepはreference validatorとJSON Schemaの
positive/negative testで閉じる。

1. `PackageApplicabilityMatrix`をfrozen `package.json` direct dependencies/devDependenciesの
   観測から導出する。missing/no-direct-next、direct-next、malformedをclosed enumにし、duplicate
   key、encoding、table/value/type mutationをrejectする。aggregateがall non-applicableなら
   `NotApplicableDecision`、一件でもmalformedならunavailableとする。
2. control候補をknown project-root pathsに限定し、一度だけstrict JSONC parseする。BOM/comments/
   trailing comma、duplicate key、unsafe `..`、package/array extends、plugins/typeRoots/types、
   invalid module/moduleResolutionをtyped fail-closedにする。include/excludeはsegment grammarで
   membershipを導出し、control failureをempty configへ置換しない。
3. `SourceAcquisitionSeal`のfrozen bytesとresolved imports/extends/ownershipからsource graphを
   内部導出する。caller/request/reader graphを無視し、edge deletion + digest recomputationをreject
   する。source integrity resultをComplete/Partial/Unavailable/Fatal unionへ投影し、fatalと
   payload_unavailableのstage/code/manifest/stdout/exitを相互に検証する。
4. process launch observationをfixture/production unionへ固定する。productionはdarwin/linuxと
   verified Node identities、handle、spawn primitive、post-spawn equality、FD/process group、TOCTOUを
   要求し、unavailable/not_applicableではidentityをnullにする。reference checksはhost processを
   実行済みと主張せず、後続production acceptanceをPlanに残す。
5. stage-dependent provenanceの同じvalidatorをNextDecisionContextとNextPublicationContextへ適用し、
   stage/code pair、observed prefix、unobserved suffix、request/limits/source-plan/toolchain/trust/
   process/compatibility/budgetの相関をclosed schemaで検証する。
6. `next_contract_vectors.json`のRound20 positive/negativeとcriterion mapを、実質的なtest bodyへ
   bidirectionalに結び付ける。fixture/HTMLの存在だけでは通さない。R/D/P、contract docs、新schema、
   human HTML（既存8 diagramsを維持）および本artifactへ同じ語彙を反映する。

#### Round 20 criterion → executable evidence

| criterion | positive/negative evidence |
| --- | --- |
| R20-P1-01 PackageApplicabilityMatrix | `test_round20_package_applicability_matrix_is_direct_dependency_only`; `test_round20_package_applicability_matrix_rejects_encoding_duplicates_and_mixed_state`; `test_round20_explicit_config_candidates_cannot_hide_package_applicability` |
| R20-P1-02 config/inheritance/membership | `test_round20_source_control_uses_segment_grammar_and_fail_closed_control_reads` |
| R20-P1-03 source graph authority | `test_round20_source_graph_is_derived_from_frozen_bytes_not_reader_injection` |
| R20-P1-04 source integrity projection | `test_round20_source_integrity_has_one_fatal_vs_payload_unavailable_projection` |
| R20-P1-05 process observation | `test_round20_process_observation_has_explicit_unavailable_union_and_no_fake_identity` |
| R20-P1-06 provenance | `test_round19_stage_provenance_reference_rejects_stage_code_and_prefix_mutations`; `test_round20_stage_provenance_is_one_canonical_shape_and_rejects_mismatch` |
| R20-P2-01 executable coverage index | `test_round20_fixture_coverage_index_is_substantive` |

Required checks are focused Round20 tests, focused Next/schema tests, contract/full pytest, mypy, ruff
check/format, SpecDock, pinned HTML PlantUML/browser validation, diff check, empty `src/**` diff, and no
generated `node_modules`. Passing these checks does not change the historical Strict verdict or establish
implementation readiness.

### Round 21 remediation plan

Round 21の固定点は SHA `67351f970835afe05b3f4db1aa40b73b3abf0198`、Strictの
`P0=0 / P1=5 / P2=1 / fail / implementation_ready=no` である。verification-only は
`issue-eight-strict-round-twenty-3`、full review は `required-strict-github-connector-verificati-704`。
historical verdictは保持し、fresh current-SHA Strictはpending、readinessは未確認、production
implementationは未着手とする。実装順序は authorityの上流から下流へ固定し、各stepをpositive/negative
contract testとSchemaで閉じる。

1. **Applicability:** frozen package bytesを一度だけ読み、direct Nextのみによる
   `PackageApplicabilityMatrix`を導出する。applicable/non-applicable/malformedを表にし、mixedでは
   applicable rootsのみ、all non-applicableではNode probe禁止のNotApplicableDecision、malformedでは
   global unavailableを同一projectionから出す。indirect/lockfile/config/dirnameはNode probeの根拠にしない。
2. **Config/source membership:** known root control candidatesだけをJSONC lexerで読み、BOM/comments/
   trailing comma（comma+comment+closingを含む）を受理する。local `extends`はproject内 explicit
   `./...` string一件だけとし、bare/package、array、absolute、`../`、URL-like、ambiguity、cycle、
   forbidden compiler optionsを拒否する。include/excludeはsegment grammarで導出し、read/parse errorを
   empty objectへ置換しない。
3. **Source graph/locality:** frozen bytesとsealed planのownerから module-plane scannerで static/
   side-effect/export-from/literal dynamic/require と baseUrl/pathsを解決する。comment/template/regexの
   false positiveを除外し、unsupported/ambiguous/unresolved/externalはopen edgeとして残す。caller graphや
   edge削除後digestを受け取らない。
4. **Provenance:** request-bound/request-independentの一つのdiscriminated shapeで stage/code、observed
   prefix/value、budget correlationを保持する。project_validation、source_control、Node/process、
   response、modelのcatalog pairをSchema/reference validatorで検査し、後続未観測値をnull/unobserved
   とする。control failureをdomain/root/stdout/exitへ通す。
5. **Process:** `next-process-launch-observation-v1`を唯一の正本とする。darwin/linuxの
   OS-native verified-open/execution、realpath/hash/version、hash/spawn identity、spawn primitive、
   post-spawn equality、argv/cwd/env/FD/group、TOCTOUを束ね、旧descriptorはcompatibility viewに限定する。
   ephemeral device/inode/FDはsecurity observationに残すがstable fingerprintから除外する。fixture-only
   reference testをOS process-level acceptanceと主張しない。
6. **Coverage:** fixtureのpositive/negative vector、test body、validator、criterion mapを相互に検証し、
   missing/misassigned criterion/vector/validator/mutationをcoverage gateが拒否する。coverage自身の
   mapping mutationも独立negativeとして実行する。

#### Round 21 criterion → executable evidence

| criterion | substantive test | vectors |
| --- | --- | --- |
| R21-P1-01 applicability | `test_round21_applicability_matrix_owns_filter_probe_and_all_public_surfaces`; `test_round21_applicability_source_observation_precedes_node_and_is_read_once` | `round21-applicability-end-to-end`; `round21-applicability-malformed-no-node` |
| R21-P1-02 config boundary | `test_round21_jsonc_extends_grammar_is_closed_and_trailing_comment_is_deterministic` | `round21-config-closed-grammar`; `round21-config-extends-injection` |
| R21-P1-03 source locality | `test_round21_source_graph_scanner_closes_supported_import_planes_and_open_edges` | `round21-source-graph-module-plane`; `round21-source-open-edge` |
| R21-P1-04 provenance | `test_round21_provenance_catalog_has_single_request_independent_source_control_union` | `round21-provenance-stage-union`; `round21-provenance-stage-mismatch` |
| R21-P1-05 process authority | `test_round21_process_observation_is_normative_and_fingerprint_excludes_ephemeral_identity` | `round21-process-observation-fingerprint`; `round21-process-identity-substitution` |
| R21-P2-01 bidirectional coverage | `test_round21_coverage_index_is_bidirectional_and_self_validating` | `round21-coverage-index`; `round21-coverage-mapping-mutation` |

Focused tests must run before the complete contract suite. Completion also requires full pytest, mypy, ruff,
SpecDock, pinned HTML validation, diff cleanliness, empty `src/**` diff, and no `node_modules`. Even with all
local checks green, only a fresh Strict `review_status=pass` with P0=0/P1=0 can authorize I05 production work.

### Round 22 remediation plan

Round 22 is a data-only remediation of reviewed SHA
`e63c5d411cedc40c85f396cccbf12ca141b1938f` (CI `33586646010`, 7/7 success).
The historical Strict result is `P0=0 / P1=20 / P2=0 / fail / implementation_ready=no`.
The review session is `required-strict-github-connector-verificati-713` (output.log
SHA-256 `d3e8c835608a41e02ac8d33080be8cda97c81f18541776b3ab3f6a92deb0ea8d`); the
verification-only session is `issue-eight-strict-round-twenty-4`. Fresh current-SHA
Strict remains pending, readiness is unconfirmed, and production implementation is absent.

The implementation order and authority are fixed:

```text
frozen package/control/source bytes
  -> PackageApplicabilityMatrix (applicable | non_applicable | malformed)
  -> JSONC control and segment membership
  -> SourceAcquisitionSeal and resolved | open source graph
  -> request-bound/request-independent provenance
  -> ValidatedAdapterRequest and opaque canonical response bytes
  -> NextRunDecision
  -> next-process-launch-observation-v1
  -> PublicationBoundaryDecision
  -> sealed domain/root manifest/stdout/stderr/artifact/exit bytes
```

1. Derive `PackageApplicabilityMatrix` first from one trusted frozen
   `package.json` observation per known root. Direct non-empty `dependencies.next` or
   `devDependencies.next` is applicable; missing/no-direct is non-applicable; duplicate,
   conflicting, encoding, JSON, table, or value errors are malformed. Malformed uses
   `CSV-NEXT-APPLICABILITY-002` and is globally unavailable with Node prohibited;
   `CSV-NEXT-APPLICABILITY-001` is reserved for non-applicable. Mixed matrices retain
   applicable roots only; all-non-applicable is `NotApplicableDecision` and reads no
   config, source, or Node.
2. Parse known-root controls once with duplicate-key rejecting JSONC. Accept BOM,
   comments outside strings, and trailing commas including comma/comment/closing. A
   single local `extends` string must be explicit `./...` and stay within the project;
   reject bare/package, array, absolute, `../`, URL-like, ambiguous, and cyclic values,
   forbidden `plugins`/`typeRoots`/`types`, invalid module/moduleResolution, and unsafe
   paths. Derive include/exclude using segment `*`, `?`, and whole-segment `**`; any
   control read/parse failure is global unavailable, never `{}`.
3. Let the seal-owned source planner derive a redacted module-plane graph from frozen
   bytes: static and side-effect imports, export-from, literal dynamic `import()`,
   literal `require()`, and `baseUrl`/`paths`. Comments/templates/regexes are not edges.
   Unsupported, ambiguous, unresolved, and external dependencies remain `open_edge`;
   no caller graph or recomputed digest may remove them or establish locality.
4. Use one catalog-derived provenance union for request-bound and request-independent
   outcomes. Every row is an observed typed `{schema, version, sha256}` identity or an
   `unobserved`/`null` suffix; no boolean-only or synthetic fixture values are allowed.
   The stage/code pair, outcome, manifest/publication, and exit projection are closed.
5. Make `next-process-launch-observation-v1` the sole process authority. v1 production
   covers macOS (`darwin`) and Linux (`linux`) only; Windows is a separate scope. The
   observation owns private cwd, exact env allowlist/denied set, pipe stdio, inherited FD
   closure, `shell=false`, process-group terminate/wait, verified executable identity,
   post-spawn equality, and TOCTOU fail-closed evidence. Split portable
   `stable_toolchain_fingerprint` from host `local_process_attestation_digest`; the
   latter retains host-ephemeral evidence while the former excludes it. Stable Node
   SemVer major >=22 is required; prerelease, older, or unparsable versions are
   `CSV-NEXT-NODE-001` unavailable.
6. Seal selected-copy publication once. A selected-output limit breach retains the
   semantic result and persisted artifact descriptor, but produces incomplete/exit 3,
   canonical `CSV-NEXT-LIMIT-003` stderr, and no partial stdout. Do not remeasure,
   rerender, or recopy a candidate; all public surfaces return final sealed bytes only.
7. Replace source-text coverage markers with an executable registry. Each Round 22 RG
   has a positive and negative vector, a callable producer, a validator, and a real
   mutation assertion. The fixture, reference validator, and focused tests must agree
   bidirectionally; missing, duplicate, unknown, unexecuted, or misassigned entries fail.

The complete acceptance map and First Red/Green evidence are recorded in
`artifacts/20260902t063000z-disc-round-22-strict-and-analysis-remediation.md`.
Focused tests run before the full contract suite, followed by full pytest, mypy, ruff,
SpecDock, pinned eight-diagram HTML validation, diff checks, an empty `src/**` diff, and
the no-`node_modules` check. Green local checks do not change the historical Strict
verdict or authorize production implementation; only a fresh same-SHA Strict pass with
`P0=0 / P1=0 / review_status=pass` can do so.
