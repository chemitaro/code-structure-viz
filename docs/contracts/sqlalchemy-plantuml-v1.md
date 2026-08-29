# SQLAlchemy PlantUML v1

SQLAlchemy snapshot の PlantUML contract は
`code-structure-viz.plantuml/sqlalchemy/v1` である。入力はtarget selection済みのimmutable
`SqlAlchemySnapshot`だけであり、rendererはsource、AST、SQLAlchemy runtime、DBを読まず、
table、member、relationを再sort・dedupe・推測しない。

document skeletonは次で固定する。

```text
@startuml
title SQLAlchemy ER snapshot
left to right direction
skinparam linetype ortho
hide methods
entity "<safe display>" as T_<64 lowercase table-id hex> {
  <closed row lines>
}
T_<source> --> T_<target> : foreign_key <safe row name>
T_<source> ..> T_<target> : relationship <safe row name>
T_<child> --|> T_<parent> : inheritance
T_<source> -- T_<secondary> : association <safe row name>
legend right
  rule_version=code-structure-viz.sqlalchemy-redaction/v1
  redacted_values=<canonical nonnegative ASCII decimal>
  --> foreign_key
  ..> relationship
  --|> inheritance
  -- association table
  [redacted] literal/expression value omitted
endlegend
@enduml
```

UTF-8、BOMなし、final LF exactly oneとする。applicable zero-table snapshotもheader、legend、
redaction metadata、`@enduml`を同じ順で持つ。

## Row vocabulary

entity bodyはsnapshotのmember orderを維持し、次のsingle-line templateだけを使用する。

- `column <name> : <type.category> type=<type.name|-> type_parameters=<token|-> nullable=<true|false|?> primary_key=<true|false|?> unique=<true|false|?> index=<true|false|?> default=<token|-> server_default=<token|-> onupdate=<token|-> server_onupdate=<token|-> computed=<token|-> identity=<token|->`
- `primary_key <name|<unnamed>> columns=<columns>`
- `unique <name|<unnamed>> columns=<columns>`
- `check <name|<unnamed>> expression=<redacted token>`
- `index <name|<unnamed>> unique=<true|false|?> terms=<ordered terms>`
- `foreign_key <name|<unnamed>> local=<columns> target=<target> remote=<columns> ondelete=<token|-> onupdate=<token|->`
- `relationship <name> target=<target> cardinality=<scalar|many|unknown> uselist=<true|false|?> back_populates=<value|-> secondary=<target|-> primaryjoin=<token|-> secondaryjoin=<token|-> order_by=<token|-> foreign_keys=<token|->`
- `inheritance target=<target>`
- `association_table <relationship name> source=<source table> target=<relationship target> relationship_member=<64 lowercase row-id hex>`

各row lineには先頭のASCII spaceを2個付ける。list separatorは`,`で追加spaceはない。
index column termは`column:<name>`、expression termはredacted tokenである。present descriptorは
`[redacted:<category>]`、absent descriptor/string/targetは`-`、unknown boolは`?`、null nameは
`<unnamed>`、unknown targetは`<unknown>`とする。これらはrenderer-owned literalである。

relationはsnapshot順を維持し、sourceとinternal targetがselected payload内にあるedgeだけを描く。
external/unknown targetはrow markerに残し、synthetic entity/edgeを生成しない。table aliasはhashed ID
だけから作り、path、range、row ID prefix、user nameを使用しない。

## Injective label escaping

`escape_plantuml_label`は入力をNFCへ正規化し、Unicode category Letter/Number、ASCII space、
`-`、`/`、`$`だけをそのまま通す。それ以外の各Unicode scalarは
`_U<uppercase 4-6 digit hex>_`へ変換する。

- `"` → `_U0022_`
- `_U0022_` → `_U005F_U0022_U005F_`
- `.` → `_U002E_`
- `_U002E_` → `_U005F_U002E_U005F_`

schema/table componentは別々にescapeし、schemaがある場合だけrenderer-owned literal `.`で結ぶ。
したがって `(schema=a, table=b.c)` は `a.b_U002E_c`、
`(schema=a.b, table=c)` は `a_U002E_b.c`となる。alias、row keyword、metadata key、placeholder、
redaction token、schema/table separatorはrenderer-owned syntaxなのでescapeしない。

## Redaction boundary

`rule_version`と`redacted_values`は`SqlAlchemySnapshot.coverage.redaction`だけをauthorityとし、
rendererでsourceやmemberを走査して再集計しない。metadataは`legend right`直後にrule、countの順で
exactly one回出す。raw default、check、join、order expression、source text、path/range、URL、tokenを
PlantUMLへ出力しない。
