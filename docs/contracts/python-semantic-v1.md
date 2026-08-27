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

## Diff projection

`python.diff.semantic.json` は snapshot の entity/member/relation identity を before/after の
二つの immutable side へ適用した projection である。root は `type: "semantic_diff"`、
`document_kind: "diff"`、`status`、`before`、`after`、`before_snapshot_sha256`、
`after_snapshot_sha256`、`file_change_set`、`semantic_change_set`、`diagnostics` を持つ。
`semantic_change_set` は entity/member/relation の delta、changed seed、before/after relation
union から得た `impact.upstream`/`impact.downstream`、高信頼 move の `matching` を含む。

side は `real`、`canonical-empty-side`、`analysis-failed` のいずれかで、analysis failure を
empty side や推測した added/removed へ変換しない。canonical empty は `domain`、
`document_kind: "internal-diff-side"`、空配列だけを key-sort した bytes とし、endpoint や source
body を含めない。diff serializer は source bytes、patch body、comment、literal、secret、
absolute path を受け取らず、metadata-only `file_change_set` は別契約で検証する。

semantic seed は class/decorator/member/relation の実質的な変更を含む entity ID であり、
空白・comment・import order のみの変更は seed にしない。impact の traversal は before/after
relation union を使い、削除 entity の before edge も保持する。move は同名または qualified name
の証拠、exact structural fingerprint、unique one-to-one candidate の全条件を満たした場合のみ
生成し、曖昧な候補は removed+added とする。
