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

- `uv run pytest tests/unit/next tests/contracts/test_json_schemas.py -q` —
  255 passed.
- `uv run pytest -q` — 1702 passed, 1 skipped.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — 174 files already formatted.
- `uv run mypy src tests` — passed for 150 source files.

The remaining process backend/OS proof gate is open. Plan-002 and Issue #8 are
not complete, and this record does not change the supported-platform contract.
