---
種別: ADR（Architecture Decision Record）
ID: "20260824t030222z-02-adr"
タイトル: "Exclude Product HTML Reports"
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

# 20260824t030222z-02-adr Exclude Product HTML Reports

## Context

- 差分結果を統合した HTML report は将来価値があるが、semantic JSON と PlantUML による正確な解析契約より優先度が低い。
- HTML report の生成・配信まで同じ Epic に含めると、初期利用可能性と semantic 精度の達成が遅れる。
- 仕様理解のために作る説明 HTML Artifact は、製品 runtime の出力機能とは別物である。

## Decision

- 現在の Initiative / Epic では、製品機能としての HTML report 生成と配信を対象外とする。
- 現在の製品出力は versioned semantic JSON と PlantUML に集中する。
- HTML report は将来の別 Epic 候補として扱い、今回の R/D/P で command、schema、UI、配信仕様を具体化しない。
- Epic と各 Issue を説明する standalone 日本語 HTML は specification Artifact として作成する。これは製品要件でも製品 runtime output でもない。

## Options

- 最初から HTML report を自動生成する案: 利便性は高いが scope と検証面が大きくなるため不採用。
- HTML を完全に扱わない案: 製品 scope は小さいが仕様理解の要望を満たさないため不採用。
- 製品 HTML は延期し、仕様説明 HTML Artifact だけを作る案: 製品の焦点と説明可能性を両立するため採用。

## Consequences

- 将来 Epic では、統合 report、Tailscale 配信、複数 diagram 統合、security boundary を改めて要件化する。
- 今回の説明 HTML は `japanese-explanatory-html` contract version 2 に従って検証する。
- 現在の CLI に HTML format flag や HTML command を予約しない。

## References

- インタビュー Artifact: `20260824t025616z-interview-codestructureviz-specification-interview.md`
- 仕様説明形式: `japanese-explanatory-html`
- 反映先: Initiative / Epic scope、Issue scope、specification Artifact package
