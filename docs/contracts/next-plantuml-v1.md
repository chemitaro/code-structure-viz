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
`unknown`. A module may intentionally emit both `client_entry` and
`server_candidate`; this is a dual role, not a conflict.

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
