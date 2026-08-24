# 成果物ルール（artifacts/rules.md）

このディレクトリには initiative に紐づく Current working artifacts を置きます。

- Artifact workflow: Current `new artifact` surface が作成する作業用 evidence surface です。
- Naming rules: `spec-dock/docs/reference_naming.md`
- 作成される artifacts はこの directory に timestamp-prefixed original として保存されます。
  - typed artifacts: `<ts>-<type>-<slug>.md`
  - typed same-second collision: `<ts>-<nn>-<type>-<slug>.md`
  - blank artifacts: `<ts>-<slug>.md`
  - blank same-second collision: `<ts>-<nn>-<slug>.md`
- `blank` は filename token を使わず、front matter の `template: "blank"` で template identity を示します。
- Canonical `requirement.md` / `design.md` / `plan.md` / `report.md` は artifacts ではありません。canonical docs は main orchestrator single-writer authority です。
- Artifact は evidence / draft / synthesis / decision candidate の作業面です。採用は canonical docs、accepted ADR、または `report.md` Evidence Adoption Ledger への反映で成立します。
- `artifact import file --initiative <id> --file <path>` は、Workbench を要求せず、一件の明示 regular file を generic Artifact として保存します。source は変更せず、bytes は opaque evidence のままです。`canonical=false` は自動採用しないことを表します。命名は [reference_naming.md](../../reference_naming.md)、privacy-safe result と publication / retry state は [guide.md](../../guide.md) を参照してください。
- Legacy `discussions/` は preservation surface です。既存 discussion docs は削除、移動、rename せず grandfathered evidence として扱います。
- Current `artifacts/` surface は legacy `discussions/` validation を弱めません。
- ADR originals may live under Current `artifacts/` or legacy `discussions/`; ADR mirror collection must collect both without moving originals.
- Direct artifact template catalog:
  - `blank`: 型を先に決めない working evidence。filename に `blank` token は要求しません。
  - `research`: source-grounded read。事実、推測、未検証、用語衝突、edge case、判断への含意を分ける。
  - `interview`: docs-aware clarification の正式質問シート。重要判断は一問一答で扱う。
  - `disc`: synthesis / 中間レポート / reflection proposal / ADR candidate triage。
  - `decision-candidate`: canonical docs / ADR / report ledger へ採用する前の判断候補。
  - `adr`: 意思決定記録。作成直後は draft / non-authoritative / non-mirror で、accepted 後に authority fields と mirror eligibility を埋めます。
- Historical-only types: `pr-repair-batch`、`draft-requirement`、`draft-design`、`draft-plan`、`scratch`、`note`。既存fileはvalidation対象として保持しますが、Currentの新規作成catalogには含めません。
- 実行場所: コマンドはリポジトリ root から実行してください。`./spec-dock/scripts/spec-dock ...` はその位置で保証される実行経路で、nested directory では相対 path が変わります。
