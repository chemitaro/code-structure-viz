# CLI v1

`code-structure-viz snapshot` は `--repo PATH`、`--output-dir PATH`、
`--domain python|sqlalchemy` を必須とする。domain 省略、`all`、`next`、
positional target、option alias、短縮形、大小文字違いは受理しない。

## Issue #8 で追加する Next snapshot branch

現在の実装境界は上記のとおりだが、Issue #8 の production step は `snapshot --domain next`
を追加する。追加後の selector は `next:semantic-json|plantuml`、Artifact は
`next.snapshot.semantic.json` / `next.snapshot.puml` とし、`diff --domain next` は Issue #9
まで受理しない。機械可読な事前契約は `schemas/next-config-v1.schema.json`、
`schemas/next-semantic-v1.schema.json`、`schemas/next-domain-manifest-v1.schema.json`、および
`schemas/run-manifest-v1.schema.json` の Next branch を正本とする。

任意optionは `--config PATH`、反復可能な `--target TARGET`、
`--upstream-depth NON_NEGATIVE_INT`、`--downstream-depth NON_NEGATIVE_INT`、
反復可能な `--format semantic-json|plantuml`、`--max-entities POSITIVE_INT`、
`--stdout SELECTOR` である。single-value optionの重複とformatの重複はexit 2。
format省略時は `semantic-json`、`plantuml` の順で両方を生成する。
Python snapshot は `python.snapshot.semantic.json` / `python.snapshot.puml`、
SQLAlchemy snapshot は `sqlalchemy.snapshot.semantic.json` / `sqlalchemy.snapshot.puml`
を公開する。`--target` の `path:` / `module:` / `class:`、upstream/downstream depth、
entity budget は選択domainの解析結果へ適用する。

`--stdout` は `manifest` または選択domainと一致する
`python|sqlalchemy:semantic-json|plantuml` selectorだけを受理する。別domain selector、
未選択format、unknown selectorはsource acquisition前にexit 2とする。

`snapshot` は `--from`、`--to`、`--pr-target`、`--max-changed-paths` を
`CSV-USAGE-003` で拒否する。`--help` と `--version` は単独のmeta operationで、
source acquisitionとpublicationを行わない。

exit codeはcomplete/not-applicableが0、fatalが1、usage/configが2、incompleteが3、
handled interruptが130である。

## diff command

`diff` は `--repo PATH`、`--output-dir PATH`、`--domain python|sqlalchemy` を必須とし、
`--from REF`、`--to REF`、`--pr-target REF`、`--max-changed-paths POSITIVE_INT` を追加で受理する。
`--from working-tree`、unsafe endpoint token、unresolved local object はそれぞれ usage または
run-fatal として fail closed する。`--to working-tree` は run 開始時の frozen working tree、
`--to head` は開始時 HEAD commit を使う。
SQLAlchemy diff は whole snapshot を比較するため `--target` を受理しない。domain固有optionは
追加せず、endpoint、depth、format、budget、stdoutの意味はPython diffと共通である。

diff の format 省略時も `semantic-json`、`plantuml` の順で生成する。公開される diff Artifact は
`file-changes.json`、選択domainの `python.diff.*` または `sqlalchemy.diff.*`、
`run-manifest.json` で、
entity/path budget または domain side failure 時は affected semantic Artifact を省略する。
`--stdout` は `manifest`、選択domainの `DOMAIN:semantic-json|plantuml` selector を一度だけ
受理し、available Artifact の exact bytes または `stdout-result/v1` を返す。
