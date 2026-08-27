---
種別: レポート（Issue）
ID: "iss-00005"
タイトル: "Compare Python Structure Changes Safely"
関連GitHub: ["#5"]
最終更新: "2026-08-28"
依存: ["requirement.md", "design.md", "plan.md"]
親: ["epic-00002", "init-00001"]
---

# Result Summary

詳細: [Report Guide](../../../../../../docs/authoring/report.md)

## Outcome

Issue 5 の Python 構造差分 vertical slice を実装した。`diff` CLI は named endpoint、implicit
base、開始時 HEAD anchor、working-tree freeze、Git read-only source acquisition、metadata-only
`FileChangeSet`、Python entity/member/relation diff、before/after union impact、safe move matching、
domain presence、changed-path/entity budget、versioned semantic JSON、member-level PlantUML、run
manifest、closed stdout selector を扱う。

既存 snapshot pipeline は維持し、diff は CodeStructureViz 所有の endpoint/source/diff/application/
renderer modules として独立させた。`pyclassuml`、`tree-git-diff`、SQLAlchemy、Next.js、HTML/Tailscale、
target repository の Git mutation、auto fetch/checkout は導入していない。

gitlink の tracked worktree 判定は、raw bytesを無条件にGit statusの代替とせず、nested config、attributes、
index flagsを閉世界で検証する内部 `GitlinkComparisonProfile` を通過した場合だけ行う。変換・filter・外部
attributes・特殊index flagなどの意味を証明できない状態は初期観測をfatalとし、`core.filemode=false`の
regular `100644`/`100755`差だけを例外的に無視する。profile/state digestは公開契約へ追加せず、source drift
検知の内部証拠として扱う。

## Strict review response

初回 Final Quality Gate の対象 SHA `d31ce4f5f47b222474fa876242e30ef0b89d2dbe` は fail となり、
P1 の root を Red/Blue の継続セッションで G1（path-state/status authority）、G2（全 changed path の
content/hunk evidence）、G3（U side の coverage/diagnostic coherence）、G4（production acceptance trace）
に整理した。人間判断が必要な境界は、既存契約に沿って H1=canonical Git event records、H2=unavailable
content の fail-closed、H3=before の実測結果を保持する U outcome、H4=`upstream_ref` namespace 展開と
して固定した。

修正は同じ branch の Luna MAX coder lane で TDD の Red→Green として実施し、既知 P1 を検出する production
CLI regression を追加した。commit object 欠損の扱いは正本契約との照合で一度修正し、最終的に run fatal
（exit 1・公開なし）へ戻した。続くStrict Blue継続セッションでは、追加P1をA（raw Git identity/index/
sparse/gitlink）、B（候補根拠とSHA証跡）、C（production acceptance coverage）へ再分類し、H5〜H8として
対応を具体化した。Luna MAX coder laneでH5〜H7（skip-worktree、gitlink、raw/NFC collision、candidate
observations）をproduction経路と受入れテストへ反映した。

同じ Final Quality Gate の継続レビュー（reviewed SHA `e09dea08322c7ce41ecc4275c23286ea2af9ca0a`）では、
P1として (1) uninitialized/missing gitlinkをcleanへ縮退する経路、(2) cross-side raw spelling transitionの
canonical mapへの吸収、(3) nested gitlink観測でtextconv/clean/process helperへ到達し得る経路、(4) それらの
production acceptance trace不足が確定した。Blue側の分析で、(1)〜(3)は実装 remediation、(4)は依存する
test remediationとし、要件・公開schema変更や人間判断は不要とした。実装可能なTDD handoffをLuna MAX coder
へ渡し、今回の修正で4件すべてを閉じる方針とした。

その後の継続 Final Quality Gate（reviewed SHA `f61b72646ac61ead0cddee6901cc545466dce38a`）では、P1-037
（raw worktree blob/mode equalityをGit clean/dirty semanticsとして扱うこと）とP1-039（既にdirtyなfixtureを
使ったためobserver誤判定を検出できないacceptance）が追加で確定した。Red/Blueの継続分析では両者を同じ
根本原因（Git変換・属性・index flagを観測せずraw比較を許可する設計）から派生する実装remediationと、
それに依存するtest remediationへ分けた。`GitlinkComparisonProfile`、profile/state fingerprint、clean
baseline fixture、autocrlf/eol/filter/index flag/core.filemodeのproduction回帰を実装し、今回の候補では
この2件を閉じる検証へ進めている。まだFinal Quality Gateの合格を意味するものではなく、push後の同一SHA
に対する継続レビュー結果だけを最終判定とする。

このReportに記載する `7daf0372f101dd992335a379e1fee6686a92bf15` および
`202e8a8bf9cf1f9c3073f0864e7d0b340a688a46` は履歴receiptであり、現行SHAではない。後続commitを含む
local/upstream/GitHub SHAの一致とFinal Quality Gateの判定は、Reportとは独立した同一SHAの外部検証receiptで
のみ確定する。

## Remediation evidence

前回の Final Quality Gate review（campaign `iss-00005-implementation-final-quality-r1`）で検出された
P1 は次のように修正した。

- working-tree の start state を HEAD、path、untracked、unmerged、inventory として先に捕捉し、
  frozen bytes、FileChangeSet、budget、final drift check を同一 run authority に統合した。
- inventory に tracking state、Git mode/type、object identity、availability、unmerged state を加え、
  budget 前に canonical `U`、tracked→untracked `D+?`、unique `R`/`C`、`A`/`D`、`T`、mode-only `M` を
  同一 path-state authority から分類するようにした。source path の再利用と rename の二重 count を防ぎ、
  `FileChangeSet.count` と manifest actual を一致させた。
- all changed path を対象に `absent`/`available`/`unavailable` の content evidence を作り、budget admission
  後にだけ hunk を投影するようにした。unknown/binary/上限超過 bytes を empty side にせず、non-Python の
  unavailable path は偽の hunk を出さず、LF/CRLF と最終改行差を deterministic range に保持する。affected
  Python path は safe metadata と `payload_unavailable` のみを公開する。
- inventory の `unavailable`/`other` を存在 path として扱い、unreadable untracked `.py` も `?` として
  changed-path budget へ含めた。candidate の non-regular/non-blob は `CSV-PY-001` の failed source
  とし、absent/canonical-empty への誤変換をなくした。
- untracked/unmerged を FileChangeSet と changed-path budget へ取り込み、unmerged は affected
  domain を `payload_unavailable` として推測しない。
- Git 固定環境へ `GIT_NO_LAZY_FETCH=1`、`GIT_NO_REPLACE_OBJECTS=1` を追加し、working-tree の
  production path から raw Git patch/clean filter 経路を外した。
- cross-side inventoryをcanonical mapとchanged-path budgetの前にraw identityとして検証し、同じNFC pathへ
  異なるraw spellingが現れた場合は `CSV-DIFF-003`・exit 1・公開なしとした。commit treeのraw spellingを
  `SourceInventoryEntry`まで保持し、同じraw spellingの再観測だけを許可した。
- gitlink observerをcomplete-onlyへ変更し、nested `.git` binding（directoryまたはbounded gitdir pointer）を
  検証済みrootへ限定した。`rev-parse`、`ls-tree`、`ls-files` とdescriptor-based raw file hashだけで
  nested stateを観測し、`git diff`/`status`、external diff、textconv、clean/process filter、任意helperを
  実行しない。初期の未読取は `CSV-DIFF-003`、公開直前の未読取は `CSV-SOURCE-001` として公開を停止する。
- raw worktree比較の前に、nested local/worktree config、`.gitattributes`の`check-attr -z --all`結果、
  index identity flagを閉世界profileへ束ねた。include/外部attributes、autocrlf/eol、filter/diff、変換系
  attributes、skip-worktree/assume-unchanged、未対応mode、symlink semanticsを含むprofileは比較を許可せず、
  初期`CSV-DIFF-003`で停止する。許可profileでは`core.filemode=false`のregular exec-bit差だけを無視し、
  profile digestとtracked raw-content digestを内部stateへ含めた。
- gitlink acceptanceは親OIDとnested HEAD/tree/indexが一致するclean baselineを別fixtureで作り、親側が既に
  dirtyなためにobserver誤判定を隠さないようにした。tracked/untracked dirty、autocrlf true/input、
  `.gitattributes` eol、skip-worktree/assume-unchanged、core.filemode=false、profile driftをproduction CLIで
  回帰し、unsafe profileは`CSV-DIFF-003`・exit 1・公開なし、clean baselineは変更なしを確認した。
- 先行4 P1を実際の `diff` CLIで回帰する acceptance（cross-side transition、missing/uninitialized/external
  pointer、final unreadable、helper sentinel）と identity/complete-only unitを追加し、no-publication境界と
  親側gitlink一件 `M` を検証した。
- unified hunk helper は payload/line bounded、file-header/hunk state 分離、quoted UTF-8 path
  decoder、matching path 必須とした。production diff は frozen content ranges を使う。
- class/decorator/entity delta を semantic seed へ含め、before/after relation union impact へ渡した。
- move は同名または qualified-name evidence、exact structural fingerprint、unique candidate の
  conjunction とし、無関係な構造同一 class を moved にしない。
- commit blob/object read failure は domain incomplete に降格せず run fatal として扱う。
- Git subprocess、source read、analysis、publication に cancellation checkpoint を通し、子 process
  group を終了して exit 130 と staging cleanup を行う。
- `file-change-set-v1` を追加し、semantic/manifest/diagnostic schemas と contract docs を diff shape
  へ更新した。requested endpoint、resolved endpoint、source、semantic side provenance を別 field
  authority として記録し、canonical empty bytes は sorted canonical JSON にした。payload unavailable
  diff でも safe `file-changes.json` descriptor を保持し、configured comparison と diff diagnostic
  codes を manifest schema へ追加した。U path は before を一度だけ解析し、その同一結果から semantic
  side・実測 coverage・parse diagnostics を構成する。未解析 after だけを source fingerprint 付き
  `analysis-failed` として記録し、synthetic coverage が before の実測結果を上書きしない。
- Design/Plan/Requirement を実装済み path/symbol、H1〜H8 境界、remediation step、test file へ同期し、
  仮想の planned path を除去した。`run-manifest/v1` の candidate observations、path identity、sparse、
  gitlink stateの契約も正本へ同期した。

P2 の改善候補（relation/status のより豊かな PlantUML primitive、blob read batching、無関係 U path の
domain-local attribution、Unicode path policy のさらなる共通化、unborn HEAD の explicit endpoint
composability）は review-response に記録し、今回の acceptance gate では未適用とした。

## Implementation Evidence

- `src/code_structure_viz/application/diff.py`: endpoint から publication までの one-run orchestration、
  changed-path/entity gate、drift/cancellation、domain outcome。
- `src/code_structure_viz/source/endpoints.py`: named endpoint、implicit base、start HEAD provenance、candidate observations。
- `src/code_structure_viz/source/freezer.py` / `source/source_view.py`: commit/frozen working-tree の
  immutable source view、secure read、inventory、fingerprint。
- `src/code_structure_viz/source/git_repository.py`: Git allowlist、fixed environment、bounded child、
  commit tree/blob、raw path identity、index skip-worktree、untracked/unmerged、gitlink metadata。
- `src/code_structure_viz/source/file_changes.py`: status、range、ordinal、content-independent hunk ID、
  bounded parser、frozen-content hunk。
- `src/code_structure_viz/semantic/diff.py` / `adapters/python/matcher.py`: presence、canonical empty、
  semantic delta/seed、union impact、high-confidence move matching。
- `src/code_structure_viz/adapters/python/diff_renderer.py` / `artifacts/manifest.py`: semantic JSON、
  member-level PlantUML、diff manifest、Artifact descriptors。
- `schemas/file-change-set-v1.schema.json`、`semantic-v1.schema.json`、`run-manifest-v1.schema.json`、
  `diagnostic-v1.schema.json`、`docs/contracts/**`: closed public contracts。

## Verification receipts

この節のSHAと結果は履歴receiptであり、後続commitを含む現行branchの証明ではない。特に
`7daf0372f101dd992335a379e1fee6686a92bf15` と
`202e8a8bf9cf1f9c3073f0864e7d0b340a688a46` は、後続のH5〜H7変更およびReport同期より前の観測点である。
これらをlocal HEAD、configured upstream、GitHub branch tipの「現行三者一致」として再利用してはならない。

今回のP1修正を含む作業木での独立再検証receiptは次のとおりである。

- Gitlink source unit: **97 passed**
- Python diff acceptance: **56 passed**
- read-only security: **1 passed**
- full suite: **546 passed, 1 skipped**
- `uv run ruff format --check .`: **成功**
- `uv run ruff check .`: **成功**
- `uv run mypy src tests`: **成功**
- `uv build`: **成功**
- `python3 ./spec-dock/scripts/spec-dock validate`: **成功**
- `git diff --check`: **成功**

このreceiptはprofile remediationを含むcandidate treeに対する主担当側の独立検証であり、レビューへ提出するcommitの厳密な
local/upstream/GitHub SHA一致はpush後に改めて取得する。Final Quality Gateの判定も、同じreviewer conversation
でそのpush済みSHAを対象に再実行した結果だけを採用する。

最終的な現行SHA、local/upstream/GitHub一致、clean checkout、Final Quality Gateの
`review_status: pass` は、Reportの履歴値ではなく、公開直前に取得した同一SHAの外部検証receiptで判定する。
重点suiteはendpoint/presence/budget/stdout、canonical status（R/C/T/D+?）、sparse/gitlink/raw path
identity/candidate provenance、semantic seed/impact/move、source/Git safety、hunk redaction・non-Python・
LF/CRLF・unavailable、schemaへtraceされる。

## Residual Risks / Follow-ups

- ambiguous move は removed+added として安全に拒否する。rename/name evidence の拡張は後続検討とする。
- diff PlantUML の relation edge と status line-style の語彙拡張、candidate blob read の batching は P2
  follow-up である。
- implicit changed-path default は 1,000、Python entity default は 500。override と実測値は manifest
  に記録する。
- HTML report、可視化共有、SQLAlchemy/Next adapter、legacy CLI compatibility は後続 Issue の責務である。

Issue を完了扱いにするには、上記検証結果に加えて、同一 pushed commit を対象とする ChatGPT Final
Quality Gate の pass（P0/P1=0、unresolved/unreviewed なし）が必要である。
