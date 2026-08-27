# SourceView v1

`code-structure-viz.source-view/v1` はrun開始時のGit working treeをrepository外の
private stagingへ固定する内部contractである。target repositoryへはread-only Git
allowlistだけを実行し、analyzerはmutableなrepository pathを再読しない。

fingerprintは次のfield orderのcanonical JSON bytes（UTF-8、NFC、LF一つ）のSHA-256で
ある。`fingerprint`自身はpreimageへ含めない。

```json
{"schema":"code-structure-viz.source-view/v1","kind":"working-tree","head_commit":"1111111111111111111111111111111111111111","files":[{"path":"src/domain/order.py","kind":"regular","resolved_target":null,"size_bytes":3,"sha256":"ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"}],"failures":[]}
```

上記exampleのfingerprintは
`3f35282e8940cdf7c783adc4880d7797eaf6d6b8d1bb78b49d5c9e237f09b531` である。
fileはpathのUTF-8 byte順、failureはpath、stage、diagnostic code順に並ぶ。
unborn HEADだけが `head_commit: null` になる。

Git path bytesを一件でもstrict UTF-8 decodeできない場合は `CSV-SOURCE-003` の
run fatalとし、SourceView、fingerprint、Artifactを作らない。NFC/case-inode collisionは
`CSV-SOURCE-004`、repository外・cycle・non-regular symlinkは `CSV-SOURCE-002` とし、
該当pathからwinnerを選ばない。publication直前のHEADまたはfingerprint差は
`CSV-SOURCE-001` のrun fatalである。

## Diff acquisition

diff の commit side は `GitRepositoryReader.enumerate_commit_tree` で tree を一度列挙し、
`read_commit_blob` で各 blob を一度だけ読み取って SourceView を構成する。blob/object の欠落や
read failure は canonical empty side に置き換えず fatal とする。working-tree side は run 開始時の
tracked/cached/untracked/unmerged enumeration と同時に `SourceViewBuilder` が inventory を作り、
repository 外の private staging へ freeze する。

内部 inventory は path、raw path、kind、size、digest だけを持つ。これは working-tree の drift と
`FileChangeSet` の A/M/D/T/U/? 判定に使う内部 value で、public SourceView JSON や manifest に source
bytes、temporary path、Git stderr を追加しない。公開直前に HEAD、path enumeration、untracked、
unmerged、inventory/fingerprint を再取得し、開始時と異なる場合は `CSV-SOURCE-001` として全 staging
を破棄する。
