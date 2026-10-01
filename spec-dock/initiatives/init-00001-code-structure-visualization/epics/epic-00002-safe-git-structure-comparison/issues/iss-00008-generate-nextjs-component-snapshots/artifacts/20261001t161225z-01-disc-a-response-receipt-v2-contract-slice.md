---
種別: disc
ID: "20261001t161225z-01-disc"
タイトル: "A request-bound run brief訂正とdescriptor-only receipt初スライス"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-10-02"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["20261001t161204z--a02-request-bound-run-v2.md", "20261001t161225z--a02-request-bound-run-v2-corrected.md"]
reflected_to: ["plan.md", "report.md", "docs/contracts/next-provenance-v2.md"]
---

# A request-bound run brief訂正とdescriptor-only receipt初スライス

## 範囲と結論

baseはclean/pushed `9b5e0d0fee6f30967dcc296d0f75a1588e56842d`です。Issue全体ではなくA02-3のrequest-bound run2へ渡すresponse receipt seamだけを実装します。raw brief二件はSpecDock `artifact import file`で元bytesを保持したnoncanonical evidenceです。CLIの`committed=true`はArtifact保存transactionを意味し、Git commit/pushや仕様採択の証明ではありません。

最初の助言§5.3／Stage2のfailure完全frame保持案は**不採用**です。Current Design78と`next-provenance-v2.md`14–18のfailure raw-buffer/candidate破棄を維持します。元frameがliveの間に独立検証し、破棄後はdescriptor-only receiptと同じrequest／immutable observation snapshotへ照合する訂正版を採用します。raw failureのbyte再計算を後段で行ったとは表現しません。

## Strict authoring証跡と限界

- 初回: specialized ChatGPT Implementation Brief Strict、`issue8-a-bound-run-brief`、original exec70054、exit0、19m09s。全文878行を主担当が読みました。conversation `6abe7ab7-f2ac-83e8-a9f5-0244fe415d6b`。GPT-5.6 Sol model pickerとPro thinking pickerをoriginal logでUI verified。raw SHA `a47aca17cf499edfb5e993d6648c7d977c352879a49e2233439035d3028bde2d`。
- 同じ目的・著者へのStrict follow-up: `issue8-a-bound-run-correction`、original exec54642、exit0、16m05s。全文739行を主担当が読みました。explicit author GPT-5.6 Sol／Proを再指定。follow-up model pickerは`skipped / verified=no / source=config`であり、親の設定・観測を継承する限界があります。今回のPro thinking pickerは`already-selected / verified=yes / failClosed=yes`。backendモデル同定とは区別します。raw SHA `cba3db2ed9cf665896295c3409fcd1b6ac5b81f687fe15d2422b1a9f9c303dfd`。
- import後、Git whitespace gate用にtrackedコピーの行末空白だけを正規化しました（初回24行／訂正版3行）。公開コピーSHAは順に`e13a3412ade15260b7ce4f322126b3e02ace8ee519a58b5c96379a92066626ed`／`06d5af788489c464716a9053bf0a2122f154af95a6bf2e0072793c3ac79cd796`です。Workbench／Oracleの元bytesは変更していません。
- 最初のfollow-up入力検査exec7429は不存在attachment pathでexit1でした。`rg --files`で実pathを訂正し、browser送信前の入力失敗だけを再実行しました。実行中jobの重複送信、Browser Use進捗監視、サブエージェントはありません。
- 両回答がexact repo／branch／full9b5 SHAのGitHub connector一致を報告しました。connector検証はprompt-enforcedで、machine attestationではありません。終了後にlocal/upstream/live refの全SHA一致とclean stateを再確認しました。
- 主担当はcaller-reported GPT-6.1 Sol／Maxです。Luna workflowは順序の参考で、active Luna sessionやbackend設定検証の主張ではありません。独立A03／Finalレビューではありません。

## 実装と局所補正

- nominal `RetainedObservedResponseReceiptV2`は同じrequest、同じimmutable observation bytes object、三field descriptor bytesだけを保持します。free descriptor constructor、raw frame、semantic payload/proof、closure／body再読pathを追加しません。通常getterはfresh projectionです。
- runtime factoryは一回snapshot化し、live receipt validatorで実SHA／len／canonical flag、閉じたcontrol/capture、actual foreign binding／echo違反を検証します。failureではcandidateを保持せず、旧descriptor accessorはreceipt経由の互換accessorにします。広い`except ValueError`をecho違反の根拠にする経路を除去しました。
- post-disposal validatorはexact receipt／result／request／snapshotのowner joins、descriptorのclosed metadata、control/capture対応を照合します。admitted transportがある場合だけ保持candidate/frame/bindingを再検証します。decoder rejectionは別の既存metadata ownerで、complete-frame receiptを作りません。
- provenance生成もruntime resultのreceipt gateを通します。ただし既存`validate_runtime_provenance_v2`からproducer value helperへの依存の除去は、後続run2 closureで行う未完了作業です。このスライスだけでprovenance全体の独立性を認定しません。
- 訂正版の内部producer helper monkeypatch案は、`tdd/mocking.md`の内部collaboratorをmockしない規則に従って採用しません。実owner／literal／変異したvalidator inputで振る舞いを検証し、必要な構造的独立性は後続の明示conformanceチェックと分けます。
- frozen／nominal型はAPI誤用・owner取り違えの防止です。callerが別途保持する入力、heap zeroization、hostile same-UID耐性は認定しません。反射的な不正入力はvalidator conformanceの負例で、security保証ではありません。

## TDDと独立known vectors

1. receipt accessor欠落を選択test本体でRED（AttributeError、1 failed）→GREEN（1 passed、1.10s）。collection failureではありません。
2. failureへのcandidate混入をpost-validatorが見逃すRED（DID NOT RAISE、1 failed）→GREEN（1 passed、1.67s）。
3. successの保持frame変更をmetadata-only検証が見逃すRED（1 failed）→GREEN（1 passed、1.66s）。
4. 別runtime snapshot receiptをprovenanceが受理するRED（1 failed）→GREEN（1 passed、1.35s）。
5. decoder rejection owner欠落をruntime validatorが見逃すRED（1 failed）→GREEN（1 passed、0.62s）。
6. fake binding／echo mismatch labelをlive validatorが受理するRED（2 failed）→GREEN（2 passed、3.28s）。

追加hardeningの中間22 testsはpass（20.54s）しました。これはその時点の部分selectionで、最終candidateのgateと区別します。Ruffのimport／format／raw regex指摘を通常の局所修正とformatterで解消し、guardを弱めませんでした。

独立ASCII literalはraw LF無し262 bytes／SHA `a1b2f3c703021e2c41f095771e4d16bb23fc1b4ce9ebea0edaa32dc8dc251407`、LF一つ263 bytes／SHA `39f69e2d4585d53c3ff3ac4db463beba675bf4fa908b6f984f08927631150a25`です。前者はcanonical=true、後者false。後者は`wc -c`／`shasum -a 256`でも実fixture bytesを独立照合しました。control-response observation KATは順に`fcb066cbc493a50d2403ac3f179c09167705dbcf390cce752e5f5a1837cf0164`／`6edadd2c0fcf54ca5477efc71e258580b669f26d92e2767fc5032d3af4f601d3`。raw digestとobservation-v2 preimage digestを区別します。

## 最終品質gate

- 新26 receipt testsを含む関連13 modules: original exec25860 exit0、491 passed（398.88s）。runtime/provenance/exchange/process/frame/rejection/Core/context/public/schemaの実selectionで、large casesの除外はありません。
- Python／SQLAlchemyの既存16 goldens＋Currentdoc pointer1: original exec22197 exit0、17 passed（5.49s）。overlapping selectionと合算しません。
- Ruff全体pass、format213 files pass、mypy177 source files pass。旧v1／all schemas／src／pyproject／uv.lock／旧巨大referenceのdiffはbaseに対して空です。
- SpecDock `sync --no-github --no-update-active`／validate（10 nodes）がpass。最終Currentdoc pointerの再確認1 passed（0.14s）、diff-checkもpass。activeを更新せず、GitHub lifecycle変更はありません。staged全文確認・ordinary commit/pushはこの検証済みtreeを対象に続けます。前checkpointの243／1316等をこのcandidateの結果へ転記しません。

## 残る境界

run2 schema／owner／全success・failure枝／Core measurement／full literal、provenance helper依存除去、reader-owned prefix／新ASSET policy、publication/domain/root/stdout exact refs、A02全gate／独立A03／production／actual TS・両OS・offline package／Finalは未完了です。新ASSET policyは未採択のままで変更していません。src／既存schema／旧巨大validator／依存／既存golden bytesをこのスライスで変更しません。
