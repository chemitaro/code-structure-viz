---
種別: ADR（Architecture Decision Record）
ID: "20260824t030222z-01-adr"
タイトル: "Static Analysis Safety Boundary"
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

# 20260824t030222z-01-adr Static Analysis Safety Boundary

## Context

- coding agent が未信頼の repository を解析する用途では、対象 module の import や application code の実行が副作用・秘密漏えい・任意 code 実行につながる。
- SQLAlchemy metadata の runtime load、Next.js runtime tree、Git の自動変更は静的可視化 tool の責務を超える。

## Decision

- 解析は static source analysis に限定し、対象 application module、plugin、migration、build script を実行しない。
- SQLAlchemy は ORM declarative model source のみを解析し、DB 接続、Alembic 実行、runtime metadata load を行わない。
- Next.js は TS/TSX と安全に解釈できる JS/JSX subset を解析し、runtime component tree や non-literal dynamic import を推測しない。
- Git repository は read-only とし、自動 fetch、checkout、reset、stash、clean を禁止する。
- 出力は provenance に必要な path、symbol、signature、relation、line range に限定し、source 本文、comment、literal、secret、absolute path を含めない。

## Options

- 対象 code を import して introspection する案: 精度が高い場面はあるが安全境界を破るため不採用。
- sandbox 内で対象 code を実行する案: 運用負荷と環境依存が大きく初期製品の責務を超えるため不採用。
- static-only で不明を `UNKNOWN` として公開する案: 網羅率は下がり得るが、安全性と再現性を優先できるため採用。

## Consequences

- 動的にしか決まらない関係を事実として補完せず、coverage と diagnostic に残す。
- 外部 parser/library は利用可能だが、lockfile、license、offline runtime、optional dependency 境界を要求する。
- 将来 runtime 補助解析を追加する場合は、別の明示的 opt-in 製品境界と ADR が必要である。

## References

- インタビュー Artifact: `20260824t025616z-interview-codestructureviz-specification-interview.md`
- 反映先: source loader、domain adapters、redaction、diagnostics、security tests
