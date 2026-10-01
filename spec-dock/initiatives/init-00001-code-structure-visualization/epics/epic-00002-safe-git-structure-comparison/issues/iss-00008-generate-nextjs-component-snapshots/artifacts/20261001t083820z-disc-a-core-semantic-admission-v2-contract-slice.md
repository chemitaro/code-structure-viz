---
種別: disc
ID: "20261001t083820z-disc"
タイトル: "a-core-semantic-admission-v2-contract-slice"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-10-01"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: []
reflected_to: []
---

# 20261001t083820z-disc a-core-semantic-admission-v2-contract-slice

採択済みAのtransport→Core semantic admissionを閉じるreference checkpointです。baseはclean/pushed `911a151e3365263f6b563155eef88c146b6552c9`。production `src`・依存・旧v1 schema/producerは変更していません。後続のpublic/failure unionはまだ未完了です。

## Inputs

- Current R/D/P、accepted A ADR、new exchange/compatibility docs。
- new Core seam/reference owner、`test_next_semantic_candidate_v2.py`、actual source acquisition fixture。
- old semantic ID/model/proof/target/export算法。旧wire/runtime certificationは呼びません。

## Synthesis

- transportで受理したmodel_digest=0×64をCoreは拒否。再hashした空/別source metadataもsource correspondenceで拒否します。
- selected missing/byte-identical duplicate、proof-derived selected taintは完全なbase/proof検証後にtarget unavailable。無関係な不正record/proofをtarget reasonで隠しません。
- Core decisionは同じsource/asset/transport/gate/parent compatibilityを保持し、fresh projectionsを返します。actual TSまたはpublicationのcertificateではありません。
- known corpus `src/Card.tsx`、`src/string-unknown.tsx`のsemantic fixtureをnew source/requestへ結合します。old export/proof oracleのfixture lookupはreferenceに限定し、productionにはactual frozen inputの一般化されたTS/witness実装が必要です。

### Red→Green evidence

- missing Core入口→model digest拒否、再hashされた空project/異なるfile metadata拒否。
- source-bound positive model/proof→derived gate、selected missing/identical duplicate routing、immutable decision factory、proof-selected taintがpartial-safeへ誤昇格する問題の修復を各focused selectionで検証。
- model-record +1が受理される意図したREDは、actual約10k context filesのfull chainで観測（original 14971、exit 1、309.68s）。quiet jobを再起動せず終了まで保持しました。このfixtureは同じmodel-record境界のgenerated propsへ置換してsource I/Oを不要にします。raw/requestの小さいactual sealを維持し、file-count/source acquisitionのperformance改善は別scopeです。
- proof-valid unknown string exportがcompleteになる意図したREDを観測。count/export GREEN selection（original 82874）→ 2 passed、40.09s、exit 0。最終のexact/+1 vectorは小さいactual source sealとgenerated propsを使い、偽counterで境界を代用しません。
- 非公開proof-only File/Module/Componentのphantom source、context-only FileのModule化、dangling ownershipが通る意図したRED→source/declared-reference joinをGREENで閉じました。published metadataの再hashだけでunobserved sourceを捏造できません。
- closed constructor/duck owner拒否、projection alias、actual source sealのrebind、source-bound zero entity、record budget exact/+1と不正proof優先、entity exact/+1とpartial-safe不昇格をhardeningで検証しました。

### Independent identity preimages

literal `{kind, version:1, identity}`を`jq -cjnS ... | shasum -a 256`で計算。new producerの出力でexpectedを生成していません。

- Card module: `824683f7952e8b11fdeb41f85419fe44398dac828c221140a11bd31e433df71e`。
- Card router_context fact: `88cd5b76689041e7b68f733b5fc162f5ae0cdff5aef9f10c861f6ab5a7959999`。
- Card component: `6227b1d19e897d12ed303743051ed58b6fac3fd2b7c64b03175713939d0cc3d9`。
- string-unknown module: `0d5793bbfc727772d88500d15174f3e1d0e105a7fa288f777411d3359f5df50a`、fact: `ac9c259691a94d1f6d7e3130c79153d96bb691282ff9f2889125ec1a582ee390`。

### Verification

- `uv run --locked pytest -q tests/contracts/test_next_semantic_candidate_v2.py -k 'not generated_model_record_limit' --tb=short`（hidden reference追加前）→ 23 passed、2 deselected、8.17s、original 59190/exit 0。
- `uv run --locked pytest --collect-only -q tests/contracts/test_next_semantic_candidate_v2.py` → new 26 tests。collectionを実行証拠に数えず、下記related runで全26を実行しました。
- `uv run --locked pytest -q tests/contracts/test_next_semantic_candidate_v2.py tests/contracts/test_next_exchange_v2.py tests/contracts/test_next_request_frame_v2.py tests/contracts/test_next_trusted_environment_v2.py tests/contracts/test_next_runtime_v2_contracts.py tests/contracts/test_next_response_frame_v2.py tests/contracts/test_next_process_observation_v2.py tests/contracts/test_json_schemas.py tests/unit/next/test_source_acquisition.py tests/unit/next/test_protocol.py tests/contracts/test_next_contracts.py::test_round23_rg_18_current_schema_and_history_contract_are_explicit --tb=short` → 444 passed、85.77s、original 57663/exit 0。
- `uv run --locked ruff check .` / `ruff format --check .` → pass、198 files。途中のimport/line-wrap/regex styleを通常formatと局所修正で閉じ、ruleを無効化していません。
- `uv run --locked mypy src tests` → pass、164 source files。generated member listのannotationを明示し、schema/runtime behaviorを弱めません。
- 記録更新後の`./spec-dock/scripts/spec-dock sync --no-github` / `validate` → pass、nodes=10、active unchanged。doc-pointer selection → 1 passed（0.14s）、`git diff --check` → pass。新全chain/両OS/TS/installed package/A03のpassを主張しません。

## Options and trade-offs

- old wire非依存semantic algorithmを再利用し、runtime v2をold certificationへ変換しません。
- opaque Core ownerはsingle authorityを明示しますが、nominal type/constructor closureをsame-UID confinementと呼びません。
- generated semantic recordsはtransport/Core record-count・予算境界を検証するfixtureであり、実TS recognition/propsの受入れではありません。

## Reflection

- Core入口/ownerと保持・移行境界をCurrent Design/Planへ、実行結果をReportへ反映します。
- new failure/provenance/public chain、actual OS/TS/CLI、A03独立reviewは後続の必須gateです。Issue/goalは未完了のままです。
