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

## diff command

`diff` は `--repo PATH`、`--output-dir PATH`、`--domain python` を必須とし、
`--from REF`、`--to REF`、`--pr-target REF`、`--max-changed-paths POSITIVE_INT` を追加で受理する。
`--from working-tree`、unsafe endpoint token、unresolved local object はそれぞれ usage または
run-fatal として fail closed する。`--to working-tree` は run 開始時の frozen working tree、
`--to head` は開始時 HEAD commit を使う。

diff の format 省略時も `semantic-json`、`plantuml` の順で生成する。公開される diff Artifact は
`file-changes.json`、`python.diff.semantic.json`、`python.diff.puml`、`run-manifest.json` で、
entity/path budget または domain side failure 時は affected semantic Artifact を省略する。
`--stdout` は `manifest`、`python:semantic-json`、`python:plantuml` の closed selector を一度だけ
受理し、available Artifact の exact bytes または `stdout-result/v1` を返す。
