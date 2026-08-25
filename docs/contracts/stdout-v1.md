# Stdout and stderr v1

`--stdout` は高々一回で、`manifest`、`python:semantic-json`、
`python:plantuml` のいずれかだけを受理する。選択されていないformatを指すselectorは
source acquisition前にexit 2とし、stdoutとArtifactを空にする。

selector省略時、stdoutは `code-structure-viz.run-summary/v1` のcanonical JSON一行。
利用可能なselectorは公開fileとexactly同じbytesだけをstdoutへ複製する。
利用不能なselectorは `code-structure-viz.stdout-result/v1` 一行を返す。

diagnosticは `code-structure-viz.diagnostic/v1` のcanonical JSON Linesだけをstderrへ
出す。stdoutへdiagnosticを混在させず、stderrへsource body、literal、secret、
absolute/temp path、Git stderr、tracebackを出さない。
