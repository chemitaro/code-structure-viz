# Next resolved limits v1

`schemas/next-limits-v1.schema.json` is the single resolved limits record for
the Next snapshot boundary. The same record is copied byte-for-byte into the
adapter request, resolved config, request fingerprint descriptor, response,
and domain manifest; reference tests reject drift between projections.

`max_entities` is the only user-resolvable budget (default `500`, bounded by
the schema). The remaining values are fixed v1 constants: 20,000 files,
4 MiB/file, 64 MiB decoded source, 96 MiB encoded stdin, JSON depth 64,
8 MiB strings, 100,000 total/20,000 per collection items, 100,000 model
records, 16 MiB stdout, 64 KiB stderr, 60 seconds, 512 MiB V8 old-space,
type depth 16, 512 type nodes/prop, 64 union/intersection members, 256 nested
properties, 16 signatures/component, 10,000 flow visits, and 64 alias edges.
There is no silent truncation and no v1 total-RSS promise.
