# Next stage-dependent provenance v1

## Current v1 normative authority

現行provenanceは`next-provenance-v1.schema.json`、公開decisionは`next-run-decision-v1.schema.json`、
それらの実値照合はreference validatorに定義する。`next-round23-authority-v1`は過去の参照実験で、
実公開経路の代用にしない。provenanceは次の4つのclosed unionである。

| kind | request | failure | 公開結果 |
| --- | --- | --- | --- |
| `request_independent_not_applicable` | 未観測/null | applicability + `CSV-NEXT-APPLICABILITY-001` | not_applicable / exit 0 |
| `request_independent_failure` | 未観測/null | observed prefix後のstage/code | payload_unavailable / exit 3 |
| `request_bound_failure` | validated requestを保持 | failure stage/code | catalog outcome |
| `request_bound_success` | validated requestを保持 | なし | complete/partial decision |

各observed rowは`state=observed`、field-specific schema/version、実際のcanonical observed valueのSHA-256を持ちます。`state=unobserved`は`value=null`かつidentity=nullで、失敗stageより前の値を消したり、後の値を合成したりできません。booleanだけのobserved marker、callerが差し替えたdigest、stage/codeに存在しない組み合わせは拒否します。

stageの前に観測されたapplicability、limits、source plan、toolchain、trusted environment、compatibility、process launch、budgetは後続 failureでも保持し、それ以降のsuffixだけをunobservedにします。request-independent failureでは未観測requestを作らず、request-bound failureではcanonical request id/files/digestsを再検証済みの値だけを保持します。`NextDecisionContext`と`NextPublicationContext`はこの同じprovenance shapeを使い、domain/root manifest/stdout/stderr/exitのprojectionはdecisionだけを入力とします。

### 実観測に結び付く早期分岐

`request_independent_not_applicable_decision`の必須入力は、凍結package bytesから導出した
`PackageApplicabilityMatrix`である。aggregateが`non_applicable`の場合だけ生成できる。
applicable、malformed、applicableを含むmixed matrixは拒否する。requestを受け取って対象外に
変換する旧互換constructorは廃止し、`NotApplicableDecision`自身もrequest保持を拒否する。
matrixのidentityはdecision contextとpublication contextで一致し、別projectのmatrixとの交換を拒否する。
matrixはmissingを含む非公開の凍結package bytesを保持し、constructorでentries/aggregateを再導出する。
分類だけを非対象へ書き換える操作は拒否する。公開wireの構造検証用matrix（bytesなし）はNAを生成する
権限を持たない。provenanceにはmatrixとpackageのsafe digest/sizeを使い、本文は公開しない。

取得失敗では、`InstrumentedSourceReader`が実際のread成功・read失敗を保持する。
packageについては`read`、`failed`、列挙で不在を確認した`missing`、未試行の`unobserved`を区別する。
全packageの観測が揃う前のfailureから、欠落扱いのmatrixや対象外成功を作らない。
configのidentityは読み取ったbytesのSHA-256・byte length・pathと失敗情報から導出する。
`observed`は取得の証拠であり、JSON解析や設定解決の成功を意味しない。

実際の`seal_source_acquisition_result`が返す早期`SourceAcquisitionUnavailable`は、
code/stageに加えこのprovenanceと、catalogが許す場合だけfailure pathを保持する。
その非公開原本は`EarlySourceReadPrefix`（roots、列挙path、取得bytes、実read failure、code/stage/path）である。
provenanceはcaller入力ではなく原本から導出するread-only値とし、code/stage/pathも原本と照合する。
別入力のdigestや未読pathへの交換、mutable aliasによる原本変更を許可しない。
`source_acquisition_failure_decision`はapplicability/source_controlの実結果を既存の
`PreResponseFailureDecision`へ接続する。malformed packageはAPPLICABILITY-002、
config読取不能はSOURCE-003/source_controlとし、後者のpathを落とさない。
provenanceを持たない旧status-only fixtureはこの接続関数に渡せない。
後段source-isolation、usage/fatal/interruptの接続を、この早期経路の成功から証明したとは扱わない。

公開側はdecision contextのprovenanceをそのまま引き継ぎ、field名だけのmarkerを再生成しない。
request-independent run fingerprintのpreimageには`observation_provenance_digest`を含める。
異なる取得済み入力はfingerprintを変え、未読sourceのbytesだけの変更は早期結果を変えない。
request、source plan、limits、toolchain、trusted environment、process、response、budgetの
未観測suffixはnullのまま保持する。生のcontrol/source本文をpublic manifestへ追加しない。

受け入れ根拠は`test_actual_early_failure_preserves_observations_through_publication`、
`test_early_failure_identity_binds_read_bytes_not_unread_suffix`、
`test_not_applicable_binds_actual_matrix_through_publication`。4 stdout selectorから
decision/domain/root manifest/typed stdoutのschemaと実値照合を実行する参照テストであり、製品実装の証明ではない。

### Validation order and ownership

表の「validated requestを保持」はprivateな所有権を指す。公開`decision.request`はrequest_id、
raw_sha256、byte_length、canonical_jsonだけ、`decision.response`はraw_sha256、byte_length、
canonical_jsonだけを持つ。source content_base64、validated_response本文、private proofを含めない。
同じsafe projectionをdomain/root manifest/publication decisionから再利用し、private sealと照合する。
公開からの除外を理由に内部のraw responseやproofの検証・保持を省略しない。

raw byte cap → bounded decode/aggregate → closed schema → base/path/reference/proof → actual model/proof-only count → model/entity gate → selected copy の順で、最初のcatalog-valid failureを採用します。`CSV-NEXT-SOURCE-INTEGRITY-001`はrevision drift・duplicate/post-seal read・seal substitution専用のfatal、`CSV-NEXT-SOURCE-003`は普通のnon-isolatable source failureです。`PROJECT-001`はdomain payloadではなくusage exit 2です。

後続のRound節はhistorical evidence（非normative）です。これはproduction implementationの完了、Node実測、OS process-level証明、fresh Strict passを意味しません。
