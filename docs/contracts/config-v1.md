# Config v1

設定schemaは `code-structure-viz.config/v1` で、次のshapeだけを受理する。

```toml
schema = "code-structure-viz.config/v1"

[python]
source_roots = ["src", "."]
include = ["**/*.py"]
exclude = []

[traversal]
upstream_depth = 1
downstream_depth = 1

[limits]
max_entities = 500
```

`[python]` はPython source inventoryの設定であり、`snapshot --domain python` と
`snapshot --domain sqlalchemy` の両方が同じfrozen bytes、source roots、include/excludeを使う。
SQLAlchemy snapshotはAST-onlyで解析し、runtime SQLAlchemy packageやDB設定を読まない。
v1に `[sqlalchemy]` tableはなく、SQLAlchemy固有の接続URL、engine、metadata import設定は
unknown keyとして拒否する。`diff` は引き続きPython domain専用である。

`diff` で暗黙の比較候補を設定する場合だけ、任意の `comparison` table を追加できる。
両方とも省略可能で、指定された値は解決済み設定の `resolved.comparison` に同じ
NFC 正規化済み文字列として記録される。

```toml
[comparison]
target_ref = "refs/remotes/origin/main"
upstream_ref = "refs/remotes/origin"
```

`target_ref` は比較対象ブランチ候補、`upstream_ref` は upstream の参照名前空間候補である。
どちらも Git endpoint の解決候補にだけ使われ、解決できない場合は比較を安全に
中止する。`resolved.comparison` を含む場合は `target_ref` と `upstream_ref` の両方を
持ち、未指定側は `null` とする。

解決順はbuilt-in、明示 `--config` またはrepository rootの
`.code-structure-viz.toml` のどちらか一つ、最後にCLI depth/max-entitiesである。
明示configとrepository configはmergeしない。environment/global config/profileは読まない。

unknown table/keyは `CSV-CONFIG-003` の定数messageだけを返し、unknown keyの
raw spelling、正規化値、dotted pathを出力しない。source rootとglobはNFCの
repository-relative POSIX値に限定する。
