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
