# Next export observation v1

Issue #8の実装前契約。公開bindingと、抽出漏れを検出するprivate observationは別のデータである。
この文書はstring-named exportについての現行規則であり、過去Roundの一律TARGET扱いや
`r23_string_export_disposition`だけの検証結果より優先する。製品adapterの実装完了を意味しない。

## 公開するもの・しないもの

- 公開`export_binding`は、IdentifierNameまたは`default`のvalue exportが1つのComponentに解決したものだけ。
- `export { View as "display-name" }`、`export { "source-name" as View } from "./source"`、
  `export * as "namespace-name" from "./source"`も走査対象。文字列が`"View"`のように
  IdentifierNameとして安全でも、string形式という構文区分は失わない。
- 生の文字列名、ソース断片、private observation/proofは公開semantic/PlantUML/domain/root manifest/
  stdout/stderrへ複製しない。private envelopeをpublic decisionへ埋め込むことも禁止する。
- 公開decisionのrequest/responseは、実際のcanonical bytesのSHA-256・byte length・canonicalフラグ
  （requestにはrequest_idも）だけ。内部のvalidated request/raw response/proofは保持して照合に使う。

## Private occurrenceの識別

`next-adapter-response-v1`の`export_observation`に`syntax_kind=string_export`のclosed branchを持つ。

| field | 規則 |
| --- | --- |
| owner / byte_start / byte_end | 凍結UTF-8ソース上の物理ownerと半開区間。listではspecifier全体、namespaceではexport文全体 |
| token_identity | owner、byte区間、区間bytesのSHA-256、nullのpublic names、string_namesをcanonical JSONでhash |
| syntax_identity | `export:<path>:<start>:<end>:string_export`。生の文字列名を含めない |
| exported_name / imported_name / expanded_exported_name | すべてnull。公開名の文法を任意stringへ広げない |
| string_names.imported / exported | form、safe_identifier、decoded_sha256の3キーだけ |
| form | identifier / string / namespace。少なくとも片方がstring |
| safe_identifier | decoded値が公開IdentifierName文法を満たす場合のNFC値、それ以外はnull |
| decoded_sha256 | decode済みJavaScript UTF-16 code unitsをBE・BOMなしでhash。NFC正規化前の区別を保持 |
| resolution / resolution_basis | 解決結果と根拠。未解決をnon-componentと推測しない |
| disposition | 以下の3経路からrequestと証拠に基づき導出。caller booleanでは選べない |

raw spellingとdecoded nameのdigestは役割が異なる。`"a"`と`"\u0061"`はdecoded digestが同じでも
source tokenのdigestは異なる。改行・空文字・引用符・補助平面文字等をsyntax identityへ直書きしない。

## 3経路と優先順位

| 条件（上から優先） | disposition | diagnostic / outcome | coverage |
| --- | --- | --- | --- |
| 明示path targetが当該ownerを含む | target_failure | TARGET-001 / payload_unavailable / exit 3 | targetはfailed、record_ids=[]、reason=unsupported_export |
| 非componentのvalueまたはtype-onlyと証明できる | intentional_unsupported | UNSUPPORTED-001 / complete / exit 0 | 既存value/type export数へ1 occurrenceずつ計上。Module単位のinfo countにも計上 |
| component binding、componentの可能性、未解決が残る | export_failure | EXPORT-001 / payload_unavailable / exit 3 | private occurrenceとfailureを保持、公開binding/artifactは生成しない |

ここでのcodeはすべて`CSV-NEXT-` prefixを持つ。file、directory、root `path:.`の包含は
segment ancestryで判断し、`src/one`を`src/one-more`に一致させない。target未指定の自動発見は
明示targetではない。既存のmalformed responseやsource failureの優先順位は変えない。

公開bindingとcoverageが同時に省略されても、凍結ソースのoccurrenceとの照合で拒否する。
string occurrenceを通常のre-export graph edgeへ見せかけたり、schemaに通るだけのdispositionや
countを採用したりしない。既存IdentifierName exportのclosed branchも緩めない。

## 現在の検証範囲と実装時ゲート

現在のPython referenceは、`tests/fixtures/next_export_census.json`の閉じたfixture grammarから
観測を再構築する。汎用TypeScript parserやTypeCheckerではなく、production source全体の解析証明ではない。
参照分類の根拠は`component_witness`、`type_only_syntax`、`primitive_const`、`open_world`である。
`primitive_const`は独立に読める単純なprimitive const宣言だけであり、Component配列に存在しないことや
動的initializerをnon-componentの証拠にしない。未証明のre-export/namespaceはopen_worldとして失敗させる。

実装時は固定TypeScript TypeCheckerと凍結SourceViewを実際につなぎ、同じ受け入れ事例を製品経路で
再検証する。fixture-only helperを製品へコピーしただけでは実装完了としない。識別子以外の文字列名を
将来サポートする場合は、公開名・redaction・identityの契約変更として別途扱う。

参照回帰は`test_actual_string_export_disposition_reaches_every_public_surface`、
`test_actual_string_export_rejects_coordinated_proof_mutations`、
`test_string_export_scanner_keeps_raw_span_and_decoded_name_digest`、
`test_public_decision_exports_descriptors_never_private_request_or_proof`。
検証結果と独立レビュー結果はIssue artifactに記録し、この文書の存在をpassの代用にはしない。

構文の一次情報:
[ECMAScript Exports / Early Errors](https://tc39.es/ecma262/multipage/ecmascript-language-scripts-and-modules.html#sec-exports-static-semantics-early-errors)。
local exportの参照元にStringLiteralは使えず、from付きexportではModuleExportNameとして扱う。
