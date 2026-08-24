---
種別: 要件定義書（Initiative）
ID: "init-00001"
タイトル: "Visualize Code Structure Changes"
関連GitHub: ["#1"]
状態: "draft"
最終更新: "2026-08-24"
---

# init-00001 Visualize Code Structure Changes — 要件定義

詳細: [Requirement Guide](../../docs/authoring/requirement.md)

## 目的

CodeStructureViz を、coding agent が source structure と変更影響を安全かつ再利用可能な Artifact として取得する独立 CLI product として成立させる。agent 自身の機械的理解と、人間へ説明するための domain-specific 図の両方を一つの contract で提供する。

本 Initiative は Python class、SQLAlchemy declarative ER、Next.js/React component の三 domain を一つの投資境界に含める。snapshot と temporal diff は別 use case とし、diff は Git text diff ではなく before/after semantic snapshot を正本とする。

## 背景

- code review の入口として構造図は有用だが、既存の `pyclassuml` と `tree-git-diff` は個別目的の legacy reference であり、将来 product の runtime boundary ではない。
- Git hunk、rename/copy status、runtime reflection だけでは semantic change、削除 entity の relation、partial failure を正確に扱えない。
- 主利用者は Codex 等の coding agent であり、machine-readable schema、deterministic output、failure provenance、safe redaction が必要である。
- exact verified commit `7951ddabc2e6a3d66edb77eada7c6c16923264f7` の interview と accepted ADR 8件が durable decision boundary を固定する。現 canonical R/D/P は template scaffold であり、本 package が whole-file adoption candidate となる。

## 観測可能な要件

| ID | 観測面 | Initiative requirement |
| --- | --- | --- |
| INIT-REQ-001 | 三 domain の利用者成果 | coding agent と人間が Python class、SQLAlchemy ER、Next.js/React component の snapshot と temporal diff を静的に取得できる。 |
| INIT-REQ-002 | 安全な独立 product | CodeStructureViz は legacy tool から独立し、target application と mutable Git operation を実行しない。 |
| INIT-REQ-003 | semantic diff | diff は before/after immutable semantic snapshot を正本とし、FileChangeSet と SemanticChangeSet を分離する。 |
| INIT-REQ-004 | agent-first output | versioned semantic JSON、domain-specific PlantUML、provenance manifest を生成し、redaction と SHA-256 を保証する。 |
| INIT-REQ-005 | failure/status | not_applicable と incomplete を区別し、partial success Artifact を保持して 0/1/2/3/130 exit contract を提供する。 |
| INIT-REQ-006 | platform/operability | macOS/Linux、Python 3.12+、Git 2.39+、Next 利用時 Node 22 LTS+、minimum/latest CI、offline runtime を満たす。 |
| INIT-REQ-007 | delivery milestones | Python+SQLAlchemy 完了を intermediate release、Next と all-domain orchestration 完了を Initiative completion とする。 |
| INIT-REQ-008 | scope exclusion | product HTML report/command/publication、runtime tree、DB/Alembic execution、native Windows、public plugin ABI、legacy CLI compatibility を対象外とする。 |

### outcome boundaries

- **INIT-REQ-001**: 一つの CLI product として三 domain を扱い、domain ごとの identity/member/relation/matching semantics は失わない。
- **INIT-REQ-003**: snapshot は whole structure または targeted dependency context を所有し、diff diagram は changed seed と configured context だけを所有する。
- **INIT-REQ-004**: JSON と PlantUML は selectable、format 未指定は両方。manifest は endpoint、fingerprint、version、coverage、diagnostic、relative path、SHA-256 を持つ。
- **INIT-REQ-005**: empty/unknown/error を同一視せず、agent が status と exit code から次 action を決定できる。

## スコープ

### 対象

- Python 3.12+ core/CLI/Git/manifest/Python/SQLAlchemy implementation。
- repository-owned TypeScript/Node Next adapter と versioned JSON bridge。
- snapshot/diff、safe source acquisition、domain analysis、semantic JSON、PlantUML、diagnostic、manifest、acceptance/CI/packaging。
- macOS/Linux local repository analysis。Git 2.39+。Node は Next target の解析時だけ必要。
- explicit CLI/config behavior、budgets、redaction、accessibility-aware visual vocabulary。

### 対象外

- product feature としての HTML report generation、HTML command、Tailscale/public publication。将来の別 Epic 候補に留める。
- DB connection、Alembic/runtime metadata、migration execution、target application/module/plugin/build script 実行。
- Next runtime component tree、non-literal dynamic behavior の推測、browser DOM/bundle analysis。
- native Windows、public third-party plugin ABI、remote execution、legacy CLI compatibility。
- `pyclassuml` と `tree-git-diff` への runtime/package/CLI dependency。

### specification HTML との分離

本 package の `explanation.html` は R/D/P を理解するための standalone specification Artifact である。製品が生成・配信する HTML ではなく、製品 CLI/schema/runtime scope に含めない。

## 失敗・境界条件

- implicit base を安全に解決できない場合、initial commit へ fallback せず fail closed。auto fetch しない。
- working tree は必要 source を repository 外へ freeze し、開始/終了 fingerprint drift では success Artifact を公開しない。
- U path は FileChangeSet evidence に残せるが affected semantic analysis は incomplete。
- target 不在は not_applicable、target 存在かつ解析不能は incomplete。partial domain failure は成功 Artifact を保持し exit 3。
- implicit changed path 1,000、entities per diagram 500、upstream/downstream depth 各 1 を built-in default とする。超過は truncation せず nonzero、明示 override を manifest に残す。
- source body、comment、literal、secret、absolute path を Artifact に含めない。SQL default literal は parser boundary で redact し、initial release に `--include-literals` を設けない。
- output directory は必須。既存 file を上書きせず、target repository へ default write しない。

## 受け入れ条件

| ID | Initiative completion evidence | trace |
| --- | --- | --- |
| INIT-AC-001 | Python snapshot/diff が exact semantic and safety contract で受け入れられる。 | ISSUE-01, ISSUE-02 |
| INIT-AC-002 | SQLAlchemy snapshot/diff と row-level ghost/before-after contract が受け入れられる。 | ISSUE-03, ISSUE-04 |
| INIT-AC-003 | ISSUE-04 完了時に Python+SQLAlchemy intermediate release gate が通る。 | ISSUE-04 / I04-AT-001〜006 |
| INIT-AC-004 | Next snapshot/diff が first-party TypeScript adapter と optional Node contract で受け入れられる。 | ISSUE-05, ISSUE-06 |
| INIT-AC-005 | domain 無指定 run、partial success retention、aggregate manifest、exit contract が受け入れられる。 | ISSUE-07 |
| INIT-AC-006 | read-only Git、static execution trap、redaction、determinism、budget negative test が全 domain で通る。 | I01/I02/I03/I04/I05/I06/I07 security/negative tests |
| INIT-AC-007 | minimum/latest CI、lockfiles、license inventory、offline runtime test が通る。 | I07-AT-006, I07-AT-007 |
| INIT-AC-008 | 製品 R/D/P と CLI に HTML runtime output を導入していない。 | EPIC-AC-008 と scope scan |

Initiative complete は `INIT-AC-001`〜`INIT-AC-008` がすべて成立し、exactly one Epic の completion report がこれを確認した時点とする。Next 未完の Python+SQLAlchemy release は intermediate milestone であり Initiative completion ではない。

## 制約・前提

- authority order: accepted ADR、interview、latest user scope、verified repository facts。解消不能な material question だけ `open-questions.md` に置く。
- dependency は exact lockfile、license review、offline runtime を必要とする。optional Next dependency は core install/runtime から分離する。
- CI は minimum supported version と repository-managed latest stable version を明示 matrix で実行する。floating `latest` label だけを再現性根拠にしない。
- Git repository は read-only。fetch/checkout/reset/stash/clean/ref/index/worktree mutation を禁止する。
- diagram は code/test review の代替ではなく、source provenance と coverage を持つ review entry point である。
- existing metadata `.meta.json` は package から直接変更しない。adoption は SpecDock commands と whole-file copy/import gate に従う。
