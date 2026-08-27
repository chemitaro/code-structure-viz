---
種別: レポート（Issue）
ID: "iss-00005"
タイトル: "Compare Python Structure Changes Safely"
関連GitHub: ["#5"]
最終更新: "2026-08-27"
依存: ["requirement.md", "design.md", "plan.md"]
親: ["epic-00002", "init-00001"]
---

# Result Summary

詳細: [Report Guide](../../../../../../docs/authoring/report.md)

## Outcome

Issue 5 の Python 構造差分 vertical slice を実装した。`diff` CLI は明示 endpoint、暗黙 base、開始時 HEAD anchor、working-tree freeze、Git read-only source acquisition、metadata-only `FileChangeSet`、Python semantic entity/member/relation diff、before/after union impact、unique structural move matching、domain presence、changed-path/entity budget、versioned semantic JSON、member-level PlantUML、run manifest、closed stdout selector を扱う。

既存の Issue 4 snapshot pipeline は維持し、Issue 5 の比較処理は CodeStructureViz 所有の endpoint/source/diff/application/renderer modules として追加した。`pyclassuml`、`tree-git-diff`、SQLAlchemy、Next.js、HTML/Tailscale、target repository の Git mutation、auto fetch/checkout は導入していない。

## Implementation Evidence

- `src/code_structure_viz/source/endpoints.py`: named endpoint と implicit base の解決、provenance。
- `src/code_structure_viz/source/freezer.py`: commit blob と frozen working-tree の immutable source view。
- `src/code_structure_viz/source/file_changes.py`: status/range/ordinal/content-independent hunk ID の metadata-only diff evidence。
- `src/code_structure_viz/semantic/diff.py`: domain presence、canonical empty side、semantic delta、union impact。
- `src/code_structure_viz/adapters/python/matcher.py` / `diff_renderer.py`: Python move matching と semantic JSON/PlantUML。
- `src/code_structure_viz/application/diff.py`: endpoint から publication までの one-run orchestration。
- `tests/acceptance/**`, `tests/integration/python/**`, `tests/security/**`, `tests/helpers/**`: Issue 5 acceptance/security/integration fixtures。

TDD の公開 seam は CLI process、SourceView/diff value、semantic differ、stdout/stderr、Artifact publication とし、endpoint、presence、budget、selector、impact、matching、redaction、Git immutability を table-driven に固定した。

## Verification

- `uv run pytest -q`: `398 passed, 1 skipped`
- Issue 5 focused acceptance/integration/security suite: `49 passed`
- `uv run ruff check .`: 成功
- `uv run mypy src tests`: 成功（97 source files）
- `uv build`: 成功
- `python3 ./spec-dock/scripts/spec-dock validate`: 成功（nodes=10）
- `git diff --check`: 成功

全Artifactは local output transaction の staging、closed path contract、atomic no-replace publication を経由し、working-tree run は publication 前に fingerprint drift を再確認する。テストでは same-input semantic result、stdout exact-byte copy、unavailable result、run-level/domain-level publication境界、raw patch/secret redaction、Git HEAD/index/refs/worktree不変性を確認した。

## Residual Risks / Follow-ups

- move matching は曖昧な候補を removed+added として扱い、意味のない moved を生成しない。複雑な rename/name evidence の拡張は後続検討とする。
- diff renderer の impact context は changed seed と指定 depth の安全なクラス集合へ限定する。HTML report、可視化共有、SQLAlchemy/Next adapter は後続 Issue の責務である。
- 仕様上の implicit changed-path default は1,000、Python entity default は500。override値と実測値は manifest に記録する。
- 実装履歴の各計画stepを単独コミットで再構成したとは主張せず、上記の as-built paths と検証結果だけを本Reportの実績とする。
