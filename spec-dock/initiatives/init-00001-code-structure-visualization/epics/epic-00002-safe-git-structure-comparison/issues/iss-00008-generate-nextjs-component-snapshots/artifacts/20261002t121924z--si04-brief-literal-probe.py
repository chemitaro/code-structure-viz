"""Read-only SI-04 brief literal check. No v3 producer/validator or file writes."""
import hashlib
import json

from tests.contracts.next_reference_validation import (
    _scan_export_file,
    join_reexport_observations_to_edges,
    recompute_export_graph_case,
)


def literal_digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


sources = {
    "package.json": (b'{"dependencies":{"next":"15"}}', 30, "e1cba2a2526ff053f2d5931bf33cfc1e9eabf400fe0651ee341cb4dac23e29f4"),
    "tsconfig.json": (b'{"include":["src/**/*"]}', 24, "d22d6c841f113e55b1ad3c0858b78148e6c5196bb88c91b8cd213f22b7524a9b"),
    "src/button.tsx": (b"export function Button() { return null; }\n", 42, "1dc7a2111f31e37e693b6b6befa5c7141411471168e20a2fc93c886382dfb862"),
    "src/index.ts": (b'export { Button as Primary } from "./button";\n', 46, "4a0d75a51f0ffd2f39ab05d7e739e1e6d045bb1e1e7177d34a32a80494592788"),
    "src/value.ts": (b'const value = 1;\nexport { value as "opaque-public-name" };\n', 59, "cd622fd53afb830fdded48bebbd77ac22f2a22da282b34bdf977cb1b3006fadd"),
    "src/global.d.ts": (b"declare interface Window { marker: string; }\n", 45, "434a26e7917f46b586775bc326d6ba34994e183118ffecf96c9caf8e09207643"),
    "src/unknown.ts": (b'const value = makeValue();\nexport { value as "opaque-public-name" };\n', 69, "4380cdb6d3d37750bf5171393d6b80e4e5c8014200456ca0d0fa90da81f534ee"),
}
source_mismatches = []
for path, (content, size, expected_hash) in sources.items():
    actual = (len(content), hashlib.sha256(content).hexdigest())
    if actual != (size, expected_hash):
        source_mismatches.append((path, actual, (size, expected_hash)))

project = "next:project:530b20c858c6039c19737f386f96cfabdadda6b8a0a1c98b5ca639beb2765c25"
modules = {
    "src/button.tsx": "next:module:4130a3bcc0554a01d2f7111d613cdf150e6e3104575fe6a46ee5b057c6414b7d",
    "src/index.ts": "next:module:024a4e0cf9fee9411a055c04c95ff34b0909e69f80b3f4a9dff0cec438c9e4c3",
    "src/value.ts": "next:module:f8a3c82434f22cef3d54190f8a81a7b7788efcbac0cdbec594a7f1b0edbbf16b",
}
files = {
    "package.json": "6e5a491cdd30e69e4cf115a95b99ad11d83beac749f4f20d7fa12cb26d9f7c0c",
    "tsconfig.json": "c891008136a6466799eb75e12e6b6d7b2bdb35587cb8c2f96b3b5a720da870bf",
    "src/button.tsx": "7d940b2adbc319b4843ed7495d2cfce15c2f5f3450ee587273b53f4f8d5ac2b5",
    "src/index.ts": "4d7ea21c5296aea27a6fd1ea2b3ec895bd40dfc5c827e1759e0a401af1ecaf30",
    "src/value.ts": "b2257b187308437ce03e40f7793970289bdb1aa71c5167b7796501cf91efa6ac",
    "src/global.d.ts": "8cb22e35356bd13a3869a5dd8bd680300b8f8ba5bd33bcdbfc7653cc1eba3e76",
}
identities = [
    ("project", "project", {"root": "."}, project),
    *[("file", "file", {"project_id": project, "path": path}, "next:file:" + value) for path, value in files.items()],
    *[("module", "module", {"project_id": project, "path": path}, value) for path, value in modules.items()],
    ("component", "component", {"module_id": modules["src/button.tsx"], "declaration_key": "Button"}, "next:component:56983cafa7d11d2d42ecdca27a9061799006d6154f77cb9e4ee2a954d95659e8"),
    ("export_binding", "member", {"owner_id": modules["src/button.tsx"], "exported_name": "Button", "role": "value"}, "next:member:9a0c2c2d46a1812864d748f99ffa5448f755aa3edcd7894873c291d46c958279"),
    ("export_binding", "member", {"owner_id": modules["src/index.ts"], "exported_name": "Primary", "role": "value"}, "next:member:0f044044b752a86452130d42b130ed1ea2952d101484e73c283db9d84094a1de"),
]
fact_hashes = {
    "src/button.tsx": "fad69b0c4f9499f6b03b9a3ed75bde3416620b9f724cb392ece749b1883ac3b7",
    "src/index.ts": "5af45a15f0cfe0ec35e9c1fe62bea79bf1fefba6968ed6bfa69573c74ca51af0",
    "src/value.ts": "75c153d8a3122c1eec2e9b23b9b93d7c7f237265c7b785b70b1c4c2e892dd8e9",
}
identities.extend(
    ("router_context", "fact", {"kind": "router_context", "owner_id": modules[path], "value": "none"}, "next:fact:" + value)
    for path, value in fact_hashes.items()
)
identity_mismatches = []
for kind, prefix, identity, expected_id in identities:
    actual_id = "next:" + prefix + ":" + literal_digest({"kind": kind, "version": 1, "identity": identity})
    if actual_id != expected_id:
        identity_mismatches.append((kind, actual_id, expected_id))

syntax = {
    path: _scan_export_file(path, sources[path][0])
    for path in ("src/button.tsx", "src/index.ts", "src/value.ts", "src/unknown.ts")
}
syntax_mismatches = []
syntax_expected = {
    "src/button.tsx": (0, 41, "named_export", "c5a8c4d6b89384890dcfa31e00c713bbbc6eb3d5f95f02e204e96b817b271006"),
    "src/index.ts": (9, 26, "reexport", "0629e28100820ed2c813333c1cb6ee468df1cbe8342568cf400c347d27bc7317"),
    "src/value.ts": (26, 55, "string_export", "5c9ef3c2108d37898e837134472acdff79f8da99522c50aa48d053c07b35857f"),
    "src/unknown.ts": (36, 65, "string_export", "b42bd21b4f85750eeb5ef2916f3c65cff232b66a218983e75dd4ead411cc3c27"),
}
for path, expected in syntax_expected.items():
    row = syntax[path][0]
    actual = tuple(row[key] for key in ("byte_start", "byte_end", "syntax_kind", "token_identity"))
    if actual != expected:
        syntax_mismatches.append((path, actual, expected))

edge = {
    "owner_file_path": "src/index.ts", "source_specifier": "./button",
    "imported_name": "Button", "exported_name": "Primary",
    "syntax_identity": "export:src/index.ts:9:26:reexport:Primary",
    "byte_start": 9, "byte_end": 26,
}
joined = join_reexport_observations_to_edges(syntax["src/index.ts"], [edge])
graph = recompute_export_graph_case({
    "modules": [
        {"path": "src/button.tsx", "exports": [{"name": "Button", "resolution": "component", "target_declaration_key": "Button"}]},
        {"path": "src/index.ts", "exports": []},
        {"path": "src/value.ts", "exports": []},
    ],
    "edges": [edge],
})
witness = graph["witnesses"][0]
assert len(joined) == 1
assert {
    key: witness[key] for key in (
        "resolved_source_file_path", "expanded_exported_name",
        "target_declaration_key", "resolution", "diagnostic"
    )
} == {
    "resolved_source_file_path": "src/button.tsx", "expanded_exported_name": "Button",
    "target_declaration_key": "Button", "resolution": "component", "diagnostic": None,
}

relation_identity = {
    "kind": "static_import", "source_id": modules["src/index.ts"],
    "target": {"kind": "internal", "module_id": modules["src/button.tsx"]},
    "role": "value", "reexport": True, "boundary_effect": "none",
}
relation_id = "next:relation:" + literal_digest({"kind": "static_import", "version": 1, "identity": relation_identity})
print(json.dumps({
    "source_literals_checked": len(sources),
    "source_mismatches": source_mismatches,
    "identity_literals_checked": len(identities),
    "identity_mismatches": identity_mismatches,
    "syntax_literals_checked": len(syntax_expected),
    "syntax_mismatches": syntax_mismatches,
    "raw_reexport_join_and_graph": "pass",
    "required_reexport_relation_literal": relation_id,
    "required_relation_preimage": {"kind": "static_import", "version": 1, "identity": relation_identity},
    "corrected_full_positive_counts": {"relations": 1, "published": 17, "discovered": 17, "internal_entities": 4},
}, ensure_ascii=False, indent=2))
if source_mismatches or identity_mismatches or syntax_mismatches:
    raise SystemExit(1)
