---
種別: disc
ID: "20260912t065527z-disc"
タイトル: "Next compiler options implementation slice"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-09-12"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: []
reflected_to: []
---

# 20260912t065527z-disc Next compiler options implementation slice

複数の証拠を統合し、選択肢と trade-off を整理します。一つの source の調査は `research` を使います。

## Inputs

- Issue #8 `requirement.md:25, 682-684, 829-834`、`design.md:40, 740-758, 1031-1047, 1665-1675`、current-v1 `plan.md:17-38, 101-107`。
- 現行契約: `docs/contracts/next-config-v1.md:1-5, 342-348`、`schemas/next-config-v1.schema.json`、`schemas/next-source-plan-v1.schema.json`。
- 実行可能なreference: `tests/contracts/next_reference_validation.py:4050-4445` と `tests/contracts/test_next_contracts.py:6000-6170, 12842-12915`。
- TypeScriptの公式 `extends` / TSConfig説明: <https://www.typescriptlang.org/tsconfig/extends.html>。継承元で宣言された相対pathは宣言元configを基準に解決する。
- 実装対象の基点: branch `iss-00008-generate-nextjs-component-snapshots`、親SHA `c769b18eb8fce1a81f94c1aca12cad97357c1deb`。前段の凍結bytes JSONC/local-extends closure はそのSHAに含まれる。

## Synthesis

- `resolve_compiler_options` は `ResolvedControlClosure` のみを受け、filesystemやNodeへアクセスしない。compiler option defaults、closed enum/module policy、project-local `baseUrl`/`paths`、declaring-config origin、stable alias precedenceを導出する。
- `plugins` / `typeRoots` / `types` は `CSV-NEXT-CONFIG-002`、unsupported optionや型・path違反は `CSV-NEXT-CONFIG-001` / `source_control` でfail-closedとする。
- emit/build-only allowlistは型検査後にsemantic option projectionへ混入させず、closureの宣言元記録に残す。これはsource acquisitionやCLIへまだ接続されていない独立sliceである。
- TDDでmissing resolverとunhashable `jsx` valueのredを確認してから実装。focused unitは61 passed。全体pytestは1558 passed / 1 skipped、mypyは145 source files、Ruff check/format、SpecDock validationもgreen。全体pytest実行中に冗長なboolean-option再検査を除いたため、candidate固定後に最終確認を繰り返す。
- **未確定のmaterial conflict:** `design.md:1045` は `files` をproject-relativeと記す。一方、実行可能source-seal testは継承元configのdirectory相対を要求し、TypeScript公式仕様も宣言元相対を説明する。`files/include/exclude` の相対path baseをユーザーに問い合わせ中であり、membership resolverはまだ実装しない。推奨案はTypeScriptとreference-testに揃え、Design表を宣言元相対へ修正すること。
- 先行control-closure sliceの独立Spec/Standardsレビューは `c29064c...c769b18` でpass。compiler-options sliceの固定SHAレビューは未実施。

## Options and trade-offs

- **compiler options:** defaultsと実行時に関係する閉じた値だけを正規化し、`baseUrl`/`paths` replacementは宣言元configからrepository-relativeへ解決する。ignored build valuesをsemantic projectionに混ぜないため、既存schemaを維持する。
- **membership path origin (pending):** (A) 宣言元config相対 — TypeScriptの継承意味と実行可能source-seal testに一致する。(B) project-root相対 — Design表の現文言に一致するが、継承base configの意図を変え、テストと外部仕様にも矛盾する。推奨はA。ユーザー回答前にどちらも実装しない。
- 現候補SHAの固定点・両軸レビュー・commit/push結果はこのArtifactの後続追記で記録する。

## Reflection

- canonical Requirement/Planの順序は変えない。ユーザーがmembership originを選んだら、Designの食い違う行を修正する必要性を判定し、正本修正は別scopeとして記録する。
- このArtifactは調査/進捗証拠であり、compiler options全体、membership、source seal、CLI、Issue #8の受入れ完了を主張しない。

## Fixed-SHA compiler-options review and remediation evidence

- Candidate: `4f49ac9e7ccdf2c5d1b4846d5345a8c209f639d4`; fixed point: `c769b18eb8fce1a81f94c1aca12cad97357c1deb`. The compiler-options review covered its implementation/remediation slice through this candidate. At review start/end, local `HEAD`, configured upstream, and GitHub branch matched the candidate and the checkout was clean.
- Spec review: `P0=0 / P1=0 / P2=0 / review_status=pass`; no findings. The reviewer confirmed `apps/web/tsconfig.json` `paths` replacement `"."` resolves at the selected nested project root while repository-root `"."` remains rejected, root `baseUrl` remains permitted, boolean-option handling is preserved, and the `allow_root_sentinel` rename is behavior-neutral.
- Standards review: pass; hard violations `0` and unresolved judgement calls `0`.
- Focused configuration evidence: `.venv/bin/python -B -m pytest tests/unit/next/test_configuration.py -q -p no:cacheprovider --tb=short` → `63 passed`. This suite covers the broader configuration module, including JSONC/control-closure cases; it is not an isolated compiler-options suite. Primary verification for the same code-content candidate: full suite `1560 passed, 1 skipped`, mypy `145` source files, Ruff check/format, and SpecDock validation passed. The independent reviewer did not rerun those broad checks.
- The nested-project fix is commit `65a0848`; the sentinel-name clarification is commit `4f49ac9`. Together with the implementation commit `c93cb00`, these are the compiler-options changes in this slice. The separate package-applicability review evidence is recorded in `20260912t042823z-disc-package-applicability-review-remediation.md`.
- This pass is limited to compiler-option resolution. It does not resolve the material `files/include/exclude` membership-origin conflict: `design.md:1045` says project-root-relative, while the executable source-seal tests and TypeScript `extends` semantics point to declaring-config-relative. No membership resolver or canonical Design change is authorized by this evidence; obtain the user's choice before that work. It also does not certify source seal, CLI, output generation, or Issue #8 acceptance. Updating this record changes the candidate SHA and requires a separate documentation-only review.
