# SI-03 root-origin / direct File witness current evidence packet

## Exact current binding and continuity

- Collection time: 2026-10-02T07:52:46Z, parent clock observation before final evidence assembly.
- Repository: chemitaro/code-structure-viz; remote HTTPS https://github.com/chemitaro/code-structure-viz.git.
- Branch: iss-00008-generate-nextjs-component-snapshots.
- Current full candidate SHA: cd0e876410d494655b4a880543337274b9ffe948.
- Current tree: c0f03d49b8287e7a2e1da26ae56896ca10cd0d3a.
- Parent and source-reviewed SHA: d3cce1cb42b3c6a00d7a8d8d2b9ee4dbed2406d1.
- Original SI-03 unit base / cumulative unit range start: ce0edaa8fe63e79523fe7ad1dcb4b0a39dc02dce, unchanged.
- Local HEAD, configured upstream and live explicit refs/heads/iss-00008-generate-nextjs-component-snapshots matched exact current full SHA after normal push. Working tree remained clean throughout post-commit checks.
- Source review: ChatGPT Code Review Strict, fresh one-shot separate reviewer; session issue8-si03-source-inventory-review; conversation6abf52c7-c150-83e8-8923-5b4661b7bf16.
- Source review terminal87543 exit10/12m35s; unchanged raw JSON SHA2569cd4663002277d8ad2bcfb8f3427550ec16d4da24f62b8803946a77511dc6670. Independent JSON-contract validation exit10 as expected for valid fail.
- Source reviewer's exact Oracle thinking argument: extra-high, directly evidenced by captured argv, saved meta browser.config.thinkingTime and native picker evidence; model GPT-5.6 Sol and Extra High both picker verified=true. This is not inferred from latency or quality.
- Source review reported one P1 (SI03-CR1-F1), no P0/P2/P3 or separately declared material gap; local parent identified the related CG-SI03-001 and EC-SI03-001 in the original complete batch.
- Stable analysis identity: issue8-si03-source-owner-cause-adjudication.
- Invocation continuity: same-objective exact recorded analyst follow-up to issue8-si03-owner-cause-analysis, conversation6abf57a0-d838-83ee-b8ef-1c963f134acc. The objective, accepted scope and governing authority meaning are unchanged; only current candidate and completed evidence advanced.
- Initial analyst76123 terminal0/9m26s, raw431-line11-H1 result SHA256f9eb8199947ac376f22a8895acdb12ef5a2b82333c95e9a6b18bb29325e21d8e; first call requested GPT-5.6 Sol/Pro and both native pickers verified=true.
- Analyst caller lineage: analyses/si03-root-witness-lineage.json. Current follow-up explicitly requests gpt-5.6-sol / pro again; inherited browser config is not fresh model-picker verification.
- All review producers and required local validation lanes are terminal before this call. No current test lane or Oracle job is still running.

## Accepted objective, scope, parent policy, authority

- Human adopted acquired inventory vs safe subset separation, then owner-closed Option A; canonical docs were updated and independent Spec Review passed at bcae954. SI-03 began at ce0edaa.
- Scope: Current Plan SI-03 source/proof reference seam in tests/contracts/next_source_inventory_v3_reference.py, next_source_inventory_v3_validation.py, test_next_source_inventory_v3.py. Same complete real SourceAcquisitionSeal, retained .2.0 assets, request-v2 and transport candidate; source discovery/full-base Module owner, exact File partition/Project views/count/fingerprint/local witness joins.
- This is not full mandatory seeds/edges exact completeness, least-fixed-point taint, full target/export/selection/source locality, budget terminal routing, Core/public certification. Those remain SI-04. Production TypeScript/OS/CLI/package are later.
- Current Requirement SI-REQ-001..007 and Design SI; Current Plan SI-03 exit specifically includes source portions of P01/P02/P04/P05/P06/P07 and N01..13/N15, rejects invented/missing owner causes, and forbids recognizing seam green as full Core/root/locality pass.
- Accepted ADR artifacts/20261002t001435z-adr-issue8-source-inventory-safe-subset.md; supplemented by artifacts/20261002t041350z-adr-issue8-owner-closed-file-module-publication.md. Both accepted; older decision candidates and old v1/v2 correspondence are historical for the superseded propositions only.
- Contract authorities: docs/contracts/next-semantic-admission-v3.md, next-semantic-v3.md, next-compatibility-v3.md. Existing wire v2/v1 shapes, original ID/trusted/Unicode/taint/root-rule meanings stay baseline, not old certificate reuse.
- Authority precedence: non-waivable constraints; explicit human decision; Current requirements; accepted Design/ADRs/contracts; Plan/test plan; code/tests/fixtures as behavior evidence; reviewer recommendation. Artifacts and analyst outputs are non-canonical evidence, not new design or permission.
- Parent blocking: valid source P0/P1 blocks SI-03. Material gap can block without fabricated P severity. P2/P3 are record-only, no autonomous improvement/backlog/re-review.
- Review closure policy: specialized Code Review Strict always fresh independent one-shot conversation for each repair, original ce0edaa range retained. Do not follow up the original reviewer or attach its review to the new reviewer; do not confuse this with exact same-identity analyst continuity.
- Parent authorizes uniquely determined, meaning-preserving in-scope P1 corrections, TDD, verification, explicit-path commit-codex and normal push. Analysis supplies no new authorization. Material changes to requirement/design/source-of-truth/ownership/responsibility/API/security/data/compatibility/recovery/risk/operation must return to a human.
- No subagents/reviewer agents. No UI solely for monitoring; quiet sparse waits on original sessions.
- ASSET policy remains a separate unadopted decision; do not merge it into this route.
- Repository root AGENTS.md does not exist at this candidate; parent follows human-supplied global AGENTS instructions. R/D/P is under spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00008-generate-nextjs-component-snapshots/.

## Complete source-native review result

Classification remains P1/priority1 for SI03-CR1-F1; reviewer recommendation is advisory evidence only.

```json
{"findings":[{"title":"[P1] seed外のroot edgeで別Moduleを失敗扱いできる","body":"2つのprogram Module A/Bがある入力で、`failure_roots`の`module_relation` rootを`record_ids=[A]`としたまま`causal_edges`へそのrootからBへの`identity_dependency` edgeを追加し、Bのdiscovery taintを`module_relation`、Bを`excluded/tainted`、そのowner Fileを`excluded/failed`にすると、このループはedgeのtargetがD内で`_causal_edge_is_allowed()`を満たすことしか確認せずBへroot kindを伝播するため、A由来のrootをBのowner causeとして借用したseamを受理します。Current SI-03は偽owner原因の拒否を出口条件とし、owner-closed A案はuntainted Fileの`excluded/failed`をowner Moduleの検証済みfailure/root/taintへ結合するため、この経路では任意のprogram File/Moduleを非公開にできます。SI-04のmandatory edge完全性を先取りする必要はありませんが、少なくともSI-03でowner causeとして利用するroot-origin witnessはそのrootのdeclared seedへ結合し、direct File failureについてはrootからFileへの直接seed edgeを要求する必要があります。","confidence_score":0.99,"priority":1,"code_location":{"repository_relative_path":"tests/contracts/next_source_inventory_v3_validation.py","line_range":{"start":323,"end":327}}}],"overall_correctness":"patch is incorrect","overall_explanation":"GitHub connectorで`chemitaro/code-structure-viz`の`iss-00008-generate-nextjs-component-snapshots`を直接確認し、branch tip `d3cce1cb42b3c6a00d7a8d8d2b9ee4dbed2406d1`がexpected SHAと完全一致すること、`ce0edaa8fe63e79523fe7ad1dcb4b0a39dc02dce..d3cce1cb42b3c6a00d7a8d8d2b9ee4dbed2406d1`が1 commitでmerge-baseも`ce0edaa8fe63e79523fe7ad1dcb4b0a39dc02dce`であることを確認しました。repository rootの`AGENTS.md`はexact refで404となり、root listingでも不在でした。変更された三つのSI-03 reference/testファイルとCurrent Requirement/Design/Plan、accepted ADR、admission/public/compatibility-v3、既存owner/request/source/causal helperを照合しました。full mandatory seed/causal completeness、least-fixed-point taint、source locality、target/export、budget routingをSI-04へ残すstage境界自体は維持されていますが、SI-03が明示的に保証すべき偽owner原因拒否を回避できるP1が1件あります。repository内Report/Artifactには309 tests、Ruff、mypy等のlocal passが記録されていますが、この外部レビューではtestsを独自実行していません。P1が存在する場合はreview gateをfailとする基準に従います。attachments-bundle","review_status":"fail","review_status_reason":"SI-03のmandatory exitであるowner-causeの正当な結合を破るP1があり、無関係なfailure rootから別Moduleへの許容edgeを追加するだけでowner Fileを`excluded/failed`へ落とせるため、このverified change rangeはstep gateを通過できません。","overall_confidence_score":0.98}
```

Source reviewer verified d3cce1c and ce0edaa..d3cce1c, reviewed all three new reference/test files plus Current R/D/P/ADRs/contracts and retained owner/source/causal helpers, did not independently execute tests. SI-04/full runtime were explicitly excluded, not silently covered. This historical fail is not a review of current cd0e876, and parent has not declared it closed.

## Prior analyst dispositions and repair

- RC-SI03-001 includes SI03-CR1-F1 (source-native P1), CG-SI03-001 (direct File bypass initially unverified material gap; no invented severity), EC-SI03-001 (old implementation Artifact overclaimed unrelated-root rejection).
- Initial primary route implementation-remediation: edge-shape legality is not root-origin declared seed authority. Existing SI-03 authority uniquely permits a local first-hop membership guard; no requirement or design meaning change.
- Initial handoff authorized only the local root-origin guard, exact Red/Green, positive controls, direct File focused falsification and required regression/docs checks.
- Direct File edge rule was conditional: reproduce and trace current authority first; do not silently import full SI-04 mandatory proof or shared helper change. If a unique local source witness obligation cannot be established, return the decision, not code.
- Implemented current delta: source_owner_witness_kinds_v3 adds five lines before adjacency; source_id recognized as failure root and target outside that root.record_ids raises bounded model_proof rejection. Existing closed rule/kind/path helper and downstream graph unchanged.
- Existing unrelated independent Module negative expanded to three nonFile root kinds × extra root-origin edge presence. Genuine First Red75664:3 failed/3 passed/71 deselected3.49s; extra-edge cases DID NOT RAISE, control rejects. Green4219:6 passed/71 deselected3.64s.
- No producer shape, source reader, shared v1 helper, schema/enum, ID/hash/preimage, runtime/Node/dependencies, public API, persistent/data/security/compatibility/operational meaning change.
- Checkpoint cd0e876 has11 in-scope paths,709 insertions/5 deletions; direct commit-codex5729 terminal0 and normal push79657 terminal0. Message generator's ordinary Spark→Luna fallback did not change implementer/analyst/reviewer settings.
- EC-SI03-001 reconciled by new artifacts/20261002t072235z-disc-si03-root-origin-adjudication-and-remediation.md plus Plan/Report: old062856z claim explicitly superseded, old evidence and initial fail preserved, no retroactive rewriting of canonical meaning.
- Raw original analyst bytes preserved in20261002t074150z--si03-root-witness-original.md.gz; decompressed bytes match raw SHAf9eb8199... exactly. Readable MD20261002t072234z--si03-root-witness-result.md removes only six trailing-space lines; separate read-view SHAffd349cada17a19dd47056c72c9163c82933e50369d2796c6af80761513c9d78. Source review raw JSON unchanged.

## Current direct File falsification — exact cd0e876

- Original working-tree probe38928 (after guard) was repeated on clean current cd0e876 as72619 terminal0. Exact runner:
uv run --locked --group dev python -c 'import runpy; runpy.run_path(".workbench/luna-max-implement/issue8-nextjs-snapshots/evidence/si03-root-seed-probe.py", run_name="__main__")'
- Ignored current output: evidence/si03-cd0e876-probe-output.txt. Same probe code is tracked at artifacts/20261002t072234z-02--si03-root-seed-probe.py. Four outputs match prior checkpoint output20261002t073514z--si03-root-seed-probe-output.txt.
- Uses real same-run source acquisition/request/assets with synthetic semantic proof fixture; does not execute actual TS parser or prove actual Core/public/process/read error. This is exact reference boundary falsification only.
- First control: two Module taints/owner File exclusions, root declared only A, edge only to A; unrelated B is rejected.
- Second control: same root→B extra edge outside declared seed; new membership guard rejects.
- For each parse_file/read_file, File F and same-path Module M both private/tainted, File failed by that kind, M excluded/tainted. Root collection=files, path_ref=F.path, record_ids=sorted([F,M]), no seed missing. Canonical edges are root→M/file_all_records and M→F/file_all_records. There is NO root→F edge.
- Factory retain_source_inventory_seam_v3 and independent validate_source_inventory_seam_v3 both admit this File as failed despite absence of direct root→File witness. This is measured admission, not accepted positive or invented new P classification.

```jsonl
{"admitted": false, "detail": "owner cause requires matching retained failure roots", "extra_root_edge": false}
{"admitted": false, "detail": "owner cause root-origin edge must target its declared seed", "extra_root_edge": true}
{"actual_file_disposition": "failed", "admitted": true, "declared_file_seed": true, "direct_file_bypass": "parse_file", "direct_root_file_edge": false, "independent_revalidation": "passed"}
{"actual_file_disposition": "failed", "admitted": true, "declared_file_seed": true, "direct_file_bypass": "read_file", "direct_root_file_edge": false, "independent_revalidation": "passed"}
```

## Verified trace and disputed obligation

- next_source_inventory_v3_validation.py::derive_source_projection_v3 direct-roots loop joins root collection/kind/path, acquired File membership in root.record_ids and typed File taint. It then uses source_owner_witness_kinds_v3 reachability (root kinds folded per target) for File/Module witnesses.
- source_owner_witness_kinds_v3 now joins each root-origin edge to that exact root's declared seed. It still propagates kinds on submitted edges permitted by _causal_edge_is_allowed.
- next_reference_validation.py::_causal_edge_is_allowed (14086+) treats a same-path Module→File file_all_records edge as shape/rule allowed; this lower-level helper is not independent mandatory-edge derivation and was not changed.
- _record_edge_rule (14176+) was fully inspected: component/relation/type/boundary/value-import/identity rules; no derived Module→File file_all_records rule. Module.references includes its Project, not owner File, so the identity rule does not produce Module→File either.
- derive_required_causal_edges (1437x+) derives required_seed_ids, checks exact declared seeds, then for EVERY root seed independently generates root→seed with TAINT_ROOT_RULES[root.kind]. Thus a mandatory File seed is directly witnessed by its root in the full baseline algorithm.
- Existing test_direct_file_failure_keeps_its_source_seed_edge_and_typed_taint rejects dropping seed, sole File edge or File taint but not the alternate root→M→F path. Current normal direct parse/read and Module-cause positive tests remain green.
- Current SI-REQ-003 preserves File mandatory seed and original root/causal/taint. Design SI and admission-v3 explicitly preserve original causal meanings/no new Module→File reverse taint; File direct failure disposition joins validated parse/read root.
- Plan SI-03 explicitly rejects source portion of seed/causal/taint omission and invented owner causes, but full mandatory edge completeness remains SI-04. The parent does not equate partial local witness checks with a full proof certificate.
- Current open question is the smallest existing proposition needed to close CG-SI03-001: whether this source File's root-local seed witness is already uniquely determined for SI-03 (without full seed/edge set derivation, kind-only laundering, shared helper or changed source-of-truth); or whether current authority actually requires a responsibility decision. Establish it independently, not by treating reviewer recommendation as authority.
- Analyze the whole group and adjacent same-kind/multiple-root/source-path controls; do not declare group closure based solely on the repaired nonseed first-hop example.

## Complete current required local evidence — all terminal

Tests below were run AFTER commit/push on clean exact cd0e876; earlier pre-commit results are separate tree-aligned history.

| Lane | Command / result / runner |
| --- | --- |
| Source and adjacent six-module | uv run --locked --group dev pytest -q --tb=short tests/contracts/test_next_source_inventory_v3.py tests/contracts/test_next_semantic_candidate_v2.py tests/contracts/test_next_request_frame_v2.py tests/contracts/test_next_exchange_v2.py tests/contracts/test_next_trusted_environment_v2.py tests/contracts/test_json_schemas.py —35922 terminal0,314 passed211.05s, no large cases excluded, source seam77 cases |
| Old-domain / Current pointer | uv run --locked --group dev pytest -q --tb=short tests/contracts/test_python_goldens.py tests/contracts/test_sqlalchemy_goldens.py tests/contracts/test_next_contracts.py::test_round23_rg_18_current_schema_and_history_contract_are_explicit —52154 terminal0,17 passed7.55s |
| Static | uv run --locked --group dev ruff check . pass; ruff format --check .230 already formatted; mypy src tests188 sources pass |
| SpecDock | sync --no-github --no-update-active pass, validate10 nodes; no tracked generator changes |
| Evidence / formatting | final staged check passed after readable-view normalization, raw gzip decode hash matches original; new disc7 local links pass; git diff --check HEAD pass after commit |
| Identity | branch unchanged, parentd3cce1c, clean; HEAD/configured upstream/live explicit full SHA equality cd0e876 |

- Required full A02/all contracts/all pytest/pinned PlantUML, SI-04 and actual TS/OS/CLI/offline package remain later and unperformed for this partial unit, not pass claims.
- No current required local failure; new measured File bypass is semantic evidence within this batch, not an infrastructure or test-availability failure.
- Historical unknown/lost59244 is never counted pass. Prior one fixture expectation regression46998 was corrected without weakened guard, followed by genuine green; not a current item.
- Positive KAT/count/Project views and old domains remain validated in these current selections, not assumed from old certificates.

## Parent consequence requested

Apply the attached shared semantic core to every current group item and supplied evidence. Return the trusted11-H1 packet, preserving source-native P1 and unclassified gap. Determine route/authority/authorization for CG-SI03-001 after its current reproduction and trace. A uniquely constrained bounded correction may receive a handoff; a real material meaning/responsibility change must receive the exact human decision boundary. No canonical rewording, shared lower-layer mutation, full proof transfer, new enum/API or scope expansion is implied. Primary owns all persistence/edits/tests/Git/fresh review and closure; no SI-04 advance or Issue completion yet.
