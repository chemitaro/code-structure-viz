# SQLAlchemy semantic v1

SQLAlchemy adapter `sqlalchemy-ast/1` はimmutable SourceView bytesだけをPython 3.12
grammarのASTへparseする。対象module、SQLAlchemy package、DB driverをimport・executeせず、
DB接続、reflection、`compile`、`eval`、raw source segmentをsemantic evidenceに使わない。

`sqlalchemy.snapshot.semantic.json` のroot field orderは次で固定する。

```text
type
schema
domain
document_kind
status
incomplete_kind（partial_safeだけ）
source
request
coverage
entities
members
relations
diagnostics
```

root discriminatorは `type: semantic_snapshot`、
`schema: code-structure-viz.semantic/v1`、`domain: sqlalchemy`、
`document_kind: snapshot` である。payload documentのstatusは `complete` または
`incomplete / partial_safe` だけであり、`not_applicable` と
`payload_unavailable` のsemantic documentは生成しない。JSON bytesはexisting canonical
encoderのUTF-8、BOMなし、余分な空白なし、final LF exactly oneを用いる。

## Entity、row、relation

table entityは `id`、`kind`、`schema_name`、`name`、`display_name`、
`mapping_kind`、`mapping_sources` の順で持つ。table IDはschema/tableだけのclosed
canonical preimageのSHA-256であり、module、path、rangeを含めない。

IDはlowercase SHA-256 hexへそれぞれ `sqlalchemy:table:`、`sqlalchemy:row:`、
`sqlalchemy:relation:` を付ける。table preimageはschema/table、row preimageはowner table ID、
row kind、kind-specific semantic identity、relation preimageはrelation kind、source/target table ID、
via member ID、roleだけへ閉じる。raw expression、default、check/join body、source path/range、
declaration orderをID preimageへ入れない。

row common prefixは `id`、`owner_id`、`kind`、`name`、`source` の順である。続くfieldは
kindごとに次へ閉じる。

- `column`: `type`、`nullable`、`primary_key`、`unique`、`index`、`default`、
  `server_default`、`onupdate`、`server_onupdate`、`computed`、`identity`
- `primary_key` / `unique`: `columns`
- `check`: `expression`
- `index`: `unique`、`terms`
- `foreign_key`: `local_columns`、`target`、`target_columns`、`ondelete`、`onupdate`
- `relationship`: `target`、`cardinality`、`uselist`、`back_populates`、`secondary`、
  `primaryjoin`、`secondaryjoin`、`order_by`、`foreign_keys`
- `inheritance`: `target`
- `association_table`: `source_table`、`relationship_target`、
  `relationship_member_id`

relationは `id`、`kind`、`source_id`、`target`、`via_member_id`、`role`、`source` の順で、
selected source/target双方が存在するinternal relationだけを含む。kindは `foreign_key`、
`relationship`、`inheritance`、`association` に閉じる。external/unknown targetはrow target
descriptorへ残し、synthetic entity/relationを作らない。

table、row、relation配列はimmutable modelのcanonical orderをそのまま使用し、serializerで
再sort、dedupe、winner選択を行わない。source locationはrepository-relative `path` と
`start_line`/`end_line`だけを公開する。adapter-internal UTF-8 byte column spanはsemantic JSON、
coverage、diagnosticへ公開しない。

non-lossy exact duplicateはmodel層でsource location最小の一件へcanonicalizeする。unnamed
checkとexpression termを含むunnamed indexだけがlossyであり、同じAST declarationの
repository-relative pathとfull internal UTF-8 byte spanが一致する再発見だけをdedupeする。
distinct occurrence/conflictはrowを公開せず、各occurrenceをraw textなしの
`sqlalchemy:occurrence:<64 lowercase hex>` symbolへhashして `CSV-SA-009` を保持する。
serializerはこの判定を再実行しない。

## Redaction と coverage

default/check/join/order/type parameter等のvalueは
`{present, category, redacted}` だけへ縮退する。present valueは常に
`redacted: true`、absent valueはcategory `absent`かつ`redacted: false`である。raw literal、
SQL body、URL、token、AST/source text fieldを追加しない。

coverage field orderは `candidate_files`、`parsed_files`、`failed_files`、
`evidence_files`、`selected_modules`、`mapped_classes`、`association_tables`、
`selected_entities`、`unknown_declarations`、`frontier`、`redaction` である。
`mapped_classes`、`association_tables`、`unknown_declarations` はselection前のfull safe
analysis countを保持し、`selected_modules`、`selected_entities`、redaction summaryだけがfinal
selected payloadへ対応する。

redaction summaryは `rule_version: code-structure-viz.sqlalchemy-redaction/v1` と
`redacted_values` を持つ。これはsemantic JSON、PlantUML、manifestが共有する唯一のsummary
authorityであり、rendererで再集計しない。

## Schema boundary

`schemas/semantic-v1.schema.json` はexisting Python snapshot/diff branchとSQLAlchemy snapshot
branchのclosed unionである。SQLAlchemy diff、cross-domain entity/row/relation、unknown row
kind、kind外field、raw expression field、internal byte-column fieldを拒否する。SQLAlchemy
diagnosticは `CSV-SA-001`〜`CSV-SA-013` とそのclosed message/severity/contextだけを受理する。
