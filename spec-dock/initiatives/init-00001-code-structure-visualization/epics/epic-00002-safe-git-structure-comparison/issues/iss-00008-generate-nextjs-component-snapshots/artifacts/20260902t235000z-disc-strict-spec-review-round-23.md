# Issue #8 — Round 23 Strict remediation evidence

## Evidence identity and boundary

- Objective: make Issue #8 implementable without another material requirement, design, public-contract, security, or platform decision; production implementation is explicitly absent.
- Reviewed/base SHA: `1e7b15f8564c17966545b902ea67928b847aa742`.
- CI: GitHub Actions run `33607326214`, reviewed SHA, 7/7 jobs successful.
- Strict review session: `required-strict-github-connector-verificati-725`.
- Strict review `output.log`: `/Users/iwasawayuuta/.oracle/sessions/required-strict-github-connector-verificati-725/output.log`, SHA-256 `ec599426300561d6c4244df0db99971f84b48008e79df786b09415e86f1a08c6`.
- Strict transcript artifact: `/Users/iwasawayuuta/.oracle/sessions/required-strict-github-connector-verificati-725/artifacts/transcript.md`, SHA-256 `6eb255c66e7c0421fdc0c412f8336c0bd73f9467024ec136327842f6aebd672a`.
- Specialized analysis session: `required-strict-github-connector-verificati-733`.
- Analysis packet: `.workbench/chatgpt/issue-8-round23-analysis-decision.log`, SHA-256 `72d776e2394880b508e6f29203639f04cf1826674354b3d49a4053c09c94fbe5`.
- Complete source packet: `.workbench/chatgpt/issue-8-round23-review-evidence-packet.md`, SHA-256 `8733607a1c29456341cc5e13a79e9ae61af6cd3ecd840afe760cb4633a1f7daf`.
- Historical Strict verdict at the fixed point: `P0=0 / P1=26 / P2=8 / fail / implementation_ready=no`.
- Fresh current-SHA Strict review: pending; this artifact never changes the historical verdict.
- Production Next adapter, Node execution, and runtime evidence: absent. The reference lane does not claim OS process-level evidence.

The Strict packet is source-native review evidence. The analysis log is advisory triage/route evidence. Local tests and this artifact are remediation evidence; none of them substitute for a fresh exact-SHA Strict pass.

## Adopted decisions

The parent explicitly adopted these seven decisions under the zero-base best-practice mandate; they are canonical requirements, not candidate text:

1. Provenance is one closed union: request-independent not-applicable, request-independent failure, request-bound failure, and request-bound success. Request-bound failure retains the validated request, limits, source-plan identity, and observed prefix. Each observed value carries its field schema/version and SHA-256 of its actual canonical value; only the unobserved suffix is null.
2. Config keeps the declaring config path for path-valued options. `files` and `include` together are `CONFIG-001`; either present empty array is authoritative; defaults apply only when both are absent. `baseUrl`/`paths` resolve from the declaring config directory, with exact-before-wildcard specificity and declaration-order replacements, through one shared compiler-options schema.
3. The scanner resolves only provable module forms. Value/type roles are retained. Property access, shadowed `require`, unsupported/uncertain syntax become open edges. Public graph data is a safe repository-relative frontier or a source-identity/byte-span opaque occurrence identity, never raw unsafe text or a reversible low-entropy digest; open retained closure prevents `partial_safe` when it is unbounded or ambiguous. External packages and unresolved relatives are distinct.
4. Process policy and process observation are distinct. Policy owns exact argv, adapter identity, private cwd, environment, stdio/FD and process-group rules, timeout and capture limits. Observation is null until an actual launch and is the only measured authority; darwin/linux availability requires the full Node/adapter/argv/cwd/env/stdio/FD/group/TOCTOU proof, otherwise it is unavailable. Legacy descriptors are one-way views.
5. String-named exports use `TARGET-001` only for explicit path target resolution. Independently proven non-component strings are intentional unsupported coverage; possible/uncertain promised component bindings use `EXPORT-001`; no `IdentifierName` is synthesized.
6. Canonical path/JSON-string normalization uses a checked-in Unicode 15.0.0 NFC profile and table digest. Unsupported code points fail closed. A future profile is a versioned compatibility migration with cross-version known-answer tests; this pre-implementation lane does not claim a complete runtime table.
7. `ImportBindingMember` is the closed `named | default | namespace` union. Namespace members carry local name, role, source and `imported_name=null`; `*` is never overloaded as an identifier. Member access remains separate evidence and namespace members share count/order rules.

## Finding → root group → executable closure

Each R23 root group has a positive and mutation vector, a callable producer and validator in `tests/contracts/next_reference_validation.py`, and a substantive reference test. The current registry has 36 R23 records (18 positive, 18 negative) and the fixture evidence map cross-checks registry identity rather than relying on source-string markers.

| Group | Strict findings | Materialized contract and executable evidence |
| --- | --- | --- |
| R23-RG-01 | P1-01, P1-02, P1-03 | `PackageApplicabilityMatrix` projection is first, all-non-applicable has no Node/config/source observation, mixed filtering is preserved, malformed applicability has `CSV-NEXT-APPLICABILITY-002`, and public domain/root/stdout/stderr/exit projections are matrix-owned. `test_round23_rg_01_applicability_is_package_first_and_project_filtered`; `round23-runtime-applicability` / mutation; `validate_r23_applicability_projection`. |
| R23-RG-02 | P1-04, P1-09, P1-24 | Catalog-derived stage/code/outcome/reference rules are represented in the closed provenance and diagnostics contract; ordinary control failures are source-control failures and usage remains distinct. `test_round23_rg_05_provenance_is_four_kind_value_bound_union`; `round23-runtime-provenance` / mutation; `validate_r23_provenance`. |
| R23-RG-03 | P1-05, P1-06 | Four-kind provenance retains the observed prefix and binds each observed row to an actual value digest; request-independent branches do not invent a request. `test_round23_rg_05_provenance_is_four_kind_value_bound_union`; `round23-runtime-provenance` / mutation. |
| R23-RG-04 | P1-07, P1-08 | Project-root-relative hard exclusions and known-control discovery are current source-plan rules; arbitrary nested same-name controls are not authority. `test_round23_rg_02_config_subset_has_one_closed_jsonc_grammar`; source-plan current-v1 contract and required graph. |
| R23-RG-05 | P1-10, P1-11, P1-12 | JSONC BOM/comments/trailing comma composition, one local `./` extends, files/include membership, declaring path, baseUrl/paths ordering, forbidden options and shared compiler schema are executable. `test_round23_rg_02_config_subset_has_one_closed_jsonc_grammar`; `test_round23_rg_16_config_files_and_include_are_explicit_authority`; `round23-runtime-config` / mutation. |
| R23-RG-06 | P1-13 | `next-source-plan-v1` now requires the source graph; the R23 graph validator closes the resolved/open union, source-byte digest and graph digest. `test_round23_rg_04_source_graph_is_frozen_resolved_or_private_open`; `round23-runtime-source-graph` / mutation. |
| R23-RG-07 | P1-14, P1-15, P1-16, P1-17 | Scanner role/certainty, open frontier redaction, unresolved-relative vs external-package discrimination, and occurrence identity are closed. `test_round23_rg_03_source_scanner_preserves_role_and_open_uncertainty`; `test_round23_rg_14_open_frontier_has_safe_public_identity_only`; `round23-runtime-scanner` / mutation and `round23-runtime-frontier` / mutation. |
| R23-RG-08 | P1-18, P1-19 | Policy/observation separation, explicit unobserved/unavailable states, and legacy one-way direction are documented and validator-tested. `test_round23_rg_07_process_policy_observation_separates_portable_and_local_identity`; `round23-runtime-process` / mutation. |
| R23-RG-09 | P1-20, P2-04 | Process policy/observation cross-fields include verified identity, argv, adapter, TOCTOU, FD/group and supported fixture states; the reference test does not claim a host process test. `test_round23_rg_07_process_policy_observation_separates_portable_and_local_identity`; `test_round23_rg_15_process_platform_scope_rejects_windows_and_toctou`; process registry vectors. |
| R23-RG-10 | P1-21, P1-22 | Portable and local process identities are separated, stable Node identity is retained, and verified Node versions require stable SemVer major >=22 (prerelease/unparsable rejected). `test_round23_rg_07_process_policy_observation_separates_portable_and_local_identity`; process mutation vectors. |
| R23-RG-11 | P1-23 | Final publication owns candidate bytes, descriptors, selected copy status, one measurement and publication-only overflow while semantic status is retained. `test_round23_rg_08_publication_owns_exact_bytes_and_selected_overflow`; `round23-runtime-publication` / mutation. |
| R23-RG-12 | P1-25, P2-05, P2-06 | Runtime registry records producer/validator/polarity for every current criterion; fixture evidence map checks bidirectional identity. The R23 tests include a real `.tsx` source path and distinct valid Next declarations in the current contract vectors. `test_round23_rg_12_coverage_index_is_bidirectional_and_substantive`; all 36 registry records execute. |
| R23-RG-13 | P1-26 | Requirement/Design/Plan, current contract docs, and HTML identify one current-v1 authority and mark historical Round sections non-normative; no production implementation is implied. `test_round23_rg_18_current_schema_and_history_contract_are_explicit`; `round23-runtime-authority` / mutation. |
| R23-RG-14 | P2-01 | String export has explicit target, intentional unsupported, and export-failure dispositions without synthesizing an identifier. `test_round23_rg_09_string_export_uses_target_or_export_owner`; string-export registry pair. |
| R23-RG-15 | P2-02 | Unicode 15.0.0/NFC profile and table digest are versioned; a small checked-in KAT witness fails closed for unsupported inputs until the future generated table is added. `test_round23_rg_10_unicode_profile_is_pinned_and_versioned`; unicode registry pair. |
| R23-RG-16 | P2-03 | The canonical validator path is `tests/contracts/next_reference_validation.py`; the current docs and plan point to it. The stale path is not used as evidence. |
| R23-RG-17 | P2-07 | Namespace binding is a discriminated member with null imported name, separated from `*` and member access. `test_round23_rg_11_namespace_import_is_a_closed_binding_member`; namespace registry pair. |
| R23-RG-18 | P2-08 | Future wheel/sdist member golden and exact pyproject delta are a Plan-only migration contract; `pyproject.toml` is intentionally unchanged in this pre-implementation batch. |

## Changed surfaces

The materialized diff is limited to the Issue #8 specification/contract/reference scope:

- Issue R/D/P: `requirement.md`, `design.md`, `plan.md`.
- Human explanation: `artifacts/20260831t022707z--nextjs-component-snapshot-best-practice-guide.html` (the existing eight PlantUML diagrams are retained).
- Contract docs: `docs/contracts/next-source-plan-v1.md`, `next-config-v1.md`, `next-process-launch-v1.md`, `stdout-v1.md`, `diagnostic-v1.md`, `next-semantic-v1.md`, `next-compatibility-v1.md`, `next-limits-v1.md`, `next-runtime-manifest-v1.md`, `next-plantuml-v1.md`, and new `next-provenance-v1.md`.
- Schemas: `schemas/next-round23-authority-v1.schema.json` (new) and `schemas/next-source-plan-v1.schema.json`.
- Reference/tests: `tests/contracts/next_reference_validation.py`, `tests/contracts/test_next_contracts.py`, `tests/contracts/test_json_schemas.py`, and `tests/fixtures/next_contract_vectors.json`.
- This durable artifact.

No `src/**`, `pyproject.toml`, `uv.lock`, dependency, or generated `node_modules` change is part of this remediation.

## Local verification record

The following table is the primary agent's independent post-materialization evidence, superseding
earlier coder-lane timings. Commands were run against the materialized worktree. A green local
gate is not a Strict pass.

| Check | Result |
| --- | --- |
| R23 focused tests (`uv run pytest tests/contracts/test_next_contracts.py tests/contracts/test_json_schemas.py -q --tb=short -k round23`) | 19 passed, 344 deselected in 0.15s |
| `uv run pytest tests/contracts/test_next_contracts.py tests/contracts/test_json_schemas.py -q --tb=short` | 363 passed in 57.60s |
| `uv run pytest tests/contracts -q --tb=short` | 386 passed in 57.27s |
| `uv run pytest -q --tb=short` | 1242 passed, 1 skipped in 195.86s |
| `uv run mypy src tests` | Success, 137 source files |
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 159 files already formatted |
| `python3 ./spec-dock/scripts/spec-dock validate` | spec-dock: ok (validate) nodes=10 |
| Japanese HTML PlantUML/static/browser/zoom validation | First two sandboxed invocations: static 8 passed, Chrome DevTools startup timed out. Escalated GUI invocation: static 8 passed, browser 8/8 inline SVG, all zoom checks passed; VALIDATED. The timeout was environment/sandbox startup behavior, not an HTML defect; no live OS process evidence claimed |
| `git diff --check` | pass (exit 0) |
| `git diff --name-only -- src pyproject.toml uv.lock` | empty |
| `find . -type d -name node_modules -print` | empty |

### First Red / Green record

- First Red authority is the fixed-point Strict review: the pre-remediation candidate was `P0=0 / P1=26 / P2=8 / fail`, with each row preserved in the finding table above. The source packet is the immutable evidence for those failures; this lane does not invent a separate synthetic pre-fix result.
- The local worktree did not retain a separate before-edit command transcript for every finding, so no unobserved per-finding failure count is claimed. Every R23 group has an executable positive and mutation vector; the mutation assertions are the local red conditions that must fail closed.
- Green evidence is the completed table above: focused R23, next/schema, full contracts, full pytest, mypy, ruff, SpecDock, HTML browser/zoom, and diff hygiene all passed. Fresh Strict remains pending.

## Skill/route evaluation

The normal Strict review route was superior for defect discovery and precise file/symbol evidence; its 20-finding flat output was expensive to remediate. The `analyze-review-findings-strict` route was superior for root-cause grouping, authority, route, ordering and authorization, so this batch used both: Strict as defect-discovery authority and the analysis skill as remediation-planning authority. The complete packet cost was 69,260 bytes/800 lines. A same-session follow-up (`required-strict-github-connector-verificati-732`) failed before submission because Chat/Work mode could not be verified; passive diagnostics plus `oracle session ... --harvest --no-recover` recovered the completed conversation, and retry with `--browser-attach-running` succeeded as session 733. The skill failed closed correctly; resume ergonomics, generic session slugs, and an analyst self-report of its external session ID as unknown remain operational concerns.

## Re-review and residual risk

- Fresh Strict at the current candidate SHA is pending and must be run by the primary agent. Historical `P0=0/P1=26/P2=8/fail` remains unchanged.
- Production implementation is absent. In particular, no OS-native Node process was launched by this reference remediation; future process-level acceptance must prove the adopted darwin/linux invariants.
- The checked-in R23 NFC witness is deliberately bounded and fail-closed; it is not runtime proof of a complete Unicode normalization implementation. The future generated profile/table and migration KAT remain a separately planned implementation obligation.
- No unresolved user decision remains within the adopted seven decisions; any new product, public migration, security, or platform choice must stop and return to human adjudication.
