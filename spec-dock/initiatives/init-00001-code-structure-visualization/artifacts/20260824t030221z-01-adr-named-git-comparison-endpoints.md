---
種別: ADR（Architecture Decision Record）
ID: "20260824t030221z-01-adr"
タイトル: "Named Git Comparison Endpoints"
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

# 20260824t030221z-01-adr Named Git Comparison Endpoints

## Context

- 引数の個数や位置で比較の開始点と終了点を推測すると、agent 利用時にも人間利用時にも意図が曖昧になる。
- 省略時には現在の作業内容を自然に比較できる必要があるが、暗黙 base の誤推定や worktree の途中変化を成功扱いしてはならない。

## Decision

- 比較 endpoint は位置引数ではなく `--from` と `--to` で名前付き指定する。
- 指定なしは暗黙 base から frozen working tree、`--from REF` は REF から working tree、`--to REF` は endpoint に対して解決した暗黙 base から REF、両方指定は厳密な REF から REF とする。
- `--to head` は開始時の HEAD、`--to working-tree` は開始時に固定した working tree とする。`--from working-tree` は初期 scope 外とする。
- 暗黙 base は明示 PR target、設定済み comparison target/upstream、`origin/HEAD`、local main/develop/master 候補、merge-base の順で探索し、解決不能なら失敗する。
- 自動 fetch、checkout、reset、stash、clean を行わない。

## Options

- 位置引数一つまたは二つを解釈する案: 短いが意図が不明瞭になるため不採用。
- 常に二 endpoint を必須にする案: 厳密だが日常的な working-tree 比較が冗長になるため不採用。
- 名前付き endpoint と安全な省略規則を併用する案: 明確さと利便性を両立するため採用。

## Consequences

- manifest に requested/resolved endpoint、base 解決方法、fingerprint を記録する。
- initial commit への暗黙 fallback は行わない。
- unmerged path は file evidence として記録できるが、その domain の semantic analysis は失敗とする。

## References

- インタビュー Artifact: `20260824t025616z-interview-codestructureviz-specification-interview.md`
- 参考挙動: `pyclassuml` の現在の比較 UX
- 反映先: CLI、Git source freezer、provenance manifest
