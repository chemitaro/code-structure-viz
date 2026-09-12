---
種別: disc
ID: "20260912t053007z-disc"
タイトル: "Next JSONC Parser Review Remediation"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-09-12"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: []
reflected_to: []
---

# 20260912t053007z-disc Next JSONC Parser Review Remediation

複数の証拠を統合し、選択肢と trade-off を整理します。一つの source の調査は `research` を使います。

## Inputs

- 統合する evidence:
  - Candidate 621b9721b33a148077c54c4fd178cb37c609ded9 はbranch iss-00008-generate-nextjs-component-snapshotsにpush済みで、parent 337c04a1ce1fb4905568fcf6b540a2c37bdffc1f とlocal/upstream/GitHub SHAが一致していた。candidateの作業ツリーはcleanだった。
  - design.md current-v1のSourceDiscoveryIntentからSourceAcquisitionPlan/v1への導出とdocs/contracts/next-config-v1.mdが、凍結bytesからduplicate-key rejecting JSONCを扱い、control parse failureをfail-closedにする契約を定める。
  - docs/contracts/next-source-plan-v1.mdはsource controlsを一度だけ観測し、後続の設定導出で生bytesを再読しないことを要求する。今回のdecoder自体はbytesだけを受け取り、filesystemには触れない。
  - 固定SHAレビュー中のStandards reviewerによる補助観測（最終所見とは区別）: b'{"value":1/*x*/2}' が {"value":12}、b'{,}' が {}、b'{"value":[,]}' が {"value":[]} として受理された。
  - 初期candidate 621b972...のレビューは、この補助観測により対象SHAを再び作り直す必要が生じた。candidate `d1260edf7e9e66204b10d93eb2f24fe0940ba492` のレビューではSpecがP0/P1/P2=0でpass、Standardsの文書化規約違反は0件だった。判断事項ST-1はblock-comment終端処理の重複。
  - ST-1は振る舞い変更なしで採用し、`block_comment_end`に終端検索とtyped errorを集約して `b898f030994d18725011866e658c743f86f1127e` をcommit/pushした。同SHAの独立レビューはSpec `P0=0/P1=0/P2=0/review_status=pass`、Standardsの文書化規約違反0件。ST-1は解消済みだが、Standards判断事項ST-2としてline-comment終端走査の短い重複が新たに報告された。
  - ST-2は規約違反・動作不良ではないが、同じ局所的走査を共有する小さな共通化として採用し、`line_comment_end`を追加した。修正後はfocused tests 24件、full pytest 1521 passed/1 skipped、Ruff check、format check（169 files）、mypy（145 source files）、SpecDock validate（nodes=10）がすべて成功した。
  - follow-up candidate `2d1cba6164d2f47f03fa42edf80de39a634fafe9` はcommit/push済みである。同SHAを対象とした累積固定SHAレビュー（base `337c04a1ce1fb4905568fcf6b540a2c37bdffc1f`）はSpec `P0=0/P1=0/P2=0/review_status=pass`、Standardsの文書化規約違反0・未解消smell判断事項0。Specは24 focused testsに加えread-only JSONC probesを確認し、Standardsは12種類のsmell baselineを確認した。開始・終了ともcleanで、local HEAD/configured upstream/GitHub branch refはすべてcandidate SHAに一致した。
  - current candidateでの全品質証拠: focused tests 24 passed、full pytest 1521 passed/1 skipped、Ruff check pass、format check 169 files、mypy 145 source files、SpecDock validate nodes=10、`git diff --check` pass。
  - `analyze-review-findings` と `chatgpt-analyze-review-findings-strict` はこのsessionの利用可能skill一覧になかったため、primaryが両レビューをcurrent-v1 authorityと照合して判断した。ユーザーの現行方針に従い、外部ChatGPTレビューskillは呼び出さず、独立レビューはGPT-6 Max local agentsで実施した。

## Synthesis

- 一致する事実と未確定事項:
  - commentはJSONCの空白として働かなければならない。削除して前後のtokenを連結すると、1/*x*/2を別値のままエラーにせず12として誤読する。
  - trailing commaは、配列/オブジェクトに値またはmemberが一つ以上ある場合に限り終端直前で許可される。closing delimiterの直前にあるだけのcommaを無条件に削ると、{,}や[,]のinvalid inputが空containerへ変換される。
  - したがってparserの問題は許容JSONCを減らすことではなく、コメントをtoken separatorとして保存し、既存の閉じたJSON構文が不正入力をrejectできる状態に保つこと。
  - parserはまだsource acquisition/extends/membershipへ未接続。今回の範囲は後続sealで再利用するJSONC decoderとそのsyntax contractに限る。

## Options and trade-offs

- 選択肢と利点・制約:
  - 採用: comment文字を空白へ置換し、CR/LFは維持する。末尾commaの除去時にはlexerが追跡する直前の有意tokenを確認し、container opener、colon、comma、入力先頭の直後にあるcommaは除去しない。最終的なJSON grammar検証は標準json.loadsに任せる。
  - 回帰確認: 正しい末尾commaは引き続き受理。コメント境界の1/*comment*/2と1//comment\n2、先行値のない{,}/[, ]、二重commaは拒否。string内のcomment記号は文字列のまま保持。duplicate key、非finite number、UTF-8、object rootの検査も維持する。
  - エラーはCSV-NEXT-CONFIG-001 / source_controlへ閉じ、入力内容は例外messageに出さず、path identityだけを持つ。新しい依存、filesystem read、CLI、config解決、membership意味論は追加しない。
  - 不採用: commentを空文字列に消す実装（token連結で解釈が変わる）、closing delimiter前なら無条件にcommaを消す実装（invalid inputを空値として受理する）、新しいJSONC grammarを憶測で拡張する案。
  - Human decision: 不要。current-v1のfail-closed要件を実装するための局所修正で、利用者向け意味や対象範囲を変更しない。

## Reflection

- durable な結論を Requirement / Design / Plan または accepted ADR に再記述する。
  - Current-v1は既にduplicate-key rejecting JSONCとmalformed control rejectionを定めているため、canonical文書は変更しない。
  - `2d1cba6`でparser sliceの固定SHAゲートを通過し、ST-1/ST-2を解消した。これはfrozen-byte JSONC decoderだけの受入れであり、次はIssue Planのsource-seal工程へ進む。parser sliceまたはIssue #8全体を完了扱いにはしない。
