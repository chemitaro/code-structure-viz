---
種別: disc
ID: "20260923t213357z-disc"
タイトル: "Issue 8 mixed-source publication validation analysis"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-09-23"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: []
reflected_to: []
---

# 20260923t213357z-disc Issue 8 mixed-source publication validation analysis

複数の証拠を統合し、選択肢と trade-off を整理します。一つの source の調査は `research` を使います。

## Inputs

- 統合する evidence:
  - Issue #8 の Requirement §24 / Design にある mixed workspace の適用性・公開 projection 契約。
  - ChatGPT-Use Strict / GPT-5.6 Pro (`browser-thinking-time=pro`) の分析セッション:
    - `required-strict-github-connector-verificati-1083`（GitHub exact SHA: `f4159066f3954454ad2f0c2701fa54bf1bc7bc4a`）
    - `required-strict-github-connector-verificati-1084`（同 SHA、`SP-1` の review finding adjudication）
    - `required-strict-github-connector-verificati-1086`（同 SHA、追加の file-count failure 分析）
  - 作業ツリーの垂直 end-to-end contract regression と実行結果。Strict の意見は advisory とし、検証器・型付き decision・seal・既存 contract に照合した。

## Synthesis

- 一致する事実と未確定事項:
  - 「依存パッケージが足りない」ことが根因ではない。現行テスト・参照実装の検証条件が、完全な取得元（SourceView / SourceAcquisitionPlan）と適用可能な公開 projection を同一集合・同一件数として扱っていた。
  - 混在 fixture の証拠は `apps/web` が Next.js 適用対象、`packages/ui` が非適用対象、sealed SourceView の captured file 数が 6、適用対象から生成する request / semantic files が 5。`packages/ui/src/widget.tsx` は公開モデルに流れない。SourceView 件数と semantic file 件数が一致しないのは意図された境界である。
  - 最初の Red は `validate_semantic_snapshot` の `source.file_count == len(files)`。この局所等式を緩めた後に `source_plan_digest` の `full plan projects == public config projects` が次の Red として露呈した。両方が一つの mixed-workspace publication を阻害していた。
  - さらに domain validator の `source.file_count == sum(project.file_ids)` も、取得元全体と公開 semantic project の射影を同一視する独立した不整合である。
  - `source_read` の request-independent path は、公開 `projects=[]` でも実取得済み SourceView の非ゼロ file count を保持する。これは count が公開 model ではなく取得元に属することを示す既存 contract。
  - Strict の adjudication は SP-1 を有効・blocking と判定し、Issue v1 の既存契約では実装 remediation を選択。新しい schema やプロダクト意味論の追加を求めていない。

## Options and trade-offs

- 選択肢と利点・制約:
  - A. Acquisition 時点で非適用 root を落とす: 件数を合わせやすい一方、取得元の完全性・監査証拠・完全計画 digest を失い、既存 applicability 要件と矛盾するため不採用。
  - B. Public project / semantic payload に非適用 root を混ぜる: 件数等式を保てる一方、非対象コードの漏えいと公開 contract 逸脱を起こすため不採用。
  - C. 完全な取得/seal を維持し、適用性 matrix から公開 project 集合を厳密に導出する。SourceView の summary は seal に結び、semantic 側は domain source summary と一致させる。取得元の完全性と公開最小化を両立するため推奨。

## 推奨 remediation 契約

1. `source_plan_digest` は元の完全 descriptor 全体を引き続き hash する。descriptor の resolution root は plan root と一対一・完全被覆であることを検証し、型付き decision の `PackageApplicabilityMatrix.applicable_projects` と `config_resolution[*].membership.kind != "not_applicable"` が一致することを検証する。
2. Request / public config の `projects` は、完全 plan のうち適用可能な root の正確な descriptor projection のみとする。missing / extra / modified root は拒否する。descriptor とその digest は短縮・再生成しない。
3. Domain の `source.file_count` は非負の厳密な整数として検証し、semantic project `file_ids` の合計とは比較しない。型付き context がある場合、source summary 全体を `source_view_descriptor`（schema / kind / head_commit / fingerprint / file_count）に固定する。
4. Semantic snapshot の `source.file_count` も非負の厳密な整数として検証し、`files` 配列長とは比較しない。既存の publication boundary にある semantic `source == domain.source` 完全一致は維持する。各 semantic file / entity / project の ownership・ID・重複・orphan checks は変更しない。
5. Schema を変更しない。request-independent failure、all-applicable / all-nonapplicable、source-read、完全な plan / digest、applicable-only payload の既存挙動を regression で守る。

## ローカル実装と検証状況

- `tests/contracts/next_reference_validation.py` の参照検証器に上記 invariant を実装した。production package、wire schema、digest preimage は変更対象ではない。
- `tests/contracts/test_next_contracts.py::test_mixed_request_publication_preserves_complete_source_and_applicable_semantics` は、2-root plan / 6-source files / 1-root・5-file semantic publication を実際の finalize → publication-chain path に通す。
- 同テストは SourceView 件数改変、semantic source 改変、seal と異なる complete plan、非適用 root の public projection 漏れを拒否することも検証する。
- focused regression: `1 passed`。Next contract module 全体: `544 passed`。全リポジトリ: `1708 passed, 1 skipped`。
- 対象ファイルの Ruff lint / format、リポジトリ全体の Ruff、`mypy src`（59 source files）、`spec-dock validate`（10 nodes）は pass。
- Strict の再呼び出しは新しい証拠が生じた場合だけに限定する。今回の分析は exact pushed base SHA 上で行い、実装評価・最終品質 review は候補 commit SHA に対して別ゲートとして行う。

## Reflection

- この Artifact は分析/evidence であり、Requirement / Design / Plan を自動変更する authority ではない。実装結果の受け入れ後、必要な契約補足だけを canonical docs に反映する。
- Issue #8 は本修正だけで完了とはしない。Plan の残項目、production の実際の OS process backend / verified executable identity、他の acceptance gates、独立 Strict review を満たすまで Issue は active のままにする。
