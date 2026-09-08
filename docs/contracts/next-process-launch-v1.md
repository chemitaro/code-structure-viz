# Next.js adapterの起動policyと観測

## 境界と正本

Issue #8 の実装前契約です。起動を許可するpolicyと実際に起きたことのobservationを別objectにします。

- next-process-launch-policy-v1.schema.json: ownerが事前に解決・封印した許可条件。
- next-process-launch-observation-v1.schema.json: 実行境界の観測。productionと明示fixtureは別branch。
- next-process-launch-v1.schema.json: 旧descriptorの派生互換view。新しいauthorityとして構築しない。

production対応範囲はdarwin/Linuxです。Windowsは別scopeです。
schemaの成功や録画fixtureはOS起動を証明しません。実装計画のOS別受入を通して初めてproduction観測として扱います。

## policyを構築するownerの前提

policyはtarget repositoryやadapter responseから受け取る設定ではありません。
trusted parent runnerが次を検証して作り、以後はdefensive copyで保持します。

1. target側のscript、package manager、node_modulesを実行せず、許可されたNode実体と同梱adapter資材を解決する。
2. Nodeのrealpath/bytes hash/version、adapterのversion/protocol/content hashを取得し、同梱inventoryと照合する。
3. trusted parentがprivate temporary directoryを新規に確保する。target rootやその子・symlink先をcwdに使わない。
4. directoryの実体・所有者・0700相当の排他アクセスと寿命を確認し、実行中はownerが保持する。target由来pathで再利用しない。
5. resolved request limitsと、固定argv/env/pipe/FD/process group規則を封印する。

cwdが絶対pathであるだけではprivate-ownedの証明になりません。
このallocation/target separationはpolicy sealing前のowner preconditionです。
同じowner policyに対する観測差替えを拒否することと、別の正当なowner policyを認めることは区別します。
参照fixtureの/.code-structure-viz/private-runは説明用の固定値で、実hostにそのdirectoryを作成・検証した主張ではありません。

## 固定launch surface

| 項目 | v1の規則 |
| --- | --- |
| Node | stable SemVer major >=22。prerelease・不正表記・旧版はunavailable |
| argv | 許可Node実体と固定adapter entrypointの2要素だけ。追加引数なし |
| shell | false |
| cwd | 上記ownerが確保・保持するprivate directory |
| env | LANG=C.UTF-8、LC_ALL=C.UTF-8、TZ=UTCだけを明示構築 |
| denied_env | PATH、NODE_OPTIONS、NODE_PATH、npm_config_user_configを含むsorted unique set。その他も継承しない |
| stdio | stdin/stdout/stderrはpipe |
| FD | adapter imageに残るFDは0/1/2だけ。検証用parent FDは3以上、close-on-execでspawn結果まで保持 |
| process group | 独立groupを作成。timeout/capture超過ではgroup全体を停止しwait |
| limits | timeoutとstdout/stderr/response capをrequestのresolved値と一致させる |

固定entrypointの/.code-structure-viz/next-adapter.mjsは契約上のruntime locationです。
実装で物理資材への対応を変える場合は、policy・inventory・OS受入を同時に整合させます。

## production observationの検証順序

1. Nodeの検証用FDを開き、hash時点のrealpath/hash/version/device/inodeを記録する。
2. 許可policyからargv/cwd/env/stdio/group/limitsを構築し、policy digestを保持する。
3. OS別のverified executable spawn経路を使う。検証用FDはstdioと役割分離し、spawn結果まで保持する。
4. spawn時の実体とhash時点のidentityを照合し、post-spawn identityもequalを確認する。
5. 観測の全launch fieldを、独立した元policyとexact一致させる。観測からpolicyを再生成しない。
6. toolchainのNode/version/status、adapter version/protocol、request limitsとの一致を確認してcontextへ封印する。

観測中のreplacement、version/hash、argv、env、FD/group、post-spawn不一致はfail-closedです。
必要なOS保証が実装できない場合はavailableを生成しません。
darwin/Linuxのschema内primitive名は検証契約の識別tagであり、同名のOS APIが存在するという主張ではありません。
実装前のOS spikeで実APIへの対応を確定し、実現不能ならこの規則を推測で緩めず設計へ戻します。

起動前の未観測suffixをavailableのdefaultで埋めません。
未取得のNode/handleはnull、未発生launchのprovenanceはunobservedです。
途中失敗で何を保持できるかはstage-dependent provenanceの観測prefixが決めます。

## 三つのdigest

- local_process_attestation_digest: host path/OS/FD/device/inodeを含む完全な観測。
- process observationのstable fingerprint: host固有identityを除き、起動条件とobserved contentを保持する実行用projection。
- semantic compatibilityのportable_toolchain_fingerprint: Node hash/version、adapter identity、TypeScript identityだけ。timeoutやcapture capを含めない。

詳細preimageは [next-compatibility-v1.md](next-compatibility-v1.md) を参照してください。
参照fixtureのa×64などのhashは録画値で、実配布物のdigestではありません。

## captureと公開

private stdoutとstderrはincrementalに数え、chunk保持前に上限を判定します。超過ならread-stop、buffer破棄、group停止/waitです。
stderrの子process本文は公開診断へ転記しません。公開するのはcatalog-owned診断だけです。

finalizerはrequest/contextの上限を使用します。参照テストのfault injection引数は縮小だけを許可し、拡大を拒否します。
capture counter、retained bytes、allowed/failure、chosen limitを照合してからpublicationへ封印します。
selected-copyだけの超過は元のsemantic/domain/artifactsを保持し、runをincomplete/exit 3にします。
先行capture/public-stderr失敗がある場合はpayload_unavailableを優先し、selected-copy失敗が併発してもtyped resultへ進めます。
部分的なstdout/stderr本文は出力しません。

summary/manifestの測定時candidateと、公開失敗を記した最終manifestは別bytesになり得ます。
selected size/hashおよびstdout.candidateは測定時candidateを指し、最終manifest/typed resultのsize/hashとは別に保持します。

## 後続実装の受入

各対応OSで、実processを用いて次を検証します。

- private cwdの所有・target separation・cleanup、PATH/env汚染、追加FD非継承。
- Nodeの解決先/hash/version、symlink/実体差替え、検証FDの寿命とpost-spawn比較。
- timeoutと両capture超過のread-stop・group全停止・wait・raw/partial破棄。
- requestから各出力surfaceまでの同一観測・上限・response bytes・descriptor結合。
- productionとfixtureの識別保持。fixtureのflagsを実OS受入の証拠に流用しない。

現時点のテストはhost-freeな参照契約です。製品adapter実装、OS-level受入、最終固定SHA認定は未完了です。
過去Roundの相反する説明はGit履歴とIssue artifactsへ分離しました。
