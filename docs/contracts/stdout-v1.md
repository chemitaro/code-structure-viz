# Stdout and stderr v1

## Current v1 normative authority

現在のstdout authorityは、semantic decisionを入力に一度だけsealしたfinal publication decisionです。summary、root manifest、selected artifact、typed unavailableのclosed unionをsealed bytesから投影し、callerのcandidate/status/chunk再注入、rerender、retryを許しません。selected copyのexactは全bytes、+1はpartial bytesなしの`CSV-NEXT-LIMIT-003`/publication-incomplete/exit 3で、semantic statusとartifact descriptorは保持します。canonical JSONはsort_keys、NFC、UTF-8、LFのみです。target failure rowsはtarget-related unavailableだけで、他branchに出ません。以下のRound節はhistorical evidence（非normative）です。

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

## Round 18 exact closed stdout result

The result is a closed union with no partially discriminated branch:
`selector=null` emits the exact summary, `selector=manifest` emits the exact
root manifest, `next:semantic-json` and `next:plantuml` emit their exact
selected artifact, and an unavailable branch emits only its typed status,
reason, descriptor, and allowed target-failure rows. Each selector has a
schema-fixed path, format, and media type; forbidden fields are rejected.
`target_failures` is required only for a target-related Next unavailable result
and is one canonical sorted row per failed target.

The final boundary receives all candidate bytes before applying the selected
copy limit. Exact bytes are retained and returned verbatim; limit+1 is
disposed and returns the schema-valid unavailable branch with no partial
payload. Summary/manifest status is sealed in a two-stage closed publication
algorithm, so a caller cannot substitute a measurement, outcome, or selected
payload after finalization. All JSON uses the existing lexicographic
`sort_keys=True` encoder with NFC, UTF-8, and one LF; path-only ordering uses
NFC UTF-8 bytes and object rows use canonical JSON bytes. The faithful iterable
capture evidence is not an OS process-level test. Fresh current-SHA Strict is
pending, readiness is unconfirmed, and production implementation is absent.

## Round 19 source and publication boundaries

The public selected stream never accepts a caller-supplied candidate map,
preselected payload, or independent status. Adapter chunks are observed at
the child-capture boundary and validated response bytes are retained as an
opaque identity; summary, root manifest, selected artifact, and typed
unavailable bytes are derived once from the semantic decision and sealed in
`PublicationBoundaryDecision`. The projection API receives that final object
only and returns its sealed bytes. An empty stdout is a usage/no-publication
case, not an alternate successful candidate.

The selected-copy algorithm is two-stage and non-circular. First measure the
success candidate once. If it is within `max_selected_stdout_bytes`, retain
and return those exact bytes. If it is over the limit, dispose of partial
bytes, create and persist one failure-manifest descriptor and one typed
unavailable result, and do not measure or copy the failure manifest again as
the selected stream. The semantic outcome remains unchanged; the publication
result records the selected-copy failure and exit 3. Candidate byte and digest
maps are sealed so non-selected-candidate mutation cannot alter a projection.

Round 19 also fixes target ordering: compare the NFC-normalized UTF-8 bytes of
the path after removing `path:`. JSON escaping does not affect path order.
Canonical JSON bytes remain the comparator for object rows only. The quote
inverse target vector is a negative acceptance case.

Executable evidence is
`test_round19_target_path_order_uses_nfc_utf8_bytes_not_json_escaping`,
`test_round18_publication_projections_return_sealed_candidate_bytes`, and
`test_round16_final_publication_decision_seals_capture_stderr_and_selected_copy`.
Fresh current-SHA Strict is pending, readiness is unconfirmed, and production
implementation is absent.

## Round 20 source and provenance inputs

The stdout projection receives source acquisition's single typed result rather
than reconstructing a status from a missing config. An all-non-applicable
`PackageApplicabilityMatrix` yields the closed not-applicable result without a
Node probe. A malformed control/package or non-isolatable source failure yields
the schema-valid manifest-only `CSV-NEXT-SOURCE-003`/`payload_unavailable`
branch; a fatal integrity result yields the fatal/no-manifest branch. The
source graph, applicability state, diagnostic, and exit are all owned by the
same decision projection.

The stage-dependent provenance used for this branch has exactly one
`{kind, stage, failure_code, observed}` shape. It records only the observed
prefix and explicit `unobserved`/`null` suffix, so stdout cannot fabricate a
request, limits, source plan, toolchain, or budget after an early failure. The
Round 20 executable checks are
`test_round20_source_integrity_has_one_fatal_vs_payload_unavailable_projection`,
`test_round20_stage_provenance_is_one_canonical_shape_and_rejects_mismatch`, and
`test_round20_package_applicability_matrix_is_direct_dependency_only`.
Fresh current-SHA Strict remains pending, readiness is unconfirmed, and
production implementation is absent.

## Round 21 closed applicability and provenance output

The stdout result is a projection of the applicability decision, never an independently inferred project
list. The frozen `PackageApplicabilityMatrix` makes direct non-empty Next dependencies applicable, missing or
non-direct roots non-applicable, and malformed package observations globally unavailable. All-non-applicable
uses the no-Node-probe `NotApplicableDecision`; a mixed matrix includes applicable roots only. Matrix rows,
toolchain permission, domain/root manifest, stdout/stderr diagnostics, and exit are checked for exact equality.

Control and source failures use the same stage/code provenance union as the decision context. The sealed source
graph recognizes static/side-effect imports, export-from, literal dynamic import, literal require, and
`baseUrl`/`paths`; unsupported, ambiguous, unresolved, or external edges stay open. Unobserved suffix values
cannot be fabricated in stdout. The process authority is `next-process-launch-observation-v1`, and its stable
fingerprint intentionally excludes ephemeral FD/device/inode values.

The executable evidence is `test_round21_applicability_matrix_owns_filter_probe_and_all_public_surfaces`,
`test_round21_provenance_catalog_has_single_request_independent_source_control_union`, and
`test_round21_coverage_index_is_bidirectional_and_self_validating`. Fresh current-SHA Strict is pending,
readiness is unconfirmed, and production implementation is absent.

## Round 22 closed stdout publication

The stdout result is never reconstructed from an independent status or candidate. The final
`PublicationBoundaryDecision` owns the exact summary, manifest, domain artifact, typed-unavailable bytes,
diagnostic JSONL, selected descriptor, and measurements. Its selected-copy overrun retains the semantic
result and persisted artifact descriptor, then emits one incomplete/exit-3 publication with canonical
`CSV-NEXT-LIMIT-003` stderr and no partial stdout; it does not remeasure, rerender, or recopy.

Upstream applicability, config, source graph, and provenance remain decision-owned: malformed package uses
`CSV-NEXT-APPLICABILITY-002`, non-applicable uses `CSV-NEXT-APPLICABILITY-001`, source-integrity
substitution is fatal `CSV-NEXT-SOURCE-INTEGRITY-001`, and ordinary non-isolatable source failure is
`CSV-NEXT-SOURCE-003`. Canonical JSON is sorted lexicographically, NFC, UTF-8, and LF. Fresh current-SHA
Strict is pending, readiness is unconfirmed, and production implementation is absent.
