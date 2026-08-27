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

## Diff run

`diff` は同じ `run-manifest/v1` root を使うが、snapshot の `source`/`request` shape を流用せず、
次の field を追加する。

- `request.from`、`request.to`、`request.pr_target`、resolved traversal depth
- `comparison`: caller の requested endpoint、resolved before/after object、endpoint kind、start HEAD anchor、
  selected base candidate、merge-base、resolution method
- `sources.before`/`sources.after`: immutable side の schema、kind、head、fingerprint、file count
- `semantic_sides.before`/`semantic_sides.after`: semantic side の kind/digest/status
- `file_change_set`: `code-structure-viz.file-change-set/v1` object
- `changed_path_budget`: requested/resolved/actual/source

diff Artifact descriptors は `file-changes.json`（`file-change-set`）、requested format の
`python.diff.semantic.json`、`python.diff.puml` の順に並ぶ。domain `artifact_paths` には semantic
JSON/PlantUML のみを記録し、file-change descriptor は run-level `artifacts` に残す。analysis
failure、entity budget overrun、unmerged path は `incomplete_kind: "payload_unavailable"`、
`payload_available: false` とし、affected semantic payload を列挙しない。changed-path overrun、
endpoint/object/drift/security failure は manifest を作らない run fatal である。

`DiffManifestBuilder` の run fingerprint preimage は endpoint、sources、semantic side、file-change
metadata、budget、status を含む。output directory、staging path、timestamp、PID、source body、Git
stderr は含まれない。同一入力で key order、Artifact bytes、descriptor SHA-256 が一致する。
