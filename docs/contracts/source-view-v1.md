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
