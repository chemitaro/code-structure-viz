# Next PlantUML contract v1

Status: pre-implementation normative contract for Issue #8.

## Encoding and line grammar

- UTF-8 without BOM, LF line endings, exactly one statement per line, and a
  final LF. No blank line, comment, raw compiler text, or second statement is
  allowed.
- Exact line templates, in this order, are:

  ```text
  @startuml
  title CodeStructureViz Next snapshot
  note top: status=<complete|partial_safe>; coverage=<complete|partial_safe>
  legend
  N_P project
  N_M module
  N_C component
  .. prop/import/export member
  --> static_import|literal_dynamic_import
  ..> jsx_render|component_wrap
  marker=client_entry|router_context=<context>|client_dependency|server_candidate|unknown
  marker=partial_safe
  endlegend
  package "P:<project-id>" as N_P_<64hex> {
  }
  component "M:<escaped-path>" as N_M_<64hex>
  rectangle "C:<escaped-declaration-key>" as N_C_<64hex>
  N_M_<64hex> .. "export|import <escaped-name>" : <member-id>
  N_C_<64hex> .. "prop <escaped-name>" : <member-id>
  N_M_<64hex> --> N_M_<64hex> : <static-import|literal-dynamic-import>
  N_C_<64hex> ..> N_C_<64hex> : <jsx-render|component-wrap>
  cloud "external:<escaped-specifier>[#<escaped-export>]" as X_<64hex>
  @enduml
  ```

  Entity/member/relation rows are omitted when their validated collection is
  empty; the header, status note, complete legend, and end marker remain.
- `@startuml`, title, status note, legend, packages, modules, components,
  members, external frontier declarations, relations, and `@enduml` are the
  only statement classes. A parser rejects any line outside these templates.
- Aliases are `N_M_<64 lowercase hex>` for Modules, `N_C_<64 lowercase hex>`
  for Components, and `N_P_<64 lowercase hex>` for projects.
- Input collection order never controls output; projects, modules, components,
  members, and relations sort by canonical semantic identity, with relation
  ties broken by kind then target identity. External frontier declarations sort
  by target digest. The same order is used for JSON and PlantUML.
- A module marker is ordered as `client_entry`, its non-`none` router context,
  then sorted derived roles; an empty marker list emits `unknown`. A
  `client_entry|server_candidate` combination is the explicit dual-role form.

## Escaping

Display labels are NFC-normalized, then escaped by this closed table before
they enter a quoted PlantUML label:

| input | emitted bytes |
| --- | --- |
| backslash | `\\` |
| quote | `\\"` |
| tab, CR, LF | `\\t`, `\\r`, `\\n` |
| semicolon | `\\;` |
| `<` or `>` markup delimiter | `\\u003c` or `\\u003e` |
| any other ASCII control or DEL | lowercase `\\uNNNN` |
| all other code points | unchanged NFC code point |

Escaping is byte-stable and never introduces a newline. Source bodies,
comments, literal values, absolute paths, raw compiler diagnostics, and
package contents are never label inputs.

## Visual vocabulary

- Module and Component use different shapes.
- Export/import/prop members use fixed stereotypes.
- Static import/literal dynamic import use `-->`, while JSX render/component
  wrap use `..>`; each relation kind also has a distinct textual label in the
  legend and line template.
- `client_entry`, router context, derived client dependency, server candidate, dual role, unknown, and partial coverage have text/symbol markers in addition to color.
- A boundary crossing is a facet on its underlying static value edge and does not create a duplicate edge.

The fixed legend names every shape, stereotype, arrow, boundary marker,
`unknown`, and `partial_safe` marker. Markers are semantic text/symbols in
addition to color, so a consumer does not need color perception to distinguish
roles. Data-only exact-byte goldens cover complete-empty, complete non-empty,
partial-safe, and malicious label/control-character vectors.

## Validation

The writer rejects unknown aliases, duplicate semantic identities, unsafe labels, absolute paths, out-of-order rows, missing legend/status, dangling relations, and any statement outside this grammar. JSON and PlantUML must be rendered from the exact same Python-validated model subset.
