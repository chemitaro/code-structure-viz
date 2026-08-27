# FileChangeSet v1

`code-structure-viz.file-change-set/v1` は diff run の repository-relative metadata だけを表す。
これは semantic snapshot の代替ではなく、変更 path の admission と semantic result の provenance
を検証するための run-level evidence である。

```json
{"schema":"code-structure-viz.file-change-set/v1","before":"<sha-or-null>","after":"<sha-or-null>","files":[{"status":"M","old_path":"src/app.py","new_path":"src/app.py","hunks":[{"old_start":1,"old_line_count":1,"new_start":1,"new_line_count":1,"ordinal":0,"hunk_id":"<sha256>"}]}]}
```

許可される status は `A`、`M`、`D`、`R`、`C`、`T`、`U`、`?`。rename/copy は old/new path、
それ以外は該当する path を持つ。path は UTF-8 strict decode、NFC normalize、repository-relative の
安全な POSIX path で、全配列は UTF-8 byte order へ正規化する。

各 hunk は old/new の start と count、0 起点の ordinal、status/path/range/ordinal から生成した
SHA-256 `hunk_id` だけを持つ。patch body、context、added/deleted line、source body、comment、
literal、secret、absolute path は schema 上も serializer 上も存在しない。

commit-to-commit の production path は Git の `--name-status -z` metadata と immutable commit blob
bytes を使う。working-tree は開始時 inventory と private frozen bytes の差から range を計算し、Git
working-tree patch を取得しない。互換用 `parse_unified_hunks` helper は 16 MiB payload、128 KiB line
の上限、quoted path decode、matching path 必須を検証し、不正入力を成功扱いしない。

`before`/`after` は comparison endpoint の commit digest（working-tree 側は null）であり、path や
source content の公開を意味しない。

Git reader が保持する raw UTF-8 path spelling と NFC canonical path は内部 identity として一緒に検証する。
同一 source または cross-side で異なる raw spelling が同じ canonical pathへ収束する場合、mapやbudgetの
前に `CSV-DIFF-003` の run fatal とし、どちらか一方を採用した FileChangeSetを公開しない。同一 raw spelling
の再観測は許可するが、raw spelling自体はこの public schemaへ追加しない。

mode `160000` のgitlinkはnested sourceへ展開せず、親側の同一path一件へ集約する。tracked/staged/untracked
 dirtyの観測には、Gitの変換・属性・index flagを閉世界で検証した内部profileが必要であり、profileが成立しない
場合はraw bytesを比較して成功扱いせず、初期観測を`CSV-DIFF-003`、公開直前のstate driftを`CSV-SOURCE-001`
としてrun fatalにする。profileやnested content digestはこのpublic schemaへ追加しない。

untracked path集合を決める `--exclude-standard` の ignore authority も内部で閉じる。local/worktree の
`core.excludesFile`、`include.*`、`includeIf.*` は値を解決せずキー存在だけで unsupported とし、初期観測を
`CSV-DIFF-003`へ倒す。許可された authority は検証済み working tree 内の regular `.gitignore` と検証済み
Git dir の regular `info/exclude` に限り、内容と安全な署名をbounded digest化する。開始時と公開直前の
`UntrackedObservation`（digestとdeterministic path集合）が一致しない場合は`CSV-SOURCE-001`とし、実在する
untracked pathを外部ignoreで隠した成功結果、changed-path budgetの過小count、nested gitlinkのclean縮退を
公開しない。authority digestは内部stateだけに保持し、public FileChangeSetのshape/versionは変更しない。
