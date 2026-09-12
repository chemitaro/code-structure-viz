---
種別: disc
ID: "20260912t063003z-disc"
タイトル: "Next control closure implementation evidence"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-09-12"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: []
reflected_to: []
---

# 20260912t063003z-disc Next control closure implementation evidence

Issue #8 の source-seal 実装を段階化するため、凍結済み control bytes 上の local `extends` closure を実装し、reference validatorとの不一致を正本に合わせて修正した記録である。このArtifactは証拠であり、Requirement/Design/Planや最終source sealの代わりではない。

## Inputs

- current canonical authority:
  - Issue #8 `plan.md` の Current v1 normative authority: package-only applicability → controls/JSONC/local-extends/membership → source graph seal の順序。
  - `design.md` の SourceDiscoveryIntent / two-phase single-read protocol。control、program、context bytesは各1回だけ読み、最後のdrift check後に plan と SourceView を一つの seal operation で確定する。
  - `docs/contracts/next-config-v1.md`: single project-local `./...` extends、duplicate-key rejecting JSONC、`files`/`include`相互排他、明示された空配列の保持、control failureはtyped fail-closed。
- resumption evidence:
  - branch `iss-00008-generate-nextjs-component-snapshots`, base `c29064c5077a1050fc33d5863d71b957c3a4a62a`;開始時clean、HEAD/upstream/originのIssue branch ref一致。
  - SpecDock active pointersは`init-00001` → `epic-00002` → `iss-00008`。GitHub Issue #8 はOPEN。
  - 前段のfrozen-byte JSONC parser sliceは`2d1cba6...`でSpec/Standards review pass、Artifact-only記録commit `c29064c...` はSpec/Standardsともpass。
- current implementation candidate:
  - `src/code_structure_viz/adapters/next/configuration.py`
  - `tests/unit/next/test_configuration.py`
  - `tests/contracts/next_reference_validation.py`
  - `tests/contracts/test_next_contracts.py`

## Synthesis

- 実装した閉じた単位:
  - `resolve_control_closure` は事前に凍結されたpath→bytes mappingのみを使い、filesystem I/Oを行わない。
  - 選択project root外のcontrolを拒否し、明示的な単一のlocal `./...` extendsだけを解決する。bare/package/URL-like参照、absolute/parent traversal、non-canonical path、未捕捉parent、cycleを拒否する。
  - allowed top-level control keysを閉じ、`compilerOptions`をparentからchildへshallow mergeする。`include`/`exclude`/`files`はchildで置換し、空配列とdeclaration pathを保持する。closure path/edgeをparent-firstで返す。
  - 戻り値はsource seal内で消費するintermediateであり、final plan/viewやcaller-provided source authorityではない。
- 正本とreferenceの不一致を発見・修正:
  - 既存reference validatorは`control.get("extends") is None`を「extends未指定」と同一視していた。
  - Current v1では`extends`が存在する場合は一つのlocal stringでなければならないため、`extends: null`は`CSV-NEXT-CONFIG-001 / source_control`として拒否する。production resolver、source-acquisition reference、closed grammar contract testを揃えた。
- 未完了:
  - `resolve_control_closure`はNext CLI/source acquisitionから未接続。membership導出、effective role、source graph、read/revision instrumentation、atomic plan+view seal、typed source-result union、process/provenance/publicationも未実装。
  - したがって、このArtifactはsource seal段階の部分成果であり、Issue #8 implementation readiness/acceptance/passを意味しない。

## Options and trade-offs

- 次の実装順:
  1. frozen control closureをpackage applicability後のsource-seal処理に接続する。control candidatesとlocal extends bytesはtrusted inventoryから各1回だけ取得し、request/callerからresolved path/role/planを受け取らない。
  2. config declaration pathを保持しつつ`files`/`include`/`exclude`/source rootsをfrozen inventoryのpath namesに適用し、effective program/context membershipを導出する。空配列はdefaultに置換しない。
  3. membership確定後にprogram/context bytesを一度だけ取得し、request file setのpath/digest/sizeと照合、最後にrevision driftを確認する。成功時のみ同じoperationからfinal planとSourceViewを返す。
  4. malformed control、uncaptured/duplicate/post-seal read、caller-derived paths/roles、revision driftについてpositive/negative vectorsを追加し、実schemaとreference validatorに照合する。
- trade-off:
  - parser/closureをfilesystemから分離したことでJSONCとpath/merge semanticsを小さなunit testで固定できる。一方、このslice単体ではtarget repositoryの安全なsingle-readを証明しないため、後続sealに独立のacceptance evidenceが必要。

## Reflection

- 新たなProduct/Policy/Security判断は追加していない。既存current-v1契約を実装し、reference validatorのnull-extends挙動をその契約へ合わせた。
- 実行証拠（2026-09-12）:
  - `uv run pytest tests/unit/next/test_configuration.py tests/contracts/test_next_contracts.py -q -k 'configuration or source_seal_derives_plan_and_view_from_one_intent_and_rejects_drift or round21_jsonc_extends_grammar_is_closed_and_trailing_comment_is_deterministic' --tb=short` → 43 passed, 459 deselected。
  - `uv run pytest -q --tb=line` → 1538 passed, 1 skipped (169.68s)。
  - `uv run mypy src tests` → 145 source files, no issues。
  - `uv run ruff check .` → pass; `uv run ruff format --check .` → 169 files formatted; `git diff --check` → pass。
  - `./spec-dock/scripts/spec-dock validate` → `nodes=10`。
- 固定SHA review、commit、pushはこのArtifact作成時点では未実施。レビューの最終結果とcandidate SHAを、レビュー後に追記する。
- Next gate: fixed/pushed candidateに対する独立Spec/Standards reviewでP0/P1を確認した後、source seal + membershipの次段階へ進む。Issue全体の完了判定は引き続き未達。
