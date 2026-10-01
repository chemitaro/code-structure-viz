---
種別: disc
ID: "20261001t030614z-disc"
タイトル: "Issue8 A Launch Feasibility Evidence"
状態: "recorded"
作成者: "iwasawayuuta"
最終更新: "2026-10-01"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["20261001t024645z-adr-issue8-trusted-toolchain-launch-model.md"]
reflected_to: ["../design.md", "../plan.md", "../report.md"]
---

# 20261001t030614z-disc Issue8 A Launch Feasibility Evidence

基点 `32422f8be8d845c3c69cd206fb05bd3691c5f235`。A採択後の非production実機試作である。公開spawn方式の成立範囲と未証明事項を分ける。製品TypeScript解析、旧verified-FD保証、Issue完了、独立レビューpassを証明しない。

## Inputs

- 採択済みADR `20261001t024645z-adr-issue8-trusted-toolchain-launch-model.md`。
- 保存した実行コード（generic importのopaque evidence、正本ではない）:
  - Python harness: `20261001t032037z--a-launch-spike.py`。元の名前は`a-launch-spike.py`。
  - bootstrap: `20261001t032037z-01--a-bootstrap.mjs`。元の名前は`a-bootstrap.mjs`。
  - synthetic analyzer: `20261001t030437z--a-analyzer.mjs`。元の名前は`a-analyzer.mjs`。
- bootstrap SHA-256: `ae9fe66bec7cc5d12ddcdcefe4d1ba471ada2578c7b57d62605e006ecffe1105`。
- analyzer SHA-256: `ee927406f9ffce03c5ffa2992802089a4339b951f4afc936f342e76462978359`。
- Linux実験は既存imageを`--pull=never`で再利用した。containerはmacOS端末上のLinux実験環境であり、製品利用時の必須条件ではない。

## Synthesis

### 実測matrix

| OS/architecture | Python | Node実値 | 結果 | 候補実体のSHA-256 |
| --- | --- | --- | --- | --- |
| macOS 27.0.1 / Darwin 27.0.0 arm64 | 3.12.11 | 22.10.0 | 8 checks pass、exit 0 | `533ae63c75da67004f803647005bfff691c2633aaff46da346392b1a3220269c` |
| 同上 | 3.12.11 | 24.14.0 | 8 checks pass、exit 0 | `20a18709f0154d668f1bd6f6ea8c2a7ae001447b4b2c339732f22e57a8767a55` |
| 同上 | 3.12.11 | 20.19.5 | unsupported、analyzer未初期化、harness exit 0 | `c37b0c15f83f1b63c4b162c6f47e586ed6b00ac9ed093037fe679f676f9d2195` |
| Linux arm64 | 3.12.14 | 22.0.0 | 8 checks pass、exit 0 | `39d79a0ac7e784fac9898a9a6b30be03ab1b3ae317e0ba094341c237c5ab6431` |
| Linux arm64 | 3.12.14 | 22.23.3 | 8 checks pass、exit 0 | `d09e299258c24f7cdf6f5d5ec185e3a56512b27a697113735dac909f1cac7b8d` |
| Linux arm64 | 3.12.14 | 20.19.4 | unsupported、analyzer未初期化、harness exit 0 | `29a5fb4fd2bf44f97eed6727263b663a0f13fb840d42859d02ba974229761acc` |

非対応Nodeの子exitは66。表のexit 0は「その拒否をharnessが検証できた」ことを表す。先行したLinux/Python 3.11.2でのpassは参考であり、Python 3.12受入れの代用にしない。

8 checksは、(1) 不正requestの単一protocol-failure応答、(2) 正常時の一つのJSON応答と同じNode processの実version、(3) 保持bytes由来のprivate資材と独立した空cwd、(4) closed argv/明示env/親のinheritable FD非継承、(5) repeat runの別temp pathと同じ資材、(6) stdout 16 MiB exact/+1、(7) stderr 64 KiB exact/+1、(8) timeout時のTERM-resistant親/子のgroup停止・直接子wait・temp cleanupである。超過時にstdout/stderrのpartial bytesを保持・公開しない。

不正requestのnegative checkを先に追加したところ、初版bootstrapはcatch後もparsed requestを使い、第二のJSONを返した（`JSONDecodeError: Extra data`、RED）。catchでrequestを破棄する最小修正後、同じInterfaceでGREENとなり、上記matrixを全再実行した。初版imports `20261001t030436z--a-launch-spike.py`と`20261001t030436z-01--a-bootstrap.mjs`はこの修正前の履歴だけであり、最新実行コードへ使わない。

### 二つの実機差異

**環境変数:** 親が渡したenvは`LANG=C.UTF-8`、`LC_ALL=C.UTF-8`、`TZ=UTC`だけ。native `/usr/bin/env -0`でも一致した。macOS Nodeの`process.env`には追加の`__CF_USER_TEXT_ENCODING`が観測された。Linuxでは追加なし。追加元の詳細は未特定であり、Nodeへ渡したenvとruntime内部の状態を同じ観測と呼ばない。親に設定した不正`NODE_OPTIONS`/`NODE_PATH`は子へ継承されなかった。

**終了済みgroup:** 単一`/usr/bin/true`の終了後、leaderをまだwait/reapしない状態でも、Darwinの`killpg(SIGTERM/SIGKILL)`およびnegative PIDの`kill`がerrno 1、`getpgid/getsid`がerrno 3になった。生存中の`/bin/sleep`ではgroup TERMが成功し、その終了後KILLがerrno 1になった。sandbox外の同じ試作も失敗したため、sandbox解除だけでは解消しなかった。

実験では`EPERM`を一律成功にせず、公開SDKの`libproc.h`/`sys/proc_info.h`にある`proc_listpids(PROC_PGRP_ONLY)`と`proc_pidinfo(PROC_PIDT_SHORTBSDINFO)`で生存group memberが無い場合だけ終了済みと判定した。問い合わせ失敗・permission error・truncation・生存memberは確認失敗にする。leaderをreapする前に問い合わせ/必要なsignalを終え、再利用されたPGIDへ後からsignalしない。これは試作上の候補方式で、全macOS版・architectureに対する製品保証ではない。

TERM-resistant childの開始をready markerで確認してからtimeoutを発生させ、遅延sentinelが書かれないことを検証した。grandchildそのものをPython親がwait/reapしたという主張はしない。group離脱・runtime exploit・任意same-UID攻撃の防御実証でもない。

### 再現手順

Git cloneからは、上記3 evidence filesをGit管理外のprivate実験directoryへ元の3名で配置する。harnessとassetsの相対配置が必要。製品locatorやfixture fallbackとして使わない。

macOS（利用者が信頼する導入済みNode実体を指定）:

```sh
uv run --locked python .workbench/luna-max-implement/issue8-nextjs-snapshots/evidence/process-spike/a-launch-spike.py --node /Users/iwasawayuuta/.anyenv/envs/nodenv/versions/22.10.0/bin/node --output .workbench/luna-max-implement/issue8-nextjs-snapshots/evidence/process-spike/a-launch-darwin22-results.json
```

Linux/Python 3.12（実験directoryをread-onlyで`/probe`へmount、既存Node ELFをstdinで渡す）:

```sh
docker run --rm --pull=never --network=none --read-only --cap-drop=ALL --security-opt=no-new-privileges --entrypoint /bin/cat node:22.0.0 /usr/local/bin/node | docker run -i --rm --pull=never --network=none --read-only --cap-drop=ALL --security-opt=no-new-privileges --pids-limit=64 --memory=768m --cpus=1 --tmpfs /tmp:rw,exec,nosuid,nodev,size=320m --mount type=bind,source=/Volumes/990p2t/offloaded/home/iwasawayuuta/.codex/worktrees/c6b6/code-structure-viz/.workbench/luna-max-implement/issue8-nextjs-snapshots/evidence/process-spike,target=/probe,readonly --entrypoint /usr/local/bin/python python:3.12 /probe/a-launch-spike.py --node-stdin --output /tmp/a-launch-linux-results.json
```

`node:22.0.0` image IDは`420b70e940673468ca7bf9bb6f54f596fca2db2d8958128de475ef8f2a2c7761`、`node:22`は`b937e94e9d34`、`node:20`は`2ee7e9a248e2`、`python:3.12`は`10845dc2c17b19aea78a9ecd06c879615a418ba7c73eee18946abbedcdc0965f`。mutable tagを後日の同じbytesの証明に使わず、candidate/asset hashも照合する。

最初のLinux/Python 3.12試行はtmpfsのnoexecにより候補の実行可能性確認で停止した。実験用trusted executableを置くtmpfsだけへ明示`exec`を付けて再実行した。runtime downloadや製品のpermission緩和ではない。実験containerと一時Node bytesは終了時に除去され、既存image・他のcontainerには変更していない。

## Options and trade-offs

- Aの公開spawn、同一process version判定、private stagingはこの実験範囲で成立した。FD-exec、sealed-FD loader、別version probeを必要としなかった。
- 複雑なlifecycleは一つの実行Moduleへ閉じる。macOS固有の環境状態/終了判定をcallerやsemantic identityへ漏らさない。
- 公開OS APIで確認できないcleanupを成功とせず、typed failure/no payloadへ落とす。EPERMの握りつぶしやPID reaping後のgroup signalは不採用。
- 実測はsynthetic analyzerで、TypeScript 5.9.2、virtual CompilerHost、対象未実行sentinel、実CLI、interrupt、Node/package drift、wheel/sdist、x64、全OS版の受入れは未実施である。

## Reflection

- RequirementのA trust modelを変えず、Designのpolicy/実測の責務分離とPlanのruntime契約移行へ接続する。
- 旧v1 process schema/fixtureのpassを新方式の受入れに流用しない。新versionのwire/compatibility/provenance/referenceが閉じ、exact-SHA独立Strict gateを通るまでproduction availabilityを追加しない。
