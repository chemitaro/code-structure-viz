# SQLAlchemy PlantUML v2

SQLAlchemy snapshot の PlantUML contract は
`code-structure-viz.plantuml/sqlalchemy/v2` である。入力はtarget selection済みのimmutable
`SqlAlchemySnapshot`だけであり、AST、SQLAlchemy runtime、DB、source textを読まない。
スナップショットの事実からPlantUML専用のimmutable ER projectionを作り、rendererはその投影を
IE (Information Engineering) 記法へ機械的に変換する。semantic JSON v1のshape、relation id、
redaction ruleは変更しない。

document skeletonは次で固定する。

```text
@startuml
title SQLAlchemy ER snapshot
top to bottom direction
hide circle
skinparam linetype ortho
hide methods
entity "<safe display>" as T_<64 lowercase table-id hex> {
  <compact column and constraint rows>
}
T_<source> <left-endpoint>--<right-endpoint> T_<target> : foreign_key <safe row name>
T_<source> <left-endpoint>..<right-endpoint> T_<target> : relationship <safe row name>
T_<child> --|> T_<parent> : inheritance
T_<source> .. T_<secondary> : association <safe row name> [source=? target=?]
legend right
  rule_version=code-structure-viz.sqlalchemy-redaction/v1
  redacted_values=<canonical nonnegative ASCII decimal>
  ||--|| exactly_one
  |o--o| zero_or_one
  }o--o{ zero_or_many
  }|--|{ one_or_many
  -- foreign_key (solid)
  .. relationship (dotted)
  --|> inheritance (not cardinality)
  .. association metadata (cardinality unknown)
  [?] evidence insufficient; plain line retained
  [redacted] literal/expression value omitted
endlegend
@enduml
```

UTF-8、BOMなし、final LF exactly oneとする。zero-table snapshotもheader、legend、redaction
metadata、`@enduml`を同じ順で持つ。entityは上から下へ並び、関係線はentity定義の後に置く。

## IE endpoint

左endpointはsource側、右endpointはtarget側である。円 `o` は0、縦棒 `|` は1、crow-foot
`{`または`}`は多を表す。`--`は物理FK、`..`はORM relationshipを表す。

| multiplicity | 左endpoint | 右endpoint |
| --- | --- | --- |
| exactly 1 | `||` | `||` |
| 0..1 | `|o` | `o|` |
| 0..N | `}o` | `o{` |
| 1..N | `}|` | `|{` |

FKではsource最小件数は常に0、local FK tupleの既知candidate key性からsource最大件数を求める。
target最大件数はtarget columnsが既知PK/UNIQUE全体を含む場合だけ1とし、local columnsの
nullableが全てfalse (PKも含む) の場合だけtarget最小件数を1とする。partial-safe snapshotで
unique evidenceがないことをnon-uniqueとは解釈しない。

ORM relationshipの`MANY`はtarget `0..N`、`SCALAR`はnullableを証明できるFKがある場合だけ
`1`または`0..1`とする。それ以外や`UNKNOWN`はcrow-footを捏造せず、plain lineと
`[source=? target=?]`を出力する。exact reciprocal `back_populates`は双方のnavigation形状を
pairingするが、`secondary`が片側だけ、または異なる場合はpairとして扱わない。両側が同じ
internal `secondary`で`MANY`なら直接のN:N edgeを1本だけ出力する。association metadataだけ
からsynthetic physical FKは作らない。

複合PKはinline `primary_key=True`列全体を一つのcandidate keyとして扱い、個々のsingleton行を
独立したunique keyとは解釈しない。expression indexはuniqueness inferenceに使わない。

## entity row vocabulary

columnは次のcompact形式である。

```text
  * id : integer (Integer) <<PK, NN>>
  email : string (String) <<UQ, NULL>>
```

`*`と`NN`は必須、`NULL`はnullable、`?NULL`は不明である。stereotypeは`PK`、`FK`、`UQ`、
`IX`、`NN`、`NULL`、`?NULL`の閉じた語彙だけを使う。type parameters、default、join、
check expressionなどの値は出力せず、descriptorは既存redaction summaryと必要な
`[redacted:<category>]`で表す。

制約行は `primary_key ... columns=(...)`、`unique ... columns=(...)`、
`check ... expression=<redacted token>`、`index ... terms=...`、
`foreign_key ... local=(...) references=<target>(...) ...`、
`relationship <name> : <scalar|many|unknown> target=... uselist=... back_populates=... secondary=...`、
`inheritance target=...`、`association_table ... source=... target=...`である。entity内の行は
snapshot member orderを維持し、columnとconstraintの境界に`  --`を一度置く。

## display escaping

PlantUML entity/table components use `escape_plantuml_label` so schema/table components and
their owned separator remain injective. Human-facing row values use the separate
`escape_plantuml_display_label` projection. It preserves common identifier punctuation,
including `_` and `.`, while still encoding quotes, braces, control characters, and other
syntax-sensitive code points. This keeps names such as `authentication_identity_id` readable
without weakening PlantUML syntax safety. Display escaping does not change semantic JSON.

## safety and compatibility

external/unknown targetのsynthetic entity/edgeは生成しない。table aliasはhashed table idだけから
作り、path、source range、row id、URL、token、raw expressionを出力しない。`redacted_values`は
snapshot coverageを唯一のauthorityとする。PlantUML v1は旧exact skeletonの履歴として保持し、
新しい出力はv2だけを公開する。run-manifest root v1、semantic v1、`sqlalchemy-ast/1`は維持する。
