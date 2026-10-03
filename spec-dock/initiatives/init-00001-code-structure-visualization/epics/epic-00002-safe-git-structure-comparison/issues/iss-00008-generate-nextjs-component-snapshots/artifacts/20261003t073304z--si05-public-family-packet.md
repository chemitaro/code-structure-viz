# SI-05 complete review-finding evidence packet

## Stable identity and complete-batch boundary

- Analysis identity: `issue8-si05-public-exact-ref-review-adjudication`; no candidate SHA is part of this identity.
- Initial fresh analyst invocation, separate from reviewer/author/implementation/other analysts. No trusted SI-05 analyst session exists yet.
- Objective: determine the validity, fault layer, blocking consequence and smallest authorized response for the completed SI-05 public/exact-ref review evidence batch; not to change requirements or implement advice.
- Repository `chemitaro/code-structure-viz`, branch `iss-00008-generate-nextjs-component-snapshots`.
- Current/reviewed/broad-tested candidate: `6d52ff7949d64e747235eef870631cd8cc29b273`.
- Original fixed point/merge-base: `2efb54c370ac05ac4da0d9b0bfe717a13b62380c`; 1 commit, 38 changed paths. Do not move the original base.
- Collection time: 2026-10-03T06:49:54Z. All review and required local lanes are terminal; no in-flight producer or test lane.
- Current branch clean, local HEAD/configured upstream/live explicit GitHub branch ref equal the candidate. Strict analyst must independently verify this through its GitHub connector before using repository facts.

## Source review provenance and preserved classification

- Source review objective: SI-05 public/exact-ref reference/schema closure, full original-base-to-current range, not production or whole Issue.
- Original exec39905 terminal exit10 with original schema-valid six-field JSON (local official contract checker also returns valid fail).
- Native reviewer session `issue8-si05-public-family-review`, conversation `6ac09f9a-3ef8-83e8-90fc-822af6fee582`; fresh independent reviewer, not author.
- Reviewer Oracle native model `gpt-5.6-sol`, exact requested thinking value `extra-high`, explicit browser/select/attachments-always. Captured invocation and native meta/log directly evidence these inputs.
- Model UI: requested/resolved GPT-5.6 Sol, already-selected, verified=true at 06:24:25.008Z. Thinking UI: Extra High, switched, verified=true at 06:24:25.305Z. No backend identity attestation claimed.
- promptSubmitted=true; submittedPromptHash `9e8a272cd870195dac8fa740d500752e3ad8788ceca9621caaf527638087845f`; native completedAt06:46:52.435Z, elapsed1349982ms.
- Raw review artifact `reviews/si05-public-family.result.json` SHA-256 `f3d84d9db3a10865a2738ec0d2e723e6fe26556ab8fa6419337e6d0af74ee420`, unchanged bytes below.
- Original Oracle log SHA-256 `2b5864740463b8935da78fac2f992bbd279190d6cf153b5fd6cb0b9b263cc2f2`.
- Stable source finding ID `SI05-CR1-F1` maps only to original findings[0]. Native classification P1/priority1, native review_status=fail; these source values are not rewritten regardless of analysis disposition.
- No other current finding or test failure. Reviewer claims full 38-path/ten-schema/owner/lower/legacy inspection and no other blocker; it did not run tests. The validity of that claimed coverage is evidence, not independent attestation.
- Reported trigger: missing `$id` in run-manifest-v2, supposedly because its first object members go directly from `$schema` to title. Reported impact: mandatory family test fails / ten-URN exact closure broken. Reported minimum correction: add the claimed missing ID. Exact source location: schemas/run-manifest-v2.schema.json lines2–3.

## Accepted authority and parent policy

- Human adopted Option A: separate acquired source inventory from safe published subset; program File publication additionally requires independently eligible Module. Current Requirement/Design/Plan and accepted two ADRs govern, historical Round/baseline entries are not fallback authority.
- Issue directory:
`spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00008-generate-nextjs-component-snapshots`.
- Canonical requirement.md, design.md, plan.md Current normative authority / SI sections; report.md is actual evidence, not replacement authority.
- Accepted ADRs: artifacts/20261002t001435z-adr-issue8-source-inventory-safe-subset.md and artifacts/20261002t041350z-adr-issue8-owner-closed-file-module-publication.md.
- Canonical v3 contracts: docs/contracts/next-semantic-admission-v3.md, next-semantic-v3.md, next-compatibility-v3.md.
- Accepted SI-05 output is six public/reference v3 schema siblings plus four closed outer-v2 siblings, exact URNs/recursive refs/consumer census, actual seven-key inventory summary, ten/fourteen-key literals, same-Core JSON/PlantUML, native numeric/owner/privacy controls, old-domain compatibility.
- Every whole new Next certificate has the required new identity; unchanged versionless leaf fragments may be reused. Old v1/v2 schema/KAT/expected bytes remain unchanged.
- Outer four records are schema/ref/shape-only in SI-05; executable diagnostic/stderr/final-owner/copy joins remain SI-06. Reader-prefix and unadopted ASSET policy remain outstanding; actual TypeScript/OS/CLI/package/Final are later gates.
- Parent blocking policy: required exact-candidate local gates and reliable fresh Code Review Strict review_status=pass / P0=P1=0 before SI-06. Current source fail cannot be waived from a local rebuttal or an analyst opinion alone.
- Parent P2/P3 report-only: no automatic fixes, backlog, new criteria or re-review for P2/P3 alone. Prior SI-04 ordinary-open-edge P2 is not an SI-05 implementation driver.
- Material coverage insufficiency may block without a fabricated P severity.
- Parent re-review contract for THIS Code Review skill requires every review, including after corrections or rebuttal, to be fresh one-shot; it forbids reviewer-conversation followups. A source fail therefore requires fresh same-objective cumulative Strict review, not resuming the reviewer conversation. The standard output heading about same-reviewer obligations must be interpreted under this source-specific fresh-review policy, not Final Quality Gate same-conversation policy.
- Parent is authorized to persist evidence, perform scoped read-only falsification, and make uniquely specified in-scope implementation/test corrections with TDD/verification/checkpoint/nonforce push. Reviewer/analyst advice itself grants no edits or new canonical meaning. No subagents, no UI progress monitoring, no new policy, no PR/merge/new branch, no hooks bypass, no alternative index or force push.
- User requested this separate Strict findings analysis using GPT-5.6 Sol / Pro. Selected analyst native value `pro` is explicit user choice, not inferred parity with reviewer latency or prose.

## Fresh falsification evidence at the same unchanged candidate

- Local exact committed blob command:
`git show 6d52ff7949d64e747235eef870631cd8cc29b273:schemas/run-manifest-v2.schema.json | jq -e '.["$id"] == "urn:code-structure-viz:schema:run-manifest-v2"'`
returned true, exit0.
- Exact Git blob ID `0fb9af64bd1908b4a109f77fc205ef6326f753f6`; SHA-256 of the entire committed blob and unchanged working file both `5e1e6ae6ab0e2d66459582941919c89a109990411920d7bdfe560df1b28c783a`.
- Top-level ID is physically at line3754, before the final object brace at3755. It was already present in the reviewed SHA; there is no post-review code correction.
- The first members indeed are $schema then title. The supplied local evidence distinguishes field placement from field absence; independently fetch/read the COMPLETE exact GitHub object including its end rather than accepting this attachment as repository authority.
- Claimed failing test `tests/contracts/test_next_public_family_v3_schemas.py::test_outer_v2_contracts_complete_the_closed_offline_v3_family` actually checks full parsed schema $id at line71, all ten URNs/closed records/resolvable refs/old-whole downgrade, not a property-order position.
- Its `_schema` loader in tests/contracts/test_json_schemas.py lines51–55 is plain UTF-8 json.loads with type cast; it does not inject the ID.
- That exact test was re-run read-only at clean6d52 after review, original command exit0: 1 passed0.33s. This is a focused falsification, not a new TDD Red or entire Linux/production gate.
- Original log `evidence/si05-id-claim-probe.log` SHA-256 `4237eb8d30ab4e25d028ca343d50bfba364b7f76a907b73390b9601a16e46fe1`.
- Broad required results below already include this test. No source/schema/test/dependency/golden or tracked documentation mutation after review. Root cause of the reviewer's conflicting observation (partial retrieval vs mistaken property order vs other mechanism) is NOT observed; don't invent one.

## Complete original review JSON (unchanged)

```json
{
  "findings": [
    {
      "title": "[P1] run-manifest-v2 から schema URN が欠落して family gate が失敗する",
      "body": "Current の exact-ref closure は十個すべての schema に `urn:code-structure-viz:schema:<target>` の `$id` を要求し、今回追加された `test_outer_v2_contracts_complete_the_closed_offline_v3_family` も各 schema について `schema[\"$id\"] == f\"urn:code-structure-viz:schema:{name}\"` を必須確認しています。しかし `run-manifest-v2.schema.json` だけは `$schema` の直後が `title` で `$id` が存在しないため、この verified SHA では FAMILY の `run-manifest-v2` 到達時に当該 gate が失敗し、SI-05 の十-schema URN/exact-ref closure を満たしません。最小訂正は他の九 schema と同様に `$id`: `urn:code-structure-viz:schema:run-manifest-v2` を追加することです。",
      "confidence_score": 0.99,
      "priority": 1,
      "code_location": {
        "repository_relative_path": "schemas/run-manifest-v2.schema.json",
        "line_range": {
          "start": 2,
          "end": 3
        }
      }
    }
  ],
  "overall_correctness": "patch is incorrect",
  "overall_explanation": "GitHub connector で `chemitaro/code-structure-viz` の `iss-00008-generate-nextjs-component-snapshots` tip が expected SHA `6d52ff7949d64e747235eef870631cd8cc29b273` と完全一致すること、固定点・merge-base が `2efb54c370ac05ac4da0d9b0bfe717a13b62380c` であること、および範囲が1 commit・38変更pathであることを確認しました。その範囲について Current Requirement/Design/Plan、二つの採択ADR、十schema、五組のreference/independent validator、新規tests、source/Core lower owners、outer/root/stdout と Python/SQLAlchemy legacy consumer を照合しました。source inventory と safe subset の分離、program File の独立Module eligibility、実count/partition、十key・十四key preimage、same-Core JSON/PlantUML、native-number・foreign-owner・rehashed-cache・privacy controls、whole-Next downgrade拒否については追加の blocker を確認していません。一方、`run-manifest-v2` の `$id` 欠落は変更内のtestとCurrent contractから直接決定できる P1 です。補助添付は同候補について contract 1995 passed、full pytest 3064 passed 等を記録しています attachments-bundle が、verified GitHub SHA 上の schema と同SHA上のtestの静的照合結果と矛盾するため、その実測記録を repository fact より優先して gate を通すことはできません。実際のtestコマンドは本レビューでは実行していません。",
  "review_status": "fail",
  "review_status_reason": "SI-05 の必須 exact-ref/schema family gate を直接破る P1 が1件あります。十schemaの一つである `run-manifest-v2` が契約上必須の schema URN `$id` を持たず、同変更内の明示的なfamily testにも適合しません。",
  "overall_confidence_score": 0.99
}
```

## Complete supplementary actual local evidence

# SI-05 exact candidate local evidence

This is supplementary command/exit/hash evidence, not repository implementation authority, an independent review or an Issue completion certificate. Inspect canonical code/contracts at the connector-verified GitHub SHA.

## Binding and scope

- Repository `chemitaro/code-structure-viz`, branch `iss-00008-generate-nextjs-component-snapshots`.
- Original SI-05 unit base `2efb54c370ac05ac4da0d9b0bfe717a13b62380c` remains fixed.
- Candidate `6d52ff7949d64e747235eef870631cd8cc29b273`, direct parent the original base, 38 owned paths / 13583 insertions / 9 deletions.
- Normal `commit-codex -a` original8125 exit0. Complete staged diff independently read; raw diff SHA-256 `99267faaf73ff1891d1e88916fa0f59fe6e756e52bc5039da70191106da7ffc3`.
- All contract/code checks below ran locally in the calling worktree, not in ChatGPT. Selection counts overlap and are not summed.
- No production source, dependency/lock, old schema/KAT/golden change. Outer domain/publication/root/stdout-v2 vectors test complete closed/ref/shape records; they do not prove an executable final-owner/copy/stderr certificate.

## Original clean candidate broad run

- Original session48020 terminal exit0, serial execution 2026-10-03T04:26:02.460458+00:00 through 06:19:05.648780+00:00.
- Before and after full HEAD exactly `6d52ff7949d64e747235eef870631cd8cc29b273`, same branch, clean status, all tracked/untracked nonignored candidate file SHA-256 maps equal. No tracked edits while in flight.
- Manifest `evidence/si05-broad-gates.json` SHA-256 `8cabeaed5edc9dd4a8903ee53c982acc5be7a9ec4e0836df9e0ea0c4658460c4` stores original argv, timestamps, exits, logs and full candidate hashes.
- Common command prefix `uv run --locked --group dev` except SpecDock.

| Command suffix | Actual result / runner duration | Original log SHA-256 |
| --- | --- | --- |
| `pytest tests/contracts -q --tb=short` | exit0; 1995 passed / 3473.072s | `e61dee09698c0470f6798cd7ca718257ef9d189a5cfb5c66a226f3fc8e3feeb2` |
| `pytest -q` | exit0; 3064 passed, 1 skipped / 3309.434s | `38667554f3c358be66f6d4fa904c26e06b7407f046deb27d96fb907fe96b1500` |
| `ruff check .` | exit0, All checks passed / 0.079s | `82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18` |
| `ruff format --check .` | exit0, 249 files already formatted / 0.030s | `cd83ead2e950d1cadea9ebbf07897f3d4cc11df68a345db6fd25a2994605a54a` |
| `mypy src tests` | exit0, 207 source files / 0.201s | `39a150ed6c86b1432bf68ac3768438f34e090ed8d676bd929dd5d762b6b38178` |
| `python3 spec-dock/scripts/spec-dock validate` | exit0, nodes=10 / 0.252s | `02dc6cc03600cad869b4fc6beaafde5dea95261ef64c26c000f858f67328315b` |

No large-case skip/deselection option was supplied. The existing `tests/integration/source/test_git_repository.py::test_linux_source_view_reads_single_nfd_physical_filename_as_nfc_identity` has a deterministic `sys.platform != "linux"` skip with reason `Linux physical Unicode spelling contract`; current platform is `darwin`. This Linux-specific test is not execution evidence on macOS. The single full-suite skip is consistent with that unchanged guard; actual OS/TypeScript production acceptance remains outside SI-05.

To identify this new full-suite skip observation without re-running the suite, the exact Linux-only test was run separately with the same common prefix and `-q -rs`: original command exit0, `1 skipped in 0.02s`, reason above at unchanged line93. Log `evidence/si05-linux-skip.log` SHA-256 `c4021299b45809a45b9298ab9b5f79764420c165d9e062384cc7099549496c78`. This is an identified platform limitation, not a passed Linux test, and is not added to the full-suite count.

## Completed focused run before checkpoint

- Original serial81335 terminal exit0 with full candidate file hashes/branch/HEAD/status unchanged before/after.
- Comparing the focused after-file map to the broad committed candidate before-file map shows exactly three differences: Plan, Report, and the SI-05 candidate evidence disc were completed with the finished focused results before checkpoint. All implementation/schema/test/literal file hashes match. The focused run itself was pre-commit at base2efb and is not relabeled as a post-commit execution. Broad tests independently validate the complete committed candidate including those documentation updates.
- Seven new family/schema modules: 253 passed829.10s; source/Core-v3: 282 passed466.44s; legacy public/run-v2 six modules: 350 passed1715.89s; Python/SQLAlchemy goldens: 16 passed5.24s; Current pointer: 1 passed0.14s.
- Actual source/Core record10000/10001, entity500/501 and legacy16MiB/+1 cases remain included. Old expected bytes were not updated.
- Exact argv/hash/timing are in tracked `artifacts/20261003t025644z-disc-si05-public-family-candidate.md` and local `evidence/si05-focused-gates.json`.

## Other inspected evidence and limits

- Fixed offline registry resolves all ten new URNs and recursive refs; controlled full siblings preserve old schema identities/bytes. Versionless leaf-fragment reuse is not old whole-Next certificate admission.
- Same-Core JSON/PlantUML, acquired/safe/proof-only partition counts, independent ten/fourteen-key literals, native-number and foreign/rehashed-cache/privacy/downgrade controls are included in the new-family suite.
- Consumer census was classified: new exact refs, unchanged leaf fragments, legacy regression/lower wire, retained baseline/historical docs. Unexpected stale new-lane consumer count0 by inspection; not a future source-reader/finalizer/production completeness claim.
- Current full-range committed diff check passes; production/dependencies/old schema and old thirteen-key literal excluded surfaces have no diff.
- SI-04 certification remains exactd6bbbcf; SI-05 requires its own fresh independent cumulative review. Prior certificates do not certify current changes.
- SI-06 diagnostics/stderr/final-owner, reader-prefix, unadopted ASSET decision, all-A02/A03, actual TypeScript/OS/CLI/package and Final/Issue completion remain outstanding. No subagents or UI progress monitoring used.

## Prior history, unresolved decisions and requested analysis boundary

- Source/Core milestones certified separately (SI-03 exact23072c2, SI-04 exactd6bbbcf); no old certificate grants SI-05 certification. Current bcae954 specification gate remains accepted, with no semantic change in this candidate.
- SI-05 intermediate fixture corrections before checkpoint are documented in tracked candidate disc; original failed logs retained. No hidden semantic fix or prior SI-05 review existed; this is its first fresh cumulative review.
- No required test failure is pending. One unchanged Linux-only test skip is explicitly recorded; no actual Linux/Windows/TypeScript/OS production pass.
- Unadopted ASSET policy remains a later human decision, not a solution to this ID observation.
- Determine claim validity, trigger/impact, first incorrect fault layer and single primary response route using the shared core, preserving SI05-CR1-F1's original P1/fail labels.
- State whether any actual implementation/test/spec change is justified at this exact candidate, what remains required for parent review closure, and which guarantees/authority must remain unchanged.
- If GitHub exact evidence differs from the supplied local entire-blob evidence, preserve the discrepancy and stop for the justified evidence recovery; don't silently resolve it by assuming one source.
