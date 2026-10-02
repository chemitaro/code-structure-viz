# Candidate and completed evidence batch

- Repository: chemitaro/code-structure-viz
- Branch: iss-00008-generate-nextjs-component-snapshots
- Current candidate and reviewed full SHA: a4efdc373a515801777c924a1d14675fda686955
- Evidence collection time: 2026-10-02T01:02:22Z
- Working tree: clean; local HEAD and configured upstream are identical. The Strict wrapper will repeat live upstream verification.
- Review source: chatgpt-spec-review-strict, first fresh independent specification review.
- Exact reviewer Oracle session: issue8-source-inventory-spec-review
- Reviewer exec session: 45005, terminal exit0, duration19m34s.
- Reviewer conversation ID: 6abefcca-0874-83ee-8647-5b0518e3106d
- Native promptSubmitted=true; submitted prompt hash4225682d48dba1630286c229f44551d5279060f98092790315c8235fcc37ce0a.
- Complete unchanged review artifact: .workbench/luna-max-implement/issue8-nextjs-snapshots/specs/source-inventory-review-result.json
- Review SHA256: 2fff0ab48628233db38a58ed86ae279ba8fb3dff95601a1e247d7efc3663676b
- Reviewer exact Oracle thinking input: pro. Provenance: captured invocation --model gpt-5.6-sol --browser-thinking-time pro and caller lineage state. Native model/thinking picker both already-selected/verified=true; Pro strictFailClosed=true. UI evidence, not backend identity attestation.
- The reviewer output has parsed as exactly one JSON object and validates unchanged against the installed specification-review output-schema.json. review_status=fail, one source-native P1, no P2/P3.
- Analyst identity: iss-00008 / source-inventory-v3-specification-finding-adjudication / accepted source separation before implementation
- Invocation: first fresh analyst, separate from reviewer, author, implementation and all earlier analysts. Exact analyst session ID to be supplied by native invocation, not guessed.

# Accepted objective and parent boundary

ユーザーは全取得inventoryと公開safe subsetの分離を採択し、要件・設計・計画を修正・チェックしてから実装再開するよう指示しました。現在はdocs-only仕様checkpointです。意味が不足/矛盾した場合は人間が判断できる具体的な選択肢・最推奨・理由を返します。

- In scope: source/proof/Project view/File partition/count/profile/public/exact-ref仕様の実装可能性、指摘の真偽/到達条件/根本原因/対応方針/認可の分析。
- Excluded: 新ASSET failure policy、early reader prefix partial-safe、File mandatory seedの省略、child自由source metadata、public proof-only参照、production完成認定、サブエージェントreview。
- Accepted risk/non-goal: A trusted user toolchain/static-only scopeは維持。same-UID adversary/RSS隔離等を新保証として追加しない。対象code/config/plugins/scripts/node_modulesを実行/loadしない。
- Parent blocking policy: schema-valid review_status=passが唯一の仕様gate。P0/P1または信頼できないcoverageは実装再開を止める。source-native classificationを変更しない。
- P2/P3 policy: information only、修復/backlog/task/re-review条件へしない。
- Same-reviewer closure: 同じ仕様objectiveの訂正はexact reviewer issue8-source-inventory-spec-reviewへStrict followup。ローカル反証やanalyst助言だけではgateを閉じない。
- Autonomous boundary: 既存authorityから一意に決まる、意味と保証を変えないtask-scoped整合は親workflowが修正・通常commit/push・再reviewできる。canonical meaning/requirement/public data/taint/ownership/compatibility/recovery/riskをmaterialに変える場合は採択済み案への暗黙拡張をせずhuman decisionへ戻す。
- 今回のanalysis route自体はread-only。reviewerのP1は仕様変更命令でも実装認可でもない。

# Repository authority and precedence

Global user AGENTS: live canonical docs/source/testsの現物確認、無関係な契約保持、scope/behavior/data/riskをmaterialに変える未決事項のみ質問、primary agentで分析し外部助言を正本へ照合、Strictのclean/pushed exact SHA。サブエージェント禁止、Oracleはoriginal session/logで静かに待機。

- spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00008-generate-nextjs-component-snapshots/requirement.md: requirements。Current normative authority / SI-REQ-001〜007 / 観測可能な要件が正本。SIは旧File全件model correspondence/Project public membershipだけを明示置換。ID/認識/props/relation意味、A runtime、静的解析、読込ordinary I/O unavailable/actual integrity fatalは維持。
- spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00008-generate-nextjs-component-snapshots/design.md: canonical design。Current AとSI target、authority index、以下三契約へ詳細を委譲。SI says safe Files必ず公開、full causal規則維持、Project taint/除外無し。歴史Round Nは非normative。
- spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00008-generate-nextjs-component-snapshots/plan.md: execution plan。SI-01docs→SI-02spec pass→SI-03source seam→SI-04full proof/Core→SI-05public refs→SI-06diagnostics→全A02→累積A03→production。meaning変更はSI-01へ戻し同じobjectiveを再認証。元base/fixed point維持。
- spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00008-generate-nextjs-component-snapshots/artifacts/20261002t001435z-adr-issue8-source-inventory-safe-subset.md: accepted decision。全取得親所有、full proof、File mandatory seed維持、safe File exact partition、Project二view。Project/File payload/null injection拒否。新ASSET未採択。
- docs/contracts/next-semantic-admission-v3.md: accepted admission target。F_safe=F−T、safe File全件公開、正当full root/seed/causal/taint維持、public program File→Module基礎規則維持、safe public references、同じseal locality/target/export/予算順序。
- docs/contracts/next-semantic-v3.md: accepted public/exact-ref target。source summary七keys、十四key run fingerprint、新Core/public/compatibility/provenance/run/candidates-v3、planned domain/publication/root/stdout-v2 refs。
- docs/contracts/next-compatibility-v3.md: accepted compatibility target。十keypreimage、旧IDs/algorithms/trusted/Unicode/binding意味維持。
- CONTEXT.md: inventory/safe subset/proof-only/partial-safeのglossary only。
- docs/contracts/next-semantic-admission-v2.md and next-semantic-v1/v2.md, tests/contracts/next_reference_validation.py and next_runtime_v2_validation.py: unchanged baseline contract/current behavior evidence for roots/causal/typed target/cardinality/selection. New profile certificate is not an old v2 certificate.
- 作成用ChatGPT回答、旧candidate、過去tests/reviewpassはadvisory/historyでaccepted authorityに昇格しない。

# Complete source-native review result

以下はresponse JSON全体の内容です。原WB file/digestを変更していません。findingはsource index1（このpacket上の識別子SPEC-SI-P1-01）、source priority=1を保持します。reviewerは問題と影響を指摘しており、特定fixは処方していません。

```json
{
  "findings": [
    {
      "title": "[P1] 非File rootでsafe Fileと必須Moduleの投影が分離する",
      "body": "docs/contracts/next-semantic-admission-v3.mdは「Fileのexact partition」でF_safe=F−Tの全件公開を要求し、「Full-inventory proofとlocality」でv1のclosed root/edge・taint固定点を維持しつつ、public Moduleはsafe Fileに対応し公開program Fileには必ずModuleがあるという基礎規則も維持しています。しかし委譲先v1 referenceのmandatory seed／causal derivationでは、module_relation、export_binding、boundary_derivation等の正当な非File rootがModuleをtaintしても、Moduleから所有Fileへの逆向きtaintは導出されません。target無しまたは別のsafe targetでこのrootが生じると、FileはT外なので公開必須、対応ModuleはT内なのでproof-only必須となり、exact partitionとFile→Module基礎規則を同時に満たすnominal candidateが存在しません。Current DesignのSI節も「full proofのcausal規則は維持」「安全Fileは必ず公開」として同じ不整合を固定しており、plan.mdのSI-04が要求する全root／causal受入れを実装・検証できません。",
      "confidence_score": 0.97,
      "priority": 1,
      "artifact_location": {
        "repository_relative_path": "docs/contracts/next-semantic-admission-v3.md",
        "section_or_line": "「Fileのexact partition」「Full-inventory proofとlocality」"
      }
    }
  ],
  "review_scope_summary": "GitHub connectorでchemitaro/code-structure-vizのiss-00008-generate-nextjs-component-snapshots tipがa4efdc373a515801777c924a1d14675fda686955と完全一致することを確認し、そのcommitだけを対象にCONTEXT.md、Current requirement/design/plan、accepted ADR、admission-v3・semantic-v3・compatibility-v3を全体横断で評価しました。解釈に必要な最小baselineとして旧admission/semantic/compatibility契約、関連schema、source-plan/config、現行referenceのroot/causal/model correspondenceだけを照合し、未実装v3 schema/reference/runtimeや未実行testを成立済みとは扱っていません。添付review-methodの全体一巡・反証・漏れ確認の手順を適用しました。 attachments-bundle",
  "review_status": "fail",
  "review_status_reason": "維持対象の正当な非File semantic rootに対し、safe Fileの全件公開とtainted Moduleの非公開、公開program File→Module基礎規則を同時に満たせないP1が1件あるためfailです。その他の取得inventory／公開safe subset、Project二view、source row省略、exact partition、counts/hash/exact-ref migration、pre-seal failure境界、A02→A03順序は確認範囲では整合していました。",
  "overall_confidence_score": 0.96
}
```

# Local tracing and focused falsification

Source claims were checked at the same a4efdc3 commit:

- tests/contracts/next_reference_validation.py:13920 _record_references: File and Module reference Project, Module does not reference its File. Project no reverse membership taint reference.
- :14176 _record_edge_rule: fixed rule selects references and semantic dependency edges; nonFile root does not derive Module→File reverse taint.
- :14232 _derive_required_root_seed_ids and :14375 derive_required_causal_edges / :14440 _derived_taint_fixed_point: path-local module_relation/export_binding/boundary_derivation can taint Modules while File remains outside the closure.
- :14491 validate_model and program File loop around14591: public program File must have exactly one public Module except supplied narrow missing-target exemption.
- :8718 target_completeness_failure: no explicit targets implicitly checks all public program Files. Therefore a no-explicit-target input may be routed to typed target failure; this nuance limits a literal claim that absolutely no typed result exists.
- :8800 _target_missing_module_exceptions: exemption applies only selected missing/component_only target cardinality. With an explicit different safe target, missing unrelated Module is not exempt.
- tests/contracts/next_runtime_v2_validation.py:1308 validate_semantic_candidate_v2 keeps raw target failure/base proof order and narrow target exception. It is old v2, not a new Core-v3 implementation.

Read-only .workbench reproduction nonfile-root-source-projection-check.py:
- Starts with the existing _model() fixture, removes cross-file relations/import-binding and re-derives roles/counts to form an explicitly disjoint data-only graph. Baseline validate_model passes before the taint projection.
- For each module_relation/export_binding/boundary_derivation at src/Card.tsx, derives mandatory seeds, causal edges and typed fixed point with current helpers.
- File Card remains untainted, Module Card tainted; F−T projection therefore retains Card File and excludes Card Module.
- Explicit safe target src/Button.tsx has no target failure and no missing exemptions, but validate_model(public) raises NextTargetCompletenessFailure for src/Card.tsx/missing.
- No explicit target in old helper produces implicit Card/missing failure. Do not misreport this nuance as target-free semantics proof.
- This is record/proof algebra and public-cardinality evidence ONLY; not a nominal new Core, full source seal/transport/export proof, actual frozen TS root generation, source locality, CLI/package acceptance.
- Harness terminal exit0 after three cases. Early scratch failures were a resolved Python import path and mistaken independence in the original linked fixture; no tracked source/test/guard was altered.

```json
{
  "baseline_model_validated": true,
  "mandatory_seeds_causal_fixed_point_checked": true,
  "cases": [
    {
      "root_kind": "module_relation",
      "path": "src/Card.tsx",
      "root_seed_count": 1,
      "file_tainted": false,
      "module_tainted": true,
      "safe_file_retained": true,
      "tainted_module_published": false,
      "explicit_safe_target_failure": null,
      "explicit_safe_target_missing_exemptions": [],
      "public_model_failure": {
        "type": "NextTargetCompletenessFailure",
        "failures": [
          {
            "target_key": "path:src/Card.tsx",
            "reason": "missing"
          }
        ]
      },
      "no_explicit_target_baseline_failure": [
        {
          "target_key": "path:src/Card.tsx",
          "reason": "missing"
        }
      ]
    },
    {
      "root_kind": "export_binding",
      "path": "src/Card.tsx",
      "root_seed_count": 1,
      "file_tainted": false,
      "module_tainted": true,
      "safe_file_retained": true,
      "tainted_module_published": false,
      "explicit_safe_target_failure": null,
      "explicit_safe_target_missing_exemptions": [],
      "public_model_failure": {
        "type": "NextTargetCompletenessFailure",
        "failures": [
          {
            "target_key": "path:src/Card.tsx",
            "reason": "missing"
          }
        ]
      },
      "no_explicit_target_baseline_failure": [
        {
          "target_key": "path:src/Card.tsx",
          "reason": "missing"
        }
      ]
    },
    {
      "root_kind": "boundary_derivation",
      "path": "src/Card.tsx",
      "root_seed_count": 2,
      "file_tainted": false,
      "module_tainted": true,
      "safe_file_retained": true,
      "tainted_module_published": false,
      "explicit_safe_target_failure": null,
      "explicit_safe_target_missing_exemptions": [],
      "public_model_failure": {
        "type": "NextTargetCompletenessFailure",
        "failures": [
          {
            "target_key": "path:src/Card.tsx",
            "reason": "missing"
          }
        ]
      },
      "no_explicit_target_baseline_failure": [
        {
          "target_key": "path:src/Card.tsx",
          "reason": "missing"
        }
      ]
    }
  ],
  "not_proven": [
    "nominal Core-v3",
    "complete proof/source seal/transport",
    "actual frozen TypeScript root generation",
    "source locality",
    "production/public integration"
  ]
}
```

# Completed validation and freshness

- At exact a4efdc3: Current pointer + existing schema meta/closed selection34 passed in0.78s, exit0. Node IDs: tests/contracts/test_next_contracts.py::test_round23_rg_18_current_schema_and_history_contract_are_explicit and tests/contracts/test_json_schemas.py::test_checked_in_schema_is_valid_and_closed.
- At exact a4efdc3: baseline tests test_taint_edges_are_derived_for_boundary_and_shared_frontier and test_program_file_requires_exactly_one_module_for_file_and_directory_targets:2 passed in0.20s, exit0. Separate selection, not summed with34.
- At exact a4efdc3: docs checker7documents/14links, run14/compatibility10/summary7/partition3keys, old source/schema/tests/dependencies unchanged; exit0.
- At exact a4efdc3: SpecDock validate10nodes exit0.
- Precommit equivalent docs semantic tree: Ruff check, format227files, SpecDock sync(no Github/no active update), diff-check pass. No tracked deltas after a4efdc3.
- No pending review/test/validation job remains. Complete current review batch has one finding, no current failing required local gate, and the review itself fails. No other source finding or obligation was silently dropped.
- New schemas/reference/Core-v3, actual TS/OS/CLI/package and whole A02/A03 are explicitly unimplemented/unverified, not missing evidence hidden behind previous748 old tests.
- This is first source-v3 spec finding. No attempted canonical fix or re-review yet.

# Questions for adjudication, not preselected responses

指摘の妥当性・root/trigger/影響と、旧typed target unavailableという安全経路による限定を区別してください。最初の誤りが仕様命題の衝突なのか、既存algorithmを再利用する対象viewの指定不足なのかも、現物から判断してください。

現行保証を全部維持する訂正が一意に存在するか、それともFile metadataとsemantic Moduleの公開対応意味、File安全性の定義、taint規則やunavailable方針のhuman decisionが必要かを判別してください。materialに変えるならCandidate textに留め、選択肢と最推奨/理由/失う保証を具体化してください。独立safe File metadataを残すが対応Moduleはproof-only、Module失敗でowner Fileも非公開、全domain unavailable等は比較仮説でありどれも採択済みではありません。

同じroot causeが非File roots全種、合法selection-only Module exclusion、target無し/明示safe/失敗target、nonprogram File、Project membership、full/private proofとpublic closure、budgets/privacy/refsへ及ぶかもcompletion sweepで確認してください。新severityや新機能を作らず、解消済み仕様論点を新たな義務へ変更しないでください。

# Unresolved independent decisions and non-mutations

ASSET ordinary I/O / installed-package corruption policy remains unadopted; cannot infer approval from source separation. No src/schema/test/dependency/golden edits were made in the spec checkpoint. No File seed/taint/root/old golden bypass is permitted. New producer planned header0.2.0 is already in target docs, not a package release change. Full production workflow remains gated by A03 independently of Spec Review. Primary parent owns artifacts/Git/reviewer followup and any human choice; analyst owns none of those actions.
