---
種別: disc
ID: "20260925t075208z-disc"
タイトル: "Issue #8 current-v1 cumulative Strict review at 54bf763"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-09-25"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: []
reflected_to: []
---

# 20260925t075208z-disc Issue #8 current-v1 cumulative Strict review at 54bf763

複数の証拠を統合し、選択肢と trade-off を整理します。一つの source の調査は `research` を使います。

## Inputs

- 統合する evidence:
  - 対象repo/branch/HEAD: `chemitaro/code-structure-viz` / `iss-00008-generate-nextjs-component-snapshots` / `54bf763f230cd89159542204562daa8ca0835754`。
  - ユーザー指定の累積固定点・merge-baseは`f4159066f3954454ad2f0c2701fa54bf1bc7bc4a`。検証済み範囲は`f4159066f3954454ad2f0c2701fa54bf1bc7bc4a..54bf763f230cd89159542204562daa8ca0835754`、21 commits / 25 changed files。
  - fresh ChatGPT Code Review Strict wrapperはexit 0でschema-valid JSONを返した。Oracle session `required-strict-github-connector-verificati-1210` がGitHub connectorでrepo、branch、exact tip SHAを確認した。
  - Strict結果: `review_status=pass`、`overall_correctness=patch is correct`、findings 0、confidence `0.88`。
  - モデル選択の証跡: invocationは`gpt-6-pro` / Proを要求。Oracleは`requestedKey=gpt-6-pro`、`target=Latest`、`resolvedLabel=Latest`、model-picker verified、thinking picker Pro verifiedを記録した。backendの実モデルidentityは独立に証明されていない。
  - exact-HEAD GitHub Actions run `36106680993` は`54bf763...`でcompleted/success、7/7 jobs成功: validate、latest full test、minimum full gate、contract/static-safety、offline package、trusted-profile、macOS filesystem。
  - ローカル`./spec-dock/scripts/spec-dock validate`は`nodes=10`でpass。Plan修正の`git diff --check`もpass。
  - readiness Artifact `20260925t054415z-disc-issue-8-current-v1-readiness-revalidation-at-14d6978.md` は、package-prefix Strict passと`14d6978...`でのfocused/full tests、Ruff、mypy、SpecDock、pinned HTML/PlantUML検証を記録している。`git diff --name-status 14d6978... 54bf763...`ではevidence Artifact追加と`plan.md`のみが変わり、source/test/schema/HTMLは変わっていない。
  - 現在のIssue `report.md`は空のtemplate。Strictはそこから実装結果を推測していない。
  - Plan修正commitは`54bf763f230cd89159542204562daa8ca0835754`、parentは`988ebba4f60d08c4d13330ef362259542ddb6270`。pushでGitHub branchは更新された一方、ローカルremote-tracking ref更新では`Operation not permitted`が出た。読み取り専用`git ls-remote`はlive tip=`54bf763...`を確認し、Strict wrapperもlive tipを2回照合してpassした。metadata repair/fetchは行っていない。
  - current Requirement/Design/Plan、applicability/source acquisition、reference validation、schemas、contract/unit tests、fixtureをレビュー資料として添付・参照した。過去のreviewer responseは添付していない。

## Synthesis

- 一致する事実と未確定事項:
  - 修正済みcurrent-v1 package適用性は、validなdirect declaration 2つのversionを比較して拒否しない。inventoryに存在するroot `package.json`の通常`READ` failureだけが`CSV-NEXT-APPLICABILITY-002` / `applicability`となり、missing package、limit、integrity、path-safety、non-regular/symlink/raced-missing、後続source-read failureは各専用結果を維持する。
  - fresh累積reviewは、その修正およびcatalog/schema/reference/testの整合性にcorrectness findingを認めなかった。reader-owned provenance prefix、source sealと公開値のbinding、mixed-projectのsource/request投影、pre-response target経路、サブエージェントを使わないreview routeも確認した。
  - 独立CIと前回local検証が、static reviewer自身は実行していないcheckをカバーする。コードと検証対象のHTML/PlantUML入力は、local verification済み候補から変更されていない。
  - 候補`54bf763...`について、current I05-PLAN-008 gateのfresh累積Code Review Strict部分は閉じた。ただしreviewerが全readiness条件を認定した意味ではない。CI success、Issueのactive/open/ready、`review_status=pass`、Issue完了は別の証拠である。
  - production adapter resource/version/hashのownerは未決のmaterial design判断。`src/code_structure_viz/adapters/next/runner.py`とpackage `_next_runtime/` resourceは未作成。resolver、Node spawn、production availability、OS process保証、future wheel/sdist受入れは証明されていない。
  - wrapper/OracleはGPT-6 Proを要求し、UI上の`Latest`/Pro選択をverifiedと記録したが、backend model identityは確定しない。サブエージェントreviewは行っていない。

## Options and trade-offs

- 選択肢と利点・制約:
  - **次に必要な判断（推奨だが未承認）:** `20260924t002133z-disc-issue8-strict-dependency-adapter-identity.md`の単一bytes owner案を採用する。locatorは`importlib.resources.files("code_structure_viz").joinpath("_next_runtime", "next-adapter.mjs")`、entrypoint先頭行のstrict stable `MAJOR.MINOR.PATCH`を同じentrypointからparseし、同一の未変更全bytesをhash、初期versionは`0.1.0`、checkout/fixture/caller fallbackなし。追加依存なしでversion/digestを実行対象bytesへ結び付ける。
  - 代替としてsidecar manifestでversionを所有できるが、第二authorityとなりbinding ruleが必要。adapter versionとPython distribution versionの同一化は独立したcomponentの変更を結び付け、current-v1にもない。いずれも具体値の人間判断とcanonical反映が実装前に必要。
  - 判断を保留して`I05-PLAN-002A`へ進まない選択は安全だが、次のproduction resolver unitを止める。他のruntime/process作業も同じidentity ownerに依存する。
  - `14d6978...`のbounded package-only Strict結果と`54bf763...`のfresh cumulative passは別の範囲であり、productionやIssue受入れと混同しない。

## Reflection

- 承認済みreview routeはcurrent-v1 `plan.md`へ反映済み: fresh ChatGPT Code Review Strict、サブエージェント不使用、ユーザー選択の累積固定点、GitHub exact-SHA binding、P0/P1=0および`review_status=pass`。モデルidentityの観測限界も明記している。
- 本Artifactは証拠のみを記録し、Requirement/Designを変更せず、adapter identity候補を承認せず、Issue #8完了も宣言しない。
- identityについてユーザー判断を得た後、正確なlocator/version/hash ownerをDesign/Planに反映し、`src/code_structure_viz/adapters/next/runner.py`と`tests/unit/next/test_runner.py`の`I05-PLAN-002A` brief/TDDへ進む。production各unitとIssue-wide受入れまでゴールを維持する。
