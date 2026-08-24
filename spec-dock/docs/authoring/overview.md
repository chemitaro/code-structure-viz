# Authoring Kit 概要

このガイドは、Initiative / Epic / Issue の仕様を Markdown で書き始めるための入口です。特定の agent、model、provider、review 手順を前提にしません。必要な支援や手順は、利用するプロジェクトの状況に合わせて選んでください。

各 scope は `requirement.md`、`design.md`、`plan.md`、`report.md` を一組として持ちます。文書は役割ごとに分け、長く残る判断は適切な正本へ記録します。

## 何をどこに書くか

- [Requirement Guide](requirement.md): 問題、利用者の成果、対象範囲、受け入れ条件を明確にする。
- [Design Guide](design.md): Requirement を満たす構造、責務境界、interface、失敗時の扱いを決める。
- [Issue Plan Guide](issue-plan.md): Issue の実装順序、検証、移行、残るリスクを実行可能な形にする。
- [Report Guide](report.md): 実装後の結果、検証、残るリスクを短く残す。
- [Scope Layering Guide](scope-layering.md): Initiative / Epic / Issue の責務と、親子間で再定義しない境界を確認する。
- [Artifact Guide](artifacts.md): Current の evidence と、durable な内容の反映先を確認する。

## Planning Level

Issue の canonical `plan.md` は一つです。完成基準は選んだ一つの Guide を参照します。

- [light Completion Guide](issue-plan-levels/light.md)
- [standard Completion Guide](issue-plan-levels/standard.md)
- [strict Completion Guide](issue-plan-levels/strict.md)
- [critical Completion Guide](issue-plan-levels/critical.md)

## Agent assistance

Agent assistance の導線は Issue 359 の handoff 後に追加できます。`.agents/skills/spec-dock/SKILL.md` と `.agents/skills/spec-dock-grill-with-docs/SKILL.md` が実在し、link 解決を確認するまでは、この節に live Markdown link を置きません。

## 基本原則

- Requirement は「なぜ・何を満たすか」、Design は「どの構造で満たすか」、Plan は「どの順序で確かめながら実装するか」を扱います。
- Report は結果の要約です。将来も参照される判断は Requirement、Design、Plan、または accepted ADR に反映します。
- まず親 scope の目的、分割、依存方向を読みます。下位 scope はそれらを言い換えず、担当する具体的な価値と受け入れ条件を追加します。
- 調査メモや会話などの evidence は、内容を検討してから正本へ反映します。ファイルが存在するだけで採用済みにはなりません。

## Scope ごとの使い分け

Initiative は複数 Epic にまたがる投資と成果を、Epic は一貫した product / architecture outcome と Issue 分割を、Issue は一つの end-to-end で観測できる価値を扱います。詳細は [Scope Layering Guide](scope-layering.md) を参照してください。
