# Next PlantUML contract v1

Status: pre-implementation normative contract for Issue #8.

## Encoding and line grammar

- UTF-8 without BOM, LF line endings, exactly one statement per line.
- Order: `@startuml`, title, status/coverage note, legend, project packages, Module entities, Component entities and members, relations, `@enduml`.
- Aliases are `N_M_<64 lowercase hex>` for Modules and `N_C_<64 lowercase hex>` for Components.
- Input collection order never controls output; all rows sort by canonical semantic identity.

## Escaping

Display labels are NFC-normalized. Backslash, quote, tab, CR, LF, PlantUML directive/control characters, and markup delimiters are escaped before rendering. Source bodies, comments, literal values, absolute paths, raw compiler diagnostics, and package contents are never label inputs.

## Visual vocabulary

- Module and Component use different shapes.
- Export/import/prop members use fixed stereotypes.
- Static import, literal dynamic import, JSX render, and component wrap use distinct line styles and textual legend labels.
- `client_entry`, router context, derived client dependency, server candidate, dual role, unknown, and partial coverage have text/symbol markers in addition to color.
- A boundary crossing is a facet on its underlying static value edge and does not create a duplicate edge.

## Validation

The writer rejects unknown aliases, duplicate semantic identities, unsafe labels, absolute paths, out-of-order rows, missing legend/status, dangling relations, and any statement outside this grammar. JSON and PlantUML must be rendered from the exact same Python-validated model subset.
