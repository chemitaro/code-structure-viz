---
種別: disc
ID: "20261001t190302z-01-disc"
タイトル: "A02 bound publication candidates contract"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-10-02"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["20261001t190302z--a02-bound-publication-v2.md"]
reflected_to: ["../plan.md", "../report.md"]
---

# 20261001t190302z-01-disc A02 bound publication candidates contract

採択済みAのA02を進めるreference-only checkpointです。独立review pass、最終publication、実TypeScript/CLI、Issue完了を表しません。

## Inputs

- 起点: clean/pushed exact `5cba0ec791ea4b9e48f036fd3043807ef7ef2a53`。A02 base `710eb49a2a3143e31b8a91580700d16839d9070d`、ユーザーの累積A03固定点 `f4159066f3954454ad2f0c2701fa54bf1bc7bc4a`は維持します。
- 正本はCurrent R/D/Pとaccepted A ADR。Report・外部回答・本Artifactを設計正本へ昇格しません。新ASSET failure policyは未採択です。
- Implementation Brief Strict: 元exec79891、Oracle `issue8-a-bound-publicatio-brief`、2026-10-01T18:35:33.028Zから18:59:33.996Zまで24m00s、exit0 completed。保存回答600行を主担当が通読し、現在のsource/schema/testsと照合しました。
- 同じBlue authorへGPT-5.6 Sol/Proを明示しました。followupのmodel pickerはskipped/verified=no（親から継承）、Pro thinking pickerはalready-selected/verified=yes。新しいmodel/backend identity検証とは主張しません。入力は29 files/native estimate239451 tokens、UI監視・重複送信・subagentなしです。
- 原回答: `20261001t190302z--a02-bound-publication-v2.md`。Workbench原bytesとimport時のSHAはともに `a62eb36d27d80e4468896ff58742bb1ec38a08ffce2d95b26f3db81de6e3284d`。tracked copyだけ四行の末尾空白を除き、SHAは `8384f1f49416dd899ca859c0f8c9798d21d4199471db268f7c9fac4d8f0fc75f`です。Workbench/native原bytesは不変。native transcript SHAは `b5ae1fd6cd2bae673d1a506ce8af28be6b551758cb8225a549fc1182ef06e3e5`。初回5872は古い `--oracle personal` 引数によるlocal CLIエラーで送信前に終了し、現在のPATH personal-use実体を確認してその引数だけ訂正しました。

## Synthesis

- 同じrun2だけからrequested semantic JSON/PlantUMLのcandidate owners、実descriptor、保持runtime observationのcapture accountingを閉じる補助契約を採用します。新request-independent/資材failure/terminal policyは導入しません。
- PlantUMLは変えないv1 renderer/独立grammar parserを、同じavailable Core model/statusに限って再利用します。旧whole runtime/publication ownerへの変換はしません。
- candidate metadataにはbytes/base64、raw failure frame、public stderr/selected stdout成功、最終exit/sealを入れません。capture-retained計測値は新ownerのraw保持量やheap zeroizationではありません。
- JSON/PlantUML候補のdescriptorは実bytesのlen/SHAです。requested format/order、same-run/Core/context、型忠実性、独立literal、malformed cache-aligned inputs、privacyを検証します。
- 正規available candidateの実16MiB exact/+1を、actual source files/seal、held request、response、Core、run ownerから確認しました。縮小override・paddingした偽owner・先行gateで拒否された入力は使いません。selected stdoutのcopy可否は後続gateです。

## Options and trade-offs

- 最終finalizer全体を先に複製する案は採りません。既存v1のcapture再入力・循環ref・未計測値の補完を避けるため、既存accepted single-owner chainの次のseamを閉じます。このcheckpointは最終成果の代替ではありません。
- 後続のpublic diagnostic JSONL、全四selectorsのselected copy、publication/domain/root/stdout-v2 exact refs、final bytes/seal、reader prefix/未決ASSET、全A02 gate/A03/production/A05は残ります。

## 実装とvertical TDD

閉じたcandidate schema、nominal immutable aggregate/factory/projection、同じCoreのPlantUML leaf、独立grammar/owner/actual metadata validatorを追加しました。旧renderer/parser/ID algorithmは不変です。metadata cacheの一致は補助であり、同じrun/Core/context、実bytesのsize/hash、held formatsと順序、元observationの計測を別に検証します。constructorやoverride引数でcaller bytes/descriptor/limitを渡せません。

| behavior | selected genuine Red | 同じselectionのGreen |
| --- | --- | --- |
| JSON-only候補factory | 14650、1 failed／3.79s | 87933、1 passed／7.95s |
| 同じCoreのPlantUML leaf | 84359、1 failed／1.52s | 85237、1 passed／1.53s |
| PlantUML-only aggregate | 62467、1 failed／5.00s | 54924、1 passed／6.77s |
| 両形式／selector非縮小 | 55367、1 failed／5.25s | 64304、1 passed／7.36s |
| 通常failureの空集合 | 24271、1 failed／1.91s | 75687、1 passed／2.30s |
| capture未取得null | 90396、1 failed／1.12s | 77057、1 passed／1.42s |
| duplicate/requested schema closure | 73056、1 failed／7.18s | 47254、1 passed／6.84s |
| JSON descriptor整数型 | 18771、1 failed／7.78s | 37199、1 passed／7.28s |
| 再hash公開JSONの整数型 | 48997、1 failed／7.42s | 22338、1 passed／7.36s |
| 元captureの整数値float | 37341、1 failed／1.32s | 40138、1 passed／1.32s |
| 元Core投影の整数値float | 44924、1 failed／7.07s | 16221、1 passed／5.22s |

閉じたpublic semantic schemaは浮動小数fieldを持たないため、独立validatorが全public recordのnative floatを拒否してから元の値・文字列・順序をjoinします。数学上のintegerというschema通過だけに頼らず、Core/capture側のfloatまで拒否し、数値をcoerceしません。文字列の厳密一致もcanonical NFC比較だけに弱めません。

既存分岐が最初から正しく処理するpartial-safe/complete-empty（2 passed）、Core unavailable四分岐（4 passed）、新same-Core prop facet欠落（1 passed／2.03s）はhardeningであり、Redを捏造していません。不正cache copyはconformance負例で、public mutation APIやhostile same-UID対策ではありません。

### Literal provenance

新candidate/leaf producerやrendererから期待fixtureを生成していません。JSON-only/pre-spawnは既存固定run2、bothは正規lower run2入力とtest-sideで明示したpublic record/preimage、PlantUMLはauthorのworked ASCII literalを使いました。独立codec、`jq`、`shasum`で確認しました。

| frozen file | exact file SHA-256 |
| --- | --- |
| `publication-candidates-json-only.json` | `243ee57df040dd8969544fa3f9b6a3e82566451c98185312aaee373fb0a85fec` |
| `publication-candidates-both.json` | `ad2424a19dcd0f8db6529342e0d2b38c8aae28b7e7733ca737bd6920679045df` |
| `publication-candidates-pre-spawn-failure.json` | `863a4f141598219c37181caa03594166fed262d6f4b0fd27d3b3c56bdab6e752` |
| `public-plantuml-card.puml` | `0bce98e4e12b722ff2685a76c52bddba7bca735af090ad735d94bbfc9e50c2a9` |

JSON-onlyはdepth1/1、9472-byte JSON／元stdout6320。bothはdepth0/0、9483-byte JSON／SHA `7e15f037bd341e26398f0bc6f8133d0ff5872ee3a7244e714b477d15d7aa634f`／元stdout6332。両者のhashを無条件に共有しません。PlantUMLは1082 bytes／24 LFです。

### Actual large fixture

1000の実program filesを有効な長いrelative pathsにdescriptor-relativeで作成・read/sealします。内容は既存known Card corpus、modelは対応Modules/router facts/full proof、CLI entity override1000です。初回のfresh seal/requestで独立期待JSONを計算し、pathの四箇所への投影とactual `.d.ts` comment sizeの十進桁差で最終入力を調整します。最終fresh seal→request→response→Core→runからcandidateを作り、独立bytesへ完全一致を確認します。request/response/source/modelの旧上限は弱めません。

最初のlarge入力65003（2 failed／153.85s）は既存export census外のprogram path/contentでCoreが拒否し、candidateへ未到達でした。feature Red/境界証拠に数えず、旧guardを変えず実known bytesとrebased `/src/Card.tsx` suffixへ修正しました。期待public requestも全configでなく閉じた十fieldへ修正。正しい2463はexit0、2 passed／727.07sで実16MiB/+1候補の保持を確認しました。source filesystem/lengthは実入力ですが、TSによる認識やOS child実測ではありません。

その他、wire control/request contextの準備誤り、test追加の配置、digest-only semantic_payload観測名をraw bodyと混同したprivacy assertionを修正しました。guard/契約を弱めません。失敗した準備をgenuine Redや最終passへ読み替えません。

## 最終local gates

- 新candidate/leafのpre-final selection57978は79 passed／2 large cases deselected／206.01s。facetの独立追加34915は1 passed／2.03s。重複selectionを合算しません。
- 旧PlantUML81482は83 passed／606 deselected／8.26s、旧Python/SQLAlchemy16 goldens＋Current pointer1の37776は17 passed／6.37s。
- 全最終code変更後のRuff check、format223 files、mypy185 sourcesはpass。全17-module candidate/adjacent selection72332はterminal exit0、**748 passed／1699.31s（28m19s）**。新候補・全隣接owner・schemaに、実16MiB候補二件、元16MiB response、96MiB stdin、10000/10001 model records等を含み、large caseの除外はありません。重複selectionを合算せず、全pytest・whole A02・A03・actual TSのpassと呼びません。
- SpecDock `sync --no-github --no-update-active`と`validate`（10 nodes）、`git diff --check`はpass。最終documentation反映後の再確認とcomplete staged diff/Git checkpointは通常手順で行います。原実行は静かに待ってterminal結果を保持し、重複job・UI監視・subagentを使いません。

全17-module command（exit0）:

```sh
uv run --locked --group dev pytest -q -rP \
  tests/contracts/test_next_publication_candidates_v2.py \
  tests/contracts/test_next_public_plantuml_v2.py \
  tests/contracts/test_next_run_decision_v2.py \
  tests/contracts/test_next_observed_response_receipt_v2.py \
  tests/contracts/test_next_runtime_result_v2.py \
  tests/contracts/test_next_provenance_v2.py \
  tests/contracts/test_next_core_failure_v2.py \
  tests/contracts/test_next_semantic_candidate_v2.py \
  tests/contracts/test_next_exchange_v2.py \
  tests/contracts/test_next_process_observation_v2.py \
  tests/contracts/test_next_rejected_frame_v2.py \
  tests/contracts/test_next_request_frame_v2.py \
  tests/contracts/test_next_response_frame_v2.py \
  tests/contracts/test_next_analysis_context_v2.py \
  tests/contracts/test_next_public_semantic_v2.py \
  tests/contracts/test_next_public_artifact_v2.py \
  tests/contracts/test_json_schemas.py
```

### Captured actual boundary measurements

| actual field | exact 16 MiB | 16 MiB＋1 |
| --- | --- | --- |
| JSON bytes | `16777216` | `16777217` |
| JSON SHA-256 | `43806a590a35166c3c4b8f97f1184e2d794e0b1f35a48d4434df9c07c7164e3c` | `ba6c2a2694399938fe222e0186a7a03878a18c47f2c141301d170ff51db7199f` |
| canonical request bytes | `4365737` | `4366938` |
| raw response bytes | `9082153` | `9082154` |
| sealed files / internal entities | `1003 / 1000` | `1003 / 1000` |
| longest relative path UTF-8 bytes | `3902` | `3902` |
| actual context file bytes | `100` | `1000` |

各descriptorは保持実bytesから算出し、実JSONは独立test-side期待bytesと一致しました。新candidate metadataにcopy_statusはありません。これらはreference-onlyの正常到達性で、selected stdout copyや実TS/OS/installed packageの測定ではありません。

## Reflection

- 内容は既存single-owner/public byte契約の機械的具体化です。Requirement/Design/ADRを実装都合で変更しません。限定進捗をPlan、実測をReport、新data contractをdocs/contractsへ反映します。
