---
種別: ADR（Architecture Decision Record）
ID: "20260824t030221z-02-adr"
タイトル: "Domain Adapter Boundaries"
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

# 20260824t030221z-02-adr Domain Adapter Boundaries

## Context

- Python class、SQLAlchemy ER、Next.js/React component は identity、member、relation、matching の意味が異なる。
- すべてを一つの汎用 model へ押し込むと、精度を落とすか common layer を複雑化する。
- Next.js/TypeScript の正確な静的解析には TypeScript compiler API が適している。

## Decision

- common layer は source snapshot、Git comparison、diagnostic、artifact/manifest、共通 graph primitive に限定する。
- semantic identity、member、relation、matching、domain-specific rendering は各 adapter が所有する。
- Core、CLI、Git、manifest、Python、SQLAlchemy は Python 3.12 以上で実装する。
- Next adapter は repository-owned の TypeScript/Node component とし、TypeScript compiler API を使う。Python 側とは versioned JSON 契約で接続する。
- Node.js 22 LTS 以上は Next adapter を利用するときだけ要求する。

## Options

- 完全共通 semantic model: 表面的には統一できるが domain の意味を失うため不採用。
- 全実装を Python に統一: 配布は単純だが TypeScript 意味解析の精度を下げるため不採用。
- 最小 core と domain adapter、Next の first-party Node component: 境界管理は必要だが精度と保守性を両立するため採用。

## Consequences

- adapter 間 JSON schema の version、compatibility、diagnostic contract を固定する。
- domain ごとの optional dependency と lockfile を分離する。
- common abstraction が domain-specific field を吸収し始めた場合は、この ADR を見直す。

## References

- インタビュー Artifact: `20260824t025616z-interview-codestructureviz-specification-interview.md`
- 反映先: package layout、adapter protocol、Next bridge、test matrix
