# Run manifest v1

Every valid core snapshot run publishes `run-manifest.json`, including
`not_applicable` and `payload_unavailable` outcomes. Usage errors, run-level
fatal errors, and handled pre-publication interrupts publish no manifest.

The manifest identifies the tool and Python AST adapter versions, resolved
command and target request, immutable working-tree source fingerprint,
resolved configuration and value sources, run outcome, Python domain outcome,
payload descriptors, and diagnostics. It contains repository-relative paths
only and never contains raw source, an output path, a staging path, a timestamp,
or a process identifier.

`artifacts` contains descriptors for requested and available semantic JSON and
PlantUML payloads in format order. Each descriptor records the final relative
path, media type, exact byte size, and SHA-256 including the final LF. The
manifest deliberately has no descriptor or digest for itself.

The run fingerprint is the SHA-256 of the canonical
`code-structure-viz.run-fingerprint/v1` object containing tool and adapter
versions, source and configuration fingerprints, command formats and stdout
selector, and the normalized target/depth request. Output locations, temporary
paths, wall time, and PID are excluded.

The single Python domain entry distinguishes `complete`, `not_applicable`,
`incomplete/partial_safe`, and `incomplete/payload_unavailable`. It repeats the
semantic coverage object, records the `max_entities` budget decision, lists
only published payload paths, and carries domain diagnostics. Root diagnostics
are reserved for valid-run diagnostics outside the domain; fatal runs have no
manifest.
