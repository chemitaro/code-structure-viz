# 連携参照（reference: GitHub）

このドキュメントは、spec-dock が GitHub CLI（`gh`）を使う箇所と、その前提/副作用/注意点をまとめた参照です。

関連:
- 入口: [README.md](README.md)
- 総合: [guide.md](guide.md)
- 命名: [reference_naming.md](reference_naming.md)
- 依存関係: [reference_deps.md](reference_deps.md)

## 1. 前提（どのリポジトリが対象になるか）

spec-dock は `gh` の全コマンドで一律に `--repo owner/repo` を省略するわけではありません。  
`import` / `issue start` / `issue finish` / deps check / sync の `gh issue view` 系では repo slug が分かっている場合に `--repo owner/repo` を付け、same-repo URL import でも current repo を明示して読み取ります。`active set` は GitHub を照会しません。
一方で `gh issue create` / `gh issue list` は repo root を `cwd` にして実行し、対象リポジトリ解決は **`gh` の通常解釈**に委ねます。

補足:
- `./spec-dock/scripts/spec-dock update [path]` は GitHub を更新しない repo-local self-update path です。target 省略時は current directory を更新し、明示 path を渡すとその managed repo を更新します
- runtime update は installer update の wrapper で、固定 upstream `git+https://github.com/chemitaro/spec-dock` を `uvx --no-cache --from git+https://github.com/chemitaro/spec-dock spec-dock update <target>` として実行します。arbitrary package source / cache option / `--force` は公開しません
- update は recognized managed distribution を一つの plan/apply として refresh します。ownership不明、modified target、symlink / hard-link、root差し替えは preserve-and-block で、`init --force` でも無条件の old workspace migration でもありません
- `spec-dock uninstall [path]` / `./spec-dock/scripts/spec-dock uninstall [path]` は repo-local managed artifacts の removal です。GitHub Issue / remote state は変更せず、Python package / global CLI / environment / `uvx` cache の uninstall も行いません
- runtime uninstall は installer uninstall の wrapper で、固定 upstream `git+https://github.com/chemitaro/spec-dock` を `uvx --no-cache --from git+https://github.com/chemitaro/spec-dock spec-dock uninstall <target>` として実行します。repo-local runtime が削除済みの場合の retry / reinstall / refresh は installer CLI の `spec-dock uninstall <target>` / `spec-dock init <target>` / `spec-dock update <target>` を使います
- dependency metadata の canonical storage は `.meta.json` top-level `depends_on` であり、追加/削除/確認は `./spec-dock/scripts/spec-dock deps add/remove/check` の command-first mutation を使います（詳細: `reference_deps.md`）
- legacy `meta.json`（旧名）、partial linkage、current-repo mismatch などの old contract 不整合は、`update` で推測修復せず preserve-and-block します。partial apply は `.distribution-journal.json` の root・intent・authority・contract・plan・protocol・exact pre/postcondition 束縛から同一または compatible newer package で forward recovery し、不一致、downgrade、incompatible package、dual recovery state は追加 mutation 前に拒否します
- `uninstall` は dry-run が既定です。`--apply` は全計画の検証後にだけ mutation を開始し、部分失敗時は legacy `.uninstall-retry.json` を保持します。`--keep-specs` では spec history を削除せず、削除には `--remove-specs` が必要です

代表的な解決材料（`gh` 側）:
- カレントディレクトリが Git リポジトリであること
- `git remote` の URL
- 必要に応じて `GH_REPO` 等の環境変数
- `gh auth`（認証）状態

## 2. 何が GitHub を更新し、何が読み取りだけか

### 更新する（GitHub Issue を作成する / クローズする）

- `new initiative` / `new epic` / `new issue`（デフォルト）は GitHub Issue を作ります（`gh issue create`）
  - `--create-github-issue` は同じ意味の explicit alias です
  - `initiative / epic / issue` では GitHub linkage が mandatory です
  - `--no-github` は node creation option ではありません。既存 Issue に紐づける場合は `--github-issue <n>` を使います
- `close` は linked GitHub Issue をクローズします（`gh issue close`）
  - top-level command として `./spec-dock/scripts/spec-dock close <target>` / `--id <node-id>` / `--github-issue <n>` を受け付けます
  - close 対象は target node 自身の linked GitHub issue のみです
  - `issue` / `epic` / `initiative` のいずれを target にしても child へ cascade close しません
  - remote mutation は close-only です。GitHub side delete は扱いません
  - close command 自体は local tree / docs / generated artifacts を直接更新しません
  - close 後の local `done` 観測は `./spec-dock/scripts/spec-dock sync` の GitHub live state 経路に委ねます
- `issue finish` は active issue lifecycle の通常終了 command です
  - `./spec-dock/scripts/spec-dock issue finish` を受け付けます
  - active issue の linked GitHub issue を close し、already-closed も success として扱います
  - `issue finish` は lifecycle closure 専用です。linked GitHub issue を close または already-closed と確認した後に active state を解除し、post-sync を行います。commit、push、PR、merge、validate、test、review の完了は保証しません。
  - active state は close / already-closed の確認成功後にだけ解除されます。close 失敗時は active を保持し、clear 失敗時は sync を実行しません
- `delete` は local spec node を削除し、linked GitHub Issue があれば close-only で扱います
  - top-level command として `./spec-dock/scripts/spec-dock delete <target> --yes` / `--id <node-id> --yes` / `--github-issue <n> --yes` を受け付けます
  - `issue` target は leaf delete を行い、linked GitHub issue は local delete 前に close します
  - `epic` / `initiative` target は `--recursive --yes` が必須で、subtree 内 linked GitHub issue 群の required remote close barrier が全件通った場合だけ local subtree removal を開始します
  - `--force` は active conflict / dependency boundary conflict override に限定され、GitHub side delete を有効にするものではありません
  - remote mutation は close-only です。GitHub side delete は扱いません
  - remote close failure や subtree metadata validation failure 時は local delete を開始しません
  - local delete 後の derived artifact 追随は `./spec-dock/scripts/spec-dock sync` と `./spec-dock/scripts/spec-dock validate` の責務です

### 読み取りだけ（非交渉）

- `import {initiative,epic,issue}` は **読み取りのみ**です
  - `gh issue view` で存在確認するだけで、GitHub の Issue 本体（title/body/labels 等）を更新しません
  - `--title` は必須です（GitHub title は取り込みません）
  - ローカルにはノードを生成し、`sync --no-update-active` 相当まで実行します（active は変更しません）
  - `import` は実行前に preflight validate（`validate` 相当）を行い、既存ツリーが不整合な場合は **副作用（テンプレートコピー/`.meta.json`生成）なし**で失敗します
  - `meta.json`（レガシー名）が混在しているツリーは非対応です（`.meta.json` へ手動移行後に実行してください）
  - linkage mismatch / current-repo mismatch は手動 normalize 前提で reject され、auto-repair / auto-migrate は行いません

### ローカルのみの実行（no GitHub calls）

- `new {initiative,epic,issue} --github-issue <n>` は「既存番号へリンク」するだけで、GitHub Issue は作りません（`gh` を呼びません）
- `./spec-dock/scripts/spec-dock update [path]` は `gh` を呼びません。固定 upstream の installer update を `uvx --no-cache` で呼び出し、managed files/docs/templates/scripts/skills を更新します
- `spec-dock uninstall [path]` / `./spec-dock/scripts/spec-dock uninstall [path]` は `gh` を呼びません。target repo 内の SpecDock-managed artifacts を dry-run / explicit apply で取り外すだけで、GitHub Issue close/delete、package/environment uninstall、`uvx` cache cleanup は行いません
- 生成される `epics/rules.md` / `issues/rules.md` / `artifacts/rules.md` は `spec-dock/docs/rules/**` への symlink です。`rules.md` は入口/ナビゲーション用で、ルールの正本は `spec-dock/docs/rules/**` にあります。runtime command はサポートされた実行経路です。既存 `discussions/rules.md` は legacy / preservation surface として残り得ますが、新規 working artifact の default destination ではありません

## 3. `import` の URL 入力に関する注意（事故防止）

`import` は `123` / `#123` / canonical GitHub issue URL を受け付けます。

重要:
- canonical URL は `https://github.com/<owner>/<repo>/issues/<n>` の形だけを受け付けます
- `import` は URL 内の `owner/repo` を current repo（`git remote.origin.url`）と照合します
- `owner/repo` mismatch は reject されます
- `initiative / epic / issue` node import は single-repo / GitHub-backed identity contract のため、foreign issue URL を許可しません
- `--allow-foreign-url` は compatibility flag として残っていますが、node identity import の成功経路にはなりません
- canonical でない URL-like target（例: `git@github.com:owner/repo/issues/123`）は reject します
- current repo を検証できない場合（origin 未設定 / GitHub 以外の remote）は、canonical URL import を fail-closed で reject します

## 4. `issue start` / `active set` と checkout（安全装置）

通常の issue execution 開始は `issue start` です。`active set` は Initiative / Epic / Issue を選択する構造操作として残ります。

- `issue start <target>` は Issue node を解決し、別 active Issue の linked GitHub state による unfinished guard、dependency readiness、branch checkout、active 設定、post-sync の順に実行します
- `issue start -f` / `--force` は unfinished active Issue guard だけを bypass します。dependency blocker、invalid target、checkout 失敗、active write 失敗は bypass しません
- 現在の branch は guard の判断材料ではありません。`OPEN` 以外を finished と推測できない active Issue は fail-closed で停止します
- `issue start` の block message では `issue finish`、必要時だけ `issue start <target> -f`、または dependency 解消の次アクションを案内します

`active set` は target を active として固定します。

- positional、`--id <node-id>`、`--github-issue <n>` の target 指定を受け付けます
- target 解決はローカル node を使い、未解決なら active 変更なしで失敗します
- checkout、GitHub state 取得、dependency 判定、unfinished guard、`--force` は持ちません。blocked Issue も調査・計画のために選択できます
- `active show` は現在の選択を表示し、`active clear` は選択を解除します

## 4.5 `close` の target syntax と副作用境界

`close` は `active set` / `deps check` と同じ target syntax を使います。

- `close <target>`: `123` / `#123` / canonical GitHub issue URL / node id を受け付けます
- `close --id <node-id>`: explicit node target
- `close --github-issue <n>`: explicit GitHub issue target
- `close` は target node を解決した上で、その node に linked された `github.issue_number` だけを close します
- local directory / docs / generated artifacts / active pointers は close command で直接変更しません
- local state を GitHub の `CLOSED` へ追随させるのは GitHub default の `sync` の責務です

## 4.6 `delete` の target syntax と safety boundary

`delete` は destructive command であり、`close` より強い safety boundary を持ちます。

- `delete <target> --yes`: node id だけを受け付けます
- `delete --id <node-id> --yes`: explicit node target
- `delete --github-issue <n> --yes`: explicit GitHub issue target
- `delete` は selector 解決後に local guardrail / subtree metadata validation / required remote close barrier を通してから mutation を開始します
- `issue` target の `--recursive` は accepted no-op です
- `epic` / `initiative` target は `--recursive --yes` が必須です。`--recursive` なしでは local subtree removal を行いません
- `--force` は active conflict / dependency boundary conflict override に限定されます
- parent recursive delete では subtree 内 linked GitHub issue 群を close-only で扱い、1 件でも remote close に失敗した場合は local subtree removal を開始しません
- GitHub side delete は扱いません。remote side は常に close-only です
- partial failure 時は structured status / payload で deleted / remaining node ids、dependency scrub failures、retry guidance を返します
- delete 後の docs / generated artifacts / local done 観測は `sync` と `validate` で確認します

## 5. `github.issue_number` のリンクと一意性（重要）

`github.issue_number` は、node（initiative/epic/issue）を GitHub Issue 番号へ紐づけるためのメタデータです。

- `new issue`（デフォルト）: `gh issue create` の結果（Issue番号）でリンクします
- `new issue --create-github-issue`: デフォルトと同じく `gh issue create` の結果（Issue番号）でリンクします
- `new {initiative,epic,issue} --github-issue <n>`: 既存番号へリンクします（新規 Issue は作りません）
- `new initiative --create-github-issue` / `new epic --create-github-issue`: `gh issue create` の結果（Issue番号）でリンクします
- `import <n|#n|url>`: 既存番号へリンクします（読み取り確認のみ）

制約:
- **同じ `github.issue_number` を持つ node は、ツリー全体で 1つ**である必要があります（initiative/epic/issue をまたいで一意）。
  - 重複すると `active set <n|url>` が `Ambiguous github.issue_number=...` で失敗し得ます
  - `validate` / `sync` の preflight validate でも重複は検知され、エラーになります

重複が検出された場合（復旧）:
- エラーメッセージに `type:id (.meta.json path)` の競合一覧が出るので、どれか1つだけが `github.issue_number` を保持するように `.meta.json` を修正してください（他は削除/変更）
- 修正後に `./spec-dock/scripts/spec-dock validate` / `./spec-dock/scripts/spec-dock sync` を再実行してください

## 6. よくある失敗

- `gh` が未導入/未認証で `new issue`（デフォルト）が失敗する
  - `initiative / epic / issue` では GitHub linkage が mandatory なので、`gh auth login` 等を先に行ってください
- Epic 配下で local-only issue を作りたい
  - 現行 contract では `initiative / epic / issue` の local-only create はサポートされません
  - current repo の GitHub Issue を作るか、既存 current-repo issue に `--github-issue <n>` でリンクしてください
- canonical URL import が失敗する → current repo（`origin`）を検証できないか、`owner/repo` mismatch の可能性があります
  - foreign GitHub issue URL は node identity import として reject されます
  - `--allow-foreign-url` を付けても cross-repo node import の compatibility success path にはなりません
  - canonical でない URL-like target は受け付けません
