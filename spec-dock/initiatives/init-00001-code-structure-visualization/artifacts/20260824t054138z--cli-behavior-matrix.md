# CLI Behavior Matrix

## Command grammar

```text
code-structure-viz snapshot --repo PATH --output-dir PATH [OPTIONS]
code-structure-viz diff --repo PATH --output-dir PATH [OPTIONS]
```

Common options:

設計判断: snapshot でも domain 省略時は全 first-party domain を対象にする。diff と対称な one-command agent UX を優先し、Next target 不在時は applicability preflight により Node を要求しない。Next target が存在して adapter が利用不能な場合は `incomplete`/exit 3 とし、暗黙に skip しない。


- `--domain python|sqlalchemy|next` repeatable。
- `--format semantic-json|plantuml` repeatable。未指定は両方。
- `--target path:VALUE|module:VALUE|class:VALUE` repeatable（snapshot/domain semantics に従う）。
- `--config PATH`; auto config creation なし。
- `--upstream-depth N`, `--downstream-depth N`; default 1/1。
- `--max-changed-paths N`; implicit default 1,000。
- `--max-entities N`; default 500 per diagram。
- `--stdout manifest|semantic-json|plantuml`; output directory は引き続き必須。semantic/PlantUML は exactly one domain/format Artifact だけ選択可能。

diff 専用 option: `--from REF`、`--to REF|head|working-tree`、`--pr-target REF`。

## Endpoint matrix

| Use case | --from | --to | Resolved before | Resolved after | Base method / notes |
| --- | --- | --- | --- | --- | --- |
| diff | なし | なし | implicit base | 開始時 frozen working-tree | implicit priority、fail closed |
| diff | REF | なし | exact REF | 開始時 frozen working-tree | REF commit resolve |
| diff | なし | REF | endpoint REF に対する implicit base | exact REF | implicit priority、merge-base with REF |
| diff | REF-A | REF-B | exact REF-A | exact REF-B | 両方 exact |
| diff | REF | head | exact REF | 開始時 HEAD commit | HEAD drift は endpoint を変えない |
| diff | REF | working-tree | exact REF | 開始時 frozen working-tree | fingerprint gate |
| diff | working-tree | 任意 | usage failure | なし | initial scope 外、exit 2 |
| snapshot | N/A | N/A | single SourceView | repository or target source | Git temporal comparison なし |

### implicit base priority

1. explicit CLI `--pr-target REF`。
2. `.code-structure-viz.toml` の configured comparison target/upstream。
3. local `origin/HEAD` symbolic target。
4. existing local refs `main`, `develop`, `master`（configured/remote candidate と duplicate を除く）。
5. candidate endpoint commit との `git merge-base` が最初に成功した commit。

local object/ref だけを使う。auto fetch、shallow deepen、initial commit fallback なし。解決不能は exit 1。

## Domain / format / failure matrix

| Command | Domain selection | Format | Execution | Published output | Exit |
| --- | --- | --- | --- | --- | --- |
| snapshot | domain omitted | format omitted | all applicable domains | JSON+PlantUML per domain | 0/3 |
| snapshot | python | semantic-json | Python only | Python JSON + manifest | 0/3 |
| diff | domain omitted | format omitted | python→sqlalchemy→next | per complete/incomplete domain JSON+PlantUML + manifest | 0/3 |
| diff | next | plantuml | Next only | Next PlantUML + manifest | 0/3 |
| diff | all not applicable | any | three applicability checks | manifest only, all not_applicable | 0 |
| diff | one adapter incomplete | any | other adapters continue | successful siblings retained, aggregate manifest | 3 |
| any | invalid config | any | no adapter | no success Artifact | 2 |
| diff | endpoint unresolved | any | no adapter | no success Artifact | 1 |
| diff | fingerprint drift | any | staging discarded | no success Artifact | 1 |
| any | SIGINT | any | cleanup | no newly published partial output | 130 |

## applicability と partial failure

| Condition | Domain status | Artifacts | Overall |
| --- | --- | --- | --- |
| supported target absent | not_applicable | domain semantic/PlantUML なし、manifest status あり | complete if no incomplete domain |
| target present and fully analyzed | complete | selected formats + manifest descriptor | complete candidate |
| target present but partial parse/protocol/coverage failure | incomplete | safe successful Artifact + diagnostic when available | exit 3 |
| core source/config/output invariant failure | run fatal/usage | success Artifact なし | exit 1 or 2 |

## Exit code contract

| Code | Meaning | Artifact rule |
| --- | --- | --- |
| 0 | selected domains complete/not_applicable | all completed safe Artifacts published |
| 1 | fatal analysis/environment/source/output | success Artifact not published; existing output unchanged |
| 2 | usage/config error | no adapter run; existing output unchanged |
| 3 | one or more selected domains incomplete after valid core run | successful sibling/domain Artifacts and aggregate manifest retained |
| 130 | interrupt | staging cleanup; no newly published incomplete transaction |

## Config matrix

```toml
schema_version = 1
domains = ["python", "sqlalchemy", "next"]
formats = ["semantic-json", "plantuml"]
upstream_depth = 1
downstream_depth = 1
max_changed_paths = 1000
max_entities = 500

[comparison]
target_ref = "origin/main"
upstream_ref = "origin/main"

[paths]
ignore = [".git/**", "dist/**"]
```

Resolution: explicit CLI > explicit/auto-discovered `.code-structure-viz.toml` > built-in。`--config` missing、unknown key、wrong type、unsupported schema version は exit 2。config を自動生成しない。environment variable は analysis behavior を変更しない。resolved config 全体と digest を manifest に記録する。

## Output names and overwrite

Planned deterministic layout:

```text
OUTPUT_DIR/
  run-manifest.json
  file-changes.json                 # diff only
  python.snapshot.semantic.json     # or python.diff.semantic.json
  python.snapshot.puml              # or python.diff.puml
  sqlalchemy.snapshot.semantic.json
  sqlalchemy.snapshot.puml
  next.snapshot.semantic.json
  next.snapshot.puml
```

not_applicable domain の semantic/PlantUML file は生成しない。指定 format 以外を生成しない。いずれかの destination が存在すれば transaction を開始せず nonzero。timestamp suffix で黙って回避しない。

## Budget examples

- implicit diff 1,001 changed paths、override なし: exit 1、downstream parse なし。
- `--max-changed-paths 1500`: explicit opt-in。resolved override と actual count を manifest に記録。
- diagram 501 entity、override なし: affected domain incomplete/exit 3（他 domain success は保持）。truncated diagram は生成しない。
- `--max-entities 750`: explicit opt-in。750 以下なら full diagram、超過なら同じ failure。
