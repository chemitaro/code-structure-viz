# Next resolved limits v1

`schemas/next-limits-v1.schema.json` is the single resolved limits record for
the Next snapshot boundary. The same record is copied byte-for-byte into the
adapter request, resolved config, request fingerprint descriptor, response,
and domain manifest; reference tests reject drift between projections.

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
| `max_collection_items` | 20,000 | records per model collection | record emission, before append | N/A | `payload_unavailable` |
| `max_model_records` | 100,000 | all discovered model records | model assembly, before publication | N/A | `payload_unavailable` |
| `max_stdout_bytes` | 16,777,216 | UTF-8 bytes per stdout payload | canonical output encode, before write | UTF-8 | `payload_unavailable` |
| `max_stderr_bytes` | 65,536 | UTF-8 bytes per stderr payload | diagnostic encode, before write | UTF-8 | `payload_unavailable` |
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

The executable boundary vectors in `tests/contracts/test_next_contracts.py`
exercise `limit-1`, `limit`, and `limit+1` arithmetically for every row, so
the suite does not allocate a 96 MiB payload merely to prove an inclusive
boundary. It also covers 500 internal entities with additional non-entity
records, 501 unavailable, a 600 override with 501 successful, and a
compositional 100,001 `max_model_records` failure. Aggregate counts
(`discovered`, `published`, `excluded`, `failed`, every collection count, and
`internal_entities`) are recomputed from records and the proof; a caller
cannot bypass a limit by mutating a summary count.
