---
種別: disc
ID: "20261002t152812z-disc"
タイトル: "SI-04 full Core参照実装・selected cardinalityと受入対応"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-10-02"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["20261002t135356z-disc", "20261002t143402z-01-disc"]
reflected_to: ["plan.md", "report.md"]
---

# 20261002t152812z-disc SI-04 full Core参照実装・selected cardinalityと受入対応

オプションAの既存仕様を維持したSI-04 **full Core参照実装の候補**です。元unit baseは`caf38329826ae34f8e3cb330b83b97e0357b7dc5`。仕様の意味、旧reference、source/schema/依存/goldensは変更しません。ローカル検証と独立Strictレビューは別ゲートで、fresh step passまではSI-05へ進みません。Issue全体・productionの完了証拠ではありません。

## Inputs

- [Current Plan](../plan.md)のSI-04、[admission-v3](../../../../../../../../docs/contracts/next-semantic-admission-v3.md)のSI-P01〜07 / SI-N01〜15を受入れ境界とします。仕様認証はbcae954、先行SI-03認証は23072c2のままです。
- [中間Core候補](20261002t135356z-disc-si04-core-intermediate-reference-evidence.md)、[selected cardinality補足の採用判断](20261002t143402z-01-disc-si04-selected-cardinality-brief-adoption.md)。補足は独立コードレビューではありません。
- 実装は`tests/contracts/next_semantic_core_v3_reference.py` / `_validation.py` / `test_next_semantic_core_v3.py`の三ファイルだけです。実DescriptorAnchoredSourceReadSessionによるcomplete source seal、retained 0.2.0 assets、request-v2 / transport ownerを使います。child semantic値とcompiler bytesは参照用fixtureであり、actual TypeScript analyzerの実行ではありません。
- 元Red/Green・最終selectionログはignored Workbench `luna-max-implement/issue8-nextjs-snapshots/evidence/si04-*`へ保存します。以下はその追跡可能な要約です。

## Synthesis

### 実装方法と通常経路の保護

通常のSI-03 `full_module_owners_v3` / `resolve_discovered_v3` / source seam factoryは不変です。正規経路は全取得source、private D、公開M、full IR / roots / causal / typed fixed point、same-seal export / source graph / target、owner-closed File partition / Project projectionを検証し、immutable same-owner decisionとcompatibility-v3を保持します。

selected `missing` / `component_only` / byte-identical `duplicate`だけは内部の**データview**を使います。candidateやModuleを偽造せず、child bytesを修正しません。取得sourceは親requestから再構成し、source discovery exactly-once / `record`key省略を要求します。proof-only Moduleをpublic Mから落としたことは`missing`の根拠になりません。

| 例外 | 保持する実データ / 検証 |
| --- | --- |
| missing | 選択Button Module / 従属semantic rowを欠いた11 unique D。元の六取得Fileは保持。欠落sourceもphysical syntax / incoming reexport graphへ参加し、偽owner observationを作らない。 |
| component_only | 同じsourceと12 unique D。Component.module_idの正確な選択欠落だけ許可し、Props repository referenceや他recordのdanglingは許可しない。orphan Componentをexport成功へ昇格しない。 |
| duplicate | 同一Button Moduleのraw二行を保持し、raw Modules=4 / published=18、Dは17 unique。選択されたcanonical byte-identicalな余分のModule行だけvalidation viewでまとめる。raw digest/order/countは別に照合し、discovery重複・異なる内容・選択外重複を拒否する。 |

例外でもunrelated source ownership / partition / Project projection、full proof / IR / refs、source-derived export、locality、target rowsを全て検証した後だけTARGET-001を返します。source seamは`None`、model/entity measurementも`None`です。available公開条件を緩めるcertificateに使えません。default targetは既存の全program File選択を維持し、mixed targetsの安全側IDsは個別解決して消しません。

### TDDと既存挙動の保護チェック

| cycle / control | 元jobの結果 |
| --- | --- |
| Cycle31 selected missing | lower owner成立後のintended Red 1 failed/0.71s → Green 1 passed/0.64s。 |
| Cycle32 component-only | intended Red 1 failed/0.77s → Green 1 passed/0.65s。 |
| Cycle33 identical duplicate | strict raw uniquenessによるintended Red 47229:1 failed/1.06s → Green 1 passed/0.74s。 |
| Cycle34 implicit selection / safe sibling | target proofのintended Red 1 failed/0.81s → Green 1 passed/0.74s。 |
| Cycle35 wrong private Module kind | classifierのKeyErrorをpublic inspectionで観測:1 failed/0.88s → bounded PROTOCOL-001 rejection:1 passed/0.69s。private Module kindをclassification前に確認する最小修復。 |
| mixed targets / exception複合負例 | 29655:27 passed/55 deselected、17.87s。既にGreenの保護チェックでありRedとは表記しない。 |
| selected以外 / contradictory duplicate / default残二kind | 14593:4 passed/85 deselected、2.29s。 |
| actual10001 / invalid proof / proven selected_taint優先 | 25709:3 passed/86 deselected、123.90s。小さい代替cap無し。独立decision/rejection validatorも同じ実ownerで再実行。 |
| 二Project・片方全File proof-only / 独立safe target | 17411:2 passed/89 deselected、2.36s。最初の2 failedはfixture failed_filesの非canonical順であり、Redではない。fixture順だけ訂正しguard不変。Project A空 / B四File保持、published8 / proof-only6 / accounted14 / entity1のliteral。 |
| represented unsupported frontier | 95257:3 passed/91 deselected、2.34s。actual acquired unresolved dynamic import、unknown relation / owner diagnosticがある時だけcomplete。count/diagnostic欠落は拒否。 |
| missing＋unrelated File root / Props closure | 81398:6 passed/94 deselected、4.04s。mandatory File seed、causal、typed taint/root kindを省略するとTARGETへ逃げず拒否。 |

### 受入れ対応（実装箇所と保護テストのcensus）

Coreテスト名は`test_v3_core_` prefixの以下suffixを指します。SI-03テストは変更せず、通常Coreのsource seamの独立再検証と合わせて回帰します。下位guardの証拠をactual TS/OS/CLIの証拠へ昇格しません。

| ID | 現在の観測可能なチェック |
| --- | --- |
| SI-P01 / P02 | `keeps_localized_acquired_file_failure_partial_safe` parse/read、`keeps_independent_safe_target_available_with_private_owner`、same-seal source graph/locality。 |
| SI-P03 | `prioritizes_proven_selected_file_failure_over_source_locality`、`actual_record_limit_preserves_proof_and_target_precedence`、三cardinality public admission / exact target rows。 |
| SI-P04 | `keeps_project_when_every_acquired_file_is_legitimately_proof_only`、`empty_project_membership_never_erases_an_independent_safe_project`、SOURCE-003 / open dependency負例。 |
| SI-P05 | `preserves_complete_empty_and_safe_nonprogram_files`、selection-only二reason、`unsupported_owner_needs_a_represented_frontier_not_a_failure`。 |
| SI-P06 | actual10000/10001、entity500/501、same-owner独立validators、fresh getters、ten-key ASCII compatibility KAT。SI-03のpartition KATも不変。 |
| SI-P07 | 三nonFile rootsの`keeps_untainted_file_private_with_its_failed_module` / independent safe target、File T外とexcluded/failed、全record / safe entity literal。 |
| SI-N01 / N02 | 全取得exact discovery / one disposition: SI-03のsource exactly-once / disposition群、新`cardinality_is_not_an_exemption_from_full_proof`のsource omission / semantic duplicate。 |
| SI-N03 / N04 | SI-03の全public source field / metadata / payload / null群、normal Core同owner再検証とexception source payload compound。 |
| SI-N05 | full typed fixed pointのcausal/root controls、`missing_target_keeps_full_unrelated_file_root_proof`。公開subsetやcardinality failureでseed/edge/taintを省略不可。 |
| SI-N06 / N07 | SI-03任意File/Module除外 / counts群、Core actual capsとproof優先、新unrelated File exclusion / raw Module count compound。 |
| SI-N08 | Core private Props scope / dangling record、component-only Props missing Module負例。通常source seamの15位置×D/M四view type-reference closureは不変。 |
| SI-N09 / N10 | proven targetはno-payload / null measurements、source syntax / binding協調省略・stale/fake witness・coverage偽造拒否。 |
| SI-N11 | complete-only real source seal / nominal owner要求。SI-03 `test_source_reader_prefix_cannot_be_promoted_to_a_complete_inventory_seam`とCoreの別source-owner error propagation。actual early-reader failure routingはSI-07の残範囲で、ここではprefixをcomplete certificateに変換しない境界だけ。 |
| SI-N12 / N13 | SI-03 Project欠落 / cross-project / nonprogram Module guard＋通常Core再検証、二Project保持正例、新full-D normal grammar。 |
| SI-N14 | actual open dependency / reverse importer省略拒否、同seal graph digest/hash導出。free isolated boolをAPIとして受けない。 |
| SI-N15 | 三owner roots / normal SI-03 eligibility、exception複合source/full proof、private Module kind bounded rejection、unselected/contradictory duplicate拒否。 |

### 最終候補のローカル検証

code-only変更は三Core filesに限定します。actual large casesを除外せず、selectionを合算しません。

| selection / 元job | 結果 |
| --- | --- |
| 最終Core全件 / 23462 | terminal exit0、101 passed、254.33s。actual record10000/10001、entity500/501を除外しない。直前94件の79986とは別selectionで、合算しない。 |
| SI-03 / v2 candidate / Core failure / request / exchange五module / 35962 | 278 passed、385.93s。 |
| shared algorithms明示16 selector / 81131 | 52 passed / 637 deselected、54.38s。 |
| Python/SQLAlchemy goldens＋JSON schemas / 11263 | 139 passed、12.33s。 |
| 全Ruff check / format、mypy src tests | check pass、233 files formatted、191 source files pass。 |
| SpecDock / Current pointer / links / diff | local-only sync（active不変）、validate10 nodes、Current pointer1 passed / 688 deselected、0.16s、新Artifact local links4/4、diff-check pass。 |

## Options and trade-offs

仕様の変更や新しい製品判断はありません。実データに対するprivate validation viewで限定target cardinalityを扱う方法を採り、通常source seamの所有権を維持しました。既存v2 whole-certificate、旧固定export facade、偽Module / fake seal / fake candidate、caller cacheを証明にする方法は使いません。

raw duplicateだけの限定count差を、normal unique Dの全体例外へ広げません。例外の元source Fileがinputに存在しても、public-v3のavailable emissionには使用できません。公開schema/dispatcher/run/provenance/candidatesと最終producerのexact refsはSI-05以降で別に閉じます。

## Reflection

Plan/Reportへ進捗と受入対応だけ反映します。元caf3832からpublished final candidateまでのfresh Code Review Strict（GPT-5.6 Sol / Extra High、主担当が直接実行）でvalid passするまでSI-04は未認定です。finding/重要coverage gapは別の専用分析へ渡し、P0/P1のみin-scope修復します。P2/P3を新しいrevision条件にしません。全A02/A03、production / actual TS / 両OS / CLI / package / Final / Issueは未完了です。Browser Useによるjob監視やsubagentは使いません。
