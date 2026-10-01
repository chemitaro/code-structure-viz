---
種別: disc
ID: "20261001t080417z-disc"
タイトル: "a-exchange-compatibility-v2-contract-slice"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-10-01"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: []
reflected_to: []
---

# 20261001t080417z-disc a-exchange-compatibility-v2-contract-slice

採択済みAのprivate transport/parent compatibilityを閉じるdata-only checkpointです。baseはclean/pushed `af8dff8c7846f672f6a9579e00097e998d654042`。production `src`、dependencies、旧v1 schema/producerを変更していません。

## Inputs

- Current R/D/P、accepted A ADR。
- new exchange/compatibility docs、compatibility-v2 schema、small runtime reference/validator、locked semantic profile module。
- `test_next_exchange_v2.py`、independent literal `tests/fixtures/next_runtime_v2/compatibility.json`。
- actual production source sealは既存acquisition経由のfixture。policy/Node version/pid/countersはsynthetic reference evidenceで、OS実測ではありません。

## Synthesis

policy/request/source/assets、prepared stdin/capture、response/request echo、retained raw SHA/control/stdout量、transport admissibilityを全ANDで検証します。単体recordsやfree true checkbox、metadata-only bindingではnormal candidate/compatibilityへ進めません。opaque transport ownerはimmutable frame/bindingを保持し、fresh projectionsを返します。

Core-certified modelではないshape-only payloadを意図的に使っています。model_digest=0×64をtransportから返せても、その値をCoreでadmitしてはいけません。実TS compiler/installed bundleの無いfixtureを製品資材のcoverageに数えません。

### Red→Green / negative evidence

- policy/request join欠落、source-owned limits置換、prepared stdin counts join欠落、response actual request binding、adapter version、trusted/limits/context echoを各public seamでfocused RED→GREEN。
- whole exchange factoryとparent compatibility producer欠落をfocused RED→GREEN。
- stdin/stdout/echoを変えてもshape-valid・transport bool=trueとなるnegativeは、whole owner joinで拒否。
- controlled protocol/unsupported/bootstrap/semantic child failureはfull capture後もsemantic candidate無し。late candidate/assets drift/cleanup未確認はcontrol prefixを維持してraw buffer/candidateを採用しません。
- policy/observation/projectionの後続mutation、constructor/duck response/candidate、再hashした偽trust/portable fingerprint/Unicode table、parent-private追加fieldを拒否。
- request targets/formats/ID、private root、node candidate path、policy digestを変えても同じbindingでcompatibilityが不変なpositiveを実行。
- transport test追加時のfixture helper挿入位置を修復後、missing factoryの意図したREDを改めて実行。fixture組立失敗を受入証拠に数えていません。

### Independent hashes

literal adapter/declaration member集合、bindingのportable preimage、9-field compatibility preimageを主担当が別に組み立て、`jq -cjnS ... | shasum -a 256`で計算しました。new producerでexpectedを導出していません。

- 5-member header/declaration asset ID: `50923cb225647685051b2f46f14fe8fc4adc02b168906595e7ed5a518cd479a7`。
- Node 22.10.0/candidate 2×64のbinding FP: `2654b8357780949c2f53254993c9bcbfd911c2222d3a69b6d1a6e4028330b888`。
- compatibility ID: `0b0d3113311bac4b3788dbd6bb4d643adb181599c7b9e7e7ae7235e382397728`。
- algorithm/ID versionsは1、document identity=semantic/v2、exact identifier/NFC table/KAT、意味profile=1を維持。new binding profileを含むpreimageへ移行し、v1 hashを上書きしません。

### Verification

- focused `uv run --locked pytest -q tests/contracts/test_next_exchange_v2.py --tb=short` → 29 passed（6.93s）。
- runtime-related 6 files selection（compatibility追加前）→ 249 passed（10.73s）、original 79632/exit 0。
- `uv run --locked pytest -q tests/contracts/test_next_exchange_v2.py tests/contracts/test_next_request_frame_v2.py tests/contracts/test_next_trusted_environment_v2.py tests/contracts/test_next_runtime_v2_contracts.py tests/contracts/test_next_response_frame_v2.py tests/contracts/test_next_process_observation_v2.py tests/contracts/test_json_schemas.py tests/unit/next/test_source_acquisition.py tests/unit/next/test_protocol.py tests/contracts/test_next_contracts.py::test_round23_rg_18_current_schema_and_history_contract_are_explicit` → 418 passed（19.52s）、original 70842/exit 0。
- `uv run --locked ruff check .` / `ruff format --check .` → pass（194 files）。
- `uv run --locked mypy src tests` → pass（163 source files）。
- この記録を含む`./spec-dock/scripts/spec-dock sync --no-github` / `validate` → pass、nodes=10、active unchanged。generated projectionsは管理外です。
- `git diff --check` → pass。

## Options and trade-offs

- whole exchangeのdata ownerを明示し、各shape gateを寄せ集めた成功flagをauthorityにしません。ただしPython nominal typeはsame-UID confinementではありません。
- compatibilityはparentがpost-control bindingから生成し、child-authored/free descriptorを許しません。host/source/request stateをportable identityへ含めません。
- old pure semantic metadata/table constantsを維持する一方、old envelope/runtime certificatesと互換viewは使用しません。

## Reflection

- new closed preimage/APIとowner boundaryをCurrent Design/Plan、結果をReportへ反映。
- Core model/proof/target/semantic decision、provenance/run/publication/domain/semantic/root/stdout exact refs、actual OS/TS/CLI/installed package、A03独立Strict gateは未完了。Issue/goalは未完了のままです。
