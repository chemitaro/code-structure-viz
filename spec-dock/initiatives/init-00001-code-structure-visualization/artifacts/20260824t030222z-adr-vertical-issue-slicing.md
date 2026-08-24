---
種別: ADR（Architecture Decision Record）
ID: "20260824t030222z-adr"
タイトル: "Vertical Issue Slicing"
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

# 20260824t030222z-adr Vertical Issue Slicing

## Context

- この Initiative は一つの Epic と複数 Issue で構成する。
- contract、source freezer、parser、renderer のような技術層だけで Issue を切ると、単独で利用者価値を検証できず、長期間統合不能になる。
- 既存の七 Issue 案は事前検討にすぎず、最終的な数と境界は高精度分析で再評価する必要がある。

## Decision

- Issue は vertical slice とし、各 Issue が CLI input、source acquisition、domain analysis、semantic JSON、PlantUML、diagnostic、acceptance test まで end-to-end に届ける。
- common foundation だけ、parser だけ、renderer だけを完成条件にする horizontal Issue は作らない。
- 一つの Epic の中で、Python と SQLAlchemy の利用可能な中間 release milestone を置き、Next.js 対応完了を Initiative 完了とする。
- Issue 数と境界はこの原則に従って GPT-5.6 Pro が再分析し、既存案を権威として踏襲しない。

## Options

- 技術層ごとの水平分割: 並行実装しやすく見えるが統合価値を遅らせるため不採用。
- domain ごとの巨大 Issue: end-to-end だが review と rollback の単位が大きすぎるため不採用。
- 観測可能な利用シナリオごとの vertical slice: common code の段階的成長は必要だが、各 Issue を受け入れ可能にできるため採用。

## Consequences

- 各 Issue の R/D/P は repository path、symbol、test、command、dependency、stop condition、traceability まで具体化する。
- common foundation は最初に独立完成させず、最初の slice で必要最小限を実装し後続 slice で拡張する。
- slice が単独で CLI から Artifact まで検証できない場合は分割を見直す。

## References

- インタビュー Artifact: `20260824t025616z-interview-codestructureviz-specification-interview.md`
- 分割評価規約: `assess-issue-granularity`
- 反映先: Epic Plan、全 Issue の Requirement / Design / Plan
