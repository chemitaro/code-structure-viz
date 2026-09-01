# Next resolved limits v1

Round 12 review state: `review_status: fail` (P0=0, P1=8, P2=0) at exact SHA
`48266f813353a7fd78e4e15d72ff6d33c4142827` (CI `33435802167`, 7/7 success).
The data-only limits and outcome vectors below remain pre-implementation
contracts. Round 12 additionally requires the same validated model to supply
computed counts, budget, coverage, publication, and fingerprint across every
surface. Fresh exact-SHA Strict is pending, readiness is unconfirmed, and
production implementation has not started; the fail result is not a pass.

Round 13 review state: Strict reviewed SHA `991516bf730f4f2ddb3d15067702dcfae95ec6b1`
with CI run `33446911714` (7/7 success) and returned `review_status: fail`,
P0=0, P1=9, P2=1. The data-only remediation checks the complete private adapter
response byte length against `max_adapter_response_bytes` before UTF-8 decoding or materialization;
the exact limit is accepted and limit+1 follows the unavailable/exit-3 path.
The historical fail is preserved. Fresh exact-SHA Strict is pending, readiness
is unconfirmed, and production implementation has not started.

Round 14 remediation adds a separate parent-side child-stdout capture
boundary, `max_adapter_stdout_capture_bytes` (16 MiB). It is measured
incrementally on each bytes chunk before retaining that chunk. Equality is
accepted; the first byte above the limit terminates the adapter process group,
discards raw and partial bytes, calls no decoder, and produces a manifest-only
`CSV-NEXT-LIMIT-003` / `payload_unavailable` result with exit 3. This capture
bound is distinct from both the private complete-response
`max_adapter_response_bytes` bound and the public selected-stream
`max_selected_stdout_bytes` bound. `max_stdout_bytes` remains a v1 compatibility
alias for the selected-stream value.
The response limit vector also uses ID-only proof evidence: a published model
record is counted once in `discovered_records`; proof-only records may carry a
payload only when they are not present in the published model. Thus the model
record cap is reachable without duplicating every model payload in the wire
response.

`schemas/next-limits-v1.schema.json` is the single resolved limits record for
the Next snapshot boundary. The same record is copied byte-for-byte into the
adapter request, resolved config, request fingerprint descriptor, response,
and domain manifest; reference tests reject drift between projections.
Operational limits, including `max_model_records`, are part of the request and
run-fingerprint preimages. They are deliberately not part of the semantic
compatibility ID; changing a limit changes the run fingerprint without
claiming a semantic-format incompatibility.

`max_entities` is the only user-resolvable budget (default `500`, bounded by
the schema). It counts selected/published internal Module + Component
records only; members, relations, facts, projects, and external frontiers do
not consume it. The all-record cap is the separate `max_model_records` limit.
Every other value is a fixed v1 constant. A boundary is
inclusive: the value equal to the limit is accepted and the first value above
it produces the stated outcome. Measurements use UTF-8 bytes where marked;
there is no implicit character-count conversion, silent truncation, or v1
total-RSS promise.

| name | value | counting unit | measurement point | encoding | over-limit outcome |
| --- | ---: | --- | --- | --- | --- |
| `max_entities` | 500 | published internal Module + Component entities | after target projection, before publication | N/A | `payload_unavailable` |
| `max_files` | 20,000 | files | after safe source selection, before read | N/A | `payload_unavailable` |
| `max_file_bytes` | 4,194,304 | UTF-8 bytes per file | after read, before base64 | UTF-8 | `payload_unavailable` |
| `max_decoded_bytes` | 67,108,864 | UTF-8 bytes per request | sum after decode, before adapter spawn | UTF-8 | `payload_unavailable` |
| `max_encoded_stdin_bytes` | 100,663,296 | UTF-8 bytes per stdin payload | canonical JSON encode, before adapter spawn | UTF-8 | `payload_unavailable` |
| `max_json_nesting` | 64 | JSON nesting levels | parser depth before child descent | UTF-8 input | `payload_unavailable` |
| `max_json_string_bytes` | 8,388,608 | UTF-8 bytes per JSON string | parser decode, before materialization | UTF-8 | `payload_unavailable` |
| `max_array_items` | 100,000 | items per JSON array | parser item count before append | N/A | `payload_unavailable` |
| `max_total_array_items` | 100,000 | items across all JSON arrays in one response | streaming aggregate counter before item materialization | N/A | `payload_unavailable` |
| `max_collection_items` | 20,000 | records per model collection | record emission, before append | N/A | `payload_unavailable` |
| `max_model_records` | 10,000 | all discovered model records | model assembly, before publication | N/A | `payload_unavailable` |
| `max_stdout_bytes` | 16,777,216 | compatibility alias for selected stdout bytes | canonical output encode, before write | UTF-8 | `payload_unavailable` |
| `max_adapter_response_bytes` | 16,777,216 | complete UTF-8 bytes of private adapter response | after child capture, before decode | UTF-8 | `payload_unavailable` |
| `max_selected_stdout_bytes` | 16,777,216 | UTF-8 bytes of public selected summary/manifest/artifact copy | canonical output encode, before copy/write | UTF-8 | `payload_unavailable` |
| `max_stderr_bytes` | 65,536 | UTF-8 bytes per stderr payload | diagnostic encode, before write | UTF-8 | `payload_unavailable` |
| `max_adapter_stderr_capture_bytes` | 65,536 | UTF-8 bytes captured from adapter stderr | incremental process-group capture before append | UTF-8 | `payload_unavailable` |
| `max_adapter_stdout_capture_bytes` | 16,777,216 | UTF-8 bytes captured from adapter stdout | incremental process-group capture before append/decode | UTF-8 | `payload_unavailable` |
| `timeout_seconds` | 60 | wall-clock seconds per adapter run | monotonic deadline at process wait | N/A | `payload_unavailable` |
| `v8_old_space_mib` | 512 | binary MiB heap limit | adapter process start flag | N/A | `payload_unavailable` |
| `max_type_depth` | 16 | TypeIR levels per prop | validator before child descent | N/A | `partial_safe` |
| `max_type_nodes_per_prop` | 512 | TypeIR nodes per prop | validator before node visit | N/A | `partial_safe` |
| `max_union_members` | 64 | members per union | validator before union-member visit | N/A | `partial_safe` |
| `max_intersection_members` | 64 | members per intersection | validator before intersection-member visit | N/A | `partial_safe` |
| `max_nested_properties` | 256 | properties per prop tree | validator before property visit | N/A | `partial_safe` |
| `max_signatures_per_component` | 16 | signatures per component | validator before signature visit | N/A | `partial_safe` |
| `max_flow_visits` | 10,000 | flow visits per component | flow traversal before node visit | N/A | `partial_safe` |
| `max_alias_edges` | 64 | alias edges per module | alias graph before edge append | N/A | `partial_safe` |

`max_entities` is applied by an independent `EntityBudgetGate` after the
response model and proof have passed structural validation and immediately
before publication. The gate recomputes
`actual = published modules + published components`; it does not trust the
submitted summary count. `actual <= resolved` publishes normally, while an
overrun records `CSV-NEXT-LIMIT-005`, keeps the actual count in the domain
manifest, returns `payload_unavailable`, and publishes neither semantic JSON
nor PlantUML. `max_model_records` remains the structural all-record boundary
and is fixed at 10,000. A published model record is represented by one ID-only
`discovered_records` observation; proof payload is not duplicated. The proof
observation is still a separate JSON-array item, so reachability must be proved
against the aggregate counter rather than asserted from the model count alone.
The generated exact-cap response (9,999 context Files plus one Project) is
schema-valid, 5,642,861 bytes, and 40,001 aggregate items; the 10,001-record
counterpart is schema-valid, 5,643,426 bytes, and 40,005 aggregate items. Both
are below the 100,000 aggregate and 16 MiB response bounds, so the model cap
and its +1 diagnostic are genuinely reachable. The response schema keeps
`proof.discovered_records` at structural `maxItems=20,000`, separate from the
semantic model cap, so cap+1 reaches `CSV-NEXT-LIMIT-005` rather than schema
rejection.

The gate receives an explicitly derived pre-budget outcome; there is no
implicit `complete` default. A valid `partial_safe` result remains
`partial_safe` under an allowed budget, including an explicit override. Only
an entity overrun becomes `payload_unavailable`. Artifact paths are selected
from the requested formats, so an unrequested renderer is never published.

`max_array_items` limits each individual JSON array, while
`max_total_array_items` counts all nested response-array items in a streaming
counter. `max_collection_items` applies only to each semantic model
collection; it is not an aggregate JSON-array limit. The reference vector
`[50000, 50000, 1]` therefore fails at aggregate 100,001 even though every
individual array is below 100,000 and no large response is allocated.

`max_stderr_bytes` is the public diagnostic encode/write bound.
`max_adapter_stderr_capture_bytes` is a separate child-process trust boundary:
the counter is incremental in UTF-8 bytes, equality is accepted, and the first
byte over the limit terminates the process group, disposes raw and partial
adapter stderr, emits only stable `CSV-NEXT-LIMIT-003`, and projects zero raw
stderr bytes into the manifest. Neither bound exposes adapter text.

`max_adapter_stdout_capture_bytes` applies to the adapter's private response
stream before `bounded_decode_json`. The parent counts first and retains only
accepted chunks; it never invokes the decoder on a partial over-limit stream.
The exact boundary is a complete capture, while limit+1 is terminated and
disposed. The public unavailable result is manifest-only and cannot contain
the discarded response or a partial semantic model. A successful bounded
capture then enters the one raw-response path, where
`max_adapter_response_bytes` is checked on the complete bytes before decoding.
After summary/manifest or semantic/PlantUML rendering, `max_selected_stdout_bytes` applies to the
public selected-stream copy. A copy breach is an explicit
`selected_artifact_unavailable` publication result (or its summary/manifest
typed-unavailable branch); it must not rewrite the
validated semantic domain outcome.

The public renderer applies the same all-or-none rule to diagnostics: it encodes
the complete canonical JSONL stream (`canonical JSON` plus one `LF` per line)
before writing. The exact limit is accepted; one byte over it writes zero
partial bytes, returns `CSV-NEXT-LIMIT-003`, and projects only that catalog
diagnostic into the manifest. Multibyte UTF-8 characters count as encoded bytes.
The reference function `render_public_diagnostic_stderr` and its vectors keep
this public gate separate from child capture.

Before response object materialization, `bounded_decode_json` streams the real
UTF-8 response bytes and counts duplicate object keys, parser nesting, decoded
string bytes, each array, and the aggregate of all array items. A response with
100,001 aggregate items fails even when every individual array has at most
100,000 items; the returned counter is `materialized=false` and no partial
response is retained.

The executable boundary vectors in `tests/contracts/test_next_contracts.py`
exercise `limit-1`, `limit`, and `limit+1` arithmetically for every row, so
the suite does not allocate a 96 MiB payload merely to prove an inclusive
boundary. It also covers 500 internal entities with additional non-entity
boundary. It also covers exact/+1 child stdout capture with a faithful
iterable chunk-reader harness and decoder spy (not an OS process-level test),
public selected-copy exact/+1, 501 unavailable, and a 600 override with 501
successful. Generated schema-valid wire envelopes cover model exact/+1 and an
aggregate+1 response through `bounded_decode_json` and
`response_boundary_decision`; no huge checked-in fixture is required. The
precedence is raw bytes first, aggregate array items second, then model
records. Aggregate counts
(`discovered`, `published`, `excluded`, `failed`, every collection count, and
`internal_entities`) are recomputed from records and the proof; a caller
cannot bypass a limit by mutating a summary count.

## Round 15 measurement and authority addendum

The three byte limits are intentionally named by boundary: child capture is
`max_adapter_stdout_capture_bytes`, the complete private response is
`max_adapter_response_bytes`, and the public selected-stream copy is
`max_selected_stdout_bytes`. They may share the v1 value (16 MiB), but they
are not interchangeable measurements. Capture measures each `Iterable[bytes]`
chunk before retaining it; response measures complete bytes before decode;
selected stdout measures the fully rendered bytes before the public copy. The
first over-limit result at each boundary disposes partial bytes and does not
silently change the semantic decision.

The `NextRunDecision` union and its immutable `NextPublicationContext` are the
authority that carries resolved limits and their measurement provenance to
domain, manifest, stdout, stderr, and publication. A request-independent
failure carries a `NextDecisionContext` with null counts where measurement was
not possible. This prevents a downstream writer from inventing a model count,
source plan, or output limit after an early failure.

The aggregate boundary is tested using a schema-valid generated response whose
extra `proof.excluded` and `proof.failed` rows make the decoded array-item
counter exactly 100,001 while the raw response remains below 16 MiB. The test
therefore proves the actual byte/decode path and its `CSV-NEXT-LIMIT-003`
precedence; it is not a direct call to the arithmetic classifier. The model
cap test separately reaches 10,000 and 10,001 model records below both caps.

## Round 16 boundary ordering and publication seal

Round 16 fixes the limit authority to one ordered path:

```text
child capture
  -> max_adapter_response_bytes (complete private bytes, before decode)
  -> bounded decode and aggregate array counter
  -> closed schema
  -> base/path/reference/proof validation
  -> actual model + proof-only count
  -> max_model_records
  -> EntityBudgetGate
  -> max_selected_stdout_bytes (public artifact copy)
```

`max_adapter_stdout_capture_bytes`, `max_adapter_response_bytes`, and
`max_selected_stdout_bytes` are three named boundaries even when their v1
values are equal. The old `max_stdout_bytes` spelling is accepted only as the
selected-output compatibility alias; it is never a private response limit.
`CSV-NEXT-LIMIT-003` is the stable code for configured byte/structural
resource boundaries (including raw response, aggregate array, string, depth,
and capture); malformed JSON, closed-schema, reference, and proof failures
remain `CSV-NEXT-PROTOCOL-001`. Every boundary is inclusive and is tested at
exact and +1 bytes/items without constructing an unnecessarily large fixture.

All measurements are collected before publication and then sealed into one
immutable publication decision together with the validated semantic decision.
An adapter capture or public stderr breach yields zero raw/partial publication;
a selected-artifact copy breach yields `selected_artifact_unavailable` while
preserving the semantic decision and its persisted artifact descriptor. The
reference stdout/stderr harness uses faithful `Iterable[bytes]` chunk reads and
does not claim to be an OS process-level test. Round 16 remains a data-only
pre-implementation contract: fresh current-SHA Strict is pending, readiness is
unconfirmed, and the production adapter/CLI is absent.

The resulting `PublicationBoundaryDecision` is the only input to domain, root
manifest, selected stdout, public stderr, artifact, and exit projections. A
caller cannot replace any measured byte count or publication outcome by
passing a second status/map to one of those projection functions. The launch
descriptor used for the capture boundary is also an explicit required field
of the decision's `NextPublicationContext`; it is fingerprinted and is never
reconstructed from a host default.

## Round 17 measurement pipeline

The executable pipeline is one closed order:

```text
raw cap
  -> bounded decode/aggregate
  -> closed schema
  -> base/path/reference/proof
  -> actual model + proof-only count
  -> model gate
  -> entity gate
  -> selected copy
```

`max_adapter_stdout_capture_bytes`, `max_adapter_response_bytes`, and
`max_selected_stdout_bytes` remain distinct measurement points. A configured
byte or structural boundary uses `CSV-NEXT-LIMIT-003`; malformed bytes,
closed-schema violations, and proof violations use
`CSV-NEXT-PROTOCOL-001`. The raw cap is checked before decode, aggregate items
before materialization, and model plus proof-only counts only after the
schema/reference/proof checks. Exact values are accepted and +1 values are
disposed without partial decoder or publication input. `max_stdout_bytes` is
only the selected-output compatibility alias.

The final measurement record is sealed into `PublicationBoundaryDecision`
before any domain, manifest, stdout, stderr, artifact, or exit projection. The
reference vectors exercise the complete schema-valid wire path and faithful
capture/copy harness; they do not replace it with an arithmetic classifier or
claim OS process-level coverage. Fresh current-SHA Strict is pending,
readiness is unconfirmed, and production implementation is absent.
