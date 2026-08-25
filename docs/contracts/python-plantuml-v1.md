# Python PlantUML v1

`python.snapshot.puml` is the deterministic visual projection of the Python
semantic snapshot. It is UTF-8 without a BOM, uses LF line endings, and ends
with exactly one LF.

The document order is fixed: preamble, the optional incomplete-snapshot note,
one package block for every selected module, internal relation lines, the
Japanese legend, and `@enduml`. Package, class, member, and relation order is
the order defined by the Python semantic v1 contract.

Module aliases are `M_` followed by the full SHA-256 of
`python:module:<module>`. Class aliases are `C_` followed by the full SHA-256
of the semantic entity ID. A selected module without a class contains one
`classなし` note whose alias is `N_EMPTY_` followed by the full SHA-256 of
`python:module-empty:<module>`.

Only internal relations are rendered. Inheritance, composition, typed
dependency, and import dependency use the fixed Japanese labels `継承`, `合成`,
`型依存`, and `import依存`. Multiple semantic relations with the same kind,
rendered endpoints, and label produce one visual line; this does not remove
relations from semantic JSON.

Member signatures contain identifiers, the closed semantic type grammar, and
fixed punctuation only. Default values are represented by ` = …`; source
literals and function bodies are never included. The first implicit `self` or
`cls` receiver is omitted only for the applicable method kind, after which
positional-only `/`, keyword-only `*`, `*args`, and `**kwargs` markers are
recalculated from the visible parameters.

All user-derived labels are NFC-normalized and escaped. Backslash, quote, LF,
CR, and TAB use `\\`, `\"`, `\n`, `\r`, and `\t`. Other control, format,
surrogate, line-separator, and paragraph-separator code points use uppercase
four- or eight-digit Unicode escapes. The output contains no timestamps,
absolute paths, source literals, or invented nodes for external or unresolved
relations.
