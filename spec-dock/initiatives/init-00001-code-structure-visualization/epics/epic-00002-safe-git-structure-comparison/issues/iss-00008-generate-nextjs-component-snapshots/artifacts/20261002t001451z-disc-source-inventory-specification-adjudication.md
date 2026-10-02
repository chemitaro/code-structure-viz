---
種別: disc
ID: "20261002t001451z-disc"
タイトル: "Source inventory仕様の採否と検証証拠"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-10-02"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["20261002t001435z-01--source-inventory-authoring-result.md", "20261001t212340z-decision-candidate-a02-file-source-inventory-taint.md"]
reflected_to: ["../requirement.md", "../design.md", "../plan.md", "20261002t001435z-adr-issue8-source-inventory-safe-subset.md"]
---

# 20261002t001451z-disc Source inventory仕様の採否と検証証拠

人間採択後の仕様作成記録です。助言をそのまま採択せず、exact source/schemaへ照合して補正しました。独立Spec Reviewは別のfresh conversationで行い、この相談をreview passにしません。

## Inputs

- 人間判断: source inventory/safe subsetの分離を採択、R/D/P修正とチェック後に実装再開。Spec Review Strictを明示。
- author: `chatgpt-use-strict`、元exec83790 terminal exit0、Oracle `issue8-source-inventory-spec-author`、29m11s、9files/約17039 native-estimate tokens。full665行を主担当が読了。exact repository/branch/f8d5c41...をGitHub connectorで確認した回答。
- requested GPT-5.6 Sol / Pro。native logのmodel/thinking pickerは両方already-selected/verified=yes、Pro failClosed=yes。UI観測でありbackend identityの証明ではない。
- WB原回答SHA `e84b05193267fee8bc3e2036db04a0bbf33d5b9dfc682e7b1847c5392925e832`。tracked imported copyは2行の末尾spaceだけ除去しSHA `05ce3f07b06c92371630b8fe336e82392b5b7e3362840eddf90b001394406e79`。原WB/native transcriptは変更しない。import `committed=true`はatomic file保存で、Git commitや採択ではない。

## Synthesis

採用: same parent inventory / safe model、全Fileの排他的partition、Project二view、File seed維持、proof-onlyも課金、v3 admission/public/compatibilityと独立hash・counts、旧v1/v2証拠保存、仕様reviewを先にする順序。

補正した箇所は次です。

1. **literal nullは使わない**。response-v1 `$defs/proof_record.record`はoptional objectでnullを許さない。助言の`record=null`は内部get(None)とwireを混同している。Project/Fileのkeyを省略し、nonnull metadata注入とliteral nullを拒否する。wire-v2 shapeは変えない。
2. **通常reader I/Oをfatalにしない**。Requirement Current item11、source failure classification/projectionはunavailableとactual integrity fatalを区別している。助言R-SI-006/status表のearly I/O=source-integrity terminalは不採用。complete-only sealとprefix非昇格は維持する。
3. **File以外のuntainted recordを一律公開にしない**。`derive_pre_budget_outcome`とproof reason semanticsには合法not_selected/target_excluded/unsupportedがある。任意除外禁止は取得Fileのexact partitionと既存selection witness規則に限定し、既存意味を維持する。
4. **File fieldsはroleではなくroles/effective_role**。schema/source record全fieldをcontent_base64だけ除いて完全一致する。
5. **partial-safeにはlocalityが必要**。same sealのresolved/open graphから導出するSourceFailureLedger等の既存意味を保持し、全File除外/隣接safeのcountだけで公開しない。unknown exportと表現済みunsupportedも同一扱いしない。
6. **旧count helperは既にpayload省略rowも数える**。response_model_record_countsはIDでproof-only rowsを数える。予算迂回を新機械的gateで確認するが、既存helperの欠陥が新たに立証されたとは書かない。正常unique baseと限定duplicate-target branchの順序も区別する。
7. **affected refsを具体化**。existing provenance-v2のcompatibility valueはv2で、run2/candidates2のexact refsとfingerprintを新Coreへそのまま使えない。新provenance/run/candidates-v3、未作成domain/publication/root/stdout-v2の新leaf接続をtarget表へ列挙する。新schemaはreview後のTDDで作り、空placeholderを置かない。

ID preimagesはProject.root、File.project_id/path、project_config_digestはroot/source_roots/config_path/compiler_optionsでmembershipを含まない現物を確認しました。既存algorithm_versionsにadmission fieldはないため、新semantic_admission_profile_idを独立追加し、recognition等のversionsとtrusted declaration profileは維持します。adapterは同じ保持headerからstable SemVerを取得する契約です。new target producer0.2.0を明示し、既存product0.1.0.dev0のrelease変更やold corpus更新は行いません。

## Options and trade-offs

人間は分離案を採択済みです。diagnostic先行やFile taint例外へ選択を戻しません。ASSET failure policyは別の未採択判断で、source inventory採択を認可にしません。source-prefix・actual TS/OS/package・全Issueの受入れも未完了です。

## Reflection

Current R/D/P、accepted ADR、三つのv3契約文書、用語glossaryへ反映しました。仕様と実装現状を分離し、Spec Review pass後に最小reference TDDへ進みます。元source decision barrierは解消し、goalはactiveです。旧candidate/blocked auditは履歴のままです。

## Local verification

- docs-only検査: 7文書／14 local Markdown links、run fingerprint 14 keys／compatibility preimage 10 keys／summary 7 keys／partition preimage 3 keysを確認しました。`f8d5c41e4c379b1ac471fa7f14f15ea75745cdbd`から`src`／schemas／tests／`pyproject.toml`／`uv.lock`の変更はありません。新v3の実行意味やschema適合を検証した結果ではありません。
- 既存Current正本参照test＋既存schema meta/closed testの限定selectionは34 passed（0.68s、exit0）。全pytest、新v3実装、実TypeScriptの受入れは未実施です。
- Ruff check、format check（227 files already formatted）、SpecDock sync（`--no-github --no-update-active`）／validate（10 nodes）、`git diff --check`はpassしました。PlantUML図のrenderer検証は未実施です。
- authorのexact conversation IDは`6abef058-429c-83e8-8002-01aa15e492ca`、native runtime `promptSubmitted=true`、submitted prompt SHAは`78a79042a7b4ac918a1e5c241afa318f04ce73efaf30c55b4af88cea6ef05e69`です。fresh independent Spec ReviewのIDや結果と混同しません。

独立Spec Review Strictはこれから実施します。未実施gateをpassと表記しません。取得したreview JSONとその採否は別のdurable evidenceへ保持します。
