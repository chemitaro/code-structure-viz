---
種別: disc
ID: "20261001t142600z-disc"
タイトル: "A public semantic v2契約スライスの実装・検証記録"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-10-01"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: ["20261001t142559z--a02-public-semantic-v2.md", "requirement.md", "design.md", "plan.md"]
reflected_to: ["plan.md", "report.md"]
---

# 20261001t142600z-disc A public semantic v2契約スライスの実装・検証記録

## Inputs

- scope: A02-3のavailable public semantic-document/v2、generic dispatcher/v2、機械的に必要なprivate parent analysis context。unit baseは`ae15deb505d610f74e7c59b506b001b5224c4235`。production、asset policy、early source prefix、publication bytes/measurement、run/domain/root/stdoutは対象外。
- authority: Requirement/Design/Planの初頭Current節、accepted A ADR。旧Round節とraw外部回答はauthorityではない。累積Strict固定点はユーザー選択済み`f4159066f3954454ad2f0c2701fa54bf1bc7bc4a`。
- fresh ChatGPT Implementation Brief Strict: Oracle `issue8-a-public-semantic-brief`、original exec15750、conversation `6abe5b14-8038-83e8-bed2-810aeaba528c`、2026-10-01T13:07:18.974Z→13:30:00.096Z、elapsed22m40s、元job exit0 / completed。
- model/thinking picker: requested/resolved GPT-5.6 Sol、Pro、両verified=true（13:07:23.323Z / 13:07:23.502Z）、thinking strictFailClosed=true。これはUI観測で、backendの内部identityの独立証明ではない。
- promptSubmitted=true、submittedPromptHash=`c1ed520fb9ef7920c0ad3a7a4197e8373fe68f2dfbfa1ec65ebb99af4c519154`。browser-only、research off、19 files、native estimated93456 tokens。GitHub exact ae15debはprompt-enforced connectorの報告で、機械attestationではない。
- 保存原回答全1333行を主担当が通読し、source/schema/known hashesへ照合。原Workbench bytes SHA-256=`17c7b0a66b220089dcf0d5980a1e19018ded897b745599561792ebdbe2a6aa57`。tracked generic copyは4行の末尾空白だけを正規化し、SHA-256=`74893b319233d9507d064e96d1ed7b6bcdc37651d9d1b3ad222dab9a1cb11d37`。original Workbench/Oracle bytesは変更しない。
- Oracle transcript SHA-256=`e3fdb031cf6c9cbb990705466c60f405f69f6b039ca5a8ba9ba6848e9b1672da`、meta SHA-256=`87a734eea616ad16548cfb71b468778ccf60c6f71bd0e114ef3c5ca836dc0028`。
- 設定はcaller-reported GPT-6.1 Sol / Max（backend未検証）。Luna workflowは順序の参考でモデル変更ではない。実装は主担当、サブエージェント無し。長時間の外部分析は元sessionだけで静かに待ち、UI監視やduplicateは行わない。

## Synthesis

公開requestに必要なdepthとdomain-config digestを、rendererがdefaultやfree hashから補完してはいけない。既存child wireに無い親のresolved intentは、同じsource/assets ownerと一緒にprivate `RetainedNextAnalysisContextV2`へ保持する。frameがそのownerとprivate digestを保持することで、child wireが同一でも別depth contextへの差し替えを拒否する。既存request schema/wire/IDを変更する必要はない。

Core-admitted `ValidatedSemanticDecisionV2`だけが新producerへの入口である。complete-emptyも実source/proof/decisionを要求し、proof-backed partial-safeだけをincompleteで公開する。unavailable/rejection/duck ownerを空の成功へ変換しない。validatorはproducer/共有expected-record builderを呼ばず、source/config/request/binding/gate/compatibility/model/orderを独立joinする。

generic v2は旧Python/SQLAlchemy v1文書と新Next v2をexclusiveにrouteする。旧generic-v1 branchをdomain限定しないと、Next-v1がbypassになる。旧schema bytesとdocument identityは維持し、Next-v1やv1/v2混在をnew dispatcherで拒否する。offline registryのretrieval URI登録はschemaそのものの改版ではない。

source/config/entity algorithmsはv1、document/compatibilityはv2である。新public run fingerprintはDesignの13-key preimageをsame ownerから導出し、candidate hash、host path/PID、private wire/provenance/compatibility hashを足さない。旧巨大whole-runtime helperの追加fieldsや強いverified-FD certificateを流用しない。metadata上のTypeScript versionはactual TS import/useと区別する。

## Options and trade-offs

採用したのは最小のprivate parent contextとdecision-only public producer/独立validatorである。公開rendererへfree depth/config/digestを渡す案はowner境界を弱めるため採らない。child wireへdepth fieldsを追加する案はこの機械的sliceの範囲を超えるため採らない。ただし、このprivate contextの保持は任意depthのgraph/query-selectionを実行した証明ではない。actual TS/Core selectionの接続はA04で受入れる。

外部回答の補正を次のように限定した。

- 回答途中の「12 fields」は誤記で、列挙と後段自己訂正どおり13 keysを採る。
- configのprojectsはactual applicable rootsへfilterする。source-plan/config-resolutionは同じfull sealを保持する。
- 旧whole-runtime fingerprint helperの追加Unicode/ledger/process fieldsを新document hashへ持ち込まない。維持するUnicode/entity algorithm自体は変更しない。
- `git fetch --no-tags`、shell `mkdir/tee`、別push shapeはそのまま実行しない。現行AGENTS/skills/user.rulesを優先し、apply_patch、WorkBench ensure、直接allowlisted Gitを使う。
- 必要なin-scope整形はdeveloperが許可するRuff formattingとする。原回答の一律formatter禁止は採用しない。
- attachment引用や空引用をexact repository attestationへ昇格しない。local canonical/source/testsへの照合を別証拠にする。
- 資材I/O unavailable対package違反fatalの未採択policy、early prefix、publication chain、production refactorはこのbriefで解決済みとしない。

## Implementation / TDD evidence

- 新context factory欠落のAttributeErrorを意図したRED→最小factoryでGREEN。
- requestの旧2 positional signatureに3番目contextを渡してTypeError RED→same-owner context保持でGREEN。
- 同じwireの別depth context差し替えが通るRED→private context stampと独立joinを追加してGREEN。
- Next semantic-v2 schema欠落のFileNotFoundError RED→closed exact-ref schemaでGREEN。
- public producer/validator module欠落のModuleNotFoundError RED→decision-only入口でGREEN。
- generic semantic-v2 schema欠落のFileNotFoundError RED→限定old-domain/new-Next branchでGREEN。
- 既存拒否guardが初回から通ったhardeningはGREEN regressionであり、架空のREDを記録しない。nested entityのunknown field拒否はoneOf上位errorとなるため、壊れやすいmessage regexをerror path検証へ直した。製品guardを弱めた修正ではない。
- independent test-side projectionはproducer実装前に明示した。known literalsはその期待recordからapply_patchで初回固定し、新producerはfixture生成に呼んでいない。以後producer変更で自動再生成しない。
- `jq -cS . <file> | tr -d '\n' | shasum -a 256`の独立結果: 13-key preimage=`066d76ba2cfbae97b137a7a1bd59a4181dee2c0ccf31f5c013a9a1735dc8c56e`、complete public record=`d9cd6519d5911be7f043dfcec3ddb96a71cfaaccc11532a74191cedb99b3b13e`。ASCII/NFC差の無いvector、末尾LF無しのreference record KATでありpublication sealではない。
- 既存request known vectorは3961 bytes、ID=`364ae1c7150c97541f990bffc4a864ebc405cdf5d0472f3c250434a8f1375197`、wire SHA=`2775c51cb98c3a0c024521007b9c3473c65720ae592597fb9f4c7a9e675ce44f`を保持。
- formal focused/adjacent、bounded contracts/security、static、SpecDockの最終結果は下の検証欄へ記録する。subsumed selectionは合算しない。

## Verification

unit base ae15deb上のauthorized implementation worktreeで実行した証拠。code/tests/schema/known literalsは下記gate後に変更していない。checkpointのfull SHA/parent/clean equalityはGitとignored run-stateで記録し、このArtifact内へ自己参照commit hashを補完しない。

| 実行command | observed result |
| --- | --- |
| `uv run --group dev pytest -q tests/contracts/test_next_analysis_context_v2.py tests/contracts/test_next_public_semantic_v2.py` | exit0、70 passed、40.83s |
| `uv run --group dev pytest -q tests/contracts tests/security` | exit0、1316 passed、356.63s。large exact/+1を除外せず、旧contract/new owner/schema/golden/securityと隣接request/exchange/Coreを含む |
| `uv run --group dev ruff check .` | exit0、All checks passed |
| `uv run --group dev ruff format --check .` | exit0、209 files already formatted |
| `uv run --group dev mypy src tests` | exit0、173 source files、issues無し |
| `./spec-dock/scripts/spec-dock sync --no-github --no-update-active` / `validate` | exit0、generated projections sync、10 nodes valid、active変更無し |
| `git diff --exit-code ae15deb505d610f74e7c59b506b001b5224c4235 -- src pyproject.toml uv.lock schemas/next-semantic-v1.schema.json schemas/semantic-v1.schema.json schemas/next-config-v1.schema.json docs/contracts/next-semantic-v1.md` | exit0、production/依存/package/主要旧v1 surface差分無し |
| `git diff --check` | exit0。staged全candidateでも再確認する |

新focusedはcontext15/public55を含む70件。18 dispatcher casesはNext2 nominal、旧Python10/SQLAlchemy6 golden、cross-version拒否を含む。既存両domainの実CLI diff outputにもnew dispatcherを適用した。public component merge vectorは手作業model/proofであり、CardのTypeScript recognitionを認定するcaseではない。generic shapeだけの旧Next1 recordは旧schemaで成立することを確認した後、新dispatcherで拒否し、v2 runtime certificateへ変換していない。

初回expanded public/schema selectionは175 passed/1 failed（unknown nested entityを拒否していたが、testのmessage regexがoneOf上位errorに一致しなかった）。error path assertionへ修正し、nested focused3 passed→全focused70→bounded1316でGREENを確認。通常hardening修正でありsemantic findingやproduction failureではない。

全pytest、actual Node/TypeScript/CLI、両OS、offline wheel/sdist、PlantUML描画、全新publication/terminal matrix、A03/Finalはこのcheckpointで実行していない。旧source/private runtime corpus回帰は新productionの証明ではない。A03 certificateではない。

## Reflection

新leaf契約は`docs/contracts/next-semantic-v2.md`、request API変更は`docs/contracts/next-adapter-request-v2.md`、限定進捗はCurrent Plan/Reportへ反映する。新資材failure policyは未採択のまま、旧v1 schema/docs/production/dependency/package surfacesは変更しない。reader-owned prefix、run/publication/domain/root/stdout全refsとterminal matrix、全A02 gate、A03、actual TS/CLI/offline package、Issue全体の完了は残る。分析/implementation briefは独立review passではなく、主担当がA03を自己認定しない。
