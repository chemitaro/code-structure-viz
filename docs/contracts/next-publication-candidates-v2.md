# Next.js request-bound publication candidates v2

## 対象と認定範囲

`code-structure-viz.next-publication-candidates/v2`は、同じrequest-bound runとCore判定に属する、要求済みsemantic JSON／PlantUMLの保持bytes・実descriptor・元のcapture計測をまとめるA02のreference契約です。最終publication decisionではありません。

`retain_request_bound_publication_candidates_v2(run_decision)`の唯一の入力は、既存の独立validatorで再照合できるnominal `RetainedRequestBoundRunDecisionV2`です。caller bytes、Core、context、format、status、hash、limit、計測値を追加引数で渡せません。target sourceの再読や、破棄済みfailure frameの再取得は行いません。

これはreference data laneです。実Node／TypeScript／OS時系列、filesystemへのpersist、CLI、stdout選択／copy、公開stderr、最終exit、installed packageの受入れを認定しません。新ASSET failure policyやrequest-independent／interrupt terminal policyも採択・実装しません。

## 所有者と候補集合

閉じたconstructorを持つimmutable ownerは、同じrun object、同じCore objectを保持するartifact ownerのtuple、immutable metadata bytesを保持します。bytesは`bytes`、metadata getterはfresh dict、reprはprivate fieldを表示しません。validatorはcacheの一致だけではなく保持ownerから独立に再導出します。内部attributeを書き換えた負例は、不正conformance inputであり、public mutation APIやhostile same-UID防御の主張ではありません。

| 同じrunのCore結果 | 候補 |
| --- | --- |
| `complete` | 要求された形式の実bytes。complete-emptyもsource／proof admissionが必要です。 |
| 証明付き`partial_safe` | 同じ安全なsubsetとincomplete表示を持つ要求済み候補。 |
| target／export／entity unavailable | 空tuple。空の成功や代替空図は作りません。 |
| typed Core rejection／通常runtime failure | 空tuple。元のfailure record／計測だけを維持します。 |

形式はheld parent contextの`requested_formats`から決まります。`[semantic-json]`、`[plantuml]`、`[semantic-json, plantuml]`の三通りだけで、両形式の順序はJSON→PlantUMLです。`stdout_selector`が一つのdomain形式を指定しても、要求済み候補集合は減らしません。selectorの実stdout可否判定は後続finalizerの責務です。

`artifact_bytes("semantic-json" | "plantuml")`は、その候補がないとき`None`を返し、空bytesを成功の代替にしません。未知formatは拒否します。leaf factoryは単独ではrequestednessを証明せず、aggregate validatorが同じheld requestへ結びます。

## 閉じたmetadataと実計測

新schemaの五つのrequired fieldは以下だけです。

| field | authority |
| --- | --- |
| `schema`／`version` | 固定identity／実整数`2`。 |
| `run_decision` | 同じrun2 ownerのrecord。v2へのexact refです。 |
| `artifacts` | 保持している実候補の六field descriptorのみ。base64／bytes／manifest descriptorを埋めません。 |
| `capture_measurements` | 同じruntime observationとrequest-owned limitsから導出。 |

captureの`adapter_stdout`／`adapter_stderr`は両方null、または両方四field objectです。元のcapture自体がない場合だけnullで、ゼロbytesの取得とは区別します。各objectは`captured_bytes`、`capture_retained_bytes`、`eof`、`limit_bytes`です。整数は実整数、EOFは実boolで照合し、同値float／boolの別表現を許しません。

`capture_retained_bytes`は元observationに記録された取得時の量です。この新ownerがfailure raw bytesを保持したこと、破棄後のメモリzeroization、OSでの実captureを証明しません。公開stderrの64 KiB byte gateとも別です。

descriptorの固定値は次です。`size_bytes`／`sha256`は保持bytesから独立に再計算します。

| format | path | media type |
| --- | --- | --- |
| `semantic-json` | `next.snapshot.semantic.json` | `application/json` |
| `plantuml` | `next.snapshot.puml` | `text/vnd.plantuml; charset=utf-8` |

旧publication-v1のversionless `$defs/artifact_descriptor`という六field shapeだけを再利用します。旧run／runtime／publication ownerへdowngradeする経路はありません。新schemaはrequested format集合・順序・available/unavailableを閉じます。schemaのshape passだけでbytes／owner／計測の正しさを認定しません。

## 独立検証とencoding

aggregate validatorは新producer、renderer、共有expected-record builderを呼びません。既存run2 validator、Core validator、JSON public-record validator、変更しないPlantUML statement parser、canonical codec、SHA primitiveは再利用します。

JSONは同じCoreのpublic recordをcanonical UTF-8 JSON＋末尾LF一つとして保持します。PlantUMLは同じmodel／outcomeの既存statement契約を維持し、UTF-8、BOMなし、CRなし、LF-only、末尾LF一つ、blank／comment／余分なstatementなしを照合します。順序・escaping・marker・facet・relationの変更は再hashしても拒否します。

JSONのclosed public recordに含まれる数値はすべて整数です。JSON Schemaの`integer`だけでは整数値のfloat（`1.0`）を拒否できないため、独立public validatorがrecordを再帰走査してfloatを拒否してから、source／request／compatibility／collections／entitiesを元の値・文字列・順序どおりownerへjoinします。数値literalの値自体はTypeIRへ公開せずredacted shapeにします。元Coreにfloatがあっても、それを公開整数へcoerceしません。`1`と`1.0`を取り違えた再hash済み候補、float size、同じcacheへ合わせた偽descriptor／capture計測も拒否します。

既知JSON-only vectorは9472 bytes／SHA-256 `545389abfa3975b2c95083db9cca6b8efbe071c4526b90cbe55fe9bdc84b5957`です。両形式はformatsとselectorがconfig／13-key fingerprintへ結合するため、このhashを無条件には流用しません。worked PlantUML literalは1082 bytes／24 LF／SHA-256 `0bce98e4e12b722ff2685a76c52bddba7bca735af090ad735d94bbfc9e50c2a9`で、producerからfixtureを生成していません。

両形式の独立vectorはdepth0/0、JSON 9483 bytes／SHA-256 `7e15f037bd341e26398f0bc6f8133d0ff5872ee3a7244e714b477d15d7aa634f`、元capture stdout 6332 bytesです。JSON-onlyは元のdepth1/1、元capture stdout 6320 bytesであり、candidate sizeとは別です。metadata literals三件は既存lower-boundary run literals、test-sideで明示したpublic preimage、worked PlantUML literalから作成し、新candidate producerやrendererの出力で更新しません。固定file SHAはtestとIssue Artifactへ記録します。

## 実サイズ境界と後続closure

候補作成にselected stdoutの16 MiB capを適用しません。実source seal／request／response／Core／runの正常経路から、候補JSONの16 MiB exact／+1が両方保持できることを検証します。巨大bytesのpadding、偽artifact、任意の小さいlimit、先行gateで拒否された入力を代用しません。実測結果と実行範囲はIssue Reportへ記録します。

境界fixtureは1000の実program filesを有効な長いrelative pathsに配置し、descriptor-relativeに作成・read/sealします。各fileは既存source corpusのCard bytes、modelは対応する1000 Modules／router factsとfull proofです。独立期待JSONの長さをpath長の四箇所への投影と実context `.d.ts` file sizeの十進桁差で調整し、最終入力をfresh source sealから正常admissionへ通します。最終JSONへのpaddingやowner改変を使いません。stdin 96 MiB、response 16 MiB、decoded source、各path/string/modelの元上限は維持します。これはreference dataの到達性で、実compilerやstdout copyの認定ではありません。

依存順序は非循環です。

```text
same runtime / receipt / Core / parent context
  -> run2
  -> requested JSON / PlantUML leaf bytes
  -> actual descriptors + original capture accounting
  -> retained candidate set
```

後続はcatalog-owned diagnostics／public stderr bytes、safe domain／root／summary／typed unavailable candidates、held selectorのpre-copy候補、selected-copyを一度だけ行う判定、semantic outcomeを変えないfinal disposition、最終bytes／計測／descriptorを保持するsingle final owner、publication/domain/root/stdoutのv2 exact refsを順に閉じます。測定したpre-copy候補と最終failure-status manifestをすり替えず、full record／sealを自身のhash対象bytesへ再帰埋込みしません。

このcandidate checkpointをwhole A02、独立A03 Strict pass、A04 production、A05／Issue完了へ読み替えません。reader-owned early prefix、未採択ASSET方針、final publication全chainと網羅gateは残ります。
