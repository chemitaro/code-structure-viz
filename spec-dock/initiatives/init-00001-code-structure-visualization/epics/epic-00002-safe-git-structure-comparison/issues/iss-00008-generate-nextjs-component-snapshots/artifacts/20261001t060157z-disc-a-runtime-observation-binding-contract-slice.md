---
種別: disc
ID: "20261001t060157z-disc"
タイトル: "a-runtime-observation-binding-contract-slice"
状態: "recorded"
作成者: "iwasawayuuta"
最終更新: "2026-10-01"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["20261001t024645z-adr-issue8-trusted-toolchain-launch-model.md", "20261001t040605z-disc-issue8-a-runtime-contract-analysis-adjudication.md"]
reflected_to: ["../requirement.md", "../design.md", "../plan.md", "../report.md"]
---

# 20261001t060157z-disc a-runtime-observation-binding-contract-slice

採択済みAのA02-1をdata-only契約として具体化した証拠です。新たなproduct判断、A02全closure、Strict pass、製品のNode/TS/CLI可用性を示しません。

## Inputs

- clean/pushed baseline: `f320d6ae9a7e7cb9ffa6123cd2c3f141ddb4f34b`。前sliceのretained execution assetsから継続。
- 現行Requirement/Design/Plan、accepted ADR、固定SHA Pro助言のローカルadjudication。
- `schemas/next-process-launch-observation-v2.schema.json`、`next-runtime-binding-v1.schema.json`。
- `tests/contracts/next_runtime_v2_reference.py`、`next_runtime_v2_validation.py`、`test_next_runtime_v2_contracts.py`、`test_next_process_observation_v2.py`。
- `tests/fixtures/next_runtime_v2/launch-observation.json`、`runtime-binding.json`。Node候補/trusted/response SHA、PID/capture量はsyntheticであり実測ではない。

## Synthesis

## 閉じたdata contract

policyと同じowner identity、全spawn parameters、new group、actual-spawn無しのnullable suffix、exit/wait、encoded/observed/retained counters、stream cap+1、complete stdoutのcontrol、adapter/request/runtime version/exitを結合します。正常経路はcomplete capture・正常cleanup・両drift unchangedを必要とします。

terminal causeとcleanup結果を分離し、後続cleanup failureでも最初のtimeout causeや既検証controlを消しません。partial stdoutはversion/controlへ昇格せず、terminal transport failureではraw buffersをゼロにします。closed child failureは正常に検証したcontrol frameを持ち得ますがsemantic payload/model/proofを生成しません。

portable bindingはsuccess-onlyで、同じ検証済み観測からversionを取り、候補/資材/header/TS/trusted identityをownerへjoinします。self fingerprintを再hashした別version・別候補・別資材・別trusted identityも拒否します。pure identity projectionに自由versionを渡しただけではadmissionになりません。

## Focused Red → Green

以下はtestが収集・実行され、意図したmissing functionまたは`DID NOT RAISE`のREDを観測後、同selectionを最小変更でGREENにしました。runner/collection failureをREDとは数えていません。

1. observationのclosed owner/policy/control/capture/cleanup基本契約（前contextから継続）。
2. cap超過causeには対応streamのcap+1実測を要求。below-cap labelはRED→GREEN、exact/+1のpositive vectorsも通過。
3. stage/spawn failureにsuccessful spawnを拒否。未起動のwait/group cleanupの偽観測もRED→GREEN。
4. observation由来のruntime binding producerを追加。controlled semantic failureからのbinding生成をRED→GREENで拒否。
5. self-validな別Node versionのbindingをobservation joinで拒否。候補/資材/adapter/trusted identityも同様にRED→GREEN。
6. 実未確認結果無しのcleanup cause、実drift無しのdrift causeを拒否。first-cause保持、後続cleanup未確認、known control保持のpositive vectorsを追加。

## Independent hash vectors

- concrete fixture policy: `jq -cjS . tests/fixtures/next_runtime_v2/launch-policy.json | shasum -a 256` → `abead3e8d882e02139fdfd849988fb3518e4d8f8b2302022699796c53c026448`。
- portable binding: `jq -cjS 'del(.schema,.runtime_toolchain_fingerprint,.adapter.entrypoint_member)' tests/fixtures/next_runtime_v2/runtime-binding.json | shasum -a 256` → `152454270b4314f8f40a6c6902c9116689e3644945f9420d98c237872bcc09a1`。
- policyはconcrete host pathをNFC変換しない。composed/decomposedのactual path spellingを保持し、異なるdigestとするtestを追加。source/semanticのUnicode 15.0.0 NFC profileは不変。

## Verification

- `uv run --locked pytest -q tests/contracts/test_next_runtime_v2_contracts.py tests/contracts/test_next_process_observation_v2.py`: 147 passed（1.68s）。
- 関連回帰: 同2 files、`test_json_schemas.py`、`test_next_contracts.py`を`-k 'not round'`で実行し811 passed / 144 deselected（86.33s）。Round履歴/残る全suiteの代用ではない。
- current正本pointer: `test_round23_rg_18_current_schema_and_history_contract_are_explicit`を明示実行し1 passed。
- `uv run --locked ruff check .`: pass。初回の長いtest名のE501だけを短縮し、same behaviorをfocused再実行。
- `uv run --locked ruff format --check .`: 184 files already formatted。
- `uv run --locked mypy src tests`: no issues / 156 source files。
- SpecDock sync `--no-github`: active Issue 8 unchanged。validate nodes=10 pass。generated projectionsはGit非管理で、このsliceのtracked差分へ加えない。
- `git diff --check`: pass。旧tracked v1 schemas、production `src`、`pyproject.toml`、`uv.lock`の差分無し。

これらはfull A02 closure/全pytest/独立Strict/OS認定ではありません。新schema/referenceとdata fixturesのみのcheckpointであり、A02-2/3/4とA03 gateを省略しません。

## Options and trade-offs

- small independent reference laneを維持し、旧巨大v1 validatorを複製しない。旧schema/algorithmを改変して新方式を認定する代用を避ける。
- data-only shape/self hash/owner joinと、actual raw-frame/OS evidenceを分離する。boolがtrueでもactual response bytesとのjoin前はadmission不可。
- concrete policyとportable bindingのhashを分離する。opaque host pathをsemantic NFCへ通さず、OS間Node binaryの同一hashを約束しない。

## Reflection

- Requirement/Design/Plan current節、`docs/contracts/next-process-launch-v2.md`、新observation/binding contract、thin Reportへ反映。
- A02-2: actual frozen request/response bytes・hash・control projection・capture counters、closed single wire/exit joinsとcompatibility。
- A02-3: retained trusted profileの完全性、source/request/runtime ownerの順序、provenance/public exact-ref closure。
- A02-4全local gateとclean/pushed SHA後にA03 independent Strict。その後だけA04の実OS/TS/CLI実装。
- production/package/dependency/lockfile/legacy v1 schemaは変更しない。既存human HTMLも変更せず、このsliceをvisual acceptanceと主張しない。
