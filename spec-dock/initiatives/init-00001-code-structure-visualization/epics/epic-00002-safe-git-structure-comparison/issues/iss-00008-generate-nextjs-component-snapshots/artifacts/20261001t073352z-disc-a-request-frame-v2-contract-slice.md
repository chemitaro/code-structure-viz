---
種別: disc
ID: "20261001t073352z-disc"
タイトル: "a-request-frame-v2-contract-slice"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-10-01"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: []
reflected_to: []
---

# 20261001t073352z-disc a-request-frame-v2-contract-slice

採択済みAを変更せず、A02-2のsource-sealed private request seamを具体化したcheckpoint evidenceです。baseはclean/pushed `4bacd5f8ea1fd6ac7f520a0a4c24715a4e6204cf`。production、依存、旧v1 schema/envelopeを変更していません。

## Inputs

- accepted A ADR、Requirement/Design/PlanのCurrent normative authority。
- `docs/contracts/next-adapter-request-v2.md`、new request schema、small runtime reference/validator、`test_next_request_frame_v2.py`。
- real production `SourceAcquisitionSeal`を既存acquisition経由で作るfixture。Node/OS観測は含みません。
- adapter fixtureはheaderだけ、trusted declarationは既存locked 4 files。実TS compiler/installed bundleではありません。

## Synthesis

通常入口はactual source sealとretained assetsを受け、projects/filesを凍結SourceView/final plan/applicable rootsから導出します。metadata-only identityをcaller入力にせず、source/assetを再readしません。runtime requirementはintentだけ、実version/candidate/compatibilityはwireへ事前入力しません。

source/entity algorithms v1を維持し、旧wire非依存canonical/context/file ID/invariant helpersだけを再利用します。旧request builder/envelope/runtime gateをv2 admissionへ流用しません。独立validatorはbuilderから期待bytesを再生成せず、actual source/config/role/bytes、trusted/adapter、limit/context、canonical byteとprivate owner stampを直接joinします。

### TDDとhardening

- 初期cycle: builder欠落→closed request、context budget不一致、非canonical targets、偽request ID、別actual source seal、同じheader/profileの別adapter bodyをfocused RED→GREEN。
- generated arrayの100,000 inclusiveとresponse-only aggregate非適用、depth 64 inclusive、UTF-8 key/value string 8 MiB inclusive、実96 MiB stdin inclusive/+1を各missing/wrong behaviorのfocused RED→GREEN。
- mutable stdinの拒否、非string JSON keyの公開error、hash/schema前のgenerated structure capをfocused RED→GREEN。
- 7種のself-consistent再hash mutation（content、membership、compiler option、roles、adapter version、trust digest、limits/context）はrecord整合だけではsource/asset ownerへadmitされません。
- actual disk bytesをseal後に変更しても保持SourceViewだけを使います。projection/caller contextのalias、直接constructor/duck frame、parent-private/actual-runtime追加fieldを拒否します。
- 初回hardeningのoptions/roles fixtureが維持contractに合わず2 tests失敗。`strict`ではなくsupported `jsx`を変更し、role precedenceに対応するeffective roleを更新したself-valid negative fixtureへ修正。製品contractをfixtureに合わせて弱めていません。

### Independent literal

4 source contentsのsize/hash/base64、identity v1 project/file preimagesとproject config、新request全preimageを手作業で構成し、`jq -cjnS`/`shasum -a 256`で独立固定しました。builderをexpected値の計算には使いません。

- project ID `next:project:530b20c858c6039c19737f386f96cfabdadda6b8a0a1c98b5ca639beb2765c25`。
- project config `382ca8954a897ab23fcde46fc2c166ff7f3db5a453165aac875627f281525c05`。
- request ID `364ae1c7150c97541f990bffc4a864ebc405cdf5d0472f3c250434a8f1375197`。
- full-wire SHA `2775c51cb98c3a0c024521007b9c3473c65720ae592597fb9f4c7a9e675ce44f`、3961 bytes、末尾LF無し。
- literal fixture `tests/fixtures/next_runtime_v2/source-sealed-request.json`。ASCII vectorなのでこのknown hashだけでproduction Unicode 15.0.0の全受入れを主張しません。

### Verification

- new focused file: `uv run --locked pytest -q tests/contracts/test_next_request_frame_v2.py --tb=short` → 28 passed（2.03s）。
- `uv run --locked pytest -q tests/contracts/test_next_request_frame_v2.py tests/contracts/test_next_trusted_environment_v2.py tests/contracts/test_next_runtime_v2_contracts.py tests/contracts/test_next_response_frame_v2.py tests/contracts/test_next_process_observation_v2.py tests/contracts/test_json_schemas.py tests/unit/next/test_source_acquisition.py tests/unit/next/test_protocol.py tests/contracts/test_next_contracts.py::test_round23_rg_18_current_schema_and_history_contract_are_explicit` → 388 passed（12.48s）、original session 62359/exit 0。
- `uv run --locked ruff check .` / `ruff format --check .` → pass（192 files）。lint/formatの初期指摘を修正後の結果です。
- `uv run --locked mypy src tests` → pass（161 source files）。target無しの初回CLI呼び出しはexit 2で、型検証の証拠に数えていません。
- この記録を含む`./spec-dock/scripts/spec-dock sync --no-github` / `validate` → pass、nodes=10、active unchanged。generated projectionsは管理外のままです。
- `git diff --check` → pass。

## Options and trade-offs

- 意味/identity algorithmは1、private envelope/representationは2を維持します。旧runtime compatibilityを事前注入する代案は採りません。
- JSON structure limitとactual encoded byte limitを分離します。96 MiB testのpaddingはbyte-bound seamの証拠であり、valid request形状や送信完了ではありません。実incremental stdin/capture/deadline/cleanupは後続A04 acceptanceです。

## Reflection

- Current Design/PlanとReportへ反映します。private request ownerが正常でもpolicy/stdin capture/response echoes/Core model-proof/compatibility/provenance/publicationの全chainは未完了です。
- A03の新固定SHA review pass、production TS/CLI/offline package、実両OSを認定していません。Issue未完了・goal activeを維持します。
