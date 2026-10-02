---
種別: disc
ID: "20261002t135356z-disc"
タイトル: "SI-04 Core参照モデルの中間実装と残るselected限定例外"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-10-02"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["20261002t121924z-02-disc"]
reflected_to: ["plan.md", "report.md"]
---

# 20261002t135356z-disc SI-04 Core参照モデルの中間実装と残るselected限定例外

これはSI-04の**中間実装checkpoint**です。仕様の意味や受入れ条件を変更しません。全SI-04、SI-05、A02/A03、実TypeScript/OS/CLI/package、Final、Issue全体は未完了です。

## Inputs

- Current Requirement/Design/Plan、二つのaccepted source/owner-closed ADR、admission-v3 / semantic-v3 / compatibility-v3を維持します。仕様認証はbcae954、先行SI-03認証は23072c2の範囲だけです。
- [採用した訂正briefとfirst fixture補正](20261002t121924z-02-disc-si04-full-core-brief-adoption.md)。原unit baseは`caf38329826ae34f8e3cb330b83b97e0357b7dc5`のままです。
- 実装対象は新しい`tests/contracts/next_semantic_core_v3_reference.py`、`next_semantic_core_v3_validation.py`、`test_next_semantic_core_v3.py`。source/schema/旧reference/依存/旧goldensは変更しません。
- 詳細な元job/Red→Green/fixture誤りのログはignored Workbench `luna-max-implement/issue8-nextjs-snapshots/evidence/si04-core-*`へ保持します。このArtifactは追跡可能な要約です。

## Synthesis

### 現在実装した範囲

- 正規0.2.0 assets、completeな実SourceAcquisitionSeal、request-v2/transport ownerから、full Dの型/record grammar、mandatory seeds、exact causal edges、typed fixed point、coverageを検証します。
- export census・direct/string observation・reexport graph/witness・public binding/coverageを、同じsealの実bytesからv3-localに導出します。旧固定corpusのexport facadeをcertificateとして使いません。
- post-acquisition parse/read rootを旧acquisition failureへ注入せず、実sealのresolved/open graphからlocalityを再計算します。SOURCE-003と、source graph上のreverse importerをproofから落として公開する不整合を区別します。
- normal source seamは完全proofの後に保持し、厳密なFile→Module owner条件を維持します。nonFile三rootではFileに偽taintを追加せず、owner Module原因のexcluded/failedにします。
- 完全target proof → target failure → actual全record cap → eligible public export/source unavailable → safe entity gateの順を接続しました。
- nominal admitted/rejected owner、fresh getter、七つの閉じたprotocol reason、actual record+1のtyped metadata、独立再検証を追加しました。予期しないowner/internal errorは子protocol rejectionへ変換しません。
- compatibility-v3を十二key/十key preimageの内部owner bytesとして保持します。独立validatorはproducer helperを呼ばずprofile/runtime bindingから再導出します。新physical schema/public consumerはSI-05です。
- Coreの内部measurementは全recordとsafe entityを分離し、未到達stageはnullにします。公開summary/schemaの追加ではありません。

### TDDと正例の区別

| 境界 | 観測した証拠 |
| --- | --- |
| export syntax/bindingの協調省略・resolution/witness/count/diagnostic偽造 | 各focused Red→minimum Green。新source acquisitionへの変更とstale witnessも拒否。 |
| mandatory causal、private Props scope、coverage affected/frontier/failed-files/unknown-relation/correlation | focused Red→Green。full Dの意味検証を公開subsetで代用しない。 |
| nonlocal source、selected File failure、source reverse importer省略 | focused Red→Green。TARGET-001はSOURCE-003より先。 |
| 実record10000 / 10001、private File/Module/Fact三行を含む | 最初は10001がbare AssertionとなるRed。構造capとtyped actual gateを分離した後、元77673 exit0、2 passed/44.95s。小さい代替limitを使わない。 |
| unknown string export | 実makeValue() bytes。初回はunknown.ts用token hashをvalue.tsへ誤適用したfixture failureで、Redとは数えない。path-bound preimageの独立SHAで訂正後、complete/actual4を返す意図したRed→EXPORT-001/no entity measurementのGreen。 |
| compatibility KAT | 十key ASCII literalをproducer実装前に固定。jq -cS / LF除去 / shasumの独立値は`ecf055ae84276a9209e8cb65addabd0cbf4d882e0b76f54cc6f06208fa95880f`。 |
| 三nonFile roots、localized parse/read、独立safe target、selection-only、complete-empty/非program File、全File proof-only | 既存の実装で最初から通る正例はregression controlと表記し、Redを捏造しない。独立target/empty/別source-owner errorは元70909 exit0、8 passed/4.10s。全File proof-onlyは1 passed、Project空membership/partial-safe。 |
| 実entity500 / 501 | 追加497/498の実取得program filesとModule/router Fact、private value owner、safe Button Componentを用いる。元20860 exit0、2 passed/11.87s。500はpartial-safe available、501はactual501付きLIMIT-005。 |

production source graphはschema-order/一LFのcodecで、semantic CJ15はsort-key/末尾LF無しです。初回のcodec誤用ログを保持し、guardや意味を弱めず正しいsource codecへ訂正しました。

### Checkpointの検証

親HEAD44303da以後の中間working treeに対する結果です。各selectionを合算しません。以下はすべて元jobのterminal exit0で、actual large casesを除外していません。

| selection / 元job | 結果 |
| --- | --- |
| 新`test_next_semantic_core_v3.py`全件 / 9807 | 51 passed、96.95s。実10000/+1とentity500/+1を含む。 |
| SI-03・旧v2 candidate/failure/request/exchange五module / 24737 | 278 passed、335.37s。旧failure guardとSI-03の意味を維持。 |
| brief指定の旧shared algorithm / 75713 | 52 passed / 637 deselected、45.72s。export/taint/type/source/target/budget/Current pointerの明示selection。 |
| 旧Python/SQLAlchemy goldens＋schema / 16970 | 139 passed、8.89s。新v3 schemaを追加したという意味ではない。 |
| 全Ruff check / format、mypy | check pass、233 files formatted、191 sources pass。 |
| SpecDock / diff | local-only sync（active不変）、validate10 nodes、diff-check pass。 |

coherent中間checkpointの検証であり、whole contracts/full pytest、selected例外、SI-04 step review、全Issue認証は未実行・未認定です。将来のpassing candidateのexact-SHA required checksを代替しません。

## Options and trade-offs

通常pathのfull Coreと、selected cardinalityの限定no-payload pathは別です。現checkpointのnormal seamはModule欠落/重複を正しく拒否しますが、仕様で維持する`missing` / `component_only` / byte-identical duplicateの専用TARGET-001経路は未実装です。通常seamを弱める、偽のModuleを補う、v2全certificateへcastする方法は採りません。

残る作業は、payload-free source discoveryを保ちながらこの専用pathの完全proof/型/refs/target/export/無関係ownerを検証し、normal seamをmintせず`source_inventory_seam=None`で利用不能を返すこと、および複合負例/再検証の残acceptanceです。同じBlue authorへ現物に即した実装clarificationを依頼し、既存仕様の範囲で照合して続けます。新しい人間のProduct判断を要求する資料ではありません。

## Reflection

Plan/Reportには中間実装と残る出口条件だけを記録します。元SI-04 baseを維持し、全required evidenceを同じcandidateへ結合したfresh Code Review Strict passまでSI-05へ進みません。主担当のみで実施し、subagent/Browser Useによるjob監視は使いません。
