# Semantic Contract

## 目的と ownership rule

common contract は run lifecycle、provenance、diagnostic、coverage、Artifact descriptor、graph primitive だけを共有する。Python、SQLAlchemy、Next の identity、member、relation、matching、domain-specific rendering は各 adapter が所有する。共通化のために domain semantics を失わない。

## Common envelope v1

```json
{
  "schema": "code-structure-viz.semantic/v1",
  "document_kind": "snapshot",
  "domain": "python",
  "status": "complete",
  "adapter": {"name": "python", "version": "semver", "contract": "v1"},
  "source": {"endpoint_digest": "sha256", "resolved_config_digest": "sha256"},
  "scope": {"mode": "whole-repository", "targets": [], "frontier": []},
  "entities": [],
  "relations": [],
  "coverage": {"discovered": 0, "analyzed": 0, "skipped": 0, "unknown": 0},
  "diagnostics": []
}
```

共通必須 field:

| Field | Contract |
| --- | --- |
| schema | 厳密な versioned identifier。未知の major version は拒否する。 |
| document_kind | `snapshot` または `diff`。両者は別 use case。 |
| domain | `python`、`sqlalchemy`、`next`。`all` は run orchestration であり semantic domain ではない。 |
| status | `complete`、`not_applicable`、`incomplete`。 |
| adapter | adapter name/version/domain contract version。 |
| source | content-addressed endpoint/snapshot/config provenance。absolute path なし。 |
| scope | whole/targeted/diff-context と traversal frontier。 |
| entities/relations | domain schema が所有する payload。 |
| coverage | discovered/analyzed/skipped/unknown と reason count。 |
| diagnostics | stable で safe な diagnostic object。 |

## Diagnostic v1

```json
{
  "code": "python_parse_failed",
  "severity": "error",
  "domain": "python",
  "recoverability": "domain_incomplete",
  "location": {"path": "src/domain/model.py", "line_range": [12, 12]},
  "message": "Python source could not be parsed safely."
}
```

`message` と `location` に source line/body、literal、comment、secret、absolute temporary path を含めない。adapter stack trace は debug log へも default 出力しない。

## Snapshot identity

### Python

- entity identity: `{normalized_module_path}::{qualified_class_name}`。
- nested class: qualified name に outer chain を含む。
- members: field、method、property、decorator metadata。member identity は entity identity + kind + declared name/signature key。
- relations: inheritance、composition、typed_dependency、import_dependency。relation identity は source/kind/target/role key。
- type/signature は safe canonical expression。body/docstring/comment/default literal は除外。

### SQLAlchemy

- table identity: `{normalized_schema_or_null}.{table_name}`。module path は provenance。
- rows: column、primary_key、foreign_key、unique、check、index、relationship、inheritance、association_table。
- row identity: table identity + row kind + explicit declarative name または stable structural key。
- ForeignKey と relationship は別 relation kind。
- default/server_default literal は value を保持せず `{present, category, redacted: true}`。

### Next

- component identity: `{repository_relative_module_path}::{exported_component_name}`。
- default export は stable exported-name metadata。route path は attribute で identity ではない。
- members: props、import/export metadata、use-client boundary metadata。
- relations: static_import、literal_dynamic_import、jsx_render、client_boundary_crossing。
- non-literal dynamic behavior/runtime tree は relation を生成せず unknown diagnostic。

## Targeted snapshot and graph primitive

- whole repository snapshot は domain 全構造を所有し、entity budget を超えれば truncation せず failure/incomplete。
- path/module/class target snapshot は resolved seed と upstream/downstream frontier を別々に保持する。
- graph edge common primitive は source identity、target identity、domain relation kind、direction、safe role、source provenance を持つ。kind の意味は adapter-owned。

## Diff envelope v1

```json
{
  "schema": "code-structure-viz.semantic/v1",
  "document_kind": "diff",
  "domain": "python",
  "before_snapshot_sha256": "digest",
  "after_snapshot_sha256": "digest",
  "file_change_set_ref": "run-manifest:file-changes",
  "semantic_change_set": {
"entities": [],
"members": [],
"relations": [],
"seeds": [],
"impact": {"upstream": [], "downstream": []}
  }
}
```

### FileChangeSet separation

FileChangeSet は Git A/M/D/R/C/T/U/?、path、previous path、safe hunk range、requested/resolved endpoint を evidence として持つ。Git hunk と R/C は candidate/provenance であり semantic change の truth ではない。

### SemanticChangeSet

- before/after snapshot の domain model を比較する。
- member または relation delta がある entity を changed seed とする。
- whitespace/comment/import-order-only は seed にしない。
- impact graph は before/after relation union、upstream/downstream は別 collection、default depth 1 each。
- removed entity は before edge で context を得る。
- diff output は seed と configured context だけ。whole structure は snapshot responsibility。

## Matching contract

moved を採用するには以下をすべて満たす。

1. before/after candidate が one-to-one。
2. domain identity/name change または Git rename evidence がある。
3. domain-owned structural fingerprint が threshold-free exact policy を満たす。
4. candidate が unique で competing match がない。
5. raw literal/body/secret を fingerprint に含めない。

条件不足または曖昧なら removed + added。Git R/C だけで moved にしない。

## Member-level visual contract

| Status | Text marker | Color | Additional cue |
| --- | --- | --- | --- |
| added | `+` | green | solid |
| removed | `-` | red | dashed / ghost row |
| modified | `~` | yellow | safe before→after value |
| moved | `→` | blue | matching evidence reference |
| unknown | `?` | gray | diagnostic/coverage reference |

Python field/method、ER row、Next props/import/relation に同 vocabulary を適用する。dark mode と color-blind access のため marker/line/legend を必須とする。

## Versioning and compatibility

- common envelope major change は new schema identifier。
- additive optional field は same v1 minor tool release で許可するが、unknown field tolerant reader を contract test する。
- domain payload version は adapter metadata で別管理し、common envelope に domain field を昇格させない。
- Next bridge `code-structure-viz.next-adapter/v1` は semantic envelope とは別 protocol version。
