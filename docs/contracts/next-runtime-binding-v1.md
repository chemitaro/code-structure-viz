# Next.js portable runtime binding v1

## 境界と成立条件

`code-structure-viz.next-runtime-binding/v1`は採択済みAの新leafです。旧verified-FD/実行image認証のdescriptorではありません。計測したNode候補、同じNode processのversion、保持したfirst-party資材を結合します。初期profileは`next-public-spawn-runtime-v1`、TypeScriptは`typescript-5.9.2`です。

Node versionはcanonical stable `major.minor.patch`でmajor >=22、sourceは`process.versions.node`だけです。別processのprobe、事前条件のminimum version、callerが指定したversionを同一process観測の代用にしません。

このsliceにはdata-only reference producer/validatorとsynthetic fixtureがあります。実Node起動、実TypeScript、actual raw frameの認定ではありません。完全admissionにはprivate request/response bytes、process観測、retained owner、trusted profileとのjoinが必要で、A02全体は未完了です。

## Portable preimage

fingerprintは次のobjectをkey-sort・compact UTF-8 JSON（末尾LF無し）としてSHA-256にします。全fieldはfixed ASCII grammarです。`schema`とfingerprint自身はpreimageに含めません。

```json
{
  "runtime_binding_profile_id": "next-public-spawn-runtime-v1",
  "node_candidate": {"sha256": "<measured candidate digest>"},
  "node_observation": {"version": "<same-process stable version>", "source": "process.versions.node"},
  "execution_asset_set_id": "<retained content identity>",
  "adapter": {"protocol": "code-structure-viz.next-adapter/v2", "version": "<retained header version>", "sha256": "<retained entrypoint digest>"},
  "typescript_identity": "typescript-5.9.2",
  "trusted_type_environment_digest": "<owned trusted profile identity>"
}
```

recordの`adapter`には固定logical `entrypoint_member`もあります。その値はschema定数とasset setで既に拘束するため、fingerprintのadapter projectionには重複して入れません。

Nodeのabsolute path、private root/cwd/argv、producer/platform、PID/PGID、FD、device/inode、request ID、limits、cleanupはこのportable preimageに含めません。ただしpolicy/processの検証から除外するという意味ではありません。異なるOSのNode binaryは通常digestが異なり得ます。「host-local fieldを除く」と「OS間で同じfingerprintを保証する」は別です。

## Producerとvalidator

- `runtime_binding_identity_v1(policy, assets, node_version=...)`はcontent projectionだけです。与えたversionの実観測・admissionを認定しません。
- `runtime_binding_from_observation_v1(policy, assets, observation)`はreferenceの成功transport観測からversionを取り、policyと同じretained bytesへjoinします。failure/unsupported/cleanup未確認ではbindingを生成しません。
- `validate_runtime_binding_identity_v1`はclosed shapeとself fingerprintを検証します。
- `validate_runtime_binding_observation_v1`は上記に加えてpolicy、retained owner、process observationとのcandidate/asset/adapter/TS/trusted identity/version joinを検証します。別versionや別identityでself fingerprintを正しく再hashしただけのrecordも拒否します。

いずれも`tests/contracts/next_runtime_v2_*.py`のdata-only referenceでありproduction runnerではありません。observationのcontrol/hashを実response bytesへjoinするgateとtrusted profile全体のbyte-bound検証は後続A02-2/3です。metadata-only validationを完全admissionとして使用しません。

controlled child failureや後続cleanup失敗では既観測control/versionを消しません。一方、success-only bindingとsemantic payload admissionは生成・採用しません。transport successでもsemantic model/proofの成立はCoreが独立に検証します。

## Known vector

`tests/fixtures/next_runtime_v2/runtime-binding.json`のfingerprintは`152454270b4314f8f40a6c6902c9116689e3644945f9420d98c237872bcc09a1`です。元のretained synthetic bytesは[execution assets v1](next-execution-assets-v1.md)を参照します。candidate/trusted identityのplaceholderを実計測値として扱いません。
