# Next.js semantic compatibility v1

## 目的と適用境界

Issue #8 の実装前契約です。比較対象のソース内容が変わっても、同じ意味で解釈したスナップショットかを判定します。
Issue #9 は compatibility_id が一致するスナップショットだけを比較します。不一致は内容差分ではなく比較不能です。

現在の正本はこの文書、next-compatibility-v1.schema.json、参照計算と既知値テストです。
過去Roundの記述はGit履歴とIssue artifactsのレビュー記録へ分離しました。旧「Node/adapter patchを変えてもID不変」という規則は採用しません。

## 正確なpreimage

compatibility_id は次の8項目だけのcanonical JSONのSHA-256です。descriptorのtransport schemaとcompatibility_id自身は除きます。

| 項目 | 意味・取得元 |
| --- | --- |
| semantic_schema | 公開semantic schemaの識別子 |
| identity_versions | project/file/module/component/member/relation/fact/props_irの各identity version |
| algorithm_versions | recognition/export/props/relation/fact/boundaryとIdentifierName Unicode profile |
| semantic_profile_id | next-trusted-profile-v1 |
| unicode_profile | Unicode 15.0.0 NFCのprofile/algorithm/table/full-scalar KAT digest |
| typescript_identity | 固定したTypeScript 5.9.2のidentity |
| trusted_type_environment_digest | 認証済み型環境全体のsha256。宣言ファイル内容、inventory、予約symbol、license情報を含む |
| portable_toolchain_fingerprint | 以下の観測済みruntime contentのdigest |

portable_toolchain_fingerprintのpreimageは閉じた次のobjectです。

```text
{
  node: { status, version, sha256 },
  adapter: { schema, version, sha256 },
  typescript_identity
}
```

Nodeの実bytes/versionとadapterの実bytes/versionのいずれかが変われば互換性IDも変わります。
Nodeの単なる「major >=22」やadapter protocol名だけで代用しません。
型環境のdigestをlicense一覧だけのdigestで代用しません。
TypeScript versionは型環境のversionと照合し、現在のprofileと異なる版は新しいversioned migrationで導入します。

Node未取得時の値はnullのままです。この状態のfailure descriptorは意味のある比較結果を認証しません。
request-independent停止ではcompatibility descriptor自体がnullです。取得stageごとの公開可否はprovenance契約に従います。

## 実行identityとの分離

次の変更はsemantic compatibilityを変えません。

- 対象repositoryのソース・config・commit・target。
- resolved resource limits、timeout、選択出力format。
- host path、OS、device/inode、FD番号、private cwd。

これらの実行条件・観測はrun fingerprintまたはlocal process attestationに記録します。
process observationのstable fingerprintは起動ポリシーや制限も含むため、semantic compatibilityのportable fingerprintにそのまま流用しません。

productionでは独立した事前policyがNode/adapterの許可identityを持ち、起動後の観測をそのpolicyと照合します。
別の正当なpolicyで別runtimeを使うこと自体は偽装ではありません。その実行は別のcompatibility_idになります。
同じpolicyから外れた観測や、応答が自己再hashした別compatibility descriptorは拒否します。

## 構築と検証

1. 同梱型環境をcontent/inventory/予約symbolまで検証する。
2. toolchainとprocess observationのNode version/status、adapter version/protocol、TypeScript identityを照合する。
3. 観測から上記8項目を導出し、NextPublicationContextへdefensive copyで封印する。
4. 応答のdescriptorをclosed schemaと既知profileで検証し、owner contextのdescriptorとexact一致させる。
5. semantic JSON、domain/run manifestは同じcontextを投影する。writerによる再推測を認めない。

参照テストのNode hash 1/2の反復とadapter hash aの反復は、明示的な録画fixtureの例です。
実ホストのprobe、同梱adapterの実bytes、OS起動を検証した証拠ではありません。製品実装では実取得値へ置き換えます。

## Unicodeと既知値

canonical JSONはUTF-8、NFC文字列、key sort、余分な空白なしです。
NFCはhost UCDではなくチェックイン済みUnicode 15.0.0の表を使います。
表・official normalization test 19,074行・license・migration条件は [next-unicode-nfc-v1.md](next-unicode-nfc-v1.md) を参照してください。

現行の標準録画fixture（Node 22.14.0/hash 1×64、adapter 1.0.0/hash a×64）の既知値:

- 型環境: `2e232edf27d832b12ecd8159295681145eb27ce906a06abfa0e666eaa82de77d`
- portable toolchain: `422c0d93f5168180c85233ffc9b7735cf66d80fb21dc1c5a66605e99e6f6089d`
- compatibility_id: `b6c2f6f7bbf0403df1357380636fc2134fa33d6588ddb9ad71d731938a32fb20`

tests/contracts/test_next_contracts.pyの既知値、runtime content変更、host/limit不変、foreign descriptor拒否テストで固定します。
これらの成功は実装前契約の確認であり、製品adapterの完成や最終レビューpassではありません。
