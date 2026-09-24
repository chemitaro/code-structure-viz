from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path, PurePosixPath
from typing import cast

import pytest

import code_structure_viz.adapters.next.source_acquisition as source_acquisition
from code_structure_viz.adapters.next.applicability import (
    PackageApplicabilityState,
    derive_package_applicability_matrix,
)
from code_structure_viz.adapters.next.source_acquisition import (
    NextSourceAcquirer,
    NextSourceAcquisitionError,
    NextSourceIntegrityError,
    SourceAcquisitionSeal,
    SourceDiscoveryIntent,
)
from code_structure_viz.source.git_repository import Commit, EnumeratedPath
from code_structure_viz.source.source_view import (
    DescriptorAnchoredSourceReadSession,
    SourceReadFailure,
    SourceReadFailureKind,
    SourceView,
)
from tests.contracts.test_json_schemas import _validator


@dataclass
class MemorySourceReader:
    files: Mapping[str, bytes]
    read_failures: Mapping[str, SourceReadFailureKind] = field(default_factory=dict)
    reads: list[str] = field(default_factory=list)
    enumerations: int = 0
    seal_calls: int = 0

    def enumerate_paths(self) -> tuple[str, ...]:
        self.enumerations += 1
        return tuple(sorted(self.files, key=lambda path: path.encode("utf-8")))

    def read_once(self, path: str) -> bytes:
        self.reads.append(path)
        if path in self.read_failures:
            raise SourceReadFailure(path, self.read_failures[path])
        return self.files[path]

    def seal(self, *, source_graph_digest: str | None = None) -> SourceView:
        self.seal_calls += 1
        raise AssertionError("this memory reader is not expected to seal")


def test_non_applicable_preflight_reads_only_direct_package_bytes_once() -> None:
    reader = MemorySourceReader(
        {
            "package.json": b'{"name":"plain-app"}',
            "tsconfig.json": b'{"compilerOptions":{"jsx":"preserve"}}',
            "src/app/page.tsx": b"export default function Page() { return null; }",
            "types/global.d.ts": b"declare const x: string;",
        }
    )

    result = NextSourceAcquirer(reader).preflight(SourceDiscoveryIntent((".",)))

    assert result.matrix.aggregate_state is PackageApplicabilityState.NON_APPLICABLE
    assert result.matrix.non_applicable_projects == (".",)
    assert reader.reads == ["package.json"]
    assert result.frozen_package_bytes == (("package.json", b'{"name":"plain-app"}'),)


def test_all_non_applicable_acquisition_stops_before_configuration_and_source_seal() -> None:
    reader = MemorySourceReader(
        {
            "package.json": b'{"name":"plain-app"}',
            "tsconfig.json": b"must remain unread",
            "src/app/page.tsx": b"must remain unread",
        }
    )

    result = source_acquisition.seal_source_acquisition(
        SourceDiscoveryIntent((".",)),
        reader,
        trusted_environment_digest="a" * 64,
    )

    assert isinstance(result, source_acquisition.NextNotApplicableAcquisition)
    assert result.package_applicability.non_applicable_projects == (".",)
    assert reader.reads == ["package.json"]
    assert reader.seal_calls == 0


def test_malformed_package_applicability_fails_before_control_reads() -> None:
    reader = MemorySourceReader(
        {
            "package.json": b'{"dependencies":{"next":false}}',
            "tsconfig.json": b"must remain unread",
        }
    )

    with pytest.raises(NextSourceAcquisitionError) as caught:
        source_acquisition.seal_source_acquisition(
            SourceDiscoveryIntent((".",)),
            reader,
            trusted_environment_digest="a" * 64,
        )

    assert caught.value.code == "CSV-NEXT-APPLICABILITY-002"
    assert caught.value.stage == "applicability"
    assert reader.reads == ["package.json"]
    assert reader.seal_calls == 0


@pytest.mark.parametrize(
    ("failure_kind", "code", "stage", "diagnostic_path"),
    [
        (
            SourceReadFailureKind.READ,
            "CSV-NEXT-APPLICABILITY-002",
            "applicability",
            None,
        ),
        (SourceReadFailureKind.TOO_LARGE, "CSV-NEXT-LIMIT-001", "source_read", None),
        (SourceReadFailureKind.MISSING, "CSV-NEXT-SOURCE-003", "source_read", "package.json"),
        (
            SourceReadFailureKind.UNSAFE_PATH,
            "CSV-NEXT-SOURCE-003",
            "source_read",
            "package.json",
        ),
        (
            SourceReadFailureKind.NON_REGULAR,
            "CSV-NEXT-SOURCE-003",
            "source_read",
            "package.json",
        ),
    ],
)
def test_package_read_failure_classification_precedes_other_observations(
    failure_kind: SourceReadFailureKind,
    code: str,
    stage: str,
    diagnostic_path: str | None,
) -> None:
    reader = MemorySourceReader(
        {
            "package.json": b"unreadable",
            "tsconfig.json": b"must remain unread",
            "src/page.tsx": b"must remain unread",
        },
        read_failures={"package.json": failure_kind},
    )

    with pytest.raises(NextSourceAcquisitionError) as caught:
        source_acquisition.seal_source_acquisition(
            SourceDiscoveryIntent((".",)),
            reader,
            trusted_environment_digest="a" * 64,
        )

    assert (caught.value.code, caught.value.stage, caught.value.path) == (
        code,
        stage,
        diagnostic_path,
    )
    assert str(caught.value) == code
    assert reader.reads == ["package.json"]
    assert reader.seal_calls == 0


def test_source_acquisition_seal_cannot_be_constructed_from_injected_plan_and_view() -> None:
    with pytest.raises(TypeError, match="created by seal_source_acquisition"):
        SourceAcquisitionSeal(
            plan_bytes=b"{}",
            plan_digest="a" * 64,
            source_view=SourceView(
                head_commit="b" * 40,
                files=(),
                failures=(),
                fingerprint="c" * 64,
            ),
            source_view_fingerprint="c" * 64,
            seal_id="d" * 64,
            package_applicability=derive_package_applicability_matrix({}, (".",)),
        )


def test_trusted_environment_digest_rejects_non_string_values_as_typed_failure() -> None:
    reader = MemorySourceReader({"package.json": b'{"dependencies":{"next":"15"}}'})

    with pytest.raises(source_acquisition.NextSourceAcquisitionError) as caught:
        source_acquisition.seal_source_acquisition(
            SourceDiscoveryIntent((".",)),
            reader,
            trusted_environment_digest=cast(str, object()),
        )

    assert caught.value.code == "CSV-NEXT-SOURCE-003"
    assert caught.value.stage == "trusted_environment"


def test_sealed_source_graph_resolves_imports_and_plan_matches_closed_schema(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    files = {
        "package.json": b'{"dependencies":{"next":"15"}}',
        "tsconfig.json": b'{"include":["src/**/*"]}',
        "src/App.tsx": (
            b'import { Button } from "./Button";\n'
            b'import React from "react";\n'
            b"export default function App() { return <Button />; }\n"
            b"const Markup = <div>import('./jsx-false')</div>;\n"
        ),
        "src/Button.tsx": b"export const Button = () => null;\n",
    }
    for path, content in files.items():
        target = repository / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    entries = tuple(
        EnumeratedPath(path, PurePosixPath(path))
        for path in sorted(files, key=lambda value: value.encode("utf-8"))
    )
    head = Commit("2" * 40)
    reader = DescriptorAnchoredSourceReadSession(
        repository,
        entries,
        head_state=head,
        current_entries=lambda: entries,
        current_head_state=lambda: head,
        max_files=20_000,
        max_file_bytes=4 * 1024 * 1024,
        max_total_bytes=64 * 1024 * 1024,
    )

    seal = source_acquisition.seal_source_acquisition(
        SourceDiscoveryIntent((".",)),
        reader,
        trusted_environment_digest="e" * 64,
    )
    assert isinstance(seal, SourceAcquisitionSeal)

    _validator("next-source-plan-v1.schema.json").validate(seal.final_plan)
    app_id = source_acquisition._digest({"kind": "source_node", "path": "src/App.tsx"})
    button_id = source_acquisition._digest({"kind": "source_node", "path": "src/Button.tsx"})
    assert {
        (edge["source"], edge["target"]) for edge in seal.final_plan["source_graph"]["edges"]
    } >= {(app_id, button_id)}
    assert any(
        edge["source"] == app_id and edge["target_kind"] == "external_package"
        for edge in seal.final_plan["source_graph"]["open_edges"]
    )
    assert "jsx-false" not in repr(seal.final_plan["source_graph"])


def test_sealed_source_graph_scans_supported_module_forms_and_keeps_uncertainty_open(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    source = b"""\
// import "./comment-false";
const template = `import("./template-false")`;
const regex = /import\\("\\.\\/regex-false"\\)/;
import "./side";
import type { Shape } from "./shape";
export { value } from "./reexport";
const dynamic = import("./dynamic");
const required = require("./required");
import { alias } from "@/alias";
import("./missing");
import("./ambiguous");
import("../private#specifier");
import(name);
"""
    files = {
        "package.json": b'{"dependencies":{"next":"15"}}',
        "tsconfig.json": (
            b'{"include":["src/**/*.ts"],"compilerOptions":'
            b'{"baseUrl":".","paths":{"@/*":["src/*"]}}}'
        ),
        "src/entry.ts": source,
        "src/side.ts": b"export const side = 1;",
        "src/shape.ts": b"export interface Shape { value: string; }",
        "src/reexport.ts": b"export const value = 1;",
        "src/dynamic.ts": b"export const dynamic = 1;",
        "src/required.ts": b"export const required = 1;",
        "src/alias.ts": b"export const alias = 1;",
        "src/ambiguous.ts": b"export const ambiguous = 1;",
        "src/ambiguous/index.ts": b"export const ambiguous = 2;",
    }
    for path, content in files.items():
        target = repository / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    entries = tuple(
        EnumeratedPath(path, PurePosixPath(path))
        for path in sorted(files, key=lambda value: value.encode("utf-8"))
    )
    head = Commit("3" * 40)
    reader = DescriptorAnchoredSourceReadSession(
        repository,
        entries,
        head_state=head,
        current_entries=lambda: entries,
        current_head_state=lambda: head,
        max_files=20_000,
        max_file_bytes=4 * 1024 * 1024,
        max_total_bytes=64 * 1024 * 1024,
    )

    seal = source_acquisition.seal_source_acquisition(
        SourceDiscoveryIntent((".",)),
        reader,
        trusted_environment_digest="f" * 64,
    )
    assert isinstance(seal, SourceAcquisitionSeal)
    _validator("next-source-plan-v1.schema.json").validate(seal.final_plan)
    graph = seal.final_plan["source_graph"]
    entry_id = source_acquisition._digest({"kind": "source_node", "path": "src/entry.ts"})
    targets = {
        source_acquisition._digest({"kind": "source_node", "path": path})
        for path in (
            "src/side.ts",
            "src/shape.ts",
            "src/reexport.ts",
            "src/dynamic.ts",
            "src/required.ts",
            "src/alias.ts",
        )
    }
    resolved = {edge["target"] for edge in graph["edges"] if edge["source"] == entry_id}
    assert resolved >= targets
    shape_edge = next(
        edge
        for edge in graph["edges"]
        if edge["source"] == entry_id
        and edge["target"]
        == source_acquisition._digest({"kind": "source_node", "path": "src/shape.ts"})
    )
    assert shape_edge["role"] == "type"
    open_edges = [edge for edge in graph["open_edges"] if edge["source"] == entry_id]
    assert any(edge["reason"] == "unsupported" for edge in open_edges)
    assert any(
        edge.get("target_kind") == "ambiguous" or edge["reason"] == "ambiguous"
        for edge in open_edges
    )
    assert "comment-false" not in repr(graph)
    assert "template-false" not in repr(graph)
    assert "regex-false" not in repr(graph)
    assert "private#specifier" not in repr(graph)


def test_config_inheritance_retains_origins_through_actual_source_seal(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    files = {
        "apps/web/package.json": b'{"dependencies":{"next":"15"}}',
        "apps/web/tsconfig.json": b'{"extends":"./config/base.json"}',
        "apps/web/config/base.json": (
            b'{"include":["src/**/*"],"exclude":["src/generated/**/*"],'
            b'"compilerOptions":{"paths":{"@/*":["src/*"]}}}'
        ),
        "apps/web/Page.tsx": b"must not be selected",
        "apps/web/config/src/Page.tsx": (
            b'import { Widget } from "@/Widget"; export default Widget;'
        ),
        "apps/web/config/src/Widget.tsx": b"export const Widget = () => null;",
        "apps/web/config/src/generated/Skip.tsx": b"must be excluded",
    }
    for path, content in files.items():
        target = repository / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    entries = tuple(
        EnumeratedPath(path, PurePosixPath(path))
        for path in sorted(files, key=lambda value: value.encode("utf-8"))
    )
    head = Commit("6" * 40)
    reader = DescriptorAnchoredSourceReadSession(
        repository,
        entries,
        head_state=head,
        current_entries=lambda: entries,
        current_head_state=lambda: head,
        max_files=20_000,
        max_file_bytes=4 * 1024 * 1024,
        max_total_bytes=64 * 1024 * 1024,
    )

    seal = source_acquisition.seal_source_acquisition(
        SourceDiscoveryIntent(("apps/web",)),
        reader,
        trusted_environment_digest="6" * 64,
    )
    assert isinstance(seal, SourceAcquisitionSeal)
    _validator("next-source-plan-v1.schema.json").validate(seal.final_plan)
    assert seal.final_plan["local_extends"] == [
        {
            "project_root": "apps/web",
            "config_path": "apps/web/tsconfig.json",
            "extends": ["apps/web/config/base.json"],
        }
    ]
    assert seal.final_plan["config_resolution"][0]["declaring_paths"] == [
        {"option": "exclude", "path": "apps/web/config/base.json"},
        {"option": "include", "path": "apps/web/config/base.json"},
        {"option": "paths", "path": "apps/web/config/base.json"},
    ]
    selected_paths = {row["path"] for row in seal.final_plan["file_role_map"]}
    assert "apps/web/config/src/Page.tsx" in selected_paths
    assert "apps/web/config/src/Widget.tsx" in selected_paths
    assert "apps/web/Page.tsx" not in selected_paths
    assert "apps/web/config/src/generated/Skip.tsx" not in selected_paths
    page_id = source_acquisition._digest(
        {"kind": "source_node", "path": "apps/web/config/src/Page.tsx"}
    )
    widget_id = source_acquisition._digest(
        {"kind": "source_node", "path": "apps/web/config/src/Widget.tsx"}
    )
    assert any(
        edge["source"] == page_id and edge["target"] == widget_id
        for edge in seal.final_plan["source_graph"]["edges"]
    )


def test_shadowed_require_is_kept_open_instead_of_resolved_as_node_loader(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    files = {
        "package.json": b'{"dependencies":{"next":"15"}}',
        "tsconfig.json": b'{"include":["src/**/*"]}',
        "src/entry.ts": (
            b'function load(require: (id: string) => unknown) { return require("./Local"); }'
        ),
        "src/Local.ts": b"export const Local = 1;",
    }
    for path, content in files.items():
        target = repository / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    entries = tuple(
        EnumeratedPath(path, PurePosixPath(path))
        for path in sorted(files, key=lambda value: value.encode("utf-8"))
    )
    head = Commit("8" * 40)
    reader = DescriptorAnchoredSourceReadSession(
        repository,
        entries,
        head_state=head,
        current_entries=lambda: entries,
        current_head_state=lambda: head,
        max_files=20_000,
        max_file_bytes=4 * 1024 * 1024,
        max_total_bytes=64 * 1024 * 1024,
    )

    seal = source_acquisition.seal_source_acquisition(
        SourceDiscoveryIntent((".",)),
        reader,
        trusted_environment_digest="8" * 64,
    )
    assert isinstance(seal, SourceAcquisitionSeal)
    graph = seal.final_plan["source_graph"]
    entry_id = source_acquisition._digest({"kind": "source_node", "path": "src/entry.ts"})
    local_id = source_acquisition._digest({"kind": "source_node", "path": "src/Local.ts"})
    assert not any(
        edge["source"] == entry_id and edge["target"] == local_id for edge in graph["edges"]
    )
    assert any(
        edge["source"] == entry_id and edge["syntax_kind"] == "module_plane"
        for edge in graph["open_edges"]
    )


def test_mixed_applicability_plan_keeps_non_applicable_project_rows(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    files = {
        "apps/web/package.json": b'{"dependencies":{"next":"15"}}',
        "apps/web/tsconfig.json": b'{"include":["src/**/*"]}',
        "apps/web/src/Page.tsx": b"export default function Page() { return null; }",
        "packages/ui/package.json": b'{"name":"ui"}',
        "packages/ui/src/Widget.tsx": b"not selected by Next acquisition",
    }
    for path, content in files.items():
        target = repository / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    entries = tuple(
        EnumeratedPath(path, PurePosixPath(path))
        for path in sorted(files, key=lambda value: value.encode("utf-8"))
    )
    head = Commit("7" * 40)
    reader = DescriptorAnchoredSourceReadSession(
        repository,
        entries,
        head_state=head,
        current_entries=lambda: entries,
        current_head_state=lambda: head,
        max_files=20_000,
        max_file_bytes=4 * 1024 * 1024,
        max_total_bytes=64 * 1024 * 1024,
    )

    seal = source_acquisition.seal_source_acquisition(
        SourceDiscoveryIntent(("apps/web", "packages/ui")),
        reader,
        trusted_environment_digest="7" * 64,
    )
    assert isinstance(seal, SourceAcquisitionSeal)
    _validator("next-source-plan-v1.schema.json").validate(seal.final_plan)
    assert [row["root"] for row in seal.final_plan["projects"]] == ["apps/web", "packages/ui"]
    assert seal.final_plan["config_resolution"][1] == {
        "project_root": "packages/ui",
        "config_path": None,
        "declaring_paths": [],
        "membership": {"kind": "not_applicable", "patterns": [], "exclude": []},
        "path_resolution_order": [],
    }
    assert [row["path"] for row in seal.final_plan["file_role_map"]] == [
        "apps/web/package.json",
        "apps/web/src/Page.tsx",
        "apps/web/tsconfig.json",
        "packages/ui/package.json",
    ]


def test_package_preflight_rejects_bytes_detached_from_applicability_matrix() -> None:
    reader = MemorySourceReader({"package.json": b'{"name":"plain-app"}'})
    result = NextSourceAcquirer(reader).preflight(SourceDiscoveryIntent((".",)))

    with pytest.raises(ValueError, match="match the applicability observation"):
        replace(
            result,
            frozen_package_bytes=(("package.json", b'{"dependencies":{"next":"15"}}'),),
        )


def test_overlapping_project_roots_fail_before_repository_observation() -> None:
    reader = MemorySourceReader(
        {
            "package.json": b'{"dependencies":{"next":"15"}}',
            "apps/web/package.json": b'{"dependencies":{"next":"15"}}',
        }
    )

    with pytest.raises(ValueError, match="project roots must not overlap"):
        intent = SourceDiscoveryIntent((".", "apps/web"))
        NextSourceAcquirer(reader).preflight(intent)

    assert reader.enumerations == 0
    assert reader.reads == []


def test_applicable_root_reads_only_selected_tsconfig_before_program_files() -> None:
    reader = MemorySourceReader(
        {
            "package.json": b'{"dependencies":{"next":"15"}}',
            "tsconfig.json": b'{"compilerOptions":{"jsx":"preserve"}}',
            "jsconfig.json": b"not valid JSONC and must remain unobserved",
            "src/app/page.tsx": b"export default function Page() { return null; }",
        }
    )
    acquirer = NextSourceAcquirer(reader)
    preflight = acquirer.preflight(SourceDiscoveryIntent((".",)))

    configuration = acquirer.resolve_configurations(preflight)

    assert preflight.matrix.aggregate_state is PackageApplicabilityState.APPLICABLE
    assert configuration.projects[0].config_path == "tsconfig.json"
    assert configuration.frozen_control_bytes == (
        ("tsconfig.json", b'{"compilerOptions":{"jsx":"preserve"}}'),
    )
    assert reader.reads == ["package.json", "tsconfig.json"]


def test_local_extends_chain_is_frozen_once_before_membership_is_resolved() -> None:
    reader = MemorySourceReader(
        {
            "package.json": b'{"devDependencies":{"next":"15"}}',
            "tsconfig.json": b'{"extends":"./config/base.json",'
            b'"compilerOptions":{"jsx":"react-jsx"}}',
            "config/base.json": b'{"compilerOptions":{"allowJs":false},"include":["**/*"]}',
            "config/app/page.tsx": b"export default function Page() { return null; }",
            "config/app/generated.js": b"export const generated = true;",
        }
    )
    acquirer = NextSourceAcquirer(reader)
    preflight = acquirer.preflight(SourceDiscoveryIntent((".",)))

    configuration = acquirer.resolve_configurations(preflight)

    project = configuration.projects[0]
    assert project.control_paths == ("config/base.json", "tsconfig.json")
    assert project.compiler_options.jsx == "react-jsx"
    assert project.compiler_options.allow_js is False
    assert project.membership.paths == ("config/app/page.tsx",)
    assert reader.reads == ["package.json", "tsconfig.json", "config/base.json"]


def test_hard_excluded_directories_never_enter_resolved_source_membership() -> None:
    reader = MemorySourceReader(
        {
            "package.json": b'{"dependencies":{"next":"15"}}',
            "tsconfig.json": b'{"include":["**/*"]}',
            "src/app/page.tsx": b"export default function Page() { return null; }",
            "node_modules/pkg/index.tsx": b"export const PackageCode = 1;",
            ".next/types/app.d.ts": b"declare const generated: string;",
            ".git/hooks/config.ts": b"export const generated = true;",
            "out/generated.tsx": b"export const generated = true;",
            "dist/generated.js": b"export const generated = true;",
            "build/generated.jsx": b"export const generated = true;",
            "coverage/generated.ts": b"export const generated = true;",
        }
    )
    acquirer = NextSourceAcquirer(reader)
    preflight = acquirer.preflight(SourceDiscoveryIntent((".",)))

    configuration = acquirer.resolve_configurations(preflight)

    assert configuration.projects[0].membership.paths == ("src/app/page.tsx",)


def test_source_seal_derives_plan_and_view_from_one_read_only_session(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    files = {
        "package.json": b'{"dependencies":{"next":"15"}}',
        "tsconfig.json": b'{"include":["src/**/*"]}',
        "src/Page.tsx": b"const Page = () => null; export default Page;",
        "src/types.d.ts": b"declare interface Props { title: string; }",
    }
    for path, content in files.items():
        target = repository / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    entries = tuple(
        EnumeratedPath(path, PurePosixPath(path))
        for path in sorted(files, key=lambda value: value.encode("utf-8"))
    )
    head = Commit("1" * 40)
    reader = DescriptorAnchoredSourceReadSession(
        repository,
        entries,
        head_state=head,
        current_entries=lambda: entries,
        current_head_state=lambda: head,
        max_files=20_000,
        max_file_bytes=4 * 1024 * 1024,
        max_total_bytes=64 * 1024 * 1024,
    )

    seal = source_acquisition.seal_source_acquisition(
        SourceDiscoveryIntent((".",)),
        reader,
        trusted_environment_digest="a" * 64,
    )
    assert isinstance(seal, SourceAcquisitionSeal)

    assert seal.final_plan["projects"][0]["root"] == "."
    assert seal.final_plan["file_role_map"] == [
        {
            "project_root": ".",
            "path": "package.json",
            "roles": ["control"],
            "effective_role": "control",
        },
        {
            "project_root": ".",
            "path": "src/Page.tsx",
            "roles": ["program"],
            "effective_role": "program",
        },
        {
            "project_root": ".",
            "path": "src/types.d.ts",
            "roles": ["context"],
            "effective_role": "context",
        },
        {
            "project_root": ".",
            "path": "tsconfig.json",
            "roles": ["control"],
            "effective_role": "control",
        },
    ]
    assert seal.final_plan["source_graph"]["graph_digest"] == seal.source_view.source_graph_digest
    assert seal.plan_digest == seal.recompute_plan_digest()
    assert seal.source_view.fingerprint == seal.source_view_fingerprint
    with pytest.raises(RuntimeError, match="sealed"):
        reader.read_once("src/Page.tsx")


def test_source_read_failure_is_a_typed_unavailable_acquisition(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    outside = tmp_path / "outside.ts"
    outside.write_bytes(b"private source")
    files = {
        "package.json": b'{"dependencies":{"next":"15"}}',
        "tsconfig.json": b'{"include":["src/**/*"]}',
    }
    for path, content in files.items():
        target = repository / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    (repository / "src").mkdir()
    (repository / "src/Page.tsx").symlink_to(outside)
    entries = tuple(
        EnumeratedPath(path, PurePosixPath(path))
        for path in ("package.json", "src/Page.tsx", "tsconfig.json")
    )
    head = Commit("4" * 40)
    reader = DescriptorAnchoredSourceReadSession(
        repository,
        entries,
        head_state=head,
        current_entries=lambda: entries,
        current_head_state=lambda: head,
        max_files=20_000,
        max_file_bytes=4 * 1024 * 1024,
        max_total_bytes=64 * 1024 * 1024,
    )

    with pytest.raises(NextSourceAcquisitionError) as caught:
        source_acquisition.seal_source_acquisition(
            SourceDiscoveryIntent((".",)),
            reader,
            trusted_environment_digest="4" * 64,
        )

    assert caught.value.code == "CSV-NEXT-SOURCE-002"
    assert caught.value.stage == "source_integrity"
    assert caught.value.path == "src/Page.tsx"


def test_descriptor_reader_size_limit_maps_to_pathless_source_read_limit(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    package_path = repository / "package.json"
    package_path.write_bytes(b'{"dependencies":{"next":"15"}}')
    entries = (EnumeratedPath("package.json", PurePosixPath("package.json")),)
    head = Commit("6" * 40)
    reader = DescriptorAnchoredSourceReadSession(
        repository,
        entries,
        head_state=head,
        current_entries=lambda: entries,
        current_head_state=lambda: head,
        max_files=20_000,
        max_file_bytes=8,
        max_total_bytes=64,
    )

    with pytest.raises(NextSourceAcquisitionError) as caught:
        source_acquisition.seal_source_acquisition(
            SourceDiscoveryIntent((".",)),
            reader,
            trusted_environment_digest="6" * 64,
        )

    assert (caught.value.code, caught.value.stage, caught.value.path) == (
        "CSV-NEXT-LIMIT-001",
        "source_read",
        None,
    )


def test_descriptor_reader_file_count_limit_maps_to_pathless_selection_limit(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    files = {
        "package.json": b'{"dependencies":{"next":"15"}}',
        "tsconfig.json": b"{}",
        "src/Page.tsx": b"export default function Page() { return null; }",
    }
    for relative_path, content in files.items():
        target = repository / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    entries = tuple(
        EnumeratedPath(path, PurePosixPath(path))
        for path in sorted(files, key=lambda value: value.encode("utf-8"))
    )
    head = Commit("7" * 40)
    reader = DescriptorAnchoredSourceReadSession(
        repository,
        entries,
        head_state=head,
        current_entries=lambda: entries,
        current_head_state=lambda: head,
        max_files=1,
        max_file_bytes=4 * 1024 * 1024,
        max_total_bytes=64 * 1024 * 1024,
    )

    with pytest.raises(NextSourceAcquisitionError) as caught:
        source_acquisition.seal_source_acquisition(
            SourceDiscoveryIntent((".",), control_candidates=("tsconfig.json",)),
            reader,
            trusted_environment_digest="7" * 64,
        )

    assert (caught.value.code, caught.value.stage, caught.value.path) == (
        "CSV-NEXT-LIMIT-002",
        "source_selection",
        None,
    )


def test_source_plan_file_count_limit_uses_selection_failure_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reader = MemorySourceReader(
        {
            "package.json": b'{"dependencies":{"next":"15"}}',
            "tsconfig.json": b'{"include":["src/**/*"]}',
            "src/Page.tsx": b"export default function Page() { return null; }",
        }
    )
    monkeypatch.setattr(
        source_acquisition,
        "DEFAULT_NEXT_LIMITS",
        {**source_acquisition.DEFAULT_NEXT_LIMITS, "max_files": 2},
    )

    with pytest.raises(NextSourceAcquisitionError) as caught:
        source_acquisition.seal_source_acquisition(
            SourceDiscoveryIntent((".",), control_candidates=("tsconfig.json",)),
            reader,
            trusted_environment_digest="8" * 64,
        )

    assert (caught.value.code, caught.value.stage, caught.value.path) == (
        "CSV-NEXT-LIMIT-002",
        "source_selection",
        None,
    )
    assert reader.reads == ["package.json", "tsconfig.json"]
    assert reader.seal_calls == 0


def test_source_plan_per_file_size_limit_does_not_publish_a_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package_bytes = b'{"dependencies":{"next":"15"}}' + b" " * 16
    reader = MemorySourceReader(
        {
            "package.json": package_bytes,
            "tsconfig.json": b"{}",
        }
    )
    monkeypatch.setattr(
        source_acquisition,
        "DEFAULT_NEXT_LIMITS",
        {**source_acquisition.DEFAULT_NEXT_LIMITS, "max_file_bytes": 8},
    )

    with pytest.raises(NextSourceAcquisitionError) as caught:
        source_acquisition.seal_source_acquisition(
            SourceDiscoveryIntent((".",), control_candidates=("tsconfig.json",)),
            reader,
            trusted_environment_digest="9" * 64,
        )

    assert (caught.value.code, caught.value.stage, caught.value.path) == (
        "CSV-NEXT-LIMIT-001",
        "source_read",
        None,
    )


def test_source_plan_total_size_limit_does_not_publish_a_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package_bytes = b'{"dependencies":{"next":"15"}}'
    config_bytes = b"{}"
    reader = MemorySourceReader(
        {
            "package.json": package_bytes,
            "tsconfig.json": config_bytes,
            "src/Page.tsx": b"x",
        }
    )
    monkeypatch.setattr(
        source_acquisition,
        "DEFAULT_NEXT_LIMITS",
        {
            **source_acquisition.DEFAULT_NEXT_LIMITS,
            "max_file_bytes": 1024,
            "max_decoded_bytes": len(package_bytes) + len(config_bytes),
        },
    )

    with pytest.raises(NextSourceAcquisitionError) as caught:
        source_acquisition.seal_source_acquisition(
            SourceDiscoveryIntent((".",), control_candidates=("tsconfig.json",)),
            reader,
            trusted_environment_digest="a" * 64,
        )

    assert (caught.value.code, caught.value.stage, caught.value.path) == (
        "CSV-NEXT-LIMIT-001",
        "source_read",
        None,
    )
    assert reader.reads == ["package.json", "tsconfig.json", "src/Page.tsx"]


def test_source_inventory_drift_is_fatal_integrity_failure(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    files = {
        "package.json": b'{"dependencies":{"next":"15"}}',
        "tsconfig.json": b'{"include":["src/**/*"]}',
        "src/Page.tsx": b"export default function Page() { return null; }",
    }
    for path, content in files.items():
        target = repository / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    entries = tuple(
        EnumeratedPath(path, PurePosixPath(path))
        for path in sorted(files, key=lambda value: value.encode("utf-8"))
    )
    current_entries = list(entries)
    head = Commit("5" * 40)
    reader = DescriptorAnchoredSourceReadSession(
        repository,
        entries,
        head_state=head,
        current_entries=lambda: tuple(current_entries),
        current_head_state=lambda: head,
        max_files=20_000,
        max_file_bytes=4 * 1024 * 1024,
        max_total_bytes=64 * 1024 * 1024,
    )
    current_entries.append(EnumeratedPath("README.md", PurePosixPath("README.md")))

    with pytest.raises(NextSourceIntegrityError) as caught:
        source_acquisition.seal_source_acquisition(
            SourceDiscoveryIntent((".",)),
            reader,
            trusted_environment_digest="5" * 64,
        )

    assert caught.value.code == "CSV-NEXT-SOURCE-INTEGRITY-001"
    assert caught.value.stage == "source_integrity"
