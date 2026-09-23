---
種別: disc
ID: "20260923t115713z-disc"
タイトル: "Issue #8 I05-PLAN-008 Request-Origin Sealing Review Closure"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-09-23"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: []
reflected_to: []
---

# Issue #8 I05-PLAN-008 Request-Origin Sealing Review Closure

このartifactはI05-PLAN-008の特定候補に対する実装・検証・レビュー証拠を記録する。Current v1 Requirement/Design/Planに対するadvisoryな証拠であり、Issue #8全体またはproduction実装の完了認定ではない。

## Candidate and review identity

| 項目 | 値 |
| --- | --- |
| repository / branch | `chemitaro/code-structure-viz` / `iss-00008-generate-nextjs-component-snapshots` |
| 固定点 | `c6b7f161c4971c620f221c3faa82098ee3510be6` |
| candidate SHA | `dedade1b9821ae7fbc732c6b983d315b013b3d81` |
| reviewed range | `c6b7f161c4971c620f221c3faa82098ee3510be6..dedade1b9821ae7fbc732c6b983d315b013b3d81` |
| Strict session | `required-strict-github-connector-verificati-1072` |
| Strict transcript SHA-256 | `d4d72cec2352f50542860c11e9ff7de83f514bd89ada56251cc9a13ca6ad63ab` |
| Strict selection evidence | GPT-5.6 Sol / Extra High。モデル・推論レベルともbrowser pickerでverified。 |
| Independent GPT-6 reviewer | `/root/issue8_plan008_gpt6_rereview_f29` のcandidate-specific follow-up。 |
| GitHub Actions run | `35856260313`、candidate `dedade1...`、`completed/success` |

Review前後でclean worktree、local HEAD、configured upstream、live branch tipがcandidate SHAへ一致した。Strict reviewはfresh browser conversationであり、responseはvalid JSON、`review_status=pass`、findingsなし、confidence `0.98`。GPT-6 reviewerも`review_status=pass`、P0/P1/P2/P3すべて0、material coverage gapなし、findingsなしを報告した。GPT-6 follow-upのmodel/effort turn telemetryは得られていないため、そのpicker verificationは主張しない。

## Finding disposition

Base `8de65d4e61052aea3ccd81941da252767f91c8b5`でのStrictとGPT-6は、同じreachable P1を報告した。Bのvalidなpre-response publication contextの`observation_provenance.observed.request`だけをAのrequest observation rowへ置き換え、contextのpublic request/config/targets/run fingerprintはBのままAのdecisionにattachすると、request identityの異なるpublic outputが生成可能だった。GPT-6は恒久回帰testの不足もmaterial coverage gapとした。

Strict findings-analysis session `required-strict-github-connector-verificati-1071`は次のように裁定した。

- Root cause group: `RG-TGT-001` — pre-response publication authorityがowning validated requestへtransitively sealされていない。
- Classification/route: `implementation-remediation`。
- Authorized boundary: `tests/contracts/next_reference_validation.py` と `tests/contracts/test_next_contracts.py` のみ。
- Canonical Current v1 Option Aから、owner request/source sealに基づく完全なpublication-context照合が一意に導ける。人間の意味判断・schema/API/format変更は不要。
- GPT-6のP1とcoverage gapは同じroot-cause invariantの未閉鎖を示す独立blockerであり、別root causeへ二重計上しない。

Analysis transcriptは `/Users/iwasawayuuta/.oracle/sessions/required-strict-github-connector-verificati-1071/artifacts/transcript.md` にあり、SHA-256は`258cc8f1cc43e420f9fd3eb77c78ad538346f16cd12a7fa988658b42a7da41e5`。Pro推論レベルはverifiedだが、このfollow-upのmodel pickerはskipped/unverifiedであり、GPT-5.6 Solの使用をverifiedとは扱わない。

## Correction and regression contract

`PreResponseFailureDecision`のaggregate construction/reconstruction boundaryで、context source sealとowner requestの対応を検証し、owner request/source sealからpublic config、public request、semantic rows、run-fingerprint inputsを独立導出してsealed publication context全体と照合した。既存のrequest-public-config生成もhelperへ集約した。projectionで不正contextをowner側へ書き換える修復はしない。

恒久回帰testはtargetが異なるA (`path:src/Button.tsx`) とB (`path:app/page.tsx`) を作り、Bのrequest observation rowだけをAへ差し替える。次の8経路をaggregate construction時点で拒否する。

| construction | selectors |
| --- | --- |
| direct constructor | selector省略、`manifest`、`next:semantic-json`、`next:plantuml` |
| `dataclasses.replace` | selector省略、`manifest`、`next:semantic-json`、`next:plantuml` |

同一requestのvalue-equivalentなpublication contextはobject identityを要求せず、公開bytesまで受け入れる。proof-backed TARGET、explicit-target NotApplicable complete-empty、targetless early failure、既存failure/status、source-read observed-prefix、およびstage/code・response timing・diagnostic/count aliasの境界は保持する。

## Red/Green and quality gates

| Gate | 結果 |
| --- | --- |
| First Red at `8de65d4` | 新規matrixが8件すべて`DID NOT RAISE`でfail |
| Focused regression + adjacent positive/negative | `24 passed, 518 deselected` |
| `uv run pytest tests/contracts/test_next_contracts.py -q` | `542 passed` |
| `uv run pytest tests/contracts/test_json_schemas.py tests/contracts/test_next_contracts.py -q` | `661 passed` |
| `uv run pytest -q` | `1662 passed, 1 skipped in 211.12s` |
| `uv run ruff check .` | passed |
| `uv run ruff format --check .` | passed; 169 files already formatted |
| `uv run mypy src tests` | passed; 145 source files |
| `./spec-dock/scripts/spec-dock validate` | passed; `nodes=10` |
| pinned PlantUML HTML validator | static 8/8、browser render 8/8、click/keyboard/bounds/focus/dismissal checks passed |
| GitHub Actions `35856260313` | 7/7 jobs success: minimum, macOS, latest, validate, trusted-profile-contract, product-contract-scope, package-offline |
| `git diff --check` | passed |

Pinned HTML validatorのsandbox内Chrome startupはtimeoutしたため、同じlocal-only commandをexecution permission付きで一度実行し、全gate passを確認した。レビュー開始前にcandidateはcommit/push済みであり、fetch後にHEAD/upstream/origin SHAを照合した。

## Scope and readiness boundary

Candidateのproduct diffは上記二つのreference-contract filesだけ。Requirement、Design、Plan、schemas、catalog、production source、dependency/lockfile、packaging、public formatは変更していない。Strictレビューはこのexact SHAでP0/P1を認めず、GPT-6レビューもmaterial coverage gapなしとし、I05-PLAN-008のcontract-readiness gateは前進可能となった。

この結果が証明しないもの:

- Production adapter、Node worker、OS/process boundary、wheel/sdist resource behavior、またはCLI-to-Artifact runtime。
- I05-PLAN-002〜007の完了。
- Issue #8の最終受入れ、Final Quality Gate Strict v2、またはIssue完了。
- GPT-6 follow-upのmodel/effort UI picker verification。

次の実装はPlanの順序に従いI05-PLAN-002へ移る。production実装とIssue全体のfinal gateは未完了のままとする。
