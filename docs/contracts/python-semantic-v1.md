# Python semantic v1

Python adapter `python-ast/1` はimmutable SourceView bytesだけをPython 3.12 grammarの
ASTへparseする。対象sourceをimport・executeせず、`compile`、`eval`、dynamic import
Callをsemantic evidenceとして使わない。

module identityは最長matching source rootからのrelative `.py` pathで作る。
末尾 `__init__` は除き、root直下だけは `__init__` とする。invalid identifier、keyword、
module/class collisionではwinnerを選ばない。

entityはdirect module/class bodyのclassだけである。memberはfield、property accessor、
methodから成り、IDはclosed identity tupleのNUL-separated UTF-8 bytesのSHA-256である。
relationはdependentからdependencyへ向き、`inheritance`、`composition`、
`typed_dependency`、`import_dependency`だけを持つ。

type textはsymbol、subscript、tuple、union、`None`、ellipsis、unknown markerのclosed
grammarに限定する。`Literal`の値と`Annotated` metadataは `?` へredactする。
builtin、typing helper、active type parameterはrelationから除外し、explicit importは
external、解決不能なsymbolだけをunknownとして `CSV-PY-008` にする。

whole modeはsafe module/class index全件をselectionへ含め、classless moduleを落とさない。
targeted modeはpath/module/classをexact解決し、一件でもmissing・ambiguous・failed seedが
あればpayload unavailableにする。membership edgeはdepth 0、semantic relationはdepth 1で、
depth-limit frontier自体はdiagnosticを生成しない。
