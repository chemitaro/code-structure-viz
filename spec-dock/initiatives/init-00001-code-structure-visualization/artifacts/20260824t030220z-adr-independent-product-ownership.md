---
種別: ADR（Architecture Decision Record）
ID: "20260824t030220z-adr"
タイトル: "Independent Product Ownership"
状態: "accepted"
作成者: "iwasawayuuta"
最終更新: "2026-08-24"
親: ["init-00001"]
authority: "accepted"
accepted_authority: "accepted ADR"
accepted_at: "2026-08-24"
accepted_by: "iwasawayuuta"
mirror_eligible: true
derived_from: ["20260824t025616z-interview-codestructureviz-specification-interview.md"]
reflected_to: []
---

# 20260824t030220z-adr Independent Product Ownership

## Context

- 既存の `pyclassuml` と `tree-git-diff` は、CodeStructureViz の着想と既存挙動を理解するための参照実装である。
- 既存 CLI への依存や互換レイヤーとして新製品を構築すると、古い責務境界と制約を継承する。
- 検証済みのアルゴリズムやテスト観点を全面的に再発明する必要はない。

## Decision

- CodeStructureViz を独立した製品・パッケージ・CLI として新規構成する。
- `pyclassuml` と `tree-git-diff` への実行時依存、パッケージ依存、CLI 呼び出し依存を禁止する。
- 既存コードはライセンスと出典を確認したうえでコピーまたは再構成してよい。取り込んだ後の保守責任とテスト責任は CodeStructureViz が持つ。
- 従来 CLI との後方互換性は保証しない。既存挙動は理解材料とし、最良の契約へ再構築する。

## Options

- 既存 CLI を呼び出す案: 初期実装は速いが、障害・版管理・契約が外部製品へ漏れるため不採用。
- 既存 package に依存する案: 重複は少ないが、古い責務境界を固定するため不採用。
- 必要な知見やコードを選択的に取り込み独立所有する案: 初期移行費用はあるが、再設計と保守性を両立できるため採用。

## Consequences

- 既存ツールの更新は CodeStructureViz へ自動反映されない。取り込み時に出典、差分、テストを記録する。
- CodeStructureViz が必要なユースケースを満たした時点で、既存ツールはその役割を終えられる。
- 一般の外部ライブラリ利用はこの決定の禁止対象ではない。

## References

- インタビュー Artifact: `20260824t025616z-interview-codestructureviz-specification-interview.md`
- 反映先: Initiative / Epic / Issue の Requirement、Design、Plan
