---
種別: disc
ID: "20260924t064155z-disc"
タイトル: "Issue #8 I05-PLAN-008 Findings Analysis (GPT-5.6 Sol Pro Strict)"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-09-24"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: []
reflected_to: []
---

# 20260924t064155z-disc Issue #8 I05-PLAN-008 Findings Analysis (GPT-5.6 Sol Pro Strict)

## Inputs

- 対象: `chemitaro/code-structure-viz`, branch `iss-00008-generate-nextjs-component-snapshots`, exact candidate `457b6c0897fd21bc4b8fb3eb3054b59c480af782`; fixed point `977feb02c05b908d5a25a97181138abe1ef54bd9`.
- Live GitHub branch SHA と local HEAD の一致、clean worktree、CI 7/7 success をStrict preflightで確認した時点のレビュー。対象は依存追加の要否ではなく、Issue #8のI05-PLAN-008 readiness gate。
- ChatGPT-Use Strict code review: fresh browser conversation `issue8-plan008-readiness-review` (conversation ID `6ab4b8cc-60e8-83e8-a981-54c051d82d96`), UI-confirmed model `GPT-5.6 Sol` (`gpt-5.6-sol`) and reasoning `Pro`; result `fail`, `P0=0/P1=1/P2=0/P3=0`, confidence `0.97`. The model and reasoning selection are separate; “Pro” is the reasoning effort. Output SHA-256 `1d9f377d9a99132cd1b13c5558baba4830fa4a050f0d02ae9be4b053fd93e69d`.
- 同一候補への独立GPT-6 Max read-only review: result `fail`, `P0=0/P1=2/P2=0/P3=0`; reviewerは編集・Git変更を行っていない。完全なsource-native出力と再現資料は ignored Workbench packet `issue8-i05-plan008-findings-packet.md` に保存。
- Strict findings adjudication using `chatgpt-analyze-review-findings-strict`: Oracle session `required-strict-github-connector-verificati-1107`, requested/UI-verified `GPT-5.6 Sol` / reasoning `Pro`; analysis output SHA-256 `e9ce81aa76fbc043bd368ce92b1ce73f6c23cdd0cd31544c9c95155f36af2b6b`. This separately adjudicated all three findings as valid, reachable, distinct, blocking, and not requiring a human decision within current-v1 scope.
- 現行正本: Issue #8の`requirement.md` / `design.md` / `plan.md` Current v1、現在のschema、reference validator、fixtureおよびcontract tests。Historical Round 23は現行権威ではない。

## Synthesis

「依存材」の根本原因は、第三者Python/npm依存の不足ではない。先行するStrict dependency analysis (`issue8-dependency-root-cause`, `gpt-5.6-sol` / UI確認済み`Pro`, transcript SHA-256 `162e1dcc5edd1de5f32e1366423b70616f8d4b65b5bb0d9dd3a0082c1f88c1ac`) と、今回の正確な候補上の実装・schema・test証拠は、実装前readiness契約に残る3つの別個の穴を示す。CIや通常テストがgreenでも、当該adversarial経路やcoverage registryの実行可能性を証明しない。

| Finding | 妥当性・根本原因 | 主経路 |
| --- | --- | --- |
| `G6-P1-1` | **有効・到達可能。** root package以降の6種のpre-seal source read failure (`TOO_LARGE`, `TOO_MANY_FILES`, `UNSAFE_PATH`, `SYMLINK`, `NON_REGULAR`, `RACED_MISSING`) は `SourceAcquisitionUnavailable(source_read)` になれるが、早期観測prefixが付かず、現行decision constructorがsource_readにはsealを必須とする。4 selectorすべてでpublicationへ到達できない。根本原因は、provenance規則がsource_readを一律「seal済み完全prefix」と仮定し、実際に観測された早期prefixを表現しないこと。 | implementation-remediation |
| `G6-P1-2` | **有効・到達可能。** 有効なearly `source_control`またはsealed `source_read` failure decisionの `diagnostic.path` を未読pathにreplaceでき、全selectorでdomain/root manifest/stderrへ漏れる。根本原因は、diagnosticのpath文法・許可は検証するが、観測されたfailure evidenceへの同一性をdecision/publication時に再束縛していないこと。 | implementation-remediation |
| `STRICT-P1-1` | **有効。** `round22.rg-01` は単一producer/vector/mutation/testだけをmapする。新たにnormativeになった不等な2つのvalid direct `next` declarationとpackage failure分類matrixの既存testsはregistry producer/vector/mutation/substantive mappingに接続されていない。実挙動が正しくても、現行G09 bidirectional registryはこれらの回帰を検出せずpassし得る。根本原因は、normative criteriaとexecutable coverage registryの同期漏れ。 | test-remediation |

分析者は3件をそれぞれ別root causeとして扱い、重複とは判定しなかった。`I05-PLAN-008`のstatusをblockし、これらの修正と新exact-SHAでの双方のfresh reviewが必要。人手による要件判断は不要と判定された。許可は既存current-v1を満たすための限定修正であり、production adapter/NodeやIssue完了の許可ではない。

### 推奨設計（current-v1の範囲内）

1. pre-seal `source_read`は既存 `request_independent_failure` kindのまま表現する。実際に読んだapplicability packageだけをprefixに記録し、失敗したread observationを保持する。config/source/limits/source-plan/その他のsuffixは`unobserved/null`のままとし、seal・request・runtime・semantic rowsを捏造しない。既存のrequest-independent payload-unavailable / exit 3 publication経路へ投影し、6 failure kind × 4 selectorを検証する。sealed read failureは現在の完全prefixのまま。
2. diagnostic pathのauthorityを読取証拠に結び付け、decision construction、dataclass replacement、最終public projectionの境界で未観測pathをrejectする。公開の許可path semanticsを変えず、別のcaller-writable path authorityを増やさない。
3. 現行`round22.rg-01`の実producer、validator、positive/negative vectors、mutation、substantive testsのmappingを増補し、新しい各branchを独立に壊したときregistryが失敗することを示す。不等dual-declaration testとpackage failure matrixを現在のRound22 registryに追加し、historical Round23を再利用しない。件数が実際に変わる場合だけRequirement/Design/Planの現行件数記述を更新する。

変更候補は `tests/contracts/next_reference_validation.py`、`tests/contracts/test_next_contracts.py`、`tests/fixtures/next_contract_vectors.json`、provenance/run/config schemasとそれらのcross-checkである。`next-publication-decision-v1.schema.json`は既存の`payload_unavailable`, null response, no artifacts, unavailable stdout, exit 3が適合するため、Redが反証しない限り変更しない。

## Options and trade-offs

- **推奨: 既存v1型のobserved-prefixと証拠束縛を完成させ、executable registryに不足caseを登録する。** Public discriminator・code/stage・schema versionを増やさず、既存のfail-closed publication境界を利用できる。テストは詳細になるが、既存契約内で閉じる。
- **却下: 全pre-seal failureをsealed failureへ昇格する。** 未観測のsuffixやsource planを偽造し、evidence provenanceを弱める。
- **却下: 新しいprovenance kind/codeまたはschema versionを追加する。** Strict分析では現在のv1のkind/fieldsで十分とされ、不要な公開契約変更となる。
- **却下: registryを静的fixtureや歴史的Round23で埋める。** current producer/validator/mutation/testが結び付かず、G09の実行証拠にならない。
- **却下: 既にgreenのfull test/CIだけを根拠に進む。** その証拠は2つの具体的counterexampleとregistry mapping欠落を覆わない。

Stop condition: 正しい修正に新しいpublic kind/field/schema identity、stage/code/path publication semantics/security/privacy/compatibilityの変更が必要と判明した場合、または既存payload-unavailable projectionがpre-seal経路を表現できないとRedで判明した場合、通常実装を止め、必要な人間の判断を返す。

## Reflection

- この分析はevidence/advisoryであり、Requirement/Design/Planのsemantic authorityを置換しない。現行のG09・I05-PLAN-008受入条件と矛盾があれば、履歴ではなくcurrent-v1と実schema/reference/testsを優先する。
- 実装は一つずつTDD Red→Greenで行う。必須coverage: 6 pre-seal source failure × 4 selectorの完全publication、source_control/sealed source_read双方のdiagnostic path mutation拒否、RG-01の各新branchに対するpositive/negative vectorとindependent mutation、criteriaとsubstantive testの双方向mapping。
- 最終gate: focused contract/schema tests、full pytest、mypy、ruff、SpecDock、`git diff --check`、current registry execution、exact-SHA CI。候補をcommit/pushした後、ChatGPT-Use Strictと独立GPT-6 Maxの双方に同じfinding scopeをfresh exact-SHA reviewさせ、`P0=0/P1=0/review_status=pass`で初めてI05-PLAN-008を解除する。そこから先もproduction unitsとIssue final gateは別途必要。
- 分析時点のstatus: three findings open. このartifactはレビュー分析時点の証拠を固定したものであり、後続の修正・テスト・再レビュー結果を記録または主張しない。I05-PLAN-008通過やIssue #8完了も主張しない。
