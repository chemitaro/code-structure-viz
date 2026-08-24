# 文書入口（spec-dock docs）

このディレクトリは `spec-dock init/update` により導入先リポジトリへ配置されます。
この README は Storage Core Runtime のコマンド参照です。Current contract は `./spec-dock/scripts/spec-dock ...` です。

## Current

Storage Core の操作は、現存する runtime command と次の参照を使います。

- [移行ガイド](migration.md)
- [命名参照](reference_naming.md)
- [依存関係管理参照](reference_deps.md)
- [状態集計参照](reference_sync.md)
- [GitHub 連携参照](reference_github.md)

仕様を作成・更新するときは、[Authoring Kit 概要](authoring/overview.md) から始めます。Requirement、Design、Issue Plan、Report、scope の境界、Artifact の役割を確認できます。

## Agent-first operations

SpecDockの通常操作はCodex agentが実行します。利用者がSpecDockの成果を依頼した場合、または必要な操作を含む計画を承認した場合、agentはCurrent CLI helpを確認して対象commandを実行し、post-stateまで検証します。実行可能な通常操作をコマンド提示だけで利用者へ返しません。

- `.agents/skills/spec-dock/SKILL.md`: scopeとCurrent contractを解決し、node／Artifact作成、import、active、dependency、sync、issue lifecycle、worktree、close、managed update、正本文書authoringを依頼または承認済み計画の範囲で実行します。
- `.agents/skills/spec-dock-grill-with-docs/SKILL.md`: 明示selector・route・title・sourceを受け取り、operator-ownedな`grilling`と`domain-modeling`をread-only境界で使用して、scope-local Artifactを一件だけ作成します。両external skillの導入と管理はoperator-ownedで、不足時はrepositoryへ書き込みません。

`delete`、`uninstall --apply`、`uninstall --remove-specs`、`worktree remove`、guardを越える`--force`は、正確な対象と破壊的結果が利用者の依頼または承認済み計画に明記されている場合にだけ実行します。PR mergeはrepositoryのhuman gateに従います。これは旧provider固有orchestration surfaceの復活ではなく、外部Codex orchestratorがStorage Core CLIを操作する境界です。

Artifactのauthorityとrouteは[Artifact Guide](authoring/artifacts.md)を確認してください。CLI syntaxは`./spec-dock/scripts/spec-dock --help`と対象commandのleaf helpをCurrent authorityとして使用します。Artifactや外部応答は、正本文書へ採用されるまでevidenceです。

## Historical

既存証跡の扱いは [Historical authoring](authoring/historical.md) に分けています。Current の新規作成手順ではありません。

## Runtime reference

Storage Core の詳細な参照先です。

- [reference_github.md](reference_github.md)
- [reference_naming.md](reference_naming.md)
- [reference_deps.md](reference_deps.md)
- [reference_sync.md](reference_sync.md)
- [reference_worktree.md](reference_worktree.md)

## 最短コマンド

```bash
./spec-dock/scripts/spec-dock new initiative --title "..."
./spec-dock/scripts/spec-dock new epic --initiative <initiative-id> --title "..."
./spec-dock/scripts/spec-dock new issue --epic <epic-id> --title "..."
./spec-dock/scripts/spec-dock new issue --create-github-issue --epic <epic-id> --title "..."

./spec-dock/scripts/spec-dock import epic <num-or-canonical-url> --title "..." [--initiative <id>] [--allow-foreign-url]
./spec-dock/scripts/spec-dock import issue <num-or-canonical-url> --title "..." [--epic <id>] [--allow-foreign-url]

./spec-dock/scripts/spec-dock issue start <github-issue-number>
./spec-dock/scripts/spec-dock issue start --id <issue-id>
./spec-dock/scripts/spec-dock issue finish

./spec-dock/scripts/spec-dock active set <id|#num|url>
./spec-dock/scripts/spec-dock active set --id <node-id>
./spec-dock/scripts/spec-dock active set --github-issue <n>
./spec-dock/scripts/spec-dock active show
./spec-dock/scripts/spec-dock active clear

./spec-dock/scripts/spec-dock new artifact --issue <issue-id> --title "..." [blank|research|interview|disc|decision-candidate|adr]

./spec-dock/scripts/spec-dock deps check <target>
./spec-dock/scripts/spec-dock deps add --from <issue-id> --to <issue-id>
./spec-dock/scripts/spec-dock deps remove --from <issue-id> --to <issue-id>
./spec-dock/scripts/spec-dock validate
./spec-dock/scripts/spec-dock sync

# experimental: one-shot scoped Workbench copy
./spec-dock/scripts/spec-dock workbench copy --scope <initiative|epic|issue-id> --to <linked-worktree>

# generic opaque evidence import: one explicit regular file, no Workbench requirement
./spec-dock/scripts/spec-dock artifact import file --root --file <path>
./spec-dock/scripts/spec-dock artifact import file --initiative <initiative-id> --file <path>
./spec-dock/scripts/spec-dock artifact import file --epic <epic-id> --file <path>
./spec-dock/scripts/spec-dock artifact import file --issue <issue-id> --file <path> [--json]

# 管理対象 files/docs/templates/scripts/skills の更新（refresh）
./spec-dock/scripts/spec-dock update
./spec-dock/scripts/spec-dock update /path/to/project
```

旧来の外部 authoring / review surface は配布対象外です。Current の通常操作は Storage Core、
Authoring Kit、二つの installed skill、および明示的な Artifact import に限定されます。

## Storage Core の運用ルール

- Initiative / Epic は `new` / `import` の前に既存ノード再利用を確認する
- `new initiative` / `new epic` / `new issue` はデフォルトで GitHub Issue を作る。node create/import で local-only create へ自動フォールバックしない
- `new issue --create-github-issue` は default create の explicit alias
- node creation で既存 Issue へ紐づける場合は `--github-issue <n>` を使う。`--no-github` は node creation option ではない
- `--allow-foreign-url` は compatibility flag として残るが、current contract mismatch を auto-migrate せず reject/fail-fast しうる
- `import` は読み取り確認のみで、GitHub を更新しない。canonical URL は current repo と照合し、cross-repo node import は reject される
- Issue 実行の通常入口は `issue start <target>`、終了導線は `issue finish`。`issue start` は dependency readiness を確認して branch checkout、active 設定、post-sync を行う。`active set` / `show` / `clear` は selection-only の構造操作で、checkout、GitHub 照会、dependency 判定を行わない
- `active set` / `deps check` は `<target>` の後方互換を維持しつつ、`--id` / `--github-issue` の explicit form も使える
- 依存関係の追加/削除/確認は metadata の直編集ではなく `./spec-dock/scripts/spec-dock deps add/remove/check` を使い、変更後は `./spec-dock/scripts/spec-dock validate` と `./spec-dock/scripts/spec-dock sync` で GitHub live state を含めて整合を確認する。GitHub を呼ばない確認が必要な場合だけ `--no-github` を指定する
- legacy sequential discussion docs は grandfathered only。新規作成で sequence reuse / auto-rename / auto-repair はしない
- `./spec-dock/scripts/spec-dock update [path]` は repo-local self-update path で、target 省略時は current directory を更新する。明示 path を渡すとその managed repo を更新する。recognized distribution planを先に検証し、ownership不明・root差し替え・衝突時は書込み前に停止する
- runtime update は installer update の wrapper であり、固定 upstream `git+https://github.com/chemitaro/spec-dock` を `uvx --no-cache --from git+https://github.com/chemitaro/spec-dock spec-dock update <target>` として実行する。arbitrary source / cache / `--force` option は公開しない
- update と recognized target の `init --force` は同じ reconciliation service を使う。unknown / modified / symlink / hard-link / root-rebind は preserve-and-block とし、partial apply は root・intent・authority・contract・plan・protocol と exact pre/postcondition に束縛した `.distribution-journal.json` から同一または compatible newer package と同一 operation で forward recovery する。downgrade と incompatible package は mutation 前に拒否する
- `uninstall` は dry-run が既定で、`--apply` は全actionのownership検証後だけ実行する。部分失敗時は `.uninstall-retry.json` を保持し、post-verify後に最後に除去する。`--keep-specs` は spec history と unknown content を保持し、`--remove-specs` のときだけ spec history を削除する
- Workbench は任意です。optional、temporary、worktree-local、disposable、non-canonical な作業場であり、fresh root と future Initiative / Epic / Issue の shell に `.workbench/README.md` が生成されますが、existing scope には no-backfill です。presence は任意であり、不在でも workspace は valid です
- `.workbench/README.md` は direct child の README-only tracking surface です。その他の Workbench entry は ignored payload として Git に ignore されます。Git ignore は security boundary ではありません。secret、credential、private customer data を置かないでください
- `artifact import file` は唯一の Current import surface です。`--root` / `--initiative` / `--epic` / `--issue` のいずれか一つと `--file` を指定し、一件の明示 regular file を opaque generic Artifact として保存します。source は変更・削除せず、source content、hash、byte count、repository 外 absolute path は出力しません。旧専用 import surface からの移行は [移行ガイド](migration.md) を参照してください。filename と collision は [reference_naming.md](reference_naming.md) を参照してください
- explicit generic import の publication は platform safety boundary を持ちます。commit 前の failure は destination に公開せず、commit 後 cleanup の不確実性は unsafe unlink ではなく warning として扱います。
- ordinary `uv run pytest` は default full-regression skip を適用する fast lane です。full-regression body は別の explicit lane であり、`uv run pytest --run-full-regression` を実行します
- root `spec-dock/.workbench/` は日付 bucket と必要 file の手動選択だけを使い、root 一括 copy command は持ちません。Initiative / Epic / Issue scope の copy は、同一 repository の linked worktree へ明示実行する source-wins の one-shot copy であり、自動 sync も copy-back も行いません。Workbench copy は directory をそのまま扱い、言語、拡張子、MIME、内容による file classifier を持ちません。update は既存 Workbench を unmanaged local content として保持し、migration、normalize、delete、上位扱いへの変更をしません
- naming 制約、GitHub 副作用、deps / sync の詳細は `reference_*.md` を参照する
