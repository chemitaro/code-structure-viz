---
種別: interview
ID: "20260824t025616z-interview"
タイトル: "CodeStructureViz Specification Interview"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-08-24"
親: ["init-00001"]
template: "interview"
authority: "evidence"
derived_from: []
reflected_to: []
---

# 20260824t025616z-interview CodeStructureViz Specification Interview

明示的な質問と回答を記録します。回答そのものは自動で採用されません。

## Question

- 目的:
  - CodeStructureVizのInitiative、1 Epic、vertical Issue slice、および各Requirement / Design / Planを外部の高深度分析で作り直す前に、製品境界、比較意味論、domain model、安全性、出力契約を明確にする。
- 資料と現行実装から明確であり再質問しなかった事項:
  - 製品名はCodeStructureViz。
  - 図はcode reviewの入口であり、codeとtest確認の代替ではない。
  - snapshotとtemporal diffは別use case。
  - Git evidenceのFileChangeSetとdomain由来のSemanticChangeSetを分離する。
  - 静的解析を基本とし、対象application codeを実行しない。
  - fetch、checkout、reset、stash、cleanを自動実行しない。
  - 読取・解析不能を削除と誤認せずfail closedにする。
  - SQLAlchemyのForeign Keyとrelationship()、Next.jsの静的JSX render relationとruntime treeを同一視しない。
- ユーザー判断を求めた主な論点:
  - Initiative完了範囲、vertical slice、dual-snapshotの採否、comparison endpoint、既存toolとの境界、出力、利用者。
  - working tree整合性、implicit base、unmerged、rename/copy、provenance。
  - Python、SQLAlchemy、Next.jsのsemantic identity、member粒度、依存探索。
  - artifact、diagnostic、設定、platform、第三者library、安全な情報露出。
  - product featureとしてのHTML reportと、仕様説明ArtifactとしてのHTMLの区別。

## Answer

- 回答者:
  - ユーザー
- Product outcome:
  - Python class、SQLAlchemy ER、Next.js / React componentの3domainを一つのInitiativeに含める。
  - PythonとSQLAlchemyの完了を中間release milestone、Next.js完了をInitiative完了とする。
  - Issueはcontract、SourceView、parser、rendererなどの技術層ではなく、CLI入力からsemantic JSON / PlantUMLまで受け入れ可能なvertical sliceにする。
  - 最終的な正式仕様は1 Epic配下へsliceする。
- Architecture and ownership:
  - CodeStructureVizは既存pyclassuml、tree-git-diffへ依存せず、独立して再構築する。
  - 既存codeのcopyまたは再構成は許可するが、移植後の実装はCodeStructureVizが所有する。
  - 既存toolはreference implementationとして残し、CodeStructureViz完成後に役割を終える。旧CLI互換性は保証しない。
  - 共通化は最小contractに留め、domain固有のidentity、member、relation、matchingは各adapterが所有する。
- Snapshot and semantic diff:
  - diffの正本はbefore / afterそれぞれのimmutable semantic snapshotを比較するdual-snapshot方式。
  - Git hunkはcandidate selectionとsource provenanceのevidenceであり、semantic changeの真実源にしない。
  - memberまたはrelationにsemantic deltaがあればclass / table / componentを変更seedとする。空白、comment、import順だけの変更はseedにしない。
  - 変更seedからupstreamとdownstreamを区別して探索し、default depthは各1。探索graphはbeforeとafterのunionを使用し、削除entityのrelationはbefore graphから保持する。
  - diff図は変更seedと指定depth内のcontextへ限定し、repository全体図はsnapshotの責務とする。
- Comparison endpoint:
  - positional revision countではなくnamed --from / --toを使う。
  - 指定なしはimplicit baseからworking tree、--fromのみは指定refからworking tree、--toのみは終点から解決したimplicit baseから指定to、両方指定時はexact from-to。
  - --to headは開始時にresolveしたHEAD commit、--to working-treeはfreezeしたworking tree。--from working-treeは初期scope外。
  - implicit baseは明示PR target、configured comparison target / upstream、origin/HEAD、local main/develop/master候補の順でmerge-baseを解決する。解決不能時はfail closedとし、initial commit fallbackと自動fetchを行わない。
  - working tree sourceを外部tempへfreezeし、開始・終了fingerprintが異なる場合は正常artifactを残さない。
  - unmerged Uが存在する場合、file evidenceは表示できるがsemantic diffは失敗する。
  - Git R/Cはevidenceに留め、semantic movedは各adapterが高確信の一対一対応を確認した場合だけ採用する。曖昧ならremoved + added。
- Domain model:
  - Python snapshotは未指定時repository全体、指定時path / module / classを起点に指定depthまで探索する。module、class、nested class、field、method、property、inheritance、composition、type/import dependency、decoratorを扱う。
  - Python classの基本identityはmodule pathとqualified class name。移動は一対一、名前またはrename evidence、構造fingerprint、候補一意性を満たす場合だけ判定する。
  - SQLAlchemyはapplication importやDB接続をせず、ORM declarative model sourceを静的解析する。schema / table、column、型、nullable、default、PK、FK、unique、index、check、inheritance、association table、relationship()を扱う。
  - ER diffはtable全体に加え、column / constraint / index / relationshipのmember row単位でadded / removed / modified / movedを表示する。削除rowはghost rowとして残し、before / after値を確認できる。
  - Next.jsはTypeScript / TSX、App Router / Pages Router、module、exported component、props、static import、literal dynamic import、JSX render relation、use clientとserver/client boundary、tsconfig/jsconfig aliasを扱う。runtime treeや非literal dynamic behaviorを推測しない。
  - Pythonではclassとfield / method、SQLAlchemyではtableとrow、Next.jsではcomponentとprop / import / relationの単位でsemantic coloringとimpact traversalを行う。
- Output and agent workflow:
  - 主な利用者はCodexなどのcoding agent。agent自身の理解と、人間向け説明資料作成の両方に使う。人間によるlocal CLI利用も保証する。
  - snapshot / diffはversioned semantic JSONとdomain別PlantUMLを生成し、formatを選択できる。未指定時はJSONとPlantUMLを生成する。
  - domain未指定のdiffは全adapterを実行する。対象不在はnot_applicable、対象があるが解析不能ならincomplete。
  - partial domain failureでは成功artifactを保持しつつ全体をincomplete、exit 3とする。completeは0、fatal analysisは1、usage/configは2、interruptは130。
  - artifact生成では--output-dirを必須とし、対象repositoryへdefault directoryを作らず、既存fileを上書きしない。
  - provenanceにはrequested / resolved endpoint、base resolution、working tree fingerprint、tool / contract / adapter version、domain、coverage、diagnostic、artifact pathとSHA-256を必須記録する。
  - source本文、comment、literal、secretらしい値、絶対pathはartifactへ含めない。相対path、symbol、型、signature、relation、line rangeは含める。SQL default literalはredactする。
  - 変更表示はadded=緑/+、removed=赤・破線/−、modified=黄/~、moved=青/→、unknown=灰/?とし、色だけに依存しない。
- Configuration, limits, platform:
  - 設定優先順位はCLI、.code-structure-viz.toml、built-in default。--configで別pathを指定でき、unknown keyや型不正はhard error。resolved configをmanifestへ記録する。
  - implicit diffのchanged path上限は1,000、1図のentity上限は500、default traversal depthはupstream / downstream各1。超過時は切り捨てず失敗し、明示optionで拡張可能にする。
  - macOS / Linux、Git 2.39以上、Python 3.12以上を初期対応とする。Next.js adapter利用時のみNode.js 22 LTS以上を要求する。Windows nativeは初期scope外。
  - Python coreとrepository内で所有するTypeScript / Node Next.js analyzerをversioned JSONで接続する。
  - pinned version、license確認、lockfile、offline runtime、optional dependency分離を満たす一般PyPI/npm libraryの利用を許可する。
- HTML:
  - product featureとしてのHTML report生成は今回のRequirement / Design / Planと実装scopeから除外し、具体化しない。
  - 後続の仕様作成deliverableとして、Epicと全Issueの内容を単独で理解できる日本語説明HTML Artifactは別物として必要である。これはproduct runtime featureではなくspecification evidenceである。

## Reflection

- Authority:
  - 本Artifactはinterview evidenceであり、回答は自動的にcanonical authorityにならない。
- Canonical reflection:
  - hard-to-reverseでtrade-offを伴う判断は個別ADRへ反映する。
  - Initiative / 1 Epic / vertical Issue sliceのRequirement / Design / Planは、現行draftをtemplate状態へ戻したclean upstreamを基点にChatGPT GPT-5.6 Proで新規作成する。
  - ChatGPTには本Artifact、accepted ADR、現行実装の必要source、SpecDock authoring rules、説明HTML templateを渡し、複数MarkdownとEpic / 全Issueの日本語HTMLを一つのZIPとして返すよう依頼する。
- Issue granularity:
  - contract-only、SourceView-only、parser-onlyなどのhorizontal Issueを作らない。
  - Python、SQLAlchemy、Next.jsのsnapshot / diffとcross-domain agent analysisを、独立して受け入れ可能な最小vertical outcomeへsliceする。
  - 具体的なIssue数と境界は本回答を制約としてGPT-5.6 Proに再評価させ、以前の7 Issue案はauthorityとして引き継がない。
- Explicitly out of scope:
  - product featureとしてのHTML report、DB接続、Alembic統合、runtime component tree、Windows native、public plugin ABI、旧CLI互換性、既存toolへのruntime dependency。
