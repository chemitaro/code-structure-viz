---
種別: disc
ID: "20261002t062856z-disc"
タイトル: "SI-03 source inventory reference seamの実装証拠"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-10-02"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: []
reflected_to: []
---

# 20261002t062856z-disc SI-03 source inventory reference seamの実装証拠

採択済みA案を、SI-03のsource/proof reference seamへ実装した証拠です。新しい製品方針、全Core admission、production解析、全A02/A03またはIssue完了を認定する文書ではありません。最終回帰テストはpass、独立Strict Code Reviewは未完了です。

## Inputs

- 正本: [Requirement](../requirement.md)、[Design](../design.md)、[Plan](../plan.md)のCurrent SI節。
- 採択済み方針: [source inventoryの分離](20261002t001435z-adr-issue8-source-inventory-safe-subset.md)と[owner-closed A案](20261002t041350z-adr-issue8-owner-closed-file-module-publication.md)。
- 仕様gate: exact `bcae9548ef515e4a7662de1ad648171622c6a437`の[再認証pass](20261002t044942z-disc-owner-closed-spec-review-pass.md)。
- SI-03元base: `ce0edaa8fe63e79523fe7ad1dcb4b0a39dc02dce`。このunitの修復・step reviewでもbaseを変更しません。
- [fresh Strict Implementation Briefの原回答](20261002t051850z--si03-source-inventory.md)は802行。`issue8-si03-source-inventory-brief`は17m20s/exit0、GPT-5.6 Sol/Extra Highの両picker verified=true、conversation `6abf39d9-bdc0-83ee-96f7-79bde716eb7f`。主担当が全文を正本・sourceへ照合しました。
- 原回答のWBとArtifactは`cmp` exit0でbyte-for-byte同一、SHA256 `ddb823b61376153c1f7ea3bbd16b7f603b6b025695206fb22fb6e995300b9e9c`です。
- [最初のowner binding TDD checkpoint](20261002t052906z-disc-si03-owner-binding-first-tdd.md)は狭い途中証拠として保存し、この全unitの結果に書き換えません。

## Synthesis

### 実装した観測可能な境界

追加codeは次の三ファイルだけです。

- `tests/contracts/next_source_inventory_v3_reference.py`: closed immutable `ValidatedSourceInventorySeamV3`、owner-bound factory、read-only投影、実count、partition preimage/hash。
- `tests/contracts/next_source_inventory_v3_validation.py`: full source discovery、full Module owner、source-public metadata、disposition/reason、参照・cause witness、実測count、独立再検証。
- `tests/contracts/test_next_source_inventory_v3.py`: 実source reader/sealを入力にする正負tests。semantic recordsはtest用であり、実TypeScript解析を行った結果ではありません。

入口は既存のdata-only request-v2/transport candidateと、**同じ実source seal・同じretained execution assets**です。raw request dict、別seal/assets、直接constructor、旧adapter `0.1.0`を拒否し、保持資材の`0.2.0`を要求します。旧資材fixture/KATは変更していません。

### A案のfull inventoryと公開投影

1. 取得した全Project/FileをDへ一度ずつ解決します。source行には`record`を置かず、parent requestからmetadataを得ます。同じ内容をchildが再送した場合も拒否し、`null` payloadは既存wire schemaで拒否します。
2. projection前の全program FileごとにModuleをちょうど一つ要求します。非公開Moduleを含めて同じ(project,path)へjoinするため、公開から消してownerを隠すことはできません。nonprogram FileへのModuleも拒否します。
3. full-baseのFile/Module taint、owner原因、既存selection/unsupportedの局所的な整合からModule eligibilityを求め、提出された公開Module集合と一致させます。公開の有無そのものをeligibilityの根拠にしません。
4. 直接parse/read rootを持つFileはfailed、untainted Fileのowner Moduleが失敗した場合は`excluded/failed`です。Module由来の偽File taint、無関係なroot原因の借用、closed referenceでないcause edgeを拒否します。
5. Fileをsafe/failed/excludedの三集合へ完全分割し、reasonまで一致させます。public Projectのmembershipだけをsafe Fileへ縮め、private Projectは全取得membershipを保持します。公開FileゼロのProjectも消しません。
6. private record参照はD内、public record参照はM内へ閉じます。Project membershipを一般参照の逆伝播へ変換しません。全recordの唯一のdisposition、Project常時公開/無taint、public record無taint、canonical proof順序も確認します。

source-owner witnessは**提出されたclosed causal edgesに沿う局所的なroot/taint join**です。mandatory seeds/edgesの完全性、typed taint全体のleast fixed point、full target/selection/source-graph localityを認定しません。これらはSI-04の独立full proof gateで検証してからCore/publicへ接続します。旧`validate_model`/`validate_proof`/whole v2 Core gateを、新profileの認定入口として呼んでいません。

### Countとfingerprint

acquired file count/bytesは全取得request、published countは実model、proof-only countはD−M、accounted countは実D、entity countは実published Module＋Componentです。child coverage cacheでこれらを置き換えません。Fileの公開減少はsource acquisition予算を減らしません。

小さい正常caseのliteralは、1 Project、4 acquired Files/145 bytes、D=6、published=6、proof-only=0、accounted=6、Module=1、Component=0です。実recordを10000/10001個作る二caseは、payload-free proof-only File一つを含めたcountの測定です。まだSI-04のbudget terminal routingではありません。

partition preimageは`profile_id/request_id/projects`の三key、各Project行は`project_id/safe_file_ids/failed_file_ids/excluded_file_ids`の四keyです。Projectはrequest root順、各File ID集合はcanonical順です。public ProjectのID順と混同しません。profileは`next-source-inventory-safe-subset-v1`、hashはSHA256(CJ15)。独立ASCII KATは次の値を固定しています。

- request ID: `8a550469363d2d92f6c55345cb8cc0c2f540109cafd4e8b507cfb5cf25de175d`
- partition SHA256: `0c380fdc863eab3e029cec9129a8fa000bb0695321221a559025757060d48b83`

KAT期待bytes/hashは、新producerが存在する前にfixture inputからstdlib JSON/hashlibで一度生成したliteralであり、test中にproducerから計算しません。

### TDDと検証の来歴

TDDはpublic source seamの一behaviorをRed→最小Greenにし、owner bind、metadata注入、source欠落/重複、full Module cardinality、二view、owner原因、source failed、references、既存reason、実count、KAT、独立revalidationを順に実装しました。後続hardeningでは無関係root借用、source causal edge欠落、proof非canonical、malformed Module、unsupported coverage偽装、failed Fileに対するpublic Moduleを実際に拒否できないRedから修復しています。

既に拒否されるnull wire、owner type/swap、既実装の10000/+1 count hardeningは新Redと数えません。unsupported fixtureの誤ったwire形状、二Project fixtureの誤ったpublic ID順、test期待regexの誤りも製品機能のRedではありません。二重disposition testはcanonical配列の重複拒否で先に落ちたため、同じrecordに二つの異なるreasonを置いて本来のdisposition guardを確認し、focused 5 passed/67 deselected（2.73s）です。拒否規則を緩和していません。

初回回帰は1 failed/308 passed（191.11s、exit1）、失敗は上記test期待の整合でした。修正後の同じ六module/large cases除外無しselectionは309 passed（211.70s、exit0）です。test整合後のRuff check/format（230 files）、mypy（188 sources）もpass。旧途中job59244のexitは不明で、pass証拠へ数えません。

実行commandsと結果は次のとおりです。重複selectionの件数を合算しません。

| check | command / selection | result |
| --- | --- | --- |
| 新unitと隣接契約 | `uv run --locked --group dev pytest -q --tb=short tests/contracts/test_next_source_inventory_v3.py tests/contracts/test_next_semantic_candidate_v2.py tests/contracts/test_next_request_frame_v2.py tests/contracts/test_next_exchange_v2.py tests/contracts/test_next_trusted_environment_v2.py tests/contracts/test_json_schemas.py` | 309 passed / 211.70s / exit0、元session51138 |
| lint | `uv run --locked --group dev ruff check .` | pass / exit0 |
| format | `uv run --locked --group dev ruff format --check .` | 230 files already formatted / exit0 |
| typing | `uv run --locked --group dev mypy src tests` | 188 sources / exit0 |
| 旧domain/Current pointer | `uv run --locked --group dev pytest -q --tb=short tests/contracts/test_python_goldens.py tests/contracts/test_sqlalchemy_goldens.py tests/contracts/test_next_contracts.py::test_round23_rg_18_current_schema_and_history_contract_are_explicit` | 17 passed / 9.94s / exit0、元session80307 |
| 文書投影 | `./spec-dock/scripts/spec-dock sync --no-github --no-update-active` | exit0、既存activeを変更せず投影生成 |
| 文書storage | `./spec-dock/scripts/spec-dock validate` | 10 nodes / exit0 |
| 新Artifactの参照 | Markdownのlocal linkを対象Artifactから相対解決して存在確認 | 8 links / exit0 |
| whitespace | `git diff --check` | exit0 |

staged diff、commit/push後の同一SHA確認は、この結果とは別に最終checkpointへ記録します。全pytestやfull A02 gateとは表記しません。

## Options and trade-offs

採択済みA案だけを実装しています。source Fileを消して取得成功のように見せる案、Fileへ逆taintを付ける案、child source metadataを信用する案、旧v2認定を呼んで新profileを通す案は実装していません。独立再検証は同じretained ownersから再導出し、producer factoryまたはcacheの値を検証根拠にしません。

## Reflection

仕様の意味を変更していないため、Requirement/Design/accepted ADRの新判断は不要です。Plan/Reportへunit実装・local evidence・未認定gateを反映します。次の出口は元baseからのfresh ChatGPT Code Review Strict（GPT-5.6 Sol/Extra High）であり、外部reviewはローカルtestsの実行証拠と分離します。

SI-04 full proof/Core、SI-05 public/exact refs、SI-06 diagnostics、reader-owned prefix、未採択ASSET policy、全A02/累積A03、実TS/OS/CLI、offline package、Final Quality Gateは残っています。source seamのpassをIssue全体の完了に読み替えません。主担当のみで実施し、subagent reviewやBrowser Useによるjob監視は実施していません。
