# Next.js semantic compatibility v3 — accepted target

新source admission profileを区別する親所有のdescriptorです。schema/referenceの追加はSpec Review Strict pass後のA02 TDD単位です。旧[compatibility v2](next-compatibility-v2.md)を遡及変更しません。

descriptorは`schema=code-structure-viz.next-semantic-compatibility/v3`、下記preimage十keys、`compatibility_id`のexact十二keysです。

| 十key preimage | 値 / authority |
| --- | --- |
| `semantic_schema` | `code-structure-viz.semantic/v3` |
| `identity_versions` | 旧v1全identity versions。Project/File ID、PropsIRも不変。 |
| `algorithm_versions` | recognition/export/props/relation/fact/boundary/Unicodeの旧v1意味と値。 |
| `semantic_profile_id` | `next-trusted-profile-v1`。宣言の意味profileでありadmission profileではない。 |
| `unicode_profile` | pinned Unicode15 profile/table/KAT。 |
| `runtime_binding_profile_id` | 保持したruntime-binding-v1のfixed profile。 |
| `typescript_identity` | `typescript-5.9.2`という同梱identity。actual import/useを推論しない。 |
| `trusted_type_environment_digest` | 同じretained declarationsのtrusted descriptor v2 hash。 |
| `portable_toolchain_fingerprint` | 同じvalidated transportのruntime binding hash。 |
| `semantic_admission_profile_id` | `next-source-inventory-safe-subset-v1`。親のfixed contract。 |

`compatibility_id=SHA256(CJ15(ten_key_preimage))`。descriptorのschemaとself IDをhashに含めません。source/request/targets/partition/status/model digest/host path/PIDを含めません。admissionルールを十番目のkeyで区別し、既存algorithm versionを新意味へ書き換えません。

2026-10-02採択のowner-closed File/Module公開条件は、この未実装・未出荷admission profileに含めます。v3/profile/producer0.2.0の計画identityは維持し、旧v1/v2のidentity/hash/KATへ遡及適用しません。新partition/public model値とその新KATは修正後の公開集合で固定します。private wireの既存excluded enumはshape再利用であり、旧v2 certificateが新公開条件を証明するという意味ではありません。

planned schemaは`schemas/next-compatibility-v3.schema.json`、URNは`urn:code-structure-viz:schema:next-compatibility-v3`です。全objectをclosedにし、変えないleafだけ既存exact refsを再利用します。typed same-owner Core/candidateから生成し、独立validatorでmetadata/binding/digestとpreimageを再導出します。旧v2 compatibilityをv3へcastしません。
