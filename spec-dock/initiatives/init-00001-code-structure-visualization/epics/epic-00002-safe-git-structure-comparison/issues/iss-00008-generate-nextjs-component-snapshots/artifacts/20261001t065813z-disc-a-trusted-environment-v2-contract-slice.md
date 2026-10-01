---
種別: disc
ID: "20261001t065813z-disc"
タイトル: "a-trusted-environment-v2-contract-slice"
状態: "final"
作成者: "iwasawayuuta"
最終更新: "2026-10-01"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["20261001t040605z-disc-issue8-a-runtime-contract-analysis-adjudication.md", "20261001t062630z-disc-a-response-frame-v2-contract-slice.md"]
reflected_to: ["design.md", "plan.md", "report.md"]
---

# 20261001t065813z-disc a-trusted-environment-v2-contract-slice

採択済みA02のtrusted manifest/descriptorとretained bytesの部分契約を具体化した証拠です。production runtime、shipping package、独立Strict pass、Issue完了の認定ではありません。

## Inputs

- 開始時clean/pushed SHA `0c5135331f7f6de9bd7ab9390df71a1e25083bb5`、branch `iss-00008-generate-nextjs-component-snapshots`。HEAD/upstream full SHA一致を確認しました。
- 旧`next-trusted-type-environment-v1` schema、既存4 declarationと`expected_inventory.json`、v1 producer/validatorを参照し、保存済みv1を変更していません。
- Current Design/Plan、accepted AとGPT-5.6 Sol / Pro advisoryのlocal adjudicationを入力とします。今回は新しい外部analysis/reviewやサブエージェントを実行していません。

## Synthesis

- 新manifest `code-structure-viz.next-trusted-type-environment-manifest/v2`とdescriptor `code-structure-viz.next-trusted-types/v2`をclosed schemaにしました。`environment_version=2`は表現/digest契約の版、意味profile=1と14 symbolsは不変です。
- logical environment preimageからpackage pathを除外し、別manifest hashへfixed package mappingとdescriptor hashを含めます。host/fixture/private-root pathsを含めず、旧v1のfull-manifest hashを別preimageで再計算しません。
- 保持資材の4 declaration、size/hash、role全集合とlocked metadataを照合し、unknown bytesへ既存certificationを発行しません。constructor/duck metadata ownerを通常Interfaceで拒否し、mutable caller mapping/fresh projectionからのaliasをなくします。
- `validate_source_seal_trusted_v2`は既存production source acquisitionを実際に用いて得たsealのopaque digestへjoinし、`validate_launch_policy_trusted_v2`は同じownerへpolicyをjoinします。source seal自体をcallerが組み立てたり後から書き換えたりしていません。Nodeは起動していません。
- reference fixtureはsynthetic adapter header＋4既存declarationのみです。TS version文字列/metadataだけで実compiler、full lib、installed package、childの利用、OS順序を認定しません。

## Independent known answers

4 bytesを`wc -c / shasum -a 256`で確認しました。順序はjsx-runtime/lib/next-dynamic/react、sizeは206/291/101/306、hashは新reference lockのliteralです。14 symbol rowsは既存inventoryに照合します。

key-sorted compact JSONは`jq -cjnS --slurpfile inventory tests/fixtures/next_trusted_profile/expected_inventory.json`で、file size/hashをliteral入力し、inventoryを`source_kind/source_name/export_path`順に投影しました。logical preimageには新schema/version/profile、TS 5.9.2、Unicode table digest `c9336daa555ce98e93cbd48e6b91df22f50a221881bd10b3ed79cf9180297969`、旧profile license metadata digest、reserved names、symbol/declaration bindings、witness、package_path無しfilesを含めます。これを直接`shasum -a 256`へ渡した結果です。

- logical descriptor: `49458cb6f0f5097d486a2e4f7691f3f80d1e62ea4dbc65ceff00b862ce84e366`。
- 上記hashをdescriptorへ入れ、fixed package mappingを含むmanifest全体（manifest_sha256自身は除外）を別jq preimageとして計測: `a23265240ebcfa3ba6670f6b0f4982eb96025be093a19ea9b1d74561d32ac31f`。
- 両方とも末尾LF無しです。期待hashをproducerで作らず、literal known answersとしてtestへ固定しました。manifest/profileのlicense metadataは実license file/noticesの出荷証拠ではありません。

## Focused Red → Green

1. metadata producer欠落をAttributeErrorでRED。新closed manifest/projectionを追加して同じselectionをGREEN。
2. changed declarationが通るRED、missing declarationがKeyErrorになるREDを観測。locked byte hash/sizeと明示missing errorでGREEN。
3. wrong role / extra declarationが通るREDを観測。exact declaration role集合でGREEN。
4. validator欠落をRED。profile/retained owner joinを追加してGREEN。
5. logical/manifest digest改変が通るREDを観測。別preimage検証でGREEN。
6. metadata改変を両hashで修復しても通る5 REDを観測。locked metadata比較でGREEN。
7. duck ownerと直接asset constructorが通るREDを観測。通常factory/type owner契約でGREEN。trusted Python自体への攻撃防止とは主張しません。
8. policy / actual source sealへのjoin欠落をRED。owner descriptor一致を追加して同じpositive/negative selectionsをGREEN。

known answers、v1 symbol inventory一致、fresh projection、legacy/host field拒否、再hashしたmapping swap/order/duplicate/license、別bytes ownerのnegative vectorsも追加しました。

## Options and trade-offs

- 採用: 同一immutable asset ownerからreadonly metadataを導出し、source sealとpolicyへjoinする。logical意味identityとpackage mapping identityを分離し、旧profileの意味と旧v1履歴を維持します。
- 不採用: fixture physical pathのproduction扱い、v1 descriptor/hashのsilent rewrite、free-form caller trusted stringsの採用、metadata resolver後の資材再read、実runtime観測のsynthetic生成。
- 限界: reference validatorのJSON Schema読込はtest契約の検証です。実行資材の再readではありません。shipping licenses/full TypeScript、production source-phase coordinator、request/response/proof/compatibility/public closureは残ります。

## Reflection

- Designにreadonly source-phase順序と二つのidentityを記述し、Planのtrusted data sliceをGREEN、後続request/provenance/public/productionを未完了へ分離しました。
- 4つの新runtime test filesの関連selectionは199 passed（3.07s）。source/旧request regressionと既存schema/doc pointerを合わせた最終selectionは359 passed（11.46s）。下記コマンドを実行し、collection失敗やzero selectionではないことを確認しました。
- `uv run --locked pytest -q tests/contracts/test_next_trusted_environment_v2.py tests/contracts/test_next_runtime_v2_contracts.py tests/contracts/test_next_response_frame_v2.py tests/contracts/test_next_process_observation_v2.py tests/contracts/test_json_schemas.py tests/unit/next/test_source_acquisition.py tests/unit/next/test_protocol.py tests/contracts/test_next_contracts.py::test_round23_rg_18_current_schema_and_history_contract_are_explicit`。
- 最終Ruff check / format（190 files）、mypy（160 source files）、SpecDock sync --no-github / validate（nodes=10）、diff-checkはpass。初回RuffのTYPE_CHECKING import間の空行I001を削除し、final checkでGREENへ修復しました。
- 全pytestの再実行とfresh exact-SHA StrictはA02全closure後に実行します。この359 passや保存済み旧v1のStrictをA03認定へ読み替えません。
- `src`、依存、lockfile、旧v1 schemas/reference、HTML/PlantUMLは変更しません。A03を通すまで新production runtimeへ接続しません。
