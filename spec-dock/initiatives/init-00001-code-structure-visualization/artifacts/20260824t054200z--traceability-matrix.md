# Traceability Matrix

## Traceability rule

- Initiative Requirement は strategic outcome/boundary。
- Epic Requirement は cross-Issue product/architecture contract。
- Issue Requirement は one vertical observable behavior。
- Design ID は structure/interface decision、Plan ID は implementation/verification sequence、AT は executable acceptance evidence。
- shared invariant は各 owning slice に slice-specific test を持たせ、同一 test を無意味に複製しない。

## Initiative → Epic → Issue → acceptance

| Initiative requirement | Epic trace | Owning Issue(s) | Final acceptance evidence |
| --- | --- | --- | --- |
| INIT-REQ-001 | EPIC-REQ-001, EPIC-REQ-003 | ISSUE-01〜07 | INIT-AC-001〜005 |
| INIT-REQ-002 | EPIC-REQ-002, EPIC-REQ-008 | ISSUE-01〜07 shared safety | INIT-AC-006, INIT-AC-008 |
| INIT-REQ-003 | EPIC-REQ-002, EPIC-REQ-003 | ISSUE-02, ISSUE-04, ISSUE-06 | I02/I04/I06 semantic and impact tests |
| INIT-REQ-004 | EPIC-REQ-004 | ISSUE-01〜07 output tests | INIT-AC-001〜005 |
| INIT-REQ-005 | EPIC-REQ-005 | ISSUE-01〜07 failure; ISSUE-07 aggregation | I07-AT-002〜005 |
| INIT-REQ-006 | EPIC-REQ-006 | ISSUE-01〜07 locks; ISSUE-07 final gate | I07-AT-006, I07-AT-007 |
| INIT-REQ-007 | EPIC-REQ-007 | ISSUE-04, ISSUE-07 | INIT-AC-003, INIT-AC-005 |
| INIT-REQ-008 | EPIC-REQ-008 | all Issue out-of-scope sections | INIT-AC-008 |

## Epic acceptance coverage

| Epic acceptance | Issue/test coverage |
| --- | --- |
| EPIC-AC-001 | ISSUE-01 I01-AT-001〜006 |
| EPIC-AC-002 | ISSUE-02 I02-AT-001〜007 |
| EPIC-AC-003 | ISSUE-03 I03-AT-001〜006 + ISSUE-04 I04-AT-001〜006 |
| EPIC-AC-004 | ISSUE-05 I05-AT-001〜006 + ISSUE-06 I06-AT-001〜006 |
| EPIC-AC-005 | ISSUE-07 I07-AT-001〜007 |
| EPIC-AC-006 | この matrix、MANIFEST dependency DAG、Issue R/D/P trace tables |
| EPIC-AC-007 | 全 security/negative/determinism/budget tests + I07 platform/package |
| EPIC-AC-008 | R/D/P scope scan + explanation HTML classification |

## ISSUE-01 Generate Python Structure Snapshots

| Requirement | Design | Plan | Acceptance | Test ID | Planned test file |
| --- | --- | --- | --- | --- | --- |
| I01-REQ-001 | I01-DES-001 | I01-PLAN-001 | I01-AC-001 | I01-AT-001 | tests/acceptance/python/test_snapshot_cli.py |
| I01-REQ-002 | I01-DES-002 | I01-PLAN-002 | I01-AC-002 | I01-AT-002 | tests/integration/python/test_targeted_snapshot.py |
| I01-REQ-003 | I01-DES-003 | I01-PLAN-003 | I01-AC-003 | I01-AT-003 | tests/acceptance/python/test_snapshot_failures.py |
| I01-REQ-004 | I01-DES-004 | I01-PLAN-004 | I01-AC-004 | I01-AT-004 | tests/security/test_python_static_boundary.py |
| I01-REQ-005 | I01-DES-005 | I01-PLAN-005 | I01-AC-005 | I01-AT-005 | tests/acceptance/python/test_snapshot_determinism.py |
| I01-REQ-006 | I01-DES-005 | I01-PLAN-005 | I01-AC-006 | I01-AT-006 | tests/acceptance/python/test_snapshot_budget.py |

## ISSUE-02 Compare Python Structure Changes Safely

| Requirement | Design | Plan | Acceptance | Test ID | Planned test file |
| --- | --- | --- | --- | --- | --- |
| I02-REQ-001 | I02-DES-001 | I02-PLAN-001 | I02-AC-001 | I02-AT-001 | tests/acceptance/python/test_diff_cli.py |
| I02-REQ-002 | I02-DES-002 | I02-PLAN-002 | I02-AC-002 | I02-AT-002 | tests/integration/python/test_impact_union_graph.py |
| I02-REQ-003 | I02-DES-003 | I02-PLAN-003 | I02-AC-003 | I02-AT-003 | tests/acceptance/git/test_diff_fail_closed.py |
| I02-REQ-004 | I02-DES-004 | I02-PLAN-004 | I02-AC-004 | I02-AT-004 | tests/security/test_git_read_only.py |
| I02-REQ-005 | I02-DES-005 | I02-PLAN-005 | I02-AC-005 | I02-AT-005 | tests/acceptance/python/test_semantic_seed.py |
| I02-REQ-006 | I02-DES-006 | I02-PLAN-006 | I02-AC-006 | I02-AT-006 | tests/integration/python/test_move_matching.py |
| I02-REQ-007 | I02-DES-006 | I02-PLAN-006 | I02-AC-007 | I02-AT-007 | tests/acceptance/git/test_changed_path_budget.py |

## ISSUE-03 Generate SQLAlchemy ER Snapshots

| Requirement | Design | Plan | Acceptance | Test ID | Planned test file |
| --- | --- | --- | --- | --- | --- |
| I03-REQ-001 | I03-DES-001 | I03-PLAN-001 | I03-AC-001 | I03-AT-001 | tests/acceptance/sqlalchemy/test_snapshot_cli.py |
| I03-REQ-002 | I03-DES-002 | I03-PLAN-002 | I03-AC-002 | I03-AT-002 | tests/integration/sqlalchemy/test_semantic_rows.py |
| I03-REQ-003 | I03-DES-003 | I03-PLAN-003 | I03-AC-003 | I03-AT-003 | tests/acceptance/sqlalchemy/test_snapshot_failures.py |
| I03-REQ-004 | I03-DES-004 | I03-PLAN-004 | I03-AC-004 | I03-AT-004 | tests/security/test_sqlalchemy_static_boundary.py |
| I03-REQ-005 | I03-DES-005 | I03-PLAN-005 | I03-AC-005 | I03-AT-005 | tests/acceptance/sqlalchemy/test_snapshot_determinism.py |
| I03-REQ-006 | I03-DES-005 | I03-PLAN-005 | I03-AC-006 | I03-AT-006 | tests/acceptance/sqlalchemy/test_applicability.py |

## ISSUE-04 Compare SQLAlchemy ER Changes

| Requirement | Design | Plan | Acceptance | Test ID | Planned test file |
| --- | --- | --- | --- | --- | --- |
| I04-REQ-001 | I04-DES-001 | I04-PLAN-001 | I04-AC-001 | I04-AT-001 | tests/acceptance/sqlalchemy/test_diff_cli.py |
| I04-REQ-002 | I04-DES-002 | I04-PLAN-002 | I04-AC-002 | I04-AT-002 | tests/acceptance/sqlalchemy/test_diff_plantuml.py |
| I04-REQ-003 | I04-DES-003 | I04-PLAN-003 | I04-AC-003 | I04-AT-003 | tests/integration/sqlalchemy/test_move_matching.py |
| I04-REQ-004 | I04-DES-004 | I04-PLAN-004 | I04-AC-004 | I04-AT-004 | tests/acceptance/sqlalchemy/test_diff_failures.py |
| I04-REQ-005 | I04-DES-005 | I04-PLAN-005 | I04-AC-005 | I04-AT-005 | tests/security/test_er_diff_redaction.py |
| I04-REQ-006 | I04-DES-005 | I04-PLAN-005 | I04-AC-006 | I04-AT-006 | tests/integration/sqlalchemy/test_impact_union_graph.py |

## ISSUE-05 Generate Next.js Component Snapshots

| Requirement | Design | Plan | Acceptance | Test ID | Planned test file |
| --- | --- | --- | --- | --- | --- |
| I05-REQ-001 | I05-DES-001 | I05-PLAN-001 | I05-AC-001 | I05-AT-001 | tests/acceptance/next/test_snapshot_cli.py |
| I05-REQ-002 | I05-DES-002 | I05-PLAN-002 | I05-AC-002 | I05-AT-002 | tests/contract/next/test_bridge_protocol.py |
| I05-REQ-003 | I05-DES-003 | I05-PLAN-003 | I05-AC-003 | I05-AT-003 | adapters/next/test/javascript-safe-subset.test.ts |
| I05-REQ-004 | I05-DES-004 | I05-PLAN-004 | I05-AC-004 | I05-AT-004 | tests/acceptance/next/test_snapshot_failures.py |
| I05-REQ-005 | I05-DES-005 | I05-PLAN-005 | I05-AC-005 | I05-AT-005 | tests/security/test_next_static_boundary.py |
| I05-REQ-006 | I05-DES-006 | I05-PLAN-005 | I05-AC-006 | I05-AT-006 | tests/acceptance/next/test_applicability.py |

## ISSUE-06 Compare Next.js Component Changes

| Requirement | Design | Plan | Acceptance | Test ID | Planned test file |
| --- | --- | --- | --- | --- | --- |
| I06-REQ-001 | I06-DES-001 | I06-PLAN-001 | I06-AC-001 | I06-AT-001 | tests/acceptance/next/test_diff_cli.py |
| I06-REQ-002 | I06-DES-002 | I06-PLAN-002 | I06-AC-002 | I06-AT-002 | adapters/next/test/semantic-seed.test.ts |
| I06-REQ-003 | I06-DES-003 | I06-PLAN-003 | I06-AC-003 | I06-AT-003 | adapters/next/test/move-matching.test.ts |
| I06-REQ-004 | I06-DES-004 | I06-PLAN-004 | I06-AC-004 | I06-AT-004 | tests/acceptance/next/test_diff_failures.py |
| I06-REQ-005 | I06-DES-005 | I06-PLAN-005 | I06-AC-005 | I06-AT-005 | tests/integration/next/test_impact_union_graph.py |
| I06-REQ-006 | I06-DES-005 | I06-PLAN-005 | I06-AC-006 | I06-AT-006 | adapters/next/test/dynamic-unknown.test.ts |

## ISSUE-07 Run Unified Multi-Domain Structure Comparison

| Requirement | Design | Plan | Acceptance | Test ID | Planned test file |
| --- | --- | --- | --- | --- | --- |
| I07-REQ-001 | I07-DES-001 | I07-PLAN-001 | I07-AC-001 | I07-AT-001 | tests/acceptance/test_multi_domain_cli.py |
| I07-REQ-002 | I07-DES-002 | I07-PLAN-002 | I07-AC-002 | I07-AT-002 | tests/acceptance/test_partial_domain_failure.py |
| I07-REQ-003 | I07-DES-003 | I07-PLAN-003 | I07-AC-003 | I07-AT-003 | tests/acceptance/test_multi_domain_applicability.py |
| I07-REQ-004 | I07-DES-004 | I07-PLAN-004 | I07-AC-004 | I07-AT-004 | tests/acceptance/test_run_atomicity.py |
| I07-REQ-005 | I07-DES-005 | I07-PLAN-005 | I07-AC-005 | I07-AT-005 | tests/acceptance/test_exit_codes.py |
| I07-REQ-006 | I07-DES-006 | I07-PLAN-006 | I07-AC-006 | I07-AT-006 | .github/workflows/ci.yml |
| I07-REQ-007 | I07-DES-006 | I07-PLAN-006 | I07-AC-007 | I07-AT-007 | tests/packaging/test_offline_install.py |


## Cross-contract verification points

| Contract | Producer | Consumer | Verification |
| --- | --- | --- | --- |
| semantic envelope v1 | ISSUE-01 | ISSUE-02〜07 | contract fixtures + manifest schema tests |
| SourceView/FileChangeSet/named endpoint | ISSUE-02 | ISSUE-04, ISSUE-06, ISSUE-07 | Git acceptance and dual snapshot digest tests |
| SQLAlchemy snapshot payload | ISSUE-03 | ISSUE-04, ISSUE-07 | row schema golden + diff input digest |
| Next adapter protocol v1 | ISSUE-05 | ISSUE-06, ISSUE-07 | Python/Node shared golden fixtures |
| domain outcome/aggregate manifest | ISSUE-07 | Initiative consumer | partial failure + exit table tests |

## Coverage conclusion

Initiative requirement 8件、Epic requirement 8件、seven Issue の全 Requirement/Design/Plan/Acceptance/Test ID が追跡可能。unresolved acceptance gap はない。実装時に planned symbol/path を変更する場合は、対応する Design/Plan/test trace を同じ change で更新する。
