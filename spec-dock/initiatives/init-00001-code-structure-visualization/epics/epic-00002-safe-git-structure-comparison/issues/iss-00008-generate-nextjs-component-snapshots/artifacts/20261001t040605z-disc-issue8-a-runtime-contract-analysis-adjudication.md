---
種別: disc
ID: "20261001t040605z-disc"
タイトル: "issue8-a-runtime-contract-analysis-adjudication"
状態: "final"
作成者: "iwasawayuuta"
最終更新: "2026-10-01"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["20261001t040546z--a-runtime-contract-analysis-result.md", "20261001t030614z-disc-issue8-a-launch-feasibility-evidence.md", "20261001t024645z-adr-issue8-trusted-toolchain-launch-model.md"]
reflected_to: ["design.md", "plan.md", "report.md"]
---

# 20261001t040605z-disc issue8-a-runtime-contract-analysis-adjudication

採択済みAの契約移行を、exact-SHA外部助言とローカルの実schema/producerへ照合した記録です。新仕様の独立レビュー、production可用性、Issue完了の認定ではありません。

## Inputs

- analysis: ChatGPT Use Strict、fresh session `issue8-a-runtime-closure`、Oracle 0.21.3、browser engineのみ。2026-10-01 03:44:19〜04:03:30 UTC、exit 0。
- exact source: `chemitaro/code-structure-viz` / `iss-00008-generate-nextjs-component-snapshots` / `710eb49a2a3143e31b8a91580700d16839d9070d`。wrapperのclean/live SHA照合を通り、回答先頭もGitHub connectorの完全一致を記録しています。connector attestationはprompt-enforcedであり、wrapperが返す機械認証ではありません。
- model/effort: requested `gpt-5.6-sol` / `pro`。`meta.json`の`browser.modelSelection`と`browser.thinkingSelection`が、それぞれ`GPT-5.6 Sol` / `Pro`、`already-selected`、`verified=true`を記録。バックエンド内部の別個の認証ではありません。
- 保存回答: [20261001t040546z--a-runtime-contract-analysis-result.md](20261001t040546z--a-runtime-contract-analysis-result.md)。Artifact SHA-256 `1d6359d6b0bfb7003f3ce90106b895c606b194b5cf6056ba2041ac1dee6e3946`。CLIの元final-message SHA-256は`1d40e6d1a39f5f7e630cffbaf4c9a548ba34ee23713d0aa93ac0dc693c360a14`。Git whitespace gateのため549/552/555行のMarkdown hardbreak用末尾2空白だけを除去し、意味内容は変更していません。Oracle session/output/transcriptは変更していません。providerの`:chatgpt-content-reference`は原文保持であり、ローカルで解決できるcitationではありません。
- ローカル照合: `schemas/next-*.schema.json`、`run-manifest-v1`、`stdout-result-v1`、`semantic-v1`、`run-summary-v1`、`runner.py`、`protocol.py`、reference validatorの`_trusted_environment_snapshot`、`_compatibility_descriptor_snapshot`、`recompute_compatibility_id`、`validate_trusted_environment`。

## Synthesis

### 採用する骨格

1. semantic entity/proofのv1 defs、TypeScript 5.9.2、Unicode 15.0.0、identity/algorithm versions=1、trusted semantic profileの意味を保持する。runtime/document envelopeは新versionで閉じる。
2. request v2はruntime requirementというintentを持ち、actual version、candidate path/hash、process observation、compatibilityを持たない。同一process bootstrapのcontrol resultの後にPython ownerがruntime binding/compatibilityを導出する。
3. response v2は単一closed object＋LF。success、unsupported、protocol、bootstrap、semantic failureを区別し、非successにはsemantic payload/model/proofを付けない。transport failureはPython側のoutcome。transport successに含まれるmodel自体はCoreでcomplete/partial-safe/target failureへ判定できるため、意味上のincompleteを機械的にchild failureへ置換しない。
4. policy v2とobservation v2をauthorityにし、旧derived `next-process-launch-v1`の新しい偽装viewを作らない。旧v1は不変回帰、別moduleのv2 reference laneでproducer/validator/negative vectorsを閉じる。
5. first-party analyzerはdescendantをspawnしない。normal exitでは直接子wait後に古いgroupへsignalしない。異常終了ではleader未reapの間にgroup stopを試み、Darwin EPERMを一律成功にしない。初期productionでlibprocを必須にせず、確認不能は`cleanup_unverified`としてpayloadを抑止する。spikeのlibprocは非production証拠のまま保持する。

### ローカル証拠による補正

| 原助言の箇所 | 現物 | 採る処置 |
| --- | --- | --- |
| stdout-result-v1をshape不変なら保持 | `schemas/stdout-result-v1.schema.json:20`はpublication-v1へのexact ref | publication v2を含む新chainにはstdout-result-v2が必要。旧v1は改変しない。 |
| semantic-v2 dispatcherは条件付き | `schemas/semantic-v1.schema.json:273`はnext-semantic-v1へのexact ref | 新documentをgeneric dispatcherで検証するlaneにsemantic-v2が必要。旧Next defs/algorithmsは再利用する。 |
| root manifestが旧process/adapter schemaを直接束縛 | rootの直接refはnext-run-decision-v1とnext-publication-decision-v1。process等への依存はそれらの先 | root v2という結論は維持するが、根拠を再帰的ref closureとして記録する。 |
| semantic/v1にdocument_contract/v2を追加 | 旧semantic v1はclosedで新fieldを許可しない | 新top-level documentの識別は新version schemaへ固定し、旧dispatcherをweakeningしない。entity identity versionsは上げない。 |
| trusted manifest v2でdescriptor/v1とshaを維持 | `_trusted_environment_snapshot`/validatorはphysical_pathを含む完全v1 manifestをhash | package mapping/semantic preimageを分離する新manifest/descriptor identityへ明示移行する。旧v1 hashを新preimageで再計算しない。semantic profileの宣言内容/認証symbolは保持する。 |
| concrete pathはobservationだけ／policyにも含めてよい | 起動前sealed policyは実spawn引数とのjoinを要する | concrete policyはhost-local。portable projectionからprivate root/argv path/device/inode等を除外する。二つの意味を同じrecordへ混ぜない。 |
| request入力API＋Module内bundle retain | callerはrequestを作るためにbundle由来identityを必要とする | public lifecycle入口はseal/intent/runtime選択。readonly bundle identityとrequest生成を同じretained ownerへbindし、caller-selected metadata/requestをauthorityにしない。詳細のproducer joinはA02で閉じる。 |
| failure stageから一律prefixを合成 | reader phase-local evidenceや、後から失敗した既観測slotがある | sourceのphase evidenceを維持する。child request bindingとPythonによるrequest生成は別観測。partial raw frameからversion/control成功を補完せず、実際に検証済みのprefixを後続failureで消さない。 |

### 閉じる版移行集合

- 新leaf: node runtime requirement、execution asset identity、runtime binding。
- v2: process policy/observation、private request/response、compatibility、trusted environment manifest/descriptor、runtime provenance、run/publication decision、Next domain/semantic document、root manifest、generic semantic dispatcher、stdout result。
- 維持: run context、limits、config/source plan、path/applicability、Next semantic/proof element defs、identity/algorithm versions、generic run summary。build inventoryはrole/member mappingの実検証でv1維持可能かを確定し、未生成inventoryを実packageの証拠にしない。
- 旧process derived descriptorのv2は不要。保証を弱めた旧v1へのadditive unionは作らない。

## Options and trade-offs

- 採用: 不変v1回帰＋新runtime v2 chain。旧強保証の虚偽移植を避け、意味要素defsを再利用するため変更の局所性を保てる。
- 不採用: 全v1 surfaceのsilent rewrite、全semantic IDsの版上げ、fixture hashをproduction認証へ転用、Node別probe、default/PATH探索、platform縮小、container/private API必須化、将来backend registry。
- cleanup候補: public killpg＋direct child waitの保守的方式を先行。libprocのsize retry/SDK struct/support matrixを満たす改善はfalse failure削減の別実装として扱い、no-live未確認の成功化やsecurity boundaryとは呼ばない。
- private exit 65/66はspike証拠あり。bootstrap 67/semantic 68は新contract候補としてnegative vectorsと同時に固定し、未実測を実測と記録しない。public CLI exit/status/codesはCoreの既存原則が所有する。
- 元analysisは巨大reference validator全通読、製品TypeScript/OS/CLI/package、独立reviewを実施していないと明記。これらを次のgateから削らない。

## Reflection

- DesignのA版移行closure、PlanのA02細分、Reportの進捗へ反映する。技術的補正は採択済みAのscope/security/OSを変更しない。
- A02は一つのschema/reference seamのRed→Greenから順に実施する。全部のimagined testsやproduction analyzerを一括実装しない。
- A02全closureとlocal gateがgreenになったclean/pushed exact SHAをfresh ChatGPT Code Review Strictへ渡す。このadvisoryを`review_status=pass`の代用にしない。
- 実行経路復旧: 初回の旧`--oracle personal`は現行launcherからCLIへ転送されunknown optionで送信前exit1。新slugのsession未作成と現行PATHのpersonal-use-v3/Oracle0.21.3を確認し、無効引数だけを除去して同じprompt/files/model/effortで開始した。Oracle checkout/共通skillのsourceは変更していない。長時間待機は元jobのみ、Browser Useによる監視・API fallback・重複送信なし。
