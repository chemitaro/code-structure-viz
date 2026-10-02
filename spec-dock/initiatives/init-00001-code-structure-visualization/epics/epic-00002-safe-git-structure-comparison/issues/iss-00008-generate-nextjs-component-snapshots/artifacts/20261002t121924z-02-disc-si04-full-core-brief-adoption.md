---
種別: disc
ID: "20261002t121924z-02-disc"
タイトル: "SI-04 full Coreブリーフの照合と採用"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-10-02"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["20261002t121923z--si04-full-core.md", "20261002t121923z-01--si04-full-core-corrected.md", "20261002t121924z--si04-brief-literal-probe.py", "20261002t121924z-01--si04-brief-literal-probe.txt"]
reflected_to: ["../plan.md", "../report.md"]
---

# 20261002t121924z-02-disc SI-04 full Coreブリーフの照合と採用

採択済みA案をfull Core referenceへ接続する実装準備の証拠です。仕様の意味や製品の採択を変更せず、SI-04の完了・コードレビュー合格を主張しません。

## Inputs

- 正本：Current [Requirement](../requirement.md)、[Design](../design.md)、[Plan](../plan.md)。仕様認証はbcae954、SI-03認証はexact `23072c288fc203071c10bfe3305e6ec5d3b055fe`。
- [初稿の原回答](20261002t121923z--si04-full-core.md)：1217行を全読、SHA256 `a84e69f074de018f757addbb6720a35421bf7eb8c486134c8252dbb763587ed3`。元49552 exit0、1193465ms（19m53s）。旧export helperの流用範囲に問題があり、実行可能なbriefとしては未採用です。
- [修正版の原回答](20261002t121923z-01--si04-full-core-corrected.md)：2588行を全読、SHA256 `6c93c529519fa8c4929fece19e431808d958d5c3cfa76791979b720c7385d5b3`。元74264 exit0、993196ms（16m33s）。原Englishをbyte-preservedで保存し、日本語の採用判断を本資料へ分離しました。
- [独立固定値probe](20261002t121924z--si04-brief-literal-probe.py)と[結果](20261002t121924z-01--si04-brief-literal-probe.txt)。stdlibで手書きpreimage/hashを照合し、新v3 producerを期待値生成に使っていません。

### 外部authorの来歴

- 同じsource-inventory実装目的・採択範囲で、SI-03 author `issue8-si03-source-inventory-brief` → `issue8-si04-full-core-brief` → `issue8-si04-full-core-correction`を直接継続。conversationは `6abf39d9-bdc0-83ee-96f7-79bde716eb7f`。reviewer/analystとは別です。
- 要求モデルはGPT-5.6 Sol / Extra High、browser-only/select/attachments always。両followupの今回model pickerはinherited/skipped/verified=falseで、fresh model確認は主張しません。親SI-03のSol pickerはverified=true、両今回Extra High pickerはalready-selected/verified=trueです。
- 両promptはsubmitted=true。初稿submitted SHAは `3029a37acba5e5471802ad1e00472fc83548511728368732928363fe20794c2a`、修正版は `6ec856500da76193e1563d676aedb5e2abfd023164dfd609ce944885813ae20a`。
- local/upstream/live exact SHA一致・cleanを確認して依頼しました。回答のGitHub connector exact-SHA宣言はprompt-enforced claimであり、machine-readable connector/backend attestationではありません。
- 原session/logを静かに待機し、duplicate/UI監視/subagentは使っていません。現在のauthor jobsは全てterminal0です。

## Synthesis

### 採用する実装境界

1. 変更するcodeは新しい `tests/contracts/next_semantic_core_v3_reference.py`、`next_semantic_core_v3_validation.py`、`test_next_semantic_core_v3.py`の三ファイルです。immutable same-owner decision/rejectionと独立再検証をfull Core入口へ閉じます。
2. full Dのsource correspondence、mandatory seeds、exact causal graph、typed taint、Props grammar、source locality、target/export/selectionを予算・outcome分岐より先に検証します。正常経路はSI-03のstrict source seamを維持します。
3. post-acquisition parse/read rootsは同じcomplete production sealのgraphと保持bytesからv3-localに導出します。旧acquisition ledgerへ架空failureを注入しません。File不適格とModule不適格を独立に扱い、reverse-affected sourceを公開しません。
4. selected missing/component-only/byte-identical duplicateの例外はfull proof成立後のTARGET-001/no-payloadだけです。通常のModule cardinality guardを弱めず、独立safe target/selection-only/三nonFile rootsをfull Core入口で検証します。
5. actual全discovery record数10000/+1、safe Module+Component entity数、unavailable優先順を独立計測します。proof invalidをcount failureで隠しません。十keyのcompatibility preimageをsame candidateへbindします。公開schema/refsはSI-05です。

### export流用範囲の補正

旧 `_export_census_for_model`、`_export_syntax_rows_for_model`、`_reexport_graph_index`、旧observation/witness/public-coverage facade等は固定legacy census/raw graphに依存していました。新しいfailed/importer/safe corpusへ使う一般APIではないため、初稿のこの助言は採用しません。

修正版のsame-seal frozen bytes → full-D syntax census → direct declaration table/raw reexport edges → generic graph recomputation → exact observation/witness joinを採用します。input-parameterized scanner、path resolution、graph primitiveだけ再利用し、unknown corpusの空exports fallback・旧fixtureのrelabel・public-Mだけのscanは認めません。proof-only Moduleもfull-D側で検証し、公開bindings/resolutions/coverageはeligible Mへ別投影します。

actual TypeCheckerをreference scannerで認定しません。Componentはfull-D declarationへの一意join、typeは実syntax、noncomponent valueはbytesで証明できるprimitive declarationのみのreference witnessです。意図的unsupported string export、unknown string、graph cycle/conflictの既存outcomeを変更しません。

### 先行probeで確認できたことと局所訂正

- 元823d42 exit0（0.053s）。source bytes/size/hash7件、ID16件、syntax span/kind/tokenID4件は不一致0。新source-derived raw reexport joinとgeneric graph recomputationはpassです。
- 実行方法：`uv run --locked --group dev python -c 'import runpy; runpy.run_path(".workbench/luna-max-implement/issue8-nextjs-snapshots/evidence/si04-brief-literal-probe.py", run_name="__main__")'`。保存済みprobeをこのcheckoutで実行しました。runner準備ミスはCoreのRedではありません。
- 初稿/修正版のfirst corpus例はrelationを数えていませんが、既存Designの`static_import`はreexportも含みます。index→button、role=value、reexport=true、boundary_effect=noneを追加し、独立ID `next:relation:4be44776badbed873e1ed93a50e33c8c248fb7a9dec5b75a9a78191df7efc03d`へ固定します。
- first corpusの正しい実数はProject1/File6/Module3/Component1/export member2/relation1/fact3 = **17 records**、internal entities=4です。raw回答は修正せず、この採用補正を適用します。これは既存仕様に沿うtest例の訂正です。
- source fixture/既存primitiveの照合であり、未実装Core/TDD/actual TS/両OS/製品acceptanceのpassではありません。

## Options and trade-offs

- 旧export facadeをそのまま再利用：新bytesとのbindingが成立しないため不採用です。
- 旧巨大validator/旧goldensを書き換える：旧regressionを失うため不採用です。
- **新v3局所pipelineをsame retained sourceへ結合**：採用。old wire非依存algorithmの意味を維持でき、new source corpusと旧v2 failure/KATを別に検証できます。実TS認定は後続A04に残ります。

### 実装・チェックの進め方

- 元SI-04 baseは `caf38329826ae34f8e3cb330b83b97e0357b7dc5`で固定。証拠checkpoint後もbaseを移しません。A02 base710eb49、A03固定点f4159066も維持します。
- `tdd`で一つのpublic observable behaviorごとにRed→minimum Green。最初は六file実bytes・real source acquisition seal・既存transport/SI-03 seam・独立export値がcoherentと確認してから、new Core factoryのmissing behaviorを観測します。
- completion checksは新Core selection、SI-03/旧v2 Core/failure/request/exchange、該当source/export/taint/type/target/budget回帰、旧Python/SQLAlchemy goldens、Current pointer、Ruff/format/mypy、SpecDock/diff-checkです。SI-07のall-contract/full gateと混同しません。
- 同じcandidateのtask-scoped explicit stage、installed `git-commit`の`commit-codex -a`、normal current-branch pushを使います。原回答のgeneric Git例はhost rulesに優先しません。全staged diff確認とclean/local-upstream-live SHA一致後、caf3832からfresh independent Code Review Strict（GPT-5.6 Sol/Extra High）を実施します。
- 新meaning/Product/Security判断・File seed省略・偽source metadata・Project taint・旧ID/preimage変更・早期partial-safe prefix・ASSET混入が必要なら正本gateへ戻ります。期待するvalidation labelだけで不正inputを通しません。

## Reflection

- 文書checkpointの限定検査：四importのbyte/hash一致、7 local links、terminal lineage、src/schema/tests/依存diff無しを確認。Current pointerは1 passed（0.14s）、Ruff check/format（188 files）、SpecDock sync（active維持）/validate10 nodes、diff-checkはpassです。Coreや全pytestの認定ではありません。
- Plan/Reportへ「SI-04 corrected brief採用・TDD開始前」の進捗だけ反映します。Requirement/Design/accepted ADRの意味、src/schema/依存/旧reference/旧goldensは変更しません。
- SI-04 full Core、SI-05公開refs、diagnostics/final publication、全A02/A03、production/実TS/OS/CLI/package、Final Quality GateとIssueは未完了です。
- 現在のcaller-visible implementerはGPT-6.1 Sol/Max。actor設定の独立検証はなく、Luna actorとして認定しません。primaryが継続し、subagentを使用しません。
