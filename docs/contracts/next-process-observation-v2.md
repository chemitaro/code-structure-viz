# Next.js public-spawn process observation v2

## 記録するもの・しないもの

`code-structure-viz.next-process-launch-observation/v2`は起動後のhost-local recordです。[policy v2](next-process-launch-v2.md)と同じproducer/platform/requestを持ち、concrete policyのdigestへjoinします。reference/fixtureとproduction/darwin・linuxを区別します。schemaにproductionがあることやreference fixtureのpassは実OS認定ではありません。

spawn、capture、exit、closed control response、観測可能なcandidate/asset drift、cleanupと最初のterminal causeを記録します。semantic model/proof/target completeness、verified handle、actual-image digestをこのrecordに追加しません。

## Host-local policy digest

policy object全体をkey-sort・compact・UTF-8 JSON（`ensure_ascii=false`、非有限数禁止、末尾LF無し）にしてSHA-256を取ります。**host pathはopaqueな実引数としてそのまま保持し、NFC正規化しません。** composed/decomposedの綴りは同じ意味pathと推測せず、異なるpolicy digestになります。既存source/semanticのUnicode 15.0.0 NFC codecを変更するものではありません。

portable [runtime binding](next-runtime-binding-v1.md)は別preimageです。policy digest、private path、PID/PGIDをsemantic fingerprintへ流しません。

## 観測prefixとcleanup

- `spawn=null`ならcapture/exit/responseもnullです。未起動の子をwaitしたりgroupへsignalしたりした記録を拒否します。stage/spawn failureにsuccessful spawnを付けません。
- write/read/cap/timeout/frame/response/binding/exit mismatchという起動後のcauseには実spawn/captureを要求します。capture/responseが無い状態へ起動後のcause名だけを付けません。
- actual spawnのparametersはpolicyのargv/shell/cwd/passed env/stdio/FD/groupと全量一致し、new sessionのleader PIDとPGIDが一致します。passed envとNode内部env、継承FDと内部FDは別です。
- `capture`はencoded stdin、送信済みstdin、読み取ったstdout/stderr、現在保持しているraw bytes、EOFを分離します。観測・encode量より大きい保持/送信量を拒否します。
- 各captureはcap+1までのbounded measurementです。exact capは上限内、named `stdout_limit`/`stderr_limit`は対応streamのcap+1実測を必要とします。childが将来出力し得る総量ではありません。
- control observationは全stdoutのEOFとcapture cap内を必要とします。partial stdoutからversion/controlを推測しません。既検証control/hashは後続failureでも保持可能ですが、全raw stdout/stderr bufferは破棄します。
- direct child waitは実exit statusの有無と一致します。normal terminalではgroup signalを使わず、wait済み・全pipes/candidate閉鎖・private root除去確認・complete capture・両drift checkの`unchanged`を必要とします。
- cleanup booleanはownerが確認したresource postconditionです。未作成resourceがあれば残存無しを確認し、close/removeを実行したという証拠を捏造しません。`direct_child_waited`だけは実waitを表し、未起動ではfalseです。
- named cleanup/drift causeには実際の対応する未確認/drift結果を必要とします。最初のterminal causeと後続cleanup結果は別であり、timeoutを後のcleanup failureで置き換えません。実時系列の所有権はproduction ownerの受入れで検証します。

Darwin EPERMを成功へ読み替えず、group terminationやprivate資材除去を確認できなければpayloadを抑止します。normal reap後に古いPGIDへsignalしません。任意hostile same-UIDやhard RSS隔離は保証しません。

## Closed child control

bindingは`unbound/null`または`bound/request_id`のclosed unionです。runtimeは未観測ならnull、観測済みならraw version・canonical stable versionまたはnull・eligibility・`process.versions.node`を保持します。raw/canonical/eligibilityの不一致や別probe sourceを拒否します。

| child result_kind | 正常対応exit | control条件 | semantic payload |
| --- | --- | --- | --- |
| `success` | 0 | bound・supported runtime | 後続wireに必要。Coreが独立検証。 |
| `protocol_failure` | 65 | unbound。未検証request IDをechoしない。 | 無し |
| `unsupported_runtime` | 66 | bound・unsupported/invalid runtime | 無し。TS import前に拒否。 |
| `bootstrap_failure` | 67 | 実際のbound/unbound・runtime/null prefix | 無し |
| `semantic_failure` | 68 | bound・supported runtime | 無し。catastrophic failure専用。 |

request binding/adapter versionとpolicyのjoin、正常controlと実exitの対応を検証します。normal transportのchild `success`は、semantic completeを意味しません。partial-safe/target failureはpayloadをCoreが判定します。

named `exit_mismatch`はcomplete controlとactual exitを必要とし、表の対応exitと実際に異なる場合だけ保持します。正常exitをmismatchへ書き換えません。`response_invalid`はretained complete frameの実request echo違反、`binding_mismatch`はactual foreign child bindingを必要とします。frame-invalidは別のdecoder-owned rejected byte ownerへjoinし、未検証controlを生成しません。捕捉interruptはordinary Next provenance/publicationから除外し、core interrupted/exit130のterminal routeへ渡します。

## Transport gateと未完了のjoin

`transport_payload_admissible`はnormal cause、success/bound/同一request/supported control、exit 0、complete capture、正常cleanup、両drift unchangedのANDです。各cross-field validatorが成立した後のdata predicateであり、schemaだけやhelperのboolだけでadmitしません。terminal transport failureはfalseでraw buffersを保持しません。closed child failureは完全なcontrol frameを検証できますがsemantic payload/target proofを生成せず、どちらの経路もraw child stderrを公開しません。

このsliceの`reference_process_observation_v2`はclosedな明示evidenceからreference recordを生成し、owner fieldsの注入を拒否します。`validate_process_observation_v2`はそのdata contractを検証します。**raw request/response bytes・digest・control projection・実counterへのjoinはA02-2で追加する必須gateです。** productionはcallerがstatusを自由入力するAPIを公開せず、実OS操作からownerが観測します。

`launch-observation.json`のPID/bytes/response SHAはsynthetic dataです。fixtureの`transport_payload_admissible=true`は例示predicateの成立だけで、actual frameやOS launchの成立を証明しません。policy known digestは`abead3e8d882e02139fdfd849988fb3518e4d8f8b2302022699796c53c026448`です。
