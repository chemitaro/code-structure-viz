# Stdout and stderr v1

`--stdout` は高々一回で、`manifest`、`python:semantic-json`、
`python:plantuml`、`sqlalchemy:semantic-json`、`sqlalchemy:plantuml`、
`next:semantic-json`、`next:plantuml` のclosed setから、選択domainと一致するものだけを受理する。
別domainまたは選択されていないformatを指すselectorは
source acquisition前にexit 2とし、stdoutとArtifactを空にする。

Next の selector と `stdout-result/v1` の status matrix は Issue #8 の
pre-implementation contract である。complete/not_applicable/partial_safe/
payload_unavailable の Next result は domain manifest と同じ status/reason を参照し、
diagnostic は必ず stderr だけに出す。current parser が Next を reject する状態は
production implementation 前の明示された境界である。

selector省略時、stdoutは `code-structure-viz.run-summary/v1` のcanonical JSON一行。
利用可能なselectorは公開fileとexactly同じbytesだけをstdoutへ複製する。
利用不能なselectorは `code-structure-viz.stdout-result/v1` 一行を返す。

diagnosticは `code-structure-viz.diagnostic/v1` のcanonical JSON Linesだけをstderrへ
出す。stdoutへdiagnosticを混在させず、stderrへsource body、literal、secret、
absolute/temp path、Git stderr、tracebackを出さない。

## Round 15 canonical bytes and target failures

Next unavailable target resultsは `next:semantic-json` または
`next:plantuml` のselectorでだけ `target_failures` を持つ。配列は
`{target_key, reason}` をtargetごとに一件だけ含み、reasonは
`missing`、`component_only`、`duplicate`、`out_of_scope`、`non_program`、
`control_context`、`project_ambiguity`、`selected_taint` のclosed enumである。
配列はcanonical JSON bytes順にsortedし、同一reasonでもtargetが異なれば
別行として保持する。available、not_applicable、generic unavailable、
fatal、interruptのbranchはこの配列も旧単一`reason`も持たない。

stdoutの全JSONは既存の一つのcanonical encoderを使う。object keyは
lexicographic `sort_keys=True`、文字列はNFC、encodingはUTF-8、行末は
LF一つであり、target failure専用の手書きfield order encoderは存在しない。
available artifact bytesのselected copyには
`max_selected_stdout_bytes`を適用し、exactは全量を返す。+1はpartial bytesを
公開せず、selected artifactだけをunavailableとする。これはvalidated semantic
decisionのstatusを別の値へ書き換えない。

adapter stdout captureとresponse decodeはpublic stdoutとは別境界である。
`max_adapter_stdout_capture_bytes`はchunkをretainする前に測定し、
`max_adapter_response_bytes`はcomplete private bytesをdecode前に測定する。
いずれも+1でread/decoderを継続せず、manifest-onlyのtyped unavailableとexit 3へ
進む。stderr harnessも同じcount-before-retain契約であり、child textをstdoutへ
漏らさない（faithful iterable testでありOS process-level testではない）。
