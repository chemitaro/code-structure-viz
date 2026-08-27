# Run manifest v1

Every valid core snapshot run publishes `run-manifest.json`, including
`not_applicable` and `payload_unavailable` outcomes. Usage errors, run-level
fatal errors, and handled pre-publication interrupts publish no manifest.

The manifest identifies the tool and Python AST adapter versions, resolved
command and target request, immutable working-tree source fingerprint,
resolved configuration and value sources, run outcome, Python domain outcome,
payload descriptors, and diagnostics. It contains repository-relative paths
only and never contains raw source, an output path, a staging path, a timestamp,
or a process identifier.

`artifacts` contains descriptors for requested and available semantic JSON and
PlantUML payloads in format order. Each descriptor records the final relative
path, media type, exact byte size, and SHA-256 including the final LF. The
manifest deliberately has no descriptor or digest for itself.

The run fingerprint is the SHA-256 of the canonical
`code-structure-viz.run-fingerprint/v1` object containing tool and adapter
versions, source and configuration fingerprints, command formats and stdout
selector, and the normalized target/depth request. Output locations, temporary
paths, wall time, and PID are excluded.

The single Python domain entry distinguishes `complete`, `not_applicable`,
`incomplete/partial_safe`, and `incomplete/payload_unavailable`. It repeats the
semantic coverage object, records the `max_entities` budget decision, lists
only published payload paths, and carries domain diagnostics. Root diagnostics
are reserved for valid-run diagnostics outside the domain; fatal runs have no
manifest.

## Diff run

`diff` は同じ `run-manifest/v1` root を使うが、snapshot の `source`/`request` shape を流用せず、
次の field を追加する。

- `request.from`、`request.to`、`request.pr_target`、resolved traversal depth
- `comparison`: caller の requested endpoint、resolved before/after object、endpoint kind、start HEAD anchor、
  selected base candidate、merge-base、resolution method、implicit base candidate observations
- `sources.before`/`sources.after`: immutable side の schema、kind、head、fingerprint、file count
- `semantic_sides.before`/`semantic_sides.after`: semantic side の kind/digest/status
- `file_change_set`: `code-structure-viz.file-change-set/v1` object
- `changed_path_budget`: requested/resolved/actual/source

diff Artifact descriptors は `file-changes.json`（`file-change-set`）、requested format の
`python.diff.semantic.json`、`python.diff.puml` の順に並ぶ。domain `artifact_paths` には semantic
JSON/PlantUML のみを記録し、file-change descriptor は run-level `artifacts` に残す。analysis
failure、entity budget overrun、unmerged path は `incomplete_kind: "payload_unavailable"`、
`payload_available: false` とし、affected semantic payload を列挙しない。ただし diff の安全な
changed-path evidence として `file-changes.json` descriptor は保持する。設定済み比較候補は
`config.resolved.comparison` に `target_ref`/`upstream_ref`（未指定側は `null`）で記録し、
`semantic_sides` の `analysis-failed` は解析していない source fingerprint を digest に使う。
changed-path overrun、
endpoint/object/drift/security failure は manifest を作らない run fatal である。

`DiffManifestBuilder` の run fingerprint preimage は endpoint、sources、semantic side、file-change
metadata、budget、status を含む。output directory、staging path、timestamp、PID、source body、Git
stderr は含まれない。同一入力で key order、Artifact bytes、descriptor SHA-256 が一致する。

### Candidate provenance

`comparison.candidate_observations` はdiff manifestで常に出力する。明示 `from`/`to` のrunは空配列、
implicit baseのrunは、評価順にdeduplicateした各候補を次のclosed objectとして記録する。

```json
{
  "ordinal": 0,
  "origin": "config-upstream",
  "reference": "refs/remotes/upstream/main",
  "resolved_object": "<sha-or-null>",
  "merge_base": "<sha-or-null>",
  "disposition": "selected"
}
```

`origin` は `pr-target`、`config-target`、`config-upstream`、`builtin` のいずれか、
`disposition` は `unresolved`、`no-merge-base`、`selected`、`not-evaluated` のいずれかである。
implicit配列はordinal連番かつselected一件で、`selected_base_candidate`/`merge_base` とselected
observationの値が一致しなければならない。builtin候補の解決失敗は観測して次候補へ進めるが、
explicit/config候補の解決失敗はendpoint fatalでありmanifestを公開しない。

### Working-tree special states

working-treeの内部source inventoryはraw Git path spelling、NFC canonical path、index mode/object、
skip-worktree、gitlink nested stateを保持する。これらの内部証拠はfingerprintとFileChangeSet分類に
のみ使い、nested source bytesやGit stderrをmanifestへ漏らさない。skip-worktreeで欠落したpathは
`sparse-unavailable`/`payload_unavailable`として扱い、実削除 `D` やindex blob再構築へ変換しない。
mode `160000` のgitlinkはnested HEAD・tracked/staged dirty・untracked dirtyを親側の一件の `M` に
集約し、nested stateの読取不能または公開直前の変化はrun fatalとする。異なるraw spellingが同一NFC
canonical pathへ収束する場合は `CSV-DIFF-003` のrun fatalとしてどちらかをwinnerにしない。

gitlink の nested state は initialized、解決済み HEAD、検証済み binding をすべて持つ観測だけを有効とする。
欠落した worktree、未初期化または外部へ逃げる `.git` pointer、unsafe な component、未読 HEAD は clean や
uninitialized の値へ縮退させず、開始時は `CSV-DIFF-003`、公開直前は `CSV-SOURCE-001` として公開を停止する。
nested 観測は固定環境で明示した git directory/work treeへ束縛し、`rev-parse`、`ls-tree`、`ls-files` と raw
worktree bytes の read-only 検証だけを行う。`git diff`、`git status`、external diff、textconv、clean/process
filter、hook、任意 helper は実行しない。nested bytes、stderr、binding identity は manifestへ出力しない。

raw worktree bytesを比較できるのは、内部のclosed-world `GitlinkComparisonProfile`が成立した場合だけである。
profileは`--no-includes`で取得したlocal/worktree config、`check-attr -z --all`の属性結果、`ls-files -v`の
index flagをcanonical digestへまとめる。external include/attributes、autocrlf/eol、filter/diff、変換系属性、
skip-worktree/assume-unchanged、未対応mode、symlink semanticsを含むprofileは安全側へ倒して初期
`CSV-DIFF-003`とする。許可されたprofileでも`core.filemode=false`が無視できるのはregular `100644`/`100755`
差だけであり、type/symlink差はdirtyである。profile digestとtracked raw-content digestは内部fingerprintだけに
使い、公開直前のprofile/state不一致は`CSV-SOURCE-001`としてmanifestを公開しない。

`--exclude-standard` による untracked 集合も、ambient な ignore authority のまま扱わない。
内部 `IgnoreAuthorityProfile` は `git config --no-includes --name-only` で local/worktree の
`core.excludesFile`、`include.*`、`includeIf.*` のキー存在を検査し、値を解決せず、存在時は初期
`CSV-DIFF-003`とする。system/global sourceは固定環境で無効にし、許可するのは検証済み repository
working tree 内の regular `.gitignore`（全階層をboundedに走査）と検証済み Git dir 直下の regular
`info/exclude` だけである。各ファイルの安全な署名と内容digestを `UntrackedObservation` に束ね、
開始・公開直前の authority/path observation を比較する。許可されたignore fileの変更、追加、削除、
symlink/non-regular/上限超過、観測中のprofile変化は `CSV-SOURCE-001`（初期は`CSV-DIFF-003`）として
manifestを公開しない。外部パス、設定値、ignore patternは出力せず、nested gitlinkではこのignore digestを
`GitlinkComparisonProfile`へ含める。public manifest shape/versionは変更しない。

ignore matching の追加 authority である `core.ignoreCase` も閉世界で束縛する。local/worktree
scopeを `--no-includes` で取得し、値がない場合は `false`、値がある場合は重複なく strict boolean として
解釈できる場合だけ許可する。captureした値は untracked 列挙 command に
`-c core.ignoreCase=true|false` として明示し、profile digestへ含める。不正値、重複、scope解決不能は初期
`CSV-DIFF-003` とし、値・設定pathはmanifestへ出力しない。

linked worktreeでは `git rev-parse --path-format=absolute --git-common-dir` の単一UTF-8絶対pathを検証し、
per-worktree Git directory自身またはその `worktrees/` descendant に束縛された non-symlink directoryだけを
有効とする。common directoryのbinding identityと直下 `info/exclude` の bounded digestを
`IgnoreAuthorityProfile`へ含め、per-worktree `info/exclude`をcommon authorityの代用にしない。開始時と公開直前の
common binding、`core.ignoreCase`、common exclude、untracked observationの不一致は
`CSV-SOURCE-001`、初期の解決不能は `CSV-DIFF-003` とし、public manifest shape/versionは変更しない。
