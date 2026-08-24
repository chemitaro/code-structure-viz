---
種別: 計画書（Epic）
ID: "epic-00002"
タイトル: "Establish Safe Git Structure Comparison"
関連GitHub: ["#2"]
状態: "draft"
最終更新: "2026-08-24"
依存: ["requirement.md", "design.md"]
親: ["init-00001"]
---

# epic-00002 Establish Safe Git Structure Comparison — 計画

詳細: [Scope Layering Guide](../../../../docs/authoring/scope-layering.md)

## 目標

seven vertical Issues を topological order で統合し、安全な snapshot/diff product と three domain support を一つの Epic outcome として完成させる。個別 Issue の implementation micro-step は各 `plan.md` を正本とする。

## 順序・依存

| Stable key | recommended title | declared dependencies | release/handoff |
| --- | --- | --- | --- |
| ISSUE-01 | Generate Python Structure Snapshots | なし | internal foundation を兼ねる最初の利用可能 slice。ただし release milestone とはせず、Python diff 完了後に Python domain preview とする。 |
| ISSUE-02 | Compare Python Structure Changes Safely | ISSUE-01 | ISSUE-01 と合わせて Python domain preview。Git comparison foundation は後続 domain diff が再利用するが、Python 固有 matching は adapter 内に残す。 |
| ISSUE-03 | Generate SQLAlchemy ER Snapshots | ISSUE-01 | ISSUE-01 の common snapshot/output contract を拡張する SQLAlchemy snapshot slice。ISSUE-04 完了までは ER diff を約束しない。 |
| ISSUE-04 | Compare SQLAlchemy ER Changes | ISSUE-02, ISSUE-03 | ISSUE-01〜04 で Python class と SQLAlchemy ER の snapshot/diff が利用可能となる intermediate release milestone。 |
| ISSUE-05 | Generate Next.js Component Snapshots | ISSUE-01 | Next snapshot preview。Python/SQLAlchemy の install/runtime requirement へ Node を持ち込まない optional adapter separation を完成させる。 |
| ISSUE-06 | Compare Next.js Component Changes | ISSUE-02, ISSUE-05 | Next domain diff preview。ISSUE-07 の統合前でも `--domain next` の単独利用が可能な acceptance boundary。 |
| ISSUE-07 | Run Unified Multi-Domain Structure Comparison | ISSUE-04, ISSUE-06 | Next.js 対応と multi-domain orchestration の完了をもって Initiative 完了。Python+SQLAlchemy intermediate release からの additive extension とする。 |

DAG edges:

```text
ISSUE-01 -> ISSUE-02
ISSUE-01 -> ISSUE-03
ISSUE-02 -> ISSUE-04
ISSUE-03 -> ISSUE-04
ISSUE-01 -> ISSUE-05
ISSUE-02 -> ISSUE-06
ISSUE-05 -> ISSUE-06
ISSUE-04 -> ISSUE-07
ISSUE-06 -> ISSUE-07
```

- ISSUE-03 と ISSUE-05 は ISSUE-01 後に並行可能。
- ISSUE-04 は Python diff spine と SQLAlchemy snapshot の両方を必要とする。
- ISSUE-06 は Git/diff spine と Next snapshot/protocol の両方を必要とする。
- ISSUE-07 は intermediate backend release と Next diff release を統合する final boundary。

## 実装step

| Phase | Issue outcomes | Epic-level integration gate |
| --- | --- | --- |
| P1 Python spine | ISSUE-01, ISSUE-02 | domain presence/empty-side、start-HEAD anchor、metadata-only FileChangeSet、run/domain budgets、CLI/schema/source/Git/Artifact v1 contract frozen for consumers |
| P2 Backend semantics | ISSUE-03, ISSUE-04 | Python+SQLAlchemy acceptance, row diff, intermediate release |
| P3 Next semantics | ISSUE-05, ISSUE-06 | Node optionality, adapter protocol, component diff |
| P4 Product completion | ISSUE-07 | per-domain semantic output、aggregate `run-manifest/v1`、cross-domain presence/budget/status/exit、package/platform、Initiative trace |

Epic-level integration does not create separate contract-only/source-only/renderer-only Issues. Shared changes remain in the first vertical slice that exercises them.

## 検証

- Run all Issue acceptance commands in topological order and full suite after each phase.
- P1 で Python diff の endpoint matrixに `--to working-tree` without `--from` を含め、start HEAD anchor、frozen digest、candidate、merge-base、resolution methodを検証する。
- P1/P2/P3 で Python、SQLAlchemy、Next の both-present/both-absent/before-only/after-only/analysis-failure truth tableを同一 expected status/publication/exitで検証する。
- implicit changed-path 1,001 overrun は exit 1・diagnostic only・final manifestなし、entity 501 overrun は affected domain incomplete・exit 3・affected payloadなし・safe manifest/sibling保持とする。valid overrides は requested/resolved/countをmanifestへ残す。
- FileChangeSet hunkがold/new ranges、status、content-independent IDだけを持ち、raw patch/context/source/comment/literal/secret/absolute pathを全 channelへ出さないことをnegative fixtureで確認する。
- domain 無指定 run は各 domain semantic JSON/PlantUML と `code-structure-viz.run-manifest/v1` だけを公開し、`code-structure-viz.semantic/v1` の `domain: all` payloadを公開しない。
- Confirm output determinism, no overwrite, Git state preservation, source execution traps, partial success retention, minimum/latest CI, core-only/Next-enabled offline install and license inventory.
- Confirm exactly one Epic, seven vertical Issues, unchanged acyclic DAG, full Requirement→Design→Plan→acceptance→test trace, and no product HTML command/schema/UI/publication.

## rollback

- phase rollback の単位は latest Issue または phase とし、先に release 済みの domain は利用可能な状態を保つ。
- If common contract regression is found, stop downstream integration and repair the owning earlier Issue rather than patching private adapters independently.
- If Next adapter causes packaging/runtime regression, retain Python+SQLAlchemy intermediate release and disable Next/default-all rollout until forward fix.
- Existing SpecDock node metadata、reports、accepted ADR、interviewは保持する。canonical R/D/Pの採用を戻す場合はexact verified commitの対応27文書へwhole-file revertする。

## exit / handoff

- Each Issue reaches its own acceptance boundary and records residual risks for the next declared consumer.
- ISSUE-04 hands off an intermediate release, not Epic completion.
- ISSUE-07 must demonstrate EPIC-AC-001〜008 and INIT-AC-001〜008, after which Epic completion can be recorded.
- adopted R/D/P, imported evidence, validation output, and source baseline are handed to Codex/user for independent verification and repository integration.
