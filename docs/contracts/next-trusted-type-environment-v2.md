# Next.js trusted environment manifest / descriptor v2

## 新identityと維持する意味

manifestは`code-structure-viz.next-trusted-type-environment-manifest/v2`、小さいdescriptorは`code-structure-viz.next-trusted-types/v2`です。descriptorの`environment_version="2"`はこの表現・digest契約の版であり、宣言の意味を変えたという意味ではありません。`semantic_profile_id="next-trusted-profile-v1"`、TypeScript 5.9.2、Unicode 15.0.0、4 declaration / 14 certified symbols、reserved names、signature digestsは維持します。

旧v1のmanifest/hashはfixture `physical_path`を含む旧identityのまま保存します。新hashを旧descriptor/v1へ代入せず、旧schemaを緩めません。v2 manifestの各fileはclosedな`package_path / virtual_path / size_bytes / sha256 / license_id`だけです。host absolute path、fixture path、private staging pathを認証identityへ含めません。

package mappingは`code_structure_viz/_next_runtime/trusted/{jsx-runtime,lib,next-dynamic,react}.d.ts`、virtual mappingは既存`/.code-structure-viz/trusted/v1/<basename>`です。4 fileはvirtual pathの固定順、すべてexecution assets内の`trusted_declaration` roleです。余分な同roleのfile、欠落、role差替え、mapping swap、同pathの別rowを拒否します。`lib.d.ts`も既存の小さいtrusted declarationであり、実TypeScript compilerや全standard libsを収録・検証したという意味ではありません。

## 二つの明示preimage

両方ともsort_keys、compact、UTF-8、ensure_ascii=false、非finite number無し、**末尾LF無し**です。ここで許すpath/name/metadataはfixed ASCIIであり、host Unicode databaseへ依存しません。source/semantic v1のUnicode 15.0.0 NFC codecは変更しません。

1. `environment_descriptor.sha256`はlogical declaration profileのidentity。preimageはdescriptorの`schema / environment_version / semantic_profile_id`（sha自身は除外）、manifestのTS version、identifier table digest、profile license metadata digest、reserved names、certified symbols、anti-shadowing witness、**package_pathを除いたfiles**です。package/hostの配置を意味identityへ入れません。
2. `manifest_sha256`はprofile identityとfixed package mappingのidentity。preimageは`manifest_sha256`自身を除いたmanifest全体です。descriptorのhashとpackage pathsを含み、循環参照はありません。

legacy profileの`license_inventory_digest`と各fileのlicense IDは固定metadataとして維持します。これは実license files/noticesやwheel/sdistの出荷証拠ではありません。それらは独立したbuild/package inventoryとA05で必須検証します。実行assets leafがlicenseを含めない規則も変えません。

## retained ownerとreadonly metadata

`retain_execution_assets_v1`だけが通常Interfaceでimmutable asset ownerを生成します。constructorやduck-typed metadata ownerを認証入力にしません。trusted Python実行環境そのものへの敵対改変を防ぐsecurity boundaryではありません。

`trusted_environment_manifest_v2(owner)`は同じ保持bytesからfresh metadataを導出し、資材のresource再lookup/re-readやNode起動をしません。locked literalの各declaration size/hashと全metadataへ照合し、unknown bytesにv1 certified symbolsを発行しません。descriptor/header/stagingも同じasset ownerへ結合します。reference validatorが読むchecked-in JSON Schemaはテストの契約検証であり、実行資材の再取得とは区別します。

`validate_trusted_environment_manifest_shape_v2`はshapeだけです。`validate_trusted_environment_manifest_v2`は固定profile、両preimage、role集合、全memberの保持bytesを結合します。改変したmetadataを再hashしても固定profile/ownerとの不一致を拒否します。returned dictを変更してもownerや次のfresh projectionは変わりません。

`validate_source_seal_trusted_v2`は既存の実`SourceAcquisitionSeal`の整合性とsource-plan/v1 shapeを検証し、planのopaque trusted digestを同じownerのdescriptorへ結合します。`validate_launch_policy_trusted_v2`は既存asset/adapter joinに加えてpolicyのtrusted digestをそのdescriptorへ結合します。どちらもNode観測、実TS version、childの宣言利用、実spawn、semantic proofの認定ではありません。

## source-phase順序

productionの順序は次です。これはA04の実装・実測条件であり、このreference metadata sliceだけで実行順序を認定しません。

```text
package-only applicability permission
  -> applicableの場合だけ実行Moduleがpackage資材を一度保持
  -> 同じModuleのreadonly trusted descriptorをCoreへ渡す
  -> Coreが同じreader-owned package/control snapshotからsource sealを生成
  -> execute(seal, analysis intent, explicit runtime selection)
     が同じ保持ownerでrequest / staging / spawn / cleanupを所有
```

all-non-applicableでは資材保持・config/source・Node観測を開始しません。callerへprepare/open/stage/closeを公開せず、seal後にbundleを読み直しません。起動前descriptorは期待する宣言profileのmetadataであり、childが実際に利用したruntime/TS/宣言の観測と混同しません。後続のrequest/stdin、response echo、compatibility/provenanceのjoinsでこの区別を維持します。

## independent known answerと限界

変更していない4 checked-in declarationのbytes、`expected_inventory.json`の14 symbols、fixed metadataを独立した`jq -cjnS`のlogical/package preimagesへ投影し、`shasum -a 256`で確認しました。producerから期待hashを生成していません。

```text
logical descriptor sha256
49458cb6f0f5097d486a2e4f7691f3f80d1e62ea4dbc65ceff00b862ce84e366
package mapping manifest_sha256
a23265240ebcfa3ba6670f6b0f4982eb96025be093a19ea9b1d74561d32ac31f
```

現在はdata-only reference契約です。fixtureにはsynthetic adapter headerと4 declarationだけを使い、実TS compilerを実行していません。製品のinstalled resource retention、source-phase coordinator、request/response/Core proof/compatibility/public closure、両OS CLI、offline package/license、独立Strict gateは別の必須受入れです。
