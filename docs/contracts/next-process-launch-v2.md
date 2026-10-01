# Next.js public-spawn runtime契約 v2

## 移行状態と保証境界

Issue #8の採択済みAに対応する新contractです。旧v1は歴史・回帰として不変に保持します。この文書/schema/referenceの整備はproduction Node実行、TS解析、CLI可用性、package収録、独立Strict passを証明しません。A02全体のclosureは未完了です。

Python・Node・インストールしたfirst-party package・OSは利用者管理のtrusted toolchainです。repositoryは非信頼dataであり、targetコード/config/plugin/script/node_modulesを実行しません。macOS/Linux、明示absolute Node、stable major >=22、同一process version bootstrap、offline runtimeを維持します。candidate hashをactual-image認証と呼ばず、same-UID hostile tamper/未知exploit完全封じ込め/hard RSSを保証しません。

## 起動前policy

`next-process-launch-policy/v2`はconcreteなhost-local起動条件です。`producer=reference/platform=fixture`とproduction OS policyを区別します。reference policyは実spawnの証拠ではありません。

- `request_id`はownerが生成したprivate requestへjoinします。
- `runtime_requirement`は閉じたnode requirement leafで、stable release/minimum major 22というintentだけです。actual Node versionをpolicyへ入れません。
- `node_candidate`は明示absolute pathとPythonが測ったcontent SHA-256だけです。実行済みNodeであるという主張を含みません。
- `adapter`はretained resourceのprotocol/version/hash/logical entrypoint member。header ownerは`code_structure_viz/_next_runtime/next-adapter.mjs`です。
- `execution_asset_set_id`、`typescript_identity`、`trusted_environment_digest`は同じretained ownerへjoinするidentityです。stagingのために別resource lookupをしません。
- `private_root`内に`runtime_directory`と別の空`cwd`を作ります。sealed argvは`[absolute_node, "--max-old-space-size=512", private_entrypoint]`。512はV8 old-space MiBでありRSSではありません。
- shell false、pipes、passed envの3キー、close_fds true/継承allowlist 0/1/2、start_new_session、group stop、direct child wait、limits v1を封じます。passed envとNodeが内部生成したenv、継承FDとNode内部FDを混同しません。
- JSON Schemaが閉じたshape/定数を検証し、reference/production ownerがpath containment、argv、request、retained identityとのcross-field joinsを追加検証します。shapeだけで新runtimeをadmitしません。

concrete policyのdigestとportable projectionを分離します。portable runtime identityにprivate paths、device/inode、PID/PGID、FD、cleanup errnoを流しません。[observation v2](next-process-observation-v2.md)と[runtime binding v1](next-runtime-binding-v1.md)がdata-only fields/preimage/owner joinsを固定します。raw wireとtrusted profileの完全joinは後続A02 unitです。

保持資材のcontent leafとbyte ownerのjoinは[execution assets identity v1](next-execution-assets-v1.md)で固定します。policy shapeの検査と、retained ownerへのasset ID/adapter identity joinは別です。部分的なidentity joinを完全なruntime admissionと見なしません。

## lifecycle受入れ

first-party analyzerはdescendantをspawnしません。normal exitはdirect childをwaitし、reap後に古いPGIDへsignalしません。異常時はunreaped leaderを保持してgroup TERM→bounded grace→KILL→direct child waitを行い、raw/partial buffersを破棄してprivate資材をcleanupします。

Darwin EPERM、signal/wait/read/temp cleanup確認不能は`cleanup_unverified`等のtyped failureでpayloadを抑止します。spikeのlibproc試作は製品必須backendへ昇格しません。公開APIで確認した事実と未確認の終了条件を区別し、正常frameを受信したことだけでcleanup成功を推論しません。

このcontractの成立には、後続のclosed observation/control wire/compatibility/provenance/public projections、negative vectors、実OS/CLI/package gateが必要です。旧derived verified-FD descriptorへの投影で代替しません。
