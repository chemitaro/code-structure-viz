---
種別: disc
ID: "20261002t072235z-disc"
タイトル: "SI-03 root-origin P1指摘分析と限定修復"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-10-02"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: []
reflected_to: []
---

# 20261002t072235z-disc SI-03 root-origin P1指摘分析と限定修復

SI-03の初回独立Code Reviewと専用指摘分析を保存し、既存仕様から一意なroot-origin修復だけを実施した途中checkpointです。SI-03の認定、隣接File迂回のclosure、SI-04移行を宣言しません。

## Inputs

- 対象は同じSI-03 source/proof seam、元base `ce0edaa8fe63e79523fe7ad1dcb4b0a39dc02dce`。初回reviewed SHAは`d3cce1cb42b3c6a00d7a8d8d2b9ee4dbed2406d1`です。
- [初回review原JSON](20261002t072233z--si03-source-inventory-result.json): schema-valid fail/P1一件、`SI03-CR1-F1`。SHA256 `9cd4663002277d8ad2bcfb8f3427550ec16d4da24f62b8803946a77511dc6670`、12m35s、元87543 exit10。Oracle `issue8-si03-source-inventory-review`、conversation `6abf52c7-c150-83e8-8923-5b4661b7bf16`、GPT-5.6 Sol/Extra Highの両picker verified=true。testsの外部実行はありません。
- [分析input packet](20261002t072234z-01--si03-root-witness-packet.md)はraw review、全required local evidence、authority/範囲/親policyとexact d3cceの局所再現を保持します。
- [専用Strict分析の可読view](20261002t072234z--si03-root-witness-result.md): 431行/11必須H1、9m26s、元76123 exit0。Oracle `issue8-si03-owner-cause-analysis`、別conversation `6abf57a0-d838-83ee-b8ef-1c963f134acc`、GPT-5.6 Sol/Proの両picker verified=true。analysis identityは`issue8-si03-source-owner-cause-adjudication`です。viewはwhitespace gateのため六行の行末spacesだけを除去し、SHA256は`ffd349cada17a19dd47056c72c9163c82933e50369d2796c6af80761513c9d78`です。[原bytesのgzip](20261002t074150z--si03-root-witness-original.md.gz)を別にopaque importし、展開後にWorkbench原回答とbyte-for-byte一致、raw SHA256 `f9eb8199947ac376f22a8895acdb12ef5a2b82333c95e9a6b18bb29325e21d8e`を確認しました。source-native意味は変更していません。
- [probeコード](20261002t072234z-02--si03-root-seed-probe.py)と[root-origin修復後の四case output](20261002t073514z--si03-root-seed-probe-output.txt)を別evidenceとして保持。原d3cceでの二case outputは分析input packetへそのまま保存済みで、修復後のoutputとは区別します。outputはGitの`*.log`除外へ入らない`.txt`としてopaque importし、元Workbench logとの`cmp`完全一致を確認しました。

## Synthesis

### 判定と限定修復

source-native P1は妥当で、fault layerはSI-03 implementation、groupは`RC-SI03-001`、routeは`implementation-remediation`です。下位helperはedgeのrule/kind/pathを検査しますが、root-origin targetのdeclared seed membershipは別義務でした。root seedがAだけでも`root→B`を加えると、元d3cceのfactory/独立再検証ともBのowner Fileを非公開にできました。既存のedge無しnegativeだけでは検出できませんでした。

`source_owner_witness_kinds_v3`へ、root-origin edgeのtargetがそのrootの`record_ids`外ならadjacency登録前に拒否する5行の局所guardを追加しました。既存closed edge helper、downstream rules、全root/taint固定点の責任分配は変えません。shared v1 helper、source owner、schema、profile/version、ID/hash/preimage、public API、元taint、File/Module cardinality、予算、既存reason、旧bytesは不変です。

first Redは既存独立Module negativeを三nonFile root kindsとextra root edge有無へparameterizeした同じpublic入口で、`extra_root_edge=True`の三caseがDID NOT RAISE、三controlはpass（元75664、3 failed/3 passed/71 deselected、3.49s、exit1）。5行修復後に同じselectionは6 passed/71 deselected（元4219、3.64s、exit0）。旧正規Module root→declared seedのpositive casesは回帰へ残します。新しい逆taintやseed拡張で通していません。

### 隣接File経路は未閉鎖

分析の`CG-SI03-001`にはseverityを追加しません。source Fileをdeclared seedへ残し、同path Moduleもseedとし、`root→Module→File`だけで`root→File`が無いinputをfocused probeしました。修復後working treeではparse/readともfactory/独立validatorが受理し、Fileをfailedにしました（元38928 exit0）。これは現挙動の測定で、accepted behaviorやCore認定ではありません。

専用分析は、direct File edgeの追加規則を再現/既存authority照合無しで実装しない条件を置いています。現時点ではroot-origin membershipの修復に留め、File迂回の局所義務とSI-04 full mandatory proof境界を同じanalystへ再照合します。旧`_derive_required_root_seed_ids`とmandatory causal builderはFileをroot-origin seed/edgeへ直接結び、`_record_edge_rule`はModule→Fileを導出しません。このtraceを閉じたdataとして渡し、shared helperや仕様を変更しません。

### Evidence reconciliation

旧[SI-03最初の実装証拠](20261002t062856z-disc-si03-source-inventory-reference-seam.md)の「無関係root原因の借用を拒否」は当時の限定testに基づく過大な一般化でした。本Artifactとexact再現でその一般的closure主張をsupersedeします。旧Artifact/初回fail/309 passを黙って書き換えず、当時の証拠として保持します。canonical Requirement/Designの意味変更はありません。

root-origin修復後のaggregate六module selectionは元72776 terminal exit0、314 passed / 213.43sです。実10000/10001等のlarge casesを除外せず、SI-03の77 casesと該当旧reference/schemaを実行しました。旧Python/SQLAlchemy16 goldens＋Current pointer1の別selectionは元63922 terminal exit0、17 passed / 7.32sです。Ruff check/format230 files、mypy188 sourcesは修復後pass。件数はselection間で合算しません。文書チェック、commit/pushとsame-identity followupは別に記録します。tree-alignedなcommit前のtestsと、exact SHAでのpost-commit確認を混同しません。

checkpoint文書のdirect checksはSpecDock `sync --no-github --no-update-active`（既存active維持）、`validate`10 nodes、local link存在確認です。raw review/input packet/probeコード/四case outputは各Workbench原本と`cmp`完全一致。分析原bytesは上記gzipで保持し、可読viewの差分が行末spacesだけであることを独立比較しました。stage後のwhitespace検査がこの六行を発見したため、そのままpassとは記録せず、原bytesを保持したうえで可読viewだけを整形し再検査します。Gitへの取り込みと、clean/pushed exact SHAでの新しい分析は親workflowの後続作業です。

## Options and trade-offs

妥当P1のdeclared-seed guardは、承認済みPlan内の一意な修復として自律実行しました。severityを修正命令に読み替えていません。File迂回を、full mandatory proofのSI-03前倒し、shared helper変更、reverse taint、新field/enum/APIで処理する選択は採択していません。新ASSET policyは別の未採択判断です。

## Reflection

Plan/Reportの現在地は「初回Strict fail、限定P1修復local green、File隣接経路の判定とfresh re-review未完了」へ整合します。元ce0edaaから全修復を含めるfresh Code Review Strictのvalid passまでSI-03を閉じません。analystのsame-objective followupは記録済みanalyst sessionだけを使い、Code Reviewのfresh一shot規則と区別します。全A02/累積A03/production/Issueは未完了のままです。
