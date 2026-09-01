# Next PlantUML contract v1

Round 12 review state: `review_status: fail` (P0=0, P1=8, P2=0) at exact SHA
`48266f813353a7fd78e4e15d72ff6d33c4142827` (CI `33435802167`, 7/7 success).
The PlantUML grammar remains a pre-implementation data-only contract. Its
external relation target grammar and the same model/publication projection are
covered locally, but fresh exact-SHA Strict is pending, readiness is
unconfirmed, and production implementation has not started.

Round 13 review state: Strict reviewed SHA `991516bf730f4f2ddb3d15067702dcfae95ec6b1`
with CI run `33446911714` (7/7 success) and returned `review_status: fail`,
P0=0, P1=9, P2=1. The data-only renderer contract binds PlantUML bytes to the
full validated semantic model and root artifact digest; graph vectors include
double alias, default-excluding star, and separate cycle/conflict unavailable
outcomes. Fresh exact-SHA Strict is pending, readiness is unconfirmed, and
production implementation has not started; this local record does not claim
pass.

Status: pre-implementation normative contract for Issue #8. The renderer in
`tests/contracts/next_reference_validation.py`, this document, the independent
parser in the same module, and the exact goldens are one contract. A change to
one requires all four to be updated together.

## Encoding and fixed statement order

Output is UTF-8 without BOM, LF-only, exactly one statement per line, and ends
with one final LF. There are no blank lines, comments, raw compiler messages,
source bodies, or second statements. The fixed prefix is:

```text
@startuml
title CodeStructureViz Next snapshot
note top: status=<complete|partial_safe>; coverage=<complete|partial_safe>
legend
N_P project
N_M module
N_C component
<<export_binding>> export member
<<import_binding>> import member
<<prop>> prop member
--> static_import|literal_dynamic_import
..> jsx_render|component_wrap
facet=role:<value|type>|reexport=<true|false>|boundary=<none|server_to_client_entry>
marker=client_entry|router_context=<context>|client_dependency|server_candidate|unknown
marker=partial_safe
external=cloud-after-components-before-members
sort=kind-prefixed-id-utf8
endlegend
```

The remaining statement templates are:

```text
package "P:<project-id>" as N_P_<64hex> {
}
component "M:<escaped-path>" as N_M_<64hex>
N_M_<64hex> : marker=<markers>
rectangle "C:<escaped-declaration-key>" as N_C_<64hex>
N_P_<64hex> .. N_M_<64hex> : contains
N_M_<64hex> .. N_C_<64hex> : contains
cloud "external:<escaped-specifier>[#<escaped-export>]" as X_<64hex>
note top: marker=partial_safe
N_C_<64hex> .. "prop <escaped-name>" <<prop>> : <member-id>|optional=<bool>|readonly=<bool>|default=<evidence>
N_M_<64hex> .. "export <escaped-name>" <<export_binding>> : <member-id>|role=value|reexport=<bool>
N_M_<64hex> .. "import <escaped-name>" <<import_binding>> : <member-id>|role=<value|type>|source=<descriptor>
N_M_<64hex> --> N_M_<64hex> : <static_import|literal_dynamic_import>|role=<value|type>|reexport=<bool>|boundary=<none|server_to_client_entry>
N_C_<64hex> ..> N_C_<64hex>|X_<64hex> : jsx_render|occurrences=<count>|contexts=<csv>
N_C_<64hex> ..> N_C_<64hex> : component_wrap|occurrences=<count>|contexts=<csv>
@enduml
```

Rows whose validated collection is empty are omitted. The first header,
legend, and end marker remain; the `partial_safe` note is emitted only for a
partial-safe result. For a non-empty model, packages, modules, components,
containment rows, external frontier clouds, members, and relations are each
sorted by their canonical kind-prefixed ID. External clouds are always after
all containment rows and before any member row. The same validated subset and
ID order feed semantic JSON and PlantUML.

The module marker tokens are ordered as `client_entry`, its non-`none` router
context, then sorted derived roles. If no token exists, the marker is
`unknown`. A direct client-entry seed is never a derived
`client_dependency` or `server_candidate`; only a distinct static-value
closure can provide those roles. A dual role is valid only when two distinct
closures independently prove `client_dependency` and `server_candidate`.

## Shapes, facets, and external frontier

Projects use `package`, modules use `component`, and components use
`rectangle`. Project-to-module and module-to-component containment is explicit
and consumes no graph traversal depth. Export, import, and prop members use
the fixed stereotypes shown in the legend. Static and literal dynamic imports
use `-->`; JSX render and component-wrap relations use `..>`.

Static and dynamic lines carry role, re-export, and boundary facets. A literal
dynamic import is always `role=value|reexport=false|boundary=none`.
`server_to_client_entry` appears only on an internal static value edge from a
server candidate to a client-entry module. It does not create a second edge.
Render/wrap rows carry occurrence count and canonical context CSV. JSX renders
may target an external/unresolved redacted cloud (`X_<64hex>`) using the same
external target descriptor as imports; the source component and the cloud are
the only graph endpoints.

Each external/unresolved target is one redacted `cloud`, keyed by the
SHA-256 of its canonical target descriptor. Its safe package specifier and
optional exported name are the only displayed data; the cloud is never
expanded into target source or a local absolute path.

## Label escaping and aliases

Display values are NFC-normalized and escaped before entering a quoted label:

| input | emitted bytes |
| --- | --- |
| backslash | `\\` |
| quote | `\"` |
| tab, CR, LF | `\t`, `\r`, `\n` |
| semicolon | `\;` |
| `<` or `>` | `\u003c` or `\u003e` |
| other ASCII control or DEL | lowercase `\uNNNN` |
| other code points | unchanged NFC code point |

Aliases are only `N_P_<64 lowercase hex>`, `N_M_<64 lowercase hex>`,
`N_C_<64 lowercase hex>`, and `X_<64 lowercase hex>`. Raw source, comments,
literal values, package contents, absolute paths, and compiler diagnostics are
never label inputs. Escaping never introduces a newline or an unescaped
semicolon.

## Validation and goldens

The parser rejects unknown aliases, duplicate aliases, dangling containment or
relation targets, out-of-order rows, missing legend/status, unsafe labels, and
any statement outside the templates above. Goldens cover complete-empty,
complete non-empty, partial-safe, internal boundary crossing, dual-role,
external literal dynamic import, external JSX render, member facets, and
malicious quote/newline/
markup labels. The exact-byte golden and parser must agree before a renderer
change can be accepted.

## Round 15 authority and boundary propagation

PlantUML is rendered from the same immutable `NextRunDecision` and validated
model as semantic JSON. The renderer does not rebuild roles, source plan,
limits, or target status. `BoundaryRolePropagation/v1` is recomputed from
client/router facts and static value edges: a client-entry seed itself is not
`client_dependency`, its closure targets are; a client app seed is not
`server_candidate`; server traversal stops before a client entry; and dual
role requires two distinct closures. The submitted model roles must equal this
independent result.

For target-related unavailable results, only `next:semantic-json` and
`next:plantuml` may carry the canonical sorted target-failure rows. The reason
enum is `missing`, `component_only`, `duplicate`, `out_of_scope`,
`non_program`, `control_context`, `project_ambiguity`, or `selected_taint`,
with exactly one row per target. All bytes use the existing sorted-key,
NFC-normalized UTF-8 JSON/LF contract; PlantUML aliases and labels remain
deterministic and contain no manual stdout field-order variant.

## Round 16 sealed publication contract

PlantUML is one projection of the immutable `NextRunDecision`; it is never
allowed to rebuild source roles, request/config, limits, toolchain, or target
failures from a fixture. Every decision variant owns a `NextPublicationContext`
whose source view and final source plan came from one
`seal_source_acquisition(intent, reader, inventory)` operation. The intent
contains only project roots, control candidates, and fixed discovery rules;
config, local-extends closure, final paths, and role/effective-role are
derived from frozen bytes and inventory before the seal. No filesystem read is
allowed after it.

The renderer consumes a `ValidatedAdapterRequest` only after the request ID,
file base64/size/digest/canonical bytes, limits, and schema have been sealed.
Response validation precedes rendering in this order: raw response cap,
bounded decode/aggregate, closed schema, base/path/reference/proof checks,
actual model and proof-only counts, model gate, entity gate, then public
selected-copy measurement. A structural resource overrun uses
`CSV-NEXT-LIMIT-003`; malformed, closed-schema, or proof violations use
`CSV-NEXT-PROTOCOL-001`. Exact boundaries are accepted and +1 never reaches a
decoder or renderer.

The public target-unavailable branch retains one sorted `{target_key, reason}`
row per Next selector target, from the eight closed reasons only. Other
branches omit target failures. Roles are derived from facts, router context,
and static value closure: a client seed itself is neither derived role, server
traversal stops before client entry, and dual role requires separate positive
closures. IdentifierName classification uses the checked-in Unicode 15.0.0
table and context-specific predicates for bindings, declaration/export keys,
JSX segments, and external/trusted references. Canonical JSON remains
lexicographic sorted keys, NFC, UTF-8, and LF.

The process launch descriptor is versioned and seals verified Node realpath,
symlink policy, fixed argv, cwd, environment allowlist/denied variables,
stdio, FD inheritance, and process-group termination. Reference capture tests
use a faithful iterable harness and do not claim OS process-level coverage.
Fresh current-SHA Strict remains pending, readiness is unconfirmed, and
production implementation has not started.

## Round 17 renderer boundary

PlantUML is a projection, not a second source of truth. It is rendered only
after the same `PublicationBoundaryDecision` has sealed the response,
validated request identity, model digest, artifact bytes, selector, diagnostic
bytes, and measurements. The renderer cannot rebuild source roles, target
reasons, config, or limits from a fixture, and a substituted PlantUML byte map
is rejected against the decision-owned model and digest.

The corresponding validation path is shown as one sequence in the human
guide: raw cap, bounded decode/aggregate, closed schema, base/path/reference/
proof, actual model/proof-only count, model gate, entity gate, then selected
copy. The role authority remains `BoundaryRolePropagation/v1`: client entry
seeds are not derived roles, server traversal stops before a client entry, and
dual role requires two distinct positive closures. Target-unavailable
PlantUML uses the same one-reason-per-target closed enum and canonical JSON
ordering as semantic JSON. Fresh current-SHA Strict is pending and production
implementation is absent.
