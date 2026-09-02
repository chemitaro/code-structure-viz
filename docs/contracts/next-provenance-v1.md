# Next stage-dependent provenance v1

## Current v1 normative authority

`next-round23-authority-v1.schema.json`とreference validatorが、Issue #8のprovenanceの単一正本です。provenanceは次の4つだけのclosed unionです。

| kind | request | failure | 公開結果 |
| --- | --- | --- | --- |
| `request_independent_not_applicable` | 未観測/null | applicability + `CSV-NEXT-APPLICABILITY-001` | not_applicable / exit 0 |
| `request_independent_failure` | 未観測/null | observed prefix後のstage/code | payload_unavailable / exit 3 |
| `request_bound_failure` | validated requestを保持 | failure stage/code | catalog outcome |
| `request_bound_success` | validated requestを保持 | なし | complete/partial decision |

各observed rowは`state=observed`、field-specific schema/version、実際のcanonical observed valueのSHA-256を持ちます。`state=unobserved`は`value=null`かつidentity=nullで、失敗stageより前の値を消したり、後の値を合成したりできません。booleanだけのobserved marker、callerが差し替えたdigest、stage/codeに存在しない組み合わせは拒否します。

stageの前に観測されたapplicability、limits、source plan、toolchain、trusted environment、compatibility、process launch、budgetは後続 failureでも保持し、それ以降のsuffixだけをunobservedにします。request-independent failureでは未観測requestを作らず、request-bound failureではcanonical request id/files/digestsを再検証済みの値だけを保持します。`NextDecisionContext`と`NextPublicationContext`はこの同じprovenance shapeを使い、domain/root manifest/stdout/stderr/exitのprojectionはdecisionだけを入力とします。

### Validation order and ownership

raw byte cap → bounded decode/aggregate → closed schema → base/path/reference/proof → actual model/proof-only count → model/entity gate → selected copy の順で、最初のcatalog-valid failureを採用します。`CSV-NEXT-SOURCE-INTEGRITY-001`はrevision drift・duplicate/post-seal read・seal substitution専用のfatal、`CSV-NEXT-SOURCE-003`は普通のnon-isolatable source failureです。`PROJECT-001`はdomain payloadではなくusage exit 2です。

後続のRound節はhistorical evidence（非normative）です。これはproduction implementationの完了、Node実測、OS process-level証明、fresh Strict passを意味しません。
