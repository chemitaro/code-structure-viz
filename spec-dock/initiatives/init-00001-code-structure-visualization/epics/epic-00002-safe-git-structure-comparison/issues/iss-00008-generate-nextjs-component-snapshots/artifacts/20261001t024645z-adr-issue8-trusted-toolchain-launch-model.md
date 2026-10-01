---
種別: ADR（Architecture Decision Record）
ID: "20261001t024645z-adr"
タイトル: "Issue8 Trusted Toolchain Launch Model"
状態: "accepted"
作成者: "iwasawayuuta"
最終更新: "2026-10-01"
親: ["iss-00008"]
authority: "accepted"
accepted_authority: "accepted ADR"
accepted_at: "2026-10-01"
accepted_by: "iwasawayuuta"
mirror_eligible: true
derived_from: []
reflected_to: ["../requirement.md", "../design.md", "../plan.md"]
---

# 20261001t024645z-adr Issue8 Trusted Toolchain Launch Model

2026-10-01、ユーザーの「この推奨案を採用します。作業を再開してください」により、直前のA案一式を採択した。これは新しいtrust modelの採択であり、実装完了・実測成功・独立レビューpassではない。

## Context

- 本製品は未信頼のNext.js repositoryを実行せず、構造を静的に解析するローカルCLIである。
- 旧process契約は、hashしたverified handleとactual executable imageの結合を両OSで要求した。Darwinの実証が成立せず、起動前actual version、固定root entrypoint、追加flagなしとも実装上の衝突があった。
- `32422f8be8d845c3c69cd206fb05bd3691c5f235`のPro分析は旧保証下での停止を推奨した。新しい保証を承認なく緩める根拠には使わない。
- 同じUIDの攻撃者はPython runnerやadapterも変更できる。Nodeのhash/FDだけを強化し、ローカルtoolchain全体のtamper耐性を主張するのは不整合である。

## Decision

1. v1の標準運用を「利用者管理のtoolchainを信頼するローカル静的解析」とする。利用者管理のNode、Python、本製品package、OSを信頼し、対象repositoryは不信データとして扱う。
2. macOS/Linuxを維持する。NodeはNextだけのoptional dependencyで、利用者が明示する外部runtime。Nodeを同梱せず、固定TypeScript、compiled first-party adapter、trusted declarations、licenseはPython配布物へ収録する。PATH自動探索、自動download、runtimeのnpm/npx/build/pullは追加しない。
3. 対象TS/JS、next.config、plugin、package script、対象node_modulesを実行・loadしない。frozen inputとclosed virtual CompilerHost、Python側の独立semantic validation/redactionは維持する。
4. 公開された通常のprocess起動APIを使う。任意のhostile same-UID processによるtoolchain/runner改変耐性、未知のruntime脆弱性への完全防御は保証対象外。verified-FD/actual-image attestationを取得したと偽らない。
5. package資材の同じ保持bytesからidentityとrun-private stagingを導出する。runtime directoryと空cwdを分ける。shell=false、最小env、継承FD `[0,1,2]`、private pipes、独立process group、bounded capture/timeout/cleanupを維持する。Node自身が生成する内部FDと、親から継承するFDを混同しない。
6. argvはabsolute Node実体、固定`--max-old-space-size=512`、run-private entrypointのclosedな構造とする。512 MiBはV8 old-space上限であり、総RSS上限ではない。
7. 起動前policyはversion適格条件、同じNode processのfirst-party bootstrapは`process.versions.node`の実値を返す。非対応versionはTypeScript初期化前に拒否する。one request/one closed response/one processを維持し、別version probe、第二のJSON/bannerは追加しない。
8. runtime制御結果とsemantic payloadは別の検証責任とする。unsupported version、bootstrap/protocol/semantic failureを区別し、target proofや成功観測を補完しない。host-local ephemeral pathをstable semantic identityへ入れない。
9. 旧process policy/observationとprivate transportの破壊的変更は新しいversionへ明示移行する。旧v1の記録を同じidentityのまま書き換えず、既存semantic identity/props/relation意味は維持する。

## Options

| 案 | 不採用の理由または位置付け |
| --- | --- |
| A: 利用者管理toolchainを信頼 | 採用。既存ローカルCLIのtrust assumptionsと整合し、対象非実行へ集中できる。 |
| B: 管理者管理trusted store必須 | 全runner/資材/更新の管理が必要。通常の開発端末へ追加しない。 |
| C: Node同梱native helper | OS/architecture別配布・署名・runtime更新責任が大きく、同梱だけでsame-UID防御にもならない。 |
| D: Linux-only sealed-FD | macOS要件を変更し、experimental loader/実bundleの受入れも残る。 |
| E: container/VM必須 | 共有サービス等で強制FS/network/resource隔離が必要なら再検討。v1の利用条件へ混ぜない。 |
| F: 旧保証のままunavailable | 判断保留には安全だが、利用可能な製品の完成案ではない。 |

private API探索、別`node --version` process、任意flag許可をAへ暗黙追加しない。

## Consequences

- 小さい非production spikeで両OSの公開spawn、bootstrap、private assets、one-response、limits/cleanupを先に実測する。その後R/D/P、versioned schema/referenceを整合し、clean/pushed exact SHAの独立Strictレビュー後にproductionへ接続する。
- 実行Moduleの小さいInterfaceが資材保持、request、起動、capture、cleanupを隠す。Coreのsemantic検証/Artifact公開を吸収せず、将来backend registryを先行追加しない。
- 候補/packageの観測可能なdriftは拒否するが、hashを初期trustの認証、0700をsame-UID隔離、記録したpathをactual-image attestationと呼ばない。
- 実TypeScript bundle、両OS E2E、minimum/更新lane、checkout外offline wheel/sdist、license、既存domain不変性、Final Quality Gateは後続受入れであり、本ADRだけで達成されない。
- 強制OS隔離・hard RSS・敵対同UID耐性が必須となる用途は、このtrust modelを再決定する。

## References

- 採択前の比較・意思決定資料: `.workbench/luna-max-implement/issue8-nextjs-snapshots/evidence/decision-options-20261001.md`（Git管理外・非正本）。本ADRに採択内容を再記述し、GitHub参照可能にする。
- 旧契約に対するPro分析: Oracle `required-strict-github-connector-verificati-1355`、固定SHA `32422f8be8d845c3c69cd206fb05bd3691c5f235`、GPT-5.6 Sol / Pro。新契約のレビューpassではない。
- Initiative ADR: `20260824t030222z-01-adr-static-analysis-safety-boundary.md`、`20260824t030221z-02-adr-domain-adapter-boundaries.md`。static-only/Python+TypeScript/Node optionalを維持する。
- [Node 22.0 process.versions](https://nodejs.org/download/release/v22.0.0/docs/api/process.html#processversions)、[max-old-space-size](https://nodejs.org/download/release/v22.0.0/docs/api/cli.html#--max-old-space-sizesize-in-megabytes)。
- 反映先: Requirementのtrust/対応範囲、Designの実行Module/版移行、Planの実測→契約→Strict→実装順序。
