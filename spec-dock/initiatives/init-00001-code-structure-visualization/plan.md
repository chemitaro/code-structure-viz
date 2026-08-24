---
種別: 計画書（Initiative）
ID: "init-00001"
タイトル: "Visualize Code Structure Changes"
関連GitHub: ["#1"]
状態: "draft"
最終更新: "2026-08-24"
依存: ["requirement.md", "design.md"]
---

# init-00001 Visualize Code Structure Changes — 計画

詳細: [Scope Layering Guide](../../docs/authoring/scope-layering.md)

## 目標

exactly one Epic `epic-00002` を通じて CodeStructureViz の product spine と三 domain を段階的に成立させる。Initiative Plan は individual implementation task を再掲せず、投資順、milestone、全体 verification、見直し条件を管理する。

## 順序・依存

1. `epic-00002` が cross-Issue contract、seven vertical slice、dependency DAG を確定する。
2. Python snapshot/diff を先行し、安全な core/source/Artifact spine を利用可能にする。
3. SQLAlchemy snapshot/diff を追加し、Python+SQLAlchemy intermediate release gate を通す。
4. Next snapshot/diff を optional first-party Node adapter として追加する。
5. all-domain orchestration、domain presence truth table、two-level budget、per-domain-only semantic output、partial success、aggregate `run-manifest/v1`、platform/package gate を完成し Initiative を close する。

Initiative 配下の Epic は本 scope では `epic-00002` 一つだけ。product HTML report は将来の別 Epic 候補であり、本 Initiative に追加しない。

## 実装step

| Initiative milestone | Owning Epic/Issue boundary | Exit evidence |
| --- | --- | --- |
| M1 Product spine + Python preview | epic-00002: ISSUE-01→ISSUE-02 | Python snapshot/diff、domain presence、start-HEAD anchor、metadata-only FileChangeSet、two-level budget、semantic Artifact acceptance |
| M2 Intermediate release | epic-00002: ISSUE-03→ISSUE-04 | Python+SQLAlchemy full acceptance、ER row diff、offline package gate |
| M3 Next preview | epic-00002: ISSUE-05→ISSUE-06 | first-party adapter、Next snapshot/diff、optional Node gate |
| M4 Initiative completion | epic-00002: ISSUE-07 | per-domain semantic output、aggregate `run-manifest/v1`、cross-domain presence/budget matrix、partial success、exit、minimum/latest CI |

M2 と ISSUE-05 work は ISSUE-01 完了後に一部並行できるが、M2 release と M3 Next diff はそれぞれ declared dependency gate を越えるまで統合しない。

## 検証

- Epic acceptance が `INIT-REQ-001`〜`INIT-REQ-008` と `INIT-AC-001`〜`INIT-AC-008` を trace する。
- exact one Epic invariant、seven Issue DAG acyclicity、verticality、intermediate/final release boundary を machine-checkable evidence で検査する。
- M1 で Python diff の five-row domain presence truth table、canonical empty-side digest、`--to working-tree` start-HEAD anchor、metadata-only hunk negative test、changed-path/entity budget matrixを固定する。
- M2 と M3 で SQLAlchemy/Next が shared endpoint/FileChangeSet contract を再利用し、片側不在を全 removed/added、解析 failure を incomplete とする同一 table-driven acceptance を通す。
- M4 で三 domain の both-absent/before-only/after-only/failure を組み合わせ、per-domain semantic JSON/PlantUMLだけが生成され、aggregate は `code-structure-viz.run-manifest/v1` だけであることを検証する。
- release ごとに static safety、Git immutability、source/secret/absolute-path/raw-hunk redaction、determinism、run-level changed-path gate、domain-local entity gate、partial failure、platform/package matrix を再実行する。
- product R/D/P と CLI help/schema から HTML runtime output が除外されていることを scope scan する。

## rollback

- M1/M2/M3/M4 は release tag/Issue group 単位で rollback 可能にする。later adapter を戻しても earlier domain の schema/CLI を壊さない。
- false success、安全性違反、secret leak は release stop 条件。affected adapter/default orchestration を無効化し、incomplete へ狭めて forward recovery する。
- target repository/data migration は N/A。CodeStructureViz は read-only analyzer である。

## exit / handoff

- Epic へは Initiative requirement、accepted ADR、milestone、scope exclusion を渡す。
- M2 で intermediate release を記録するが Initiative を close しない。
- M4 で Next/all-domain acceptance、one Epic completion、trace matrix、open question なし、package/CI gate を確認して Initiative completion とする。
- implementation result と residual risk は canonical Initiative Report に記録し、本 Plan は execution log にしない。
