# Issue #8 process boundary: root-cause analysis and implementation sequence

## Purpose and authority

This artifact records an advisory, read-only Strict analysis of the remaining I05-PLAN-002 Node process boundary. It does not amend Requirement, Design, Plan, schemas, or tests, and does not claim implementation readiness or Issue completion. Canonical Current v1 authority and locally verified source at the reviewed commit remain controlling.

## Review provenance

- Repository: `chemitaro/code-structure-viz`
- Branch: `iss-00008-generate-nextjs-component-snapshots`
- Expected and GitHub connector observed branch-tip SHA: `da70fd6ba360706b30f88d87d6ff69519bc1f1dc` (exact match)
- Oracle session: `required-strict-github-connector-verificati-1281`
- Conversation: `6ab8e230-f5bc-83e9-ba0c-a2e3f6e62083`
- Requested model/effort: GPT-5.6 Sol / Pro; recovered capture reports Thinking effort 5.6 Pro
- Recovery: the original completed conversation was harvested by exact target identity after the local wrapper/controller stopped. `state=completed`, `stop=no`, `send=no`, one assistant turn, capture identity matched. No second prompt was submitted.
- Recovered raw answer SHA-256: `daf2fabbbcb28a88feeae6528b812d9f3c753f038c86f425e771efd726c520c0` (original capture at `/private/tmp/issue8-process-analysis-1281-raw.md`; raw file is temporary, so this artifact preserves the relevant analysis below).
- The analysis ran no repository tests, Node process, OS race harness, or CI. All repository claims were checked against the exact GitHub SHA above and the corresponding local checkout. Technical recommendations below are analysis, not independent proof.
- Local capability snapshot: Python 3.12.6 on Darwin 27.0.0 reports `os.execve in os.supports_fd == False`; `os.open` and `os.stat` support `dir_fd`; `O_NOFOLLOW`, `O_CLOEXEC`, and `O_DIRECTORY` are present. This is a capability observation for this host/runtime only, not a statement about every Darwin/Python build.
- Primary references checked for the OS feasibility question: [Python 3.12 `os` documentation](https://docs.python.org/3.12/library/os.html) says FD-path support is platform-dependent and discoverable via `os.supports_fd`; [Apple `execve(2)` manual](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/execve.2.html) documents a pathname argument. These sources do not establish that no other Darwin primitive exists; they establish that the currently observed Python FD-exec route is unavailable and path-based `execve` alone is insufficient evidence of verified-FD binding.

## Bottom line

Current v1 is broadly coherent about the one-shot boundary and failure handling, but the path from its available policy fields to a truthful production `available` observation is not fully closed. Safest progress is staged and fail-closed: prove verified-open executable preflight first, prove a generic supervisor with a repository-owned helper separately, then prove OS-specific execution binding. Do not call any of these fixtures production Node evidence, and do not emit `available` until every required authority and race condition is observed.

At least two authority gaps prevent the full production launch from being derived safely from the current contract alone:

1. The pre-launch policy requires a Node version, while the strict one-request/one-response/one-process contract has no accepted pre-launch version channel. Probing `node --version` adds a process; learning `process.versions.node` in the adapter is post-launch and is absent from the closed response schema. Parsing binary strings or trusting an undocumented inventory would invent authority.
2. The packaged adapter is identified by Python package-resource bytes, whereas fixed argv names the absolute runtime path `/.code-structure-viz/next-adapter.mjs`. No physical mapping from those packaged bytes to that absolute path is defined. Placing a file in a private working directory does not satisfy an unrelated absolute path.

Also unproven before production `available`: a Darwin primitive that binds execution to the verified-open Node file; and a threat-model/immutability condition that prevents same-inode content mutation between hashing and execution. These must not be “solved” by silently weakening the identity guarantee.

## Exact-SHA source inventory

| Boundary | Verified state | Consequence |
| --- | --- | --- |
| Current-v1 Requirement/Design | Applicable runs only require stable Node >=22; one-shot adapter, fixed argv, private cwd, minimal env, bounded stdio/process and TOCTOU evidence are required. | Non-applicable runs must not discover/open/spawn Node. |
| Packaged adapter identity | `runner.py` resolves only the packaged resource and derives version/hash from one read. | This is adapter-resource identity only, not Node discovery or process evidence. |
| Request builder | `protocol.py` builds canonical private request bytes from `SourceAcquisitionSeal`. | Source acquisition/request work is not the missing OS process boundary. |
| Process schemas | Policy requires pre-launch Node realpath/hash/version; production observation requires measured identity and launch lifecycle. | A schema-valid object is not proof that a host executable was run. |
| Reference validator | Checks recorded policy/observation equality and identity relations, but does not operate the host process. | Fixture/contract green cannot establish spawn behavior. |
| Existing Git subprocess runner | Supplies useful examples for selectors, bounded capture, session/group cleanup, but uses different stdin/cwd/path and identity semantics. | Reuse patterns, not its authority model or implementation wholesale. |
| Plan | I05-PLAN-002A proves only packaged adapter identity; Node probe, policy, spawn, and observation are later work. | Preserve this boundary; do not relabel prior work as production readiness. |

## Recommended staged work

Labels S1–S4 below are implementation slices for discussion, not new canonical Plan IDs.

### S1 — verified-open Node preflight; no Node launch

After (and only after) package applicability authorizes a Next run: discover a candidate in the parent, convert it to an absolute path, walk every path component without following symlinks, open the final file read-only and close-on-exec, verify it is a regular executable, hash the same FD, record device/inode, compare identity before/after hashing, and keep the FD alive until the later launch result. Report capability and fail closed if any required primitive is unavailable.

This slice explicitly does not decide whether the first PATH candidate is trusted, establish a Node-version authority, build a complete production process policy, spawn the adapter, create a production observation, or claim I05-PLAN-002/Issue completion. Tests should include ancestor/final symlink rejection, path replacement, identity drift during hashing, FD lifecycle/double close, unsupported capability, and a non-applicable run whose discovery/open/temp/spawn traps are all untouched.

### S2 — common one-shot supervisor using a repository-owned non-Node helper

Separately prove private empty cwd, exact child environment, pipe-backed stdin/stdout/stderr, process group, monotonic timeout, concurrent incremental capture, count-before-retain limits, cap+1 full-buffer discard, group termination and wait, interrupt cleanup, and suppression of raw child stderr. Keep this a test-helper observation, never a Node production observation. Existing Git runner logic is a pattern reference only.

### S3 — platform-specific verified-FD execution spikes

- **Linux:** test whether the host supports an FD-bound execution primitive and demonstrate replacement-race resistance, FD closure, exec-success/error distinction, group lifecycle, and same-object identity. Any unsupported primitive or failed race test stops the route; do not fall back to path-based spawn.
- **Darwin:** verify a documented and experimentally demonstrated primitive that executes the verified-open object, with equivalent race/FD tests. The cited path-based spawn interfaces alone do not demonstrate this property. If no qualifying primitive is proven, production availability remains false; return to design rather than substituting `/dev/fd`, symlink, or path-based launch without an accepted guarantee.

### S4 — policy/observation integration, only after decision gates close

Construct policy and observation from the accepted authorities and actual measurements, exact-match them, bind spawn-time/post-spawn identity, then connect bounded response handling and existing safe failure classification. A process failure must not invoke the response decoder or synthesize target-completeness/publication data.

## Decision gates before production `available`

These are material trust/security choices, not implementation details:

1. **Node version authority:** either explicitly permit and observe a probe process; revise the one-process/response/policy contract to carry a same-process version measurement with coherent timing; or adopt a trusted signed/checked runtime inventory. Current sources do not select among these.
2. **Adapter physical runtime mapping:** define how exact packaged resource bytes become the fixed absolute argv entrypoint while retaining that resource as sole identity authority.
3. **Same-inode mutation threat model:** define sufficient immutability evidence (for example trusted non-writable roots or a trusted signed runtime inventory) or explicitly exclude same-user hostile mutation. Hash + inode alone does not make file contents immutable.
4. **Candidate trust:** decide whether first stable Node >=22 found on PATH is eligible after safe opening, or whether trusted roots/signature/inventory are required. FD binding prevents post-discovery path replacement; it does not establish that the initial candidate was trusted.
5. **Darwin feasibility:** this is an empirical stop/go gate. No production availability until the exact property is proven on Darwin; a failed spike does not authorize weakening the requirement.

## Minimum process-level regression matrix

| Case | Required result |
| --- | --- |
| Not applicable | Candidate discovery, temp allocation, open, and spawn are never called; no Node identity observation. |
| Final/ancestor symlink | Reject during verified open; ancestor components require no-follow treatment too. |
| PATH or pathname replacement after open | Execute the opened object or fail; never silently execute a replacement. |
| Hash/open identity drift | Reject; no production `available`. |
| Same-inode mutation | Detect and fail where measurable; if the execution-time race cannot be excluded, require a threat-model/design decision. |
| FD lifecycle | Verification FD is retained through spawn result, close-on-exec, and absent from child image except 0/1/2. |
| Process group/timeout | Terminate descendants, wait, clean up; deterministic classified failure. |
| stdout/stderr exact limit and cap+1 | Exact limit is accepted; cap+1 is counted before retention, all partial buffers discarded, child group stopped/waited; raw stderr never published. |
| Exact one response / noise / malformed / nonzero exit | Enforce existing precedence; no target/publication projection on process failure. |
| Hostile inherited environment / argv mutation | Child receives only the exact fixed environment and exact two-element argv; reject otherwise. |
| Unsupported OS primitive | Fail closed; no pathname fallback and no production observation. |
| Missing version or adapter physical mapping | Do not construct launch policy or `available`; preserve only honest preflight/unavailable evidence. |

## Local adjudication and next action

The analysis distinguishes contract coherence from implementation feasibility: bounded capture, cwd/env/stdio, group cleanup, optionality, and fixture/production separation are implementable and testable. The four decision gaps above are not closed by the passing reference validator or by a guessed API. The next safe step is to turn S1 into a bounded implementation brief tied to the existing Plan and tests; before production launch integration, bring the unresolved authority choices back for explicit decision and update canonical Requirement/Design/Plan accordingly. No code or platform support should be inferred from this advisory alone.
