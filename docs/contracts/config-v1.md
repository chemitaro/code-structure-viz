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

解決順はbuilt-in、明示 `--config` またはrepository rootの
`.code-structure-viz.toml` のどちらか一つ、最後にCLI depth/max-entitiesである。
明示configとrepository configはmergeしない。environment/global config/profileは読まない。

unknown table/keyは `CSV-CONFIG-003` の定数messageだけを返し、unknown keyの
raw spelling、正規化値、dotted pathを出力しない。source rootとglobはNFCの
repository-relative POSIX値に限定する。
