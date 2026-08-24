---
種別: ADR（Architecture Decision Record）
ID: "20260824t030221z-adr"
タイトル: "Dual Snapshot Semantic Diff"
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

# 20260824t030221z-adr Dual Snapshot Semantic Diff

## Context

- Git の行差分だけでは、クラス、テーブル、コンポーネント、メンバー、関係の意味的変更を正確に表現できない。
- 削除された要素の依存関係は変更後の source だけでは復元できない。
- file 変更の証拠と、利用者へ提示する semantic change を分離する必要がある。

## Decision

- diff の正本を、比較前と比較後の二つの不変な semantic snapshot とする。
- Git hunks と rename/copy 判定は候補抽出・出典・補助証拠に限定し、意味的変更の正本にしない。
- `FileChangeSet` と `SemanticChangeSet` を分離する。
- 変更 seed の影響探索は before/after graph の和集合上で行い、削除要素は before 側の辺を使う。
- 空白、comment、import 順だけの変更は semantic seed にしない。

## Options

- Git hunks を直接描画する案: 実装は単純だが semantic 精度が不足するため不採用。
- 変更後だけを解析する案: 実装量は減るが削除・関係消失を説明できないため不採用。
- before/after を独立解析して照合する案: 解析費用は増えるが、削除・移動・関係差分を一貫して扱えるため採用。

## Consequences

- 比較開始時に両 endpoint を固定し、途中変化を検出した場合は成功 Artifact を生成しない。
- adapter ごとの安定 identity と matching confidence が必要になる。
- 大規模 repository 向けに明示的な budget と fail-closed 動作を設ける。

## References

- インタビュー Artifact: `20260824t025616z-interview-codestructureviz-specification-interview.md`
- 反映先: semantic model、diff pipeline、impact traversal、manifest
