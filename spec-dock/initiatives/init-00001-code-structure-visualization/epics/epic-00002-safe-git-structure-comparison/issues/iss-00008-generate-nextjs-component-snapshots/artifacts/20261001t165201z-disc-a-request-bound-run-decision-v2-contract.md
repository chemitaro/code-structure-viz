---
種別: disc
ID: "20261001t165201z-disc"
タイトル: "A02 request-bound run-decision-v2 reference contract"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-10-02"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["20261001t161225z--a02-request-bound-run-v2-corrected.md", "20261001t161225z-01-disc-a-response-receipt-v2-contract-slice.md"]
reflected_to: ["../plan.md", "../report.md"]
---

# 20261001t165201z-disc A02 request-bound run-decision-v2 reference contract

## Inputs

- 正本はCurrent Requirement/Design/Planとaccepted A ADRです。修正版Strict briefは実行補助で、独立A03 reviewやpolicy採択ではありません。
- authoring unit baseは`9b5e0d0fee6f30967dcc296d0f75a1588e56842d`、この継続のclean/pushed checkpointは`ab97cea32617e44670ce584e34655a51ac62468a`です。receiptだけは実装・検証済みで、run2は未実装でした。
- 同じimmutable runtime result、matching validated/rejected Core owner、親analysis contextを新run recordへjoinします。新schema/producer/独立validatorと正負vectorが今回の対象です。

## Synthesis

- receiptは元frameがliveの時点でbyte/control/captureを検証し、failureではmetadataだけを残します。破棄済みbodyの再計算やheap zeroizationを約束しません。
- request-bound success/failureだけを扱います。13-key fingerprint、17-slot provenance、実entity/model-record measurementを同じownersから導出し、callerのfree status/hash/measurementを受けません。
- 既存provenance validatorのproducer-value-helper依存を今回のclosureで除去します。内部collaboratorのmonkeypatch案は`tdd/mocking.md`に従い不採用で、独立literal/再hash mutationと別の検証実装で証拠を作ります。

## 実施範囲・除外

- new run2 schema、opaque owner、projection、owner validator、Core測定値、literal、関連tests、限定contract docs/Plan/Report/evidence。
- 旧schema・旧巨大validator・catalog・production・依存/lockfile・既存goldensは変更しません。
- request-independent reader prefix、未採択ASSET policy、final publication/domain/root/stdout closure、actual Node/TS/OS/package、A03/A04/Finalは未完了のままです。

## TDDと検証記録

### 実際に選択bodyが走ったRed→Green

| public seamの観測 | Red | Green |
| --- | --- | --- |
| new closed run schema | 1 failed / 0.11s | 1 passed / 0.07s |
| completeのnew factory/owner/projection/validator | 1 failed / 1.34s | 1 passed / 6.35s |
| proof-backed partial-safe | 1 failed / 1.94s | 1 passed / 5.21s |
| validated target unavailable | 1 failed / 1.88s | 1 passed / 5.04s |
| typed Core invariant rejection | 1 failed / 2.05s | 1 passed / 4.87s |
| 実model records 10001 / limit 10000 | 1 failed / 89.34s | 1 passed / 170.49s |
| pre-spawn二branch | 2 failed / 0.96s | 2 passed / 2.50s |
| valid projectionとforeign producer-cache不一致 | 1 failed / 5.08s | 1 passed / 3.81s |
| 実entity measurementのfloat同値置換 | 1 failed / 6.16s | 1 passed / 5.43s |
| request実byte lengthのfloat同値置換 | 1 failed / 5.02s | 1 passed / 5.02s |
| response実byte lengthのfloat同値置換 | 1 failed / 5.06s | 1 passed / 5.16s |
| held depth/budgetのfloat同値置換 | 3 failed / 7.36s | 3 passed / 7.27s |
| version/exitのfloat同値置換 | 2 failed / 6.38s | 2 passed / 4.21s |
| observation versionのfloat同値置換 | 1 failed / 5.12s | 1 passed / 4.96s |
| observed-prefixのexact JSON alias | 1 failed / 4.86s | 1 passed / 5.01s |

全て意図した欠落／拒否漏れでtestが実行された結果です。collection errorや未実行testをRed/Greenへ数えません。10001件は実Core/proof corpusを検証したcountで、free actual、fake gate、縮小fixtureではありません。

### Hardeningと独立性

- 13-key各値と17 observation各slotを別々に再hashし、prefix aliasとproducer cacheを同時に合わせても独立owner照合で拒否します。fake owner/direct constructor、別exchangeの同content Core、mutable getter、全nestedのprivate/proof/path/process fields、未来kind/未採択ASSET codeも拒否します。
- complete-emptyの実測0、export measurement無し、entity actual2/limit1、typed model-record actual10001/limit10000を分離します。通常failure matrixはcontrol有無を実frame/receiptから決め、stageだけでversion/control/semantic suffixを補完しません。interruptへ普通のrun2を生成しません。
- failureの元caller frameをfactory後に変更してもdescriptor-only receiptを照合し、再readしません。transport成功後のCore unavailable/rejectedに既存candidateを保持する経路とは混同しません。
- provenance validatorは17 valuesとportable policy/spawnをvalidator-localに再導出しました。二validator sourceを直接確認し、producer provenance-value/portable helperやrun producer/projectionを呼ばないことを確認しました。これは構造変更の直接検証で、内部helperをmonkeypatchした偽Redではありません。下位owner validators、codec/SHA、変えないsource/semantic algorithmsは共有し、全製品の独立性は認定しません。
- 途中のmatrix selectionで67 passed/1 failed/63 deselected（34.99s）。唯一の失敗はfixture親directoryの作り忘れで、parent作成を修正し同じselected bodyが1 passed（5.26s）。これはfeature Redではありません。初回Ruffの未format E501とmypyのnegative-test ignore位置/nullable raw typingも修正し、guardや型検査を弱めていません。

### 三つの独立literal

test-sideの明示ASCII期待値と既知lower input corpusから初回固定し、新run/provenance producerをfixture生成に使っていません。selected literal testsは3 passed（13.49s）。既存process-startのprimitive表記`subprocess.Popen`とKATを照合してから固定しました。

| case | CJ bytes / LF無しSHA-256 | fixture file（LF一つ）SHA-256 |
| --- | --- | --- |
| complete | 7763 / `673215084459eee6f9bb8bad68d450af15bd3b3f0ec83cdaea2f14142a4418f1` | `1371006299668af69f7a04bc0d179ed162f9089a00a2f4dbd640847cbd1bf24f` |
| pre-spawn-failure | 5671 / `b075ae42f25d307d3a7aa3adffcaecc5af7634a90650bc806a526ecc177abfbf` | `05e6d22d9565a57a938ecff753ddeab71cc3a5bd19eb368f5b8f4216be151017` |
| core-rejected | 6644 / `bae073c0520dbe79823dda41d583626d773071a1dcfe58857b6ed7138af16e6c` | `ee65f475d92172ddc2b0f8dbf2e3f88182bf897ae7420e13ab67da2adcd17622` |

`jq -cjS . <各fixture> | shasum -a 256`、fileそのものの`shasum -a 256`の独立計算も一致しました。9472 bytesのpublic semantic Artifact候補と6320 bytesのknown raw response、別corpusの3902/3961 request bytesを混同しません。literal自動更新器は作りません。

### 最終関連gate

新run/receiptと隣接Core/provenance/schemaの14-module selectionを一回にまとめ、実large casesを除外せず637 passed（730.28s / 12m10s）、exit 0を確認しました。original session99385を完了まで待ち、quietなだけで再実行／重複送信していません。過去receipt491、semantic1316等の重複selectionを新candidateの件数へ合算しません。

別selectionの既存Python/SQLAlchemy16 goldens＋Current doc pointer1は17 passed（6.10s）。Ruff check全体pass、format217 files、mypy180 sources、SpecDock sync（no-GitHub/no-active-update）/validate10 nodes、tracked diff whitespace checkがpass。source/dependency/lockfile/旧巨大reference/goldensはHEAD比diff無し、既存schemaも変更無しです。新untracked fileを含むstaged全量はcommit直前に確認します。

この14-module selectionは依頼されたfocused/adjacent checksをまとめたものです。全pytest、全contracts/security、全A02、independent A03、actual Node/TS/OS/CLI、package/offline/licenses、Finalは実施・認定していません。Luna workflowはcaller-reported GPT-6.1 Sol/Max sessionの順序参考で、Luna sessionやbackend identityの証明ではありません。サブエージェント／Browser Useによるjob監視はありません。

## Reflection

- 既存のsingle-owner/版移行契約を具体化します。Requirement/Design/accepted ADRの意味や未採択asset policyを変更しません。
- 実装済み範囲はPlan、実測結果はReport、commit後SHAとclean/upstream/live一致はignored Workbenchへ記録します。
