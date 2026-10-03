# SI-04 full Core — exact fixed-candidate local verification

Repository `chemitaro/code-structure-viz`; branch `iss-00008-generate-nextjs-component-snapshots`.
Candidate `d6bbbcf337ee4008d5925a6294a9065ca167a0e2`, tree `4fb7265be5831d8bf109ebf21eab5d0038603ea3`, parent `58864bf0223e35c6cf31ca09b0d9040954e3d9cc`.
Original unit base remains `caf38329826ae34f8e3cb330b83b97e0357b7dc5`.

All processes below began after checkpoint commit d6bbbcf and printed the same full HEAD at start and end. All jobs are terminal, exit0. No tracked source/document changes occurred during these checks. Each selection is separate and may overlap; do not sum counts.

| Check / original session | Result | Captured log SHA-256 |
| --- | --- | --- |
| Full new Core /61078 | 107 passed, 296.86s; actual 10000/10001 and entity500/501 included, no exclusions | `8eef1ccdb739993152764d56a7afd7418eb4b81917a640f13c10a00ad2ba2c8d` |
| Old five modules /9527 | 278 passed, 410.97s; no large-case exclusions | `79c1b07e641b7327b623fb48e61d417bb7750b7f7242024bc1adf2fde0f824cc` |
| Shared sixteen selectors /1500 | 52 passed /637 deselected, 55.21s | `2cdc15a32f1d3895da474e387b6f194b2150bdaa6bf712c25d258380f49838f2` |
| Schema / Python+SQLAlchemy goldens /27582 | 139 passed, 15.06s | `c0fbe1d623d94fa0f746dd88b4b08966dc97770bb85cad2bed91294738c2682c` |
| Global Ruff check/format/mypy | All checks passed /233 files already formatted /191 source files no issues | `b5da91f2557b9439a42b022ba416a988565aba20edd1cd0c2b50fd5a7ee0ef3f` |
| Local SpecDock/pointer/diff /65854 | sync no-GitHub/no-active-update; validate10nodes; pointer1 passed /688 deselected,0.21s; current and committed diff-check pass | `db48e67d1d5fdac756a12b965d8f0b77c3ebcb00e72a2911faabf258f1bbfc37` |

Log names under this directory: `si04-locality-fixed-{core,old,shared,goldens,statics,docs}.log`.

## Exact commands

```text
uv run --locked --group dev pytest tests/contracts/test_next_semantic_core_v3.py -q
uv run --locked --group dev pytest -q --tb=short tests/contracts/test_next_source_inventory_v3.py tests/contracts/test_next_semantic_candidate_v2.py tests/contracts/test_next_core_failure_v2.py tests/contracts/test_next_request_frame_v2.py tests/contracts/test_next_exchange_v2.py
uv run --locked --group dev pytest tests/contracts/test_next_contracts.py -q -k 'export_resolution_witness_uses_complete_source_census_and_coverage_only_rows or export_scanner_closes_unicode_bom_crlf_comments_and_reexport_forms or reexport_graph_recomputes_alias_star_cycle_and_conflict_witnesses or main_reexport_witness_comes_from_raw_declarations_and_edges or round13_reexport_join_is_bijective_for_aliases_and_repeated_forms or actual_string_export_disposition_reaches_every_public_surface or actual_string_export_rejects_coordinated_proof_mutations or string_export_scanner_keeps_raw_span_and_decoded_name_digest or target_failure_validates_complete_proof_before_typed_routing or entity_and_record_budgets_use_distinct_non_allocating_counters or schema_valid_model_record_limit_is_reachable_on_generated_wire or entity_budget_gate_preserves_partial_safe_and_overrun_is_unavailable or props_ir_limits_and_canonical_rules_are_reference_enforced or round21_source_graph_scanner_closes_supported_import_planes_and_open_edges or round20_source_graph_is_derived_from_frozen_bytes_not_reader_injection or round23_rg_18_current_schema_and_history_contract_are_explicit'
uv run --locked --group dev pytest -q --tb=short tests/contracts/test_python_goldens.py tests/contracts/test_sqlalchemy_goldens.py tests/contracts/test_json_schemas.py
uv run --locked --group dev ruff check .
uv run --locked --group dev ruff format --check .
uv run --locked --group dev mypy src tests
python3 spec-dock/scripts/spec-dock sync --no-github --no-update-active
python3 spec-dock/scripts/spec-dock validate
uv run --locked --group dev pytest tests/contracts/test_next_contracts.py -q -k round23_rg_18_current_schema_and_history_contract_are_explicit
git diff --check
git show --format= --check HEAD
```

Each log additionally captures `git rev-parse HEAD` before and after its command group; `set -e` preserves failure exit rather than replacing it with the final SHA check.

## Limits and next gate

These are primary-agent local executions, not tests executed by ChatGPT. They do not certify all-contract/full pytest, whole A02/A03, actual TypeScript/OS/CLI/publication/package, Final or the Issue. Fresh independent cumulative Code Review Strict from unchanged caf3832 to this candidate is still required before SI-04 certification or SI-05 implementation.
Prior reviewer or analyst replies are not included in this supplementary test record and are not new acceptance criteria.
