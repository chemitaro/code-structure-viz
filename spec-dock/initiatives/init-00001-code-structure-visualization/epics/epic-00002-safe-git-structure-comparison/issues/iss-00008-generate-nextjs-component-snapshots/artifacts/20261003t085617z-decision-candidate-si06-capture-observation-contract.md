---
種別: decision-candidate
ID: "20261003t085617z-decision-candidate"
タイトル: "SI06 capture observation contract decision"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-10-03"
親: ["iss-00008"]
template: "decision-candidate"
authority: "draft"
derived_from: ["20261003t085653z-01--si06-brief-compatibility.read-view.md", "20261003t085654z--si06-brief-compatibility-probe.json"]
reflected_to: []
---

# SI-06公開計測契約：未観測と0を区別するための判断材料

未採択のdecision candidateです。schema変更、version選択、移行の承認ではありません。以前採択したA runtime／owner-closed File・Module公開方針を取り消すものでもありません。今回判断するのは、起動前失敗を公開する際のcapture計測の表現と、その訂正をどのschema版へ反映するかだけです。

## 結論と現在地

推奨は、現在の`next-publication-decision-v2`へ**両captureが未観測なら両方null**という限定訂正を加え、仕様チェックを先行することです。ただし、外部consumerがobject必須を前提にしている場合は同時更新が必要です。既存版不変の保証が必要なら後継版を選びます。未確認の外部利用を「存在しない」とは断定しません。

- SI-03 source/proof、SI-04 Core、SI-05 public/exact-ref referenceは、それぞれの記録済みexact SHAで部分認定済みです。
- SI-06の実装ブリーフは回収・全文照合済みですが、公開schemaとの不整合が見つかったため、現状のまま実装入力に採用していません。
- SI-06のコード／schema／受入テストは未変更です。製品のTypeScript解析、OS／CLI／package、全A02/A03、Final、Issue #8の完了ではありません。
- 元SI-06 baseは`af6f5d33f9487a33dabf2ddfe41df85b3d8267fb`のまま固定します。証拠保存checkpointを新baseにしません。

## 何が起きているか

### F1：合法な失敗状態をschemaが表現できない

同じrequestに結び付いた既存`stage_failed`経路は、起動／captureが起きていないため、runtimeの`capture=None`、候補の`adapter_stdout=null`／`adapter_stderr=null`を保持します。これは未観測を正直に表す正常なfailure recordです。

ところが、最終公開schemaの`measurements.adapter_stdout`と`adapter_stderr`は、常に次のような計測objectを要求します。

```json
{"allowed": true, "measured_bytes": 0, "retained_bytes": 0}
```

このobjectは「実際に計測して0 bytesだった」という意味であり、未観測の代用品にはできません。

| 実際の状態 | 元ownerの意味 | 正直な最終表現 | 現schema |
| --- | --- | --- | --- |
| 起動前のstage失敗 | capture未観測 | 両方null | 拒否する |
| capture実施、0 bytes | 観測済み0 | 両方計測object | 表現可能 |
| capture実施、上限超過 | 実測した超過 | 実測object、該当allowed=false | 表現可能 |

read-only probeは既存fixture／通常factoryでruntime→run-v3→candidates-v3を構築し、両nullと現schemaのnull拒否を確認しました。偽Core／seal、縮小した上限、架空の成功certificateは使っていません。これはschema断片との照合であり、未実装final ownerの受入テストや実OS起動の証拠ではありません。

最初の不整合はlower runtimeやCoreではなく、公開schemaへの統合層です。0埋め、架空overflow、stage_failedの除外、下位ownerの変更では、既存の未観測／0の区別またはrequired coverageを壊します。

### F2：解析結果と公開処理の結果は別の軸

こちらはschema変更を要する第二の問題ではありません。原briefの説明不足を、既存Designと維持baselineへ照合して解消できます。

- 解析が不成立でも、失敗結果のmanifest／診断を正しく公開できたなら、semantic/runは`payload_unavailable`、publicationは`published`、exitは3です。
- 検証済みCoreがあるSOURCE／TARGET／EXPORT／entity-budget失敗では、同じtransport由来のresponse識別情報を保持できます。公開artifactは空です。
- rejected Coreやruntime-only failureではresponseを補完しません。
- capture上限または最終stderr上限を超え、公開処理自体が`payload_unavailable`になった場合はresponse=null、artifacts空へします。

`published`は「解析が成功した」ではなく「公開境界が結果を正常に封印・公開した」です。この切り分けは既存baselineの`_materialize_publication_boundary`／`next_publication_decision_projection`と現schemaから導けます。旧finalizer全体、再capture、旧owner/certificateを新v3へ流用する許可ではありません。新ownerでの実行証拠はまだありません。

## 選択肢と互換性

| 選択肢 | 変更範囲 | 利点 | 影響／条件 |
| --- | --- | --- | --- |
| **現v2の限定訂正（推奨）** | publication-v2のcapture二fieldとpaired-state制約、対応テスト／新final owner／正本説明 | 既存outer exact refsを維持できる。SI-06の変更範囲が最小 | 旧object-only consumerは新null recordを拒否する。未公開のtarget contractとして訂正する、またはconsumerを同時更新する判断が必要 |
| 後継版へ移行 | 新publication identity、依存domain/root/stdout等のexact refsとconsumer／rollback計画 | 既存v2の契約を不変に保持できる | 新版の番号、URN、移行対象、切替規則を先に決定する。暗黙のdual reader/writeは追加しない |

0埋めやbranch除外は採用可能な選択肢ではありません。新しい観測を捏造するか、合意済みcoverageを削るためです。

ローカルconsumer censusでは、publication-v2の参照は四schema、`next-semantic-v3.md`、二schema testにあり、検索した`src/**`には一致がありません。planned SI-06 finalizer七pathも未作成です。これはrepo内の現状態で、release済みrecord、外部schema利用、永続consumerの不存在を証明しません。

推奨の根拠は、新final ownerがまだ未実装の段階で、下位owner・解析意味を変えずに欠落状態を閉じられることです。一方、公開版を不変とする運用保証または外部consumer維持が必要なら、最小差分より互換性を優先して後継版を選びます。

## 未採択の限定訂正文言

Candidate text — not adopted: `next-publication-decision-v2.measurements.adapter_stdout`と`adapter_stderr`は、同じcandidates-v3のcaptureが両方nullの場合に限って両方nullとする。nullは未観測を表し、0-byte observation、allowed=false、overflowを意味しない。観測済みは従来の計測objectを維持する。片側null、zero-fill、再captureを禁止する。public_stderrとselected_stdoutは常に実測objectとする。

Candidate text — not adopted: 現v2 target contractを上記の範囲で訂正し、producer／validator／schema vectorsを一緒に切り替える。既存object/object recordは引き続きvalidとする。旧object-only consumerへ新null recordを無条件に送らない。外部consumerまたは永続recordの互換性維持が必要と判明したら切替を止め、後継版または同時更新の判断に戻る。

このArtifactの保存や過去のオプションA採択だけでは、上のpublic-contract変更は採択されません。F2の既存意味に沿った説明訂正はlocal advisory clarificationとして受け入れますが、F1未決のままwhole SI-06 briefを実装可能にはしません。

## 採択後の作業順序と出口

1. 限定訂正か後継版かを人間が採択し、互換性の扱いを確定する。
2. Requirement／Design／Planと契約文書へ先に明記する。scope外のreader-prefix、新ASSET、production、旧schema/KAT、runtime/Coreは変更しない。
3. clean/pushed exact spec SHAでChatGPT Spec Review Strictを実施する。過去のpassを新意味へ流用しない。
4. 採択済み意味へbriefを改訂し、first Red→Greenでschema表現／同じownerのfinal projectionを閉じる。
5. 観測済み0、両null、片側null拒否、0埋め拒否、foreign owner拒否、response/outcome matrixを検証する。
6. configured 64KiB stderr exact/+1、16MiB selected-copy exact/+1を実bytesで検証する。元candidateのpre-copy計測と最終replacement stdoutを分離し、再計測・partial write・再captureをしない。
7. 同じfinal candidateで必須aggregate／回帰／statics／docs checks、通常checkpoint/push、元af6fからのfresh独立Code Review Strictを実施する。P0/P1=0／valid passまでSI-06を認定しない。P2/P3はreport-onlyのまま。

元SI-05認定`6d52ff7949d64e747235eef870631cd8cc29b273`は当時のsource/schemaとscopeの証拠として保持します。訂正後schemaの証明には使わず、新candidateの検証記録で当該契約範囲だけをsupersedeします。既存public ownersや旧証跡全体を取り消したり、過去のraw passを書き換えたりしません。

rollbackもschema／producer／validatorを一緒に扱います。paired-null producerだけを旧object-only schemaへ戻すmixed stateを認めません。新しい第三capture状態、片側未観測、lower contract変更、追加wire/versionが必要になった場合は局所修復を続けません。

## 原証跡と再開用資料

分析対象のrepository／branch／full SHAは`chemitaro/code-structure-viz`／`iss-00008-generate-nextjs-component-snapshots`／`af6f5d33f9487a33dabf2ddfe41df85b3d8267fb`です。以下はgeneric evidenceで、自動的なcanonical authorityではありません。

| 資料 | 保存先 | 内容／整形 |
| --- | --- | --- |
| 回収済み原author brief | [lossless gzip](20261003t085652z--si06-diagnostics-final-owner.md.gz)、[可読版](20261003t085652z-01--si06-diagnostics-final-owner.read-view.md) | rawは2251 LFと最終非LF行。可読版だけ一行の末尾spacesを除去し、最終LFを一つ追加。意味は未採択 |
| 独立指摘分析 | [lossless gzip](20261003t085653z--si06-brief-compatibility.md.gz)、[可読版](20261003t085653z-01--si06-brief-compatibility.read-view.md) | 原906行／11 H1を全文照合。可読版だけ五行の末尾spacesを除去 |
| complete primary packet | [lossless gzip](20261003t085653z-02--si06-brief-compatibility-packet.md.gz) | 原brief全文、二つのsource-native所見、complete probe、authority／scope／履歴／政策を保持 |
| actual-owner probe | [script](20261003t085653z-03--si06-brief-compatibility-probe.py)、[結果](20261003t085654z--si06-brief-compatibility-probe.json) | clean af6fのread-only診断。final-owner test／TDD Redではない |
| author lineage | [JSON](20261003t085654z-01--si06-author-lineage.json) | 同Blue会話の回収、元exit1／回収exit0、model観測限界、当時のpending status |
| analyst lineage | [JSON](20261003t085654z-02--si06-brief-compatibility-lineage.json) | fresh separate Sol/Pro、両picker verified、元98849 exit0、意味採択は別 |
| transport recovery | [記録](20261003t085654z-03--si06-original-session.md) | stale answer不採用、送信済みturnの再確認、lost observer exit未知、原会話での完了 |

raw SHA-256はbrief=`89874d1617df851ada743baf716a6c32b835ca59b2773cf09a813d066ef8ad8f`、analyst=`08b2983b76d11a69ec46a12d9a4d30fedf7dd0d79148ba5598553122951c4091`、packet=`b3e7822ca93b5c73017c8aab912d762d2b2752d5303f803d533bc7fbc81b6e52`です。probe script=`7cb78da88a3364ddad67b47db9fec806d82c7eba17d6581c675871500d20905f`／結果=`eac06a1e3128c6e578d60d02ad4f214dea1541aab6a1fa19ecd9136b13ac64be`、原analyst log=`2405f5eabacc59aa78ed808b10d3182998870122f6ad3e000439aeed379ff3e6`、完了回収log=`639a3bd15c9f6537a6c482b81dd84f90f3523f3d1e1fbc4c1789a0e651c21af0`。logsは既存ignored Workbenchへ保持します。

authorはsame Blue `6abf39d9-bdc0-83ee-96f7-79bde716eb7f`、native `issue8-si06-final-publicatio`。要求Sol/Extra Highですがmodelは継承skipped/unverifiedfreshで、Extra Highは観測済みです。別analystはnative `issue8-si06-owner-admission`／conversation `6ac0bd51-3764-83ee-ab90-19072c7a5ce4`、2026-10-03T08:30:25.599Z〜08:47:33.625Z、要求Sol/Proの両UI picker verified。backend identityの外部attestationはどちらにもありません。

原所見`SI06-BA-F1/F2`はprimary admission observationsで、P severity unset／formal review_statusなしです。分析をCode Review passやseverity付きfailへ変換しません。reviewerの助言によってschema編集権限も作りません。

## 保存時の検証と未確認点

- SpecDock command-firstで十regular filesをgeneric importし、source／destinationの全bytes一致を確認しました。三gzipは展開後の原bytes/hash一致、二可読版は上記整形だけの一致を確認しています。
- analyst original98849 exit0、全906行／exact十一H1の順序と、requested Sol/Proの実picker観測を確認しました。GitHub tip一致はanalyst回答に記録されています。
- actorのread-only probe69095 exit0はclean af6fへbindします。原実行コマンドは`uv run --locked --group dev python -c 'import runpy; runpy.run_path(".workbench/luna-max-implement/issue8-nextjs-snapshots/recovery/si06-brief-compatibility-probe.py", run_name="__main__")'`です。移動済みArtifactを現cwdから再実行すれば新たな診断であり、旧結果のSHA証明にはなりません。
- 保存候補のproportional checksは、HEAD af6f＋この十三pathのdocs/evidence差分に対して実施しました。`uv run --locked --group dev`で`pytest tests/contracts/test_json_schemas.py -q`が133 passed（4.51s、元69210 exit0）、`pytest tests/contracts/test_next_contracts.py::test_round23_rg_18_current_schema_and_history_contract_are_explicit -q`が1 passed（0.13s、exit0）。`ruff check .`、`ruff format --check .`（249 files）、`mypy src tests`（207 source files）もexit0です。`spec-dock sync --no-github`はactive unchanged、`validate`は10 nodesでpass。既存code/schemaが不変のため、all-contract/full pytestは再実行せず、旧SI-05実行結果を本docs候補やSI-06の新passへ拡張しません。
- SI-06実装／required acceptance／新Spec Reviewはまだ実施していません。公開契約採択とその後のchecksが必要です。外部・永続consumer、未確認OS branchは未確認のままです。

採択を受けるまでは`authority: draft`／`reflected_to: []`を維持します。再開に必要な判断は「現v2の限定訂正で進む」か「既存v2を不変にして後継版へ移す」かです。
