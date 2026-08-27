---
種別: レポート（Issue）
ID: "iss-00005"
タイトル: "Compare Python Structure Changes Safely"
関連GitHub: ["#5"]
最終更新: "2026-08-27"
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

## Strict review response

初回 Final Quality Gate の対象 SHA `d31ce4f5f47b222474fa876242e30ef0b89d2dbe` は fail となり、
P1 の root を Red/Blue の継続セッションで G1（path-state/status authority）、G2（全 changed path の
content/hunk evidence）、G3（U side の coverage/diagnostic coherence）、G4（production acceptance trace）
に整理した。人間判断が必要な境界は、既存契約に沿って H1=canonical Git event records、H2=unavailable
content の fail-closed、H3=before の実測結果を保持する U outcome、H4=`upstream_ref` namespace 展開と
して固定した。

修正は同じ branch の Luna MAX coder lane で TDD の Red→Green として実施し、既知 P1 を検出する production
CLI regression を追加した。commit object 欠損の扱いは正本契約との照合で一度修正し、最終的に run fatal
（exit 1・公開なし）へ戻した。現行候補 commit は
`7daf0372f101dd992335a379e1fee6686a92bf15` で、local HEAD、configured upstream、GitHub branch tip の
三者が一致している。Final Quality Gate はこの SHA に対して再実行するまで未完了である。

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
- Design/Plan/Requirement を実装済み path/symbol、H1/H2/H3/H4 境界、remediation step、test file へ同期し、
  仮想の planned path を除去した。

P2 の改善候補（relation/status のより豊かな PlantUML primitive、blob read batching、無関係 U path の
domain-local attribution、Unicode path policy のさらなる共通化、unborn HEAD の explicit endpoint
composability）は review-response に記録し、今回の acceptance gate では未適用とした。

## Implementation Evidence

- `src/code_structure_viz/application/diff.py`: endpoint から publication までの one-run orchestration、
  changed-path/entity gate、drift/cancellation、domain outcome。
- `src/code_structure_viz/source/endpoints.py`: named endpoint、implicit base、start HEAD provenance。
- `src/code_structure_viz/source/freezer.py` / `source/source_view.py`: commit/frozen working-tree の
  immutable source view、secure read、inventory、fingerprint。
- `src/code_structure_viz/source/git_repository.py`: Git allowlist、fixed environment、bounded child、
  commit tree/blob、untracked/unmerged metadata。
- `src/code_structure_viz/source/file_changes.py`: status、range、ordinal、content-independent hunk ID、
  bounded parser、frozen-content hunk。
- `src/code_structure_viz/semantic/diff.py` / `adapters/python/matcher.py`: presence、canonical empty、
  semantic delta/seed、union impact、high-confidence move matching。
- `src/code_structure_viz/adapters/python/diff_renderer.py` / `artifacts/manifest.py`: semantic JSON、
  member-level PlantUML、diff manifest、Artifact descriptors。
- `schemas/file-change-set-v1.schema.json`、`semantic-v1.schema.json`、`run-manifest-v1.schema.json`、
  `diagnostic-v1.schema.json`、`docs/contracts/**`: closed public contracts。

## Verification

2026-08-27 に commit `7daf0372f101dd992335a379e1fee6686a92bf15` と同じ内容の branch working tree で次を実行した。

- `uv run pytest -q`: **450 passed, 1 skipped**
- U path の Red→Green acceptance: **2 failed, 5 passed** → **7 passed**
- related diff focused suite（endpoint/status/hunk/U/budget/schema/security を含む）: **170 passed, 1 skipped**
- `uv run ruff format --check .`: **成功（107 files already formatted）**
- `uv run ruff check .`: **成功**
- `uv run mypy src tests`: **成功（98 source files）**
- `uv build`: **成功**
- `python3 ./spec-dock/scripts/spec-dock validate`: **成功（nodes=10）**
- `git diff --check`: **成功**

重点 suite は endpoint/presence/budget/stdout、canonical status（R/C/T/D+?）、semantic seed/impact/move、
source/Git safety、hunk redaction・non-Python・LF/CRLF・unavailable、schema の実ファイルへ trace され、
full suite に含まれる。生成した diff の semantic JSON、run manifest、file-change set は同梱 schema で検証し、
working-tree run は publication 前に index/path/untracked/unmerged state と fingerprint drift を再確認する。

## Residual Risks / Follow-ups

- ambiguous move は removed+added として安全に拒否する。rename/name evidence の拡張は後続検討とする。
- diff PlantUML の relation edge と status line-style の語彙拡張、candidate blob read の batching は P2
  follow-up である。
- implicit changed-path default は 1,000、Python entity default は 500。override と実測値は manifest
  に記録する。
- HTML report、可視化共有、SQLAlchemy/Next adapter、legacy CLI compatibility は後続 Issue の責務である。

Issue を完了扱いにするには、上記検証結果に加えて、同一 pushed commit を対象とする ChatGPT Final
Quality Gate の pass（P0/P1=0、unresolved/unreviewed なし）が必要である。
