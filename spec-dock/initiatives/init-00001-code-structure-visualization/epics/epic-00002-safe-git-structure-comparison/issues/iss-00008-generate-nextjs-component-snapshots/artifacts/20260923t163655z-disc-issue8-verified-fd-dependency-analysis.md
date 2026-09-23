# Issue #8 — verified-executable-FD blocker analysis

Status: advisory investigation record; it does not amend Requirement, Design,
Plan, or any public schema. Canonical v1 authority remains unchanged.

## Strict analysis provenance

- Oracle session: `required-strict-github-connector-verificati-1074`.
- Requested reasoning: GPT-5.6 Pro. The UI resolved this to GPT-5.6 Sol with
  Pro thinking time; both selections were verified.
- Repository: `chemitaro/code-structure-viz`.
- Strict GitHub connector verified branch
  `iss-00008-generate-nextjs-component-snapshots` at
  `40765dcdf7de75fc35d60866dd8b1dabb0484db4` before and after analysis.
- Full Oracle output:
  `/Users/iwasawayuuta/.oracle/sessions/required-strict-github-connector-verificati-1074/output.log`
- Output SHA-256:
  `714ec9683eb7ef559856b8da5a68c52cb4b10470177e081b4fcf6d55ba1f0672`.
- The model's response is advisory. The root-cause conclusion below was
  checked against the live local contract, schemas, source seal, tests, and
  the previously recorded Darwin feasibility probe.

## Finding

This blocker is not merely an absent package or a missing Python convenience
function. The current process contract requires the executable actually
started to be the same verified-open executable whose identity and bytes were
checked before launch. The local Darwin host has not demonstrated a supported
OS path that binds `posix_spawn` to that verified file descriptor. The previous
probe found that Python does not expose FD execution support on this build and
that the documented pathname-based `posix_spawn`/tested `/dev/fd` routes do
not meet the contract. That is host-specific negative evidence, not proof
that no native implementation exists anywhere on Darwin.

Relevant platform facts:

- Apple documents `posix_spawn` with a pathname argument; this API contract
  alone does not provide same-verified-FD execution:
  [Apple `posix_spawn(2)`](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/posix_spawn.2.html).
- Python documents that `os.execve` can accept an open FD only where the
  platform exposes FD support, which should be checked through
  `os.execve in os.supports_fd`; the absence of `os.fexecve` by itself is not
  a sufficient conclusion:
  [Python `os` documentation](https://docs.python.org/3.12/library/os.html).
- Linux exposes `execveat` with `AT_EMPTY_PATH` and `fexecve` routes for an
  executable FD. However, an open descriptor does not make the underlying
  inode's contents immutable; a same-inode write after hashing still needs a
  separate immutability control:
  [Linux `execveat(2)`](https://man7.org/linux/man-pages/man2/execveat.2.html),
  [Linux `fexecve(3)`](https://man7.org/linux/man-pages/man3/fexecve.3.html).
- Apple suspended spawn and Security code validation/CDHash are possible
  ingredients for a different design, not proof that such a design satisfies
  this contract:
  [Apple spawn flags](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man3/posix_spawnattr_setflags.3.html),
  [Apple `SecCodeCheckValidity`](https://developer.apple.com/documentation/security/seccodecheckvalidity%28_%3A_%3A_%3A%29).

## Safest next implementation

Preserve the v1 verified-FD invariant and advance only on host-independent
boundaries until real OS evidence exists:

1. Build an immutable private request only from `SourceAcquisitionSeal`.
   Project/file identity, membership, role, content digest, and Base64 bytes
   must be derived from its one frozen source view and plan.
2. Canonicalize request JSON and request ID under the checked-in contract and
   reject an encoded stdin payload over the sealed limit before spawn.
3. Keep launch policy separate from observation. A desired policy or a test
   fixture must never be accepted as proof that production execution occurred.
4. Permit `available` only after an OS backend has passed real process tests
   for descriptor identity, same-inode mutation, pathname replacement, child
   FD inheritance, timeout, capture limits, and process-group cleanup.
5. If Darwin cannot meet the invariant through a supported route, return to
   the product/security owner to choose between deferring Darwin production
   execution and adopting a separately reviewed security contract. Do not
   silently substitute hash-then-path, reopen-and-compare, post-spawn checks,
   or an undocumented API.

## Implementation checkpoint (2026-09-24 JST)

The bounded first slice has been implemented in
`src/code_structure_viz/adapters/next/protocol.py` with an exercising test in
`tests/unit/next/test_protocol.py`. It creates the request from a real source
seal, validates the current JSON Schema and independent reference envelope,
and checks canonical bytes and request identity. It does not spawn Node and
does not claim production availability.

Verification:

- `uv run pytest tests/unit/next/test_protocol.py tests/contracts/test_next_contracts.py tests/contracts/test_json_schemas.py -q` —
  666 passed.
- `uv run pytest -q` — 1705 passed, 1 skipped.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — 174 files already formatted.
- `uv run mypy src tests` — passed for 150 source files.
- `./spec-dock/scripts/spec-dock validate` — `nodes=10`, passed.

## Follow-up fixed-SHA review attempt and local adjudication (2026-09-24 JST)

An additional `chatgpt-code-review-strict` run targeted the pushed change from
`40765dcdf7de75fc35d60866dd8b1dabb0484db4` through
`ebe28111ebe15ee9effda818cc6017fa07b09660` (Oracle session
`required-strict-github-connector-verificati-1078`). The browser response did
not satisfy the wrapper's JSON output contract; the wrapper exited 20 with
`OUS-O001-OUTPUT-CONTRACT-INVALID`. Therefore this run is neither a valid
review pass nor an accepted review failure. Its three candidate claims were
checked independently against the live schemas/reference validator:

1. The request builder had accepted trusted environment/profile v2 even though
   the v1 reference validator accepts only environment version `1` and profile
   `next-trusted-profile-v1`; both the builder and request schema now enforce
   those exact values.
2. `max_total_array_items` is response-aggregate-only, so applying it to the
   request would have contradicted the existing contract. However, the
   normalized request's `compilerOptions.paths` arrays had no per-array bound.
   A generated source seal with 100,001 replacements reproduced the gap. The
   request builder now checks per-array count and common JSON string/nesting
   bounds before canonical encoding; the shared config/request schema declares
   `maxItems: 100000`. The response-only aggregate remains unchanged.
3. `stage="request"` is not in the provenance enum and cannot pair with
   `CSV-NEXT-LIMIT-001`. Request-side structural or encoded-stdin overflow now
   uses `CSV-NEXT-LIMIT-001/stdin_encode`; the provenance schema, failure
   matrix, Design, and contract docs now agree. The request builder never
   spawns Node.

Focused contract/schema/Next tests passed (666 tests at the full focused run;
the additional targeted regression set passed 5 tests). The whole repository
suite passed 1705 tests with 1 skipped. This local remediation does not convert
the malformed Strict review response into a pass and does not close the
Darwin verified-FD execution gate.

The remaining process backend/OS proof gate is open. Plan-002 and Issue #8 are
not complete, and this record does not change the supported-platform contract.

## Fresh ChatGPT Use Strict analysis at current candidate (2026-09-24)

- Oracle session: `required-strict-github-connector-verificati-1079`.
- Requested model/reasoning: GPT-5.6 Sol / Pro. The browser model picker and
  Pro thinking selection were both UI-verified. Session metadata records
  `modelSelection.verified=true` and `thinkingSelection.verified=true`.
- Strict GitHub binding: repository `chemitaro/code-structure-viz`, branch
  `iss-00008-generate-nextjs-component-snapshots`, expected and connector-read
  full SHA `f86b741ce50c1e7381186baff1d3f26e6347fcfe`; exact comparison passed.
  The connector did not use the default or another branch.
- Full transcript:
  `/Users/iwasawayuuta/.oracle/sessions/required-strict-github-connector-verificati-1079/artifacts/transcript.md`
  (SHA-256 `961dad778ad78733f1bfc9e5df482202534b76360d8ef9905127fadabf11f0d4`).
  Oracle output log SHA-256:
  `c4bfa951a285c964fbe6ba76f22e2471904b2dedcaf062a251d3f788973a6dcd`.

### Adjudicated root cause and recommendation

The Strict analysis agrees with the earlier finding: this is not a missing
Python/Node package. Current v1 requires the actual process image to be bound
to the same open executable whose identity and bytes were checked before
launch, with the verified descriptor retained through spawn and not inherited
by the adapter. The local macOS/Python evidence does not demonstrate such a
supported launch path. It establishes that the tested documented routes fail
on this host, not that every Darwin implementation is impossible.

At the fixed SHA, `applicability.py`, configuration/source acquisition/source
graph, and the immutable source-sealed `protocol.py` request builder exist; a
production runner, Darwin/Linux backend, actual process observation, and
process-level acceptance do not. `protocol.py` creates bounded canonical
request bytes without spawning Node. The host was independently observed as
macOS 27.0 arm64, Python 3.12.6, with
`os.execve in os.supports_fd == False` and no `os.fexecve` attribute.

Strict recommendation, locally checked against the current-v1 contract and
plan:

1. Keep the verified-FD and fail-closed `unavailable` invariants; do not
   substitute hash-then-path, pathname-only spawn, reopen-and-compare,
   post-spawn detection, schema-valid objects, fixtures, or packaging evidence.
2. Continue only host-independent request/policy/unavailable boundaries in the
   production path. A native `VerifiedLaunchReceipt` may be the sole authority
   for constructing a production-available observation; ordinary dicts,
   fixtures, and schema validation must not promote themselves.
3. Run Darwin and Linux feasibility as isolated real-process harnesses which
   cannot emit production `available`. Linux FD execution is a candidate, not
   sufficient evidence: same-inode mutation still requires a separate
   immutability control. Darwin remains unproven, not declared impossible.
4. Require adversarial pathname replacement, symlink replacement, same-inode
   mutation, child-FD inheritance, FD lifetime, identity equality, timeout,
   capture-limit, and process-group cleanup tests before native backend
   acceptance. A wrong image that starts and is killed later is a failure.
5. Treat Linux-only completion, private-copy execution, or a signed-code /
   suspended-spawn model as a user-approved canonical security/platform
   decision, not an implementation inference.

The Strict result is **production `available`: NO-GO**;
**host-independent request preparation and isolated feasibility research: GO**.
Plan-002 and Issue #8 remain incomplete. This refresh is advisory evidence and
does not amend Requirement, Design, Plan, schemas, platform scope, or source.

### Local and primary-source cross-check

- Local runtime probe reproduced the current-host capability boundary without
  spawning Node. The earlier `/dev/fd` `/bin/echo` spike remains scoped to the
  exact tested `posix_spawn` routes; it is not a universal Darwin impossibility
  proof.
- Apple's documented `posix_spawn` interface takes an executable pathname,
  while Python documents FD execution as platform-dependent and exposes
  `os.supports_fd` for capability checks. Linux `execveat(AT_EMPTY_PATH)` and
  `fexecve` can designate an executable FD, but the Linux manual warns that
  descriptor execution alone does not stop post-hash changes to that inode.
- This Strict call is an analysis record, not the Plan-008 code-review pass.
  The current Plan's exact-SHA review gate and the package-only re-review
  objective remain separate and must be completed before advancing the
  implementation sequence.
