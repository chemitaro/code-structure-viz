---
種別: disc
ID: "20261001t094029z-disc"
タイトル: "a-runtime-result-provenance-v2-contract-slice"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-10-01"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["requirement.md", "design.md", "plan.md", "20261001t040546z--a-runtime-contract-analysis-result.md"]
reflected_to: ["design.md", "plan.md", "report.md"]
---

# 20261001t094029z-disc a-runtime-result-provenance-v2-contract-slice

採択済みAのA02 runtime-result / provenance契約スライスです。referenceデータのowner/値の整合を検証し、production起動・実TS・Issue完了やA03レビューpassを証明しません。

## Inputs

- 開始checkpoint: clean/pushed `7bf1a8f72bcd3e9e7b5e9921f99a7a0ffee4b02d`。A02契約baseは`710eb49a2a3143e31b8a91580700d16839d9070d`、累積Strictのユーザー指定固定点は`f4159066f3954454ad2f0c2701fa54bf1bc7bc4a`のままです。
- 正本: Requirement/Design/PlanのCurrent authority、accepted A ADR。Pro助言のfailure prefix / portable-host-local分離を、実schemaと保持ownerへ照合しました。
- 変更: small v2 reference lane、runtime-result/provenance tests、新provenance-v2 schemaと契約文書。旧v1、production `src/`、依存・lockfile・出荷runtime資材は変更しません。

## Synthesis

- `RetainedRuntimeResultV2`は同じactual source seal/retained assets/request/policy/observation/frameをjoinします。成功時だけtransport candidateを保持し、closed child failureとtransport failureではcontrol/byte descriptorだけを保持します。failure raw bufferやprivate proofを公開しません。
- v2 response descriptorは元bytesのSHA/lengthとcanonical JSON一致flagです。whitespace/LFを許可したframeのflagを常にtrueにせず、reserializeしたSHAへ置き換えません。
- `request_bound`は親がvalidated requestを保持する意味です。child protocol failureのunbound echoを、親requestの観測無しに読み替えません。foreign child bindingを修正せず、そのままfailure prefixへ残します。
- provenanceは17 named slotsの実値から生成します。readonly trusted metadataは期待宣言profileであり、未観測のTS import成功ではありません。control前のfailureにversion/semantic/compatibility/model/budgetを補完しません。late cleanup/driftで既検証version/controlを消しません。
- portable launch/process-start projectionはabsolute Node/private path、platform、policy digest、PID/PGIDを除きます。実Popen parametersとexpected compiler metadataを別にします。候補content hashをactual-image attestationとは呼びません。
- Core ownerのtarget failureはfailure provenanceにし、未実測entity budgetはunobserved/nullです。referenceのknown corpus以外の実解析を認定しません。

## Options and trade-offs

- 採択済みの実値owner由来projectionを実装します。stage名だけのprefix推測、boolean/free status入力、旧v1互換view、failureへの成功suffix補完は不採用です。
- field digest preimageはversioned observation wrapper＋closed slot name＋actual portable valueです。単なるfield-name markerやmutable aliasを観測証拠にしません。hash-only公開とhost-local保持を分離します。
- 独立ASCII KAT: `node_candidate` observation `49629589791b75238da6a7744ddb40b19386eb9482a8e05a90a2bf2717870def`、`process_start` observation `3869aabc86551c31c55fca1229360dc3efe591ab6449bb33dc465a3b8bf6b5d4`。fixed fixtureと手で組んだprojectionを`jq -cSj | shasum -a 256`で計算し、reference producerをexpected生成に使いません。

## TDD / verification

- runtime-result API欠落→unsupported child result、success candidate無し→same-exchange candidate、timeoutのNone frame拒否→観測無しbranch、foreign bindingの一律拒否→failure-only保持、fake mismatch label許容→実foreign binding必須、をそれぞれfocused RED→GREENで検証しました。runtime-result全15 tests pass。
- provenance API欠落、Core owner引数欠落、v2 schema validator欠落、timeout/late failure branch欠落、target failureのsuccess誤分類、process-startへのexpected compiler metadata混入をfocused REDで観測し、各最小変更でGREENを確認しました。
- 全hashが正しくてもsuccessを偽LIMIT-005 failureへ書き換えられたREDに対し、actual runtime/Core ownerからkind/stage/codeを再導出して拒否するGREENを確認。別exchangeのCore、duck owner、17 rowsそれぞれのschema-valid hash改変、legacy identity/slots/version、fabricated unsupported suffixも拒否します。
- runtime-result 15 / provenance 33の新focused48 testsは26.46sでpass。format/type修正後のruntime/旧schema/source/request関連selectionは465 passed（47.71s）、original job exit0を回収し、quiet jobを重複実行していません。
- Ruff check全対象、format check（201 files）、mypy（166 source files）、SpecDock sync（active iss-00008不変）/validate（nodes=10）、Current doc-pointer（1 passed）、diff-checkがpass。SpecDockの初回helpは誤った`spec-dock.py` pathでexit2になり、現物の`spec-dock`へ修正してroot/leaf helpを読んでから正常実行しました。
- 上記はこのsliceの終端検証です。全A02/全suite/actual OS/TS/A03 gateは未完了です。checkpointは通常のstaging/staged diff確認/`commit-codex -a`/pushで作成し、SHAとclean upstream一致は次のsliceのInputsへ保存します。

## Reflection

- 詳細契約と最新実測をCurrent Design/Plan/薄いReportへ反映します。
- 継続gate: request-independent reader-owned phase prefix、invalid Core/record-limit failure union、readonly source-phase sequence、run/publication/domain/semantic/root/stdout exact refs、全A02 negative/full gates。A03はwhole A02のclean/pushed exact SHAに対して独立Strict reviewを行い、valid passまでA04へ進みません。
