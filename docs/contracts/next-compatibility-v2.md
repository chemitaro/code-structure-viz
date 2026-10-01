# Next.js semantic compatibility v2

## Parent-owned identity

`schema=code-structure-viz.next-semantic-compatibility/v2`、semantic document/dispatcher=`code-structure-viz.semantic/v2`へ移行します。document identityを変更しても、entity/props identity、recognition/export/props/relation/fact/boundaryのalgorithmはすべて1のままです。Unicode 15.0.0 NFC/identifier、fixed TS 5.9.2、trusted meaning profile=1を保持します。旧v1 hashを別preimageで再計算しません。

通常producerの`compatibility_descriptor_v2(candidate)`とvalidatorの`validate_compatibility_descriptor_v2(record, candidate)`は、[whole-exchange transport owner](next-adapter-exchange-v2.md)を要求します。free runtime version、metadata-only binding、child-authored descriptor、duck candidateを入力にしません。parentが検証済みcontrol後のruntime bindingからTS/trusted digest/portable fingerprintを導出します。Core semantic受入れとは別です。

locked semantic metadataは`next_semantic_profile_v1_reference.py`、schema shapeはv2 leaf、維持するidentity/algorithm/Unicodeの要素defsだけはv1を参照します。table digestsまでexactに検証し、shape-validな偽tableや再hashした別bindingを拒否します。

## Closed preimage

`compatibility_id`は次の**9 fieldsだけ**のpinned Unicode 15.0.0 canonical JSON digestです。sorted/compact UTF-8、末尾LF無し、float/NaN禁止です。

| field | owner |
| --- | --- |
| `semantic_schema` | new document/dispatcher identity `code-structure-viz.semantic/v2` |
| `identity_versions` | unchanged semantic ID algorithm v1 |
| `algorithm_versions` | unchanged recognition等v1、exact identifier table digest |
| `semantic_profile_id` | `next-trusted-profile-v1` |
| `unicode_profile` | exact Unicode 15.0.0 NFC table/full-scalar KAT |
| `runtime_binding_profile_id` | `next-public-spawn-runtime-v1` |
| `typescript_identity` | joined bindingのfixed TS identity |
| `trusted_type_environment_digest` | same retained declarationsのnew logical descriptor identity |
| `portable_toolchain_fingerprint` | joined bindingの`runtime_toolchain_fingerprint` |

top-level `schema`とself `compatibility_id`はpreimageから除きます。project/source/request ID/targets/formats/limits、host-local policy/observation digest、candidate path、private root/device/inode/PIDは入れません。explicit binding profileでtrust modelを識別し、candidate hashをactual-image attestationへ昇格しません。

public field名`portable_toolchain_fingerprint`は維持しますが、v2では新public-spawn bindingのcontent fingerprintを指します。旧verified-FD toolchain fingerprintの互換viewではありません。content identityを含むため実Node version/candidate bytes/retained assetsが変わればcompatibilityが変わり得ます。source/request内容や同じbytesのhost path relocationだけでは変わりません。

## Independent vector / 未完了gate

`tests/fixtures/next_runtime_v2/compatibility.json`はliteral metadata＋独立計算binding fingerprint `2654b835...`から作ったvectorです。jq/shasumで計算したcompatibility IDは`0b0d3113311bac4b3788dbd6bb4d643adb181599c7b9e7e7ae7235e382397728`。new producerでexpected hashを計算していません。source/selector/format/host pathsを変更しても同じbindingなら同じdescriptorになるpositiveと、再hashした偽trust/portable/Unicode metadataのnegativeを検証します。

Core model/proof/target gate、new provenance/run/publication/domain/semantic/root/stdoutへのexact-ref closure、actual process/TS/CLI/installed distribution、A03独立reviewはこのsliceでは未認定です。
