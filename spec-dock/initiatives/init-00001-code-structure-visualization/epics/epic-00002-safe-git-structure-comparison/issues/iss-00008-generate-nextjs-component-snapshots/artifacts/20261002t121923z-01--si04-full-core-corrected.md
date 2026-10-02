# Issue #8 SI-04 full Core reference — corrected executable implementation brief

## 1. Fixed point and execution judgment

This brief supersedes the previous SI-04 authoring brief operationally. The original SI-04 unit base remains unchanged:

```text
caf38329826ae34f8e3cb330b83b97e0357b7dc5
```

GitHub connector verification was repeated before using prior conversation context or the attached brief:

| Item | Verified value |
|---|---|
| repository | `chemitaro/code-structure-viz` |
| branch | `iss-00008-generate-nextjs-component-snapshots` |
| expected SHA | `caf38329826ae34f8e3cb330b83b97e0357b7dc5` |
| connector branch tip | `caf38329826ae34f8e3cb330b83b97e0357b7dc5` |
| comparison | exact match |

No material authority contradiction was found. SI-04 remains executable under the accepted source-inventory / owner-closed Option A specification. The correction required here is implementation-specific: the old export census / witness façade cannot be reused as a generic source oracle because several of its higher-level helpers bind to fixed legacy fixture files.

The attached brief contract requires the implementation brief to remain grounded in the whole supplied specification and verified code, distinguish existing behavior from proposed work, identify concrete targets and completion evidence, and return a blocker rather than silently amend the specification if a material contradiction is found. :chatgpt-content-reference{index="0"}

The caller-supplied implementer target remains **GPT-6.1 Sol / Max**. This is authoring guidance, not verified runtime model identity.

---

## 2. Scope

SI-04 implements only the **full v3 Core reference**.

The unit starts from:

```text
RetainedExecutionAssets (adapter 0.2.0)
+ complete SourceAcquisitionSeal
+ RetainedRequestFrameV2
+ ValidatedTransportCandidateV2
+ SI-03 source-inventory semantics
```

and closes:

```text
full D
→ semantic record/type validation
→ mandatory root seeds
→ exact causal edges
→ typed least-fixed-point taint
→ same-seal source-byte-bound export evidence
→ source-graph locality
→ target / selection semantics
→ exact File/Module owner-closed projection
→ actual model-record budget
→ export/source unavailability
→ entity budget
→ parent-owned compatibility-v3
→ immutable ValidatedSemanticDecisionV3
   or RejectedSemanticDecisionV3
```

The following remain out of scope:

```text
SI-05 public semantic-v3/schema/exact refs
SI-05 provenance/run/candidates-v3
domain/publication/root/stdout v2 chain
SI-06 diagnostic/stderr/final publication
production TypeScript execution
actual OS/process/CLI certification
package/wheel/sdist acceptance
ASSET policy changes
full A02 / cumulative A03 / Issue Final
```

No public v3 schema or public consumer is to be added in this unit.

---

## 3. Authority

The implementation must preserve, rather than reinterpret, these authorities:

- `CONTEXT.md`
- Current SI section of `requirement.md`
- Current SI section of `design.md`
- Current SI implementation table and stop conditions in `plan.md`
- `20261002t001435z-adr-issue8-source-inventory-safe-subset.md`
- `20261002t041350z-adr-issue8-owner-closed-file-module-publication.md`
- `docs/contracts/next-semantic-admission-v3.md`
- `docs/contracts/next-semantic-v3.md` as downstream SI-05 boundary
- `docs/contracts/next-compatibility-v3.md`
- unchanged lower-owner contracts in:
  - `next-semantic-admission-v2.md`
  - `next-adapter-request-v2.md`
  - `next-adapter-exchange-v2.md`
  - `next-adapter-response-v2.md`

The SI-03 review artifact at `23072c288fc203071c10bfe3305e6ec5d3b055fe` is scoped evidence that SI-03 passed. It is not additional semantic authority.

---

## 4. Existing implementation retained unchanged

The following SI-03 APIs already exist and remain the normal source-inventory seam:

```text
tests/contracts/next_source_inventory_v3_reference.py
  ValidatedSourceInventorySeamV3
  retain_source_inventory_seam_v3

tests/contracts/next_source_inventory_v3_validation.py
  validate_source_record_payloads_v3
  validate_public_source_metadata_v3
  resolve_discovered_v3
  full_module_owners_v3
  derive_source_projection_v3
  measure_source_inventory_v3
  source_partition_preimage_v3
  validate_source_inventory_seam_v3
```

They already close:

- same request/seal/assets ownership;
- acquired Project/File reconstruction;
- normal one-Module-per-program-File ownership;
- independent Module eligibility;
- owner-closed File partition;
- acquired/public Project views;
- private/public record-reference closure;
- actual source-inventory counts;
- partition fingerprint.

They do **not** certify full mandatory root completeness, full causal closure, typed least fixed point, complete PropsTypeIR grammar, source locality, complete target/export semantics, or Core budget routing. SI-04 must add those checks without weakening SI-03.

The normal `full_module_owners_v3()` rule stays strict. Do not add an exception parameter to it.

---

# Part I — Corrected export reuse boundary

## 5. Exact old export helper classification

The previous brief incorrectly treated the old `expected_export_*` façade as if it were source-generic. It is not.

### 5.1 Reusable source-parameterized primitives

The following existing functions are genuinely parameterized by their inputs and do not themselves load the fixed export fixture corpus:

| Symbol | Reuse status | Reason |
|---|---|---|
| `_export_tokens(content)` | reuse | scans supplied immutable bytes |
| `_scan_export_file(path, content)` | reuse | derives export syntax and byte spans from supplied bytes |
| `_string_export_resolution(syntax, content, components)` | reuse narrowly | source bytes + positive Component evidence; does not load export fixture |
| `_resolve_export_source_path(owner_path, source_specifier)` | reuse | pure path resolver |
| `recompute_export_graph_case(case)` | reuse | operates entirely on passed declaration/edge case |
| `_reexport_join_key(row)` | reuse | pure identity tuple |
| `join_reexport_observations_to_edges(syntax_rows, raw_edges, ...)` | reuse | exact bijection over supplied rows |
| `_terminal_export_source_path(graph_witness, graph_result)` | reuse | follows supplied graph result |
| `string_export_target_resolutions(...)` | reuse | pure transformation of validated observations |
| `expected_string_export_diagnostics(observations)` | reuse only on v3-derived public observations | uses current diagnostic catalog, not legacy export corpus |

`recompute_export_graph_case()` is particularly useful. It does not read a global graph. Its correctness depends entirely on the caller supplying an independently derived `case["modules"]` and `case["edges"]`.

### 5.2 Not reusable as v3 source authority

The following must **not** be called as the expected-value oracle by SI-04:

```text
load_export_census_fixture
load_export_graph_fixture
load_export_graph_raw_fixture
load_export_graph_cases

scan_export_syntax_census
_export_syntax_rows_for_model
_export_census_for_model
_reexport_graph_index

expected_export_observations
validate_export_observations
expected_export_resolution_witness
expected_export_reexport_witness
_export_binding_projection_for_model
expected_export_coverage_counts
```

Concrete reasons:

- `_export_syntax_rows_for_model()` loads `load_export_census_fixture()` and resolves every Module path against the legacy catalog, including suffix fallback.
- `_export_census_for_model()` again loads that catalog and verifies File hash/size against those old bytes.
- It then uses `_reexport_graph_index()` and `load_export_graph_raw_fixture()`, which are a separate fixed legacy declaration/edge corpus.
- `expected_export_observations()`, `validate_export_observations()`, both witness helpers, public binding projection, and coverage counts transitively depend on those fixture-bound functions.

Therefore a new source file such as `src/button.tsx` cannot honestly be certified through those functions.

No monkeypatch, suffix relabeling, fixture substitution, or temporary mutation of the old fixture globals is allowed.

---

## 6. Correct v3 export architecture

SI-04 must add a v3-local export reference pipeline inside the proposed Core validation module.

Proposed internal functions:

```python
def frozen_source_bytes_v3(
    candidate: ValidatedTransportCandidateV2,
    seal: SourceAcquisitionSeal,
) -> dict[str, bytes]: ...

def scan_export_syntax_v3(
    full_d: FullResolvedViewV3,
    frozen_bytes: dict[str, bytes],
) -> tuple[dict[str, Any], ...]: ...

def derive_direct_export_table_v3(
    full_d: FullResolvedViewV3,
    syntax_rows: tuple[dict[str, Any], ...],
    frozen_bytes: dict[str, bytes],
) -> tuple[dict[str, Any], ...]: ...

def derive_raw_reexport_edges_v3(
    syntax_rows: tuple[dict[str, Any], ...],
) -> tuple[dict[str, Any], ...]: ...

def derive_export_evidence_v3(
    full_d: FullResolvedViewV3,
    public_model: dict[str, Any],
    frozen_bytes: dict[str, bytes],
    request_targets: list[str],
) -> DerivedExportEvidenceV3: ...

def validate_export_evidence_v3(
    candidate: ValidatedTransportCandidateV2,
    full_d: FullResolvedViewV3,
    evidence: DerivedExportEvidenceV3,
) -> None: ...
```

These are proposed symbols, not existing APIs.

`DerivedExportEvidenceV3` should be an internal immutable result containing at least:

```text
full_syntax_observations
full_reexport_witnesses
public_export_bindings
public_resolution_witnesses
public_coverage_counts
public_string_export_diagnostics
target_adjustments
export_failure_rows
```

It must be re-derived independently during `validate_semantic_decision_v3`; retained producer caches are not the expected-value oracle.

---

## 7. Same-seal source bytes

`frozen_source_bytes_v3()` must read from the actual retained `SourceAcquisitionSeal`:

```python
seal.source_view.files[*].content
```

`SourceFile.content` is immutable `bytes` and is excluded from repr.

The same helper must join those bytes back to the retained request:

```text
request File path
request content_base64
request size_bytes
request sha256
        ==
seal SourceFile path
seal SourceFile.content
seal SourceFile.size_bytes
seal SourceFile.sha256
```

`validate_response_request_v2()` and the existing request/seal validators remain lower-owner guards, but the export scanner itself must consume the bytes from the sealed owner rather than caller bytes or fixture loaders.

Do not accept:

```text
dict[path, bytes] from caller
temporary filesystem reread
load_export_census_fixture()
submitted token hashes
submitted byte spans
```

as export syntax authority.

---

## 8. Full source syntax census

For **every full-D Module**, locate its acquired program File and run:

```python
_scan_export_file(module["path"], frozen_bytes[module["path"]])
```

The census covers D, not just public M.

Thus:

```text
D Module
  → same acquired File
  → same sealed bytes
  → independently scanned syntax rows
```

A proof-only Module's export syntax is still validated.

However:

```text
proof-only export syntax ≠ public export success
```

Public success is derived later from M.

Every syntax row must retain the byte-bound identity already defined by the old scanner:

```text
owner_file_path
byte_start
byte_end
token_identity
syntax_identity
syntax_kind
exported_name
role
reexport
star
source_specifier
imported_name
```

A changed source byte sequence with unchanged submitted witness must therefore fail.

---

## 9. Direct declaration classification without fake TypeChecker evidence

The v3 reference must not use:

```text
"no Component was submitted" => "therefore this is a non-component value"
```

That inference is forbidden.

For each non-reexport syntax row, classify only independently provable evidence.

### Component

A direct export may be resolved as `component` only when:

1. the source-byte scanner identifies the declaration/exported identifier; and
2. full D contains exactly one valid Component owned by that Module with the matching declaration key.

This is a **reference Core join**, not proof that TypeScript actually recognized the Component in production.

### Type

A source-byte row whose closed syntax has:

```text
role == "type"
```

may be resolved as `type`.

### Primitive non-component value

A `value` resolution without a Component is permitted only for a narrow, byte-provable closed form.

Reuse the existing primitive-constant rule embodied by `_string_export_resolution()`:

```text
const <identifier> = <single primitive literal>;
```

where the initializer is the supported literal class already used by that helper.

For ordinary non-string export rows, implement the same small source-token proof locally rather than interpreting Component absence as positive value evidence.

### Otherwise

If the reference implementation cannot independently prove:

```text
component
type
primitive literal value
```

it must not synthesize a `value` observation.

For SI-04 reference admission, an otherwise unproven direct semantic resolution is an invariant failure (`model_proof`), not a new domain diagnostic or new semantic reason.

Production TypeChecker evidence remains A04 work.

---

## 10. Re-export graph built only from v3-derived evidence

Construct a local graph case from the source-byte census.

### Direct module tables

For each full-D Module:

```json
{
  "path": "src/button.tsx",
  "exports": [
    {
      "name": "Button",
      "resolution": "component",
      "target_declaration_key": "Button"
    }
  ]
}
```

The `exports` entries come from the independently classified direct source rows above.

String-named exports whose public name is not a normal identifier are not inserted into this direct graph table. They remain separately validated string-export observations.

### Raw re-export edges

For every non-string re-export syntax row, construct:

```json
{
  "owner_file_path": "...",
  "source_specifier": "...",
  "imported_name": "...",
  "exported_name": "...",
  "syntax_identity": "...",
  "byte_start": 0,
  "byte_end": 0
}
```

The identity fields are copied from the independently scanned syntax row, not from submitted proof.

Then:

```python
joined = join_reexport_observations_to_edges(
    syntax_rows,
    raw_edges,
)

graph_result = recompute_export_graph_case(
    {
        "modules": direct_module_tables,
        "edges": raw_edges,
    }
)
```

Both functions are safe to reuse here because the caller supplies all source-derived inputs.

Use `_terminal_export_source_path()` against this **same graph_result**, not `load_export_graph_raw_fixture()`.

---

## 11. Re-export resolution

Map each graph witness back into full D:

```text
resolved_source_file_path
   ↓
full-D Module at that path
   ↓
target_declaration_key
   ↓
full-D Component owned by that Module
```

If `graph_result` says `resolution == component`, the corresponding Component must exist and be unique.

Do not turn a missing Component into `value`.

The resulting expected re-export witness keeps the existing wire shape:

```text
owner_module_id
owner_file_path
byte_start
byte_end
token_identity
syntax_identity
source_specifier
imported_name
original_exported_name
exported_name
resolved_source_module_id
expanded_exported_name
target_declaration_id
resolution
diagnostic
```

Cycle / conflict / missing-source / missing-export semantics remain exactly those returned by `recompute_export_graph_case()`.

No new diagnostic vocabulary is introduced.

---

## 12. Full-D versus public-M export views

Validation happens in two stages.

### Stage A — full D

First validate all source syntax and export witnesses against:

```text
full acquired source
+
full D
```

This includes proof-only Modules and Components.

Submitted:

```text
proof.export_observations
proof.export_reexport_witness
```

must exactly match the same-seal-derived full evidence.

A proof-only export cannot disappear merely because its Module was excluded from public M.

### Stage B — public M projection

Only after the complete evidence passes do we project public success.

A public ExportBinding is allowed only when:

```text
owner Module ∈ M
and
resolution == component
and
target Component ∈ M
```

For direct exports, project from the validated direct observation.

For re-exports, project from the independently recomputed re-export graph witness.

Do not derive the re-export binding from the submitted observation row.

Expected ExportBinding identity remains:

```text
kind = export_binding
owner_id
exported_name
role = value
target_component_id
resolution_kind = component
reexport
```

and its ID remains the unchanged semantic ID algorithm.

Then compare the independently projected binding set for exact equality with public `model["members"]` filtered to `kind == "export_binding"`.

This exact equality catches coordinated:

```text
delete source-derived observation
+
delete public ExportBinding
+
repair model counts/hash
```

attempts.

---

## 13. Resolution witness and public coverage

After independently deriving public ExportBindings, derive `proof.export_resolution_witness` from those computed bindings, not from submitted members.

Each row is:

```json
{
  "member_id": "...",
  "resolution": "component",
  "component_id": "..."
}
```

and must exactly equal the submitted witness array.

Public export coverage is computed only from validated export evidence whose owner belongs to M.

Therefore:

```text
proof-only value export
    does not increment public non-component value count

proof-only type export
    does not increment public type-only count

proof-only component export
    does not create a public ExportBinding
```

`coverage.non_component_value_export_count` and
`coverage.type_only_export_count` are independently recomputed from the public-M projection.

Proof-only rows remain necessary for complete private proof but do not become public success.

---

## 14. String-export behavior

The existing source-parameterized `_string_export_resolution()` may be reused after passing:

```text
same sealed content
+
full-D Components owned by the Module
```

Its accepted semantics remain:

| Proven evidence | resolution / disposition |
|---|---|
| positive Component witness | `component` |
| type-only syntax | `type` |
| primitive const | `value / intentional_unsupported` |
| otherwise | `unknown / export_failure` |

For a public owner Module, an `intentional_unsupported` observation projects the existing:

```text
CSV-NEXT-UNSUPPORTED-001
severity=info
recoverable=true
outcome=complete
ref_permission=symbol
```

diagnostic.

The `symbol_ref` must identify the public owner Module, preserving public-M reference closure.

Do not produce an unsupported diagnostic whose symbol points at a proof-only Module.

---

## 15. Target and export failure ordering

Explicit targets are processed after the full source/proof/export evidence is valid.

For a string export intersecting an explicit target, reuse the semantics of:

```python
string_export_target_resolutions(...)
```

after feeding it the **v3 source-bound observations**.

Thus:

```text
explicit selected unsupported export
→ TARGET-001 / unsupported_export
→ no payload
```

at stage 4.

Without an explicit selected target:

```text
unknown string export / re-export cycle/conflict
→ record-budget stage first
→ then CSV-NEXT-EXPORT-001
```

at stage 6.

A proof-only export failure on an unrelated excluded owner must not independently make an unrelated public safe subset unavailable.

Full evidence is still checked, but export-unavailability routing is based on the eligible/public or selected export surface.

---

# Part II — New closed 0.2.0 reference corpus

## 16. Physical location

No additional old-style JSON export fixture is needed.

Keep the new closed corpus as literal data in the proposed:

```text
tests/contracts/test_next_semantic_core_v3.py
```

and materialize it into a temporary repository through the existing real acquisition flow.

This avoids creating a second global fixture registry and makes it impossible for the Core validator to silently fall back to `load_export_*()`.

Proposed product-code/test boundary remains:

```text
tests/contracts/next_semantic_core_v3_reference.py
tests/contracts/next_semantic_core_v3_validation.py
tests/contracts/test_next_semantic_core_v3.py
```

Authorized SpecDock evidence Artifacts and limited Plan/Report status updates may be added separately through SpecDock commands; they are not part of the three-file Core implementation boundary.

---

## 17. Minimal first full-Core positive corpus

Use exactly these literal source bytes for the first normal positive:

```python
CORE_V3_SOURCE_BYTES = {
    "package.json":
        b'{"dependencies":{"next":"15"}}',

    "tsconfig.json":
        b'{"include":["src/**/*"]}',

    "src/button.tsx":
        b"export function Button() { return null; }\n",

    "src/index.ts":
        b'export { Button as Primary } from "./button";\n',

    "src/value.ts":
        b'const value = 1;\n'
        b'export { value as "opaque-public-name" };\n',

    "src/global.d.ts":
        b"declare interface Window { marker: string; }\n",
}
```

The acquisition must use:

```text
DescriptorAnchoredSourceReadSession
→ seal_source_acquisition
→ actual complete SourceAcquisitionSeal
→ build_request_frame_v2
→ 0.2.0 retained assets
→ actual request/response/transport owner flow
```

Do not construct a `SourceAcquisitionSeal` manually.

### Worked source literals

For this proposed ASCII corpus:

| path | bytes | SHA-256 |
|---|---:|---|
| `package.json` | 30 | `e1cba2a2526ff053f2d5931bf33cfc1e9eabf400fe0651ee341cb4dac23e29f4` |
| `tsconfig.json` | 24 | `d22d6c841f113e55b1ad3c0858b78148e6c5196bb88c91b8cd213f22b7524a9b` |
| `src/button.tsx` | 42 | `1dc7a2111f31e37e693b6b6befa5c7141411471168e20a2fc93c886382dfb862` |
| `src/index.ts` | 46 | `4a0d75a51f0ffd2f39ab05d7e739e1e6d045bb1e1e7177d34a32a80494592788` |
| `src/value.ts` | 59 | `cd622fd53afb830fdded48bebbd77ac22f2a22da282b34bdf977cb1b3006fadd` |
| `src/global.d.ts` | 45 | `434a26e7917f46b586775bc326d6ba34994e183118ffecf96c9caf8e09207643` |

The test should retain these as literals and independently confirm the acquired File metadata matches them.

Do not derive these expected hashes from the new Core validator.

---

## 18. Minimal coherent semantic records

Project root `.` retains the existing semantic Project identity:

```text
next:project:530b20c858c6039c19737f386f96cfabdadda6b8a0a1c98b5ca639beb2765c25
```

Worked record IDs for this proposed corpus:

### Files

```text
package.json
next:file:6e5a491cdd30e69e4cf115a95b99ad11d83beac749f4f20d7fa12cb26d9f7c0c

tsconfig.json
next:file:c891008136a6466799eb75e12e6b6d7b2bdb35587cb8c2f96b3b5a720da870bf

src/button.tsx
next:file:7d940b2adbc319b4843ed7495d2cfce15c2f5f3450ee587273b53f4f8d5ac2b5

src/index.ts
next:file:4d7ea21c5296aea27a6fd1ea2b3ec895bd40dfc5c827e1759e0a401af1ecaf30

src/value.ts
next:file:b2257b187308437ce03e40f7793970289bdb1aa71c5167b7796501cf91efa6ac

src/global.d.ts
next:file:8cb22e35356bd13a3869a5dd8bd680300b8f8ba5bd33bcdbfc7653cc1eba3e76
```

### Modules

```text
src/button.tsx
next:module:4130a3bcc0554a01d2f7111d613cdf150e6e3104575fe6a46ee5b057c6414b7d

src/index.ts
next:module:024a4e0cf9fee9411a055c04c95ff34b0909e69f80b3f4a9dff0cec438c9e4c3

src/value.ts
next:module:f8a3c82434f22cef3d54190f8a81a7b7788efcbac0cdbec594a7f1b0edbbf16b
```

Every Module must have:

```text
router_context = "none"
client_entry = false
derived_roles = []
```

and every Module must have its matching `router_context` fact.

Worked fact IDs:

```text
button:
next:fact:fad69b0c4f9499f6b03b9a3ed75bde3416620b9f724cb392ece749b1883ac3b7

index:
next:fact:5af45a15f0cfe0ec35e9c1fe62bea79bf1fefba6968ed6bfa69573c74ca51af0

value:
next:fact:75c153d8a3122c1eec2e9b23b9b93d7c7f237265c7b785b70b1c4c2e892dd8e9
```

This closes the Module/fact correspondence that the SI-03 minimal fixture did not provide.

---

## 19. Component and public bindings

The positive corpus contains one reference Component:

```text
Module: src/button.tsx
declaration_key: Button
recognition_evidence: ["trusted_callable"]
props_state: no_props
```

Worked Component ID:

```text
next:component:56983cafa7d11d2d42ecdca27a9061799006d6154f77cb9e4ee2a954d95659e8
```

Expected public ExportBindings:

```text
Button:
next:member:9a0c2c2d46a1812864d748f99ffa5448f755aa3edcd7894873c291d46c958279

Primary:
next:member:0f044044b752a86452130d42b130ed1ea2952d101484e73c283db9d84094a1de
```

Both target the same Button Component.

These IDs are fixed from the unchanged semantic identity preimages, not from the new Core producer.

The test should independently recompute the literal preimages outside the new v3 validator before accepting these values as KATs.

---

## 20. Independent export syntax KAT

### `src/button.tsx`

Source:

```text
export function Button() { return null; }
```

Worked source-bound observation:

```text
byte_start = 0
byte_end = 41
syntax_kind = named_export
exported_name = Button
imported_name = Button
role = value
reexport = false
```

Token bytes SHA-256:

```text
79e383a1be08ab3834a04380a79cf0de83bcdaeb7cc6e1c480e36ae53288bbf5
```

Token identity:

```text
c5a8c4d6b89384890dcfa31e00c713bbbc6eb3d5f95f02e204e96b817b271006
```

Syntax identity:

```text
export:src/button.tsx:0:41:named_export:Button
```

Expected resolution:

```text
component
```

because there is positive full-D Component evidence for declaration `Button`.

### `src/index.ts`

Source:

```text
export { Button as Primary } from "./button";
```

The scanner row is tied to the export-list item, not the whole statement:

```text
byte_start = 9
byte_end = 26
token bytes = Button as Primary
syntax_kind = reexport
imported_name = Button
exported_name = Primary
source_specifier = ./button
```

Token bytes SHA-256:

```text
5a061af3c771a939d195d636e9b0f8c3275c650896fda93c26ea0a25581aa765
```

Token identity:

```text
0629e28100820ed2c813333c1cb6ee468df1cbe8342568cf400c347d27bc7317
```

Syntax identity:

```text
export:src/index.ts:9:26:reexport:Primary
```

The independently constructed raw edge is therefore:

```json
{
  "owner_file_path": "src/index.ts",
  "source_specifier": "./button",
  "imported_name": "Button",
  "exported_name": "Primary",
  "syntax_identity": "export:src/index.ts:9:26:reexport:Primary",
  "byte_start": 9,
  "byte_end": 26
}
```

`recompute_export_graph_case()` must resolve this to:

```text
resolved_source_file_path = src/button.tsx
expanded_exported_name = Button
target_declaration_key = Button
resolution = component
diagnostic = null
```

which then joins to the Button Component ID above.

---

## 21. Independently grounded intentional unsupported case

`src/value.ts` contains:

```text
const value = 1;
export { value as "opaque-public-name" };
```

The source scanner row spans:

```text
byte_start = 26
byte_end = 55
syntax_kind = string_export
```

Token identity:

```text
5c9ef3c2108d37898e837134472acdff79f8da99522c50aa48d053c07b35857f
```

Syntax identity:

```text
export:src/value.ts:26:55:string_export
```

The imported name is `value`.

The source bytes independently show:

```text
const value = 1;
```

which is the closed primitive-literal case.

Expected result:

```text
resolution = value
resolution_basis = primitive_const
disposition = intentional_unsupported
component_id = null
target_declaration_id = null
resolved_source_module_id = src/value.ts Module ID
```

The Module remains public.

Expected public diagnostic:

```json
{
  "code": "CSV-NEXT-UNSUPPORTED-001",
  "severity": "info",
  "recoverable": true,
  "outcome": "complete",
  "ref_permission": "symbol",
  "path_ref": null,
  "symbol_ref": "next:module:f8a3c82434f22cef3d54190f8a81a7b7788efcbac0cdbec594a7f1b0edbbf16b",
  "count": 1
}
```

This verifies legitimate unsupported-complete behavior without manufacturing a non-component TypeChecker result from missing Component data.

---

## 22. Full positive coverage

For the six-file positive corpus:

```text
projects   = 1
files      = 6
modules    = 3
components = 1
members    = 2
relations  = 0
facts      = 3

internal_entities = 4
published         = 16
discovered        = 16
excluded          = 0
failed            = 0
```

Other coverage:

```text
failed_files = []
affected_ids = []
taint_frontier = []
opaque_reason_counts = {}
unknown_relation_count = 0
correlation_losses = []
non_component_value_export_count = 1
type_only_export_count = 0
target_completeness = []
```

Proof:

```text
discovered_records = all 16 records exactly once
failure_roots = []
causal_edges = []
excluded = []
failed = []
target_resolutions = []
```

plus the independently derived export observations/resolution/re-export witnesses.

The source-inventory seam must also pass before the Core factory is called.

This is the **first full-Core positive fixture**.

It is reference-only evidence:

- acquisition bytes are real and seal-owned;
- source graph and export syntax are derived from those real bytes;
- semantic Module/Fact/Component records are explicit reference witnesses;
- no actual TypeScript Compiler API execution occurs;
- no claim of production Component recognition is made.

---

## 23. Unknown export case

Add a separate source variant:

```python
b'const value = makeValue();\n'
b'export { value as "opaque-public-name" };\n'
```

For path:

```text
src/unknown.ts
```

worked values are:

```text
size = 69
SHA-256 =
4380cdb6d3d37750bf5171393d6b80e4e5c8014200456ca0d0fa90da81f534ee

File ID =
next:file:18d43cf6b06e7a48118f54fd24f45c4a10787b7c889175921d49fb4c506c3fac

Module ID =
next:module:730057a88b0f2cce9271853e547c9254003f9bfdecfd13bda6a94dd5699e4d01

router-context Fact ID =
next:fact:06e72bd5602dee3eb8552c16edb45e1a2de4d4bfa4a99dd9f007833308e23bcc
```

The export item spans:

```text
36..65
```

with token identity:

```text
b42bd21b4f85750eeb5ef2916f3c65cff232b66a218983e75dd4ead411cc3c27
```

The bytes provide neither:

```text
positive Component evidence
nor
primitive-const evidence
```

so the only independently supportable result is:

```text
resolution = unknown
resolution_basis = open_world
disposition = export_failure
```

For no explicit selected target, after valid proof and model-record budget:

```text
CSV-NEXT-EXPORT-001
payload_unavailable
```

For an explicit target containing this export:

```text
TARGET-001
reason = unsupported_export
```

must win earlier.

---

# Part III — Required export negatives

## 24. Coordinated observation/binding omission

Starting from the full positive corpus:

1. remove the direct Button export observation;
2. remove the corresponding Button ExportBinding;
3. remove the matching resolution witness;
4. repair model counts;
5. repair model digest.

Do not change sealed source bytes.

Transport remains admissible.

The v3 Core must independently rescan:

```text
src/button.tsx
```

derive the missing export, and reject the coordinated omission.

Expected class:

```text
CSV-NEXT-PROTOCOL-001
reason = model_proof
```

Do not allow mutually consistent submitted omission to erase frozen source syntax.

---

## 25. Changed source bytes with stale witness

Create a second real acquisition whose `src/index.ts` contains:

```text
export { Button as Secondary } from "./button";
```

Build the new:

```text
seal
request
response/control
transport candidate
```

normally from that changed source.

Then submit the old `Primary`:

```text
export_observation
re-export witness
ExportBinding
```

with internally repaired model digest/counts.

The v3 Core must rescan the changed seal and derive `Secondary`.

The stale `Primary` evidence is rejected.

Do not mutate an existing seal to manufacture this case.

This specifically proves:

```text
export witness identity is bound to actual frozen source bytes,
not merely Module path or record IDs.
```

---

## 26. Re-export witness mutation

From the positive `Primary` case, independently mutate one of:

```text
resolved_source_module_id
expanded_exported_name
target_declaration_id
resolution
syntax_identity
byte_start
byte_end
```

while keeping other submitted structures self-consistent where possible.

The source-derived `case` + `recompute_export_graph_case()` result must still win.

---

# Part IV — Full Core validation

## 27. Proposed implementation modules

Create:

```text
tests/contracts/next_semantic_core_v3_reference.py
tests/contracts/next_semantic_core_v3_validation.py
tests/contracts/test_next_semantic_core_v3.py
```

These paths are proposed; they do not currently exist.

### Reference module

Proposed API:

```python
@dataclass(frozen=True, slots=True, init=False)
class ValidatedSemanticDecisionV3: ...

@dataclass(frozen=True, slots=True, init=False)
class RejectedSemanticDecisionV3: ...

def compatibility_descriptor_v3(
    candidate: ValidatedTransportCandidateV2,
) -> dict[str, Any]: ...

def decide_semantic_candidate_v3(
    candidate: ValidatedTransportCandidateV2,
    seal: SourceAcquisitionSeal,
    assets: RetainedExecutionAssets,
) -> ValidatedSemanticDecisionV3: ...

def inspect_semantic_candidate_v3(
    candidate: ValidatedTransportCandidateV2,
    seal: SourceAcquisitionSeal,
    assets: RetainedExecutionAssets,
) -> ValidatedSemanticDecisionV3 | RejectedSemanticDecisionV3: ...
```

### Validation module

In addition to the export helpers above:

```python
class SemanticCandidateInvalidErrorV3(ValueError):
    reason: str

def resolve_full_core_view_v3(...) -> FullResolvedViewV3: ...
def validate_full_model_semantics_v3(...) -> int: ...
def validate_full_proof_v3(...) -> ...: ...
def derive_post_acquisition_locality_v3(...) -> ...: ...
def validate_selected_cardinality_exception_v3(...) -> ...: ...
def compatibility_preimage_v3(...) -> dict[str, Any]: ...
def validate_compatibility_descriptor_v3(...) -> None: ...

def validate_semantic_candidate_v3(...) -> CoreValidationResultV3: ...
def validate_semantic_decision_v3(...) -> None: ...
def validate_rejected_semantic_decision_v3(...) -> None: ...
```

The helper/result dataclasses may remain module-internal.

---

## 28. Full D

Use `resolve_discovered_v3()` as the source-owner/identity starting point.

Build a collection-indexed full D containing:

```text
Projects: acquired full membership
Files: acquired parent File records
Modules: public + proof-only
Components: public + proof-only
Members: public + proof-only
Relations: public + proof-only
Facts: public + proof-only
```

Do not derive D from M.

For Project/File rows, continue requiring absence of child `record` payload.

All acquired Project/File IDs must occur exactly once.

---

## 29. Full semantic/type validation

Build a validation-only model from full D and apply the unchanged semantic grammar.

`validate_model()` may be reused for wire-independent model semantics, but do not let its normal `max_model_records` check perform SI-04's stage-5 routing prematurely.

Use an existing wider structural cap for the validation-only call, then perform actual:

```text
request.limits.max_model_records
```

routing at stage 5.

This full semantic check covers:

```text
Project identity/config/path
File roles/path/project ownership
Module owner/router/client/derived roles
Component ownership/declaration
member semantics
full PropsTypeIR grammar
type parameter scope
depth/node/property/union/intersection/signature limits
relations
facts
boundary-role derivation
diagnostics shape
coverage structural invariants
```

SI-03's local Props reference walker remains useful for D/M reference closure, but it is not a substitute for `_validate_type_node()`.

---

## 30. Mandatory seeds and exact causal graph

Submitted seeds and edges are evidence, not authority.

Convert resolved D into the shape required by the existing wire-independent proof algorithms.

Require:

```python
proof["causal_edges"] == derive_required_causal_edges(proof, resolved_by_collection)
```

and require:

```python
_derived_taint_fixed_point(proof, resolved_by_collection)
```

to equal the exact submitted taint sets.

This closes:

```text
missing mandatory seed
extra seed
wrong root-origin edge
missing transitive edge
extra causal edge
wrong edge rule
missing taint
extra taint
wrong typed taint
```

No reverse Module→File or File→Project taint is added.

---

# Part V — Locality

## 31. Do not reuse `SourceFailureLedger` for post-acquisition roots

Existing `SourceFailureLedger.__post_init__()` requires:

```text
failures == source_seal.source_view["read_failures"]
```

The production complete `SourceAcquisitionSeal` forbids acquisition failures.

SI-04:

```text
parse_file
read_file
```

roots are observations made **after successful acquisition of the frozen bytes**.

Therefore SI-04 must not:

- put them into `source_view.read_failures`;
- mutate the seal;
- instantiate an artificial legacy ledger;
- construct a fake acquisition failure certificate.

---

## 32. v3-local same-seal locality

Implement:

```python
derive_post_acquisition_locality_v3(...)
```

inside the new validation module.

Inputs:

```text
actual SourceAcquisitionSeal
fully validated post-acquisition File roots
request targets
validated full D / partition
```

Read the sealed graph only from:

```python
seal.final_plan["source_graph"]
```

and verify its identity back to the same seal/source files.

Preserve the accepted old wire-independent locality meaning:

- failed File graph node is the start;
- forward closure follows dependencies;
- reverse closure includes importers that can reach the failed node;
- an open dependency intersecting the affected region prevents isolation;
- `module_plane` uncertainty is conservative;
- explicit target intersection with affected closure means target-tainted;
- caller-provided `isolated` booleans are never accepted.

Result is internal:

```text
localized
nonlocal
```

Routing:

```text
localized semantic File failure
→ partial_safe may remain available

nonlocal
→ CSV-NEXT-SOURCE-003
→ payload unavailable
```

No new public code/state is added.

---

# Part VI — selected cardinality exception

## 33. Keep normal SI-03 seam strict

Normal available Core path must still call:

```python
retain_source_inventory_seam_v3(...)
```

after full proof validation.

It must therefore continue requiring:

```text
one canonical Module per acquired program File
```

No missing/duplicate Module enters an available normal seam.

---

## 34. Dedicated no-payload selected exception

Before normal seam admission, detect the narrow selected cardinality cases using the existing target semantics.

Permitted cases remain:

```text
missing
component_only
byte-identical duplicate
```

Only selected program Files may use them.

Create a v3-specific exceptional proof validator that still validates:

```text
all acquired source discovery
all unrelated semantic records
record identity
full references
full type grammar
mandatory roots
causal exactness
taint fixed point
export witnesses
target witness
all unrelated Module owners
```

The old `_target_missing_module_exceptions()` and
`_target_duplicate_module_exceptions()` may supply the narrow exception sets.

Do not call old `_validate_target_exception_proof_base()` as the v3 certificate because it resolves Project/File discovery through old public-model assumptions.

A successful exceptional result is:

```text
ValidatedSemanticDecisionV3
gate = TARGET-001
payload_available = false
source_inventory_seam = None
compatibility-v3 retained
entity measurement = null
```

Do not produce an available source partition for the exceptional candidate.

---

# Part VII — target, selection and outcome ordering

## 35. Target validation

Normal target resolution must be based on a full validation view plus independently derived unavailable IDs, not merely M.

This lets a selected acquired-but-excluded File become:

```text
selected_taint
```

instead of being misreported as `missing`.

After source/export evidence is validated:

```text
proven selected target failure
→ CSV-NEXT-TARGET-001
→ no payload
```

before model-record routing.

---

## 36. Selection-only behavior

Preserve:

```text
not_selected
target_excluded
represented unsupported frontier
```

as legitimate exclusions when independently witnessed.

They do not by themselves lower complete → partial_safe.

Do not classify legal selection-only exclusion as arbitrary omission.

Full-D exports are still validated even when their owner is selection-excluded; they simply do not become public success.

---

# Part VIII — budgets and outcomes

## 37. Model-record count

Reuse the wire-independent counting meaning of:

```python
response_model_record_counts(...)
```

Actual accounted records are:

```text
published model records
+
proof-only discovered records
```

Payload-free source discovery rows count once.

Required actual tests:

```text
10,000
10,001
```

Do not lower `max_model_records` to a small stand-in.

Proof validation occurs before this gate.

Therefore:

```text
malformed proof + 10,001
```

must be a protocol invariant rejection, not LIMIT-005.

---

## 38. Export and nonlocal source routing

Only after valid proof and valid 10,000-or-less model-record count:

```text
selected target failure   [already handled earlier]
↓
record budget
↓
export unavailable
or
source nonlocal
↓
entity gate
```

Unknown unselected string export:

```text
CSV-NEXT-EXPORT-001
```

Nonlocal File failure:

```text
CSV-NEXT-SOURCE-003
```

Both have no entity-budget measurement because the entity gate is not reached.

---

## 39. Entity gate

Measure:

```text
len(public safe Modules) + len(public Components)
```

not acquired Modules.

Reuse `entity_budget_gate()` only after deriving the pre-budget semantic outcome.

`partial_safe` must never become `complete`.

Entity +1 remains:

```text
CSV-NEXT-LIMIT-005
payload_unavailable
```

with actual entity measurement.

---

# Part IX — compatibility-v3

## 40. Minimal internal compatibility projection

SI-04 needs an immutable parent-owned compatibility descriptor inside the Core owner.

It does **not** need the SI-05 physical schema.

Exact keys:

```text
schema
semantic_schema
identity_versions
algorithm_versions
semantic_profile_id
unicode_profile
runtime_binding_profile_id
typescript_identity
trusted_type_environment_digest
portable_toolchain_fingerprint
semantic_admission_profile_id
compatibility_id
```

Exact ten-key hash preimage:

```text
semantic_schema
identity_versions
algorithm_versions
semantic_profile_id
unicode_profile
runtime_binding_profile_id
typescript_identity
trusted_type_environment_digest
portable_toolchain_fingerprint
semantic_admission_profile_id
```

Fixed identities:

```text
schema =
code-structure-viz.next-semantic-compatibility/v3

semantic_schema =
code-structure-viz.semantic/v3

semantic_profile_id =
next-trusted-profile-v1

semantic_admission_profile_id =
next-source-inventory-safe-subset-v1

typescript_identity =
typescript-5.9.2
```

Use unchanged semantic profile metadata and the same candidate's runtime binding.

Do not cast `compatibility_descriptor_v2()`.

Do not add:

```text
schemas/next-compatibility-v3.schema.json
```

in SI-04.

That schema and all public consumers remain SI-05.

---

## 41. Compatibility KAT

Before implementing `compatibility_descriptor_v3()`, materialize its ten-key fixture preimage as a literal JSON object in the test.

Compute its expected SHA outside the new producer/validator, for example:

```bash
jq -cS . /tmp/si04-compatibility-preimage.json \
  | tr -d '\n' \
  | shasum -a 256
```

The test then asserts:

```text
derived preimage == literal preimage
compatibility_id == literal SHA-256
```

Do not ask the new producer to generate its own expected hash.

---

# Part X — immutable owners

## 42. `ValidatedSemanticDecisionV3`

The proposed immutable owner holds:

```text
same ValidatedTransportCandidateV2
same SourceAcquisitionSeal
same RetainedExecutionAssets

validated gate bytes
compatibility-v3 bytes
Core measurement bytes
locality evidence bytes where applicable
ValidatedSourceInventorySeamV3 for normal path
```

Normal complete/partial-safe paths require the retained SI-03 seam.

Target-cardinality exceptional no-payload path may have:

```text
source_inventory_seam = None
```

because minting the normal seam would require weakening `full_module_owners_v3()`.

Fresh getters must not expose mutable aliases.

---

## 43. `RejectedSemanticDecisionV3`

Only expected invariant/record-cap failures become a rejected Core owner.

Closed protocol rejection:

```json
{
  "stage": "response_validation",
  "diagnostic_code": "CSV-NEXT-PROTOCOL-001",
  "reason": "<closed v3 rejection label>",
  "model_records": null
}
```

Record +1:

```json
{
  "stage": "model_validation",
  "diagnostic_code": "CSV-NEXT-LIMIT-005",
  "reason": "max_model_records",
  "model_records": 10001
}
```

Allowed invariant labels remain:

```text
file_correspondence
project_correspondence
proof_source_owner
proof_module_owner
proof_references
model_proof
source_inventory_partition
```

Do not add a new public label for export-witness mismatch; it is `model_proof`.

Unexpected owner/internal errors escape. Do not relabel them as child protocol failures.

---

# Part XI — vertical TDD

## 44. Cycle 1 must start from a coherent positive fixture

Do not use the existing minimal SI-03 synthetic corpus as the full-Core positive.

The first test must construct the six-file literal corpus above and, **before invoking the proposed Core factory**, verify with existing lower owners that:

```text
adapter version == 0.2.0
request/seal/assets ownership is valid
ValidatedTransportCandidateV2 exists
retain_source_inventory_seam_v3(...) succeeds
normal one-Module-per-program-File ownership holds
all three Modules have router-context facts
Button Component ID is the worked literal
both ExportBinding IDs are the worked literals
source hashes are the worked literals
coverage/count arrays are internally coherent
```

Do not top-level-import the missing new Core module before these assertions if doing so would prevent the fixture checks from executing.

An intended first Red can be:

```text
coherent lower fixture passes
then proposed Core module/factory is absent
```

A malformed fixture is not Red evidence.

---

## 45. Required Red → minimum Green order

Implement one behavior at a time.

| Cycle | Behavior |
|---:|---|
| 1 | coherent six-file source-bound normal Core positive |
| 2 | direct Button export observation/binding coordinated omission rejected |
| 3 | changed `Primary→Secondary` source bytes with stale witness rejected |
| 4 | re-export witness mutation rejected |
| 5 | primitive string export stays complete + `UNSUPPORTED-001` |
| 6 | unknown string export routes EXPORT-001 |
| 7 | complete PropsTypeIR grammar/depth/scope negative |
| 8 | missing mandatory root seed rejected |
| 9 | extra/missing/wrong causal edge rejected |
| 10 | extra/missing/wrong typed taint rejected |
| 11 | actual frozen-source `parse_file` localized partial-safe |
| 12 | post-acquisition `read_file` localized without legacy acquisition ledger |
| 13 | resolved importer contaminates dependent target |
| 14 | actual source `module_plane` open dependency routes SOURCE-003 |
| 15 | `module_relation` owner failure with untainted File |
| 16 | `export_binding` owner failure with untainted File |
| 17 | `boundary_derivation` owner failure with untainted File |
| 18 | all Files proof-only, Project empty membership |
| 19 | multi-Project safe side remains public |
| 20 | legitimate `not_selected` complete |
| 21 | legitimate `target_excluded` complete |
| 22 | selected missing Module → TARGET-001 after complete exceptional proof |
| 23 | selected component-only → TARGET-001 |
| 24 | selected byte-identical duplicate → TARGET-001 |
| 25 | non-selected missing/inconsistent duplicate rejected |
| 26 | malformed proof cannot hide behind TARGET-001 |
| 27 | actual 10,000 accounted records accepted |
| 28 | actual 10,001 rejected with measured 10001 |
| 29 | malformed proof + 10,001 rejects proof first |
| 30 | entity exact/+1 and partial-safe preservation |
| 31 | compatibility-v3 literal KAT / owner rebinding negative |
| 32 | rejection immutability / privacy / closed reason |
| 33 | P01–P07 and N01–N15 Core matrix completion sweep |

Do not author all 33 tests horizontally before implementing behavior 1.

---

# Part XII — SI obligation mapping

## 46. Positive acceptance

| ID | Full Core evidence |
|---|---|
| SI-P01 | actual seal graph, parse root, exact seeds/FP, independent safe File, localized partial-safe |
| SI-P02 | post-acquisition read root on complete seal, no fake acquisition failure |
| SI-P03 | selected failed/excluded structure → TARGET-001 after complete proof |
| SI-P04 | all Files proof-only, Project empty, multi-Project safe side preserved |
| SI-P05 | complete-empty/nonprogram/selection-only/intentional unsupported complete |
| SI-P06 | independently validated partition/count + actual 10000/10001 |
| SI-P07 | three nonFile roots, untainted File / tainted Module, independent safe target |

## 47. Negative acceptance

| ID | Required rejection |
|---|---|
| N01 | missing acquired source discovery |
| N02 | duplicate discovery/disposition |
| N03 | fake Project/File metadata |
| N04 | Project/File proof `record` payload/null |
| N05 | seed/causal/taint incompleteness or extra |
| N06 | arbitrary safe File/Module omission |
| N07 | proof-only record budget bypass |
| N08 | private dangling/public proof-only refs, including nested Props refs |
| N09 | selected failure downgraded to partial-safe |
| N10 | safe subset used as false full inventory |
| N11 | source reader prefix promoted to Core |
| N12 | cross-project membership / Project loss |
| N13 | Module on nonprogram File |
| N14 | locality forgery / resolved dependency/open dependency omitted |
| N15 | forged owner cause, hidden Module missing/duplicate, fake File taint/root |

The corrected export negatives are part of `N05/N06/N08` and `model_proof` integrity, even though they are not given a new SI-N number.

---

# Part XIII — verification commands

## 48. Unit-focused commands

These commands are prescribed for the implementer; they have not been executed by this brief author.

Use the caller-required locked dev environment:

```bash
uv run --locked --group dev pytest \
  tests/contracts/test_next_semantic_core_v3.py \
  -q
```

Individual vertical cycle example:

```bash
uv run --locked --group dev pytest \
  tests/contracts/test_next_semantic_core_v3.py::test_v3_core_accepts_same_seal_source_bound_export_corpus \
  -q
```

Export-specific cycle:

```bash
uv run --locked --group dev pytest \
  tests/contracts/test_next_semantic_core_v3.py \
  -q -k export
```

Locality:

```bash
uv run --locked --group dev pytest \
  tests/contracts/test_next_semantic_core_v3.py \
  -q -k locality
```

Budgets:

```bash
uv run --locked --group dev pytest \
  tests/contracts/test_next_semantic_core_v3.py \
  -q -k '10000 or 10001 or entity_budget'
```

---

## 49. Direct affected regression modules

Run:

```bash
uv run --locked --group dev pytest \
  tests/contracts/test_next_source_inventory_v3.py \
  tests/contracts/test_next_semantic_candidate_v2.py \
  tests/contracts/test_next_core_failure_v2.py \
  tests/contracts/test_next_request_frame_v2.py \
  tests/contracts/test_next_exchange_v2.py \
  -q
```

This confirms the new Core did not weaken SI-03 or old v2 lower/failure guards.

---

## 50. Targeted shared-algorithm regression

Because SI-04 reuses old scanner/graph/type/target/budget primitives, select the affected old tests explicitly rather than running all `tests/contracts` as an SI-04 requirement.

Run:

```bash
uv run --locked --group dev pytest \
  tests/contracts/test_next_contracts.py \
  -q \
  -k 'export_resolution_witness_uses_complete_source_census_and_coverage_only_rows \
      or export_scanner_closes_unicode_bom_crlf_comments_and_reexport_forms \
      or reexport_graph_recomputes_alias_star_cycle_and_conflict_witnesses \
      or main_reexport_witness_comes_from_raw_declarations_and_edges \
      or round13_reexport_join_is_bijective_for_aliases_and_repeated_forms \
      or actual_string_export_disposition_reaches_every_public_surface \
      or actual_string_export_rejects_coordinated_proof_mutations \
      or string_export_scanner_keeps_raw_span_and_decoded_name_digest \
      or target_failure_validates_complete_proof_before_typed_routing \
      or entity_and_record_budgets_use_distinct_non_allocating_counters \
      or schema_valid_model_record_limit_is_reachable_on_generated_wire \
      or entity_budget_gate_preserves_partial_safe_and_overrun_is_unavailable \
      or props_ir_limits_and_canonical_rules_are_reference_enforced \
      or round21_source_graph_scanner_closes_supported_import_planes_and_open_edges \
      or round20_source_graph_is_derived_from_frozen_bytes_not_reader_injection \
      or round23_rg_18_current_schema_and_history_contract_are_explicit'
```

If an actual shared helper is modified despite the proposed three-new-file design, broaden the regression according to the demonstrated affected surface.

Do not make:

```bash
pytest tests/contracts
```

an SI-04 completion requirement merely because it is broad. Current Plan reserves the whole contract/full gate for later A02/SI-07 closure.

---

## 51. Old domain goldens

Run explicitly:

```bash
uv run --locked --group dev pytest \
  tests/contracts/test_python_goldens.py \
  tests/contracts/test_sqlalchemy_goldens.py \
  -q
```

Their bytes must remain unchanged.

---

## 52. Static checks

```bash
uv run --locked --group dev ruff check .
uv run --locked --group dev ruff format --check .
uv run --locked --group dev mypy src tests
```

No dependency changes.

---

## 53. SpecDock checks

Repository-local `.agents/skills/spec-dock/SKILL.md` requires current CLI help to be inspected immediately before command use.

Read:

```bash
python3 ./spec-dock/scripts/spec-dock --help
python3 ./spec-dock/scripts/spec-dock sync --help
python3 ./spec-dock/scripts/spec-dock validate --help
```

Then use the caller-prescribed local-only sync:

```bash
python3 ./spec-dock/scripts/spec-dock sync \
  --no-github \
  --no-update-active

python3 ./spec-dock/scripts/spec-dock validate
```

And:

```bash
git diff --check
```

Do not infer Issue/A02 completion from these checks.

---

# Part XIV — evidence and publication

## 54. Product-code boundary

Normal Core implementation paths are:

```text
tests/contracts/next_semantic_core_v3_reference.py
tests/contracts/next_semantic_core_v3_validation.py
tests/contracts/test_next_semantic_core_v3.py
```

Do not change:

```text
src/
schemas/
pyproject.toml
uv.lock
old v1/v2 reference code
old v1/v2 KATs
old export fixture files
Python/SQLAlchemy goldens
SI-03 source-inventory semantics
```

If changing one of these becomes necessary for correctness, apply the stop-condition section rather than silently expanding scope.

---

## 55. Durable progress evidence

The three Core files are the implementation boundary, not a prohibition on repository evidence.

If the authorized workflow persists:

```text
authoring result
TDD evidence
local validation evidence
Strict review raw result
review certificate
limited Plan/Report status
```

use SpecDock commands and current help, consistent with `.agents/skills/spec-dock/SKILL.md`.

Do not hand-edit managed SpecDock metadata as a command fallback.

Evidence Artifacts remain evidence, not new authority.

---

# Part XV — Git checkpoint procedure

## 56. Preconditions

Original unit base stays:

```bash
BASE=caf38329826ae34f8e3cb330b83b97e0357b7dc5
BRANCH=iss-00008-generate-nextjs-component-snapshots
```

Before publication verify:

```bash
git status --short
git branch --show-current
git rev-parse HEAD
git config --get "branch.${BRANCH}.remote"
git config --get "branch.${BRANCH}.merge"
```

Require:

```text
current branch == iss-00008-generate-nextjs-component-snapshots
configured remote == origin
configured merge ref == refs/heads/iss-00008-generate-nextjs-component-snapshots
```

Do not create a new checkout.

---

## 57. Explicit staging

For the Core implementation:

```bash
git add -- \
  tests/contracts/next_semantic_core_v3_reference.py \
  tests/contracts/next_semantic_core_v3_validation.py \
  tests/contracts/test_next_semantic_core_v3.py
```

If authorized SpecDock evidence/Plan/Report paths were created, add those explicit paths in the same manner.

Never use:

```text
git add .
git add -A
```

as the staging route.

---

## 58. Read the full staged diff

Before commit:

```bash
git diff --cached --check
git diff --cached --
```

The **entire staged diff must be read**, not only `--stat` or filenames.

Also inspect:

```bash
git status --short
```

Confirm no unrelated staged path exists.

---

## 59. Commit

Use the installed current-host commit workflow exactly as prescribed by the caller:

```bash
commit-codex -a
```

Do not substitute a generic manual `git commit`.

Do not bypass hooks.

No history rewrite.

---

## 60. Push

Reverify configured origin/branch, then perform explicit non-force push to the verified current branch:

```bash
git push origin \
  HEAD:refs/heads/iss-00008-generate-nextjs-component-snapshots
```

Do not use bare `git push` as a fallback.

Do not use:

```text
--force
--force-with-lease
```

After push:

```bash
git rev-parse HEAD
git status --short
```

and independently compare local/upstream/live full SHA in the normal workflow.

---

# Part XVI — Code Review Strict

## 61. Review identity

Every SI-04 cumulative review uses the unchanged original unit base:

```text
repository:
chemitaro/code-structure-viz

branch:
iss-00008-generate-nextjs-component-snapshots

base:
caf38329826ae34f8e3cb330b83b97e0357b7dc5

head:
current pushed cumulative SI-04 candidate
```

Required review target:

```text
GPT-5.6 Sol / Extra High
fresh Code Review Strict
```

This is separate from the author lane.

The Strict wrapper must independently verify the branch/full SHA through GitHub connector.

No prior SI-03 review pass substitutes for SI-04 review.

---

## 62. Failed review handling

If a semantic Code Review Strict result fails:

1. preserve the raw result;
2. do not let the author directly reinterpret it as permission to patch;
3. send it through a separate findings-analyst lane;
4. determine whether each finding is valid under Current authority;
5. remediate only validated in-scope findings;
6. publish additive fix commits;
7. rerun cumulative review from the same `caf3832` base.

No subagents.

No Browser Use/CUA progress monitoring.

---

# Part XVII — stop conditions

## 63. Stop rather than redesign when any of these becomes necessary

| Required change discovered | Action |
|---|---|
| use old `load_export_*` fixture as v3 source witness | stop implementation path and correct locally |
| monkeypatch old export helpers/fixtures | stop |
| infer `value` solely from missing Component | stop |
| fabricate TypeChecker evidence | stop |
| skip unknown export validation with empty observations | stop |
| mutate complete source seal to add post-acquisition read failure | stop |
| reuse `SourceFailureLedger` by pretending post-acquisition root is acquisition failure | stop |
| reverse Module→File taint | authority conflict |
| File→Project taint | authority conflict |
| remove File mandatory seed | authority conflict |
| child-provided File/Project metadata becomes authority | authority conflict |
| weaken `full_module_owners_v3()` normal path | authority conflict |
| make selected exception produce available partition success | authority conflict |
| create new rejection label/code/state | human/spec decision |
| require public compatibility-v3 schema | SI-05 boundary |
| require public semantic/provenance/run consumer | SI-05 boundary |
| require production TypeScript | A04 boundary |
| require dependency/lock changes | stop |
| require new ASSET policy | separate human decision |
| rewrite old fixtures/KAT/goldens | stop |

An unsupported reference-corpus source form is not permission to invent a TypeChecker result. Either provide a closed independent reference witness under current semantics or stop that test case.

---

# Part XVIII — completion conditions

## 64. SI-04 is complete only when the same pushed candidate establishes all of the following

1. `ValidatedSemanticDecisionV3` exists as an immutable same-owner Core authority.
2. `RejectedSemanticDecisionV3` exists with closed failure metadata.
3. adapter `0.2.0` is bound through retained assets → request → response control → candidate.
4. old `0.1.0` KATs remain unchanged.
5. full D reconstructs all acquired Project/File records from the parent request.
6. all proof-only semantic records are present and structurally validated.
7. full PropsTypeIR grammar, canonicality, scope and limits are validated.
8. private refs close in D and public refs close in M.
9. every acquired program File has one normal Module owner on the normal path.
10. Module eligibility is independent of submitted model absence.
11. exact mandatory root seeds are independently rederived.
12. exact causal edges are independently rederived.
13. typed least-fixed-point taint equals submitted typed taints.
14. no reverse Module→File or File→Project taint is introduced.
15. export syntax is scanned from same-seal frozen bytes, not legacy export fixtures.
16. the old fixture-bound `expected_export_*` façade is not used as v3 oracle.
17. direct component/type/primitive-value resolution uses positive evidence only.
18. absent Component is never treated as proof of a value export.
19. re-export graph closure comes from v3-derived direct tables/edges passed to `recompute_export_graph_case()`.
20. submitted observations and re-export witnesses equal the source-derived evidence.
21. public ExportBindings equal the independently projected public-M set.
22. coordinated observation/binding omission is rejected.
23. changed frozen bytes with stale witness are rejected.
24. proof-only exports remain validated privately but do not count as public success.
25. the primitive string-export corpus remains `complete` with existing `UNSUPPORTED-001`.
26. the unknown string-export corpus routes to EXPORT-001 when unselected.
27. selected unsupported export routes to TARGET-001 first.
28. same-seal post-acquisition locality is derived without legacy acquisition-failure forgery.
29. resolved dependency and open dependency cases are fail-closed.
30. SI-P01 through SI-P07 pass at full Core level.
31. SI-N01 through SI-N15 pass at full Core level.
32. missing/component-only/byte-identical duplicate target exceptions are no-payload-only.
33. normal SI-03 Module-owner admission remains strict.
34. invalid proof wins over target/record-budget routing.
35. actual 10,000 accounted records pass.
36. actual 10,001 records produce measured `10001` Core rejection.
37. source/export unavailability occurs after record validation and before entity gate.
38. entity count is actual safe Modules + Components.
39. partial-safe is never upgraded to complete by the entity gate.
40. internal compatibility-v3 has exact ten-key preimage and independent literal KAT.
41. no SI-05 physical public schema/consumer is claimed as certified.
42. old SI-03/v2 Core failure/request/exchange guards remain green.
43. affected old export/type/source/target/budget regressions remain green.
44. Python/SQLAlchemy goldens remain green and byte-unchanged.
45. Ruff check passes.
46. Ruff format check passes.
47. mypy `src tests` passes.
48. SpecDock local sync/validate passes.
49. `git diff --check` passes.
50. no production `src`, dependency, lock, old schema, or old golden rewrite occurs.
51. full staged diff is read before commit.
52. `commit-codex -a` runs with normal hooks.
53. only the verified configured `origin` branch is non-force pushed with explicit ref.
54. fresh cumulative Code Review Strict passes from original base `caf38329826ae34f8e3cb330b83b97e0357b7dc5`.

A successful SI-04 candidate certifies the **full v3 reference Core contract only**.

It does not certify:

```text
SI-05 public/exact refs
SI-06 final publication/diagnostics
whole A02
cumulative A03
actual TypeScript child execution
OS/CLI/package behavior
Issue #8 Final
```
