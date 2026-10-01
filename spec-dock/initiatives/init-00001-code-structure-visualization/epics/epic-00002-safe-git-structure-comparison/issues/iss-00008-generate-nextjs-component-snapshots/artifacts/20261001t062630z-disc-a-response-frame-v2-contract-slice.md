---
種別: disc
ID: "20261001t062630z-disc"
タイトル: "a-response-frame-v2-contract-slice"
状態: "recorded"
作成者: "iwasawayuuta"
最終更新: "2026-10-01"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["20261001t040605z-disc-issue8-a-runtime-contract-analysis-adjudication.md", "20261001t060157z-disc-a-runtime-observation-binding-contract-slice.md"]
reflected_to: ["../design.md", "../plan.md", "../report.md"]
---

# 20261001t062630z-disc a-response-frame-v2-contract-slice

採択済みA/A02-2のresponse-byte部分を閉じたreference evidenceです。Issue/A02全体、production、独立Strictの完了ではありません。

## Inputs

- clean/pushed baseline: `15a0c0a85cb7260acacea6b17e382b28f8fed428`。上流SHA一致を確認して継続。
- 現行AのR/D/P、response control/policy/observation/binding leaf。
- 新`next-adapter-response-v2.schema.json`、`test_next_response_frame_v2.py`、reference producer/validator、`docs/contracts/next-adapter-response-v2.md`。

## Synthesis

- wire rootは一つのschema/control/nullable semantic payload。successだけがpayload必須、4 child failureはnull。runtime binding/compatibilityはparent-owned。
- 通常constructorを拒否し、immutable bytes→bounded grammar→closed shape/control→retained frameの一入口。raw bytesとSHAを保持し、fresh gettersの変更がownerへ戻らない。
- 全raw bytesのSHA、control projection、stdout observed countをprocess recordへjoin。valid SHAだけで別version/control/counterを許可しない。
- source/request/context/trusted/model digest/proof/targetとOS captureは未完了。success shape positiveは明示的な未認定candidateであり、semantic complete_emptyや実解析受入れではない。

## Red → Green / known bytes

- factory欠落のREDからclosed failure frame保持をGREEN。
- duplicate keyを通常JSON decodeが上書きしていたREDから既存bounded grammarへ接続してGREEN。
- mutable入力は旧helperのAssertionErrorを漏らしていた。public TypeError contractのREDからimmutable bytes guardでGREEN。
- raw response join欠落、SHAだけが正しい偽control/count、caller duck ownerのREDから必要なjoin/type checkをGREEN。
- 16 MiB raw exact/+1（whitespace込み）、BOM/banner/二つのJSON/partial、constructor拒否、no mutable projection alias、failure payload null/nonnull拒否、success refsを検証。
- failure byte known SHAは`f0bbb753ad4ae8fa9304279c4075b2388e1b01a11d92d1ae457e23f76551b6ce`。testのliteral bytesを`sys.stdout.buffer.write`し、独立`shasum -a 256`で固定。Nodeを起動した値ではない。

## Verification

- 新wireのfocusedは19 tests。runtime/observation/schema/current-doc pointerを合わせた最終selectionは287 passed（6.56s）。旧全suite/A02全closureの代用ではない。
- `uv run --locked ruff check .`: pass、`ruff format --check .`: 186 files already formatted。
- `uv run --locked mypy src tests`: no issues / 157 source files。初回のnegative型testの誤配置ignore/未注釈fake objectを明示`cast(Any, ...)`へ修正しただけで、runtime拒否条件を弱めていない。
- SpecDock sync `--no-github`: active Issue 8 unchanged。validate nodes=10 pass。
- `git diff --check`: pass。production `src`、依存/lockfile、旧v1 schemasと`next_reference_validation.py`に差分無し。
- 実Node/capture/package build、全semantic chain、fresh independent Strictは未実施。このscopeをA02完了やproduction開始gateとして使用しない。

## Options and trade-offs

- ModuleのInterfaceはraw bytesを受ける通常factoryとreadonly projectionに限定。caller prepare/metadata/statusからframe authorityを構築しない。production execution ModuleのOS lifecycleは後段。
- wire非依存bounded JSON grammarは既存`bounded_decode_json`を再利用する。旧巨大reference moduleへのこのhelper依存は残るが、parser複製/別grammarを増やさず、旧runtime validator/certificateを使わない。旧model/proof/要素 defs参照も維持する意味だけ。
- success shapeとCore proof admissionを分離。reference型/shape/hashをactual Node/捕捉済みrequest/semantic成功へ昇格しない。

## Reflection

- Design/Plan current節と新response contractへ反映し、Reportは検証範囲だけを記録。
- 次はretained trusted descriptor/readonly owner sequenceを前提として閉じ、source-sealed request v2、request/stdin/context/identity、Core semantic/proof、compatibility、provenance/public refsへ接続する。
- runtime binding成功生成にはここでのactual raw-frame joinと後続request/owner joinsも必要。metadata-only fixtureのtransport boolはadmissionでない。
- terminal failure公開時はcontrol/hash metadataのみを残し、raw capture/semantic frameを公開・採用しない。actual OS/cleanup/no remaining resourcesはA04で認定する。
