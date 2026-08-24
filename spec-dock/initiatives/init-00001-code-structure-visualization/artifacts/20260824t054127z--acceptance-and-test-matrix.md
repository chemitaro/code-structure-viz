# Acceptance and Test Matrix

## Initiative-level gates

| Gate | Type | Evidence | Failure effect |
| --- | --- | --- | --- |
| G-INIT-01 | normal | Python/SQLAlchemy/Next snapshot+diff acceptance suites | Initiative not complete |
| G-INIT-02 | intermediate release | ISSUE-01〜04 full suite + package/offline core-only | M2 release blocked |
| G-INIT-03 | final release | ISSUE-01〜07 full suite + aggregate manifest/exit/platform | Initiative completion blocked |
| G-INIT-04 | safety | target execution traps, Git immutability, redaction, absolute path scan | release stop |
| G-INIT-05 | determinism | same-input bytes/order/hash on macOS/Linux | release stop |
| G-INIT-06 | scope | no product HTML command/schema/UI/publication | specification rejection |

## Epic-level integration gates

| Gate | Boundary | Required test groups |
| --- | --- | --- |
| G-EPIC-01 | ISSUE-01→02 | semantic envelope compatibility, SourceView, Python dual snapshot |
| G-EPIC-02 | ISSUE-02/03→04 | endpoint/freeze reuse, SQLAlchemy row snapshot compatibility |
| G-EPIC-03 | ISSUE-01/02/05→06 | Python core/endpoint + Next protocol compatibility |
| G-EPIC-04 | ISSUE-04/06→07 | domain status, successful Artifact retention, aggregate hashes |
| G-EPIC-05 | package | core-only and Next-enabled offline install/license/lock |

## Issue acceptance matrix

| Issue | Test ID | Category | Observable behavior | Command |
| --- | --- | --- | --- | --- |
| ISSUE-01 | I01-AT-001 | normal | whole repository の Python class/member/relation を JSON と PlantUML へ決定的に出力する。 | uv run pytest tests/acceptance/python/test_snapshot_cli.py -q |
| ISSUE-01 | I01-AT-002 | boundary | path/module/class target と upstream/downstream depth が frontier を正しく制限する。 | uv run pytest tests/integration/python/test_targeted_snapshot.py -q |
| ISSUE-01 | I01-AT-003 | negative | syntax error と unreadable file を削除扱いせず incomplete と diagnostic にする。 | uv run pytest tests/acceptance/python/test_snapshot_failures.py -q |
| ISSUE-01 | I01-AT-004 | security | fixture の import side effect、secret literal、absolute path が実行・出力されない。 | uv run pytest tests/security/test_python_static_boundary.py -q |
| ISSUE-01 | I01-AT-005 | determinism | 同一入力の二回実行で semantic/PlantUML bytes と manifest artifact SHA が一致する。 | uv run pytest tests/acceptance/python/test_snapshot_determinism.py -q |
| ISSUE-01 | I01-AT-006 | budget | 501 entity は無切り捨て failure、明示 600 override は成功する。 | uv run pytest tests/acceptance/python/test_snapshot_budget.py -q |
| ISSUE-02 | I02-AT-001 | normal | 全 `--from`/`--to` 組合せで requested/resolved endpoint と snapshot digest が一致する。 | uv run pytest tests/acceptance/python/test_diff_cli.py -q |
| ISSUE-02 | I02-AT-002 | boundary | deleted class の before edge と union graph で upstream/downstream depth 1 を別々に選ぶ。 | uv run pytest tests/integration/python/test_impact_union_graph.py -q |
| ISSUE-02 | I02-AT-003 | negative | base 解決不能、U path、missing object、fingerprint drift で fail closed になる。 | uv run pytest tests/acceptance/git/test_diff_fail_closed.py -q |
| ISSUE-02 | I02-AT-004 | security | 全 Git invocation が read-only allowlist 内で、refs/index/worktree fingerprint を変更しない。 | uv run pytest tests/security/test_git_read_only.py -q |
| ISSUE-02 | I02-AT-005 | semantic | whitespace/comment/import-order only は seed 0、member/relation delta は seed になる。 | uv run pytest tests/acceptance/python/test_semantic_seed.py -q |
| ISSUE-02 | I02-AT-006 | matching | 一意な rename+fingerprint だけ moved、ambiguous candidate は removed+added になる。 | uv run pytest tests/integration/python/test_move_matching.py -q |
| ISSUE-02 | I02-AT-007 | budget | implicit 1,001 path は無切り捨て failure、明示 override は manifest に残る。 | uv run pytest tests/acceptance/git/test_changed_path_budget.py -q |
| ISSUE-03 | I03-AT-001 | normal | declarative model と association table を table/row semantic JSON と ER PlantUML にする。 | uv run pytest tests/acceptance/sqlalchemy/test_snapshot_cli.py -q |
| ISSUE-03 | I03-AT-002 | semantic | FK と relationship、constraint/index、inheritance を別 kind として保持する。 | uv run pytest tests/integration/sqlalchemy/test_semantic_rows.py -q |
| ISSUE-03 | I03-AT-003 | negative | runtime-only factory、duplicate table identity、broken declarative source を incomplete にする。 | uv run pytest tests/acceptance/sqlalchemy/test_snapshot_failures.py -q |
| ISSUE-03 | I03-AT-004 | security | DB connector と target import を呼ばず、default/URL/secret literal を Artifact へ出さない。 | uv run pytest tests/security/test_sqlalchemy_static_boundary.py -q |
| ISSUE-03 | I03-AT-005 | determinism | source declaration order が semantics に影響しない row ordering と hash を確認する。 | uv run pytest tests/acceptance/sqlalchemy/test_snapshot_determinism.py -q |
| ISSUE-03 | I03-AT-006 | applicability | ORM target なしは not_applicable、候補あり解析不能は incomplete を区別する。 | uv run pytest tests/acceptance/sqlalchemy/test_applicability.py -q |
| ISSUE-04 | I04-AT-001 | normal | table と各 row kind の added/removed/modified を before/after 値付きで出力する。 | uv run pytest tests/acceptance/sqlalchemy/test_diff_cli.py -q |
| ISSUE-04 | I04-AT-002 | visual | removed row が ghost row、modified row が before/after 表記、記号と線種を持つ。 | uv run pytest tests/acceptance/sqlalchemy/test_diff_plantuml.py -q |
| ISSUE-04 | I04-AT-003 | matching | 一意 structural match だけ moved、ambiguous table/row は removed+added。 | uv run pytest tests/integration/sqlalchemy/test_move_matching.py -q |
| ISSUE-04 | I04-AT-004 | negative | 片側 parse failure を削除にせず incomplete にする。 | uv run pytest tests/acceptance/sqlalchemy/test_diff_failures.py -q |
| ISSUE-04 | I04-AT-005 | security | before/after/diff の default literal と absolute path が redacted される。 | uv run pytest tests/security/test_er_diff_redaction.py -q |
| ISSUE-04 | I04-AT-006 | impact | deleted table の before edge を union graph context に保持する。 | uv run pytest tests/integration/sqlalchemy/test_impact_union_graph.py -q |
| ISSUE-05 | I05-AT-001 | normal | App/Pages Router の TS/TSX component、props、static relation、use client を出力する。 | uv run pytest tests/acceptance/next/test_snapshot_cli.py -q |
| ISSUE-05 | I05-AT-002 | adapter | versioned stdin/stdout JSON と Python envelope mapping を contract fixture で検証する。 | uv run pytest tests/contract/next/test_bridge_protocol.py -q |
| ISSUE-05 | I05-AT-003 | javascript | JS/JSX safe subset は解析し、unsafe dynamic behavior は unknown にする。 | npm --prefix adapters/next test -- --runInBand |
| ISSUE-05 | I05-AT-004 | negative | Node missing、schema mismatch、protocol noise、tsconfig alias failure を incomplete にする。 | uv run pytest tests/acceptance/next/test_snapshot_failures.py -q |
| ISSUE-05 | I05-AT-005 | security | build/config/plugin/application module を実行せず、literal/body/absolute path を出力しない。 | uv run pytest tests/security/test_next_static_boundary.py -q |
| ISSUE-05 | I05-AT-006 | applicability | Next target なしでは Node probe を行わず not_applicable。 | uv run pytest tests/acceptance/next/test_applicability.py -q |
| ISSUE-06 | I06-AT-001 | normal | component/prop/import/render/boundary change を member-level JSON と PlantUML にする。 | uv run pytest tests/acceptance/next/test_diff_cli.py -q |
| ISSUE-06 | I06-AT-002 | semantic | format/comment/import-order only は seed にならず static relation change は seed になる。 | npm --prefix adapters/next test -- semantic-seed |
| ISSUE-06 | I06-AT-003 | matching | 一意 component move だけ moved、ambiguous candidate は removed+added。 | npm --prefix adapters/next test -- move-matching |
| ISSUE-06 | I06-AT-004 | negative | 片側 adapter/config failure を removal にせず incomplete にする。 | uv run pytest tests/acceptance/next/test_diff_failures.py -q |
| ISSUE-06 | I06-AT-005 | impact | removed component の before edge を union graph context に保持する。 | uv run pytest tests/integration/next/test_impact_union_graph.py -q |
| ISSUE-06 | I06-AT-006 | unknown | nonliteral dynamic behavior を unknown とし runtime relation を生成しない。 | npm --prefix adapters/next test -- dynamic-unknown |
| ISSUE-07 | I07-AT-001 | normal | domain 無指定で三 domain を順に実行し、一つの aggregate manifest を出力する。 | uv run pytest tests/acceptance/test_multi_domain_cli.py -q |
| ISSUE-07 | I07-AT-002 | partial failure | Next incomplete、Python/SQLAlchemy complete で Artifact を保持し exit 3 にする。 | uv run pytest tests/acceptance/test_partial_domain_failure.py -q |
| ISSUE-07 | I07-AT-003 | applicability | Next target なしは Node 未導入でも not_applicable、overall exit 0。 | uv run pytest tests/acceptance/test_multi_domain_applicability.py -q |
| ISSUE-07 | I07-AT-004 | fatal | endpoint/fingerprint/output collision の run-level failure で success Artifact を公開しない。 | uv run pytest tests/acceptance/test_run_atomicity.py -q |
| ISSUE-07 | I07-AT-005 | exit contract | 0/1/2/3/130 と stdout/stderr/manifest の組合せを table-driven に検証する。 | uv run pytest tests/acceptance/test_exit_codes.py -q |
| ISSUE-07 | I07-AT-006 | platform | macOS/Linux、Python 3.12 と latest stable、Git 2.39 と latest、Next 選択時 Node 22 と latest を CI で確認する。 | uv run pytest && npm --prefix adapters/next test |
| ISSUE-07 | I07-AT-007 | packaging | uv lock/npm lock、license inventory、offline runtime install fixture を検証する。 | uv run pytest tests/packaging/test_offline_install.py -q |

## Normal paths

- 各 domain の whole-repository snapshot と targeted snapshot。
- diff の implicit base→frozen working tree、明示 from→working tree、implicit→to、exact from→to。
- 既定の両 format、単一 format、単一 domain、全 domain。
- 一 domain が incomplete でも complete sibling を保持する partial success。

## Boundary paths

| Boundary | Expected |
| --- | --- |
| 0 changed semantic seeds | complete diff with empty SemanticChangeSet; FileChangeSet may be nonempty |
| target absent | not_applicable, no fabricated empty diagram |
| deleted entity | before edge available in union impact graph |
| ambiguous move | removed+added, never moved |
| exactly 1000 changed paths | allowed implicit |
| 1001 changed paths | nonzero before semantic analysis unless explicit override |
| exactly 500 diagram entities | allowed |
| 501 diagram entities | no truncation, nonzero/incomplete unless explicit override |
| depth 0 | seed only, upstream/downstream empty |
| output file already exists | transaction not started, existing bytes unchanged |

## Negative and fail-closed paths

- invalid/missing repository、HEAD absent、revision invalid、implicit base unavailable、missing Git object。
- working-tree fingerprint changes between freeze and publication。
- unmerged U path affecting selected domain。
- syntax/type/protocol parse failure on one endpoint。
- unknown config key、wrong type、unsupported schema version、`--from working-tree`。
- Next target present with Node missing/unsupported、adapter protocol noise/schema mismatch。
- SQLAlchemy runtime-only factory/duplicate table identity。

## Security/privacy

| Threat | Fixture/action | Expected evidence |
| --- | --- | --- |
| target import side effect | module raises/writes on import | no side effect; AST-only result |
| DB access | engine/session connector trap | connector never called |
| Next build/plugin execution | package scripts/next config trap | process never invoked |
| Git mutation | instrument subprocess verb allowlist + state fingerprint | no fetch/checkout/reset/stash/clean/ref/index change |
| secret literal | token/password/URL/default fixtures | no raw value in JSON/Puml/manifest/stdout/stderr |
| absolute/temp path leak | random absolute roots | repository-relative only; byte scan clean |
| path escape | symlink outside repository | not followed; safe diagnostic |

## Determinism

- locale、filesystem traversal order、Git status order、JSON key/order、PlantUML alias/order を canonical sort。
- timestamp/random temp path を semantic Artifact へ含めない。run time metadata が必要なら manifest の non-content field と hash policy を明示する。
- same source/config/endpoint/tool/adapter version の two-run payload bytes と SHA-256 を比較する。

## Partial failure and exit

| Scenario | Domain states | Published | Exit |
| --- | --- | --- | --- |
| all complete | complete/complete/complete | all selected Artifacts + manifest | 0 |
| target absent | complete/not_applicable/not_applicable | complete Artifact + manifest | 0 |
| Next incomplete | complete/complete/incomplete | Python+SQLA safe Artifacts + any safe Next partial + manifest | 3 |
| invalid config | no domain run | none | 2 |
| fingerprint drift | transaction discarded | none | 1 |
| interrupt | staging cleanup | none from interrupted run | 130 |

## CI matrix

- OS: macOS latest runner、Linux latest runner。native Windows なし。
- Python: explicit 3.12 minimum、repository-managed explicit latest stable。
- Git: 2.39 fixture/container minimum、runner latest stable capability lane。
- Node: Next-enabled lane only; explicit 22 minimum、repository-managed explicit latest stable。
- package: `uv sync --frozen --offline` equivalent cache fixture、`npm ci --offline` cache fixture、license inventory deny/allow gate。
