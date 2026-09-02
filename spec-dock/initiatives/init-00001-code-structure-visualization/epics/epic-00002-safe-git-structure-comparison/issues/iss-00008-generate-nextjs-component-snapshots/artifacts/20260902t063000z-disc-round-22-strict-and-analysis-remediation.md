# Issue #8 Round 22 Strict and analysis remediation record

## Evidence identity and boundary

This is the durable remediation record for the pre-implementation contract of Issue #8. It records
repository materialization evidence and does not claim a product implementation, an Issue close, or a
Strict pass.

- Reviewed/base SHA: `e63c5d411cedc40c85f396cccbf12ca141b1938f`
- Remediated candidate SHA: pending commit/publication
- CI: `33586646010`, exact SHA, 7/7 success
- Strict review session: `required-strict-github-connector-verificati-713`
- Strict source output: `/Users/iwasawayuuta/.oracle/sessions/required-strict-github-connector-verificati-713/output.log`
- Strict source output SHA-256: `d3e8c835608a41e02ac8d33080be8cda97c81f18541776b3ab3f6a92deb0ea8d`
- Verification-only session: `issue-eight-strict-round-twenty-4`
- Analysis session: `required-strict-github-connector-verificati-716`
- Analysis output SHA-256: `22da412f210af7ae5783cf207426187e7b0e82fee1815e218c53e52ffbfdafa3`
- Evidence packet: `.workbench/chatgpt/issue-8-round22-review-evidence-packet.md` (SHA-256 `3d4cb41aa803931284f00c8b427683c1fb410407eaee0e81b985839dc45cde88`)
- Analysis decision packet: `.workbench/chatgpt/issue-8-round22-analysis-decision.md` (SHA-256 `31c443512429773536fb46d858df7f43ada5251033a50e352fefb908483a8902`)
- Analysis identity: `issue-8-nextjs-snapshot-remediation-analysis-v1`

The source Strict verdict remains historical and unchanged: `P0=0 / P1=20 / P2=0 /
review_status=fail / implementation_ready=no`. A fresh Strict review of the current SHA is pending;
readiness is unconfirmed; production implementation is absent. Local tests and CI cannot replace the
same-reviewer current-SHA Strict pass.

## Source-native findings and exact root-cause assignment

The 20 source-native findings are retained by ID and title below. Each ID occurs once in the assignment;
the RG labels are remediation organization, not a severity change.

| Finding | Source-native finding | RG |
| --- | --- | --- |
| P1-01 | `dependencies.next` と `devDependencies.next` の同時宣言に対する規則が矛盾 | RG-01 |
| P1-02 | ApplicabilityMatrix が source/config acquisition より後に導出 | RG-01 |
| P1-03 | malformed package/config が `CSV-NEXT-CONFIG-002` に誤分類 | RG-02 |
| P1-04 | `allowJs` の default と source membership への効果が矛盾 | RG-01 |
| P1-05 | local `extends` file の read failure が global control failure として未閉包 | RG-01 |
| P1-06 | SourceFailureLedger の taint traversal 方向が逆で safe subset が過大 | RG-03 |
| P1-07 | module-plane scanner が TSX と template substitution を安全に走査できない | RG-03 |
| P1-08 | `.js/.jsx/.mjs/.cjs` specifier の TypeScript 同stem解決が契約不一致 | RG-03 |
| P1-09 | sealed source graph が edge kind、specifier、open reasonを保持しない | RG-04 |
| P1-10 | product platform scope と process schema の Windows 要求が矛盾 | RG-05 |
| P1-11 | normative process observation が security-critical launch policyを所有しない | RG-06 |
| P1-12 | process observation が正本ではなく legacy descriptorから再構成 | RG-07 |
| P1-13 | `stable_fingerprint` が cross-machine stableでない | RG-08 |
| P1-14 | Node.js 22以上という minimum runtimeが machine-checkableでない | RG-09 |
| P1-15 | provenance が observed booleanだけで観測値へbindされない | RG-10 |
| P1-16 | coverage validatorが test source文字列への自己参照 | RG-11 |
| P1-17 | Applicability public projection schemaが closed/redactedでない | RG-01 |
| P1-18 | source-integrity fatal と payload-unavailable が同じ diagnostic code | RG-12 |
| P1-19 | project root overlapが usage exit 2 と domain unavailable exit 3の双方 | RG-13 |
| P1-20 | selected stdout copy limit超過時の `CSV-NEXT-LIMIT-003` projection未閉包 | RG-14 |

## Adopted decisions

The parent/user authorization for the Round 22 best-practice remediation selected these nine canonical
decisions. They are synchronized across Requirement/Design/Plan, contract docs, schemas, reference
validation, fixtures, and the human HTML.

1. Malformed package applicability is `CSV-NEXT-APPLICABILITY-002` at `applicability`, globally
   `payload_unavailable`, non-recoverable, no ref, and Node-prohibited. `CSV-NEXT-APPLICABILITY-001`
   is reserved for intentional non-applicability. Equal valid direct declarations are applicable.
2. The sealed source graph is a redacted closed `resolved | open` union. Resolved edges carry source,
   target, syntax kind, role, normalized specifier, and specifier identity. Open edges carry a closed
   reason plus a safe frontier or keyed specifier digest; unsafe raw text is not public.
3. v1 production supports only macOS (`darwin`) and Linux (`linux`). Windows is a separate scope and
   is not a v1 production branch.
4. `next-process-launch-observation-v1` is the process authority. It owns private cwd, exact environment
   allowlist/denied set, pipe stdio, inherited FD closure, `shell=false`, process-group terminate/wait,
   verified executable identity, and TOCTOU evidence. A legacy descriptor is derived only.
5. Portable `stable_toolchain_fingerprint` and host `local_process_attestation_digest` are separate.
   Host path, OS primitive, device/inode, and FD are retained only by local attestation, not cross-machine
   stable identity.
6. A parseable stable Node SemVer with major >=22 is allowed. Older, prerelease, or unparsable versions
   are `CSV-NEXT-NODE-001` unavailable; build metadata does not affect ordering.
7. Provenance rows are typed observed `{schema, version, sha256}` identities or `unobserved`/`null`.
   The observed prefix is retained and only the suffix is unobserved; boolean-only authority is invalid.
8. Revision drift, duplicate/post-seal read, seal mismatch, and source substitution are fatal
   `CSV-NEXT-SOURCE-INTEGRITY-001` (exit 1, no semantic or failure manifest), while ordinary
   non-isolatable source failure remains `CSV-NEXT-SOURCE-003` manifest-only/exit 3.
9. Selected stdout-copy overflow retains the semantic result and persisted artifact descriptor, then
   seals one incomplete/exit-3 `CSV-NEXT-LIMIT-003` publication with canonical stderr and no partial
   stdout. It never remeasures, rerenders, or recopies.

## Root-cause group closure and executable evidence

| RG | Scope and materialized closure | Executable evidence |
| --- | --- | --- |
| RG-01 | Matrix-first applicability, config/membership authority, all-non-applicable short circuit, `allowJs`/extends failure, closed applicability projection | `test_round22_applicability_dual_valid_and_malformed_projection`; `test_round22_all_non_applicable_short_circuits_config_and_source_reads`; `test_round22_config_codes_and_jsonc_composition_are_closed`; `test_round22_dynamic_extends_read_failure_is_global_control_failure` |
| RG-02 | Dedicated malformed package diagnostic and provenance/schema branch | `test_round22_applicability_dual_valid_and_malformed_projection`; `test_round20_package_applicability_matrix_rejects_encoding_duplicates_and_mixed_state` |
| RG-03 | Reverse taint, lexical template/JSX scan, runtime suffix handling, explicit open dependency | `test_round22_source_locality_scans_executable_template_jsx_and_runtime_suffixes`; existing source-failure and source-graph tests |
| RG-04 | Redacted resolved/open graph with closed reason and keyed identity; source-plan schema is the owner | `test_round22_source_graph_is_a_redacted_resolved_or_open_union`; runtime source-graph positive/mutation pair |
| RG-05 | macOS/Linux-only v1 platform contract | `test_round22_process_observation_rejects_prerelease_and_windows`; process observation schema |
| RG-06 | Observation-owned security launch fields and no host process claim | `test_round21_process_observation_is_normative_and_fingerprint_excludes_ephemeral_identity`; `test_round18_process_descriptor_requires_os_identity_and_spawn_binding` |
| RG-07 | Legacy process descriptor is compatibility-derived, not a second authority | `test_round22_process_observation_rejects_prerelease_and_windows`; existing descriptor/observation substitution tests |
| RG-08 | Portable/local fingerprint split | `test_round21_process_observation_is_normative_and_fingerprint_excludes_ephemeral_identity` |
| RG-09 | Stable SemVer major policy and prerelease rejection | `test_round22_process_observation_rejects_prerelease_and_windows`; process schema node-version pattern |
| RG-10 | Typed observed value and observed-prefix provenance | `test_round22_provenance_observed_rows_have_typed_identity`; runtime provenance mutation pair |
| RG-11 | Callable producer/validator runtime registry with positive/negative execution | `test_round22_runtime_registry_executes_vectors_and_named_validators` |
| RG-12 | Fatal integrity outcome separated from ordinary unavailable | `test_round22_source_integrity_has_distinct_fatal_diagnostic`; `test_round20_source_integrity_has_one_fatal_vs_payload_unavailable_projection` |
| RG-13 | Root overlap is pre-acquisition CLI usage: exit 2, zero reader/stdout/artifact | `test_round22_project_root_overlap_is_usage_before_source_acquisition`; `test_round22_project_usage_code_is_not_a_domain_failure_pair` |
| RG-14 | Selected-copy overflow is final sealed publication with canonical stderr | `test_round16_final_publication_decision_seals_capture_stderr_and_selected_copy`; runtime selected-copy positive/mutation pair |

The registry in `tests/fixtures/next_contract_vectors.json` contains a positive and negative vector for
each materialized runtime group. Its callable producer and validator names are resolved and executed by
`test_round22_runtime_registry_executes_vectors_and_named_validators`; missing, duplicate, unknown, or
wrong-criterion records are rejected. The fixture criterion map includes `round22.rg-01` through
`round22.rg-14` and is checked against real test definitions.

## First Red / Green evidence

The selected-copy boundary supplied a concrete First Red before the implementation correction:

```text
uv run pytest tests/contracts/test_next_contracts.py::test_round16_final_publication_decision_seals_capture_stderr_and_selected_copy -q --tb=short
FAIL: selected_stderr was b'' but the required canonical LIMIT-003 JSONL was expected
```

After the final publication branch was updated to seal canonical selected-copy failure stderr and avoid
rerender/recopy, the same test passed (`1 passed in 0.49s`). The related publication selection run passed
`5 passed, 227 deselected in 1.26s`. Round 22 focused evidence then passed `12 passed, 332 deselected in
0.12s`, and the fixture criterion-index test passed `1 passed in 0.10s`. These are reference-contract
tests only; no Node process was launched.

## Changed surfaces

- Issue canonical documents: `spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00008-generate-nextjs-component-snapshots/requirement.md`,
  `spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00008-generate-nextjs-component-snapshots/design.md`, and
  `spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00008-generate-nextjs-component-snapshots/plan.md`.
- Human artifact: `spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00008-generate-nextjs-component-snapshots/artifacts/20260831t022707z--nextjs-component-snapshot-best-practice-guide.html`; its existing
  eight PlantUML diagrams remain exactly eight, with Round 22 explanatory text added without a diagram.
- Contract docs (10): `docs/contracts/next-config-v1.md`, `docs/contracts/next-source-plan-v1.md`,
  `docs/contracts/next-process-launch-v1.md`, `docs/contracts/next-limits-v1.md`,
  `docs/contracts/diagnostic-v1.md`, `docs/contracts/stdout-v1.md`,
  `docs/contracts/next-runtime-manifest-v1.md`, `docs/contracts/next-semantic-v1.md`,
  `docs/contracts/next-compatibility-v1.md`, and `docs/contracts/next-plantuml-v1.md`.
- Schemas (6): `schemas/diagnostic-v1.schema.json`, `schemas/next-diagnostic-catalog-v1.json`,
  `schemas/next-process-launch-observation-v1.schema.json`, `schemas/next-process-launch-v1.schema.json`,
  `schemas/next-provenance-v1.schema.json`, and `schemas/next-source-plan-v1.schema.json`.
- Reference contract/tests (3): `tests/contracts/next_reference_validation.py`,
  `tests/contracts/test_json_schemas.py`, and `tests/contracts/test_next_contracts.py`.
- Fixture: `tests/fixtures/next_contract_vectors.json`.
- Durable artifact: this file.

No `src/**` file, dependency, lockfile, product implementation, or live Node process evidence is part of
this remediation.

## Verification record

The following local checks were required. Entries are updated only with measured output from this worktree.

| Command/check | Result |
| --- | --- |
| Round 22 focused Next/schema (parent independent) | `12 passed, 332 deselected in 0.13s` |
| selected-copy First Red | failed as recorded above; corrected and green |
| publication focused subset | `5 passed, 227 deselected in 1.26s` |
| fixture criterion-index focused | `1 passed in 0.10s` |
| Next/schema contract suite (parent independent) | `344 passed in 47.22s` |
| contracts suite (parent independent) | `367 passed in 52.08s` |
| full pytest (parent independent) | `1223 passed, 1 skipped in 179.79s` |
| mypy (137 files) | `Success, 137 source files` |
| ruff check | `All checks passed!` |
| ruff format check | `158 files already formatted` |
| SpecDock validate | `spec-dock: ok (validate) nodes=10` |
| HTML PlantUML validator | `static PASS 8; browser 8/8 inline SVG; zoom operations PASS` |
| `git diff --check` | `exit 0` |
| `git diff --name-only -- src` | `empty` |
| `pyproject.toml` / `uv.lock` diff | `empty` |
| node_modules check | `find . -type d -name node_modules -print` returned empty |

The reviewer and analyst workflows remain separate: Strict is the defect-discovery authority, while the
analysis skill supplied triage, root-cause grouping, authority/route/authorization ordering, and the
remediation packet. Fresh current-SHA Strict remains pending after these local changes.

## Skill comparison and workflow conclusion

The ordinary Strict review had stronger discovery and precise file/symbol evidence, but was flat: about
77.47k input tokens, 63 minutes, and 20 findings. The new analysis skill was shorter (about 16.82k input
tokens and 25 minutes) and stronger at root cause, authority, route, authorization, and verification
planning. The combined workflow is therefore preferred: Strict for review generation, then the analysis
skill for post-review remediation planning. The complete packet cost was 835 lines / 48,562 bytes. The
analyst output called its own session unknown, which was supplemented by wrapper session
`required-strict-github-connector-verificati-716`; generic session slugs make provenance harder to read.
An initial shell quoting error was not sent to ChatGPT and is not treated as a skill defect.

## Re-review gate and remaining risk

The remediation is bounded to data-only pre-implementation surfaces. A same-reviewer Strict review at the
new exact SHA must return `review_status=pass`, `P0=0`, and `P1=0` before implementation readiness can be
considered. The remaining declared risk is the intentionally unperformed OS process-level acceptance and
the absence of production implementation; this record does not claim either was completed. No material
product/policy/security/platform decision remains outside the nine decisions explicitly adopted above.
