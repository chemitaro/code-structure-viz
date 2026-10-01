# Next.js Core semantic admission v2

## TransportとCoreの境界

`validate_semantic_candidate_v2(candidate, source_seal, retained_assets)`は、whole-exchange transport ownerを入口にします。shape-valid payload、transport bool、caller-supplied model/status/gateだけではCore admissionになりません。source/asset stampとresponse echoを再検証し、保持したpayloadのmodel digest、同じrequestのproject/file全membership・metadataを照合します。

Coreは維持するsemantic ID/record/reference/count/proof/targetのalgorithm v1を適用します。新wireを旧request/response envelope validator、旧verified-FD runtime gate、旧publication constructorへ投影しません。依存するのはwire非依存のsemantic要素アルゴリズムです。

proofの非公開recordもsource/ownershipの例外にしません。全frozen project/fileはmodel correspondenceに含まれるため、proof-only project/fileで別の観測sourceを追加できません。proof-only Moduleは実requestのprogram Fileを所有し、その他のproof-only recordの宣言referenceもpublished/discovered setへ閉じます。selected component-only failureのmissing Module IDだけは既存の限定例外を保持します。

判定は次の順です。

1. 保持owner、new wire、source correspondence、model digest。
2. path/order/ID/reference/countの基礎検証。selected File→Moduleの限定的な欠落/component-only/byte-identical duplicate以外は例外を認めません。
3. selected cardinality failureなら、その限定例外を含む**完全なproof base**を検証してtyped target failureへ進みます。無関係な不正recordをtarget failureで隠しません。
4. 通常model/proof、root/taint/causal/disposition、export/target witnessを検証。proof-derived selected taint等はtarget failureです。
5. actual wireのpublished＋proof-only model-record量を10,000 exact/+1で判定。不正proofはcount gateより先に拒否します。
6. validated export failureをtyped unavailableへ。complete/partial-safeをderiveした後、Module＋Component実数をsource-owned entity予算へ照合します。

target failureは`CSV-NEXT-TARGET-001`、export failureは`CSV-NEXT-EXPORT-001`、entity +1は`CSV-NEXT-LIMIT-005`でpayload無しです。model-record +1は既存のtyped `ModelRecordLimitError`を保持し、protocol assertionへ潰しません。entity gateがpartial-safeをcompleteへ昇格させることはありません。zero entityもsource membership/proofが閉じた後にだけ認めます。

## 一つのimmutable decision

`decide_semantic_candidate_v2`がCore検証とparent-owned compatibilityから`ValidatedSemanticDecisionV2`を作ります。constructorは閉じ、同じsource seal、asset owner、typed transport candidate、immutable gate/compatibility bytesを保持します。projectionの後続mutationから再判定しません。`validate_semantic_decision_v2`は同じownerに対してgate/compatibilityを独立に再照合します。

これはreference Coreの内部authorityです。公開run/publication/domain/semantic/root/stdoutのv2 projectionとfinalizerは別のclosureであり、このownerの存在だけでArtifact、stdout、exitや実行成功を認定しません。

## Known corpusと未認定の範囲

`test_next_semantic_candidate_v2.py`はactual production source acquisitionでfixture bytesをsealし、new request/exchangeから入ります。Module/fact/component IDはliteral preimageをjq/shasumで独立計算し、ASCII model bytesのdigestはtestで別codecを明示します。runtime pid/version/counters、compiler無し資材、意味recordはsyntheticであり実TS/OSの結果ではありません。

維持するold reference proof/exportアルゴリズムのcensus/graph oracleはchecked-in known corpusに結合しています。新reference成功はそのcorpusでの契約意味・owner joinの証拠であり、任意TS入力を解析できるproduction compilerの証明ではありません。productionではactual frozen inputに結合する一般化されたfirst-party TS/witness経路が必要です。fixture lookupや旧runtime/envelope gateをproduction fallbackにしません。

さらに、source acquisition failure/controlled child failureから新run decisionへのclosed union、provenance prefix、新public exact refs、publication byte seal、actual CLI/installed distribution/両OS、A03独立Strict reviewは未認定です。旧v1 record/schema/hashを上書きせず、Issue全体を完了扱いにしません。
