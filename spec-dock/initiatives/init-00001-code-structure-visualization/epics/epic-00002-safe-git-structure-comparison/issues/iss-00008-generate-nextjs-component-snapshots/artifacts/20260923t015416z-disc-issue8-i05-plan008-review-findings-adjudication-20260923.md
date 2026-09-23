---
種別: disc
ID: "20260923t015416z-disc"
タイトル: "Issue #8 I05-PLAN-008 Review Findings Adjudication"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-09-23"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: []
reflected_to: []
---

# 20260923t015416z-disc Issue #8 I05-PLAN-008 Review Findings Adjudication

複数のレビュー、canonical authority、現候補の検証証拠を統合したadvisoryな分析です。要件・設計・計画への採用や実装修正の認可を意味しません。

## Inputs

- 統合する evidence:
  - Issue #8 requirement.md、design.md、plan.mdのCurrent v1 normative authority、および該当schema・reference validator・tests。
  - Strict reviewer: Oracle session required-strict-github-connector-verificati-1057、レビューSHA 707fefe47717dbed4afd3a9e266ced9a55f9d06b、transcript SHA-256 c92adf14894b93511e52ae418bed22d2370c1893a72d1175556b645a0fa3d341。結果 review_status=fail, P0=0/P1=1/P2=0/P3=0。source reviewerはGPT-5.6 Sol / Extra High。
  - 独立I05-PLAN-008 reviewer: /root/issue8_plan008_gpt6_max_review。GPT-6 Astra / Maxを要求したがpickerの直接証拠はなく、実使用levelはunknown。結果 review_status=fail, P0=0/P1=1/P2=1/P3=0、production implementation可否はno。
  - 完全なsource-native review batch: .workbench/luna-max-implement/issue8-nextjs-snapshots/evidence/707fefe-current-review-batch.md、SHA-256 901611b6ca9d3310f9501019083602fc142c6fdf8f7bf0a1ba9b0ee7a4023ac1。
  - Current candidate: f47e5bb55cba52eb19c0fab6e958d93ca5b8175b。Strict analyst session required-strict-github-connector-verificati-1059でGitHub branch tipとのbyte-for-byte一致を確認。Commit tree dd97babc4d8624f1629efbf72e6de0497a043ca3、parentはレビュー候補707fefe。
  - 707fefeからf47e5bbの変更pathは前回分析Artifact一件のみ。Product source、schema、tests、Requirement、Design、Planは不変。ただしsource reviews自体はf47eで再実施されていない。
  - f47eの検証記録: full suite 1590 passed, 1 skipped、package-applicability unit 31 passed、選択contract 18 passed、Plan-001 registry 2 passed、Ruff/format/mypy/SpecDock/diff check pass、pinned HTML/PlantUML 8/8 browser render pass、GitHub Actions run 35619946633は7 jobs success。これはanalysis packetとWorkbench state記録の証拠で、本分析中に再実行していない。
  - Strict分析入力packet: .workbench/luna-max-implement/issue8-nextjs-snapshots/evidence/20260923-review-findings-analysis-packet.md、SHA-256 d4cc2623b6c35e01afb8cc47d6bf6aadd841f91a923f3b379679c9b621748d88。
  - Strict analyst transcript: Oracle session required-strict-github-connector-verificati-1059、transcript SHA-256 fa8664c41785d08570853f13e8ded558b7884b183e75dc24d415fb84c1d07c5f。Oracle metadataはモデルgpt-5.6-sol、推論Pro。今回のPro pickerはverified、model pickerはskipped/unverified。継続元session 1058と同一conversationであり、1058はGPT-5.6 Sol / ProをUI verification済み。このfollow-upはGPT-5.6 Sol / Proを指定して実行されたが、今回のmodel picker自体の再検証はない。
  - 今回のStrict分析依頼はread-only。以前のIssue #8作業承認はtarget-completenessのcanonical意味変更を採択したものではない。

## Synthesis

- 一致する事実と未確定事項:
  - **RC-OBS-001 — Strict S1 / source-read observed-prefix loss (source-native P1): 妥当で親gateをblockする。** 実source_read failureではresult.sealが存在し、provenanceはsource/config/limits/source-planをobservedとする一方、request-independent publication projectionは同じ値をnull化する。これはCurrent v1の「failure stage以前の観測prefixを保持し、後続suffixだけをnullにする」に違反する。到達matrixはno-proof-root / unsafe-proof-root × 4 selectors。First incorrect layerはreference implementation / generated projection、primary routeはimplementation-remediation。Adapter requestなし、semantic target resolutionを捏造しない、explicit target identity保持、failure code/status/exit/artifactなし、read-once/redactionを維持する。
  - **RC-TGT-002 — GPT-6 G1 / request-bound pre-response target completeness (source-native P1): renderer-validator不整合は実在するが、正しいpublic意味は未決でblockする。** Validated requestとexplicit targetがあり、response decodeまたはvalidation failureでvalidated semantic responseがないとき、rendererはrowsを空にし、validatorはrequest targetとのkey完全一致を要求する。4 selectors × 2 failure stages = 8経路で再現し、targetless controlはpass。First incorrect layerはRequirement / canonical design / public data semantics、primary routeはrequirement-decision-required。I05-REQ-004はvalidated responseからtarget completenessを検証すると定めるが、validated semantic response前のrowsを定義しない。Schemaのclosed failed-reason enumにも「未評価/response unavailable」はない。これは707fefeで新規発生したregressionではなく、baseline c6b7にも存在したreadiness gap。
  - **RC-CFG-003 — compiler-option parity (source-native P2): 妥当だがreport-only / non-blocking。** strict:[]、declaration:"yes"、lib:"ES2022"をproductionはfail-closedに拒否する一方、referenceはCompleteSourceSealとして通す。Primary routeはout-of-scope-follow-up。RG-02は現scope外で、今回の修正対象に含めない。
  - **RC-FRESH-004 — f47e5bbへのrequired same-reviewer evidence不足: material coverage gap、severityなし。** 現候補にfull tests、CI、HTML/PlantUML evidenceはあるが、Strictと独立GPT-6のレビューは707fefeに対するもの。Artifact-only差分で対象codeは不変だが、これはfresh current-SHA reviewの代替ではない。I05-PLAN-008 readinessを引き続きblockする。
  - S1とG1は両方pre-response publicationに関わるが、同一root causeではない。S1は既観測値を失うimplementation defect、G1は未実施のtarget evaluationをpublicにどう表すかというcontract gapである。
  - Current candidateのgreen tests、CI、HTML/PlantUMLはcoverage evidenceであり、未assertのsemantic contradictionやsame-reviewer closureを反証しない。Issue #8全体、production Node/OS/package/CLI-to-Artifact完了は認定されていない。
  - 親policyではP0/P1またはmaterial contract gapがPlan-008をblockし、P2/P3はreport-only。I05-PLAN-002..007の開始およびIssue completionは未許可。

## Options and trade-offs

- 選択肢と利点・制約:
  - **Option A — 未評価rowsを生成しない（GPT分析の推奨、未採択）。** Validated semantic responseとtarget-resolution proofがないpre-response failureではtarget identityをrequest/configに保持し、public target_completenessは空にする。complete/failedのどちらも推測しない。Schema shapeとreason enumは維持でき、false semantic resolutionを避ける。ただし空rowsは「targetなし」と「targetはあるが未評価」の両方を表し得るため、consumer interpretationとcanonical wordingを明示する必要がある。
  - **Option B — unresolved / not_evaluated public variantを追加する。** Target identityとevaluation stateを明確に分けられる一方、schema/discriminated union、compatibility、consumer実装、version/migrationを決める必要があり、current bounded scopeを超える可能性が高い。
  - **Option C — 各targetをfailed rowにする。** 現行reason enumに該当する理由がなく新reasonが必要。「応答全体が不成立」と「個別targetがsemanticに失敗」を混同するため非推奨。
  - 推奨はOption Aだが、採択はユーザー/authority ownerの判断である。必要なら空rowsの外部consumer上の意味・互換性を確認し、canonical wordingを採択するまでは実装しない。

## Reflection

- 本Artifactの判断案は未採択であり、今回Requirement / Design / Planまたはaccepted ADRへ反映しない。採用する場合はユーザーの明示判断後に正本へ再記述する。
- 次に必要な判断は、request-bound pre-response failureにおけるtarget completenessをOption A/B/Cまたは同等の具体的意味で決めること。提案は未採択で、正本へ反映していない。
- その判断とbounded implementation authorizationの後、S1と採択済みG1意味をreference-contract修正として処理し、clean pushed SHAでFirst Red/focused regression、schema/reference/full suite、quality gates、CI、pinned diagramを確認する。
- Strict reviewer session 1057と独立GPT-6 reviewerが同一post-change SHAを再確認し、P0=0/P1=0/review_status=passおよびmaterial coverage gapなしになるまでproduction I05-PLAN-002..007を開始しない。
- RC-CFG-003は本gateではreport-onlyのまま扱う。
- **実装handoffは未認可。** 今回は分析のみ。Canonical Requirement/Design/Planは変更せず、本Artifactもdraft/evidenceのadvisory記録とする。GPT提案は自動で正本にならない。
