---
種別: disc
ID: "20261001t105753z-disc"
タイトル: "a-runtime-failure-prefix-v2-contract-closure"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-10-01"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["requirement.md", "design.md", "plan.md", "20261001t040546z--a-runtime-contract-analysis-result.md"]
reflected_to: ["design.md", "plan.md", "report.md"]
---

# 20261001t105753z-disc a-runtime-failure-prefix-v2-contract-closure

採択済みAのA02 failure-prefix契約を継続します。referenceデータの保持・照合であり、production/実TS/A03の認定ではありません。

## Inputs

- 開始checkpoint: clean/pushed `9a151f131f6d3977cd25469e2e6218571aabf19f`。local HEAD/upstream/live GitHub SHA一致を確認。直前sliceは48 focused / 465 related、Ruff/format201/mypy166、SpecDock10 nodes、doc-pointer/diff-checkがpass。
- authorityはCurrent R/D/Pとaccepted A。累積Strict固定点は`f4159066f3954454ad2f0c2701fa54bf1bc7bc4a`。旧v1/production/依存/lockfileは変更しません。

## Synthesis

- 既存catalogのprocess start不能はNODE-002、I/O/process failureはNODE-004、bounded byte/structural breachはLIMIT-003、malformed/echo/protocol違反はPROTOCOL-001です。actual retained evidenceからbranchを閉じ、成功defaultを付けません。
- observed control/versionは後続failureで消さず、partial/rejected frameから補完しません。捕捉interruptは普通のpayload-unavailable publicationではなくcore interrupted/exit130へ渡します。
- `RejectedResponseFrameV2`はsame limits、元bytesのhash/length、bounded decoderの実measurement、closed stage/code/reasonだけを保持します。raw body/parsed object/controlは保持しません。runtime joinはactual spawn、complete stdout/EOF、全byte length、cap内、control未観測とframe-invalid causeを必要とします。constructor/duck input、別limits、偽count/incomplete stdout/blind controlを拒否します。
- actual capture capとraw response capが同じ16 MiBなので、capture +1をdecoderへ渡しません。standalone decoderのraw +1 testは分類順だけを検証し、実executor/capture gateの代用ではありません。per-array breachのtotal countは実scannerの100000、aggregate breachは100001であり、失敗時の未走査itemを測定値へ足しません。

## Options and trade-offs

- 新semantic identityや新diagnostic catalogを増やさず、採択済みv2 recordsと旧wire非依存JSON grammarを結合します。free label/boolean/hashでは失敗証拠をmintせず、typed immutable ownerとactual measurementを必要とします。

## TDD / verification

- stage/spawn、capture cap+1、write/read、binding/exit、echoのprovenance branch欠落を各focused REDで確認し、最小catalog対応でGREEN。unspawned post-spawn cause、matching exitのfalse mismatch、valid/missing frameのfalse echo violationもRED→GREENで拒否します。
- rejected-byte API欠落、schema違反が例外のみ、raw/depth/array/string breachesの誤PROTOCOL分類、same captureへのrejected owner join欠落を各REDで確認し、typed union/measurement/joinsの最小変更でGREEN。interruptがordinary transport failureになったREDをterminal kindへ修正しました。
- rejected frame focusedは21 passed（4.56s）。新40 testsを含むruntime/source/旧request/schema関連selectionは505 passed（61.64s）、original job exit0。同じquiet jobを重複実行していません。
- Ruff全対象/format（202 files）、mypy（167 source files）がpass。format後にnegative bytearray testのtype-ignoreが別引数行へ移動したためmypyが2 errorsとなり、該当引数行へ戻してGREEN。実行behaviorは変えていません。巨大byte-vectorの初回param IDは表示が長くなったため短い明示IDへ変更しました。
- SpecDock sync（active iss-00008不変）/validate（nodes=10）、Current doc-pointer（1 passed）、diff-checkがpass。明示パスstaging→complete staged diff→通常`commit-codex -a`→pushのcheckpointへ進みます。new SHAとclean upstream一致は次sliceのInputsへ保存します。
- 全A02・full-suite・actual OS/TS・A03は未完了です。

## Reflection

- 完了した契約をCurrent Design/Plan、契約文書と薄いReportへ反映します。remaining reader-owned prefix/public exact refs/full A02 gates/A03/productionは継続します。
