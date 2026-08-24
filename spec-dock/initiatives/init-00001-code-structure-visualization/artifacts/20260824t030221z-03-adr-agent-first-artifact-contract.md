---
種別: ADR（Architecture Decision Record）
ID: "20260824t030221z-03-adr"
タイトル: "Agent First Artifact Contract"
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

# 20260824t030221z-03-adr Agent First Artifact Contract

## Context

- 主利用者は Codex などの coding agent であり、自身の理解と人間向け説明の両方に利用する。
- machine-readable な構造と、人間が読みやすい図のどちらか一方では用途を満たさない。
- 部分失敗や解析対象外を成功または空結果へ潰さない契約が必要である。

## Decision

- versioned semantic JSON と domain-specific PlantUML を一次出力とし、format 指定で選択可能、未指定時は両方を生成する。
- `--output-dir` を必須とし、対象 repository へ暗黙に書き込まない。既存 file を上書きしない。
- manifest に endpoint、base 解決、fingerprint、tool/contract/adapter version、domain coverage、diagnostic、Artifact 相対 path と SHA-256 を記録する。
- domain ごとの `complete`、`not_applicable`、`incomplete` を保持する。部分成功 Artifact を残しつつ、全体が不完全なら exit 3 とする。
- exit code は 0 complete、1 fatal analysis/environment、2 usage/config、3 incomplete、130 interrupt とする。

## Options

- JSON のみ: agent には適するが人間への説明力が不足するため不採用。
- PlantUML のみ: 人間には適するが agent が厳密に再利用しにくいため不採用。
- 両形式と provenance manifest: 出力量は増えるが二つの主要用途を満たすため採用。

## Consequences

- schema と visual vocabulary を version 管理し、追加・削除・変更・移動・不明を色だけでなく記号でも示す。
- source code、comment、literal、secret、absolute path は Artifact に含めない。SQL default literal は redact する。
- config precedence は CLI、`.code-structure-viz.toml`、built-in の順とし、解決結果を manifest に残す。

## References

- インタビュー Artifact: `20260824t025616z-interview-codestructureviz-specification-interview.md`
- 反映先: CLI output contract、JSON schema、PlantUML renderer、manifest、exit status
