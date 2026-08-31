# Diagnostic v1 contract

`schemas/next-diagnostic-catalog-v1.json` is the single authority for the
Next diagnostic code, fixed message, severity, recoverability, outcome, and
safe reference permission. The public `schemas/diagnostic-v1.schema.json`
requires those values for every `CSV-NEXT-*` record; `run-manifest` domain and
top-level diagnostics use the same public record.

`ref_permission` is structural, not advisory:

| permission | public fields |
| --- | --- |
| `none` | `path=null`, `symbol=null` |
| `path` | non-empty relative `path`, `symbol=null` |
| `symbol` | `path=null`, non-empty safe `symbol` |
| `path_or_symbol` | exactly one of `path` and `symbol` |

All Next diagnostics use `domain=next` and `line=null`; source content,
absolute paths, compiler text, and captured stderr are never copied into the
message. The Next domain manifest may carry these public records as its
`diagnostics` array. The stderr writer emits fixed catalog messages only and
never emits raw adapter output. `stdout-result/v1` carries only the typed
outcome/reason projection and never carries a diagnostic body.

The following outcome mapping is normative:

- applicability is `not_applicable`;
- flow, source, and type-local failures are `partial_safe` when the proof
  contract succeeds;
- unsupported runtime patterns are `complete` with an informational record;
- configuration, project, target, trust, process, protocol, identity, and
  resource-limit failures are `payload_unavailable`.
