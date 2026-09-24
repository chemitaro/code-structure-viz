---
種別: disc
ID: "20260924t085449z-disc"
タイトル: "Issue #8 I05-PLAN-008 Review Findings Analysis (GPT-5.6 Sol Pro Strict)"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-09-24"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: []
reflected_to: []
---

# 20260924t085449z-disc Issue #8 I05-PLAN-008 Review Findings Analysis (GPT-5.6 Sol Pro Strict)

## Provenance

- Stable analysis identity: `issue8-i05-plan008-readiness-findings-adjudication`.
- Exact branch: `iss-00008-generate-nextjs-component-snapshots`.
- Candidate, reviewed, tested, and GitHub branch-tip SHA: `1df6c4e8c8b76bf1ebc02590600d98f8fa6491a8`.
- Reviewer range: `977feb02c05b908d5a25a97181138abe1ef54bd9..1df6c4e8c8b76bf1ebc02590600d98f8fa6491a8`.
- Analyst Oracle session: `required-strict-github-connector-verificati-1121`; conversation `6ab4c16a-faa0-83e8-9c5d-696ff22ecbcc`; same-objective follow-up to `required-strict-github-connector-verificati-1107`.
- Requested/resolved analyst model: `gpt-5.6-sol`; Pro thinking was already selected and verified. Model-picker metadata for the follow-up was `skipped/unverified` due inherited same-conversation config; parent session metadata and the same conversation UI showed `GPT-5.6 Sol / 5.6 Pro`. Preserve this provenance nuance; do not claim a fresh model-picker verification on session 1121.
- Transcript artifact: `/Users/iwasawayuuta/.oracle/sessions/required-strict-github-connector-verificati-1121/artifacts/transcript.md`; whole transcript SHA-256 `45a01f2bfc7c619bedb1c016efe8b6ad3de2c54aebd2a4a962bb7eccce198609`.
- Primary evidence packet SHA-256: `a100cf4a2eb6e1dcc22dcc54f4291a6ad1cb134d75d4d4284ad91192c7ca8464`. GPT-6 source-native report SHA-256: `3e9400ee33f600f16ea748bf196b5cf5f7a5a6d595e2b6124b1806540ddb1382`. Strict reviewer JSON SHA-256: `97f1abe8d3feb49940d3a7cc25cde5e26a5dc9d8712f1d6f5aa99b249539b729`.
- The analyst independently verified exact GitHub branch tip and commit object through the Strict connector. The output is evidence/advice, not canonical authority or permission by itself.
- This artifact records the complete current findings batch and bounded remediation analysis. It does not mark I05-PLAN-008 or Issue #8 complete.

## Source-native Strict analyst decision packet

# Binding and evidence completeness

GitHub Connector で `chemitaro/code-structure-viz` の `refs/heads/iss-00008-generate-nextjs-component-snapshots` を直接取得し、branch tip の full object ID が `1df6c4e8c8b76bf1ebc02590600d98f8fa6491a8` であることを確認しました。これは指定された `expected_sha` と byte-for-byte で一致します。対象 commit object も同じ SHA で取得でき、その直接の親は前回分析対象の `457b6c0897fd21bc4b8fb3eb3054b59c480af782` です。既定 branch や別 branch へのフォールバックは行っていません。

| 項目                    | 確認結果                                                 |
| --------------------- | ---------------------------------------------------- |
| Repository            | `chemitaro/code-structure-viz`                       |
| Target branch         | `iss-00008-generate-nextjs-component-snapshots`      |
| Expected SHA          | `1df6c4e8c8b76bf1ebc02590600d98f8fa6491a8`           |
| GitHub branch-tip SHA | `1df6c4e8c8b76bf1ebc02590600d98f8fa6491a8`           |
| SHA comparison        | 完全一致                                                 |
| Candidate SHA         | `1df6c4e8c8b76bf1ebc02590600d98f8fa6491a8`           |
| Reviewed SHA          | Candidate と一致                                        |
| Tested SHA            | Candidate と一致                                        |
| Analysis identity     | `issue8-i05-plan008-readiness-findings-adjudication` |
| Continuity mode       | 同一目的の follow-up                                      |
| Comparison base       | `977feb02c05b908d5a25a97181138abe1ef54bd9`           |

一次 evidence packet は `20260924-plan008-review-batch-1df6c4e.md`、申告 SHA-256 は `a100cf4a2eb6e1dcc22dcc54f4291a6ad1cb134d75d4d4284ad91192c7ca8464` です。対象範囲、非目標、blocking policy、candidate、branch、clean worktree、CI、reviewer provenance、テスト結果が同じ packet 内で関連付けられています。

Review lineage は次のとおりです。

* ChatGPT Strict review は Oracle session `required-strict-github-connector-verificati-1113`、conversation `6ab4d4d9-5f60-83ee-9b66-f4fefb2b36bd`、GPT-5.6 Sol / Pro です。保存済み source-native JSON の SHA-256 は `97f1abe8d3feb49940d3a7cc25cde5e26a5dc9d8712f1d6f5aa99b249539b729` です。Reviewer 自身はローカルテストを実行せず、GitHub 上の exact commit と checked-in evidence を静的に確認しています。
* 独立 GPT-6 review は read-only agent `/root/issue8_plan008_gpt6_rereview_1df6c4e`、source-native report SHA-256 は `3e9400ee33f600f16ea748bf196b5cf5f7a5a6d595e2b6124b1806540ddb1382` です。Packet が保証するモデル表記は GPT-6 Astra / Max までで、具体的な picker 証拠と完了時刻は source report に含まれていません。
* Analyst lineage は前回の `required-strict-github-connector-verificati-1107`、conversation `6ab4c16a-faa0-83e8-9c5d-696ff22ecbcc` の同一目的 follow-up です。前回 candidate は `457b6c...`、前回出力 SHA-256 は `e9ce81aa76fbc043bd368ce92b1ce73f6c23cdd0cd31544c9c95155f36af2b6b` とされています。今回、前回の repository facts を無条件に再利用せず、現在の branch tip と現行コードを再取得しました。

GitHub Actions run `35970125988` は exact candidate SHA を head として完了し、結論は `success` です。Jobs endpoint は 7 jobs を返し、すべて完了成功として記録されています。

Evidence batch は、今回の意味論的 adjudication を開始するには十分です。Objective、固定 scope、source-native findings、再現条件、canonical authority、candidate-local tests、CI、prior remediation、非実施環境、同一 reviewer closure policy が含まれています。分類、claim validity、blocking effect、response route、authorization は独立に判断すべきであり、P1 や reviewer recommendation 自体を変更命令として扱ってはならない、という governing skill の境界も満たしています。

残る material evidence gap は次のとおりです。

* 一次 packet と supporting report の SHA-256 は caller 申告値であり、この analyst は原本ファイルから再計算していません。
* GPT-6 reviewer の具体的な model-picker provenance と完了 timestamp は source-native report にありません。
* Strict reviewer はローカルテストを実行していません。
* GPT-6 reviewer は focused checks を実行しましたが、full suite、mypy、Ruff 等を自身では再実行していません。
* Node spawn、production adapter resource resolution、OS process-boundary proof、installed-wheel runtime、consumer integration、release acceptance は未実施です。ただし、いずれも I05-PLAN-008 の明示的な非目標であり、今回の semantic adjudication を妨げる欠落ではありません。
* 初回 follow-up wrapper の `chat-mode-selection` 失敗は prompt 未送信の mechanical failure として記録されており、semantic finding には含めません。

# Executive disposition

**現在の batch には、source-native で合計 3 件の P1 があり、いずれも有効かつ到達可能です。ただし、独立した根本原因は 2 群です。**

1. acquisition phase をまたぐ際に、reader が確定した typed failure classification と実観測 prefix が catch block で上書きまたは吸収される implementation defect
2. ordinary package READ、actual integrity、および control／local-extends／program／context の typed failure propagation を現在の executable registry が falsify できない qualification defect

`G6-RR-2` と Strict reviewer の implementation 部分は同じ第1根本原因を指しています。`G6-RR-1` と Strict reviewer の coverage 部分は同じ第2根本原因を指しています。Strict reviewer の 1 件の P1 は複合 claim であり、2 件の新しい severity に分割したものではありません。

親 policy 上、いずれかの有効な P1 が存在する限り、candidate `1df6c4e8...` と I05-PLAN-008 は blocked です。Green CI、full pytest、focused tests は重要な回帰証拠ですが、到達可能な counterexample と executable-coverage gap を反証しません。P0/P1 は certification を block しますが、それ自体は修正 authorization ではなく、authorization は別途 parent boundary から確認する必要があります。

主要 response route は次のとおりです。

| Root-cause group | Primary route                |
| ---------------- | ---------------------------- |
| `RCG-I05-004`    | `implementation-remediation` |
| `RCG-I05-005`    | `test-remediation`           |

Current-v1 requirement、design、plan は、failure code／stage の保持、実観測 prefix の保持、integrity の fatal terminal behavior、current registry の executable bidirectional coverage を一意に要求しています。したがって、現時点では新しい requirement、state model、public API、security policy、compatibility policy を選ぶ人間判断は不要です。

ユーザーが Issue #8 の継続実装と artifact 更新を明示的に認可しているため、Current-v1 の既存意味を復元する bounded remediation は authorized です。ただし、安全に進行できる範囲はこの remediation と exact-SHA verification に限定されます。I05-PLAN-002～007 の production adapter／Node work は引き続き開始できません。

前回 batch の次の findings は current reviewers により成立確認済みであり、今回の current item として再オープンしません。

* pre-seal package failure 6 種類 × 4 selectors の publication
* diagnostic path の source evidence への拘束
* unequal dual direct declarations
* 既存追加 vector の個別 mutation rejection

これらは今回の regression sweep 対象には含めますが、新しい remediation root cause としては扱いません。

# Root-cause groups

前回 decision packet の `RCG-I05-001`～`RCG-I05-003` を安定 ID として予約したまま、今回新たに確認された根本原因へ次の ID を割り当てます。

| Group ID      | Source item                                              | Source-native classification | 根本原因                                                                                                                                                                           | Primary route                | Authorization |
| ------------- | -------------------------------------------------------- | ---------------------------: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------- | ------------- |
| `RCG-I05-004` | `G6-RR-2`、Strict review の sole P1 の implementation claim |                        P1、P1 | `ReferenceSourceFailureKind` と元の code/stage/path が phase-local catch で上書きまたは `failed_paths` へ吸収され、terminal integrity と typed limit/path-safety outcome が失われる                   | `implementation-remediation` | Authorized    |
| `RCG-I05-005` | `G6-RR-1`、Strict review の sole P1 の coverage claim       |                        P1、P1 | Current RG-01 registry が package の 6-case subset のみを実行し、ordinary READ、actual integrity、非package phase propagation を producer／validator／substantive test／mutation の閉じた組として検証しない | `test-remediation`           | Authorized    |

`G6-RR-1` と `G6-RR-2` は grouping しません。前者は qualification evidence が誤った実装を検知できない問題で、後者は実際の control/data path が誤る問題です。Implementation を修正しても registry gap は残り、registry を拡充しても現在の誤分類は直りません。

Strict reviewer の 1 件の P1 は、本文中で implementation propagation と coverage 不足の双方を述べています。そのため同じ source finding ID を 2 group に関連付けますが、source-native finding 数や severity を二重計上しません。

Material coverage gap は `RCG-I05-005` に包含します。別の P severity は付与しません。

# Detailed adjudication

## `RCG-I05-004` — acquisition phase 間で typed failure authority が失われる

### Claim validity

**有効です。**

Current `InstrumentedSourceReader.read()` は `ReferenceSourceFailureKind` を、次の typed public projection に変換します。

* `ORDINARY_READ` → `CSV-NEXT-SOURCE-001 / source_read`
* `TOO_LARGE`、`TOO_MANY_FILES` → `CSV-NEXT-LIMIT-001 / source_read`
* `UNSAFE_PATH`、`SYMLINK`、`NON_REGULAR`、`RACED_MISSING` → `CSV-NEXT-SOURCE-003 / source_read`
* `INTEGRITY_DRIFT` → `CSV-NEXT-SOURCE-INTEGRITY-001 / source_integrity`

この時点では failure kind、code、stage、catalog-permitted path が typed evidence として保持されています。

一方、`seal_source_acquisition()` の phase-local catch は次の動作です。

* root package phase は `ORDINARY_READ` だけを `CSV-NEXT-APPLICABILITY-002 / applicability` に変換し、その他はそのまま再送出します。この部分は Current-v1 と整合しています。
* root config／local extends の control queue は、すべての `SourceAcquisitionError` を捕捉して stage を `source_control` に書き換えます。`CSV-NEXT-LIMIT-001` や `CSV-NEXT-SOURCE-INTEGRITY-001` に `source_control` を組み合わせると、closed decision matrix に存在しない pair になります。
* program／context read は、`allow_partial=True` の場合に failure kind を問わず `failed_paths` へ格納します。このため limit や integrity も通常の isolatable source failure のように扱われ、後続で source seal と `CSV-NEXT-SOURCE-003 / source_read` に変質できます。

`seal_source_acquisition_result()` は、例外として `source_integrity` が到達した場合には正しく `SourceIntegrityFatal` を作成します。しかし control catch が stage を変更した場合、または program/context catch が例外を吸収した場合、その terminal branch へ到達しません。

GPT-6 reviewer の実再現では、root config の `TOO_LARGE`／`INTEGRITY_DRIFT` が不正な `source_control` pair となり assertion、program source の同 failure が `CSV-NEXT-SOURCE-003 / source_read` に変質しました。Program integrity は全 selectors で finalizer まで進み、exit 3、manifest あり、seal ありになっています。これはコードパスと一致する再現です。

### Trigger reachability

Trigger は通常の reference harness から到達可能です。

* selected `tsconfig.json` の read
* arbitrary-name の local `extends` target read
* program file read
* context `.d.ts` read

いずれも `InstrumentedSourceReader(..., read_failures={path: failure_kind})` と `seal_source_acquisition_result()` だけで到達します。特殊な monkey patch、invalid API、production Node、filesystem race の実環境は不要です。

### In-scope impact

影響は I05-PLAN-008 の data-only reference authority 内です。

* `CSV-NEXT-LIMIT-001` が closed stage/code pair を失い assertion する
* integrity failure が fatal exit 1 ではなく domain incomplete exit 3 になる
* integrity failure で manifest、source seal、finalizer/publication path が発生する
* path-safety／symlink／non-regular／raced-missing が本来の typed evidence を失い得る
* actual observed prefix と public provenance が一致しなくなる
* 将来実装者へ誤った reference contract を渡す

したがって、production adapter が未実装であっても readiness gate を無効にする in-scope defect です。

### Blocking effect

`G6-RR-2` と Strict review の implementation claim はともに P1 です。親 policy により I05-PLAN-008 を block します。Severity を変更する根拠はありません。

### Violated authority and exact proposition

違反している Current-v1 proposition は次のとおりです。

1. root package の通常 READ だけが APP-002/applicability へ変換され、limit、integrity、path-safety、symlink、non-regular、raced-missing は既存の typed code/stage を維持する。
2. source-integrity drift は `CSV-NEXT-SOURCE-INTEGRITY-001`、exit 1、manifest／Artifact なしの run-level terminal branch であり、decoder／finalizer／artifact read を呼ばない。
3. provenance は実際に観測された prefix を保持し、failure 後の suffix だけを `unobserved/null` にする。
4. 全 public surface は同一 decision から投影し、catch block が別 status や別 evidence を再構築しない。

### First incorrect fault layer

最初に誤っている layer は **reference implementation** です。

Requirement と design は typed failure preservation と integrity terminal behavior を既に固定しています。最初の逸脱は `seal_source_acquisition()` の control/program/context catch です。Schema が中間 observed prefix を十分表せない点は downstream の補助的 defect ですが、元の failure kind が catch 時点で失われることが最初の fault です。

### Root cause

根本原因は、次の二つの意味を一つに潰していることです。

* failure の意味を決める reader-owned typed classification
* failure が発生した acquisition phase と、そこで観測済みの evidence prefix

Control catch は phase を public failure stage に上書きし、program/context catch は「partial にできる ordinary read failure」と「global typed failure」を区別せず同じ `failed_paths` に格納しています。

さらに現在の `EarlySourceReadPrefix.provenance()` は public `stage` から observed prefix を推定しています。`source_read` stage の failure が package、control、program/context のどこで起きたかを区別できないため、stage と evidence completeness を誤って同一視しています。

### Primary response route

**`implementation-remediation`**

Accepted requirement と canonical design が一意であり、reference implementation がそれに違反しています。新しい outcome や public discriminator を選ぶ必要はありません。

### Preserved guarantees

* root package ordinary READ の APP-002 special case
* existing diagnostic codes、stages、path permission
* ordinary program/context read の既存 partial-safe／payload-unavailable 判定
* actual bytes の read-once と no post-seal read
* fail-closed behavior
* raw source、OS error、private path の非公開
* existing public schema identity `v1`
* four selectors の同一 terminal/publication semantics
* no production Node／adapter work

### Changed behavior

* typed non-ordinary failure を phase-local catch で変換しない
* integrity はすべての read phase から terminal fatal branch へ到達する
* limit/path-safety failure は actual code/stage/path と実観測 prefix を持つ pre-seal unavailable result になる
* program/context の `failed_paths` へ入るのは、既存 authority が局所隔離を認める ordinary read failure に限定される
* provenance が stage だけでなく実際の reader-owned phase evidence から導出される

### Missing evidence

現 candidate では、config、local extends、program、context の各 phase に全 typed failure family を注入した executable matrix はありません。したがって、修正後の exact observed-prefix shape は First Red と Current-v1 proposition から確定し、同一 final SHA で検証する必要があります。

## `RCG-I05-005` — Current registry が failure taxonomy を実行可能に証明しない

### Claim validity

**有効です。**

Current `runtime_vector_registry` は 20 records です。RG-01 には次の 3 positive/negative pair が登録されています。

* base applicability
* unequal dual applicability
* pre-seal package failure matrix

ただし、`runtime_vector_round22_preseal_package_failure_matrix()` が実行するのは次の 6 種類だけです。

* `TOO_LARGE`
* `TOO_MANY_FILES`
* `UNSAFE_PATH`
* `SYMLINK`
* `NON_REGULAR`
* `RACED_MISSING`

`ORDINARY_READ` と `INTEGRITY_DRIFT` は含まれません。Mutation は先頭 row の stage/code を変更するだけで、ordinary-read special case や actual integrity path を独立に falsify しません。

Fixture の `round22.rg-01` substantive mapping は次の 3 tests です。

* `test_round22_applicability_dual_declarations_and_malformed_projection`
* `test_round22_applicability_unequal_dual_declarations_are_applicable`
* `test_preseal_package_source_read_failure_reaches_publication`

8-class test `test_package_read_failure_preserves_its_distinct_reference_outcome` は mapping に含まれていません。また、6-class publication test 自体も ordinary READ と integrity を含みません。

既存の `runtime_vector_round22_integrity()` は `SourceIntegrityFatal` を直接構築して projection を検証しています。Actual reader から package/control/program/context を経て terminal result に到達する経路は実行しないため、`RCG-I05-004` の catch defect を検出できません。

GPT-6 reviewer は、ordinary package READ の条件をメモリ内で壊しても current 20 vectors と RG-01 mapped tests がすべて pass することを確認しています。この mutation は coverage claim の直接的な falsification evidence です。

### Trigger reachability

Trigger は次のいずれかの regression です。

* ordinary root package READ を APP-002 へ変換しなくなる
* non-ordinary package failure を APP-002 へ誤変換する
* actual package integrity を fatal terminal にしない
* control/local-extends/program/context の typed limit/integrity/path-safety を generic failure へ潰す
* integrity を `failed_paths` に吸収する

Current registry は producer が該当 branch を通らないため、上記 regression が存在しても自己整合した fixture と validator のまま green になり得ます。

### In-scope impact

G09 の machine-checkable trace が不完全です。I05-PLAN-008 は reference behavior のみでなく、criterion、positive/negative vectors、actual callable producer、validator、substantive test の bidirectional correspondence を gate としています。したがって、通常 unit test が別の場所に存在するだけでは readiness evidence として不十分です。

### Blocking effect

`G6-RR-1` は source-native P1 です。Strict reviewer の sole P1 も同じ coverage 不足を含みます。また、仮に severity のない独立 coverage gap として扱っても、親 policy では material executable-coverage gap が block します。新しい severity は付与しません。

### Violated authority and exact proposition

違反命題は次のとおりです。

1. Current registry の各 criterion は、positive/negative vector、actual callable producer、validator、substantive test の実行可能な対応を持つ。
2. Source code 中の名前や別 criterion の unit test は、current producer を実行する evidence の代用にならない。
3. Historical Round 23 registry を current coverage の fallback にしない。
4. Integrity の fixture-only direct construction から actual acquisition propagation の正しさを推論しない。

### First incorrect fault layer

最初に誤っている layer は **test／fixture qualification** です。

Product/reference behavior の修正は `RCG-I05-004` が所有します。本 group は、その behavior が再び壊れたときに current G09 gate が fail するための executable evidence を所有します。

### Root cause

Root cause は、failure taxonomy を「package の 6 non-ordinary cases」という狭い enumeration として登録し、次の dimension を registry identity に含めなかったことです。

* read phase
* ordinary versus non-ordinary
* terminal versus domain-unavailable
* actual acquisition path versus synthetic result construction
* publication/finalizer の有無

その結果、fixture registry は自分が記録した 20 vectors の整合性は検証できますが、authority が要求する未登録 branch の欠落を検知できません。

### Primary response route

**`test-remediation`**

Current authority を変えず、producer／vector／validator／mapping／mutation を補完します。Reference implementation を coverage に合わせて歪めてはなりません。

### Preserved guarantees

* current／historical registry 分離
* Round 23 の non-normative status
* actual callable resolution
* positive／negative polarity pairing
* fail-closed validator
* current criterion IDs
* production behaviorを test convenience のために変更しないこと

### Changed evidence

* ordinary package READ を実 acquisition から生成する current producer が追加される
* actual package integrity を reader から terminal projection まで通す producer が追加される
* control／local-extends／program／context の typed failure matrix が executable になる
* 各 normative branch を独立に壊す mutation が gate を red にする
* 8-class substantive test と phase-specific tests が該当 criterion へ mapping される

## Current prior findings の扱い

前回の `RCG-I05-001`～`RCG-I05-003` に相当する findings は、今回の reviewers が修復を確認しています。したがって、現在の open group へ統合しません。ただし、同じ source-acquisition authority の adjacent-path regression として re-review completion sweep には残します。

# Integrated response design

## Governing invariant

今回の response 全体を支配する invariant は次の一文です。

**Reader が確定した immutable failure kind と実際の read-phase evidence が唯一の classification/provenance authority であり、phase-local catch、partial-safe routing、publication writer、fixture registry はそれを再分類または再構築しません。**

## Required state transitions

| Read phase                  | Ordinary READ                                                | Limit                                          | Integrity drift                       | Path-safety／symlink／non-regular／raced-missing   |
| --------------------------- | ------------------------------------------------------------ | ---------------------------------------------- | ------------------------------------- | ----------------------------------------------- |
| root package                | APP-002 / applicability / no public path                     | LIMIT-001 / source_read / pre-seal unavailable | SOURCE-INTEGRITY-001 / fatal terminal | SOURCE-003 / source_read / pre-seal unavailable |
| root config / local extends | 既存 source-control unavailable semanticsを維持                   | LIMIT-001 / source_read / pre-seal unavailable | SOURCE-INTEGRITY-001 / fatal terminal | SOURCE-003 / source_read / pre-seal unavailable |
| program / context           | 既存の locality proof に基づき partial-safe または payload-unavailable | LIMIT-001 / source_read / pre-seal unavailable | SOURCE-INTEGRITY-001 / fatal terminal | SOURCE-003 / source_read / pre-seal unavailable |

Ordinary program/context READ だけが existing failure ledger／safe-subset path に参加できます。Non-ordinary global or typed failuresを `failed_paths` へ入れてはいけません。

## Observed-prefix design

Current public provenance fieldsと4-kind unionはそのまま使用できます。ただし、`source_read` という public stage だけから evidence completeness を推論してはなりません。

| Actual point of failure       | Observed public identities                             | Must remain unobserved                             |
| ----------------------------- | ------------------------------------------------------ | -------------------------------------------------- |
| package preflight             | applicability read-attempt prefix                      | config、source、limits、source-plan、request、runtime以降 |
| root config / local extends   | applicability、actual config read-attempt prefix        | source、limits、source-plan、request、runtime以降        |
| program / context before seal | applicability、config、actual source read-attempt prefix | unsealed plan、limits、request、runtime以降             |
| sealed source-read failure    | applicability、config、source、limits、source-plan         | request、runtime/toolchain/process/response/budget  |
| integrity terminal            | terminal diagnosticだけ                                  | domain/root manifest、Artifact、finalizer input      |

Private implementationには、`EarlySourceReadPrefix` または同等の immutable evidence object に、public failure stage と独立した acquisition phase／observed-surface witness が必要です。名称は非canonicalですが、次の条件を満たす必要があります。

* actual reader の captured/failed rows だけから導出する
* local extends の任意 filename を suffix や path-name heuristics で誤分類しない
* raw bytes を public provenance に出さず、safe canonical identity digest のみを出す
* source plan や seal を合成しない
* diagnostic path を同じ evidence object に拘束する

Schema は新しい public field を追加せず、既存 `observed` map の許容 shape を authority-required prefix に合わせます。具体的には、request-independent `source_read` について次を区別できる必要があります。

* applicability-only
* applicability + config
* applicability + config + pre-seal source observation
* sealed full source prefix

これは state-model の新設ではなく、既存の「実観測 prefix を消さない」という Current-v1 meaning の実装です。

## Ordered coherent response

1. **First Red を追加する**

   * root config、local extends、program、context の各 phase へ limit、integrity、path-safety family を注入する。
   * ordinary package READ と actual package integrity を current registry 経由で破壊できる mutation を追加する。
   * integrity が seal/finalizer/publicationへ入る現状を red として固定する。

2. **Typed failure routing を一箇所に集約する**

   * Package ordinary READ の special case だけを明示的に変換する。
   * Control ordinary READ の既存意味だけを phase-specific に処理する。
   * Program/context ordinary READ だけを locality path へ渡す。
   * Limit、integrity、path-safety family は元の code/stage/path を保持して再送出する。

3. **Actual phase evidence を保持する**

   * `EarlySourceReadPrefix` か同等 object へ phase witness を保持する。
   * Public provenance をその evidence から導出する。
   * Stage から observation prefix を逆算する既存 assumption を除去する。

4. **Terminal integrity を acquisition boundary で閉じる**

   * `SourceIntegrityFatal` に変換した後は source seal、decision finalizer、domain/root manifest、Artifact read を実行しない。
   * 全4 selectors で exit 1 と terminal stderr を同じ branch から生成する。

5. **Current public schemas と reference validators を揃える**

   * Authority-required intermediate prefix だけを additive に許容する。
   * Fabricated mixed prefix、synthetic plan/seal、invalid code/stage pair は引き続き拒否する。

6. **Current registry を拡張する**

   * ordinary package READ の actual producer と独立 mutation
   * actual package integrity の producer と独立 mutation
   * control/local-extends/program/context の typed failure producer
   * catch-all collapse を検知する mutation
   * substantive test mapping
   * existing synthetic integrity vector は残してもよいが、actual acquisition evidence の代用として数えない

7. **Focused、aggregate、exact-SHA review gate を実行する**

## Affected surfaces

* `tests/contracts/next_reference_validation.py`
* `tests/contracts/test_next_contracts.py`
* `tests/fixtures/next_contract_vectors.json`
* `schemas/next-provenance-v1.schema.json`
* 必要な場合のみ `schemas/next-run-decision-v1.schema.json`
* 必要な場合のみ `schemas/next-config-v1.schema.json`
* mechanically stale になった current registry 件数／mapping を記録する Current-v1 documentation

## Unaffected surfaces

* `src/**` の production adapter implementation
* Node process launch
* dependencies、lockfiles、wheel/sdist
* public schema identity/version
* diagnostic catalog meaning
* target grammar
* semantic entity model
* I05-PLAN-002 の verified-FD decision
* historical Round 23 registry
* Issue #8 completion status

## Compatibility and operational boundary

既存 valid documents は引き続き valid でなければなりません。新しく valid になるのは、Current-v1 が既に要求している actual pre-seal evidence prefix だけです。Consumer-visible field、code、stage、outcome、exit、path permission は変更しません。

Data migration、persistent-state migration、runtime deployment、recovery procedure はありません。Rollback は remediation commit 一式の atomic revert で可能ですが、schema、reference、fixture、tests の一部だけを戻して不一致状態を作ってはいけません。Rollback 後の `1df6c4e8...` は既知 P1 を持つ blocked candidate であり、readiness pass には戻りません。

## Structural stop signals

次のいずれかが発生した場合は patch chaining を停止し、human decision へ戻します。

* 第5の provenance kind が必要になる
* 新しい public discriminator、field、schema version が必要になる
* accepted failure code、stage、outcome、path permission を変更する必要がある
* ordinary READ の既存 partial-safe meaningを変更する必要がある
* synthetic seal／source plan／applicability matrix が必要になる
* production adapter、Node、OS process boundary、dependency、package変更が必要になる
* phase ごとに独立 shim／exception branch を追加し続け、typed failure の単一 owner を説明できなくなる
* public/config/provenance authorityを同時に満たせない

# Human decisions and authorization

Parent authorization は、ユーザーが Issue #8 の継続実装、artifact 更新、検証済み scoped changes の commit/push を許可したことに由来します。P1 classification や reviewer recommendation 自体は authorization ではありません。Governing skill も、reported classification、validity、blocking、route、authorization を分離し、material meaning change は人間へ返すことを要求しています。

今回の correction は、既存 authority から一意に決まります。

* ordinary root package READ だけを APP-002 にする
* typed limit／integrity／path-safety class を保持する
* integrity を fatal terminal にする
* observed prefix を実 evidence から導出する
* executable registry を全 normative branch に接続する

したがって、**現時点では human decision は不要です。**

次の事項は変更しません。

* objective と fixed scope
* public API／schema identity
* security、privacy、redaction
* data semantics
* migration、rollback、recovery
* compatibility guarantee
* operational guarantee
* risk acceptance
* responsibility allocation
* source of truth

次のいずれかが判明した時点で implementation authorization は停止します。

* existing four-kind union では authority-required result を表現できない
  -新しい public state、schema version、compatibility contract が必要
* integrity の terminal meaningを変える必要がある
* production/lower-layer contract変更が必要
* current requirement、design、plan の間に material contradiction がある

その場合に限り、`design-decision-required` または `requirement-decision-required` として parent へ返します。

# Implementation handoff

**Bounded implementation handoff は authorized です。**

## Objective

Verified base `1df6c4e8c8b76bf1ebc02590600d98f8fa6491a8` から、reader-owned typed failure classification と actual phase evidence を control／local-extends／program／context まで保持し、actual integrity を terminal fatal として閉じ、current executable registry が ordinary READ、integrity、cross-phase failure propagation を独立に falsify できるようにします。

## Exact verified paths and symbols

### `tests/contracts/next_reference_validation.py`

* `EarlySourceReadPrefix`
* `ReferenceSourceFailureKind`
* `_REFERENCE_SOURCE_FAILURES`
* `InstrumentedSourceReader.read`
* `InstrumentedSourceReader.early_read_prefix`
* `seal_source_acquisition`
* `seal_source_acquisition_result`
* `SourceAcquisitionUnavailable`
* `SourceIntegrityFatal`
* `source_acquisition_result_decision`
* `next_terminal_run_publication`
* `_expected_provenance_observed`
* `validate_stage_dependent_provenance`
* `RUNTIME_VECTOR_REGISTRY`
* `runtime_vector_round22_preseal_package_failure_matrix`
* `runtime_vector_round22_preseal_package_failure_matrix_mutation`
* `runtime_vector_round22_integrity`
* `validate_preseal_package_failure_matrix`
* 新しい current-only producer／mutation／validator

Current control catch と program/context catch が typed failure を失う位置は exact candidate で確認済みです。

### `schemas`

* `schemas/next-provenance-v1.schema.json`
* 必要な場合のみ `schemas/next-run-decision-v1.schema.json`
* 必要な場合のみ `schemas/next-config-v1.schema.json`

現 schema は `source_read` を applicability-only early prefix または sealed full prefix として扱っており、control／program/context の pre-seal intermediate prefix は表現できません。

### `tests/contracts/test_next_contracts.py`

* `test_package_read_failure_preserves_its_distinct_reference_outcome`
* `test_preseal_package_source_read_failure_reaches_publication`
* `test_actual_early_failure_preserves_observations_through_publication`
* `test_round22_runtime_registry_executes_vectors_and_named_validators`
* integrity terminal selector tests
* control/local-extends/program/context classification matrix tests
* catch-all mutation tests

### `tests/fixtures/next_contract_vectors.json`

* `coverage_mapping["round22.rg-01"]`
* 必要に応じて `coverage_mapping["round22.rg-06"]`
* `runtime_vector_registry`
* current positive catalog
* current negative catalog

Historical Round 23 recordsは変更せず、current producer として解決してはいけません。

## Ordered changes

1. **First Red**

   * root package ordinary READ mutation
   * actual package integrity mutation
   * root config、local extends、program、context の limit/integrity injection
   * generic catch-all reclassification mutation
   * four-selector integrity terminal assertions

2. **Single typed-failure routing**

   * reader-generated failure kind を保持する private phase-aware helper を `seal_source_acquisition` 近傍に置く
   * package ordinary READ のみ APP-002 へ変換する
   * control ordinary READ の existing behaviorを維持する
   * program/context ordinary READ のみ partial-safe candidate にする
   * non-ordinary typed failuresをそのまま outer result boundaryへ渡す

3. **Phase evidence**

   * `EarlySourceReadPrefix` または同等 object に actual phase witness を保持する
   * package/control/source observation identityを実際の captured/failed rows から導出する
   * filename suffix や public stage だけから phase を推定しない

4. **Provenance/schema**

   * source-read independent failure の exact allowed prefix を schema と reference validator に追加する
   * early、control-prefix、source-prefix、sealed-prefix の間に fabricated mixed state を許さない
   * source plan、limits、seal を合成しない

5. **Terminal integrity**

   * every phase の `INTEGRITY_DRIFT` を `SourceIntegrityFatal` にする
   * `next_terminal_run_publication` より後の finalizer／manifest path に渡さない

6. **Registry**

   * ordinary package READ actual producer + mutation
   * actual package integrity producer + mutation
   * phase-specific typed-failure producers + mutations
   * substantive tests を current criterion に mapping
   * existing 8-class test を executable coverage に接続
   * current registry 件数を事実に合わせて更新

7. **Regression and exact-SHA evidence**

   * focused tests
   * schema/contract tests
   * full suite
   * static checks
   * exact-SHA CI
   * fresh same-reviewer reviews

## Explicit non-goals

* production adapter／Node implementation
* `src/**` の機能拡張
* dependencies、lockfiles、wheel、sdist
* public schema version変更
* failure code／stage／outcome変更
* diagnostic path/redaction変更
* target semantics変更
* historical Round 23 の current 化
* I05-PLAN-008 pass や Issue #8 completion の宣言

## Preserved guarantees

* fail closed
* read once
* no synthetic evidence
* immutable reader authority
* actual observed prefix
* no raw content publication
* exact diagnostic path ownership
* terminal integrity
* current/historical registry separation
* same-reviewer closure
* no production work before Plan-008 pass

## Prohibited choices

* control failureを一律 `source_control` へ再包装する
* `allow_partial` で non-ordinary failure を `failed_paths` へ入れる
* integrityを exit 3 + manifest にする
* empty or synthetic seal を作る
* source plan／limits／config resolutionを未観測から合成する
* public stage だけで evidence prefix を決める
* local extends を filename suffix で分類する
* direct `SourceIntegrityFatal(...)` fixtureだけで actual reader path の coverage とみなす
* historical R23 producerで current gap を埋める
* source-text markerや test-name existence を executable evidence とみなす

## First-red evidence

最低限、次を remediation 前に red として記録します。

1. `tsconfig.json` + `TOO_LARGE`
2. local extends target + `TOO_LARGE`
3. program file + `TOO_LARGE`
4. context file + `TOO_LARGE`
5. 上記各 phase + `INTEGRITY_DRIFT`
6. path-safety family が generic SOURCE-003 以外へ誤変換される mutation
7. package ordinary READ の APP-002 condition mutation
8. package actual integrity の terminal mutation
9. missing producer／validator／mapping／negative pair を current registry が拒否すること
10. integrity が全4 selectorsで seal/finalizer/manifest に到達しないこと

## Stop-and-return conditions

以下に該当したら実装を停止し、parentへ返します。

* Current-v1 authority contradiction
* 新しい public kind／field／schema version が必要
* accepted code/stage/outcome変更が必要
* ordinary program/context partial-safe meaningの変更が必要
* security、privacy、path-publication変更が必要
* production/lower-layer API変更が必要
* data、migration、compatibility、rollback、recovery、operationsへの影響
* verified path/symbol が実装 base に存在しない
* exact branch tip が implementation base と不一致
* prior closed findings が再発し、今回の root cause では説明できない

## Evidence return destination and format

Implementer は parent I05-PLAN-008 workflow へ、次を含む一つの Markdown evidence packet を返します。

* base full SHA と resulting full SHA
* changed paths/symbols
* First Red の command、exact result、failure reason
* focused green、aggregate green、static checks
* phase × failure-kind matrix
* selector × terminal/publication matrix
* provenance prefix accepted/rejected matrix
* current registry records、producer、validator、mapping、mutation
* CI run ID と exact head SHA
* prior findings regression results
* handoff からの deviation、または `none`
* unresolved evidence、または `none`

Parent が artifact persistence、commit、push、reviewer invocation、workflow transition、closure を所有します。

# Verification plan

## Supplied results for current candidate

次の結果はすべて candidate `1df6c4e8c8b76bf1ebc02590600d98f8fa6491a8` に binding しています。ただし、既知 P1 の修復証拠ではありません。

| Lane                           | Supplied result                                                                                        |
| ------------------------------ | ------------------------------------------------------------------------------------------------------ |
| Focused contract module        | 585 passed                                                                                             |
| Schema + Next contract modules | 704 passed                                                                                             |
| Full suite                     | 1757 passed、1 skipped                                                                                  |
| Ruff                           | check / format passed                                                                                  |
| Mypy                           | 150 source files passed                                                                                |
| SpecDock                       | `nodes=10` passed                                                                                      |
| Whitespace                     | passed                                                                                                 |
| Pinned HTML / PlantUML         | passed                                                                                                 |
| GitHub Actions                 | Run `35970125988`, 7/7 success                                                                         |
| GPT-6 focused read-only checks | 60 contract PASS、9 related unit PASS、whitespace PASS                                                   |
| Strict reviewer                | Static exact-commit review、local test未実行                                                               |
| Prior remediation checks       | pre-seal six-case publication、diagnostic-path binding、unequal dual、existing vector mutations confirmed |

Candidate-local gates と review provenance は packet に記録されています。

## Future First Red and focused falsification

すべて resulting candidate full SHA に binding させます。

### Classification matrix

各 read phase に対し、少なくとも次を injection します。

* ordinary read
* too large
* too many files
* unsafe path
* symlink
* non-regular
* raced missing
* integrity drift

Phases:

* root package
* root config
* local extends
* program
* context

各 case で次を確認します。

* exact result type
* exact diagnostic code
* exact stage
* exact path/null
* actual read counts
* seal count
* observed prefix
* manifest availability
* exit code

### Integrity terminal matrix

全4 selectors:

* selector omitted
* `manifest`
* `next:semantic-json`
* `next:plantuml`

Assertions:

* exit 1
* no run/domain manifest
* no semantic/PlantUML Artifact
* no source seal
* no finalizer call
* no artifact read
* catalog-backed stderr
* no raw error/path when permission is none

### Limit/path-safety publication

* exit 3
* payload unavailable
* no semantic/PlantUML Artifact
* no synthetic seal/plan
* exact code/stage/path
* actual prefix only
* raw source bytes absent
* four selectors share the same immutable decision

### Mutation coverage

Independently mutate:

* ordinary package READ special case
* non-ordinary package reclassification
* integrity stage
* integrity terminal outcome
* control catch stage overwrite
* program/context catch-all absorption
* path permission
* observed-prefix completeness
* registry producer name
* validator name
* polarity
* criterion mapping
* missing substantive test
* missing positive/negative counterpart

Each mutation must make the corresponding gate red.

## Aggregate regression checks

Resulting SHA に対して次を実行します。

* focused new tests
* `tests/contracts/test_next_contracts.py`
* `tests/contracts/test_json_schemas.py`
* full pytest
* mypy
* Ruff format/check
* SpecDock validation
* `git diff --check`
* pinned HTML/PlantUML checks
* current runtime registry full execution
* clean worktree
* local HEAD／upstream／GitHub branch-tip equality
* exact-SHA GitHub Actions all required jobs

## Integration/runtime evidence

I05-PLAN-008 における integration evidence は data-only reference chain です。

* actual reader
* typed acquisition result
* provenance
* run decision
* config/domain projection
* terminal or publication decision
* root manifest
* stdout/stderr/exit
* current registry

Actual Node、production adapter、installed wheel、OS process boundary は今回の completion evidence には含めません。

## Semantic checkpoints

* Ordinary root package READ だけが APP-002
* Non-ordinary package failureは元の classを保持
* Control/local-extends/program/context でも typed failureを保持
* Program/context ordinary READ だけが locality-based partial pathへ入る
* Integrityは常に fatal terminal
* Pre-seal prefixは actual read evidence から導出
* Seal-less failureに source plan、limits、request、runtimeを合成しない
* Sealed failureは既存 full prefixを維持
* Diagnostic pathは actual evidence-owned path または null
* Current registry は actual producerを実行
* Historical R23 は current executorから到達不能
* Prior fixed findingsは再発しない

## Negative assertions

次を拒否します。

* `LIMIT-001 / source_control`
* `SOURCE-INTEGRITY-001 / source_control`
* integrityを `failed_paths` へ格納
* pre-seal failureに source seal を付与
* intermediate prefix に fabricated source-plan digestを付与
* actual config read後に applicability-only prefixへ縮退
* actual source read-attempt後に source observationを消去
* unread diagnostic path
* pathless permission に pathを付与
* ordinary READとnon-ordinary failureの同一分類
* direct synthetic terminal fixtureだけで actual acquisition coverageを満たしたとすること
* historical producerによる current criterion充足

## Rollback verification

* Existing valid Current-v1 vectors がすべて pass
* Prior six pre-seal package failure publicationが byte/semantic stable
* Diagnostic-path substitution rejectionが維持
* Unequal dual applicabilityが維持
* Sealed source-read prefix publicationが維持
* Remediationの typed-routingを除去すると First Red が再現
* New producer/mapping/mutationを1件除去すると registry gate が fail
* No persistent migration／package migration／operational rollback が発生しない

# Same-reviewer re-review obligations

すべて resulting pushed exact SHA で実施します。

## Independent GPT-6 Astra / Max reviewer

| Source finding | Group         | Required independent re-check                                                                                                                                           | Current status |
| -------------- | ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------- |
| `G6-RR-1`      | `RCG-I05-005` | Ordinary package READ と actual package integrity の producer／positive-negative vector／validator／substantive mappingを確認し、それぞれの独立 mutation で current gate が fail することを確認する | Still open     |
| `G6-RR-2`      | `RCG-I05-004` | root config、local extends、program、context の limit/integrity/path-safety injectionを再実行し、typed class、prefix、terminal/publication behaviorを確認する                            | Still open     |

Completion sweep:

* package ordinary READ
* package six non-ordinary pre-seal failures
* package actual integrity
* root config
* local extends
* program
* context
* all four selectors
* no-seal versus sealed source-read
* diagnostic-path binding
* prior unequal-dual fix
* registry missing-record/mapping/mutation rejection

Expected outcome は **closure expected after remediation** ですが、同 reviewer が fresh exact-SHA で確認するまでは open です。

Disproof として認められるのは、現在の reproducer が exact candidate では到達不能であることを independent evidence が示した場合だけです。現時点のコードと再現証拠は disproof を支持しません。

Supersession は、承認済み canonical contract change が存在する場合だけです。今回その authorization はありません。

## ChatGPT Strict reviewer

| Source finding                                   | Group                       | Required independent re-check                                                                                                                                                       | Current status |
| ------------------------------------------------ | --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------- |
| Sole Strict P1: `package以外でもread failure種別を保持する` | `RCG-I05-004`、`RCG-I05-005` | Phase-local catch が typed class を保持すること、integrity terminal、current registry の package/non-package paired vectors、substantive tests、independent mutations、R23非利用を exact commit で確認する | Still open     |

Strict reviewer は implementation と coverage の両方を確認する必要があります。一方だけの修正では source finding を閉じられません。

## Closure states

* **Expected closure:** authorized remediation が authority と一致し、same reviewer が fresh SHA で確認
* **Disproof:** exact evidence により trigger または claim が成立しないと確認
* **Supersession:** approved canonical contract change により finding の前提が置換
* **Still open:** 現在の状態。Local green、別 reviewer、analyst判断だけでは closure しない

# Parent workflow consequence

Parent workflow の次の action は、`RCG-I05-004` と `RCG-I05-005` を一つの bounded TDD remediation batch として implementation owner に渡すことです。

I05-PLAN-008 pass の prerequisites は次のとおりです。

1. Typed failure propagation と phase evidence の correction
2. Current executable registry の completion
3. First Red と focused green
4. Full candidate-local quality gates
5. Clean worktree
6. Commit/push 後の local/upstream/GitHub exact-SHA equality
7. Exact-SHA GitHub Actions success
8. Fresh GPT-6 review で P0=0/P1=0
9. Fresh Strict review で P0=0/P1=0、`review_status=pass`

それまで次は blocked です。

* I05-PLAN-008 completion
* I05-PLAN-002～007
* production adapter／Node work
* Issue #8 completion
* package/runtime acceptance claim

現時点で human decision や fresh remediation campaign は不要です。同一 objective、同一 authority、同一 reviewer roles の fresh exact-SHA re-review で足ります。

次の条件では human decision または fresh campaign が必要になります。

* public state model／schema version変更
* accepted code/stage/outcome変更
* production/lower-layer boundary変更
* scope拡大
* security／compatibility／operations変更
* current authorities の material conflict

Edits、test execution、Git operations、artifact persistence、commit、push、reviewer contact、workflow transition、closure はこの analyst skill の外です。

# Assumptions and unresolved evidence

* 一次 packet SHA-256、GPT-6 report SHA-256、Strict JSON SHA-256 は caller 提示値を採用しており、原本から独立再計算していません。
* GPT-6 source-native report には具体的な model-picker provenance と completion timestamp がありません。
* Strict reviewer はローカルテストを実行していません。
* GPT-6 reviewer は focused tests のみで、full suite、mypy、Ruff 等を自身では再認定していません。
* `EarlySourceReadPrefix` に追加する private phase witness の名称や具体的クラス構成は canonical decision ではありません。Canonicalなのは、reader-owned evidenceから observed prefixを一意に導出する invariantです。
* Program/context pre-seal failure の public `source` observation identity の正確な private preimage は、First Red と既存 canonical redaction rules に従って決める必要があります。Raw bytes や synthetic planを含めてはなりません。
* Root config ordinary READ と program/context ordinary READ の既存意味は変更しない前提です。修正にその意味の変更が必要と判明した場合、authorization は失効します。
* Current `next-run-decision-v1`／`next-config-v1` の field set は十分と推定しています。新しい public field または schema version が必要と判明した場合は design decision が必要です。
* Actual Node spawn、production adapter、OS process proof、installed-wheel runtime、consumer integration、release acceptance は unavailable ですが、I05-PLAN-008 の明示的な非目標です。
* Repository root の `AGENTS.md` は exact commit で確認できませんでした。現在参照できた repository-specific canonical authority は Issue #8 Requirement／Design／Plan と checked-in schemas／reference／tests／fixtures です。
* Branch tip が `1df6c4e8c8b76bf1ebc02590600d98f8fa6491a8` から移動した時点で、この packet の repository facts は current candidate factsではなくなり、次の分析または re-review 前に strict GitHub verification が再度必要です。
