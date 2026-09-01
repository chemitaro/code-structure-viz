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
利用可能なselectorは、selectorなしならsummary、`manifest`ならroot manifest、
domain selectorなら公開fileを、選択されたstreamのexact bytesとしてstdoutへ複製する。
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
summary、manifest、available artifact bytesの各selected streamには
`max_selected_stdout_bytes`を適用し、exactは全量を返す。+1はpartial bytesを
公開せず、選択されたstreamだけをtyped unavailableとする。これはvalidated semantic
decisionのstatusを別の値へ書き換えない。

adapter stdout captureとresponse decodeはpublic stdoutとは別境界である。
`max_adapter_stdout_capture_bytes`はchunkをretainする前に測定し、
`max_adapter_response_bytes`はcomplete private bytesをdecode前に測定する。
いずれも+1でread/decoderを継続せず、manifest-onlyのtyped unavailableとexit 3へ
進む。stderr harnessも同じcount-before-retain契約であり、child textをstdoutへ
漏らさない（faithful iterable testでありOS process-level testではない）。

## Round 16 final publication seal

Child stdout capture, complete private response, public diagnostic stderr, and
selected artifact copy are separate measurement points. Their exact/+1
results are sealed once in the final immutable publication decision before
domain, root manifest, stdout, stderr, or exit is projected. A selected-copy
overrun preserves the validated semantic decision and artifact descriptor but
returns a typed selected-artifact-unavailable result; it does not silently
change `complete` to another semantic outcome. Capture harness evidence uses
incremental `Iterable[bytes]` reads with read-stop/dispose/process-group flags,
and is explicitly not an OS process-level test.

`PublicationBoundaryDecision` is the sole input to the publication projections:
domain, root manifest, artifact bytes/descriptors, selected stdout, public
stderr, and exit code all receive that one immutable object. They must not
accept a semantic decision plus a separately reconstructed publication status,
measurement dictionary, or retained-byte value. The decision is sealed only
after the four measurements are complete; an omitted or substituted process
launch descriptor is likewise invalid because the descriptor is mandatory in
every decision's `NextPublicationContext` and its fingerprint preimage.
The final object also carries a digest over the four measurement records, so
replacing a retained buffer or counter without resealing the boundary is
rejected.

All result JSON, including target failures, uses the existing canonical
lexicographic encoder (`sort_keys=True`, NFC, UTF-8, LF). No manual field-order
encoder is allowed. Fresh Round 16 Strict remains pending; the historical
review was `P0=0 / P1=16 / P2=3 / fail` at SHA
`732477c72c7e05d3f15818ba8a3f75a4c97dc5a9`.

## Round 17 closed stdout union

The final stdout result is a closed union: selector `null` returns the exact
run summary; `manifest` returns the exact root manifest; a selected
`next:semantic-json` or `next:plantuml` returns that exact artifact; and a
typed unavailable branch returns schema-valid status/reason with no partial
bytes. The same `max_selected_stdout_bytes` copy gate measures all three
successful stream kinds. At exact size the retained bytes are emitted; at
limit+1 they are discarded and the typed branch is emitted instead. The
null branch keeps `run_status` and no artifact; a selected-copy failure may
make that run incomplete while the semantic domain remains complete. The manifest branch keeps the
persisted `run-manifest.json` descriptor; the domain branch keeps its
persisted artifact descriptor. `target_failures` is legal only on a Next
target-related unavailable branch, with exactly one stable reason row per
target from the eight closed reasons. Selector branch mutations, duplicate
reasons, missing reasons, and non-target failures are rejected.

All of these branches are projections of one immutable
`PublicationBoundaryDecision`, which seals response bytes, validated request
ID, model digest, exact artifact/selector/diagnostic bytes, and capture,
stderr, and selected-copy measurements. The final boundary receives the
canonical summary/manifest/selected-artifact stream bytes before the copy
gate; its projection returns only the retained sealed bytes or the canonical
typed-unavailable line. No projection accepts an independent outcome or
measurement map, and no writer re-renders bytes. Canonical output uses
lexicographic `sort_keys=True`, NFC, UTF-8, and one LF; submitted order is
validated before sorting. Fresh current-SHA Strict remains pending, readiness
is unconfirmed, and production implementation has not started.
