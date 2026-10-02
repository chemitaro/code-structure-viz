# SI-03 root-origin witness current evidence packet

## Binding / lineage

- Collection time: 2026-10-02T07:03:21Z (UTC、分析用packet準備時のclock観測。review terminalは06:56:39.864Z)。
- Repository: chemitaro/code-structure-viz
- Branch: iss-00008-generate-nextjs-component-snapshots
- Current candidate / reviewed SHA: d3cce1cb42b3c6a00d7a8d8d2b9ee4dbed2406d1
- Original unit base / merge-base: ce0edaa8fe63e79523fe7ad1dcb4b0a39dc02dce
- Fixed accepted scope: Current Plan SI-03 source/proof reference seam。全Issue、full A02/A03、SI-04 Core/productionは今回の認定範囲ではありません。
- Review source: ChatGPT Code Review Strict、一shotのfresh independent conversation。
- Reviewer Oracle session: issue8-si03-source-inventory-review
- Reviewer conversation: 6abf52c7-c150-83e8-8923-5b4661b7bf16
- Reviewer promptSubmitted=true、submittedPromptHash=20ec572a6c94fc386d512483410487f434d3c5a6952beed402e2095d0eff7f80。
- Source reviewer Oracle thinking argument: extra-high。直接実行argv・保存meta browser.config.thinkingTime・native thinking-picker evidenceで確認、推測ではありません。
- Requested/resolved reviewer model: GPT-5.6 Sol、model/thinkingの両picker verified=true。Oracle0.21.3、12m35s。元exec87543 terminal exit10、JSON契約checker再検証もexit10です。
- Review Artifact WB identity: reviews/si03-source-inventory-result.json
- Raw review SHA256: 9cd4663002277d8ad2bcfb8f3427550ec16d4da24f62b8803946a77511dc6670
- Complete log WB identity: reviews/si03-source-inventory-oracle.log
- Analyst identity: issue8-si03-source-owner-cause-adjudication
- Continuity: first analysis、fresh analyst conversation。reviewer/brief author/以前の仕様決定analystとは別系統です。新candidateのみの変更ではなく、SI-03実装owner-causeの分析objectiveとして初回です。

## Accepted objective / parent policy / authorization

- Human explicitly adopted source-inventory/safe-subset separation and owner-closed Option A, and authorized implementation completion after canonical specification and Strict Spec Review. SI-01/02 passed on bcae954; SI-03 commenced on ce0edaa.
- In-scope production contract here means the three new test-only reference/validation/test files. Same retained complete SourceAcquisitionSeal/assets/request-v2/transport candidate, adapter0.2.0, acquisition/private/public source joins and exact partition/count/fingerprint.
- Full mandatory root/edge derivation, least-fixed-point taint, full selection/target/export/source locality, actual budget terminal routing and Core/public certification remain SI-04; actual TS/OS/CLI/package remain later.
- Parent gate: source Code Review P0/P1 blocks this SI-03 candidate; valid review_status=pass is required. P2/P3 are record-only and do not authorize autonomous edits, backlog or re-review. A material coverage gap can block without inventing a severity.
- Source closure policy: specialized chatgpt-code-review-strict requires a fresh one-shot conversation for every review, including corrections. Keep original ce0edaa range and same scope, independently review current code; do not follow up old reviewer or attach its answer to the re-review. Generic same-reviewer headings in analyst output must be interpreted under this exact parent fresh-session policy.
- Parent implementation authorization: uniquely determined P0/P1 corrections inside the accepted SI-03 contract, TDD, local verification, explicit-path commit-codex and normal push are authorized by the approved Plan and ongoing user task. Analysis itself is read-only and supplies no new authorization.
- Human decision required for material Requirement/Design/source-of-truth/ownership/API/security/data/compatibility/recovery/risk changes. Do not reinterpret Option A as a general source/proof waiver or as adoption of new ASSET failure policy.
- No subagents/reviewer agents. Primary invokes external analysis directly. No Browser Use/Computer Use solely to monitor; original jobs finish with quiet sparse original-session waiting.
- Existing complete source inventory, original record taint, full Module owner cardinality, closed wire/enums, source budgets, KAT/ID meanings, prior v1/v2 and Python/SQLAlchemy bytes must remain unchanged.
- New ASSET policy is still unadopted and unrelated. No work on source-reader failure classification, runtime/Node version, package, dependencies, public diagnostics/stderr or publishing is authorized by this finding.

## Governing exact repository authorities

- Current Issue R/D/P: spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00008-generate-nextjs-component-snapshots/requirement.md, design.md, plan.md。
- Accepted ADRs in that Issue artifacts/: 20261002t001435z-adr-issue8-source-inventory-safe-subset.md and 20261002t041350z-adr-issue8-owner-closed-file-module-publication.md。
- docs/contracts/next-semantic-admission-v3.md, next-semantic-v3.md, next-compatibility-v3.md。
- Human Option A and Current SI supersede only the old all-File public correspondence/Project public membership parts; old runtime/semantic baseline meanings and old certificates are preserved.
- SI-REQ-002 requires exact File partition and justified owner-closed exclusion; SI-REQ-003 preserves full inventory proof/taint, mandatory File seed, and public references/cardinality.
- Plan SI-03 specifically rejects invented/missing owner causes; full mandatory proof/locality/Core gate is deferred to SI-04. The stage boundary is not authority for arbitrary File/Module omission.
- Repository-root AGENTS.md is not tracked at this exact SHA. User supplied global AGENTS.md applies to parent operations; it requires preserving unrelated work, inspect/stage explicit paths, commit-codex, and no routine pause. It is not a reviewer role override.

## Complete raw current review

The following JSON bytes are the source-native response, unchanged in meaning and field values. Finding source ID is SI03-CR1-F1; source-native priority is P1 (integer1), not a new local classification.

```json
{"findings":[{"title":"[P1] seed外のroot edgeで別Moduleを失敗扱いできる","body":"2つのprogram Module A/Bがある入力で、`failure_roots`の`module_relation` rootを`record_ids=[A]`としたまま`causal_edges`へそのrootからBへの`identity_dependency` edgeを追加し、Bのdiscovery taintを`module_relation`、Bを`excluded/tainted`、そのowner Fileを`excluded/failed`にすると、このループはedgeのtargetがD内で`_causal_edge_is_allowed()`を満たすことしか確認せずBへroot kindを伝播するため、A由来のrootをBのowner causeとして借用したseamを受理します。Current SI-03は偽owner原因の拒否を出口条件とし、owner-closed A案はuntainted Fileの`excluded/failed`をowner Moduleの検証済みfailure/root/taintへ結合するため、この経路では任意のprogram File/Moduleを非公開にできます。SI-04のmandatory edge完全性を先取りする必要はありませんが、少なくともSI-03でowner causeとして利用するroot-origin witnessはそのrootのdeclared seedへ結合し、direct File failureについてはrootからFileへの直接seed edgeを要求する必要があります。","confidence_score":0.99,"priority":1,"code_location":{"repository_relative_path":"tests/contracts/next_source_inventory_v3_validation.py","line_range":{"start":323,"end":327}}}],"overall_correctness":"patch is incorrect","overall_explanation":"GitHub connectorで`chemitaro/code-structure-viz`の`iss-00008-generate-nextjs-component-snapshots`を直接確認し、branch tip `d3cce1cb42b3c6a00d7a8d8d2b9ee4dbed2406d1`がexpected SHAと完全一致すること、`ce0edaa8fe63e79523fe7ad1dcb4b0a39dc02dce..d3cce1cb42b3c6a00d7a8d8d2b9ee4dbed2406d1`が1 commitでmerge-baseも`ce0edaa8fe63e79523fe7ad1dcb4b0a39dc02dce`であることを確認しました。repository rootの`AGENTS.md`はexact refで404となり、root listingでも不在でした。変更された三つのSI-03 reference/testファイルとCurrent Requirement/Design/Plan、accepted ADR、admission/public/compatibility-v3、既存owner/request/source/causal helperを照合しました。full mandatory seed/causal completeness、least-fixed-point taint、source locality、target/export、budget routingをSI-04へ残すstage境界自体は維持されていますが、SI-03が明示的に保証すべき偽owner原因拒否を回避できるP1が1件あります。repository内Report/Artifactには309 tests、Ruff、mypy等のlocal passが記録されていますが、この外部レビューではtestsを独自実行していません。P1が存在する場合はreview gateをfailとする基準に従います。attachments-bundle","review_status":"fail","review_status_reason":"SI-03のmandatory exitであるowner-causeの正当な結合を破るP1があり、無関係なfailure rootから別Moduleへの許容edgeを追加するだけでowner Fileを`excluded/failed`へ落とせるため、このverified change rangeはstep gateを通過できません。","overall_confidence_score":0.98}
```

The source review reports exact connector SHA/range verification and reads all three new code files, Current R/D/P, ADR/contracts, relevant retained-owner/source/causal helpers. It explicitly does not run local tests. It reports one P1, no other current finding or separately declared coverage gap. Its excluded SI-04/actual runtime surfaces must remain explicit rather than being counted as reviewed.

## Local candidate / validation evidence

- d3cce1c contains one coherent 8-path checkpoint, parentce0edaa, 2808 insertions/4 deletions. Clean attached current worktree, configured upstream/live explicit GitHub ref equal full d3cce1c after normal push.
- Required changed-unit six-module regression before checkpoint: session51138 terminal exit0, 309 passed211.70s; includes all72 new SI-03 cases and relevant v2 semantic candidate/request/exchange/trusted/schema tests, with actual10000/+1 cases not excluded. Tested final code/docs tree was staged and committed unchanged as d3cce1c; this is tree-aligned evidence, not a claim that tests were rerun after commit.
- Separate old Python/SQLAlchemy goldens16 plus Current pointer1: session80307 terminal exit0,17 passed9.94s.
- Ruff check pass, Ruff format230 files pass, mypy188 sources pass, SpecDock sync/validate10 nodes pass, additional Artifact8 local links pass, staged whitespace pass.
- Persisted exact evidence: Issue artifacts/20261002t062856z-disc-si03-source-inventory-reference-seam.md and Report at d3cce1c.
- Historical first final regression46998 was1failed/308passed191.11s; a multiple-disposition fixture hit canonical duplicate rejection earlier than its expected guard. Distinct-reason fixture correction focused71218 passed5/67deselected2.73s, then full same309 selection passed. That test expectation issue is closed and not a current test failure.
- Old lost handle59244 has unknown exit; never counted as pass. No relevant local test or review producer remains running.

## Focused current claim probe (parent evidence collection, not analyst execution)

- Candidate code is clean exact d3cce1c, with only ignored Workbench probe input/log.
- Probe path: .workbench/luna-max-implement/issue8-nextjs-snapshots/evidence/si03-root-seed-probe.py
- Original diagnostic runner32522 terminal exit0; uses real SourceAcquisitionSeal/assets/request and same test-only semantic fixtures; no product code, canonical docs or tracked tests edited.
- Command: uv run --locked --group dev python -c 'import runpy; runpy.run_path(".workbench/luna-max-implement/issue8-nextjs-snapshots/evidence/si03-root-seed-probe.py", run_name="__main__")'
- Control input is the existing unrelated-root negative: two Module taints/owner File exclusions, root seed only the first Module, root edge only to first Module. B is rejected.
- Bypass changes only one causal root-origin edge: same root → second Module, identity_dependency. Its declared root record_ids still contains exactly the first Module. The factory and independent revalidation accept the seam and exclude both owner Files.
- Output (exact local log):
```jsonl
{"admitted": false, "detail": "owner cause requires matching retained failure roots", "extra_root_edge": false}
{"admitted": true, "excluded_owner_files": 2, "extra_root_edge": true, "independent_revalidation": "passed", "module_paths": ["src/other.tsx", "src/page.tsx"], "root_seed_count": 1}
```
- Static traced path: tests/contracts/next_source_inventory_v3_validation.py::source_owner_witness_kinds_v3 checks roots uniqueness/seed references, then _causal_edge_is_allowed and propagates root kind on all allowed submitted edges. Existing tests/contracts/next_reference_validation.py::_causal_edge_is_allowed checks root rule kinds but does not join root-origin edge target to root.record_ids. Full mandatory proof previously owned that separate obligation. New SI-03 uses this helper standalone.
- Existing source File negative drops its only edge. It does not test an alternate path through a same-path Module back to the File. This adjacent recommendation is not locally reproduced yet; analyze against exact code and canonical proposition, preserve uncertainty rather than pretending an observed failure.
- First probe invocation used python -m with a filesystem path and failed mechanically; corrected runner then produced the above complete evidence. Neither this runner error nor the probe counts as a new TDD Red/Green.

## Repair history / implications / result requested

- No response edit after this review. Do not treat reviewer recommendation as accepted design or mutation authority.
- The source seam introduced a bounded witness graph, explicitly not full proof certification. It reused the closed causal helper only; old whole validator and old assets/fixtures are unchanged.
- Evaluate the entire root-origin/witness obligation and adjacent direct File seed path as one current evidence batch; identify whether accepted authority already determines a bounded repair or whether meaning must change.
- Preserved scope/non-goals: no reverse Module→File taint invention, no added state/code/enum/schema/public field, no early partial-safe or production/Core certification, no child metadata/boolean authority.
- If clarification is not uniquely determined or expands full proof responsibility/API/data/compatibility, return the exact decision boundary. A more complex helper/dual gate is not implicitly authorized.
- Apply the attached semantic core and return the role-defined decision packet. The parent owns persistence, tests, implementation, Git, fresh review and closure.
