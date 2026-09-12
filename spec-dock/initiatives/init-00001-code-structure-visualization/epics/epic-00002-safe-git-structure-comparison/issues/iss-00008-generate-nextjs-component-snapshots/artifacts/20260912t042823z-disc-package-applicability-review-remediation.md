---
種別: disc
ID: "20260912t042823z-disc"
タイトル: "Package Applicability Review and Remediation"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-09-12"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: []
reflected_to: []
---

# 20260912t042823z-disc Package Applicability Review and Remediation

固定SHAに対する独立レビュー、Issue #8のcurrent-v1契約、局所再現をまとめた実装前分析。これはevidenceであり、Requirement / Design / Planを置き換えない。

## Inputs

- 統合する evidence:
  - Candidate: `7d094f0a66c42e3907846ec123ed0649d0b89e3e`; fixed point: parent `8f17f40055f6dc892bd53f8d51349a2f607ade8b`.
  - Branch `iss-00008-generate-nextjs-component-snapshots` は clean で、local HEAD、configured upstream、GitHub origin branch が同じ `7d094f0...`。差分は1 commit、5 files。
  - Issue `requirement.md` current-v1 authority（immutable decision chain、Unicode 15.0.0 profile、canonical index/reference validator）、`design.md` current-v1 authority、`plan.md` package-only preflight順序。
  - `schemas/next-path-v1.schema.json` と `tests/contracts/next_reference_validation.py` の path / package-applicability 契約。
  - 独立 GPT-6 Max Standards / Spec review reports。外部 ChatGPT Use Strict / ChatGPT strict review skill は、直近ユーザー指示により停止中のため使用していない。内部レビューを外部Strict passとは扱わない。
  - 初回候補の検証: full pytest `1487 passed, 1 skipped`; applicability unit `23 passed`; current-v1 parity `4 passed`; Ruff, format, mypy, SpecDock validationは成功。

## Synthesis

- 一致する事実と未確定事項:
  - Standards: 文書化された標準違反は0件。`ST-1 possible Duplicated Code` は判断上の指摘であり、hard violationではない。`PackageApplicabilityEntry`のpackage path式と `_package_path` が重複している。
  - Spec: `P0=0 / P1=1 / P2=2 / review_status=fail`。`SP-1 [P1, implementation error]`: frozen dataclassが外側のobservationsだけをtuple化し、mutableなinner listを保持する。再現ではroot matrixが`applicable`のまま、後変更した`b"{}"`のsize/SHAを観測した。requirement current-v1の同一immutable decisionとreference validatorのinner tuple検査に不一致。
  - `SP-2 [P2, partial implementation]`: `apps/web#x` と project root 4084 UTF-8 bytes＋`/package.json`＝4097 bytesをproduction classifierが受理し、referenceが拒否した。4096 bytesはinclusive boundaryとして受理されるべき。Issueのcanonical path contractは`#`と4096-byte超過を拒否する。
  - `SP-3 [P2, implementation error]`: host `unicodedata.normalize` を使用。root `apps/\U000105d2\u0307` はPython 3.12.11/UCD 15.0.0と固定referenceでは受理、Python 3.14.6/UCD 16.0.0では同じproduction classifierが拒否した。IssueはUnicode 15.0.0 NFC profileを固定する。
  - 追加再現（reviewerのP件数には含めない）: 20,011-byteのvalid deeply-nested JSONで `RecursionError` が分類器から漏れる。str/int payloadでは`AttributeError`、present `None`はreference同様`missing_package`になる。str/intは宣言型`Mapping[str, bytes]`外、`None`は欠落表現との曖昧さがあるため、各々の扱いを分離する。
  - Unit/parityテストは当初すべてgreenだったが、mutable row、`#`/byte boundary、Unicode version境界を閉じていなかった。これはimplementation evidenceのcoverage gap。

## Options and trade-offs

- 選択肢と利点・制約:
  - 採用: accepted current-v1 contractから一意に決まるため、production applicabilityの範囲内で修正する。observed rowsをdeep-freezeまたは拒否する回帰テストを追加する。rootと派生`package_path`の両方へcanonical path validationを適用し、Unicode 15.0.0 frozen normalization tableをproduction helperから使う。宣言型外の非-bytes runtime inputは観測値として保存せず、制御された`ValueError`で拒否する。parserの`RecursionError`はmalformed evidenceへfail-closedし、referenceも同じ境界へ更新する。ST-1はpackage-path helperを共有して重複をなくす。
  - 保持する保証: direct-dependencyだけでapplicabilityを決めること、aggregate precedence、安全な観測値、schema shape、入力の有効な既存ケース、Issueの固定Unicode/path profile。変更するのは現行契約を破っていた不正入力・unsafe pathの受入れと、parser exceptionの外部漏出だけ。
  - 追加依存、lockfile、Node adapter、filesystem read、CLI route、snapshot生成はこのpackage-only sliceに持ち込まない。Issue #8全体の完了やcloseoutとは扱わない。
  - 不採用: host Unicode databaseへの依存継続（cross-runtimeでpath classificationが変わる）。RecursionErrorを未処理のまま残す案（JSON parser失敗が閉じたmalformed結果を迂回して呼出元へ漏れる）。
  - Human decision: 不要。SP-1〜3はIssueのcurrent-v1 requirement/schema/referenceを満たす実装修正で、目的・公開意味・リスク許容を変更しない。深いJSONも既存のmalformed branchへ閉じ、成功判定を緩めない。`None`は既存referenceと同じく欠落package sentinelとして維持する。

## Fixed-SHA re-review evidence

- Re-review candidate: `514b6fc785a8f523070993b2d224d4bb4ad081ee`; fixed point remains `8f17f40055f6dc892bd53f8d51349a2f607ade8b`. Local branch, upstream, and GitHub origin matched the candidate and the tree was clean.
- Spec re-review: `P0=0 / P1=1 / P2=0 / review_status=fail`. `SP-1` through `SP-3` were confirmed resolved. Standards re-review: documented violations 0, unresolved judgement calls 0; `ST-1` is resolved by sharing `_package_path`.
- `SP-4 [P1, acceptance-test implementation error]`: the two new tests assumed 10,000 nested arrays must trigger `RecursionError`. The same valid JSON returns `malformed` under Python 3.12.11 and `non_applicable` under Python 3.14.6. This makes the latest-stable test lane fail even though the product catches `RecursionError` when the runtime parser raises it.
- Authority analysis: requirement current-v1 line 146 places the nesting-64 limit under transport/process; design line 1120 scopes that limit to request/response. The package-applicability contract specifies UTF-8/BOM/duplicate/root/table/value handling but no package JSON depth ceiling. Extending the 64-depth policy to `package.json` would reject otherwise valid packages under a new package-input policy, so it is not adopted.
- Primary response route: `test-remediation`. Keep the production and reference `RecursionError -> malformed` fail-closed handling, replace parser-version-dependent deep-input assertions with scoped injection of `RecursionError` into `json.loads`, and verify unit plus production/reference parity. No product semantics, canonical requirement, or package depth limit changes; no human decision is needed.
- The 514b6fc review result is historical evidence for this response. Any record of the next verdict changes the candidate itself and therefore requires review of the resulting SHA.

## Reflection

- durable な結論を Requirement / Design / Plan または accepted ADR に再記述する。
  - Current-v1正本は既に必要な意味を定めているため、canonical Requirement / Design / Planは変更しない。このArtifactはレビューと修正判断のevidenceのみ。
  - 現候補のSpec軸review statusはfailであり、次の計画実装段階へ進む前に修正・検証・固定SHA再レビューを行う。re-reviewの最終SHA/verdictをこのArtifactへ追記する場合、その追記自体が新しい候補SHAを作るため、更新後のSHAも改めて固定してレビューする。レビュー証拠はこの記録のまま保ち、P0/P1=0とreview passを証明するまではIssue実装全体を完了扱いにしない。
