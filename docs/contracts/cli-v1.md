# CLI v1

`code-structure-viz snapshot` は `--repo PATH`、`--output-dir PATH`、
`--domain python` を必須とする。domain 省略、`all`、`sqlalchemy`、`next`、
positional target、option alias、短縮形、大小文字違いは受理しない。

任意optionは `--config PATH`、反復可能な `--target TARGET`、
`--upstream-depth NON_NEGATIVE_INT`、`--downstream-depth NON_NEGATIVE_INT`、
反復可能な `--format semantic-json|plantuml`、`--max-entities POSITIVE_INT`、
`--stdout SELECTOR` である。single-value optionの重複とformatの重複はexit 2。
format省略時は `semantic-json`、`plantuml` の順で両方を生成する。

`snapshot` は `--from`、`--to`、`--pr-target`、`--max-changed-paths` を
`CSV-USAGE-003` で拒否する。`--help` と `--version` は単独のmeta operationで、
source acquisitionとpublicationを行わない。

exit codeはcomplete/not-applicableが0、fatalが1、usage/configが2、incompleteが3、
handled interruptが130である。
