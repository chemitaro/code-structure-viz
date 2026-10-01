# Next.js execution assets identity v1

## 何を証明するrecordか

`code-structure-viz.next-execution-assets/v1`は、保持した実行資材bytesのportable content identityです。新conceptの最初の版であり、旧reference/build inventoryを改名したものではありません。host path、device/inode、PID/FD、source checkout pathは含めません。

このleafだけでは、TypeScript version、trusted declarationの意味profile、locked member全集合、wheel/sdist収録、実spawn、製品availabilityを証明しません。それらはそれぞれ対応するprofile/build/runtime gateへjoinします。現在のreference fixtureはsyntheticな2 memberで、実TypeScript libraryやcomplete package profileではありません。

## closed fieldsとpreimage

- `schema`: 上記の固定identity。
- `entrypoint_member`: `code_structure_viz/_next_runtime/next-adapter.mjs`。保持member内にrole `adapter`として必ず存在します。
- `members`: `package_path`, `role`, `size_bytes`, `sha256`だけを持つrows。package pathのUTF-8 bytes順で、pathは重複不可です。
- `asset_set_id`: 下記preimageのSHA-256、lowercase 64 hexです。

package pathは`code_structure_viz/_next_runtime/`内のrelative POSIX pathです。ASCII lowercase/digit/`.`/`_`/`-`のcomponentを使い、空component、`.`、`..`、absolute path、backslash、control、trailing LFを拒否します。entrypointとpackage名の既存underscoreは維持します。

preimageは`asset_set_id`自身を除いたrecord全体です。object keysをsortし、UTF-8、空白無し、`ensure_ascii=false`、非finite number無しでencodeします。member順は上の規則で固定し、**digest入力には末尾LFを付けません**。JSON wire/documentの末尾LFとは別です。全fieldがASCII path/定数/hexとintegerなので、このleafにhost Unicode databaseは関与しません。

roleは`adapter`、`typescript_lib`、`trusted_declaration`です。license/noticeは実行意味を変えないためこの集合から除き、出荷の`next-runtime-build-inventory/v1`には必ず別途収録・検証します。licenseを不要とした判断ではありません。

## 同一bytes ownerと検証の二層

referenceの`retain_execution_assets_v1`は既読のimmutable bytesを一つのsnapshotへ保持します。mutableなcaller mappingの後続変更、返したdescriptorの変更はownerへ影響しません。filenameからの後続再read、自由なcaller version/hash、byte以外からの暗黙変換は使いません。

ownerの`descriptor()`、`adapter_identity()`、`staging_members()`は同じsnapshotから導出します。header versionはentrypointの先頭に一度だけ現れるASCII stable semver markerで、BOM/CRLF/重複/prerelease/build metadata等の旧採択済み拒否規則を保持します。protocolはpolicy schemaと同じ`code-structure-viz.next-adapter/v2`です。

`validate_execution_asset_identity_v1`はclosed shape、順序、pathの重複、entrypointのrole、self digestを検証します。これはmetadataの自己整合性だけです。`validate_execution_assets_v1`はさらにretained ownerの実bytes由来descriptorと完全一致を要求します。改変metadataを再hashしても、このbyte joinを通りません。

`validate_launch_policy_assets_v2`はpolicyのasset IDとadapter identityを同じownerへjoinします。この部分検証だけでrequest、trusted profile、candidate drift、observation、complete runtime profileをadmitしません。productionの実行Module内ではこれらをすべて検証し、callerへretention/staging/spawnの順序を公開しません。

## 独立worked vector

fixture `tests/fixtures/next_runtime_v2/execution-assets.json`の入力は以下だけです。

```text
next-adapter.mjs: // CodeStructureViz-Adapter-Version: 0.1.0\n
  43 bytes / a0a769eddee8f677bcabbf0b1884c32c509c8b7ebccd9f41cf3473a5f67a57b4
typescript/typescript.cjs: reference compiler\n
  19 bytes / 4b507a55c78e8cab287c0c8385ad7e3c72acabd93dc616d9fda9aa98883a17b6
asset_set_id:
  516ab8709db31afdb0b1906a14b9aff17d8106e6827674f3b453660ec0d9c856
```

期待値はproducerによる再計算ではなく、literal bytesとkey-sorted literal preimageを`shasum -a256`で独立に計算した値です。この2 memberを出荷profileや実compilerとして使いません。
