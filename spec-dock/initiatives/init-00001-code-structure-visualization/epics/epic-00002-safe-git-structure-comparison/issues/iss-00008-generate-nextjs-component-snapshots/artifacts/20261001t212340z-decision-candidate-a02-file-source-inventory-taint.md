---
種別: decision-candidate
ID: "20261001t212340z-decision-candidate"
タイトル: "A02 File source inventoryとsafe semantic taintの整合判断"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-10-02"
親: ["iss-00008"]
template: "decision-candidate"
authority: "draft"
derived_from: ["20261001t212330z--a02-bound-diagnostics-v2.md", "20261001t212339z--a02-file-root-probe.py"]
reflected_to: []
---

# 20261001t212340z-decision-candidate A02 File source inventoryとsafe semantic taintの整合判断

未採用のdecision候補です。A runtimeの採択、既存checkpointの品質gate、外部advisoryを、この新しいsource/proof所有権の採択へ読み替えません。Requirement／Design／accepted ADRは変更していません。

## Context

### 結論

公開診断の次のcheckpointを準備したところ、**取得済みFile inventoryを全件modelへ保持する規則と、解析失敗Fileをsafe modelから除外する規則が衝突している**ことを確認しました。診断のencode不足やOracle故障ではありません。診断層で例外を握りつぶしたり、protocol rejectionをSOURCE-001へ読み替えたりしても、正規Core ownerは成立しません。

推奨は、**診断実装の前に、取得inventoryとsafe semantic subsetの所有権を整合させる先行設計unitを置くこと**です。具体的なFile／Project／proof／counts／public projection／版の扱いを正本へ確定してから実装します。本書の候補を直接guard変更の認可にしません。

### 検証基準と現状

- repository／branch: `chemitaro/code-structure-viz`／`iss-00008-generate-nextjs-component-snapshots`。
- local／configured upstream／live GitHub tip: `987d0ebc7244c0ea0d2b0400f013cc220e7cccb3`をclean状態で確認してStrictを実行しました。parentは`5cba0ec791ea4b9e48f036fd3043807ef7ef2a53`。
- この987d0ebは要求済みJSON／PlantUML候補保持のcheckpointです。関連17-module selection748 passed（1699.31s、実large cases除外無し）、他の限定gateもpass。Issue全体、全入力class、A02全closure、A03独立レビュー、製品TypeScript／CLI／packageのpassではありません。
- 元A02 baseは`710eb49a2a3143e31b8a91580700d16839d9070d`、ユーザーの累積A03固定点は`f4159066f3954454ad2f0c2701fa54bf1bc7bc4a`のままです。

### 因果関係

正常に取得したFile `F`のpathにparse/read failure rootがある場合を考えます。

```text
requestのFile F
  → correspondenceはFをmodel.filesへ残すよう要求
  → file-rootのmandatory seedはF自身も含む
  → Fはtaint対象になる
  → safe modelはtainted Fの公開を禁止
```

Fを除くとcorrespondence違反、proof側に自由なFile metadataを付けるとsource owner違反、seedから省くとunder-taint違反です。失敗したファイルを安全として扱わないguard自体は維持すべきです。

確認した正本／実装は次です。

| 規則 | 現物 |
| --- | --- |
| 全frozen project/fileをmodel correspondenceへ結合 | `docs/contracts/next-semantic-admission-v2.md`、`tests/contracts/next_runtime_v2_validation.py:1326`・`:1339` |
| proof-only source metadataの自由注入を禁止 | 同validator`:1351` |
| file-rootの必須seedに同pathのFileを含める | `tests/contracts/next_reference_validation.py::_record_project_path`（14012）、`_derive_required_root_seed_ids`（14232） |
| submitted seedを独立導出集合へ完全一致 | 同reference`derive_required_causal_edges:14397` |
| published recordはuntainted、taint closureとpublishedは非交差 | 同reference`validate_proof:15843`・`:15881` |

### ローカル再現：静的推論だけではありません

再現コードは同directoryの`20261001t212339z--a02-file-root-probe.py`です。actual frozen source seal→request→retained response→同一runtime/candidate→Core→run2を使用します。production、guard、schema、known fixturesを変更しません。child compiler／OSで実際のparse/read失敗を発生させた実験ではなく、構造化されたprivate payloadと実source ownerを検証するreference診断です。

訂正後の元実行12322はterminal exit0。正常controlが`complete / actual=1`で通ることを確認したうえで、`parse_file`と`read_file`それぞれの必須seedが`router_context / file / module`を含むことと、次の8入力の拒否を確認しました。

| 入力（各parse/read） | 実拒否理由 | 実到達点 |
| --- | --- | --- |
| Fileをmodelへ残し、rootに属するrecordをtaintedにする | `model_proof / PROTOCOL-001` | `validate_proof:15843`、published recordのtaintsは空というassert |
| 対象Fileをmodelから除く | `file_correspondence / PROTOCOL-001` | v2 Core`:1339` |
| discovered File rowへsource `record`を付ける | `proof_source_owner / PROTOCOL-001` | v2 Core`:1351` |
| Fileをmandatory seedから省き、published rowsをuntaintedのままにする | `model_proof / PROTOCOL-001` | `derive_required_causal_edges:14397`、seed完全一致assert |

3番目はsource-record注入guardを独立に確認する不正入力です。model内のFileも残すため、validなproof-only移行の成功例ではありません。Fileを本当に移す案は先行correspondenceも変更しなければ成立しません。8例を正例／TDD Red／全proof coverageとして数えません。

再実行する場合はrepository rootで次を使用します。

```bash
uv run --locked --group dev python -u -c 'import runpy; runpy.run_path("spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00008-generate-nextjs-component-snapshots/artifacts/20261001t212339z--a02-file-root-probe.py")'
```

初回のscript-path import失敗、fixture親directory欠落、causeのないtyped errorを一律cause tracebackとして扱ったharness失敗は修正しました。これらはsetup failureで、根本原因やfeature Redの証拠ではありません。最終元実行12322だけを完了証拠にします。temporary fixtureはツールの一時directory lifecycleで破棄され、対象repositoryのsourceを変更していません。

### 64 KiB側は別問題です

同じprobeの正規16 missing-target request／proof／Core／run2は成立しました。target pathは実requestの有効pathで、diagnosticへ人工paddingを注入していません。独立固定row／ASCII codecで綴ったJSONLは外部計算と一致しました。

| 実測 | exact | +1 |
| --- | ---: | ---: |
| request bytes | 64141 | 64142 |
| retained response bytes | 129228 | 129230 |
| independent JSONL bytes | 65536 | 65537 |
| target-array bytes | 60241 | 60242 |
| Core entity actual | null | null |
| run outcome | payload_unavailable | payload_unavailable |

JSONL SHAはexact `702dbbfdd93207ea5e659026f9706d8278a3568eaf401394f57adfda56411216`、+1 `c9373a44926510bbf4508a8702e0f8f9b217764ea4f1f7979f342c61b3e3a08b`。target-array SHAはexact `28ecb3b271908a668a6784f7dd13f1b0da87688ef1ac788bfd4d409ea2b36975`、+1 `202edea2fb3f5a9aeb2eca6f85c238d541c96c0fd9b4e083ad21e86efa53e583`。

これは**境界用の正規入力とliteralの到達性**の証拠です。まだないpublic diagnostic owner／stderr byte gate、actual stderr write、最終manifest／publicationのpassではありません。従来の64KiB＋1契約（stderr空、partial0、LIMIT-003一件だけmanifest用）は変更しません。

## Options

| 選択肢 | 内容 | 長所／影響 |
| --- | --- | --- |
| **1. 先行source/proof整合unit（推奨）** | 取得inventoryとsafe semantic subsetを区別する方針で、File／Project membership／proof disposition／counts／public projection／versionを正本へ確定する | 診断とsafe partialの両方を成立させる根本対処。reference下位契約と公開集合への影響をreviewする必要があり、単なるdiagnostic修正ではない。 |
| 2. file-rootを後続へ分離し、他の診断checkpointだけ進める | 現在成立するsemantic／target／export／limits／child／transport診断と64KiB境界を先に閉じる | 小さい進捗は得られるが、file-rootの矛盾は残る。全A02やIssue完了を認定できず、後で所有権の整合は必要。 |
| 3. 全File保持を維持し、File metadataだけtaint例外にする | v2のsource metadataはsemantic taintから除外する新規則を設計する | inventory投影は維持できる可能性があるが、Fileもpublished semantic recordとして扱う既存proof意味を変える。一般的なtaint解除／under-taint迂回にしない新証明が必要で、guard一箇所の緩和として採らない。 |

2はcheckpointの順序変更であって根治ではありません。1と3はいずれも意味の選択を含むため、主担当が実装に紛れ込ませて採択しません。旧v1 algorithm／recordを上書きせず、必要な新version／compatibility／hash preimage／exact refsを設計時に確定します。

## Candidate

選択肢1を推奨します。**安全subsetから失敗recordを外す保証と、同じsource ownerへinventoryを完全に結合する保証を、どちらも保つ**ためです。File seedを無視する、protocol rejectionをSOURCEへ付け替える、旧ownerへdowngradeする方法を選びません。

先行unitで具体化する候補は次です。まだ採択済みの実装契約ではありません。

1. 全取得inventoryは同じsealed request／parent ownerで保持する。childの自由なsource recordをauthorityにしない。
2. safe modelのFile／Module／派生record集合と、proofに残す失敗・除外record集合を区別する。合併・重複禁止・metadata完全一致を独立に照合する。
3. request Projectの取得membershipと、公開safe Projectの`file_ids`の対応を別に閉じる。Projectを変えずFileだけ除く処理にしない。
4. source-plan/read count、proof discovered/disposition count、公開model countを混同せず、同じownerから実値を導出する。
5. parse失敗（bytes取得済み）とsource read未完了（bytes／hash未取得）を段階で分ける。未観測bytes/hashやrequestを補完しない。今回の構造的`read_file` root probeはreader-owned早期prefixの実験ではない。
6. 新record/profileの移行、public File集合、fingerprint／compatibility／provenance／literal hashへの影響をR/D/Pと必要なschema closureへ反映し、正負testを追加する。変更仕様と実装を混ぜない。

判断していただきたいのは、**選択肢1の方針で先行source/proof整合を設計し、採択対象を具体化してよいか**です。これは新ASSET failure policyの採否とは別です。ここで先行unitの方針が採択されても、未具体化の個別schema／field／compatibility変更を実装してよいという認定にはしません。

## Reflection

### External advisoryの来歴

- specialized ChatGPT Implementation Brief Strict元exec74210、exact Oracle `issue8-a-bound-diagnostic-brief`、terminal exit0、11m28s。22 packedfiles／約196763 native-estimate tokens。
- author parent `issue8-a-bound-publicatio-brief`、同じBlue conversation `6abe7ab7-f2ac-83e8-a9f5-0244fe415d6b`。promptSubmitted=true、submitted prompt SHA `9638a93a54c507ed2fa9c0df8d27d1ff3e6e564ba1598fa502c07e304298360c`。
- requested GPT-5.6 Sol／Pro。followup modelpickerはskipped／verified=false／source=config、thinking pickerはPro already-selected／verified=true／failClosed=true。新しいmodel selection／backend identityを検証したとは主張しません。
- 答え全267行を主担当が読み、static claimsを実sourceと元probe12322へ照合しました。ready briefではなくdecision packageです。独立A03 reviewではありません。
- original WB answer SHA `c7aad90499f06112021eb0e7359641f45559a4e078a6d311f37696820eec9e95`、native transcript SHA `edd194cc8bdf36a017876c26c911c391649f3b4666c9ad80210c669abaca595d`。原本は変更しません。
- SpecDock imported tracked copyだけ5行の末尾spaceを除き、SHA `31c123a74a70525b6e77a739f0ad49c05912f4614ddbc7a066309d51c053eefa`。probeのWB／tracked copyは同じSHA `46a1aded2209e70e30820277be78db8ff2af0dbe5e04b43fdb691b83cf3b4797`。
- 元session/logで静かに待ち、restart／UI progress monitoring／subagents／API fallbackは使いませんでした。Artifact importの`committed=true`はatomic file importであり、Git commit／policy採択／review passの意味ではありません。

### 採択と停止境界

今回のdocument-only checkpointではSpecDock sync（`--no-github --no-update-active`）／validate10 nodes、Ruff check／format223 files、Current pointer1 passed（0.14s）、`git diff --check`がpass。`src`／schema／contract docs／tests／依存の987d0ebからのdiffは空です。全pytest、mypy、actual OS、独立reviewを新しく実行したとは表記しません。artifact scriptはRuffの既存`spec-dock`除外内にあり、product lint結果をscript検証の代替にせず、元実行12322と同じscript hashを証拠にします。

人間判断後、先行設計を具体化し、採用する意味をRequirement／Design／Planまたはaccepted ADRへ明示反映します。それまではdiagnostic全範囲のready brief、source/proof guard変更、新ASSET code、A03／productionへ進みません。

source/proof整合、未採択ASSET policy、reader-prefix、public全refs／final single owner、全A02 local gate／独立A03／actual TS・OS・offline package・Finalは未完了です。本調査はそれらのpassを代替しません。
