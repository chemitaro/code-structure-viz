---
種別: disc
ID: "20261003t181426z-disc"
タイトル: "SI-06 公開境界の実装経過とroot fingerprint契約の確認点"
状態: "in_progress"
作成者: "iwasawayuuta"
最終更新: "2026-10-04"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["20261003t142223z-adr", "20261003t145358z-01-disc", "20261003t163442z-disc"]
reflected_to: []
---

# 20261003t181426z-disc SI-06 公開境界の実装経過とroot fingerprint契約の確認点

これはreference-onlyの中間実装記録と、未採択の契約確認点です。仕様採択、SI-06 unit認定、Code Review pass、production/Issue完了を意味しません。主担当はユーザー指定のGPT-6 Astra / Max（caller-visible、backend未attested）、サブエージェントは使用していません。

## Inputs

- [現v2限定訂正のaccepted ADR](20261003t142223z-adr-si06-capture-observation-current-v2.md)とCurrent R/D/P、public-v3三契約が正本です。
- [exact26d3ce1の先行Spec Review pass](20261003t145358z-01-disc-si06-capture-spec-review-pass.md)は仕様gateのみです。
- [exactc0a1dd2の改訂Implementation Brief採用](20261003t163442z-disc-si06-capture-brief-adoption.md)とbyte-preserved raw/log/lineageを参照します。
- 元SI-06累積review baseは`af6f5d33f9487a33dabf2ddfe41df85b3d8267fb`のままです。実装中HEADは`c0a1dd2a35326f1656d87ea9a0b907f45a8b123f`、同名upstreamを持つIssue branchです。以下はその上のowned working-tree変更で、まだclean/pushed候補の認定ではありません。

## Synthesis

### 今回実装した限定範囲

`next-publication-decision-v2`のschemaは、adapter capture二fieldにnull/nullまたはobject/objectを許す限定訂正です。wire version/URN、public-stderr/selected-stdoutの実測object、旧schema/lower owner/旧domain/src/依存は変更していません。

catalog-owned diagnostic producerと独立validatorを追加し、actual run/Coreからstage failure、Rejected、SOURCE-003、TARGET、EXPORT、entity budget、complete/partial-safeの診断を導出します。cacheやproducer builderはvalidatorのauthorityにしません。

single final ownerはsame candidates-v3一つだけから、artifact-selector向けstdout、public stderr、実capture pair、response link、descriptor、sealを保持します。semantic failureとpublication failureを分離し、未観測nullと実capture0、実cap+1を区別します。元private response bindingをsealへ保持する意味と、公開response=nullになる条件も分けます。

stderr超過時は元encoded lengthを保持し、public stderrを空、manifest用診断をcatalog LIMIT-003一件にします。selected超過時は元候補の計測値/descriptor、元semantic statusと適格responseを保持し、typed replacementへ分離します。publication-scope LIMIT-003を最終stderrの一回encode前に追加します。

### 実行結果（合算しない）

| selection / 原session | 結果・証明範囲 |
| --- | --- |
| nullable schema family / 8814 | 24 pass。actual stage ownerを使ったshape/negative vectors。final owner全体の認定ではない。 |
| new diagnostics / 40085 | 11 pass、170.59s。actual分類/ref/cache/privacyのfocused証拠。 |
| final owner小規模 / 80158 | 15 pass、2 deselected、356.55s。stage/実0/capture/source/target/export/entity/partial/rejected/64KiB exact/+1。deselected二件は当時並行していた元16805の16MiB exact/+1だけで、後述の同原sessionで完了。aggregateの除外ではない。 |
| actual selected boundary Red / 82296 | 1 pass/1 fail、2266.06s。exact16MiBは全量/独立literal/owner投影pass。+1もactual source/Core/run/candidatesと独立literal一致後、未実装guardで意図したRed。 |
| same selected boundary Green / 16805 | 2 pass、2887.68s。configured16MiB exact/+1がactual v3 owner/literal/元measurement/descriptor/typed replacementでpass。元session完了まで参照ファイルをfreezeし、再実行/除外/UI監視なし。 |
| stage known-answer / 52811 | 1 pass、3.47s。独立measurement digestと12-key boundary seal literalを固定。旧scratch constantの不一致はtest準備の誤りで、productのRedではない。 |
| rehashed native/cache controls / 28980 | 11 pass、40.24s。両seal/cacheを揃えても、同値float/boolのversion/exit/各measurementをactual owner照合で拒否。新product実装なし。 |
| equal-content foreign owner / 11943 | 1 pass、5.05s。別actual source/runtime/run/candidatesの公開recordが同値でも、元final ownerの検証inputとして差し替えを拒否。 |
| resealed null/zero controls / 85956 | 2 pass、6.95s。実capture0のnull化と未観測captureの0埋めを、両seal/cacheが一致しても拒否。 |
| partial-safe final privacy / 75103 | 1 pass、30.59s。公開recordとdecoded stdout/stderr/artifactにprivate proof/source bytes/process keysがないことを確認。catalog許可pathと公開countsは維持。data-only reference scope。 |
| focused final4file statics | mechanical format/import ordering後にRuff/mypy pass。全repo/全testではない。 |
| schema/旧goldens/Current pointer / 73699 | 174 pass、28.16s。schema/exact refs、Python/SQLAlchemy bytes、Current文書指向。all-contract/fullpytestではない。 |
| current static/docs/scope checks | 全repo Ruff pass、format256files、mypy214sources、SpecDock sync --no-github/validate10 nodes、diff-check。元af6fからのsrc/adapters/依存/lower-owner変更は0。 |

大規模fixtureはactual1000 Modules/1003 source-sealed Files/3004 discovered recordsとadapter0.2.0のv3 owner chainを使います。既存raw real-file input helperだけを再利用し、旧Core/run ownerをcastしません。新metadataを独立の十key compatibility、十四key run、三key partition、七key summaryとstdlib codecへ結び、configured16MiB/64KiBの上限は変更していません。上記はreference data-only chainの証拠で、actual TS/compiler/process captureの認定ではありません。producer/validator/大規模fixture/境界test本体はGreen16805完了後も不変です。

stage measurement digestは`55e1176ea7f986b17dd9179ef571767614c50f3fd10dd79a1b08afc092675bef`、12-key boundary sealは`b790e3d366dec43adad1c2ed0926e33d5961f81d699d40423370e3f66a822e27`です。旧scratchの`96942a2d…`は未検証constantとして撤回しました。原46002のliteral自己hash不一致はtest-only準備失敗で、actual owner probe67021と独立worked literalが一致した正しい値へtestだけを修正しています。

追加test-only controls後の中間checkpoint checksは、全repo Ruff check/format256 files、mypy214 sources、SpecDock sync --no-github/validate10 nodes、Current pointer1 pass/0.13s、diff-checkがpassです。六opaque importsのsource bytes一致、二gzipの展開後原bytes/SHA一致、十一local links、probe二SHAとexactc0/originalaf6f lineageを再確認しました。元af6fからのsrc/依存/runtime/Core/run/candidates差分は0です。schema/大規模境界の参照実装は先行pass時点から不変ですが、これをcommit後exact candidateのall-contract/full pytestと混同しません。

### root fingerprintの限定probe

Core無しstage failureのactual run-v3は`context.run_fingerprint=null`です。旧Next root referenceの`root.run.fingerprint = domain.run_fingerprint`を維持してrun blockだけを作ると、現`run-manifest-v2:$defs.run`はfingerprintの`None`をstring typeとして拒否します。再現probe原59716はexit0、唯一のschema errorは`["fingerprint"] / type / None is not of type 'string'`です。

これは未実装root ownerが実際に失敗したという主張ではありません。root/domain/summary/manifestは現在未実装guardで、まだfinal全surface認定へ進めていません。probeのfile-path初回起動はtests import pathの準備失敗（exit1）で、repo cwdのrunpyで実行し直した上記結果だけを採用します。

再現補助は[probe原script](20261003t181631z--si06-root-fingerprint.py)（SHA256 `656ad029f203a9032b7dff453754035ec54d9aa32096e6f0bebb75145fee48c5`）と[JSON出力の記録](20261003t181631z-01--si06-root-fingerprint-result.json)（SHA256 `e55a42624d7ca3f94b590eb5a711eb7b901e8cb16a724c3d8193300270bea45a`）です。generic import後に元Workbenchとのcmp一致を確認しました。JSONは元59716のstdoutを記録したもので、public schema recordではありません。CLIの`committed:true`はfilesystemへのArtifact公開で、Git commitを意味しません。

## Options and trade-offs

確認すべき定義は、semantic run fingerprintとgeneric root request fingerprintが同じものか、別の既存正本を持つかです。

- `docs/contracts/next-run-decision-v2.md:61`のv3継承は、matching transport/Core無しのsemantic fingerprintをnullにし、failure専用hash/fake bindingを禁止します。
- `docs/contracts/next-semantic-v3.md:31-35`は十四keyのsemantic familyを固定します。
- `next-domain-manifest-v2.run_fingerprint`はdigest/null、`next-config-v1.snapshot_request.run_fingerprint`はoptional digestです。未認定時のoptional request field省略と、root必須digestは同じ問題ではありません。
- 旧Next root producer/validatorはrootとdomainのfingerprint equalityを要求します。一方、generic coreの`docs/contracts/run-manifest-v1.md:19` / `src/code_structure_viz/artifacts/manifest.py:_run_fingerprint`には七keyの`run-fingerprint/v1`が存在します。

generic七keyを新Next rootへ適用できる根拠が既にあるのか、別meaningの採択が必要なのかはまだ確定していません。仮に変更が必要なら、Next-only nullable root、root request identityの明示分離、Core無しmanifest抑止等はそれぞれschema/consumer/Productに異なる影響があります。どれも現在の採択済み案として扱いません。便宜的なfailure hash、未観測値補完、lower owner guard緩和、旧Python/SQLAlchemy変更は実施しません。

## Reflection

Current R/D/Pやaccepted ADRのmeaningを、このArtifactだけで変更しません。現在のartifact-boundary TDDを閉じた後、rootのauthority/consumer joinsを確認し、必要な場合はclean/pushedのcoherent checkpointに対するStrict advisoryで選択肢と人間判断の境界を具体化します。

先行schema/boundary selectionと最新の中間checkpoint checksは上記の別々の証拠です。全contract/full pytest、全selector/domain/root owner、privacy等の残るcontrols、元af6fからのfresh cumulative Code Review Strictは未完了です。SI-07/SI-08、reader-prefix/ASSET、actual TS/OS/CLI/package、Final Quality Gate、Issue全体の完了は主張しません。
