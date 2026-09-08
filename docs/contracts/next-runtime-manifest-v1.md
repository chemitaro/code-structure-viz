# Next.js runtime inventoryと実行manifestの分離

## 三つの用途

Issue #8 の実装前契約です。「runtime manifest」の語で実行結果と同梱ファイル一覧を兼用しません。
この文書のパスは既存リンクを維持していますが、正規schema名は次のとおりです。

| 用途 | schema / 正本 | 証明するもの |
| --- | --- | --- |
| 実行結果 | run-manifest-v1、next-domain-manifest-v1、next-run-decision-v1、next-publication-decision-v1 | その実行の観測、意味判定、公開bytes、診断、終了code |
| 参照fixtureのinventory | next-reference-runtime-inventory-v1 | チェックイン済み4ファイルとそのmapping、内容hash、license |
| 将来の製品build inventory | next-runtime-build-inventory-v1 | 配布物に入れるruntime resourceのexact setとbuild入力/出力hash |

旧next-runtime-manifest-v1.schema.jsonは用途が曖昧なため廃止し、後二者へ分離しました。
名前変更はfixtureを製品runtimeに昇格させるものではありません。現時点で製品adapter、wheel/sdistの変更は行いません。

## 参照fixture inventory

next-reference-runtime-inventory/v1は4件のexact setです。

| 実在するfixture | 参照上のvirtual path | role |
| --- | --- | --- |
| tests/fixtures/next_runtime/adapter.js | src/code_structure_viz/_next_runtime/adapter.js | adapter |
| tests/fixtures/next_runtime/manifest.json | src/code_structure_viz/_next_runtime/manifest.json | manifest |
| tests/fixtures/next_runtime/trusted.d.ts | src/code_structure_viz/_next_runtime/trusted.d.ts | trusted_declaration |
| tests/fixtures/next_runtime/typescript-lib.d.ts | src/code_structure_viz/_next_runtime/typescript-lib.d.ts | typescript_lib |

virtual pathはfixtureの対応関係であり、実wheelのmember名ではありません。
実filesのUTF-8 bytes、size、SHA-256と各rowを一致させ、追加・欠落・重複・role変更・path変更を拒否します。
trusted semantic profileの4宣言ファイル/認証symbol集合は別のinventoryです。上表の小さなtrusted.d.tsをその代用にしません。

membersはpath順、licensesはecosystem/name/version/license_id順です。
licenseはTypeScript 5.9.2のApache-2.0とCodeStructureViz trusted-typesのMITの2件を閉じた集合として検証します。

```text
build_input_digest  = SHA256(canonical-json({members, licenses}))
build_output_digest = SHA256(canonical-json({members}))
inventory_attestation.sha256 = SHA256(canonical-json({members}))
manifest_sha256 = SHA256(canonical-json(inventory without manifest_sha256))
```

attestation.membersはmembersのexact copyです。自己hashをそのpreimageに含めず、循環を作りません。
テスト上のvalidate_runtime_manifestという旧helper名は、この参照inventoryだけを検証します。

## 将来の製品build inventory

next-runtime-build-inventory/v1は、製品resourceを実装した段階でbuild ownerが生成します。
現在のschemaはその形式を定めるものであり、製品ファイルが存在・同梱済みという証拠ではありません。

- membersはsource_kind、source_path、package_path、size_bytes、sha256、roleを持つ。
- source_pathはbuild入力のrepository-relative path。package_pathはwheel内の配布相対pathで、src/ layout prefixと区別する。
- adapter、固定TypeScript資材、trusted declarations、license資材を含むexact resource setをinventory_versionごとに定義する。
- path traversal、絶対path、symlink逃逸、重複正規化pathを拒否する。各roleとsource_kindは対応させる。
- source bytes、build output bytes、archiveから読んだbytesのsize/hashを照合する。hashを記したJSONだけで同梱を証明しない。
- inventory自身とarchiveのRECORD等の自己参照的metadataをresource setから分離する。archive全体を相互hashする循環を作らない。

将来実装の受入は次の順序で行います。

1. versioned build recipeとlocked inputsから、期待するruntime resourceのexact member setを作る。
2. clean buildでwheelとsdistを生成する。現在のpyprojectを仕様作成だけのために変更しない。
3. wheelのcode_structure_viz/_next_runtime/配下を列挙し、期待集合との完全一致・内容hash・licenseを検証する。
4. sdistは配布名/versionの単一rootを確認してから相対化し、同じ資材対応を検証する。sdist由来の再buildでも同じruntime bytesを得る。
5. missing/extra/duplicate/traversal/hash/role/licenseのmutationを一つずつ失敗させる。
6. インストール先でpackage resourcesから資材を取得し、target側のnode_modules・config・scriptに依存しない実行を受け入れる。

参照4ファイル検査がgreenでも、この製品package gateをpassにしません。
member setを変更するときはinventory versionと既知値・migration・compatibility影響を同時に更新します。

## 実行時の関係

製品build inventoryのadapter content identityは起動前policyの入力になります。
型環境は自身の完全digest、Nodeはhostの検証済み実体identityを持ちます。
それぞれを [next-process-launch-v1.md](next-process-launch-v1.md) と [next-compatibility-v1.md](next-compatibility-v1.md) の境界で結合します。

run manifestはその実行のsealed decisionを投影するだけです。inventoryから未観測のrequest、Node起動、応答成功を合成しません。
未観測段階のnull、partial-safe、公開失敗の扱いはprovenance/publication契約が所有します。

過去Roundのレビュー経緯はGit履歴およびIssue artifactsへ移しました。現在の判定は最終固定SHAレビュー前であり、実装着手可能との認定はまだありません。
